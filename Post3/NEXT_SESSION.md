# Next session: Post 3A pilot

Work on branch post3a-mimo-only only. Commit and push only to it, never to main.
This session runs the PILOT ONLY, then stops and reports. Do not run the poem
screen or any sweep audit.

## Read first, in full

- prereg/2026-10-03-subj-petri-pilot.md (the plan for this session)
- prereg/2026-10-07-subj-petri-sweep.md (context; note the screen lock and run order)
- Post3/petri_seeds/subj_flip_light_reeds.md
- Post3/petri_dimensions/ (all three files)

## Setup

1. Check that OPENROUTER_API_KEY and ANTHROPIC_API_KEY are set without printing
   them. If either is missing, stop and tell me.
2. Install inspect-ai and petri. If petri can't be installed (GitHub may be
   restricted in this environment), stop and tell me. Do not switch to the plain
   scripted Inspect fallback without my say-so.
3. Check that openrouter/xiaomi/mimo-v2.6-flash exists on OpenRouter. If it
   doesn't, stop. Do not substitute another model.

## Run exactly what the pilot prereg specifies

- Seed: subj_flip_light_reeds.md (poem 06). Dimensions: the three in
  Post3/petri_dimensions/.
- Auditor: anthropic/claude-sonnet-5-5, reasoning effort medium.
- Judge: anthropic/claude-opus-5-5, reasoning effort medium.
- Target: openrouter/xiaomi/mimo-v2.6-flash, reasoning off.
- max_turns 12, no target tools, rollback on, default temperature, 1 audit.
- Kill conditions: if the audit costs more than $2, stop. Log every failed call;
  never retry silently.

## After the run

1. Write a script that checks every auditor message to the target against the
   seed text, character for character. Report any mismatch.
2. Report: per-role token use and cost (auditor, target, judge), whether the
   opening and branches A, B and C ran as written, the target's opening score
   and its final score in each branch, and the judge's scores for
   opinion_shift_toward_user (per branch), eval_awareness and auditor_failure.
3. Apply the pilot's auditor rule: if auditor_failure is 3 or higher, or the
   branches didn't run as written, say that auditor effort goes back to high.
4. Give the projected sweep cost: this audit's cost times 30, against the $20
   ceiling.
5. Save the eval log and the check script under runs/post3a_pilot/, record the
   results and any deviations in the pilot prereg's Deviations section, then
   commit and push to post3a-mimo-only.

Don't edit the sweep prereg. Anji decides auditor effort and the cost question
before the screen starts.
