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

__version__ = "1.1.0"  # Hollingham (2026) - 2026-09-24. Martin: "if this is the case then it
#   needs to be included as a gate" — the two description classes the audit note said
#   no gate could see, now gated where they are mechanical: (1) a VERSION quoted for a
#   tool or script on an undated line must be the file's current __version__ / VERSION;
#   (2) a sentence that says a tool GATES ("is a gate", "gates in check_all", "check_all
#   runs it") must name a tool check_all.sh actually runs, and a sentence that says it
#   does NOT must name one it does not. Dated lines and lines with a history word
#   (since, until, was, introduced, added, moved) are testimony and are skipped.

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


VERSION_RX = re.compile(r"`?((?:[\w./-]+/)?[A-Za-z0-9_.-]+?(?:\.py|\.sh)?)`?\s*\(?(?:v|version\s+)?(\d+\.\d+\.\d+)\)?(?![\w.])")
HISTORY_RX = re.compile(r"\b20\d\d-\d\d(?:-\d\d)?\b|\b(?:since|until|before|was|were|introduced|added|moved|had|from v|then|earlier|previously|old)\b|→|->", re.I)
GATE_RX = re.compile(r"\b(?:gate|gates|gated|gating)\b", re.I)
NEGATION_RX = re.compile(r"\b(?:not|no|never|neither|nor|outside|advisory|cannot|without|retired|off)\b", re.I)
TOOL_RX = re.compile(r"`((?:tools/)?[A-Za-z0-9_]+(?:\.py|\.sh)?)`")


def file_version(p: Path) -> str | None:
    txt = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^__version__\s*=\s*[\"']([^\"']+)[\"']", txt, flags=re.M)      # the ASSIGNMENT
    if m:
        return m.group(1)
    m = re.search(r"^#\s*VERSION\s+(\d+\.\d+\.\d+)", txt, flags=re.M)               # shell scripts
    return m.group(1) if m else None


def tool_file(name: str) -> Path | None:
    base = name.strip("`").split("/")[-1]
    cands = [base] if "." in base else [base + ".py", base + ".sh"]
    for c in cands:
        for d in ("tools", "src", "src/utils", "working", "."):
            p = REPO / d / c
            if p.is_file():
                return p
    return None


def check_versions(rel: str, doc: Path) -> list[str]:
    out = []
    for n, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if HISTORY_RX.search(line) or HISTORY_MARK.search(line):
            continue
        for m in VERSION_RX.finditer(line):
            name, quoted = m.group(1), m.group(2)
            p = tool_file(name)
            if p is None or p.suffix not in (".py", ".sh"):
                continue
            live = file_version(p)
            if live and live != quoted:
                out.append(f"  {rel}:{n}  {name} quoted at {quoted}; the file is {live}")
    return out


def check_all_names() -> set[str]:
    ca = REPO / "tools" / "check_all.sh"
    return set(re.findall(r"tools/([A-Za-z0-9_]+)\.(?:py|sh)", ca.read_text(encoding="utf-8"))) if ca.is_file() else set()


def check_gate_claims(rel: str, doc: Path, gated: set[str]) -> list[str]:
    """A sentence that says `tool` gates must name a tool check_all runs (and vice versa)."""
    out = []
    text = doc.read_text(encoding="utf-8", errors="replace")
    for n, line in enumerate(text.splitlines(), 1):
        if HISTORY_RX.search(line) or HISTORY_MARK.search(line):
            continue
        for sent in re.split(r"(?<=[.;])\s+", line):
            if not GATE_RX.search(sent) or "check_all" not in sent and "gate" not in sent.lower():
                continue
            tools = [t.split("/")[-1].rsplit(".", 1)[0] for t in TOOL_RX.findall(sent)]
            # only tools that ARE checks: a data module named in the same sentence
            # ("`table_configs.py` (gated by `table_source_lint`)") is not the claim
            tools = [t for t in tools if re.search(r"lint|check|audit|verify|guard", t) and t != "check_all"]
            if not tools:
                continue
            negated = bool(NEGATION_RX.search(sent))
            for t in tools:
                is_gate = t in gated
                if not negated and not is_gate and (REPO / "tools" / f"{t}.py").is_file():
                    out.append(f"  {rel}:{n}  `{t}` is described as a gate but check_all.sh does not run it: …{sent.strip()[:110]}…")
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
    gated = check_all_names()
    desc: list[str] = []
    for rel in DOCS:
        doc = REPO / rel
        if doc.exists():
            desc += check_versions(rel, doc)
            desc += check_gate_claims(rel, doc, gated)
    desc = [d for d in desc if d.split("  ", 2)[-1].split(";")[0].strip() not in exempt]
    tail = (f"{checked} mention(s) checked across the root documents; {exempted} exempt"
            + (f"; {skipped_working} under working/ skipped (not present here)" if skipped_working else ""))
    if desc:
        print(f"  mention_lint: {len(desc)} description(s) disagree with the tree (versions, gate claims):")
        print(*desc, sep="\n")
    if missing:
        print(f"  mention_lint: {len(missing)} mention(s) name a file that does not exist:")
        print(*missing, sep="\n")
    if missing or desc:
        print("  (fix the document, date the sentence, or add the mention to tools/mention_lint_exempt.csv with a reason)")
        print(f"  mention_lint: FAIL — {tail}")
        return 1
    print(f"  mention_lint: OK — {tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
