# Setting the project up on a new machine

The project lives in three stores, split by what each thing is rather than where
it came from. Reconstructing it means fetching all three.

| store | holds | why there |
|---|---|---|
| this repository, public | code, tools, markdown mirrors, `DECISIONS_PUBLIC.md` | text that wants diffing and history |
| `Newborough_Hydrology_working`, **private** | decision log, changelogs, work register, working notes | text, but the deliberation rather than the conclusions |
| `gdrive:NRG_documents` | the ODT documents themselves | zips: git cannot diff them and stores each save whole |

The third split is not fastidiousness. An ODT is a zip, so two saves of a
document share almost no bytes; `report9.odt` is 123 MB, and a fortnight of
edits adds a gigabyte of history that no amount of packing will compress. This
repository reached **6.9 GB** that way and had to be rewritten on 2026-08-24.
The markdown mirrors are the diffable surface, so the *text* of every document
is version controlled — just not the container around it.

---

## 1. Prerequisites

```bash
sudo apt install git python3 python3-pip libreoffice rclone
```

**pandoc must be 3.x.** The mirrors are byte-for-byte reproducible under
3.1.3 and `refresh_mirrors.py` refuses below 3.0, because 2.x drops display
equations and escapes underscores the committed mirrors leave bare. Ubuntu 24.04
ships 3.1.3; on anything older take the `.deb` from
`github.com/jgm/pandoc/releases`.

```bash
pandoc --version | head -1        # must say 3.x
```

Python packages: `pandas numpy scipy statsmodels matplotlib odfpy`.

## 2. The public repository

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/newbroman/Newborough_Hydrology.git NRG
cd NRG
```

## 3. The private working records

These live in a **second git directory over the same working tree**. Nothing
moves: `DECISION_LOG.md` sits at the repository root where `decision_lint` and
`build_public_decisions` expect it, and `.git-working` simply ignores everything
it does not own.

```bash
cd ~/projects/NRG
git init --bare --quiet .git-working
git --git-dir=.git-working --work-tree=. config core.bare false
git --git-dir=.git-working --work-tree=. remote add origin \
    https://github.com/newbroman/Newborough_Hydrology_working.git
git --git-dir=.git-working --work-tree=. fetch origin
git --git-dir=.git-working --work-tree=. checkout -f main
```

`checkout -f` is safe here and only here: the private repository's four paths do
not exist in the public one, so nothing of the public checkout is overwritten.

Give it an identity. The public repository keeps `user.name` / `user.email` in
`.git/config` rather than globally, and a second git directory inherits none of
it — without this the first `wgit commit` dies with *"cannot auto-detect email
address"* after the message has already been typed:

```bash
for k in user.name user.email; do
  git --git-dir=.git-working --work-tree=. config "$k" "$(git config "$k")"
done
```

Then restore its exclude list, or a later `wgit status` will offer to commit the
entire public repository:

```bash
cat > .git-working/info/exclude <<'EOF'
/*
!/DECISION_LOG.md
!/WORK_REGISTER.md
!/changelogs/
!/Updates_required/
!/README_WORKING.md
EOF
```

`wgit` and `README_WORKING.md` arrive with the checkout. Use `./wgit` for the
private repository; plain `git` always means the public one.

## 4. The documents

```bash
rclone config          # n → name it exactly "gdrive" → drive → scope 1 → browser auth
rclone copy gdrive:NRG_documents . --progress
```

Scope **1** (full access), not `drive.file`: the folder was created outside
rclone, and `drive.file` only shows rclone what it made itself.

About 404 MB. Then mark the archive current so the toolkit does not report drift
that is not there:

```bash
touch .last_drive_archive
```

## 5. Verify

```bash
bash tools/check_all.sh
```

Expect `check_all: OK`. If the mirrors section complains, the ODTs did not
arrive; if the decisions section complains, the private repository did not.

```bash
./wgit log --oneline -1          # the working records
git log --oneline -1             # the public repository
python3 tools/task_lint.py       # what is outstanding
```

## 6. Working from there

`bash nrg_git.sh` is the front door.

- **2) Push my changes** commits and pushes *both* repositories, public first.
- **11) Archive documents** rclones the ODTs to Drive. Deliberately not part of
  option 2: the first upload took over an hour on a domestic connection, and a
  push that might block for an hour is a push nobody runs. Option 2 instead
  *reports* how many documents have changed since the last archive.
- **q** quits.

## What is deliberately not reproduced

`_to_delete/`, `_frozen/`, `_superseded/` and `backups/` — around 2.4 GB of
pre-edit snapshots, each superseded the moment the edit it guarded was verified.
They are excluded from the Drive archive and from both repositories. If you find
yourself wanting one, the git history of the public repository and the bundle
taken before the 2026-08-24 rewrite are the places to look.

## The one rule

Never put `.git` — either of them — inside a folder synced by a live cloud
daemon. Partial and concurrent syncs corrupt repositories. The same applies to
the ODTs for a different reason: LibreOffice rewrites the whole file on every
save, so a daemon would re-upload 123 MB each time `report9` is touched, and a
zip captured mid-save is a corrupt document. `rclone copy`, run on demand, is
the whole of the sync story.
