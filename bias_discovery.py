"""Best Bias Discovery analysis: road ATTRIBUTE completeness (names / surface / speed limits) in Overture,
a navigability dimension the automated scorecard (length/count coverage x strata) does not measure.

Step 1 (DuckDB, challenge data only): per tract, km of drivable Overture road (scored `overture-roads`
layer) split by class group and whether the segment has names.primary / road_surface / speed_limits.
Step 2 (pandas): join strata; tabulate the unnamed-road share by tribal status, urban/rural, SVI
quartile, wildfire-hazard quartile; OLS with region fixed effects; list the most affected tracts.

Usage: PYTHONUTF8=1 python modules/competitions/zindi-bias-bounty/bias_discovery.py [--skip-extract]
Writes <work>/features/road_attrs.parquet and prints markdown tables (pasted into WRITEUP.md).
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
REGIONS = ["maricopa-az", "northern-ca", "eastern-ok", "south-central-tx", "eastern-wa"]
NAMED = "('motorway','trunk','primary','secondary')"


def extract(region: str) -> pd.DataFrame:
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial; SET threads TO 8;")
    ref = WORK / "reference" / region / f"{region}-"
    strata = WORK / "strata" / region / f"{region}-"
    con.sql(f"""
        CREATE TABLE tracts AS
        SELECT t.GEOID, t.bbox, t.geometry
        FROM '{strata}census-tracts.parquet' t
        JOIN read_csv('{ref}sample-submission.csv', types={{'GEOID':'VARCHAR'}}) s USING (GEOID)
    """)
    con.sql(f"""
        CREATE TABLE roads AS
        SELECT CASE WHEN class IN {NAMED} THEN 'named' ELSE 'minor' END AS cgrp, class,
               names.primary IS NOT NULL AS has_name,
               road_surface IS NOT NULL AND len(road_surface) > 0 AS has_surface,
               speed_limits IS NOT NULL AND len(speed_limits) > 0 AS has_speed,
               bbox, geometry
        FROM '{ref}overture-roads.parquet'
    """)
    df = con.sql("""
        SELECT t.GEOID, r.cgrp, r.class, r.has_name, r.has_surface, r.has_speed,
               sum(ST_Length_Spheroid(ST_FlipCoordinates(
                   CASE WHEN ST_Within(r.geometry, t.geometry) THEN r.geometry
                        ELSE ST_Intersection(r.geometry, t.geometry) END)) / 1000.0) AS km
        FROM roads r JOIN tracts t
          ON r.bbox.xmin <= t.bbox.xmax AND r.bbox.xmax >= t.bbox.xmin
         AND r.bbox.ymin <= t.bbox.ymax AND r.bbox.ymax >= t.bbox.ymin
         AND ST_Intersects(r.geometry, t.geometry)
        GROUP BY 1,2,3,4,5,6
    """).df()
    con.close()
    df["region"] = region
    return df


def tract_table(long: pd.DataFrame) -> pd.DataFrame:
    g = long.groupby("GEOID")
    t = pd.DataFrame({
        "road_km": g.km.sum(),
        "minor_km": long[long.cgrp == "minor"].groupby("GEOID").km.sum(),
        "residential_km": long[long["class"] == "residential"].groupby("GEOID").km.sum(),
        "unnamed_km": long[~long.has_name].groupby("GEOID").km.sum(),
        "unnamed_minor_km": long[(~long.has_name) & (long.cgrp == "minor")].groupby("GEOID").km.sum(),
        "unnamed_residential_km": long[(~long.has_name) & (long["class"] == "residential")].groupby("GEOID").km.sum(),
        "nosurface_km": long[~long.has_surface].groupby("GEOID").km.sum(),
        "nospeed_km": long[~long.has_speed].groupby("GEOID").km.sum(),
        "nospeed_named_km": long[(~long.has_speed) & (long.cgrp == "named")].groupby("GEOID").km.sum(),
        "named_km": long[long.cgrp == "named"].groupby("GEOID").km.sum(),
    }).fillna(0.0)
    t["unnamed_share"] = t.unnamed_km / t.road_km.replace(0, np.nan)
    t["unnamed_res_share"] = t.unnamed_residential_km / t.residential_km.replace(0, np.nan)
    t["nosurface_share"] = t.nosurface_km / t.road_km.replace(0, np.nan)
    t["nospeed_named_share"] = t.nospeed_named_km / t.named_km.replace(0, np.nan)
    return t.reset_index()


def q4(s: pd.Series, labels=("Q1 low", "Q2", "Q3", "Q4 high")) -> pd.Series:
    return pd.qcut(s.rank(method="first"), 4, labels=list(labels))


def analyse(t: pd.DataFrame) -> None:
    f = pd.concat([pd.read_parquet(WORK / "features" / f"{r}.parquet") for r in REGIONS], ignore_index=True)
    s = pd.concat([pd.read_parquet(WORK / "strata" / r / f"{r}-strata-tract-table.parquet",
                                   columns=["GEOID", "usfs_WHP_mean", "usfs_BP_mean", "rucc_desc", "aiannh_name",
                                            "svi_housing_transport", "epht_heat_days_summer", "usdm_summer_dsci"])
                   for r in REGIONS], ignore_index=True)
    d = t.merge(f[["GEOID", "region", "pop_total", "land_km2", "pct_urban", "ur_class", "tribal_any", "tribal_pct",
                   "svi_overall", "cvi_overall", "rucc_2023", "housing_units", "poi_n", "poi_fire", "bld_n"]], on="GEOID") \
         .merge(s, on="GEOID", how="left")
    d["tribal"] = np.where(d.tribal_any.fillna(0).astype(float) > 0, "tribal", "non-tribal")
    d["svi_q"] = q4(d.svi_overall.fillna(d.svi_overall.median()))
    d["whp_q"] = q4(d.usfs_WHP_mean.fillna(0))
    d["pop_density"] = d.pop_total / d.land_km2.replace(0, np.nan)
    d["unnamed_km_per_1000pop"] = 1000 * d.unnamed_km / d.pop_total.replace(0, np.nan)
    d.to_parquet(WORK / "features" / "road_attrs_joined.parquet", index=False)

    def wshare(g, num, den):
        return g[num].sum() / g[den].sum()

    pd.set_option("display.width", 220)
    print("\n## Unnamed drivable road km share (km-weighted), all five regions")
    print(f"overall: {wshare(d, 'unnamed_km', 'road_km'):.3f}  (minor classes only: {wshare(d, 'unnamed_minor_km', 'minor_km'):.3f}; residential only: {wshare(d, 'unnamed_residential_km', 'residential_km'):.3f})")
    for key in ["region", "ur_class", "tribal", "svi_q", "whp_q"]:
        g = d.groupby(key, observed=True)
        tab = pd.DataFrame({"tracts": g.size(), "road_km": g.road_km.sum().round(0),
                            "unnamed_share": g.apply(lambda x: wshare(x, "unnamed_km", "road_km")).round(3),
                            "unnamed_res_share": g.apply(lambda x: wshare(x, "unnamed_residential_km", "residential_km")).round(3),
                            "nosurface_share": g.apply(lambda x: wshare(x, "nosurface_km", "road_km")).round(3),
                            "nospeed_named_share": g.apply(lambda x: wshare(x, "nospeed_named_km", "named_km")).round(3),
                            "median_tract_unnamed_share": g.unnamed_share.median().round(3)})
        print(f"\n### by {key}\n" + tab.to_markdown())
    print("\n### tribal x urban/rural (unnamed share of residential km; median tract share)")
    g = d.groupby(["ur_class", "tribal"], observed=True)
    print(pd.DataFrame({"tracts": g.size(), "unnamed_res_share": g.apply(lambda x: wshare(x, "unnamed_residential_km", "residential_km")).round(3),
                        "median_tract_unnamed_share": g.unnamed_share.median().round(3),
                        "pop": g.pop_total.sum()}).to_markdown())
    print("\n### region x tribal (unnamed share of residential km)")
    g = d.groupby(["region", "tribal"], observed=True)
    print(pd.DataFrame({"tracts": g.size(), "unnamed_res_share": g.apply(lambda x: wshare(x, "unnamed_residential_km", "residential_km")).round(3),
                        "pop": g.pop_total.sum()}).to_markdown())

    # OLS with region fixed effects: tract unnamed share ~ rural + tribal + svi + log density
    import statsmodels.formula.api as smf  # open-source; used only here
    m = d.dropna(subset=["unnamed_share", "svi_overall"]).copy()
    m["rural"] = (m.ur_class == "Rural").astype(float)
    m["is_tribal"] = (m.tribal == "tribal").astype(float)
    m["log_density"] = np.log(m.pop_density.clip(lower=0.1))
    m["whp"] = m.usfs_WHP_mean.fillna(0)
    res = smf.wls("unnamed_share ~ rural + is_tribal + svi_overall + log_density + whp + C(region)", data=m, weights=m.road_km).fit(cov_type="HC1")
    print("\n### WLS (weights = road km), unnamed share of tract road km, region fixed effects\n")
    print(res.summary().tables[1].as_text())
    print(f"n = {int(res.nobs)}, R2 = {res.rsquared:.3f}")

    print("\n### Most affected populated tracts (pop >= 1000), ranked by unnamed road km")
    cols = ["GEOID", "region", "aiannh_name", "ur_class", "pop_total", "road_km", "unnamed_km", "unnamed_share", "svi_overall", "usfs_WHP_mean"]
    top = d[d.pop_total >= 1000].sort_values("unnamed_km", ascending=False).head(15)[cols].round(3)
    print(top.to_markdown(index=False))
    print("\n### Populated tracts (pop >= 1000) with the highest unnamed SHARE (>= 20 road km)")
    top = d[(d.pop_total >= 1000) & (d.road_km >= 20)].sort_values("unnamed_share", ascending=False).head(15)[cols].round(3)
    print(top.to_markdown(index=False))
    print("\n### Tracts with >= 50% of road km unnamed: counts and population")
    bad = d[d.unnamed_share >= 0.5]
    print(bad.groupby(["region", "tribal"], observed=True).agg(tracts=("GEOID", "size"), pop=("pop_total", "sum")).to_markdown())
    print("\nPeople living in tracts where >=50% of drivable road km is unnamed:", int(bad.pop_total.sum()),
          f"({bad.pop_total.sum()/d.pop_total.sum():.1%} of regional population); tribal share of those people: {bad[bad.tribal=='tribal'].pop_total.sum()/max(bad.pop_total.sum(),1):.1%} vs tribal share overall {d[d.tribal=='tribal'].pop_total.sum()/d.pop_total.sum():.1%}")


def main() -> None:
    path = WORK / "features" / "road_attrs.parquet"
    if "--skip-extract" not in sys.argv or not path.exists():
        long = pd.concat([extract(r) for r in REGIONS], ignore_index=True)
        long.to_parquet(path, index=False)
        print("extracted", len(long), "rows ->", path)
    long = pd.read_parquet(path)
    t = tract_table(long)
    analyse(t)


if __name__ == "__main__":
    main()
