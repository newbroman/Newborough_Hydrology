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

__version__ = "1.6.0"  # Hollingham (2026) — 2026-08-22. Adds
#   uniform_residual_mm_yr, the first-pass default for the measured uniform
#   decline that replaces c as Script 37b's uniform driver row (D-057).
#   climate_c_mm_yr is retained: nothing consumes it now, but removing a
#   documented default silently is how a first pass starts failing quietly.
#
# v1.5.0
#   refreshed -6.35 -> 0.18 to match the committed 25_01. It had drifted in sign
#   as well as magnitude, and it now backs a drawn figure element
#   (mechanism_fig_utils' far-field fallback) as well as Script 37b, so a
#   fallback that fires would have drawn a fall where the fit gives a rise —
#   the v1.2.1 lambda lesson, repeated.
#
# v1.4.0 (2026-08-19). D-043: the four
#   far-field fallbacks added in 1.3.0 are removed again with the band they
#   stood in for — farfield_sum_lo_mm_yr, farfield_sum_hi_mm_yr,
#   mech_farfield_lo_5yr_mm, mech_farfield_hi_5yr_mm. A fallback with no live
#   reader is a default waiting to be mistaken for a result. The 1.3.0
#   retirement of mech_climate_20yr_mm STANDS: nothing draws a spatially
#   uniform amplitude on the 09f/09g figures. climate_c_mm_yr is still retained
#   for Script 37b, which reads it.
#
# v1.3.0 (2026-08-19): far-field fallbacks added for the 09f band (D-039,
#   D-042); mech_climate_20yr_mm retired. Superseded in part by 1.4.0.
#
# v1.2.3  # Hollingham (2026) — 2026-08-19. Reads the per-well
#   WTF Sy table from OUT_18_WELL_SY_TABLE; INT_WTF_WELL_SY is retired
#   (D-038). Pure path/symbol change, values identical.
#
# v1.2.2  # Hollingham (2026) — 2026-08-18
# v1.2.2 (2026-08-18): _DEFAULTS gains ceh36_scrape_response_m, so Script 20's
#   fallback for the scrape H0 anchor reads a documented default instead of a
#   published result typed into an except branch.
# v1.2.1 (2026-08-18): _DEFAULTS["drawdown_lambda_m"] refreshed 224.9 -> 228.1 to
#   match the committed 20_report_numbers.csv. A first-pass fallback that has
#   drifted from the value it stands in for is worse than no fallback, because
#   the warning says "default" and the reader assumes it is the documented one.
# v1.2.0 (2026-08-18): the scenario-parameter store keeps full precision.
#   beta_1/2/3, Sy, h_disp, the two B2 multipliers and the summer climate means
#   were rounded to 4 (or 6) decimals on the way IN, so every consumer computed
#   from a truncated number and the loss was invisible - it looked like a
#   display convention sitting in a data store. Rounding belongs at the point of
#   rendering, where the 3-decimal output convention applies; the store carries
#   what the pipeline computed. _DEFAULTS are unchanged: those are documented
#   fallback constants, quoted at the precision they were agreed at.
#   NOTE this moves consumer numbers in the fifth significant figure - Scripts
#   09d, 19, 21 and 37b read these values - so their outputs will differ
#   slightly on the next run. That is the correction, not a side effect.
# Module versioning introduced 2026-08-13 (pre-1.1.0 history via CHANGELOG_delta
# files). Bump on ANY edit, as for pipeline scripts.
# v1.1.1 (2026-08-13): moved `from __future__ import annotations` above the
#   __version__ assignment so the module imports — the v1.1.0 header put the
#   assignment first, which is a SyntaxError ("future import must occur at the
#   beginning of the file") and blocked every script importing pipeline_params.
# v1.1.0 (2026-08-13): __version__ introduced; no functional change.


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
    # --- Reach-figure fallbacks (Script 09f) ---------------------------------
    # Documented Newborough-2026 values used on a first-pass run before the
    # upstream scripts that produce them have executed. Script 09f reads the
    # live CSVs first (20_report_numbers, 25_01_panel_fit_parameters, 09d_01,
    # 10a_report_numbers) and falls back to these with a console warning. Any
    # future script needing these first-pass values should read them via
    # default_value().
    # REFRESHED 2026-08-28 against the committed CSVs. Four of the six below
    # had drifted, and the drift was invisible because these values are only
    # read when the live CSV is missing — a path that, by construction, nobody
    # exercises on a complete run. A fallback that is never taken is never
    # checked, and a fallback that IS taken is taken on the run where nothing
    # else is available to notice.
    #
    # Two of the four matter beyond tidiness. `clearfell_recovery_mm` was 119.6
    # against a committed 113.09 — M31 raised exactly this: Script 37b's
    # clearfell anchor falls back to it with a warning and continues, so a
    # failed CSV read would compute the whole site-integrated footing on a
    # superseded step. And `coast_delta0_mm_yr` / `coast_reach_L_m` were
    # -29.0 / 894, which is the PRE-D-046 parameter block T-18c spent a morning
    # clearing out of the Methods Supplement. Leaving the same pair here as the
    # pipeline's own fallback is how it would have come back.
    "drawdown_lambda_m":        226.4,   # 20_report_numbers.csv (drawdown_lambda
                                         # = 226.442); was 228.1, refreshed
                                         # 2026-08-28
    "coast_delta0_mm_yr":       -31.33,  # 25_01 forest_free/linear_capped δ₀;
                                         # was -29.0, the pre-D-046 value
    "coast_reach_L_m":          895.0,   # 25_01 forest_free/linear_capped L;
                                         # was 894.0, the pre-D-046 value
    "scrape_offsite_100m_vol":  -31.2,   # 09d_01 Scraping (off-site 100 m)
                                         # mm w.e./month; was -30.3
    "clearfell_recovery_mm":    113.1,   # 10a ANCOVA_Forest_Impact_clearfell_step
                                         # ×1000 = 113.09; was 119.6 — see M31
    "ceh36_scrape_response_m":  0.1294,  # 09a paired BACI, CEH36 Pure_Scraping vs
                                         # CEH4; the H0 anchor for the scrape-drain
                                         # maps in Script 20
    "uniform_residual_mm_yr":  -11.0,   # mean over the open-dune clusters of
                                         # (balanced observed decline − modelled coastal
                                         # gradient), 25_03_cluster_partition.csv. The
                                         # spatially-uniform decline the footing carries
                                         # (D-057). A CENTRAL ESTIMATE, not a resolved
                                         # rate: the clusters agree because their
                                         # year-to-year swings are common-mode, so the
                                         # agreement shows uniformity and does not lower
                                         # the detection floor on the magnitude
    "climate_c_mm_yr":           0.18,   # 25_01 forest_free/linear_capped c_mm_yr,
                                         # refreshed 2026-08-19 from the committed
                                         # value; was -6.35, stale by the sign as
                                         # well as the magnitude. NOT a climate
                                         # background and NOT a rate to take abs()
                                         # of: c is not separately identified
                                         # (D-039). Read by Script 37b and by
                                         # mechanism_fig_utils' far-field fallback.
    "wmc3_drawdown_mm":         -55.2,   # 10m WMC3_BACI_DiD_step_2015_scraping ×1000 (measured off-cut)
    "wmc3_distance_m":          262.4,   # 09b_01 wmc3 dist_m (CEH36 -> WMC3 separation)
    # --- Mechanism-diagram fallbacks (Script 09g) ----------------------------
    # Edge amplitudes (mm) for the §5.8 mechanism diagrams. Live source is
    # 09f_01_reach_profile.csv ROW 0 (distance 0) — one column per driver —
    # read via mechanism_fig_utils.load_amplitudes(); the measured scrape
    # off-cut reuses "wmc3_drawdown_mm" above (10m WMC3 BACI). 09g runs after
    # 09f in Phase 17, so these engage only on a partial/interrupted run.
    "mech_forest_standing_mm":  -150.0,  # 09f_01 standing_pine_head_mm
    "mech_coastal_5yr_mm":      -145.15, # 09f_01 coastal_5yr_head_mm
    "mech_scrape_cut_rise_mm":   129.43, # 09f_01 scrape_head_mm (CEH36 cut rise)
    "mech_thinned_mm":           -75.0,  # 09f_01 thinned_forest_head_mm
    "mech_coastal_storm_mm":     -20.99, # 09f_01 coastal_6m_storm_head_mm
    "clearfell_summer_step_mm":   46.3,  # 10a ANCOVA_Forest_Impact_clearfell_step_summer x1000
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
      - 18_wtf_01_well_sy_estimates.csv → Sy

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
        OUT_10E_COEFF_SHIFTS, OUT_18_WELL_SY_TABLE, INT_CLUSTER_PEAK_MONTHS,
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
    if OUT_18_WELL_SY_TABLE.exists() and clusters:
        try:
            sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
            sy_median = sy_df.groupby("Cluster")["Sy_median"].median()
            for cl in clusters:
                if cl in sy_median.index:
                    sy_by_cluster[cl] = float(sy_median[cl])
            print(f"  Pipeline params: Sy loaded from {OUT_18_WELL_SY_TABLE.name} "
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
            "beta_1": float(beta["b1"]) if beta else _DEFAULTS["beta_1"],
            "beta_2": float(beta["b2"]) if beta else _DEFAULTS["beta_2"],
            "beta_3": float(beta["b3"]) if beta else _DEFAULTS["beta_3"],
            "Sy": float(sy) if sy else _DEFAULTS["Sy"],
            "h_disp": float(h_disp) if h_disp else float(DRAINAGE_DATUM - 0.5),
            "forest": cl in FOREST_CIDS,
            "peak_month": peak if peak else _DEFAULTS["peak_month"],
            "clearfell_b2_mult": float(clearfell_b2),
            "thinning_b2_mult": float(thinning_b2),
            "broadleaf_b2_summer": BROADLEAF_B2_SUMMER,
            "broadleaf_b2_winter": BROADLEAF_B2_WINTER,
            "summer_P": float(summer_P),
            "summer_PET": float(summer_PET),
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
        "h_disp": float(DRAINAGE_DATUM - 0.5),
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
        df.loc[mask, "beta_1"] = float(row["beta_1_recharge"])
        df.loc[mask, "beta_2"] = float(row["beta_2_atmospheric_draw"])
        df.loc[mask, "beta_3"] = float(row["beta_3_drainage"])
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
    df["clearfell_b2_mult"] = float(clearfell_mult)
    df["thinning_b2_mult"] = float(thinning_mult)
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
            df.loc[mask, "Sy"] = float(sy_val)
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
            df.loc[mask, "h_disp"] = float(h_val)
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

def default_value(key):
    """Return a documented first-pass default from _DEFAULTS.

    Public accessor so scripts (e.g. Script 09f) can fall back to the
    centralised first-pass defaults without importing the private dict.
    Raises KeyError if the key is not a defined default.
    """
    if key not in _DEFAULTS:
        raise KeyError(
            f"{key!r} is not a defined pipeline default; "
            f"available: {sorted(_DEFAULTS)}")
    return _DEFAULTS[key]


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
