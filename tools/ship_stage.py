#!/usr/bin/env python3
"""ship_stage.py — what did the ship's regenerate step change, and was each change asked for? (D-326, T-203)

D-213 made `ship_regenerate()` rebuild every derived artefact before check_all, so on the only path that reaches
GitHub seventeen gates are satisfied by construction: the regenerate writes, the gate reads what it just wrote
(fault 1 of 2026-11-08 — a false manifest line, read back as true). D-326: the signal was never the rebuild, it
is WHAT THE REBUILD CHANGED, and nothing showed that. This is the comparison.

It is a content snapshot rather than a second tree: the twenty-odd tools ship_regenerate runs all write in place,
and taking the tree's hashes before and after gives the same evidence — every byte the regenerate moved, against
the state the ship started from — without teaching each tool a staging path.

    python3 tools/ship_stage.py snapshot OUT.json            before ship_regenerate
    python3 tools/ship_stage.py diff OUT.json [--request R]  after it: print every changed file with a diff summary;
                                                             FAIL (exit 1) when a change falls under a claim the
                                                             request does not declare (doc_lock.claim_for_path)
    python3 tools/ship_stage.py --selftest

WHAT COUNTS AS EXPLAINED. A changed derived file under a CLAIM is explained only when the ship request lists that
claim, or names the path in `paths`: a PaperM ship that moves the Methods Supplement's mirror or manifest line has
changed something nobody asked it to (D-326's own example, v2_0_127 -> v2_0_128 under a PDF it had not rebuilt).
Files under no claim — the ledgers, the HANDOFF, DECISIONS_PUBLIC, the chat corpus — are shown and allowed: every
ship rebuilds them. With no request (Martin by hand, `--ship-all`), everything is shown and nothing refused.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-24. New (T-203, D-326).

import hashlib
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
SHOW_LINES = 6          # diff lines shown per text file
SHOW_FILES = 40         # files listed in full before summarising


def tree_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=REPO,
                         capture_output=True, text=True).stdout
    return sorted(p for p in out.split("\0") if p and (REPO / p).is_file())


def snapshot() -> dict:
    snap = {}
    for p in tree_files():
        b = (REPO / p).read_bytes()
        snap[p] = {"sha256": hashlib.sha256(b).hexdigest(),
                   "text": None if b"\0" in b[:8192] or len(b) > 2_000_000 else b.decode("utf-8", "replace")}
    return snap


def changes(before: dict, after: dict) -> list[tuple[str, str]]:
    out = []
    for p in sorted(set(before) | set(after)):
        if p not in after:
            out.append((p, "deleted"))
        elif p not in before:
            out.append((p, "new"))
        elif before[p]["sha256"] != after[p]["sha256"]:
            out.append((p, "changed"))
    return out


def summary(p: str, kind: str, before: dict, after: dict) -> list[str]:
    if kind != "changed" or before[p]["text"] is None or after[p]["text"] is None:
        return []
    import difflib
    d = [l for l in difflib.unified_diff(before[p]["text"].splitlines(), after[p]["text"].splitlines(),
                                         lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    plus, minus = sum(l.startswith("+") for l in d), sum(l.startswith("-") for l in d)
    return [f"+{plus} -{minus}"] + [l[:150] for l in d[:SHOW_LINES]]


def request(path: str | None) -> dict | None:
    if not path or not pathlib.Path(path).is_file():
        return None
    t = pathlib.Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(t)
    except ValueError:
        r = {}
        for line in t.splitlines():
            if ":" in line or "=" in line:
                k, _, v = line.replace("=", ":", 1).partition(":")
                r[k.strip()] = v.strip()
        return r


def unexplained(chg: list[tuple[str, str]], req: dict | None, claim_for=None) -> list[tuple[str, str]]:
    if not req or not (req.get("chat") or req.get("claims")):
        return []
    if claim_for is None:
        import doc_lock
        claim_for = doc_lock.claim_for_path
    claims = req.get("claims") or []
    claims = claims.replace(",", " ").split() if isinstance(claims, str) else list(claims)
    paths = req.get("paths") or []
    paths = paths.replace(",", " ").split() if isinstance(paths, str) else list(paths)
    bad = []
    for p, _kind in chg:
        cl = claim_for(p)
        if cl and cl not in claims and not any(p == x or p.startswith(x.rstrip("/") + "/") for x in paths):
            bad.append((p, cl))
    return bad


def diff(snap_path: str, req_path: str | None) -> int:
    before = json.loads(pathlib.Path(snap_path).read_text(encoding="utf-8"))
    after = snapshot()
    chg = changes(before, after)
    print(f"  ship_stage: the regenerate changed {len(chg)} file(s) (D-326)")
    for i, (p, kind) in enumerate(chg):
        if i == SHOW_FILES:
            print(f"    ... and {len(chg) - SHOW_FILES} more (all listed in {snap_path}.changes)")
            break
        s = summary(p, kind, before, after)
        print(f"    {kind:8s} {p}" + (f"   {s[0]}" if s else ""))
        for l in s[1:]:
            print(f"               {l}")
    pathlib.Path(snap_path + ".changes").write_text("".join(f"{k}\t{p}\n" for p, k in chg), encoding="utf-8")
    bad = unexplained(chg, request(req_path))
    for p, cl in bad:
        print(f"  REFUSED  {p}: the regenerate changed it, and it is under {cl}, which this ship's request does not declare")
    if bad:
        print(f"ship_stage: FAIL — {len(bad)} change(s) nobody asked for. Add the claim or the path to the request, "
              f"or find out why the regenerate moved them")
        return 1
    print("ship_stage: OK" + ("" if req_path else " (no ship request: shown, not judged)"))
    return 0


def selftest() -> int:
    b = {"a.md": {"sha256": "1", "text": "x\ny\n"}, "x/mirror.txt": {"sha256": "2", "text": "p\n"}, "gone": {"sha256": "3", "text": None}}
    a = {"a.md": {"sha256": "9", "text": "x\nz\n"}, "x/mirror.txt": {"sha256": "2", "text": "p\n"}, "new.bin": {"sha256": "4", "text": None}}
    chg = changes(b, a)
    cf = lambda p: {"a.md": "doc:MS"}.get(p)
    ok = (chg == [("a.md", "changed"), ("gone", "deleted"), ("new.bin", "new")]
          and summary("a.md", "changed", b, a)[0] == "+1 -1"
          and unexplained(chg, {"chat": "C", "claims": ["doc:PaperM"]}, cf) == [("a.md", "doc:MS")]
          and unexplained(chg, {"chat": "C", "claims": ["doc:MS"]}, cf) == []
          and unexplained(chg, {"chat": "C", "claims": [], "paths": ["a.md"]}, cf) == []
          and unexplained(chg, None, cf) == [])
    print(f"  ship_stage --selftest: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    if len(argv) >= 3 and argv[1] == "snapshot":
        snap = snapshot()
        pathlib.Path(argv[2]).write_text(json.dumps(snap), encoding="utf-8")
        print(f"  ship_stage: snapshot of {len(snap)} file(s) -> {argv[2]}")
        return 0
    if len(argv) >= 3 and argv[1] == "diff":
        req = argv[argv.index("--request") + 1] if "--request" in argv else None
        return diff(argv[2], req)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
