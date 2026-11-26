#!/usr/bin/env python3
"""
task_lint.py — outstanding work, where "done" is a command rather than a memory.

WHAT GOES WRONG WITHOUT IT

  This project keeps four registers of state, and every one of them has rotted
  the same way:

      citation_index.csv    119 stale rows      — until cite_check
      DECISION_LOG.md       two numbering schemes — until decision_lint
      SCRIPT_LEDGER.md      29 stale versions, 2 missing scripts — until ledger_lint
      NRG_WORK_REGISTER.md  said 37 easting passages; there were 113

  The pipeline never does this. `run_analysis.py` registers every step, emits
  `pipeline_manifest.json`, and `sync_index_counts` reads it, so a step cannot be
  quietly lost. The editorial side had registers that nothing read, and a record
  nothing reads is a record that rots.

THE DESIGN, WHICH IS ONE IDEA

  **A task has no stored status.** There is no `done` column, because a stored
  status is a claim someone has to remember to update — which is the failure
  above, in miniature. Instead each row carries a CHECK: a command, and the
  output it must produce. Status is computed every run.

  A task therefore closes itself the moment its condition is met, and — more to
  the point — REOPENS ITSELF if the condition stops holding. Marking something
  done that isn't is not possible, because nobody marks anything.

  What cannot be expressed as a check does not belong here. A row that says
  "tidy up the coastal section" is a note, not a task, and notes live in
  `Updates_required/`. The discipline the register imposes is on whoever writes
  the row: state the condition under which you would agree it is finished.

A BROKEN CHECK IS NOT A PASS

  The failure mode that would make this tool worse than useless is a check that
  errors and reads as success — the same shape as a reference nothing matches
  being invisible to the thing that would report it, which has caught this
  project four times. So:

      command exits non-zero  -> ERROR, and the run fails
      command produces nothing -> ERROR, and the run fails
      output != expect        -> OPEN
      output == expect        -> DONE
      output is "<tool>: SKIP …" -> SKIPPED (1.1.0)

  SKIPPED is for a check whose inputs are absent BY DESIGN in this checkout — the
  ODT documents, which the public repository does not carry. The tool itself must
  decide that and say SKIP; task_lint never infers it. It is counted on its own,
  never as done, open or broken, so a cloud run without the documents reports the
  project's state instead of a broken check every day.

  ERROR is louder than OPEN, deliberately. An open task is work; a broken check
  is a lie waiting to happen.

ON RUNNING COMMANDS FROM A CSV

  `tools/task_register.csv` is tracked, reviewed in diff like any other file, and
  its commands run with the repo root as the working directory. The refusal list
  below is a TRIPWIRE, not a sandbox: it catches a destructive command arriving
  by accident or by careless copy-paste, and it would not stop anyone determined.
  Checks must be read-only. If one needs to write, it is not a check.

Usage:
    python3 tools/task_lint.py             # full report
    python3 tools/task_lint.py --quiet     # gate: fails only on a broken check
    python3 tools/task_lint.py --open      # just the open ones
"""
from __future__ import annotations

__version__ = "1.4.0"  # Hollingham (2026) — 2026-11-26 (Martin: "fix the whole check-all process"; the Fable gate
#   review of the same day). (1) The register's `needs` column (private | odt) says what a check reads that a
#   public clone lacks; task_lint still infers nothing from the command. A `private` check with the private store
#   ABSENT is a FLAG and a FAIL - "The private repository should always be present, surely" (Martin, 2026-11-26) -
#   never a skip and never a phantom OPEN or DONE; an `odt` check with no ODTs is SKIP (a session without the Drive
#   secret is a blessed mode, CLAUDE.md 4g). (2) `cite_check --index-only` runs ONCE: its output is shared with the
#   checks through NRG_CITE_INDEX_OUT (check_all sets it; standalone, task_lint runs it once itself). (3)
#   --states-out PATH writes {id: status} for register_lint, which ran all of task_lint a second time. (4) Checks run
#   on a thread pool capped at the core count (NRG_TASK_LINT_WORKERS); verdicts matched serial on all 225 rows.
# 1.3.0  # Hollingham (2026) — 2026-11-11 (J-12, T-196). render() is the printed report,
#   shared by main() and by as_json(with_text=True), so the HQ daily pass can hand proof_copy's tasks tab the
#   same text `--open` prints from the ONE evaluation it already runs for the HQ page (the checks are not run
#   twice, which is what check_all's --tasks-from did until check_all 1.41.0). Output unchanged.
# 1.2.0  # Hollingham (2026) — 2026-11-05 (D-301, spec NRG_handover_HQ_page_2026-11-05,
#   signed off). --json for the HQ page's tasks band and its 7-run trend, carrying the store state because a task's
#   status is store-dependent; evaluate() shared with the printed report so the two cannot disagree; D8's optional
#   `claim` column read and reported, never used to decide a status.
# 1.1.0  # Hollingham (2026) — 2026-10-27. SKIPPED: a check that answers "<tool>: SKIP …" (its inputs are
#   absent by design, e.g. the ODTs in the public clone) is counted on its own, not as broken (T-126, T-127 in the
#   daily cloud check).
# 1.0.0  # Hollingham (2026) — 2026-08-25.

import argparse
import csv
import datetime
import json
import os
import re
import tempfile
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))          # 1.2.0: doc_lock, for the store state in --json
REGISTER = REPO / "tools/task_register.csv"
TIMEOUT = 120

# Tripwire, not a sandbox — see the docstring. A check that trips this is a
# mistake in the register, and the register is the thing to fix.
#
# Discarding stderr is read-only, and the first run of this tool refused three
# perfectly good checks over `2>/dev/null`. The guard was wrong, not the checks.
# It is stripped before the test rather than carved out of the pattern, because
# a redirect exemption written into a regex of forbidden redirects is a thing
# nobody will read correctly six months from now.
_DEVNULL = re.compile(r"\d*>>?\s*/dev/null")

FORBIDDEN = re.compile(
    r"(?:^|[\s;|&(])(?:rm|mv|cp|dd|mkfs|chmod|chown|truncate|shred)\s"
    r"|>\s*[^&|]|>>|git\s+(?:push|commit|reset|checkout|clean|rm)\b",
    re.I)


# 1.1.0: a check's answer of the form "<tool>: SKIP ..." (or "SKIP ...")
SKIP_RE = re.compile(r"^(?:[\w.-]+:\s+)?SKIP\b")


def is_read_only(cmd: str) -> bool:
    return not FORBIDDEN.search(_DEVNULL.sub("", cmd))


def run_check(cmd: str) -> tuple[str | None, str]:
    """Returns (stdout-or-None, note). None means the check did not produce
    an answer, which is an ERROR and never a pass."""
    if not is_read_only(cmd):
        return None, "refused: the check is not read-only"
    try:
        p = subprocess.run(cmd, shell=True, cwd=REPO, timeout=TIMEOUT,
                           capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return None, f"timed out after {TIMEOUT}s"
    if p.returncode != 0:
        err = (p.stderr or "").strip().split("\n")[-1][:90]
        return None, f"exit {p.returncode}: {err}"
    out = (p.stdout or "").strip()
    if out == "":
        return None, "produced no output — a check must answer"
    return out, ""


CITE_ENV = "NRG_CITE_INDEX_OUT"
ODT_GLOBS = ("report_edits/odt/report*.odt", "docs/papers/*/*.odt")
PRIVATE_FLAG = ("the private repository is absent - it should always be present (Martin, 2026-11-26); "
                "this check reads it and cannot answer")


def _needs(r: dict) -> set[str]:
    return {n.strip() for n in (r.get("needs") or "").split(";") if n.strip()}


def _odts_present() -> bool:
    return any(any(REPO.glob(g)) for g in ODT_GLOBS)


def _private_present() -> tuple[bool, str]:
    import doc_lock
    state, why = doc_lock.store_state()
    return state != "ABSENT", why


def _share_cite_index(rows: list[dict]) -> None:
    """1.4.0: run cite_check --index-only once for every check that reads it (three did, 20 s each)."""
    if os.environ.get(CITE_ENV) and Path(os.environ[CITE_ENV]).exists():
        return
    if not any(CITE_ENV in (r.get("check") or "") for r in rows):
        return
    fd, path = tempfile.mkstemp(prefix="nrg_cite_index_", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        p = subprocess.run([sys.executable, str(REPO / "tools/cite_check.py"), "--index-only"], cwd=REPO,
                           capture_output=True, text=True, timeout=TIMEOUT * 3)
        fh.write(p.stdout)
    os.environ[CITE_ENV] = path


def _workers() -> int:
    try:
        return max(1, int(os.environ.get("NRG_TASK_LINT_WORKERS", "")))
    except ValueError:
        return max(1, min(4, os.cpu_count() or 1))


def evaluate(rows: list[dict]) -> tuple[list, list, list, list]:
    """Run every row's check once and sort the rows four ways. Shared by the printed report and
    --json (1.2.0), so the HQ snapshot cannot disagree with what the gate printed. 1.4.0: a `private` check with
    the store absent is an ERROR carrying PRIVATE_FLAG (it is not run); an `odt` check with no ODTs is skipped."""
    done, open_, errors, skipped = [], [], [], []
    have_private, _why = _private_present()
    have_odt = _odts_present()
    _share_cite_index(rows)

    def one(r):
        nd = _needs(r)
        if "private" in nd and not have_private:
            return None, "FLAG: " + PRIVATE_FLAG
        if "odt" in nd and not have_odt:
            return "SKIP (inputs absent by design) - this check reads the ODTs, which this session does not hold", ""
        return run_check(r["check"])

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=_workers()) as ex:
        results = list(ex.map(one, rows))
    for r, (out, note) in zip(rows, results):
        if out is None:
            errors.append((r, note))
        elif SKIP_RE.match(out):
            skipped.append((r, out))
        elif out == r["expect"].strip():
            done.append(r)
        else:
            open_.append((r, out))
    return done, open_, errors, skipped


def read_register() -> list[dict]:
    with REGISTER.open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r.get("id", "").strip()]


def render(rows, done, open_, errors, skipped, only_open: bool = False, quiet: bool = False) -> str:
    """1.3.0: the printed report as text, byte-for-byte what main() printed before, so main() and
    as_json(with_text=True) cannot disagree."""
    out: list[str] = []
    say = out.append
    if errors:
        say(f"  FAIL  {len(errors)} check(s) could not answer — "
            f"a broken check is not a pass:")
        for r, note in errors:
            say(f"          {r['id']}  {r['title'][:52]}")
            say(f"                {note}")

    if not only_open and not quiet and done:
        say(f"\n  {len(done)} task(s) now satisfy their check "
            f"(remove the row, or leave it as a regression guard):")
        for r in done:
            say(f"      DONE  {r['id']}  {r['title'][:64]}")

    if open_ and not quiet:
        say(f"\n  {len(open_)} open:")
        for r, o in sorted(open_, key=lambda x: x[0]["id"]):
            impl = f"  [{r['implements']}]" if r.get("implements") else ""
            say(f"      OPEN  {r['id']}  {r['title'][:60]}{impl}")
            say(f"                {o}  (want {r['expect'].strip()})"
                f"   opened {r.get('opened','')}")

    if skipped and not quiet:
        say(f"\n  {len(skipped)} skipped (inputs absent in this checkout by design):")
        for r, o in skipped:
            say(f"      SKIP  {r['id']}  {r['title'][:60]}")
            say(f"                {o[:110]}")

    if quiet:
        say("task_lint: " + ("FAIL" if errors else "OK"))
    else:
        say(f"\n  {len(rows)} task(s): {len(done)} done, {len(open_)} open, "
            f"{len(errors)} broken" + (f", {len(skipped)} skipped" if skipped else ""))
    return "\n".join(out)


def as_json(with_text: bool = False) -> dict:
    """1.2.0 (D-301): the register, machine-readable, for the HQ page's tasks band and its trend.

    It carries the STORE STATE, because a task's status is store-dependent: a session holding only
    the public repository measured 133 tasks / 104 done / 28 open on 2026-11-05 where a session with
    both measured 134 / 120 / 14. Writing that into the HQ snapshot would invent 14 open tasks, so
    the consumer refuses a snapshot whose store is ABSENT (D-300 applied to the auditor itself)."""
    import doc_lock
    state, why = doc_lock.store_state()
    rows = read_register() if REGISTER.exists() else []
    done, open_, errors, skipped = evaluate(rows)
    def row(r, status, got="", note=""):
        # D8: `claim` is an OPTIONAL column. task_lint ignores it when deciding status - it only
        # says who should pick the task up - so a register without it behaves exactly as before.
        return {"id": r.get("id", ""), "title": r.get("title", ""),
                "implements": r.get("implements", ""), "check": r.get("check", ""),
                "want": (r.get("expect") or "").strip(), "got": got, "status": status,
                "opened": r.get("opened", ""), "claim": (r.get("claim") or "").strip(),
                "note": note or (r.get("note") or "")[:400]}
    res = {
        "store": state, "store_why": why,
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "counts": {"total": len(rows), "done": len(done), "open": len(open_),
                   "broken": len(errors), "skipped": len(skipped)},
        "has_claim_column": any((r.get("claim") or "").strip() for r in rows),
        "tasks": ([row(r, "DONE", (r.get("expect") or "").strip()) for r in done]
                  + [row(r, "OPEN", o) for r, o in open_]
                  + [row(r, "BROKEN", "", n) for r, n in errors]
                  + [row(r, "SKIP", o) for r, o in skipped]),
    }
    if with_text:
        # 1.3.0 (J-12): what `--open` prints, from this same evaluation - for proof_copy's tasks tab.
        res["open_text"] = render(rows, done, open_, errors, skipped, only_open=True)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--open", action="store_true", dest="only_open")
    ap.add_argument("--json", action="store_true", help="the register machine-readable (1.2.0, D-301)")
    ap.add_argument("--states-out", metavar="PATH", help="1.4.0: also write {id: status} as JSON, for register_lint")
    args = ap.parse_args()

    if args.json:
        print(json.dumps(as_json(), indent=2))
        return 0

    if not REGISTER.exists():
        print(f"  SKIP  {REGISTER.name} not in this checkout")
        return 0

    rows = read_register()
    done, open_, errors, skipped = evaluate(rows)
    if args.states_out:
        st = {r["id"]: "done" for r in done}
        st.update({r["id"]: "open" for r, _ in open_})
        st.update({r["id"]: "broken" for r, _ in errors})
        st.update({r["id"]: "skip" for r, _ in skipped})
        Path(args.states_out).write_text(json.dumps(st, indent=1, sort_keys=True), encoding="utf-8")
    flagged = [r for r, n in errors if n.startswith("FLAG: ")]
    if flagged:
        print(f"  FLAG  the private repository is ABSENT: {len(flagged)} task check(s) read it and were not run. "
              "It should always be present (Martin, 2026-11-26) - attach it (tools/cloud_setup.sh).")
    print(render(rows, done, open_, errors, skipped, only_open=args.only_open, quiet=args.quiet))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
