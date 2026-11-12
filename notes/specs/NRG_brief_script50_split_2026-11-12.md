# Brief — split Script 50 (`50_record_length.py`) by experiment family

*Queued 2026-11-12 by chat 'Cloud setup J-14' on Martin's word: "queue the script 50 splitting as a seperate
task". Task **T-208**, job **J-15**. Claims: `pipeline` (code), then `doc:MS` (the Supplement chapters). Waits for J-9 (which edits Script 50 in its phase 2a).*

## Why

`src/50_record_length.py` began on 2026-10-01 as one experiment (D-222: what the record length decides) and has
since become the home of every follow-up model experiment: E5/E6 (datum sweeps), E8–E8g (two-store, D-231 to
D-236, D-255), E9 (Ranwell 1951–53, D-229), E10 (forest forcing, D-260), E11 (D-261), E12 (per well or per
cluster, D-268), E13/E13b (D-273), E16 (one elevation base / mean high water, D-286), E17 (D-287), E18 (D-290),
E19. On 2026-11-12 it was **5,937 lines and 167 functions**, and it is **2,916 s of the pipeline's ~5,900 s**
(`outputs/pipeline_provenance.json`). A change to one experiment re-runs all of them, and a reader looking for
one experiment's logic has to find it among eighteen. J-9 phase 2a adds the mean-high-water form to several
experiments, so it grows again.

## Martin's ruling on the shape (2026-11-12)

> *"when script 50 is split I want it treated as the other pipeline steps. I dont like the fact its been used as a
> dumping ground to prevent rewriting step counts and the methods supplement"*

So the split is into **separate pipeline steps**, each a script like every other step — not modules hidden behind
one step. The extra work that the "one step" shape avoided is the point, not a cost to minimise.

## What to do

1. **One step per experiment family.** Propose the grouping to Martin first (e.g. record length itself — the
   original D-222 experiment; the datum sweeps and drainage bases E5/E6/E16/E17; the two-store tests E8–E8g; the
   drier epochs E9/E11; forest forcing and evaporation E10/E13; per-well vs per-cluster and calibration transfer
   E12/E18; E19), with a script number and name for each, and wait for his yes.
2. **Register each as a real step** exactly as other steps are: its `Step(...)` row in `run_analysis.py`
   (phase, opt-in or not — Script 50 is opt-in today; ask whether each family stays opt-in), the documented step
   counts (`_DOCUMENTED_COUNTS` and wherever else counts are checked — `pipeline_lint`, `pipeline_index`), a
   `SCRIPT_LEDGER` row, its own output directory and `paths.py` constants, its own `NN_report_numbers.csv`, and
   **a Methods Supplement chapter heading naming it** (`tools/ms_chapters.py` refuses a step without one).
3. **Report-number keys keep their names** where possible so documents do not drift; a key that must move file
   (from `50_report_numbers.csv` to the new step's) is repointed with the repo's tools (`repoint_index.py`,
   `cite_check`), never by hand, and listed in the changelog.
4. **The Methods Supplement chapters** are document work under the `doc:MS` claim, written through
   `tools/odt_edit.py` and verified in headless LibreOffice (CLAUDE.md §3). Plan that as its own phase of the job,
   after the code split ships.
5. Script 50 keeps the original record-length experiment (D-222) — what its name says — or is retired if every
   family moves out; ask.

## The acceptance test

**Behaviour-preserving, measured, not assumed:** every output file the experiments write today is reproduced
byte-identical by the new steps (in their new directories where they move — compare by content hash, and list
the old path → new path map in the changelog), every report-number value is unchanged, and
`bash tools/check_all.sh` is OK with the new step counts and the new Supplement chapters in place.

## Constraints

- Read `python3 tools/context_for.py src/50_record_length.py` first; D-222, D-225, D-229, D-231–D-236, D-255,
  D-260, D-261, D-268, D-273, D-286, D-287, D-290 all trace to it.
- Keep each function's dated version comments with the function when it moves (they are its history).
- `free_run(..., base=DRAINAGE_DATUM)` binds its default at definition time — pass `base=` explicitly
  everywhere (the trap recorded in the J-9 brief, Addendum 3).
- Ask before every push.
