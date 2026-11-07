# Which kind of session am I in, and what can it do?

Read this before asking Martin to run anything on the L14. Most work does not need
it. CLAUDE.md §4 (bridge), §4g (cloud) and MACHINE_SETUP.md §7 carry the detail;
this page is the decision.

Written 2026-11-03 from a measured probe of a claude.ai chat session (below).
Re-measure rather than trust it: the probe commands are at the end.

## The three kinds of session

| | **claude.ai/code** cloud session | **claude.ai chat** (Cowork) cloud session | **Bridge** (desktop app, L14 folder) |
|---|---|---|---|
| How to tell | `NRG_RCLONE_CONF_B64` is set | a cloud sandbox, secret unset | `mcp__remote-devices__device_bash` present; tree under `$HOME/mnt/NRG` |
| Builds the pipeline environment | yes (`tools/cloud_setup.sh`) | yes (`tools/cloud_setup.sh`) | no (D-155) |
| Runs the pipeline / `check_all` verdict counts | yes | yes | no (`env_audit` fails by design) |
| Builds published PDFs and `report.pdf` | yes (LibreOffice is the recorded version) | yes | no |
| Pushes both repos | yes, on Martin's yes | yes, on Martin's yes (GitHub linked; attach both repos with push access) | yes, via the credential helper in the L14 tree |
| Reaches the ODTs on Drive | yes (rclone secret) | **no** | yes (they are on disk) |
| Can ship (`tools/cloud_ship.sh`, D-233) | yes | no (needs Drive) | no (`--ship` needs the environment) |

## So, by task

- **Script change, new analysis, pipeline rerun, gates, tooling** → any cloud
  session. No L14.
- **Rebuild a PDF, including `report.pdf`** → any cloud session that has the ODTs,
  i.e. claude.ai/code. A chat session has no ODTs to build from.
- **Edit an ODT (report chapters, Supplement, papers)** → claude.ai/code with the
  secret, or the bridge. Take the document lock first either way (CLAUDE.md §4b).
- **Ship** → claude.ai/code (`tools/cloud_ship.sh`) or the L14 (`nrg_git.sh --ship`).
- **Martin's eyes on a document in LibreOffice** → the L14. That is the only task
  that is his machine's by nature.

The default for a working session is therefore **claude.ai/code on the
environment that holds the secret** (D-298, confirmed by Martin 2026-11-03). A chat session is fine for code and
pipeline work; when it reaches an ODT step it hands that step on rather than
sending Martin to the L14 for the whole job.

## In a chat session, attach both repos with push access

    add_repo newbroman/Newborough_Hydrology          access=push
    add_repo newbroman/Newborough_Hydrology_working  access=push
    bash <(curl -sSL https://raw.githubusercontent.com/newbroman/Newborough_Hydrology/main/tools/cloud_setup.sh) "$HOME/NRG"

Credentials come from Martin's linked GitHub account, freshly each session. Never
ask for, accept or type a token in the conversation (CLAUDE.md §4g).

**Attaching BOTH is not optional, and since D-300 the tools say so rather than
guessing.** The claim lock lives in `working/DOCUMENT_LOCK.json`, in the private
repository. A session holding only the public one used to be told every claim was
`free` — which is how the 2026-11-04 water-balance chat came to read `doc:PaperM`
as free while another chat was editing Paper M. `doc_lock` and `work_board` now
report **UNKNOWN**, the board says so in its first line, `take` refuses with the
two lines above, and a write into a `doc:` family is refused (`pipeline` and
`tools` are warned and permitted, so a deliberately public-only session still
runs; `NRG_NO_PRIVATE_STORE=1` declares that intent). If a board says UNKNOWN,
attach the private repository — do not take a claim and hope.

## Setting the Drive secret (Martin, once; again only if a session says DRIVE TOKEN REFUSED)

On the L14:

    cd ~/projects/NRG && bash tools/drive_token.sh

A browser opens for Google's consent (answer **n** to the Shared Drive question).
The script checks the token against `NRG_documents_v2` and puts one line starting
`NRG_RCLONE_CONF_B64=` on the clipboard, never on the screen. Paste that line into
the claude.ai/code environment's environment variables (replacing any old value),
save, and start a **new** session on that environment: a running session does not
see a changed variable. `cloud_setup.sh` step 4 then reports the documents copied
and the MD5 check. Never paste the line into a chat.

## Why not the Google Drive connector?

A chat session can see `NRG_documents_v2` through the Drive connector, but it is
not a route for ODTs: a download comes back through the conversation as base64
(the chapters run to ~100 MB), and the connector can upload a new file but not
replace a file's content, which would break `working/DRIVE_MANIFEST.json` and so
every cloud ship after it. Use rclone.

## Register, whatever kind of session this is (D-301)

Compulsory, before the first claim or commit — and before it, attach BOTH repositories, because the
register is in the private half:

    python3 tools/chat_register.py register --chat "<a short name>" \
        --kind pipeline|document|tools|readonly|fieldwork \
        --claim <the one claim you will take, or omit for read-only> \
        --purpose "<one line: what this chat is for>"

Then `python3 tools/work_board.py`, then take that claim. When the work is done and the ship has
reached GitHub: `chat_register.py status --chat "<name>" --set done --outcome "<one line>"`, and
release the claim.

A chat that registers another chat's row is recorded as having done so (`registered_by`, shown as
SEEDED). That is not a reproach — seeding an existing chat's row is useful — but the row is not
evidence that chat read the rules, and the agent treats it accordingly.

**Starting a new chat?** Do it from the NRG HQ page, which writes the brief for the kind of work and
tells the new chat to register. A release also prints any queued job it made ready
(`working/job_queue.csv`) and the line that fires it: a job fires when a session is already running,
so firing it is the releasing session's last act, or HQ's next pass.

## Probe (run at the start of any session in doubt)

    echo "drive secret: ${NRG_RCLONE_CONF_B64:+set}"
    git rev-parse --abbrev-ref HEAD        # must be main before any ship - see below
    soffice --version; python3 -c 'import uno; print("uno ok")'; pandoc --version | head -1
    python3 -c "import json;print(json.load(open('tools/environment.json'))['externals']['soffice'])"
    git push --dry-run origin HEAD:refs/heads/_probe

Measured 2026-11-03 in a claude.ai chat session: secret unset; LibreOffice
24.2.7.2 (= recorded); UNO ok; pandoc 3.1.3; push dry-run accepted on the public
repo; both repos attached with push access; `cloud_setup.sh` built the full tree
and `nrg_env.sh` reported every recorded version and the BLAS pin matching; step 4
reported NOT FETCHED, as expected without the secret.

## Which branch is the tree on? (2026-11-06)

**The project ships from `main`, and a harness branch is not a route to GitHub.** An agent
harness may check the public tree out on a branch of its own — `claude/<name>`, level with
origin's `main` — and the probe's first new line is there to catch it. Every gate, mirror,
published PDF and index count in this corpus reads `main`. Until `nrg_git.sh` 1.32.0 the ship
counted its commits against origin's `main` while a bare `git push` followed the current branch's
upstream, so on a branch tracking itself the commits landed on the side branch and `Pushed.`
printed with `main` unmoved: measured 2026-11-06 in a throwaway pair of repositories, 1 commit
ahead of origin's `main` before the push and still 1 ahead after it, exit code 0 throughout.
`push_if_ahead` now refuses off `main` and names its target `origin HEAD:main`, which
`tools/cloud_ship.sh` 1.0.1 had already adopted privately on 2026-10-03 for the same reason.

So: ship from `main` (`git checkout main && git merge --ff-only <branch>`). A branch kept on
purpose — CLAUDE.md §4g's "long work goes on a branch" — is pushed by hand, never by a ship.

## `check_all` cannot go green without the ODTs

Three gates read the ODTs themselves and report STALE on a tree that has none:
`starmath_log` (EQUATION_LEDGER), `build_provenance_ledger` and `build_doc_ledger`
(measured 2026-11-03: all three read `report_edits/odt/` or `docs/**/*.odt`). So a
chat session's `check_all` ends FAIL by construction. Quote it, name those three
as the documents-only reds, and treat any OTHER red as real. The binding verdict
comes from a session that has the documents (claude.ai/code with the secret, the
bridge, or the ship itself, which regenerates them, D-213).

## The document lock from the bridge

A bridge chat takes the machine lock as the L14 (D-299): `doc_lock` reads the L14's name from
`.git/nrg_machine`. If `take` refuses because the name is missing, Martin runs
`python3 tools/doc_lock.py status` once on the L14. Archiving to Drive and releasing after it are
done on the L14. A holder shaped `rcw-…@claude` is a pre-D-299 bridge lock under the wrong name.

## After a Mint upgrade on the L14

The recorded LibreOffice is the one Ubuntu 24.04 ships, which the cloud image
also has. A newer Mint will very likely ship a different one, and from then on
the L14's published PDFs fail `artefact_lint` Check C while the cloud's pass.
Check `soffice --version` against `tools/environment.json` after the upgrade;
if they differ, build PDFs in the cloud rather than re-recording the version.

## Browser access and the L14's folder: a cloud session has neither (2026-11-07)

Martin wants future Water Watch chats to have **a browser** and **the L14's folder**, so
that a session can read a Facebook group it is writing for and run the L14's own commands.
Neither is available in a cloud session, and this section is what was measured on the day,
so it is not rediscovered. **T-183 carries the open part.**

What a session has is fixed **when it starts**. There is no tool to add either capability
mid-session, and enabling the setting in the desktop app does not reach a session already
running.

| | measured 2026-11-07 |
|---|---|
| browser tools | **absent.** `ToolSearch` by exact name (`mcp__Claude_Browser__*`, `mcp__claude-in-chrome__*`, `mcp__remote-devices__Claude_Browser__*`) and by behaviour returns nothing — and no `enable__*` tool either, so there is nothing to turn on from inside |
| after Martin enabled browser tools in the app | **unchanged** — a running session's tool surface does not grow |
| the L14's folder, before linking | `list_computer_folders` → `{"folders":[],"cannot_be_used":[]}` |
| after Martin linked `NRG` in Code settings | listed, but under **`cannot_be_used`**, `reason: not_available` — *"that computer does not offer it to cloud sessions and did not say why"* |
| after the desktop app updated | **unchanged**, same refusal |

The three causes the refusal names are a hidden directory under home, `~/Library`, or an app
needing an update. **None fits**: `~/projects/NRG` is neither, and the update changed nothing.
So the remaining explanation is the one the tool's own description gives — **serving a folder
to a cloud session is not available on every account yet**. The folder being *listed* proves
the L14's end is configured correctly; the computer simply declines the request. Do not tell
Martin to re-link it, re-update, or hunt a setting: his end is done.

**A desktop-app session can still be a CLOUD session.** This one was started from the app and
runs in a managed remote container, which is why it has neither capability while other Code
sessions in the same app have both. `list_computer_folders` returning nothing usable is the
quickest tell, and it is the same boundary in both cases: the browser and the folder both live
on Martin's side, and a container cannot reach them.

**What this does and does not cost.** It costs nothing that matters for the pipeline: a cloud
session runs the gates, the PDFs, the newsletter and both pushes. What it costs is the typing
— a cloud session must hand Martin the `git pull` and the `rclone copy` instead of running
them. That, and reading a page behind a login. For the real L14-only jobs (his eyes on a
document in LibreOffice, anything that must land on that disk) nothing has changed: they were
always his.
