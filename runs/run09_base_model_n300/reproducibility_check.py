"""
Decisive same-session reproducibility check, run 2026-09-14, in response to
Anji's challenge: before trusting the Sept10-vs-Sept14 drift finding, verify
whether this API even reproduces its own output twice in a row, right now,
with identical params -- fully decoupled from any cross-day confound.

Reuses generate_completions.py's actual build_transcripts(), max_tokens_for(),
and Call A payload shape verbatim (imported, not reimplemented) so this test
cannot introduce a second, different inconsistency on top of whatever caused
the original drift.

Method: for each of 10 NM (non-math, shared with Runs 7-12) questions, fire
the exact same Call A payload (model, prompt, max_tokens, temperature=1,
seed=1, stop=["User:"], logprobs=5) TWICE, back to back, for the
escalated-pushback / correct-seed condition (the condition with the largest
observed Sept10-to-Sept14 swing: trinity's deflected rate 56% -> 2%). Compare
completion #1 to completion #2 for exact byte-for-byte match.

Usage:
    python3 runs/run09_base_model_n300/reproducibility_check.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_completions import (  # noqa: E402
    build_transcripts, max_tokens_for, MODELS, PUSHBACK_STYLES, LOGPROBS_TOPK, API_BASE, API_KEY,
)
import httpx  # noqa: E402

QUESTIONS_PATH = Path(__file__).resolve().parent / "run13to18_questions.json"
TEST_QIDS = [f"NM{i:02d}" for i in range(1, 11)]
STYLE = "escalated"
SEED_CONDITION = "correct"


async def fire_once(client, model_id, prompt, max_tokens):
    payload = {
        "model": model_id,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 1,
        "seed": 1,
        "stop": ["User:"],
        "logprobs": LOGPROBS_TOPK,
    }
    resp = await client.post("/completions", json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["text"], data.get("id")


async def main():
    questions = json.load(open(QUESTIONS_PATH))
    by_qid = {q["qid"]: q for q in questions}
    pushback_text = PUSHBACK_STYLES[STYLE]

    results = []
    async with httpx.AsyncClient(base_url=API_BASE, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=120) as client:
        for qid in TEST_QIDS:
            q = by_qid[qid]
            seed_text = q["correct_seed_text"] if SEED_CONDITION == "correct" else q["wrong_seed_text"]
            prompt_A, _, _ = build_transcripts(q["question"], seed_text, pushback_text)
            max_tokens = max_tokens_for(q["dataset"])
            for model_name, model_id in MODELS.items():
                text1, id1 = await fire_once(client, model_id, prompt_A, max_tokens)
                text2, id2 = await fire_once(client, model_id, prompt_A, max_tokens)
                identical = text1 == text2
                results.append({
                    "qid": qid, "model": model_name, "identical": identical,
                    "completion_1": text1, "completion_2": text2,
                    "request_id_1": id1, "request_id_2": id2,
                })
                status = "MATCH" if identical else "DIFFERENT"
                print(f"{qid} / {model_name}: {status}")
                if not identical:
                    print(f"   call 1: {text1!r}")
                    print(f"   call 2: {text2!r}")

    n_match = sum(r["identical"] for r in results)
    print(f"\n=== {n_match}/{len(results)} back-to-back calls produced byte-identical completions ===")

    out_path = Path(__file__).resolve().parent / "reproducibility_check_results.json"
    json.dump(results, open(out_path, "w"), indent=2)
    print(f"Full results written to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
