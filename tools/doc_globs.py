#!/usr/bin/env python3
"""
doc_globs.py — the one list of documents the corpus sweeps read.

WHY THIS IS ITS OWN MODULE

  `cite_check` and `symbol_check` each carried their own copy of this list, and
  `symbol_check`'s said:

      # Kept in step with cite_check.DOC_GLOBS: a document outside this list is
      # invisible to both nets, and the two should never diverge.

  They had diverged. `cite_check` swept `INTERCEPTION_TREATMENT.md`;
  `symbol_check` did not, so every symbol in that document was outside the
  register's net while a comment asserted otherwise. Nothing could have caught
  it, because a copied list has no mechanism to notice it has drifted from the
  thing it was copied from — the same failure this project has now fixed for the
  citation index, the decision log, the script ledger and the mirrors.

  A comment saying "keep these in step" is a request. A shared constant is a
  guarantee.

WHAT BELONGS HERE

  Every document that states a number, a symbol or a citation the project is
  answerable for. A file outside this list is invisible to BOTH nets at once,
  which is the property that makes the list worth keeping in one place and worth
  reviewing when the tree moves.

  Note what is deliberately absent: `notes/findings/`, `notes/specs/` and
  `changelogs/` are working records. They quote numbers freely, they are allowed
  to be superseded, and sweeping them would fill both reports with findings
  against documents nobody will publish. `notes/reference/` IS swept — those are
  standing references the report leans on.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-27.

DOC_GLOBS = [
    # the report, chapter by chapter
    "report_edits/text/report*.md",
    # every published document's markdown mirror
    "docs/**/text/*.md",
    # the two web pages that state pipeline numbers
    "index.html",
    # the repository's own front matter
    "readme.md",
    "PIPELINE_README.md",
    # standing references the report leans on (moved from the root 2026-08-27)
    "notes/reference/*.md",
    # the ledgers, which quote versions and counts
    "notes/ledgers/*.md",
    # the decision log states the numbers the decisions turned on
    "DECISION_LOG.md",
]
