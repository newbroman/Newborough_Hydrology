> ## Recovered 2026-08-26 — BUILT, kept as the design record
>
> Written **2026-07-06**, never committed, recovered from Trash under T-10 and
> kept **verbatim below**. `src/37b_driver_footing.py:7` cites it as its design
> document.
>
> **Its "design document for sign-off, no code until approved" header is spent.**
> It was approved — the script header records "Sign-off decisions (2026-07-06)" —
> and `37b_driver_footing.py` is now at **v1.3.0 (2026-08-22)**, six weeks and
> several revisions past this spec.
>
> Read it for the reasoning behind the comparative-footing design: the common
> currencies, the shared 2005–2025 horizon, and what it amends in
> `SPEC_script37_scale_factor_regression_2026-07-06.md` (which is still missing —
> it is on the T-10 list). Do **not** read the numbers or the routing note as
> current; the script has moved.
>
> ---

# SPEC — Part B: comparative driver footing (forest · scrape · coast)

*Amends:* `SPEC_script37_scale_factor_regression_2026-07-06.md`, Part B section.
*Design document for sign-off. No code until approved.*
*Model routing:* this spec + interpretation → Fable/Opus; **build → Sonnet 5**;
run + CHANGELOG_delta → Haiku 4.5.

---

## Purpose — the whole story on one footing

Put the three drivers side by side in the **same currencies** so a reader can see
their relative weight at a glance, over a common **2005→2025** horizon. This is
the comparison your goal 2 asked for (forest comparable to scrape and coast) and
the honest test of the report's "scraping worsens site-wide decline" claim.

**Critical design constraint:** Part B does **not** use Script 37's scale factors
(unresolved/null — Part A). It rests on **observed anchors** (BACI steps) and the
**modelled Script 20 fields**, with every cell flagged observed or modelled. The
even-handedness rule is enforced structurally: each driver is entered as a
**gain component and a loss component**, because all three are in fact two-sided.

| Driver | Gain component | Loss component |
|---|---|---|
| Forest management | Clearfell (canopy removed) | Broadleaf restock (canopy added) |
| Dune scraping | On-site slack rise | Off-site drain cone |
| Coast | Sea-level rise (head gain) | Chronic erosion drawdown |

At the 2025 horizon all step effects (clearfell 2017; scrapes 2013/2015/2023) are
fully realised; coast is 20 × δ₀. A **mechanism-type** column carries the
distinction the record forces us to keep — *step* (one-off, persistent),
*redistributive* (local rise + neighbour draw), *progressive* (accumulating) —
so the comparison never implies these are the same kind of quantity.

---

## Housing — sign-off decision

Two options; pick one:

- **(A, recommended) New Script 37b** (analytical, Phase 15, after Script 37).
  Emits the comparison CSV + figure. **Cost:** pipeline 44→45, analytical
  41→42 (phases unchanged 17/16); Abstract/Conclusions/Methods count updates
  needed.
- **(B) Extend Script 09f** (the existing display/utility spatial-reach synthesis
  figure). **No analytical-count change**, reuses 09f's first-pass fallback
  machinery for λ, δ₀, L. But 09f becomes heavy and the comparison CSV then rides
  under a display/utility script.

Recommendation: **(A)** — the integrals and threshold counts are genuinely
analytical and produce report-cited numbers, so they deserve an analytical slot.
If you want zero count-churn, **(B)** is defensible. *Your call.*

---

## The three currencies

### Currency 1 — Peak local head change (mm)

One number per component, at its worst-affected point. Mostly observed:

| Component | Peak (mm) | Source | Flag |
|---|---|---|---|
| Clearfell | +119.6 | `10a_report_numbers.csv` ANCOVA step ×1000 | observed |
| Broadleaf restock | ≈ −56 | Script 20 increment (indicative) | modelled |
| Scrape on-site | +129.5 | `09_scrape_03_baci_shifts.csv` CEH36 | observed |
| Scrape off-site | −55 | WMC3 DiD (observed); modelled cone larger near-field | observed |
| Coastal drawdown | −581 | δ₀ × 20 yr (δ₀ from Script 25) | modelled |
| SLR | +20 | Script 20 SLR strip | modelled |

Reads coast as dominant — but this is peak-at-a-single-point; coast's peak is only
at the shoreline and decays over L = 894 m. Currency 2 corrects for that.

### Currency 2 — Area-integrated change (mm·ha, and m³)

Integrate each **Script 20 unit field at its 2025 amplitude** over the site mask
(`make_site_mask`, canonical extent E 240100–243900, N 362200–365500):

```
mm_ha = Σ_cells ( h_field(cell) [mm] × cell_area [ha] )
m3    = Σ_cells ( h_field(cell) [m]  × cell_area [m²] × Sy(cell) )
```

This is where scraping's real footing appears: the **on-site rise** is
small-area/high-amplitude, the **off-site drain cone** is large-area/low-amplitude
(decay length λ ≈ 224.9 m from `20_report_numbers.csv`). Report the scrape as
**rise integral, drain integral, and net** — the sign of the net is the
quantitative basis for "scraping worsens the site-wide table while benefiting the
slack." Expect the coastal integral (20-yr accumulation over the L-band) to
dominate all others by volume; that comparison is the point.

**Sy — sign-off decision.** Primary: per-driver **representative Sy** from the
cluster each field predominantly occupies (scrape/coast → C3 0.311; forest →
C4/C5 ≈ 0.25–0.31), traceable and transparent. Optional robustness: **per-cell
Sy** from a cluster-membership raster. Recommend representative Sy for the
headline, note the ±40% Sy spread as a caveat. *Which?*

### Currency 3 — Ecological threshold crossings (Curreli)

Per-well, primary (avoids double interpolation):

1. Baseline = observed **summer-minimum depth** per well from
   `14_annual_extremes.csv` (the Fig 34 source).
2. Add each component's head delta, evaluated at the well from its Script 20 field.
3. Count wells crossing the **Curreli summer thresholds**: wet-slack **−0.61 m**,
   dry-slack **−0.98 m** (from `config.py`), with the sign convention: a positive
   head delta is a *rise* (toward wetter, away from the deep negative threshold).

This is the decision-relevant currency and it exposes the even-handed truth:
**coast** pushes coastal-margin slacks toward drying (crossings worsen);
**clearfell** *raises* levels in its footprint (crossings relieve — a local
ecological benefit); **scrape** is two-sided (on-site relief, off-site worsening).
Report crossings per component in both directions. Optional secondary: area
crossing (needs the baseline IDW surface + field surfaces) — flag as modelled.

---

## Inputs (all traced to committed CSVs — no hardcoded values)

| Quantity | Source |
|---|---|
| Clearfell step | `10a_report_numbers.csv` (ANCOVA_Forest_Impact_clearfell_step) |
| Scrape on-site / off-site | `09_scrape_03_baci_shifts.csv`; WMC3 DiD from scraping outputs |
| δ₀, L | `OUT_25_FIT_PARAMETERS` (forest-free linear-capped) |
| Drain-cone λ | `20_report_numbers.csv` (drawdown_lambda) |
| Fields | Script 20 v1.32.0 builders via `importlib.util` (as Script 37) |
| Sy per cluster | canonical WTF/cluster Sy (config / committed CSV) |
| Curreli thresholds | `config.py` |
| Baseline summer minima | `14_annual_extremes.csv` |

First-pass fallbacks (λ, δ₀, L, Sy) via `pipeline_params.default_value()` per the
existing 09f precedent, with console warnings.

---

## Outputs

| Path constant | File |
|---|---|
| `OUT_37B_COMPARISON` | `37b_driver_footing.csv` — component × currency, mechanism-type, observed/modelled flag |
| `OUT_37B_FIGURE` | `37b_driver_footing.png` — grouped bars, one panel per currency (or the three currencies as sub-panels) |
| `OUT_37B_RESULTS` | `37b_results.txt` — the whole-story summary + caveats |

Map/figure discipline: `MPL_DEFAULTS`, `console_utils`, `present_files`. Dates
`%b %Y`/`%Y` on any axis, JPEG q85.

---

## Even-handedness (enforced, per working rules)

- Every cell flagged **observed** or **modelled**; coast (both components),
  broadleaf, scrape off-site cone and SLR are modelled; clearfell, scrape on-site
  and scrape off-site (WMC3 DiD point) are observed.
- Coast's 20-yr drawdown is stated as a **modelled projection anchored on the
  observed δ₀, unconfirmed spatially by Part A** — never as a validated site-wide
  loss.
- Language: "indicates" / "consistent with", not "confirms" / "demonstrates".
- The "scraping worsens site-wide" claim is reported **with its magnitude in
  context** — i.e. its net integral set against the coastal integral — so the
  reader sees it is (if negative at all) a minor contributor beside coast, not a
  headline driver.

---

## What Part B does NOT do

- Does not use Script 37 scale factors (null; Part A owns that verdict).
- Does not close a water budget — first-order superposition, an upper bound in
  overlap zones (same caveat as the Script 20 map).
- Does not resolve the near-field scrape cone observationally (nearest uphill
  well 247 m — modelled).
- Does not re-estimate any driver amplitude — it *places* the established
  observed/modelled amplitudes on common axes.

---

## Sign-off checklist

1. **Housing:** new Script 37b (A, recommended) vs extend 09f (B). — *decide.*
2. **Sy for volume:** per-driver representative (recommended) vs per-cell. — *decide.*
3. **Two-sided component structure** (gain + loss per driver) and mechanism-type
   column. — *agree?*
4. **Threshold currency per-well primary**, area secondary/modelled. — *agree?*
5. **Baseline = `14_annual_extremes.csv` summer minima.** Confirm this is the
   right baseline surface (vs an MSL5 / Script 26 basis). — *confirm.*
6. Once signed off: build on Sonnet, bring `37b_results.txt` back here to read the
   whole-story summary before it goes near the report.
