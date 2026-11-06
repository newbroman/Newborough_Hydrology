# Brief — one safe way to bring a machine up to date

*Raised by Martin, 2026-11-06: "this so fraught with errors I could easily mess up, we need to
write a handover to the control board chat to fix this". Written by the `Fieldwork Oct 2026`
chat, which caused the confusion. Claim: `tools`.*

## What happened

Asked how to update the L14 after a cloud session had pushed, a session (this one) handed Martin
two raw `git pull` commands plus a **conditional**: *"the last history slim was 2026-10-11; if
your clone hasn't pulled since then, a plain `git pull` would merge the old history back, so run
`slim_history.sh --resync` first."* Martin's reply is the whole defect: **he has no way to tell
which case he is in, and the consequence of getting it wrong is putting a slimmed history back
on GitHub.**

## The part that is already solved, and was not used

`nrg_git.sh` option **4) Pull** already runs `slim_guard()` (nrg_git.sh:598-619). It fetches,
tests `merge-base HEAD origin/main`, counts `rev-list origin/main..HEAD`, and refuses above
`SLIM_GUARD_AHEAD=100` with the exact message and the exact remedy:

> the public repository here has N commits GitHub does not — its history was slimmed (D-257).
> This clone still holds the old history. Pulling or pushing now would put it back.
> Adopt GitHub's history first: `bash tools/slim_history.sh --resync`

**So the judgement was never Martin's to make. The tool makes it.** The error was a session
routing him around the front door to raw git. That is the first thing to fix, and it is a rule,
not code: **a session must never hand Martin a bare `git pull` for this project.**

## What is NOT solved, and is the real work

Bringing a machine up to date after a cloud session currently takes **four different mechanisms**,
and only the first is guarded:

| what | how, today |
|---|---|
| public + private repositories | `nrg_git.sh` 4), guarded |
| the ODTs | `tools/drive_pull.sh`, separately |
| the workbook (`Newborough_well_records*.ods`) | not in either repo; by hand from Drive |
| anything gitignored a cloud session produced — e.g. `living/output/` | **no route at all** |

The last row is what prompted this. The October Water Watch set (9 files, 8.9 MB) existed only in
a cloud container; `living/output/` is gitignored (`.gitignore:54`), so no pull would ever bring
it. It was moved by hand: `rclone copy` into
`01 Projects/Newborough research/water_watch_2026-10`, then a `rclone copy` back on the L14.
That worked, and nothing records that it is the route.

## What to build

**One option — "Update this machine" — that leaves the user no decision to make.** It should:

1. Pull both repositories **through the existing `slim_guard`**, so the resync case is detected,
   not guessed. If the guard fires, print its remedy and stop — do not half-update.
2. Run `tools/drive_pull.sh` when rclone is configured; say plainly when it is not, and that the
   ODTs are therefore untouched.
3. Report **what moved and what it could not bring**: commits pulled per repository, ODTs
   refreshed, and an explicit line for the gitignored outputs it cannot fetch.
4. Never require the operator to evaluate a precondition. If a judgement is needed, the tool makes
   it and says what it concluded.

**And decide the gitignored-output route** (this is a design question, not a coding one, so it
wants Martin's word): either a documented Drive hand-off folder per month that
`living/MONTHLY_ROUTINE.md` names and the update option offers to fetch, or the report is simply
always generated on the machine that will publish it — in which case a cloud session should say so
instead of generating one. Note the PDF already forces this: `reportlab` is absent from the pinned
venv (D-227), so a cloud session cannot produce the newsletter PDF at all.

## Checks this should carry

- A check that `nrg_git.sh`'s pull path still calls `slim_guard` for BOTH repositories — the guard
  is the whole safety property and nothing asserts it today.
- A check that the update option reports the gitignored-output gap rather than silently omitting it.

## Not in scope

Changing `slim_history.sh` itself. Its `--resync` is careful (saves unpushed commits as patches,
saves uncommitted tracked files, refuses rather than destroys) and nothing here suggests it is
wrong. The fault is in how a user is routed to it.

---

## Correction appended 2026-11-06, after the control board chat answered it

The control board chat — running in the L14's own tree — read this brief and corrected it on
three counts. All three are accepted; the text above stands as written and is superseded here.

### 1. The framing was wrong: "update the L14" is not a handover

The control board IS on the ThinkPad. So updating that clone is a job *inside* that session, not
something to hand to it. It ran the update while this brief was still unpushed: **no resync was
needed**, both repositories fast-forwarded cleanly, and the oldest commit reachable there is
`253d0b13` dated 2026-06-21 — older than the 2026-10-11 slim, so the clone was already on
GitHub's post-slim history.

**So the caveat was redundant twice over**, and the second way is the one worth keeping: option 4
makes the judgement anyway, *and the condition did not hold*. The correction this brief already
records (never hand over a bare `git pull`) stopped one step short — it should also have asked
**whether the condition was live at all**. The evidence was in hand: the laptop chats had been
pushing all day, so that clone was necessarily current. A session that cannot check a
precondition should say which observation would settle it, not pass the doubt along.

### 2. The newsletter-PDF premise was false, and the real defect is the toolchain

This brief argued the routing question partly on "a cloud session cannot produce the newsletter
PDF at all". **It can.** `reportlab` installed to a directory on `PYTHONPATH`, outside the pinned
venv, produced it within the hour; the nine other outputs were byte-identical to the run without
it, so nothing drifted. That argument is withdrawn.

The control board names the actual defect: **the newsletter PDF is built today by a route outside
the environment pin and outside the Producer gate.** Measured here:

| | Producer | pages | bytes |
|---|---|---|---|
| reportlab (today's route) | `ReportLab PDF Library - (opensource)` | 5 | 8,072,969 |
| LibreOffice, from the ODT the engine already writes | **`LibreOffice 24.2`** | 5 | **1,727,955** |

`artefact_lint` Check C compares each manifest PDF's `/Producer` major.minor against
`externals.soffice`, which is `24.2.7.2`. `reportlab` appears in **neither** `requirements.txt`
**nor** `tools/environment.json`. So a reportlab-built newsletter entering the published corpus
would **fail Check C**, and committing the newsletter is therefore *not independent* of the
toolchain decision — it requires it first.

**On the measurements, the LibreOffice route wins on every axis**: it passes the existing gate
unchanged, needs no new dependency, uses the `.odt` the engine already writes beside the PDF, and
is 4.7x smaller — which matters for a committed artefact under D-257's thresholds. Recommended
over adding `reportlab` to the pin, though the ruling is Martin's.

### 3. The design question is answered better than either option offered

Neither of this brief's two options. **Split by what each artefact is:**

- **The accumulated `living/output/` maps are regenerable intermediate** (96 MB even in this fresh
  container; more in the L14 tree). Do not commit them, and **do not build a monthly Drive
  hand-off folder for them either** — nothing needs handing off, because they regenerate where
  they are needed. A documented manual hand-off with no gate is the shape of the hand-edited
  `PDF_MANIFEST.txt` that kept a foreign PDF in the published corpus for three days.
- **The newsletter is a published artefact and it is small.** It belongs where this corpus keeps
  published artefacts — committed, under `PDF_MANIFEST.txt` and Check C — not in gitignored
  `living/output/`. Put it there and the pull brings it, and **the fourth unguarded mechanism
  stops existing** rather than needing a route invented for it.

That is strictly better than the Drive hand-off this brief proposed, and it retires that proposal.
Note the ordering it implies: the toolchain decision in §2 comes first, because committing a
reportlab-built PDF would fail the gate on arrival.

**Still worth building**, for the two mechanisms that are real: one "Update this machine" that
pulls both repositories through the existing guard and runs `drive_pull.sh`. Once the newsletter
is committed, the workbook on Drive is the only genuine residue.

### 4. A second rule for CLAUDE.md §4b — shared records are owned by their tools

Three chats hit the same fault tonight: the Pipeline chat hit the shared-record merge conflict and
aborted, this chat hit it and resolved it (private `d92749f`, "six conflicts, both sides' records
kept"), and the control board caused the mirror image by releasing a claim after a push. **One
cause:** `DOCUMENT_LOCK.json`, `chat_register.csv` and the markers are owned by their tools at
both ends, and **a chat's commit should carry them only when a tool wrote them in that session.**

This chat's own evidence for it: resolving `DOCUMENT_LOCK.json` by taking `origin/main`'s version
silently **erased this chat's own `pipeline` claim**, with nothing to say so. The control board
will write this rule and the no-bare-`git pull` rule into §4b when `tools` frees up; recorded here
so the evidence sits with the job.
