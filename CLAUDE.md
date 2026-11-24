# NRG — read this before touching anything

Twenty-one years of dipwell monitoring at **Newborough Warren, Anglesey**, being
prepared for *Journal of Hydrology: Regional Studies*: two companion papers, a
technical report, a Methods Supplement and a Supplementary Material. Martin
Hollingham is the author. **This repository is public.**

`MACHINE_SETUP.md` sets the project up on a new machine (renamed from `BOOTSTRAP.md` on 2026-09-10; it collided with `working/HANDOVER_BOOTSTRAP.md`, the SESSION bootstrap). <!-- former path --> This file is the traps
and the non-negotiables — the things that have cost previous sessions hours to
rediscover. It carries no counts and no state: those live in the manifest, in
what `check_all` prints, and in the generated HANDOFF.

**Start here, every session — two lines (D-143):** (a Claude cloud session runs
`tools/cloud_setup.sh` first, which builds the tree and ends with line 2 — §4g)

1. Read `working/HANDOVER_BOOTSTRAP.md` — the Tier-0 read order, its budget,
   and `tools/context_for.py`, which surfaces the decisions that bind a file
   *at the moment you touch it*.
2. Run `python3 tools/session_handover.py` — the state of the tree, generated.
   End every session with `--write`, a dated entry (≤40 lines) at the top of
   `working/updates/HANDOVER_NOTE.md`, and `--check` green. `check_all` gates it.

**Working sessions run in the cloud by default (D-298)**: claude.ai/code on the
environment holding the Drive secret, or a claude.ai chat with both repositories
attached. **Before sending Martin to the L14 for anything, read
`notes/reference/SESSION_MODES.md`** — which kind of session this is and what it
can do. Pipeline runs, gates, PDFs and pushes all work in a cloud session; only
ODT access depends on the session holding the Drive secret.

---

## 1. The one command

```bash
python3 run_analysis.py --full --with-supplementary   # regenerate EVERYTHING
bash tools/check_all.sh                               # must end "check_all: OK"
```

**`--with-supplementary` is not optional before a commit** (D-102) — gated by `output_lag` (R01): when it
fails, re-run the script it names; never skip the check.

The gates are the sections `check_all` prints — read them from the run, never
from a list here (this file said "sixteen" while the script ran twenty-seven).
Two need explaining: **artefacts** checks an output against ITSELF — row
arithmetic, the empty artefact, and (since 2026-09-01) the PDF *Producer*. It
exists because three failures that week all sat in the gap where no gate looked.
**typed references** covers tables AND figures: `--kind figure` asks whether a
number still MEANS what it did, which `figref_lint` explicitly does not check.
Run `check_all` before you commit and quote the verdict in the message. If a
gate you did not touch starts failing, stop and find out why before proceeding.

`bash working/nrg_git.sh` is the front door for committing and pushing: **2)** pushes
both repositories, **11)** archives the ODTs to Drive, **q** quits.

**`--ship` rebuilds every derived artefact the gates check BEFORE running them** (D-213), so a red gate after a
ship is a defect in the work, never "rebuild X and retry" — gated by `ship_regen_lint` (R66): the fix is a line
in `ship_regenerate()`. A ship also refuses when the local branch has diverged from GitHub.

## 2. The three stores

| store | holds |
|---|---|
| this repository, **public** | code, tools, markdown mirrors, `DECISIONS_PUBLIC.md` |
| `Newborough_Hydrology_working`, **private** | `DECISION_LOG.md`, `changelogs/`, `updates/` (was `Updates_required/`), `WORK_REGISTER.md` (a signpost; the live register is `updates/NRG_WORK_REGISTER.md`), and this repo's own tooling |  <!-- former path -->
| `gdrivefile:NRG_documents_v2` | the ODTs themselves (git cannot diff a zip); `tools/drive_pull.sh` brings them down |

Two git directories over **one** working tree. `./working/wgit` is the private one;
plain `git` always means the public one. That asymmetry is deliberate — the
mistake you want is forgetting to commit privately, not publishing by accident.

**Never `wgit add -A`.** It would sweep the public repository into the private
one. `push_working()` stages explicit paths and refuses any file that is also
tracked publicly.

## 3. Rules that are not negotiable

- **Never rewrite a dated record.** `changelogs/`, `DECISION_LOG.md` and
  anything with a date in its name state what was true then. Correct them by
  appending, never by editing. A superseded value gets a banner, not a
  substitution.
- **The decision log is private.** `DECISIONS_PUBLIC.md` is *generated* from it
  by `tools/build_public_decisions.py`, keeping D-numbers. Regenerate both
  together; `check_all` verifies it.
- **No Pye & Blott figure.** Martin does not own it.
- **ODTs are edited only through `tools/odt_edit.py`.** Never odfpy for writing —
  its round-trip drops namespace declarations and produces a file LibreOffice
  will not open. `odt_edit` gives counted substitutions and four guards. After
  any edit, open the result in headless LibreOffice and read the passage back.
- **One document family is live at a time; the rest are numbers-only (D-144).**
  `tools/doc_tier.csv` says which. `odt_edit` refuses a prose write to a frozen
  document unless `odt_edit.REASON` (or `ODT_EDIT_REASON`) names the D-number or
  changelog id that requires it; tables, references, versions and symbols go
  through their own tools and are exempt. Numbers always regenerate. A sentence
  in a frozen document changes now only if a gate is red; otherwise it waits for
  the next phase's refresh pass. The Methods Supplement follows the pipeline by
  refusal: `run_analysis.py` will not register a step without a Supplement chapter
  heading naming it and a `SCRIPT_LEDGER` row (`tools/ms_chapters.py`).
- **ODTs are versioned.** Edit `Doc_v1_9_46.odt` → write `Doc_v1_9_47.odt`.
  Mirrors follow the highest version automatically.
- **Mirrors need pandoc ≥ 3.0** and are byte-reproducible on 3.1.3.
- **No pipeline script silences its warnings**: silence one individually, by message and module, with the
  reason beside it (D-155; T-81's check keeps the category-wide count at zero).
- **Do not send a reader to the Methods Supplement.** Say the thing, or name
  the script that does it. A cross-reference is a promise that the other
  document says what you think it says, and this corpus has repeatedly not.
  Applies to the Supplement referring to itself by chapter as well.
- **A 0.01 difference at the quoted precision is acceptable — do not churn the
  corpus over it** (Martin, 2026-09-02). Two-decimal renderings sit near
  rounding boundaries and a rerun can flip the last digit without anything
  being wrong: `ANCOVA_FarField_Impact_s_coast` went -1.5049 -> -1.5083 on the
  PE/PW run, moving the published digit from -1.50 to -1.51 and back again in
  one day. Fix a number when it MOVES, not when it rounds differently. This
  does not license quoting a stale value: a change larger than that at the
  quoted precision is still a correction.
- **`export_master_pdf.py` exports JPEG at quality 80 because that is what
  Martin does by hand.** It used LibreOffice's default of 90 until 2026-09-02,
  which is the whole of W126's "+27% larger than published" — not the
  LibreOffice version it was blamed on. If a rebuilt `report.pdf` is suddenly
  much bigger, check `PDF_FILTER_DATA["Quality"]` before the toolchain.

## 4. Environment traps that have each cost a session

The bridge VM's history — what `device_bash` is and is not, the mount that refuses `unlink`, pandoc on the
VM, the PDF that came from the wrong LibreOffice, `soffice` orphans, the bridge-vs-pipeline boundary (D-155,
D-227) — is in **`notes/reference/BRIDGE_ENVIRONMENT.md`** (moved verbatim 2026-11-24, D-330). Read it before
any bridge session. What still binds every session, in one line each:

- **The pipeline and every published PDF come from a built environment** (`tools/nrg_env.sh`: the laptop or
  a cloud session), never the bridge — gated by `env_audit` and `artefact_lint` (R15).
- **Over the bridge: `source tools/bridge_py.sh` first; sweep git locks with `mv … .stale.$$`, never `rm`;
  `pgrep -x soffice.bin`, never `-f`.** The reasons are in the reference note.
- **`device_commit_files` re-encodes binaries** — gzip first and check the sha256 against provenance.
- **Don't hand Martin what the session can run.** Run it, `tee` it into `scratch/`, read the file.
- **Show progress** on anything long handed to him: `console_utils.track()` / `progress()`.

## 4b. Two machines at once

Both git repositories merge, so code, tools, the decision log and the changelogs
are safe to work on from two machines simultaneously.

**The ODTs are not.** `rclone copy` is one-way with no conflict detection, and a
zip has nothing to merge. Worse: **the mirrors are committed and the ODTs are
not**, so a machine holding a stale ODT regenerates the mirror from it and
pushes a reversion of someone else's prose. `refresh_mirrors --check` compares CONTENT
(since 1.3.0, 2026-09-08), but against the ODT on THIS disk, so a stale ODT yields a self-consistent stale
mirror and reads green; `nrg_git.sh`'s mirror source guard and `cloud_ship`'s `--verify` against Drive catch it.

`tools/doc_lock.py` makes that a refusal instead. `nrg_git.sh` **12)** takes and
releases; **11)** will not archive while another machine holds it; **2)** warns
if documents changed here without it. The lock lives in the private repo, so it
is only as current as the last fetch — it is a handover protocol between one
person's machines, not a mutex.

Never run `refresh_mirrors.py` on a machine whose ODTs you have not just pulled.

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
a new emit asks the `pipeline` holder.

## 4d. What the gates do not catch (2026-09-20)

- **`reference_lint` cannot see a reference that moved TWICE.** It checks
  references against captions, and a double-moved reference still points at a
  caption that exists. Twelve went undetected. Only `ref_audit` saw any, and
  only the 4 that name a script output. **Run `tools/repoint_verify.py` after a
  repoint pass and before any hand repair.**
- **The renumber recipe lost a step**: plan pass → `figure_map.py` →
  `repoint_verify` → `reference_lint --snapshot` → `ref_audit`. No separate
  `--abbrev-only` pass — since repoint_refs 1.6.0 the default pattern already
  matches `Fig N`, and 1.6.1 now refuses the flag.
- **Every generated artefact gets its `--check` in `check_all` on the day it is written** (R22).
- **A new caption's sequence field reads "Table 0"** in the ODT's cached text and
  the mirror until LibreOffice recalculates it: Tools ▸ Update ▸ Fields → save →
  `refresh_mirrors` → `reference_lint --snapshot`. And **`pdftotext` is not a
  witness** to field numbering — it reported a duplicate and a gap in a correct
  document.
- **Running one script standalone breaks `pipeline_lint --check runid`** —
  `pipeline_site_observations.csv` is run-scoped. The remedy is a full
  `run_analysis.py --full --with-supplementary`.

## 4e. The ledgers are keyed by OUTPUT FILE (2026-09-20)

`PROVENANCE_LEDGER.md` and `VALUE_REGISTER.md` answer *this script's output changed — what has to be re-read?*
**A table cannot have no CSV** (Martin) — gated by `table_provenance_lint` (R23). All <!--PL:report_tables-->33<!--/PL:report_tables--> report tables trace to an output.

**When auditing references, relate them to the CSV.** The report, Paper 1 and
Paper 2 each number tables from 1. Prose similarity left 150 of 211 references
unresolved; the CSV link left none. Registry rows are parsed field by field and
prose is scoped to the sentence — a character window reaches into the
neighbouring table's caption. A *reference* has no CSV: it names a table, and
the table carries the provenance.

## 4f. A ship is TWO pushes (2026-09-20)

`working/` is **not untracked**. It is tracked by a second repository —
`.git-working` → `Newborough_Hydrology_working` — and each repo excludes the
other's half. `.git/info/exclude` explains why it is done there and not in
`.gitignore`. **Do not "fix" that exclude**: deleting it sweeps 676 MB of the
private half into the public repo and publishes material kept out of it
deliberately.

The public repo carries code, tools and mirrors. The working repo carries the
reasoning that explains them — changelogs, the decision log, the handover note,
the register. **A public commit without its working commit is a change nobody
can account for later.** On 2026-09-20 `.git-working` was found three shipping
cycles behind: 19f, 20a and 20b had shipped publicly while the records
explaining them sat on one machine, which is exactly the crash exposure the two
repositories exist to prevent.

`working/nrg_git.sh` does both on the publishing machine. A bridge session
cannot run it, so:

    git push
    ./working/wgit add -A working/
    ./working/wgit commit -F - <<'MSG' … MSG
    ./working/wgit push

**Commit the private half through `./working/wgit`, not a bare `git --git-dir=.git-working`** (J-7,
2026-11-12): `wgit commit` regenerates the HANDOFF and stages it into the same commit, so `records`
stays green afterwards. A bare commit leaves the HANDOFF behind and the next `check_all` is red.

## 4g. Claude cloud sessions (D-227, 2026-10-02)

A cloud session is a full machine for this project: it can run the pipeline, build
PDFs and ship. Start it with

    curl -sSL https://raw.githubusercontent.com/newbroman/Newborough_Hydrology/main/tools/cloud_setup.sh | bash

which clones the public repository as the working tree, puts the private one at
`.git-working` over the same tree (§4f), builds the environment, copies the ODTs
down from Drive if the session has the `NRG_RCLONE_CONF` secret, shows the doc lock
and runs the session handover. Without the secret, the session works from the
committed mirrors and does not edit ODTs.

- **Never ask for, accept or type a credential in the conversation.** The Drive
  token reaches a session only as the `NRG_RCLONE_CONF_B64` environment secret
  (the `[gdrivefile]` section, written by `tools/drive_token.sh`), set by Martin.
  Its rclone client is published with the `drive.file` scope only (2026-10-02), so
  the weekly lapse (T-65) is over; `cloud_setup.sh` shouts when a supplied token is
  refused.
- **A cloud ship (D-233) is `tools/cloud_ship.sh`, run in a claude.ai/code session** on the environment
  that holds the secret — never from a Cowork chat, whose built-in `cloud_default` environment carries no
  custom variables. It refuses unless Drive matches the Drive manifest that every archive writes into
  `working/` (since nrg_git.sh 1.26.0), no mirror is ahead of
  Drive, outputs are current and the doc lock is free; afterwards the L14 runs `tools/drive_pull.sh`
  before editing (the lock note says so).
- **A claude.ai chat (Cowork) session is a cloud session too, minus the ODTs**
  (measured 2026-11-03, `notes/reference/SESSION_MODES.md`). Attach both repositories
  with push access through the linked GitHub account, run `cloud_setup.sh`, and it
  runs the pipeline, the gates and the PDF tools and pushes both repositories. It
  cannot reach Drive, so an ODT step in such a session is handed on to a
  claude.ai/code session or the bridge, not the whole job to the L14. The Google
  Drive connector is not a route for ODTs: it returns files through the
  conversation and cannot replace one in place.
- **Pushing is still Martin's call each time** (§7). A cloud session commits, shows
  the commit, and pushes on his yes; long work goes on a branch.
- **THE PROJECT'S BRANCH IS `main`, AND A SESSION CHECKS WHICH BRANCH IT IS ON BEFORE
  SHIPPING.** An agent harness may check the public tree out on a branch of its own
  (`claude/<name>`), level with origin's `main`. That is not a route to GitHub: every
  gate, mirror, published PDF and index count in this corpus reads `main`, and
  until `nrg_git.sh` 1.32.0 the ship counted its commits against origin's `main` while a bare
  `git push` followed the current branch's upstream — so on a branch tracking itself
  the work went to the side branch and `Pushed.` printed with `main` unmoved
  (measured 2026-11-06: 1 commit ahead before the push, still 1 ahead after it).
  `push_if_ahead` now **refuses** off `main` and names its target `origin HEAD:main`,
  as `tools/cloud_ship.sh` 1.0.1 already did privately. Ship from `main`
  (`git checkout main && git merge --ff-only <branch>`); a branch kept on purpose is
  pushed by hand, never by a ship.
- **Unlike the bridge, a cloud process survives between tool calls**, so long runs
  (a full `--full --with-supplementary`, the film, a full `cite_check`) go in the
  background with their log tee'd to a file the session reads.
- **Third-party data that is not in either repository** stops a cloud run quietly:
  Script 26's EbF pass needs `data/Ecohydrology_dataset.xlsx`, which lives in the
  private repository for that reason. A new external input goes there too.

## 4h. GitHub size (D-257, 2026-10-11)

**gh-pages is one commit with no history** — `publish_pages` replaces it and force-pushes. Publish
only through `nrg_git.sh` 13); a hand-built gh-pages commit hung off the previous one brings the
history back. **Superseded binaries are stripped from history** by `tools/slim_history.sh` when
GitHub passes the D-257 thresholds; text history and every commit stay. After a slim, an older
clone must run `bash tools/slim_history.sh --resync` before it pulls — `nrg_git.sh` refuses until
it has, because a plain `git pull` would merge the old history back. A clone too old to have the
script fetches it without pulling: `git fetch -q origin && git show origin/main:tools/slim_history.sh
> /tmp/slim_history.sh && bash /tmp/slim_history.sh --resync` (1.1.0 handles a clone that was behind,
saving any uncommitted edits to `~/NRG_resync_saved_<date>/` first). A commit hash quoted in a dated
record from before a slim is translated by `notes/history_maps/` (public) or `working/history_maps/`
(private). Regenerable caches under `working/` are listed once, in `.gitignore`'s `private-repo
caches` block; never force-add them.

## 5. Where numbers come from

**The committed CSVs under `outputs/` are the truth.** Documents quote them;
`citation_index.csv` records where.

**`citation_index.csv` is known to mispoint inside tables.** It locates a
citation by value plus surrounding characters, and in a corpus dense with wide
tables and confidence intervals it repeatedly latched onto a neighbouring cell —
a different well's Δβ₂, a CI upper bound, a Durbin–Watson statistic. On
2026-08-25 all 27 rows `cite_check` reported as drifted were mispointings and
every document was current. **Before believing a DRIFTED report, find the
occurrence, read its table header, and confirm the number is the quantity the
key names.** `repoint_index.py`'s refusals are usually right; do not work around
them.

## 6. What is outstanding

`python3 tools/task_lint.py` — the register. A task has no stored status; each
row carries a check command and its expected output, so the list cannot rot. An
open task never fails the gate; a *broken check* does.

`tools/docref_lint.py` holds a frozen inventory of documents cited by live source
that do not exist. Four were recovered from Martin's Drive store; the rest were
written beside the project and never in it.

## 7. What needs Martin

Prose judgement in the ODTs, anything that changes a
published claim rather than a stale value, pushing, and any decision that would
add a new entry to the decision log. Everything else — audits, tooling, mirrors,
value corrections, the Methods Supplement and Supplementary Material — he has
asked to be done and then reported, not asked about first.

**Git: run it, but ASK BEFORE EVERY PUSH (2026-09-01, his instruction).**
Check the branch first: the project ships from `main` and the ship refuses
elsewhere (§4g). **One exemption, D-314: `doc_lock` pushes the lock record itself,
because a claim nobody can see is not a claim (§4b).**
Commits over the bridge are fine — sweep the lock residue after each one. Pushing
is his call each time, so show the command and wait. He may or may not have a
credential helper populated; if not, hand him the one line.

**Never build a published PDF or run the pipeline over the bridge** — different
LibreOffice, different Python, missing libraries. Read, search, edit text, run
the text-only linters; anything that produces a published artefact runs where the
environment is built: the laptop, or a cloud session (D-227).

Show your working. He checks.
