# CHANGELOG — 14 May 2026 (Greyscale filename rename follow-up)

## Context

The 13 May alignment edit ("Pipeline / README / run_analysis alignment")
documented an outstanding inconsistency: `utils/paths.py` defined
`DIR_26 = "26_greyscale_figures"` (anticipating a forthcoming rename),
but the actual script file was still `25_greyscale_figures.py`. The
script-name decision has now been taken — the file is renamed to
`26_greyscale_figures.py` and committed to `main`. This entry brings
`run_analysis.py`, `PIPELINE_README.md`, and `readme.md` into line
with the new filename.

The rename is logically correct: prior to the alignment edit, two
scripts (`25_coastal_gradient.py` and `25_greyscale_figures.py`)
shared a `25_` filename prefix and both claimed step 27/27 in their
docstrings. The alignment edit kept both filenames but separated the
orchestrator step numbers (24 for coastal, 28 for greyscale). The
rename to `26_greyscale_figures.py` now also separates the filename
prefixes, eliminating the source of confusion entirely.

Filename prefix and orchestrator step still do not match (the new
filename prefix is 26, the orchestrator step is 28). This is
acceptable and was deliberate at the alignment-edit stage: the
filename prefix groups the script alphabetically with other `2x_`
analytical scripts, while the orchestrator step reflects its position
in the pipeline run order after the supplementary diagnostics.

## Bug fixed

Before this edit, `run_analysis.py` would have failed at step 28
because it called `25_greyscale_figures.py`, which no longer exists
on `main`. Running the full pipeline or the greyscale option would
have produced a `FileNotFoundError`. The fix below resolves this.

## Files changed

### `run_analysis.py`

Nine references to `25_greyscale_figures.py` / "Script 25 grey"
updated to `26_greyscale_figures.py` / "Script 26":

- `PHASE_13` script filename: `"25_greyscale_figures.py"` →
  `"26_greyscale_figures.py"`.
- Module docstring header: "Script 25 grey" → "Script 26".
- `ALL_PHASES` entry label: "Greyscale Figure Conversion (Script 25
  grey)" → "Greyscale Figure Conversion (Script 26)".
- `run_full_pipeline()` phase label: same change.
- MENU items 6a and 6b: "Script 25 grey" → "Script 26".
- `menu_run_single()` BW branch: `run_script` call updated to
  `26_greyscale_figures.py`.
- `run_greyscale()` script_path probe: updated to
  `26_greyscale_figures.py`.
- `run_greyscale()` full-rerun comment: "Script 25 greyscale" →
  "Script 26 greyscale".
- `run_greyscale()` final `run_script` call: updated to
  `26_greyscale_figures.py`.

Step number unchanged at 28/28; phase number unchanged at 13.

### `PIPELINE_README.md`

- Run-order line ending: `25 (grey)` → `26 (grey)`.
- Phase summary paragraph: "Script 25 grey" → "Script 26".
- "Two scripts share the `25_` prefix" disambiguation paragraph
  rewritten to reflect the resolved state: the prefix collision
  no longer exists; Phase 11 is Script 25, Phase 13 is Script 26.

### `readme.md`

- Phase summary paragraph: "`25_greyscale_figures.py`" →
  "`26_greyscale_figures.py`", with the prefix-collision note
  rewritten to describe the resolved state.
- Phase table row 13: "25 (greyscale)" → "26 (greyscale)".

## What was NOT changed

- The `26_greyscale_figures.py` script itself. Its module docstring
  says "Pipeline step: 26 (post-processing)" — this refers to the
  filename prefix, not the orchestrator step number (which is 28).
  Left as-is because both interpretations are defensible: the
  filename prefix is 26 and the script naturally describes itself
  by its prefix.
- `utils/paths.py`. `DIR_26 = "26_greyscale_figures"` was already
  correct before this edit (it anticipated the rename); no changes
  needed.
- Any other script. The pipeline scientific logic is unchanged.

## Validation

- `python3 -c "import ast; ast.parse(open('run_analysis.py').read())"`
  passes.
- `run_analysis.py` loaded as a module: step 28 now resolves to
  `26_greyscale_figures.py`, Phase 13 label is "Greyscale Figure
  Conversion (Script 26)".
- `grep -nE "25_greyscale|Script 25 grey|25 \(grey"` returns nothing
  across all three updated files.

## Reminders

- Upload `run_analysis.py`, `PIPELINE_README.md`, and `readme.md` to
  the project store and push to GitHub `main`.
- Confirm that the deleted `25_greyscale_figures.py` is not still
  resident anywhere in `src/` (a `git status` after pushing should
  show clean).
- The Methods Supplement front matter draft (F.1–F.5) currently
  refers to "25_greyscale_figures.py" in F.4 (the "Two `25_*`
  scripts" subsection) and notes the rename as pending. This will
  need a small edit before the front matter is finalised — the
  pending-rename note can become a one-line "Script 26 is the
  greyscale utility; its filename prefix is 26 but its orchestrator
  step is 28" clarification.
