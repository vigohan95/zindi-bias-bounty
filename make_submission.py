"""Build the Zindi submission CSV from a prediction parquet, with sanity checks.

Usage:
    PYTHONUTF8=1 python modules/competitions/zindi-bias-bounty/make_submission.py [pred_name] [--out NAME] [--components]

Reads  <work>/pred/<pred_name>.parquet   (default baseline_v1)
Aligns to the official Zindi SampleSubmission.csv (<work>/official/SampleSubmission.csv, 9,794 rows, 5 regions)
in that file's row order.
Writes <work>/submissions/<NAME>.csv with columns GEOID,coverage_gap_score
       (add --components to also include transport_gap,building_gap,poi_gap; every cell filled)
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

import pandas as pd

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
OFFICIAL = WORK / "official" / "SampleSubmission.csv"
EXPECTED = {"maricopa-az": 1593, "northern-ca": 591, "eastern-ok": 1192, "south-central-tx": 6003, "eastern-wa": 415}


def main() -> None:
    argv = sys.argv[1:]
    with_components = "--components" in argv
    out_name = None
    if "--out" in argv:
        out_name = argv[argv.index("--out") + 1]
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--out")]
    name = args[0] if args else "baseline_v1"
    build(name, out_name or name, with_components)


def build(name: str, out_name: str, with_components: bool = False) -> Path:
    pred = pd.read_parquet(WORK / "pred" / f"{name}.parquet")
    pred["GEOID"] = pred.GEOID.astype(str).str.zfill(11)
    assert pred.GEOID.is_unique

    official = pd.read_csv(OFFICIAL, dtype={"GEOID": str})
    official["GEOID"] = official.GEOID.str.zfill(11)
    assert official.GEOID.is_unique, "duplicate GEOID in official sample"
    official["_order"] = range(len(official))

    sub = official[["GEOID", "region", "_order"]].merge(pred, on="GEOID", how="left", suffixes=("", "_pred"))
    missing = sub[sub.coverage_gap_score.isna()].GEOID.tolist()
    assert not missing, f"{len(missing)} official tracts without prediction, e.g. {missing[:5]}"
    assert (sub.region == sub.region_pred).all(), "region mismatch between official file and features"
    sub = sub.sort_values("_order")

    cols = ["GEOID", "coverage_gap_score"]
    if with_components:
        sub["transport_gap"] = sub.gap_t
        sub["building_gap"] = sub.gap_b
        sub["poi_gap"] = sub.gap_p
        cols = ["GEOID", "transport_gap", "building_gap", "poi_gap", "coverage_gap_score"]
    out = sub[cols].copy()
    for c in cols[1:]:
        out[c] = out[c].astype(float).clip(0, 1).round(6)

    # ---- sanity checks ----
    assert out.GEOID.str.len().eq(11).all() and out.GEOID.str.isdigit().all(), "GEOID must be 11 digits"
    assert not out.isna().any().any(), "NaN in submission"
    assert ((out[cols[1:]] >= 0) & (out[cols[1:]] <= 1)).all().all(), "scores outside [0,1]"
    assert len(out) == len(official) == sum(EXPECTED.values()), f"row count {len(out)} != {len(official)}"
    assert set(out.GEOID) == set(official.GEOID), "GEOID set differs from official"
    assert (out.GEOID.values == official.GEOID.values).all(), "row order differs from official"
    counts = sub.groupby("region").size()
    for r, n in EXPECTED.items():
        assert counts[r] == n, f"{r}: {counts[r]} rows, expected {n}"

    (WORK / "submissions").mkdir(exist_ok=True)
    path = WORK / "submissions" / f"{out_name}{'_components' if with_components else ''}.csv"
    out.to_csv(path, index=False, lineterminator="\n")
    print(f"wrote {path}  rows={len(out)}  cols={cols}")
    pd.set_option("display.width", 220)
    print(sub.groupby("region")["coverage_gap_score"].describe(percentiles=[.05, .25, .5, .75, .95]).round(3).to_string())
    print("overall mean", round(out.coverage_gap_score.mean(), 4), "sd", round(out.coverage_gap_score.std(), 4))
    print(out.head(3).to_string(index=False))
    return path


if __name__ == "__main__":
    main()
