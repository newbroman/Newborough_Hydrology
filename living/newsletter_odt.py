"""
newsletter_odt.py — write the Water Watch newsletter as an editable ODT.

The PDF builder in newborough_report.py assembles a reportlab "story" (a list of
Paragraph / Image / Table / Spacer / PageBreak flowables). This module turns that
same story into a Flat ODT (.fodt) and has LibreOffice convert it to .odt, so the
ODT and the PDF carry identical text, figures and tables from one source.

Layout rule the PDF lacked: a heading is never left at the foot of a page with
its figure on the next. Headings carry keep-with-next, and so does any paragraph
that sits between a heading and its figure; the figure paragraph keeps with its
caption.

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-07. New (Martin: "can you make
#   the report an odt"; the heading/figure page splits he reported).
"""
__version__ = "1.0.0"

import base64
import html
import os
import re
import shutil
import subprocess
import tempfile

PT_PER_CM = 72.0 / 2.54

_STYLE_MAP = {           # reportlab ParagraphStyle name -> ODT paragraph style
    "ReportTitle": "WWTitle",
    "ReportH2": "WWH2",
    "ReportH3": "WWH3",
    "ReportBody": "WWBody",
    "Caption": "WWCaption",
    "Warning": "WWWarning",
}
_HEADINGS = {"WWTitle", "WWH2", "WWH3"}


def _inline(markup: str) -> str:
    """reportlab paragraph markup -> ODF inline XML (bold/italic spans, line breaks)."""
    s = markup.replace("<br/>", "\n").replace("<br>", "\n")
    out, pos = [], 0
    for m in re.finditer(r"</?(b|i|strong|em)>", s):
        out.append(("text", s[pos:m.start()]))
        out.append(("tag", m.group(0)))
        pos = m.end()
    out.append(("text", s[pos:]))
    xml, stack = [], []
    for kind, val in out:
        if kind == "text":
            t = html.escape(html.unescape(re.sub(r"<[^>]+>", "", val)), quote=False)
            xml.append(t.replace("\n", "<text:line-break/>"))
        elif val.startswith("</"):
            if stack:
                stack.pop()
                xml.append("</text:span>")
        else:
            name = "WWBold" if val.strip("<>") in ("b", "strong") else "WWItalic"
            stack.append(name)
            xml.append(f'<text:span text:style-name="{name}">')
    xml.extend("</text:span>" for _ in stack)
    return "".join(xml)


def _blocks(story):
    """Flatten the reportlab story into simple blocks."""
    from reportlab.platypus import Paragraph, Image, Table, PageBreak, KeepTogether
    blocks = []

    def walk(items):
        for f in items:
            if isinstance(f, KeepTogether):
                walk(f._content)
            elif isinstance(f, Paragraph):
                blocks.append({"kind": "p", "style": _STYLE_MAP.get(f.style.name, "WWBody"),
                               "xml": _inline(f.text)})
            elif isinstance(f, Image):
                blocks.append({"kind": "img", "path": f.filename,
                               "w_pt": float(f.drawWidth), "h_pt": float(f.drawHeight)})
            elif isinstance(f, Table):
                blocks.append({"kind": "table", "rows": [[str(c) for c in r] for r in f._cellvalues]})
            elif isinstance(f, PageBreak):
                blocks.append({"kind": "break"})
    walk(story)
    return blocks


def _fit(w_pt, h_pt, max_w_cm=17.0, max_h_cm=13.5):
    w, h = w_pt / PT_PER_CM, h_pt / PT_PER_CM
    k = min(1.0, max_w_cm / w, max_h_cm / h)
    return w * k, h * k


def _table_xml(rows, n):
    head = rows[0]
    risers = len(head) == 5 and head[0] == "Well" and head[3] == "Well"
    ncol = max(len(r) for r in rows)
    cols = "".join(f'<table:table-column table:style-name="WWCol{len(head)}_{j}"/>' for j in range(ncol))
    out = [f'<table:table table:name="WWTable{n}" table:style-name="WWTable{len(head)}">{cols}']
    for i, r in enumerate(rows):
        out.append("<table:table-row>")
        for j, c in enumerate(r + [""] * (ncol - len(r))):
            if risers and j == 2:
                cell = "WWCellGap"
            elif i == 0:
                cell = ("WWCellHeadGreen" if j < 2 else "WWCellHeadRed") if risers else "WWCellHead"
            else:
                cell = "WWCell"
            pst = "WWCellTextHead" if i == 0 else ("WWCellText" if j in (0, 3) and risers or (j == 0 and not risers) else "WWCellTextC")
            txt = html.escape(c, quote=False).replace("\n", "<text:line-break/>")
            out.append(f'<table:table-cell table:style-name="{cell}" office:value-type="string">'
                       f'<text:p text:style-name="{pst}">{txt}</text:p></table:table-cell>')
        out.append("</table:table-row>")
    out.append("</table:table>")
    return "".join(out)


_STYLES = """
<office:font-face-decls>
 <style:font-face style:name="Liberation Sans" svg:font-family="'Liberation Sans'" style:font-family-generic="swiss"/>
</office:font-face-decls>
<office:styles>
 <style:default-style style:family="paragraph">
  <style:paragraph-properties fo:orphans="2" fo:widows="2"/>
  <style:text-properties style:font-name="Liberation Sans" fo:font-size="10pt" fo:language="en" fo:country="GB"/>
 </style:default-style>
 <style:style style:name="Standard" style:family="paragraph" style:class="text"/>
 <style:style style:name="WWBody" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:margin-bottom="0.3cm" fo:line-height="140%" fo:text-align="justify"/>
 </style:style>
 <style:style style:name="WWBodyKeep" style:family="paragraph" style:parent-style-name="WWBody">
  <style:paragraph-properties fo:keep-with-next="always"/>
 </style:style>
 <style:style style:name="WWTitle" style:family="paragraph" style:parent-style-name="Standard" style:default-outline-level="1">
  <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.6cm" fo:keep-with-next="always"/>
  <style:text-properties fo:font-size="20pt" fo:font-weight="bold" fo:color="#1a5276"/>
 </style:style>
 <style:style style:name="WWH2" style:family="paragraph" style:parent-style-name="Standard" style:default-outline-level="2">
  <style:paragraph-properties fo:margin-top="0.6cm" fo:margin-bottom="0.3cm" fo:keep-with-next="always"/>
  <style:text-properties fo:font-size="14pt" fo:font-weight="bold" fo:color="#2e86c1"/>
 </style:style>
 <style:style style:name="WWH3" style:family="paragraph" style:parent-style-name="Standard" style:default-outline-level="3">
  <style:paragraph-properties fo:margin-top="0.4cm" fo:margin-bottom="0.2cm" fo:keep-with-next="always"/>
  <style:text-properties fo:font-size="11pt" fo:font-weight="bold" fo:color="#2874a6"/>
 </style:style>
 <style:style style:name="WWFigure" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:text-align="center" fo:keep-with-next="always" fo:margin-bottom="0.1cm"/>
 </style:style>
 <style:style style:name="WWCaption" style:family="paragraph" style:parent-style-name="Standard">
  <style:paragraph-properties fo:text-align="center" fo:margin-bottom="0.4cm"/>
  <style:text-properties fo:font-size="9pt" fo:font-style="italic" fo:color="#666666"/>
 </style:style>
 <style:style style:name="WWWarning" style:family="paragraph" style:parent-style-name="WWBody">
  <style:text-properties fo:font-style="italic" fo:color="#c0392b"/>
 </style:style>
 <style:style style:name="WWCellText" style:family="paragraph" style:parent-style-name="Standard">
  <style:text-properties fo:font-size="9pt"/>
 </style:style>
 <style:style style:name="WWCellTextC" style:family="paragraph" style:parent-style-name="WWCellText">
  <style:paragraph-properties fo:text-align="center"/>
 </style:style>
 <style:style style:name="WWCellTextHead" style:family="paragraph" style:parent-style-name="WWCellText">
  <style:paragraph-properties fo:text-align="center"/>
  <style:text-properties fo:font-weight="bold" fo:color="#ffffff"/>
 </style:style>
 <style:style style:name="WWBold" style:family="text"><style:text-properties fo:font-weight="bold"/></style:style>
 <style:style style:name="WWItalic" style:family="text"><style:text-properties fo:font-style="italic"/></style:style>
</office:styles>
<office:automatic-styles>
 <style:page-layout style:name="WWPage">
  <style:page-layout-properties fo:page-width="21cm" fo:page-height="29.7cm" fo:margin-top="2cm" fo:margin-bottom="2cm" fo:margin-left="2cm" fo:margin-right="2cm"/>
 </style:page-layout>
 <style:style style:name="WWBreak" style:family="paragraph" style:parent-style-name="WWH2">
  <style:paragraph-properties fo:break-before="page"/>
 </style:style>
 <style:style style:name="WWFrame" style:family="graphic">
  <style:graphic-properties style:vertical-pos="top" style:vertical-rel="baseline" fo:border="none"/>
 </style:style>
 %TABLESTYLES%
 <style:style style:name="WWCell" style:family="table-cell">
  <style:table-cell-properties fo:padding="0.1cm" fo:border="0.5pt solid #cccccc"/>
 </style:style>
 <style:style style:name="WWCellGap" style:family="table-cell">
  <style:table-cell-properties fo:padding="0.1cm" fo:border="none"/>
 </style:style>
 <style:style style:name="WWCellHead" style:family="table-cell">
  <style:table-cell-properties fo:padding="0.1cm" fo:background-color="#2e86c1" fo:border="0.5pt solid #cccccc"/>
 </style:style>
 <style:style style:name="WWCellHeadGreen" style:family="table-cell">
  <style:table-cell-properties fo:padding="0.1cm" fo:background-color="#27ae60" fo:border="0.5pt solid #cccccc"/>
 </style:style>
 <style:style style:name="WWCellHeadRed" style:family="table-cell">
  <style:table-cell-properties fo:padding="0.1cm" fo:background-color="#c0392b" fo:border="0.5pt solid #cccccc"/>
 </style:style>
</office:automatic-styles>
<office:master-styles>
 <style:master-page style:name="Standard" style:page-layout-name="WWPage"/>
</office:master-styles>
"""


def _table_styles(blocks):
    """Column widths per table shape (4- or 5-column weather table; 5-column risers table)."""
    widths = {4: [3.5, 4.0, 3.5, 4.0], 5: [3.0, 2.5, 1.0, 3.0, 2.5], 6: [3.2, 3.4, 3.4, 3.2, 3.6]}
    out, seen = [], set()
    for b in blocks:
        if b["kind"] != "table":
            continue
        n = len(b["rows"][0])
        if n in seen:
            continue
        seen.add(n)
        w = widths.get(n, [16.0 / n] * n)
        out.append(f'<style:style style:name="WWTable{n}" style:family="table">'
                   f'<style:table-properties style:width="{sum(w):.2f}cm" table:align="center" '
                   f'fo:margin-bottom="0.2cm"/></style:style>')
        for j, cw in enumerate(w):
            out.append(f'<style:style style:name="WWCol{n}_{j}" style:family="table-column">'
                       f'<style:table-column-properties style:column-width="{cw:.2f}cm"/></style:style>')
    return "".join(out)


def write_odt(story, odt_path):
    """Write `story` to `odt_path` (.odt). Returns the path, or None on failure."""
    blocks = _blocks(story)
    # keep-with-next for body paragraphs that lead into a figure under the same heading
    for i, b in enumerate(blocks):
        if b["kind"] == "p" and b["style"] == "WWBody":
            nxt = next((x for x in blocks[i + 1:] if x["kind"] != "break"), None)
            if nxt is not None and nxt["kind"] == "img":
                b["style"] = "WWBodyKeep"
    body, pending_break, n_img, n_tbl = [], False, 0, 0
    for b in blocks:
        if b["kind"] == "break":
            pending_break = True
            continue
        if b["kind"] == "p":
            st = b["style"]
            if pending_break:
                st = "WWBreak" if st == "WWH2" else st
                if st != "WWBreak":
                    body.append('<text:p text:style-name="WWBreak"/>')
                pending_break = False
            tag = "text:h" if st in _HEADINGS or st == "WWBreak" else "text:p"
            lvl = {"WWTitle": 1, "WWH2": 2, "WWBreak": 2, "WWH3": 3}.get(st)
            attr = f' text:outline-level="{lvl}"' if lvl else ""
            body.append(f'<{tag} text:style-name="{st}"{attr}>{b["xml"]}</{tag}>')
        elif b["kind"] == "img":
            n_img += 1
            w, h = _fit(b["w_pt"], b["h_pt"])
            with open(b["path"], "rb") as fh:
                data = base64.b64encode(fh.read()).decode()
            body.append(
                f'<text:p text:style-name="WWFigure"><draw:frame draw:style-name="WWFrame" '
                f'draw:name="Figure{n_img}" text:anchor-type="as-char" svg:width="{w:.3f}cm" '
                f'svg:height="{h:.3f}cm"><draw:image><office:binary-data>{data}'
                f'</office:binary-data></draw:image></draw:frame></text:p>')
        elif b["kind"] == "table":
            n_tbl += 1
            body.append(_table_xml(b["rows"], n_tbl))
    doc = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
           'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
           'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
           'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
           'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
           'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
           'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
           'xmlns:xlink="http://www.w3.org/1999/xlink" '
           'office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">'
           + _STYLES.replace("%TABLESTYLES%", _table_styles(blocks))
           + '<office:body><office:text>' + "".join(body) + '</office:text></office:body></office:document>')
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("    Warning: LibreOffice not found - ODT not written")
        return None
    with tempfile.TemporaryDirectory() as td:
        stem = os.path.splitext(os.path.basename(odt_path))[0]
        fodt = os.path.join(td, stem + ".fodt")
        with open(fodt, "w", encoding="utf-8") as fh:
            fh.write(doc)
        profile = "file://" + os.path.join(td, "lo_profile")
        r = subprocess.run([soffice, f"-env:UserInstallation={profile}", "--headless",
                            "--convert-to", "odt", "--outdir", td, fodt],
                           capture_output=True, text=True, timeout=300)
        out = os.path.join(td, stem + ".odt")
        if r.returncode != 0 or not os.path.exists(out):
            print(f"    Warning: ODT conversion failed: {r.stderr.strip()[:200]}")
            return None
        shutil.move(out, odt_path)
    return odt_path
