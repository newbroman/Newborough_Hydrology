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

## 5. Open question I could not answer from the tree

Who runs the pass? HQ's daily pass is a session Martin starts. A coordinator that fires jobs is
only as prompt as its own trigger, so a queue runner that wakes once a day has not removed the
wait, only shortened it. A scheduled task would, but that is a standing automation on Martin's
account and outside anything this chat should set up. **This is the part of the design I do not
have an answer for, and it determines whether 3a is worth building at all.**
