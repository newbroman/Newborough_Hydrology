# Draft — the coordinating chat (NRG Control)

**Status: a draft for Martin, 2026-11-07. Nothing built. Written by the Pipeline chat after
three cycles in one evening lost to generated artefacts and a claim nobody could see.**

Martin, 2026-11-07: *"This all points to needing one coordinating chat which handles the errors
and the work is needed."* And earlier the same day: *"Still waiting for another chat to finish,
surely there must be a way to queue the work so one chat isnt waiting on another."*

---

## 1. The two things that actually went wrong

Worth separating, because they need different answers.

**(a) A chat sat idle waiting for a claim.** The queue for this exists — `working/job_queue.csv`,
D-301 — and it works. Its one gap is stated in CLAUDE.md §4b: **"a job does not fire itself"**. It
fires when something is already running, so `doc_lock release` prints the jobs its release made
ready and HQ's daily pass is the backstop. Between a release and the next HQ pass, a ready job
waits on a human noticing.

**(b) Generated artefacts went stale and reds followed.** Today: the HANDOFF predated the newest
private commit (a red), and `tools/proof_bundle_state.json` was dirtied on every `check_all` run
(T-136, logged 2026-11-05, reproduced twice). Neither was a defect in the work. Both cost a cycle.

These are not the same problem and a single agent "handling the errors" conflates them.

## 2. What already covers this, so the draft does not reinvent it

- **D-301** — the chat register, the job queue, the five condition kinds, HQ's daily pass.
- **D-302** — the HQ agent **reports and never intervenes**. It releases no claim and edits
  nothing under another chat's claim.
- **T-137** — `tools/rule_audit.py`, the agent that audits the *chats*. Not built. Spec §8 lists
  its checks; spec §7 lists which findings page Martin.
- **CLAUDE.md §1 / `ship_regen_lint`** — **a red gate after a ship is a defect in the work, never
  "rebuild X and retry"; if it looks like the latter, the fix is a line in `ship_regenerate()`.**

That last one is the load-bearing rule here, and it decides most of the design below.

## 3. The recommendation

**Build the coordinator as a job runner, not an error fixer.** Its core function needs no new
grant at all, and it is the part that answers Martin's actual complaint.

### 3a. What it does — fire ready jobs (no new permission needed)

A pass over `job_queue.csv`: for every job whose conditions are met and whose claim is free, start
the chat named in its brief. That is all. Firing a job is starting a chat; it edits nothing, holds
nothing, and overrides nothing. D-302 is untouched because the coordinator is not auditing anyone.

This removes (a) entirely. The gap closes without a decision.

### 3b. What it does NOT do — fix generated artefacts ad hoc

Tempting and wrong. `ship_regen_lint` exists because "rebuild X and retry" is the failure mode:
three ships died on it on 2026-09-30 and three on 2026-09-24. A coordinator that quietly
regenerates a stale artefact and re-runs the gate **hides the missing `ship_regenerate()` line
instead of adding it**, and does so faster and more often than a human would.

So: when the coordinator finds a stale generated artefact, it does not regenerate it. It **queues
a job to add the line to `ship_regenerate()`** and names the artefact. The fault is fixed once,
in the ship, rather than papered over on every run.

Today's HANDOFF red is the test case. The right outcome was not "regenerate the HANDOFF" — it was
to ask why a private commit can leave the HANDOFF behind when `nrg_git.sh` option 2 regenerates it
before the private commit, and whether a bridge-or-cloud commit made outside option 2 should do
the same. I regenerated it by hand. That was the expedient fix, not the correct one.

### 3c. Where it may act directly

One class only, and it is already exempt: **its own records**. The job queue and the chat register
publish themselves under D-314. Nothing else.

Explicitly outside its mandate, in every case reported and never touched:
- prose, numbers, or anything bearing on a published claim (§7 — Martin's);
- any file under another chat's claim (D-302);
- a forced release of a stale or abandoned claim (D-302's own Revisit-if names this as the likely
  first intervention Martin would grant — it is not granted here);
- a push of anything but a shared record (§7).

## 4. The decision Martin has to make, if any

**On the recommendation above: none.** 3a needs no grant, 3b is a restatement of an existing rule,
3c is already D-314. The coordinator can be built under the decisions that exist.

A decision is needed only if Martin wants more than this. Two candidates, both of which widen
D-302 and so need a log entry:

- **Release a claim past the abandoned age (72 h).** D-302 anticipates this as the first likely
  grant. Note that staleness is measured from last *activity* and a flag never releases anything;
  `release --force --by NAME` is the only override and every one is logged to
  `working/claim_overrides.csv`. A coordinator doing this automatically would be the first thing in
  the project that takes work away from a chat without a human.
- **Fix an exact finding directly.** The distinguishing test from D-302's rationale is
  *exact versus inferential*: "a finding class becomes exact rather than inferential, in which case
  acting on that class alone" may be reconsidered. A gate verdict is exact. "This commit's files
  fall outside its chat's claim" is inferential. If Martin wants direct action, it should be
  granted per finding class, naming each, rather than as a general licence.

**My recommendation: build 3a, change nothing else, and see whether (b) still hurts once jobs fire
on time.** Most of today's cost was a chat waiting, not a chat unable to fix something.

## 5. Who opens the session (corrected 2026-11-07, after Martin: "Doesn't the pass run in the
background as each task finishes?")

**It does, and the first draft of this section was wrong to ask who runs the pass.** `doc_lock
release` calls `jobs_made_ready()`, which evaluates the whole queue with `promote=True` at the
moment a task finishes; `job_queue.py fire` then runs every gate — conditions met, claim free, no
other active job on that claim, a brief that exists. The pass is already at the right place.

**The wall is one step later: firing a job does not open a chat.** `fire` marks the row `fired`
and prints `>>> start the session with: Run job <id>: read <brief> and follow it` — a line for a
person to paste. Nothing in the project can create a Claude session, which is what CLAUDE.md §4b's
"a job does not fire itself" actually encodes.

So the real question is **who opens the session the pass names**, and the answer depends on where
the coordinator lives:

- **A script on the L14 cannot.** No amount of work on `job_queue.py` gets past this.
- **A cloud session can.** A claude.ai/code session has session-creating tooling
  (`create_session`) and can schedule its own wake-ups (`create_trigger`). So a coordinating chat
  is able to start the sibling chats its pass names. That is a remit decision for Martin, not a
  missing mechanism.

What a coordinator cannot escape is needing to be **awake at the moment of release**. A release by
another chat at 22:40 reaches nobody if the coordinator last ran at 06:30. That is the only place a
schedule earns its keep, and it is a standing automation on Martin's account — so it is his to
create, not a session's to set up unasked.

**Residual recommendation unchanged:** build the job runner (§3a), let it open the sessions its
pass names, and leave §3b alone. Whether it also needs a schedule is answerable only after seeing
how often a release lands with no coordinator awake.

## 6. The sweep in sections (Martin, 2026-11-07: "the coordinator should be informed of what each
chat is changing so the pass sweep can be run in sections")

**The motivating cost is real and was paid today.** T-136 and T-171 touched `tools/` only, and
this chat ran the full 50-section `check_all` twice at ~20 minutes each to learn that `tools/`
was fine. A sweep narrowed to the sections a change can actually reach would have cost a minute.

**What already exists.** The coordinator can see what each chat is changing without anyone
telling it: `work_board.py` prints the uncommitted paths in the tree and each repository's
position, `claim_for_path` maps a path to its claim, and `scratch/check_all_summary.json` (1.34.0)
carries a per-section verdict with the section's name and seconds.

**What does not exist.** Two things:

1. **A path → section map.** Nothing says which of the 50 gates a change to a given path can
   reach. This has to be written, and it is a claim about coupling that can be wrong.
2. **A selector in `check_all.sh`.** `section()` prints the header and records timing; there is no
   `--only`, no skip, and no way to ask for a subset. All 50 always run.

**The safety property that decides the design.** A sectioned sweep must never be able to stand in
for the full run. CLAUDE.md §1 and `--ship` are built on the full gate set, and a map that wrongly
says "`tools/` cannot reach the mirrors section" would hide a red exactly where no gate is looking
— the same shape as the three failures of 2026-09-01 that `artefact_lint` was written for. So:

- **the subset run is advisory, for feedback while working; the full run still gates every ship**,
  and the ship must refuse a verdict that came from a subset (the summary json should record which
  sections were asked for, so a partial verdict is self-identifying rather than trusted);
- **the map fails open, never closed.** A path matching no pattern selects ALL sections. Narrowing
  happens only where a pattern explicitly claims it is safe;
- **the map gets its own `--check` on the day it is written** (§4d: a generated artefact with no
  check rots silently — TABLE_LEDGER did). The check: every section name in the map exists in the
  summary json, and every section in the summary json is reachable from at least one pattern.

**Recommended shape.** `tools/gate_scope.py`: patterns → section names, a `--for <paths>` mode
printing the sections to run, a `--check` as above, and `NRG_ONLY_SECTIONS` honoured by
`section()` in `check_all.sh` (skipped sections recorded as `SKIPPED`, not `OK`, so a partial run
cannot read as a clean one). Both files are under `tools`, so they are the builder's to change.

**One honest caveat.** The first version of the map will be wrong somewhere, and it will be wrong
in the direction of narrowing too much, because that is the direction the author is motivated to
take. Failing open limits the damage; the ship still running everything is what makes it safe to
be wrong at all.
