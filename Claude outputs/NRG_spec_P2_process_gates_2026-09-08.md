# Spec — P2 process gaps from the cross-reference audit: three tooling changes (for sign-off)

**Provenance.** Cowork session `01PhSvhMMGSWW9UnSFdTK5GU` · configured `claude-fable-5-1` ·
2026-09-08, evening. Martin: "can we work on P2 process". Read against the tree after 08e. Tooling
only — no document text moves; every change is a gate or a scope widening. Design → sign-off → build.

## What the survey found (measured tonight, not recalled)

1. **`section_map.csv` was stale again.** Dated 2026-09-07 15:20; §5.7.9 (added this morning) was
   not in it until I regenerated it just now. `section_map.py`'s own docstring says the map is
   "emitted alongside the mirrors so map and mirror cannot diverge" — but `refresh_mirrors.py`
   never calls it, and `check_all` never regenerates or compares it. `section_ref_audit` and
   `section_map --check-refs` both scored against a map with a missing section and reported OK.
   (Regenerated map is in the current batch: +1 row.)
2. **Three documents carry typed cross-references that no renumber tool reaches.**
   `repoint_refs.ODTS` covers report8–12, the Supplement, the SM and the academic summary.
   Outside it: **report6** (12 typed "Section", 1 "Table" — including today's 5.7.8/5.7.9),
   **report7** (6 "Figure", 3 "Section") and **report.odm**, the master (1 "Figure", 1 "Section"
   in the Abstract — the "Figure 65" that went stale on 09-07). `reference_lint` scans typed
   references only in the sub-documents `master_order()` lists, so the master's own text is
   outside its census too.
3. **Of the two audit checks proposed for promotion, one already gates and one nearly does.**
   `section_ref_audit` returns 1 on any DISAGREES row and is already in `check_all` — the
   section↔figure co-citation check is done, and nothing needs building. The caption `Source:`
   check exists in `build_figure_ledger` (it flags captions with no resolvable marker — it caught
   Figure 75 this afternoon) but `check_all` does not run it, so a flagged caption is visible only
   to whoever regenerates the ledger by hand.

## Proposed changes

### A. `section_map.py` 1.1.0 → 1.2.0: a `--check` mode, wired in two places
- `--check`: build the map in memory, compare to `tools/section_map.csv`, print the rows that
  differ (added / removed / renamed), exit 1 on any difference. Same shape as
  `refresh_mirrors --check` and `build_public_decisions --check`.
- `refresh_mirrors.py` 1.1.0 → 1.2.0: after writing any report chapter mirror, call
  `section_map.build()` and write the CSV — the docstring's promise made true. (Pandoc-version
  refusal unaffected: the map is read from the ODT XML, not from pandoc.)
- `check_all.sh`: `python3 tools/section_map.py --check || rc=1` immediately before
  `section_ref_audit`, so the audit is known to score against a current map. The existing
  `--check-refs` call stays.

### B. Widen the renumber and census scope to report6, report7 and the master
- `repoint_refs.py` 1.2.0 → 1.3.0: add `"report6"`, `"report7"` and `"report"` (→
  `report_edits/odt/report.odm`) to `ODTS`. The write path is `odt_edit.edit`, which already
  handles the `.odm` package (same zip layout; `doc_tier.csv` row "report" covers the master).
  The SEC matcher currently anchors on `4\.\d+` (Results-chapter numbers only) — leave that as is
  for this change; widening section renumbering is a separate decision because §5.x/§3.x moves
  have never been planned through the tool.
- `reference_lint.py` 1.1.0 → 1.2.0: the typed-reference census adds the master's own mirror
  (`report.md`) after the sub-documents; captions are unaffected (the master has none). The
  snapshot row count does not change; the reference count rises by the master's few.
- `figref_lint` reads the exported PDF and already sees the master's text; no change.

### C. Gate the `Source:` marker; record the co-citation gate as already in place
- `build_figure_ledger.py` 2.2.0 → 2.3.0: `--check` — regenerate to memory, exit 1 if any caption
  is flagged (no resolvable `Source:`) **or** if the regenerated ledger differs from the committed
  `notes/ledgers/FIGURE_LEDGER.md` (so the ledger cannot go stale either).
- `check_all.sh`: `python3 tools/build_figure_ledger.py --check || rc=1` in the references
  block, after `reference_lint --kind figure`.
- No change for co-citation: note in the priority doc that `section_ref_audit` already gates.

### D. Housekeeping riding along
- `.claude/` added to `.gitignore` (stops the untracked-directory noise in `git status` and the
  stop hook).
- `working/_xref/` — Martin to delete when he closes the audit; not touched here.

## Cost, order, verification
- All four files are tools on the public repo; edits are bridge-writable. Each gets a version bump
  and an inline changelog line; `check_all` is re-run here (its environment gate will fail on the
  bridge as always — every other line is readable) and on the L14 by Martin.
- Verification: (A) rename a heading in a scratch copy → `--check` must fail; (B) `repoint_refs
  --dry-run` on the current plan must report report6/report7/report as scanned with 0 moves;
  (C) `build_figure_ledger --check` must pass now (78/78) and must fail when a `Source:` marker is
  removed in a scratch ODT.
- Records: changelog 2026-09-08f; the priority doc's "P2 — process" section closed; handover line.
  No D-entry — these are gates on rules already decided (D-062 family).

## Not proposed
- Widening `SEC` beyond §4.x, and making `report.odm` part of the mirror snapshot — both are
  bigger than a P2 fix and need their own spec.
