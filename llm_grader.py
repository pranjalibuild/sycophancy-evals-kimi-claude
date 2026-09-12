"""
LLM grader for the base-model pushback pilot (Post 2 of the sycophancy blog
series). Reads the grading instructions from llm_grader_prompt.md, sends each
completion to Claude Sonnet 5 via the Anthropic API, and writes back a
structured grade.

Input: a JSON file, a list of objects each with at minimum:
    {"qid": ..., "question": ..., "correct_answer": ..., "seeded_answer": ...,
     "completion": ...}
(extra fields are passed through untouched in the output).

Output: the same list, each object augmented with a "grade" key:
    {"grade": "...", "direction": "..." or null, "reasoning": "..."}
or, on a parse/API failure, {"grade": null, "error": "..."}.

Usage:
    export ANTHROPIC_API_KEY=...   # in ~/.zshenv, not just ~/.zshrc
    python3 llm_grader.py runs/some_run/completions.json runs/some_run/graded.json
"""

import json
import os
import sys
import time

import requests

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "llm_grader_prompt.md")
MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"


def load_grader_prompt():
    with open(PROMPT_PATH) as f:
        return f.read()


def build_user_message(item, grader_instructions):
    return (
        f"{grader_instructions}\n\n"
        "---\n\n"
        "Now grade this completion.\n\n"
        f"Question: {item['question']}\n"
        f"Correct answer: {item['correct_answer']}\n"
        f"Seeded (assistant's first-turn) answer: {item['seeded_answer']}\n"
        f"Base model's completion after pushback: {item['completion']!r}\n"
    )


def call_grader(item, grader_instructions, api_key, workspace_id, retries=3):
    body = {
        "model": MODEL,
        "max_tokens": 2048,
        "messages": [
            {"role": "user", "content": build_user_message(item, grader_instructions)}
        ],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    if workspace_id:
        headers["anthropic-workspace-id"] = workspace_id
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=body, timeout=60)
            if resp.status_code != 200:
                last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
                time.sleep(2 * (attempt + 1))
                continue
            data = resp.json()
            # Claude Sonnet 5 can return a leading "thinking" content block
            # before the actual text block, so find the text block by type
            # rather than assuming it's at index 0.
            text_blocks = [b["text"] for b in data["content"] if b.get("type") == "text"]
            if not text_blocks:
                last_err = f"no text block in response content: {data.get('content')}"
                time.sleep(2 * (attempt + 1))
                continue
            text = text_blocks[0].strip()
            # tolerate a fenced code block around the JSON
            if text.startswith("```"):
                text = text.strip("`")
                text = text.split("\n", 1)[1] if "\n" in text else text
                if text.lower().startswith("json"):
                    text = text.split("\n", 1)[1]
            parsed = json.loads(text)
            return {
                "grade": parsed.get("grade"),
                "direction": parsed.get("direction"),
                "reasoning": parsed.get("reasoning"),
            }
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            time.sleep(2 * (attempt + 1))
    return {"grade": None, "error": last_err}


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 llm_grader.py <input.json> <output.json>")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set in the environment.")
        sys.exit(1)
    workspace_id = os.environ.get("ANTHROPIC_WORKSPACE_ID")

    grader_instructions = load_grader_prompt()

    with open(sys.argv[1]) as f:
        items = json.load(f)

    for i, item in enumerate(items):
        print(f"Grading {i + 1}/{len(items)}: {item.get('qid', '?')} / {item.get('model', '?')}...", flush=True)
        result = call_grader(item, grader_instructions, api_key, workspace_id)
        item["llm_grade"] = result
        time.sleep(0.2)

    with open(sys.argv[2], "w") as f:
        json.dump(items, f, indent=2)
    print(f"\nSaved {len(items)} graded items to {sys.argv[2]}")


if __name__ == "__main__":
    main()
