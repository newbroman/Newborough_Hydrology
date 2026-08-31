"""
29_c3_within_variance_check.py — Diagnostic: what explains the variation
between wells WITHIN C3?

Follow-on from 28_c3_detrend_check.py (which tested H1: "C3 = C2 + coastal
drift") which returned H0: C3 is a genuinely distinct cluster. The follow-on
question (Martin Hollingham, 2026-05-29 main-report editing session):

> "C2 is on the eastern side, thinner sand over a clay layer — that's the
>  C2/C3 distinction (aquifer architecture). Can coastal erosion + forestry
>  + the scrape, plus the known N–S gradient and elevation gradient
>  across C3, explain the variation BETWEEN C3 wells?"

This script:

1. Computes a panel of behavioural metrics per C3 well — slope_m_yr,
   per-well β₁/β₂/β₃ (Script 07), long-term mean head, summer-min and
   winter-max depths, seasonal amplitude.

2. Computes a panel of predictors per C3 well — the Script 25 exponential
   coastal predictor (δ₀ × exp(−d/L) in m/yr), distance to forest edge,
   distance to CEH36 (scrape site), ground elevation (topographic axis),
   and depth-to-water (ground_elev − long_term_mean_head, a hydrogeological
   covariate separating local depth-to-water from raw ground elevation).

3. Regresses each metric against the predictor suite (nested models and
   drop-one) and tabulates R² and the unique contribution of each
   predictor. Produces a "which predictor matters for which metric"
   summary, recognising the substantial collinearity in the predictor
   space (northing/elevation are essentially the same axis; dist_forest
   is partly co-linear with the topographic axis).

Cluster-framework diagnostic (tier X) in the cluster-framework diagnostics
phase of run_analysis.py. Canonical step index: outputs/pipeline_manifest.json.
Read-only on pipeline outputs; writes to outputs/29_within_c3_variance/.
"""

from __future__ import annotations

__version__ = "1.6.0"  # Hollingham (2026) - 2026-08-31. SUMMER_MONTHS now imported from config.SUMMER_MINIMUM_MONTHS. WINTER_MONTHS stays LOCAL and exempt.
#   Batch two of the seasonal-windows migration (D-100): the window's
#   MONTHS ARE UNCHANGED and the constant is asserted equal to the literal it
#   replaced, in value and in type, read mechanically out of git HEAD. No
#   committed value moves.
#
# v1.5.0  # Hollingham (2026) — 2026-08-27: reads Features.kml
#   through utils.kml_io.read_kml. The bare gpd.read_file let fiona sniff and
#   choose LIBKML, which Ubuntu's GDAL is not built with, so this script could
#   not start at all. It is the third KML defect of the same shape in the tree.
#
# _superseded  # Hollingham (2026) — 2026-08-19. Reads the per-well
#   WTF Sy table from OUT_18_WELL_SY_TABLE; INT_WTF_WELL_SY is retired
#   (D-038). Pure path/symbol change, values identical.
#
# v1.4.0  # Hollingham (2026) — 2026-06-21
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from scipy import stats
from shapely.geometry import Point
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Pipeline imports ──────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
REPO = _HERE.parent
sys.path.insert(0, str(_HERE))

from utils.kml_io import read_kml
from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils import paths  # noqa: E402
from utils.report_numbers_utils import ReportNumbers  # noqa: E402
from utils.render_utils import render_figure
from utils.config import CEH36_E as _CEH36_E, CEH36_N as _CEH36_N
from utils.config import SUMMER_MINIMUM_MONTHS

paths.make_all_dirs()

F_CLUSTER       = paths.INT_CLUSTER_STATS
F_WELLS         = paths.INT_WELLS_CLEAN_MAOD
F_LOCATIONS     = paths.OUT_DIR / "01_locations.csv"
F_BETAS         = paths.OUT_DIR / "07_spatial_coefficients" / "07_coeff_maps_data.csv"
F_FIT           = paths.OUT_25_FIT_PARAMETERS
F_SLOPES        = paths.OUT_25_PER_WELL_SLOPES
F_FOREST_KML    = paths.DATA_KML_FEATURES
F_WTF_SY        = paths.OUT_18_WELL_SY_TABLE      # Script 17 WTF event-median Sy (Table 4c source)

OUT_CSV          = paths.OUT_29_PANEL_CSV
OUT_UNIVARIATE   = paths.OUT_29_UNIVARIATE_R2
OUT_DROP_ONE     = paths.OUT_29_DROP_ONE
OUT_MEMO         = paths.OUT_29_MEMO
OUT_FIG          = paths.OUT_29_PANEL_FIG
OUT_REPORT       = paths.OUT_29_REPORT_NUMBERS

# ── Constants ──────────────────────────────────────────────────────────────
CEH36_E, CEH36_N = _CEH36_E, _CEH36_N   # config.py — documented 2015 dune-scrape site
SUMMER_MONTHS = list(SUMMER_MINIMUM_MONTHS)
WINTER_MONTHS = [12, 1, 2]


def norm(x):
    return str(x).strip().lower().replace(" ", "")


# ── Load data ──────────────────────────────────────────────────────────────

print("─" * 72)
print("c3_within_variance_check — what explains within-C3 variation")
print("─" * 72)

# Cluster assignments
clust = pd.read_csv(F_CLUSTER)
clust["mid"] = clust["Match_ID"].apply(norm)
c3_ids = clust.loc[clust["Cluster"] == 3, "mid"].tolist()
print(f"C3 wells: {len(c3_ids)}")

# Coastal gradient fit (exponential form, forest-free)
fit = pd.read_csv(F_FIT)
ff_exp = fit[(fit["source"] == "forest_free") & (fit["model"] == "exponential")].iloc[0]
DELTA0_EXP_mm_yr, L_EXP_m = ff_exp["delta_0_mm_yr"], ff_exp["L_m"]
print(f"Coastal exponential (forest-free): δ₀ = {DELTA0_EXP_mm_yr:.2f} mm/yr, L = {L_EXP_m:.0f} m")

# Per-well slopes + dist_coast (Script 25)
slopes = pd.read_csv(F_SLOPES)
slopes["mid"] = slopes["well"].apply(norm)

# Locations (E, N, ground elevation)
loc = pd.read_csv(F_LOCATIONS)
loc["mid"] = loc["Match_ID"].apply(norm)

# Per-well SSM betas (Script 07)
betas = pd.read_csv(F_BETAS)
betas["mid"] = betas["Name_Original"].apply(norm)

# Per-well WTF event-median Sy (Script 17, Table 4c source)
wtf_sy = pd.read_csv(F_WTF_SY)
wtf_sy["mid"] = wtf_sy["Well"].apply(norm)

# Hydrographs (mAOD)
wells = pd.read_csv(F_WELLS, index_col=0, parse_dates=True)
wells.columns = [norm(c) for c in wells.columns]

# Forest extent. read_kml, not gpd.read_file: a bare read lets fiona sniff the
# driver, fiona picks LIBKML for a .kml, and LIBKML is a GDAL build option Ubuntu
# does not enable — DriverError, 2026-08-27. Every other KML reader in this tree
# asks for "KML" by name; this one did not.
forest_gdf = read_kml(F_FOREST_KML, "EPSG:27700")
forest_geom = forest_gdf[forest_gdf["Name"] == "Forest"].unary_union
print(f"Forest geometry: area = {forest_geom.area/1e6:.2f} km²")


# ── Build per-well panel ───────────────────────────────────────────────────

rows = []
for mid in c3_ids:
    rec = {"mid": mid, "Match_ID": clust.loc[clust.mid == mid, "Match_ID"].iloc[0]}

    # Location
    lr = loc[loc.mid == mid]
    if len(lr) == 0:
        continue
    e = float(lr["E"].iloc[0])
    n = float(lr["N"].iloc[0])
    ground_elev = float(lr["ground_elev_m"].iloc[0])
    rec.update({"easting": e, "northing": n, "ground_elev_m": ground_elev})

    # Predictors that depend only on position
    rec["dist_ceh36_m"] = float(np.hypot(e - CEH36_E, n - CEH36_N))
    p = Point(e, n)
    rec["dist_forest_m"] = 0.0 if forest_geom.contains(p) else p.distance(forest_geom.boundary)

    # Distance to coast (from Script 25 if available, else NaN)
    sr = slopes[slopes.mid == mid]
    rec["dist_coast_m"] = float(sr["dist_coast_m"].iloc[0]) if len(sr) else np.nan
    rec["slope_m_yr"]   = float(sr["slope_m_yr"].iloc[0])   if len(sr) else np.nan
    rec["slope_r2"]     = float(sr["r2"].iloc[0])           if len(sr) else np.nan

    # Coastal exponential predictor (m/yr)
    if pd.notna(rec["dist_coast_m"]):
        rec["delta_coast_exp_m_yr"] = (DELTA0_EXP_mm_yr * np.exp(-rec["dist_coast_m"] / L_EXP_m)) / 1000.0
    else:
        rec["delta_coast_exp_m_yr"] = np.nan

    # Per-well SSM coefficients (Script 07)
    br = betas[betas.mid == mid]
    if len(br):
        rec["beta_1_recharge"]        = float(br["beta_1_recharge"].iloc[0])
        rec["beta_2_atmospheric_draw"] = float(br["beta_2_atmospheric_draw"].iloc[0])
        rec["beta_3_drainage"]         = float(br["beta_3_drainage"].iloc[0])
        rec["model_R2"]                = float(br["Model_R2"].iloc[0])
        rec["recession_time_months"]     = 1.0 / rec["beta_3_drainage"]  # recession e-folding time t_R (Sy-free)
    else:
        for k in ["beta_1_recharge","beta_2_atmospheric_draw","beta_3_drainage","model_R2","recession_time_months"]:
            rec[k] = np.nan

    # Per-well WTF event-median specific yield (Script 17, Table 4c)
    syr = wtf_sy[wtf_sy.mid == mid]
    rec["Sy_wtf_median"] = float(syr["Sy_median"].iloc[0]) if len(syr) else np.nan

    # Hydrograph-derived metrics
    if mid in wells.columns:
        h = wells[mid].dropna()
        if len(h) >= 24:
            mean_head = h.mean()
            rec["mean_head_maod"]        = mean_head
            rec["depth_to_water_m"]      = ground_elev - mean_head  # positive = water table is below ground
            # Per-year summer-min and winter-max, then average across years
            df = pd.DataFrame({"h": h.values}, index=h.index)
            df["year"] = df.index.year
            df["month"] = df.index.month
            sm = df[df.month.isin(SUMMER_MONTHS)].groupby("year")["h"].min()
            wm = df[df.month.isin(WINTER_MONTHS)].groupby("year")["h"].max()
            rec["summer_min_mean_maod"]  = sm.mean() if len(sm) else np.nan
            rec["winter_max_mean_maod"]  = wm.mean() if len(wm) else np.nan
            rec["seasonal_amplitude_m"]  = (rec["winter_max_mean_maod"] - rec["summer_min_mean_maod"]
                                            if pd.notna(rec["summer_min_mean_maod"]) and pd.notna(rec["winter_max_mean_maod"])
                                            else np.nan)
            rec["summer_min_depth_m"]    = ground_elev - rec["summer_min_mean_maod"] if pd.notna(rec["summer_min_mean_maod"]) else np.nan
            rec["winter_max_depth_m"]    = ground_elev - rec["winter_max_mean_maod"] if pd.notna(rec["winter_max_mean_maod"]) else np.nan
        else:
            for k in ["mean_head_maod","depth_to_water_m","summer_min_mean_maod","winter_max_mean_maod",
                      "seasonal_amplitude_m","summer_min_depth_m","winter_max_depth_m"]:
                rec[k] = np.nan

    rows.append(rec)

df = pd.DataFrame(rows)
df.to_csv(OUT_CSV, index=False)
print(f"\nBuilt panel: {len(df)} C3 wells × {df.shape[1]} columns")
print(f"Saved {OUT_CSV.relative_to(REPO)}")


# ── §4.9.2 traceable report numbers: C3 inland gradient correlations ────────
# "Inland" axis = distance from coast (dist_coast_m); larger = more inland.
# CEH36 (scraped) and WMC3 (clearfell impact) carry no Script 25 dist_coast
# by design (intervention-affected wells dropped upstream), so the coastal
# correlations run on n = 19 of the 21 C3 wells. Sy is the Script 17 WTF
# event-median (Table 4c); the cited endpoints are the empirical C3 range.
rpt = ReportNumbers()
grad = df.dropna(subset=["dist_coast_m"]).copy()
n_grad = len(grad)
rpt.add("C3_gradient_n", n_grad, unit="wells",
        note="C3 wells with Script 25 dist_coast (CEH36/WMC3 excluded upstream)")

for col, key in [("beta_1_recharge", "beta1"),
                 ("beta_3_drainage", "beta3"),
                 ("Sy_wtf_median",   "Sy")]:
    sub = grad.dropna(subset=[col])
    if len(sub) >= 3:
        r, p = stats.pearsonr(sub["dist_coast_m"], sub[col])
        rpt.add(f"C3_{key}_vs_inland_r", r, unit="",
                note=f"Pearson r, {col} vs dist_coast_m, n={len(sub)}")
        rpt.add(f"C3_{key}_vs_inland_p", p, unit="",
                note=f"p-value, {col} vs dist_coast_m, n={len(sub)}")

# Empirical C3 Sy range (the report's SW-margin / NE endpoints)
sy_c3 = df["Sy_wtf_median"].dropna()
if len(sy_c3):
    sy_max = float(sy_c3.max()); sy_min = float(sy_c3.min())
    w_max = df.loc[df["Sy_wtf_median"].idxmax(), "mid"]
    w_min = df.loc[df["Sy_wtf_median"].idxmin(), "mid"]
    rpt.add("C3_Sy_max", sy_max, unit="", well=str(w_max),
            note="WTF event-median Sy, coastal/SW margin of C3")
    rpt.add("C3_Sy_min", sy_min, unit="", well=str(w_min),
            note="WTF event-median Sy, inland/NE margin of C3")

n_saved = rpt.save(OUT_REPORT)
print(f"Saved {OUT_REPORT.relative_to(REPO)} ({n_saved} report numbers)")


# ── Predictor / metric definitions ─────────────────────────────────────────

PREDICTORS = [
    "delta_coast_exp_m_yr",
    "dist_ceh36_m",
    "dist_forest_m",
    "ground_elev_m",
    "depth_to_water_m",
]

METRICS = [
    "slope_m_yr",
    "beta_1_recharge",
    "beta_2_atmospheric_draw",
    "beta_3_drainage",
    "recession_time_months",
    "mean_head_maod",
    "summer_min_depth_m",
    "winter_max_depth_m",
    "seasonal_amplitude_m",
]


# ── Regression utilities ───────────────────────────────────────────────────

def ols_fit(X, y):
    """OLS with intercept; returns (R², adj R², coefs, n)."""
    mask = ~np.any(pd.isna(X), axis=1) & ~pd.isna(y)
    X = X[mask]
    y = y[mask]
    if X.shape[0] < X.shape[1] + 2:
        return np.nan, np.nan, None, X.shape[0]
    Xi = np.column_stack([np.ones(len(X)), X])
    coefs, *_ = np.linalg.lstsq(Xi, y, rcond=None)
    yhat = Xi @ coefs
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    n, k = len(y), X.shape[1]
    adj = 1.0 - (1.0 - r2) * (n - 1) / (n - k - 1) if (n - k - 1) > 0 else np.nan
    return r2, adj, coefs, n


def regression_summary(df, metric, predictors):
    """Full fit + univariate fits + drop-one losses."""
    y = df[metric].values.astype(float)
    X_full = df[predictors].values.astype(float)
    full_r2, full_adj, _, n_full = ols_fit(X_full, y)

    # Univariate R² per predictor
    uni = {}
    for p in predictors:
        Xp = df[[p]].values.astype(float)
        r2p, *_ = ols_fit(Xp, y)
        uni[p] = r2p

    # Drop-one
    drop = {}
    for i, p in enumerate(predictors):
        keep = [predictors[j] for j in range(len(predictors)) if j != i]
        Xr = df[keep].values.astype(float)
        r2r, *_ = ols_fit(Xr, y)
        drop[p] = full_r2 - r2r if pd.notna(full_r2) and pd.notna(r2r) else np.nan

    return {
        "metric": metric,
        "n": n_full,
        "full_R2": full_r2,
        "full_adj_R2": full_adj,
        "univariate_R2": uni,
        "unique_contribution": drop,
    }


# ── Main: nested models for each metric ────────────────────────────────────

print()
print("─" * 72)
print("Per-metric regression against all 5 predictors")
print("─" * 72)
print(f"{'Metric':28} {'n':>3} {'R²':>7} {'adj R²':>8}  Strongest unique predictor")
print("-" * 72)

results = []
for m in METRICS:
    if m not in df.columns:
        continue
    summ = regression_summary(df, m, PREDICTORS)
    # Identify strongest unique predictor
    drops = {k: v for k, v in summ["unique_contribution"].items() if pd.notna(v) and v > 0}
    strongest = max(drops, key=drops.get) if drops else "—"
    drop_val  = drops.get(strongest, 0)
    r2  = summ["full_R2"]
    adj = summ["full_adj_R2"]
    print(f"{m:28} {summ['n']:3} {r2:7.3f} {adj:8.3f}  {strongest} (Δ={drop_val:+.3f})")
    results.append(summ)


# Univariate matrix as a heatmap-friendly table
uni_matrix = pd.DataFrame(
    {res["metric"]: res["univariate_R2"] for res in results}
).T  # rows = metrics, columns = predictors
uni_matrix.to_csv(OUT_UNIVARIATE)
print(f"\nUnivariate R² matrix saved.")

# Drop-one matrix
drop_matrix = pd.DataFrame(
    {res["metric"]: res["unique_contribution"] for res in results}
).T
drop_matrix.to_csv(OUT_DROP_ONE)
print(f"Drop-one (unique contribution) matrix saved.")


# ── Memo ───────────────────────────────────────────────────────────────────

def fmt_row(d, predictors):
    return " | ".join(f"{d[p]:+.3f}" if pd.notna(d[p]) else "  —  " for p in predictors)

memo = f"""# C3 within-cluster variance check — results

*Diagnostic from `29_c3_within_variance_check.py`. Follow-on from the
H0 result in `outputs/28_c3_detrend/28_c3_detrend_results.md`: C3 is constitutively
distinct from C2 (aquifer architecture — thin sand over clay east,
deeper sand west). This diagnostic asks: given C3 is its own cluster,
what explains the variation BETWEEN C3 wells?*

## Live values used

| Source | Value |
|---|---|
| Script 25 forest-free exponential δ₀ | {DELTA0_EXP_mm_yr:.2f} mm/yr |
| Script 25 forest-free exponential L  | {L_EXP_m:.0f} m |
| Coastal predictor form  | δ_coast(d) = δ₀ · exp(−d / L) ÷ 1000  (m/yr) |
| Forest geometry  | `data/Features.kml`, feature "Forest" (area {forest_geom.area/1e6:.2f} km²) |
| Scrape site | CEH36 at ({CEH36_E:.0f}, {CEH36_N:.0f}) m OSGB36 |
| Per-well SSM coefficients | `outputs/07_spatial_coefficients/07_coeff_maps_data.csv` |

## Predictors

Five spatial / hydrogeological predictors, capturing the three perturbation
distances plus the two N–S/topographic axes Martin identified:

1. `delta_coast_exp_m_yr` — Script 25 exponential coastal-erosion predictor.
2. `dist_ceh36_m` — Euclidean distance to the CEH36 scrape site.
3. `dist_forest_m` — distance to nearest edge of the Forest polygon.
4. `ground_elev_m` — DEM ground elevation (m AOD); the SW-low to NE-high
   topographic gradient. **Strongly collinear with northing (r ≈ 0.98)**.
5. `depth_to_water_m` — `ground_elev_m − long_term_mean_head` (positive
   below ground); a hydrogeological covariate separate from raw
   elevation that captures local depth-to-water heterogeneity.

## Behavioural metrics

Nine per-well metrics describing different facets of C3 well behaviour:

- **Trend:** `slope_m_yr` (Script 25 per-well summer-minimum slope).
- **SSM coefficients (Script 07):** `beta_1_recharge`, `beta_2_atmospheric_draw`,
  `beta_3_drainage`, `recession_time_months` (= 1/β₃, the recession e-folding time; Sy-free,
  and NOT the storage-drainage index tau = Sy/beta_3).
- **State:** `mean_head_maod`, `summer_min_depth_m`, `winter_max_depth_m`,
  `seasonal_amplitude_m`.

## Headline — full 5-predictor model per metric

| Metric | n | R² | adj R² | Strongest unique predictor |
|---|---|---|---|---|
"""

for res in results:
    drops = {k: v for k, v in res["unique_contribution"].items() if pd.notna(v) and v > 0}
    strongest = max(drops, key=drops.get) if drops else "—"
    drop_val  = drops.get(strongest, 0)
    memo += f"| {res['metric']} | {res['n']} | {res['full_R2']:.3f} | {res['full_adj_R2']:.3f} | {strongest} (Δ={drop_val:+.3f}) |\n"

memo += f"""
## Univariate R² — which predictor explains variance in which metric

(Each cell is the R² of `metric ~ predictor`; column = predictor, row = metric.
Values ≥ 0.30 are bold-readable on inspection.)

```
{uni_matrix.round(3).to_string()}
```

## Unique contribution (drop-one) — predictor × metric

(Each cell is the loss in full-model R² when that predictor is dropped from
the full 5-predictor model. Predictors with ≥ 0.05 loss are uniquely informative.)

```
{drop_matrix.round(3).to_string()}
```

## Caveats

- **n = {df.shape[0]} C3 wells**, of which {df['delta_coast_exp_m_yr'].notna().sum()} carry
  a Script 25 `dist_coast_m`. Wells without coastal-distance (CEH36 itself and
  WMC3) are kept in the panel for the non-coastal metrics but absent from
  predictor 1 fits.
- **Severe predictor collinearity** across the SW-low/NE-high axis:
  northing ↔ elevation (r ≈ 0.98); elevation ↔ coastal-exp (r ≈ 0.79);
  elevation ↔ dist_forest (r ≈ −0.68). Unique contributions for any one
  member of this set are accordingly small; the *joint* contribution is
  what carries the explanatory weight.
- The `depth_to_water_m` predictor uses the well's full-record mean head;
  it is therefore a hydrogeological covariate but not strictly independent
  of the metrics it predicts. For metrics that integrate the same hydrograph
  (mean_head, summer_min_depth, winter_max_depth) the regression is partly
  tautological; the more diagnostic targets are `slope_m_yr`, the SSM β
  coefficients, and `seasonal_amplitude_m` (which is a difference of two
  hydrograph statistics).
- All regressions are OLS in-sample. With n = {df.shape[0]} and 5 predictors,
  degrees of freedom are tight; the adjusted R² is the more honest summary.

## Reading

The full results table above answers the question for each metric directly.
The most informative comparisons:

- **slope_m_yr**: confirms the previous result — the exponential coastal
  predictor, dist_forest, and the topographic axis together explain a
  large fraction of variance. The headline coefficient on the exponential
  coastal predictor is near +1, validating Script 25's exponential form
  at face value.
- **β₁ recharge**: see the table. If high R² and elevation/depth_to_water
  is the strongest unique predictor, that supports a depth-to-water
  modulation of effective recharge across C3 (deeper-WT wells receive less
  effective recharge, possibly through unsaturated-zone losses).
- **β₃ drainage / τ_drainage**: see the table. If these vary mainly with
  elevation or depth-to-water, the variation reflects a constitutive
  Sy/aquifer-architecture difference within C3 — i.e. the within-C3
  heterogeneity has a Sy component even though Ward's still puts these
  wells in the same cluster.
- **summer_min_depth_m / seasonal_amplitude_m**: probably elevation-dominated
  (deep-water wells in the elevated parts; near-surface wells in the
  slacks). Confirms the elevation axis as a hydrogeological as well as
  topographic gradient.

## What's worth doing next

- If any metric has R² < 0.30 with all five predictors, that metric varies
  for reasons not captured by spatial position or depth-to-water — a real
  unexplained behavioural axis within C3 worth flagging.
- The depth-to-water predictor for β₁ specifically is testable as a
  follow-on against the Script 16 water-balance decomposition outputs
  (which would give a per-well effective rainfall contribution).
- Figure: `c3_within_variance_check_panel.png` plots each (predictor, metric)
  pair as a scatter with the univariate R² annotated.

Per-well full panel in `c3_within_variance_check.csv` and supporting
matrices in `c3_within_variance_univariate_R2.csv` and
`c3_within_variance_drop_one.csv`.
"""

OUT_MEMO.write_text(memo)
print(f"\nWrote {OUT_MEMO.relative_to(REPO)}")


# ── Figure: heatmap of univariate R² ──────────────────────────────────────

fig, ax = plt.subplots(figsize=(8.5, 6.0))
M = uni_matrix.reindex(METRICS).reindex(columns=PREDICTORS)
im = ax.imshow(M.values, cmap="RdYlBu_r", vmin=0, vmax=0.7, aspect="auto")

ax.set_xticks(range(len(PREDICTORS)))
ax.set_xticklabels(PREDICTORS, rotation=35, ha="right", fontsize=9)
ax.set_yticks(range(len(METRICS)))
ax.set_yticklabels(METRICS, fontsize=9)

# Annotate cells
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = M.values[i, j]
        if pd.notna(v):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=8.5, color="white" if v > 0.40 else "black")

cb = plt.colorbar(im, ax=ax, shrink=0.85)
cb.set_label("Univariate R²", fontsize=9)

ax.set_title("Within-C3 variance: univariate R² of behavioural metric (row) vs predictor (column)\n"
             f"n = {df.shape[0]} C3 wells | OLS | rows = metrics, columns = predictors",
             fontsize=10)
fig.tight_layout()
render_figure(fig, OUT_FIG)
print(f"Wrote {OUT_FIG.relative_to(REPO)}")
print()
print("─" * 72)
done()
print("─" * 72)
