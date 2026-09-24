#!/usr/bin/env python3
"""mention_lint.py — every script, tool and path a root document names must exist.

The documentation LAYER around the corpus — CLAUDE.md, MACHINE_SETUP.md, the
READMEs, index.html, the session bootstrap — describes the tree in prose, and
nothing read that prose back against the tree. `csv_mention_lint` covers the
CSVs and JSONs a document names and `docref_lint` the documents; this covers
the rest: scripts (`03_state_space_model.py`, `run_10_clearfell.py`), tools
(`tools/repoint_verify.py`, `working/nrg_git.sh`), modules (`utils/kml_io.py`)
and any other `dir/file.ext` path. The 2026-09-24 audit found `./wgit` and
`bash nrg_git.sh` (moved to `working/` on 2026-08-27), `30_c4_constrained_fit.py`
(renamed), `20_drawdown_propagation.png` and `03_cluster_averages_maod.csv`
(never those names), and a tools/ handover naming a CSV retired a month earlier
— every one in a file that tells the reader it is authoritative.

    python3 tools/mention_lint.py            # gate: exit 1 on any missing target
    python3 tools/mention_lint.py --list     # every mention and where it resolved

Scope: the documents in DOCS that exist. `working/` is a second repository, so a
clone without it skips `working/...` mentions and says so. A mention on a line
carrying `<!-- former path -->` or `<!-- former name -->` is history, not a claim,
and is skipped; so is a path listed in `tools/mention_lint_exempt.csv` with its
reason. Bare script names resolve against src/, src/utils/, tools/ and the root;
`dir/file` paths resolve from the root, then src/, outputs/ and the document's own directory. Historical narrative ("it was
`BOOTSTRAP.md` until 2026-09-10") is the exemption file's job — mark the line,
do not weaken the pattern.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-24. The documentation-layer audit's gate.

import argparse
import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCS = [
    "CLAUDE.md", "MACHINE_SETUP.md", "readme.md", "PIPELINE_README.md", "index.html",
    "notes/ledgers/README.md", "literature/README.md",
    "working/HANDOVER_BOOTSTRAP.md", "working/README_WORKING.md", "working/WORK_REGISTER.md",
]
EXEMPT = REPO / "tools" / "mention_lint_exempt.csv"
SEARCH_DIRS = ["src", "src/utils", "tools", "working", "."]
HISTORY_MARK = re.compile(r"<!--\s*former (?:path|name)\s*-->")

# `dir/file.ext` with at least one slash, or a bare pipeline script / runner name.
PATH_RE = re.compile(
    r"(?<![\w./-])"
    r"((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:py|sh|csv|json|md|html|txt|png|kml|geojson|npz|odt|odm|pdf))"
    r"(?![\w/-])")
SCRIPT_RE = re.compile(r"(?<![\w./-])((?:\d{2}[a-z]?_[A-Za-z0-9_]+|run_[A-Za-z0-9_]+)\.py)(?![\w/-])")
SKIP_PREFIX = ("http://", "https://", "gdrive:", "$HOME", "~/", "/home/", "/tmp/", "/sessions/", "<")


def load_exempt() -> dict[str, str]:
    if not EXEMPT.exists():
        return {}
    with EXEMPT.open(encoding="utf-8", newline="") as f:
        return {r["mention"].strip(): r["reason"].strip() for r in csv.DictReader(f) if r.get("mention")}


def resolve(mention: str, doc_dir: Path) -> Path | None:
    m = mention.strip("`'\"()[],;:")
    m = m.lstrip("./")
    if "/" in m:
        # utils/x.py lives in src/; 07_x/y.csv in outputs/; a document under
        # working/ names its neighbours relative to itself (updates/…)
        for base in (REPO, REPO / "src", REPO / "outputs", doc_dir):
            p = base / m
            if p.exists():
                return p
        return None
    for d in SEARCH_DIRS:
        p = REPO / d / m
        if p.exists():
            return p
    return None


def scan(doc: Path) -> list[tuple[int, str]]:
    out = []
    for n, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if HISTORY_MARK.search(line):
            continue
        for rx in (PATH_RE, SCRIPT_RE):
            for m in rx.finditer(line):
                s = m.group(1)
                if s.startswith(SKIP_PREFIX) or "*" in s or "<" in s or "{" in s:
                    continue
                out.append((n, s))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="print every mention and its resolution")
    a = ap.parse_args()
    exempt = load_exempt()
    have_working = (REPO / "working").is_dir()
    missing: list[str] = []
    checked = skipped_working = exempted = 0
    for rel in DOCS:
        doc = REPO / rel
        if not doc.exists():
            continue
        seen = set()
        for n, s in scan(doc):
            key = s.strip("`'\"()[],;:").lstrip("./")
            if (rel, key) in seen:
                continue
            seen.add((rel, key))
            if key in exempt:
                exempted += 1
                continue
            if key.startswith("working/") and not have_working:
                skipped_working += 1
                continue
            if any(k.endswith("/") and key.startswith(k) for k in exempt if k.endswith("/")):
                exempted += 1
                continue
            checked += 1
            p = resolve(key, doc.parent)
            if a.list:
                print(f"  {rel}:{n}  {key}  ->  {p.relative_to(REPO) if p else 'MISSING'}")
            if p is None:
                missing.append(f"  {rel}:{n}  {key}")
    tail = (f"{checked} mention(s) checked across the root documents; {exempted} exempt"
            + (f"; {skipped_working} under working/ skipped (not present here)" if skipped_working else ""))
    if missing:
        print(f"  mention_lint: {len(missing)} mention(s) name a file that does not exist:")
        print(*missing, sep="\n")
        print("  (fix the document, or add the mention to tools/mention_lint_exempt.csv with a reason)")
        print(f"  mention_lint: FAIL — {tail}")
        return 1
    print(f"  mention_lint: OK — {tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
