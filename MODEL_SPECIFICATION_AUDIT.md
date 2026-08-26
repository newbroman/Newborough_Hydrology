> ## Recovered 2026-08-26 — READ THIS FIRST
>
> Written **27 April 2026**, never committed, recovered from Trash under T-10 and
> kept **verbatim below** — it is a dated record and is not edited.
> `src/23_ridge_recharge_lag_test.py:96` cites it for Scientific Question B.
>
> **Its authority line is no longer true.** The document opens "This document is
> the definitive SSM specification. Any script that fits, simulates, or consumes
> SSM coefficients MUST conform. No exceptions." It is not: it is the April 2026
> specification, and one clause of it has since been superseded by a recorded
> decision. Read it as history and as a rationale, not as a build contract.
>
> **What is still current** (checked 2026-08-26 against the tree, not assumed):
>
> - `DRAINAGE_DATUM = 3.7` — unchanged in `utils/config.py`.
> - The displacement formulation `h_disp = DRAINAGE_DATUM + h_depth`, and the
>   rule that Δh is differenced from the raw series while only the β₃ predictor
>   uses `h_disp`.
> - The sign conventions, and the β₃ soft-assertion.
> - The column-name standard. The rename it ordered is **complete**:
>   `beta_3_internal_brake` has zero occurrences anywhere in `src/`.
> - Section 15's nuance — that the depth-PET extinction term stays raw depth
>   while the β₃ design column uses displacement — still holds and is still the
>   easiest thing in the pipeline to get wrong.
>
> **What is superseded:** the equation at line 15 is written `β₁·P(t−1)`.
> The canonical pipeline is **`HEADLINE_LAG = 0`** — see **D-008** in
> `DECISION_LOG.md` and the comment block at `utils/config.py:188`. That is a
> change of *labelling*, not of physics: the April 2026 bucketing fix moved
> readings onto the month they represent, so same-month rainfall now gives the
> pairing that lag-1 gave before, and the coefficients are unchanged by the
> switch. Every "must use lag-1" instruction below therefore means "must use the
> headline lag", and the headline lag is now 0. **Do not reintroduce a lag-1
> term on the strength of this document** — D-008 explicitly retires that scheme.
>
> **Its one unticked action is now formally rejected.** Line 95 asks for
> `RAF_VALLEY_LAT_DEG` 53.25 → 53.15. **Do not make that change.** Ruled by
> Martin, 2026-08-26, on the Met Office station header itself:
>
> > Valley — Location: 230800E 375800N, Lat 53.252 Lon -4.535, 10 metres amsl
>
> 53.252 rounds to 53.25. The constant is the station's latitude and it is
> right as it stands; 53.15 is roughly the site, and was never the intended
> basis. The checkbox below is closed, not outstanding.
>
> **The per-script audit below is an April 2026 snapshot.** Script versions,
> line numbers and file names have all moved since. It is useful as a record of
> what was wrong and why, not as a to-do list.
>
> ---

# Pipeline-Wide Model Specification & Audit

**Written:** 27 April 2026
**Authority:** This document is the definitive SSM specification.
Any script that fits, simulates, or consumes SSM coefficients MUST
conform to this specification. No exceptions.

---

## THE MODEL SPECIFICATION

### Equation

```
Δh(t) = β₁·P(t−1) + β₂·(−PET(t)) + β₃·(−h_disp_prev(t))
```

where:
```
h_disp = DRAINAGE_DATUM + h_depth
       = 3.7 + h_depth    (h_depth is negative, depth below ground surface)
```

### Constants (from config.py)

| Constant | Value | Import |
|---|---|---|
| `DRAINAGE_DATUM` | 3.7 m | `from utils.config import DRAINAGE_DATUM` |
| `HEADLINE_LAG` | 1 month | Defined in Script 03; other scripts should use 1 |
| `FOREST_INTERCEPTION` | 0.24 | Per-script (not centralised) |

### Design matrix columns

| Column name | Formula | Physical meaning |
|---|---|---|
| `beta_1_recharge` or `beta_1` | `+P(t−1)` | Rainfall (lagged 1 month) raises water table |
| `beta_2_atmospheric_draw` or `beta_2` | `−PET(t)` | PET draws water table down |
| `beta_3_drainage` or `beta_3` | `−h_disp_prev(t)` | Drainage increases with head above datum |

### Sign conventions

| Coefficient | Expected sign | Assertion level |
|---|---|---|
| β₁ | Positive | **Hard** — halt pipeline if violated |
| β₂ | Positive | **Hard** — halt pipeline if violated |
| β₃ | Positive | **Soft** — warn, do not halt |

### Column name standard

The canonical column name for β₃ is `beta_3_drainage`.
The old name `beta_3_internal_brake` is **retired**. Every script
that writes or reads this column must use `beta_3_drainage`.

### Upstand correction for per-well fits

Any script that fits the SSM to individual wells (not cluster centroids)
must apply upstand correction BEFORE fitting, so that the DRAINAGE_DATUM
displacement is relative to ground surface, not pipe top:

```python
h_corrected = wells_clean[col] - upstand
h_disp = DRAINAGE_DATUM + h_corrected
```

Cluster centroids are already upstand-corrected in their construction.

### Δh is computed from raw h

Δh = h(t) − h(t−1) using the raw (uncorrected, no displacement) series.
The DRAINAGE_DATUM constant cancels in the first difference. Only the
β₃ predictor column uses h_disp.

---

## PER-SCRIPT AUDIT

### ✅ Scripts that need NO changes (no SSM fits, no β consumption)

| Script | Reason |
|---|---|
| 00_climate_summary.py | Climate stats only |
| 02_clustering.py | Clustering only (already imports from config) |
| 04_cluster_visualisations.py | Plotting only (already imports from config) |
| 05_pearson_affinity.py | Correlation analysis (already imports from config) |
| 06_pearson_extended.py | Correlation analysis (already imports from config) |
| 12_figure_site_overview.py | Map figure only |
| 13_figure_experimental_design.py | Design figure only |

### ⚠️ Script 01 — data_prep.py

**Issue:** Latitude constant `RAF_VALLEY_LAT_DEG = 53.25` should be `53.15`.
**No SSM issues** — Script 01 does not fit the SSM or reference β values.

Changes:
- [ ] `RAF_VALLEY_LAT_DEG = 53.25` → `53.15`

### ✅ Script 03 — state_space_model.py

**Already rebuilt** in this chat. Lag-1, displacement datum, all
assertions, full diagnostic suite.

### 🔴 Script 07 — boundary_intercept.py

**What it does:** Fits Model A (no intercept) and Model B (with intercept)
per well, via `model_utils.compute_intercept_audit()`.

**Issues:**
- [ ] `model_utils.py` uses `−h_prev` (raw depth), not `−h_disp_prev`
- [ ] `model_utils.py` uses contemporaneous `P`, not `P(t−1)`
- [ ] `model_utils.py` uses column names `P`, `PET_neg`, `h_prev_neg`
      — should be `beta_1_recharge`, `beta_2_atmospheric_draw`,
      `beta_3_drainage`
- [ ] The iterative simulation in `model_utils.py` (lines 118–125)
      must use `DRAINAGE_DATUM + h_prev` for the β₃ term and lag-1 P
- [ ] Hard-coded labels (1 dict) → import from config

**Dependency:** Fixing `model_utils.py` fixes Scripts 07 AND 08 together.

### 🔴 Script 08 — model_benchmarking.py

**What it does:** SSM vs TLM comparison, via `model_utils.py`.

**Issues:** Same as Script 07 — both depend on `model_utils.py`.
- [ ] All `model_utils.py` changes (see Script 07)
- [ ] Hard-coded labels (1 dict) → import from config

### 🔴 Script 09 — scraping_intervention.py

**What it does:** Fits its own OLS per well (pre/post scraping windows)
to detect β shifts from management interventions.

**Issues:**
- [ ] Uses `−h_prev` (raw depth), not `−h_disp_prev` (lines 302, 323)
- [ ] Column name `beta_3_internal_brake` throughout (lines 106, 302,
      323, 330, 338, 605–608) → `beta_3_drainage`
- [ ] Uses `P_m_lag1` — CHECK: is this already lag-1? If so, lag is OK.
      If it's computing its own lag, verify it matches HEADLINE_LAG = 1
- [ ] No import of DRAINAGE_DATUM from config
- [ ] No config import for labels (but may not need labels — check)
- [ ] Upstand correction before fitting? Verify.

**Note:** Scripts 09 and 10 build their own design matrices with
`beta_3_internal_brake` as an internally-created column name. The
handover said "self-consistent, not reading from master CSV." This
is WRONG — the column name and the h_prev formulation must match
the pipeline specification regardless of whether the column is
read or created. The OLS coefficient from `−h_prev` is a DIFFERENT
NUMBER from the coefficient from `−h_disp_prev`. Downstream
consumers that compare β₃ across scripts will get inconsistent
values if the formulation differs.

### 🔴 Script 10 — clearfell_baci.py

**What it does:** Before-After-Control-Impact analysis of clearfell
effects on β values, with its own OLS fits per well.

**Issues:**
- [ ] Uses `−h_prev` (raw depth), not `−h_disp_prev` (lines 405, 494)
- [ ] Column name `beta_3_internal_brake` throughout (lines 157–158,
      405, 441, 494, 507–509, 960, 1410) → `beta_3_drainage`
- [ ] Uses `P_m_lag1` — verify this is lag-1 as intended
- [ ] No import of DRAINAGE_DATUM from config
- [ ] References to `3.7` exist (10 hits) — CHECK: is this already
      using the datum in some places but not others? Inconsistency risk.
- [ ] No config import for labels

### 🔴 Script 11 — forecasting_thresholds.py

**What it does:** Reads β from Script 03's mechanistic table, builds
P_flood threshold equations.

**Issues:**
- [ ] Line 311: `b3 = abs(float(row["beta_3"]))` — forces β₃ positive
      by taking absolute value. Under the displacement formulation β₃
      IS positive, so `abs()` is redundant but not harmful. Remove `abs()`
      for clarity or at minimum document why it's there.
- [ ] Line 322: prints `b3*h_prev` in the equation string — should
      be `b3*h_disp_prev` or at minimum document that the P_flood
      equation uses displacement-referenced β₃
- [ ] Old label strings in logic (6 hits) — must update
- [ ] Does NOT fit its own OLS — reads from Script 03. So β values
      will be correct once Script 03 is updated. BUT the P_flood
      forward calculation must use h_disp, not raw h_prev, when
      computing the threshold rainfall.
- [ ] Config import exists (1) but check if DRAINAGE_DATUM is imported

### 🟡 Script 11b — spatial_thresholds.py

**What it does:** Spatial extension of Script 11's thresholds.

**Issues:**
- [ ] Does NOT fit its own OLS — reads β from Script 03 outputs
- [ ] Uses `beta_3_drainage` (2 hits) — correct column name ✅
- [ ] Old label strings (4 hits) — must update
- [ ] Must use h_disp in any forward P_flood calculation
- [ ] Check if DRAINAGE_DATUM is imported when computing thresholds

### 🟡 Script 14 — climate_projections.py

**What it does:** Forward simulation of water levels under climate
scenarios using β coefficients.

**Issues:**
- [ ] Does NOT fit its own OLS — reads β from Script 03 regional averages
- [ ] The forward simulation MUST use `DRAINAGE_DATUM + h_prev` for
      the β₃ term, otherwise the projection uses β₃ values calibrated
      against displacement but applied to raw depth — producing wrong
      projections
- [ ] Must use lag-1 P in the forward simulation
- [ ] Hard-coded labels (2 dicts) → import from config
- [ ] Old label string (1 hit) — must update

### 🔴 Script 15 — depth_dependent_pet.py

**What it does:** Grid-searches λ for depth-dependent PET attenuation,
comparing depth-coupled SSM against standard SSM baseline.

**Issues:**
- [ ] Uses contemporaneous `P(t)`, not `P(t−1)` — must add lag-1
- [ ] Uses `−h_prev` (raw depth) for β₃, not `−h_disp_prev`
      (lines 145–147, 274–276)
- [ ] Column name `beta_3_internal_brake` (4 hits) → `beta_3_drainage`
- [ ] No import of DRAINAGE_DATUM or HEADLINE_LAG from config
- [ ] Iterative simulation (line ~98) must use displacement for β₃ term
      and lag-1 P
- [ ] **IMPORTANT NUANCE:** The depth-coupling term `d_prev` (depth
      below ground for PET decay) should remain as raw depth
      `−h_prev + upstand`, NOT displacement. The displacement is for
      the β₃ design matrix; the PET extinction depth is a physical
      distance from the surface. These are two different uses of depth.

### 🟡 Script 16 — water_bal.py

**What it does:** Water balance decomposition using β values.

**Issues:**
- [ ] Hard-coded labels (1 dict) → import from config
- [ ] Reads β from Script 03 — verify it uses the displacement-
      referenced β₃ correctly in the decomposition
- [ ] If it multiplies β₃ by h_prev to estimate drainage volume,
      it must use h_disp, not raw h_prev

### 🔴 Script 17 — wtf_specific_yield.py

**What it does:** Water table fluctuation method for Sy estimation.
Reads β₃ from `03_master_data.csv` to correct Δh for drainage.

**Issues:**
- [ ] Line 140: reads `beta_3_internal_brake` from master_data
      → `beta_3_drainage`
- [ ] Line 160 comment: "Δh_corrected = Δh + β₃·|h_prev|" — under
      the displacement formulation this should be `β₃·h_disp_prev`,
      not `β₃·|h_prev|`. The drainage correction term changes because
      h_disp_prev ≠ |h_prev|.
- [ ] Hard-coded labels (2 dicts) → import from config
- [ ] No import of DRAINAGE_DATUM

### 🟡 Script 18 — wtf_spatial.py

**What it does:** Spatial mapping of WTF results.

**Issues:**
- [ ] Reads from master_data — column name `beta_3_internal_brake`?
      Check and update if present
- [ ] Hard-coded labels — grep shows 4 hard-coded dicts, but config
      import exists (3 hits). Audit for inconsistency.

### 🟡 Script 19 — spatial_groundwater.py

**What it does:** Scenario viewer / spatial groundwater model.

**Issues:**
- [ ] Reads β from master_data, already uses `beta_3_drainage` (2 hits) ✅
- [ ] BUT: does it use h_disp when applying β₃ in the spatial model?
      If it multiplies β₃ by h_prev instead of h_disp, projections wrong.
- [ ] No config import — needs DRAINAGE_DATUM for any forward simulation
- [ ] No config import for labels

### 🟡 Script 20 — spatial_figures.py

**What it does:** Maps of per-well β values.

**Issues:**
- [ ] Reads `beta_3_internal_brake` from master_data (2 hits)
      → `beta_3_drainage`
- [ ] Display only — no fitting or forward simulation, so displacement
      datum not directly relevant. But column name must match.

### 🔴 Script 21 — forestry_scenarios.py

**What it does:** Forest management scenario modelling using β values.

**Issues:**
- [ ] Line 283: reads `beta_3_internal_brake` from master_data
      → `beta_3_drainage`
- [ ] References to `3.7` exist (5 hits) — may already partially
      use the datum. CHECK for consistency.
- [ ] Forward simulation must use h_disp for the β₃ term
- [ ] Must use lag-1 P in forward simulation
- [ ] Hard-coded labels (1 dict) → import from config

### 🟡 Script 22 — residual_lag_analysis.py

**What it does:** Fits per-well SSM and analyses residual autocorrelation.

**Issues:**
- [ ] Uses `−h_prev` (raw depth), not `−h_disp_prev` (line 137)
- [ ] Uses contemporaneous P, not lag-1 (check — the script may use
      lag-0 deliberately as its baseline to measure residual lag)
- [ ] No import of DRAINAGE_DATUM
- [ ] **DESIGN QUESTION:** Script 22 was written to diagnose whether
      lag-0 residuals show temporal structure. Under the lag-1 headline
      model, should Script 22 refit at lag-0 (to reproduce its original
      diagnostic) or at lag-1 (to show the residual structure under the
      current model)? RECOMMEND: fit at lag-1 with displacement, because
      the residuals of the CURRENT model are what matter for diagnostics.
      The old lag-0 diagnostic is already captured in Script 03's
      `03_04_lag_diagnostic.csv`.

### 🟡 Script 23 — ridge_recharge_lag_test.py

**What it does:** Fits an extended model (P(t) + P(t−1)) per well,
analyses residual cross-correlation with rainfall vs ridge distance.

**Issues:**
- [ ] Uses `−h_prev` (raw depth), not `−h_disp_prev` (line 145)
- [ ] The extended model includes BOTH P(t) and P(t−1). Under the
      lag-1 headline, the P(t) term may be absorbing noise. Consider
      whether the extended model should be P(t−1) + P(t−2), or
      whether keeping P(t) + P(t−1) is still appropriate as the
      extended model that absorbs the generic lag signal.
- [ ] No import of DRAINAGE_DATUM
- [ ] Labels: already imports from config ✅
- [ ] Column names: uses local names `P`, `P_lag1`, `PET_n`, `h_prev`
      — fine internally as long as the formulation is correct

**DESIGN QUESTION:** Script 23's extended model deliberately includes
both P(t) and P(t−1) to "absorb the generic vadose-zone lag" so the
residuals contain only the candidate ridge signal. Now that the
headline model IS lag-1, the extended model might need to be
P(t−1) + P(t−2) to serve the same absorb-the-generic-lag purpose.
Alternatively, the current formulation (P(t) + P(t−1)) may still be
appropriate because it spans the same two-month window. This is a
scientific question — consult Martin before changing.

### 🟡 Script 24 — residual_seasonality.py

**What it does:** Fits per-well SSM and analyses residual seasonal
patterns.

**Issues:**
- [ ] Uses `−h_prev` (raw depth), not `−h_disp_prev`
- [ ] Uses contemporaneous P — should use lag-1
- [ ] No import of DRAINAGE_DATUM
- [ ] Labels: already imports from config ✅

### 🔴 model_utils.py

**What it does:** Shared SSM fit infrastructure for Scripts 07 and 08
(intercept audit, Model A vs Model B).

**Issues:**
- [ ] Uses contemporaneous `P`, not `P(t−1)` (line 83)
- [ ] Uses `−h_prev` (raw depth), not `−h_disp_prev` (line 98)
- [ ] Column names `P`, `PET_neg`, `h_prev_neg` — should align
      with the pipeline convention
- [ ] Iterative simulation (lines 118–125, 137–144) must use
      `DRAINAGE_DATUM + h_prev` for β₃ term and lag-1 P
- [ ] No import of DRAINAGE_DATUM or config

---

## SUMMARY: WHAT NEEDS FIXING

### Tier 1 — Scripts that FIT their own OLS (wrong coefficients NOW)

These scripts produce β values that are fitted under the wrong
specification. Their outputs are numerically wrong until fixed.

| Script | Issues |
|---|---|
| **model_utils.py** | No lag-1, no displacement, old column names |
| **07** boundary_intercept | Via model_utils + hard-coded labels |
| **08** model_benchmarking | Via model_utils + hard-coded labels |
| **09** scraping_intervention | No displacement, old column names |
| **10** clearfell_baci | No displacement, old column names |
| **15** depth_dependent_pet | No lag-1, no displacement, old column names |
| **22** residual_lag_analysis | No displacement (lag-0 may be by design — check) |
| **23** ridge_recharge_lag_test | No displacement (lag design question) |
| **24** residual_seasonality | No lag-1, no displacement |

### Tier 2 — Scripts that CONSUME β values in forward simulation

These scripts read correct β values (once Script 03 is fixed) but
apply them using the wrong formulation (raw h_prev instead of h_disp).
Their projections/thresholds are numerically wrong until fixed.

| Script | Issues |
|---|---|
| **11** forecasting_thresholds | P_flood uses h_prev, should use h_disp; old labels |
| **11b** spatial_thresholds | Same as 11; old labels |
| **14** climate_projections | Forward sim uses h_prev; old labels |
| **21** forestry_scenarios | Forward sim uses h_prev; old column name; old labels |

### Tier 3 — Scripts that READ β column names only (display/mapping)

These scripts just read and display β values. Only the column name
needs updating.

| Script | Issues |
|---|---|
| **17** wtf_specific_yield | Reads `beta_3_internal_brake`; drainage correction formula |
| **18** wtf_spatial | Check column name |
| **19** spatial_groundwater | Already uses `beta_3_drainage` ✅ — check h_disp in simulation |
| **20** spatial_figures | Reads `beta_3_internal_brake` for display |

### Tier 4 — Scripts needing ONLY label/colour updates

| Script | Issues |
|---|---|
| **16** water_bal | Hard-coded labels only |

### Already correct

| Script | Status |
|---|---|
| **03** state_space_model | Rebuilt in this chat ✅ |
| **04** cluster_visualisations | Config imports ✅ |
| **05** pearson_affinity | Config imports ✅ |
| **06** pearson_extended | Config imports ✅ |
| **19** spatial_groundwater | Column names ✅ (check h_disp use) |

---

## HOW TO USE THIS DOCUMENT

Drop this file into any new chat that is tasked with updating a
pipeline script. The chat should:

1. Read this document FIRST for the specification
2. Read the target script
3. Apply ALL changes listed for that script
4. Verify the design matrix matches the specification exactly
5. Ship the complete updated script

DO NOT partially fix a script. Every change listed must be applied
in the same edit, or the script will be internally inconsistent.

---

## FILES TO INCLUDE IN ANY FIX CHAT

1. This document (MODEL_SPECIFICATION_AUDIT.md)
2. The target script(s) to be fixed
3. `config.py` (current version with DRAINAGE_DATUM, CLUSTER_LABELS)
4. `paths.py` (for output file paths)
5. `model_utils.py` (if fixing Scripts 07 or 08)
6. `data_utils.py` (for normalize_well_name)
