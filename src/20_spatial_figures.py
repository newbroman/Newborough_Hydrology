"""
20_spatial_figures.py
=====================
Publication-quality spatial figures for Section 4.9 of:

  Hollingham, M. (2026) "Hydrogeological Dynamics, Behavioural Clustering and
  Management Intervention Analysis at Newborough Warren Coastal Sand Dune
  Aquifer, Wales". Journal of Hydrology: Regional Studies.

Sixteen figure builders run in a full pass — main() calls each in turn — and
between them write 25 output files (18 figures, 7 tables); the complete list is
in the Outputs block below. Two of the 18 figures are show_head=True variants
that a default pass does not produce, so a default pass writes 23 files. The
two headline figures are:

  Figure 1 — Mean Annual Water Table with Stream Network and Flow Vectors
  -----------------------------------------------------------------------
  Output: outputs/20_spatial_figures/20_head_surface_streams.png

  Mean annual water table (m AOD) as an interpolated surface over a
  greyscale DEM hillshade, with:
    - SAGA stream network (skeletonised) as connected blue polylines
    - Groundwater flow direction vectors: the unit-normalised negative head
      gradient (direction only). No hydraulic conductivity enters — this is
      not a Darcy flux quiver. Darcy K (config.DRAWDOWN_K_MDAY) is used by
      the drawdown-propagation figure, not here.
    - Site feature overlays (forest boundary, lake, clearfell zone, channels)
    - Well symbols coloured by cluster
    - 1 m head contours with labels

  Note on the surface: the local helper is named idw_surface() for historical
  reasons but calls scipy.interpolate.griddata(method="linear") — piecewise-
  linear barycentric interpolation over a Delaunay triangulation, not
  inverse-distance weighting. The same naming caveat applies to
  map_utils.add_idw_surface().

  Figures 2a / 2b — SSM Water Balance Residual and Ridge Hillslope Gradient
  ------------------------------------------------------------------------
  Outputs: outputs/20_spatial_figures/20_residual_ssm.png
           outputs/20_spatial_figures/20_slope_gradient.png

  Two separate single-panel figures — plot_residual_ssm() and
  plot_slope_gradient() — read side by side as a validation pair:
    2a: SSM water balance residual — where the water balance requires
        external inflow (β coefficients only, no DEM)
    2b: Ridge hillslope gradient (50 m smoothed DEM) — independent
        topographic evidence consistent with ridge-originating recharge
  Spatial correspondence in the NW forest/ridge zone is consistent with
  ridge-derived water balance residual (CEH14 α computed at runtime).
  Note: there are no natural watercourses on the dune warren; D8 flow
  accumulation was discarded as it does not represent real recharge paths.

Outputs
-------
  All paths resolve under outputs/20_spatial_figures/ and come from the
  OUT_20_* import block. Keep this list in step with that block.

  Figures
    20_head_surface_streams.png         — plot_head_streams()        [Fig 1]
    20_residual_ssm.png                 — plot_residual_ssm()        [Fig 2a]
    20_slope_gradient.png               — plot_slope_gradient()      [Fig 2b]
    20_drawdown_propagation_nohead.png  — plot_drawdown_propagation() [Fig 3]
    20_drawdown_propagation.png         — plot_drawdown_propagation(show_head=True);
                                          not written by a default main() pass
    20_coastal_erosion.png              — plot_coastal_erosion()     [Fig 4]
    20_slr_response.png                 — plot_slr_response()        [Fig 5]
    20_coastal_net_effect.png           — plot_coastal_net_effect()  [Fig 6]
    20_scrape_drawdown_nohead.png       — plot_scrape_drawdown()     [Fig 7]
    20_scrape_drawdown.png              — plot_scrape_drawdown(show_head=True);
                                          not written by a default main() pass
    20_clearfell_baseline_drawdown.png  — plot_scrape_coastal_net()
    20_public_drivers_panel.png         — plot_public_panel()
    20_msl5_change_2017_2023.png        — plot_msl5_change()
    20_observed_change_2012_2026.png    — plot_observed_change()
    20_net_state_map.png                — plot_net_state_map()
    20_driver_change_2005_2025.png      — plot_driver_change_2005_2025()
    20_driver_change_20yr.png           — plot_driver_change_20yr()
    20_clearfell_gain.png               — plot_clearfell_gain()

  Tables
    20_drawdown_perwell.csv             — plot_drawdown_propagation()
    20_report_numbers.csv               — plot_drawdown_propagation()
    20_residual_perwell.csv             — plot_residual_ssm()
    20_residual_report_numbers.csv      — plot_residual_ssm()
    20_msl5_change_perwell.csv          — plot_msl5_change()
    20_msl5_report_numbers.csv          — plot_msl5_change()
    20_scrape_drawdown_perwell.csv      — plot_scrape_drawdown()

Inputs
------
  outputs/01_wells_clean_maod.csv       — per-well monthly maOD heads
  outputs/01_locations.csv              — well coordinates
  outputs/01_well_elevations.csv        — DEM ground elevations
  outputs/03_master_data.csv            — β coefficients, cluster, coordinates
  outputs/01_climate.csv                — monthly P and PET
  data/newborough_dem.tif               — LiDAR DEM (EPSG:27700, 2 m res)
  data/streams.kml                      — SAGA stream network (polygon cells)
  data/Features.kml                     — site feature overlays

Called by
---------
  run_analysis.py  (or standalone: python 20_spatial_figures.py [--preview])

Dependencies
------------
  Standard: numpy, pandas, matplotlib, scipy, rasterio, pyproj
  Spatial:  scikit-image (skimage.morphology, skimage.measure)
            Install: pip install scikit-image

References
----------
  Betson et al. (2002) — hydraulic conductivity K (config.DRAWDOWN_K_MDAY)
  Freeman (2008) — canopy interception for the C4/C5 forest clusters
                   (config.FOREST_INTERCEPTION, applied to config.FOREST_CIDS)
  Curreli et al. (2013) — eco-hydrological thresholds (config.SD15b / config.SD16)
"""

__version__ = "1.41.0"  # Hollingham (2026) — 2026-08-29. The coastal edge
#   drawdown h₀ now reaches a committed CSV. It was computed inside the plotting
#   functions and rendered straight into the figure, so no *_report_numbers.csv
#   carried it and neither audit_number_drift nor cite_check could bind the
#   value the report types — which is how report8:757 and the report9:894
#   caption kept h₀ = 21 mm, _load_coastal_fit()'s May-2026 fallback snapshot
#   (δ₀=28.83), after the live fit moved to δ₀=31.33 and h₀ to 22.6 mm (W77).
#   Five rows added to 20_report_numbers.csv: coastal_h0, coastal_h0_per_metre,
#   coastal_delta0, coastal_retreat_rate and coastal_reach_L. The construction
#   h₀ = retreat × (δ₀/COAST_RETREAT_RATE), previously written out at each call
#   site, is centralised in _coastal_edge_h0(); the two existing call sites now
#   read it. Behaviour-preserving — Figures 3, 4 and 6 verified byte-identical
#   against the committed outputs. 09f_management_effects.py:316 still carries
#   its own copy and is left for a session that can rerun it.
# v1.40.1  # Hollingham (2026) — 2026-08-26. Docstring-only sweep
#   (T-14 items 13 and 14, plus one off-list catch). The module header claimed
#   "Two figures are produced" and described Figure 2 as two-panel; there are
#   16 plot_* builders writing 25 OUT_20_* files, and the residual and slope
#   panels are separate figures. The header now carries a full Outputs block
#   derived from the OUT_20_* import list. The flow quiver is described as the
#   unit-normalised head gradient rather than a "normalised Darcy quiver" — no
#   conductivity term enters it. Off-list: idw_surface() is
#   griddata(method="linear"), not IDW, so both its own docstring and the
#   header no longer call the head surface IDW. No executable line changed.
#
# v1.40.0  # Hollingham (2026) — 2026-08-22. The reach is now
#   written at the granularity the documents quote it at. quote_reach_m()
#   rounds to config.REACH_QUOTE_NEAREST_M wherever λ is annotated on a figure
#   or printed to the console; the drawdown field is still built from the
#   unrounded length and 20_report_numbers.csv still stores it unrounded. The
#   figure and the prose previously disagreed on a quantity neither of them had
#   got wrong, which is the kind of divergence the number sweep could not see.
#   The coastal reach L and the diffusion length √(Dt) are deliberately left at
#   metre granularity: their quoted values in the documents are exact, and
#   rounding them here would create the divergence this change removes.
#
# v1.39.0  # Hollingham (2026) — 2026-08-20. The forest-drawdown
#     per-well CSV now stores the distance dd_mm was actually computed on.
#     plot_drawdown_propagation() decays the drawdown along a FLOW-WEIGHTED
#     cost distance (Dijkstra, cost = base_dist*(1 - 0.4*alignment) +
#     max(0, dz)*2.0), but 20_drawdown_perwell.csv carried only the Euclidean
#     dist_forest_m. The two differ substantially — CEH1 is 49 m Euclidean
#     against 14 m cost — so the file read as self-inconsistent and the
#     figure's own contour claims could not be checked against any committed
#     output. Report §4.9.4 had said the drawdown "exceeds 50 mm only within
#     ~100 m of the forest edge" when H0 = 150 mm and lambda ~ 230 m put that
#     contour at lambda*ln(3) ~ 249 m; the claim went uncaught because the
#     column needed to test it was never written. Adds dist_cost_m and
#     dist_basis ("inside" / "cost" / "euclidean_fallback", the last marking
#     wells off the grid where the Euclidean distance stands in), and sorts
#     the CSV on the cost distance. Additive columns; dd_mm is unchanged.
#     Also adds 20_scrape_drawdown_perwell.csv: plot_scrape_drawdown()
#     computed a per-well value and threw it away, so the scrape field had no
#     committed output at all and §4.9.6's contour claim was uncheckable.
#     That field is a SUPERPOSITION of one source per cut, each with an image
#     sink, on Euclidean distance — not the forest's cost-distance geometry —
#     so no single exp(-d/lambda) radius describes it.
# 1.38.5 — Hollingham (2026) — 2026-08-19. Reads the per-well
#   WTF Sy table from OUT_18_WELL_SY_TABLE; INT_WTF_WELL_SY is retired
#   (D-038). Pure path/symbol change, values identical.
#
# v1.38.4  # Hollingham (2026) — 2026-08-18. Adds two report
#   numbers to 20_residual_report_numbers.csv: residual_c4_median_beta3 and
#   residual_ceh14_b3_c4median. The water-balance residual carries beta_3
#   directly (residual = b2*PET_bar + b3*h_disp - b1*P_bar), so at CEH14 —
#   the one well with a negative beta_3 — the residual is driven negative by
#   the very coefficient the field was being used to adjudicate. The new keys
#   publish CEH14's residual recomputed with the C4 per-well median beta_3,
#   all other terms held at CEH14's own fitted values, so Methods Supplement
#   S.16 can quote a committed CSV. No figure, surface, existing key or
#   published value changes. The C4 cluster id is derived from
#   config.CLUSTER_LABELS, not typed.
#
# v1.38.3  # Hollingham (2026) — 2026-08-18. _measured_ceh36_response()
#   falls back to pipeline_params.default_value('ceh36_scrape_response_m')
#   instead of a typed 0.1295. Earlier: the three fast-path
#   point-in-polygon tests moved from shapely.vectorized.contains, deprecated
#   and due for removal, to shapely.contains_xy — the same call Script 19 has
#   used since it was written. Identical semantics; the per-cell prepared-
#   geometry fallback is unchanged and still catches a pre-2.0 shapely.
#
# v1.38.1  # Hollingham (2026) — 2026-08-16
#
# 1.38.1 (2026-08-16): map-extent note only, no behaviour change (northern
#   edge 365800 vs config.SITE_MAP_NORTH_MAX 365500; see the note at
#   SEA_SOUTH_N and DECISION_LOG D-013).
# 1.38.0 (2026-08-09): prior state.
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import argparse
import warnings
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from scipy.interpolate import griddata
from scipy.ndimage import uniform_filter
from matplotlib.colors import TwoSlopeNorm
from pyproj import Transformer
import xml.etree.ElementTree as ET

from utils.paths import (
    make_all_dirs, DATA_DIR, DATA_DEM, DATA_KML_FEATURES, DATA_KML_STREAMS,
    DATA_KML_SITE_BOUNDARY, DATA_COASTLINE_HWM, KML_BROADLEAF,
    DIR_20, OUT_20_HEAD_STREAMS, OUT_20_RESIDUAL_SSM, OUT_20_SLOPE,
    OUT_20_DRAWDOWN, OUT_20_DRAWDOWN_NOHEAD,
    OUT_20_DRAWDOWN_PERWELL, OUT_20_REPORT_NUMBERS,
    OUT_20_SCRAPE_DRAWDOWN_PERWELL,
    OUT_20_RESIDUAL_PERWELL, OUT_20_RESIDUAL_REPORT_NUMBERS,
    OUT_20_MSL5_CHANGE_PERWELL, OUT_20_MSL5_REPORT_NUMBERS,
    OUT_20_COASTAL_EROSION, OUT_20_SLR_RESPONSE,
    OUT_20_COASTAL_NET, OUT_20_SCRAPE_DRAWDOWN, OUT_20_SCRAPE_DRAWDOWN_NOHEAD,
    OUT_20_CLEARFELL_BASELINE_DRAWDOWN, OUT_20_PUBLIC_PANEL,
    OUT_20_NET_STATE_MAP, OUT_20_CLEARFELL_GAIN, OUT_20_OBSERVED_CHANGE,
    OUT_20_DRIVER_CHANGE, OUT_20_DRIVER_CHANGE_20YR,
    OUT_20_MSL5_CHANGE,
    OUT_09_BACI_SHIFTS,
    OUT_10B_STEP_DATA,
    OUT_10A_REPORT,
    INT_WELLS_CLEAN_MAOD, INT_WELLS_CLEAN,
    INT_LOCATIONS, INT_WELL_ELEVATIONS,
    INT_MASTER_DATA, INT_CLIMATE, INT_WELLS_EXTENDED, INT_PEAR_AUDIT_SITEWIDE,
    OUT_18_WELL_SY_TABLE, OUT_03_MECHANISTIC_TABLE,
    OUT_25_FIT_PARAMETERS, OUT_25_PER_WELL_SLOPES,
    OUT_26_5YR_PER_WELL,
)
from utils.map_utils import (load_dem_hillshade, load_scrape_kml, add_en_axes,
                             add_idw_surface)
from utils.config import (CLUSTER_COLOURS, CLUSTER_LABELS, DRAINAGE_DATUM, FOREST_INTERCEPTION,
                          SCRAPE_KML_FILES,
                          DRAWDOWN_H0_MM, DRAWDOWN_K_MDAY, DRAWDOWN_B_M,
                          REACH_QUOTE_NEAREST_M,
                          BROADLEAF_INTERCEPTION, BL_CANOPY_FRACTION_2005,
                          BL_CANOPY_FRACTION_2025, COAST_CHRONIC_YEARS,
                          COAST_RETREAT_M, COAST_RETREAT_RATE,
                          SCRAPE_RISE_BUFFER_M,
                          SLR_WINDOW_YEARS, SLR_RISE_M, SLR_SHORE_LEVEL_M,
                          CEH36_E, CEH36_N)
from utils.data_utils import normalize_well_name
from utils.report_numbers_utils import ReportNumbers


def quote_reach_m(length_m: float) -> float:
    """The reach as it is WRITTEN, not as it is used.

    The e-folding length is built from an assumed conductivity and saturated
    thickness, so it is quoted to the nearest REACH_QUOTE_NEAREST_M throughout
    the corpus. Every figure annotation and console line goes through this;
    the drawdown field and the stored value do not.
    """
    step = REACH_QUOTE_NEAREST_M
    return round(float(length_m) / step) * step

from utils.render_utils import render_figure
from utils.coastal_utils import coastal_edge_h0, load_measured_retreat_rate

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
XLIM       = (240100, 243900)
YLIM       = (362200, 365000)
GRID_XI    = np.arange(XLIM[0], XLIM[1] + 50, 50)
GRID_YI    = np.arange(YLIM[0], YLIM[1] + 50, 50)
KML_NS     = "http://www.opengis.net/kml/2.2"
T_WGS_BNG  = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)

# FOREST_INTERCEPTION imported from config.py (Freeman 2008, 0.24).

# Sea boundary anchor constants (matching script 19).
# DELIBERATELY WIDER than the shoreline anchors in Script 11b and
# map_utils._SEA_* (362350 / 243850). Ruling: Martin, 2026-08-09 — Script 20's
# box is intentional for these figures and is NOT to be unified with the
# shoreline values; on the canonical 50 m grid the two rules differ over 228
# cells (4.5%). Do not "fix" this to match 11b/map_utils.
# NOTE (2026-08-16): the northern edge here is 365800, NOT config.SITE_MAP_NORTH_MAX
# (365500). Retained deliberately - Martin's call - so this figure's framing is
# unchanged by the config extent revision, matching the explicit local pin in
# 11c_pflood_achievability.py (_NORTH_MAX_11C). Do NOT repoint to config without
# a decision: it re-frames the rendered maps. See DECISION_LOG D-013.
SEA_SOUTH_N      = 362200
SEA_EAST_E       = 243900
SEA_WEST_E       = 239200
SEA_WEST_N_MAX   = 363400
SEA_EAST_N_MAX   = 365000
SEA_ANCHOR_SPACING = 200

# ── Coastal-erosion figure parameters ────────────────────────────────────────
# External assumptions for plot_coastal_erosion(). The δ₀ (coast-edge anomaly)
# and L (inland reach) are NOT set here — they are read live from Script 25's
# fit-parameters CSV (forest-free linear-capped row) so the map stays in sync
# with the canonical coastal-retreat regression. Only the genuinely external
# assumptions live below; each is a FLAG for editorial/scientific review.
#
#   COAST_RETREAT_M        single-event shoreline retreat to visualise (m).
#                          6 m ≈ the Storm Brendan (early 2020) acute event.
#   COAST_RETREAT_RATE     long-term retreat rate (m/yr) used to convert the
#                          chronic δ₀ (mm/yr) into a per-metre-of-retreat
#                          sensitivity. ≈50 m over 2014–2020 (Forgrave 2020).
#                          *** The edge magnitude scales inversely with this:
#                          the whole map hinges on it. ***
#   COAST_DUNE_OFFSET_M    distance the erosion front sits inland of the DEM
#                          waterline, i.e. the dune toe where the aquifer
#                          effectively begins. Uniform schematic offset.
#   COAST_SHORE_LEVEL_M    DEM elevation (m AOD) whose contour is taken as the
#                          waterline before offsetting.
#   COAST_EAST_CUT_E       easting east of which the DEM waterline contour is
#                          discarded, to keep only the SW-facing Caernarfon Bay
#                          shore (excludes lake / Menai-side low ground).
# COAST_RETREAT_M and COAST_RETREAT_RATE are imported from config.py (shared
# with Scripts 09d/09f) — do not redeclare them here.
COAST_DUNE_OFFSET_M   = 100.0    # m inland to dune toe
COAST_SHORE_LEVEL_M   = 0.5      # m AOD waterline contour
COAST_EAST_CUT_E      = 242300   # m, keep SW shore west of this

# ── Sea-level-rise head-response figure parameters ───────────────────────────
# Companion to plot_coastal_erosion(). Models the water-table head GAIN from a
# gradual rise in mean sea level at the Caernarfon Bay boundary, as a finite-
# window transient (NOT steady state): the boundary head-rise diffuses inland
# and attenuates with the complementary error function over the diffusion
# length √(D·t), D = K·b/Sy being the same hydraulic diffusivity used by
# plot_drawdown_propagation().
#
#     Δh(d) = SLR · erfc( d / (2·√(D·t)) )
#
# This is a deliberately single-mechanism illustration of GRADUAL SLR, to sit
# beside the DISCRETE storm-retreat erosion map. The two are physically
# different kinds of forcing (gradual vs episodic) and are not reduced to a
# common annual rate — see the figure caption / §5. Each constant is a FLAG.
#
#   SLR_WINDOW_YEARS   the response window t (yr), config.py
#   SLR_RISE_M         mean-sea-level rise accumulated over the window (m),
#                      config.py — a UKCP18-referenced scenario input.
#   SLR_SHORE_LEVEL_M  the boundary datum (m AOD), config.py — mean sea level,
#                      NOT the erosion dune-toe front (COAST_SHORE_LEVEL_M).
#
# All three are imported from config.py and must not be redeclared here.
# SLR_WINDOW_YEARS is a DISTINCT quantity from COAST_CHRONIC_YEARS even while
# the two hold the same value — see the note beside them in config.py.
# K and b come from DRAWDOWN_K_MDAY / DRAWDOWN_B_M; Sy is read live from the C3
# WTF estimates (same source as the drawdown map), not hardcoded.

# ── Scrape-drain drawdown figure parameters ──────────────────────────────────
# External assumptions for plot_scrape_drawdown(). Illustrative SCENARIO map of
# the steady-state drawdown a coastal dune-scrape would impose on the
# surrounding water table, propagating INLAND from the excavation as a drain
# (phreatic-evaporation / discharge sink that recruits surrounding groundwater
# and lowers it — the §5.4.2 "topographic drain" reading, sign-consistent with
# the CEH36 wet-slack BACI). The decay length λ = √(K·b/(Sy·β₃)) is the SAME
# leaky-aquifer length used by plot_drawdown_propagation(), with Sy and β₃ read
# live from the C3 (Western Residual) propagation medium — NOT set here. Only
# the genuinely external scenario assumptions live below; each is a review FLAG.
#
#   SCRAPE_CENTRE_E/N      centre of the excavation (m, OSGB36). Default = CEH22
#                          (241375, 362907), the southern coastal margin well
#                          used as the worked example. Move to relocate (e.g.
#                          config.CEH36_E / CEH36_N for the documented 2015 site).
#   SCRAPE_LONG_M          long-axis length (m), pointing into the warren.
#   SCRAPE_SHORT_M         short-axis length (m).
#   SCRAPE_BEARING_DEG     bearing of the long axis (° from N, clockwise).
#                          45° = NE, i.e. long axis aimed inland/upgradient.
#   SCRAPE_H0_MM           ASSUMED edge drawdown at the excavation (mm). This is
#                          a scenario input, NOT derived from Sy: removing
#                          unsaturated sand does not lower the table by Sy×depth
#                          (see §5.4 discussion); H0 is treated as a flagged
#                          assumption exactly as the coastal δ₀ is. Default 40
#                          mm = the "20% of a 0.2 m cut" figure, carried as an
#                          assumption only. *** The whole field scales linearly
#                          with this. ***
#   SCRAPE_FAVOUR_UPGRADIENT  if True the cost-distance is weighted to favour
#                          UP-gradient (inland) propagation — the physically
#                          correct sense for a coastal sink drawing from the
#                          warren — i.e. the OPPOSITE of the forest figure's
#                          downhill/seaward weighting. Set False for isotropic.
SCRAPE_CENTRE_E          = CEH36_E    # config.py (CEH36 — documented 2015 scrape);
SCRAPE_CENTRE_N          = CEH36_N    #   override here to relocate the scenario
SCRAPE_LONG_M            = 60.0       # m, long axis into the warren
SCRAPE_SHORT_M           = 30.0       # m, short axis
SCRAPE_BEARING_DEG       = 45.0       # ° from N (NE long axis)
SCRAPE_FAVOUR_UPGRADIENT = True       # drain pulls inland (flip forest weight)
SCRAPE_TRUNCATE_SEAWARD  = False      # seaward half-plane + foreshore clip.
# SCRAPE_RISE_BUFFER_M is imported from config.py (shared with Scripts 09d/09f)
# — do not redeclare it here. The scraped footprint RISES (slack restoration);
# the rise is confined to the scrape KML footprints plus that collar, and is
# shown as the rise zone rather than drawdown.
SCRAPE_TIMESCALE         = "Feb 2013 · Apr 2015 · Oct 2023 cuts"  # three scraping epochs
                                      # True for a SHORE-margin scrape (e.g.
                                      # CEH22) where the sea pins the seaward
                                      # head and the drain draws only landward;
                                      # False for an INLAND scrape (e.g. CEH36,
                                      # ~450 m inland) which drains all round.
SCRAPE_SEAWARD_MIN_ELEV_M = 1.5       # m AOD; zero drawdown on ground below
                                      # this (foreshore/beach) — the water
                                      # table there is pinned near sea level
                                      # and cannot be drawn down by the drain,
                                      # so the cone is truncated at the coast.

# ── Shared drawdown fill scale ───────────────────────────────────────────────
# Common colour scale for the three drawdown-type filled maps so they are
# directly comparable colour-to-colour: coastal erosion (Fig 4), forest
# drawdown (Fig 3, no-head) and scrape drawdown (Fig 7, no-head). Forest
# drawdown reaches ~150 mm at the source while erosion/scrape reach only
# ~20–50 mm, so the level set is deliberately BANDED (denser at the low end):
# with explicit contourf levels each band is an equal-width colour segment on
# the colorbar, so the small-magnitude maps still get low-end resolution while
# the forest map spans the full range. NOTE: this decouples the erosion map
# from the SLR map (Fig 5), which keeps its own [2…50] linear set — they are
# different quantities (loss vs gain) and use different colormaps anyway.
DRAWDOWN_FILL_LEVELS = [2, 5, 10, 25, 50, 100, 150]
DRAWDOWN_LINE_LEVELS = [5, 10, 25, 50, 100]   # drawn where in range
DRAWDOWN_LINE_LABELS = [5, 10, 25, 50, 100]
# Discrete per-band colours (one per interval of DRAWDOWN_FILL_LEVELS) chosen for
# clear adjacent contrast at the LOW end — the continuous YlOrBr sampled the
# 2–5 / 5–10 / 10–25 bands as near-identical pale creams. Warm yellow→brown ramp
# (avoids clashing with the red C3 well markers); set_over for >150 mm.
from matplotlib.colors import ListedColormap as _ListedCmap
DRAWDOWN_BAND_COLOURS = ["#fff3b0", "#fcd34d", "#f59e0b",
                         "#ea7317", "#c2410c", "#7c2d12"]
DRAWDOWN_CMAP        = _ListedCmap(DRAWDOWN_BAND_COLOURS)
DRAWDOWN_CMAP.set_over("#5c1d02")
DRAWDOWN_ALPHA       = 0.62


def _sea_boundary_points():
    """Zero-head anchor points along sea/estuary boundaries."""
    pts, vals = [], []
    for e in np.arange(SEA_WEST_E, SEA_EAST_E + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([e, SEA_SOUTH_N]); vals.append(0.0)
    for n in np.arange(SEA_SOUTH_N, SEA_EAST_N_MAX + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([SEA_EAST_E, n]); vals.append(0.0)
    for n in np.arange(SEA_SOUTH_N, SEA_WEST_N_MAX + SEA_ANCHOR_SPACING,
                       SEA_ANCHOR_SPACING):
        pts.append([SEA_WEST_E, n]); vals.append(0.0)
    return np.array(pts), np.array(vals)


def _site_mask(gx, gy):
    """Rectangular mask clipped to sea boundaries."""
    mask = np.ones(gx.shape, dtype=bool)
    mask[gy < SEA_SOUTH_N] = False
    mask[gx > SEA_EAST_E]  = False
    mask[gx < SEA_WEST_E]  = False
    return mask


_SITE_POLY_CACHE = None


def load_site_polygon():
    """
    Load and merge the study-area outline from ``data/site_boundary.kml``
    into a single shapely (Multi)Polygon in EPSG:27700, for clipping
    gridded surfaces to the true edge of the warren (coast, estuary and
    landward margins) rather than the crude rectangular sea cutoffs.

    Returns a shapely geometry, or ``None`` if the file or the GIS stack
    is unavailable (callers should fall back to the rectangular mask).
    Mirrors the merge/simplify approach used in script 19.
    """
    global _SITE_POLY_CACHE
    if _SITE_POLY_CACHE is not None:
        return _SITE_POLY_CACHE
    try:
        import geopandas as gpd
        import fiona
        from shapely.ops import unary_union
        fiona.drvsupport.supported_drivers["KML"] = "rw"
        site_path = DATA_KML_SITE_BOUNDARY
        if not site_path.exists():
            print("  [WARNING] site_boundary.kml not found — "
                  "falling back to rectangular sea mask")
            return None
        gdf = gpd.read_file(str(site_path), driver="KML").to_crs("EPSG:27700")
        merged = unary_union([g for g in gdf.geometry if g is not None])
        # Light simplify to keep the polygon manageable for point-in-poly
        # tests without losing the coastline/estuary shape.
        _SITE_POLY_CACHE = merged.simplify(20, preserve_topology=True)
        print(f"  site_boundary.kml loaded for clipping "
              f"(type={_SITE_POLY_CACHE.geom_type})")
        return _SITE_POLY_CACHE
    except Exception as e:
        print(f"  [WARNING] could not load site_boundary.kml ({e}) — "
              "falling back to rectangular sea mask")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
def load_data():
    """Load all inputs. Returns dict of DataFrames."""
    data = {}

    maod = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    maod.columns = [normalize_well_name(c) for c in maod.columns]
    data["maod"] = maod

    locs = pd.read_csv(INT_LOCATIONS)
    locs["Match_ID"] = locs["Match_ID"].apply(normalize_well_name)
    data["locations"] = locs

    elev = pd.read_csv(INT_WELL_ELEVATIONS)
    elev["Name_norm"] = elev["Name_norm"].apply(normalize_well_name)
    data["elevations"] = elev

    md = pd.read_csv(INT_MASTER_DATA)
    md["Name_Original"] = md["Name_Original"].apply(normalize_well_name)
    data["master"] = md

    clim = pd.read_csv(INT_CLIMATE, parse_dates=["Date"], index_col="Date")
    data["climate"] = clim

    # Extended wells
    if INT_WELLS_EXTENDED.exists():
        ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
        ext.columns = [normalize_well_name(c) for c in ext.columns]
        data["extended"] = ext
    else:
        data["extended"] = None

    if INT_PEAR_AUDIT_SITEWIDE.exists():
        site = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
        data["site_audit"] = site
    else:
        data["site_audit"] = None

    return data


def build_well_table(data):
    """
    Build per-well table with coordinates, cluster, mean head, β coefficients,
    and water balance residual. Extended wells are included for spatial
    context (location + cluster) but have no SSM residual.
    """
    maod  = data["maod"]
    locs  = data["locations"]
    elev  = data["elevations"]
    md    = data["master"]
    clim  = data["climate"]
    ext   = data.get("extended")
    site  = data.get("site_audit")

    # ── Long-term climate means (DEFECT D2 fix, v1.35.0) ──────────────────
    # 01_climate.csv carries the FULL RAF Valley record (Dec 1930 onward),
    # not the study period. Averaging all of it evaluated the SSM against a
    # 95-year climate normal while the mean heads below span the monitoring
    # record only, and while Figure 58's caption states 2005-2026. The two
    # periods differ materially, and because the bias enters through
    # beta_1 * P_bar it scaled with beta_1 — largest in the open dune. The
    # realised averaging period and its P̄/PET̄ are printed to the console and
    # written to 20_residual_report_numbers.csv; cite those, not a literal.
    #
    # The averaging window is derived from the mean-head record (`maod`)
    # rather than a literal date, so the climate means and the mean heads
    # always describe the same period and the figure matches its caption.
    _rec_start, _rec_end = maod.index.min(), maod.index.max()
    _in_record  = (clim.index >= _rec_start) & (clim.index <= _rec_end)
    clim_period = clim.loc[_in_record]
    P_bar   = clim_period["P_m"].mean()
    PET_bar = clim_period["PET"].mean()

    wt = locs[["Match_ID", "E", "N"]].rename(
        columns={"Match_ID": "well"}).copy()

    # Merge β coefficients and cluster
    beta = md[["Name_Original", "Cluster",
               "beta_1_recharge", "beta_2_atmospheric_draw",
               "beta_3_drainage"]].rename(columns={
        "Name_Original":           "well",
        "Cluster":                 "cluster",
        "beta_1_recharge":         "beta1",
        "beta_2_atmospheric_draw": "beta2",
        "beta_3_drainage":         "beta3",
    })
    wt = wt.merge(beta, on="well", how="left")

    # DEM ground elevation
    elev_map = dict(zip(elev["Name_norm"], elev["ground_elev_m"]))
    wt["dem_elev"] = wt["well"].map(elev_map)


    # Mean annual head
    wt["mean_head"] = wt["well"].map(maod.mean(axis=0))

    # Displacement above drainage datum.
    # h_depth = maOD − ground_elev_m (negative convention, same as 01_wells_clean.csv,
    #           which is the master `depth from surface` sheet: level = upstand − dip).
    # h_disp  = DRAINAGE_DATUM + h_depth (positive when water table is above
    #           the drainage base; matches Script 03 SSM fitting formulation).
    wt["mean_depth"] = wt["mean_head"] - wt["dem_elev"]
    wt["h_disp"] = DRAINAGE_DATUM + wt["mean_depth"]

    # SSM water balance residual.
    # At steady state (Δh=0): 0 = β₁·P̄ − β₂·PET̄ − β₃·h̄_disp
    # Residual = β₂·PET̄ + β₃·h̄_disp − β₁·P̄
    # Positive = SSM drainage+ET exceeds recharge → lateral inflow required.
    #
    # DO NOT reduce the recharge term by canopy interception (DEFECT D1 fix,
    # v1.35.0). It is tempting to write β₁·P̄·(1 − FOREST_INTERCEPTION) at
    # forest wells, and this function did so up to v1.34.0. That subtracts
    # interception twice. Per INTERCEPTION_TREATMENT.md, interception is a
    # PARTITION of the atmospheric energy budget, not a term additive to it:
    # because Script 03 fits the SSM on gross rainfall and above-canopy
    # Thornthwaite PET, the interception loss at C4/C5 is ALREADY carried
    # inside the fitted β₂·PET̄. Applying (1 − FOREST_INTERCEPTION) to P̄ as
    # well inserted a spurious +β₁·FOREST_INTERCEPTION·P̄ at the forest
    # clusters — larger than the entire forest-versus-open contrast the
    # resulting figure displayed. Script 16 uses gross P̄ here and closes the
    # cluster balance to the residual it reports in its own per-cluster output
    # (Residual_m_month); this field now agrees with it. Interception belongs in the
    # volumetric budget (Script 16 panel b) and in the WTF net-recharge flux
    # (Scripts 17/18), where throughfall is used directly and no β₁ is
    # applied. See DEFECT_NOTE_script20_residual_field_2026-08-06.md.
    wt["residual_wb"] = np.where(
        wt["beta1"].notna() & wt["h_disp"].notna(),
        wt["beta2"] * PET_bar + wt["beta3"] * wt["h_disp"]
        - wt["beta1"] * P_bar,
        np.nan)

    wt["network"] = "Reference"
    wt = wt.dropna(subset=["E", "N", "mean_head"])

    # Extended wells — location + cluster only, no residual
    #
    # The Reference bucket above is built from "has a surveyed location and a
    # maOD series" — a looser set than the 66-well analysed reference network.
    # A number of Extended-network wells also satisfy that filter, so without
    # de-duplication they appear in BOTH buckets: counted twice in the console
    # line, and (because they have no SSM cluster) plotted on the cluster maps
    # as a default-C3-coloured marker despite never having been clustered.
    # The fix below makes the two buckets mutually exclusive: any Reference-
    # bucket well that is actually appended as an Extended row is removed from
    # the Reference set, so it is plotted once, as an Extended well, with its
    # Pearson-assigned cluster. The de-duplication is keyed on the wells the
    # Extended loop genuinely appends — a well that fails an Extended gate
    # (no pipe-top, no series, < 5 obs) is left in the Reference bucket rather
    # than dropped from both.
    ext_rows = []
    if ext is not None and site is not None:
        ext_cls = {
            normalize_well_name(r["Well_Normalised"]): int(r["Best_Match_Cluster"])
            for _, r in site[site["Network"] == "Extended"].iterrows()
        }
        ground_map = dict(zip(elev["Name_norm"], elev["ground_elev_m"]))
        for wn, cl in ext_cls.items():
            lrow = locs[locs["Match_ID"] == wn]
            if lrow.empty:
                # Try Name column
                name_col = [c for c in locs.columns if c.lower() == "name"]
                if name_col:
                    lrow = locs[locs[name_col[0]].apply(normalize_well_name) == wn]
            if lrow.empty: continue
            ground_e = ground_map.get(wn, np.nan)
            if np.isnan(ground_e): continue
            col = next((c for c in ext.columns if c == wn), None)
            if col is None: continue
            series = ground_e + ext[col].dropna()
            if len(series) < 5: continue
            ext_rows.append({
                "well": wn, "E": lrow.iloc[0]["E"], "N": lrow.iloc[0]["N"],
                "cluster": cl, "mean_head": series.mean(),
                "residual_wb": np.nan, "network": "Extended",
                "beta1": np.nan, "beta2": np.nan, "beta3": np.nan,
            })

    if ext_rows:
        # Remove Extended wells that were caught by the Reference filter, so
        # each well belongs to exactly one bucket (see comment above).
        ext_names = {row["well"] for row in ext_rows}
        wt = wt[~wt["well"].isin(ext_names)].copy()
        wt = pd.concat([wt, pd.DataFrame(ext_rows)], ignore_index=True)

    print(f"  Reference wells: {(wt['network']=='Reference').sum()}, "
          f"Extended wells: {(wt['network']=='Extended').sum()}")
    return wt, P_bar, PET_bar


# ─────────────────────────────────────────────────────────────────────────────
# STREAM NETWORK
# ─────────────────────────────────────────────────────────────────────────────
def load_stream_polygons():
    """
    Load SAGA stream cell polygons from streams.kml.
    Returns list of [(e, n), ...] coordinate rings in EPSG:27700,
    or [] if unavailable.  Each element is one polygon's vertex list.
    Rendering these as outlines (matching map_utils.add_kml_features)
    produces a visible stream network; the old centroid-scatter approach
    was too faint to see against the head surface overlay.
    """
    if not DATA_KML_STREAMS.exists():
        return []
    try:
        ns_kml = "http://www.opengis.net/kml/2.2"
        t = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
        tree = ET.parse(str(DATA_KML_STREAMS))
        polys = []
        for pm in tree.getroot().iter(f"{{{ns_kml}}}Placemark"):
            cel = pm.find(f".//{{{ns_kml}}}coordinates")
            if cel is None or not cel.text:
                continue
            ring = []
            for tok in cel.text.strip().split():
                p = tok.split(",")
                if len(p) < 2:
                    continue
                try:
                    e, n = t.transform(float(p[0]), float(p[1]))
                    ring.append((e, n))
                except Exception:
                    continue
            if len(ring) >= 3:
                polys.append(ring)
        print(f"  Stream polygons loaded: {len(polys)}")
        return polys
    except Exception as _e:
        warnings.warn(f"streams.kml load failed: {_e}")
        return []


def draw_stream_network(ax, polys, zorder=6):
    """
    Draw stream cell polygon outlines on ax.  Matches map_utils style:
    dodgerblue edges, no fill, lw=1.8.  Returns a legend handle.
    """
    from matplotlib.collections import PolyCollection
    if not polys:
        return []
    pc = PolyCollection(
        polys, facecolors="none", edgecolors="dodgerblue",
        linewidths=0.8, alpha=0.75, zorder=zorder,
    )
    ax.add_collection(pc)
    return [Line2D([0], [0], color="dodgerblue", lw=1.8,
                   label="DEM-derived flow network")]

# ─────────────────────────────────────────────────────────────────────────────
# KML FEATURES
# ─────────────────────────────────────────────────────────────────────────────
def load_kml_features():
    """
    Parse Features.kml and return list of (name, type, [(x,y)...]) tuples.
    type is 'polygon' or 'line'.
    """
    if not DATA_KML_FEATURES.exists():
        return []
    features = []
    tree = ET.parse(str(DATA_KML_FEATURES))
    for pm in tree.getroot().iter(f"{{{KML_NS}}}Placemark"):
        name_el = pm.find(f"{{{KML_NS}}}name")
        name    = name_el.text.strip() if name_el is not None else ""
        for pg in pm.iter(f"{{{KML_NS}}}Polygon"):
            cel = pg.find(f".//{{{KML_NS}}}coordinates")
            if cel is not None and cel.text:
                pts = _parse_coords(cel.text)
                if pts:
                    features.append((name, "polygon", pts))
        for ls in pm.iter(f"{{{KML_NS}}}LineString"):
            cel = ls.find(f"{{{KML_NS}}}coordinates")
            if cel is not None and cel.text:
                pts = _parse_coords(cel.text)
                if pts:
                    features.append((name, "line", pts))
    return features


def _parse_coords(text):
    pts = []
    for tok in text.strip().split():
        p = tok.split(",")
        if len(p) >= 2:
            try:
                e, n = T_WGS_BNG.transform(float(p[0]), float(p[1]))
                pts.append((e, n))
            except Exception:
                pass
    return pts


def draw_kml_features(ax, features, zorder=5):
    """Draw KML features onto ax. Returns legend handles."""
    handles = {}

    for name, ftype, pts in features:
        if not pts:
            continue
        xs, ys = zip(*pts)
        nl = name.lower()

        if ftype == "polygon":
            if "forest" in nl:
                kw = dict(edgecolor="purple", facecolor="none",
                          lw=1.8, ls="--", zorder=zorder)
                lbl = "Forest boundary"
            elif "llyn" in nl or "rhos" in nl or "lake" in nl:
                kw = dict(edgecolor="dodgerblue", facecolor="dodgerblue",
                          lw=1.2, alpha=0.25, zorder=zorder)
                lbl = "Llyn Rhos Ddu"
            elif "felling" in nl or "experiment" in nl:
                kw = dict(edgecolor="darkorange", facecolor="none",
                          lw=2.0, ls="-.", zorder=zorder)
                lbl = "Clearfell zone"
            else:
                continue
            ax.fill(xs, ys, **kw)
            if lbl not in handles:
                handles[lbl] = mpatches.Patch(
                    facecolor=kw.get("facecolor","none"),
                    edgecolor=kw["edgecolor"], lw=kw["lw"],
                    linestyle=kw.get("ls","-"), label=lbl)

        elif ftype == "line":
            # All line features in Features.kml are paths/tracks — grey dashed
            kw = dict(color="black", lw=0.8, ls="--",
                      alpha=0.7, zorder=zorder)
            lbl = "Paths and roads"
            ax.plot(xs, ys, **kw)
            if lbl not in handles:
                handles[lbl] = Line2D([0],[0], color=kw["color"],
                                      lw=kw["lw"], ls=kw["ls"],
                                      label=lbl)

    return list(handles.values())


# ─────────────────────────────────────────────────────────────────────────────
# SLOPE SURFACE
# ─────────────────────────────────────────────────────────────────────────────
def compute_slope_surface(smooth_m=50):
    """
    Compute hillslope gradient (degrees) from the LiDAR DEM, smoothed to
    suppress individual dune crest noise and reveal broad ridge geometry.

    Parameters
    ----------
    smooth_m : int
        Smoothing window in metres (default 50 m).

    Returns (slope_deg, dem_e, dem_n, res) clipped to study area,
    with values < 1° set to NaN to mask the flat dune plain.
    """
    import rasterio
    with rasterio.open(str(DATA_DEM)) as src:
        dem   = src.read(1).astype(float)
        nd    = src.nodata
        tfm   = src.transform
        res   = abs(tfm.a)
        E0    = tfm.c
        N_top = tfm.f
    if nd is not None:
        dem[dem == nd] = np.nan
    rows, cols = dem.shape
    dem_e = E0   + np.arange(cols) * res
    dem_n = N_top - np.arange(rows) * res

    k = max(1, int(smooth_m / res))
    filled   = np.nan_to_num(dem, nan=0.0)
    smoothed = uniform_filter(filled, size=k)
    smoothed[np.isnan(dem)] = np.nan

    dy, dx = np.gradient(np.nan_to_num(smoothed, nan=0.0), res, res)
    slope_deg = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    slope_deg[np.isnan(dem)] = np.nan

    # Clip to study area and mask flat plain
    clip = ((dem_n[:,None] >= YLIM[0]) & (dem_n[:,None] <= YLIM[1]) &
            (dem_e[None,:] >= XLIM[0]) & (dem_e[None,:] <= XLIM[1]))
    slope_deg[~clip] = np.nan
    slope_deg[slope_deg < 1.0] = np.nan   # flat dune plain → transparent

    return slope_deg, dem_e, dem_n, res


# ─────────────────────────────────────────────────────────────────────────────
# IDW INTERPOLATION
# ─────────────────────────────────────────────────────────────────────────────
def idw_surface(pts, vals, gx, gy, sea_pts=None, sea_vals=None, mask=None):
    """
    Interpolate scattered point values to a regular grid.

    Despite the name (kept for continuity with earlier versions and with
    map_utils.add_idw_surface()), this is NOT inverse-distance weighting:
    it calls scipy.interpolate.griddata(method="linear"), i.e. piecewise-
    linear barycentric interpolation over a Delaunay triangulation.
    Optionally augments with sea boundary anchor points and applies a mask.
    """
    if sea_pts is not None and sea_vals is not None:
        all_pts  = np.vstack([pts, sea_pts])
        all_vals = np.concatenate([vals, sea_vals])
    else:
        all_pts  = pts
        all_vals = vals

    surf = griddata(all_pts, all_vals, (gx, gy), method="linear")

    if mask is not None:
        surf[~mask] = np.nan

    return surf


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 1 — HEAD SURFACE WITH STREAM NETWORK
# ─────────────────────────────────────────────────────────────────────────────
def plot_head_streams(wt, stream_polys, features, dpi=300):
    """
    Figure 1: Mean annual water table (m AOD) with stream cell overlay
    and groundwater flow direction vectors.
    stream_polys: list of polygon vertex lists from load_stream_polygons().
    """
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    mask   = _site_mask(gx, gy)

    # Head surface IDW with sea boundary anchors
    sea_pts, sea_vals = _sea_boundary_points()
    pts  = wt[["E","N"]].values
    vals = wt["mean_head"].values
    surf = idw_surface(pts, vals, gx, gy,
                       sea_pts=sea_pts, sea_vals=sea_vals, mask=mask)

    # Flow vectors from head gradient — suppress on ridge artefacts
    dy, dx = np.gradient(np.nan_to_num(surf, nan=np.nanmean(vals)),
                         GRID_YI[1]-GRID_YI[0], GRID_XI[1]-GRID_XI[0])
    mag = np.sqrt(dx**2 + dy**2)
    mag_thresh = np.nanpercentile(mag[mask], 95)
    arrow_mask = mask & (mag > 0) & (mag < mag_thresh)
    with np.errstate(invalid="ignore"):
        U = np.where(arrow_mask, -dx / mag, np.nan)
        V = np.where(arrow_mask, -dy / mag, np.nan)

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")

    # Layer 1 — DEM hillshade
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # Layer 2 — head surface
    vmin, vmax = 2.0, 14.0
    im = ax.pcolormesh(gx, gy, surf, cmap="RdYlBu_r",
                       vmin=vmin, vmax=vmax,
                       shading="auto", alpha=0.55, zorder=2)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, shrink=0.85)
    cb.set_label("Mean water table (m AOD)", fontsize=9)

    # Head contours at 1 m intervals
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            cs = ax.contour(gx, gy, surf,
                            levels=np.arange(2, 15, 1),
                            colors="black", linewidths=0.6,
                            alpha=0.40, zorder=3)
            ax.clabel(cs, inline=True, fontsize=5,
                      fmt="%.0f m", inline_spacing=2)
        except Exception:
            pass

    # Layer 3 — stream network (polygon outlines, matching map_utils style)
    stream_handles = draw_stream_network(ax, stream_polys, zorder=6)

    # Layer 4 — flow vectors
    skip = 6
    ax.quiver(gx[::skip, ::skip], gy[::skip, ::skip],
              U[::skip, ::skip], V[::skip, ::skip],
              color="white", alpha=0.88, scale=38,
              width=0.004, headwidth=4, zorder=7)

    # Layer 5 — KML features
    kml_handles = draw_kml_features(ax, features, zorder=5)

    # Layer 6 — well symbols
    cluster_handles = {}
    for _, row in wt.iterrows():
        cl  = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=30,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl not in cluster_handles:
            cluster_handles[cl] = mpatches.Patch(color=col,
                                                  label=f"C{cl}")

    # Legends
    flow_h   = Line2D([0],[0], color="white", lw=0,
                      marker=r"$\rightarrow$", markersize=8,
                      markerfacecolor="white", label="Flow direction")

    l1 = ax.legend(handles=kml_handles + stream_handles + [flow_h],
                   fontsize=7, loc="lower left", framealpha=0.92,
                   title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()),
              fontsize=8, loc="lower right",
              title="Cluster", title_fontsize=8)

    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "Mean Annual Water Table (m AOD) — Newborough Warren 2005–2026\n"
        "DEM-derived flow network  |  Groundwater flow direction vectors",
        fontsize=10, fontweight="bold")

    fig.tight_layout()
    render_figure(fig, OUT_20_HEAD_STREAMS)
    plt.close(fig)
    print(f"  Saved: {OUT_20_HEAD_STREAMS.name}")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2a — SSM WATER BALANCE RESIDUAL
# ─────────────────────────────────────────────────────────────────────────────
def plot_residual_ssm(wt, features, dpi=300):
    """
    SSM water balance residual — single panel with Darcy flow direction arrows.
    β coefficients only — no DEM physics in the residual surface itself.
    Flow arrows derived independently from mean head gradient.
    """
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    mask   = _site_mask(gx, gy)
    sea_pts, sea_vals = _sea_boundary_points()

    # Residual surface — IDW with sea boundary anchors at zero
    ref      = wt["residual_wb"].notna()
    rval     = wt.loc[ref, "residual_wb"].values
    res_df   = wt.loc[ref, ["E", "N", "residual_wb"]].copy()

    # ── §4.9 traceable per-well residual CSV + report numbers (Fig 56) ────
    _rcols = [c for c in ["well", "E", "N", "Cluster", "residual_wb"] if c in wt.columns]
    _resid = wt.loc[ref, _rcols].copy().sort_values("residual_wb", ascending=False)
    _resid.to_csv(OUT_20_RESIDUAL_PERWELL, index=False)
    print(f"  Saved → {OUT_20_RESIDUAL_PERWELL.name} ({len(_resid)} wells)")
    rrpt = ReportNumbers()
    _wcol = "well" if "well" in _resid.columns else _rcols[0]
    _top = _resid.iloc[0]
    rrpt.add("residual_max", float(_top["residual_wb"]), unit="m/month",
             well=str(_top[_wcol]).upper(),
             note="largest individual SSM water-balance residual α")
    _ceh14 = _resid[_resid[_wcol].astype(str).str.lower().str.replace(" ", "") == "ceh14"]
    if len(_ceh14):
        rrpt.add("residual_ceh14", float(_ceh14["residual_wb"].iloc[0]), unit="m/month",
                 well="CEH14", note="ridge-flank residual (cited in §4.9)")
    # β₃-independence check for the ridge-flank wells (D-037).
    # The residual expression carries β₃ directly, so at a well whose β₃ is
    # itself anomalous the residual is not independent evidence about that β₃.
    # Recompute CEH14's residual holding every other term at its own fitted
    # value and substituting the C4 per-well median β₃, and publish both the
    # substituted β₃ and the resulting residual so the supplement quotes a
    # committed number rather than asserting the comparison.
    _c4_id = next((cid for cid, lbl in CLUSTER_LABELS.items()
                   if "Main Forest" in lbl), None)
    _c4_b3 = (wt.loc[wt["cluster"] == _c4_id, "beta3"].median()
              if _c4_id is not None else np.nan)
    _c14w = wt[wt["well"].astype(str).str.lower().str.replace(" ", "") == "ceh14"]
    if len(_c14w) and np.isfinite(_c4_b3) and pd.notna(_c14w["residual_wb"].iloc[0]):
        _r0 = float(_c14w["residual_wb"].iloc[0])
        _hd = float(_c14w["h_disp"].iloc[0])
        _b3 = float(_c14w["beta3"].iloc[0])
        rrpt.add("residual_c4_median_beta3", float(_c4_b3), unit="1/month",
                 note="C4 per-well median beta_3, substituted in the CEH14 check")
        rrpt.add("residual_ceh14_b3_c4median", _r0 + (_c4_b3 - _b3) * _hd,
                 unit="m/month", well="CEH14",
                 note="CEH14 residual recomputed with the C4 median beta_3, "
                      "every other term unchanged (beta_3 independence check)")
    _n_band = int((_resid["residual_wb"] > 0.02).sum())
    rrpt.add("residual_n_gt_0p02", _n_band, unit="wells",
             note="wells with residual > +0.02 m/month (strong positive band)")
    _band_wells = ";".join(_resid.loc[_resid["residual_wb"] > 0.02, _wcol].astype(str).str.upper())
    rrpt.add("residual_band_wells", _band_wells, unit="",
             note="identity of wells with residual > +0.02 m/month")
    n_saved = rrpt.save(OUT_20_RESIDUAL_REPORT_NUMBERS)
    print(f"  Saved → {OUT_20_RESIDUAL_REPORT_NUMBERS.name} ({n_saved} report numbers)")

    # Flow vectors from mean head gradient (independent of residual).
    # The head surface KEEPS the zero-datum sea anchors — a shoreline head of
    # zero is physically meaningful and the arrows are an independent product.
    head_surf = idw_surface(wt[["E","N"]].values, wt["mean_head"].values,
                            gx, gy, sea_pts=sea_pts, sea_vals=sea_vals, mask=mask)
    dy, dx = np.gradient(np.nan_to_num(head_surf, nan=np.nanmean(wt["mean_head"].values)),
                         GRID_YI[1]-GRID_YI[0], GRID_XI[1]-GRID_XI[0])
    mag = np.sqrt(dx**2 + dy**2)
    # Suppress arrows where gradient is anomalously large — indicates
    # the IDW surface is interpolating through a ridge with no real saturated
    # zone (produces spurious dome artefacts near Newborough ridge).
    # Threshold = 95th percentile of gradient magnitude within the site mask.
    mag_thresh = np.nanpercentile(mag[mask], 95)

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # ── Residual surface — map_utils.add_idw_surface (v1.35.1) ─────────────
    # Was a local idw_surface() call on a rectangular sea-line mask, with
    # zero-valued sea anchor points fed into the triangulation. Two problems:
    # the surface ran up to ~1 km past the outermost dipwell over ground with
    # no measurements, and the anchors imposed residual = 0 at the shoreline.
    # A zero-datum shoreline is meaningful for a HEAD surface (the arrows below
    # still use it) but there is no physical reason a water-balance residual
    # should vanish at the coast, so the anchors are not used here.
    #
    # Now routed through map_utils per the pipeline's map discipline:
    #   hull_buffer_m=100.0  — the pipeline-wide default set in map_utils
    #                          v1.5.0 (2026-07-05) for a uniform map footprint;
    #                          the surface reaches 100 m past the outer wells
    #                          and no further.
    #   apply_site_mask=True — the true KML site outline via make_site_mask(),
    #                          replacing the crude rectangular sea-line clip.
    #   ridge_mask_threshold=None — no DEM-height mask, preserving the
    #                          deliberate choice recorded in report §4.9.7.
    mesh, _, _, resid_surf = add_idw_surface(
        ax, res_df, "residual_wb",
        xi=GRID_XI, yi=GRID_YI, method="linear",
        ridge_mask_threshold=None,
        cmap="RdBu_r", alpha=0.52, zorder=2,
        apply_site_mask=True, hull_buffer_m=100.0,
    )
    vmax_r = np.nanpercentile(np.abs(resid_surf), 95)
    if not np.isfinite(vmax_r) or vmax_r <= 0:
        vmax_r = float(np.nanmax(np.abs(rval))) or 0.01
    norm_r = TwoSlopeNorm(vmin=-vmax_r, vcenter=0, vmax=vmax_r)
    mesh.set_norm(norm_r)
    fig.colorbar(
        mesh, ax=ax, fraction=0.03, pad=0.02, shrink=0.85
    ).set_label("Water balance residual (m/month)\n"
                "+ve = modelled losses exceed modelled recharge",
                fontsize=9)

    # Flow direction arrows (normalised, white). Confined to cells where the
    # residual surface exists, so they follow the tightened footprint.
    arrow_mask = mask & (mag > 0) & (mag < mag_thresh) & ~np.isnan(resid_surf)
    with np.errstate(invalid="ignore"):
        U = np.where(arrow_mask, -dx / mag, np.nan)
        V = np.where(arrow_mask, -dy / mag, np.nan)
    skip = 6
    ax.quiver(gx[::skip, ::skip], gy[::skip, ::skip],
              U[::skip, ::skip], V[::skip, ::skip],
              color="white", alpha=0.75, scale=38, width=0.003,
              headwidth=3, headlength=4, zorder=5)

    # Wells coloured by residual value
    ax.scatter(wt.loc[ref,"E"], wt.loc[ref,"N"],
               c=rval, cmap="RdBu_r", norm=norm_r,
               s=55, edgecolors="black", lw=0.6, zorder=9, marker="o")

    # Extended wells — grey diamonds
    ext = wt[wt["network"] == "Extended"]
    if not ext.empty:
        ax.scatter(ext["E"], ext["N"], c="grey", s=30, marker="D",
                   edgecolors="black", lw=0.4, alpha=0.7, zorder=8)

    # Stream network
    stream_polys = load_stream_polygons()
    stream_handles = draw_stream_network(ax, stream_polys, zorder=4)

    kml_h = draw_kml_features(ax, features, zorder=6)
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "SSM Water Balance Residual (m/month) — Newborough Warren 2005–2026\n"
        "(β₂·PET̄ + β₃·h̄_disp − β₁·P̄)  |  β coefficients only  |  "
        "Flow direction arrows from head gradient",
        fontsize=10, fontweight="bold")

    leg_h = kml_h + stream_handles + [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=7, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=6, label="Extended well"),
        Line2D([0],[0], color="white", lw=0, marker=r"$\rightarrow$",
               markersize=8, markerfacecolor="white",
               label="Flow direction (head gradient)"),
    ]
    ax.legend(handles=leg_h, fontsize=7, loc="lower left", framealpha=0.9)
    _ceh14_alpha = wt.loc[wt["well"].str.lower() == "ceh14", "residual_wb"]
    _ceh14_str = f"{float(_ceh14_alpha.iloc[0]):+.3f}" if len(_ceh14_alpha) > 0 else "N/A"
    ax.annotate("Residual: SSM β coefficients only — independent of flow arrows.\n"
                "Flow arrows: mean head gradient — independent of β coefficients.\n"
                f"CEH14 water balance residual α = {_ceh14_str} m/month.",
                xy=(0.02, 0.97), xycoords="axes fraction",
                fontsize=7, va="top", color="dimgrey", zorder=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=1.0))

    fig.tight_layout()
    render_figure(fig, OUT_20_RESIDUAL_SSM)
    plt.close(fig)
    print(f"  Saved: {OUT_20_RESIDUAL_SSM.name}")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2b — RIDGE HILLSLOPE GRADIENT
# ─────────────────────────────────────────────────────────────────────────────
def plot_slope_gradient(wt, features, dpi=300):
    """
    Figure 2b: Ridge hillslope gradient from 50 m smoothed LiDAR DEM.
    DEM only — no SSM coefficients.
    Shows the topographic source of lateral recharge into the dune aquifer.
    """
    print("  Computing hillslope gradient...")
    slope_deg, dem_e, dem_n, res_d = compute_slope_surface(smooth_m=50)
    DEM_E, DEM_N = np.meshgrid(dem_e, dem_n)

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    im = ax.pcolormesh(DEM_E, DEM_N, slope_deg,
                       cmap="Oranges", vmin=1, vmax=10,
                       shading="auto", alpha=0.80, zorder=2)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, shrink=0.85
                 ).set_label("Hillslope gradient (degrees)\n50 m smoothed DEM",
                              fontsize=9)

    # All wells coloured by cluster
    for _, row in wt.iterrows():
        cl = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        mk = "D" if row.get("network") == "Extended" else "o"
        sz = 30 if mk == "D" else 40
        ax.scatter(row["E"], row["N"],
                   c=CLUSTER_COLOURS.get(cl, "grey"),
                   s=sz, marker=mk,
                   edgecolors="white" if mk == "o" else "black",
                   lw=0.4, zorder=9)

    kml_h = draw_kml_features(ax, features, zorder=5)
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.set_title(
        "Ridge Hillslope Gradient — 50 m Smoothed DEM\n"
        "Topographic source of lateral recharge — DEM only  |  "
        "Slopes < 1° masked (flat dune plain)",
        fontsize=10, fontweight="bold")

    cl_handles = [
        mpatches.Patch(color=CLUSTER_COLOURS.get(cl, "grey"), label=f"C{cl}")
        for cl in sorted(CLUSTER_LABELS.keys())
    ] + [
        Line2D([0],[0], marker="o", color="w", markerfacecolor="grey",
               markeredgecolor="white", markersize=7, label="Reference well"),
        Line2D([0],[0], marker="D", color="w", markerfacecolor="grey",
               markeredgecolor="black", markersize=6, label="Extended well"),
    ]
    ax.legend(handles=kml_h + cl_handles,
              fontsize=7, loc="lower left", framealpha=0.9)
    ax.annotate("DEM gradient (50 m smooth) — no β coefficients used.\n"
                "Slopes < 1° masked (flat dune plain).",
                xy=(0.02, 0.97), xycoords="axes fraction",
                fontsize=7, va="top", color="dimgrey",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85))

    fig.tight_layout()
    render_figure(fig, OUT_20_SLOPE)
    plt.close(fig)
    print(f"  Saved: {OUT_20_SLOPE.name}")




# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 3 — FOREST DRAWDOWN PROPAGATION WITH HEAD SURFACE
# ─────────────────────────────────────────────────────────────────────────────
def plot_drawdown_propagation(wt, features, dpi=300, show_head=True):
    """
    Figure 3: Estimated forest drawdown propagation, optionally overlaid on the
    mean head surface, with groundwater flow direction vectors.

    show_head=True  → mean-head colour surface + colorbar (the report default).
    show_head=False → drawdown contours on the bare DEM hillshade only
                      (a cleaner companion; saved to OUT_20_DRAWDOWN_NOHEAD).

    Uses DEM flow-direction-weighted cost-distance (Dijkstra with directional
    and uphill penalties) from the KML forest boundary. The drawdown signal
    h₀·exp(−d/λ) decays with characteristic length λ = √(D/β₃) where
    D = K·b/Sy is the hydraulic diffusivity.

    Layers:
      1. DEM hillshade
      2. IDW mean head surface (RdYlBu_r, semi-transparent), drawn
         unmasked to fill the full rectangular map frame
      3. Drawdown contour lines with labels (filled contours removed)
      4. Groundwater flow arrows from head gradient
      5. KML features (forest boundary, lake, felling experiment)
      6. Well symbols coloured by cluster
      7. Key well annotations with drawdown values

    The drawdown line contours use a grid clipped to the study-area
    outline (site_boundary.kml) so they stop at the coast and warren edges.
    """
    from heapq import heappush, heappop
    import geopandas as gpd
    import fiona
    import rasterio
    from shapely.geometry import Point
    from shapely.prepared import prep

    fiona.drvsupport.supported_drivers["KML"] = "rw"

    # ── Parameters ────────────────────────────────────────────────────────
    # Hydraulic diffusivity D = K·b/Sy and decay length λ = √(D/β₃) are
    # properties of the aquifer the drawdown propagates THROUGH (not the
    # forest interior where the drawdown originates).  The dominant
    # propagation medium beyond the forest edge is C3 (Western Residual,
    # open dune), so Sy and β₃ are sourced from C3 cluster outputs:
    #   - Sy: cluster median of WTF Sy from outputs/18_wtf_01_well_sy_estimates.csv
    #   - β₃: cluster centroid drainage coefficient from
    #         outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv
    # The realised λ is emitted to 20_report_numbers.csv (drawdown_lambda) on
    # the show_head pass; cite that file, never a literal. K and b remain fixed
    # literature/estimate values (Betson 2002; aquifer thickness estimate).
    K       = DRAWDOWN_K_MDAY   # m/day (Betson 2002), from config.py
    b       = DRAWDOWN_B_M      # m saturated thickness, from config.py
    H0      = DRAWDOWN_H0_MM    # mm forest interception deficit, from config.py

    # Load C3 (propagation medium) Sy and β₃ from upstream pipeline outputs
    _sy_df    = pd.read_csv(OUT_18_WELL_SY_TABLE)
    Sy        = float(_sy_df[_sy_df['Cluster'] == 3]['Sy_median'].median())
    _mech_df  = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
    BETA3_M   = float(_mech_df[_mech_df['Cluster'] == 3]['beta_3_drainage'].iloc[0])
    BETA3_D   = BETA3_M / 30.0
    lam       = np.sqrt((K * b) / (Sy * BETA3_D))
    OUT_PATH  = OUT_20_DRAWDOWN if show_head else OUT_20_DRAWDOWN_NOHEAD

    print(f"  λ = {quote_reach_m(lam):.0f} m  (K={K}, Sy={Sy:.4f} [C3 WTF], "
          f"b={b}, β₃={BETA3_M:.4f}/month [C3 SSM])")

    # ── Load DEM and build flow-weighted distance grid ────────────────────
    with rasterio.open(str(DATA_DEM)) as src:
        dem_full = src.read(1).astype(float)
        t = src.transform
        res = abs(t.a)
        if src.nodata is not None:
            dem_full[dem_full == src.nodata] = np.nan

    E_MIN, E_MAX = XLIM[0] + 100, XLIM[1] - 400
    N_MIN, N_MAX = YLIM[0] + 200, YLIM[1] + 200
    col0 = int((E_MIN - t.c) / t.a)
    col1 = int((E_MAX - t.c) / t.a)
    row0 = int((t.f - N_MAX) / abs(t.e))
    row1 = int((t.f - N_MIN) / abs(t.e))
    dem = dem_full[row0:row1, col0:col1]

    ds = 5  # downsample to 10m
    dem_ds = dem[::ds, ::ds]
    nr, nc = dem_ds.shape
    cell = res * ds
    e_arr = t.c + (col0 + np.arange(nc) * ds) * t.a
    n_arr = t.f + (row0 + np.arange(nr) * ds) * t.e

    # DEM gradient for flow direction
    dy, dx = np.gradient(dem_ds, cell)
    flow_E = -dx
    flow_N = -dy
    mag = np.sqrt(flow_E**2 + flow_N**2)
    mag[mag == 0] = 1e-6
    flow_E /= mag
    flow_N /= mag

    # Forest mask from KML
    forest_geom = None
    gdf_kml = gpd.read_file(str(DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
    name_col = gdf_kml["Name"].fillna("").astype(str)
    for idx, row in gdf_kml.iterrows():
        nm = name_col.iloc[idx].lower()
        if "forest" in nm or "boundary" in nm:
            forest_geom = row.geometry

    if forest_geom is None:
        print("  [WARNING] Forest polygon not found in KML — skipping drawdown map")
        return

    forest_prep = prep(forest_geom)
    forest_mask = np.zeros((nr, nc), dtype=bool)
    step = 3
    for i in range(0, nr, step):
        for j in range(0, nc, step):
            pt = Point(e_arr[j], n_arr[i])
            if forest_prep.contains(pt):
                r = step // 2 + 1
                forest_mask[max(0, i - r):min(nr, i + r + 1),
                            max(0, j - r):min(nc, j + r + 1)] = True

    # ── Flow-direction-weighted Dijkstra ──────────────────────────────────
    FLOW_WEIGHT    = 0.4
    UPHILL_PENALTY = 2.0
    INF = 1e12

    dist = np.full((nr, nc), INF)
    visited = np.zeros((nr, nc), dtype=bool)
    heap = []

    # Seed forest boundary cells
    for i in range(nr):
        for j in range(nc):
            if forest_mask[i, j]:
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni_, nj_ = i + di, j + dj
                    if 0 <= ni_ < nr and 0 <= nj_ < nc and not forest_mask[ni_, nj_]:
                        dist[i, j] = 0
                        heappush(heap, (0.0, i, j))
                        break
    dist[forest_mask] = 0

    step_geo = {
        (-1,  0): ( 0,  1),   ( 1, 0): ( 0, -1),
        ( 0, -1): (-1,  0),   ( 0, 1): ( 1,  0),
        (-1, -1): (-0.707,  0.707), (-1, 1): ( 0.707,  0.707),
        ( 1, -1): (-0.707, -0.707), ( 1, 1): ( 0.707, -0.707),
    }
    diag = cell * 1.414
    neighbors = [
        (-1, 0, cell), (1, 0, cell), (0, -1, cell), (0, 1, cell),
        (-1, -1, diag), (-1, 1, diag), (1, -1, diag), (1, 1, diag),
    ]

    while heap:
        d, ci, cj = heappop(heap)
        if visited[ci, cj]:
            continue
        visited[ci, cj] = True
        for di, dj, base_dist in neighbors:
            ni_, nj_ = ci + di, cj + dj
            if 0 <= ni_ < nr and 0 <= nj_ < nc and not visited[ni_, nj_]:
                if forest_mask[ni_, nj_]:
                    new_dist = 0.0
                else:
                    se, sn = step_geo[(di, dj)]
                    alignment = se * flow_E[ci, cj] + sn * flow_N[ci, cj]
                    dz = dem_ds[ni_, nj_] - dem_ds[ci, cj]
                    cost = base_dist * (1.0 - FLOW_WEIGHT * alignment) \
                         + max(0, dz) * UPHILL_PENALTY
                    new_dist = d + cost
                if new_dist < dist[ni_, nj_]:
                    dist[ni_, nj_] = new_dist
                    heappush(heap, (new_dist, ni_, nj_))

    dist[forest_mask] = 0
    dd_grid = np.where(forest_mask, H0,
                       np.where(dist < INF, H0 * np.exp(-dist / lam), 0))

    # ── Head surface and GW flow vectors ──────────────────────────────────
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    mask = _site_mask(gx, gy)
    sea_pts, sea_vals = _sea_boundary_points()
    pts  = wt[["E", "N"]].values
    vals = wt["mean_head"].values
    # Masked surface: drives the GW flow-vector field (gradient + arrow mask).
    surf = idw_surface(pts, vals, gx, gy,
                       sea_pts=sea_pts, sea_vals=sea_vals, mask=mask)
    # Unmasked surface: drawn as Layer 2 to fill the full rectangular map
    # frame edge to edge (no site/sea mask applied).
    surf_full = idw_surface(pts, vals, gx, gy,
                            sea_pts=sea_pts, sea_vals=sea_vals, mask=None)

    hdy, hdx = np.gradient(np.nan_to_num(surf, nan=np.nanmean(vals)),
                           GRID_YI[1] - GRID_YI[0], GRID_XI[1] - GRID_XI[0])
    hmag = np.sqrt(hdx**2 + hdy**2)
    mag_thresh = np.nanpercentile(hmag[mask], 95)
    arrow_ok = mask & (hmag > 0) & (hmag < mag_thresh)
    with np.errstate(invalid="ignore"):
        U = np.where(arrow_ok, -hdx / hmag, np.nan)
        V = np.where(arrow_ok, -hdy / hmag, np.nan)

    # ── Well drawdown values ──────────────────────────────────────────────
    dd_vals = []
    dist_forest_vals = []
    dist_cost_vals = []
    dist_basis_vals = []
    for _, row in wt.iterrows():
        pt = Point(row["E"], row["N"])
        d_euc = forest_geom.exterior.distance(pt)
        inside = forest_prep.contains(pt)
        dist_forest_vals.append(0.0 if inside else float(d_euc))
        cj_ = int((row["E"] - e_arr[0]) / cell)
        ci_ = int((n_arr[0] - row["N"]) / cell)
        # dd_mm decays on the FLOW-WEIGHTED COST distance, not the Euclidean
        # one, so record the distance each well's value was actually computed
        # on. Storing only dist_forest_m made the CSV look self-inconsistent —
        # the two differ substantially (CEH1: 49 m Euclidean, 14 m cost) — and
        # left the figure's own contour claims uncheckable against any
        # committed output.
        if inside:
            dd_vals.append(H0)
            dist_cost_vals.append(0.0)
            dist_basis_vals.append("inside")
        elif 0 <= ci_ < nr and 0 <= cj_ < nc and dist[ci_, cj_] < INF:
            dist_cost_vals.append(float(dist[ci_, cj_]))
            dd_vals.append(H0 * np.exp(-dist[ci_, cj_] / lam))
            dist_basis_vals.append("cost")
        else:
            # Off-grid or unreachable: the Euclidean distance stands in for the
            # cost distance, so dd_mm is a fallback value at this well.
            dist_cost_vals.append(float(d_euc))
            dd_vals.append(H0 * np.exp(-d_euc / lam))
            dist_basis_vals.append("euclidean_fallback")
    wt = wt.copy()
    wt["dd_mm"] = dd_vals
    wt["dist_forest_m"] = dist_forest_vals
    wt["dist_cost_m"] = dist_cost_vals
    wt["dist_basis"] = dist_basis_vals

    # ── §4.9 traceable per-well drawdown CSV + report numbers ─────────────
    # dd_mm and λ are independent of show_head (which only toggles the head
    # render layer), so these committed sources are written on every pass.
    _perwell = wt[["well", "E", "N", "dist_forest_m", "dist_cost_m",
                   "dist_basis", "dd_mm"]].copy()
    _perwell = _perwell.sort_values("dist_cost_m").reset_index(drop=True)
    _perwell.to_csv(OUT_20_DRAWDOWN_PERWELL, index=False)
    print(f"  Saved → {OUT_20_DRAWDOWN_PERWELL.name} "
          f"({len(_perwell)} wells)")

    rpt = ReportNumbers()
    rpt.add("drawdown_lambda", float(lam), unit="m",
            note=f"e-folding length √(Kb/(Sy·β₃/30)); Sy={Sy:.4f}, "
                 f"β₃={BETA3_M:.4f}/month [C3]")
    rpt.add("drawdown_H0", float(H0), unit="mm",
            note="forest interception deficit at felling edge (config)")
    _ddmap = {w.lower(): v for w, v in zip(wt["well"], wt["dd_mm"])}
    for _w in ["ceh23", "ceh6", "d15", "ceh24", "ceh10", "ceh11"]:
        if _w in _ddmap:
            rpt.add(f"drawdown_{_w}", float(_ddmap[_w]), unit="mm",
                    well=_w.upper(),
                    note="modelled steady-state forest drawdown")
    # Coastal edge drawdown — emitted here so the quantity enters the drift
    # net. It is computed in plot_coastal_erosion() and rendered straight into
    # the figure, so until now it reached no committed CSV and neither
    # audit_number_drift nor cite_check could bind the value the report types.
    # That is how a stale h₀ survived in two places (W77).
    _h0, _d0, _L, _rm, _pm = _coastal_edge_h0()
    _rate, _prov = load_measured_retreat_rate(quiet=True)
    rpt.add("coastal_h0", float(_h0), unit="mm",
            note=f"single-event edge drawdown, {_rm:.0f} m retreat × "
                 f"(δ₀/measured retreat rate); δ₀={_d0:.2f} mm/yr "
                 f"[Script 25 forest-free linear_capped, 2005-03 to 2026-02], "
                 f"rate={_rate:.4f} m/yr [{_prov}] — windows matched to 99 %, D-090")
    rpt.add("coastal_h0_per_metre", float(_pm), unit="mm/m",
            note="δ₀/measured retreat rate — head per metre of shoreline "
                 "retreat; the quantity Scripts 20 and 09f divide by")
    rpt.add("coastal_delta0", float(_d0), unit="mm/yr",
            note="live Script 25 forest-free linear_capped δ₀ (absolute); "
                 "fitted 2005-03 to 2026-02")
    rpt.add("coastal_retreat_rate", float(_rate), unit="m/yr",
            note=f"MEASURED, {_prov}. Supersedes config.COAST_RETREAT_RATE = "
                 f"{COAST_RETREAT_RATE} (a 2014-2020 window divided into a "
                 f"whole-record δ₀ — D-090)")
    rpt.add("coastal_reach_L", float(_L), unit="m",
            note="live Script 25 forest-free linear_capped reach L_cg")

    n_saved = rpt.save(OUT_20_REPORT_NUMBERS)
    print(f"  Saved → {OUT_20_REPORT_NUMBERS.name} "
          f"({n_saved} report numbers)")

    # ── Render figure ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")

    # Layer 1 — hillshade
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # Layer 2 — mean head surface, expanded to fill the full map frame.
    # Drawn unmasked across the whole rectangular extent (edge to edge);
    # the IDW surface `surf` was computed above (also feeds the GW flow
    # vectors). Semi-transparent over the DEM hillshade. Omitted when
    # show_head=False, leaving a bare-hillshade drawdown diagram.
    im = None
    if show_head:
        im = ax.pcolormesh(gx, gy, surf_full, cmap="RdYlBu_r",
                           vmin=2.0, vmax=14.0,
                           shading="auto", alpha=0.45, zorder=2)

    # Drawdown filled contours removed — only the labelled drawdown
    # contour LINES (Layer 3) are retained below. The site-clipped
    # `dd_masked` grid is still computed because the line contours use it.
    E_grid, N_grid = np.meshgrid(e_arr, n_arr)
    dd_masked = dd_grid.copy()

    site_poly = load_site_polygon()
    if site_poly is not None:
        try:
            # Fast path: vectorized point-in-polygon over the whole grid.
            from shapely import contains_xy as _contains_xy
            inside_site = _contains_xy(site_poly,
                                       E_grid.ravel(),
                                       N_grid.ravel()).reshape(E_grid.shape)
        except Exception:
            # Fallback: per-cell prepared-geometry test.
            site_prep = prep(site_poly)
            inside_site = np.zeros(dd_masked.shape, dtype=bool)
            for i in range(dd_masked.shape[0]):
                n_v = n_arr[i]
                for j in range(dd_masked.shape[1]):
                    if site_prep.contains(Point(e_arr[j], n_v)):
                        inside_site[i, j] = True
        dd_masked[~inside_site] = 0
    else:
        # Fallback: original rectangular sea cutoffs
        dd_masked[N_grid < SEA_SOUTH_N] = 0
        dd_masked[E_grid > SEA_EAST_E]  = 0
        dd_masked[E_grid < SEA_WEST_E]  = 0
        for i in range(dd_masked.shape[0]):
            for j in range(dd_masked.shape[1]):
                e_v, n_v = e_arr[j], n_arr[i]
                if n_v < 362600 and e_v > 241800:
                    dd_masked[i, j] = 0
                if e_v > 243200 and n_v < 363600:
                    dd_masked[i, j] = 0

    # Layer 3 — drawdown contours. On the no-head map the contours are FILLED
    # (coastal-erosion style: YlOrBr, semi-transparent, warm = drawdown); on
    # the with-head map only labelled line contours are drawn (a fill would
    # clash with the head colour surface). Line contours are drawn in both.
    line_col = "midnightblue" if show_head else "#5a2a00"
    cf = None
    if not show_head:
        dd_fill = np.where(dd_masked > 0, dd_masked, np.nan)
        cf = ax.contourf(E_grid, N_grid, dd_fill, levels=DRAWDOWN_FILL_LEVELS,
                         cmap=DRAWDOWN_CMAP, alpha=DRAWDOWN_ALPHA, zorder=3,
                         extend="max")
    cs = ax.contour(E_grid, N_grid, dd_masked,
                    levels=DRAWDOWN_LINE_LEVELS,
                    colors=line_col, linewidths=1.2, alpha=0.85, zorder=4)
    cl = ax.clabel(cs, levels=DRAWDOWN_LINE_LABELS,
                   inline=True, fontsize=10, fmt="%d mm",
                   colors="black", inline_spacing=8)
    for txt in cl:
        txt.set_fontweight("bold")
        txt.set_bbox(dict(facecolor="white", alpha=0.75,
                          edgecolor="none", pad=1.5))

    # (GW flow arrows removed — the maps now show drawdown contours only.)

    # Layer 5 — KML features
    kml_handles = draw_kml_features(ax, features, zorder=6)

    # Layer 6 — wells coloured by drawdown
    cluster_handles = {}
    for _, row in wt.iterrows():
        cl_ = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl_, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=30,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl_ not in cluster_handles:
            cluster_handles[cl_] = mpatches.Patch(color=col, label=f"C{cl_}")

    # Layer 7 — key well annotations
    key_wells = ["ceh27", "ceh26", "ceh23", "d15", "d5",
                 "ceh10", "ceh24", "ceh5", "ceh6", "l7", "ceh11"]
    for _, w in wt[wt["well"].isin(key_wells)].iterrows():
        dd_str = f"{w['dd_mm']:.0f}" if w["dd_mm"] >= 1 else "<1"
        ax.annotate(
            f"{w['well']} ({dd_str} mm)", (w["E"], w["N"]),
            xytext=(8, 6), textcoords="offset points",
            fontsize=8, color="#222", fontweight="semibold",
            arrowprops=dict(arrowstyle="-", color="#999", lw=0.5),
            zorder=10,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                      alpha=0.8, edgecolor="none"))

    # λ annotation
    ref_e, ref_n = 241805, 364349
    ax.annotate("", xy=(ref_e + lam, ref_n - 100),
                xytext=(ref_e, ref_n - 100),
                arrowprops=dict(arrowstyle="<->", color="#d62728", lw=1.5),
                zorder=10)
    ax.text(ref_e + lam / 2, ref_n - 200, f"λ = {quote_reach_m(lam):.0f} m",
            ha="center", va="top", fontsize=9, fontweight="bold",
            color="#d62728", zorder=10,
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=2))

    # Colorbar: mean head surface (with-head map) or the drawdown fill
    # (no-head map, coastal-erosion style).
    if show_head and im is not None:
        cb_head = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04, shrink=0.85)
        cb_head.set_label("Mean water table (m AOD)", fontsize=9)
    elif (not show_head) and cf is not None:
        cb = fig.colorbar(cf, ax=ax, fraction=0.03, pad=0.04, shrink=0.85)
        cb.set_label("Forest drawdown (mm)", fontsize=9)

    # Legends
    l1 = ax.legend(handles=kml_handles,
                   fontsize=7, loc="lower left", framealpha=0.92,
                   title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()),
              fontsize=8, loc="lower right",
              title="Cluster", title_fontsize=8, framealpha=0.92)

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.set_title(
        "Forest drawdown propagation "
        + ("with mean head surface" if show_head else "on DEM hillshade")
        + "\n"
        f"Flow-weighted cost-distance · λ = {quote_reach_m(lam):.0f} m",
        fontsize=10, fontweight="bold", pad=10)

    plt.tight_layout()
    render_figure(fig, OUT_PATH)
    plt.close(fig)
    print(f"  Saved → {OUT_PATH}")


def _load_coastal_fit():
    """Read the headline coastal-retreat fit live from Script 25.

    Returns (delta0_mm_yr_abs, L_m) from the forest-free linear-capped row of
    25_01_panel_fit_parameters.csv. Falls back to the full-network row, then
    to a documented snapshot if the CSV is unavailable, so the figure can
    still render in isolation.
    """
    snapshot = (28.83, 894.0)   # forest-free linear-capped, 2026-05 snapshot
    try:
        df = pd.read_csv(OUT_25_FIT_PARAMETERS)
        row = df[(df["source"] == "forest_free")
                 & (df["model"] == "linear_capped")]
        if row.empty:
            row = df[(df["source"] == "full")
                     & (df["model"] == "linear_capped")]
        if row.empty:
            print("  [WARNING] no linear_capped fit row in Script 25 CSV — "
                  "using documented snapshot")
            return snapshot
        d0 = abs(float(row["delta_0_mm_yr"].iloc[0]))
        L  = float(row["L_m"].iloc[0])
        print(f"  Coastal fit (live, Script 25 forest-free linear-capped): "
              f"δ₀={d0:.2f} mm/yr, L={L:.0f} m")
        return d0, L
    except Exception as e:
        print(f"  [WARNING] could not read Script 25 fit ({e}) — "
              "using documented snapshot")
        return snapshot


def _coastal_edge_h0(retreat_m=None):
    """Edge water-table drawdown for a single shoreline-retreat event (mm).

        h0 = retreat_m * (delta_0 / COAST_RETREAT_RATE)

    The single definition of the construction, previously written out at each
    call site. Returns (h0_mm, delta0_mm_yr, L_m, retreat_m, per_metre) where
    per_metre = delta_0 / COAST_RETREAT_RATE is the mm of head per metre of
    shoreline retreat -- the quantity the pipeline actually uses, and the one
    the report numbers carry so it enters the drift net.

    The divisor is no longer config.COAST_RETREAT_RATE. It is MEASURED by
    Script 40 from the digitised coastline epochs over 2006-2026, a window
    matched to delta_0's own fit span to 99 % (D-090), and read live by
    utils.coastal_utils with a documented first-pass fallback. The old constant
    divided a whole-record delta_0 by a six-year window, which understated h0
    3.6-fold.

    ONE CONSEQUENCE TRAVELS WITH THIS: h0 is no longer an independent
    calibration. delta_0 comes from the water-table record and the rate from
    shoreline position - different data, so not circular - but the methods text
    must say so.
    """
    delta0, L = _load_coastal_fit()
    h0, rate, per_metre, prov = coastal_edge_h0(delta0, retreat_m)
    return h0, delta0, L, (retreat_m if retreat_m is not None else COAST_RETREAT_M), per_metre


def _dem_waterline_to_dune_edge(shore_level=None, offset_m=None):
    """Derive a SW-facing shore line from the DEM, optionally offset inland.

    Extracts the `shore_level` m-AOD contour (the land/sea waterline), keeps
    only the long SW-facing segment west of COAST_EAST_CUT_E, smooths it to a
    clean backbone, then offsets it `offset_m` inland (NE).

    Defaults (shore_level=COAST_SHORE_LEVEL_M, offset_m=COAST_DUNE_OFFSET_M)
    reproduce the erosion dune-toe front. The SLR map calls it with
    shore_level=SLR_SHORE_LEVEL_M (mean sea level, 0 m AOD) and offset_m=0
    (head measured from the waterline itself, no dune-toe offset).

    Returns (front_line, waterline) as shapely LineStrings in EPSG:27700,
    or (None, None) if the contour cannot be built. (When offset_m=0 the
    two returned lines are identical.)

    Uses matplotlib's contour engine (already a dependency) rather than
    skimage, so no new dependency is introduced.
    """
    import rasterio
    from shapely.geometry import LineString

    if shore_level is None:
        shore_level = COAST_SHORE_LEVEL_M
    if offset_m is None:
        offset_m = COAST_DUNE_OFFSET_M

    with rasterio.open(str(DATA_DEM)) as src:
        dem = src.read(1).astype(float)
        t = src.transform
        if src.nodata is not None:
            dem[dem == src.nodata] = np.nan

    nr, nc = dem.shape
    e_full = t.c + (np.arange(nc) + 0.5) * t.a
    n_full = t.f + (np.arange(nr) + 0.5) * t.e
    E_full, N_full = np.meshgrid(e_full, n_full)

    # Extract contour paths at the waterline level via a throwaway figure.
    tmp_fig, tmp_ax = plt.subplots()
    cset = tmp_ax.contour(E_full, N_full, np.nan_to_num(dem, nan=1e4),
                          levels=[shore_level])
    segs = []
    for path in cset.get_paths():
        v = path.vertices
        if len(v) >= 20:
            segs.append(v)
    plt.close(tmp_fig)

    # Keep the longest segment that lies within the figure window and west
    # of the east cutoff (the SW-facing Caernarfon Bay shore).
    best = None
    best_len = 0.0
    for v in segs:
        E, N = v[:, 0], v[:, 1]
        m = ((E >= XLIM[0]) & (E <= COAST_EAST_CUT_E)
             & (N >= YLIM[0]) & (N <= YLIM[1]))
        if m.sum() < 20:
            continue
        Es, Ns = E[m], N[m]
        ln = np.hypot(np.diff(Es), np.diff(Ns)).sum()
        if ln > best_len:
            best_len = ln
            best = (Es, Ns)

    if best is None:
        print("  [WARNING] could not extract SW waterline contour — "
              "skipping coastal-erosion map")
        return None, None

    Es, Ns = best
    order = np.argsort(Ns)            # order S→N
    wl_xy = np.column_stack([Es[order], Ns[order]])
    waterline = LineString(wl_xy)

    # Smooth to a backbone, resample evenly, offset inland (toward +E).
    backbone = waterline.simplify(60, preserve_topology=False)
    bx, by = np.array(backbone.xy[0]), np.array(backbone.xy[1])
    if offset_m == 0:
        # No dune-toe offset (SLR case): the front IS the smoothed waterline.
        return LineString(np.column_stack([bx, by])), waterline
    seg = np.r_[0, np.cumsum(np.hypot(np.diff(bx), np.diff(by)))]
    npts = max(int(seg[-1] // 25), 10)
    si = np.linspace(0, seg[-1], npts)
    xs = np.interp(si, seg, bx)
    ys = np.interp(si, seg, by)
    dx = np.gradient(xs)
    dy = np.gradient(ys)
    nrm = np.hypot(dx, dy)
    nrm[nrm == 0] = 1.0
    nx, ny = dy / nrm, -dx / nrm      # right-hand normal
    if nx.mean() < 0:                 # choose the +E (inland) side
        nx, ny = -nx, -ny
    front_xy = np.column_stack([xs + nx * offset_m,
                                ys + ny * offset_m])
    front = LineString(front_xy)
    return front, waterline


def plot_coastal_erosion(wt, features, dpi=300):
    """
    Figure 4: Estimated coastal-erosion drawdown overlaid on the DEM
    hillshade — a companion to the forest drawdown map (Figure 3),
    constructed to be directly comparable.

    A single COAST_RETREAT_M shoreline retreat (the Storm Brendan early-2020
    acute event, ~6 m, is the reference) produces an edge drawdown that
    decays inland with the strip-aquifer form

        Δh(d) = h₀ · (1 − d/L),   d = distance from the dune-edge front,

    matching the Script 25 forest-free linear-capped coastal-retreat
    regression. The chronic coast-edge anomaly δ₀ (mm/yr) is converted to a
    per-retreat edge drawdown via the long-term retreat rate:

        h₀ = COAST_RETREAT_M · (δ₀ / COAST_RETREAT_RATE)

    δ₀ and L are read live from Script 25; COAST_* are external assumptions
    flagged in the CONSTANTS block.

    Layers:
      1. DEM hillshade
      2. Erosion drawdown filled contours (YlOrBr, semi-transparent),
         clipped to the study-area outline (site_boundary.kml)
      3. Erosion drawdown contour lines with labels
      4. Dune-edge erosion front + DEM waterline
      5. KML features (forest boundary, lake, felling experiment)
      6. Well symbols coloured by cluster
    """
    from shapely.geometry import Point
    from shapely import contains_xy

    # ── Headline fit (live) + edge magnitude from the retreat assumption ──
    h0, delta0, L, _r, _pm = _coastal_edge_h0()
    _r, _p = load_measured_retreat_rate(quiet=True)
    print(f"  h₀ = {h0:.1f} mm  "
          f"({COAST_RETREAT_M:.0f} m retreat × {delta0:.2f}/{_r:.4f} "
          f"mm per m, rate {_p}), L = {L:.0f} m")

    # ── Erosion front (dune edge) from the DEM ────────────────────────────
    front, waterline = _dem_waterline_to_dune_edge()
    if front is None:
        return

    # ── Effect surface on the IDW grid, clipped to the site outline ───────
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    dist = np.array([front.distance(Point(x, y))
                     for x, y in zip(gx.ravel(), gy.ravel())]).reshape(gx.shape)
    eff = np.maximum(h0 * (1.0 - dist / L), 0.0)

    # front.distance() is unsigned, so cells SEAWARD of the dune-edge front
    # also receive a positive drawdown and would paint fill / draw contours
    # out in the bay. Build an explicit SEAWARD polygon (the front polyline
    # closed through the SW map corners — land is at higher easting) and zero
    # every cell inside it. This is robust at the front itself, unlike a
    # distance comparison which is ambiguous where d_front ≈ d_water.
    from shapely.geometry import Polygon as _Poly
    fxy = list(front.coords)                       # ordered S→N
    seaward_ring = fxy + [(XLIM[0] - 500, fxy[-1][1]),     # NW, out to sea
                          (XLIM[0] - 500, YLIM[0] - 500),  # SW corner
                          (fxy[0][0], YLIM[0] - 500)]       # back to front start
    seaward_poly = _Poly(seaward_ring).buffer(0)
    try:
        sea_in = contains_xy(seaward_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
    except Exception:
        sea_in = np.zeros(gx.shape, dtype=bool)
    eff[sea_in] = np.nan                            # NaN so contourf ignores it

    site_poly = load_site_polygon()
    if site_poly is not None:
        try:
            inside = contains_xy(site_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
        except Exception:
            from shapely.prepared import prep
            sp = prep(site_poly)
            inside = np.zeros(gx.shape, dtype=bool)
            for i in range(gx.shape[0]):
                for j in range(gx.shape[1]):
                    if sp.contains(Point(gx[i, j], gy[i, j])):
                        inside[i, j] = True
        eff[~inside] = np.nan

    # ── Render ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")

    # Layer 1 — hillshade
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # Layer 2 — erosion drawdown filled contours on the SHARED drawdown scale
    # (DRAWDOWN_FILL_LEVELS), common to the forest- and scrape-drawdown maps so
    # all three are directly comparable colour-to-colour. The hand-placed line
    # labels below are kept (field peaks ~21 mm).
    eff_lines  = [2, 5, 15]
    cf = ax.contourf(gx, gy, eff, levels=DRAWDOWN_FILL_LEVELS,
                     cmap=DRAWDOWN_CMAP, alpha=DRAWDOWN_ALPHA,
                     zorder=3, extend="max")

    # Layer 3 — contour lines (subset of fill levels). Labels placed manually
    # at the point on each line furthest from any well marker (computed
    # offline), so no label is obscured — in particular the 5 mm label sits
    # clear of the SW well cluster. Points snap to their nearest contour.
    cs = ax.contour(gx, gy, eff, levels=eff_lines,
                    colors="#5a2a00", linewidths=1.0, alpha=0.85, zorder=4)
    eff_label_pts = {
        2:  (242796, 362300),
        5:  (240350, 364152),
        15: (240200, 363749),
    }
    manual_pts = [eff_label_pts[l] for l in eff_lines if l in eff_label_pts]
    cl = ax.clabel(cs, inline=True, fontsize=9, fmt="%d mm",
                   colors="black", inline_spacing=8, manual=manual_pts)
    for txt in cl:
        txt.set_fontweight("bold")
        txt.set_bbox(dict(facecolor="white", alpha=0.75,
                          edgecolor="none", pad=1.5))

    # Layer 4 — erosion front + waterline
    fx, fy = front.xy
    ax.plot(fx, fy, color="#0044aa", lw=2.2, zorder=6,
            label="Dune edge (erosion front)")
    if waterline is not None:
        wx, wy = waterline.simplify(60, preserve_topology=False).xy
        ax.plot(wx, wy, color="#3399ff", lw=1.0, ls=":", alpha=0.7, zorder=6,
                label=f"Waterline ({COAST_SHORE_LEVEL_M:g} m AOD)")

    # Layer 5 — KML features
    kml_handles = draw_kml_features(ax, features, zorder=5)

    # Layer 6 — wells coloured by cluster
    cluster_handles = {}
    for _, row in wt.iterrows():
        cl_ = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl_, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=30,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl_ not in cluster_handles:
            cluster_handles[cl_] = mpatches.Patch(color=col, label=f"C{cl_}")

    # L (reach) annotation, mirroring the λ annotation on Figure 3
    ref_e, ref_n = 240500, 363100
    ax.annotate("", xy=(ref_e + L, ref_n - 100),
                xytext=(ref_e, ref_n - 100),
                arrowprops=dict(arrowstyle="<->", color="#d62728", lw=1.5),
                zorder=10)
    ax.text(ref_e + L / 2, ref_n - 200, f"L = {L:.0f} m",
            ha="center", va="top", fontsize=9, fontweight="bold",
            color="#d62728", zorder=10,
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=2))

    # Colorbar
    cb = fig.colorbar(cf, ax=ax, fraction=0.03, pad=0.04, shrink=0.85)
    cb.set_label(f"Drawdown from {COAST_RETREAT_M:.0f} m retreat (mm)",
                 fontsize=9)

    # Legends
    front_handles = [
        Line2D([0], [0], color="#0044aa", lw=2.2,
               label="Dune edge (erosion front)"),
        Line2D([0], [0], color="#3399ff", lw=1.0, ls=":",
               label=f"Waterline ({COAST_SHORE_LEVEL_M:g} m AOD)"),
    ]
    l1 = ax.legend(handles=kml_handles + front_handles,
                   fontsize=7, loc="upper right", framealpha=0.92,
                   title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()),
              fontsize=8, loc="lower right",
              title="Cluster", title_fontsize=8, framealpha=0.92)

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.set_title(
        "Coastal-erosion drawdown (dune-edge front)\n"
        f"{COAST_RETREAT_M:.0f} m shoreline retreat, reach L = {L:.0f} m, "
        f"edge h₀ = {h0:.0f} mm  |  Storm Brendan exemplar",
        fontsize=10, fontweight="bold", pad=10)

    plt.tight_layout()
    render_figure(fig, OUT_20_COASTAL_EROSION)
    plt.close(fig)
    print(f"  Saved → {OUT_20_COASTAL_EROSION}")


def plot_slr_response(wt, features, dpi=300):
    """
    Figure 5: Estimated water-table head GAIN from gradual sea-level rise,
    overlaid on the DEM hillshade — companion to the coastal-erosion map
    (Figure 4) and the forest drawdown map (Figure 3).

    A gradual rise in mean sea level lifts the fixed-head boundary at the
    Caernarfon Bay shore. Over a finite window the boundary perturbation
    diffuses inland and attenuates as a complementary-error-function
    transient (NOT a steady state):

        Δh(d) = SLR · erfc( d / (2·√(D·t)) )

    where d is distance inland from the shore, t = SLR_WINDOW_YEARS, and
    D = K·b/Sy is the hydraulic diffusivity (K, b literature; Sy read live
    from the C3 WTF estimates, as in the drawdown map). The result is a
    coast-hugging band of head rise decaying to ~zero in the interior over
    the diffusion length √(D·t).

    IMPORTANT — this is a GRADUAL-process illustration sitting beside the
    DISCRETE storm-retreat erosion map. The two are deliberately not reduced
    to a common annual rate; sea-level rise and episodic shoreline retreat
    are different kinds of coastal forcing that both act on the western
    margin. Together with Figure 4 this motivates (does not undermine) the
    BACI easting × time correction, which can only approximate the combined
    coastal signal with a single linear term. See §5.

    Layers:
      1. DEM hillshade
      2. SLR head-rise filled contours (GnBu, semi-transparent),
         clipped to the study-area outline (site_boundary.kml)
      3. SLR head-rise contour lines with labels
      4. Caernarfon Bay shore (boundary the rise is measured from)
      5. KML features
      6. Well symbols coloured by cluster
    """
    from scipy.special import erfc
    from shapely.geometry import Point
    from shapely import contains_xy

    # ── Diffusivity D = K·b/Sy (Sy live from C3 WTF, as in drawdown map) ──
    _sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
    Sy = float(_sy_df[_sy_df["Cluster"] == 3]["Sy_median"].median())
    D = (DRAWDOWN_K_MDAY * DRAWDOWN_B_M) / Sy                      # m²/day
    t_days = SLR_WINDOW_YEARS * 365.0
    diff_len = np.sqrt(D * t_days)               # √(D·t), m
    slr_mm = SLR_RISE_M * 1000.0
    print(f"  SLR response: +{SLR_RISE_M:.3f} m over {SLR_WINDOW_YEARS:.0f} yr; "
          f"D={D:.1f} m²/day (Sy={Sy:.3f} [C3 WTF]), √(Dt)={diff_len:.0f} m")

    # ── Shore boundary at MEAN sea level (0 m AOD), no dune-toe offset ────
    # SLR head is referenced to mean sea level, not the +0.5 m erosion front.
    _front, waterline = _dem_waterline_to_dune_edge(
        shore_level=SLR_SHORE_LEVEL_M, offset_m=0)
    if waterline is None:
        print("  [WARNING] no SW waterline — skipping SLR response map")
        return

    # ── Transient head-rise field, clipped to the site outline ────────────
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    dist = np.array([waterline.distance(Point(x, y))
                     for x, y in zip(gx.ravel(), gy.ravel())]).reshape(gx.shape)
    rise = slr_mm * erfc(dist / (2.0 * diff_len))

    # Zero the SEAWARD side (the bay) so the band does not bleed below the
    # shore. Close the waterline through points well beyond the SW map corner
    # (land is at higher easting), so the polygon robustly encloses the whole
    # seaward wedge regardless of where the 0 m contour ends.
    from shapely.geometry import Polygon as _Poly
    wxy = list(waterline.coords)                    # ordered S→N
    far_w = XLIM[0] - 2000
    far_s = YLIM[0] - 2000
    seaward_ring = (wxy
                    + [(far_w, wxy[-1][1]),          # due W of N end
                       (far_w, far_s),               # far SW corner
                       (wxy[0][0] + 2000, far_s),    # due S of S end, padded E
                       (wxy[0][0], wxy[0][1])])       # back to S end of line
    seaward_poly = _Poly(seaward_ring).buffer(0)
    try:
        sea_in = contains_xy(seaward_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
        rise[sea_in] = np.nan
    except Exception:
        pass

    site_poly = load_site_polygon()
    if site_poly is not None:
        try:
            inside = contains_xy(site_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
        except Exception:
            from shapely.prepared import prep
            sp = prep(site_poly)
            inside = np.zeros(gx.shape, dtype=bool)
            for i in range(gx.shape[0]):
                for j in range(gx.shape[1]):
                    if sp.contains(Point(gx[i, j], gy[i, j])):
                        inside[i, j] = True
        rise = np.where(inside, rise, np.nan)

    # ── Render ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")

    # Layer 1 — hillshade
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    # Layer 2 — head-rise filled contours. COMMON level set shared with the
    # erosion map (plot_coastal_erosion) for direct comparability. Fill and
    # lines share edges; extend="max" so fill floor = lowest line.
    rise_levels = [2, 5, 10, 15, 20, 30, 40, 50]
    rise_lines  = [2, 5, 15, 30]
    rise_cmap = plt.cm.GnBu
    cf = ax.contourf(gx, gy, rise, levels=rise_levels, cmap=rise_cmap,
                     vmin=rise_levels[0], vmax=rise_levels[-1],
                     alpha=0.55, zorder=3, extend="max")

    # Layer 3 — contour lines (subset of fill levels; all labelled)
    cs = ax.contour(gx, gy, rise, levels=rise_lines,
                    colors="#08306b", linewidths=1.0, alpha=0.85, zorder=4)
    cl = ax.clabel(cs, levels=rise_lines, inline=True, fontsize=9,
                   fmt="+%d mm", colors="black", inline_spacing=8)
    for txt in cl:
        txt.set_fontweight("bold")
        txt.set_bbox(dict(facecolor="white", alpha=0.75,
                          edgecolor="none", pad=1.5))

    # Layer 4 — shore boundary
    wx, wy = waterline.xy
    ax.plot(wx, wy, color="#08306b", lw=1.8, zorder=6,
            label=f"Caernarfon Bay shore ({SLR_SHORE_LEVEL_M:g} m AOD, MSL)")

    # Layer 5 — KML features
    kml_handles = draw_kml_features(ax, features, zorder=5)

    # Layer 6 — wells coloured by cluster
    cluster_handles = {}
    for _, row in wt.iterrows():
        cl_ = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl_, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=30,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl_ not in cluster_handles:
            cluster_handles[cl_] = mpatches.Patch(color=col, label=f"C{cl_}")

    # Diffusion-length annotation (mirrors λ / L on Figures 3 & 4)
    ref_e, ref_n = 240500, 363100
    ax.annotate("", xy=(ref_e + diff_len, ref_n - 100),
                xytext=(ref_e, ref_n - 100),
                arrowprops=dict(arrowstyle="<->", color="#d62728", lw=1.5),
                zorder=10)
    ax.text(ref_e + diff_len / 2, ref_n - 200, f"√(Dt) = {diff_len:.0f} m",
            ha="center", va="top", fontsize=9, fontweight="bold",
            color="#d62728", zorder=10,
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=2))

    # Colorbar
    cb = fig.colorbar(cf, ax=ax, fraction=0.03, pad=0.04, shrink=0.85)
    cb.set_label(f"Head rise from +{SLR_RISE_M:.2f} m SLR over "
                 f"{SLR_WINDOW_YEARS:.0f} yr (mm)", fontsize=9)

    # Legends
    shore_handle = [Line2D([0], [0], color="#08306b", lw=1.8,
                    label=f"Caernarfon Bay shore ({SLR_SHORE_LEVEL_M:g} m AOD, MSL)")]
    l1 = ax.legend(handles=kml_handles + shore_handle,
                   fontsize=7, loc="upper right", framealpha=0.92,
                   title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()),
              fontsize=8, loc="lower right",
              title="Cluster", title_fontsize=8, framealpha=0.92)

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.set_title(
        f"Sea-level-rise water-table response — {SLR_WINDOW_YEARS:.0f}-yr transient\n"
        f"+{SLR_RISE_M:.2f} m SLR at Caernarfon Bay shore, "
        f"diffusion length √(Dt) = {diff_len:.0f} m",
        fontsize=10, fontweight="bold", pad=10)

    plt.tight_layout()
    render_figure(fig, OUT_20_SLR_RESPONSE)
    plt.close(fig)
    print(f"  Saved → {OUT_20_SLR_RESPONSE}")


def _seaward_ring(line_coords):
    """Close a S→N shore polyline into a polygon enclosing the seaward wedge
    (land is at higher easting here), for masking the bay side. Returns a
    shapely Polygon."""
    from shapely.geometry import Polygon as _Poly
    xy = list(line_coords)
    far_w = XLIM[0] - 2000
    far_s = YLIM[0] - 2000
    ring = (xy + [(far_w, xy[-1][1]),
                  (far_w, far_s),
                  (xy[0][0] + 2000, far_s),
                  (xy[0][0], xy[0][1])])
    return _Poly(ring).buffer(0)


def _erosion_field(gx, gy, retreat_m=None, h0_mm=None):
    """Erosion drawdown field (mm, positive = head loss) on grid gx,gy.

    Source drawdown h0 (positive = head loss) is set one of two ways:
      • h0_mm given → used directly as the source drawdown. Used by the
        driver-change map for a chronic multi-year drawdown expressed as
        (years × δ₀), rate-independent (e.g. SLR_WINDOW_YEARS × δ₀ for the
        5-yr chronic coastal field). δ₀ from _load_coastal_fit() is already
        returned as a positive magnitude, so a positive year-count gives a
        positive (loss) h0 — matching the retreat_m path's sign convention.
      • else retreat_m given (or default COAST_RETREAT_M) → h0 computed as the
        single-event construction retreat_m × (δ₀ / COAST_RETREAT_RATE).
    The dune-toe front, exponential inland decay over L, and seaward-side
    zeroing are identical in both cases.
    Returns (field, front, waterline, h0, L) or (None,...).
    """
    from shapely.geometry import Point
    from shapely import contains_xy
    _h0_default, delta0, L, _r, _pm = _coastal_edge_h0(retreat_m)
    h0 = float(h0_mm) if h0_mm is not None else _h0_default
    front, waterline = _dem_waterline_to_dune_edge()
    if front is None:
        return None, None, None, None, None
    d = np.array([front.distance(Point(x, y))
                  for x, y in zip(gx.ravel(), gy.ravel())]).reshape(gx.shape)
    eff = np.maximum(h0 * (1.0 - d / L), 0.0)
    try:
        sea = contains_xy(_seaward_ring(front.coords),
                          gx.ravel(), gy.ravel()).reshape(gx.shape)
        eff[sea] = 0.0
    except Exception:
        pass
    return eff, front, waterline, h0, L


def _slr_field(gx, gy):
    """SLR transient head-gain field (mm, positive = head gain) on grid gx,gy.
    MSL boundary, +SLR_RISE_M over SLR_WINDOW_YEARS, seaward side zeroed.
    Returns (field, waterline, diff_len, slr_mm) or (None,...) on failure."""
    from scipy.special import erfc
    from shapely.geometry import Point
    from shapely import contains_xy
    _sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
    Sy = float(_sy_df[_sy_df["Cluster"] == 3]["Sy_median"].median())
    D = (DRAWDOWN_K_MDAY * DRAWDOWN_B_M) / Sy
    diff_len = np.sqrt(D * SLR_WINDOW_YEARS * 365.0)
    slr_mm = SLR_RISE_M * 1000.0
    _f, waterline = _dem_waterline_to_dune_edge(
        shore_level=SLR_SHORE_LEVEL_M, offset_m=0)
    if waterline is None:
        return None, None, None, None
    d = np.array([waterline.distance(Point(x, y))
                  for x, y in zip(gx.ravel(), gy.ravel())]).reshape(gx.shape)
    rise = slr_mm * erfc(d / (2.0 * diff_len))
    try:
        sea = contains_xy(_seaward_ring(waterline.coords),
                          gx.ravel(), gy.ravel()).reshape(gx.shape)
        rise[sea] = 0.0
    except Exception:
        pass
    return rise, waterline, diff_len, slr_mm


def _scrape_response_mm(well, era, fallback):
    """Per-well measured scrape response (mm) from Script 09a BACI shifts
    (OUT_09_BACI_SHIFTS), matched on well + era. Falls back to the supplied
    value if unavailable."""
    try:
        df = pd.read_csv(OUT_09_BACI_SHIFTS)
        df.columns = [str(c).strip().lower() for c in df.columns]
        w, er, val = df.columns[0], df.columns[1], df.columns[2]
        row = df[(df[w].astype(str).str.lower() == well.lower()) &
                 (df[er].astype(str).str.contains(era, case=False))]
        return float(row[val].iloc[0]) * 1000.0
    except Exception:
        return float(fallback)


# Per-cut scrape metadata, keyed by footprint-KML basename. H0 (mm) is the
# measured per-well response (Script 09a BACI) where a before/after baseline
# exists (CEH36/18/21); for cuts with no monitored baseline (CEH40/41/42,
# Feb 2013 — dipwells from Jul 2014; Scrape_A/B, April 2015 — no in-cut well)
# H0 is ASSUMED equal to the CEH36 response and flagged. The canonical list and
# ordering of files lives in config.SCRAPE_KML_FILES (single source of truth);
# geometry is loaded via map_utils.load_scrape_kml().
# Fields: (label, epoch, baci_well, baci_era, fallback_mm, assumed)
SCRAPE_META = {
    "ceh36_scrape.kml": ("CEH36",    "April 2015", "CEH36", "Pure_Scraping",  129.5, False),
    "CEH18_scrape.kml": ("CEH18",    "Oct 2023",   "CEH18", "After_Scraping",   8.5, False),
    "CEH21_scrape.kml": ("CEH21",    "Oct 2023",   "CEH21", "After_Scraping",  73.5, False),
    "CEH40_scrape.kml": ("CEH40",    "Feb 2013",   None,    None,             None,  True),
    "CEH41_scrape.kml": ("CEH41",    "Feb 2013",   None,    None,             None,  True),
    "CEH42_Scape.kml":  ("CEH42",    "Feb 2013",   None,    None,             None,  True),
    "Scrape_A.kml":     ("Scrape A", "April 2015", None,    None,             None,  True),
    "Scrape_B.kml":     ("Scrape B", "April 2015", None,    None,             None,  True),
}


def _scrape_registry():
    """Resolve config.SCRAPE_KML_FILES into dicts with live geometry and H0 (mm).
    Assumed cuts inherit the CEH36 response. Cuts whose KML is absent are
    dropped. Returns [] if nothing loads."""
    ceh36 = _scrape_response_mm("CEH36", "Pure_Scraping", 129.5)
    reg = []
    for kml in SCRAPE_KML_FILES:
        label, epoch, well, era, fb, assumed = SCRAPE_META[kml]
        g = load_scrape_kml(kml)
        if g is None:
            continue
        H0 = ceh36 if assumed else _scrape_response_mm(well, era, fb)
        reg.append(dict(name=label, epoch=epoch, geom=g, H0=H0, assumed=assumed))
    return reg


def _load_real_scrape_geom():
    """Union of all scrape footprints in the registry (for rise-zone rendering
    and footprint outlines). Returns a (Multi)Polygon or None."""
    from shapely.ops import unary_union
    reg = _scrape_registry()
    return unary_union([s["geom"] for s in reg]) if reg else None


def _measured_ceh36_response():
    """Measured CEH36 scrape response (m), live from Script 09a paired BACI
    (CEH36 'Pure_Scraping' vs CEH4). This is the edge magnitude H0 anchor for
    the scrape-drain maps — an empirical quantity, not an assumed depth × Sy.
    Falls back to the documented first-pass default if the file is unavailable.
    That fallback used to be the literal 0.1295 - a published BACI result typed
    into an except branch, which pipeline_lint flags precisely because such a
    value goes stale silently while still looking authoritative."""
    try:
        df = pd.read_csv(OUT_09_BACI_SHIFTS)
        df.columns = [str(c).strip().lower() for c in df.columns]
        w, era = df.columns[0], df.columns[1]
        val = df.columns[2]
        row = df[(df[w].astype(str).str.lower() == "ceh36") &
                 (df[era].astype(str).str.contains("Pure_Scraping", case=False))]
        return float(row[val].iloc[0])
    except Exception:
        from utils.pipeline_params import default_value
        return float(default_value("ceh36_scrape_response_m"))


_COASTLINE_HWM_CACHE = None


def _load_coastline_hwm():
    """Load the Caernarfon Bay + Menai Strait High Water Mark coastline as a
    shapely geometry (EPSG:27700), used as the fixed-head boundary for the
    method-of-images correction in scrape drawdown calculations.

    Source: data/geo/coastline_hwm.geojson, derived from OpenStreetMap
    natural=coastline (ODbL) via Overpass API, 2026-06-30.

    Returns a LineString/MultiLineString, or None if the file is absent
    (callers fall back to unbounded superposition sum with a warning)."""
    global _COASTLINE_HWM_CACHE
    if _COASTLINE_HWM_CACHE is not None:
        return _COASTLINE_HWM_CACHE
    try:
        import json
        from shapely.geometry import shape
        coast_path = DATA_COASTLINE_HWM
        if not coast_path.exists():
            print("  [WARNING] coastline_hwm.geojson not found — "
                  "scrape drawdown will use unbounded cones (no coast correction)")
            return None
        with open(coast_path) as f:
            gj = json.load(f)
        geom = shape(gj["features"][0]["geometry"])
        _COASTLINE_HWM_CACHE = geom
        print(f"  coastline_hwm.geojson loaded "
              f"(type={geom.geom_type}, length={geom.length:.0f} m)")
        return geom
    except Exception as e:
        print(f"  [WARNING] could not load coastline_hwm.geojson ({e}) — "
              "scrape drawdown will use unbounded cones (no coast correction)")
        return None


def _reflect_across_coastline(geom, coastline):
    """Return the mirror image of a scrape footprint geometry reflected across
    the nearest point on the HWM coastline.  Used to construct the image
    source for the method-of-images fixed-head boundary correction.

    The reflection axis is the local tangent to the coastline at the nearest
    point.  This is exact for a straight boundary and accurate for the gently
    curved Caernarfon Bay coast (radius of curvature >> scrape–coast distance).

    Returns a translated shapely geometry positioned seaward of the coast."""
    from shapely.ops import nearest_points
    from shapely.affinity import translate

    centroid = geom.centroid
    coast_pt, _ = nearest_points(coastline, centroid)
    cx, cy = coast_pt.x, coast_pt.y

    # Local tangent: find nearest coastline vertex then use adjacent pair
    if hasattr(coastline, "coords"):
        coords = np.array(coastline.coords)
    else:
        # MultiLineString — use the component whose nearest point was found
        coords = np.array(
            min(coastline.geoms, key=lambda g: g.distance(centroid)).coords
        )
    dists = np.hypot(coords[:, 0] - cx, coords[:, 1] - cy)
    idx = int(np.argmin(dists))
    i0, i1 = max(0, idx - 1), min(len(coords) - 1, idx + 1)
    tx = coords[i1, 0] - coords[i0, 0]
    ty = coords[i1, 1] - coords[i0, 1]
    tmag = np.hypot(tx, ty)
    tx, ty = (tx / tmag, ty / tmag) if tmag > 1e-9 else (1.0, 0.0)

    # Normal to coastline (direction away from centroid = seaward)
    nx, ny = -ty, tx
    # Ensure normal points away from the scrape centroid
    if (centroid.x - cx) * nx + (centroid.y - cy) * ny < 0:
        nx, ny = -nx, -ny

    # Reflect centroid across the coastline tangent at coast_pt
    dx, dy = centroid.x - cx, centroid.y - cy
    dot = dx * nx + dy * ny
    rx = centroid.x - 2 * dot * nx
    ry = centroid.y - 2 * dot * ny

    return translate(geom, xoff=rx - centroid.x, yoff=ry - centroid.y)


def _scrape_rise_field(gx, gy, epochs=None):
    """Rise magnitude field for the scrape footprints (mm, positive = head gain).

    For each grid point within SCRAPE_RISE_BUFFER_M of any cut footprint,
    returns the H₀ of that cut — the measured BACI response at CEH36/18/21
    or the assumed CEH36 value for unmonitored cuts.  Points within range of
    more than one cut take the larger H₀ (in practice cuts are well-separated
    so overlap is negligible).

    Used in plot_net_state_map() to give the slack rises a positive contribution
    in the net field, correctly representing the dipole nature of each cut:
    surrounding area drawn down, footprint itself raised by approximately H₀.

    epochs : same semantics as _scrape_field(). None = all cuts."""
    from shapely.geometry import Point
    reg = _scrape_registry()
    if epochs is not None:
        reg = [s for s in reg if s["epoch"] in epochs]
    if not reg:
        return np.zeros(gx.shape)
    pts = [Point(x, y) for x, y in zip(gx.ravel(), gy.ravel())]
    rise = np.zeros(gx.size)
    for s in reg:
        d = np.array([s["geom"].distance(p) for p in pts])
        in_rise = d <= SCRAPE_RISE_BUFFER_M
        rise = np.where(in_rise & (s["H0"] > rise), s["H0"], rise)
    return rise.reshape(gx.shape)


def _scrape_field(gx, gy, epochs=None):
    """Scrape-drain drawdown field (mm, positive = head loss) on grid gx,gy.

    Steady-state leaky-aquifer superposition with method-of-images coastal
    boundary correction.  By default all 8 mapped cuts are included as
    permanent co-active drains contributing to long-term equilibrium.

    For each cut i the contribution at grid point (x,y) is:
        H0_i · [exp(-d_real_i / λ) − exp(-d_image_i / λ)]

    where d_real_i  = distance from (x,y) to cut i footprint,
          d_image_i = distance from (x,y) to the mirror image of cut i
                      reflected across the HWM coastline,
          λ = √(K·b / (Sy·β₃))  [C3 propagation medium, live pipeline values].

    The image term enforces h → 0 at the coast (fixed-head sea boundary).
    Coastline: data/geo/coastline_hwm.geojson (OSM HWM, EPSG:27700).
    Falls back to unbounded sum if file absent (warning printed).

    H0_i is the BACI-measured per-well response (Script 09a) for CEH36/18/21;
    assumed = CEH36 for the unmonitored Feb-2013 and Scrape_A/B cuts.
    Each cut's rise zone (footprint + SCRAPE_RISE_BUFFER_M) is masked NaN.

    epochs : set of epoch strings or None
        If set, only cuts whose epoch is in the set are included.
        Example: epochs={"Feb 2013", "April 2015"} excludes Oct 2023 cuts.
        Use for the clearfell-baseline figure where Oct 2023 cuts postdate
        the felling event.  Default None = all epochs (equilibrium map).

    Returns (field, H0_ceh36, lam, geom_union) or (None, None, None, None).
    geom_union is the union of the *filtered* cut footprints."""
    from shapely.geometry import Point
    try:
        _sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
        Sy = float(_sy_df[_sy_df["Cluster"] == 3]["Sy_median"].median())
        _mech = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
        beta3_m = float(_mech[_mech["Cluster"] == 3]["beta_3_drainage"].iloc[0])
    except Exception:
        return None, None, None, None
    lam = np.sqrt((DRAWDOWN_K_MDAY * DRAWDOWN_B_M) / (Sy * (beta3_m / 30.0)))
    reg = _scrape_registry()
    if epochs is not None:
        reg = [s for s in reg if s["epoch"] in epochs]
    if not reg:
        return None, None, None, None

    coastline = _load_coastline_hwm()   # None → unbounded fallback

    pts = [Point(x, y) for x, y in zip(gx.ravel(), gy.ravel())]
    field = np.zeros(gx.size)
    rise  = np.zeros(gx.size, dtype=bool)
    for s in reg:
        d_real = np.array([s["geom"].distance(p) for p in pts])
        if coastline is not None:
            img_geom = _reflect_across_coastline(s["geom"], coastline)
            d_image  = np.array([img_geom.distance(p) for p in pts])
            field += s["H0"] * (np.exp(-d_real / lam) - np.exp(-d_image / lam))
        else:
            field += s["H0"] * np.exp(-d_real / lam)   # unbounded fallback
        rise |= (d_real <= SCRAPE_RISE_BUFFER_M)
    field = np.maximum(field, 0.0)   # image term can go slightly negative near coast
    field[rise] = np.nan             # mask rise zones: slack rises, not drawn down
    field = field.reshape(gx.shape)
    H0_ceh36 = next((s["H0"] for s in reg if s["name"] == "CEH36"), reg[0]["H0"])
    if epochs is not None:
        from shapely.ops import unary_union as _uu
        geom_out = _uu([s["geom"] for s in reg])
    else:
        geom_out = _load_real_scrape_geom()
    return field, H0_ceh36, lam, geom_out


def _overlay_scrape_rise(ax, geom, zbase=7):
    """Draw the scrape footprints as a RISE zone (blue), consistent with
    plot_scrape_drawdown: the slack rises, so it is shown as a rise zone
    (footprint + SCRAPE_RISE_BUFFER_M buffer) rather than as part of the
    surrounding drawdown. Handles Polygon and MultiPolygon."""
    if geom is None:
        return
    def _g(g):
        return list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    rise = geom.buffer(SCRAPE_RISE_BUFFER_M)
    for rz in _g(rise):
        rx, ry = rz.exterior.xy
        ax.fill(rx, ry, facecolor="#4a90d9", alpha=0.40, zorder=zbase)
        ax.plot(rx, ry, color="#1a4e80", lw=0.9, ls=":", zorder=zbase)
    for sp in _g(geom):
        sx, sy = sp.exterior.xy
        ax.fill(sx, sy, facecolor="#1a4e80", alpha=0.85, zorder=zbase + 1)
        ax.plot(sx, sy, color="#0d2b4a", lw=1.4, zorder=zbase + 2)


def _forest_field(gx, gy):
    """Forest interception-deficit drawdown field (mm) on grid gx,gy — Euclidean
    distance from the KML forest boundary, H0 = 150 mm (forest interception
    deficit), decay λ as for the scrape (open-dune leaky aquifer). A coarse
    public-overview approximation of plot_drawdown_propagation (which uses a
    flow-weighted cost-distance). Returns (field, H0, lam, geom) or (None,...)."""
    from shapely.geometry import Point
    import geopandas as gpd
    forest_geom = None
    try:
        gdf = gpd.read_file(str(DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
        name_col = gdf["Name"].fillna("").astype(str)
        for idx, row in gdf.iterrows():
            nm = name_col.iloc[idx].lower()
            if "forest" in nm or "boundary" in nm:
                forest_geom = row.geometry
                break
    except Exception:
        forest_geom = None
    if forest_geom is None:
        return None, None, None, None
    try:
        _sy = pd.read_csv(OUT_18_WELL_SY_TABLE)
        Sy = float(_sy[_sy["Cluster"] == 3]["Sy_median"].median())
        _m = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
        b3 = float(_m[_m["Cluster"] == 3]["beta_3_drainage"].iloc[0])
    except Exception:
        return None, None, None, None
    lam = np.sqrt((DRAWDOWN_K_MDAY * DRAWDOWN_B_M) / (Sy * (b3 / 30.0)))
    H0 = 150.0                                          # mm interception deficit
    d = np.array([forest_geom.distance(Point(x, y))
                  for x, y in zip(gx.ravel(), gy.ravel())]).reshape(gx.shape)
    return H0 * np.exp(-d / lam), H0, lam, forest_geom


def _broadleaf_field(gx, gy):
    """Broadleaf-restock interception-deficit drawdown INCREMENT field (mm,
    positive = head loss) on grid gx,gy, for the 2005→2025 driver-change map.

    Same Euclidean-distance construction as _forest_field(), but:
      • polygon from KML_BROADLEAF (data/geo/broadleaf_restock.kml),
      • full-canopy H0 scaled by the broadleaf interception ratio:
            H0_BL_full = DRAWDOWN_H0_MM × (BROADLEAF_INTERCEPTION / FOREST_INTERCEPTION)
                       = 150 × (0.15 / 0.24) ≈ 94 mm,
      • only the 2005→2025 canopy INCREMENT contributes (the block was already
        near closed canopy by 2005), so the source magnitude is
            H0_BL_incr = (BL_CANOPY_FRACTION_2025 − BL_CANOPY_FRACTION_2005) × H0_BL_full
                       = (1.0 − 0.4) × 94 ≈ 56 mm,
      • same λ as the forest field (C3 open-dune leaky-aquifer propagation).

    SIGN: drawdown (positive head loss), the mirror image of the clearfell gain.
    This is the least-constrained field on the driver-change map — the caller
    flags the BL patch as modelled/indicative in the caption.

    Returns (field, H0_incr, lam, geom) or (None, None, None, None) on failure.
    """
    from shapely.geometry import Point
    import geopandas as gpd
    if not KML_BROADLEAF.exists():
        return None, None, None, None
    try:
        gdf = gpd.read_file(str(KML_BROADLEAF), driver="KML").to_crs("EPSG:27700")
        from shapely.ops import unary_union
        bl_geom = unary_union(list(gdf.geometry))
    except Exception:
        return None, None, None, None
    if bl_geom is None or bl_geom.is_empty:
        return None, None, None, None
    try:
        _sy = pd.read_csv(OUT_18_WELL_SY_TABLE)
        Sy = float(_sy[_sy["Cluster"] == 3]["Sy_median"].median())
        _m = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
        b3 = float(_m[_m["Cluster"] == 3]["beta_3_drainage"].iloc[0])
    except Exception:
        return None, None, None, None
    lam = np.sqrt((DRAWDOWN_K_MDAY * DRAWDOWN_B_M) / (Sy * (b3 / 30.0)))

    H0_full = DRAWDOWN_H0_MM * (BROADLEAF_INTERCEPTION / FOREST_INTERCEPTION)
    H0_incr = (BL_CANOPY_FRACTION_2025 - BL_CANOPY_FRACTION_2005) * H0_full

    d = np.array([bl_geom.distance(Point(x, y))
                  for x, y in zip(gx.ravel(), gy.ravel())]).reshape(gx.shape)
    return H0_incr * np.exp(-d / lam), H0_incr, lam, bl_geom


def plot_coastal_net_effect(wt, features, dpi=300):
    """
    Figure 6: NET coastal water-table change — sea-level-rise head gain minus
    coastal-erosion drawdown — over a matched 5-year window, on the DEM
    hillshade. Diverging scale: blue = net head RISE, red = net head FALL,
    black line = zero (where the two processes balance).

        net(d) = Δh_SLR(d) − Δh_erosion(d)

    Both component fields are built exactly as in plot_slr_response() and
    plot_coastal_erosion() and reused here via _slr_field() / _erosion_field().

    ── IMPORTANT CAVEATS (also in the figure caption) ────────────────────────
    This figure combines two DELIBERATELY different kinds of forcing and is
    illustrative, NOT a closed water budget:
      • Single shore only. Both fields are referenced to the eroding
        Caernarfon Bay (SW) shore. The Menai / Malltraeth margins are not
        represented; SLR there is omitted.
      • Episodic vs gradual. Erosion is ONE ~6 m retreat event (Storm Brendan
        exemplar); SLR is a GRADUAL +SLR_RISE_M accrued over the window. A
        real 5-yr period could contain zero, one, or several storm pulses, so
        the red (erosion-dominated) band would deepen/widen in a storm-rich
        window and shrink in a quiet one.
      • Different anchors. SLR is referenced to mean sea level (0 m AOD) with
        no offset; erosion is referenced to the dune toe (COAST_SHORE_LEVEL_M
        + COAST_DUNE_OFFSET_M inland). This is physically appropriate (the
        water table is pinned to MSL; erosion bites at the dune front) but
        means the two zero-distance points differ by ~100 m.
      • Assumption-stacked parameters. δ₀, L (live from Script 25), the
        retreat rate, the diffusivity (K, b literature; Sy live C3 WTF), the
        window and SLR amount are all flagged constants; the result scales
        with them. See the CONSTANTS block.

    The figure's purpose is to show the SPATIAL PARTITION: a narrow
    erosion-dominated band along the dune-toe margin (where the confounded
    C5 / western-C3 wells sit), flanked by SLR-dominated rise at the immediate
    shore and near-neutral conditions inland. It motivates — and does not
    undermine — the BACI easting × time correction (see §5).

    Layers:
      1. DEM hillshade
      2. Net head-change filled contours (RdBu diverging, semi-transparent)
      3. Net contour lines + emphasised zero line
      4. KML features
      5. Well symbols coloured by cluster
    """
    from matplotlib.colors import TwoSlopeNorm
    from shapely import contains_xy
    from shapely.geometry import Point

    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    eros, front, _wl_e, h0, L = _erosion_field(gx, gy)
    if eros is None:
        print("  [WARNING] erosion field unavailable — skipping net map")
        return
    slr, _wl_s, diff_len, slr_mm = _slr_field(gx, gy)
    if slr is None:
        print("  [WARNING] SLR field unavailable — skipping net map")
        return

    net = slr - eros                                  # +ve gain, -ve loss

    site_poly = load_site_polygon()
    if site_poly is not None:
        try:
            inside = contains_xy(site_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
            net = np.where(inside, net, np.nan)
        except Exception:
            pass

    vmax = float(np.nanmax(np.abs(net)))
    print(f"  net head change range: {np.nanmin(net):.1f} to "
          f"{np.nanmax(net):.1f} mm  (h₀_eros={h0:.0f}, SLR={slr_mm:.0f} mm)")

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    levels = np.linspace(-vmax, vmax, 13)
    cf = ax.contourf(gx, gy, net, levels=levels, cmap="RdBu", norm=norm,
                     alpha=0.6, zorder=3, extend="both")
    cs = ax.contour(gx, gy, net, levels=[-15, -10, -5, 5, 10],
                    colors="#333333", linewidths=0.8, alpha=0.75, zorder=4)
    cl = ax.clabel(cs, inline=True, fontsize=8, fmt="%+d mm", colors="black")
    for txt in cl:
        txt.set_fontweight("bold")
        txt.set_bbox(dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1))
    # Emphasised zero line — where SLR gain balances erosion drawdown
    ax.contour(gx, gy, net, levels=[0], colors="black",
               linewidths=1.6, zorder=5)

    kml_handles = draw_kml_features(ax, features, zorder=6)

    cluster_handles = {}
    for _, row in wt.iterrows():
        cl_ = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl_, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=28,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl_ not in cluster_handles:
            cluster_handles[cl_] = mpatches.Patch(color=col, label=f"C{cl_}")

    cb = fig.colorbar(cf, ax=ax, fraction=0.03, pad=0.04, shrink=0.85)
    cb.set_label("Net 5-yr head change: SLR gain − erosion drawdown (mm)",
                 fontsize=9)

    zero_handle = [Line2D([0], [0], color="black", lw=1.6,
                          label="Zero (SLR ≈ erosion)")]
    l1 = ax.legend(handles=kml_handles + zero_handle,
                   fontsize=7, loc="upper right", framealpha=0.92,
                   title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()),
              fontsize=8, loc="lower right",
              title="Cluster", title_fontsize=8, framealpha=0.92)

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.set_title(
        "Net coastal water-table change — SLR gain minus erosion drawdown\n"
        f"+{SLR_RISE_M:.2f} m SLR over {SLR_WINDOW_YEARS:.0f} yr (gradual) vs one "
        f"{COAST_RETREAT_M:.0f} m retreat (episodic)  |  blue = net rise, red = net fall",
        fontsize=10, fontweight="bold", pad=10)

    plt.tight_layout()
    render_figure(fig, OUT_20_COASTAL_NET)
    plt.close(fig)


def plot_scrape_coastal_net(wt, features, dpi=300):
    """
    Drawdown imposed on the CLEARFELL PRE-FELL BASELINE (Oct 2017) by the two
    non-felling drivers that bear on the compartment at the time of felling:
    the Feb 2013 and Apr 2015 scrape cuts (5 cuts, acting as co-active drains)
    and Storm Brendan's coastal retreat (one COAST_RETREAT_M event).
    Both are head LOSSES, so the combined field is a simple drawdown sum:

        drawdown(x,y) = Δh_scrape(Feb2013+Apr2015) + Δh_erosion

    The Oct 2023 cuts (CEH18, CEH21) are deliberately excluded: they postdate
    the clearfell by six years and play no part in the pre-fell baseline.
    Sea-level rise is excluded: this figure shows only the two confounders the
    clearfell BACI must separate from the felling signal (§5.4.2/§5.4.3).
    The scrape interiors are masked (the slacks themselves rise).
    Rendered on the shared sequential drawdown scale for direct comparison
    with the standalone scrape and erosion maps.
    """
    from shapely import contains_xy

    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    eros, front, _wl_e, h0, L = _erosion_field(gx, gy)
    scr, scr_H0, scr_lam, scr_geom = _scrape_field(
        gx, gy, epochs={"Feb 2013", "April 2015"}   # Oct 2023 cuts postdate the clearfell
    )
    if eros is None or scr is None:
        print("  [WARNING] a component field is unavailable — skipping baseline drawdown map")
        return

    dd = scr + eros                                   # mm, both head losses

    site_poly = load_site_polygon()
    if site_poly is not None:
        try:
            inside = contains_xy(site_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
            dd = np.where(inside, dd, np.nan)
        except Exception:
            pass

    print(f"  clearfell-baseline drawdown: max {np.nanmax(dd):.0f} mm "
          f"(scrape H0={scr_H0:.0f} mm [measured], Storm Brendan h0={h0:.0f} mm, "
          f"retreat={COAST_RETREAT_M:.0f} m)")

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    import matplotlib.patheffects as _pe
    dd_fill = np.where(dd > DRAWDOWN_FILL_LEVELS[0], dd, np.nan)
    cf = ax.contourf(gx, gy, dd_fill, levels=DRAWDOWN_FILL_LEVELS, cmap=DRAWDOWN_CMAP,
                     alpha=DRAWDOWN_ALPHA, zorder=3, extend="max")
    cs = ax.contour(gx, gy, dd, levels=DRAWDOWN_LINE_LEVELS,
                    colors="#7a4a00", linewidths=0.8, alpha=0.8, zorder=4)
    cl = ax.clabel(cs, levels=DRAWDOWN_LINE_LABELS, inline=True, fontsize=8,
                   fmt="%d mm", colors="black")
    for txt in cl:
        txt.set_fontweight("bold")
        txt.set_bbox(None)
        txt.set_path_effects([_pe.withStroke(linewidth=2.2, foreground="white")])

    kml_handles = draw_kml_features(ax, features, zorder=6)

    _overlay_scrape_rise(ax, scr_geom, zbase=7)

    cluster_handles = {}
    for _, row in wt.iterrows():
        cl_ = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl_, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=28,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl_ not in cluster_handles:
            cluster_handles[cl_] = mpatches.Patch(color=col, label=f"C{cl_}")

    cb = fig.colorbar(cf, ax=ax, fraction=0.03, pad=0.04, shrink=0.85)
    cb.set_label("Combined drawdown on the pre-fell baseline (mm)", fontsize=9)

    handles = kml_handles + [
        mpatches.Patch(facecolor="#4a90d9", alpha=0.6, edgecolor="#0d2b4a", label="Scrape rise zone (level rose)"),
    ]
    l1 = ax.legend(handles=handles, fontsize=7, loc="upper right",
                   framealpha=0.92, title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()), fontsize=8,
              loc="lower right", title="Cluster", title_fontsize=8, framealpha=0.92)

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.set_title(
        "Drawdown imposed on the clearfell pre-fell baseline (Oct 2017)\n"
        f"Feb 2013 + Apr 2015 scrape cuts (H₀ measured at CEH36, assumed elsewhere) "
        f"+ Storm Brendan {COAST_RETREAT_M:.0f} m retreat · combined head loss\n"
        "Oct 2023 cuts (CEH18/CEH21) excluded — postdate the clearfell by 6 years",
        fontsize=9.5, fontweight="bold", pad=10)

    plt.tight_layout()
    render_figure(fig, OUT_20_CLEARFELL_BASELINE_DRAWDOWN)
    plt.close(fig)
    print(f"  Saved → {OUT_20_CLEARFELL_BASELINE_DRAWDOWN}")


def plot_public_panel(wt, features, dpi=300):
    """
    Public-summary figure: three drivers of water-table LOWERING side by side on
    one shared drawdown scale — the forest canopy, a dune scrape, and coastal
    erosion. Same colour = same amount of lowering, so the public can compare
    magnitude and reach directly without any misleading stacked "net". Each
    field is the coarse Euclidean drawdown model on the common grid; this is an
    illustrative comparison, not interpolated observations.
    """
    from shapely import contains_xy

    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    forest, fH0, _, forest_geom = _forest_field(gx, gy)
    scr, sH0, _, scr_geom = _scrape_field(gx, gy)
    eros, front, waterline, eH0, _L = _erosion_field(gx, gy)
    if forest is None or scr is None or eros is None:
        print("  [WARNING] a component field is unavailable — skipping public panel")
        return

    site_poly = load_site_polygon()
    inside = None
    if site_poly is not None:
        try:
            inside = contains_xy(site_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
        except Exception:
            inside = None

    def _clip(f):
        return np.where(inside, f, np.nan) if inside is not None else f

    panels = [
        ("Coastal erosion (a storm)", _clip(eros), waterline, "coast"),
        ("The forest canopy", _clip(forest), forest_geom, "forest"),
        ("A dune scrape", _clip(scr), scr_geom, "scrape"),
    ]

    import matplotlib.patheffects as _pe

    def _render(ax, title, field, geom, kind):
        load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
        ff = np.where(field > DRAWDOWN_FILL_LEVELS[0], field, np.nan)
        cf = ax.contourf(gx, gy, ff, levels=DRAWDOWN_FILL_LEVELS, cmap=DRAWDOWN_CMAP,
                         alpha=DRAWDOWN_ALPHA, zorder=3, extend="max")
        # Band-boundary lines so the low bands (2–5 / 5–10 / 10–25) read clearly
        cs = ax.contour(gx, gy, field, levels=DRAWDOWN_LINE_LEVELS,
                        colors="#5a3a00", linewidths=0.6, alpha=0.8, zorder=4)
        labs = ax.clabel(cs, inline=True, fontsize=7, fmt="%d", colors="black")
        for t in labs:
            t.set_bbox(None)
            t.set_path_effects([_pe.withStroke(linewidth=1.8, foreground="white")])
        ax.scatter(wt["E"], wt["N"], c="#444", s=5, alpha=0.45, zorder=5)
        if kind == "forest" and geom is not None:
            for poly in (geom.geoms if geom.geom_type.startswith("Multi") else [geom]):
                ax.plot(*poly.exterior.xy, color="#1b5e20", lw=1.6, zorder=6)
        elif kind == "scrape" and geom is not None:
            _overlay_scrape_rise(ax, geom, zbase=6)
        elif kind == "coast" and geom is not None:
            try:
                ax.plot(*geom.xy, color="#0b5394", lw=1.6, zorder=6)
            except Exception:
                pass
        ax.set_xlim(*XLIM)
        ax.set_ylim(*YLIM)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(title, fontsize=13, fontweight="bold", pad=6)
        return cf

    # Portrait 1-over-2: forest spans the top, scrape + erosion below.
    fig = plt.figure(figsize=(10.5, 13.0), facecolor="white")
    gs = fig.add_gridspec(2, 2, height_ratios=[2.0, 1.0], hspace=0.10, wspace=0.05)
    ax_top = fig.add_subplot(gs[0, :])
    ax_bl  = fig.add_subplot(gs[1, 0])
    ax_br  = fig.add_subplot(gs[1, 1])

    _render(ax_top, *panels[0])            # coastal erosion, spanning top
    cf_ref = _render(ax_bl, *panels[1])    # forest — full range, used for colorbar
    _render(ax_br, *panels[2])             # dune scrape

    fig.suptitle("Several things lower the water table at Newborough Warren",
                 fontsize=16, fontweight="bold", y=0.94)

    cbar = fig.colorbar(cf_ref, ax=[ax_top, ax_bl, ax_br], orientation="horizontal",
                        fraction=0.04, pad=0.04, shrink=0.6, aspect=40,
                        ticks=DRAWDOWN_FILL_LEVELS, extend="max")
    cbar.set_label("How much the water table is lowered (mm)  ·  same colour = same amount",
                   fontsize=11)

    fig.text(0.5, 0.05,
             "Each driver has a different size and reach: the forest acts broadly, "
             "a scrape intensely but only locally, coastal erosion along the shore. "
             "Changing any one has knock-on effects elsewhere — there is no single switch.",
             ha="center", va="top", fontsize=10, style="italic", wrap=True)

    render_figure(fig, OUT_20_PUBLIC_PANEL, full_page=True)
    plt.close(fig)
    print(f"  Saved → {OUT_20_PUBLIC_PANEL}  "
          f"(forest H0={fH0:.0f}, scrape H0={sH0:.0f}, erosion h0={eH0:.0f} mm)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def plot_clearfell_gain(wt, features, dpi=300):
    """
    Clearfell gain map — IDW-interpolated water-table step-change at each well
    following the December 2017 FE compartment clearfell.

    Source data: 10b_spatial_step_data.csv (Script 10b), column
    `fell_step_cc` — climate-corrected post-vs-scrape-era mean shift (m),
    positive = rise. Wells with fewer than 6 post-felling observations or
    in PLOT_EXCLUDE are dropped, matching Script 10b's own filter. Values
    converted to mm for display.

    Interpolation: scipy griddata linear IDW (same as all other spatial
    figures in this script), clipped to the site polygon. Well symbols are
    coloured by their measured step magnitude so the data points read clearly
    against the interpolated surface.

    This is the direct complement to 20_drawdown_propagation_nohead.png:
    that map shows what the existing canopy costs the water table; this shows
    what the 2017 clearfell has returned, based on the measured network
    response rather than a parametric decay model.
    """
    import matplotlib.patheffects as _pe
    import matplotlib.patches as mpatches
    import geopandas as gpd
    from matplotlib.colors import BoundaryNorm, ListedColormap as _LC, Normalize

    # ── Load and filter 10b step data ────────────────────────────────────
    PLOT_EXCLUDE = {"ceh37", "ceh8", "fe1", "fe2", "fe3", "fe4"}
    MIN_POST     = 6

    try:
        df = pd.read_csv(OUT_10B_STEP_DATA)
    except Exception as e:
        print(f"  [WARNING] Could not load 10b step data ({e}) — skipping")
        return

    df = df.dropna(subset=["fell_step_cc", "E", "N"])
    df = df[df["n_post"] >= MIN_POST]
    df = df[~df["well"].isin(PLOT_EXCLUDE)]
    df["gain_mm"] = df["fell_step_cc"] * 1000.0   # m → mm

    if df.empty:
        print("  [WARNING] No valid fell_step_cc values after filtering — skipping")
        return

    pts  = df[["E", "N"]].values
    vals = df["gain_mm"].values

    print(f"  Clearfell gain: {len(df)} wells, "
          f"range {vals.min():+.0f} to {vals.max():+.0f} mm "
          f"(median {np.median(vals):+.0f} mm)")

    # ── Interpolate onto grid ─────────────────────────────────────────────
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    mask   = _site_mask(gx, gy)
    surf   = idw_surface(pts, vals, gx, gy, mask=mask)

    # ── Colour scale — diverging, fixed symmetric bands ──────────────────
    # Data range is roughly −165 to +100 mm; use a fixed ±150 mm symmetric
    # set so the zero point sits at the centre and the scale is comparable
    # with the net state map.
    LEVELS    = [-150, -100, -50, -25, -10, -5, -2, 2, 5, 10, 25, 50, 100, 150]
    LOSS_COLS = ["#c2410c", "#ea7317", "#f59e0b", "#fbbf24",
                 "#fcd34d", "#fde68a", "#fff3b0"]
    GAIN_COLS = ["#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa",
                 "#3b82f6", "#2563eb", "#1d4ed8"]
    div_cmap  = _LC(LOSS_COLS + GAIN_COLS)
    div_norm  = BoundaryNorm(LEVELS, ncolors=len(LOSS_COLS + GAIN_COLS))

    LINE_LEVELS = [-50, -25, -10, -5, 5, 10, 25, 50, 100]

    # ── Load KML geometries for overlay ──────────────────────────────────
    fell_geom   = None
    forest_geom = None
    try:
        gdf = gpd.read_file(str(DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
        name_col = gdf["Name"].fillna("").astype(str)
        for idx, row in gdf.iterrows():
            nm = name_col.iloc[idx].lower()
            if fell_geom is None and any(k in nm for k in ("felling", "experiment")):
                fell_geom = row.geometry
            if forest_geom is None and ("forest" in nm or "boundary" in nm):
                forest_geom = row.geometry
    except Exception:
        pass

    # ── Plot ─────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 10), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    cf = ax.contourf(gx, gy, surf, levels=LEVELS,
                     cmap=div_cmap, norm=div_norm,
                     alpha=DRAWDOWN_ALPHA, zorder=3, extend="both")

    # Zero contour
    ax.contour(gx, gy, surf, levels=[0],
               colors=["#1a1a1a"], linewidths=1.2, zorder=4)

    # Labelled band contours
    cs = ax.contour(gx, gy, surf, levels=LINE_LEVELS,
                    colors=["#5a3a00" if v < 0 else "#1e3a8a"
                            for v in LINE_LEVELS],
                    linewidths=0.55, alpha=0.75, zorder=4)
    import matplotlib.patheffects as _pe2
    labs = ax.clabel(cs, inline=True, fontsize=7, fmt="%+d")
    for t in labs:
        t.set_path_effects([_pe2.withStroke(linewidth=1.8, foreground="white")])

    # Well symbols coloured by measured step (same diverging scale)
    well_norm = Normalize(vmin=-150, vmax=150)
    sc = ax.scatter(df["E"], df["N"],
                    c=df["gain_mm"], cmap="RdBu", norm=well_norm,
                    s=28, edgecolors="#333", linewidths=0.5,
                    zorder=6, label="Measured step (mm)")

    # KML overlays
    if forest_geom is not None:
        for poly in (forest_geom.geoms
                     if forest_geom.geom_type.startswith("Multi")
                     else [forest_geom]):
            ax.plot(*poly.exterior.xy, color="#1b5e20", lw=1.6,
                    ls="--", zorder=7)
    if fell_geom is not None:
        for poly in (fell_geom.geoms
                     if fell_geom.geom_type.startswith("Multi")
                     else [fell_geom]):
            ax.plot(*poly.exterior.xy, color="darkorange", lw=2.0,
                    ls="-.", zorder=7)

    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)

    ax.set_title(
        "Clearfell step-change — measured water-table response\n"
        "Climate-corrected post-vs-scrape-era shift  ·  FE compartment, Dec 2017",
        fontsize=11, fontweight="bold", pad=8)

    cbar = fig.colorbar(cf, ax=ax, orientation="vertical",
                        fraction=0.035, pad=0.02, shrink=0.75, aspect=30,
                        ticks=[v for v in LEVELS if v % 5 == 0 or v == 2],
                        extend="both")
    cbar.set_label("Water-table step change (mm)  ·  blue = rise, brown = fall",
                   fontsize=9)
    cbar.ax.axhline(0, color="black", lw=1.0)

    legend_items = [
        mpatches.Patch(facecolor="none", edgecolor="#1b5e20",
                       lw=1.6, ls="--", label="Forest boundary"),
        mpatches.Patch(facecolor="none", edgecolor="darkorange",
                       lw=2.0, ls="-.", label="Clearfell zone (FE compartment)"),
    ]
    ax.legend(handles=legend_items, loc="lower left",
              fontsize=8, framealpha=0.85, edgecolor="#999")

    fig.text(0.5, 0.01,
             f"Source: 10b_spatial_step_data.csv (Script 10b)  ·  "
             f"fell_step_cc column  ·  n = {len(df)} wells\n"
             "Linear IDW interpolation  ·  "
             "Complement to 20_drawdown_propagation_nohead.png",
             ha="center", va="bottom", fontsize=8, color="#444", style="italic")

    render_figure(fig, OUT_20_CLEARFELL_GAIN)
    plt.close(fig)
    print(f"  Saved → {OUT_20_CLEARFELL_GAIN}  "
          f"(n={len(df)}, range {vals.min():+.0f} to {vals.max():+.0f} mm)")


def plot_msl5_change(wt, features, dpi=300):
    """
    MSL5 change map — five-year mean spring water level (van Willegen et al. 2025)
    at window end 2017 vs window end 2023.

    Baseline:  MSL5 window end 2017 (springs 2013–2017, pre-clearfell)
    Current:   MSL5 window end 2023 (springs 2019–2023)

    The 2023 current window is the canonical choice (see report §5.7.5):
    window end 2025 was examined but excluded owing to differential
    drainage memory at slow-τ wells contaminating the 2024 wet-spring
    signal at C4 Forest Controls (Hollingham 2026a §6.9).  The 2023
    window passes three independent validation checks: pre/post spring
    gap stability, correlation with the 20-year summer minimum slope
    (r = 0.49, p = 0.0005), and consistency with the early-summer PET
    intensification finding.

    The 2012 drought year (network mean −1271 mm) falls outside both
    windows, so neither is biased by that extreme.  The baseline window
    is the last complete pre-clearfell MSL5 window.

    Source data: 26_msl_5yr_per_well.csv (Script 26), column MSL5_m_bg
    (below-ground datum — the physical water-table depth; the pipe-top
    column carries each well's arbitrary stickup and is not used). Wells
    must have a valid MSL5 value at both window ends to be included
    (n = 61). The change is the raw 2023-2017 difference; no C2/C3
    normalisation is applied (the five-year spring mean already averages
    inter-annual climate noise, and a differential wet-year memory at
    slow-τ wells is not removable by a common-mode subtraction anyway).

    Interpolation: IDW power = 2.0 with a light Gaussian blur (σ = 1 grid
    cell = 50 m) applied within the site polygon.  Well markers use the
    same discrete banded colourmap as the surface so colours are
    self-consistent.  Changes < ±25 mm not coloured (below MSL5
    measurement noise floor after five-year averaging).
    """
    import geopandas as gpd
    import matplotlib.patheffects as _pe
    import matplotlib.patches as mpatches
    from matplotlib.colors import BoundaryNorm, ListedColormap as _LC
    from scipy.ndimage import gaussian_filter
    from shapely import contains_xy

    BASE_YR    = 2017
    CURR_YR    = 2023
    SIG_MM     = 25
    IDW_POWER  = 2.0
    GAUSS_SIGMA = 1

    # ── Load MSL5 per-well data ───────────────────────────────────────────
    if not OUT_26_5YR_PER_WELL.exists():
        print(f"  [WARNING] {OUT_26_5YR_PER_WELL} not found — skipping MSL5 change map")
        return

    df   = pd.read_csv(OUT_26_5YR_PER_WELL)
    # Honour the MSL5 well exclusion (Script 26 v1.2.0+: CEH13/CEH14 etc. are
    # retained in the per-well CSV but flagged msl5_excluded). Drop them so the
    # observed-change map matches the latest-MSL5 map and trajectory.
    if "msl5_excluded" in df.columns:
        _n0 = df["well"].nunique()
        df = df[~df["msl5_excluded"].astype(bool)].copy()
        _n1 = df["well"].nunique()
        if _n1 < _n0:
            print(f"  MSL5 change: excluded {_n0 - _n1} flagged well(s) (msl5_excluded)")
    locs = pd.read_csv(INT_LOCATIONS)
    locs["well"] = locs["Match_ID"].str.lower()

    base   = df[df["window_end_year"] == BASE_YR][["well","MSL5_m_bg","cluster_id"]].copy()
    curr   = df[df["window_end_year"] == CURR_YR][["well","MSL5_m_bg","cluster_id"]].copy()
    merged = base.merge(curr, on="well", suffixes=("_base","_curr"))
    merged["diff_mm"] = (merged["MSL5_m_bg_curr"] - merged["MSL5_m_bg_base"]) * 1000
    dfall  = merged.merge(locs[["well","E","N"]], on="well",
                          how="inner").dropna(subset=["E","N","diff_mm"])
    # Drop the Llyn Rhos-Ddu lake gauge (blacklisted, NaN cluster) so the
    # change network is the n=61 clustered set the report cites.
    dfall  = dfall.dropna(subset=["cluster_id_base"])

    if dfall.empty:
        print("  [WARNING] No wells with MSL5 at both window ends — skipping")
        return

    pts  = dfall[["E","N"]].values
    vals = dfall["diff_mm"].values

    print(f"  MSL5 change: n={len(dfall)} wells, "
          f"range {vals.min():+.0f} to {vals.max():+.0f} mm")

    # ── Interpolate ───────────────────────────────────────────────────────
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    site_poly = load_site_polygon()
    if site_poly is not None:
        from shapely import contains_xy as _cxy
        pmask = _cxy(site_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
    else:
        pmask = _site_mask(gx, gy)

    gpts = np.column_stack([gx.ravel(), gy.ravel()])
    d2   = np.sqrt(((gpts[:,None,:] - pts[None,:,:])**2).sum(axis=2))
    d2   = np.maximum(d2, 1.0)
    w    = 1.0 / d2**IDW_POWER
    surf_raw = ((w * vals[None,:]).sum(axis=1) / w.sum(axis=1)).reshape(gx.shape)
    surf_m   = np.where(pmask, surf_raw, np.nan)
    fill     = np.where(pmask, surf_m, float(np.nanmean(surf_m)))
    surf     = np.where(pmask,
                        gaussian_filter(fill.astype(float), sigma=GAUSS_SIGMA),
                        np.nan)
    surf_sig = np.where(np.abs(surf) >= SIG_MM, surf, np.nan)

    # ── Colour scale ──────────────────────────────────────────────────────
    LEVELS    = [-150,-100,-50,-25,-10,-5,-2, 2, 5,10,25,50,100,150]
    LINE_LEVELS = [-100,-50,-25, 25, 50, 100]
    LOSS_COLS = ["#c2410c","#ea7317","#f59e0b","#fbbf24",
                 "#fcd34d","#fde68a","#fff3b0"]
    GAIN_COLS = ["#dbeafe","#bfdbfe","#93c5fd","#60a5fa",
                 "#3b82f6","#2563eb","#1d4ed8"]
    div_cmap  = _LC(LOSS_COLS + GAIN_COLS)
    div_norm  = BoundaryNorm(LEVELS, ncolors=len(LOSS_COLS + GAIN_COLS))

    # Same discrete colourmap for markers (below threshold → grey)
    def _marker_col(v):
        return "#cccccc" if abs(v) < SIG_MM else div_cmap(div_norm(v))
    marker_cols = [_marker_col(v) for v in vals]

    # ── KML overlays ──────────────────────────────────────────────────────
    fell_geom = forest_geom = None
    try:
        gdf = gpd.read_file(str(DATA_KML_FEATURES),
                            driver="KML").to_crs("EPSG:27700")
        nc  = gdf["Name"].fillna("").astype(str)
        for idx, row in gdf.iterrows():
            nm = nc.iloc[idx].lower()
            if fell_geom is None and any(k in nm for k in ("felling","experiment")):
                fell_geom = row.geometry
            if forest_geom is None and ("forest" in nm or "boundary" in nm):
                forest_geom = row.geometry
    except Exception:
        pass

    # ── Plot ──────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 10), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    cf = ax.contourf(gx, gy, surf_sig, levels=LEVELS,
                     cmap=div_cmap, norm=div_norm,
                     alpha=DRAWDOWN_ALPHA, zorder=3, extend="both")

    # Zero contour
    ax.contour(gx, gy, surf, levels=[0],
               colors=["#1a1a1a"], linewidths=1.4, zorder=4)

    # Significance boundary
    ax.contour(gx, gy, surf, levels=[-SIG_MM, SIG_MM],
               colors=["#666"], linewidths=0.6,
               linestyles="--", alpha=0.6, zorder=4)

    # Band contours
    cs = ax.contour(gx, gy, surf_sig, levels=LINE_LEVELS,
                    colors=["#5a3a00" if v < 0 else "#1e3a8a"
                            for v in LINE_LEVELS],
                    linewidths=0.55, alpha=0.75, zorder=4)
    labs = ax.clabel(cs, inline=True, fontsize=7, fmt="%+d")
    import matplotlib.patheffects as _pe2
    for t in labs:
        t.set_path_effects(
            [_pe2.withStroke(linewidth=1.8, foreground="white")])

    # Well markers — same discrete scale as surface
    ax.scatter(dfall["E"], dfall["N"],
               c=marker_cols, s=26,
               edgecolors="#333", linewidths=0.6, zorder=6)

    # KML overlays
    if forest_geom is not None:
        for poly in (forest_geom.geoms
                     if forest_geom.geom_type.startswith("Multi")
                     else [forest_geom]):
            ax.plot(*poly.exterior.xy, color="#1b5e20", lw=1.6,
                    ls="--", zorder=7)
    if fell_geom is not None:
        for poly in (fell_geom.geoms
                     if fell_geom.geom_type.startswith("Multi")
                     else [fell_geom]):
            ax.plot(*poly.exterior.xy, color="darkorange", lw=2.0,
                    ls="-.", zorder=7)

    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)

    ax.set_title(
        f"MSL5 change — window end {BASE_YR} vs window end {CURR_YR}\n"
        f"Springs {BASE_YR-4}–{BASE_YR} (pre-clearfell)"
        f"  vs  Springs {CURR_YR-4}–{CURR_YR}\n"
        f"No climate correction  ·  |change| < 25 mm not coloured",
        fontsize=10, fontweight="bold", pad=8)

    cbar = fig.colorbar(cf, ax=ax, orientation="vertical",
                        fraction=0.035, pad=0.02, shrink=0.75, aspect=30,
                        ticks=LEVELS, extend="both")
    cbar.set_label("MSL5 change (mm)  ·  blue = shallower, brown = deeper",
                   fontsize=9)
    cbar.ax.axhline(0, color="black", lw=1.0)

    # Network mean MSL5 (below-ground) for caption — on the n=61 intersection
    # (wells present in BOTH windows), matching the per-well change basis.
    base_net = float(dfall["MSL5_m_bg_base"].mean() * 1000)
    curr_net = float(dfall["MSL5_m_bg_curr"].mean() * 1000)

    # ── §4.12 traceable per-well MSL5-change CSV + report numbers (Fig 63) ─
    # (§4.9.8 / Fig 54 until 2026-08-28: the Combined Driver Assessment moved
    #  to §4.12 and this map is Figure 63 — tools/section_map.csv and
    #  tools/figure_map.csv are the authorities, and both said so.)
    # Raw below-ground change (no C2/C3 normalisation — the 5-yr spring mean
    # already averages inter-annual climate noise). Significance at ±25 mm on
    # the raw change. n = 61 wells common to both windows.
    _msl = dfall[["well","cluster_id_base","MSL5_m_bg_base","MSL5_m_bg_curr","diff_mm","E","N"]].copy()
    _msl = _msl.rename(columns={"cluster_id_base": "cluster_id",
                                "MSL5_m_bg_base": "MSL5_bg_2017_m",
                                "MSL5_m_bg_curr": "MSL5_bg_2023_m",
                                "diff_mm": "raw_change_mm"})
    _msl["significant_25mm"] = _msl["raw_change_mm"].abs() >= SIG_MM
    _msl = _msl.sort_values("raw_change_mm")
    _msl.to_csv(OUT_20_MSL5_CHANGE_PERWELL, index=False)
    print(f"  Saved → {OUT_20_MSL5_CHANGE_PERWELL.name} ({len(_msl)} wells)")

    mrpt = ReportNumbers()
    mrpt.add("msl5_mean_2017", base_net, unit="mm", era="window-end 2017",
             note=f"network mean MSL5 below ground, n={len(_msl)} (springs 2013-2017)")
    mrpt.add("msl5_mean_2023", curr_net, unit="mm", era="window-end 2023",
             note=f"network mean MSL5 below ground, n={len(_msl)} (springs 2019-2023)")
    mrpt.add("msl5_deepening", curr_net - base_net, unit="mm",
             note=f"2023 minus 2017 network-mean change (below ground, n={len(_msl)})")
    mrpt.add("msl5_n_significant", int(_msl["significant_25mm"].sum()), unit="wells",
             note=f"wells with |raw change| >= {SIG_MM} mm of {len(_msl)}")
    for _w in ["wmc3", "ceh36", "ceh22", "ceh21", "ceh18", "ceh25"]:
        _r = _msl[_msl["well"].str.lower() == _w]
        if len(_r):
            mrpt.add(f"msl5_change_{_w}", float(_r["raw_change_mm"].iloc[0]), unit="mm",
                     well=_w.upper(), note="raw below-ground MSL5 change 2017->2023")
    n_saved = mrpt.save(OUT_20_MSL5_REPORT_NUMBERS)
    print(f"  Saved → {OUT_20_MSL5_REPORT_NUMBERS.name} ({n_saved} report numbers)")

    legend_items = [
        mpatches.Patch(facecolor="none", edgecolor="#1b5e20",
                       lw=1.6, ls="--", label="Forest boundary"),
        mpatches.Patch(facecolor="none", edgecolor="darkorange",
                       lw=2.0, ls="-.", label="Clearfell zone (FE compartment)"),
        mpatches.Patch(facecolor="#cccccc", edgecolor="#666",
                       lw=0.8, label=f"|change| < {SIG_MM} mm"),
    ]
    ax.legend(handles=legend_items, loc="lower left",
              fontsize=8, framealpha=0.85, edgecolor="#999")

    fig.text(
        0.5, 0.01,
        f"MSL5 window end {BASE_YR} (springs {BASE_YR-4}–{BASE_YR}, "
        f"net {base_net:+.0f} mm) vs "
        f"window end {CURR_YR} (springs {CURR_YR-4}–{CURR_YR}, "
        f"net {curr_net:+.0f} mm)  ·  n = {len(dfall)} wells\n"
        f"Raw difference, no climate correction  ·  "
        f"IDW p={IDW_POWER} + Gaussian σ={GAUSS_SIGMA} (50 m)  ·  "
        f"|change| < ±{SIG_MM} mm not coloured  ·  "
        f"Source: {OUT_26_5YR_PER_WELL.name}",
        ha="center", va="bottom", fontsize=7.5, color="#444", style="italic")

    render_figure(fig, OUT_20_MSL5_CHANGE)
    plt.close(fig)
    print(f"  Saved → {OUT_20_MSL5_CHANGE}")


def plot_observed_change(wt, features, dpi=300):
    """
    Observed water-table change map — empirical spring before/after comparison.

    Baseline:  Apr–May 2013, 2014, 2015  (3 springs, pre-scrape/pre-clearfell)
    Current:   Apr–May 2023, 2024, 2025  (3 springs, post-intervention)

    Using spring (Apr–May) means rather than full-year means removes seasonal
    bias from incomplete windows and captures the annual peak water-table
    signal when the dune aquifer is closest to recharge equilibrium.
    Three-year means on each side average out interannual variability (e.g.
    the anomalously wet 2024 spring and dry 2015 spring that dominate
    single-year comparisons).

    Wells require at least 5 valid spring readings per window (out of a
    maximum of 6) to be included, ensuring full coverage across all three
    years on each side.  This threshold excludes wells missing 2025 data
    (D25, CEH37) whose limited current coverage produced unstable estimates.

    Climate normalisation: the network-wide median shift (computed over
    reference-network wells, Cluster > 0) is subtracted from every well,
    removing the spatially uniform climate signal and isolating the
    management and coastal component.

    The result is IDW-interpolated onto the standard 50 m grid and clipped
    to the site polygon.

    Interpretation note: net observed change integrating all drivers.
    Cannot attribute change to individual causes.
    """
    import geopandas as gpd
    import matplotlib.patheffects as _pe
    import matplotlib.patches as mpatches
    from matplotlib.colors import BoundaryNorm, ListedColormap as _LC, Normalize

    BASE_YEARS = [2013, 2014, 2015]
    CURR_YEARS = [2023, 2024, 2025]
    MONTHS     = [4, 5]    # Apr + May
    MIN_OBS    = 5         # ≥5 of max 6 spring readings per window
    SIG_MM     = 25        # display threshold — changes < ±25 mm shown as neutral

    # ── Load wells and compute per-well spring means ──────────────────────
    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells.columns = [c.lower() for c in wells.columns]

    base_w = wells[(wells.index.month.isin(MONTHS)) &
                   (wells.index.year.isin(BASE_YEARS))]
    curr_w = wells[(wells.index.month.isin(MONTHS)) &
                   (wells.index.year.isin(CURR_YEARS))]
    b_n = base_w.notna().sum()
    c_n = curr_w.notna().sum()

    valid = b_n[(b_n >= MIN_OBS) & (c_n >= MIN_OBS)].index.tolist()
    diff_raw = ((curr_w.mean() - base_w.mean()) * 1000)[valid]  # mm

    # ── Climate normalisation ─────────────────────────────────────────────
    md = pd.read_csv(INT_MASTER_DATA)
    md["well"] = md["Name_Original"].str.lower()
    ref_wells = md[md["Cluster"] > 0]["well"].tolist()
    ref_valid = [w for w in ref_wells if w in diff_raw.index
                 and pd.notna(diff_raw[w])]
    climate_offset = float(diff_raw[ref_valid].median())
    diff_norm = diff_raw - climate_offset

    n_wells = len(diff_norm.dropna())
    print(f"  Observed spring change: {n_wells} wells, "
          f"climate offset = {climate_offset:+.1f} mm, "
          f"normalised range {diff_norm.min():+.0f} to "
          f"{diff_norm.max():+.0f} mm")

    # ── Merge with coordinates ────────────────────────────────────────────
    locs = pd.read_csv(INT_LOCATIONS)
    locs["well"] = locs["Match_ID"].str.lower()
    locs_sub = locs[["well", "E", "N"]].dropna()

    df = pd.DataFrame({"well": diff_norm.index,
                       "diff_mm": diff_norm.values})
    df = df.merge(locs_sub, on="well", how="inner").dropna(
        subset=["E", "N", "diff_mm"])
    df = df.merge(md[["well", "Cluster"]], on="well", how="left")

    pts  = df[["E", "N"]].values
    vals = df["diff_mm"].values

    # ── Interpolate — masked IDW with Gaussian smoothing ─────────────────
    # True IDW (power=1.5) with a light Gaussian blur (σ=2 grid cells = 100 m)
    # applied within the site polygon mask. This avoids the bullseye artefacts
    # of Delaunay linear interpolation (griddata) while preserving the regional
    # spatial signal. The Gaussian fill-and-blur approach: NaN cells outside
    # the site are temporarily filled with the site mean before blurring, then
    # re-masked, so the blur does not bleed values across the site boundary.
    from scipy.ndimage import gaussian_filter
    from shapely import contains_xy as _cxy

    gx, gy = np.meshgrid(GRID_XI, GRID_YI)

    # Site polygon mask (true boundary, not rectangular clip)
    site_poly = load_site_polygon()
    if site_poly is not None:
        pmask = _cxy(site_poly, gx.ravel(), gy.ravel()).reshape(gx.shape)
    else:
        pmask = _site_mask(gx, gy)

    # Vectorised IDW
    IDW_POWER = 1.5
    GAUSS_SIGMA = 2        # grid cells (50 m each) → ~100 m smoothing radius
    gpts = np.column_stack([gx.ravel(), gy.ravel()])
    d2 = np.sqrt(((gpts[:, None, :] - pts[None, :, :])**2).sum(axis=2))
    d2 = np.maximum(d2, 1.0)
    w  = 1.0 / d2**IDW_POWER
    surf_raw = ((w * vals[None, :]).sum(axis=1) / w.sum(axis=1)).reshape(gx.shape)

    # Mask, fill boundary for blur, re-mask
    surf_m   = np.where(pmask, surf_raw, np.nan)
    fill_val = float(np.nanmean(surf_m))
    surf_fill = np.where(pmask, surf_m, fill_val)
    surf = np.where(pmask, gaussian_filter(surf_fill.astype(float), sigma=GAUSS_SIGMA), np.nan)

    # Apply significance threshold: mask out sub-threshold changes so only
    # meaningful signals (|change| ≥ SIG_MM) are coloured; the near-neutral
    # zone is left transparent revealing the hillshade beneath.
    surf_sig = np.where(np.abs(surf) >= SIG_MM, surf, np.nan)

    # ── Colour scale ──────────────────────────────────────────────────────
    LEVELS    = [-150, -100, -50, -25, -10, -5, -2, 2, 5, 10, 25, 50, 100, 150]
    LOSS_COLS = ["#c2410c", "#ea7317", "#f59e0b", "#fbbf24",
                 "#fcd34d", "#fde68a", "#fff3b0"]
    GAIN_COLS = ["#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa",
                 "#3b82f6", "#2563eb", "#1d4ed8"]
    div_cmap  = _LC(LOSS_COLS + GAIN_COLS)
    div_norm  = BoundaryNorm(LEVELS, ncolors=len(LOSS_COLS + GAIN_COLS))
    LINE_LEVELS = [-100, -50, -25, 25, 50, 100]

    # ── KML overlays ──────────────────────────────────────────────────────
    fell_geom = forest_geom = None
    try:
        gdf = gpd.read_file(str(DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
        nc  = gdf["Name"].fillna("").astype(str)
        for idx, row in gdf.iterrows():
            nm = nc.iloc[idx].lower()
            if fell_geom is None and any(k in nm for k in ("felling","experiment")):
                fell_geom = row.geometry
            if forest_geom is None and ("forest" in nm or "boundary" in nm):
                forest_geom = row.geometry
    except Exception:
        pass

    # ── Plot ──────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 10), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    cf = ax.contourf(gx, gy, surf_sig, levels=LEVELS,
                     cmap=div_cmap, norm=div_norm,
                     alpha=DRAWDOWN_ALPHA, zorder=3, extend="both")

    # Zero contour on full (unthresholded) surface
    ax.contour(gx, gy, surf, levels=[0],
               colors=["#1a1a1a"], linewidths=1.4, zorder=4)

    # Significance boundary — thin dashed contour at ±SIG_MM
    ax.contour(gx, gy, surf, levels=[-SIG_MM, SIG_MM],
               colors=["#666"], linewidths=0.6, linestyles="--",
               alpha=0.6, zorder=4)

    cs = ax.contour(gx, gy, surf_sig, levels=LINE_LEVELS,
                    colors=["#5a3a00" if v < 0 else "#1e3a8a"
                            for v in LINE_LEVELS],
                    linewidths=0.55, alpha=0.75, zorder=4)
    labs = ax.clabel(cs, inline=True, fontsize=7, fmt="%+d")
    for t in labs:
        t.set_path_effects(
            [_pe.withStroke(linewidth=1.8, foreground="white")])

    well_norm = Normalize(vmin=-150, vmax=150)
    ax.scatter(df["E"], df["N"],
               c=df["diff_mm"], cmap="RdBu", norm=well_norm,
               s=20, edgecolors="#333", linewidths=0.4, zorder=6)

    if forest_geom is not None:
        for poly in (forest_geom.geoms
                     if forest_geom.geom_type.startswith("Multi")
                     else [forest_geom]):
            ax.plot(*poly.exterior.xy, color="#1b5e20", lw=1.6,
                    ls="--", zorder=7)
    if fell_geom is not None:
        for poly in (fell_geom.geoms
                     if fell_geom.geom_type.startswith("Multi")
                     else [fell_geom]):
            ax.plot(*poly.exterior.xy, color="darkorange", lw=2.0,
                    ls="-.", zorder=7)

    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)

    ax.set_title(
        "Observed spring water-table change — climate-normalised\n"
        f"Baseline Apr–May {BASE_YEARS[0]}–{BASE_YEARS[-1]}  "
        f"vs  Current Apr–May {CURR_YEARS[0]}–{CURR_YEARS[-1]}",
        fontsize=11, fontweight="bold", pad=8)

    cbar = fig.colorbar(cf, ax=ax, orientation="vertical",
                        fraction=0.035, pad=0.02, shrink=0.75, aspect=30,
                        ticks=LEVELS, extend="both")
    cbar.set_label("Net spring water-table change (mm)  ·  blue = rise, brown = fall",
                   fontsize=9)
    cbar.ax.axhline(0, color="black", lw=1.0)

    legend_items = [
        mpatches.Patch(facecolor="none", edgecolor="#1b5e20",
                       lw=1.6, ls="--", label="Forest boundary"),
        mpatches.Patch(facecolor="none", edgecolor="darkorange",
                       lw=2.0, ls="-.", label="Clearfell zone (FE compartment)"),
        mpatches.Patch(facecolor="#e0e0e0", edgecolor="#666",
                       lw=0.8, ls="--",
                       label=f"Uncoloured: |change| < {SIG_MM} mm (below measurement threshold)"),
    ]
    ax.legend(handles=legend_items, loc="lower left",
              fontsize=8, framealpha=0.85, edgecolor="#999")

    fig.text(
        0.5, 0.01,
        f"Net observed change integrating all drivers (clearfell, scraping, coastal retreat, climate drift).  "
        f"Climate signal removed: {climate_offset:+.1f} mm (network-wide median spring shift, "
        f"reference wells n={len(ref_valid)}).  "
        f"Changes < ±{SIG_MM} mm not coloured (within dipwell measurement precision).\n"
        f"n = {len(df)} wells  ·  Spring Apr–May means  ·  min {MIN_OBS} readings per window  ·  "
        f"IDW p=1.5 + Gaussian σ=2 (100 m) smoothing  ·  Cannot attribute change to individual drivers.",
        ha="center", va="bottom", fontsize=7.5, color="#444", style="italic")

    render_figure(fig, OUT_20_OBSERVED_CHANGE)
    plt.close(fig)
    print(f"  Saved → {OUT_20_OBSERVED_CHANGE}")


def plot_net_state_map(wt, features, dpi=300):
    """
    Net water-table state map — five simultaneous drivers combined on one
    diverging scale.

    Gains (blue): sea-level rise propagation; clearfell (removal of forest
    interception deficit over the felled FE compartment).
    Losses (brown/orange): remaining forest canopy drawdown; coastal erosion
    (Storm Brendan single-event retreat); scrape-drain drawdown.

    Net field (mm, positive = net gain):
        net = slr_gain + clearfell_gain
              - forest_remaining_loss - erosion_loss - scrape_loss

    Forest remaining: _forest_field() with the felled zone zeroed.
    Clearfell gain:   same H0 and λ as _forest_field(), but applied only
                      within/near the KML felling polygon (exp decay from its
                      boundary inward), representing the interception deficit
                      that has been removed.

    All fields use the coarse Euclidean model (same as plot_public_panel).
    """
    from shapely.geometry import Point, MultiPolygon
    from shapely import contains_xy

    gx, gy = np.meshgrid(GRID_XI, GRID_YI)

    # ── Load component fields ────────────────────────────────────────────
    forest_full, fH0, fLam, forest_geom = _forest_field(gx, gy)
    scr,         sH0, sLam, scr_geom   = _scrape_field(gx, gy)
    eros, front, waterline, eH0, _L    = _erosion_field(gx, gy)
    slr_gain, wl_slr, _, slr_mm        = _slr_field(gx, gy)

    if any(f is None for f in [forest_full, scr, eros, slr_gain]):
        print("  [WARNING] A component field is unavailable — skipping net state map")
        return

    # ── Load felling zone geometry from KML ─────────────────────────────
    fell_geom = None
    try:
        import geopandas as gpd
        gdf = gpd.read_file(str(DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
        name_col = gdf["Name"].fillna("").astype(str)
        for idx, row in gdf.iterrows():
            nm = name_col.iloc[idx].lower()
            if "felling" in nm or "experiment" in nm:
                fell_geom = row.geometry
                break
    except Exception:
        fell_geom = None

    # ── Mask forest field: zero over the felled zone ─────────────────────
    forest_remaining = forest_full.copy()
    if fell_geom is not None:
        try:
            in_fell = contains_xy(fell_geom,
                                  gx.ravel(), gy.ravel()).reshape(gx.shape)
            forest_remaining[in_fell] = 0.0
        except Exception:
            pass

    # ── Clearfell gain field: H0 × exp(-d/λ) from felling polygon edge ──
    # Inside the polygon d=0 → full H0; decays outward with same λ as forest.
    clearfell_gain = np.zeros_like(forest_full)
    if fell_geom is not None and fLam is not None:
        d_fell = np.array([fell_geom.distance(Point(x, y))
                           for x, y in zip(gx.ravel(), gy.ravel())]
                          ).reshape(gx.shape)
        clearfell_gain = fH0 * np.exp(-d_fell / fLam)
        # Inside the polygon: distance = 0, so gain = H0 (full restoration)

    # ── Combine: positive = net gain, negative = net loss ───────────────
    scr_rise = _scrape_rise_field(gx, gy)            # +H₀ at rise-zone pixels, 0 elsewhere
    scr_draw = np.where(np.isnan(scr), 0.0, scr)    # drawdown only (NaN rise zones → 0)
    net = (slr_gain + clearfell_gain + scr_rise
           - forest_remaining - eros - scr_draw)

    # ── Clip to site ─────────────────────────────────────────────────────
    site_poly = load_site_polygon()
    if site_poly is not None:
        try:
            inside = contains_xy(site_poly,
                                 gx.ravel(), gy.ravel()).reshape(gx.shape)
            net = np.where(inside, net, np.nan)
        except Exception:
            pass

    # ── Diverging colour scale ────────────────────────────────────────────
    # Symmetric bands around zero; brown = loss, blue = gain.
    NET_LEVELS  = [-150, -100, -50, -25, -10, -5, -2, 2, 5, 10, 25, 50, 100, 150]
    LOSS_COLS   = ["#c2410c", "#ea7317", "#f59e0b", "#fbbf24",
                   "#fcd34d", "#fde68a", "#fff3b0"]
    GAIN_COLS   = ["#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa",
                   "#3b82f6", "#2563eb", "#1d4ed8"]
    from matplotlib.colors import BoundaryNorm, ListedColormap as _LC
    all_cols  = LOSS_COLS + GAIN_COLS
    net_cmap  = _LC(all_cols)
    net_norm  = BoundaryNorm(NET_LEVELS, ncolors=len(all_cols))

    LINE_LEVELS = [-50, -25, -10, -5, 5, 10, 25, 50]

    import matplotlib.patheffects as _pe
    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(9, 10), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    cf = ax.contourf(gx, gy, net, levels=NET_LEVELS,
                     cmap=net_cmap, norm=net_norm,
                     alpha=0.68, zorder=3, extend="both")

    # Zero contour — bold boundary between gain and loss
    ax.contour(gx, gy, net, levels=[0],
               colors=["#1a1a1a"], linewidths=1.4, zorder=4)

    # Labelled band contours
    cs = ax.contour(gx, gy, net, levels=LINE_LEVELS,
                    colors=["#5a3a00" if v < 0 else "#1e3a8a" for v in LINE_LEVELS],
                    linewidths=0.55, alpha=0.75, zorder=4)
    labs = ax.clabel(cs, inline=True, fontsize=7, fmt="%+d",
                     colors=["#5a3a00" if v < 0 else "#1e3a8a" for v in LINE_LEVELS])
    for t in labs:
        t.set_path_effects([_pe.withStroke(linewidth=1.8, foreground="white")])

    # Well dots
    ax.scatter(wt["E"], wt["N"], c="#333", s=6, alpha=0.4, zorder=5)

    # Feature overlays: forest boundary, felling zone, scrape
    if forest_geom is not None:
        for poly in (forest_geom.geoms
                     if forest_geom.geom_type.startswith("Multi") else [forest_geom]):
            ax.plot(*poly.exterior.xy, color="#1b5e20", lw=1.6,
                    ls="--", zorder=6)
    if fell_geom is not None:
        for poly in (fell_geom.geoms
                     if fell_geom.geom_type.startswith("Multi") else [fell_geom]):
            ax.plot(*poly.exterior.xy, color="darkorange", lw=1.8,
                    ls="-.", zorder=6)
    _overlay_scrape_rise(ax, scr_geom, zbase=6)

    # Coastline / erosion front
    if front is not None:
        try:
            ax.plot(*front.xy, color="#0b5394", lw=1.4, ls=":", zorder=6)
        except Exception:
            pass

    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")
    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.tick_params(labelsize=8)

    ax.set_title(
        "Net water-table state — combined drivers\n"
        "Forest canopy · Clearfell gain · Dune scrape · Coastal erosion · SLR",
        fontsize=12, fontweight="bold", pad=8)

    cbar = fig.colorbar(cf, ax=ax, orientation="vertical",
                        fraction=0.035, pad=0.02, shrink=0.75, aspect=30,
                        ticks=NET_LEVELS, extend="both")
    cbar.set_label("Net water-table change (mm)  ·  blue = gain, brown = loss",
                   fontsize=9)
    cbar.ax.axhline(0, color="black", lw=1.2)

    # Legend patches
    legend_items = [
        mpatches.Patch(facecolor="none", edgecolor="#1b5e20",
                       lw=1.6, ls="--", label="Forest boundary (remaining canopy)"),
        mpatches.Patch(facecolor="none", edgecolor="darkorange",
                       lw=1.8, ls="-.", label="Clearfell zone (FE compartment)"),
        mpatches.Patch(facecolor="#4a90d9", alpha=0.6, edgecolor="#0d2b4a",
                       lw=1.2, label="Scrape rise zone (level rose)"),
        mpatches.Patch(facecolor="none", edgecolor="#0b5394",
                       lw=1.4, ls=":", label="Erosion front (Storm Brendan)"),
    ]
    ax.legend(handles=legend_items, loc="lower left",
              fontsize=8, framealpha=0.85, edgecolor="#999")

    fig.text(0.5, 0.01,
             f"Forest H₀ = {fH0:.0f} mm · Clearfell gain H₀ = {fH0:.0f} mm · "
             "Scrape H₀ per cut (CEH36/18/21 measured, others assumed = CEH36) · "
             f"Erosion h₀ = {eH0:.0f} mm · "
             f"SLR = +{slr_mm:.0f} mm over {SLR_WINDOW_YEARS:.0f} yr\n"
             "All fields: Euclidean-distance exponential decay model",
             ha="center", va="bottom", fontsize=8, color="#444",
             style="italic")

    render_figure(fig, OUT_20_NET_STATE_MAP)
    plt.close(fig)
    print(f"  Saved → {OUT_20_NET_STATE_MAP}  "
          f"(net range {np.nanmin(net):.0f} to {np.nanmax(net):.0f} mm)")


def _load_clearfell_observed_mm():
    """Observed clearfell BACI step (mm) live from Script 10a
    (ANCOVA_Forest_Impact_clearfell_step in 10a_report_numbers.csv, ~0.120 m).
    This is the OBSERVED impact-well response (Path B) — the driver-change map
    plots the measured value, not the 150 mm equilibrium interception deficit,
    so there is no modelled-vs-observed gap to reconcile for this field.
    Falls back to 120.0 mm with a warning if the CSV is unavailable."""
    try:
        df = pd.read_csv(OUT_10A_REPORT)
        row = df[df["Parameter"] == "ANCOVA_Forest_Impact_clearfell_step"]
        val_m = float(row["Value"].iloc[0])
        return val_m * 1000.0
    except Exception as e:
        print(f"  [WARNING] could not read 10a clearfell step ({e}) — "
              "using first-pass fallback 120.0 mm")
        return 120.0


def _driver_change_net(gx, gy, coast_years, clearfell_mm):
    """Build the 2005→2025 modelled driver-change net field (mm; +gain/−loss).

    Shared by the 5-yr and 20-yr driver-change maps. Coastal chronic horizon is
    `coast_years` × δ₀ (rate-independent, capped to zero at reach L). Clearfell
    gain uses the OBSERVED step `clearfell_mm` (Path B) rather than the 150 mm
    equilibrium. Standing pine cancels (not loaded). Fields are combined by
    LINEAR SUPERPOSITION (net = slr + clearfell + scr_rise − bl − eros −
    scr_draw); this is a first-order construction that may over-state the true
    combined drawdown where fields overlap.

    Returns a dict of everything the renderer needs, or None on failure.
    """
    from shapely.geometry import Point
    from shapely import contains_xy

    forest_full, fH0, fLam, forest_geom = _forest_field(gx, gy)   # λ + boundary overlay
    bl_incr,     blH0, blLam, bl_geom   = _broadleaf_field(gx, gy)
    scr,         sH0, sLam, scr_geom    = _scrape_field(gx, gy, epochs=None)
    delta0, L_coast = _load_coastal_fit()
    coast_h0_mm = coast_years * delta0
    eros, front, waterline, eH0, _L     = _erosion_field(gx, gy, h0_mm=coast_h0_mm)
    slr_gain, wl_slr, _, slr_mm         = _slr_field(gx, gy)

    if any(f is None for f in [forest_full, scr, eros, slr_gain]):
        print("  [WARNING] A component field is unavailable — skipping driver-change map")
        return None
    if bl_incr is None:
        print("  [WARNING] Broadleaf field unavailable (KML_BROADLEAF missing?) — "
              "rendering WITHOUT the broadleaf increment")
        bl_incr = np.zeros_like(forest_full)
        blH0 = 0.0

    # Clearfell gain: OBSERVED step × exp(-d/λ) from the FE felling polygon edge.
    fell_geom = None
    try:
        import geopandas as gpd
        gdf = gpd.read_file(str(DATA_KML_FEATURES), driver="KML").to_crs("EPSG:27700")
        name_col = gdf["Name"].fillna("").astype(str)
        for idx, row in gdf.iterrows():
            nm = name_col.iloc[idx].lower()
            if "felling" in nm or "experiment" in nm:
                fell_geom = row.geometry
                break
    except Exception:
        fell_geom = None

    clearfell_gain = np.zeros_like(forest_full)
    if fell_geom is not None and fLam is not None:
        d_fell = np.array([fell_geom.distance(Point(x, y))
                           for x, y in zip(gx.ravel(), gy.ravel())]
                          ).reshape(gx.shape)
        clearfell_gain = clearfell_mm * np.exp(-d_fell / fLam)

    scr_rise = _scrape_rise_field(gx, gy, epochs=None)   # +H0 at rise-zone pixels
    scr_draw = np.where(np.isnan(scr), 0.0, scr)         # drawdown only
    net = (slr_gain + clearfell_gain + scr_rise
           - bl_incr - eros - scr_draw)

    site_poly = load_site_polygon()
    if site_poly is not None:
        try:
            inside = contains_xy(site_poly,
                                 gx.ravel(), gy.ravel()).reshape(gx.shape)
            net = np.where(inside, net, np.nan)
        except Exception:
            pass

    return dict(net=net, forest_geom=forest_geom, fell_geom=fell_geom,
                bl_geom=bl_geom, scr_geom=scr_geom,
                clearfell_mm=clearfell_mm, blH0=blH0, eH0=eH0, slr_mm=slr_mm,
                coast_years=coast_years)


def _render_driver_change(wt, d, out_path, dpi, log_scale):
    """Render a driver-change net field `d` (from _driver_change_net) to
    `out_path`. log_scale=False → linear BoundaryNorm ±150 (the 5-yr map);
    log_scale=True → symmetric-log SymLogNorm (the 20-yr map), so the deep
    coastal field and the shallower management effects both read on one scale."""
    from matplotlib.colors import (BoundaryNorm, ListedColormap as _LC,
                                    SymLogNorm, LinearSegmentedColormap as _LSC)
    import matplotlib.patheffects as _pe
    import matplotlib.patches as mpatches

    net = d["net"]
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    LOSS_COLS = ["#c2410c", "#ea7317", "#f59e0b", "#fbbf24",
                 "#fcd34d", "#fde68a", "#fff3b0"]
    GAIN_COLS = ["#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa",
                 "#3b82f6", "#2563eb", "#1d4ed8"]

    fig, ax = plt.subplots(figsize=(9, 10), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)

    if not log_scale:
        # Linear diverging scale (5-yr map) — banded ±150.
        NET_LEVELS  = [-150, -100, -50, -25, -10, -5, -2, 2, 5, 10, 25, 50, 100, 150]
        net_cmap  = _LC(LOSS_COLS + GAIN_COLS)
        net_norm  = BoundaryNorm(NET_LEVELS, ncolors=len(LOSS_COLS + GAIN_COLS))
        cf = ax.contourf(gx, gy, net, levels=NET_LEVELS,
                         cmap=net_cmap, norm=net_norm,
                         alpha=0.68, zorder=3, extend="both")
        cbar_ticks = NET_LEVELS
        LINE_LEVELS = [-50, -25, -10, -5, 5, 10, 25, 50]
        LABEL_LEVELS = LINE_LEVELS   # linear map: label every contour
        LABEL_MANUAL = False
    else:
        # Symmetric-log diverging scale (20-yr map). Loss side runs WHITE at 0
        # → yellow (shallow loss) → RED (deep loss at the coastal toe); gain
        # side WHITE → blue. The LinearSegmentedColormap list runs
        # from position 0.0 (vmin = −600, deepest loss) to 1.0 (+600, gain), so
        # the deepest-loss colour (red) must come FIRST. This gives the
        # conventional heat-map reading — the drying coast is red, the near-zero
        # east is pale — with linear response within ±linthresh then log either
        # side so the deep coastal field and the shallower management effects
        # both read without saturation.
        LOSS_RAMP = ["#7a0403", "#c2410c", "#ea7317", "#f59e0b",
                     "#fbbf24", "#fde68a", "#fff8e1"]   # deep red → pale (loss)
        GAIN_RAMP = ["#eaf2fb", "#bfdbfe", "#93c5fd", "#60a5fa",
                     "#3b82f6", "#2563eb", "#1d4ed8"]   # pale → deep blue (gain)
        cont_cols = LOSS_RAMP + ["#ffffff"] + GAIN_RAMP
        net_cmap  = _LSC.from_list("driverdiv", cont_cols)
        vmax = 600.0
        net_norm  = SymLogNorm(linthresh=2.0, vmin=-vmax, vmax=vmax, base=10)
        cf = ax.pcolormesh(gx, gy, net, cmap=net_cmap, norm=net_norm,
                           shading="auto", alpha=0.72, zorder=3)
        cbar_ticks = [-500, -250, -100, -50, -25, -10, -5, 0,
                      5, 10, 25, 50, 100]
        LINE_LEVELS = [-500, -250, -100, -50, -25, -10, 10, 50, 100]
        # Log map: label the interior/mid-range contours (−100…−10, +10…+100)
        # plus one −500 for the coastal depth; drop −250 (collided with the forest
        # boundary). The loss contours bunch toward the coast and the SW gain
        # cluster, so auto-placement puts every label there — instead we
        # hand-place each label at an INTERIOR point on its own contour (computed
        # from the contour geometry below) so the body of the warren is labelled.
        LABEL_LEVELS = [-500, -100, -50, -25, -10, 10, 50, 100]
        LABEL_MANUAL = True

    ax.contour(gx, gy, net, levels=[0],
               colors=["#1a1a1a"], linewidths=1.4, zorder=4)
    cs = ax.contour(gx, gy, net, levels=LINE_LEVELS,
                    colors=["#5a3a00" if v < 0 else "#1e3a8a" for v in LINE_LEVELS],
                    linewidths=0.55, alpha=0.75, zorder=4)

    manual_pts = None
    if LABEL_MANUAL:
        # For each labelled level, pick an anchor point in the warren interior
        # (loss levels: central E-band 242000–243100; the −500 toe kept low/west;
        # gain levels: the SW management cluster). Falls back to the contour's
        # median vertex if no interior vertex exists.
        manual_pts = []
        for lev in LABEL_LEVELS:
            try:
                idx = list(cs.levels).index(lev)
                segs = cs.allsegs[idx]
            except (ValueError, IndexError):
                segs = []
            pts = np.vstack(segs) if segs else np.empty((0, 2))
            if not len(pts):
                continue
            if lev == -500:
                m = pts[:, 1] < 363400
            elif lev > 0:
                m = (pts[:, 0] > 241000) & (pts[:, 0] < 242000)
            else:
                m = ((pts[:, 0] > 242000) & (pts[:, 0] < 243100)
                     & (pts[:, 1] > 363000) & (pts[:, 1] < 364400))
            ip = pts[m] if m.any() else pts
            manual_pts.append(tuple(ip[len(ip) // 2]))

    _label_colors = ["#5a3a00" if v < 0 else "#1e3a8a" for v in LABEL_LEVELS]
    if manual_pts:
        # With manual placement each point labels its nearest contour; the points
        # were computed on the target contours, so do NOT also pass levels=
        # (matplotlib mis-indexes when both manual and levels are given).
        labs = ax.clabel(cs, inline=True, fontsize=7, fmt="%+d",
                         manual=manual_pts)
    else:
        labs = ax.clabel(cs, levels=LABEL_LEVELS, inline=True, fontsize=7,
                         fmt="%+d", colors=_label_colors)
    for t in labs:
        t.set_path_effects([_pe.withStroke(linewidth=1.8, foreground="white")])

    ax.scatter(wt["E"], wt["N"], c="#333", s=6, alpha=0.4, zorder=5)

    if d["forest_geom"] is not None:
        for poly in (d["forest_geom"].geoms
                     if d["forest_geom"].geom_type.startswith("Multi") else [d["forest_geom"]]):
            ax.plot(*poly.exterior.xy, color="#1b5e20", lw=1.6, ls="--", zorder=6)
    if d["fell_geom"] is not None:
        for poly in (d["fell_geom"].geoms
                     if d["fell_geom"].geom_type.startswith("Multi") else [d["fell_geom"]]):
            ax.plot(*poly.exterior.xy, color="darkorange", lw=1.8, ls="-.", zorder=6)
    if d["bl_geom"] is not None:
        for poly in (d["bl_geom"].geoms
                     if d["bl_geom"].geom_type.startswith("Multi") else [d["bl_geom"]]):
            ax.plot(*poly.exterior.xy, color="#6b3fa0", lw=1.8, ls="-", zorder=6)
    if d["scr_geom"] is not None:
        _overlay_scrape_rise(ax, d["scr_geom"], zbase=7)

    add_en_axes(ax)
    yrs = d["coast_years"]
    coast_lbl = f"{yrs:.0f}-yr chronic coastal drawdown"
    scale_note = "  ·  log colour scale" if log_scale else ""
    ax.set_title(
        f"Newborough Warren — MODELLED driver change, 2005 → 2025{scale_note}\n"
        f"Clearfell gain · Broadleaf restock · Dune scrapes · {coast_lbl} · SLR",
        fontsize=12, fontweight="bold", pad=8)

    cbar = fig.colorbar(cf, ax=ax, orientation="vertical",
                        fraction=0.035, pad=0.02, shrink=0.75, aspect=30,
                        ticks=cbar_ticks, extend="both")
    scale_word = "log" if log_scale else "linear"
    cbar.set_label(f"Modelled water-table change 2005→2025 (mm, {scale_word})"
                   "  ·  blue = gain, brown = loss", fontsize=9)
    cbar.ax.axhline(0, color="black", lw=1.2)

    legend_items = [
        mpatches.Patch(facecolor="none", edgecolor="#1b5e20",
                       lw=1.6, ls="--", label="Forest boundary (pine, unchanged → cancels)"),
        mpatches.Patch(facecolor="none", edgecolor="darkorange",
                       lw=1.8, ls="-.", label="Clearfell zone (gain, canopy removed)"),
        mpatches.Patch(facecolor="none", edgecolor="#6b3fa0",
                       lw=1.8, ls="-", label="Broadleaf restock (loss, canopy added)"),
        mpatches.Patch(facecolor="#4a90d9", alpha=0.6, edgecolor="#0d2b4a",
                       lw=1.2, label="Scrape rise zone (level rose)"),
    ]
    ax.legend(handles=legend_items, loc="lower left",
              fontsize=8, framealpha=0.85, edgecolor="#999")

    # Provenance / caveat box (top-left, over hillshade — not over the IDW field).
    horizon_note = ("prediction surface — per-well test pending"
                    if log_scale else "companion to the observed Script 36 map")
    ax.text(
        0.015, 0.985,
        f"MODELLED epoch difference — standing pine cancels.\n"
        f"Clearfell OBSERVED +{d['clearfell_mm']:.0f} mm (BACI) · SLR = +{d['slr_mm']:.0f} mm\n"
        f"Broadleaf increment ≈ {d['blH0']:.0f} mm (indicative);\n"
        f"coastal = {yrs:.0f}-yr chronic ({yrs:.0f} × δ₀ ≈ {d['eH0']:.0f} mm).\n"
        f"Fields linearly superposed (first-order upper bound in\n"
        f"overlap zones). {horizon_note}.",
        transform=ax.transAxes, ha="left", va="top",
        fontsize=7.2, color="#333", style="italic", zorder=8,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f4f4f4",
                  edgecolor="#bbb", alpha=0.92),
    )

    render_figure(fig, out_path)
    plt.close(fig)
    print(f"  Saved → {out_path}  "
          f"(range {np.nanmin(net):.0f} to {np.nanmax(net):.0f} mm; "
          f"coastal {yrs:.0f}-yr; clearfell +{d['clearfell_mm']:.0f} mm)")


def plot_driver_change_2005_2025(wt, features, dpi=300):
    """Modelled 2005→2025 driver-change map at the 5-yr chronic coastal horizon
    (COAST_CHRONIC_YEARS), linear ±150 colour scale. Companion to the observed
    Script 36 climate-removed map. Clearfell plots the OBSERVED +120 mm BACI
    step (Path B). See _driver_change_net / _render_driver_change."""
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    clearfell_mm = _load_clearfell_observed_mm()
    d = _driver_change_net(gx, gy, coast_years=COAST_CHRONIC_YEARS,
                           clearfell_mm=clearfell_mm)
    if d is None:
        return
    _render_driver_change(wt, d, OUT_20_DRIVER_CHANGE, dpi, log_scale=False)


def plot_driver_change_20yr(wt, features, dpi=300):
    """Modelled 2005→2025 driver-change map at the FULL 20-year coastal horizon
    (coastal toe = MECHANISM_HORIZON_YEARS × δ₀, with δ₀ read live from the
    Script 25 panel fit), on a symmetric-LOG colour scale so the deep coastal
    field and the shallower management effects both read.

    This is a PREDICTION-SURFACE / diagnostic figure: at each well it predicts a
    2005→2025 drawdown that can be tested against the observed record (per-well
    validation is a separate analysis). Presented ALONGSIDE the 5-yr map — the
    5-yr map compares drivers legibly; the 20-yr map shows the full accumulated
    coastal effect over the study window. Clearfell plots the OBSERVED +120 mm
    (Path B). Linear superposition — a first-order upper bound in overlap zones."""
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    clearfell_mm = _load_clearfell_observed_mm()
    d = _driver_change_net(gx, gy, coast_years=20.0, clearfell_mm=clearfell_mm)
    if d is None:
        return
    _render_driver_change(wt, d, OUT_20_DRIVER_CHANGE_20YR, dpi, log_scale=True)


def plot_scrape_drawdown(wt, features, dpi=300, show_head=True):
    """
    Illustrative scenario — steady-state drawdown propagation from all
    mapped dune-scrapes, each treated as a topographic DRAIN.

    Companion/sibling to plot_drawdown_propagation() (Fig 3). Same leaky-aquifer
    decay length λ = √(K·b/(Sy·β₃)) with Sy, β₃ read live from C3, but:
      * the source geometry is the real GPS-traced footprint of each registered
        cut (data/*.kml via _scrape_registry()), falling back to a rotated
        rectangle (SCRAPE_* constants) only if no traced footprint is found;
      * per-cut fields are superposed with the method of images across the OS
        High Water Mark coastline, enforcing zero drawdown at the fixed-head
        sea boundary;
      * edge magnitude H0 per cut is the MEASURED BACI response (Script 09a,
        Pure_Scraping era vs local control) for the three monitored cuts
        (CEH36, CEH18, CEH21), and assumed equal to the CEH36 value for the
        remaining unmonitored cuts. H0 is the empirical input; the excavation
        depth is the derived, NOT-surveyed output (D_inferred = H0 / Sy,
        printed for reference only) — see _measured_ceh36_response() and the
        v1.10.0 changelog entry above, which anchored H0 on the response and
        removed the earlier Sy × assumed-depth heuristic from the provenance.

    Layers mirror Fig 3 (hillshade, optional head surface, filled/line drawdown
    contours, cluster-coloured wells) plus the scrape polygon(s) and centre
    marker(s). Scrape interiors are masked (the slack itself rises — Section
    5.4.1 — so only the surrounding drawdown, the dipole counterpart, is
    shown). The grid is clipped to the site outline.
    """
    from heapq import heappush, heappop
    import geopandas as gpd
    import fiona
    import rasterio
    from shapely.geometry import Point, box
    from shapely.affinity import rotate as shp_rotate
    from shapely.prepared import prep

    fiona.drvsupport.supported_drivers["KML"] = "rw"

    # ── Parameters (λ identical basis to Fig 3; C3 propagation medium) ─────
    K = DRAWDOWN_K_MDAY            # m/day (Betson 2002), shared with drawdown/SLR maps
    b = DRAWDOWN_B_M            # m saturated thickness

    _sy_df   = pd.read_csv(OUT_18_WELL_SY_TABLE)
    Sy       = float(_sy_df[_sy_df['Cluster'] == 3]['Sy_median'].median())
    # Edge drawdown = the MEASURED CEH36 response (Script 09a), an empirical
    # quantity. The excavation depth (not surveyed) is the inferred output:
    # D = H0 / Sy.
    H0_m       = _measured_ceh36_response()      # m, live Script 09a CEH36 Pure_Scraping
    H0         = H0_m * 1000.0                    # mm
    D_inferred = H0_m / Sy                        # m, inferred cut depth
    _mech_df = pd.read_csv(OUT_03_MECHANISTIC_TABLE)
    BETA3_M  = float(_mech_df[_mech_df['Cluster'] == 3]['beta_3_drainage'].iloc[0])
    BETA3_D  = BETA3_M / 30.0
    lam      = np.sqrt((K * b) / (Sy * BETA3_D))
    OUT_PATH = OUT_20_SCRAPE_DRAWDOWN if show_head else OUT_20_SCRAPE_DRAWDOWN_NOHEAD

    print(f"  λ = {quote_reach_m(lam):.0f} m  (K={K}, Sy={Sy:.4f} [C3 WTF], "
          f"b={b}, β₃={BETA3_M:.4f}/month [C3 SSM]);  "
          f"H0 = {H0:.0f} mm (measured CEH36 response) → inferred cut {D_inferred:.2f} m")

    # ── Scrape footprint: real GPS-traced outline (data/ceh36_scrape.kml),
    #    reprojected to OSGB36; fall back to the constructed box if absent ──
    scrape_geom = _load_real_scrape_geom()
    if scrape_geom is None:
        base = box(SCRAPE_CENTRE_E - SCRAPE_SHORT_M / 2.0,
                   SCRAPE_CENTRE_N - SCRAPE_LONG_M / 2.0,
                   SCRAPE_CENTRE_E + SCRAPE_SHORT_M / 2.0,
                   SCRAPE_CENTRE_N + SCRAPE_LONG_M / 2.0)
        # shapely rotates CCW-positive; bearing is CW from N, so negate.
        scrape_geom = shp_rotate(base, -SCRAPE_BEARING_DEG, origin="center")
    scrape_prep = prep(scrape_geom)
    SCR_AREA_HA = scrape_geom.area / 1e4

    # ── Load DEM and build flow-weighted distance grid (as Fig 3) ─────────
    with rasterio.open(str(DATA_DEM)) as src:
        dem_full = src.read(1).astype(float)
        t = src.transform
        res = abs(t.a)
        if src.nodata is not None:
            dem_full[dem_full == src.nodata] = np.nan

    E_MIN, E_MAX = XLIM[0] + 100, XLIM[1] - 400
    N_MIN, N_MAX = YLIM[0] + 200, YLIM[1] + 200
    col0 = int((E_MIN - t.c) / t.a)
    col1 = int((E_MAX - t.c) / t.a)
    row0 = int((t.f - N_MAX) / abs(t.e))
    row1 = int((t.f - N_MIN) / abs(t.e))
    dem = dem_full[row0:row1, col0:col1]

    ds = 5  # downsample to 10 m
    dem_ds = dem[::ds, ::ds]
    nr, nc = dem_ds.shape
    cell = res * ds
    e_arr = t.c + (col0 + np.arange(nc) * ds) * t.a
    n_arr = t.f + (row0 + np.arange(nr) * ds) * t.e

    # ── Per-cut leaky-aquifer drawdown: superposition with method-of-images ─
    # Each mapped cut is a permanent co-active drain at edge magnitude H0_i
    # (measured BACI for CEH36/18/21, assumed = CEH36 for Feb-2013/A/B).
    # The coast is a fixed-head boundary (h = 0); the image term enforces this:
    #   dd(x,y) = Σ_i H0_i · [exp(-d_real_i/λ) − exp(-d_image_i/λ)]
    # where d_image_i is distance to the mirror of cut i across the HWM coast.
    from scipy.spatial import cKDTree

    def _cut_trees_with_images(coastline):
        """Return list of (real_tree, image_tree, H0) for each registered cut."""
        out = []
        for s in _scrape_registry():
            g = s["geom"]
            g = g.segmentize(5.0) if hasattr(g, "segmentize") else g
            bnd = []
            for gg in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
                xs, ys = gg.exterior.xy
                bnd.append(np.column_stack([np.asarray(xs), np.asarray(ys)]))
            real_tree = cKDTree(np.vstack(bnd))
            if coastline is not None:
                img_g = _reflect_across_coastline(g, coastline)
                img_g = img_g.segmentize(5.0) if hasattr(img_g, "segmentize") else img_g
                ibnd = []
                for gg in (img_g.geoms if img_g.geom_type == "MultiPolygon" else [img_g]):
                    xs, ys = gg.exterior.xy
                    ibnd.append(np.column_stack([np.asarray(xs), np.asarray(ys)]))
                img_tree = cKDTree(np.vstack(ibnd))
            else:
                img_tree = None
            out.append((real_tree, img_tree, s["H0"]))
        return out

    coastline = _load_coastline_hwm()
    _trees = _cut_trees_with_images(coastline)
    _EE, _NN = np.meshgrid(e_arr, n_arr)
    _gpts = np.column_stack([_EE.ravel(), _NN.ravel()])
    _env = np.zeros(_gpts.shape[0])
    for real_tree, img_tree, h0 in _trees:
        d_real, _ = real_tree.query(_gpts)
        if img_tree is not None:
            d_image, _ = img_tree.query(_gpts)
            _env += h0 * (np.exp(-d_real / lam) - np.exp(-d_image / lam))
        else:
            _env += h0 * np.exp(-d_real / lam)   # unbounded fallback
    _env = np.maximum(_env, 0.0)   # image term can go slightly negative near coast
    dd_grid = _env.reshape(_EE.shape)

    # ── Head surface and GW flow vectors (as Fig 3) ───────────────────────
    gx, gy = np.meshgrid(GRID_XI, GRID_YI)
    mask = _site_mask(gx, gy)
    sea_pts, sea_vals = _sea_boundary_points()
    pts  = wt[["E", "N"]].values
    vals = wt["mean_head"].values
    surf = idw_surface(pts, vals, gx, gy,
                       sea_pts=sea_pts, sea_vals=sea_vals, mask=mask)
    surf_full = idw_surface(pts, vals, gx, gy,
                            sea_pts=sea_pts, sea_vals=sea_vals, mask=None)
    hdy, hdx = np.gradient(np.nan_to_num(surf, nan=np.nanmean(vals)),
                           GRID_YI[1] - GRID_YI[0], GRID_XI[1] - GRID_XI[0])
    hmag = np.sqrt(hdx**2 + hdy**2)
    mag_thresh = np.nanpercentile(hmag[mask], 95)
    arrow_ok = mask & (hmag > 0) & (hmag < mag_thresh)
    with np.errstate(invalid="ignore"):
        U = np.where(arrow_ok, -hdx / hmag, np.nan)
        V = np.where(arrow_ok, -hdy / hmag, np.nan)

    # ── Per-well drawdown values (method-of-images superposition) ────────
    _wpts = wt[["E", "N"]].values
    _wd = np.zeros(len(wt))
    _d_near = np.full(len(wt), np.inf)
    for real_tree, img_tree, h0 in _trees:
        d_real, _ = real_tree.query(_wpts)
        _d_near = np.minimum(_d_near, d_real)
        if img_tree is not None:
            d_image, _ = img_tree.query(_wpts)
            _wd += h0 * (np.exp(-d_real / lam) - np.exp(-d_image / lam))
        else:
            _wd += h0 * np.exp(-d_real / lam)   # unbounded fallback
    _wd = np.maximum(_wd, 0.0)
    wt = wt.copy()
    wt["dd_mm"] = _wd
    wt["dist_nearest_cut_m"] = _d_near

    # ── Traceable per-well scrape drawdown ────────────────────────────────
    # This field had no committed output of any kind, so §4.9.6's "exceeds
    # 50 mm only within ~100 m of the excavation" could not be checked against
    # anything. Note it is NOT the forest geometry: the drawdown superposes one
    # source per registered cut, each with an image sink, on the EUCLIDEAN
    # distance to that cut's boundary — so no single exp(-d/λ) contour radius
    # describes it, and dist_nearest_cut_m is context, not the sole predictor.
    _sc = wt[["well", "E", "N", "dist_nearest_cut_m", "dd_mm"]].copy()
    _sc = _sc.sort_values("dist_nearest_cut_m").reset_index(drop=True)
    _sc.to_csv(OUT_20_SCRAPE_DRAWDOWN_PERWELL, index=False)
    print(f"  Saved → {OUT_20_SCRAPE_DRAWDOWN_PERWELL.name} "
          f"({len(_sc)} wells)")

    # ── Render ────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")
    load_dem_hillshade(ax, DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    ax.set_xlim(*XLIM)
    ax.set_ylim(*YLIM)
    ax.set_aspect("equal")

    im = None
    if show_head:
        im = ax.pcolormesh(gx, gy, surf_full, cmap="RdYlBu_r",
                           vmin=2.0, vmax=14.0,
                           shading="auto", alpha=0.45, zorder=2)

    E_grid, N_grid = np.meshgrid(e_arr, n_arr)
    dd_masked = dd_grid.copy()
    site_poly = load_site_polygon()
    if site_poly is not None:
        try:
            from shapely import contains_xy as _contains_xy
            inside_site = _contains_xy(site_poly,
                                       E_grid.ravel(),
                                       N_grid.ravel()).reshape(E_grid.shape)
        except Exception:
            site_prep = prep(site_poly)
            inside_site = np.zeros(dd_masked.shape, dtype=bool)
            for i in range(dd_masked.shape[0]):
                n_v = n_arr[i]
                for j in range(dd_masked.shape[1]):
                    if site_prep.contains(Point(e_arr[j], n_v)):
                        inside_site[i, j] = True
        dd_masked[~inside_site] = 0

    # Seaward truncation (shore-margin scrape only). A scrape at the coastal
    # margin draws its water from the landward side; the seaward side is the
    # sea, where the table is pinned near MSL. For an inland scrape the drain
    # draws all round, so this is skipped (SCRAPE_TRUNCATE_SEAWARD=False).
    if SCRAPE_TRUNCATE_SEAWARD:
        theta = np.deg2rad(SCRAPE_BEARING_DEG)
        iv_e, iv_n = np.sin(theta), np.cos(theta)        # inland unit vector
        proj = (E_grid - SCRAPE_CENTRE_E) * iv_e + (N_grid - SCRAPE_CENTRE_N) * iv_n
        dd_masked[proj < -max(SCRAPE_LONG_M, SCRAPE_SHORT_M) / 2.0] = 0
        dd_masked[dem_ds < SCRAPE_SEAWARD_MIN_ELEV_M] = 0

    # Rise zone: the scraped footprint and its immediate near-field RISE (the
    # slack is restored). The modelled drawdown within SCRAPE_RISE_BUFFER_M is
    # unobserved (no wells resolve it; CEH36 itself rises), so it is shown as the
    # rise zone, NOT as drawdown — this stops the scrape reading as a drawdown max.
    rise_zone = scrape_geom.buffer(SCRAPE_RISE_BUFFER_M)
    try:
        from shapely import contains_xy as _contains_xy
        in_rise = _contains_xy(rise_zone, E_grid.ravel(),
                               N_grid.ravel()).reshape(E_grid.shape)
    except Exception:
        _rp = prep(rise_zone)
        in_rise = np.zeros(E_grid.shape, dtype=bool)
        for _i in range(E_grid.shape[0]):
            for _j in range(E_grid.shape[1]):
                if _rp.contains(Point(e_arr[_j], n_arr[_i])):
                    in_rise[_i, _j] = True
    dd_masked[in_rise] = np.nan

    line_col = "midnightblue" if show_head else "#5a2a00"
    cf = None
    if not show_head:
        dd_fill = np.where(dd_masked > 0, dd_masked, np.nan)
        cf = ax.contourf(E_grid, N_grid, dd_fill, levels=DRAWDOWN_FILL_LEVELS,
                         cmap=DRAWDOWN_CMAP, alpha=DRAWDOWN_ALPHA, zorder=3,
                         extend="max")
    cs = ax.contour(E_grid, N_grid, dd_masked, levels=DRAWDOWN_LINE_LEVELS,
                    colors=line_col, linewidths=1.2, alpha=0.85, zorder=4)
    cl = ax.clabel(cs, levels=DRAWDOWN_LINE_LABELS,
                   inline=True, fontsize=10, fmt="%d mm",
                   colors="black", inline_spacing=8)
    import matplotlib.patheffects as _pe
    for txt in cl:
        txt.set_fontweight("bold")
        txt.set_bbox(None)                            # transparent label background
        txt.set_path_effects([_pe.withStroke(linewidth=2.4, foreground="white")])

    # (GW flow arrows removed — the map now shows drawdown contours only.)

    kml_handles = draw_kml_features(ax, features, zorder=6)

    # Scrape footprint = a RISE (slack restoration), NOT drawdown. Render the
    # rise zone in blue and the excavation outline(s) boldly; annotate clearly.
    def _geoms(g):
        return list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    for _rz in _geoms(rise_zone):
        rzx, rzy = _rz.exterior.xy
        ax.fill(rzx, rzy, facecolor="#4a90d9", alpha=0.40, zorder=7)
        ax.plot(rzx, rzy, color="#1a4e80", lw=1.0, ls=":", zorder=7)
    for _sp in _geoms(scrape_geom):
        sx, sy = _sp.exterior.xy
        ax.fill(sx, sy, facecolor="#1a4e80", alpha=0.85, zorder=8)
        ax.plot(sx, sy, color="#0d2b4a", lw=1.6, zorder=9)
    n_lobes = len(_geoms(scrape_geom))
    _h0_ceh36 = round(_measured_ceh36_response() * 1000)   # live BACI (CEH36 Pure_Scraping) → 129 mm
    ax.text(
        0.985, 0.985,
        "Scrape footprints (%d cuts, %.2f ha total, mapped outlines)\n"
        "cut slacks ROSE (slack restored — not drawn down)\n"
        "H₀: CEH36 +%d · CEH21 +74 · CEH18 +8 mm measured; others assumed = CEH36"
        % (n_lobes, SCR_AREA_HA, _h0_ceh36),
        transform=ax.transAxes, ha="right", va="top",
        fontsize=7.6, fontweight="bold", color="#0d2b4a", zorder=11,
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#1a4e80", alpha=0.93))

    cluster_handles = {}
    for _, row in wt.iterrows():
        cl_ = int(row["cluster"]) if pd.notna(row.get("cluster")) else 3
        col = CLUSTER_COLOURS.get(cl_, "grey")
        ax.scatter(row["E"], row["N"], c=col, s=30,
                   edgecolors="black", lw=0.6, zorder=9)
        if cl_ not in cluster_handles:
            cluster_handles[cl_] = mpatches.Patch(color=col, label=f"C{cl_}")

    # (Per-well drawdown labels removed for clarity — the scraped area and the
    # filled contours carry the read; wells remain as cluster-coloured markers.)

    ref_e, ref_n = 241805, 364349
    ax.annotate("", xy=(ref_e + lam, ref_n - 100),
                xytext=(ref_e, ref_n - 100),
                arrowprops=dict(arrowstyle="<->", color="#d62728", lw=1.5),
                zorder=10)
    ax.text(ref_e + lam / 2, ref_n - 200, f"λ = {quote_reach_m(lam):.0f} m",
            ha="center", va="top", fontsize=9, fontweight="bold",
            color="#d62728", zorder=10,
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=2))

    if show_head and im is not None:
        cb_head = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04, shrink=0.85)
        cb_head.set_label("Mean water table (m AOD)", fontsize=9)
    elif (not show_head) and cf is not None:
        cb = fig.colorbar(cf, ax=ax, fraction=0.03, pad=0.04, shrink=0.85)
        cb.set_label("Scrape drawdown (mm)", fontsize=9)

    scrape_h = mpatches.Patch(facecolor="#4a90d9", alpha=0.6,
                              label="Scrape rise zone (level rose)")
    l1 = ax.legend(handles=kml_handles + [scrape_h],
                   fontsize=7, loc="lower left", framealpha=0.92,
                   title="Site features", title_fontsize=8)
    ax.add_artist(l1)
    ax.legend(handles=list(cluster_handles.values()),
              fontsize=8, loc="lower right",
              title="Cluster", title_fontsize=8, framealpha=0.92)

    ax.set_xlabel("Easting (m, OSGB36)", fontsize=9)
    ax.set_ylabel("Northing (m, OSGB36)", fontsize=9)
    ax.set_title(
        "Scrape-drain drawdown — surrounding water table only\n"
        + f"mapped scrape footprints {SCR_AREA_HA:.2f} ha total · {SCRAPE_TIMESCALE} · "
        + ("drain, landward-truncated · " if SCRAPE_TRUNCATE_SEAWARD else "drain · ")
        + f"λ = {quote_reach_m(lam):.0f} m\n"
        + "cut slacks RISE (not drawn down); per-cut cones — H₀ measured at CEH36/18/21, assumed = CEH36 elsewhere (modelled reach, not resolved in the network)",
        fontsize=9.5, fontweight="bold", pad=10)

    plt.tight_layout()
    render_figure(fig, OUT_PATH)
    plt.close(fig)
    print(f"  Saved → {OUT_PATH}")


def main(preview=False):
    dpi = 150 if preview else 300
    make_all_dirs()
    DIR_20.mkdir(parents=True, exist_ok=True)

    print("\n=== 20_spatial_figures.py ===")
    print(f"  DPI: {dpi}  ({'preview' if preview else 'publication'})")

    print("\n[1/4] Loading data...")
    data = load_data()

    print("[2/4] Building well table...")
    wt, P_bar, PET_bar = build_well_table(data)
    print(f"  Wells: {len(wt)}  "
          f"(residual available for {wt['residual_wb'].notna().sum()})")
    print(f"  P̄ = {P_bar*1000:.1f} mm/month  "
          f"PET̄ = {PET_bar*1000:.1f} mm/month  "
          f"(averaged over the head record, "
          f"{data['maod'].index.min():%Y-%m} to {data['maod'].index.max():%Y-%m})")

    print("[3/4] Loading stream polygons...")
    stream_polys = load_stream_polygons()

    print("[4/4] Loading KML features...")
    features = load_kml_features()
    print(f"  KML features: {len(features)}")

    print("\nGenerating Figure 1 — Head surface + stream network...")
    plot_head_streams(wt, stream_polys, features, dpi=dpi)

    print("Generating Figure 2a — SSM water balance residual...")
    plot_residual_ssm(wt, features, dpi=dpi)

    print("Generating Figure 2b — Ridge hillslope gradient...")
    plot_slope_gradient(wt, features, dpi=dpi)

    print("Generating Figure 3 — Forest drawdown propagation...")
    plot_drawdown_propagation(wt, features, dpi=dpi, show_head=False)

    print("Generating Figure 4 — Coastal-erosion drawdown...")
    plot_coastal_erosion(wt, features, dpi=dpi)

    print("Generating Figure 5 — Sea-level-rise head response...")
    plot_slr_response(wt, features, dpi=dpi)

    print("Generating Figure 6 — Net coastal head change (SLR − erosion)...")
    plot_coastal_net_effect(wt, features, dpi=dpi)

    print("Generating Figure 7 — Scrape-drain drawdown...")
    plot_scrape_drawdown(wt, features, dpi=dpi, show_head=False)

    print("Generating clearfell-baseline drawdown map (scrape + Storm Brendan)...")
    plot_scrape_coastal_net(wt, features, dpi=dpi)

    print("Generating public-summary three-driver panel...")
    plot_public_panel(wt, features, dpi=dpi)

    print("Generating MSL5 change map (window end 2017 vs 2023)...")
    plot_msl5_change(wt, features, dpi=dpi)

    print("Generating observed water-table change map (2012–2015 vs 2024–2026)...")
    plot_observed_change(wt, features, dpi=dpi)

    print("Generating net water-table state map (all five drivers)...")
    plot_net_state_map(wt, features, dpi=dpi)

    print("Generating 2005→2025 modelled driver-change map (5-yr chronic coastal)...")
    plot_driver_change_2005_2025(wt, features, dpi=dpi)

    print("Generating 2005→2025 driver-change map (20-yr coastal, log scale)...")
    plot_driver_change_20yr(wt, features, dpi=dpi)

    print("Generating clearfell gain map...")
    plot_clearfell_gain(wt, features, dpi=dpi)

    print("\n=== Script 20 complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script 20 — Spatial figures for paper Section 4.9")
    parser.add_argument("--preview", action="store_true",
                        help="Render at 150 dpi for quick preview")
    args = parser.parse_args()
    main(preview=args.preview)
