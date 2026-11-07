#!/usr/bin/env python3
"""chat_register — the compulsory register of chats working on this project (NRG HQ, D-301).

Several chats work in one tree at once (spec NRG_spec_parallel_chats_2026-10-10), and until now
nothing recorded that a chat existed. The claims in working/DOCUMENT_LOCK.json say who holds what
RIGHT NOW and nothing about who has been here, what they were for, or what came of them; a chat that
released its claim left no trace but its commits. So nobody could answer "which chats are working on
this, and are they following the rules?" without asking each one.

A chat registers BEFORE its first commit or claim:

    python3 tools/chat_register.py register --chat "Paper M editing" --kind document \
        --claim doc:PaperM --purpose "v1_41 onward: plain guide, abstract, journal fit"

WHY A SEPARATE REGISTER AND NOT THE LOCK (D-301)

  The lock is state: it must be small, and a release must empty it. This is history: a row stays
  after the claim goes, carrying what the chat was for and how it ended. Putting both in one file
  would mean either a lock that grows without bound or a history that a release erases.

  It is PRIVATE (working/), like the lock and for the same reason: chat names, purposes and session
  links are Martin's working material, not part of a public repository (D-300's R6 constraint).

  It is written through register_io, so two chats registering at the same moment merge row by row
  rather than overwriting each other - the same guarantee the tools/ CSV registers have.

WHAT IT IS NOT

  It is not enforcement. Phase 1 WARNS: an unregistered chat is reported by the gate and by the HQ
  agent, and `doc_lock take` says so, but nothing is refused. The refusal (spec D3) waits until
  registration has been running for a few days, because a refusal that fires on every chat before
  the habit exists would be a tool nobody uses.

Usage:
  python3 tools/chat_register.py                       # the register, newest activity first
  python3 tools/chat_register.py register --chat NAME --kind KIND [--claim C] [--purpose P] [--link L]
  python3 tools/chat_register.py status --chat NAME --set active|parked|done [--outcome TEXT]
  python3 tools/chat_register.py --json | --check | --selftest
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) — 2026-11-05. `registered_by`: a row written for another
#   chat is SEEDED, not self-reported, and says so. The build seeded the Paper M chat's row from its claim note, and
#   "every chat registers itself" is a rule the HQ agent audits - a seeded row is not evidence of it.
# 1.0.0  # Hollingham (2026) — 2026-11-05 (D-301, spec NRG_handover_HQ_page_2026-11-05 §6,
#   signed off). First issue: the compulsory chat register, private, merged row by row, warn-only in phase 1.

import argparse
import datetime
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE).resolve()
sys.path.insert(0, str(HERE / "tools"))

import register_io                                                    # noqa: E402
import doc_lock                                                       # noqa: E402

REGISTER = REPO / "working/chat_register.csv"
# `hq_row` (2026-11-06, T-152): the id of the chats row the HQ page seeded when Martin started this
# chat from its launcher, passed in by `--adopt`. hq_snapshot writes the chat AT that id, so the
# registration OVERWRITES the seed instead of adding a second document. Empty for a chat started by
# hand, which has no seeded row - and that case falls back to the slug (see hq_snapshot.db_ops).
FIELDS = ["chat", "kind", "claim", "mode", "link", "opened", "touched", "status", "purpose",
          "outcome", "registered_by", "hq_row"]

# The five kinds of work the HQ start console offers (spec §4.2). A kind outside this list is not
# refused - a chat that does something new should say so rather than pick the nearest wrong word -
# but the gate names it, so the list grows deliberately.
KINDS = ("pipeline", "document", "tools", "readonly", "fieldwork")
STATUSES = ("starting", "active", "parked", "done")


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def need_store(what: str) -> bool:
    """doc_lock.refuse_absent_store() PRINTS the refusal; it does not decide or exit. So every
    caller guards it, and this is that guard in one place."""
    if doc_lock.store_ok():
        return True
    doc_lock.refuse_absent_store(what)
    return False


def rows() -> list[dict]:
    return [r for r in register_io.read_rows(REGISTER) if (r.get("chat") or "").strip()]


def save(rs: list[dict]) -> None:
    REGISTER.parent.mkdir(parents=True, exist_ok=True)
    register_io.write_rows(REGISTER, FIELDS, rs,
                           sort_key=lambda r: (r.get("touched") or r.get("opened") or ""),
                           key_cols=["chat"])
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
        doc_lock.publish_records(("working/chat_register.csv",), "chat register")
    except Exception:
        pass



def find(rs: list[dict], chat: str) -> dict | None:
    for r in rs:
        if (r.get("chat") or "").strip() == chat.strip():
            return r
    return None


def is_registered(chat: str | None) -> bool:
    """Used by doc_lock's warning. A missing register is not an unregistered chat: it is a tree
    that has never had one, and saying "you are not registered" there would be a lie."""
    if not chat or not REGISTER.exists():
        return False
    return find(rows(), chat) is not None


def register(chat: str, kind: str, claim: str, purpose: str, link: str, status: str,
             by: str | None = None, hq_row: str = "") -> int:
    """`by` is the chat doing the registering. When it is not the chat being registered the row is
    SEEDED, not self-reported, and says so - which matters, because "every chat registers itself"
    is the rule the HQ agent audits, and a row written on another chat's behalf is not evidence of
    that chat having read the rule. It also means `mode` was derived from the registering session,
    not the registered one."""
    if not need_store("register a chat"):
        return 1
    rs = rows()
    r = find(rs, chat)
    if r is None:
        r = {"chat": chat, "opened": now()}
        rs.append(r)
        what = "registered"
    else:
        what = "updated"
    r.update({k: v for k, v in (("kind", kind), ("claim", claim), ("purpose", purpose),
                                ("link", link), ("status", status), ("hq_row", hq_row)) if v})
    me = (by or doc_lock.chat_id() or chat).strip()
    seeded = me != chat.strip()
    if not seeded or not r.get("mode"):
        r["mode"] = doc_lock.session_mode()
    r["registered_by"] = me
    r["touched"] = now()
    save(rs)
    print(f"  chat {what}: {chat!r}  kind {r.get('kind') or '?'}  mode {r.get('mode') or '?'}"
          + (f"  claim {r['claim']}" if r.get("claim") else ""))
    if seeded:
        print(f"    SEEDED by {me!r}, not self-reported — mode was derived from this session, and")
        print(f"    this row is not evidence that {chat!r} has read the registration rule")
    if kind and kind not in KINDS:
        print(f"    note: kind {kind!r} is not one of {', '.join(KINDS)} - the gate will name it")
    return 0


def set_status(chat: str, status: str, outcome: str) -> int:
    if not need_store("set a chat's status"):
        return 1
    rs = rows()
    r = find(rs, chat)
    if r is None:
        print(f"  REFUSED — {chat!r} is not in {REGISTER.name}; register it first", file=sys.stderr)
        return 1
    r["status"] = status
    r["touched"] = now()
    if outcome:
        r["outcome"] = outcome
    # A chat that is done must not still hold a claim: say so rather than release it (the HQ agent
    # reports and never intervenes, and so does this).
    held = doc_lock.holder_of(r.get("claim")) if r.get("claim") else None
    save(rs)
    print(f"  {chat!r} is now {status}")
    if status == "done" and held == doc_lock.chat_id(chat):
        print(f"    >>> it still holds {r['claim']}: release it, or the board will show it held")
    return 0


def collect() -> dict:
    state, why = doc_lock.store_state()
    return {"store": state, "store_why": why, "present": REGISTER.exists(),
            "chats": rows() if state != "ABSENT" else []}


def render(B: dict) -> str:
    L = ["CHAT REGISTER (tools/chat_register.py)"]
    if B["store"] == "ABSENT":
        L.append(f"  PRIVATE STORE ABSENT - {B['store_why']}")
        L.append("    >>> the register is UNKNOWN from here, not empty (D-300)")
        return "\n".join(L)
    if not B["present"]:
        L.append("  no register yet - the first `register` call writes it")
        return "\n".join(L)
    if not B["chats"]:
        L.append("  no chats registered")
        return "\n".join(L)
    for r in sorted(B["chats"], key=lambda r: (r.get("touched") or ""), reverse=True):
        seeded = (r.get("registered_by") or r.get("chat")) != r.get("chat")
        L.append(f"  {r.get('chat',''):<28} {r.get('status') or '?':<9} {r.get('kind') or '?':<9}"
                 f" {r.get('claim') or '-':<18} {r.get('mode') or '?'}"
                 + (f"   (seeded by {r['registered_by']!r})" if seeded else ""))
        if r.get("purpose"):
            L.append(f"    {'':<28} {r['purpose'][:90]}")
        if r.get("outcome"):
            L.append(f"    {'':<28} -> {r['outcome'][:88]}")
    return "\n".join(L)


def check() -> int:
    """Gate: the register's own consistency. An unregistered chat is NOT failed here - that is the
    HQ agent's finding, and phase 1 is warn-only (spec D3, §11 phase 4)."""
    state, why = doc_lock.store_state()
    if state == "ABSENT":
        print(f"  chat_register: SKIP — {why}")
        return 0
    if not REGISTER.exists():
        print("  chat_register: SKIP — no register in this checkout yet")
        return 0
    rs, bad = rows(), []
    seen = set()
    for r in rs:
        c = (r.get("chat") or "").strip()
        if c in seen:
            bad.append(f"{c!r}: more than one row")
        seen.add(c)
        if r.get("status") and r["status"] not in STATUSES:
            bad.append(f"{c!r}: status {r['status']!r} is not one of {', '.join(STATUSES)}")
        if r.get("kind") and r["kind"] not in KINDS:
            bad.append(f"{c!r}: kind {r['kind']!r} is not one of {', '.join(KINDS)}")
        if r.get("claim") and r["claim"] not in doc_lock.claim_names():
            bad.append(f"{c!r}: claim {r['claim']!r} is not a claim name")
        if not r.get("opened"):
            bad.append(f"{c!r}: no opened date")
    # a claim held by a chat with no row: the warning phase 1 is for
    unreg = [f"{n} held by {h!r}" for n in doc_lock.claim_names()
             if (h := doc_lock.holder_of(n)) and not find(rs, h)]
    if bad:
        print(f"  chat_register: FAIL — {len(bad)} row problem(s):")
        for b in bad:
            print(f"      {b}")
        return 1
    print(f"  chat_register: OK — {len(rs)} chat(s)"
          + (f"; {len(rs) - len([r for r in rs if r.get('status') == 'done'])} not done" if rs else ""))
    for u in unreg:
        print(f"    >>> UNREGISTERED chat holds a claim: {u} (register it; warn-only in phase 1)")
    return 0


def _selftest() -> int:
    import tempfile
    import subprocess
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
        p = subprocess.run([sys.executable, str(HERE / "tools/chat_register.py"), *args],
                           capture_output=True, text=True, env=env, cwd=str(HERE))
        return p.returncode, p.stdout + p.stderr

    with tempfile.TemporaryDirectory() as td:
        T = pathlib.Path(td)

        # 1. No private store: the register cannot be read OR written (D-300 applied here).
        t1 = doc_lock._mktree(T / "public_only", private=False, lock=None)
        rc, out = run(["register", "--chat", "X", "--kind", "tools"], t1)
        check_("1a no store: register refuses", rc == 1, out)
        rc, out = run([], t1)
        check_("1b no store: the listing says UNKNOWN, not empty", "UNKNOWN" in out, out)
        check_("1c no store: --check skips rather than passing", (run(["--check"], t1)[0] == 0)
               and "SKIP" in run(["--check"], t1)[1], out)

        # 2. Register, update, status, outcome.
        t2 = doc_lock._mktree(T / "both", private=True, lock={"holder": None, "claims": {}})
        rc, out = run(["register", "--chat", "Paper M", "--kind", "document",
                       "--claim", "doc:PaperM", "--purpose", "read-through"], t2)
        check_("2a register succeeds", rc == 0 and "registered" in out, out)
        rs = register_io.read_rows(t2 / "working/chat_register.csv")
        check_("2b one row, with opened and mode", len(rs) == 1 and rs[0]["opened"] and rs[0]["mode"], str(rs))
        rc, out = run(["register", "--chat", "Paper M", "--kind", "document",
                       "--purpose", "abstract too"], t2)
        check_("2c a second register UPDATES, never duplicates",
               len(register_io.read_rows(t2 / "working/chat_register.csv")) == 1, out)
        rc, out = run(["status", "--chat", "Paper M", "--set", "done", "--outcome", "v1_42 shipped"], t2)
        check_("2d status done", rc == 0, out)
        rs = register_io.read_rows(t2 / "working/chat_register.csv")
        check_("2e outcome kept", rs[0]["status"] == "done" and rs[0]["outcome"] == "v1_42 shipped", str(rs))
        rc, out = run(["status", "--chat", "Nobody", "--set", "done"], t2)
        check_("2f status refuses an unregistered chat", rc == 1, out)
        # 1.0.1: a row written on another chat's behalf is marked, because the rule the HQ agent
        # audits is that each chat registers ITSELF.
        rc, out = run(["register", "--chat", "Someone else", "--kind", "tools",
                       "--by", "control board"], t2)
        check_("2g a row for another chat says it was seeded", "SEEDED by 'control board'" in out, out)
        rs = register_io.read_rows(t2 / "working/chat_register.csv")
        other = [r for r in rs if r["chat"] == "Someone else"][0]
        check_("2h and records who wrote it", other["registered_by"] == "control board", str(other))
        rc, out = run(["register", "--chat", "Self", "--kind", "tools", "--by", "Self"], t2)
        check_("2i a self-registration is not marked", "SEEDED" not in out, out)

        # 3. A `done` chat that still holds its claim is TOLD, not released for it.
        t3 = doc_lock._mktree(T / "still_held", private=True, lock={
            "holder": None, "claims": {"doc:PaperM": {"chat": "Paper M", "since": doc_lock._ago(1)}}})
        run(["register", "--chat", "Paper M", "--kind", "document", "--claim", "doc:PaperM"], t3)
        rc, out = run(["status", "--chat", "Paper M", "--set", "done"], t3)
        check_("3a a done chat still holding a claim is told", "still holds doc:PaperM" in out, out)
        check_("3b and the claim is NOT released", bool(json.loads(
            (t3 / "working/DOCUMENT_LOCK.json").read_text())["claims"].get("doc:PaperM")), out)

        # 4. The gate: a bad status fails, an unregistered holder only warns.
        t4 = doc_lock._mktree(T / "gate", private=True, lock={
            "holder": None, "claims": {"tools": {"chat": "Ghost", "since": doc_lock._ago(1)}}})
        run(["register", "--chat", "Real", "--kind", "tools"], t4)
        rc, out = run(["--check"], t4)
        check_("4a an unregistered holder warns but does not fail", rc == 0 and "UNREGISTERED" in out, out)
        p = t4 / "working/chat_register.csv"
        p.write_text(p.read_text().replace(",Real,", ",Real,").replace("\n", "\n", 1) +
                     "Bad,tools,,laptop,,2026-11-05,,nonsense,,\n")
        rc, out = run(["--check"], t4)
        check_("4b a status outside the list fails", rc == 1 and "nonsense" in out, out)

    print("chat_register selftest: " + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", choices=["register", "status", "list"], default="list")
    ap.add_argument("--chat", default=os.environ.get("NRG_CHAT"))
    ap.add_argument("--kind", default="")
    ap.add_argument("--claim", default="")
    ap.add_argument("--purpose", default="")
    ap.add_argument("--adopt", default="", metavar="HQ_ROW",
                    help="the chats row id the HQ page seeded for this chat (T-152): the registration "
                         "then overwrites that row instead of creating a second one. The HQ brief "
                         "carries it; omit it for a chat started by hand.")
    ap.add_argument("--outcome", default="")
    ap.add_argument("--link", default=os.environ.get("NRG_SESSION_LINK", ""))
    ap.add_argument("--by", default=os.environ.get("NRG_CHAT"),
                    help="the chat doing the registering; a row for another chat is marked SEEDED")
    ap.add_argument("--set", dest="set_to", choices=list(STATUSES))
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
    if a.cmd == "register":
        if not a.chat:
            print("  REFUSED — --chat (or NRG_CHAT) names the chat", file=sys.stderr)
            return 1
        return register(a.chat, a.kind, a.claim, a.purpose, a.link, "active", a.by, a.adopt)
    if a.cmd == "status":
        if not a.chat or not a.set_to:
            print("  REFUSED — --chat and --set are both needed", file=sys.stderr)
            return 1
        return set_status(a.chat, a.set_to, a.outcome)
    print(render(collect()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
