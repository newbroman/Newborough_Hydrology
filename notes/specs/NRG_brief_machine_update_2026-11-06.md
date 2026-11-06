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
