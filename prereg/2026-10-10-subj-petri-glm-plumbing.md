# Pre-registration: GLM plumbing audit for the Post 3 petri sweep

Date: 2026-10-10. Written before any petri audit was run against GLM-5.3-Flash.
Approved by Anji 2026-10-10 at about $0.16.

## Why this exists

The pilot (`prereg/2026-10-03-subj-petri-pilot.md`) covered MiMo only. This is
the same single plumbing check for the second sweep target, and the first use
of a pinned first-party OpenRouter endpoint. It is not a result and will not be
reported as one.

## Hypothesis

None tested.

## Measure

- Whether the audit runs at all with the provider pinned to Z.AI and reasoning
  off, and which provider actually served each target call.
- Whether the opening turn plus branches A, B and C ran, and whether every
  auditor message matches the seed exactly (`Post3/check_pilot_script.py`).
- Whether each target reply contains a score out of 10, and in what wording.
- Reasoning tokens billed, and any reasoning-style text in visible replies,
  recorded verbatim.
- Stop reason and output token count of each target reply.
- Per-role tokens and cost. Judge scores on the three dimensions.

## Setup

Identical to the valid pilot attempt except the target:

- Seed: `Post3/petri_seeds/` (one seed, poem 06), as reworded 2026-10-08.
- Target: openrouter/z-ai/glm-5.3-flash, reasoning off, provider pinned to
  Z.AI (fp8) with fallbacks off.
- Auditor: anthropic/claude-sonnet-5-5, effort medium.
- Judge: anthropic/claude-opus-5-5, effort medium.
- max_turns 12, target_tools none, rollback on, default temperature, no
  max_tokens set. 1 audit, `--limit 1`.
- Log dir: `runs/subj01_petri_glm_plumbing/`.

## Rule deviations, stated up front

- n=1, below the 5-runs minimum. Acceptable only because no comparison is made.
- Two things differ from the MiMo pilot (target model, and provider pinning).
  No comparison between the two pilots is drawn, so this is not a
  one-variable comparison and is not treated as one.

## Kill conditions

- If the audit errors, or the pinned provider rejects the request, log it and
  stop. No retry without a new OK.
- If cost exceeds $1, stop and re-estimate.
- Any failed call is logged, not dropped or retried silently.
