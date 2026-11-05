# Handover: NRG HQ, a landing page for every chat, with a daily rule-checking agent

**Status:** HANDOVER for the chat holding `tools`. D1–D8 SIGNED OFF by Martin (2026-11-05 03:09) as
recommended in §10; D9, the job queue (§14), signed off 03:16. The builder still gives its own design for sign-off before code.
**Written:** 2026-11-05 03:05, claude.ai chat session (Claude Opus 5.5), against public `main` at
`cd42999` (the private repository was not attached to the writing session).
**Builder:** a Claude Code session with BOTH repositories attached (notes/reference/SESSION_MODES.md),
holding `tools`. It builds on D-300 (the control board) and does not replace it.

---

## 1. Martin's request (2026-11-05, 02:59–03:03)

"A project management page, a bit like the one I designed for Music of the Spheres. A landing page
for all chats and code work about the project, and it uses an agent to monitor all the chats to make
sure they are behaving and following the rules."

His answers to the design questions (03:02–03:03):
- Checks at least daily.
- Registering is compulsory for every chat.
- The session holding `tools` builds it.
- Findings go on the page AND to his phone.
- The task register goes on the page: the list of known work and how it is moving.
- The `check_all` routines go on it too, as summaries.

## 2. Precedents to build from

- **MOTS HQ** (claude.ai artifact "MOTS HQ"): a private page with the `db` and `user` capabilities.
  A "start a new chat" console writes a brief for the chosen kind of work, copies it and opens the
  project; a chat index (`chats` collection) every chat registers in; `dates` and `meta/links`
  collections; an HQ Claude Code session that checks in on a schedule and keeps the page current.
  Reuse its structure, its brief-copying flow and its db layout. NRG gets its own look.
- **NRG Work Board** (D-300, `tools/board_artifact.py`, artifact "NRG Work Board"): the claims,
  both repositories against origin, ships, uncommitted files, from `work_board.py --json`.
- **`tools/task_lint.py`**: a task has no stored status; each row in `tools/task_register.csv`
  carries a check command and the output it must produce, and status is computed every run
  (OPEN / DONE / BROKEN / SKIP). On 2026-11-05: 133 tasks, 104 done, 28 open, 0 broken, 1 skipped.
- **`tools/check_all.sh`**: 50 sections, each headed `── name ──`, about 90 commands that set
  `rc=1`; it prints one overall line (`check_all: OK|FAIL`) and no per-section verdict.

## 3. What the agent can and cannot do

It cannot watch a chat live; no tool reads another conversation while it runs. It AUDITS AFTER THE
FACT, from what chats leave behind: commits and their `Claude-Session` trailers, handover entries,
the decision log, claims and the override log, ships, gate logs, the task register. Nearly every rule
leaves evidence, which is why this works. It REPORTS and never intervenes: it releases no claim,
edits nothing under another claim, and pushes nothing to `main` except its own records.

## 4. The page (one private claude.ai artifact, "NRG HQ")

Bands, top to bottom:

1. **Header links.** Talk to HQ (the HQ session), the project, both repositories, the proof page.
2. **Start a new chat.** Choose the kind of work, describe it in a line, and the page copies a brief
   and opens the project, as MOTS does. Kinds and what each brief carries:
   - *Pipeline / analysis* — attach both repositories, `cloud_setup.sh`, D-143 start, take `pipeline`.
   - *Document edit* — the same, take `doc:<family>`, and check `work_board.py` first.
   - *Tools* — the same, take `tools`.
   - *Read-only analysis or question* — no claim; told in the brief that it must not commit.
   - *Fieldwork / data in* — what it may write and where.
   Every brief ends with the registration step (§6) and the handover rules. The page also writes a
   `starting` row to `chats` itself, as MOTS does.
3. **Needs you.** The serious findings (§7) at the top, each with evidence and the chat concerned.
4. **Chats on the project.** Registered chats: title, kind, claim, mode (laptop / bridge / cloud-code
   / cloud-chat), status (starting / active / parked / done), last activity, outcome, link.
   Filters Active / Done / All, as MOTS.
5. **Work board.** Claims with taken / last activity / stale flag, both repositories against origin
   with fetch time, ships waiting, uncommitted files by claim. Rendered from the board snapshot (§5),
   so the separate NRG Work Board page becomes optional (D7).
6. **Tasks.** From `task_lint`: open tasks first, each with id, title, what it implements, current
   value against wanted value, age since opened, and a trend from the daily history (closer to done,
   further, unchanged). Done tasks collapsed with the date each closed. BROKEN and SKIP shown
   separately. A headline: open / done / broken, and how many closed or reopened this week.
7. **Gate.** The last full `check_all`: when, where (machine / session), overall verdict, and one
   line per section with its verdict. Advisory counts the gate prints but does not gate on (stale
   ledger versions, known dangling references, symbol backlog, and similar) shown with their trend,
   because those are work outstanding too. A section that turned red since the last run is flagged.
8. **Coming up and owed.** Owed republishes (the proof page, which has been behind its bundle since
   2026-10-09; the board page), unmerged branches older than a week, dates Martin adds.

## 5. Data

The page declares `db` (and `user`, for who is viewing). Collections:
`chats`, `findings`, `board` (latest snapshot), `tasks` (latest snapshot), `task_history` (one row per
task per run: value, status), `gate_runs` (one row per run: when, where, verdict),
`gate_sections` (per run per section: verdict, advisory counts), `dates`, `meta/links`.
The HQ agent writes them with ArtifactData (batch writes). The page renders from the db, so it is
live without republishing. Claim metadata stays off the public repository (D-300's R6 constraint);
the page is private to Martin.

## 6. Registration (compulsory)

- A chat registers before its first commit or claim: a row in a new private register
  `working/chat_register.csv` (written through `register_io`, so two chats merge row by row): chat
  name, kind, claim, mode, session link if known, opened, status, purpose. The HQ agent mirrors it to
  the `chats` collection.
- Enforcement, proposed (D3): `doc_lock.py take` refuses for a chat name not in the register, with
  the one-line command to register; and every commit should carry the `Claude-Session` trailer the
  harness already adds, which the agent matches against the register.
- CLAUDE.md §4b and the project instructions gain the rule; the brief carries it.

## 7. The HQ agent

**Schedule.** A scheduled task (create_trigger), daily, early morning London time, jittered off the
hour (say 06:41), with push notifications on. Plus on demand: "Talk to HQ" opens the HQ session,
where "check now" runs the same routine. Martin asked for at least daily; twice daily is a D4 option.

**Each run:**
1. Attach both repositories, `cloud_setup.sh`, D-143 start; pull.
2. `work_board.py --json --probe` → `board`.
3. `task_lint.py` in a machine-readable mode → `tasks`, `task_history`.
4. `check_all.sh` with a per-section summary (D5) → `gate_runs`, `gate_sections`. Piped through
   `tee`, with `${PIPESTATUS[0]}` as the real exit code (Martin's standing preference).
5. `tools/rule_audit.py` (new, §8) over everything since the previous run → `findings`.
6. Write the db in one batch; refresh `meta`; publish only if the page itself changed.
7. One handover entry of its own, and a push notification when anything serious is found.

**Notifications.** Serious findings go to Martin's phone; everything else waits on the page. Serious:
- an edit or commit under a claim held by another chat, or a forced take or release;
- a commit from an unregistered chat, or with no session trailer;
- `check_all` FAIL or FAULT on `main`, or a section newly red;
- a task gone BROKEN, or a DONE task reopened;
- a claim past the abandoned age (72 h of no activity);
- a ship waiting more than a day, or a repository behind origin on the machine that publishes.

## 8. What `rule_audit.py` checks

Each check reads evidence; each finding names the commit, file, chat and rule.
- Every commit since the last run has a dated handover entry with a provenance block and a
  "Decisions recorded this session" line (D-143; the project rules).
- New decision-log entries carry Retires and Revisit-if.
- Files changed in a commit fall under a claim held by the chat that made it (claim_for_path, the
  lock's history and the override log).
- A ship quotes a `check_all` verdict, and that verdict is OK.
- Versioned documents were bumped, never edited in place; the newest version found numerically.
- Script edits bump `__version__` (the assignment) and the SCRIPT_LEDGER row together.
- Every registered chat with activity has a status; a `done` chat holds no claim.
- Branches pushed but not merged for more than a week (the 2026-11-04 notes branch is the first).
- Em spaces, typed numbers and the rest are NOT re-implemented: the agent reads the existing lints'
  verdicts from the gate summary, so a rule is checked in one place only.

## 9. Gate summaries (D5)

`check_all` gives one verdict for 50 sections. Two ways to get per-section verdicts:
- (a) **Instrument `check_all.sh`**: a small `section NAME` helper records `rc` at each header and
  writes `scratch/check_all_summary.json` at the end (section, verdict, seconds, the advisory count
  lines the section printed). Exact, and costs nothing at run time.
- (b) **Parse the tee'd log** with a new `tools/gate_summary.py`, leaving `check_all` untouched.
  Fragile: a section's verdict has to be inferred from its printed lines.
Recommend (a). `check_all` is under `tools`, so it is the builder's to change, and the per-section
JSON also helps every chat that today greps the log for "FAIL".

## 10. Decisions (signed off 03:09, all as recommended)

- **D1 Name.** "NRG HQ", matching "MOTS HQ".
- **D2 Kinds of work** in the start console: the five in §4.2, or a different list.
- **D3 Enforcement.** `take` refuses unregistered chats (recommended), or registration is checked
  only after the fact by the agent.
- **D4 Schedule.** Daily at about 06:41 (recommended), or twice daily (06:41 and 18:41).
- **D5 Gate summary.** Instrument `check_all` (recommended) or parse its log.
- **D6 Task trend window.** Trend over the last 7 daily runs (recommended).
- **D7 The NRG Work Board page.** Fold into HQ and stop republishing it (recommended), or keep both.
- **D9 Job queue (§14).** Signed off 03:16: a queue of jobs that fire themselves when their conditions
  are met, so Martin stops carrying messages between chats.
- **D8 Task ownership.** Optionally add a `claim` column to `task_register.csv` so each task shows
  who should do it (T-135 → `pipeline`). Recommended, as an optional column task_lint ignores.

## 11. Build order

1. Page, db, registration register, board and tasks bands, the scheduled task with notifications.
2. Gate summary (D5) and its band.
3. `rule_audit.py` and the findings band.
4. Enforcement in `doc_lock.py take` (D3), once registration has run for a few days.

## 12. Acceptance tests

In throwaway trees through `NRG_REPO_ROOT` (D-300); never the real lock or register.
- A commit under another chat's claim → a serious finding and a notification.
- A commit with no handover entry → a finding; with one → none.
- A task whose check value changes between two runs → the trend moves; a DONE task reopened → serious.
- A section that fails in one run and passed the run before → flagged newly red.
- An unregistered chat's `take` → refused (if D3), with the register command printed.
- A run with the private store absent → the agent reports it cannot audit, and does not report
  "all clear" (the D-300 lesson, applied to the auditor itself).

## 13. Records the build writes

Version bumps and inline changelogs (`doc_lock.py`, `work_board.py`, `task_lint.py`, `check_all.sh`,
new `rule_audit.py`); a CHANGELOG_delta; a decision-log entry for the registration rule and one for
the agent's report-only remit; CLAUDE.md §4b, SESSION_MODES.md, the project instructions; a task row
for each build phase not finished in the first session; the handover entry.

## 14. The job queue (D9, signed off 03:16)

Martin's request: "is there a way of automating this", meaning: one chat finishing should start the
next without him passing prompts by hand.

**The register.** `working/job_queue.csv` in the private repository, written through `register_io` so
chats merge row by row. Columns: `id`, `title`, `brief` (path to a self-contained brief file, never
the prompt inline), `claim` (what the job will take), `waits_for` (conditions, all of which must
hold), `target` (`new_session` or `notify`), `status` (`queued` / `ready` / `fired` / `done` /
`held`), `trigger_id`, `fired_at`, `fired_by`, `note`.

**Conditions** (`waits_for`, semicolon-separated, each machine-checkable):
`claim_free:<name>`, `job_done:<id>`, `on_main:<path>` (a file exists on `main`),
`task_done:<T-id>`, `held_by_martin` (never fires until he clears it).

**Firing.** Each `new_session` job gets a poke-only scheduled task (create_trigger with no schedule)
whose prompt is "Run job <id>: read <brief> and follow it". A job is fired, by the HQ agent's daily
run and by `doc_lock.py release` (which prints any job its release made ready, and the session
releasing then fires it), once every condition holds. Firing records `trigger_id`, `fired_at`,
`fired_by`, and sends Martin a phone notification. A `notify` job, for work that must go to an existing
chat (one cannot message another session), only notifies Martin with the brief to paste.

**Guards.** A job never fires while its `claim` is held. One job per claim at a time. A fired session
that meets a design question stops and waits for Martin (every brief says so); the queue does not
make decisions, it only removes the relaying. If the private store is absent, nothing fires and the
HQ page says why.

**The page** shows the queue as its own band: each job, its conditions with which hold and which do
not, and status.

**Seeded on first build** (the build session writes these rows as its final step):
- **J-1** Script 55 build. Brief `notes/specs/NRG_brief_script55_build_2026-11-05.md`. Claim
  `pipeline`. Waits for: HQ shipped (`on_main:tools/rule_audit.py` or the HQ build's own marker) and
  `claim_free:pipeline`. Target `new_session`. With HQ shipped, it is ready at once, so the build
  session fires it after its own ship and release.
- **J-2** Paper M §5.3 passages and the §7.1 clause. Waits for `job_done:J-1`. Target `notify`
  (the Paper M chat holds `doc:PaperM`; Martin passes it the keys and drafts), unless that chat has
  released `doc:PaperM` by then, in which case a new session takes it.
