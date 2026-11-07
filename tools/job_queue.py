#!/usr/bin/env python3
"""job_queue — jobs that start when their conditions are met, so Martin stops carrying prompts
between chats (D-301, spec NRG_handover_HQ_page_2026-11-05 §14, signed off 2026-11-05 03:16).

One chat finishing should start the next. Until now that handover went through Martin: a session
ended, told him what was next, and he opened a chat and pasted a brief. The queue removes the
relaying. It does not make decisions - every brief says that a design question stops and waits for
him.

WHAT THE QUEUE CANNOT DO, STATED PLAINLY (measured 2026-11-05)

  A job does NOT fire itself. §14 proposed a poke-only scheduled task per job; such a task exists,
  but the tool that makes it says an ad-hoc task "can only be started manually", and a scheduled
  task in the desktop app runs only while the app is open. Nothing in the queue wakes up.

  So a job fires when SOMETHING IS ALREADY RUNNING, and there are exactly two such moments:
    - `doc_lock.py release` - the release that frees a claim prints the jobs it made ready, and the
      releasing session fires them (doc_lock 1.5.0);
    - the HQ agent's daily pass, as the backstop.
  Worst case a job waits until the next morning. That is the honest claim, and it is still what
  Martin asked for: he is no longer the relay.

CONDITIONS (`waits_for`, semicolon-separated; ALL must hold)

  claim_free:<name>   nobody holds that claim          (UNKNOWN with no private store - see below)
  job_done:<id>       another row in this queue is done
  on_main:<path>      the file exists on main - the PRIVATE main for a working/ path, else public
  task_done:<T-id>    that task register row's own check now answers what it wants
  held_by_martin      never holds; he clears it by hand when he is ready

WITH NO PRIVATE STORE, NOTHING FIRES (D-300)

  The queue lives in the private repository, and so does the lock that says whether a claim is free.
  A session holding only the public half cannot see either, so `claim_free` reads UNKNOWN rather
  than true, and firing refuses outright. A queue that fired on a store it could not read would
  start a session into work another chat already holds - the 2026-11-04 incident with consequences.

Usage:
  python3 tools/job_queue.py                                   # the queue, condition by condition
  python3 tools/job_queue.py add --id J-3 --title ... --brief PATH --claim pipeline \
      --waits-for "job_done:J-1;claim_free:pipeline" --target new_session
  python3 tools/job_queue.py ready                             # promote queued -> ready; print the fire line
  python3 tools/job_queue.py fire J-1 --by "control board" [--trigger-id ID]
  python3 tools/job_queue.py done J-1 | hold J-1 | unhold J-1
  python3 tools/job_queue.py --json | --check | --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-05 (D-301, spec §14, signed off). First issue:
#   the five condition kinds, the three guards (no store, claim held, one job per claim), and ready/fire/done.

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

import register_io                                                    # noqa: E402
import doc_lock                                                       # noqa: E402

QUEUE = REPO / "working/job_queue.csv"
FIELDS = ["id", "title", "brief", "claim", "waits_for", "target", "status",
          "trigger_id", "fired_at", "fired_by", "note"]

TARGETS = ("new_session", "notify")
STATUSES = ("queued", "ready", "fired", "done", "held")
COND_KINDS = ("claim_free", "job_done", "on_main", "task_done", "held_by_martin")
# A job that has been fired but never marked done still OWNS its claim as far as the queue is
# concerned: another job for the same claim must not fire behind its back.
ACTIVE = ("ready", "fired")


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def need_store(what: str) -> bool:
    """doc_lock.refuse_absent_store() prints the refusal and does not decide; this is the guard."""
    if doc_lock.store_ok():
        return True
    doc_lock.refuse_absent_store(what)
    return False


def rows() -> list[dict]:
    return [r for r in register_io.read_rows(QUEUE) if (r.get("id") or "").strip()]


def save(rs: list[dict]) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    register_io.write_rows(QUEUE, FIELDS, rs, sort_key=lambda r: r.get("id") or "", key_cols=["id"])
    # D-314 (widened 2026-11-06, Martin: "s to all shared records locks should be automatic"):
    # publish it at once, so a row exists for every chat the moment it is written. This chat's own
    # `status done` was lost to exactly this on 2026-11-06, alongside two claim releases.
    #
    # NO rebase-on-origin here, unlike the lock, and the difference is the file format: the lock is
    # ONE json document with no merge, so a write must land on origin's version or it reverts
    # someone; these are CSVs that register_io merges ROW BY ROW and whose writer already keeps
    # rows another writer added and honours removals. So they need publishing, not rebasing.
    try:
        import doc_lock
        doc_lock.publish_records(("working/job_queue.csv",), "job queue")
    except Exception:
        pass



def find(rs: list[dict], jid: str) -> dict | None:
    for r in rs:
        if (r.get("id") or "").strip() == jid.strip():
            return r
    return None


def conds(r: dict) -> list[str]:
    return [c.strip() for c in (r.get("waits_for") or "").split(";") if c.strip()]


def _git_has(path: str) -> bool:
    """Does `path` exist on main? A working/ path is the PRIVATE repository's half of this one tree
    (CLAUDE.md 4f), so it is asked of .git-working - asking the public repo would always say no."""
    private = path.startswith("working/")
    gd = REPO / (".git-working" if private else ".git")
    if not gd.exists():
        return False
    cmd = ["git", f"--git-dir={gd}", "cat-file", "-e", f"main:{path}"]
    return subprocess.run(cmd, cwd=str(REPO), capture_output=True).returncode == 0


def _task_done(tid: str) -> tuple[bool, str]:
    """Run that one task register row's own check. The register is SHARED (tools/), never claimed."""
    import csv
    reg = REPO / "tools/task_register.csv"
    if not reg.exists():
        return False, "no task register in this checkout"
    with reg.open(encoding="utf-8") as fh:
        row = next((r for r in csv.DictReader(fh) if (r.get("id") or "").strip() == tid), None)
    if row is None:
        return False, f"{tid} is not in the task register"
    try:
        import task_lint
    except Exception as e:                                            # pragma: no cover
        return False, f"task_lint not importable: {e}"
    out, note = task_lint.run_check(row["check"])
    if out is None:
        return False, f"{tid}'s check is broken: {note}"
    return out == row["expect"].strip(), f"{tid} answers {out!r}, wants {row['expect'].strip()!r}"


def cond_holds(c: str, rs: list[dict]) -> tuple[bool, str]:
    kind, _, arg = c.partition(":")
    if kind == "held_by_martin":
        return False, "held by Martin until he clears it"
    if kind == "claim_free":
        if not doc_lock.store_ok():
            return False, f"{arg} is UNKNOWN - no private store (D-300)"
        h = doc_lock.holder_of(arg)
        return (h is None), ("free" if h is None else f"held by {h!r}")
    if kind == "job_done":
        o = find(rs, arg)
        if o is None:
            return False, f"{arg} is not in the queue"
        return (o.get("status") == "done"), f"{arg} is {o.get('status') or '?'}"
    if kind == "on_main":
        ok = _git_has(arg)
        return ok, (f"{arg} is on main" if ok else f"{arg} is not on main yet")
    if kind == "task_done":
        return _task_done(arg)
    return False, f"unknown condition kind {kind!r}"


def evaluate(r: dict, rs: list[dict]) -> tuple[bool, list[tuple[str, bool, str]]]:
    out = [(c, *cond_holds(c, rs)) for c in conds(r)]
    return all(h for _, h, _ in out), out


def blocking_job(r: dict, rs: list[dict]) -> dict | None:
    """One job per claim at a time (§14's guard). A job already ready or fired for the same claim
    blocks this one even if every condition holds."""
    if not r.get("claim"):
        return None
    for o in rs:
        if o is r or o.get("claim") != r["claim"]:
            continue
        if o.get("status") in ACTIVE:
            return o
    return None


def ready(promote: bool = True, quiet: bool = False) -> list[dict]:
    """Jobs whose every condition holds. Promotes queued -> ready, which is what makes a release
    able to say "this is now ready" without evaluating anything twice."""
    rs = rows()
    out, changed = [], False
    for r in rs:
        if r.get("status") not in ("queued", "ready"):
            continue
        ok, _ = evaluate(r, rs)
        if not ok:
            if r.get("status") == "ready":      # a condition stopped holding: back to queued
                r["status"] = "queued"
                changed = True
            continue
        if blocking_job(r, rs) is not None:
            continue
        if r.get("status") != "ready" and promote:
            r["status"] = "ready"
            changed = True
        out.append(r)
    if changed and promote and doc_lock.store_ok():
        save(rs)
    if not quiet:
        if not out:
            print("  no job is ready")
        for r in out:
            print(f"  READY  {r['id']}  {r.get('title','')[:66]}")
            print(f"           brief {r.get('brief','')}")
            print(f"           fire it: python3 tools/job_queue.py fire {r['id']} --by \"<this chat>\"")
    return out


def fire(jid: str, by: str, trigger_id: str, dry: bool = False) -> int:
    if not need_store("fire a job"):
        return 1
    rs = rows()
    r = find(rs, jid)
    if r is None:
        print(f"  REFUSED — {jid} is not in the queue", file=sys.stderr)
        return 1
    if r.get("status") in ("fired", "done"):
        print(f"  REFUSED — {jid} is already {r['status']}"
              + (f" (by {r.get('fired_by')} at {r.get('fired_at')})" if r.get("fired_at") else ""),
              file=sys.stderr)
        return 1
    if r.get("status") == "held":
        print(f"  REFUSED — {jid} is held; `unhold` it first", file=sys.stderr)
        return 1
    ok, detail = evaluate(r, rs)
    if not ok:
        print(f"  REFUSED — {jid} is not ready:", file=sys.stderr)
        for c, h, why in detail:
            print(f"      {'ok ' if h else 'NO '} {c:<28} {why}", file=sys.stderr)
        return 1
    if r.get("claim") and doc_lock.holder_of(r["claim"]) is not None:
        print(f"  REFUSED — {r['claim']} is held by {doc_lock.holder_of(r['claim'])!r}; a job never "
              f"fires into a claim someone holds", file=sys.stderr)
        return 1
    b = blocking_job(r, rs)
    if b is not None:
        print(f"  REFUSED — {b['id']} is {b['status']} for the same claim ({r['claim']}); "
              f"one job per claim at a time", file=sys.stderr)
        return 1
    brief = r.get("brief") or ""
    if brief and not (REPO / brief).exists() and not _git_has(brief):
        print(f"  REFUSED — the brief {brief} is neither in the tree nor on main; a job never fires "
              f"a prompt nobody can read", file=sys.stderr)
        return 1
    if dry:
        print(f"  would fire {jid}: {r.get('title','')}")
        return 0
    r.update({"status": "fired", "fired_at": now(), "fired_by": by or doc_lock.chat_id() or "?",
              "trigger_id": trigger_id or r.get("trigger_id") or ""})
    save(rs)
    print(f"  FIRED  {jid}  {r.get('title','')[:66]}")
    print(f"    target {r.get('target')}   claim {r.get('claim') or '-'}   by {r['fired_by']}")
    if r.get("target") == "notify":
        print(f"    >>> target is notify: no session is started. The brief to hand on is {brief}")
    else:
        print(f"    >>> start the session with: Run job {jid}: read {brief} and follow it")
    return 0


def set_status(jid: str, status: str, note: str = "") -> int:
    if not need_store(f"mark a job {status}"):
        return 1
    rs = rows()
    r = find(rs, jid)
    if r is None:
        print(f"  REFUSED — {jid} is not in the queue", file=sys.stderr)
        return 1
    r["status"] = status
    if note:
        r["note"] = ((r.get("note") or "") + ("; " if r.get("note") else "") + note)[:400]
    save(rs)
    print(f"  {jid} is now {status}")
    if status == "done":
        nxt = [o["id"] for o in ready(promote=True, quiet=True)]
        if nxt:
            print(f"    this made ready: {', '.join(nxt)}")
    return 0


def add(jid: str, title: str, brief: str, claim: str, waits_for: str, target: str, note: str) -> int:
    if not need_store("add a job"):
        return 1
    rs = rows()
    if find(rs, jid) is not None:
        print(f"  REFUSED — {jid} is already in the queue", file=sys.stderr)
        return 1
    bad = [c for c in [x.strip() for x in waits_for.split(";") if x.strip()]
           if c.partition(":")[0] not in COND_KINDS]
    if bad:
        print(f"  REFUSED — condition kind(s) not understood: {', '.join(bad)}\n"
              f"  the kinds are: {', '.join(COND_KINDS)}", file=sys.stderr)
        return 1
    if target not in TARGETS:
        print(f"  REFUSED — target must be one of {', '.join(TARGETS)}", file=sys.stderr)
        return 1
    rs.append({"id": jid, "title": title, "brief": brief, "claim": claim, "waits_for": waits_for,
               "target": target, "status": "queued", "note": note})
    save(rs)
    print(f"  queued {jid}  {title[:66]}")
    return 0


def collect() -> dict:
    state, why = doc_lock.store_state()
    if state == "ABSENT":
        return {"store": state, "store_why": why, "jobs": [], "fires": False,
                "fires_why": "no private store: nothing fires, and no claim can be read (D-300)"}
    rs = rows()
    jobs = []
    for r in rs:
        ok, detail = evaluate(r, rs)
        b = blocking_job(r, rs)
        jobs.append(dict(r, conditions=[{"cond": c, "holds": h, "why": w} for c, h, w in detail],
                         all_hold=ok,
                         blocked_by=(b["id"] if b is not None else None)))
    return {"store": state, "store_why": why, "jobs": jobs, "fires": True, "fires_why": ""}


def render(B: dict) -> str:
    L = ["JOB QUEUE (tools/job_queue.py)"]
    if B["store"] == "ABSENT":
        L.append(f"  PRIVATE STORE ABSENT - {B['store_why']}")
        L.append("    >>> the queue is UNKNOWN from here and NOTHING fires (D-300)")
        return "\n".join(L)
    if not B["jobs"]:
        L.append("  the queue is empty")
        return "\n".join(L)
    for j in B["jobs"]:
        flag = "READY" if (j["all_hold"] and j["status"] in ("queued", "ready")) else j["status"].upper()
        L.append(f"  {j['id']:<6} {flag:<7} {j.get('title','')[:62]}")
        L.append(f"  {'':<6} claim {j.get('claim') or '-':<12} target {j.get('target') or '-':<12}"
                 f" brief {j.get('brief') or '-'}")
        for c in j["conditions"]:
            L.append(f"  {'':<6}   {'ok ' if c['holds'] else 'NO '} {c['cond']:<28} {c['why']}")
        if j.get("blocked_by"):
            L.append(f"  {'':<6}   >>> blocked: {j['blocked_by']} is active for the same claim")
        if j.get("fired_at"):
            L.append(f"  {'':<6}   fired {j['fired_at']} by {j.get('fired_by')}")
        if j.get("note"):
            L.append(f"  {'':<6}   {j['note'][:92]}")
    return "\n".join(L)


def check() -> int:
    state, why = doc_lock.store_state()
    if state == "ABSENT":
        print(f"  job_queue: SKIP — {why}")
        return 0
    if not QUEUE.exists():
        print("  job_queue: SKIP — no queue in this checkout yet")
        return 0
    rs, bad = rows(), []
    seen = set()
    for r in rs:
        jid = (r.get("id") or "").strip()
        if jid in seen:
            bad.append(f"{jid}: more than one row")
        seen.add(jid)
        if r.get("status") not in STATUSES:
            bad.append(f"{jid}: status {r.get('status')!r} is not one of {', '.join(STATUSES)}")
        if r.get("target") not in TARGETS:
            bad.append(f"{jid}: target {r.get('target')!r} is not one of {', '.join(TARGETS)}")
        if r.get("claim") and r["claim"] not in doc_lock.claim_names():
            bad.append(f"{jid}: claim {r['claim']!r} is not a claim name")
        for c in conds(r):
            if c.partition(":")[0] not in COND_KINDS:
                bad.append(f"{jid}: condition {c!r} is not a kind job_queue understands")
            if c.startswith("job_done:") and find(rs, c.partition(":")[2]) is None:
                bad.append(f"{jid}: waits for {c.partition(':')[2]}, which is not in the queue")
        b = r.get("brief") or ""
        if r.get("status") not in ("done",) and b and not (REPO / b).exists() and not _git_has(b):
            bad.append(f"{jid}: brief {b} is neither in the tree nor on main")
        if r.get("status") == "fired" and not r.get("fired_at"):
            bad.append(f"{jid}: fired with no fired_at")
    # two ACTIVE jobs on one claim is the guard failing, not a style point
    byclaim: dict[str, list[str]] = {}
    for r in rs:
        if r.get("status") in ACTIVE and r.get("claim"):
            byclaim.setdefault(r["claim"], []).append(r["id"])
    for cl, ids in byclaim.items():
        if len(ids) > 1:
            bad.append(f"{cl}: {len(ids)} active jobs ({', '.join(ids)}); one job per claim at a time")
    if bad:
        print(f"  job_queue: FAIL — {len(bad)} problem(s):")
        for b in bad:
            print(f"      {b}")
        return 1
    n = {s: len([r for r in rs if r.get("status") == s]) for s in STATUSES}
    print(f"  job_queue: OK — {len(rs)} job(s): " + ", ".join(f"{v} {k}" for k, v in n.items() if v))
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
        for k in ("NRG_CHAT", "NRG_NO_PRIVATE_STORE", "NRG_SESSION_LINK"):
            env.pop(k, None)
        env.update({k: v for k, v in env_extra.items() if v is not None})
        p = subprocess.run([sys.executable, str(HERE / "tools/job_queue.py"), *args],
                           capture_output=True, text=True, env=env, cwd=str(HERE))
        return p.returncode, p.stdout + p.stderr

    def mk(tree, rows_):
        (tree / "working").mkdir(parents=True, exist_ok=True)
        # the brief has to be readable in the throwaway tree: a job never fires a prompt nobody can
        # read, so without this every fire below would refuse for the right reason at the wrong time
        for r in rows_:
            if r.get("brief"):
                b = tree / r["brief"]
                b.parent.mkdir(parents=True, exist_ok=True)
                if not b.exists() and "does_not_exist" not in r["brief"]:
                    b.write_text("# throwaway brief\n", encoding="utf-8")
        import csv as _csv
        with (tree / "working/job_queue.csv").open("w", encoding="utf-8", newline="") as fh:
            w = _csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows_)

    with tempfile.TemporaryDirectory() as td:
        T = pathlib.Path(td)
        brief = "notes/specs/NRG_brief_script55_build_2026-11-05.md"

        # 1. No private store: nothing fires, nothing is added, and the queue reads UNKNOWN (D-300).
        t1 = doc_lock._mktree(T / "public_only", private=False, lock=None)
        mk(t1, [{"id": "J-1", "title": "t", "brief": brief, "claim": "pipeline",
                 "waits_for": "claim_free:pipeline", "target": "new_session", "status": "queued"}])
        rc, out = run([], t1)
        check_("1a no store: the queue reads UNKNOWN", "UNKNOWN" in out and "NOTHING fires" in out, out)
        rc, out = run(["fire", "J-1", "--by", "X"], t1)
        check_("1b no store: fire refuses", rc == 1, out)
        rc, out = run(["add", "--id", "J-9", "--title", "t", "--target", "notify"], t1)
        check_("1c no store: add refuses", rc == 1, out)

        # 2. A condition that does not hold refuses, and says which.
        t2 = doc_lock._mktree(T / "held", private=True, lock={
            "holder": None, "claims": {"pipeline": {"chat": "Other", "since": doc_lock._ago(1)}}})
        mk(t2, [{"id": "J-1", "title": "t", "brief": brief, "claim": "pipeline",
                 "waits_for": "claim_free:pipeline", "target": "new_session", "status": "queued"}])
        rc, out = run(["fire", "J-1", "--by", "X"], t2)
        check_("2a a job never fires into a held claim", rc == 1 and "held by 'Other'" in out, out)
        rc, out = run(["ready"], t2)
        check_("2b and it is not ready", "no job is ready" in out, out)

        # 3. The claim frees: it becomes ready, fires once, and refuses the second time.
        t3 = doc_lock._mktree(T / "free", private=True, lock={"holder": None, "claims": {}})
        mk(t3, [{"id": "J-1", "title": "Script 55", "brief": brief, "claim": "pipeline",
                 "waits_for": "claim_free:pipeline", "target": "new_session", "status": "queued"},
                {"id": "J-2", "title": "Paper M passages", "brief": brief, "claim": "",
                 "waits_for": "job_done:J-1", "target": "notify", "status": "queued"}])
        rc, out = run(["ready"], t3)
        check_("3a J-1 is ready, J-2 is not", "READY  J-1" in out and "J-2" not in out, out)
        rc, out = run(["fire", "J-1", "--by", "control board"], t3)
        check_("3b J-1 fires", rc == 0 and "FIRED  J-1" in out, out)
        rc, out = run(["fire", "J-1", "--by", "control board"], t3)
        check_("3c a fired job does not fire twice", rc == 1 and "already fired" in out, out)
        rc, out = run(["done", "J-1"], t3)
        check_("3d done J-1 reports that J-2 became ready", "J-2" in out, out)
        rc, out = run(["fire", "J-2", "--by", "control board"], t3)
        check_("3e a notify job fires without starting a session", rc == 0 and "notify" in out, out)

        # 4. One job per claim at a time, and held_by_martin never holds.
        t4 = doc_lock._mktree(T / "two", private=True, lock={"holder": None, "claims": {}})
        mk(t4, [{"id": "J-1", "title": "a", "brief": brief, "claim": "pipeline",
                 "waits_for": "", "target": "new_session", "status": "fired", "fired_at": now()},
                {"id": "J-2", "title": "b", "brief": brief, "claim": "pipeline",
                 "waits_for": "", "target": "new_session", "status": "queued"},
                {"id": "J-3", "title": "c", "brief": brief, "claim": "",
                 "waits_for": "held_by_martin", "target": "notify", "status": "queued"}])
        rc, out = run(["fire", "J-2", "--by", "X"], t4)
        check_("4a one job per claim: the second refuses", rc == 1 and "same claim" in out, out)
        rc, out = run(["fire", "J-3", "--by", "X"], t4)
        check_("4b held_by_martin never fires", rc == 1 and "held by Martin" in out, out)

        # 5. A brief nobody can read never fires - a prompt that points nowhere is not a job.
        t5 = doc_lock._mktree(T / "nobrief", private=True, lock={"holder": None, "claims": {}})
        # assembled rather than written out: docref_lint reads any *.md token in tools/*.py as a
        # citation of a document that should exist, and this one must NOT exist - that is the test.
        absent = "notes/specs/does_not_exist" + ".md"
        mk(t5, [{"id": "J-1", "title": "t", "brief": absent, "claim": "",
                 "waits_for": "", "target": "new_session", "status": "queued"}])
        rc, out = run(["fire", "J-1", "--by", "X"], t5)
        check_("5a a missing brief refuses", rc == 1 and "nor on main" in out, out)
        rc, out = run(["--check"], t5)
        check_("5b and the gate names it", rc == 1 and "brief" in out, out)

        # 6. The gate: an unknown condition kind, a dangling job_done, two active on one claim.
        t6 = doc_lock._mktree(T / "gate", private=True, lock={"holder": None, "claims": {}})
        mk(t6, [{"id": "J-1", "title": "t", "brief": brief, "claim": "",
                 "waits_for": "when_martin_feels_like_it;job_done:J-7", "target": "sideways",
                 "status": "queued"}])
        rc, out = run(["--check"], t6)
        check_("6a unknown kind, dangling job_done and bad target all fail",
               rc == 1 and "when_martin_feels_like_it" in out and "J-7" in out and "sideways" in out, out)
        rc, out = run(["add", "--id", "J-2", "--title", "t", "--target", "new_session",
                       "--waits-for", "nonsense:x"], t6)
        check_("6b add refuses an unknown condition kind", rc == 1 and "not understood" in out, out)

        # 7. on_main reads the PRIVATE repo for a working/ path. Neither git dir here is a real
        #    repository, so both answer no - what is tested is that it does not crash and does not
        #    say yes, which is the safe direction for a condition.
        t7 = doc_lock._mktree(T / "onmain", private=True, lock={"holder": None, "claims": {}})
        mk(t7, [{"id": "J-1", "title": "t", "brief": brief, "claim": "",
                 "waits_for": "on_main:working/job_queue.csv", "target": "notify", "status": "queued"}])
        rc, out = run(["fire", "J-1", "--by", "X"], t7)
        check_("7a on_main for a working/ path does not fire on a tree with no private main",
               rc == 1 and "not on main yet" in out, out)

    print("job_queue selftest: " + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?",
                    choices=["list", "add", "ready", "fire", "done", "hold", "unhold"], default="list")
    ap.add_argument("job", nargs="?")
    ap.add_argument("--id", dest="jid", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--claim", default="")
    ap.add_argument("--waits-for", dest="waits_for", default="")
    ap.add_argument("--target", default="new_session")
    ap.add_argument("--note", default="")
    ap.add_argument("--by", default=os.environ.get("NRG_CHAT", ""))
    ap.add_argument("--trigger-id", dest="trigger_id", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()
    if a.check:
        return check()
    if a.json:
        print(json.dumps(collect(), indent=2))
        return 0
    if a.cmd == "add":
        if not a.jid or not a.title:
            print("  REFUSED — --id and --title are both needed", file=sys.stderr)
            return 1
        return add(a.jid, a.title, a.brief, a.claim, a.waits_for, a.target, a.note)
    if a.cmd == "ready":
        ready()
        return 0
    if a.cmd in ("fire", "done", "hold", "unhold"):
        jid = a.job or a.jid
        if not jid:
            print(f"  REFUSED — name the job: job_queue.py {a.cmd} J-1", file=sys.stderr)
            return 1
        if a.cmd == "fire":
            return fire(jid, a.by, a.trigger_id, a.dry_run)
        return set_status(jid, {"done": "done", "hold": "held", "unhold": "queued"}[a.cmd], a.note)
    print(render(collect()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
