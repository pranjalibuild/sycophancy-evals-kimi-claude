# Pre-registration: does Ragas faithfulness agree with human hallucination labels?

Date: 2026-10-30. Draft. Written before any Ragas run or any RAGTruth item was
opened. Nothing below has been checked against the dataset's real schema or
the installed Ragas version's API.

## Why this exists

First case study for the eval-audit practice. Product teams ship RAG features
gated on an off-the-shelf faithfulness score without checking that the score
agrees with a human. This audits that one metric the way a client engagement
would: against human labels, at the thresholds teams actually use, and
including whether it gives the same answer twice.

The claim under audit is the one teams make, not the one Ragas makes. Ragas
says faithfulness measures whether the answer's claims are supported by the
retrieved context. Teams use it as "hallucination rate." Where those two
differ is part of the finding.

## Stage 1: plumbing pilot

### Question

Can RAGTruth items run through a pinned Ragas version end to end, and do the
labels map cleanly onto a binary faithful / unfaithful?

### Measure

- 20 items from the RAGTruth QA subset, 10 labelled hallucinated, 10 clean.
- Ragas version, judge model, and the exact decomposition and verification
  prompts it sends, saved to the run folder.
- Cost per item, seconds per item, hours spent.
- Whether a RAGTruth item gives question, context and response as separate
  fields, or needs reconstruction.

### Kill conditions

- Context has to be reconstructed by hand for more than 3 of 20 items: switch
  to a different labelled set (HaluBench or similar), re-run Stage 1, log the
  deviation.
- More than 5 hours on Stage 1: stop and write up what broke as a lab note.

Hours cap for Stage 1: 5.

## Stage 2: main audit

### Ground truth

- RAGTruth QA subset, test split. Response-level label: any annotated
  hallucination span means unfaithful; no span means faithful.
- I re-label a random 50 of the 200 myself, blind to RAGTruth's label, before
  looking at any Ragas score. RAGTruth's labels are audited too, not assumed.

### Sample

- n = 200: 100 unfaithful, 100 faithful, random within each stratum.
- Within the unfaithful 100, record RAGTruth's hallucination type for each
  item (baseless information vs. conflict with context, evident vs. subtle).
- Stratifying fixes prevalence at 50%. TPR and TNR do not depend on
  prevalence; any precision figure is re-weighted to RAGTruth's natural
  prevalence and labelled as such.

### Judge models

Two, named here before running:
- Cheap model a product team would default to: <name before Stage 2>.
- Strong model: <name before Stage 2>.

Two models separate "the metric's design fails" from "this judge model
fails."

### Measures

1. **Agreement.** TPR (unfaithful items scored below threshold) and TNR
   (faithful items scored at or above threshold), at three thresholds fixed
   now: 0.5, 0.8, and 1.0 (any unsupported claim fails the item). Also ROC
   AUC. Counts reported with every rate ("61 of 100").
2. **Stability.** Each item scored 3 times per judge model. Report the share
   of items whose pass/fail flips across runs at each threshold, and the
   spread of the raw score.
3. **Failure modes.** Every disagreement with ground truth at threshold 0.8
   is open-coded by hand, then grouped. Codes expected, not imposed:
   decomposition dropped the hallucinated claim; claim kept but verdict
   wrong; claim not checkable against context; ground-truth label wrong.

### Hypothesis

At threshold 0.8 with the cheap judge, Ragas faithfulness catches fewer than
75 of 100 unfaithful items, and the misses concentrate in the subtle
hallucination types. Stated so it can fail: TPR at or above 0.75, or misses
spread evenly across types, and the hypothesis is wrong. A clean result gets
published with the same weight as a damning one.

### Rules

- Thresholds, sample, models and Ragas version fixed before Stage 2 runs. No
  threshold chosen after seeing scores. Any change goes in Deviations.
- Ragas version pinned; prompts and raw judge outputs saved per item.
- Input hashes recorded for the 200-item sample, as in subj04.
- Failure-mode codes are mine, by hand. No LLM grades the disagreements.
- 10% of failure-mode codes re-coded a week later, blind; report agreement.

### Kill conditions

- My blind re-label agrees with RAGTruth on fewer than 40 of 50: RAGTruth's
  labels are not reliable enough to be ground truth. Switch ground truth to
  my own labels on 100 items, report both, log the deviation.
- Stability flip rate above 20% at threshold 0.8: lead the write-up with
  stability, because agreement numbers from a single run would then be noise.

## Known limitations, named before running

- RAGTruth responses come from 2023-era models. Their hallucinations may be
  cruder than a current model's, which would flatter Ragas. The result holds
  for this corpus, not for any team's production traffic.
- RAGTruth has been public since January 2024; either judge model may have
  seen it.
- Faithfulness to context is not correctness. An answer that faithfully
  repeats wrong context passes. Out of scope here, said once in the post.
- One metric, one library. DeepEval and promptfoo are follow-ups, not this
  study.

## Budget

- Hours: about 20 (Stage 1 up to 5, blind re-label 3, failure-mode coding 5,
  analysis 2, writing 5). Displaces: <name what this pushes out of the
  November plan>.
- API: 200 items x 2 judges x 3 runs, two or more calls each, so at least
  2,400 calls. Estimate the dollar figure from Stage 1's cost per item before
  starting Stage 2.

## Deviations
