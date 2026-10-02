# Taking over the project — a maintainer's guide

Written 2026-10-02 for a person (not a Claude session) who inherits the Newborough Warren
groundwater study from Martin Hollingham, or who maintains it alongside him. It says what you need
to be given, how to get a working machine, what the routine is, and where the reasoning lives. It
deliberately carries no counts and no results: those live in the committed outputs and the
manifest, and they move.

`MACHINE_SETUP.md` is the detailed setup; `CLAUDE.md` is the list of traps that have each cost a
working session, written for Claude but true for anyone. Read both after this.

## 1. What the project is

Twenty-one years of monthly dipwell readings at Newborough Warren, Anglesey, analysed by a Python
pipeline (`run_analysis.py`, scripts in `src/`) into committed outputs (`outputs/`), from which a
technical report, a Methods Supplement, a Supplementary Material, papers and public summaries are
written (LibreOffice ODT documents). Every number in a document must trace to a committed output.

It lives in three stores, by kind:

| store | holds |
|---|---|
| GitHub `newbroman/Newborough_Hydrology` (public) | code, tools, outputs, markdown mirrors of every document, `DECISIONS_PUBLIC.md` |
| GitHub `newbroman/Newborough_Hydrology_working` (private) | `working/`: the decision log, changelogs, handover notes, task register, `nrg_git.sh`; also third-party data that may not be republished |
| Google Drive `NRG_documents` | the ODT documents themselves (git cannot diff a zip) |

The two git repositories share **one working tree**: the private one is a second git directory,
`.git-working`, over the same folder (`CLAUDE.md` section 4f). Plain `git` is the public one;
`./working/wgit` is the private one.

## 2. Access to transfer (a checklist)

None of this is automatic. Each item is Martin's today.

- [ ] **GitHub, public repository:** collaborator with write access, or a transfer of ownership.
- [ ] **GitHub, private repository:** the same. Without it you cannot see the decision log, the
      changelogs or the handover notes — the reasoning behind every choice.
- [ ] **Google Drive `NRG_documents`:** shared with edit rights, or moved to a shared drive.
- [ ] **The rclone Google app** used to copy ODTs to and from Drive: a Google Cloud OAuth client
      named rclone-nrg in Martin's Google Cloud project, still in *Testing* status, so its tokens
      lapse every seven days (task T-65). A new maintainer either joins that project or creates
      their own client (rclone's documentation: "Making your own client_id"), and ideally
      publishes it so the weekly lapse ends.
- [ ] **Zenodo:** the software record (concept doi:10.5281/zenodo.19567643, all versions) is created by Zenodo's GitHub
      integration from Martin's account. New versions appear automatically when a GitHub release is
      published from the repository; the integration and the record's ownership stay with the
      account that enabled them unless transferred (Zenodo's record sharing).
- [ ] **Authorship and contact:** `CITATION.cff` and `.zenodo.json` name Martin, his ORCID and a
      project contact address. Add yourself as a contributor; do not replace the author.
- [ ] **Claude (optional):** the claude.ai project "NRG rebuild" and its scheduled tasks (a
      Tuesday reminder to refresh the Drive token) are on Martin's account.

## 3. Your first day

```bash
# 1. both repositories, laid out as one tree (or: tools/cloud_setup.sh does all of this)
git clone https://github.com/newbroman/Newborough_Hydrology.git NRG && cd NRG
git clone --bare https://github.com/newbroman/Newborough_Hydrology_working.git .git-working
git --git-dir=.git-working config core.bare false
git --git-dir=.git-working --work-tree=. checkout -f HEAD -- .
cp working/.git-working/info/exclude .git-working/info/exclude
echo "/working/" >> .git/info/exclude

# 2. the machine
bash tools/nrg_env.sh --system      # sudo: git, rclone, LibreOffice, poppler; checks LibreOffice
bash tools/nrg_env.sh               # the environment; must end "the pipeline's environment"

# 3. the documents
rclone config                       # a remote named exactly "gdrive", scope 1 (full drive)
rclone copy gdrive:NRG_documents . --filter-from tools/rclone-odt-filter.txt --progress

# 4. orientation
python3 tools/session_handover.py   # the state of the tree, generated
bash tools/check_all.sh 2>&1 | tee check_all.log   # must end "check_all: OK"
```

`MACHINE_SETUP.md` explains each step and what goes wrong when one is skipped.

## 4. The routine

**Change, run, check, ship.**

1. Edit a script; bump its `__version__` with a dated changelog line in the file, and its row in
   `notes/ledgers/SCRIPT_LEDGER.md`.
2. Run what changed: `python3 run_analysis.py --step N` (N is the SCRIPT number), or the whole
   thing: `python3 run_analysis.py --full --with-supplementary`.
3. `bash tools/check_all.sh` must end `check_all: OK`. If a gate you did not touch fails, find out
   why before going on.
4. `bash working/nrg_git.sh` → option **17, Ship**: it rebuilds every derived artefact the gates
   check (PDFs, mirrors, ledgers, manifest), runs `check_all` again, pushes **both** repositories
   and archives the ODTs to Drive. A ship is two pushes; a public commit without its private
   companion is a change nobody can explain later.

Other menu options worth knowing: **4** pull both repositories (do this before starting), **12** the
documents lock, **11** archive the ODTs to Drive, **13** republish the web tools, **15** rebuild
`report.pdf` from the master document.

**Documents.** Take the lock first (option 12, or `python3 tools/doc_lock.py take --note "..."`):
the ODTs cannot be merged, and two machines editing one document lose work silently. Edit in
LibreOffice for prose and layout; scripted text edits go through `tools/odt_edit.py` only (never a
library that rewrites the XML). Versioned documents (Methods Supplement, papers, summaries) are
never edited in place: each batch saves a new `_vN` file. The ship then moves every older
version out of `docs/` into `archive/` (not public; five backups per document, every version on
Drive), so `docs/` always holds just the current documents. After an edit,
`python3 tools/refresh_mirrors.py` rebuilds the markdown mirror that the gates read.

**Every non-trivial methodological or editorial call** gets an entry in
`working/DECISION_LOG.md` (question, decision, rationale, what it retires, when to revisit), in the
same session it is made. `DECISIONS_PUBLIC.md` is generated from it.

## 5. Regular chores

| when | what |
|---|---|
| weekly, until the rclone app is published | refresh the Drive token: `rclone config reconnect gdrive:` |
| after any OS update or reinstall | `bash tools/nrg_env.sh --rebuild`; `python3 tools/env_audit.py` must still say the pipeline's environment |
| when offered a LibreOffice update | decline it, or hold it (`nrg_env.sh --system` prints the command): its version decides the bytes of every published PDF |
| at each ship | nothing extra: option 17 archives the ODTs |
| at submission of a paper | release 1.0.0 (section 6) |

**Why the environment survives an OS upgrade and LibreOffice does not.** Everything under `venv/`
— Python itself, installed by `uv`; every library, pinned in `requirements.txt`; the maths-library
settings that make two different CPUs compute the same last digit — is rebuilt identically by
`nrg_env.sh` on any Linux machine. A new Mint or Ubuntu cannot move a published *number*.
LibreOffice is an OS package: the OS chooses its version, and `artefact_lint` refuses a published
PDF whose producer is not the recorded version. If the machine's LibreOffice has moved, build PDFs
in a Claude cloud session (whose image carries the recorded version), or move the whole project to
the new version deliberately: rebuild every published PDF on it, then
`venv/bin/python tools/env_audit.py --record`, with a decision-log entry.

## 6. Releases and Zenodo

The version is `0.9.<orchestrator major>.<minor>` until a paper is submitted, then `1.0.0`
(D-228). It lives once, as `PIPELINE_VERSION` in `src/utils/config.py`, and becomes the git tag,
the GitHub release and the Zenodo version:

1. Set `PIPELINE_VERSION` and `PIPELINE_RELEASE_DATE` in `config.py` and `date-released` in
   `CITATION.cff`; run `python3 run_analysis.py --manifest-only`; ship.
2. On GitHub (https://github.com/newbroman/Newborough_Hydrology/releases/new): Choose a tag →
   type `v<version>` → "Create new tag on publish", target `main`; a title; "Generate release
   notes"; leave *pre-release* unticked; Publish. (A tag pushed from a Claude cloud session is
   refused by its git connection, which is why the form makes the tag.) Zenodo archives the
   release as a new version of the record within minutes, using `.zenodo.json` for its metadata.
3. Add the new version DOI to `CITATION.cff` `identifiers`.

Papers cite the record's *concept* DOI, 10.5281/zenodo.19567643 (all versions, always the
latest), and name the version DOI that produced their numbers: 0.9.2.23 is
10.5281/zenodo.23096072 (released 2026-10-02).

## 7. Where the knowledge lives

| question | where |
|---|---|
| why was this decided? | `working/DECISION_LOG.md` (private); `DECISIONS_PUBLIC.md` (public, generated) |
| what changed, when, by whom? | `working/changelogs/`, git history of both repositories |
| what was the last session doing, and what is owed? | `working/updates/HANDOVER_NOTE.md` (newest first); `python3 tools/session_handover.py` |
| what is still to do? | `python3 tools/task_lint.py` (the task register, each row with its own check) |
| what does each script read and write? | `PIPELINE_README.md`; `notes/ledgers/SCRIPT_LEDGER.md` |
| which output feeds which figure or table? | `notes/ledgers/FIGURE_LEDGER.md`, `PROVENANCE_LEDGER.md` |
| which record does each analysis fit? | `tools/record_basis.csv` |
| what goes wrong, and how? | `CLAUDE.md` (the traps), `MACHINE_SETUP.md` |

## 8. What is personal to Martin and must be re-created

- `working/nrg_git.sh` assumes his remotes, a credential helper stored inside each repository
  (`.git/credentials`, `.git-working/credentials`) and the rclone remote named `gdrive`. Set up
  your own credential helper; keep the remote name.
- The rclone OAuth client and its weekly lapse (section 2).
- His name, ORCID and contact address in `CITATION.cff` and `.zenodo.json`, which stay his as the
  author's.
- The claude.ai project and its instructions, if you work with Claude: the project instructions box
  restates the rules in `CLAUDE.md` and `MACHINE_SETUP.md` and must be re-created on your account.
