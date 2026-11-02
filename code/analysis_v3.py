#!/usr/bin/env python3
"""Revision analyses (v3) for the TC-ingress localization manuscript.

Standard library + numpy only.  Run:
    python3 analysis_v3.py --root <project folder> [--out results]

Sections
  A  field re-analysis from the 2026-10-30 snapshots (per-type increments,
     cross-device counter chain A2 GE1/0/23 -> A2 GE1/0/25 -> A1 GE1/0/5)
  B  native per-port TC counters collected 2026-11-02 (reconciliation,
     decomposition of the constant C - B)
  C  rules x scenarios on constructed count models (7 scenarios, 5 rules)
  D  protocol-level Monte Carlo simulation (6 conditions x 30 replications)
  E  finite-hypothesis identifiability enumeration for Eq. (1)
Every output row carries an evidence_type tag: field_observation,
native_counter, constructed_model or simulation.
"""
import argparse, csv, json, re, itertools, random
from pathlib import Path
from collections import defaultdict, OrderedDict
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--root', required=True)
ap.add_argument('--out', default=str(Path(__file__).resolve().parent / 'results'))
ap.add_argument('--seed', type=int, default=20261102)
A = ap.parse_args()
ROOT = Path(A.root); OUT = Path(A.out); OUT.mkdir(parents=True, exist_ok=True)
RAW = ROOT / '03_原始附件/脱敏交付包_解包/交付包/A_关键路径原始输出'
PKG = ROOT / '02_配套支撑资料' if (ROOT / '02_配套支撑资料').exists() else ROOT / 'inputs'
DATA = PKG / 'data'
NAT = ROOT / '补采包_20261102/2_原始输出'
SUMMARY = OrderedDict()

def wcsv(name, rows):
    with open(OUT / name, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def clean(p):
    return Path(p).read_bytes().decode('utf-8', 'ignore').replace('\r', '').replace('\x00', '')

# ------------------------------------------------------------------ parsers --
def parse_display_stp(path):
    t = clean(path)
    g = int(re.search(r'TC or TCN received\s*:\s*(\d+)', t).group(1))
    m = re.search(r'Time since last TC\s*:\s*(\d+) days (\d+)h:(\d+)m:(\d+)s', t)
    age = int(m.group(1)) * 86400 + int(m.group(2)) * 3600 + int(m.group(3)) * 60 + int(m.group(4)) if m else None
    ports = OrderedDict()
    for mm in re.finditer(r'----\[Port(\d+)\((\S+?)\)\]\[(\w+)\]----(.*?)(?=----\[Port|\Z|<)', t, re.S):
        blk = mm.group(4)
        role = re.search(r'Port role\s*:\s*(.*)', blk)
        s = re.search(r'BPDU sent\s*:\s*(\d+)\s*\n\s*TCN: (\d+), Config: (\d+), RST: (\d+), MST: (\d+)', blk)
        r = re.search(r'BPDU received\s*:\s*(\d+)\s*\n\s*TCN: (\d+), Config: (\d+), RST: (\d+), MST: (\d+)', blk)
        if not (s and r): continue
        ports[mm.group(2)] = dict(state=mm.group(3), role=role.group(1).strip() if role else '',
                                 sent=dict(zip(['total', 'tcn', 'config', 'rst', 'mst'], map(int, s.groups()))),
                                 recv=dict(zip(['total', 'tcn', 'config', 'rst', 'mst'], map(int, r.groups()))))
    return dict(global_tc=g, last_tc_age_s=age, ports=ports)

def parse_native(path):
    t = clean(path)
    out = dict(uptime=re.search(r'uptime is (.*)', t).group(1).strip())
    tc = OrderedDict()
    sec = t.split('display stp tc', 1)[1].split('<', 1)[0]
    for m in re.finditer(r'^\s*0\s+(\S+)\s+(\d+)\s+(\d+)\s*$', sec, re.M):
        tc[m.group(1)] = dict(receive=int(m.group(2)), send=int(m.group(3)))
    out['stp_tc'] = tc
    bs = {}
    for m in re.finditer(r'display stp bpdu-statistics interface GigabitEthernet ?(\S+)\s*\n(.*?)<', t, re.S):
        d = {}
        for line in m.group(2).splitlines():
            mm = re.match(r'\s*(Invalid BPDUs|Looped-back BPDUs|Max-aged BPDUs|TCN sent|TCN received|TCA sent|TCA received|Config sent|Config received|RST sent|RST received|MST sent|MST received|Timeout BPDUs|Max-hoped BPDUs|TC detected|TC sent|TC received)\s+(\d+)\s*(.*)$', line)
            if mm: d[mm.group(1)] = dict(count=int(mm.group(2)), last=mm.group(3).strip())
        if d and ('GigabitEthernet' + m.group(1)) not in bs: bs['GigabitEthernet' + m.group(1)] = d
    out['bpdu_stats'] = bs
    stp = parse_display_stp(path)
    out['global_tc'] = stp['global_tc']; out['last_tc_age_s'] = stp['last_tc_age_s']
    out['notified_tc_log'] = len(re.findall(r'STP_NOTIFIED_TC', t))
    out['notified_tc_ports'] = sorted(set(re.findall(r'STP_NOTIFIED_TC: Instance 0.s port (\S+) was notified', t)))
    return out

# ============================================================ A. field data ==
snaps = [r for r in csv.DictReader(open(DATA / 'stp_all_port_snapshots.csv', encoding='utf-8-sig'))]
by = defaultdict(dict)
C = {}
for r in snaps:
    k = int(r['checkpoint']); by[k][r['interface']] = r; C[k] = int(r['global_tc_or_tcn_received'])
K = sorted(C); P = list(by[K[0]])
dC = {k: C[k] - C[k - 1] for k in K[1:]}
active = [k for k in K[1:] if dC[k] > 0]

# A1: per-type increments of GE1/0/5 and all ports
rows = []
for k in K[1:]:
    a, b = by[k - 1]['GigabitEthernet1/0/5'], by[k]['GigabitEthernet1/0/5']
    rows.append(dict(interval=f'{k-1}->{k}', global_dC=dC[k],
                     dTCN=int(b['rx_tcn']) - int(a['rx_tcn']), dConfig=int(b['rx_config']) - int(a['rx_config']),
                     dRST=int(b['rx_rst']) - int(a['rx_rst']), dMST=int(b['rx_mst']) - int(a['rx_mst']),
                     dTotal=int(b['bpdu_received']) - int(a['bpdu_received']), evidence_type='field_observation'))
wcsv('A1_ge105_type_increments.csv', rows)
tot = {x: sum(r[x] for r in rows) for x in ['dTCN', 'dConfig', 'dRST', 'dMST', 'dTotal', 'global_dC']}
SUMMARY['A1_ge105_type_totals'] = tot

# cross-device chain from paired A1/A2 snapshots
pairs = [('ep0', 7), ('ep1', 8), ('fx0', 13), ('fx1', 14)]
PARSED = PKG / 'data/parsed_counters.json'          # repository mode: parsed counters instead of raw CLI text
if RAW.exists():
    a1 = {n: parse_display_stp(RAW / f'{n}_IP-1103.out') for n, _ in pairs}
    a2 = {n: parse_display_stp(RAW / f'{n}_IP-1104.out') for n, _ in pairs}
else:
    _pc = json.load(open(PARSED, encoding='utf-8')); a1, a2 = _pc['A1_paired'], _pc['A2_paired']
chain = []
for n, k in pairs:
    p25 = a2[n]['ports']['GigabitEthernet1/0/25']; p23 = a2[n]['ports']['GigabitEthernet1/0/23']; p5 = a1[n]['ports']['GigabitEthernet1/0/5']
    chain.append(dict(snapshot=n, a1_checkpoint=k, A2_global_tc=a2[n]['global_tc'], A2_p23_rx_tcn=p23['recv']['tcn'],
                      A2_p25_tx_mst=p25['sent']['mst'], A1_p5_rx_mst=p5['recv']['mst'], tx_minus_rx_A2toA1=p25['sent']['mst'] - p5['recv']['mst'],
                      A1_p5_tx_mst=p5['sent']['mst'], A2_p25_rx_mst=p25['recv']['mst'], rx_minus_tx_A1toA2=p25['recv']['mst'] - p5['sent']['mst'],
                      A1_global_tc=a1[n]['global_tc'], A1_last_tc_age_s=a1[n]['last_tc_age_s'], A2_last_tc_age_s=a2[n]['last_tc_age_s'],
                      evidence_type='field_observation'))
wcsv('cross_device_counters.csv', chain)
ivals = []
for (n0, k0), (n1, k1) in [(pairs[0], pairs[1]), (pairs[2], pairs[3]), (pairs[1], pairs[2])]:
    c0, c1 = chain[[p[0] for p in pairs].index(n0)], chain[[p[0] for p in pairs].index(n1)]
    note = 'A2 GE1/0/23 counters restarted (port disabled and re-enabled) between snapshots' if n0 == 'ep1' else ''
    ivals.append(dict(interval=f'{n0}->{n1}', A2_p23_d_rx_tcn=c1['A2_p23_rx_tcn'] - c0['A2_p23_rx_tcn'] if not note else 'n/a',
                      A2_d_global=c1['A2_global_tc'] - c0['A2_global_tc'], A2_p25_d_tx_mst=c1['A2_p25_tx_mst'] - c0['A2_p25_tx_mst'],
                      A1_p5_d_rx_mst=c1['A1_p5_rx_mst'] - c0['A1_p5_rx_mst'], A1_d_global=c1['A1_global_tc'] - c0['A1_global_tc'],
                      A2_p25_d_rx_hello=c1['A2_p25_rx_mst'] - c0['A2_p25_rx_mst'],
                      hello_proxy_s=2 * (c1['A2_p25_rx_mst'] - c0['A2_p25_rx_mst']), note=note, evidence_type='field_observation'))
wcsv('cross_device_chain_intervals.csv', ivals)
SUMMARY['cross_device'] = dict(snapshots=chain, intervals=ivals,
                               timer_window_A2_fx_s=297 - 64)

# A2 per-port increments for the active paired interval (ep0 -> ep1)
a2rows = []
for p, v1 in a2['ep1']['ports'].items():
    v0 = a2['ep0']['ports'][p]
    a2rows.append(dict(interface=p, role=v1['role'], state=v1['state'], d_rx_total=v1['recv']['total'] - v0['recv']['total'],
                       d_rx_tcn=v1['recv']['tcn'] - v0['recv']['tcn'], d_rx_config=v1['recv']['config'] - v0['recv']['config'],
                       d_rx_mst=v1['recv']['mst'] - v0['recv']['mst'], cum_rx_total=v1['recv']['total'], evidence_type='field_observation'))
wcsv('A2_port_increments_ep.csv', a2rows)
A2_dC = a2['ep1']['global_tc'] - a2['ep0']['global_tc']

# ===================================================== B. native counters ===
if NAT.exists():
    nat1 = parse_native(NAT / 'A1_IP-1103_20261102.txt'); nat2 = parse_native(NAT / 'A2_IP-1104_20261102.txt')
else:
    nat1, nat2 = _pc['A1_native'], _pc['A2_native']
json.dump(dict(A1_paired=a1, A2_paired=a2, A1_native=nat1, A2_native=nat2), open(OUT / 'parsed_counters.json', 'w'), indent=1, ensure_ascii=False)
p5 = nat1['bpdu_stats']['GigabitEthernet1/0/5']; p25 = nat2['bpdu_stats']['GigabitEthernet1/0/25']; p23 = nat2['bpdu_stats']['GigabitEthernet1/0/23']
sum_rx_a1 = sum(v['receive'] for v in nat1['stp_tc'].values())
other_rx_a1 = sum_rx_a1 - nat1['stp_tc']['GigabitEthernet1/0/5']['receive']
non_tc_mst = p5['MST received']['count'] - p5['TC received']['count']
recon = OrderedDict(
    A1_uptime=nat1['uptime'], A2_uptime=nat2['uptime'],
    A1_global_tc=nat1['global_tc'], A1_sum_port_tc_receive=sum_rx_a1, A1_global_equals_sum=nat1['global_tc'] == sum_rx_a1,
    A1_p5_tc_receive=nat1['stp_tc']['GigabitEthernet1/0/5']['receive'], A1_p5_tc_send=nat1['stp_tc']['GigabitEthernet1/0/5']['send'],
    A1_other_ports_tc_receive=other_rx_a1,
    A1_other_ports_tc_send={k: v['send'] for k, v in nat1['stp_tc'].items() if k != 'GigabitEthernet1/0/5'},
    A1_p5_share_of_tc_receive=nat1['stp_tc']['GigabitEthernet1/0/5']['receive'] / sum_rx_a1,
    A1_p5_mst_received=p5['MST received']['count'], A1_p5_non_tc_mst=non_tc_mst,
    A1_p5_tc_detected=p5['TC detected']['count'],
    C_minus_B_reconstructed=other_rx_a1 - non_tc_mst,
    C_minus_B_observed_1030=C[K[0]] - int(by[K[0]]['GigabitEthernet1/0/5']['bpdu_received']),
    end_to_end=dict(TC_A2toA1=(p25['TC sent']['count'], p5['TC received']['count']),
                    TC_A1toA2=(p5['TC sent']['count'], p25['TC received']['count']),
                    TCA_A1toA2=(p5['TCA sent']['count'], p25['TCA received']['count']),
                    TCA_A2toA1=(p25['TCA sent']['count'], p5['TCA received']['count']),
                    MST_A2toA1=(p25['MST sent']['count'], p5['MST received']['count']),
                    MST_A1toA2=(p5['MST sent']['count'], p25['MST received']['count'])),
    A2_global_tc=nat2['global_tc'], A2_sum_port_tc_receive=sum(v['receive'] for v in nat2['stp_tc'].values()),
    A2_p23_tcn_received=p23['TCN received']['count'], A2_p23_tc_detected=p23['TC detected']['count'],
    A2_p23_config_sent=p23['Config sent']['count'], A2_p25_tc_detected=p25['TC detected']['count'],
    A2_p25_tc_sent=p25['TC sent']['count'],
    A1_log_notified_tc=nat1['notified_tc_log'], A1_log_notified_ports=nat1['notified_tc_ports'],
    evidence_type='native_counter')
assert recon['C_minus_B_reconstructed'] == recon['C_minus_B_observed_1030'], recon
assert recon['A1_global_equals_sum']
SUMMARY['native'] = recon
json.dump(recon, open(OUT / 'native_reconciliation.json', 'w'), indent=1, ensure_ascii=False)

# ================================================ rules (shared function) ===
def rules(dB, dCk, cum, tol=1, max_subset=3):
    """dB: {port: [increments per interval]}, dCk: [global increments], cum: {port: final cumulative}"""
    act = [i for i, c in enumerate(dCk) if c > 0]
    pos = sorted(p for p, v in dB.items() if sum(v) > 0)
    strict = sorted(p for p, v in dB.items() if act and all(v[i] == dCk[i] for i in act))
    toler = sorted(p for p, v in dB.items() if sum(v) > 0 and act and all(abs(v[i] - dCk[i]) <= tol for i in act))
    largest = [max(cum, key=cum.get)] if cum else []
    ss = []
    for r in range(1, max_subset + 1):
        for S in itertools.combinations(pos, r):
            if any(set(T) <= set(S) for T in ss): continue
            if all(sum(dB[p][i] for p in S) == dCk[i] for i in act):
                ss.append(S)
        if ss: break
    subset = sorted(set(p for S in ss for p in S))
    return OrderedDict(R1_strict=strict, R2_positive=pos, R3_largest_cum=largest, R4_tolerance=toler, R5_subset_sum=subset)

# field rows
a1_dB = {p: [int(by[k][p]['bpdu_received']) - int(by[k - 1][p]['bpdu_received']) for k in K[1:]] for p in P}
a1_cum = {p: int(by[K[-1]][p]['bpdu_received']) for p in P}
field_a1 = rules(a1_dB, [dC[k] for k in K[1:]], a1_cum)
a2_dB = {r['interface']: [r['d_rx_total']] for r in a2rows}
a2_cum = {r['interface']: r['cum_rx_total'] for r in a2rows}
field_a2 = rules(a2_dB, [A2_dC], a2_cum)
nat_a2_cum = {p: v['receive'] for p, v in nat2['stp_tc'].items()}
SUMMARY['field_rules'] = dict(A1=field_a1, A2_ep=field_a2, A2_dC=A2_dC,
                              A2_native_largest_cumulative_tc=max(nat_a2_cum, key=nat_a2_cum.get))

# ============================================== C. constructed scenarios ====
model = [r for r in csv.DictReader(open(PKG / 'reviewer/results/model_counterexample_intervals.csv', encoding='utf-8-sig'))]
tx = [int(r['bpdu_sent']) for r in csv.DictReader(open(PKG / 'reviewer/data/sending_snapshots.csv', encoding='utf-8-sig')) if r['interface'] == 'GigabitEthernet1/0/5']
hello = [b - a for a, b in zip(tx, tx[1:])]   # 13 per-interval Hello-count proxies (field sequence)
names = OrderedDict([
    ('ideal_single_ingress', 'S1 ideal single ingress'),
    ('one_background_bpdu_on_true_ingress', 'S2 +1 ordinary BPDU on true ingress'),
    ('one_interior_snapshot_read_phase_error', 'S3 one interior snapshot misread by 1'),
    ('two_true_ingresses', 'S4 two ingresses (48 + 44)'),
    ('true_ingress_background_and_coincident_distractor', 'S5 coincident background on another port'),
    ('background_only_in_one_inactive_interval', 'S6 +1 ordinary BPDU in a zero interval'),
    ('S7', 'S7 non-coincident periodic background on another port')])
truth = {'two_true_ingresses': ['P1', 'P2']}
base = {'P1': 2139540, 'P2': 13}
crow = []
for key, label in names.items():
    if key == 'S7':
        src = [r for r in model if r['scenario'] == 'ideal_single_ingress']
        g = [int(r['global_tc_delta']) for r in src]
        dB = {'P1': [int(r['observed_bpdu_P1']) for r in src], 'P2': hello[:]}
        b2 = dict(P1=base['P1'], P2=43752)
    else:
        src = [r for r in model if r['scenario'] == key]
        g = [int(r['global_tc_delta']) for r in src]
        dB = {'P1': [int(r['observed_bpdu_P1']) for r in src], 'P2': [int(r['observed_bpdu_P2']) for r in src]}
        b2 = dict(base)
    cum = {p: b2[p] + sum(v) for p, v in dB.items()}
    res = rules(dB, g, cum)
    tr = truth.get(key, ['P1'])
    row = OrderedDict(scenario=label, true_ingress='+'.join(tr))
    for rn, cand in res.items():
        verdict = ('correct' if sorted(cand) == sorted(tr) else 'covers (non-unique)' if set(tr) <= set(cand) else
                   'empty' if not cand else 'wrong unique' if len(cand) == 1 else 'wrong')
        row[rn] = '{' + ','.join(cand) + '}' if cand else 'empty'
        row[rn + '_verdict'] = verdict
    row['evidence_type'] = 'constructed_model'
    crow.append(row)
wcsv('rules_by_scenario.csv', crow)
SUMMARY['rules_by_scenario'] = crow

# ================================================= D. Monte Carlo simulation =
rng = random.Random(A.seed)
HELLO = 2.0

def simulate(cond, origin, seed, n_snap=14, T=3 * 3600):
    """Counter-level discrete-event simulation of TC propagation.
    Root R: ports r_dn (to S, true ingress), r_alt (second downstream Z), r_q1..r_q3 quiet designated.
    Non-root S (MSTP boundary): s_up root port (receives R Hellos), s_dn designated to legacy X, s_q1, s_q2.
    Legacy X relays/originates TCN; Y downstream of X."""
    rr = random.Random(seed)
    events = []                          # (time, ingress at R, ingress at S)
    t = rr.expovariate(1 / 600)
    while t < T:
        size = 1 + int(rr.expovariate(1 / 2.5))
        tt = t
        for _ in range(size):
            if tt >= T: break
            via_alt = cond.get('dual') and rr.random() < 0.45
            events.append((tt, 'r_alt' if via_alt else 'r_dn', None if via_alt else 's_dn'))
            tt += rr.uniform(0.5, 8.0)
        t = tt + rr.expovariate(1 / 700)
    bgR = []
    if cond.get('bg_true'): bgR += [(rr.uniform(0, T), 'r_dn') for _ in range(rr.choice([1, 1, 2, 3]))]
    if cond.get('bg_other'):
        per = rr.uniform(20, 120)       # periodic-like background on another port, not tied to TC activity
        x = rr.uniform(0, per)
        while x < T: bgR.append((x, 'r_q1')); x += per * rr.uniform(0.8, 1.2)
    snaps_t = sorted(rr.uniform(0, T) for _ in range(n_snap))
    skew = cond.get('skew', 0.0)
    R_ports = ['r_dn', 'r_alt', 'r_q1', 'r_q2', 'r_q3']; S_ports = ['s_up', 's_dn', 's_q1', 's_q2']
    baseR = {p: int(rr.lognormvariate(6, 2)) for p in R_ports}; baseS = {p: int(rr.lognormvariate(6, 2)) for p in S_ports}
    evR_tc = sorted((e[0], e[1]) for e in events); evS_tc = sorted((e[0] - 0.01, e[2]) for e in events if e[2])
    def count(evlist, port, t):
        return sum(1 for (x, p) in evlist if p == port and x <= t)
    obs = dict(R=dict(C=[], B={p: [] for p in R_ports}, N={p: [] for p in R_ports}),
               S=dict(C=[], B={p: [] for p in S_ports}, N={p: [] for p in S_ports}))
    for ts in snaps_t:
        obs['R']['C'].append(sum(1 for (x, _) in evR_tc if x <= ts))
        obs['S']['C'].append(sum(1 for (x, _) in evS_tc if x <= ts))
        for i, p in enumerate(R_ports):
            tp = ts + (rr.uniform(0, skew) if skew else 0.0)        # non-atomic readout of port blocks
            tc_here = count(evR_tc, p, tp)
            obs['R']['B'][p].append(baseR[p] + tc_here + count(bgR, p, tp))
            obs['R']['N'][p].append(tc_here)
        for p in S_ports:
            tp = ts + (rr.uniform(0, skew) if skew else 0.0)
            tc_here = count(evS_tc, p, tp)
            hello_rx = int(tp // HELLO) if p == 's_up' else 0      # root port receives a Hello every 2 s
            obs['S']['B'][p].append(baseS[p] + tc_here + hello_rx)
            obs['S']['N'][p].append(tc_here)
    # legacy bridge X record (TC detected locally vs TCN received from Y)
    nS = len(evS_tc)
    xlog = dict(detected=nS, tcn_received=0) if origin == 'H1' else dict(detected=0, tcn_received=nS)
    truthR = sorted(set(e[1] for e in events)) if events else []
    return obs, truthR, ['s_dn'] if evS_tc else [], xlog

def evaluate(obs_dev, truth_set):
    Cs = obs_dev['C']; dCk = [b - a for a, b in zip(Cs, Cs[1:])]
    if not any(dCk): return None
    dB = {p: [b - a for a, b in zip(v, v[1:])] for p, v in obs_dev['B'].items()}
    cum = {p: v[-1] for p, v in obs_dev['B'].items()}
    res = rules(dB, dCk, cum)
    nat = sorted(p for p, v in obs_dev['N'].items() if v[-1] - v[0] > 0)
    res['R0_native_tc'] = nat
    out = {}
    for rn, cand in res.items():
        out[rn] = dict(cover=set(truth_set) <= set(cand), exact=sorted(cand) == sorted(truth_set),
                       wrong_unique=len(cand) == 1 and set(cand) != set(truth_set) and not set(truth_set) <= set(cand),
                       empty=len(cand) == 0, size=len(cand))
    return out

conds = OrderedDict([('C0 baseline', {}), ('C1 background on true ingress', dict(bg_true=1)),
                     ('C2 periodic background on another port', dict(bg_other=1)), ('C3 two ingresses', dict(dual=1)),
                     ('C4 non-atomic readout (skew <= 1 s)', dict(skew=1.0)),
                     ('C5 C1 + C2 + C4 combined', dict(bg_true=1, bg_other=1, skew=1.0))])
REPS = 30
simrows = []; hh = []
for cname, cond in conds.items():
    agg = {dev: defaultdict(lambda: defaultdict(float)) for dev in ['R', 'S']}; n = {'R': 0, 'S': 0}
    for rep in range(REPS):
        seed = rng.randrange(10 ** 9)
        o1, tR, tS, x1 = simulate(cond, 'H1', seed)
        o2, _, _, x2 = simulate(cond, 'H2', seed)                  # same timeline, different origin
        same = o1 == o2
        hh.append(dict(condition=cname, rep=rep, observations_identical_H1_H2=same,
                       X_log_separates=(x1['detected'] > 0) != (x2['detected'] > 0) or (x1 == x2 and not tS),
                       evidence_type='simulation'))
        for dev, truth_set in [('R', tR), ('S', tS)]:
            ev = evaluate(o1[dev], truth_set)
            if ev is None: continue
            n[dev] += 1
            for rn, m in ev.items():
                for k, v in m.items(): agg[dev][rn][k] += float(v)
    for dev in ['R', 'S']:
        for rn in ['R0_native_tc', 'R1_strict', 'R2_positive', 'R3_largest_cum', 'R4_tolerance', 'R5_subset_sum']:
            m = agg[dev][rn]; N = max(n[dev], 1)
            simrows.append(OrderedDict(condition=cname, device='root A1-like' if dev == 'R' else 'non-root A2-like', rule=rn,
                                       n=n[dev], coverage=round(m['cover'] / N, 3), exact=round(m['exact'] / N, 3),
                                       wrong_unique=round(m['wrong_unique'] / N, 3), empty=round(m['empty'] / N, 3),
                                       mean_set_size=round(m['size'] / N, 2), evidence_type='simulation'))
wcsv('simulation_metrics.csv', simrows)
wcsv('simulation_H1_H2.csv', hh)
SUMMARY['simulation'] = dict(reps_per_condition=REPS, conditions=list(conds),
                             H1H2_identical_at_R_S=sum(r['observations_identical_H1_H2'] for r in hh), H1H2_runs=len(hh),
                             X_log_separates=sum(r['X_log_separates'] for r in hh))

# ============================================== E. identifiability (Eq. 1) ==
# Factorised finite hypothesis space.
#  A1 part: ingress port (27) x background u in {0,1}^13 on the ingress x readout deviation
#           (none, or eps in {-1,+1} at one of the 14 snapshots of the ingress port)  -> 27*8192*29
#  A2 part: ingress at A2 (28 ports or 'A2 itself') x origin {A2-local, X-local (H1), Y via X (H2), beyond Y}
dCv = np.array([dC[k] for k in K[1:]]); nI = len(dCv)
obsB = {p: np.array(a1_dB[p]) for p in P}
U = np.array(list(itertools.product([0, 1], repeat=nI)))           # 8192 x 13
eps_opts = [None] + [(m, e) for m in range(len(K)) for e in (-1, 1)]
surv_A1 = []
for ing in P:
    others_ok = all(not obsB[q].any() for q in P if q != ing)       # non-ingress ports predicted zero
    if not others_ok: continue
    for eo in eps_opts:
        eps = np.zeros(len(K))
        if eo: eps[eo[0]] = eo[1]
        pred = dCv[None, :] + U + (eps[1:] - eps[:-1])[None, :]
        ok = np.all(pred == obsB[ing][None, :], axis=1) & np.all(pred >= 0, axis=1)
        for i in np.nonzero(ok)[0]:
            surv_A1.append((ing, int(U[i].sum()), eo))
A2_ports = list(a2['ep1']['ports'])
origins = ['A2-local', 'X-local (H1)', 'Y relayed by X (H2)', 'beyond Y']
surv_A2 = []
for ing in A2_ports + ['A2 itself']:
    for org in origins:
        # predictions for the active paired interval ep0->ep1 and the native counters
        if org == 'A2-local' or ing == 'A2 itself':
            # A2 would detect the change itself: requires TC detected >> 1 and no TC receptions -> contradicts
            ok = False
        else:
            ok = (a2rows[[r['interface'] for r in a2rows].index(ing)]['d_rx_tcn'] + a2rows[[r['interface'] for r in a2rows].index(ing)]['d_rx_mst'] * 0 == A2_dC) and \
                 a2rows[[r['interface'] for r in a2rows].index(ing)]['d_rx_tcn'] > 0
        if ok: surv_A2.append((ing, org))
def attr(vals): return sorted(set(map(str, vals)))
ident = OrderedDict(
    hypothesis_space=dict(A1=len(P) * len(U) * len(eps_opts), A2=(len(A2_ports) + 1) * len(origins),
                          total=len(P) * len(U) * len(eps_opts) * (len(A2_ports) + 1) * len(origins)),
    surviving=dict(A1=len(surv_A1), A2=len(surv_A2), total=len(surv_A1) * len(surv_A2)),
    attributes=OrderedDict(
        A1_ingress=attr(s[0] for s in surv_A1),
        A1_background_on_ingress_in_window=attr(s[1] for s in surv_A1),
        A1_readout_deviation=attr(s[2] for s in surv_A1),
        A2_ingress=attr(s[0] for s in surv_A2),
        origin=attr(s[1] for s in surv_A2)),
    with_X_detection_log=dict(origin_if_X_detected_gt0=['X-local (H1)'], origin_if_X_detected_eq0=['Y relayed by X (H2)', 'beyond Y'],
                              note='adding X\'s TC-detected record splits the surviving origin set; one further hop (Y) is needed to separate H2 from beyond-Y'),
    evidence_type='field_observation + constructed hypothesis space')
SUMMARY['identifiability'] = ident
json.dump(SUMMARY, open(OUT / 'summary_v3.json', 'w'), indent=1, ensure_ascii=False, default=str)
print(json.dumps(dict(type_totals=tot, chain=ivals, field_rules=SUMMARY['field_rules'], recon={k: recon[k] for k in ['A1_global_tc', 'A1_sum_port_tc_receive', 'A1_p5_non_tc_mst', 'C_minus_B_reconstructed', 'end_to_end']},
                      ident=ident['surviving'], ident_attr=ident['attributes'], sim=SUMMARY['simulation']), indent=1, default=str))
