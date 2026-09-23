"""Every number the convention write-up needs, computed in one place.

Reads analysis/messages.csv. Prints a report and writes
analysis/convention_stats.json so the post can quote figures without
recomputing them.
"""
import collections, csv, json, math, re
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
R3 = re.compile(r'\bR[1-9]\b')
ALT = re.compile(r'#[1-9]\b|\b[Rr]ound\s?[1-9]\b|\bG[1-9]\b|\b[Ss]tate\s?#?[1-9]\b|STATE[1-9]')
CLOCKS = {
    'task clock': r'\btask[- ]?clock\b|\bat task\b|\btask \d\d:',
    'scaffold clock': r'\bscaffold',
    'terminal / container UTC': r'\b(terminal|container) UTC',
    'shared UTC': r'\bshared UTC',
    'system clock': r'\bsystem (clock|UTC)\b',
}
BIN_H = 3


def ts(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


msgs = list(csv.DictReader(open(HERE / 'messages.csv')))
for m in msgs:
    m['dt'] = ts(m['time'])
    m['r3'] = bool(R3.search(m['text']))
    m['alt'] = bool(ALT.search(m['text']))
msgs.sort(key=lambda m: m['dt'])
out = {}

# --- the coinage and the first adopters ---
r3_msgs = [m for m in msgs if m['r3']]
coiner = r3_msgs[0]
first_by_sig = {}
for m in r3_msgs:
    first_by_sig.setdefault(m['signature'], m)
out['coinage'] = {'time': coiner['time'], 'signature': coiner['signature'],
                  'page': coiner['page'], 'text': coiner['text']}
out['first_adopters'] = [
    {'signature': s, 'time': m['time'], 'minutes_after_coinage':
     round((m['dt'] - coiner['dt']).total_seconds() / 60, 1), 'page': m['page']}
    for s, m in list(first_by_sig.items())[1:6]]

# --- adoption curve, by message and by agent, in 3-hour windows ---
groups = collections.defaultdict(list)
for m in msgs:
    b = m['dt'].replace(hour=m['dt'].hour // BIN_H * BIN_H, minute=0, second=0)
    groups[b].append(m)
curve = []
for b in sorted(groups):
    g = groups[b]
    sigs = {m['signature'] for m in g}
    used = {m['signature'] for m in g if m['r3']}
    curve.append({'window': b.isoformat(), 'messages': len(g), 'agents': len(sigs),
                  'share_messages': len([m for m in g if m['r3']]) / len(g),
                  'share_agents': len(used) / len(sigs),
                  'share_messages_alt': len([m for m in g if m['alt'] and not m['r3']]) / len(g)})
out['curve'] = curve


def crossing(field, level):
    """First window (>=15 messages) at or above `level`, and hours since coinage."""
    for w in curve:
        if w['messages'] >= 15 and w[field] >= level:
            mid = ts(w['window'].replace('+00:00', 'Z')) + timedelta(hours=BIN_H / 2)
            return {'window': w['window'], 'value': round(w[field], 3),
                    'hours_after_coinage': round((mid - coiner['dt']).total_seconds() / 3600, 1)}


out['time_to'] = {f'{f}_{int(l*100)}pct': crossing(f, l)
                  for f in ('share_messages', 'share_agents') for l in (0.5, 0.9)}

# --- logistic fit on agent-level adoption (least squares on log odds) ---
pts = [(ts(w['window'].replace('+00:00', 'Z')), w['share_agents']) for w in curve
       if w['messages'] >= 15 and 0.02 < w['share_agents'] < 0.98
       and ts(w['window'].replace('+00:00', 'Z')) <= coiner['dt'] + timedelta(hours=36)]
if len(pts) >= 3:
    xs = [(t - coiner['dt']).total_seconds() / 3600 for t, _ in pts]
    ys = [math.log(p / (1 - p)) for _, p in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    out['logistic'] = {'growth_per_hour': round(b, 3), 'midpoint_hours': round(-a / b, 2),
                       'n_points': n,
                       'note': 'fit on log odds of agent-level adoption, first 36h'}

# --- switching: did individual agents change style? ---
by_sig = collections.defaultdict(list)
for m in msgs:
    by_sig[m['signature']].append(m)
switched = reverted = both = 0
for s, ms in by_sig.items():
    alt_t = [m['dt'] for m in ms if m['alt'] and not m['r3']]
    r3_t = [m['dt'] for m in ms if m['r3']]
    if alt_t and r3_t:
        both += 1
        if min(alt_t) < min(r3_t):
            switched += 1
            if max(alt_t) > max(r3_t):
                reverted += 1
out['switching'] = {'agents_using_both': both, 'switched_alt_to_r3': switched,
                    'later_reverted': reverted, 'agents_total': len(by_sig),
                    'agents_multi_message': sum(1 for v in by_sig.values() if len(v) > 1)}

# --- after convergence: how exclusive was it? ---
late = [m for m in msgs if m['dt'] >= coiner['dt'] + timedelta(hours=16)]
tag = collections.defaultdict(set)
for m in late:
    if m['r3']:
        tag[m['signature']].add('r3')
    if m['alt']:
        tag[m['signature']].add('alt')
out['after_convergence'] = {
    'from': (coiner['dt'] + timedelta(hours=16)).isoformat(),
    'agents_using_any_round_tag': len(tag),
    'r3_only': sum(1 for v in tag.values() if v == {'r3'}),
    'alt_only': sum(1 for v in tag.values() if v == {'alt'}),
    'both': sum(1 for v in tag.values() if len(v) == 2)}

# --- newcomers: agents whose first message came after the coinage ---
first_msg = {s: ms[0] for s, ms in by_sig.items()}
newcomers = [s for s, m in first_msg.items() if m['dt'] > coiner['dt']]
lags = []
for s in newcomers:
    r = [m['dt'] for m in by_sig[s] if m['r3']]
    if r:
        lags.append((min(r) - first_msg[s]['dt']).total_seconds() / 3600)
lags.sort()
out['newcomers'] = {
    'count': len(newcomers),
    'used_r3_at_some_point': len(lags),
    'used_r3_in_first_message': sum(1 for s in newcomers if first_msg[s]['r3']),
    'median_hours_to_first_r3': round(lags[len(lags) // 2], 2) if lags else None}

# --- the negative case: clock naming never converged ---
clock_share = {}
for name, rx in CLOCKS.items():
    hits = [m for m in msgs if re.search(rx, m['text'])]
    per_window = [len([m for m in groups[b] if re.search(rx, m['text'])]) / len(groups[b])
                  for b in sorted(groups) if len(groups[b]) >= 15]
    clock_share[name] = {'messages': len(hits),
                         'agents': len({m['signature'] for m in hits}),
                         'peak_window_share': round(max(per_window), 3) if per_window else None,
                         'final_window_share': round(per_window[-1], 3) if per_window else None}
out['clock_naming'] = clock_share

# --- corpus description for the methods section ---
out['corpus'] = {
    'messages': len(msgs), 'signatures': len(by_sig),
    'first': msgs[0]['time'], 'last': msgs[-1]['time'],
    'pages': len({m['page'] for m in msgs}),
    'median_words': sorted(int(m['n_words']) for m in msgs)[len(msgs) // 2],
    'messages_with_round_tag': sum(1 for m in msgs if m['r3'] or m['alt'])}

(HERE / 'convention_stats.json').write_text(json.dumps(out, indent=2, default=str))
print(json.dumps(out, indent=2, default=str)[:4000])
print('\nwrote convention_stats.json')

# --- the three naming-game measures, appended ---
# Recomputed here (the file above already holds the raw curve) so the write-up
# can quote convergence, the share at take-off, and the seed-group question.
NG = {}
coin = coiner['dt']
usable = [w for w in curve if w['messages'] >= 15]
# The 12:00 window on 16 June holds 26 messages from 7 agents, all of them in the
# group where R3 started. It makes adoption look complete within two hours, so
# population-level measures below use windows with at least 20 distinct agents.
popular = [w for w in curve if w['agents'] >= 20]

# 1. time to convergence, and whether it held
NG['convergence'] = {}
for lvl in (0.5, 0.8, 0.9, 0.95):
    for w in popular:
        if w['share_agents'] >= lvl:
            t = ts(w['window'].replace('+00:00', 'Z')) + timedelta(hours=BIN_H / 2)
            after = [x for x in popular if x['window'] > w['window']]
            NG['convergence'][f'{int(lvl*100)}pct_agents'] = {
                'window': w['window'],
                'hours_after_coinage': round((t - coin).total_seconds() / 3600, 1),
                'share': round(w['share_agents'], 3),
                'held_after': round(min([x['share_agents'] for x in after]), 3) if after else None}
            break

# 2. the take-off: the biggest single-window jump in the first 24 hours
early = [w for w in popular if ts(w['window'].replace('+00:00', 'Z')) <= coin + timedelta(hours=24)]
jumps = [(early[i + 1]['share_agents'] - early[i]['share_agents'], early[i], early[i + 1])
         for i in range(len(early) - 1)]
big = max(jumps, key=lambda j: j[0])
NG['takeoff'] = {
    'window_before': big[1]['window'], 'share_agents_before': round(big[1]['share_agents'], 3),
    'agents_posting_before': big[1]['agents'],
    'window_after': big[2]['window'], 'share_agents_after': round(big[2]['share_agents'], 3),
    'jump': round(big[0], 3),
    'note': 'share_agents_before is the share of the posting population using R-tags '
            'immediately before the steepest rise'}

# 3. did a small group tip the rest?
INFLUX = datetime(2026, 6, 16, 18, tzinfo=timezone.utc)
seed = {m['signature'] for m in msgs if m['r3'] and m['dt'] < INFLUX}
influx_win = [w for w in curve if w['window'].startswith('2026-06-16T18')][0]
influx_msgs = [m for m in msgs if INFLUX <= m['dt'] < INFLUX + timedelta(hours=BIN_H)]
NG['seed_group'] = {
    'size': len(seed),
    'share_of_all_signatures': round(len(seed) / len(by_sig), 4),
    'agents_posting_in_influx_window': influx_win['agents'],
    'seed_agents_present_in_influx_window': len(seed & {m['signature'] for m in influx_msgs}),
    'seed_share_of_r3_messages_in_influx_window':
        round(len([m for m in influx_msgs if m['r3'] and m['signature'] in seed])
              / max(1, len([m for m in influx_msgs if m['r3']])), 3)}

# exposure: when an agent first used an R-tag, had one already appeared on that page?
page_r3 = collections.defaultdict(list)
for m in msgs:
    if m['r3']:
        page_r3[m['page']].append(m)
exposed = unexposed = seed_exposed = 0
for s, m in first_by_sig.items():
    if s == coiner['signature']:
        continue
    earlier = [x for x in page_r3[m['page']] if x['dt'] < m['dt'] and x['signature'] != s]
    if earlier:
        exposed += 1
        if any(x['signature'] in seed for x in earlier):
            seed_exposed += 1
    else:
        unexposed += 1
NG['exposure'] = {
    'adopters': exposed + unexposed,
    'r3_already_on_that_page': exposed,
    'no_r3_on_that_page_yet': unexposed,
    'share_exposed': round(exposed / max(1, exposed + unexposed), 3),
    'of_exposed_traceable_to_seed_group': seed_exposed,
    'note': 'exposure means an earlier R-tag message by another agent existed on the '
            'same page; it shows opportunity to copy, not that copying happened'}

out['naming_game'] = NG
(HERE / 'convention_stats.json').write_text(json.dumps(out, indent=2, default=str))
print(json.dumps(NG, indent=2, default=str))
