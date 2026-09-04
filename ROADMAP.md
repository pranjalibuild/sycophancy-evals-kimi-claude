# Evals skill roadmap

Built 2026-08-31. Budget assumption: 4 to 5 hours a week, so roughly 18 usable hours a month once real life takes its cut. Hour costs below are honest, not aspirational.

## The thesis this body of work argues

Do not position as "person learning to run evals." That role is crowded and the entry-level version of it is being automated.

Position as **the person who audits whether an eval measures what it claims to measure.**

That thesis is already supported by things that happened, not things you plan to do. You found a scoring-validity bug in the `inspect_evals` reference implementation, where reasoning-enabled content becomes a list of typed blocks and a naive substring check against a target letter of "C" or "T" matches the class names `ContentReasoning` and `ContentText` regardless of the model's actual answer. You wrote the acceptance criteria a third-party GenAI vendor had to clear at Coconut before you would approve it. You blocked an AI hiring-screen vendor whose marketing claims did not survive scrutiny. Same instinct, three settings.

Almost nobody occupies this position publicly. Most eval writing is either "here is my benchmark result" or academic methodology papers. The gap in between, written by someone who can also explain to a VP why the number is untrustworthy, is yours to take.

Every step below either produces evidence for that thesis or gets cut.

---

## Step 1 — Sycophancy series (in flight)

Runs 1 through 8, blog post one, plus the Position-Subjective/Explicit sequel. Governed by `TAXONOMY_MAP.md` and `run_log.csv`. Do not re-litigate that design, it is sound.

**Skills this already builds:** Inspect harness fluency, single-variable experimental design, construct grounding against a published taxonomy, LLM-as-judge scoring, multi-model comparison, debugging someone else's scorer.

**Two holes to patch before you publish, not after.**

### Hole 1: no error bars. This is the credibility risk.

n = 25, two models. The gap between a 0.40 and a 0.48 sycophancy rate at n = 25 is indistinguishable from noise. If the post reports point estimates run over run and says "escalated pushback increased sycophancy," the first competent reader asks for a confidence interval and stops reading when there isn't one. Every downstream post inherits the damage.

The fix is small. Bootstrap a 95% CI on each rate, plot runs with the intervals shown, and run a power calculation up front that tells you how large n has to be to detect the effect sizes you actually care about. If the answer is "n = 300 to detect a 10 point difference," then say so in the post and report the small runs as exploratory rather than conclusive. That sentence alone reads as more competent than a confident claim.

`scipy` and `statsmodels` are not in the venv yet. Install them.

**Cost: 6 to 8 hours.** Highest return per hour in the entire roadmap.

### Hole 2: the grader is unvalidated.

GPT-4o decides whether the model admitted a mistake, and nothing has checked whether GPT-4o agrees with you. Everything in the series rests on that judgment.

Fix: hand-grade 50 to 60 items yourself, blind to the grader's call, compute Cohen's kappa, and inspect the disagreements. Whatever the number is, it is publishable. High agreement validates the series. Low agreement is a better post than the series itself.

**Cost: 8 to 10 hours.** This is Step 3 in miniature and it doubles as the first artifact of the thesis.

### Two accuracy notes for the writeup

The baseline set is AQuA math multiple choice, not trivia. `TAXONOMY_MAP.md` and the run notes call it trivia in places. Describe it correctly in the post, because someone will open the jsonl.

Run 1 already flags that `are_you_sure.jsonl` is public and may be memorized. Keep that caveat in the post rather than burying it. It is the natural setup for Step 2.

**Step 1 revised total: roughly 45 to 55 hours including the patches, both posts, and the repo cleanup. Call it three to four months.**

---

## Step 2 — Build a dataset from scratch

You have never done this. Every run so far borrows someone else's items, with a contamination risk you already identified.

Build 100 to 150 items with verified ground truth, in a domain where you can check correctness yourself. Document construction: where items came from, how ground truth was established, what you excluded and why. Run a contamination check by asking the models to complete items from the prefix and seeing whether they recall them. Then re-run the sycophancy baseline on clean items and compare against the public set.

**Skill unlocked:** dataset construction, contamination testing, ground-truth verification. This is the line between running evals and making them.

**Artifact:** public dataset with a documented construction methodology, plus a post on what changed when contamination was removed.

**Cost: 25 to 30 hours.**

---

## Step 3 — Judge and grader methodology

The deepest current methodological problem in the field, and where Step 1's Hole 2 expands into a specialty.

Cover: human agreement baselines and kappa, judge sensitivity to grading-prompt wording, position bias in pairwise comparison, self-preference bias where a model as judge favors its own family, and the cost and reliability tradeoff between a frontier judge and a cheap one.

Concretely, take one fixed set of graded conversations and vary only the judge: GPT-4o, Claude, a small open-weight model, and you. Report where they diverge. Single-variable design again, same discipline as Step 1, applied one level up.

**Skill unlocked:** grader validation. This is the most transferable and least commoditized eval skill available to you, and it does not require ML engineering.

**Artifact:** the flagship post. This is the one that gets cited.

**Cost: 30 to 35 hours.**

---

## Step 4 — Multi-turn and agentic evals

Static single-turn question and answer is the easy case and the field has moved past it. Run 8 is the toe in the water.

Cover Inspect's multi-turn solvers, tool use, and agent scaffolds. Build one eval where the model has tools and the failure mode only appears over several turns. Sycophancy is a good vehicle: does a model that holds its position under one-shot pushback fold when the pressure is spread over five turns, and does it fold faster when it has a tool that lets it appear to defer to the user?

**Skill unlocked:** agentic eval design, trajectory scoring rather than final-answer scoring. Scoring a trajectory is meaningfully harder than scoring an answer and is where the interesting open problems are.

**Cost: 30 to 40 hours.**

---

## Step 5 — Elicitation and adversarial robustness

The discipline of not trusting your own negative result. If a model appears safe on your eval, the question is whether it is safe or whether you failed to elicit the behavior. Better scaffolding, better prompting, and adversarial search often turn a clean result dirty.

Take one of your own earlier runs where a model looked good and try to break it. Publish the before and after.

**Skill unlocked:** capability elicitation, red-teaming, and the epistemics of negative results. This is the argument that separates people who take evals seriously from people who produce leaderboards.

**Cost: 20 to 25 hours.**

---

## Step 6 — From eval result to deployment decision

Thread this through every step, do not save it for the end. It is your actual edge and no ML engineer writes it well.

The questions: what result would change a deployment decision, who owns the threshold, what happens when the number is ambiguous, how a governance gate consumes an eval without understanding its internals, and why a vendor's own eval is not evidence.

You already ran this in production. The stage-gated model at Coconut, the acceptance criteria for the GenAI summarization vendor, the pre-launch validation gate requiring manual evaluation against real customer transcripts rather than vendor proof-of-concept claims. Those are the same argument at organizational scale.

**Artifact:** one essay connecting the methodological posts to the decision layer. Publish it after Step 3, when you have earned the technical standing to make the argument without it reading as a PM avoiding the math.

**Cost: 10 to 12 hours.**

---

## Sequencing against the calendar

Months 1 to 4: Step 1 including both patches. Two or three posts out.
Months 5 to 7: Step 2 and Step 3. The flagship post lands here.
Month 7: Step 6 essay.
Months 8 to 12: Step 4, then Step 5.

Steps 1 through 3 alone are enough to be taken seriously in an evals conversation. Steps 4 and 5 are what make you competitive for a role where evals is the job rather than part of it.

## Where to publish

LessWrong and the EA Forum are where this audience reads. Cross-post to pranjalideshpande.com. Keep the repo public and clean from the start, because the repo is checked more often than the post is read.

The `.text` bug writeup is a short standalone post and it should go out first, before the full series. It is four hours of work, it is a real finding in a widely used reference implementation, and it establishes the thesis before the long posts arrive. Consider opening an issue or a PR against `inspect_evals` at the same time. A merged PR to the library everyone in the field uses is worth more than any post.

## What this does and does not qualify you for

Does not: research scientist, ML engineer, interpretability researcher. No amount of part-time study reaches those.

Does: evals and safety PM roles at labs and eval orgs, technical program management on model safety, AI assurance and audit in regulated sectors, governance roles that need someone who can read a methodology and say whether it holds, and the enablement track where "I can measure whether this vendor's model does what they claim" is rare and billable.

## Open decisions

1. Does Run 9 stay the boundary where you write the eval yourself, or does the grader-validation work in Hole 2 become that milestone instead? Hole 2 is more original and arguably the better place to take the wheel.
2. Public repo now or after post one? Recommend now. Work in the open compounds.
3. Is the PM-task human-graded eval in the taxonomy idea bank a Step 3 component, since it is fundamentally about human versus automated grading, rather than a separate project?
