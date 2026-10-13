"""Spot-check (WRITEUP §7.4 follow-up): do Overture's unnamed road segments in Maverick County TX carry a name in
TxDOT's public Roadway Inventory (all public roads, on- and off-system; ArcGIS feature service, no sign-up)?

Deterministic sample: unnamed drivable segments inside the county's scored tracts, ordered by md5(id), first N;
a named control sample is drawn the same way. For each segment the TxDOT service is queried for roadway features
within RADIUS_M of the segment midpoint; a match "has a name" when STE_NAM or HWY is non-empty.
Not used by the scored submission. Allowed for the Bias Discovery prize (external public data).

Usage: PYTHONUTF8=1 python modules/competitions/zindi-bias-bounty/spotcheck_txdot.py [--n 30]
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb
import pandas as pd

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
REGION, STATE, COUNTY = "south-central-tx", "48", "323"
SERVICE = "https://services.arcgis.com/KTcxiTD9dsQw4r7Z/arcgis/rest/services/TxDOT_Roadway_Inventory/FeatureServer/0/query"
RADIUS_M = 30


def sample(con, named: bool, n: int) -> pd.DataFrame:
    ref, strata = WORK / "reference" / REGION / f"{REGION}-", WORK / "strata" / REGION / f"{REGION}-"
    return con.sql(f"""
        WITH cty AS (SELECT ST_Union_Agg(geometry) AS g FROM '{strata}census-tracts.parquet' WHERE STATEFP='{STATE}' AND COUNTYFP='{COUNTY}')
        SELECT r.id, r.class, r.names.primary AS name,
               ST_X(ST_PointN(r.geometry, ((ST_NPoints(r.geometry) + 1) // 2)::INTEGER)) AS lon,
               ST_Y(ST_PointN(r.geometry, ((ST_NPoints(r.geometry) + 1) // 2)::INTEGER)) AS lat,
               ST_Length_Spheroid(ST_FlipCoordinates(r.geometry)) AS len_m
        FROM '{ref}overture-roads.parquet' r, cty
        WHERE ST_Within(r.geometry, cty.g) AND ST_GeometryType(r.geometry) = 'LINESTRING'
          AND (r.names.primary IS {'NOT ' if named else ''}NULL)
        ORDER BY md5(r.id) LIMIT {n}
    """).df()


def query_txdot(lon: float, lat: float) -> list[dict]:
    params = {
        "f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "distance": RADIUS_M, "units": "esriSRUnit_Meter",
        "outFields": "STE_NAM,HWY,HSYS,RDWAY_MAINT_AGCY,F_SYSTEM,RU,ADT_CUR,SRF_TYPE", "returnGeometry": "false",
    }
    url = SERVICE + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8"}), timeout=60) as r:
                return [f["attributes"] for f in json.loads(r.read()).get("features", [])]
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    return []


def check(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, s in df.iterrows():
        feats = query_txdot(s.lon, s.lat)
        names = sorted({(f.get("STE_NAM") or "").strip() for f in feats} - {""})
        hwys = sorted({(f.get("HWY") or "").strip() for f in feats} - {""})
        rows.append({"id": s.id, "class": s["class"], "overture_name": s["name"], "len_m": round(s.len_m), "lon": round(s.lon, 5), "lat": round(s.lat, 5),
                     "txdot_features": len(feats), "txdot_names": "; ".join(names), "txdot_hwy": "; ".join(hwys),
                     "txdot_has_name": bool(names or hwys),
                     "maint_agency": ";".join(sorted({str(f.get("RDWAY_MAINT_AGCY")) for f in feats})),
                     "rural_urban": ";".join(sorted({str(f.get("RU")) for f in feats}))})
        time.sleep(0.3)
    return pd.DataFrame(rows)


def main() -> None:
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 30
    con = duckdb.connect(); con.sql("INSTALL spatial; LOAD spatial;")
    out = WORK / "spotcheck_txdot_maverick.csv"
    results = {}
    for label, named in [("unnamed", False), ("named (control)", True)]:
        df = check(sample(con, named, n))
        df["sample"] = label
        results[label] = df
        print(f"\n### {label}: {n} Overture segments in Maverick County, TxDOT Roadway Inventory within {RADIUS_M} m of the midpoint")
        print(f"in TxDOT inventory at all: {int((df.txdot_features > 0).sum())}/{n};  with a TxDOT street name or highway id: {int(df.txdot_has_name.sum())}/{n}")
        print(df[["id", "class", "overture_name", "len_m", "txdot_features", "txdot_names", "txdot_hwy", "maint_agency"]].to_string(index=False))
    pd.concat(results.values(), ignore_index=True).to_csv(out, index=False)
    print("\nwrote", out)


if __name__ == "__main__":
    main()
