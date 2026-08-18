# NUMBER_LEDGER — provenance for every cited number

**Living ledger. Edit in place; never date the filename.**

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

| ID | Quantity | Committed value | Source | Volatility | Cited in | Notes |
|----|----------|-----------------|--------|-----------|----------|-------|
| N-01 | Total registered steps | **49** | `outputs/pipeline_manifest.json` `total_registered` | stable | short-form headline everywhere | pipeline v2.3.0 |
| N-02 | Total phases | **17** | manifest `total_phases` | stable | R8, MS | |
| N-03 | Analytical top-level / display-utility / opt-in diagnostic | **39 / 4 / 6** | manifest `by_tier` | stable | MS | |
| N-04 | Default-exec / opt-in steps | **46 / 3** | manifest `by_exec` | stable | MS | |
| N-04b | Analytical phases | **15** | manifest `analytical_phases` | stable | **none — do not cite** | ⚠ the working-rules box says "17 analytical phases"; the manifest says 15 and the field is explicitly not for citation. See D-023. |
| N-05 | Script 20 figure count / line count | **18 figures**, 4399 lines | `src/20_spatial_figures.py` | stable | MS §S.13 | ⚠ MS says "ten spatial outputs", "~1200 lines". Script 19: 2127 lines, MS says ~1800. |

## B. Network counts

| ID | Quantity | Committed value | Source | Volatility | Cited in | Notes |
|----|----------|-----------------|--------|-----------|----------|-------|
| N-06 | Classified network | **88 dipwells = 66 reference + 22 extended** | `outputs/01_wells_reference.csv` (66 cols), `01_wells_extended.csv` (22) | stable | R8, MS, P1 | 89 "measuring points" adds the Llyn Rhos-Ddu lake gauge, which is **not** in the classified network |
| N-06b | Wells carried in `01_wells_clean.csv` | **78 columns = 77 dipwells + `llyn rhos`** | `outputs/01_wells_clean.csv` | stable | Scripts 33/35 | **77 is the amplification-metric well count** (lake gauge excluded, CEH13/CEH14 included — D-028), confirmed against the 2026-06-27 delta. The 11 wells in reference+extended but absent here (`FE4, L1, LIS1, ceh12, ceh35, ceh38, nw12, p1, p2, pe, pw`) lack usable series. **88 ≠ 78 ≠ 77 — all three are correct on different bases; never substitute one for another.** |
| N-06c | Amplification metric coverage | **77 wells**; 66 Tier-A on the surface | `src/35_per_well_amplification.py`, `33_envelope_per_well.csv` | stable | R8, MS, SM | CEH13 and CEH14 are the two highest (1.86, 2.20) |
| N-06d | C4 forest amplification / site-mean swing | **1.72×** / **752 mm (0.75 m)** | `33_envelope_per_well.csv`, `33_results.txt` | stable | R8 §5.7.5 | supersedes 1.62× / 735 mm (pre-blanket-include). C1 0.61×, C2 0.94×, C3 1.20×, C5 0.84×. ⚠ the per-cluster **n** here (7/27/18/10/6 = 68) is the *sitewide* Pearson assignment including extended wells — **not** the 66-well reference partition of N-07. Do not read cluster sizes off this table |
| N-07 | Cluster membership | C1 **7** · C2 **24** · C3 **21** · C4 **9** · C5 **5** | `outputs/02_clustering/02_07_cluster_membership_k5.csv`, config labels | stable | R8, MS, P1 | supersedes April-2026 8/28/22 — see D-020 |

## C. SSM cluster coefficients — `03_03_cluster_mechanistic_coefficients.csv`

Volatility: **stable**, but **N-08…N-12 for C4 are `MOVING`** — D-005 (CEH13/CEH14
exclusion) is signed off and will change the C4 row on the next Script 03 run.

| ID | Cluster | β₁ recharge | β₂ atmos. draw | β₃ drainage | p(β₃) | R² | n | LCSC % |
|----|---------|------------|----------------|-------------|-------|----|----|--------|
| N-08 | C1 Lake Edge | 4.5758 | 0.9562 | 0.08804 | 4.4e−35 | 0.7314 | 236 | 21.85 |
| N-09 | C2 Dune | 3.9735 | 1.7619 | 0.06407 | 1.5e−25 | 0.7460 | 247 | 25.17 |
| N-10 | C3 Western Residual | 3.5735 | 1.8334 | **0.05657** | 1.5e−28 | 0.8127 | 248 | 27.98 |
| N-11 | **C4 Main Forest** | 2.4873 | 2.5829 | **0.01832** | 1.7e−03 | 0.7253 | 236 | 40.20 |
| N-12 | C5 Coastal Forest | 2.4232 | 1.3071 | 0.04417 | 2.3e−16 | 0.6852 | 238 | 41.27 |

⚠ **These have already moved once unannounced.** The 2026-07-02 correction note
recorded C1 0.103 / C2 0.073 / C3 0.058 / C4 0.016 / C5 0.046 from
`03_master_data.csv`. Every one differs from the committed `03_03` values above.
Any document quoting the July figures is stale. **C4 will move again** to ≈0.030
under D-005.

| ID | Quantity | Committed value | Source | Notes |
|----|----------|-----------------|--------|-------|
| N-13 | C4 centroid β₃ (canonical) | **0.0183**, p = 0.0017 | `30_c4_report_numbers.csv` `c4_centroid_beta3` | matches N-11; `MOVING` under D-005 |
| N-14 | C4 VIF (identifiability) | **1.0934** — second lowest; C5 is lower at **1.0713** | `30_c4_report_numbers.csv`, `30_c4_identifiability_by_cluster.csv` | the number that refuted the triangulation premise (D-001). ⚠ "network minimum" was wrong — corrected 2026-08-16, same stale claim as D-011 |
| N-15 | C4 corr(PET, h_disp_prev) | **−0.0396** — network minimum | `30_c4_report_numbers.csv` | |
| N-16 | C4 SD of displacement | **0.4774 m** — network maximum | `30_c4_report_numbers.csv` | |
| N-17 | C4 per-well non-significant β₃ fits | **6 wells** | `30_c4_report_numbers.csv` | sampling noise, not collinearity |
| N-18 | C4 open-dune conservative bound | **0.058** | retained as a bound only | ⚠ **not** a triangulation result — see D-001 |

## D. Datum

| ID | Quantity | Committed value | Source | Volatility | Notes |
|----|----------|-----------------|--------|-----------|-------|
| N-19 | `DRAINAGE_DATUM` | **3.7 m** below ground | `src/utils/config.py` | constant | D-007 |
| N-20 | Shallowest depth with β₃ > 0 and p < 0.05 in **all** clusters | **1.5 m** (C4 p = **0.0443**) | `03_08_datum_sensitivity.csv` | stable | ⚠ MS line 731 says "1.7 m, C4 p = 0.022"; the same document's line 162 and SM Note S9 already say 1.5 m |
| N-21 | Optimal-datum slope on ground elevation | **+0.133** (depth) / **+0.868** (elevation), r +0.317 / +0.909, n = 66 | `03_09_well_optimal_datums.csv` × `01_well_elevations.csv` | stable | supersedes the 2026-06-08 values +0.146 / +0.854 |
| N-22 | Ground-elevation spread | **10.9 m** (3.53–14.42 mAOD) | `01_well_elevations.csv` | stable | supersedes 10.8 m |

## E. Specific yield — **the two aggregations are not interchangeable (D-009)**

| ID | Quantity | Committed value | Source | Volatility | Consumed by |
|----|----------|-----------------|--------|-----------|-------------|
| N-23 | C3 **cluster event median** | **0.3283** | `17_wtf_01_sy_estimates.csv` `Sy_event_median` | stable | **no script** — reported in Paper 1 Table 4 only |
| N-24 | C3 **median of per-well** | **0.3057** | `outputs/17_wtf_well_sy.csv` `Sy_median` (written by Script **18**) | stable | 09d, 20, 21, 29, 30, 31, 37b — and λ |
| N-25 | Per-cluster median-of-per-well | C1 0.2142 · C2 0.2609 · C3 0.3057 · C4 0.2541 · C5 0.3084 | `17_wtf_well_sy.csv` | stable | C4/C5 flagged `Corrected` |
| N-26 | Per-cluster event medians | C1 0.2102 · C2 0.2809 · C3 0.3283 · C4 0.3149 · C5 0.3560 (C4/C5 corrected: 0.2587 / 0.3213) | `17_wtf_01_sy_estimates.csv` | stable | |

⚠ **N-23 drift:** the project working-rules box states the C3 cluster event median
is **0.3255** and that this is the Paper 1 Table 4 value. The committed CSV gives
**0.3283**. One of the two is stale. **Resolve before either is published** — check
Paper 1 Table 4 against the committed file, then correct whichever is wrong.

## F. λ — the drawdown reach (**by name, never by number** — D-024)

| ID | Quantity | Committed value | Source | Volatility | Notes |
|----|----------|-----------------|--------|-----------|-------|
| N-27 | λ drawdown reach | **228.14 m** | `20_report_numbers.csv` `drawdown_lambda` | **volatile** | computed from Sy = 0.3057 (N-24), β₃ = 0.0566/mo (N-10), K = 6.0, b = 5.0 |
| N-28 | `DRAWDOWN_H0_MM` / `K_MDAY` / `B_M` | **150.0 mm / 6.0 m·d⁻¹ / 5.0 m** | `config.py` | constant | K from Betson (2002) |
| N-29 | Modelled steady-state forest drawdown | CEH23 25.19 · D15 35.11 · CEH6 8.45 · CEH10 1.46 · CEH24 0.66 · CEH11 0.38 mm | `20_report_numbers.csv` | volatile | |

⚠ Documents have carried λ as 223, 224.9, 225, 228.1 and 230. **Never quote a λ
number without retracing it.** Render: `20_drawdown_propagation_nohead.png` =
report Fig 50 = Paper 1 Fig 19 (**Script 20**, not 09f).

## G. Benchmarking and BACI headlines

| ID | Quantity | Committed value | Source | Volatility | Notes |
|----|----------|-----------------|--------|-----------|-------|
| N-30 | TLM median iterative NSE | **0.18** | `08_lcsc_04_table3_benchmark_summary.csv` | stable | ⚠ MS line 1055 says 0.16 |
| N-31 | Wells with TLM iterative NSE > 0 | **44 / 66** (SSM: 65/66) | same | stable | ⚠ MS says "Forty-three" |
| N-32 | Median iterative R² | TLM **0.66** → SSM **0.80** (Δ 0.13) | same | stable | |
| N-33 | Median one-step R² | TLM 0.91 → SSM 0.92 | same | stable | |
| N-34 | Clearfell ANCOVA step (Forest Impact) | **0.1196 m**, p < 0.001, CI [0.0497, 0.1894] | `10a_report_numbers.csv` | **volatile** | the "+0.120 m" headline; retrace every time |
| N-35 | Scraping ANCOVA step | **0.3436 m**, p = 0.0019 | `10a_report_numbers.csv` | volatile | model R² 0.2737, n = 162 months |
| N-36 | CEH34 hindcast R² | **0.9115** | `10i_report_numbers.csv` `CEH34_hindcast_r2` | volatile | ⚠ **the 2026-08-14 audit was wrong here**: it claimed the committed value was 0.89 and the report's 0.91 was stale. The committed value is 0.9115 — the report is right. Donor CEH9; α −0.1485, slope 1.0515; RMSE 0.1246 m; 80-month calibration, 51-month synthetic extension |
| N-37 | CEH36 pure-scraping BACI shift | **+0.1294 m** vs CEH4 | `09_scrape_report_numbers.csv` | volatile | net benefit vs CEH21 coastal benchmark: +0.1435 m |

## H. Water balance — `16_water_bal_table.csv` (**Sy-free**, D-021)

| ID | Cluster | Drainage % | ET % | Residual (m/month) |
|----|---------|-----------|------|--------------------|
| N-38 | C1 Lake Edge | 84.72 | 15.28 | −0.0043 |
| N-39 | C2 Dune | 67.80 | 32.20 | −0.0035 |
| N-40 | C3 Western Residual | 62.28 | 37.72 | −0.0005 |
| N-41 | **C4 Main Forest** | 23.47 | **76.53** | −0.0009 |
| N-42 | C5 Coastal Forest | 61.11 | 38.89 | −0.0040 |

`MOVING` — C4 and the site aggregate change under D-005. The C4 closure-minimising
β₃ is **0.0160** (`30_c4_report_numbers.csv` `c4_closure_min_beta3`), close to the
current canonical 0.0183.

## I. Config constants (change only by deliberate edit)

| ID | Constant | Value | Notes |
|----|----------|-------|-------|
| N-43 | `HEADLINE_LAG` | **0** | no rainfall lag — D-008 |
| N-44 | `FOREST_INTERCEPTION` | **0.24** | a partition of the PET budget, applies to C4 **and** C5 — D-022 |
| N-45 | `REFERENCE_CUTOFF_DATE` | **2026-02-01** | |
| N-46 | `RAF_VALLEY_LAT_DEG` | **53.25** | confirmed correct; 53.15 is stale |
| N-47 | `SCRAPE_RISE_BUFFER_M` / `COAST_RETREAT_M` / `COAST_RETREAT_RATE` | **10.0 m / 6.0 m / 8.3 m·yr⁻¹** | shared by Scripts 20, 09d, 09f |
| N-48 | `COAST_RETREAT_2005_2025_M` / `_EFFECTIVE_M` | **50.0 m / 105.0 m** | 50 m is the physical measurement (Pye & Blott); **not** rate × 20 (=166 m, which overstates) |
| N-49 | `ENVELOPE_WET_YEARS` | **[2014, 2016, 2021, 2024]** | ⚠ report8 line 388 and MS line 3832 give {2014, 2021, 2024} — **2016 is missing from the docs, not from the code**. Headline swing numbers were computed with 2016 in, so the numbers are right and the set list is wrong |
| N-50 | `RESIDUAL_DIAG_MIN_MONTHS` / excluded wells | **140** / `{ceh3, ceh4, ceh7, ceh8, ceh37, llynrhos}` | Scripts 23, 24 |
| N-51 | `LCSC_DATA_LIMIT` | **100** | ✔ **resolved 2026-08-16** — now declared once in `config.py` and imported by Scripts 03, 08 and 30 (`model_utils` re-exports the name). Was mirrored as a per-script local in three files. See D-007 (the window policy) and D-027 (this fix) |

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
