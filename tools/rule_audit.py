#!/usr/bin/env python3
"""rule_audit — the half of NRG HQ that reports on the CHATS, not on the tree (D-301, D-302).

The HQ page's board, tasks and gate bands answer "what does the tree look like". This module
answers the other half of Martin's 2026-11-05 02:59 request: *are the project's own rules being
followed, by whom, and since when*. It reads evidence and emits findings; `tools/hq_snapshot.py`
step 5 calls it and writes them to the page's `findings` collection.

IT REPORTS AND NEVER INTERVENES (D-302)

  It releases no claim, edits nothing under another chat's claim, and writes nothing at all when the
  private store is absent - because the lock, the registers and the decision log are all private, so
  a public-only run has no evidence and must never read as "all clear". That is D-300's lesson
  applied to the auditor itself.

IT IS AN AUDITOR OF THE AUDIT TRAIL, NOT A SECOND LINTER

  The em-space lint, the typed-number gate, the forty-eight others: each is checked in ONE place.
  This module reads their verdicts from `scratch/check_all_summary.json` (check_all 1.34.0) and
  re-implements none of them. Where a rule already has a gate, it is that gate's; what is left -
  and what nothing checked before this - is the CONDUCT of the chats: who committed what, under
  whose claim, with which record left behind.

WHAT IT CHECKS (spec §8; the rule ids are stable and are what the page keys on)

  handover-entry    every commit day in the window has a dated HANDOVER_NOTE entry, with a
                    provenance block and the D-numbers it recorded (D-143). session_handover's
                    own --check asks only about the NEWEST commit day; this asks about each.
  decision-fields   a new DECISION_LOG entry carries Retires and Revisit-if.
  claim-coverage    files a commit changed fall under a claim held, AT THAT MOMENT, by the chat
                    that made it - from claim_for_path, the lock's history and claim_overrides.csv.
  session-trailer   a commit carries the Claude-Session trailer, and its chat is registered.
  ship-verdict      a ship quotes a check_all verdict, and that verdict is OK.
  doc-version       a versioned document was bumped, not edited in place (the mirror header's
                    source-sha256 moved while the version in its filename did not).
  script-version    a pipeline script's edit bumps `__version__` AND its SCRIPT_LEDGER row, in
                    the same commit.
  chat-status       a registered chat with activity has a status, and a `done` chat holds no claim.
  claim-stale       a claim past the abandoned age (72 h of no ACTIVITY, D-300).
  override          a forced take or release inside the window.
  gate-verdict      check_all FAIL/FAULT, or a section newly red, from the summary - not re-run.
  ship-waiting      a ship request waiting more than a day.
  repo-behind       a repository behind origin on the publishing machine.
  stale-branch      a branch pushed and unmerged for over a week. Suppressible with a REASON
                    (working/rule_audit_suppress.csv): notes/2026-11-04-water-balance-handovers
                    is deliberate - it is for reading, not merging - and a rule that cannot be
                    told so is a rule that gets ignored.

THE WINDOW, AND WHY THE FIRST RUN IS BOUNDED

  "Everything since the previous run" needs a previous run. The watermark is
  `working/rule_audit_state.json` (private, like everything else here). With no state - a first
  run, a fresh clone - the window is the last SINCE_DAYS days rather than 21 years of history, so
  the first run reports today's conduct and not the whole corpus's. `--since REV` overrides both.

ATTRIBUTION IS BY TRAILER, AND WHAT IT CANNOT DO IS SAID OUT LOUD

  A commit says nothing about which chat made it except through the `Claude-Session` trailer the
  harness adds, matched against the register's `link` column (spec §6). Measured 2026-11-05: no
  register row carries a link yet and 1 of the last 6 public commits carries the trailer. So
  `session-trailer` fires, which is correct and is the point - and `claim-coverage` reports the
  commits it could NOT attribute as one aggregate finding rather than accusing them, because an
  unattributable commit is a gap in the evidence, not a breach of the rule.

Usage:
  python3 tools/rule_audit.py                      # the findings, as text
  python3 tools/rule_audit.py --json               # the payload hq_snapshot step 5 reads
  python3 tools/rule_audit.py --since 873a3c91     # an explicit window
  python3 tools/rule_audit.py --write-state        # move the watermark to HEAD
  python3 tools/rule_audit.py --check | --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-05 (D-301, D-302, T-137, spec
#   NRG_handover_HQ_page_2026-11-05 §8 and §11 phase 3; brief NRG_brief_rule_audit_2026-11-05).
#   First issue: the fourteen rules above, the lock-history timeline that makes claim-coverage an
#   evidence check rather than a guess, a bounded first window, suppression with a reason, and a
#   refusal to report anything without the private store.

import argparse
import csv
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE).resolve()
sys.path.insert(0, str(HERE / "tools"))

import doc_lock                                                       # noqa: E402
import chat_register                                                  # noqa: E402

STATE = REPO / "working/rule_audit_state.json"
SUPPRESS = REPO / "working/rule_audit_suppress.csv"
NOTE = REPO / "working/updates/HANDOVER_NOTE.md"
DECISIONS = REPO / "working/DECISION_LOG.md"
LEDGER = REPO / "notes/ledgers/SCRIPT_LEDGER.md"
GATE_SUMMARY = REPO / (os.environ.get("NRG_GATE_SUMMARY") or "scratch/check_all_summary.json")

SINCE_DAYS = 2            # the bounded first window; see the docstring
MAX_PER_RULE = 8          # a rule that fires on many subjects reports this many, then one summary
SHIP_WAIT_HOURS = 24      # spec §7: "a ship waiting more than a day"

SUPPRESS_FIELDS = ["rule", "subject", "reason", "by", "when"]

# D-143 asks a handover entry for three things. The provenance block is the entry's own account of
# where the work came from - in practice a `**Why:**` bullet naming a spec, brief or changelog. The
# decisions line is "which D-numbers (or 'none')", as working/HANDOVER_BOOTSTRAP.md states the rule;
# the literal phrase "Decisions recorded this session" is one way of writing it and appears in 1 of
# the note's entries, so matching only that phrase would flag almost every honest entry.
PROVENANCE_RE = re.compile(r"\*\*Why:?\*\*|(?:spec|brief|changelog)\s+[`\w/]", re.I)
DECISIONS_RE = re.compile(r"Decisions recorded this session|\bD-\d+\b"
                          r"|no (?:new )?decisions|decisions?:?\s*none", re.I)

# The mirror header refresh_mirrors writes. The source filename carries the version; source-sha256
# carries the content. If the sha moves and the version does not, the document was edited in place.
MIRROR_HEAD_RE = re.compile(r"GENERATED MIRROR of (\S+).*?source-sha256=([0-9a-f]+)", re.S)
VERSION_IN_NAME_RE = re.compile(r"_v(\d+(?:[_.]\d+)*)\.od[tm]$")
SCRIPT_VERSION_RE = re.compile(r"^__version__\s*=", re.M)

# A pipeline script has a SCRIPT_LEDGER row; a tool does not (the ledger is "one row per pipeline
# script"). So script-version applies to src/ and run_analysis.py, and the __version__ half alone
# applies to tools/ - which is what the ledger can actually witness.
PIPELINE_SCRIPT_RE = re.compile(r"^(?:src/[^/]+\.py|run_analysis\.py)$")


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def stamp() -> str:
    return now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: str | None) -> datetime.datetime | None:
    if not ts:
        return None
    try:
        d = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


# ── git, over either repository (CLAUDE.md §4f: two git directories, one tree) ───────────────

def _git(*args: str, private: bool = False) -> str:
    gd = REPO / (".git-working" if private else ".git")
    cmd = ["git", "--no-optional-locks", f"--git-dir={gd}"]
    if private:
        cmd.append(f"--work-tree={REPO}")
    try:
        p = subprocess.run(cmd + list(args), cwd=str(REPO), capture_output=True, text=True, timeout=60)
        return p.stdout.rstrip("\n") if p.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


SEP = "\x1f"
REC = "\x1e"


def commits(private: bool = False, since: str | None = None, days: int = SINCE_DAYS) -> list[dict]:
    """The commits in the window, newest last. `since` is a rev; without one, the last `days`."""
    rng = [f"{since}..HEAD"] if since else [f"--since={days}.days.ago"]
    raw = _git("log", "--no-merges", "--reverse",
               f"--format=%H{SEP}%cI{SEP}%s{SEP}%(trailers:key=Claude-Session,valueonly){SEP}%b{REC}",
               *rng, private=private)
    out = []
    for rec in raw.split(REC):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        parts = rec.split(SEP)
        if len(parts) < 5:
            continue
        sha, when, subject, session, body = parts[0], parts[1], parts[2], parts[3], parts[4]
        files = [f for f in _git("show", "--name-only", "--format=", sha,
                                 private=private).splitlines() if f.strip()]
        out.append({"sha": sha[:8], "full": sha, "at": when, "subject": subject,
                    "session": session.strip(), "body": body, "files": files,
                    "repo": "private" if private else "public", "private": private})
    return out


def _show(sha: str, path: str, private: bool = False) -> str:
    return _git("show", f"{sha}:{path}", private=private)


# ── the lock's history: who held a claim at a given moment ──────────────────────────────────

def lock_timeline() -> list[dict]:
    """Every state working/DOCUMENT_LOCK.json has been committed in, oldest first.

    The lock file records only the CURRENT claims, so "who held `tools` when that commit landed" is
    not in it. It is in the private repository's history of the file: each commit of it is a dated
    snapshot. That is the evidence the spec means by "the lock's history", and it is why
    claim-coverage is a check rather than a guess.
    """
    raw = _git("log", "--reverse", f"--format=%H{SEP}%cI", "--", "working/DOCUMENT_LOCK.json",
               private=True)
    out = []
    for line in raw.splitlines():
        if SEP not in line:
            continue
        sha, when = line.split(SEP, 1)
        try:
            d = json.loads(_show(sha, "working/DOCUMENT_LOCK.json", private=True) or "{}")
        except ValueError:
            continue
        out.append({"at": _parse(when), "claims": {k: (v or {}).get("chat")
                                                   for k, v in (d.get("claims") or {}).items()
                                                   if v and v.get("chat")}})
    return out


def holder_at(timeline: list[dict], claim: str, when: datetime.datetime | None) -> str | None:
    """The chat holding `claim` at `when`, from the newest snapshot at or before it.

    A snapshot is the state AFTER that commit, so the one that applies to an event at `when` is the
    last one committed at or before it. With nothing before it - the lock's history starts later
    than the commit - the honest answer is None, not "free".
    """
    if when is None:
        return None
    best = None
    for snap in timeline:
        if snap["at"] and snap["at"] <= when:
            best = snap
        else:
            break
    if best is None:
        return None
    return best["claims"].get(claim)


# ── suppression: a rule that cannot be told "this one is deliberate" gets ignored ────────────

def suppressions() -> list[dict]:
    if not SUPPRESS.exists():
        return []
    try:
        import register_io
        return register_io.read_rows(SUPPRESS)
    except Exception:                                                 # pragma: no cover
        try:
            with SUPPRESS.open(encoding="utf-8") as fh:
                return list(csv.DictReader(fh))
        except OSError:
            return []


def is_suppressed(rows: list[dict], rule: str, subject: str) -> dict | None:
    for r in rows:
        if (r.get("rule") or "").strip() == rule and (r.get("subject") or "").strip() == subject \
                and (r.get("reason") or "").strip():
            return r
    return None


# ── findings ────────────────────────────────────────────────────────────────────────────────

def _slug(s: str) -> str:
    out = "".join(c if (c.isalnum() or c in "_-.:") else "-" for c in (s or "").strip())
    return (out.strip("-") or "x")[:120]


class Audit:
    """Collects findings. `key` is rule + subject, so "newly found" means something across runs -
    the same keying contract hq_snapshot's newly_red() uses for gate sections."""

    def __init__(self) -> None:
        self.findings: list[dict] = []
        self.suppressed: list[dict] = []
        self.sup = suppressions()
        self._counts: dict[str, int] = {}

    def add(self, rule: str, subject: str, title: str, detail: str = "", *,
            serious: bool = False, chat: str | None = None, commit: str | None = None,
            file: str | None = None, evidence: str = "", at: str = "") -> None:
        s = is_suppressed(self.sup, rule, subject)
        if s:
            self.suppressed.append({"rule": rule, "subject": subject, "title": title,
                                    "reason": s.get("reason", ""), "by": s.get("by", "")})
            return
        n = self._counts.get(rule, 0) + 1
        self._counts[rule] = n
        if n > MAX_PER_RULE:
            return
        self.findings.append({"key": f"{rule}:{_slug(subject)}", "rule": rule, "subject": subject,
                              "title": title, "detail": detail, "evidence": evidence,
                              "serious": bool(serious), "chat": chat or "", "commit": commit or "",
                              "file": file or "", "at": at or stamp()})

    def overflow(self) -> None:
        """A rule that fired more than MAX_PER_RULE times gets one finding for the remainder, so the
        page is bounded and the count is still true."""
        for rule, n in sorted(self._counts.items()):
            if n > MAX_PER_RULE:
                self.findings.append({
                    "key": f"{rule}:and-{n - MAX_PER_RULE}-more", "rule": rule,
                    "subject": f"and {n - MAX_PER_RULE} more",
                    "title": f"{rule}: {n - MAX_PER_RULE} further subject(s) not listed",
                    "detail": f"{n} subjects matched this rule in the window; the first "
                              f"{MAX_PER_RULE} are above.",
                    "evidence": "", "serious": False, "chat": "", "commit": "", "file": "",
                    "at": stamp()})


# ── the rules ───────────────────────────────────────────────────────────────────────────────

def note_entry_days() -> dict[str, str]:
    """{date -> that entry's text}, from HANDOVER_NOTE's `## YYYY-MM-DD — title` entries."""
    if not NOTE.exists():
        return {}
    try:
        text = NOTE.read_text(encoding="utf-8")
    except OSError:
        return {}
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})\b", line)
        if m:
            if cur:
                out.setdefault(cur, "\n".join(buf))
            cur, buf = m.group(1), [line]
        elif cur:
            buf.append(line)
    if cur:
        out.setdefault(cur, "\n".join(buf))
    return out


def rule_handover(a: Audit, cs: list[dict]) -> None:
    """Each commit day in the window has an entry, with a provenance block and its D-numbers.

    One finding per DAY, not per commit: twelve commits on one day with no entry are one missing
    record, and saying it twelve times would bury the other rules."""
    entries = note_entry_days()
    days = {}
    for c in cs:
        d = (_parse(c["at"]) or now()).astimezone().date().isoformat()
        days.setdefault(d, []).append(c)
    for day, group in sorted(days.items()):
        shas = ", ".join(x["sha"] for x in group[:6]) + (" …" if len(group) > 6 else "")
        text = entries.get(day)
        if text is None:
            a.add("handover-entry", day,
                  f"no handover entry for {day}, which has {len(group)} commit(s)",
                  "D-143: one dated entry per session at the top of working/updates/HANDOVER_NOTE.md.",
                  serious=False, evidence=shas, at=day)
            continue
        missing = []
        if not PROVENANCE_RE.search(text):
            missing.append("a provenance block (what the work came from: the spec, brief or changelog)")
        if not DECISIONS_RE.search(text):
            missing.append("the decisions it recorded (the D-numbers, or 'none')")
        if missing:
            a.add("handover-entry", f"{day}/fields",
                  f"the {day} handover entry is missing {len(missing)} of D-143's parts",
                  "; ".join(missing), serious=False, evidence=shas, at=day)


def rule_decision_fields(a: Audit, cs: list[dict]) -> None:
    """A new DECISION_LOG entry carries Retires and Revisit-if.

    decision_lint already gates the Rationale block, so that is its rule and not re-checked here.
    New entries are found by diffing the log across the window rather than by reading all 305."""
    touched = [c for c in cs if c["private"] and "working/DECISION_LOG.md" in c["files"]]
    if not touched or not DECISIONS.exists():
        return
    first = touched[0]
    before = _show(f"{first['full']}^", "working/DECISION_LOG.md", private=True)
    try:
        after = DECISIONS.read_text(encoding="utf-8")
    except OSError:
        return
    had = set(re.findall(r"^#+\s*\*{0,2}(D-\d+)", before, re.M))
    for m in re.finditer(r"^#+\s*\*{0,2}(D-\d+)(.*?)(?=^#+\s*\*{0,2}D-\d+|\Z)",
                         after, re.M | re.S):
        did, body = m.group(1), m.group(2)
        if did in had:
            continue
        missing = [f for f, pat in (("Retires", r"Retires:"), ("Revisit-if", r"Revisit[- ]if:"))
                   if not re.search(pat, body, re.I)]
        if missing:
            a.add("decision-fields", did, f"{did} has no {' and no '.join(missing)} field",
                  "A new decision says what it retires and what would reopen it; without "
                  "Revisit-if the burden on reopening it cannot be met.",
                  serious=False, commit=first["sha"], evidence=body.strip().splitlines()[0][:120]
                  if body.strip() else "")


def rule_claims_and_trailers(a: Audit, cs: list[dict], timeline: list[dict],
                             reg: list[dict]) -> None:
    """claim-coverage and session-trailer. See the docstring on attribution."""
    links = {}
    for r in reg:
        link = (r.get("link") or "").strip()
        if link:
            links[link] = r.get("chat")
    names = {(r.get("chat") or "").strip() for r in reg if (r.get("chat") or "").strip()}
    unattributed = []
    for c in cs:
        chat = None
        if c["session"]:
            chat = links.get(c["session"]) or next(
                (v for k, v in links.items() if k and (k in c["session"] or c["session"] in k)), None)
        else:
            a.add("session-trailer", c["sha"], f"commit {c['sha']} carries no Claude-Session trailer",
                  "Spec §6: the trailer is what lets a commit be matched to a registered chat. "
                  "Without it this commit cannot be audited against the claim it was made under.",
                  serious=True, commit=c["sha"], evidence=c["subject"][:120], at=c["at"])
        if chat is None:
            unattributed.append(c)
            continue
        if chat not in names:
            a.add("session-trailer", f"{c['sha']}/unregistered",
                  f"commit {c['sha']} is from chat {chat!r}, which is not registered",
                  "D-301: a chat registers in working/chat_register.csv before its first claim "
                  "or commit.", serious=True, chat=chat, commit=c["sha"], at=c["at"])
        when = _parse(c["at"])
        for f in c["files"]:
            cl = doc_lock.claim_for_path(f)
            if not cl:
                continue
            h = holder_at(timeline, cl, when)
            if h and h != chat:
                a.add("claim-coverage", f"{c['sha']}/{f}",
                      f"{f} was changed by chat {chat!r} while {cl} was held by {h!r}",
                      "CLAUDE.md §4b: a claim held by another chat is a refusal, not advice.",
                      serious=True, chat=chat, commit=c["sha"], file=f, at=c["at"])
    if unattributed:
        a.add("claim-coverage", "unattributable",
              f"{len(unattributed)} commit(s) in the window could not be attributed to a chat",
              "Their claim coverage is UNKNOWN, not clean: no Claude-Session trailer matched a "
              "register row's link. Reported as a gap in the evidence, not as a breach.",
              serious=False,
              evidence=", ".join(c["sha"] for c in unattributed[:10])
                        + (" …" if len(unattributed) > 10 else ""))


def rule_ship_verdict(a: Audit, board: dict) -> None:
    """A ship quotes a check_all verdict, and that verdict is OK."""
    ship = (board or {}).get("ship") or {}
    if not ship or ship.get("state") not in ("done", "failed"):
        return
    v = (ship.get("verdict") or "").strip()
    line = (ship.get("ship_line") or "")
    if not v:
        a.add("ship-verdict", ship.get("id", "ship"),
              f"ship {ship.get('id', '?')} quotes no check_all verdict",
              "CLAUDE.md §1: run check_all before you commit and quote the verdict.",
              serious=False, evidence=line[:160])
    elif v.upper() not in ("OK",):
        a.add("ship-verdict", ship.get("id", "ship"),
              f"ship {ship.get('id', '?')} shipped on a {v} verdict",
              "A red gate after a ship is a defect in the work (D-213), never a reason to ship.",
              serious=True, evidence=line[:160])


def rule_doc_versions(a: Audit, cs: list[dict]) -> None:
    """A versioned document was bumped, not edited in place.

    The ODTs are gitignored, so the committed surface is the mirror - and its generated header
    names both the source filename (which carries the version) and the source's sha256. A sha that
    moved while the version did not is an edit in place. Versions compare NUMERICALLY, through
    refresh_mirrors' own _version_key, because v1_9_46 sorts after v1_9_9 only that way."""
    try:
        import refresh_mirrors
        vkey = refresh_mirrors._version_key
    except Exception:                                                 # pragma: no cover
        def vkey(p):                                                  # noqa: ANN001
            m = VERSION_IN_NAME_RE.search(str(p))
            return [int(n) for n in re.split(r"[_.]", m.group(1))] if m else [-1]
    for c in cs:
        if c["private"]:
            continue
        for f in c["files"]:
            if not f.endswith(".md") or "/text/" not in f:
                continue
            new = _show(c["full"], f)
            old = _show(f"{c['full']}^", f)
            if not new or not old:
                continue
            mn, mo = MIRROR_HEAD_RE.search(new), MIRROR_HEAD_RE.search(old)
            if not mn or not mo:
                continue
            if mn.group(2) == mo.group(2):
                continue                           # the source did not change
            # NOT every document is versioned, and this rule is only about the ones that are.
            # refresh_mirrors.SOURCES carries a `versioned` flag: the report chapters, the master
            # report.odm, the public summaries and the web manuals have STABLE filenames by design,
            # so "the content moved and the filename did not" is their normal state, not a defect.
            # Measured 2026-11-05 before this guard: 5 findings, all of them report chapters
            # (report8/9/12/15 and report.odm) from two legitimate commits - a rule that would have
            # fired on every report edit for ever. The version in the filename is the test.
            if not (VERSION_IN_NAME_RE.search(mn.group(1))
                    and VERSION_IN_NAME_RE.search(mo.group(1))):
                continue
            if mn.group(1) == mo.group(1):
                a.add("doc-version", f"{c['sha']}/{f}",
                      f"{pathlib.Path(mn.group(1)).name} changed content without a version bump",
                      "CLAUDE.md §3: edit Doc_v1_9_46.odt, write Doc_v1_9_47.odt. The mirror's "
                      "source-sha256 moved while its source filename did not.",
                      serious=False, commit=c["sha"], file=f, at=c["at"],
                      evidence=f"{mo.group(2)} -> {mn.group(2)}")
            elif vkey(pathlib.Path(mn.group(1))) < vkey(pathlib.Path(mo.group(1))):
                a.add("doc-version", f"{c['sha']}/{f}/backwards",
                      f"{f} now mirrors an OLDER version of its source",
                      "A machine holding a stale ODT regenerated the mirror from it (CLAUDE.md §4b).",
                      serious=True, commit=c["sha"], file=f, at=c["at"],
                      evidence=f"{pathlib.Path(mo.group(1)).name} -> {pathlib.Path(mn.group(1)).name}")


def rule_script_versions(a: Audit, cs: list[dict]) -> None:
    """A script edit bumps `__version__`, and a PIPELINE script's edit also moves its ledger row."""
    for c in cs:
        if c["private"]:
            continue
        scripts = [f for f in c["files"]
                   if (f.startswith("src/") or f.startswith("tools/")) and f.endswith(".py")
                   or f == "run_analysis.py"]
        ledger_touched = "notes/ledgers/SCRIPT_LEDGER.md" in c["files"]
        for f in scripts:
            new, old = _show(c["full"], f), _show(f"{c['full']}^", f)
            if not new or not old:
                continue                            # a new file has nothing to bump from
            def vline(t: str) -> str:
                m = re.search(r"^__version__\s*=.*$", t, re.M)
                return m.group(0) if m else ""
            if not SCRIPT_VERSION_RE.search(new):
                continue                            # no __version__ at all: not this rule's business
            if vline(new) == vline(old):
                a.add("script-version", f"{c['sha']}/{f}",
                      f"{f} was edited without bumping __version__",
                      "Every script's version is its own account of what changed.",
                      serious=False, commit=c["sha"], file=f, at=c["at"],
                      evidence=vline(new)[:120])
            elif PIPELINE_SCRIPT_RE.match(f) and not ledger_touched:
                a.add("script-version", f"{c['sha']}/{f}/ledger",
                      f"{f} bumped __version__ with no SCRIPT_LEDGER row in the same commit",
                      "§4d: SCRIPT_LEDGER is the anti-drift spine, and it rots when the bump and "
                      "the row part company.", serious=False, commit=c["sha"], file=f, at=c["at"],
                      evidence=vline(new)[:120])


def rule_chats(a: Audit, reg: list[dict], claims: dict) -> None:
    """A registered chat with activity has a status; a `done` chat holds no claim.

    MEASURED TRAP (2026-11-05, and the brief says so): the register's `claim` column records what a
    chat is registered to work on. It is NOT a live hold. `control board` is `done` with
    `claim=tools` in the register while `tools` is free on the board. So this reads the LOCK - which
    is the only thing that knows who holds what - and never the register's column."""
    held_by = {}
    for name, c in (claims or {}).items():
        if c and c.get("chat"):
            held_by.setdefault(c["chat"], []).append(name)
    for r in reg:
        chat = (r.get("chat") or "").strip()
        if not chat:
            continue
        status = (r.get("status") or "").strip()
        if (r.get("touched") or r.get("opened")) and not status:
            a.add("chat-status", chat, f"chat {chat!r} has activity and no status",
                  "Set it when the work finishes: python3 tools/chat_register.py status "
                  f"--chat {chat!r} --set done --outcome \"…\"", serious=False, chat=chat,
                  evidence=f"touched {r.get('touched') or r.get('opened')}")
        if status == "done" and held_by.get(chat):
            a.add("chat-status", f"{chat}/holds",
                  f"chat {chat!r} is done and still holds {', '.join(held_by[chat])}",
                  "A done chat's claim blocks the next one. Release it (doc_lock release), or say "
                  "in the handover why it stays held.", serious=False, chat=chat,
                  evidence=", ".join(held_by[chat]))


def rule_claim_age(a: Audit, claims: dict) -> None:
    """A claim past the abandoned age. Staleness is measured from last ACTIVITY (D-300), which is
    doc_lock's own definition - read from it rather than restated here."""
    limit = doc_lock.abandoned_hours()
    for name, c in (claims or {}).items():
        if not c or not c.get("chat"):
            continue
        age = doc_lock.age_h(c)
        if age is not None and age >= limit:
            a.add("claim-stale", name,
                  f"{name} has had no activity for {age:.0f} h (abandoned at {limit:.0f} h)",
                  f"Held by {c['chat']!r}. A flag never releases anything (D-300): "
                  f"release --force --by NAME is the only override, and it is logged.",
                  serious=True, chat=c.get("chat"), evidence=f"since {c.get('since')}")


def rule_overrides(a: Audit, since: datetime.datetime | None) -> None:
    """A forced take or release in the window. Every one is logged (D-300 R7); this reads that log."""
    path = REPO / doc_lock.OVERRIDES
    if not path.exists():
        return
    try:
        import register_io
        rows = register_io.read_rows(path)
    except Exception:                                                 # pragma: no cover
        return
    for r in rows:
        when = _parse(r.get("when"))
        if since and when and when < since:
            continue
        a.add("override", f"{r.get('when')}/{r.get('claim')}",
              f"{r.get('action')} of {r.get('claim')} by {r.get('by') or 'unsigned'}",
              f"From {r.get('from_chat') or '-'} to {r.get('to_chat') or '-'}. "
              f"{r.get('note') or ''}".strip(),
              serious=True, chat=r.get("to_chat") or r.get("from_chat"),
              at=r.get("when") or "", evidence=r.get("note", "")[:120])


def rule_gate(a: Audit, newly_red: list[str]) -> None:
    """check_all's verdict, READ and not re-run (the brief's main warning)."""
    if not GATE_SUMMARY.exists():
        a.add("gate-verdict", "no-summary", "no check_all summary to read",
              f"Run bash tools/check_all.sh (1.34.0 writes {GATE_SUMMARY.name}).", serious=False)
        return
    try:
        d = json.loads(GATE_SUMMARY.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        a.add("gate-verdict", "unreadable", f"{GATE_SUMMARY.name} is not readable", str(e),
              serious=False)
        return
    v = (d.get("verdict") or "").upper()
    failed = [s["key"] for s in (d.get("sections") or []) if s.get("verdict") != "OK"]
    if v not in ("OK", ""):
        a.add("gate-verdict", f"{d.get('generated', '?')}",
              f"the last check_all was {v}", f"{len(failed)} section(s) red: "
              + (", ".join(failed[:6]) or "none named"), serious=True,
              at=d.get("generated", ""), evidence=f"host {d.get('host', '?')}")
    for key in (newly_red or []):
        a.add("gate-verdict", f"newly-red/{key}", f"{key} is newly red",
              "It passed on the previous run.", serious=True, at=d.get("generated", ""))


def rule_ships_and_repos(a: Audit, board: dict) -> None:
    """A ship waiting more than a day; a repository behind origin (spec §7)."""
    b = board or {}
    # work_board exposes `ship_request_waiting` (the file's existence) and not the request itself,
    # so the request is read here. CLAUDE.md §4b gives its shape: id, requested_at, requested_by,
    # message, chat, claims, paths. Measured 2026-11-05: reading b["ship_request"] gave {} always,
    # so this rule would have fired with no id and no age at all.
    req = {}
    rf = REPO / "working/.ship_request"
    if rf.exists():
        try:
            req = json.loads(rf.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError):
            req = {}
    if b.get("ship_request_waiting") or req:
        when = _parse(req.get("requested_at"))
        hours = (now() - when).total_seconds() / 3600 if when else None
        if hours is None or hours >= SHIP_WAIT_HOURS:
            a.add("ship-waiting", req.get("id", "waiting"),
                  "a ship request has been waiting"
                  + (f" {hours:.0f} h" if hours is not None else ""),
                  f"Requested by {req.get('requested_by') or 'unknown'}: "
                  f"{(req.get('message') or '')[:100]}", serious=True,
                  at=req.get("requested_at", ""))
    for r in b.get("repos") or []:
        if r.get("present") and (r.get("behind") or 0) > 0:
            a.add("repo-behind", r.get("name", "?"),
                  f"the {r.get('name')} repository is {r['behind']} commit(s) behind origin",
                  "A pull is owed before anything is regenerated from this tree.",
                  serious=True, evidence=f"head {r.get('head')} vs origin {r.get('origin_main')}")


def rule_stale_branches(a: Audit) -> None:
    """Branches pushed and unmerged for over a week - hq_snapshot already measures them, so this
    reads that one implementation and only decides whether each is a finding."""
    try:
        import hq_snapshot
        branches = hq_snapshot.stale_branches()
    except Exception:                                                 # pragma: no cover
        return
    for b in branches:
        a.add("stale-branch", b["branch"],
              f"{b['branch']} has been unmerged for {b['days']} days",
              "Merge it, or record in working/rule_audit_suppress.csv why it stays apart "
              "(a reason is required; a bare row suppresses nothing).",
              serious=False, at=b.get("last_commit", ""), evidence=b.get("subject", "")[:120])


# ── the run ─────────────────────────────────────────────────────────────────────────────────

def read_state() -> dict:
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_state(payload: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({
        "last_run": payload["generated"],
        "public": _git("rev-parse", "HEAD")[:40],
        "private": _git("rev-parse", "HEAD", private=True)[:40],
        "findings": payload["counts"],
    }, indent=2) + "\n", encoding="utf-8")


def audit(since: str | None = None, days: int = SINCE_DAYS, board: dict | None = None,
          newly_red: list[str] | None = None) -> dict:
    """The payload. `board` and `newly_red` come from hq_snapshot when it calls this, so neither
    work_board nor the history is computed twice in one HQ pass."""
    state, why = doc_lock.store_state()
    if state == "ABSENT":
        return {"generated": stamp(), "store": state, "store_why": why, "can_report": False,
                "window": {}, "findings": [], "suppressed": [],
                "counts": {"total": 0, "serious": 0, "suppressed": 0},
                "why_nothing": "the private store is absent, so there is no lock, no register and "
                               "no decision log to audit: this is UNKNOWN, not all clear (D-302)."}
    st = read_state()
    pub_since = since or st.get("public") or None
    prv_since = st.get("private") if not since else None
    if pub_since and not _git("rev-parse", "--verify", f"{pub_since}^{{commit}}"):
        pub_since = None
    if prv_since and not _git("rev-parse", "--verify", f"{prv_since}^{{commit}}", private=True):
        prv_since = None
    cs = commits(private=False, since=pub_since, days=days) \
        + commits(private=True, since=prv_since, days=days)
    cs.sort(key=lambda c: c["at"])
    window_from = _parse(cs[0]["at"]) if cs else (now() - datetime.timedelta(days=days))

    if board is None:
        import work_board
        board = work_board.collect()
    claims = (board or {}).get("claims") or {}
    reg = chat_register.rows() if hasattr(chat_register, "rows") else []

    a = Audit()
    tl = lock_timeline()
    rule_handover(a, cs)
    rule_decision_fields(a, cs)
    rule_claims_and_trailers(a, cs, tl, reg)
    rule_ship_verdict(a, board)
    rule_doc_versions(a, cs)
    rule_script_versions(a, cs)
    rule_chats(a, reg, claims)
    rule_claim_age(a, claims)
    rule_overrides(a, window_from)
    rule_gate(a, newly_red or [])
    rule_ships_and_repos(a, board)
    rule_stale_branches(a)
    a.overflow()

    serious = len([f for f in a.findings if f["serious"]])
    return {"generated": stamp(), "store": state, "store_why": why, "can_report": True,
            "window": {"since_public": pub_since or f"{days} days", "commits": len(cs),
                       "from": window_from.strftime("%Y-%m-%dT%H:%M:%SZ") if window_from else "",
                       "last_run": st.get("last_run", "")},
            "findings": a.findings, "suppressed": a.suppressed,
            "counts": {"total": len(a.findings), "serious": serious,
                       "suppressed": len(a.suppressed),
                       "by_rule": dict(sorted(a._counts.items()))}}


def report(p: dict) -> None:
    if not p.get("can_report"):
        print(f"  rule_audit: CANNOT AUDIT — {p.get('why_nothing')}")
        return
    w = p["window"]
    print(f"  window: {w['commits']} commit(s) since {w['since_public']}"
          + (f" (last run {w['last_run']})" if w.get("last_run") else " (no previous run)"))
    if not p["findings"]:
        print("  no findings.")
    for f in sorted(p["findings"], key=lambda x: (not x["serious"], x["rule"])):
        print(f"  {'SERIOUS' if f['serious'] else 'note   '}  [{f['rule']}] {f['title']}")
        if f["detail"]:
            print(f"            {f['detail']}")
        if f["evidence"]:
            print(f"            evidence: {f['evidence']}")
    for s in p["suppressed"]:
        print(f"  suppressed [{s['rule']}] {s['title']} — {s['reason']}"
              + (f" (by {s['by']})" if s.get("by") else ""))
    c = p["counts"]
    print(f"  {c['total']} finding(s), {c['serious']} serious, {c['suppressed']} suppressed")


def check() -> int:
    """The gate (§4d: a generated artefact with no --check rots silently).

    Cheap by construction: it asks whether this module can audit at all and whether anything
    SERIOUS is outstanding - it does not re-run the gate it reads, and a note-level finding never
    fails it, because an open finding is work outstanding and not a broken check."""
    state, why = doc_lock.store_state()
    if state == "ABSENT":
        print(f"  rule_audit: SKIP — {why}")
        return 0
    p = audit()
    c = p["counts"]
    notes = [f"{c['total']} finding(s)"]
    if c["suppressed"]:
        notes.append(f"{c['suppressed']} suppressed with a reason")
    if not p["window"].get("last_run"):
        notes.append(f"no previous run: the window is the last {SINCE_DAYS} days")
    if c["serious"]:
        print(f"  rule_audit: {c['serious']} SERIOUS finding(s) — " + "; ".join(notes))
        for f in p["findings"]:
            if f["serious"]:
                print(f"    SERIOUS [{f['rule']}] {f['title']}")
        print("    These are reported, not gated: rule_audit reports and never intervenes (D-302).")
        return 0
    print("  rule_audit: OK — " + "; ".join(notes))
    return 0


# ── selftest ────────────────────────────────────────────────────────────────────────────────

def _mkrepo(d: pathlib.Path, lock: dict | None = None) -> pathlib.Path:
    """A throwaway tree with BOTH git directories over it, as the real one has (CLAUDE.md §4f)."""
    (d / "working/updates").mkdir(parents=True, exist_ok=True)
    (d / "tools").mkdir(exist_ok=True)
    (d / "src").mkdir(exist_ok=True)
    (d / "notes/ledgers").mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    # Two git directories over one tree, as the real one has: .git plain, and .git-working
    # pointed at the same work tree.
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(d), capture_output=True, env=env)
    subprocess.run(["git", f"--git-dir={d / '.git-working'}", f"--work-tree={d}",
                    "init", "-q", "-b", "main"], cwd=str(d), capture_output=True, env=env)
    if lock is not None:
        (d / "working/DOCUMENT_LOCK.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")
    return d


def _commit(tree: pathlib.Path, paths: list[str], message: str, private: bool = False,
            when: str | None = None) -> str:
    gd = tree / (".git-working" if private else ".git")
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    if when:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when
    base = ["git", f"--git-dir={gd}", f"--work-tree={tree}"]
    subprocess.run(base + ["add", "--"] + paths, cwd=str(tree), capture_output=True, env=env)
    subprocess.run(base + ["commit", "-q", "-m", message], cwd=str(tree), capture_output=True,
                   env=env)
    p = subprocess.run(base + ["rev-parse", "HEAD"], cwd=str(tree), capture_output=True,
                       text=True, env=env)
    return p.stdout.strip()[:8]


def _run(args: list[str], tree: pathlib.Path, **env_extra) -> tuple[int, str]:
    env = dict(os.environ, NRG_REPO_ROOT=str(tree))
    # Every NRG_* override that would reach into a throwaway tree is cleared, not just the three
    # doc_lock's own harness clears. MEASURED 2026-11-05: a gate run with
    # NRG_GATE_SUMMARY=scratch/check_all_summary_ruleaudit.json (set to stop two concurrent
    # check_all runs clobbering one file, T-146) made the selftest FAIL inside check_all while
    # passing when run by hand - test 12 writes scratch/check_all_summary.json in its tree and the
    # module was looking for the inherited name. A selftest that depends on the caller's
    # environment is not a selftest.
    for k in ("NRG_CHAT", "NRG_NO_PRIVATE_STORE", "NRG_SESSION_LINK", "NRG_GATE_SUMMARY",
              "NRG_DOC_LOCK_FILE", "NRG_RULE_AUDIT_SINCE", "NRG_CLAIM_STALE_HOURS",
              "NRG_CLAIM_ABANDONED_HOURS"):
        env.pop(k, None)
    env.update({k: v for k, v in env_extra.items() if v is not None})
    p = subprocess.run([sys.executable, str(HERE / "tools/rule_audit.py"), *args],
                       capture_output=True, text=True, env=env, cwd=str(HERE))
    # stdout and stderr are kept APART on purpose: override_warnings() writes to stderr, and a
    # merged stream made every --json payload in this selftest unparseable (measured, first run).
    return p.returncode, p.stdout, p.stderr


def _selftest() -> int:
    """Each branch is exercised BOTH ways - fires and does not fire - because the phase-1/2 build's
    three defects were all found by reading output rather than by a test that could fail."""
    import tempfile
    ok = True

    def check_(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        print(f"  {'ok  ' if cond else 'FAIL'}  {label}")
        if not cond:
            ok = False
            if detail:
                print("          " + detail.strip().replace("\n", "\n          ")[:1400])

    def payload(tree: pathlib.Path, **env) -> dict:
        rc, out, _err = _run(["--json"], tree, **env)
        try:
            return json.loads(out)
        except ValueError:
            print("          could not parse --json: " + out[:800])
            return {}

    def rules_of(p: dict) -> set:
        return {f["rule"] for f in p.get("findings", [])}

    def subjects_of(p: dict, rule: str) -> set:
        return {f["subject"] for f in p.get("findings", []) if f["rule"] == rule}

    with tempfile.TemporaryDirectory() as td:
        T = pathlib.Path(td)

        # 1. No private store: it reports that it cannot audit, and never "all clear" (D-300/D-302).
        t1 = T / "public_only"
        _mkrepo(t1, lock=None)
        (t1 / "a.txt").write_text("x", encoding="utf-8")
        _commit(t1, ["a.txt"], "first")
        import shutil
        shutil.rmtree(t1 / ".git-working", ignore_errors=True)
        p = payload(t1)
        check_("1a no store: can_report is False", p.get("can_report") is False, json.dumps(p)[:600])
        check_("1b no store: no findings are invented", p.get("findings") == [], json.dumps(p)[:400])
        check_("1c no store: it says why, and does not say all clear",
               "UNKNOWN, not all clear" in (p.get("why_nothing") or ""), str(p.get("why_nothing")))
        rc, out, err = _run(["--check"], t1); out += err
        check_("1d no store: --check SKIPs", rc == 0 and "SKIP" in out, out)

        # 2. A commit under another chat's claim is a SERIOUS claim-coverage finding; the same
        #    commit by the holding chat is not. The register's link is what attributes it.
        t2 = T / "coverage"
        _mkrepo(t2, lock={"holder": None, "claims": {}})
        reg = t2 / "working/chat_register.csv"
        reg.write_text("chat,kind,claim,mode,link,opened,touched,status,purpose,outcome,registered_by\n"
                       "Paper M,document,doc:PaperM,laptop,sess_PM,2026-11-01,2026-11-01,active,x,,Paper M\n"
                       "tools chat,tools,tools,laptop,sess_T,2026-11-01,2026-11-01,active,x,,tools chat\n",
                       encoding="utf-8")
        (t2 / "working/DOCUMENT_LOCK.json").write_text(json.dumps(
            {"holder": None, "claims": {"tools": {"chat": "tools chat", "since": "2026-11-01T00:00:00Z",
                                                  "touched": stamp()}}}, indent=2), encoding="utf-8")
        _commit(t2, ["working/chat_register.csv", "working/DOCUMENT_LOCK.json"],
                "the register and the lock", private=True)
        (t2 / "tools/thing.py").write_text("__version__ = '1.0.0'\n", encoding="utf-8")
        _commit(t2, ["tools/thing.py"],
                "edit a tools file\n\nClaude-Session: sess_PM\n")
        p = payload(t2)
        check_("2a a commit under another chat's claim is found",
               "claim-coverage" in rules_of(p), json.dumps(p.get("findings"), indent=1)[:900])
        cov = [f for f in p["findings"] if f["rule"] == "claim-coverage" and f["file"]]
        check_("2b and it is SERIOUS, naming the chat, the file and the holder",
               bool(cov) and cov[0]["serious"] and cov[0]["chat"] == "Paper M"
               and cov[0]["file"] == "tools/thing.py" and "tools chat" in cov[0]["title"],
               json.dumps(cov, indent=1)[:700])
        # The branch bites: the SAME edit, from the chat that holds the claim, is not a finding.
        # Built as its own tree rather than by resetting a copy of t2 - public has only one commit
        # there, so a `reset --hard HEAD~1` had no parent and silently left both in the window
        # (measured, first run of this selftest).
        t2b = T / "coverage_ok"
        _mkrepo(t2b, lock=None)
        (t2b / "working/chat_register.csv").write_text(
            (t2 / "working/chat_register.csv").read_text(encoding="utf-8"), encoding="utf-8")
        (t2b / "working/DOCUMENT_LOCK.json").write_text(
            (t2 / "working/DOCUMENT_LOCK.json").read_text(encoding="utf-8"), encoding="utf-8")
        _commit(t2b, ["working/chat_register.csv", "working/DOCUMENT_LOCK.json"],
                "the register and the lock", private=True)
        (t2b / "tools/thing.py").write_text("__version__ = '1.0.0'\n", encoding="utf-8")
        _commit(t2b, ["tools/thing.py"], "edit a tools file\n\nClaude-Session: sess_T\n")
        p2 = payload(t2b)
        check_("2c the holding chat's own commit is NOT a claim-coverage finding",
               not [f for f in p2["findings"] if f["rule"] == "claim-coverage" and f["file"]],
               json.dumps([f for f in p2["findings"] if f["rule"] == "claim-coverage"], indent=1)[:700])

        # 3. A commit with no trailer is SERIOUS; one with a trailer whose chat is registered is not.
        # 3. A commit with no trailer is SERIOUS; one whose chat is registered raises nothing.
        #    t2's commits all carry trailers, so its ONLY untrailered commit is the private one -
        #    which is the honest expectation, and the assertion says so rather than being
        #    unfalsifiable (the first version of this line was `... or True and ...`).
        p2a = payload(t2)
        check_("3a a trailered commit raises no trailer finding against itself",
               not [f for f in p2a["findings"]
                    if f["rule"] == "session-trailer" and f["commit"]
                    and "edit a tools file" in f.get("evidence", "")],
               json.dumps([f for f in p2a["findings"]
                           if f["rule"] == "session-trailer"], indent=1)[:600])
        t3 = T / "trailer"
        _mkrepo(t3, lock={"holder": None, "claims": {}})
        (t3 / "working/chat_register.csv").write_text(
            "chat,kind,claim,mode,link,opened,touched,status,purpose,outcome,registered_by\n"
            "c,tools,tools,laptop,sess_C,2026-11-01,2026-11-01,active,x,,c\n", encoding="utf-8")
        _commit(t3, ["working/chat_register.csv"], "register", private=True)
        (t3 / "a.txt").write_text("1", encoding="utf-8")
        _commit(t3, ["a.txt"], "no trailer at all")
        p3 = payload(t3)
        st = [f for f in p3["findings"] if f["rule"] == "session-trailer"]
        check_("3b a commit with no trailer is a serious finding",
               bool(st) and st[0]["serious"], json.dumps(st, indent=1)[:500])
        (t3 / "a.txt").write_text("2", encoding="utf-8")
        _commit(t3, ["a.txt"], "with a trailer\n\nClaude-Session: sess_C\n")
        p3b = payload(t3, NRG_RULE_AUDIT_SINCE="HEAD~1")
        check_("3c the branch bites: a trailered commit from a registered chat raises none",
               not [f for f in payload(t3)["findings"]
                    if f["rule"] == "session-trailer" and f["commit"]
                    and "with a trailer" in f.get("evidence", "")],
               json.dumps(p3b.get("findings"), indent=1)[:500])

        # 4. A commit with no handover entry is a finding; with a complete one, none.
        t4 = T / "handover"
        _mkrepo(t4, lock={"holder": None, "claims": {}})
        (t4 / "a.txt").write_text("1", encoding="utf-8")
        _commit(t4, ["a.txt"], "work with no record")
        check_("4a a commit day with no handover entry is found",
               "handover-entry" in rules_of(payload(t4)),
               json.dumps(payload(t4).get("findings"), indent=1)[:600])
        today = now().astimezone().date().isoformat()
        # The fixture's brief is named `BRIEF_UNDER_TEST` and not a filename: docref_lint scans
        # source for cited documents, and the first version of this fixture named a plausible
        # one-letter markdown file, which that gate read as a NEW reference to a document that does
        # not exist - correctly. A test fixture must not look like a citation.
        (t4 / "working/updates/HANDOVER_NOTE.md").write_text(
            f"# notes\n\n## {today} — a session\n- **Why:** brief `BRIEF_UNDER_TEST`\n"
            "- Decisions recorded this session: none.\n", encoding="utf-8")
        _commit(t4, ["working/updates/HANDOVER_NOTE.md"], "the record", private=True)
        check_("4b the branch bites: a complete entry raises no handover-entry finding",
               "handover-entry" not in rules_of(payload(t4)),
               json.dumps([f for f in payload(t4)["findings"]
                           if f["rule"] == "handover-entry"], indent=1)[:600])
        (t4 / "working/updates/HANDOVER_NOTE.md").write_text(
            f"# notes\n\n## {today} — a session\n- it happened\n", encoding="utf-8")
        _commit(t4, ["working/updates/HANDOVER_NOTE.md"], "a thin record", private=True)
        hv = [f for f in payload(t4)["findings"] if f["rule"] == "handover-entry"]
        check_("4c an entry with neither provenance nor D-numbers names both",
               bool(hv) and "provenance" in hv[0]["detail"] and "D-numbers" in hv[0]["detail"],
               json.dumps(hv, indent=1)[:600])

        # 5. A new decision without Retires/Revisit-if is found; with both, not.
        t5 = T / "decisions"
        _mkrepo(t5, lock={"holder": None, "claims": {}})
        dl = t5 / "working/DECISION_LOG.md"
        dl.write_text("# log\n\n## D-001 — the first\n**Rationale:** x\nRetires: none\n"
                      "Revisit-if: never\n", encoding="utf-8")
        _commit(t5, ["working/DECISION_LOG.md"], "d1", private=True)
        dl.write_text(dl.read_text(encoding="utf-8")
                      + "\n## D-002 — the second\n**Rationale:** y\n", encoding="utf-8")
        _commit(t5, ["working/DECISION_LOG.md"], "d2", private=True)
        df = [f for f in payload(t5)["findings"] if f["rule"] == "decision-fields"]
        check_("5a a new decision with neither field is found, by its D-number",
               bool(df) and df[0]["subject"] == "D-002", json.dumps(df, indent=1)[:500])
        check_("5b and the PRE-EXISTING entry is not re-flagged",
               "D-001" not in subjects_of(payload(t5), "decision-fields"),
               json.dumps(df, indent=1)[:400])
        dl.write_text(dl.read_text(encoding="utf-8").replace(
            "## D-002 — the second\n**Rationale:** y\n",
            "## D-002 — the second\n**Rationale:** y\nRetires: none\nRevisit-if: never\n"),
            encoding="utf-8")
        _commit(t5, ["working/DECISION_LOG.md"], "d2 fields", private=True)
        check_("5c the branch bites: both fields present raises nothing",
               not [f for f in payload(t5)["findings"] if f["rule"] == "decision-fields"],
               json.dumps([f for f in payload(t5)["findings"]
                           if f["rule"] == "decision-fields"], indent=1)[:500])

        # 6. A script edited without a __version__ bump is found; a bump is not. A pipeline script
        #    bumped without its SCRIPT_LEDGER row is found separately.
        t6 = T / "scripts"
        _mkrepo(t6, lock={"holder": None, "claims": {}})
        (t6 / "src/55_x.py").write_text("__version__ = \"1.0.0\"\nprint(1)\n", encoding="utf-8")
        (t6 / "notes/ledgers/SCRIPT_LEDGER.md").write_text("| 55 | 55_x.py | 1.0.0 |\n",
                                                           encoding="utf-8")
        _commit(t6, ["src/55_x.py", "notes/ledgers/SCRIPT_LEDGER.md"], "script and ledger")
        (t6 / "src/55_x.py").write_text("__version__ = \"1.0.0\"\nprint(2)\n", encoding="utf-8")
        _commit(t6, ["src/55_x.py"], "edit, no bump")
        sv = [f for f in payload(t6)["findings"] if f["rule"] == "script-version"]
        check_("6a an edit with no __version__ bump is found",
               bool(sv) and "without bumping" in sv[0]["title"], json.dumps(sv, indent=1)[:500])
        (t6 / "src/55_x.py").write_text("__version__ = \"1.1.0\"\nprint(3)\n", encoding="utf-8")
        _commit(t6, ["src/55_x.py"], "bump, no ledger")
        sv2 = [f for f in payload(t6)["findings"]
               if f["rule"] == "script-version" and f["subject"].endswith("/ledger")]
        check_("6b a pipeline bump with no SCRIPT_LEDGER row in the commit is found",
               bool(sv2), json.dumps([f for f in payload(t6)["findings"]
                                      if f["rule"] == "script-version"], indent=1)[:700])
        (t6 / "src/55_x.py").write_text("__version__ = \"1.2.0\"\nprint(4)\n", encoding="utf-8")
        (t6 / "notes/ledgers/SCRIPT_LEDGER.md").write_text("| 55 | 55_x.py | 1.2.0 |\n",
                                                           encoding="utf-8")
        _commit(t6, ["src/55_x.py", "notes/ledgers/SCRIPT_LEDGER.md"], "bump with the ledger")
        last = [f for f in payload(t6, NRG_RULE_AUDIT_SINCE="HEAD~1")["findings"]
                if f["rule"] == "script-version"]
        check_("6c the branch bites: a bump WITH its ledger row raises nothing", not last,
               json.dumps(last, indent=1)[:500])

        # 7. A mirror whose source-sha256 moved while its version did not is an edit in place.
        t7 = T / "docs"
        _mkrepo(t7, lock={"holder": None, "claims": {}})
        (t7 / "docs/papers/paper_M/text").mkdir(parents=True, exist_ok=True)
        mir = t7 / "docs/papers/paper_M/text/PaperM.md"
        head = ("<!-- GENERATED MIRROR of docs/papers/paper_M/PaperM_v1_42.odt — do not edit. "
                "source-sha256={} pandoc=3.1.3 -->\n")
        mir.write_text(head.format("aaaa1111") + "text\n", encoding="utf-8")
        _commit(t7, [str(mir.relative_to(t7))], "mirror")
        mir.write_text(head.format("bbbb2222") + "edited\n", encoding="utf-8")
        _commit(t7, [str(mir.relative_to(t7))], "same version, new content")
        dv = [f for f in payload(t7)["findings"] if f["rule"] == "doc-version"]
        check_("7a an edit in place (sha moved, version did not) is found",
               bool(dv) and "without a version bump" in dv[0]["title"],
               json.dumps(dv, indent=1)[:600])
        mir.write_text(head.replace("v1_42", "v1_43").format("cccc3333") + "bumped\n",
                       encoding="utf-8")
        _commit(t7, [str(mir.relative_to(t7))], "bumped properly")
        dv2 = [f for f in payload(t7, NRG_RULE_AUDIT_SINCE="HEAD~1")["findings"]
               if f["rule"] == "doc-version"]
        check_("7b the branch bites: a bumped version raises nothing", not dv2,
               json.dumps(dv2, indent=1)[:500])
        mir.write_text(head.replace("v1_42", "v1_9").format("dddd4444") + "reverted\n",
                       encoding="utf-8")
        _commit(t7, [str(mir.relative_to(t7))], "mirror from a stale ODT")
        dv3 = [f for f in payload(t7, NRG_RULE_AUDIT_SINCE="HEAD~1")["findings"]
               if f["rule"] == "doc-version"]
        check_("7c v1_9 after v1_43 is caught, so versions compare NUMERICALLY",
               bool(dv3) and dv3[0]["serious"] and "OLDER" in dv3[0]["title"],
               json.dumps(dv3, indent=1)[:600])

        # 7d. An UNVERSIONED document - a report chapter, the master, a public summary - has a
        #     stable filename by design, so a moved sha is its normal state. Without this branch the
        #     rule fired on 5 legitimate report commits in the real tree (measured 2026-11-05).
        unv = t7 / "report_edits/text/report8.md"
        unv.parent.mkdir(parents=True, exist_ok=True)
        uhead = ("<!-- GENERATED MIRROR of report_edits/odt/report8.odt — do not edit. "
                 "source-sha256={} pandoc=3.1.3 -->\n")
        unv.write_text(uhead.format("1111aaaa") + "chapter\n", encoding="utf-8")
        _commit(t7, [str(unv.relative_to(t7))], "an unversioned chapter")
        unv.write_text(uhead.format("2222bbbb") + "chapter, edited\n", encoding="utf-8")
        _commit(t7, [str(unv.relative_to(t7))], "the chapter is edited, as chapters are")
        dv4 = [f for f in payload(t7, NRG_RULE_AUDIT_SINCE="HEAD~1")["findings"]
               if f["rule"] == "doc-version"]
        check_("7d an UNVERSIONED document's moved sha is not a finding", not dv4,
               json.dumps(dv4, indent=1)[:600])

        # 8. A done chat still holding a claim; and the measured trap - the register's `claim`
        #    column is not a hold, so a done chat whose claim is FREE raises nothing.
        t8 = T / "chats"
        _mkrepo(t8, lock={"holder": None, "claims": {}})
        (t8 / "working/chat_register.csv").write_text(
            "chat,kind,claim,mode,link,opened,touched,status,purpose,outcome,registered_by\n"
            "done chat,tools,tools,laptop,,2026-11-01,2026-11-01,done,x,y,done chat\n"
            "no status,tools,,laptop,,2026-11-01,2026-11-01,,x,,no status\n", encoding="utf-8")
        _commit(t8, ["working/chat_register.csv"], "register", private=True)
        p8 = payload(t8)
        check_("8a a chat with activity and no status is found",
               "no status" in subjects_of(p8, "chat-status"),
               json.dumps([f for f in p8["findings"] if f["rule"] == "chat-status"], indent=1)[:500])
        check_("8b THE TRAP: a done chat whose registered claim is FREE raises nothing",
               "done chat/holds" not in subjects_of(p8, "chat-status"),
               json.dumps([f for f in p8["findings"] if f["rule"] == "chat-status"], indent=1)[:500])
        (t8 / "working/DOCUMENT_LOCK.json").write_text(json.dumps(
            {"holder": None, "claims": {"tools": {"chat": "done chat",
                                                  "since": "2026-11-01T00:00:00Z",
                                                  "touched": stamp()}}}, indent=2), encoding="utf-8")
        _commit(t8, ["working/DOCUMENT_LOCK.json"], "it still holds it", private=True)
        check_("8c and when the LOCK says it holds it, it is found",
               "done chat/holds" in subjects_of(payload(t8), "chat-status"),
               json.dumps([f for f in payload(t8)["findings"]
                           if f["rule"] == "chat-status"], indent=1)[:500])

        # 9. A claim with no activity past the abandoned age is serious; a fresh one is not.
        t9 = T / "age"
        _mkrepo(t9, lock={"holder": None, "claims": {}})
        old = (now() - datetime.timedelta(hours=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
        (t9 / "working/DOCUMENT_LOCK.json").write_text(json.dumps(
            {"holder": None, "claims": {"tools": {"chat": "ghost", "since": old, "touched": old}}},
            indent=2), encoding="utf-8")
        _commit(t9, ["working/DOCUMENT_LOCK.json"], "an old claim", private=True)
        cs9 = [f for f in payload(t9)["findings"] if f["rule"] == "claim-stale"]
        check_("9a a claim with 100 h of no activity is serious",
               bool(cs9) and cs9[0]["serious"], json.dumps(cs9, indent=1)[:500])
        (t9 / "working/DOCUMENT_LOCK.json").write_text(json.dumps(
            {"holder": None, "claims": {"tools": {"chat": "ghost", "since": old,
                                                  "touched": stamp()}}}, indent=2), encoding="utf-8")
        _commit(t9, ["working/DOCUMENT_LOCK.json"], "it worked just now", private=True)
        check_("9b the branch bites: ACTIVITY, not age since `since`, clears it (D-300)",
               not [f for f in payload(t9)["findings"] if f["rule"] == "claim-stale"],
               json.dumps([f for f in payload(t9)["findings"]
                           if f["rule"] == "claim-stale"], indent=1)[:500])

        # 10. A forced take or release is serious, and is read from the override log.
        t10 = T / "overrides"
        _mkrepo(t10, lock={"holder": None, "claims": {}})
        (t10 / "working/claim_overrides.csv").write_text(
            "when,action,claim,from_chat,to_chat,by,note\n"
            f"{stamp()},forced-take,doc:PaperM,A,B,martin,took it over\n", encoding="utf-8")
        _commit(t10, ["working/claim_overrides.csv"], "an override", private=True)
        ov = [f for f in payload(t10)["findings"] if f["rule"] == "override"]
        check_("10a a forced take is a serious finding naming who signed it",
               bool(ov) and ov[0]["serious"] and "martin" in ov[0]["title"],
               json.dumps(ov, indent=1)[:500])

        # 11. Suppression needs a REASON; a bare row suppresses nothing.
        t11 = T / "suppress"
        _mkrepo(t11, lock={"holder": None, "claims": {}})
        (t11 / "working/claim_overrides.csv").write_text(
            "when,action,claim,from_chat,to_chat,by,note\n"
            f"{stamp()},forced-take,doc:X,A,B,martin,n\n", encoding="utf-8")
        _commit(t11, ["working/claim_overrides.csv"], "an override", private=True)
        ovr11 = [f for f in payload(t11)["findings"] if f["rule"] == "override"]
        check_("11pre an override finding exists to suppress", bool(ovr11),
               json.dumps(payload(t11).get("findings"), indent=1)[:400])
        subj = ovr11[0]["subject"] if ovr11 else "none"
        (t11 / "working/rule_audit_suppress.csv").write_text(
            "rule,subject,reason,by,when\n" f"override,{subj},,martin,{stamp()}\n", encoding="utf-8")
        check_("11a a suppression row with NO reason suppresses nothing",
               [f for f in payload(t11)["findings"] if f["rule"] == "override"],
               json.dumps(payload(t11).get("suppressed"), indent=1)[:400])
        (t11 / "working/rule_audit_suppress.csv").write_text(
            "rule,subject,reason,by,when\n"
            f"override,{subj},deliberate: Martin took it himself,martin,{stamp()}\n",
            encoding="utf-8")
        p11 = payload(t11)
        check_("11b with a reason it is suppressed, and the reason is reported",
               not [f for f in p11["findings"] if f["rule"] == "override"]
               and any("deliberate" in s.get("reason", "") for s in p11["suppressed"]),
               json.dumps(p11, indent=1)[:700])

        # 12. The gate's verdict is READ, never re-run, and a newly-red section is serious.
        t12 = T / "gate"
        _mkrepo(t12, lock={"holder": None, "claims": {}})
        (t12 / "scratch").mkdir(exist_ok=True)
        (t12 / "scratch/check_all_summary.json").write_text(json.dumps(
            {"generated": stamp(), "host": "h", "verdict": "FAIL",
             "sections": [{"index": 1, "key": "01 mirrors", "section": "mirrors",
                           "verdict": "FAIL", "seconds": 1}],
             "counts": {"sections": 1, "failed": 1}}), encoding="utf-8")
        g = [f for f in payload(t12)["findings"] if f["rule"] == "gate-verdict"]
        check_("12a a FAIL verdict in the summary is a serious finding",
               bool(g) and g[0]["serious"] and "FAIL" in g[0]["title"],
               json.dumps(g, indent=1)[:500])
        (t12 / "scratch/check_all_summary.json").write_text(json.dumps(
            {"generated": stamp(), "host": "h", "verdict": "OK",
             "sections": [{"index": 1, "key": "01 mirrors", "section": "mirrors",
                           "verdict": "OK", "seconds": 1}],
             "counts": {"sections": 1, "failed": 0}}), encoding="utf-8")
        check_("12b the branch bites: an OK verdict raises no gate finding",
               not [f for f in payload(t12)["findings"]
                    if f["rule"] == "gate-verdict" and f["serious"]],
               json.dumps([f for f in payload(t12)["findings"]
                           if f["rule"] == "gate-verdict"], indent=1)[:500])

        # 17. An old unmerged remote branch is a finding, and is suppressible with a reason -
        #     because notes/2026-11-04-water-balance-handovers stays apart deliberately. Without
        #     this test, disabling rule_stale_branches changed nothing at all (measured by
        #     mutating every rule in turn, 2026-11-05).
        t17 = T / "branches"
        _mkrepo(t17, lock={"holder": None, "claims": {}})
        (t17 / "working/DOCUMENT_LOCK.json").write_text(
            json.dumps({"holder": None, "claims": {}}, indent=2), encoding="utf-8")
        _commit(t17, ["working/DOCUMENT_LOCK.json"], "lock", private=True)
        (t17 / "a.txt").write_text("1", encoding="utf-8")
        _commit(t17, ["a.txt"], "on main")
        old_when = (now() - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S+0000")
        env17 = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                     GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
                     GIT_AUTHOR_DATE=old_when, GIT_COMMITTER_DATE=old_when)
        g17 = ["git", f"--git-dir={t17 / '.git'}", f"--work-tree={t17}"]
        subprocess.run(g17 + ["checkout", "-q", "-b", "side"], cwd=str(t17), capture_output=True)
        (t17 / "b.txt").write_text("2", encoding="utf-8")
        subprocess.run(g17 + ["add", "b.txt"], cwd=str(t17), capture_output=True, env=env17)
        subprocess.run(g17 + ["commit", "-q", "-m", "a month-old side branch"],
                       cwd=str(t17), capture_output=True, env=env17)
        side = subprocess.run(g17 + ["rev-parse", "HEAD"], cwd=str(t17), capture_output=True,
                              text=True).stdout.strip()
        subprocess.run(g17 + ["checkout", "-q", "main"], cwd=str(t17), capture_output=True)
        subprocess.run(g17 + ["update-ref", "refs/remotes/origin/side", side],
                       cwd=str(t17), capture_output=True)
        sb = [f for f in payload(t17)["findings"] if f["rule"] == "stale-branch"]
        check_("17a a remote branch unmerged for 30 days is found",
               bool(sb) and "origin/side" in sb[0]["subject"] and not sb[0]["serious"],
               json.dumps(payload(t17).get("findings"), indent=1)[:700])
        (t17 / "working/rule_audit_suppress.csv").write_text(
            "rule,subject,reason,by,when\n"
            f"stale-branch,origin/side,deliberate: it is for reading not merging,martin,{stamp()}\n",
            encoding="utf-8")
        p17 = payload(t17)
        check_("17b and a reason suppresses it, which is why the notes branch can stay apart",
               not [f for f in p17["findings"] if f["rule"] == "stale-branch"]
               and any(s["rule"] == "stale-branch" for s in p17["suppressed"]),
               json.dumps(p17.get("suppressed"), indent=1)[:500])
        subprocess.run(g17 + ["merge", "-q", "side"], cwd=str(t17), capture_output=True, env=env17)
        (t17 / "working/rule_audit_suppress.csv").unlink()
        check_("17c the branch bites: once merged it raises nothing",
               not [f for f in payload(t17)["findings"] if f["rule"] == "stale-branch"],
               json.dumps([f for f in payload(t17)["findings"]
                           if f["rule"] == "stale-branch"], indent=1)[:500])

        # 18. A ship that shipped on a non-OK verdict, and one that quotes none. Without these,
        #     disabling rule_ship_verdict changed nothing (mutation pass, 2026-11-05).
        t18 = T / "ships"
        _mkrepo(t18, lock={"holder": None, "claims": {}})
        (t18 / "working/DOCUMENT_LOCK.json").write_text(
            json.dumps({"holder": None, "claims": {}}, indent=2), encoding="utf-8")
        _commit(t18, ["working/DOCUMENT_LOCK.json"], "lock", private=True)
        (t18 / "working/.ship_status.json").write_text(json.dumps(
            {"id": "ship_x", "state": "done", "verdict": "FAIL",
             "ship_line": "SHIP: FAIL (pushed anyway)"}), encoding="utf-8")
        sv18 = [f for f in payload(t18)["findings"] if f["rule"] == "ship-verdict"]
        check_("18a a ship on a FAIL verdict is serious",
               bool(sv18) and sv18[0]["serious"] and "FAIL" in sv18[0]["title"],
               json.dumps(sv18, indent=1)[:500])
        (t18 / "working/.ship_status.json").write_text(json.dumps(
            {"id": "ship_x", "state": "done", "verdict": "", "ship_line": "SHIP: done"}),
            encoding="utf-8")
        sv18b = [f for f in payload(t18)["findings"] if f["rule"] == "ship-verdict"]
        check_("18b a ship quoting no verdict at all is a finding, not silence",
               bool(sv18b) and "quotes no check_all verdict" in sv18b[0]["title"],
               json.dumps(sv18b, indent=1)[:500])
        (t18 / "working/.ship_status.json").write_text(json.dumps(
            {"id": "ship_x", "state": "done", "verdict": "OK", "ship_line": "SHIP: OK abc1234"}),
            encoding="utf-8")
        check_("18c the branch bites: an OK ship raises nothing",
               not [f for f in payload(t18)["findings"] if f["rule"] == "ship-verdict"],
               json.dumps([f for f in payload(t18)["findings"]
                           if f["rule"] == "ship-verdict"], indent=1)[:500])

        # 19. A ship request waiting over a day, and a repository behind origin.
        t19 = T / "waiting"
        _mkrepo(t19, lock={"holder": None, "claims": {}})
        (t19 / "working/DOCUMENT_LOCK.json").write_text(
            json.dumps({"holder": None, "claims": {}}, indent=2), encoding="utf-8")
        _commit(t19, ["working/DOCUMENT_LOCK.json"], "lock", private=True)
        two_days = (now() - datetime.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
        (t19 / "working/.ship_request").write_text(json.dumps(
            {"id": "ship_waiting", "requested_at": two_days, "requested_by": "a chat",
             "message": "ship it", "chat": "a chat", "claims": ["tools"], "paths": []}),
            encoding="utf-8")
        sw = [f for f in payload(t19)["findings"] if f["rule"] == "ship-waiting"]
        check_("19a a request waiting 48 h is serious, with its age and who asked",
               bool(sw) and sw[0]["serious"] and "48 h" in sw[0]["title"]
               and "a chat" in sw[0]["detail"], json.dumps(sw, indent=1)[:500])
        (t19 / "working/.ship_request").write_text(json.dumps(
            {"id": "ship_waiting", "requested_at": stamp(), "requested_by": "a chat",
             "message": "ship it"}), encoding="utf-8")
        check_("19b the branch bites: a request made just now is not yet a finding",
               not [f for f in payload(t19)["findings"] if f["rule"] == "ship-waiting"],
               json.dumps([f for f in payload(t19)["findings"]
                           if f["rule"] == "ship-waiting"], indent=1)[:500])

        # 13. Keys are stable across runs: the same evidence gives the same keys.
        a_keys = {f["key"] for f in payload(t10)["findings"]}
        b_keys = {f["key"] for f in payload(t10)["findings"]}
        check_("13a the same evidence gives the same keys, so 'newly found' means something",
               a_keys == b_keys and all(":" in k for k in a_keys), str(sorted(a_keys))[:400])

        # 14. The overflow summary is bounded and the count stays true.
        t14 = T / "overflow"
        _mkrepo(t14, lock={"holder": None, "claims": {}})
        rows = ["when,action,claim,from_chat,to_chat,by,note"]
        for i in range(MAX_PER_RULE + 4):
            rows.append(f"{stamp()},forced-take,doc:X{i},A,B,martin,n{i}")
        (t14 / "working/claim_overrides.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
        _commit(t14, ["working/claim_overrides.csv"], "many overrides", private=True)
        p14 = payload(t14)
        ovs = [f for f in p14["findings"] if f["rule"] == "override"]
        check_("14a a rule firing many times is capped, with one summary finding",
               len(ovs) == MAX_PER_RULE + 1
               and any(f["subject"].startswith("and ") for f in ovs),
               json.dumps([f["subject"] for f in ovs])[:400])
        check_("14b and the true count survives in counts.by_rule",
               p14["counts"]["by_rule"].get("override") == MAX_PER_RULE + 4,
               json.dumps(p14["counts"], indent=1)[:400])

        # 15. --check never fails on findings: it reports them (D-302, report-only).
        rc, out, err = _run(["--check"], t10); out += err
        check_("15a --check returns 0 with a serious finding outstanding, and says so",
               rc == 0 and "SERIOUS" in out and "never intervenes" in out, out[:600])
        rc, out, err = _run(["--check"], t12); out += err
        check_("15b and reads OK when there is nothing serious", rc == 0 and "OK" in out, out[:400])

        # 16. The watermark bounds the window and is only written when asked.
        rc, out, err = _run(["--json"], t10); out += err
        check_("16a a run does not write the state file by itself",
               not (t10 / "working/rule_audit_state.json").exists(), out[:300])
        rc, out, err = _run(["--write-state"], t10); out += err
        check_("16b --write-state records the watermark and both heads",
               (t10 / "working/rule_audit_state.json").exists()
               and "public" in json.loads(
                   (t10 / "working/rule_audit_state.json").read_text(encoding="utf-8")), out[:400])

    print("  rule_audit selftest: " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="audit the chats against the project's own rules")
    ap.add_argument("--json", action="store_true", help="the payload hq_snapshot step 5 reads")
    ap.add_argument("--since", help="a rev to audit from (overrides the stored watermark)")
    ap.add_argument("--days", type=int, default=SINCE_DAYS,
                    help=f"the window when there is no watermark (default {SINCE_DAYS})")
    ap.add_argument("--write-state", action="store_true",
                    help="move the watermark to HEAD after reporting")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.check:
        return check()
    for w in doc_lock.override_warnings():
        print(f"  >>> {w}", file=sys.stderr)
    p = audit(since=a.since or os.environ.get("NRG_RULE_AUDIT_SINCE"), days=a.days)
    if a.json:
        print(json.dumps(p, indent=2))
    else:
        report(p)
    if a.write_state and p.get("can_report"):
        write_state(p)
        print(f"  watermark written to {STATE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
