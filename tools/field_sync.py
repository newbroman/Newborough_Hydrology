#!/usr/bin/env python3
"""
field_sync.py — every pipeline number in the documents is a field, set from the committed CSVs.

WHY THIS EXISTS
  A document used to hold a typed copy of each pipeline value. When the pipeline moved, the copy did
  not, and the only link between them was a citation-index row a person had to confirm. The papers
  drifted that way (inventory 2026-10-01: Paper 1 carried 6 confirmed citations against 773 numbers,
  many older than the report). Martin, 2026-10-01: "build the structure so that the numbers in the
  report tally with the numbers in the paper directly. So any changes to reports can move with them
  into the papers directly." (D-219)

HOW
  A quoted pipeline number is an ODF user field: a declaration in the document
  (<text:user-field-decl text:name="N" office:string-value="V"/>) and one or more uses in the text
  (<text:user-field-get text:name="N">V</text:user-field-get>). LibreOffice shows and keeps them
  (tested 2026-10-01); pandoc drops the use's text, so refresh_mirrors unwraps fields before converting.

  tools/number_fields.csv is the ONE register shared by every document:
      field, source_csv, key, scale, abs, dp, plus, minus, thousands, note
  `key` is the label cite_check.collect_values() gives the row (Parameter, qualified by its Well/Era
  cells where the Parameter repeats). A value is rendered as
      x = value * scale (then |x| if abs); fixed to dp places; thousands separator if set;
      a leading `minus` character when negative after rounding, `+` when positive and plus=1.
  Rounding is a rendering decision (CLAUDE.md); the register says how, once, for every document.

  --check   every field declared in every document is in the register, renders from its CSV, and
            the declaration and every displayed use equal the rendering. Exit 1 otherwise. A gate.
  --write   set every declaration and use to the rendering (odt_edit's guarded write, in place, like
            table_gen: field values are generated content). Prints each field whose value MOVED with
            the sentence it sits in, so a change of conclusion is seen (D-191), not silently typeset.
  --list    the register, with each field's current rendering and the documents using it.

Usage:
    python3 tools/field_sync.py --check
    python3 tools/field_sync.py --write
    python3 tools/field_sync.py --list [--doc report8]
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

REGISTER = REPO / "tools" / "number_fields.csv"
COLUMNS = ["field", "source_csv", "key", "scale", "abs", "dp", "plus", "minus", "thousands", "note"]

DECL_RE = re.compile(r'<text:user-field-decl\b[^>]*?text:name="([^"]+)"[^>]*?/>')
DECL_VAL_RE = re.compile(r'office:string-value="([^"]*)"')
GET_RE = re.compile(r'<text:user-field-get\b[^>]*?text:name="([^"]+)"[^>]*>(.*?)</text:user-field-get>', re.S)


# ── register ────────────────────────────────────────────────────────────────
def load_register() -> dict[str, dict]:
    if not REGISTER.exists():
        return {}
    with REGISTER.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    reg = {}
    for r in rows:
        if r["field"] in reg:
            raise SystemExit(f"number_fields.csv: field {r['field']!r} registered twice")
        reg[r["field"]] = r
    return reg


def save_register(reg: dict[str, dict]) -> None:
    with REGISTER.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for name in sorted(reg):
            w.writerow({c: reg[name].get(c, "") for c in COLUMNS})


_VALUES: dict | None = None


def values() -> dict[tuple[str, str], float]:
    """(source_csv, key) -> committed value, exactly as cite_check registers it."""
    global _VALUES
    if _VALUES is None:
        import cite_check as cc
        _VALUES = {(src, lab): v for src, lab, v in cc.collect_values()}
    return _VALUES


def render(v: float, row: dict) -> str:
    x = v * float(row.get("scale") or 1)
    if str(row.get("abs") or "") in ("1", "True", "true"):
        x = abs(x)
    dp = int(row.get("dp") or 0)
    body = f"{abs(x):,.{dp}f}" if row.get("thousands") == "," else f"{abs(x):.{dp}f}"
    if round(x, dp) < 0:
        return (row.get("minus") or "−") + body
    if round(x, dp) > 0 and str(row.get("plus") or "") in ("1", "True", "true"):
        return "+" + body
    return body


def rendered(row: dict) -> str | None:
    v = values().get((row["source_csv"], row["key"]))
    return None if v is None else render(v, row)


# ── documents ───────────────────────────────────────────────────────────────
def documents() -> list[pathlib.Path]:
    """Every ODT/ODM the mirrors are made from (the newest version of each family)."""
    import refresh_mirrors as rm
    return [src for src, _dst in rm.resolve()]


def read_xml(p: pathlib.Path) -> str:
    with zipfile.ZipFile(p) as z:
        return z.read("content.xml").decode("utf-8")


def fields_in(xml: str) -> tuple[dict, list]:
    decls = {}
    for m in DECL_RE.finditer(xml):
        vm = DECL_VAL_RE.search(m.group(0))
        decls[m.group(1)] = (m.start(), m.end(), html.unescape(vm.group(1)) if vm else None)
    gets = [(m.group(1), m.start(2), m.end(2), html.unescape(re.sub(r"<[^>]+>", "", m.group(2))))
            for m in GET_RE.finditer(xml)]
    return decls, gets


def _plain_context(xml: str, pos: int, width: int = 90) -> str:
    a = xml.rfind("<text:p", 0, pos)
    b = xml.find("</text:p>", pos)
    t = re.sub(r"<[^>]+>", "", xml[a:pos]) + "⟦" + re.sub(r"<[^>]+>", "", xml[pos:b])
    i = t.index("⟦")
    return html.unescape(t[max(0, i - width):i + width]).replace("⟦", "")


# ── check / write ───────────────────────────────────────────────────────────
def audit(reg, docs):
    """[(doc, kind, field, detail)] and per-doc planned spans for --write."""
    faults, plans = [], {}
    for p in docs:
        xml = read_xml(p)
        decls, gets = fields_in(xml)
        if not decls and not gets:
            continue
        spans = []
        for name, (a, b, val) in decls.items():
            row = reg.get(name)
            if row is None:
                faults.append((p, "unregistered", name, "declared in the document, not in number_fields.csv"))
                continue
            want = rendered(row)
            if want is None:
                faults.append((p, "no-value", name, f"{row['source_csv']} · {row['key']} is not a committed value"))
                continue
            if val != want:
                faults.append((p, "decl", name, f"declared {val!r}, CSV renders {want!r}"))
                tag = xml[a:b]
                new = DECL_VAL_RE.sub(f'office:string-value="{html.escape(want, quote=True)}"', tag, count=1)
                spans.append((a, b, new, name, val, want))
        for name, a, b, shown in gets:
            if name not in decls:
                faults.append((p, "undeclared", name, "used in the text with no declaration"))
                continue
            row = reg.get(name)
            want = rendered(row) if row else None
            if want is not None and shown != want:
                faults.append((p, "shown", name, f"shows {shown!r}, CSV renders {want!r} — …{_plain_context(xml, a)}…"))
                spans.append((a, b, html.escape(want, quote=False), name, shown, want))
        if spans:
            plans[p] = spans
    return faults, plans


def write(plans) -> bool:
    import odt_edit
    odt_edit.REASON = "field_sync"
    ok = True
    for p, spans in plans.items():
        tmp = pathlib.Path(tempfile.gettempdir()) / ("fs_" + p.name)
        shutil.copyfile(p, tmp)
        xml = read_xml(tmp)
        for a, b, new, name, old, want in spans:
            if xml[a:b].startswith("<text:user-field-decl"):
                print(f"  MOVED {name}: {old!r} → {want!r}  ({p.name})")
            else:
                print(f"        …{_plain_context(xml, a)}…")
        r = odt_edit.edit_spans(tmp, p, [(a, b, new) for a, b, new, *_ in spans],
                                expect=len(spans), allow_tag_change=True)
        tmp.unlink(missing_ok=True)
        ok &= bool(r)
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    g.add_argument("--list", action="store_true")
    ap.add_argument("--doc", help="restrict to documents whose filename contains this")
    a = ap.parse_args()
    reg = load_register()
    docs = [p for p in documents() if not a.doc or a.doc in p.name]
    if a.list:
        use = {}
        for p in docs:
            d, _ = fields_in(read_xml(p))
            for n in d:
                use.setdefault(n, []).append(p.stem)
        for n, r in sorted(reg.items()):
            print(f"  {n:60s} {str(rendered(r)):>12s}  {r['source_csv'].split('/')[-1]} · {r['key']}  [{', '.join(use.get(n, ['unused']))}]")
        print(f"field_sync: {len(reg)} registered field(s)")
        return 0
    faults, plans = audit(reg, docs)
    n_fields = sum(len(fields_in(read_xml(p))[0]) for p in docs)
    if a.check:
        for p, kind, name, det in faults:
            print(f"  FAIL  {p.name}: {kind} {name}: {det}")
        print(f"field_sync: {'OK' if not faults else 'FAIL'} — {len(reg)} registered field(s), "
              f"{n_fields} declaration(s) across the documents, {len(faults)} fault(s)")
        return 0 if not faults else 1
    hard = [f for f in faults if f[1] in ("unregistered", "no-value", "undeclared")]
    for p, kind, name, det in hard:
        print(f"  FAIL  {p.name}: {kind} {name}: {det}")
    if hard:
        print("field_sync: not writing — fix the register first")
        return 1
    if not plans:
        print(f"field_sync: every field current ({n_fields} declaration(s))")
        return 0
    return 0 if write(plans) else 1


if __name__ == "__main__":
    sys.exit(main())
