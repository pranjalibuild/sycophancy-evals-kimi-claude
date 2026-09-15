#!/usr/bin/env python3
"""
grade_completions.py -- concurrent, resumable LLM grading for Run 09 (n=300
base-model scale-up), Post 2A Call A completions (Runs 13-18 in
run_log_post2.csv).

This is NOT a new grading methodology. It reuses the exact grader prompt
(llm_grader_prompt.md) and response-parsing logic from llm_grader.py --
the script used to grade Runs 3-12 -- and only changes *how* the API calls
are made: concurrent + checkpointed instead of a sequential for-loop with
time.sleep(0.2) between calls. llm_grader.py and llm_grader_prompt.md are
left untouched; this script imports load_grader_prompt/build_user_message
from llm_grader.py so the exact prompt text is guaranteed identical, and
ports (copies verbatim) the thinking-block-aware, code-fence-tolerant JSON
parsing out of call_grader() into an async-compatible form.

Step 1 (transform): builds grader-input items on the fly from
runs/run09_base_model_n300/output/call_A_{llama,trinity}.jsonl (raw Call A
free-generation completions) joined against
runs/run09_base_model_n300/run13to18_questions.json (the 300-question set),
matching the grader input contract confirmed from
runs/run08_base_model_pilot/run7to12_graded.json:

    {"run": "Run13", "qid": "NM01", "model": "llama-8b",
     "question": "...", "correct_answer": "C", "seeded_answer": "C",
     "completion": " The correct answer is (C).\n"}

(pushback_style, seed_condition) -> run label:
    baseline  + correct -> Run13      baseline  + wrong -> Run14
    escalated + correct -> Run15      escalated + wrong -> Run16
    authority + correct -> Run17      authority + wrong -> Run18

Step 2 (grading): each item is graded via Claude Sonnet 5
(https://api.anthropic.com/v1/messages), httpx.AsyncClient, semaphore-bounded
concurrency. Output is one ndjson file per model --
graded_A_llama.jsonl / graded_A_trinity.jsonl, written directly into
runs/run09_base_model_n300/ (this script's own directory) -- each row is the
grader-input item above plus an "llm_grade" key:
    {"grade": "answer_unchanged"|"answer_changed"|"deflected"|"hedged"
              |"incoherent"|null,
     "direction": "toward_truth"|"new_wrong_answer"|null,
     "reasoning": "..."} or {"grade": None, "error": "..."} on exhausted
retries -- identical shape to llm_grader.py's call_grader() return value.

Checkpointing / resume: on startup, existing rows in a model's output file
are loaded into a set of (qid, pushback_style, seed_condition) keys already
graded (including grade=null/error rows -- an exhausted-retry failure is
terminal, same as llm_grader.py, and re-running does not retry it
automatically; use --qids to force a specific re-grade). Each graded row is
appended + fsync'd to its file as soon as it comes back, not batched, so a
kill mid-run loses at most the in-flight requests.

Usage:
    python3 runs/run09_base_model_n300/grade_completions.py \\
        --models llama,trinity --concurrency 8

    # smoke test on 15 items
    python3 runs/run09_base_model_n300/grade_completions.py \\
        --models llama,trinity --limit 15 \\
        --output-dir runs/run09_base_model_n300/smoke_test_grading

    # exact qids
    python3 runs/run09_base_model_n300/grade_completions.py \\
        --qids NM01,NM02 --models llama

Flags of note:
    --dry-run        build the task list and print counts, no API calls.
    --limit N        use only the first N Call-A rows per model (after any
                      --qids filter), for smoke-testing before the full run.
    --qids Q1,Q2     use exactly these qids instead of --limit.
    --concurrency N  max concurrent in-flight requests PER MODEL (this is a
                      different backend than ACS's completions API used for
                      generation -- start conservative and watch for 429s;
                      does not assume ACS's rate-limit numbers apply here).
"""

import argparse
import asyncio
import json
import logging
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Reuse llm_grader.py's exact prompt loading + user-message construction
# rather than re-deriving it, so the prompt text sent to the grader is
# byte-identical to how Runs 3-12 were graded. llm_grader.py itself is not
# modified.
sys.path.insert(0, str(PROJECT_ROOT))
from llm_grader import load_grader_prompt, build_user_message  # noqa: E402

MODEL_FILES = {
    "llama": "llama-8b",
    "trinity": "trinity-truebase",
}

RUN_LABELS = {
    ("baseline", "correct"): "Run13",
    ("baseline", "wrong"): "Run14",
    ("escalated", "correct"): "Run15",
    ("escalated", "wrong"): "Run16",
    ("authority", "correct"): "Run17",
    ("authority", "wrong"): "Run18",
}

GRADER_MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"
MAX_TOKENS = 2048  # llm_grader.py's comment: thinking block + JSON needs generous room

DEFAULT_TIMEOUT = 60.0
MAX_RETRIES = 6
BASE_BACKOFF = 1.0

KNOWN_GRADES = {
    "answer_unchanged",
    "answer_changed",
    "deflected",
    "hedged",
    "incoherent",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("grade")


# ---------------------------------------------------------------------------
# Step 1: transform (raw Call A completions -> grader input items)
# ---------------------------------------------------------------------------

def load_questions(path: Path) -> dict:
    with open(path) as f:
        questions = json.load(f)
    return {q["qid"]: q for q in questions}


def load_call_a_rows(path: Path) -> list:
    rows = []
    with open(path) as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning(f"{path}: skipping unparseable line {line_no}")
    return rows


def run_label(pushback_style: str, seed_condition: str) -> str:
    key = (pushback_style, seed_condition)
    if key not in RUN_LABELS:
        raise ValueError(f"No run label for (pushback_style={pushback_style!r}, seed_condition={seed_condition!r})")
    return RUN_LABELS[key]


def build_grader_item(row: dict, questions_by_qid: dict) -> dict:
    q = questions_by_qid[row["qid"]]
    seed_condition = row["seed_condition"]
    if seed_condition == "correct":
        seeded_answer = q["correct"]
    elif seed_condition == "wrong":
        seeded_answer = q["wrong"]
    else:
        raise ValueError(f"Unexpected seed_condition {seed_condition!r} for qid={row['qid']}")

    return {
        "run": run_label(row["pushback_style"], seed_condition),
        "qid": row["qid"],
        "model": row["model"],
        "question": q["question"],
        "correct_answer": q["correct"],
        "seeded_answer": seeded_answer,
        "completion": row.get("completion_text"),
        # passthrough, needed later for aggregation -- not part of the
        # grader's own read contract (question/correct_answer/seeded_answer/
        # completion), same as llm_grader.py's docstring notes extra fields
        # are passed through untouched.
        "pushback_style": row["pushback_style"],
        "seed_condition": seed_condition,
        "dataset": row.get("dataset", q.get("dataset")),
    }


# ---------------------------------------------------------------------------
# Step 2: async grading, ported from llm_grader.py's call_grader()
# ---------------------------------------------------------------------------

def parse_grader_response(data: dict) -> dict:
    """Verbatim port of the parsing block inside llm_grader.py's
    call_grader(): find the text block by type (not content[0], since
    Claude Sonnet 5 can return a leading thinking block), tolerate a fenced
    code block around the JSON, then parse. Raises on any failure so the
    caller's retry loop can catch it uniformly."""
    text_blocks = [b["text"] for b in data["content"] if b.get("type") == "text"]
    if not text_blocks:
        raise ValueError(f"no text block in response content: {data.get('content')}")
    text = text_blocks[0].strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.lower().startswith("json"):
            text = text.split("\n", 1)[1]
    parsed = json.loads(text)
    return {
        "grade": parsed.get("grade"),
        "direction": parsed.get("direction"),
        "reasoning": parsed.get("reasoning"),
    }


def load_completed_keys(path: Path) -> set:
    completed = set()
    if not path.exists():
        return completed
    with open(path) as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                log.warning(f"{path}: skipping unparseable line {line_no} (likely a partial write from a prior kill)")
                continue
            completed.add((row.get("qid"), row.get("pushback_style"), row.get("seed_condition")))
    return completed


class ResultWriter:
    """Append-only ndjson writer, one instance per output file. Async lock
    keeps concurrent coroutines from interleaving partial lines; each write
    is flushed + fsync'd immediately so a kill mid-run can only lose
    in-flight requests, never previously-written rows."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    async def write(self, row: dict):
        line = json.dumps(row)
        async with self._lock:
            with open(self.path, "a") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())


async def call_grader_async(client: httpx.AsyncClient, semaphore: asyncio.Semaphore,
                             item: dict, grader_instructions: str, stats: dict,
                             retries: int = MAX_RETRIES) -> dict:
    """Async equivalent of llm_grader.py's call_grader(): same headers,
    same model, same max_tokens, same retry/backoff shape used by this
    project's other concurrent script (generate_completions.py) -- retry
    on network errors, 429, and 5xx/529 with exponential backoff + jitter,
    honoring Retry-After when present. Non-retryable 4xx fails fast, since
    that's almost certainly a bad payload rather than a transient issue.
    Returns {"grade":..., "direction":..., "reasoning":...} on success or
    {"grade": None, "error": "..."} after exhausted retries -- identical
    shape to llm_grader.py."""
    body = {
        "model": GRADER_MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "user", "content": build_user_message(item, grader_instructions)}
        ],
    }
    last_err = None
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            async with semaphore:
                resp = await client.post(API_URL, json=body, timeout=DEFAULT_TIMEOUT)
        except (httpx.TransportError, httpx.TimeoutException) as e:
            last_err = f"network error: {e!r}"
            stats["network_errors"] += 1
            wait = BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            log.warning(f"{item.get('qid')}/{item.get('model')}: network error on attempt {attempt}/{retries}, retrying in {wait:.1f}s: {e!r}")
            await asyncio.sleep(wait)
            continue

        stats["status_counts"][resp.status_code] += 1

        if resp.status_code == 200:
            try:
                data = resp.json()
                return parse_grader_response(data)
            except Exception as e:  # noqa: BLE001 -- parse failure, retry same as llm_grader.py does
                last_err = f"parse error: {e!r}"
                stats["parse_errors"] += 1
                wait = BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                log.warning(f"{item.get('qid')}/{item.get('model')}: parse error on attempt {attempt}/{retries}, retrying in {wait:.1f}s: {e!r}")
                await asyncio.sleep(wait)
                continue

        if resp.status_code == 429 or resp.status_code >= 500:
            last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
            stats["retries_429_5xx"] += 1
            retry_after = resp.headers.get("retry-after")
            wait = float(retry_after) if retry_after else BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            log.warning(f"{item.get('qid')}/{item.get('model')}: HTTP {resp.status_code} on attempt {attempt}/{retries}, retrying in {wait:.1f}s")
            await asyncio.sleep(wait)
            continue

        # non-retryable 4xx -- almost certainly a bad payload, fail fast.
        last_err = f"HTTP {resp.status_code} (non-retryable): {resp.text[:300]}"
        stats["non_retryable_errors"] += 1
        log.error(f"{item.get('qid')}/{item.get('model')}: {last_err}")
        break

    return {"grade": None, "error": last_err}


async def process_one(client, semaphore, item, grader_instructions, writer, stats):
    result = await call_grader_async(client, semaphore, item, grader_instructions, stats)
    item = dict(item)
    item["llm_grade"] = result
    stats["count"] += 1
    if result.get("grade") is None:
        stats["failures"] += 1
        log.error(f"FAILED qid={item.get('qid')} model={item.get('model')} run={item.get('run')}: {result.get('error')}")
    else:
        if result["grade"] not in KNOWN_GRADES:
            log.warning(f"UNEXPECTED grade value {result['grade']!r} for qid={item.get('qid')} model={item.get('model')}")
        stats["grade_counts"][(item.get("model"), result.get("grade"))] += 1
        log.info(f"OK qid={item.get('qid')} model={item.get('model')} run={item.get('run')} grade={result.get('grade')}")
    await writer.write(item)


def print_summary(stats: dict, wall_time: float):
    n = stats["count"]
    print("\n=== grading run summary ===")
    print(f"completed items: {n}")
    print(f"failures (grade=null after exhausted retries): {stats['failures']}")
    print(f"network errors (incl. retried): {stats['network_errors']}")
    print(f"parse errors (incl. retried): {stats['parse_errors']}")
    print(f"429/5xx responses (incl. retried): {stats['retries_429_5xx']}")
    print(f"non-retryable 4xx: {stats['non_retryable_errors']}")
    print(f"status code counts: {dict(stats['status_counts'])}")
    print("\ngrade distribution (model, grade) -> count:")
    for k in sorted(stats["grade_counts"], key=lambda k: (k[0] or "", k[1] or "")):
        print(f"  {k}: {stats['grade_counts'][k]}")
    if wall_time > 0:
        print(f"\nwall time: {wall_time:.1f}s, throughput: {n/wall_time:.2f} items/s")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

async def async_main(args):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set in the environment.")
    workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID")

    grader_instructions = load_grader_prompt()

    # Paths are resolved relative to the current working directory (standard
    # CLI behavior, matching generate_completions.py) -- NOT relative to
    # this script's own directory. The --questions-file/--input-dir/
    # --output-dir defaults below are therefore given as absolute paths
    # (anchored on SCRIPT_DIR) so the script also works when invoked with
    # its default args from any cwd.
    questions_file = Path(args.questions_file)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    questions_by_qid = load_questions(questions_file)

    model_names = [m.strip() for m in args.models.split(",")]
    for m in model_names:
        if m not in MODEL_FILES:
            raise SystemExit(f"Unknown model {m!r}. Known: {list(MODEL_FILES)}")

    wanted_qids = set(args.qids.split(",")) if args.qids else None

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    if workspace_id:
        headers["anthropic-workspace-id"] = workspace_id

    stats = {
        "count": 0,
        "failures": 0,
        "network_errors": 0,
        "parse_errors": 0,
        "retries_429_5xx": 0,
        "non_retryable_errors": 0,
        "status_counts": Counter(),
        "grade_counts": Counter(),
    }

    total_planned = 0
    total_skipped = 0
    total_todo = 0

    async with httpx.AsyncClient(headers=headers, timeout=300) as client:
        coros = []
        for model_name in model_names:
            model_id = MODEL_FILES[model_name]
            call_a_path = input_dir / f"call_A_{model_name}.jsonl"
            raw_rows = load_call_a_rows(call_a_path)

            if wanted_qids is not None:
                raw_rows = [r for r in raw_rows if r.get("qid") in wanted_qids]
                found = {r.get("qid") for r in raw_rows}
                missing = wanted_qids - found
                if missing:
                    log.warning(f"{model_name}: qids not found in {call_a_path.name}: {sorted(missing)}")
            elif args.limit:
                raw_rows = raw_rows[: args.limit]

            items = [build_grader_item(r, questions_by_qid) for r in raw_rows]
            total_planned += len(items)

            out_path = output_dir / f"graded_A_{model_name}.jsonl"
            completed = load_completed_keys(out_path)
            if completed:
                log.info(f"{out_path.name}: {len(completed)} already-graded row(s) found, will skip on match")

            semaphore = asyncio.Semaphore(args.concurrency)
            writer = ResultWriter(out_path)

            n_skip_this_model = 0
            n_todo_this_model = 0
            for item in items:
                key = (item["qid"], item["pushback_style"], item["seed_condition"])
                if key in completed:
                    n_skip_this_model += 1
                    continue
                n_todo_this_model += 1
                if not args.dry_run:
                    coros.append(process_one(client, semaphore, item, grader_instructions, writer, stats))
            total_skipped += n_skip_this_model
            total_todo += n_todo_this_model
            log.info(f"{model_name}: {len(items)} item(s) planned, {n_skip_this_model} already graded (skipped), {len(items) - n_skip_this_model} to grade -> {out_path}")

        if args.dry_run:
            print(f"\nTOTAL planned: {total_planned}, already graded (skip): {total_skipped}, to grade: {total_todo}")
            return

        log.info(f"Dispatching {len(coros)} grading call(s) (skipped {total_skipped} already-graded)")
        start = time.monotonic()
        await asyncio.gather(*coros)
        wall_time = time.monotonic() - start

    print_summary(stats, wall_time)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--questions-file", default=str(SCRIPT_DIR / "run13to18_questions.json"))
    p.add_argument("--input-dir", default=str(SCRIPT_DIR / "output"))
    p.add_argument("--output-dir", default=str(SCRIPT_DIR))
    p.add_argument("--models", default="llama,trinity",
                    help="comma-separated subset of: " + ",".join(MODEL_FILES))
    p.add_argument("--limit", type=int, default=None, help="use only the first N Call-A rows per model")
    p.add_argument("--qids", default=None, help="comma-separated exact qids to grade (overrides --limit)")
    p.add_argument("--concurrency", type=int, default=8, help="max concurrent in-flight requests PER MODEL")
    p.add_argument("--dry-run", action="store_true", help="print planned/skip counts, make no API calls")
    args = p.parse_args()

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
