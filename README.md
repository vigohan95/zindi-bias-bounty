# Bias Bounty Mapping Equity Challenge — label-free coverage-gap model and the unnamed-roads bias discovery

Entry for the Zindi [Bias Bounty Mapping Equity Challenge](https://zindi.world/competitions/bias-bounty-mapping-equity-challenge).
Everything here uses only the challenge data (Overture 2026-08-19.0 extracts, ACS, strata) and open-source Python packages; nothing is random, so every output reproduces bit-for-bit.

- **`WRITEUP.md`** — the full methodology: method card (§0), data (§2), features (§3), the expected-gap model (§4), what the public leaderboard taught us and the blends (§5), scorecard reflection (§6), **Best Bias Discovery: unnamed roads (§7)**, reproduction and file integrity (§8).
- **`writeup.ipynb`** — executed notebook: reruns the pipeline end to end on the Eastern WA slice in about a minute and reproduces every §7 table.
- **`figures/fig_unnamed_roads.png`** — Figure 1: Maverick County TX and Washita County OK choropleths of the unnamed-road share, and the share by scorecard stratum.

![Figure 1](figures/fig_unnamed_roads.png)

## Run it

```bash
pip install -r requirements.txt          # Python 3.11

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

# 3. full five-region pipeline (~20 min, Texas dominates). Data folder: ./data, or set ZINDI_WORK.
PYTHONUTF8=1 python features.py
PYTHONUTF8=1 python baseline_v1.py
PYTHONUTF8=1 python make_submission.py baseline_v1 --out baseline_v2
PYTHONUTF8=1 python hypotheses.py            # six single-signal priors
PYTHONUTF8=1 python blend.py                 # blend_all5.csv / blend_top3.csv (the submitted files)
PYTHONUTF8=1 python bias_discovery.py        # Section 7 tables (~4 min)
PYTHONUTF8=1 python figure_unnamed_roads.py  # Figure 1
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
| `bias_discovery.py` | unnamed / unsurfaced / unposted road km by tract and stratum, WLS, most-affected tracts |
| `figure_unnamed_roads.py` | Figure 1 |
| `spotcheck_txdot.py`, `spotcheck_txdot_maverick.csv` | §7 spot-check of 30 unnamed + 30 named Maverick County segments against TxDOT's public Roadway Inventory (external public data; not used by the submission) |

## Licence

Code and text: MIT (see `LICENSE`). Data: Overture Maps (ODbL / CDLA-Permissive 2.0, © Overture Maps Foundation and contributors including OpenStreetMap), US Census (public domain), and the strata sources listed in the challenge bucket README.
