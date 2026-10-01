#!/usr/bin/env python3
"""
field_convert.py — turn a document's confirmed citations into number fields (D-219).

Each CONFIRMED row of tools/citation_index.csv names a number a document quotes and the committed
value it cites. This tool wraps that number, in the document's content.xml, in an ODF user field named
for the value (see field_sync.py), adds the declaration, and adds the field to
tools/number_fields.csv with the rendering that reproduces the quoted text exactly.

Conservative by construction — a number is converted only when ALL hold:
  - the citation is confirmed and its value is committed now (cite_check.collect_values);
  - some rendering of the committed value (scale 1, 100, 1000 or 0.001, optionally absolute) gives
    EXACTLY the quoted string, sign and separators included — so conversion never changes the text;
  - the quoted string occurs in the document as one text run (not split across spans), outside any
    table (generated tables belong to table_gen) and not already inside a field;
  - the index row's context picks out exactly one such occurrence.
Everything else is listed with its reason and left as it is.

Usage:
    python3 tools/field_convert.py report8 --dry-run
    python3 tools/field_convert.py report8
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-01 (D-219). First issue.

import argparse
import csv
import html
import pathlib
import re
import shutil
import sys
import tempfile
import zipfile

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import field_sync as fs  # noqa: E402

SCALES = (1, 100, 1000, 0.001)


def _norm(t: str) -> str:
    t = html.unescape(t).replace("\\", "").replace("*", "")
    t = t.replace("---", "—").replace("--", "–")
    return re.sub(r"\s+", " ", t).strip().lower()


def _spec_for(v: float, quoted: str):
    """A register row (without field/source/key) whose rendering of v is exactly `quoted`."""
    q = quoted.strip()
    m = re.fullmatch(r"([+−\-]?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?", q)
    if not m:
        return None
    sign, whole, frac = m.groups()
    dp = len(frac or "")
    thousands = "," if "," in whole else ""
    minus = sign if sign in ("−", "-") else "−"
    for scale in SCALES:
        for absf in ("", "1"):
            row = {"scale": str(scale), "abs": absf, "dp": str(dp), "plus": "1" if sign == "+" else "",
                   "minus": minus, "thousands": thousands}
            if fs.render(v, row) == q:
                return row
    return None


def field_name(key: str, spec: dict) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_")
    tag = ""
    if spec["scale"] != "1":
        tag += "_x" + spec["scale"].replace(".", "p")
    if spec["abs"]:
        tag += "_abs"
    tag += f"_dp{spec['dp']}"
    if spec["plus"]:
        tag += "_plus"
    if spec["minus"] == "-":
        tag += "_hy"
    if spec["thousands"]:
        tag += "_th"
    return base + tag


def doc_for(stem: str):
    import refresh_mirrors as rm
    for src, dst in rm.resolve():
        if pathlib.Path(dst).stem == stem or src.stem == stem:
            return src, pathlib.Path(dst)
    raise SystemExit(f"no document with mirror stem {stem!r}")


def _occurrences(xml: str, quoted_x: str):
    """Positions of quoted_x as a whole number in a text run, outside tables and fields."""
    out = []
    for m in re.finditer(re.escape(quoted_x), xml):
        a, b = m.start(), m.end()
        pre, post = xml[a - 1:a], xml[b:b + 1]
        if re.match(r"[\d.,]", pre) or re.match(r"\d", post) or (post == "." and re.match(r"\d", xml[b + 1:b + 2])):
            continue
        if pre in ("+", "-", "−") and not quoted_x[:1] in ("+", "-", "−"):
            continue
        last_lt, last_gt = xml.rfind("<", 0, a), xml.rfind(">", 0, a)
        if last_lt > last_gt:
            continue                                   # inside a tag
        if xml.rfind("<table:table ", 0, a) > xml.rfind("</table:table>", 0, a):
            continue                                   # inside a table
        if xml.rfind("<text:user-field-get", 0, a) > xml.rfind("</text:user-field-get>", 0, a):
            continue                                   # already a field
        out.append((a, b))
    return out


def _plain_around(xml: str, a: int, b: int, width: int = 60):
    p0 = xml.rfind("<text:p", 0, a)
    p0 = max(p0, xml.rfind("<text:h", 0, a))
    p1 = xml.find("</text:p>", b)
    before = re.sub(r"<[^>]+>", "", xml[p0:a])
    after = re.sub(r"<[^>]+>", "", xml[b:p1])
    return _norm(before)[-width:], _norm(after)[:width]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stem", help="mirror stem, e.g. report8, Paper1, Newborough_Methods_Supplement")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    src, mirror = doc_for(a.stem)
    rel_mirror = str(mirror.relative_to(REPO)) if mirror.is_absolute() else str(mirror)
    rows = [r for r in csv.DictReader(open(REPO / "tools/citation_index.csv", encoding="utf-8"))
            if r["status"] == "confirmed" and r["document"] == rel_mirror]
    xml = fs.read_xml(src)
    reg = fs.load_register()
    vals = fs.values()
    spans, new_fields, skipped = [], {}, []
    taken = set()
    for r in rows:
        v = vals.get((r["source_csv"], r["key"]))
        if v is None:
            skipped.append((r, "value no longer committed")); continue
        spec = _spec_for(v, r["quoted"])
        if spec is None:
            skipped.append((r, f"no rendering of {v!r} gives {r['quoted']!r} exactly")); continue
        occ = _occurrences(xml, html.escape(r["quoted"].strip(), quote=False))
        if not occ:
            skipped.append((r, "not found as one text run outside tables and fields")); continue
        nb, na = _norm(r["before"])[-25:], _norm(r["after"])[:25]
        hits = []
        for (x0, x1) in occ:
            pb, pa = _plain_around(xml, x0, x1)
            if (not nb or pb.endswith(nb[-min(len(nb), len(pb)):] if pb else False)) and (not na or pa.startswith(na[:min(len(na), len(pa))])):
                hits.append((x0, x1))
        if len(hits) != 1:
            skipped.append((r, f"context matches {len(hits)} occurrence(s) of {len(occ)}")); continue
        x0, x1 = hits[0]
        if (x0, x1) in taken:
            continue
        taken.add((x0, x1))
        name = field_name(r["key"], spec)
        row = dict(spec, field=name, source_csv=r["source_csv"], key=r["key"],
                   note=f"converted from citation_index ({rel_mirror})")
        if name in reg and any(reg[name].get(k) != row.get(k) for k in ("source_csv", "key", "scale", "abs", "dp", "plus", "minus", "thousands")):
            skipped.append((r, f"field {name} already registered with a different spec")); continue
        new_fields[name] = row
        spans.append((x0, x1, f'<text:user-field-get text:name="{name}">{xml[x0:x1]}</text:user-field-get>'))
    # declarations
    decls, _ = fs.fields_in(xml)
    add = [n for n in new_fields if n not in decls]
    if add:
        dx = "".join(f'<text:user-field-decl office:value-type="string" office:string-value="{html.escape(fs.render(vals[(new_fields[n]["source_csv"], new_fields[n]["key"])], new_fields[n]), quote=True)}" text:name="{n}"/>' for n in add)
        if "<text:user-field-decls>" in xml:
            i = xml.index("<text:user-field-decls>") + len("<text:user-field-decls>")
            spans.append((i, i, dx))
        else:
            ot = xml.index("<office:text")
            i = xml.index(">", ot) + 1
            first_block = min(k for k in (xml.find("<text:p", i), xml.find("<text:h", i), len(xml)) if k != -1)
            for anchor in ("</text:sequence-decls>", "</text:variable-decls>"):
                k = xml.find(anchor, i, first_block)
                if k != -1:
                    i = k + len(anchor)
                    break
            spans.append((i, i, "<text:user-field-decls>" + dx + "</text:user-field-decls>"))
    print(f"field_convert {a.stem}: {len(rows)} confirmed citation(s); {len(taken)} to convert, "
          f"{len(new_fields)} field(s), {len(skipped)} left as text")
    for r, why in skipped:
        print(f"   skip  {r['key'][:60]:60s} {r['quoted']!r:>12s}  {why}")
    if a.dry_run or not taken:
        return 0
    import odt_edit
    odt_edit.REASON = "field_convert"
    tmp = pathlib.Path(tempfile.gettempdir()) / ("fc_" + src.name)
    shutil.copyfile(src, tmp)
    ok = odt_edit.edit_spans(tmp, src, spans, expect=len(spans), allow_tag_change=True)
    tmp.unlink(missing_ok=True)
    if ok:
        reg.update(new_fields)
        fs.save_register(reg)
        print(f"  registered {len(new_fields)} field(s) in tools/number_fields.csv")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
