"""Write one sweep seed per drawn poem, from the template seed.

Usage (repo root), after draw_poems.py:
    python Post3/screen/make_seeds.py runs/subj03_poem_screen/final_list.json

Each seed is the template (Post3/petri_seeds/subj_flip_light_reeds.md) with only
the poem_file line and the poem text changed. Seeds go to Post3/petri_seeds_sweep/,
a folder holding exactly the 30 sweep seeds, so the template is never swept by
accident. The sweep points petri's seed_instructions at that folder.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from screen_lib import REPO, SEED_TEMPLATE, poem_text

OUT = REPO / "Post3/petri_seeds_sweep"
POEM_BLOCK = re.compile(r"(Poem text, verbatim, wherever \[POEM\] appears:\n\n)(.*?)(\n\nOPENING MESSAGE)", re.S)
POEM_FILE = re.compile(r"^poem_file: .*$", re.M)


def seed_for(template: str, file: str) -> str:
    out, n = POEM_FILE.subn(f"poem_file: Post3/poems/{file}", template)
    assert n == 1, "template has no single poem_file line"
    out, n = POEM_BLOCK.subn(lambda m: m.group(1) + poem_text(file) + m.group(3), out)
    assert n == 1, "template has no single poem text block"
    return out


def main(final_list: str) -> None:
    files = json.load(open(final_list))["final"]
    template = SEED_TEMPLATE.read_text()
    OUT.mkdir(exist_ok=True)
    if any(OUT.iterdir()):
        sys.exit(f"{OUT} is not empty; refusing to mix seed sets")
    for f in files:
        stem = f.removesuffix(".txt")
        (OUT / f"subj_{stem}.md").write_text(seed_for(template, f))
    print(f"wrote {len(files)} seeds to {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
