> ## Recovered 2026-08-26 — BUILT IN FULL
>
> Recovered 2026-08-26 from the **project store** of a Claude project — not from a
> chat, and not from disk. All five files in this block lived in a `claude/`
> working directory that was never committed and no longer exists, which is why
> the code that cites them points at paths that cannot resolve. Kept **verbatim
> below**; byte-identical to the recovered originals.
>
> Cited from `src/utils/clearfell_common.py:438` and `:1164`.
>
> **Every item in its build plan was implemented.** Checked line by line:
> `annual_seasonal_metric()` at `clearfell_common.py:1011`, `annual_spring_mean()` at
> `:1067`, `annual_summer_minimum()` reduced to a wrapper at `:1090`,
> `SPRING_PANEL_MAX_MISSING = 0` at `:1165`, `SPRING_PANEL_YEARS_EXCLUDED = [2012]` at
> `:1166`, `wmc3_usable_spring_years()` at `:1278` with the warn-on-disagreement pattern
> intact, `forest_control_centroid_spring_mean()` at `:1430`. No `SPRING_MEAN_MIN_MONTHS`
> was ever added — `config.MSL_SPRING_MONTHS` and `MSL_MIN_MONTHS_PER_SPRING` carry the
> rule, exactly as this document argued. 37 spring references in `paths.py`;
> `10d_06_spring_means.csv`, `10d_07`, `10d_08`, the `10d_09/10` figures and
> `10l_06_four_zone_spring_results.csv` are all emitted.
>
> **Its open question was settled the way it recommended.** The spring figures carry no
> SD15b/SD16 bands; Script 09c says so at `:46`, `:66`, `:219` and `:594` — "there is no
> spring equivalent of SD15b/SD16". The MSL5 spring-class alternative was not taken.

# Spring-mean (MAM) BACI — spec for Scripts 09c / 10d / 10l (2026-08-13)

Repo HEAD `edb35d6`. Motivation (Martin): noticed the absence of an MAM analysis while
reading the summer-minima analysis in the scraping methods. Decision: **add spring
alongside summer — do not swap.** The summer minimum is the drought-stress metric and is
cited throughout the report; MAM is additive. This batch is built **before** the
Script 25 / Script 14 coastal-gradient work (`claude/NRG_spring_mean_build_design_2026-08-13.md`).

Status: awaiting sign-off on the ecological-threshold question; everything else settled.

---

## Why the BACI branch is not affected by the Script 25 power concern

The power concern raised for Script 25 applies to **one regression only** — the
coastal-gradient panel fit, which runs on the raw *monthly* panel (12,456 well-months,
11 month-dummies demeaned out). Restricting that to MAM keeps ~25% of rows.

The BACI scripts have a different shape entirely. `09c`, `10d` and `10l` all reduce each
well to `annual_summer_minimum(..., min_measured=2)` — **one value per well per year** —
then run BACI on impact vs control, before/after. A spring mean is also one value per well
per year: same wells, same years, same N. **No power cost.**

If anything the spring mean is the better-conditioned response variable. A summer minimum
is an extreme-order statistic — whichever single month happened to be lowest — so
measurement noise and one dry month propagate straight in. A three-month mean averages that
down. Against a BACI design, a less noisy response is a tighter test. The Curreli
ecological thresholds are also defined on spring levels, so a spring BACI speaks to the
habitat question more directly.

---

## Empirical findings (read-only, this session)

**Method validated.** The summer WMC3 gatekeeper set was reproduced independently and
matches the committed `wmc3_usable_summer_years()` output exactly:
`[2011, 2013–2018, 2020–2025]` (13 years, 2012 and 2019 excluded).

**Finding 1 — the MAM record is as complete as the Jun–Sep record.**
Network well-years surviving the completeness guard (measured cells only, 2006–2026):

| Rule | Well-years |
|---|---|
| Jun–Sep, ≥2 of 4 measured (**committed summer rule**) | 293 |
| MAM, ≥1 of 3 | 294 |
| MAM, ≥2 of 3 | 291 |
| MAM, **≥3 of 3** | **289** |

The strictest possible spring rule costs 4 well-years against the committed summer rule
(1.4%). In the Script 25 / trend branch (88-well network, 2004–2025, non-null cells) the
same pattern holds: 1,329 well-years at ≥1 month vs 1,301 at 3-of-3 (2%), and the number
of wells with ≥10 usable spring years is **77 under all three rules**.

**Finding 2 — the spring four-zone panel gains a year over the summer panel.**
WMC3 MAM completeness, 2011–2025: 3-of-3 measured in **14 of 15 years**. Only 2012 is thin
(1 measured, 1 interpolated, 1 missing). **2019 — excluded from the summer panel because
WMC3's Jun–Sep was one interpolated June plus three missing months — is fully measured in
spring.** So at `max_missing = 0` (stricter than the summer panel's `max_missing = 1`) the
spring panel is `[2011, 2013–2025]` = **14 years, vs the summer panel's 13.**

---

## Consequence: use the strict 3-of-3 rule, and reuse the existing constant

This **supersedes decision 1** in `claude/NRG_spring_mean_analysis_spec_2026-08-12.md`
(Script 36 convention — mean of whatever MAM months are present) and withdraws the
proposed `SPRING_MEAN_MIN_MONTHS = 1` constant from
`claude/NRG_spring_mean_build_design_2026-08-13.md`.

That decision was taken on the assumption the rule mattered. It does not — the difference
between the loosest and strictest rule is ~2% of well-years in both branches. Given that,
the strict rule is the better choice: a "spring mean" that is genuinely the mean of all
three spring months, needing no caveat about which months contributed.

It also means **no new constant is required**. `config.MSL_SPRING_MONTHS = (3, 4, 5)` and
`config.MSL_MIN_MONTHS_PER_SPRING = 3` already exist and already encode exactly this rule.
Adopting them gives one definition of "spring mean" across the whole pipeline — BACI,
coastal gradient, and the van Willegen MSL5 classification — instead of two divergent ones.
The Script 36 loose convention stays as-is in Script 36 (not re-litigated here); the note
below records the divergence.

*Recommend this also be carried into the Script 25 / Script 14 build, replacing the earlier
decision, so the spring metric has a single definition. Martin's call.*

---

## Build plan

**`src/utils/clearfell_common.py`** (version bump)
* Generalise `annual_summer_minimum()` → `annual_seasonal_metric(series, months, agg, ...)`,
  preserving the provenance-aware measured-only logic and the `min_measured` guard verbatim.
  `annual_summer_minimum()` becomes a thin wrapper (precedent: the 20-yr thin-wrapper
  refactor). New thin wrapper `annual_spring_mean()` → `months=config.MSL_SPRING_MONTHS`,
  `agg=mean`, `min_measured=config.MSL_MIN_MONTHS_PER_SPRING`.
* Same treatment for `forest_control_centroid_summer_min()` → general centroid function +
  summer and spring wrappers.
* Generalise `well_year_usable_summer()` / `wmc3_usable_summer_years()` likewise; add
  `SPRING_PANEL_MAX_MISSING = 0` and reviewed constant `SPRING_PANEL_YEARS_EXCLUDED = [2012]`,
  cross-checked against live data with the same warn-on-disagreement pattern.
* `SUMMER_MONTHS = [6, 7, 8, 9]` stays local (pre-existing duplication with
  `scraping_common`); spring months come from `config` — no third local copy.

**`src/09c_summer_minima.py`** (version bump) — spring-mean BACI alongside the summer
minimum: per-well spring means, climate-control centroid, paired-control shifts, same
equilibration fit machinery.

**`src/10d_summer_minima.py`** (version bump) — same, with forest/coastal/climate control
centroids.

**`src/10l_four_zone_summer_minima.py`** (version bump) — four-zone panel on the spring
mean, using the spring gatekeeper (14 years). Report the extra year explicitly.

**Outputs** — new `paths.py` constants, spring-suffixed. **Nothing committed is
overwritten**; every existing summer CSV/figure keeps its name and content.

**Not in this batch:** Script 25 + Script 14 (next); report placement; the spring-mean MSL5
threshold-exceedance variant (still open).

## Open question — ecological threshold bands on the spring figures

`config.SD15b` (0.61 m) and `SD16` (0.98 m) are the **summer** slack viability limits
(Script 14 uses them as `WET_SLACK_SUMMER` / `DRY_SLACK_SUMMER`; `SD15b_WINTER` /
`SD16_WINTER` are the winter variants). There is **no spring equivalent constant**, and the
09c/10d summer figures draw these bands. Options: omit the bands from the spring figures
(recommended — honest, and defers to the open MSL5 item), or overlay the van Willegen MSL5
spring class boundaries.

## Guardrails
All I/O via `paths.py`; constants from `config.py`; no hardcoded values; `console_utils`
output; `MPL_DEFAULTS` / `render_figure` house style; every number traces to a committed CSV;
even-handed framing. One CHANGELOG delta for the batch, version bumps on all touched files.
No new registered pipeline step, so `_EXPECTED_ANALYTICAL_TOPLEVEL = 39` and the 46/17
headline are untouched. Claude does not push — Martin runs `nrg_git.sh` option 2.
