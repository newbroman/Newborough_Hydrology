#!/usr/bin/env python3
"""
docglob_lint.py
================
Every document is in the drift net.

Why this exists.

  The drift net — cite_check.py and audit_number_drift.py — reads two routes
  into the corpus: `tools/doc_globs.py` DOC_GLOBS sweeps text documents in
  place (index.html, the repo markdown, the ledgers, the decision log), and
  `tools/refresh_mirrors.py` SOURCES turns every ODT family into a markdown
  mirror that DOC_GLOBS then sweeps. A document reachable by NEITHER route is
  invisible to both, and the gap has appeared three times: Paper 2 sat outside
  the net for months because the mirror glob said `Paper2_v*.odt` and the
  files were `Hollingham_2026_Paper2_amended*.odt`; `build_pdfs.sh` was
  pinned to `_v1_*`; `repoint_refs.py` omitted report13-16. Each time, the
  document existed, was edited, and nothing downstream ever compared it
  against the pipeline.

  This lint reuses refresh_mirrors.SOURCES and refresh_mirrors.resolve()
  directly rather than restating the family list — a second copy of that
  list is the same drift one directory along (doc_globs.py's own opening
  argument). It reuses doc_globs.DOC_GLOBS the same way.

What it flags.

  (a) ODT coverage. Every `*.odt` under `docs/` and `report_edits/odt/`
      (excluding anything under a directory literally named `archive`,
      `_to_delete`, `media_store` or `scratch`, and excluding filenames that
      look like a stripped/temporary copy) must be matched by at least one
      `refresh_mirrors.SOURCES` glob pattern, and the mirror `resolve()`
      would write for it must exist on disk. A source outside every pattern
      is the Paper 2 shape of bug; a source inside a pattern but with no
      mirror written is a regeneration that never happened.

  (b) Mirror coverage. Every mirror path `refresh_mirrors.resolve()` would
      write, given the ODT sources present, must be matched by at least one
      `tools/doc_globs.py` DOC_GLOBS pattern. A mirror outside DOC_GLOBS is
      written but never read by cite_check or audit_number_drift. (This is
      deliberately the resolve()-exact set, not every `.md` already committed
      under the two mirror roots: `report_edits/text/style_donor.md` is real
      and committed but is not a refresh_mirrors output — no ODT source
      matches any SOURCES pattern for it, because it is a LibreOffice
      style-loading source, not report prose — so it is outside this check's
      business, and sweeping it in reports a "gap" that was never a drift-net
      gap.)

  (c) Version currency. For a versioned family (Methods Supplement,
      Supplementary Material, the Papers, academic summaries), the mirror's
      own header stamp — `<!-- GENERATED MIRROR of <path> ... -->`, written
      by refresh_mirrors.convert() — must name the file that is CURRENTLY the
      highest version present on disk, compared numerically
      (refresh_mirrors._version_key), never lexicographically. This is the
      failure mode `refresh_mirrors.py`'s own docstring names: `ls | tail`
      sorts `v1_9` after `v1_18`. A mirror that still names the previous
      version has not been regenerated since the last version bump, which is
      a real staleness signal independent of refresh_mirrors --check's
      content-hash comparison (that catches an edited, unregenerated ODT;
      this catches a NEW file that superseded the one the mirror was last
      written from).

Allowlist.

  tools/docglob_allow.csv: path, reason. A row admits one ODT (by
  repo-relative path) that is legitimately outside the net — e.g. a style
  template that is not itself a cited document. Adding a row to quiet a real
  gap is the failure this file exists to prevent; a row that no longer
  matches an existing off-net ODT is reported as stale. The real tree this
  lint was built against needed none — every ODT present resolves cleanly —
  so the file is not shipped; create it only if the tree changes and a
  genuine exception appears, and name it in the run output rather than
  silently excusing it.

Usage:
    python3 tools/docglob_lint.py            # report, non-zero exit on a fault
    python3 tools/docglob_lint.py --quiet    # one line unless something fails
    python3 tools/docglob_lint.py --selftest
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-21. First gate for "every
#   document is in the drift net" — reuses refresh_mirrors.SOURCES/resolve()
#   and doc_globs.DOC_GLOBS rather than restating either list.

REPO = Path(__file__).resolve().parents[1]
ALLOW = REPO / "tools" / "docglob_allow.csv"

EXCLUDE_DIR_NAMES = {"archive", "_to_delete", "media_store", "scratch"}
STRIPPED_RE = re.compile(r"(?i)_stripped\b|^~\$")

SRC_STAMP_RE = re.compile(r"GENERATED MIRROR of (\S+)")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doc_globs  # noqa: E402 — the canonical DOC_GLOBS list; pure constant,
#   no import-time side effects (its own docstring's argument for existing).

# refresh_mirrors is the canonical SOURCES/resolve(); importing it runs a
# `pandoc --version` read at module load (its own PANDOC_VERSION) but touches
# nothing on disk. If pandoc is entirely unavailable that read raises at
# IMPORT time, before main() runs — caught here so the lint reports a fault
# instead of a bare traceback.
try:
    import refresh_mirrors as rm  # noqa: E402
    _IMPORT_ERROR: Exception | None = None
except Exception as _e:  # noqa: E402
    rm = None  # type: ignore[assignment]
    _IMPORT_ERROR = _e


# ── pure helpers (unit-tested by selftest against synthetic trees) ─────────

def _excluded_by_dir(rel_parts: tuple[str, ...]) -> bool:
    return any(part in EXCLUDE_DIR_NAMES for part in rel_parts)


def find_odts(repo: Path, roots: list[str]) -> list[Path]:
    """*.odt under any of `roots`, skipping excluded directories and
    stripped/temporary copies. Sorted for stable output."""
    out = []
    for root in roots:
        base = repo / root
        if not base.exists():
            continue
        for p in base.rglob("*.odt"):
            rel = p.relative_to(repo)
            if _excluded_by_dir(rel.parts[:-1]):
                continue
            if STRIPPED_RE.search(p.name):
                continue
            out.append(p)
    return sorted(set(out))


def check_odt_coverage(odt_files: list[Path], repo: Path, sources) -> list[tuple[str, str]]:
    """(a): every odt matched by at least one SOURCES pattern."""
    matched: set[Path] = set()
    for pattern, _mirror_dir, _versioned in sources:
        matched.update(repo.glob(pattern))
    faults = []
    for f in odt_files:
        if f not in matched:
            faults.append((
                str(f.relative_to(repo)),
                "not matched by any refresh_mirrors.SOURCES pattern — outside every mirror family",
            ))
    return faults


def check_mirrors_present(jobs: list[tuple[Path, Path]], repo: Path) -> list[tuple[str, str]]:
    """(a), continued: every job resolve() would run has its mirror on disk."""
    faults = []
    for src, dst in jobs:
        if not dst.exists():
            faults.append((
                str(dst.relative_to(repo)),
                f"mirror missing for {src.relative_to(repo)} — refresh_mirrors.py has not been run for it",
            ))
    return faults


def check_docglob_coverage(mirror_paths: list[Path], repo: Path, doc_globs_list) -> list[tuple[str, str]]:
    """(b): every mirror path matched by at least one DOC_GLOBS pattern."""
    matched: set[Path] = set()
    for g in doc_globs_list:
        matched.update(repo.glob(g))
    faults = []
    for m in sorted(set(mirror_paths)):
        if m not in matched:
            faults.append((
                str(m.relative_to(repo)),
                "not matched by any DOC_GLOBS pattern (tools/doc_globs.py) — invisible to cite_check / audit_number_drift",
            ))
    return faults


def check_version_stamp(mirror_path: Path, versioned_matches: list[Path], repo: Path,
                         version_key_fn) -> tuple[str, str] | None:
    """(c): the mirror's header names the numerically-highest version present."""
    if not versioned_matches or not mirror_path.exists():
        return None
    highest = max(versioned_matches, key=version_key_fn)
    with mirror_path.open("r", encoding="utf8", errors="replace") as fh:
        head = fh.readline() + fh.readline()
    m = SRC_STAMP_RE.search(head)
    if not m:
        return None  # no stamp at all — legacy mirror, not this check's business
    named = Path(m.group(1)).name
    if named != highest.name:
        return (
            str(mirror_path.relative_to(repo)),
            f"mirror header names {named} but the highest version present (numeric compare) "
            f"is {highest.name} — regenerate with refresh_mirrors.py",
        )
    return None


# ── allowlist ────────────────────────────────────────────────────────────

def _allow() -> list[dict]:
    if not ALLOW.exists():
        return []
    with ALLOW.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r.get("path")]


# ── the real run ─────────────────────────────────────────────────────────

def scan(repo: Path = REPO):
    """Return (faults_a, faults_b, faults_c, stale_allow) against the real tree."""
    allow_rows = _allow()
    used = [False] * len(allow_rows)

    def _apply_allow(faults):
        kept = []
        for path, reason in faults:
            hit = None
            for i, row in enumerate(allow_rows):
                if row["path"] == path and not used[i]:
                    hit = i
                    break
            if hit is not None:
                used[hit] = True
            else:
                kept.append((path, reason))
        return kept

    odt_files = find_odts(repo, ["docs", "report_edits/odt"])
    faults_a = check_odt_coverage(odt_files, repo, rm.SOURCES)
    jobs = rm.resolve()
    faults_a += check_mirrors_present(jobs, repo)
    faults_a = _apply_allow(faults_a)

    # (b): exactly the mirrors refresh_mirrors.resolve() would write given the
    # sources present right now. Deliberately NOT every .md already committed
    # under the two mirror roots: report_edits/text/style_donor.md is real and
    # committed but is not a refresh_mirrors output at all (no ODT source
    # matches any SOURCES pattern for it — it is a LibreOffice style-loading
    # source, not report prose), so it is not this check's business; sweeping
    # it in produced a false "gap" that was never a drift-net gap.
    mirror_paths = {dst for _src, dst in jobs}
    faults_b = check_docglob_coverage(sorted(mirror_paths), repo, doc_globs.DOC_GLOBS)

    faults_c = []
    for pattern, mirror_dir, versioned in rm.SOURCES:
        if not versioned:
            continue
        matches = sorted(repo.glob(pattern))
        if not matches:
            continue
        highest = max(matches, key=rm._version_key)
        stem = rm._stem_without_version(highest)
        mirror_path = repo / mirror_dir / f"{stem}.md"
        fault = check_version_stamp(mirror_path, matches, repo, rm._version_key)
        if fault:
            faults_c.append(fault)

    stale = [r for r, u in zip(allow_rows, used) if not u]
    return faults_a, faults_b, faults_c, stale, len(odt_files), len(mirror_paths)


# ── selftest: pure logic against a synthetic temp tree, no pandoc needed ──

def selftest() -> bool:
    import tempfile
    if _IMPORT_ERROR is not None:
        print(f"  selftest FAIL: refresh_mirrors did not import (pandoc unavailable?): {_IMPORT_ERROR!r}")
        return False
    ok = True
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "report_edits" / "odt").mkdir(parents=True)
        (repo / "report_edits" / "text").mkdir(parents=True)
        (repo / "docs" / "paper" / "text").mkdir(parents=True)
        (repo / "archive").mkdir(parents=True)

        # covered, non-versioned, mirror present
        (repo / "report_edits" / "odt" / "report7.odt").write_bytes(b"x")
        (repo / "report_edits" / "text" / "report7.md").write_text(
            "<!-- GENERATED MIRROR of report_edits/odt/report7.odt -->\n", encoding="utf8")

        # covered, non-versioned, mirror MISSING
        (repo / "report_edits" / "odt" / "report8.odt").write_bytes(b"x")

        # NOT covered by any pattern
        (repo / "docs" / "paper" / "orphan.odt").write_bytes(b"x")

        # excluded by directory name — must not be flagged at all
        (repo / "archive" / "old.odt").write_bytes(b"x")

        sources = [
            ("report_edits/odt/report*.odt", "report_edits/text", False),
            ("docs/paper/Paper_v*.odt", "docs/paper/text", True),
        ]

        odt_files = find_odts(repo, ["docs", "report_edits/odt"])
        assert repo / "archive" / "old.odt" not in odt_files, "archive/ not excluded"
        faults_a = check_odt_coverage(odt_files, repo, sources)
        names_a = {f[0] for f in faults_a}
        if "docs/paper/orphan.odt" not in names_a:
            print("  selftest FAIL: orphan.odt not flagged"); ok = False
        if "report_edits/odt/report7.odt" in names_a or "report_edits/odt/report8.odt" in names_a:
            print("  selftest FAIL: covered odt flagged as uncovered"); ok = False

        jobs = [
            (repo / "report_edits/odt/report7.odt", repo / "report_edits/text/report7.md"),
            (repo / "report_edits/odt/report8.odt", repo / "report_edits/text/report8.md"),
        ]
        faults_missing = check_mirrors_present(jobs, repo)
        if len(faults_missing) != 1 or "report8.md" not in faults_missing[0][0]:
            print(f"  selftest FAIL: expected exactly one missing-mirror fault, got {faults_missing}")
            ok = False

        # (b) docglob coverage
        doc_globs_list = ["report_edits/text/report*.md"]
        mirror_paths = [repo / "report_edits/text/report7.md",
                         repo / "docs/paper/text/Paper.md"]  # second not on a swept glob
        (repo / "docs/paper/text/Paper.md").write_text("x", encoding="utf8")
        faults_b = check_docglob_coverage(mirror_paths, repo, doc_globs_list)
        if len(faults_b) != 1 or "Paper.md" not in faults_b[0][0]:
            print(f"  selftest FAIL: expected Paper.md flagged uncovered, got {faults_b}")
            ok = False

        # (c) version stamp — numeric, not lexicographic
        (repo / "docs" / "paper" / "Paper_v1_9.odt").write_bytes(b"x")
        (repo / "docs" / "paper" / "Paper_v1_18.odt").write_bytes(b"x")  # numerically higher
        mirror = repo / "docs" / "paper" / "text" / "Paper.md"
        mirror.write_text("<!-- GENERATED MIRROR of docs/paper/Paper_v1_9.odt -->\n", encoding="utf8")
        matches = [repo / "docs" / "paper" / "Paper_v1_9.odt", repo / "docs" / "paper" / "Paper_v1_18.odt"]
        fault_c = check_version_stamp(mirror, matches, repo, rm._version_key)
        if fault_c is None or "Paper_v1_18" not in fault_c[1]:
            print(f"  selftest FAIL: expected a stale-version fault naming v1_18, got {fault_c}")
            ok = False
        # regenerate against the true highest — must now pass
        mirror.write_text("<!-- GENERATED MIRROR of docs/paper/Paper_v1_18.odt -->\n", encoding="utf8")
        fault_c2 = check_version_stamp(mirror, matches, repo, rm._version_key)
        if fault_c2 is not None:
            print(f"  selftest FAIL: expected no fault once header names the true highest, got {fault_c2}")
            ok = False

    return ok


def main(argv) -> int:
    quiet = "--quiet" in argv
    if "--selftest" in argv:
        ok = selftest()
        print("  docglob_lint selftest: " + ("OK" if ok else "FAIL"))
        return 0 if ok else 1

    if _IMPORT_ERROR is not None:
        print(f"  FAIL cannot import refresh_mirrors.py (pandoc unavailable?): {_IMPORT_ERROR!r}")
        return 1
    try:
        faults_a, faults_b, faults_c, stale, n_odt, n_mirrors = scan()
    except Exception as e:  # any other fault mid-scan
        print(f"  FAIL cannot evaluate docglob_lint: {e!r}")
        return 1

    rc = 0
    for path, reason in faults_a:
        print(f"  FAIL (a) {path}: {reason}")
        rc = 1
    for path, reason in faults_b:
        print(f"  FAIL (b) {path}: {reason}")
        rc = 1
    for path, reason in faults_c:
        print(f"  FAIL (c) {path}: {reason}")
        rc = 1
    for row in stale:
        print(f"  FAIL docglob_allow.csv row matches nothing: {row['path']!r}")
        rc = 1

    n_faults = len(faults_a) + len(faults_b) + len(faults_c) + len(stale)
    if rc:
        print(f"  docglob_lint: {len(faults_a)} ODT-coverage fault(s), {len(faults_b)} "
              f"DOC_GLOBS-coverage fault(s), {len(faults_c)} stale version-stamp fault(s), "
              f"{len(stale)} stale allowlist row(s)")
    elif not quiet:
        print(f"  docglob_lint: {n_odt} ODT(s) covered and mirrored, {n_mirrors} mirror(s) "
              f"swept by DOC_GLOBS, every versioned family's mirror names its current "
              f"highest version")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
