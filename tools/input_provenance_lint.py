#!/usr/bin/env python3
"""input_provenance_lint - do the committed outputs still match the committed INPUTS?

W132. `output_lag` watches the script->output boundary; nothing watched the
input->output boundary, so a raw record could change under a corpus of committed
numbers with every gate green (the D-115 case: Newborough_Cleaned_For_Model.csv
edited under outputs dated three days earlier, check_all entirely green).

run_analysis.py records the SHA-256 + byte length of each REQUIRED_DATA raw input
into outputs/pipeline_manifest.json under `input_provenance`, on a from-step-1
full run (and carries it forward unchanged on --manifest-only / a resume). This
gate recomputes those hashes and fails when a raw input has changed since the run
that produced the committed outputs.

  python tools/input_provenance_lint.py            # report
  python tools/input_provenance_lint.py --gate     # exit 1 on a real mismatch
  python tools/input_provenance_lint.py --selftest # prove the detection works

FIRST-RUN SKIP: until a full run records input_provenance the manifest has no
such key; the gate reports a clean skip ("rerun run_analysis.py to activate") and
never fails on it. It goes live once the key exists.
"""
import argparse
import hashlib
import json
import pathlib
import sys
import tempfile

__version__ = "1.0.0"

REPO = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO / "outputs" / "pipeline_manifest.json"


def _sha256(path):
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def evaluate(provenance, root):
    """(state, rows): state in {'skip','ok','fail'}; rows = [(path, verdict, detail)]."""
    if not provenance:
        return "skip", []
    rows = []
    state = "ok"
    for rel, rec in sorted(provenance.items()):
        recorded = rec.get("sha256")
        now = _sha256(root / rel)
        if now is None:
            rows.append((rel, "MISSING", "recorded but not on disk")); state = "fail"
        elif recorded is None:
            rows.append((rel, "NO-BASELINE", "input was unreadable at run time")); state = "fail"
        elif now == recorded:
            rows.append((rel, "OK", now[:8]))
        else:
            rows.append((rel, "CHANGED", "recorded %s, now %s" % (recorded[:8], now[:8]))); state = "fail"
    return state, rows


def load_manifest():
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return None


def selftest():
    ok = True
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "data").mkdir()
        f = root / "data" / "x.csv"
        f.write_text("alpha\n")
        rec = {"data/x.csv": {"sha256": hashlib.sha256(b"alpha\n").hexdigest(), "bytes": 6}}
        cases = []
        st, _ = evaluate(rec, root); cases.append(("clean match", st == "ok"))
        f.write_text("beta\n")
        st, _ = evaluate(rec, root); cases.append(("mutated input caught", st == "fail"))
        st, _ = evaluate(None, root); cases.append(("absent provenance -> skip", st == "skip"))
        f.unlink()
        st, _ = evaluate(rec, root); cases.append(("missing input caught", st == "fail"))
    for name, good in cases:
        print("  %-4s %s" % ("ok" if good else "BAD", name))
        ok = ok and good
    print("  input_provenance_lint --selftest: %d case(s), %s"
          % (len(cases), "all correct" if ok else "FAILURES"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true", help="exit 1 on a real mismatch")
    ap.add_argument("--selftest", action="store_true", help="prove the detection works")
    args = ap.parse_args()
    if args.selftest:
        return 0 if selftest() else 1
    m = load_manifest()
    if m is None:
        print("  input_provenance_lint: no manifest at %s" % MANIFEST)
        return 1 if args.gate else 0
    state, rows = evaluate(m.get("input_provenance"), REPO)
    if state == "skip":
        print("  input_provenance_lint: no input provenance recorded yet - "
              "rerun run_analysis.py --full to activate (W132)")
        return 0
    for rel, verdict, detail in rows:
        print("  %-11s %s  %s" % (verdict, rel, detail))
    if state == "ok":
        print("  input_provenance_lint: OK - %d raw input(s) match the committed manifest" % len(rows))
        return 0
    print("  input_provenance_lint: FAIL - a raw input changed since the run that "
          "produced the committed outputs; rerun run_analysis.py")
    return 1 if args.gate else 0


if __name__ == "__main__":
    sys.exit(main())
