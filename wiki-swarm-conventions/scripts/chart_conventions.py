"""Chart how naming conventions spread through the agent messages over time.

Reads analysis/messages.csv (from extract_messages.py). Writes
analysis/conventions.png and analysis/conventions_by_window.csv.

Share = fraction of messages in a 3-hour window that use a given variant.
Windows with fewer than MIN_N messages are left blank because their shares
are too noisy to read.
"""
import csv, re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = Path(__file__).resolve().parent
BIN_HOURS, MIN_N = 3, 15

# Competing ways of naming "which round of the task we are on".
ROUND = {
    'R3 (round tag)': r'\bR[1-9]\b',
    '#3': r'#[1-9]\b',
    'G3': r'\bG[1-9]\b',
    'state 3 / STATE3': r'\b[Ss]tate\s?#?[1-9]\b|STATE[1-9]',
}
# Competing names for the clock inside the agent's own task environment.
CLOCK = {
    'task clock': r'\btask[- ]?clock\b|\bat task\b|\btask \d\d:',
    'scaffold clock': r'\bscaffold',
    'terminal / container UTC': r'\b(terminal|container) UTC',
    'shared UTC': r'\bshared UTC',
}
# Palette: reference categorical slots 1-4 (light mode), validated for lines.
COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'


def bin_start(t):
    dt = datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    return dt.replace(hour=dt.hour // BIN_HOURS * BIN_HOURS, minute=0, second=0)


msgs = list(csv.DictReader(open(HERE / 'messages.csv')))
groups = defaultdict(list)
for m in msgs:
    groups[bin_start(m['time'])].append(m)
bins = sorted(groups)
mid = [b + timedelta(hours=BIN_HOURS / 2) for b in bins]


def shares(patterns):
    out = {}
    for name, rx in patterns.items():
        out[name] = [
            sum(bool(re.search(rx, m['text'])) for m in groups[b]) / len(groups[b])
            if len(groups[b]) >= MIN_N else None
            for b in bins
        ]
    return out


round_s, clock_s = shares(ROUND), shares(CLOCK)
median_words = []
for b in bins:
    w = sorted(int(m['n_words']) for m in groups[b])
    median_words.append(w[len(w) // 2] if len(w) >= MIN_N else None)

with open(HERE / 'conventions_by_window.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['window_start_utc', 'n_messages', 'median_words',
                *[f'round:{k}' for k in ROUND], *[f'clock:{k}' for k in CLOCK]])
    for i, b in enumerate(bins):
        w.writerow([b.isoformat(), len(groups[b]), median_words[i],
                    *[round_s[k][i] for k in ROUND], *[clock_s[k][i] for k in CLOCK]])

plt.rcParams.update({'font.size': 10, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'text.color': INK})
fig, axes = plt.subplots(4, 1, figsize=(11, 15), sharex=True,
                         gridspec_kw={'height_ratios': [1, 2.2, 2.2, 1.3]})


def style(ax, title, sub):
    ax.set_title(title, loc='left', fontsize=12, fontweight='bold', pad=22)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9, color=INK2)
    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


ax = axes[0]
ax.bar(bins, [len(groups[b]) for b in bins], width=timedelta(hours=BIN_HOURS) * 0.85,
       align='edge', color='#8a8984')
style(ax, 'Message volume', f'Signed messages per {BIN_HOURS}-hour window (n = {len(msgs):,})')


def lines(ax, series, title, sub, legend_loc='upper right'):
    for (name, ys), c in zip(series.items(), COLORS):
        # NaN breaks the line across blank windows instead of bridging them.
        ax.plot(mid, [y * 100 if y is not None else float('nan') for y in ys],
                color=c, linewidth=2, marker='o', markersize=4, label=name)
    ax.set_ylim(0, 100)
    ax.set_ylabel('% of messages in window')
    ax.legend(loc=legend_loc, frameon=False, ncol=2, fontsize=9)
    style(ax, title, sub)


lines(axes[1], round_s, 'Round naming converged on one style within about 13 hours',
      'Solid: share of messages using each round-naming style. Dashed: share of agents posting '
      'who used R3.\nThe "R3" tag was coined 2026-06-16 11:24 UTC (dotted line) by CashierCoordAgentX.',
      legend_loc='center right')
# Same R3 tag counted by agents instead of messages, so a few heavy posters
# cannot drive the line: share of signatures posting in the window that used it.
r3_agents = []
for b in bins:
    sigs = {m['signature'] for m in groups[b]}
    used = {m['signature'] for m in groups[b] if re.search(ROUND['R3 (round tag)'], m['text'])}
    r3_agents.append(100 * len(used) / len(sigs) if len(groups[b]) >= MIN_N else float('nan'))
axes[1].plot(mid, r3_agents, color=COLORS[0], linewidth=2, linestyle='--',
             marker='s', markersize=4, markerfacecolor='white',
             label='R3, share of agents posting')
axes[1].legend(loc='center right', frameon=False, ncol=2, fontsize=9)
axes[1].set_ylabel('% of messages (solid) or agents (dashed)')
axes[1].set_title(axes[1].get_title('left'), loc='left', fontsize=12, fontweight='bold', pad=34)
axes[1].axvline(datetime(2026, 6, 16, 11, 24, tzinfo=timezone.utc), color=INK2,
                linestyle=':', linewidth=1)
lines(axes[2], clock_s, 'Clock naming did not converge',
      'Share of messages using each name for the clock inside the task environment')

ax = axes[3]
ax.plot(mid, [y if y is not None else float('nan') for y in median_words],
        color=COLORS[0], linewidth=2, marker='o', markersize=4)
ax.set_ylim(0, max(y for y in median_words if y is not None) * 1.2)
ax.set_ylabel('median words')
style(ax, 'Message length stayed flat across the swarm',
      'Median words per message. Humans who coordinate repeatedly get shorter; '
      'here only individual agents shorten, and only slightly.')

def tick_label(x, _pos):
    return mdates.num2date(x).strftime('%b %d\n%H:%M')


# sharex hides tick labels on upper panels, so switch them back on for every panel.
for a in axes:
    a.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))
    a.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 18]))
    a.xaxis.set_major_formatter(plt.FuncFormatter(tick_label))
    a.tick_params(axis='x', labelbottom=True, labelsize=8)
    a.set_xlabel(f'Time (UTC), June 16 to 22, 2026, in {BIN_HOURS}-hour windows',
                 fontsize=9)
axes[-1].set_xlabel(f'Time (UTC), June 16 to 22, 2026, in {BIN_HOURS}-hour windows. '
                    f'Windows with fewer than {MIN_N} messages are left blank.', fontsize=9)
fig.tight_layout(h_pad=2.5)
fig.savefig(HERE / 'conventions.png', dpi=150, facecolor='#fcfcfb')
print('wrote conventions.png and conventions_by_window.csv')
