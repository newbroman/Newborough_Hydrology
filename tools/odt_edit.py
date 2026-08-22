#!/usr/bin/env python3
"""
odt_edit — surgical, counted, verified edits to an ODT/ODM content.xml.

Why this exists, and why it is not odfpy.

  **Never write ODT files through odfpy.** Its contentxml() round-trip silently
  drops namespace declarations and other markup, producing a file odfpy itself
  will reload happily and LibreOffice will not open. Reading and flattening with
  odfpy is fine. Writing is not.

  So the write path is: extract content.xml, edit it AS TEXT, and rezip with the
  entry list, entry order and compression preserved and `mimetype` STORED first.
  Everything below is the safety rail around that.

Every guard here was added because something got past its absence:

  counted substitutions   each (old, new, want) must match exactly `want` times,
                          and the batch total must match `expect`. A rename that
                          hits four places when you predicted three is a bug you
                          want before the archive is written, not after.
  tag-sequence identity   the full sequence of tags before and after must be
                          byte-identical unless allow_tag_change is set. Editing
                          text should not move markup.
  declared styles         when markup DOES change, every text:style-name the new
                          markup uses must already be declared in the document.
  span-delta balance      an edit must add as many </text:span> as <text:span>.
                          NOT absolute counts: LibreOffice writes span-like
                          constructs a naive regex miscounts, and a perfectly
                          well-formed document can read as 811 open against 607
                          close. The BEFORE/AFTER DELTA is the invariant; the
                          baseline is whatever it is.
  em-space                U+2003 must not appear. Asserted with chr(0x2003),
                          never a typed literal, because a typed one is
                          invisible in review and in a diff.
  archive shape           entry list and order preserved, mimetype STORED first,
                          testzip() clean, before anything is copied onto the
                          target.

  The temp archive is written to /tmp, never beside the target. On a bridge
  mount Path.unlink() fails with "Operation not permitted", so a temp written
  next to the document cannot be cleaned up and is left behind.

After any edit, open the result in headless LibreOffice and read the changed
passage back. A file that rezips is not a file that opens.

Usage:
    import sys; sys.path.insert(0, "tools")
    from odt_edit import edit
    edit("Doc_v1_2.odt", "Doc_v1_3.odt",
         [("λ ≈ 225 m", "λ ≈ 230 m", 1)], expect=1)
"""
from __future__ import annotations

__version__ = "1.3.0"  # Hollingham (2026) — 2026-08-22. The declared-style
#   guard checked EVERY style name in the document, so it aborted a sound edit to
#   the public summary over a "Title" style the document already contained and
#   the edit never touched. It now checks only the styles the edit INTRODUCES.
#   The invariant is "no undeclared markup added", not "every style in the file
#   resolves" — the second is a document-validity question and not this
#   function's job.
#
#   edit() also had its OWN COPY of the whole guard block and never called
#   _guards() — the refactor at v1.1.0 added the shared version without removing
#   the original, so the fix above landed in the copy nothing was using. Both are
#   now one function. Two copies of a guard is how a guard comes to disagree with
#   itself.
#
# v1.2.0  # Hollingham (2026) — 2026-08-22. Adds edit_entries(),
#   which reaches the EMBEDDED FORMULA OBJECTS. An ODF equation is not in
#   content.xml: it is an "Object NN/content.xml" part holding a MathML tree and
#   a StarMath annotation of the same expression. report8 carries 82 of them.
#   A symbol rename that edits only the prose renames the sentence naming the
#   symbol and leaves the equation above it unchanged — strictly worse than not
#   renaming at all. The tag-sequence guard cannot apply to a MathML edit, which
#   is a markup change by construction, so the guard there is XML
#   well-formedness plus the counted substitution.
#
# v1.1.0  # Hollingham (2026) — 2026-08-22. Adds edit_spans(),
#   which applies replacements given as content.xml character ranges rather than
#   as literal strings, so a caller that has located occurrences by position —
#   symbol_apply.py, renaming one SENSE of a glyph and leaving the others — can
#   use the same guards. The guards are factored out and shared: both entry
#   points run the identical tag-sequence, style, span-delta and em-space checks.
#
# v1.0.0  # Hollingham (2026) — 2026-08-22. First issue as a
#   committed tool (M22). Previously rebuilt from scratch in /tmp every session,
#   which cost an hour on 2026-08-21 to a bug in the span-balance guard that a
#   tested, committed version would not have carried: it compared ABSOLUTE
#   <text:span> open and close counts across the whole document and aborted a
#   valid edit twice. The guard now compares the before/after delta.

import pathlib
import re
import shutil
import sys
import zipfile

EM_SPACE = chr(0x2003)


def _span_balance(xml: str) -> tuple[int, int]:
    return (len(re.findall(r"<text:span\b", xml)),
            len(re.findall(r"</text:span>", xml)))


def _guards(orig_xml: str, xml: str, zin, name: str,
            allow_tag_change: bool) -> bool:
    """Every structural check, shared by both entry points."""
    before_tags = re.findall(r"<[^>]+>", orig_xml)
    after_tags = re.findall(r"<[^>]+>", xml)
    if before_tags != after_tags:
        if not allow_tag_change:
            print(f"  ABORT {name}: tag sequence changed")
            return False
        # Only styles this EDIT introduced. Checking every style in the
        # document flags whatever the document already contained — a Title
        # style declared some other way, an inherited name — and aborts a
        # sound edit for a condition that predates it. The invariant is "no
        # undeclared markup ADDED", not "every style in the file resolves".
        styles = zin.read("styles.xml").decode("utf-8") + xml
        used_before = set(re.findall(r'text:style-name="([^"]+)"', "".join(before_tags)))
        used_after = set(re.findall(r'text:style-name="([^"]+)"', "".join(after_tags)))
        undeclared = [u for u in (used_after - used_before)
                      if f'style:name="{u}"' not in styles]
        if undeclared:
            print(f"  ABORT {name}: edit introduces undeclared style(s) {undeclared}")
            return False
        b_open, b_close = _span_balance(orig_xml)
        a_open, a_close = _span_balance(xml)
        d_open, d_close = a_open - b_open, a_close - b_close
        if d_open != d_close:
            print(f"  ABORT {name}: edit unbalances spans "
                  f"({d_open:+d} open, {d_close:+d} close)")
            return False
        print(f"  note: tag sequence changed by {len(after_tags) - len(before_tags)} "
              f"tag(s); all styles declared; span delta balanced "
              f"({d_open:+d}/{d_close:+d}) against a baseline of {b_open}/{b_close}")
    if EM_SPACE in xml:
        print(f"  ABORT {name}: em-space (U+2003) present")
        return False
    return True


def _write(src, dst, xml: str, zin, names) -> bool:
    data = xml.encode("utf-8")
    tmp = pathlib.Path("/tmp") / (dst.name + ".ziptmp")
    with zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            payload = data if info.filename == "content.xml" else zin.read(info.filename)
            ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            ni.external_attr = info.external_attr
            ni.compress_type = (zipfile.ZIP_STORED if info.filename == "mimetype"
                                else zipfile.ZIP_DEFLATED)
            zout.writestr(ni, payload)
    zo = zipfile.ZipFile(tmp)
    ok = (zo.namelist() == names
          and zo.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
          and zo.testzip() is None)
    zo.close()
    if not ok:
        print(f"  ABORT {src.name}: archive verification failed")
        tmp.unlink()
        return False
    with open(tmp, "rb") as a, open(dst, "wb") as b:
        shutil.copyfileobj(a, b)
    tmp.unlink()
    print(f"  OK  {dst.name}  ({dst.stat().st_size} bytes, {len(names)} entries)")
    return True


def edit_spans(src, dst, spans, expect: int) -> bool:
    """Replace content.xml character ranges. spans = [(start, end, new_text)].

    For callers that located occurrences by POSITION rather than by literal
    string — renaming one sense of a glyph while leaving the glyph's other
    senses alone, where the same three characters must change in one place and
    not in the next. Ranges must not overlap; they are applied last-first so
    earlier offsets stay valid.
    """
    src, dst = pathlib.Path(src), pathlib.Path(dst)
    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    if names[0] != "mimetype":
        print(f"  ABORT {src.name}: mimetype is not the first archive entry")
        zin.close(); return False
    xml = orig_xml = zin.read("content.xml").decode("utf-8")
    spans = sorted(spans, key=lambda t: t[0])
    for (a1, b1, _), (a2, _, _) in zip(spans, spans[1:]):
        if b1 > a2:
            print(f"  ABORT {src.name}: overlapping spans at {a1}, {a2}")
            zin.close(); return False
    if len(spans) != expect:
        print(f"  ABORT {src.name}: {len(spans)} span(s), expected {expect}")
        zin.close(); return False
    for start, end, new in reversed(spans):
        xml = xml[:start] + new + xml[end:]
    print(f"  {len(spans)}x  span replacement(s) in {src.name}")
    if not _guards(orig_xml, xml, zin, src.name, allow_tag_change=False):
        zin.close(); return False
    ok = _write(src, dst, xml, zin, names)
    zin.close()
    return ok


def edit(src, dst, subs, expect, allow_tag_change: bool = False) -> bool:
    """Apply counted substitutions to `src`'s content.xml, writing `dst`.

    subs     [(old, new, want), ...] — literal strings, `want` occurrences each
    expect   total substitutions across the batch, as a second check on subs
    allow_tag_change  permit the tag sequence to change (adding a span, say).
                      The style and span-delta guards then apply instead.

    Returns True on success. On any failed guard, prints why and returns False
    WITHOUT touching `dst`.
    """
    src, dst = pathlib.Path(src), pathlib.Path(dst)
    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    if names[0] != "mimetype":
        print(f"  ABORT {src.name}: mimetype is not the first archive entry")
        zin.close()
        return False
    xml = zin.read("content.xml").decode("utf-8")
    orig_xml = xml

    total = 0
    for old, new, want in subs:
        n = xml.count(old)
        if n != want:
            print(f"  ABORT {src.name}: {old[:60]!r} found {n}x, expected {want}x")
            zin.close()
            return False
        xml = xml.replace(old, new)
        total += n
        print(f"  {n}x  {old[:56]!r} -> {new[:56]!r}")
    if total != expect:
        print(f"  ABORT {src.name}: {total} substitutions, expected {expect}")
        zin.close()
        return False

    if not _guards(orig_xml, xml, zin, src.name, allow_tag_change):
        zin.close()
        return False
    ok = _write(src, dst, xml, zin, names)
    zin.close()
    return ok


def read_text(src) -> str:
    """content.xml with tags stripped — for locating a passage, never for writing."""
    xml = zipfile.ZipFile(src).read("content.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", "", xml)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(read_text(sys.argv[1])[:4000])


def edit_entries(src, dst, entry_subs: dict, expect: int) -> bool:
    """Counted substitutions inside NON-content.xml archive entries.

    entry_subs = {"Object 46/content.xml": [(old, new, want), ...], ...}

    For embedded formula objects. Each edited part must still parse as XML —
    the tag-sequence guard is meaningless here because changing <mi>D</mi> to
    <msub><mi>z</mi><mn>0</mn></msub> is precisely a markup change — and the
    substitution counts do the rest of the work.

    An ODF equation stores the expression TWICE: once as MathML, which is what
    renders, and once as a StarMath annotation, which is what you get back when
    you double-click it. Change one and not the other and the formula silently
    reverts the next time anyone edits it. Pass both substitutions for each part.
    """
    import xml.etree.ElementTree as ET
    src, dst = pathlib.Path(src), pathlib.Path(dst)
    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    if names[0] != "mimetype":
        print(f"  ABORT {src.name}: mimetype is not the first archive entry")
        zin.close(); return False
    missing = [k for k in entry_subs if k not in names]
    if missing:
        print(f"  ABORT {src.name}: no such entry {missing}")
        zin.close(); return False

    edited, total = {}, 0
    for entry, subs in entry_subs.items():
        text = zin.read(entry).decode("utf-8")
        for old, new, want in subs:
            n = text.count(old)
            if n != want:
                print(f"  ABORT {src.name} [{entry}]: {old[:44]!r} found {n}x, "
                      f"expected {want}x")
                zin.close(); return False
            text = text.replace(old, new)
            total += n
        try:
            ET.fromstring(text)
        except ET.ParseError as exc:
            print(f"  ABORT {src.name} [{entry}]: not well-formed after edit — {exc}")
            zin.close(); return False
        if EM_SPACE in text:
            print(f"  ABORT {src.name} [{entry}]: em-space (U+2003) present")
            zin.close(); return False
        edited[entry] = text.encode("utf-8")
        print(f"  {sum(w for _, _, w in subs)}x  {entry}")
    if total != expect:
        print(f"  ABORT {src.name}: {total} substitutions, expected {expect}")
        zin.close(); return False

    tmp = pathlib.Path("/tmp") / (dst.name + ".ziptmp")
    with zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            payload = edited.get(info.filename) or zin.read(info.filename)
            ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            ni.external_attr = info.external_attr
            ni.compress_type = (zipfile.ZIP_STORED if info.filename == "mimetype"
                                else zipfile.ZIP_DEFLATED)
            zout.writestr(ni, payload)
    zin.close()
    zo = zipfile.ZipFile(tmp)
    ok = (zo.namelist() == names
          and zo.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
          and zo.testzip() is None)
    zo.close()
    if not ok:
        print(f"  ABORT {src.name}: archive verification failed")
        tmp.unlink(); return False
    with open(tmp, "rb") as a, open(dst, "wb") as b:
        shutil.copyfileobj(a, b)
    tmp.unlink()
    print(f"  OK  {dst.name}  ({dst.stat().st_size} bytes, {len(names)} entries)")
    return True
