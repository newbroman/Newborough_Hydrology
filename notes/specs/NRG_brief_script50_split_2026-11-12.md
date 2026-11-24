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

## Addendum, 2026-11-24 — the pre-split review, and Martin's three decisions

Reviewed by chat 'Paper M J-24-26' before starting, at Martin's request ("review the changes needed now so j15 can
proceed after your push"). Read-only; nothing was changed for J-15 itself.

**Martin's decisions (2026-11-24), answering step 1 and step 5 of this brief:**
1. **Five families**, one step each.
2. **Numbered as a suite, 50a–50e**, the way 09a–09g and 10a–10n are.
3. **All five stay opt-in** (tier X, exec optin), as Script 50 is today.

| step | family | Script 50 phases / experiments today | report-key prefixes (keep the names) |
|---|---|---|---|
| **50a** | record length (D-222; what the name says) | phases 1–5: per-well forecast, within-record hindcast and stability at each length; the CCW hindcast by length; stable lengths; identity checks against 39 and 48 | `reclen_*`, `window_*`, the stable-length and identity keys |
| **50b** | datum and drainage bases | phase 6 (E5/E6: CCW, split and projection by datum; Ranwell by datum, E9; split series), 17b E16, 17c E17 | `datum_*`, `projection_*`, `ranwell_*` (by-datum), `e16_*`, `e17_*` |
| **50c** | transfer between wells | phase 6's T-173 neighbour transfer (A, MHW, B) and transfer rule; phase 15 E12; 15b E12b placement; 17d E18; **and `plot_decision_tree()`** (Paper M Figure 7, J-25) | `transfer_*`, `basis_*`, `placement_*`, `e_qm_*` |
| **50d** | two stores and non-climatic change | phases 7–12: E8, E8b/E8c, E8d, E8e, E8f, E8g | `two_store*`, change/surface, `e8*`, `precanopy*` |
| **50e** | drier epochs and forcing | phase 13 E10, phase 14 E11, phases 16–17 E13/E13b, 17e E19 | `forest_forcing*`, `ranwell_need*`, `ranwell_epoch*`, `e13*`, `e13b*`, `e19*` |

**What the review found, which the split must handle:**
- **Size and cost, measured.** 6,268 lines, 172 functions. The last run log gives Script 50 59.4 min of about
  118 script-minutes (Script 47 is 24.8 min, Script 03 12.1). The run log has no per-phase timings, so time each
  family on the first run and record it in the changelog.
- **Cross-links.**
  - Three stay inside their family: E12b reads E12's table (both 50c), E17 reads E16's (both 50b), and E13b reads
    E13's monthly series (both 50e).
  - **One crosses:** E10 (`forest_forcing`, 50e) takes `df`, the record-length per-well results. In 50e it must
    read 50a's saved per-well CSV instead, so 50a must run first. Confirm byte-identity holds through the CSV round
    trip (float formatting). If it does not, write the frame with full precision rather than changing E10's
    arithmetic.
- **`plot_decision_tree()` (Script 50 1.30.0)** reads `reclen_*` (50a), `ranwell_nse_median_model_b` and the
  `basis_*`/`placement_*` keys (50c), plus Script 48. In 50c it must read 50a's and 50b's report-number files by
  their new paths (Ranwell-by-datum lives in 50b).
- **No randomness:** no RNG anywhere in the script, and the "seed" is the equilibrium state. Byte-identical outputs
  are achievable.
- **Documents.** 196 fields in `tools/number_fields.csv` and about 897 rows of `tools/citation_index.csv` point at
  `outputs/50_record_length/50_report_numbers.csv`. With the key names kept, only the source path moves. Repoint it
  by key-prefix map with the repo's tools (`repoint_index.py`; `number_fields.csv`'s source column), never by hand,
  and list the map in the changelog.
  - Also cited directly: `50_36_pet_comparison.csv` (80 rows; E13b → 50e) and `50_24_clearance_step_by_well.csv`
    (2 rows; E8f → 50d).
  - `tools/table_configs.py`, `tools/cite_check.py` and `tools/field_md_build.py` name Script 50 paths. Update them.
- **Code outside Script 50.** `src/54_dry_year_hysteresis.py` reads `OUT_50_E13_PET` (50_32, E13 → 50e). Keep the
  constant name in `paths.py` and point it at 50e's file. Grep `OUT_50_` and `DIR_50` again before starting.
- **The Methods Supplement gate, which decides the order.** `run_analysis.py` refuses to register a step without a
  chapter heading (`tools/ms_chapters.py`), so the Supplement must change BEFORE the new steps can run. The parser
  reads `Script NN suite (a--e)` (`_SUITE`), so one heading change does it: **S.23f "Script 50 --- What the record
  length decides" → "Script 50 suite (a--e) --- …"**.
  - That is one prose write to a frozen document (D-144). Set `ODT_EDIT_REASON` to T-208/J-15, take `doc:MS`, read
    it back in headless LibreOffice and refresh the mirror.
  - The fuller per-step chapter text stays the later document phase, as step 4 says.
- **Registration.**
  - Five `Step(...)` rows replace Script 50's (opt-in, tier X).
  - `_DOCUMENTED_COUNTS`: total_registered +4, optin_diagnostic +4, by_exec.optin +4. Read the current values, and
    check how phase numbering treats a suite.
  - `pipeline_lint` and `pipeline_index` counts, five `SCRIPT_LEDGER` rows, five output folders, five
    `NN_report_numbers.csv`.
- **Old outputs.** After the split, `outputs/50_record_length/` must not keep orphaned files that read as current.
  Move them to their new folders by the old→new map (content hashes listed) and remove the rest in the same commit.
- **Acceptance (unchanged):**
  - byte-identical outputs by content hash, old path → new path;
  - every report-number value unchanged;
  - a full `--full --with-supplementary` run, then `check_all: OK`.
- **What it buys.** A change to one experiment becomes `run_analysis.py --step 50x` (minutes) instead of the whole
  hour. `--step` runs inside the pipeline's run token, so the `runid` and `output_lag` gates accept it.
