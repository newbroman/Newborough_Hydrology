> ## Recovered 2026-08-26 — CLOSED, kept as the record of the question
>
> Written **2026-05-26** during the §5.5.1 editorial pass, never committed,
> recovered under T-10 from `~/Downloads/cleanup/` and kept **verbatim below**.
> It is a dated record and is not edited.
>
> **Why the citation dangled.** `FINDINGS_script21_summer_minima.md:25` opens
> *"Response to `DIAGNOSTIC_script21_vs_script10_summer_minima.md`"*. The answer
> was recovered into this repository earlier on 2026-08-26; the question was
> still outside it. `docref_lint.py` recorded the pair as "the answer survived
> and the question did not". It has now survived too.
>
> ---
>
> ### Status today, checked against the committed tree: all five divergences are FIXED
>
> **Do not raise these as open defects.** Script 21 **v1.1.0** (Option 2, Martin,
> 2026-05-26) migrated `_zone_summer_mins()` to the shared estimator. The
> script's own comment block at `src/21_forestry_scenarios.py:1449` lists the
> same five drifts this brief diagnosed and records the migration:
>
> > *"As of v1.1.0 (Option 2, Martin 2026-05-26) the function is migrated to the
> > shared `clearfell_common.annual_summer_minimum()` estimator. Each well's
> > per-year summer minimum is computed individually, with the Defect-E
> > provenance / min_measured=2 filter, and the per-year zone value is the MEAN
> > across wells (per-well-then-aggregate). This matches Script 10d's method by
> > construction."*
>
> Divergence by divergence, verified 2026-08-26:
>
> | # | Brief's finding | Today |
> |---|---|---|
> | 1 | min-of-centroid, not mean-of-min | fixed — per-well `annual_summer_minimum()`, then cross-well mean |
> | 2 | no provenance / `min_measured` filter | fixed — `min_measured=2` passed at `21_forestry_scenarios.py:1641`; `01_wells_provenance.csv` loaded at line 1498 |
> | 3 | unbounded, composition-varying pre-2015 window | fixed — `_BACI_ZONE_FIRST_YEAR = 2011`, `_BACI_ZONE_LAST_YEAR = 2025`, matching Script 10d's `first_year = max(2011, …)` |
> | 4 | local reimplementation, not the shared helper | fixed — calls `clearfell_common` |
> | 5 | `N_summers` counted well-years, not centroid-years | fixed — pre-2015 now reports **N_summers = 4** (2011–2014), not 9 |
>
> **The brief's numerical prediction landed.** It said the Forest Control
> pre-2015 figure "will move from ~−1.30 m to ~−1.82 m, bringing the violin into
> agreement with its own caption". Today
> `outputs/21_forestry_scenarios/21_forestry_04_baci_zone_means.csv` gives Forest
> Ctrl **1.8855 / 1.7533 / 1.7760 m** across the three phases — a ~13 cm spread,
> stable, not the spurious ~275 mm deepening. Impact (WMC3) pre-2015 is
> **1.5733 m at N = 3**, matching the Script 10d value the brief quoted. The
> figure was regenerated; caption and figure agree.
>
> **Units caveat before comparing any number here with Script 10d.** The brief
> compares Script 21 and `10d_01_summer_minima.csv` figures directly. Since the
> migration they are in different units — Script 21 plots depth below ground
> (positive), `clearfell_common` and 10d work in raw pipe-relative depth — and
> the conversion carries a per-well upstand offset spanning 0.04–0.71 m in the
> Forest Control tier. The two now **match by method, not by value**
> (`21_forestry_scenarios.py:1468–1480`). The sign-flipped comparisons in the
> table below are of their period, not a template.
>
> ### What is durable
>
> - **The five-divergence anatomy.** This is the only place they are set out as a
>   diagnosis rather than as a five-line code comment. The Defect-E phantom
>   interpolated minima (WMC3, NW6, NW7, 2019) are exactly the class of thing
>   that returns once nobody remembers why the filter is there.
> - **The composition-varying-centroid failure mode** — a control centroid whose
>   membership changes through the record produces a spurious trend. It is the
>   same defect the fixed-membership migration fixed in the 10-series, and the
>   brief's diagnosis of it (§ Divergence 3) is the clearest statement of it in
>   the project.
> - **The estimator-order distinction** (min-of-mean vs mean-of-min) and why
>   unequal record lengths make them disagree.
>
> ### What is dated
>
> - **Every number in the comparison table**, on both sides.
> - **Section and figure numbering.** "Figure 30" is now **Figure 33**; "§5.5.1"
>   is now §4.6.3 / §4.6.4; the methods-supplement chapter is S.14 as stated but
>   its numbering has moved with the rest.
> - **The repository line.** "`github.com/newbroman/Newborough_Hydrology`, branch
>   `main`. Clone fresh." was the working arrangement in May; it is not a current
>   instruction.
> - **The "Recommended fix direction" and "Deliverable from the receiving chat"
>   sections are spent.** The findings note was written, the fix approach was
>   approved, and v1.1.0 landed — all on the same day, 2026-05-26.
>
> ### One item this closes and one it leaves
>
> The brief's knock-on list asked for a methods-supplement flag on the
> `_zone_summer_mins()` issue "update once the script fix lands". The fix landed.
>
> **Still open, and not introduced by the recovery:** the live Figure 33 caption
> (`report_edits/text/report9.md:437`) reads "Summer minimum depth distributions
> by BACI tier, Newborough Warren **2007--2026**". Since the v1.1.0 migration the
> BACI-zone window is bounded to **2011–2025**. The caption's stated span no
> longer matches the figure's. Flagged here, not fixed.

---

# DIAGNOSTIC BRIEF — Script 21 BACI-zone summer minima vs the Script 10 series

**Date raised:** 2026-05-26 (during §5.5 main-report editorial pass)
**Type:** Diagnostic — verify data-set and method consistency; recommend a code fix
**Repo:** `github.com/newbroman/Newborough_Hydrology`, branch `main`. Clone fresh.
**Scope:** `src/21_forestry_scenarios.py` — the `plot_baci_zone_violin()` /
`_zone_summer_mins()` pair that produces Figure 30 of the main report.

---

## Why this brief exists

The §5.5.1 editorial pass needs the WMC3 (Impact) and Forest-Control summer-minimum
era means for Figure 30. Two pipeline outputs disagree, and the disagreement is not a
rounding difference — it is a different statistic computed from a differently-composed
panel:

| Tier / phase | Script 10d (`10d_01_summer_minima.csv`) | Script 21 (`21_forestry_04_baci_zone_means.csv`) |
|---|---|---|
| Forest Ctrl pre-2015 | **−1.822 m** (n=18 well-years) | **−1.298 m** (N_summers=9) |
| Forest Ctrl 2015–17 | −1.753 m | −1.553 m |
| Forest Ctrl post-fell | −1.766 m | −1.573 m |
| Impact (WMC3) pre-2015 | −1.573 m (n=3) | −1.437 m (N_summers=5) |

Script 10d shows the Forest Control tier **stable** across all three phases (~6 cm
spread). Script 21 shows it **deepening by ~275 mm**. The main report's Figure 30
caption states "the Forest Control group shows stable summer minima throughout" —
which matches Script 10d, not Script 21. But Figure 30's *violin* is drawn by
`plot_baci_zone_violin()` in Script 21. So the figure and its own caption are
inconsistent, and the §5.5.1 prose cannot be finalised until the source is settled.

---

## What the diagnostic must establish

The task is to confirm whether `plot_baci_zone_violin()` / `_zone_summer_mins()` in
Script 21 operate on the **same data set and the same method** as the Script 10
clearfell-BACI suite (10a/10d in particular). The investigation below has already
identified five candidate divergences — the receiving chat should verify each against
the live code and report findings; it should **not** edit code without Martin's
sign-off on the fix approach.

### Divergence 1 — estimator order (centroid-first vs well-first)

`_zone_summer_mins()` (Script 21, ~line 1379) does:

```python
combined = pd.concat(well_depths, axis=1).mean(axis=1)   # average wells FIRST
mins = [combined[summer_mask_for_year].max() ...]         # THEN take annual min
```

i.e. **min-of-mean**: average the wells into a single zone centroid, then take that
centroid's annual summer minimum.

Script 10d does the opposite — **mean-of-min**: `annual_summer_minimum()` per well,
then aggregate the per-well minima.

These are different statistics and will not match when wells have unequal record
lengths. Confirm which order each script uses and whether that is intended.

### Divergence 2 — no provenance / `min_measured` filter in Script 21

Script 10d passes `provenance=` and `min_measured=2` into `annual_summer_minimum()`
and `forest_control_centroid_summer_min()` — the **Defect E fix** — so well-years
with fewer than two measured Jun–Sep readings (phantom interpolated minima) are
dropped. WMC3/NW6/NW7 2019 are the documented cases.

`_zone_summer_mins()` in Script 21 applies **no provenance filter** and only a
`len(d) >= 2` check on the centroid series — it does not read `01_wells_provenance.csv`
at all. Confirm: does Script 21's BACI violin include phantom interpolated summer
minima that Script 10d excludes?

### Divergence 3 — year window / composition control

Script 10d sets `first_year = max(2011, …)` — "2011 is the first year all 17 network
wells have complete observed Jun–Sep coverage" — and works on the fixed
`ALL_NETWORK_WELLS` set. Script 21's `_zone_summer_mins()` takes `start`/`end` from
the phase definition only (`Pre-2015` phase has `start=None`), so the pre-2015 centroid
spans **2007 onward** and averages whatever wells happen to be online in each year.
For the Forest Control tier the member wells have very different install dates
(CEH2 ~2011, CEH32/33/34 earlier, NW10 later), so the pre-2015 centroid is a
**composition-varying** series — its early years are a 1–2 well mean, its later years
a 5-well mean. This is the most likely root cause of the spurious 1.298 m pre-2015
figure (note that row's SD = 0.558 m, min = 0.57 m, max = 2.41 m — a single shallow
well alone in an early year).

This is the same class of defect that the `PRE_FELL_START` / fixed-membership
control-centroid migration fixed elsewhere in the 10-series (`clearfell_common`
v1.7.0, `AUDIT_10series_PRE_FELL_START.md`). Confirm whether Script 21's BACI violin
should adopt the same fixed-composition / fixed-start discipline.

### Divergence 4 — reimplemented helper vs shared helper

Script 10d calls `annual_summer_minimum()` and `forest_control_centroid_summer_min()`
from `clearfell_common` (the single-source-of-truth helpers, Defect-E-aware).
Script 21 reimplements the calculation locally in `_zone_summer_mins()`. Even if the
two were intended to match, a local reimplementation will drift. Confirm whether
Script 21's BACI violin can be migrated to call the `clearfell_common` helpers
directly, the way Scripts 10a/10d/10e already do.

### Divergence 5 — N_summers count looks wrong

`21_forestry_04_baci_zone_means.csv` reports `N_summers = 9` for Forest Ctrl pre-2015
and `N_summers = 8` for Edge pre-2015. Pre-2015 (the window end is 2015-04-01) covers
hydrological summers 2007–2014 = **8 years maximum**. A centroid-first estimator
produces **one** minimum per year, so `N_summers` should be ≤ 8. A value of 9
suggests `N_summers` is being counted as well-years, not centroid-years — i.e. the
column does not mean what its name says, or the estimator is not purely centroid-first.
Resolve what `N_summers` actually counts.

---

## Tier-definition cross-check (do both scripts use the same wells?)

Confirm that the BACI tier rosters Script 21 uses are **identical** to the Script 10
suite's. Script 21 builds `BACI_ZONE_WELLS` from `TIERS` in `clearfell_common`
(lines ~1362–1376) — and Script 10d uses `FOREST_CONTROL_WELLS`,
`CLIMATE_CONTROL_WELLS`, `ALL_NETWORK_WELLS` from the same module. They *should*
match, but verify:

- Forest Control tier: 10d gives `CEH2, CEH32, CEH33, CEH34, NW10` (5 wells).
- Confirm Script 21's `TIERS['Forest Ctrl']` (or equivalent) resolves to the same 5.
- Repeat for Impact (WMC3), Edge, Coastal Ctrl, Climate Ctrl.

If the tier rosters match but the numbers don't, the divergence is purely
method (Divergences 1–4); if the rosters differ too, that is an additional defect.

---

## Recommended fix direction (for Martin's decision, not to apply unilaterally)

The Script 10d method is the canonical one — per-well `annual_summer_minimum()` with
`provenance`/`min_measured=2`, fixed `ALL_NETWORK_WELLS`, `first_year` floor. The
cleanest fix is to make `plot_baci_zone_violin()` / `_zone_summer_mins()` consume the
**same** `clearfell_common` helpers and the **same** per-well-then-aggregate method,
or — simplest of all — to have Script 21 read `10d_01_summer_minima.csv` directly
rather than recomputing summer minima from raw wells. Script 10d already runs earlier
in the pipeline (Phase 3) than Script 21 (Phase 10), so the dependency direction is
available.

Whichever route is chosen, the consequence is that **Figure 30 must be regenerated**
and `21_forestry_04_baci_zone_means.csv` will change — the Forest Control pre-2015
figure in particular will move from ~−1.30 m to ~−1.82 m, bringing the violin into
agreement with its own caption.

## Knock-on items

- **Methods supplement §S.14 (Script 21)** — no numerical amendment needed yet, but
  add a flag noting the `_zone_summer_mins()` composition-varying-centroid issue;
  update once the script fix lands.
- **Main report §5.5.1 ¶4** — the editorial pass will source the WMC3 / Forest-Control
  era means from `10d_01_summer_minima.csv` (the robust series), which already matches
  the Figure 30 caption. The figure itself awaits the Script 21 fix + regeneration.
- **Figure 30 caption** — its `Source:` line currently names
  `21_forestry_04_baci_zone_violin.png`; that is correct as the file name, but the
  file's *content* is what this brief is about. No caption edit needed beyond what
  the regeneration produces.

## Deliverable from the receiving chat

A short findings note confirming or correcting each of Divergences 1–5 and the tier
roster cross-check, plus a recommended one- or two-line fix approach for Martin to
approve. Code changes to Script 21 should be made only after that approval, in a
dedicated fix chat, with the usual complete-file + CHANGELOG discipline.
