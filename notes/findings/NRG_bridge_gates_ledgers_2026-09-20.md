# The bridge, pushing, the gates and the ledgers — what 2026-09-19/20 taught

Written after two days of document surgery (recession partition, the 1.4a–d
promotion, Table 1.4) in which most of the lost time went to the environment
rather than the work. Each item below cost something.

---

## 1. The Cowork bridge

### What it can do that the notes implied it could not

- **LibreOffice and UNO both work.** `soffice` is on PATH and `import uno`
  succeeds. `tools/export_master_pdf.py` ran there successfully twice, lint and
  all, and `build_pdfs.sh` rebuilt two per-document PDFs. Rendering a chapter to
  PDF is the fastest way to check a layout change — it is how the header-wrap
  fix and the keep-with-next work were verified rather than assumed.
- **git over HTTPS works.** `nrg_autopush.sh`'s header says the bridge is
  network-blocked; for git it is not — `git push` to GitHub succeeded. Keep
  using autopush on the publishing machine for anything with deletions, because
  its mass-deletion guard is the reason it exists, but a plain push from the
  bridge is not blocked.

### What it cannot do

- **Each `device_bash` call is a fresh shell, and nothing survives it.**
  `nohup`, `setsid`, `&` — all die with the call. There is no way to start a
  long job and poll it. A task longer than the call ceiling must run on the
  publishing machine.
- **The call ceiling is ~120 s in practice** (the tool advertises up to 180 s;
  120 s is what was repeatedly enforced). The master export finishes inside it
  when the machine is clean, and does not when it is not.
- **D-155 still holds**: the bridge does not produce committable pipeline
  artefacts. Reading, linting, rendering and editing documents is fine; running
  `run_analysis.py` is not.

### Three traps, in the order they bit

1. **A timed-out shell orphans `soffice`.** The driver is killed, the process is
   not, and the next export hangs on the stale UNO listener rather than failing.
   *Before any export, check `pgrep -x soffice.bin` and `ls report_edits/odt/.~lock*`.*
   A stale `.~lock.report.odm#` was left behind and would have blocked the next
   master export.
2. **`pkill -f soffice` matches the shell that is asking.** The command line
   contains the pattern, so the shell kills itself — exit 143, nothing else
   happens.
3. **`pgrep -f 'office.bin'` returned pids 1, 2, 3.** Same self-match, and those
   are the VM's init processes; `kill -9` on them was sent. The VM survived,
   but only by luck. **Always `pgrep -x soffice.bin`** — exact name match, which
   cannot match the questioner.

---

## 2. Pushing, and verifying that it happened

Two commits were believed pushed and had not been. `HEAD` was still the previous
commit, a new tool was untracked, and a day of document work sat in the working
tree. The likely cause: a `git commit -m "…"` message spanning twenty lines does
not survive being pasted into a terminal.

**Hand over `git commit -F - <<'MSG' … MSG`, not `-m` with a long message.** A
heredoc has no quoting hazard.

**And verify.** `git log --oneline -1` and `git status -sb` after a push take a
second and are the only proof. "Pushed" is a belief until the log shows it.

---

## 3. What the gates actually catch — and the three blind spots

`check_all` is dense and mostly excellent. These are the gaps that let real
faults through this week.

### `reference_lint` cannot see a reference that moved twice

It compares typed references against **captions**. A reference moved two places
still points at a caption that exists — the wrong one. On 2026-09-19 twelve
references were double-moved and it read green.

Only `ref_audit` saw it, because it asks a different question: does the
reference agree with the **output the surrounding text names**? And it saw only
4 of the 12, because the other 8 name no output.

**The remedy is `tools/repoint_verify.py`**, written for this: it diffs every
reference against its pre-pass value in git and flags any delta that is not the
plan's. Run it immediately after a repoint pass and **before any hand repair** —
it compares against the plan, so a repair that also fixes older drift reads as
MOVED WRONG.

### `repoint_refs` had two silent double-application traps

- `--abbrev-only` was a pre-1.6.0 catch-up. Since 1.6.0 the default `FIG`
  pattern already matches `Fig N`, so running it after a default pass moves the
  abbreviated form a **second** time. It now refuses without `--pre-1-6-catchup`.
- `--plan` overrode the figure map only. `--plan mine.csv --kind table` printed
  "plan file: mine.csv" and then loaded `renumber_plan_table.csv` — a historical,
  already-applied plan. Fixed in 1.6.1; both maps now honour `--plan`.

**The renumber recipe is now:** plan pass → `figure_map.py` → `repoint_verify`
→ `reference_lint --snapshot` → `ref_audit`. No separate abbreviated pass.

### A generated ledger without a `--check` rots, silently

`TABLE_LEDGER.md` and `FIGURE_LEDGER.md` were built the same way from the same
manifest. FIGURE was correct throughout; TABLE had 48 tables with 20 flagged, 19
rows carrying an **empty source**, and a document list five supplement versions
old. The only difference: `build_figure_ledger.py --check` is a line in
`check_all.sh` and `build_table_ledger.py --check` never was.

**Every generated artefact gets a `--check` in `check_all` on the day it is
written, or it is not worth writing.**

### Smaller ones worth knowing

- **Field-carrying captions read stale until LibreOffice recalculates them.**
  A new `<text:sequence>` renders "Table 0" in the ODT's cached text and in the
  pandoc mirror. `reference_lint` then fails for a reason that is not a fault.
  The sequence is: **open in LibreOffice → Tools ▸ Update ▸ Fields → save →
  `refresh_mirrors` → `reference_lint --snapshot`.**
- **`pdftotext` is not a witness.** It reported Table 1.11 twice and no 1.13 in a
  correct document. Check field numbering in the ODT's own caption order, not in
  extracted text.
- **Running one script standalone breaks `pipeline_lint --check runid`.**
  `pipeline_site_observations.csv` is run-scoped; a standalone write mixes with
  the last full pass. The remedy is a full `run_analysis.py --full
  --with-supplementary`, which is the pre-commit form anyway because
  `output_lag` gates the opt-in steps.
- **`docref_lint` reads docstring placeholders as citations.** a placeholder output path ending in a markdown extension, and a
  paper-manifest path written with an N standing in for the paper number, both
  failed it in tool docstrings. Write placeholders that are not filenames.
- **A generated index that quotes glyphs trips `symbol_check`.** Both new
  ledgers are excluded, on the `VALUE_LEDGER` precedent — indexing a glyph is
  not using it.

---

## 4. The ledgers, and why they are keyed by output file

A document-keyed ledger says "table N of document D came from file F". The
question that matters when a script's output changes is the **inverse**: which
exhibits, in which documents, must be re-checked? Until 2026-09-20 that could
only be answered by grep.

- **`PROVENANCE_LEDGER.md`** (`build_provenance_ledger.py`) — every exhibit in
  the report chapters and both papers, keyed by the output that makes it, plus
  the outputs nothing renders. Derived from ODT captions, `table_configs.py`,
  `figure_map.csv` and each paper's exhibit manifest.
- **`VALUE_REGISTER.md`** (`build_value_register.py`) — the same inversion for
  cited values (`citation_index.csv`) and for the registered symbol senses bound
  to the output columns carrying them.
- **`table_provenance_lint.py`** — asserts the rule Martin stated: *a table
  cannot have no CSV; that breaks the line of truth from the pipeline to the
  documents.* All 24 report tables trace to a committed output.

Both ledgers are `--check` gated.

**The cross-document view is the payoff.** `07_coeff_05_cluster_ranges.csv` now
shows as feeding both Paper 1's Table 6 and report9's Table 1.4 — which is how
the missing report table was noticed at all.

### When auditing references, relate them to the CSV

Martin's question, and the method that made the audit work. The report, Paper 1
and Paper 2 each number tables from 1 and the supplement cites all three with the
same bare form. Prose similarity left 150 of 211 references unresolved; the CSV
link left none. `tools/table_ref_audit.py` does this, with two scoping rules
learned the hard way:

- **a registry row is parsed field by field**, never by character window — both
  pipe tables and pandoc simple tables. A window spanning two rows pairs a
  reference with the row above's CSV;
- **prose context is the sentence**, not ±200 characters, for the same reason:
  the window reaches into the neighbouring table's caption.

A **reference** has no CSV and is not supposed to have one — it names a table,
and the table carries the provenance. Resolving references through the table
inventory, not through nearby text, is what took the residue to zero.
