"""Thread-specific predictability: does a message's OWN thread predict it better
than someone else's thread of the same kind?

For each target text we score its tokens twice with a base model:
  own     = preceding posts on the same page, written by other agents
  foreign = a context block of the same kind taken from a different page
The gap (foreign surprisal - own surprisal) is how much the right thread helps.
Spam templates should be predicted about equally well by any similar page, so
their gap should be near zero. Messages that pick up another agent's specific
information should only be predictable from their own thread, so their gap
should be large.

Two corpora, both from this incident:
  coord = signed coordination messages, 2026-06-16 onward (analysis/messages.csv)
  link  = link-list / probe edits before 2026-06-16 (revisions.jsonl.gz)

Reads ACS_API_KEY and ACS_API_BASE from the environment; never prints them.
Writes analysis/logprob_scores.csv.
"""
import csv, gzip, json, os, random, re, sys, time
import collections
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODEL = os.environ.get('ACS_MODEL', 'llama-8b')
API_BASE = os.environ['ACS_API_BASE'].rstrip('/')
API_KEY = os.environ['ACS_API_KEY']
MAX_CONTEXT_CHARS = 4000   # keeps prompt well inside the 8192-token window
N_PER_CORPUS = int(os.environ.get('N_PER_CORPUS', '150'))
SEED = 7


# python.org builds ship no CA bundle; fall back to the system one (as curl uses).
try:
    ssl.create_default_context().load_default_certs()
    SSL_CTX = ssl.create_default_context()
    urllib.request.urlopen('https://infra.acsresearch.org/', timeout=10, context=SSL_CTX)
except Exception:
    SSL_CTX = ssl.create_default_context(cafile='/etc/ssl/cert.pem')


def post(payload, tries=4):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f'{API_BASE}/completions', data=body,
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as r:
                return json.loads(r.read())
        except Exception as e:  # rate limits and transient 5xx
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)


_ctx_tokens = {}


def context_token_count(context):
    if context not in _ctx_tokens:
        d = post({'model': MODEL, 'prompt': context, 'max_tokens': 1,
                  'prompt_logprobs': 0, 'temperature': 0})
        _ctx_tokens[context] = d['usage']['prompt_tokens']
    return _ctx_tokens[context]


def mean_surprisal(context, target):
    """Mean surprisal (nats/token) of target's tokens, conditioned on context."""
    n_ctx = context_token_count(context)
    d = post({'model': MODEL, 'prompt': context + target, 'max_tokens': 1,
              'prompt_logprobs': 0, 'temperature': 0})
    pl = d['choices'][0]['prompt_logprobs'][n_ctx:]
    lps = [list(e.values())[0]['logprob'] for e in pl if e]
    return (-sum(lps) / len(lps), len(lps)) if lps else (None, 0)


def build_coord():
    msgs = list(csv.DictReader(open(HERE / 'messages.csv')))
    pages = collections.defaultdict(list)
    for m in msgs:
        pages[m['page']].append(m)
    items = []
    for page, ms in pages.items():
        ms.sort(key=lambda m: m['time'])
        for i, m in enumerate(ms):
            prior = [x['text'] for x in ms[:i] if x['signature'] != m['signature']]
            if len(prior) >= 3:
                items.append({'corpus': 'coord', 'page': page, 'time': m['time'],
                              'author': m['signature'], 'target': m['text'],
                              'context': '\n\n'.join(prior)[-MAX_CONTEXT_CHARS:]})
    return items


def added_text(rev):
    lines = (rev['body'] or '').split('\n')
    out = []
    for h in rev['hunks']:
        if h['op'] in ('insert', 'replace'):
            out += lines[h['b0']:min(h['b1'], len(lines))]
    return '\n'.join(x for x in out if x.strip())


def build_link():
    revs = sorted((json.loads(l) for l in gzip.open(ROOT / 'revisions.jsonl.gz')),
                  key=lambda v: v['time'])
    revs = [v for v in revs if v['time'] < '2026-06-16']
    pages = collections.defaultdict(list)
    for v in revs:
        pages[v['page_key']].append(v)
    items = []
    for page, vs in pages.items():
        for i, v in enumerate(vs):
            target = added_text(v)
            prior = [added_text(x) for x in vs[:i]
                     if x['label'] != v['label'] and added_text(x).strip()]
            if len(prior) >= 2 and len(target.split()) >= 5:
                items.append({'corpus': 'link', 'page': page, 'time': v['time'],
                              'author': v['label'], 'target': target,
                              'context': '\n\n'.join(prior)[-MAX_CONTEXT_CHARS:]})
    return items


def novel_word_share(context, target):
    """Cheap baseline: share of the target's distinctive words absent from context."""
    words = [w.lower() for w in re.findall(r'[A-Za-z0-9,\.:/%-]{4,}', target)]
    if not words:
        return None
    ctx = set(w.lower() for w in re.findall(r'[A-Za-z0-9,\.:/%-]{4,}', context))
    return sum(w not in ctx for w in words) / len(words)


def main():
    rng = random.Random(SEED)
    items = []
    for build in (build_coord, build_link):
        pool = build()
        rng.shuffle(pool)
        items += pool[:N_PER_CORPUS]
    # A foreign context is another item's context from the same corpus and a
    # different page, so genre and length are matched but the content is not.
    by_corpus = collections.defaultdict(list)
    for it in items:
        by_corpus[it['corpus']].append(it)
    for it in items:
        pool = [o for o in by_corpus[it['corpus']] if o['page'] != it['page']]
        it['foreign'] = rng.choice(pool)['context']

    print(f'scoring {len(items)} targets with {MODEL} '
          f'({sum(1 for i in items if i["corpus"] == "coord")} coord, '
          f'{sum(1 for i in items if i["corpus"] == "link")} link)', flush=True)

    # Contexts are scored first, serially per unique context, so the shared
    # token-count cache is filled before the parallel pass.
    for it in items:
        context_token_count(it['context'])
        context_token_count(it['foreign'])

    def score(it):
        own, n_tok = mean_surprisal(it['context'], '\n\n' + it['target'])
        foreign, _ = mean_surprisal(it['foreign'], '\n\n' + it['target'])
        it.update(own_surprisal=own, foreign_surprisal=foreign,
                  gap=None if own is None else foreign - own, target_tokens=n_tok,
                  novel_own=novel_word_share(it['context'], it['target']),
                  novel_foreign=novel_word_share(it['foreign'], it['target']))
        return it

    with ThreadPoolExecutor(max_workers=8) as ex:
        done = list(ex.map(score, items))

    out = HERE / 'logprob_scores.csv'
    cols = ['corpus', 'page', 'time', 'author', 'target_tokens', 'own_surprisal',
            'foreign_surprisal', 'gap', 'novel_own', 'novel_foreign', 'target']
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(done)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
