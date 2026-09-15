# Evals roadmap

Originally built 2026-08-31. Consolidated 2026-09-12 after the BlueDot cohort finished, replacing the original plus its September addendum. Previous versions sit in `ROADMAP.backup-2026-09-12.md`.

Budget assumption: 4 to 5 hours a week, so roughly 18 usable hours a month once real life takes its cut. Hour costs below are honest, not aspirational. **Revisit the budget now that both kids are in daycare and school.** Everything in this document scales off that number, and it was set in August when the number was smaller.

---

## Part 1 — The thesis

### What this body of work argues

Do not position as "person learning to run evals." That role is crowded and the entry-level version of it is being automated.

Position as **the person who audits whether an eval measures what it claims to measure.**

That thesis rests on things that happened, not things planned. You found a scoring-validity bug in the `inspect_evals` reference implementation, where reasoning-enabled content becomes a list of typed blocks and a naive substring check against a target letter of "C" or "T" matches the class names `ContentReasoning` and `ContentText` regardless of the model's actual answer. You wrote the acceptance criteria a third-party GenAI vendor had to clear at Coconut before you would approve it. You blocked an AI hiring-screen vendor whose marketing claims did not survive scrutiny. Same instinct, three settings.

Almost nobody occupies this position publicly. Most eval writing is either "here is my benchmark result" or an academic methodology paper. The gap in between, written by someone who can also explain to a VP why the number is untrustworthy, is yours to take.

AVERI was founded on the argument that labs should not grade their own homework. That is the same sentence as this thesis, which makes it the clearest organisational expression of the position you are building toward.

### Two archetypes, and how they combine

From the technical AI safety talent taxonomy: **iterator** runs experiments quickly and builds tight feedback loops; **amplifier** multiplies other people's work through communication, program management, and coordination. Amplifiers stay undersupplied in this field. Iterators, at the entry level, do not.

The strategy is both, in a specific order. **The amplifier work opens doors. The iterator work is the work you want to do once inside.** Facilitation, curriculum, community building, and program management get you known and get you hired. The audit trail is what separates you from a generic program manager, and it is the thing you actually enjoy.

**The failure mode of this combination has a name.** The amplifier role is what someone hires you to do. Once you hold it, the iterator work reverts to evenings and weekends, except now against a full job rather than leave. The combination only compounds if the amplifier role sits inside an organisation where eval work is already in scope. Program management at an education-focused org leaves the audit trail a hobby forever. Program or research management at AVERI, Epoch, Amii, or an eval-producing lab puts both halves in one building.

That is the single most important sentence in this document for choosing between offers.

---

## Part 2 — The opportunity filter

Run every new opportunity, grant, program, or role through these gates before it enters the plan. The list has grown three times in one month. The gates exist so that it stops.

**Gate 1. Which half does it serve?** Iterator, meaning it produces evidence for the audit thesis. Or amplifier, meaning it opens a door. If neither, cut it. If an item claims both, name which half is paying for it, because that decides how many hours it deserves.

**Gate 2. For amplifier items: does the organisation produce evals, or only teach about them?** See the failure mode above. An education org is fine for a stepping stone and wrong as a destination.

**Gate 3. What does it cost, and what does it displace?** Name the displaced item explicitly. Nothing enters the plan without something else leaving it or slipping. An 18-hour month has no slack to discover later.

**Gate 4. How good is the evidence for the mechanism?** "People who did X went on to get Y" observed in two cases with no control group is the same error you would reject in a run. Ask what the base rate is and whether anyone got Y without doing X.

**Gate 5. Does it require the work your own files say drains you?** Organisational politics, ladder climbing, meetings that signal rather than do, unpaid roles carrying real obligation. The Women in AI chapter lead failed this gate in August and withdrawing was correct.

**Gate 6. Does it produce an artifact someone outside the organisation can check?** A public repo, a published post, a merged PR. Credibility that only exists inside one org does not travel when that org has no opening.

---

## Part 3 — Publishing cadence

Weekly publishing only works with two post types. A research post at the current definition costs 20 to 25 hours. Weekly at that definition is 80 to 100 hours a month against 18, which is a five-times overrun, and the item that would break is the research, because research is the only thing here with no external deadline forcing it.

**Lab note. 1 to 2 hours. Weekly.** One finding, one thing that broke, one decision and why. No literature review, no setup walkthrough, no charts unless a chart is the finding. The `.text` bug writeup at four hours is the upper bound, and that one included filing a repo issue.

**Research post. 20 to 25 hours. Roughly quarterly.** What post 1 already is. Full methodology, gaps named up front, replication path.

Publish both on Audit Trail under a clear label. A reader who opens a two-hour note expecting post 1 will discount both.

Cross-post the research posts to LessWrong and the EA Forum, where this audience reads, and to pranjalideshpande.com. Keep the repo public and clean, because people check the repo more often than they read the post.

---

## Part 4 — The research programme

### Step 1 — Sycophancy series (in flight)

Runs 1 through 8 plus the base-model comparison. Governed by `TAXONOMY_MAP.md` and `run_log.csv`. That design is sound, do not re-litigate it.

**Skills this already builds:** Inspect harness fluency, single-variable experimental design, construct grounding against a published taxonomy, LLM-as-judge scoring, multi-model comparison, debugging someone else's scorer.

Two holes to patch before publishing further, not after.

#### Hole 1: no error bars. This is the credibility risk.

At n = 25 with two models, the gap between a 0.40 and a 0.48 sycophancy rate is indistinguishable from noise. A post reporting point estimates and claiming escalated pushback increased sycophancy invites the first competent reader to ask for a confidence interval and stop reading when there is not one. Every downstream post inherits that damage.

Fix: bootstrap a 95% CI on each rate, plot runs with intervals shown, and run a power calculation up front that says how large n must be to detect the effect sizes you care about. If the answer is n = 300 to detect a 10-point difference, say so and report the small runs as exploratory. That sentence reads as more competent than a confident claim. Install `scipy` and `statsmodels`.

**Cost: 6 to 8 hours. Highest return per hour in this document.**

#### Hole 2: the grader is unvalidated. This is now the flagship project.

GPT-4o decides whether the model admitted a mistake, and nothing has checked whether GPT-4o agrees with you. Everything in the series rests on that judgment.

Fix: hand-grade 50 to 60 items yourself, blind to the grader's call, compute Cohen's kappa, and inspect the disagreements. High agreement validates the series. Low agreement makes a better post than the series itself. At n = 50 to 60 the kappa carries a wide confidence interval, so report it as substantial agreement with a wide interval rather than as a precise figure.

**Cost: 8 to 10 hours.** This is the BlueDot Project Sprint proposal.

#### Two accuracy notes for any writeup

The baseline set is AQuA math multiple choice, not trivia. `TAXONOMY_MAP.md` and some run notes call it trivia. Describe it correctly, because someone will open the jsonl.

`are_you_sure.jsonl` is public and may be memorised. Keep that caveat in the post rather than burying it. It is the natural setup for Step 2.

### Step 2 — Build a dataset from scratch

Every run so far borrows someone else's items, with the contamination risk you already identified. Build 100 to 150 items with verified ground truth in a domain where you can check correctness yourself. Document construction: where items came from, how you established ground truth, what you excluded and why. Run a contamination check by asking models to complete items from the prefix. Then re-run the baseline on clean items and compare against the public set.

**Skill unlocked:** dataset construction, contamination testing, ground-truth verification. This is the line between running evals and making them.

**Cost: 25 to 30 hours. Deferred to 2027.**

### Step 3 — Judge and grader methodology

Where Hole 2 expands into a specialty, and the deepest current methodological problem in the field.

Cover human agreement baselines and kappa, judge sensitivity to grading-prompt wording, position bias in pairwise comparison, self-preference bias where a model judge favours its own family, and the cost-reliability tradeoff between a frontier judge and a cheap one. Concretely: take one fixed set of graded conversations and vary only the judge across GPT-4o, Claude, a small open-weight model, and yourself. Report where they diverge. Single-variable design again, one level up.

**Skill unlocked:** grader validation. The most transferable and least commoditised eval skill available to you, and it needs no ML engineering.

**Cost: 30 to 35 hours.** The Sprint delivers the first slice of this.

### Step 4 — Multi-turn and agentic evals

Static single-turn question and answer is the easy case and the field has moved past it. Cover Inspect's multi-turn solvers, tool use, and agent scaffolds. Build one eval where the model has tools and the failure mode only appears across several turns. Sycophancy is a good vehicle: does a model that holds position under one-shot pushback fold when the pressure spreads over five turns, and does it fold faster when a tool lets it appear to defer?

**Skill unlocked:** agentic eval design, trajectory scoring rather than final-answer scoring.

**Cost: 30 to 40 hours. Deferred to 2027.**

### Step 5 — Elicitation and adversarial robustness

The discipline of not trusting your own negative result. If a model looks safe on your eval, the question is whether it is safe or whether you failed to elicit the behaviour. Take an earlier run where a model looked good and try to break it. Publish before and after.

**Skill unlocked:** capability elicitation, red-teaming, the epistemics of negative results.

**Cost: 20 to 25 hours. Deferred to 2027.**

### Step 6 — From eval result to deployment decision

Thread this through every step. It is your actual edge and no ML engineer writes it well. What result would change a deployment decision, who owns the threshold, what happens when the number is ambiguous, how a governance gate consumes an eval without understanding its internals, why a vendor's own eval is not evidence.

You ran this in production already: the stage-gated model at Coconut, the acceptance criteria for the GenAI summarisation vendor, the pre-launch validation gate requiring manual evaluation against real customer transcripts rather than vendor proof-of-concept claims.

**Cost: 10 to 12 hours.** Publish after Step 3, when you have earned the standing to make the argument without it reading as a PM avoiding the math.

---

## Part 5 — Amplifier track

### BlueDot facilitation — applying now, October cohorts

**Why this is in the plan.** Three reasons, and they are not equally strong. First, BlueDot's rapid grants page states that priority goes to course participants, alumni, facilitators, and active community members, so facilitation moves you up a list the funder publishes. Second, observed cases of people who facilitated and then received the career transition grant, which is the door-opening hypothesis. Third, it scratches the AI literacy itch that has been in your profile for years.

Gate 4 applies to the second reason. You observed a couple of people, you are already a participant and an alum on that same priority list, and you do not know the base rate. Find out whether anyone received the grant without facilitating before you weight this heavily. The first and third reasons hold on their own regardless.

**Cost:** paid, and stated at 5 hours per cohort. Confirm that number. BlueDot's public course page describes the part-time format as roughly 6 weeks at 5 hours a week with a 2-hour Zoom discussion each week led by the facilitator, and 12 hours of live session does not fit inside 5 hours per cohort. If the real figure is 5 hours a week, that is 30 hours per cohort, which equals the entire Project Sprint and cannot run in the same window.

**How to position the application.** Invert the usual shape. Most applicants dispatch facilitation in a sentence and spend the rest proving technical credibility. You have the opposite problem, so spend the space on rooms you have actually run: a governance committee with rotating moderation, synthesis across levels from engineer to CEO, 60 user interviews at AWS and 30 to 40 at Coconut, a 7-person team built from scratch, a designed and delivered workshop. Then settle the technical question fast and concretely: graduated the cohort, published an eval series, found a scoring-validity bug in the reference implementation everyone uses, ran eight controlled experiments on frontier models.

**Name the difference rather than claiming the skills are identical.** Your fifteen years is stakeholder alignment: competing interests, a decision to reach, convergence as the goal. A cohort discussion is eight strangers with no shared stake and no decision on the table, and the facilitator opens thinking up rather than driving it to a conclusion. Acknowledging that gap convinces more than papering over it.

**One flag from your own profile.** It lists moderating meetings among what you are good at and then says you do not particularly enjoy it. This role is a two-hour moderated discussion weekly for six weeks. It may dissolve on inspection, since what drains you is politics and signalling and a cohort carries neither. Check before committing rather than after.

### Facilitation may replace the curriculum track, not add to it

The list currently carries a separate literacy track: a rapid grant to build AI safety curriculum for universities or schools, plus AI literacy projects and curriculum design for Canadian schools. If a six-week cohort using materials someone else wrote scratches this itch, then building curriculum from scratch is a far more expensive way to scratch the same one. **Decide whether facilitation stands in for that track.** That is the version where this list gets shorter.

The same question applies to the "curriculum and AI literacy design for Canadian schools and universities" line on the one-pager. Is that a role you want, or the thing facilitation already gives you?

### Grants

**BlueDot Rapid Grant. Cost: under an hour.** Up to $10,000, a five-minute application, most decisions inside a day and 90% inside a week. Target it at API spend for grader validation, where 50 to 60 conversations run through four judges. Ask for what the runs cost rather than a round number. Do this regardless of everything else in this document.

**BlueDot Career Transition Grant. Cost: 4 to 6 hours.** Funds continued research. Sequence it after facilitation is on the record, per the door-opening hypothesis, and after the Sprint is underway so the application describes work in progress rather than work you intend.

**Diversify the funders.** The current plan has one funder and one prospective employer. Coefficient Giving runs career development and transition funding, and the Long-Term Future Fund backs independent research. A second funder costs a few hours and removes the single point of failure.

### SPAR

Missed the Fall 2026 deadline. Apply for spring. The shortlisted project slate skews toward governance research: AI constitutions compliance mapping, AI Safety Fieldmap, Middle-Power AI Safety Institutes, Commitment Atlas. Direct outreach to project leads remains an option in the meantime.

---

## Part 6 — Current commitments and sequence

### In flight right now

| Item | State | Next action |
|---|---|---|
| BlueDot Technical AI Safety | Graduated 2026-09-11 | One-pager submitted for the certificate |
| Audit Trail post 2 (base models via ACS Infra vs RLHF'd chat) | Publishing 2026-09-12 | Ship it |
| ACS Research, product role | Cleared round 1, awaiting interview decision | Post 2 is the credibility artifact for this lab |
| 80,000 Hours, Talent Database Lead | Technical assessment received, paid, 90 minutes | Monday 2026-09-14, once kids are back |
| BlueDot facilitator, October cohorts | Applying within two days | Confirm the hours figure while applying |
| BlueDot Project Sprint | Applications close 2026-09-27 | Propose grader validation |
| BlueDot Rapid Grant | Not started | This week, under an hour |
| `inspect_evals` `.text` bug | Found, written up, not filed upstream | File the issue or PR |

### Sequence through the rest of 2026

**This week.** Rapid Grant application. Facilitator application. File the `inspect_evals` issue, which turns your strongest claim into a link anyone can check. First lab note.

**Monday 2026-09-14.** 80,000 Hours assessment. Ninety minutes, protected time.

**Before 2026-09-27.** Project Sprint application, proposing grader validation.

**October and November.** Sprint runs, with grader validation as the project. Facilitate a cohort if accepted. Weekly lab notes. Patch Hole 1 while the Sprint runs, since error bars cost 6 to 8 hours and raise the credibility of everything. One research post at the end, which doubles as the Sprint deliverable.

**November.** Career transition grant, written against Sprint results. Second funder application.

**December.** Step 6 essay if the hours exist. Review what the offer picture looks like.

### What this pushes out

Steps 2, 4 and 5 all move to 2027. Dataset construction, multi-turn and agentic evals, elicitation and adversarial robustness. That is the honest consequence of adding five amplifier items to an 18-hour month, and writing it down now beats discovering it in February.

---

## Part 7 — The masters question, closed for now

SFU's Computing Science MSc admits new students to the thesis option only; the department closes the project and course-based options to incoming students. Six semesters, supervisory committee by semester three, and guaranteed funding of $24,000 a year for two years paid through teaching assistantships and fellowships, which assumes a full-time student who is not working elsewhere. Part-time enrolment appears nowhere in the materials.

SFU's alternatives are course-based professional masters in Big Data, Visual Computing and Cybersecurity, plus graduate diplomas in each. None is research.

UBC's CS department runs an explicit part-time master's designed for people who keep working, with either thesis or course-based tracks. But the department funds no part-time students, no supervising faculty member normally funds their research, and courses meet twice weekly for 75 minutes, daytime, on the Point Grey campus, with nothing in the evenings, on weekends, or by distance.

**The decision, and the reasoning behind it.** A masters at either school puts your research training in the hands of one supervisor whose area almost certainly is not AI safety, on top of CS coursework you largely already hold. Two years for a credential and a thesis in someone else's problem. The field built its own on-ramps precisely because this route is slow: ARENA, MATS, Astra, the Anthropic Fellows programme, LASR, SPAR. Those run in months and select on demonstrated work rather than transcripts, which is the currency you are already accumulating.

**Held as a December fallback only.** If the offer picture in December produces nothing you want, a funded full-time MSc becomes a coherent two-year plan rather than something squeezed around a job. SFU's Fall 2027 MSc applications open 2026-10-01 and the deadline is unposted; comparable rounds closed in January. The long pole is a supervisor, not the application, and that outreach takes months. So if December says yes to this, the work starts immediately and not in the spring.

**On ARENA.** It is the right curriculum for mechanistic interpretability, which this document says you are not targeting. Read the sections on evals and model behaviour. Skip the full interpretability track, and treat it as reading rather than as a credential.

---

## Part 8 — What this qualifies you for

**Does not:** research scientist, ML engineer, interpretability researcher. No amount of part-time study reaches those, and the masters is the only item that could ever rewrite this sentence.

**Does:** evals and safety PM roles at labs and eval orgs, technical program management on model safety, research management, AI assurance and audit in regulated sectors, governance roles that need someone who can read a methodology and say whether it holds, curriculum and literacy work, and the enablement track where "I can measure whether this vendor's model does what they claim" is rare and billable.

---

## Part 9 — Open decisions

1. **Is the 18-hour budget still right** now that both kids are in daycare and school? Everything above scales off it and the number was set in August.
2. **Facilitator hours: 5 per cohort, or 5 per week?** The answer decides whether facilitation runs alongside the Sprint or instead of it.
3. **Does facilitation replace the curriculum-building track,** including the rapid grant for school and university curriculum and the curriculum line on the one-pager?
4. **What is the base rate on the facilitation-to-grant pattern?** Did anyone receive the career transition grant without facilitating?
5. **Lab notes on Audit Trail under a separate label, or a separate feed?** Same site with a clear label is cheaper and probably right.
6. **Public repo cleanup before or after post 2?** Work in the open compounds, so before.
7. **Does the Run 9 write-your-own-eval milestone survive,** or does grader validation become that milestone instead? Grader validation is more original and a better place to take the wheel.
8. **Is the PM-task human-graded eval in the taxonomy idea bank a Step 3 component,** since it is fundamentally about human versus automated grading, rather than a separate project?

---

## Appendix A — Grant application question log

**How to use this.** Every time you open a grant application, paste its questions here with the funder's name and the date. Over three or four applications the same questions repeat, and Appendix B grows into a library that means you never start from a blank page again. Log the question even when you answer it well, because next time you will not remember how you phrased it.

Format: funder, date seen, the question verbatim, word limit, and a pointer to the Appendix B block that answers it.

### BlueDot Rapid Grant
*(Application is short, reportedly about five minutes. Log the actual fields when you open it.)*

- Questions:
- Word limits:
- Answered from:

### BlueDot Career Transition Grant
*(Log when you open it.)*

- Questions:
- Word limits:
- Answered from:

### Coefficient Giving, career development and transition funding
*(Log when you open it.)*

- Questions:
- Word limits:
- Answered from:

### Long-Term Future Fund
*(Log when you open it.)*

- Questions:
- Word limits:
- Answered from:

### Questions to expect, based on how these applications usually read

Pre-answered in Appendix B. Add to this list as reality corrects it.

1. What will you do? Describe the project.
2. Why does it matter? What changes if it works?
3. Why are you the person to do it?
4. What will you produce, and by when?
5. What do you need the money for, specifically?
6. How will you know whether it worked?
7. What would you do without this funding?
8. What are the main risks, and what happens if the project fails?
9. Who else works on this, and why has nobody done it already?
10. What is your longer-term plan, and how does this fit into it?

---

## Appendix B — Reusable answer blocks

Written 2026-09-12 from the body of this roadmap. Edit these in place as the work progresses rather than rewriting them per application. Every number here is real, so keep it that way.

### B1. The project, in two sentences

Grader validation. My published sycophancy eval relies on GPT-4o to judge whether a model caved under user pushback, and nobody has checked whether that judgment matches a human's, so I will hand-grade 50 to 60 of the same conversations blind and measure agreement with Cohen's kappa. Then I will hold the conversations fixed and vary only the judge across GPT-4o, Claude, a small open-weight model, and myself, to find where automated graders disagree with each other and with me.

### B2. Why it matters

Almost every published eval result now depends on a model grading another model, and the grader is usually unvalidated. If judges disagree in patterned ways, then a reported sycophancy rate is partly a property of which judge the author happened to pick rather than a property of the model under test. That makes a whole class of published numbers less informative than they look, and it is cheap to check and rarely checked. Independent audit of evals is becoming a load-bearing question in AI safety, and AVERI was founded on exactly this argument, that labs should not grade their own homework.

### B3. Why me

- I found a scoring-validity bug in the `inspect_evals` reference implementation, where reasoning-enabled content becomes a list of typed blocks so a substring check against a target letter of "C" or "T" matches the class names `ContentReasoning` and `ContentText` regardless of the model's answer.
- I have already run and published an eight-run single-variable eval series on Claude Sonnet 5 and Kimi K2, with the methodology gaps named in the post rather than left for a reader to find. Repo and run logs are public.
- I graduated BlueDot's Technical AI Safety course, September 2026.
- Before this I spent twelve years as a product manager at AWS, PayPal and Coconut Software, after six years as a software engineer. At Coconut I wrote the acceptance criteria a third-party GenAI vendor had to clear before I would approve it, blocked an AI hiring-screen vendor whose marketing claims did not survive scrutiny, and defined a pre-launch gate requiring manual evaluation of model output against real customer transcripts instead of vendor proof-of-concept claims.
- The instinct behind all of that is the same one this project uses: do not accept a measurement without checking what it measures.

### B4. Deliverables

- A published methodology post reporting the human-versus-grader agreement, the disagreement cases, and where the four judges diverge.
- A public repo with the hand-grading labels, the grading prompts, the per-judge outputs, and the analysis code, so anyone can rerun it.
- Weekly lab notes while the work is in progress, so the reasoning is visible and not just the conclusion.
- If the divergence is large enough to matter, a short guidance note on what an eval author should report about their grader.

### B5. Timeline

- Hand-grading and kappa: 8 to 10 hours.
- Multi-judge comparison: the first slice inside the same window, the full version 30 to 35 hours.
- Confidence intervals and a power calculation across the existing series: 6 to 8 hours, and the highest return per hour in this roadmap.
- At 4 to 5 hours a week this lands over roughly two to three months. October through December 2026.

### B6. What the money is for

Compute and API spend, which is the binding constraint. Be specific rather than round:

- Re-running 50 to 60 conversations through four judges, plus reruns when a grading prompt changes.
- Frontier API calls for GPT-4o and Claude as judges.
- Open-weight model inference for the cheap-judge comparison.
- Headroom to scale n toward the 300-sample floor described in Perez's empirical alignment research tips, since small-n runs risk reading noise as a trend.

**Before submitting: compute this from the actual token counts in `run_log.csv` and price it. Do not guess.**

### B7. How I will know it worked

The project produces a usable result in every direction, which is the point of choosing it:

- **High agreement** validates the existing series and gives eval authors a reason to trust a frontier judge for this task. Publishable as a validation note.
- **Low agreement** is the more interesting finding and a better post than the series itself, because it says the construct the grader scores is not the construct I defined.
- **Patterned divergence between judges** is the strongest outcome, because it generalises past my series to anyone using LLM-as-judge.

The failure mode to name honestly: at n = 50 to 60 the kappa carries a wide confidence interval, so the honest report is substantial agreement with a wide interval rather than a precise figure. I will say that plainly rather than presenting a clean number.

### B8. What I would do without the funding

Run it smaller. Fewer judges, cheaper models, and a smaller sample, which widens the intervals and weakens the claim without killing the project. The hand-grading costs nothing but my time and happens either way. Funding buys the multi-judge comparison at a sample size that supports a conclusion rather than a hint.

### B9. Risks

- **The grader agrees closely and the post is thin.** Mitigated by the multi-judge arm, which produces a finding regardless of how the human comparison lands.
- **Hand-grading 50 to 60 items is tedious and slips.** Mitigated by the BlueDot Project Sprint structure, which puts a weekly check-in and an external deadline on it.
- **My own grading is biased because I designed the eval.** Mitigated by grading blind to the model's call and by publishing the labels so someone else can disagree with me.
- **Sample size is too small for a confident claim.** Named in the writeup rather than hidden, with a power calculation stating what n would be needed.

### B10. Longer-term plan

This is step one of a specialty rather than a one-off. After grader methodology comes building a dataset from scratch with verified ground truth and a contamination check, then multi-turn and agentic evals where you score a trajectory instead of a final answer, then elicitation and adversarial robustness, which is the discipline of not trusting your own negative result. Threaded through all of it is the piece no ML engineer writes well: how an eval result becomes a deployment decision, who owns the threshold, and why a vendor's own eval is not evidence. I ran that second part in production at Coconut before I could do the first part.

### B11. One-line descriptions, for forms with tight limits

- **15 words:** I check whether AI evaluations measure what they claim, starting with the graders nobody validates.
- **30 words:** I audit AI evaluations. Most now depend on one model grading another, and that grader is rarely checked against a human. I am checking mine, publicly, and publishing what I find.
- **Project title options:** "Who grades the grader?" · "Validating LLM-as-judge in a sycophancy eval" · "The unvalidated grader problem"
