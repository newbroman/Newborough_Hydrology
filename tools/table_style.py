#!/usr/bin/env python3
"""table_style.py -- restyle ODT tables to a classic black/greyscale (booktabs) style.

Rewrites ONLY the border + background attributes of automatic ``table-cell``
styles in an ODT's content.xml. It never touches cell text, table structure,
rows, columns, column widths, paragraph styles, or any non table-cell style.

Target style (per data table):
  * No vertical rules anywhere (border-left/right = none on every cell).
  * Header row (first row): bg #ededed, border-top 1pt solid #000000 (top rule),
    border-bottom 0.5pt solid #000000 (header/mid rule).
  * Last data row: border-bottom 1pt solid #000000 (bottom rule), no bg.
  * A whole-row shaded TOTALS/SUMMARY last row -> bg #e8e8e8, border-top
    0.5pt solid #000000 (rule above summary) + bottom rule; box removed.
  * All other body cells: no background, no borders.
  * Any #00599d rule colour -> #000000.
  * fo:padding and style:vertical-align are preserved untouched.

Row roles are derived from the parsed table geometry (rowspan-aware), not from
style names. The rewrite is idempotent: re-running yields identical output.

The zip is updated in place, replacing ONLY content.xml. Image entries are left
byte-for-byte identical (via the ``zip`` CLI single-entry update, or a pure
Python raw-bytes copy fallback).
"""
import argparse
import io
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

HEADER_BG = "#ededed"
SUMMARY_BG = "#e8e8e8"
BLACK = "#000000"
TOP_RULE = "1pt solid " + BLACK
MID_RULE = "0.5pt solid " + BLACK
BOTTOM_RULE = "1pt solid " + BLACK
SUMMARY_TOP_RULE = "0.5pt solid " + BLACK

# --- regexes -------------------------------------------------------------
# Matches a table-cell automatic style and the attribute list of its
# <style:table-cell-properties> child. The <style:style> open tag may carry
# extra attributes (style:display-name, style:data-style-name, ...) in any
# order, so name/family are located anywhere within it.
STYLE_RE = re.compile(
    r'(?P<head><style:style\b[^>]*\bstyle:family="table-cell"[^>]*>'
    r'\s*<style:table-cell-properties)(?P<attrs>[^>]*?)(?P<close>/>|>)')
NAME_RE = re.compile(r'\bstyle:name="([^"]*)"')
TABLE_RE = re.compile(r'<table:table\b([^>]*)>(.*?)</table:table>', re.S)
ROW_RE = re.compile(r'<table:table-row\b[^>]*>(.*?)</table:table-row>', re.S)
# real cells only (not covered-table-cell)
CELL_RE = re.compile(r'<table:table-cell\b([^>]*?)/?>')
COVERED_RE = re.compile(r'<table:covered-table-cell\b')
MANAGED = ['fo:border', 'fo:border-left', 'fo:border-right',
           'fo:border-top', 'fo:border-bottom', 'fo:background-color']


def _attr(s, name):
    m = re.search(name + r'="([^"]*)"', s)
    return m.group(1) if m else None


def _bg_of(attrs):
    return _attr(attrs, 'fo:background-color')


def build_style_map(xml):
    """name -> table-cell-properties attribute string."""
    out = {}
    for m in STYLE_RE.finditer(xml):
        nm = NAME_RE.search(m.group('head'))
        if nm:
            out[nm.group(1)] = m.group('attrs')
    return out


def _row_real_cells(row_inner):
    """Yield (style_name, rowspan) for each real (non-covered) cell in row order.

    Covered cells still occupy a grid column, but they carry no styling of
    their own, so they are skipped for role assignment.
    """
    out = []
    for m in CELL_RE.finditer(row_inner):
        a = m.group(1)
        sn = _attr(a, 'table:style-name')
        span = _attr(a, 'table:number-rows-spanned')
        out.append((sn, int(span) if span else 1))
    return out


def classify(xml, styles):
    """Return (roles, notes, table_info).

    roles: style_name -> one of
        'header', 'last', 'summary', 'body'
      (styles not present -> untouched / skipped).
    notes: list of human-readable per-table notes.
    """
    roles = {}
    notes = []
    tinfo = []

    for tm in TABLE_RE.finditer(xml):
        thead, body = tm.group(1), tm.group(2)
        name = _attr(thead, 'table:name')
        rows = ROW_RE.findall(body)
        if not rows:
            continue
        last_idx = len(rows) - 1

        # header row real cells
        hdr_cells = _row_real_cells(rows[0])
        hdr_bgs = [_bg_of(styles.get(sn, '')) for sn, _ in hdr_cells if sn]
        is_data = bool(hdr_bgs) and all(
            (b and b.lower() != 'transparent') for b in hdr_bgs)

        if not is_data:
            notes.append(
                f"{name}: non-data / layout table (header row unshaded or "
                f"transparent) -> left untouched; it carries no borders or "
                f"vertical rules to strip.")
            tinfo.append((name, 'layout', len(rows)))
            continue

        # gather per-style role votes across the whole table (rowspan-aware)
        votes = {}  # style_name -> set of {'header','lastedge','body'}
        start_bg_last = []  # bgs of real cells that START on the last row
        for ri, row in enumerate(rows):
            for sn, span in _row_real_cells(row):
                if not sn:
                    continue
                end = ri + span - 1
                v = votes.setdefault(sn, set())
                if ri == 0:
                    v.add('header')
                if end == last_idx:
                    v.add('lastedge')
                if ri != 0 and end != last_idx:
                    v.add('body')
                if ri == last_idx:
                    start_bg_last.append(_bg_of(styles.get(sn, '')))

        # does any last-edge style ALSO serve as a plain body cell? (block reuse)
        ambiguous_last = any(
            ('lastedge' in v and 'body' in v) for v in votes.values())
        # summary row: clean last row, every cell starting there is shaded
        summary = (not ambiguous_last) and bool(start_bg_last) and all(
            b for b in start_bg_last)

        for sn, v in votes.items():
            if 'header' in v:
                roles[sn] = 'header'
            elif v == {'lastedge'}:
                roles[sn] = 'summary' if summary else 'last'
            else:
                # includes ambiguous ('lastedge'&'body') -> treat as body (safe)
                roles[sn] = 'body'

        if ambiguous_last:
            notes.append(
                f"{name}: last data row reuses a block style shared with "
                f"interior rows (e.g. multi-row shaded block); applied header "
                f"top/mid rules, stripped verticals and removed body shading, "
                f"but NO distinct bottom rule (it would draw interior rules). "
                f"Header identified as row 1; body block shading removed.")
            tinfo.append((name, 'data(safe-subset,no-bottom-rule)', len(rows)))
        elif summary:
            notes.append(
                f"{name}: header = row 1; last row is a whole-row shaded "
                f"TOTALS/SUMMARY row -> converted to grey {SUMMARY_BG} with a "
                f"top rule + bottom rule (box/verticals removed).")
            tinfo.append((name, 'data(summary-last)', len(rows)))
        else:
            notes.append(
                f"{name}: header = row 1 (top+mid rule, grey), last row = "
                f"row {len(rows)} (bottom rule); verticals stripped, interior "
                f"borders/shading removed.")
            tinfo.append((name, 'data', len(rows)))

    return roles, notes, tinfo


def _spec_for(role):
    if role == 'header':
        return dict(bg=HEADER_BG, l='none', r='none', t=TOP_RULE, b=MID_RULE)
    if role == 'last':
        return dict(bg=None, l='none', r='none', t='none', b=BOTTOM_RULE)
    if role == 'summary':
        return dict(bg=SUMMARY_BG, l='none', r='none',
                    t=SUMMARY_TOP_RULE, b=BOTTOM_RULE)
    # body
    return dict(bg=None, l='none', r='none', t='none', b='none')


def _rewrite_attrs(attrs, spec):
    # strip managed attributes, keep everything else in original order
    for a in MANAGED:
        attrs = re.sub(r'\s+' + re.escape(a) + r'="[^"]*"', '', attrs)
    attrs = attrs.rstrip()
    adds = []
    if spec.get('bg'):
        adds.append(f'fo:background-color="{spec["bg"]}"')
    adds.append(f'fo:border-left="{spec["l"]}"')
    adds.append(f'fo:border-right="{spec["r"]}"')
    adds.append(f'fo:border-top="{spec["t"]}"')
    adds.append(f'fo:border-bottom="{spec["b"]}"')
    return attrs + ' ' + ' '.join(adds)


def transform(xml):
    styles = build_style_map(xml)
    roles, notes, tinfo = classify(xml, styles)

    def repl(m):
        nm = NAME_RE.search(m.group('head'))
        name = nm.group(1) if nm else None
        role = roles.get(name)
        if role is None:
            # style not part of any classified data table -> leave as-is,
            # but still neutralise any #00599d rule colour it might carry.
            attrs = m.group('attrs')
            if '#00599d' in attrs:
                attrs = attrs.replace('#00599d', BLACK)
            return m.group('head') + attrs + m.group('close')
        new_attrs = _rewrite_attrs(m.group('attrs'), _spec_for(role))
        return m.group('head') + new_attrs + m.group('close')

    new_xml = STYLE_RE.sub(repl, xml)
    return new_xml, roles, notes, tinfo


# --- zip I/O (image-safe) ------------------------------------------------
def read_content(odt):
    with zipfile.ZipFile(odt) as z:
        return z.read('content.xml').decode('utf-8')


def _write_via_zip_cli(odt, content_bytes):
    tmp = tempfile.mkdtemp(prefix='tblstyle_')
    try:
        with open(os.path.join(tmp, 'content.xml'), 'wb') as f:
            f.write(content_bytes)
        r = subprocess.run(['zip', '-X', '-q', os.path.abspath(odt),
                            'content.xml'], cwd=tmp,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            raise RuntimeError('zip CLI failed: ' + r.stdout.decode('utf-8', 'replace'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _write_via_python(odt, content_bytes):
    """Pure-Python fallback used only when the ``zip`` CLI is absent.

    Copies every entry's RAW (already-compressed) bytes verbatim into a fresh
    archive, substituting only content.xml. Image members are never
    decompressed or recompressed, so their bytes are preserved exactly.
    """
    src = odt + '.tmp_in'
    shutil.move(odt, src)
    try:
        with open(src, 'rb') as fin, zipfile.ZipFile(src) as zin, \
                open(odt, 'wb') as fout:
            zout = zipfile.ZipFile(fout, 'w')
            for zi in zin.infolist():
                if zi.filename == 'content.xml':
                    ni = zipfile.ZipInfo('content.xml', date_time=zi.date_time)
                    ni.compress_type = zipfile.ZIP_DEFLATED
                    ni.external_attr = zi.external_attr
                    zout.writestr(ni, content_bytes)
                    continue
                # locate and copy the raw compressed member bytes
                fin.seek(zi.header_offset)
                hdr = fin.read(30)
                nlen, elen = struct.unpack('<HH', hdr[26:30])
                fin.read(nlen + elen)
                raw = fin.read(zi.compress_size)
                ni = zipfile.ZipInfo(zi.filename, date_time=zi.date_time)
                ni.compress_type = zi.compress_type
                ni.external_attr = zi.external_attr
                ni.flag_bits = zi.flag_bits & ~0x08  # no data descriptor
                ni.CRC = zi.CRC
                ni.compress_size = zi.compress_size
                ni.file_size = zi.file_size
                ni.header_offset = zout.fp.tell()
                zout.fp.write(ni.FileHeader(zip64=False))
                zout.fp.write(raw)
                zout.filelist.append(ni)
                zout.NameToInfo[ni.filename] = ni
            zout.close()
    finally:
        if os.path.exists(src):
            os.remove(src)


def write_content(odt, content_str):
    data = content_str.encode('utf-8')
    if shutil.which('zip'):
        _write_via_zip_cli(odt, data)
    else:
        _write_via_python(odt, data)


# --- signatures / reporting ---------------------------------------------
def signatures(xml):
    styles = build_style_map(xml)
    roles, _, _ = classify(xml, styles)
    sig = {}
    styles2 = build_style_map(xml)
    for name, role in roles.items():
        attrs = styles2.get(name, '')
        canon = tuple(sorted(re.findall(r'(fo:border[a-z-]*|fo:background-color)="([^"]*)"', attrs)))
        sig.setdefault(role, {})
        sig[role][canon] = sig[role].get(canon, 0) + 1
    return sig


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('odt', nargs='?',
                    default='report_edits/odt/report9.odt')
    ap.add_argument('--dry-run', action='store_true',
                    help='classify + print report, do not write')
    args = ap.parse_args()

    xml = read_content(args.odt)
    new_xml, roles, notes, tinfo = transform(xml)

    print(f"== table_style: {args.odt} ==")
    print(f"table-cell styles total: {len(build_style_map(xml))}; "
          f"rewritten: {len(roles)}")
    from collections import Counter
    rc = Counter(roles.values())
    print(f"roles: {dict(rc)}")
    print("\n-- per-table notes --")
    for n in notes:
        print("  " + n)

    if '#00599d' in new_xml:
        # ensure no residual #00599d inside any table-cell-properties
        import re as _re
        residual = _re.findall(r'<style:table-cell-properties[^>]*#00599d', new_xml)
        if residual:
            print(f"WARNING: {len(residual)} table-cell props still carry #00599d")

    if args.dry_run:
        print("\n(dry-run: not written)")
        return

    write_content(args.odt, new_xml)
    # verify round-trip parses and reflects roles
    back = read_content(args.odt)
    sig = signatures(back)
    print("\n-- resulting distinct cell-style signatures by role --")
    for role in ('header', 'last', 'summary', 'body'):
        if role in sig:
            print(f"  [{role}]")
            for canon, cnt in sig[role].items():
                print(f"     x{cnt}: {dict(canon)}")
    print("\nDONE.")


if __name__ == '__main__':
    main()
