# Pre-registration: pinned-Xiaomi plumbing audit for the Post 3 petri sweep

Date: 2026-10-12. Written before any petri audit was run on the pinned Xiaomi
endpoint. Approved by Anji 2026-10-12 at about $0.16.

## Why this exists

The valid pilot (`runs/subj00_petri_pilot/`) was served by GMICloud at bf16
with no reply length limit, and its opening reply stopped at exactly 1,024
tokens mid-sentence. The sweep will instead pin Xiaomi's first-party endpoint
(fp8) and set an explicit reply length limit. This single audit checks that
those exact sweep settings work. It is not a result and will not be reported
as one.

## Hypothesis

None tested.

## Measure

- Which provider served each target call, and reasoning tokens billed.
- Output tokens and stop reason of each target reply, and whether any reply
  ends mid-sentence or hits the limit.
- Whether the opening turn plus branches A, B and C ran, and whether every
  auditor message matches the seed exactly (`Post3/check_pilot_script.py`).
- Whether each target reply contains a score out of 10, and in what wording.
- Any reasoning-style text in visible replies, recorded verbatim.
- Per-role tokens and cost. Judge scores on the three dimensions.

## Setup

Same as the valid pilot attempt except two target settings:

- Target: openrouter/xiaomi/mimo-v2.6-flash, reasoning off, provider pinned
  to Xiaomi (fp8) with fallbacks off, max_tokens 4096.
- Seed: `Post3/petri_seeds/` (one seed, poem 06), as reworded 2026-10-08.
- Auditor: anthropic/claude-sonnet-5-5, effort medium.
- Judge: anthropic/claude-opus-5-5, effort medium.
- max_turns 12, target_tools none, rollback on, default temperature.
  1 audit, `--limit 1`.
- Log dir: `runs/subj02_petri_xiaomi_plumbing/`.

The 4096 limit was chosen as about 4 times the longest pilot reply (1,024
tokens), so it should never bind on a normal reply.

## Rule deviations, stated up front

- n=1, below the 5-runs minimum. Acceptable only because no comparison is made.
- Two settings differ from the pilot (provider, reply limit). No comparison
  with the pilot is drawn, so differences in the target's scores between the
  two audits are not evidence of anything.

## Kill conditions

- If the audit errors or the pinned provider rejects the request, log it and
  stop. No retry without a new OK.
- If cost exceeds $1, stop and re-estimate.
- Any failed call is logged, not dropped or retried silently.
