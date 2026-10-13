"""Per-tract feature extraction for the Zindi Bias Bounty Mapping Equity Challenge.

Uses ONLY the challenge-provided data (Overture extracts + ACS housing + strata).
Writes one parquet per region to <work>/features/<region>.parquet.

Usage:
    PYTHONUTF8=1 python modules/competitions/zindi-bias-bounty/features.py [region ...]
"""
from __future__ import annotations

import sys
import time
import os
from pathlib import Path

import duckdb

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
REGIONS = ["northern-ca", "eastern-ok", "maricopa-az", "south-central-tx", "eastern-wa"]

NAMED = "('motorway','trunk','primary','secondary')"
FIRE = "('fire_department')"
EMS = "('ambulance_and_ems_services')"
SCHOOL = "('elementary_school','middle_school','high_school','school','private_school','public_school')"
HOSP = "('hospital')"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")
    con.sql("SET threads TO 8;")
    return con


def build(region: str) -> None:
    con = connect()
    t0 = time.time()
    ref = WORK / "reference" / region / f"{region}-"
    strata = WORK / "strata" / region / f"{region}-"
    out = WORK / "features"
    out.mkdir(exist_ok=True)

    # Tract polygons (authoritative scored list = sample submission)
    con.sql(f"""
        CREATE TABLE tracts AS
        SELECT t.GEOID, t.STATEFP, t.ALAND, t.pop_total, t.pop_urban, t.pop_rural, t.pct_urban, t.ur_class,
               t.bbox, t.geometry
        FROM '{strata}census-tracts.parquet' t
        JOIN read_csv('{ref}sample-submission.csv', types={{'GEOID':'VARCHAR'}}) s USING (GEOID)
    """)
    n_tracts = con.sql("SELECT count(*) FROM tracts").fetchone()[0]
    print(f"[{region}] tracts: {n_tracts}", flush=True)

    # ---- Roads: km per tract by class group x route group (clipped to tract) ----
    con.sql(f"""
        CREATE TABLE roads AS
        SELECT id, class, subclass,
               CASE WHEN class IN {NAMED} THEN 'named' ELSE 'minor' END AS cgrp,
               CASE
                 WHEN routes IS NULL OR len(routes) = 0 THEN 'none'
                 WHEN list_contains(list_transform(routes, r -> r.network), 'US:I') THEN 'I'
                 WHEN list_contains(list_transform(routes, r -> r.network), 'US:US') THEN 'US'
                 WHEN len(list_filter(routes, r -> regexp_matches(coalesce(r.network,''), '^US:[A-Z]{{2}}$'))) > 0 THEN 'state'
                 WHEN len(list_filter(routes, r -> regexp_matches(coalesce(r.network,''), '^US:[A-Z]{{2}}:'))) > 0 THEN 'county'
                 ELSE 'other'
               END AS rgrp,
               names.primary IS NOT NULL AS has_name,
               bbox, geometry
        FROM '{ref}overture-roads.parquet'
    """)
    con.sql("""
        CREATE TABLE road_tract AS
        SELECT t.GEOID, r.cgrp, r.rgrp, r.class, r.has_name,
               ST_Length_Spheroid(ST_FlipCoordinates(
                   CASE WHEN ST_Within(r.geometry, t.geometry) THEN r.geometry
                        ELSE ST_Intersection(r.geometry, t.geometry) END)) / 1000.0 AS km
        FROM roads r
        JOIN tracts t
          ON r.bbox.xmin <= t.bbox.xmax AND r.bbox.xmax >= t.bbox.xmin
         AND r.bbox.ymin <= t.bbox.ymax AND r.bbox.ymax >= t.bbox.ymin
         AND ST_Intersects(r.geometry, t.geometry)
    """)
    con.sql("""
        CREATE TABLE road_feats AS
        SELECT GEOID,
            sum(km) AS road_km,
            sum(km) FILTER (cgrp='named') AS named_km,
            sum(km) FILTER (class='motorway') AS motorway_km,
            sum(km) FILTER (class='trunk') AS trunk_km,
            sum(km) FILTER (class='primary') AS primary_km,
            sum(km) FILTER (class='secondary') AS secondary_km,
            sum(km) FILTER (class='tertiary') AS tertiary_km,
            sum(km) FILTER (class='unclassified') AS unclassified_km,
            sum(km) FILTER (class='residential') AS residential_km,
            sum(km) FILTER (cgrp='named' AND rgrp IN ('I','US','state')) AS named_routed_km,
            sum(km) FILTER (cgrp='named' AND rgrp='county') AS named_county_km,
            sum(km) FILTER (cgrp='named' AND rgrp='other') AS named_otherroute_km,
            sum(km) FILTER (cgrp='named' AND rgrp='none') AS named_unrouted_km,
            sum(km) FILTER (cgrp='named' AND has_name) AS named_hasname_km,
            sum(km) FILTER (cgrp='minor' AND rgrp IN ('I','US','state')) AS minor_routed_km,
            sum(km) FILTER (cgrp='minor' AND rgrp='county') AS minor_county_km,
            sum(km) FILTER (cgrp='minor' AND rgrp='other') AS minor_otherroute_km,
            sum(km) FILTER (cgrp='minor' AND has_name) AS minor_hasname_km
        FROM road_tract GROUP BY GEOID
    """)
    print(f"[{region}] roads done {time.time()-t0:.0f}s", flush=True)

    # ---- Buildings: counts by source (centroid in tract) ----
    con.sql(f"""
        CREATE TABLE bld AS
        SELECT list_any_value(list_filter(sources, s -> s.property = '' OR s.property IS NULL)).dataset AS primary_src,
               list_contains(list_transform(sources, s -> s.dataset), 'Microsoft ML Buildings') AS has_ms,
               list_contains(list_transform(sources, s -> s.dataset), 'OpenStreetMap') AS has_osm,
               len(sources) AS n_src,
               subtype IS NOT NULL AS has_subtype,
               ST_Area_Spheroid(ST_FlipCoordinates(geometry)) AS area_m2,
               ST_Centroid(geometry) AS pt
        FROM '{ref}overture-buildings.parquet'
    """)
    con.sql("""
        CREATE TABLE bld_feats AS
        SELECT t.GEOID,
            count(*) AS bld_n,
            count(*) FILTER (b.primary_src = 'Microsoft ML Buildings') AS bld_ms_primary,
            count(*) FILTER (b.primary_src = 'OpenStreetMap') AS bld_osm_primary,
            count(*) FILTER (b.primary_src = 'Esri Community Maps') AS bld_esri_primary,
            count(*) FILTER (b.has_ms) AS bld_has_ms,
            count(*) FILTER (b.has_osm AND NOT b.has_ms) AS bld_osm_only,
            count(*) FILTER (b.n_src >= 2) AS bld_multi_src,
            sum(b.area_m2) AS bld_area_m2,
            median(b.area_m2) AS bld_area_med
        FROM bld b JOIN tracts t
          ON ST_X(b.pt) BETWEEN t.bbox.xmin AND t.bbox.xmax
         AND ST_Y(b.pt) BETWEEN t.bbox.ymin AND t.bbox.ymax
         AND ST_Contains(t.geometry, b.pt)
        GROUP BY t.GEOID
    """)
    print(f"[{region}] buildings done {time.time()-t0:.0f}s", flush=True)

    # ---- POIs ----
    con.sql(f"""
        CREATE TABLE poi AS
        SELECT categories.primary AS cat, confidence, operating_status,
               list_transform(sources, s -> s.dataset) AS src,
               geometry AS pt
        FROM '{ref}overture-pois.parquet'
    """)
    con.sql(f"""
        CREATE TABLE poi_feats AS
        SELECT t.GEOID,
            count(*) AS poi_n,
            count(*) FILTER (p.operating_status = 'permanently_closed') AS poi_closed,
            count(*) FILTER (p.confidence >= 0.5) AS poi_conf50,
            count(*) FILTER (p.cat IS NULL) AS poi_nocat,
            count(*) FILTER (p.cat IN {FIRE}) AS poi_fire,
            count(*) FILTER (p.cat IN {EMS}) AS poi_ems,
            count(*) FILTER (p.cat IN {SCHOOL}) AS poi_school,
            count(*) FILTER (p.cat IN {HOSP}) AS poi_hospital,
            count(*) FILTER (list_contains(p.src, 'meta')) AS poi_meta,
            count(*) FILTER (list_contains(p.src, 'Microsoft')) AS poi_msft,
            avg(p.confidence) AS poi_conf_mean
        FROM poi p JOIN tracts t
          ON ST_X(p.pt) BETWEEN t.bbox.xmin AND t.bbox.xmax
         AND ST_Y(p.pt) BETWEEN t.bbox.ymin AND t.bbox.ymax
         AND ST_Contains(t.geometry, p.pt)
        GROUP BY t.GEOID
    """)
    print(f"[{region}] pois done {time.time()-t0:.0f}s", flush=True)

    # ---- Join everything with strata ----
    con.sql(f"""
        CREATE TABLE feats AS
        SELECT t.GEOID, '{region}' AS region, t.STATEFP, t.ALAND / 1e6 AS land_km2, t.pop_total, t.pct_urban, t.ur_class,
               h.housing_units,
               s.ruca_primary, s.rucc_2023, s.rucc_metro, s.nchs_2013, s.tribal_any, s.tribal_pct,
               s.svi_overall, s.cvi_overall, s.usfs_BuildingCount_sum, s.usfs_HUCount_sum, s.carbonplan_buildings,
               r.* EXCLUDE (GEOID), b.* EXCLUDE (GEOID), p.* EXCLUDE (GEOID)
        FROM tracts t
        LEFT JOIN '{ref}census-acs-housing.parquet' h USING (GEOID)
        LEFT JOIN '{strata}strata-tract-table.parquet' s USING (GEOID)
        LEFT JOIN road_feats r USING (GEOID)
        LEFT JOIN bld_feats b USING (GEOID)
        LEFT JOIN poi_feats p USING (GEOID)
    """)
    # fill missing aggregates with 0 (tract with no feature of that kind)
    cols = [c[0] for c in con.sql("DESCRIBE feats").fetchall()]
    fill = [c for c in cols if c.endswith("_km") or c.startswith("bld_") or c.startswith("poi_") or c == "road_km"]
    sel = ", ".join(f"coalesce({c}, 0) AS {c}" if c in fill else c for c in cols)
    con.sql(f"COPY (SELECT {sel} FROM feats ORDER BY GEOID) TO '{out / (region + '.parquet')}' (FORMAT PARQUET)")
    n = con.sql(f"SELECT count(*) FROM '{out / (region + '.parquet')}'").fetchone()[0]
    print(f"[{region}] wrote {n} rows -> {out / (region + '.parquet')} ({time.time()-t0:.0f}s)", flush=True)
    con.close()


if __name__ == "__main__":
    regions = sys.argv[1:] or REGIONS
    for r in regions:
        build(r)
