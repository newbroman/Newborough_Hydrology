#!/usr/bin/env python3
"""
build_diary.py — the project diary, derived rather than written.

WHY DERIVED

  Four records already exist and none of them is a history:

    working/DECISION_LOG.md      WHY something is the way it is        75 entries
    working/changelogs/          WHAT changed, one delta per batch     93 files
    working/updates/             what was FOUND, dated notes           82 files
    git log                      WHEN code moved                      388 commits

  Each is authoritative for its own question and silent on the others. Nothing
  says that on 2026-08-27 a symbol pass corrupted eleven substitutions in three
  published documents, which produced two new guards, exposed a defect in
  doc_lock, and was recorded in one delta and no decision. That sentence needs
  all four sources and lives in none of them.

  It is DERIVED because a hand-maintained fifth record would go stale, and this
  project has the evidence: `working/WORK_REGISTER.md` still describes
  `Updates_required/` and `store/`, both renamed on 2026-08-27, and it is the
  file a cold session is told to read first. A diary written by hand would be
  that file within a fortnight.

WHAT IT IS FOR

  Three things, in the order they will actually be used:

    1. "When did X happen, and what else was going on?" — the lookup a decision
       log cannot answer because it is ordered by decision, not by day.
    2. The shape of the work — where effort clustered, and where a quiet week
       preceded a bad one.
    3. Raw material for a methods history. A 21-year monitoring record analysed
       over ten weeks has a story, and the story is currently spread over four
       directories.

PRIVATE

  It derives from `DECISION_LOG.md` and `changelogs/`, both of which are private
  by ruling — the decision log because it is *"meant for us to keep track not
  for the public"*. So the diary is private too, and lives under `working/`.
  `--public` emits a thin version with dates, counts and commit subjects only:
  no decision text, no changelog titles, no finding titles.

Usage
    python3 tools/build_diary.py                 write working/PROJECT_DIARY.md
    python3 tools/build_diary.py --since 2026-08-01
    python3 tools/build_diary.py --public        redacted, for the public repo
    python3 tools/build_diary.py --stdout        print, write nothing
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-28.

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKING = REPO / "working"
DATE = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def _h1(path: Path) -> str:
    """The document's own title, or its filename if it has none."""
    try:
        for line in path.read_text(encoding="utf8", errors="replace").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
            if line.strip() and not line.startswith("#"):
                break
    except OSError:
        pass
    return path.stem.replace("_", " ")


def decisions() -> tuple[dict[str, list[str]], list[str]]:
    """({date: [entry]}, [undated entries]) from the decision log's headings.

    THREE heading formats are in use and a fourth group has no date at all:

        D-001   ... (2026-07-24 · status: active)
        D-008   ... (status: active · rationale confirmed 2026-08-16)
        D-019   ... (2026-06-08, refined 2026-08-12 · status: active)
        D-020   ... (status: active)                      <- no date

    The first regex written here matched only the first form and dropped the
    other ten entries silently — the precise failure this project has spent a
    week removing from its other checks, reproduced in a new tool inside an
    hour. So: take the FIRST date anywhere in the parenthetical, and return
    everything dateless separately so the diary can print it rather than lose
    it.
    """
    f = WORKING / "DECISION_LOG.md"
    out, undated = defaultdict(list), []
    if not f.exists():
        return out, undated
    pat = re.compile(r"^###\s+(D-\d+)\s+(.*?)\s*\(([^)]*)\)\s*$")
    for line in f.read_text(encoding="utf8", errors="replace").splitlines():
        m = pat.match(line)
        if not m:
            continue
        did, title, paren = m.groups()
        st = re.search(r"status:\s*([^·)]+)", paren)
        status = st.group(1).strip() if st else ""
        mark = "" if status in ("active", "") else f" [{status}]"
        dates = DATE.findall(paren)
        entry = f"**{did}** {title.strip()}{mark}"
        if dates:
            if len(dates) > 1:
                entry += f"  *(refined {dates[-1]})*"
            out[dates[0]].append(entry)
        else:
            undated.append(entry)
    return out, undated


def dated_files(folder: Path) -> tuple[dict[str, list[tuple[str, str]]], list[tuple[str, str]]]:
    """({date: [(filename, title)]}, [undated]) for files whose NAME has a date.

    Undated files are RETURNED, not skipped. Three changelogs and thirteen notes
    carry no date in their filename; dropping them would make the diary quietly
    incomplete, which is worse than a diary that says what it could not place.
    """
    out, undated = defaultdict(list), []
    if not folder.is_dir():
        return out, undated
    for p in sorted(folder.glob("*.md")):
        m = DATE.search(p.name)
        if m:
            out[m.group(1)].append((p.name, _h1(p)))
        else:
            undated.append((p.name, _h1(p)))
    return out, undated


def commits(since: str | None) -> dict[str, list[tuple[str, str, int]]]:
    """{date: [(sha, subject, files changed)]} — newest first within a day."""
    cmd = ["git", "--no-optional-locks", "log",
           "--format=%H%x1f%ad%x1f%s", "--date=short", "--shortstat"]
    if since:
        cmd.append(f"--since={since}")
    try:
        raw = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                             timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return defaultdict(list)
    out = defaultdict(list)
    sha = date = subj = None
    for line in raw.splitlines():
        if "\x1f" in line:
            if sha:
                out[date].append((sha[:7], subj, 0))
            sha, date, subj = line.split("\x1f", 2)
        elif line.strip().startswith(tuple("0123456789")) and sha:
            n = re.search(r"(\d+) files? changed", line)
            if n and out[date] and out[date][-1][0] == sha[:7]:
                pass
            if n:
                out[date].append((sha[:7], subj, int(n.group(1))))
                sha = None
    if sha:
        out[date].append((sha[:7], subj, 0))
    # a commit with no shortstat (empty) can double-add; de-duplicate by sha
    for d in out:
        seen, keep = set(), []
        for c in out[d]:
            if c[0] in seen:
                continue
            seen.add(c[0]); keep.append(c)
        out[d] = keep
    return out


def build(since: str | None, public: bool) -> str:
    dec, dec_undated = decisions()
    chg, chg_undated = dated_files(WORKING / "changelogs")
    upd, upd_undated = dated_files(WORKING / "updates")
    com = commits(since)

    days = sorted(set(dec) | set(chg) | set(upd) | set(com), reverse=True)
    if since:
        days = [d for d in days if d >= since]
    if not days:
        return "# Project diary\n\nNothing to report.\n"

    n_com = sum(len(v) for d, v in com.items() if d in days)
    L = ["# NRG — project diary", ""]
    L += ["**Generated by `tools/build_diary.py`. Do not edit by hand.**", ""]
    if public:
        L += ["*Public form: dates, counts and commit subjects only. The "
              "decisions, deltas and findings themselves are private.*", ""]
    else:
        L += ["*Private. It derives from `DECISION_LOG.md` and `changelogs/`, "
              "which are private by ruling.*", ""]
    L += [f"- **Span:** {days[-1]} to {days[0]} ({len(days)} active days)",
          f"- **Commits:** {n_com}",
          f"- **Decisions:** {sum(len(v) for v in dec.values())}",
          f"- **Change deltas:** {sum(len(v) for v in chg.values())}",
          f"- **Findings and notes:** {sum(len(v) for v in upd.values())}", ""]
    n_undated = len(dec_undated) + len(chg_undated) + len(upd_undated)
    if n_undated:
        L += [f"- **Undated, and so not placed on any day: {n_undated}** — "
              f"listed at the end", ""]

    # ── the shape of the work, oldest first ──────────────────────────────────
    L += ["## Timeline", "",
          "| date | commits | decisions | deltas | notes |", "|---|---|---|---|---|"]
    for d in reversed(days):
        c, k, u, n = len(com.get(d, [])), len(dec.get(d, [])), \
                     len(chg.get(d, [])), len(upd.get(d, []))
        bar = "█" * min(int(c / 3) + (1 if c else 0), 14)
        L.append(f"| {d} | {c} {bar} | {k or ''} | {u or ''} | {n or ''} |")
    L.append("")

    # ── the days themselves, newest first for lookup ─────────────────────────
    L += ["## By day", ""]
    for d in days:
        L.append(f"### {d}")
        L.append("")
        if dec.get(d) and not public:
            L.append("**Decisions**")
            L.append("")
            for t in dec[d]:
                L.append(f"- {t}")
            L.append("")
        elif dec.get(d):
            L.append(f"**Decisions:** {len(dec[d])} recorded")
            L.append("")
        if chg.get(d):
            L.append("**Changed**")
            L.append("")
            for fn, title in chg[d]:
                L.append(f"- {title}" if not public else f"- (delta)")
            L.append("")
        if upd.get(d):
            L.append("**Found / written**")
            L.append("")
            for fn, title in upd[d]:
                L.append(f"- {title}" if not public else f"- (note)")
            L.append("")
        if com.get(d):
            L.append("**Commits**")
            L.append("")
            for sha, subj, nf in com[d]:
                files = f"  ({nf} files)" if nf else ""
                L.append(f"- `{sha}` {subj}{files}")
            L.append("")

    if n_undated:
        L += ["## Undated", "",
              "Carrying no date, so placed on no day. Not a diary fault — a "
              "record that cannot say when it happened.", ""]
        if dec_undated:
            L += [f"**Decision log — {len(dec_undated)} entries with no date "
                  f"in the heading**", ""]
            for e in dec_undated:
                L.append(f"- {e}" if not public else "- (decision)")
            L.append("")
        for label, items in (("Changelogs", chg_undated), ("Notes", upd_undated)):
            if items:
                L += [f"**{label} — {len(items)} with no date in the filename**", ""]
                for fn, title in items:
                    L.append(f"- `{fn}` — {title}" if not public else f"- `{fn}`")
                L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="only days on or after this date (YYYY-MM-DD)")
    ap.add_argument("--public", action="store_true",
                    help="redacted: dates, counts and commit subjects only")
    ap.add_argument("--stdout", action="store_true", help="print, write nothing")
    ap.add_argument("--out", help="write somewhere other than the default")
    a = ap.parse_args()

    text = build(a.since, a.public)
    if a.stdout:
        sys.stdout.write(text)
        return 0
    dest = Path(a.out) if a.out else (
        REPO / ("notes/PROJECT_HISTORY.md" if a.public
                else "working/PROJECT_DIARY.md"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf8")
    print(f"  wrote {dest.relative_to(REPO)}  ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
