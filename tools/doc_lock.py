#!/usr/bin/env python3
"""doc_lock — one machine at a time may edit the ODTs.

WHY THIS EXISTS

  The project is machine-independent in two of its three stores. Both git
  repositories merge; two machines can work on code, tools, the decision log and
  the changelogs at the same time and git will tell you if they collide.

  The ODTs cannot. `rclone copy` is one-way, on demand, with no merge and no
  conflict detection, and an ODT is a zip - there is nothing to merge even in
  principle. Two machines editing report9.odt means whoever archives last wins
  and the other's work is gone, silently.

  There is a subtler version that would bite even someone careful about Drive.
  THE MIRRORS ARE COMMITTED; THE ODTs ARE NOT. So if machine A edits an ODT,
  regenerates the mirror and pushes, and machine B still holds the older ODT,
  B's next refresh_mirrors run regenerates the mirror FROM ITS STALE ODT and
  pushes what looks like an ordinary commit but is a reversion of A's prose.
  check_all's mirror gate compares modification times only - it never reads
  content - so B's stale mirror reads as current and every gate stays green.

  This turns that silent loss into a refusal.

WHAT IT IS NOT

  Not a concurrency primitive. The lock lives in the private git repository, so
  it is only as current as the last fetch, and two machines that both take it
  while offline will both believe they hold it. It is a handover protocol
  between one person's machines, not a mutex. It stops the accident, not an
  adversary.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-25. First issue.

import argparse, datetime, json, os, pathlib, socket, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[1]
LOCK = REPO / "working/DOCUMENT_LOCK.json"


def _who() -> str:
    return f"{os.environ.get('USER') or os.environ.get('USERNAME') or '?'}@{socket.gethostname()}"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read() -> dict | None:
    if not LOCK.exists():
        return None
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"holder": "UNREADABLE", "since": "?", "note": "lock file is corrupt"}


def status(quiet: bool = False) -> int:
    """0 = free or held by me, 1 = held by someone else."""
    st = read()
    me = _who()
    # A RELEASED lock is a file with holder null, not an absent file: the bridge
    # mount refuses unlink, so release() empties rather than deletes. Both read
    # as unlocked, and forgetting that made the first version report a released
    # lock as held by someone else.
    if st is None or not st.get("holder"):
        if not quiet:
            print("  documents UNLOCKED — take it before editing any ODT")
        return 0
    mine = st.get("holder") == me
    if not quiet:
        word = "you hold it" if mine else "HELD BY ANOTHER MACHINE"
        print(f"  documents locked: {word}")
        print(f"    holder {st.get('holder')}   since {st.get('since')}")
        if st.get("note"):
            print(f"    note   {st['note']}")
    return 0 if mine else 1


def acquire(note: str, force: bool) -> int:
    st = read()
    me = _who()
    # `st.get("holder")` FIRST. A released lock is a file with holder null — this
    # module says so at status() and the bridge mount's refusal to unlink is why.
    # Without that clause `None != me` is true, so every correctly released lock
    # refused the next taker and the only way past it was --force. Which is what
    # was done on 2026-08-27, on a lock nobody held.
    if st and st.get("holder") and st.get("holder") != me and not force:
        print(f"  REFUSED — {st.get('holder')} has held the documents since {st.get('since')}.")
        print("  Ask that machine to release, or --force if you know it is idle.")
        print("  Forcing while the other machine has unarchived edits loses them.")
        return 1
    LOCK.write_text(json.dumps(
        {"holder": me, "since": _now(), "note": note}, indent=2) + "\n", encoding="utf-8")
    print(f"  documents locked to {me}")
    print("  commit and push the private repo so the other machine can see it.")
    return 0


def release() -> int:
    st = read()
    if st is None:
        print("  already unlocked")
        return 0
    me = _who()
    if st.get("holder") != me:
        print(f"  note: the lock is held by {st.get('holder')}, not by you — releasing anyway")
    # The bridge mount refuses unlink, so emptying beats deleting: a zero-holder
    # file reads as unlocked and never leaves a half-removed lock behind.
    LOCK.write_text(json.dumps({"holder": None, "since": _now(),
                                "note": f"released by {me}"}, indent=2) + "\n", encoding="utf-8")
    print("  documents released — commit and push the private repo")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["status", "take", "release", "check"])
    ap.add_argument("--note", default="", help="what you are editing")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.action in ("status", "check"):
        return status(quiet=a.quiet) if a.action == "check" else (status(), 0)[1]
    if a.action == "take":
        return acquire(a.note, a.force)
    return release()


if __name__ == "__main__":
    sys.exit(main())
