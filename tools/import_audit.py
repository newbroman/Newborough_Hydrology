#!/usr/bin/env python3
"""
import_audit.py — does importing a module do anything besides define names?

WHY IT EXISTS

  Two things, one of which is a correction to the other.

  1. `check_all` reads every file as text and imports nothing, so a module that
     will not parse looks exactly like one that is fine. That is how a 3.12-only
     line in `mechanism_fig_utils` went five weeks without anyone establishing
     whether Script 09g could start. A single pass that imports each module
     answers that in a second, and this is it.

  2. On 2026-08-26 two committed CSVs were found rewritten with placeholder
     values, and I attributed it to my own `python3 -c "import
     utils.mechanism_fig_utils"` — plausibly, and wrongly. This tool, used on the
     question, says so: `utils` audits clean, 0 modules write on import, and
     there is no module-level write anywhere in that chain. The real writer was
     an in-progress pipeline run, whose Script 01 legitimately writes
     `source=defaults` for later scripts to fill in.

     So the standing lesson is not "imports are dangerous". It is that **"does
     importing this module write?" was unanswerable without trying it on the real
     tree** — and when the answer mattered, a guess went into a commit message.
     A guess is what this replaces.

HOW IT ANSWERS WITHOUT WRITING

  Each module is imported in its own subprocess, under a tripwire that patches
  every write path this codebase uses — `open` in a writing mode, `os.open` with
  O_WRONLY/O_CREAT, `Path.write_text/write_bytes/open`, `os.replace/rename/
  remove`, `shutil.copy*/move`, `DataFrame.to_csv/to_excel/to_json/to_parquet`,
  `Figure.savefig`, `plt.savefig`. A patched call RECORDS its target and then
  does nothing, handing back an in-memory buffer where one is expected, so the
  import runs on to completion and every write is seen rather than only the
  first.

  Nothing reaches the filesystem. It is safe to run against the working tree,
  which is the point — the unsafe version of this test is the one that caused
  the problem.

  Subprocess isolation matters: module state, and a half-applied patch, must not
  leak from one import into the next.

WHAT THE VERDICTS MEAN

  OK        imports cleanly and writes nothing.
  WRITES    imports, but touches the filesystem while doing it. Each path is
            listed. This is a defect unless the module is deliberately a script.
  FAILED    does not import here. Read it with `env_audit` beside you: a
            ModuleNotFoundError for a third-party package is usually a statement
            about THIS machine, and is reported separately as MISSING-DEP for
            exactly that reason. A SyntaxError never is.

Usage:
    python3 tools/import_audit.py                # every module under src/
    python3 tools/import_audit.py utils          # only src/utils
    python3 tools/import_audit.py --quiet        # one verdict line (check_all)
    python3 tools/import_audit.py --strict       # non-zero on WRITES or FAILED
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-09-03. --static: the
#   source-only half of the audit, in milliseconds instead of minutes, so it
#   can be a standing check. Covers src/utils/ as well as the flat scripts,
#   which the guard grep could not — mask_streams_to_land.py was a script
#   living in src/utils/. D-120; task_register T-18.
# v1.0.0  # Hollingham (2026) — 2026-08-26.

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"

C_RED, C_YEL, C_GRN, C_DIM, C_0 = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"


def _c(s: str, c: str) -> str:
    return s if not sys.stdout.isatty() else f"{c}{s}{C_0}"


# The harness runs in a fresh interpreter, one module per run. It is a string
# rather than a file so there is no second thing to keep in step with this one.
HARNESS = r'''
import builtins, io, json, os, shutil, sys, importlib
from pathlib import Path

WRITES = []

def _note(kind, target):
    try:
        t = str(target)
    except Exception:
        t = "<unprintable>"
    WRITES.append(f"{kind} {t}")

# -- builtins.open ---------------------------------------------------------
_open = builtins.open
def open_(file, mode="r", *a, **k):
    if any(c in mode for c in "wxa+"):
        _note("open", file)
        return io.StringIO() if "b" not in mode else io.BytesIO()
    return _open(file, mode, *a, **k)
builtins.open = open_

# -- os level --------------------------------------------------------------
_os_open = os.open
def os_open_(path, flags, *a, **k):
    if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC):
        _note("os.open", path)
        return _os_open(os.devnull, os.O_WRONLY)
    return _os_open(path, flags, *a, **k)
os.open = os_open_

for name in ("replace", "rename", "remove", "unlink", "rmdir", "truncate"):
    if hasattr(os, name):
        def _mk(n):
            def f(*a, **k):
                _note("os." + n, a[0] if a else "?")
            return f
        setattr(os, name, _mk(name))

# mkdir is allowed to be a no-op rather than recorded: creating an output
# directory is not the failure this looks for, and blocking it noisily would
# bury the writes that matter.
os.makedirs = lambda *a, **k: None
os.mkdir = lambda *a, **k: None

# -- pathlib ---------------------------------------------------------------
Path.write_text  = lambda self, *a, **k: _note("Path.write_text", self)
Path.write_bytes = lambda self, *a, **k: _note("Path.write_bytes", self)
Path.mkdir       = lambda self, *a, **k: None
Path.unlink      = lambda self, *a, **k: _note("Path.unlink", self)
_p_open = Path.open
def p_open_(self, mode="r", *a, **k):
    if any(c in mode for c in "wxa+"):
        _note("Path.open", self)
        return io.StringIO() if "b" not in mode else io.BytesIO()
    return _p_open(self, mode, *a, **k)
Path.open = p_open_

# -- shutil ----------------------------------------------------------------
for name in ("copy", "copy2", "copyfile", "move", "rmtree"):
    if hasattr(shutil, name):
        def _mks(n):
            def f(*a, **k):
                _note("shutil." + n, a[1] if len(a) > 1 else (a[0] if a else "?"))
            return f
        setattr(shutil, name, _mks(name))

# -- the libraries that write without going through open() -----------------
try:
    import pandas as pd
    for meth in ("to_csv", "to_excel", "to_json", "to_parquet", "to_pickle"):
        if hasattr(pd.DataFrame, meth):
            def _mkp(m):
                def f(self, *a, **k):
                    _note("DataFrame." + m, a[0] if a else "<buffer>")
                return f
            setattr(pd.DataFrame, meth, _mkp(meth))
except Exception:
    pass

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    Figure.savefig = lambda self, *a, **k: _note("savefig", a[0] if a else "?")
    import matplotlib.pyplot as plt
    plt.savefig = lambda *a, **k: _note("plt.savefig", a[0] if a else "?")
except Exception:
    pass

# -- import it -------------------------------------------------------------
sys.path.insert(0, sys.argv[1])          # src/
name = sys.argv[2]
verdict, detail = "OK", ""
try:
    importlib.import_module(name)
except SyntaxError as e:
    verdict, detail = "SYNTAX", f"{e.msg} (line {e.lineno})"
except ModuleNotFoundError as e:
    verdict, detail = "MISSING-DEP", str(e)
except BaseException as e:                # SystemExit included: a module that
    verdict = "FAILED"                    # exits on import has still failed to
    detail = f"{type(e).__name__}: {e}"   # be importable.

print("@@AUDIT@@" + json.dumps({"verdict": verdict, "detail": detail,
                                "writes": WRITES}))
'''


def audit_one(modname: str) -> dict:
    r = subprocess.run([sys.executable, "-c", HARNESS, str(SRC), modname],
                       capture_output=True, text=True, timeout=120,
                       cwd=str(REPO))
    for line in (r.stdout or "").splitlines():
        if line.startswith("@@AUDIT@@"):
            return json.loads(line[len("@@AUDIT@@"):])
    return {"verdict": "FAILED",
            "detail": (r.stderr or "no output from the harness").strip()[-300:],
            "writes": []}


def modules(only: str | None) -> list[str]:
    out = []
    if only != "utils":
        for p in sorted(SRC.glob("*.py")):
            out.append(p.stem)
    for p in sorted((SRC / "utils").glob("*.py")):
        if p.stem != "__init__":
            out.append(f"utils.{p.stem}")
    return out


# --- static mode -------------------------------------------------------------
# The audit above is the real answer: it IMPORTS each module behind a write
# tripwire and reports what actually happened. It also takes many minutes, which
# is longer than task_lint's TIMEOUT, so it cannot BE a standing check — a row
# calling it records "timed out", which task_lint treats as an error and never
# as a pass.
#
# --static answers the cheap half in milliseconds, by reading the source instead
# of running it: does any module carry work at the TOP LEVEL — a loop, a `with`,
# or a call statement that is not one of the recognised bootstrap calls — while
# having no `__main__` guard to stop that work happening on import? That is the
# D-120 condition, and it covers src/utils/ as well as the flat scripts, which
# the guard grep alone could not: mask_streams_to_land.py was a SCRIPT living in
# src/utils/, and no check that globs src/*.py would ever have seen it.
#
# It is a proxy and says so. A module that opens a file inside a top-level
# ASSIGNMENT (`DF = pd.read_csv(...)`) passes this and would fail the real
# audit. Static mode narrows the gap; it does not close it, and --strict still
# runs the imports.
_BOOTSTRAP_CALLS = {"insert", "append", "filterwarnings", "use",
                    "register_matplotlib_converters", "seed"}


def _toplevel_work(path) -> list[tuple[int, str]]:
    """Top-level statements that DO something when the module is imported."""
    import ast
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as e:
        return [(getattr(e, "lineno", 0) or 0, f"unparseable: {e.msg}")]
    found = []
    for n in tree.body:
        if isinstance(n, (ast.For, ast.While, ast.With,
                          ast.AsyncFor, ast.AsyncWith)):
            found.append((n.lineno, type(n).__name__.lower()))
        elif isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
            fn = n.value.func
            name = getattr(fn, "attr", getattr(fn, "id", "?"))
            if name not in _BOOTSTRAP_CALLS:
                found.append((n.lineno, f"{name}()"))
    return found


def _guarded(path) -> bool:
    with open(path, encoding="utf-8") as fh:
        return any(line.startswith("if __name__ ==") for line in fh)


def static_scan(quiet: bool = False) -> int:
    """Count modules that run work on import. Returns that count."""
    paths = sorted(SRC.glob("*.py")) + sorted((SRC / "utils").glob("*.py"))
    offenders = {}
    for p in paths:
        if p.stem == "__init__":
            continue
        work = _toplevel_work(p)
        if work and not _guarded(p):
            offenders[p] = work
    if not quiet:
        for p, work in offenders.items():
            where = ", ".join(f"line {ln}: {what}" for ln, what in work[:4])
            extra = "" if len(work) <= 4 else f" (+{len(work) - 4} more)"
            print(_c(f"  RUNS ON IMPORT  {p.relative_to(REPO)}", C_RED))
            print(f"      {where}{extra}")
        verdict = (f"  import_audit --static: {len(paths)} module(s), "
                   f"{len(offenders)} run work on import with no __main__ guard")
        print(_c(verdict, C_RED if offenders else C_GRN))
    print(len(offenders))
    return len(offenders)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("only", nargs="?", default=None,
                    help="'utils' to limit to the shared modules")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--static", action="store_true",
                    help="fast source-only scan: which modules run work on "
                         "import with no __main__ guard (task_register T-18)")
    a = ap.parse_args()

    if a.static:
        return 1 if (static_scan(a.quiet) and a.strict) else 0

    writes, failed, syntax, missing, ok = {}, {}, {}, {}, 0
    names = modules(a.only)
    for name in names:
        res = audit_one(name)
        v = res["verdict"]
        if res["writes"]:
            writes[name] = res["writes"]
        if v == "OK" and not res["writes"]:
            ok += 1
        elif v == "SYNTAX":
            syntax[name] = res["detail"]
        elif v == "MISSING-DEP":
            missing[name] = res["detail"]
        elif v == "FAILED":
            failed[name] = res["detail"]

    if syntax:
        print(_c(f"  SYNTAX — {len(syntax)} module(s) this interpreter cannot "
                 f"parse. Never an environment excuse:", C_RED))
        for k, v in syntax.items():
            print(f"      {k}: {v}")

    if writes:
        print(_c(f"  WRITES — {len(writes)} module(s) touch the filesystem "
                 f"while being imported:", C_RED))
        for k, v in writes.items():
            print(f"      {k}")
            for w in v[:8]:
                print(f"          {w}")
            if len(v) > 8:
                print(f"          … and {len(v) - 8} more")
        print("  Importing one of these ALTERS THE REPOSITORY — a read-only "
              "reader, a linter,")
        print("  an editor's language server or an agent inspecting the tree "
              "would all do it")
        print("  without meaning to. Move the write behind an explicit call.")

    if failed:
        print(_c(f"  FAILED — {len(failed)} module(s) raised on import:", C_RED))
        for k, v in failed.items():
            print(f"      {k}: {v}")

    if missing:
        print(_c(f"  MISSING-DEP — {len(missing)} module(s) want a package this "
                 f"environment lacks", C_YEL))
        print("  (a statement about this machine — check tools/env_audit.py "
              "before reading it as a defect)")
        for k, v in sorted(missing.items())[:6]:
            print(f"      {k}: {v}")
        if len(missing) > 6:
            print(f"      … and {len(missing) - 6} more")

    bad = bool(syntax or writes or failed)
    verdict = (f"  import_audit: {len(names)} module(s) — {ok} clean, "
               f"{len(writes)} write on import, {len(syntax)} unparseable, "
               f"{len(failed)} raise, {len(missing)} missing a dependency here")
    print(_c(verdict, C_RED if bad else C_GRN))
    return 1 if (bad and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
