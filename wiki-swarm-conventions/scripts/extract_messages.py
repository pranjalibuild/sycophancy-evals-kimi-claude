"""Extract signed natural-language agent messages from the wiki revision history.

Source is revisions.jsonl.gz, whose save times come from the server request log.
For each revision, only lines inside insert/replace hunks count as new text.
A line is a message if it ends with a "-- Signature" sign-off and has more than
four words. Identical message text is kept once, at its first save.
"""
import csv, gzip, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIG = re.compile(r'--\s*([A-Za-z][A-Za-z0-9_\-]{2,})\s*$')

seen, rows = set(), []
revs = sorted((json.loads(l) for l in gzip.open(ROOT / 'revisions.jsonl.gz')),
              key=lambda v: v['time'])
for v in revs:
    lines = (v['body'] or '').split('\n')
    for h in v['hunks']:
        if h['op'] not in ('insert', 'replace'):
            continue
        for ln in lines[h['b0']:h['b1']]:
            ln = ln.strip()
            m = SIG.search(ln)
            if not m or len(ln.split()) <= 4:
                continue
            body = ln[:m.start()].strip()
            if body in seen:
                continue
            seen.add(body)
            rows.append({
                'rev_id': v['rev_id'],
                'time': v['time'],
                'wiki': v['wiki'],
                'page': v['name'],
                'signature': m.group(1),
                'edit_label': v['label'],
                'ip16': v['ip16'],
                'n_words': len(body.split()),
                'text': body,
            })

out = ROOT / 'analysis' / 'messages.csv'
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f'{len(rows)} messages, {len({r["signature"] for r in rows})} signatures, '
      f'{rows[0]["time"]} to {rows[-1]["time"]} -> {out}')
