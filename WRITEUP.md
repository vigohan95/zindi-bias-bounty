# Bias Bounty Mapping Equity Challenge — Methodology Writeup

*Entry: label-free expected-value model of the Overture coverage-gap score, plus a bias-discovery analysis of road-attribute completeness. All code is open source (Python 3.11), deterministic (no random seeds are consumed; where a library accepts one it is fixed to 0), and runs on a laptop in under 25 minutes after download.*

Public repository: `<REPO_URL>` — `features.py`, `baseline_v1.py`, `make_submission.py`, `hypotheses.py`, `blend.py`, `blend_v2.py`, `bias_discovery.py`, `figure_unnamed_roads.py`, the executed notebook `writeup.ipynb` (Eastern WA end to end in about one minute, plus every Section 7 table), `figures/fig_unnamed_roads.png`, `requirements.txt`, and this file.

---

## 0. Method card

**What this entry is.** Two separable pieces. (1) A *scored submission* that predicts the organiser's `coverage_gap_score` without labels: an expected-value model built only from the challenge data (§3–4), re-centred and blended using public-leaderboard feedback (§5). (2) A *Bias Discovery* finding — unnamed roads — that uses the same data and the same strata but a quantity the score does not measure (§7).

**Pipeline.**

```
data.source.coop bucket (Overture 2026-08-19.0 extracts, ACS, strata)        Zindi public leaderboard
        │                                                                              │
        ▼ features.py (DuckDB spatial; per-tract km / counts / strata)                  │
   features/<region>.parquet ──► baseline_v1.py (expected gap, §4) ──► pred/baseline_v1 │
        │                                 │                                            │
        │                                 ▼ hypotheses.py (6 single-signal priors) ◄── implied corr r_i (§5.1)
        │                                 ▼ blend.py / blend_v2.py (w* ∝ C⁻¹r, §5.2)
        │                                 ▼ make_submission.py (aligned to SampleSubmission.csv, checks §4.5)
        │                            submissions/blend_all5.csv, blend_top3.csv  ──► Zindi (THErq5e9, fhLZv9UF)
        ▼ bias_discovery.py (road km with / without names.primary × strata) ──► §7 tables, figure_unnamed_roads.py
```

**Model assumptions (hand-set; no labels exist).**

| symbol | value | role | basis |
|---|---|---|---|
| σ_T | 0.55 | log-sd of TIGER length around its proxy | regional Overture/proxy ratios spread 0.76–1.91 (§4.1) |
| county weight | 0.5 | share of county-routed km counted as TIGER S1200 | organiser undefined-shares and ratio range (§4.1) |
| P(transport defined \| no route) | 0.03 | | 1–2 % of tracts lack named classes but TIGER is route-based |
| σ_B | 0.20 | log-sd of Microsoft footprint count around proxy | USFS/Overture per-tract ratio spread (§4.2) |
| σ_C | 0.50 | log-sd of CBP count around proxy | CBP is not published at tract level (§4.3) |
| k, ρ | 0.0243, 2.0 | establishments per resident; Overture places per establishment | national CBP/population; regional places per resident |
| u_fire, u_ems, u_school | 0.45, 0.30, 0.12 | extra reference facilities per expected Overture facility | README ordering "fire carries the component, EMS rarely binds"; schools over-counted ≈ 2:1 |
| truth moments | mean 0.060, sd 0.089 | public-subset re-centring target | two constant submissions (§5) |

**What the analysis establishes.**
- The organiser score is first of all a *rurality* signal: a pure strata prior out-scores every Overture-derived ratio on the public leaderboard (§5.1), and the best linear blend of six challenge-data signals reaches an implied correlation ≈ 0.49 with the truth (RMSE 0.0775 vs 0.089 for the best constant).
- In Overture's scored road layer, 24.7 % of drivable road km in the five regions carry no `names.primary` (263,772 of 1,069,751 km), with a steep gradient by density and SVI and a concentration on tribal land and in the Texas border colonias (§7.2); 146 tracts have ≥ 50 % of their km unnamed and 393,307 people live in them, 32.4 % of them on tribal land.
- Unnamed km are disproportionately unreviewed TIGER-era imports (TX: 37.9 % of unnamed km unedited since 2011 vs 5.9 % of named km).

**What it does not establish.**
- *Transcription vs reality.* "Unnamed" is a property of the Overture/OSM transcription (`names.primary` null). It does not by itself show that the road exists on the ground or that it lacks an official name. A spot-check against TxDOT's public-road inventory (§7.4, Maverick County, 30 unnamed + 30 named segments) found that 28 of the 30 unnamed segments are **not public roads at all** (absent from the inventory, which matched 29 of 30 named segments) and only 2 carry a TxDOT name — so in that county the unnamed kilometres are overwhelmingly private ranch/lease tracks or stale import geometry, not public streets missing a name. The operational reading in §7.3 therefore applies with that qualification: the failure is that the road layer is padded with unverifiable geometry around the people who live there, and the small public remainder is unnamed; it is one county and a segment-weighted sample of 30, not a km-weighted five-region estimate.
- *The score itself.* No compliant entry has labels; every "implied correlation" is solved from public RMSEs on a 30 % subset (sampling sd ≈ 0.02 per value), and the scorecard ratios in §6 describe our prior, not the truth.
- *Causality.* The WLS in §7.2 is descriptive (region fixed effects, density, SVI, tribal flag); the tribal coefficient being insignificant after controls means the disparity is carried by where tribal land is, not that tribal status is irrelevant.
- *Individuals.* Strata are tract-level (SVI, any-AIANNH-overlap); statements about "people living in" a tract are ecological.

**Data provenance.** Everything from `https://data.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/` as listed in §2, retrieved 2026-10-08 (Eastern WA added the same day), byte-size-verified against the bucket listing; Overture release 2026-08-19.0; Census 2020 tracts and strata as provided. The reference layers removed on 2026-09-25 were never downloaded (work started 2026-10-08) and no equivalent copy was used. No external dataset is used anywhere, including in §7.

**Limits.** Texas is 61 % of the tracts and dominates every pooled number; two Gulf water tracts have no roads; highways whose identity lives only in `routes[].ref` are counted as unnamed in the all-classes figures (hence the residential-only figures); the figure's county outlines are the union of scored tracts; runtime and versions are in §8.

---

## 1. Problem statement and what changed on 25 September 2026

Each scored tract receives `coverage_gap_score = mean of the defined components` among

| component | Overture side | reference side | undefined when |
|---|---|---|---|
| `transport_gap` | km of `overture-roads` with `class ∈ {motorway, trunk, primary, secondary}` | km of TIGER/Line roads, MTFCC S1100 + S1200 | tract has no TIGER highway |
| `building_gap` | count of `overture-buildings` | count of Microsoft US Building Footprints | tract has no MS footprint |
| `poi_gap` | mean of the HIFLD half (mean over defined types of fire / EMS / schools, matched on `categories.primary`) and the CBP half (all `overture-pois` vs CBP establishments) | USGS National Map facilities; CBP establishments | no facility of any type **and** no establishment |

with every ratio-gap defined as `1 − min(1, overture / reference)` (bucket README, "Format & conventions").

On 2026-09-25 the organisers removed the four reference layers from the data bucket and the rules forbid using them or equivalent copies from elsewhere. **No labels exist for a compliant entry.** This writeup therefore describes (a) a principled *prior* model that predicts the expected score from the remaining data, (b) what we learned from the public leaderboard about that prior, and (c) a bias finding that the automated scorecard cannot see.

## 2. Data sources (retrieved 2026-10-08, all public, no credentials)

Base URL `https://data.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/` (equivalently `s3://us-west-2.opendata.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/`). The S3 listing at the base URL enumerates 327 keys; every downloaded file was byte-size-verified against it.

Per region `R ∈ {maricopa-az, northern-ca, eastern-ok, south-central-tx, eastern-wa}`:

- `reference/R/R-overture-roads.parquet` (Overture 2026-08-19.0, `transportation/segment`, `subtype=road`, classes motorway…unclassified) — the scored road layer.
- `reference/R/R-overture-buildings.parquet` (`buildings/building`), `reference/R/R-overture-pois.parquet` (`places/place`), `reference/R/R-overture-infrastructure.parquet`, `reference/R/R-overture-rail.parquet` (the last two are read but not used by the model).
- `reference/R/R-census-acs-housing.parquet` (ACS 2020-2024 B25001 housing units).
- `reference/R/R-sample-submission.csv` — the authoritative scored tract list per region.
- `strata/R/R-strata-tract-table.parquet` (232 columns: Census 2020 population / urban-rural, CDC SVI 2022, CVI, RUCA 2020, RUCC 2023, NCHS 2013, tribal overlap, USDM / SPI / PMDI drought, EPHT / NASA / CDC heat, USFS Wildfire Risk to Communities 2nd ed., CarbonPlan, MTBS, NIFC, FPA-FOD, USGS fire, NOAA GHCN).
- `strata/R/R-census-tracts.parquet` (tract polygons, `ALAND`, `pop_total`, `ur_class`).
- `boundaries/R-tract-geoids.csv`, `boundaries/all-aois.geojson` (membership check only).
- Official Zindi `SampleSubmission.csv` (9,794 rows; columns `GEOID, coverage_gap_score, region, transport_gap, transport_defined, building_gap, building_defined, poi_gap, poi_defined, poi_gap_fire, poi_defined_fire, poi_gap_ems, poi_defined_ems, poi_gap_schools, poi_defined_schools, poi_gap_cbp, poi_defined_cbp`).

Scored tracts: TX 6,003, AZ 1,593 (incl. NM tract 35023970000), OK 1,192, CA 591, WA 415 = 9,794. No other dataset is used for the scored submission. Section 7 (Bias Discovery) uses only these files too.

## 3. Feature extraction (`features.py`)

DuckDB 1.5.6 with the `spatial` extension, one region at a time, all geometry in OGC:CRS84; lengths and areas by `ST_Length_Spheroid` / `ST_Area_Spheroid` after `ST_FlipCoordinates` (the README's documented axis-order pitfall). Tract polygons come from `R-census-tracts.parquet` restricted to the GEOIDs in `R-sample-submission.csv`; `GEOID` is read as text everywhere.

- **Roads.** Every segment is joined to every tract whose bbox overlaps and which `ST_Intersects`; the length inside the tract is `ST_Length` of `ST_Intersection` (or the full segment when `ST_Within`). Segments are tagged with a class group (`named` = motorway/trunk/primary/secondary, `minor` = tertiary/unclassified/residential) and a route group from `routes[].network`: `I` (`US:I`), `US` (`US:US`), `state` (`US:XX`), `county` (`US:XX:…`), `other` (forest, scenic, historic …), `none`. Output: km per tract for each class, and for each class-group × route-group cell.
- **Buildings.** Centroid-in-tract assignment. Per tract: count, count by primary source (`sources[].property = ''` → Microsoft ML Buildings / OpenStreetMap / Esri Community Maps), count with *any* Microsoft source (`bld_has_ms`; an OSM building that was conflated with a Microsoft footprint keeps the Microsoft record as a second source), footprint area.
- **Places.** Point-in-tract. Per tract: total, `permanently_closed`, confidence ≥ 0.5, and category counts using exactly the organiser's lists: fire = `fire_department`; EMS = `ambulance_and_ems_services`; schools = `elementary_school, middle_school, high_school, school, private_school, public_school`; hospitals (reported, not used).
- **Strata join.** `ALAND`, `pop_total`, `pct_urban`, `ur_class`, housing units, RUCA, RUCC, NCHS, `tribal_any`, SVI, CVI, `usfs_BuildingCount_sum`, `usfs_HUCount_sum`, `carbonplan_buildings`.

Runtime: CA 34 s, WA 28 s, OK 52 s, AZ 81 s, TX 16 min (4.4 M buildings). Output: `work/zindi/bias-bounty/features/<region>.parquet`, 57 columns.

## 4. The model (`baseline_v1.py`): expected gap under log-normal uncertainty

Because the reference quantities are unknown, each is treated as a log-normal random variable centred on a proxy computed from the provided data. For a component with Overture quantity `O`, proxy `P` and log-sd `σ`, the prediction is the **expected gap**

`E[gap] = E[max(0, 1 − e^y)]`, `y ~ N(log(O/P), σ²)` = `Φ(−x/σ) − e^{x+σ²/2} Φ(−(x+σ²)/σ)`, `x = log(O/P)`,

which is the RMSE-optimal point prediction under that belief. Definedness is likewise a probability, and the composite is `E[mean of defined components | ≥ 1 defined]`, computed exactly by enumerating the 2³ definedness patterns (and, inside POI, the 2³ facility types and the 2 halves).

### 4.1 Transport
- Overture side: `named_km` (the four classes, links included — the README states a class filter only).
- Reference proxy: TIGER S1100 + S1200 ≈ km of *any* Overture segment carrying an Interstate / US / state route ref, plus **0.5 ×** km carrying a county route ref. Evidence for this proxy, all from organiser statements: (i) the share of tracts with zero routed km is OK 21 %, CA 28–40 %, AZ 53 %, TX 19–39 % against the organisers' "≥ 1 undefined component" shares of 21 / 37 / 55 / 28 % and "over half of Maricopa has no named highway" (whereas only 1–2 % of tracts lack Overture's named *classes*); (ii) regional ratios `named_km / proxy` are OK 0.76, CA 1.55, TX 1.47, AZ 1.91 against the organisers' stated 0.71–1.59 range (Maricopa's TIGER S1200 evidently also contains unrouted arterials).
- `σ = 0.55`; `P(defined)` = 1 if routed km > 0, 0.5 if only county-routed km, 0.03 otherwise; a tract with no named km but a defined component gets gap 1.

### 4.2 Building
- Overture side: building count.
- Reference proxy: `max(usfs_BuildingCount_sum, bld_has_ms)`. The USFS Wildfire-Risk-to-Communities building count (a provided stratum, derived from Microsoft footprints at 30 m) tracks Overture counts closely (regional ratio 1.05–1.09; per-tract median 1.02; 35–40 % of tracts have Overture < USFS). `carbonplan_buildings` was rejected as a proxy because it equals the Overture count exactly (it is Overture-derived). `bld_has_ms` is a good lower bound in CA/OK/WA (ratio 1.12–1.14) but not in Phoenix (OSM import city, ratio 2.2).
- `σ = 0.20`; defined with probability 1 (0.2 if the tract has no building and no proxy).

### 4.3 POI
- **CBP half.** CBP establishment counts are not published at tract level, so the proxy is the geometric mean of a population scaling (`0.0243 × pop`, the US ratio of CBP establishments to residents) and the Overture count scaled by `ρ = 2.0` places per establishment (the regional Overture places-per-resident of 0.047–0.053 divided by 0.0243). `σ = 0.50`; defined if pop > 0 or places > 0.
- **HIFLD half.** For each type `t`, a Poisson regression (scikit-learn `PoissonRegressor`, α = 10⁻³) of the Overture count on log pop, log land area, urban share, log housing units, log places and region dummies gives `λ_t`. The number of reference facilities *not* in Overture is modelled as `K ~ Poisson(u_t λ_t)` with `u = 0.45` (fire), `0.30` (EMS), `0.12` (schools; Overture over-counts schools ≈ 2:1). If Overture has `O ≥ 1`: `gap_t = E[K/(O+K)]`, defined with probability 1. If `O = 0`: defined with probability `1 − e^{−u_t λ_t}` and gap 1 when defined. The README's note that "fire stations carry the component, EMS rarely binds" motivated the ordering of `u`.
- `poi_gap` = expected mean of the defined halves.

### 4.4 Edge cases
- **Zero-population tracts** (AZ 11, TX 14, mostly industrial/airport/water): CBP proxy uses `pop = 1`, so the CBP half reduces to the Overture-scaled term; HIFLD λ is driven by area/places. Two TX water tracts (48039990000, 48057990000) have *no* Overture roads, buildings or places; since they are on the scored list at least one component is defined and `1 − min(1, 0/ref) = 1`, so the model's 1.0 is exact by construction.
- **Water-dominated / huge rural tracts** (e.g. 40149965400, 941 km²): the transport proxy uses clipped lengths, so tract area never enters a ratio directly; the HIFLD λ uses log area so large tracts get a higher prior of containing a station.
- **No-Overture-feature components** (no named-class km, no building, no place): gap 1 whenever the component is defined; P(defined) falls back to the strata-based priors.
- **Negative or infinite logs**: Overture quantities are floored at 10⁻³ before the log; proxies at zero are set to NaN and replaced by the fallback proxy.
- **GEOID formatting**: zero-padded to 11 characters on every read and write (the Maricopa region is state FIPS 04).

### 4.5 Submission (`make_submission.py`)
Aligns predictions to the official `SampleSubmission.csv` (same 9,794 GEOIDs, same order) and asserts: no NaN, 11-digit GEOIDs, scores in [0,1], per-region counts, region label agreement, GEOID set and order equality. Output columns `GEOID, coverage_gap_score` (component columns can be added with `--components`, every cell filled).

Predicted distribution (mean / sd / p50 / p95): OK 0.106 / 0.063 / 0.093 / 0.240; AZ 0.089 / 0.045 / 0.080 / 0.171; CA 0.088 / 0.041 / 0.080 / 0.171; TX 0.084 / 0.049 / 0.073 / 0.171; WA 0.072 / 0.032 / 0.067 / 0.132. Model-implied share of tracts with ≥ 1 undefined component: OK 22 %, CA 34 %, TX 29 %, AZ 57 %, WA 24 % (organisers: 21 / 37 / 28 / 55 / –).

## 5. What the public leaderboard taught us, and alternative weightings

Public RMSE (30 % of tracts): baseline_v2 0.09213; constant 0.087 → 0.09308; constant 0.02 → 0.09752. Solving `RMSE²(c) = (c − m)² + s²` gives truth mean `m ≈ 0.060`, sd `s ≈ 0.089` on the public subset: the true score is strongly right-skewed (most tracts near zero, a tail of large gaps). From the model's own moments, `corr(pred, truth) ≈ +0.30` and the optimal linear rescale is `≈ 0.54`, giving an expected RMSE ≈ 0.085 (file `cal_k05.csv`; it scored **0.084027** on the public leaderboard, as predicted). The model is therefore informative but biased high and over-dispersed for its signal strength.

Alternative weightings and priors prepared as separate submissions (`hypotheses.py`; each affinely re-centred to mean 0.060, sd 0.045):

| file | hypothesis about where the gap lives |
|---|---|
| `cal_k05`, `cal_k10` | baseline rescaled (k = 0.5, 1.0) around 0.060 |
| `hyp_poi_only` | only the POI component carries gap (Overture ≥ reference for roads and buildings almost everywhere) |
| `hyp_undefined` | gap concentrates in tracts likely to have undefined components (fewer, noisier components; rural) |
| `hyp_osm_buildings` | building mismatch where footprints are OSM-drawn rather than Microsoft-derived |
| `hyp_rural_tribal` | pure strata prior: land area, non-urban share, tribal overlap |
| `hyp_sparse_places` | places per resident, inverted (both POI halves bind together) |

Why we did not simply weight components differently: the organiser composite is an unweighted mean of *defined* components, so any re-weighting must act through the definedness probabilities; the hypotheses above change the *location* of the gap rather than the weights.

### 5.1 Results of the hypothesis runs (public LB, 2026-10-09) and implied correlations

| file | public RMSE | implied corr with truth |
|---|---|---|
| `hyp_rural_tribal` | **0.08378** | +0.37 |
| `cal_k05` (baseline rescaled) | 0.08403 | +0.34 |
| `hyp_poi_only` | 0.09504 | +0.12 |
| `hyp_sparse_places` | 0.09793 | +0.05 |
| `hyp_undefined` | 0.10806 | −0.21 |
| `hyp_osm_buildings` | 0.11072 | −0.29 |

Correlations follow from `RMSE² = var_y + sd_p² − 2 ρ sd_p sd_y` with the truth moments of Section 5 (sampling sd ≈ 0.02 each on the 30 % subset). Three lessons: (i) a pure strata prior (land area, non-urban share, tribal overlap) carries more signal than any Overture-derived ratio — the organiser gap is first of all a rurality signal; (ii) the **Microsoft-sourced building share is positively correlated with the true gap** (+0.29): where no OpenStreetMap mapper has drawn the buildings, places, facilities and road attributes are thin too, so the OSM share is a proxy for mapping-community attention, the complement of the gap (and for the building component itself OSM-drawn areas usually hold *more* footprints than Microsoft, giving ratio > 1 and gap 0); (iii) tracts likely to have an undefined component have *smaller* true gaps (−0.21) — undefined components are dropped from the mean, and the remaining components in those (often suburban, no-highway) tracts are well covered — the opposite of the "fewer components, bigger gap" hypothesis.

### 5.2 Blending the signals (`blend.py`)

With standardized signals `s_i`, their correlation matrix `C` on the 9,794 tracts, and the implied `r_i = corr(s_i, y)`, a blend `b = Σ w_i s_i` has `corr(b, y) = wᵀr / √(wᵀCw)`, maximized by `w* ∝ C⁻¹ r` with `ρ* = √(rᵀ C⁻¹ r)`. The submission is `0.060 + ρ_blend · sd_y · b / sd_b`, clipped to [0, 1]; the expected RMSE is `sd_y √(1 − ρ²)`, and for a scale factor `c` on that optimum, `sd_y √(1 − ρ² (2c − c²))`. Signal correlations are moderate (baseline–rural/tribal 0.31, rural/tribal–Microsoft share 0.47, baseline–POI-only 0.65), so the blend gains over the best single signal.

| file | signals (weights, Σ|w| = 1) | implied ρ | expected RMSE |
|---|---|---|---|
| `blend_all5` | baseline 0.44, rural/tribal 0.13, MS share 0.12, POI-only −0.02, defined 0.29 | 0.50 | 0.0772 |
| `blend_all5_x08` / `_x125` | same, scale × 0.8 / × 1.25 | 0.50 | 0.0777 / 0.0780 |
| `blend_top3` | baseline 0.40, rural/tribal 0.39, MS share 0.21 | 0.45 | 0.0793 |
| `blend_rt_ms` | rural/tribal 0.67, MS share 0.33 (no Overture ratios at all) | 0.39 | 0.0819 |
| `rural_tribal_k037` | rural/tribal alone at its implied-optimal scale | 0.37 | 0.0827 |

The implied ρ of a blend is an in-sample upper bound (five weights fitted to five noisy correlations), so `blend_top3` is the more conservative choice and `blend_all5` the more optimistic one; the scale variants test whether the optimal-scale formula holds once clipping at 0 is applied.

## 6. Bias-scorecard reflection (scorecard returned for `cal_k05`, public RMSE 0.084027)

The scorecard's "disparity ratio" is the mean *predicted* gap in a stratum divided by the mean in its complement. Because our submission is a model of the organiser score and not the score itself, the scorecard measures **what our prior believes**, not where the truth is; it is a check on the model's assumptions, and it should be read together with the RMSE (0.084, against 0.089 for the best constant).

| stratum | disparity ratio | reading |
|---|---|---|
| Rural vs urban | **1.36×** | predicted gaps 36 % larger in rural tracts |
| Tribal vs non-tribal | **1.29×** | 29 % larger on tribal land |
| Wildfire hazard | 1.12× | modestly larger |
| High climate vulnerability (CVI) | 1.05× | similar |
| Winter drought / summer drought / summer heat | 1.02× / 0.99× / 0.97× | similar |
| High social vulnerability (SVI) | 0.94× | similar (slightly lower) |
| High hazard + high vulnerability | 0.96× | similar |

**Why the model says this.** The rural and tribal ratios come almost entirely from two terms: (i) the *definedness* of the transport component — tracts with no routed highway (53 % of Maricopa, 21–29 % elsewhere, overwhelmingly rural) average over fewer components, so the POI term dominates their composite; and (ii) the POI term itself, whose CBP half rises where Overture places per resident are low and whose HIFLD half rises where a rural tract has no `fire_department` place but a high prior of containing a station (λ grows with land area). The building term is nearly flat across strata, and the transport *ratio* term is small everywhere except Eastern Oklahoma (county-routed roads). None of the model inputs is SVI, CVI or a hazard index — the Poisson regressions use population, land area, urban share, housing units and places — so the ≈1.0 ratios on those strata are by construction, not a finding: **the model is deliberately SVI-neutral and hazard-neutral.** The 1.12× wildfire ratio is a by-product of wildfire-hazard tracts being large and rural.

**What the scorecard cannot tell us.** It cannot say whether the *true* rural/tribal disparity is 1.3× or 3×, because it is computed on our predictions; the leaderboard says only that our predictions carry ≈ 0.3 correlation with truth. The re-centring that produced `cal_k05` is affine, so it leaves every ratio ordering unchanged relative to `baseline_v2`. The one place where the scorecard and Section 7 genuinely disagree is SVI: the scorecard sees no vulnerability gradient in the *coverage* metrics, while the unnamed-road analysis finds a strong, significant SVI gradient in *usability* — which is precisely why Section 7 looks outside the five scorecard metrics.

---

## 7. Best Bias Discovery — *Unnamed roads: the navigability gap the scorecard cannot see*

### 7.1 The pattern in one sentence
In Overture's *scored* drivable-road layer, **one quarter of all road kilometres across the five regions carry no name** (`names.primary` is null: 264,000 of 1,070,000 km), and this navigability gap is concentrated in high-SVI, low-density and tribal tracts — a dimension the scorecard cannot see, because the scorecard compares *lengths* and *counts* against reference layers that are themselves name-agnostic (TIGER km, footprint counts, facility counts). A road that exists in Overture but has no name is "covered" at full credit in `transport_gap`, yet it cannot be used to geocode a 911 address, to issue a street-level evacuation order, or to route relief convoys by turn-by-turn directions.

### 7.2 Evidence (all five regions, 9,792 tracts with road km; `bias_discovery.py`)

**Scale.** Unnamed share of drivable road km, km-weighted: Eastern OK 32.6 %, South-Central TX 27.4 %, Northern CA 18.7 %, Maricopa 12.1 %, Eastern WA 8.8 %. Among `residential`-class km alone (the streets people live on): OK 24.7 %, TX 28.1 %, CA 23.9 %, AZ 12.1 %, WA 7.6 %.

**Strata gradients (outside the scorecard's metrics, inside its strata so they are directly comparable):**

| stratum | unnamed share of road km | median tract share |
|---|---|---|
| Urban tracts | 10.9 % | 4.1 % |
| Rural tracts | **31.3 %** | **19.1 %** |
| Non-tribal tracts | 23.0 % | 5.2 % |
| Tribal tracts (any AIANNH overlap) | **31.8 %** | **13.9 %** |
| SVI quartile 1 (least vulnerable) | 14.4 % | 3.8 % |
| SVI quartile 3 / 4 | 28.8 % / 26.2 % | 6.8 % / 5.9 % |
| Wildfire hazard (USFS WHP) quartile 1 → 4 | 8.2 % → 25.6 % | 3.1 % → 9.9 % |

![Unnamed roads: Maverick County TX and Washita County OK choropleths, and unnamed share by stratum](figures/fig_unnamed_roads.png)

*Figure 1 — (a) Maverick County, TX (Eagle Pass and its colonias; Kickapoo (TX) Reservation) and Washita County, OK (Cheyenne and Arapaho OTSA): tract fill is the unnamed share of drivable Overture road km, thin dark lines are the unnamed segments themselves, white lines the named roads. 2,976 of Maverick's 3,786 drivable km (79 %) and 3,027 of Washita's 3,534 km (86 %) carry no name; the ten small city tracts of Eagle Pass sit at 1–15 %, the three large tracts around them at 65–93 %. (b) Km-weighted unnamed share by scorecard stratum across all five regions (n = tracts): rural 31.3 % vs urban 10.9 %, tribal 31.8 % vs non-tribal 23.0 %, SVI quartile 1 → 3 14.4 % → 28.8 %, wildfire-hazard quartile 1 → 4 8.2 % → 25.6 %. Source: `figure_unnamed_roads.py`; data as in §7.4.*

Within rural tracts the *median* tribal tract has 26.9 % of its road km unnamed against 17.0 % for rural non-tribal tracts; in Maricopa, Northern CA and Eastern WA the tribal tracts' residential streets are unnamed 3–7× more often than their non-tribal neighbours (37.8 % vs 9.8 %, 37.1 % vs 23.2 %, 32.1 % vs 4.5 %).

**Controlling for region and density** (weighted least squares, weights = road km, region fixed effects, n = 9,706, R² = 0.55): each 0.1 of SVI adds **+0.86 percentage points** of unnamed share (p < 0.001); each e-fold drop in population density adds +6.3 points (p < 0.001); the tribal flag is not significant once region and density are held fixed (+1.0 pt, p = 0.58) — the tribal disparity is carried by *where* tribal tracts are (Eastern Oklahoma, low density), which is exactly the kind of structural pattern the scorecard's one-dimensional strata hide.

**Who lives there.** 146 tracts have ≥ 50 % of their drivable road km unnamed; **393,000 people** live in them (1.0 % of the five-region population), and **32.4 % of those people live on tribal land, against 7.3 % of the population overall — a 4.4× over-representation.** Of the 55 such tracts in Eastern Oklahoma, 49 are tribal (Cheyenne and Arapaho OTSA, Choctaw, Muscogee, Cherokee areas).

**Named tracts (population ≥ 1,000):**

| GEOID | where | class | pop | road km | unnamed | SVI |
|---|---|---|---|---|---|---|
| 48323950701 | Maverick County TX (east of Eagle Pass; colonias at its western edge, ranch grid beyond) | Urban | 5,574 | 1,797 | **92.6 %** | 0.91 |
| 48323950207 | Kickapoo (TX) Reservation, Maverick County | Urban | 4,614 | 1,250 | 82.0 % | 0.94 |
| 40149965000 | Cheyenne and Arapaho OTSA, Washita County OK | Rural | 1,989 | 897 | 91.3 % | 0.52 |
| 40149965100 | Cheyenne and Arapaho OTSA, Washita County OK | Rural | 3,409 | 641 | 86.6 % | 0.55 |
| 40149965400 | Cheyenne and Arapaho OTSA, Washita County OK | Rural | 1,750 | 1,128 | 86.2 % | 0.52 |
| 48505950402 | Zapata County TX | Rural | 2,567 | 2,285 | 86.1 % | 0.98 |
| 48047950100 | Brooks County TX | Rural | 2,236 | 2,052 | 85.5 % | 0.91 |
| 48271950100 | Kinney County TX | Rural | 3,129 | 3,811 | 86.9 % | 0.71 |
| 48137950300 | Edwards County TX | Rural | 1,422 | 4,697 | 86.3 % | 0.72 |
| 48507950301 | Zavala County TX (Crystal City) | Urban | 1,744 | 1,390 | 83.1 % | 0.99 |

Eight of the ten are in the SVI top decile; the Texas ones are the border-county colonia belt (Maverick, Zapata, Brooks, Zavala), which the heat/drought strata flag as high-exposure.

**What the unnamed roads are.** Overture's `sources[].update_time` shows that unnamed km are disproportionately unreviewed legacy imports: in South-Central Texas 37.9 % of unnamed km has not been edited in OpenStreetMap since 2011 (the TIGER 2007–08 import era) against 5.9 % of named km; Northern CA 36.6 % vs 4.7 %; Eastern OK 18.9 % vs 8.8 %; Maricopa 9.1 % vs 0.5 %. Either these are real streets whose names were never transcribed, or they are stale import geometry that no longer exists — both are failures of the map for the people who live on them, and both are invisible to a length-based coverage metric (stale segments in the four scored classes actually *inflate* Overture's transport coverage).

**Spot-check against a public road inventory (2026-10-13, `spotcheck_txdot.py`, external public data — allowed for this prize, not used by the submission).** For Maverick County, 30 unnamed and 30 named drivable Overture segments inside the scored tracts were drawn deterministically (first 30 by `md5(id)`) and each midpoint was queried against TxDOT's Roadway Inventory (all public roads, state-, county- and city-maintained; ArcGIS feature service, no sign-up) within 30 m. Result: **29 of 30 named segments are in the inventory and carry a TxDOT street name or highway id; only 2 of 30 unnamed segments are** (one is County Road 97, one a trunk link of SL 480 / US 277 whose identity lives in `routes[].ref`); the other 28 — 28 `residential`, median length 730 m, 24 km in total, 99.4 % of the sampled unnamed km — are **absent from the public-road inventory altogether**. So in Maverick County the unnamed kilometres are not public streets whose names were never transcribed; they are overwhelmingly private ranch and lease tracks (TIGER's 2007–08 import included private roads) or geometry that no longer exists. Tract 9507.01's 1,797 km are the ranch grid east of Eagle Pass, not the colonia streets at its western edge. This sharpens rather than weakens the finding: the scored road layer around these communities is padded with unverifiable, unroutable geometry (and, as the control shows, the public streets that do exist are named and inventoried), which a length-based metric rewards. Per-segment results: `spotcheck_txdot_maverick.csv`. Limits: one county, a segment-weighted sample of 30, a 30 m match radius; Oklahoma has no equivalent free statewide service that was checked.

### 7.3 Why it matters for dispatch, evacuation and relief
- **911 / CAD dispatch** geocodes the caller's address against a street centreline file; a street with no name cannot be matched, so the call falls back to coordinates or to the dispatcher's local knowledge. In the Cheyenne-Arapaho tracts and the Eagle Pass colonias above, 8–9 of every 10 road kilometres are in that state.
- **Evacuation orders** (wildfire in Northern CA / Eastern WA, flash flood and heat emergencies in the Texas border counties) are issued by street and zone name and pushed through navigation apps that consume Overture/OSM; residents on unnamed streets get no routable instruction and responders cannot confirm which houses are inside a closure.
- **Relief logistics** (water distribution during the drought/heat seasons the strata encode, FEMA damage assessment) run on address lists; unnamed roads force manual field triage, which is slowest exactly where the SVI is highest.
- The scorecard would rate these tracts as *well covered* for roads: Overture km ≥ TIGER km. The bias is not "missing roads" but "roads that are present but unusable", a different remediation (name conflation from county 911 addressing files, which most Texas and Oklahoma counties publish as open data) from the one the scorecard implies (digitising more centrelines).

### 7.4 Reproducibility and caveats
- Everything above uses only `reference/<region>/<region>-overture-roads.parquet` and `strata/<region>/<region>-strata-tract-table.parquet` / `-census-tracts.parquet`; `PYTHONUTF8=1 python bias_discovery.py` regenerates every table in about 4 minutes (output saved as `bias_discovery_out.md`; per-tract table `features/road_attrs_joined.parquet`). The edit-age figures come from the one-off DuckDB query recorded in `NOTES.md`.
- Surface (`road_surface`) and speed-limit completeness were computed as well (67 % of km lack surface, 50 % of named-class km lack a speed limit) but vary less across strata and are omitted from the headline.
- Caveat: "unnamed" means `names.primary` is null in Overture; a road may carry its name only in `routes[].ref` (highways — excluded by restricting the residential figures) or be genuinely nameless (ranch tracks). The residential-class figures and the edit-age evidence are provided so readers can judge how much of the gap is transcription vs reality; both interpretations lead to the same operational problem.
- External data: none in the tables and figure above. The only external source is the TxDOT Roadway Inventory used for the 60-segment Maverick County spot-check in §7.2 (`spotcheck_txdot.py`, results in `spotcheck_txdot_maverick.csv`); a county 911 address-point conflation for Washita County remains the natural next test.

---

## 8. Reproduction

```bash
# Windows / Git Bash, Python 3.11.9. Versions used: duckdb 1.5.6, pyarrow 25.0.1, pandas 3.0.3, numpy 2.4.6,
# scipy 1.17.1, scikit-learn 1.9.1, shapely 2.2.0, statsmodels 0.15.0, tabulate 0.10.0 (all open source).
# figure: matplotlib 3.11.2, geopandas 1.2.0; notebook execution: nbclient 0.11.0, ipykernel.
pip install -r requirements.txt

# 1. data (≈3.1 GB; no credentials). Edit WORK in the scripts if you use another folder.
B=https://data.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge
mkdir -p data && cd data            # or any folder; point ZINDI_WORK at it
for r in maricopa-az northern-ca eastern-ok south-central-tx eastern-wa; do
  for l in overture-roads overture-buildings overture-pois overture-infrastructure overture-rail census-acs-housing; do
    curl -sSL --retry 5 -C - --create-dirs -o reference/$r/$r-$l.parquet $B/reference/$r/$r-$l.parquet; done
  curl -sSL --retry 5 --create-dirs -o reference/$r/$r-sample-submission.csv $B/reference/$r/$r-sample-submission.csv
  for t in strata-tract-table census-tracts; do
    curl -sSL --retry 5 --create-dirs -o strata/$r/$r-$t.parquet $B/strata/$r/$r-$t.parquet; done
done
# place Zindi's SampleSubmission.csv at official/SampleSubmission.csv

# 2. features, model, submission (deterministic; total ≈ 20 min, dominated by Texas)
cd <repo folder>   # scripts live at the repository root; data folder via ZINDI_WORK (default: ./data next to the scripts)
PYTHONUTF8=1 python features.py
PYTHONUTF8=1 python baseline_v1.py
PYTHONUTF8=1 python make_submission.py baseline_v1 --out baseline_v2
PYTHONUTF8=1 python hypotheses.py          # alternative priors
PYTHONUTF8=1 python bias_discovery.py      # Section 7 tables
PYTHONUTF8=1 python blend.py               # blend_all5 / blend_top3 (the submitted files)
PYTHONUTF8=1 python figure_unnamed_roads.py # Figure 1
```

The Poisson regressions are convex (unique optimum); DuckDB aggregations are order-independent; no sampling is used anywhere, so repeated runs reproduce the CSVs bit-for-bit (floating-point sums over the same inputs in DuckDB's deterministic single-file scans).

### 8.1 Notebook

`writeup.ipynb` (executed outputs kept) reruns the pipeline on the Eastern WA slice — download if missing (175 MB), features, model, submission alignment and checks, the §7 extraction and edit-age query — in about one minute, and reproduces the five-region §7 tables from the cached `bias_discovery.py` output. It inlines the scripts' code, imports only open-source packages, and reports the maximum absolute difference against the cached scripted outputs (0.0 for features and for all 9,794 predictions on 2026-10-13). Run with `jupyter nbconvert --execute --to notebook --inplace writeup.ipynb` or open it in Jupyter; set `ZINDI_WORK` to the data folder (the scripts honour the same variable).

### 8.2 Integrity of the submitted files

The two files selected for the private leaderboard, with their SHA-256 digests as submitted (recomputed in the notebook):

| Zindi submission | file | public RMSE | SHA-256 |
|---|---|---|---|
| THErq5e9 | `blend_all5.csv` (9,794 rows, `GEOID,coverage_gap_score`, LF, no BOM) | 0.077475 | `8af73f9a3a253a1858e2d8487b6d8381f1b8d6e28ea8550d977fb08d6f04d325` |
| fhLZv9UF | `blend_top3.csv` (same format) | 0.079601 | `b2727e963c4eb07a75018c9c0f2b60ce363a55307bf6fe7120d0444425ca01d4` |

Run on a Windows 11 laptop (8 threads), Python 3.11.9, 2026-10-08 to 2026-10-10; full five-region pipeline ≈ 20 minutes after download.

## 9. Licences and attribution
Overture Maps (buildings/transportation ODbL; places/base CDLA-Permissive 2.0, © Overture Maps Foundation and contributors incl. OpenStreetMap), US Census (public domain), CDC SVI, USFS, and other strata as listed in the bucket README. This writeup and code: MIT.
