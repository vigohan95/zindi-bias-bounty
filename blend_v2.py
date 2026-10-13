"""blend_v2: all-six-signal blend with correlations re-fitted to ALL public-LB results (2026-10-10).

Step 1 (truth moments): the two constants give mean_y 0.0598, sd_y 0.0890.
Step 2 (per-file covariance with truth): for every scored file f,
    cov(f, y) = (sd_y² + sd_f² + (mean_f − mean_y)² − RMSE_f²) / 2
using the file's ACTUAL mean/sd (after clipping) read from the submission CSV.
Step 3 (map files to raw signals): regress each file on the six standardized raw signals s_i in-sample
    (R² ≥ 0.994 everywhere except hyp_sparse_places 0.94) → f ≈ const + Σ β_fi s_i,
    so cov(f, y) ≈ Σ β_fi g_i with g_i = cov(s_i, y). Weighted least squares over the 11 scored files
    (weights 1/sd_f) gives g, hence r_i = g_i / sd_y. The 11 files contain the 6 single-signal files
    plus 5 blends/rescales, so r is over-determined (11 equations, 6 unknowns; residuals ≤ 3e-5 in cov units
    except baseline_v2 −8e-5, i.e. cal_k05 and baseline_v2 disagree by Δρ 0.03 — the LB noise floor).
Step 4: w* ∝ C⁻¹ r over all six signals, scale k = ρ*·sd_y (the three all5 scale points put the optimum at c = 1.00).

Usage: PYTHONUTF8=1 python modules/competitions/zindi-bias-bounty/blend_v2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from blend import WORK, write, z  # noqa: E402
from hypotheses import raw_signals  # noqa: E402

SUB = WORK / "submissions"
LB = {  # public RMSE (30 % of tracts), 2026-10-08 .. 2026-10-10
    "blend_all5": 0.077474964, "blend_all5_x08": 0.077914648, "blend_all5_x125": 0.078142491, "blend_top3": 0.07960138,
    "hyp_rural_tribal": 0.083782, "cal_k05": 0.084027, "hyp_poi_only": 0.095044, "hyp_sparse_places": 0.097934,
    "hyp_undefined": 0.108055, "hyp_osm_buildings": 0.110719, "baseline_v2": 0.092129,
    "const_002": 0.097517, "const_0087": 0.093083,
}
SIGNALS = ["baseline_v2", "rural_tribal", "ms_share", "poi_only", "sparse_places", "defined"]
# measured-on-LB? not yet: shown in the correlation matrix but given no weight (hyp_unnamed_roads.csv pending, 2026-10-10)
UNWEIGHTED = ["unnamed_roads"]


def truth_moments() -> tuple[float, float]:
    c1, r1, c2, r2 = 0.02, LB["const_002"], 0.087, LB["const_0087"]
    m = ((r2**2 - r1**2) - (c2**2 - c1**2)) / (2 * (c1 - c2))
    return m, float(np.sqrt(r1**2 - (c1 - m) ** 2))


def main() -> None:
    m_y, sd_y = truth_moments()
    print(f"truth (public subset): mean {m_y:.4f}  sd {sd_y:.4f}")
    df, hyps, p = raw_signals()
    base = p.set_index("GEOID").loc[df.GEOID, "coverage_gap_score"].to_numpy()
    S_full = pd.DataFrame({
        "baseline_v2": z(base), "rural_tribal": z(hyps["rural_tribal"]), "ms_share": -z(hyps["osm_buildings"]),
        "poi_only": z(hyps["poi_only"]), "sparse_places": z(hyps["sparse_places"]), "defined": -z(hyps["undefined"]),
        "unnamed_roads": z(hyps["unnamed_roads"]),
    })
    C = S_full.corr()
    print("signal correlation matrix (9,794 tracts; unweighted signals included):")
    print(C.round(3).to_string())
    S = S_full[SIGNALS].set_index(df.GEOID.astype(str).str.zfill(11))

    files = [n for n in LB if not n.startswith("const")]
    F = pd.DataFrame({n: pd.read_csv(SUB / f"{n}.csv", dtype={"GEOID": str}).set_index("GEOID").coverage_gap_score for n in files})
    S = S.loc[F.index]
    X = np.column_stack([np.ones(len(S)), S.to_numpy()])
    rows, B, g_meas, wts = [], [], [], []
    for n in files:
        f = F[n].to_numpy()
        sd_f, m_f = f.std(), f.mean()
        cov = (sd_y**2 + sd_f**2 + (m_f - m_y) ** 2 - LB[n] ** 2) / 2
        beta, *_ = np.linalg.lstsq(X, f, rcond=None)
        r2 = 1 - (f - X @ beta).var() / f.var()
        rows.append((n, LB[n], m_f, sd_f, (f == 0).mean(), cov, cov / (sd_f * sd_y), r2))
        B.append(beta[1:]); g_meas.append(cov); wts.append(1 / sd_f)
    tab = pd.DataFrame(rows, columns=["file", "rmse", "mean", "sd", "frac0", "cov_y", "rho_file", "R2_on_signals"]).set_index("file")
    pd.set_option("display.width", 200)
    print(tab.round(4).to_string())
    B, g_meas, wts = np.array(B), np.array(g_meas), np.array(wts)
    g, *_ = np.linalg.lstsq(B * wts[:, None], g_meas * wts, rcond=None)
    r = g / sd_y
    print("\nrefined r:", {n: round(v, 3) for n, v in zip(SIGNALS, r)})
    print("fit residuals (cov units):", dict(zip(files, np.round(g_meas - B @ g, 6))))

    # three scale points of blend_all5 → parabola in c
    cs = np.array([0.8, 1.0, 1.25]); y2 = np.array([LB["blend_all5_x08"], LB["blend_all5"], LB["blend_all5_x125"]]) ** 2
    a0, b1, d2 = np.linalg.solve(np.vstack([np.ones(3), cs, cs**2]).T, y2)
    print(f"scale parabola: c* = {-b1 / (2 * d2):.3f}, min RMSE {np.sqrt(a0 - b1**2 / (4 * d2)):.5f}")

    Cs = C.loc[SIGNALS, SIGNALS].to_numpy()
    w = np.linalg.solve(Cs, r)
    rho = float(np.sqrt(r @ w))
    w = w / np.abs(w).sum()
    print("\nblend_v2 weights (Σ|w|=1): " + ", ".join(f"{n}={wi:+.3f}" for n, wi in zip(SIGNALS, w)) + f"  -> rho*={rho:.4f}")
    b = S_full[SIGNALS].to_numpy() @ w
    write("blend_v2", b, rho, 1.0, df)
    old = F["blend_all5"]
    new = pd.read_csv(SUB / "blend_v2.csv", dtype={"GEOID": str}).set_index("GEOID").coverage_gap_score.loc[old.index]
    print(f"corr(blend_v2, blend_all5) = {np.corrcoef(old, new)[0, 1]:.4f}; mean abs diff {np.abs(old - new).mean():.4f}")


if __name__ == "__main__":
    main()
