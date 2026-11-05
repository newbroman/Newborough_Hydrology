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
   row's check, about two minutes), that gate summary, the queue and the chat register, gathered
   into `scratch/hq/payload.json`, with the page's documents written one per file under
   `scratch/hq/db/` and indexed in `scratch/hq/db/ops.json`. It also appends one run to
   `working/hq_history.json`, which is where the task trend and "newly red" come from.
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
    `working/hq_history.json`, `working/chat_register.csv`. Nothing under `tools/`, `src/`, `docs/`
    or `outputs/`. A public commit without its private commit is a change nobody can account for
    (CLAUDE.md §4f), so if you touch anything public, commit both halves.
11. `python3 tools/chat_register.py status --chat "HQ daily pass" --set done --outcome "<one line>"`.

## What is not built yet

`rule_audit` (T-137) is the module that will make the findings above systematic — reading commits,
handover entries, the decision log and the lock's history. Until it lands, report what the gate
summary, the board and the task register show, and say in your report that the conduct checks are
not implemented. **Do not improvise them**: a hand-rolled audit that disagrees with the eventual
module would be worse than none, and spec §8 is explicit that a rule is checked in one place only.
