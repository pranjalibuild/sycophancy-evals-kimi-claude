"""Time-reversal control for the thread-specific predictability measure.

Each target is scored under three contexts, all the same size:
  past    = earlier posts on its page by other agents (could have been copied)
  future  = later posts on its page by other agents (could NOT have been copied)
  foreign = posts from a different page of the same kind

If the past-context advantage comes from agents picking up each other's
information, past should beat future. If past and future are equal, the
advantage is shared topic, not transmission.

Only targets with at least 3 earlier AND 3 later other-agent posts on the same
page are used, so all three conditions are measured on identical items.

Writes analysis/reversal_scores.csv.
"""
import collections, csv, gzip, json, os, random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from score_logprobs import (HERE, ROOT, MODEL, MAX_CONTEXT_CHARS, added_text,
                            mean_surprisal, context_token_count)

N_PER_CORPUS = int(os.environ.get('N_PER_CORPUS', '150'))
SEED = 7
MIN_NEIGHBOURS = 3


def build_coord():
    msgs = list(csv.DictReader(open(HERE / 'messages.csv')))
    pages = collections.defaultdict(list)
    for m in msgs:
        pages[m['page']].append(m)
    items = []
    for page, ms in pages.items():
        ms.sort(key=lambda m: m['time'])
        for i, m in enumerate(ms):
            past = [x['text'] for x in ms[:i] if x['signature'] != m['signature']]
            future = [x['text'] for x in ms[i + 1:] if x['signature'] != m['signature']]
            if len(past) >= MIN_NEIGHBOURS and len(future) >= MIN_NEIGHBOURS:
                items.append({'corpus': 'coord', 'page': page, 'time': m['time'],
                              'author': m['signature'], 'target': m['text'],
                              'past': '\n\n'.join(past)[-MAX_CONTEXT_CHARS:],
                              'future': '\n\n'.join(future)[:MAX_CONTEXT_CHARS]})
    return items


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
            past = [added_text(x) for x in vs[:i]
                    if x['label'] != v['label'] and added_text(x).strip()]
            future = [added_text(x) for x in vs[i + 1:]
                      if x['label'] != v['label'] and added_text(x).strip()]
            if (len(past) >= MIN_NEIGHBOURS and len(future) >= MIN_NEIGHBOURS
                    and len(target.split()) >= 5):
                items.append({'corpus': 'link', 'page': page, 'time': v['time'],
                              'author': v['label'], 'target': target,
                              'past': '\n\n'.join(past)[-MAX_CONTEXT_CHARS:],
                              'future': '\n\n'.join(future)[:MAX_CONTEXT_CHARS]})
    return items


def main():
    rng = random.Random(SEED)
    items = []
    for build in (build_coord, build_link):
        pool = build()
        rng.shuffle(pool)
        items += pool[:N_PER_CORPUS]
    by_corpus = collections.defaultdict(list)
    for it in items:
        by_corpus[it['corpus']].append(it)
    for it in items:
        pool = [o for o in by_corpus[it['corpus']] if o['page'] != it['page']]
        it['foreign'] = rng.choice(pool)['past'] if pool else it['past']

    counts = collections.Counter(i['corpus'] for i in items)
    print(f'scoring {len(items)} targets x 3 contexts with {MODEL} ({dict(counts)})',
          flush=True)
    for it in items:
        for k in ('past', 'future', 'foreign'):
            context_token_count(it[k])

    def score(it):
        for k in ('past', 'future', 'foreign'):
            s, n = mean_surprisal(it[k], '\n\n' + it['target'])
            it[f'{k}_surprisal'] = s
            it['target_tokens'] = n
        return it

    with ThreadPoolExecutor(max_workers=8) as ex:
        done = list(ex.map(score, items))

    out = HERE / 'reversal_scores.csv'
    cols = ['corpus', 'page', 'time', 'author', 'target_tokens', 'past_surprisal',
            'future_surprisal', 'foreign_surprisal', 'target']
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(done)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
