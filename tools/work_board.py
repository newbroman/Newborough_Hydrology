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

  STORE           1.2.0: whether the PRIVATE repository is here at all. Without it the claims are
                  UNKNOWN, never free - a public-only clone was told every claim was free on
                  2026-11-04 while another chat held doc:PaperM (D-300).
  REPOSITORIES    1.2.0: public and private side by side - branch, HEAD, ahead/behind origin/main,
                  whether origin has moved since the last fetch, and that fetch's time.

FRESHNESS IS PROBED WITH ls-remote, NOT fetch (1.2.0)

  The lock is only as current as the last fetch of the private repository, and the board used not to
  say when that was. It now asks the remote directly - `git ls-remote origin refs/heads/main`, 0.6 s
  per repository - and compares the answer to the local refs/remotes/origin/main.

  ls-remote rather than fetch, deliberately: it writes NOTHING into .git. No FETCH_HEAD, no ref
  update, so no *.lock residue - which matters because the bridge mount refuses unlink and a stray
  refs/heads/main.lock wedges the next ref update (CLAUDE.md 4). A board that runs at every session
  start and inside check_all should not write to both git directories for what it only reads.

  The probe is OFF for --gate and --json: check_all must not acquire a network dependency, and the
  06:30 dashboard runs unattended. Both then report freshness from the ref mtime alone.

Usage:  python3 tools/work_board.py [--json] [--gate] [--probe|--no-probe]
  --gate   advisory (check_all): name uncommitted work under a claim nobody holds, and held-back
           work never restored. Always exits 0.
  --probe  ask each origin whether it has moved (default on for the printed board, off for
           --gate/--json); --no-probe for offline.
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-11-04 (D-300, spec NRG_handover_control_board_2026-11-04,
#   signed off). The control board. R1: an ABSENT private store reads UNKNOWN on every claim instead of free, in the
#   board's first line. R2: freshness per repository, probed read-only with ls-remote (never fetch - no .git writes,
#   no lock residue) and off by default for --gate/--json. R3: one block per repository - branch, HEAD, ahead/behind
#   origin/main, origin moved, uncommitted files by covering claim, with the private half labelled "records (shared,
#   merged row by row)" rather than pretending working/ is claimable. R4: claims carry activity age and a STALE or
#   ABANDONED flag. R6(b): --json carries all of it for working/dashboard/emit_status.py.
# 1.1.0  # Hollingham (2026) — 2026-11-03 (D-299). The machine-lock line flags a bridge lock under the
#   VM's rcw-<session>@claude name (doc_lock.BRIDGE_HOLDER), which blocked the L14's archives for eight days.
# 1.0.0  # Hollingham (2026) — 2026-10-10. First issue (spec NRG_spec_parallel_chats_2026-10-10).

import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE).resolve()
sys.path.insert(0, str(HERE / "tools"))

# R3: the two halves of this one working tree (CLAUDE.md 4f). The private half is a second git
# directory over the same files, so every private command needs BOTH --git-dir and --work-tree -
# with --git-dir alone, `rev-parse HEAD origin/main` is fatal while `rev-list` quietly still works.
REPOS = (("public", ".git", "code, tools, mirrors"),
         ("private", ".git-working", "decision log, changelogs, updates, the lock itself"))
PROBE_TIMEOUT_S = 5.0        # measured 0.55-0.64 s per repository; 5 s is slack, not an expectation
# R3: working/ is not claimable and never will be - the registers under it are merged row by row by
# register_io. It still needs a name on the board, or the whole private half reads "(shared)".
RECORDS_LABEL = "records (shared, merged row by row)"


def _git(*a, gitdir: str = ".git") -> str:
    """Always --no-optional-locks: the board must never write an index, least of all on the bridge."""
    base = ["git", "-C", str(REPO), "--git-dir", str(REPO / gitdir), "--no-optional-locks"]
    if gitdir != ".git":
        base += ["--work-tree", str(REPO)]
    r = subprocess.run(base + list(a), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def _mtime(p: pathlib.Path) -> str | None:
    try:
        return datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc)\
            .strftime("%Y-%m-%dT%H:%MZ")
    except OSError:
        return None


def last_fetch(gitdir: str) -> str | None:
    """When this repository last heard from origin. The remote-tracking ref if it is loose, else
    FETCH_HEAD; packed refs have no per-ref mtime, so None is an honest answer."""
    g = REPO / gitdir
    return _mtime(g / "refs/remotes/origin/main") or _mtime(g / "FETCH_HEAD")


def probe_origin(gitdir: str) -> tuple[str | None, str | None]:
    """R2: ask origin for refs/heads/main WITHOUT writing anything into .git. (sha, error)."""
    try:
        r = subprocess.run(["git", "-C", str(REPO), "--git-dir", str(REPO / gitdir),
                            "--no-optional-locks", "ls-remote", "origin", "refs/heads/main"],
                           capture_output=True, text=True, timeout=PROBE_TIMEOUT_S)
        if r.returncode != 0:
            return None, (r.stderr.strip().splitlines() or ["ls-remote failed"])[-1][:120]
        out = r.stdout.split()
        return (out[0] if out else None), None
    except subprocess.TimeoutExpired:
        return None, f"origin did not answer within {PROBE_TIMEOUT_S:.0f} s"
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)[:120]


def repo_state(name: str, gitdir: str, holds: str, do_probe: bool) -> dict:
    """R3: one repository's position, and R2's freshness."""
    d = {"name": name, "gitdir": gitdir, "holds": holds, "present": (REPO / gitdir).exists()}
    if not d["present"]:
        return d
    d["branch"] = (_git("rev-parse", "--abbrev-ref", "HEAD", gitdir=gitdir).strip() or None)
    d["head"] = (_git("rev-parse", "--short", "HEAD", gitdir=gitdir).strip() or None)
    d["origin_main"] = (_git("rev-parse", "--short", "origin/main", gitdir=gitdir).strip() or None)
    cnt = _git("rev-list", "--left-right", "--count", "origin/main...HEAD", gitdir=gitdir).split()
    if len(cnt) == 2:
        d["behind"], d["ahead"] = int(cnt[0]), int(cnt[1])
    d["last_fetch"] = last_fetch(gitdir)
    if do_probe:
        sha, err = probe_origin(gitdir)
        local = _git("rev-parse", "origin/main", gitdir=gitdir).strip() or None
        d["probe_error"] = err
        if sha and local:
            d["origin_moved"] = (sha != local)
            d["origin_sha"] = sha[:7]
    return d


def _json(p: pathlib.Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def private_changes() -> list[str]:
    """R3: the private half's uncommitted files. A separate repository over the same tree, so
    ship_scope.changed_paths() (public) never sees them."""
    out = []
    for line in _git("status", "--porcelain", "--", "working/", gitdir=".git-working").splitlines():
        if len(line) > 3:
            out.append(line[3:].strip().strip('"').split(" -> ")[-1])
    return sorted(set(out))


def collect(do_probe: bool = False) -> dict:
    import doc_lock
    import ship_scope
    store, store_why = doc_lock.store_state()
    absent = (store == "ABSENT")
    lock = {} if absent else (doc_lock.read() or {})
    held = {} if absent else doc_lock.claims()
    try:
        changes = ship_scope.changed_paths()
    except RuntimeError:
        changes = []
    by = collections.defaultdict(list)
    for st, p in changes:
        if p.startswith(".ship_hold/"):
            continue
        by[doc_lock.claim_for_path(p) or "(shared / no claim)"].append(p)
    # R3: the private half, under its own label. Not a claim - nothing new for anyone to hold.
    priv = private_changes() if (REPO / ".git-working").exists() else []
    for pth in priv:
        by[doc_lock.claim_for_path(pth) or RECORDS_LABEL].append(pth)
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
        "store": store,
        "store_why": store_why,
        "warnings": doc_lock.override_warnings(),
        "repos": [repo_state(nm, gd, hd, do_probe) for nm, gd, hd in REPOS],
        "private_changes": priv,
        # R4: activity age and the flag, computed here so every consumer agrees (R6(b)).
        "stale": {k: {"flag": doc_lock.staleness(v), "note": doc_lock.stale_note(v),
                      "age_h": doc_lock.age_h(v)}
                  for k, v in held.items() if doc_lock.staleness(v)},
        "stale_hours": doc_lock.stale_hours(),
        "abandoned_hours": doc_lock.abandoned_hours(),
        "machine_lock": {k: lock.get(k) for k in ("holder", "since", "note")},
        # R1: UNKNOWN, not free. None would be indistinguishable from "nobody holds it".
        "claims": ({n: "UNKNOWN" for n in doc_lock.claim_names()} if absent
                   else {n: held.get(n) for n in doc_lock.claim_names()}),
        "ship": {k: status.get(k) for k in ("id", "state", "verdict", "requested_by", "started", "finished",
                                            "ship_line", "sha_public")},
        "ship_request_waiting": pending,
        "last_commits": [l for l in _git("log", "-4", "--format=%h %ad %s", "--date=format:%m-%d %H:%M").splitlines()],
        "changes": {k: sorted(v) for k, v in sorted(by.items())},
        "held_back": holds,
    }


def _repo_line(r: dict) -> list[str]:
    if not r.get("present"):
        return [f"    {r['name']:<8} NOT PRESENT in this session  ({r['holds']})"]
    pos = f"{r.get('head') or '?'} on {r.get('branch') or '?'}"
    if r.get("behind") is not None:
        if r["behind"] or r["ahead"]:
            pos += f"   {r['ahead']} ahead, {r['behind']} behind origin/main"
        else:
            pos += "   level with origin/main"
    out = [f"    {r['name']:<8} {pos}"]
    fresh = f"as of fetch {r['last_fetch']}" if r.get("last_fetch") else "last fetch unknown"
    if r.get("origin_moved") is True:
        out.append(f"    {'':<8} >>> ORIGIN HAS MOVED since your last fetch (origin/main is {r.get('origin_sha')}):")
        out.append(f"    {'':<8} >>> `git fetch` before trusting the counts above, and before taking a claim")
    elif r.get("origin_moved") is False:
        fresh += ", origin asked just now: in step"
    elif r.get("probe_error"):
        fresh += f", origin not reached ({r['probe_error']})"
    out.append(f"    {'':<8} {fresh}")
    return out


def render(B: dict) -> str:
    L = []
    L.append("WORK BOARD (tools/work_board.py)")
    # R1: the first line, because what the rest of the board is worth depends on it.
    if B.get("store") == "ABSENT":
        L.append(f"  PRIVATE STORE ABSENT - {B.get('store_why')}")
        L.append("    >>> every claim below reads UNKNOWN, NOT free. Another chat may hold any of them.")
        L.append("    >>> attach both repositories with push access (notes/reference/SESSION_MODES.md):")
        L.append("    >>>     add_repo newbroman/Newborough_Hydrology          access=push")
        L.append("    >>>     add_repo newbroman/Newborough_Hydrology_working  access=push")
        L.append("    >>> then run tools/cloud_setup.sh. (D-300, the 2026-11-04 incident.)")
    elif B.get("store") == "PRESENT_NO_LOCK":
        L.append(f"  private store present, no lock file yet - {B.get('store_why')}")
    for w in B.get("warnings") or []:
        L.append(f"  >>> {w}")
    if B.get("repos"):
        L.append("  REPOSITORIES")
        for r in B["repos"]:
            L += _repo_line(r)
    ml = B["machine_lock"]
    L.append(f"  documents (machine lock): {ml.get('holder') or 'free'}"
             + (f" since {ml.get('since')}" if ml.get("holder") else ""))
    if ml.get("holder") and re.match(r"^rcw-[0-9a-z]+@claude$", ml["holder"]):   # 1.1.0, D-299
        L.append("    >>> a BRIDGE lock under the wrong name: archive on the L14, then take --force and release there")
    L.append("  CLAIMS")
    free, unknown = [], []
    for n, c in B["claims"].items():
        if c == "UNKNOWN":
            unknown.append(n)
        elif c:
            st = (B.get("stale") or {}).get(n) or {}
            tail = "  ".join(x for x in (c.get("mode") or "", st.get("note") or "",
                                         c.get("note") or "") if x)
            L.append(f"    {n:<18} chat {c['chat']!r:<30} since {c.get('since', '?')}  {tail}".rstrip())
            if c.get("touched") and c["touched"] != c.get("since"):
                L.append(f"    {'':<18} last activity {c['touched']}")
            if c.get("link"):
                L.append(f"    {'':<18} {c['link']}")
        else:
            free.append(n)
    if unknown:
        L.append(f"    UNKNOWN (no private store): {', '.join(unknown)}")
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
        c = B["claims"].get(k) if k in B["claims"] else None
        # 1.2.0: c is a dict, None (free), or the STRING "UNKNOWN" when there is no private store.
        if c == "UNKNOWN":
            who = "holder UNKNOWN (no private store)"
        else:
            h = (c or {}).get("chat")
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


def digest(B: dict) -> str:
    """R6(c): the whole board in one line, for the top of a session's output. Says the worrying
    things only - a quiet tree reduces to "nothing held, both repositories level"."""
    if B.get("store") == "ABSENT":
        return ("BOARD: private store ABSENT - every claim is UNKNOWN, not free. "
                "Attach both repositories before taking anything (D-300).")
    bits = []
    held = {k: v for k, v in B["claims"].items() if v and v != "UNKNOWN"}
    flags = B.get("stale") or {}
    bits.append(f"{len(held)} claim(s) held" + (f", {len(flags)} stale" if flags else "")
                if held else "no claims held")
    for r in B.get("repos") or []:
        if not r.get("present"):
            bits.append(f"{r['name']} NOT PRESENT")
        elif r.get("origin_moved"):
            bits.append(f"{r['name']} behind origin (fetch)")
        elif r.get("ahead") or r.get("behind"):
            bits.append(f"{r['name']} {r.get('ahead', 0)}/{r.get('behind', 0)} ahead/behind")
    if not any("ahead" in b or "behind" in b or "NOT PRESENT" in b for b in bits[1:]):
        bits.append("both repositories level")
    if B.get("held_back"):
        bits.append(f"{len(B['held_back'])} ship hold(s) not restored")
    return "BOARD: " + "; ".join(bits) + "."


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--digest", action="store_true",
                    help="R6(c): the one-line summary only, for the top of a session's output")
    ap.add_argument("--probe", dest="probe", action="store_true", default=None,
                    help="ask each origin whether it has moved (read-only ls-remote)")
    ap.add_argument("--no-probe", dest="probe", action="store_false",
                    help="offline: report freshness from the ref mtime only")
    a = ap.parse_args()
    # R2: the printed board probes; --gate and --json do not. check_all must not acquire a network
    # dependency, and the 06:30 dashboard runs unattended.
    do_probe = (not (a.gate or a.json or a.digest)) if a.probe is None else a.probe
    try:
        B = collect(do_probe)
    except Exception as e:                       # the board informs; it must never block anything
        print(f"  work_board: could not read the board ({e})")
        return 0
    if a.json:
        print(json.dumps(B, indent=1, default=str))
        return 0
    if a.digest:
        print(digest(B))
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
