"""Best Bias Discovery analysis (WRITEUP §7): phantom roads — unnamed, import-era geometry in Overture's scored
road layer, a data-source behaviour the automated scorecard (length/count coverage x strata) does not measure
and in fact rewards.

Step 1 (DuckDB, challenge data only): per tract, km of drivable Overture road (scored `overture-roads` layer)
split by class group, whether the segment has names.primary / road_surface / speed_limits, and whether its
latest source edit (`max(sources[].update_time)`) predates 2012-01-01 — i.e. nothing has touched the segment
since the 2007-08 TIGER import era ("import age").
Step 2 (pandas): join strata; tabulate the unnamed share and the unnamed-and-unedited-since-2011 share by
region and by the scorecard strata (with n tracts and road km per row); km of the four *scored* classes that
are unnamed-and-unedited; within-region rural tribal vs non-tribal medians with Mann-Whitney p; the
self-constructed "import-era tract" stratum (>= 50 % of drivable km unnamed-and-unedited, with 30 % / 70 %
sensitivity); WLS with region fixed effects; the most affected tracts with county / AIANNH names and the
hazard columns used for the place-specific facts in WRITEUP §7.3.

Usage: PYTHONUTF8=1 python bias_discovery.py [--skip-extract] [--out PATH]
Writes <work>/features/road_attrs.parquet (long table), <work>/features/road_attrs_joined.parquet (per tract)
and prints markdown tables, teed to --out (default <work>/bias_discovery_out.md).
County names come from external/census_gaz_counties_2023_subset.csv (Census Bureau 2023 Gazetteer, public
domain; labels only, see external/SOURCES.md); without that file the FIPS code is printed instead.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
HERE = Path(__file__).resolve().parent
REGIONS = ["maricopa-az", "northern-ca", "eastern-ok", "south-central-tx", "eastern-wa"]
NAMED = "('motorway','trunk','primary','secondary')"
IMPORT_CUTOFF = "2012-01-01"  # latest sources[].update_time strictly before this = unedited since the TIGER-import era
# Texas border colonia belt used for the within-rural-Texas comparison (state+county FIPS)
BORDER_BELT = {"48323": "Maverick", "48505": "Zapata", "48047": "Brooks", "48271": "Kinney", "48507": "Zavala", "48137": "Edwards"}


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
    # has_import_age: the newest update_time among the segment's sources is before 2012-01-01 (ISO-8601 strings
    # compare lexicographically). Segments whose sources carry no update_time at all (a few hundred per region)
    # count as NOT import-aged, which can only understate the stale share.
    con.sql(f"""
        CREATE TABLE roads AS
        SELECT CASE WHEN class IN {NAMED} THEN 'named' ELSE 'minor' END AS cgrp, class,
               names.primary IS NOT NULL AS has_name,
               road_surface IS NOT NULL AND len(road_surface) > 0 AS has_surface,
               speed_limits IS NOT NULL AND len(speed_limits) > 0 AS has_speed,
               coalesce(list_max(list_transform(sources, s -> s.update_time)) < '{IMPORT_CUTOFF}', false) AS has_import_age,
               bbox, geometry
        FROM '{ref}overture-roads.parquet'
    """)
    df = con.sql("""
        SELECT t.GEOID, r.cgrp, r.class, r.has_name, r.has_surface, r.has_speed, r.has_import_age,
               sum(ST_Length_Spheroid(ST_FlipCoordinates(
                   CASE WHEN ST_Within(r.geometry, t.geometry) THEN r.geometry
                        ELSE ST_Intersection(r.geometry, t.geometry) END)) / 1000.0) AS km
        FROM roads r JOIN tracts t
          ON r.bbox.xmin <= t.bbox.xmax AND r.bbox.xmax >= t.bbox.xmin
         AND r.bbox.ymin <= t.bbox.ymax AND r.bbox.ymax >= t.bbox.ymin
         AND ST_Intersects(r.geometry, t.geometry)
        GROUP BY 1,2,3,4,5,6,7
    """).df()
    con.close()
    df["region"] = region
    return df


def tract_table(long: pd.DataFrame) -> pd.DataFrame:
    def ksum(mask):
        return long[mask].groupby("GEOID").km.sum()
    unnamed, stale, named_cls = ~long.has_name, long.has_import_age, long.cgrp == "named"
    t = pd.DataFrame({
        "road_km": long.groupby("GEOID").km.sum(),
        "minor_km": ksum(~named_cls),
        "residential_km": ksum(long["class"] == "residential"),
        "unnamed_km": ksum(unnamed),
        "unnamed_minor_km": ksum(unnamed & ~named_cls),
        "unnamed_residential_km": ksum(unnamed & (long["class"] == "residential")),
        "nosurface_km": ksum(~long.has_surface),
        "nospeed_km": ksum(~long.has_speed),
        "nospeed_named_km": ksum(~long.has_speed & named_cls),
        "named_km": ksum(named_cls),
        "stale_km": ksum(stale),                                   # unedited since 2011, any name status
        "unnamed_stale_km": ksum(unnamed & stale),                 # unnamed AND unedited since 2011 ("phantom" candidates)
        "named_stale_km": ksum(~unnamed & stale),
        "stale_scored_km": ksum(stale & named_cls),                # four scored classes, unedited since 2011
        "unnamed_stale_scored_km": ksum(unnamed & stale & named_cls),
    }).fillna(0.0)
    rk = t.road_km.replace(0, np.nan)
    t["unnamed_share"] = t.unnamed_km / rk
    t["unnamed_res_share"] = t.unnamed_residential_km / t.residential_km.replace(0, np.nan)
    t["nosurface_share"] = t.nosurface_km / rk
    t["nospeed_named_share"] = t.nospeed_named_km / t.named_km.replace(0, np.nan)
    t["stale_share"] = t.stale_km / rk
    t["unnamed_stale_share"] = t.unnamed_stale_km / rk
    return t.reset_index()


def q4(s: pd.Series, labels=("Q1 low", "Q2", "Q3", "Q4 high")) -> pd.Series:
    return pd.qcut(s.rank(method="first"), 4, labels=list(labels))


def county_names() -> dict[str, str]:
    p = HERE / "external" / "census_gaz_counties_2023_subset.csv"
    if not p.exists():
        return {}
    g = pd.read_csv(p, dtype=str)
    return dict(zip(g.STATEFP + g.COUNTYFP, g.USPS + " " + g.NAME.str.replace(" County", "", regex=False)))


def wshare(g, num, den):
    return g[num].sum() / g[den].sum()


def mw(a: pd.Series, b: pd.Series) -> str:
    a, b = a.dropna(), b.dropna()
    if len(a) < 5 or len(b) < 5:
        return "n too small"
    return f"{mannwhitneyu(a, b, alternative='two-sided').pvalue:.2e}"


def analyse(t: pd.DataFrame, long: pd.DataFrame) -> None:
    f = pd.concat([pd.read_parquet(WORK / "features" / f"{r}.parquet") for r in REGIONS], ignore_index=True)
    s = pd.concat([pd.read_parquet(WORK / "strata" / r / f"{r}-strata-tract-table.parquet",
                                   columns=["GEOID", "STATEFP", "COUNTYFP", "usfs_WHP_mean", "usfs_BP_mean", "rucc_desc", "aiannh_name",
                                            "svi_housing_transport", "epht_heat_days_summer", "usdm_summer_dsci", "usdm_winter_dsci"])
                   for r in REGIONS], ignore_index=True)
    d = t.merge(f[["GEOID", "region", "pop_total", "land_km2", "pct_urban", "ur_class", "tribal_any", "tribal_pct",
                   "svi_overall", "cvi_overall", "rucc_2023", "housing_units", "poi_n", "poi_fire", "bld_n"]], on="GEOID") \
         .merge(s, on="GEOID", how="left")
    d["tribal"] = np.where(d.tribal_any.fillna(0).astype(float) > 0, "tribal", "non-tribal")
    d["svi_q"] = q4(d.svi_overall.fillna(d.svi_overall.median()))
    d["svi_decile"] = np.ceil(d.svi_overall.clip(lower=1e-9) * 10).clip(1, 10)  # CDC SVI RPL is a 0-1 percentile rank
    d["whp_q"] = q4(d.usfs_WHP_mean.fillna(0))
    d["pop_density"] = d.pop_total / d.land_km2.replace(0, np.nan)
    d["unnamed_km_per_1000pop"] = 1000 * d.unnamed_km / d.pop_total.replace(0, np.nan)
    d["county_fips"] = d.STATEFP.astype(str) + d.COUNTYFP.astype(str)
    cn = county_names()
    d["county"] = d.county_fips.map(cn).fillna(d.county_fips)
    d["where"] = np.where(d.aiannh_name.notna(), d.county + " — " + d.aiannh_name.fillna(""), d.county)
    d.to_parquet(WORK / "features" / "road_attrs_joined.parquet", index=False)
    pd.set_option("display.width", 220)

    # ------------------------------------------------------------------ 1. scale
    print("\n## 1. Unnamed drivable road km share (km-weighted), all five regions")
    print(f"tracts with road km: {len(d):,}; road km: {d.road_km.sum():,.0f}; unnamed km: {d.unnamed_km.sum():,.0f}")
    print(f"overall unnamed share: {wshare(d, 'unnamed_km', 'road_km'):.3f}  (minor classes only: {wshare(d, 'unnamed_minor_km', 'minor_km'):.3f}; residential only: {wshare(d, 'unnamed_residential_km', 'residential_km'):.3f})")
    print(f"unnamed AND unedited since 2011 ('import-era' km): {d.unnamed_stale_km.sum():,.0f} km = {wshare(d, 'unnamed_stale_km', 'road_km'):.3f} of all road km, "
          f"{d.unnamed_stale_km.sum() / d.unnamed_km.sum():.3f} of unnamed km")

    # ------------------------------------------------------------------ 2. edit age by region and by stratum
    print("\n## 2. Edit age (latest `sources[].update_time` < 2012-01-01) by region and by scorecard stratum")
    print("Columns: n tracts; road km; unnamed km; share of UNNAMED km unedited since 2011; share of NAMED km unedited since 2011; "
          "unnamed-and-unedited km; that km as a share of all road km; median tract unnamed-and-unedited share.")
    for key in ["region", "ur_class", "tribal", "svi_q", "whp_q"]:
        g = d.groupby(key, observed=True)
        tab = pd.DataFrame({
            "tracts": g.size(), "road_km": g.road_km.sum().round(0), "unnamed_km": g.unnamed_km.sum().round(0),
            "unnamed_share": g.apply(lambda x: wshare(x, "unnamed_km", "road_km")).round(3),
            "stale_share_of_unnamed": g.apply(lambda x: wshare(x, "unnamed_stale_km", "unnamed_km")).round(3),
            "stale_share_of_named": g.apply(lambda x: x.named_stale_km.sum() / max(x.road_km.sum() - x.unnamed_km.sum(), 1e-9)).round(3),
            "unnamed_stale_km": g.unnamed_stale_km.sum().round(0),
            "unnamed_stale_share": g.apply(lambda x: wshare(x, "unnamed_stale_km", "road_km")).round(3),
            "median_tract_unnamed_stale_share": g.unnamed_stale_share.median().round(3),
        })
        print(f"\n### edit age by {key}\n" + tab.to_markdown())
    print("\n### region x urban/rural: share of unnamed km unedited since 2011 vs share of named km")
    g = d.groupby(["region", "ur_class"], observed=True)
    print(pd.DataFrame({"tracts": g.size(), "road_km": g.road_km.sum().round(0),
                        "stale_share_of_unnamed": g.apply(lambda x: wshare(x, "unnamed_stale_km", "unnamed_km")).round(3),
                        "stale_share_of_named": g.apply(lambda x: x.named_stale_km.sum() / max(x.road_km.sum() - x.unnamed_km.sum(), 1e-9)).round(3),
                        "unnamed_stale_share": g.apply(lambda x: wshare(x, "unnamed_stale_km", "road_km")).round(3)}).to_markdown())

    # ------------------------------------------------------------------ 3. scored classes
    print("\n## 3. The four SCORED classes (motorway/trunk/primary/secondary): km unnamed AND unedited since 2011")
    print("This is the km that enters the organiser's transport_gap numerator although nobody has edited it since the import era and it has no name.")
    sc = long[long.cgrp == "named"]
    g = sc.groupby("region")
    tab = pd.DataFrame({
        "scored_km": g.km.sum().round(0),
        "unnamed_scored_km": sc[~sc.has_name].groupby("region").km.sum().round(0),
        "stale_scored_km": sc[sc.has_import_age].groupby("region").km.sum().round(0),
        "unnamed_stale_scored_km": sc[(~sc.has_name) & sc.has_import_age].groupby("region").km.sum().round(1),
    }).fillna(0.0)
    tab["unnamed_stale_share_of_scored"] = (tab.unnamed_stale_scored_km / tab.scored_km).round(4)
    tab.loc["ALL"] = tab.sum(numeric_only=True)
    tab.loc["ALL", "unnamed_stale_share_of_scored"] = round(tab.loc["ALL", "unnamed_stale_scored_km"] / tab.loc["ALL", "scored_km"], 4)
    print("\n### by region\n" + tab.to_markdown())
    g = sc.groupby("class")
    tab = pd.DataFrame({"scored_km": g.km.sum().round(0),
                        "unnamed_stale_km": sc[(~sc.has_name) & sc.has_import_age].groupby("class").km.sum().round(1)}).fillna(0.0)
    tab["share"] = (tab.unnamed_stale_km / tab.scored_km).round(4)
    print("\n### by class\n" + tab.to_markdown())
    for key in ["ur_class", "tribal", "svi_q"]:
        g = d.groupby(key, observed=True)
        tab = pd.DataFrame({"tracts": g.size(), "scored_km": g.named_km.sum().round(0),
                            "unnamed_stale_scored_km": g.unnamed_stale_scored_km.sum().round(1),
                            "share": g.apply(lambda x: wshare(x, "unnamed_stale_scored_km", "named_km")).round(4),
                            "tracts_with_any": g.apply(lambda x: int((x.unnamed_stale_scored_km > 0).sum()))})
        print(f"\n### by {key}\n" + tab.to_markdown())
    tot_un_st = sc[(~sc.has_name) & sc.has_import_age].km.sum()
    print(f"\nTotal scored-class km that is unnamed and unedited since 2011: {tot_un_st:,.1f} km of {sc.km.sum():,.0f} scored km "
          f"({tot_un_st / sc.km.sum():.2%}); tracts with any such km: {int((d.unnamed_stale_scored_km > 0).sum())} of {len(d):,}.")
    print(f"For comparison, unnamed-and-unedited km in the MINOR classes (tertiary/unclassified/residential): {d.unnamed_stale_km.sum() - d.unnamed_stale_scored_km.sum():,.0f} km.")

    # ------------------------------------------------------------------ 4. strata tables (supporting)
    print("\n## 4. Unnamed share by scorecard stratum (supporting evidence; n tracts and km per row)")
    for key in ["region", "ur_class", "tribal", "svi_q", "whp_q"]:
        g = d.groupby(key, observed=True)
        tab = pd.DataFrame({"tracts": g.size(), "road_km": g.road_km.sum().round(0),
                            "unnamed_share": g.apply(lambda x: wshare(x, "unnamed_km", "road_km")).round(3),
                            "unnamed_res_share": g.apply(lambda x: wshare(x, "unnamed_residential_km", "residential_km")).round(3),
                            "unnamed_stale_share": g.apply(lambda x: wshare(x, "unnamed_stale_km", "road_km")).round(3),
                            "nosurface_share": g.apply(lambda x: wshare(x, "nosurface_km", "road_km")).round(3),
                            "nospeed_named_share": g.apply(lambda x: wshare(x, "nospeed_named_km", "named_km")).round(3),
                            "median_tract_unnamed_share": g.unnamed_share.median().round(3)})
        print(f"\n### by {key}\n" + tab.to_markdown())
    print("\n### tribal x urban/rural (unnamed share of residential km; median tract share)")
    g = d.groupby(["ur_class", "tribal"], observed=True)
    print(pd.DataFrame({"tracts": g.size(), "unnamed_res_share": g.apply(lambda x: wshare(x, "unnamed_residential_km", "residential_km")).round(3),
                        "median_tract_unnamed_share": g.unnamed_share.median().round(3),
                        "median_tract_unnamed_stale_share": g.unnamed_stale_share.median().round(3),
                        "pop": g.pop_total.sum().astype(int)}).to_markdown())
    print("\n### region x tribal (unnamed share of residential km)")
    g = d.groupby(["region", "tribal"], observed=True)
    print(pd.DataFrame({"tracts": g.size(), "unnamed_res_share": g.apply(lambda x: wshare(x, "unnamed_residential_km", "residential_km")).round(3),
                        "pop": g.pop_total.sum().astype(int)}).to_markdown())

    # ------------------------------------------------------------------ 5. within-region tests
    print("\n## 5. Within-region comparisons (rural tracts only): medians and Mann-Whitney U (two-sided)")
    rows = []
    rural = d[d.ur_class == "Rural"]
    for r, g in rural.groupby("region"):
        a, b = g[g.tribal == "tribal"], g[g.tribal == "non-tribal"]
        rows.append({"region": r, "comparison": "tribal vs non-tribal", "n_a": len(a), "n_b": len(b),
                     "median_unnamed_share_a": round(a.unnamed_share.median(), 3) if len(a) else np.nan,
                     "median_unnamed_share_b": round(b.unnamed_share.median(), 3) if len(b) else np.nan,
                     "p_unnamed": mw(a.unnamed_share, b.unnamed_share),
                     "median_unnamed_stale_share_a": round(a.unnamed_stale_share.median(), 3) if len(a) else np.nan,
                     "median_unnamed_stale_share_b": round(b.unnamed_stale_share.median(), 3) if len(b) else np.nan,
                     "p_unnamed_stale": mw(a.unnamed_stale_share, b.unnamed_stale_share)})
    tx = rural[rural.region == "south-central-tx"]
    a, b = tx[tx.county_fips.isin(BORDER_BELT)], tx[~tx.county_fips.isin(BORDER_BELT)]
    rows.append({"region": "south-central-tx", "comparison": "border colonia belt (Maverick, Zapata, Brooks, Kinney, Zavala, Edwards) vs rest of rural TX",
                 "n_a": len(a), "n_b": len(b),
                 "median_unnamed_share_a": round(a.unnamed_share.median(), 3), "median_unnamed_share_b": round(b.unnamed_share.median(), 3),
                 "p_unnamed": mw(a.unnamed_share, b.unnamed_share),
                 "median_unnamed_stale_share_a": round(a.unnamed_stale_share.median(), 3), "median_unnamed_stale_share_b": round(b.unnamed_stale_share.median(), 3),
                 "p_unnamed_stale": mw(a.unnamed_stale_share, b.unnamed_stale_share)})
    ok = rural[rural.region == "eastern-ok"]
    a, b = ok[ok.aiannh_name.fillna("").str.contains("Cheyenne and Arapaho|Choctaw")], ok[ok.aiannh_name.isna()]
    rows.append({"region": "eastern-ok", "comparison": "Cheyenne-Arapaho / Choctaw OTSA tracts vs rural tracts outside any AIANNH area",
                 "n_a": len(a), "n_b": len(b),
                 "median_unnamed_share_a": round(a.unnamed_share.median(), 3), "median_unnamed_share_b": round(b.unnamed_share.median(), 3),
                 "p_unnamed": mw(a.unnamed_share, b.unnamed_share),
                 "median_unnamed_stale_share_a": round(a.unnamed_stale_share.median(), 3), "median_unnamed_stale_share_b": round(b.unnamed_stale_share.median(), 3),
                 "p_unnamed_stale": mw(a.unnamed_stale_share, b.unnamed_stale_share)})
    print(pd.DataFrame(rows).to_markdown(index=False))
    print("\n(a = first-named group, b = second; shares are per-tract fractions of drivable road km; 'n too small' when a group has < 5 tracts.)")

    # ------------------------------------------------------------------ 6. WLS
    import statsmodels.formula.api as smf  # open-source; used only here
    m = d.dropna(subset=["unnamed_share", "svi_overall"]).copy()
    m["rural"] = (m.ur_class == "Rural").astype(float)
    m["is_tribal"] = (m.tribal == "tribal").astype(float)
    m["log_density"] = np.log(m.pop_density.clip(lower=0.1))
    m["whp"] = m.usfs_WHP_mean.fillna(0)
    print("\n## 6. WLS (weights = road km), region fixed effects — descriptive pooled test")
    for y in ["unnamed_share", "unnamed_stale_share"]:
        res = smf.wls(f"{y} ~ rural + is_tribal + svi_overall + log_density + whp + C(region)", data=m, weights=m.road_km).fit(cov_type="HC1")
        print(f"\n### dependent: {y}\n")
        print(res.summary().tables[1].as_text())
        print(f"n = {int(res.nobs)}, R2 = {res.rsquared:.3f}  (tracts dropped for missing SVI: {len(d) - int(res.nobs)})")

    # ------------------------------------------------------------------ 7. import-era tracts (self-constructed stratum)
    print("\n## 7. Import-era tracts: >= X % of drivable km is unnamed AND unedited since 2011 (self-constructed stratum)")
    pop_all = d.pop_total.sum()
    trib_all = d[d.tribal == "tribal"].pop_total.sum() / pop_all
    rows = []
    for thr in [0.3, 0.5, 0.7]:
        e = d[d.unnamed_stale_share >= thr]
        rows.append({"threshold": f">= {thr:.0%}", "tracts": len(e), "pop": int(e.pop_total.sum()), "pop_share": f"{e.pop_total.sum() / pop_all:.2%}",
                     "tribal_pop_share": f"{e[e.tribal == 'tribal'].pop_total.sum() / max(e.pop_total.sum(), 1):.1%}",
                     "overrep_vs_all": round(e[e.tribal == 'tribal'].pop_total.sum() / max(e.pop_total.sum(), 1) / trib_all, 2),
                     "rural_tracts": int((e.ur_class == "Rural").sum()), "median_svi": round(e.svi_overall.median(), 3),
                     "pop_in_svi_top_decile": int(e[e.svi_decile >= 10].pop_total.sum()), "counties": e.county.nunique(),
                     "road_km": int(e.road_km.sum()), "unnamed_stale_km": int(e.unnamed_stale_km.sum()), "scored_km": int(e.named_km.sum())})
    print(pd.DataFrame(rows).to_markdown(index=False))
    print(f"\n(five-region population {pop_all:,.0f}; tribal share of population overall {trib_all:.1%}; median tract SVI overall {d.svi_overall.median():.3f})")
    e = d[d.unnamed_stale_share >= 0.5].copy()
    print(f"\n### Import-era tracts at the 50 % threshold: {len(e)} tracts, {int(e.pop_total.sum()):,} people")
    print("\n#### by region x tribal")
    print(e.groupby(["region", "tribal"], observed=True).agg(tracts=("GEOID", "size"), pop=("pop_total", "sum"), road_km=("road_km", "sum"),
                                                              unnamed_stale_km=("unnamed_stale_km", "sum")).round(0).to_markdown())
    print("\n#### by county (all counties with an import-era tract)")
    cty = e.groupby(["region", "county"]).agg(tracts=("GEOID", "size"), pop=("pop_total", "sum"), road_km=("road_km", "sum"),
                                              unnamed_stale_km=("unnamed_stale_km", "sum"), median_svi=("svi_overall", "median"),
                                              aiannh=("aiannh_name", lambda x: "; ".join(sorted(set(x.dropna()))))).round(2)
    print(cty.sort_values("pop", ascending=False).to_markdown())
    print("\n#### population of import-era tracts by SVI decile (1 = least vulnerable), vs the five-region population")
    dec = pd.DataFrame({"import_era_pop": e.groupby("svi_decile").pop_total.sum(), "all_pop": d.groupby("svi_decile").pop_total.sum()}).fillna(0)
    dec["import_era_share"] = (dec.import_era_pop / dec.import_era_pop.sum()).round(3)
    dec["all_share"] = (dec.all_pop / dec.all_pop.sum()).round(3)
    dec["ratio"] = (dec.import_era_share / dec.all_share).round(2)
    print(dec.astype({"import_era_pop": int, "all_pop": int}).to_markdown())
    print("\n#### hazard exposure of import-era tracts (medians) vs all tracts in the same region")
    haz = ["epht_heat_days_summer", "usdm_summer_dsci", "usfs_WHP_mean", "svi_overall"]
    rows = []
    for r in REGIONS:
        er, dr = e[e.region == r], d[d.region == r]
        if len(er) == 0:
            continue
        row = {"region": r, "import_era_tracts": len(er)}
        for h in haz:
            row[h + "_import_era"] = round(er[h].median(), 2)
            row[h + "_region"] = round(dr[h].median(), 2)
        rows.append(row)
    print(pd.DataFrame(rows).to_markdown(index=False))
    print("\n#### all import-era tracts (50 % threshold), sorted by population")
    cols = ["GEOID", "where", "ur_class", "pop_total", "road_km", "unnamed_share", "unnamed_stale_share", "named_km", "svi_overall", "epht_heat_days_summer", "usdm_summer_dsci", "usfs_WHP_mean"]
    print(e.sort_values("pop_total", ascending=False)[cols].round(3).to_markdown(index=False))

    # ------------------------------------------------------------------ 8. named tracts
    cols = ["GEOID", "where", "ur_class", "pop_total", "road_km", "unnamed_km", "unnamed_share", "unnamed_stale_share", "svi_overall", "svi_decile",
            "epht_heat_days_summer", "usdm_summer_dsci", "usfs_WHP_mean"]
    print("\n## 8. Named tracts")
    print("\n### 8a. Most affected populated tracts (pop >= 1000), ranked by unnamed road km (area-biased: large ranch tracts)")
    print(d[d.pop_total >= 1000].sort_values("unnamed_km", ascending=False).head(15)[cols].round(3).to_markdown(index=False))
    print("\n### 8b. Populated tracts (pop >= 1000, >= 20 road km) with the highest unnamed SHARE")
    print(d[(d.pop_total >= 1000) & (d.road_km >= 20)].sort_values("unnamed_share", ascending=False).head(15)[cols].round(3).to_markdown(index=False))
    print("\n### 8c. Populated tracts (pop >= 1000, >= 20 road km) with the highest unnamed-AND-unedited (import-era) share")
    print(d[(d.pop_total >= 1000) & (d.road_km >= 20)].sort_values("unnamed_stale_share", ascending=False).head(15)[cols].round(3).to_markdown(index=False))

    # ------------------------------------------------------------------ 9. clusters: one checkable fact each
    print("\n## 9. Named clusters: hazard and vulnerability columns from the challenge strata table (medians over the cluster's tracts)")
    clusters = {
        "Maverick County TX (all scored tracts)": d.county_fips == "48323",
        "Maverick: 48323950701 + 48323950207 (east of Eagle Pass; Kickapoo Reservation)": d.GEOID.isin(["48323950701", "48323950207"]),
        "Zapata County TX": d.county_fips == "48505",
        "Brooks County TX": d.county_fips == "48047",
        "Kinney County TX": d.county_fips == "48271",
        "Zavala County TX": d.county_fips == "48507",
        "Edwards County TX": d.county_fips == "48137",
        "Cheyenne and Arapaho OTSA, Washita County OK (40149965000/965100/965400)": d.GEOID.isin(["40149965000", "40149965100", "40149965400"]),
        "Cheyenne and Arapaho OTSA (all tracts)": d.aiannh_name.fillna("").str.contains("Cheyenne and Arapaho"),
        "Choctaw OTSA (all tracts)": d.aiannh_name.fillna("").str.contains("Choctaw"),
    }
    rows = []
    for name, mask in clusters.items():
        c = d[mask]
        reg = d[d.region.isin(c.region.unique())]
        rows.append({"cluster": name, "tracts": len(c), "pop": int(c.pop_total.sum()), "road_km": int(c.road_km.sum()),
                     "unnamed_share_kmw": round(wshare(c, "unnamed_km", "road_km"), 3),
                     "unnamed_stale_share_kmw": round(wshare(c, "unnamed_stale_km", "road_km"), 3),
                     "import_era_tracts(>=50%)": int((c.unnamed_stale_share >= 0.5).sum()),
                     "median_svi": round(c.svi_overall.median(), 3), "svi_region_median": round(reg.svi_overall.median(), 3),
                     "median_heat_days_summer": round(c.epht_heat_days_summer.median(), 1), "heat_region_median": round(reg.epht_heat_days_summer.median(), 1),
                     "median_summer_dsci": round(c.usdm_summer_dsci.median(), 1), "dsci_region_median": round(reg.usdm_summer_dsci.median(), 1),
                     "median_whp": round(c.usfs_WHP_mean.median(), 1), "whp_region_median": round(reg.usfs_WHP_mean.median(), 1)})
    print(pd.DataFrame(rows).to_markdown(index=False))
    print("\nColumn meanings (challenge strata table): epht_heat_days_summer = CDC EPHT extreme-heat days per summer; usdm_summer_dsci = US Drought Monitor "
          "summer Drought Severity and Coverage Index (0-500); usfs_WHP_mean = USFS Wildfire Hazard Potential (mean); svi_overall = CDC SVI 2022 overall percentile rank.")

    # ------------------------------------------------------------------ 10. >= 50 % unnamed (the earlier headline count, kept for continuity)
    print("\n## 10. Tracts with >= 50 % of road km unnamed (any edit age): counts and population")
    bad = d[d.unnamed_share >= 0.5]
    print(bad.groupby(["region", "tribal"], observed=True).agg(tracts=("GEOID", "size"), pop=("pop_total", "sum")).to_markdown())
    print("\nPeople living in tracts where >= 50 % of drivable road km is unnamed:", int(bad.pop_total.sum()),
          f"({bad.pop_total.sum() / pop_all:.1%} of regional population); tribal share of those people: {bad[bad.tribal == 'tribal'].pop_total.sum() / max(bad.pop_total.sum(), 1):.1%} vs tribal share overall {trib_all:.1%}")


class _Tee(io.TextIOBase):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
        return len(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def main() -> None:
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else WORK / "bias_discovery_out.md"
    path = WORK / "features" / "road_attrs.parquet"
    with open(out, "w", encoding="utf-8") as fh:
        sys.stdout = _Tee(sys.__stdout__, fh)
        try:
            print(f"# bias_discovery.py output — Overture 2026-08-19.0 scored road layer, five regions; import-age cutoff {IMPORT_CUTOFF}")
            if "--skip-extract" not in sys.argv or not path.exists():
                long = pd.concat([extract(r) for r in REGIONS], ignore_index=True)
                long.to_parquet(path, index=False)
                print("extracted", len(long), "rows ->", path)
            long = pd.read_parquet(path)
            if "has_import_age" not in long.columns:
                raise SystemExit("cached road_attrs.parquet predates the import-age column; rerun without --skip-extract")
            t = tract_table(long)
            analyse(t, long)
        finally:
            sys.stdout = sys.__stdout__
    print("wrote", out)


if __name__ == "__main__":
    main()
