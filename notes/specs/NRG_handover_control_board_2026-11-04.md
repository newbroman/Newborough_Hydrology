# Handover: a control board for who holds what across both repositories

**Status:** HANDOVER for a new chat. Design → Martin's sign-off → build. No code before sign-off.
**Written:** 2026-11-04, claude.ai chat session (Claude Opus 5.5), against public `main` (the
private repository was NOT attached to that session, which is the incident below).
**Claim for the build:** `tools`. The build session must attach BOTH repositories with push access
(notes/reference/SESSION_MODES.md) so it can test against the real lock.

---

## 1. Martin's request (21:18)

"Perhaps I need another tool in this project which tells me who has control of which parts of the
different repositories, the private and the public one, so that it's easier for different chats to
monitor and for me to regulate what's going on."

## 2. The incident that prompted it

The 2026-11-04 water-balance chat cloned only the public repository (a bare `git clone`, without the
D-143 bootstrap or `cloud_setup.sh`). It ran `python3 tools/work_board.py` and got:

    documents (machine lock): free
    CLAIMS
      free: doc:MS, doc:PAPER1_SI_methods, doc:Paper1, doc:Paper2, doc:PaperM, ... pipeline, tools

That is false reassurance. The lock lives in `working/DOCUMENT_LOCK.json`, in the PRIVATE repository,
which that clone did not have. "free" meant "no lock file here", while another chat was actively
working on Paper M. A session acting on that output could have taken a claim nobody else would see,
or edited a family another chat holds.

## 3. What already exists (build on it, do not replace it)

- `tools/doc_lock.py` 1.3.0: the machine lock (which machine's ODTs are current on Drive) and claims
  held by a chat (`doc:<family>`, `pipeline`, `tools`); `take`, `release`, `status`, `who PATH`,
  `claims --json`. A claim refuses `odt_edit`, `run_analysis` and scoped ships for other chats.
- `tools/work_board.py` 1.1.0: prints claims, ships waiting, uncommitted changes, held-back work;
  `--json` feeds `working/dashboard/emit_status.py`; `--gate` is advisory in `check_all`.
- `tools/ship_scope.py`: scoped ships and held-back work.
- Spec `NRG_spec_parallel_chats_2026-10-10`, D-298 (cloud default), D-299 (bridge lock name).

## 4. Gaps

1. **Absent lock reads as "free".** With no private store, `doc_lock`/`work_board` should report
   UNKNOWN and refuse `take`, not report every claim free.
2. **Freshness is invisible.** The lock is only as current as the last fetch of the private
   repository. The board does not say when that was, and does not fetch.
3. **No per-repository view.** Nothing shows, side by side, for public and private: the local HEAD
   against `origin/main`, unpushed commits, uncommitted files, and which claim covers them.
4. **Claim age.** A claim taken by a chat that has since ended stays held with no flag.
5. **Martin's view.** The board is a terminal command. Martin wants to monitor and regulate from
   wherever he is, including his phone.
6. **Session identity.** Claims name a chat by free text. Nothing ties a claim to a session link,
   so Martin cannot jump to the chat that holds it.

## 5. Requirements (proposed; Martin to confirm)

- R1. A session without the private store gets `UNKNOWN (private repository not present)` on every
  claim, and `take` refuses with the attach instructions from SESSION_MODES.md.
- R2. The board fetches both remotes (read-only, `GIT_OPTIONAL_LOCKS=0 --no-optional-locks`) before
  reporting, and prints "as of fetch HH:MM" per repository; `--no-fetch` for offline.
- R3. One table per repository: branch, local vs `origin/main` (ahead/behind), uncommitted files
  grouped by the claim that covers them, and unclaimed changes flagged.
- R4. Each claim shows holder, age and note; claims older than a configurable age are flagged STALE
  (value in config, not typed). Releasing a stale claim stays a deliberate act: never automatic.
- R5. `take` records the session link (claude.ai/code or chat URL) when the session knows it, so the
  board can show where the holder lives.
- R6. A view for Martin. Options, his decision:
  (a) a published private claude.ai artifact the board republishes on each `take`/`release`;
  (b) a JSON status file in the private repository, rendered by the existing dashboard;
  (c) a short summary line in the session-start output (`session_handover.py`).
  Constraint: claim metadata lives in the private repository and must not be copied into the public
  one.
- R7. Regulation: `doc_lock release NAME --force --by martin` stays the only override, and every
  override is logged with who and when.

## 6. Acceptance tests (in scratch directories, never against the real lock)

- Public-only clone: board says UNKNOWN; `take` refuses.
- Both repositories, lock present: board matches `doc_lock status`, with fetch times.
- A claim older than the stale age is flagged; a fresh one is not.
- Uncommitted file under a claim held by another chat: named, with the holder.
- Private repository 2 commits behind origin: shown as behind, and `take` warns to pull first.
- The bridge cases from D-299 still pass unchanged.

## 7. Who should build it

**A separate chat, claiming `tools`, in a session with both repositories attached.** It is independent
of the water-balance work, which will hold `pipeline`, and of the Paper M chat, which holds
`doc:PaperM`. Running it in parallel costs nothing and keeps each claim clean. The water-balance chat
could take it on afterwards, but it would then hold two claims for no gain.

## 8. Records the build session writes

Version bumps and inline changelogs on `doc_lock.py` and `work_board.py`; `SCRIPT_LEDGER` rows if the
ledger covers tools; a CHANGELOG_delta; a decision-log entry (the UNKNOWN-not-free rule is a behaviour
change worth a D-entry); a note in SESSION_MODES.md and CLAUDE.md §4b; the handover entry.

---

# Sign-off and design as built (2026-11-04, chat "control board", claim `tools`)

Brought onto `main` from the `notes/2026-11-04-water-balance-handovers` branch, where this handover
was written. Everything above this line is the handover as received, unedited. Below is Martin's
sign-off verbatim, the design it signed off, and what was built.

## Martin's sign-off, 2026-11-04

> Signed off, with these answers:
> 1. Refuse doc:* and warn on the rest. When NRG_NO_PRIVATE_STORE=1 is set, the board says so in its first line.
> 2. ls-remote approved, off by default in --gate/--json.
> 3. Display label approved, no new claim name.
> 4. 24 h / 72 h, but measured from last activity: odt_edit, ships and run_analysis refresh a `touched` time on the claim they pass through, and staleness is flagged from that, not from `since`.
> 5. Chat name + mode; store the link when known, never required.
> R6. Build (b) and (c), and (a) in the same pass: the phone view is the point.
> 6. --by mandatory on a forced take, defaulted to NRG_CHAT on release.
> 7. Env overrides approved; the board prints a warning whenever either is set.
> Yes, commit the design to notes/specs/ on main with this sign-off attached.

## The design, as signed off and built

**R1 — three states, not two.** `doc_lock.store_state()` returns `PRESENT` (`.git-working` resolves
*and* `working/DOCUMENT_LOCK.json` is tracked in it), `ABSENT` (no private store) or
`PRESENT_NO_LOCK` (the store is there and has no lock file yet). The third state is kept distinct
because it is what a fresh clone of **both** repositories looks like before anyone has ever locked;
a rule keyed on the lock file's absence alone would make the first-ever `take` impossible.
`ABSENT` makes every claim read `UNKNOWN`; `take` and `release` refuse, quoting this document's two
`add_repo` lines; `check_write` refuses `doc:*` and warns-but-permits `pipeline` and `tools`
(answer 1), because the ODTs are not in a public-only clone anyway while refusing everywhere would
stop a legitimate public-only cloud session running the pipeline. `NRG_NO_PRIVATE_STORE=1` declares
the intent and appears in the board's first line.

**R2 — `ls-remote`, not `fetch`** (answer 2). Measured 0.55–0.64 s per repository. It writes nothing
into `.git`: no `FETCH_HEAD`, no ref update, so no `*.lock` residue — which matters because the
bridge mount refuses `unlink` and a stray `refs/heads/main.lock` wedges the next ref update
(CLAUDE.md §4). The board runs at every session start and inside `check_all`, so it must not write
to both git directories for what it only reads. The probe compares the remote's
`refs/heads/main` to the local `refs/remotes/origin/main` and says "origin has moved since your last
fetch" with `git fetch` as the remedy. Freshness itself comes from the mtime of
`refs/remotes/origin/main`, falling back to `FETCH_HEAD`, then "unknown" — packed refs have no
per-ref mtime, and "unknown" is the honest answer there. Off by default for `--gate` and `--json`.

**R3 — one block per repository.** Branch, HEAD, ahead/behind `origin/main`, origin moved, last
fetch, and uncommitted files grouped by covering claim. The private half's files all live under
`working/`, which maps to no claim, so they carry the display **label**
`records (shared, merged row by row)` and not a claim name (answer 3) — there is nothing new for
anyone to hold. Mechanical note: every private git command passes **both** `--git-dir` and
`--work-tree` plus `--no-optional-locks`; with `--git-dir` alone, `rev-parse HEAD origin/main` is
fatal while `rev-list` quietly still works.

**R4 — staleness from ACTIVITY** (answer 4, which changed the design). `since` says only when a
claim was taken. Every write passing a claim gate now refreshes `touched` via `doc_lock.touch()`,
throttled to 60 s because `ship_scope` calls `check_write` once per path and a scoped ship would
otherwise rewrite the lock file hundreds of times in a second. `STALE_CLAIM_HOURS = 24` and
`ABANDONED_CLAIM_HOURS = 72` are module constants carrying their D-number, following
`session_handover.py`'s `TIER0_PROSE_BUDGET` — the house convention for a tunable, there being no
config-file convention to use instead (every `tools/*.json` is a baseline or state). Overridable by
`NRG_CLAIM_STALE_HOURS` / `NRG_CLAIM_ABANDONED_HOURS`. A flag never releases anything.

`odt_edit` and `ship_scope` reach `touch()` for free, both going through `check_write`.
**`run_analysis.py` does not** — its gate reads `holder_of("pipeline")` — and that one line was
deliberately not applied, because `run_analysis.py` is under the `pipeline` claim this chat did not
hold. Tracked as **T-135** with the exact line, for whichever chat holds `pipeline`.

**R5 — identity** (answer 5). A claim records `mode`, derived (`laptop` / `bridge` / whatever
`NRG_SESSION_MODE` says), and `link`, given by `--link` or `NRG_SESSION_LINK` and never required.

**R6 — all three views** (answer R6). (b) `work_board --json` carries store state, per-repository
position, staleness flags, warnings and the digest into `working/dashboard/emit_status.py` 1.2.0,
which the 06:30 snapshot already publishes. (c) `work_board --digest` is one line, printed *before*
the handover text by `session_handover.py` 2.4.0, so a session that reads no further still sees an
absent store or another chat's claim; it costs Tier 0 nothing, being printed rather than written.
(a) `tools/board_artifact.py` renders the board as a private claude.ai artifact. A script cannot
publish, so a take or release leaves `working/.board_publish_owed` and `--check` tells the next
session the page is behind — the pattern `tools/proof_copy.py` already uses. R6's constraint is
kept by construction: the rendered HTML goes to `scratch/board/` (gitignored), the published URL to
`working/.board_artifact.json` (private), and the script itself carries no data.

**R7 — regulation** (answer 6). A forced **take** is refused without `--by`, being the destructive
override that leaves another chat's unshipped work unprotected; a forced **release** defaults `--by`
to `NRG_CHAT`, a release being recoverable by retaking. Both append to
`working/claim_overrides.csv` through `register_io.write_rows`, so two chats appending merge row by
row. Append-only.

**Testing** (answer 7). `NRG_DOC_LOCK_FILE` and `NRG_REPO_ROOT` redirect the lock, and
`override_warnings()` announces either wherever the board prints — a board read from a scratch lock
that looked like the real one would be worse than no board. `python3 tools/doc_lock.py --selftest`
runs section 6 in throwaway trees; **the real lock is never read or written.** It is gated in
`check_all` 1.33.0 beside the `register_io` and `ship_scope` selftests.

## Beyond the spec, added

1. `work_board.collect()` swallows every exception and returns 0 ("the board informs; it must never
   block anything"). `UNKNOWN` had to survive that: a thrown store check must not degrade to the
   *reassuring* message, which would be the original failure again.
2. The `check_all` gate stays advisory and exits 0, so a public-only CI clone prints `UNKNOWN`
   without failing the build.
3. D-299 is untouched: `BRIDGE_HOLDER`, `MACHINE_FILE` and the bridge refusal in `acquire()` are
   unchanged, and the selftest covers both bridge cases.

## Section 8's conditional, resolved

No `SCRIPT_LEDGER` rows. `notes/ledgers/SCRIPT_LEDGER.md` is "one row per pipeline script" and
carries no `tools/` rows, so the ledger does not cover this.

## Records written

D-300; changelog `2026-11-04g`; T-135; `CLAUDE.md` §4b; `notes/reference/SESSION_MODES.md`;
version bumps and inline changelogs on `doc_lock.py` 1.4.0, `work_board.py` 1.2.0,
`board_artifact.py` 1.0.0, `session_handover.py` 2.4.0, `check_all.sh` 1.33.0,
`emit_status.py` 1.2.0; `DECISIONS_PUBLIC.md` regenerated.
