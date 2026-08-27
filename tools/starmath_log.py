#!/usr/bin/env python3
"""
starmath_log.py — the one surface none of the other checks can see.

WHY THIS EXISTS

  An ODF formula is not text in the document. It is a whole embedded document:
  `Object NN/content.xml` inside the zip, holding the same equation TWICE --

      MathML          <mi>d</mi> ...      what a renderer draws
      StarMath        {d} over {30}       what LibreOffice re-parses on open

  Both live below the top-level `content.xml`. `refresh_mirrors` runs pandoc over
  the document and gets an image or a flattened string; `symbol_check` reads the
  mirrors; `symbol_apply` reads the top-level `content.xml` only. So every glyph
  inside an equation is invisible to all three, and has been for the whole
  project. report8 alone carries 82 of them.

  Worse than invisible: EDITABLE WRONG. LibreOffice treats the StarMath
  annotation as the source and regenerates the MathML from it when the formula is
  next touched. Edit the MathML alone and the change survives every check in this
  repository, renders correctly in the exported PDF, and then silently reverts the
  first time someone double-clicks the equation. That is a corruption with a
  delay fuse on it, and nothing here would have caught it.

WHAT THIS TOOL DOES

  Reads every embedded formula object in the corpus and reports three things:

  DRIFT      the two representations disagree about which registered glyphs they
             contain. Exactly the fuse above: one was edited, the other was not.
             This GATES.

  DISPLACED  the formula carries a glyph whose registered sense says it must
             yield -- work `symbol_check` would have listed if it could see in
             here. Advisory, because a formula gives too little context to
             classify the sense automatically, and guessing is how `α_B_B` nearly
             reached three published documents.

  INVENTORY  all of them, one line each, written to the ledger so the equations
             are a diffable surface for the first time.

  It writes nothing into any document. Applying an equation edit means editing
  BOTH representations, by hand, in `tools/odt_edit.py`'s `edit_entries()`.

Usage
    python3 tools/starmath_log.py              audit; exits 1 on DRIFT
    python3 tools/starmath_log.py --write      regenerate the ledger
    python3 tools/starmath_log.py --show 5     dump one object's two forms
    python3 tools/starmath_log.py --doc report8   restrict to one document
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-27.

import argparse
import csv
import html
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doc_paths as dp  # noqa: E402

REPO = dp.REPO
REGISTER = REPO / "tools" / "symbol_register.csv"
LEDGER = REPO / "notes" / "ledgers" / "EQUATION_LEDGER.md"

_OBJ = re.compile(r"^Object \d+/content\.xml$")
_ANN = re.compile(r'<annotation encoding="StarMath 5\.0">(.*?)</annotation>', re.S)
_MI = re.compile(r"<m(?:i|o)[^>]*>([^<]*)</m(?:i|o)>")

# StarMath spells Greek two ways and both occur in this corpus: the literal
# character (Object 2's `^ {α}`) and the escape (`%alpha`). Only the glyphs the
# register actually carries need mapping.
_GREEK = {
    "%alpha": "α", "%delta": "δ", "%epsilon": "ε", "%eta": "η",
    "%lambda": "λ", "%sigma": "σ", "%tau": "τ", "%phi": "φ", "%psi": "ψ",
    "%ALPHA": "Α", "%DELTA": "Δ",
}

# LibreOffice does NOT render %phi as φ. It renders it as ϕ (U+03D5, GREEK PHI
# SYMBOL), and %epsilon as ϵ (U+03F5), and it writes those codepoints into the
# MathML while the StarMath keeps the escape. The register, the prose and every
# other tool in this repository spell φ and ε. To a reader they are the same
# letter; to `str.find` they are not, which is why the equations sat outside the
# symbol register without either side noticing.
#
# Folded here so a typographic split does not read as a semantic one, and
# reported separately below so it does not read as nothing at all.
_VARIANTS = {
    "\u03d5": "φ", "\u03f5": "ε", "\u03d1": "θ", "\u03f0": "κ",
    "\u03d6": "π", "\u03f1": "ρ", "\u03c2": "σ", "\u03d2": "Υ",
}


def _fold(ch: str) -> str:
    return _VARIANTS.get(ch, ch)


def registered_glyphs() -> tuple[set[str], dict[str, list[dict]]]:
    """The bare-sense glyphs, and the displaced senses each one carries.

    Only BARE senses are collected, for the same reason `symbol_check` audits
    only those: a reader seeing D_fell is in no doubt which quantity is meant,
    so a subscripted sense does not compete for the glyph.
    """
    if not REGISTER.exists():
        sys.exit(f"no register at {REGISTER.relative_to(REPO)}")
    glyphs: set[str] = set()
    displaced: dict[str, list[dict]] = {}
    for row in csv.DictReader(REGISTER.open(encoding="utf8")):
        if (row.get("form") or "").strip() != "bare":
            continue
        g = (row.get("glyph") or "").strip()
        if not g:
            continue
        glyphs.add(g)
        if (row.get("status") or "").strip() == "displaced":
            displaced.setdefault(g, []).append(row)
    return glyphs, displaced


def latest_versions(paths: list[Path]) -> list[Path]:
    """One ODT per document family — the highest _vN_M, or the only one.

    `docs/` keeps every exported version. Logging all of them would report the
    same five formulas five times over and bury the report's eighty-two.
    """
    fam: dict[str, tuple[tuple[int, ...], Path]] = {}
    for p in paths:
        m = re.match(r"^(.*?)_v(\d+(?:_\d+)*)$", p.stem)
        stem, key = (m.group(1), tuple(int(x) for x in m.group(2).split("_"))) \
            if m else (p.stem, (-1,))
        cur = fam.get(stem)
        if cur is None or key > cur[0]:
            fam[stem] = (key, p)
    return sorted((v[1] for v in fam.values()), key=lambda p: p.as_posix())


def source_odts() -> list[Path]:
    """Every ODT that could hold a formula: the live chapters plus the newest
    export of each published document."""
    chapters = sorted(dp.ODT_DIR.glob("report*.odt"))
    published = latest_versions(sorted((REPO / "docs").rglob("*.odt")))
    return chapters + published


def glyphs_in_mathml(xml: str, known: set[str]) -> set[str]:
    body = _ANN.sub("", xml)
    found = set()
    for tok in _MI.findall(body):
        tok = html.unescape(tok).strip()
        if len(tok) == 1:
            tok = _fold(tok)
        if tok in known:
            found.add(tok)
    return found


def variants_in_mathml(xml: str, known: set[str]) -> set[str]:
    """Registered glyphs written with a variant codepoint — ϕ for φ, ϵ for ε.

    Not drift: the formula says what it means. But a document that spells one
    glyph two ways defeats every search that would have found it, including the
    one this project runs to prove a symbol means one thing everywhere.
    """
    body = _ANN.sub("", xml)
    out = set()
    for tok in _MI.findall(body):
        tok = html.unescape(tok).strip()
        if len(tok) == 1 and tok in _VARIANTS and _VARIANTS[tok] in known:
            out.add(tok)
    return out


def glyphs_in_starmath(sm: str, known: set[str]) -> set[str]:
    """Registered glyphs used as identifiers.

    Tokenised rather than searched, because StarMath's keywords are made of the
    same letters the register spends: a substring scan finds `c` and `d` in
    `cdot` and reports drift in every formula with a product in it. A token of
    length one is an identifier; a longer alphabetic token is a keyword or a
    function name.
    """
    for esc, ch in _GREEK.items():
        sm = sm.replace(esc, ch)
    found = set()
    for tok in re.findall(r"[^\W\d_]+", sm, re.UNICODE):
        if len(tok) == 1 and _fold(tok) in known:
            found.add(_fold(tok))
    return found


def read_objects(odt: Path, known: set[str]) -> list[dict]:
    out = []
    try:
        z = zipfile.ZipFile(odt)
    except (OSError, zipfile.BadZipFile) as e:
        print(f"  starmath_log: cannot open {dp.rel(odt)} — {e}")
        return out
    with z:
        for name in sorted((n for n in z.namelist() if _OBJ.match(n)),
                           key=lambda s: int(re.search(r"\d+", s).group())):
            try:
                xml = z.read(name).decode("utf8", errors="replace")
            except (KeyError, OSError):
                continue
            m = _ANN.search(xml)
            sm = html.unescape(m.group(1)).strip() if m else ""
            out.append({
                "doc": dp.rel(odt),
                "obj": name.split("/")[0],
                "starmath": sm,
                "has_annotation": bool(m),
                "mathml": glyphs_in_mathml(xml, known),
                "variants": variants_in_mathml(xml, known),
                "sm_glyphs": glyphs_in_starmath(sm, known) if m else set(),
            })
    return out


def audit(objs: list[dict], displaced: dict[str, list[dict]]):
    drift, missing, disp, var = [], [], [], []
    for o in objs:
        if not o["has_annotation"]:
            # No StarMath at all: the formula cannot be re-parsed, and an edit
            # to the MathML is the ONLY edit possible. Worth knowing, not a fault.
            missing.append(o)
            continue
        if o["mathml"] != o["sm_glyphs"]:
            drift.append(o)
        hit = sorted(g for g in (o["mathml"] | o["sm_glyphs"]) if g in displaced)
        if hit:
            disp.append((o, hit))
        if o["variants"]:
            var.append(o)
    return drift, missing, disp, var


def write_ledger(objs: list[dict], drift, missing, disp, var) -> None:
    by_doc: dict[str, list[dict]] = {}
    for o in objs:
        by_doc.setdefault(o["doc"], []).append(o)
    L = []
    A = L.append
    A("# EQUATION_LEDGER — the embedded formula objects")
    A("")
    A("**Generated by `tools/starmath_log.py`. Do not edit by hand — regenerate"
      " with `--write`.**")
    A("")
    A("Every equation in this corpus is an embedded ODF object carrying the same")
    A("formula twice: MathML, which is drawn, and a StarMath annotation, which")
    A("LibreOffice re-parses and from which it REGENERATES the MathML. They are")
    A("below the top-level `content.xml`, so `refresh_mirrors` does not mirror")
    A("them, `symbol_check` does not read them and `symbol_apply` does not write")
    A("them. This file is the only place they are visible.")
    A("")
    A("**Editing one representation and not the other reverts the edit silently**")
    A("the next time the formula is opened. Both, or neither.")
    A("")
    A(f"- **Objects:** {len(objs)} across {len(by_doc)} document(s)")
    A(f"- **MathML/StarMath drift:** {len(drift)}")
    A(f"- **No StarMath annotation:** {len(missing)}")
    A(f"- **Carrying a displaced glyph:** {len(disp)}")
    A(f"- **Spelling a glyph with a variant codepoint:** {len(var)}")
    A("")
    if drift:
        A("## Drift — the two representations disagree")
        A("")
        A("| document | object | MathML | StarMath |")
        A("|---|---|---|---|")
        for o in drift:
            A(f"| {o['doc']} | {o['obj']} | "
              f"{' '.join(sorted(o['mathml'])) or '—'} | "
              f"{' '.join(sorted(o['sm_glyphs'])) or '—'} |")
        A("")
    if disp:
        A("## Carrying a glyph the register says must yield")
        A("")
        A("Advisory. A formula carries too little context to say which sense is")
        A("meant, and a symbol renamed on a guess changes what an equation")
        A("asserts without changing anything a proof-reader would notice.")
        A("")
        A("| document | object | glyph(s) | formula |")
        A("|---|---|---|---|")
        for o, hit in disp:
            f = o["starmath"].replace("|", "\\|")
            f = f[:110] + ("…" if len(o["starmath"]) > 110 else "")
            A(f"| {o['doc']} | {o['obj']} | {' '.join(hit)} | `{f}` |")
        A("")
    if var:
        A("## Variant codepoints — the same letter, spelled twice")
        A("")
        A("LibreOffice renders `%phi` as **ϕ** (U+03D5) and `%epsilon` as **ϵ**")
        A("(U+03F5). The register, the prose and every other check in this")
        A("repository spell **φ** (U+03C6) and **ε** (U+03B5). A reader cannot")
        A("tell them apart; `str.find` cannot see past it. This is why the")
        A("equations sat outside the symbol register with neither side noticing.")
        A("")
        A("| document | object | variant | canonical |")
        A("|---|---|---|---|")
        for o in var:
            for ch in sorted(o["variants"]):
                A(f"| {o['doc']} | {o['obj']} | {ch} U+{ord(ch):04X} | "
                  f"{_VARIANTS[ch]} U+{ord(_VARIANTS[ch]):04X} |")
        A("")
    A("## Inventory")
    A("")
    for doc in sorted(by_doc):
        A(f"### {doc}")
        A("")
        A("| object | glyphs | StarMath |")
        A("|---|---|---|")
        for o in by_doc[doc]:
            f = o["starmath"].replace("|", "\\|")
            f = f[:150] + ("…" if len(o["starmath"]) > 150 else "")
            g = " ".join(sorted(o["mathml"] | o["sm_glyphs"])) or "—"
            A(f"| {o['obj']} | {g} | `{f or 'NO STARMATH ANNOTATION'}` |")
        A("")
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text("\n".join(L) + "\n", encoding="utf8")
    print(f"  wrote {dp.rel(LEDGER)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="regenerate the ledger")
    ap.add_argument("--show", help="dump one object, e.g. --show 5")
    ap.add_argument("--doc", help="restrict to documents whose path contains this")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    known, displaced = registered_glyphs()
    odts = source_odts()
    if a.doc:
        odts = [p for p in odts if a.doc in p.as_posix()]
    objs = [o for p in odts for o in read_objects(p, known)]

    if a.show:
        want = f"Object {a.show}"
        for o in objs:
            if o["obj"] == want:
                print(f"{o['doc']}  {o['obj']}")
                print(f"  MathML glyphs   : {' '.join(sorted(o['mathml'])) or '—'}")
                print(f"  StarMath glyphs : {' '.join(sorted(o['sm_glyphs'])) or '—'}")
                print(f"  StarMath        : {o['starmath'] or 'NONE'}")
        return 0

    drift, missing, disp, var = audit(objs, displaced)

    if not a.quiet:
        print("=" * 78)
        print("EQUATIONS — the embedded formula objects")
        print("=" * 78)
        docs = sorted({o["doc"] for o in objs})
        for d in docs:
            n = sum(1 for o in objs if o["doc"] == d)
            print(f"  {n:4d}  {d}")
        print()

    if missing and not a.quiet:
        print(f"  {len(missing)} object(s) with NO StarMath annotation — MathML is")
        print("  the only representation, so a MathML edit is safe there and")
        print("  nowhere else:")
        for o in missing[:10]:
            print(f"    {o['doc']}  {o['obj']}")
        print()

    if disp and not a.quiet:
        print(f"  {len(disp)} object(s) carry a glyph with a displaced sense —")
        print("  work symbol_check cannot see. Advisory; see the ledger.")
        for o, hit in disp[:8]:
            print(f"    {o['doc']}  {o['obj']}  [{' '.join(hit)}]")
            print(f"        {o['starmath'][:96]}")
        if len(disp) > 8:
            print(f"    … and {len(disp) - 8} more")
        print()

    if var and not a.quiet:
        chars = sorted({c for o in var for c in o["variants"]})
        print(f"  {len(var)} object(s) spell a registered glyph with a variant")
        print("  codepoint — " + ", ".join(
            f"{c} U+{ord(c):04X} for {_VARIANTS[c]} U+{ord(_VARIANTS[c]):04X}"
            for c in chars) + ".")
        print("  Same letter to a reader, different string to every check.")
        print()

    if a.write:
        write_ledger(objs, drift, missing, disp, var)

    if drift:
        print("  starmath_log: FAULT — MathML and StarMath disagree")
        for o in drift:
            print(f"    {o['doc']}  {o['obj']}")
            print(f"        MathML   {' '.join(sorted(o['mathml'])) or '—'}")
            print(f"        StarMath {' '.join(sorted(o['sm_glyphs'])) or '—'}")
        print("  One representation was edited and the other was not. LibreOffice")
        print("  regenerates the MathML from the StarMath, so the MathML edit will")
        print("  revert the next time the formula is opened. Edit both.")
        return 1

    if not a.quiet:
        print(f"  starmath_log: OK — {len(objs)} formula object(s), "
              f"MathML and StarMath agree, "
              f"{len(disp)} displaced + {len(var)} variant (advisory)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
