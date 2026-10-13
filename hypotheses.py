"""Structurally different hypotheses about where the true coverage gap concentrates.

Each hypothesis produces a raw per-tract score from the features / baseline diagnostics, which is
then affinely re-centred to mean 0.060 and sd 0.045 (public-LB-implied truth mean 0.060, sd 0.089;
sd 0.045 = optimal scale if the hypothesis correlates ~0.5 with truth), clipped to [0, 1], and
written as a submission aligned to the official SampleSubmission.csv. Deterministic (no RNG).

Usage: PYTHONUTF8=1 python modules/competitions/zindi-bias-bounty/hypotheses.py [--only NAME]
Writes <work>/pred/hyp_<name>.parquet and <work>/submissions/hyp_<name>.csv
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from make_submission import build  # noqa: E402

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
REGIONS = ["maricopa-az", "northern-ca", "eastern-ok", "south-central-tx", "eastern-wa"]
TARGET_MEAN, TARGET_SD = 0.060, 0.045


def recentre(raw: pd.Series, mean: float = TARGET_MEAN, sd: float = TARGET_SD) -> np.ndarray:
    z = (raw - raw.mean()) / (raw.std() + 1e-12)
    a = mean
    for _ in range(50):  # fix the post-clipping mean
        x = np.clip(a + sd * z, 0, 1)
        a += mean - x.mean()
    return np.clip(a + sd * z, 0, 1)


def raw_signals() -> tuple[pd.DataFrame, dict[str, pd.Series], pd.DataFrame]:
    """Return (joined features, {name: raw signal}, baseline predictions) — shared with blend.py."""
    f = pd.concat([pd.read_parquet(WORK / "features" / f"{r}.parquet") for r in REGIONS], ignore_index=True)
    p = pd.read_parquet(WORK / "pred" / "baseline_v1.parquet")
    df = f.merge(p[["GEOID", "p_def_t", "gap_t", "gap_b", "gap_p", "gap_hifld", "p_def_hifld", "gap_cbp"]], on="GEOID")
    # bias_discovery output: per tract, km of drivable Overture roads with names.primary null / all drivable km.
    # Two Gulf water tracts (48039990000, 48057990000) have no roads -> region median share.
    ra = pd.read_parquet(WORK / "features" / "road_attrs_joined.parquet")[["GEOID", "unnamed_share"]]
    df = df.merge(ra, on="GEOID", how="left")
    df["unnamed_share"] = df.unnamed_share.fillna(df.groupby("region").unnamed_share.transform("median"))
    routed = df.named_routed_km + df.minor_routed_km + df.named_county_km + df.minor_county_km

    hyps = {
        # 1. Gap concentrates where components are likely UNDEFINED: a tract with no TIGER highway and no
        #    reference facility averages over fewer, noisier components (POI half dominated), and those
        #    tracts are rural / low-density where Overture places are sparsest.
        "undefined": (1 - df.p_def_t) + (1 - df.p_def_hifld),
        # 2. Only the POI component carries real gap (Overture >= reference for roads and buildings almost
        #    everywhere); transport and building contribute ~0.
        "poi_only": df.gap_p,
        # 3. Building reference mismatch where Overture footprints come from OSM rather than Microsoft:
        #    OSM-drawn footprints merge/split differently from the MS footprints the reference counts.
        "osm_buildings": df.bld_osm_primary / df.bld_n.clip(lower=1),
        # 4. Pure rurality/tribal prior: gap grows with land area, falls with urban share, higher on tribal land.
        "rural_tribal": (np.log1p(df.land_km2) - np.log1p(df.land_km2).mean()) / np.log1p(df.land_km2).std()
                        + (1 - df.pct_urban.fillna(0)) + df.tribal_any.fillna(0).astype(float),
        # 5. Sparse-places prior: Overture places per capita (log), inverted. Tracts with few mapped places per
        #    resident are where both the CBP and facility halves bind.
        "sparse_places": -np.log((df.poi_n + 1) / (df.pop_total + 100)),
        # 6. (2026-10-10) Unnamed-road share: length-weighted share of a tract's drivable Overture road km whose
        #    names.primary is null. Unnamed km are mostly unreviewed TIGER-era imports (WRITEUP §7), i.e. a proxy
        #    for absent mapping-community attention -> places/facilities also thin -> larger gap. Raw share
        #    (skew 2.4), not logit, so the right tail is emphasised like the truth's.
        "unnamed_roads": df.unnamed_share,
    }
    hyps = {k: pd.Series(np.asarray(v, dtype=float)).replace([np.inf, -np.inf], np.nan).fillna(0) for k, v in hyps.items()}
    return df, hyps, p


def main() -> None:
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    df, hyps, p = raw_signals()
    for name, raw in hyps.items():
        if only and name != only:
            continue
        score = recentre(raw)
        out = pd.DataFrame({"GEOID": df.GEOID, "region": df.region, "coverage_gap_score": score,
                            "gap_t": 0.0, "gap_b": 0.0, "gap_p": 0.0})
        out.to_parquet(WORK / "pred" / f"hyp_{name}.parquet", index=False)
        print(f"\n### hyp_{name}: raw corr with baseline_v2 = {np.corrcoef(raw, p.set_index('GEOID').loc[df.GEOID, 'coverage_gap_score'])[0,1]:.3f}")
        build(f"hyp_{name}", f"hyp_{name}", False)


if __name__ == "__main__":
    main()
