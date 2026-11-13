"""
15_depth_dependent_pet.py — Explores a depth-dependent PET coefficient using exponential decay.
Purpose: Explore a depth-dependent PET coefficient using exponential decay.

The standard SSM (contemporaneous rainfall, displacement formulation,
HEADLINE_LAG = 0) is:
    Δh_t = β₁·P(t)  −  β₂·PET(t)  −  β₃·h_disp_prev(t)

    where h_disp = DRAINAGE_DATUM + h_depth     (displacement above the config datum)

The modified model replaces the fixed β₂ with a depth-dependent term:
    Δh_t = β₁·P(t)  −  β₂·exp(−d_{t-1}/L_E)·PET(t)  −  β₃·h_disp_prev(t)

Since 1.11.0 (D-332) both are fitted as Model B: a free intercept α is added to each (β₃ bounded below
at MODEL_B_BETA3_MIN), so β₃ drains to the implied base DRAINAGE_DATUM − α/β₃, and α is carried into the
simulation and the loss partition. Model A (no α, at DRAINAGE_DATUM) is the *_model_a sensitivity.

where d_{t-1} = depth below ground surface at the previous timestep:
    d_{t-1} = max(−h_{t-1}, 0)                     (m, always ≥ 0)

No upstand is added: 01_wells_clean.csv already carries the master's
`depth from surface` values, so h is referenced to the ground surface
(GEOMETRY_ARCHITECTURE_SPEC.md §3). Adding the upstand here would measure
d from the pipe top and double-count it.

IMPORTANT: The depth-coupling term d_prev is a PHYSICAL DISTANCE from the
soil surface, used for PET extinction. It is NOT the displacement term.
The displacement h_disp = DRAINAGE_DATUM + h is for the β₃ design matrix
only (hydraulic drainage above a reference base). These are two different
uses of depth and must not be conflated.

L_E is a new free parameter (m): the attenuation length of evaporative draw.
The grid is searched over its RECIPROCAL, inv_L_E = 1/L_E (m⁻¹), because the
no-attenuation null is inv_L_E = 0 and is then exactly representable, where
L_E = ∞ is not. At inv_L_E = 0, exp(−d/L_E) = 1 and the standard SSM is
recovered exactly. As L_E → 0, PET influence vanishes at depth.

The physical interpretation: capillary connectivity between root zone and
saturated zone decays exponentially with depth, so evapotranspiration exerts
diminishing influence as the water table falls.

Fitting strategy:
    - Grid search inv_L_E = 1/L_E over [0, 6] m⁻¹ in steps of 0.05
    - At each inv_L_E, the modified predictor  −exp(−d/L_E)·PET  is linear in β₂,
      so β₁, β₂, β₃ (and α, Model B) are recovered by OLS
    - Best L_E selected by iterative NSE on held-out simulation

Outputs (in outputs/15_depth_dependent_pet/):
    15_01_lambda_profile.png        — NSE vs 1/L_E for each cluster
    15_02_fit_comparison.png        — Observed vs fitted (best model vs SSM)
    15_03_benchmark_table.csv       — Cluster-level comparison table
    15_04_best_params.csv           — Optimal L_E and β coefficients per cluster
"""

__version__ = "1.11.0"  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). Every fit is Model B: an intercept α in
#   the grid-search OLS (fit_at_inv_LE) and in the 1/L_E = 0 baseline (fit_ssm(intercept=True)), with β₃ bounded below at
#   config.MODEL_B_BETA3_MIN as model_utils does; α is carried into the iterative simulation (Δh += α) and the loss
#   partition (drainage = β₃·mean h_disp_prev − α = β₃·mean(h_prev + implied_datum_m)). The headline report numbers
#   carry Model B; the centroid Model A results stay as *_model_a keys. 15_05 gains alpha, implied_datum_m and
#   beta_3_bound_binds; a per-well set whose implied base is not below ground is not identified (counted:
#   ddp_per_well_n_excluded_datum). Identity checks: depth_dependent_pet_check_ssm_full_vs_03 now compares the full-record
#   standard share with the share Script 03's Model B centroid (03_03) gives on the same months, and the old check
#   against 03_12 at the project datum (Model A) moves to *_model_a; ddp_per_well_check_b3_k0_vs_03 compares with
#   03_master_data beta_3_drainage (now Model B), its Model A twin with beta_3_drainage_model_a.
# 1.10.1  # Hollingham (2026) - 2026-11-11. Docstring only: its first line now says what the script does, for pipeline_index.html (T-197 follow-up). No code change.
# 1.10.0  # Hollingham (2026) — 2026-10-27 (D-281; Martin 01:53 "c both", 02:14 "Agree with the 3 tiers").
#   The centroids and the per-well sets are fitted to the level frame in which each dry month carries Script 03's fill
#   (model_utils.apply_dry_fill: its expected level below the bound, centred on its nearest cluster-mate); the centroids
#   are then exactly Script 03's. The depth-dependent model is nonlinear, so the fill is the approximation to censoring.
#   The comparison window is the last DATA_LIMIT calendar months (model_utils.last_calendar_months), not valid rows.
# 1.9.0  # Hollingham (2026) — 2026-10-27 (D-280; Martin 01:21 "Add the depth-dependent model as a
#   third projection", 01:25 "I will follow your recommendations"). New 15_05_ddp_per_well.csv: each reference
#   well's depth-dependent set on the comparison window, kappa fixed at its cluster's, beta refitted, with the
#   identifiability flag; centroid sets on both bases beside it. fit_at_inv_LE also returns the beta_3 p-value
#   and n. Report numbers: ddp_per_well_n_wells, _n_identified, _dnse_median and the identity check
#   ddp_per_well_check_b3_k0_vs_03. No existing value changes.
#
# 1.8.0  # Hollingham (2026) — 2026-10-27 (D-279; Martin 01:19 "the fit window, use both"). The
#   partition is also computed on each centroid's full record with its own kappa grid search:
#   depth_dependent_pet_drainage_share_{ssm,ddp}_full_pct, _shift_full_pts, depth_dependent_pet_best_inv_L_E_full,
#   and the identity check depth_dependent_pet_check_ssm_full_vs_03 against Script 03's 03_12 at the project
#   datum. The 1.7.0 keys stay as the comparison-window set. No existing value changes.
#
# 1.7.0  # Hollingham (2026) — 2026-10-26 (D-279; Martin 11:14 "Can we give script 15 the same
#   treatment"). Emits the drainage share of the modelled mean loss at each centroid under the standard SSM and
#   the depth-dependent fit, and the shift between them (depth_dependent_pet_drainage_share_{ssm,ddp}_pct,
#   _shift_pts), also as two new columns of 15_04_best_params.csv; loss_partition() follows Script 03's definition.
#   DATA_LIMIT now reads config.LCSC_DATA_LIMIT (same value). No existing value changes.
#
# 1.6.0  # Hollingham (2026) — 2026-09-29. T-96: emits
#   depth_dependent_pet_L_E_m per cluster, the 1/e decay depth 1/κ of the
#   best-fit κ (report9 §4.4, "a 1/e decay depth of 0.43 m at C1"). Additive; no
#   existing output changes.
#
# 1.5.0  # Hollingham (2026) — 2026-09-28. T-91: emit the per-cluster
#   best-fit κ (Best_inv_L_E, unrounded, from the in-memory best_params dict)
#   to a new 15_report_numbers.csv, so the Methods Supplement's exp(-2.30·0.5)
#   worked example binds to a committed value. No output value changes.
#
# v1.4.0  # Hollingham (2026) — 2026-08-28 (T-14 E7): the κ=0
#   baseline is fitted by utils.model_utils.fit_ssm instead of a local
#   re-implementation of the same three-column no-intercept design. The
#   grid-search fit stays inline: its β₂ column carries −exp(−κ·d)·PET and
#   is not an SSM. PREDICTION, falsifiable on the next run: SSM_NSE and
#   SSM_OneStep_R2 in 15_03_benchmark_table.csv do not change. If they do,
#   the baseline was NOT the canonical SSM and report8 §3.4.6 rests on a
#   comparison against something else.
#
# _superseded  __version__ = "1.3.0"  # Hollingham (2026) — 2026-08-27: the decay parameter is
#   κ, not λ. report8 §3.4.6 and the symbol register have called it κ throughout;
#   this script called it λ in its docstring, its identifiers and its output
#   columns. λ is spoken for three ways in this project — the drawdown reach
#   √(Kb/β₃), the BACI scraping distance-decay length L_s, and the P_flood
#   rainfall multiplier m_P — which is how the collision arose and why the
#   register displaces it. OUTPUT FILENAMES ARE UNCHANGED: they are identifiers,
#   not symbols, and renaming them would ripple into paths.py, the Methods
#   Supplement output table, the manifest and the archive for no gain.
#
# _superseded  # Hollingham (2026) — 2026-08-26: dropped k=6 "C6 if fitted" comment fossil (T-14 E4)
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec

# ---------------------------------------------------------------------------
# Paths — replicate the structure from paths.py without importing the full
# pipeline, so this script can run standalone.
# ---------------------------------------------------------------------------
from utils.paths import (
    make_all_dirs, DIR_15,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_CLUSTER_STATS,
    INT_LOCATIONS, INT_WELL_ELEVATIONS,
    OUT_15_LAMBDA_PROFILE, OUT_15_FIT_COMPARISON,
    OUT_15_BENCHMARK_TABLE, OUT_15_BEST_PARAMS, OUT_15_REPORT_NUMBERS,
    OUT_03_PARTITION_VS_DATUM, OUT_15_DDP_PER_WELL, INT_MASTER_DATA,
    OUT_03_MECHANISTIC_TABLE,
)
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS, DRAINAGE_DATUM, HEADLINE_LAG, LCSC_DATA_LIMIT
from utils.config import MODEL_B_BETA3_MIN   # 1.11.0 (D-332): Model B's lower bound on β₃

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import render_figure
from utils.model_utils import fit_ssm, apply_dry_fill, last_calendar_months   # T-14 E7; 1.10.0 D-281
from utils.report_numbers_utils import ReportNumbers  # T-91
make_all_dirs()

INT_WELL_ELEV       = INT_WELL_ELEVATIONS   # local alias used throughout script
OUT_LAMBDA_PROFILE  = OUT_15_LAMBDA_PROFILE
OUT_FIT_COMPARISON  = OUT_15_FIT_COMPARISON
OUT_BENCHMARK_TABLE = OUT_15_BENCHMARK_TABLE
OUT_BEST_PARAMS     = OUT_15_BEST_PARAMS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INV_LE_MIN   = 0.0
INV_LE_MAX   = 6.0
INV_LE_STEP  = 0.05
DATA_LIMIT   = LCSC_DATA_LIMIT   # months — the comparison window, from config (1.7.0; was a local 100)

# HEADLINE_LAG imported from config.py (= 0 after bucketing fix).

# CLUSTER_LABELS and CLUSTER_COLOURS imported from utils.config (k=5 partition).

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_well_name(name: str) -> str:
    """Lower-case, strip spaces — matches script 03 / data_utils convention."""
    return str(name).lower().replace(" ", "")


def nse(observed: np.ndarray, simulated: np.ndarray) -> float:
    """Nash-Sutcliffe Efficiency."""
    obs = np.asarray(observed, dtype=float)
    sim = np.asarray(simulated, dtype=float)
    mask = np.isfinite(obs) & np.isfinite(sim)
    obs, sim = obs[mask], sim[mask]
    if len(obs) < 5:
        return np.nan
    ss_res = np.sum((obs - sim) ** 2)
    ss_tot = np.sum((obs - np.mean(obs)) ** 2)
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan


def iterative_simulate(h0: float, P: np.ndarray, PET: np.ndarray,
                       b1: float, b2: float, b3: float,
                       kap: float,
                       drainage_datum: float = DRAINAGE_DATUM,
                       alpha: float = 0.0) -> np.ndarray:
    """
    Simulate water table iteratively from initial condition h0.

    Uses the displacement formulation for β₃ and contemporaneous rainfall
    (HEADLINE_LAG = 0), matching Script 03's headline SSM specification.

    For the standard SSM (kap=0), depth_prev is ignored because exp(0)=1.
    For the depth-dependent model, depth_prev is recalculated at each step
    from the *simulated* h, so the decay feedback is genuine.

    Parameters
    ----------
    h0       : initial water table (negative convention, m from ground surface)
    P        : precipitation array (m) — contemporaneous (HEADLINE_LAG = 0)
    PET      : PET array (m) — contemporaneous
    b1,b2,b3 : OLS coefficients (β₃ fitted against displacement)
    kap      : inverse attenuation length 1/L_E (m⁻¹)
    drainage_datum : reference depth for displacement (default DRAINAGE_DATUM)
    alpha    : 1.11.0 (D-332) Model B's intercept, added to every step; with the β's of a Model B fit
               this is β₃ draining to the implied base DRAINAGE_DATUM − α/β₃. 0 is Model A.
    """
    n = len(P)
    h = np.full(n, np.nan)
    h_t = h0

    for t in range(n):
        # PET extinction depth: physical distance below ground surface (≥ 0)
        # This is NOT the displacement term — it is a separate concept.
        d_t = max(-h_t, 0.0)
        decay = np.exp(-kap * d_t)

        # Displacement above drainage datum for β₃ term
        h_disp_t = drainage_datum + h_t

        delta = b1 * P[t] - b2 * decay * PET[t] - b3 * h_disp_t + alpha
        h_t = h_t + delta
        h[t] = h_t

    return h


def fit_at_inv_LE(df: pd.DataFrame, kap: float,
                  drainage_datum: float = DRAINAGE_DATUM, intercept: bool = True) -> dict:
    """
    Given a cluster centroid DataFrame with columns [h, P_m, PET, h_prev,
    h_disp_prev], fit the depth-dependent SSM by OLS at a fixed 1/L_E.

    Uses contemporaneous rainfall (HEADLINE_LAG = 0) and displacement for β₃,
    matching Script 03.

    1.11.0 (D-332): intercept=True (the default) is Model B: a free constant α, and β₃ bounded below at
    MODEL_B_BETA3_MIN exactly as model_utils.fit_ssm(intercept=True) bounds it (the objective is a convex
    quadratic, so a free estimate under the bound is replaced by the fit with β₃ held on it; its p-value is
    then NaN). intercept=False is Model A (no constant, no bound), the sensitivity.

    Returns dict with b1, b2, b3, alpha (0 under Model A), implied_datum (DRAINAGE_DATUM − α/β₃), r2,
    pvalue_b3, n, bound_binds.
    """
    # PET extinction depth: physical distance below ground (always ≥ 0)
    d_prev = np.maximum(-df["h_prev"].values, 0.0)
    decay  = np.exp(-kap * d_prev)

    X = pd.DataFrame({
        "beta_1_recharge":         df["P"].values,
        "beta_2_atmospheric_draw": -decay * df["PET"].values,
        "beta_3_drainage":         -df["h_disp_prev"].values,
    }, index=df.index)
    if intercept:
        X["const"] = 1.0

    model = sm.OLS(df["Delta_h"], X).fit()
    b3, p3, binds = model.params["beta_3_drainage"], model.pvalues["beta_3_drainage"], False
    if intercept and b3 < MODEL_B_BETA3_MIN:
        y = df["Delta_h"] + MODEL_B_BETA3_MIN * df["h_disp_prev"]   # the drainage term as a known offset
        model = sm.OLS(y, X.drop(columns=["beta_3_drainage"])).fit()
        b3, p3, binds = MODEL_B_BETA3_MIN, np.nan, True
        sst = float(np.sum((df["Delta_h"] - df["Delta_h"].mean()) ** 2))
        r2 = 1.0 - float(np.sum(model.resid ** 2)) / sst if sst > 0 else np.nan
    else:
        r2 = model.rsquared
    alpha = float(model.params["const"]) if intercept else 0.0

    return {
        "b1":  model.params["beta_1_recharge"],
        "b2":  model.params["beta_2_atmospheric_draw"],
        "b3":  b3,
        "alpha": alpha,
        "implied_datum": drainage_datum - alpha / b3 if b3 != 0 else np.nan,
        "r2":  r2,
        "pvalue_b3": p3,   # 1.9.0: for the identifiability rule
        "n":   int(len(df)),
        "bound_binds": binds,
    }


def evaluate_iterative_nse(df: pd.DataFrame, kap: float,
                            b1: float, b2: float, b3: float, alpha: float = 0.0) -> float:
    """
    Run the full iterative simulation and return NSE vs observed centroid.
    """
    h_sim = iterative_simulate(
        h0      = df["h"].iloc[0],
        P       = df["P"].values,
        PET     = df["PET"].values,
        b1=b1, b2=b2, b3=b3, kap=kap, alpha=alpha,
    )
    return nse(df["h"].values, h_sim)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data():
    print("Loading data...")
    wells_clean   = pd.read_csv(INT_WELLS_CLEAN,   index_col=0, parse_dates=True)
    climate       = pd.read_csv(INT_CLIMATE,       index_col=0, parse_dates=True)
    cluster_stats = pd.read_csv(INT_CLUSTER_STATS)
    locations     = pd.read_csv(INT_LOCATIONS)

    # Normalise names
    cluster_stats["Match_ID"] = cluster_stats["Match_ID"].apply(normalize_well_name)
    locations["Match_ID"]     = locations["Match_ID"].apply(normalize_well_name)
    well_col_lookup = {normalize_well_name(c): c for c in wells_clean.columns}

    # Load upstand data if available
    upstand_map = {}
    if INT_WELL_ELEV.exists():
        elev_df = pd.read_csv(INT_WELL_ELEV)
        # Expect columns: Name_norm, Upstand_m (Script 01 output format)
        name_col = "Name_norm" if "Name_norm" in elev_df.columns else (
            "Well" if "Well" in elev_df.columns else elev_df.columns[0]
        )
        if "Upstand_m" in elev_df.columns:
            for _, row in elev_df.iterrows():
                k = normalize_well_name(str(row[name_col]))
                v = row["Upstand_m"]
                if pd.notna(v):
                    upstand_map[k] = float(v)
        print(f"  Loaded upstand data for {len(upstand_map)} wells")
    else:
        warn("01_well_elevations.csv not found — upstand set to 0.05m for all wells")

    return wells_clean, climate, cluster_stats, locations, well_col_lookup, upstand_map


def build_cluster_centroids(wells_clean, cluster_stats, well_col_lookup, upstand_map):
    """
    Build the mean centroid series per cluster.

    No correction is applied: the clean file is already ground-referenced, so
    cluster members share a common datum and average directly. The cluster mean
    upstand is still computed and returned because it is REPORTED as
    `Mean_Upstand_m` in 15_04_best_params.csv — reading the carrier is allowed,
    re-deriving a correction from it is not.

    Returns dict: {cluster_id (int): (centroid_series, mean_upstand)}
    """
    print("Building cluster centroids...")
    cluster_ids = sorted(
        pd.to_numeric(cluster_stats["Cluster"], errors="coerce")
        .dropna().astype(int).unique()
    )

    centroids = {}
    for cid in cluster_ids:
        c_wells = cluster_stats[
            pd.to_numeric(cluster_stats["Cluster"], errors="coerce") == cid
        ]["Match_ID"].astype(str).values

        available_cols = []
        well_upstands  = []
        for w in c_wells:
            col = well_col_lookup.get(normalize_well_name(w))
            if col is not None:
                available_cols.append(col)
                us = upstand_map.get(normalize_well_name(w), 0.05)
                well_upstands.append(us)

        if not available_cols:
            print(f"  C{cid}: no wells found — skipping")
            continue

        centroid = wells_clean[available_cols].mean(axis=1)
        mean_upstand = float(np.mean(well_upstands))   # reported, not applied

        print(f"  C{cid}: {len(available_cols)} wells, mean upstand = {mean_upstand:.3f} m")
        centroids[cid] = (centroid, mean_upstand)

    return centroids


def build_regression_df(centroid: pd.Series, climate: pd.DataFrame,
                        data_limit: int = DATA_LIMIT,
                        drainage_datum: float = DRAINAGE_DATUM) -> pd.DataFrame:
    """Merge centroid with climate and build Δh, h_prev, h_disp_prev, P.

    Builds the design-matrix columns used downstream by fit_standard_ssm
    and fit_at_inv_LE.  Column naming matches model_utils.build_ssm_frame:
    rainfall is stored under "P" rather than "P_lag1" — the canonical
    SSM is contemporaneous (HEADLINE_LAG = 0) so the historical "lag1"
    label was misleading.  The `.shift(HEADLINE_LAG)` is retained for
    forward-compatibility: under HEADLINE_LAG = 0 it is a no-op, and
    if HEADLINE_LAG is ever re-enabled the shift would automatically
    track without code changes.
    """
    df = centroid.to_frame(name="h").join(climate[["P_m", "PET"]], how="inner")
    df["h_prev"]  = df["h"].shift(1)
    df["Delta_h"] = df["h"] - df["h_prev"]

    # Displacement above drainage datum for β₃ predictor
    df["h_disp_prev"] = drainage_datum + df["h_prev"]

    # Rainfall predictor: P_m shifted by HEADLINE_LAG.  HEADLINE_LAG = 0
    # under the canonical (post-bucketing-fix) SSM, so this is a no-op
    # and "P" equals "P_m".  The shift is preserved so any future change
    # to HEADLINE_LAG flows through without code edits.
    df["P"] = df["P_m"].shift(HEADLINE_LAG)

    df = df.dropna(subset=["Delta_h", "P", "PET", "h_prev", "h_disp_prev"])
    # 1.10.0 (D-281): the last data_limit CALENDAR months, as model_utils' window, not the last
    # data_limit valid rows (which reached further back at a well with gaps)
    return last_calendar_months(df, data_limit) if data_limit is not None else df


# ---------------------------------------------------------------------------
# Standard SSM baseline (1/L_E = 0)
# ---------------------------------------------------------------------------

def fit_standard_ssm(df: pd.DataFrame, intercept: bool = True) -> dict | None:
    """The 1/L_E = 0 baseline, fitted by the SHARED SSM routine (T-14 E7).

    This used to build its own three-column no-intercept design and call
    sm.OLS directly. That design was character-for-character the one in
    `model_utils.fit_ssm` — the same P, −PET, −h_disp_prev columns, the same
    no-intercept OLS — so the baseline was a re-implementation of the canonical
    SSM that was BELIEVED identical to Script 03's rather than known to be.

    It matters because `SSM_NSE` and `SSM_OneStep_R2` in 15_03_benchmark_table
    are the reference the depth-coupled model is scored against, and report8
    §3.4.6's decision not to adopt the depth-dependent formulation rests on
    that comparison. A baseline that drifts from the canonical SSM would move
    the reported NSE gains with nothing to catch it.

    Delegating is numerically identical — verified column by column before the
    change — and buys the p-values, standard errors and the insufficient-data
    guard that the inline version had none of.

    NOT done at fit_at_inv_LE (the grid search): its β₂ column carries
    −exp(−d/L_E)·PET, which is a different design matrix and not an SSM. That one
    stays inline, deliberately.

    1.11.0 (D-332): intercept=True (default) is Model B, fit_ssm(intercept=True) with its β₃ bound, and
    α enters the simulation; intercept=False is the Model A sensitivity.
    """
    fit = fit_ssm(pre_built_frame=df, intercept=intercept)
    if fit is None:                        # < SSM_MIN_OBS rows, or OLS failed
        return None
    b1 = fit["beta_1_recharge"]
    b2 = fit["beta_2_atmospheric_draw"]
    b3 = fit["beta_3_drainage"]
    r2 = fit["R2"]
    alpha = float(fit.get("alpha", 0.0)) if intercept else 0.0

    # Iterative NSE — for the standard SSM (1/L_E = 0) the PET decay is exp(0)=1,
    # but displacement is still needed for β₃.
    h_sim = iterative_simulate(
        h0=df["h"].iloc[0], P=df["P"].values, PET=df["PET"].values,
        b1=b1, b2=b2, b3=b3, kap=0.0, alpha=alpha,
    )
    nse_val = nse(df["h"].values, h_sim)

    return {"b1": b1, "b2": b2, "b3": b3, "alpha": alpha, "r2_onestep": r2,
            "nse_iterative": nse_val,
            # Free from the shared routine; the inline OLS reported none of it.
            "se_b1": fit["se_beta_1"], "se_b2": fit["se_beta_2"],
            "se_b3": fit["se_beta_3"], "n_obs": fit["n"]}


# ---------------------------------------------------------------------------
# Grid search
# ---------------------------------------------------------------------------

def grid_search_inv_LE(df: pd.DataFrame, intercept: bool = True) -> pd.DataFrame:
    """
    Search inv_L_E over [INV_LE_MIN, INV_LE_MAX] and record OLS R² and
    iterative NSE at each step.
    """
    inv_LEs = np.arange(INV_LE_MIN, INV_LE_MAX + INV_LE_STEP / 2, INV_LE_STEP)
    records = []

    for kap in inv_LEs:
        fit = fit_at_inv_LE(df, kap, intercept=intercept)
        # Only evaluate iterative NSE if all coefficients are physically
        # plausible (positive β₁, positive β₂, positive β₃)
        if fit["b1"] > 0 and fit["b2"] > 0 and fit["b3"] > 0:
            nse_val = evaluate_iterative_nse(
                df, kap, fit["b1"], fit["b2"], fit["b3"], fit["alpha"]
            )
        else:
            nse_val = np.nan

        records.append({
            "inv_L_E": round(kap, 4),
            "b1": fit["b1"],
            "b2": fit["b2"],
            "b3": fit["b3"],
            "alpha": fit["alpha"],                   # 1.11.0 (D-332); 0 under Model A
            "r2_onestep":    fit["r2"],
            "nse_iterative": nse_val,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

CLUSTER_ORDER = sorted(CLUSTER_LABELS.keys())   # all clusters under k=5


def loss_partition(df: pd.DataFrame, b2: float, b3: float, kap: float, alpha: float = 0.0) -> dict:
    """1.7.0: the drainage share of the modelled mean loss at a centroid, in head units, as Script 03's
    partition defines it (drainage = beta_3 * mean h_disp_prev; atmospheric draw = beta_2 * mean of the
    PET term), with the PET term attenuated by exp(-depth to water / L_E) as in the fit (1/L_E = 0 is
    the standard SSM). Sy-free: a share, not a depth of water.
    1.11.0 (D-332): under Model B the drainage is beta_3 * mean h_disp_prev - alpha, i.e. beta_3 to the
    implied base DRAINAGE_DATUM - alpha/beta_3; alpha = 0 is Model A at DRAINAGE_DATUM."""
    d_prev = np.maximum(-df["h_prev"].values, 0.0)
    drain = float(b3 * df["h_disp_prev"].mean() - alpha)
    draw = float(b2 * np.mean(np.exp(-kap * d_prev) * df["PET"].values))
    tot = drain + draw
    return {"drain": drain, "draw": draw, "share_pct": 100.0 * drain / tot if tot > 0 else np.nan}


def per_well_ddp(wells_clean, climate, cluster_stats, well_col_lookup, inv_LE_by_cluster) -> pd.DataFrame:
    """1.9.0 (D-280): each reference well's depth-dependent set on the comparison window, with
    L_E fixed at its cluster's comparison-window value (a per-well L_E is weakly identified on
    LCSC_DATA_LIMIT months) and beta_1..beta_3 refitted by no-intercept OLS at that L_E. A set is
    identified when beta_1, beta_2 > 0 and beta_3 passes response_identified (Script 48's rule,
    three parameters) -- the rule the Model A / Model B pair already uses. The 1/L_E = 0 refit is
    carried beside it (b3_k0) so it can be checked against Script 03's per-well fit.

    1.11.0 (D-332): the sets are Model B (fit_at_inv_LE's default): alpha, implied_datum_m and
    beta_3_bound_binds are written beside b1..b3, response_identified counts four parameters, and a set
    whose implied base is not below ground is not identified (the rule of Scripts 39 and 44). b3_k0_model_a
    is the Model A refit at 1/L_E = 0, for the Model A identity check."""
    from utils.model_utils import response_identified   # noqa: PLC0415
    rows = []
    for _, r in cluster_stats.iterrows():
        cid = int(pd.to_numeric(r["Cluster"], errors="coerce")) if pd.notna(r["Cluster"]) else None
        col = well_col_lookup.get(normalize_well_name(r["Match_ID"]))
        if col is None or cid not in inv_LE_by_cluster:
            continue
        df = build_regression_df(wells_clean[col], climate)
        if len(df) <= 30:
            continue
        kap = float(inv_LE_by_cluster[cid])
        f = fit_at_inv_LE(df, kap)
        f0 = fit_at_inv_LE(df, 0.0)
        f0a = fit_at_inv_LE(df, 0.0, intercept=False)
        ok_signs = f["b1"] > 0 and f["b2"] > 0 and f["b3"] > 0
        base_ok = bool(f["implied_datum"] > 0)          # D-332: implied base below ground
        ident = bool(ok_signs and base_ok and response_identified(f["b3"], f["pvalue_b3"], f["n"], 4)[0])
        nse_d = evaluate_iterative_nse(df, kap, f["b1"], f["b2"], f["b3"], f["alpha"]) if ok_signs else np.nan
        nse_0 = (evaluate_iterative_nse(df, 0.0, f0["b1"], f0["b2"], f0["b3"], f0["alpha"])
                 if (f0["b1"] > 0 and f0["b2"] > 0 and f0["b3"] > 0) else np.nan)
        rows.append({"level": "well", "basis": "comparison_window", "well": normalize_well_name(r["Match_ID"]),
                     "Cluster": cid, "inv_L_E": kap, "b1": f["b1"], "b2": f["b2"], "b3": f["b3"],
                     "pvalue_b3": f["pvalue_b3"], "n": f["n"], "r2_onestep": f["r2"],
                     "nse_iterative": nse_d, "nse_iterative_k0": nse_0, "b3_k0": f0["b3"],
                     "identified": ident,
                     "alpha": f["alpha"], "implied_datum_m": f["implied_datum"],
                     "beta_3_bound_binds": f["bound_binds"], "implied_base_below_ground": base_ok,
                     "b3_k0_model_a": f0a["b3"]})
    return pd.DataFrame(rows)


def plot_inv_LE_profiles(profiles: dict, ssm_baselines: dict):
    """
    One panel per cluster: NSE vs 1/L_E, with horizontal dashed line at SSM NSE.
    """
    # 2x3 grid accommodates up to 6 clusters; unused panels hidden after the loop.
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), dpi=150)
    axes = axes.flatten()

    for ax, cid in zip(axes, CLUSTER_ORDER):
        if cid not in profiles:
            ax.set_visible(False)
            continue

        prof = profiles[cid]
        ssm  = ssm_baselines[cid]
        if ssm is None:                    # fit_ssm declined this cluster
            continue
        col  = CLUSTER_COLOURS.get(cid, "steelblue")
        label = CLUSTER_LABELS.get(cid, f"C{cid}")

        ax.plot(prof["inv_L_E"], prof["nse_iterative"], color=col, lw=2,
                label="Depth-dependent model")
        ax.axhline(ssm["nse_iterative"], color="black", lw=1.5, ls="--",
                   label=f"Standard SSM (NSE = {ssm['nse_iterative']:.3f})")

        # Mark best 1/L_E
        best_idx = prof["nse_iterative"].idxmax()
        if pd.notna(prof.loc[best_idx, "nse_iterative"]):
            best_kap = prof.loc[best_idx, "inv_L_E"]
            best_nse = prof.loc[best_idx, "nse_iterative"]
            ax.axvline(best_kap, color=col, lw=1, ls=":", alpha=0.7)
            ax.scatter([best_kap], [best_nse], color=col, zorder=5, s=60,
                       label=f"Best 1/L_E = {best_kap:.2f} m⁻¹")

        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_xlabel("1/L_E (m⁻¹)", fontsize=10)
        ax.set_ylabel("Iterative NSE", fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(INV_LE_MIN, INV_LE_MAX)

    # Hide any unused panels (e.g. the 6th in a 2x3 grid with 5 clusters).
    for ax in axes[len(CLUSTER_ORDER):]:
        ax.set_visible(False)

    fig.suptitle("Depth-Dependent PET Model (Model B): NSE vs inverse attenuation length 1/L_E\n"
                 "(dashed = Standard SSM baseline)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    render_figure(plt.gcf(), OUT_LAMBDA_PROFILE)
    plt.close()
    saved(f"{OUT_LAMBDA_PROFILE.name}")


def plot_fit_comparison(regression_dfs: dict, centroids: dict, climate: pd.DataFrame,
                        best_params: dict, ssm_baselines: dict):
    """
    For each cluster: observed vs iterative simulation (standard SSM and best
    depth-dependent model), shown as time series.
    """
    fig = plt.figure(figsize=(17, 10), dpi=150)
    # 2x3 grid; unused cells stay empty.
    gs  = gridspec.GridSpec(2, 3, hspace=0.45, wspace=0.3)

    for i, cid in enumerate(CLUSTER_ORDER):
        if cid not in regression_dfs or cid not in best_params:
            continue

        ax  = fig.add_subplot(gs[i // 3, i % 3])
        df  = regression_dfs[cid]
        bp  = best_params[cid]
        ssm = ssm_baselines[cid]
        if ssm is None:
            continue
        col = CLUSTER_COLOURS.get(cid, "steelblue")
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        # Standard SSM simulation (1/L_E = 0 → exp(0)=1, no PET depth decay)
        h_ssm = iterative_simulate(
            h0=df["h"].iloc[0], P=df["P"].values, PET=df["PET"].values,
            b1=ssm["b1"], b2=ssm["b2"], b3=ssm["b3"], kap=0.0, alpha=ssm["alpha"],
        )

        # Depth-dependent simulation
        h_ddp = iterative_simulate(
            h0=df["h"].iloc[0], P=df["P"].values, PET=df["PET"].values,
            b1=bp["b1"], b2=bp["b2"], b3=bp["b3"],
            kap=bp["best_inv_LE"], alpha=bp["alpha"],
        )

        ax.plot(df.index, df["h"].values, color="black", lw=1.5,
                label="Observed centroid")
        ax.plot(df.index, h_ssm, color="grey", lw=1, ls="--",
                label=f"SSM (NSE={ssm['nse_iterative']:.2f})")
        ax.plot(df.index, h_ddp, color=col, lw=1.5,
                label=f"Depth-dep. 1/L_E={bp['best_inv_LE']:.2f} (NSE={bp['nse_iterative']:.2f})")

        ax.set_title(label, fontsize=10, fontweight="bold")
        ax.set_ylabel("Depth to WT (m)", fontsize=9)
        ax.legend(fontsize=7.5)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    fig.suptitle("Iterative Simulation: Standard SSM vs Depth-Dependent PET Model (both Model B)",
                 fontsize=13, fontweight="bold")
    render_figure(plt.gcf(), OUT_FIT_COMPARISON)
    plt.close()
    saved(f"{OUT_FIT_COMPARISON.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    banner("15", "Depth-Dependent PET Model", version=__version__)
    print("=" * 65)
    print("  15: Depth-Dependent PET Model — Grid Search")
    print("=" * 65)

    # Load
    wells_clean, climate, cluster_stats, locations, well_col_lookup, upstand_map = load_data()
    # 1.10.0 (D-281): centroids and per-well sets are fitted to the level frame in which each dry
    # month carries Script 03's fill (its expected level below the bound). The depth-dependent model
    # is nonlinear, so the exact censored likelihood Script 03 uses does not apply; fitting it to the
    # filled frame is the approximation, and the centroids are then exactly Script 03's.
    wells_clean = apply_dry_fill(wells_clean)
    centroids = build_cluster_centroids(wells_clean, cluster_stats, well_col_lookup, upstand_map)

    # Build regression DataFrames
    regression_dfs = {}
    for cid, (centroid, _mean_upstand) in centroids.items():
        df = build_regression_df(centroid, climate)
        if len(df) > 30:
            regression_dfs[cid] = df

    # Standard SSM baseline
    print("\nFitting standard SSM baselines (1/L_E = 0)...")
    ssm_baselines = {}
    for cid, df in regression_dfs.items():
        ssm = fit_standard_ssm(df)
        ssm_baselines[cid] = ssm
        if ssm is None:
            # fit_ssm returns None below SSM_MIN_OBS or on an OLS failure. The
            # inline version could not express that and would have raised.
            print(f"  C{cid}  SKIPPED — fewer than SSM_MIN_OBS rows, or the "
                  f"OLS did not converge")
            continue
        print(f"  C{cid}  one-step R²={ssm['r2_onestep']:.3f}  "
              f"iterative NSE={ssm['nse_iterative']:.3f}  n={ssm['n_obs']}  α={ssm['alpha']:+.4f}")

    # Grid search
    print(f"\nGrid searching 1/L_E ∈ [{INV_LE_MIN}, {INV_LE_MAX}] m⁻¹ "
          f"step {INV_LE_STEP} ({int((INV_LE_MAX - INV_LE_MIN) / INV_LE_STEP) + 1} values)...")
    profiles = {}
    for cid, df in regression_dfs.items():
        print(f"  C{cid} ...", end=" ", flush=True)
        prof = grid_search_inv_LE(df)
        profiles[cid] = prof
        valid = prof.dropna(subset=["nse_iterative"])
        if not valid.empty:
            best = valid.loc[valid["nse_iterative"].idxmax()]
            print(f"best 1/L_E={best['inv_L_E']:.2f}  NSE={best['nse_iterative']:.3f}")
        else:
            skipped("no valid 1/L_E found")

    # Extract best params per cluster
    print("\nExtracting best parameters...")
    best_params = {}
    for cid, prof in profiles.items():
        valid = prof.dropna(subset=["nse_iterative"])
        if valid.empty:
            continue
        best_row = valid.loc[valid["nse_iterative"].idxmax()]
        _, upstand = centroids[cid]
        best_params[cid] = {
            "best_inv_LE":    best_row["inv_L_E"],
            "b1":             best_row["b1"],
            "b2":             best_row["b2"],
            "b3":             best_row["b3"],
            "alpha":          best_row["alpha"],          # 1.11.0 (D-332)
            "r2_onestep":     best_row["r2_onestep"],
            "nse_iterative":  best_row["nse_iterative"],
            "upstand":        upstand,
        }

    # -----------------------------------------------------------------------
    # Console summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("  BENCHMARK SUMMARY — Depth-Dependent vs Standard SSM")
    print("=" * 65)
    print(f"{'Cluster':<8} {'SSM NSE':>9} {'DDP NSE':>9} {'Δ NSE':>8}  "
          f"{'Best 1/L_E':>10}  {'Note'}")
    print("-" * 65)

    benchmark_rows = []
    for cid in sorted(CLUSTER_LABELS.keys()):
        ssm = ssm_baselines.get(cid)
        bp  = best_params.get(cid)
        if ssm is None:
            continue
        ssm_nse = ssm["nse_iterative"]
        ddp_nse = bp["nse_iterative"] if bp else np.nan
        delta   = ddp_nse - ssm_nse if (bp and pd.notna(ddp_nse)) else np.nan
        best_kap = bp["best_inv_LE"] if bp else np.nan

        # Flag if improvement is marginal (< 0.01) or model performs worse
        if pd.isna(delta):
            note = "no valid fit"
        elif delta > 0.02:
            note = "↑ improvement"
        elif delta > 0.005:
            note = "~ marginal gain"
        elif delta > -0.005:
            note = "~ equivalent"
        else:
            note = "↓ worse"

        print(f"  C{cid:<5}  {ssm_nse:>9.3f}  {ddp_nse:>9.3f}  {delta:>+8.3f}  "
              f"{best_kap:>8.2f}  {note}")

        benchmark_rows.append({
            "Cluster":           f"C{cid}",
            "Label":             CLUSTER_LABELS.get(cid, ""),
            "SSM_Iterative_NSE": round(ssm_nse, 3),
            "DDP_Iterative_NSE": round(ddp_nse, 3) if pd.notna(ddp_nse) else np.nan,
            "Delta_NSE":         round(delta, 3)   if pd.notna(delta) else np.nan,
            "Best_inv_L_E_m-1":   round(best_kap, 2) if pd.notna(best_kap) else np.nan,
            "DDP_b1":            round(bp["b1"], 4) if bp else np.nan,
            "DDP_b2":            round(bp["b2"], 4) if bp else np.nan,
            "DDP_b3":            round(bp["b3"], 4) if bp else np.nan,
            "DDP_alpha":         float(bp["alpha"]) if bp else np.nan,   # 1.11.0 (D-332); unrounded (D-035)
            "SSM_OneStep_R2":    round(ssm["r2_onestep"], 3),
            "DDP_OneStep_R2":    round(bp["r2_onestep"], 3) if bp else np.nan,
        })

    print("=" * 65)

    # -----------------------------------------------------------------------
    # Save outputs
    # -----------------------------------------------------------------------
    print("\nSaving outputs...")

    pd.DataFrame(benchmark_rows).to_csv(OUT_BENCHMARK_TABLE, index=False)
    saved(f"{OUT_BENCHMARK_TABLE.name}")

    params_rows = []
    partitions = {}
    for cid, bp in best_params.items():
        ssm = ssm_baselines.get(cid) or {}
        df_c = regression_dfs[cid]
        p_ssm = loss_partition(df_c, ssm["b2"], ssm["b3"], 0.0, ssm["alpha"]) if ssm else {"share_pct": np.nan}
        p_ddp = loss_partition(df_c, bp["b2"], bp["b3"], bp["best_inv_LE"], bp["alpha"])
        partitions[cid] = (p_ssm, p_ddp)
        params_rows.append({
            "Cluster":        f"C{cid}",
            "Label":          CLUSTER_LABELS.get(cid, ""),
            "Best_inv_L_E":    bp["best_inv_LE"],
            "b1":             bp["b1"],
            "b2":             bp["b2"],
            "b3":             bp["b3"],
            "alpha":          bp["alpha"],                # 1.11.0 (D-332)
            "Mean_Upstand_m": bp["upstand"],
            "R2_OneStep":     bp["r2_onestep"],
            "NSE_Iterative":  bp["nse_iterative"],
            "SSM_b1":         ssm.get("b1", np.nan),
            "SSM_b2":         ssm.get("b2", np.nan),
            "SSM_b3":         ssm.get("b3", np.nan),
            "SSM_alpha":      ssm.get("alpha", np.nan),
            "SSM_NSE":        ssm.get("nse_iterative", np.nan),
            "SSM_Drainage_Share_pct": partitions[cid][0]["share_pct"],
            "DDP_Drainage_Share_pct": partitions[cid][1]["share_pct"],
        })
    pd.DataFrame(params_rows).to_csv(OUT_BEST_PARAMS, index=False)
    saved(f"{OUT_BEST_PARAMS.name}")

    # T-91: bind the per-cluster best-fit decay parameter (unrounded, from
    # the in-memory best_params dict above, before any display rounding)
    # to a committed report number.
    rn = ReportNumbers()
    for cid, bp in best_params.items():
        rn.add("depth_dependent_pet_best_inv_L_E", bp["best_inv_LE"],
               unit="m^-1", well=f"C{cid}",
               note="Best-fit inverse PET attenuation length 1/L_E "
                    "(grid-search argmax NSE_iterative), unrounded; "
                    "15_04_best_params.csv Best_inv_L_E")
    # T-96: the attenuation length L_E itself (report9 §4.4 quotes it for C1) — the
    # 1/e decay depth, which is the reciprocal of the fitted inv_L_E. Not defined at
    # inv_L_E = 0 (no attenuation detected), so no row is written then.
    for cid, bp in best_params.items():
        if pd.notna(bp["best_inv_LE"]) and bp["best_inv_LE"] > 0:
            rn.add("depth_dependent_pet_L_E_m", 1.0 / bp["best_inv_LE"],
                   unit="m", well=f"C{cid}",
                   note="attenuation length of evaporative draw L_E (the 1/e decay "
                        "depth), the reciprocal of the best-fit inverse length "
                        "(depth_dependent_pet_best_inv_L_E), unrounded")
    # 1.8.0 (D-279; Martin 2026-10-27 01:19 "the fit window, use both"): the same partition on each
    # centroid's FULL record, with its own inv_L_E grid search, so the report's water-balance estimators
    # sit on one basis. The full-record standard share must reproduce Script 03's partition at the
    # project datum (03_12_partition_vs_datum.csv) -- an identity check, expected 0.
    # 1.11.0 (D-332): both passes are Model B (the headline keys); the same centroid passes under Model A
    # are the *_model_a keys below.
    full_parts = {}
    full_sets = {}
    full_dfs = {}
    for cid, (centroid, _u) in centroids.items():
        df_f = build_regression_df(centroid, climate, data_limit=len(centroid) + 1)
        ssm_f = fit_standard_ssm(df_f)
        if ssm_f is None or len(df_f) <= 30:
            continue
        prof_f = grid_search_inv_LE(df_f).dropna(subset=["nse_iterative"])
        if prof_f.empty:
            continue
        bf = prof_f.loc[prof_f["nse_iterative"].idxmax()]
        full_dfs[cid] = df_f
        full_parts[cid] = (loss_partition(df_f, ssm_f["b2"], ssm_f["b3"], 0.0, ssm_f["alpha"]),
                           loss_partition(df_f, bf["b2"], bf["b3"], bf["inv_L_E"], bf["alpha"]),
                           float(bf["inv_L_E"]), len(df_f))
        full_sets[cid] = {"inv_L_E": float(bf["inv_L_E"]), "b1": float(bf["b1"]), "b2": float(bf["b2"]),
                          "b3": float(bf["b3"]), "alpha": float(bf["alpha"]),
                          "implied_datum_m": DRAINAGE_DATUM - float(bf["alpha"]) / float(bf["b3"]),
                          "n": len(df_f), "nse_iterative": float(bf["nse_iterative"])}
    # 1.11.0 (D-332): the identity check is against Script 03's Model B centroid (03_03, full record): the
    # share its coefficients give on these same months. The check against 03_12 at the project datum is
    # Model A's (03_12 tests A's datum) and moves to the *_model_a key.
    m03 = pd.read_csv(OUT_03_MECHANISTIC_TABLE).set_index("Cluster") if OUT_03_MECHANISTIC_TABLE.exists() else None
    p03 = None
    if OUT_03_PARTITION_VS_DATUM.exists():
        p03 = pd.read_csv(OUT_03_PARTITION_VS_DATUM)
        p03 = p03[np.isclose(p03["ref_depth"], DRAINAGE_DATUM)].set_index("Cluster")["drainage_share_pct"]
    for cid, (p_ssm, p_ddp, kap_f, n_f) in full_parts.items():
        rn.add("depth_dependent_pet_drainage_share_ssm_full_pct", p_ssm["share_pct"], unit="%", well=f"C{cid}",
               note=f"Model B (D-332): drainage share of the modelled mean loss, standard SSM, centroid on the full "
                    f"record (n = {n_f})")
        rn.add("depth_dependent_pet_drainage_share_ddp_full_pct", p_ddp["share_pct"], unit="%", well=f"C{cid}",
               note="Model B (D-332): the same share with the PET term attenuated by exp(-d / L_E), L_E from a "
                    "full-record grid search")
        rn.add("depth_dependent_pet_drainage_share_shift_full_pts", p_ddp["share_pct"] - p_ssm["share_pct"],
               unit="percentage points", well=f"C{cid}", note="Model B: depth-dependent minus standard, full record")
        rn.add("depth_dependent_pet_best_inv_L_E_full", kap_f, unit="m^-1", well=f"C{cid}",
               note="Model B: best-fit inverse attenuation length 1/L_E on the full record (grid-search argmax "
                    "NSE_iterative)")
        if m03 is not None and cid in m03.index and "alpha" in m03.columns:
            r03 = m03.loc[cid]
            share03 = loss_partition(full_dfs[cid], float(r03["beta_2_atmospheric_draw"]),
                                     float(r03["beta_3_drainage"]), 0.0, float(r03["alpha"]))["share_pct"]
            rn.add("depth_dependent_pet_check_ssm_full_vs_03", p_ssm["share_pct"] - share03,
                   unit="percentage points", well=f"C{cid}",
                   note="identity check (D-332): full-record Model B standard share less the share of Script 03's "
                        "Model B centroid coefficients (03_03) on the same months (expected 0)")

    # 1.11.0 (D-332): Model A, the sensitivity -- the same centroid passes with no intercept, at DRAINAGE_DATUM.
    def _best(prof):
        v = prof.dropna(subset=["nse_iterative"])
        return None if v.empty else v.loc[v["nse_iterative"].idxmax()]
    for cid, df_c in regression_dfs.items():
        ssm_a = fit_standard_ssm(df_c, intercept=False)
        ba = _best(grid_search_inv_LE(df_c, intercept=False))
        if ssm_a is None or ba is None:
            continue
        pa_s = loss_partition(df_c, ssm_a["b2"], ssm_a["b3"], 0.0)
        pa_d = loss_partition(df_c, ba["b2"], ba["b3"], ba["inv_L_E"])
        rn.add("depth_dependent_pet_best_inv_L_E_model_a", ba["inv_L_E"], unit="m^-1", well=f"C{cid}",
               note="Model A at DRAINAGE_DATUM: best-fit 1/L_E on the comparison window")
        if ba["inv_L_E"] > 0:
            rn.add("depth_dependent_pet_L_E_m_model_a", 1.0 / ba["inv_L_E"], unit="m", well=f"C{cid}",
                   note="Model A at DRAINAGE_DATUM: attenuation length L_E on the comparison window")
        rn.add("depth_dependent_pet_drainage_share_ssm_pct_model_a", pa_s["share_pct"], unit="%", well=f"C{cid}",
               note="Model A at DRAINAGE_DATUM: drainage share, standard SSM, centroid on the comparison window")
        rn.add("depth_dependent_pet_drainage_share_ddp_pct_model_a", pa_d["share_pct"], unit="%", well=f"C{cid}",
               note="Model A at DRAINAGE_DATUM: drainage share, depth-dependent, comparison window")
        rn.add("depth_dependent_pet_drainage_share_shift_pts_model_a", pa_d["share_pct"] - pa_s["share_pct"],
               unit="percentage points", well=f"C{cid}", note="Model A: depth-dependent minus standard")
    for cid, df_f in full_dfs.items():
        ssm_a = fit_standard_ssm(df_f, intercept=False)
        ba = _best(grid_search_inv_LE(df_f, intercept=False))
        if ssm_a is None or ba is None:
            continue
        pa_s = loss_partition(df_f, ssm_a["b2"], ssm_a["b3"], 0.0)
        pa_d = loss_partition(df_f, ba["b2"], ba["b3"], ba["inv_L_E"])
        rn.add("depth_dependent_pet_drainage_share_ssm_full_pct_model_a", pa_s["share_pct"], unit="%",
               well=f"C{cid}", note="Model A at DRAINAGE_DATUM: drainage share, standard SSM, full record")
        rn.add("depth_dependent_pet_drainage_share_ddp_full_pct_model_a", pa_d["share_pct"], unit="%",
               well=f"C{cid}", note="Model A at DRAINAGE_DATUM: drainage share, depth-dependent, full record")
        rn.add("depth_dependent_pet_drainage_share_shift_full_pts_model_a", pa_d["share_pct"] - pa_s["share_pct"],
               unit="percentage points", well=f"C{cid}", note="Model A: depth-dependent minus standard, full record")
        rn.add("depth_dependent_pet_best_inv_L_E_full_model_a", float(ba["inv_L_E"]), unit="m^-1", well=f"C{cid}",
               note="Model A at DRAINAGE_DATUM: best-fit 1/L_E on the full record")
        if p03 is not None and cid in p03.index:
            rn.add("depth_dependent_pet_check_ssm_full_vs_03_model_a", pa_s["share_pct"] - float(p03.loc[cid]),
                   unit="percentage points", well=f"C{cid}",
                   note="identity check: full-record Model A standard share less Script 03's partition at the "
                        "project datum (03_12, Model A) (expected 0)")

    # 1.9.0 (D-280): the per-well depth-dependent sets for the third projection form (Scripts 50, 19),
    # with the centroid sets on both bases beside them (extended wells in the viewer take their
    # cluster's full-record centroid, as they do under Model A).
    pw = per_well_ddp(wells_clean, climate, cluster_stats, well_col_lookup,
                      {cid: bp["best_inv_LE"] for cid, bp in best_params.items()})
    cent_rows = []
    for cid, bp in best_params.items():
        cent_rows.append({"level": "centroid", "basis": "comparison_window", "well": "", "Cluster": cid,
                          "inv_L_E": bp["best_inv_LE"], "b1": bp["b1"], "b2": bp["b2"], "b3": bp["b3"],
                          "alpha": bp["alpha"], "implied_datum_m": DRAINAGE_DATUM - bp["alpha"] / bp["b3"],
                          "n": len(regression_dfs[cid]), "nse_iterative": bp["nse_iterative"], "identified": True})
    for cid, fs_ in full_sets.items():
        cent_rows.append({"level": "centroid", "basis": "full_record", "well": "", "Cluster": cid,
                          **fs_, "identified": True})
    ddp_all = pd.concat([pw, pd.DataFrame(cent_rows)], ignore_index=True)
    ddp_all.to_csv(OUT_15_DDP_PER_WELL, index=False)
    saved(f"{OUT_15_DDP_PER_WELL.name} ({len(pw)} wells, {int(pw['identified'].sum()) if len(pw) else 0} identified)")
    if len(pw):
        rn.add("ddp_per_well_n_wells", float(len(pw)), unit="count", note="reference wells fitted under the depth-dependent form (comparison window, cluster L_E)")
        rn.add("ddp_per_well_n_identified", float(pw["identified"].sum()), unit="count",
               note="of which identified (Model B, D-332: beta_1, beta_2 > 0; beta_3 by response_identified, "
                    "4 parameters; implied base below ground)")
        rn.add("ddp_per_well_n_excluded_datum", float((~pw["implied_base_below_ground"].astype(bool)).sum()),
               unit="count", note="reference wells whose Model B depth-dependent set has its implied base "
                                  "DRAINAGE_DATUM - alpha/beta_3 not below ground, left out (D-332)"
               + (" (" + ", ".join(f"{w} {z:+.2f} m" for w, z in zip(
                   pw.loc[~pw["implied_base_below_ground"].astype(bool), "well"],
                   pw.loc[~pw["implied_base_below_ground"].astype(bool), "implied_datum_m"])) + ")"
                  if (~pw["implied_base_below_ground"].astype(bool)).any() else ""))
        rn.add("ddp_per_well_n_bound_binds", float(pw["beta_3_bound_binds"].astype(bool).sum()), unit="count",
               note="reference wells whose Model B depth-dependent beta_3 sits at MODEL_B_BETA3_MIN (D-332)")
        d_nse = (pw["nse_iterative"] - pw["nse_iterative_k0"]).dropna()
        rn.add("ddp_per_well_dnse_median", float(d_nse.median()) if len(d_nse) else np.nan, unit="",
               note="median iterative NSE gain of the depth-dependent set over the 1/L_E = 0 refit, per well")
        if INT_MASTER_DATA.exists():
            m = pd.read_csv(INT_MASTER_DATA)
            name_col = "Match_ID" if "Match_ID" in m.columns else "Name_Original"
            m["_n"] = m[name_col].astype(str).apply(normalize_well_name)
            _mc = ["_n", "beta_3_drainage"] + (["beta_3_drainage_model_a"] if "beta_3_drainage_model_a" in m.columns else [])
            j = pw.merge(m[_mc], left_on="well", right_on="_n", how="inner")
            rn.add("ddp_per_well_check_b3_k0_vs_03", float((j["b3_k0"] - j["beta_3_drainage"]).abs().max()) if len(j) else np.nan,
                   unit="", note="identity check (D-332, Model B): max |beta_3 at 1/L_E = 0 less 03_master_data "
                                 "beta_3_drainage (Model B)| over the wells (expected near 0; Script 03 fits dry "
                                 "months censored, this script fits the filled frame)")
            if "beta_3_drainage_model_a" in j.columns:
                rn.add("ddp_per_well_check_b3_k0_vs_03_model_a",
                       float((j["b3_k0_model_a"] - j["beta_3_drainage_model_a"]).abs().max()) if len(j) else np.nan,
                       unit="", note="identity check, Model A: max |beta_3 at 1/L_E = 0, no intercept, less "
                                     "03_master_data beta_3_drainage_model_a| over the wells")

    # 1.7.0 (D-279): how far letting the PET term weaken with depth to water moves the drainage share of
    # the modelled mean loss, on this script's own basis (centroids on the comparison window), so the
    # documents' caveat that the SSM's drainage share leans high binds to committed values.
    for cid, (p_ssm, p_ddp) in partitions.items():
        rn.add("depth_dependent_pet_drainage_share_ssm_pct", p_ssm["share_pct"], unit="%", well=f"C{cid}",
               note="Model B (D-332): drainage share of the modelled mean loss, standard SSM (1/L_E = 0), this "
                    "script's centroid on the comparison window; head units, Sy-free")
        rn.add("depth_dependent_pet_drainage_share_ddp_pct", p_ddp["share_pct"], unit="%", well=f"C{cid}",
               note="the same share with the PET term attenuated by exp(-d / L_E) at the best-fit L_E")
        rn.add("depth_dependent_pet_drainage_share_shift_pts", p_ddp["share_pct"] - p_ssm["share_pct"],
               unit="percentage points", well=f"C{cid}",
               note="depth-dependent minus standard drainage share; negative = loss moved from drainage to ET")
    rn.save(OUT_15_REPORT_NUMBERS)
    saved(f"{OUT_15_REPORT_NUMBERS.name}")

    # Inverse-attenuation-length profile for all clusters (C1-C5 under the k = 5 partition)
    profile_all = pd.concat(
        {f"C{cid}": prof for cid, prof in profiles.items()},
        names=["Cluster"]
    ).reset_index(level="Cluster")
    profile_all.to_csv(DIR_15 / "15_00_lambda_profiles_raw.csv", index=False)

    # Figures
    print("\nGenerating figures...")
    plot_inv_LE_profiles(profiles, ssm_baselines)
    plot_fit_comparison(regression_dfs, centroids, climate, best_params, ssm_baselines)

    print("\n15 Complete.")


if __name__ == "__main__":
    main()
