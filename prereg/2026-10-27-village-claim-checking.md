# Pre-registration: do AI Village agents check each other's completion claims?

Date: 2026-10-27. Draft. Written before the AI Village dataset was opened.
Nothing below has been checked against the data's real schema.

## Why this exists

Proposed project for the AI Village $1,000 / one-month grant, deliverable a
one-page human-written report. Two stages: a feasibility pilot that decides
whether the main study is possible, then the main study. The pilot runs before
the application is sent, because applications are rolling.

## Stage 1: feasibility pilot (before applying)

### Question

Can a completion claim made in chat ("I sent the email", "the form is live",
"I updated the doc") be checked against the same agent's computer-use log?

### Measure

- For 20 completion claims sampled from one season: verifiable true,
  verifiable false, or unverifiable from the logs.
- Hours spent reaching those 20 labels.
- What the computer-use records actually contain: structured actions,
  screenshots only, or summaries.

### Kill conditions

- Fewer than 12 of 20 claims verifiable, or more than 4 hours spent: drop
  ground truth. Fall back to the uptake-only design (below) and say so in the
  application.
- No season has goals with checkable outputs: stop. Do not apply with this
  project.

Hours cap for Stage 1: 6.

## Stage 2: main study

### Hypothesis

Agents take up a peer's false completion claim without checking at roughly
the same rate as a true one. Stated so it can fail: if uptake-without-checking
is at least 15 percentage points lower for false claims than true ones, agents
are discriminating, and the hypothesis is wrong.

### Unit and sample

- One season, picked in Stage 1 for checkable goals. Named here before any
  labels: <fill after Stage 1, before Stage 2 labelling>.
- Completion claims made by one agent in group chat, extracted by keyword
  search, with a cheap model filter only if keywords give more than 50% noise
  on a 30-message hand check.
- Target n = 150 claims, hand-labelled. Random sample if extraction yields
  more. Report counts ("23 of 41"), not bare percentages.

### Labels per claim

1. Truth: true, false, or unverifiable (from the claiming agent's computer-use
   log).
2. Uptake by any other agent within the next 24 hours of village time:
   - acted on it (built on the claimed output),
   - repeated it (restated it as fact to others or to a human),
   - checked it (opened, visited or asked for evidence of the output),
   - ignored it.

### Comparison

Share of claims taken up without checking (acted on or repeated, never
checked), for false versus true claims. Unverifiable claims are reported as a
count and excluded from the comparison.

### Uptake-only fallback (if Stage 1 kills ground truth)

Same extraction and uptake labels, no truth label. Report how often any
completion claim is checked before uptake. Weaker: it shows whether agents
verify, not whether they discriminate.

### Rules

- Labels are mine, by hand. No LLM grader for the headline numbers, so the
  grader-validation problem does not apply.
- 10% of claims re-labelled a week later, blind to the first label; report
  agreement.
- Every extracted claim that is dropped is logged with a reason.
- The model behind each agent changed across seasons; the result is stated
  for the named season only.

### Kill conditions

- Fewer than 20 false claims in the sample: no comparison is possible. Report
  the uptake-only result instead.
- Re-label agreement below 80% on uptake: the labels are not reliable enough
  to report a rate.

## Budget

- Hours: about 20 (Stage 1 up to 6, labelling 8, analysis 2, writing 3).
  Displaces: <name what this pushes out of the October-November plan>.
- API: under $50, only if the model filter is needed.

## Deviations
