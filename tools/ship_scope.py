#!/usr/bin/env python3
"""ship_scope — a ship commits what the shipping chat changed, and holds the rest back.

WHY THIS EXISTS

  Several chats work in one tree on the L14 at once (spec NRG_spec_parallel_chats_2026-10-10). A
  ship staged the public repository with `git add -A`, so whichever chat shipped first committed
  every other chat's unfinished work under its own message, and check_all judged that unfinished
  work too. Claims (tools/doc_lock.py 1.2.0) say which chat is working on what; this module turns
  that into a ship that leaves another chat's work alone.

HOW

  plan     From the ship request (chat, claims, paths) and the tree: every changed file under a
           claim held by ANOTHER chat, and not named in the request's paths, is HELD BACK. Files
           under no claim, or under an unclaimed one, ship as they always did (Martin's own edits,
           the shared registers, the derived files every ship rebuilds).
           Documents need one more step, because their mirrors are rebuilt from the ODTs during the
           ship. For each family another chat holds, the ODT is compared with the committed
           mirror's source stamp (refresh_mirrors 1.3.0):
             same                           nothing unshipped: the family ships with the rest
             a NEWER VERSION FILE           (PaperM_v1_9.odt beside the shipped v1_8) - parked for the
                                            ship, so the mirror is rebuilt from the shipped version
             the shipped file itself edited (report9.odt, public_summary_EN.odt: families with no
                                            version in the name) - the ship STOPS and names the holder.
                                            There is no copy of the shipped state to rebuild from, and
                                            rebuilding from the edit would publish it.
  park     Moves the held-back work out of the way into .ship_hold/<id>/ (gitignored, outside the
           Drive filter): a changed tracked file is copied there and put back to its committed state;
           an untracked one is moved there; a parked ODT is moved there. manifest.json records it all.
  restore  Puts it all back after the ship. A file the ship itself changed meanwhile (a mirror the
           ship rebuilt, a file the pull brought in) is NOT overwritten: it stays in .ship_hold with
           a line saying so, and nothing is lost.
  check    For a cloud ship (its own clone, so nothing to hold back): refuse if a changed file is
           under a claim another chat holds.

Usage:
  python3 tools/ship_scope.py plan    --request FILE [--json]
  python3 tools/ship_scope.py park    --request FILE --id ID
  python3 tools/ship_scope.py restore --id ID
  python3 tools/ship_scope.py check   [--chat NAME]
  python3 tools/ship_scope.py --selftest
Exit: 0 go, 1 refused or stopped (the reason printed), 2 usage.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-10. First issue (spec NRG_spec_parallel_chats_2026-10-10).

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
HOLD = REPO / ".ship_hold"

_STAMP_RE = re.compile(r"GENERATED MIRROR of (\S+) .*?source-sha256=([0-9a-f]{16})")


def _git(*a, check=True) -> str:
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr.strip()}")
    return r.stdout


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── the request ─────────────────────────────────────────────────────────────
def read_request(path: str | None) -> dict:
    """JSON, or the watcher's "key: value" lines (claims/paths split on commas or spaces)."""
    if not path:
        return {}
    t = pathlib.Path(path).read_text(encoding="utf-8")
    try:
        d = json.loads(t)
    except ValueError:
        d = {}
        for line in t.splitlines():
            m = re.match(r"\s*([A-Za-z_]+)\s*[:=]\s*(.*)$", line)
            if m:
                d[m.group(1)] = m.group(2).strip()
    for k in ("claims", "paths"):
        v = d.get(k)
        if isinstance(v, str):
            d[k] = [x for x in re.split(r"[,\s]+", v) if x]
        elif v is None:
            d[k] = []
    d["chat"] = (d.get("chat") or "").strip() or None
    return d


# ── the tree ────────────────────────────────────────────────────────────────
def changed_paths() -> list[tuple[str, str]]:
    """(status, path) for every change git sees: modified, deleted, added, untracked (not ignored)."""
    out = _git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    items, parts, i = [], out.split("\0"), 0
    while i < len(parts):
        e = parts[i]
        if not e:
            i += 1
            continue
        st, p = e[:2], e[3:]
        if st[0] in "RC":                  # rename: the next field is the old name
            i += 1
        items.append((st, p))
        i += 1
    return items


def _content_hash(odt: pathlib.Path) -> str:
    with zipfile.ZipFile(odt) as zf:
        return hashlib.sha256(zf.read("content.xml")).hexdigest()[:16]


def _head_stamp(mirror_rel: str) -> tuple[str | None, str | None]:
    """(source path, source hash) from the committed mirror's banner, or (None, None)."""
    try:
        head = _git("show", f"HEAD:{mirror_rel}")[:600]
    except RuntimeError:
        return None, None
    m = _STAMP_RE.search(head)
    return (m.group(1), m.group(2)) if m else (None, None)


def _mirror_jobs():
    import refresh_mirrors as rm
    return rm


def family_documents(fam: str):
    """[(sources_in_tree_for_this_mirror, resolved_source, mirror)] for a family, via refresh_mirrors'
    own SOURCES list, so a versioned family lists every version file in its folder."""
    import doc_tier
    rm = _mirror_jobs()
    out = []
    for pattern, mirror_dir, versioned in rm.SOURCES:
        matches = sorted(REPO.glob(pattern))
        matches = [m for m in matches if doc_tier.family(m) == fam]
        if not matches:
            continue
        if versioned:
            latest = max(matches, key=rm._version_key)
            out.append((matches, latest, REPO / mirror_dir / f"{rm._stem_without_version(latest)}.md"))
        else:
            for m in matches:
                out.append(([m], m, REPO / mirror_dir / f"{m.stem}.md"))
    return out


# ── the plan ────────────────────────────────────────────────────────────────
def plan(req: dict) -> dict:
    import doc_lock
    chat = req.get("chat")
    want = list(req.get("claims") or [])
    paths = set(req.get("paths") or [])
    held = doc_lock.claims()
    others = {k: v["chat"] for k, v in held.items() if v.get("chat") and v["chat"] != chat}
    P = {"chat": chat, "claims": want, "paths": sorted(paths), "others": others,
         "hold": [], "park_docs": [], "stop": [], "mode": "scoped", "notes": []}

    if not chat and not want and not paths:
        if others:
            P["stop"].append("this ship names no chat and no claims, and claims are in use: "
                             + ", ".join(f"{k} ({v})" for k, v in sorted(others.items()))
                             + ". A ship request needs chat, claims and paths now; Martin can still "
                               "ship everything by hand with nrg_git.sh --ship-all.")
        else:
            P["mode"] = "all"
            P["notes"].append("no claims are held anywhere: the ship takes the whole tree, as before")
        return P
    for c in want:
        if c not in doc_lock.claim_names():
            P["stop"].append(f"no claim called {c!r}")
        elif c in others:
            P["stop"].append(f"the request lists {c}, which chat {others[c]!r} holds, not {chat!r}")
    if not chat:
        P["stop"].append("the request names claims or paths but no chat")
    if P["stop"]:
        return P

    for st, p in changed_paths():
        cl = doc_lock.claim_for_path(p)
        if cl in others and p not in paths:
            P["hold"].append({"path": p, "status": st, "claim": cl, "holder": others[cl]})

    # documents of families another chat holds
    for cl in sorted(c for c in others if c.startswith("doc:")):
        for fam in doc_lock.families_of(cl):
            for sources, resolved, mirror in family_documents(fam):
                mrel = mirror.relative_to(REPO).as_posix()
                hsrc, hhash = _head_stamp(mrel)
                if hsrc is None:
                    if hhash is None and mirror.exists():
                        P["notes"].append(f"{mrel}: committed mirror carries no source stamp; not compared")
                    else:
                        P["stop"].append(f"{fam}: no committed mirror to compare with; chat {others[cl]!r} "
                                         f"holds {cl} and its documents have never shipped")
                    continue
                shipped = REPO / hsrc
                if resolved.resolve() != shipped.resolve():
                    if not shipped.exists():
                        P["stop"].append(f"{fam}: the shipped source {hsrc} is not in the tree, so the "
                                         f"family cannot be put back to its shipped state; chat "
                                         f"{others[cl]!r} holds {cl}")
                        continue
                    import refresh_mirrors as rm
                    kv = rm._version_key(shipped)
                    newer = [s for s in sources if rm._version_key(s) > kv]
                    for s in newer:
                        P["park_docs"].append({"path": s.relative_to(REPO).as_posix(), "claim": cl,
                                               "holder": others[cl]})
                    if _content_hash(shipped) != hhash:
                        P["stop"].append(f"{hsrc} itself has changed since it shipped, and chat "
                                         f"{others[cl]!r} holds {cl}")
                elif _content_hash(resolved) != hhash:
                    P["stop"].append(f"{hsrc} has unshipped edits and chat {others[cl]!r} holds {cl}. "
                                     f"Ship after that chat does, or ship together (one request "
                                     f"naming both claims, from the chat that holds both)")
    return P


def print_plan(P: dict) -> None:
    print(f"  ship scope: chat {P['chat']!r}, claims {', '.join(P['claims']) or 'none'}, "
          f"{len(P['paths'])} named path(s); mode {P['mode']}")
    for k, v in sorted(P["others"].items()):
        print(f"    held by another chat: {k:<18} {v!r}")
    if P["hold"]:
        print(f"  held back ({len(P['hold'])} file(s) - another chat's work, not in this commit):")
        for h in P["hold"][:40]:
            print(f"    {h['status']} {h['path']}   [{h['claim']}, chat {h['holder']!r}]")
        if len(P["hold"]) > 40:
            print(f"    ... and {len(P['hold']) - 40} more")
    for d in P["park_docs"]:
        print(f"  parked for the ship: {d['path']}   [{d['claim']}, chat {d['holder']!r}]")
    for n in P["notes"]:
        print(f"  note: {n}")
    for s in P["stop"]:
        print(f"  STOP: {s}")


# ── park and restore ────────────────────────────────────────────────────────
def _blob(rel: str) -> str | None:
    p = REPO / rel
    if not p.exists():
        return None
    return _git("hash-object", "--", rel).strip()


def _head_blob(rel: str) -> str | None:
    out = _git("ls-tree", "HEAD", "--", rel)
    return out.split()[2] if out.strip() else None


def _remove(p: pathlib.Path) -> None:
    try:
        p.unlink()
    except OSError:                       # the bridge mount refuses unlink
        d = REPO / "_to_delete" / "ship_hold"
        d.mkdir(parents=True, exist_ok=True)
        os.rename(p, d / f"{p.name}.{os.getpid()}.{int(datetime.datetime.now().timestamp())}")


def park(P: dict, sid: str) -> int:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", sid):
        print(f"  bad id {sid!r}")
        return 2
    root = HOLD / sid
    if root.exists():
        print(f"  {root.relative_to(REPO)} already exists - a ship id runs once")
        return 1
    files = root / "files"
    files.mkdir(parents=True)
    man = {"id": sid, "parked_at": _now(), "chat": P["chat"], "head": _git("rev-parse", "HEAD").strip(),
           "entries": [], "restored": False}
    mf = root / "manifest.json"

    def save():
        mf.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    save()
    for h in P["hold"]:
        rel = h["path"]
        src = REPO / rel
        hb = _head_blob(rel)
        e = {"path": rel, "claim": h["claim"], "holder": h["holder"], "head_blob": hb}
        if src.exists():
            dst = files / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            e["kind"] = "modified" if hb else "added"
        else:
            e["kind"] = "deleted"
        man["entries"].append(e)
        save()
        if hb:
            _git("checkout", "HEAD", "--", rel)        # back to its committed state for the ship
        else:
            _remove(src)
    for d in P["park_docs"]:
        rel = d["path"]
        dst = files / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.rename(REPO / rel, dst)
        man["entries"].append({"path": rel, "claim": d["claim"], "holder": d["holder"], "kind": "doc"})
        save()
    print(f"  parked {len(man['entries'])} item(s) in {root.relative_to(REPO)}")
    return 0


def restore(sid: str) -> int:
    root = HOLD / sid
    mf = root / "manifest.json"
    if not mf.exists():
        print(f"  nothing parked under {sid}")
        return 0
    man = json.loads(mf.read_text(encoding="utf-8"))
    if man.get("restored"):
        print(f"  {sid}: already restored")
        return 0
    files = root / "files"
    left = []
    for e in man["entries"]:
        rel, kind = e["path"], e["kind"]
        tree = REPO / rel
        held = files / rel
        if kind == "doc":
            if tree.exists():
                left.append((rel, "a file of that name appeared during the ship"))
                continue
            tree.parent.mkdir(parents=True, exist_ok=True)
            os.rename(held, tree)
            e["restored"] = True
            continue
        now = _blob(rel)
        if now != e.get("head_blob"):
            left.append((rel, "the ship changed it (a rebuilt mirror or PDF, or the pull)"))
            continue
        if kind == "deleted":
            _remove(tree)
        else:
            tree.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(held, tree)
        e["restored"] = True
    man["restored"] = not left
    man["restored_at"] = _now()
    man["left"] = [{"path": r, "why": w} for r, w in left]
    mf.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    n = sum(1 for e in man["entries"] if e.get("restored"))
    print(f"  restored {n} of {len(man['entries'])} held-back item(s) from {root.relative_to(REPO)}")
    for r, w in left:
        print(f"    NOT put back: {r} - {w}; the held copy is {(files / r).relative_to(REPO)}")
    return 0 if not left else 3


def check(chat: str | None, rng: str | None = None) -> int:
    """For a ship from a clone of its own: no changed file - in the tree, or in the commits of
    rng (e.g. origin/main..HEAD) - may be under a claim another chat holds."""
    import doc_lock
    me = doc_lock.chat_id(chat)
    bad = []
    paths = [p for _, p in changed_paths()]
    if rng:
        paths += [p for p in _git("diff", "--name-only", rng).splitlines() if p]
    for p in sorted(set(paths)):
        ok, why = doc_lock.check_write(p, me)
        if not ok:
            bad.append(why)
    for b in bad[:20]:
        print(f"  REFUSED: {b}")
    return 1 if bad else 0


# ── self-test: two chats in a throwaway repository ──────────────────────────
def _selftest() -> int:
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as d:
        dd = pathlib.Path(d)
        subprocess.run(["git", "init", "-q", str(dd)], check=True)
        for rel, txt in {"src/a.py": "a=1\n", "tools/t.py": "t=1\n", "tools/reg.csv": "k\n",
                         "notes/n.txt": "n\n"}.items():
            (dd / rel).parent.mkdir(parents=True, exist_ok=True)
            (dd / rel).write_text(txt)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@t")
        subprocess.run(["git", "-C", str(dd), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(dd), "commit", "-qm", "base"], check=True, env=env)
        global REPO, HOLD
        R0, H0 = REPO, HOLD
        REPO, HOLD = dd, dd / ".ship_hold"
        (dd / ".gitignore").write_text(".ship_hold/\n")
        try:
            import doc_lock
            saved = (doc_lock.claims, doc_lock.claim_for_path, doc_lock.claim_names)
            doc_lock.claims = lambda: {"pipeline": {"chat": "B"}}
            doc_lock.claim_names = lambda: ["pipeline", "tools", "doc:report"]
            doc_lock.claim_for_path = lambda p: ("pipeline" if p.startswith("src/") else
                                                 "tools" if p.endswith(".py") and p.startswith("tools/") else None)
            (dd / "src/a.py").write_text("a=2\n")          # chat B, pipeline
            (dd / "src/new.py").write_text("n\n")          # chat B, new file
            (dd / "tools/t.py").write_text("t=2\n")        # chat A, tools
            (dd / "tools/reg.csv").write_text("k\nx\n")    # shared
            P = plan({"chat": "A", "claims": ["tools"], "paths": []})
            held = sorted(h["path"] for h in P["hold"])
            if held != ["src/a.py", "src/new.py"] or P["stop"]:
                print("FAIL plan", held, P["stop"]); ok = False
            if park(P, "t1") != 0:
                print("FAIL park"); ok = False
            if (dd / "src/a.py").read_text() != "a=1\n" or (dd / "src/new.py").exists():
                print("FAIL parked tree"); ok = False
            st = sorted(p for _, p in changed_paths())
            if st != [".gitignore", "tools/reg.csv", "tools/t.py"]:
                print("FAIL tree during ship", st); ok = False
            subprocess.run(["git", "-C", str(dd), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(dd), "commit", "-qm", "ship A"], check=True, env=env)
            if restore("t1") != 0:
                print("FAIL restore"); ok = False
            if (dd / "src/a.py").read_text() != "a=2\n" or (dd / "src/new.py").read_text() != "n\n":
                print("FAIL restored tree"); ok = False
            P2 = plan({})
            if not P2["stop"]:
                print("FAIL: a claimless ship was not stopped while B holds pipeline"); ok = False
            P3 = plan({"chat": "A", "claims": ["pipeline"]})
            if not P3["stop"]:
                print("FAIL: A listed B's claim and was not stopped"); ok = False
            doc_lock.claims, doc_lock.claim_for_path, doc_lock.claim_names = saved
        finally:
            REPO, HOLD = R0, H0
    print("ship_scope selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("action", nargs="?", choices=["plan", "park", "restore", "check"])
    ap.add_argument("--request", default=os.environ.get("NRG_SHIP_REQUEST"))
    ap.add_argument("--id", default=None)
    ap.add_argument("--chat", default=None)
    ap.add_argument("--range", default=None, help="check: also the files changed by these commits")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.action == "check":
        return check(a.chat, a.range)
    if a.action == "restore":
        if not a.id:
            ap.error("restore needs --id")
        return restore(a.id)
    if not a.action:
        ap.error("an action is needed")
    P = plan(read_request(a.request))
    if a.json:
        print(json.dumps(P, indent=1))
    else:
        print_plan(P)
    if P["stop"]:
        return 1
    if a.action == "park":
        if not a.id:
            ap.error("park needs --id")
        if P["mode"] == "all" or not (P["hold"] or P["park_docs"]):
            print("  nothing to hold back")
            return 0
        return park(P, a.id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
