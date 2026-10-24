# `data/ccw_similarity_groups_martin.csv` — provenance

Martin Hollingham's own groupings of the thirteen CCW dipwells (codes 1A–1F on transect 1, 2A–2G on transect 2, read from February 1989), by similarity of their hydrographs. Added 2026-10-24 for Script 51 (D-275), which reports the groupings beside its 1989–96 clustering of the same wells.

- **Source:** Martin's workbook `Newborough_well_records.ods` (Google Drive `spreadsheets/`, nightly copy in `~/backups/well_records/`, copy of 23 October 2026), sheet **"CCW chart ex"**. The sheet holds 19 charts drawn from the sheet "ccw data" (rows 4–16 = codes 1A–2G).
- **Transcription:** each chart's title and the rows its data series read. These were extracted from the chart objects' `chart:values-cell-range-address` and `chart:label-cell-address` (session_015vCVAbUkwZHg65xKiYZr5j, 2026-10-24). Nothing was inferred; a chart's members are exactly the series it plots.
- **Columns:**
  - `chart`, the chart object's name in the workbook;
  - `title`, the chart title as Martin wrote it;
  - `similar`, `yes` when the title begins "Similar" (Martin's groupings by similarity), otherwise `no` (groupings by transect or land cover);
  - `code`, a CCW code. The modern well for each code is in `ccw_1989_1996_code_map.csv`; 2A is unidentified.
- **Read by:** `src/51_cluster_gap_fill.py` only, a documented raw-input exception (its header).
