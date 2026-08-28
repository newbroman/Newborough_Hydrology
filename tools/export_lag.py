#!/usr/bin/env python3
"""
export_lag.py — which published PDFs are older than the documents they came from.

WHY
    A PDF is a derived artefact with no link back to its source, so it goes stale
    silently. That is not only untidy — `tools/figref_lint.py` PARSES the
    exported PDF, because it is the only artefact where captions and in-text
    references both carry resolved numbers. On 2026-08-23 report.pdf was dated
    06:51 while four of its source documents had been edited after it, so the
    figure lint was checking a document that no longer existed and reporting it
    clean. A check that reads a stale artefact does not fail; it lies.

    The same shape as the pandoc guard in refresh_mirrors, and the same remedy:
    make the staleness visible, and make the tool that depends on it refuse.

WHERE THE MAPPING COMES FROM
    tools/build_pdfs.sh already carries source-glob -> PDF for every document it
    builds. That array is parsed here rather than copied, so the two cannot drift.

    report.pdf is the exception build_pdfs.sh names itself: report.odm is a master
    document and is exported by hand. Its sources are the master AND all ten
    linked sub-documents, since editing any chapter changes the assembled PDF.
    That is the pairing this project actually gets wrong, so it is stated
    explicitly below.

THE SECOND LAG
    A PDF can be current against its ODT and still be a version behind on the
    live site, because publishing is a separate manual act. On 2026-08-28
    gh-pages was built at 01:46 and both report.pdf and the Methods Supplement
    PDF were re-exported after it — every link resolved, every file present, and
    two of them were the previous export. `publish_pages` checks that the
    published set is COMPLETE; nothing checked that it was CURRENT.

    check_pages_lag() answers that by content, not by time: each published file's
    working-tree blob hash against the blob recorded in the gh-pages tree. Hashes
    do not care about mtimes, so it is as true after a clone as before one.

EXIT
    0   always, by default — this is advisory. A PDF export is slow and manual,
        and a gate that fires between every ODT edit and the next export would be
        switched off inside a week, which is the reasoning check_all already
        applies to pipeline_lint's literal check.
    --strict makes it gate, for use before a release.
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-08-28

import argparse
import pathlib
import re
import subprocess
import sys
from doc_paths import MASTER_ODM, ODT_GLOB

REPO = pathlib.Path(__file__).resolve().parent.parent
BUILD_PDFS = REPO / "tools/build_pdfs.sh"

# The hand-exported master, which build_pdfs.sh deliberately does not build.
MASTER = ("docs/report/report.pdf",
          [str(MASTER_ODM.relative_to(REPO)), ODT_GLOB])

# build_pdfs.sh already records which ODT VERSION each PDF was built from, which
# is a better signal than a modification time and the reason this tool reads it.
#
# git does not preserve mtimes. A clone or a checkout stamps every file with the
# checkout time, so on a fresh clone "the ODT is newer than the PDF" means
# nothing at all, and after a pull it can be true of a PDF that is perfectly
# current. A recorded source VERSION survives all of that: v1_9_42 against a live
# v1_9_43 is a fact about content, not about when a file happened to be written.
#
# mtime is still the only signal available for unversioned sources (the public
# summaries, the web-tools notes) and for the hand-exported master, and those are
# labelled as such rather than presented with the same confidence.
MANIFEST = REPO / "docs/PDF_MANIFEST.txt"

# Published PDFs with no ODT source, authored directly. Listed rather than left
# silent: an unexplained gap in a check is indistinguishable from an oversight,
# and this tool exists because an unmapped PDF went two months unnoticed.
NO_SOURCE = {
    "docs/Glossaries/Dune_Hydrology_Glossary.pdf",
    "docs/Glossaries/Geirfa_Hydroleg_Twyni.pdf",
    "docs/Glossaries/Slownik_Hydrologii_Wydm.pdf",
}


def manifest() -> dict:
    """{pdf path: source basename recorded at build time}."""
    out = {}
    if not MANIFEST.exists():
        return out
    for line in MANIFEST.read_text(encoding="utf8").splitlines():
        if line.startswith("#") or "<-" not in line:
            continue
        pdf, rest = line.split("<-", 1)
        out[pdf.strip()] = rest.split("|")[0].strip()
    return out

_PAIR = re.compile(r'^\s*"([^"|]+)\|([^"|]+)"\s*$')


def pairs() -> list[tuple[str, list[str]]]:
    """[(pdf, [source globs])] — build_pdfs.sh's array, plus the master."""
    out: list[tuple[str, list[str]]] = []
    if BUILD_PDFS.exists():
        for line in BUILD_PDFS.read_text(encoding="utf8").splitlines():
            m = _PAIR.match(line)
            if m:
                out.append((m.group(2), [m.group(1)]))
    out.append(MASTER)
    return out


_VER = re.compile(r"_v(\d+(?:[._]\d+)*)")


def _version_key(p: pathlib.Path):
    m = _VER.search(p.name)
    return [int(n) for n in re.split(r"[._]", m.group(1))] if m else [-1]


def _newest(globs: list[str]) -> list[pathlib.Path]:
    """The sources that actually matter for a PDF.

    A VERSIONED glob (one containing "_v") names a family whose live member is
    the highest version — comparing a PDF against v2..v10 individually says
    nothing, since the older ones are history. An unversioned glob names every
    file it matches, which is what the hand-exported master needs: report.pdf
    depends on the master AND all ten linked sub-documents, because editing any
    chapter changes the assembled export.
    """
    found: list[pathlib.Path] = []
    for g in globs:
        matches = sorted(REPO.glob(g))
        if not matches:
            continue
        found += [max(matches, key=_version_key)] if "_v" in g else matches
    return found


def run(strict: bool, only: str | None = None) -> int:
    print("=" * 78)
    print("EXPORT LAG — is each published PDF newer than its sources?")
    print("=" * 78)
    lagging = 0
    stale: list[str] = []
    man = manifest()
    for pdf_rel, globs in pairs():
        pdf = REPO / pdf_rel
        srcs = _newest(globs)
        if not srcs:
            continue
        if not pdf.exists():
            stale.append(pdf_rel)
            print(f"\n  MISSING  {pdf_rel} has never been built")
            lagging += 1
            continue
        # Version drift first: the strong signal, and immune to git's mtimes.
        recorded = man.get(pdf_rel)
        live = max(srcs, key=_version_key)
        if recorded and "_v" in live.name:
            if recorded != live.name:
                lagging += 1
                stale.append(pdf_rel)
                print(f"\n  STALE    {pdf_rel}")
                print(f"           built from {recorded}")
                print(f"           live source is {live.name}")
                continue
            print(f"  current  {pdf_rel}  <-  {recorded}")
            continue
        if recorded is None and any("_v" in g for g in globs):
            lagging += 1
            stale.append(pdf_rel)
            print(f"\n  UNBUILT  {pdf_rel}")
            print(f"           no line in {MANIFEST.relative_to(REPO)} — "
                  f"build_pdfs.sh has never built it")
            print(f"           live source is {live.name}")
            continue

        # Unversioned sources, and the hand-exported master: mtime is all there is.
        pt = pdf.stat().st_mtime
        ahead = [s for s in srcs if s.stat().st_mtime > pt]
        if ahead:
            lagging += 1
            stale.append(pdf_rel)
            print(f"\n  STALE?   {pdf_rel}   (by modification time only — "
                  f"unreliable after a git checkout)")
            print(f"           {len(ahead)} source(s) modified since it was built:")
            for s in sorted(ahead, key=lambda x: -x.stat().st_mtime):
                print(f"             {s.relative_to(REPO)}")
    # A PDF with no mapping is never checked by anything, which is the same
    # false assurance this tool exists to remove. Paper 2's published PDF sat two
    # months and eight versions behind its ODT precisely because build_pdfs.sh
    # had no pairing for it, so nothing — including the first version of this
    # check — ever looked.
    mapped = {(REPO / pdf).resolve() for pdf, _ in pairs()}
    unmapped = sorted(
        q for q in REPO.glob("docs/**/*.pdf")
        if q.resolve() not in mapped
        and not any(part.startswith("_") for part in q.relative_to(REPO).parts)
        and str(q.relative_to(REPO)) not in NO_SOURCE
    )
    if NO_SOURCE:
        print(f"\n  NO SOURCE — {len(NO_SOURCE)} PDF(s) declared as authored "
              f"directly, with no ODT to rebuild from:")
        for q in sorted(NO_SOURCE):
            print(f"             {q}")

    if unmapped:
        print(f"\n  UNMAPPED — {len(unmapped)} published PDF(s) with no source "
              f"pairing in tools/build_pdfs.sh.")
        print("           Nothing rebuilds or checks these. Either add a pairing "
              "or confirm the")
        print("           PDF is authored directly and has no ODT source.")
        for q in unmapped:
            print(f"             {q.relative_to(REPO)}")

    print()
    if lagging:
        print(f"  {lagging} published PDF(s) behind their sources.")
        print("  Rebuild the buildable ones with tools/build_pdfs.sh.")
        # Only say this when it is TRUE of report.pdf. It used to print
        # unconditionally, which put the string "report.pdf" into the output of
        # every run — and figref_lint's guard matched on that substring, so it
        # refused to lint a perfectly current report.pdf because Paper 2 was
        # unbuilt. A filename appearing in a sentence is not a verdict.
        if MASTER[0] in stale:
            print(f"  {MASTER[0]} is exported by hand from report.odm "
                  f"(File > Export as PDF);")
            print("  until then tools/figref_lint.py is reading a document "
                  "that no longer")
            print("  exists and would report it clean.")
    else:
        print("  every published PDF is at least as new as its sources.")

    # --pdf asks about ONE artefact and is answered by its exit code alone.
    if only is not None:
        return 1 if only in stale else 0
    return 1 if (lagging and strict) else 0


# --- the published site ------------------------------------------------------
# The published set is derived from index.html exactly as working/nrg_git.sh
# derives it, and for the same reason: a list of what to publish and a list of
# what the page links to are the same list. Two lists that must agree are a
# defect waiting for a quiet afternoon, so this reads the page rather than
# repeating the answer.
PAGES_ROOT = ["index.html", "scenario_viewer.html",
              "seasonal_extremes_scatter.html"]
PAGES_BRANCH = "gh-pages"
_SITE = "https://newbroman.github.io/Newborough_Hydrology/"
_HREF = re.compile(r'href="([^"]+)"')


def _git(*args: str) -> tuple[int, str]:
    """git, read-only. --no-optional-locks: the bridge mount cannot unlink, so a
    command that takes the index lock leaves one behind that nothing can clear."""
    r = subprocess.run(["git", "--no-optional-locks", *args],
                       cwd=REPO, capture_output=True, text=True)
    return r.returncode, r.stdout


def pages_links() -> list[str]:
    """Every site-local href in index.html, absolute ones reduced to their path."""
    idx = REPO / "index.html"
    if not idx.exists():
        return []
    out = set()
    for h in _HREF.findall(idx.read_text(encoding="utf8", errors="replace")):
        h = h.removeprefix(_SITE)
        if h.startswith(("#", "http:", "https:", "mailto:")):
            continue
        out.add(h)
    return sorted(out)


def check_pages_lag(strict: bool) -> int:
    """Is what is PUBLISHED the same content as what is built?

    Returns the number of published files behind the working tree.
    """
    print()
    print("=" * 78)
    print("PAGES LAG — is the published site the same content as the working tree?")
    print("=" * 78)

    rc, _ = _git("rev-parse", "-q", "--verify", f"refs/heads/{PAGES_BRANCH}")
    if rc != 0:
        # Silence here would read as "nothing to report", which is the exact
        # failure this file exists to remove.
        print(f"  no {PAGES_BRANCH} branch in this clone — nothing has been "
              f"published from here.")
        print("  (nrg_git.sh option 13 builds and pushes it.)")
        return 0

    rc, out = _git("ls-tree", "-r", PAGES_BRANCH)
    if rc != 0:
        print(f"  could not read the {PAGES_BRANCH} tree.")
        return 0
    published: dict[str, str] = {}
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob":
            published[path] = parts[2]

    wanted = sorted(set(PAGES_ROOT) | set(pages_links()))
    behind: list[str] = []
    absent: list[str] = []
    untracked: list[str] = []

    for rel in wanted:
        local = REPO / rel
        if not local.exists():
            # publish_pages refuses this case outright; here it is only noted,
            # because the fix is to the page, not to the publish.
            untracked.append(rel)
            continue
        rc, h = _git("hash-object", "--", rel)
        if rc != 0:
            continue
        h = h.strip()
        if rel not in published:
            absent.append(rel)
        elif published[rel] != h:
            behind.append(rel)

    for rel in behind:
        print(f"\n  BEHIND   {rel}")
        print(f"           published {published[rel][:8]}, built "
              f"{_git('hash-object', '--', rel)[1].strip()[:8]}")
    for rel in absent:
        print(f"\n  ABSENT   {rel} is linked from index.html but is not on "
              f"{PAGES_BRANCH}")
    for rel in untracked:
        print(f"\n  MISSING  {rel} is linked from index.html but is not in the "
              f"working tree")

    # A file published from a tree that no longer names it is a 404 waiting for
    # a visitor, and the reverse of everything above.
    orphan = sorted(k for k in published
                    if k not in set(wanted) and k != ".nojekyll")
    if orphan:
        print(f"\n  ORPHAN — {len(orphan)} file(s) published but no longer "
              f"linked from index.html:")
        for k in orphan:
            print(f"             {k}")

    n = len(behind) + len(absent)
    print()
    if n:
        print(f"  {n} published file(s) are not the ones you built.")
        print("  Republish with nrg_git.sh option 13.")
    elif untracked:
        print("  the published files match, but index.html links "
              f"{len(untracked)} file(s) that do not exist.")
    else:
        print(f"  the published site matches the working tree "
              f"({len(wanted)} file(s)).")
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero when anything lags (for a release check)")
    ap.add_argument("--pdf", metavar="PATH", default=None,
                    help="exit non-zero only if THIS pdf is stale; ignore the rest")
    ap.add_argument("--pages", action="store_true",
                    help="only the gh-pages check; skip the PDF/ODT comparison")
    ap.add_argument("--no-pages", action="store_true",
                    help="skip the gh-pages check")
    a = ap.parse_args()
    only = a.pdf
    if only:
        try:
            only = str(pathlib.Path(only).resolve().relative_to(REPO))
        except ValueError:
            only = a.pdf

    # --pdf asks one question and is answered by its exit code, so the pages
    # section would only add noise to it.
    if a.pages:
        return 1 if (check_pages_lag(a.strict) and a.strict) else 0
    rc = run(a.strict, only)
    if only is None and not a.no_pages:
        if check_pages_lag(a.strict) and a.strict:
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
