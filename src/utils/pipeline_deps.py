"""
pipeline_deps.py — static down-pipeline dependency auditor for the
Newborough Warren analytical pipeline (Hollingham 2026).

A *down-pipeline* (backward) dependency is a script that READS an output
which is PRODUCED by a script running at a LATER execution step. On a fresh
first-pass run that output does not yet exist, so the reader either falls
back (if guarded) or crashes (if not). This module finds every such case by
static analysis — no scripts are executed and nothing is imported.

How producers are resolved
--------------------------
Outputs follow the naming convention OUT_<NN>[<letter>]_* (produced by script
NN[letter]). That convention is authoritative because several scripts write
through a local alias (e.g. ``OUT_5YR = paths.OUT_26_5YR_PER_WELL`` then
``df.to_csv(OUT_5YR)``), which a write-call scan alone would miss. For
INT_* intermediates that carry no script number in the name, the producer is
taken from whichever script writes the constant.

Usage
-----
    from utils.pipeline_deps import build_dependencies, print_audit, notes_for_step
    deps = build_dependencies(SRC_DIR, step_map=_STEP_MAP)   # step_map optional
    print_audit(deps)                       # full report
    for msg in notes_for_step(30, deps):    # contextual warnings for a step
        print(msg)

Or standalone:  python -m utils.pipeline_deps  /path/to/src
"""
from __future__ import annotations
import ast, re, sys
from collections import namedtuple
from pathlib import Path

Dep = namedtuple("Dep",
    "const producer producer_step reader reader_step gap guarded")

_WRITE_FUNCS = {"to_csv","savefig","write_text","write_bytes","to_parquet",
                "imwrite","save","to_excel"}
_READ_FUNCS  = {"read_csv","read_parquet","read_excel","load","read_text",
                "read_bytes","exists","imread","is_file"}
# sub-script suites map to their orchestrated parent step
_SUITE = {**{f"09{c}_": "run_09_scraping.py"  for c in "abcde"},
          **{f"10{c}_": "run_10_clearfell.py" for c in "abcdefghijkl"}}


def _constants(src: Path) -> set[str]:
    txt = (src / "utils" / "paths.py").read_text()
    return {c for c in re.findall(r'^([A-Z][A-Z0-9_]+)\s*=', txt, re.M)
            if c.startswith(("OUT_", "INT_"))}


def _consts_in(node, consts):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id in consts:
            out.add(n.id)
        elif isinstance(n, ast.Attribute) and n.attr in consts:
            out.add(n.attr)
    return out


def _scan(src: Path, consts):
    """Return reads{const:{script}}, writes{const:{script}}, guarded{(script,const)}."""
    reads, writes, guarded = {}, {}, set()
    for f in sorted(src.glob("*.py")):
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        # consts that appear inside a try-block or an .exists()/.is_file() test
        guard_consts = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                guard_consts |= _consts_in(node, consts)
            if isinstance(node, ast.Call):
                fn = node.func
                fname = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                if fname in ("exists", "is_file"):
                    guard_consts |= _consts_in(node, consts)
        for c in guard_consts:
            guarded.add((f.name, c))
        # read / write classification by call target
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            fname = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            cs = _consts_in(node, consts)
            if not cs:
                continue
            if fname in _READ_FUNCS:
                for c in cs:
                    reads.setdefault(c, set()).add(f.name)
            elif fname in _WRITE_FUNCS:
                for c in cs:
                    writes.setdefault(c, set()).add(f.name)
    return reads, writes, guarded


def _producer(const, scripts, writes):
    m = re.match(r'^OUT_(\d+)([A-Z]?)_', const)
    if m:
        pref = f"{m.group(1)}{m.group(2).lower()}_"
        cand = [s for s in scripts if s.startswith(pref)]
        if cand:
            return cand[0]
    d = writes.get(const)
    return sorted(d)[0] if d else None


def _step_map_from_run_analysis(src: Path):
    txt = (src / "run_analysis.py").read_text()
    return {s: int(n) for s, n in
            re.findall(r'\("([\w.]+\.py)",\s*"\s*(\d+)/\d+', txt)}


def _exec_step(script, step_of_script):
    if script in step_of_script:
        return step_of_script[script]
    for pre, parent in _SUITE.items():
        if script.startswith(pre):
            return step_of_script.get(parent)
    return None


def build_dependencies(src: Path, step_map=None):
    """Return a sorted list of down-pipeline Dep records (largest gap first)."""
    src = Path(src)
    scripts = sorted(p.name for p in src.glob("*.py"))
    consts = _constants(src)
    reads, writes, guarded = _scan(src, consts)
    # accept run_analysis's own {step:(script,...)} map or a {script:step} map
    if step_map and all(isinstance(k, int) for k in step_map):
        step_of = {v[0]: k for k, v in step_map.items()}
    elif step_map:
        step_of = dict(step_map)
    else:
        step_of = _step_map_from_run_analysis(src)

    deps = []
    for const, readers in reads.items():
        prod = _producer(const, scripts, writes)
        if not prod:
            continue
        ps = _exec_step(prod, step_of)
        for r in sorted(readers):
            if r == prod:
                continue
            rs = _exec_step(r, step_of)
            if rs is not None and ps is not None and rs < ps:
                deps.append(Dep(const, prod, ps, r, rs, ps - rs,
                                (r, const) in guarded))
    deps.sort(key=lambda d: (-d.gap, d.producer, d.reader))
    return deps


def print_audit(deps, out=print):
    if not deps:
        out("No down-pipeline dependencies found — pipeline is strictly ordered.")
        return
    out(f"{len(deps)} DOWN-PIPELINE DEPENDENCY(IES) "
        "(a script reads an output produced by a LATER step):\n")
    for d in deps:
        guard = "guarded fallback" if d.guarded else "UNGUARDED — hard-fails on first pass"
        out(f"  step {d.reader_step:>2}  {d.reader}")
        out(f"           reads {d.const}")
        out(f"           produced by step {d.producer_step:>2} {d.producer} "
            f"(+{d.gap} steps downstream)  [{guard}]\n")


def notes_for_step(step, deps):
    """Contextual lines to show when a user runs `step`."""
    msgs = []
    # this step produces things consumed earlier
    consumed = [d for d in deps if d.producer_step == step]
    if consumed:
        who = ", ".join(f"{d.reader} (step {d.reader_step})" for d in consumed)
        msgs.append(f"[deps] This step's outputs are consumed earlier by: {who}. "
                    f"On a fresh tree those steps used fallbacks — re-run them "
                    f"after this step for final figures.")
    # this step consumes something not yet produced
    waiting = [d for d in deps if d.reader_step == step]
    for d in waiting:
        kind = "falls back" if d.guarded else "WILL FAIL (unguarded)"
        msgs.append(f"[deps] This step reads {d.const} from {d.producer} "
                    f"(step {d.producer_step}); if that hasn't run yet it {kind}.")
    return msgs


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    deps = build_dependencies(src)
    print_audit(deps)
    print("--- contextual note example: running step 30 (script 26) ---")
    for m in notes_for_step(30, deps):
        print(m)
