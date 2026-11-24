# The bridge environment — moved out of CLAUDE.md (D-330, 2026-11-24)

These sections stood in `CLAUDE.md` until 2026-11-24 and were moved here **verbatim** under D-330 ("CLAUDE.md holds
what no gate can; the bridge's environment history moves out"). D-298 made cloud sessions the default and the bridge
the exception, so this is read before a bridge session rather than by every session. Nothing was deleted; the
one-line digest of what still binds is CLAUDE.md §4. References elsewhere to "CLAUDE.md §4", "§4c" or "the bridge
is not the pipeline's machine" now mean this file. Revisit-if (D-330): a session breaks a rule *because* its
history moved out.

---

## 4. Environment traps that have each cost a session

- **`device_bash` is NOT Martin's machine.** It is a separate Linux VM with his
  `~/projects` mounted — not a shell on the ThinkPad. Its pandoc reports
  **2.9.2** against his 3.1.3, its Python is 3.10 against his 3.12, and scipy,
  statsmodels, sklearn, geopandas, shapely, contextily and adjustText are **not
  importable there at all**. A session once told him to downgrade pandoc on that
  evidence. Only `$HOME/mnt/NRG` is real; `$HOME` is not his home directory.
  **`source tools/bridge_py.sh` at the start of every call** (2026-10-28): it gives
  `nrgpy` (uv CPython 3.12.3 on the venv's site-packages, kept in `venv/.bridge/`,
  BLAS pin applied — numbers match the L14), pandoc 3.1.3 on `PATH`, and
  `TMPDIR=/tmp`. The VM's `/sessions` home volume is full and shared with old
  bridge sessions it cannot clean: write nothing large to `$HOME`.
- **THE PIPELINE CANNOT BE RUN FROM THE BRIDGE VM.** The pipeline runs on any
  machine that has built the environment with `tools/nrg_env.sh` (D-227): the
  laptop, or a Claude cloud session (§4g). On the bridge, `nrgpy` runs single scripts on
  the venv's libraries, but a call stops at 180 s and background jobs die with it,
  and its LibreOffice, git and pandoc are its own, so a full run there is not the
  pipeline's, and `env_audit` says so. Pipeline runs and published PDFs
  come from a built environment; everything text-only runs on the bridge.
- **DON'T HAND MARTIN WHAT THE BRIDGE CAN DO — RUN IT HERE, `tee` IT, READ IT.**
  Before handing over ANY command, ask what actually needs his machine. The
  bridge can install pandoc 3.1.3 (above), run `refresh_mirrors.py`,
  `build_citation_index.py`, `build_value_ledger.py`, every doc/table/citation
  gate, and commit/push (credentials are populated — see below). DO those here
  and read the result — never rely on Martin pasting output back. `scratch/` is
  gitignored and inside the mount, so capture anything into it and grep the file:
  ```bash
  source tools/bridge_py.sh                              # nrgpy, pandoc 3.1.3, TMPDIR=/tmp
  python3 tools/refresh_mirrors.py 2>&1 | tee scratch/refresh.log
  bash tools/check_all.sh 2>&1 | tee scratch/last_run.log
  ```
  He still sees it scroll; the session reads the file rather than being handed
  400 lines. `tee -a` to accumulate a session. Adopted 2026-09-02 (log-not-paste,
  at his request); **widened 2026-09-19** after a session handed him
  `refresh_mirrors`/`build_citation_index`/`check_all` it could have run itself.
  What the bridge cannot do: pipeline runs, the `report.pdf` rebuild, and the
  env-verified `./working/nrg_git.sh --ship` — `env_audit` fails on the bridge by
  design. Those run on the laptop or in a cloud session that has built the
  environment (D-227, §4g).
- **SHOW PROGRESS.** Anything handed to Martin to run that takes more than a few
  seconds must print a completion indicator — a percentage, a count of N, or a bar with
  elapsed and remaining time — on its own line as it goes, not only at the end.
  Adopted 2026-09-15 at his request: a 45-minute Sentinel download printed one
  line per twenty scenes and looked hung. `console_utils.track()` (1.2.0,
  2026-09-23) wraps any loop and prints `  [ 37 %  112/298  4m12s left ]`;
  `progress()` (1.1.0) is the bare call. Use them; do not print a bar by hand.
  A silent long run is a defect, whoever wrote it.
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
  from the bridge works on this machine, and **Martin authorised it as standing
  practice on 2026-09-08** ("but you have my push credentials"): first bridge
  pushes were `72dabec` (public) and `1c20e7e` (private, via `working/wgit`,
  whose helper is `store --file=.git-working/credentials`). Run every gate the
  bridge can first and quote the verdict — `check_all` itself reads FAIL here on
  the ENVIRONMENT line alone, by design, so the L14 verdict comes from Martin's
  `./working/nrg_git.sh --ship`, which also rebuilds report.pdf and
  archives to Drive. Sweep the lock/tmp_obj residue into `_to_delete/` after
  each git write. Stage by NAME, not `add -A`: `Claude outputs/` is ignored
  (its earlier contents moved to the private repository on 2026-10-02).
  **A claim made here on 2026-09-02 that the project-instructions box states
  this unconditionally was WRONG, and is withdrawn.** The box reads *"Pushes
  cannot be made from the bridge UNLESS a credential helper has been
  populated"* — conditional, and correct. Nothing disagrees with anything.
  Martin went looking for the contradiction and could not find it, because
  it was never there. Quote a document before characterising it.
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
  string, but the rule is simpler: PDFs are built where LibreOffice is the
  recorded version** (`tools/environment.json`; the laptop and the cloud image both
  are, 2026-10-02 — after a laptop OS upgrade, check before building). If one
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
- **`device_bash` calls die at their time limit** (120 s by default, 180 s at
  most — it was 45 s until 2026-09-20, see §4c) and backgrounded jobs die with
  them. `check_all` and a full `cite_check` exceed it; `--claims-only` and
  `--index-only` take ~1 s.
- **`device_commit_files` re-encodes images — gzip anything binary first.** It recognises a PNG by its
  content, not its name (a `.bin` was re-encoded too), and writes a valid but different file: same
  pixels, different bytes, so a committed output no longer matches its provenance hash. Measured
  2026-10-02 on three Script 50 figures (`check_all` did not notice). Send `gzip -n` copies to
  `scratch/` and decompress on the laptop; check the sha256 against `pipeline_provenance.json`.
- **Do not leave files staged in his tree.** His next `nrg_git.sh` commit will
  sweep them into his message.

### From CLAUDE.md §3: the 100-MB ODT and the bridge

- **A 100-MB-plus ODT will not cross the bridge — strip its image members and it will.**
  `device_stage_files` fails on `report9.odt` twice over, once on a wall-clock
  timeout and once on an upload failure, while report8 (0.8 MB) and report11
  (69 KB) go through fine. Rebuild the archive without its ODF **Pictures** members
  — mimetype STORED first, everything else copied — and it drops to **0.19 MB**.
  Pandoc reads image geometry from `draw:frame` attributes in `content.xml`, not
  from the image bytes, so **the mirror built from the stripped copy is
  BYTE-IDENTICAL to the one built from the full document** (verified 2026-09-02
  against a mirror generated on Martin's own machine: diff 0 lines). Write the
  stripped copy to the VM's `/tmp` (its home volume is full), never into the mounted folder. **A read path only** —
  never commit or edit the stripped file, and never let it near
  `report_edits/odt/`.
  `refresh_mirrors.py` refuses below 3.0 — let it.

## 4c. The bridge: what it can do, and three ways to break it (2026-09-20)

LibreOffice **and UNO both work on the bridge** — `soffice` is on PATH,
`import uno` succeeds, and `export_master_pdf.py` and `build_pdfs.sh` both run
there. Rendering a chapter to PDF is the fastest way to *check* a layout change
rather than assume it. **git over HTTPS also works**, despite `nrg_autopush.sh`'s
header; keep autopush on the publishing machine for anything with deletions,
for its mass-deletion guard.

**Nothing survives a `device_bash` call.** `nohup`, `setsid`, `&` all die with
it, so there is no start-and-poll. The practical ceiling is ~120 s. D-155 still
holds: the bridge does not produce committable pipeline artefacts.

Three traps, each of which bit on 2026-09-20:

1. **A timed-out shell orphans `soffice`** — the driver dies, the process does
   not, and the next export hangs on the stale UNO listener. Before any export:
   `pgrep -x soffice.bin` and `ls report_edits/odt/.~lock*`.
2. **`pkill -f soffice` kills the shell asking** — its own command line matches.
3. **`pgrep -f 'office.bin'` returned pids 1, 2, 3** — the VM's init, which then
   received `kill -9`. **Always `pgrep -x soffice.bin`.**

**A long `git commit -m` message does not survive a paste.** Two commits were
believed pushed and were not; a day's work sat untracked. Hand over
`git commit -F - <<'MSG' … MSG`, and verify with `git log --oneline -1` —
"pushed" is a belief until the log shows it.

Full account: `notes/findings/NRG_bridge_gates_ledgers_2026-09-20.md`.

## The bridge is not the pipeline's machine (D-155, D-227)

**Since D-227 (2026-10-02) the pipeline's machine is an ENVIRONMENT, not a host:**
Python 3.12.3 (uv-managed), `requirements.txt`, the externals and the BLAS/SIMD pin
in `tools/environment.json`, built by `tools/nrg_env.sh`. Any machine that builds it
produces byte-identical outputs — measured on 2026-10-02 between the laptop (Ryzen)
and a cloud container (Xeon), 58 of 58 files — and may run the pipeline and ship.
`env_audit` compares the environment; the hostname is reported, not compared.
What follows is the history that made the pin necessary.

Outputs committed to the repo are produced by a machine that has built the
environment, running `run_analysis.py`. A bridge run reads, inspects, lints and proves a script parses
— it does **not** produce committable artefacts.

The two environments are genuinely different. The publishing machine resolves
`geopandas` from `/usr/lib/python3/dist-packages` with **fiona and no pyogrio**,
so geopandas falls back to the fiona engine; the bridge has its own `~/.local`
site-packages **with pyogrio**, which does not. The same line succeeds in one and
raises in the other — that is how Script 41 broke on 2026-09-11 while "working"
when tested through the bridge: `gpd.read_file(..., driver="KML")` is accepted
by pyogrio and refused by fiona 1.10.1, which no longer lists the KML driver
(Script 41 2.7.0; every KML read now goes through `utils/kml_io.py`).

It is also why re-running Script 11 through the bridge moved **54 committed
numbers by up to one ULP** and tripped `provenance_lint`: different numeric
build, same arithmetic. Nothing was wrong with either result; they were produced
by different machines. The same last-digit drift appears between two machines
with identical libraries when OpenBLAS picks different kernels or thread counts,
or numpy uses AVX-512 on one and AVX2 on the other — which is what the D-227 pin
removes. (The fiona-only geopandas described above was the venv of 2026-09-11;
`requirements.txt` now pins both fiona and pyogrio, and every KML read goes
through `utils/kml_io.py` either way.)


---

## History of gated rules reduced to one line in CLAUDE.md (D-330, 2026-11-24)

D-330: every rule the matrix calls `gated` is one line naming its gate; the history that was still evidence is kept here, verbatim.

### §1, R01 (output_lag)

**`--with-supplementary` is not optional before a commit** (D-102). `--full` skips
the opt-in diagnostics, so an opt-in step can sit on `main` with edited code and
outputs from the previous version while every other gate reads green — every one
of them reads the outputs and finds them self-consistent. That happened to
`24b_residual_climatology.py` on 2026-08-31. `output_lag` is now a **gate** rather
than advice and is what enforces this; if it fails, the fix is to re-run the
script it names, never to skip the check.

### §4e, R23 (table_provenance_lint)

`PROVENANCE_LEDGER.md` (exhibits) and `VALUE_REGISTER.md` (cited values and
symbols) answer the question a document-keyed ledger cannot: *this script's
output changed — what has to be re-read?* `table_provenance_lint.py` enforces
Martin's rule that **a table cannot have no CSV; that breaks the line of truth
from the pipeline to the documents**. All <!--PL:report_tables-->

### §4d, R22 (the ledger --check gates)

- **A generated ledger with no `--check` in `check_all` rots silently.**
  TABLE_LEDGER did (19 empty sources, a five-versions-old document list) while
  FIGURE_LEDGER, built identically, stayed correct — the only difference was the
  gate. Every generated artefact gets its `--check` on the day it is written.

### §1, R66 (ship_regen_lint)

**`--ship` rebuilds every derived artefact the gates check BEFORE running them**
(D-213): version stamps, mirrors, published PDFs, index counts, the ledgers and
registers, the public decisions, the section map, the HANDOFF — and archives old
handover entries when Tier 0 is over budget. So a red gate after a ship is a defect
in the work, never "rebuild X and retry"; if it looks like the latter, the fix is
a line in `ship_regenerate()`, and `ship_regen_lint` says so. Three ships died on
exactly that on 2026-09-30, and three on 2026-09-24. A ship also refuses when
the local branch has diverged from GitHub (an `--amend` after a ship does that).
