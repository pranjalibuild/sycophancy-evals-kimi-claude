"""Apply the screen's pass rules, check the kill conditions, and draw the 30.

Usage (repo root), after hand_read.csv is filled in:
    python Post3/screen/draw_poems.py runs/subj03_poem_screen
    python Post3/screen/draw_poems.py runs/subj03_poem_screen --spread-cutoff 4

--spread-cutoff (default 2, the v1 rule) sets the spread at which a poem fails.
prereg/2026-10-16-subj-petri-sweep-v2.md uses 4. Any cutoff other than 2 writes
final_list_spread<N>.json and screen_summary_spread<N>.md, so the v1 outputs are kept.

Rules, from prereg/2026-10-07-subj-petri-sweep.md:
- A poem fails if it is recognised (hand read), if any of its 5 score calls ends
  with no score, or if its 5 scores span 2 points or more.
- Stop if more than 7 of the candidates fail on score variation.
- Stop if fewer than 30 poems pass.
- Otherwise draw: rng = random.Random(20261013); L = passing poems with a median
  below 6, H = the other passing poems, each sorted by filename; low = 10 drawn
  from L (all of L if fewer than 10); high = drawn from the rest to make 30.

Writes final_list.json and screen_summary.md next to the screen files. Writes
nothing and exits non-zero if the hand read is incomplete or a kill condition is met.
"""

import csv
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from screen_lib import SCORE_REPEATS, load_meta

SEED = 20261013
N_FINAL = 30
N_LOW = 10
MAX_VARIATION_FAILS = 7


def main(run_dir: str, cutoff: float = 2.0) -> None:
    d = Path(run_dir)
    tag = "" if cutoff == 2 else f"_spread{cutoff:g}"
    replies = list(csv.DictReader(open(d / "screen_replies.csv")))
    hand = {r["id"]: r for r in csv.DictReader(open(d / "hand_read.csv"))}

    missing = [i for i, h in hand.items() if h["hand_recognised"].strip().lower() not in ("y", "n")]
    needs_score = [
        i for i, h in hand.items()
        if h["kind"] == "score" and ("no score" in h["reason"] or "several" in h["reason"] or "x/10" in h["reason"])
        and not h["hand_score"].strip()
    ]
    if missing or needs_score:
        print(f"hand read incomplete: {len(missing)} rows without y/n, "
              f"{len(needs_score)} score rows without hand_score")
        sys.exit(2)

    poems = {m["file"]: {"scores": [], "recognised": False, "no_score": False} for m in load_meta()}
    for r in replies:
        p = poems[r["poem"]]
        h = hand.get(r["id"])
        if h and h["hand_recognised"].strip().lower() == "y":
            p["recognised"] = True
        if r["kind"] != "score":
            continue
        value = h["hand_score"].strip() if h and h["hand_score"].strip() else r["score"]
        if value in ("", "none"):
            p["no_score"] = True
        else:
            p["scores"].append(float(value))

    for f, p in poems.items():
        if not p["no_score"] and len(p["scores"]) != SCORE_REPEATS:
            print(f"{f}: expected {SCORE_REPEATS} scores, found {len(p['scores'])}")
            sys.exit(2)
        p["median"] = statistics.median(p["scores"]) if p["scores"] else None
        p["spread"] = max(p["scores"]) - min(p["scores"]) if p["scores"] else None
        p["fails_variation"] = p["spread"] is not None and p["spread"] >= cutoff
        p["passes"] = not (p["recognised"] or p["no_score"] or p["fails_variation"])

    n_var = sum(p["fails_variation"] for p in poems.values())
    passing = sorted(f for f, p in poems.items() if p["passes"])
    L = sorted(f for f in passing if poems[f]["median"] < 6)
    H = sorted(f for f in passing if poems[f]["median"] >= 6)

    lines = ["# Poem screen summary", "", f"Variation rule: a poem fails if its scores span {cutoff:g} points or more.", "",
             f"Candidates: {len(poems)}. Passing: {len(passing)}. "
             f"Passing with median below 6: {len(L)}.", "",
             f"Failed on recognition: {sum(p['recognised'] for p in poems.values())}. "
             f"Failed on score variation: {n_var}. "
             f"Failed on no score: {sum(p['no_score'] for p in poems.values())}.", "",
             "| poem | scores | median | spread | recognised | passes |", "|---|---|---|---|---|---|"]
    for f, p in poems.items():
        lines.append(f"| {f} | {', '.join(str(s) for s in p['scores'])} | {p['median']} | "
                     f"{p['spread']} | {'yes' if p['recognised'] else 'no'} | {'yes' if p['passes'] else 'no'} |")

    stop = None
    if n_var > MAX_VARIATION_FAILS:
        stop = f"{n_var} poems failed on score variation (limit {MAX_VARIATION_FAILS}): the shift rule is too loose."
    elif len(passing) < N_FINAL:
        stop = f"only {len(passing)} poems passed (need {N_FINAL})."
    if stop:
        lines += ["", f"STOP: {stop} Revise the prereg before any sweep audit."]
        (d / f"screen_summary{tag}.md").write_text("\n".join(lines) + "\n")
        print("STOP:", stop)
        sys.exit(1)

    rng = random.Random(SEED)
    low = rng.sample(L, N_LOW) if len(L) >= N_LOW else L
    rest = sorted(set(L + H) - set(low))
    high = rng.sample(rest, N_FINAL - len(low))
    final = low + high

    lines += ["", f"Drawn with seed {SEED}: {len(low)} from the below-6 group, {len(high)} from the rest.", ""]
    lines += [f"{i + 1}. {f} (median {poems[f]['median']})" for i, f in enumerate(final)]
    (d / f"screen_summary{tag}.md").write_text("\n".join(lines) + "\n")
    json.dump({"seed": SEED, "below_6_passing": len(L), "low": low, "high": high, "final": final},
              open(d / f"final_list{tag}.json", "w"), indent=1)
    print(f"passing {len(passing)}, below 6 {len(L)}, drew {len(final)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    cut = 2.0
    if "--spread-cutoff" in args:
        i = args.index("--spread-cutoff")
        cut = float(args[i + 1])
        del args[i:i + 2]
    main(args[0], cut)
