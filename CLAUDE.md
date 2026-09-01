# NRG — read this before touching anything

Twenty-one years of dipwell monitoring at **Newborough Warren, Anglesey**, being
prepared for *Journal of Hydrology: Regional Studies*: two companion papers, a
technical report, a Methods Supplement and a Supplementary Material. Martin
Hollingham is the author. **This repository is public.**

`BOOTSTRAP.md` sets the project up on a new machine. This file is for a new
*session* — the things that have cost previous sessions hours to rediscover.

---

## 1. The one command

```bash
python3 run_analysis.py --full --with-supplementary   # regenerate EVERYTHING
bash tools/check_all.sh                               # must end "check_all: OK"
```

**`--with-supplementary` is not optional before a commit** (D-102). `--full` skips
the opt-in diagnostics, so an opt-in step can sit on `main` with edited code and
outputs from the previous version while every other gate reads green — every one
of them reads the outputs and finds them self-consistent. That happened to
`24b_residual_climatology.py` on 2026-08-31. `output_lag` is now a **gate** rather
than advice and is what enforces this; if it fails, the fix is to re-run the
script it names, never to skip the check.

Sixteen gates: document versions, mirrors, pipeline literals, record basis,
store-time rounding, **artefacts**, decisions, ledgers, document references,
tasks, symbols, typed references, references-by-meaning, export lag, claims,
citations (advisory). **artefacts** is the one that checks an output against
ITSELF — row arithmetic and the empty artefact — and it was added on 2026-09-01
because two failures that week both sat in the gap where no gate looked. Run it before you commit and quote the verdict in the message. If a
gate you did not touch starts failing, stop and find out why before proceeding.

`bash nrg_git.sh` is the front door for committing and pushing: **2)** pushes
both repositories, **11)** archives the ODTs to Drive, **q** quits.

## 2. The three stores

| store | holds |
|---|---|
| this repository, **public** | code, tools, markdown mirrors, `DECISIONS_PUBLIC.md` |
| `Newborough_Hydrology_working`, **private** | `DECISION_LOG.md`, `changelogs/`, `updates/` (was `Updates_required/`), `WORK_REGISTER.md` (a signpost; the live register is `updates/NRG_WORK_REGISTER.md`), and this repo's own tooling |  <!-- former path -->
| `gdrive:NRG_documents` | the ODTs themselves (git cannot diff a zip) |

Two git directories over **one** working tree. `./wgit` is the private one;
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
- **ODTs are versioned.** Edit `Doc_v1_9_46.odt` → write `Doc_v1_9_47.odt`.
  Mirrors follow the highest version automatically.
- **Mirrors need pandoc ≥ 3.0** and are byte-reproducible on 3.1.3.
  `refresh_mirrors.py` refuses below 3.0 — let it.

## 4. Environment traps that have each cost a session

- **`device_bash` is NOT Martin's machine.** It is a sandbox with its own
  package set. Its pandoc reports **2.9.2**; his is 3.1.3. A session once told
  him to downgrade on that evidence. Only `$HOME/mnt/NRG` is real; `$HOME`
  is not his home directory.
- **The mount refuses `unlink`.** `rm -f` on a stale git lock *fails silently*.
  Move it instead:
  ```bash
  mkdir -p _to_delete/locks
  find .git .git-working -name '*.lock' -exec mv {} _to_delete/locks/ \;
  ```
  Locks appear as `index.lock`, `HEAD.lock` **and** `refs/heads/main.lock` —  <!-- former path -->
  sweep all of them, not just the first.
  **`tools/check_all.sh` creates an `index.lock` too** — measured, 2026-08-31:
  one appears after every run over the bridge. Locks are not only left by
  running git directly, so sweep after `check_all` as well.
- **`device_bash` DOES have network** — corrected 2026-09-01, measured:
  `https://github.com` returns 200 and a release tarball downloads. The old note
  here said it had none, and that cost a session: mirrors were regenerated by
  staging ODTs to the cloud container and committing them back, and Martin was
  asked to type `refresh_mirrors.py` himself. **`git push` is still refused**
  (403 from the proxy) and pushing stays Martin's; general egress works.
- **Install pandoc 3.1.3 on the bridge and the mirror problem goes away.** The
  bridge's own pandoc is 2.9.2 and `refresh_mirrors.py` rightly refuses below
  the pinned 3.0. Put a modern one in the VM's OWN home — never in Martin's
  tree — and point PATH at it:
  ```bash
  curl -sSL -o /tmp/pandoc.tgz \
    https://github.com/jgm/pandoc/releases/download/3.1.3/pandoc-3.1.3-linux-amd64.tar.gz
  tar xzf /tmp/pandoc.tgz -C /tmp && mkdir -p "$HOME/bin"
  cp /tmp/pandoc-3.1.3/bin/pandoc "$HOME/bin/" && chmod +x "$HOME/bin/pandoc"
  export PATH="$HOME/bin:$PATH"        # then refresh_mirrors.py just works
  ```
  The VM boots fresh, so this is a per-session step, not a one-off install.
  **Use `--only <substring>` and do one document per call**: a full run over the
  bridge exceeds the 45-second limit, but one document takes a few seconds.
  report9 and report10 are ~200 MB and are the ones to expect trouble from.
- **`tools/build_pdfs.sh` CANNOT run over the bridge**, measured 2026-09-01. It
  builds into a temp dir and publishes with `mv -f`, and the mount refuses the
  unlink that overwriting an existing target needs:
  `unable to remove target: Operation not permitted`. The PDF is built and then
  thrown away. Convert with `soffice` into the VM's own `$HOME`, then publish
  with a **copy that truncates rather than unlinks** — the same pattern
  `odt_edit._write` uses:
  ```python
  with open(src,'rb') as a, open(dst,'wb') as b: shutil.copyfileobj(a,b)
  ```
  and update `docs/PDF_MANIFEST.txt` by hand, since the script never reached it.
  **`tools/export_master_pdf.py` is fine** — it publishes with `shutil.copy2`.
- **A killed export leaves a LibreOffice lock on `report.odm`.** Backgrounding
  does not survive the call, so a `nohup`'d export is killed mid-load and
  `export_master_pdf.py` then refuses with *"the master is LOCKED"* — correctly,
  because a headless load of a locked document returns nothing silently. If the
  lock names THIS session, `--force-unlock` is safe. Run the export in the
  FOREGROUND with a long `timeout_ms`; it took **48 s** to write and about two
  minutes in total on 2026-09-01.
- **PDFs built here come from a DIFFERENT LibreOffice than Martin's** — the
  bridge reported **26.2.5.2** against his 24.2 on 2026-09-01. The Supplement
  came out at exactly the same 271 pages, so pagination agreed; but `report.pdf`
  came out **36.8 MB against 28.9 MB, +27%**, which the export script flags
  itself. Treat a bridge-built published PDF as provisional until Martin has
  rebuilt it, or until the size step is understood.
- **`device_bash` calls die at 45 seconds** and backgrounded jobs die with them.
  `cite_check` full-run exceeds it; `--claims-only` and `--index-only` take ~1 s.
- **Do not leave files staged in his tree.** His next `nrg_git.sh` commit will
  sweep them into his message.

## 4b. Two machines at once

Both git repositories merge, so code, tools, the decision log and the changelogs
are safe to work on from two machines simultaneously.

**The ODTs are not.** `rclone copy` is one-way with no conflict detection, and a
zip has nothing to merge. Worse: **the mirrors are committed and the ODTs are
not**, so a machine holding a stale ODT regenerates the mirror from it and
pushes a reversion of someone else's prose — and `check_all`'s mirror gate
compares modification times only, never content, so it reads as green.

`tools/doc_lock.py` makes that a refusal instead. `nrg_git.sh` **12)** takes and
releases; **11)** will not archive while another machine holds it; **2)** warns
if documents changed here without it. The lock lives in the private repo, so it
is only as current as the last fetch — it is a handover protocol between one
person's machines, not a mutex.

Never run `refresh_mirrors.py` on a machine whose ODTs you have not just pulled.

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

Prose judgement in the ODTs (the symbol register, T-01), anything that changes a
published claim rather than a stale value, pushing, and any decision that would
add a new entry to the decision log. Everything else — audits, tooling, mirrors,
value corrections, the Methods Supplement and Supplementary Material — he has
asked to be done and then reported, not asked about first.

**Pushing: ask whether he is at the PC first (2026-08-29, his instruction).**
A session with the bridge *can* rebuild the PDFs and push both repos, and on
2026-08-29 it did — but report9.odt is 123 MB and report.pdf 36 MB, so every file
crosses the bridge in checksum-verified parts and the whole sequence costs the
best part of an hour. At his own machine he does it in minutes with
`working/nrg_git.sh`. So the question to ask is not *may I push* but **"are you
at the PC and able to push, or shall I?"** — and if he is away, do it, because
knowing it can be done unattended is the point.

Show your working. He checks.
