# Bias Bounty Mapping Equity Challenge — label-free coverage-gap model and the phantom-roads bias discovery

Entry for the Zindi [Bias Bounty Mapping Equity Challenge](https://zindi.world/competitions/bias-bounty-mapping-equity-challenge) by Zindi user **vigohan** — leaderboard submissions **THErq5e9** (`blend_all5.csv`) and **fhLZv9UF** (`blend_top3.csv`); entered for **Best Bias Discovery** (WRITEUP §7) and **Best Documentation** (WRITEUP §§0–5, 8).

The scored submission uses only the challenge data (Overture 2026-08-19.0 extracts, ACS, strata) and open-source Python packages; nothing is random, so every output reproduces bit-for-bit. The discovery section additionally uses two documented external public sources (TxDOT's public-road inventory as ground truth, a Census county-name list for labels). The inventory is publicly accessible without sign-up, but its ArcGIS item licence restricts redistribution, so the raw responses are not in this repository — only our derived per-segment observations and the SHA-256 of each response; the check reproduces online with one command.

- **`WRITEUP.md`** — the full methodology: method card (§0), data (§2), features (§3), the expected-gap model (§4, edge cases in §4.4), what the public leaderboard taught us and the blends (§5), scorecard reflection (§6), **Best Bias Discovery — phantom roads: the unreviewed 2007–08 TIGER import that pads Overture's road layer around the Texas border colonias (§7)**, reproduction and file integrity (§8).
- **`bias_discovery_out.md`** — every table behind §7 (edit age by region and stratum, scored-class check, within-region Mann-Whitney tests, WLS, the import-era stratum, named tracts, per-cluster hazard columns), as printed by `bias_discovery.py`.
- **`spotcheck/`** — the TxDOT ground-truth check: `spotcheck_txdot_summary.md`, our per-segment observation table `spotcheck_txdot_results.csv` (segment id, county, sample, import-era flag, length, in_inventory, has_txdot_name, retrieval time, SHA-256 of the response), `SHA256SUMS` of the raw responses (tamper-evidence record), and `TXDOT_SOURCE.md` (service URL, query parameters, retrieval date, licence).
- **`writeup.ipynb`** — executed notebook: reruns the pipeline end to end on the Eastern WA slice in about a minute, reproduces the §7 tables from the cached five-region extraction, and rebuilds the spot-check table offline from the results CSV.
- **`figures/fig_unnamed_roads.png`** — Figure 1.

![Figure 1](figures/fig_unnamed_roads.png)

## Reproduce Section 7 (Best Bias Discovery) with one command

```bash
pip install -r requirements.txt            # Python 3.11
PYTHONUTF8=1 python reproduce_section7.py  # after the data download below (~5 min); runs:
#   bias_discovery.py              -> bias_discovery_out.md (every number in §7, incl. edit age)
#   spotcheck_txdot.py --offline   -> rebuilds the TxDOT table from spotcheck/spotcheck_txdot_results.csv (no network)
#   figure_unnamed_roads.py        -> figures/fig_unnamed_roads.png
PYTHONUTF8=1 python reproduce_section7.py --offline   # only the spot-check table: needs neither the data nor the network
PYTHONUTF8=1 python spotcheck_txdot.py                 # online reproduction: same deterministic 360 segments, re-queried at <= 2 req/s
```

## Full run

```bash
# 1. data (public bucket, no credentials). Eastern WA alone is 175 MB; all five regions about 3.1 GB.
#    The notebook downloads the Eastern WA files itself. For the full run:
B=https://data.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge
mkdir -p data && cd data
for r in maricopa-az northern-ca eastern-ok south-central-tx eastern-wa; do
  for l in overture-roads overture-buildings overture-pois overture-infrastructure overture-rail census-acs-housing; do
    curl -sSL --retry 5 -C - --create-dirs -o reference/$r/$r-$l.parquet $B/reference/$r/$r-$l.parquet; done
  curl -sSL --retry 5 --create-dirs -o reference/$r/$r-sample-submission.csv $B/reference/$r/$r-sample-submission.csv
  for t in strata-tract-table census-tracts; do
    curl -sSL --retry 5 --create-dirs -o strata/$r/$r-$t.parquet $B/strata/$r/$r-$t.parquet; done
done
# put Zindi's SampleSubmission.csv (login required) at data/official/SampleSubmission.csv
cd ..

# 2. notebook (Eastern WA, ~1 min)
jupyter nbconvert --execute --to notebook --inplace writeup.ipynb

# 3. five-region pipeline (~20 min, Texas dominates). Data folder: ./data, or set ZINDI_WORK.
PYTHONUTF8=1 python features.py
PYTHONUTF8=1 python baseline_v1.py
PYTHONUTF8=1 python make_submission.py baseline_v1 --out baseline_v2
PYTHONUTF8=1 python hypotheses.py            # six single-signal priors
PYTHONUTF8=1 python blend.py                 # blend_all5.csv / blend_top3.csv (the submitted files)
PYTHONUTF8=1 python reproduce_section7.py    # Section 7
```

Outputs land in `data/features/`, `data/pred/`, `data/submissions/`. The SHA-256 digests of the two submitted files are in WRITEUP §8.2 and are recomputed by the notebook.

## Files

| file | role |
|---|---|
| `features.py` | per-tract features from the Overture layers, ACS and strata (DuckDB spatial) |
| `baseline_v1.py` | expected coverage gap under log-normal uncertainty about the reference quantities |
| `make_submission.py` | alignment to the official sample submission with format checks |
| `hypotheses.py` | six structurally different single-signal priors, each re-centred to the leaderboard-implied truth moments |
| `blend.py`, `blend_v2.py` | linear blends weighted by the leaderboard-implied correlations |
| `bias_discovery.py` | §7: unnamed / import-era road km by tract and stratum, scored-class check, Mann-Whitney, WLS, import-era stratum, named tracts, hazard columns |
| `spotcheck_txdot.py` | §7: six-county ground truth against TxDOT's Roadway Inventory (online); `--offline` rebuilds the table from our results CSV |
| `figure_unnamed_roads.py` | Figure 1 |
| `reproduce_section7.py` | runs the three §7 scripts in order |
| `external/` | Census Gazetteer county-name extract and `SOURCES.md` (URLs, retrieval dates, hashes) |
| `spotcheck/` | per-segment results CSV, `SHA256SUMS` of the (unpublished) raw responses, summary table, `TXDOT_SOURCE.md` |

## Licence

Code and text: MIT (see `LICENSE`). Data: Overture Maps (ODbL / CDLA-Permissive 2.0, © Overture Maps Foundation and contributors including OpenStreetMap), US Census (public domain), the strata sources listed in the challenge bucket README; TxDOT Roadway Inventory © Texas Department of Transportation — publicly accessible without sign-up, item licence restricts redistribution, so no raw responses are included (statement in `spotcheck/TXDOT_SOURCE.md`).
