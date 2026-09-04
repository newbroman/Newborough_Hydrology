> ## Recovered 2026-09-04 — the audit that seeded SCRIPT_LEDGER
>
> Written **2026-08-14** as a read-only methods↔code audit, never committed to
> this repository, recovered under T-10 from the Claude project store
> (`claude/NRG_methods_code_audit_2026-08-14.md`) and kept **verbatim below**.
> It is a dated record and is not edited.
>
> **Why the citation dangled.** `notes/ledgers/SCRIPT_LEDGER.md:10` names it as
> the audit the ledger was seeded from. The audit lived in the project store,
> not the repository; git never carried it.
>
> **Status today.** A dated register of proposed findings. Many were
> subsequently triaged and applied through the SCRIPT_LEDGER rows and dated
> deltas — the Script-29 τ-label, the Script-20 output count, and the Script-16
> Sy-free reconciliation among them. Treat the ledger and the changelogs, not
> this audit, as the current state; this is kept as the record of where the
> ledger's rows came from.
>
> ---

# NRG methods↔code audit — findings register

**Date:** 2026-08-14 · **Code baseline:** `main` HEAD `30aed9b` ·
**Docs audited:** report8 (Methods), Methods Supplement v1_9_8, Supplementary
Material v1_6, Paper 1 (+SI), Paper 2 · **Companion:** `SCRIPT_LEDGER.md`.

Read-only audit. **Nothing has been edited.** These are proposed findings for
Martin to triage. 66 numbered scripts audited; 21 carry a finding. Each was
produced by reading the actual source against the actual document passage;
headline structural drifts were spot-verified against the code (Script 07 "pure
visualisation", Script 16 "No Sy-dependent conversion", Script 30 identifiability
diagnostic, Script 14 Chart.js, `ENVELOPE_WET_YEARS` includes 2016 — all
confirmed). Confidence is noted per item; `medium`/`?` items need a pipeline
rerun or a second look before editing.

Method note: because report text sits at the bottom of the source-of-truth
hierarchy and the scripts moved repeatedly this year, most drift is doc-lagging-
code, not code error. Fixes are therefore documentation edits unless flagged.

---

## Class 1 — Structural drift ("Script-35 class": prose describes a pipeline shape the code no longer has). HIGHEST PRIORITY.

**07_spatial_coefficients.py** — MS §S.6/line 181 lists Script 07 among scripts
that "fit Model B (with intercept α) … as a diagnostic." Script 07 does no
fitting at all — its docstring: "replaces the former 07_boundary_intercept.py …
a pure visualization: no refit, no statistical test, no Model B fit." It only
renders IDW surfaces from `03_master_data.csv`. **Fix:** drop "07" → "fitted in
Scripts 08, 22, and 24." (high)

**09f_management_effects.py** — MS §S.15c describes a single spatial-reach
figure with two measured anchors. Code is a **two-panel** figure: panel (b)
"Development timescale" computes t½ relaxation curves from
`03_03_cluster_mechanistic_coefficients.csv`, and panel (a) plots a **third**
anchor (WMC3 off-cut drawdown from `10m_report_numbers.csv` +
`09b_01_individual_well_baci.csv`). None of panel (b), the WMC3 anchor, or the
three extra inputs appear in S.15c. **Fix:** update S.15c to the current
two-panel/three-anchor form. (high)

**10i_ceh34_hindcast.py** — report8 §3.5.4 says CEH34 "installed August 2010 …
one month after July 2010, the date at which the clearfell BACI opens … a single
hindcast value for July 2010 was supplied … R² = 0.91." Code:
`PRE_FELL_START = 2011-01-01`, and 10i hindcasts the **entire** pre-2010-08
window as a spliced series (not one cell); committed R² = **0.89**. MS §1457
already describes this correctly. **Fix:** rewrite the report8 CEH34 paragraph to
match MS §1457 (Jan-2011 window; full 2006–2010 hindcast retained for
reproducibility; R² 0.89). (high; 0.91→0.89 is a regenerated number — confirm on
rerun)

**16_water_bal.py** — report8 §3.7 and MS line 312 describe an "indicative
volumetric conversion using assumed specific yield values (Fetter, 2001)" with a
"hatched band" spanning a Fetter-vs-WTF-Sy bracket. Code uses **no Sy at all**:
`save_volumetric_table()` — "No Sy-dependent conversion — the partition is
derived from headspace ratios (SSM) and observed recession rates"; the band is
SSM-headspace vs seasonal-recession. MS §S.11 line 2173 already states this
correctly. **Fix:** reconcile report8 §3.7 + MS line 312 to the Sy-free method;
correct the hatched-band attribution. Also MS line 285 references
`SUMMER_TRENDS`/`FLOOD_FREQ` dicts "in Script 16" that do not exist — drop or
re-attribute. (high)

**20_spatial_figures.py** — MS §S.13 says "Script 20 generates **ten** spatial
outputs … all ten at publication DPI" and cites "~1200 lines." Code emits **18**
figures (incl. net_state_map = Fig 60, driver_change_2005_2025 = Fig 61,
clearfell_gain, msl5_change_2017_2023, observed_change_2012_2026, with-head
drawdown variants) and is 4399 lines. MS's own later subsections describe several
of the "extra" figures, so the "ten" headline simply was never updated. **Fix:**
update the output-count claim and the stale line counts (Script 20 ~1200→4399;
Script 19 ~1800→2127). (high)

**30_c4_drainage_identifiability.py** — MS §S.19.3 documents a retired script:
wrong filename (`30_c4_constrained_fit.py`), wrong title ("constrained-β₃
triangulation sensitivity"), wrong premise, wrong method ("re-fitted through
fit_ssm(fixed_beta_3=…)"), and four output filenames that no longer exist. The
current script (v2.1.0) "supersedes the earlier 30_c4_constrained_fit.py, whose
premise is not supported" and is a 4-test identifiability diagnostic emitting
`30_c4_identifiability_by_cluster.csv` / `30_c4_perwell_beta3.csv` /
`30_c4_report_numbers.csv` / `30_c4_drainage_identifiability.png`. report8 §3.5.4
lead label is also stale ("constrained-β₃ triangulation"), though its trailing
clause is updated. Also MS line 3651 "the two scripts in this chapter" covers
three (28, 29, 30). **Fix:** rewrite MS §S.19.3 to the identifiability diagnostic;
fix the report8 lead label and the "two scripts" count. (high)

---

## Class 2 — Stale numbers / counts (method is right; a figure or tally is out of date).

**03_state_space_model.py** — MS line 731 gives the datum empirical minimum as
"1.7 m … C4 p = 0.022 at 1.7 m." Committed `03_08_datum_sensitivity.csv`: all
five clusters first satisfy β₃>0 & p<0.05 at **1.5 m** (C4 p = 0.044). The same
document's line 162 and Supplementary Material Note S9 already say 1.5 m —
line 731 is internally contradicted. **Fix:** 1.7 m → 1.5 m; "C4 p = 0.022 at
1.7 m" → "C4 p = 0.044 at 1.5 m." (high)

**08_model_benchmarking.py** — MS line 1055: "median iterative NSE of **0.16** …
**Forty-three** of 66 reference wells have iterative NSE > 0 under the TLM."
Committed `08_lcsc_04_table3_benchmark_summary.csv` (and the doc's own Table 5):
TLM median iterative NSE = **0.18**, **44/66**. **Fix:** 0.16→0.18,
Forty-three→Forty-four. (high)

**14_climate_projections.py** — MS §S.8 says the interactive HTML scatter is
"**Plotly**"; the code builds it with **Chart.js** (`chart.umd.js`,
`new Chart(...)`). Also "The three figure outputs … Four CSV companions"
under-counts: v1.4.x also emits `14_climate_trajectory_spring.png` +
`14_spring_trend_stats.csv` (documented in a later paragraph but missing from the
enumeration/Outputs table). **Fix:** Plotly→Chart.js; update the figure/CSV
counts and Outputs table. (high / medium)

**26_van_willegen_msl.py** — MS line 3312 "processes **1,304 (91%)** … derived
**884** … 5-year window rows"; report8 §3.7.5 (committed-aligned) says "**13 of
1302** admitted annual spring means … **28 of 895** admitted five-year windows."
MS is stale. Caveat: the committed `26_report_numbers.csv` predates v1.7.0 (lacks
the new `msl5_n_*` keys) — confirm on rerun. Upstand check: **CLEAN** (no
document describes an upstand offset in the MSL computation). (medium; needs
rerun)

---

## Class 3 — Wrong attribution / provenance (right numbers, wrong source named).

**00_climate_summary.py** — MS line 95 says "Potential evapotranspiration is
computed inside the pipeline **(Script 00)** using Thornthwaite." Script 00 does
not compute PET — it reads `PET` already present in `01_climate.csv`; PET is
computed in Script 01 (`thornthwaite_pet_m()`). MS line 479 already says "PET is
computed locally inside Script 01." **Fix:** "(Script 00)" → "(Script 01)" at
line 95. (high)

**18_wtf_spatial.py** — MS line 2237 places `17_wtf_well_sy.csv` ("the per-well
event-based values … read by Scripts 09d, 20, 29, 30, 31, 37b") under the Script
**17** heading. That file is written by Script **18** (the "17_" prefix is
legacy). **Fix:** attribute the per-well Sy file to Script 18. (high on emitter;
low materiality)

**26b_van_willegen_msl_projections.py** — MS §S.18b.3.8 says 26b "fits the SSM β
coefficients on the cluster-centroid hydrograph: one OLS per cluster, with β₁/β₂
from … `03_regional_averages.csv`." Code reads **pre-fitted** coefficients from
`03_03_cluster_mechanistic_coefficients.csv` and runs no OLS (Script 03 does the
fitting). Numbers unaffected. **Fix:** describe 26b as consuming pre-fitted β;
correct the input filename. (medium)

**09f → Paper 1 Figure 19 provenance** — Paper 1's figure-source list attributes
Fig 19 to "Script 09f" with parameters `DRAWDOWN_H0/K/B`. 09f imports only
`DRAWDOWN_H0_MM`; the H0/K/B λ-cone render is `20_drawdown_propagation_nohead.png`
(Script 20) — consistent with the durable rule that Paper 1 Fig 19 is the Script
20 render. **Fix:** re-attribute Fig 19 to Script 20. (medium)

**Approach-B Sy conflation (MS §S.12)** — MS line 2351 states Scripts 19 and 21
"all use the cluster-level Sy from Script 17, not the per-well values." Code:
Script 19 uses per-well `Sy_median` from `18_wtf_01_well_sy_estimates.csv`;
Script 21 uses `median-of-per-well` from `17_wtf_well_sy.csv`; Script 20's λ uses
the C3 median of per-well estimates. None consume the `17_wtf_01` cluster
event-median. This is exactly the "two Approach-B aggregations must not be
conflated" rule. **Fix:** correct the S.12 downstream-consumer statement.
(medium-high)

---

## Class 4 — Undocumented emitted element (GAP).

**37b_driver_footing.py** — v1.2.0 (2026-07-17) added a **seventh** component
`"climate": ("Climate (common-mode)", "uniform", "loss")` — its own hatched bar,
CSV row, and figure-title term ("forest · scrape · coast · climate") — but MS
§S.20.6 and report8 line 392 still list only forest/scrape/coast. The common-mode
term is on the committed figure. **Fix:** add the common-mode component to S.20.6
and the report 37b passage. (high)

**33_envelope_amplification.py** — emits `33_amplification_field_recent.png`,
`33_dry_spring_depth_recent.png`, `33_envelope_per_well_recent.csv` (recent-window
/ extended-network products) that neither report nor MS output lists mention.
Decide whether these are numbered figures or internal companions. (medium)

---

## Class 5 — Minor / low-materiality stragglers.

- **09b** — MS documents `09b_report_numbers.csv` (not produced by the code);
  "three centroid groups" is actually four (adds "All uphill"); report8 §3.5 says
  a "distance-decay regression" was fitted — 09b fits none (it examines Δβ₃ vs
  distance without a regression). (high/medium)
- **09c** — S.6 09c section heading + output tables omit `09c_05…08` spring-mean
  outputs (documented elsewhere — MS addendum, SM Note S8, P1SI §S13.6). (low)
- **10h** — report8 line 229 "FE1, FE2 (both installed August 2015)"; code and
  report8 line 283 both say July 2015. (fact high, materiality low)
- **10m** — report8 line 12 range "10a–10l" omits 10m (MS §1309 correct). (low)
- **26c / MS step numbers** — MS §S.18b/§S.19 carry stale totals ("/35", "/36" →
  /49) and 26/26b/26c per-step numbers that contradict the manifest and the
  document's own canonical numbering elsewhere. (low)
- **29_c3_within_variance_check.py** — MS §S.19.2 lists the 5th metric as
  "storage–drainage index **τ = Sy/β₃**" with a table row (0.700). Code computes
  the **Sy-free** recession time `1/β₃` and explicitly comments it is "NOT the
  storage-drainage index tau = Sy/beta_3." Per the τ-retirement rule the doc
  should relabel this to recession time 1/β₃. (high on label; the 0.700 R² is for
  a metric the code no longer computes) — arguably Class 1, listed here for the
  τ-rule tie-in.
- **32** — `32_site_mean_trend.csv` output not itemised in the S.20.1 outputs
  table (value quoted in-text). (trivial)
- **33** — report8 line 388 + MS line 3832 give the wet-extreme set as
  "{2014, 2021, 2024}"; `config.ENVELOPE_WET_YEARS = [2014, 2016, 2021, 2024]`.
  Docs correctly note the 2006 exclusion but omit the paired 2016 inclusion.
  Headline swing numbers were computed with 2016 in, so the set list is the
  error, not the numbers. **Fix:** add 2016 to the wet set in both docs. (high)

---

## Traceability risks (not drift — flagged per the volatile-number rule)

- **10a / 10d** — every quoted BACI/mixed-model number (e.g. +0.120 m headline,
  −13/−109/+73 mm, curvature terms, ΔAIC) is written live to `report_numbers`
  and shifts on rerun. Structure matches the docs; re-trace each quoted figure to
  the committed CSV before publication.

## Confirmed clean (things most likely to have rotted — checked, no finding)

- **τ = Sy/β₃ retirement** — no document calls it a "drainage timescale" or
  "residence time" (MS explicitly states it is not); 1/β₃ and t½ = ln2/β₃ used
  correctly. (Exception: the Script 29 metric *label*, Class 5 above.)
- **MSL upstand removal (Script 26)** — no document still describes an upstand
  offset in the MSL computation.
- **Script 35 (the trigger case)** — now documented correctly as a Paper 1
  standalone product (r≈0.99), not a separate report map.
- **19b_scraping_simulator.py** — cited nowhere, but it is an orphaned
  interactive HTML tool not registered in `run_analysis.py`/the manifest and
  emits no analytical output; legitimately undocumented, **not** a gap. (Parity
  note: its sibling, Script 19's scenario viewer, *is* documented.)

## Also stale (not audited docs, flagged for completeness)

- Source-file **docstrings** for 09b, 09d carry stale "amplification"/output
  descriptions from the 2026-07-02 amplification removal; the published docs are
  correct. Script 07's docstring cites "Script 08 NSE = 0.77" (committed 0.75).
