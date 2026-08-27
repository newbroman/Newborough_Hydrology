> ## Recovered 2026-08-26 — its proposed constant was withdrawn
>
> Recovered 2026-08-26 from the **project store** of a Claude project — not from a
> chat, and not from disk. All five files in this block lived in a `claude/`
> working directory that was never committed and no longer exists, which is why
> the code that cites them points at paths that cannot resolve. Kept **verbatim
> below**; byte-identical to the recovered originals.
>
> Batch 3 of the spring-mean workstream (Scripts 25 + 14). **The
> `SPRING_MEAN_MIN_MONTHS = 1` constant it proposed was withdrawn** the same day by
> `NRG_spring_BACI_spec_2026-08-13.md`, on the finding that the loosest and strictest
> rules differ by ~2% of well-years. It does not exist in `config.py` and never did.
>
> Whether the batch-3 work it designs was built has **not** been verified here.

# Spring-mean (MAM) analysis — Script 25 + Script 14 build design (2026-08-13)

Batch 3 of the spring-mean workstream. Batch 1 (shared helpers + Script 09c) is **done and
verified** — see `claude/CHANGELOG_delta_2026-08-13_spring_mean_BACI_09c.md`. Batch 2
(Scripts 10d + 10l) comes first. Live state:
`claude/HANDOVER_cowork_NRG_2026-08-13b.md`. Built against HEAD `edb35d6`.

---

## RESOLVED DECISIONS

### Missing-month rule — STRICT 3-of-3 (Martin, 2026-08-13)

**Use `config.MSL_SPRING_MONTHS` + `config.MSL_MIN_MONTHS_PER_SPRING` (3 of 3).**
Martin: *"Carry the strict rule into the Script 25/14 build."*

This **supersedes decision 1 in `claude/NRG_spring_mean_analysis_spec_2026-08-12.md`**
(the Script 36 convention — mean of whatever MAM months are present). That decision was
taken on the assumption the rule mattered; measurement shows it does not:

| Branch | Loosest | Strictest (3-of-3) |
|---|---|---|
| BACI network well-years (measured cells) | 294 at ≥1 | **289** (vs 293 for the committed summer ≥2-of-4 rule) |
| Script 25 branch well-years (2004–2025, non-null) | 1,329 at ≥1 | **1,301** |
| Script 25 wells with ≥10 usable spring years | 77 | **77** — identical under all three rules |

So the rule moves ~2% of well-years and zero wells. The strict rule means a "spring mean"
is genuinely a three-month mean needing no caveat about which months contributed, and it
reuses constants that already exist — one definition of spring across BACI, coastal
gradient, and the van Willegen MSL5 classification. **No new constant.** Batch 1 already
adopted it (`clearfell_common.SPRING_MONTHS` / `SPRING_MIN_MEASURED`); batch 3 imports the
same. The earlier proposal of `SPRING_MEAN_MIN_MONTHS = 1` is **withdrawn**.

Script 36's own looser `spring_year_table()` is left as-is (not re-litigated); the
divergence is recorded here and in `clearfell_common`.

### Observed cluster-centroid spring slope — EXTEND SCRIPT 14 (Martin, 2026-08-13)

Script 14 gains a spring-mean centroid trend computed the same way as its existing
summer/winter trends from `03_regional_averages.csv`, emitting `14_spring_trend_stats.csv`
(same columns as `14_summer_trend_stats.csv`). Keeps the partition's `observed` column on
identical footing to the committed summer number.

**Year basis:** MAM sits wholly inside a calendar year, so the spring metric is indexed by
calendar year (as Script 36 does), not the Oct-start hydrological year the summer minimum
uses. Note it in the docstring and the comparison table.

### Panel fit scope — BOTH, all-season as the report headline (Martin: "show both")

Emit both; recommendation for the report is the **all-season fit**.

---

## What the code actually does today (read at HEAD `edb35d6`)

Structural finding that changes what "run the regression on spring" means:

* **The coastal-gradient panel fit is not seasonal.** `load_panel()` → `build_design()` →
  `fit_panel()` builds a *monthly* long panel (all 12 months, 12,456 obs full network) and
  fits δ(d)·t by profile non-linear least squares, with well and month fixed effects
  absorbed by within-well demeaning (Frisch–Waugh–Lovell) and a CWB slope controlled. It
  estimates one season-independent **trend** gradient (δ₀ = −29.03 ± 1.92 mm/yr,
  L = 894 ± 51 m, c = −6.35 mm/yr for the headline forest-free linear-capped spec,
  `25_01_panel_fit_parameters.csv`).
* **Only two functions are metric-specific**: `compute_per_well_slopes()` (min of Apr–Sep
  per hydrological year) and `cluster_partition()`.
* `baci_corroboration()` (`25_04`) reads the Script 10a BACI `easting × time` coefficient —
  **metric-independent**, so it is not re-emitted for spring.
* Nothing else regresses per-well slope on distance; distance enters the partition only via
  each cluster's mean `dist_coast_m`.

### Why all-season is the report headline

1. **Structural parallelism.** The committed summer decomposition already applies the
   all-season gradient to a summer metric. All-season gradient + spring metric is the exact
   parallel. A MAM-only refit would make the spring branch differ from the committed summer
   branch in *two* ways at once (metric **and** gradient), so any spring-vs-summer
   difference could not be attributed to either.
2. **Power.** MAM-only drops the panel from ~12,456 to ~3,100 obs and collapses the month
   fixed effects from 11 dummies to 2. δ₀ SE should roughly double and L will loosen
   considerably — a wide spring L could read as a real seasonal difference when it is
   sampling noise. *(This power point applies to THIS regression only. It does not apply to
   the BACI branch, where each well reduces to one value per year — see the handover.)*
3. **Physics.** Coastal retreat lowers the seaward boundary head, a year-round boundary
   condition. Whether the drawdown gradient is itself seasonal is legitimate, but two subset
   fits with overlapping CIs answer it weakly.

**Still open (Martin's call):** if "is the coastal gradient itself seasonal?" is worth
answering properly, the clean test is a **season × δ(d)·t interaction on the full panel** —
one model, all 12,456 obs, an actual p-value — rather than comparing two subset fits. Small
addition to `fit_panel()`. Not in the base build.

---

## Build plan

**`src/14_climate_projections.py`** (version bump) — spring-mean centroid trend alongside
summer/winter; emit `14_spring_trend_stats.csv`. CSV only — **open:** does Martin want a
spring figure to match the summer/winter ones?

**`src/25_coastal_gradient.py`** v1.4.0 → v1.5.0 — parameterise on
`metric ∈ {summer_min, spring_mean}`, following the `_METRICS` + `_run_metric()` pattern
established in 09c v1.5.0 (batch 1):
* `compute_per_well_slopes(long, metric)` — summer: min of `SUMMER_MONTHS` by hydro year
  (unchanged). Spring: mean of `MSL_SPRING_MONTHS` by calendar year, `MSL_MIN_MONTHS_PER_SPRING`
  guard. Identical OLS, `PANEL_OBS_MIN_YEARS` guard, output columns.
* `cluster_partition(..., metric)` — reads the matching Script 14 CSV. Identical maths.
* `main()` runs **both** metrics in one pass. No new registered pipeline step, so
  `_EXPECTED_ANALYTICAL_TOPLEVEL = 39` and the 46/17 headline are untouched. Optional
  `--metric` CLI flag for ad-hoc runs.

**Outputs** (new `paths.py` constants; nothing committed overwritten):
* `25_02_per_well_spring_mean_slopes.csv`
* `25_03_cluster_partition_spring.csv`
* `25_05` / `25_07` spring figure analogues
* `25_08_spring_vs_summer_comparison.csv` + figure
* `25_01_panel_fit_parameters.csv` gains MAM-only sensitivity rows (`forest_free_mam` etc.)
  beside the existing all-season rows
* `25_04` **not** re-emitted

**Regression bar:** every committed Script 14 and Script 25 output must reproduce
byte-identically (the standard met in batch 1). Beware: figure text built from f-strings
must render the exact prior wording — in batch 1 a `title`-cased ylabel silently changed
two committed PNGs until caught by the diff.

**Not in this build:** report placement (build outputs, show Martin, then decide main report
vs supplement); the spring-mean MSL5 threshold-exceedance variant (still open).

## Guardrails
All I/O via `paths.py`; constants from `config.py`; no hardcoded values; `console_utils`
output; `MPL_DEFAULTS` / `render_figure` house style; every number traces to a committed CSV;
even-handed framing. CHANGELOG delta + version bumps. Claude does not push — Martin runs
`nrg_git.sh` option 2. **Next session: have the Claude desktop app open so the device bridge
attaches and files can be written straight into `/home/john/projects/NRG`.**
