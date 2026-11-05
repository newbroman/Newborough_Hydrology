#!/usr/bin/env python3
"""hq_snapshot — everything the NRG HQ page shows, gathered into one payload (D-301).

The page (tools/hq_page.py) renders from the artifact's `db`, and only a SESSION can write that db:
the ArtifactData tool belongs to the conversation, not to a script. So the split is deliberate -

    this script gathers and computes;  the session writes one batch;  the page renders.

Nothing here touches the network or the db, which is why it can be tested in a throwaway tree.

WHAT IT GATHERS
  board          tools/work_board.py  - claims, both repositories, ships, uncommitted files
  tasks          tools/task_lint.py --json  (runs every row's check: the slow part, ~1-2 min)
  gate           scratch/check_all_summary.json + the tee'd log, for the advisory lines
  queue          tools/job_queue.py   - jobs and which of their conditions hold
  chats          tools/chat_register.py
  owed           republishes owed, the proof page behind its bundle, stale unmerged branches
  audit          tools/rule_audit.py  - the conduct checks (step 5, phase 3): commits against the
                 claims held at the time, handover entries, decision fields, version bumps, the
                 chat register and the override log. It re-implements no lint.

HISTORY LIVES IN THE PRIVATE REPOSITORY, NOT IN THE DB (decided 2026-11-05)

  The tasks band wants a trend (spec D6: over the last 7 runs) and the gate band wants "newly red
  since the last run". Both need yesterday. Keeping that only in the db would mean the script could
  not compute either without a session to read it back, and a run with no db - a bridge session, a
  test - would silently have no history at all.

  So working/hq_history.json is the record, appended per run, last HISTORY_RUNS kept, and the db
  gets the DERIVED answer. It is private, like the lock and the registers.

A RUN WITHOUT THE PRIVATE STORE WRITES NOTHING (D-300, applied to the auditor)

  A task's status is store-dependent: a public-only session measured 104 of 133 done on 2026-11-05
  where a session with both repositories measured 120 of 134. So a snapshot taken without the
  private store would invent 14 open tasks and a dozen free claims. Such a run refuses to write the
  history or the payload, and says what it cannot see - it never reports "all clear".

Usage:
  python3 tools/hq_snapshot.py                       # gather, write the payload, append history
  python3 tools/hq_snapshot.py --no-tasks            # skip the slow part (board/queue/gate only)
  python3 tools/hq_snapshot.py --out PATH --no-history
  python3 tools/hq_snapshot.py --check | --selftest
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-11-05 (D-301 phase 3, T-137). Step 5 wired in:
#   collect() calls rule_audit.audit() with the board and newly-red list it has already computed, db_ops
#   writes the `findings` collection with `serious` set EXPLICITLY on every row (the page's band renders
#   serious !== false, so a missing field would read as serious), and run_record keeps the finding KEYS
#   so the next run can say which are newly found.
# 1.0.0  # Hollingham (2026) — 2026-11-05 (D-301, spec NRG_handover_HQ_page_2026-11-05,
#   signed off). First issue: the payload for the HQ page's db, the 7-run task trend and the newly-red gate
#   comparison from working/hq_history.json (private), and a refusal to write anything without the private store.
#   --db-ops writes the ArtifactData batch, one file per document, with the snake_case -> camelCase contract in
#   one place: a 150 kB payload must not pass through a conversation to reach the store.

import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE).resolve()
sys.path.insert(0, str(HERE / "tools"))

import doc_lock                                                       # noqa: E402
import work_board                                                     # noqa: E402
import job_queue                                                      # noqa: E402
import chat_register                                                  # noqa: E402
import rule_audit                                                     # noqa: E402

HISTORY = REPO / "working/hq_history.json"
HISTORY_RUNS = 30                 # enough for D6's 7-run trend with room to look further back
TREND_RUNS = 7                    # spec D6, signed off
PAYLOAD = REPO / "scratch/hq/payload.json"
GATE_SUMMARY = REPO / (os.environ.get("NRG_GATE_SUMMARY") or "scratch/check_all_summary.json")
STALE_BRANCH_DAYS = 7             # spec §4.8: unmerged branches older than a week are "owed"

# An advisory count line is one a section prints that does NOT set rc: a backlog, a known-dangling
# reference, a stale ledger version. They are work outstanding, so the page shows them with their
# trend - but they are matched from the log rather than captured per section, because capturing
# stdout inside check_all would reorder fifty sections' output to buy a line we can read afterwards.
ADVISORY_RE = r"(?i)\b(\d+)\s+(advisory|backlog|outstanding|dangling|to change|unresolved)\b"


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def need_store(what: str) -> bool:
    if doc_lock.store_ok():
        return True
    doc_lock.refuse_absent_store(what)
    return False


def _git(*args: str, private: bool = False) -> str:
    gd = REPO / (".git-working" if private else ".git")
    cmd = ["git", "--no-optional-locks", f"--git-dir={gd}"]
    if private:
        cmd.append(f"--work-tree={REPO}")
    try:
        p = subprocess.run(cmd + list(args), cwd=str(REPO), capture_output=True, text=True, timeout=30)
        return p.stdout.strip() if p.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def stale_branches() -> list[dict]:
    """Branches pushed and not merged into main for more than a week (spec §4.8). The notes branch
    of 2026-11-04 is the first - it carries the specs this build was written from."""
    out = []
    raw = _git("for-each-ref", "--format=%(refname:short)%09%(committerdate:iso8601)%09%(subject)",
               "refs/remotes/origin")
    merged = set(_git("branch", "-r", "--merged", "main", "--format=%(refname:short)").split())
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=STALE_BRANCH_DAYS)
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        name, when = parts[0], parts[1]
        if name in merged or name.endswith("/HEAD") or name in ("origin/main", "origin/gh-pages"):
            continue
        try:
            dt = datetime.datetime.fromisoformat(when.replace(" ", "T", 1).replace(" ", ""))
        except ValueError:
            continue
        if dt < cutoff:
            out.append({"branch": name, "last_commit": when,
                        "days": round((datetime.datetime.now(datetime.timezone.utc) - dt).days),
                        "subject": (parts[2] if len(parts) > 2 else "")[:120]})
    return sorted(out, key=lambda b: -b["days"])


def owed() -> list[dict]:
    """Things behind where they should be. Each one names what to run."""
    out = []
    st = REPO / "tools/proof_bundle_state.json"
    if st.exists():
        try:
            d = json.loads(st.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        if d.get("bundle_sha256") and d.get("published_sha256") != d.get("bundle_sha256"):
            out.append({"what": "the proof page is behind its bundle",
                        "since": d.get("published_at") or "unknown",
                        "do": "python3 tools/proof_copy.py --refresh, then republish the proof artifact"})
    for marker, what, do in (
            (doc_lock.PUBLISH_OWED, "the work board page is behind the lock",
             "python3 tools/board_artifact.py  (D7: folded into HQ - republish HQ instead)"),
            ("working/.hq_publish_owed", "the HQ page is behind the db",
             "python3 tools/hq_page.py, then republish the HQ artifact")):
        m = REPO / marker
        if m.exists():
            try:
                why = m.read_text(encoding="utf-8").strip()
            except OSError:
                why = ""
            if why:                      # an empty marker is not an owed republish, it is a stray file
                out.append({"what": what, "since": "", "why": why[:200], "do": do})
    for b in stale_branches():
        out.append({"what": f"{b['branch']} is unmerged after {b['days']} days",
                    "since": b["last_commit"], "do": "merge it, or say in the handover why it stays apart"})
    return out


def gate() -> dict:
    """The last check_all, from the summary check_all.sh now writes (1.34.0). The log beside it, if
    one is there, gives the advisory lines - matched, not captured; see ADVISORY_RE."""
    if not GATE_SUMMARY.exists():
        return {"present": False,
                "why": f"no {GATE_SUMMARY.name}: run bash tools/check_all.sh (1.34.0 writes it)"}
    try:
        d = json.loads(GATE_SUMMARY.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return {"present": False, "why": f"{GATE_SUMMARY.name} is not readable: {e}"}
    d["present"] = True
    d["advisory"] = advisory_lines()
    return d


def advisory_lines() -> list[dict]:
    """Count lines a gate log printed that no gate failed on. Read from the newest log in scratch/
    whose name looks like a check_all run, because that is where the project tees them (CLAUDE.md 4)."""
    import re
    logs = sorted((REPO / "scratch").glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True) \
        if (REPO / "scratch").is_dir() else []
    log = next((p for p in logs if "check_all" in p.name), None)
    if log is None:
        return []
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out, section = [], ""
    for line in text.splitlines():
        if line.startswith("── "):
            section = line[3:].split("─")[0].split(" (")[0].strip()
        m = re.search(ADVISORY_RE, line)
        if m and "FAIL" not in line:
            out.append({"section": section, "count": int(m.group(1)), "line": line.strip()[:160]})
    return out[:60]


def history() -> list[dict]:
    if not HISTORY.exists():
        return []
    try:
        d = json.loads(HISTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return d.get("runs", []) if isinstance(d, dict) else []


def append_history(run: dict) -> int:
    runs = history() + [run]
    runs = runs[-HISTORY_RUNS:]
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps({"kept": HISTORY_RUNS, "runs": runs}, indent=2) + "\n",
                       encoding="utf-8")
    return len(runs)


def trend(task_id: str, got: str, runs: list[dict]) -> str:
    """D6: closer to done, further, or unchanged, over the last TREND_RUNS runs.

    A task's value is whatever its check prints, so it is compared as a number when both ends are
    numbers and as a string otherwise - which is the honest answer for a check that answers a word.
    """
    past = [r for r in runs[-TREND_RUNS:] if task_id in (r.get("tasks") or {})]
    if not past:
        return "new"
    then = (past[0]["tasks"][task_id] or {}).get("got", "")
    if then == got:
        return "unchanged"
    try:
        a, b = float(then), float(got)
    except (TypeError, ValueError):
        return "changed"
    return "closer" if abs(b) < abs(a) else "further"


def newly_red(sections: list[dict], runs: list[dict]) -> list[str]:
    """A section that failed this run and passed the one before. Keyed by `key` (index + name),
    because two sections may share a name - "claims" did until check_all 1.34.0 renamed one."""
    prev = next((r for r in reversed(runs) if r.get("gate_sections")), None)
    if prev is None:
        return []
    was = {k: v for k, v in (prev.get("gate_sections") or {}).items()}
    return [s["key"] for s in sections
            if s["verdict"] != "OK" and was.get(s["key"], "OK") == "OK"]


def collect(do_tasks: bool = True, do_probe: bool = False) -> dict:
    state, why = doc_lock.store_state()
    board = work_board.collect(do_probe=do_probe)
    q = job_queue.collect()
    chats = chat_register.collect()
    g = gate()
    tasks = None
    if do_tasks:
        import task_lint
        tasks = task_lint.as_json()
    runs = history()
    secs = g.get("sections") or []
    payload = {
        "generated": now(),
        "store": state,
        "store_why": why,
        "can_report": state != "ABSENT",
        "mode": doc_lock.session_mode(),
        "host": os.uname().nodename if hasattr(os, "uname") else "",
        "board": board,
        "digest": work_board.digest(board),
        "queue": q,
        "chats": chats,
        "gate": g,
        "gate_newly_red": newly_red(secs, runs) if secs else [],
        "tasks": tasks,
        "owed": owed(),
        "history_runs": len(runs),
    }
    # Step 5 (spec §7): the conduct checks. rule_audit is given the board and the newly-red list
    # this pass has already computed, so work_board is not walked twice and the two agree by
    # construction. It returns its own refusal when the store is absent, which cannot happen here -
    # collect() is only reached with the store present - but the field is carried either way, so
    # the page can say "UNKNOWN" rather than show an empty findings band as if it were clean.
    payload["audit"] = rule_audit.audit(board=board, newly_red=payload["gate_newly_red"])
    if tasks:
        for t in tasks["tasks"]:
            t["trend"] = trend(t["id"], t.get("got", ""), runs)
    return payload


def run_record(payload: dict) -> dict:
    """What goes into the history: small, and only what a trend needs."""
    return {
        "at": payload["generated"],
        "store": payload["store"],
        "verdict": (payload.get("gate") or {}).get("verdict"),
        "gate_sections": {s["key"]: s["verdict"] for s in ((payload.get("gate") or {}).get("sections") or [])},
        "counts": ((payload.get("tasks") or {}).get("counts") or {}),
        "tasks": {t["id"]: {"got": t.get("got", ""), "status": t.get("status")}
                  for t in ((payload.get("tasks") or {}).get("tasks") or [])},
        # The findings' KEYS, so the next run can say which are newly found - the same contract
        # gate_sections uses for newly_red(). Keys only: the titles would bloat 30 runs of history.
        "finding_keys": sorted(f["key"] for f in ((payload.get("audit") or {}).get("findings") or [])),
    }


# ── the db documents ────────────────────────────────────────────────────────────────────────
#
# The page reads camelCase; the tools speak snake_case. The translation lives HERE, in one place,
# so there is exactly one definition of the contract between the two - and each document is written
# to its own file, so a 150 kB payload never passes through a conversation to reach the store.
DB_DIR = REPO / "scratch/hq/db"


def _slug(s: str) -> str:
    out = "".join(c if (c.isalnum() or c in "_-.~:@+") else "-" for c in (s or "").strip())
    return (out.strip("-") or "x")[:200]


def db_ops(payload: dict) -> list[dict]:
    """The batch a session writes with ArtifactData. Returns [{op, collection, doc_id, file_path}]."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    ops: list[dict] = []

    def put(collection: str, doc_id: str, data: dict) -> None:
        f = DB_DIR / f"{collection.replace('/', '_')}_{doc_id}.json"
        f.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        ops.append({"op": "set", "collection": collection, "doc_id": doc_id,
                    "file_path": str(f.relative_to(REPO))})

    g = payload.get("gate") or {}
    put("meta", "snapshot", {
        "generated": payload["generated"], "store": payload["store"],
        "storeWhy": payload["store_why"], "canReport": payload["can_report"],
        "digest": payload["digest"], "mode": payload.get("mode", ""),
        "host": payload.get("host", ""), "historyRuns": payload.get("history_runs", 0),
        "gateNewlyRed": payload.get("gate_newly_red") or [],
        "warnings": (payload.get("board") or {}).get("warnings") or [],
    })
    put("meta", "owed", {"items": payload.get("owed") or [], "generated": payload["generated"]})
    # meta/links is MERGED, never replaced: the HQ session link and the project link are Martin's to
    # set, and this tool does not know them. It writes only the links it can derive.
    links = {"repoPublic": "https://github.com/newbroman/Newborough_Hydrology",
             "repoPrivate": "https://github.com/newbroman/Newborough_Hydrology_working"}
    for key, f in (("board", "working/.board_artifact.json"), ("hqPage", "working/.hq_artifact.json")):
        try:
            u = json.loads((REPO / f).read_text(encoding="utf-8")).get("url")
        except (OSError, ValueError):
            u = None
        if u:
            links[key] = u
    lf = DB_DIR / "meta_links.json"
    lf.write_text(json.dumps(links, indent=2) + "\n", encoding="utf-8")
    # An `update` to a document that does not exist is REFUSED ("no such ... document"), and the
    # batch is atomic, so the very first HQ write failed on this one op and wrote nothing (measured
    # 2026-11-05). So the op carries the fallback: try update, and set it if it is not there yet.
    ops.append({"op": "update", "collection": "meta", "doc_id": "links",
                "file_path": str(lf.relative_to(REPO)), "create_if_missing": True})
    put("board", "current", dict(payload.get("board") or {}, generated=payload["generated"]))
    t = payload.get("tasks")
    if t:
        put("tasks", "current", {"counts": t["counts"], "tasks": t["tasks"],
                                 "generated": t.get("generated") or payload["generated"],
                                 "store": t.get("store")})
    if g.get("present"):
        at = g.get("generated") or payload["generated"]
        put("gate_runs", _slug(at.replace("-", "").replace(":", "")), {
            "at": at, "host": g.get("host", ""), "verdict": g.get("verdict"),
            "counts": g.get("counts") or {}, "sections": g.get("sections") or [],
            "advisory": g.get("advisory") or [], "newlyRed": payload.get("gate_newly_red") or [],
        })
    for j in (payload.get("queue") or {}).get("jobs") or []:
        put("jobs", _slug(j.get("id", "")), {
            "id": j.get("id"), "title": j.get("title"), "brief": j.get("brief"),
            "claim": j.get("claim"), "target": j.get("target"), "status": j.get("status"),
            "waitsFor": j.get("waits_for"), "conditions": j.get("conditions") or [],
            "allHold": j.get("all_hold"), "blockedBy": j.get("blocked_by"),
            "firedAt": j.get("fired_at"), "firedBy": j.get("fired_by"), "note": j.get("note"),
        })
    # findings (phase 3, T-137). The page's "Needs you" band renders f.serious !== false, so every
    # finding carries `serious` EXPLICITLY - a missing field would read as serious.
    for f in (payload.get("audit") or {}).get("findings") or []:
        put("findings", _slug(f.get("key", "")), {
            "key": f.get("key"), "rule": f.get("rule"), "subject": f.get("subject"),
            "title": f.get("title"), "detail": f.get("detail"), "evidence": f.get("evidence"),
            "serious": bool(f.get("serious")), "chat": f.get("chat"), "commit": f.get("commit"),
            "file": f.get("file"), "at": f.get("at"),
            "generated": payload["generated"],
        })
    for c in (payload.get("chats") or {}).get("chats") or []:
        put("chats", _slug(c.get("chat", "")), {
            "chat": c.get("chat"), "kind": c.get("kind"), "claim": c.get("claim"),
            "mode": c.get("mode"), "link": c.get("link"), "status": c.get("status"),
            "purpose": c.get("purpose"), "outcome": c.get("outcome"),
            "opened": c.get("opened"), "touched": c.get("touched"),
            "registeredBy": c.get("registered_by"),
            "seeded": bool(c.get("registered_by")) and c.get("registered_by") != c.get("chat"),
        })
    (DB_DIR / "ops.json").write_text(json.dumps(ops, indent=2) + "\n", encoding="utf-8")
    return ops


def check() -> int:
    """Gate: cheap by construction. It must NOT re-run the 134 task checks - task_lint's own section
    has just done that - so this asks only whether the pieces the page needs are there."""
    state, why = doc_lock.store_state()
    if state == "ABSENT":
        print(f"  hq_snapshot: SKIP — {why}")
        return 0
    notes = []
    if not GATE_SUMMARY.exists():
        notes.append(f"no {GATE_SUMMARY.name} yet (check_all 1.34.0 writes it; this run will)")
    if not HISTORY.exists():
        notes.append("no history yet: the first snapshot writes working/hq_history.json")
    else:
        runs = history()
        if runs:
            last = runs[-1].get("at", "")
            notes.append(f"{len(runs)} run(s) in history, last {last}")
    print("  hq_snapshot: OK" + (f" — {'; '.join(notes)}" if notes else ""))
    return 0


def _selftest() -> int:
    import tempfile
    ok = True

    def check_(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        if not cond:
            ok = False
            print(f"  FAIL  {label}" + (f"\n        {detail.strip()[:500]}" if detail else ""))

    def run(args, tree, **env_extra):
        env = dict(os.environ, NRG_REPO_ROOT=str(tree))
        for k in ("NRG_CHAT", "NRG_NO_PRIVATE_STORE", "NRG_GATE_SUMMARY"):
            env.pop(k, None)
        env.update({k: v for k, v in env_extra.items() if v is not None})
        p = subprocess.run([sys.executable, str(HERE / "tools/hq_snapshot.py"), *args],
                           capture_output=True, text=True, env=env, cwd=str(HERE))
        return p.returncode, p.stdout + p.stderr

    with tempfile.TemporaryDirectory() as td:
        T = pathlib.Path(td)

        # 1. No private store: nothing is written, and the payload does not claim it can report.
        t1 = doc_lock._mktree(T / "public_only", private=False, lock=None)
        rc, out = run(["--no-tasks"], t1)
        check_("1a no store: refuses to write", rc == 1, out)
        check_("1b no store: says what it cannot see", "not present" in out.lower(), out)
        check_("1c no store: no payload written", not (t1 / "scratch/hq/payload.json").exists(), out)
        check_("1d no store: no history written", not (t1 / "working/hq_history.json").exists(), out)
        rc, out = run(["--check"], t1)
        check_("1e no store: the gate skips rather than passing green", rc == 0 and "SKIP" in out, out)

        # 2. With the store: a payload, and a history that grows by one per run.
        t2 = doc_lock._mktree(T / "both", private=True, lock={"holder": None, "claims": {}})
        (t2 / "scratch").mkdir(exist_ok=True)
        (t2 / "scratch/check_all_summary.json").write_text(json.dumps({
            "generated": now(), "verdict": "FAIL", "host": "test",
            "sections": [{"index": 1, "key": "01 mirrors", "section": "mirrors", "verdict": "OK",
                          "seconds": 2},
                         {"index": 2, "key": "02 tasks", "section": "tasks", "verdict": "FAIL",
                          "seconds": 9}]}), encoding="utf-8")
        rc, out = run(["--no-tasks"], t2)
        check_("2a with the store: a payload is written", rc == 0
               and (t2 / "scratch/hq/payload.json").exists(), out)
        pay = json.loads((t2 / "scratch/hq/payload.json").read_text())
        check_("2b it carries the gate's sections", len(pay["gate"]["sections"]) == 2, str(pay["gate"])[:200])
        check_("2c and can_report is true", pay["can_report"] is True, str(pay)[:200])
        check_("2d the first run has no newly-red (nothing to compare)", pay["gate_newly_red"] == [],
               str(pay["gate_newly_red"]))
        h1 = json.loads((t2 / "working/hq_history.json").read_text())["runs"]
        check_("2e history has one run", len(h1) == 1, str(h1)[:200])

        # 3. Newly red: the SECOND run sees a section that passed before and fails now.
        (t2 / "scratch/check_all_summary.json").write_text(json.dumps({
            "generated": now(), "verdict": "FAIL", "host": "test",
            "sections": [{"index": 1, "key": "01 mirrors", "section": "mirrors", "verdict": "FAIL",
                          "seconds": 2},
                         {"index": 2, "key": "02 tasks", "section": "tasks", "verdict": "FAIL",
                          "seconds": 9}]}), encoding="utf-8")
        rc, out = run(["--no-tasks"], t2)
        pay = json.loads((t2 / "scratch/hq/payload.json").read_text())
        check_("3a mirrors is flagged newly red", pay["gate_newly_red"] == ["01 mirrors"],
               str(pay["gate_newly_red"]))
        check_("3b tasks, red in both runs, is NOT flagged", "02 tasks" not in pay["gate_newly_red"],
               str(pay["gate_newly_red"]))
        check_("3c history has two runs",
               len(json.loads((t2 / "working/hq_history.json").read_text())["runs"]) == 2, "")

        # 4. --no-history leaves the record alone (so a test or a bridge run cannot pollute it).
        rc, out = run(["--no-tasks", "--no-history"], t2)
        check_("4a --no-history does not append",
               len(json.loads((t2 / "working/hq_history.json").read_text())["runs"]) == 2, out)

        # 5. The trend reads a number as a number and a word as a word.
        runs = [{"tasks": {"T-1": {"got": "9"}, "T-2": {"got": "ok"}, "T-3": {"got": "2"}}}]
        check_("5a a falling number is closer", trend("T-1", "4", runs) == "closer")
        check_("5b a rising number is further", trend("T-3", "7", runs) == "further")
        check_("5c the same value is unchanged", trend("T-2", "ok", runs) == "unchanged")
        check_("5d a word that moved is 'changed', never 'closer'", trend("T-2", "no", runs) == "changed")
        check_("5e a task with no history is new", trend("T-9", "1", runs) == "new")

        # 6. An EMPTY owed marker is a stray file, not an owed republish (the board_artifact bug of
        #    2026-11-04: unlink raised, the fallback wrote "", and --check then claimed it was owed).
        t6 = doc_lock._mktree(T / "owed", private=True, lock={"holder": None, "claims": {}})
        (t6 / "working/.hq_publish_owed").write_text("", encoding="utf-8")
        rc, out = run(["--no-tasks"], t6)
        pay = json.loads((t6 / "scratch/hq/payload.json").read_text())
        check_("6a an empty marker is not owed", not any("HQ page" in o["what"] for o in pay["owed"]),
               str(pay["owed"]))
        (t6 / "working/.hq_publish_owed").write_text("a claim was taken", encoding="utf-8")
        rc, out = run(["--no-tasks"], t6)
        pay = json.loads((t6 / "scratch/hq/payload.json").read_text())
        check_("6b a marker with a reason IS owed", any("HQ page" in o["what"] for o in pay["owed"]),
               str(pay["owed"]))

    print("hq_snapshot selftest: " + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(PAYLOAD))
    ap.add_argument("--no-tasks", action="store_true", help="skip the 1-2 minute task sweep")
    ap.add_argument("--no-history", action="store_true",
                    help="do not append to working/hq_history.json, and do not move the "
                         "audit watermark (the two go together)")
    ap.add_argument("--probe", action="store_true", help="ask each origin whether it has moved")
    ap.add_argument("--db-ops", dest="db_ops", action="store_true",
                    help="also write the ArtifactData batch (scratch/hq/db/, index ops.json)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()
    if a.check:
        return check()
    if not need_store("take an HQ snapshot"):
        print("  nothing written: a snapshot taken without the private store would invent open tasks\n"
              "  and free claims, and this tool does not report 'all clear' for what it cannot see.")
        return 1

    payload = collect(do_tasks=not a.no_tasks, do_probe=a.probe)
    out = pathlib.Path(a.out)
    if not out.is_absolute():
        out = REPO / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    ops = db_ops(payload) if a.db_ops else []
    kept = append_history(run_record(payload)) if not a.no_history else len(history())
    # The audit's watermark moves with the history, and for the same reason: both say "this run
    # happened". --no-history holds both back, so a test or a dry run never advances the window and
    # silently hides a day's conduct from the next pass.
    if not a.no_history and (payload.get("audit") or {}).get("can_report"):
        rule_audit.write_state(payload["audit"])
    if not a.quiet:
        g = payload.get("gate") or {}
        t = payload.get("tasks") or {}
        print(f"  hq_snapshot: {out.relative_to(REPO) if out.is_relative_to(REPO) else out}"
              f"  ({out.stat().st_size:,} bytes)")
        print(f"    {payload['digest']}")
        print(f"    gate {g.get('verdict') or 'not run'}"
              + (f", {g.get('counts', {}).get('failed', 0)} of {g.get('counts', {}).get('sections', 0)}"
                 f" section(s) red" if g.get("present") else f" ({g.get('why','')})"))
        if payload["gate_newly_red"]:
            print(f"    >>> NEWLY RED since the last run: {', '.join(payload['gate_newly_red'])}")
        if t:
            c = t["counts"]
            print(f"    tasks {c['total']}: {c['done']} done, {c['open']} open, {c['broken']} broken")
        if ops:
            print(f"    {len(ops)} document(s) for the page's store: scratch/hq/db/ops.json")
            if any(o.get("create_if_missing") for o in ops):
                print("      (meta/links is an update with create_if_missing: an update to a "
                      "document that\n       does not exist is refused, and a batch is atomic)")
        au = payload.get("audit") or {}
        if au.get("can_report"):
            ac = au.get("counts") or {}
            print(f"    findings {ac.get('total', 0)}: {ac.get('serious', 0)} serious,"
                  f" {ac.get('suppressed', 0)} suppressed"
                  f"  (window {(au.get('window') or {}).get('commits', 0)} commit(s))")
            for f in (au.get("findings") or []):
                if f.get("serious"):
                    print(f"      >>> SERIOUS [{f['rule']}] {f['title']}")
        elif au:
            print(f"    findings: CANNOT AUDIT — {au.get('why_nothing', '')}")
        print(f"    queue {len(payload['queue'].get('jobs') or [])} job(s);"
              f" chats {len(payload['chats'].get('chats') or [])};"
              f" owed {len(payload['owed'])};  history {kept} run(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
