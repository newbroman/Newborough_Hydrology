# Spec — placing Script 44's hindcast figure in report10 §5.7.9: caption-free variant, insertion, renumbering (for sign-off)

**Provenance.** Cowork session `01PhSvhMMGSWW9UnSFdTK5GU` · configured `claude-fable-5-1` ·
2026-09-08. Martin: "place 44_07 only, spec the caption-free variant and the renumber". The
report is the live document (D-144); D-145 governs the content. Design → sign-off → build.

## 1. Script 44 1.0.0 → 1.1.0: a report render beside the annotated one

- `44_07_hindcast.png` stays as it is (panel titles carry r / NSE / ranges; suptitle names the
  model) — it is the Methods Supplement's figure (§S.23c) and a working diagnostic.
- New **`44_07b_hindcast_report.png`** (`paths.OUT_44_HINDCAST_REPORT_FIG`): the same three panels
  and data, rendered for the report under the house rule that captions live in the document text:
  no suptitle; panel titles reduced to the site and its slack, e.g. "Ranwell Site 1 (Penlon
  slack), paired with ceh25" — a well name is a label, not a result, and the reader needs it to
  match the text; legend entries "Ranwell 1951–53, monthly mean of readings" and "SSM hindcast,
  offset removed, capped at the ground surface"; the ground-surface dotted line kept; y-axis
  "Water-table level (m OD)"; `MPL_DEFAULTS` house style via `apply_house_style` (already applied);
  the offset value moves out of the legend (it is in `44_04`). Same `render_figure` path and dpi
  as its neighbours in the report (the Script 39 figure is the model).
- One plotting function with a `report: bool` switch, called twice — no duplicated drawing code.
- `SCRIPT_LEDGER` row 44: version 1.1.0, `44_07b` in Emits (figs); `FIGURE_LEDGER` regenerates
  from captions (`build_figure_ledger.py`) once the figure is in the ODT.
- Verification: L14 `run_analysis.py --step 44`, read back that both PNGs exist and that
  `44_04`/`44_05` are byte-identical to the 13:41 run (a render change must not move a number).

## 2. Insertion into report10

- **Position:** in §5.7.9, immediately after the second paragraph ("Two tests follow … in the
  last years before the forest closed.") and before the third ("The second test asks whether the
  level has moved …"), so the figure sits with the dynamics test it illustrates.
- **In-text reference:** the second paragraph's sentence "What remains is a test of the dynamics
  alone: at the nearest paired well the correlation …" gains "(Figure 75)" after "alone" —
  typed, as every reference in the report is, and therefore inside `repoint_refs`' reach for any
  future move.
- **Caption (document text, sequence-numbered by the field; number not typed):**
  > Ranwell's 1951–53 water-table readings against the SSM hindcast, at the three sites whose
  > series he published. Points are the monthly means of his fortnightly readings at Sites 1
  > (Penlon slack), 4 (Clwt Gwlyb) and 8 (the coastal slack); the line is the modern per-well
  > model at the nearest dipwell in the same terrain basin (ceh25, ceh27, nw5), driven by RAF
  > Valley climate from 1930 with the coefficients fitted to 2005–2026, shifted by the mean level
  > difference between pipe and well and capped at the ground surface (dotted), which is where a
  > flooded slack reads. Correlations and bias-removed efficiencies are given in the text;
  > Methods Supplement §S.23c.
- **Markup:** report10 does not use report9's nested text-box form — its figures are a `Cap`
  paragraph holding one `draw:frame` (`fr6`, anchor paragraph, `style:rel-width="100%"`,
  width 15.803 cm) followed by a `Cap` paragraph with `T29` spans and the
  `<text:sequence text:name="Figure" text:formula="ooow:Figure+1">` field. `odt_edit.insert_figure`
  currently emits only the nested form with fr10/fr18, whose style guard would abort on report10.
  **Change:** `odt_edit` 1.5.0 → 1.6.0 adds `layout="nested" | "plain"`; `"plain"` emits the
  report10 form (styles taken from the document: `fr6`, `Cap`, `T29`), keeps the manifest entry,
  the sha-named `Pictures/` entry, the marker check, the declared-style guard and the LibreOffice
  read-back. Image height from the PNG's aspect at 15.803 cm width.
- **Backup** of report10.odt beside it (`_to_delete/` copy) before the write, as for the text edits.

## 3. Renumbering — a three-row permutation, applied once

- The new figure becomes **Figure 75**; the current 75 (spatial reach of interventions, §5.8),
  76 (four-driver schematic) and 77 (P_flood achievability) become **76, 77, 78**. The captions
  renumber themselves (sequence fields). The **typed references** that must move, measured in the
  mirrors: report10 "Figure 75" ×1, "Figure 76" ×2, "Figure 77" ×1; report12 "Figure 77" ×1;
  report8 "Figure 75" ×1; report9 "Figure 75" ×1 — seven occurrences, none elsewhere in the
  corpus (`index.html`, the Supplement and the Papers cite none of these three).
- **Plan file `tools/renumber_plan_ranwell_fig.csv`** (kind,old,new: figure,75,76 / 76,77 /
  77,78) — a correction plan of its own, as `repoint_refs.py` requires; `renumber_plan.csv` is not
  rewritten. Applied with `repoint_refs.py --plan tools/renumber_plan_ranwell_fig.csv --kind
  figure --apply` in one simultaneous pass (the 76→77 / 77→78 chain is exactly the cycle the tool
  exists for). `--dry-run` first; the count must be seven.
- **Bare continuation numbers** ("Figures 76 and 77"): the tool reports them rather than
  rewriting; a `grep` of the mirrors for `Figures 7[5-7]` before the apply settles whether any
  exist (none in the current mirrors).
- **After the apply:** `refresh_mirrors`; `reference_lint --kind figure --snapshot` re-pins the
  meaning snapshot (78 rows; the lint will otherwise report "meaning changed" for 75–77, which is
  the correct signal that the pin needs moving, not a fault); `figref_lint`; `section_ref_audit`;
  `tools/reference_index_figure.csv` regenerates from the captions; `build_figure_ledger.py`;
  `cite_check --claims-only`. The project instructions' "Figure 57 / 50 / 17" note about the λ
  render is unaffected (below 75).
- **PDF:** `report.pdf` lags until `export_master_pdf.py` on the L14 (fields and indexes refresh
  there, which is what renumbers the captions in print).

## 4. Records

- Changelog 2026-09-08c; SCRIPT_LEDGER row 44; FIGURE_LEDGER regenerated; `odt_edit` 1.6.0 inline
  changelog; W140 addendum in the register ("figure placed"); handover note line.
- No D-entry: the figure and the renumbering are editorial consequences of D-145.

## 5. Order and division of labour

1. Sign-off on this spec (position, caption, well names in the panel titles, the `plain` layout
   in `odt_edit`).
2. Bridge: Script 44 1.1.0, paths, `odt_edit` 1.6.0, plan CSV, ledger row — all writable here.
3. L14 (Martin): `python3 run_analysis.py --step 44` to emit `44_07b`; tell me it has run.
4. Bridge: insert the figure, add "(Figure 75)", apply the plan, refresh mirrors, re-pin the
   snapshot, run the reference gates, regenerate FIGURE_LEDGER; write the records.
5. L14: `bash tools/check_all.sh`, `export_master_pdf.py`, option 2 / 11.
