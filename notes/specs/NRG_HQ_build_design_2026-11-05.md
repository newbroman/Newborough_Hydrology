# NRG HQ — build design for sign-off

**Builder:** control board chat, Claude Code desktop on the L14, holding `tools`.
**Against:** `notes/specs/NRG_handover_HQ_page_2026-11-05.md` (D1–D9 signed off), MOTS HQ
(artifact `EKEkVTBVmMbrXzDCxsWUF5`, read in full), `notes/specs/NRG_brief_script55_build_2026-11-05.md`.
**Public main:** `394e3814`. **Private:** `3d599ba`.

---

## 0. Three things I measured that change the spec

### 0.1 A scheduled task in this app is NOT a cloud trigger (affects §7, §14)

The spec says `create_trigger`, daily at 06:41, with push notifications. What this session actually
has is `mcp__scheduled-tasks__create_scheduled_task`, and its own description is explicit:

- the task is stored under `/home/john/.claude/scheduled-tasks/<id>/` as that task's own skill
  file — **on the L14**;
- "Scheduled tasks run while this app is open. If the app is closed when a task is due, it runs on
  next launch."

So a 06:41 daily task does not run at 06:41. It runs whenever Martin next opens the desktop app,
which is exactly the failure mode the HQ agent exists to prevent — it would report yesterday's state
as today's. It also cannot `cloud_setup.sh` and attach both repositories the way §7.1 requires,
because it runs in whatever state the laptop is in.

The vehicle that matches §7 is a **scheduled cloud agent (routine)** — the `/schedule` skill's
"scheduled cloud agents (routines) that execute on a cron schedule". That runs without the laptop,
can attach both repositories, and is where a daily audit belongs. **Q1 below.**

### 0.2 "A job fires itself" has no engine between runs (affects §14)

§14 gives each `new_session` job a poke-only trigger "with no schedule". That exists — omit both
`cronExpression` and `fireAt` and the task is ad-hoc — but the same tool says an ad-hoc task "can
only be started manually". Nothing in it wakes up. So a job only ever fires when **something is
already running**: the HQ routine's daily pass, or the session that released the claim. Between
those two, the queue is inert, whatever rows it holds.

That is still worth having — it removes Martin from the relay, which is what he asked for — but the
honest claim is "fires within a day, or immediately on the release that unblocks it", not "fires
itself". **Q2 below.**

### 0.3 J-1's own `waits_for` would not be satisfied by this build (affects §14, §11)

§14 seeds J-1 waiting on `on_main:tools/rule_audit.py`. `rule_audit.py` is **phase 3** of §11's
build order. If this session ships phases 1–2, J-1 would sit `queued` on a file that does not exist
yet, and Script 55 would not start — the opposite of the intent, which is that J-1 is ready the
moment HQ is shipped. The spec itself offers the alternative ("or the HQ build's own marker").

I propose J-1 waits on `on_main:tools/job_queue.py;claim_free:pipeline` — the queue's own module,
which is phase 1 and therefore true as soon as the queue exists to hold the row.

### 0.4 Two smaller measurements

- **`check_all` instrumentation is safe.** `rc` is read in exactly two places, lines 808–809
  (`[ "$rc" = "0" ] && … ; exit "$rc"`). Nowhere else reads it. So a `section` helper can flush and
  **reset** `rc` at every header and accumulate a separate total, and none of the 97 `rc=1` sites
  needs touching. Without the reset the design would be wrong: `rc` is sticky, so after the first
  red section every later one would read green. 50 headers live in the script; the log shows 53
  `──` lines, so three come from called tools — the helper keys on its own headers only.
- **`task_lint` has no machine-readable mode** (`--quiet`, `--open` only), so it needs `--json`.
  And its counts are **store-dependent**: the spec's writing session (public only) measured
  133 tasks / 104 done / 28 open / 1 skipped; this session, with both repositories, measures
  **134 / 120 / 14 / 0**. That is not drift, it is the D-300 lesson again — a public-only run would
  overwrite the snapshot with 14 phantom open tasks. The agent therefore records the store state on
  every snapshot and **refuses to write** one taken without the private store (§12's last test).

---

## 1. The page (one private artifact, "NRG HQ")

`capabilities: {db: {}, user: {}}`. Not `artifact`: the page never republishes itself — HQ writes the
db and the page renders live from it, so no conflict machinery and no self-publish path. Default db
rules; the page is private to Martin, who is the owner.

**Look.** Its own identity, not the Work Board's and not MOTS's. Dune-slack palette: marram and wet
sand neutrals with a slate ink and a saltmarsh accent; Spectral for display, IBM Plex Sans for body,
IBM Plex Mono for every number, claim and sha. Both themes, tokens on `:root`, the two dark blocks.

**Bands, top to bottom** (§4, with the queue band from §14 placed where it earns its position):

1. **Header** — Talk to HQ / project / both repositories / proof page, from `meta/links` so a link
   changes without republishing.
2. **Needs you** — serious findings, each with its evidence, rule and chat. Empty state says
   "nothing since <when>", never "all clear" with no run behind it.
3. **Start a new chat** — the five kinds from §4.2, a line of description, copy-brief-and-open, and a
   `starting` row written to `chats`. Every brief ends with the registration step and the handover
   rules. MOTS's flow verbatim, including the readonly textarea fallback when the clipboard refuses.
4. **Jobs** — the queue: each job, its conditions with a tick or a cross against each, status.
5. **Chats** — registered chats, filters Active / Done / All.
6. **Work board** — claims with taken / last activity / stale flag, both repositories against origin
   with fetch time, ships, uncommitted files by claim. From the `board` snapshot (D7: this replaces
   the separate Work Board page).
7. **Tasks** — open first, each with current against wanted, age, and a 7-run trend (D6); done
   collapsed; BROKEN and SKIP separate; the headline counts.
8. **Gate** — the last `check_all`: when, where, verdict, one line per section, advisory counts with
   their trend, and a flag on any section newly red.
9. **Coming up and owed** — owed republishes, unmerged branches over a week old, Martin's dates.

Collections exactly as §5: `chats`, `findings`, `board`, `tasks`, `task_history`, `gate_runs`,
`gate_sections`, `jobs`, `dates`, `meta/links`.

## 2. What the build changes, file by file

| file | from | what |
|---|---|---|
| `tools/check_all.sh` | 1.33.0 → **1.34.0** | `section "<name>"` helper replacing the 50 `echo "── … ──"` lines: prints the same header, flushes the previous section's verdict, resets `rc`, accumulates `total`; writes `scratch/check_all_summary.json` (section, verdict, seconds, advisory lines) and keeps the one `check_all: OK|FAIL` line and the same exit code (D5a) |
| `tools/task_lint.py` | → **+`--json`** | one row per task: id, title, check, want, got, status, opened, closed, and the optional `claim` column (D8) |
| `tools/doc_lock.py` | 1.4.1 → **1.5.0** | `release` prints any queued job its release made ready, with the one line that fires it; reads the chat register for the warning in phase 1 (the D3 **refusal** waits for phase 4, as §11 says) |
| **new** `tools/chat_register.py` | 1.0.0 | `working/chat_register.csv` through `register_io`: `register` / `status` / `list` / `--check`; the compulsory row of §6 |
| **new** `tools/job_queue.py` | 1.0.0 | `working/job_queue.csv` through `register_io`: `add` / `ready` / `fire` / `done` / `hold` / `--check`; the five condition kinds of §14, each machine-checkable; the guards (never while the claim is held, one job per claim, nothing fires with no private store) |
| **new** `tools/hq_snapshot.py` | 1.0.0 | gathers board + tasks + gate summary + queue + register + findings into one payload for the db. **It writes no db** — no script can; only a session holding the ArtifactData tool can, so the script's job is the payload and the session's job is one batch write |
| **new** `tools/hq_page.py` | 1.0.0 | renders the page to `scratch/hq/index.html` (gitignored), `--check` for an owed republish, `--published URL` recorded in `working/.hq_artifact.json` (private) — the privacy shape `board_artifact.py` already uses |
| **new** `tools/rule_audit.py` | 1.0.0 | §8's checks, phase 3; reads the existing lints' verdicts from the gate summary rather than re-implementing a single rule |
| `tools/board_artifact.py` | 1.0.1 → **1.1.0** | D7: kept as a module, stops being republished, its `--check` leaves `check_all` |
| `tools/check_all.sh` | (same bump) | `--selftest` gates for `chat_register`, `job_queue`, `hq_snapshot`; `--check` for both new registers, on the day they are written (§4d's rule) |
| records | | CHANGELOG delta; two decision-log entries (the compulsory registration rule; the agent's report-only remit) + `DECISIONS_PUBLIC.md`; CLAUDE.md §4b; `notes/reference/SESSION_MODES.md`; a task row per unfinished phase; the handover entry |

## 3. What ships this session, and what does not

§11's order, with a line drawn where I think this session should stop:

- **Phase 1** page + db + `chat_register` + `job_queue` + board and tasks bands + `hq_snapshot`.
- **Phase 2** gate summary (D5a) and its band.
- — ship here, and seed and fire J-1 —
- **Phase 3** `rule_audit.py` and the findings band → a task row, and a queued job.
- **Phase 4** D3 refusal in `doc_lock take`, "once registration has run for a few days" (§11's own
  condition, which cannot be met today) → a task row.

Phases 1–2 are what make J-1 fireable, which is the point of tonight. Phase 3 is the largest single
piece of the build and the one most likely to need its own judgement calls about what counts as
evidence; it deserves its own session rather than the tail of this one.

## 4. Testing

Throwaway trees through `NRG_REPO_ROOT`, never the real lock, register or queue — D-300's rule,
which `doc_lock --selftest` already follows. `_selftest()` in each new module, gated in `check_all`.
§12's acceptance tests, each in a throwaway tree, including the two that matter most:

- a run with the private store absent → the agent reports it cannot audit and writes no snapshot,
  and the page says why. **Not** "all clear".
- a condition's tick and cross, and a job that must not fire because its claim is held.

The page itself gets the functional pass the capabilities guidance requires: after the first
publish, one `ArtifactData` list of each collection it writes.

## 5. Questions — the three I cannot answer for you

**Q1. Where does the daily agent run?** (§0.1)
- (a) **A claude.ai scheduled cloud agent**, daily ~06:41 London. Runs without the laptop, attaches
  both repositories, does the full §7 routine. **Recommended.**
- (b) A local scheduled task on the L14 — runs when you next open the app, not at 06:41.
- (c) Both: the cloud routine audits; a local task is the "check now" poke.

**Q2. What fires a queued job between daily runs?** (§0.2)
- (a) **The release that unblocks it, plus the daily routine as the backstop.** `doc_lock release`
  prints the ready job and the session fires it; worst case a job waits until the next morning.
  **Recommended** — it is honest about the engine and needs nothing new.
- (b) Additionally a short cloud routine every two hours whose only job is to drain the queue.
- (c) A one-shot cloud agent created at fire time, so the job runs in the cloud rather than waiting
  for a session on the laptop.

**Q3. Where do serious findings go when Remote Control is not connected?** `PushNotification`
reaches your phone only while Remote Control is connected to this machine; a cloud routine has its
own notification path. Recommended: the cloud routine notifies, and the "Needs you" band is the
durable record that survives a missed notification — so nothing depends on a push arriving.

And one I will take as yes unless you say otherwise: **J-1 waits on
`on_main:tools/job_queue.py;claim_free:pipeline`** rather than on `rule_audit.py` (§0.3).

---

## 6. Sign-off (Martin, 2026-11-05)

> Yes, as recommended

Taken as: Q1 (a) a claude.ai scheduled cloud agent, daily about 06:41 London; Q2 (a) the release
that unblocks a job fires it, with the daily routine as the backstop; Q3 the routine notifies and
the "Needs you" band is the durable record; and J-1 waits on
`on_main:tools/job_queue.py;claim_free:pipeline` rather than on `rule_audit.py`.

## 7. As built (phases 1 and 2)

| file | version | what |
|---|---|---|
| `tools/chat_register.py` | **1.0.1** new | `working/chat_register.csv` through `register_io`; `register` / `status` / `--check` / `--json` / `--selftest`. 1.0.1 adds `registered_by`: a row written for ANOTHER chat is marked SEEDED, because "every chat registers itself" is a rule the agent audits and a seeded row is not evidence of it |
| `tools/job_queue.py` | **1.0.0** new | `working/job_queue.csv`; the five condition kinds; `ready` / `fire` / `done` / `hold`; the guards — nothing fires with no private store, never into a held claim, one job per claim, and never a brief nobody can read |
| `tools/task_lint.py` | 1.1.0 → **1.2.0** | `--json`, carrying the store state because a task's status is store-dependent; `evaluate()` shared with the printed report; D8's optional `claim` column read and reported, never used to decide a status |
| `tools/check_all.sh` | 1.33.0 → **1.34.0** | the `section` helper (D5a): fifty headers printed byte-identically, per-section verdicts in `scratch/check_all_summary.json`, keyed by position as well as name. cite_check's section renamed "asserted claims" — it and the chat claims board were both headed "claims" |
| `tools/hq_snapshot.py` | **1.0.0** new | the payload for the page's db; the 7-run trend and the newly-red comparison from `working/hq_history.json` (private); refuses to write anything without the private store |
| `tools/hq_page.py` | **1.0.0** new | the page: nine bands, the start console with a brief per kind, the queue band. Carries **no data** — it renders from the db at view time, so the shell is public-safe and the page is live |
| `tools/task_register.csv` | | the `claim` column (D8); T-135 → `pipeline`, T-136 → `tools` |

**Measured during the build, and worth keeping:**

- `rc` in `check_all.sh` was read in exactly two places, so the `section` helper could reset it per
  section without touching any of the ninety-seven `rc=1` sites. The reset is the whole trick: `rc`
  is sticky, and the first instrumented run proved the point by catching **two** red sections
  (`33 records`, `37 document references`) that a snapshot-without-reset would have reported as one.
- The slowest section is `tasks` at 111 s of a ~700 s run — which is why `hq_snapshot --check` must
  never re-run the task sweep, and does not.
- `doc_lock.refuse_absent_store()` only PRINTS; it neither decides nor exits. Both new modules wrap
  it in a `need_store()` guard, which is what the first selftest run caught.

**Not built, by the plan above:** `rule_audit.py` and the findings band (phase 3, a task row and a
queued job), and the D3 refusal in `doc_lock take` (phase 4, which §11 conditions on registration
having run for a few days). The page's "Needs you" band is built and renders findings when they
exist; today it shows newly-red gate sections only.
