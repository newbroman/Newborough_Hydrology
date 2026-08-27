#!/usr/bin/env python3
"""
snapshot_for_cloud.py — build a text-only replica of the corpus for analysis
elsewhere.

WHY

  Every lint, map and audit in tools/ reads the ODTs. Run on the desktop bridge
  they are round-trips to Martin's machine, and check_all.sh alone exceeds the
  bridge's 45-second ceiling. Run against a replica they take seconds and
  nothing is capped.

  The replica is exact for every purpose except rendering. Images are replaced
  by a 1x1 PNG while entry names, order and frame geometry are preserved, so
  content.xml is byte-identical and pandoc's output from the stripped copy
  matches the original byte for byte (verified 2026-08-23). report9 goes from
  123 MB to 158 KB; the whole corpus fits in about 9 MB.

WHAT IT IS NOT

  It is not an editing surface. odt_edit writes to the real documents, which
  carry the images; a stripped copy written back would destroy them. Edit on
  the device — a full report9 rewrite costs 4.4 s, measured — and re-run this
  to refresh the replica.

Usage:
    python3 tools/snapshot_for_cloud.py            # three tarballs in _to_delete/
    python3 tools/snapshot_for_cloud.py --docs     # documents and tools only
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23.

import argparse
import base64
import os
import sys
import tarfile
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refresh_mirrors import resolve                              # noqa: E402
from doc_paths import MIRROR_DIR, MASTER_ODM, ODT_DIR

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "_to_delete"
STRIP = OUT / "snapshot"

# A 1x1 transparent PNG. Every image entry becomes this; nothing else changes.
TINY = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGA"
    "hKmMIQAAAABJRU5ErkJggg==")

TEXT = (".py", ".sh", ".csv", ".md", ".txt", ".json")
DOC_TREES = [str(MIRROR_DIR), "docs/report/text", "docs/papers",
             "docs/academic_summaries/text", "docs/public_summaries/text",
             "docs/web_tools/text"]
LOOSE = ["PIPELINE_README.md", "readme.md", "working/DECISION_LOG.md", "config.py"]


def strip_one(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    zin = zipfile.ZipFile(src)
    with zipfile.ZipFile(dst, "w") as zo:
        # mimetype must be first and STORED or the file is not an ODF document.
        if "mimetype" in zin.namelist():
            zo.writestr(zipfile.ZipInfo("mimetype"), zin.read("mimetype"),
                        compress_type=zipfile.ZIP_STORED)
        for i in zin.infolist():
            if i.filename == "mimetype":
                continue
            data = (TINY if i.filename.startswith(("Pictures/", "Thumbnails/"))
                    else zin.read(i.filename))
            zo.writestr(zipfile.ZipInfo(i.filename, date_time=i.date_time),
                        data, compress_type=zipfile.ZIP_DEFLATED)


def live_documents() -> list[Path]:
    """Every ODT the mirrors resolve, plus the report sub-documents.

    resolve() is asked rather than the filesystem, because `ls | tail` sorts
    v1_9 after v1_18 and that mistake has already cost one confident wrong
    verdict (refresh_mirrors, 2026-08-23).
    """
    docs = [src for src, _ in resolve()]
    docs += [REPO / str(ODT_DIR) / f"report{i}.odt" for i in range(6, 16)]
    docs += [REPO / str(MASTER_ODM)]
    return [p for p in dict.fromkeys(docs) if p.exists()]


def only(exts):
    def f(ti):
        return ti if ti.isdir() or ti.name.endswith(exts) else None
    return f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", action="store_true",
                    help="documents and tools only; skip outputs/ and src/")
    args = ap.parse_args()
    t0 = time.time()
    os.chdir(REPO)

    docs = live_documents()
    for p in docs:
        strip_one(p, STRIP / p.relative_to(REPO))
    print(f"  stripped {len(docs)} live document(s)")

    made = []
    tar = OUT / "nrg_snap.tar.gz"
    with tarfile.open(tar, "w:gz") as tf:
        tf.add(STRIP, arcname="odt", filter=only((".odt", ".odm")))
        tf.add("tools", arcname="tools", filter=only(TEXT))
        for d in DOC_TREES:
            if os.path.isdir(d):
                tf.add(d, arcname=d, filter=only(TEXT))
        for f in LOOSE:
            if os.path.isfile(f):
                tf.add(f, arcname=f)
        tf.add("changelogs", arcname="changelogs", filter=only(TEXT))
    made.append(tar)

    if not args.docs:
        t = OUT / "nrg_outputs.tar.gz"
        # outputs/ is 227 MB of figures and 4.6 MB of CSVs. Only the CSVs are
        # read by cite_check and the claims register.
        with tarfile.open(t, "w:gz") as tf:
            tf.add("outputs", arcname="outputs", filter=only((".csv", ".txt")))
            tf.add("data", arcname="data", filter=only(TEXT))
        made.append(t)

        t = OUT / "nrg_src.tar.gz"
        # src/ is 876 MB, almost all of it committed figures. record_basis_lint
        # needs the .py files and nothing else.
        with tarfile.open(t, "w:gz") as tf:
            for p in sorted(Path("src").rglob("*.py")):
                if "__pycache__" not in p.parts:
                    tf.add(p, arcname=str(p))
            for p in sorted(Path(".").glob("*.py")):
                tf.add(p, arcname=str(p))
        made.append(t)

    for m in made:
        print(f"  {m.relative_to(REPO)}   {m.stat().st_size / 1e6:.1f} MB")
    print(f"\n  {time.time() - t0:.0f}s. Stage these, unpack, and `touch` the "
          f"mirrors —\n  refresh_mirrors --check compares modification times "
          f"only, so a freshly\n  unpacked ODT reads as newer than its mirror.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
