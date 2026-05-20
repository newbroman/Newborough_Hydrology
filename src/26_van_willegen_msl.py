"""
26_van_willegen_msl.py
======================

Five-year mean spring water level (MSL) — the dune-slack vegetation metric
established by van Willegen et al. (2025) as the best-performing predictor
of Ellenberg EbF community response.

Method (van Willegen et al. 2025, Ecological Indicators 170, 113016):

  * Spring window  : 1st March – 31st May
  * Annual MSL_y   : unweighted mean of {Mar, Apr, May} water levels in
                     hydrology year y. Hydrology year y runs from 1 Jun y-1
                     to 31 May y (paper's "hydrology year B", their default).
  * MSL5(end=y)    : unweighted mean of {MSL_{y-4}, MSL_{y-3}, ..., MSL_y}.
  * MAX_y / MAX5   : annual maximum water level over the same hydrology
                     year, and the 5-year mean of those. The paper notes
                     MAX performed similarly to MSL but was dispreferred
                     because topography can truncate or enhance peaks at
                     individual slacks. Carried here as a secondary metric.

Sign convention: water level is expressed in the depth-below-ground frame
to match the paper (negative = below ground surface). The pipeline's raw
series is in depth-below-pipe-top. Conversion: level_bg = level_pipe +
Upstand_m. A pipe-top column is retained in every CSV for cross-reference
to the rest of the pipeline.

Strictness (per scoping decision 2026-05-20):
  * MSL_MIN_MONTHS_PER_SPRING = 3 — all three of {Mar, Apr, May} must be
    present; one-month interpolation (S.1 limit=1) is allowed to count.
  * MSL_MIN_YEARS_IN_WINDOW   = 5 — all five annual MSLs must be valid for
    the 5-year mean to be reported.

Outputs (DIR_26 / "26_van_willegen_msl/"):
  * 26_msl_annual_per_well.csv      Per (well, hydro_year) annual MSL, MAX
  * 26_msl_5yr_per_well.csv         Per (well, end_year) MSL5, MAX5
  * 26_msl_5yr_per_cluster.csv      Cluster-mean trajectory
  * 26_msl_5yr_latest_per_well.csv  Most-recent valid MSL5, used for the map
  * 26_msl_5yr_map.png              IDW-interpolated MSL5 surface
  * 26_msl_5yr_trajectory.png       Cluster trajectories with Curreli refs
  * 26_msl_5yr_quadrat_wells.png    Per-well trajectories at van-Willegen
                                    co-located quadrat wells (calibrated set)
  * 26_msl_results.txt              Run transcript

References
----------
van Willegen, L., Wallace, H., Curreli, A., Dwyer, C., Ratcliffe, J.,
Jones, D. L., Williams, G., Hollingham, M., & Jones, L. (2025).
Five-year carry-over effects in dune slack vegetation response to
hydrology. Ecological Indicators, 170, 113016.
https://doi.org/10.1016/j.ecolind.2024.113016

Curreli, A. et al. (2013) — SD15b/SD16 threshold reference lines.

Version: 1.0.2 (2026-05-20) — Intervention markers:
  * Cluster trajectory and quadrat plots now show three intervention dates
    (2015 scrape, 2017 clearfell, 2023 re-scrape) as paired vertical lines:
    solid at the first window-end carrying any post-intervention spring
    data, dashed at the first window-end fully post-intervention.
  * Dates imported from `scraping_common.{SCRAPING_DATE, INTERVENTION_DATE,
    SCRAPING_DATE_2}` rather than duplicated locally.

Version: 1.1.2 (2026-05-20) — Method B (cluster-centroid MSL5) added:
  * New function cluster_centroid_trajectory() computes MSL5 from the
    Script 03 cluster-centroid monthly series in 03_regional_averages.csv
    using the same 3/3 + 5/5 strictness as Method A. Pass 3b in main()
    writes the result to OUT_26_5YR_PER_CLUSTER_CENTROID.
  * Rationale: Method A (per-well aggregation across the extended cluster
    network, ~25 wells per cluster in C5) and Method B (cluster centroid
    from the LCSC reference network, ~5 wells in C5) give substantially
    different numbers — mean |Δ| ≈ 0.30 m across the network, max ≈ 0.78 m
    at C4 — because they describe different network compositions, not
    different aggregation algebra. Both are valid; they answer different
    questions.
  * Method A remains the headline monitoring metric (maximum spatial
    coverage; van-Willegen-aligned per-piezometer framework). Method B is
    the SSM-consistent companion (same baseline as cluster β coefficients,
    P_flood, Scripts 11 transfer functions, and Script 26b UKCP18
    projections — Tools A & B).
  * No change to existing outputs. New CSV
    26_msl_5yr_per_cluster_centroid.csv added alongside the existing
    26_msl_5yr_per_cluster.csv.
  * Trajectory figure unchanged (still Method A; van Willegen anchor).
    Script 26b updated separately to use Method B baseline (v1.0.1).

Version: 1.1.1 (2026-05-20) — Map extent harmonisation:
  * MSL5 spatial map now uses the canonical site bounds
    (E 240100–243900, N 362200–365800) matching Script 11b's summer-minima
    figure. Previously the map autoscaled to the IDW surface footprint,
    which extended further than the other publication-quality spatial maps.
  * Bounds added to utils.config as SITE_MAP_EAST_MIN/MAX and
    SITE_MAP_NORTH_MIN/MAX so they are shareable with any future spatial
    script that wants the same canonical extent.

Version: 1.1.0 (2026-05-20) — Conventions compliance:
  * All paths now sourced from utils.paths (no hardcoded path literals).
  * All methodological constants now sourced from utils.config:
    MSL_SPRING_MONTHS, MSL_HYDRO_YEAR_START_MONTH, MSL_DEFAULT_WINDOW_YEARS,
    MSL_MIN_MONTHS_PER_SPRING, MSL_MIN_YEARS_IN_WINDOW,
    MSL_TRAJECTORY_START_YEAR, VW_QUADRAT_WELLS.
  * Intervention-marker colours sourced from utils.config
    (INTERVENTION_COLOUR_SCRAPE, INTERVENTION_COLOUR_CLEARFELL).
  * Intervention dates still sourced from utils.scraping_common (canonical).
  * Output paths via paths.OUT_26_* (added alongside paths.DIR_26 redefine).
  * Greyscale utility relocated from paths.DIR_26 to paths.DIR_27 by sibling
    commit; see CHANGELOG_script26_renumbering_phase13.md.

Version: 1.0.4 (2026-05-20) — Legend headroom (cluster trajectory only):
  * Cluster trajectory y-axis extended below the data range to make
    space for the bottom-left / bottom-right legends. The C3/C4 lines
    no longer sit underneath the legend boxes.
  * Quadrat plot reverted to v1.0.3 axis behaviour: data fills the
    canvas, legend overlap accepted in the bottom-left corner.

Version: 1.0.3 (2026-05-20) — Quadrat-plot label collision fix:
  * Right-edge labels now placed in a dedicated label column with a
    minimum vertical spacing enforced between consecutive labels.
  * Thin connector lines link each label back to the series endpoint.
  * The x-axis is extended on the right to make room for the label
    column without altering the data range.

Version: 1.0.2 (2026-05-20) — Intervention markers and CEH9 audit
  (see CHANGELOG_script26_v1_0_2.md).

Version: 1.0.1 (2026-05-20) — Plot-side refinements:
  * Cluster trajectory and quadrat-wells figures restricted to window
    ends from 2014 onwards (first window fully drawn from post-2010
    network). Per-well CSVs retain the full record.
  * Line plots now break across non-consecutive year gaps (NW6/NW7 lose
    hydrology year 2012 under the strict 3/3 rule and correctly render
    with a true gap rather than a straight-line bridge).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ── Repo imports ──────────────────────────────────────────────────────────────
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils import config, paths
from utils.map_utils import (
    load_dem_hillshade,
    add_idw_surface,
    add_kml_features,
)

# ── Output paths ──────────────────────────────────────────────────────────────
# All paths come from utils.paths so that filename / location changes propagate
# from a single place. The script writes nothing outside DIR_26.
paths.DIR_26.mkdir(parents=True, exist_ok=True)

OUT_ANNUAL    = paths.OUT_26_ANNUAL_PER_WELL
OUT_5YR       = paths.OUT_26_5YR_PER_WELL
OUT_CLUSTER   = paths.OUT_26_5YR_PER_CLUSTER
OUT_CLUSTER_CENTROID = paths.OUT_26_5YR_PER_CLUSTER_CENTROID
OUT_LATEST    = paths.OUT_26_5YR_LATEST_PER_WELL
OUT_MAP       = paths.OUT_26_MAP
OUT_TRAJ      = paths.OUT_26_TRAJECTORY
OUT_QUADRAT   = paths.OUT_26_QUADRAT_WELLS
OUT_TXT       = paths.OUT_26_RESULTS_TXT

# ── Methodological constants from utils.config ────────────────────────────────
# Convention: no methodological numbers are hardcoded in this script. The
# spring window, hydrology-year start, window length, strictness rules, the
# trajectory-restriction start year, and the van Willegen quadrat-well roster
# all live in utils/config.py. Edit there if any of these change.
MSL_SPRING_MONTHS          = config.MSL_SPRING_MONTHS
MSL_HYDRO_YEAR_START_MONTH = config.MSL_HYDRO_YEAR_START_MONTH
MSL_DEFAULT_WINDOW_YEARS   = config.MSL_DEFAULT_WINDOW_YEARS
MSL_MIN_MONTHS_PER_SPRING  = config.MSL_MIN_MONTHS_PER_SPRING
MSL_MIN_YEARS_IN_WINDOW    = config.MSL_MIN_YEARS_IN_WINDOW
TRAJECTORY_START_YEAR      = config.MSL_TRAJECTORY_START_YEAR
VW_QUADRAT_WELLS           = list(config.VW_QUADRAT_WELLS)

# ── Intervention markers on the trajectory plots ──────────────────────────────
# Dates are imported from utils.scraping_common (the canonical source used by
# Scripts 09a–09e, 10a–10i, 21). Colours are imported from utils.config.
# Mapping calendar date → hydrology year y (where hy y = 1 Jun y-1 to 31 May y):
#   * April 2015 scraping     → hydro year 2015 (spring event; partial-year impact)
#   * December 2017 clearfell → hydro year 2018 (winter event; spring 2018 fully post)
#   * October 2023 re-scrape  → hydro year 2024 (autumn event; spring 2024 fully post)
#
# Two derived guides are drawn from each:
#   * solid line at the first window-end containing *any* post-intervention
#     spring data
#   * dashed line at the first window-end that is *fully* post-intervention
#     (intervention's hydro year + window − 1)
# This is the management-relevant horizon for expecting vegetation response
# under the van Willegen 5-year framework.
def _intervention_to_hydro_year(date: pd.Timestamp) -> int:
    """Calendar date → hydrology year y where y runs 1 Jun y-1 to 31 May y."""
    return int(date.year + (1 if date.month >= MSL_HYDRO_YEAR_START_MONTH else 0))


def _intervention_markers_from_canonical():
    """
    Build the intervention-marker list from canonical pipeline constants.

    Dates: utils.scraping_common (SCRAPING_DATE, INTERVENTION_DATE,
    SCRAPING_DATE_2). Colours: utils.config (INTERVENTION_COLOUR_SCRAPE,
    INTERVENTION_COLOUR_CLEARFELL).
    """
    from utils.scraping_common import (
        SCRAPING_DATE, INTERVENTION_DATE, SCRAPING_DATE_2,
    )
    return [
        {"date":   SCRAPING_DATE,
         "label":  "Scrape (CEH36, Apr 2015)",
         "colour": config.INTERVENTION_COLOUR_SCRAPE},
        {"date":   INTERVENTION_DATE,
         "label":  "Clearfell (Dec 2017)",
         "colour": config.INTERVENTION_COLOUR_CLEARFELL},
        {"date":   SCRAPING_DATE_2,
         "label":  "Re-scrape (CEH18/21, Oct 2023)",
         "colour": config.INTERVENTION_COLOUR_SCRAPE},
    ]


INTERVENTION_MARKERS = _intervention_markers_from_canonical()


# ── Helpers ───────────────────────────────────────────────────────────────────
def hydrology_year(date: pd.Timestamp,
                   start_month: int = MSL_HYDRO_YEAR_START_MONTH) -> int:
    """
    Curreli / van Willegen 'hydrology year B': starts 1st June.
    A reading dated 2010-06 to 2011-05 belongs to hydrology year 2011.
    """
    return int(date.year + (1 if date.month >= start_month else 0))


def _to_long(wells_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot wide wells_clean to long form with date / well / level_pipe.
    Date semantics: the row labelled YYYY-MM-01 carries the YYYY-MM water level
    (the '-01' is pandas formatting, not the 1st of the month). See F.2.
    """
    df = wells_clean.copy()
    if df.columns[0] in ("Unnamed: 0", "") or df.columns[0].lower().startswith("date"):
        df.columns = ["date", *df.columns[1:]]
    df["date"] = pd.to_datetime(df["date"])
    long = df.melt(id_vars="date", var_name="well", value_name="level_pipe")
    long["well"] = long["well"].astype(str).str.strip().str.lower().str.replace(" ", "")
    long = long.dropna(subset=["level_pipe"]).reset_index(drop=True)
    long["month"] = long["date"].dt.month
    long["hydro_year"] = long["date"].apply(hydrology_year)
    return long


def _ground_offset(elev: pd.DataFrame) -> pd.Series:
    """
    Return per-well Upstand_m (metres pipe-top is above ground).
    level_bg = level_pipe + Upstand_m.
    """
    elev = elev.copy()
    elev["well"] = elev["Name"].astype(str).str.strip().str.lower().str.replace(" ", "")
    return elev.set_index("well")["Upstand_m"]


# ── Pass 1: annual MSL and MAX per well per hydrology year ───────────────────
def annual_msl_max(long: pd.DataFrame,
                   upstand: pd.Series,
                   provenance_long: pd.DataFrame | None) -> pd.DataFrame:
    """
    For each (well, hydro_year):
      MSL = mean of level over Mar/Apr/May (only if 3 measurements present)
      MAX = max of level over full hydro year (1 Jun y-1 to 31 May y)

    Both expressed in the depth-below-ground frame (paper convention).
    """
    rows = []
    spring_mask = long["month"].isin(MSL_SPRING_MONTHS)
    spring = long[spring_mask]

    # MSL — spring only
    msl_g = spring.groupby(["well", "hydro_year"])
    msl_records = msl_g["level_pipe"].agg(["mean", "count"]).reset_index()
    msl_records = msl_records.rename(columns={"mean": "MSL_m_pipe",
                                              "count": "n_spring_months"})

    # MAX — over full hydrology year
    max_g = long.groupby(["well", "hydro_year"])
    max_records = max_g["level_pipe"].agg(["max", "count"]).reset_index()
    max_records = max_records.rename(columns={"max": "MAX_m_pipe",
                                              "count": "n_hydroyear_months"})

    annual = pd.merge(msl_records, max_records, on=["well", "hydro_year"], how="outer")

    # interpolation flags via provenance (optional)
    if provenance_long is not None and not provenance_long.empty:
        spring_prov = provenance_long[provenance_long["month"].isin(MSL_SPRING_MONTHS)]
        n_interp = (spring_prov[spring_prov["was_interpolated"]]
                    .groupby(["well", "hydro_year"]).size()
                    .rename("n_interpolated_spring").reset_index())
        annual = annual.merge(n_interp, on=["well", "hydro_year"], how="left")
        annual["n_interpolated_spring"] = annual["n_interpolated_spring"].fillna(0).astype(int)
    else:
        annual["n_interpolated_spring"] = 0

    # convert to depth-below-ground
    up = annual["well"].map(upstand)
    annual["MSL_m_bg"] = annual["MSL_m_pipe"] + up
    annual["MAX_m_bg"] = annual["MAX_m_pipe"] + up

    # validity: STRICT 3-of-3
    annual["valid"] = (annual["n_spring_months"] >= MSL_MIN_MONTHS_PER_SPRING)

    return annual[["well", "hydro_year",
                   "MSL_m_pipe", "MSL_m_bg", "n_spring_months",
                   "n_interpolated_spring",
                   "MAX_m_pipe", "MAX_m_bg", "n_hydroyear_months",
                   "valid"]].sort_values(["well", "hydro_year"]).reset_index(drop=True)


# ── Pass 2: 5-year rolling MSL and MAX per well ──────────────────────────────
def rolling_5yr(annual: pd.DataFrame,
                window: int = MSL_DEFAULT_WINDOW_YEARS,
                min_years: int = MSL_MIN_YEARS_IN_WINDOW) -> pd.DataFrame:
    """
    For each well, for each end_year y in the well's record:
      MSL5(y) = mean of {MSL_{y-4} ... MSL_y}, only if min_years valid present.
    """
    rows = []
    for well, sub in annual.groupby("well"):
        sub = sub.set_index("hydro_year").sort_index()
        valid_sub = sub[sub["valid"]]
        if valid_sub.empty:
            continue
        years_span = range(int(valid_sub.index.min()), int(valid_sub.index.max()) + 1)
        for end_y in years_span:
            window_years = list(range(end_y - window + 1, end_y + 1))
            present = valid_sub.reindex(window_years)
            n_valid = present["MSL_m_bg"].notna().sum()
            if n_valid < min_years:
                continue
            rows.append({
                "well": well,
                "window_end_year": end_y,
                "n_years_in_window": int(n_valid),
                "MSL5_m_pipe": present["MSL_m_pipe"].mean(),
                "MSL5_m_bg":   present["MSL_m_bg"].mean(),
                "MAX5_m_pipe": present["MAX_m_pipe"].mean(),
                "MAX5_m_bg":   present["MAX_m_bg"].mean(),
                "n_interp_in_window": int(present["n_interpolated_spring"].fillna(0).sum()),
            })
    return pd.DataFrame(rows).sort_values(["well", "window_end_year"]).reset_index(drop=True)


# ── Pass 3: cluster aggregation ──────────────────────────────────────────────
def attach_cluster_ids(per_well: pd.DataFrame,
                       ref_clusters: pd.DataFrame,
                       ext_clusters: pd.DataFrame) -> pd.DataFrame:
    """
    Merge cluster IDs onto per-well rows.
      * Reference network → 02_07_cluster_membership_k5.csv (column `cluster_k5`)
      * Extended network  → 06_pear_membership_audit_sitewide.csv
                            (column `Best_Match_Cluster`; the consumer-of-record).
    """
    ref = ref_clusters.copy()
    ref["well"] = ref["well"].astype(str).str.strip().str.lower().str.replace(" ", "")
    ref = ref[["well", "cluster_k5"]].rename(columns={"cluster_k5": "cluster_id_ref"})

    ext = ext_clusters.copy()
    ext["well"] = ext["Well_Normalised"].astype(str).str.strip().str.lower().str.replace(" ", "")
    ext = ext[["well", "Best_Match_Cluster", "Network"]].rename(
        columns={"Best_Match_Cluster": "cluster_id_ext"}
    )

    df = per_well.merge(ref, on="well", how="left").merge(ext, on="well", how="left")
    df["cluster_id"] = df["cluster_id_ref"].fillna(df["cluster_id_ext"])
    df["cluster_id"] = df["cluster_id"].astype("Int64")
    df["cluster_label"] = df["cluster_id"].map(config.CLUSTER_LABELS)
    df["network"] = df["Network"].fillna("Reference")
    return df.drop(columns=["cluster_id_ref", "cluster_id_ext", "Network"])


def cluster_trajectory(per_well_with_cluster: pd.DataFrame) -> pd.DataFrame:
    g = per_well_with_cluster.dropna(subset=["cluster_id"]).groupby(
        ["cluster_id", "window_end_year"]
    )
    out = g.agg(
        cluster_label=("cluster_label", "first"),
        n_wells=("well", "nunique"),
        MSL5_m_bg_mean=("MSL5_m_bg", "mean"),
        MSL5_m_bg_median=("MSL5_m_bg", "median"),
        MSL5_m_bg_std=("MSL5_m_bg", "std"),
        MAX5_m_bg_mean=("MAX5_m_bg", "mean"),
        MAX5_m_bg_median=("MAX5_m_bg", "median"),
    ).reset_index().sort_values(["cluster_id", "window_end_year"])
    return out


# ── Method B: cluster-centroid MSL5 from 03_regional_averages ────────────────
# Method A above aggregates per-well MSL5 across the extended cluster network
# (Script 26's primary monitoring metric, van-Willegen-aligned).
#
# Method B aggregates differently: it takes the cluster-centroid monthly mean
# series produced by Script 03 (which uses the LCSC reference network only,
# ~5-26 wells per cluster) and computes MSL5 on that centroid series.
#
# The two methods give *different* numbers (sometimes by >0.3 m) because they
# describe different network compositions:
#   - Method A: extended cluster, ~25 wells in C5
#   - Method B: reference cluster, ~5 wells in C5
#
# Both are valid; they answer different questions. Method A is the headline
# monitoring metric (maximum spatial coverage). Method B is the SSM-consistent
# companion (same baseline as the cluster β coefficients, P_flood, Scripts 11
# transfer functions, and Script 26b UKCP18 projections). The report uses
# Method A in §4.9.8 spatial / trajectory figures, and Method B in §3.6 /
# Tools A & B projection figures.
#
# This function consumes 03_regional_averages.csv directly. The block-column
# naming mirrors Script 03's BLOCK_MAP.
def cluster_centroid_trajectory(
    regional_path: Path,
    window_years: int = MSL_DEFAULT_WINDOW_YEARS,
    min_months_per_spring: int = MSL_MIN_MONTHS_PER_SPRING,
    min_years_in_window: int = MSL_MIN_YEARS_IN_WINDOW,
) -> pd.DataFrame:
    """
    Compute per-cluster MSL5 from the Script 03 cluster-centroid monthly
    series in 03_regional_averages.csv. Strictness rules match Method A
    (3/3 spring months, 5/5 annual MSLs).

    Returns
    -------
    pd.DataFrame with columns:
        cluster_id, cluster_label, window_end_year,
        MSL5_m_bg_centroid, MAX5_m_bg_centroid, n_years_in_window
    """
    reg = pd.read_csv(regional_path)
    reg["Date"] = pd.to_datetime(reg["Date"])
    reg = reg.set_index("Date").sort_index()
    reg["month"] = reg.index.month
    reg["vw_year"] = reg.index.year + (
        reg["month"] >= MSL_HYDRO_YEAR_START_MONTH
    ).astype(int)

    block_map = {
        1: ("Lake_Edge",      "C1 (Lake Edge)"),
        2: ("Eastern_Block",  "C2 (Dune)"),
        3: ("Western_Block",  "C3 (Western Residual)"),
        4: ("Forest",         "C4 (Main Forest)"),
        5: ("Coastal_Forest", "C5 (Coastal Forest)"),
    }

    out_rows = []
    for cid, (col, label) in block_map.items():
        if col not in reg.columns:
            continue
        spring_only = reg[reg["month"].isin(MSL_SPRING_MONTHS)][[col, "vw_year"]].dropna()
        annual_min = annual_max = annual_msl = None
        # Annual aggregation (Mar-May) — strict min_months_per_spring
        ann = (spring_only.groupby("vw_year")
               .agg(MSL=(col, "mean"),
                    MAX=(col, "max"),
                    n_spring_months=(col, "count"))
               .reset_index())
        ann = ann[ann["n_spring_months"] >= min_months_per_spring]
        ann = ann.sort_values("vw_year").reset_index(drop=True)
        # 5-year rolling — strict min_years_in_window
        ann["MSL5"] = ann["MSL"].rolling(
            window=window_years, min_periods=min_years_in_window
        ).mean()
        ann["MAX5"] = ann["MAX"].rolling(
            window=window_years, min_periods=min_years_in_window
        ).mean()
        valid = ann.dropna(subset=["MSL5"]).copy()
        for _, row in valid.iterrows():
            out_rows.append({
                "cluster_id":         cid,
                "cluster_label":      label,
                "window_end_year":    int(row["vw_year"]),
                "MSL5_m_bg_centroid": float(row["MSL5"]),
                "MAX5_m_bg_centroid": float(row["MAX5"]),
                "n_years_in_window":  window_years,
            })

    return pd.DataFrame(out_rows).sort_values(
        ["cluster_id", "window_end_year"]
    ).reset_index(drop=True)


def _draw_intervention_markers(ax, xmin: int, xmax: int,
                               window_years: int = MSL_DEFAULT_WINDOW_YEARS):
    """
    Draw intervention markers as paired vertical lines on a window-end-year
    axis.

    For each intervention:
      * SOLID line at the first window-end containing any post-intervention
        spring data. For autumn/winter events (Oct, Dec), this is the
        hydro year of intervention itself. For spring events (Mar–May), the
        spring within the intervention's hydro year is partially post; the
        first window-end with substantial post-intervention spring data is
        the hydro year of intervention + 0.
      * DASHED line at the first window-end fully post-intervention
        (= first post-intervention hydro year + window_years − 1).
    Both confined to the visible x-range.
    """
    handles = []
    labels = []
    for m in INTERVENTION_MARKERS:
        date = m["date"]
        hy_int = _intervention_to_hydro_year(date)
        # Spring (Mar–May) interventions impact spring of hy_int itself;
        # other interventions impact the spring of hy_int+1 onwards.
        if date.month in MSL_SPRING_MONTHS:
            first_post_hy = hy_int          # partial impact
            first_full_hy = hy_int + window_years - 1
        else:
            first_post_hy = hy_int          # next spring is fully post
            first_full_hy = hy_int + window_years - 1

        col = m["colour"]
        # Solid: first impact window-end
        if xmin <= first_post_hy <= xmax:
            h = ax.axvline(first_post_hy, color=col, linewidth=1.4,
                           linestyle="-", alpha=0.85, zorder=1)
            handles.append(h)
            labels.append(f"{m['label']}: 1st impact")
        # Dashed: first fully-post-intervention window
        if xmin <= first_full_hy <= xmax:
            h = ax.axvline(first_full_hy, color=col, linewidth=1.2,
                           linestyle="--", alpha=0.75, zorder=1)
            handles.append(h)
            labels.append(f"{m['label']}: 1st full window")
    return handles, labels


# ── Plotting ──────────────────────────────────────────────────────────────────
def _plot_with_gaps(ax, years, values, **kwargs):
    """
    Plot a series, breaking the line across any non-consecutive year gaps.

    NW6 and NW7 (for example) have hydrology year 2012 fully missing under
    the strict 3/3 spring rule, so their MSL5 series jumps from window-end
    2011 to window-end 2017. A naive ax.plot bridges the gap visually,
    falsely implying continuity. This helper plots each consecutive run as
    a separate line segment so missing windows render as a true gap.

    The `label` kwarg is applied to the first segment only to avoid duplicate
    legend entries.
    """
    years = list(map(int, years))
    if not years:
        return
    # Identify consecutive runs
    runs = []
    run = [(years[0], values[0])]
    for y, v in zip(years[1:], values[1:]):
        if y == run[-1][0] + 1:
            run.append((y, v))
        else:
            runs.append(run)
            run = [(y, v)]
    runs.append(run)
    # Plot each run; apply label only to the first to avoid duplication
    label = kwargs.pop("label", None)
    for i, r in enumerate(runs):
        xs = [pt[0] for pt in r]
        ys = [pt[1] for pt in r]
        if i == 0 and label is not None:
            ax.plot(xs, ys, label=label, **kwargs)
        else:
            ax.plot(xs, ys, **kwargs)


def plot_cluster_trajectory(per_cluster: pd.DataFrame, out: Path) -> None:
    # Restrict to representative-network windows (see TRAJECTORY_START_YEAR
    # rationale in the script header).
    plot_df = per_cluster[per_cluster["window_end_year"] >= TRAJECTORY_START_YEAR]
    if plot_df.empty:
        print("  [warn] no cluster trajectory data after restriction — skipping")
        return

    fig, ax = plt.subplots(figsize=(10, 5.5))

    # Intervention markers drawn first so cluster lines overlay them
    xmin = int(plot_df["window_end_year"].min())
    xmax = int(plot_df["window_end_year"].max())
    int_handles, int_labels = _draw_intervention_markers(ax, xmin, xmax)

    colours = config.CLUSTER_COLOURS
    cluster_handles = []
    cluster_labels = []
    for cid, sub in plot_df.groupby("cluster_id"):
        sub = sub.sort_values("window_end_year")
        col = colours.get(int(cid), "#444")
        lbl = config.CLUSTER_LABELS.get(int(cid), f"C{int(cid)}")
        _plot_with_gaps(
            ax,
            sub["window_end_year"].tolist(),
            sub["MSL5_m_bg_mean"].tolist(),
            marker="o", linewidth=1.6, color=col, label=lbl,
        )
        # capture a handle for the combined legend
        cluster_handles.append(plt.Line2D([0], [0], color=col, marker="o", lw=1.6))
        cluster_labels.append(lbl)

    # Curreli reference lines in depth-below-ground sign convention.
    # MSL is most-comparable on its level scale to the Curreli summer
    # thresholds (the wet/dry slack viability cutoffs).
    h_sd15 = ax.axhline(-config.SD15b, ls="--", color="#1a7a1a", lw=1.0)
    h_sd16 = ax.axhline(-config.SD16,  ls="--", color="#cc0000", lw=1.0)
    ax.axhline(0, color="#333", lw=0.6)
    cluster_handles += [h_sd15, h_sd16]
    cluster_labels  += [f"SD15b wet slack (−{config.SD15b:.2f} m)",
                        f"SD16 dry slack (−{config.SD16:.2f} m)"]

    ax.set_xlabel("Hydrology year (window end)")
    ax.set_ylabel("5-year MSL (m, depth below ground)")
    ax.set_title("Cluster-mean 5-year MSL trajectory\n"
                 "van Willegen et al. (2025) metric  "
                 f"(window ends {TRAJECTORY_START_YEAR}+)")

    # Extend y-axis lower bound to give the legends clear space below the
    # data. The data range alone places the lowest cluster mean (C3/C4
    # around end-2020) at ~−1.20 m; we extend below that so the
    # lower-left / lower-right legends do not overlay the C3/C4 lines.
    ax.relim()
    ax.autoscale_view()
    y_lo, y_hi = ax.get_ylim()
    legend_headroom = 0.45 * (y_hi - y_lo)   # ~45% extra below the data
    ax.set_ylim(y_lo - legend_headroom, y_hi)

    # Two-column legend: clusters + thresholds on the left, interventions on the right
    leg1 = ax.legend(cluster_handles, cluster_labels,
                     loc="lower left", fontsize=8, ncol=2,
                     title="Clusters & thresholds", title_fontsize=8)
    ax.add_artist(leg1)
    if int_handles:
        ax.legend(int_handles, int_labels, loc="lower right", fontsize=7,
                  title="Interventions  (solid = 1st impact, dashed = 1st full window)",
                  title_fontsize=7)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_quadrat_wells(per_well_with_cluster: pd.DataFrame, out: Path) -> None:
    """Per-well MSL5 trajectories restricted to van Willegen quadrat wells.

    Lines are broken across non-consecutive year gaps (e.g. NW6 and NW7 lose
    the 2012 hydrology year under the strict 3/3 spring rule, so their MSL5
    series jumps from 2011 to 2017 — this is rendered as a true gap rather
    than a straight-line bridge).
    """
    sub_all = per_well_with_cluster[
        per_well_with_cluster["well"].isin(VW_QUADRAT_WELLS)
        & (per_well_with_cluster["window_end_year"] >= TRAJECTORY_START_YEAR)
    ]
    if sub_all.empty:
        print("  [warn] no quadrat-well data to plot")
        return

    fig, ax = plt.subplots(figsize=(11, 6))

    xmin = int(sub_all["window_end_year"].min())
    xmax = int(sub_all["window_end_year"].max())
    int_handles, int_labels = _draw_intervention_markers(ax, xmin, xmax)

    colours = config.CLUSTER_COLOURS
    # First pass — plot trajectories and collect endpoint info for label placement.
    endpoints = []
    for well in sorted(sub_all["well"].unique()):
        ss = sub_all[sub_all["well"] == well].sort_values("window_end_year")
        cid = ss["cluster_id"].dropna().iloc[0] if ss["cluster_id"].notna().any() else None
        col = colours.get(int(cid), "#777") if cid is not None else "#777"
        _plot_with_gaps(
            ax,
            ss["window_end_year"].tolist(),
            ss["MSL5_m_bg"].tolist(),
            marker="o", lw=1.2, markersize=3.5, color=col, alpha=0.85,
        )
        last = ss.iloc[-1]
        endpoints.append({
            "well":   well,
            "x_last": int(last["window_end_year"]),
            "y_last": float(last["MSL5_m_bg"]),
            "colour": col,
        })

    h_sd15 = ax.axhline(-config.SD15b, ls="--", color="#1a7a1a", lw=1.0)
    h_sd16 = ax.axhline(-config.SD16,  ls="--", color="#cc0000", lw=1.0)
    ax.axhline(0, color="#333", lw=0.6)

    ax.set_xlabel("Hydrology year (window end)")
    ax.set_ylabel("5-year MSL (m, depth below ground)")
    ax.set_title("5-year MSL at van Willegen et al. (2025) quadrat-calibrated wells  "
                 f"(window ends {TRAJECTORY_START_YEAR}+)")

    # ── Collision-resolving right-edge labels ─────────────────────────────────
    # Reserve room on the right for a labelled column. We don't set ax.set_xlim
    # ourselves; matplotlib auto-scaled the data range. Stretch the right side
    # to make room for the label column without altering the data plot.
    ax.grid(alpha=0.25)
    cur_xmin, cur_xmax = ax.get_xlim()
    data_xmax = max(ep["x_last"] for ep in endpoints)
    label_col_x = data_xmax + 0.9
    connector_kink_x = data_xmax + 0.25
    ax.set_xlim(cur_xmin, label_col_x + 1.1)

    # Walk top-to-bottom, enforcing MIN_DY between consecutive labels.
    y_min, y_max = ax.get_ylim()
    MIN_DY = 0.038 * (y_max - y_min)
    endpoints_sorted = sorted(endpoints, key=lambda d: -d["y_last"])
    prev_label_y = None
    for ep in endpoints_sorted:
        if prev_label_y is None:
            ep["label_y"] = ep["y_last"]
        else:
            ep["label_y"] = min(ep["y_last"], prev_label_y - MIN_DY)
        prev_label_y = ep["label_y"]
    # If labels squeezed below the axis, redistribute upward from the bottom.
    overflow = min(ep["label_y"] for ep in endpoints_sorted) - y_min
    if overflow < 0:
        endpoints_bottom_up = sorted(endpoints_sorted, key=lambda d: d["label_y"])
        prev_label_y = None
        for ep in endpoints_bottom_up:
            if prev_label_y is None:
                ep["label_y"] = max(ep["label_y"], y_min + 0.02 * (y_max - y_min))
            else:
                ep["label_y"] = max(ep["label_y"], prev_label_y + MIN_DY)
            prev_label_y = ep["label_y"]

    # Draw connector lines and labels.
    for ep in endpoints_sorted:
        ax.plot(
            [ep["x_last"], connector_kink_x, label_col_x - 0.08],
            [ep["y_last"], ep["label_y"], ep["label_y"]],
            color=ep["colour"], lw=0.6, alpha=0.55, zorder=2,
        )
        ax.text(
            label_col_x, ep["label_y"], ep["well"].upper(),
            fontsize=7.5, va="center", ha="left",
            color=ep["colour"], fontweight="bold",
        )

    # Combined legend: thresholds + intervention markers
    misc_handles = [h_sd15, h_sd16] + int_handles
    misc_labels  = [f"SD15b (−{config.SD15b:.2f} m)",
                    f"SD16 (−{config.SD16:.2f} m)"] + int_labels
    ax.legend(misc_handles, misc_labels, loc="lower left", fontsize=7, ncol=1)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


def plot_msl5_map(latest_per_well: pd.DataFrame,
                  locations: pd.DataFrame,
                  elev: pd.DataFrame,
                  out: Path) -> None:
    """IDW surface of latest MSL5 (depth-below-ground) over the site grid."""
    locs = locations.copy()
    locs["well"] = locs["Name"].astype(str).str.strip().str.lower().str.replace(" ", "")
    el = elev.copy()
    el["well"] = el["Name"].astype(str).str.strip().str.lower().str.replace(" ", "")
    el = el[["well", "DEM_Ground_Elev"]].rename(columns={"DEM_Ground_Elev": "dem"})

    merged = (latest_per_well
              .merge(locs[["well", "E", "N"]], on="well", how="inner")
              .merge(el, on="well", how="left"))
    merged = merged.dropna(subset=["MSL5_m_bg", "E", "N"])
    if merged.empty:
        print("  [warn] no wells with both MSL5 and locations — skipping map")
        return

    fig, ax = plt.subplots(figsize=(10, 9))

    # DEM hillshade backdrop — map_utils signature: load_dem_hillshade(ax, data_dir, ...)
    try:
        result = load_dem_hillshade(ax, paths.DATA_DIR)
        # Returns (img, ok, dem_e_arr, dem_n_arr, dem_data) per 11b usage
        if isinstance(result, tuple) and len(result) >= 5:
            _, _ok, dem_e_arr, dem_n_arr, dem_data = result[:5]
        else:
            dem_e_arr = dem_n_arr = dem_data = None
    except Exception as e:
        print(f"  [warn] hillshade failed: {e}")
        dem_e_arr = dem_n_arr = dem_data = None

    # MSL5 IDW surface. Sign: deeper (more negative) = drier slack.
    vals = merged["MSL5_m_bg"].to_numpy()
    vmin_eff = float(min(vals.min(), -config.SD16 - 0.2))
    vmax_eff = float(max(vals.max(), 0.0))
    vcenter  = -config.SD15b
    # TwoSlopeNorm requires vmin < vcenter < vmax. Guard against degenerate runs.
    if not (vmin_eff < vcenter < vmax_eff):
        # fall back to a plain linear norm
        norm = mcolors.Normalize(vmin=vmin_eff, vmax=vmax_eff)
    else:
        norm = mcolors.TwoSlopeNorm(vmin=vmin_eff, vcenter=vcenter, vmax=vmax_eff)
    cmap = plt.get_cmap("RdYlBu")

    mesh, gx, gy, surf = add_idw_surface(
        ax=ax,
        df=merged,
        value_col="MSL5_m_bg",
        easting_col="E",
        northing_col="N",
        dem_col="dem",
        dem_e_arr=dem_e_arr,
        dem_n_arr=dem_n_arr,
        dem_data=dem_data,
        cmap=cmap,
        norm=norm,
        alpha=0.78,
    )

    cbar = fig.colorbar(mesh, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("5-year MSL (m, below ground)\nvan Willegen et al. (2025)")

    # KML site features
    try:
        add_kml_features(ax, paths.DATA_DIR, include_streams=False)
    except Exception as e:
        print(f"  [warn] KML features failed: {e}")

    # Plot wells, distinguishing van Willegen quadrat wells
    is_quadrat = merged["well"].isin(VW_QUADRAT_WELLS)
    ax.scatter(merged.loc[~is_quadrat, "E"], merged.loc[~is_quadrat, "N"],
               s=22, facecolor="white", edgecolor="black", linewidth=0.7,
               zorder=5, label="Reference / extended well")
    ax.scatter(merged.loc[is_quadrat, "E"], merged.loc[is_quadrat, "N"],
               s=55, facecolor="yellow", edgecolor="black", linewidth=0.9,
               marker="D", zorder=6, label="van Willegen quadrat well")

    ax.set_xlabel("Easting (m, OSGB36)")
    ax.set_ylabel("Northing (m, OSGB36)")
    latest_year = int(latest_per_well["window_end_year"].max())
    ax.set_title(f"5-year mean spring water level (MSL) — window ending {latest_year}\n"
                 "van Willegen et al. (2025); SD15b/SD16 reference values from Curreli et al. (2013)")
    ax.legend(loc="lower right", fontsize=8)
    # Match the canonical site map extent used by Script 11b's summer-minima
    # figure and the other publication-quality spatial maps. Bounds live in
    # utils.config so all spatial figures stay in sync.
    ax.set_xlim(config.SITE_MAP_EAST_MIN,  config.SITE_MAP_EAST_MAX)
    ax.set_ylim(config.SITE_MAP_NORTH_MIN, config.SITE_MAP_NORTH_MAX)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    print("=" * 72)
    print("Script 26 — van Willegen et al. (2025) 5-year MSL aggregation")
    print("=" * 72)

    # Load inputs — all paths from utils.paths (canonical pipeline constants).
    wells_clean = pd.read_csv(paths.INT_WELLS_CLEAN)
    print(f"  {paths.INT_WELLS_CLEAN.name:<28s} : {wells_clean.shape[0]} rows × "
          f"{wells_clean.shape[1] - 1} wells")

    try:
        wells_ext = pd.read_csv(paths.INT_WELLS_EXTENDED)
        print(f"  {paths.INT_WELLS_EXTENDED.name:<28s} : {wells_ext.shape[0]} rows × "
              f"{wells_ext.shape[1] - 1} wells")
    except FileNotFoundError:
        wells_ext = None
        print(f"  {paths.INT_WELLS_EXTENDED.name:<28s} : not found (skipping extended network)")

    elev = pd.read_csv(paths.INT_WELL_ELEVATIONS)
    print(f"  {paths.INT_WELL_ELEVATIONS.name:<28s} : {elev.shape[0]} wells")
    upstand = _ground_offset(elev)

    locations = pd.read_csv(paths.INT_LOCATIONS)
    print(f"  {paths.INT_LOCATIONS.name:<28s} : {locations.shape[0]} wells")

    # k=5 cluster membership template (paths.OUT_02_MEMBERSHIP_SWEEP carries a
    # {k} placeholder; the canonical Newborough partition is k=5).
    ref_clusters_path = Path(str(paths.OUT_02_MEMBERSHIP_SWEEP).format(k=5))
    ref_clusters = pd.read_csv(ref_clusters_path)
    print(f"  {ref_clusters_path.name:<28s} : {ref_clusters.shape[0]} wells")

    ext_clusters = pd.read_csv(paths.INT_PEAR_AUDIT_SITEWIDE)
    print(f"  {paths.INT_PEAR_AUDIT_SITEWIDE.name:<28s} : "
          f"{ext_clusters.shape[0]} wells")

    # Provenance — defensive read because the file is optional (S.1 may not
    # have run yet on a fresh clone; the script falls back to n_interpolated = 0).
    try:
        prov = pd.read_csv(paths.INT_WELLS_PROVENANCE)
        # Provenance can be wide-form (rows=date, cols=well, values=flag)
        # or long-form. Handle both.
        if "well" in prov.columns and "was_interpolated" in prov.columns:
            prov["date"] = pd.to_datetime(prov["date"])
            prov_long = prov[["date", "well", "was_interpolated"]].copy()
        else:
            # wide form: pivot
            if prov.columns[0] in ("Unnamed: 0", "") or \
               prov.columns[0].lower().startswith("date"):
                prov.columns = ["date", *prov.columns[1:]]
            prov["date"] = pd.to_datetime(prov["date"])
            prov_long = prov.melt(id_vars="date", var_name="well",
                                  value_name="flag")
            prov_long["was_interpolated"] = prov_long["flag"].astype(str).str.lower().isin(
                ["interp", "interpolated", "true", "1"]
            )
        prov_long["well"] = prov_long["well"].astype(str).str.strip().str.lower().str.replace(" ", "")
        prov_long["month"] = prov_long["date"].dt.month
        prov_long["hydro_year"] = prov_long["date"].apply(hydrology_year)
        prov_long = prov_long[["well", "date", "month", "hydro_year", "was_interpolated"]]
        print(f"  {paths.INT_WELLS_PROVENANCE.name:<28s} : "
              f"{prov_long['well'].nunique()} wells, {len(prov_long)} (well,month) cells")
    except FileNotFoundError:
        prov_long = None
        print(f"  {paths.INT_WELLS_PROVENANCE.name:<28s} : not found (interp flag will be 0)")

    # ── Build long-form per well from reference + extended ────────────────
    long_ref = _to_long(wells_clean)
    long_ref["network"] = "Reference"
    if wells_ext is not None:
        long_ext = _to_long(wells_ext)
        long_ext["network"] = "Extended"
        long = pd.concat([long_ref, long_ext], ignore_index=True)
    else:
        long = long_ref

    # ── Pass 1 ────────────────────────────────────────────────────────────
    annual = annual_msl_max(long, upstand, prov_long)
    annual.to_csv(OUT_ANNUAL, index=False)
    print(f"\nPass 1 — annual MSL/MAX: {len(annual)} (well, hydro_year) rows; "
          f"{annual['valid'].sum()} valid (3/3 spring rule)")
    print(f"   → {OUT_ANNUAL.name}")

    # ── Pass 2 ────────────────────────────────────────────────────────────
    per_well = rolling_5yr(annual)
    print(f"\nPass 2 — 5-year rolling MSL/MAX: "
          f"{len(per_well)} (well, end_year) rows across "
          f"{per_well['well'].nunique()} wells")

    # ── Cluster attach ─────────────────────────────────────────────────────
    per_well_with_cluster = attach_cluster_ids(per_well, ref_clusters, ext_clusters)
    per_well_with_cluster.to_csv(OUT_5YR, index=False)
    print(f"   → {OUT_5YR.name}")

    # ── Pass 3 — Cluster trajectory (Method A: per-well aggregation) ───────
    per_cluster = cluster_trajectory(per_well_with_cluster)
    per_cluster.to_csv(OUT_CLUSTER, index=False)
    print(f"\nPass 3 — cluster trajectories (Method A, per-well aggregation): "
          f"{len(per_cluster)} (cluster, year) rows")
    print(f"   → {OUT_CLUSTER.name}")

    # ── Pass 3b — Cluster-centroid trajectory (Method B) ───────────────────
    # Aggregates from Script 03's cluster-centroid monthly series (reference
    # network, LCSC partition) — internally consistent with the SSM
    # coefficients in 03_03_cluster_mechanistic_coefficients.csv, which is the
    # baseline that Script 11 Section 5 (Tool A) fits against and Script 26b
    # (Tool B) projects from. See the cluster_centroid_trajectory() docstring
    # for the rationale.
    per_cluster_centroid = cluster_centroid_trajectory(paths.INT_REGIONAL_AVG)
    per_cluster_centroid.to_csv(OUT_CLUSTER_CENTROID, index=False)
    print(f"\nPass 3b — cluster-centroid trajectories (Method B, reference "
          f"network): {len(per_cluster_centroid)} (cluster, year) rows")
    print(f"   → {OUT_CLUSTER_CENTROID.name}")

    # ── Pass 4 — Latest per well ───────────────────────────────────────────
    latest = (per_well_with_cluster.sort_values("window_end_year")
                                    .groupby("well", as_index=False).tail(1))
    latest.to_csv(OUT_LATEST, index=False)
    print(f"\nPass 4 — latest MSL5 per well: {len(latest)} wells")
    print(f"   → {OUT_LATEST.name}")

    # ── Figures ────────────────────────────────────────────────────────────
    print("\nRendering figures...")
    plot_cluster_trajectory(per_cluster, OUT_TRAJ)
    print(f"   → {OUT_TRAJ.name}")
    plot_quadrat_wells(per_well_with_cluster, OUT_QUADRAT)
    print(f"   → {OUT_QUADRAT.name}")
    plot_msl5_map(latest, locations, elev, OUT_MAP)
    print(f"   → {OUT_MAP.name}")

    # ── Summary transcript ────────────────────────────────────────────────
    lines = []
    lines.append("Script 26 — van Willegen et al. (2025) 5-year MSL")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Method parameters (strict per scoping decision 2026-05-20):")
    lines.append(f"  Spring months          : {MSL_SPRING_MONTHS}")
    lines.append(f"  Hydro year start month : {MSL_HYDRO_YEAR_START_MONTH}")
    lines.append(f"  Window length          : {MSL_DEFAULT_WINDOW_YEARS} years")
    lines.append(f"  Min months/spring      : {MSL_MIN_MONTHS_PER_SPRING} / 3")
    lines.append(f"  Min years/window       : {MSL_MIN_YEARS_IN_WINDOW} / 5")
    lines.append("")
    lines.append("Network coverage:")
    lines.append(f"  Annual rows total      : {len(annual)}")
    lines.append(f"  Annual rows valid      : {annual['valid'].sum()}")
    lines.append(f"  Wells with ≥1 MSL5     : {per_well['well'].nunique()}")
    lines.append(f"  Quadrat wells found    : "
                 f"{sum(w in per_well['well'].unique() for w in VW_QUADRAT_WELLS)}/17")
    lines.append("")
    lines.append("Most recent (window-end) MSL5 by cluster, m below ground:")
    latest_year = int(latest["window_end_year"].max())
    lines.append(f"  Window end year : {latest_year}")
    cl_summary = (latest.groupby(["cluster_id", "cluster_label"])
                          .agg(n=("well", "nunique"),
                               MSL5_mean=("MSL5_m_bg", "mean"),
                               MSL5_median=("MSL5_m_bg", "median"),
                               MAX5_mean=("MAX5_m_bg", "mean"))
                          .reset_index())
    for _, r in cl_summary.iterrows():
        lines.append(f"  {r['cluster_label']:<20s} n={int(r['n']):>3d}  "
                     f"MSL5 mean={r['MSL5_mean']:+.3f} m  median={r['MSL5_median']:+.3f} m  "
                     f"MAX5 mean={r['MAX5_mean']:+.3f} m")
    lines.append("")
    lines.append("Curreli (2013) reference values:")
    lines.append(f"  SD15b (wet slack)  : −{config.SD15b:.2f} m below ground")
    lines.append(f"  SD16  (dry slack)  : −{config.SD16:.2f} m below ground")
    lines.append("")
    lines.append("Coverage at van Willegen quadrat wells (calibrated EbF set):")
    for w in VW_QUADRAT_WELLS:
        if w in latest["well"].values:
            row = latest[latest["well"] == w].iloc[0]
            lines.append(f"  {w.upper():<6s}  MSL5={row['MSL5_m_bg']:+.3f} m  "
                         f"MAX5={row['MAX5_m_bg']:+.3f} m  window end={int(row['window_end_year'])}")
        else:
            lines.append(f"  {w.upper():<6s}  no valid MSL5 (insufficient data)")
    OUT_TXT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n   → {OUT_TXT.name}")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
