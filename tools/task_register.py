#!/usr/bin/env python3
"""task_register.py — mint a task id from ORIGIN, and publish the row that takes it.

WHY THIS EXISTS (2026-11-08, Martin: "task register should publish").

On 2026-11-08 two chats each minted a T-183 and a T-184: four distinct tasks under two
ids, found only when the branches merged. Neither chat did anything wrong. A chat takes
`max(id) + 1` over the register it can SEE, and both were reading a `--depth 50` clone,
so neither could see the other's rows -- nor rows older than fifty commits.

Two things had to change, and this tool is the second:

  1. tools/cloud_setup.sh now clones with --filter=blob:none, not --depth 50, so a chat
     sees the whole history. That removes the stale-view cause.
  2. An id is still only taken when GITHUB has it. Minting locally and pushing hours
     later at ship time leaves a window in which two chats can both mint the same number.
     This tool closes it: `add` fetches origin, mints from ORIGIN's register, appends the
     row, commits and pushes THAT FILE ALONE.

The rule the lock already states (CLAUDE.md §4b) applies unchanged: an id is not taken
until GitHub has it. A mint that cannot be published says LOCAL ONLY and means it.

ON THE PUSH, because this is the first PUBLIC record to publish itself. D-314 exempts a
lock push from "ask before every push" (§7) on the grounds that it publishes "no code, no
prose and no numbers". A task row carries prose, so the exemption is NOT inherited: this
tool pushes only when nothing else is waiting to be pushed, and refuses otherwise, naming
what blocked it -- the T-175 guard, which was written after a `take` carried five
unapproved commits to GitHub. The push therefore adds exactly one commit touching exactly
one file, which is the narrowest thing that can still be called publication.

    python3 tools/task_register.py next-id
    python3 tools/task_register.py add --subject "..." --source "..." --check-cmd "..." \
        --expect 0 --claim pipeline --note "..."
    python3 tools/task_register.py --check          # gate: no id disagrees with origin
    python3 tools/task_register.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-08. First cut: mint from origin, publish
#   the row alone, and gate a local id that disagrees with origin's.

import argparse
import csv
import io
import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
REGISTER = pathlib.Path(os.environ.get("NRG_TASK_REGISTER") or (REPO / "tools/task_register.csv"))
ID_RE = re.compile(r"^T-(\d+)$")
# Only this file may ride the automatic push. Anything else is work someone chooses to push.
REGISTER_REL = "tools/task_register.csv"
PUBLIC_RECORD_PATHS = (REGISTER_REL,)


def _git(*args: str, repo: pathlib.Path | None = None, timeout: int = 120):
    return subprocess.run(["git", "--no-optional-locks", *args], cwd=str(repo or REPO),
                          capture_output=True, text=True, timeout=timeout)


def _rows(text: str) -> tuple[list[str], list[list[str]]]:
    r = list(csv.reader(io.StringIO(text)))
    return (r[0], [x for x in r[1:] if x]) if r else ([], [])


def read_local() -> tuple[list[str], list[list[str]]]:
    return _rows(REGISTER.read_text(encoding="utf8"))


def _local_rows(repo: pathlib.Path | None):
    """This tree's rows, or a temp tree's in --selftest."""
    if repo is None:
        return read_local()
    return _rows((repo / REGISTER_REL).read_text(encoding="utf8"))


def read_origin(repo: pathlib.Path | None = None) -> tuple[list[str], list[list[str]]] | None:
    """Origin's register, or None when origin cannot be reached. None means 'unknown', and
    every caller treats it as a reason to say so rather than to assume agreement."""
    # Always repo-relative: the register sits at the same path inside whichever tree we are
    # asked about, and REGISTER is an absolute path into THIS one.
    p = _git("show", f"origin/main:{REGISTER_REL}", repo=repo)
    return _rows(p.stdout) if p.returncode == 0 else None


def max_id(rows: list[list[str]]) -> int:
    return max((int(m.group(1)) for r in rows if r and (m := ID_RE.match(r[0]))), default=0)


def next_id(fetch: bool = True, repo: pathlib.Path | None = None) -> tuple[str, str]:
    """The next free id, taken over the UNION of origin's register and this tree's.

    The union matters: origin alone would re-mint an id this tree has already written but
    not yet pushed, and local alone is the bug this tool exists to fix.
    """
    if fetch:
        _git("fetch", "-q", "origin", "main", repo=repo)
    _, local = _local_rows(repo)
    o = read_origin(repo)
    if o is None:
        return f"T-{max_id(local) + 1}", "LOCAL ONLY — origin unreachable; this id is not reserved"
    return f"T-{max(max_id(local), max_id(o[1])) + 1}", "from origin+local"


def disagreements(repo: pathlib.Path | None = None) -> list[tuple[str, str, str]]:
    """Ids present on both sides whose SUBJECT differs — the collision, caught at gate time
    instead of at merge time."""
    o = read_origin(repo)
    if o is None:
        return []
    _, local = _local_rows(repo)
    od = {r[0]: r for r in o[1]}
    out = []
    for r in local:
        if r[0] in od and len(r) > 1 and len(od[r[0]]) > 1 and r[1].strip() != od[r[0]][1].strip():
            out.append((r[0], r[1][:70], od[r[0]][1][:70]))
    return out


def _blockers(repo: pathlib.Path | None = None) -> list[str]:
    """Commits between origin/main and HEAD touching anything but the register (T-175)."""
    p = _git("rev-list", "origin/main..HEAD", repo=repo)
    if p.returncode:
        return []
    out = []
    for sha in [s for s in p.stdout.split() if s]:
        files = _git("show", "--name-only", "--format=", sha, repo=repo).stdout.split()
        if any(f not in PUBLIC_RECORD_PATHS for f in files):
            subj = _git("log", "-1", "--format=%h %s", sha, repo=repo).stdout.strip()
            out.append(subj)
    return out


def publish(message: str, repo: pathlib.Path | None = None) -> tuple[bool, str]:
    if os.environ.get("NRG_NO_LOCK_PUSH"):
        return False, "LOCAL ONLY — NRG_NO_LOCK_PUSH is set"
    if not _git("config", "--get", "remote.origin.url", repo=repo).stdout.strip():
        return False, "LOCAL ONLY — no origin remote"
    branch = _git("rev-parse", "--abbrev-ref", "HEAD", repo=repo).stdout.strip()
    if branch != "main":
        return False, f"LOCAL ONLY — on branch {branch!r}, and this project ships from main (§4g)"
    _git("add", "--", *PUBLIC_RECORD_PATHS, repo=repo)
    if not _git("diff", "--cached", "--name-only", repo=repo).stdout.strip():
        return False, "nothing to commit"
    _git("commit", "-q", "-m", message, repo=repo)
    blocked = _blockers(repo)
    if blocked:
        return False, ("LOCAL ONLY — the row is committed but NOT PUSHED: "
                       + f"{len(blocked)} unpushed commit(s) here touch more than the register, "
                       + "and this push would carry them too (§7, T-175):\n    "
                       + "\n    ".join(blocked))
    if _git("push", "-q", "origin", "HEAD:main", repo=repo).returncode:
        return False, "LOCAL ONLY — the push was refused (fetch and merge, then re-run)"
    return True, "published"


def add(args) -> int:
    tid, how = next_id(repo=None)
    hdr, rows = read_local()
    row = [tid, args.subject, args.source, args.check_cmd, args.expect, args.opened or "",
           args.claim or "", args.note or ""]
    row = (row + [""] * len(hdr))[:len(hdr)]
    with REGISTER.open("w", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(hdr)
        w.writerows(rows + [row])
    ok, why = publish(f"task register: {tid} minted by chat "
                      f"{os.environ.get('NRG_CHAT', '(unnamed)')!r}", repo=None)
    print(f"  {tid}  ({how})")
    print(f"  {'published' if ok else why}")
    if not ok:
        print("  the id is NOT reserved until GitHub has it (CLAUDE.md §4b)")
    return 0


def check() -> int:
    bad = disagreements()
    if read_origin() is None:
        print("  task_register: origin unreachable — id agreement NOT checked")
        print("task_register --check: OK")
        return 0
    for tid, mine, theirs in bad:
        print(f"  FAIL  {tid} means two different things")
        print(f"          here:   {mine}")
        print(f"          origin: {theirs}")
    print("task_register --check: " + ("FAIL" if bad else "OK"))
    return 1 if bad else 0


def selftest() -> int:
    """Five properties, each on a throwaway repo pair."""
    fails = []
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        up, wk = t / "up.git", t / "wk"
        # capture_output: cloning an empty bare repo warns on stderr, and a selftest that
        # prints a warning in every check_all run trains people to ignore its output.
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(up)],
                       check=True, capture_output=True)
        subprocess.run(["git", "clone", "-q", str(up), str(wk)],
                       check=True, capture_output=True)
        for k, v in (("user.email", "t@t"), ("user.name", "t")):
            _git("config", k, v, repo=wk)
        reg = wk / "tools/task_register.csv"
        reg.parent.mkdir(parents=True, exist_ok=True)
        reg.write_text("id,subject\nT-1,one\nT-2,two\n", encoding="utf8")
        _git("add", "-A", repo=wk); _git("commit", "-q", "-m", "base", repo=wk)
        _git("push", "-q", "origin", "main", repo=wk); _git("fetch", "-q", "origin", repo=wk)

        # 1. next id is max+1 over the union
        got, _ = next_id(fetch=False, repo=wk)
        if got != "T-3":
            fails.append(f"1: next_id {got} != T-3")
        # 2. an unpushed local row still counts, so an id is never re-minted
        reg.write_text("id,subject\nT-1,one\nT-2,two\nT-9,nine\n", encoding="utf8")
        got, _ = next_id(fetch=False, repo=wk)
        if got != "T-10":
            fails.append(f"2: next_id {got} != T-10 with an unpushed T-9")
        # 3. same id, different subject -> a disagreement
        reg.write_text("id,subject\nT-1,ONE CHANGED\nT-2,two\n", encoding="utf8")
        d = disagreements(repo=wk)
        if not any(x[0] == "T-1" for x in d):
            fails.append("3: a changed subject on a shared id was not reported")
        # 4. identical rows are not a disagreement
        reg.write_text("id,subject\nT-1,one\nT-2,two\n", encoding="utf8")
        if disagreements(repo=wk):
            fails.append("4: identical registers reported a disagreement")
        # 5. a commit touching anything else blocks the push (T-175)
        (wk / "other.txt").write_text("x", encoding="utf8")
        _git("add", "-A", repo=wk); _git("commit", "-q", "-m", "unrelated", repo=wk)
        if not _blockers(repo=wk):
            fails.append("5: an unrelated unpushed commit did not block the push")
    for f in fails:
        print(f"  FAIL {f}")
    print(f"task_register --selftest: {'FAIL' if fails else 'OK'} (5 properties)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", choices=["next-id", "add"], default=None)
    ap.add_argument("--subject", default=""); ap.add_argument("--source", default="")
    ap.add_argument("--check-cmd", default=""); ap.add_argument("--expect", default="")
    ap.add_argument("--opened", default=""); ap.add_argument("--claim", default="")
    ap.add_argument("--note", default=""); ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.check:
        return check()
    if a.command == "next-id":
        tid, how = next_id()
        print(f"{tid}  ({how})")
        return 0
    if a.command == "add":
        if not a.subject:
            ap.error("--subject is required for add")
        return add(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
