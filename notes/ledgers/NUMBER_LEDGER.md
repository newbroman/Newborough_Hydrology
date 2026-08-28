# NUMBER_LEDGER — provenance for every cited number

**Living ledger. Edit in place; never date the filename.**

> **2026-08-25 — the value columns are retired.** This ledger no longer carries a
> copy of the numbers. `cite_check` and `tools/citation_index.csv` check 1,700
> committed values against every document in the corpus automatically; keeping a
> second hand-maintained copy here duplicated that work and drifted from it — by
> 2026-08-25 all five cluster β₁ figures were wrong in the fourth decimal, the
> re-fit this file had itself predicted. What the ledger keeps is what only it
> holds: which quantities are load-bearing, where each comes from, how volatile
> it is on a rerun, and which documents cite it.

The enforcement arm of the standing rule *"numbers must trace to a committed CSV
before entering the report; never cache a value that shifts when scripts rerun."*
One row per headline number or constant that appears in a document. If a number is
in a document and not in this table, it is untraced.

- **All values below were read from committed outputs at GitHub `main` HEAD
  `30aed9b` on 2026-08-14.** Where a document carries a different value, the
  committed value is authoritative and the document is the thing to fix.
- **Volatility** says what happens on a rerun: `constant` = a config value, only
  changes by deliberate edit · `stable` = regenerates to the same value on
  unchanged inputs · `volatile` = written live to a `report_numbers` CSV and
  expected to move · `MOVING` = a signed-off change will move it imminently.
- **⚠ drift** marks a row where a document (or the project working-rules box) is
  known to disagree with the committed value.

**Retrace protocol:** before a number is published, re-read it from the file named
in the `Source` column at the current HEAD and update `Last traced`. Do not copy
it from a docstring, a prior document, or an earlier row of this table — the
2026-08-14 audit was itself wrong twice by doing exactly that (see N-05, N-27).

---

## A. Pipeline structure

| ID | Quantity | Source | Volatility | Cited in | Notes |
|----|----------|--------|-----------|----------|-------|
| N-01 | Total registered steps | `outputs/pipeline_manifest.json` `total_registered` | stable | short-form headline everywhere | pipeline v2.3.0 |
| N-02 | Total phases | manifest `total_phases` | stable | R8, MS | |
| N-03 | Analytical top-level / display-utility / opt-in diagnostic | manifest `by_tier` | stable | MS | |
| N-04 | Default-exec / opt-in steps | manifest `by_exec` | stable | MS | |
| N-04b | Analytical phases | manifest `analytical_phases` | stable | **none — do not cite** | ⚠ the working-rules box says "17 analytical phases"; the manifest says 15 and the field is explicitly not for citation. See D-023. |
| N-05 | Script 20 figure count / line count | `src/20_spatial_figures.py` | stable | MS §S.13 | ⚠ MS says "ten spatial outputs", "~1200 lines". Script 19: 2127 lines, MS says ~1800. |

## B. Network counts

| ID | Quantity | Source | Volatility | Cited in | Notes |
|----|----------|--------|-----------|----------|-------|
| N-06 | Classified network | `outputs/01_wells_reference.csv` (66 cols), `01_wells_extended.csv` (22) | stable | R8, MS, P1 | 89 "measuring points" adds the Llyn Rhos-Ddu lake gauge, which is **not** in the classified network |
| N-06b | Wells carried in `01_wells_clean.csv` | `outputs/01_wells_clean.csv` | stable | Scripts 33/35 | **77 is the amplification-metric well count** (lake gauge excluded, CEH13/CEH14 included — D-028), confirmed against the 2026-06-27 delta. The 11 wells in reference+extended but absent here (`FE4, L1, LIS1, ceh12, ceh35, ceh38, nw12, p1, p2, pe, pw`) lack usable series. **88 ≠ 78 ≠ 77 — all three are correct on different bases; never substitute one for another.** |
| N-06c | Amplification metric coverage | `src/35_per_well_amplification.py`, `33_envelope_per_well.csv` | stable | R8, MS, SM | CEH13 and CEH14 are the two highest (1.86, 2.20) |
| N-06d | C4 forest amplification / site-mean swing | `33_envelope_per_well.csv`, `33_results.txt` | stable | R8 §5.7.5 | supersedes 1.62× / 735 mm (pre-blanket-include). C1 0.61×, C2 0.94×, C3 1.20×, C5 0.84×. ⚠ the per-cluster **n** here (7/27/18/10/6 = 68) is the *sitewide* Pearson assignment including extended wells — **not** the 66-well reference partition of N-07. Do not read cluster sizes off this table |
| N-07 | Cluster membership | `outputs/02_clustering/02_07_cluster_membership_k5.csv`, config labels | stable | R8, MS, P1 | supersedes April-2026 8/28/22 — see D-020 |

## C. SSM cluster coefficients — `03_03_cluster_mechanistic_coefficients.csv`

Volatility: **stable**, but **N-08…N-12 for C4 are `MOVING`** — D-005 (CEH13/CEH14
exclusion) is signed off and will change the C4 row on the next Script 03 run.

**N-08 … N-12** — one row per cluster in
`03_03_cluster_mechanistic_coefficients.csv`: β₁ recharge, β₂ atmospheric draw,
β₃ drainage, p(β₃), R², n and LCSC %.

The values themselves are not reproduced here. `cite_check` holds them under the
keys `C1 (Lake Edge) · beta_1_recharge` and its siblings and checks them against
every document in the corpus, which is a job this table was doing by hand and
losing: on 2026-08-25 all five β₁ figures had drifted into the fourth decimal.

⚠ **These have already moved once unannounced.** The 2026-07-02 correction note
recorded C1 0.103 / C2 0.073 / C3 0.058 / C4 0.016 / C5 0.046 from
`03_master_data.csv`. Every one differs from the committed `03_03` values above.
Any document quoting the July figures is stale. **C4 will move again** to ≈0.030
under D-005.

| ID | Quantity | Source | Notes |
|----|----------|--------|-------|
| N-13 | C4 centroid β₃ (canonical) | `30_c4_report_numbers.csv` `c4_centroid_beta3` | matches N-11; `MOVING` under D-005 |
| N-14 | C4 VIF (identifiability) | `30_c4_report_numbers.csv`, `30_c4_identifiability_by_cluster.csv` | the number that refuted the triangulation premise (D-001). ⚠ "network minimum" was wrong — corrected 2026-08-16, same stale claim as D-011 |
| N-15 | C4 corr(PET, h_disp_prev) | `30_c4_report_numbers.csv` | |
| N-16 | C4 SD of displacement | `30_c4_report_numbers.csv` | |
| N-17 | C4 per-well non-significant β₃ fits | `30_c4_report_numbers.csv` | sampling noise, not collinearity |
| N-18 | C4 open-dune conservative bound | retained as a bound only | ⚠ **not** a triangulation result — see D-001 |

## D. Datum

| ID | Quantity | Source | Volatility | Notes |
|----|----------|--------|-----------|-------|
| N-19 | `DRAINAGE_DATUM` | `src/utils/config.py` | constant | D-007 |
| N-20 | Shallowest depth with β₃ > 0 and p < 0.05 in **all** clusters | `03_08_datum_sensitivity.csv` | stable | ⚠ MS line 731 says "1.7 m, C4 p = 0.022"; the same document's line 162 and SM Note S9 already say 1.5 m |
| N-21 | Optimal-datum slope on ground elevation | `03_09_well_optimal_datums.csv` × `01_well_elevations.csv` | stable | supersedes the 2026-06-08 values +0.146 / +0.854 |
| N-22 | Ground-elevation spread | `01_well_elevations.csv` | stable | supersedes 10.8 m |

## E. Specific yield — **the two aggregations are not interchangeable (D-009)**

| ID | Quantity | Source | Volatility | Consumed by |
|----|----------|--------|-----------|-------------|
| N-23 | C3 **cluster event median** | `17_wtf_01_sy_estimates.csv` `Sy_event_median` | stable | **no script** — reported in Paper 1 Table 4 only |
| N-24 | C3 **median of per-well** | `outputs/18_wtf_spatial/18_wtf_01_well_sy_estimates.csv` `Sy_median` (written by Script **18**) | stable | 09d, 20, 21, 29, 30, 31, 37b — and λ |
| N-25 | Per-cluster median-of-per-well | `18_wtf_01_well_sy_estimates.csv` | stable | C4/C5 flagged `Corrected` |
| N-26 | Per-cluster event medians | `17_wtf_01_sy_estimates.csv` | stable | |

⚠ **N-23 drift:** the project working-rules box states the C3 cluster event median
is **0.3255** and that this is the Paper 1 Table 4 value. The committed CSV gives
**0.3283**. One of the two is stale. **Resolve before either is published** — check
Paper 1 Table 4 against the committed file, then correct whichever is wrong.

## F. λ — the drawdown reach (**by name, never by number** — D-024)

| ID | Quantity | Source | Volatility | Notes |
|----|----------|--------|-----------|-------|
| N-27 | λ drawdown reach | `20_report_numbers.csv` `drawdown_lambda` | **volatile** | computed from Sy = 0.3057 (N-24), β₃ = 0.0566/mo (N-10), K = 6.0, b = 5.0 |
| N-28 | `DRAWDOWN_H0_MM` / `K_MDAY` / `B_M` | `config.py` | constant | K from Betson (2002) |
| N-29 | Modelled steady-state forest drawdown | `20_report_numbers.csv` | volatile | |

⚠ Documents have carried λ as 223, 224.9, 225, 228.1 and 230. **Never quote a λ
number without retracing it.** Render: `20_drawdown_propagation_nohead.png` =
report Fig 50 = Paper 1 Fig 19 (**Script 20**, not 09f).

## G. Benchmarking and BACI headlines

| ID | Quantity | Source | Volatility | Notes |
|----|----------|--------|-----------|-------|
| N-30 | TLM median iterative NSE | `08_lcsc_04_table3_benchmark_summary.csv` | stable | ⚠ MS line 1055 says 0.16 |
| N-31 | Wells with TLM iterative NSE > 0 | same | stable | ⚠ MS says "Forty-three" |
| N-32 | Median iterative R² | same | stable | |
| N-33 | Median one-step R² | same | stable | |
| N-34 | Clearfell ANCOVA step (Forest Impact) | `10a_report_numbers.csv` | **volatile** | the "+0.113 m" headline; retrace every time |
| N-35 | Scraping ANCOVA step | `10a_report_numbers.csv` | volatile | model R² 0.2737, n = 162 months |
| N-36 | CEH34 hindcast R² | `10i_report_numbers.csv` `CEH34_hindcast_r2` | volatile | ⚠ **the 2026-08-14 audit was wrong here**: it claimed the committed value was 0.89 and the report's 0.91 was stale. The committed value is 0.9115 — the report is right. Donor CEH9; α −0.1485, slope 1.0515; RMSE 0.1246 m; 80-month calibration, 51-month synthetic extension |
| N-37 | CEH36 pure-scraping BACI shift | `09_scrape_report_numbers.csv` | volatile | net benefit vs CEH21 coastal benchmark: +0.1435 m |

## H. Water balance — `16_water_bal_table.csv` (**Sy-free**, D-021)

**N-38 … N-42** — one row per cluster in `16_water_bal_table.csv`
(**Sy-free**, D-021): drainage %, ET % and the residual in m/month.

Volatility **stable**. C4 Main Forest is the row worth watching — its ET share is
the outlier that the forest-interception argument rests on.

Values are not reproduced here; `cite_check` holds them and checks them against
the corpus.

`MOVING` — C4 and the site aggregate change under D-005. The C4 closure-minimising
β₃ is **0.019** (`30_c4_report_numbers.csv` `c4_closure_min_beta3`), close to the
current canonical **0.0185**
(`03_03_cluster_mechanistic_coefficients.csv`, C4 `beta_3_drainage` = 0.018455).

> *Note added 2026-08-28 (T-18d).* Both numbers in the sentence above were
> stale. The canonical was written 0.0183 against a committed 0.018455, and the
> closure-minimising value was written 0.0160 against a committed 0.019 — which
> the T-18d sweep did not reach, because `c4_closure_min_beta3` is stored at
> 3 dp and 0.0160 was therefore never a near-miss on anything it could search.
> A ledger other documents are told to trust is the worst place in the corpus
> for a stale number, and this row's own `MOVING` marker is what it was for.

## I. Config constants (change only by deliberate edit)

| ID | Constant | Notes |
|----|----------|-------|
| N-43 | `HEADLINE_LAG` | no rainfall lag — D-008 |
| N-44 | `FOREST_INTERCEPTION` | a partition of the PET budget, applies to C4 **and** C5 — D-022 |
| N-45 | `REFERENCE_CUTOFF_DATE` | |
| N-46 | `RAF_VALLEY_LAT_DEG` | confirmed correct; 53.15 is stale |
| N-47 | `SCRAPE_RISE_BUFFER_M` / `COAST_RETREAT_M` / `COAST_RETREAT_RATE` | shared by Scripts 20, 09d, 09f |
| N-48 | `COAST_RETREAT_2005_2025_M` / `_EFFECTIVE_M` | 50 m is the physical measurement (Pye & Blott); **not** rate × 20 (=166 m, which overstates) |
| N-49 | `ENVELOPE_WET_YEARS` | ⚠ report8 line 388 and MS line 3832 give {2014, 2021, 2024} — **2016 is missing from the docs, not from the code**. Headline swing numbers were computed with 2016 in, so the numbers are right and the set list is wrong |
| N-50 | `RESIDUAL_DIAG_MIN_MONTHS` / excluded wells | Scripts 23, 24 |
| N-51 | `LCSC_DATA_LIMIT` | ✔ **resolved 2026-08-16** — now declared once in `config.py` and imported by Scripts 03, 08 and 30 (`model_utils` re-exports the name). Was mirrored as a per-script local in three files. See D-007 (the window policy) and D-027 (this fix) |

## J. Known-stale sources — do not read numbers from these

| ID | Source | Problem |
|----|--------|---------|
| N-52 | `outputs/30_c4_constrained_fit/` | archived outputs of a **retired** script; produced by no live script (D-001) |
| N-53 | `outputs/26_van_willegen_msl/26_report_numbers.csv` | predates Script 26 v1.7.0 — lacks the `msl5_n_*` keys. MS line 3312 ("1,304 (91%) … 884 windows") vs report8 §3.7.5 ("13 of 1302 … 28 of 895"). **Needs a rerun to resolve** |
| N-54 | `utils/` at repo root (`config.py`, `model_utils.py`, `clearfell_common.py`, `map_utils.py`, `scraping_common.py`, `site_observations.py`) | a **stale shadow copy** of `src/utils/`; all six files differ from the live versions and `config.py` is missing 5 constants. Nothing imports it (scripts put `src/` on `sys.path`), but it is a live trap for anyone reading constants. See the reorg proposal |
| N-55 | Source-file docstrings | 09b and 09d carry stale "amplification" descriptions from the 2026-07-02 removal; `07`'s docstring cites "Script 08 NSE = 0.77" against a committed 0.75. **Docstrings are not a source — always read the CSV** |

---

## Maintenance

1. When a script changes, update its `SCRIPT_LEDGER` row **and** re-trace every
   `NUMBER_LEDGER` row sourced from it. Rows marked `volatile` need this on every
   rerun; `stable` rows need it whenever the producing script's version bumps.
2. `tools/audit_number_drift.py` mechanises the detection half: it diffs every
   numeric cell of the committed CSVs between two git refs and searches the
   document corpus for renderings of the old value. Run it before any publication
   pass — it over-reports by design, so every hit still needs eyeballing.
3. A number that cannot be given a `Source` cell does not go in a document.

> *Note added 2026-08-28 (T-15).* N-24 and N-25 named `17_wtf_well_sy.csv`, a path **retired on 2026-08-19 under D-038** and no longer written by anything — `paths.py` says so in terms, and the file is not on disk. Re-pointed to Script 18's `18_wtf_01_well_sy_estimates.csv`, which is the same content under the name that survived. The same stale path was live in eight places in the Methods Supplement and one in `PAPER1_TABLES.md`; all corrected the same day.
