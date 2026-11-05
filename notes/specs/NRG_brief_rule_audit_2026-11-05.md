# Job brief: `tools/rule_audit.py` and the findings band — NRG HQ phase 3

**Queued job J-3** in the NRG HQ job queue (`working/job_queue.csv`). Claim **`tools`**. Ready when
**J-1** is done — that is, when Script 55 is on `main` with its outputs committed. Target
`new_session`.

**Why it waits for J-1 rather than for `claim_free:tools`.** `tools` is free now, so the condition
would already hold. The wait is deliberate: J-1 ships Script 55, `run_analysis.py` and a
SCRIPT_LEDGER row, and this job edits `tools/` and `check_all.sh`. Two chats shipping across that
boundary on the same day is how the ship-hold machinery earns its keep, and there is no reason to
find out. J-1 first.

**Written:** 2026-11-05 by the HQ build session, from
`notes/specs/NRG_handover_HQ_page_2026-11-05.md` §§7, 8, 10 (D8), 11 (phase 3) and 12, which Martin
signed off as D1–D9. Nothing here is new design; it is the handover's own instruction, made
self-contained, plus what the phase-1/2 build learned.

**This is the part of Martin's 2026-11-05 02:59 request still owed.** He asked for a page *and* an
agent that monitors the chats. The page reports the state of the TREE and is live. This is the half
that reports on the CHATS. T-137 is its register row.

## Step one: merge `fix/hq-mobile-wrap` and record the publish

The first piece of WORK, before `rule_audit.py` itself. **Before the code** below still comes first — register the chat, take `tools`, read the spec — because this merge lands in `tools/`.

Martin, 2026-11-05: "merge branch fix/hq-mobile-wrap (hq_page 1.0.1: phone wrapping, the
machine-lock card wording, the fired pill). It is already published to the HQ artifact from a
public-only chat; after check_all, record it with
`python3 tools/hq_page.py --published https://claude.ai/artifact/QV6MQcRvVx3eiDqgmFZCyt`"

    git fetch -q origin && git merge --no-ff origin/fix/hq-mobile-wrap

One commit, `97e94152`, one file, +28/-7, all of it `tools/hq_page.py`. Inspected 2026-11-05 from
this chat: it is **rendering only**. `.cond`'s text column becomes `minmax(0, 1fr)` (a bare `1fr`
has a min-content floor, so one long brief path widened the column past a phone screen), list items
and flex rows get `min-width: 0` and `overflow-wrap: anywhere`, the `fired` pill gains the amber it
was missing, and the machine-lock card now says what the lock MEANS — the machine whose copy of the
ODTs is the working copy, which since D-299 a bridge chat takes under the L14's name — instead of
reading as a laptop in use. It adds no data to the shell, which still renders from its own store,
and `fmt()` (used by the new `since` rendering) is defined at line 398. `tools/` is J-3's claim, so
this merge is in scope.

**Then, after `check_all`, record it. `--published` RECORDS; it does not publish.** It stamps the
url, the time and the local `__version__` into `working/.hq_artifact.json` and clears
`working/.hq_publish_owed` — nothing is sent to claude.ai. Order matters: merge first, so the
version it stamps is 1.0.1 and not 1.0.0.

**Why the step exists at all, and it is worth understanding before running it.**
`working/.hq_artifact.json` is in the PRIVATE repository. The chat that published the page holds
only the public one, so it could publish and could not record. That is the whole of this step.

**Do NOT republish the shell here.** The artifact already carries a version published after this
session's (`1793880105-b284`, read 2026-11-05), so a republish needs the url read again and the
edits merged onto that version first. The merge plus `--published` leaves the live page exactly as
it is and only makes the repo's record true.

**And a gap in `--check` that this exposes, which is reportable under §8 rather than something to
fix here.** The check compares the RECORDED `shell_version` against the local `__version__`
(`hq_page.py:779`). It never looks at the artifact. So right now, with the record at 1.0.0, the repo
at 1.0.0 and the live page at 1.0.1, it prints `OK — is current (shell 1.0.0)`: it can see a repo
that is ahead of the page and is blind to a page that is ahead of the repo. Between the merge and
`--published` it will say "republish it", which is also wrong, because the page is already 1.0.1.
Both readings are honest about what it measures and wrong about the world. Note it as a finding;
widening it is not this job.

## What it is

One new module, `tools/rule_audit.py`, that reads evidence and emits findings. **Each finding names
the commit, file, chat and rule.** It is bound by **D-302**: it reports, it never intervenes, and it
writes nothing when the private store is absent.

The findings band and the serious/not-serious split **already exist** in `tools/hq_page.py` and in
the db schema (`findings`). This job fills them; it does not design them.

## The checks (spec §8)

Each reads evidence; none is a heuristic over prose.

1. Every commit since the last run has a dated handover entry in
   `working/updates/HANDOVER_NOTE.md` with a provenance block and a "Decisions recorded this
   session" line (D-143).
2. New `DECISION_LOG.md` entries carry **Retires** and **Revisit-if**.
3. Files changed in a commit fall under a claim held by the chat that made it — from
   `claim_for_path`, the lock's history, and `working/claim_overrides.csv`.
4. A ship quotes a `check_all` verdict, **and that verdict is OK**.
5. Versioned documents were bumped, never edited in place; the newest version found **numerically**,
   not lexically (`v1_9_46` sorts after `v1_9_9`).
6. A script edit bumps `__version__` (the assignment) **and** its SCRIPT_LEDGER row together.
7. Every registered chat with activity has a status; a `done` chat holds no claim.
   **Measured trap, 2026-11-05:** the register's `claim` column records what a chat is registered to work on; it is **not** a live hold. `control board` is `done` with `claim=tools` in the register while `tools` is free on the board. Check the lock, not the register column, or this rule fires on every finished chat.
8. Branches pushed but not merged for more than a week. `notes/2026-11-04-water-balance-handovers`
   is the first, and it is deliberate — it is for reading, not merging — so the finding must be
   suppressible with a reason, not just reported.

## What it must NOT do

**Do not re-implement the em-space, typed-number or any other existing lint.** Read their verdicts
from the gate summary (`scratch/check_all_summary.json`, written by `check_all.sh` 1.34.0, which the
phase-2 build added). A rule is checked in **one** place. The spec says this explicitly and it is
the main way this module could go wrong: it is an auditor of the audit trail, not a second linter.

## Serious, for the notification (spec §7)

Serious findings go to Martin's phone; everything else waits on the page. Serious is:

- an edit or commit under a claim held by another chat, or a forced take or release;
- a commit from an unregistered chat, or with no session trailer;
- `check_all` FAIL or FAULT on `main`, or a section newly red;
- a task gone BROKEN, or a DONE task reopened;
- a claim past the abandoned age (72 h of **no activity** — staleness is measured from last
  activity, not from when the claim was taken, D-300);
- a ship waiting more than a day, or a repository behind origin on the publishing machine.

## Wiring

- `tools/hq_snapshot.py` step 5 calls it and writes `findings`. The snapshot's `newly_red()` keys on
  `s["key"]`; findings need the same stable keying so "newly found" means something across runs.
- `notes/reference/HQ_DAILY_PASS.md` already describes step 5. Check whether what you build matches
  what that runbook tells the 06:41 cloud routine to do, and correct the runbook if not — the
  routine reads it from `main`.
- A `--check` on the day it is written. §4d of CLAUDE.md: a generated artefact without its `--check`
  in `check_all` rots silently, and TABLE_LEDGER is the measured case.
- A `_selftest()` in-module, and a gate in `check_all.sh`. Add it to the existing
  `rule audit` position or open one; `ship_regen_lint` will want to know about any new generated
  artefact.

## Acceptance tests (spec §12)

In throwaway trees through **`NRG_REPO_ROOT`** (D-300) — **never the real lock or register.**

- A commit under another chat's claim → a serious finding and a notification.
- A commit with no handover entry → a finding; with one → none.
- A task whose check value changes between two runs → the trend moves; a DONE task reopened →
  serious.

And one the phase-1/2 build earned the hard way: **make each selftest branch bite.** Disable the
branch under test and confirm the test fails. Three defects in the phase-1/2 work were found by
reading output, not by a gate — an unanchored `grep` that matched the selftest's own source and read
T-138 as DONE while the switch was off; `grep -c` exiting 1 on a count of zero, which `task_lint`
correctly calls BROKEN rather than a pass; and two `check_all` sections both named "claims".

## Before the code (do this first of all)

- Register the chat (compulsory in practice, D-301):
  `python3 tools/chat_register.py register --chat "<name>" --kind tools --claim tools
  --purpose "rule_audit and the findings band (T-137, HQ phase 3)"`
- `python3 tools/doc_lock.py take tools --chat "<name>" --note "rule_audit (J-3)"`
- `python3 tools/work_board.py`, and read `notes/specs/NRG_handover_HQ_page_2026-11-05.md` §§7, 8,
  10, 11, 12 in full before writing anything. This brief is a summary of them; they are the source.
- Attach **both** repositories. Without the private one the lock reads UNKNOWN, `take` refuses, and
  this module has no evidence to read (D-300).

## Phase 4 is not this job

T-138 — flipping `REGISTRATION_REQUIRED` to `True` in `doc_lock.py` — waits until registration has
run for a few days. The mechanism is already in `doc_lock` 1.5.0 and it is a one-line change. Do not
do it as part of this job.

## Unattended rule

If a question comes up that this brief and the spec do not answer — whether a particular rule's
evidence is strong enough to call a finding serious, how to suppress the deliberate unmerged branch —
stop, set out the question with a recommendation, and wait for Martin. The queue removes the
relaying; it does not make decisions.
