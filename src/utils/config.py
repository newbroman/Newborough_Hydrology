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

CLUSTER_COLOURS = {
    1: "#1a6faf",   # C1 Lake — old C1 blue
    2: "#2ca02c",   # C2 Dune — old C2 green
    3: "#d62728",   # C3 Western Residual — old C3 red
    4: "#7f77dd",   # C4 Main Forest — old C4 purple
    5: "#8B4513",   # C5 Coastal Forest — brown (saddlebrown)
    6: "#0072B2",   # reserved
}

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

# ── DEM colour scale ─────────────────────────────────────────────────────────
# TwoSlopeNorm anchors used across all map products
DEM_VMIN = 0.0
DEM_VCENTER = 12.0
DEM_VMAX = 35.0
