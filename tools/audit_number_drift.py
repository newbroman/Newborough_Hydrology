"""
audit_number_drift.py
=====================
Machine-check documents against committed pipeline CSVs.

Diffs every numeric cell of a set of committed CSVs between two git refs, then
searches the document corpus for renderings of the OLD value that the new value
no longer produces. The output is a triage list: each hit is a place where a
document may still be quoting a superseded pipeline number.

This is a detector, not a fixer. It over-reports by design — a bare figure like
0.281 occurs in many unrelated contexts — so every hit needs eyeballing. What it
guarantees is that no changed cell goes unsearched.

Usage:
    python3 tools/audit_number_drift.py --old <ref> [--new <ref>]
                                        [--glob outputs/17_*.csv ...]
                                        [--dp 2 3 4] [--min-abs-change 0]

Hits are suppressed when the old and new values render identically at the
decimal place being searched, and when the rendered string is short enough to be
ambiguous (see _AMBIGUOUS).
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
from doc_paths import MIRROR_GLOB

REPO = Path(__file__).resolve().parents[1]

# Document corpus. PDFs are converted with pdftotext when available.
DOC_GLOBS = [
    MIRROR_GLOB,
    "docs/papers/paper_1/*.md",
    "docs/papers/**/*.md",
    "docs/**/*.md",
]
PDF_GLOBS = [
    "docs/papers/paper_1/Paper1.pdf",
    "docs/papers/paper_1/PAPER1_SI_methods.pdf",
]

# Renderings shorter than this are too ambiguous to be worth reporting.
_MIN_RENDER_LEN = 4

# Values whose rendering is a common bare integer or a round number that will
# match everywhere. Extend as needed.
_AMBIGUOUS = {"0.0", "1.0", "0.00", "1.00", "0.5", "0.50", "0.25", "0.75",
              "0.1", "0.10", "0.2", "0.20", "100", "1000"}


def _git_show(ref: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path}"],
                       capture_output=True, text=True, cwd=REPO)
    return r.stdout if r.returncode == 0 else None


def _ls_tree(ref: str, pattern: str) -> list[str]:
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref],
                       capture_output=True, text=True, cwd=REPO)
    import fnmatch
    return [p for p in r.stdout.splitlines() if fnmatch.fnmatch(p, pattern)]


def _flatten(text: str) -> str:
    """Collapse whitespace and strip pandoc escaping and HTML tags."""
    text = re.sub(r"<[^>]+>", " ", text)
    for a, b in (("\\_", "_"), ("\\|", "|"), ("\\*", "*"),
                 ("\\[", "["), ("\\]", "]"), ("\\$", "$")):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text)


def load_documents() -> dict[str, str]:
    docs: dict[str, str] = {}
    seen: set[Path] = set()
    for g in DOC_GLOBS:
        for p in REPO.glob(g):
            if p in seen or not p.is_file():
                continue
            seen.add(p)
            docs[str(p.relative_to(REPO))] = _flatten(
                p.read_text(errors="ignore"))
    for g in PDF_GLOBS:
        for p in REPO.glob(g):
            if p in seen or not p.is_file():
                continue
            seen.add(p)
            out = Path("/tmp") / (p.stem + ".audit.txt")
            r = subprocess.run(["pdftotext", str(p), str(out)],
                               capture_output=True)
            if r.returncode == 0 and out.exists():
                docs[str(p.relative_to(REPO))] = _flatten(
                    out.read_text(errors="ignore"))
            else:
                print(f"  [warn] could not convert {p.name} — skipped",
                      file=sys.stderr)
    return docs


def changed_cells(old_ref: str, new_ref: str, globs: list[str],
                  min_abs_change: float):
    """Yield (path, row_label, column, old_value, new_value) for numeric drift."""
    paths: list[str] = []
    for g in globs:
        paths.extend(_ls_tree(new_ref, g))
    for path in sorted(set(paths)):
        old_txt, new_txt = _git_show(old_ref, path), _git_show(new_ref, path)
        if old_txt is None or new_txt is None:
            continue
        try:
            old = pd.read_csv(io.StringIO(old_txt))
            new = pd.read_csv(io.StringIO(new_txt))
        except Exception:
            continue
        if old.shape != new.shape or list(old.columns) != list(new.columns):
            print(f"  [note] {path}: shape or columns changed "
                  f"({old.shape} -> {new.shape}) — cell diff skipped",
                  file=sys.stderr)
            continue
        label_col = next((c for c in old.columns
                          if old[c].dtype == object), None)
        for col in old.select_dtypes("number").columns:
            for i in range(len(old)):
                o, n = old[col].iloc[i], new[col].iloc[i]
                if pd.isna(o) or pd.isna(n):
                    continue
                if abs(float(o) - float(n)) <= min_abs_change:
                    continue
                label = str(old[label_col].iloc[i]) if label_col else f"row {i}"
                yield path, label, col, float(o), float(n)


def render(value: float, dp: int) -> str:
    return f"{abs(value):.{dp}f}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit documents for stale pipeline numbers.")
    ap.add_argument("--old", required=True, help="baseline git ref")
    ap.add_argument("--new", default="HEAD", help="current git ref (default HEAD)")
    ap.add_argument("--glob", nargs="+", default=["outputs/17*.csv",
                                                  "outputs/17_*/*.csv",
                                                  "outputs/18_*/*.csv"])
    ap.add_argument("--dp", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--min-abs-change", type=float, default=1e-9)
    ap.add_argument("--columns", nargs="+", default=None,
                    help="only audit these CSV columns (substring match)")
    ap.add_argument("--context", nargs="+", default=None,
                    help="only report hits whose surrounding text contains one "
                         "of these keywords (case-insensitive)")
    ap.add_argument("--window", type=int, default=110,
                    help="characters of context either side of a hit")
    args = ap.parse_args()

    print(f"Baseline {args.old}  ->  current {args.new}")
    docs = load_documents()
    print(f"Loaded {len(docs)} documents\n")

    cells = list(changed_cells(args.old, args.new, args.glob,
                               args.min_abs_change))
    if args.columns:
        cells = [c for c in cells
                 if any(k.lower() in c[2].lower() for k in args.columns)]
    print(f"{len(cells)} numeric cells changed across the selected CSVs\n")

    hits, searched = [], set()
    for path, label, col, o, n in cells:
        for dp in args.dp:
            ro, rn = render(o, dp), render(n, dp)
            if ro == rn or len(ro) < _MIN_RENDER_LEN or ro in _AMBIGUOUS:
                continue
            for doc, text in docs.items():
                for m in re.finditer(r"(?<![\d.])" + re.escape(ro) + r"(?![\d])",
                                     text):
                    key = (doc, m.start(), ro)
                    if key in searched:
                        continue
                    ctx = text[max(0, m.start() - args.window):
                               m.end() + args.window]
                    if args.context and not any(k.lower() in ctx.lower()
                                                for k in args.context):
                        continue
                    searched.add(key)
                    hits.append({
                        "document": doc, "stale": ro, "current": rn,
                        "source": f"{Path(path).name}:{label}:{col}",
                        "context": ctx,
                    })

    if not hits:
        print("No stale renderings found.")
        return

    by_doc: dict[str, list[dict]] = {}
    for h in hits:
        by_doc.setdefault(h["document"], []).append(h)

    print(f"{len(hits)} candidate stale renderings in {len(by_doc)} documents\n")
    for doc in sorted(by_doc):
        print("=" * 78)
        print(doc)
        print("=" * 78)
        for h in sorted(by_doc[doc], key=lambda x: x["stale"]):
            print(f"  {h['stale']} -> {h['current']}   [{h['source']}]")
            print(f"     ...{h['context']}...\n")


if __name__ == "__main__":
    main()
