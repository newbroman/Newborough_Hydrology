#!/usr/bin/env python3
"""drive_manifest_list.py — what a Drive pull should fetch, and whether it arrived intact (T-118).

working/DRIVE_MANIFEST.json is written by every archive (nrg_git.sh write_drive_manifest): path -> MD5
of each document the archive filter selected on disk, after prune_versions. It is the current set.
Drive also keeps every superseded version (the archive copies, never syncs), so a pull by filter
alone brings those back; a pull by this list does not.

  python3 tools/drive_manifest_list.py list REMOTE    # print the manifest's paths, one per line
                                                      # exit 2 (message on stderr) if there is no
                                                      # usable manifest for REMOTE: callers fall back
  python3 tools/drive_manifest_list.py plan REMOTE    # 1.1.0 (T-205, D-328): the paths a pull should
                                                      # fetch, decided by CONTENT: missing here, or
                                                      # here as a copy some earlier archive recorded
                                                      # (stale). A file whose MD5 no archive ever
                                                      # recorded is an edit not yet archived: kept,
                                                      # and named on stderr. Exit 2 as for list.
  python3 tools/drive_manifest_list.py verify         # compare local MD5s with the manifest; report,
                                                      # never fail (a file newer here is kept by
                                                      # --update on purpose)

Spec working/updates/NRG_spec_T118_drive_pull_manifest_2026-10-21.md (Martin 2026-10-21 21:29,
"I approve, include the optional check").
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-11-24 (T-205, D-328). `plan`: what to fetch by MD5
#   against the manifest and its history in the private repository, replacing rclone --update's mtimes.
# 1.0.0  # Hollingham (2026) — 2026-10-21. New (T-118).

import hashlib
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = REPO / "working" / "DRIVE_MANIFEST.json"


def load(remote: str | None = None) -> dict | None:
    if not MANIFEST.exists():
        print(f"no {MANIFEST.relative_to(REPO)} (private store absent?)", file=sys.stderr)
        return None
    try:
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"{MANIFEST.relative_to(REPO)} unreadable: {e}", file=sys.stderr)
        return None
    files = m.get("files") or {}
    if not files:
        print(f"{MANIFEST.relative_to(REPO)} lists no files", file=sys.stderr)
        return None
    if remote and m.get("remote") and m["remote"] != remote:
        print(f"manifest describes {m['remote']}, not {remote}", file=sys.stderr)
        return None
    return m


def md5(p: pathlib.Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def history() -> dict[str, set]:
    """path -> every MD5 any committed manifest recorded for it (the private repository's history)."""
    import subprocess
    seen: dict[str, set] = {}
    g = ["git", f"--git-dir={REPO / '.git-working'}", f"--work-tree={REPO}"]
    try:
        revs = subprocess.run(g + ["log", "--format=%H", "--", "working/DRIVE_MANIFEST.json"],
                              capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return seen
    for rev in revs:
        r = subprocess.run(g + ["show", f"{rev}:working/DRIVE_MANIFEST.json"], capture_output=True, text=True)
        try:
            for p, h in (json.loads(r.stdout).get("files") or {}).items():
                seen.setdefault(p, set()).add(h)
        except ValueError:
            continue
    return seen


def superseded(files: dict) -> set:
    """Manifest paths that are not their versioned family's newest (the archive is written before the
    prune, so it names them; a pull brings down the current set, T-118)."""
    import re
    sys.path.insert(0, str(REPO / "tools"))
    try:
        from refresh_mirrors import SOURCES, _version_key
    except Exception:
        return set()
    out = set()
    for pattern, _mirror, versioned in SOURCES:
        if not versioned:
            continue
        rx = re.compile("^" + re.escape(pattern).replace(r"\*", "[_v0-9]*") + "$")
        fam = sorted((p for p in files if rx.match(p)), key=lambda p: _version_key(pathlib.Path(p)))
        out.update(fam[:-1])
    return out


def plan(m: dict) -> tuple[list, list]:
    """(fetch, kept): fetch what is missing or a stale archived copy; keep an edit no archive recorded."""
    past = None
    fetch, kept = [], []
    old = superseded(m["files"])
    for p, h in sorted(m["files"].items()):
        f = REPO / p
        if not f.exists():
            # prune_versions moved a superseded version to archive/<below docs/>: present, if it is this copy
            a = REPO / "archive" / p[len("docs/"):] if p.startswith("docs/") else None
            if not (a and a.is_file() and md5(a) == h) and p not in old:
                fetch.append(p)
            continue
        here = md5(f)
        if here == h:
            continue
        if past is None:
            past = history()
        (fetch if here in past.get(p, set()) else kept).append(p)
    return fetch, kept


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "plan", "verify"):
        print(__doc__, file=sys.stderr)
        return 1
    if sys.argv[1] == "list":
        m = load(sys.argv[2] if len(sys.argv) > 2 else None)
        if m is None:
            return 2
        sys.stdout.write("".join(p + "\n" for p in sorted(m["files"])))
        return 0
    if sys.argv[1] == "plan":
        m = load(sys.argv[2] if len(sys.argv) > 2 else None)
        if m is None:
            return 2
        fetch, kept = plan(m)
        for p in kept:
            print(f"  KEPT (an edit here that no archive recorded - archive it, or move it aside to take Drive's): {p}",
                  file=sys.stderr)
        sys.stdout.write("".join(p + "\n" for p in fetch))
        return 0
    m = load()
    if m is None:
        print("  md5 check: skipped (no manifest)")
        return 0
    missing, differ = [], []
    for p, h in sorted(m["files"].items()):
        f = REPO / p
        if not f.exists():
            missing.append(p)
        elif md5(f) != h:
            differ.append(p)
    n = len(m["files"])
    print(f"  md5 check: {n - len(missing) - len(differ)} of {n} match the manifest "
          f"(archived {m.get('archived_at', '?')})")
    for p in missing:
        print(f"    missing here: {p}")
    for p in differ:
        print(f"    differs (newer here, or Drive changed since the archive): {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
