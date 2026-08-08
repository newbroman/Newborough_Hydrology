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
series is ALREADY in that frame: 01_wells_clean.csv carries the master's
`depth from surface` values (level = upstand - dip), a signed height relative
to the ground surface. No conversion is applied.

2026-08-08: the previous header claimed the raw series was depth-below-pipe-top
and applied `level_bg = level_pipe + Upstand_m`. That was wrong — the upstand is
applied by the master on export, so this added it a second time. The `_m_pipe`
column names are retained for continuity with existing consumers but carry
ground-referenced values; they are scheduled for renaming to `_m_bg`.
Per GEOMETRY_ARCHITECTURE_SPEC.md.

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
  * 26_equilibrium_wetness_index_per_well.csv
                                    Per-well equilibrium wetness index (EWI):
                                    steady-state spring level from the SSM
                                    coefficients under long-term mean climate
                                    (reference + extended network tiers)
  * 26_ewi_msl5_comparison.csv      Per-well observed vs EWI-predicted MSL5
                                    (calibrated MSL5 = a + b·EWI) with residuals
                                    and in_van_willegen flag — the weighable
                                    prediction table (report §4.8.5)
  * 26_ebf_comparison.csv           Per-piezometer Ellenberg-F with MSL5 and EWI
                                    predictions (v1.3.3; external input required)
  * 26_ebf_prediction_scatter.png   Three-panel EbF scatter — report Fig XX
                                    (v1.3.3; external input required)
  * 26_metric_diagnostics_per_well.csv
                                    Per-well window sensitivity and index
                                    precision (v1.4.0): interannual spring SD,
                                    lag-1 autocorrelation against its AR(1)
                                    expectation, MSL5 window standard error and
                                    realised spread, and the EWI standard error
  * 26_index_precision_by_cluster.csv
                                    The same rolled up per cluster, under both
                                    network scopes (reference / all)
  * 26_report_numbers.csv           Scalar statistics cited in §4.8.6 / §6.9,
                                    including the ewi_msl5_* calibration
                                    constants (v1.5.0)
  * 26_table_s7_1_ewi_per_well.csv  Display-formatted per-well EWI / MSL5
                                    reconstruction — Supplementary Table S7.1
                                    (v1.5.0); paste into the ODT via Paste
                                    Special > Unformatted text
  * 26_table_s7_1_ewi_per_well.md   The same table rendered for review (v1.5.0)
  * 26_metric_diagnostics.png       Two-panel diagnostic — report Fig XX
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

Version: 1.5.0 (2026-08-05) — Supplementary Table S7.1 emitter (Pass 9):
  * New emit_supplementary_table_s7_1(): renders the per-well equilibrium
    wetness index and its MSL5 reconstruction as a display-formatted table for
    Supplementary Note S7 of the Supplementary Material. Report §4.8.6 promises
    "the full per-well reconstruction, with the out-of-scope forest wells
    flagged" and, until now, that forward reference resolved to nothing — the
    table had never been rendered. This closes it WITHOUT recomputing anything:
    the emitter is a rendering of the committed Pass 5 and Pass 6 outputs, so
    the table cannot drift from the CSVs it is drawn from.
    All 84 wells are listed. A three-valued Status column distinguishes the
    n=62 in-scope wells that carry an observed MSL5 and therefore entered the
    calibration, the n=2 in-scope wells that have an index but no valid
    five-year spring window (reconstructed only), and the n=20 C4/C5 forest
    wells held out of scope per §4.8.6. Standard errors are the β₃-only
    variant, the dominant term; the full three-coefficient variant stays in
    26_equilibrium_wetness_index_per_well.csv.
    Outputs 26_table_s7_1_ewi_per_well.csv (display strings, for Paste Special >
    Unformatted text into the ODT) and 26_table_s7_1_ewi_per_well.md (for review
    before pasting). paths gains OUT_26_TABLE_S7_1_CSV, OUT_26_TABLE_S7_1_MD.
  * The Pass 6 calibration now reaches a committed CSV. compute_ewi_msl5_
    comparison() has always returned intercept_a, slope_b, r, r2,
    rmse_mm_open_dune and n_calibration, but they went only to the run
    transcript — so the MSL5 = a + b·EWI constants quoted in §4.8.6 had no
    committed-CSV trace. They are now written into 26_report_numbers.csv under
    an ewi_msl5_* prefix, and the emitter reads the calibration from there
    rather than restating it. 26_report_numbers.csv is consequently assembled
    across Passes 6 and 8 and written once, after Pass 8, so the calibration
    lands even if the Pass 8 diagnostics are skipped.
  * Still Passes inside Script 26 — no new pipeline step, and the 41-step
    analytical headline is unchanged.

Version: 1.4.0 (2026-08-02) — Metric diagnostics (Pass 8) and EWI uncertainty:
  * compute_equilibrium_wetness_index() now propagates SSM coefficient
    uncertainty into the index. Reference-tier standard errors are recovered
    exactly from the committed β/p-value/n in 03_master_data.csv (SE = β/|t| on
    n−3 df, no-intercept 3-predictor OLS); extended-tier fits take se_beta_*
    straight from fit_ssm(), which already returns them. EWI CSV gains
    se_beta_1/2/3, n_obs, h_disp_eq_m, EWI_se_m_beta3 and EWI_se_m_full.
    IMPORTANT: the propagation is anchored on |h_disp_eq|, not |EWI_m_pipe|.
    Subtracting the constant DRAINAGE_DATUM shifts the value but not its
    uncertainty; anchoring on EWI_m_pipe understates the error severely at
    wells whose equilibrium level sits near the datum.
  * New compute_metric_diagnostics() + plot_metric_diagnostics() (Pass 8): the
    statistics behind the report's MSL5 window-sensitivity discussion are now
    PIPELINE-GENERATED rather than computed in prose. Three findings:
      (a) spring levels are NOT serially correlated — observed lag-1
          autocorrelation is near zero at every cluster and uncorrelated with
          the recession time, against an AR(1) expectation of exp(−12·β₃)
          rising to ≈0.8 at C4. Spring is the seasonal maximum reached after
          the winter recharge season, so the monthly recession operates within
          the annual cycle, not across it. The 5-year mean behaves as intended.
      (b) window sensitivity is real but is a matter of AMPLITUDE: interannual
          spring SD tracks β₂, not β₃, on partial rank correlations. β₂ and t_R
          are themselves correlated, which is why t_R appears diagnostic alone.
          Triage should therefore use spring SD (or β₂), not the recession time.
      (c) the two indices fail at the same wells for opposite reasons — MSL5
          through the high β₂ driving amplitude, the equilibrium index through
          the low, weakly-identified β₃ in its denominator.
  * Outputs 26_metric_diagnostics_per_well.csv, 26_index_precision_by_cluster.csv
    (rolled up per cluster under both network scopes, reference and all),
    26_report_numbers.csv and 26_metric_diagnostics.png added. paths gains
    OUT_26_METRIC_DIAGNOSTICS, OUT_26_INDEX_PRECISION, OUT_26_REPORT_NUMBERS,
    OUT_26_METRIC_DIAG_FIG. New module constant DIAG_MIN_SPRINGS = 12.
  * Still a Pass inside Script 26 — no change to the pipeline step count.

Version: 1.3.3 (2026-07-03) — EbF cross-validation moved into the pipeline:
  * New compute_ebf_crossvalidation() + plot_ebf_scatter(): the Ellenberg-F
    validation is now PIPELINE-GENERATED (Pass 7) rather than a one-off. It reads
    the documented external van Willegen dataset (paths.DATA_ELLENBERG_EXT; van
    Willegen et al. 2024, Mendeley — gitignored, not redistributed) and runs only
    if that file is present, skipping cleanly otherwise. Between the 17 van
    Willegen piezometers it regresses mean Ellenberg-F on observed MSL5 and on the
    equilibrium index (annual and spring climatology), reporting r (Fisher-z CI),
    RMSE (bootstrap CI), Williams' test (MSL5 vs annual EWI), and A–D match bands.
  * Outputs 26_ebf_comparison.csv and 26_ebf_prediction_scatter.png (report
    Fig XX) added. paths gains DATA_ELLENBERG_EXT, OUT_26_EBF_COMPARISON,
    OUT_26_EBF_SCATTER. MSL5-vs-EbF correlation settles at the per-piezometer
    aggregation (r ≈ 0.83), matching the Table YY / Williams basis.
  * Still a Pass inside Script 26 — no change to the pipeline step count.

Version: 1.3.2 (2026-07-03) — Open-dune scoping via site-wide Pearson clusters:
  * Extended wells now carry a canonical cluster label, read from the Pearson
    site-wide integration (06_pear_membership_audit_sitewide.csv:
    Original_Cluster else Best_Match_Cluster). This corrects the earlier gap
    where 8 extended wells that are in fact forest (FE1–4, NW8, CEH3, CEH15,
    LIS1) carried no label and leaked into the open-dune set.
  * compute_ewi_msl5_comparison() now calibrates and reports MSL5-prediction as
    an OPEN-DUNE metric (C1–C3), mirroring MSL5's own open-dune framing (§4.8.4).
    C4/C5 forest wells are still predicted and written, flagged
    open_dune_scope=False — the coefficients are least constrained there (§4.9.2)
    so predictions degrade (forest RMSE ≈ 220 mm vs open-dune ≈ 119 mm).
  * Comparison CSV gains `open_dune_scope`; calib dict reports rmse_mm_open_dune.
  * Motivation: EbF equivalence (report §4.8.5) — MSL5 and EWI are statistically
    indistinguishable as Ellenberg-F predictors (Williams' test p ≈ 0.81, n=18);
    the open-dune MSL5-prediction generalizes (RMSE ≈ 100 mm on wells outside
    van Willegen's set).

Version: 1.3.1 (2026-07-03) — Extended network + EWI→MSL5 comparison; map dropped:
  * compute_equilibrium_wetness_index() now also fits the extended network
    (01_wells_extended.csv) via the shared fit_ssm(), tagged network='extended'
    (single-pass, no reference QA) alongside the reference tier. EWI CSV gains a
    `network` column.
  * New compute_ewi_msl5_comparison(): calibrates observed MSL5 on EWI
    (MSL5 = a + b·EWI, OLS over all wells with both) and reports per-well
    observed vs EWI-predicted MSL5 and the residual, plus an in_van_willegen
    flag. Output 26_ewi_msl5_comparison.csv (Pass 6). The report presents this
    as a per-well table / match-band summary (§4.8.5); generalization to the
    ~60 wells outside van Willegen's 17-piezometer set is the headline check.
  * plot_ewi_map() and OUT_26_EWI_MAP REMOVED — a standalone EWI surface
    overstated the (modest) coverage advantage; the weighable comparison table
    replaces it. paths.OUT_26_EWI_MAP retired; paths.OUT_26_EWI_MSL5_COMPARISON
    added.

Version: 1.3.0 (2026-07-03) — Equilibrium Wetness Index (EWI):
  * New compute_equilibrium_wetness_index(): the steady-state water-table
    level implied by each well's fitted SSM coefficients under long-term mean
    climate. Setting mean monthly Δh = 0 and solving the head-dependent
    drainage term gives h_disp_eq = (β₁·P̄ − β₂·PET̄)/β₃, so
    EWI_pipe = h_disp_eq − DRAINAGE_DATUM; EWI_bg is identical (no upstand term).
    P̄, PET̄ are the full-record monthly-mean rainfall and PET (the same
    long-term climatology basis as the Script 21 scenario normals), making the
    index climate-window-independent — it needs only a valid SSM fit, not the
    multi-year spring record MSL5 requires. Per-well β from 03_master_data.csv.
  * New plot_ewi_map(): IDW surface of EWI_m_bg on the canonical site extent,
    sharing the MSL5 map's Curreli-referenced colour norm so the two surfaces
    are directly comparable.
  * Outputs 26_equilibrium_wetness_index_per_well.csv and
    26_equilibrium_wetness_index_map.png added (Pass 5). MSL5_EXCLUDED_WELLS
    (CEH13, CEH14) are excluded from the EWI as from MSL5 — their near-zero /
    negative β₃ is the EWI denominator and would send the level to ±∞; a
    belt-and-braces EWI_MIN_BETA3 floor guards any other degenerate β₃.
  * No change to any existing MSL5 output. Motivated by the vegetation
    cross-validation in report §4.8.5 / §5.7.6: EWI predicts mean Ellenberg-F
    (van Willegen et al. 2025) between wells at r ≈ 0.81, against r ≈ 0.84 for
    observed MSL5. Output paths are the canonical paths.OUT_26_EWI_PER_WELL and
    paths.OUT_26_EWI_MAP (added to utils/paths.py alongside the other OUT_26_*).

Version: 1.2.0 (2026-06-25) — MSL5 well exclusion (CEH13, CEH14):
  * CEH13 (near-zero SSM beta_3) and CEH14 (negative beta_3,
    SSM failure NSE -3.21) are excluded from the MSL5 analysis: their long
    drainage memory makes spring readings autocorrelated within the 5-year
    window, so their MSL5 change values and IDW-map contribution are
    unreliable. Same wells already excluded by Script 18 on beta_3 grounds.
  * Mechanism (whole-analysis, flagged): rows are RETAINED in
    26_msl_5yr_per_well.csv with new columns msl5_excluded / msl5_excluded_reason;
    all derived products (Method A cluster trajectory, latest-per-well, IDW
    map, quadrat figure) use the included-only subset. Method B cluster-centroid
    trajectory (Pass 3b, regional-average baseline) is a separate construct and
    is unaffected, so Script 26b projections and the Script 19 viewer DeltaMSL5
    row are unchanged. Exclusion set in config.MSL5_EXCLUDED_WELLS.

Version: 1.0.2 (2026-05-20) — Intervention markers:
  * Cluster trajectory and quadrat plots now show three intervention dates
    (2015 scrape, 2017 clearfell, 2023 re-scrape) as paired vertical lines:
    solid at the first window-end carrying any post-intervention spring
    data, dashed at the first window-end fully post-intervention.
  * Dates imported from `scraping_common.{SCRAPING_DATE, INTERVENTION_DATE,
    SCRAPING_DATE_2}` rather than duplicated locally.

Version: 1.1.3 (2026-05-27) — Cluster-ID source fix:
  * attach_cluster_ids() now reads reference-network cluster IDs from
    paths.INT_CLUSTER_STATS (02_cluster_stats.csv, the post-anchor-remap
    canonical store) instead of paths.OUT_02_MEMBERSHIP_SWEEP formatted
    at k=5 (02_07_cluster_membership_k5.csv, a pre-remap bootstrap-
    stability diagnostic file).
  * The change is a label-correction only — the same 66-well partition
    is described by both files, but they had used different integer
    labels for three of the five clusters. Under the old (pre-remap)
    labelling, what Script 26 wrote out as "C5 Coastal Forest" was
    actually the canonical C3 Western Residual well pool; "C4 Main
    Forest" was the canonical C5 wells; "C3 Western Residual" was the
    canonical C4 wells. C1 and C2 happened to be label-invariant.
  * 35 of 66 reference wells carried the wrong cluster_id / cluster_label
    before this fix; the affected outputs and figures are
    26_msl_5yr_per_well.csv, 26_msl_5yr_latest_per_well.csv,
    26_msl_annual_per_well.csv, 26_msl_5yr_per_cluster.csv,
    26_msl_5yr_trajectory.png, 26_msl_5yr_quadrat_wells.png,
    26_msl_5yr_map.png, 26_msl_results.txt, and any Script 26c figure
    that reads 26_msl_5yr_per_cluster.csv. All have been regenerated
    by re-running the pipeline after this fix.
  * Method B outputs (26_msl_5yr_per_cluster_centroid.csv) and all
    Script 26b outputs (centroid and v1.1.0 per-well pathways) were
    already correct — they read from 03_03_cluster_mechanistic_
    coefficients.csv and 03_master_data.csv directly, which carry
    canonical post-remap IDs. Script 19 v2.8.0's viewer ΔMSL5 row and
    its scenario_summary CSV likewise unaffected — viewer sourcing is
    independent.
  * A defensive guard added in attach_cluster_ids() asserts that the
    reference-cluster file's unique IDs match the canonical 1..5 set
    in config.CLUSTER_LABELS, so any future regression to a pre-remap
    source fails loudly rather than silently relabelling.
  * Full diagnostic in DIAGNOSTIC_REPORT_script_26_cluster_assignment.md
    (in-session record); CHANGELOG.md carries the headline entry.

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
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)

from __future__ import annotations

__version__ = "1.5.0"  # Hollingham (2026) — 2026-08-08 (upstand corrections removed)
# Changelog:
#   1.5.0 (2026-08-08) — Upstand corrections removed at both levels: the MSL/MAX
#     conversion (level_bg = level_pipe + Upstand_m) and the equilibrium index
#     (EWI_bg = EWI_pipe + Upstand_m). 01_wells_clean.csv carries the master's
#     `depth from surface` values (level = upstand - dip), already referenced to
#     the ground surface, so both added the upstand a second time. The _m_pipe
#     and _m_bg column pairs are now identical and are retained only because the
#     Methods Supplement documents the pairing; collapse them with that edit.
#     Geometry columns repointed to ground_elev_m. Per GEOMETRY_ARCHITECTURE_SPEC.md.
#     First numbered version in-file; 1.4.0 was tracked externally
#     (CHANGELOG_delta_2026-08-02_script26_v1p4p0_metric_diagnostics.md).

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy import stats

# ── Repo imports ──────────────────────────────────────────────────────────────
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)

from utils import config, paths
from utils.model_utils import fit_ssm
from utils.map_utils import (
    load_dem_hillshade,
    add_idw_surface,
    add_kml_features,
)
from utils.render_utils import render_figure

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
# EWI outputs (v1.3.0) — canonical paths from utils.paths.
OUT_EWI       = paths.OUT_26_EWI_PER_WELL
OUT_EWI_COMPARISON = paths.OUT_26_EWI_MSL5_COMPARISON
# Supplementary Table S7.1 renderings (v1.5.0).
OUT_TABLE_S7_1_CSV = paths.OUT_26_TABLE_S7_1_CSV
OUT_TABLE_S7_1_MD  = paths.OUT_26_TABLE_S7_1_MD

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
# EWI (v1.3.0): β₃ is the denominator of the equilibrium level, so guard against
# a vanishing drainage coefficient sending it to ±∞. The known offenders
# (CEH13/CEH14) are already in MSL5_EXCLUDED_WELLS; this is a belt-and-braces
# floor for any other degenerate fit.
EWI_MIN_BETA3 = 0.001
# Metric diagnostics (v1.4.0): minimum count of valid annual spring means for a
# well to contribute an interannual standard deviation or a lag-1
# autocorrelation. Below this the per-well statistics are too noisy to carry;
# the well still appears in the per-well CSV with those two fields blank.
DIAG_MIN_SPRINGS = 12

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
    level_bg is identical to level_pipe: the series is already ground-referenced.
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
    annual["MSL_m_bg"] = annual["MSL_m_pipe"]
    annual["MAX_m_bg"] = annual["MAX_m_pipe"]

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
      * Reference network → 02_cluster_stats.csv (post-anchor-remap canonical
                            cluster store; column `Cluster` keyed by
                            `Match_ID`). This is the same source Script 03
                            inherits into 03_master_data.csv, so cluster IDs
                            match every downstream script on the project's
                            canonical 1→C1 Lake Edge ... 5→C5 Coastal Forest
                            ordering.
      * Extended network  → 06_pear_membership_audit_sitewide.csv
                            (column `Best_Match_Cluster`; the consumer-of-
                            record. The Pearson audit also keys against
                            02_cluster_stats.csv at upstream-build time, so
                            its IDs are likewise canonical.)

    v1.1.3 (2026-05-27) — bug fix.  This function previously read
    `02_07_cluster_membership_k5.csv` (the bootstrap-stability sweep's
    diagnostic membership file at k=5), which carries raw Ward integer
    labels because the anchor remap in Script 02 is calibrated for k=5
    only and is not applied inside the K_RANGE_BOOTSTRAP loop that
    writes the membership-sweep files. That produced a clean three-way
    label permutation between Script 26's cluster_id and every other
    script's Cluster ID: 35 of 66 reference wells carried the wrong
    cluster_id (and therefore wrong cluster_label via config.CLUSTER_LABELS),
    with what Script 26 called "C5 Coastal Forest" actually containing
    the canonical C3 Western Residual well pool, and so on.
    See DIAGNOSTIC_REPORT_script_26_cluster_assignment.md for the full
    crosstab and blast radius.
    """
    ref = ref_clusters.copy()
    ref["well"] = ref["Match_ID"].astype(str).str.strip().str.lower().str.replace(" ", "")
    ref = ref[["well", "Cluster"]].rename(columns={"Cluster": "cluster_id_ref"})

    # Defensive guard — fail loudly if the source file is ever swapped out
    # for one whose Cluster IDs are not the canonical 1..5 set, rather than
    # silently re-introducing the v1.1.2 mislabelling. Inserted alongside
    # the v1.1.3 fix per the diagnostic's §6 recommendation.
    ref_unique = set(int(c) for c in ref["cluster_id_ref"].dropna().unique())
    expected   = set(config.CLUSTER_LABELS.keys())
    if ref_unique != expected:
        raise ValueError(
            f"attach_cluster_ids: reference-cluster source carries IDs "
            f"{sorted(ref_unique)}, expected the canonical 1..5 set "
            f"{sorted(expected)} from utils.config.CLUSTER_LABELS. "
            f"Most likely cause: the reference-cluster CSV was changed to "
            f"a pre-remap file (e.g. 02_07_cluster_membership_k5.csv "
            f"under the K_RANGE_BOOTSTRAP sweep). Read INT_CLUSTER_STATS "
            f"(02_cluster_stats.csv) instead — this is the post-anchor-"
            f"remap canonical store."
        )

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
        warn("no cluster trajectory data after restriction — skipping")
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
    render_figure(fig, out)
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
        warn("no quadrat-well data to plot")
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
    render_figure(fig, out)
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
    el = el[["well", "ground_elev_m"]].rename(columns={"ground_elev_m": "dem"})

    merged = (latest_per_well
              .merge(locs[["well", "E", "N"]], on="well", how="inner")
              .merge(el, on="well", how="left"))
    merged = merged.dropna(subset=["MSL5_m_bg", "E", "N"])
    if merged.empty:
        warn("no wells with both MSL5 and locations — skipping map")
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
        warn(f"hillshade failed: {e}")
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
        warn(f"KML features failed: {e}")
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
    render_figure(fig, out)
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────
def compute_equilibrium_wetness_index(elev: pd.DataFrame,
                                      locations: pd.DataFrame) -> pd.DataFrame:
    """
    Equilibrium wetness index (EWI): the steady-state water-table level implied
    by each well's fitted SSM coefficients under long-term mean climate.

    Setting the mean monthly change to zero in the SSM (report §3.4) and solving
    the head-dependent drainage term for the equilibrium displacement gives

        h_disp_eq = (β₁·P̄ − β₂·PET̄) / β₃
        EWI_pipe  = h_disp_eq − DRAINAGE_DATUM       (ground frame; name is legacy)
        EWI_bg    = EWI_pipe                        (identical — no upstand term)

    P̄, PET̄ are the full-record monthly-mean rainfall and PET (the same long-term
    climatology basis as the Script 21 scenario normals), so the index is
    climate-window-independent.

    Two network tiers (v1.3.1):
      * reference — β read from 03_master_data.csv (Script 03, reference-QA'd:
        leave-one-out, datum sensitivity, sign checks).
      * extended  — β fitted here from 01_wells_extended.csv via the shared
        fit_ssm(). These are single-pass fits WITHOUT the reference QA, flagged
        network='extended' and treated as lower-confidence downstream.
    """
    clim = pd.read_csv(paths.INT_CLIMATE, index_col=0, parse_dates=True)
    P_bar   = float(clim["P_m"].mean())
    PET_bar = float(clim["PET"].mean())
    info(f"long-term monthly climate normals: P̄={P_bar:.4f} m  PET̄={PET_bar:.4f} m")

    # Upstand_m per well (pipe→bg), normalised exactly as plot_msl5_map does.
    el = elev.copy()
    el["well"] = el["Name"].astype(str).str.strip().str.lower().str.replace(" ", "")
    offset = el.set_index("well")["Upstand_m"]
    excluded = set(config.MSL5_EXCLUDED_WELLS)

    def _row(w, b1, b2, b3, network, cluster_id=np.nan,
             se1=np.nan, se2=np.nan, se3=np.nan, n_obs=np.nan):
        if not (np.isfinite(b1) and np.isfinite(b2) and np.isfinite(b3)):
            return None
        if b3 <= EWI_MIN_BETA3:
            warn(f"{w.upper()} β₃={b3:.4f} ≤ {EWI_MIN_BETA3} — EWI undefined, skipped")
            return None
        h_disp_eq = (b1 * P_bar - b2 * PET_bar) / b3
        ewi_pipe = h_disp_eq - config.DRAINAGE_DATUM
        ups = offset.get(w, np.nan)
        # No upstand term: the clean series is already ground-referenced, so
        # the equilibrium displacement is in the ground frame already.
        ewi_bg = ewi_pipe

        # Uncertainty (v1.4.0). Subtracting the constant DRAINAGE_DATUM shifts
        # the value but not its uncertainty, so SE(EWI) = SE(h_disp_eq) and the
        # propagation is anchored on |h_disp_eq|, NOT on |EWI_m_pipe|. Anchoring
        # on EWI_m_pipe understates the error — severely at wells where the
        # equilibrium level sits near the datum and EWI_m_pipe is close to zero.
        #
        #   β₃-only : the dominant term; h_disp_eq ∝ 1/β₃, so the relative error
        #             in β₃ passes straight through.
        #   full    : first-order propagation over all three coefficients,
        #             treating them as independent. Collinearity between the
        #             recharge and atmospheric-draw terms is mild network-wide
        #             (C4, the worst case, has VIF ≈ 1.11), so this is a close
        #             approximation rather than an exact joint interval.
        se_b3_term = abs(h_disp_eq) * (se3 / b3) if np.isfinite(se3) else np.nan
        if np.isfinite(se1) and np.isfinite(se2) and np.isfinite(se3):
            num = b1 * P_bar - b2 * PET_bar
            var = ((P_bar * se1) ** 2
                   + (PET_bar * se2) ** 2
                   + (num * se3 / b3) ** 2) / (b3 ** 2)
            se_full = float(np.sqrt(var))
        else:
            se_full = np.nan
        return dict(well=w, network=network,
                    beta_1_recharge=b1, beta_2_atmospheric_draw=b2,
                    beta_3_drainage=b3,
                    se_beta_1=se1, se_beta_2=se2, se_beta_3=se3, n_obs=n_obs,
                    h_disp_eq_m=h_disp_eq,
                    EWI_m_pipe=ewi_pipe, EWI_m_bg=ewi_bg,
                    EWI_se_m_beta3=se_b3_term, EWI_se_m_full=se_full,
                    cluster_id=cluster_id)

    def _se_from_pvalue(beta, pval, n_obs, k=3):
        """Recover an OLS standard error from a committed coefficient/p-value.

        03_master_data.csv carries β, its two-sided p-value and n but not the
        standard error. For the no-intercept 3-predictor SSM the t statistic is
        t = β/SE on n−k degrees of freedom, so SE = β/|t| inverts exactly. Used
        only for the reference tier; extended-tier fits take se_beta_* straight
        from fit_ssm().
        """
        if not (np.isfinite(beta) and np.isfinite(pval) and np.isfinite(n_obs)):
            return np.nan
        df = int(n_obs) - k
        if df <= 0 or pval <= 0.0 or pval >= 1.0:
            return np.nan
        t = float(stats.t.isf(pval / 2.0, df))
        return abs(beta) / t if t > 0 else np.nan

    rows = []
    # ── reference tier: β from master_data ────────────────────────────────
    master = pd.read_csv(paths.INT_MASTER_DATA)
    master["well"] = master["Name_Original"].astype(str).str.strip().str.lower()
    for _, r in master.iterrows():
        if r["well"] in excluded:
            continue
        _b1 = r.get("beta_1_recharge", np.nan)
        _b2 = r.get("beta_2_atmospheric_draw", np.nan)
        _b3 = r.get("beta_3_drainage", np.nan)
        _n  = r.get("n", np.nan)
        row = _row(r["well"], _b1, _b2, _b3,
                   "reference", r.get("Cluster", np.nan),
                   se1=_se_from_pvalue(_b1, r.get("pvalue_beta_1", np.nan), _n),
                   se2=_se_from_pvalue(_b2, r.get("pvalue_beta_2", np.nan), _n),
                   se3=_se_from_pvalue(_b3, r.get("pvalue_beta_3", np.nan), _n),
                   n_obs=_n)
        if row:
            rows.append(row)

    # ── extended tier: fit β here via the shared fit_ssm() ────────────────
    try:
        ext = pd.read_csv(paths.INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
    except Exception as e:
        ext = None
        warn(f"extended-network file unavailable, EWI reference-only: {e}")
    if ext is not None:
        n_ext_fit = 0
        for w in ext.columns:
            wl = str(w).strip().lower()
            if wl in excluded:
                continue
            try:
                fit = fit_ssm(h_series=ext[w], climate=clim)
            except Exception as e:
                warn(f"extended {wl.upper()} SSM fit failed: {str(e)[:50]}")
                continue
            if not fit:                       # fit_ssm returns None for < min_obs
                continue
            row = _row(wl, fit.get("beta_1_recharge", np.nan),
                       fit.get("beta_2_atmospheric_draw", np.nan),
                       fit.get("beta_3_drainage", np.nan), "extended",
                       se1=fit.get("se_beta_1", np.nan),
                       se2=fit.get("se_beta_2", np.nan),
                       se3=fit.get("se_beta_3", np.nan),
                       n_obs=fit.get("n", np.nan))
            if row:
                rows.append(row); n_ext_fit += 1
        info(f"extended-network SSM fits contributing to EWI: {n_ext_fit}")

    ewi = pd.DataFrame(rows)
    if ewi.empty:
        return ewi
    # attach canonical cluster for extended wells (Pearson site-wide integration:
    # reference keeps its Original_Cluster; extended takes Best_Match_Cluster).
    try:
        site = pd.read_csv(paths.INT_PEAR_AUDIT_SITEWIDE)
        site["well"] = site["Well_Normalised"].astype(str).str.strip().str.lower()
        smap = site.set_index("well").apply(
            lambda r: r["Original_Cluster"] if pd.notna(r["Original_Cluster"])
            else r["Best_Match_Cluster"], axis=1)
        ewi["cluster_id"] = ewi.apply(
            lambda r: r["cluster_id"] if pd.notna(r["cluster_id"])
            else smap.get(r["well"], np.nan), axis=1)
    except Exception as e:
        warn(f"site-wide cluster attach failed (extended wells uncluster'd): {e}")
    ewi["cluster_id"]    = ewi["cluster_id"].astype("Int64")
    ewi["cluster_label"] = ewi["cluster_id"].map(config.CLUSTER_LABELS)
    locs = locations.copy()
    locs["well"] = locs["Name"].astype(str).str.strip().str.lower().str.replace(" ", "")
    ewi = ewi.merge(locs[["well", "E", "N"]], on="well", how="left")
    return ewi


def compute_ewi_msl5_comparison(ewi: pd.DataFrame,
                                latest: pd.DataFrame) -> tuple:
    """
    Per-well comparison of observed MSL5 against EWI-predicted MSL5 (v1.3.1).

    EWI is on its own (deeper-biased) scale, so it is calibrated onto the van
    Willegen MSL5 scale by an OLS fit of observed MSL5 on EWI across all wells
    carrying both (reference + extended). The fitted MSL5_pred is then reported
    per well alongside the observed value and the residual, so the prediction
    can be weighed directly. Wells with EWI but no observed MSL5 are retained
    with MSL5_pred only (unweighable, residual NaN).

    Returns (comparison_df, calibration_dict). No map — the report presents this
    as a per-well table / match-band summary (see report §4.8.5).
    """
    vw = {str(w).strip().lower() for w in config.VW_QUADRAT_WELLS}
    latest = latest.copy()
    latest["well"] = latest["well"].astype(str).str.strip().str.lower()
    comp = ewi.merge(latest[["well", "MSL5_m_bg", "window_end_year"]],
                     on="well", how="left")

    # Open-dune scope: EWI-predicted MSL5 is calibrated and reported as an
    # open-dune metric (C1–C3), mirroring MSL5's own open-dune framing (§4.8.4).
    # C4/C5 forest wells are predicted but flagged out-of-scope — the coefficients
    # are least constrained there (§4.9.2) and predictions degrade badly.
    comp["open_dune_scope"] = comp["cluster_id"].isin([1, 2, 3])

    cal = comp[(comp["open_dune_scope"])].dropna(subset=["EWI_m_bg", "MSL5_m_bg"])
    if len(cal) < 3:
        warn("too few open-dune wells with both EWI and observed MSL5 — comparison skipped")
        return pd.DataFrame(), {}
    b, a = np.polyfit(cal["EWI_m_bg"].to_numpy(), cal["MSL5_m_bg"].to_numpy(), 1)
    comp["MSL5_pred_m_bg"] = a + b * comp["EWI_m_bg"]
    comp["residual_mm"] = (comp["MSL5_pred_m_bg"] - comp["MSL5_m_bg"]) * 1000.0
    comp["in_van_willegen"] = comp["well"].isin(vw)

    # headline stats on the open-dune (in-scope) weighable wells
    scoped = comp[comp["open_dune_scope"]].dropna(subset=["residual_mm"])
    r = float(np.corrcoef(cal["EWI_m_bg"], cal["MSL5_m_bg"])[0, 1])
    rmse = float(np.sqrt((scoped["residual_mm"] ** 2).mean()))
    calib = dict(intercept_a=float(a), slope_b=float(b), r=r, r2=r * r,
                 rmse_mm_open_dune=rmse, n_calibration=int(len(cal)),
                 scope="open_dune_C1_C3")

    out = comp[["well", "network", "cluster_label", "open_dune_scope",
                "in_van_willegen", "EWI_m_bg", "MSL5_m_bg", "MSL5_pred_m_bg",
                "residual_mm", "window_end_year", "E", "N"]].copy()
    out = out.rename(columns={"cluster_label": "cluster",
                              "MSL5_m_bg": "MSL5_obs_m_bg",
                              "window_end_year": "obs_window_end"})
    out["well"] = out["well"].str.upper()
    out = out.sort_values(["network", "MSL5_obs_m_bg"], na_position="last")
    return out, calib





def compute_ebf_crossvalidation(elev: pd.DataFrame):
    """
    One-off-in-code, pipeline-generated Ellenberg-F cross-validation (v1.3.3).

    Reads the documented external van Willegen ecohydrology dataset
    (paths.DATA_ELLENBERG_EXT; van Willegen et al. 2024, Mendeley Data). If the
    file is absent the Pass is skipped cleanly and the rest of Script 26 runs.

    Between the 17 van Willegen piezometers, regresses mean Ellenberg-F on three
    water-table metrics — observed MSL5, the equilibrium index on the annual
    climatology, and on the spring climatology — reporting per-metric r (Fisher-z
    CI), RMSE (bootstrap CI), the Williams test for MSL5 vs the annual index, and
    A–D match bands. Correlations/RMSE are datum-invariant, so pipe-frame EWI and
    the dataset's own Mean Spring are used directly.

    Returns (per_well_df, summary_dict) or (None, None) if the input is absent.
    """
    from scipy.stats import pearsonr, t as _t
    xlsx = paths.DATA_ELLENBERG_EXT
    if not xlsx.exists():
        warn(f"external Ellenberg dataset not found at {xlsx} — EbF Pass skipped "
             f"(obtain from Mendeley doi:10.17632/p4xvb6xxp9.1)")
        return None, None
    try:
        _sheets = set(pd.ExcelFile(xlsx).sheet_names)
        _need = {"meanEbF", "Hydrology_metric_YearB"}
        if not _need.issubset(_sheets):
            warn(f"Ellenberg dataset at {xlsx} is missing sheet(s) {_need - _sheets} "
                 f"(found {sorted(_sheets)}) — EbF Pass skipped")
            return None, None
        ebf = pd.read_excel(xlsx, "meanEbF")
        yb = pd.read_excel(xlsx, "Hydrology_metric_YearB")
    except Exception as e:
        warn(f"Ellenberg dataset at {xlsx} present but unreadable ({type(e).__name__}: "
             f"{str(e)[:80]}) — EbF Pass skipped (needs openpyxl and the meanEbF / "
             f"Hydrology_metric_YearB sheets)")
        return None, None
    for c in ["EbF1a", "EbF1b", "EbF1c", "EbF1d"]:
        ebf[c] = pd.to_numeric(ebf[c], errors="coerce")
    ebf["EbF"] = ebf[["EbF1a", "EbF1b", "EbF1c", "EbF1d"]].mean(axis=1)
    ebf["piezo"] = (ebf["ID"].astype(str).str.rsplit("_", n=1).str[0]
                    .str.replace(r"-\d+$", "", regex=True).str.lower())
    ebf = ebf.dropna(subset=["EbF"]).groupby("piezo")["EbF"].mean()

    # observed MSL5 (dataset's own Mean Spring, 5-yr rolling, per-piezo mean)
    yb["piezo"] = yb["Statistic"].astype(str).str.replace(r"-\d+$", "", regex=True).str.lower()
    piv = yb.pivot_table(index="Year", columns="piezo", values="Mean Spring")
    msl5 = piv.rolling(5, min_periods=5).mean().mean().rename("MSL5")

    # EWI per piezometer from committed β on annual and spring climatologies
    clim = pd.read_csv(paths.INT_CLIMATE, index_col=0, parse_dates=True)
    P_ann, PET_ann = clim["P_m"].mean(), clim["PET"].mean()
    sp = clim[clim.index.month.isin(config.MSL_SPRING_MONTHS)]
    P_sp, PET_sp = sp["P_m"].mean(), sp["PET"].mean()
    md = pd.read_csv(paths.INT_MASTER_DATA); md["piezo"] = md["Name_Original"].str.lower()
    md["EWI_annual"] = (md["beta_1_recharge"] * P_ann - md["beta_2_atmospheric_draw"] * PET_ann) \
        / md["beta_3_drainage"] - config.DRAINAGE_DATUM
    md["EWI_spring"] = (md["beta_1_recharge"] * P_sp - md["beta_2_atmospheric_draw"] * PET_sp) \
        / md["beta_3_drainage"] - config.DRAINAGE_DATUM
    md = md.set_index("piezo")[["EWI_annual", "EWI_spring", "Cluster"]]

    df = pd.DataFrame({"EbF": ebf}).join(msl5).join(md).dropna(subset=["EbF", "MSL5", "EWI_annual"])
    n = len(df)

    def _fit(col, B=5000):
        x, y = df[col].to_numpy(), df["EbF"].to_numpy()
        b, a = np.polyfit(x, y, 1); pred = a + b * x
        res = np.abs(y - pred); rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
        r = float(pearsonr(x, y)[0])
        z, se = np.arctanh(r), 1 / np.sqrt(len(x) - 3)
        rlo, rhi = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
        rng = np.random.default_rng(0); bs = []
        for _ in range(B):
            i = rng.integers(0, len(x), len(x))
            bb, aa = np.polyfit(x[i], y[i], 1)
            bs.append(np.sqrt(np.mean((y[i] - (aa + bb * x[i])) ** 2)))
        return dict(r=r, r_lo=float(rlo), r_hi=float(rhi), rmse=rmse,
                    rmse_lo=float(np.percentile(bs, 2.5)), rmse_hi=float(np.percentile(bs, 97.5)),
                    resid=res)

    fit = {c: _fit(c) for c in ["MSL5", "EWI_annual", "EWI_spring"]}

    # Williams' test: MSL5 vs annual EWI as EbF predictors (dependent)
    r_ey = pearsonr(df["MSL5"], df["EbF"])[0]
    r_ez = pearsonr(df["EWI_annual"], df["EbF"])[0]
    r_yz = pearsonr(df["MSL5"], df["EWI_annual"])[0]
    R = (1 - r_ey**2 - r_ez**2 - r_yz**2) + 2 * r_ey * r_ez * r_yz
    t_w = (r_ey - r_ez) * np.sqrt((n - 1) * (1 + r_yz) /
          (2 * ((n - 1) / (n - 3)) * R + ((r_ey + r_ez)**2 / 4) * (1 - r_yz)**3))
    p_w = float(2 * (1 - _t.cdf(abs(t_w), n - 3)))

    # A–D match bands (Ellenberg-F units), MSL5 vs annual EWI
    edges = [0, 0.15, 0.30, 0.50, np.inf]; labs = ["A", "B", "C", "D"]
    bands = {}
    for lab, lo, hi in zip(labs, edges[:-1], edges[1:]):
        bands[lab] = (int(((fit["MSL5"]["resid"] > lo) & (fit["MSL5"]["resid"] <= hi)).sum()),
                      int(((fit["EWI_annual"]["resid"] > lo) & (fit["EWI_annual"]["resid"] <= hi)).sum()))

    out = df.copy(); out.index.name = "piezo"; out = out.reset_index()
    out["piezo"] = out["piezo"].str.upper()
    out["resid_MSL5"] = fit["MSL5"]["resid"]
    out["resid_EWI_annual"] = fit["EWI_annual"]["resid"]
    out = out[["piezo", "Cluster", "EbF", "MSL5", "EWI_annual", "EWI_spring",
               "resid_MSL5", "resid_EWI_annual"]]

    summary = dict(n=n, fit=fit, williams_t=float(t_w), williams_p=p_w, bands=bands,
                   r_MSL5=fit["MSL5"]["r"], r_EWI_annual=fit["EWI_annual"]["r"])
    return out, summary


def plot_ebf_scatter(df: pd.DataFrame, summary: dict, out: Path) -> None:
    """Three-panel between-well EbF scatter: MSL5 | annual EWI | spring EWI (Fig XX)."""
    panels = [("MSL5", "5-yr mean spring level MSL5 (m)", "(a) Observed MSL5"),
              ("EWI_annual", "Equilibrium index, annual climate (m)", "(b) EWI — annual"),
              ("EWI_spring", "Equilibrium index, spring climate (m)", "(c) EWI — spring")]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), sharey=True)
    for ax, (col, xlab, title) in zip(axes, panels):
        for cid in sorted(df["Cluster"].dropna().astype(int).unique()):
            s = df[df["Cluster"] == cid]
            ax.scatter(s[col], s["EbF"], s=55, edgecolor="k", linewidth=0.4,
                       color=config.CLUSTER_COLOURS.get(cid, "grey"),
                       label=config.CLUSTER_LABELS.get(cid, f"C{cid}"), zorder=3)
        m, c = np.polyfit(df[col], df["EbF"], 1); xs = np.array([df[col].min(), df[col].max()])
        ax.plot(xs, m * xs + c, "k--", lw=1, zorder=2)
        r = summary["fit"][col]["r"]
        ax.set_xlabel(xlab); ax.set_title(f"{title}\nr = {r:+.2f}  (n = {summary['n']})", fontsize=10)
    axes[0].set_ylabel("Mean Ellenberg-F (moisture)")
    axes[2].legend(fontsize=7, loc="lower right", title="Habitat")
    fig.tight_layout(); render_figure(fig, out); plt.close(fig)


def _partial_spearman(frame: pd.DataFrame, x: str, y: str, z: str):
    """Rank partial correlation of x and y controlling for z.

    Spearman ranks are regressed on the control's ranks and the residuals
    correlated, which is the standard rank analogue of a partial correlation.
    Returns (r, p, n); NaNs if fewer than four complete cases.
    """
    d = frame[[x, y, z]].dropna()
    if len(d) < 4:
        return np.nan, np.nan, len(d)
    xr, yr, zr = (stats.rankdata(d[c]) for c in (x, y, z))
    rx = xr - np.poly1d(np.polyfit(zr, xr, 1))(zr)
    ry = yr - np.poly1d(np.polyfit(zr, yr, 1))(zr)
    r, p = stats.pearsonr(rx, ry)
    return float(r), float(p), len(d)


# ── Pass 8: metric diagnostics ────────────────────────────────────────────────
def compute_metric_diagnostics(annual: pd.DataFrame,
                               per_well: pd.DataFrame,
                               ewi: pd.DataFrame) -> tuple:
    """Window sensitivity of MSL5, and the precision of the two indices.

    Report §4.8.6 / §6.9 rest on three findings, all emitted here rather than
    computed in prose:

    1. Spring levels are NOT serially correlated. Reading the fitted drainage
       term as a first-order recession predicts a year-to-year persistence of
       exp(−12·β₃) — from ≈0.3 at C1 to ≈0.8 at C4. The observed lag-1
       autocorrelation of annual spring level is near zero at every cluster and
       is uncorrelated with the recession time. Spring is the seasonal maximum,
       reached after the winter recharge season, so each winter resets the
       water table: the monthly recession operates within the annual cycle, not
       across it. The five-year mean therefore behaves as intended.

    2. Window sensitivity is nonetheless graded across the network, and it is a
       matter of AMPLITUDE, not memory. What governs the interannual spring
       standard deviation — and hence the standard error of a window mean — is
       β₂, not β₃. The two are themselves correlated across wells, which is why
       the recession time looks diagnostic when examined alone.

    3. The two indices fail at the same wells for opposite reasons: MSL5
       through the high β₂ that drives amplitude, the equilibrium index through
       the low and weakly-identified β₃ in its denominator.

    Returns (per_well_diagnostics, per_cluster_precision, report_numbers dict).
    """
    win = int(MSL_DEFAULT_WINDOW_YEARS)
    ann_valid = annual[annual["valid"]].copy()
    ann_valid["well"] = ann_valid["well"].astype(str).str.strip().str.lower()

    rows = []
    for _, e in ewi.iterrows():
        w = str(e["well"]).strip().lower()

        # Annual spring series, reindexed over the full span so that missing
        # years appear as gaps rather than silently closing up — an
        # autocorrelation across a gap would otherwise pair non-adjacent years.
        s = ann_valid.loc[ann_valid["well"] == w].set_index("hydro_year")["MSL_m_pipe"]
        s = s.sort_index()
        if len(s):
            s = s.reindex(range(int(s.index.min()), int(s.index.max()) + 1))
        n_spr = int(s.notna().sum())
        if n_spr >= DIAG_MIN_SPRINGS:
            sd_mm = float(s.std(ddof=1) * 1000.0)
            rho = float(s.autocorr(1))
        else:
            sd_mm, rho = np.nan, np.nan

        # Realised window sensitivity: the spread of this well's own MSL5
        # series, an observed quantity rather than a modelled one.
        pw = per_well[(per_well["well"] == w)
                      & (per_well["n_years_in_window"] >= MSL_MIN_YEARS_IN_WINDOW)]
        spread_mm = (float((pw["MSL5_m_pipe"].max() - pw["MSL5_m_pipe"].min()) * 1000.0)
                     if len(pw) > 2 else np.nan)

        b3 = float(e["beta_3_drainage"])
        se3 = e.get("se_beta_3", np.nan)
        msl5_se = sd_mm / np.sqrt(win) if np.isfinite(sd_mm) else np.nan
        ewi_se_b3 = (float(e["EWI_se_m_beta3"]) * 1000.0
                     if np.isfinite(e.get("EWI_se_m_beta3", np.nan)) else np.nan)
        ewi_se_full = (float(e["EWI_se_m_full"]) * 1000.0
                       if np.isfinite(e.get("EWI_se_m_full", np.nan)) else np.nan)

        rows.append(dict(
            well=w, network=e["network"],
            cluster_id=e.get("cluster_id", pd.NA),
            cluster_label=e.get("cluster_label", None),
            n_springs=n_spr, n_msl5_windows=int(len(pw)),
            n_obs_ssm=e.get("n_obs", np.nan),
            spring_sd_mm=sd_mm,
            rho_lag1=rho,
            rho_ar1_expected=float(np.exp(-12.0 * b3)),
            t_R_months=1.0 / b3 if b3 > 0 else np.nan,
            beta_2=float(e["beta_2_atmospheric_draw"]),
            beta_3=b3,
            se_beta_3=float(se3) if np.isfinite(se3) else np.nan,
            rel_se_beta_3=float(se3) / b3 if (np.isfinite(se3) and b3 > 0) else np.nan,
            msl5_window_se_mm=msl5_se,
            msl5_window_spread_mm=spread_mm,
            ewi_se_mm_beta3=ewi_se_b3,
            ewi_se_mm_full=ewi_se_full,
            ewi_over_msl5_se_beta3=(ewi_se_b3 / msl5_se
                                    if np.isfinite(ewi_se_b3) and np.isfinite(msl5_se)
                                    and msl5_se > 0 else np.nan),
        ))

    diag = pd.DataFrame(rows)
    if diag.empty:
        return diag, pd.DataFrame(), {}

    # ── cluster rollup, both network scopes ───────────────────────────────
    # 'reference' is the citable basis (Script 03 QA'd β); 'all' adds the
    # extended tier, whose shorter records bear on the coverage question and
    # which materially changes only C5, where the reference tier has n=5.
    out = []
    for scope in ("reference", "all"):
        sub = diag if scope == "all" else diag[diag["network"] == "reference"]
        for cid, g in sub.groupby("cluster_id", dropna=True):
            gs = g.dropna(subset=["spring_sd_mm"])
            out.append(dict(
                network_scope=scope,
                cluster_id=cid,
                cluster_label=config.CLUSTER_LABELS.get(
                    int(cid) if pd.notna(cid) else -1, None),
                n_wells=int(len(g)),
                n_wells_with_springs=int(len(gs)),
                t_R_months_median=float(g["t_R_months"].median()),
                rho_ar1_expected_mean=float(g["rho_ar1_expected"].mean()),
                rho_lag1_mean=float(gs["rho_lag1"].mean()) if len(gs) else np.nan,
                spring_sd_mm_median=float(gs["spring_sd_mm"].median()) if len(gs) else np.nan,
                msl5_window_se_mm_median=float(gs["msl5_window_se_mm"].median()) if len(gs) else np.nan,
                ewi_se_mm_beta3_median=float(g["ewi_se_mm_beta3"].median()),
                ewi_se_mm_full_median=float(g["ewi_se_mm_full"].median()),
            ))
    prec = pd.DataFrame(out)
    if not prec.empty:
        prec["ewi_over_msl5_ratio_beta3"] = (prec["ewi_se_mm_beta3_median"]
                                             / prec["msl5_window_se_mm_median"])
        prec["ewi_over_msl5_ratio_full"] = (prec["ewi_se_mm_full_median"]
                                            / prec["msl5_window_se_mm_median"])
        prec = prec.sort_values(["network_scope", "cluster_id"])

    # ── scalar statistics cited in the report ─────────────────────────────
    d = diag.dropna(subset=["rho_lag1", "spring_sd_mm"])
    nums = {"diag_min_springs": DIAG_MIN_SPRINGS, "diag_n_wells": int(len(d))}

    if len(d) >= 4:
        r, p = stats.spearmanr(d["t_R_months"], d["rho_lag1"])
        nums["rho_lag1_vs_tR_spearman_r"] = float(r)
        nums["rho_lag1_vs_tR_spearman_p"] = float(p)
        nums["rho_lag1_mean"] = float(d["rho_lag1"].mean())
        nums["rho_ar1_expected_mean"] = float(d["rho_ar1_expected"].mean())
        r, p = stats.spearmanr(d["beta_2"], d["t_R_months"])
        nums["beta2_vs_tR_spearman_r"] = float(r)
        nums["beta2_vs_tR_spearman_p"] = float(p)
        for lab, (x, z) in {"beta2_given_tR": ("beta_2", "t_R_months"),
                            "tR_given_beta2": ("t_R_months", "beta_2")}.items():
            r, p, _ = _partial_spearman(d, x, "spring_sd_mm", z)
            nums[f"partial_springSD_vs_{lab}_r"] = r
            nums[f"partial_springSD_vs_{lab}_p"] = p

    # Site-mean spring series: the network-scale counterpart to the per-well
    # autocorrelation, free of per-well measurement noise.
    site = (ann_valid.groupby("hydro_year")["MSL_m_pipe"].mean().sort_index())
    if len(site):
        site = site.reindex(range(int(site.index.min()), int(site.index.max()) + 1))
        if int(site.notna().sum()) >= DIAG_MIN_SPRINGS:
            nums["site_mean_spring_rho_lag1"] = float(site.autocorr(1))
            nums["site_mean_spring_n_years"] = int(site.notna().sum())

    # Index comparison, and the short-record question: does β₃ precision decay
    # with a shorter record? If not, the equilibrium index carries no penalty
    # for the extended tier's later start.
    cmp_ = diag.dropna(subset=["ewi_se_mm_beta3", "msl5_window_se_mm"])
    if len(cmp_):
        nums["n_wells_index_comparison"] = int(len(cmp_))
        nums["n_wells_ewi_more_precise_than_msl5"] = int(
            (cmp_["ewi_se_mm_beta3"] < cmp_["msl5_window_se_mm"]).sum())
    ext = diag[(diag["network"] == "extended")].dropna(
        subset=["rel_se_beta_3", "n_obs_ssm"])
    if len(ext) >= 4:
        r, p = stats.spearmanr(ext["n_obs_ssm"], ext["rel_se_beta_3"])
        nums["extended_relSE_beta3_vs_nobs_spearman_r"] = float(r)
        nums["extended_relSE_beta3_vs_nobs_spearman_p"] = float(p)

    return diag, prec, nums


def plot_metric_diagnostics(diag: pd.DataFrame, prec: pd.DataFrame,
                            out: Path) -> None:
    """Two panels: the autocorrelation null, and index precision by cluster.

    Left  — observed lag-1 autocorrelation against the AR(1) value implied by
            each well's β₃, with the 1:1 line. Points fall far below it.
    Right — median standard error of the two indices per cluster, on a shared
            axis so the comparison is direct.
    """
    d = diag.dropna(subset=["rho_lag1", "rho_ar1_expected"])
    p = prec[prec["network_scope"] == "reference"].dropna(
        subset=["msl5_window_se_mm_median"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6))

    for cid, g in d.groupby("cluster_id", dropna=True):
        ax1.scatter(g["rho_ar1_expected"], g["rho_lag1"], s=34,
                    color=config.CLUSTER_COLOURS.get(int(cid), "0.4"),
                    edgecolor="white", linewidth=0.5, zorder=3,
                    label=config.CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))
    lim = [-0.6, 1.0]
    ax1.plot(lim, lim, ls="--", lw=1.0, color="0.35", zorder=2,
             label="1:1 (AR(1) expectation)")
    ax1.axhline(0.0, lw=0.8, color="0.6", zorder=1)
    ax1.set_xlim(0, 1.0); ax1.set_ylim(*lim)
    ax1.set_xlabel("Persistence implied by β₃,  exp(−12·β₃)")
    ax1.set_ylabel("Observed lag-1 autocorrelation of annual spring level")
    ax1.set_title("(a) Spring levels are not serially correlated", loc="left")
    ax1.legend(fontsize=7, loc="upper left", framealpha=0.9)

    x = np.arange(len(p)); wbar = 0.38
    ax2.bar(x - wbar / 2, p["msl5_window_se_mm_median"], wbar,
            color="#4C72B0", edgecolor="white", label="MSL5 (5-year window mean)")
    ax2.bar(x + wbar / 2, p["ewi_se_mm_beta3_median"], wbar,
            color="#C44E52", edgecolor="white", label="Equilibrium index (β₃ only)")
    ax2.errorbar(x + wbar / 2, p["ewi_se_mm_full_median"], fmt="_", ms=14,
                 color="0.15", lw=1.4, ls="none", zorder=4,
                 label="Equilibrium index (all three β)")
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(s).split(" ")[0] for s in p["cluster_label"]])
    ax2.set_ylabel("Standard error (mm)")
    ax2.set_title("(b) Index precision by cluster", loc="left")
    ax2.legend(fontsize=7, framealpha=0.9)
    ax2.grid(axis="y", lw=0.4, alpha=0.4)
    ax2.set_axisbelow(True)

    fig.tight_layout()
    render_figure(fig, out)
    plt.close(fig)


# ── Pass 9: Supplementary Table S7.1 emitter ──────────────────────────────────
# Column headings for the rendered table. Kept as a module constant so the CSV
# and Markdown renderings cannot drift apart, and so a heading change is a
# one-line edit rather than a hunt through two writers.
# Headings are deliberately terse: ten columns have to fit portrait width in the
# Supplementary Material, and units are carried in the caption rather than
# repeated in every heading. The CSV and the ODT table must stay identical, so
# any heading change here is a change to the document too.
TABLE_S7_1_COLUMNS = [
    "Well",
    "Network",
    "Cluster",
    "β₃ (mth⁻¹)",
    "EWI (m bg)",
    "SE (mm)",
    "MSL5 obs",
    "MSL5 recon",
    "Resid. (mm)",
    "Status",
]

# Status values. Three-valued rather than two independent flags: nine columns
# fit a portrait page and eleven do not, and the distinction that matters to a
# reader is a single ordinal one — did this well set the calibration, was it
# only reconstructed by it, or is it outside its scope entirely.
# Terse for the same width reason; the caption defines all three.
STATUS_CALIBRATION   = "Calibration"
STATUS_RECONSTRUCTED = "Reconstructed"
STATUS_OUT_OF_SCOPE  = "Out of scope"


def _fmt(value, dp: int, blank: str = "") -> str:
    """Fixed-decimal string, or `blank` where the value is missing."""
    if value is None or not np.isfinite(value):
        return blank
    return f"{value:.{dp}f}"


def emit_supplementary_table_s7_1(ewi: pd.DataFrame, comp: pd.DataFrame,
                                  calib: dict):
    """
    Render Supplementary Table S7.1 — per-well equilibrium wetness index and
    MSL5 reconstruction (v1.5.0).

    Report §4.8.6 closes by promising "the full per-well reconstruction, with
    the out-of-scope forest wells flagged", pointing at the Supplementary
    Material. This emitter produces that table.

    It computes NOTHING. Every value is read from the Pass 5 index frame (`ewi`)
    or the Pass 6 comparison frame (`comp`), and the calibration constants come
    from the Pass 6 `calib` dict rather than being restated here. That is
    deliberate: a table transcribed or recomputed by hand drifts silently the
    next time the pipeline runs, and the whole point of an emitter is that it
    cannot.

    Scope, following §4.8.6. The MSL5 calibration is scoped to the open-dune
    network (C1–C3, reference and extended). Of the 64 open-dune wells carrying
    an index, 62 also carry an observed MSL5 and set the calibration; the other
    two lack a valid five-year spring window and are reconstructed only. The 20
    C4/C5 forest wells are reconstructed but held out of scope — their
    coefficients are the least constrained on the site and the estimate is too
    coarse to place a well across a Curreli threshold. All 84 appear in the
    table, because the scoping is only visible if the out-of-scope wells are
    present and flagged.

    Standard errors are the β₃-only variant (`EWI_se_m_beta3`) — the dominant
    term, since the equilibrium displacement is inversely proportional to β₃.
    The full three-coefficient variant remains in the per-well CSV. Note that
    the propagation behind both is anchored on |h_disp_eq|, not |EWI_m_pipe|;
    see compute_equilibrium_wetness_index() and report §3.7.6.

    Returns (display_df, caption). Empty frame and empty caption if the inputs
    cannot support the table.
    """
    if ewi.empty or comp.empty:
        return pd.DataFrame(), ""

    base = ewi.copy()
    base["_well_key"] = base["well"].astype(str).str.strip().str.lower()

    # comp uppercases `well` in its final projection; rejoin on a normalised key
    # rather than assuming either frame's case convention.
    c = comp.copy()
    c["_well_key"] = c["well"].astype(str).str.strip().str.lower()
    keep = ["_well_key", "open_dune_scope", "MSL5_obs_m_bg",
            "MSL5_pred_m_bg", "residual_mm"]
    missing = [k for k in keep if k not in c.columns]
    if missing:
        warn(f"Table S7.1 — comparison frame lacks {missing}; table not written")
        return pd.DataFrame(), ""

    df = base.merge(c[keep], on="_well_key", how="left")

    unmatched = int(df["open_dune_scope"].isna().sum())
    if unmatched:
        warn(f"Table S7.1 — {unmatched} well(s) present in the index but absent "
             f"from the comparison frame; their status cannot be determined")

    def _status(r) -> str:
        scope = r["open_dune_scope"]
        if not isinstance(scope, (bool, np.bool_)):
            return ""
        if not bool(scope):
            return STATUS_OUT_OF_SCOPE
        obs = r["MSL5_obs_m_bg"]
        return (STATUS_CALIBRATION if (obs is not None and np.isfinite(obs))
                else STATUS_RECONSTRUCTED)

    df["_status"] = df.apply(_status, axis=1)

    # Cluster order C1→C5 from the canonical cluster_id, reference before
    # extended within a cluster, then alphabetical. cluster_label comes from
    # config.CLUSTER_LABELS upstream — never a raw Ward integer.
    df["_net_order"] = (df["network"].astype(str).str.lower()
                        .map({"reference": 0, "extended": 1}).fillna(9))
    df = df.sort_values(["cluster_id", "_net_order", "_well_key"],
                        na_position="last")

    out = pd.DataFrame({
        TABLE_S7_1_COLUMNS[0]: df["_well_key"].str.upper(),
        TABLE_S7_1_COLUMNS[1]: df["network"].astype(str).str.capitalize(),
        TABLE_S7_1_COLUMNS[2]: df["cluster_label"].astype(str),
        TABLE_S7_1_COLUMNS[3]: [_fmt(v, 4) for v in df["beta_3_drainage"]],
        TABLE_S7_1_COLUMNS[4]: [_fmt(v, 3) for v in df["EWI_m_bg"]],
        TABLE_S7_1_COLUMNS[5]: [_fmt(v * 1000.0 if v is not None
                                     and np.isfinite(v) else np.nan, 0)
                                for v in df["EWI_se_m_beta3"]],
        TABLE_S7_1_COLUMNS[6]: [_fmt(v, 3) for v in df["MSL5_obs_m_bg"]],
        TABLE_S7_1_COLUMNS[7]: [_fmt(v, 3) for v in df["MSL5_pred_m_bg"]],
        TABLE_S7_1_COLUMNS[8]: [_fmt(v, 0) for v in df["residual_mm"]],
        TABLE_S7_1_COLUMNS[9]: df["_status"],
    })

    n_total = len(out)
    n_cal   = int((df["_status"] == STATUS_CALIBRATION).sum())
    n_rec   = int((df["_status"] == STATUS_RECONSTRUCTED).sum())
    n_out   = int((df["_status"] == STATUS_OUT_OF_SCOPE).sum())

    # Caption built from the data, so its numbers cannot disagree with the rows
    # beneath it. Calibration constants come from the Pass 6 fit. No section
    # number is hard-typed here — generated output that cites §3.7.6 would go
    # stale the next time the report's section numbering drifts.
    a = calib.get("intercept_a")
    b = calib.get("slope_b")
    r = calib.get("r")
    rmse = calib.get("rmse_mm_open_dune")
    fit_txt = ""
    if all(v is not None and np.isfinite(v) for v in (a, b, r, rmse)):
        fit_txt = (f" reconstructed from the open-dune calibration "
                   f"MSL5 = {a:+.3f} + {b:.3f}·EWI "
                   f"(r = {r:.2f}, RMSE = {rmse:.0f} mm)")

    caption = (
        f"Table S7.1. Equilibrium wetness index and MSL5 reconstruction, per "
        f"well (n = {n_total}). Levels are metres below ground surface, "
        f"negative below the surface. The index is{fit_txt}, fitted on the "
        f"{n_cal} in-scope wells carrying an observed five-year mean spring "
        f"level. A further {n_rec} open-dune well(s) carry an index but no "
        f"valid five-year spring window and are reconstructed only; the "
        f"{n_out} C4/C5 forest wells are reconstructed but held out of scope, "
        f"their coefficients being the least constrained on the site. Status "
        f"reads: '{STATUS_CALIBRATION}', an in-scope well that entered the fit; "
        f"'{STATUS_RECONSTRUCTED}', in scope but with no observed spring level; "
        f"'{STATUS_OUT_OF_SCOPE}', a forest well outside the calibration's "
        f"scope. "
        f"Standard errors on the index propagate the drainage coefficient "
        f"alone, the dominant term; the full three-coefficient variant is "
        f"carried in {OUT_EWI.name}. Source: {OUT_EWI.name}, "
        f"{OUT_EWI_COMPARISON.name}."
    )
    return out, caption


def write_supplementary_table_s7_1(out: pd.DataFrame, caption: str,
                                   csv_path: Path, md_path: Path) -> None:
    """
    Write the two renderings of Table S7.1.

    CSV — display strings, for Paste Special > Unformatted text into the ODT,
    which routes through LibreOffice's text-import dialogue and lands as a
    table. The caption is written as a trailing comment line rather than a
    header row, so the pasted block is the table alone.

    Markdown — the same table for review before pasting.
    """
    out.to_csv(csv_path, index=False)
    with open(csv_path, "a", encoding="utf-8") as fh:
        fh.write(f"\n# {caption}\n")

    header = "| " + " | ".join(out.columns) + " |"
    rule   = "|" + "|".join("---" for _ in out.columns) + "|"
    rows   = ["| " + " | ".join(str(v) for v in r) + " |"
              for r in out.itertuples(index=False, name=None)]
    md = "\n".join([header, rule, *rows])
    md_path.write_text(f"{md}\n\n*{caption}*\n", encoding="utf-8")


def main() -> int:
    banner("26", "van Willegen MSL Projection")
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

    # Reference-network cluster source: the post-anchor-remap canonical
    # cluster store from Script 02. This is the same file Script 03 reads
    # into 03_master_data.csv, so cluster IDs match every downstream
    # consumer. Prior to v1.1.3 (2026-05-27) this read
    # 02_07_cluster_membership_k5.csv (a pre-remap bootstrap-sweep
    # diagnostic file with raw Ward IDs); that introduced a clean three-
    # way permutation between Script 26's cluster_id and the canonical
    # ID set, mislabelling 35 of the 66 reference wells. See
    # DIAGNOSTIC_REPORT_script_26_cluster_assignment.md (in CHANGELOG.md
    # under the 2026-05-27 entry).
    ref_clusters = pd.read_csv(paths.INT_CLUSTER_STATS)
    print(f"  {paths.INT_CLUSTER_STATS.name:<28s} : {ref_clusters.shape[0]} wells")

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
    saved(f"{OUT_ANNUAL.name}")

    # ── Pass 2 ────────────────────────────────────────────────────────────
    per_well = rolling_5yr(annual)
    print(f"\nPass 2 — 5-year rolling MSL/MAX: "
          f"{len(per_well)} (well, end_year) rows across "
          f"{per_well['well'].nunique()} wells")

    # ── Cluster attach ─────────────────────────────────────────────────────
    per_well_with_cluster = attach_cluster_ids(per_well, ref_clusters, ext_clusters)

    # ── MSL5 well exclusion (whole-analysis, flagged) ──────────────────────
    # Ridge-flank forest wells whose drainage memory makes the 5-year MSL
    # window unreliable (config.MSL5_EXCLUDED_WELLS). Rows are RETAINED in the
    # per-well CSV with an msl5_excluded flag; every derived MSL5 product uses
    # the included-only subset (per_well_incl). Method B centroid (Pass 3b) is a
    # separate regional-average construct and is intentionally not filtered here.
    _excl = {w.strip().lower() for w in config.MSL5_EXCLUDED_WELLS}
    _wl = per_well_with_cluster["well"].astype(str).str.strip().str.lower()
    per_well_with_cluster["msl5_excluded"] = _wl.isin(_excl)
    per_well_with_cluster["msl5_excluded_reason"] = _wl.map(
        lambda w: config.MSL5_EXCLUDED_WELLS.get(w, ""))
    per_well_with_cluster.to_csv(OUT_5YR, index=False)
    saved(f"{OUT_5YR.name}")
    _present = sorted(set(_wl[per_well_with_cluster["msl5_excluded"]]))
    if _present:
        print("  MSL5 exclusion (flagged in per-well CSV; removed from cluster "
              "trajectory / latest / map): " + ", ".join(w.upper() for w in _present))
    per_well_incl = per_well_with_cluster[~per_well_with_cluster["msl5_excluded"]].copy()

    # ── Pass 3 — Cluster trajectory (Method A: per-well aggregation) ───────
    per_cluster = cluster_trajectory(per_well_incl)
    per_cluster.to_csv(OUT_CLUSTER, index=False)
    print(f"\nPass 3 — cluster trajectories (Method A, per-well aggregation): "
          f"{len(per_cluster)} (cluster, year) rows")
    saved(f"{OUT_CLUSTER.name}")

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
    saved(f"{OUT_CLUSTER_CENTROID.name}")

    # ── Pass 4 — Latest per well ───────────────────────────────────────────
    latest = (per_well_incl.sort_values("window_end_year")
                                    .groupby("well", as_index=False).tail(1))
    latest.to_csv(OUT_LATEST, index=False)
    print(f"\nPass 4 — latest MSL5 per well: {len(latest)} wells")
    saved(f"{OUT_LATEST.name}")

    # ── Pass 5 — Equilibrium Wetness Index (v1.3.1) ────────────────────────
    print("\nPass 5 — equilibrium wetness index (EWI) from SSM coefficients")
    ewi = compute_equilibrium_wetness_index(elev, locations)
    if ewi.empty:
        warn("EWI produced no rows — check 03_master_data.csv β coefficients")
    else:
        ewi.to_csv(OUT_EWI, index=False)
        saved(f"{OUT_EWI.name}")
        for net in ["reference", "extended"]:
            sub = ewi[ewi["network"] == net]
            if len(sub):
                info(f"  {net:<10s} n={len(sub):>3d}  "
                     f"EWI mean={sub['EWI_m_bg'].mean():+.3f} m below ground")

    # ── Pass 6 — EWI-predicted MSL5 comparison (v1.3.1) ────────────────────
    print("\nPass 6 — EWI-predicted MSL5 vs observed (per-well comparison)")
    # Hoisted out of the Pass 6 block (v1.5.0) so Pass 9 can render from them.
    # report_nums accumulates across Passes 6 and 8 and is written once after
    # Pass 8, so the calibration constants reach a committed CSV even when the
    # Pass 8 diagnostics are skipped.
    comp = pd.DataFrame()
    calib: dict = {}
    report_nums: dict = {}
    if not ewi.empty:
        comp, calib = compute_ewi_msl5_comparison(ewi, latest)
        if not comp.empty:
            comp.to_csv(OUT_EWI_COMPARISON, index=False)
            saved(f"{OUT_EWI_COMPARISON.name}")
            # The MSL5 = a + b·EWI constants are quoted in report §4.8.6 and in
            # the Table S7.1 caption; until v1.5.0 they reached only the run
            # transcript and so had no committed-CSV trace.
            report_nums.update({f"ewi_msl5_{k}": v for k, v in calib.items()})
            info(f"  open-dune calibration  MSL5 = {calib['intercept_a']:+.3f} + "
                 f"{calib['slope_b']:.3f}·EWI   "
                 f"(n={calib['n_calibration']}, r={calib['r']:.3f}, "
                 f"RMSE={calib['rmse_mm_open_dune']:.0f} mm)")
            scoped = comp[comp["open_dune_scope"]].dropna(subset=["residual_mm"])
            am = scoped["residual_mm"].abs()
            for lab, m in [("≤50 mm", am <= 50), ("50–100 mm", (am > 50) & (am <= 100)),
                           ("100–200 mm", (am > 100) & (am <= 200)), (">200 mm", am > 200)]:
                info(f"    |residual| {lab:<10s}: {int(m.sum()):>2d} open-dune wells")
            vw = scoped[scoped["in_van_willegen"]]; nvw = scoped[~scoped["in_van_willegen"]]
            info(f"  generalization: RMSE {np.sqrt((nvw['residual_mm']**2).mean()):.0f} mm "
                 f"on {len(nvw)} non-van-Willegen open-dune wells vs "
                 f"{np.sqrt((vw['residual_mm']**2).mean()):.0f} mm on {len(vw)} calibration wells")
            forest = comp[~comp["open_dune_scope"]].dropna(subset=["residual_mm"])
            if len(forest):
                info(f"  out-of-scope forest (C4/C5): n={len(forest)}, "
                     f"RMSE {np.sqrt((forest['residual_mm']**2).mean()):.0f} mm "
                     f"(predicted but flagged unreliable)")

    # ── Pass 7 — Ellenberg-F cross-validation (v1.3.3, external input) ─────
    print("\nPass 7 — Ellenberg-F cross-validation (MSL5 vs EWI; external dataset)")
    ebf_df, ebf_summary = compute_ebf_crossvalidation(elev)
    if ebf_df is not None:
        ebf_df.to_csv(paths.OUT_26_EBF_COMPARISON, index=False)
        saved(f"{paths.OUT_26_EBF_COMPARISON.name}")
        f = ebf_summary["fit"]
        info(f"  EbF ~ MSL5:  r={f['MSL5']['r']:+.3f} [{f['MSL5']['r_lo']:+.2f},{f['MSL5']['r_hi']:+.2f}]  "
             f"RMSE={f['MSL5']['rmse']:.3f} EbF-units")
        info(f"  EbF ~ EWI :  r={f['EWI_annual']['r']:+.3f} [{f['EWI_annual']['r_lo']:+.2f},{f['EWI_annual']['r_hi']:+.2f}]  "
             f"RMSE={f['EWI_annual']['rmse']:.3f} EbF-units")
        info(f"  Williams' test (MSL5 vs EWI): t={ebf_summary['williams_t']:+.3f}, "
             f"p={ebf_summary['williams_p']:.3f} "
             f"({'indistinguishable' if ebf_summary['williams_p'] >= 0.05 else 'distinguishable'})")
        info("  match bands (MSL5 / EWI): " +
             ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in ebf_summary["bands"].items()))
        try:
            plot_ebf_scatter(ebf_df, ebf_summary, paths.OUT_26_EBF_SCATTER)
            saved(f"{paths.OUT_26_EBF_SCATTER.name}")
        except Exception as e:
            warn(f"EbF scatter (Fig XX) render failed ({type(e).__name__}: "
                 f"{str(e)[:80]}) — comparison CSV was written; figure not produced")

    # ── Pass 8 — Metric diagnostics (v1.4.0) ───────────────────────────────
    print("\nPass 8 — metric diagnostics (window sensitivity and index precision)")
    diag = prec = pd.DataFrame()
    diag_nums = {}
    if ewi.empty:
        skipped("metric diagnostics — no EWI rows to characterize")
    else:
        diag, prec, diag_nums = compute_metric_diagnostics(annual, per_well, ewi)
        if diag.empty:
            warn("metric diagnostics produced no rows")
        else:
            diag.to_csv(paths.OUT_26_METRIC_DIAGNOSTICS, index=False)
            saved(f"{paths.OUT_26_METRIC_DIAGNOSTICS.name}")
            prec.to_csv(paths.OUT_26_INDEX_PRECISION, index=False)
            saved(f"{paths.OUT_26_INDEX_PRECISION.name}")
            report_nums.update(diag_nums)

            info(f"  autocorrelation (n={diag_nums.get('diag_n_wells', 0)} wells with "
                 f"≥{DIAG_MIN_SPRINGS} springs): observed lag-1 mean "
                 f"{diag_nums.get('rho_lag1_mean', float('nan')):+.3f} against an "
                 f"AR(1) expectation of {diag_nums.get('rho_ar1_expected_mean', float('nan')):.3f}")
            if "site_mean_spring_rho_lag1" in diag_nums:
                info(f"    site-mean spring series: ρ={diag_nums['site_mean_spring_rho_lag1']:+.3f} "
                     f"over {diag_nums['site_mean_spring_n_years']} years")
            info(f"    ρ vs recession time: Spearman "
                 f"r={diag_nums.get('rho_lag1_vs_tR_spearman_r', float('nan')):+.3f}, "
                 f"p={diag_nums.get('rho_lag1_vs_tR_spearman_p', float('nan')):.3f} "
                 f"— no association")
            info("  interannual spring SD (what drives window sensitivity):")
            info(f"    vs β₂ controlling for t_R: partial r="
                 f"{diag_nums.get('partial_springSD_vs_beta2_given_tR_r', float('nan')):+.3f}, "
                 f"p={diag_nums.get('partial_springSD_vs_beta2_given_tR_p', float('nan')):.2e}")
            info(f"    vs t_R controlling for β₂: partial r="
                 f"{diag_nums.get('partial_springSD_vs_tR_given_beta2_r', float('nan')):+.3f}, "
                 f"p={diag_nums.get('partial_springSD_vs_tR_given_beta2_p', float('nan')):.3f}")
            info(f"    (β₂ and t_R themselves correlate at Spearman "
                 f"{diag_nums.get('beta2_vs_tR_spearman_r', float('nan')):+.3f})")
            n_better = diag_nums.get("n_wells_ewi_more_precise_than_msl5")
            if n_better is not None:
                info(f"  index precision: the equilibrium index is more precise than a "
                     f"5-year MSL5 mean at {n_better}/"
                     f"{diag_nums.get('n_wells_index_comparison', 0)} wells")
            for _, r in prec[prec["network_scope"] == "reference"].iterrows():
                info(f"    {str(r['cluster_label']):<22s} MSL5 SE "
                     f"{r['msl5_window_se_mm_median']:>6.0f} mm | EWI SE "
                     f"{r['ewi_se_mm_beta3_median']:>7.0f} mm | ratio "
                     f"{r['ewi_over_msl5_ratio_beta3']:.2f}")
            try:
                plot_metric_diagnostics(diag, prec, paths.OUT_26_METRIC_DIAG_FIG)
                saved(f"{paths.OUT_26_METRIC_DIAG_FIG.name}")
            except Exception as e:
                warn(f"metric diagnostics figure render failed ({type(e).__name__}: "
                     f"{str(e)[:80]}) — CSVs were written; figure not produced")

    # Scalar statistics cited in §4.8.6 / §6.9, written once (v1.5.0) now that
    # the accumulator is filled by both Pass 6 and Pass 8.
    if report_nums:
        (pd.DataFrame(sorted(report_nums.items()), columns=["key", "value"])
           .to_csv(paths.OUT_26_REPORT_NUMBERS, index=False))
        saved(f"{paths.OUT_26_REPORT_NUMBERS.name}")
    else:
        skipped("report numbers — neither the calibration nor the diagnostics "
                "produced any statistics")

    # ── Pass 9 — Supplementary Table S7.1 (v1.5.0) ─────────────────────────
    print("\nPass 9 — Supplementary Table S7.1 (per-well EWI reconstruction)")
    if ewi.empty or comp.empty:
        skipped("Table S7.1 — the index or comparison frame is empty")
    else:
        s7_1, s7_1_caption = emit_supplementary_table_s7_1(ewi, comp, calib)
        if s7_1.empty:
            warn("Table S7.1 produced no rows")
        else:
            write_supplementary_table_s7_1(s7_1, s7_1_caption,
                                           OUT_TABLE_S7_1_CSV,
                                           OUT_TABLE_S7_1_MD)
            saved(f"{OUT_TABLE_S7_1_CSV.name}")
            saved(f"{OUT_TABLE_S7_1_MD.name}")
            counts = s7_1[TABLE_S7_1_COLUMNS[9]].value_counts()
            info(f"  {len(s7_1)} wells listed")
            for label in (STATUS_CALIBRATION, STATUS_RECONSTRUCTED,
                          STATUS_OUT_OF_SCOPE):
                info(f"    {label:<16s} {int(counts.get(label, 0)):>3d}")

    # ── Figures ────────────────────────────────────────────────────────────
    print("\nRendering figures...")
    plot_cluster_trajectory(per_cluster, OUT_TRAJ)
    saved(f"{OUT_TRAJ.name}")
    plot_quadrat_wells(per_well_incl, OUT_QUADRAT)
    saved(f"{OUT_QUADRAT.name}")
    plot_msl5_map(latest, locations, elev, OUT_MAP)
    saved(f"{OUT_MAP.name}")

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
