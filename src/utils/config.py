"""
utils/config.py
Shared constants for cluster colours, labels, and DEM rendering scale.
All scripts import from here so that palette and scale changes propagate everywhere.
"""

CLUSTER_COLOURS = {
    1: "#E69F00",
    2: "#009E73",
    3: "#CC79A7",
    4: "#D55E00",
    5: "#56B4E9",
    6: "#0072B2",
}

CLUSTER_LABELS = {
    1: "C1 (Eastern Block Lake)",
    2: "C2 (Eastern Block Mature Dune)",
    3: "C3 (Western Block Mature Dune)",
    4: "C4 (Forest)",
    5: "C5 (Coastal)",
    6: "C6 (Lake)",
}

CLUSTER_MARKERS = {
    1: "o",
    2: "s",
    3: "^",
    4: "D",
    5: "P",
    6: "*",
}

# Shared recency cutoff used for reference-network selection across scripts.
REFERENCE_CUTOFF_DATE = "2026-02-01"

# DEM colour scale — TwoSlopeNorm anchors used across all map products
DEM_VMIN = 0.0
DEM_VCENTER = 12.0
DEM_VMAX = 35.0
