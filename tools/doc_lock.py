#!/usr/bin/env python3
"""doc_lock — one machine at a time may edit the ODTs.

WHY THIS EXISTS

  The project is machine-independent in two of its three stores. Both git
  repositories merge; two machines can work on code, tools, the decision log and
  the changelogs at the same time and git will tell you if they collide.

  The ODTs cannot. `rclone copy` is one-way, on demand, with no merge and no
  conflict detection, and an ODT is a zip - there is nothing to merge even in
  principle. Two machines editing report9.odt means whoever archives last wins
  and the other's work is gone, silently.

  There is a subtler version that would bite even someone careful about Drive.
  THE MIRRORS ARE COMMITTED; THE ODTs ARE NOT. So if machine A edits an ODT,
  regenerates the mirror and pushes, and machine B still holds the older ODT,
  B's next refresh_mirrors run regenerates the mirror FROM ITS STALE ODT and
  pushes what looks like an ordinary commit but is a reversion of A's prose.
  check_all's mirror gate compares modification times only - it never reads
  content - so B's stale mirror reads as current and every gate stays green.

  This turns that silent loss into a refusal.

WHAT IT IS NOT

  Not a concurrency primitive. The lock lives in the private git repository, so
  it is only as current as the last fetch, and two machines that both take it
  while offline will both believe they hold it. It is a handover protocol
  between one person's machines, not a mutex. It stops the accident, not an
  adversary.

CLAIMS (1.2.0, spec NRG_spec_parallel_chats_2026-10-10)

  The lock above answers "which MACHINE's documents are current on Drive". Several chats now work
  in one tree at once - one on the report, one on Paper M, one on the scripts - and that needs a
  second question answered: "which CHAT is working on this?". A claim answers it. It lives in the
  same file, under "claims", and is held by a chat, not a machine:

    doc:<family>   a document family's ODTs, mirrors and PDFs (families from tools/doc_tier.csv;
                   doc:Paper2, doc:MS, doc:SM, doc:summaries, doc:academic and doc:web_manuals
                   name families with long names, or several together)
    pipeline       src/, outputs/ (not outputs/chat/), data/, run_analysis.py, requirements.txt
    tools          tools/*.py and tools/*.sh (not the CSV registers in tools/, which every chat
                   writes and tools/register_io.py merges)

    python3 tools/doc_lock.py take doc:PaperM --chat "Paper M v1_9" --note "read-through"
    python3 tools/doc_lock.py release doc:PaperM --chat "Paper M v1_9"
    python3 tools/doc_lock.py status                      # machine lock and every claim
    python3 tools/doc_lock.py who <path>                  # the claim covering a path, and its holder

  The chat's name comes from --chat or the NRG_CHAT environment variable. A claim held by another
  chat refuses: odt_edit writes into its documents, run_analysis while `pipeline` is held, and a
  scoped ship staging its files (tools/ship_scope.py). An UNCLAIMED area refuses nothing: claims
  protect work that someone has said they are doing, and Martin's own edits by hand stay as they
  were.
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-10-10. Claims, held by a chat (spec
#   NRG_spec_parallel_chats_2026-10-10): take/release NAME, who PATH, claims --json; every write to the
#   lock file goes through a lock file of its own (tools/register_io.excl_lock) and keeps the other half.
# 1.1.0  # Hollingham (2026) — 2026-10-02. Cloud ship (spec NRG_spec_cloud_ship_2026-10-02,
#   signed off): the holder name may be fixed with NRG_DOC_LOCK_HOLDER (a cloud session has a new hostname
#   every time, so it uses "cloud"); `release` refuses while documents have changed since the last Drive
#   archive (.last_drive_archive) unless --force, and takes --note.
# 1.0.0 — 2026-08-25. First issue.

import argparse, datetime, json, os, pathlib, re, socket, subprocess, sys

REPO = pathlib.Path(__file__).resolve().parents[1]
LOCK = REPO / "working/DOCUMENT_LOCK.json"
sys.path.insert(0, str(REPO / "tools"))


def _who() -> str:
    if os.environ.get("NRG_DOC_LOCK_HOLDER"):
        return os.environ["NRG_DOC_LOCK_HOLDER"]
    return f"{os.environ.get('USER') or os.environ.get('USERNAME') or '?'}@{socket.gethostname()}"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read() -> dict | None:
    if not LOCK.exists():
        return None
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"holder": "UNREADABLE", "since": "?", "note": "lock file is corrupt"}


def status(quiet: bool = False) -> int:
    """0 = free or held by me, 1 = held by someone else."""
    st = read()
    me = _who()
    # A RELEASED lock is a file with holder null, not an absent file: the bridge
    # mount refuses unlink, so release() empties rather than deletes. Both read
    # as unlocked, and forgetting that made the first version report a released
    # lock as held by someone else.
    if st is None or not st.get("holder"):
        if not quiet:
            print("  documents UNLOCKED — take it before editing any ODT")
        return 0
    mine = st.get("holder") == me
    if not quiet:
        word = "you hold it" if mine else "HELD BY ANOTHER MACHINE"
        print(f"  documents locked: {word}")
        print(f"    holder {st.get('holder')}   since {st.get('since')}")
        if st.get("note"):
            print(f"    note   {st['note']}")
    return 0 if mine else 1


def acquire(note: str, force: bool) -> int:
    st = read()
    me = _who()
    # `st.get("holder")` FIRST. A released lock is a file with holder null — this
    # module says so at status() and the bridge mount's refusal to unlink is why.
    # Without that clause `None != me` is true, so every correctly released lock
    # refused the next taker and the only way past it was --force. Which is what
    # was done on 2026-08-27, on a lock nobody held.
    if st and st.get("holder") and st.get("holder") != me and not force:
        print(f"  REFUSED — {st.get('holder')} has held the documents since {st.get('since')}.")
        print("  Ask that machine to release, or --force if you know it is idle.")
        print("  Forcing while the other machine has unarchived edits loses them.")
        return 1
    _update(lambda d: d.update({"holder": me, "since": _now(), "note": note}))
    print(f"  documents locked to {me}")
    print("  commit and push the private repo so the other machine can see it.")
    return 0


MARKER = REPO / ".last_drive_archive"
_SKIP = ("_to_delete/", "_transfer/", "/_frozen/", "/_superseded/", "/backups/", "venv/", ".git")


def unarchived() -> list[str] | None:
    """Documents changed since the last Drive archive (nrg_git.sh documents_since_archive, in Python).
    None when there has never been an archive here."""
    if not MARKER.exists():
        return None
    t = MARKER.stat().st_mtime
    out = []
    for pat in ("*.odt", "*.odm"):
        for f in REPO.rglob(pat):
            r = f.relative_to(REPO).as_posix()
            if any(k.strip("/") in r.split("/") or r.startswith(k) for k in _SKIP):
                continue
            if f.stat().st_mtime > t:
                out.append(r)
    return sorted(out)


def release(note: str = "", force: bool = False) -> int:
    st = read()
    if st is None:
        print("  already unlocked")
        return 0
    me = _who()
    # 1.1.0: releasing is the handover that says "Drive is current"; a cloud ship trusts it.
    # Releasing with unarchived edits would hand over a Drive that is behind this machine.
    pend = unarchived()
    if pend and not force:
        print(f"  REFUSED — {len(pend)} document(s) changed since the last Drive archive:")
        for r in pend[:10]:
            print(f"    {r}")
        print("  Archive first (nrg_git.sh option 11, or ship), then release. --force releases anyway.")
        return 1
    if st.get("holder") != me:
        print(f"  note: the lock is held by {st.get('holder')}, not by you — releasing anyway")
    # The bridge mount refuses unlink, so emptying beats deleting: a zero-holder
    # file reads as unlocked and never leaves a half-removed lock behind.
    _update(lambda d: d.update({"holder": None, "since": _now(),
                                "note": f"released by {me}" + (f": {note}" if note else "")}))
    print("  documents released — commit and push the private repo")
    return 0


# ── the lock file, written whole under its own lock ──────────────────────────
def _update(fn) -> dict:
    """Read the lock file, apply fn(dict) in place, write it back, all under a lock file, so a
    claim taken by one chat and the machine lock taken by another never overwrite each other."""
    import register_io
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with register_io.excl_lock(LOCK):
        d = read() or {"holder": None, "since": _now(), "note": ""}
        if d.get("holder") == "UNREADABLE":
            raise SystemExit("  working/DOCUMENT_LOCK.json is corrupt; repair it by hand before taking anything")
        fn(d)
        LOCK.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return d


# ── claims (1.2.0) ───────────────────────────────────────────────────────────
# Families whose doc_tier name is long, or that are edited together, have a short claim name.
ALIASES = {
    "doc:Paper2": ("Hollingham_2026_Paper2_amended",),
    "doc:MS": ("Newborough_Methods_Supplement",),
    "doc:SM": ("Supplementary_Material",),
    "doc:summaries": ("public_summary_EN", "public_summary_CY", "public_summary_PL"),
    "doc:academic": ("academic_Summary", "crynodeb_academaidd"),
    "doc:web_manuals": ("NRG_Web_Tools_User_Manual", "NRG_Web_Tools_Technical_Note"),
}
AREAS = ("pipeline", "tools")
PIPELINE_PREFIXES = ("src/", "outputs/", "data/")
PIPELINE_FILES = ("run_analysis.py", "requirements.txt")
PIPELINE_EXCEPT = ("outputs/chat/",)          # rebuilt by every ship (build_chat_corpus): derived


def _families() -> list[str]:
    import doc_tier
    return sorted(doc_tier.read_register()[1])


def claim_for_family(fam: str) -> str:
    for name, fams in ALIASES.items():
        if fam in fams:
            return name
    return f"doc:{fam}"


def claim_names() -> list[str]:
    return sorted({claim_for_family(f) for f in _families()}) + list(AREAS)


def families_of(claim: str) -> tuple[str, ...]:
    if claim in ALIASES:
        return ALIASES[claim]
    if claim.startswith("doc:"):
        return (claim[4:],)
    return ()


_PDF_SRC: dict[str, str] | None = None


def _pdf_sources() -> dict[str, str]:
    """published PDF path -> its source ODT's file name, from docs/PDF_MANIFEST.txt."""
    global _PDF_SRC
    if _PDF_SRC is None:
        _PDF_SRC = {}
        man = REPO / "docs/PDF_MANIFEST.txt"
        if man.exists():
            for line in man.read_text(encoding="utf-8").splitlines():
                m = re.match(r"\s*(\S+\.pdf)\s+<-\s+(\S+)", line)
                if m:
                    _PDF_SRC[m.group(1)] = m.group(2)
    return _PDF_SRC


def family_of_path(rel: str) -> str | None:
    """The document family a path belongs to: its ODT, its mirror or its published PDF."""
    import doc_tier
    rel = rel.replace("\\", "/")
    if rel.startswith("report_edits/") or rel == "docs/report/report.pdf":
        name = rel.rsplit("/", 1)[-1]
        if re.fullmatch(r"report\d*\.(odt|odm|md)", name) or rel == "docs/report/report.pdf":
            return "report"
        return None
    f = doc_tier.family(rel)
    if f:
        return f
    m = re.search(r"/text/([^/]+)\.md$", rel)
    if m and rel.startswith("docs/"):
        f = doc_tier.family(m.group(1) + ".odt")
        return f if f in _families() else None
    if rel.endswith(".pdf") and rel in _pdf_sources():
        return doc_tier.family(_pdf_sources()[rel])
    return None


def claim_for_path(rel: str) -> str | None:
    """The claim that covers a repository-relative path, or None (a shared or unclaimed file)."""
    rel = rel.replace("\\", "/")
    rel = rel[2:] if rel.startswith("./") else rel
    fam = family_of_path(rel)
    if fam:
        return claim_for_family(fam)
    if any(rel.startswith(x) for x in PIPELINE_EXCEPT):
        return None
    if rel in PIPELINE_FILES or any(rel.startswith(x) for x in PIPELINE_PREFIXES):
        return "pipeline"
    if rel.startswith("tools/") and rel.endswith((".py", ".sh")):
        return "tools"
    return None


def claims() -> dict[str, dict]:
    st = read() or {}
    return {k: v for k, v in (st.get("claims") or {}).items() if v and v.get("chat")}


def chat_id(explicit: str | None = None) -> str | None:
    c = (explicit or os.environ.get("NRG_CHAT") or "").strip()
    return c or None


def holder_of(claim: str | None) -> str | None:
    if not claim:
        return None
    c = claims().get(claim)
    return c.get("chat") if c else None


def check_write(rel: str, chat: str | None = None) -> tuple[bool, str]:
    """May this chat write this path? Refused only when ANOTHER chat holds the claim covering it."""
    cl = claim_for_path(rel)
    h = holder_of(cl)
    me = chat_id(chat)
    if h is None or h == me:
        return True, ""
    since = claims()[cl].get("since", "?")
    return False, (f"{rel} is in {cl}, which chat {h!r} has held since {since}"
                   f" ({claims()[cl].get('note') or 'no note'}). "
                   + ("Set NRG_CHAT to this chat's name if it is this chat's claim. " if not me else "")
                   + "Ask that chat to release it, or ask Martin.")


def take_claim(name: str, chat: str | None, note: str, force: bool) -> int:
    me = chat_id(chat)
    if not me:
        print("  REFUSED - a claim is held by a chat: give --chat NAME or set NRG_CHAT")
        return 1
    if name not in claim_names():
        print(f"  REFUSED - no claim called {name!r}. Claims: {', '.join(claim_names())}")
        return 1
    out = {}

    def fn(d):
        c = (d.get("claims") or {}).get(name)
        if c and c.get("chat") and c["chat"] != me and not force:
            out["refused"] = c
            return
        d.setdefault("claims", {})[name] = {"chat": me, "host": _who(), "since": _now(), "note": note}
    _update(fn)
    if "refused" in out:
        c = out["refused"]
        print(f"  REFUSED - {name} is held by chat {c['chat']!r} since {c.get('since')} ({c.get('note') or 'no note'}).")
        print("  Ask that chat to release it. --force takes it anyway (Martin's call: that chat's unshipped work is then unprotected).")
        return 1
    print(f"  {name} claimed by chat {me!r}")
    return 0


def release_claim(name: str, chat: str | None, force: bool) -> int:
    me = chat_id(chat)
    out = {}

    def fn(d):
        c = (d.get("claims") or {}).get(name)
        if not c or not c.get("chat"):
            out["free"] = True
            return
        if c["chat"] != me and not force:
            out["other"] = c["chat"]
            return
        d["claims"].pop(name, None)
    _update(fn)
    if out.get("free"):
        print(f"  {name} was not claimed")
        return 0
    if "other" in out:
        print(f"  REFUSED - {name} is held by chat {out['other']!r}, not {me!r}. --force releases it anyway.")
        return 1
    print(f"  {name} released")
    return 0


def print_claims() -> None:
    cs = claims()
    if not cs:
        print("  claims: none held")
        return
    print("  claims:")
    for k in sorted(cs):
        c = cs[k]
        print(f"    {k:<18} chat {c['chat']!r:<28} since {c.get('since','?')}  {c.get('note') or ''}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["status", "take", "release", "check", "who", "claims"])
    ap.add_argument("name", nargs="?", default=None,
                    help="take/release: a claim name (doc:PaperM, pipeline, tools...); omitted = the machine lock. "
                         "who: a path")
    ap.add_argument("--chat", default=None, help="this chat's name (default: $NRG_CHAT)")
    ap.add_argument("--note", default="", help="what you are editing")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.action == "claims":
        if a.json:
            print(json.dumps({"names": claim_names(), "held": claims()}, indent=1))
        else:
            print_claims()
        return 0
    if a.action == "who":
        if not a.name:
            ap.error("who needs a path")
        cl = claim_for_path(a.name)
        h = holder_of(cl)
        print(f"{a.name}: {cl or 'no claim covers it (shared)'}" + (f", held by chat {h!r}" if h else (", unclaimed" if cl else "")))
        return 0
    if a.action == "check":
        return status(quiet=a.quiet)
    if a.action == "status":
        status()
        print_claims()
        return 0
    if a.action == "take":
        return take_claim(a.name, a.chat, a.note, a.force) if a.name else acquire(a.note, a.force)
    return release_claim(a.name, a.chat, a.force) if a.name else release(a.note, a.force)


if __name__ == "__main__":
    sys.exit(main())
