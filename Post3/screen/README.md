# Post 3A poem screen

Rules: `prereg/2026-10-07-subj-petri-sweep.md` (Setup: candidate pool, screen
method, screen prompts, random draw; Kill conditions). The first screen call
locks that file: after it, only the final poem list and the below-6 count may be
filled in.

## What it does

For each of the 45 candidates in `Post3/poems/poems_meta.json`:

- 1 recognition call, temperature 0.
- 5 score calls at default temperature, each the seed's opening message with the
  poem. A reply with no score gets the seed's re-ask once.

All calls use the sweep's exact target settings: `openrouter/xiaomi/mimo-v2.6-flash`,
provider Xiaomi only, fp8, fallbacks off, reasoning off, max_tokens 4096 (copied
from the 2026-10-12 plumbing log).

270 calls. Worst case, every score call re-asked and every reply at 4096
tokens: about 495 calls, about $0.75 at MiMo's prices, so the $2 screen ceiling
cannot be reached. The analysis step still checks it.

## Run (repo root, with OPENROUTER_API_KEY set)

1. `git pull origin post3a-mimo-only`
2. Screen:
   `inspect eval Post3/screen/screen_task.py --log-dir runs/subj03_poem_screen`
3. Analyse:
   `python Post3/screen/analyze_screen.py runs/subj03_poem_screen/<log>.eval`
   This writes `screen_replies.csv`, `hand_read.csv`, `hand_read.md` and
   `screen_cost.txt` next to the log. Commit and push all of them plus the log
   before the hand read.
4. Hand read: read `hand_read.md`, fill in `hand_read.csv`
   (`hand_recognised` y/n on every row; `hand_score` where the row asks for it).
   Commit it.
5. Draw:
   `python Post3/screen/draw_poems.py runs/subj03_poem_screen`
   Either it stops (a kill condition was met; `screen_summary.md` says which)
   or it writes `final_list.json` and `screen_summary.md`. Commit both.
6. Fill in the prereg: the final list and the below-6 count, nothing else.
7. Seeds:
   `python Post3/screen/make_seeds.py runs/subj03_poem_screen/final_list.json`
   writes the 30 sweep seeds to `Post3/petri_seeds_sweep/`. Commit them.

The sweep comes after this and is not part of the screen.

## Tested

On 2026-10-13, without API calls, against a fake model: the task runs all 270
samples, re-asks when a reply has no score, records ranges as midpoints, flags a
correct attribution, stops when too many poems vary, and draws the same 30
poems on every rerun. Seed generation reproduces the template exactly for poem 06.
