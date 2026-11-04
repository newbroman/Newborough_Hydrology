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
