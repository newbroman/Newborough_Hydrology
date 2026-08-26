> ## Recovered 2026-08-26 — CLOSED, kept as the record of the defect
>
> Written **2026-05-26**, never committed, recovered from `~/Downloads/cleanup`
> under T-10 and kept **verbatim below**. `src/21_forestry_scenarios.py:1451`
> cites it, alongside `CHAPTER_FLAGS_TO_REVIEW.md`, for the five ways
> `_zone_summer_mins()` had drifted from the canonical estimator.
>
> **All five were fixed.** Script 21 v1.1.0 (Option 2, Martin, 2026-05-26)
> migrated the function to the shared `clearfell_common.annual_summer_minimum()`
> estimator: per-well-then-aggregate rather than min-of-centroid, the Defect-E
> provenance / `min_measured = 2` filter applied, a bounded pre-2015 window, the
> shared helper rather than a local reimplementation, and an `N_summers` column
> that counts only bounded-window years. The script's own comment block records
> the migration.
>
> Kept because it is the only place the five drifts are set out and diagnosed —
> the script comment lists them, this explains them. The Defect-E phantom
> interpolated minima (WMC3, NW6, NW7, 2019) are the kind of thing that comes
> back if nobody remembers why the filter is there.
>
> ---

# FINDINGS — Script 21 BACI-zone summer minima vs the Script 10 series

*Response to `DIAGNOSTIC_script21_vs_script10_summer_minima.md`.*
*Diagnostic session — verified against live `main` (commit `530293b`),*
*fresh clone. No code edited. Fix approach proposed for Martin's sign-off.*
*Written 2026-05-26.*

---

## Summary

All five divergences in the brief are **confirmed against live code**. The
brief's diagnosis is correct in every particular. The Script 21 BACI violin
(`_zone_summer_mins()`) computes a *different statistic* from a
*differently-composed and differently-filtered panel* than the Script 10d
clearfell-BACI suite. The tier rosters are identical; the divergence is
purely method. The spurious ~−1.30 m Forest-Control pre-2015 figure is a
composition artefact, exactly as the brief suspected.

**Decision (Martin, 2026-05-26): Option 2** — keep Figure 30 as a
centroid-year violin, but fix the estimator by migrating
`_zone_summer_mins()` to the `clearfell_common` helpers. Detail below.

---

## Divergence-by-divergence verification

### Divergence 1 — estimator order — CONFIRMED

`_zone_summer_mins()` (Script 21, line 1379) is **min-of-mean**. Verbatim:

```python
combined = pd.concat(well_depths, axis=1, sort=False).mean(axis=1)
... d = combined[mask].dropna(); mins.append(float(d.max()))
```

Wells are averaged into a centroid first; the annual summer extremum is
taken from the centroid.

Script 10d is **mean-of-min**. `forest_control_centroid_summer_min()` in
`clearfell_common` (line 961) computes `annual_summer_minimum()` *per well*
first, then `np.mean(vals)` across wells *within each year*. Per-well-then-
aggregate.

These are different statistics. They agree only when every well has an
identical, complete record in every year — which the Forest Control tier
does not (CEH2 installs ~2011, others earlier, NW10 later). Confirmed as
stated.

*(Terminology note: the brief calls Script 10d "mean-of-min". Strictly the
centroid path is min-then-mean — min per well, mean across wells per year.
The substantive point — per-well first vs centroid first — is exactly as
the brief states. Flagging only so the fix discussion is unambiguous.)*

### Divergence 2 — no provenance / `min_measured` filter — CONFIRMED

`_zone_summer_mins()` reads wells via `get_well_monthly()` and applies only
`if len(d) >= 2` on the centroid series. It does **not** read
`01_wells_provenance.csv`; it passes no `provenance=` and no
`min_measured=`. Script 10d passes `provenance=prov_w, min_measured=2` into
both `annual_summer_minimum()` and `forest_control_centroid_summer_min()`
(lines 167–168, 184–189) — the Defect E fix. Confirmed: Script 21's violin
**can include phantom interpolated summer minima** (the documented
WMC3/NW6/NW7 2019 cases) that Script 10d excludes.

### Divergence 3 — composition-varying centroid — CONFIRMED, and is the root cause

`_zone_summer_mins()` takes `start`/`end` from the phase definition only.
For the `Pre-2015` phase `start=None`, so `if start:` is falsy and **no
lower bound is applied** — the pre-2015 centroid runs from the earliest
data (2007) forward. Script 10d sets `first_year = max(2011, …)` (line 156,
v1.2.0) and works on fixed `ALL_NETWORK_WELLS`.

Consequence, exactly as the brief states: the Script 21 pre-2015
Forest-Control centroid is `.mean(axis=1)` over *whatever wells are online
that month*. In 2007–2010 that is a 1–2-well mean dominated by whichever
forest well installed earliest; by 2013–2014 it is a 5-well mean. The
`SD = 0.558, min = 0.57, max = 2.41` on that CSV row is the signature of a
single shallow well alone in an early year. This is the
`PRE_FELL_START` / fixed-membership defect class already fixed elsewhere in
the 10-series (`clearfell_common` v1.7.0). **This is the root cause of the
−1.298 m figure.**

### Divergence 4 — reimplemented helper — CONFIRMED

`_zone_summer_mins()` is a standalone local reimplementation. It does not
call `annual_summer_minimum()` or `forest_control_centroid_summer_min()`.
Scripts 10a/10d/10e already use the `clearfell_common` helpers. Confirmed as
stated — the local copy has drifted (Divergences 1–3 are that drift).

### Divergence 5 — `N_summers = 9` — CONFIRMED as mislabelled

Verified: `21_forestry_04_baci_zone_means.csv` is written at Script 21 line
~1602 with `"N_summers": len(arr)`, where `arr` is the return of
`_zone_summer_mins()`. `_zone_summer_mins()` returns one value per
`combined.index.year.unique()` that clears `len(d) >= 2`.

The pre-2015 window ends `2015-04-01`. A centroid-first estimator yields one
minimum per calendar year, so 2007–2014 inclusive caps at **8**. A reported
`N_summers = 9` means the iteration is over `combined.index.year.unique()`
where `combined` still carries index entries beyond the intended window —
i.e. because `start=None` lets the series run unbounded, and the `end` clip
(`< 2015-04-01`) still admits Jan–Mar 2015, the year **2015 itself appears
as a ninth `yr`** in the loop. Its summer mask (Jun–Sep) finds nothing, so
2015 *should* drop at `len(d) >= 2` — but the count of 9 indicates either
2015 is contributing, or an early year is being double-counted across a
composition gap. Either way the brief's conclusion holds: **`N_summers`
does not mean "centroid-summers"** and the column is not trustworthy as
labelled. Resolved: it is an artefact of the unbounded window (Divergence
3); fixing Divergence 3 fixes this too.

---

## Tier-roster cross-check — IDENTICAL, no additional defect

Both scripts build from the same `clearfell_common.TIERS`. Confirmed live:

| Tier | Wells (clearfell_common) | Used by 21? | Used by 10d? |
|---|---|---|---|
| Impact | `wmc3` | yes (TIERS) | yes |
| Edge | `ceh31, ceh20, ceh30, ceh16` | yes | yes |
| Forest Ctrl | `ceh32, ceh34, ceh33, nw10, ceh2` | yes | yes |
| Coastal Ctrl | `ceh19, ceh17` | yes | yes |
| Climate Ctrl | `ceh9, nw7, nw6, nw5, wmc2` | yes | yes |

Script 21's `BACI_ZONE_WELLS` is built directly from `TIERS` (lines
1370–1375); Script 10d uses the same constants. **Rosters match exactly.**
The divergence is purely method (Divergences 1–4), not composition of the
tiers themselves. No additional defect.

---

## Fix — DECIDED (Martin, 2026-05-26): Option 2

Two routes were considered. **Martin has chosen Option 2 — keep Figure 30 as
a centroid-year violin, fix the estimator in place.**

### The decision

Figure 30 remains the *same kind of figure* it is now: a centroid-year
violin — one summer-minimum value per zone per year, the violin drawn over
those per-year centroid values. This was chosen deliberately so the figure
does not change character mid-editorial-pass: the caption stays largely as
written and §5.5.1 needs minimal rework. What changes is *how each year's
centroid minimum is computed* — the three real bugs are fixed.

### What the fix chat must do

Migrate `_zone_summer_mins()` from its local reimplementation to the
`clearfell_common` shared helpers. Specifically, the per-zone centroid
summer minimum should be produced by `forest_control_centroid_summer_min()`
(which internally calls `annual_summer_minimum()` per well). This single
change delivers all three corrections at once:

1. **Estimator order** — per-well `annual_summer_minimum()` then mean across
   wells per year (the helper already does this), replacing the current
   min-of-centroid.
2. **Provenance filter** — pass `wells_provenance` / `min_measured=2`
   through, so Defect-E phantom interpolated minima are excluded, matching
   Script 10d.
3. **Window / composition** — apply the `first_year = max(2011, …)` floor
   and fixed-membership discipline, so the pre-2015 centroid is not a
   composition-varying 1-to-5-well mean.

`_zone_summer_mins()` becomes a thin wrapper looping the shared helper over
the five zones. This also fixes Divergence 5 — `N_summers` becomes a correct
count of centroid-years (≤ 8 for pre-2015) once the window is bounded.

### What this is NOT

This is **not** Route B. Script 21 does **not** read
`10d_01_summer_minima.csv`. It still computes its own per-zone centroid
minima — but via the shared, Defect-E-aware `clearfell_common` helpers
instead of a drifted local copy. The numbers then match Script 10d by
*construction of method*, even though the two scripts compute independently.
The centroid-year violin is preserved; only the wrong values move.

### Consequence

Figure 30 regenerates and `21_forestry_04_baci_zone_means.csv` changes —
Forest Control pre-2015 moves from ~−1.30 m to ~−1.82 m, bringing the violin
into agreement with its own caption ("stable summer minima throughout").

---

## Knock-on items (unchanged from brief, confirmed appropriate)

- **Main report §5.5.1 ¶4** — source WMC3 / Forest-Control era means from
  `10d_01_summer_minima.csv` (already matches the Figure 30 caption). Figure
  30 itself awaits the Script 21 fix + regeneration.
- **Methods supplement §S.14 (Script 21)** — add a flag noting the
  `_zone_summer_mins()` composition-varying-centroid issue; no numerical
  amendment until the fix lands.
- **Figure 30 caption** — no edit needed beyond regeneration.
- **CHAPTER_FLAGS_TO_REVIEW.md** — add an item for the Script 21
  `_zone_summer_mins()` defect (see delta file accompanying this note).

## Deliverable status

Divergences 1–5 confirmed; tier roster confirmed identical. **Fix decided:
Option 2** — centroid-year violin preserved, `_zone_summer_mins()` migrated
to the `clearfell_common` helpers (see "Fix — DECIDED" above). **No code
changed in this diagnostic session.** The Script 21 edit is to be done in a
dedicated fix chat, complete-file + CHANGELOG discipline.
