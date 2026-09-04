> ## Reconstructed 2026-09-04 under T-10 — NOT the original dated spec
>
> The original `SPEC_script37_scale_factor_regression_2026-07-06.md` (the
> design document for the Script 37 driver-validation regression) was never
> committed to this repository and was not found in any store, on disk, in the
> desktop trash, or in any archived project bundle — searched under T-10 on
> 2026-08-26 and again on 2026-09-04. This document is a **reconstruction dated
> 2026-09-04**, rebuilt from the surviving material so the live citations resolve
> to a real document. It is not passed off as the original spec.
>
> **Rebuilt from:** the design section preserved in `src/37_driver_validation.py`'s
> module docstring (which names this spec as its design document, Part A) and the
> in-repo companion `notes/specs/SPEC_script37b_partB_comparative_footing_2026-07-06.md`,
> which amends this spec's Part B.
>
> **Cited by:** `src/37_driver_validation.py:8` ("Design document: … Part A only"),
> `src/37b_driver_footing.py:8` ("amends … Part B section"), and
> `notes/specs/SPEC_script37b_partB_comparative_footing_2026-07-06.md`.
>
> **Authority.** `src/37_driver_validation.py` is the authority for the method as
> built; Part B is superseded by the in-repo Part B spec and by
> `37b_driver_footing.py`. Read this for the Part A design intent only.
>
> ---

# SPEC — Script 37: per-driver scale-factor regression (driver validation)

*Part A signed off 2026-07-06 (items 1–7); Part B deferred (later handled by the*
*Part B comparative-footing spec). Reconstructed 2026-09-04 from the Script 37*
*design docstring.*

## Purpose

Validate Script 20's **modelled** driver-change field against Script 36's
**observed**, climate-corrected per-well secular trends, by fitting a
per-driver **dimensionless scale factor** — how much of the modelled amplitude
the aquifer actually feels.

## Observed signal (reused, not refit)

Per well, `dh_corr,i` is Script 36's climate-corrected endpoint difference:
`b_hat` is fit once on `config.ACT_BHAT_WINDOW = (2005, 2017)`,
`h_corr(t) = h(t) − b_hat·CWB(t)`, then a non-overlapping endpoint-mean
difference with `config.ACT_ENDPOINT_FRACTION` (1/3). Read directly from
Script 36's committed CSV; **not** refit in Script 37.

## Modelling step (the scale-factor regression)

Each window is a separate OLS regression of `dh_corr` on the modelled driver
fields as **separate regressors**, with a **free spatially-uniform intercept**:

    dh_corr,i = s_coast · coast_i + s_cf · clearfell_i + c + eps_i

- `coast_i`, `clearfell_i` are the modelled amplitudes (mm) for that window,
  β₃-corrected per well, so each scale factor `s` is **dimensionless**
  (s = 1 → the aquifer feels exactly the modelled amplitude; s < 1 → modelled
  amplitude overstated; s > 1 → understated).
- `c` is a **free uniform intercept**. It absorbs the site-wide β₁ decline
  (present at the unfelled Climate-Control tier) so background drying cannot be
  laundered into `s_coast`. This is the key identification move relative to the
  earlier single-summed-prediction form.
- **Coastal amplitude** per window = `δ₀ · dt_mid · shape_i`, where `dt_mid` is
  the difference between Script 36's own endpoint-group centroid years for that
  well/window (built to match Script 36's construction exactly). `δ₀` is read
  live from the forest-free linear-capped row of the Script 25 fit parameters —
  **not** the raw window length, **not** a fixed 20-year figure.
- **Clearfell amplitude** = `clearfell_step_mm · exp(−d_fell/λ)`, the step read
  live from `10a_report_numbers.csv` (`ANCOVA_Forest_Impact_clearfell_step`,
  observed ≈ +120 mm BACI). Zero for wells first observed after the Dec-2017
  clearfell (no pre-event baseline to attribute a gain against).
- **Standard errors: HC3** heteroskedasticity-robust specifically (statsmodels
  `get_robustcov_results('HC3')`, not HC0/HC1) — well counts are small enough
  that the distinction matters.

## Windows

Each window enters only the regressors it can identify — e.g. `2006_2012`
{coast, c} (pre-everything, clean coast + background); `2018_2025`
{coast, clearfell, c} (clearfell isolated, the window starting the year after the
Dec-2017 event so no pre-clearfell spring observation falls inside it). The full
window list and regressor sets are in `src/37_driver_validation.py`.

## Part B (deferred)

Part B — putting forest, scrape and coast side by side on a common comparative
footing over a shared 2005→2025 horizon — was **deferred** at sign-off and is
specified separately in
`notes/specs/SPEC_script37b_partB_comparative_footing_2026-07-06.md` and built in
`src/37b_driver_footing.py`. Part B deliberately does **not** consume Script 37's
scale factors; it rests on observed BACI anchors and the modelled Script 20
fields, each cell flagged observed or modelled.
