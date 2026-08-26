#!/usr/bin/env python3
"""
drive_lag.py — which canonical documents have been edited since the last upload
to Google Drive.

WHY

    The .odt and .odm documents are the canonical text of this project and they
    are in NO repository. `.gitignore` excludes them deliberately: the
    sub-documents are ~200 MB each and the markdown mirrors are the git-diffable
    surface. That is the right call, and it has one consequence nobody was
    checking — **the only copies of the canonical documents are this disk and
    Google Drive.** Between an edit and the next `rclone copy`, a document exists
    once.

    BOOTSTRAP.md already knew this. Its step 4 ends:

        touch .last_drive_archive

    with the reason "mark the archive current so the toolkit does not report
    drift that is not there". But no tool ever read that marker. The instruction
    was live, the check it was written for was never built, and on 2026-08-26 the
    marker did not exist at all — so a fresh machine was being told to create a
    file that nothing consumed, and this machine had no record of when the
    documents were last archived.

    This is that check.

WHAT IT COMPARES

    Every source in refresh_mirrors.SOURCES — the same list the mirrors are built
    from, so a document cannot be canonical for one tool and invisible to the
    other — against the mtime of `.last_drive_archive`. A document newer than the
    marker has been edited since the last upload.

    Versioned documents resolve to the highest version, as everywhere else. An
    older version that has never been uploaded is NOT reported: it is superseded,
    and telling you to archive it would be telling you to archive history.

EXIT

    0   always, by default. Advisory, for the same reason as export_lag: an
        upload is slow and manual, and a gate that fires between every edit and
        the next sync would be switched off inside a week.
    --strict makes it gate, for use before stepping away from the machine.

    A missing marker is reported loudly and is NOT treated as "everything is
    stale" — it means the question cannot be answered, which is a different
    thing and wants a different action.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-26

import argparse
import datetime as _dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from refresh_mirrors import SOURCES, _version_key  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[1]
MARKER = REPO / ".last_drive_archive"
REMOTE = "gdrive:NRG_documents"


def canonical_documents() -> list[pathlib.Path]:
    """The current .odt/.odm for every source refresh_mirrors mirrors."""
    docs: list[pathlib.Path] = []
    for pattern, _mirror_dir, versioned in SOURCES:
        matches = sorted(REPO.glob(pattern))
        if not matches:
            continue
        if versioned:
            matches = [max(matches, key=_version_key)]
        docs.extend(matches)
    return sorted(set(docs))


def _stamp(ts: float) -> str:
    return _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when documents are unarchived")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    docs = canonical_documents()
    if not docs:
        print("  drive_lag: no canonical documents found — are the .odt files here?")
        return 1

    if not MARKER.exists():
        print("  drive_lag: NO MARKER — .last_drive_archive does not exist, so "
              "there is no record of\n"
              "             when these documents were last copied to Drive. "
              f"{len(docs)} canonical\n"
              "             document(s) are on this disk and in no repository.")
        print(f"             Archive them, then mark it:\n"
              f"               rclone copy . {REMOTE} --include '*.odt' "
              f"--include '*.odm' --progress\n"
              f"               touch .last_drive_archive")
        return 1 if a.strict else 0

    cutoff = MARKER.stat().st_mtime
    stale = [(p, p.stat().st_mtime) for p in docs if p.stat().st_mtime > cutoff]

    if not a.quiet:
        print(f"  drive_lag: last archived {_stamp(cutoff)} — "
              f"{len(docs)} canonical document(s) checked")
    if not stale:
        if not a.quiet:
            print("  drive_lag: OK — every canonical document is in the archive")
        return 0

    print(f"  {len(stale)} document(s) edited since the last archive and held "
          f"only on this disk:")
    for p, ts in sorted(stale, key=lambda x: -x[1]):
        size = p.stat().st_size / 1e6
        print(f"    UNARCHIVED  {p.relative_to(REPO)}   "
              f"{_stamp(ts)}  ({size:.1f} MB)")
    print(f"    rclone copy . {REMOTE} --include '*.odt' --include '*.odm' "
          f"--progress && touch .last_drive_archive")
    return 1 if a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
