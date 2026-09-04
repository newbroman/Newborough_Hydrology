> ## Reconstructed 2026-09-04 under T-10 — NOT the original dated spec
>
> The original `SPEC_script35_per_well_amplification_metric.md` (locked
> **2026-06-27**) was never committed to this repository and was not found in any
> store, on disk, in the desktop trash, or in any of the archived project bundles
> — searched under T-10 on 2026-08-26 and again on 2026-09-04. This document is a
> **reconstruction dated 2026-09-04**, rebuilt from the surviving material so the
> live citations resolve to a real document. It is not passed off as the original.
>
> **Rebuilt from:** the locked-spec method block preserved verbatim in
> `src/35_per_well_amplification.py`'s module docstring (the spec was quoted into
> the code when it was locked), `src/utils/envelope_metric.py`, and the
> `ENVELOPE_METRIC_*` constants in `src/utils/config.py`.
>
> **Cited by:** `src/35_per_well_amplification.py:14`, `src/utils/config.py:1719`
> ("Spec-locked 2026-06-27"), `src/utils/envelope_metric.py:16`.
>
> **Authority.** The code is the authority, not this document. Where this
> reconstruction and the script differ, the script wins; this records the design
> intent behind the locked method, not a second editable copy of it.
>
> ---

# SPEC — Script 35: per-well climate-sensitivity coefficient (amplification metric)

*Locked 2026-06-27. Reconstructed 2026-09-04 from the locked method preserved in
the Script 35 docstring.*

## Purpose

A **frame-independent per-well coefficient** describing how much each well
magnifies (> 1) or damps (< 1) the shared **spring** climate swing. It is the
discrete per-well companion to Script 33's interpolated amplification field:
Script 35 produces **no surface** — a coefficient table (with confidence interval
and confidence tier), an SSM-calibration figure, and a discrete per-well marker
map — so it does not duplicate Script 33's maps.

The metric is co-temporally normalised so that wells measured on different
extreme-year subsets stay comparable, is SSM-calibrated, and is extended to
short / inconsistent-record wells that the Script 33 matched surface and the SSM
itself cannot reach.

## Method (the locked specification)

1. **Spring value per well-year** = mean of the available MAM months
   (`config.MSL_SPRING_MONTHS`).

2. **Extreme-year pools** — antecedent-screened supersets of the canonical and
   recent sets: `DRY = config.ENVELOPE_METRIC_DRY_POOL`,
   `WET = config.ENVELOPE_METRIC_WET_POOL`.

3. **Per-well state** = mean over the pool years the well actually holds
   (at least one of each side required).

4. **Co-temporal normalisation.** The reference core is the set of wells with
   *full* dry coverage (all `DRY_POOL` years) and at least
   `ENVELOPE_METRIC_REF_MIN_WET` wet years. A well's coefficient is its own swing
   divided by the core's mean swing **recomputed over that well's own extreme
   years**. This cancels the common climate signal window-by-window, so the
   coefficient reproduces the matched-window amplification (validated r ≈ 0.98)
   while removing coverage artefacts — e.g. the CEH9/CEH39 25 m step on the
   Figure 60a surface, where CEH39 lacks the extreme 2012 spring.

5. **Confidence tiers.** A (≥ 2 dry & ≥ 2 wet), B (≥ 1 each, not A),
   C (1 dry & 1 wet).

6. **Confidence interval.** Delete-one-extreme-year jackknife; for singleton
   sides (tier C / n = 1) the within-state single-year noise — estimated from the
   multi-year wells — is folded in. 90 % (z = 1.645).

7. **Validation.** The coefficient tracks the independently-fitted SSM response
   (amplitude vs β₂, amplitude vs β₃); the calibration regression is written to
   the figure and the results table.

## Honesty rule (locked into the spec)

The coefficient is validated where β₂ exists (long-record wells). Short-record
wells are both the use case and the place it cannot be directly verified — the
tiers, the CIs, and the β₂/β₃ calibration are how that extrapolation is kept
honest. Language throughout is *"consistent with the fitted drainage/draw
response"*, never *"confirms"*.

## Inputs (read at runtime via `utils.paths`; nothing hardcoded)

| Constant | File | Use |
|---|---|---|
| `INT_WELLS_CLEAN` | `01_wells_clean.csv` | spring levels |
| `INT_LOCATIONS` | `01_locations.csv` | well E/N |
| `INT_MASTER_DATA` | `03_master_data.csv` | β₁/β₂/β₃ + cluster (calibration + cluster) |
| `INT_PEAR_AUDIT_SITEWIDE` | `06_pear_membership_audit_sitewide.csv` | cluster fallback for unclustered wells |

## Relationship to the rest of the pipeline

Script 35 is a Paper 1 standalone product (the SSM-calibrated per-well
amplification coefficient, r ≈ 0.99 against the matched-window metric), **not** a
separate report map. It is the discrete companion to Script 33's field; the two
are not to be conflated.
