#!/usr/bin/env python3
"""
form_label_lint.py — does every split and every timescale say which model form it comes from?
===========================================================================================
Model A (no intercept, fixed datum) and Model B (free intercept) give different evaporation/
drainage splits and timescales about three times apart, and since D-283 the documents quote the
split from Model B and most other quantities from Model A. A share or a timescale quoted with no
form named is therefore ambiguous, and a wrong reading changes the answer (Martin 2026-10-28:
"do we make it clear in the documents when we are citing model a or model b?" ... "all 3 please").

Two passes, both over the documents the mirrors are made from:

  fields  Every number field (text:user-field-get) whose key names a form-dependent quantity --
          a drainage or ET share, a drainage/ET fraction, a half-life, an e-folding or
          mean-reversion time -- must have a FORM WORD in its sentence (Model A, Model B,
          no-intercept, free-intercept, depth-dependent, model-free, observed, Pastas, the
          recession ratio). A field in a table is checked against the table and its caption.
  typed   Every typed sentence in the mirrors that gives such a quantity as a number
          ("24 % of losses", "a half-life of 7.8 months") is held to the same rule.

A coefficient (beta_1..beta_3) on its own is NOT gated: each document's convention sentence says
an unnamed coefficient is Model A at the network datum. Exemptions, each with a reason, live in
tools/form_label_exempt.csv (doc stem, field or text fragment, reason).

Usage:
    python3 tools/form_label_lint.py            # report, exit 1 on any unlabelled value
    python3 tools/form_label_lint.py --list     # also print every labelled hit
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-28. First issue (D-284).

import argparse
import csv
import html
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
EXEMPT = REPO / "tools/form_label_exempt.csv"

FIELD_KEY = re.compile(r"drain(age)?_share|drain_frac|drain_pct|(^|_)ET_(pct|frac|share)|et_share|"
                       r"t_half|half_life|efold|e_fold|mean_reversion|recession_(time|months)", re.I)
# not timescales or shares: a regression R² over recession times; the depth-dependent model's 1/e decay DEPTH
FIELD_SKIP = re.compile(r"cluster_splithalf|_ari_|scrape_|_R2_|efold_depth", re.I)
FORM = re.compile(r"Model\s*A|Model\s*B|no-intercept|free-intercept|without an intercept|with an intercept|"
                  r"free intercept|intercept form|depth-dependent|model-free|without (a|either) model|observed|"
                  r"Pastas|recession ratio|seasonal recession|lag-1|autocorrelation|both forms|either form|"
                  r"each form|two forms|three estimators|four estimators|"
                  # a datum below ground implies the no-intercept form: Model B has none (D-217)
                  r"(at|to|of) (the|a|each well's|every) (project|network|network-wide|anchored|physical|MHW|common) datum|"
                  r"at the datum|(project|network|anchored|MHW|depth) datum|\d\.\d m datum|datum of \d|"
                  # the plain-language companions say the same in words, and the Welsh summaries in Welsh
                  r"(with|using) no model|no model|without a model|floor at|-metre floor|floor anywhere|"
                  r"nad yw'n defnyddio model|heb fodel|Model[au]? [AB]\b", re.I)
TYPED = re.compile(r"\d+(\.\d+)?\s*%\s*of\s*(the\s*)?(mean\s*)?(modelled\s*)?loss(es)?|"
                   r"drainage share[^.]{0,40}?\d+(\.\d+)?\s*%|"
                   r"(half-life|e-folding time|mean-reversion time|recession time|t½)[^.]{0,30}?\d+(\.\d+)?\s*months", re.I)
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def _plain(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def _sentence(text: str, i: int) -> str:
    starts = [0] + [m.end() for m in SENT.finditer(text) if m.end() <= i]
    a = starts[-1]
    m = SENT.search(text, i)
    return text[a:m.start() if m else len(text)]


def load_exempt() -> list[tuple[str, str]]:
    if not EXEMPT.exists():
        return []
    with EXEMPT.open(encoding="utf8") as fh:
        return [(r["doc"].strip(), r["match"].strip()) for r in csv.DictReader(fh)]


def exempt(ex, doc, what) -> bool:
    return any(d in (doc, "*") and m and m in what for d, m in ex)


def field_pass(ex, show):
    import field_sync as fs
    faults, ok = [], 0
    for p in fs.documents():
        xml = fs.read_xml(p)
        _, gets = fs.fields_in(xml)
        for name, a, b, shown in gets:
            if not FIELD_KEY.search(name) or FIELD_SKIP.search(name):
                continue
            t0 = xml.rfind("<table:table ", 0, a)
            t1 = xml.find("</table:table>", a)
            in_table = t0 != -1 and t1 != -1 and xml.rfind("</table:table>", 0, a) < t0
            if in_table:
                cap0 = max(0, xml.rfind("<text:p", 0, max(0, xml.rfind("<text:p", 0, t0))))
                ctx = _plain(xml[cap0:t1])
            else:
                pa, pb = xml.rfind("<text:p", 0, a), xml.find("</text:p>", a)
                pre, post = _plain(xml[pa:a]), _plain(xml[a:pb])
                ctx = _sentence(pre + "⟦" + post, len(pre)).replace("⟦", "")
            if FORM.search(ctx) or exempt(ex, p.stem, name):
                ok += 1
                if show:
                    print(f"  ok     {p.stem}: {name}")
                continue
            faults.append((p.stem, name, ctx.strip()[:200]))
    return faults, ok


def typed_pass(ex, show):
    import refresh_mirrors as rm
    faults, ok = [], 0
    for _src, mirror in rm.resolve():
        mp = pathlib.Path(mirror)
        mp = mp if mp.is_absolute() else REPO / mp
        if not mp.exists():
            continue
        for para in re.split(r"\n\s*\n", mp.read_text(encoding="utf8")):
            if para.lstrip().startswith(("<!--", "|", "+-", "#")):
                continue
            flat = " ".join(para.split())
            for m in TYPED.finditer(flat):
                s = _sentence(flat, m.start())
                if FORM.search(s) or exempt(ex, mp.stem, s):
                    ok += 1
                    continue
                faults.append((mp.stem, m.group(0), s.strip()[:200]))
    return faults, ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    ex = load_exempt()
    ff, fok = field_pass(ex, a.list)
    tf, tok = typed_pass(ex, a.list)
    for doc, name, ctx in ff:
        print(f"  FAIL  {doc}: field {name} has no form named in its sentence: …{ctx}…")
    for doc, hit, ctx in tf:
        print(f"  FAIL  {doc}: typed {hit!r} has no form named in its sentence: …{ctx}…")
    n = len(ff) + len(tf)
    print(f"form_label_lint: {'OK' if not n else 'FAIL'} — {fok + len(ff)} field(s) and {tok + len(tf)} typed "
          f"value(s) checked; {n} without a form")
    return 1 if n else 0


if __name__ == "__main__":
    raise SystemExit(main())
