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
bash tools/check_all.sh        # must end "check_all: OK"
```

Fifteen gates: document versions, mirrors, pipeline literals, record basis,
store-time rounding, decisions, ledgers, document references, tasks, symbols,
typed references, references-by-meaning, export lag, claims, citations
(advisory). Run it before you commit and quote the verdict in the message. If a
gate you did not touch starts failing, stop and find out why before proceeding.

`bash nrg_git.sh` is the front door for committing and pushing: **2)** pushes
both repositories, **11)** archives the ODTs to Drive, **q** quits.

## 2. The three stores

| store | holds |
|---|---|
| this repository, **public** | code, tools, markdown mirrors, `DECISIONS_PUBLIC.md` |
| `Newborough_Hydrology_working`, **private** | `DECISION_LOG.md`, `changelogs/`, `WORK_REGISTER.md`, `Updates_required/`, and this repo's own tooling |
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
  Locks appear as `index.lock`, `HEAD.lock` **and** `refs/heads/main.lock` —
  sweep all of them, not just the first.
- **`device_bash` has no network.** `git push` returns 403 from the proxy;
  Martin pushes. The **cloud container does** have network and pandoc 3.1.3 —
  use it for anything needing either.
- **`device_bash` calls die at 45 seconds** and backgrounded jobs die with them.
  `cite_check` full-run exceeds it; `--claims-only` and `--index-only` take ~1 s.
- **Do not leave files staged in his tree.** His next `nrg_git.sh` commit will
  sweep them into his message.

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

Show your working. He checks.
