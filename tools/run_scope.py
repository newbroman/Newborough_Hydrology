#!/usr/bin/env python3
"""run_scope.py — run only the pipeline steps a change reaches (D-340, draft; Martin 2026-11-24: "build it").

A full `run_analysis.py --full --with-supplementary` takes about three hours. Most changes touch a few scripts whose
outputs a handful of later steps read. Every full run records, per step, the files it read and the files it wrote
with their hashes (outputs/pipeline_provenance.json), and the code each step ran (outputs/pipeline_code_signatures.json).
That is enough to run just what a change reaches - IF the propagation follows what actually changed:

    SEEDS    every step whose code signature differs from the one recorded (tools/code_signature.differs), every
             step with a recorded input whose file has changed since (stale upstream), and any --changed script.
    PASS     in pipeline order, run a step when it is a seed or reads a file a step of this pass CHANGED (by
             hash, after re-running). A step whose outputs come back byte-identical wakes nobody.
    LOOPS    the pipeline has deliberate backward reads (Script 01 reads 03, 06, 18 and 10e outputs; the settle
             passes of run_analysis 2.x). A file changed late that an EARLIER step reads starts another pass, at
             most SETTLE_MAX_PASSES (run_analysis), exactly as the full run settles.
    REFUSAL  a scoped run that would re-run Script 01 or 03 - the data preparation and the model every later step
             rests on - refuses and says to run the full pipeline (--allow-core overrides, on Martin's word).
    SHARED   a file written by more than one step (the site-observations ledger, the scenario-params ledger) is a
             record of the pass, not a dependency, and never wakes a step.

Every step runs through `run_analysis.py --step`, so provenance, code signatures and the site-observations token
are recorded exactly as in a full run; all steps of one scoped run share one NRG_RUN_ID (run_analysis 2.33.0 takes
NRG_RUN_SCOPE_ID). What a scoped run does NOT replace: the gates. check_all's output_lag, step provenance and runid
sections judge the result exactly as they judge a full run's.

    python3 tools/run_scope.py                    # the plan: seeds, the static reach, the loops, the estimate
    python3 tools/run_scope.py --changed 16 20    # plan with extra seeds (script keys or filenames)
    python3 tools/run_scope.py --run              # run it; record to scratch/run_scope_<stamp>.json
    python3 tools/run_scope.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.2"  # Hollingham (2026) — 2026-11-24. A step whose own output it also reads (run_10 over
#   10a_report_numbers.csv) settles once more when that output changed, as the full run's settle does. 1.0.1 skipped it,
#   and check_all's step provenance caught it on the first real scoped run ("produced from ... which has since changed").
# 1.0.1  # Hollingham (2026) — 2026-11-24. An "ondemand" step (27_greyscale_figures.py) is left out of
#   the order, as the full run leaves it out; 1.0.0's unrecorded-step refusal fired on it on the first real plan.
# 1.0.0  # Hollingham (2026) — 2026-11-24. New (D-340): scoped runs by measured provenance.

import argparse
import collections
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import uuid

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
PROV = REPO / "outputs" / "pipeline_provenance.json"
RUNNER = REPO / "run_analysis.py"
CORE = {"01_data_prep.py", "03_state_space_model.py"}
SETTLE_DEFAULT = 2


# ── the graph ─────────────────────────────────────────────────────────────────────────────────────
def pipeline_order(src: str | None = None) -> list[str]:
    """Registered steps in run order, read from run_analysis.py's Step(...) table (no import: it builds menus)."""
    src = src if src is not None else RUNNER.read_text(encoding="utf-8")
    # an "ondemand" step (27_greyscale_figures.py) is outside the full run by design, so outside a scoped one too
    return [m.group(1) for m in re.finditer(r'Step\("([^"]+\.py)"[^\n]*', src)
            if '"ondemand"' not in m.group(0)]


def settle_passes(src: str | None = None) -> int:
    src = src if src is not None else RUNNER.read_text(encoding="utf-8")
    m = re.search(r"^SETTLE_MAX_PASSES\s*=\s*(\d+)", src, re.M)
    return int(m.group(1)) if m else SETTLE_DEFAULT


def load_prov(path: pathlib.Path = PROV) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    return d.get("steps", d)


def shared_files(steps: dict) -> set[str]:
    c = collections.Counter(f for r in steps.values() for f in r.get("emitted", {}))
    return {f for f, n in c.items() if n > 1}


def readers(steps: dict, shared: set[str]) -> dict[str, set[str]]:
    """file -> the steps that read it (shared ledgers excluded). An input the recorder could not place
    (inputs_unresolved: a bare name such as 'wet_area_model.json') counts as reading every emitted file of that name,
    so it still wakes its step - erring toward running, never toward missing."""
    out = collections.defaultdict(set)
    by_name = collections.defaultdict(set)
    for r in steps.values():
        for f in r.get("emitted", {}):
            by_name[pathlib.PurePosixPath(f).name].add(f)
    for st, r in steps.items():
        for f in r.get("inputs", {}):
            if f not in shared:
                out[f].add(st)
        for name in r.get("inputs_unresolved") or []:
            for f in by_name.get(pathlib.PurePosixPath(str(name)).name, ()):
                if f not in shared:
                    out[f].add(st)
    return out


def sha(path: pathlib.Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def _same(recorded: str, now: str | None) -> bool:
    return now is not None and (recorded == now or recorded.endswith(now) or now.endswith(recorded))


# ── seeds ─────────────────────────────────────────────────────────────────────────────────────────
def code_seeds(order: list[str]) -> dict[str, str]:
    try:
        import code_signature
    except ImportError:
        return {}
    sigs = code_signature.load()
    out = {}
    for s in order:
        moved = code_signature.differs(s, sigs)
        if moved:
            out[s] = "code changed: " + ", ".join(moved)
            continue
        # a runner (run_09, run_10) is one step; its sub-scripts carry signatures of their own
        src = REPO / "src" / s
        if s.startswith("run_") and src.is_file():
            subs = [x for x in code_signature.sub_scripts(s, src.read_text(encoding="utf-8"))
                    if code_signature.differs(x, sigs)]
            if subs:
                out[s] = "code changed in " + ", ".join(subs)
    return out


def stale_seeds(steps: dict, order: list[str], root: pathlib.Path = REPO) -> dict[str, str]:
    shared = shared_files(steps)      # a pass ledger changes every run; it is a record, not a dependency
    out = {}
    for s in order:
        for f, h in steps.get(s, {}).get("inputs", {}).items():
            if f in shared:
                continue
            if not _same(h, sha(root / f)):
                out[s] = f"input changed since it ran: {f}"
                break
    return out


def resolve(keys: list[str], order: list[str]) -> dict[str, str]:
    out = {}
    for k in keys:
        k2 = k.strip().lower()
        hits = [s for s in order if s.lower() == k2 or s.lower().startswith(k2 + "_") or s.lower() == k2 + ".py"
                or (k2.isdigit() and s.startswith(f"{int(k2):02d}_"))]
        if k2 in ("10", "10a", "10b", "10c", "10d", "10e", "10f", "10g", "10h", "10i", "10j", "10k", "10l", "10m"):
            hits = [s for s in order if s.startswith("run_10")]
        if k2.startswith("09") and len(k2) == 3 and k2[2] in "abcde":
            hits = [s for s in order if s.startswith("run_09")]
        if len(hits) != 1:
            raise SystemExit(f"run_scope: --changed {k!r} matches {len(hits)} step(s)")
        out[hits[0]] = "named with --changed"
    return out


# ── the plan (static) ─────────────────────────────────────────────────────────────────────────────
def static_reach(seeds: set[str], steps: dict, order: list[str]) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Forward reach in pipeline order (an upper bound: assumes every output of a reached step changes), and the
    loop edges it touches (a reached step's file read by an EARLIER step) - those decide whether a settle pass runs."""
    pos = {s: i for i, s in enumerate(order)}
    shared = shared_files(steps)
    rd = readers(steps, shared)
    reach, stack, loops = set(seeds), list(seeds), []
    while stack:
        s = stack.pop()
        for f in steps.get(s, {}).get("emitted", {}):
            for r in rd.get(f, ()):
                if r == s or r not in pos or s not in pos:
                    continue
                if pos[r] > pos[s]:
                    if r not in reach:
                        reach.add(r)
                        stack.append(r)
                else:
                    loops.append((r, s, f))
    return sorted(reach, key=lambda s: pos.get(s, 999)), sorted(set(loops))


def minutes(steps: dict, names) -> float:
    return sum((steps.get(s, {}).get("seconds") or 0) for s in names) / 60


# ── the run (dynamic) ─────────────────────────────────────────────────────────────────────────────
def run_step(script: str, env: dict) -> int:
    key = script[:-3]
    return subprocess.call([sys.executable, str(RUNNER), "--step", key], cwd=REPO, env=env)


def execute(seeds: dict[str, str], order: list[str], allow_core: bool, runner=run_step,
            prov_path: pathlib.Path = PROV, root: pathlib.Path = REPO, settle: int | None = None) -> dict:
    """Run in pipeline order; wake a step only on a file that actually changed. Returns the record."""
    settle = settle_passes() if settle is None else settle
    steps = load_prov(prov_path)
    shared = shared_files(steps)
    pos = {s: i for i, s in enumerate(order)}
    token = f"run:{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}-scope-{uuid.uuid4().hex[:6]}"
    env = dict(os.environ, NRG_RUN_SCOPE_ID=token)
    rec = {"tool": f"run_scope {__version__}", "token": token, "seeds": seeds, "passes": [], "refused": None}
    pending = dict(seeds)          # step -> why
    for p in range(settle + 1):
        if not pending:
            break
        ran, changed = [], set()
        for s in order:
            steps = load_prov(prov_path)
            rd = readers(steps, shared)
            wake = sorted(f for f in changed if s in rd.get(f, ()))
            why = pending.pop(s, None) or (f"reads {wake[0]}" + (f" (+{len(wake) - 1})" if len(wake) > 1 else "")
                                           if wake else None)
            if not why:
                continue
            if s in CORE and not allow_core:
                rec["refused"] = f"{s} would re-run ({why}): Script 01 or 03 changes the ground every step stands on; run the full pipeline"
                return rec
            before = {f: h for f, h in steps.get(s, {}).get("emitted", {}).items()}
            print(f"  run_scope: pass {p + 1}, {s} — {why}", flush=True)
            rc = runner(s, env)
            if rc != 0:
                rec["passes"].append({"pass": p + 1, "ran": ran + [{"step": s, "why": why, "rc": rc}]})
                rec["failed"] = s
                return rec
            after = load_prov(prov_path).get(s, {}).get("emitted", {})
            moved = sorted(f for f in set(before) | set(after)
                           if f not in shared and before.get(f) != after.get(f))
            changed |= set(moved)
            ran.append({"step": s, "why": why, "rc": rc, "changed": moved})
        rec["passes"].append({"pass": p + 1, "ran": ran})
        # a file changed in this pass that an EARLIER step reads: that step goes again (the settle)
        steps = load_prov(prov_path)
        late = {}
        rd = readers(steps, shared)
        for r in order:
            for f in sorted(x for x in changed if r in rd.get(x, ())):
                if True:
                    prod = next((x["step"] for x in ran if f in x["changed"]), None)
                    # r == prod is a step that reads its own previous output (run_10 consolidates over
                    # 10a_report_numbers.csv): the full run's settle pass re-runs it once, and so must this (1.0.2)
                    if prod and pos.get(r, 0) <= pos.get(prod, 0) and r not in late:
                        late[r] = f"settle: reads {f}, changed later in the pass by {prod}"
        pending = late
    if pending:
        rec["unsettled"] = pending
    return rec


# ── selftest ──────────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    import tempfile
    ok = True
    src = ('Step("01_a.py", "x", "A"),\nStep("02_b.py", "x", "A"),\nStep("03_c.py", "x", "A"),\nStep("04_d.py", "x", "A"),\n'
           'Step("27_g.py", "on demand only", "D", "ondemand"),\nSETTLE_MAX_PASSES = 2\n')
    order = pipeline_order(src)
    ok &= order == ["01_a.py", "02_b.py", "03_c.py", "04_d.py"] and settle_passes(src) == 2
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        files = {n: t / n for n in ("a.csv", "b.csv", "c.csv", "d.csv", "ledger.csv")}
        for f in files.values():
            f.write_text("0")
        H = lambda n: sha(files[n])  # noqa: E731
        prov = {"steps": {
            "01_a.py": {"inputs": {"c.csv": H("c.csv")}, "emitted": {"a.csv": H("a.csv"), "ledger.csv": "x"}},
            "02_b.py": {"inputs": {"a.csv": H("a.csv")}, "emitted": {"b.csv": H("b.csv"), "ledger.csv": "x"}},
            "03_c.py": {"inputs": {"b.csv": H("b.csv")}, "emitted": {"c.csv": H("c.csv")}},
            "04_d.py": {"inputs": {"a.csv": H("a.csv")}, "emitted": {"d.csv": H("d.csv")}}}}
        pp = t / "prov.json"
        pp.write_text(json.dumps(prov))
        st = load_prov(pp)
        ok &= shared_files(st) == {"ledger.csv"}
        reach, loops = static_reach({"02_b.py"}, st, order)
        ok &= reach == ["02_b.py", "03_c.py"] and loops == [("01_a.py", "03_c.py", "c.csv")]

        def fake(changes):
            done = set()                   # a deterministic step writes the same bytes the second time

            def runner(s, env):
                d = json.loads(pp.read_text())
                first = s not in done
                done.add(s)
                for f in (changes.get(s, []) if first else []):
                    (t / f).write_text((t / f).read_text() + "1")
                    d["steps"][s]["emitted"][f] = sha(t / f)
                for f in d["steps"][s]["inputs"]:
                    d["steps"][s]["inputs"][f] = sha(t / f)
                pp.write_text(json.dumps(d))
                return 0
            return runner
        # 02 changes b -> 03 runs and changes nothing: 04 never runs, no settle
        r1 = execute({"02_b.py": "seed"}, order, True, runner=fake({"02_b.py": ["b.csv"]}), prov_path=pp, root=t)
        ran1 = [x["step"] for x in r1["passes"][0]["ran"]]
        ok &= ran1 == ["02_b.py", "03_c.py"] and len(r1["passes"]) == 1
        # 03 changes c -> 01 (earlier) reads c: a settle pass runs 01; the core refusal stops it without allow_core
        pp.write_text(json.dumps(prov))
        r2 = execute({"03_c.py": "seed"}, order, False, runner=fake({"03_c.py": ["c.csv"]}), prov_path=pp, root=t)
        ok &= r2["refused"] is None and "unsettled" not in r2 and len(r2["passes"]) == 2 \
            and r2["passes"][1]["ran"][0]["step"] == "01_a.py"
        # a step that reads its own output (05 reads e.csv, writes e.csv): changed -> one settle pass of itself
        pe = t / "e.csv"; pe.write_text("0")
        order5 = order + ["05_e.py"]
        prov5 = json.loads(json.dumps(prov)); prov5["steps"]["05_e.py"] = {"inputs": {"e.csv": sha(pe)},
                                                                             "emitted": {"e.csv": sha(pe)}}
        pp.write_text(json.dumps(prov5))
        r4 = execute({"05_e.py": "seed"}, order5, True, runner=fake({"05_e.py": ["e.csv"]}), prov_path=pp, root=t)
        ok &= len(r4["passes"]) == 2 and r4["passes"][1]["ran"][0]["step"] == "05_e.py"
    # an unresolved bare name still wakes its reader
    st2 = {"45_x.py": {"inputs": {}, "emitted": {"living/wet_area_model.json": "h"}},
           "19_y.py": {"inputs": {}, "inputs_unresolved": ["wet_area_model.json"], "emitted": {}}}
    ok &= readers(st2, set()).get("living/wet_area_model.json") == {"19_y.py"}
    # the core refusal, on the real names
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        pp = t / "prov.json"
        pp.write_text(json.dumps({"steps": {"01_data_prep.py": {"inputs": {}, "emitted": {}}}}))
        r3 = execute({"01_data_prep.py": "seed"}, ["01_data_prep.py"], False, runner=lambda s, e: 0, prov_path=pp)
        ok &= bool(r3["refused"])
    print(f"  run_scope --selftest: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


# ── main ──────────────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--changed", nargs="*", default=[], help="extra seed steps (script keys or filenames)")
    ap.add_argument("--run", action="store_true", help="run the scoped pass (default: print the plan)")
    ap.add_argument("--allow-core", action="store_true", help="let Script 01 or 03 re-run (Martin's word only)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    order = pipeline_order()
    steps = load_prov()
    seeds = {**stale_seeds(steps, order), **code_seeds(order), **resolve(a.changed, order)}
    reach, loops = static_reach(set(seeds), steps, order)
    print(f"run_scope {__version__}: {len(seeds)} seed step(s); static reach {len(reach)} of {len(order)} steps, "
          f"~{minutes(steps, reach):.0f} of ~{minutes(steps, order):.0f} min (an upper bound: assumes every output of "
          f"a reached step changes)")
    for s, why in sorted(seeds.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 999):
        print(f"  seed   {s:38} {why}")
    for s in reach:
        if s not in seeds:
            print(f"  reach  {s}")
    if loops:
        print(f"  {len(loops)} loop edge(s) - an earlier step reads a reached step's file; a settle pass runs only "
              f"if that file actually changes:")
        for r, p, f in loops[:12]:
            print(f"    {r} <- {p}: {f}")
    core = sorted(CORE & set(reach))
    if core:
        print(f"  NOTE: {', '.join(core)} in the reach — a run will refuse there unless --allow-core")
    unrecorded = [s for s in order if s not in steps]
    if unrecorded:
        print(f"  NOTE: {len(unrecorded)} registered step(s) have no provenance record ({', '.join(unrecorded[:5])}"
              f"{'…' if len(unrecorded) > 5 else ''}) — the plan cannot see what they read; a run refuses (D-340 rule 2)")
    if not a.run:
        return 0
    if unrecorded:
        print("run_scope: REFUSED — the step list has changed since the last full run; run the full pipeline")
        return 1
    if not seeds:
        print("run_scope: nothing to run")
        return 0
    rec = execute(seeds, order, a.allow_core)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    out = REPO / "scratch" / f"run_scope_{stamp}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    n = sum(len(p["ran"]) for p in rec["passes"])
    if rec.get("refused"):
        print(f"run_scope: REFUSED — {rec['refused']}  ({out.relative_to(REPO)})")
        return 1
    if rec.get("failed"):
        print(f"run_scope: FAILED at {rec['failed']} after {n} step(s)  ({out.relative_to(REPO)})")
        return 1
    print(f"run_scope: ran {n} step(s) in {len(rec['passes'])} pass(es)"
          + (f"; UNSETTLED {sorted(rec['unsettled'])}" if rec.get("unsettled") else "")
          + f"  ({out.relative_to(REPO)}). Now: bash tools/check_all.sh")
    return 1 if rec.get("unsettled") else 0


if __name__ == "__main__":
    sys.exit(main())
