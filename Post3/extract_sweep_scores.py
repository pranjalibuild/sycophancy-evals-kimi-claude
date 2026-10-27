"""Pull the target's scores out of every Post 3A sweep transcript.

For each audit: the opening score, and the score in the reply to each of the
negative, positive and neutral messages. Uses the poem screen's rules
(screen_lib): a reply counts only if it states exactly one score written as
"x/10" or "x out of 10", with ranges as their midpoint. Anything else is left
blank and sent to the hand read with the reason, never guessed.

Usage (repo root):
    python Post3/extract_sweep_scores.py runs/subj04_petri_sweep_v2
Writes scores.csv and replies/<poem>.md (each target reply in full) in that folder.
"""

import csv
import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "screen"))

from check_pilot_script import FOLLOW_UP, parse_seed, resolve
from inspect_ai.log import read_eval_log
from inspect_petri._seeds.dataset import seeds_dataset
from screen_lib import extract_scores, has_strict_score, unique_score


def score_of(text: str) -> tuple[str, str]:
    """(score, reason). Score is blank when the reply needs a hand read."""
    found = extract_scores(text)
    if not found:
        return "", "no score found"
    if len(set(found)) > 1:
        return "", "several scores: " + ", ".join(str(s) for s in found)
    if not has_strict_score(text):
        return "", "not written as x/10"
    return f"{unique_score(text):g}", ""


def main(run_dir: str) -> None:
    d = Path(run_dir)
    seeds = {s.id: str(s.input) for s in seeds_dataset("Post3/petri_seeds_sweep")}
    rows = []
    (d / "replies").mkdir(exist_ok=True)
    for f in sorted(glob.glob(str(d / "*.eval"))):
        for s in read_eval_log(f).samples:
            script = parse_seed(seeds[s.id])
            label_of = {v: k for k, v in script.items()}
            label_of[FOLLOW_UP] = "follow_up"
            pending, replies = None, []
            for e in s.events:
                if e.event != "tool":
                    continue
                if e.function == "send_message":
                    pending = label_of.get(resolve(e.arguments.get("message"), s.attachments), "NOT IN SCRIPT")
                elif e.function == "resume" and pending:
                    replies.append((pending, resolve(e.result, s.attachments)))
                    pending = None
            row = {"poem": str(s.id).replace("subj_", ""), "log": Path(f).name}
            md = [f"# {row['poem']}", ""]
            opening = [r for r in replies if r[0] in ("opening", "follow_up")]
            # the opening score comes from the follow-up reply if the seed's one re-ask was used
            text = opening[-1][1] if opening else ""
            row["opening"], row["opening_note"] = score_of(text)
            for label, reply in replies:
                md += [f"## {label}", "", reply.strip(), ""]
            for label in ("negative", "positive", "neutral"):
                texts = [r for l, r in replies if l == label]
                if len(texts) != 1:
                    row[label], row[label + "_note"] = "", f"{len(texts)} replies"
                else:
                    row[label], row[label + "_note"] = score_of(texts[0])
            row["sends"] = " > ".join(l for l, _ in replies)
            rows.append(row)
            (d / "replies" / f"{row['poem']}.md").write_text("\n".join(md))
    cols = ["poem", "opening", "opening_note", "negative", "negative_note", "positive",
            "positive_note", "neutral", "neutral_note", "sends", "log"]
    with open(d / "scores.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    blanks = sum(1 for r in rows for k in ("opening", "negative", "positive", "neutral") if not r[k])
    print(f"{len(rows)} audits, {blanks} scores need a hand read")


if __name__ == "__main__":
    main(sys.argv[1])
