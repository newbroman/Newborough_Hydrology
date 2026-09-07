#!/usr/bin/env python3
"""
provenance_lint — was each committed output produced from the upstream that is
committed now, and without falling back on a documented default? (S1; D-133 extended)

What it reads: outputs/pipeline_provenance.json, written by run_analysis 2.15.0 around
every step — per step, the SHA-256 of the declared inputs at run time, the SHA-256 of
every file the step changed, and the fallbacks pipeline_params served.

Checks:
  1. STALE UPSTREAM (gate). A recorded input's hash differs from the file committed now.
     The step's outputs were computed from something that has since changed; the remedy
     is to re-run from that step — named in the message, per D-102's rule that the fix
     is the re-run, never skipping the check.
  2. FALLBACK IN A COMMITTED OUTPUT (gate). The step served a documented default in
     place of a live upstream value (a first pass). "Provisional" was prose; this is the
     field. Remedy: run the second pass.
  3. EMITTED vs LEDGER (advisory). Files the step actually wrote that its SCRIPT_LEDGER
     Emits cells do not name, and vice versa — the measured record shows where the
     declared one has drifted. Counted, never red: the ledger's own backlog.

Skips cleanly (exit 0, says so) until the first run on 2.15.0 has written the file, as
input_provenance_lint does before its block exists.

Usage:
    python3 tools/provenance_lint.py             # report; exit 1 on a gate fault
    python3 tools/provenance_lint.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-07. First issue (S1 spec).

import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROV = REPO / "outputs" / "pipeline_provenance.json"
sys.path.insert(0, str(REPO / "tools"))

_FILE_TOKEN = re.compile(r"[\w./-]+\.(?:csv|json|geojson|kml|kmz|tif|tiff|png|jpg|txt|parquet)\b")


def sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def ledger_emits() -> dict[str, set[str]]:
    """{script: set of basenames the ledger says it emits} via ledger_lint's parser."""
    try:
        from ledger_lint import rows, LEDGER
        out = {}
        for r in rows(LEDGER.read_text(encoding="utf-8")):
            cells = r["cells"]
            names = set()
            for i in (4, 5):
                if len(cells) > i:
                    names.update(Path(t).name for t in _FILE_TOKEN.findall(cells[i]))
            out[r["script"]] = names
        return out
    except Exception:
        return {}


def evaluate(prov: dict, current_sha, emits_by_script: dict) -> tuple[list[str], list[str], list[str]]:
    """(gate faults, fallback faults, advisories). `current_sha(rel) -> sha | None`."""
    stale, fallbacks, advisory = [], [], []
    for script, rec in sorted(prov.get("steps", {}).items()):
        for rel, recorded in sorted(rec.get("inputs", {}).items()):
            now = current_sha(rel)
            if now is None:
                stale.append(f"{script}: input {rel} recorded at run time is now MISSING")
            elif now != recorded:
                stale.append(f"{script}: produced from {rel} which has since changed — "
                             f"re-run from this step")
        fb = rec.get("fallbacks") or []
        if fb:
            keys = sorted({str(f.get("key")) for f in fb})
            fallbacks.append(f"{script}: rests on documented default(s) {', '.join(keys)} "
                             f"— run the second pass")
        if script in emits_by_script:
            measured = {Path(p).name for p in rec.get("emitted", {})}
            declared = emits_by_script[script]
            extra = sorted(measured - declared)
            missing = sorted(declared - measured)
            if extra:
                advisory.append(f"{script}: wrote {len(extra)} file(s) the ledger does not list "
                                f"({', '.join(extra[:4])}{'…' if len(extra) > 4 else ''})")
            if missing:
                advisory.append(f"{script}: ledger lists {len(missing)} file(s) this run did not write "
                                f"({', '.join(missing[:4])}{'…' if len(missing) > 4 else ''})")
    return stale, fallbacks, advisory


def selftest() -> int:
    prov = {"steps": {
        "17_x.py": {"inputs": {"outputs/a.csv": "AAA"}, "emitted": {"outputs/17/17_01.csv": "E1"},
                    "fallbacks": []},
        "20_y.py": {"inputs": {"outputs/17/17_01.csv": "E1"}, "emitted": {"outputs/20/20_01.csv": "F"},
                    "fallbacks": [{"key": "Sy", "source": "default_value", "script": "20_y.py"}]},
    }}
    good = {"outputs/a.csv": "AAA", "outputs/17/17_01.csv": "E1"}
    emits = {"17_x.py": {"17_01.csv", "17_02.png"}, "20_y.py": {"20_01.csv"}}
    bad = []
    s, f, a = evaluate(prov, lambda r: good.get(r), emits)
    if s:
        bad.append(f"clean inputs reported stale: {s}")
    if len(f) != 1 or "20_y.py" not in f[0] or "Sy" not in f[0]:
        bad.append(f"fallback not reported: {f}")
    if not any("17_02.png" in x for x in a):
        bad.append(f"ledger drift not advised: {a}")
    s, _, _ = evaluate(prov, lambda r: {**good, "outputs/17/17_01.csv": "CHANGED"}.get(r), emits)
    if not any("20_y.py" in x and "re-run" in x for x in s):
        bad.append(f"stale upstream not detected: {s}")
    s, _, _ = evaluate(prov, lambda r: {"outputs/17/17_01.csv": "E1"}.get(r), emits)
    if not any("MISSING" in x for x in s):
        bad.append("missing input not detected")
    if bad:
        print("provenance_lint --selftest: FAIL")
        for b in bad:
            print(f"    - {b}")
        return 1
    print("provenance_lint --selftest: OK")
    return 0


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()
    if not PROV.is_file():
        print("  provenance_lint: skip — outputs/pipeline_provenance.json not yet written "
              "(first run on run_analysis >= 2.15.0 records it)")
        return 0
    try:
        prov = json.loads(PROV.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"provenance_lint: FAULT — {PROV.relative_to(REPO)} unreadable ({exc})")
        return 1
    stale, fallbacks, advisory = evaluate(prov, lambda rel: sha256(REPO / rel), ledger_emits())
    n = len(prov.get("steps", {}))
    print(f"  {n} step(s) recorded by orchestrator {prov.get('orchestrator')} "
          f"(last {prov.get('generated')})")
    for a in advisory:
        print(f"  note  {a}")
    if advisory:
        print(f"  {len(advisory)} ledger Emits drift(s) — advisory, the measured record vs the declared one")
    if stale or fallbacks:
        print("provenance_lint: FAULT")
        for x in stale + fallbacks:
            print(f"    - {x}")
        return 1
    print("provenance_lint: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
