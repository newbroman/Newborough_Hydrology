# The NRG HQ daily pass — the routine's own instructions (D-301, D-302)

A claude.ai scheduled cloud agent runs this every morning at 06:41 Europe/London. Its prompt is one
line pointing here, so that **what it does is version-controlled and reviewable** rather than buried
in a routine's configuration where nobody will read it again.

**The remit, before anything else: REPORT, NEVER INTERVENE (D-302).** Release no claim, edit nothing
under another chat's claim, and push nothing but your own records — your handover entry and the
snapshot. A wrong report costs a conversation; a wrong release costs another chat's work.

## Setup, in this order

1. `curl -sSL https://raw.githubusercontent.com/newbroman/Newborough_Hydrology/main/tools/cloud_setup.sh | bash`
   It clones the public repository as the working tree, puts the private one at `.git-working` over
   the same tree (CLAUDE.md §4f), builds the environment, and runs the session handover.
   **Do not wrap it in a timeout** (`timeout 170` or any other): it can take half an hour, because the
   private checkout fetches each of ~2,500 files on demand. Run it in the background with its log
   tee'd to a file and read the log; a cloud process survives between tool calls (CLAUDE.md §4g). On
   2026-11-11 this pass cut the setup short with its own timeout and saw ~2,159 private files as
   deleted (T-198). Since `cloud_setup.sh` 1.3.0 a re-run finishes a half-done checkout, but a
   killed run is still a wasted run. Before step 3, `git --git-dir=.git-working --work-tree=. ls-files
   --deleted | wc -l` must print 0; if it does not, the private store is incomplete: re-run the setup,
   and do not read claims from a half-built tree.
2. Read `working/HANDOVER_BOOTSTRAP.md` and `CLAUDE.md`. CLAUDE.md is the traps file and §4b is this
   system. Read the newest entry of `working/updates/HANDOVER_NOTE.md`.
3. `python3 tools/doc_lock.py status`
   **If the private store is ABSENT, STOP.** Write nothing, publish nothing. Report that you could
   not audit and name the half that was missing. A snapshot taken without the private repository
   invents open tasks and free claims — measured 2026-11-05: a public-only session read 104 of 133
   tasks done where a session with both read 120 of 136 — and this routine must never report
   "all clear" for what it cannot see. That is D-302, and it is not negotiable.
4. Register: `python3 tools/chat_register.py register --chat "HQ daily pass" --kind readonly
   --purpose "the daily HQ snapshot"`. **Take no claim.**

## The pass

5. `bash tools/check_all.sh 2>&1 | tee scratch/hq_gate.log` — about twelve minutes. Run it in the
   background and read the log rather than waiting on it. Use `${PIPESTATUS[0]}` for the real exit
   code, never the exit code of `tee`. It writes `scratch/check_all_summary.json`: a verdict per
   section (`check_all.sh` 1.34.0), which is what you read instead of grepping the log for "FAIL".
6. `python3 tools/hq_snapshot.py --db-ops --probe` — the board, the task register (it runs every
   row's check, about two minutes), that gate summary, the queue, the chat register and
   **`rule_audit`'s findings** (the conduct checks, below), gathered
   into `scratch/hq/payload.json`, with the page's documents written one per file under
   `scratch/hq/db/` and indexed in `scratch/hq/db/ops.json`. It also appends one run to
   `working/hq_history.json`, which is where the task trend and "newly red" come from.
   **Since hq_snapshot 1.2.0 (J-12, 2026-11-11) it also refreshes the proof page's bundle** —
   `proof_copy.py --refresh`, moved here from `check_all`, with its tasks tab fed from the sweep
   above. It prints one `proof page:` line saying whether the published proof artifact is current.
   A cold container regenerates all 25 chapters (about 4½ minutes); later runs only what changed.
7. **Write those documents to the HQ page's store** with the `ArtifactData` tool, `action: "batch"`,
   `url: <the HQ page's URL>` (it is in `working/.hq_artifact.json`), passing each op from
   `ops.json` as `{op, collection, doc_id, file_path}`. Two things to know:
   - An op marked `create_if_missing` (today only `meta/links`) is an **update**, and an update to a
     document that does not exist is refused — and a batch is atomic, so one such op writes nothing
     at all. If it fails that way, set that document instead and batch the rest. Measured on the
     first HQ write, 2026-11-05.
   - A write to a document that already exists needs `if_version`, the version you last read. Read
     the collection first (`action: "list"`) and pin each write, or set them one at a time.
   If the `ArtifactData` tool is not available to you, say so plainly in your report rather than
   working around it: the payload is committed, so any session can write it, and the page will show
   the previous day's snapshot until one does. Do not try to publish the page itself — the shell
   changes rarely, and `python3 tools/hq_page.py --check` says when it is owed.
7b. **If the `proof page:` line says BEHIND, republish it and stamp it** (J-12; Martin 2026-11-09:
   *"q9 move to the hq daily pass"*). With the Artifact tool, publish
   `scratch/proof_bundle/NRG_proof_shell.html` as the page and
   `scratch/proof_bundle/proof_chapters.json` as a file beside it (`files`), to the URL in
   `working/.proof_artifact.json` — read the artifact first if this session has not, as the tool
   requires. Then `python3 tools/proof_copy.py --published <the version the publish returned>`,
   which writes `tools/proof_bundle_state.json` (it refuses if the bundle on disk is not the one the
   state describes). **This is the pass's own page, not intervention** (D-302 binds it to report-only
   for OTHER chats' work): the stamp file is under no claim. If the Artifact tool is not available,
   say so in the report and leave the stamp alone — a stamp without a publish is a false record.
   The `bundle_sha256` it compares is a function of the chapters and the Bindings tabs (proof_copy
   1.38.0), so an unchanged bundle stays current; a change to the tasks tab alone does not make the
   page stale.
8. `python3 tools/job_queue.py ready` — any job whose conditions now all hold. Fire a `new_session`
   job only if you can actually start that session; otherwise leave it `ready` and name it in your
   report, which is what the queue expects of you (a job fires when something is already running).
   Never fire a job whose claim is held.

## What to report, and how loudly

**To his phone** (serious), and on the page:
- an edit or commit under a claim another chat held, or any forced take or release
  (`working/claim_overrides.csv` is append-only and is the evidence);
- a commit from a chat that is not in `working/chat_register.csv`;
- `check_all` FAIL or FAULT on `main`, or any section newly red since the previous run;
- a task gone BROKEN, or one that was DONE and has reopened;
- a claim past the abandoned age (72 h with no activity) — **flag it, never release it**;
- a ship request waiting more than a day, or a repository behind origin.

**On the page only:** everything else — open-task movement, advisory counts, owed republishes,
branches unmerged for more than a week.

## Finish

9. One dated entry of your own at the top of `working/updates/HANDOVER_NOTE.md` (≤40 lines), saying
   what you found and what you could not see. Then `python3 tools/session_handover.py --write --check`.
10. Commit **only** `working/` records and the snapshot — your handover entry,
    `working/hq_history.json`, `working/chat_register.csv` — and, when step 7b stamped a publish,
    `tools/proof_bundle_state.json` (public; the one exception, J-12). Nothing else under `tools/`,
    and nothing under `src/`, `docs/` or `outputs/`. If the refresh left
    `tools/proof_bundle_state.json` changed WITHOUT a publish (the chapters moved), commit it too:
    it records what the bundle was built from, and leaving it modified hands it to the next commit. A public commit without its private commit is a change nobody can account for
    (CLAUDE.md §4f), so if you touch anything public, commit both halves.
11. `python3 tools/chat_register.py status --chat "HQ daily pass" --set done --outcome "<one line>"`.

## The conduct checks (T-137 landed 2026-11-05)

`tools/rule_audit.py` makes the findings above systematic, and step 6 above now calls it: it reads
the commits in the window, the handover entries, the decision log, the lock's history, the override
log, the registers and the gate summary, and returns findings with a `serious` flag that matches
"What to report, and how loudly" above. **It is still report-only (D-302)**: `--check` returns 0
with serious findings outstanding and says so, because an open finding is work outstanding, not a
broken check.

Three things this routine needs to know about it.

- **The window is a watermark**, `working/rule_audit_state.json`. `hq_snapshot --db-ops` moves it
  after a successful pass, so each morning audits the day before and not the whole corpus. With no
  state — a first run, a fresh clone — the window is the last two days. Do not pass `--since`
  unless you mean to re-audit old history.
- **Attribution is by the `Claude-Session` trailer**, matched against the register's `link` column.
  Commits without it are reported as a serious `session-trailer` finding, and their claim coverage
  is reported as UNKNOWN in one aggregate finding rather than as a breach. So a morning with many
  untrailered commits is a true report about the records, not a pile of accusations — say so that
  way in your report.
- **A finding you judge deliberate is suppressed with a REASON**, never by editing the rule:
  a row in `working/rule_audit_suppress.csv` (`rule,subject,reason,by,when`). A row with an empty
  reason suppresses nothing, by design. The first such row is the
  `notes/2026-11-04-water-balance-handovers` branch, which stays unmerged because it is for reading.
  **Adding a suppression is Martin's call, not this routine's** — report the finding and say that
  suppressing it is available; do not write the row yourself (D-302: report, never intervene).

`python3 tools/rule_audit.py` on its own prints the findings as text, which is the quickest way to
see what the page will show before you write the db.

## What is not built yet

Phase 4 — T-138, making registration a refusal rather than a warning
(`REGISTRATION_REQUIRED = True` in `doc_lock.py`). It waits deliberately until registration has run
for a few days (spec §11), and flipping it is not this routine's to do.
