#!/usr/bin/env python3
"""
proof_corrections.py — the queue of corrections clicked in the proof copies.

  python3 tools/proof_corrections.py            # list what is pending
  python3 tools/proof_corrections.py --all      # include done items
  python3 tools/proof_corrections.py --done 3 5 # mark items 3 and 5 done (by index)
  python3 tools/proof_corrections.py --md       # the pending list as markdown, for a changelog

Reads scratch/proof/corrections.jsonl, written by tools/proof_serve.py (or pasted
from the page's "copy for chat" block). An item is a suggestion, not an edit: the
session verifies it against the committed CSV first, edits through odt_edit, and
only then marks it done. Marking done appends a status line rather than rewriting
the record — the queue is an append-only log.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-20.

import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
QUEUE = REPO / "scratch" / "proof" / "corrections.jsonl"


def load():
    items, done = [], set()
    if QUEUE.exists():
        for line in QUEUE.read_text(encoding="utf8").splitlines():
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if o.get("_done"):
                done.add(o["_done"])
            else:
                items.append(o)
    for i, it in enumerate(items, 1):
        it["_i"] = i
        it["done"] = it.get("id", "") + "@" + it.get("ts", "") in done
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--done", nargs="*", type=int)
    ap.add_argument("--md", action="store_true")
    a = ap.parse_args()
    items = load()
    if a.done:
        with QUEUE.open("a", encoding="utf8") as fh:
            for i in a.done:
                it = next((x for x in items if x["_i"] == i), None)
                if it:
                    fh.write(json.dumps({"_done": it.get("id", "") + "@" + it.get("ts", "")}) + "\n")
                    print(f"  done  #{i}  {it['doc']} {it['value']!r} -> {it['suggested']!r}")
        return 0
    shown = [it for it in items if a.all or not it["done"]]
    if not shown:
        print("queue empty" if not items else f"nothing pending ({len(items)} done)")
        return 0
    for it in shown:
        if a.md:
            print(f"- **{it['doc']}** §{it['section']} — `{it['value']}` → **{it['suggested'] or '(note)'}**"
                  + (f" — {it['note']}" if it.get("note") else "") + f"  \n  _{it['verdict']}: {it['detail'][:120]}_  \n  …{it['context']}…")
        else:
            flag = "done " if it["done"] else "     "
            print(f"#{it['_i']:<3}{flag}{it['doc']:<9} §{it['section'][:34]:34} {it['value']:>10} -> {it['suggested'] or '(note)':<12} {it['note'][:50]}")
            print(f"        {it['verdict']}: {it['detail'][:110]}")
            print(f"        …{it['context'][:150]}…")
    print(f"\n{len([i for i in items if not i['done']])} pending, {len([i for i in items if i['done']])} done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
