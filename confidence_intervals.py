"""
Error bars for Post 1 (Runs 1-7). Closes the gap Post 1 names in its limitations
section: "I haven't computed [a confidence interval]".

No new model calls. Reads each run's results_combined.csv and reports, for the
headline metric (second-answer-incorrect rate among originally-correct answers):

1. Per run, per model: the rate with a 95% Wilson interval and a 95% percentile
   bootstrap interval (resampling questions).
2. Paired comparisons for the claims Post 1 makes. Runs 4 vs 5 and Runs 6 vs 7
   use the same questions, so each question is its own control: the difference
   is computed on questions the model got right in both runs, with a bootstrap
   CI and an exact McNemar test on the discordant pairs. Run 3's non-math subset
   vs Run 4 is the same 40 questions with escalated pushback.
3. Claude vs Kimi within each run, paired on questions both models got right.
4. A power calculation: how many originally-correct questions per condition an
   unpaired comparison needs to detect a 10-point difference at 80% power.

Usage:
    python3 confidence_intervals.py [--boot 10000] [--seed 0]
Writes confidence_intervals_results.json next to this script.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_confint, proportion_effectsize

RUNS = {
    1: "runs/run01_10q_pilot",
    2: "runs/run02_25q_stratified_baseline",
    3: "runs/run03_question_type_variation",
    4: "runs/run04_escalated_pushback_nonmath",
    5: "runs/run05_authority_claim_pushback",
    6: "runs/run06_pushback_at_scale",
    7: "runs/run07_pushback_at_scale_authority",
}
MODELS = {"anthropic/claude-sonnet-5": "Claude", "openrouter/moonshotai/kimi-k2": "Kimi"}

# (label, run_a, run_b) -- same questions in both runs, one variable changed
PAIRED_RUN_COMPARISONS = [
    ("Run 3 non-math -> Run 4 (escalated pushback)", 3, 4),
    ("Run 4 -> Run 5 (escalated -> authority claim)", 4, 5),
    ("Run 6 -> Run 7 (escalated -> authority claim, n=100)", 6, 7),
]


def load(run):
    d = pd.read_csv(Path(RUNS[run]) / "results_combined.csv")
    d["model"] = d["model"].map(MODELS)
    d["correct"] = d["original_answer_correct"] == "C"
    d["sai"] = d["second_answer_incorrect"].astype(bool)
    return d


def boot_ci(values, n_boot, rng):
    """Percentile CI for the mean of a 0/1 array, resampling items."""
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return (float("nan"), float("nan"))
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    means = values[idx].mean(axis=1)
    return tuple(float(x) for x in np.percentile(means, [2.5, 97.5]))


def paired(a, b, n_boot, rng):
    """a, b: aligned 0/1 arrays for the same items. Returns diff (b - a), CI, McNemar p."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    diff = b - a
    only_a, only_b = int(((a == 1) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())
    discordant = only_a + only_b
    p = binomtest(only_b, discordant, 0.5).pvalue if discordant else 1.0
    lo, hi = boot_ci(diff, n_boot, rng)
    return {
        "n_items": int(len(a)),
        "rate_a": float(a.mean()),
        "rate_b": float(b.mean()),
        "diff_b_minus_a": float(diff.mean()),
        "diff_ci95": [lo, hi],
        "only_a": only_a,
        "only_b": only_b,
        "mcnemar_exact_p": float(p),
    }


def pct(x):
    return f"{100 * x:5.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    data = {r: load(r) for r in RUNS}
    out = {"per_run": [], "paired_runs": [], "claude_vs_kimi": [], "power": {}}

    print("1. Second-answer-incorrect rate, originally-correct questions only\n")
    print(f"{'run':>3} {'model':<7} {'k/n':>7} {'rate':>6}  {'Wilson 95%':<17} {'bootstrap 95%':<17}")
    for r, d in data.items():
        for m in MODELS.values():
            v = d[(d.model == m) & d.correct].sai.to_numpy()
            k, n = int(v.sum()), len(v)
            w = proportion_confint(k, n, alpha=0.05, method="wilson")
            b = boot_ci(v, args.boot, rng)
            print(f"{r:>3} {m:<7} {f'{k}/{n}':>7} {pct(k / n)}  [{pct(w[0])}, {pct(w[1])}]  [{pct(b[0])}, {pct(b[1])}]")
            out["per_run"].append({"run": r, "model": m, "k": k, "n": n, "rate": k / n,
                                   "wilson_ci95": list(w), "bootstrap_ci95": list(b)})

    print("\n2. Same questions, one variable changed (paired on questions correct in both runs)\n")
    for label, ra, rb in PAIRED_RUN_COMPARISONS:
        for m in MODELS.values():
            a = data[ra][(data[ra].model == m) & data[ra].correct].set_index("question").sai
            b = data[rb][(data[rb].model == m) & data[rb].correct].set_index("question").sai
            common = a.index.intersection(b.index)
            res = paired(a[common], b[common], args.boot, rng)
            res.update({"comparison": label, "model": m})
            out["paired_runs"].append(res)
            print(f"{label:<55} {m:<7} n={res['n_items']:>3}  {pct(res['rate_a'])} -> {pct(res['rate_b'])}  "
                  f"diff {res['diff_b_minus_a']:+.2f} [{res['diff_ci95'][0]:+.2f}, {res['diff_ci95'][1]:+.2f}]  "
                  f"McNemar p={res['mcnemar_exact_p']:.3f} ({res['only_a']} vs {res['only_b']} discordant)")

    print("\n3. Claude vs Kimi, paired on questions both models originally got right\n")
    for r, d in data.items():
        c = d[(d.model == "Claude") & d.correct].set_index("question").sai
        k = d[(d.model == "Kimi") & d.correct].set_index("question").sai
        common = c.index.intersection(k.index)
        res = paired(c[common], k[common], args.boot, rng)
        res.update({"run": r})
        out["claude_vs_kimi"].append(res)
        print(f"Run {r}  n={res['n_items']:>3}  Claude {pct(res['rate_a'])}  Kimi {pct(res['rate_b'])}  "
              f"Kimi-Claude {res['diff_b_minus_a']:+.2f} [{res['diff_ci95'][0]:+.2f}, {res['diff_ci95'][1]:+.2f}]  "
              f"McNemar p={res['mcnemar_exact_p']:.3f}")

    print("\n3b. Failure composition (Findings 2 and 3), paired on questions correct in both runs\n")
    out["composition_paired"] = []
    for label, ra, rb in PAIRED_RUN_COMPARISONS[1:]:
        for m in MODELS.values():
            a = data[ra][(data[ra].model == m) & data[ra].correct].set_index("question").flip_type
            b = data[rb][(data[rb].model == m) & data[rb].correct].set_index("question").flip_type
            common = a.index.intersection(b.index)
            for kind, types in (("genuine_wrong", {"genuine_wrong_answer"}),
                                ("deflect_or_hedge", {"deflection", "ambiguous_hedge"})):
                res = paired(a[common].isin(types), b[common].isin(types), args.boot, rng)
                res.update({"comparison": label, "model": m, "outcome": kind})
                out["composition_paired"].append(res)
                print(f"{label:<55} {m:<7} {kind:<17} {pct(res['rate_a'])} -> {pct(res['rate_b'])}  "
                      f"diff {res['diff_b_minus_a']:+.2f} [{res['diff_ci95'][0]:+.2f}, {res['diff_ci95'][1]:+.2f}]  "
                      f"McNemar p={res['mcnemar_exact_p']:.3f}")

    print("\n3c. Claude genuine-wrong rate, pooled across Runs 3-7 (Finding 3)\n")
    gw = sum(int((data[r][(data[r].model == "Claude") & data[r].correct].flip_type == "genuine_wrong_answer").sum())
             for r in (3, 4, 5, 6, 7))
    gn = sum(int(((data[r].model == "Claude") & data[r].correct).sum()) for r in (3, 4, 5, 6, 7))
    w = proportion_confint(gw, gn, alpha=0.05, method="wilson")
    out["claude_genuine_wrong_pooled"] = {"k": gw, "n": gn, "wilson_ci95": list(w)}
    print(f"  {gw}/{gn} = {pct(gw / gn)}  Wilson 95% [{pct(w[0])}, {pct(w[1])}]  "
          "(pooled responses, not independent questions: Runs 4/5 and 6/7 reuse questions)")

    print("\n4. Power: originally-correct questions needed PER CONDITION (unpaired, two-sided, alpha=0.05, 80% power)\n")
    power = NormalIndPower()
    for base in (0.2, 0.3, 0.4):
        for delta in (0.10, 0.15):
            h = abs(proportion_effectsize(base + delta, base))
            n = power.solve_power(effect_size=h, alpha=0.05, power=0.8, ratio=1.0)
            out["power"][f"{base:.2f}->{base + delta:.2f}"] = int(np.ceil(n))
            print(f"  detect {pct(base)} -> {pct(base + delta)}: n = {int(np.ceil(n))}")

    Path("confidence_intervals_results.json").write_text(json.dumps(out, indent=2))
    print("\nWrote confidence_intervals_results.json")


if __name__ == "__main__":
    main()
