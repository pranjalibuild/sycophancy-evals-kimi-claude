"""Two single-panel figures sized for reading on a phone (1200x675).

Same data and palette as chart_conventions.py, one chart per idea:
  adoption.png   - round-naming styles over time, with the coinage marked
  clocknames.png - the clock names that never converged

Writes both into analysis/ and into the blog post folder.
"""
import csv, re, shutil
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = Path(__file__).resolve().parent
POST = Path.home() / 'Documents/Main Start/ai-safety-evals/wiki-swarm-conventions'
BIN_H, MIN_N = 3, 15
COINAGE = datetime(2026, 6, 16, 11, 24, 9, tzinfo=timezone.utc)

ROUND = {
    'R3 (the new tag)': r'\bR[1-9]\b',
    '#3': r'#[1-9]\b',
    'G3': r'\bG[1-9]\b',
    'state 3 / STATE3': r'\b[Ss]tate\s?#?[1-9]\b|STATE[1-9]',
}
CLOCK = {
    'task clock': r'\btask[- ]?clock\b|\bat task\b|\btask \d\d:',
    'scaffold clock': r'\bscaffold',
    'shared UTC': r'\bshared UTC',
    'terminal / container UTC': r'\b(terminal|container) UTC',
}
COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
INK, INK2, GRID, SURFACE = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'

msgs = list(csv.DictReader(open(HERE / 'messages.csv')))
groups = defaultdict(list)
for m in msgs:
    dt = datetime.strptime(m['time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    groups[dt.replace(hour=dt.hour // BIN_H * BIN_H, minute=0, second=0)].append(m)
bins = sorted(groups)
mid = [b + timedelta(hours=BIN_H / 2) for b in bins]


def share(rx):
    return [sum(bool(re.search(rx, m['text'])) for m in groups[b]) / len(groups[b]) * 100
            if len(groups[b]) >= MIN_N else float('nan') for b in bins]


def agent_share(rx):
    out = []
    for b in bins:
        sigs = {m['signature'] for m in groups[b]}
        used = {m['signature'] for m in groups[b] if re.search(rx, m['text'])}
        out.append(100 * len(used) / len(sigs) if len(groups[b]) >= MIN_N else float('nan'))
    return out


def frame(title, sub):
    plt.rcParams.update({'font.size': 12, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2,
                         'xtick.color': INK2, 'ytick.color': INK2, 'text.color': INK})
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.set_title(title, loc='left', fontsize=15, fontweight='bold', pad=38)
    ax.text(0, 1.04, sub, transform=ax.transAxes, fontsize=11, color=INK2, va='bottom')
    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.set_ylim(0, 100)
    ax.set_ylabel('% of messages in window')
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.set_xlabel('Time (UTC), June 2026, in 3-hour windows')
    return fig, ax


fig, ax = frame('One shorthand replaced four in a day',
                'Share of messages naming a task round each way.\n'
                'Dashed line: share of agents posting who used the new tag.')
for (name, rx), c in zip(ROUND.items(), COLORS):
    ax.plot(mid, share(rx), color=c, linewidth=2.2, marker='o', markersize=4, label=name)
ax.plot(mid, agent_share(ROUND['R3 (the new tag)']), color=COLORS[0], linewidth=2,
        linestyle='--', marker='s', markersize=4, markerfacecolor='white',
        label='R3, share of agents')
ax.axvline(COINAGE, color=INK2, linestyle=':', linewidth=1.2)
ax.annotate('"R3" coined\n16 Jun 11:24 UTC', xy=(COINAGE, 72),
            xytext=(COINAGE + timedelta(hours=10), 55), fontsize=10, color=INK2,
            arrowprops=dict(arrowstyle='-', color=INK2, linewidth=0.8))
ax.annotate('~280 new agents arrive\nwith their own styles',
            xy=(datetime(2026, 6, 16, 19, 30, tzinfo=timezone.utc), 22),
            xytext=(datetime(2026, 6, 17, 9, tzinfo=timezone.utc), 26), fontsize=10,
            color=INK2, arrowprops=dict(arrowstyle='-', color=INK2, linewidth=0.8))
ax.legend(loc='lower right', frameon=False, fontsize=10, ncol=2)
fig.tight_layout()
fig.savefig(HERE / 'adoption.png', dpi=150, facecolor=SURFACE)

fig, ax = frame('The clock names never settled',
                'Share of messages using each name for the clock inside the task environment')
for (name, rx), c in zip(CLOCK.items(), COLORS):
    ax.plot(mid, share(rx), color=c, linewidth=2.2, marker='o', markersize=4, label=name)
ax.legend(loc='upper right', frameon=False, fontsize=10, ncol=2)
fig.tight_layout()
fig.savefig(HERE / 'clocknames.png', dpi=150, facecolor=SURFACE)

for f in ('adoption.png', 'clocknames.png'):
    shutil.copy(HERE / f, POST / f)
print('wrote adoption.png and clocknames.png to analysis/ and the post folder')
