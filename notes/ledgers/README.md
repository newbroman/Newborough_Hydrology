# `ledgers/` — living current-state documents

**Read these first.** Everything else in the project store is history.

## The two document kinds, kept apart

| Kind | Examples | Rule |
|------|----------|------|
| **Dated deltas = history** | `CHANGELOG_delta_*`, `CORRECTION_*`, `HANDOVER_*` | append-only, never edited, always dated in the filename |
| **Living ledgers = current state** | everything in this folder | edited **in place**, **never** dated in the filename, single source of truth for its concern |

The delta records *what changed*. The ledger records *what is now true*. Neither
replaces the other, and the whole point is that you should never have to replay
113 dated deltas to answer "what is the state of X?".

## The ledgers

| File | Answers | Status |
|------|---------|--------|
| `SCRIPT_LEDGER.md` | what does each script consume, emit, and which documents describe it? | hand-maintained (one row per script, bumped with the script); gated by `tools/ledger_lint.py` |
| `NUMBER_LEDGER.md` | which report-numbers key is cited where; key collisions across scripts | living; its value columns were retired 2026-08-25 (the values are checked by `cite_check`); `tools/build_number_ledger.py --check` gates key collisions |
| `FIGURE_LEDGER.md` | figure no. → section → caption → source PNG → on-disk resolution | **generated** by `tools/build_figure_ledger.py` (report figures from `tools/figure_map.py`; Source column is each figure's caption `Source:` marker, resolved on disk); `--check` gates |
| `PROVENANCE_LEDGER.md` | every pipeline output → the exhibits (tables, figures) that render it, keyed by OUTPUT FILE | **generated** by `tools/build_provenance_ledger.py`; `--check` gates; `table_provenance_lint` enforces that no table lacks a CSV |
| `VALUE_REGISTER.md` | cited quantities and symbols, keyed by output file | **generated** by `tools/build_value_register.py`; `--check` gates |
| `VALUE_LEDGER.md` (with its HTML rendering and the `VALUE_LEDGER_report` pair) | every cited value, its source, symbol and drift — agrees with `cite_check --index-only` by construction | **generated** by `tools/build_value_ledger.py --write`; `--check` gates |
| `EQUATION_LEDGER.md` | the embedded formula objects: MathML and StarMath, per document | **generated** by `tools/starmath_log.py --write`; `--check` gates (added 2026-09-24 — it was the one generated ledger without one, and was stale from 2026-08-27) |
| `DOC_LEDGER.md` | published PDF → source ODT → built date → live lag state | **generated** by `tools/build_doc_ledger.py` (from `PDF_MANIFEST.txt` + `export_lag.py`); `--check` gates |
| `TABLE_LEDGER.md` | — | **RETIRED 2026-09-19**; superseded by `PROVENANCE_LEDGER.md`. Kept on disk with its banner; `check_all` asserts it stays retired |
| `DECISION_LOG.md` | — | **retired 2026-08-16** — merged into the private `working/DECISION_LOG.md`, the only decision log (D-029); `DECISIONS_PUBLIC.md` at the repo root is generated from it. No file of that name remains here |

Every generated ledger has its `--check` in `tools/check_all.sh` (CLAUDE.md §4d): a
generated file with no check rots silently, which is how `TABLE_LEDGER` died.
This table was itself stale from 2026-09-07 to 2026-09-24 (five ledgers unlisted,
one described as retired that is live, one described as live that is retired).

## The three upkeep rules

These are the whole system. If they are followed, the state is always one lookup
away; if they are not, no amount of folder tidying helps.

> **1. Every code change drops a dated `CHANGELOG_delta` AND updates its
> `SCRIPT_LEDGER` row.**
>
> **2. Every scientific decision drops a `DECISION_LOG` entry** — including, and
> especially, decisions to *retire* something. A retirement carries the removal
> checklist (code · outputs · ledger row · documents · numbers); see D-027.
>
> **3. Every number that enters a document traces to a committed file** — a
> table through `tools/table_configs.py` (gated by `table_source_lint`), a
> headline claim through the claims register, a prose number through
> `cite_check`. No committed source → it does not go in.

### Rule retirements

Rules have the same lifecycle as decisions (D-143): a rule that is superseded is
retired here with a date, not silently dropped or left to drift.

- **2026-09-07 — the former rule 3, "every number has a `NUMBER_LEDGER` row",
  retired.** The ledger was last maintained 2026-08-28 (67 rows) while the
  table-generation program that closed 2026-09-05 wired every corpus table to a
  CSV without one. The rule had been superseded by tooling and nobody said so;
  `NUMBER_LEDGER.md` stays on disk as history. Replaced by the rule 3 above.

## Why the Decision Log exists

The project's recurring failure is not disorganisation — it is **decision
amnesia**. Three worked examples, all from a single 2026-08-14 session:

- The **C4 β₃ triangulation** was retired on 2026-07-24 because its premise was
  tested and refuted. It came back weeks later because the reason for retiring it
  was not written anywhere the reintroducer would look. Rediscovering that cost a
  session. → `DECISION_LOG` **D-001**.
- The **100-month window** was designed as a *minimum* record length so the method
  would transfer to other sites. That intent evaporated and it silently became an
  *upper bound*, understating drainage at long-record wells. Nobody decided that.
  → **D-002**.
- **CEH13/CEH14's** inclusion in the C4 centroid was never an explicit, justified
  decision, so the tension — excluded everywhere else, yet setting the headline
  coefficient — sat unnoticed until it was stumbled on. → **D-005**.

The `Retires` and `Revisit-if` fields are what stop this. An entry saying
"RETIRED — premise refuted by Script 30 v2.1.0; do not reintroduce unless the
β₂–β₃ VIF at C4 exceeds ~2" ends the argument in a lookup instead of a session.

## Source-of-truth hierarchy (unchanged)

1. Files uploaded directly into the current conversation
2. Live committed pipeline CSVs on GitHub `main`
3. **These ledgers**, then the changelogs
4. Handover documents
5. Report text (lowest — the report lags the pipeline)

The primary source is always the committed output. The 2026-08-14 audit was itself
wrong twice by trusting a docstring and a prior document instead of the CSV
(`NUMBER_LEDGER` N-36, N-55).
