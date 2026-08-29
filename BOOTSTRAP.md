# Setting the project up on a new machine

Rewritten 2026-08-27, after the directory restructure and after an audit found
the environment section wrong in a way that mattered. If you are standing this up
somewhere new, read §1 properly — it is the part that used to be wrong.

The project lives in three stores, split by what each thing is rather than where
it came from. Reconstructing it means fetching all three.

| store | holds | why there |
|---|---|---|
| this repository, public | code, tools, markdown mirrors, `DECISIONS_PUBLIC.md` | text that wants diffing and history |
| `Newborough_Hydrology_working`, **private** | everything under `working/` — the decision log, changelogs, work register, working notes, and `nrg_git.sh` | text, but the deliberation rather than the conclusions |
| `gdrive:NRG_documents` | the ODT documents themselves | zips: git cannot diff them and stores each save whole |

The third split is not fastidiousness. An ODT is a zip, so two saves of a
document share almost no bytes; `report9.odt` is 123 MB, and a fortnight of
edits adds a gigabyte of history that no amount of packing will compress. This
repository reached **6.9 GB** that way and had to be rewritten on 2026-08-24.
The markdown mirrors are the diffable surface, so the *text* of every document
is version controlled — just not the container around it.

## The shape of the tree

Restructured 2026-08-27. Two rules explain nearly all of it.

**`docs/` is what the project produces. `notes/` is everything written *about*
producing it.** Reports, papers, summaries, glossaries and the web tools are
deliverables; ledgers, specs, findings and standing references are not.

**`working/` is the private half, and it is a directory rather than a list.**
Everything the second repository owns lives under it and nothing else does.

```
NRG/
├── readme.md  CLAUDE.md  PIPELINE_README.md  BOOTSTRAP.md
├── run_analysis.py        the pipeline entry point
├── index.html  scenario_viewer.html  seasonal_extremes_scatter.html
│                          staged web tools — see §6
├── src/                   the pipeline
├── tools/                 the checking suite
├── data/                  raw inputs
├── outputs/               everything the pipeline writes
├── docs/                  DELIVERABLES: report, papers, summaries, glossaries, web_tools
├── notes/                 ledgers/  reference/  specs/  findings/
├── working/               PRIVATE: DECISION_LOG, WORK_REGISTER, changelogs/,
│                          updates/, nrg_git.sh, wgit, DOCUMENT_LOCK.json
├── literature/            source PDFs (Ranwell, Pye, Curreli) — not in either repo
├── living/                the monthly forecaster hub
└── venv/                  present, and not actually used — see §1
```

---

## 1. Prerequisites

**Read this section rather than skimming it.** Until 2026-08-27 it told you to
`pip install -r requirements.txt`, and that instruction was wrong twice over.

### The interpreter

**Python 3.12.** Not "3.10 or later": 3.12 is a floor *and* a ceiling. One module
needed 3.12-only syntax until 2026-08-27, and the recorded library versions have
no cp313 wheels, so 3.13 is untested and 3.11 will fail. Ubuntu 24.04 ships
3.12.3, which is the recorded interpreter.

```bash
python3 --version        # must say 3.12.x
```

**`venv/` IS the environment.** Until 2026-08-29 this section said to ignore it
and use the system interpreter with apt packages. That was wrong, and provably
so: built exactly to the apt line this section used to give, the pipeline dies at
Step 3 — `03_state_space_model.py` calls `ax.boxplot(tick_labels=…)`, and
`tick_labels` was added in **matplotlib 3.9**, above the 3.6.3 that apt ships on
noble. The documented environment could not run the code it documented.

Activate the venv, or call its interpreter directly:

```bash
source venv/bin/activate
python3 --version        # must say 3.12.3
```

One trap survives from the old text and is worth keeping in mind:
`venv/bin/python3` is a symlink to `/usr/bin/python3`, so the venv supplies
libraries but **not** an interpreter. On a machine whose `python3` is not 3.12
the venv appears to work and imports nothing — the same shape of failure that
cost a day on 2026-08-26 with `src/venv`.  <!-- former path -->
If `python3 --version` disagrees with
`venv/lib/python3.12`, that is the cause.

### The libraries: `requirements.txt`, and it is accurate

```bash
python3 -m venv venv                       # only if there is no venv/
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` pins the nineteen packages the pipeline actually runs on —
numpy 2.4.6, pandas 3.0.3, scipy 1.17.1, matplotlib 3.10.9, scikit-learn 1.9.0,
geopandas 1.1.3, shapely 2.1.2, pyproj 3.7.2, statsmodels 0.14.6, and the figure
dependencies adjustText, contextily and cairosvg. Its own header used to
disclaim it as *"a pip freeze from an environment this project has never run
in"*; that disclaimer was backwards and has been corrected.

Non-Python tools still come from apt, and pandoc's version matters (below):

```bash
sudo apt install git rclone libreoffice pandoc poppler-utils
```


### Do not trust this list — verify it

The list above is a starting point, not a proof. Two commands settle it, and the
second one is the reason the first can be incomplete without costing you a day:

```bash
python3 tools/env_audit.py       # what is here, against the recorded reference
python3 tools/import_audit.py    # every module imported; MISSING-DEP names the gaps
```

`import_audit` imports each module in its own subprocess under a write tripwire,
so it is safe to run on a working tree. Anything the apt line above missed shows
up as `MISSING-DEP` with the package name in the message. Install and re-run
until that count is zero.

**pandoc must be 3.x.** The mirrors are byte-for-byte reproducible under 3.1.3
and `refresh_mirrors.py` refuses below 3.0, because 2.x drops display equations
and escapes underscores the committed mirrors leave bare. Ubuntu 24.04 ships
3.1.3.

---

## 2. The public repository

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/newbroman/Newborough_Hydrology.git NRG
cd NRG
```

Then tell this repository to ignore the private half, which does not exist yet:

```bash
cat >> .git/info/exclude <<'EOF'
/working/
EOF
```

This goes in `.git/info/exclude` and **not** in `.gitignore`, and the reason is
worth understanding before you are tempted to move it. `.gitignore` is a
working-tree file, so both repositories read it, and it outranks a git
directory's `info/exclude`. A private path named in `.gitignore` is therefore  <!-- former path -->
hidden from the repository that is supposed to track it. Each repository excludes
the other's half in its own git directory; the shared `.gitignore` stays silent
on the subject and carries a comment saying so.

## 3. The private working records

These live in a **second git directory over the same working tree**. Nothing is
duplicated: the private repository owns `working/` and the public one owns
everything else.

```bash
cd ~/projects/NRG
git init --bare --quiet .git-working
git --git-dir=.git-working --work-tree=. config core.bare false
git --git-dir=.git-working --work-tree=. remote add origin \
    https://github.com/newbroman/Newborough_Hydrology_working.git
git --git-dir=.git-working --work-tree=. fetch origin
git --git-dir=.git-working --work-tree=. checkout -f main
```

`checkout -f` is safe here and only here: `working/` does not exist in the public
checkout, so nothing of it is overwritten.

**Give it an identity, with your actual name and address.** Earlier versions of
this file suggested copying the public repository's identity:

```bash
# DO NOT DO THIS — it is what the old instruction said, and it fails silently
for k in user.name user.email; do
  git --git-dir=.git-working --work-tree=. config "$k" "$(git config "$k")"
done
```

Nothing in this file ever sets the public repository's identity, so
`git config user.name` returns nothing, the loop writes an **empty** value, and
it exits 0. The first `wgit commit` then dies with *"cannot auto-detect email
address"* — the exact error the step claimed to prevent — and because a local
empty value outranks a global one, setting a global identity afterwards does not
fix it. Set both explicitly, in both repositories:

```bash
git config user.name  "Your Name"
git config user.email "you@example.com"
git --git-dir=.git-working --work-tree=. config user.name  "Your Name"
git --git-dir=.git-working --work-tree=. config user.email "you@example.com"
```

Then restore its exclude list, which is the mirror of the one in §2:

```bash
cat > .git-working/info/exclude <<'EOF'
# This repository owns the working records and nothing else. Everything is
# ignored by default so that a stray `wgit add -A` can never sweep up the
# public repository's files.
/*
!/working/
EOF
```

Two lines, because the boundary is a directory. It used to be seven anchored
negations here mirrored by seven entries in `.gitignore` — two hand-maintained
lists that had to disagree about every file, and if they ever both omitted one it
was tracked in neither repository. That is not hypothetical: until 2026-08-25
`wgit` and `setup_working_repo.sh` were in that state, present on one disk and
nowhere else.

`working/.gitignore` arrives with the checkout and carries `!*.sh`. Leave it
there. The root `.gitignore` blanket-ignores shell scripts, both repositories
read it, and it outranks `info/exclude` — so without that one line `nrg_git.sh`  <!-- former path -->
and `setup_working_repo.sh` are invisible to the repository that owns them.

`wgit`, `nrg_git.sh` and `README_WORKING.md` all arrive with this checkout. Use
`./working/wgit` for the private repository; plain `git` always means the public
one.

## 4. The documents

```bash
rclone config          # n → name it exactly "gdrive" → drive → scope 1 → browser auth
rclone copy gdrive:NRG_documents . --progress
```

Scope **1** (full access), not `drive.file`: the folder was created outside
rclone, and `drive.file` only shows rclone what it made itself.

About 404 MB. Then mark the archive current, so `tools/drive_lag.py` does not
report drift that is not there:

```bash
touch .last_drive_archive
```

That marker is read by `tools/drive_lag.py`, which `check_all` runs. It answers
the one question the `.gitignore` creates: the `.odt` and `.odm` documents are
in no repository, so between an edit and the next `rclone copy` they exist on
one disk only. Re-touch the marker after every upload:

```bash
rclone copy . gdrive:NRG_documents --include '*.odt' --include '*.odm' --progress
touch .last_drive_archive
```

## 5. Verify

```bash
bash tools/check_all.sh
```

Expect `check_all: OK`. Read the **first** section before any other: it names the
machine you are on and whether it is the recorded one. Every check below it that
mentions a version — pandoc, LibreOffice, pdftotext — is describing *this*
machine, and until 2026-08-27 none of them said so. A day was lost to a sandbox's
pandoc 2.9.2 being read as this project's.

If the mirrors section complains, the ODTs did not arrive. If the decisions
section complains, the private repository did not.

```bash
./working/wgit log --oneline -1     # the working records
git log --oneline -1                # the public repository
python3 tools/task_lint.py          # what is outstanding
python3 tools/import_audit.py       # every module imports, and none writes
```

## 6. Working from there

`bash working/nrg_git.sh` is the front door. It moved out of the root on
2026-08-27 because it belongs to the private repository — it carries the push
logic for both — and a file at the root cannot be hidden behind a directory
exclusion. Its `REPO_DIR` is absolute, so it behaves identically from anywhere.

- **2) Push my changes** commits and pushes *both* repositories, public first.
- **11) Archive documents** rclones the ODTs to Google Drive. Deliberately not
  part of option 2: the first upload took over an hour on a domestic connection,
  and a push that might block for an hour is a push nobody runs. Option 2 instead
  *reports* how many documents have changed since the last archive.
- **13) Publish web tools** builds and pushes the `gh-pages` branch from the three
  HTML files at the root. They stay at the root because that is where option 1
  stages them from `outputs/`; only the published copy lives on the branch.
- **q** quits.

**GitHub Pages** serves `main` from the root, which publishes the *entire
repository* at `newbroman.github.io/Newborough_Hydrology/` — every output CSV,
every figure, `notes/`, and `docs/papers/`. Martin confirmed on 2026-08-27 that
the manuscript PDFs are deliberately public, so this is untidiness rather than
exposure, and switching is optional.

What switching buys, if you want it: the published site becomes the three web
tools and nothing else, instead of 200 MB of intermediate CSVs and working notes
that search engines will otherwise index. Order matters, because the branch has
to exist on GitHub before the setting can name it:

1. `working/nrg_git.sh` option 13 — builds `gh-pages` and offers to push it
2. Settings → Pages → Source → *Deploy from a branch* → `gh-pages` → `/ (root)`

Note the repository, not just the setting: `Newborough_Hydrology`. The private
`Newborough_Hydrology_working` cannot serve Pages at all without Enterprise, and
`Newborough_welllogger` is a different project.

## 7. The second machine

Two machines share this project (a ThinkPad L14 and a ThinkPad A475). Follow
§§1–6 on the new one, then read this.

**`env_audit` will report `NOT THE MACHINE THIS PIPELINE RUNS ON`, permanently,
and that is correct.** `tools/environment.json` records one reference
environment; a second machine is not it. The message is the tool telling you that
any version-dependent line below it describes the machine you are sitting at.

**Do not run `env_audit --record` on the second machine.** The record is tracked
and pushed, so recording there overwrites the reference, publishes it, and leaves
every later run comparing against whichever machine recorded last. The tool
refuses, and `--force` exists only for a genuine change of reference machine.

**Take the documents lock before editing any ODT.** Option 12, or
`python3 tools/doc_lock.py take --note "what you are editing"`. The ODTs live on
Google Drive and are copied on demand, not synced, so two machines editing the
same document produce two whole files and no merge. Worse, it fails quietly: a
stale ODT regenerates a mirror that reverts the other machine's prose while every
gate in `check_all` still reports green, because the mirror faithfully matches
the document it was made from.

**Pull both repositories before starting and push both before stopping.**
`working/nrg_git.sh` option 4 pulls both; option 2 pushes both.

## What is deliberately not reproduced

`_to_delete/`, `_audit_tmp/`, and the three graveyards the 2026-08-27
restructure moved into `scratch/` and renamed flat — `scratch/report_edits__frozen/`,
`scratch/report_edits__superseded/` and `scratch/report_edits_backups/` — a few gigabytes of pre-edit snapshots, each superseded the moment
the edit it guarded was verified. They are excluded from the Drive archive and
from both repositories. If you find yourself wanting one, the git history of the
public repository and the bundle taken before the 2026-08-24 rewrite are the
places to look.

`literature/` is likewise not in either repository — source PDFs by other
authors, whose copyright is not ours to redistribute. Only its `README.md` is
tracked.

## The one rule

Never put `.git` — either of them — inside a folder synced by a live cloud
daemon. Partial and concurrent syncs corrupt repositories. The same applies to
the ODTs for a different reason: LibreOffice rewrites the whole file on every
save, so a daemon would re-upload 123 MB each time `report9` is touched, and a
zip captured mid-save is a corrupt document. `rclone copy`, run on demand, is
the whole of the sync story.
