# Decisions

Analytical decisions taken in the course of this study, in the order they were
numbered. Each entry records what was decided, when, and whether it still
stands. They are cited by number from the Methods Supplement and the pipeline
documentation.

A decision appears here because a choice existed and one option was taken:
which wells enter a control tier, what a fitted constant may and may not be
read as, where a boundary between an input and a result falls. Several record
that a quantity the data appear to offer is not one the record can support, and
those are decisions too — the useful output of an analysis includes what it
declines to claim.

This is a distillation. The working record behind it carries, for each entry,
the question that prompted it, the reasoning, the alternatives weighed and any
later correction. Only the settled decision is reproduced here.

*Generated from the working record by `tools/build_public_decisions.py`. Do not
edit by hand.*

---

## Citations written before 2026-08-16

`ledgers/DECISION_LOG.md` was a second decision log whose D-numbers meant
different things. It is retired. Anything written before 2026-08-16 that cites a
D-id may be using the ledger numbering — translate it here first.

| Was | Is now | |
|---|---|---|
| ledger D-001 | **D-019** | imported verbatim on merge |
| ledger D-002 | **D-007** | already recorded here under a different number |
| ledger D-003 | **D-001** | already recorded here under a different number |
| ledger D-004 | **D-005** | already recorded here under a different number |
| ledger D-005 | **D-002** | already recorded here under a different number |
| ledger D-006 | **D-010** | already recorded here under a different number |
| ledger D-007 | **D-009** | already recorded here under a different number |
| ledger D-008 | **D-020** | imported verbatim on merge |
| ledger D-009 | **D-008** | already recorded here under a different number |
| ledger D-010 | **D-021** | imported verbatim on merge |
| ledger D-011 | **D-022** | imported verbatim on merge |
| ledger D-012 | **D-023** | imported verbatim on merge |
| ledger D-013 | **D-024** | imported verbatim on merge |
| ledger D-014 | **D-025** | imported verbatim on merge |
| ledger D-015 | **D-026** | imported verbatim on merge |
| ledger D-016 | **D-027** | imported verbatim on merge |
| ledger D-017 | **D-028** | imported verbatim on merge |

---

---

### D-001 — C4 β₃ triangulation retired

*2026-07-24*

The triangulation is retired. The direct centroid fit stands as the cluster coefficient.

**Revisit if** the C4 centroid VIF rises materially relative to the rest of the network on a future data vintage. The open-dune anchor (0.058 month⁻¹) is retained in report9 §5.2.3 as a conservative bound only — it opens the closure residual well beyond the fitted value.

### D-002 — SSM fitting-window policy — the 100-month window is a comparison window, not a cap

*2026-08-16*

The pipeline is **not re-cut**. The published per-well coefficients keep the comparison window. The improvement available on full records is **reported as a cited sensitivity** (D-005) rather than adopted.

**Revisit if** a future analysis needs per-well coefficients pooled or ranked across wells on a fit-quality metric — that needs an equal window and should use the existing comparison constant, not a new one. Full audit and evidence: `NRG_window_policy_spec_2026-08-14.md`.

### D-003 — Panel balance does not require an equal window

*2026-08-16*

Full-record fits do not unbalance the per-well comparisons. The imbalance is measurable and benign. The real composition imbalance is in the cluster centroids, and is disclosed rather than removed (D-004).

**Revisit if** a future vintage introduces wells whose record length correlates with cluster, which would reconnect epoch to the contrasts.

### D-004 — Cluster centroids keep growing membership; the disclosure is corrected

*2026-08-16*

The published coefficients stand. The **§3.4.1 sensitivity statement is corrected** so the disclosure matches the data, and the check is emitted to a committed CSV.

**Revisit if** a cluster's membership changes, or the composition sensitivity at any cluster exceeds the C4 figure — at which point fixed-membership centroids (the fix `clearfell_common` v1.7.0 already applies in the BACI suite) should be specced properly.

### D-005 — CEH13/CEH14 exclusion is reported, not adopted

*2026-08-16*

Not adopted. The published C4 centroid remains the nine-member fit. The exclusion is **reported as a sensitivity** in report9 §5.2.3.

**Revisit if** the report is restructured such that C4's headline is regenerating anyway, or a reviewer requires the exclusion in the headline. If adopted, scope it to the **coefficient fit only** — the two wells are anomalous in dynamics, not level, and must stay in `03_regional_averages.csv`.

### D-006 — Editorial principle: published numbers stand, improvements are cited as sensitivities

*2026-08-16*

**Keep the published numbers; report the improvement as a cited sensitivity, traceable to a committed CSV.** Re-cut only when the published number is *wrong*, not when it is merely improvable.

**Revisit if** a published number is found to be wrong rather than superseded, or sensitivities accumulate to the point that the headline is no longer the best available estimate.

### D-007 — Drainage datum fixed at 3.7 m on a Darcy regime argument

*2026-08-13 rationale confirmed 2026-08-16*

`DRAINAGE_DATUM = 3.7 m`, uniform, justified on the deeper-datum Darcy argument recorded in SI Note S9.

**Revisit if** any cluster returns a negative β₃ at the uniform datum — the project rule is that a negative β₃ means the datum is wrong.

### D-008 — HEADLINE_LAG = 0 after the bucketing fix

*rationale confirmed 2026-08-16*

Rainfall enters the SSM without a lag: `HEADLINE_LAG = 0`.

**Revisit if** the measurement protocol changes.

### D-009 — Two Approach-B specific-yield aggregations, and which consumes which

*rationale confirmed 2026-08-16*

Supersedes the other — they are different aggregations and are not interchangeable. The cluster-level event median (C3 = 0.3255) is reported in Paper 1 Table 4; the median of per-well event estimates (C3 = 0.3057) is consumed by Scripts 09d/20/29/30/31/37b and is the value behind λ.

**Revisit if** a consumer is added — it must state which aggregation it takes. Note λ is referred to **by name, never by number**; there is no single correct value.

### D-010 — τ = Sy/β₃ retired as a timescale

*rationale confirmed 2026-08-16*

It is the storage–drainage index, a diagnostic. The Sy-free recession time is 1/β₃ and the reported half-life is t½ = ln(2)/β₃.

**Revisit if** never, on current understanding — this is a definitional correction, not a modelling choice.

### D-011 — No asserted results in code

*2026-08-16*

Results, rankings and superlatives are **derived at run time** from the script's own outputs, or they are not stated in code at all.

**Revisit if** never. If a finding is worth stating, it is worth deriving.

### D-012 — Mirrors are generated; claims are registered

*2026-08-16*

Markdown mirrors are **generated** from the ODTs by `tools/refresh_mirrors.py` and never hand-edited; the lints read the mirrors. `tools/cite_check.py` runs a **standing** comparison of every published value against the corpus, and evaluates `tools/claims_register.csv` for the assertions that carry no number.

**Revisit if** the editing surface changes (e.g. markdown becomes canonical and the ODTs are generated), which would invert the direction but not the principle.

### D-013 — Map extent retained at 365800 in Scripts 07, 11b and 20

*2026-08-16*

The three scripts keep 365800. A comment at each site records that this is deliberate and names this entry; no behaviour changes.

**Revisit if** the report's figures are re-laid-out and a uniform extent becomes worth the re-render, or a new script needs the extent — in which case it imports from config and joins the 365500 group, widening a split that is currently three scripts plus 11c.

### D-014 — 09d's specific-yield fallbacks aligned on default_value("Sy")

*2026-08-16*

Both now return `pipeline_params.default_value("Sy")`. The row-missing branch moves from **0.30 to 0.25**.

**Revisit if** `_DEFAULTS["Sy"]` is revised, which now moves both branches together — as intended.

### D-015 — Citation index: confirmed rows gate, unreviewed rows advise, rejections do not inherit

*2026-08-16*

Three rules. (1) Only rows a human has **confirmed** gate the build; unreviewed rows are reported as advisory. (2) A **confirmation** is inherited by every other occurrence of the same key — the judgement is made once, the locations follow. (3) A **rejection is not inherited**: it is recorded per location.

**Revisit if** the documents gain explicit citation markers, at which point the index becomes derivable rather than curated and the confirm step goes away.

### D-016 — LCSC_DATA_LIMIT is a config constant, not a per-script local

*2026-08-16*

`config.py` holds the single declaration; `model_utils` re-exports the name so `from utils.model_utils import LCSC_DATA_LIMIT` (Script 30) still resolves. Scripts 03 and 08 import it. Script 03's `MIN_OBS_PER_WELL` likewise becomes an alias of `config.SSM_MIN_OBS`. Values unchanged: 100 and 30. No fit, metric, figure or CSV changes.

**Revisit if** the per-well window is ever changed from 100. It now moves in one edit and propagates to all three consumers, which is the point — but the published per-well coefficients, the benchmark and Script 30's sensitivity all move together, so the change is a re-run of the analysis, not a tweak.

### D-017 — The duplicate top-level utils/ package is removed

*2026-08-16*

Remove. The directory is moved to `_to_delete/utils_stale_package_2026-08-16/`; the six files therefore read as deleted in `git status` and the deletion is staged by the next `git add -A` (nrg_git.sh option 2). Git history is preserved. The `git rm --cached` was **not** run from the bridge deliberately: per the 2026-08-12 ops note, git invoked through the FUSE mount cannot unlink `.git/index.lock` and leaves a stale lock behind. Martin deletes `_to_delete/` on his own machine.

**Revisit if** a second import root is ever wanted deliberately — in which case it needs an `__init__.py`, a distinct package name and a reason, not a copy of an existing name.

### D-018 — cite_check strips only real HTML tags

*2026-08-16*

Tighten to `</?[A-Za-z!][^<>]*>`: a tag must open with a letter or `!` and may not contain a further `<`.

**Revisit if** a mirror ever legitimately contains `<` inside a tag attribute, or the mirrors move to a format that needs real HTML parsing rather than a regex — at which point parse, don't widen the pattern.

### D-019 — Drainage datum geometry: surface-following, not mAOD

*2026-06-08, refined 2026-08-12*

A common **depth below ground** — a surface-following base. The datum enters the model in exactly one place, the β₃ predictor `h_disp_prev = DRAINAGE_DATUM + h_prev`; it cancels from Δh entirely.

**Revisit if** the per-well datum sweep is regenerated and the depth-on-elevation slope moves materially away from ~0.13 (e.g. above ~0.4), or the network is extended into terrain that breaks the surface-following assumption.

### D-020 — k = 5 partition, post-v1.3.0 blacklist, canonical cluster IDs

*undated*

**k = 5**, analyst-fixed (not silhouette-selected), on Ward's linkage over `1 − Pearson` between well hydrographs. Current membership: C1 Lake Edge 7 · C2 Dune 24 · C3 Western Residual 21 · C4 Main Forest 9 · C5 Coastal Forest 5 = 66 reference wells. IDs, labels and colours come **only** from `config.py` `CLUSTER_LABELS` / `CLUSTER_COLOURS` — never from the raw Ward's integers in `02_07_cluster_membership_k5.csv`, which are pre-remap and non-canonical.

**Revisit if** the blacklist changes, the extended network is folded into the clustering input, or a rerun moves the Pearson+Ward reproduction ARI off 1.000.

### D-021 — Script 16 water balance is Sy-free

*undated*

**No.** The partition is derived from SSM headspace ratios and observed recession rates. **No Sy-dependent conversion anywhere in Script 16.**

**Revisit if** a volumetric (m³) product is required that genuinely needs Sy — in which case it is a *separate*, explicitly Sy-dependent output, not a change to the partition.

### D-022 — Forest interception is a partition of the PET budget, not an addition

*undated*

`FOREST_INTERCEPTION` enters the water balance as a **partition of the PET energy budget** — not an additive term on top of PET. Applies to **both C4 and C5**.

**Revisit if** a site-specific interception measurement replaces the literature value, or a canopy-phenology term is introduced (currently one of the open candidates for the C4 semi-annual residual).

### D-023 — No hand-maintained analytical step-count headline

*undated*

**documents cite manifest fields.** There is deliberately **no** single hand-maintained "analytical headline" constant. The short-form headline is the **total registered** count.

**Revisit if** never for the framing. When a step is added or retired, the manifest moves on its own and the guard trips if a documented count no longer matches — that trip is the signal to re-read this entry, not to edit a constant.

### D-024 — λ is referred to by name, never by number

*undated*

The forest-interception drawdown reach `λ = √(Kb/(Sy·β₃))` is referred to **by name**. The render is `20_drawdown_propagation_nohead.png` (Script 20) = report **Figure 50** = Paper 1 **Figure 19**.

**Revisit if** never for the naming rule. The number is retraced on every rerun.

### D-025 — `datum_geometry_test.py` not promoted to a numbered pipeline step

*2026-08-12*

**No.** Instead, state the derivation in the methods, naming the committed CSVs the slopes are read from.

**Revisit if** the diagnostic starts being cited in more than one document, or needs to be rerun routinely rather than once.

### D-026 — Never write ODT files through odfpy

*undated*

**read** and flatten with odfpy if useful; **write** by editing `content.xml` as text and rezipping with `mimetype` stored first.

**Revisit if** never, unless odfpy fixes the round-trip and it is verified byte-identical on a real project document.

### D-027 — Retirement hygiene: a retirement triggers a documented sweep

*2026-08-14*

A retirement is **one Decision Log entry carrying a full removal checklist**, not just a code deletion.

**Revisit if** the checklist proves too heavy in practice — in which case trim it, but keep item (4), which is the one that actually failed.

### D-028 — An observational metric does not inherit SSM-failure exclusions

*2026-06-27*

**No. Blanket-include.** The amplification coefficient excludes the lake gauge only. The *calibration* regression (amplification vs β) separately drops the SSM-unreliable wells, because there β is the untrustworthy axis.

**Revisit if** the amplification coefficient ever acquires an SSM-derived input, at which point the independence argument lapses.

### D-029 — One decision log, at the repo root

*2026-08-16*

This file, at the repo root, is canonical. The ten decisions that existed only in the ledger copy are imported verbatim as D-019 to D-028; the seven that existed in both keep their root ids, with the old ledger ids recorded in the mapping table above. `ledgers/DECISION_LOG.md` is replaced by a stub pointing here, and `tools/decision_lint.py` now fails if a second decision log appears anywhere in the tree.

**Revisit if** the ledger family grows a genuine need for decision records scoped to one ledger — in which case they are sections of this file, not a second file with its own numbering.

### D-030 — The clustering basis stays the full record; month-wise stability is disclosed

*2026-08-16*

The partition stays on the full record. **Month-wise stability is added to the pipeline and reported alongside the existing well-wise bootstrap**, and both month-wise statistics are published.

**Revisit if** a well's *character* is shown to change materially within the record — a genuine regime shift rather than sampling noise. The pre/post halves agree with each other (ARI 0.733) better than either agrees with the full record, which argues against it, but that test is coarse. Also revisit if k is reopened: month-wise reproducibility this flat is consistent with the underlying structure being a gradient with five defensible cuts rather than five natural kinds. Nothing published depends on the clusters being natural kinds, but the question is fair and is better answered before a referee asks.

### D-031 — Cluster membership is not an intervention detector — tested and dropped

*2026-08-16*

Tested, negative, dropped. Do not rebuild it.

**Revisit if** a future intervention is large enough to break the correlation structure rather than shift the level — a hydrological disconnection rather than a canopy or surface change.

### D-032 — The "≥100 months" transferability claim is scoped to fitting, not to the partition

*2026-08-16*

It supports admission and model fitting. It does **not** support a reproducible partition, and the claim is rescoped to say so.

**Revisit if** the partition is re-derived on a basis whose reproducibility is measured rather than assumed — in which case quote that method's own figure, not this one.

### D-033 — One window: cluster coefficients move to the comparison window

*2026-08-16*

*(withdrawn — see above)* Martin's call, 2026-08-16 was **the 100-month comparison window.** Centroid fits move to it, so Table 3, Figure 48 and the benchmark share one basis and the report tells the reader about one window rather than three. The full-record values are **cited as the sensitivity**, explicitly, wherever they change a conclusion.

**Revisit if** a future analysis needs record-average rather than current-state cluster coefficients, or C4's window-basis non-significance proves load-bearing for a conclusion the sensitivity citation cannot carry.

### D-034 — Two bases, both published; scenarios stay single-numbered

*2026-08-16*

**Keep both bases; publish both.** Nothing is re-cut. Table 3 prints the full-record and comparison-window estimates **side by side for all five clusters**, from the new `03_14_centroid_window_sensitivity.csv`. The scenario layer keeps **single** numbers, on the published full-record coefficients; the current-state contrast is reported **once, as a sensitivity**, not as a parallel set of scenario outputs. The window policy is explained in the methods through the record-basis table rather than by making the pipeline uniform.

**Revisit if** the scenario current-state sensitivity comes back material — a measured reason to reopen, rather than the aesthetic one that opened it. Note also that a reader who finds the report leaning on "but on the full record…" repeatedly in the C4 narrative is seeing the same signal.

### D-035 — Stores carry computed precision; rounding is a display step

*2026-08-18*

**No. Stores carry what the pipeline computed; rounding happens where a number is displayed.** The three-decimal convention stands as a display rule, with one rider: **values below 0.1 are shown to three significant figures rather than three decimal places.** Store-time rounding removed from `report_numbers_utils`, `pipeline_params`, and Scripts 17, 18, 09a, 10a and 10h.

**Revisit if** a consumer is found that depends on a stored value being pre-rounded, or the display rider proves ambiguous at a real call site.

### D-036 — Thornthwaite heat index on a trailing 12-month window

*2026-08-18*

Sum `I` over the **trailing 12 months ending at the month being computed** (Martin's proposal). The first eleven months of the record, which have no complete window, are back-filled from the first that does.

**Revisit if** the record is only ever analysed at complete calendar years, in which case the classical form is preferable for citability; or a source of the station's own published PET becomes available, which would supersede computing it at all.

### D-037 — The residual field does not adjudicate CEH14; ridge recharge stays a named candidate

*2026-08-18*

**No on both counts.** The residual field stands as a **network-level** result and is retained as such. It does **not** adjudicate the two wells whose beta_3 is itself anomalous (CEH14, CEH13). Ridge-derived recharge is retained across the corpus as a **named, unconfirmed candidate** at CEH14 specifically — neither asserted as the mechanism nor excluded.

**Revisit if** a fit resolves CEH14's beta_3 positive without adding a term to the three-term SSM (both the full record, -0.0146, and the comparison window, -0.0207, are currently negative and neither is significant); **or** a monitoring point is installed between CEH14 and the ridge toe, which would let the source head be observed rather than inferred and would make the amplitude-ratio question decidable.

### D-038 — One per-well WTF Sy table, named for the script that writes it

*2026-08-19*

Retire the `17_`-named copy. `OUT_18_WELL_SY_TABLE` (`18_wtf_01_well_sy_estimates.csv`) is the single path; all eleven consumers now read it. `INT_WTF_WELL_SY` is **removed** from `paths.py`, not aliased, so a stale importer fails loudly.

**Revisit if** Script 17 is ever changed to produce a per-well table of its own, in which case a `17_`-prefixed file becomes correct and the two aggregations need re-separating; or the 18-series output directory is restructured.

### D-039 — The cluster attribution declares a balanced basis; c is not a climate background

*2026-08-19*

The decomposition is computed against a declared **balanced** observed basis: `observed_balanced_annual_mean_mm_yr`, the OLS slope of the annual cross-well mean of the per-well seasonal metric over the same well-set as 25_02. The basis is named inside the file by a literal `decomposition_basis` column. The centroid slope and the per-well mean are retained as context columns and are no longer subtracted from. `c` is reported as `far_field_offset_mm_yr` — its literal meaning — beside a new `climate_cwb_mm_yr` = 1000·β_cwb·d(CWB)/dt, because **c is not separately identified**. Every column whose meaning or basis changed was renamed rather than reused (`predicted_climate_mm_yr` → `far_field_offset_mm_yr`, `predicted_total_mm_yr` → `modelled_total_mm_yr`, `residual_mm_yr` → `unexplained_mm_yr`, `*_pct_of_observed` → `*_pct_of_basis`), so a stale reader raises a `KeyError` instead of silently reading a different quantity.

**Revisit if** the panel gains a covariate that pins the level independently of the CWB (an absolute-datum or regional-network constraint), in which case `c` becomes identified and the two columns can be collapsed; or the per-well record windows are equalised, in which case the per-well mean and the balanced basis converge and the distinction stops earning its place.

### D-040 — The matched-window refit is reported, not adopted

*2026-08-19*

Not in this change. The refit is emitted to `25_11_matched_window_sensitivity.csv`, marked `status = reported_only_not_adopted`, and nothing downstream reads it. The published δ₀ and L in 25_01 stand.

**Revisit if** the owner decides the far-field constant must be estimated on a common window; or the network gains enough long-record wells that the split stops changing the answer.

### D-041 — A document's in-text version is derived from its filename; the date follows only when the number moves

*2026-08-19*

The filename is authoritative. `tools/doc_version_sync.py` derives the version from the `_v1_9_24` suffix (underscore-separated integers, joined with dots -> 1.9.24) and writes it into the document; the disagreement is a `tools/check_all.sh` gate. The month and year are refreshed from the live file's mtime ONLY when the version number itself changes, and the gate never looks at them. A version-string sync is bookkeeping, not an edit batch, so it edits the live file in place and does not bump the filename.

**Revisit if** documents start carrying a release date distinct from their last edit (a publication date), in which case the parenthesis is no longer a function of the file and must be typed and gated separately; or the repository gains a mechanism that preserves mtime across clones, which would make the date gateable.

### D-042 — The far-field level is drawn as a band, and the coastal/climate crossing is retired

*2026-08-19 · **superseded***

Stop drawing a far-field driver and stop computing a crossing. The coastal reach is unchanged. In its place the panel draws a **band** spanning `identified_sum_mm_yr` (c + β_cwb·d(CWB)/dt) across **every** matched-window specification in `25_11_matched_window_sensitivity.csv`, accumulated over the same horizon as the coastal curve, labelled as a far-field *level* that is not separately identified and whose sign is unresolved. No specification is selected by name: the band is the min and max of that column, so it tracks the table rather than this file. Removed: the flat climate line, the crossing marker and its annotation, the `cross_x` return, the `crossing_m` key on `mechanism_fig_utils.load_reach()`, and the `climate_5yr_head_mm` / `climate_20yr_head_mm` columns of `09f_01_reach_profile.csv` (replaced by `far_field_level_lo_head_mm` / `far_field_level_hi_head_mm`, signed, on the coastal 5-yr basis).

**Revisit if** the far-field level becomes separately identified (a design that breaks the offset/CWB-trend trade-off, or a covariate that carries no trend over the fitted span), in which case a level with a sign can be drawn and a comparison with the coastal term becomes meaningful again; or the owner adopts a matched window (D-040's Revisit-if), which would change what the band spans.

### D-043 — Nothing replaces the flat climate line; panel (a) returns to five curves

*2026-08-19 amended 2026-08-19*

Empty. The band is withdrawn. Panel (a) is five distance-decay curves — scrape dipole, standing pine, thinned forest, 6 m acute storm, 5-year coastal accumulation — plus the measured anchors and the reach-L rule. Script 09g follows *for the band only*: no band is drawn there either, and `load_reach()` emits no `far_field_lo/hi` keys. (Per the amendment above, 09g does still draw the far-field term itself, signed, from 25_01, and its stack and the lay figure keep their three panels.) The two `far_field_level_*` columns of `09f_01_reach_profile.csv` and the four `pipeline_params._DEFAULTS` fallbacks that supported them are retired with it.

**Revisit if** the far-field level becomes separately identified, in which case a term with a sign and a magnitude can be drawn and compared; or a future reviewer asks why the panel shows no site-wide term, which is a caption question, not a figure question, and is answered from 25_11.

### D-044 — The far-field constant is a window statistic, not a rate

*2026-08-20*

`c` is **identified but not interpretable as a rate**. No far-field rate is quoted in any document. Where the site-wide decline needs an account, it is treated under the existing β₁ / seasonal-redistribution argument, not here.

**Revisit if** the record lengthens enough that the far-field series stops being dominated by multi-year excursions, at which point a window-stable asymptote would be a different object from this one and could be re-examined. A single window agreeing with the observed trend is **not** sufficient — the sweep shows agreement occurs by coincidence at some starts.

### D-045 — The coastal panel's well-inclusion policy

*2026-08-20*

Three rules, all in `load_panel` and `apply_scrape_treatment`: (a) extended-network wells take their cluster from the sitewide Pearson audit's `Best_Match_Cluster`; (b) wells installed after their scrape are dropped entirely, wells scraped mid-record are censored at the scrape date; (c) ceh4 is retained in full.

**Revisit if** a further scrape is cut, or a post-install well accumulates enough post-scrape record to support a censored rather than dropped treatment. Any new scrape well is classified by **when it was installed relative to the cut**, not by its distance from the footprint.

### D-046 — Forest-free means not under canopy, not "not in C4/C5"

*2026-08-20*

**Land cover.** `exclude_forested` keys on the `in_forest` flag Script 01 derives from the committed plantation outline. The headline δ₀ moves from −26.42 to **−31.33 ± 1.97** (L = 895 m) on 61 wells. The canopy-controlled full-network fit is reported alongside it, and its agreement is the evidence that the forest is not driving the gradient.

**Revisit if** the plantation outline changes — a clearfell moves the boundary and wells change class — or the network gains near-shore wells that reduce ceh3's leverage. **δ₀'s sensitivity to ceh3 is stated wherever δ₀ is quoted**; a single well carrying 2–4 mm/yr of a headline is a fact about the network, not a defect to be hidden, but it must not go unmentioned.

### D-047 — The headline coast-edge rate is quoted at 150 m, not at d = 0

*2026-08-20*

**Neither question needed answering, because the headline was being quoted in the wrong place.** The headline is now the fitted trend at `config.COASTAL_REFERENCE_DISTANCE_M` = **150 m**, emitted as `Headline_coastal_rate_at_ref`: **−26.18 mm/yr, delta-method SE 1.45, 95 % CI [−29.0, −23.3]** on the forest-free linear-capped fit. δ₀ and L remain in `25_01` as fitted parameters, and δ₀'s note in `25_report_numbers.csv` now labels it an extrapolation and points at the new key.

**Revisit if** the network gains a well closer than 150 m, which would allow the reference to move shoreward and should prompt asking whether it ought to; or the near-shore wells are lost, at which point the guard fires and the constant must move inland. **Do not move the reference distance to make a number look better** — it is set by where the data starts, not by what it yields.

### D-048 — ceh12 leaves the coastal-gradient population

*2026-08-20*

Excluded from **every** coastal-gradient specification via `config.COASTAL_GRADIENT_EXCLUDED_WELLS`, applied in `load_panel()` before the cluster restriction so no fit can pick it up. Martin's ruling, 2026-08-20.

**Revisit if** other wells are identified on the ridge — ceh12 is currently a clean outlier rather than the top of a continuum, which is what makes a single-well exclusion right; a set would want a geometric criterion instead of a name. Also revisit if the ridge is ever shown to be hydraulically connected to the dune aquifer over the study window.

### D-049 — The far-field term leaves the 09g mechanism figures

*2026-08-21*

It is removed from the 09g reach figure, the reach stack and the lay-drivers figure. `uniform_offset_table()`, the `FARF` palette entry and the `far_field_*` keys `load_reach()` emitted are retired with it. The grid's driver count is now **derived from the driver register rather than typed**, so it cannot go stale again; it renders "Three drivers". Martin's ruling.

**Revisit if** the far-field level becomes separately identified *across* windows, not merely within one — which is a different and stronger condition than D-043's revisit clause, and is what D-044's amendment shows is not currently met.

### D-050 — A far-field control tier, and what it revealed about the BACI corroboration

*2026-08-21*

Build `FAR_FIELD_CONTROL_WELLS` = **nw4b, wmc1, ceh5, l7, ceh6** — five open-ground wells beyond 1.6 × the fitted reach, mean 1946 m, contrast 1393 m against WMC3. Admission is a **multiple of the fitted reach**, not a typed distance, so the criterion moves if the reach does. The tier does **not** join the `Combined` control set: folding it in would move a published number for no analytical gain.

**Consequence.** `baci_absorbs_mm_yr` is a **nuisance parameter fitted to absorb whatever the model leaves**, not an independent estimate of the gradient. Comparing it against the gradient model's single prediction is a category error, and the agreement on the Forest tier is as much an artefact of that tier's narrow span as the disagreement elsewhere is of a wide one. **The BACI leg of the coastal-gradient corroboration is withdrawn.** The easting × time term continues to do its actual job in Script 10a — absorbing the easting-correlated trend so it cannot alias into the felling steps — and nothing about the published clearfell results changes.

**Revisit if** the ANCOVA replaces its linear easting × time covariate with a distance-decay term of the same form as the gradient model, at which point the comparison becomes meaningful and the tier becomes the test it was built to be. That is the constructive route out of this, and it is a Script 10 design change.

### D-051 — The CCW 1989–96 block enters the pipeline as a raw input

*2026-08-21*

Script 39 is registered in Phase 16 as an analytical-default step and reads two files that no earlier step produces: `data/ccw_1989_1996_depths.csv` and `data/ccw_1989_1996_code_map.csv`. This is a documented exception to the rule that scripts never read raw inputs unless they are Script 01, in the same class as Scripts 09/10 for the BACI and Script 24 for sunshine hours.

**Revisit if** the historic block is ever extended to a size where it should join the cleaned matrix properly — a second recovered epoch, or the FC well records reduced to the same datum — at which point the right answer is a Script 01 branch with an epoch flag, not a second edge-reading step.

### D-052 — The Paper 1 SI definition of the LCSC

*2026-08-21*

The definition is wrong and is replaced. LCSC is `100/β₁`, and Section S6.4 now says so, gives the dimensional argument, states the *lumped* caveat, and names its source file. The **name is canonical and unchanged**.

**Revisit if** a script is ever added that emits a variance-decomposition statistic for the climate terms. That would be a genuinely new quantity and needs its own name and symbol — it must not reclaim "LCSC", which is in the abstract and four other places.

### D-053 — The forest reach is quoted at 230 m, on the figure as well as in the prose

*2026-08-22*

**230 m everywhere, including the figure.** Twenty-one occurrences across seven documents now read 230, and Script 20 renders the annotation and its console line through `quote_reach_m()`, which rounds to `config.REACH_QUOTE_NEAREST_M`.

**Revisit if** Sy or β₃ moves enough to carry λ across a rounding boundary — past 235 m or below 225 m. At that point the quoted figure changes and every document moves with it, which the SPREAD check (D-054) now makes visible in one run.

### D-054 — The sweep asks two questions, not one

*2026-08-22*

A second check, **SPREAD**, added at `cite_check` v1.9.0. Alongside "does the corpus quote the committed value?" the sweep now asks **"does the corpus quote the same value everywhere?"**, and reports the distinct set of renderings found near a quantity's anchor. Values of magnitude ≥ `LARGE_VALUE_MIN` are also searched at dp = 0 in the same release.

**Revisit if** the registered set grows past a handful of quantities and the per-quantity exclusions start duplicating `symbol_register.csv`. At that point the right move is to read the anchors out of the symbol register rather than maintain two lists, and this entry is the reason not to do it prematurely — the two registers answer different questions and only overlap on the symbols.

### D-055 — The drainage datum becomes z₀, in the equations as well as the prose

*2026-08-22*

The datum becomes **z₀**. Diffusivity keeps D: it is standard in groundwater hydraulics and not ours to reassign. The rename covers **62 prose occurrences across six documents and four embedded equation objects in report8**. `DRAINAGE_DATUM` keeps its name in code.

**Revisit if** a downstream tool is ever built that parses the equations rather than rendering them. z₀ as MathML is `<msub><mi>z</mi><mn>0</mn></msub>`, which a naive parser reads as a subscripted variable rather than a named constant.

### D-056 — Near misses carry a heavier anchor than exact hits

*2026-08-22*

The sweep was finding both real drift and coincidences, and the two are now separated. The anchor test is **permissive for an exact hit and strict for a near miss**: a near miss must sit near a SUBJECT anchor *and* a QUANTITY anchor, where a key naming both is split into the two groups. Triage falls from 195 rows to 119 while recognised citations **rise** from 258 to 267.

**Revisit if** a real drift is ever found to have been hidden by the strict near-miss anchor. The failure mode to watch is a document that reports a number without naming the quantity anywhere near it — in which case the document has a problem the sweep is right not to paper over.

### D-057 — The site-wide climate term leaves the driver ranking

*2026-08-22*

The climate term is **listed but not ranked**. The report no longer states that climate is the largest driver, and no site-wide rate is quoted. Coastal retreat becomes the reference term, at −85 mm site-mean over twenty years. The direction of the climate effect is retained and sourced to the other evidence in the same chapter; only the magnitude goes.

**Revisit if** the panel gains a covariate that pins the level independently of the CWB — the same condition D-039 names — in which case `c` becomes a rate and can be ranked; **or** the record lengthens enough that the site-mean trend clears its detection floor. On the current spread that needs roughly a doubling of the record, which is the same conclusion the record-length analysis reaches for every other rate in this study.

### D-058 — The unexplained uniform decline is quantified and ranked

*2026-08-22*

The site-wide decline is quantified as the **unexplained uniform decline**, at **−11.0 mm yr⁻¹**, ranked first on the site-integrated footing at −220 mm over a twenty-year horizon against coastal retreat's −85 mm — **as a central estimate the record does not resolve**, and stated as such wherever it appears. Script 37b's uniform row is sourced from it instead of from `c`.

**Revisit if** a per-cluster standard error is computed for the balanced basis, which would let the uniform term carry a real interval instead of inheriting the site-mean floor; or the record lengthens enough to clear that floor. Either would turn a central estimate into a rate and the ranking would stop needing its caveat.

### D-059 — The SSM over-predicts head where the water table reaches the surface

*2026-08-22*

It is a property of the model, it is measurable in the committed modern record, and it is recorded as a limitation of the SSM's functional form at wells whose water table reaches their own ground surface. **No published coefficient, step or gradient changes.**

**Revisit if** the residual-versus-level relationship is emitted as a committed artefact rather than a working note, at which point the bias could be quoted per well and a corrected scenario Δh offered for slack wells; or a non-flooding comparison group with data above −0.25 m becomes available, which would separate surface bounding from a general high-level nonlinearity. The non-flooding wells also trend negative toward their own shallowest levels, so that separation is not yet clean.

### D-060 — The long-run coastal retreat rate is measured, and is a quarter of the twenty-year rate

*2026-08-22*

The long-run rate is measurable. From OS Anglesey XXV.NW (revised 1899) against the 2015 DEM, the dune edge retreated a **median 75 m in 116 years = 0.65 m yr⁻¹**, and the high-water line **137 m in 127 years = 1.08 m yr⁻¹**. **The dune-edge figure is the citable one.** Neither committed constant changes.

**Revisit if** the measurement is scripted so it reproduces from committed inputs rather than living in a working note; the MHW definition drift is quantified, which would make the 1.08 m yr⁻¹ tidal figure citable too; or an intermediate epoch (1920s revision, 1940s–50s aerial photography) is added, which would test whether the acceleration is real or an artefact of comparing a long-run mean with a storm-weighted window.

### D-061 — Script 10a is principal for the clearfell step; Script 10k for the zone comparisons

*2026-08-23*

**+113 mm, Script 10a, is the §4.6 headline for the Impact step.** Script 10k is principal for **comparing zones** — Impact against Edge against C3/Warren — where a single coefficient vector and covariance matrix make the zones exactly subtractable. Martin's ruling, 2026-08-22. The 10k docstring's primacy claim is retired under D-011 (10k v1.3.1); no code path, output or committed value changes.

**Revisit if** the Impact zone gains a second well, which would remove ground (2) and make the pooled estimate competitive for the step as well as the comparison; or a normalisation is found that reconciles the paired and pooled estimators on the same contrast, at which point the sign disagreement above becomes a resolvable quantity rather than a stated tension; or Script 10f is changed to form the Impact-minus-control contrast itself, which would make the −21.9 mm a committed value and require the panel description to be rewritten around it.

### D-062 — z is the test statistic, z₀ is the datum, and the register may hand z to nobody

*2026-08-23*

**the bare letter z belongs to the standard-normal test statistic; z₀ belongs to the drainage datum; no register sense may be re-lettered onto either.** `d_depth` is **retired**, not re-lettered, with the replacement `(rewrite as: −h, depth below ground)`. And where a comparison survives at all, **report the difference with its standard error rather than a z ratio** — the difference is the informative quantity and the ratio hides it.

**Revisit if** a second standard-normal statistic enters the corpus under a different name, or a register sense arrives whose conventional glyph genuinely is z — at which point `RESERVED_GLYPHS` needs an owner recorded rather than `None`.

### D-063 — `living/` is a separate lane from the report, and stays one

*2026-08-23*

`living/` remains a **separate operational lane**. It is not a chapter of the report, its outputs are not report artefacts, and it is not run by `run_analysis.py`. `living/forecaster_monthly_update.sh` stays gitignored; `tools/*.sh` is admitted (see below). Nothing here changes what `living/` does.

**Revisit if** the report ever needs to quote a level more recent than the last pipeline rerun. That is the only thing that would make the two lanes want to share a data path, and it should be answered by rerunning the pipeline on a later extract rather than by reading the living hub.

### D-064 — The report is a technical record; Papers 1 and 2 are what gets defended

*2026-08-23*

**develop it as a technical record, alongside the Methods Supplement. Paper 1 and Paper 2 are the outputs that have to be defended.** Nothing is deleted to make the report smaller.

**Consequence.** a Paper 2 methods supplement is a required deliverable, not an improvement. Its contents are a selection from S.6, S.7, S.14, S.15, S.15c, S.18 and S.20, adapted from record voice to paper voice; S.1–S.5 and S.10–S.13 stay deferred to Paper 1's SI, which is what the seventeen cross-references already assume.

**Revisit if** a journal requires the technical record itself as supplementary material at a length it will not accept, which would make the report's size a publication constraint rather than a readability one — a different question from the one settled here.

### D-065 — Paper 2 claims its transferability, and the structured abstract honours D-057 by naming only what the fit identifies

*2026-08-23*

**a new §5.6 that claims the mechanisms and explicitly disclaims the magnitudes; and a 225-word abstract that ranks the interventions only against coastal-retreat drawdown.**

**Revisit if** the target journal changes and the 225-word structured abstract is no longer required, in which case the D-057 caveat should be restored to the abstract in full rather than left to the body — the structural honouring above is a consequence of the word limit, not a preference.

### D-066 — `cite_check` becomes unit-aware for metres quoted in millimetres, and M23 is answered by M31 rather than fixed

*2026-08-23*

**the checker converts, metres to millimetres, gated at three significant digits and behind the strict anchor. The documents are not standardised. M23's rule is not adopted; the tightening it wanted ships inside M31's pass and nowhere else.**

**Revisit if** the millimetre pass's precision falls below about 80% as the corpus grows — in which case the gate goes to four significant digits and the pass admits almost nothing, and the durable answer becomes teaching `build_citation_index.py` to propose millimetre renderings so the rows are confirmed by hand once rather than re-adjudicated on every run.

### D-067 — §4.10 lands by relocation, and the cross-reference re-point is scoped to references that were correct before the move

*2026-08-23*

**the permutation is applied only to references that were demonstrably correct before the move. References that were already wrong are corrected by meaning, one at a time, against a unique text anchor and with the reason recorded (`tools/fix_stale_refs.py`). References in a form the re-pointer cannot read — the § symbol, and abbreviated "Fig 59" — are left alone and raised, because at least some of them are stale on an older baseline and permuting them would replace one wrong number with another.**

**Revisit if** the § audit lands and finds the § references were in fact uniformly pre-move after all — in which case the caution here cost one pass of hand-checking and the permutation could have been trusted. That is the cheap side of the trade; the expensive side is a corpus of confidently wrong numbers that no gate can see.

### D-068 — a reference form the re-pointer cannot read is a gate failure, not a silent skip

*2026-08-23*

**no. The regex is fixed (`(?!\d)(?!\.\d)`), captions are excluded by construction through `_caption_ranges()` rather than by the accident of chapter-prefixed numbering, and the class of references the broken pass could not have touched is repaired through an explicit `--missed-only` switch rather than by re-running the pass. But the durable part is that the reference lints must stop reporting success on a corpus they cannot fully read.**

**Revisit if** `--missed-only` is ever reached for again. It exists to finish one specific broken pass and is a no-op on anything else; a second use would mean the same bug had been reintroduced, and the answer then is the gate, not another repair switch.

### D-069 — a wrong renumber plan is corrected in a second file, and a reference is re-pointed only where evidence says which number it meant

*2026-08-23*

**the plan is not edited. `renumber_plan.csv` records what was applied; the fix is a second file, `renumber_plan_correction.csv`, carrying its own reasons. And a reference is re-pointed only where the corpus itself says which number it meant — the script named beside a figure, the figure cited beside a section — with the unevidenced remainder moved on the strength of a measured agreement rate and said to be an inference.**

**Revisit if** a § reference outside the evidenced 21 is later found pointing at the wrong section. The inference above would then have a counterexample, and the answer is not a better heuristic but more evidence — the cheapest source being a declaration of which section each figure belongs to at the point the figure is placed, rather than recovered afterwards from heading order.

### D-070 — a missing rainfall month is read as missing, the record is not truncated, and the long-record rainfall figures become committed keys

*2026-08-23*

**it is read as missing. The record is NOT truncated: the month is excluded, not the eleven years before it. And the long-record rainfall figures the discussion turns on become committed keys in Script 00, because they were prose.**

**Revisit if** another "---" appears as the record extends. One missing month in 95 years is why the complete-years rule costs almost nothing; a run of them in the recent record would make exclusion expensive and the question would become interpolation, which is a different decision with a different burden of proof.

### D-071 — a tool never names a document version

*2026-08-23*

**no. The version is resolved, never typed. `refresh_mirrors.resolve()` already knows which file is current, and every tool that needs a versioned document now asks it through `repoint_refs._versioned()`.**

**Revisit if** a tool genuinely needs a specific historical version — a comparison against what a document said at v1.9.45, say. That is a different operation from "the current document" and should look nothing like it in the code, so that the two can never be confused.

### D-072 — an embedded figure is checked against the output it declares, and re-embedded by content rather than by position

*2026-08-23*

**each embedded entry is identified through git history — the revision of the declared source whose bytes ARE embedded — never by document order. Where no revision in a file's history is embedded, the figure is NOT replaced and the declaration is treated as suspect.**

**Revisit if** a figure is ever inserted into a document from somewhere other than a committed pipeline output. The whole method rests on the source being tracked, so an image pasted in from a desktop has no history to match against and will read as "declaration probably wrong" forever. If that becomes common the answer is a declared provenance at insertion time, not a cleverer matcher.

### D-073 — a mirror is verified by regenerating it, not by its timestamp — and two reported tool defects were mine, not the tools'

*2026-08-23*

**neither was true, and nothing needed fixing. `cite_check` recognises 19 Script 00 keys including both numbers named. Pandoc 3.1.3 reproduces all 23 committed mirrors byte for byte. What ships instead is `refresh_mirrors --verify`, which regenerates every mirror and compares bytes — the check whose absence let the second claim stand for four hours.**

**Revisit if** `--verify` ever reports DRIFT. It has exactly two causes and the output names both — the source changed since the mirror was written, or this pandoc differs from the one that wrote it — and regenerating separates them: if the content then changes the mirror was stale, and if it does not the two pandocs agree after all.

### D-074 — the driver synthesis follows the mechanisms it weighs; and a figure declaration keyed on position does not survive a reorder

*2026-08-23*

**the section. The synthesis and its comparative-footing subsection move whole, becoming §4.11 and §4.11.1 after the coastal section, and Scenario Analysis becomes §4.12. Every forward reference becomes a backward one and the reader meets each driver before the comparison of drivers.**

**Revisit if** another block moves inside a sub-document. The sub-figure ids shift again, and until `figure_table_sources.csv` is keyed on the source filename the re-keying has to be repeated — with `ref_audit` as the thing that notices if it is forgotten.

### D-075 — inputs live in the constants files and are checked there; fitted results live in report-numbers files and stay out of Methods

*2026-08-23*

**the line is between inputs and results, and it is the same line the report draws between Methods and Results. Inputs live in `config.py` / `pipeline_params.py`, which `cite_check` now reads as value sources. Fitted results live in report-numbers files and are quoted in Results. δ₀ does NOT go into a constants file: it is a fit, and a fitted value written into a constants file is a hard-coded result that can drift from the fit that produced it — the thing `pipeline_lint --check literals` exists to catch.**

**Revisit if** a constants file starts carrying anything that is not an input. The whole arrangement rests on that separation, and the day a fitted value is parked in `config.py` for convenience, `cite_check` will faithfully confirm the prose agrees with a number that no longer agrees with its own fit.

### D-076 — the coastal drift covariate is re-parameterised, not re-fitted: `s_coast` free is canonical, fixed at 1 is the sensitivity

*2026-08-28*

**adopt the re-parameterisation with `s_coast` FREE. Report `s_coast` fixed at 1 as a sensitivity, not as the headline.** Martin, on the recommendation below.

**Revisit if** the BACI ever moves to a pooled per-well design like 10k's. There `easting_x_time` is a genuine spatial interaction rather than a rescaled time trend, the equivalence in this entry does **not** hold, and substituting δ(d_w) is a real design change with a real answer.

### D-077 — a document renders a committed value by rounding half away from zero, never by truncating

*2026-08-28*

**round half away from zero at the precision the document itself uses.** Truncation is a defect, not a house style.

**Revisit if** a document needs a *deliberate* coarser rendering — a public summary rounding to the nearest hundred, say. That is a different act from truncating a millimetre and should say so on the page ("roughly", "about"), as the public summaries already do.

### D-078 — the CWB² × clearfell curvature result is withdrawn

*2026-08-28*

**the prose. The significance claim is withdrawn** from report9 §4.6.2, report10 §4.12 and §5, and the Methods Supplement. Martin, on the recommendation.

**Revisit if** a second felling event, or a longer post-felling record, gives the interaction the power it currently lacks. The estimate's sign is the thing to test again, not the claim.

### D-079 — report §4.2.3 stands on the live identifiability outputs; the constrained-fit sweep is not reconstructed

*2026-08-28*

**Rewrite the paragraphs.** The drainage-share sweep across the β₃ range (24 / 31 / 34 / 56 %) and the closure-residual percentages are dropped. Nothing is reconstructed, and no constrained fit is reinstated.

**Revisit if** a future Script 30 emits a drainage-share sweep as a live output, at which point the fuller paragraph can be restored from it — but on the identifiability framing, not the triangulation one.

### D-080 — the prose record is tiered and queried, not read

*2026-08-28*

**Tier the record by whether it must be read or merely reachable, and make the reachable part queryable at the moment of use.** Tier 0 (read every session, capped at **250 lines of prose** — the one-line-per-decision index is excluded, since it grows with the log and that is the right price; `session_handover.py` measures and reports the figure every time it runs, because a cap nobody measures is a wish): `working/HANDOVER_BOOTSTRAP.md`, the generated `HANDOFF_<date>.md`, and `working/DECISION_INDEX.md`. Tier 1 (never read whole; query): `DECISION_LOG.md` and `NRG_WORK_REGISTER.md`, through `tools/context_for.py`. Tier 2 (reference on demand): everything else. **Nothing joins Tier 0 without something leaving it.**

**Revisit if** Tier 0 creeps past ~250 lines, or `context_for.py` starts returning so many matches per query that the ranking stops discriminating — at which point the fix is a better index, not a longer read.

### D-081 — the historic OS scan stays out of the repository, and its attribution travels with the derived vector

*2026-08-28*

**Yes, it stays out** — but as a choice, not a prohibition. And the attribution it carries is owed by `coast1900.kml` and by everything derived from it, whether or not the scan is ever published.

**Revisit if** the papers move to an open-access venue under a compatible licence, at which point share-alike stops being an obstacle and committing the scan would improve reproducibility.

### D-082 — the broadleaf restock year is 1995, and site_boundary.kml is a stream-network mask

*2026-08-29*

**The restock year is 1995**, used consistently everywhere. **`site_boundary.kml` is the GRASS-derived stream network of the study area** — Martin's own, the source from which `streams.kml` was made, and used in the pipeline as a mask. The catchment is the unit of study, this being a hydrological study, so a catchment-derived mask is the right object and the filename is a description of its role rather than an error.

**Revisit if** a primary forestry record gives a restocking date other than 1995, or `f_2005` is revisited — at which point the ten-season basis is the starting point, not seven.

### D-083 — intervention dates are the author's recollection, and are recorded as such

*2026-08-29*

**Martin's recollection**, stated by him on 2026-08-29, with one exception: `config.py:508` records CEH36 as the *"documented April 2015 dune-scrape site"*, so that one has a source. **This is recorded as a stated limitation, not left implicit**, and belongs in the methods text.

**Revisit if** a felling or scraping record is located that gives a different date — in which case centralise **first**, then change the value once.

### D-084 — intervention dates are centralised in config.py; the clearfell date and the post-felling era boundary are different things

*2026-08-29*

The four intervention dates live in **`config.py` as ISO strings**, and every other module builds from them. `CLEARFELL_DATE` is added as the unambiguous alias; `INTERVENTION_DATE` is kept as the legacy name because twelve modules import it.

**Revisit if** a felling or scraping record gives a different date. Change it in `config.py` and nowhere else — which is the point of this entry, and matters because D-083 records that these dates are recollection and may yet move.

---

84 decisions. Generated by `tools/build_public_decisions.py`.
