"""
utils/config.py
Shared constants for cluster colours, labels, and DEM rendering scale.
All scripts import from here so that palette and scale changes propagate everywhere.

The current partition is k=5 (see 02_clustering.py CLUSTER_PARTITIONING_CONFIG
docstring for the rationale). CLUSTER_COLOURS and CLUSTER_MARKERS keep a C6
entry reserved for future extension, but CLUSTER_LABELS is authoritative for
which cluster IDs are currently in use — downstream code that needs to iterate
over "all clusters" should iterate over CLUSTER_LABELS.keys().
"""

# ── Journal B&W mode ─────────────────────────────────────────────────────────
# Toggle to produce journal-ready greyscale figures.
# When True, scripts use CLUSTER_COLOURS_BW, apply BW_HATCHES to bar charts,
# use BW_LINESTYLES for multi-series line plots, and call load_dem_auto()
# (which routes to hillshade) for map basemaps.
#
# Can be activated three ways:
#   1. Set BW_MODE = True here (permanent)
#   2. Set environment variable NRG_BW_MODE=1 before running (temporary)
#   3. Use run_analysis.py menu option 6 or --greyscale (sets env var)
import os as _os
BW_MODE = _os.environ.get("NRG_BW_MODE", "").strip().lower() in ("1", "true", "yes")
if BW_MODE:
    print("  [config.py] BW_MODE=True (NRG_BW_MODE env var detected)")

CLUSTER_COLOURS = {
    1: "#1a6faf",   # C1 Lake — old C1 blue
    2: "#2ca02c",   # C2 Dune — old C2 green
    3: "#d62728",   # C3 Western Residual — old C3 red
    4: "#7f77dd",   # C4 Main Forest — old C4 purple
    5: "#8B4513",   # C5 Coastal Forest — brown (saddlebrown)
    6: "#0072B2",   # reserved
}

# Greyscale equivalents — chosen for maximum perceptual separation.
# These map to luminance values spaced ~40 units apart on a 0–255 scale,
# ensuring distinguishability even when printed on a low-quality laser.
CLUSTER_COLOURS_BW = {
    1: "#2a2a2a",   # C1 — near-black (L ≈ 42)
    2: "#808080",   # C2 — mid-grey   (L ≈ 128)
    3: "#b8b8b8",   # C3 — light grey (L ≈ 184)
    4: "#545454",   # C4 — dark grey  (L ≈ 84)
    5: "#a0a0a0",   # C5 — grey       (L ≈ 160)
    6: "#d0d0d0",   # reserved
}

# Bar chart hatching patterns — used when BW_MODE is True.
# Index by cluster ID or by series index for non-cluster bar charts.
BW_HATCHES = {
    1: "",       # C1 — solid fill (no hatch)
    2: "///",    # C2 — diagonal lines
    3: "...",    # C3 — dots
    4: "xxx",    # C4 — crosses
    5: "\\\\\\",   # C5 — back-diagonal
    6: "+++",    # reserved
}

# General-purpose bar hatches for non-cluster series (e.g. P vs PET,
# climate vs forest management scenarios).
BW_BAR_HATCHES = ["", "///", "...", "xxx", "\\\\\\", "+++", "---", "ooo"]

# Line styles for multi-series plots — cycle through these when BW_MODE
# is True so lines are distinguishable without colour.
BW_LINESTYLES = [
    {"linestyle": "-",  "linewidth": 2.0},   # solid thick
    {"linestyle": "--", "linewidth": 1.8},   # dashed
    {"linestyle": ":",  "linewidth": 2.0},   # dotted
    {"linestyle": "-.", "linewidth": 1.8},   # dash-dot
    {"linestyle": (0, (5, 1)), "linewidth": 2.0},  # dense dash
    {"linestyle": (0, (3, 1, 1, 1)), "linewidth": 1.8},  # dash-dot-dot
]

# Greyscale line tones — pair with BW_LINESTYLES for maximum contrast.
# Darker lines for primary series, lighter for secondary/reference.
BW_LINE_COLOURS = ["#000000", "#555555", "#888888", "#333333", "#aaaaaa", "#666666"]

CLUSTER_LABELS = {
    1: "C1 (Lake Edge)",
    2: "C2 (Dune)",
    3: "C3 (Western Residual)",
    4: "C4 (Main Forest)",
    5: "C5 (Coastal Forest)",
}

# SSM displacement reference datum. The state-space model fits β₃ on
# displacement above this depth (h_disp = DRAINAGE_DATUM + h_depth, where
# h_depth is negative-convention depth below ground surface). β₃ > 0 then
# means "higher head above the drainage base drives faster drainage" —
# Darcy-consistent.
#
# Value selected by sensitivity analysis (Script 03, output 03_08): 3.7 m
# is the minimum reference depth at which all five clusters produce positive
# AND significant (p < 0.05) β₃. See HANDOVER_SCRIPT03_DATUM.md.
DRAINAGE_DATUM = 3.7  # metres below ground surface

# Headline rainfall lag applied in the SSM and all per-well OLS regressions.
# All scripts import this value rather than defining their own copy.
#
# History: originally set to 1 to compensate for a bucketing convention that
# assigned end-of-month / start-of-next-month field readings to the FOLLOWING
# calendar month (e.g. a reading on 01/09 representing August's water level
# was bucketed to September). With lag-1 rainfall, September's model row used
# August's rainfall — giving the correct physical pairing despite the
# mislabelled month.
#
# After fixing the bucketing in Script 01 (day ≤ 15 → previous month), the
# well data is correctly labelled and lag-0 gives the same physical pairing.
# All regression coefficients are numerically identical.
HEADLINE_LAG = 0

# Canopy interception fraction for Corsican pine (Freeman, 2008).
# Measured at C5 (Coastal Forest) throughfall gauge, applied to all
# forested clusters (C4 and C5). The interception is a partition of the
# PET energy budget: ET_at_WT = PET − I, so I is NOT additive to PET.
# See INTERCEPTION_TREATMENT.md for the full derivation.
FOREST_INTERCEPTION = 0.24

# Cluster IDs carrying forest canopy (Corsican pine). These receive the
# interception correction in water-balance, WTF, and scenario scripts.
# Under k=5: C4 (Main Forest) and C5 (Coastal Forest).
FOREST_CIDS = (4, 5)

CLUSTER_MARKERS = {
    1: "o",
    2: "s",
    3: "^",
    4: "D",
    5: "P",
    6: "*",  # reserved
}

# Shared recency cutoff used for reference-network selection across scripts.
REFERENCE_CUTOFF_DATE = "2026-02-01"

# ── Site geography ────────────────────────────────────────────────────────────
# RAF Valley climate station, Anglesey — latitude for Thornthwaite day-length
# correction. Confirmed 53°14′32″N → 53.242° ≈ 53.25.
RAF_VALLEY_LAT_DEG = 53.25

# ── Ecological thresholds — Curreli et al. (2013) ────────────────────────────
# Dune slack community viability limits, expressed as depth below ground
# surface (m, positive downward). Applied in threshold forecasting (11, 11b),
# climate projections (14), spatial viewer (19), and forestry scenarios (21).
SD15b     = 0.61   # m — wet slack viability
SD15b_REC = 0.75   # m — wet slack recovery / excavation limit
SD16      = 0.98   # m — dry slack threshold
SD16_REC  = 1.20   # m — dry slack recovery / excavation limit

# Winter thresholds used in climate projections (negative = below ground
# in the sign convention of Script 14's depth axis).
SD15b_WINTER = 0.10  # m — winter flooding limit for wet slack
SD16_WINTER  = 0.25  # m — winter flooding limit for dry slack

# ── Broadleaf interception ────────────────────────────────────────────────────
# Deciduous annual-mean interception fraction — Komatsu et al. (2011).
# Approximates summer (~25 %, leafed) and winter (~0 %, leafless) averaged
# over the year. Used in replanting scenarios (scripts 19, 21).
BROADLEAF_INTERCEPTION = 0.15

# Broadleaf summer β₂ multiplier — deciduous phenology effect on ET.
# Derived from Script 21's monthly β₂ profile (Hollingham, 2026):
#   Jun=1.08, Jul=1.12, Aug=1.15, Sep=1.10 → summer mean = 1.1125
# In full leaf, broadleaf transpiration exceeds pine transpiration
# despite lower interception. This only applies to summer scenario bars;
# the annual-mean effect is approximately ×1.0 (seasonal pattern cancels).
BROADLEAF_B2_SUMMER = 1.1125

# Broadleaf winter β₂ multiplier — leafless dormancy reduces ET draw.
# Derived from Script 21's monthly β₂ profile (Hollingham, 2026):
#   Oct=1.02, Nov=0.92, Dec=0.87, Jan=0.85, Feb=0.85, Mar=0.88 → winter mean ≈ 0.8983
# Leafless broadleaf canopy has negligible transpiration; value < 1.0
# reflects the reduced atmospheric draw relative to evergreen pine.
BROADLEAF_B2_WINTER = 0.8983

# ── DEM colour scale ─────────────────────────────────────────────────────────
# TwoSlopeNorm anchors used across all map products
DEM_VMIN = 0.0
DEM_VCENTER = 12.0
DEM_VMAX = 35.0

# ── UKCP18 RCP8.5 Wales central estimates ────────────────────────────────────
# Seasonal precipitation and PET scaling factors for climate scenarios.
# Source: UKCP18 probabilistic projections, 50th percentile, 2050s (2040-2069),
# RCP8.5, Wales region. Applied as multipliers to the monitoring-period
# climatology in Scripts 09d, 19, and 21.
UKCP18_DRY_P_WINTER  = 1.05   # +5% winter P
UKCP18_DRY_P_SUMMER  = 0.83   # −17% summer P
UKCP18_DRY_PET_WINTER = 1.05  # +5% winter PET
UKCP18_DRY_PET_SUMMER = 1.12  # +12% summer PET
UKCP18_WET_P_WINTER  = 1.15   # +15% winter P
UKCP18_WET_P_SUMMER  = 1.10   # +10% summer P
UKCP18_WET_PET_WINTER = 0.98  # −2% winter PET
UKCP18_WET_PET_SUMMER = 0.95  # −5% summer PET


# ── BW-mode convenience functions ────────────────────────────────────────────

def get_cluster_colours():
    """Return the active cluster colour dict (colour or BW depending on mode)."""
    return CLUSTER_COLOURS_BW if BW_MODE else CLUSTER_COLOURS


def get_cluster_colour(cid: int):
    """Return the colour for a single cluster (respects BW_MODE)."""
    src = CLUSTER_COLOURS_BW if BW_MODE else CLUSTER_COLOURS
    return src.get(cid, "#888888")


def get_bar_hatch(index: int):
    """Return a bar hatching pattern for series `index` (empty string if colour mode)."""
    if not BW_MODE:
        return ""
    return BW_BAR_HATCHES[index % len(BW_BAR_HATCHES)]


def get_line_style(index: int):
    """Return a dict of linestyle + linewidth for series `index`.

    In colour mode returns a default solid line; in BW mode cycles through
    distinct dash patterns.

    Usage: ax.plot(x, y, color=..., **get_line_style(i))
    """
    if not BW_MODE:
        return {"linestyle": "-", "linewidth": 1.5}
    return BW_LINESTYLES[index % len(BW_LINESTYLES)]


def get_line_colour(index: int):
    """Return a greyscale tone for series `index` (in BW mode).

    In colour mode returns None (caller should use their own colour).
    """
    if not BW_MODE:
        return None
    return BW_LINE_COLOURS[index % len(BW_LINE_COLOURS)]


def get_cmap(colour_cmap: str, bw_cmap: str = "Greys") -> str:
    """Return the appropriate colormap name for the current mode.

    Parameters
    ----------
    colour_cmap : str
        Colormap to use in colour mode (e.g. "viridis", "RdYlGn").
    bw_cmap : str
        Colormap to use in BW mode (default "Greys" — linear light→dark).
        Use "Greys_r" for dark→light if that better matches the semantics.

    In BW mode, returns a truncated Greys colormap (light grey → black)
    so the minimum value is distinguishable from a white background.

    Usage: cmap = get_cmap("RdYlGn")
    """
    if not BW_MODE:
        return colour_cmap
    if bw_cmap == "Greys":
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap
        base = plt.cm.Greys
        # Truncate: start from 5% grey (near-white but distinguishable) to 100% black
        colours = base(_import_numpy().linspace(0.05, 1.0, 256))
        return LinearSegmentedColormap.from_list("Greys_trunc", colours)
    return bw_cmap


def _import_numpy():
    """Lazy numpy import for get_cmap."""
    import numpy as np
    return np
