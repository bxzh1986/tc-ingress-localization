#!/usr/bin/env python3
"""Unified figure set (Figs. 1-8) for the restructured manuscript.

All numerical panels are drawn from the anonymised derived data in
02_配套支撑资料 (data/ and reviewer/results/).  Schematic panels are original
drawings; constructed-model values are labelled as such.

    python3 plot_figures_v2.py [--data 02_配套支撑资料] [--out figures_v2]
"""
import argparse, csv, os, json
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', '/tmp/mplcache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle
from matplotlib.lines import Line2D
import numpy as np

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument('--data'); ap.add_argument('--out')
A = ap.parse_args()
DATA = Path(A.data) if A.data else next(p for p in [HERE.parent / '02_配套支撑资料', HERE / 'data_pkg'] if p.exists())
OUT = Path(A.out) if A.out else HERE / 'figures_v2'
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- style ----
# Palette: Okabe–Ito colour-blind-safe set (Wong, Nat. Methods 2011), as shipped by
# seaborn's "colorblind" palette; tints are derived by blending toward white so that
# every fill keeps the hue of its semantic role.  Semantic roles used throughout:
#   BLUE   observed data / deterministic steps          ORANGE  hypothesis / constructed / proposed
#   GREEN  secondary observed series (P1 in models)     GREY    structure / unresolved / neutral
import seaborn as sns
import scienceplots  # noqa: F401  (registers the 'science' / 'nature' styles)
from matplotlib.colors import to_rgb, to_hex, ListedColormap
_cb = sns.color_palette('colorblind')
def tint(c, f=.86):
    r, g, b = to_rgb(c); return to_hex((r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f))
BLUE = to_hex(_cb[0]); ORANGE = to_hex(_cb[3]); GREEN = to_hex(_cb[2]); PURPLE = to_hex(_cb[4]); SKY = to_hex(_cb[9]); AMBER = to_hex(_cb[1])
BLUE_L = tint(BLUE); ORANGE_L = tint(ORANGE); GREEN_L = tint(GREEN); BLUE_M = tint(BLUE, .55)
INK = '#1B2631'; GRAY = '#5D6D7E'; GRAY_L = '#F2F4F6'; GRAY_M = '#C5CDD6'; RULE = '#AEB6BF'
plt.style.use(['science', 'nature', 'no-latex'])
plt.rcParams.update({
    'font.family': ['Liberation Sans', 'Nimbus Sans', 'DejaVu Sans'], 'font.size': 8.2,
    'axes.labelsize': 8.2, 'xtick.labelsize': 7.6, 'ytick.labelsize': 7.6, 'axes.titlesize': 8.6,
    'axes.linewidth': .6, 'axes.edgecolor': GRAY, 'xtick.color': GRAY, 'ytick.color': GRAY,
    'axes.labelcolor': INK, 'text.color': INK, 'axes.spines.top': False, 'axes.spines.right': False,
    'xtick.direction': 'out', 'ytick.direction': 'out', 'xtick.minor.visible': False, 'ytick.minor.visible': False,
    'xtick.major.width': .6, 'ytick.major.width': .6, 'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'xtick.top': False, 'ytick.right': False, 'axes.grid': False, 'axes.prop_cycle': plt.cycler(color=[to_hex(c) for c in _cb]),
    'svg.fonttype': 'none', 'savefig.facecolor': 'white', 'figure.dpi': 100, 'legend.frameon': False, 'legend.fontsize': 7.6,
})

def save(fig, name):
    fig.savefig(OUT / f'{name}.svg', bbox_inches='tight', pad_inches=.04)
    fig.savefig(OUT / f'{name}.png', dpi=600, bbox_inches='tight', pad_inches=.04)
    plt.close(fig); print('saved', name)

def rbox(ax, x, y, w, h, text='', *, edge=GRAY, face='white', ls='-', lw=.9, size=8.2, bold=False, color=INK, r=.012, ls_text=1.3, z=2, pad=0.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad={pad},rounding_size={r}', lw=lw, ls=ls, edgecolor=edge, facecolor=face, zorder=z))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=size, weight='bold' if bold else 'normal', color=color, linespacing=ls_text, zorder=z + 1)

def arrow(ax, p0, p1, *, color=GRAY, ls='-', lw=.9, ms=8, rad=0.0, shrink=2.0, z=3, style='-|>'):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, lw=lw, ls=ls, color=color, shrinkA=shrink, shrinkB=shrink, connectionstyle=f'arc3,rad={rad}', zorder=z))

def label(ax, x, y, s, *, size=7.6, color=GRAY, ha='center', va='center', bold=False, bg=True, rot=0, z=4, ls_text=1.25):
    ax.text(x, y, s, ha=ha, va=va, fontsize=size, color=color, weight='bold' if bold else 'normal', rotation=rot, zorder=z, linespacing=ls_text,
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.0} if bg else None)

def panel_title(ax, x, y, s, size=8.8):
    ax.text(x, y, s, ha='left', va='center', fontsize=size, weight='bold', color=INK)

def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis('off')
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig, ax

# ---------------------------------------------------------------- data -----
def read_csv(p):
    with open(p, encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
CK = read_csv(DATA / 'data/stp_checkpoints.csv')
INT = read_csv(DATA / 'data/stp_all_port_intervals.csv')
SNAP = read_csv(DATA / 'data/stp_all_port_snapshots.csv')
WIN = read_csv(DATA / 'data/stp_windows.csv')
MODEL = read_csv(DATA / 'reviewer/results/model_counterexample_intervals.csv')
MSUM = {r['scenario']: r for r in read_csv(DATA / 'reviewer/results/model_counterexample_summary.csv')}

C = np.array([int(r['tc_or_tcn_received']) for r in CK]); B5 = np.array([int(r['port5_bpdu_received']) for r in CK])
AGE = np.array([int(r['last_tc_age_s']) for r in CK])
dC = np.diff(C); dB5 = np.diff(B5); K = len(C)
ZERO = [k for k in range(2, K + 1) if dC[k - 2] == 0]

# ================================================================ Fig. 1 ===
def fig1():
    fig, ax = canvas(6.7, 3.9)
    def node(x, y, w, h, code, role, *, root=False, unc=False):
        rbox(ax, x, y, w, h, edge=BLUE if root else GRAY, face=BLUE_L if root else 'white', lw=1.3 if root else .9, ls='--' if unc else '-', r=.015)
        ax.text(x + w / 2, y + h * .66, code, ha='center', va='center', fontsize=9.6, weight='bold', color=BLUE if root else INK)
        ax.text(x + w / 2, y + h * .28, role, ha='center', va='center', fontsize=7.6, color=GRAY)
    W, H = .185, .135
    N = {'A1': (.055, .40), 'A2': (.055, .07), 'A3': (.405, .60), 'W1': (.755, .60), 'W2': (.755, .07), 'U': (.405, .07), 'C1': (.755, .835)}
    node(*N['A1'], W, H, 'A1', 'Aggregation · CIST root', root=True)
    node(*N['A2'], W, H, 'A2', 'Access switch')
    node(*N['A3'], W, H, 'A3', 'Aggregation')
    node(*N['W1'], W, H, 'W1', 'WLAN aggregation')
    node(*N['W2'], W, H, 'W2', 'WLAN access')
    node(*N['U'], W, H, 'U', 'Unknown transit path', unc=True)
    node(*N['C1'], W, H, 'C1', 'Wireless core · STP off')
    def seg(p, q, ls='-'): ax.plot([p[0], q[0]], [p[1], q[1]], ls=ls, color=GRAY, lw=.95, zorder=1)
    def pill(x, y, s, color=INK):
        ax.text(x, y, s, ha='center', va='center', fontsize=6.9, color=color, zorder=5,
                bbox={'boxstyle': 'round,pad=0.22,rounding_size=0.6', 'facecolor': 'white', 'edgecolor': GRAY_M, 'lw': .6})
    # A1-A2 observed uplink
    xa = N['A1'][0] + W * .62
    seg((xa, N['A1'][1]), (xa, N['A2'][1] + H)); pill(xa + .06, N['A1'][1] - .035, 'p5  D/B/F'); pill(xa + .06, N['A2'][1] + H + .035, 'p25  R/B/F')
    # A2 - U - W2 candidate
    yb = N['A2'][1] + H * .45
    seg((N['A2'][0] + W, yb), (N['U'][0], yb), '--'); pill((N['A2'][0] + W + N['U'][0]) / 2, yb - .055, 'p23  D/B/F')
    seg((N['U'][0] + W, yb), (N['W2'][0], yb), '--')
    # W2 - W1 - C1 ; A3 - W1
    xw = N['W1'][0] + W / 2
    seg((xw, N['W2'][1] + H), (xw, N['W1'][1])); pill(xw + .045, N['W2'][1] + H + .05, 'p25'); pill(xw + .045, N['W1'][1] - .05, 'p5')
    seg((xw, N['W1'][1] + H), (xw, N['C1'][1]))
    ya = N['A3'][1] + H / 2
    seg((N['A3'][0] + W, ya), (N['W1'][0], ya)); pill((N['A3'][0] + W + N['W1'][0]) / 2, ya + .05, 'p19 – p7')
    # A1 - wired network - A3 (aggregated)
    xl = N['A1'][0] + W * .62
    ax.plot([xl, xl, N['A3'][0]], [N['A1'][1] + H, ya, ya], ls=':', color=GRAY, lw=1.0, zorder=1)
    label(ax, (xl + N['A3'][0]) / 2, ya - .05, 'Wired network (aggregated)', size=7.2)
    # notification reception direction (blue)
    arrow(ax, (N['A1'][0] + W * .3, N['A2'][1] + H + .01), (N['A1'][0] + W * .3, N['A1'][1] - .01), color=BLUE, lw=1.3, ms=9)
    arrow(ax, (N['U'][0] - .012, yb + .06), (N['A2'][0] + W + .012, yb + .06), color=BLUE, lw=1.3, ms=9)
    label(ax, (N['A2'][0] + W + N['U'][0]) / 2, yb + .115, 'TC reception', size=7.4, color=BLUE)
    # legend
    lx, ly = .055, .955
    items = [('-', 'Observed adjacency (LLDP / bridge port)'), ('--', 'Candidate connection (MAC reachability)'), (':', 'Aggregated wired path')]
    for i, (ls, t) in enumerate(items):
        y = ly - i * .055; ax.plot([lx, lx + .05], [y, y], ls=ls, color=GRAY, lw=1.0); label(ax, lx + .062, y, t, ha='left', size=7.2)
    y = ly - 3 * .055; arrow(ax, (lx, y), (lx + .05, y), color=BLUE, lw=1.3, ms=9); label(ax, lx + .062, y, 'Notification reception direction (device-local)', ha='left', size=7.2, color=BLUE)
    rbox(ax, .43, .80, .30, .15, edge=GRAY_M, face=GRAY_L, lw=.6, r=.01)
    ax.text(.58, .915, 'Port role / state key', ha='center', va='center', fontsize=7.4, weight='bold', color=INK)
    ax.text(.58, .85, 'D Designated · R Root · B Boundary\nF FORWARDING · pN = port N at that end', ha='center', va='center', fontsize=6.9, color=GRAY, linespacing=1.3)
    save(fig, 'fig2_network_path')

# ================================================================ Fig. 2 ===
def fig2():
    fig, ax = canvas(6.7, 5.2)
    # ---- (a) mechanism
    panel_title(ax, .01, .975, '(a) Legacy STP topology-change signalling (simplified)')
    bw, bh, y = .19, .085, .83
    xs = [.04, .395, .75]
    for x, (c, r) in zip(xs, [('B1', 'detects local change'), ('B2', 'relay bridge'), ('B3', 'root bridge')]):
        rbox(ax, x, y, bw, bh, edge=GRAY, face='white', r=.012)
        ax.text(x + bw / 2, y + bh * .64, c, ha='center', va='center', fontsize=8.6, weight='bold'); ax.text(x + bw / 2, y + bh * .28, r, ha='center', va='center', fontsize=7.2, color=GRAY)
    for x0, x1 in [(xs[0] + bw, xs[1]), (xs[1] + bw, xs[2])]:
        arrow(ax, (x0, y + bh * .72), (x1, y + bh * .72), color=BLUE, lw=1.1); label(ax, (x0 + x1) / 2, y + bh * .72 + .035, 'TCN BPDU', color=BLUE, size=7.2)
        arrow(ax, (x1, y + bh * .25), (x0, y + bh * .25), color=ORANGE, lw=1.1, ls=(0, (4, 2))); label(ax, (x0 + x1) / 2, y + bh * .25 - .035, 'Config BPDU, TC flag', color=ORANGE, size=7.2)
    ax.text(.5, .765, 'TCN BPDUs are regenerated hop by hop toward the root; TC-flagged configuration BPDUs then propagate from the root and shorten FDB ageing.', ha='center', va='center', fontsize=7.2, color=GRAY)
    ax.plot([.01, .99], [.735, .735], color=RULE, lw=.6)
    # ---- (b) two histories, one projection
    panel_title(ax, .01, .705, '(b) Two histories that project onto the same observation at A1 / A2')
    def chain(y, tag, nodes, star_idx, note):
        ax.text(.01, y + .035, tag, ha='left', va='center', fontsize=7.8, weight='bold', color=INK)
        x0 = .04; w, h, gap = .105, .07, .055
        pos = []
        for i, (c, sub) in enumerate(nodes):
            x = x0 + i * (w + gap); pos.append(x)
            observed = i < 2
            rbox(ax, x, y - h / 2 + .035, w, h, edge=BLUE if observed else GRAY, face=BLUE_L if observed else 'white', ls='-' if observed else '--', r=.01)
            ax.text(x + w / 2, y + .035 + (h * .18 if sub else 0), c, ha='center', va='center', fontsize=7.8, weight='bold', color=BLUE if observed else INK)
            if sub: ax.text(x + w / 2, y + .035 - h * .22, sub, ha='center', va='center', fontsize=6.4, color=GRAY)
            if i == star_idx:
                ax.text(x + w - .012, y + .035 + h / 2 - .004, '★', ha='center', va='center', fontsize=9, color=ORANGE, zorder=6)
        for i in range(len(nodes) - 1):
            arrow(ax, (pos[i + 1], y + .035), (pos[i] + w, y + .035), color=BLUE if i == 0 else GRAY, lw=1.0, ms=7)
        ax.text(pos[-1] + w + .02, y + .035, note, ha='left', va='center', fontsize=7.0, color=GRAY, linespacing=1.25)
    chain(.615, 'H₁', [('A1', 'ingress p5'), ('A2', 'p23 notified'), ('X', 'local change ★')], 2, 'X detects a change\nand notifies upstream.')
    chain(.49, 'H₂', [('A1', 'ingress p5'), ('A2', 'p23 notified'), ('X', 'relay'), ('Y', 'change ★')], 3, 'X forwards Y’s\nnotification upstream.')
    # projection box
    rbox(ax, .04, .33, .60, .105, edge=BLUE, face=BLUE_L, r=.012)
    ax.text(.34, .41, 'Identical observation E in both histories', ha='center', va='center', fontsize=7.8, weight='bold', color=BLUE)
    ax.text(.34, .36, 'same A1 ingress (p5) · same ΔC = ΔB · same A1–A2 adjacency · same A2 log direction (p23)', ha='center', va='center', fontsize=6.7, color=INK)
    ax.plot([.015, .015, .025], [.655, .455, .455], color=BLUE, lw=.8, ls=':'); ax.plot([.015, .025], [.655, .655], color=BLUE, lw=.8, ls=':')
    arrow(ax, (.015, .455), (.06, .437), color=BLUE, lw=.8, ms=7, ls=':', shrink=0)
    label(ax, .045, .47, 'projection', size=6.4, color=BLUE, ha='left', bg=False)
    rbox(ax, .67, .33, .32, .105, edge=ORANGE, face=ORANGE_L, ls=(0, (4, 2)), r=.012)
    ax.text(.83, .41, 'Required to separate H₁ from H₂', ha='center', va='center', fontsize=7.8, weight='bold', color=ORANGE)
    ax.text(.83, .36, 'X’s local detect / receive logs\nand captures on both sides of X', ha='center', va='center', fontsize=7.0, color=INK, linespacing=1.25)
    ax.text(.04, .30, 'Solid blue boxes: devices and ports observed in this incident; dashed boxes: unobserved devices on the unknown path U. ★ marks the physical origin of the change.', ha='left', va='center', fontsize=6.8, color=GRAY)
    ax.plot([.01, .99], [.27, .27], color=RULE, lw=.6)
    # ---- (c) message fields
    panel_title(ax, .01, .24, '(c) What the message fields can and cannot preserve')
    def fields(x, y, title, cells, widths, hl=None):
        ax.text(x, y + .075, title, ha='left', va='center', fontsize=7.6, weight='bold', color=INK)
        cx = x
        for i, (c, w) in enumerate(zip(cells, widths)):
            face = ORANGE_L if hl == i else 'white'; edge = ORANGE if hl == i else GRAY
            ax.add_patch(Rectangle((cx, y), w, .055, facecolor=face, edgecolor=edge, lw=.8, zorder=2))
            ax.text(cx + w / 2, y + .0275, c, ha='center', va='center', fontsize=6.6, color=INK, zorder=3); cx += w
    fields(.04, .13, 'TCN BPDU', ['Protocol ID', 'Version', 'Type = TCN'], [.09, .07, .10])
    ax.text(.04, .095, 'No bridge or port identity at all → the ingress reveals\nonly the direction of the last hop.', ha='left', va='center', fontsize=6.9, color=GRAY, linespacing=1.25)
    fields(.40, .13, 'Configuration BPDU (TC flag set)', ['Flags: TC | TCA', 'Root ID', 'Bridge ID', 'Port ID', 'Timers'], [.11, .09, .11, .09, .09], hl=2)
    ax.text(.40, .095, 'Bridge ID = the designated sender of this BPDU, not the\nbridge that originally detected the topology change.', ha='left', va='center', fontsize=6.9, color=GRAY, linespacing=1.25)
    ax.text(.5, .025, 'Original drawing from protocol semantics; fields are not to byte scale, and the chronology is not a reconstruction of the observed site.', ha='center', va='center', fontsize=6.6, color=GRAY)
    save(fig, 'fig1_protocol_identity')

# ================================================================ Fig. 3 ===
def fig3():
    fig, ax = canvas(6.7, 5.2)
    lanes = [('Field semantics  Hₛ(E)', .615, .25), ('Local structure  Hɡ(E)', .395, .2), ('Device-local time  Hₜ(E)', .215, .16)]
    for name, y, h in lanes:
        ax.add_patch(Rectangle((.0, y), 1.0, h, facecolor=GRAY_L, edgecolor='none', zorder=0))
        ax.text(.008, y + h - .016, name, ha='left', va='top', fontsize=7.2, weight='bold', color=GRAY)
    panel_title(ax, .008, .975, 'Inputs (retrospective, anonymised CLI material)')
    srcs = [('A1 snapshots, 30 Oct', '14 checkpoints × 27 interfaces'), ('A1/A2 paired snapshots, 30 Oct', 'per-port BPDU counters · LLDP · logs'), ('Native counters, 2 Nov', 'display stp tc · bpdu-statistics · logbuffer')]
    for i, (t, sub) in enumerate(srcs):
        x = .008 + i * .335
        rbox(ax, x, .885, .32, .07, edge=BLUE, face=BLUE_L, r=.01)
        ax.text(x + .16, .935, t, ha='center', va='center', fontsize=7.3, weight='bold', color=BLUE); ax.text(x + .16, .903, sub, ha='center', va='center', fontsize=6.0, color=INK)
    def step(x, y, w, h, title, detail, ref):
        rbox(ax, x, y, w, h, edge=GRAY, face='white', r=.01)
        ax.text(x + w / 2, y + h - .021, title, ha='center', va='center', fontsize=7.1, weight='bold')
        ax.text(x + w / 2, y + h / 2 - .012, detail, ha='center', va='center', fontsize=5.9, color=INK, linespacing=1.25)
        ax.text(x + w - .006, y + .005, ref, ha='right', va='bottom', fontsize=5.5, color=GRAY)
    xs = [.03, .275, .52, .765]; w, h, y = .215, .13, .645
    steps1 = [('① Parse & reconcile', 'type sums = totals;\nno cumulative decreases', '§3.2'),
              ('② Verify checkpoint order', '6 Tx counters, 91 pairs each,\n0 ties / 0 inversions', '§3.2 · §4.1'),
              ('③ Per-hop concordance', 'R1–R5 (Eqs. 2–5), designated ports\nA1 → {GE1/0/5}; A2 → {GE1/0/23}', '§3.4 · §4.2–4.3'),
              ('④ Boundaries', '7 constructed scenarios (Eq. 6)\n6 × 30 simulation · enumeration', '§3.3, 3.6 · §4.5–4.7')]
    for (t, d, r), x in zip(steps1, xs): step(x, y, w, h, t, d, r)
    for a_, b_ in zip(xs, xs[1:]): arrow(ax, (a_ + w, y + h / 2), (b_, y + h / 2), color=GRAY, lw=.9, ms=7)
    arrow(ax, (.168, .885), (.168, y + h), color=BLUE, lw=.9, ms=7)
    y2 = .41
    step(.15, y2, .33, .13, '⑤ Cross-device chain', 'LLDP / bridge-port identity A1 p5 ⟷ A2 p25\n+8 TCN (A2 p23) → +8 MST → +8 at A1\nlink-end offsets 2, 2, 1, 1', '§3.5 · §4.3')
    step(.52, y2, .33, .13, '⑥ Native verification', 'Σ per-port TC rx = global (1,729,714)\nA2→A1 TC 1,729,649 = 1,729,649\nsend deficit · TC detected → A2 relays', '§3.5 · §4.4')
    arrow(ax, (.6275, y), (.6275, y2 + .13), color=GRAY, lw=.9, ms=7)
    ax.plot([.99, .99], [.885, y2 + .065], color=BLUE, lw=.9, ls=':', zorder=1); ax.plot([.838, .838, .99], [.885, .875, .875], color=BLUE, lw=.9, ls=':', zorder=1)
    arrow(ax, (.99, y2 + .065), (.85, y2 + .065), color=BLUE, lw=.9, ms=7, ls=':', shrink=0)
    arrow(ax, (.48, y2 + .065), (.52, y2 + .065), color=GRAY, lw=.9, ms=7)
    ax.plot([.505, .505], [.885, y2 + .16], color=BLUE, lw=.9, zorder=1)
    arrow(ax, (.505, y2 + .16), (.40, y2 + .13), color=BLUE, lw=.9, ms=7, shrink=0)
    y3 = .228
    step(.275, y3, .46, .12, '⑦ Unchanged-counter windows & operation order', 'T₀ = aᵥ − aᵤ (Eq. 7): 289 s · 234 s · 233 s; Hello proxy 234 s\nshutdown → undo shutdown ≈ 19 min 6 s on A2 (device-local)', '§3.7 · §4.8')
    arrow(ax, (.505, y2), (.505, y3 + .12), color=GRAY, lw=.9, ms=7)
    outs = [('Observed facts', 'unique ingress per hop: A1 GE1/0/5, A2 GE1/0/23\nzero-discrepancy native reconciliation\nA2 relays; offset C − B explained', BLUE, BLUE_L, '-'),
            ('Compatible explanations', 'origin: X local (H₁) · Y via X (H₂) · beyond Y\nmaintenance convergence · link flap\nwireless contention', GRAY, 'white', '-'),
            ('Unresolved → next measurements', 'TC-detected record on X (and Y)\nsynchronised FDB · packets · transactions\n(Table 9, Figure 9)', ORANGE, ORANGE_L, (0, (4, 2)))]
    yo, ho = .035, .12
    for i, (t, d_, e, f, ls) in enumerate(outs):
        x = .008 + i * .335
        rbox(ax, x, yo, .32, ho, edge=e, face=f, ls=ls, r=.01)
        ax.text(x + .16, yo + ho - .022, t, ha='center', va='center', fontsize=7.2, weight='bold', color=e)
        ax.text(x + .16, yo + .045, d_, ha='center', va='center', fontsize=5.9, color=INK, linespacing=1.25)
    ytop = yo + ho; ymid = (y3 + ytop) / 2
    ax.plot([.168, .838], [ymid, ymid], color=GRAY, lw=.9, zorder=1)
    ax.plot([.505, .505], [y3, ymid], color=GRAY, lw=.9, zorder=1)
    for xx in [.168, .505, .838]: arrow(ax, (xx, ymid), (xx, ytop), color=GRAY, lw=.9, ms=7, shrink=0)
    ax.text(.992, .004, 'H(E) = Hₛ(E) ∩ Hɡ(E) ∩ Hₜ(E) (Eq. 1) is evaluated on a finite hypothesis space (step ④).', ha='right', va='bottom', fontsize=5.9, color=GRAY)
    save(fig, 'fig3_workflow')

# ================================================================ Fig. 4 ===
def fig4():
    fig = plt.figure(figsize=(6.7, 4.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.45, 1], height_ratios=[1, 1], hspace=.55, wspace=.32, left=.085, right=.985, top=.93, bottom=.1)
    k = np.arange(1, K + 1); ki = np.arange(2, K + 1)
    # (a)
    ax = fig.add_subplot(gs[0, 0])
    for z in ZERO: ax.axvspan(z - 1, z, color=tint(SKY, .8), zorder=0)
    ax.plot(k, C - C[0], '-', color=BLUE, lw=1.1, marker='o', ms=4.2, label='Global TC/TCN received  (C − C₁)')
    ax.plot(k, B5 - B5[0], ls='none', marker='o', ms=7.5, mfc='none', mec=ORANGE, mew=1.0, label='GE1/0/5 BPDU received  (B − B₁)')
    ax.set(xlabel='Checkpoint index k', ylabel='Cumulative increase', xticks=k); ax.set_ylim(-4, 104)
    ax.annotate('+92', (14, 92), xytext=(12.6, 100), fontsize=7.6, color=INK)
    ax.text(ZERO[0] - .5, 6, 'I', ha='center', fontsize=7.4, color=GRAY); ax.text(ZERO[1] - .5, 6, 'II', ha='center', fontsize=7.4, color=GRAY)
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.0), handlelength=1.6, borderaxespad=0)
    ax.set_title('(a) Co-variation of the two counters', loc='left')
    # (b)
    ax = fig.add_subplot(gs[1, 0])
    for z in ZERO: ax.axvspan(z - 1, z, color=tint(SKY, .8), zorder=0)
    ax.bar(ki, dC, width=.62, color=BLUE_M, edgecolor=BLUE, lw=.6, label='ΔCₖ (global)')
    ax.plot(ki, dB5, ls='none', marker='D', ms=4.2, color=ORANGE, label='ΔB₅,ₖ (GE1/0/5)')
    for x, v in zip(ki, dC): ax.text(x, v + 1.2, str(v), ha='center', va='bottom', fontsize=6.4, color=GRAY)
    ax.set(xlabel='Interval ending at checkpoint k', ylabel='Interval increment', xticks=ki); ax.set_ylim(0, 50)
    ax.text(ZERO[0] - .5, 30, 'zero\n(not in\nSₚ)', ha='center', va='top', fontsize=6.0, color=GRAY, linespacing=1.1)
    ax.text(ZERO[1] - .5, 30, 'zero', ha='center', va='top', fontsize=6.0, color=GRAY)
    ax.legend(loc='upper center', bbox_to_anchor=(.55, 1.0), handlelength=1.4, ncol=2, columnspacing=1.0); ax.set_title('(b) Interval increments: 11 of 11 active intervals match', loc='left')
    # (c) constant difference
    ax = fig.add_subplot(gs[0, 1])
    diff = C - B5
    ax.plot(k, diff, '-', color=INK, lw=1.0, marker='s', ms=3.6, mfc='white', mec=INK)
    ax.set(xlabel='Checkpoint index k', ylabel='C − B (GE1/0/5)', xticks=[1, 4, 7, 10, 14])
    ax.set_ylim(diff[0] - 3, diff[0] + 3); ax.set_yticks([diff[0] - 2, diff[0], diff[0] + 2])
    ax.ticklabel_format(axis='y', style='plain', useOffset=False)
    ax.text(7.5, diff[0] + 1.0, f'constant −{abs(diff[0])} at all 14 checkpoints', ha='center', fontsize=6.8, color=INK)
    ax.text(7.5, diff[0] - 1.6, 'equivalent to ΔB = ΔC on all 13 intervals;\nindependent of record order', ha='center', fontsize=6.3, color=GRAY, linespacing=1.2)
    ax.set_title('(c) Constant offset', loc='left')
    # (d) windows
    ax = fig.add_subplot(gs[1, 1])
    rows = [('I · A1  (ck 9→10)', 'aggregation_sd'), ('II · A1  (ck 13→14)', 'aggregation_fx'), ('II · A2  (paired)', 'access_fx')]
    for i, (lab, key) in enumerate(rows):
        w = next(r for r in WIN if r['window'] == key); a0, a1 = int(w['age_first_s']), int(w['age_second_s']); T = int(w['relative_interval_s'])
        y = 2 - i
        ax.plot([0, T], [y, y], color=BLUE, lw=2.2, solid_capstyle='butt'); ax.plot([0, T], [y, y], ls='none', marker='o', ms=4.5, mfc='white', mec=BLUE, mew=1.1)
        ax.text(T + 8, y, f'{T} s', va='center', fontsize=7.4, color=INK)
        ax.text(T / 2, y + .22, f'timer {a0} s → {a1} s, C unchanged', ha='center', va='bottom', fontsize=6.0, color=GRAY)
    ax.set_yticks([2, 1, 0]); ax.set_yticklabels([r[0] for r in rows]); ax.set_ylim(-.6, 2.7); ax.set_xlim(0, 360)
    ax.set_xlabel('Relative duration (s), own origin per window')
    ax.set_title('(d) Unchanged-counter windows', loc='left')
    save(fig, 'fig4_counters')

# ================================================================ Fig. 5 ===
def fig5():
    # matrix of matches: 27 interfaces x 13 intervals
    ifaces = []
    for r in SNAP:
        if r['checkpoint'] == '1': ifaces.append((r['interface'], r['state'], r['role'], int(r['bpdu_received'])))
    last = {r['interface']: int(r['bpdu_received']) for r in SNAP if r['checkpoint'] == str(K)}
    def short(n): return n.replace('Ten-GigabitEthernet', 'XGE').replace('GigabitEthernet', 'GE').replace('Bridge-Aggregation1', 'BAGG1')
    fwd = [i for i in ifaces if i[1] == 'FORWARDING']; down = [i for i in ifaces if i[1] != 'FORWARDING']
    order = [i for i in fwd if '1/0/5' in i[0]] + [i for i in fwd if '1/0/5' not in i[0]] + down
    names = [o[0] for o in order]
    M = np.zeros((len(order), K - 1), dtype=int); dB = np.zeros_like(M)
    for r in INT:
        i = names.index(r['interface']); j = int(r['checkpoint']) - 2
        M[i, j] = 1 if r['numerical_match'] == 'True' else 0; dB[i, j] = int(r['port_bpdu_delta'])
    nF = len(fwd)
    fig = plt.figure(figsize=(6.7, 5.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 11], width_ratios=[13, 3.2], hspace=.04, wspace=.05, left=.17, right=.985, top=.95, bottom=.11)
    # top: ΔC strip
    axt = fig.add_subplot(gs[0, 0])
    axt.bar(np.arange(K - 1), dC, color=BLUE_M, edgecolor=BLUE, lw=.5, width=.8)
    for j, v in enumerate(dC): axt.text(j, v + 2, str(v), ha='center', va='bottom', fontsize=6.4, color=INK)
    axt.set_xlim(-.5, K - 1.5); axt.set_ylim(0, 60); axt.set_xticks([]); axt.set_yticks([]); axt.spines['left'].set_visible(False); axt.spines['bottom'].set_visible(False)
    axt.set_ylabel('ΔCₖ', rotation=0, ha='right', va='center', fontsize=7.6)
    axt.set_title('Match matrix: ΔBₚ,ₖ = ΔCₖ for 27 interfaces × 13 adjacent intervals', loc='left', fontsize=8.6)
    # main matrix
    ax = fig.add_subplot(gs[1, 0])
    cmap = ListedColormap(['#FFFFFF', BLUE])
    ax.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect='auto', interpolation='nearest')
    for j in range(K - 1):
        if (j + 2) in ZERO: ax.axvspan(j - .5, j + .5, color=tint(SKY, .6), zorder=1)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=BLUE, label='match in active interval (ΔB = ΔC > 0)'), Patch(facecolor=tint(SKY, .6), label='trivial match in zero interval (0 = 0)'), Patch(facecolor='white', edgecolor=GRAY_M, label='mismatch (ΔB = 0 ≠ ΔC)')],
              loc='upper left', bbox_to_anchor=(0, -.11), ncol=3, fontsize=6.4, handlelength=1.2, columnspacing=1.2, frameon=False)
    for j in range(K - 1):
        for i in range(len(order)):
            if M[i, j]:
                ax.text(j, i, '=', ha='center', va='center', fontsize=6.2, color='white', weight='bold')
    # grid
    ax.set_xticks(np.arange(-.5, K - 1, 1), minor=True); ax.set_yticks(np.arange(-.5, len(order), 1), minor=True)
    ax.grid(which='minor', color=GRAY_M, lw=.4); ax.tick_params(which='minor', length=0)
    ax.set_xticks(np.arange(K - 1)); ax.set_xticklabels([f'{j + 1}→{j + 2}' for j in range(K - 1)], fontsize=6.4, rotation=90)
    ax.set_yticks(np.arange(len(order))); ax.set_yticklabels([short(n) for n in names], fontsize=6.4)
    ax.axhline(nF - .5, color=INK, lw=1.0); ax.axhline(.5, color=INK, lw=1.0)
    ax.set_xlabel('Adjacent interval (checkpoint k−1 → k)', fontsize=7.4)
    for sp in ax.spines.values(): sp.set_visible(True); sp.set_color(GRAY)
    ax.text(-.5 - 3.9, (nF + .5) / 2 + .5 - .5, '', fontsize=6)
    # group labels at left outside
    ax.text(-4.6, 0, 'candidate', ha='right', va='center', fontsize=6.4, color=ORANGE, weight='bold', transform=ax.transData)
    ax.text(-4.6, (1 + nF - 1) / 2, '5 other\nFORWARDING', ha='right', va='center', fontsize=6.4, color=GRAY, linespacing=1.1)
    ax.text(-4.6, (nF + len(order) - 1) / 2, '21 DOWN', ha='right', va='center', fontsize=6.4, color=GRAY)
    # right: counts
    axr = fig.add_subplot(gs[1, 1], sharey=ax)
    act = M[:, [j for j in range(K - 1) if (j + 2) not in ZERO]].sum(1); allm = M.sum(1)
    axr.barh(np.arange(len(order)), act, color=BLUE, height=.62, label='active 11')
    axr.barh(np.arange(len(order)), allm - act, left=act, color=tint(SKY, .6), height=.62, label='+ zero intervals')
    for i in range(len(order)):
        axr.text(13.3, i, f'{act[i]}/11 · {allm[i]}/13', va='center', fontsize=5.9, color=INK)
    axr.set_xlim(0, 26); axr.set_xticks([0, 11]); axr.tick_params(axis='y', left=False, labelleft=False); axr.tick_params(axis='x', labelsize=6.2)
    axr.spines['left'].set_visible(False); axr.set_xlabel('matches', fontsize=7.0)
    axr.legend(loc='lower right', fontsize=6.0, handlelength=1.0, bbox_to_anchor=(1.02, 1.0), ncol=1, borderaxespad=0)
    # totals annotation
    tot = {n: last[n] - f for n, _, _, f in order}
    axr.text(13.3, 0, f'11/11 · 13/13  (ΔB = +{tot[names[0]]})', va='center', fontsize=5.9, color=ORANGE, weight='bold', bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': .5})
    save(fig, 'fig5_match_matrix')

# ================================================================ Fig. 6 ===
def fig6():
    cases = [('ideal_single_ingress', '(a) Ideal single ingress', 'TC-bearing ingress: P1'),
             ('one_background_bpdu_on_true_ingress', '(b) One extra ordinary BPDU on P1', 'TC-bearing ingress: P1'),
             ('two_true_ingresses', '(c) Two TC-bearing ingresses', 'TC-bearing ingresses: P1 + P2'),
             ('true_ingress_background_and_coincident_distractor', '(d) Coincident numerical match', 'TC-bearing ingress: P1')]
    fig, axes = plt.subplots(2, 2, figsize=(6.7, 5.0), sharex=True, sharey=True)
    fig.subplots_adjust(left=.08, right=.985, top=.90, bottom=.13, hspace=.38, wspace=.10)
    for ax, (key, title, sub) in zip(axes.flat, cases):
        rows = [r for r in MODEL if r['scenario'] == key and r['active_interval'] == 'True']
        x = np.arange(1, len(rows) + 1); g = [int(r['global_tc_delta']) for r in rows]; p1 = [int(r['observed_bpdu_P1']) for r in rows]; p2 = [int(r['observed_bpdu_P2']) for r in rows]
        ax.plot(x, g, '-', color=GRAY, lw=1.0, marker='o', ms=6.5, mfc='white', mec=GRAY, zorder=2)
        ax.plot(x, p1, '-', color=BLUE, lw=1.0, marker='o', ms=3.4, zorder=3)
        ax.plot(x, p2, '--', color=ORANGE, lw=1.0, marker='^', ms=3.8, mfc='white', zorder=3)
        s_ = MSUM[key]; cand = s_['strict_candidates'].replace('EMPTY', '∅').replace(';', ', ')
        cand = '{' + cand + '}' if cand != '∅' else '∅'
        wrong = key.startswith('true_ingress_background')
        ax.set_title(title, loc='left', fontsize=8.4, pad=4)
        ax.text(.98, .97, sub, transform=ax.transAxes, fontsize=6.6, color=GRAY, ha='right', va='top')
        ax.text(.98, .86, f"Active matches: P1 {s_['P1_matches']}/11 · P2 {s_['P2_matches']}/11", transform=ax.transAxes, fontsize=6.8, color=INK, ha='right', va='top')
        ax.text(.98, .75, f'Strict candidate: {cand}', transform=ax.transAxes, fontsize=7.4, weight='bold', color=ORANGE if wrong else INK, ha='right', va='top')
        if key == 'one_background_bpdu_on_true_ingress' or wrong:
            ax.annotate('+1 ordinary BPDU on P1\n(3 → 4)', (1, 4), xytext=(2.6, 22), fontsize=6.4, color=BLUE, arrowprops={'arrowstyle': '-', 'color': BLUE, 'lw': .7, 'shrinkB': 3}, linespacing=1.15)
        ax.set_xticks(x); ax.set_ylim(-2, 52)
    for ax in axes[1]: ax.set_xlabel('Active interval (constructed)')
    for ax in axes[:, 0]: ax.set_ylabel('Counter increment')
    h = [Line2D([], [], color=GRAY, marker='o', mfc='white', ms=6.5, lw=1, label='Global ΔC'), Line2D([], [], color=BLUE, marker='o', ms=3.4, lw=1, label='P1: ΔB'), Line2D([], [], color=ORANGE, ls='--', marker='^', mfc='white', ms=3.8, lw=1, label='P2: ΔB')]
    fig.legend(handles=h, loc='upper center', ncol=3, bbox_to_anchor=(.5, .985), handlelength=1.8)
    fig.text(.08, .02, 'Constructed count models (Eq. 5): ΔC follows the field sequence; backgrounds and source splits are hypothetical.\nMatch counts express numerical equality only, not diagnostic accuracy. All seven scenarios: Table 7.', fontsize=6.6, color=GRAY, linespacing=1.3)
    save(fig, 'fig7_rule_boundary')

# ================================================================ Fig. 7 ===
def fig7():
    fig, ax = canvas(6.7, 4.4)
    rbox(ax, .03, .835, .94, .12, edge=BLUE, face=BLUE_L, r=.012)
    ax.text(.5, .92, 'Observed facts in this incident (control plane / structure)', ha='center', va='center', fontsize=8.4, weight='bold', color=BLUE)
    ax.text(.5, .865, 'TC-related counters (A1, A2)   •   port notification logs (A2 p23)   •   LLDP / bridge-port adjacency   •   device-local operation order', ha='center', va='center', fontsize=7.2, color=INK)
    ax.text(.5, .805, 'These facts constrain the notification direction; they do not measure the mechanism below.', ha='center', va='center', fontsize=7.2, color=BLUE, style='italic')
    ax.plot([.03, .97], [.775, .775], color=RULE, lw=.6)
    ax.text(.5, .748, 'Hypothesised cross-layer pathway — not established by this event', ha='center', va='center', fontsize=8.4, weight='bold', color=ORANGE)
    cols = [(.155, 'Competing explanations'), (.5, 'Unmeasured mechanism'), (.835, 'Discriminating measurement')]
    for x, t in cols: ax.text(x, .705, t, ha='center', va='center', fontsize=7.6, weight='bold')
    ys = [.575, .435, .295, .155]; h = .085; xm, wm = .37, .26
    mech = ['TC handling\n(flush / ageing change)', 'FDB refresh /\naddress relearning', 'Unknown unicast,\nloss / retransmission', 'Transaction completion\ntime (user-visible stall)']
    meas = ['TC types & flags per hop;\nsynchronised capture clocks', 'FDB update & ageing events;\nunknown-unicast counters', 'Packet traces at A2 / A1;\nloss & retransmission counts', 'Fixed-transaction FCT\ndistribution; failure rate']
    for y, m, s in zip(ys, mech, meas):
        rbox(ax, xm, y, wm, h, m, edge=ORANGE, face=ORANGE_L, ls=(0, (4, 2)), size=7.3)
        rbox(ax, .70, y, .27, h, s, edge=GRAY, face=GRAY_L, size=7.0)
        ax.plot([xm + wm + .01, .69], [y + h / 2, y + h / 2], color=GRAY_M, lw=.7, ls=':')
    for a, b in zip(ys, ys[1:]): arrow(ax, (xm + wm / 2, a), (xm + wm / 2, b + h), color=ORANGE, lw=1.0, ls=(0, (4, 2)), ms=8)
    comp = [(.575, 'Normal maintenance\nconvergence'), (.295, 'Physical link\ninstability (A2 p23)'), (.155, 'Wireless contention\n(busy time, retries)')]
    for y, t in comp:
        rbox(ax, .03, y, .25, h, t, edge=ORANGE, face='white', ls=(0, (4, 2)), size=7.3)
        arrow(ax, (.28, y + h / 2), (xm, y + h / 2), color=ORANGE, lw=1.0, ls=(0, (4, 2)), ms=8)
    ax.text(.155, .455, 'selected alternative routes,\nnot an exhaustive causal graph', ha='center', va='center', fontsize=6.6, color=GRAY, linespacing=1.2)
    ax.text(.03, .075, 'Orange dashed: hypotheses, including competing routes.  Grey dotted: alignment of a measurement with a layer, not a measured relation.', ha='left', va='center', fontsize=6.6, color=GRAY)
    ax.text(.03, .04, 'FDB dynamics, packet traces and application outcomes were not obtained in this study (see Table 9).', ha='left', va='center', fontsize=6.6, color=GRAY)
    save(fig, 'fig9_mechanism')


# ================================================================ Fig. 6 (new) counter chain ===
RES = next(p for p in [Path(__file__).resolve().parent / 'results', Path(__file__).resolve().parent.parent / 'results'] if p.exists())
def fig_chain():
    S3 = json.load(open(RES / 'summary_v3.json', encoding='utf-8'))
    cd = S3['cross_device']; nat = S3['native']
    fig = plt.figure(figsize=(6.7, 5.3))
    # (a) chain diagram
    ax = fig.add_axes([0.0, 0.62, 1.0, 0.38]); ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis('off')
    panel_title(ax, .01, .95, '(a) One active paired interval (ep0 → ep1): counter increments along the path')
    iv = cd['intervals'][0]
    boxes = [(.01, 'A2 GE1/0/23', 'designated · boundary', f"+{iv['A2_p23_d_rx_tcn']} TCN received", 'legacy BPDUs from U'),
             (.21, 'A2 global', 'TC or TCN received', f"+{iv['A2_d_global']}", 'A2 relays (native, §4.4)'),
             (.41, 'A2 GE1/0/25', 'root port · boundary', f"+{iv['A2_p25_d_tx_mst']} MST sent", f"+{iv['A2_p25_d_rx_hello']} Hellos received"),
             (.61, 'A1 GE1/0/5', 'designated · boundary', f"+{iv['A1_p5_d_rx_mst']} MST received", 'type: MST only'),
             (.81, 'A1 global', 'TC or TCN received', f"+{iv['A1_d_global']}", 'A1 = CIST root')]
    for i, (x, t, r, v, n) in enumerate(boxes):
        dev2 = t.startswith('A2')
        rbox(ax, x, .22, .18, .58, edge=BLUE, face=BLUE_L if 'global' not in t else 'white', r=.02)
        ax.text(x + .09, .70, t, ha='center', va='center', fontsize=7.6, weight='bold', color=BLUE)
        ax.text(x + .09, .60, r, ha='center', va='center', fontsize=6.0, color=GRAY)
        ax.text(x + .09, .45, v, ha='center', va='center', fontsize=8.2, weight='bold', color=INK)
        ax.text(x + .09, .31, n, ha='center', va='center', fontsize=5.9, color=ORANGE if 'Hello' in n else GRAY)
        if i < 4: arrow(ax, (x + .18, .51), (boxes[i + 1][0], .51), color=BLUE, lw=1.2, ms=8)
    ax.plot([.205, .205], [.12, .86], color=GRAY_M, lw=.6, ls=':'); 
    ax.text(.30, .10, 'device A2 (access)', ha='center', fontsize=6.4, color=GRAY); ax.text(.80, .10, 'device A1 (aggregation, root)', ha='center', fontsize=6.4, color=GRAY)
    ax.plot([.60, .60], [.15, .86], color=GRAY, lw=.8, ls='--'); ax.text(.60, .885, 'A1–A2 link (LLDP)', ha='center', fontsize=6.0, color=GRAY)
    # (b) link-end offsets
    ax = fig.add_axes([0.085, 0.17, 0.33, 0.36])
    snaps = cd['snapshots']; xs = np.arange(len(snaps))
    ax.plot(xs, [r['tx_minus_rx_A2toA1'] for r in snaps], '-o', color=BLUE, lw=1.1, ms=4.5, label='A2 p25 sent − A1 p5 received')
    ax.plot(xs, [r['rx_minus_tx_A1toA2'] for r in snaps], '--s', color=ORANGE, lw=1.1, ms=4.2, mfc='white', label='A2 p25 received − A1 p5 sent')
    for x, r in zip(xs, snaps):
        ax.text(x, r['tx_minus_rx_A2toA1'] + .7, str(r['tx_minus_rx_A2toA1']), ha='center', fontsize=6.4, color=BLUE)
        ax.text(x, r['rx_minus_tx_A1toA2'] + .7, str(r['rx_minus_tx_A1toA2']), ha='center', fontsize=6.4, color=ORANGE)
    ax.set_xticks(xs); ax.set_xticklabels([r['snapshot'] for r in snaps]); ax.set_ylim(-1, 15)
    ax.set_xlabel('Paired snapshot'); ax.set_ylabel('BPDU count offset')
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.02), fontsize=6.3, handlelength=1.6)
    ax.set_title('(b) Link-end offsets (30 Oct)', loc='left')
    # (c) native per-port TC counters
    ax = fig.add_axes([0.59, 0.17, 0.37, 0.36])
    ports = ['GigabitEthernet1/0/5', 'GigabitEthernet1/0/1', 'GigabitEthernet1/0/2', 'GigabitEthernet1/0/3', 'GigabitEthernet1/0/7', 'Bridge-Aggregation1']
    lab = [p.replace('GigabitEthernet', 'GE').replace('Bridge-Aggregation1', 'BAGG1') for p in ports]
    native = json.load(open(RES / 'native_reconciliation.json', encoding='utf-8'))
    from collections import OrderedDict
    # receive values from the native table (stp tc)
    rx = {'GigabitEthernet1/0/5': nat['A1_p5_tc_receive']}
    sends = nat['A1_other_ports_tc_send']; sends['GigabitEthernet1/0/5'] = nat['A1_p5_tc_send']
    others_rx = {'GigabitEthernet1/0/1': 12, 'GigabitEthernet1/0/2': 12, 'GigabitEthernet1/0/3': 31, 'GigabitEthernet1/0/7': 10, 'Bridge-Aggregation1': 0}
    rx.update(others_rx)
    y = np.arange(len(ports)); hgt = .36
    ax.barh(y - hgt / 2, [max(rx[p], .8) for p in ports], height=hgt, color=BLUE, label='TC received')
    ax.barh(y + hgt / 2, [max(sends[p], .8) for p in ports], height=hgt, color=tint(ORANGE, .35), edgecolor=ORANGE, lw=.5, label='TC sent')
    ax.set_xscale('log'); ax.set_xlim(.7, 6e7); ax.set_yticks(y); ax.set_yticklabels(lab); ax.invert_yaxis()
    for i, p in enumerate(ports):
        ax.text(max(rx[p], .8) * 1.4, i - hgt / 2, f'{rx[p]:,}', va='center', fontsize=5.8, color=BLUE)
        ax.text(max(sends[p], .8) * 1.4, i + hgt / 2, f'{sends[p]:,}', va='center', fontsize=5.8, color=ORANGE)
    ax.set_xlabel('Count since boot (log scale)')
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, 1.0), ncol=2, fontsize=6.3, handlelength=1.2, borderaxespad=0.1)
    ax.set_title('(c) A1 native TC counters (2 Nov)', loc='left', pad=14)
    e = nat['end_to_end']
    txt = (f"A2→A1 TC  {e['TC_A2toA1'][0]:,} = {e['TC_A2toA1'][1]:,}\nA1→A2 TC  {e['TC_A1toA2'][0]} = {e['TC_A1toA2'][1]}\n"
           f"TCA  {e['TCA_A1toA2'][0]:,} = {e['TCA_A1toA2'][1]:,};  {e['TCA_A2toA1'][0]} = {e['TCA_A2toA1'][1]}")
    txt = txt.replace('\n', ' · ', 1).replace('\n', '\n')
    fig.text(.775, .03, 'Link-end equality, A2 GE1/0/25 vs A1 GE1/0/5:\n' + txt, ha='center', va='center', fontsize=5.8, color=INK, linespacing=1.3,
             bbox={'boxstyle': 'round,pad=0.35', 'facecolor': GRAY_L, 'edgecolor': GRAY_M, 'lw': .5})
    save(fig, 'fig6_counter_chain')

# ================================================================ Fig. 8 (new) simulation ===
def fig_sim():
    rows = list(csv.DictReader(open(RES / 'simulation_metrics.csv', encoding='utf-8')))
    conds = list(dict.fromkeys(r['condition'] for r in rows)); rules = ['R0_native_tc', 'R1_strict', 'R2_positive', 'R3_largest_cum', 'R4_tolerance', 'R5_subset_sum']
    rlab = ['R0 native TC', 'R1 strict', 'R2 positive', 'R3 largest cum.', 'R4 tolerance', 'R5 subset sum']
    clab = [c.split(' ', 1)[0] for c in conds]
    fig, axes = plt.subplots(1, 2, figsize=(6.7, 3.6), sharey=True)
    fig.subplots_adjust(left=.15, right=.90, top=.84, bottom=.20, wspace=.06)
    cmap = sns.light_palette(BLUE, as_cmap=True)
    for ax, dev, title in zip(axes, ['root A1-like', 'non-root A2-like'], ['(a) Root bridge (all ports designated)', '(b) Non-root bridge (root port receives Hellos)']):
        M = np.zeros((len(rules), len(conds)))
        for i, rn in enumerate(rules):
            for j, c in enumerate(conds):
                r = next(x for x in rows if x['condition'] == c and x['device'] == dev and x['rule'] == rn)
                M[i, j] = float(r['coverage'])
                ann = f"{float(r['coverage']) * 100:.0f}"
                sub = ''
                if float(r['wrong_unique']) > 0: sub = f"wrong {float(r['wrong_unique']) * 100:.0f}"
                elif float(r['empty']) > 0: sub = f"empty {float(r['empty']) * 100:.0f}"
                elif float(r['mean_set_size']) > 1.05 and float(r['exact']) < .5: sub = f"size {float(r['mean_set_size']):.1f}"
                col = 'white' if M[i, j] > .6 else INK
                ax.text(j, i - .12, ann, ha='center', va='center', fontsize=7.4, weight='bold', color=col)
                if sub: ax.text(j, i + .25, sub, ha='center', va='center', fontsize=5.3, color=col)
        im = ax.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(len(conds))); ax.set_xticklabels(clab); ax.set_yticks(range(len(rules))); ax.set_yticklabels(rlab)
        ax.set_xticks(np.arange(-.5, len(conds)), minor=True); ax.set_yticks(np.arange(-.5, len(rules)), minor=True)
        ax.grid(which='minor', color='white', lw=1.2); ax.tick_params(which='minor', length=0)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.set_title(title, loc='left', fontsize=8.0)
        ax.axhline(.5, color=INK, lw=.8)
    cax = fig.add_axes([.915, .20, .015, .64]); cb = fig.colorbar(im, cax=cax); cb.set_label('Coverage of true ingress set', fontsize=7); cb.ax.tick_params(labelsize=6.5)
    cb.set_ticks([0, .5, 1]); cb.set_ticklabels(['0', '50%', '100%'])
    fig.text(.15, .055, 'C0 baseline · C1 ordinary BPDUs on the root’s true ingress · C2 periodic background on another root port · C3 two ingresses · C4 readout skew ≤ 1 s · C5 = C1+C2+C4.\nCell: coverage (%) over 30 replications; second line: wrong unique, empty, or mean set size when extra candidates are returned. R0 uses native TC counters.', fontsize=5.9, color=GRAY, linespacing=1.3)
    save(fig, 'fig8_simulation')

if __name__ == '__main__':
    for f in [fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig_chain, fig_sim]: f()
