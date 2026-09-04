> ## Reconstructed 2026-09-04 under T-10 — NOT the original dated handover
>
> The original `HANDOVER_c3_detrend_check.md` (dated **2026-05-29**) was never
> committed to this repository and was not found in any store, on disk, in the
> desktop trash, or in any archived project bundle — searched under T-10 on
> 2026-08-26 and again on 2026-09-04. This document is a **reconstruction dated
> 2026-09-04**, rebuilt from the surviving material so the live citations resolve
> to a real document. It is not passed off as the original handover.
>
> **Rebuilt from:** `src/28_c3_detrend_check.py` (which quotes the handover's
> procedure and decision logic verbatim and writes the results memo), the
> committed `outputs/28_c3_detrend/` products, and Methods Supplement §S.19.1.
>
> **Cited by:** `src/28_c3_detrend_check.py` (×4, incl. "Routed from
> HANDOVER_c3_detrend_check.md (2026-05-29)") and `PIPELINE_README.md:1389`.
>
> **Authority.** Script 28 and its committed outputs are the authority; the
> headline verdict and every number live there, not here.
>
> ---

# Handover — C3 de-trending check

*Routed 2026-05-29 → `src/28_c3_detrend_check.py` (cluster-framework diagnostic,*
*tier X). Read-only on pipeline outputs; writes to `outputs/28_c3_detrend/`.*

## The question

Is **C3 (Western Residual)** mechanistically just **C2 (Dune)** plus a
coastal-erosion drift — i.e. a C2 hydrograph slowly declining under the Script 25
forest-free coastal gradient — rather than a genuinely distinct cluster?

- **H0** — C3 is a genuinely distinct cluster; the gradient adds drift but is not
  the constitutive mechanism.
- **H1** — the gradient explains the C2/C3 distinction; C3 is C2 + coastal drift.

## Procedure (implemented in Script 28)

1. For each well, compute the predicted coastal-erosion drift rate
   δ(d) = δ₀ × max(0, 1 − d/L) using the **live Script 25 forest-free
   linear-capped fit** (δ₀, L read at runtime, not hardcoded).
2. De-trend the well's monthly hydrograph by subtracting the linear trend of
   slope δ(d). Since δ is negative (a decline), this adds a positive correction
   over time, undoing the decline.
3. Re-classify the de-trended hydrograph against the **un-de-trended** cluster
   centroids (correlation distance over the month-anomaly series).
4. Tabulate per well: original best-match, de-trended best-match, and the
   sensitivity outcomes.

## Sensitivities to run

Alongside the headline (forest-free, monthly-uniform δ), the script reports:
summer-only (Jun–Sep) de-trending; the full δ₀ including forest; and L = 500 m
and L = 1500 m. A **sanity check** requires high C2 self-retention — C2 wells
should not be perturbed by a small δ(d) correction; low C2 retention would mean
the procedure is contaminating hydrographs rather than testing the hypothesis.

## Reading the result

The headline is the count of C3 wells that move **→ C2** after forest-free
monthly-uniform de-trending, out of the C3 wells that carry a Script 25
`dist_coast` and hydrograph (forest-zone and heavily-perturbed wells without
coastal-distance metadata are excluded — e.g. CEH36, WMC3).

- **Most C3 wells move to C2** → H1 (or H1-partial: gradient explains most of the
  distinction but residual structure remains).
- **C3 wells stay in C3** → H0 confirmed.

## What follows from the result

- **If H1** (report reframing follow-on): C3 is re-described as C2 under coastal
  drift, and the report's cluster-framework sections are reframed accordingly.
- **If H0** (single-sentence follow-on): a sentence in the report §5.1.1 /
  §5.4.3 aquifer-architecture-validation paragraph notes that the check was
  performed and that C3 survives it as a distinct cluster; the diagnostic is
  documented in Methods Supplement §S.19.1 and supports the main-report
  aquifer-architecture-validation claim.

The committed verdict, per-well detail (`c3_detrend_check.csv`) and figure
(`c3_detrend_check_panel.png`) are in `outputs/28_c3_detrend/`.
