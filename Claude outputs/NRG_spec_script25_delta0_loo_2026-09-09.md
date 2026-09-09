# Spec — Script 25: leave-one-out leverage of δ₀ on the headline panel (25_16), so D-046's "stated wherever δ₀ is quoted" can be met with a committed number (for sign-off)

**Provenance.** Cowork session `01PhSvhMMGSWW9UnSFdTK5GU` · configured `claude-fable-5-1` · 2026-09-09.
Martin: "do it properly, spec the LOO". Design → sign-off → build; the run is the L14's.

## 1. Why
D-046 (2026-08-20) moved the forest-free panel from the cluster rule to the land-cover flag, which
brought ceh3 (176 m from the shore, the second-nearest well) into the headline panel and moved δ₀ from
−26.42 to −31.33 mm/yr. Its own Revisit-if/requirement reads: **"δ₀'s sensitivity to ceh3 is stated
wherever δ₀ is quoted; a single well carrying 2–4 mm/yr of a headline is a fact about the network, not a
defect to be hidden, but it must not go unmentioned."** Today no document states it — not Paper 1 §4.11
(which quotes δ₀ four ways), not report9 §4.10.2, not MS §S.15 — and the 2–4 mm/yr figure lives only in a
changelog's working table, not in any committed CSV. The project rule is that a number enters a document
only from a committed CSV, so the leverage has to be emitted before it can be quoted. R4 (the critique's
"quote canopy-controlled δ₀ and C3-only beside the headline") was found already done at v1_39; this is the
part of the δ₀ story still owed.

## 2. What Script 25 gains (1.25.0 → 1.26.0)

**`25_16_delta0_leave_one_out.csv`** (`paths.OUT_25_DELTA0_LOO`), one row per well in the headline
panel (forest-free, linear-capped, all-season — the `("forest_free", "linear_capped")` fit, currently 61
wells), each row the same fit with that well's rows withheld and everything else unchanged (same `p0`,
`bounds`, covariate, within-well demeaning):

| column | meaning |
|---|---|
| `well`, `cluster`, `dist_coast_m`, `n_obs_withheld` | identity and how much of the panel the well is |
| `delta_0_loo_mm_yr`, `delta_0_loo_se`, `L_loo_m`, `c_loo_mm_yr`, `delta_ref_loo_mm_yr` | the refit |
| `d_delta_0_mm_yr` | `delta_0_loo − delta_0_headline` (sign: what withholding the well does) |
| `d_delta_ref_mm_yr` | the same for the quoted 150 m rate |
| `abs_rank` | 1 = largest |abs(d_delta_0)| |

A trailing block is NOT added to this table; the summary goes to `25_report_numbers.csv`:

| key | meaning |
|---|---|
| `delta0_loo_n_wells` | panel size (61 today) |
| `delta0_loo_max_well`, `delta0_loo_max_well_dist_m` | the highest-leverage well and its distance |
| `delta0_loo_max_shift_mm_yr` | its `d_delta_0` |
| `delta0_loo_second_shift_mm_yr`, `delta0_loo_second_well` | the runner-up, so "about N times the next" is quotable |
| `delta0_loo_jackknife_se_mm_yr` | √((n−1)/n · Σ(δ₀,ᵢ − δ̄₀)²) — a model-free SE on δ₀ to set beside the fitted 1.97 |
| `delta0_loo_range_mm_yr` | max − min of the LOO estimates |
| `delta_ref_loo_max_shift_mm_yr` | the largest single-well shift in the 150 m rate (the number the paper quotes as headline) |

Every note string names the source file and the basis, in the house style of the existing rows.

**Figure `25_16_delta0_leave_one_out.png`** (diagnostic, not placed): `d_delta_0` against
`dist_coast_m`, the top three wells labelled, a dashed band at ± the fitted SE. `MPL_DEFAULTS`,
`render_figure`. Tier of the script unchanged; the figure joins Emits as a diagnostic.

**Cost.** One headline fit is a fraction of Script 25's 51 s; 61 refits are estimated at 1–2 minutes.
The loop prints its elapsed time. It runs by default: the whole point is that the number is committed
with every run. If the L14 measures more than 3 minutes, the loop moves behind `--with-supplementary`
(opt-in) and the spec is amended — Martin's call at that point.

**Code shape.** One new function `delta0_leave_one_out(df_ff, fit_ff_l, decay_func, p0, bounds,
distances) -> pd.DataFrame` beside `matched_window_sensitivity()`, which already does the
"refit a subset with the same settings" pattern; it calls the existing `fit_panel` and
`delta_at_distance` — no reimplementation of the fit. `p0`/`bounds` are passed through from the
call site (they are literals there today; this change does not add new ones). Report-number keys
are appended in `build_report_numbers`. A `paths.py` bump (1.16.2 → 1.17.0) adds the two paths.
Docstring outputs list, inline changelog, `SCRIPT_LEDGER` row 25 Emits (+25_16 csv, +25_16 fig);
`record_basis.csv` needs no new row (same wells, same record, same evaluation as RB-25's headline).

## 3. Verification (the artefact is read back, per CLAUDE.md)
- A "withhold nothing" control inside the function must reproduce `fits[("forest_free",
  "linear_capped")]` to machine precision (assert, not print).
- The ceh3 row should land near the 2026-08-20 working figure (−28.1 ± 2.3 when ceh3 is out of a
  −31.3 headline). A material departure is a finding to report, not to tune away.
- Read back from the written CSV: 61 rows, `abs_rank == 1` names one well, jackknife SE finite;
  `25_report_numbers.csv` carries the eight keys. Byte-identical `25_01`–`25_15` (the LOO reads,
  never writes, the existing fits).
- `check_all` on the L14 (record_basis_lint, rounding_lint, provenance, output_lag all touched).

## 4. Documents, after the run (numbers read from the CSV, not from this spec)
- **Paper 1 §4.11** (frozen; `REASON=<this changelog id>`, v1_40 → v1_41): one sentence after "…so
  the coast-proximal decline is not an artefact of the plantation's own drawdown.":
  > "The amplitude does carry one well's leverage: withholding ceh3, the second-nearest well to the
  > shore at 176 m, moves δ₀ by ⟨max shift⟩ mm/yr, ⟨ratio⟩ times the next-largest single-well shift
  > (leave-one-out over the ⟨n⟩-well panel, SI §S13.5); the jackknife standard error across the panel,
  > ⟨jk SE⟩ mm/yr, agrees with the fitted ⟨1.97⟩, so the leverage is a property of a network with few
  > wells inside 300 m rather than an instability of the fit."
  (If the jackknife SE does NOT agree with the fitted SE, the sentence says that instead — the
  wording is decided by the number.)
- **report9 §4.10.2** (live): the same sentence, cross-referenced to the CSV in the house style.
- **Methods Supplement §S.15** (frozen; REASON; bump): a short paragraph naming `25_16` and the
  jackknife construction; **Paper 1 SI §S13** gains sub-section S13.5 with the table's top five rows
  (REASON; bump) so the paper's "SI §S13.5" resolves.
- `citation_index` rows for the quoted values (the cite_check net); `D-046` Traces-to gains `25_16`
  and its requirement is marked met; changelog; register row (a new W-row, "δ₀ leverage stated",
  closed in the same batch); handover.

## 5. Not proposed
- Leverage for the other specifications (full, canopy, C3-only, MAM) — the headline is what is quoted;
  the CSV layout allows a `spec` column later if wanted.
- Dropping ceh3 anywhere (D-046 "Not adopted" already refuses it).
- A LOO on L_cg — L's SE (48 m) is not the contested number; it comes out of the same refits and is in
  the table (`L_loo_m`) without being summarised.

## 6. Order
1. Sign-off on this spec. 2. Bridge: Script 25 1.26.0, paths 1.17.0, ledger row, changelog draft.
3. L14: `python3 run_analysis.py --step 25`, then `--manifest-only` if needed; tell me it has run.
4. Bridge: read back, draft the three sentences with the numbers, get wording approval, apply
   (report9 live; Paper 1 / SI / MS under REASON), mirrors, gates, records, push. 5. L14: `--ship`.
