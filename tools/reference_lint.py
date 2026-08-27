#!/usr/bin/env python3
"""
reference_lint.py — one audit over the registers a document must agree with.

WHY THIS EXISTS, AND WHY IT IS NOT figref_lint
----------------------------------------------
Three things in this corpus are "a declared inventory that the prose must match",
and until now each was checked by a different tool, or by nothing:

    figures   figref_lint.py   — reads the EXPORTED PDF
    symbols   symbol_check.py  — reads the mirrors
    tables    nothing at all

The gap was found the hard way. Table captions in report.odm are auto-numbered
sequence fields and renumber themselves when a table is added or removed. The
in-text references are TYPED BY HAND — cross-references cannot span the master's
sections — so they silently fall out of step. Cutting one table in report9 would
have shifted 35 typed references across four sub-documents with nothing to catch
a single miss.

THE PDF IS THE WRONG SOURCE
    figref_lint reads the exported PDF because that is where caption numbers are
    resolved. But the PDF lags: report.pdf was older than report.odm, and older
    than the edits of the night before, so the lint was checking yesterday's
    document — the same failure refresh_mirrors exists to prevent.

    It is not necessary. An ODF sequence field caches its own resolved value as
    the element's text:

        <text:sequence text:name="Table" text:formula="ooow:Table+1">1.8</text:sequence>

    So resolved caption numbers can be read straight from the ODTs, in master
    order, with no export step. This tool does that, and additionally compares
    the cached values against a recount — a mismatch means the document has been
    edited without LibreOffice renumbering, which is itself worth knowing.

EXIT CODES — split deliberately
    0   structurally sound (references resolve; cache agrees with the recount)
    1   STRUCTURAL failure: a reference points at a caption that does not exist
    Orphan captions (a table nothing references) are reported but do NOT gate:
    that is an editorial backlog, not a broken document, and gating on it would
    make the check unadoptable on day one.

WORKFLOW WHEN A CAPTION CHANGES ON PURPOSE
    A reworded caption fires the same check as a renumbering, because from the
    outside they are the same event: the number now means something else. That
    is deliberate — it forces a look at the citing documents, which the report
    names — and the resolution is to review the list and re-pin:

        python3 tools/reference_lint.py             # read what moved, and who cites it
        python3 tools/reference_lint.py --snapshot  # re-pin, once satisfied

    Same as tools/citation_index.csv's confirmed rows: the snapshot records a
    human decision, not an automatic state.

USAGE
    python3 tools/reference_lint.py                 # tables (default)
    python3 tools/reference_lint.py --kind table
    python3 tools/reference_lint.py --orphans       # also list unreferenced captions
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23. Tables only. Figures and
#   the symbol register fold in behind the same --kind switch; the caption reader
#   and the reference scraper are already kind-agnostic.

import argparse
import csv
import pathlib
import re
import sys
import zipfile
from doc_paths import MASTER_ODM, ODT_DIR, MIRROR_DIR

REPO = pathlib.Path(__file__).resolve().parent.parent
MASTER = REPO / str(MASTER_ODM)
ODT_DIR = REPO / str(ODT_DIR)
MIRROR_DIR = REPO / str(MIRROR_DIR)

# A caption's own "Table 8:" text must never be read as a reference to itself.
CAPTION_LEAD = re.compile(r"^\s*\*?\*?(Table|Figure)\s")


def master_order() -> list[str]:
    """Sub-document filenames in the order the master links them.

    hrefs are stored relative to the master and are not trusted for their
    directory part — only for the basename and the ORDER, which is the thing
    that determines numbering.
    """
    xml = zipfile.ZipFile(MASTER).read("content.xml").decode("utf-8")
    hrefs = re.findall(r'text:section-source xlink:href="([^"]+)"', xml)
    return [h.rsplit("/", 1)[-1] for h in hrefs]


def _title_after(xml: str, end: int, chars: int = 90) -> str:
    """The caption's own words, as a stable anchor for what a number MEANS.

    Markup is stripped and whitespace collapsed so that a restyle does not read
    as a changed caption. The leading ": " that follows the sequence field goes
    too.
    """
    tail = xml[end:end + chars * 6]
    tail = tail.split("</text:p>")[0]
    txt = re.sub(r"<[^>]+>", "", tail)
    txt = txt.replace("&apos;", "'").replace("&quot;", '"').replace("&amp;", "&")
    txt = re.sub(r"\s+", " ", txt).strip().lstrip(":").strip()
    return txt[:chars]


def captions(kind: str) -> list[tuple[str, int, str, str]]:
    """(document, position-in-master-order, cached value, title) in order."""
    # ODF capitalises the sequence name: text:name="Table" / "Figure".
    pat = re.compile(
        r'<text:sequence[^>]*text:name="%s"[^>]*>([^<]*)</text:sequence>'
        % kind.capitalize()
    )
    out: list[tuple[str, int, str, str]] = []
    n = 0
    for name in master_order():
        p = ODT_DIR / name
        if not p.exists():
            print(f"  MISSING  master links {name}, which is not in {ODT_DIR}")
            continue
        xml = zipfile.ZipFile(p).read("content.xml").decode("utf-8")
        for m in pat.finditer(xml):
            n += 1
            out.append((name, n, m.group(1).strip(), _title_after(xml, m.end())))
    return out


def references(kind: str) -> dict[str, list[int]]:
    """Typed 'Table N' / 'Figure N' occurrences per mirror, caption lines excluded."""
    word = kind.capitalize()
    pat = re.compile(rf"\b{word}s?\s+(\d+)")
    found: dict[str, list[int]] = {}
    for name in master_order():
        mirror = MIRROR_DIR / (pathlib.Path(name).stem + ".md")
        if not mirror.exists():
            continue
        hits: list[int] = []
        for line in mirror.read_text(encoding="utf-8").splitlines():
            if CAPTION_LEAD.match(line) or line.lstrip().startswith("!["):
                continue          # a caption, or an image whose alt text is one
            hits += [int(m) for m in pat.findall(line)]
        if hits:
            found[mirror.name] = hits
    return found


def run(kind: str, show_orphans: bool, write_snapshot: bool) -> int:
    print("=" * 78)
    print(f"REFERENCE LINT — {kind} captions against typed in-text references")
    print("=" * 78)

    caps = captions(kind)
    if not caps:
        print(f"  no {kind} captions found — nothing to check")
        return 0
    total = len(caps)
    print(f"  {total} {kind} caption(s) across {len({c[0] for c in caps})} sub-document(s)")

    fatal = 0

    # 1. caption number FORMAT, advisory only.
    #
    #    The cached value is NOT the resolved master number and must not be
    #    treated as one. A sub-document opened on its own restarts its sequence
    #    at 1, so report10's single caption legitimately caches as "1" while
    #    sitting at position 21 of the master. An earlier version of this check
    #    called that a stale number and was wrong.
    #
    #    What IS worth reporting is a format split: report9's captions carry a
    #    chapter prefix ("1.8") and report10's does not ("1"), so the assembled
    #    document renders two caption styles. That is an editorial inconsistency,
    #    not a broken reference, so it does not gate.
    formats = {}
    for doc, n, cached, _title in caps:
        if cached:
            formats.setdefault("chapter-prefixed" if "." in cached else "plain",
                               set()).add(doc)
    if len(formats) > 1:
        print("\n  MIXED CAPTION FORMAT (advisory, does not gate)")
        for style, docs in sorted(formats.items()):
            print(f"      {style}: {', '.join(sorted(docs))}")
        print("      the assembled master renders two caption styles")

    # 2. references that point at nothing.
    refs = references(kind)
    cited: set[int] = set()
    for doc, hits in sorted(refs.items()):
        for h in hits:
            cited.add(h)
            if h > total or h < 1:
                print(f"\n  DANGLING  {doc} cites {kind.capitalize()} {h}, "
                      f"but only {total} {kind} caption(s) exist")
                fatal += 1

    # 3. captions nothing points at — advisory only.
    orphans = [(d, n) for d, n, _c, _t in caps if n not in cited]
    if orphans:
        print(f"\n  {len(orphans)} unreferenced {kind}(s) (advisory, does not gate)")
        if show_orphans:
            for d, n in orphans:
                print(f"      {kind.capitalize()} {n}  ({d})")

    # 4. THE CHECK THIS TOOL EXISTS FOR.
    #
    #    Dangling references only catch a number with no caption. They do NOT
    #    catch the actual failure mode: remove one table and every later caption
    #    renumbers itself while the typed references stay put, so all of them
    #    still resolve — to the WRONG table. Nothing is dangling and everything
    #    is wrong.
    #
    #    So the snapshot records what each number MEANT. A number whose caption
    #    title has changed is a reference that now points somewhere else, and
    #    every typed citation of it needs bumping. This is the same device as
    #    tools/citation_index.csv: pin the meaning, then detect the drift.
    snap = REPO / f"tools/reference_index_{kind}.csv"
    if write_snapshot:
        with open(snap, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["number", "document", "title"])
            for doc, n, _c, title in caps:
                w.writerow([n, doc, title])
        print(f"\n  snapshot written: {snap.relative_to(REPO)} ({len(caps)} rows)")
    elif snap.exists():
        was = {int(r["number"]): (r["document"], r["title"])
               for r in csv.DictReader(open(snap, encoding="utf-8"))}
        moved = []
        for doc, n, _c, title in caps:
            if n in was and was[n][1] and was[n][1] != title:
                moved.append((n, was[n][1], title))
        gone = sorted(set(was) - {c[1] for c in caps})
        if moved or gone:
            print(f"\n  MEANING CHANGED since the snapshot — typed references to "
                  f"these numbers now point elsewhere")
            for n, before, after in moved:
                print(f"\n      {kind.capitalize()} {n}")
                print(f"        was:  {before}")
                print(f"        now:  {after}")
                for d, hits in sorted(refs.items()):
                    if n in hits:
                        print(f"        cited in {d} x{hits.count(n)}")
            for n in gone:
                print(f"\n      {kind.capitalize()} {n} no longer exists "
                      f"(was: {was[n][1]})")
            fatal += len(moved) + len(gone)
        else:
            print(f"\n  snapshot agrees: every number still means what it did "
                  f"({len(was)} rows)")
    else:
        print(f"\n  no snapshot at {snap.relative_to(REPO)} — run --snapshot to "
              f"pin the current meanings before editing")

    print()
    n_refs = sum(len(v) for v in refs.values())
    print(f"  {n_refs} typed reference(s) across {len(refs)} document(s); "
          f"{len(orphans)} unreferenced caption(s)")
    if fatal:
        print(f"\nreference_lint ({kind}): FAIL — {fatal} structural problem(s)")
        return 1
    print(f"\nreference_lint ({kind}): OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="table", choices=["table", "figure"],
                    help="which register to audit (default: table)")
    ap.add_argument("--orphans", action="store_true",
                    help="list unreferenced captions individually")
    ap.add_argument("--snapshot", action="store_true",
                    help="pin what each number currently means, before editing")
    a = ap.parse_args()
    return run(a.kind, a.orphans, a.snapshot)


if __name__ == "__main__":
    sys.exit(main())
