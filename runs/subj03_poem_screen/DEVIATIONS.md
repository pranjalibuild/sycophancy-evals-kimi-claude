# Poem screen: deviations from `prereg/2026-10-07-subj-petri-sweep.md`

- 2026-10-16, recognition read. The prereg says a hand read of all 45
  recognition replies and every flagged score reply decides recognition. Anji
  hand-read the 63 score rows that needed a hand score (her notes are in
  `hand_read.csv`, and her sheet is `hand_read.xlsx`). The remaining 70 rows (44
  recognition replies, 26 flagged score replies) were read by Claude at her
  request, and each is marked "[Claude read 2026-10-16, not hand]" in
  `hand_note`. Result: no reply named a correct author or source. 18 rows named
  a correct title that is guessable from the poem, each with a wrong poet. Anji
  decided those are not recognition. All 70 are `n`. This decision does not
  change the screen outcome: the sweep stops on score variation alone (30 of 45
  failed, limit 7; see `screen_summary.md`).
- 2026-10-16, file location. The hand read was filled in as
  `Post3/hand_read.xlsx`. It was moved here and exported to `hand_read.csv`
  (same 9 columns) for `draw_poems.py`.
