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
      field, source_csv, key, scale, abs, dp, plus, minus, thousands, note, date
  `key` is the label cite_check.collect_values() gives the row (Parameter, qualified by its Well/Era
  cells where the Parameter repeats). A value is rendered as
      x = value * scale (then |x| if abs); fixed to dp places; thousands separator if set;
      a NEGATIVE dp rounds to tens, hundreds, ... and prints no decimals ("about 900 m": dp = -2);
      a leading `minus` character when negative after rounding, `+` when positive and plus=1.
  Rounding is a rendering decision (CLAUDE.md); the register says how, once, for every document.

  A DATE field (1.3.0, J-31) has a format in `date` and leaves the number columns empty. Its source is a
  report-numbers row whose Value is an ISO date — YYYY, YYYY-MM or YYYY-MM-DD — keyed exactly as
  cite_check keys a number (dates()). The format takes %B (January), %b (Jan), %Y (2018), %y (18),
  %m (01) and %d (01), with English month names whatever the locale. A year range ("1989–96") is two
  fields with the en dash typed between them: `%Y` on the first month, `%y` on the last.

  --check   every field declared in every document is in the register, renders from its CSV, and
            the declaration and every displayed use equal the rendering. Exit 1 otherwise. A gate.
  --write   set every declaration and use to the rendering (odt_edit's guarded write, in place, like
            table_gen: field values are generated content). Prints each field whose value MOVED with
            the sentence it sits in, so a change of conclusion is seen (D-191), not silently typeset.
  --list    the register, with each field's current rendering and the documents using it.
  --selftest the renderings (number and date) against fixed cases; no document is read. Exit 1 on a miss.

Usage:
    python3 tools/field_sync.py --check
    python3 tools/field_sync.py --write
    python3 tools/field_sync.py --list [--doc report8]
"""
from __future__ import annotations

__version__ = "1.4.0"  # Hollingham (2026) — 2026-11-24 (T-204, D-327): declares its inputs (tools/gate_inputs.py);
#   SKIP when they are absent by design, FAIL on zero subjects.
# "1.3.0"  # Hollingham (2026) — 2026-11-23 (J-31; Martin 2026-11-21: "all dates should be fields!"). A DATE
#   field: a `date` column holds a format (%B %Y -> "January 2018", %y -> "96"), and its value is an ISO date a
#   report-numbers row carries as a string (dates()). The number path is unchanged: a row with `date` empty renders
#   exactly as 1.2.0 did. --selftest added.
# 1.2.0  # Hollingham (2026) — 2026-10-10 (spec NRG_spec_parallel_chats_2026-10-10): the register is
#   read and written through tools/register_io, so a field another chat registered while this one
#   ran is kept, not overwritten (a short lock file and a row merge).
# 1.1.0  # Hollingham (2026) — 2026-10-09 (spec NRG_spec_emit_first_report9_2026-10-09): dp may be
#   negative, rounding to tens/hundreds for a number the text quotes round ("about 900 m" from L = 902).
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
from gate_inputs import declare_inputs  # noqa: E402  (T-204, D-327)

REGISTER = REPO / "tools" / "number_fields.csv"
COLUMNS = ["field", "source_csv", "key", "scale", "abs", "dp", "plus", "minus", "thousands", "note", "date"]

DECL_RE = re.compile(r'<text:user-field-decl\b[^>]*?text:name="([^"]+)"[^>]*?/>')
DECL_VAL_RE = re.compile(r'office:string-value="([^"]*)"')
GET_RE = re.compile(r'<text:user-field-get\b[^>]*?text:name="([^"]+)"[^>]*>(.*?)</text:user-field-get>', re.S)


# ── register ────────────────────────────────────────────────────────────────
def load_register() -> dict[str, dict]:
    if not REGISTER.exists():
        return {}
    import register_io
    rows = register_io.read_rows(REGISTER)
    reg = {}
    for r in rows:
        if r["field"] in reg:
            raise SystemExit(f"number_fields.csv: field {r['field']!r} registered twice")
        reg[r["field"]] = r
    return reg


def save_register(reg: dict[str, dict]) -> None:
    # 1.2.0: merged against the file as it is now, under a lock (tools/register_io.py), so fields
    # another chat registered since load_register() survive.
    import register_io
    register_io.write_rows(REGISTER, COLUMNS, [{c: reg[name].get(c, "") for c in COLUMNS} for name in sorted(reg)],
                           sort_key=lambda r: r["field"], key_cols=["field"])


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
    if dp < 0:                                   # 1.1.0: round to 10**-dp, print as a whole number
        x = float(round(x, dp))
    fdp = max(dp, 0)
    body = f"{abs(x):,.{fdp}f}" if row.get("thousands") == "," else f"{abs(x):.{fdp}f}"
    if round(x, dp) < 0:
        return (row.get("minus") or "−") + body
    if round(x, dp) > 0 and str(row.get("plus") or "") in ("1", "True", "true"):
        return "+" + body
    return body


# ── dates (1.3.0, J-31) ─────────────────────────────────────────────────────
ISO_DATE_RE = re.compile(r"(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December")
_DATE_TOKENS = {"B", "b", "Y", "y", "m", "d"}
_DATES: dict | None = None


def dates() -> dict[tuple[str, str], str]:
    """(source_csv, key) -> committed ISO date string, keyed as cite_check.collect_values() keys a number.

    collect_values() skips a row whose Value is not a number, so a date never enters the number register
    and nothing that checks numbers sees it; this reads the same files for the rows it skipped."""
    global _DATES
    if _DATES is None:
        import pandas as pd
        import cite_check as cc
        _DATES = {}
        for p in sorted(REPO.glob("outputs/**/*report_numbers*.csv")):
            if any(d in p.parts for d in cc.EXCLUDE_OUTPUT_DIRS):
                continue
            try:
                df = pd.read_csv(p, dtype=str, keep_default_na=False)
            except Exception:
                continue
            cols = {c.lower(): c for c in df.columns}
            kcol = cols.get("key") or df.columns[0]
            vcol = cols.get("value")
            if vcol is None:
                continue
            repeated = set(df[kcol][df[kcol].duplicated(keep=False)])
            qual = [c for c in (cols.get("well"), cols.get("era"), cols.get("control"), cols.get("tier")) if c]
            rel = str(p.relative_to(REPO))
            for _, r in df.iterrows():
                v = str(r[vcol]).strip()
                if not ISO_DATE_RE.fullmatch(v):
                    continue
                lab = str(r[kcol])
                if lab in repeated:
                    parts = [str(r[c]).strip() for c in qual if str(r[c]).strip()]
                    if parts:
                        lab = " · ".join([lab] + parts)
                _DATES[(rel, lab)] = v
    return _DATES


def render_date(iso: str, fmt: str) -> str:
    """An ISO date (YYYY, YYYY-MM or YYYY-MM-DD) in `fmt`. A token the date does not carry (a month in a
    bare year) or a token outside %B %b %Y %y %m %d raises ValueError: the register is wrong, not the text."""
    m = ISO_DATE_RE.fullmatch(str(iso).strip())
    if not m:
        raise ValueError(f"not an ISO date: {iso!r}")
    y, mo, d = m.group(1), m.group(2), m.group(3)

    def tok(t: re.Match) -> str:
        c = t.group(1)
        if c == "%":
            return "%"
        if c not in _DATE_TOKENS:
            raise ValueError(f"date format {fmt!r}: %{c} is not supported")
        if c == "Y":
            return y
        if c == "y":
            return y[2:]
        if c in ("B", "b", "m"):
            if mo is None:
                raise ValueError(f"date format {fmt!r} needs a month; {iso!r} has none")
            name = MONTHS[int(mo) - 1]
            return name if c == "B" else name[:3] if c == "b" else mo
        if d is None:
            raise ValueError(f"date format {fmt!r} needs a day; {iso!r} has none")
        return d
    return re.sub(r"%(.)", tok, fmt)


def is_date(row: dict) -> bool:
    return bool((row.get("date") or "").strip())


def rendered(row: dict) -> str | None:
    if is_date(row):                             # 1.3.0
        v = dates().get((row["source_csv"], row["key"]))
        return None if v is None else render_date(v, row["date"])
    v = values().get((row["source_csv"], row["key"]))
    return None if v is None else render(v, row)


def selftest() -> int:
    """Fixed cases for both paths. The number cases pin 1.2.0's behaviour, which 1.3.0 must not move."""
    num = [(0.6119815, dict(dp="2"), "0.61"), (-1.5049, dict(dp="2"), "−1.50"), (-1.5083, dict(dp="2"), "−1.51"),
           (902.0, dict(dp="-2"), "900"), (0.4512, dict(scale="100", dp="0"), "45"), (-0.25, dict(dp="2", abs="1"), "0.25"),
           (0.18, dict(dp="2", plus="1"), "+0.18"), (-0.18, dict(dp="2", minus="-"), "-0.18"),
           (12345.6, dict(dp="0", thousands=","), "12,346"), (0.0, dict(dp="2", plus="1"), "0.00"),
           (0.004, dict(dp="2"), "0.00"), (-0.004, dict(dp="2"), "0.00")]
    dat = [("2018-01-01", "%B %Y", "January 2018"), ("2026-02-01", "%B %Y", "February 2026"),
           ("2026-02", "%b %Y", "Feb 2026"), ("1989-03-01", "%Y", "1989"), ("1996-12-01", "%y", "96"),
           ("1951", "%Y", "1951"), ("2017-12-31", "%d/%m/%Y", "31/12/2017"), ("2005-03", "%Y-%m", "2005-03"),
           ("2000-01", "100%% %Y", "100% 2000")]
    bad = [("1951", "%B %Y"), ("2018-01", "%d"), ("2018-01-01", "%A"), ("January 2018", "%Y")]
    miss = 0
    for v, row, want in num:
        got = render(v, row)
        if got != want:
            miss += 1
            print(f"  MISS number {v!r} {row}: {got!r} != {want!r}")
        if rendered_number_unchanged(v, row) != got:
            miss += 1
            print(f"  MISS number {v!r} {row}: an empty `date` changed the rendering")
    for iso, fmt, want in dat:
        got = render_date(iso, fmt)
        if got != want:
            miss += 1
            print(f"  MISS date {iso!r} {fmt!r}: {got!r} != {want!r}")
    for iso, fmt in bad:
        try:
            got = render_date(iso, fmt)
        except ValueError:
            continue
        miss += 1
        print(f"  MISS date {iso!r} {fmt!r}: rendered {got!r}, should have refused")
    n = len(num) * 2 + len(dat) + len(bad)
    print(f"field_sync selftest: {'OK' if not miss else 'FAIL'} — {n - miss} of {n} case(s)")
    return 0 if not miss else 1


def rendered_number_unchanged(v: float, row: dict) -> str:
    """The number path with an explicit empty `date`: what every pre-1.3.0 row in the register is."""
    return render(v, dict(row, date=""))


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
                faults.append((p, "no-value", name, f"{row['source_csv']} · {row['key']} is not a committed "
                                                    f"{'date' if is_date(row) else 'value'}"))
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
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--doc", help="restrict to documents whose filename contains this")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    inp = declare_inputs("field_sync", documents=["docs/**/*.odt", "report_edits/odt/*.odt"],
                         register="tools/number_fields.csv")
    if inp.absent and (a.check or a.write):
        return inp.skip()
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
        bad = inp.floor_fault(n_fields, "field declaration(s) across the documents")
        if bad:
            return bad
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
