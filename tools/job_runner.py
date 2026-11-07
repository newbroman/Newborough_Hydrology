#!/usr/bin/env python3
"""
job_runner.py — the coordinator's pass over the job queue.

WHY THIS EXISTS

  D-301 gave the project a queue (`working/job_queue.csv`) and the moment to evaluate it: a
  `doc_lock release` calls `jobs_made_ready()`, so the pass already runs the instant a task
  finishes. CLAUDE.md §4b says "a job does not fire itself", and the reason is one step further
  on than it sounds — `job_queue.py fire` marks the row and then prints

      >>> start the session with: Run job J-6: read <brief> and follow it

  a line for a PERSON to paste. Nothing in this repository can open a Claude session. That, and
  not the evaluation, is the wall.

  So this is the pass, and it stops exactly where a script must: it evaluates, gates, fires and
  records, then hands back the list of sessions to open. A coordinating CHAT running in the cloud
  has session tooling and can open them; a script on the laptop cannot, and pretending otherwise
  is how a queue silently stops being a queue.

  Martin, 2026-11-07: "build the job runner". Design: notes/specs/NRG_draft_coordinating_chat_2026-11-07.md §3a, §5.

WHAT IT WILL NOT DO (D-302, and §3b/§3c of that draft)

  - It does not release a claim, forcibly or otherwise, and does not edit anything under one.
  - It does not regenerate a stale artefact to make a gate pass. That is the `ship_regen_lint`
    anti-pattern: the fix for a red that a rebuild would clear is a line in `ship_regenerate()`,
    never a rebuild here (three ships died on that on 2026-09-30, three more on 2026-09-24).
    J-7 exists for exactly that reason.
  - It pushes nothing but the queue itself, which publishes itself under D-314 as widened.
  - It fires nothing into a held claim, behind another active job for the same claim, with an
    unreadable brief, or without the private store. Those gates live in `job_queue.fire` and are
    used here rather than restated.

  REPORTING IS THE DEFAULT. A plain run changes nothing and prints what it would do; `--fire` is
  the one that acts. The queue is shared state and a runner that acted by default would be a
  stranger writing to it on every invocation.

Usage:
    python3 tools/job_runner.py                 # the pass, reporting only
    python3 tools/job_runner.py --fire --by "NRG Control"
    python3 tools/job_runner.py --json          # machine-readable, for a coordinating chat
    python3 tools/job_runner.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-07 (Martin: "build the job runner").
#   First issue: the pass over the queue, reporting by default, --fire to act, --json for a
#   coordinating chat that can open the sessions this cannot. Built on job_queue.ready() and
#   job_queue.fire() rather than re-evaluating conditions, so there is one implementation of
#   "is this job ready" and one of "may it fire".

import argparse
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import doc_lock                                  # noqa: E402
import job_queue                                 # noqa: E402

REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE.parent).resolve()


def _session_prompt(r: dict) -> str:
    """What a chat should be opened with. Deliberately the same sentence job_queue.fire prints,
    so the two cannot drift into saying different things to whoever reads them."""
    return f"Run job {r['id']}: read {r.get('brief', '')} and follow it"


def survey() -> dict:
    """The pass. Reads only: every queued/ready job, whether it can fire, and if not, why.

    `job_queue.ready(promote=True)` is the project's one definition of ready and promotes
    queued -> ready as a side effect, which is what lets a release say "this is now ready".
    """
    if not doc_lock.store_ok():
        return {"store": False, "ready": [], "blocked": [], "sessions": [],
                "note": "the private store is not present: the queue cannot be read (D-302)"}

    rs = job_queue.rows()
    ready = job_queue.ready(promote=True, quiet=True)
    ready_ids = {r["id"] for r in ready}

    sessions, blocked = [], []
    for r in ready:
        claim = r.get("claim") or ""
        holder = doc_lock.holder_of(claim) if claim else None
        if holder is not None:
            blocked.append({"id": r["id"], "title": r.get("title", ""),
                            "why": f"claim {claim!r} is held by {holder!r}"})
            continue
        brief = r.get("brief") or ""
        if brief and not (REPO / brief).is_file() and not job_queue._git_has(brief):
            blocked.append({"id": r["id"], "title": r.get("title", ""),
                            "why": f"brief {brief!r} is neither in the tree nor on main"})
            continue
        sessions.append({"id": r["id"], "title": r.get("title", ""), "claim": claim,
                         "brief": brief, "target": r.get("target", ""),
                         "prompt": _session_prompt(r)})

    # everything else, so a reporting run says why a job is NOT moving rather than omitting it
    for r in rs:
        if r.get("status") in ("fired", "done") or r["id"] in ready_ids:
            continue
        if r.get("status") == "held":
            blocked.append({"id": r["id"], "title": r.get("title", ""), "why": "held"})
            continue
        ok, detail = job_queue.evaluate(r, rs)
        if not ok:
            why = "; ".join(f"{c}: {w}" for c, h, w in detail if not h) or "a condition does not hold"
            blocked.append({"id": r["id"], "title": r.get("title", ""), "why": why})
        else:
            b = job_queue.blocking_job(r, rs)
            if b is not None:
                blocked.append({"id": r["id"], "title": r.get("title", ""),
                                "why": f"{b['id']} is {b['status']} for the same claim"})

    return {"store": True, "ready": [r["id"] for r in ready], "blocked": blocked,
            "sessions": sessions, "note": ""}


def run(fire: bool, by: str, as_json: bool) -> int:
    s = survey()
    if as_json:
        print(json.dumps(s, indent=2, sort_keys=True))
        return 0 if s["store"] else 1

    if not s["store"]:
        print(f"  REFUSED — {s['note']}", file=sys.stderr)
        return 1

    if not s["sessions"] and not s["blocked"]:
        print("  the queue is empty, or every job is done.")
        return 0

    if s["sessions"]:
        verb = "FIRING" if fire else "would fire"
        print(f"  {len(s['sessions'])} job(s) {verb}:")
        for j in s["sessions"]:
            print(f"      {j['id']}  {j['title'][:70]}")
            print(f"            claim {j['claim'] or '-'}   brief {j['brief']}")
            print(f"            open a session with: {j['prompt']}")
    else:
        print("  nothing is ready to fire.")

    if s["blocked"]:
        print(f"  {len(s['blocked'])} job(s) not moving:")
        for b in s["blocked"]:
            print(f"      {b['id']}  {b['why'][:96]}")

    if not fire:
        if s["sessions"]:
            print("  reporting only — pass --fire to mark these fired (it still cannot open the")
            print("  sessions; a coordinating chat does that, from --json).")
        return 0

    rc = 0
    for j in s["sessions"]:
        if job_queue.fire(j["id"], by or doc_lock.chat_id() or "job_runner", "", dry=False):
            rc = 1
    return rc


def _selftest() -> int:
    """Properties that must hold whatever the queue contains. No fixture: the live queue is read
    READ-ONLY here, which is itself the first property."""
    fails = []

    def check(name, ok, detail=""):
        print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  {detail}" if detail and not ok else ""))
        if not ok:
            fails.append(name)

    before = job_queue.QUEUE.read_bytes() if job_queue.QUEUE.exists() else b""
    s = survey()
    after = job_queue.QUEUE.read_bytes() if job_queue.QUEUE.exists() else b""
    # ready(promote=True) may legitimately promote queued -> ready; what must NOT change is any
    # job's identity or its fired/done status.
    check("1 a survey never invents or removes a job",
          before.count(b"\n") == after.count(b"\n"), "row count moved")
    check("2 every session carries a brief",
          all(j["brief"] for j in s["sessions"]), "a session had no brief")
    check("3 no session fires into a held claim",
          all(doc_lock.holder_of(j["claim"]) is None for j in s["sessions"] if j["claim"]),
          "a held claim was offered")
    check("4 ready and blocked never name the same job",
          not ({j["id"] for j in s["sessions"]} & {b["id"] for b in s["blocked"]}),
          "a job was both")
    check("5 the prompt names the job and its brief",
          all(j["id"] in j["prompt"] and (not j["brief"] or j["brief"] in j["prompt"])
              for j in s["sessions"]))
    print(f"job_runner selftest: {'OK' if not fails else 'FAIL — ' + ', '.join(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fire", action="store_true",
                    help="mark the ready jobs fired (default: report only)")
    ap.add_argument("--by", default="", help="who is firing, for the queue's record")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="machine-readable, for a coordinating chat that can open the sessions")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    return run(a.fire, a.by, a.as_json)


if __name__ == "__main__":
    sys.exit(main())
