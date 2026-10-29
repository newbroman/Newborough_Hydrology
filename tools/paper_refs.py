#!/usr/bin/env python3
"""
paper_refs.py — typed figure and table numbering in the papers, checked and re-plannable.

WHY THIS EXISTS

  The report numbers its captions with sequence fields, and reference_lint reads
  them from report.odm. The papers do not: every caption number is TYPED
  ("**Figure 18.**"), so is the image's alt text ("Figure 18. Illustrative
  forest reach ..."), and so is every reference in the paper, its SI and its
  plain companion. Adding one figure to Paper 1 therefore moves three kinds of
  typed number in three documents, and until 2026-10-25 nothing checked any of
  them: reference_lint reads only the master, figref_lint only report.pdf.

WHAT IT CHECKS (per family: the paper, then its SI and plain companion)

  captions    each kind numbered 1..n in the main paper, no gap, no duplicate   GATES
  references  every typed "Figure N" / "Table N" (and each number of a plural
              list or range) in any document of the family resolves to a caption  GATES
  alt text    every number an image's alt text gives is a caption number      GATES
  meaning     each caption's opening words against tools/paper_caption_snapshot.csv:
              a number that now heads a different caption fails until re-pinned  GATES
  orphans     captions nothing references                                     advisory
  alt titles  alt text whose opening words differ from its caption's         advisory

  A reference is EXTERNAL, and not checked, when the words just before it name
  another work ("Hollingham, 2026c", "report") — "Figure S3" never matches. A
  number followed by "_" (a filename) or "-0N" (a script id), or preceded by
  "script", is not a reference (the repoint_refs 1.7.0 rules).

RENUMBERING A PAPER

  1. Bump the paper's version first (odt_edit): versioned documents are never
     edited in place, and the re-point below writes the current file.
  2. python3 tools/paper_refs.py --plan paper1 --kind figure --insert 7
       writes tools/renumber_plan_paper1_figure_<date>.csv (every number >= 7
       moves up one); --remove N writes the opposite move.
  3. python3 tools/repoint_refs.py --scope paper1 --kind figure --plan <csv> --dry-run
       then --apply: captions, alt text and references move together, in the
       paper, its SI and its plain companion, and nowhere else.
  4. Insert the new figure and its caption under the freed number.
  5. python3 tools/paper_refs.py  — "meaning" fails for the moved numbers; read
     them, then --snapshot to re-pin.
  6. python3 tools/repoint_verify.py --plan <csv> --path docs/papers/<paper dir>  against the mirrors
     (a paper that gained references to the new figure is reported "not alignable"; count them).

Usage:
    python3 tools/paper_refs.py                     # check every family; exit 1 on a gate
    python3 tools/paper_refs.py --family paper1
    python3 tools/paper_refs.py --snapshot          # re-pin caption meanings
    python3 tools/paper_refs.py --plan paper1 --kind figure --insert 7
    python3 tools/paper_refs.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) - 2026-10-27. SKIP, not FAIL, when the checkout carries no paper
#   document at all (the public clone; T-127 read "broken" in the daily cloud check).
# 1.0.0  # Hollingham (2026) - 2026-10-25. First issue (Martin 06:52: "set up
#   mechanisms so that renumbering for new figures and tables in the papers is already set up").

import argparse
import csv
import datetime
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refresh_mirrors import resolve                          # noqa: E402
from repoint_refs import _text_view                          # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "tools" / "paper_caption_snapshot.csv"

# family -> (main paper stem, other documents citing its numbers). Stems are filename
# prefixes of resolve()'s CURRENT files, never typed versions (D-071).
FAMILIES = {
    "paper1": ("Paper1_v", ["PAPER1_SI_methods", "Paper1_plain"]),
    "paper2": ("Hollingham_2026_Paper2_amended", ["Paper2_plain"]),
    "paperM": ("PaperM_v", ["PaperM_plain"]),
}
KINDS = ("figure", "table")

ALT = re.compile(r"<(svg:desc|svg:title)>([^<]*)</\1>")
CAPTION = re.compile(r"(?m)^[ \t ]*(Figure|Table)[ \t ]+(\d{1,3})\.(?!\d)")
SINGLE = re.compile(r"(?i)\b(figure|fig\.?|table)[^\S\n]+(\d{1,3})(?!\d)(?!\.\d)")
PLURAL = re.compile(r"(?i)\b(figures|figs\.?|tables)((?:[^\S\n]|\d{1,3}|,|;|and|to|–|—|-)+)")
NUMS = re.compile(r"(\d{1,3})(?:\s*(?:[–—]|-{1,2}|to)\s*(\d{1,3}))?")
EXTERNAL = re.compile(r"(?i)(hollingham[^)\n]{0,12}20\d\d[a-z]?[,;]?\s*(§[\d.]+,?\s*)?|\breport\s+|\bscript\s+)$")


def current(stem: str) -> Path | None:
    for src, _mirror in resolve():
        if src.name.startswith(stem):
            return src
    return None


def read(path: Path) -> tuple[str, list[str]]:
    """(text view with alt text removed, [alt texts])."""
    xml = zipfile.ZipFile(path).read("content.xml").decode("utf-8")
    alts = [m.group(2) for m in ALT.finditer(xml)]
    return _text_view(ALT.sub("", xml))[0], alts


def captions(text: str) -> dict[str, list[tuple[int, str, int]]]:
    out = {k: [] for k in KINDS}
    for m in CAPTION.finditer(text):
        title = " ".join(text[m.end():m.end() + 200].split())[:60]
        out[m.group(1).lower()].append((int(m.group(2)), title, m.start(2)))
    return out


def _not_reference(text: str, b: int) -> bool:
    nxt = text[b:b + 3]
    return nxt[:1] == "_" or bool(re.match(r"-0\d", nxt))


def references(text: str, skip_at: set[int]) -> tuple[dict[str, list[int]], int]:
    """{kind: [numbers]} for typed references, and the count of external ones."""
    refs, external, claimed = {k: [] for k in KINDS}, 0, set()
    for m in PLURAL.finditer(text):
        kind = "table" if m.group(1).lower().startswith("tab") else "figure"
        if EXTERNAL.search(text, max(0, m.start() - 40), m.start()):
            external += 1
            continue
        base = m.start(2)
        for n in NUMS.finditer(m.group(2)):
            a, b = base + n.start(1), base + n.end()
            if _not_reference(text, b):
                continue
            lo = int(n.group(1))
            hi = int(n.group(2)) if n.group(2) else lo
            refs[kind] += list(range(lo, hi + 1)) if 0 <= hi - lo <= 30 else [lo, hi]
            claimed.add(a)
    for m in SINGLE.finditer(text):
        a = m.start(2)
        if a in skip_at or a in claimed or _not_reference(text, m.end(2)):
            continue
        if EXTERNAL.search(text, max(0, m.start() - 40), m.start()):
            external += 1
            continue
        kind = "table" if m.group(1).lower().startswith("tab") else "figure"
        refs[kind].append(int(m.group(2)))
    return refs, external


def check(family: str, snap: dict, verbose: bool = True) -> tuple[int, list[tuple]]:
    main_stem, others = FAMILIES[family]
    main = current(main_stem)
    if main is None:
        print(f"── {family}: FAIL no current document for {main_stem!r}")
        return 1, []
    text, alts = read(main)
    caps = captions(text)
    bad, pins = 0, []
    other_paths = [p for p in (current(o) for o in others) if p]
    print(f"── {family}  ({main.name}" + "".join(f", {p.name}" for p in other_paths) + ")")
    for kind in KINDS:
        nums = [n for n, _, _ in caps[kind]]
        if nums and sorted(nums) != list(range(1, max(nums) + 1)):
            dup = sorted({n for n in nums if nums.count(n) > 1})
            gap = sorted(set(range(1, max(nums) + 1)) - set(nums))
            print(f"   FAIL  {kind} captions are not 1..{max(nums)}: gaps {gap}, duplicates {dup}")
            bad += 1
        for n, title, _ in caps[kind]:
            pins.append((family, kind, n, title))
            old = snap.get((family, kind, n))
            if old is not None and old != title:
                print(f"   FAIL  {kind} {n} now heads a different caption (re-pin with --snapshot "
                      f"once its references are checked)\n           was: {old}\n           now: {title}")
                bad += 1
    have = {k: {n for n, _, _ in caps[k]} for k in KINDS}
    cited = {k: set() for k in KINDS}
    ext_total = 0
    for path in [main] + other_paths:
        t = text if path == main else read(path)[0]
        at = {pos for k in KINDS for _, _, pos in caps[k]} if path == main else set()
        refs, ext = references(t, at)
        ext_total += ext
        for kind in KINDS:
            cited[kind] |= set(refs[kind])
            dangling = sorted(set(refs[kind]) - have[kind])
            if dangling:
                print(f"   FAIL  {path.name}: {kind} reference(s) {dangling} resolve to no caption")
                bad += 1
    for a in alts:
        m = re.match(r"\s*(Figure|Table)\s+(\d{1,3})\.", a)
        if not m:
            continue
        kind, n = m.group(1).lower(), int(m.group(2))
        if n not in have[kind]:
            print(f"   FAIL  alt text names {kind} {n}, which has no caption: {a[:60]!r}")
            bad += 1
            continue
        title = next(t for nn, t, _ in caps[kind] if nn == n)
        alt_title = " ".join(a[m.end():].split())[:25]
        if verbose and alt_title and not title.startswith(alt_title):
            print(f"   note  alt text of {kind} {n} differs from its caption: {alt_title!r} / {title[:25]!r}")
    for kind in KINDS:
        orphan = sorted(have[kind] - cited[kind])
        if orphan and verbose:
            print(f"   note  {kind} caption(s) {orphan} referenced nowhere in the family")
    print(f"   {'ok' if not bad else 'FAIL'}    figures {len(have['figure'])}, tables {len(have['table'])}, "
          f"external references skipped {ext_total}")
    return bad, pins


def load_snapshot() -> dict:
    if not SNAPSHOT.exists():
        return {}
    with SNAPSHOT.open(encoding="utf8") as fh:
        return {(r["family"], r["kind"], int(r["number"])): r["title"] for r in csv.DictReader(fh)}


def write_plan(family: str, kind: str, insert: int | None, remove: int | None) -> int:
    main = current(FAMILIES[family][0])
    caps = captions(read(main)[0])[kind]
    top = max((n for n, _, _ in caps), default=0)
    if insert is not None:
        rows, what = [(n, n + 1) for n in range(insert, top + 1)], f"insert-{insert}"
    else:
        rows, what = [(n, n - 1) for n in range(remove + 1, top + 1)], f"remove-{remove}"
    out = REPO / "tools" / f"renumber_plan_{family}_{kind}_{datetime.date.today():%Y-%m-%d}.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["kind", "old", "new", "reason"])
        for o, n in rows:
            w.writerow([kind, o, n, f"{family} {what} ({main.name})"])
    rel = out.relative_to(REPO)
    print(f"  wrote {rel}: {len(rows)} {kind} move(s), {what}, {main.name}")
    print(f"  next: python3 tools/repoint_refs.py --scope {family} --kind {kind} --plan {rel} --dry-run")
    return 0


def selftest() -> int:
    t = ("\nFigure 1. Site map.\nSee Figure 2 and Figures 1–2, Table 1, (Hollingham, 2026c, Figure 9), "
         "script figure 21-01, figure 17_wtf_03.\nFigure 2. Hydrographs.\nTable 1. Coefficients.\n")
    caps = captions(t)
    refs, ext = references(t, {p for k in KINDS for _, _, p in caps[k]})
    ok = ([n for n, _, _ in caps["figure"]] == [1, 2] and sorted(refs["figure"]) == [1, 2, 2]
          and refs["table"] == [1] and ext == 1)
    print(f"  {'ok  ' if ok else 'FAIL'}  captions {[n for n, _, _ in caps['figure']]} refs {refs} external {ext}")
    print(f"paper_refs selftest: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(FAMILIES))
    ap.add_argument("--snapshot", action="store_true", help="re-pin caption meanings")
    ap.add_argument("--plan", choices=sorted(FAMILIES), help="write a renumber plan for this family")
    ap.add_argument("--kind", choices=KINDS, default="figure")
    ap.add_argument("--insert", type=int)
    ap.add_argument("--remove", type=int)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.plan:
        if (a.insert is None) == (a.remove is None):
            ap.error("--plan needs exactly one of --insert N or --remove N")
        return write_plan(a.plan, a.kind, a.insert, a.remove)
    snap = {} if a.snapshot else load_snapshot()
    fams = [a.family] if a.family else list(FAMILIES)
    # 1.0.1: a checkout with NO paper document at all (the public clone: the ODTs live in Drive, by
    # design) cannot answer, and says so as SKIP rather than as a FAIL that reads like a project fault.
    # One missing family where others are present is still a FAIL.
    if not a.snapshot and all(current(FAMILIES[f][0]) is None for f in fams):
        print("paper_refs: SKIP (no paper document in this checkout; the ODTs are not in the public repo)")
        return 0
    bad, pins = 0, []
    for fam in fams:
        b, p = check(fam, snap, verbose=not a.quiet)
        bad += b
        pins += p
    if a.snapshot:
        keep = [r for r in load_snapshot().items() if a.family and r[0][0] != a.family]
        with SNAPSHOT.open("w", newline="", encoding="utf8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["family", "kind", "number", "title"])
            for (f, k, n), t in keep:
                w.writerow([f, k, n, t])
            for f, k, n, t in pins:
                w.writerow([f, k, n, t])
        print(f"  pinned {len(pins)} caption(s) to {SNAPSHOT.relative_to(REPO)}")
    print(f"paper_refs: {'OK' if not bad else f'FAIL ({bad})'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
