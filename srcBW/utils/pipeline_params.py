"""
utils/pipeline_params.py
========================
Consolidated scenario parameter file — single source of truth for all
downstream scripts that need per-cluster SSM coefficients, Sy, head
displacement, forestry multipliers, and summer climate means.

Architecture
------------
Script 01 calls write_initial_params() to create the file with defaults
and the values it can compute (summer climate, h_disp, forest flag).

Later scripts call update_params() to fill in their values:
  - Script 03: β₁, β₂, β₃
  - Script 10e: clearfell_b2_mult, thinning_b2_mult
  - Script 17: Sy

Downstream consumers (09b, 09d, 19, 21) call load_params() to get
everything in one read.

The file has a 'source_pass' column:
  - "defaults" — values are placeholders from the initial write
  - "pipeline" — values have been updated by the producing script

If source_pass contains any "defaults" entries, a warning is printed
recommending a second pipeline run.

File location: outputs/01_data_prep/pipeline_scenario_params.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path


def _params_path():
    """Return the path to the pipeline scenario params CSV."""
    from utils.paths import DIR_01
    return DIR_01 / "pipeline_scenario_params.csv"


# ============================================================================
# DEFAULTS — used on first pass before upstream scripts have run
# ============================================================================
_DEFAULTS = {
    "beta_1": 3.5,
    "beta_2": 1.5,
    "beta_3": 0.025,
    "Sy": 0.25,
    "clearfell_b2_mult": 1.10,
    "thinning_b2_mult": 1.05,
    "peak_month": 2,   # February — typical for most clusters
}


# ============================================================================
# WRITER — called by Script 01
# ============================================================================

def write_initial_params(wells_clean, climate):
    """Write pipeline_scenario_params.csv, using real values where available.

    Called by Script 01 after computing climate and well data.
    Always populates: summer_P, summer_PET, forest flag.

    Opportunistically reads from existing upstream outputs:
      - 03_master_data.csv → h_disp, and
        03_03_cluster_mechanistic_coefficients.csv → β₁, β₂, β₃
      - 10e_01_coefficient_shifts.csv → clearfell_b2_mult, thinning_b2_mult
      - 17_wtf_01_sy_estimates.csv → Sy

    If any upstream file is missing (e.g. first-ever run), defaults are
    used for those fields and the source column is set to "defaults".

    Parameters
    ----------
    wells_clean : pd.DataFrame
        Clean well depth time series (index=dates, columns=well names).
    climate : pd.DataFrame
        Monthly climate with P_m and PET columns.
    """
    from utils.config import DRAINAGE_DATUM, FOREST_CIDS, BROADLEAF_B2_SUMMER, BROADLEAF_B2_WINTER
    from utils.paths import (
        INT_MASTER_DATA, OUT_03_MECHANISTIC_TABLE,
        OUT_10E_COEFF_SHIFTS, INT_WTF_WELL_SY,
    )

    # Summer climate means
    summer = climate[climate.index.month.isin([6, 7, 8, 9])]
    summer_P = float(summer["P_m"].mean())
    summer_PET = float(summer["PET"].mean())

    clusters = [1, 2, 3, 4, 5]

    # ── Try to load β coefficients from Script 03 ────────────────────────
    beta_by_cluster = {}
    if OUT_03_MECHANISTIC_TABLE.exists():
        try:
            coeff = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
            for _, row in coeff.iterrows():
                cl = int(row["Cluster"])
                beta_by_cluster[cl] = {
                    "b1": float(row["beta_1_recharge"]),
                    "b2": float(row["beta_2_atmospheric_draw"]),
                    "b3": float(row["beta_3_drainage"]),
                }
            print(f"  Pipeline params: β coefficients loaded from {OUT_03_MECHANISTIC_TABLE.name}")
        except Exception as e:
            print(f"  Pipeline params: could not read β from {OUT_03_MECHANISTIC_TABLE.name}: {e}")

    # ── Try to load h_disp from Script 01/03 master data ─────────────────
    h_disp_by_cluster = {}
    if INT_MASTER_DATA.exists():
        try:
            master = pd.read_csv(INT_MASTER_DATA)
            master["match"] = master["Name_Original"].str.lower().str.replace(" ", "")
            wells_lower = wells_clean.copy()
            wells_lower.columns = wells_lower.columns.str.lower().str.replace(" ", "")
            for cl in clusters:
                cl_wells = master[master["Cluster"] == cl]["match"].tolist()
                available = [w for w in cl_wells if w in wells_lower.columns]
                if available:
                    mean_depth = wells_lower[available].mean().mean()
                    h_disp_by_cluster[cl] = DRAINAGE_DATUM + mean_depth
            print(f"  Pipeline params: h_disp loaded from {INT_MASTER_DATA.name}")
        except Exception as e:
            print(f"  Pipeline params: could not read h_disp: {e}")

    # ── Try to load B2 multipliers from Script 10e ───────────────────────
    clearfell_b2 = _DEFAULTS["clearfell_b2_mult"]
    thinning_b2 = _DEFAULTS["thinning_b2_mult"]
    b2_source = "defaults"
    if OUT_10E_COEFF_SHIFTS.exists():
        try:
            from utils.clearfell_common import load_clearfell_b2_multiplier
            cf, thin, _ = load_clearfell_b2_multiplier(verbose=False)
            clearfell_b2 = cf
            thinning_b2 = thin
            b2_source = "pipeline"
            print(f"  Pipeline params: β₂ multipliers loaded "
                  f"(clearfell={cf:.4f}, thinning={thin:.4f})")
        except Exception as e:
            print(f"  Pipeline params: could not read B2 multipliers: {e}")

    # ── Try to load Sy from Script 17 ────────────────────────────────────
    sy_by_cluster = {}
    if INT_WTF_WELL_SY.exists():
        try:
            sy_df = pd.read_csv(INT_WTF_WELL_SY)
            sy_median = sy_df.groupby("Cluster")["Sy_median"].median()
            for cl in clusters:
                if cl in sy_median.index:
                    sy_by_cluster[cl] = float(sy_median[cl])
            print(f"  Pipeline params: Sy loaded from {INT_WTF_WELL_SY.name} "
                  f"({len(sy_by_cluster)} clusters)")
        except Exception as e:
            print(f"  Pipeline params: could not read Sy: {e}")

    # ── Try to load peak months from Script 03 ───────────────────────────
    from utils.paths import INT_CLUSTER_PEAK_MONTHS
    peak_by_cluster = {}
    if INT_CLUSTER_PEAK_MONTHS.exists():
        try:
            pm_df = pd.read_csv(INT_CLUSTER_PEAK_MONTHS)
            for _, row in pm_df.iterrows():
                cl = int(row["cluster_id"])
                peak_by_cluster[cl] = int(row["peak_month"])
            print(f"  Pipeline params: peak months loaded from "
                  f"{INT_CLUSTER_PEAK_MONTHS.name}")
        except Exception as e:
            print(f"  Pipeline params: could not read peak months: {e}")

    # ── Build rows ───────────────────────────────────────────────────────
    rows = []
    for cl in clusters:
        beta = beta_by_cluster.get(cl, None)
        h_disp = h_disp_by_cluster.get(cl, None)
        sy = sy_by_cluster.get(cl, None)
        peak = peak_by_cluster.get(cl, None)

        rows.append({
            "Cluster": f"C{cl}",
            "beta_1": round(beta["b1"], 4) if beta else _DEFAULTS["beta_1"],
            "beta_2": round(beta["b2"], 4) if beta else _DEFAULTS["beta_2"],
            "beta_3": round(beta["b3"], 4) if beta else _DEFAULTS["beta_3"],
            "Sy": round(sy, 4) if sy else _DEFAULTS["Sy"],
            "h_disp": round(h_disp, 4) if h_disp else round(DRAINAGE_DATUM - 0.5, 4),
            "forest": cl in FOREST_CIDS,
            "peak_month": peak if peak else _DEFAULTS["peak_month"],
            "clearfell_b2_mult": round(clearfell_b2, 4),
            "thinning_b2_mult": round(thinning_b2, 4),
            "broadleaf_b2_summer": BROADLEAF_B2_SUMMER,
            "broadleaf_b2_winter": BROADLEAF_B2_WINTER,
            "summer_P": round(summer_P, 6),
            "summer_PET": round(summer_PET, 6),
            "source_beta": "pipeline" if beta else "defaults",
            "source_Sy": "pipeline" if sy else "defaults",
            "source_peak_month": "pipeline" if peak else "defaults",
            "source_b2_mult": b2_source,
            "source_h_disp": "pipeline" if h_disp else "defaults",
            "source_climate": "pipeline",
        })

    df = pd.DataFrame(rows)
    out_path = _params_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    # Summary
    source_cols = [c for c in df.columns if c.startswith("source_")]
    n_pipeline = sum(1 for c in source_cols if (df[c] == "pipeline").all())
    n_defaults = sum(1 for c in source_cols if (df[c] == "defaults").any())
    print(f"  Pipeline params written: {out_path.name} "
          f"({len(df)} clusters, {n_pipeline}/{len(source_cols)} fields from pipeline)")
    if n_defaults > 0:
        default_fields = [c.replace("source_", "")
                         for c in source_cols if (df[c] == "defaults").any()]
        print(f"  NOTE: default values for: {', '.join(default_fields)}. "
              f"Run full pipeline to populate.")
    else:
        print(f"  All fields populated from pipeline outputs.")

    return out_path


# ============================================================================
# UPDATERS — called by Scripts 03, 10e, 17
# ============================================================================

def update_beta_coefficients(coeff_df):
    """Update β₁, β₂, β₃ from Script 03's cluster mechanistic table.

    Parameters
    ----------
    coeff_df : pd.DataFrame
        Must have columns: Cluster, beta_1_recharge,
        beta_2_atmospheric_draw, beta_3_drainage.
    """
    path = _params_path()
    if not path.exists():
        print(f"  WARNING: {path.name} not found — skipping β update")
        return

    df = pd.read_csv(path)
    for _, row in coeff_df.iterrows():
        cl = f"C{int(row['Cluster'])}"
        mask = df["Cluster"] == cl
        if mask.any():
            df.loc[mask, "beta_1"] = round(float(row["beta_1_recharge"]), 4)
            df.loc[mask, "beta_2"] = round(float(row["beta_2_atmospheric_draw"]), 4)
            df.loc[mask, "beta_3"] = round(float(row["beta_3_drainage"]), 4)
            df.loc[mask, "source_beta"] = "pipeline"

    df.to_csv(path, index=False)
    print(f"  Pipeline params updated: β coefficients from Script 03")


def update_b2_multipliers(clearfell_mult, thinning_mult):
    """Update clearfell/thinning β₂ multipliers from Script 10e.

    Parameters
    ----------
    clearfell_mult : float
    thinning_mult : float
    """
    path = _params_path()
    if not path.exists():
        print(f"  WARNING: {path.name} not found — skipping B2 update")
        return

    df = pd.read_csv(path)
    df["clearfell_b2_mult"] = round(clearfell_mult, 4)
    df["thinning_b2_mult"] = round(thinning_mult, 4)
    df["source_b2_mult"] = "pipeline"

    df.to_csv(path, index=False)
    print(f"  Pipeline params updated: β₂ multipliers from Script 10e "
          f"(clearfell={clearfell_mult:.4f}, thinning={thinning_mult:.4f})")


def update_specific_yield(sy_by_cluster):
    """Update per-cluster Sy from Script 17.

    Parameters
    ----------
    sy_by_cluster : dict
        {cluster_id: Sy_value}, e.g. {1: 0.21, 2: 0.29, ...}
    """
    path = _params_path()
    if not path.exists():
        print(f"  WARNING: {path.name} not found — skipping Sy update")
        return

    df = pd.read_csv(path)
    for cl_id, sy_val in sy_by_cluster.items():
        cl = f"C{cl_id}" if isinstance(cl_id, int) else cl_id
        mask = df["Cluster"] == cl
        if mask.any():
            df.loc[mask, "Sy"] = round(float(sy_val), 4)
            df.loc[mask, "source_Sy"] = "pipeline"

    df.to_csv(path, index=False)
    print(f"  Pipeline params updated: Sy from Script 17 "
          f"({len(sy_by_cluster)} clusters)")


def update_h_disp(h_disp_by_cluster):
    """Update per-cluster h_disp (e.g. after Script 01 re-run with new data).

    Parameters
    ----------
    h_disp_by_cluster : dict
        {cluster_id: h_disp_value}
    """
    path = _params_path()
    if not path.exists():
        print(f"  WARNING: {path.name} not found — skipping h_disp update")
        return

    df = pd.read_csv(path)
    for cl_id, h_val in h_disp_by_cluster.items():
        cl = f"C{cl_id}" if isinstance(cl_id, int) else cl_id
        mask = df["Cluster"] == cl
        if mask.any():
            df.loc[mask, "h_disp"] = round(float(h_val), 4)
            df.loc[mask, "source_h_disp"] = "pipeline"

    df.to_csv(path, index=False)


def update_peak_months(peak_by_cluster):
    """Update per-cluster peak water-table month from Script 03.

    Parameters
    ----------
    peak_by_cluster : dict
        {cluster_id: peak_month}, e.g. {1: 2, 2: 1, ...}
    """
    path = _params_path()
    if not path.exists():
        print(f"  WARNING: {path.name} not found — skipping peak_month update")
        return

    df = pd.read_csv(path)
    for cl_id, pm in peak_by_cluster.items():
        cl = f"C{cl_id}" if isinstance(cl_id, int) else cl_id
        mask = df["Cluster"] == cl
        if mask.any():
            df.loc[mask, "peak_month"] = int(pm)
            df.loc[mask, "source_peak_month"] = "pipeline"

    df.to_csv(path, index=False)
    print(f"  Pipeline params updated: peak months from Script 03 "
          f"({len(peak_by_cluster)} clusters)")


# ============================================================================
# READER — called by downstream scripts (09b, 09d, 19, 21)
# ============================================================================

def load_params(warn_defaults=True):
    """Load the consolidated pipeline scenario parameters.

    Returns
    -------
    dict with keys:
        "clusters" : dict {cname: {b1, b2, b3, Sy, h_disp, forest}}
        "clearfell_b2_mult" : float
        "thinning_b2_mult" : float
        "broadleaf_b2_summer" : float
        "broadleaf_b2_winter" : float
        "summer_P" : float
        "summer_PET" : float
        "all_pipeline" : bool — True if no defaults remain

    Raises
    ------
    FileNotFoundError if the params file doesn't exist (pipeline not run).
    """
    path = _params_path()
    if not path.exists():
        raise FileNotFoundError(
            f"{path.name} not found. Run Script 01 (data prep) first.")

    df = pd.read_csv(path)

    # Check for remaining defaults
    source_cols = [c for c in df.columns if c.startswith("source_")]
    has_defaults = any((df[c] == "defaults").any() for c in source_cols)

    if has_defaults and warn_defaults:
        default_fields = [c.replace("source_", "")
                         for c in source_cols if (df[c] == "defaults").any()]
        print(f"  WARNING: pipeline_scenario_params.csv contains default "
              f"values for: {', '.join(default_fields)}")
        print(f"  Run the full pipeline twice for canonical values.")

    # Build cluster params dict
    clusters = {}
    peak_months = {}
    for _, row in df.iterrows():
        clusters[row["Cluster"]] = {
            "b1": float(row["beta_1"]),
            "b2": float(row["beta_2"]),
            "b3": float(row["beta_3"]),
            "Sy": float(row["Sy"]),
            "h_disp": float(row["h_disp"]),
            "forest": bool(row["forest"]),
            "peak_month": int(row["peak_month"]),
        }
        peak_months[row["Cluster"]] = int(row["peak_month"])

    return {
        "clusters": clusters,
        "peak_months": peak_months,
        "clearfell_b2_mult": float(df["clearfell_b2_mult"].iloc[0]),
        "thinning_b2_mult": float(df["thinning_b2_mult"].iloc[0]),
        "broadleaf_b2_summer": float(df["broadleaf_b2_summer"].iloc[0]),
        "broadleaf_b2_winter": float(df.get("broadleaf_b2_winter",
                                             pd.Series([0.87])).iloc[0]),
        "summer_P": float(df["summer_P"].iloc[0]),
        "summer_PET": float(df["summer_PET"].iloc[0]),
        "all_pipeline": not has_defaults,
    }
