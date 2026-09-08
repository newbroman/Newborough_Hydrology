# CHANGELOG delta — 2026-09-08c — Script 44 report render placed as report Figure 75 (§5.7.9); Figures 75–77 → 76–78; `odt_edit` 1.6.0

**Provenance.** Cowork session `01PhSvhMMGSWW9UnSFdTK5GU` · configured `claude-fable-5-1` ·
against the tree after 08b (54-step manifest). Spec approved by Martin ("place 44_07 only, spec the
caption-free variant and the renumber" → `NRG_spec_figure_44_07_placement_2026-09-08.md`, "go").
The report is the live document (D-144); no D-entry — an editorial consequence of D-145.

## What changed

- **`src/44_ranwell_hindcast.py` 1.0.0 → 1.1.2.** `plot_hindcast(..., report=False)` gains a
  `report=True` render written to `paths.OUT_44_HINDCAST_REPORT_FIG` =
  `44_07b_hindcast_report.png`: no suptitle, panel titles "Ranwell Site N (slack), paired with well",
  legend without values (once, on the top panel — on the lower panels it covered the August 1951
  minimum, 1.1.2), y-axis "Water-table level (m OD)". `44_07` unchanged. 1.1.1 restored the
  `month` index name after the Parc Mawr / RAF Valley join — pandas 2.1 on the L14 drops it and the
  forcing check raised `KeyError` (the cloud's 2.3 kept it, which is why 1.0.0 passed there and 1.1.0
  failed on the L14). **No number moved:** `44_04` md5 `410302c7…` and `44_05` `7a5ef5c3…` are the
  12:41 run's after all three L14 passes (18:40, 18:51). `paths.py` 1.16.1; `SCRIPT_LEDGER` row 44.
- **`tools/odt_edit.py` 1.5.0 → 1.6.0.** `insert_figure(..., layout="nested" | "plain")`. `"plain"`
  emits report10's form — a `Cap` paragraph holding one image frame (`fr6`, anchor paragraph,
  `rel-width 100%`) then a `Cap` paragraph with `T29` spans and the `<text:sequence
  text:name="Figure">` field. The declared-style guard now checks the frame styles the chosen layout
  emits plus the paragraph and run styles. Report10's own empty trailing `T29` span after the frame
  is NOT emitted: it carries nothing and trips the span-balance guard. Verified on a scratch copy
  before the live write; LibreOffice reopens the result.
- **`report_edits/odt/report10.odt`** §5.7.9: `44_07b` inserted after the second paragraph, before
  "The second test asks whether the level has moved", 15.803 × 13.251 cm, as
  `Pictures/NRG84D78E14A5B1EE6CED6865AB.png`; caption from the spec, plus the house
  `(Source: 44_07b_hindcast_report.png)` marker (`figure_map` resolves it; the spec omitted it and
  `build_figure_ledger` flagged the gap). "What remains is a test of the dynamics alone" gains
  "(Figure 75)" — typed AFTER the renumber so it was not itself moved. Pre-edit copy:
  `_to_delete/report10_pre_fig75_2026-09-08.odt`.
- **Renumber 75→76, 76→77, 77→78** via `tools/renumber_plan_ranwell_fig.csv` (a correction plan of
  its own; `renumber_plan.csv` untouched) with `repoint_refs.py --plan … --kind figure --apply`:
  seven typed references — report10 ×4, report8, report9, report12 — dry-run and apply both 7, none
  left for review; no bare "Figures 7x" continuations existed. Captions renumber by field.
- Mirrors `report8/9/10/12.md` regenerated in the cloud (bridge pandoc 2.9.2 is below the 3.0 pin)
  and committed back; `refresh_mirrors --check` current. `reference_lint --kind figure --snapshot`
  re-pinned (78 rows; the pre-pin FAIL for 75–77 was the expected "meaning changed" signal);
  reference_lint OK, section_ref_audit OK, cite_check --claims-only exit 0, `FIGURE_LEDGER`
  regenerated: 78 report figures, 78 resolve to a source on disk, 0 flagged.

## Not done / owed

- `report.pdf` lags until `export_master_pdf.py` on the L14 (fields refresh there); `check_all`
  and option 2 / 11 owed for 08b + 08c. `figref_lint` reads the exported PDF — run it after the export.
- Spec deviations recorded here rather than in the spec: Source marker, single legend, no empty span.
