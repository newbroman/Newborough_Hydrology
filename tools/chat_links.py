#!/usr/bin/env python3
"""chat_links — put each chat's conversation URL in the register, so the HQ page can link to it.

Martin, 2026-11-21: *"I need to archive chats that are complete. I can't tell which chat I should
go back to in the project."* The register already says which chats are done and which hold a claim
(tools/chat_register.py, D-301), and the HQ page already renders a chat's name as a hyperlink when
its `link` column is set - but on 2026-11-21 only 3 of 26 rows had one, and all three held a BARE
session id rather than a URL, so the page emitted href="session_0121..." and every link on it was
dead. Matching a row to a conversation in the app was therefore done by eye, against the sidebar.

WHERE THE LINK COMES FROM

  Every commit this project's sessions make carries a `Claude-Session:` trailer, which IS the
  conversation's URL. So a chat that committed anything has already published its own link; it was
  simply never written down. This tool reads both repositories' commits and puts it in the register.

WHAT IT WILL NOT DO, AND WHY (the whole design)

  A session is matched to a chat ONLY by the job or task id in the chat's own name - `Paper 1 J-19`
  against subjects naming `J-19` - and `\b` boundaries keep J-19 off J-19b's commits.

  Matching by TIME was tried first and is deliberately not used. Sessions overlap: scoring every
  commit that falls inside a row's opened..touched window gave `Paper M proofread` the session that
  belongs to `Plain report J-16`, and handed one unrelated session to three different rows. A wrong
  link is worse than none here, because it is a link Martin would click and believe. So a row whose
  name carries no id is reported UNRESOLVED and left alone: the live chats all carry one, which is
  the half that matters, and the rest are closed.

  An existing link is never replaced, only normalised (bare id -> URL). `--force` is not offered.

Usage:
  python3 tools/chat_links.py                 # what it would write, with the evidence
  python3 tools/chat_links.py --write         # fill empty links, normalise bare ids
  python3 tools/chat_links.py --check         # a malformed link is a FAIL; missing ones are a count
  python3 tools/chat_links.py --json | --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-21. First issue (Martin: "I can't tell which chat
#   I should go back to"). Links derived from Claude-Session trailers, id-matched only; bare ids normalised.

import argparse
import collections
import csv
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE).resolve()
sys.path.insert(0, str(HERE / "tools"))

import register_io                                                    # noqa: E402
import doc_lock                                                       # noqa: E402

REGISTER = REPO / "working/chat_register.csv"
FIELDS = ["chat", "kind", "claim", "mode", "link", "opened", "touched", "status", "purpose",
          "outcome", "registered_by", "hq_row"]
BASE = "https://claude.ai/code/"
ID_IN_NAME = re.compile(r"\b([JT]-\d+[a-z]?)\b")
SESSION = re.compile(r"session_[A-Za-z0-9]+")
MAX_COMMITS = 800             # the whole of this project's session-trailer era, with room to spare
MIN_SCORE = 1                 # one commit naming the id is enough: the id is the evidence, not the count
# A subject that OPENS with the id is the chat doing that job ("J-13 / T-197: ship_regenerate ...");
# one that names it in passing is usually another chat writing ABOUT it ("Brief for T-197 / J-13: ...").
# Both were J-13's only two commits, one each, and a straight count called it ambiguous. Leading
# counts for three, mentioned-anywhere for one, so the chat that did the work wins and the chat that
# briefed it does not - without bringing time back in, which is what mismatched in the first place.
LEAD_WEIGHT, MENTION_WEIGHT = 3, 1


def normalise(link: str) -> str:
    """A bare `session_...` becomes its URL. The page renders the value as an href, so a bare id is
    not a weaker link - it is a RELATIVE one, and goes nowhere. Anything else is left untouched."""
    s = (link or "").strip()
    if not s or s.startswith("http"):
        return s
    m = SESSION.fullmatch(s)
    return BASE + s if m else s


def well_formed(link: str) -> bool:
    s = (link or "").strip()
    return (not s) or s.startswith("https://")


def rows() -> list[dict]:
    return [r for r in register_io.read_rows(REGISTER) if (r.get("chat") or "").strip()]


def commits(limit: int = MAX_COMMITS) -> list[dict]:
    """Every commit carrying a Claude-Session trailer, from BOTH halves of the one tree (4f)."""
    out = []
    for private in (False, True):
        gd = REPO / (".git-working" if private else ".git")
        if not gd.exists():
            continue
        p = subprocess.run(["git", "--no-optional-locks", f"--git-dir={gd}", "log", "--all",
                            f"-{limit}", "--format=%h%x1f%cI%x1f%s%x1f"
                            "%(trailers:key=Claude-Session,valueonly)"],
                           capture_output=True, text=True, cwd=str(REPO))
        for line in p.stdout.splitlines():
            f = line.split("\x1f")
            if len(f) == 4 and f[3].strip():
                out.append({"sha": f[0], "when": f[1], "subject": f[2],
                            "session": f[3].strip().splitlines()[0].strip(),
                            "repo": "private" if private else "public"})
    return out


def derive(rs: list[dict] | None = None, cs: list[dict] | None = None) -> list[dict]:
    rs = rows() if rs is None else rs
    cs = commits() if cs is None else cs
    out = []
    for r in rs:
        name = (r.get("chat") or "").strip()
        have = (r.get("link") or "").strip()
        fixed = normalise(have)
        rec = {"chat": name, "status": r.get("status", ""), "claim": r.get("claim", ""),
               "link_now": have, "proposed": fixed or "", "why": "", "action": "none"}
        if have and fixed != have:
            rec.update(action="normalise", why="a bare session id is a relative href and goes nowhere")
        elif have:
            rec.update(action="keep", why="already set")
        else:
            m = ID_IN_NAME.search(name)
            if not m:
                rec.update(action="unresolved",
                           why="the chat's name carries no job or task id, and time alone mismatches")
            else:
                jid = m.group(1)
                pat = re.compile(r"\b" + re.escape(jid) + r"\b")
                lead = re.compile(r"^\W*" + re.escape(jid) + r"\b")
                by, n_lead, n_any = collections.Counter(), collections.Counter(), collections.Counter()
                for c in cs:
                    if not pat.search(c["subject"]):
                        continue
                    leads = bool(lead.match(c["subject"]))
                    by[c["session"]] += LEAD_WEIGHT if leads else MENTION_WEIGHT
                    n_lead[c["session"]] += 1 if leads else 0
                    n_any[c["session"]] += 1
                top = by.most_common(2)
                if not top or top[0][1] < MIN_SCORE:
                    rec.update(action="unresolved", why=f"no commit subject names {jid}")
                elif len(top) > 1 and top[1][1] == top[0][1]:
                    rec.update(action="unresolved",
                               why=f"{jid} is named by {len(top)} sessions with equal weight - ambiguous")
                else:
                    s0 = top[0][0]
                    rec.update(action="fill", proposed=normalise(s0),
                               why=f"{n_any[s0]} commit(s) naming {jid}, {n_lead[s0]} of them leading"
                                   + (f"; next session scores {top[1][1]} against {top[0][1]}"
                                      if len(top) > 1 else ""))
        out.append(rec)
    return out


def write(plan: list[dict]) -> int:
    rs = rows()
    by = {(r.get("chat") or "").strip(): r for r in rs}
    n = 0
    for p in plan:
        if p["action"] in ("fill", "normalise") and p["proposed"]:
            by[p["chat"]]["link"] = p["proposed"]
            n += 1
    if n:
        register_io.write_rows(REGISTER, FIELDS, rs, key_cols=["chat"])
        try:
            doc_lock.publish_records(("working/chat_register.csv",), "chat links")
        except Exception:
            pass
    return n


def report(plan: list[dict]) -> None:
    w = max([len(p["chat"]) for p in plan] + [10])
    for p in sorted(plan, key=lambda p: (p["action"] != "fill", p["chat"])):
        tag = {"fill": "FILL ", "normalise": "FIX  ", "keep": "kept ", "unresolved": "---  ",
               "none": "     "}[p["action"]]
        print(f"  {tag} {p['chat']:<{w}}  {p['proposed'] or '-'}")
        if p["why"] and p["action"] in ("fill", "normalise", "unresolved"):
            print(f"  {'':5} {'':<{w}}  {p['why']}")
    c = collections.Counter(p["action"] for p in plan)
    print(f"\n  {c['fill']} to fill, {c['normalise']} to normalise, {c['keep']} already set, "
          f"{c['unresolved']} unresolved")


def check() -> int:
    if not doc_lock.store_ok():
        print("  chat_links: SKIP — no private store (the register is private)")
        return 0
    if not REGISTER.exists():
        print("  chat_links: SKIP — no chat register in this checkout yet")
        return 0
    rs = rows()
    bad = [r["chat"] for r in rs if not well_formed(r.get("link", ""))]
    if bad:
        print(f"  chat_links: FAIL — {len(bad)} link(s) are not a URL, so the HQ page renders a "
              f"relative href that goes nowhere:")
        for b in bad[:8]:
            print(f"      {b}")
        print("      fix: python3 tools/chat_links.py --write")
        return 1
    live = [r for r in rs if (r.get("status") or "") != "done"]
    without = [r["chat"] for r in live if not (r.get("link") or "").strip()]
    msg = f"  chat_links: OK — {sum(1 for r in rs if (r.get('link') or '').strip())} of {len(rs)} chat(s) link to their conversation"
    if without:
        msg += f"; {len(without)} live chat(s) with no link (advisory): {', '.join(without[:4])}"
    print(msg)
    return 0


def _selftest() -> int:
    ok = True

    def t(label, cond, detail=""):
        nonlocal ok
        if not cond:
            ok = False
            print(f"  FAIL  {label}" + (f"\n        {detail}" if detail else ""))

    t("1a a bare id becomes a URL",
      normalise("session_0121abc") == BASE + "session_0121abc", normalise("session_0121abc"))
    t("1b a URL is left alone", normalise(BASE + "session_x") == BASE + "session_x")
    t("1c empty stays empty", normalise("") == "")
    t("1d something else is not mangled", normalise("ask Martin") == "ask Martin")
    t("1e a bare id is NOT well formed", not well_formed("session_x"))
    t("1f a URL is", well_formed("https://claude.ai/code/session_x") and well_formed(""))

    cs = [{"sha": "1", "when": "", "subject": "J-19: Paper 1 cites Paper M", "session": "session_A", "repo": "public"},
          {"sha": "2", "when": "", "subject": "J-19b: v1_95 fixes", "session": "session_B", "repo": "public"},
          {"sha": "3", "when": "", "subject": "J-19: more", "session": "session_A", "repo": "public"},
          {"sha": "4", "when": "", "subject": "J-7 and J-7 again", "session": "session_C", "repo": "public"},
          {"sha": "5", "when": "", "subject": "J-7 elsewhere", "session": "session_D", "repo": "public"},
          {"sha": "6", "when": "", "subject": "J-13 / T-197: the work itself", "session": "session_W", "repo": "private"},
          {"sha": "7", "when": "", "subject": "Brief for T-197 / J-13: written by another chat", "session": "session_X", "repo": "private"}]
    rs = [{"chat": "Paper 1 J-19", "link": "", "status": "done"},
          {"chat": "Paper 1 J-19b", "link": "", "status": "active"},
          {"chat": "Gates review", "link": "", "status": "done"},
          {"chat": "Tie J-7", "link": "", "status": "done"},
          {"chat": "Old one", "link": "session_Z", "status": "done"},
          {"chat": "Index J-13", "link": "", "status": "active"}]
    p = {x["chat"]: x for x in derive(rs, cs)}
    t("2a J-19 takes its own session", p["Paper 1 J-19"]["proposed"] == BASE + "session_A",
      str(p["Paper 1 J-19"]))
    t("2b J-19 does NOT take J-19b's commits (word boundary)",
      p["Paper 1 J-19"]["why"].startswith("2 commit"), p["Paper 1 J-19"]["why"])
    t("2c J-19b takes its own", p["Paper 1 J-19b"]["proposed"] == BASE + "session_B")
    t("2d a name with no id is unresolved, never guessed",
      p["Gates review"]["action"] == "unresolved" and not p["Gates review"]["proposed"])
    t("2e a tie is unresolved rather than arbitrary",
      p["Tie J-7"]["action"] == "unresolved" and "ambiguous" in p["Tie J-7"]["why"], str(p["Tie J-7"]))
    t("2g the chat that DID the job beats the chat that briefed it (leading id)",
      p["Index J-13"]["action"] == "fill" and p["Index J-13"]["proposed"] == BASE + "session_W",
      str(p["Index J-13"]))
    t("2f an existing bare id is normalised, not re-derived",
      p["Old one"]["action"] == "normalise" and p["Old one"]["proposed"] == BASE + "session_Z")
    print("chat_links selftest: " + ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.check:
        return check()
    if not doc_lock.store_ok():
        doc_lock.refuse_absent_store("read the chat register")
        return 1
    plan = derive()
    if a.json:
        print(json.dumps(plan, indent=2))
        return 0
    report(plan)
    if a.write:
        n = write(plan)
        print(f"  wrote {n} link(s) into {REGISTER.relative_to(REPO)}")
    else:
        print("  nothing written (--write does it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
