"""Two-panel figure for WRITEUP.md section 7 (Best Bias Discovery: unnamed roads).

(a) Tract-level choropleth of the unnamed share of drivable Overture road km for Maverick County TX
    (Eagle Pass / Kickapoo Reservation) and Washita County OK (Cheyenne and Arapaho OTSA), with the
    unnamed segments themselves drawn as thin lines over the tract fill.
(b) Km-weighted unnamed share by stratum (urban/rural, tribal, SVI quartile, wildfire-hazard quartile).

Inputs (challenge data only): <work>/features/road_attrs_joined.parquet (bias_discovery.py output),
<work>/strata/<region>/<region>-census-tracts.parquet, <work>/reference/<region>/<region>-overture-roads.parquet.
Output: modules/competitions/zindi-bias-bounty/figures/fig_unnamed_roads.png (1600 x 900 px).

Usage: PYTHONUTF8=1 python modules/competitions/zindi-bias-bounty/figure_unnamed_roads.py
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from shapely import wkb

matplotlib.use("Agg")

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
OUT = Path(__file__).parent / "figures" / "fig_unnamed_roads.png"
EQUAL_AREA = "EPSG:5070"  # organisers' length/area CRS

# Single-hue sequential ramp (blue 100 -> 700) and neutral inks.
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
        "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("blue_seq", RAMP)
INK, INK2, INK3, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#fcfcfb"
BAR = "#2a78d6"

SHORT = {"Kickapoo (TX) Reservation": "Kickapoo (TX) Res."}
COUNTIES = {  # region, state FIPS, county FIPS, title
    "maverick": ("south-central-tx", "48", "323", "Maverick County, TX\n(Eagle Pass and its colonias)"),
    "washita": ("eastern-ok", "40", "149", "Washita County, OK\n(Cheyenne and Arapaho OTSA)"),
}


def county_layers(region: str, state: str, county: str) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Tract polygons of one county and the drivable road segments clipped to the county, with has_name."""
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")
    tr = con.sql(f"""
        SELECT GEOID, NAMELSAD, pop_total, ur_class, ST_AsWKB(geometry) AS wkb
        FROM '{WORK}/strata/{region}/{region}-census-tracts.parquet'
        WHERE STATEFP = '{state}' AND COUNTYFP = '{county}'
    """).df()
    con.sql(f"""
        CREATE TABLE cty AS SELECT ST_Union_Agg(geometry) AS g
        FROM '{WORK}/strata/{region}/{region}-census-tracts.parquet'
        WHERE STATEFP = '{state}' AND COUNTYFP = '{county}'
    """)
    rd = con.sql(f"""
        SELECT r.class, r.names.primary IS NOT NULL AS has_name,
               ST_AsWKB(CASE WHEN ST_Within(r.geometry, c.g) THEN r.geometry ELSE ST_Intersection(r.geometry, c.g) END) AS wkb
        FROM '{WORK}/reference/{region}/{region}-overture-roads.parquet' r, cty c
        WHERE ST_Intersects(r.geometry, c.g)
    """).df()
    con.close()
    tracts = gpd.GeoDataFrame(tr.drop(columns="wkb"), geometry=[wkb.loads(bytes(b)) for b in tr.wkb], crs="EPSG:4326")
    roads = gpd.GeoDataFrame(rd.drop(columns="wkb"), geometry=[wkb.loads(bytes(b)) for b in rd.wkb], crs="EPSG:4326")
    roads = roads[~roads.geometry.is_empty].explode(ignore_index=True)
    roads = roads[roads.geom_type == "LineString"]  # ST_Intersection can leave point parts at the county edge
    return tracts.to_crs(EQUAL_AREA), roads.to_crs(EQUAL_AREA)


def strata_table(d: pd.DataFrame) -> list[tuple[str, list[tuple[str, float, int]]]]:
    """Km-weighted unnamed share per stratum: [(group title, [(label, share, n_tracts), ...])]."""
    def rows(key: str, order: list[str], names: dict[str, str] | None = None):
        out = []
        for lvl in order:
            g = d[d[key].astype(str) == lvl]
            out.append(((names or {}).get(lvl, lvl), g.unnamed_km.sum() / g.road_km.sum(), len(g)))
        return out
    return [
        ("Urban / rural (Census 2020)", rows("ur_class", ["Urban", "Rural"])),
        ("Tribal land (any AIANNH overlap)", rows("tribal", ["non-tribal", "tribal"], {"non-tribal": "Non-tribal", "tribal": "Tribal"})),
        ("CDC SVI quartile", rows("svi_q", ["Q1 low", "Q2", "Q3", "Q4 high"], {"Q1 low": "Q1 (least vulnerable)", "Q4 high": "Q4 (most vulnerable)"})),
        ("USFS wildfire-hazard quartile", rows("whp_q", ["Q1 low", "Q2", "Q3", "Q4 high"], {"Q1 low": "Q1 (lowest)", "Q4 high": "Q4 (highest)"})),
    ]


def draw_map(ax, tracts: gpd.GeoDataFrame, roads: gpd.GeoDataFrame, shares: pd.DataFrame, title: str, norm: Normalize) -> None:
    tracts = tracts.merge(shares, left_on="GEOID", right_index=True, how="left")
    tracts.plot(ax=ax, column="share", cmap=CMAP, norm=norm, edgecolor=SURFACE, linewidth=1.2)
    roads[roads.has_name].plot(ax=ax, color=SURFACE, linewidth=0.35, alpha=0.9)
    roads[~roads.has_name].plot(ax=ax, color=INK, linewidth=0.3, alpha=0.55)
    tracts.boundary.plot(ax=ax, color=SURFACE, linewidth=1.2)
    # label every tract with its unnamed share; small urban tracts are labelled once, as a cluster
    big = tracts[tracts.geometry.area > 0.04 * tracts.geometry.area.sum()]
    for _, t in big.iterrows():
        p = t.geometry.representative_point()
        dark = t.share >= 0.45
        lab = t.NAMELSAD.replace("Census Tract ", "tract ") + (f"\n{SHORT.get(t.aiannh, t.aiannh)}" if isinstance(t.aiannh, str) and t.aiannh not in title else "")
        ax.text(p.x, p.y, f"{t.share:.0%}\n{lab}", ha="center", va="center",
                fontsize=8.5, color=SURFACE if dark else INK, fontweight="bold" if t.share >= 0.75 else "normal")
    small = tracts[tracts.geometry.area <= 0.04 * tracts.geometry.area.sum()]
    if len(small):
        c = small.geometry.union_all().representative_point()
        lo, hi = small.share.min(), small.share.max()
        ax.annotate(f"{len(small)} city tracts:\n{lo:.0%}–{hi:.0%} unnamed", xy=(c.x, c.y), xytext=(-10, -80), textcoords="offset points",
                    fontsize=8.5, color=INK, ha="left", arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8),
                    bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec="none", alpha=0.9))
    ax.set_title(title, fontsize=10.5, color=INK, loc="left", pad=6)
    ax.set_anchor("N")
    ax.set_axis_off()
    # 10 km scale bar (CRS is metres)
    x0, y0, x1, y1 = tracts.total_bounds
    bx, by = x0 + 0.04 * (x1 - x0), y0 + 0.03 * (y1 - y0)
    ax.plot([bx, bx + 10_000], [by, by], color=INK2, lw=1.5, solid_capstyle="butt")
    ax.text(bx + 5_000, by + 0.012 * (y1 - y0), "10 km", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xlim(x0 - 0.03 * (x1 - x0), x1 + 0.03 * (x1 - x0))
    ax.set_ylim(y0 - 0.03 * (y1 - y0), y1 + 0.03 * (y1 - y0))


def draw_bars(ax, groups) -> None:
    labels, vals, ns, ypos, gtitles = [], [], [], [], []
    y = 0.0
    for title, rows in groups:
        gtitles.append((title, y))
        y -= 0.75
        for lab, share, n in rows:
            labels.append(f"{lab}  (n = {n:,})"); vals.append(share); ns.append(n); ypos.append(y)
            y -= 1.0
        y -= 0.55
    ax.barh(ypos, [v * 100 for v in vals], height=0.68, color=BAR, edgecolor=SURFACE, linewidth=1)
    for yp, v, n in zip(ypos, vals, ns):
        ax.text(v * 100 + 0.6, yp, f"{v:.1%}", va="center", ha="left", fontsize=9, color=INK)
    for title, yt in gtitles:
        ax.text(-0.42, yt, title, fontsize=9.5, color=INK2, va="center", ha="left", fontweight="bold", transform=ax.get_yaxis_transform())
    ax.set_yticks(ypos); ax.set_yticklabels(labels, fontsize=9, color=INK)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xlim(0, 36); ax.set_xticks([0, 10, 20, 30])
    ax.set_xlabel("Unnamed share of drivable road km, % (km-weighted, all five regions)", fontsize=9, color=INK2, loc="right")
    ax.tick_params(axis="x", colors=INK2, labelsize=8.5)
    ax.grid(axis="x", color="#e6e5e1", lw=0.8); ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#d6d5d0")
    ax.set_ylim(min(ypos) - 0.8, 0.6)
    ax.set_title("(b) Unnamed share by scorecard stratum", fontsize=11, color=INK, loc="left", pad=10)


def main() -> Path:
    d = pd.read_parquet(WORK / "features" / "road_attrs_joined.parquet")
    d["GEOID"] = d.GEOID.astype(str).str.zfill(11)
    shares = d.set_index("GEOID")[["unnamed_share", "aiannh_name"]].rename(columns={"unnamed_share": "share", "aiannh_name": "aiannh"})
    norm = Normalize(vmin=0, vmax=1)

    fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=SURFACE)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.35], height_ratios=[22, 1], left=0.02, right=0.60, top=0.80, bottom=0.08, wspace=0.04, hspace=0.02)
    gs2 = fig.add_gridspec(1, 1, left=0.77, right=0.985, top=0.80, bottom=0.08)
    ax_mav = fig.add_subplot(gs[0, 0]); ax_was = fig.add_subplot(gs[0, 1]); ax_bar = fig.add_subplot(gs2[0, 0])
    ax_cb = fig.add_subplot(gs[1, :])
    for ax in (ax_mav, ax_was, ax_bar, ax_cb):
        ax.set_facecolor(SURFACE)

    for key, ax, tag in (("maverick", ax_mav, "(a) "), ("washita", ax_was, "")):
        region, state, county, title = COUNTIES[key]
        title = tag + title
        tracts, roads = county_layers(region, state, county)
        unnamed_km = d[d.GEOID.str.startswith(state + county)].unnamed_km.sum()
        road_km = d[d.GEOID.str.startswith(state + county)].road_km.sum()
        draw_map(ax, tracts, roads, shares, f"{title}\n{unnamed_km:,.0f} of {road_km:,.0f} drivable km unnamed ({unnamed_km / road_km:.0%})", norm)

    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=norm)
    cb = fig.colorbar(sm, cax=ax_cb, orientation="horizontal")
    cb.set_ticks([0, 0.25, 0.5, 0.75, 1.0]); cb.set_ticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"])
    cb.ax.tick_params(labelsize=8.5, colors=INK2, length=3)
    cb.outline.set_visible(False)
    cb.set_label("Tract fill: unnamed share of drivable road km   ·   thin dark lines: the unnamed segments themselves   ·   white lines: named roads", fontsize=8.5, color=INK2)

    draw_bars(ax_bar, strata_table(d))

    fig.text(0.02, 0.955, "Roads that exist in Overture but have no name — the navigability gap a length-based coverage score cannot see",
             fontsize=13, color=INK, fontweight="bold", ha="left")
    fig.text(0.02, 0.918,"Overture Maps 2026-08-19.0 `transportation/segment` (drivable classes, the challenge's scored road layer): share of road km with `names.primary` null, clipped to Census 2020 tracts. "
             "Strata from the challenge's tract table.", fontsize=9, color=INK2, ha="left")
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=100, facecolor=SURFACE)
    print("wrote", OUT)
    return OUT


if __name__ == "__main__":
    main()
