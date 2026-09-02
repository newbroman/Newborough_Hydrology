# CHANGELOG delta — cluster region overlay (KML + newborough_report.py v1.4.0)

**Date:** 2026-09-02
**New file:** `data/geo/cluster_regions.kml`
**Changed:** `living/newborough_report.py` (v1.3.0 → v1.4.0)
**Ruling:** Martin, 2026-09-02 — cluster outlines on the difference maps, drawn
as nearest-well (Voronoi) regions.

---

## Why a Voronoi partition and not a hull

The k=5 clusters are defined by **SSM coefficient behaviour, not by geography**,
and on the ground they interdigitate. C1 contains CEH11, 2.1 km from the rest of
the cluster and below lake level. Any hull — convex or concave — would therefore
draw a C1 shape stretching across wells that belong to other clusters, asserting
a spatial extent the clustering never claimed.

A nearest-well partition asserts only what is defensible: *the nearest monitored
reference well here belongs to Cn*. It leaves CEH11 as its own detached piece
(C1 comes out in two parts) rather than dragging a boundary across the reserve,
and it tiles the site exactly once with no overlaps — verified at 100.0% of the
site boundary area, 8.62 km².

| Region | Area | Parts | Wells |
|---|---|---|---|
| C1 Lake Edge | 1.42 km² | **2** | 7 |
| C2 Dune | 2.80 km² | 1 | 24 |
| C3 Western Residual | 2.06 km² | 1 | 21 |
| C4 Main Forest | 1.63 km² | 1 | 9 |
| C5 Coastal Forest | 0.70 km² | 1 | 5 |

**Basis and limits, which any caption using the layer must carry:**

- Seeded by the **66 reference wells** in `outputs/03_master_data.csv`. The 22
  extended wells are not in the k=5 partition and do not seed cells.
- It is a **rendering of well membership, not a mapped hydrological boundary**.
  A cell edge lies midway between two wells and moves if the network changes.
  Regenerate whenever the partition or the reference network changes.

The generator is `build_cluster_kml.py` (delivered alongside; not yet placed in
`tools/`). It reads `03_master_data.csv` and `data/geo/site_boundary.kml`, and
writes the KML with each region's colour taken from `config.py`
`CLUSTER_COLOURS`. The written file was read back with `kml_io.read_kml` and
re-measured before delivery.

## newborough_report.py v1.4.0

- `add_kml_features()` gains `cluster_regions=False`. When True it reads
  `cluster_regions.kml` from `kml_dir` and outlines each region.
- `create_difference_map()` gains `cluster_regions=True` and passes it through.
  **`create_msl_map()` is deliberately unchanged.**
- **Outlines only, never filled.** The difference surface underneath is the
  month's signal; a colour wash over it would corrupt the reader's judgement of
  the diverging scale. Dashed, 1.4 pt, in each cluster's colour.
- Each region is tagged `C1`…`C5` at its representative point, so the legend
  needs **one** entry ("Cluster regions (C1–C5)") rather than five in an already
  four-entry legend.
- **The colours are read from the KML's own `<Style>` blocks**
  (`_cluster_region_colours`), not restated in the script. The KML is generated
  from `config.py` `CLUSTER_COLOURS` and carries them with it, so this standalone
  script mirrors no pipeline constant and the two cannot drift — the no-hardcoded
  -values rule applied to a script that cannot import `config.py`.
- Absent the KML the map is byte-comparable to v1.3.0, so a clone without the
  layer loses nothing and no caller has to change.

## Verified

Run against the live August 2026 data with the layer present: 25 KML files found
(was 24), all three difference maps regenerated, outlines and C1–C5 tags render
in cluster colour with a single legend entry, and the PNG was read back and
inspected rather than assumed. Module compiles; `__version__` assignment bumped.

## Wants a decision-log entry

The choice of boundary method is a methodological call and belongs in the private
`DECISION_LOG.md`. Draft text supplied separately — **not appended by this
session**, since the log is private, dated records are append-only, and this
session is not pushing.

## Deploy

`data/geo/cluster_regions.kml` is a **new tracked file** in the public repo and
needs `git add`. Regenerate it after any change to the k=5 partition.

## Known rough edge, for review

The site boundary extends past the maps' canonical extent, so the C4 and C5 tags
and some region edges fall outside the interpolated surface, over bare hillshade.
It reads correctly but adds clutter at the western margin. Clipping the overlay
to the interpolated area instead of the site boundary would tidy it; that is a
rendering choice and has not been made unilaterally.
