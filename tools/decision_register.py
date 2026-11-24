#!/usr/bin/env python3
"""decision_register.py — mint a D-number from ORIGIN's decision log, and gate a collision (T-187).

WHY. On 2026-11-08 D-318 was written twice — once for nrg_git.sh --push, once for the censored-fit
gradient gate — and the second had to be renumbered D-319 (whose entry records the irony: task_register.py,
built that morning for exactly this, was not applied to D-numbers). A chat took max+1 over the log in ITS
clone; another chat's entry was on GitHub, or in a tree, it could not see.

WHAT IT DOES, over working/DECISION_LOG.md (private; read through .git-working):

    next-id     fetch the private origin, and print max(D) + 1 over origin's log UNIONED with this tree's
                — the union because origin alone would re-mint an id written here and not yet pushed.
                Origin unreachable: the local answer, marked LOCAL ONLY.
    --check     the gate (check_all): FAIL when one log carries a D-number twice, or when a D-number is on
                both sides with a different TITLE. The heading's trailing "(date · status: …)" is left out
                of the comparison, because a status may legitimately move to "superseded" by an appended
                banner. Silent about origin when it cannot be read; it says so rather than guess.
    --selftest  the parsing and the comparison on fixed text.

It does not publish. Adding a decision is Martin's call (CLAUDE.md §7), and the log is private, so the
window between minting and pushing is closed by running next-id at the moment of writing and by the gate.

    python3 tools/decision_register.py next-id
    python3 tools/decision_register.py --check
    python3 tools/decision_register.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-24. New (T-187).

import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
LOG_REL = "working/DECISION_LOG.md"
LOG = REPO / LOG_REL
GITDIR = REPO / ".git-working"
HEAD_RE = re.compile(r"^#{2,4}\s*(D-(\d{3,}))\b\s*(.*)$")


def _git(*args: str, timeout: int = 60):
    return subprocess.run(["git", "--no-optional-locks", f"--git-dir={GITDIR}", f"--work-tree={REPO}", *args],
                          capture_output=True, text=True, timeout=timeout)


def title(rest: str) -> str:
    """A heading's title without its trailing '(date · status: …)' and with spacing normalised."""
    rest = re.sub(r"\s*\((\d{4}-\d{2}-\d{2})[^()]*\)\s*$", "", rest.strip())
    return re.sub(r"\s+", " ", rest).strip()


def entries(text: str) -> list[tuple[str, int, str]]:
    """(D-id, number, title) for every heading, in order."""
    out = []
    for line in text.splitlines():
        m = HEAD_RE.match(line)
        if m:
            out.append((m.group(1), int(m.group(2)), title(m.group(3))))
    return out


def read_origin(fetch: bool = True) -> str | None:
    if not GITDIR.is_dir():
        return None
    if fetch:
        _git("fetch", "-q", "origin", "main")
    p = _git("show", f"origin/main:{LOG_REL}")
    return p.stdout if p.returncode == 0 else None


def next_id(fetch: bool = True) -> tuple[str, str]:
    local = entries(LOG.read_text(encoding="utf-8")) if LOG.is_file() else []
    o = read_origin(fetch)
    n = max([e[1] for e in local] or [0])
    if o is None:
        return f"D-{n + 1:03d}", "LOCAL ONLY — origin unreadable; this id is not reserved"
    n = max(n, max([e[1] for e in entries(o)] or [0]))
    return f"D-{n + 1:03d}", "from origin+local"


def problems(local_text: str, origin_text: str | None) -> list[str]:
    out = []
    sides = [("local", local_text)] + ([("origin", origin_text)] if origin_text is not None else [])
    maps = {}
    for side, text in sides:
        seen: dict[str, str] = {}
        for did, _n, t in entries(text):
            if did in seen:
                out.append(f"{did} appears twice in the {side} log: '{seen[did][:60]}' / '{t[:60]}'")
            else:
                seen[did] = t
        maps[side] = seen
    if "origin" in maps:
        for did, t in maps["local"].items():
            ot = maps["origin"].get(did)
            if ot is not None and ot != t:
                out.append(f"{did} differs between this tree and origin:\n          here:   {t[:100]}\n"
                           f"          origin: {ot[:100]}")
    return out


def check() -> int:
    if not LOG.is_file():
        print(f"  decision_register: no {LOG_REL} (private store absent) — NOT checked")
        return 0
    o = read_origin(fetch=False)
    bad = problems(LOG.read_text(encoding="utf-8"), o)
    for b in bad:
        print(f"  FAIL  {b}")
    if o is None:
        print("  decision_register: origin's log unreadable — agreement with origin NOT checked")
    n = len(entries(LOG.read_text(encoding="utf-8")))
    print(f"  decision_register: {n} decisions, {'no collision' if not bad else f'{len(bad)} collision(s)'}")
    return 1 if bad else 0


def selftest() -> int:
    a = ("### D-001  First thing (2026-01-01 · status: active)\n"
         "### D-002  Second thing (2026-01-02 · status: active)\n")
    b = a.replace("status: active)\n### D-002", "status: superseded)\n### D-002")
    c = a + "### D-002  Something else entirely (2026-01-03 · status: active)\n"
    d = a.replace("Second thing", "A different second thing")
    ok = (not problems(a, b)                               # a status change is not a collision
          and any("twice" in x for x in problems(c, a))    # a duplicate in one log is
          and any("differs" in x for x in problems(a, d))  # a different title on the two sides is
          and title("Mint ids  (2026-11-24 · status: active)") == "Mint ids"
          and [e[0] for e in entries(a)] == ["D-001", "D-002"])
    print(f"  decision_register --selftest: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "--check"
    if cmd == "next-id":
        did, how = next_id(fetch="--no-fetch" not in argv)
        print(did)
        print(f"  ({how})", file=sys.stderr)
        return 0
    if cmd == "--check":
        return check()
    if cmd == "--selftest":
        return selftest()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
