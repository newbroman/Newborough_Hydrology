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
citations (advisory). **artefacts** checks an output against ITSELF — row
arithmetic, the empty artefact, and (since 2026-09-01) the PDF *Producer*. It
exists because three failures that week all sat in the gap where no gate looked.
**typed references** covers tables AND figures: `--kind figure` asks whether a
number still MEANS what it did, which `figref_lint` explicitly does not check.
Run `check_all` before you commit and quote the verdict in the message. If a
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
- **A 118 MB ODT will not cross the bridge — strip `Pictures/` and it will.**
  `device_stage_files` fails on `report9.odt` twice over, once on a wall-clock
  timeout and once on an upload failure, while report8 (0.8 MB) and report11
  (69 KB) go through fine. Rebuild the archive without its `Pictures/` members
  — mimetype STORED first, everything else copied — and it drops to **0.19 MB**.
  Pandoc reads image geometry from `draw:frame` attributes in `content.xml`, not
  from the image bytes, so **the mirror built from the stripped copy is
  BYTE-IDENTICAL to the one built from the full document** (verified 2026-09-02
  against a mirror generated on Martin's own machine: diff 0 lines). Write the
  stripped copy to the VM's own home, never into `mnt/`. **A read path only** —
  never commit or edit the stripped file, and never let it near
  `report_edits/odt/`.
  `refresh_mirrors.py` refuses below 3.0 — let it.

## 4. Environment traps that have each cost a session

- **`device_bash` is NOT Martin's machine.** It is a separate Linux VM with his
  `~/projects` mounted — not a shell on the ThinkPad. Its pandoc reports
  **2.9.2** against his 3.1.3, its Python is 3.10 against his 3.12, and scipy,
  statsmodels, sklearn, geopandas, shapely, contextily and adjustText are **not
  importable there at all**. A session once told him to downgrade pandoc on that
  evidence. Only `$HOME/mnt/NRG` is real; `$HOME` is not his home directory.
- **THE PIPELINE CANNOT BE RUN FROM HERE, and sharing more of his disk would not
  change that.** Asked on 2026-09-02 whether granting the home directory would
  help: it would not. The venv is built against his system Python and its
  compiled wheels; mounting it does not change which machine executes. Installing
  the libraries into the sandbox would not help either, because `env_audit`
  refuses results from a machine that is not the recorded one — which is the
  gate that makes the foreign-PDF class of error catchable. **Pipeline runs and
  PDF builds are Martin's, by design.** Everything text-only runs here.
- **ASK FOR A LOG FILE, NOT A PASTE.** `scratch/` is gitignored and inside the
  mount, so anything he runs can be captured where this session can read it:
  ```bash
  bash tools/check_all.sh 2>&1 | tee scratch/last_run.log
  python3 src/10a_ancova_baci.py 2>&1 | tee scratch/10a.log
  ```
  He still sees it scroll; the session reads the file and can grep it rather
  than being handed 400 lines. Adopted 2026-09-02 at his request — copying long
  terminal output by hand was the friction. `tee -a` to accumulate a session.
- **The mount refuses `unlink`.** `rm -f` on a stale git lock *fails silently*.
  Move it instead:
  ```bash
  mkdir -p _to_delete/locks
  for f in $(find .git .git-working -name '*.lock' 2>/dev/null); do
    mv "$f" "_to_delete/locks/$(basename $f).stale.$$" 2>/dev/null
  done
  ```
  **THE `.stale.$$` SUFFIX IS NOT DECORATION.** `-exec mv {} _to_delete/locks/ \;`
  is the obvious form and it silently STOPS WORKING after the first sweep: the
  destination name is taken, overwriting it needs an unlink, the mount refuses
  that, and `2>/dev/null` hides the failure. Measured 2026-09-02 — two commits
  in a row died with *"Another git process seems to be running"* when none was,
  because every sweep after the first had quietly done nothing. `working/wgit`
  has always appended `.stale.$$`; that is why.
  Locks appear as `index.lock`, `HEAD.lock` **and** `refs/heads/*.lock` —
  sweep all of them, not just the first. **A commit also leaves temp objects**
  (`.git/objects/*/tmp_obj_*`), measured 2026-09-01: harmless, but move them too
  or `git fsck` will complain. Sweep only when no git process is running.
  **`tools/check_all.sh` creates an `index.lock` too** — measured, 2026-08-31:
  one appears after every run over the bridge. Locks are not only left by
  running git directly, so sweep after `check_all` as well.
- **`device_bash` DOES have network** — corrected 2026-09-01, measured:
  `https://github.com` returns 200 and a release tarball downloads. The old note
  here said it had none, and that cost a session: mirrors were regenerated by
  staging ODTs to the cloud container and committing them back, and Martin was
  asked to type `refresh_mirrors.py` himself. **`git push` fails for want of
  CREDENTIALS, not network** — `could not read Username for 'https://github.com'`,
  because the sandbox mounts only the connected folder and never `/home/john`,
  and there is no TTY to prompt at. Corrected 2026-09-01; it is not a 403.
  With a credential helper populated inside the repo it pushes normally.
  **On the L14 that condition is now MET** — `.git/credentials` exists,
  written 2026-09-02, and `credential.helper` is `store --file=.git/credentials`,
  which is inside the mount and therefore visible to the sandbox. So a push
  from the bridge should work on this machine; ASK FIRST regardless (below).
  **The project-instructions box still says pushes CANNOT be made from the
  bridge, unconditionally.** That was true before the helper existed and is
  now too strong; the box is Martin's to edit, not this file's, so the two
  disagree until he does. Believe this line — it is checkable in one command.
- **Install pandoc 3.1.3 on the bridge and the mirror problem goes away.** Its
  own is 2.9.2 and `refresh_mirrors.py` rightly refuses below the pinned 3.0.
  Put a modern one in the VM's OWN home — never in Martin's tree:
  ```bash
  curl -sSL -o /tmp/p.tgz https://github.com/jgm/pandoc/releases/download/3.1.3/pandoc-3.1.3-linux-amd64.tar.gz
  tar xzf /tmp/p.tgz -C /tmp && mkdir -p "$HOME/bin"
  cp /tmp/pandoc-3.1.3/bin/pandoc "$HOME/bin/" && export PATH="$HOME/bin:$PATH"
  ```
  Per-session, not a one-off — the VM boots fresh. Use `--only <substring>`, one
  document per call: a full run exceeds the 45-second limit. Output is
  byte-identical to Martin's 3.1.3, verified 2026-09-01.
- **DO NOT BUILD A PUBLISHED PDF OVER THE BRIDGE. Ever.** This file used to
  give a workaround for `build_pdfs.sh` failing here — convert with `soffice`,
  copy over the target, and *update `docs/PDF_MANIFEST.txt` by hand*. **That
  advice put a foreign PDF into the published corpus on 2026-09-01 and hid it
  for three days.** Three safeguards failed in series: the mount refuses the
  `mv -f` that publishing needs, so a hand workaround got used; hand-editing the
  manifest CERTIFIED the bad build, because `build_pdfs.sh` decides staleness
  from it; and that check is mtime-only, so a foreign build is newer than its
  source and reads as "current". The PDF was Martin's LibreOffice 24.2 replaced
  by the bridge's 26.2.5.2. **`artefact_lint` Check C now gates on the Producer
  string, but the rule is simpler: PDFs are built on Martin's machine.** If one
  needs replacing, DELETE it and re-run `build_pdfs.sh` there — the builder will
  not overwrite a file that looks newer than its source.
- **A killed export leaves a LibreOffice lock on `report.odm`.** Backgrounding
  does not survive the call, so a `nohup`'d export is killed mid-load and
  `export_master_pdf.py` then refuses with *"the master is LOCKED"* — correctly,
  because a headless load of a locked document returns nothing silently. If the
  lock names THIS session, `--force-unlock` is safe. Run the export in the
  FOREGROUND with a long `timeout_ms`; it took **48 s** to write and about two
  minutes in total on 2026-09-01.
- **A venv without `--system-site-packages` cannot see `python3-uno`**, so
  `export_master_pdf.py` aborts inside the venv and works outside it. Same shape
  as the trap above: `check_all` also fails outside the venv, because the system
  Python has neither the recorded library versions nor `cairosvg`. Two different
  commands wanting two different interpreters, on the same machine.
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

**Git: run it, but ASK BEFORE EVERY PUSH (2026-09-01, his instruction).**
Commits over the bridge are fine — sweep the lock residue after each one. Pushing
is his call each time, so show the command and wait. He may or may not have a
credential helper populated; if not, hand him the one line.

**Never build a published PDF or run the pipeline over the bridge** — different
LibreOffice, different Python, missing libraries. Read, search, edit text, run
the text-only linters; leave anything that produces a published artefact to his
machine.

Show your working. He checks.
