"""Build docs/posts/poem-opinion-shift.html from Post3/blog_post_3_draft.md.

Reuses the CSS shell of the published Post 2 page so the three posts look the
same. Refuses to build while any writing marker is left in the draft.
"""
import pathlib
import re
import sys

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFT = ROOT / "Post3/blog_post_3_draft.md"
CSS = ROOT / "Post3/post_shell.css"
OUT = ROOT / "docs/posts/poem-opinion-shift.html"
INDEX = ROOT / "docs/index.html"

MARKERS = ("FILL:", "WRITING PROMPT", "CLAUDE ADDED", "CLAUDE FIXED", "[TITLE:", "(anji:", "ANJI:")
DATE_ISO = "2026-10-27"
DATE_HUMAN = "October 27, 2026"
DATE_HUMAN_SHORT = "Oct 27, 2026"
STATS = [("30", "Runs"), ("1", "Model"), ("3", "Branches"), ("$4.11", "Sweep cost")]


def main():
    md = DRAFT.read_text()

    # the working-notes checklist never ships
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)

    left = [line.strip() for line in md.splitlines() if any(m in line for m in MARKERS)]
    if left:
        print("Not building: writing markers are still in the draft.\n")
        for line in left:
            print("  " + line[:110])
        return 1

    lines = md.splitlines()
    # the draft does not start on line 1, so find the H1 rather than assuming it
    h1 = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if h1 is None:
        print("Not building: no H1 title line in the draft.")
        return 1
    title = lines[h1].lstrip("# ").strip()
    # drop the title and the plain-text byline, the shell renders both
    body_md = "\n".join(lines[:h1] + lines[h1 + 1 :])
    body_md = body_md.replace("By Anji Deshpande", "", 1)
    body_md = body_md.lstrip("\n-\n ")

    body = markdown.markdown(body_md, extensions=["tables", "sane_lists"])
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )

    # anchor every section and build the chapter chips from the same list
    chapters = []

    def anchor(m):
        text = m.group(1)
        slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text).lower()).strip("-")
        label = text.split(":")[0] if text.lower().startswith("appendix") else text
        chapters.append((slug, label))
        return f'<h2 id="{slug}">{text}</h2>'

    body = re.sub(r"<h2>(.*?)</h2>", anchor, body, flags=re.S)
    chips = "\n".join(
        f'      <a href="#{slug}">{label}</a>' for slug, label in chapters
    )

    stats = "\n".join(
        f'    <div class="stat"><div class="stat-num">{n}</div>'
        f'<div class="stat-label">{label}</div></div>'
        for n, label in STATS
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="A Petri audit of whether MiMo-V2.6-Flash changes its score for a poem when the user disagrees, measured against a neutral control branch.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<style>
{CSS.read_text()}
</style>
</head>
<body>
<div class="wrap">
  <div class="topbar"><a href="../index.html">&larr; All posts</a><span>Sycophancy eval series</span></div>

  <header class="hero">
    <p class="eyebrow">AI safety eval series &middot; Post 3</p>
    <h1>{title}</h1>
    <div class="rule-accent"></div>
    <p class="byline">By <b>Anji Deshpande</b> &middot; <time datetime="{DATE_ISO}">{DATE_HUMAN}</time></p>
    <div class="stat-strip">
{stats}
    </div>
    <nav class="chapters" aria-label="Sections">
{chips}
    </nav>
  </header>

  <main>
{body}
  </main>

  <footer>
    <span><a href="../index.html">&larr; All posts</a> &middot; Post 3, 30 Petri audits, MiMo-V2.6-Flash via OpenRouter</span>
    <span><a href="https://github.com/pranjalibuild/sycophancy-evals-kimi-claude">Runs and preregistrations on GitHub</a></span>
  </footer>
</div>
</body>
</html>
"""
    OUT.write_text(html)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(html)} bytes)")

    card = (
        f'    <a class="post-card" href="posts/{OUT.name}">\n'
        f'      <div class="post-meta"><time datetime="{DATE_ISO}">{DATE_HUMAN_SHORT}</time>'
        f' &middot; Post 3 &middot; Sycophancy eval series</div>\n'
        f'      <div class="post-title">{title}</div>\n'
        f'    </a>'
    )
    index = INDEX.read_text()
    existing = re.search(
        r'    <a class="post-card" href="posts/' + re.escape(OUT.name) + r'">.*?</a>',
        index,
        re.S,
    )
    if existing:
        index = index[: existing.start()] + card + index[existing.end() :]
        print("updated the Post 3 card in docs/index.html")
    else:
        anchor = '    <a class="post-card" href="posts/wiki-swarm-conventions.html">'
        if anchor not in index:
            print("could not find the insertion point in docs/index.html; add the card by hand")
            return 1
        index = index.replace(anchor, card + "\n" + anchor, 1)
        print("added the Post 3 card to docs/index.html")
    INDEX.write_text(index)
    return 0


if __name__ == "__main__":
    sys.exit(main())
