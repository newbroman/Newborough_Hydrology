# NRG — handoff to the next session (Opus), 2026-09-09

**Provenance.** Written by Cowork session `01PhSvhMMGSWW9UnSFdTK5GU` (configured `claude-fable-5-1`)
at the point Martin switched models. Public tree at `bde7a37` plus the uncommitted batch below.
Start as always: read `working/HANDOVER_BOOTSTRAP.md`, run `python3 tools/session_handover.py`,
read `CLAUDE.md` and the top entry of `working/updates/HANDOVER_NOTE.md`.

## 1. Where the tree is — one batch, built and verified, NOT committed

Batch **2026-09-09c** (changelog `working/changelogs/CHANGELOG_delta_2026-09-09c_well_basis_uncertainty_D147.md`,
decision **D-147**, register **W143**): the coastal-gradient uncertainties (δ₀, the 150 m rate, L_cg) are
quoted on the well basis. Everything in it is done except the gate run and the commit:

Public repo, modified (stage these BY NAME — never `git add -A`; `Claude outputs/` is untracked and not
ignored):
```
src/25_coastal_gradient.py                      (1.26.0 -> 1.27.0)
notes/ledgers/SCRIPT_LEDGER.md                  (row 25)
outputs/25_coastal_gradient/25_report_numbers.csv
outputs/pipeline_provenance.json  outputs/pipeline_run_log.json
report_edits/text/report9.md  report_edits/text/report10.md
docs/papers/paper_1/text/Paper1.md  docs/papers/paper_1/text/PAPER1_SI_methods.md
docs/report/text/Newborough_Methods_Supplement.md  docs/report/text/Supplementary_Material.md
tools/claims_register.csv                       (+2 rows)
DECISIONS_PUBLIC.md                             (147)
```
Private store (`./working/wgit`), modified: `working/DECISION_LOG.md` (D-147), `working/DECISION_INDEX.md`,
`working/updates/NRG_WORK_REGISTER.md` (W143), `working/updates/HANDOVER_NOTE.md` (top entry),
`working/doc_tier_log.csv` (REASON stamps), the new changelog, and this file.

ODTs (not in git; the ODT copies travel with `--ship`'s archive): `report_edits/odt/report9.odt`,
`report10.odt` edited in place (live); new versions `docs/papers/paper_1/Paper1_v1_42.odt`,
`PAPER1_SI_methods_v1_18.odt`, `docs/report/Newborough_Methods_Supplement_v1_9_121.odt`,
`Supplementary_Material_v1_29.odt` (prior versions left on disk). Their PDFs are NOT built yet.

Verified already: L14 run of `--step 25` (66.5 s); `25_01` and `25_16` byte-identical to the committed
versions; all nine `*_well_basis_*` keys read back from the CSV; every ODT edit was a counted
`tools/odt_edit.py` substitution; mirrors regenerated in the cloud with pandoc 3.1.3 (the bridge's
2.9.2 is refused) and `refresh_mirrors --check` reports all current, 0 legacy; `doc_version_sync`
(REASON) in step; `cite_check --claims-only` HOLDS on the two new rows; `decision_lint` OK;
`session_handover --check` OK; no em space (U+2003) anywhere written; no "jackknife" in new wording.

## 2. What to do first (in order)

1. `cd ~/projects/NRG && bash tools/check_all.sh 2>&1 | tee scratch/check_all_09c.log | tail -25; echo "exit ${PIPESTATUS[0]}"`
   — run on Martin's L14 (the bridge shell times out at 120–180 s; `check_all` is longer). Expected
   green. If `output_lag` complains about Script 25, the run has already happened — check the
   mtime of `25_report_numbers.csv` against `src/25_coastal_gradient.py` before doing anything.
2. Commit public (bridge git works; sweep residue after every write):
   ```
   cd ~/projects/NRG && git add src/25_coastal_gradient.py notes/ledgers/SCRIPT_LEDGER.md \
     outputs/25_coastal_gradient/25_report_numbers.csv outputs/pipeline_provenance.json outputs/pipeline_run_log.json \
     report_edits/text/report9.md report_edits/text/report10.md \
     docs/papers/paper_1/text/Paper1.md docs/papers/paper_1/text/PAPER1_SI_methods.md \
     docs/report/text/Newborough_Methods_Supplement.md docs/report/text/Supplementary_Material.md \
     tools/claims_register.csv DECISIONS_PUBLIC.md
   git commit -m "Script 25 1.27.0: coastal-gradient uncertainties on the well basis (D-147) in report9/10, Paper 1 v1_42, SI v1_18, MS v1_9_121, SM v1_29; claims rows (09c)"
   ```
   Private: `./working/wgit add working/DECISION_LOG.md working/DECISION_INDEX.md working/updates/NRG_WORK_REGISTER.md working/updates/HANDOVER_NOTE.md working/doc_tier_log.csv working/changelogs/CHANGELOG_delta_2026-09-09c_well_basis_uncertainty_D147.md working/updates/NRG_HANDOFF_to_opus_2026-09-09.md && ./working/wgit commit -m "D-147, W143, changelog 09c, handover"`.
   After any bridge git write: move `.git/HEAD.lock`, `.git/index.lock`, `.git-working/index.lock`
   and stray `.git/objects/**/tmp_obj_*` into `_to_delete/` (rename, not delete) before the next
   git command.
3. Martin runs `cd ~/projects/NRG && NRG_SHIP=1 bash tools/nrg_git.sh --ship "09c well-basis uncertainties"`
   — builds the four lagging PDFs (`build_pdfs.sh`; the PDF must be built by the L14, never by the
   sandbox), runs `check_all`, pushes, archives. Read `scratch/ship_<stamp>.log`; last line must be
   `SHIP: OK <sha>`.
4. AFTER the push: `python3 tools/session_handover.py --write` then `--check` (the records gate wants
   the HANDOFF newer than the push), commit that, and regenerate the project-store copy of the
   handover if it changed.

## 3. Then the open list (priority order, from `NRG_priority_work_2026-09-07.md` and the register)

- **W141** — report9 §4.10.2 still says "The headline fit is the forest-free panel (C4 and C5 dropped)"
  and "12,457 observations across 72 wells": pre-D-046 wording (forest-free = not under canopy, by
  the land-cover flag; 61 wells, ~10,929 rows in the headline panel — read `n_obs` from `25_01`).
  Live document, `odt_edit.py`, then mirror (cloud pandoc), `cite_check`, changelog, W141 closed.
- Martin's own items: T-22 Paper 1 abstract ≤225 words (233 now), T-23 highlights, T-24 well KML,
  T-25 AI declaration; S4 (config split), S9; Welsh W129/W122 parked; empty `_to_delete/`.
- Later: W116 (Script 40 MS chapter), Figure 8 uncited, PLURAL_SEC in `repoint_refs`, W31, R2;
  "jackknife" survives in the MS's Script 43 chapter and glossary (pre-existing) if Martin wants
  it reworded there too.

## 4. Standing constraints that bit this week (do not relearn)

- Design → sign-off → build; delegate mechanical, well-specified work to Sonnet from a written spec;
  judgement (wording, decisions, scientific calls) stays with the main model; Martin approves methods
  sentences and D-entries before they go in.
- ODT edits only through `tools/odt_edit.py` with counted substitutions; frozen docs (Paper 1, SI,
  MS, Supplementary Material, summaries) need `ODT_EDIT_REASON=<changelog id>` and a bumped
  filename; report chapters are live and edited in place. Get the literal string from the
  document's `content.xml` first — spans split numbers (`−3<span>1.3</span>`), apostrophes differ
  (report9 straight, Paper 1/MS curly), and removing a span needs `allow_tag_change=True`.
- Mirrors: regenerate in the cloud (`git clone --depth 1`, stage the ODT, `refresh_mirrors.py --only`),
  write the `.md` back with `device_commit_files`; the section-map step of `refresh_mirrors` errors in
  the cloud for want of `report.odm` — harmless, the mirror is already written.
- Numbers enter documents only from a committed CSV; name the basis (row/well; windowed/full record).
- Exact paste-able commands for Martin, `tee` to `scratch/`, `${PIPESTATUS[0]}` for the exit code.
- Never em space; never the word "jackknife"; never hand-edit `PDF_MANIFEST.txt`; Ranwell scans never
  committed; decision IDs are not cited in Paper 1 or its SI (report and MS may cite them).
- Every handover ends with "Decisions recorded this session: …" — this one: **D-147**.
