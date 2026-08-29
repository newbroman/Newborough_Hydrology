#!/usr/bin/env python3
"""
context_for — "what do I already know about this, before I touch it?"

Why this exists.

  The prose record is now ~55,000 lines: ~26,000 in `working/updates/`, ~17,000
  in `working/changelogs/`, ~3,900 in `working/DECISION_LOG.md`, plus the
  ledgers and PIPELINE_README. No session will ever read more than a few per
  cent of that, and the few per cent it *does* read will be the wrong few per
  cent unless something points at the right part.

  The failure this is built to stop is not ignorance of the corpus. It is
  **knowing a record exists somewhere and not knowing it bears on the thing in
  front of you.** On 2026-08-28 a session recommended reinstating the C4
  constrained fit — the one action `D-001` forbids by name. The log had been
  open in that same session, two hours earlier, to add three new entries. The
  instruction "search the decision log first" was written at the top of the
  file, and was not enough. An instruction you must remember to follow is a
  worse mechanism than a command that answers the question for you.

  So: no summaries (a summary is a second thing to keep in sync, and it drops
  the detail that turns out to matter), and no cache (this project's
  characteristic defect is an artifact that outlived what produced it — see
  `outputs/30_c4_constrained_fit/`). The log is parsed live on every call. It
  takes milliseconds and cannot go stale.

Usage:
    python3 tools/context_for.py "report10 §4.2.3"
    python3 tools/context_for.py src/30_c4_drainage_identifiability.py
    python3 tools/context_for.py --changed     # every modified file, both repos
    python3 tools/context_for.py --index       # write working/DECISION_INDEX.md
    python3 tools/context_for.py --audit       # entries with no trace, or a dead one
"""
from __future__ import annotations

__version__ = "1.6.0"  # Hollingham (2026) — 2026-08-28.

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PRIVATE_GIT = REPO / ".git-working"
DECISIONS = REPO / "working" / "DECISION_LOG.md"
REGISTER = REPO / "working" / "updates" / "NRG_WORK_REGISTER.md"
INDEX_OUT = REPO / "working" / "DECISION_INDEX.md"
SEARCH_DIRS = [REPO / "working" / "updates", REPO / "working" / "changelogs"]

# Fields worth printing in full when an entry matches. "Question" and "Rationale"
# are the long ones and are summarised by their first sentence instead.
KEY_FIELDS = ["Decision", "Retires", "Supersedes / Retires", "Supersedes",
              "Not adopted", "Revisit-if", "Traces to"]

# The header carries a trailing parenthetical, and it comes in at least three
# shapes across the log's history:
#     (2026-07-24 · status: active)
#     (status: active · rationale confirmed 2026-08-16)
#     (2026-06-08, refined 2026-08-12 · status: active)
#     (status: active)                       <- no date at all
# An earlier regex assumed the first shape only and silently dropped 10 of 79
# entries. Silently, which is the part that matters: a decision missing from
# the index is a decision the next session never learns exists.
ENTRY_RE = re.compile(r"^### (D-\d+)\s+(.+?)\s*$", re.M)
PAREN_RE = re.compile(r"\(([^()]*status:[^()]*)\)\s*$", re.I)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
STATUS_RE = re.compile(r"status:\s*([^·)]+)", re.I)

# A token is worth matching on if it looks like an identifier rather than prose:
# a script/output stem, a section reference, a document name, a filename.
IDENTIFIERY = re.compile(
    r"(?:§\s*[\d.]+"                      # § 4.2.3
    r"|\b\d{1,2}[a-z]?_[a-z0-9_]{3,}"     # 30_c4_drainage_identifiability
    r"|\b[A-Za-z][A-Za-z0-9_]*\.(?:py|csv|md|odt|json|png|jpg)\b"
    r"|\breport\d+\b|\bPaper\d\b|\bD-\d+\b|\bW\d+\b"
    r"|\b[a-z][a-z0-9_]{5,}\b"            # beta3, clearfell, coastal_gradient…
    r"|\bC[1-5]\b|\bβ₃\b|\bβ₂\b|\bβ₁\b)", re.I)

STOP = {"python", "script", "scripts", "output", "outputs", "report", "reports",
        "committed", "values", "value", "number", "numbers", "should", "before",
        "against", "working", "update", "updates", "document", "documents"}

# Directory names are not content. Every file lives in one, so matching on it
# returns the whole log and buries the entries that actually bear on the file.
DIR_STOP = {"tools", "src", "utils", "working", "outputs", "docs", "notes",
            "updates", "changelogs", "report_edits", "odt", "text", "md",
            "papers", "paper_1", "ledgers", "reference", "data", "scratch"}


def _run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception:
        return 1, ""


def tokens_from(query: str) -> list[str]:
    """Identifier-ish tokens, plus the stem/parent of anything that is a path."""
    out: list[str] = []
    p = Path(query)
    if (REPO / query).exists() or len(p.parts) > 1:
        out += [p.name, p.stem]
        if p.parent.name and p.parent.name.lower() not in DIR_STOP:
            out.append(p.parent.name)
        # a numeric script prefix is a strong signal on its own: 30_c4_… -> "30_c4"
        m = re.match(r"(\d{1,2}[a-z]?_[a-z0-9]+)", p.stem)
        if m:
            out.append(m.group(1))
    for m in IDENTIFIERY.finditer(query):
        out.append(m.group(0))
    seen, keep = set(), []
    for t in out:
        t = t.strip().strip(".,;:()[]`'\"").replace("§ ", "§")
        if len(t) < 3 or t.lower() in STOP or t.lower() in seen:
            continue
        seen.add(t.lower())
        keep.append(t)
    return keep


def parse_entries() -> list[dict]:
    if not DECISIONS.is_file():
        return []
    text = DECISIONS.read_text(encoding="utf-8")
    marks = list(ENTRY_RE.finditer(text))
    entries = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.end():end]
        fields = {}
        for fm in re.finditer(r"^- \*\*([^:*]+):\*\*\s*(.*?)(?=^- \*\*|\Z)",
                              body, re.M | re.S):
            fields[fm.group(1).strip()] = re.sub(r"\s+", " ", fm.group(2)).strip()
        raw_title = m.group(2).strip()
        pm = PAREN_RE.search(raw_title)
        if pm:
            meta, title = pm.group(1), raw_title[:pm.start()].strip()
        else:
            meta, title = "", raw_title
        dm, sm = DATE_RE.search(meta), STATUS_RE.search(meta)
        entries.append({"id": m.group(1), "title": title,
                        "date": dm.group(1) if dm else "undated",
                        "status": sm.group(1).strip() if sm else "unstated",
                        "body": body, "fields": fields})
    return entries


def score(entry: dict, toks: list[str]) -> tuple[int, list[str]]:
    hay = (entry["title"] + " " + entry["body"]).lower()
    traces = (entry["fields"].get("Traces to", "")
              + " " + entry["fields"].get("Retires", "")).lower()
    hits, pts = [], 0
    for t in toks:
        tl = t.lower()
        if tl in hay:
            hits.append(t)
            # a hit inside "Traces to"/"Retires" is about provenance, and is the
            # kind of hit that actually decides whether you may touch something
            pts += 3 if tl in traces else 1
    return pts, hits


def show_entry(e: dict, hits: list[str]) -> str:
    out = [f"### {e['id']}  {e['title']}",
           f"  _{e['date']} · status: {e['status']}_ · matched: {', '.join(hits[:6])}"]
    q = e["fields"].get("Question", "")
    if q:
        out.append(f"  **Question:** {q[:220]}{'…' if len(q) > 220 else ''}")
    for f in KEY_FIELDS:
        v = e["fields"].get(f)
        if v:
            out.append(f"  **{f}:** {v[:500]}{'…' if len(v) > 500 else ''}")
    return "\n".join(out) + "\n"


def register_hits(toks: list[str]) -> list[str]:
    if not REGISTER.is_file():
        return []
    rows = []
    for line in REGISTER.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| **W"):
            continue
        low = line.lower()
        hit = [t for t in toks if t.lower() in low]
        if not hit:
            continue
        wid = re.match(r"\| \*\*(W\d+)\*\*", line)
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        subj = re.sub(r"\s+", " ", cells[1] if len(cells) > 1 else "")[:150]
        rows.append(f"- **{wid.group(1) if wid else '?'}** {subj}…  "
                    f"(matched: {', '.join(hit[:4])})")
    return rows


def file_hits(toks: list[str]) -> list[str]:
    """Paths only. These are long documents — the point is to name them, not read them."""
    out = []
    for d in SEARCH_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            try:
                low = f.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            hit = [t for t in toks if t.lower() in low]
            if len(hit) >= 2 or any(t.lower() in f.name.lower() for t in toks):
                out.append(f"- `{f.relative_to(REPO)}`  ({', '.join(hit[:4])})")
    return out


def report(query: str, entries: list[dict]) -> str:
    toks = tokens_from(query)
    if not toks:
        return f"## {query}\n\nNo identifier-like terms in that query — try a path, a "\
               f"script stem, a section reference (§4.2.3) or a document name.\n"
    scored = [(s, h, e) for e, (s, h) in ((e, score(e, toks)) for e in entries) if s]
    scored.sort(key=lambda x: (-x[0], x[2]["id"]))

    out = [f"## {query}", "", f"_tokens: {', '.join(toks[:10])}_", ""]
    if scored:
        out.append(f"### Decisions bearing on this — {len(scored)} match"
                   f"{'es' if len(scored) != 1 else ''}")
        out.append("")
        out.append("**These are binding.** To go against one, defeat its `Revisit-if` "
                   "— do not re-derive the answer.")
        out.append("")
        for s, h, e in scored[:6]:
            out.append(show_entry(e, h))
        if len(scored) > 6:
            out.append("Lower-scoring: " + ", ".join(f"{e['id']}" for _, _, e in scored[6:]))
            out.append("")
    else:
        out += ["### Decisions bearing on this", "", "None found. That is not a "
                "guarantee — try a broader term before concluding the question is open.", ""]

    rows = register_hits(toks)
    out += ["### Register rows", ""] + (rows[:10] or ["- none"]) + [""]
    files = file_hits(toks)
    out += ["### Records to read only if needed", ""] + (files[:12] or ["- none"]) + [""]
    return "\n".join(out)


_PRUNE_DIRS = {".git", ".git-working", "venv", "_audit_tmp", "node_modules",
               "__pycache__", ".ipynb_checkpoints"}
_NAME_INDEX: dict[str, list[str]] | None = None


def _name_index() -> dict[str, list[str]]:
    """basename -> repo-relative paths, built once per process."""
    global _NAME_INDEX
    if _NAME_INDEX is None:
        import os
        idx: dict[str, list[str]] = {}
        for root, dirs, files in os.walk(REPO):
            dirs[:] = [d for d in dirs if d not in _PRUNE_DIRS and not d.startswith(".git")]
            for f in files:
                idx.setdefault(f, []).append(str(Path(root, f).relative_to(REPO)))
        _NAME_INDEX = idx
    return _NAME_INDEX


def resolve_trace(raw: str) -> tuple[str, str]:
    """Resolve one Traces-to token. Returns (verdict, detail).

    Traces were written by hand over months and are not uniformly repo-relative:
    `utils/config.py`, `20_spatial_figures.py`, `src/16_water_bal.py::save()`,
    `utils/{a,b}.py`, `outputs/31_cluster_validation/*` all appear. Judging those
    dead because they are not literal paths would bury the few that really are
    dead, which are the only ones worth anyone's attention.
    """
    tok = raw.strip()
    tok = re.split(r"::", tok)[0].strip()          # drop ::symbol()
    tok = re.sub(r"\s+[A-Z_]{3,}.*$", "", tok)     # drop a trailing CONSTANT name
    tok = tok.strip().rstrip("/")
    if not tok:
        return "SKIP", raw
    if "{" in tok or "}" in tok:
        return "SKIP", "brace form — not machine-checkable"
    # Backticks wrap expressions as well as paths: `DRAWDOWN_H0_MM × (A / B)` is
    # a formula, and calling it a missing file is noise that hides real rot.
    if re.search(r"[×=+()]|\s", tok):
        return "SKIP", "expression, not a path"
    if "*" in tok:
        return ("EXISTS", tok) if list(REPO.glob(tok)) else ("ABSENT", tok)
    if (REPO / tok).exists():
        return "EXISTS", tok
    hits = _name_index().get(Path(tok).name, [])
    if hits:
        return "MOVED", hits[0]
    return "ABSENT", tok


def audit(entries: list[dict]) -> int:
    """Check the Traces-to fields themselves.

    A trace is a claim about the tree, so it can go wrong in both directions: an
    entry with no trace is invisible to every query, and an entry pointing at a
    path that no longer exists is worse than silent — it asserts provenance that
    has evaporated. That is this repository's signature defect (D-001's archived
    outputs, `outputs/30_c4_constrained_fit/`), so the field that exists to
    prevent it should not be exempt from it.
    """
    missing, stale, declared, corrected, ok = [], [], [], [], 0
    for e in entries:
        val = e["fields"].get("Traces to", "")
        if not val:
            missing.append(e["id"])
            continue
        paths = re.findall(r"`([^`]+)`", val)
        paths = [p for p in paths if "/" in p or p.endswith(
            (".py", ".csv", ".md", ".sh", ".json", ".odt", ".txt", ".jpg", ".png"))]
        gone = []
        for pth in paths:
            verdict, detail = resolve_trace(pth)
            if verdict != "ABSENT":
                continue
            # A trace can honestly point at something that was never committed —
            # a session probe, a licence-restricted source. Where the entry says
            # so beside the path, that is disclosure, not rot, and lumping the
            # two together buries the rot.
            at = val.find(pth)
            near = val[at:at + 160].lower() if at >= 0 else ""
            if any(k in near for k in ("session probe", "not committed",
                                       "licence-restricted", "license-restricted",
                                       "deliberately not", "rerunnable")):
                declared.append((e["id"], pth))
                continue
            # This project corrects a dated record by APPENDING a dated Note, never
            # by repointing it. So a trace can be knowingly superseded while the
            # original text stays as written — and reporting that as rot forever
            # would train everyone to ignore the report. A dated Note naming the
            # path is the entry saying "we know".
            notes = [b for b in re.findall(r"- \*\*Note, \d{4}-\d{2}-\d{2}.*?(?=\n- \*\*|\Z)",
                                           e["body"], re.S)]
            if any(pth in n or Path(pth).name in n for n in notes):
                corrected.append((e["id"], pth))
                continue
            gone.append((pth, detail))
        if gone:
            stale.append((e["id"], gone))
        elif paths:
            ok += 1
    print(f"# Trace audit — {len(entries)} entries\n")
    print(f"{ok} entries trace to paths that all exist.")
    if missing:
        print(f"\n## No Traces-to field ({len(missing)})")
        print("These are invisible to every `context_for` query that does not happen "
              "to hit their prose.\n")
        for i in missing:
            print(f"  {i}")
    if stale:
        print(f"\n## Traces to a path that no longer exists ({len(stale)})")
        print("Either the file moved — repoint the trace — or it was retired, in "
              "which case say so in the entry rather than leaving a dead path.\n")
        for i, gone in stale:
            for g, _ in gone:
                print(f"  {i}  ->  {g}")
    if corrected:
        print(f"\n## Superseded, and said so in a dated Note ({len(corrected)}) — not a defect")
        print("The entry records the correction without repointing itself, which is the "
              "convention here.\n")
        for i, pth in corrected:
            print(f"  {i}  ->  {pth}")
    if declared:
        print(f"\n## Declared as never committed ({len(declared)}) — not a defect")
        print("The entry says so beside the path. Listed so the count reconciles.\n")
        for i, pth in declared:
            print(f"  {i}  ->  {pth}")
    if not missing and not stale:
        print("\nNo missing traces and no dead paths.")
    return 1 if (missing or stale) else 0


def changed_files() -> list[str]:
    paths = []
    for private in (False, True):
        base = ["git", "--no-optional-locks"]
        if private:
            if not PRIVATE_GIT.exists():
                continue
            base += [f"--git-dir={PRIVATE_GIT}", f"--work-tree={REPO}"]
        rc, so = _run(base + ["status", "--porcelain"])
        if rc == 0:
            for l in so.splitlines():
                if not l.strip():
                    continue
                # NOT a fixed slice: _run() strips stdout, so the first line has
                # lost porcelain's leading space and is one character narrower
                # than every line below it.
                m = re.match(r"^\s*\S{1,2}\s+(.*)$", l)
                if m:
                    paths.append(m.group(1).strip().strip('"'))
    return sorted(set(paths))


def write_index(entries: list[dict]) -> None:
    lines = ["# Decision index",
             "",
             "**Generated by `tools/context_for.py --index`. Do not hand-edit.**",
             "",
             "One line per decision, so the whole set can be scanned without reading "
             "3,900 lines. To pull the entries that bear on something specific:",
             "",
             "```",
             "python3 tools/context_for.py \"report10 §4.2.3\"",
             "python3 tools/context_for.py --changed",
             "```",
             "",
             f"{len(entries)} entries.",
             "",
             "| id | decision | date | status |",
             "|---|---|---|---|"]
    for e in entries:
        title = e["title"].replace("|", "\\|")
        lines.append(f"| **{e['id']}** | {title} | {e['date']} | {e['status']} |")
    INDEX_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  WROTE  {INDEX_OUT.relative_to(REPO)}  ({len(entries)} entries)")


def main(argv: list[str]) -> int:
    entries = parse_entries()
    if not entries:
        print("could not parse working/DECISION_LOG.md", file=sys.stderr)
        return 1

    if "--audit" in argv:
        return audit(entries)

    if "--index" in argv:
        write_index(entries)
        return 0

    if "--changed" in argv:
        paths = changed_files()
        if not paths:
            print("No modified files in either repository.\n\n"
                  "Note that **ODTs are gitignored**, so document edits never appear "
                  "here. Query those by name: `context_for.py \"report10 §4.2.3\"`.")
            return 0
        print(f"# Context for {len(paths)} changed file(s)\n")
        for p in paths:
            print(report(p, entries))
        return 0

    query = " ".join(a for a in argv if not a.startswith("--"))
    if not query:
        print(__doc__)
        return 2
    print(report(query, entries))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
