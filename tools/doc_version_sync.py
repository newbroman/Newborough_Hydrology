#!/usr/bin/env python3
"""
====================================================================================
doc_version_sync.py — hold a document's in-text version string on its filename
====================================================================================

Purpose:
    Versioned documents are never edited in place: an edit batch saves to a
    bumped filename (Newborough_Methods_Supplement_v1_9_23.odt -> _v1_9_24.odt)
    and the newest file is the live one. The Methods Supplement also states its
    own version in its front matter, and nothing has ever maintained that line.
    On 2026-08-19 it read "Document version: 1.9.7 (August 2026)" against a
    filename of _v1_9_24 — seventeen bumps behind. Sessions had noticed it
    repeatedly and left it, which is the signature of a job that has to be
    mechanical rather than remembered.

    This tool derives the version from the filename and writes it into the
    document; --check makes the disagreement a gate failure (tools/check_all.sh).

Mapping (filename -> text):
    The version suffix is a run of underscore-separated integers after "_v".
    Those integers, joined with dots, ARE the in-text version:

        Newborough_Methods_Supplement_v1_9_24.odt  ->  1.9.24
        Supplementary_Material_v1_14.odt           ->  1.14

    The component count is whatever the filename carries — no padding, no fixed
    depth. The live file is the highest version by natural sort, resolved with
    refresh_mirrors._version_key and refresh_mirrors.SOURCES, so that this tool
    and the mirror refresh can never disagree about which file is live or about
    which documents are versioned. Add a document there, not here.

The date in the parenthesis:
    The line is "Document version: 1.9.24 (August 2026)". The month and year are
    refreshed from the live file's mtime ONLY when the version number itself
    changes, and --check never looks at them. mtime is not preserved by a clone
    or a copy, so a gate on it would fail differently on Martin's machine and on
    John's and would demand a rewrite of a document that is correct; the version
    number comes from the filename and is the same everywhere. --refresh-date
    forces the date for a document already in sync, for when the month is simply
    wrong. Month names come from a table, not strftime, whose %B follows the
    machine locale.

How the string is stored (checked 2026-08-19, v1_9_24):
    In content.xml, as one unsplit run:

        <text:p text:style-name="Text_20_body">Document version: 1.9.7
        (August 2026).</text:p>

    Once, in content.xml only — not in styles.xml (headers and footers), not in
    settings.xml, and not in meta.xml, which carries no version field at all
    (dc:title and the meta:user-defined set are empty), so there is nothing
    there to sync. If a future edit splits the number across inline markup —
    1.9.<text:span …>24</text:span> renders as "1.9.24" and would defeat the
    pattern — the label is still found, the document is reported MANUAL, and
    nothing is written.

Writing:
    Never through odfpy, whose contentxml() round-trip drops namespace
    declarations and yields a file LibreOffice will not open. content.xml is
    replaced as bytes and the archive is rebuilt entry by entry in the original
    order, preserving each entry's compression, attributes and timestamps, with
    mimetype first and STORED. The rebuilt archive is verified BEFORE it
    replaces the original — entry names and order identical, mimetype first and
    uncompressed, testzip() clean, content.xml parses, and the version line read
    back out of the new file — and only then moved into place.

    The file's mode is preserved; its mtime is NOT — it becomes now, which is
    what makes tools/refresh_mirrors.py --check report the mirror stale, as it
    should be once the ODT has changed.

    A version-string sync is bookkeeping, not an edit batch: the tool edits the
    live file in place and never bumps the filename.

Usage:
    python3 tools/doc_version_sync.py                  # sync every document
    python3 tools/doc_version_sync.py --check          # report only, 1 on drift
    python3 tools/doc_version_sync.py --check --quiet  # the gate form
    python3 tools/doc_version_sync.py --only Methods
    python3 tools/doc_version_sync.py --refresh-date

Exit codes:
    0  in sync, or the sync was applied and verified
    1  --check found drift; or a REQUIRED document has lost its version line;
       or a line needs a human (split by markup)
    2  a real failure: a document that will not open, or a rebuilt archive that
       failed verification — in which case nothing was written
====================================================================================
"""
from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-19
# 1.0.0 — first version. The Methods Supplement's front matter had said 1.9.7
#         since the file was named _v1_9_7; the filename had reached _v1_9_24.
#         Nothing owned the line, so every session that spotted it left it.
#         Registered documents, and which file of a versioned set is live, are
#         imported from refresh_mirrors rather than restated here: a second copy
#         of that list is the same drift one directory along.

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from refresh_mirrors import SOURCES, _stem_without_version, _version_key  # noqa: E402

# Documents that MUST carry a version line. For anything else a missing line is
# "this document does not state its version", which is not drift; the day one
# gains a line it starts being checked automatically.
REQUIRED = {"Newborough_Methods_Supplement"}

MIMETYPE = "mimetype"
CONTENT = "content.xml"

# strftime("%B") follows the machine locale; these documents are English.
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")

# U+2003 must never reach a document. Built from the code point: a typed literal
# degrades to a normal space on the way through an editor and passes silently.
EM_SPACE = chr(0x2003).encode("utf-8")

# "Document version: 1.9.7 (August 2026)". \s in a bytes pattern is ASCII-only,
# so a non-breaking space is spelled out.
_SP = rb"(?:\s|\xc2\xa0)*"
_LABEL_RE = re.compile(rb"Document version:")
_LINE_RE = re.compile(
    rb"(Document version:" + _SP + rb")"      # 1: label
    rb"(\d+(?:\.\d+)*)"                       # 2: version number
    rb"(" + _SP + rb"\()"                     # 3: opening bracket
    rb"([^)<>]*)"                             # 4: month and year
    rb"(\))"                                  # 5: closing bracket
)


class VerificationError(RuntimeError):
    """A rebuilt archive failed its read-back; the original was left alone."""


def documents() -> list[Path]:
    """The live file of every versioned document registered in refresh_mirrors."""
    live: list[Path] = []
    for pattern, _mirror_dir, versioned in SOURCES:
        if not versioned:
            continue
        matches = [p for p in sorted(_ROOT.glob(pattern)) if _version_key(p) != [-1]]
        if matches:
            live.append(max(matches, key=_version_key))
    return live


def filename_version(path: Path) -> str:
    """1.9.24 from Newborough_Methods_Supplement_v1_9_24.odt."""
    return ".".join(str(n) for n in _version_key(path))


def month_year(path: Path) -> str:
    when = datetime.fromtimestamp(path.stat().st_mtime)
    return f"{MONTHS[when.month - 1]} {when.year}"


def read_content(path: Path) -> bytes:
    with zipfile.ZipFile(path) as zf:
        return zf.read(CONTENT)


def _verify(tmp: Path, names: list[str], expected: str) -> None:
    """Read the rebuilt archive back. Raise on anything that is not identical."""
    with zipfile.ZipFile(tmp) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise VerificationError(f"corrupt entry {bad}")
        infos = zf.infolist()
        if [i.filename for i in infos] != names:
            raise VerificationError("entry names or order changed")
        if infos[0].filename != MIMETYPE:
            raise VerificationError("mimetype is not the first entry")
        if infos[0].compress_type != zipfile.ZIP_STORED:
            raise VerificationError("mimetype is not stored uncompressed")
        content = zf.read(CONTENT)
    try:
        ET.fromstring(content)
    except ET.ParseError as exc:
        raise VerificationError(f"content.xml will not parse ({exc})") from exc
    found = {m.group(2).decode("utf8") for m in _LINE_RE.finditer(content)}
    if found != {expected}:
        raise VerificationError(f"version line reads {found or 'nothing'}, "
                                f"expected {expected}")


def rebuild(path: Path, content: bytes, expected: str) -> None:
    """Replace content.xml in `path`, mimetype first and stored, verified first."""
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(path) as zin:
        infos = zin.infolist()
        payloads = [(i, zin.read(i.filename)) for i in infos]
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, payload in payloads:
            entry = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            entry.compress_type = (zipfile.ZIP_STORED if info.filename == MIMETYPE
                                   else info.compress_type)
            entry.external_attr = info.external_attr
            entry.internal_attr = info.internal_attr
            entry.create_system = info.create_system
            zout.writestr(entry, content if info.filename == CONTENT else payload)
    try:
        _verify(tmp, [i.filename for i in infos], expected)
    except VerificationError:
        tmp.unlink(missing_ok=True)
        raise
    os.chmod(tmp, stat.S_IMODE(path.stat().st_mode))
    tmp.replace(path)


def process(path: Path, apply: bool, refresh_date: bool) -> tuple[str, str]:
    """Return (status, message) for one document. Nothing is written unless
    `apply`. Status is one of OK, SYNCED, DRIFT, ABSENT, MANUAL."""
    wanted = filename_version(path)
    try:
        content = read_content(path)
    except (zipfile.BadZipFile, KeyError, OSError) as exc:
        raise VerificationError(f"cannot read {path.name}: {exc}") from exc

    labels = len(_LABEL_RE.findall(content))
    matches = _LINE_RE.findall(content)
    if labels == 0:
        return "ABSENT", 'no "Document version:" line'
    if len(matches) != labels:
        return "MANUAL", (f'{labels} "Document version:" label(s), '
                          f"{len(matches)} in the recognised form — the rest are "
                          "split by inline markup or worded differently; "
                          "nothing written")

    present = sorted({m[1].decode("utf8") for m in matches})
    changed = present != [wanted]
    if not changed and not refresh_date:
        where = "" if labels == 1 else f" ({labels} occurrences)"
        return "OK", f"{wanted}{where}"

    date = month_year(path)
    keep_date = not changed

    def _swap(m: re.Match) -> bytes:
        return (m.group(1) + wanted.encode("utf8") + m.group(3)
                + (m.group(4) if keep_date else date.encode("utf8"))
                + m.group(5))

    updated = _LINE_RE.sub(_swap, content)
    if updated == content:
        # --refresh-date on a document whose date is already right.
        return "OK", f"{wanted} ({date})"
    if EM_SPACE in updated:
        raise VerificationError("rewritten content.xml contains U+2003")

    shown = ", ".join(present)
    detail = (f"{shown} -> {wanted}" if changed else f"{wanted}, date -> {date}")
    if not apply:
        return "DRIFT", detail
    rebuild(path, updated, wanted)
    return "SYNCED", detail


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Sync a document's in-text version string to its filename.")
    ap.add_argument("--check", action="store_true",
                    help="report drift and exit non-zero; write nothing")
    ap.add_argument("--quiet", action="store_true",
                    help="print only the documents that need attention")
    ap.add_argument("--only", default=None,
                    help="substring filter on the document filename")
    ap.add_argument("--refresh-date", action="store_true",
                    help="also refresh the (Month Year) part of a document "
                         "whose version number is already correct")
    args = ap.parse_args()

    if args.check and args.refresh_date:
        print("  note: --refresh-date does nothing under --check; the date is "
              "never gated.")

    paths = documents()
    if args.only:
        paths = [p for p in paths if args.only in p.name]
    if not paths:
        print("No versioned documents matched.")
        return 1

    drift = required_missing = manual = synced = 0
    for path in paths:
        try:
            status, message = process(path, apply=not args.check,
                                      refresh_date=args.refresh_date)
        except VerificationError as exc:
            print(f"  ERROR   {path.name}\n            {exc}")
            return 2

        if status == "ABSENT" and _stem_without_version(path) in REQUIRED:
            status = "MISSING"
            message = ('this document is required to carry a version line and '
                       'no longer does — restore "Document version: '
                       f'{filename_version(path)} (Month Year)."')
            required_missing += 1
        elif status == "DRIFT":
            drift += 1
        elif status == "MANUAL":
            manual += 1
        elif status == "SYNCED":
            synced += 1

        if args.quiet and status in {"OK", "ABSENT"}:
            continue
        print(f"  {status:<7} {path.name}\n            {message}")

    total = len(paths)
    if drift:
        print(f"\n{drift} document(s) out of step with their filename — run "
              "python3 tools/doc_version_sync.py")
    if required_missing or manual:
        print(f"\n{required_missing + manual} document(s) need a human.")
    if not (drift or required_missing or manual):
        print(f"\n{total} versioned document(s) checked, all in step.")
    if synced:
        print("The mirror of every document written above is now behind it — "
              "run python3 tools/refresh_mirrors.py")

    return 1 if (drift or required_missing or manual) else 0


if __name__ == "__main__":
    sys.exit(main())
