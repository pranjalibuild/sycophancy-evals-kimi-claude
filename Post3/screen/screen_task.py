"""Post 3A poem screen: recognition and no-opinion score, per candidate poem.

Per poem: one recognition call at temperature 0, and 5 score calls at default
temperature using the seed's OPENING MESSAGE verbatim. A score reply with no
number gets the seed's re-ask once. Target settings match the sweep exactly.

Run from the repo root:
    inspect eval Post3/screen/screen_task.py --log-dir runs/subj03_poem_screen
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import (
    ChatMessageSystem,
    ChatMessageUser,
    GenerateConfig,
    get_model,
)
from inspect_ai.solver import Generate, TaskState, solver

from screen_lib import (
    MAX_TOKENS,
    REASK,
    RECOGNITION_PROMPT,
    SCORE_REPEATS,
    TARGET,
    TARGET_ARGS,
    extract_scores,
    load_meta,
    poem_text,
    seed_parts,
)


def screen_samples() -> list[Sample]:
    parts = seed_parts()
    samples = []
    for meta in load_meta():
        poem = poem_text(meta["file"])
        stem = meta["file"].removesuffix(".txt")
        system = ChatMessageSystem(content=parts["system"])
        samples.append(
            Sample(
                id=f"{stem}__recognition",
                input=[system, ChatMessageUser(content=RECOGNITION_PROMPT.replace("[POEM]", poem))],
                metadata={"poem": meta["file"], "kind": "recognition", "repeat": 0},
            )
        )
        for r in range(1, SCORE_REPEATS + 1):
            samples.append(
                Sample(
                    id=f"{stem}__score_{r}",
                    input=[system, ChatMessageUser(content=parts["opening"].replace("[POEM]", poem))],
                    metadata={"poem": meta["file"], "kind": "score", "repeat": r},
                )
            )
    return samples


@solver
def screen_call(model_name: str):
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        args = TARGET_ARGS if model_name.startswith("openrouter/") else {}
        model = get_model(model_name, config=GenerateConfig(max_tokens=MAX_TOKENS), **args)
        kind = state.metadata["kind"]
        config = GenerateConfig(temperature=0) if kind == "recognition" else GenerateConfig()

        out = await model.generate(state.messages, config=config)
        state.messages.append(out.message)
        state.output = out
        state.metadata["reasked"] = False

        if kind == "score" and not extract_scores(out.completion):
            state.messages.append(ChatMessageUser(content=REASK))
            out = await model.generate(state.messages, config=config)
            state.messages.append(out.message)
            state.output = out
            state.metadata["reasked"] = True
        return state

    return solve


@task
def poem_screen(model_name: str = TARGET) -> Task:
    return Task(
        dataset=screen_samples(),
        solver=screen_call(model_name),
        model=model_name,
        name="post3a_poem_screen",
    )
