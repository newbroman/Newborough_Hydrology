"""
03_state_space_model.py
=======================
State-space model (SSM) fits for the Newborough Warren pipeline.

Model (lag-1 headline, displacement formulation, per-cluster centroid and per-well):

    Δh(t) = β₁·P(t−1) + β₂·(−PET(t)) + β₃·(−h_disp_prev(t))

    where h_disp = DRAINAGE_DATUM + h_depth
          (displacement above a reference drainage base, in metres;
           DRAINAGE_DATUM = 3.7 m below ground surface)

The displacement formulation was adopted after a sensitivity analysis found
that the depth-below-surface formulation produces negative β₃ for three of
five clusters (C3, C4, C5), making the drainage term Darcy-inconsistent.
Reformulating as displacement above a 3.7 m drainage base resolves this:
all five clusters produce positive, significant β₃ with comparable or
improved R². See HANDOVER_SCRIPT03_DATUM.md for full rationale.

The lag-1 specification was adopted after the lag diagnostic (03_04) found that
every cluster prefers lag-1 over lag-0, with R² jumping from ~0.3–0.5 to
~0.6–0.7, and β₁ consistently large, significant, and positive. Physical
basis: monthly dipwell readings taken in the first week of month t reflect
recharge from the previous month's rainfall. Confirmed on post-bucketing-fix
data, ruling out a Script 01 artefact.

Physical sign conventions (authoritative, per NEWBOROUGH_HANDOVER.md):
    beta_1 > 0  — rainfall raises the water table              [hard assertion]
    beta_2 > 0  — PET draws the water table down               [hard assertion]
    beta_3 > 0  — drainage increases with head                 [reported, not asserted]

LCSC = 100 / beta_1   (Lumped Catchment Storage Coefficient, %).

Inputs:
    01_locations.csv, 01_climate.csv, 01_wells_clean.csv,
    01_wells_clean_maod.csv, 01_well_elevations.csv, 02_cluster_stats.csv

Outputs (intermediate — outputs/ root):
    03_master_data.csv           — per-well SSM coefficients
    03_regional_averages.csv     — cluster-centroid hydrographs + climate
    03_regional_averages_maod.csv— cluster-centroid maOD hydrographs + climate

Outputs (final — outputs/03_state_space_model/):
    03_01_mechanistic_signatures.png       — 3-panel bar chart with bootstrap CIs
    03_02_cluster_summary_table.csv        — headline per-cluster summary
    03_03_cluster_mechanistic_coefficients.csv — centroid coefficients + p-values
    03_04_lag_diagnostic.csv               — per-cluster fits at lags 0, 1, 2, 3
    03_05_bootstrap_ci.csv                 — B=1000 bootstrap CIs per cluster
    03_06_leave_one_out.csv                — per-cluster leave-one-well-out fits
    03_07_c1_split_window.csv              — C1 pre/post-2018 split-window fits

Phase 1 validation (rebuild priorities):
    * beta_1 > 0 and beta_2 > 0 asserted on every centroid fit (hard-fail).
    * beta_3 reported with no hard assertion (see handover discussion).
    * Bootstrap-of-SSM-fits (B=1000) per cluster, fixed seed, for beta CIs.
    * Leave-one-out by well per cluster, to detect single-well domination.
    * R^2 and p-values reported per cluster.
    * Neutral cluster labels from utils.config.CLUSTER_LABELS throughout.
    * Lag diagnostic (lags 0, 1, 2, 3 months) — Option Y of the rebuild brief.
    * C1 Lake pre/post-2018 split-window diagnostic.
    * Upstand audit — flags wells with upstand > UPSTAND_AUDIT_THRESHOLD.

Rebuild brief: SCRIPT_03_BRIEF.md
Handovers:     NEWBOROUGH_HANDOVER.md, P_FLOOD_HANDOVER_2_.md
"""

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
del _sys, _os

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

from utils.data_utils import normalize_well_name
from utils.paths import (
    make_all_dirs,
    INT_LOCATIONS, INT_CLIMATE, INT_WELLS_CLEAN, INT_WELL_ELEVATIONS,
    INT_CLUSTER_STATS,
    INT_MASTER_DATA, INT_REGIONAL_AVG, INT_CLUSTER_AVG_MAOD,
    INT_WELLS_CLEAN_MAOD, INT_CLUSTER_PEAK_MONTHS,
    OUT_03_SIGNATURES, OUT_03_CLUSTER_SUMMARY, OUT_03_MECHANISTIC_TABLE,
    DIR_03,
    OUT_02_AMP_PER_WELL,
)
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS, DRAINAGE_DATUM


# ==========================================================================
# CONFIGURATION
# ==========================================================================

# Most-recent window for per-well and centroid fits.
# Chosen to match the published analysis and Script 07's LCSC window.
LCSC_DATA_LIMIT = 100

# Minimum observations required for a per-well SSM fit (first-differences).
MIN_OBS_PER_WELL = 30

# Headline rainfall lag (months). The lag diagnostic (03_04) found that every
# cluster's centroid fit prefers lag-1 (R^2 ~ 0.6-0.7 vs 0.3-0.5 at lag-0,
# beta_1 large/significant/positive vs small/borderline/negative at lag-0).
# Physical basis: monthly dipwell readings are taken in the first week of
# month t, so the water level recorded reflects recharge from the previous
# month's rainfall. This is consistent across all five clusters and confirmed
# on post-bucketing-fix data (ruling out a Script 01 artefact).
HEADLINE_LAG = 1

# Bootstrap configuration — well-level resampling within each cluster.
N_BOOTSTRAP = 1000
BOOTSTRAP_SEED = 20260424

# Lag diagnostic — fit the centroid SSM with rainfall at P(t-k) for k in LAGS.
LAGS = (0, 1, 2, 3)

# Upstand audit threshold. CEH2 (~71 cm) is deliberately tall-for-visibility
# in the forest understorey — listed but not a data-quality flag. NW2 (59 cm)
# and t41a (40 cm) are the other two cases above threshold.
UPSTAND_AUDIT_THRESHOLD = 0.30

# C1 Lake split-window diagnostic — separates the record at 2018-01-01.
# Rationale (from amplitude analysis, SCRIPT_03_BRIEF.md): the Lake cluster
# shows a ~15% post-2018 amplitude enlargement in four of its seven wells
# even after climate normalisation. This diagnostic tests whether fitting a
# single beta set across the whole record averages over two regimes.
C1_SPLIT_DATE = pd.Timestamp("2018-01-01")

# Block aggregation — one label per cluster under the current Option-A
# partition. Lake Edge (C1) and Eastern Block (C2 Dune) may be grouped in
# the final report if SSM results confirm they are closely related (as in
# the original analysis). For now they are reported separately so the
# evidence can be evaluated first.
BLOCK_MAP = {
    1: "Lake Edge",
    2: "Eastern Block",
    3: "Western Block",
    4: "Forest",
    5: "Coastal Forest",
}

# Amplitude heterogeneity — hard-coded fallback values from the brief.
# These are only used if Script 02's per-well amplitude output
# (OUT_02_AMP_PER_WELL) does not exist yet. When it does, the values
# are computed from the data.
_AMPLITUDE_FALLBACK = {
    1: (True,  0.85, 1.23),   # C1 Lake — post-2018 amplitude range
    2: (True,  0.78, 1.37),   # C2 Dune
    3: (True,  0.64, 1.27),   # C3 Western Residual
    4: (False, np.nan, np.nan),  # C4 Main Forest — tighter, no flag
    5: (False, np.nan, np.nan),  # C5 Coastal Forest — tighter, no flag
}


def load_amplitude_heterogeneity(cluster_ids: list[int],
                                  cluster_df: pd.DataFrame) -> dict:
    """
    Load per-cluster amplitude heterogeneity from Script 02's per-well
    amplitude output (OUT_02_AMP_PER_WELL) if available. Falls back to
    hard-coded values from SCRIPT_03_BRIEF.md if the file does not exist.

    The amplitude file's 'cluster' column may use a different numbering
    scheme if it came from an older Script 02 run (pre-Option-A). To handle
    this safely, we join on normalised well name via cluster_df (which has the
    authoritative Option-A assignments) rather than trusting the amplitude
    file's cluster column.

    Schema (from 02_clustering.py amplitude descriptor block):
        well, cluster, n_months_pre, n_months_post,
        p90_p10_full, p90_p10_pre2018, p90_p10_post2018,
        p90_p10_pre2018_climnorm, p90_p10_post2018_climnorm,
        std_full, summer_min_post2018

    Returns {cluster_id: (heterogeneous_bool, amp_lo_m, amp_hi_m)}.
    """
    if not OUT_02_AMP_PER_WELL.exists():
        print(f"    [INFO] {OUT_02_AMP_PER_WELL.name} not found \u2014 using "
              "hard-coded amplitude flags from SCRIPT_03_BRIEF.md.")
        return {cid: _AMPLITUDE_FALLBACK.get(cid, (False, np.nan, np.nan))
                for cid in cluster_ids}

    try:
        amp_df = pd.read_csv(OUT_02_AMP_PER_WELL)

        amp_col = "p90_p10_post2018"
        if amp_col not in amp_df.columns:
            print(f"    [WARNING] {OUT_02_AMP_PER_WELL.name} found but no "
                  f"'{amp_col}' column \u2014 using fallback values.")
            return {cid: _AMPLITUDE_FALLBACK.get(cid, (False, np.nan, np.nan))
                    for cid in cluster_ids}

        # Join on well name so we use Option-A cluster IDs from cluster_df,
        # not the possibly-stale IDs in the amplitude file.
        amp_df["_well_norm"] = amp_df["well"].apply(
            lambda w: normalize_well_name(str(w))
        )
        cdf = cluster_df[["Match_ID", "Cluster"]].copy()
        cdf["_well_norm"] = cdf["Match_ID"].apply(normalize_well_name)
        merged = amp_df.merge(cdf[["_well_norm", "Cluster"]],
                               on="_well_norm", how="left",
                               suffixes=("_amp", ""))

        result = {}
        for cid in cluster_ids:
            sub = merged[pd.to_numeric(merged["Cluster"],
                                        errors="coerce") == cid][amp_col]
            sub = sub.dropna()
            if len(sub) >= 2:
                lo, hi = float(sub.min()), float(sub.max())
                ratio = hi / lo if lo > 0 else np.inf
                result[cid] = (ratio > 1.5, lo, hi)
            else:
                result[cid] = (False, np.nan, np.nan)

        print(f"    Loaded amplitude heterogeneity from "
              f"{OUT_02_AMP_PER_WELL.name} ({len(merged)} wells matched).")
        return result

    except Exception as exc:
        print(f"    [WARNING] Could not read {OUT_02_AMP_PER_WELL.name}: "
              f"{exc} \u2014 using fallback values.")
        return {cid: _AMPLITUDE_FALLBACK.get(cid, (False, np.nan, np.nan))
                for cid in cluster_ids}


# ==========================================================================
# CORE FIT — THE SIGN CONVENTION LIVES HERE
# ==========================================================================

def fit_ssm(h_series: pd.Series, climate: pd.DataFrame,
            lag: int = 0, window: int | None = LCSC_DATA_LIMIT,
            drainage_datum: float = DRAINAGE_DATUM,
            ) -> dict | None:
    """
    Fit the state-space model to a single water-level series.

    Model (displacement formulation):
        Δh(t) = β₁·P(t−lag) + β₂·(−PET(t)) + β₃·(−h_disp_prev(t))
        (no-intercept OLS)

    where h_disp = drainage_datum + h_depth (displacement above a reference
    drainage base). Δh is computed from h_depth directly (the datum constant
    cancels in first differences). Only the β₃ predictor column uses h_disp.

    Sign convention:
        β₁ > 0  — rainfall raises water table              [hard assertion]
        β₂ > 0  — PET draws water table down                [hard assertion]
        β₃ > 0  — drainage increases with head above datum  [soft assertion]

    Parameters
    ----------
    h_series : pd.Series of water level in ground-surface depth convention
               (negative = below ground). For per-well fits, the caller must
               apply upstand correction before passing the series so that the
               displacement datum is relative to ground, not pipe top.
    climate  : DataFrame with columns 'P_m' (rainfall, m/month) and 'PET'
               (PET, m/month), indexed by datetime.
    lag      : integer month lag applied to rainfall. lag=1 is the headline.
    window   : keep only the most recent `window` observations after alignment.
               None disables windowing and fits on the full record.
    drainage_datum : reference depth (m below ground surface) for the
               displacement. Default from config.DRAINAGE_DATUM (3.7 m).

    Returns
    -------
    dict with keys: beta_1, beta_2, beta_3, pvalue_beta_1, pvalue_beta_2,
    pvalue_beta_3, R2, n, resid (residual series) — or None if insufficient data.
    """
    df = pd.DataFrame({
        "h":   pd.to_numeric(h_series, errors="coerce"),
        "P":   pd.to_numeric(climate["P_m"], errors="coerce"),
        "PET": pd.to_numeric(climate["PET"], errors="coerce"),
    }).dropna()

    # Displacement above drainage datum. h is negative (below ground),
    # so h_disp = datum + h = datum - |depth|. Positive when water table
    # is above the datum; zero at the datum; negative below it.
    df["h_disp"] = drainage_datum + df["h"]
    df["h_disp_prev"] = df["h_disp"].shift(1)

    # Δh is computed from the raw h (the datum cancels in differences).
    df["h_prev"] = df["h"].shift(1)
    df["Delta_h"] = df["h"] - df["h_prev"]

    if lag > 0:
        df["P"] = df["P"].shift(lag)

    df = df.dropna(subset=["Delta_h", "P", "PET", "h_disp_prev"])
    if window is not None and len(df) > window:
        df = df.iloc[-window:]

    if len(df) < MIN_OBS_PER_WELL:
        return None

    # Design matrix — displacement formulation for β₃.
    X = pd.DataFrame({
        "beta_1": df["P"].values,
        "beta_2": -df["PET"].values,
        "beta_3": -df["h_disp_prev"].values,
    }, index=df.index)
    y = df["Delta_h"].values

    try:
        model = sm.OLS(y, X).fit()
    except Exception:
        return None

    return {
        "beta_1":        float(model.params["beta_1"]),
        "beta_2":        float(model.params["beta_2"]),
        "beta_3":        float(model.params["beta_3"]),
        "pvalue_beta_1": float(model.pvalues["beta_1"]),
        "pvalue_beta_2": float(model.pvalues["beta_2"]),
        "pvalue_beta_3": float(model.pvalues["beta_3"]),
        "R2":            float(model.rsquared),
        "n":             int(len(df)),
        "resid":         pd.Series(model.resid, index=df.index, name="resid"),
    }


def assert_physical_signs(fit: dict, context: str) -> tuple[list[str], list[str]]:
    """
    Check physical-sign assertions on a fit result.

    Hard assertions (β₁ > 0, β₂ > 0): violations halt the pipeline.
    Soft assertion (β₃ > 0): violation is warned but does not halt.
    Under the displacement formulation, β₃ > 0 is physically expected
    (Darcy-consistent drainage). A negative β₃ is anomalous and worth
    investigating but not pipeline-fatal.

    Returns (hard_violations, soft_warnings) — both lists of strings.
    """
    hard = []
    soft = []
    if fit is None:
        return hard, soft
    if not (fit["beta_1"] > 0):
        hard.append(
            f"  [SIGN VIOLATION] {context}: beta_1 = {fit['beta_1']:+.4f} "
            f"(must be > 0; p = {fit['pvalue_beta_1']:.3f})"
        )
    if not (fit["beta_2"] > 0):
        hard.append(
            f"  [SIGN VIOLATION] {context}: beta_2 = {fit['beta_2']:+.4f} "
            f"(must be > 0; p = {fit['pvalue_beta_2']:.3f})"
        )
    if not (fit["beta_3"] > 0):
        soft.append(
            f"  [SIGN WARNING]   {context}: beta_3 = {fit['beta_3']:+.4f} "
            f"(expected > 0 under displacement formulation; "
            f"p = {fit['pvalue_beta_3']:.3f})"
        )
    return hard, soft


# ==========================================================================
# CENTROID CONSTRUCTION — upstand-corrected cluster averaging
# ==========================================================================

def build_upstand_lookup(elev_path) -> dict[str, float]:
    """Return {normalised_well_name: upstand_m} from the elevation file."""
    lookup = {}
    if not elev_path.exists():
        print(" -> [WARNING] Elevation file not found. Centroid upstand "
              "correction skipped.")
        return lookup

    elev_df = pd.read_csv(elev_path)
    elev_df.columns = [c.strip() for c in elev_df.columns]
    if "Name_norm" in elev_df.columns and "Upstand_m" in elev_df.columns:
        for _, row in elev_df.iterrows():
            if pd.notna(row.get("Upstand_m")):
                lookup[str(row["Name_norm"])] = float(row["Upstand_m"])
    print(f" -> Upstand lookup loaded: {len(lookup)} wells.")
    return lookup


def upstand_audit(cluster_df: pd.DataFrame,
                  upstand_lookup: dict[str, float]) -> None:
    """
    Print any reference-network wells with upstand above the audit threshold,
    grouped by cluster. Diagnostic — does not filter or alter anything.
    """
    print(f"\n -> Upstand audit (threshold > {UPSTAND_AUDIT_THRESHOLD:.2f} m):")
    flagged = []
    for _, row in cluster_df.iterrows():
        norm = normalize_well_name(str(row["Match_ID"]))
        u = upstand_lookup.get(norm)
        if u is not None and u > UPSTAND_AUDIT_THRESHOLD:
            flagged.append((row["Cluster"], row["Match_ID"], u))

    if not flagged:
        print("    (no wells exceed threshold)")
        return

    flagged.sort(key=lambda t: (t[0], -t[2]))
    for cid, name, u in flagged:
        print(f"    C{cid}: {name:10s}  upstand = {u:.3f} m")


def build_cluster_centroids(cluster_df: pd.DataFrame,
                            wells_clean: pd.DataFrame,
                            upstand_lookup: dict[str, float],
                            well_col_lookup: dict[str, str]
                            ) -> dict[int, pd.Series]:
    """
    For each cluster, build the upstand-corrected mean hydrograph.

    Each well's series has its upstand subtracted (pipe-top depth -> ground-
    surface depth) before averaging, so all cluster members share a common
    datum. Wells without an upstand entry are averaged uncorrected (the
    constant offset affects intercept only, which a no-intercept OLS does
    not fit — so the slope coefficients are still clean).

    Returns {cluster_id: pd.Series of monthly cluster-mean h}.
    """
    centroids: dict[int, pd.Series] = {}
    for cid in sorted(pd.to_numeric(cluster_df["Cluster"],
                                     errors="coerce").dropna().astype(int).unique()):
        c_wells = cluster_df[
            pd.to_numeric(cluster_df["Cluster"], errors="coerce") == cid
        ]["Match_ID"].astype(str).values

        available = [
            well_col_lookup.get(normalize_well_name(w))
            for w in c_wells
            if well_col_lookup.get(normalize_well_name(w)) is not None
        ]
        if not available:
            continue

        if upstand_lookup:
            corrected = {}
            n_corr = 0
            for col in available:
                col_norm = normalize_well_name(col).lower()\
                           .replace(" ", "").replace("_", "")
                u = upstand_lookup.get(col_norm)
                if u is not None:
                    corrected[col] = wells_clean[col] - u
                    n_corr += 1
                else:
                    corrected[col] = wells_clean[col]
            n_unc = len(available) - n_corr
            centroids[cid] = pd.DataFrame(corrected).mean(axis=1)
            print(f"    C{cid}: {n_corr} upstand-corrected, "
                  f"{n_unc} uncorrected")
        else:
            centroids[cid] = wells_clean[available].mean(axis=1)

    return centroids


# ==========================================================================
# PER-WELL FIT LOOP (unchanged convention from the old pipeline, but using
# the shared fit_ssm function for consistency with the centroid fit)
# ==========================================================================

def per_well_fits(cluster_df: pd.DataFrame,
                  locs_clean: pd.DataFrame,
                  wells_clean: pd.DataFrame,
                  climate: pd.DataFrame,
                  well_col_lookup: dict[str, str],
                  upstand_lookup: dict[str, float]) -> pd.DataFrame:
    """
    Fit the SSM to every reference well individually.

    Each well's series is upstand-corrected (pipe-top depth → ground-surface
    depth) before fitting, so that the DRAINAGE_DATUM displacement is relative
    to the ground surface for every well. This is required for physical
    consistency of the β₃ coefficient under the displacement formulation.

    Produces the per-well master table (INT_MASTER_DATA). Per-well LCSC uses
    the regression beta_1 when beta_1 > 0; otherwise LCSC is NaN.
    """
    # Ensure Match_ID is normalised for the merge.
    cluster_df = cluster_df.copy()
    cluster_df["Match_ID"] = cluster_df["Match_ID"].apply(normalize_well_name)

    if "Name_Original" not in cluster_df.columns:
        cluster_df = cluster_df.merge(
            locs_clean[["Match_ID", "Name"]], on="Match_ID", how="left"
        )
        cluster_df = cluster_df.rename(columns={"Name": "Name_Original"})

    map_data = pd.merge(cluster_df, locs_clean, on="Match_ID", how="inner")

    results = []
    for _, row in map_data.iterrows():
        well_name = row["Name_Original"]
        target_col = well_col_lookup.get(normalize_well_name(well_name))
        if target_col is None:
            continue

        # Upstand-correct: pipe-top depth → ground-surface depth, so the
        # DRAINAGE_DATUM displacement is relative to the ground for every well.
        col_norm = normalize_well_name(target_col).lower()\
                   .replace(" ", "").replace("_", "")
        u = upstand_lookup.get(col_norm, 0.0)
        h_corrected = wells_clean[target_col] - u

        fit = fit_ssm(h_corrected, climate, lag=HEADLINE_LAG,
                      window=LCSC_DATA_LIMIT)

        # Empirical LCSC — ratio of rainfall to water-table rise during
        # unambiguous recharge events. Kept for cross-comparison with the
        # regression LCSC; uses the full available record for each well.
        df_emp = pd.DataFrame({
            "h":  pd.to_numeric(wells_clean[target_col], errors="coerce"),
            "P":  pd.to_numeric(climate["P_m"], errors="coerce"),
        }).dropna()
        df_emp["Delta_h"] = df_emp["h"].diff()
        df_emp = df_emp.dropna()
        if len(df_emp) > LCSC_DATA_LIMIT:
            df_emp = df_emp.iloc[-LCSC_DATA_LIMIT:]

        lcsc_empirical = np.nan
        recharge_events = df_emp[df_emp["Delta_h"] > 0.02].copy()
        if len(recharge_events) > 10:
            recharge_events["LCSC_raw"] = (
                recharge_events["P"] / recharge_events["Delta_h"]
            )
            valid = recharge_events[
                (recharge_events["LCSC_raw"] > 0.05) &
                (recharge_events["LCSC_raw"] <= 1.0)
            ]
            if len(valid) > 0:
                lcsc_empirical = float(valid["LCSC_raw"].mean() * 100)

        if fit is not None:
            lcsc_reg = (100.0 / fit["beta_1"]) if fit["beta_1"] > 0 else np.nan
            results.append({
                "Name_Original":           target_col,
                "Cluster":                 row["Cluster"],
                "Easting":                 row["E"],
                "Northing":                row["N"],
                "LCSC_Empirical_Percent":  lcsc_empirical,
                "LCSC_Regression_Percent": lcsc_reg,
                "beta_1_recharge":         fit["beta_1"],
                "beta_2_atmospheric_draw": fit["beta_2"],
                "beta_3_drainage":         fit["beta_3"],
                "pvalue_beta_1":           fit["pvalue_beta_1"],
                "pvalue_beta_2":           fit["pvalue_beta_2"],
                "pvalue_beta_3":           fit["pvalue_beta_3"],
                "Model_R2":                fit["R2"],
                "n":                       fit["n"],
            })
        else:
            results.append({
                "Name_Original":           target_col,
                "Cluster":                 row["Cluster"],
                "Easting":                 row["E"],
                "Northing":                row["N"],
                "LCSC_Empirical_Percent":  lcsc_empirical,
                "LCSC_Regression_Percent": np.nan,
                "beta_1_recharge":         np.nan,
                "beta_2_atmospheric_draw": np.nan,
                "beta_3_drainage":         np.nan,
                "pvalue_beta_1":           np.nan,
                "pvalue_beta_2":           np.nan,
                "pvalue_beta_3":           np.nan,
                "Model_R2":                np.nan,
                "n":                       0,
            })

    return pd.DataFrame(results)


# ==========================================================================
# CENTROID FITS — HEADLINE + DIAGNOSTICS
# ==========================================================================

def centroid_headline_fits(centroids: dict[int, pd.Series],
                            climate: pd.DataFrame
                            ) -> tuple[pd.DataFrame, list[str], list[str]]:
    """
    Headline centroid SSM fit (displacement formulation), per cluster.

    Returns:
        mech_df    — long-form table of coefficients, p-values, R², n
                     with labels from config.CLUSTER_LABELS
        violations — list of hard sign-violation messages (β₁, β₂)
        warnings   — list of soft sign-warning messages (β₃)
    """
    rows = []
    violations = []
    warnings = []
    for cid in sorted(centroids):
        fit = fit_ssm(centroids[cid], climate, lag=HEADLINE_LAG, window=None)
        label = CLUSTER_LABELS.get(cid, f"C{cid}")

        if fit is None:
            rows.append({
                "Cluster": cid, "Cluster_Label": label,
                "beta_1": np.nan, "pvalue_beta_1": np.nan,
                "beta_2": np.nan, "pvalue_beta_2": np.nan,
                "beta_3": np.nan, "pvalue_beta_3": np.nan,
                "R2": np.nan, "n": 0,
                "LCSC_percent": np.nan,
                "drainage_datum_m": DRAINAGE_DATUM,
            })
            continue

        lcsc = (100.0 / fit["beta_1"]) if fit["beta_1"] > 0 else np.nan
        rows.append({
            "Cluster":       cid,
            "Cluster_Label": label,
            "beta_1":        fit["beta_1"],
            "pvalue_beta_1": fit["pvalue_beta_1"],
            "beta_2":        fit["beta_2"],
            "pvalue_beta_2": fit["pvalue_beta_2"],
            "beta_3":        fit["beta_3"],
            "pvalue_beta_3": fit["pvalue_beta_3"],
            "R2":            fit["R2"],
            "n":             fit["n"],
            "LCSC_percent":  lcsc,
            "drainage_datum_m": DRAINAGE_DATUM,
        })
        hard, soft = assert_physical_signs(fit, f"C{cid} {label}")
        violations.extend(hard)
        warnings.extend(soft)

    return pd.DataFrame(rows), violations, warnings


def lag_diagnostic(centroids: dict[int, pd.Series],
                   climate: pd.DataFrame) -> pd.DataFrame:
    """
    Fit the centroid SSM at rainfall lags 0, 1, 2, 3 months, per cluster.

    Addresses the question "does the centroid water-level series respond to
    this month's or last month's rainfall?" — relevant because forest wells
    may show lagged recharge, and because the prior (pre-rebuild) lag finding
    may have been an artefact of the Script 01 bucketing bug.

    Read this table alongside the bootstrap CIs: a lag-1 fit with a much
    higher R^2 than lag-0, and physically-coherent sign, is evidence the
    headline model should use that lag instead.
    """
    rows = []
    for cid in sorted(centroids):
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        for lag in LAGS:
            fit = fit_ssm(centroids[cid], climate, lag=lag, window=None)
            if fit is None:
                rows.append({
                    "Cluster": cid, "Cluster_Label": label, "Lag_months": lag,
                    "beta_1": np.nan, "pvalue_beta_1": np.nan,
                    "beta_2": np.nan, "pvalue_beta_2": np.nan,
                    "beta_3": np.nan, "pvalue_beta_3": np.nan,
                    "R2": np.nan, "n": 0,
                    "beta_1_physically_coherent": np.nan,
                    "beta_2_physically_coherent": np.nan,
                })
                continue
            rows.append({
                "Cluster":       cid,
                "Cluster_Label": label,
                "Lag_months":    lag,
                "beta_1":        fit["beta_1"],
                "pvalue_beta_1": fit["pvalue_beta_1"],
                "beta_2":        fit["beta_2"],
                "pvalue_beta_2": fit["pvalue_beta_2"],
                "beta_3":        fit["beta_3"],
                "pvalue_beta_3": fit["pvalue_beta_3"],
                "R2":            fit["R2"],
                "n":             fit["n"],
                "beta_1_physically_coherent": fit["beta_1"] > 0,
                "beta_2_physically_coherent": fit["beta_2"] > 0,
            })

    return pd.DataFrame(rows)


def bootstrap_centroid_fits(cluster_df: pd.DataFrame,
                             wells_clean: pd.DataFrame,
                             climate: pd.DataFrame,
                             upstand_lookup: dict[str, float],
                             well_col_lookup: dict[str, str],
                             n_boot: int = N_BOOTSTRAP,
                             seed: int = BOOTSTRAP_SEED) -> pd.DataFrame:
    """
    Bootstrap the centroid SSM fit per cluster by resampling member wells
    with replacement. For each bootstrap replicate:
        - draw n_cluster wells from the cluster with replacement,
        - build the centroid hydrograph over the resample (upstand-corrected
          where possible),
        - refit the SSM at lag 0.

    Reports median and (2.5%, 97.5%) percentile CI per cluster for beta_1,
    beta_2, beta_3, R^2, and LCSC_percent. Phase 1 validation diagnostic.
    """
    rng = np.random.default_rng(seed)
    rows = []

    for cid in sorted(pd.to_numeric(cluster_df["Cluster"],
                                     errors="coerce").dropna().astype(int).unique()):
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        c_wells_raw = cluster_df[
            pd.to_numeric(cluster_df["Cluster"], errors="coerce") == cid
        ]["Match_ID"].astype(str).values

        # Resolve to actual wells_clean columns up front; skip members not present.
        resolved = [
            well_col_lookup.get(normalize_well_name(w))
            for w in c_wells_raw
            if well_col_lookup.get(normalize_well_name(w)) is not None
        ]
        if len(resolved) < 2:
            continue

        beta_1s, beta_2s, beta_3s, r2s, lcscs = [], [], [], [], []
        n_success = 0
        for _ in range(n_boot):
            idx = rng.integers(0, len(resolved), size=len(resolved))
            sampled = [resolved[i] for i in idx]

            cols = {}
            for i, col in enumerate(sampled):
                col_norm = normalize_well_name(col).lower()\
                           .replace(" ", "").replace("_", "")
                u = upstand_lookup.get(col_norm)
                series = wells_clean[col] - u if u is not None else wells_clean[col]
                cols[f"{col}__{i}"] = series  # dedup with replacement
            centroid = pd.DataFrame(cols).mean(axis=1)

            fit = fit_ssm(centroid, climate, lag=HEADLINE_LAG, window=None)
            if fit is None:
                continue
            beta_1s.append(fit["beta_1"])
            beta_2s.append(fit["beta_2"])
            beta_3s.append(fit["beta_3"])
            r2s.append(fit["R2"])
            lcsc = (100.0 / fit["beta_1"]) if fit["beta_1"] > 0 else np.nan
            lcscs.append(lcsc)
            n_success += 1

        def pct(arr, q):
            a = np.asarray([x for x in arr if np.isfinite(x)])
            return float(np.percentile(a, q)) if len(a) else np.nan

        rows.append({
            "Cluster": cid, "Cluster_Label": label,
            "n_wells": len(resolved),
            "n_boot_success": n_success,
            "beta_1_median":  float(np.median(beta_1s)) if beta_1s else np.nan,
            "beta_1_lo":      pct(beta_1s, 2.5),
            "beta_1_hi":      pct(beta_1s, 97.5),
            "beta_2_median":  float(np.median(beta_2s)) if beta_2s else np.nan,
            "beta_2_lo":      pct(beta_2s, 2.5),
            "beta_2_hi":      pct(beta_2s, 97.5),
            "beta_3_median":  float(np.median(beta_3s)) if beta_3s else np.nan,
            "beta_3_lo":      pct(beta_3s, 2.5),
            "beta_3_hi":      pct(beta_3s, 97.5),
            "R2_median":      float(np.median(r2s)) if r2s else np.nan,
            "LCSC_median":    float(np.nanmedian(lcscs)) if lcscs else np.nan,
            "LCSC_lo":        pct(lcscs, 2.5),
            "LCSC_hi":        pct(lcscs, 97.5),
            "beta_1_frac_positive": (
                float(np.mean(np.asarray(beta_1s) > 0)) if beta_1s else np.nan
            ),
        })

    return pd.DataFrame(rows)


def leave_one_out_fits(cluster_df: pd.DataFrame,
                        wells_clean: pd.DataFrame,
                        climate: pd.DataFrame,
                        upstand_lookup: dict[str, float],
                        well_col_lookup: dict[str, str]) -> pd.DataFrame:
    """
    Per-cluster leave-one-well-out centroid fits.

    For each cluster with >= 4 members, refit the centroid SSM with each
    member excluded in turn. Useful for detecting single-well domination —
    if beta_1 flips sign or changes by a large factor when a particular
    well is removed, that well is anchoring the cluster's fit.
    """
    rows = []
    for cid in sorted(pd.to_numeric(cluster_df["Cluster"],
                                     errors="coerce").dropna().astype(int).unique()):
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        c_wells = cluster_df[
            pd.to_numeric(cluster_df["Cluster"], errors="coerce") == cid
        ]["Match_ID"].astype(str).values

        resolved = [
            (w, well_col_lookup.get(normalize_well_name(w)))
            for w in c_wells
        ]
        resolved = [(w, c) for w, c in resolved if c is not None]
        if len(resolved) < 4:
            continue

        for exclude_name, _ in resolved:
            kept = [c for w, c in resolved if w != exclude_name]
            cols = {}
            for col in kept:
                col_norm = normalize_well_name(col).lower()\
                           .replace(" ", "").replace("_", "")
                u = upstand_lookup.get(col_norm)
                series = wells_clean[col] - u if u is not None else wells_clean[col]
                cols[col] = series
            centroid = pd.DataFrame(cols).mean(axis=1)

            fit = fit_ssm(centroid, climate, lag=HEADLINE_LAG, window=None)
            if fit is None:
                rows.append({
                    "Cluster": cid, "Cluster_Label": label,
                    "Excluded_Well": exclude_name,
                    "beta_1": np.nan, "beta_2": np.nan, "beta_3": np.nan,
                    "R2": np.nan, "n": 0,
                })
                continue
            rows.append({
                "Cluster":       cid,
                "Cluster_Label": label,
                "Excluded_Well": exclude_name,
                "beta_1":        fit["beta_1"],
                "beta_2":        fit["beta_2"],
                "beta_3":        fit["beta_3"],
                "R2":            fit["R2"],
                "n":             fit["n"],
            })

    return pd.DataFrame(rows)


def c1_split_window_diagnostic(centroids: dict[int, pd.Series],
                                cluster_df: pd.DataFrame,
                                wells_clean: pd.DataFrame,
                                climate: pd.DataFrame,
                                upstand_lookup: dict[str, float],
                                well_col_lookup: dict[str, str],
                                split_date: pd.Timestamp = C1_SPLIT_DATE,
                                n_boot: int = N_BOOTSTRAP,
                                seed: int = BOOTSTRAP_SEED + 1
                                ) -> pd.DataFrame:
    """
    C1 Lake split-window diagnostic.

    Fits the C1 centroid SSM separately on pre-`split_date` and post-
    `split_date` windows, and bootstraps each side by well-resampling.
    If the two beta sets are non-overlapping (CI disjoint), the single-beta
    Lake fit averages over two regimes — see SCRIPT_03_BRIEF.md amplitude
    analysis for physical context (four of seven Lake wells enlarge
    post-2018 even after climate normalisation).
    """
    if 1 not in centroids:
        return pd.DataFrame()

    c1_series = centroids[1]
    pre  = c1_series[c1_series.index <  split_date]
    post = c1_series[c1_series.index >= split_date]

    def fit_and_boot(series_window: pd.Series,
                      window_label: str,
                      bs_seed: int) -> dict:
        headline = fit_ssm(series_window, climate, lag=HEADLINE_LAG, window=None)
        if headline is None:
            return {"window": window_label,
                    "beta_1": np.nan, "beta_2": np.nan, "beta_3": np.nan,
                    "R2": np.nan, "n": 0,
                    "beta_1_lo": np.nan, "beta_1_hi": np.nan,
                    "beta_2_lo": np.nan, "beta_2_hi": np.nan,
                    "beta_3_lo": np.nan, "beta_3_hi": np.nan}

        # Bootstrap: resample C1 wells with replacement, build centroid over
        # that window, refit.
        c_wells = cluster_df[
            pd.to_numeric(cluster_df["Cluster"], errors="coerce") == 1
        ]["Match_ID"].astype(str).values
        resolved = [
            well_col_lookup.get(normalize_well_name(w))
            for w in c_wells
            if well_col_lookup.get(normalize_well_name(w)) is not None
        ]

        rng = np.random.default_rng(bs_seed)
        b1s, b2s, b3s = [], [], []
        for _ in range(n_boot):
            idx = rng.integers(0, len(resolved), size=len(resolved))
            sampled = [resolved[i] for i in idx]
            cols = {}
            for i, col in enumerate(sampled):
                col_norm = normalize_well_name(col).lower()\
                           .replace(" ", "").replace("_", "")
                u = upstand_lookup.get(col_norm)
                series = wells_clean[col] - u if u is not None else wells_clean[col]
                if window_label == "pre_2018":
                    series = series[series.index < split_date]
                else:
                    series = series[series.index >= split_date]
                cols[f"{col}__{i}"] = series
            centroid = pd.DataFrame(cols).mean(axis=1)
            fit = fit_ssm(centroid, climate, lag=HEADLINE_LAG, window=None)
            if fit is None:
                continue
            b1s.append(fit["beta_1"])
            b2s.append(fit["beta_2"])
            b3s.append(fit["beta_3"])

        def pct(arr, q):
            a = np.asarray([x for x in arr if np.isfinite(x)])
            return float(np.percentile(a, q)) if len(a) else np.nan

        return {
            "window":   window_label,
            "beta_1":   headline["beta_1"],
            "beta_2":   headline["beta_2"],
            "beta_3":   headline["beta_3"],
            "R2":       headline["R2"],
            "n":        headline["n"],
            "beta_1_lo": pct(b1s, 2.5),  "beta_1_hi": pct(b1s, 97.5),
            "beta_2_lo": pct(b2s, 2.5),  "beta_2_hi": pct(b2s, 97.5),
            "beta_3_lo": pct(b3s, 2.5),  "beta_3_hi": pct(b3s, 97.5),
        }

    return pd.DataFrame([
        fit_and_boot(pre,  "pre_2018",  seed),
        fit_and_boot(post, "post_2018", seed + 100),
    ])


# ==========================================================================
# DATUM SENSITIVITY ANALYSIS
# ==========================================================================

def datum_sensitivity_analysis(centroids: dict[int, pd.Series],
                                climate: pd.DataFrame) -> pd.DataFrame:
    """
    Sweep reference datum depths from 0.5 to 8.0 m in 0.1 m steps.
    At each depth, fit the centroid SSM for all five clusters and record
    β₁, β₂, β₃, p-values, R², AIC.

    Selection criterion: the minimum depth at which β₃ is positive AND
    significant (p < 0.05) for all five clusters simultaneously.

    Output: DataFrame with columns (ref_depth, Cluster, Cluster_Label,
    beta_1..3, pvalue_beta_1..3, R2, AIC, beta_3_positive, beta_3_sig).
    """
    datums = np.arange(0.5, 8.05, 0.1)
    rows = []
    for d in datums:
        for cid in sorted(centroids):
            label = CLUSTER_LABELS.get(cid, f"C{cid}")
            fit = fit_ssm(centroids[cid], climate,
                          lag=HEADLINE_LAG, window=None,
                          drainage_datum=d)
            if fit is None:
                rows.append({
                    "ref_depth": round(d, 1), "Cluster": cid,
                    "Cluster_Label": label,
                    "beta_1": np.nan, "beta_2": np.nan, "beta_3": np.nan,
                    "pvalue_beta_1": np.nan, "pvalue_beta_2": np.nan,
                    "pvalue_beta_3": np.nan,
                    "R2": np.nan, "AIC": np.nan,
                    "beta_3_positive": False, "beta_3_sig": False,
                })
                continue

            # Compute AIC from residuals (OLS, no intercept, k=3 params).
            n = fit["n"]
            rss = float((fit["resid"] ** 2).sum())
            aic = n * np.log(rss / n) + 2 * 3 if n > 0 else np.nan

            rows.append({
                "ref_depth":       round(d, 1),
                "Cluster":         cid,
                "Cluster_Label":   label,
                "beta_1":          fit["beta_1"],
                "beta_2":          fit["beta_2"],
                "beta_3":          fit["beta_3"],
                "pvalue_beta_1":   fit["pvalue_beta_1"],
                "pvalue_beta_2":   fit["pvalue_beta_2"],
                "pvalue_beta_3":   fit["pvalue_beta_3"],
                "R2":              fit["R2"],
                "AIC":             aic,
                "beta_3_positive": fit["beta_3"] > 0,
                "beta_3_sig":      fit["pvalue_beta_3"] < 0.05,
            })

    return pd.DataFrame(rows)


def make_datum_sensitivity_figure(sens_df: pd.DataFrame,
                                   selected_datum: float,
                                   out_path) -> None:
    """
    3-panel figure:
      Top:    β₃ vs reference depth per cluster (with p < 0.05 markers)
      Middle: R² vs reference depth per cluster
      Bottom: mean R² and sum AIC vs reference depth
      Vertical line at selected datum.
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 14), dpi=300, sharex=True)
    fig.suptitle("Datum Sensitivity Analysis — SSM Displacement Formulation",
                 fontsize=16, fontweight="bold", y=0.98)

    cids = sorted(sens_df["Cluster"].unique())
    datums = sorted(sens_df["ref_depth"].unique())

    # Top: β₃ per cluster
    ax = axes[0]
    for cid in cids:
        sub = sens_df[sens_df.Cluster == cid].sort_values("ref_depth")
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        colour = CLUSTER_COLOURS.get(cid, "#888888")
        ax.plot(sub["ref_depth"], sub["beta_3"], color=colour, label=label,
                linewidth=1.5)
        # Mark where p < 0.05
        sig = sub[sub["beta_3_sig"]]
        ax.scatter(sig["ref_depth"], sig["beta_3"], color=colour, s=8,
                   zorder=5, alpha=0.4)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.axvline(selected_datum, color="black", linewidth=1.2, linestyle=":",
               label=f"Selected datum ({selected_datum} m)")
    ax.set_ylabel(r"$\beta_3$ (drainage coefficient)", fontsize=12)
    ax.set_title(r"$\beta_3$ vs reference depth (dots = p < 0.05)", fontsize=13)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(alpha=0.3)

    # Middle: R² per cluster
    ax = axes[1]
    for cid in cids:
        sub = sens_df[sens_df.Cluster == cid].sort_values("ref_depth")
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        colour = CLUSTER_COLOURS.get(cid, "#888888")
        ax.plot(sub["ref_depth"], sub["R2"], color=colour, label=label,
                linewidth=1.5)
    ax.axvline(selected_datum, color="black", linewidth=1.2, linestyle=":")
    ax.set_ylabel("R²", fontsize=12)
    ax.set_title("R² vs reference depth per cluster", fontsize=13)
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(alpha=0.3)

    # Bottom: mean R² and sum AIC
    ax = axes[2]
    agg = sens_df.groupby("ref_depth").agg(
        mean_R2=("R2", "mean"),
        sum_AIC=("AIC", "sum"),
    ).reset_index()
    ax.plot(agg["ref_depth"], agg["mean_R2"], color="#333333",
            linewidth=2, label="Mean R²")
    ax.axvline(selected_datum, color="black", linewidth=1.2, linestyle=":")
    ax.set_ylabel("Mean R²", fontsize=12, color="#333333")
    ax.set_xlabel("Reference depth (m below ground surface)", fontsize=12)
    ax.tick_params(axis="y", labelcolor="#333333")

    ax2 = ax.twinx()
    ax2.plot(agg["ref_depth"], agg["sum_AIC"], color="#cc6600",
             linewidth=1.5, linestyle="--", label="Sum AIC")
    ax2.set_ylabel("Sum AIC (lower = better)", fontsize=12, color="#cc6600")
    ax2.tick_params(axis="y", labelcolor="#cc6600")

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc="center right")
    ax.set_title("Aggregate fit quality vs reference depth", fontsize=13)
    ax.grid(alpha=0.3)

    # Mark the band where all β₃ positive + sig
    all_pos_sig = sens_df.groupby("ref_depth").agg(
        all_pos=("beta_3_positive", "all"),
        all_sig=("beta_3_sig", "all"),
    ).reset_index()
    valid = all_pos_sig[all_pos_sig["all_pos"] & all_pos_sig["all_sig"]]
    if len(valid) > 0:
        lo, hi = valid["ref_depth"].min(), valid["ref_depth"].max()
        for a in axes:
            a.axvspan(lo, hi, alpha=0.08, color="green",
                      label=f"All β₃ > 0 & sig [{lo:.1f}–{hi:.1f} m]")

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f" -> Saved: {out_path.name}")


# ==========================================================================
# SUMMARY TABLE + FIGURE
# ==========================================================================

def build_summary_table(mech_df: pd.DataFrame,
                         boot_df: pd.DataFrame,
                         cluster_df: pd.DataFrame) -> pd.DataFrame:
    """
    Headline per-cluster summary. Merges centroid mechanistic table with
    bootstrap CIs and the amplitude-heterogeneity flag.

    Columns:
        Cluster, Cluster_Label, Block, n_wells,
        beta_1..3 (centroid),  LCSC_percent (centroid),
        beta_1_lo, beta_1_hi, LCSC_lo, LCSC_hi (bootstrap),
        R2, beta_1_frac_positive,
        amplitude_heterogeneous, post2018_amp_lo_m, post2018_amp_hi_m.
    """
    counts = (pd.to_numeric(cluster_df["Cluster"], errors="coerce")
              .dropna().astype(int).value_counts()
              .rename_axis("Cluster").rename("n_wells").reset_index())

    m = mech_df.copy()
    m = m.merge(counts, on="Cluster", how="left")
    m["Block"] = m["Cluster"].map(BLOCK_MAP)

    b = boot_df[[
        "Cluster", "beta_1_lo", "beta_1_hi",
        "LCSC_lo", "LCSC_hi", "beta_1_frac_positive",
    ]].rename(columns={
        "beta_1_lo": "beta_1_boot_lo",
        "beta_1_hi": "beta_1_boot_hi",
        "LCSC_lo":   "LCSC_boot_lo",
        "LCSC_hi":   "LCSC_boot_hi",
    })
    m = m.merge(b, on="Cluster", how="left")

    cluster_ids = sorted(m["Cluster"].astype(int).unique())
    amp_het = load_amplitude_heterogeneity(cluster_ids, cluster_df)
    het_rows = []
    for cid, (het, lo, hi) in amp_het.items():
        het_rows.append({"Cluster": cid,
                         "amplitude_heterogeneous": het,
                         "post2018_amp_lo_m": lo,
                         "post2018_amp_hi_m": hi})
    m = m.merge(pd.DataFrame(het_rows), on="Cluster", how="left")

    col_order = [
        "Cluster", "Cluster_Label", "Block", "n_wells",
        "beta_1", "beta_1_boot_lo", "beta_1_boot_hi", "pvalue_beta_1",
        "beta_2", "pvalue_beta_2",
        "beta_3", "pvalue_beta_3",
        "R2",
        "LCSC_percent", "LCSC_boot_lo", "LCSC_boot_hi",
        "beta_1_frac_positive",
        "amplitude_heterogeneous", "post2018_amp_lo_m", "post2018_amp_hi_m",
        "n",
    ]
    col_order = [c for c in col_order if c in m.columns]
    return m[col_order].sort_values("Cluster").reset_index(drop=True)


def make_signatures_figure(mech_df: pd.DataFrame,
                            boot_df: pd.DataFrame,
                            out_path) -> None:
    """3-panel beta bar chart with bootstrap CI error bars."""
    df = mech_df.merge(
        boot_df[["Cluster", "beta_1_lo", "beta_1_hi",
                 "beta_2_lo", "beta_2_hi",
                 "beta_3_lo", "beta_3_hi"]],
        on="Cluster", how="left",
    ).sort_values("Cluster")

    cids = df["Cluster"].astype(int).tolist()
    labels = [CLUSTER_LABELS.get(c, f"C{c}") for c in cids]
    colors = [CLUSTER_COLOURS.get(c, "#888888") for c in cids]

    fig, axes = plt.subplots(1, 3, figsize=(15, 6), dpi=300)
    fig.suptitle("State-Space Mechanistic Signatures by Hydrogeological Cluster",
                 fontsize=18, fontweight="bold", y=1.02)

    panels = [
        ("beta_1", "beta_1_lo", "beta_1_hi",
         r"Recharge Sensitivity ($\beta_1$)", "Water table rise per mm rain"),
        ("beta_2", "beta_2_lo", "beta_2_hi",
         r"Atmospheric Draw ($\beta_2$)",     "Water table drop per mm PET"),
        ("beta_3", "beta_3_lo", "beta_3_hi",
         r"Internal Drainage ($\beta_3$)",    "Proportional decay rate"),
    ]

    for ax, (col, lo_col, hi_col, title, ylabel) in zip(axes, panels):
        vals = df[col].values.astype(float)
        lo = df[lo_col].values.astype(float)
        hi = df[hi_col].values.astype(float)
        # Error bars are distances from centre, not absolute bounds.
        yerr_lo = np.where(np.isfinite(lo), vals - lo, 0)
        yerr_hi = np.where(np.isfinite(hi), hi - vals, 0)
        ax.bar(labels, vals, color=colors, edgecolor="black",
               linewidth=1.0, zorder=3,
               yerr=[yerr_lo, yerr_hi], capsize=5, ecolor="black")
        ax.axhline(0, color="black", linewidth=0.8, linestyle="-", alpha=0.7)
        ax.set_title(title, fontsize=14, pad=10)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)
        ax.tick_params(axis="x", rotation=25)
        ax.set_facecolor("#f8f9fa")
        for i, v in enumerate(vals):
            if np.isfinite(v):
                offset = (hi[i] - lo[i]) * 0.05 if np.isfinite(hi[i]) and \
                         np.isfinite(lo[i]) else abs(v) * 0.05 + 1e-6
                ax.text(i, v + np.sign(v) * offset if v != 0 else offset,
                        f"{v:.3f}", ha="center",
                        va="bottom" if v >= 0 else "top",
                        fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f" -> Saved: {out_path.name}")


# ==========================================================================
# REGIONAL AVERAGE EXPORTS
# ==========================================================================

def export_regional_averages(centroids: dict[int, pd.Series],
                              climate: pd.DataFrame,
                              master_df: pd.DataFrame) -> None:
    """
    Build the cluster-centroid + per-block average hydrograph export.

    Under the Option-A partition, each cluster is its own block (C1 Lake is
    reported separately per Martin's call, not folded into Eastern Block).
    So the block columns are simple aliases of the cluster columns, with
    readable names.
    """
    df_export = pd.DataFrame({f"C{cid}": centroids[cid]
                              for cid in sorted(centroids)})
    df_export.index.name = "Date"

    # One block per cluster under Option A — names from BLOCK_MAP.
    for cid, block_name in BLOCK_MAP.items():
        c_col = f"C{cid}"
        if c_col in df_export.columns:
            # Sanitise the block name for use as a column name (spaces -> _)
            df_export[block_name.replace(" ", "_")] = df_export[c_col]

    # Final manuscript LCSC print — per cluster now, not per merged block.
    master_df = master_df.copy()
    master_df["Block"] = pd.to_numeric(master_df["Cluster"],
                                        errors="coerce").map(BLOCK_MAP)
    block_stats = master_df.groupby("Block")["LCSC_Regression_Percent"]\
                            .mean().sort_index()
    print("\n" + "=" * 50)
    print("   FINAL MANUSCRIPT LCSC PERCENTAGES")
    print("=" * 50)
    for block, val in block_stats.items():
        if pd.notna(block):
            print(f" {block:16s} : {val:.1f}%")
    print("=" * 50)

    df_export = df_export.join(climate[["P_m", "PET"]])
    df_export = df_export.rename(columns={"P_m": "P_mm", "PET": "PET_mm"})
    df_export["P_mm"]   *= 1000
    df_export["PET_mm"] *= 1000
    df_export.to_csv(INT_REGIONAL_AVG)
    print(f" -> Saved: {INT_REGIONAL_AVG.name}")


def export_regional_averages_maod(cluster_df: pd.DataFrame,
                                   climate: pd.DataFrame) -> None:
    """maOD cluster-centroid export — unchanged logic from the pre-rebuild
    script. Consumed by Script 21 (forestry scenarios) and other scripts
    needing absolute head values."""
    if not INT_WELLS_CLEAN_MAOD.exists():
        print(f"    [WARNING] {INT_WELLS_CLEAN_MAOD.name} not found — "
              "Script 21 will fail without maOD file.")
        return

    try:
        maod_df = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0,
                               parse_dates=True)
        maod_df.columns = [normalize_well_name(c) for c in maod_df.columns]
    except Exception as exc:
        print(f"    [WARNING] maOD cluster averages not written: {exc}")
        return

    cluster_maod_ts = {}
    for cid in sorted(pd.to_numeric(cluster_df["Cluster"],
                                     errors="coerce").dropna().astype(int).unique()):
        c_wells = cluster_df[
            pd.to_numeric(cluster_df["Cluster"], errors="coerce") == cid
        ]["Match_ID"].astype(str).values
        available = [normalize_well_name(w) for w in c_wells
                     if normalize_well_name(w) in maod_df.columns]
        if available:
            cluster_maod_ts[f"C{cid}"] = maod_df[available].mean(axis=1)

    if not cluster_maod_ts:
        print("    [WARNING] No maOD cluster averages computed — "
              "check well-name matching.")
        return

    df_maod = pd.DataFrame(cluster_maod_ts)
    df_maod.index.name = "Date"
    df_maod = df_maod.join(climate[["P_m", "PET"]])
    df_maod = df_maod.rename(columns={"P_m": "P_mm", "PET": "PET_mm"})
    df_maod["P_mm"]   *= 1000
    df_maod["PET_mm"] *= 1000
    df_maod.to_csv(INT_CLUSTER_AVG_MAOD)
    print(f" -> Saved: {INT_CLUSTER_AVG_MAOD.name}")


def export_cluster_peak_months(centroids: dict) -> None:
    """
    Derive each cluster's peak water-table month from the long-term monthly
    mean of the cluster centroid hydrograph and write to
    INT_CLUSTER_PEAK_MONTHS.

    Peak month = the calendar month with the shallowest (least negative)
    mean depth-below-ground, i.e. the month when the water table is closest
    to the surface.

    Output columns:
        cluster_id     int   — numeric cluster ID (e.g. 1, 2, …)
        cluster_label  str   — human-readable label from config.CLUSTER_LABELS
        peak_month     int   — calendar month 1–12
    """
    rows = []
    for cid in sorted(centroids):
        ts = centroids[cid].dropna()
        if len(ts) < 24:
            print(f"    [WARNING] C{cid}: too few data points for peak month "
                  f"({len(ts)}); skipping.")
            continue
        monthly_mean = ts.groupby(ts.index.month).mean()
        # Shallowest = least negative (max) for depth convention
        peak = int(monthly_mean.idxmax())
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        rows.append({
            "cluster_id":    cid,
            "cluster_label": label,
            "peak_month":    peak,
        })
    df = pd.DataFrame(rows)
    df.to_csv(INT_CLUSTER_PEAK_MONTHS, index=False)
    print(f" -> Saved: {INT_CLUSTER_PEAK_MONTHS.name}  "
          f"({len(df)} clusters)")
    for _, r in df.iterrows():
        print(f"    C{r['cluster_id']} ({r['cluster_label']}): "
              f"peak month = {r['peak_month']}")


# ==========================================================================
# MAIN
# ==========================================================================

def main() -> None:
    make_all_dirs()
    print("Starting 03: State-Space Regression & LCSC...")

    # ---- Load ----
    locs_clean  = pd.read_csv(INT_LOCATIONS)
    cluster_df  = pd.read_csv(INT_CLUSTER_STATS)
    climate     = pd.read_csv(INT_CLIMATE,     index_col=0, parse_dates=True)
    wells_clean = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)

    # ---- Validate cluster partition against config.CLUSTER_LABELS ----
    cluster_ids_in_file = sorted(pd.to_numeric(cluster_df["Cluster"],
                                                 errors="coerce")
                                  .dropna().astype(int).unique())
    cluster_ids_in_config = sorted(CLUSTER_LABELS.keys())
    if cluster_ids_in_file != cluster_ids_in_config:
        raise AssertionError(
            f"Cluster IDs in {INT_CLUSTER_STATS.name} ({cluster_ids_in_file}) "
            f"do not match config.CLUSTER_LABELS ({cluster_ids_in_config}). "
            "Re-run Script 02 or fix the partition file before proceeding."
        )
    print(f" -> Cluster partition verified: {cluster_ids_in_file} "
          f"matches config.CLUSTER_LABELS.")

    # ---- Locations and normalisation ----
    locs_clean["Match_ID"] = locs_clean["Match_ID"].apply(normalize_well_name)
    cluster_df["Match_ID"] = cluster_df["Match_ID"].apply(normalize_well_name)
    well_col_lookup = {normalize_well_name(c): c for c in wells_clean.columns}

    # ---- Upstand lookup + audit ----
    upstand_lookup = build_upstand_lookup(INT_WELL_ELEVATIONS)
    upstand_audit(cluster_df, upstand_lookup)

    # ---- Per-well SSM fits ----
    print("\n -> Fitting per-well SSM and computing LCSC...")
    master_df = per_well_fits(cluster_df, locs_clean, wells_clean,
                               climate, well_col_lookup, upstand_lookup)
    master_df.to_csv(INT_MASTER_DATA, index=False)
    print(f" -> Saved: {INT_MASTER_DATA.name} "
          f"({len(master_df)} wells)")

    n_bad_b1 = int((master_df["beta_1_recharge"] < 0).sum())
    n_bad_b2 = int((master_df["beta_2_atmospheric_draw"] < 0).sum())
    if n_bad_b1 or n_bad_b2:
        print(f"    [INFO] Per-well sign violations: "
              f"beta_1<0 in {n_bad_b1} wells, beta_2<0 in {n_bad_b2} wells. "
              "Not halting — per-well violations are informational. "
              "Centroid-fit violations halt the pipeline.")

    print("\n   PER-WELL AVERAGE STATISTICS BY CLUSTER (window = "
          f"{LCSC_DATA_LIMIT} months)")
    print(master_df.groupby("Cluster")[
        ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage",
         "LCSC_Regression_Percent", "Model_R2"]
    ].mean().round(3))

    # ---- Build cluster centroids ----
    print("\n -> Building cluster centroids (upstand-corrected)...")
    centroids = build_cluster_centroids(cluster_df, wells_clean,
                                          upstand_lookup, well_col_lookup)

    # ---- Centroid headline fits (the CSV the report cites) ----
    print(f"\n -> Fitting cluster-centroid SSMs (headline, lag {HEADLINE_LAG})...")
    mech_df, violations, b3_warnings = centroid_headline_fits(centroids, climate)
    mech_df.to_csv(OUT_03_MECHANISTIC_TABLE, index=False)
    print(f" -> Saved: {OUT_03_MECHANISTIC_TABLE.name}")

    # Sign violations are reported loudly here but don't halt yet — the
    # diagnostics below (lag sweep, bootstrap, LOO, split-window) are the
    # tools for investigating *why* a fit violated. Halting before running
    # them defeats the purpose. Hard-halt is deferred to after all diagnostic
    # tables and the signatures figure are saved.
    if violations:
        print("\n" + "!" * 70)
        print("!! CENTROID SIGN ASSERTIONS FAILED — see diagnostics below. !!")
        print("!" * 70)
        for v in violations:
            print(v)
        print("!" * 70)

    if b3_warnings:
        print("\n" + "-" * 70)
        print("-- β₃ soft warnings (displacement formulation expects β₃ > 0) --")
        print("-" * 70)
        for w in b3_warnings:
            print(w)
        print("-" * 70)

    # ---- Lag diagnostic (lags 0..3) ----
    print("\n -> Lag diagnostic (lags 0, 1, 2, 3 months)...")
    lag_df = lag_diagnostic(centroids, climate)
    lag_path = DIR_03 / "03_04_lag_diagnostic.csv"
    lag_df.to_csv(lag_path, index=False)
    print(f" -> Saved: {lag_path.name}")

    # ---- Datum sensitivity analysis ----
    print(f"\n -> Datum sensitivity analysis (0.5–8.0 m, 0.1 m steps, "
          f"selected = {DRAINAGE_DATUM} m)...")
    sens_df = datum_sensitivity_analysis(centroids, climate)
    sens_path = DIR_03 / "03_08_datum_sensitivity.csv"
    sens_df.to_csv(sens_path, index=False)
    print(f" -> Saved: {sens_path.name}")

    # Find and report the actual minimum datum where all β₃ > 0 and sig.
    all_valid = sens_df.groupby("ref_depth").agg(
        all_pos=("beta_3_positive", "all"),
        all_sig=("beta_3_sig", "all"),
    ).reset_index()
    valid_datums = all_valid[all_valid["all_pos"] & all_valid["all_sig"]]
    if len(valid_datums) > 0:
        empirical_min = float(valid_datums["ref_depth"].min())
        print(f"    Minimum datum for all β₃ > 0 & p < 0.05: {empirical_min:.1f} m")
        if abs(empirical_min - DRAINAGE_DATUM) > 0.15:
            print(f"    [NOTE] Empirical minimum ({empirical_min:.1f} m) differs "
                  f"from DRAINAGE_DATUM ({DRAINAGE_DATUM:.1f} m) — consider "
                  "updating config.DRAINAGE_DATUM.")
    else:
        print("    [WARNING] No reference depth produces all-positive, "
              "all-significant β₃ — check datum sensitivity figure.")

    sens_fig_path = DIR_03 / "03_08_datum_sensitivity.png"
    make_datum_sensitivity_figure(sens_df, DRAINAGE_DATUM, sens_fig_path)

    # ---- Bootstrap CIs on centroid fits ----
    print(f"\n -> Bootstrapping centroid fits (B = {N_BOOTSTRAP}, "
          f"seed = {BOOTSTRAP_SEED})...")
    boot_df = bootstrap_centroid_fits(cluster_df, wells_clean, climate,
                                        upstand_lookup, well_col_lookup)
    boot_path = DIR_03 / "03_05_bootstrap_ci.csv"
    boot_df.to_csv(boot_path, index=False)
    print(f" -> Saved: {boot_path.name}")

    # ---- Leave-one-out per cluster ----
    print("\n -> Leave-one-well-out centroid fits...")
    loo_df = leave_one_out_fits(cluster_df, wells_clean, climate,
                                  upstand_lookup, well_col_lookup)
    loo_path = DIR_03 / "03_06_leave_one_out.csv"
    loo_df.to_csv(loo_path, index=False)
    print(f" -> Saved: {loo_path.name}")

    # ---- C1 Lake pre/post-2018 split ----
    print("\n -> C1 Lake pre/post-2018 split-window diagnostic...")
    split_df = c1_split_window_diagnostic(centroids, cluster_df, wells_clean,
                                            climate, upstand_lookup,
                                            well_col_lookup)
    split_path = DIR_03 / "03_07_c1_split_window.csv"
    split_df.to_csv(split_path, index=False)
    print(f" -> Saved: {split_path.name}")

    # ---- Summary table with heterogeneity flag ----
    summary_df = build_summary_table(mech_df, boot_df, cluster_df)
    summary_df.to_csv(OUT_03_CLUSTER_SUMMARY, index=False)
    print(f" -> Saved: {OUT_03_CLUSTER_SUMMARY.name}")

    # ---- Signatures figure (with bootstrap error bars) ----
    make_signatures_figure(mech_df, boot_df, OUT_03_SIGNATURES)

    # ---- Regional averages exports ----
    export_regional_averages(centroids, climate, master_df)
    export_regional_averages_maod(cluster_df, climate)

    # ---- Cluster peak months (consumed by scripts 11, 11b) ----
    print("\n -> Exporting cluster peak months...")
    export_cluster_peak_months(centroids)

    # ---- Hard halt if centroid sign assertions failed ----
    # Deferred until here so the diagnostic tables (03_04/05/06/07) and the
    # signatures figure are saved — the whole point of the LOO and bootstrap
    # diagnostics is to investigate exactly this kind of failure. Downstream
    # scripts that try to consume a summary table containing a negative beta_1
    # should still fail loudly, but the investigator now has the diagnostic
    # outputs to work with.
    if violations:
        print("\n" + "!" * 70)
        print("!! CENTROID SIGN ASSERTIONS FAILED                               !!")
        print("!! (diagnostic tables and figure saved; summary reflects NaNs on  !!")
        print("!!  the LCSC column for the offending cluster — see stdout above) !!")
        print("!" * 70)
        raise AssertionError(
            f"{len(violations)} centroid SSM sign violation(s). "
            "See stdout above."
        )

    print("\n03 complete.")


if __name__ == "__main__":
    main()
