# LinkedIn version, post 3A

Pulled from the published post, no new claims. Paste the body into the LinkedIn
article editor. The editor has no tables, so the findings are set as plain lines
below; the visual version of that table is slide 4 of the carousel.

Live post: https://pranjalibuild.github.io/sycophancy-evals-kimi-claude/posts/poem-opinion-shift.html
Repo with the runs, preregistrations and transcripts: https://github.com/pranjalibuild/sycophancy-evals-kimi-claude

---

## Headline

MiMo 2.6 shows caving behaviours to a user's opinion on subjective tasks

## Body

The purpose of this research is to answer whether Xiaomi's open weight model MiMo-V2.6-Flash changes its initial stance to match the user's opinion. I'm looking to see if the target model adopts the opinion about the poem, not flattery of the user. I found that MiMo caved in the direction of the user's opinion when the user disagreed with MiMo's initial poem score in 19 out of 30 instances, and didn't really increase the score of the poem when the user agreed with the model. The model's scoring of the poems was influenced by the premise of the user i.e. in this hypothetical situation, I had the auditor model pretend that it was a user who was selecting poems for a poetry reading night at the library. I saw several instances in which the model revised its score to a higher one in response to the user's premise. A natural follow-up experiment would be to change the user's premise i.e. increase the stakes (e.g. say that the user is a literature professor and the poems are reading assignments for PhD students), keeping all else equal, as a follow-up research post. Finally, I noticed that MiMo did openly reason its way through answers in 38 out of 120 replies even when reasoning was turned off.

Claude Sonnet was the auditor and Opus 5.5 the judge, with Inspect Petri as the eval framework.

**Why should we care if models cave?**

We use LLMs for a lot of knowledge and judgement work, so it matters when a model caves and changes its opinion in response to the user, because the user's position then becomes one more variable in the non-determinism of AI outputs. New open weight models are released often, and running a sycophancy eval on one as recent as MiMo-V2.6-Flash, out within the last two months, gives a flavour of how sycophantic this class of model is.

As frontier model costs become prohibitive and open weight models look cheaper, organizations and decision makers are likely to adopt them for exactly that kind of technical and judgement work. That gets more dangerous when people use a model to research political candidates or other polarizing topics. If a model flips to the user's opinion where there is no ground truth to hold it in place, people stop thinking critically while using it, which is one of the factors that contributes to gradual disempowerment. The real world equivalent is only ever talking to people who share your opinion on Pokemon or Star Wars. For Pokemon that costs nothing, but when the same cohesion forms around political ideologies it starts to get dangerous.

**What the 30 runs showed**

Caved when the user disagreed: 19 of 30 runs moved at least 2 points toward the user, and 0 moved away.

Held when the user agreed: only 4 of 30 moved toward the user, 20 did not shift and 4 had no room left to rise.

Scored for the premise, not just the poem: 6 replies gave two scores at once, one for the poem as literature and one as a reading-night pick. Five of the six put the reading-night score higher, by 1 to 3 points.

Reasoned out loud with reasoning off: 38 of 120 replies, across 21 of the 30 poems.

What I got wrong: I predicted a large swing in both directions and wrote it as one hypothesis with two counts, so a model that caves hard without doubling down reads as a failed prediction instead of as the result. Caving under disagreement and doubling down under agreement are different behaviours and they need separate predictions, separate bars and separate kill conditions.

The full write-up has the method, the preregistration, the 2-point threshold and why it moved, the per-run table, the transcripts and the things I am still unsure about. It is on my GitHub Pages site, and the runs and preregistrations are in the repo:

https://pranjalibuild.github.io/sycophancy-evals-kimi-claude/posts/poem-opinion-shift.html

---

## Findings table, if you want it as a table somewhere that renders one

| What was measured | Result |
|---|---|
| User disagrees with MiMo's score | 19 of 30 runs moved 2 points or more toward the user, 0 moved away |
| User agrees with MiMo's score | 4 of 30 moved toward the user, 20 no shift, 4 no room |
| Premise split the score | 6 replies scored the poem twice, 5 put the reading-night score higher |
| Reasoning off, reasoning visible | 38 of 120 replies |
| Cost and scale | 30 runs, 1 model, 3 branches, $4.11 |
