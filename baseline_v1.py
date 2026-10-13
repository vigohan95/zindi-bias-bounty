"""Baseline v1: probabilistic expected-value model of the organiser coverage-gap score.

No labels exist (reference layers were removed 2026-09-25), so every component is modelled as
    gap = 1 - min(1, overture / reference)
with `reference` unknown and treated as log-normally uncertain around a proxy that is built ONLY
from the challenge-provided data (Overture attributes + ACS + strata). The prediction is the
expected composite, E[mean of defined components], which is RMSE-optimal under the model.

Components (see NOTES.md for the organiser definitions):
  transport : reference ~ TIGER S1100+S1200 km. Proxy = km of Overture segments (any class) carrying an
              Interstate / US / state route ref + 0.5 * km carrying a county route ref. Overture side =
              km of class in {motorway, trunk, primary, secondary}. Undefined when proxy = 0.
  building  : reference ~ Microsoft US footprint count. Proxy = max(usfs_BuildingCount_sum (strata; USFS
              WRC is built from MS footprints), count of Overture buildings with a Microsoft source).
  poi       : mean(hifld half, cbp half).
              hifld half: per type (fire, ems, school) H = O + K, K ~ Poisson(lambda_t * u_t) extra
                          reference facilities not in Overture; lambda_t from a Poisson regression of
                          Overture counts on strata covariates. Undefined if H = 0.
              cbp half  : reference ~ CBP establishments. Proxy = geometric mean of (k * pop) and
                          (overture_places / rho), k = 0.0243 establishments per capita (national CBP/pop),
                          rho = 2.0 (Overture places per CBP establishment, regional).

Usage: PYTHONUTF8=1 python modules/competitions/zindi-bias-bounty/baseline_v1.py
Writes <work>/pred/baseline_v1.parquet (per-tract expectations + diagnostics).
"""
from __future__ import annotations

import itertools
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, poisson
from sklearn.linear_model import PoissonRegressor

# challenge data folder; override with the ZINDI_WORK environment variable
WORK = Path(os.environ.get("ZINDI_WORK", Path(__file__).resolve().parent / "data"))
REGIONS = ["maricopa-az", "northern-ca", "eastern-ok", "south-central-tx", "eastern-wa"]

# ---- hand-set parameters (documented in NOTES.md) ----
SIG_T = 0.55      # log-normal sd of TIGER length around proxy
SIG_B = 0.20      # log-normal sd of MS count around proxy
SIG_C = 0.50      # log-normal sd of CBP count around proxy
COUNTY_W = 0.5    # share of county-routed km assumed to be TIGER S1200
P_DEF_T_NOROUTE = 0.03   # P(TIGER highway exists | no routed km at all)
K_CBP = 0.0243    # CBP establishments per capita (US ~8.1M / ~333M)
RHO_CBP = 2.0     # Overture places per CBP establishment
# HIFLD: multiplier u_t = expected extra reference facilities per expected Overture facility
U_T = {"fire": 0.45, "ems": 0.30, "school": 0.12}


def exp_gap_lognormal(x: np.ndarray, sig: float) -> np.ndarray:
    """E[max(0, 1 - exp(y))] with y ~ N(x, sig^2);  x = log(overture / reference_proxy)."""
    x = np.asarray(x, dtype=float)
    out = norm.cdf(-x / sig) - np.exp(x + sig**2 / 2) * norm.cdf(-(x + sig**2) / sig)
    return np.clip(out, 0.0, 1.0)


def fit_lambda(df: pd.DataFrame, col: str) -> np.ndarray:
    X = np.column_stack([
        np.log1p(df.pop_total), np.log(df.land_km2.clip(lower=0.01)), df.pct_urban.fillna(0),
        np.log1p(df.housing_units.fillna(0)), np.log1p(df.poi_n),
    ] + [(df.region == r).astype(float) for r in REGIONS[1:]])
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Xs = (X - mu) / sd
    m = PoissonRegressor(alpha=1e-3, max_iter=1000).fit(Xs, df[col])
    return m.predict(Xs)


def expected_ratio_gap(O: np.ndarray, lam_extra: np.ndarray, kmax: int = 40) -> np.ndarray:
    """E[K/(O+K)] for K ~ Poisson(lam_extra), O >= 1."""
    ks = np.arange(kmax + 1)
    pk = poisson.pmf(ks[None, :], lam_extra[:, None])
    g = ks[None, :] / (O[:, None] + ks[None, :])
    return (pk * g).sum(1)


def mean_of_defined(p_def: list[np.ndarray], val: list[np.ndarray]):
    """Components independently defined with prob p_i and value v_i when defined.
    Returns (E[mean over defined | >=1 defined], P(>=1 defined))."""
    n = len(p_def)
    num = np.zeros_like(p_def[0]); pany = np.zeros_like(p_def[0])
    for mask in itertools.product([0, 1], repeat=n):
        if sum(mask) == 0:
            continue
        pr = np.ones_like(p_def[0])
        s = np.zeros_like(p_def[0])
        for i, m in enumerate(mask):
            pr = pr * (p_def[i] if m else 1 - p_def[i])
            if m:
                s = s + val[i]
        num += pr * s / sum(mask)
        pany += pr
    return num / np.where(pany > 0, pany, 1), pany


def main() -> pd.DataFrame:
    df = pd.concat([pd.read_parquet(WORK / "features" / f"{r}.parquet") for r in REGIONS], ignore_index=True)
    df["GEOID"] = df.GEOID.astype(str).str.zfill(11)
    n = len(df)

    # ---------- transport ----------
    routed = df.named_routed_km + df.minor_routed_km
    county = df.named_county_km + df.minor_county_km
    t_proxy = routed + COUNTY_W * county
    p_def_t = np.where(routed > 0, 1.0, np.where(county > 0, COUNTY_W, P_DEF_T_NOROUTE))
    # when defined but no routed km, the proxy is county km (not halved) or a nominal 1 km
    t_ref = np.where(routed > 0, t_proxy, np.where(county > 0, county * COUNTY_W + 0.5, 1.0))
    x_t = np.log(df.named_km.clip(lower=1e-3) / t_ref)
    gap_t = np.where(df.named_km > 0, exp_gap_lognormal(x_t, SIG_T), 1.0)

    # ---------- building ----------
    ms_proxy = np.maximum(df.usfs_BuildingCount_sum.fillna(0), df.bld_has_ms)
    ms_proxy = np.where(ms_proxy > 0, ms_proxy, np.nan)
    p_def_b = np.where(np.isnan(ms_proxy) & (df.bld_n == 0), 0.2, 1.0)
    x_b = np.log(df.bld_n.clip(lower=1e-3) / np.nan_to_num(ms_proxy, nan=1.0))
    gap_b = np.where(df.bld_n > 0, exp_gap_lognormal(x_b, SIG_B), 1.0)

    # ---------- poi: cbp half ----------
    pop = df.pop_total.clip(lower=1)
    x_c = 0.5 * (np.log(df.poi_n.clip(lower=0.5) / (K_CBP * pop)) + np.log(RHO_CBP))
    gap_c = np.where(df.poi_n > 0, exp_gap_lognormal(x_c, SIG_C), 1.0)
    p_def_c = np.where((df.pop_total > 0) | (df.poi_n > 0), 1.0, 0.3)

    # ---------- poi: hifld half ----------
    p_def_h, val_h = [], []
    for t, col in [("fire", "poi_fire"), ("ems", "poi_ems"), ("school", "poi_school")]:
        lam_o = fit_lambda(df, col)
        lam_extra = U_T[t] * lam_o
        O = df[col].to_numpy(dtype=float)
        pdef = np.where(O >= 1, 1.0, 1 - np.exp(-lam_extra))
        g = np.where(O >= 1, expected_ratio_gap(np.maximum(O, 1), lam_extra), 1.0)
        p_def_h.append(pdef); val_h.append(g)
        df[f"lam_{t}"] = lam_o; df[f"pdef_{t}"] = pdef; df[f"gap_{t}"] = g
    gap_h, p_def_hifld = mean_of_defined(p_def_h, val_h)
    gap_p, p_def_p = mean_of_defined([p_def_hifld, p_def_c], [gap_h, gap_c])

    # ---------- composite ----------
    score, p_any = mean_of_defined([p_def_t, p_def_b, p_def_p], [gap_t, gap_b, gap_p])

    out = df[["GEOID", "region", "ur_class", "pop_total", "land_km2", "named_km", "bld_n", "poi_n",
              "poi_fire", "poi_ems", "poi_school"]].copy()
    out["t_proxy_km"] = t_ref; out["p_def_t"] = p_def_t; out["gap_t"] = gap_t
    out["ms_proxy"] = ms_proxy; out["gap_b"] = gap_b
    out["gap_cbp"] = gap_c; out["gap_hifld"] = gap_h; out["p_def_hifld"] = p_def_hifld
    out["gap_p"] = gap_p; out["p_def_p"] = p_def_p
    out["p_any_defined"] = p_any
    out["coverage_gap_score"] = np.clip(score, 0, 1)
    (WORK / "pred").mkdir(exist_ok=True)
    out.to_parquet(WORK / "pred" / "baseline_v1.parquet", index=False)

    pd.set_option("display.width", 220)
    print(out.groupby("region")[["gap_t", "p_def_t", "gap_b", "gap_cbp", "gap_hifld", "p_def_hifld", "gap_p", "coverage_gap_score"]]
          .mean().round(3).to_string())
    print()
    print(out.groupby("region")["coverage_gap_score"].describe(percentiles=[.05, .25, .5, .75, .95]).round(3).to_string())
    print("\nexpected share of tracts with >=1 undefined component (organiser: OK 21%, CA 37%, TX 28%, AZ 55%, WA n/a):")
    und = 1 - (out.p_def_t * out.p_def_p * 1.0)
    print(und.groupby(out.region).mean().round(3).to_string())
    return out


if __name__ == "__main__":
    main()
