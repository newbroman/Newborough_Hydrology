#!/usr/bin/env python3
"""register_io — a short exclusive lock, and a CSV write that keeps other writers' rows.

WHY THIS EXISTS

  Several chats now work in one tree at once (spec NRG_spec_parallel_chats_2026-10-10). A few files
  every chat writes: tools/number_fields.csv, tools/citation_index.csv. Each tool that writes them
  read the file when it started and rewrote it whole when it finished, so rows another chat wrote in
  between were lost without a word. This module turns that into a merge:

    rows = read_rows(path)                 # remembers what was read
    ... change rows ...
    write_rows(path, fieldnames, rows)     # under the lock: re-read the file, apply only THIS
                                           # writer's additions, changes and removals, write

  Rows are compared whole. A row this writer did not touch is taken from the file as it is NOW, so
  another chat's rows added since the read survive, and rows another chat removed stay removed.

  The lock is a lock FILE created with O_EXCL, not fcntl: the desktop bridge reaches the laptop tree
  through a mount, and an fcntl lock taken inside one bridge VM is not seen by another VM or by the
  laptop. An exclusive create is. The mount refuses unlink, so a lock that cannot be removed is
  renamed into _to_delete/locks/ with a unique suffix (CLAUDE.md section 4 explains the suffix).
  A lock older than STALE_S is broken the same way, with a note.

Usage (self-test):  python3 tools/register_io.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-10. First issue (spec NRG_spec_parallel_chats_2026-10-10).

import contextlib
import csv
import io
import os
import pathlib
import socket
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
STALE_S = 300          # a writer holds the lock for well under a second; five minutes is a crash
WAIT_S = 60

_SNAPSHOT: dict[str, list[tuple]] = {}


def _aside(p: pathlib.Path, why: str) -> None:
    """Remove a lock file: unlink, or (on the bridge mount) rename it out of the way."""
    try:
        p.unlink()
        return
    except FileNotFoundError:
        return
    except OSError:
        pass
    d = REPO / "_to_delete" / "locks"
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.rename(p, d / f"{p.name}.{why}.{int(time.time())}.{os.getpid()}")
    except FileNotFoundError:
        pass


@contextlib.contextmanager
def excl_lock(target: pathlib.Path | str, wait_s: float = WAIT_S):
    """Hold <target>.lock for the duration. Waits up to wait_s; breaks a lock older than STALE_S."""
    lock = pathlib.Path(str(target) + ".lock")
    t0 = time.time()
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, f"pid={os.getpid()} host={socket.gethostname()} t={int(time.time())}\n".encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                age = time.time() - lock.stat().st_mtime
            except FileNotFoundError:
                continue
            if age > STALE_S:
                print(f"  register_io: breaking a stale lock {lock.name} ({int(age)} s old)", file=sys.stderr)
                _aside(lock, "stale")
                continue
            if time.time() - t0 > wait_s:
                raise TimeoutError(f"{lock} held for {int(age)} s by another writer; try again")
            time.sleep(0.2)
    try:
        yield
    finally:
        _aside(lock, "released")


def _key(row: dict, fieldnames) -> tuple:
    return tuple((row.get(c) or "") for c in fieldnames)


def _read(path: pathlib.Path) -> tuple[list[str], list[dict]]:
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def read_rows(path) -> list[dict]:
    """Read a CSV register and remember it as the base for write_rows()."""
    path = pathlib.Path(path)
    fields, rows = _read(path)
    _SNAPSHOT[str(path.resolve())] = [_key(r, fields) for r in rows] if fields else []
    _SNAPSHOT[str(path.resolve()) + "#fields"] = fields
    return rows


def merge(base: list[tuple], mine: list[tuple], disk: list[tuple]) -> tuple[list[tuple], int, int]:
    """Three-way merge of row multisets. Order: mine first (as this writer arranged it), then rows
    added on disk since base. Returns (rows, n_kept_from_others, n_dropped_by_others)."""
    from collections import Counter
    cb, cm, cd = Counter(base), Counter(mine), Counter(disk)
    added_by_others = cd - cb            # rows on disk now that were not there when we read
    removed_by_others = cb - cd          # rows that were there and are gone now
    out, drop = [], Counter(removed_by_others)
    n_drop = 0
    for r in mine:
        if drop[r] > 0 and cm[r] <= cb[r]:   # we did not add this row; another writer removed it
            drop[r] -= 1
            n_drop += 1
            continue
        out.append(r)
    have = Counter(out)
    extra = []
    for r, n in added_by_others.items():
        k = n - max(0, have[r] - cb[r])      # rows we also added count once
        extra += [r] * max(0, k)
    return out + extra, len(extra), n_drop


def write_rows(path, fieldnames: list[str], rows: list[dict], sort_key=None, key_cols=None) -> None:
    """Write rows, keeping every row another writer added or removed since read_rows(path).

    key_cols: for a keyed register (one row per key), a key both writers changed keeps THIS
    writer's row, and the other is reported rather than duplicated."""
    path = pathlib.Path(path)
    sk = str(path.resolve())
    with excl_lock(path):
        dfields, drows = _read(path)
        if sk not in _SNAPSHOT or not dfields:
            final = [_key(r, fieldnames) for r in rows]
            kept = dropped = 0
        else:
            bfields = _SNAPSHOT[sk + "#fields"] or fieldnames
            # compare in this writer's column order; a base or disk row lacking a column reads ""
            def recode(keys, fields):
                return [_key(dict(zip(fields, k)), fieldnames) for k in keys]
            base = recode(_SNAPSHOT[sk], bfields)
            disk = [_key(r, fieldnames) for r in drows]
            mine = [_key(r, fieldnames) for r in rows]
            final, kept, dropped = merge(base, mine, disk)
        out_rows = [dict(zip(fieldnames, k)) for k in final]
        if key_cols:
            seen, dedup, clash = set(), [], []
            for r in out_rows:                    # this writer's rows come first in `final`
                kk = tuple(r.get(c, "") for c in key_cols)
                if kk in seen:
                    clash.append(kk)
                    continue
                seen.add(kk)
                dedup.append(r)
            if clash:
                print(f"  register_io: {path.name}: {len(clash)} key(s) changed by another writer as well; "
                      f"this writer's row kept: {', '.join('/'.join(k) for k in clash[:5])}", file=sys.stderr)
            out_rows = dedup
        if sort_key is not None:
            out_rows.sort(key=sort_key)
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\r\n" if _crlf(path) else "\n")
        w.writeheader()
        w.writerows(out_rows)
        with path.open("w", encoding="utf-8", newline="") as fh:   # in place: the mount refuses a replacing rename
            fh.write(buf.getvalue())
        _SNAPSHOT[sk] = final
        _SNAPSHOT[sk + "#fields"] = list(fieldnames)
        if kept or dropped:
            print(f"  register_io: {path.name}: kept {kept} row(s) another writer added and honoured "
                  f"{dropped} removal(s) since this tool read the file", file=sys.stderr)


def _crlf(path: pathlib.Path) -> bool:
    """Keep the file's own line ending (csv's default is CRLF; some registers are LF)."""
    try:
        with path.open("rb") as fh:
            head = fh.read(4096)
        return b"\r\n" in head
    except FileNotFoundError:
        return False


def _selftest() -> int:
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "reg.csv"
        F = ["k", "v"]
        p.write_text("k,v\na,1\nb,2\n", encoding="utf-8")
        # writer A reads, writer B reads, B adds c and removes b, A changes a and adds d
        a = read_rows(p)
        snapA = dict(_SNAPSHOT)
        b = read_rows(p)
        b = [r for r in b if r["k"] != "b"] + [{"k": "c", "v": "3"}]
        write_rows(p, F, b)
        _SNAPSHOT.clear(); _SNAPSHOT.update(snapA)
        a = [{"k": "a", "v": "9"} if r["k"] == "a" else r for r in a] + [{"k": "d", "v": "4"}]
        write_rows(p, F, a, sort_key=lambda r: r["k"])
        got = p.read_text(encoding="utf-8")
        want = "k,v\na,9\nc,3\nd,4\n"
        if got != want:
            print(f"FAIL merge: got {got!r} want {want!r}"); ok = False
        # both change the same key: this writer wins, no duplicate
        a = read_rows(p); snapA = dict(_SNAPSHOT)
        b = [{"k": "a", "v": "5"} if r["k"] == "a" else r for r in read_rows(p)]
        write_rows(p, F, b, key_cols=["k"])
        _SNAPSHOT.clear(); _SNAPSHOT.update(snapA)
        a = [{"k": "a", "v": "7"} if r["k"] == "a" else r for r in a]
        write_rows(p, F, a, sort_key=lambda r: r["k"], key_cols=["k"])
        got = p.read_text(encoding="utf-8")
        if got != "k,v\na,7\nc,3\nd,4\n":
            print(f"FAIL keyed clash: got {got!r}"); ok = False
        # lock: a second holder waits, then times out
        with excl_lock(p):
            try:
                with excl_lock(p, wait_s=0.5):
                    print("FAIL lock: second holder got in"); ok = False
            except TimeoutError:
                pass
        if pathlib.Path(str(p) + ".lock").exists():
            print("FAIL lock: not released"); ok = False
    print("register_io selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    print(__doc__)
