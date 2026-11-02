# TC-ingress localization from sparse CLI snapshots — code and derived data

Companion repository for the manuscript *Localizing Topology-Change Ingress from Sparse CLI Snapshots: Identifiability Analysis and Validation in a Campus Wireless Network* (X. Bao, J. Wang, J. Jiang, J. Ye; prepared for submission to *Electronics*, 2026).

## Contents

| Path | Content |
|---|---|
| `code/analysis_v3.py` | All analyses of the paper: per-type increments, cross-device counter chain, native-counter reconciliation, rules × scenarios (R1–R5), counter-level Monte Carlo simulation (6 conditions × 30 replications), finite-hypothesis identifiability enumeration |
| `code/plot_figures_v3.py` | Figures 1–9 (SVG + 600 dpi PNG) |
| `inputs/data/` | Derived, anonymized counter data: 14 A1 checkpoints × 27 interfaces, intervals, windows, and `parsed_counters.json` (numerical counters parsed from the paired 30-Oct snapshots and from the read-only 2-Nov native statistics) |
| `inputs/reviewer/` | Constructed count-model inputs (two-ingress additive model) and transmit-counter sequences used for checkpoint ordering |
| `results/` | Outputs of `analysis_v3.py` (each row tagged `field_observation`, `native_counter`, `constructed_model` or `simulation`) |
| `figures/` | Figures accompanying the manuscript |

## Reproduce

```bash
pip install numpy matplotlib seaborn SciencePlots   # Python ≥ 3.10
python3 code/analysis_v3.py --root . --out results  # ≈ 1–3 min; fixed seed 20261102
python3 code/plot_figures_v3.py --data inputs --out figures
```

Running from the parsed counters reproduces `results/` byte-for-byte. The parser for the raw H3C CLI text is included in `analysis_v3.py`; the raw device outputs themselves are not published (see below).

## Data provenance and anonymization

The data stem from one production incident (30 October 2026) in a campus wireless network and from a read-only collection three days later (2 November 2026). Written approval from the network centre, as data custodian, for the use and publication of the anonymized derived data is pending. IPv4 addresses, device names and user names were replaced by labels; MAC addresses (bridge identifiers and terminal MACs) were replaced by the first 12 hexadecimal digits of a salted SHA-256 hash; the salt is held by the custodian and is not released. Raw device outputs contain operational details of a production network and are available from the corresponding author (bxz@ky.zstu.edu.cn) on reasonable request, subject to the custodian's permission.

Constructed model values and simulation outputs are not field measurements; they are labelled as such in every file.

## Licence

Code: MIT (see `LICENSE`). Data and figures: CC BY 4.0 (see `DATA_LICENSE`).

## Citation

See `CITATION.cff`. After the Zenodo release, cite the archived version via its DOI.
