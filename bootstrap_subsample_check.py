"""
Checks whether Run 1's n=18 grade rates (correct seed / baseline pushback,
original question set) look like a plausible random draw from Run 7's n=50
grades (same condition, fresh question set) -- or whether they sit outside
the range n=18 sampling noise alone would produce.

This does NOT prove the question sets behave identically. It only tells you
whether "different n, different question set" could be explained by sampling
noise alone, using data that already exists (no new model calls).

Method: for each model, draw many 18-question subsamples WITHOUT replacement
from Run 7's 50 graded completions, compute each grade category's rate per
draw, and report where Run 1's actual observed count falls in that
distribution (percentile rank + whether it's inside the 90% interval).

Usage:
    python3 bootstrap_subsample_check.py [--draws 10000] [--seed 0]
"""

import argparse
import csv
import json
import random
import re
from collections import Counter
from pathlib import Path

GRADED_JSON = Path("runs/run08_base_model_pilot/run7to12_graded.json")
RUN_LOG = Path("run_log_post2.csv")
REFERENCE_RUN = "Run7"  # correct seed / baseline pushback, n=50, same condition as Run 1
SUBSAMPLE_N = 18  # matches Run 1's n
CATEGORIES = ["answer_unchanged", "answer_changed", "deflected", "hedged", "incoherent"]

MODEL_COLUMNS = {
    "llama-8b": "model_1",
    "trinity-truebase": "model_2",
}


def load_run1_observed_counts():
    """Pull Run 1's actual per-category counts straight from run_log_post2.csv
    so this script stays correct if that row is ever corrected."""
    with open(RUN_LOG, newline="") as f:
        rows = list(csv.DictReader(f))
    row = next(r for r in rows if r["post2_run_number"] == "1")

    observed = {}
    for model, prefix in MODEL_COLUMNS.items():
        counts = {}
        for cat in CATEGORIES:
            raw = row[f"{prefix}_{cat}"]  # e.g. "11 (61%)"
            counts[cat] = int(re.match(r"\s*(\d+)", raw).group(1))
        observed[model] = counts
    return observed


def load_reference_grades():
    """Per-model list of grade labels for Run 7's 50 questions."""
    data = json.loads(GRADED_JSON.read_text())
    grades = {model: [] for model in MODEL_COLUMNS}
    for item in data:
        if item["run"] == REFERENCE_RUN and item["model"] in grades:
            grades[item["model"]].append(item["llm_grade"]["grade"])
    for model, g in grades.items():
        assert len(g) == 50, f"expected 50 graded items for {model} in {REFERENCE_RUN}, got {len(g)}"
    return grades


def bootstrap_rates(grades, n_sub, n_draws, rng):
    """Returns {category: sorted list of counts-out-of-n_sub, one per draw}."""
    counts_by_cat = {cat: [] for cat in CATEGORIES}
    pool = list(grades)
    for _ in range(n_draws):
        draw = rng.sample(pool, n_sub)
        tally = Counter(draw)
        for cat in CATEGORIES:
            counts_by_cat[cat].append(tally.get(cat, 0))
    for cat in counts_by_cat:
        counts_by_cat[cat].sort()
    return counts_by_cat


def percentile_rank(sorted_values, value):
    """Fraction of bootstrap draws <= value."""
    import bisect
    idx = bisect.bisect_right(sorted_values, value)
    return idx / len(sorted_values)


def interval(sorted_values, lo=0.05, hi=0.95):
    n = len(sorted_values)
    return sorted_values[int(n * lo)], sorted_values[min(int(n * hi), n - 1)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    observed = load_run1_observed_counts()
    reference = load_reference_grades()

    print(f"Reference pool: {REFERENCE_RUN} (n=50, fresh question set, correct seed / baseline pushback)")
    print(f"Comparing against: Run 1 (n=18, original question set, same condition)")
    print(f"Subsample size: {SUBSAMPLE_N}, draws: {args.draws}\n")

    for model in MODEL_COLUMNS:
        print(f"=== {model} ===")
        boot = bootstrap_rates(reference[model], SUBSAMPLE_N, args.draws, rng)
        for cat in CATEGORIES:
            obs_count = observed[model][cat]
            sorted_counts = boot[cat]
            lo, hi = interval(sorted_counts)
            pct = percentile_rank(sorted_counts, obs_count) * 100
            flag = "" if lo <= obs_count <= hi else "  <-- OUTSIDE 90% interval"
            print(
                f"  {cat:18s} Run1 observed={obs_count:2d}/18   "
                f"bootstrap 90% interval=[{lo},{hi}]   "
                f"Run1 percentile={pct:5.1f}%{flag}"
            )
        print()

    print(
        "Reading this: if Run 1's count falls inside the 90% interval, its rate for that\n"
        "category is consistent with n=18 sampling noise alone -- no need to invoke a\n"
        "question-set effect. A count outside the interval (flagged above) means n=18 noise\n"
        "alone is an unlikely explanation, so a real difference between the two question sets\n"
        "(or something else that changed) is the more likely story for that category."
    )


if __name__ == "__main__":
    main()
