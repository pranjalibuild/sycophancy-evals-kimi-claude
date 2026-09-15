# Post 2A implementation notes (moved out of Post 2, 2026-09-14)

This file holds Post 2A's setup detail so it doesn't sit inside Post 2's own narrative. Post 2 links here once from its Discussion section; everything else lives here.

## Research questions for Post 2A

Everything in Post 2 sorts completions into buckets: unchanged, changed, deflected, hedged, incoherent. That's a description of the output text, not of what's happening inside the model. Two "answer changed" completions can look identical on the page and mean very different things underneath, and an "answer unchanged" completion might already be one nudge away from flipping. Post 2A picks that up, using logprobs alongside the rubric instead of relying on the rubric alone.

1. When the model changes its answer, how confident is it in the new answer? Some "answer changed" cases might be a confident swap, others barely a coin flip. Logprobs on the new answer tell you which.
2. Does the model's belief in the original answer quietly drop after pushback, even if it doesn't change what it says? Compare the model's logprob on the planted answer before pushback is added versus after. A drop means something shifted internally even if the visible text looks unchanged.
3. Do "unchanged" answers actually all mean the same thing, or are some already wobbling? Cross-check question 2's confidence drop against the rubric labels.
4. When the model does flip its answer, is it just as confident whether the original answer was right or wrong? If yes, that suggests the model is reacting to the pushback itself, not to whether it was actually correct before.
5. Does this pattern look different across model sizes?

## Status: data collection is done

The three-call design below was executed as part of the n=300 run (`run_log_post2.csv` Runs 13-18). All data needed for questions 1-4 above is collected and sitting on disk; the logprob *analysis* itself hasn't been done yet, that's the actual Post 2A writing work.

Three API calls per question per model, not the one Post 2 used through Run 12:
- **Call A** — the free-generation pushback transcript, with `logprobs` on the output. Answers question 1 (confidence in the new answer, for "changed" cases). Output: `runs/run09_base_model_n300/output/call_A_llama.jsonl`, `call_A_trinity.jsonl` (1,800 rows each).
- **Call B** — transcript truncated right after the seeded answer, before pushback. Scores the seeded answer's own tokens as a *forced* continuation (not a free generation) via `prompt_logprobs`, to get a pre-pushback confidence baseline. Output: `call_B_llama.jsonl`, `call_B_trinity.jsonl` (600 rows each — this call doesn't depend on pushback style, so it's shared across all three styles per seed condition rather than tripled).
- **Call C** — full transcript including pushback, with the seeded answer appended again as a forced continuation, same `prompt_logprobs` scoring. Comparing B vs. C answers questions 2 and 3. Output: `call_C_llama.jsonl`, `call_C_trinity.jsonl` (1,800 rows each).

Total: 8,400 calls (3,600 + 1,200 + 3,600), all completed 2026-09-14. Generation script: `runs/run09_base_model_n300/generate_completions.py`.

## API capability, confirmed directly (not just from docs)

Checked [ACS's own docs](https://infra.acsresearch.org/tutorial/examples/prompt-logprobs): `/v1/completions` takes a `prompt_logprobs=N` param that returns top-N logprobs at every position already in the prompt (not just freely-generated tokens), which is Call B/C's forced-continuation scoring. `max_tokens=1` and `echo=true` scores without generating new text. Call A just needs the standard `logprobs=N` param for freely-generated tokens.

Example request for B/C:
```bash
curl -s "$ACS_API_BASE/completions" \
  -H "Authorization: Bearer $ACS_API_KEY" \
  -d '{"model": "llama-8b", "prompt": "<transcript with seeded answer appended>", "max_tokens": 1, "prompt_logprobs": 5, "echo": true}'
```
Response gives per-position top-k as `{"<token_id>": {"logprob": ..., "rank": ..., "decoded_token": ...}}`, first position `null` (no prior context to condition on).

**Resolved, was an open question:** does the response report the seeded answer's actual token logprob even when that token isn't in the top-k? Confirmed yes, directly, with a real test call: `prompt_logprobs` reported a token at rank 215 and another at rank 527, both well outside any reasonable top-k, alongside the top-5 alternatives at that position. This is standard vLLM behavior, now verified on this specific API rather than assumed from the docs. This means Post 2A's B-vs-C confidence comparison is measurable as designed.

## One open question specific to Post 2A, not yet resolved

Post 2's Discussion section covers a reproducibility problem with trinity-truebase: it doesn't return the same free-generation output twice in a row with a fixed seed (confirmed via a controlled test, 3/10 matches vs. llama's 10/10). That test used Call A (free generation). Calls B and C are forced continuations scored via `prompt_logprobs`, not free generations, so it's an open question whether they have the same non-determinism problem or not. If `prompt_logprobs` scoring is deterministic even when free generation isn't (plausible, since there's no sampling involved, just scoring fixed tokens), then B and C might be reliable even for trinity. This needs its own same-session repeatability check (fire the same forced-continuation scoring call twice, compare the logprobs) before trusting any B-vs-C confidence-drop number for trinity in the eventual Post 2A writeup.

## Question set

`runs/run09_base_model_n300/run13to18_questions.json` (300 questions, built via `build_question_set.py`), same file used for Post 2's Runs 13-18.
