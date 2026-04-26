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

# DEM colour scale — TwoSlopeNorm anchors used across all map products
DEM_VMIN = 0.0
DEM_VCENTER = 12.0
DEM_VMAX = 35.0
