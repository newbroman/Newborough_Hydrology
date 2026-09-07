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
| `SCRIPT_LEDGER.md` | what does each script consume, emit, and which documents describe it? | populated 2026-08-14 |
| `DECISION_LOG.md` | **retired 2026-08-16** — merged into the repo-root `DECISION_LOG.md`, which is now the only decision log (D-029). The file here is a stub. |
| `NUMBER_LEDGER.md` | where does this cited number come from, and has it drifted? | **RETIRED 2026-09-07** (D-143) — kept as history, no new rows; superseded by `table_source_lint` (tables), the claims register (`check_all` claims) and `cite_check` (prose numbers) |
| `FIGURE_LEDGER.md` | figure no. → section → caption → source PNG → on-disk resolution | **generated** by `tools/build_figure_ledger.py` v2.2 (report figures live from `tools/figure_map.py`; Source column is each figure's caption `Source:` marker, resolved on disk) |
| `TABLE_LEDGER.md` | table no. → source → document + resolution; global caption index | **generated** by `tools/build_table_ledger.py` (from `figure_table_manifest.csv` + `reference_index_table.csv`) |
| `DOC_LEDGER.md` | published PDF → source ODT → built date → live lag state | **generated** by `tools/build_doc_ledger.py` (from `PDF_MANIFEST.txt` + `export_lag.py`) |

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
