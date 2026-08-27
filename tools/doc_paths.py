#!/usr/bin/env python3
"""
doc_paths.py — where the report's editable sources and mirrors live.

WHY THIS EXISTS

  `report_edits/` was spelled 36 times across 15 files. That is not a tidiness
  complaint: it is the reason moving the report's sources was ranked as the one
  restructuring step too expensive to attempt during a submission. A path in
  fifteen places is a refactor; a path in one place is a line.

  It also matters because of WHAT lives there. `report_edits/text/*.md` is the
  markdown mirror of every report chapter — the diffable surface of the whole
  corpus, and the thing `cite_check`, `symbol_check`, `reference_lint`,
  `refresh_mirrors`, `doc_version_sync`, `export_lag`, `figref_lint` and
  `snapshot_for_cloud` all read. On 2026-08-27 two directory moves each silently
  narrowed `docref_lint`'s net — 347 references to 287, then 357 to 290 — in the
  tool whose entire job is noticing a reference go missing. Nothing announced it
  either time. A move of the mirrors would put every one of those eight tools in
  the same position at once.

  So this module is the preparation, not the move. When the sources do go under
  `docs/`, the change is here and the tools follow.

WHAT BELONGS HERE

  Only the roots and the patterns derived from them. A tool that needs one
  particular chapter builds it from `ODT_DIR` or `MIRROR_DIR`; a tool that needs
  to glob uses the string forms, which are relative to the repository root
  because that is what `Path.glob` and the DOC_GLOBS machinery expect.

  Not here: `docs/` and its per-document subfolders. Those are the published
  deliverables, they are addressed by glob rather than by name, and
  `tools/doc_globs.py` already owns the list of what gets swept.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-27.

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# ── the roots ────────────────────────────────────────────────────────────────
REPORT_EDITS = REPO / "report_edits"      # the editable report sources
ODT_DIR      = REPORT_EDITS / "odt"       # chapters + the master, gitignored
MIRROR_DIR   = REPORT_EDITS / "text"      # pandoc mirrors, tracked and diffable

# ── the master document ──────────────────────────────────────────────────────
# report.odm is an ODF *master*: it carries the front matter and links the
# chapter sub-documents. It is the one .odm the .gitignore admits.
MASTER_ODM   = ODT_DIR / "report.odm"
MASTER_MD    = MIRROR_DIR / "report.md"

# ── glob patterns, relative to REPO ──────────────────────────────────────────
# Strings rather than Paths: these are handed to REPO.glob() and to the
# DOC_GLOBS list, both of which want a repo-relative pattern.
ODT_GLOB     = "report_edits/odt/report*.odt"
ODM_GLOB     = "report_edits/odt/report.odm"
MIRROR_GLOB  = "report_edits/text/report*.md"
MIRROR_ANY   = "report_edits/text/*.md"


def chapter_odt(n: str | int) -> Path:
    """The ODT for chapter n — `chapter_odt(8)` -> report_edits/odt/report8.odt.

    Several tools carried the chapter filenames as literals, which is how
    `fix_stale_refs` came to hold twenty-one hard-coded paths with no existence
    guard behind them.
    """
    return ODT_DIR / f"report{n}.odt"


def chapter_md(n: str | int) -> Path:
    """The mirror for chapter n — `chapter_md(9)` -> report_edits/text/report9.md."""
    return MIRROR_DIR / f"report{n}.md"


def rel(p: Path) -> str:
    """A path as the repository sees it, for printing and for glob comparison."""
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)
