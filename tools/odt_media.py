#!/usr/bin/env python3
"""Store each document image ONCE, and keep every ODT self-contained (W154, D-149).

THE PROBLEM. Paper1_v1_44.odt is 24.8 MB, of which 24.7 MB - 100%, across 24
files - is `Pictures/`; its text is under 100 KB. Versioned documents are never
edited in place, so every edit batch writes another whole copy carrying
byte-identical images. Measured 2026-09-09: twenty Paper 1 versions on disk
holding 497 MB, and TWENTY-FIVE distinct images between them. The academic
summaries are worse in proportion - sixteen files, six distinct images, 150 MB.
Every copy is uploaded to Drive, and a 25 MB upload is what broke the archive
(W153).

WHY NOT REFERENCE THE IMAGES FROM INSIDE THE ODT. Because it was tried, and it
fails silently. ODF can point `xlink:href` outside the package, and through this
project's own toolchain (LibreOffice 24.2, headless, PDF export):

    embedded, as a control              10,694,800 bytes   35 images
    xlink:href="media/x.png"               523,875 bytes    2 images
    xlink:href="./media/x.png"             523,875 bytes    2 images
    xlink:href="file:///abs/.../x.png"  10,694,800 bytes   35 images

Relative links do not resolve at all. Absolute file:// links work perfectly and
bake a machine-specific path into the document, so it renders on one machine at
one path and nowhere else - the forecaster.html trap with its polarity reversed.
And the disqualifying property is not the failure but the SILENCE: the broken
export succeeded, exit 0, 58 pages, correct /Producer, artefact_lint Check C
green, and 33 of 35 figures gone. A manuscript could reach submission that way.

SO THE DEDUPLICATION HAPPENS OUTSIDE THE DOCUMENT, where no part of ODF,
LibreOffice or a journal is involved:

    docs/media_store/<md5><ext>        each distinct image exactly once
    <document>.odt                     SUPERSEDED versions stripped, ~112 KB
    <document>.odt.media.json          entry order, per-entry zip metadata, md5s

THE CURRENT VERSION OF EVERY DOCUMENT IS NEVER STRIPPED. Only superseded ones
are, so build_pdfs.sh, export_lag, doc_version_sync, refresh_mirrors and every
editing path go on seeing a whole file and need no change. Stripping is
something that happens to history.

BYTE-IDENTICAL OR IT DID NOT WORK. The sidecar records the md5 of the ORIGINAL
whole file, and `verify` rebuilds every stripped document in memory and checks
it. That is the whole guarantee, and it is a gate in check_all rather than an
assumption: "the archive is still reconstructable" is a thing that fails.

The store is content-addressed, so it is append-only - an image is written once
and never modified - which is why re-running is cheap and why `rclone copy`
uploads each image exactly once, ever.

The store is NOT committed. D-081's shape applies: these figures derive from
licensed aerial imagery, and a public repository attached to a journal
submission is exactly the place that licence terms reach. It goes to Drive with
the ODTs. The sidecars ARE committed - they are text, they carry md5s and no
image data, and they are the integrity record.

Usage:
    python3 tools/odt_media.py verify              # gate: every stripped ODT rebuilds
    python3 tools/odt_media.py strip <odt>...      # externalise Pictures/
    python3 tools/odt_media.py rehydrate <odt>...  # put them back, in place
    python3 tools/odt_media.py plan                # what would strip, and the saving
    python3 tools/odt_media.py --selftest          # prove the round trip and the failure
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-09. First version (W154, D-149).

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STORE = REPO / "docs" / "media_store"
PIC = "Pictures/"

# The families that duplicate. Measured 2026-09-09; the Methods Supplement and
# Paper 1 SI carry no images at all, and the report chapters carry 86 distinct
# images with NO duplication because they are not versioned - which is the
# behaviour this tool recreates for everything else, so they are left alone.
FAMILIES = [
    ("docs/papers/paper_1", r"^Paper1_v(\d+)_(\d+)\.odt$"),
    ("docs/papers/paper_2", r"^Hollingham_2026_Paper2_amended_v(\d+)()\.odt$"),
    ("docs/academic_summaries", r"^academic_Summary_v(\d+)_(\d+)\.odt$"),
    ("docs/academic_summaries", r"^crynodeb_academaidd_v(\d+)_(\d+)\.odt$"),
    ("docs/report", r"^Supplementary_Material_v(\d+)_(\d+)\.odt$"),
]


def _md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def sidecar_path(odt: Path) -> Path:
    return odt.with_suffix(odt.suffix + ".media.json")


def is_stripped(odt: Path) -> bool:
    return sidecar_path(odt).is_file()


def _members(z: zipfile.ZipFile):
    return [i for i in z.infolist()]


def strip(odt: Path, dry_run: bool = False, force: bool = False) -> tuple[int, int]:
    """Move Pictures/ into the store. Returns (images, bytes freed)."""
    if is_stripped(odt):
        return (0, 0)
    # THE NEWEST VERSION OF A FAMILY IS NEVER STRIPPED, and this is a guard
    # rather than a note because the note was not enough: within a minute of the
    # rule being written, `strip docs/academic_summaries/*.odt` stripped the two
    # CURRENT summaries along with their history. Everything downstream -
    # build_pdfs, export_lag, doc_version_sync, refresh_mirrors, opening the file
    # - assumes the current document is whole.
    if not force and odt.resolve() in {p.resolve() for p in _newest()}:
        print(f"  REFUSED  {odt.name} is the CURRENT version of its family — "
              f"stripping it would leave the live document unopenable. --force to override.")
        return (0, 0)
    raw = odt.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = _members(z)
        pics = [i for i in infos if i.filename.startswith(PIC)]
        if not pics:
            return (0, 0)
        side = {
            "tool_version": __version__,
            "odt_md5": _md5(raw),
            "odt_bytes": len(raw),
            "order": [i.filename for i in infos],
            "pictures": {},
        }
        blobs = {}
        for i in pics:
            data = z.read(i.filename)
            h = _md5(data)
            side["pictures"][i.filename] = {
                "md5": h,
                "ext": Path(i.filename).suffix.lower(),
                "compress_type": i.compress_type,
                "date_time": list(i.date_time),
                "external_attr": i.external_attr,
                "create_system": i.create_system,
                "extra": i.extra.hex(),
                "bytes": len(data),
            }
            blobs[h] = (data, Path(i.filename).suffix.lower())
        if dry_run:
            return (len(pics), sum(p["bytes"] for p in side["pictures"].values()))

        STORE.mkdir(parents=True, exist_ok=True)
        for h, (data, ext) in blobs.items():
            dest = STORE / f"{h}{ext}"
            if not dest.exists():                       # content-addressed: append-only
                dest.write_bytes(data)
            elif _md5(dest.read_bytes()) != h:          # cannot happen, so say so if it does
                raise SystemExit(f"  FAULT  store collision at {dest.name}")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as out:
            for i in infos:
                if i.filename.startswith(PIC):
                    continue
                zi = zipfile.ZipInfo(i.filename, i.date_time)
                zi.compress_type = i.compress_type
                zi.external_attr = i.external_attr
                zi.create_system = i.create_system
                zi.extra = i.extra
                out.writestr(zi, z.read(i.filename))

    # Prove the rebuild BEFORE the original is replaced. Nothing is destroyed on
    # the strength of an intention.
    rebuilt = _rebuild(buf.getvalue(), side)
    if _md5(rebuilt) != side["odt_md5"]:
        # NOT an error, and not fatal to a batch: some archives cannot be
        # reproduced byte-for-byte by Python's zip writer. Supplementary_Material
        # v1_6 and its siblings were written with per-entry DATA DESCRIPTORS
        # (flag bit 3, so flag_bits 2056); `writestr` chooses its own flag bits
        # and will not emit one. The file is simply left whole, because the
        # guarantee this tool sells is byte-identity and a file it cannot
        # guarantee is a file it does not touch.
        print(f"  LEFT WHOLE  {odt.name}: this archive cannot be rebuilt "
              f"byte-for-byte (zip flag bits), so it is not stripped")
        return (0, 0)

    odt.write_bytes(buf.getvalue())
    sidecar_path(odt).write_text(json.dumps(side, indent=1), encoding="utf-8")
    return (len(pics), sum(p["bytes"] for p in side["pictures"].values()))


def _rebuild(stripped_bytes: bytes, side: dict) -> bytes:
    """The original archive, from the stripped one plus the store."""
    out_buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(stripped_bytes)) as zs:
        have = {i.filename: i for i in zs.infolist()}
        with zipfile.ZipFile(out_buf, "w") as out:
            for name in side["order"]:
                if name in have:
                    i = have[name]
                    zi = zipfile.ZipInfo(name, i.date_time)
                    zi.compress_type = i.compress_type
                    zi.external_attr = i.external_attr
                    zi.create_system = i.create_system
                    zi.extra = i.extra
                    out.writestr(zi, zs.read(name))
                else:
                    m = side["pictures"][name]
                    src = STORE / f"{m['md5']}{m['ext']}"
                    data = src.read_bytes()
                    if _md5(data) != m["md5"]:
                        raise SystemExit(f"  FAULT  {src.name} does not match its own name")
                    zi = zipfile.ZipInfo(name, tuple(m["date_time"]))
                    zi.compress_type = m["compress_type"]
                    zi.external_attr = m["external_attr"]
                    zi.create_system = m["create_system"]
                    zi.extra = bytes.fromhex(m["extra"])
                    out.writestr(zi, data)
    return out_buf.getvalue()


def rehydrate(odt: Path) -> bool:
    side_p = sidecar_path(odt)
    if not side_p.is_file():
        print(f"  skip   {odt.name} is not stripped")
        return True
    side = json.loads(side_p.read_text(encoding="utf-8"))
    rebuilt = _rebuild(odt.read_bytes(), side)
    if _md5(rebuilt) != side["odt_md5"]:
        print(f"  FAULT  {odt.name}: rebuild does not match the recorded md5")
        return False
    odt.write_bytes(rebuilt)
    _retire(side_p)
    print(f"  restored {odt.name}  ({len(rebuilt)/1048576:.1f} MB)")
    return True


def _retire(path: Path) -> None:
    """Remove a sidecar, on a filesystem that may refuse to remove anything.

    The bridge mount denies unlink - the same constraint `working/wgit` works
    around for git locks - so a plain .unlink() raises PermissionError and
    aborts a multi-file rehydrate halfway. Rename into _to_delete/ instead: a
    rename is permitted where a delete is not.
    """
    try:
        path.unlink()
        return
    except (PermissionError, OSError):
        pass
    bin_dir = REPO / "_to_delete" / "media_sidecars"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dest = bin_dir / path.name
    n = 0
    while dest.exists():
        n += 1
        dest = bin_dir / f"{path.name}.{n}"
    path.rename(dest)


def verify(quiet: bool = False) -> int:
    """Rebuild every stripped document IN MEMORY and check it. The gate."""
    bad = n = 0
    for side_p in sorted(REPO.glob("docs/**/*.odt.media.json")):
        odt = Path(str(side_p)[: -len(".media.json")])
        n += 1
        if not odt.is_file():
            print(f"  FAULT  {side_p.name} has no document beside it")
            bad += 1
            continue
        try:
            side = json.loads(side_p.read_text(encoding="utf-8"))
            got = _md5(_rebuild(odt.read_bytes(), side))
        except SystemExit as e:
            print(f"  FAULT  {odt.name}: {e}")
            bad += 1
            continue
        except Exception as e:
            print(f"  FAULT  {odt.name}: {type(e).__name__}: {e}")
            bad += 1
            continue
        if got != side["odt_md5"]:
            print(f"  FAULT  {odt.name}: rebuilds to {got[:12]}, recorded {side['odt_md5'][:12]}")
            bad += 1
    store_n = len(list(STORE.glob("*"))) if STORE.is_dir() else 0
    store_mb = sum(f.stat().st_size for f in STORE.glob("*")) / 1048576 if store_n else 0
    if not quiet:
        if n == 0:
            print("  no stripped document(s) — THIS GATE IS CHECKING NOTHING")
        else:
            print(f"  {n} stripped document(s) all rebuild byte-identically; "
                  f"store holds {store_n} image(s), {store_mb:.1f} MB")
    print(f"\nodt_media: {'OK' if bad == 0 else 'FAIL'}")
    return 1 if bad else 0


def _family_members(root: Path, pattern: str) -> list[Path]:
    rx = re.compile(pattern)
    hits = []
    for p in sorted(root.iterdir()) if root.is_dir() else []:
        m = rx.match(p.name)
        if m:
            key = tuple(int(g) for g in m.groups() if g not in (None, ""))
            hits.append((key, p))
    hits.sort()
    return [p for _, p in hits]


def _newest() -> list[Path]:
    """The current version of each family. Never stripped."""
    out = []
    for rel, pattern in FAMILIES:
        members = _family_members(REPO / rel, pattern)
        if members:
            out.append(members[-1])
    return out


def superseded() -> list[Path]:
    """Every version of a family EXCEPT its newest. The newest is never touched."""
    out = []
    for rel, pattern in FAMILIES:
        members = _family_members(REPO / rel, pattern)
        out.extend(members[:-1])
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", nargs="?", default="verify",
                    choices=["verify", "strip", "rehydrate", "plan"])
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--all-superseded", action="store_true",
                    help="strip/rehydrate every superseded version of every family")
    a = ap.parse_args(argv)

    if a.selftest:
        return _selftest()

    if a.action == "verify":
        return verify()

    if a.action == "plan":
        rows = superseded()
        img = free = 0
        for p in rows:
            if is_stripped(p):
                continue
            n, b = strip(p, dry_run=True)
            img += n
            free += b
        print(f"  {len(rows)} superseded version(s); {img} embedded image(s), "
              f"{free/1048576:.0f} MB would move to the store")
        return 0

    targets = [Path(x) for x in a.paths] or (superseded() if a.all_superseded else [])
    if not targets:
        print("  nothing named. Pass paths, or --all-superseded.")
        return 2

    if a.action == "strip":
        tot_i = tot_b = 0
        for p in targets:
            if is_stripped(p):
                continue
            i, b = strip(p)
            if i:
                print(f"  stripped {p.name}  {i} image(s), {b/1048576:.1f} MB")
            tot_i += i
            tot_b += b
        print(f"\n  {tot_i} image(s) externalised, {tot_b/1048576:.0f} MB")
        return verify(quiet=True)

    ok = all(rehydrate(p) for p in targets)
    return 0 if ok else 1


def _selftest() -> int:
    """A checker that cannot fail proves nothing. Round trip, then corrupt the
    store and assert the gate notices."""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    try:
        src = tmp / "t.odt"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            zi = zipfile.ZipInfo("mimetype", (2026, 9, 9, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_STORED
            z.writestr(zi, b"application/vnd.oasis.opendocument.text")
            z.writestr("content.xml", b"<x/>")
            z.writestr(PIC + "a.png", b"IMAGE-A" * 500)
            z.writestr(PIC + "b.png", b"IMAGE-B" * 500)
        src.write_bytes(buf.getvalue())
        original = src.read_bytes()

        global STORE
        real, STORE = STORE, tmp / "store"
        try:
            strip(src)
            assert is_stripped(src), "sidecar not written"
            assert len(src.read_bytes()) < len(original), "not smaller"
            side = json.loads(sidecar_path(src).read_text())
            assert _md5(_rebuild(src.read_bytes(), side)) == _md5(original), "round trip"

            # now break one stored image and assert the rebuild refuses
            victim = next(STORE.glob("*.png"))
            victim.write_bytes(b"CORRUPT")
            failed = False
            try:
                _rebuild(src.read_bytes(), side)
            except SystemExit:
                failed = True
            assert failed, "a corrupted store was NOT detected"
        finally:
            STORE = real
        print("  selftest: OK")
        return 0
    except AssertionError as e:
        print(f"  selftest: FAILED — {e}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
