# The documentation layer, audited — 2026-09-24

**Session:** Fable (Cowork bridge / cloud clone), session_01EpgeUDxt66S79EacJHmXo5.
Martin: "given that you have just found stale elements in a core doc, should I ask
you to do a full audit? or sub agent it out?" — "go".

## Why this layer, and not the corpus

Two faults were found earlier the same day that no gate could see: `requirements.txt`
claimed to be the venv's freeze while 42 of 94 installed packages were unpinned and its
header had been sorted into alphabetical order; `MACHINE_SETUP.md` said it pinned
"nineteen packages". Neither is in the gated corpus. The ODTs, mirrors, citations,
figure numbers, counts and retired phrases are covered by the sections `check_all`
prints; the faults were in the layer *around* the corpus — root and setup documents,
configuration files, READMEs — prose that describes the tree and that nothing read back
against the tree. `docref_lint` and `csv_mention_lint` had closed that gap for documents
and CSVs; nothing had closed it for scripts, tools, paths and counts.

## Method

Three Sonnet subagents in parallel, read-only, one bundle of documents each, with a
fixed brief: every file, tool, function, command, flag, count, version and
"X is a gate" claim, checked against the tree, reported as a table of
*claim / what the tree says (the command run) / verdict*, non-OK rows only. Every
finding below was re-verified in the tree by the main session before anything changed.
Bundles: (A) `CLAUDE.md`, `MACHINE_SETUP.md`; (B) `readme.md`, `PIPELINE_README.md`,
`index.html`; (C) `working/HANDOVER_BOOTSTRAP.md`, `working/README_WORKING.md`,
`working/WORK_REGISTER.md`, `notes/ledgers/README.md`, `literature/README.md`, and an
untracked Cowork handover of 2026-08-12 found sitting in `tools/`. Roughly 800 claims checked; 30
stale or wrong.

## Findings and what was done

| Document | Finding | Fix |
|---|---|---|
| CLAUDE.md §1, §2 | `bash nrg_git.sh` and `./wgit` at the root; both moved to `working/` on 2026-08-27 | paths corrected |
| CLAUDE.md §4 | "`console_utils` is the place for a shared `progress()` helper; until it exists, print by hand" — `progress()` (1.1.0) and `track()` (1.2.0) exist | sentence rewritten to use them |
| CLAUDE.md §4 | "`device_bash` calls die at 45 seconds" — superseded by §4c (~120 s) in the same file; the tool's own limit is 120 s default / 180 s max | corrected, with the date the limit moved |
| CLAUDE.md §4 | "A 118 MB ODT" — report9.odt is 129,572,320 bytes; MACHINE_SETUP said 123 MB | "100-MB-plus"; the number is not carried |
| CLAUDE.md §4 | `--ship` "(1.16.0)" — nrg_git.sh is 1.19.0 | version dropped |
| CLAUDE.md D-155 | Script 41's 2026-09-11 break attributed to the pyogrio/fiona engine split without the mechanism | the mechanism added: fiona 1.10.1 no longer lists the KML driver; pyogrio accepts `driver="KML"` |
| CLAUDE.md D-155 | "No script silences its warnings" — `utils/mask_streams_to_land.py` carries a blanket `filterwarnings("ignore")`; Scripts 25, 31, 31b silence whole categories | sentence states the fact; **T-81** opened (Martin's design call: which warnings, why) |
| MACHINE_SETUP tree | `venv/ … present, and not actually used — see §1` while §1 says venv IS the environment | corrected |
| MACHINE_SETUP §libraries | the probed-library list omitted odfpy | added |
| MACHINE_SETUP ffmpeg | a separate `pip install imageio-ffmpeg` step — it has been pinned since 2026-09-17 | points at `pip install -r requirements.txt` |
| readme.md Quick Start | **the whole section was the retracted pre-2026-08-29 story**: "Not a venv, and not `pip install -r requirements.txt`… the reference environment is Ubuntu 24.04's apt packages" — the apt packages cannot run Script 03 | rewritten to the venv; says what it used to say and why that was wrong |
| readme.md | "Python 3.10 or later"; index.html ×2 the same | 3.12.x, a floor and a ceiling |
| readme.md | 57 / 52 / 18 / 43 typed in six places (the counts stamped elsewhere by `sync_index_counts`) | every count wrapped in a `<!--PL:key-->` marker; **readme.md joins `sync_index_counts` DEFAULT_TARGETS (1.3.0)** |
| readme.md | `03_cluster_averages_maod.csv` (×2) — the file is `03_regional_averages_maod.csv`; `30_c4_constrained_fit.py` — retired (D-001), the script is `30_c4_drainage_identifiability.py` | corrected |
| readme.md | Phase table: rows 16 and 17 wrong on steps and scripts (39, 40, 41, 43, 44 unlisted), no Phase 19; the Methods Supplement absent from the documents table | rows rewritten from the manifest; Phase 19 row; MS row |
| PIPELINE_README | run order stopped at 27; "canonical step numbers (1–52)"; sub-script set "10a–10m", "the other eleven" — it is 10a–10n, twelve; no entry for Scripts 40, 41, 43, 44 (48 has one from the morning) | run order completed; step total markered; 10n; entries for 40 and 41 written, Phase 17 heading names 43/44 |
| PIPELINE_README | `20_drawdown_propagation.png` (×2) — the file is `_nohead`; Figures 26–28 sourced to `10a_03_baci_timeseries_*.png` — a CSV stem; `MSL_SPRING_MONTHS = (3, 4, 5)` — config says (2, 3, 4) | corrected |
| PIPELINE_README | two hand-typed quick-reference tables: figures 1–46 on a numbering the report left behind (its "Figure 45" is not the report's), 46 of 83 figures, three rows at files that do not exist | **both replaced by pointers to the generated, gated FIGURE and PROVENANCE ledgers** |
| index.html | "10 documents" (13 linked); "47 figures and 16 tables" (83 / 24 in the ledgers); `--full` "all 58 steps" (it runs the 53 default); `.venv` | counts corrected or removed; `--full` line markered as default-of-total; `venv` |
| notes/ledgers/README.md | five of nine ledgers unlisted (PROVENANCE, VALUE_REGISTER, VALUE_LEDGER, EQUATION); NUMBER_LEDGER described as retired (it is live and gated); TABLE_LEDGER described as live (retired 2026-09-19); a `DECISION_LOG.md` "stub" that does not exist; build_figure_ledger "v2.2" (2.3.0) | table rewritten from the directory and `check_all` |
| literature/README.md | titled `store/` (renamed `literature/` 2026-08-27); "the `store/` block in `.gitignore`"; "documents supplied to the 2026-08-22 session" over rows dated 09-21 and 09-24; a dangling "Wanted entry below" | corrected |
| working/HANDOVER_BOOTSTRAP.md | Tier 0 "capped at 250 lines" — `TIER0_PROSE_BUDGET = 600` since D-150; "90 files / 94 files" — 824 and 338 | corrected; the counts are given as an order and dated |
| working/README_WORKING.md | DECISION_LOG "75 entries" — 191 | order-of-magnitude, dated |
| working/WORK_REGISTER.md | file counts (88 / 93); `notes/ledgers/` "SCRIPT, NUMBER and EQUATION ledgers" | counts dropped; ledger list corrected |
| two untracked files in `tools/` (a Cowork handover and a figure-refresh plan, both 2026-08-12) | free-form handovers, the format D-143 retired, naming a CSV retired on 2026-08-19 as live and every document family at a version four to forty bumps old | moved to `working/updates/Handover_NRG_rebuild_Cowork_2026-08-12_superseded.md` and `working/updates/NRG_figure_refresh_plan_2026-08-12_superseded.md` with a banner; the originals in `_to_delete/tools_strays/` |
| report10.odt | Figure 80's sequence field cached as "Figure 0" (the §4d trap: a new caption until LibreOffice recalculates) | fields refreshed headless by UNO; `figure_map`, `FIGURE_LEDGER`, mirror regenerated. The re-save renamed the package's picture members and wrote frame sizes in inches — the mirror's image lines change, the prose does not (verified character by character) |

Not changed, and why: dated historical measurements (48 s, 45-minute download, "54 numbers by one ULP", "150 of 211") are testimony about a date and were left; report9.odt's fields were refreshed and found unchanged, so the 129 MB file was not rewritten; the two `working/` file counts the two bootstrap documents disagreed on were replaced by measured orders rather than new exact numbers that would rot the same way.

## The gate

`tools/mention_lint.py` 1.0.0 — every script, tool, module and `dir/file.ext` path a
root document names must exist (bare script names resolve against `src/`, `src/utils/`,
`tools/`, `working/` and the root; paths from the root, then `src/`, `outputs/` and the
document's own directory). Exemptions carry a reason in `tools/mention_lint_exempt.csv`
(one row: the retired `30_c4_constrained_fit.py`, named as history). A line marked
`<!-- former path -->` or `<!-- former name -->` is history and skipped. Runs in
`check_all` 1.18.0 after `csv_mention_lint`; 170 mentions on the L14, 148 in a clone
without `working/`. Rule **R65** in the rule → gate matrix; readme.md's counts are
stamped by `sync_index_counts` 1.3.0.

What it does not do: it cannot tell a stale *description* from a current one ("X is
a gate", "N packages", a version number). Counts belong in markers; the rest remains
prose, and prose is re-broken by every fresh session. The audit above is the second
pass of its kind (the first was `NRG_critique_audit_sweep_2026-09-20.md`, over the
corpus); the same sweep over the ungated layer is worth repeating when a rename or a
tool move lands, not on a calendar.

## The ledgers, audited (Martin: "which are retired, which aren't")

Read from each file's own banner, its last commit and the `check_all` line that checks it.

| Ledger | State | Built by | Gate in check_all |
|---|---|---|---|
| `SCRIPT_LEDGER.md` | live, hand-maintained (one row per script, bumped with it) | — | `ledger_lint` (every script listed, versions agree, no orphans) |
| `NUMBER_LEDGER.md` | live; value columns retired 2026-08-25 (values are `cite_check`'s), keys and collisions remain | `build_number_ledger.py` | `--check` (key collisions) |
| `FIGURE_LEDGER.md` | live, generated | `build_figure_ledger.py` | `--check` |
| `PROVENANCE_LEDGER.md` | live, generated (outputs → exhibits, keyed by output file) | `build_provenance_ledger.py` | `--check`; `table_provenance_lint` |
| `VALUE_REGISTER.md` | live, generated | `build_value_register.py` | `--check` |
| `VALUE_LEDGER.md` (+ HTML, `_report` pair) | live, generated | `build_value_ledger.py --write` | `--check` |
| `EQUATION_LEDGER.md` | live, generated — **was stale from 2026-08-27** (16 lines): the one generated ledger with no `--check` | `starmath_log.py --write` | `--check` **added today** (starmath_log 1.2.0, check_all 1.19.0) |
| `DOC_LEDGER.md` | live, generated | `build_doc_ledger.py` | `--check` |
| `TABLE_LEDGER.md` | **retired 2026-09-19**, superseded by PROVENANCE_LEDGER; kept with its banner | — | `build_table_ledger.py --check` asserts it stays retired |
| `DECISION_LOG.md` (in ledgers/) | **retired 2026-08-16**, merged into the private `working/DECISION_LOG.md`; no file remains here | `build_public_decisions.py` generates `DECISIONS_PUBLIC.md` | `--check` (public = generated from private) |

`notes/ledgers/README.md` now says the same.

## The description classes, gated (Martin: "then it needs to be included as a gate")

The note above first said the sweep "is worth repeating when a rename lands". That is a
wish, not a gate, so the three mechanical classes now are:

- **Counts.** `sync_index_counts` 1.4.0 derives keys from the tree beside the manifest's —
  `pins`, `ledgers`, `doc_links`, `report_figures`, `report_tables`, `decisions`,
  `wells_reference` / `wells_extended` / `wells_total`, `wells_dist_coast` — so any of them
  can sit in a `<!--PL:key-->` marker (CLAUDE.md, readme.md, PIPELINE_README.md and
  index.html now carry them), and `--check` FAILS on a number-plus-noun claim of ten or
  more ("nineteen packages", "47 figures", "63 wells") outside a marker on an undated
  line. A dated count is testimony; an undated one is a claim, and a claim is a marker or
  an exemption with a reason (`tools/count_claims_exempt.csv`). `--check` runs in
  `check_all` 1.19.0 — until today the stamp ran only when somebody remembered.
- **Versions.** `mention_lint` 1.1.0: a version quoted for a tool or script on an undated
  line must equal the file's `__version__` assignment (or a shell script's `# VERSION`).
- **Gate claims.** A sentence saying a lint-like tool gates must name one `check_all.sh`
  runs.

What remains prose: what a tool *does*. That class has no mechanical check and is the
one the sweep is for; the trigger for the sweep is now the gate that fires (a rename
trips `mention_lint`), not a calendar.

## Gates run (bridge)

`mention_lint` OK (170); `sync_index_counts` current in three files;
`pipeline_count_lint` OK; `csv_mention_lint` OK; `cite_check --index-only` 1937
exact, 0 drifted; `reference_lint --kind figure` OK; `figure_ledger --check` OK;
`rule_gate_lint` 65 rules, 0 findings; `task_lint` 63 / 16 / 0 after T-81 (open).
`check_all` in full exceeds the bridge's time limit; the L14 verdict is Martin's `--ship`.
