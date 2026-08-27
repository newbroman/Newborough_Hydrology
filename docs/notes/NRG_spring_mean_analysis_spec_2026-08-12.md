> ## Recovered 2026-08-26 — SUPERSEDED in part, and it says so itself
>
> Recovered 2026-08-26 from the **project store** of a Claude project — not from a
> chat, and not from disk. All five files in this block lived in a `claude/`
> working directory that was never committed and no longer exists, which is why
> the code that cites them points at paths that cannot resolve. Kept **verbatim
> below**; byte-identical to the recovered originals.
>
> **Its decision 1 was superseded the next day** by
> `NRG_spring_BACI_spec_2026-08-13.md`, which replaced the Script 36 loose convention
> (mean of whatever MAM months are present) with the strict 3-of-3 rule. The strict rule
> is what shipped: `config.MSL_MIN_MONTHS_PER_SPRING = 3`.
>
> Its own status block — the divergence check — stands, and is the reason the build
> happened: spring and summer diverge, per-well slope r = +0.91 but the secular trend
> flips sign in the open dune. **Those per-cluster figures are 2026-08-12 numbers and
> have not been re-checked against the current pipeline.**

> **STATUS 2026-08-13 — divergence check DONE, build gated on Martin's outputs review.**
> Read-only check ran (method validated: summer per-cluster slopes reproduce committed
> `25_03` exactly). **Result: spring and summer DIVERGE → full build justified.** Spatial
> pattern shared (per-well spring vs summer slope r=+0.91; coastal gradient present in
> spring, C3 r=+0.43 p=0.07); but the secular trend flips sign in the open dune — spring
> ~+8–16 mm/yr more positive than summer everywhere. Per-cluster spring means:
> C1 +6.6, C2 +12.9, C3 +4.4, C4 −3.6, C5 −24.7 mm/yr (vs committed summer
> −9.1/−0.8/−5.9/−12.6/−32.7). **Caveat:** raw comparison; the raw spring rise is likely
> wet-spring (CWB) loaded (Script 36's "+19.66 mm/yr wet-spring-lifted mean"), so the full
> Script-25 decomposition (which removes spring CWB) is exactly what disentangles
> structural vs wet-spring. Scratch: `/tmp/spring_vs_summer.csv` (that session only).
>
> **Decisions (Martin):** (1) missing-month rule **AGREED** = Script 36 convention
> (`config.MSL_SPRING_MONTHS=(3,4,5)`, mean of months present; no strict all-3).
> (2) **Same treatment as summer** = **parameterise `src/25_coastal_gradient.py`** with a
> metric arg (`summer_min | spring_mean`) so both run the identical regression +
> decomposition (DRY); NOT a parallel script. (3) Placement (main report vs supplement)
> **deferred** — build the outputs first, show Martin, then decide. (4) Spring-mean MSL5
> threshold-exceedance version — **still open**.
>
> NOTE: decision 1 above was subsequently SUPERSEDED on 2026-08-13 — the strict 3-of-3 rule
> was adopted instead (see `claude/NRG_spring_BACI_spec_2026-08-13.md` and
> `claude/NRG_spring_mean_build_design_2026-08-13.md`).
>
> Full onboarding + state: `claude/HANDOVER_cowork_NRG_2026-08-13.md`.

---

# Spring-mean (MAM) analysis — spec / handover (2026-08-12)

Standalone task, requested by Martin. Add an **annual spring-mean** water-level
analysis paralleling the existing **summer-minimum** analysis. Design → sign-off →
build; do the divergence check FIRST (below) before committing to the full build.

## The metric
Per well, per year: **spring mean = arithmetic mean of the March, April and May
monthly water-table levels** for that year. One value per well per year.
- This is NOT the 5-year MSL5 (which averages spring means over 5 years for the
  Curreli threshold classification), and NOT a whole-year annual mean. It is the
  per-year MAM level, to be trended and decomposed exactly like the summer minimum.
- Missing-month rule to confirm with Martin: require all 3 of Mar/Apr/May, or
  admit a year with ≥2 of 3? (Summer-minimum analysis convention should be matched.)

## What already exists vs what is new
- **Exists:** a per-year spring value (mean Mar–May) is already formed in the
  differential map (Fig 63), the absolute climate-trend map (Fig 64, Script 36),
  and the MSL5 machinery (Scripts 26/26b/34). Script 36 already fits a
  climate-removed **spring trend** per well, h(t)=a+b·CWB+c·t.
- **New:** the **Script 25-style coastal-retreat gradient decomposition** —
  per-well spring-mean slope vs distance-to-coast, split per cluster into a
  climate component and a coastal-retreat component — currently runs **only on the
  summer minimum** (`25_02_per_well_summer_min_slopes.csv`, `25_03_cluster_partition.csv`,
  `25_04_baci_corroboration.csv`). Applying that same decomposition to the spring
  mean, on identical footing, is the genuinely new piece, plus the spring-vs-summer
  comparison.

## Why it's worth doing
The Curreli ecological thresholds are defined on **spring** levels, so a spring-mean
trend + gradient speaks more directly to the habitat threshold-exceedance question
than the summer minimum does. Comparing spring vs summer also reveals whether the
site is drying uniformly across the year or whether the **seasonality is changing**
(e.g. summer crashing faster than spring) — a contrast not captured now.

## Sequencing — DIVERGENCE CHECK FIRST (gates the build)
Before building the full parallel analysis, run a read-only check against committed
monthly data (`01_wells_clean.csv`):
1. Form the annual spring mean (MAM) per well; aggregate to per-cluster.
2. Fit the per-cluster spring-mean secular trend and the coastal-distance slope
   (dist_coast from `01_dist_coast_validation.csv` / `25_02`).
3. Lay these beside the committed **summer-minimum** trend/gradient (Script 25 /
   `25_03`, and the §4.8.1 decomposition).
- If spring and summer track together (similar sign/magnitude, similar gradient) →
  the full parallel analysis is largely confirmatory (short paragraph, maybe one
  panel).
- If they diverge → build the full Script-25-style decomposition on the spring mean
  + a spring-vs-summer figure pair + a report subsection.  [← this branch: they DIVERGE.]

## Build (only if the check justifies it)
- Preferred: **parameterise Script 25** to take a metric argument
  (`summer_min | spring_mean`) so the coastal-gradient regression + per-cluster
  decomposition run on either, DRY. Fallback: a parallel script (e.g. `25s_*` /
  next free number) mirroring Script 25.  [← Martin chose PARAMETERISE (decision 2).]
- Outputs paralleling `25_02/25_03/25_04` for the spring mean; a spring-vs-summer
  comparison table/figure.
- Report placement: parallel to §4.8 / §4.8.1 (summer-minimum decomposition), tied
  explicitly to the Curreli spring thresholds. Decide with Martin whether it lands
  in the main report now or as a supplement.  [← deferred until outputs seen.]

## Guardrails (project rules)
All I/O via `paths.py`; constants from `config.py`; no hardcoded values; every
number traces to a committed CSV before entering the report; even-handed framing
("consistent with"/"indicates", not "confirms"). Clone `main`, read the Script 25
+ Script 36 changelogs before touching them. New/parameterised script → CHANGELOG
delta + version bump; if a new registered step is added, mind the manifest guard.

## Decisions to confirm with Martin before building
1. Missing-month rule for the MAM mean (all 3 vs ≥2 of 3) — match the summer-min
   convention.  [RESOLVED: Script 36 convention, mean of months present. LATER SUPERSEDED → strict 3-of-3.]
2. Parameterise Script 25 vs a new parallel script.  [RESOLVED: parameterise.]
3. Which outputs/figures, and main-report vs supplement placement.  [DEFERRED: build first.]
4. Whether to also produce a spring-mean version of the MSL5 threshold-exceedance
   (vs keeping thresholds on the 5-yr MSL5 only).  [OPEN.]
