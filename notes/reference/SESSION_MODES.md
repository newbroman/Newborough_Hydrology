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

## Probe (run at the start of any session in doubt)

    echo "drive secret: ${NRG_RCLONE_CONF_B64:+set}"
    soffice --version; python3 -c 'import uno; print("uno ok")'; pandoc --version | head -1
    python3 -c "import json;print(json.load(open('tools/environment.json'))['externals']['soffice'])"
    git push --dry-run origin HEAD:refs/heads/_probe

Measured 2026-11-03 in a claude.ai chat session: secret unset; LibreOffice
24.2.7.2 (= recorded); UNO ok; pandoc 3.1.3; push dry-run accepted on the public
repo; both repos attached with push access; `cloud_setup.sh` built the full tree
and `nrg_env.sh` reported every recorded version and the BLAS pin matching; step 4
reported NOT FETCHED, as expected without the secret.

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
