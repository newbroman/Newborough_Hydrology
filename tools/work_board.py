#!/usr/bin/env python3
"""work_board — who is doing what in this tree: claims, ships, uncommitted work, held-back work.

Several chats work in one tree at once (spec NRG_spec_parallel_chats_2026-10-10). Nobody could see
who was doing what without asking each chat. This prints it, from the claims in
working/DOCUMENT_LOCK.json (tools/doc_lock.py), the ship watcher's status, git, and .ship_hold/:

  CLAIMS          each claim, its chat, since when, and its note
  SHIPS           the watcher's last ship and any request waiting; the last commits
  CHANGES         uncommitted files in the tree, grouped by the claim that covers them
  HELD BACK       work a ship parked that was not put back (tools/ship_scope.py restore)

It runs at the start of every session (tools/session_handover.py), in the ship log, and in the
06:30 dashboard snapshot (working/dashboard/emit_status.py reads --json).

Usage:  python3 tools/work_board.py [--json] [--gate]
  --gate   advisory (check_all): name uncommitted work under a claim nobody holds, and held-back
           work never restored. Always exits 0.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-10. First issue (spec NRG_spec_parallel_chats_2026-10-10).

import argparse
import collections
import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))


def _git(*a) -> str:
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def _json(p: pathlib.Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def collect() -> dict:
    import doc_lock
    import ship_scope
    lock = doc_lock.read() or {}
    held = doc_lock.claims()
    try:
        changes = ship_scope.changed_paths()
    except RuntimeError:
        changes = []
    by = collections.defaultdict(list)
    for st, p in changes:
        if p.startswith(".ship_hold/"):
            continue
        by[doc_lock.claim_for_path(p) or "(shared / no claim)"].append(p)
    status = _json(REPO / "working/.ship_status.json") or {}
    pending = (REPO / "working/.ship_request").exists()
    holds = []
    hd = REPO / ".ship_hold"
    if hd.is_dir():
        for m in sorted(hd.glob("*/manifest.json")):
            man = _json(m) or {}
            if not man.get("restored"):
                holds.append({"id": man.get("id", m.parent.name), "chat": man.get("chat"),
                              "left": man.get("left") or [e["path"] for e in man.get("entries", [])
                                                          if not e.get("restored")]})
    return {
        "machine_lock": {k: lock.get(k) for k in ("holder", "since", "note")},
        "claims": {n: held.get(n) for n in doc_lock.claim_names()},
        "ship": {k: status.get(k) for k in ("id", "state", "verdict", "requested_by", "started", "finished",
                                            "ship_line", "sha_public")},
        "ship_request_waiting": pending,
        "last_commits": [l for l in _git("log", "-4", "--format=%h %ad %s", "--date=format:%m-%d %H:%M").splitlines()],
        "changes": {k: sorted(v) for k, v in sorted(by.items())},
        "held_back": holds,
    }


def render(B: dict) -> str:
    L = []
    L.append("WORK BOARD (tools/work_board.py)")
    ml = B["machine_lock"]
    L.append(f"  documents (machine lock): {ml.get('holder') or 'free'}"
             + (f" since {ml.get('since')}" if ml.get("holder") else ""))
    L.append("  CLAIMS")
    free = []
    for n, c in B["claims"].items():
        if c:
            L.append(f"    {n:<18} chat {c['chat']!r:<30} since {c.get('since', '?')}  {c.get('note') or ''}".rstrip())
        else:
            free.append(n)
    if free:
        L.append(f"    free: {', '.join(free)}")
    s = B["ship"]
    L.append("  SHIPS")
    if s.get("id"):
        L.append(f"    last request {s['id']}: {s.get('state')}"
                 + (f" - {s.get('ship_line') or s.get('verdict') or ''}" if s.get("state") == "done" else ""))
    L.append(f"    waiting: {'a request is queued' if B['ship_request_waiting'] else 'none'}")
    for c in B["last_commits"][:3]:
        L.append(f"    {c[:110]}")
    L.append("  UNCOMMITTED CHANGES IN THE TREE")
    if not B["changes"]:
        L.append("    none")
    for k, v in B["changes"].items():
        h = (B["claims"].get(k) or {}).get("chat") if k in B["claims"] else None
        who = f"chat {h!r}" if h else ("UNCLAIMED" if k in B["claims"] else "")
        L.append(f"    {k:<20} {len(v):4d} file(s)  {who}".rstrip())
        for p in v[:3]:
            L.append(f"        {p}")
        if len(v) > 3:
            L.append(f"        ... {len(v) - 3} more")
    if B["held_back"]:
        L.append("  HELD BACK BY A SHIP AND NOT PUT BACK  (python3 tools/ship_scope.py restore --id ID)")
        for h in B["held_back"]:
            L.append(f"    {h['id']} (chat {h.get('chat')!r}): {len(h['left'])} item(s)")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()
    try:
        B = collect()
    except Exception as e:                       # the board informs; it must never block anything
        print(f"  work_board: could not read the board ({e})")
        return 0
    if a.json:
        print(json.dumps(B, indent=1, default=str))
        return 0
    if a.gate:
        unclaimed = {k: v for k, v in B["changes"].items() if k in B["claims"] and not B["claims"][k]}
        n = sum(len(v) for v in unclaimed.values())
        if n:
            print(f"  note  {n} uncommitted file(s) under claims nobody holds "
                  f"({', '.join(f'{k} {len(v)}' for k, v in unclaimed.items())}): "
                  f"a ship takes them with whatever it ships")
        for h in B["held_back"]:
            print(f"  note  ship {h['id']} held back {len(h['left'])} item(s) that were never put back")
        if not n and not B["held_back"]:
            print("  OK  every uncommitted change is under a held claim or shared")
        return 0
    print(render(B))
    return 0


if __name__ == "__main__":
    sys.exit(main())
