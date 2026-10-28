"""Restyle the older published pages onto docs/assets/post.css.

Reads each page from git HEAD rather than the working tree, so running it twice
gives the same result. Posts 1, 2 and the field note keep their markup and their
component classes; what changes is the shell around them: the productbc type and
palette, a reading column with tables breaking out, section anchors, the chips
under the hero and the left rail.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = [
    ("docs/posts/are-you-sure.html", "Sycophancy eval series"),
    ("docs/posts/base-model-pushback.html", "Sycophancy eval series"),
    ("docs/posts/wiki-swarm-conventions.html", "Field notes"),
]
FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400'
    '&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">\n'
    '<link rel="stylesheet" href="../assets/post.css">'
)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text).lower()).strip("-")


def short(text):
    text = re.sub(r"<[^>]+>", "", text).strip()
    if text.lower().startswith("appendix"):
        return text.split(":")[0].strip()
    m = re.match(r"Part \d+:\s*(.+)", text)
    return m.group(1).strip() if m else text


def restyle(rel, kicker):
    src = subprocess.run(
        ["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout

    # one shared stylesheet in place of the per-page ones
    head, _, rest = src.partition("<style>")
    body = rest[rest.rindex("</style>") + len("</style>") :]
    src = head + FONTS + body

    src = src.replace("<body>", '<body id="top">\n<div class="progress"><i></i></div>', 1)
    src = re.sub(
        r'<div class="top-nav">.*?</div>',
        '<div class="wrap">\n  <div class="topbar">'
        '<a href="../index.html">&larr; All posts</a>'
        f"<span>{kicker}</span></div>",
        src,
        count=1,
        flags=re.S,
    )
    src = src.replace('<div class="page">', '<header class="hero">', 1)

    # an accent rule under the title, as on post 3
    src = re.sub(r'(<p class="subtitle">.*?</p>\n)', r'\1  <div class="rule-accent"></div>\n', src, count=1, flags=re.S)

    # anchor every section, remember the labels for the chips and the rail
    sections = []

    def anchor(m):
        attrs, text = m.group(1), m.group(2)
        existing = re.search(r'id="([^"]+)"', attrs)
        sid = existing.group(1) if existing else slug(text)
        sections.append((sid, short(text)))
        label = short(text)
        extra = f' data-short="{label}"' if label != re.sub(r"<[^>]+>", "", text).strip() else ""
        return f'<h2 id="{sid}"{extra}>{text}</h2>'

    src = re.sub(r"<h2([^>]*)>(.*?)</h2>", anchor, src, flags=re.S)

    chips = "\n".join(f'      <a href="#{sid}">{label}</a>' for sid, label in sections)
    hero_end = (
        f'\n    <nav class="chapters" aria-label="Sections">\n{chips}\n    </nav>\n'
        "  </header>\n\n  <main>\n"
    )

    # the hero runs to the end of the lede, or of the stat strip when there is none
    lede = re.search(r'<p class="lede">.*?</p>\n', src, re.S)
    if lede:
        cut = lede.end()
    else:
        strip = re.search(r'<div class="stat-strip">.*?\n[ \t]*</div>\n', src, re.S)
        cut = strip.end()
    src = src[:cut] + hero_end + src[cut:]

    src = src.replace("<footer", "  </main>\n\n  <footer", 1)
    src = src.replace(
        "</body>", '<script src="../assets/post.js" defer></script>\n</body>', 1
    )

    out = ROOT / rel
    out.write_text(src)
    print(f"{rel}: {len(sections)} sections, {len(src)} bytes")


def main():
    for rel, kicker in PAGES:
        restyle(rel, kicker)
    return 0


if __name__ == "__main__":
    sys.exit(main())
