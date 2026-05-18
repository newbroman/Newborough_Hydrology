# Partition history & cluster identity

This note exists because the cluster numbering has changed at least once, and
that kind of change has gotchas. Anyone working on this project — human or
LLM — should read this before touching code that's keyed on cluster ID.

## Current partition (k=5)

The authoritative source for IDs, labels, and colours is `utils/config.py`.
The anchors that map Ward's raw output to these canonical IDs are in
`02_clustering.py`'s `CLUSTER_ID_ANCHORS` dict. A guard at module load time
asserts the two agree.

| ID | Label              | Anchor wells     | Old-partition equivalent                 |
|----|--------------------|------------------|------------------------------------------|
| 1  | Lake (Edge)        | ceh5, ceh11      | Old C1 (Eastern Block Lake)              |
| 2  | Dune               | d10              | Old C2 (Eastern Block Mature Dune)       |
| 3  | Western Residual   | nw1              | Old C3 (Western Block Mature Dune)       |
| 4  | Main Forest        | ceh2             | Old C4 (Forest)                          |
| 5  | Coastal Forest     | ceh16, nw9       | Subset of Old C3 — forested wells split out |

The block label for C1 is "Lake Edge" in any new prose; "Lake-buffer" /
"Eastern Block Lake" are old labels and should not appear in new code or
figures.

## Dropped from the partition (old k=6 → new k=5)

These were small-n / physically unreliable groups in the old partition and
were dropped at the partition step. Their names re-appear in the new
partition but refer to different physical clusters — do not conflate.

- Old C5 (Coastal, n=1) — dropped
- Old C6 (Lake, n=1)    — dropped (this is NOT the new C1 Lake Edge)

## Identity vs integer — the gotcha

Most code keyed on cluster ID happens to transfer cleanly under the current
renumber because the integers 1..4 align with their old equivalents. But the
distinction below matters and will bite again if the partition changes:

- **Things keyed on cluster identity** (labels, colours, markers, anchor
  wells, well-to-cluster membership) — these move with the partition. When
  the partition changes, these values stay attached to the same physical
  cluster and just get reassigned to whatever new ID that cluster carries.

- **Things keyed on cluster integer** (Python dicts mapping `1`, `2`, ...
  to specific yields, peak months, trend values, flood frequencies, residual
  standard errors, etc.) — these are physical inputs to downstream
  arithmetic. When the partition changes, the dict key is just an integer;
  it doesn't follow a cluster around. Each entry needs to be checked
  individually: does the value still apply to whatever physical cluster has
  that integer ID under the new partition?

Convention going forward: if a dict is keyed by integer cluster ID and holds
anything other than labels/colours/markers, treat it as physical data tied
to a specific cluster. When the partition changes, walk through every such
dict and verify each entry, don't assume.

## Specific yield values

Two methods produce Sy values per cluster.

### Fetter (mass-balance) — committed values under the new partition

```
C1 (Lake Edge):       0.08   # lake-adjacent, finer sediments
C2 (Dune):            0.12
C3 (Western Residual):0.12
C4 (Main Forest):     0.12
C5 (Coastal Forest):  0.12
```

These are the values to use anywhere `SY = {...}` appears.

### WTF (empirical)

```
C1 (Lake Edge):       0.223
C2 (Dune):            0.234
C3 (Western Residual):0.259
C4 (Main Forest):     0.227
C5 (Coastal Forest):  not yet computed
```

The C5 WTF Sy needs to be computed by extending Script 17's WTF analysis to
the n=5 Coastal Forest cluster (which is feasible — old C3 was where these
wells previously sat).

## Other ID-keyed scientific dicts that need attention under the new partition

These were committed values under the old partition and need recomputing for
all clusters under the new one. They are NOT label-pass items.

- `SUMMER_TRENDS` (script 16) — m/yr drying trend per cluster
- `FLOOD_FREQ` (script 16) — flood frequency per cluster
- `RESIDUAL_PCT_SE` (script 16) — water-balance residual standard error %
- `CLUSTER_PEAK_MONTH` (script 11) — historical mean peak month per cluster
  used to set the forecasting horizon. The old values were
  `{C1: 1, C2: 1, C3: 2, C4: 4}`; under the new partition C4 (Main Forest)
  still maps cleanly to old C4 (Forest, peak April) but the rest need
  re-deriving from the new cluster-average hydrographs.

Until these are recomputed, scripts 11 and 16 should be treated as
mechanically renamed but scientifically suspect: the labels are correct, the
input dicts are not.

## What should NOT change with the partition

- The amplitude descriptor outputs (`02_08_…per_well.csv`,
  `02_09_…summary.csv`) — these are derived from per-well time series and
  the cluster ID is just attached at the end. Renumbering does not affect
  the underlying numbers, only which cluster they're filed under.
- The cluster anchors as a concept — the anchor wells stay the same, only
  which canonical ID they get mapped to changes.
- The state-space model and BACI analysis specifications.
