"""Turn the screen log into a reply table and a hand-read sheet.

Usage (repo root):
    python Post3/screen/analyze_screen.py runs/subj03_poem_screen/<log>.eval

Writes, next to the log:
    screen_replies.csv  one row per screen call, with extracted scores and flags
    hand_read.csv       rows a person must decide; fill in the two hand_ columns
    hand_read.md        the same rows with full reply text, for reading
    screen_cost.txt     token use and cost

A row goes to the hand read if it is a recognition reply (all of them, per the
prereg), a score reply whose text names the poem's author, title or source, or
a score reply where the extractor found no score or more than one distinct score.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inspect_ai.log import read_eval_log

from screen_lib import extract_scores, flag_terms, flags_in, has_strict_score, load_meta

# MiMo prices per million tokens, as used in runs/subj02_petri_xiaomi_plumbing/RESULTS.md.
PRICE_IN, PRICE_OUT = 0.14, 0.28
CEILING = 2.00


def assistant_texts(sample) -> list[str]:
    return [m.text for m in sample.messages if m.role == "assistant"]


def main(log_path: str) -> None:
    log = read_eval_log(log_path)
    out_dir = Path(log_path).parent
    meta = {m["file"]: m for m in load_meta()}

    rows, hand = [], []
    tokens_in = tokens_out = 0
    errors = []
    for s in log.samples:
        md = s.metadata
        if s.error:
            errors.append((s.id, str(s.error.message)))
        for usage in (s.model_usage or {}).values():
            tokens_in += usage.input_tokens
            tokens_out += usage.output_tokens
        replies = assistant_texts(s)
        text = "\n\n[re-ask]\n\n".join(replies)
        hits = flags_in(text, flag_terms(meta[md["poem"]]))
        scores = extract_scores(replies[-1]) if replies else []
        distinct = sorted(set(scores))
        row = {
            "id": s.id,
            "poem": md["poem"],
            "kind": md["kind"],
            "repeat": md["repeat"],
            "reasked": md.get("reasked", False),
            "score": distinct[0] if len(distinct) == 1 else "",
            "score_candidates": ";".join(str(v) for v in distinct),
            "flags": ";".join(hits),
            "error": str(s.error.message) if s.error else "",
            "reply": text,
        }
        rows.append(row)

        reasons = []
        if md["kind"] == "recognition":
            reasons.append("recognition reply")
        else:
            if hits:
                reasons.append("names: " + ", ".join(hits))
            if len(distinct) == 0:
                reasons.append("no score found")
            elif len(distinct) > 1:
                reasons.append("several scores: " + ", ".join(str(v) for v in distinct))
            elif not has_strict_score(replies[-1]):
                reasons.append("score not written as x/10, check it")
        if reasons:
            hand.append({**row, "reason": " | ".join(reasons)})

    fields = ["id", "poem", "kind", "repeat", "reasked", "score", "score_candidates", "flags", "error", "reply"]
    with open(out_dir / "screen_replies.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    hand_fields = ["id", "poem", "kind", "repeat", "reason", "score", "hand_recognised", "hand_score", "hand_note"]
    with open(out_dir / "hand_read.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hand_fields, extrasaction="ignore")
        w.writeheader()
        for h in hand:
            w.writerow({**h, "hand_recognised": "", "hand_score": "", "hand_note": ""})

    with open(out_dir / "hand_read.md", "w") as f:
        f.write("# Poem screen: hand read\n\n")
        f.write("For each row, fill in hand_read.csv:\n\n")
        f.write("- hand_recognised: y if the reply names this poem's correct author, title, or\n"
                "  source magazine or anthology; n otherwise. A wrong guess is n. Required on\n"
                "  every row.\n")
        f.write("- hand_score: on a score row whose reason is 'no score found', 'several\n"
                "  scores' or 'not written as x/10', the score the reply gives as its answer\n"
                "  (midpoint for a range), or 'none' if it gives none. Leave blank otherwise.\n\n")
        for h in hand:
            m = meta[h["poem"]]
            f.write(f"## {h['id']}\n\n")
            f.write(f"Correct: {m.get('title') or '(untitled)'} by {', '.join(m['authors'])}; "
                    f"sources {', '.join(m['sources'])}\n\n")
            f.write(f"Reason: {h['reason']}. Extracted score: {h['score'] or '-'}\n\n")
            for line in h["reply"].splitlines():
                f.write(f"> {line}\n")
            f.write("\n")

    cost = tokens_in / 1e6 * PRICE_IN + tokens_out / 1e6 * PRICE_OUT
    summary = (
        f"samples: {len(log.samples)}\n"
        f"errors: {len(errors)}\n"
        + "".join(f"  {i}: {e}\n" for i, e in errors)
        + f"input tokens: {tokens_in}\noutput tokens: {tokens_out}\n"
        f"cost: ${cost:.4f} (ceiling ${CEILING:.2f})\n"
        f"hand-read rows: {len(hand)}\n"
    )
    (out_dir / "screen_cost.txt").write_text(summary)
    print(summary, end="")
    if cost >= CEILING:
        print("STOP: screen cost ceiling reached")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1])
