#!/usr/bin/env python3
"""
record_basis_claims_lint.py
===========================
Every registered analysis STATES, in its own methods section, which record it uses.

Why this exists.

  tools/record_basis.csv is the register of which wells and which record each
  analysis fits and evaluates, and record_basis_lint proves the register against
  each script's fit_ssm call. That closes the code-to-register link. The
  register-to-reader link was open: the report told the reader in one sentence
  (§3.1.1) that "the analyses that follow deliberately use different parts of
  the record", and pointed elsewhere for the details. Martin (2026-09-21) chose
  to state the basis in each methods section rather than add a generated table
  ("B with a gate is better than A with a table renumber") — and a statement
  with no gate is the shape of the rule that was broken six times that morning.

  This lint is the gate. tools/record_basis_claims.csv carries, for every row
  of record_basis.csv, the document and methods section that states the basis
  and the FRAGMENT of that statement which must be present. The chain is then
  code -> register (record_basis_lint) -> sentence (this lint), each link
  checked before every commit.

What it checks.

  1. Every id in record_basis.csv has at least one claims row; a claims row
     whose id has left the register is stale. Both fail.
  2. The claims row's document exists (a mirror), its section heading is found,
     and the fragment appears in that section's text — headings and prose are
     normalised the same way (pandoc escapes, bold markers, dash forms,
     whitespace) so a fragment is written as a reader would read it.
  3. A row with doc=none states, with a reason in its note, that no document
     presents the analysis (a working phase, an unpresented output). It is an
     explicit absence, not a gap, and it fails without the reason.
  4. A fragment must say something about the RECORD: it has to contain one of
     the basis words (record, window, months, pre-, post-, event, scene, frame,
     fit, refit, no fit, interpolat, inherit, panel, aggregat, seeded, year,
     calibrat). "See Section 3.4" is not a statement of basis.

  A fragment that no longer appears is the signal: the prose was edited and
  the statement fell out, or the register changed and the prose did not.

Usage:
    python3 tools/record_basis_claims_lint.py             # gate; non-zero on a fault
    python3 tools/record_basis_claims_lint.py --quiet
    python3 tools/record_basis_claims_lint.py --selftest
    python3 tools/record_basis_claims_lint.py --show report8 "Spatial Coefficient Mapping"
                                                          # print a section's normalised text
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-21. Option B for the record basis.

REPO = Path(__file__).resolve().parents[1]
REGISTER = REPO / "tools/record_basis.csv"
CLAIMS = REPO / "tools/record_basis_claims.csv"
DOCS = {
    "report6": "report_edits/text/report6.md", "report7": "report_edits/text/report7.md",
    "report8": "report_edits/text/report8.md", "report9": "report_edits/text/report9.md",
    "report10": "report_edits/text/report10.md", "report11": "report_edits/text/report11.md",
    "report12": "report_edits/text/report12.md",
    "MS": "docs/report/text/Newborough_Methods_Supplement.md",
    "SM": "docs/report/text/Supplementary_Material.md",
    "Paper1": "docs/papers/paper_1/text/Paper1.md",
    "Paper2": "docs/papers/paper_2/text/Hollingham_2026_Paper2_amended.md",
}
BASIS_WORDS = re.compile(r"record|window|months|\bpre-|\bpost-|event|scene|frame|\bfit|refit|no fit|"
                         r"interpolat|inherit|panel|aggregat|seeded|year|calibrat|driven", re.I)
HEADING = re.compile(r"^(#+)\s*(.*)$")


def normalise(text: str) -> str:
    text = re.sub(r"\[\]\{#[^}]*\}", "", text)          # pandoc anchors
    text = text.replace("\\'", "'").replace('\\"', '"').replace("\\_", "_").replace("\\*", "*")
    text = text.replace("**", "").replace("*", "")
    text = text.replace("---", "—").replace("--", "–")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def sections(md_text: str) -> list[tuple[int, str, str]]:
    """[(level, heading, body)] for every heading in a mirror."""
    out, cur, buf = [], None, []
    for line in md_text.splitlines():
        m = HEADING.match(line)
        if m:
            if cur:
                out.append((cur[0], cur[1], "\n".join(buf)))
            cur, buf = (len(m.group(1)), normalise(m.group(2))), []
        else:
            buf.append(line)
    if cur:
        out.append((cur[0], cur[1], "\n".join(buf)))
    # a section's text runs to the next heading of the same or a higher level
    result = []
    for i, (lvl, head, body) in enumerate(out):
        text = [body]
        for lvl2, _h2, body2 in out[i + 1:]:
            if lvl2 <= lvl:
                break
            text.append(body2)
        result.append((lvl, head, normalise(" ".join(text))))
    return result


def find_section(secs, wanted: str):
    w = normalise(wanted).lower()
    hits = [s for s in secs if w in s[1].lower()]
    return hits


def load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if any(v.strip() for v in r.values() if v)]


def check(register_rows, claim_rows, read=lambda rel: (REPO / rel).read_text(encoding="utf-8"),
          docs=DOCS) -> list[str]:
    faults = []
    reg_ids = {r["id"] for r in register_rows}
    claimed = {r["rb_id"] for r in claim_rows}
    for rid in sorted(reg_ids - claimed):
        faults.append(f"{rid}: registered in record_basis.csv but no claims row states its basis")
    cache = {}
    for r in claim_rows:
        rid = r["rb_id"]
        if rid not in reg_ids:
            faults.append(f"{rid}: claims row for an analysis no longer in record_basis.csv")
            continue
        if r["doc"] == "none":
            # an explicit statement that no document presents the analysis --
            # accepted only with a reason, so silence is never the default
            if not (r.get("note") or "").strip():
                faults.append(f"{rid}: doc=none needs a note saying why no document states its basis")
            continue
        rel = docs.get(r["doc"])
        if not rel:
            faults.append(f"{rid}: unknown doc {r['doc']!r}")
            continue
        if rel not in cache:
            try:
                cache[rel] = sections(read(rel))
            except FileNotFoundError:
                faults.append(f"{rid}: mirror {rel} not found")
                cache[rel] = None
                continue
        secs = cache[rel]
        if secs is None:
            continue
        hits = find_section(secs, r["section"])
        if not hits:
            faults.append(f"{rid}: no heading containing {r['section']!r} in {r['doc']}")
            continue
        frag = normalise(r["fragment"])
        if not BASIS_WORDS.search(frag):
            faults.append(f"{rid}: fragment states nothing about the record: {frag[:80]!r}")
            continue
        if not any(frag.lower() in s[2].lower() for s in hits):
            faults.append(f"{rid}: fragment not found in {r['doc']} § {hits[0][1][:50]!r}: {frag[:90]!r}")
    return faults


def selftest() -> bool:
    md = ("# Methods\n\n## Clustering\n\nEach pair is correlated on the months the two wells share; no fitting window is applied.\n\n"
          "## Mapping\n\nThe atlas interpolates the per-well store and fits nothing itself.\n\n### Sub\n\nmore text\n\n## Other\n\nunrelated\n")
    reg = [{"id": "RB-A"}, {"id": "RB-B"}, {"id": "RB-C"}]
    claims = [
        {"rb_id": "RB-A", "doc": "T", "section": "Clustering", "fragment": "no fitting window is applied"},
        {"rb_id": "RB-B", "doc": "T", "section": "Mapping", "fragment": "fits nothing itself"},
        {"rb_id": "RB-B", "doc": "T", "section": "Mapping", "fragment": "see Section 3.4"},           # no basis word
        {"rb_id": "RB-Z", "doc": "T", "section": "Other", "fragment": "full record"},                 # stale id
        {"rb_id": "RB-A", "doc": "T", "section": "Nowhere", "fragment": "full record"},               # no heading
        {"rb_id": "RB-A", "doc": "T", "section": "Other", "fragment": "the full record of every well"},  # absent
    ]
    faults = check(reg, claims, read=lambda rel: md, docs={"T": "t.md"})
    want = ["RB-C: registered", "RB-B: fragment states nothing", "RB-Z: claims row", "RB-A: no heading", "RB-A: fragment not found"]
    ok = len(faults) == 5 and all(any(f.startswith(w) for f in faults) for w in want)
    if not ok:
        print("  selftest FAIL:"); [print("   ", f) for f in faults]
    return ok


def main(argv) -> int:
    if "--selftest" in argv:
        ok = selftest()
        print("  record_basis_claims_lint selftest: " + ("OK" if ok else "FAIL"))
        return 0 if ok else 1
    if "--show" in argv:
        i = argv.index("--show")
        doc, head = argv[i + 1], argv[i + 2]
        secs = sections((REPO / DOCS[doc]).read_text(encoding="utf-8"))
        for lvl, h, body in find_section(secs, head):
            print(f"== {'#' * lvl} {h}\n{body}\n")
        return 0
    quiet = "--quiet" in argv
    reg, claims = load(REGISTER), load(CLAIMS)
    faults = check(reg, claims)
    for f in faults:
        print(f"  FAIL {f}")
    if faults:
        print(f"  record_basis_claims_lint: {len(faults)} fault(s) — an analysis whose record basis "
              f"the methods text no longer states")
        return 1
    if not quiet:
        print(f"  record_basis_claims_lint: OK — {len(reg)} analyses, {len(claims)} statement(s) found "
              f"in the methods text")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
