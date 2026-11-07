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

THE PRIVATE STORE MUST BE PRESENT FOR ANY OF THIS TO MEAN ANYTHING (1.4.0, spec
NRG_handover_control_board_2026-11-04)

  The lock file lives in working/, which belongs to the PRIVATE repository. A clone that has only
  the public one has no lock file - and until 1.4.0 that read as every claim FREE, which is the
  most dangerous answer available. On 2026-11-04 the water-balance chat cloned the public
  repository alone, ran work_board, and was told every claim was free while another chat was
  actively working on Paper M. "Free" meant "no lock file here".

  So absence is now distinguished from freedom, in three states, not two (store_state()):

    PRESENT          .git-working resolves AND working/DOCUMENT_LOCK.json is tracked in it
    ABSENT           no private store: every claim reads UNKNOWN and `take` refuses
    PRESENT_NO_LOCK  the private store is there but has no lock file yet - genuinely free

  The third state is not pedantry. It is what a fresh clone of BOTH repositories looks like before
  anyone has ever locked, and a rule that keyed on the file's absence alone would make the
  first-ever `take` impossible.

  check_write() is where this bites hardest, because it is what odt_edit, run_analysis and
  ship_scope consult, and "no claim covers it" has always meant PERMITTED. With the store absent
  it refuses doc:* paths (the ODTs are not in a public-only clone anyway) and warns on pipeline
  and tools, so a deliberately public-only session can still run. NRG_NO_PRIVATE_STORE=1 says the
  session means it; the board then says so in its first line.

STALENESS IS MEASURED FROM ACTIVITY, NOT FROM WHEN THE CLAIM WAS TAKEN (1.4.0)

  A claim's `since` says when it was taken, which says nothing about whether the chat still exists.
  Every write that passes a claim gate refreshes `touched` on that claim (touch(), throttled to
  TOUCH_THROTTLE_S so a per-path loop does not rewrite the file hundreds of times), and age is
  measured from that. A chat that has been working all evening is never stale; one that took a
  claim and vanished is flagged after STALE_CLAIM_HOURS and loudly after ABANDONED_CLAIM_HOURS.
  Flagging is all it does: releasing another chat's claim stays a deliberate act, logged under R7.
"""
from __future__ import annotations

__version__ = "1.7.0"  # Hollingham (2026) — 2026-11-07 (T-175, Martin: "2b"). publish_records
#   refuses the push when commits between origin/main and HEAD touch anything beside the records,
#   printing LOCAL ONLY and naming them. D-314 exempts publishing "chat X holds Y" from "ask
#   before every push"; it never covered the rest of the branch, which `push HEAD:main` carried
#   anyway — measured 2026-11-07, when a take and a queue publish together sent six unapproved
#   private commits to GitHub. The record is still committed locally, so the claim holds here.
# "1.6.0"  # Hollingham (2026) — 2026-11-06 (D-314, Martin: "allow pushes for locks").
#   A CLAIM IS NOT A CLAIM UNTIL GITHUB HAS IT. take and release now commit and push the lock record
#   themselves, through _update(publish=...), and apply the change ON TOP OF ORIGIN'S record rather than
#   merging into it. Until now the whole durability mechanism was two print() calls asking a human to
#   commit and push - which a session that releases AFTER its ship has nothing left to carry. Three
#   failures in one evening, one in each direction. Never fatal: an unpublishable claim is still taken
#   and says LOCAL ONLY. Off under NRG_NO_LOCK_PUSH=1 and where there is no remote, so --selftest's
#   temp trees cannot reach the real repository. The `touched` refresh is NOT published, or every
#   claim-gate pass would push.
__version__ = "1.5.1"  # Hollingham (2026) — 2026-11-06 (T-155). _run() strips NRG_DOC_LOCK_HOLDER and
#   NRG_DOC_LOCK_FILE, so the selftest is not decided by a caller's override: cloud_ship.sh exports
#   NRG_DOC_LOCK_HOLDER="cloud" for the whole run and it reached this selftest through nrg_git.sh --ship
#   and check_all, failing 8a/8b and so every cloud ship since check_all 1.33.0 gated it (2026-11-04).
# "1.5.0"  # Hollingham (2026) — 2026-11-05 (D-301, spec NRG_handover_HQ_page_2026-11-05,
#   signed off). `take` tells a chat that is not in the chat register, and REFUSES it once REGISTRATION_REQUIRED is
#   flipped - which is the whole of phase 4 (T-138). `release` prints the queued jobs it made ready and the line that
#   fires each: a job fires when something is already running, and a release is one of the two such moments.
# 1.4.1  # Hollingham (2026) — 2026-11-05. --selftest 1g/1h/2d: the machine-lock
#   line reads UNKNOWN with no private store and "free" with a store and no holder (work_board 1.2.1).
# 1.4.0  # Hollingham (2026) - 2026-11-04 (D-300, spec NRG_handover_control_board_2026-11-04,
#   signed off). The control board. R1: store_state() tells an ABSENT private store from a free claim; every claim
#   reads UNKNOWN without it, `take` refuses with the attach lines, and check_write refuses doc:* while warning on
#   pipeline/tools (NRG_NO_PRIVATE_STORE=1 to mean it). R4: `touched` is refreshed by every write that passes a
#   claim gate and staleness is measured from it, not from `since` (STALE/ABANDONED_CLAIM_HOURS). R5: a claim
#   records the session `mode` (derived) and `link` (given, never required). R7: a forced take needs --by, a forced
#   release defaults it to NRG_CHAT, and both append to working/claim_overrides.csv. NRG_DOC_LOCK_FILE and
#   NRG_REPO_ROOT redirect the lock for testing and are announced wherever the board prints.
# 1.3.0  # Hollingham (2026) - 2026-11-03 (D-299). A bridge session takes the machine lock under the
#   L14's own name: off the bridge, every call records USER@host in .git/nrg_machine (untracked, inside the mount);
#   on the bridge (HOME under /sessions/) _who() reads it, and `take` refuses when it is absent rather than locking
#   under the VM's rcw-<session>@claude, which made the L14 refuse its own archives from 2026-10-26 to 2026-11-03.
#   status flags any rcw-*@claude holder as a bridge lock under the wrong name.
# 1.2.3  # Hollingham (2026) - 2026-10-17 (D-270). doc:Paper2 covers Paper 2 and Paper2_plain.
# 1.2.2  # Hollingham (2026) - 2026-10-15 (D-265). doc:Paper1 covers Paper1 and Paper1_plain.
# 1.2.1  # Hollingham (2026) - 2026-10-12 (D-258). doc:PaperM also covers PaperM_plain.
# 1.2.0  # Hollingham (2026) — 2026-10-10. Claims, held by a chat (spec
#   NRG_spec_parallel_chats_2026-10-10): take/release NAME, who PATH, claims --json; every write to the
#   lock file goes through a lock file of its own (tools/register_io.excl_lock) and keeps the other half.
# 1.1.0  # Hollingham (2026) — 2026-10-02. Cloud ship (spec NRG_spec_cloud_ship_2026-10-02,
#   signed off): the holder name may be fixed with NRG_DOC_LOCK_HOLDER (a cloud session has a new hostname
#   every time, so it uses "cloud"); `release` refuses while documents have changed since the last Drive
#   archive (.last_drive_archive) unless --force, and takes --note.
# 1.0.0 — 2026-08-25. First issue.

import argparse, datetime, json, os, pathlib, re, socket, subprocess, sys

# HERE is where this file actually lives; REPO is the tree whose lock we read. They differ only
# under NRG_REPO_ROOT, which the acceptance tests use - imports must keep following HERE, or a test
# pointing REPO at scratch/ would lose register_io and doc_tier.
HERE = pathlib.Path(__file__).resolve().parents[1]
REPO = pathlib.Path(os.environ.get("NRG_REPO_ROOT") or HERE).resolve()
LOCK = pathlib.Path(os.environ["NRG_DOC_LOCK_FILE"]).resolve() if os.environ.get("NRG_DOC_LOCK_FILE") \
    else REPO / "working/DOCUMENT_LOCK.json"
sys.path.insert(0, str(HERE / "tools"))


def override_warnings() -> list[str]:
    """7: whenever the lock has been redirected, say so wherever the board prints. A board read
    from a scratch lock that looked like the real one would be worse than no board."""
    w = []
    if os.environ.get("NRG_REPO_ROOT"):
        w.append(f"NRG_REPO_ROOT is set: this board is {REPO}, not the tree this script lives in")
    if os.environ.get("NRG_DOC_LOCK_FILE"):
        w.append(f"NRG_DOC_LOCK_FILE is set: the lock read here is {LOCK}, not working/DOCUMENT_LOCK.json")
    if os.environ.get("NRG_NO_PRIVATE_STORE"):
        w.append("NRG_NO_PRIVATE_STORE=1: this session has declared it is working without the private store, "
                 "so claim state is UNKNOWN and nothing here is a statement about what other chats hold")
    return w


# ── the private store, session identity, activity and overrides (1.4.0) ─────
STALE_CLAIM_HOURS = 24        # D-300. Flagged as STALE after this long with no activity. A chat working
ABANDONED_CLAIM_HOURS = 72    #   through the evening on one document is normal here, so 24 h is the floor,
                              #   not an hour or two. Both are overridable by NRG_CLAIM_STALE_HOURS /
                              #   NRG_CLAIM_ABANDONED_HOURS; neither ever releases anything by itself.
TOUCH_THROTTLE_S = 60         # ship_scope calls check_write once PER PATH. Without a throttle a scoped
                              #   ship would rewrite the lock file hundreds of times in a second.
WORKING_GIT = ".git-working"  # the private repository's git directory, over this same tree (CLAUDE.md 4f)
# D-301 phase 4. Registration in working/chat_register.csv is COMPULSORY from 2026-11-05, but the
# refusal waits: spec §11 conditions it on "registration having run for a few days", because a
# refusal that fires on every chat before the habit exists is a tool nobody uses. The mechanism is
# below and warns; flipping this to True is the whole of phase 4, and T-138 checks for the flip.
REGISTRATION_REQUIRED = False

OVERRIDES = "working/claim_overrides.csv"     # R7: append-only, merged row by row by register_io
PUBLISH_OWED = "working/.board_publish_owed"  # R6(a): a take/release leaves this; a session republishes

# The two attach lines from notes/reference/SESSION_MODES.md. Quoted, not paraphrased: a session that
# cannot see the private store needs the exact command, not a description of it.
ATTACH = ("add_repo newbroman/Newborough_Hydrology          access=push",
          "add_repo newbroman/Newborough_Hydrology_working  access=push")


def _hours(name: str, default: int) -> float:
    try:
        return float(os.environ.get(name) or default)
    except ValueError:
        return float(default)


def stale_hours() -> float:
    return _hours("NRG_CLAIM_STALE_HOURS", STALE_CLAIM_HOURS)


def abandoned_hours() -> float:
    return _hours("NRG_CLAIM_ABANDONED_HOURS", ABANDONED_CLAIM_HOURS)


def store_state() -> tuple[str, str]:
    """R1: PRESENT | ABSENT | PRESENT_NO_LOCK, and why, for the private store this tree's claims live in.

    ABSENT is NOT the same as "every claim is free" - that equation is the whole reason this exists.
    PRESENT_NO_LOCK is a real and benign state: both repositories are here and nobody has ever taken
    a claim, which must stay possible."""
    if os.environ.get("NRG_NO_PRIVATE_STORE"):
        return "ABSENT", "NRG_NO_PRIVATE_STORE=1 - this session has declared it works without the private store"
    gd = REPO / WORKING_GIT
    if not gd.exists():
        return "ABSENT", f"no {WORKING_GIT} in {REPO} - the private repository is not attached to this session"
    # Tracked in the private repository is the strongest available evidence that this IS the store.
    try:
        r = subprocess.run(["git", "-C", str(REPO), "--git-dir", str(gd), "--no-optional-locks",
                            "ls-files", "--error-unmatch", "working/DOCUMENT_LOCK.json"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return "PRESENT", "the private store is attached and the lock file is tracked in it"
    except (OSError, subprocess.SubprocessError):
        pass
    # The git directory is there but cannot vouch for the lock file: fall back to the file itself.
    if LOCK.exists():
        return "PRESENT", f"{WORKING_GIT} is present; the lock file is present but not tracked in it"
    return "PRESENT_NO_LOCK", (f"{WORKING_GIT} is present and has no lock file yet - "
                               "no claim has ever been taken in this tree")


def store_ok() -> bool:
    return store_state()[0] != "ABSENT"


def refuse_absent_store(what: str) -> None:
    st, why = store_state()
    print(f"  REFUSED - {what} needs the private repository, and it is not present.")
    print(f"  {why}.")
    print("  Claims live in working/DOCUMENT_LOCK.json, which is the PRIVATE repository's half of this tree.")
    print("  Attach both repositories with push access (notes/reference/SESSION_MODES.md):")
    for line in ATTACH:
        print(f"      {line}")
    print("  then run tools/cloud_setup.sh. Without them this session cannot see what other chats hold,")
    print("  and 'free' would mean 'no lock file here' (the 2026-11-04 incident, D-300).")


def session_mode() -> str:
    """R5: where the holder lives, derived - never asked for. Enough to find a chat without a URL."""
    if os.environ.get("NRG_SESSION_MODE"):
        return os.environ["NRG_SESSION_MODE"]
    if on_bridge():
        return "bridge"
    try:
        if MACHINE_FILE.exists() and MACHINE_FILE.read_text(encoding="utf-8").strip() == _native():
            return "laptop"
    except OSError:
        pass
    return "unknown"


def _parse(ts: str | None) -> datetime.datetime | None:
    try:
        return datetime.datetime.strptime(ts or "", "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)
    except (ValueError, TypeError):
        return None


def activity(c: dict) -> str | None:
    """When this claim was last used. `touched` if anything has passed its gate, else `since`."""
    return c.get("touched") or c.get("since")


def age_h(c: dict) -> float | None:
    t = _parse(activity(c))
    if t is None:
        return None
    return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 3600.0


def staleness(c: dict) -> str:
    """"" | STALE | ABANDONED, from ACTIVITY (R4), never from when the claim was taken."""
    a = age_h(c)
    if a is None:
        return ""
    if a >= abandoned_hours():
        return "ABANDONED"
    if a >= stale_hours():
        return "STALE"
    return ""


def stale_note(c: dict) -> str:
    f = staleness(c)
    if not f:
        return ""
    a = age_h(c) or 0
    word = "no activity" if c.get("touched") else "never used since it was taken"
    return f"{f} ({word} for {a:.0f} h)"


def touch(claim: str | None, chat: str | None = None) -> None:
    """R4: this chat just did something under `claim` - refresh its activity time.

    Called from check_write (odt_edit and ship_scope reach it that way) and intended for
    run_analysis's pipeline gate. Throttled, and it NEVER raises: a failure to record activity
    must not be the reason a write is refused."""
    if not claim:
        return
    try:
        me = chat_id(chat)
        if not me or not store_ok():
            return
        c = claims().get(claim)
        if not c or c.get("chat") != me:
            return
        last = _parse(activity(c))
        if last and (datetime.datetime.now(datetime.timezone.utc) - last).total_seconds() < TOUCH_THROTTLE_S:
            return

        def fn(d):
            cc = (d.get("claims") or {}).get(claim)
            if cc and cc.get("chat") == me:
                cc["touched"] = _now()
        _update(fn)
    except Exception:
        pass


def log_override(action: str, claim: str, from_chat: str | None, to_chat: str | None,
                 by: str, note: str = "") -> None:
    """R7: every override appends a row. Append-only - a dated record is never rewritten."""
    try:
        import register_io
        path = REPO / OVERRIDES
        fields = ["when", "action", "claim", "from_chat", "to_chat", "by", "note"]
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = register_io.read_rows(path) if path.exists() else []
        rows.append({"when": _now(), "action": action, "claim": claim, "from_chat": from_chat or "",
                     "to_chat": to_chat or "", "by": by, "note": note})
        register_io.write_rows(path, fields, rows)
        print(f"  logged: {action} {claim} by {by} -> {OVERRIDES}")
    except Exception as e:
        print(f"  WARNING - the override was NOT logged ({e}); record it in the handover note by hand")


def mark_publish_owed(why: str) -> None:
    """R6(a): the board artifact is now behind. doc_lock cannot publish - only a session can - so it
    leaves the marker and board_artifact.py --check tells the session to republish."""
    try:
        pth = REPO / PUBLISH_OWED
        pth.parent.mkdir(parents=True, exist_ok=True)
        pth.write_text(f"{_now()}  {why}\n", encoding="utf-8")
    except OSError:
        pass


# 1.3.0 (D-299): the machine whose tree this is, recorded where the bridge can read it. .git is inside
# the connected folder, so the bridge sees this file; it is untracked, so every clone has its own.
MACHINE_FILE = REPO / ".git" / "nrg_machine"
# The holder name a bridge VM produced before 1.3.0: USER rcw-<session id>, host "claude".
BRIDGE_HOLDER = re.compile(r"^rcw-[0-9a-z]+@claude$")


def on_bridge() -> bool:
    """The Cowork bridge VM: its home is under /sessions/ (the test tools/bridge_py.sh uses)."""
    return (os.environ.get("HOME") or "").startswith("/sessions/")


def _native() -> str:
    return f"{os.environ.get('USER') or os.environ.get('USERNAME') or '?'}@{socket.gethostname()}"


def _who() -> str:
    """The lock holder for this process. "" on the bridge when the machine's name is not recorded."""
    if os.environ.get("NRG_DOC_LOCK_HOLDER"):
        return os.environ["NRG_DOC_LOCK_HOLDER"]
    if on_bridge():
        # The bridge edits the L14's own files, so for the documents it IS the L14 (D-299).
        try:
            return MACHINE_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            return ""
    me = _native()
    try:
        if MACHINE_FILE.parent.is_dir() and (not MACHINE_FILE.exists()
                                             or MACHINE_FILE.read_text(encoding="utf-8").strip() != me):
            MACHINE_FILE.write_text(me + "\n", encoding="utf-8")
    except OSError:
        pass
    return me


def _wrong_name_note(holder: str | None) -> None:
    if holder and BRIDGE_HOLDER.match(holder):
        print("    >>> a BRIDGE lock under the wrong name (the bridge VM's user, not the L14's): the documents")
        print("    >>> are the L14's. On the L14: archive (nrg_git.sh 11), then take --force and release (D-299).")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read() -> dict | None:
    if not LOCK.exists():
        return None
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"holder": "UNREADABLE", "since": "?", "note": "lock file is corrupt"}


def print_store_line() -> str:
    """1.4.0: the first line of any board. What the rest of it is worth depends on this."""
    state, why = store_state()
    if state == "ABSENT":
        print(f"  private store: ABSENT - {why}")
        print("    >>> every claim below reads UNKNOWN, NOT free. This session cannot see what other")
        print("    >>> chats hold. Attach both repositories (SESSION_MODES.md) before taking anything.")
    elif state == "PRESENT_NO_LOCK":
        print(f"  private store: present, no lock file yet - {why}")
    for w in override_warnings():
        print(f"    >>> {w}")
    return state


def status(quiet: bool = False) -> int:
    """0 = free or held by me, 1 = held by someone else or the store is absent."""
    if not quiet:
        if print_store_line() == "ABSENT":
            print("  documents UNKNOWN - the lock cannot be read from this session")
            return 1
    elif not store_ok():
        return 1
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
        _wrong_name_note(st.get("holder"))
    return 0 if mine else 1


def acquire(note: str, force: bool) -> int:
    if not store_ok():
        refuse_absent_store("taking the machine lock")
        return 1
    st = read()
    me = _who()
    if not me:
        print("  REFUSED — this is the bridge, and the L14's own name is not recorded in .git/nrg_machine,")
        print("  so a lock taken here would carry the VM's name and block the L14's archives (D-299).")
        print("  On the L14 run once:  python3 tools/doc_lock.py status   (any nrg_git.sh option also records it)")
        return 1
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
    _update(lambda d: d.update({"holder": me, "since": _now(), "note": note}),
            publish=f"documents locked to {me}")
    print(f"  documents locked to {me}")
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
    me = _who() or "the bridge (L14 name not recorded)"
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
                                "note": f"released by {me}" + (f": {note}" if note else "")}),
            publish=f"documents released by {me}")
    print("  documents released")
    mark_publish_owed("machine lock released")
    return 0


# ── D-314: a claim is not a claim until GitHub has it ────────────────────────
# Martin, 2026-11-06, after three failures in one evening, one in each direction: a take that
# never reached the lock file, his `tools` release that reached only his tree (803cdce), and this
# chat's release that reached only its container. Each looked like a lock failure and was not: the
# lock reported what GitHub held, correctly. Until now the ENTIRE durability mechanism was two
# print() calls - "commit and push the private repo so the other machine can see it" - i.e. a
# human instruction, which a session that releases AFTER its ship has nothing left to carry.
#
# His ruling: a LOCK PUSH IS NOT A CONTENT PUSH. It publishes no code, no prose and no numbers,
# only "chat X holds Y", so it is exempt from "ask before every push" (CLAUDE.md section 7), which
# exists to control what reaches the published corpus.
#
# Two halves, and the second matters as much as the first:
#   1. the record is pushed the moment it changes, so a claim exists as soon as it is taken;
#   2. the change is applied ON TOP OF ORIGIN'S record, never merged into it - restore from
#      origin first, then let the tool rewrite its row. That is the rule the same evening
#      produced twice over: these files are owned by their tools at both ends, and a git-side
#      merge of them is how a claim gets silently dropped or reinstated.
# Half 2 is safe only BECAUSE of half 1: it would discard an unpushed local claim, and after this
# change there are none. During the transition there may be, which is why it says what it did.
#
# It never fails the operation. A claim that cannot be published is still taken locally and says
# so loudly - the one thing it must not do is report success for a claim nobody else can see.
RECORD_PATHS = ("working/DOCUMENT_LOCK.json", "working/claim_overrides.csv")
_WGIT = ("git", "--no-optional-locks")


def _wgit(*args: str, timeout: int = 60):
    import subprocess
    return subprocess.run([*_WGIT, f"--git-dir={REPO / WORKING_GIT}", f"--work-tree={REPO}", *args],
                          cwd=str(REPO), capture_output=True, text=True, timeout=timeout)


def _publishing() -> bool:
    """Off when asked, and off where there is nothing to push to - a temp tree in --selftest has a
    .git-working directory but no remote, and must never reach the real repository."""
    if os.environ.get("NRG_NO_LOCK_PUSH"):
        return False
    if not (REPO / WORKING_GIT).is_dir():
        return False
    try:
        return bool(_wgit("config", "--get", "remote.origin.url").stdout.strip())
    except (OSError, Exception):
        return False


def _rebase_records_on_origin() -> None:
    """Half 2: start from origin's record, so the row is written on top of truth, never merged."""
    try:
        if _wgit("fetch", "-q", "origin", "main", timeout=120).returncode:
            return
        behind = _wgit("rev-list", "--count", "HEAD..origin/main").stdout.strip()
        if behind in ("", "0"):
            return
        local = _wgit("status", "--porcelain", "--", *RECORD_PATHS).stdout.strip()
        if local:
            print(f"  note: the private half is {behind} commit(s) behind origin and these records"
                  f" differ here;\n        taking origin's and re-applying this change on top of it (D-314).")
        _wgit("checkout", "origin/main", "--", *RECORD_PATHS)
    except (OSError, Exception):
        pass


def _unpublished_non_record_commits(paths) -> list[str]:
    """T-175 / fix (b): the commits between origin/main and HEAD that touch anything BESIDE these
    records. D-314 exempts a lock push from "ask before every push" because it publishes only
    "chat X holds Y" — but the push is `HEAD:main`, which carries the WHOLE branch, so the
    exemption is only true while nothing else is sitting unpushed. Measured 2026-11-07: a
    `take doc:Paper2` carried five unapproved private commits to GitHub, and a queue publish
    carried a sixth. Returns one "<sha> <subject>" per offending commit, newest first; an empty
    list means the push really does publish nothing but the records.
    """
    try:
        rng = "origin/main..HEAD"
        out = _wgit("log", "--format=%h %s", "--name-only", rng, timeout=60)
        if out.returncode:
            return []                                   # no origin/main to compare: _publishing() gates that
        keep, cur, touched = [], None, False
        for line in out.stdout.split("\n") + [""]:
            if line.strip() == "":
                if cur and touched:
                    keep.append(cur)
                continue
            if cur is None or _looks_like_header(line):
                if cur and touched:
                    keep.append(cur)
                cur, touched = line.strip(), False
            elif line.strip() not in paths:
                touched = True
        return keep
    except (OSError, Exception):
        return []


def _looks_like_header(line: str) -> bool:
    """A `--format=%h %s --name-only` header line: a short sha, a space, then the subject. A path
    never starts with a 7-12 hex token followed by a space, so this separates the two safely."""
    head = line.split(" ", 1)
    return (len(head) == 2 and 4 <= len(head[0]) <= 12
            and all(c in "0123456789abcdef" for c in head[0]))


def publish_records(paths=RECORD_PATHS, what: str = "the claim") -> None:
    """Half 1: commit and push JUST these records, immediately. Never fatal."""
    if not _publishing():
        return
    try:
        present = [p for p in paths if (REPO / p).exists()]
        if not present:
            return
        _wgit("add", "--", *present)
        if not _wgit("diff", "--cached", "--quiet", "--", *present).returncode:
            return                                      # nothing staged: already current
        if _wgit("commit", "-q", "-m", f"doc_lock: {what}", "--", *present).returncode:
            print("  WARNING: could not commit the record — the claim is LOCAL ONLY (D-314)")
            return
        # T-175 fix (b), Martin 2026-11-07: the push is HEAD:main, so it carries the whole
        # branch. D-314's exemption covers the RECORD, not whatever else is unpushed, so refuse
        # rather than publish someone's unapproved work as a side effect of taking a claim.
        riders = _unpublished_non_record_commits(tuple(present))
        if riders:
            print(f"  the record is committed but NOT PUSHED — the claim is LOCAL ONLY (D-314, T-175).")
            print(f"           {len(riders)} unpushed commit(s) here touch more than the record, and a lock")
            print( "           push would publish them too, which D-314 does not cover:")
            for c in riders[:5]:
                print(f"             {c[:96]}")
            if len(riders) > 5:
                print(f"             ... and {len(riders) - 5} more")
            print( "           Push them yourself when you mean to (CLAUDE.md §7), then re-run this")
            print( "           command and the claim publishes on its own.")
            return
        r = _wgit("push", "-q", "origin", "HEAD:main", timeout=180)
        if r.returncode:
            print("  WARNING: the record is committed but NOT PUSHED — no other chat can see this")
            print("           claim yet (D-314). " + (r.stderr.strip().splitlines() or [""])[-1][:120])
            print("           Fetch, then re-run this command: the tool rewrites its row on top of origin.")
    except (OSError, Exception) as e:
        print(f"  WARNING: the claim is LOCAL ONLY — could not publish it ({type(e).__name__}) (D-314)")


# ── the lock file, written whole under its own lock ──────────────────────────
def _update(fn, publish: str | None = None) -> dict:
    """Read the lock file, apply fn(dict) in place, write it back, all under a lock file, so a
    claim taken by one chat and the machine lock taken by another never overwrite each other.
    With `publish`, the result is committed and pushed at once (D-314)."""
    import register_io
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if publish:
        _rebase_records_on_origin()
    with register_io.excl_lock(LOCK):
        d = read() or {"holder": None, "since": _now(), "note": ""}
        if d.get("holder") == "UNREADABLE":
            raise SystemExit("  working/DOCUMENT_LOCK.json is corrupt; repair it by hand before taking anything")
        fn(d)
        LOCK.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if publish:
        publish_records(what=publish)
    return d


# ── claims (1.2.0) ───────────────────────────────────────────────────────────
# Families whose doc_tier name is long, or that are edited together, have a short claim name.
ALIASES = {
    "doc:Paper2": ("Hollingham_2026_Paper2_amended", "Paper2_plain"),   # the paper and its plain-language companion (D-270)
    "doc:PaperM": ("PaperM", "PaperM_plain"),   # the paper and its plain-language companion (D-258)
    "doc:Paper1": ("Paper1", "Paper1_plain"),   # the paper and its plain-language companion (D-265)
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
    """May this chat write this path? Refused when ANOTHER chat holds the claim covering it - or,
    since 1.4.0, when the private store is absent and the path is a document (R1).

    The absent-store case splits deliberately. For doc:* it REFUSES: the ODTs are not in a
    public-only clone anyway, so nothing legitimate is lost, and an unseen claim on a document
    family is exactly the Paper M accident. For pipeline and tools it WARNS and permits, so a
    session that genuinely has only the public repository can still run the pipeline."""
    cl = claim_for_path(rel)
    state, why = store_state()
    if state == "ABSENT":
        if cl and cl.startswith("doc:"):
            return False, (f"{rel} is in {cl}, and the private repository is not present ({why}), so whether "
                           f"another chat holds {cl} is UNKNOWN - not free. Attach both repositories "
                           f"({ATTACH[0]} / {ATTACH[1]}) and run tools/cloud_setup.sh, then retry.")
        print(f"  WARNING: {rel}"
              + (f" is in {cl}, whose holder is UNKNOWN" if cl else " is not under any claim")
              + f" - the private repository is not present ({why}). Permitting the write: a public-only"
              " session may still run the pipeline and the tools. Nothing here is a statement that the"
              " claim is free.", file=sys.stderr)
        return True, ""
    h = holder_of(cl)
    me = chat_id(chat)
    if h is None or h == me:
        if h == me:
            touch(cl, chat)        # R4: activity, not age since `since`
        return True, ""
    since = claims()[cl].get("since", "?")
    return False, (f"{rel} is in {cl}, which chat {h!r} has held since {since}"
                   f" ({claims()[cl].get('note') or 'no note'}). "
                   + ("Set NRG_CHAT to this chat's name if it is this chat's claim. " if not me else "")
                   + "Ask that chat to release it, or ask Martin.")


def registration_note(chat: str | None) -> tuple[bool, list[str]]:
    """(may proceed, lines to print). D-301: a chat that has not registered is told, and under
    REGISTRATION_REQUIRED refused. Import late and defensively - chat_register imports this module,
    and a tree without the register must still be able to take the first claim."""
    try:
        import chat_register
    except Exception:                                                 # pragma: no cover
        return True, []
    if not chat or chat_register.is_registered(chat):
        return True, []
    lines = [f"  chat {chat!r} is not in {chat_register.REGISTER.name} — registration is compulsory"
             f" (D-301). Register it with:",
             f"      python3 tools/chat_register.py register --chat {chat!r} --kind "
             f"pipeline|document|tools|readonly|fieldwork --purpose \"<one line>\""]
    if REGISTRATION_REQUIRED:
        return False, ["  REFUSED - " + lines[0][7:]] + lines[1:]
    return True, ["  WARNING:" + lines[0][2:]] + lines[1:]


def jobs_made_ready() -> list[str]:
    """D-301: a job fires when something is already running, and a release is one of the two such
    moments. So a release says what it unblocked - the session that released then fires it."""
    try:
        import job_queue
        return [j["id"] for j in job_queue.ready(promote=True, quiet=True)]
    except Exception:                                                 # pragma: no cover
        return []


def take_claim(name: str, chat: str | None, note: str, force: bool,
               link: str | None = None, by: str | None = None) -> int:
    if not store_ok():
        refuse_absent_store(f"taking the claim {name!r}")
        return 1
    me = chat_id(chat)
    if not me:
        print("  REFUSED - a claim is held by a chat: give --chat NAME or set NRG_CHAT")
        return 1
    if name not in claim_names():
        print(f"  REFUSED - no claim called {name!r}. Claims: {', '.join(claim_names())}")
        return 1
    may, lines = registration_note(me)
    for line in lines:
        print(line, file=sys.stderr if not may else sys.stdout)
    if not may:
        return 1
    # R7: a forced TAKE is the destructive override - it leaves the other chat's unshipped work
    # unprotected - so it must be signed. A forced release is not, and defaults --by instead.
    if force and not (by or "").strip():
        held = claims().get(name)
        if held and held.get("chat") and held["chat"] != me:
            print(f"  REFUSED - --force would take {name} from chat {held['chat']!r}, whose unshipped work")
            print("  would then be unprotected. That is an override and must be signed: add --by NAME")
            print(f"  (for example --by martin). It is logged to {OVERRIDES}.")
            return 1
    out = {}
    lk = (link or os.environ.get("NRG_SESSION_LINK") or "").strip()

    def fn(d):
        c = (d.get("claims") or {}).get(name)
        if c and c.get("chat") and c["chat"] != me and not force:
            out["refused"] = c
            return
        out["took_from"] = c.get("chat") if c else None
        rec = {"chat": me, "host": _who(), "mode": session_mode(), "since": _now(),
               "touched": _now(), "note": note}
        if lk:
            rec["link"] = lk              # R5: stored when known, never required
        d.setdefault("claims", {})[name] = rec
    _update(fn, publish=f"{name} claimed by chat {me!r}")
    if "refused" in out:
        c = out["refused"]
        print(f"  REFUSED - {name} is held by chat {c['chat']!r} since {c.get('since')} ({c.get('note') or 'no note'}).")
        if stale_note(c):
            print(f"  It is {stale_note(c)} - which flags it, and does not release it (R4).")
        print("  Ask that chat to release it. --force --by NAME takes it anyway (Martin's call: that chat's unshipped work is then unprotected).")
        return 1
    print(f"  {name} claimed by chat {me!r}" + (f" ({session_mode()})" if session_mode() != "unknown" else ""))
    if force and out.get("took_from") and out["took_from"] != me:
        log_override("forced-take", name, out["took_from"], me, (by or "").strip(), note)
    mark_publish_owed(f"take {name} by {me}")
    return 0


def release_claim(name: str, chat: str | None, force: bool, by: str | None = None) -> int:
    if not store_ok():
        refuse_absent_store(f"releasing the claim {name!r}")
        return 1
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
        out["held_by"] = c.get("chat")
        out["note"] = c.get("note") or ""
        d["claims"].pop(name, None)
    _update(fn, publish=f"{name} released by chat {me!r}")
    if out.get("free"):
        print(f"  {name} was not claimed")
        return 0
    if "other" in out:
        print(f"  REFUSED - {name} is held by chat {out['other']!r}, not {me!r}. --force --by NAME releases it anyway.")
        return 1
    print(f"  {name} released")
    # R7: releasing SOMEONE ELSE'S claim is the override. --by defaults to this chat (the sign-off),
    # because a release is recoverable - the claim can simply be retaken.
    if out.get("held_by") and out["held_by"] != me:
        log_override("forced-release", name, out["held_by"], None,
                     (by or "").strip() or me or "unknown", out.get("note", ""))
    mark_publish_owed(f"release {name}")
    ready = jobs_made_ready()
    if ready:
        print(f"  this release made {len(ready)} job(s) ready: {', '.join(ready)}")
        for jid in ready:
            print(f"      python3 tools/job_queue.py fire {jid} --by {me or '<this chat>'!r}")
        print("  fire them now, or they wait for HQ's next pass (D-301).")
    return 0


def print_claims() -> None:
    if not store_ok():
        # R1: never print a list of free claims we cannot vouch for.
        print("  claims: UNKNOWN (private repository not present)")
        for k in claim_names():
            print(f"    {k:<18} UNKNOWN")
        return
    cs = claims()
    if not cs:
        print("  claims: none held")
        return
    print("  claims:")
    for k in sorted(cs):
        c = cs[k]
        extra = "  ".join(x for x in (c.get("mode") or "", stale_note(c), c.get("note") or "") if x)
        print(f"    {k:<18} chat {c['chat']!r:<28} since {c.get('since','?')}  {extra}".rstrip())
        if c.get("link"):
            print(f"    {'':<18} {c['link']}")



# ── acceptance tests (1.4.0, spec NRG_handover_control_board_2026-11-04 section 6) ──────────────
# Every case runs the real CLI in a throwaway tree through NRG_REPO_ROOT. THE REAL LOCK IS NEVER
# READ OR WRITTEN: that was the condition this work was signed off under.
def _run(args: list[str], tree: pathlib.Path, **env_extra) -> tuple[int, str]:
    env = dict(os.environ, NRG_REPO_ROOT=str(tree))
    env.pop("NRG_CHAT", None)
    env.pop("NRG_NO_PRIVATE_STORE", None)
    env.pop("NRG_SESSION_LINK", None)
    # 2026-11-06 (T-155): the two LOCK overrides, for the same reason as the three above - a
    # selftest declares its own world, and anything it inherits decides a test it did not set.
    # tools/cloud_ship.sh:59 exports NRG_DOC_LOCK_HOLDER="cloud" for the whole run, correctly:
    # during a cloud ship the lock IS held as "cloud". That export reaches nrg_git.sh --ship at
    # its line 147, then check_all, then this selftest, where _who() honours the override before
    # consulting .git/nrg_machine - so tests 8a and 8b could never reach the D-299 path they
    # assert and both failed. check_all 1.33.0 made this selftest a GATE on 2026-11-04, so from
    # that day every cloud ship failed at section 31 with no cloud ship in between to notice.
    # Measured 2026-11-06: selftest exit 0 bare, exit 1 under the override, 8a and 8b the only
    # failures. Fixed here rather than in cloud_ship because the caller is right and a selftest
    # that reads ambient state is wrong whoever set it.
    env.pop("NRG_DOC_LOCK_HOLDER", None)
    env.pop("NRG_DOC_LOCK_FILE", None)
    env.update({k: v for k, v in env_extra.items() if v is not None})
    for k, v in env_extra.items():
        if v is None:
            env.pop(k, None)
    r = subprocess.run([sys.executable, str(HERE / "tools" / args[0]), *args[1:]],
                       capture_output=True, text=True, env=env, cwd=str(HERE))
    return r.returncode, r.stdout + r.stderr


def _mktree(d: pathlib.Path, private: bool, lock: dict | None) -> pathlib.Path:
    (d / "working").mkdir(parents=True, exist_ok=True)
    (d / ".git").mkdir(exist_ok=True)
    if private:
        (d / ".git-working").mkdir(exist_ok=True)
    if lock is not None:
        (d / "working/DOCUMENT_LOCK.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")
    return d


def _ago(h: float) -> str:
    return (datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _selftest() -> int:
    import tempfile
    ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        if not cond:
            ok = False
            print(f"  FAIL  {label}" + (f"\n        {detail.strip()[:600]}" if detail else ""))

    with tempfile.TemporaryDirectory() as td:
        T = pathlib.Path(td)

        # 1. A public-only clone: UNKNOWN, not free - and `take` refuses with the attach lines.
        t1 = _mktree(T / "public_only", private=False, lock=None)
        rc, out = _run(["doc_lock.py", "claims"], t1)
        check("1a public-only: claims read UNKNOWN", "UNKNOWN" in out, out)
        check("1b public-only: no claim is listed as free", "free:" not in out, out)
        rc, out = _run(["doc_lock.py", "take", "tools", "--chat", "X"], t1)
        check("1c public-only: take refuses", rc == 1, out)
        check("1d public-only: the refusal gives the attach lines", "add_repo newbroman" in out, out)
        rc, out = _run(["work_board.py", "--no-probe"], t1)
        check("1e public-only: the board says ABSENT first", "PRIVATE STORE ABSENT" in out, out)
        check("1f public-only: the board does not say free", "    free:" not in out, out)
        # 1.4.1: the machine-lock line is read from the SAME private file, so it read "free" while
        # every claim above it read UNKNOWN. Found from a public-only clone at cd42999.
        check("1g public-only: the machine-lock line reads UNKNOWN",
              "documents (machine lock): UNKNOWN" in out, out)
        check("1h public-only: the machine-lock line does not say free",
              "machine lock): free" not in out, out)

        # 2. Both repositories, no lock yet: the first-ever take MUST still be possible.
        t2 = _mktree(T / "no_lock_yet", private=True, lock=None)
        rc, out = _run(["doc_lock.py", "claims"], t2)
        check("2a present-no-lock: reported as such", "no lock file yet" in out, out)
        rc, out = _run(["doc_lock.py", "take", "tools", "--chat", "First", "--note", "n"], t2)
        check("2b present-no-lock: the first take succeeds", rc == 0, out)
        held = json.loads((t2 / "working/DOCUMENT_LOCK.json").read_text())["claims"]["tools"]
        check("2c the take records mode and activity", bool(held.get("mode")) and bool(held.get("touched")), str(held))
        # 1.4.1: the other half of 1g - with the store PRESENT and nobody holding the ODTs, the
        # machine-lock line must still read "free". UNKNOWN is the absent store, not the empty lock.
        rc, out = _run(["work_board.py", "--no-probe"], t2)
        check("2d present-no-lock: the machine-lock line reads free",
              "documents (machine lock): free" in out, out)

        # 3. Staleness is measured from ACTIVITY, not from `since` (R4).
        base = {"holder": None, "since": _ago(200), "note": "", "claims": {
            "tools":      {"chat": "Fresh", "since": _ago(200), "touched": _ago(0.5), "note": "busy"},
            "doc:report": {"chat": "Quiet", "since": _ago(200), "touched": _ago(30),  "note": "went away"},
            "doc:MS":     {"chat": "Gone",  "since": _ago(200), "touched": _ago(100), "note": "long gone"}}}
        t3 = _mktree(T / "stale", private=True, lock=base)
        rc, out = _run(["work_board.py", "--no-probe"], t3)
        check("3a a claim taken 200 h ago but used 30 min ago is NOT stale",
              "Fresh" in out and "STALE" not in out.split("Quiet")[0].split("Fresh")[-1], out)
        check("3b 30 h without activity is STALE", "STALE" in out, out)
        check("3c 100 h without activity is ABANDONED", "ABANDONED" in out, out)
        rc, out = _run(["doc_lock.py", "claims", "--json"], t3)
        j = json.loads(out)
        check("3d --json carries the flags for the dashboard (R6b)",
              j["stale"].get("doc:report") == "STALE" and j["stale"].get("doc:MS") == "ABANDONED", out)
        check("3e the thresholds are configurable, not typed",
              j["stale_hours"] == 24 and j["abandoned_hours"] == 72, out)
        rc, out = _run(["doc_lock.py", "claims", "--json"], t3, NRG_CLAIM_STALE_HOURS="48")
        check("3f NRG_CLAIM_STALE_HOURS moves the line",
              json.loads(out)["stale"].get("doc:report") is None, out)

        # 4. A path under another chat's claim is named, with its holder.
        rc, out = _run(["doc_lock.py", "who", "report_edits/odt/report9.odt"], t3)
        check("4a who names the holder", "doc:report" in out and "Quiet" in out, out)
        check("4b who shows the staleness", "STALE" in out, out)

        # 5. check_write: refuses doc:*, warns and permits pipeline/tools, with no private store.
        code = ("import sys,doc_lock;"
                "a=doc_lock.check_write('report_edits/odt/report9.odt','X');"
                "b=doc_lock.check_write('tools/x.py','X');"
                "print('DOC',a[0]);print('TOOLS',b[0]);print('WHY',a[1][:80])")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           cwd=str(HERE / "tools"), env=dict(os.environ, NRG_REPO_ROOT=str(t1)))
        out = r.stdout + r.stderr
        check("5a no store: a document write is REFUSED", "DOC False" in out, out)
        check("5b no store: a tools write is permitted", "TOOLS True" in out, out)
        check("5c no store: the tools write warns", "WARNING" in out, out)
        check("5d the document refusal says UNKNOWN, not free", "UNKNOWN" in out, out)

        # 6. R7: a forced take must be signed; a forced release defaults --by; both are logged.
        t6 = _mktree(T / "override", private=True, lock={
            "holder": None, "since": _ago(1), "note": "",
            "claims": {"tools": {"chat": "Owner", "since": _ago(1), "touched": _ago(1), "note": "mine"}}})
        rc, out = _run(["doc_lock.py", "take", "tools", "--chat", "Thief"], t6)
        check("6a an unforced take of a held claim refuses", rc == 1 and "REFUSED" in out, out)
        rc, out = _run(["doc_lock.py", "take", "tools", "--chat", "Thief", "--force"], t6)
        check("6b a forced take without --by refuses", rc == 1 and "--by" in out, out)
        rc, out = _run(["doc_lock.py", "take", "tools", "--chat", "Thief", "--force", "--by", "martin"], t6)
        check("6c a forced take with --by succeeds", rc == 0, out)
        ov = (t6 / "working/claim_overrides.csv")
        check("6d the override is logged", ov.exists() and "forced-take" in ov.read_text()
              and "martin" in ov.read_text(), ov.read_text() if ov.exists() else "no file")
        rc, out = _run(["doc_lock.py", "release", "tools", "--chat", "Someone", "--force"], t6)
        check("6e a forced release needs no --by", rc == 0, out)
        check("6f the forced release is logged against this chat",
              "forced-release" in ov.read_text() and "Someone" in ov.read_text(), ov.read_text())
        check("6g the override log is append-only", len(ov.read_text().strip().splitlines()) == 3, ov.read_text())

        # 7. The env overrides are announced wherever the board prints.
        rc, out = _run(["work_board.py", "--no-probe"], t3)
        check("7a NRG_REPO_ROOT is announced", "NRG_REPO_ROOT is set" in out, out)
        rc, out = _run(["doc_lock.py", "claims"], t1, NRG_NO_PRIVATE_STORE="1")
        check("7b NRG_NO_PRIVATE_STORE is announced in the first line",
              "NRG_NO_PRIVATE_STORE=1" in out, out)
        t7 = _mktree(T / "declared", private=True, lock=base)
        rc, out = _run(["doc_lock.py", "take", "tools", "--chat", "X"], t7, NRG_NO_PRIVATE_STORE="1")
        check("7c a session that declares no private store cannot take a claim", rc == 1, out)

        # 8. D-299 unchanged: on the bridge, with no recorded machine name, the machine lock refuses.
        t8 = _mktree(T / "bridge", private=True, lock={"holder": None, "since": _ago(1), "note": ""})
        rc, out = _run(["doc_lock.py", "take"], t8, HOME="/sessions/rcw-test")
        check("8a bridge without .git/nrg_machine refuses the machine lock", rc == 1 and "D-299" in out, out)
        (t8 / ".git/nrg_machine").write_text("john@john-ThinkPad-L14\n")
        rc, out = _run(["doc_lock.py", "take", "--note", "x"], t8, HOME="/sessions/rcw-test")
        check("8b with the name recorded it locks as the L14", rc == 0 and "ThinkPad" in out, out)
        check("8c BRIDGE_HOLDER still matches the old bad name",
              bool(BRIDGE_HOLDER.match("rcw-abc123@claude")))

        # 9. R3/R2: the private repository two commits behind origin is shown as behind.
        t9 = _mktree(T / "behind", private=True, lock=base)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        bare = T / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
        gd = ["git", "--git-dir", str(t9 / ".git-working"), "--work-tree", str(t9)]
        subprocess.run(["git", "init", "-q", "-b", "main", "--separate-git-dir",
                        str(t9 / ".git-working"), str(t9 / "wt")], check=True, capture_output=True)
        # init above makes a worktree we do not want; drive the real one directly instead
        subprocess.run(gd + ["add", "working/DOCUMENT_LOCK.json"], check=True, env=env, capture_output=True)
        subprocess.run(gd + ["commit", "-qm", "base"], check=True, env=env)
        subprocess.run(gd + ["remote", "add", "origin", str(bare)], check=True)
        subprocess.run(gd + ["push", "-q", "-u", "origin", "main"], check=True, env=env)
        other = T / "other"
        subprocess.run(["git", "clone", "-q", str(bare), str(other)], check=True)
        for i in (1, 2):
            (other / f"f{i}").write_text("x")
            subprocess.run(["git", "-C", str(other), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(other), "commit", "-qm", f"c{i}"], check=True, env=env)
        subprocess.run(["git", "-C", str(other), "push", "-q"], check=True, env=env)
        subprocess.run(gd + ["fetch", "-q", "origin"], check=True, env=env)
        rc, out = _run(["work_board.py", "--no-probe"], t9)
        check("9a the private repository is shown 2 behind origin/main", "2 behind" in out, out)
        check("9b the board reports a fetch time", "as of fetch" in out, out)

        # 10 (1.5.0, D-301). Registration warns and does not refuse; a release names the jobs it
        # made ready. The refusal itself is phase 4 and is exercised by flipping the switch.
        t10 = _mktree(T / "d301", private=True, lock={"holder": None, "claims": {}})
        rc, out = _run(["doc_lock.py", "take", "tools", "--chat", "Unregistered"], t10)
        check("10a an unregistered chat is warned", rc == 0 and "is not in chat_register.csv" in out, out)
        check("10b and the warning gives the register command", "chat_register.py register" in out, out)
        rc, out = _run(["doc_lock.py", "release", "tools", "--chat", "Unregistered"], t10)
        check("10c release works", rc == 0, out)
        # the same take with the switch flipped is a refusal, which is all phase 4 is (T-138)
        src = (HERE / "tools/doc_lock.py").read_text(encoding="utf-8")
        (t10 / "tools").mkdir(exist_ok=True)
        for mod in ("register_io.py", "chat_register.py", "job_queue.py", "doc_tier.py"):
            f = HERE / "tools" / mod
            if f.exists():
                (t10 / "tools" / mod).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
        (t10 / "tools/doc_lock.py").write_text(
            src.replace("REGISTRATION_REQUIRED = False", "REGISTRATION_REQUIRED = True"),
            encoding="utf-8")
        r = subprocess.run([sys.executable, str(t10 / "tools/doc_lock.py"), "take", "tools",
                            "--chat", "Unregistered"], capture_output=True, text=True,
                           env=dict(os.environ, NRG_REPO_ROOT=str(t10)), cwd=str(t10))
        check("10d with REGISTRATION_REQUIRED the same take is REFUSED",
              r.returncode == 1 and "REFUSED" in (r.stdout + r.stderr), r.stdout + r.stderr)

        # a release that frees a claim a queued job waits for names that job
        t11 = _mktree(T / "d301b", private=True, lock={
            "holder": None, "claims": {"pipeline": {"chat": "Mine", "since": _ago(1),
                                                    "touched": _ago(0.1), "note": ""}}})
        import csv as _csv
        import job_queue as _jq
        (t11 / "notes/specs").mkdir(parents=True, exist_ok=True)
        # assembled, not written out: docref_lint reads any *.md token in tools/*.py as a citation
        # of a document that should exist, and this one is a throwaway-tree fixture (same reason as
        # job_queue.py's `absent`).
        fixture = "notes/specs/throwaway_brief" + ".md"
        (t11 / fixture).write_text("brief", encoding="utf-8")
        with (t11 / "working/job_queue.csv").open("w", encoding="utf-8", newline="") as fh:
            w = _csv.DictWriter(fh, fieldnames=_jq.FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerow({"id": "J-7", "title": "waiting on pipeline", "brief": fixture,
                        "claim": "pipeline", "waits_for": "claim_free:pipeline",
                        "target": "new_session", "status": "queued"})
        rc, out = _run(["doc_lock.py", "release", "pipeline", "--chat", "Mine"], t11)
        check("10e the release names the job it made ready", "J-7" in out and "made" in out, out)
        check("10f and gives the line that fires it", "job_queue.py fire J-7" in out, out)

    print("doc_lock selftest (control board, spec section 6):", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["status", "take", "release", "check", "who", "claims"])
    ap.add_argument("name", nargs="?", default=None,
                    help="take/release: a claim name (doc:PaperM, pipeline, tools...); omitted = the machine lock. "
                         "who: a path")
    ap.add_argument("--chat", default=None, help="this chat's name (default: $NRG_CHAT)")
    ap.add_argument("--note", default="", help="what you are editing")
    ap.add_argument("--link", default=None,
                    help="R5: this session's claude.ai URL, when it knows it (or $NRG_SESSION_LINK). Never required")
    ap.add_argument("--by", default=None,
                    help="R7: who authorised an override. Required for a forced take; defaults to this chat on release")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.action == "claims":
        state, why = store_state()
        if a.json:
            held = claims() if store_ok() else {}
            print(json.dumps({"store": state, "store_why": why, "names": claim_names(), "held": held,
                              "stale": {k: staleness(v) for k, v in held.items() if staleness(v)},
                              "warnings": override_warnings(),
                              "stale_hours": stale_hours(), "abandoned_hours": abandoned_hours()}, indent=1))
        else:
            print_store_line()
            print_claims()
        return 0
    if a.action == "who":
        if not a.name:
            ap.error("who needs a path")
        cl = claim_for_path(a.name)
        if not store_ok():
            print(f"{a.name}: {cl or 'no claim covers it (shared)'}"
                  + (", holder UNKNOWN (private repository not present)" if cl else ""))
            return 1 if cl else 0
        h = holder_of(cl)
        hold = ""
        if h:
            c = claims()[cl]
            hold = f", held by chat {h!r}" + (f" [{stale_note(c)}]" if stale_note(c) else "")
        print(f"{a.name}: {cl or 'no claim covers it (shared)'}" + (hold if h else (", unclaimed" if cl else "")))
        return 0
    if a.action == "check":
        return status(quiet=a.quiet)
    if a.action == "status":
        status()
        print_claims()
        return 0
    if a.action == "take":
        return (take_claim(a.name, a.chat, a.note, a.force, a.link, a.by) if a.name
                else acquire(a.note, a.force))
    return release_claim(a.name, a.chat, a.force, a.by) if a.name else release(a.note, a.force)


if __name__ == "__main__":
    sys.exit(main())
