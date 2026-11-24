#!/usr/bin/env python3
"""
doc_tier_lint — is the document-phase register complete and self-consistent? (D-144)

Checks, all gating:
  1. Every ODT/ODM family on disk (docs/**, report_edits/odt) has a doc_tier.csv row,
     and every row names a family that exists. An unregistered family is one
     odt_edit would refuse to write — so this fails BEFORE a session meets that.
  2. `current` agrees with the phase: a family is `live` iff its phase_live equals
     the header's phase. (A family live out of phase is a decision, and needs the
     header changed with a D-entry, not a cell changed by hand.)
  3. Every `set_by` and every logged `reason` that is a D-number exists in the
     decision log; every logged reason is a valid reason (D-number, changelog id,
     or exempt tool).
  4. Header carries phase= and set_by=.
  5. WITNESS (1.1.0, D-325: `committed`). A frozen family's committed mirror is compared with its
     own earlier committed state, and a change in PROSE must be accounted for by a row of
     working/doc_tier_log.csv carrying a D-number or a changelog id. Two actors: the mirror is
     pandoc reading the ODT's bytes, whoever wrote them; the log row is written by odt_edit's guard
     at the moment of a reasoned write. A hand edit in LibreOffice, a write by any other route, or a
     prose write passed off under a mechanical tool's name leaves a mirror that moved and no such
     row. Checks 1-4 cannot see any of those: they read the register and the log, never a document.

     What is compared: for each frozen family, the LATEST step in which its mirror's prose moved —
     HEAD -> working tree, then each commit touching the mirror against its parent, newest first,
     stopping at the first that moved prose (so a numbers-only commit on top of an unaccounted edit
     does not launder it). "Prose" is the mirror with its header dropped and every number, sign and month name
     folded to `#`, so what the exempt tools do (numbers, versions, table values, field dates,
     renumbered references) is not a change. A step is judged only if the family was frozen in the
     register AT BOTH ENDS of it (a family's last live edit is not a fault on the day it freezes).
     What accounts for it: a D-number/changelog row for that family whose `dst` version lies in
     (old mirror's source version, new one's]; when the document was written in place (same version,
     or an unversioned family), a row dated inside the step (previous mirror commit, this one].
     What it cannot see: a second, unlogged write hidden inside a step that also carries a reasoned
     one (the log records no content hash); a step older than a shallow clone's boundary; anything
     in a clone without the private log, where it says SKIP and checks 1-4 still gate.
     Cleared by: the reasoned odt_edit write that should have been made (a new version, logged).

Usage:
    python3 tools/doc_tier_lint.py             # report, exit 1 on any fault
    python3 tools/doc_tier_lint.py --selftest  # exercise the detectors
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-11-24 (D-325, R07). The gate gets a witness: a frozen family's
#   committed mirror against its own earlier committed state, and a prose change must have a D-number/changelog row
#   in working/doc_tier_log.csv (check 5). Until now nothing here read a document, so a prose edit to a frozen ODT
#   made outside odt_edit, or under a mechanical tool's name, passed. Measured on the day: 35 mirror steps in this
#   clone's history, 13 with a prose change, every one accounted for; --selftest proves the unaccounted one fails.
# 1.0.0  # Hollingham (2026) — 2026-09-07. First issue (D-144).

import csv
import datetime
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from doc_tier import (REGISTER, LOG, REASON_RE, STATES, family, read_register,   # noqa: E402
                      reason_is_valid)

ODT_GLOBS = ("docs/**/*.odt", "docs/**/*.odm", "report_edits/odt/*.odt", "report_edits/odt/*.odm")


def families_on_disk() -> set[str]:
    fams = set()
    for g in ODT_GLOBS:
        for p in REPO.glob(g):
            if p.name.startswith((".", "~")) or "_to_delete" in p.parts:
                continue
            f = family(p)
            if f:
                fams.add(f)
    return fams


def decision_ids() -> set[str]:
    try:
        from context_for import parse_entries
        return {e["id"] for e in parse_entries()}
    except Exception as exc:                       # the lint must still run without it
        print(f"  warn  could not parse the decision log ({exc}); D-number checks skipped")
        return set()


def evaluate(meta: dict, rows: dict[str, dict], on_disk: set[str],
             dids: set[str] | None, log_rows: list[dict]) -> list[str]:
    faults = []
    phase = meta.get("phase")
    if not phase:
        faults.append("header comment lacks phase=")
    if not meta.get("set_by"):
        faults.append("header comment lacks set_by=")
    for f in sorted(on_disk - set(rows)):
        faults.append(f"no doc_tier.csv row for family {f!r} (odt_edit would refuse to write it)")
    for f in sorted(set(rows) - on_disk):
        faults.append(f"row {f!r} names a family with no ODT on disk")
    for f, r in rows.items():
        cur = r.get("current")
        if cur not in STATES:
            faults.append(f"{f}: current={cur!r} is not one of {STATES}")
            continue
        want = "live" if (phase and r.get("phase_live") == phase) else "frozen"
        if cur != want:
            faults.append(f"{f}: current={cur} but phase={phase} and phase_live={r.get('phase_live')} "
                          f"imply {want} — change the phase (with a D-entry), not the cell")
        sb = r.get("set_by", "")
        if not reason_is_valid(sb):
            faults.append(f"{f}: set_by={sb!r} is not a D-number or changelog id")
        elif dids is not None and sb.startswith("D-") and sb not in dids:
            faults.append(f"{f}: set_by {sb} is not in the decision log")
    for i, lr in enumerate(log_rows, 1):
        rs = lr.get("reason", "")
        if not reason_is_valid(rs):
            faults.append(f"doc_tier_log row {i}: reason {rs!r} invalid")
        elif dids is not None and rs.startswith("D-") and rs not in dids:
            faults.append(f"doc_tier_log row {i}: {rs} is not in the decision log")
        if lr.get("family") not in rows:
            faults.append(f"doc_tier_log row {i}: family {lr.get('family')!r} has no register row")
    return faults


def read_log() -> list[dict]:
    if not LOG.is_file():
        return []
    with LOG.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- check 5: the witness (D-325)

MIRROR_GLOBS = ("docs/**/text/*.md", "report_edits/text/*.md")
_SRC = re.compile(r"GENERATED MIRROR of (\S+\.od[tm])")
_NUM = re.compile(r"[-−–+]?\d+(?:[.,]\d+)*")
_MONTH = re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
                    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b")
_VERSION = re.compile(r"_v(\d+(?:_\d+)*)$")


def mirror_source(text: str) -> str | None:
    """The ODT a mirror says it was generated from (its first line), or None."""
    m = _SRC.search(text[:400])
    return m.group(1) if m else None


def prose(text: str) -> list[str]:
    """A mirror as prose: header comments dropped, numbers (with sign) and month names folded to '#'."""
    out = []
    for line in text.splitlines():
        if line.startswith("<!--"):
            continue
        line = re.sub(r"\s+", " ", _MONTH.sub("#", _NUM.sub("#", line))).strip()
        if line:
            out.append(line)
    return out


def _ver(name: str | None) -> tuple[int, ...] | None:
    m = _VERSION.search(Path(name).stem) if name else None
    return tuple(int(x) for x in m.group(1).split("_")) if m else None


def accounting_rows(fam: str, old_src: str | None, new_src: str | None, t0: str, t1: str,
                    log_rows: list[dict]) -> list[dict]:
    """The log rows that account for a prose change in `fam` between two mirror states.

    Only a D-number or a changelog id accounts for prose; a mechanical tool's row never does. By version when
    the document moved to a new one, by the step's dates when it was written in place."""
    vo, vn = _ver(old_src), _ver(new_src)
    by_version = vo is not None and vn is not None and vo != vn
    out = []
    for r in log_rows:
        if r.get("family") != fam or not REASON_RE.match(r.get("reason", "")):
            continue
        if by_version:
            v = _ver(r.get("dst"))
            if v is not None and vo < v <= vn:
                out.append(r)
        elif _when(t0) < _when(r.get("date", "")) <= _when(t1):
            out.append(r)
    return out


def _when(iso: str) -> datetime.datetime:
    try:
        d = datetime.datetime.fromisoformat(iso)
    except ValueError:
        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


def _git(repo: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def _frozen_at(repo: Path, rev: str | None, fam: str) -> bool:
    """Was `fam` frozen in the register as committed at `rev` (None = the working tree)?"""
    if rev is None:
        text = (repo / "tools" / "doc_tier.csv").read_text(encoding="utf-8")
    else:
        text = _git(repo, "show", f"{rev}:tools/doc_tier.csv")
        if text is None:
            return False
    body = [l for l in text.splitlines() if not l.startswith("#")]
    return any((r.get("family") or "").strip() == fam and (r.get("current") or "").strip() == "frozen"
               for r in csv.DictReader(body))


def witness(repo: Path, log_rows: list[dict], now: str | None = None) -> tuple[list[str], int, list[str]]:
    """(faults, steps judged, notes). One step per frozen family: the latest in which its mirror's prose moved."""
    faults, notes, judged = [], [], 0
    now = now or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    for g in MIRROR_GLOBS:
        for mp in sorted(repo.glob(g)):
            tree = mp.read_text(encoding="utf-8", errors="replace")
            src = mirror_source(tree)
            fam = family(src) if src else None
            if not fam or not _frozen_at(repo, None, fam):
                continue
            rel = mp.relative_to(repo).as_posix()
            log = (_git(repo, "log", "--format=%H %aI", "--", rel) or "").split("\n")
            commits = [l.split() for l in log if l.strip()]
            if not commits:
                notes.append(f"{fam}: mirror has no committed state yet")
                continue

            def steps():
                """Newest first: (label, old text, new text, frozen at both ends?, window start, window end)."""
                head = _git(repo, "show", f"HEAD:{rel}")
                if head is not None and head != tree:
                    yield "uncommitted", head, tree, _frozen_at(repo, "HEAD", fam), commits[0][1], now
                for i, (c, cdate) in enumerate(commits):
                    old = _git(repo, "show", f"{c}^:{rel}")
                    new = _git(repo, "show", f"{c}:{rel}")
                    if old is None or new is None:     # the mirror's first commit, or a shallow clone's boundary
                        return
                    t0 = commits[i + 1][1] if i + 1 < len(commits) else "1970-01-01T00:00:00+00:00"
                    yield (c[:8], old, new, _frozen_at(repo, f"{c}^", fam) and _frozen_at(repo, c, fam),
                           t0, cdate)

            seen = 0
            for label, a, b, was_frozen, t0, t1 in steps():
                seen += 1
                pa, pb = prose(a), prose(b)
                if pa == pb:
                    continue                           # numbers only: look at the step before
                judged += 1
                if not was_frozen:
                    notes.append(f"{fam}: prose moved at {label} while the family was live")
                    break
                rows = accounting_rows(fam, mirror_source(a), mirror_source(b), t0, t1, log_rows)
                if rows:
                    break
                n = len(set(pa) ^ set(pb))
                moved = [l for l in pb if l not in set(pa)] or [l for l in pa if l not in set(pb)]
                faults.append(
                    f"{fam} is frozen and its mirror's prose changed at {label} ({n} line(s), "
                    f"{Path(mirror_source(a) or '?').name} -> {Path(mirror_source(b) or '?').name}) with no "
                    f"D-number/changelog row in doc_tier_log for it: {moved[0][:90]!r}")
                break
            else:
                if seen:
                    judged += 1                        # every step numbers-only: examined, nothing to account for
                else:
                    notes.append(f"{fam}: no earlier committed mirror within this clone's history")
    return faults, judged, notes


def _selftest_witness() -> list[str]:
    bad = []
    old = ("<!-- GENERATED MIRROR of docs/x/Doc_v1_4.odt — do not edit. source-sha256=aa pandoc=3.1.3 -->\n"
           "The decline was 0.12 m by March 2018 (Table 4).\n\nRecharge fell after the clearfell.\n")
    nums = old.replace("Doc_v1_4", "Doc_v1_5").replace("0.12", "−0.31").replace("March 2018", "April 2019") \
              .replace("Table 4", "Table 6")
    edit = nums.replace("fell after", "rose after")
    row = lambda reason, dst="Doc_v1_5.odt", fam="Doc", date="2026-01-02T00:00:00+00:00": \
        {"family": fam, "dst": dst, "reason": reason, "date": date}
    a = lambda rows, o="docs/x/Doc_v1_4.odt", n="docs/x/Doc_v1_5.odt": \
        accounting_rows("Doc", o, n, "2026-01-01T00:00:00+00:00", "2026-01-03T00:00:00+00:00", rows)
    if prose(old) != prose(nums):
        bad.append("witness: a numbers-only change (value, sign, date, reference, version) read as prose")
    if prose(old) == prose(edit):
        bad.append("witness: a changed word not seen")
    if a([]) or a([row("table_gen")]) or a([row("field_convert")]):
        bad.append("witness: a mechanical tool's row accounted for prose")
    if not a([row("D-144")]) or not a([row("2026-09-07k")]):
        bad.append("witness: a reasoned row for the new version did not account for it")
    if a([row("D-144", fam="Other")]) or a([row("D-144", dst="Doc_v1_4.odt")]) or a([row("D-144", dst="Doc_v1_6.odt")]):
        bad.append("witness: a row for another family or a version outside the step accounted for it")
    same = lambda rows: a(rows, "docs/x/Doc.odt", "docs/x/Doc.odt")
    if not same([row("D-144", dst="Doc.odt")]) or same([row("D-144", dst="Doc.odt", date="2025-12-25T00:00:00+00:00")]):
        bad.append("witness: an in-place write is not judged by the step's dates")

    # End to end, in a throwaway repository: the FAULT this check exists for must fail, and its repair must pass.
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        g = lambda *args, date="2026-01-01T12:00:00+00:00": subprocess.run(
            ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
            capture_output=True, text=True, check=True,
            env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date, "PATH": __import__("os").environ["PATH"],
                 "HOME": tmp, "GIT_CONFIG_NOSYSTEM": "1"})
        (repo / "tools").mkdir()
        (repo / "docs/x/text").mkdir(parents=True)
        reg, mir = repo / "tools/doc_tier.csv", repo / "docs/x/text/Doc.md"

        def commit(text, date, tier="frozen"):
            reg.write_text(f"# phase=1 set_by=D-144\nfamily,phase_live,current,set_by,note\nDoc,-,{tier},D-144,\n")
            mir.write_text(text, encoding="utf-8")
            g("add", "-A", date=date)
            g("commit", "-q", "--allow-empty", "-m", "x", date=date)

        g("init", "-q")
        commit(old, "2026-01-01T12:00:00+00:00")
        commit(nums, "2026-01-02T12:00:00+00:00")
        f, n, _ = witness(repo, [])
        if f or n != 1:
            bad.append(f"witness (repo): a committed numbers-only step faulted or was not examined: {f} n={n}")
        commit(edit.replace("Doc_v1_5", "Doc_v1_6"), "2026-01-03T12:00:00+00:00")
        f, n, _ = witness(repo, [row("table_gen", dst="Doc_v1_6.odt")])
        if len(f) != 1 or "rose after" not in f[0]:
            bad.append(f"witness (repo): THE FAULT — frozen prose changed in a commit with no reasoned row — passed: {f}")
        if witness(repo, [row("2026-01-03a", dst="Doc_v1_6.odt")])[0]:
            bad.append("witness (repo): the same step WITH its reasoned row faulted")
        mir.write_text(edit.replace("Doc_v1_5", "Doc_v1_6").replace("clearfell", "storm"), encoding="utf-8")
        f, _, _ = witness(repo, [row("2026-01-03a", dst="Doc_v1_6.odt")], now="2026-01-04T12:00:00+00:00")
        if len(f) != 1 or "uncommitted" not in f[0]:
            bad.append(f"witness (repo): an UNCOMMITTED in-place prose edit to a frozen mirror passed: {f}")
        if witness(repo, [row("D-144", dst="Doc_v1_6.odt", date="2026-01-04T00:00:00+00:00")],
                   now="2026-01-04T12:00:00+00:00")[0]:
            bad.append("witness (repo): an uncommitted edit with a reasoned row inside the step faulted")
        commit(edit.replace("Doc_v1_5", "Doc_v1_7").replace("Recharge", "Storage"), "2026-01-05T12:00:00+00:00",
               tier="live")
        if witness(repo, [])[0]:
            bad.append("witness (repo): a live family's prose edit faulted")
        commit(edit.replace("Doc_v1_5", "Doc_v1_7").replace("Recharge", "Storage"), "2026-01-06T12:00:00+00:00")
        f, _, notes = witness(repo, [])
        if f or not any("while the family was live" in x for x in notes):
            bad.append(f"witness (repo): a family's last LIVE edit faulted on the day it froze: {f} {notes}")
    return bad


def selftest() -> int:
    meta = {"phase": "1", "set_by": "D-144"}
    rows = {"report": {"family": "report", "phase_live": "1", "current": "live", "set_by": "D-144"},
            "Paper1": {"family": "Paper1", "phase_live": "2", "current": "frozen", "set_by": "D-144"}}
    disk = {"report", "Paper1"}
    ok = evaluate(meta, rows, disk, {"D-144"}, []) == []
    bad = []
    if not ok:
        bad.append("clean case reported faults")
    if not evaluate(meta, rows, disk | {"Supplementary_Material"}, {"D-144"}, []):
        bad.append("missing row not detected")
    r2 = {**rows, "Paper1": {**rows["Paper1"], "current": "live"}}
    if not any("imply frozen" in f for f in evaluate(meta, r2, disk, {"D-144"}, [])):
        bad.append("out-of-phase live not detected")
    if not evaluate(meta, rows, disk, {"D-144"}, [{"family": "Paper1", "reason": "because"}]):
        bad.append("invalid log reason not detected")
    if not evaluate(meta, rows, disk, {"D-144"}, [{"family": "Paper1", "reason": "D-999"}]):
        bad.append("unknown D-number in log not detected")
    if family("report10.odt") != "report" or family("Paper1_v1_38.odt") != "Paper1" \
            or family("notes" + ".md") is not None:   # built, not a literal: docref_lint reads literals as citations
        bad.append("family() derivation")
    bad += _selftest_witness()
    if bad:
        print("doc_tier_lint --selftest: FAIL")
        for b in bad:
            print(f"    - {b}")
        return 1
    print("doc_tier_lint --selftest: OK")
    return 0


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()
    if not REGISTER.is_file():
        print(f"doc_tier_lint: FAULT — {REGISTER.relative_to(REPO)} missing")
        return 1
    meta, rows = read_register()
    faults = evaluate(meta, rows, families_on_disk(), decision_ids(), read_log())
    live = [f for f, r in rows.items() if r.get("current") == "live"]
    print(f"  phase {meta.get('phase')} (set by {meta.get('set_by')}): "
          f"live = {', '.join(live) or 'none'}; {len(rows) - len(live)} frozen; "
          f"{len(read_log())} logged frozen-document write(s)")
    if not LOG.is_file():
        print(f"  witness: SKIP (inputs absent by design) — no {LOG.relative_to(REPO)} (the private store); "
              f"no frozen document's prose was compared. Checks 1-4 still gate.")
    elif _git(REPO, "rev-parse", "HEAD") is None:
        print("  witness: SKIP — not a git checkout, so there is no committed mirror to compare with.")
    else:
        w_faults, judged, notes = witness(REPO, read_log())
        frozen = len(rows) - len(live)
        print(f"  witness (committed): {judged} of {frozen} frozen famil(ies) compared with an earlier committed "
              f"mirror; {len(w_faults)} unaccounted prose change(s)")
        for n in notes:
            print(f"      note  {n}")
        faults += w_faults
    if faults:
        print("doc_tier_lint: FAULT")
        for f in faults:
            print(f"    - {f}")
        return 1
    print("doc_tier_lint: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
