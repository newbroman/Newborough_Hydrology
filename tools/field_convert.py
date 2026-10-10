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

--bindings FILE (1.1.0) takes the numbers from FILE instead of the citation index: one row per number
with quoted, before, after (plain text either side; after may be empty), source_csv, key, and
optionally the rendering (scale, abs, dp, plus, minus, thousands; dp may be negative, field_sync 1.1.0)
and a field name. The emit-first pass (spec NRG_spec_emit_first_report9_2026-10-09) binds each number
to the key a script emits for it; the same guards apply, and a given rendering must reproduce the
quoted text exactly.

Usage:
    python3 tools/field_convert.py report8 --dry-run
    python3 tools/field_convert.py report8
    python3 tools/field_convert.py report9 --bindings scratch/emit/report9_demo_bind.csv --dry-run
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-10-10: --content FILE converts a content.xml taken out of
#   the document (written to FILE.new, applied on the publishing machine by a whole-content odt_edit swap), so a
#   chapter-sized binding file runs where there is no time limit; occurrences are cached per quoted string.
# 1.1.0  # Hollingham (2026) — 2026-10-09 (spec NRG_spec_emit_first_report9_2026-10-09): --bindings
#   FILE binds numbers to named keys from a file rather than the citation index; a negative dp is tagged _dpmN.
# 1.0.0  # Hollingham (2026) — 2026-10-01 (D-219). First issue.

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
    tag += f"_dp{spec['dp']}".replace("-", "m")
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
    ap.add_argument("--content", help="a content.xml to convert instead of the ODT; the result goes to CONTENT.new")
    ap.add_argument("--bindings", help="CSV of numbers to bind (quoted, before, after, source_csv, key[, rendering][, field])")
    a = ap.parse_args()
    if a.content:      # 1.2.0: the ODT may not be on this machine; the mirror names the document
        src = None
        hits = [p for p in list(REPO.glob("report_edits/text/*.md")) + list(REPO.glob("docs/**/text/*.md")) if p.stem == a.stem]
        if len(hits) != 1:
            raise SystemExit(f"--content: {len(hits)} mirrors with stem {a.stem!r}")
        mirror = hits[0]
    else:
        src, mirror = doc_for(a.stem)
    rel_mirror = str(mirror.relative_to(REPO)) if mirror.is_absolute() else str(mirror)
    if a.bindings:
        rows = list(csv.DictReader(open(a.bindings, encoding="utf-8")))
        origin = f"bound by {pathlib.Path(a.bindings).name} ({rel_mirror})"
    else:
        rows = [r for r in csv.DictReader(open(REPO / "tools/citation_index.csv", encoding="utf-8"))
                if r["status"] == "confirmed" and r["document"] == rel_mirror]
        origin = f"converted from citation_index ({rel_mirror})"
    xml = pathlib.Path(a.content).read_text(encoding="utf-8") if a.content else fs.read_xml(src)
    _occ_cache: dict = {}
    reg = fs.load_register()
    vals = fs.values()
    spans, new_fields, skipped = [], {}, []
    taken = set()
    for r in rows:
        v = vals.get((r["source_csv"], r["key"]))
        if v is None:
            skipped.append((r, "value no longer committed")); continue
        given = {k: (r.get(k) or "") for k in ("scale", "abs", "dp", "plus", "minus", "thousands")}
        if given["dp"] != "":
            given["scale"] = given["scale"] or "1"
            given["minus"] = given["minus"] or "−"
            spec = given if fs.render(v, given) == r["quoted"].strip() else None
        else:
            spec = _spec_for(v, r["quoted"])
        if spec is None:
            skipped.append((r, f"no rendering of {v!r} gives {r['quoted']!r} exactly")); continue
        _qx = html.escape(r["quoted"].strip(), quote=False)
        if _qx not in _occ_cache:
            _occ_cache[_qx] = _occurrences(xml, _qx)
        occ = _occ_cache[_qx]
        if not occ:
            skipped.append((r, "not found as one text run outside tables and fields")); continue
        nb, na = _norm(r.get("before") or "")[-25:], _norm(r.get("after") or "")[:25]
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
        name = (r.get("field") or "").strip() or field_name(r["key"], spec)
        # 1.2.0: two keys from different files can sanitise to one name (C3 · p_value in 14_ and 21_);
        # the second takes its file's stem as a prefix rather than overwriting the first.
        _same = lambda d: d.get("source_csv") == r["source_csv"] and d.get("key") == r["key"]
        if (name in new_fields and not _same(new_fields[name])) or (name in reg and not _same(reg[name])):
            name = re.sub(r"[^A-Za-z0-9]+", "_", pathlib.Path(r["source_csv"]).stem).strip("_") + "__" + name
        row = dict(spec, field=name, source_csv=r["source_csv"], key=r["key"], note=origin)
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
    print(f"field_convert {a.stem}: {len(rows)} {'binding(s)' if a.bindings else 'confirmed citation(s)'}; {len(taken)} to convert, "
          f"{len(new_fields)} field(s), {len(skipped)} left as text")
    for r, why in skipped:
        print(f"   skip  {r['key'][:60]:60s} {r['quoted']!r:>12s}  {why}")
    if a.dry_run or not taken:
        return 0
    if a.content:
        out = xml
        for x0, x1, rep_ in sorted(spans, key=lambda t: (t[0], t[1]), reverse=True):
            out = out[:x0] + rep_ + out[x1:]
        pathlib.Path(a.content + ".new").write_text(out, encoding="utf-8")
        reg.update(new_fields)
        fs.save_register(reg)
        print(f"  wrote {a.content}.new; registered {len(new_fields)} field(s) in tools/number_fields.csv")
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
