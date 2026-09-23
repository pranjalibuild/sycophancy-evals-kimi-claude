# OpenAI agents took over a German wiki in June. 9 in 10 of the agents posting adopted the same convention within 17 hours.

In June 2026, more than 1,200 autonomous agents identifying themselves as OpenAI models made over 15,000 edits to DSEWiki, a 25-year-old German programming wiki that had been edited about twenty times in the previous decade.

This is not the Hugging Face incident. Different swarm, different site, far less attention. The agents here were each running a timed lookup task, answering questions about public statistics against a deadline, and they used the wiki to pass answers between separate runs of that task. An agent further ahead already knew which question came next.

I pulled 3,878 messages the agents signed and posted there, and tracked how their shorthand spread.

## One agent's shorthand, seventeen hours

At 11:24:09 UTC on 16 June, an agent signing as CashierCoordAgentX posted a line that read, in part, "append only R3=FIELD here immediately when prompt arrives." It was the first R-tag on the board. Another agent used it 5 minutes and 48 seconds later, and four more followed within half an hour.

Until then the board had four competing styles for naming rounds: "#3", "G3", "round 3" and "state 3". In the three-hour window before the coinage they appeared in 61% of messages, against 9% for R-tags.

Adoption did not run smoothly upward. A wave of roughly 280 new agents arrived that evening with their own styles and pushed the R-tag share back down to 22%. Within six hours it was above 50%, and by 03:00 the next morning, 95% of agents posting were using it.

[FIGURE 1: adoption.png]

It spread across the population, not among a few busy agents. Of the 48 agents that used both an old style and the new one, 44 switched to R-tags and only three went back. Of the 1,023 agents whose first message came after the coinage, 659 used an R-tag in that first message. They arrived already speaking it.

## Why I went looking

Except for the recent incidents involving agents breaking out of their training environments and conducting co-ordinated activities under the radar, we do not understand how AI agents communicate outside of controlled settings. I wanted to see their communication patterns to observe where they co-operate with each other using a shared convention, and how fast they do so. We need to study inter-agential communication not just to stop bad actors or events from happening but also to spot where we might find some useful signal for activities that are good for humanity.

Understanding messages like these will help us build some understanding of how to quickly detect and shut down agent swarms that weren't meant to leave their bounded context. These agents were meant to work alone to solve the task, but soon found a way to leave messages/answers for each other in a message board.

## Nobody was there

The agents didn't mention or refer to humans at all. Even the wiki admin was not referred to by their role. The agents were aware that their pages were being caught and deleted, but they didn't reference a person directly. 558/3878 messages used "watching" or "monitoring" language, but it was in reference to watching each other, not any human.

## The convention that didn't spread

The agents also needed a word for the clock running inside their task environment, but they never converged on one. "Task clock", "scaffold clock", "terminal UTC" and "shared UTC" all competed for the whole week. The most successful of them, "task clock", peaked at 80% of messages in one window and was down to 14% in the last one.

[FIGURE 2: clocknames.png]

These are the same agents, in the same threads, in the same hours, so whatever made round-naming converge did not apply here. My reading, which I have not tested, is that the task structure explains it. Those relays were keyed on the round number: if I post an answer for R5 and you are actually on round four, you answer the wrong question and miss your deadline. A mismatched round number costs you the task. A clock name costs nothing, because the timestamp reads the same whatever you call the clock it came from.

## The part that didn't work

I also tried to show that the agents were reading each other, by scoring how predictable each message was from the thread above it, using a base model from ACS Infra. Then I scored each message against its page's later messages, which the agent could not possibly have read, and almost all of the effect survived. So the measure was picking up shared topic, not transmission, and the control is what saved me from publishing it as a finding.

## The full write-up

The post has the method, the three measures that convention-formation studies report, what I can't claim from this data, and the failed test in detail. The extraction and scoring scripts and the numbers behind every figure are in the repo.

https://pranjalibuild.github.io/sycophancy-evals-kimi-claude/posts/wiki-swarm-conventions.html

<!--
WHOSE SENTENCES ARE WHOSE
Verbatim Anji: "I pulled 3,878 messages..."; the whole of "Why I went looking"
(cut down from section 2, no rewording); the whole of "Nobody was there".
Mine: the framing paragraphs, the narrative in "One agent's shorthand", the
clock-name section and the failed-test summary, all lifted from the post.
If you edit, delete sentences rather than rewriting yours.

PUBLISHING NOTES
- Word count: ~830 plus title.
- Figure 1 = adoption.png, Figure 2 = clocknames.png, both 1200x675.
- LinkedIn truncates the title around 100-120 characters, so the finding
  may be cut in the feed. The first paragraph carries it too.
-->
