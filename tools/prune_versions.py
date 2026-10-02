#!/usr/bin/env python3
"""
prune_versions — docs/ holds the CURRENT version of each document; backups live in archive/.

WHY. docs/report, docs/papers/* and docs/academic_summaries are where a reader goes to find
the current documents (Martin, 2026-10-02: "its meant to be the place to go to find the
current docs. Backups should be in a different folder and not public facing"). Every edit
batch saves to a bumped filename and leaves the prior version on disk (the versioned-document
rule), which is right while editing - but the tail used to stay in docs/ for good.

WHAT IT DOES, per versioned family (refresh_mirrors.SOURCES):

    the NEWEST            stays in docs/. Never moved, never removed.
    every older version   MOVES to archive/<its path below docs/>, with its
                          `.odt.media.json` sidecar (docs/report/X -> archive/report/X).
    the archive           is capped at --keep backups (default 10): the OLDEST - the origin
                          of the family, Martin's call 2026-09-10 - and the most recent of
                          the rest. Older backups are removed from this machine.

archive/ is gitignored (not public) and excluded from the Drive upload filter, because
every version was uploaded to Drive while it was still in docs/ (`rclone copy` never deletes,
so Drive keeps every version ever archived). The ship runs this only AFTER a successful
Drive archive (nrg_git.sh 1.25.0). As a second guard, a backup newer than the last Drive
archive (`.last_drive_archive`) is never moved or removed: it stays where it is, reported,
until the next archive has uploaded it.

Pre-edit snapshots (`..._v2_0_4.pre-tablegen-2026-09-19.odt`) are not versions of the family
and are left alone.

WHAT IT REFUSES TO DO:

  * run at all when `odt_media verify` is not green. Superseded documents may be stubs whose
    images live in docs/media_store, and verify proves each still rebuilds byte-identically.
  * move or remove a document without its sidecar (an orphaned sidecar FAILs verify).
  * change anything without --apply. The default is a plan.

ORPHANED STORE IMAGES are reported, never deleted (D-081, D-149).

Usage:
    python3 tools/prune_versions.py                 # plan, all families
    python3 tools/prune_versions.py --keep 12       # backups kept in archive/
    python3 tools/prune_versions.py --only Methods
    python3 tools/prune_versions.py --apply
"""
from __future__ import annotations

__version__ = "1.2.1"  # Hollingham (2026) — 2026-10-02. Default --keep 10 backups (Martin: "lets
#   keep it at 10 versions"; D-151 third note).
# 1.2.0  # Hollingham (2026) — 2026-10-02. docs/ keeps only the newest version;
#   older versions MOVE to archive/<path below docs/> (gitignored, not on Drive's upload
#   filter); the archive keeps --keep backups (oldest + most recent); removal refused for a
#   backup newer than .last_drive_archive. D-151 note 2026-10-02.
# 1.1.0  # Hollingham (2026) — 2026-10-02. Default --keep 5; the ship runs it after a successful
#   Drive archive (nrg_git.sh 1.25.0).
# 1.0.0  # Hollingham (2026) — 2026-09-10. First version.

import argparse
import json
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from refresh_mirrors import SOURCES, _version_key  # noqa: E402
import odt_media  # noqa: E402

STORE = REPO / "docs" / "media_store"
ARCHIVE = REPO / "archive"
DOCS = REPO / "docs"
MARKER = REPO / ".last_drive_archive"


def _name_rx(pattern: str) -> re.Pattern:
    """A family's filename pattern, with `*` admitting only a version tag, so a pre-edit
    snapshot (`_v2_0_4.pre-tablegen-...odt`) is not taken for a version."""
    base = pattern.split("/")[-1]
    return re.compile("^" + re.escape(base).replace(r"\*", "[_v0-9]*") + "$")


def families() -> dict[str, list[Path]]:
    """Every versioned SOURCES pattern, resolved to its files in docs/, newest last."""
    out: dict[str, list[Path]] = {}
    for pattern, _mirror, versioned in SOURCES:
        if not versioned or not pattern.startswith("docs/"):
            continue
        rx = _name_rx(pattern)
        matches = sorted((p for p in REPO.glob(pattern) if rx.match(p.name)), key=_version_key)
        if matches:
            out[pattern] = matches
    return out


def archived(pattern: str) -> list[Path]:
    """Backups of a family anywhere under archive/ (older moves used a flatter layout)."""
    rx = _name_rx(pattern)
    return sorted((p for p in ARCHIVE.rglob("*.odt") if rx.match(p.name)), key=_version_key) \
        if ARCHIVE.is_dir() else []


def archive_path(f: Path) -> Path:
    return ARCHIVE / f.relative_to(DOCS)


def plan(keep: int, only: str | None):
    """(family, newest, to_move, to_remove) per family."""
    rows = []
    for pattern, files in families().items():
        if only and only.lower() not in pattern.lower():
            continue
        newest, move = files[-1], files[:-1]
        backups = sorted({*archived(pattern), *(archive_path(f) for f in move)},
                         key=_version_key)
        remove: list[Path] = []
        if len(backups) > keep:
            oldest = backups[0]
            kept = {oldest, *[b for b in reversed(backups) if b != oldest][: keep - 1]}
            remove = [b for b in backups if b not in kept]
        rows.append((pattern, newest, move, remove))
    return rows


def referenced_images() -> set[str]:
    names: set[str] = set()
    for side in [*REPO.glob("docs/**/*.odt.media.json"), *REPO.glob("archive/**/*.odt.media.json")]:
        try:
            d = json.loads(side.read_text(encoding="utf-8"))
        except Exception:
            continue
        for entry in d.get("images", d.get("entries", [])):
            n = entry.get("store") if isinstance(entry, dict) else None
            if n:
                names.add(Path(n).name)
    return names


def _move(f: Path) -> None:
    dest = archive_path(f)
    dest.parent.mkdir(parents=True, exist_ok=True)
    for src, dst in ((f, dest), (odt_media.sidecar_path(f), odt_media.sidecar_path(dest))):
        if src.is_file():
            src.rename(dst)          # a rename: permitted on the bridge mount, where unlink is not


def _remove(f: Path) -> None:
    for victim in (f, odt_media.sidecar_path(f)):
        if victim.is_file():
            try:
                victim.unlink()
            except OSError:
                odt_media._retire(victim)   # the mount refuses unlink


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", type=int, default=10,
                    help="backups kept in archive/ per family, the oldest included (default 10)")
    ap.add_argument("--only", help="substring of the family pattern")
    ap.add_argument("--apply", action="store_true", help="move and remove; default is a plan")
    a = ap.parse_args(argv[1:])

    if a.keep < 2:
        print("  --keep must be at least 2 (the oldest and the most recent backup)")
        return 1

    if a.apply:
        print("Gate: odt_media verify")
        if odt_media.verify(quiet=True) != 0:
            print("  REFUSED — the media store is not green. Fix that first: a prune on top")
            print("            of a broken store removes the evidence of what broke.")
            return 1

    marker = MARKER.stat().st_mtime if MARKER.is_file() else None
    n_move = n_rm = n_held = n_stay = 0
    mb_rm = 0.0
    for pattern, newest, move, remove in plan(a.keep, a.only):
        fam = pattern.split("/")[-1]
        # Not yet on Drive -> neither moved (archive/ is outside the upload filter, so a
        # version moved before its first upload would never reach Drive) nor removed.
        unsafe = lambda f: f.is_file() and (marker is None or f.stat().st_mtime > marker)
        stay = [f for f in move if unsafe(f)]
        move = [f for f in move if f not in stay]
        held = [r for r in remove if unsafe(r)]
        remove = [r for r in remove if r not in held]
        size = sum(r.stat().st_size for r in remove if r.is_file()) / 1048576
        state = "ok    " if not (move or remove or held or stay) else "tidy  "
        print(f"  {state}  {fam}  current {newest.relative_to(REPO)}")
        if move:
            print(f"            move {len(move)} to {archive_path(newest).parent.relative_to(REPO)}/: "
                  + ", ".join(f.name for f in move))
        if remove:
            print(f"            remove {len(remove)} old backup(s), {size:.1f} MB (on Drive): "
                  + ", ".join(r.name for r in remove))
        if stay:
            print(f"            LEAVE {len(stay)} in docs/ until the next Drive archive: "
                  + ", ".join(f.name for f in stay))
        if held:
            print(f"            KEEP {len(held)} newer than the last Drive archive: "
                  + ", ".join(r.name for r in held))
        n_move += len(move); n_rm += len(remove); n_held += len(held); n_stay += len(stay)
        mb_rm += size
        if a.apply:
            for f in move:
                _move(f)
            for r in remove:
                _remove(r if r.is_file() else archive_path(r))

    verb = "" if a.apply else "would be "
    print(f"\n  {n_move} version(s) {verb}moved to archive/; {n_rm} backup(s), {mb_rm:.1f} MB "
          f"{verb}removed" + (f"; {n_held + n_stay} left alone (not yet on Drive)" if n_held + n_stay else ""))

    if a.apply and (n_move or n_rm):
        rc = odt_media.verify(quiet=True)
        print(f"  post-prune odt_media verify: {'OK' if rc == 0 else 'FAIL'}")
        if rc:
            return 1

    referenced = referenced_images()
    if STORE.is_dir() and referenced:
        orphans = [f for f in STORE.glob("*") if f.name not in referenced]
        if orphans:
            mb = sum(f.stat().st_size for f in orphans) / 1048576
            print(f"  note: {len(orphans)} store image(s) ({mb:.1f} MB) referenced by no "
                  f"surviving sidecar — reported, not removed")

    print(f"\nprune_versions: {'APPLIED' if a.apply else 'PLAN ONLY'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
