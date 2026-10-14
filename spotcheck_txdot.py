"""Ground-truth spot-check for WRITEUP §7 (Best Bias Discovery): are Overture's unnamed drivable road segments in the
Texas border colonia belt public roads at all? Each sampled segment's midpoint is queried against TxDOT's Roadway
Inventory (every public road in Texas — state-, county- and city-maintained, on- and off-system; public ArcGIS
feature service, no sign-up), within RADIUS_M. A hit "has a name" when STE_NAM (street name) or HWY (highway id)
is non-empty.

External public data, used ONLY in this §7 check; never touched by the scored submission. Not a TIGER/Line
derivative. Source, query parameters, retrieval date and licence are recorded in spotcheck/TXDOT_SOURCE.md and in
every frozen response file.

Sampling (deterministic, no RNG): drivable segments of the scored `overture-roads` layer lying within the county's
scored tracts, LINESTRING geometry, ordered by md5(id); the first N unnamed (`names.primary` null) and the first N
named segments. Lengths (spheroid metres) are kept so the summary can be km-weighted as well as segment-counted.

Online run:  PYTHONUTF8=1 python spotcheck_txdot.py [--counties maverick,zapata,...] [--n 30]
             -> freezes every raw response under spotcheck/txdot_responses/<county>/<segment id>.json,
                writes spotcheck/txdot_responses/SHA256SUMS, spotcheck/spotcheck_txdot_results.csv and
                spotcheck/spotcheck_txdot_summary.md. Polite to the service: >= 0.5 s between requests.
Offline run: PYTHONUTF8=1 python spotcheck_txdot.py --offline
             -> verifies SHA256SUMS and rebuilds the results CSV and the summary table from the frozen responses
                only (no network, no challenge data needed).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "spotcheck"
RESP_DIR = OUT_DIR / "txdot_responses"
REGION, STATE = "south-central-tx", "48"
COUNTIES = {  # county FIPS within Texas; all six are in the named-tract tables of WRITEUP §7
    "maverick": "323", "zapata": "505", "brooks": "047", "kinney": "271", "zavala": "507", "edwards": "137",
}
SERVICE_LAYER = "https://services.arcgis.com/KTcxiTD9dsQw4r7Z/arcgis/rest/services/TxDOT_Roadway_Inventory/FeatureServer/0"
SERVICE = SERVICE_LAYER + "/query"
ITEM_URL = "https://www.arcgis.com/sharing/rest/content/items/843ebe994c114961a855ec76ddcde086?f=pjson"  # licence / metadata
RADIUS_M = 30
OUT_FIELDS = "STE_NAM,HWY,HSYS,RDWAY_MAINT_AGCY,F_SYSTEM,RU,ADT_CUR,SRF_TYPE"
MIN_INTERVAL_S = 0.5  # <= 2 requests per second
UA = "zindi-bias-bounty-spotcheck/1.0 (+https://github.com/vigohan95/zindi-bias-bounty)"
_last_request = [0.0]


def _get(url: str, timeout: int = 60) -> bytes:
    wait = MIN_INTERVAL_S - (time.monotonic() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
                raw = r.read()
            _last_request[0] = time.monotonic()
            j = json.loads(raw)
            if isinstance(j, dict) and "error" in j:
                raise RuntimeError(f"ArcGIS error: {j['error']}")
            return raw
        except Exception:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    return b""


def query_params(lon: float, lat: float) -> dict:
    return {
        "f": "json", "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "distance": RADIUS_M, "units": "esriSRUnit_Meter",
        "outFields": OUT_FIELDS, "returnGeometry": "false",
    }


def sample(con, county_fips: str, named: bool, n: int) -> pd.DataFrame:
    ref, strata = WORK / "reference" / REGION / f"{REGION}-", WORK / "strata" / REGION / f"{REGION}-"
    return con.sql(f"""
        WITH cty AS (SELECT ST_Union_Agg(t.geometry) AS g FROM '{strata}census-tracts.parquet' t
                     JOIN read_csv('{ref}sample-submission.csv', types={{'GEOID':'VARCHAR'}}) s USING (GEOID)
                     WHERE t.STATEFP='{STATE}' AND t.COUNTYFP='{county_fips}')
        SELECT r.id, r.class, r.names.primary AS name,
               ST_X(ST_PointN(r.geometry, ((ST_NPoints(r.geometry) + 1) // 2)::INTEGER)) AS lon,
               ST_Y(ST_PointN(r.geometry, ((ST_NPoints(r.geometry) + 1) // 2)::INTEGER)) AS lat,
               ST_Length_Spheroid(ST_FlipCoordinates(r.geometry)) AS len_m,
               list_max(list_transform(r.sources, s -> s.update_time)) AS last_update
        FROM '{ref}overture-roads.parquet' r, cty
        WHERE ST_Within(r.geometry, cty.g) AND ST_GeometryType(r.geometry) = 'LINESTRING'
          AND (r.names.primary IS {'NOT ' if named else ''}NULL)
        ORDER BY md5(r.id) LIMIT {n}
    """).df()


def fetch_and_freeze(county: str, seg: pd.Series, sample_label: str) -> dict:
    params = query_params(round(float(seg.lon), 6), round(float(seg.lat), 6))
    url = SERVICE + "?" + urllib.parse.urlencode(params)
    raw = _get(url)
    rec = {
        "segment": {"id": seg.id, "county": county, "sample": sample_label, "class": seg["class"], "overture_name": seg["name"],
                    "len_m": round(float(seg.len_m), 1), "lon": round(float(seg.lon), 6), "lat": round(float(seg.lat), 6),
                    "overture_last_update": seg.last_update},
        "query": {"service_layer": SERVICE_LAYER, "url": url, "params": params},
        "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response_raw": raw.decode("utf-8"),
    }
    d = RESP_DIR / county
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{seg.id}.json", "w", encoding="utf-8", newline="\n") as fh:  # LF on every platform so SHA256SUMS is portable
        fh.write(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    return rec


def evaluate(rec: dict) -> dict:
    feats = [f["attributes"] for f in json.loads(rec["response_raw"]).get("features", [])]
    names = sorted({(f.get("STE_NAM") or "").strip() for f in feats} - {""})
    hwys = sorted({(f.get("HWY") or "").strip() for f in feats} - {""})
    s = rec["segment"]
    return {"county": s["county"], "sample": s["sample"], "id": s["id"], "class": s["class"], "overture_name": s["overture_name"],
            "overture_last_update": s.get("overture_last_update"), "len_m": s["len_m"], "lon": s["lon"], "lat": s["lat"],
            "txdot_features": len(feats), "txdot_names": "; ".join(names), "txdot_hwy": "; ".join(hwys),
            "txdot_in_inventory": len(feats) > 0, "txdot_has_name": bool(names or hwys),
            "maint_agency": ";".join(sorted({str(f.get("RDWAY_MAINT_AGCY")) for f in feats})),
            "f_system": ";".join(sorted({str(f.get("F_SYSTEM")) for f in feats})),
            "rural_urban": ";".join(sorted({str(f.get("RU")) for f in feats})), "retrieved_utc": rec["retrieved_utc"]}


def write_manifest() -> Path:
    lines = []
    for p in sorted(RESP_DIR.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(RESP_DIR).as_posix()}")
    m = RESP_DIR / "SHA256SUMS"
    with open(m, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return m


def verify_manifest() -> int:
    m = RESP_DIR / "SHA256SUMS"
    bad, n = [], 0
    for line in m.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        n += 1
        p = RESP_DIR / rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(rel)
    if bad:
        raise SystemExit(f"SHA256SUMS verification FAILED for {len(bad)} file(s): {bad[:5]} ...")
    print(f"SHA256SUMS verified: {n} files match")
    return n


def summarise(res: pd.DataFrame) -> str:
    rows = []
    for (county, smp), g in res.groupby(["county", "sample"], sort=True):
        km = g.len_m.sum() / 1000
        rows.append({"county": county, "sample": smp, "n": len(g), "in_inventory": int(g.txdot_in_inventory.sum()),
                     "with_txdot_name": int(g.txdot_has_name.sum()), "absent": int((~g.txdot_in_inventory).sum()),
                     "sampled_km": round(km, 1), "absent_km_share": round(g[~g.txdot_in_inventory].len_m.sum() / g.len_m.sum(), 3),
                     "median_len_m": int(g.len_m.median()), "classes": ", ".join(f"{k} {v}" for k, v in g["class"].value_counts().items())})
    for smp, g in res.groupby("sample", sort=True):
        rows.append({"county": "POOLED", "sample": smp, "n": len(g), "in_inventory": int(g.txdot_in_inventory.sum()),
                     "with_txdot_name": int(g.txdot_has_name.sum()), "absent": int((~g.txdot_in_inventory).sum()),
                     "sampled_km": round(g.len_m.sum() / 1000, 1), "absent_km_share": round(g[~g.txdot_in_inventory].len_m.sum() / g.len_m.sum(), 3),
                     "median_len_m": int(g.len_m.median()), "classes": ", ".join(f"{k} {v}" for k, v in g["class"].value_counts().items())})
    tab = pd.DataFrame(rows)
    stale = res[res["sample"] == "unnamed"].copy()
    stale["import_era"] = stale.overture_last_update.fillna("9999") < "2012-01-01"
    extra = ""
    if len(stale):
        a = stale.groupby("import_era").agg(n=("id", "size"), absent=("txdot_in_inventory", lambda x: int((~x).sum())), km=("len_m", lambda x: round(x.sum() / 1000, 1)))
        extra = "\n\nUnnamed sample split by Overture edit age (import_era = latest `sources[].update_time` before 2012-01-01):\n\n" + a.to_markdown()
    pooled_un = res[res["sample"] == "unnamed"]
    pooled_nm = res[res["sample"] == "named (control)"]
    head = (f"TxDOT Roadway Inventory within {RADIUS_M} m of the segment midpoint; {len(res.county.unique())} counties "
            f"({', '.join(sorted(res.county.unique()))}); retrieved {res.retrieved_utc.min()[:10]} to {res.retrieved_utc.max()[:10]} UTC.\n\n"
            f"Pooled: unnamed {int((~pooled_un.txdot_in_inventory).sum())}/{len(pooled_un)} absent from the inventory "
            f"({pooled_un[~pooled_un.txdot_in_inventory].len_m.sum() / max(pooled_un.len_m.sum(), 1):.1%} of sampled unnamed km), "
            f"{int(pooled_un.txdot_has_name.sum())}/{len(pooled_un)} carry a TxDOT name or highway id; "
            f"named controls {int(pooled_nm.txdot_in_inventory.sum())}/{len(pooled_nm)} in the inventory, "
            f"{int(pooled_nm.txdot_has_name.sum())}/{len(pooled_nm)} with a TxDOT name or highway id.\n\n")
    return head + tab.to_markdown(index=False) + extra + "\n"


def main() -> None:
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 30
    counties = sys.argv[sys.argv.index("--counties") + 1].split(",") if "--counties" in sys.argv else list(COUNTIES)
    OUT_DIR.mkdir(exist_ok=True)
    if "--offline" in sys.argv:
        verify_manifest()
        recs = [json.loads(p.read_text(encoding="utf-8")) for c in sorted(RESP_DIR.iterdir()) if c.is_dir() and not c.name.startswith("_")
                for p in sorted(c.glob("*.json"))]
        res = pd.DataFrame([evaluate(r) for r in recs])
    else:
        import duckdb
        con = duckdb.connect()
        con.sql("INSTALL spatial; LOAD spatial;")
        meta = RESP_DIR / "_service"
        meta.mkdir(parents=True, exist_ok=True)
        (meta / "layer.json").write_bytes(_get(SERVICE_LAYER + "?f=pjson"))
        (meta / "item.json").write_bytes(_get(ITEM_URL))
        with open(meta / "retrieved.txt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + "\n")
        rows = []
        for county in counties:
            fips = COUNTIES[county]
            for label, named in [("unnamed", False), ("named (control)", True)]:
                df = sample(con, fips, named, n)
                print(f"{county}: {len(df)} {label} segments sampled; querying TxDOT ...", flush=True)
                for _, seg in df.iterrows():
                    rows.append(evaluate(fetch_and_freeze(county, seg, label)))
        res = pd.DataFrame(rows)
        m = write_manifest()
        print("manifest:", m)
    res = res.sort_values(["county", "sample", "id"]).reset_index(drop=True)
    res.to_csv(OUT_DIR / "spotcheck_txdot_results.csv", index=False, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    summary = summarise(res)
    with open(OUT_DIR / "spotcheck_txdot_summary.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(summary)
    print(summary)
    print("\nwrote", OUT_DIR / "spotcheck_txdot_results.csv", "and", OUT_DIR / "spotcheck_txdot_summary.md")


if __name__ == "__main__":
    main()
