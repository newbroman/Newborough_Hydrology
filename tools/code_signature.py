#!/usr/bin/env python3
"""code_signature.py — the code each pipeline step RAN, recorded, so output_lag has a witness (Fable review 2026-11-24).

output_lag decided "behind" from clocks, and excused any script whose provenance-recorded __version__ equals the live
one on the premise that every edit bumps it — which nothing gates. Measured 2026-11-24: an executable edit with no
bump read OK; a fresh clone of a branch with 22 edited, unrun scripts read OK, because a checkout rewrites mtimes.
Both are clocks and labels, written by the same hand as the edit. The witness is the CODE: a hash of each script's
executable source (comments, docstrings and __version__ removed; text, so every Python version agrees), and of
every src/utils module it imports, recorded at the moment the step ran.

    outputs/pipeline_code_signatures.json    {"scripts": {script: {"sig": h, "utils": {module: h}, "recorded": t}}}

    python3 tools/code_signature.py record SCRIPT [...]   run_analysis.py, after each successful step (a sub-runner
                                                          records the scripts it runs)
    python3 tools/code_signature.py seed                  one-off: for every step with provenance, record the code AS
                                                          COMMITTED AT THAT STEP'S RUN START (git), not the code now
    python3 tools/code_signature.py --selftest

`differs(script)` is what output_lag asks: None when nothing is recorded (it falls back to its clocks), else the list
of what changed ("script" and/or "utils/<m>.py").
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-24. New (Fable review risks 1 and 2; output_lag 1.2.0). Signatures
#   are of cleaned source TEXT, not ast.dump, so they agree across Python versions.

import ast
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO / "src"
FILE = REPO / "outputs" / "pipeline_code_signatures.json"
PROV = REPO / "outputs" / "pipeline_provenance.json"
RUNNERS = ("run_09_scraping.py", "run_10_clearfell.py")


def clean_lines(src: str) -> list[str] | None:
    """The source with comments, docstrings and __version__ assignments blanked, line positions kept.

    Text, not ast.dump: ast.dump's output differs between Python versions (measured 2026-11-24: a 3.13 seed read
    every script as changed under check_all's 3.12), and a witness that depends on the interpreter is no witness.
    The AST is used only for POSITIONS, which every version reports the same."""
    import io
    import tokenize
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    lines = src.splitlines()
    spans = []                                          # (line0, col0, line1, col1), 1-based lines
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = node.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                d = b[0]
                spans.append((d.lineno, d.col_offset, d.end_lineno, d.end_col_offset))
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "__version__" for t in n.targets):
            spans.append((n.lineno, n.col_offset, n.end_lineno, n.end_col_offset))
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                spans.append((tok.start[0], tok.start[1], tok.end[0], tok.end[1]))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    for l0, c0, l1, c1 in sorted(spans, reverse=True):
        if l0 == l1:
            lines[l0 - 1] = lines[l0 - 1][:c0] + lines[l0 - 1][c1:]
        else:
            lines[l0 - 1] = lines[l0 - 1][:c0]
            for k in range(l0, l1 - 1):
                lines[k] = ""
            lines[l1 - 1] = lines[l1 - 1][c1:]
    return [l.rstrip() for l in lines]


def _h(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(l for l in lines if l.strip()).encode()).hexdigest()[:16]


def signature(src: str) -> str | None:
    """sha256 (16 hex) of the executable source: comments, docstrings and __version__ removed."""
    cl = clean_lines(src)
    return None if cl is None else _h(cl)


def imported_names(src: str) -> dict[str, set | None]:
    """{module: names imported from it, or None for the whole module}. Only names matter: a module that gains a
    constant nobody imports has not changed what this script runs (J-15 added fifty to utils/paths.py)."""
    out: dict[str, set | None] = {}
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {m: None for m in utils_of(src)}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("utils."):
            m = n.module.split(".", 1)[1]
            if out.get(m, set()) is not None:
                out.setdefault(m, set()).update(a.name for a in n.names)
            if any(a.name == "*" for a in n.names):
                out[m] = None
        elif isinstance(n, ast.ImportFrom) and n.module == "utils":
            for a in n.names:
                out[a.name] = None
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("utils."):
                    out[a.name.split(".", 1)[1]] = None
    # a whole-module import (`from utils import paths`, `import utils.paths as p`) uses only the attributes the
    # script reads through its alias; the module stays whole (None) only if the alias is used bare
    aliases: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "utils":
            for a in n.names:
                aliases[a.asname or a.name] = a.name
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("utils.") and a.asname:
                    aliases[a.asname] = a.name.split(".", 1)[1]
    attr_parent = {id(x.value) for x in ast.walk(tree) if isinstance(x, ast.Attribute)}
    for al, m in aliases.items():
        if out.get(m, "x") is not None and m in out and out[m]:
            continue                                     # names already collected for it
        bare = any(isinstance(x, ast.Name) and x.id == al and id(x) not in attr_parent for x in ast.walk(tree))
        attrs = {x.attr for x in ast.walk(tree) if isinstance(x, ast.Attribute)
                 and isinstance(x.value, ast.Name) and x.value.id == al}
        out[m] = None if bare else attrs
    return {m: v for m, v in out.items() if (SRC / "utils" / f"{m}.py").exists()}


def names_signature(module_src: str | None, names: set | None) -> str | None:
    """Signature of the top-level definitions of `names` in a module, closed over the module-level names they use;
    the whole module when `names` is None."""
    if module_src is None:
        return None
    if names is None:
        return signature(module_src)
    try:
        tree = ast.parse(module_src)
    except SyntaxError:
        return None
    defs: dict[str, list] = {}
    for n in tree.body:
        targets = []
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            targets = [n.name]
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                targets += [x.id for x in ast.walk(t) if isinstance(x, ast.Name)]
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            targets = [(a.asname or a.name).split(".")[0] for a in n.names]
        for t in targets:
            defs.setdefault(t, []).append(n)
    seen, todo = set(), [x for x in names if x in defs]
    while todo:
        x = todo.pop()
        if x in seen:
            continue
        seen.add(x)
        for node in defs[x]:
            todo += [y.id for y in ast.walk(node) if isinstance(y, ast.Name) and y.id in defs and y.id not in seen]
    cl = clean_lines(module_src)
    if cl is None:
        return None
    nodes = sorted({(node.lineno, node.end_lineno) for x in seen for node in defs[x]})
    return _h([l for a, b in nodes for l in cl[a - 1:b]])


def utils_of(src: str) -> list[str]:
    """src/utils modules a script imports (from utils.X import …, import utils.X, from utils import X)."""
    mods = set(re.findall(r"^\s*(?:from|import)\s+utils\.(\w+)", src, re.M))
    for grp in re.findall(r"^\s*from\s+utils\s+import\s+\(?([\w,\s]+)\)?", src, re.M):
        mods.update(m.strip() for m in grp.split(",") if m.strip())
    return sorted(m for m in mods if (SRC / "utils" / f"{m}.py").exists())


def sub_scripts(runner: str, src: str) -> list[str]:
    names = set(re.findall(r'"(\d\d[a-z]?_[a-z0-9_]+?)(?:\.py)?"', src))
    return sorted(f"{n}.py" for n in names if (SRC / f"{n}.py").exists())


def entry(script: str, read) -> dict | None:
    """read(relpath) -> text or None; the signature record of one script and its utils."""
    s = read(f"src/{script}")
    if s is None or signature(s) is None:
        return None
    return {"sig": signature(s), "utils": {f"utils/{m}.py": names_signature(read(f"src/utils/{m}.py"), names)
                                           for m, names in sorted(imported_names(s).items())}}


def _live(rel: str) -> str | None:
    p = REPO / rel
    return p.read_text(encoding="utf-8") if p.is_file() else None


def load() -> dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"scripts": {}}


def save(d: dict) -> None:
    FILE.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def record(scripts: list[str], when: str | None = None) -> list[str]:
    d = load()
    done = []
    when = when or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    todo = list(scripts)
    for s in scripts:
        if s in RUNNERS and _live(f"src/{s}"):
            todo += sub_scripts(s, _live(f"src/{s}"))
    for s in dict.fromkeys(todo):
        e = entry(s, _live)
        if e:
            e["recorded"] = when
            d.setdefault("scripts", {})[s] = e
            done.append(s)
    save(d)
    return done


def differs(script: str, d: dict | None = None) -> list[str] | None:
    rec = (d or load()).get("scripts", {}).get(script)
    if not rec or not (SRC / script).exists():          # nothing recorded, or a retired script
        return None
    now = entry(script, _live)
    if now is None:
        return ["script (does not parse)"]
    out = ["script"] if now["sig"] != rec["sig"] else []
    for m in sorted(set(now["utils"]) | set(rec.get("utils", {}))):
        if now["utils"].get(m) != rec.get("utils", {}).get(m):
            out.append(m)
    return out


def seed() -> None:
    """For each step in provenance, the code as committed at its run START — the code that ran — never today's."""
    prov = json.loads(PROV.read_text(encoding="utf-8")).get("steps", {})
    d = load(); n = skipped = 0
    for step, rec in sorted(prov.items()):
        started = rec.get("started")
        if not started:
            continue
        # The code that ran is the copy carrying the __version__ provenance recorded at run time: usually the last
        # commit before the run, but a batch is often run on uncommitted edits and committed after, so the first
        # commit after the run is the other candidate. Neither carrying it: skipped, and output_lag keeps its clocks.
        git = lambda *a: subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.strip()
        # the TREE at the run: the last commit of any kind before it, or the first after it (a run on uncommitted
        # work) - one commit, so the script, its utils and a runner's sub-scripts are all read as they were together
        before = git("rev-list", "-1", f"--before={started}", "HEAD")
        after = (git("rev-list", "--reverse", f"--since={started}", "HEAD").split() or [""])[0]
        sha = None
        for cand in (before, after):
            if cand and rec.get("version") and re.search(
                    r'^__version__\s*=\s*"' + re.escape(rec["version"]) + '"',
                    git("show", f"{cand}:src/{step}"), re.M):
                sha = cand
                break
        if not sha:
            skipped += 1
            continue
        def at(rel, sha=sha):
            r = subprocess.run(["git", "show", f"{sha}:{rel}"], cwd=REPO, capture_output=True, text=True)
            return r.stdout if r.returncode == 0 else None
        names = [step] + (sub_scripts(step, at(f"src/{step}") or "") if step in RUNNERS else [])
        for s in names:
            e = entry(s, at)
            if e:
                e["recorded"] = f"seed: code at {sha[:8]}, the commit carrying version {rec.get('version')} run at {started}"
                d.setdefault("scripts", {})[s] = e
                n += 1
    save(d)
    print(f"  code_signature: seeded {n} script(s) from the code committed at their recorded run start; "
          f"{skipped} step(s) whose run version no commit carries (left to output_lag's clocks)")


def selftest() -> int:
    a = 'x = 1\n__version__ = "1.0"\ndef f():\n    "doc"\n    return x\n'
    b = 'x = 1\n__version__ = "2.0"\ndef f():\n    "other doc"\n    return x  # comment\n'
    c = 'x = 2\n__version__ = "1.0"\ndef f():\n    return x\n'
    ok = (signature(a) == signature(b) and signature(a) != signature(c)
          and utils_of("from utils.config import A\nimport utils.paths\nfrom utils import (render_utils,\n x)\n")
          == sorted(m for m in ("config", "paths", "render_utils") if (SRC / "utils" / f"{m}.py").exists()))
    print(f"  code_signature --selftest: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(selftest())
    if a[:1] == ["seed"]:
        seed(); sys.exit(0)
    if a[:1] == ["record"] and len(a) > 1:
        print(f"  code_signature: recorded {', '.join(record(a[1:])) or 'nothing'}"); sys.exit(0)
    print(__doc__); sys.exit(2)
