# CHANGELOG — 13 May 2026 (Pipeline/README/run_analysis alignment)

## Context

`run_analysis.py`, `PIPELINE_README.md`, and `readme.md` had drifted
out of agreement on step and phase counts, and `25_coastal_gradient.py`
(a main analytical script for the C5 coastal-retreat hypothesis) was
present in `src/` but unwired from the orchestrator. The two `25_*`
scripts (`25_coastal_gradient.py` and `25_greyscale_figures.py`) both
claimed step 27/27 in their docstrings, but only the greyscale script
was registered.

This entry brings all three files into agreement on a single canonical
structure: **28 steps across 13 phases**, with coastal-retreat as the
final main analytical phase (Phase 11) ahead of supplementary diagnostics
(Phase 12) and the greyscale utility step (Phase 13). Within the Script 10
clearfell BACI suite, `10c_forest_zone_analysis.py` is now labelled
supplementary.

## Decisions taken (per Martin)

1. Script 25 (`25_coastal_gradient.py`) is a main analytical script,
   not supplementary. It is wired into the orchestrator as Phase 11
   (step 24), sitting between forestry scenarios (Phase 10) and
   supplementary diagnostics (now Phase 12).
2. Script 25 greyscale (`25_greyscale_figures.py`) remains a callable
   step in `run_analysis.py` but is treated as a post-pipeline utility
   rather than an analytical phase. It is not documented in
   `PIPELINE_README.md` like the other pipeline scripts.
3. Within the Script 10 clearfell suite, 10c (forest zone spatial
   analysis) is supplementary; the other seven sub-scripts (10a, 10b,
   10d–10h) contribute to the primary report results. The execution
   order is unchanged; only the labelling has changed.
4. Step labels in `run_analysis.py` are the canonical step numbers.
   Inline `(step N)` annotations in `PIPELINE_README.md` further down
   that document use a different (per-sub-script flattened) numbering
   that does not match the orchestrator; a clarifying note has been
   added near the top of the document. The 124 inline annotations were
   not rewritten — that is a larger separate task.

## Files changed

### `run_analysis.py`

- Step labels bumped from `X/27` to `X/28`.
- New `PHASE_11 = [("25_coastal_gradient.py", "24/28  ...")]` added
  between forestry scenarios and supplementary diagnostics.
- Old `PHASE_11` (scripts 22, 23, 24) renumbered to `PHASE_12` with
  step labels 25–27.
- Old `PHASE_12` (greyscale) renumbered to `PHASE_13` with step label
  28/28.
- `ALL_PHASES` extended: 13 phases total.
- `run_full_pipeline()` updated to call all three new phases with
  correct labels.
- `run_supplementary()` updated to reference `PHASE_12` (was
  `PHASE_11`).
- Docstring header rewritten: "all 28 steps", with a one-paragraph
  note explaining the 11+1+1 phase structure (main / supplementary /
  utility).
- MENU and CLI help text updated to "28 steps".
- All `27/27` greyscale step labels updated to `28/28`.
- Smoke-tested: AST parse passes, `_STEP_MAP` covers steps 1–28 with
  no gaps or duplicates, 13 phases registered with the expected
  script counts per phase.

### `src/run_10_clearfell.py`

- Docstring header rewritten to distinguish primary sub-scripts (10a,
  10b, 10d–10h) from the supplementary sub-script (10c). Execution
  order unchanged.
- `SUBSCRIPTS` table description strings updated: 10a labelled
  "(primary)", 10c labelled "(supplementary)".

### `PIPELINE_README.md`

- Run-order line extended to include `25 (coastal)` and `25 (grey)`.
- Canonical count statement: "**28 pipeline steps across 13 phases.**"
- New paragraph describing the 11/12/13 phase split (main /
  supplementary / utility) and the two `25_*` scripts.
- 10c flagged supplementary in the suite description.
- New section: **Phase 11 — Coastal-Retreat Gradient Analysis**, with
  full I/O contract for `25_coastal_gradient.py` (reads, writes, and
  the OS-Open-Map-Local distance-to-coast input).
- Old "Phase 11 — Supplementary Diagnostics" section relabelled as
  Phase 12.
- Greyscale (Phase 13) intentionally not given a section: per
  decision (2), the utility step is documented only by its presence in
  `run_analysis.py`, not in this README.
- Clarifying note added near the top warning that the inline
  `(step N)` annotations against individual outputs derive from an
  automated I/O audit using per-sub-script flattening and do not
  match the orchestrator's step numbers.

### `readme.md`

- All five "29 steps" references corrected to "28 steps". (The readme
  had a more granular flattened numbering than `run_analysis.py`; the
  alignment uses the orchestrator's canonical 28-step / 13-phase
  structure.)
- "Eleven sequential phases" → "Thirteen sequential phases".
- Validation-checkpoint list updated: now Phases 1, 3, 9, 10 (was 1,
  3, 10 — Phase 9 has a checkpoint in the code).
- Phase table rewritten against orchestrator's 1–28 numbering. Each
  row now maps cleanly to one or more `run_analysis.py` step numbers.
- New row added for Phase 11 (coastal-gradient) and Phase 13
  (greyscale utility).
- New paragraph explaining the main / supplementary / utility split,
  the two `25_*` scripts, and the 10c supplementary status.
- New ordering constraint listed: Script 25 (coastal) requires
  outputs from Script 14 (summer-trend stats) and Script 10a (ANCOVA
  coefficients) — already enforced by phase ordering, but documented
  for clarity.

## What was deliberately not done

- The 124 inline `(step N)` annotations in `PIPELINE_README.md` were
  left in place. Reconciling them with the orchestrator's step
  numbering is a separate task and would require regenerating the
  README from a fresh I/O audit. The clarifying note added near the
  top tells readers how to interpret them.
- No changes to any analysis script other than `run_10_clearfell.py`
  (docstring + table description strings only). The scientific
  pipeline is unchanged.
- No update to `index.html` or other GitHub Pages content. If those
  also reference step/phase counts, they need a separate alignment
  pass.

## Validation

- `python3 -c "import ast; ast.parse(open('run_analysis.py').read())"`
  passes.
- `run_analysis.py` loaded as a module: `_STEP_MAP` keys = {1..28}
  exactly, no gaps. `ALL_PHASES` has 13 entries.
- `python run_analysis.py --help` runs without error and reports "all
  28 steps".
- `run_10_clearfell.py` AST parse passes.
- Phase / step count grep across all three documents agrees on 28/13.

## Reminders

- Upload the new `run_analysis.py`, `src/run_10_clearfell.py`,
  `PIPELINE_README.md`, and `readme.md` to the project store and
  push to GitHub.
- Push the canonical step list (this CHANGELOG entry) so the next
  session has the up-to-date orchestrator structure on hand.
