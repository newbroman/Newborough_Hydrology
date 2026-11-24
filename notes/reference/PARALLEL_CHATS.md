# Parallel chats, the claims, HQ and the queue — moved out of CLAUDE.md §4b (D-330, 2026-11-24)

These paragraphs stood in `CLAUDE.md` §4b until 2026-11-24 and were moved here **verbatim** under D-330 ("CLAUDE.md
holds what no gate can"), closing T-206: the file had grown back past its 420-line threshold with that day's D-340
and review-page additions, and Martin chose this block to move (2026-11-24: "move the 4b detail"). Nothing was
deleted. The digest of what still binds every session stays in CLAUDE.md §4b, and references elsewhere to
"CLAUDE.md §4b" for claims, registration, the queue, HQ, the board or the ship request now mean this file as
well. Revisit-if (D-330): a session breaks a rule *because* its history moved out.

---

**A bridge session takes the machine lock under the L14's own name (D-299, introduced in doc_lock 1.5.0).** The bridge
edits the L14's files, so for the documents it is the L14. Before 1.3.0 it locked as the VM's
`rcw-<session>@claude`, the L14 saw that as another machine, and every archive refused from 2026-10-26
to 2026-11-03 while Drive fell a week behind. Now the L14 records its name in `.git/nrg_machine` on every
`doc_lock` call, the bridge reads it, and `take` on the bridge refuses if it is missing. The archive and
the release after it stay the L14's (the bridge has no rclone config).

**Several chats in one tree (2026-10-10, spec `NRG_spec_parallel_chats_2026-10-10`).** The
lock above is per MACHINE. Chats sharing the L14's tree each CLAIM what they work on — `doc:<family>`
(`doc:report`, `doc:PaperM`, `doc:summaries`…), `pipeline` (src, outputs, data, run_analysis) or
`tools` (tools/*.py, *.sh). The CSV registers in `tools/` are shared and merged row by row
(`tools/register_io.py`), never claimed.

    python3 tools/work_board.py                                      # who holds what; what is uncommitted
    python3 tools/hq_page.py --check                                  # is Martin's HQ page behind? (D-301)
    python3 tools/chat_register.py register --chat "Paper M" --kind document --claim doc:PaperM \
        --purpose "v1_9 read-through"                                 # COMPULSORY, before any claim (D-301)
    python3 tools/doc_lock.py take doc:PaperM --chat "Paper M" --note "v1_9 read-through"
    export NRG_CHAT="Paper M"                                         # in EVERY shell call over the bridge
    python3 tools/doc_lock.py release doc:PaperM --chat "Paper M"    # after the ship reaches GitHub

A claim held by another chat refuses `odt_edit` writes into its documents and `run_analysis.py`
while `pipeline` is held. An unclaimed area refuses nothing.

**A CLAIM IS NOT A CLAIM UNTIL GITHUB HAS IT, and since D-314 `doc_lock` sees to that itself.**
`take` and `release` commit and push the lock record at once, and apply the change on top of
ORIGIN's record rather than merging into it. **A lock push is exempt from "ask before every push"
(§7): it publishes no code, no prose and no numbers, only "chat X holds Y".** Before D-314 the whole
mechanism was a printed reminder to commit and push, and on 2026-11-06 it failed three times in one
evening — one take and two releases that reached only the tree that made them, blocking other chats
for hours. **Each looked like a lock failure and none was**: the lock reported what GitHub held. A
claim that cannot be published is still taken locally and says `LOCAL ONLY`; believe that line.
`NRG_NO_LOCK_PUSH=1` turns the push off. **Widened the same day to every shared record** (Martin:
*"to all shared records locks should be automatic"*): `chat_register.csv` and `job_queue.csv` publish
themselves too — but without the rebase-on-origin the lock gets, because they are CSVs that
`register_io` merges row by row, while the lock is one json document with no merge.

**EVERY CHAT REGISTERS ITSELF, AND THE QUEUE PASSES THE WORK ON (D-301, 2026-11-05).** NRG HQ is a
private page that answers "who is working on this, what does the tree look like, and what is
owed" — the landing page for every chat. Three things it adds that bind a session:

- **Registration is compulsory** and happens BEFORE the first claim or commit, in
  `working/chat_register.csv` (private, merged row by row). `doc_lock take` warns a chat that is not
  there; `doc_lock.REGISTRATION_REQUIRED` turns that into a refusal, and flipping it is the whole of
  T-138. A row written for ANOTHER chat is marked **SEEDED** and is not evidence that chat read the
  rule. Set your status when you finish: `chat_register.py status --chat NAME --set done --outcome "…"`.
- **`working/job_queue.csv` is the queue.** A job carries a brief FILE (never a prompt inline), a
  claim, and conditions of five kinds (`claim_free:`, `job_done:`, `on_main:`, `task_done:`,
  `held_by_martin`). **A job does not fire itself**: it fires when something is already running, so
  `doc_lock release` prints the jobs its release made ready and the line that fires each, and HQ's
  daily pass is the backstop. Nothing fires without the private store, into a held claim, behind
  another active job for the same claim, or with a brief nobody can read.
- **`check_all` now says which section went red** — `scratch/check_all_summary.json` (1.34.0). Read
  that instead of grepping the log for "FAIL". `tools/hq_snapshot.py` gathers the board, the tasks,
  that summary and the queue into one payload; a SESSION writes it to the page's store, because a
  script cannot. A run without the private store writes **nothing** and says so (D-302).

The agent that audits the chats (`rule_audit`, spec §8) is **not built yet** — T-137, which carries
the list of checks. HQ
reports the state of the tree today, not yet the conduct of the chats. It reports and never
intervenes: it releases no claim and edits nothing under another chat's claim (D-302).

**A board that cannot read the lock says UNKNOWN, not free (D-300).** The lock is in the PRIVATE
repository, so a session holding only the public one can see nothing — and until 2026-11-04 it was
told every claim was free, which is how a chat read `doc:PaperM` as free while another chat was
editing Paper M. Attach both repositories (§4g, `notes/reference/SESSION_MODES.md`). Without them
`take` refuses and a write into a `doc:` family is refused; `pipeline` and `tools` warn and permit.
**Staleness is measured from a claim's last ACTIVITY, not from when it was taken** — anything
passing a claim gate refreshes it — so a chat working all evening is never flagged, and a flag
(STALE 24 h, ABANDONED 72 h) never releases anything: `release --force --by NAME` is the only
override and every one is logged to `working/claim_overrides.csv`. Martin's own view of the board is
a private artifact (`tools/board_artifact.py`), the 06:30 dashboard, and the one-line digest that
opens every session handover. **A ship request names the chat, its
claims and any other paths it carries** —
`{"id","requested_at","requested_by","message","chat","claims":[…],"paths":[…]}` — and
`nrg_git.sh --ship` (1.29.0) parks every other chat's changed files in `.ship_hold/<id>/` before the
regenerate step, ships, and puts them back before the Drive archive (`tools/ship_scope.py`). A
family another chat holds with a NEW version file is parked too; one whose shipped file itself was
edited (the report chapters, the public summaries) STOPS the ship with the holder's name — ship
after that chat, or from one chat holding both claims. A request with no chat or claims is refused
while anyone holds a claim; `nrg_git.sh --ship-all` is Martin's, by hand. A document chat that needs
a new emit asks the `pipeline` holder. **A ship commits only what it can explain (D-339)**: anything not under a
declared claim or derived must be in `paths`, and a changed `tools/*.csv` register not named there STOPS the ship.
