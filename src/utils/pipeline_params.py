"""
utils/pipeline_params.py
========================
Consolidated scenario parameter file — single source of truth for all
downstream scripts that need per-cluster SSM coefficients, Sy, head
displacement, forestry multipliers, summer climate means, the realised
cluster partition, and the analyst-set tunables for the cluster-validation
diagnostics (Scripts 31 / 31b).

Architecture
------------
Script 01 calls write_initial_params() to create the file with the values
it can compute (summer climate, h_disp, forest flag) over the cluster set
**derived from the committed pipeline partition** — never a hard-coded K.

Later scripts call update_params() to fill in their values:
  - Script 03: β₁, β₂, β₃  (also upserts rows for any realised cluster that
               did not yet exist, so the per-cluster scaffold is seeded from
               the actual partition even on a pristine first run)
  - Script 10e: clearfell_b2_mult, thinning_b2_mult
  - Script 17: Sy

Downstream consumers (09b, 09d, 19, 21, 31, 31b) call load_params() /
get_cluster_ids() to read everything in one place.

The cluster count (K) and the cluster ids are ALWAYS derived from a
pipeline run via get_cluster_ids(); they are never written as a literal
anywhere in the codebase.  The committed partition output
(03_master_data.csv, falling back to 02_cluster_stats.csv or the Script 03
mechanistic table) is the single source of truth for the partition.

The file has a 'source_pass' column:
  - "defaults" — values are placeholders from the initial write
  - "pipeline" — values have been updated by the producing script

If source_pass contains any "defaults" entries, a warning is printed
recommending a second pipeline run.

File location: outputs/01_data_prep/pipeline_scenario_params.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _params_path():
    """Return the path to the pipeline scenario params CSV."""
    from utils.paths import DIR_01
    return DIR_01 / "pipeline_scenario_params.csv"


# ============================================================================
# CLUSTER PARTITION — derived from the pipeline run, never hard-coded
# ============================================================================
# Source priority: the committed partition outputs, most-authoritative first.
# K (the number of clusters) and the cluster ids are read from whichever of
# these a pipeline run has produced; nothing in the codebase asserts "k = 5".
def _partition_sources():
    from utils.paths import (
        INT_MASTER_DATA, INT_CLUSTER_STATS, OUT_03_MECHANISTIC_TABLE,
    )
    return [INT_MASTER_DATA, INT_CLUSTER_STATS, OUT_03_MECHANISTIC_TABLE]


def get_cluster_ids(strict: bool = True, source=None) -> list[int]:
    """Return the realised cluster ids as a sorted list of ints.

    The partition is read from a committed pipeline output (the 'Cluster'
    column of 03_master_data.csv, falling back to 02_cluster_stats.csv or the
    Script 03 mechanistic table).  K therefore always reflects an actual
    clustering run rather than a hard-coded value.

    Parameters
    ----------
    strict : bool
        If True (default), raise FileNotFoundError when no committed
        partition exists — downstream diagnostics must run against a real
        partition, not a literal.  If False, return [] so first-pass writers
        (Script 01, before Script 02 has run) can degrade gracefully.
    source : path-like, optional
        Explicit partition CSV to read instead of the default search order.

    Returns
    -------
    list[int]  e.g. [1, 2, 3, 4, 5]
    """
    candidates = [Path(source)] if source is not None else _partition_sources()
    for path in candidates:
        if Path(path).exists():
            df = pd.read_csv(path)
            if "Cluster" not in df.columns:
                continue
            ids = pd.to_numeric(df["Cluster"], errors="coerce").dropna().astype(int)
            if not ids.empty:
                return sorted(ids.unique().tolist())
    if strict:
        searched = ", ".join(Path(p).name for p in candidates)
        raise FileNotFoundError(
            "No committed cluster partition found (searched: "
            f"{searched}). Run the clustering pipeline (Scripts 01–03) first; "
            "the cluster count must come from a pipeline run, not a literal."
        )
    return []


def get_n_clusters(strict: bool = True, source=None) -> int:
    """Return K — the realised number of clusters from the pipeline run."""
    return len(get_cluster_ids(strict=strict, source=source))


# ============================================================================
# DIAGNOSTIC PARAMETERS — Scripts 31 / 31b (cluster-partition validation)
# ============================================================================
# Analyst-set methodology tunables for the cluster-validation diagnostics.
# Housed in this parameters file (not config.py) so every tunable input lives
# in one discoverable place.  These are inputs to the analysis, not values
# produced by a pipeline run.
CV_KNN_K            = 6           # neighbours for spatial weights (Moran, join-count)
CV_N_PERM           = 10000       # permutations for spatial significance tests
CV_EDGE_BUFFER_M    = 50.0        # ± band (m) around the forest boundary => "borderline"
CV_MIN_YEAR_OBS     = 6           # min monthly obs in a year to use it for amplitude
CV_DTW_WINDOW       = 12          # Sakoe-Chiba band (months) for DTW distance
CV_AMPLITUDE_MONTHS = (6, 7, 8, 9)  # months used for the summer-amplitude statistic
CV_RNG_SEED         = 20260625    # fixed seed for reproducible permutation/bootstrap


# ============================================================================
# PARTITION PARAMETER — the clustering target K (an INPUT, fixed by the analyst)
# ============================================================================
# K is the ONE value that must be supplied to the clustering step (Script 02):
# the dendrogram cannot discover it, because automatic selection on silhouette
# peaks at the trivial two-way split (k=2, silhouette 0.46) rather than the five
# physically-distinct hydrogeological clusters (k=5, silhouette 0.40; Ward
# merge-distance and Calinski-Harabasz both support five). The partition is
# therefore analyst-FIXED at five and must never be auto-selected.
#
# This is the single legitimate home for the literal "5": it is the requested
# clustering target. Everything downstream reads the *realised* partition back
# from the committed output via get_cluster_ids() and never re-asserts it.
#
# A run may override the target via the NRG_N_CLUSTERS environment variable
# (e.g. run_analysis.py --clusters N), so the run parameters can request the
# count explicitly; absent that, the documented default applies.
REQUESTED_N_CLUSTERS = 5  # analyst-fixed clustering target (see note above)


def get_requested_n_clusters() -> int:
    """Return the requested clustering target K (input to Script 02).

    Order of precedence:
      1. NRG_N_CLUSTERS environment variable (set by run_analysis.py --clusters
         N or the full-run prompt), if present and a positive integer;
      2. REQUESTED_N_CLUSTERS (the documented analyst default, 5).

    This is the clustering *target*, not the realised partition. Downstream
    scripts read the realised partition with get_cluster_ids() / get_n_clusters().
    """
    import os
    raw = os.environ.get("NRG_N_CLUSTERS")
    if raw is not None:
        try:
            val = int(raw)
            if val >= 2:
                return val
        except (TypeError, ValueError):
            pass
    return REQUESTED_N_CLUSTERS


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

    The cluster set is derived from the committed partition via
    get_cluster_ids(); on a pristine first run (no partition yet) no
    per-cluster rows are written, and Script 03's update_beta_coefficients
    upserts them from the realised partition later in the same run.

    Opportunistically reads from existing upstream outputs:
      - 03_master_data.csv → h_disp, and
        03_03_cluster_mechanistic_coefficients.csv → β₁, β₂, β₃
      - 10e_01_coefficient_shifts.csv → clearfell_b2_mult, thinning_b2_mult
      - 17_wtf_well_sy.csv → Sy

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
        OUT_10E_COEFF_SHIFTS, INT_WTF_WELL_SY, INT_CLUSTER_PEAK_MONTHS,
    )

    # Summer climate means
    summer = climate[climate.index.month.isin([6, 7, 8, 9])]
    summer_P = float(summer["P_m"].mean())
    summer_PET = float(summer["PET"].mean())

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

    # ── Try to load peak months from Script 03 ───────────────────────────
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

    # ── Determine the cluster set from the pipeline run (never a literal) ─
    clusters = get_cluster_ids(strict=False)
    if not clusters:
        # Pristine first run: no committed partition yet. Fall back to any
        # cluster ids that the upstream per-cluster tables already expose.
        clusters = sorted(set(beta_by_cluster) | set(peak_by_cluster))
    if not clusters:
        print("  Pipeline params: no cluster partition available yet — "
              "per-cluster rows deferred to Script 03 (upsert) on this run.")

    # ── Try to load h_disp from Script 01/03 master data ─────────────────
    h_disp_by_cluster = {}
    if INT_MASTER_DATA.exists() and clusters:
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
    if INT_WTF_WELL_SY.exists() and clusters:
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

    # ── Build rows over the realised cluster set ─────────────────────────
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

    df = pd.DataFrame(rows, columns=_PARAM_COLUMNS)
    out_path = _params_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    # Summary
    source_cols = [c for c in df.columns if c.startswith("source_")]
    n_pipeline = sum(1 for c in source_cols if len(df) and (df[c] == "pipeline").all())
    n_defaults = sum(1 for c in source_cols if (df[c] == "defaults").any())
    print(f"  Pipeline params written: {out_path.name} "
          f"({len(df)} clusters, {n_pipeline}/{len(source_cols)} fields from pipeline)")
    if len(df) == 0:
        print("  NOTE: no cluster rows yet (pristine run). They will be "
              "seeded from the realised partition by Script 03; run the full "
              "pipeline twice for canonical values.")
    elif n_defaults > 0:
        default_fields = [c.replace("source_", "")
                         for c in source_cols if (df[c] == "defaults").any()]
        print(f"  NOTE: default values for: {', '.join(default_fields)}. "
              f"Run full pipeline to populate.")
    else:
        print("  All fields populated from pipeline outputs.")

    return out_path


# Canonical column order — also used to seed upserted rows with a stable schema.
_PARAM_COLUMNS = [
    "Cluster", "beta_1", "beta_2", "beta_3", "Sy", "h_disp", "forest",
    "peak_month", "clearfell_b2_mult", "thinning_b2_mult",
    "broadleaf_b2_summer", "broadleaf_b2_winter", "summer_P", "summer_PET",
    "source_beta", "source_Sy", "source_peak_month", "source_b2_mult",
    "source_h_disp", "source_climate",
]


def _seed_row(cluster_label: str) -> dict:
    """Default-seeded parameter row for a cluster that does not yet exist.

    Used by update_beta_coefficients() to upsert rows for clusters present in
    the realised partition but missing from a pristine-run params file.
    Non-β fields take _DEFAULTS and are flagged 'defaults' so the standard
    second-pass warning still fires until the producing scripts fill them.
    """
    from utils.config import FOREST_CIDS, BROADLEAF_B2_SUMMER, BROADLEAF_B2_WINTER
    from utils.config import DRAINAGE_DATUM
    cl_int = int(str(cluster_label).lstrip("C"))
    return {
        "Cluster": cluster_label,
        "beta_1": _DEFAULTS["beta_1"], "beta_2": _DEFAULTS["beta_2"],
        "beta_3": _DEFAULTS["beta_3"], "Sy": _DEFAULTS["Sy"],
        "h_disp": round(DRAINAGE_DATUM - 0.5, 4),
        "forest": cl_int in FOREST_CIDS,
        "peak_month": _DEFAULTS["peak_month"],
        "clearfell_b2_mult": _DEFAULTS["clearfell_b2_mult"],
        "thinning_b2_mult": _DEFAULTS["thinning_b2_mult"],
        "broadleaf_b2_summer": BROADLEAF_B2_SUMMER,
        "broadleaf_b2_winter": BROADLEAF_B2_WINTER,
        "summer_P": float("nan"), "summer_PET": float("nan"),
        "source_beta": "defaults", "source_Sy": "defaults",
        "source_peak_month": "defaults", "source_b2_mult": "defaults",
        "source_h_disp": "defaults", "source_climate": "defaults",
    }


# ============================================================================
# UPDATERS — called by Scripts 03, 10e, 17
# ============================================================================

def update_beta_coefficients(coeff_df):
    """Update β₁, β₂, β₃ from Script 03's cluster mechanistic table.

    Upserts: a cluster present in the realised partition (coeff_df) but absent
    from the params file is appended (default-seeded for non-β fields), so the
    per-cluster scaffold is created from the actual partition even on a
    pristine first run — no cluster count is ever assumed.

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
    appended = 0
    for _, row in coeff_df.iterrows():
        cl = f"C{int(row['Cluster'])}"
        mask = df["Cluster"] == cl
        if not mask.any():
            df = pd.concat([df, pd.DataFrame([_seed_row(cl)])], ignore_index=True)
            mask = df["Cluster"] == cl
            appended += 1
        df.loc[mask, "beta_1"] = round(float(row["beta_1_recharge"]), 4)
        df.loc[mask, "beta_2"] = round(float(row["beta_2_atmospheric_draw"]), 4)
        df.loc[mask, "beta_3"] = round(float(row["beta_3_drainage"]), 4)
        df.loc[mask, "source_beta"] = "pipeline"

    df = df.sort_values("Cluster").reset_index(drop=True)
    df.to_csv(path, index=False)
    extra = f" (+{appended} cluster row(s) seeded from partition)" if appended else ""
    print(f"  Pipeline params updated: β coefficients from Script 03{extra}")


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
# READER — called by downstream scripts (09b, 09d, 19, 21, 31, 31b)
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
        print("  Run the full pipeline twice for canonical values.")

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
