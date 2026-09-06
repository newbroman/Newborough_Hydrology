#!/usr/bin/env python3
"""
export_master_pdf — export report.odm to docs/report/report.pdf, headless.

WHY THIS IS NOT `soffice --convert-to pdf`.

  report.odm is a MASTER document. Its body is eleven linked sub-documents
  (report6..report15.odt) plus a table of contents and a figure index, and
  every "Figure 34" in the text is a SEQUENCE FIELD whose rendered number is
  computed at layout time across the assembled whole. A plain convert-to
  opens the master, does not necessarily pull the links, does not refresh the
  fields, does not rebuild the indexes, and writes a PDF that looks complete.

  That failure is silent and it is the expensive kind. A PDF whose links did
  not update carries the PREVIOUS revision of eleven chapters under today's
  timestamp; a PDF whose fields did not refresh carries figure numbers from
  whenever they were last laid out. Nothing downstream can tell — which is
  exactly why report.pdf was exported by hand for the life of the project,
  and why it then drifted four days behind its sources without anyone
  noticing (see tools/export_lag.py's docstring).

  So this drives LibreOffice through UNO and does the four steps by name:

      1. load with UpdateDocMode = FULL_UPDATE
      2. XLinkUpdate.updateLinks()        — pull the sub-documents
      3. TextFields.refresh()             — recompute the sequence fields
      4. every DocumentIndex .update()    — rebuild the TOC and figure index
      5. TextFields.refresh() again       — index page numbers move fields

  and then, because "the steps ran" is not the same as "the output is right":

      6. LINT THE RESULT BEFORE IT IS PUBLISHED.

THE GUARD IS THE POINT.

  The PDF is written to a temporary path and passed to tools/figref_lint.py.
  It is moved onto docs/report/report.pdf only if the caption sequence is
  clean and every in-text reference resolves. A headless export that lost its
  links produces a document with a fraction of the captions and hundreds of
  dangling references, so the lint catches precisely the failure that makes
  automation dangerous here. --baseline additionally refuses an export whose
  caption count has FALLEN against the published PDF, which catches a partial
  link update that is internally consistent.

  Refusing leaves the published PDF untouched and the temporary one on disk,
  named in the error, so the bad export can be opened and looked at.

USAGE
    python3 tools/export_master_pdf.py              # export, lint, publish
    python3 tools/export_master_pdf.py --check      # export and lint only
    python3 tools/export_master_pdf.py --out PATH   # write somewhere else
    python3 tools/export_master_pdf.py --no-baseline

REQUIRES
    python3-uno (Debian/Ubuntu: apt install python3-uno) and libreoffice.
    Both are checked for by name before anything is started.

EXIT
    0  exported and published (or --check passed)
    1  the export was refused by the lint, or a step failed
    2  the environment is missing something
"""
from __future__ import annotations

__version__ = "1.3.1"  # Hollingham (2026) — 2026-09-06. main() calls
#   uno_pdf.ensure_uno_interpreter() so `python tools/export_master_pdf.py`
#   from an active venv re-execs under the system python3-uno instead of
#   failing (the report.pdf rebuild trap, 2026-09-06).
# v1.3.0  # Hollingham (2026) — 2026-09-05. Refactored onto
#   tools/uno_pdf.py (W137/D-135): connect/refresh/store are now shared with
#   export_odt_pdf.py so the two PDF paths cannot drift; report.pdf output is
#   unchanged (same load props, refresh sequence and filter data). Prior:
# v1.2.0  # Hollingham (2026) — 2026-09-02. JPEG quality
#   90 -> 80, matching Martin's hand export on the L14. W126 recorded a
#   bridge-built report.pdf 27% larger than the published one and blamed the
#   LibreOffice version; the cause was this line. Content is unaffected —
#   only the image compression of the embedded figures.
# v1.1.0  # Hollingham (2026) — 2026-08-28. Pins the PDF
#   export settings and reports the size delta; 1.0.0 inherited the API
#   defaults and produced a file 26% larger than the hand export.

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import uuid

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from doc_paths import MASTER_ODM                      # noqa: E402
import uno_pdf                                       # noqa: E402
_find_soffice = uno_pdf.find_soffice          # kept: used by main()
_uno_available = uno_pdf.uno_available        # kept: used by main()

PUBLISHED = REPO / "docs/report/report.pdf"
FIGREF = REPO / "tools/figref_lint.py"
# Long, because this is eleven linked chapters and a 29 MB PDF, not a letter.
SOFFICE_TIMEOUT = 1800


LOCK = MASTER_ODM.parent / f".~lock.{MASTER_ODM.name}#"


def read_lock() -> dict | None:
    """Who holds LibreOffice's lock on the master, if anyone.

    The lock file is comma-separated: userid, username, when, host, profile.
    """
    if not LOCK.exists():
        return None
    try:
        f = LOCK.read_text(errors="replace").split(",")
    except OSError:
        return {"raw": "<unreadable>"}
    keys = ("userid", "username", "when", "host", "profile")
    d = {k: (f[i].strip() if i < len(f) else "") for i, k in enumerate(keys)}
    d["raw"] = ",".join(x.strip() for x in f)
    return d


def lock_is_our_own_corpse(info: dict) -> bool:
    """A lock this tool left behind, whose LibreOffice is definitely gone.

    Every run gets a throwaway profile under /tmp/lo_master_*. If the lock
    names one of those and the directory is no longer there, the process that
    held it cannot still be running, so the lock is a corpse and nothing is
    protected by honouring it. Any other holder — the user's own LibreOffice,
    another machine, a profile that still exists — is left strictly alone.
    """
    prof = (info.get("host") or "") + (info.get("profile") or "")
    m = re.search(r"/tmp/(lo_master_[0-9a-f]+)", prof)
    if not m:
        return False
    return not pathlib.Path("/tmp") .joinpath(m.group(1)).exists()


def _fail(msg: str, code: int = 1) -> int:
    print(f"  ABORT  {msg}")
    return code


# Warn above this, as a fraction of the currently published file. Not a gate:
# a report that genuinely grew is not a defect, and a size check that blocks a
# correct export teaches people to pass --force.
SIZE_WARN_FRACTION = 0.15


def export(out_pdf: pathlib.Path) -> bool:
    """Refresh (links, fields, indexes) and export the master to out_pdf.

    The connect/refresh/store plumbing lives in tools/uno_pdf.py since 1.3.0.
    profile_prefix stays "lo_master" so lock_is_our_own_corpse() still
    recognises this tool's own stale locks. update_links=True pulls the
    eleven linked sub-documents — the step that makes this a master export.
    """
    return uno_pdf.export_pdf(MASTER_ODM, out_pdf, update_links=True,
                              profile_prefix="lo_master")


def caption_count(pdf: pathlib.Path) -> int | None:
    """Captions figref_lint can see, or None if it could not read the PDF."""
    r = subprocess.run([sys.executable, str(FIGREF), str(pdf)],
                       capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if "captions found" in line:
            digits = "".join(c for c in line if c.isdigit())
            return int(digits) if digits else None
    return None


def lint(pdf: pathlib.Path) -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(FIGREF), str(pdf)],
                       capture_output=True, text=True)
    return r.returncode == 0, r.stdout + r.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="export and lint, but do not publish")
    ap.add_argument("--out", default=None,
                    help="publish somewhere other than docs/report/report.pdf")
    ap.add_argument("--force-unlock", action="store_true",
                    help="move an existing LibreOffice lock aside before "
                         "loading (only when nothing really has it open)")
    ap.add_argument("--no-baseline", action="store_true",
                    help="skip the caption-count comparison with the "
                         "published PDF")
    a = ap.parse_args()

    # Re-exec under a python3-uno-capable interpreter if this one
    # cannot import uno (e.g. launched by an active venv). No-op when
    # uno is already importable; the _uno_available() check below is
    # the clean fallback if no capable interpreter exists.
    uno_pdf.ensure_uno_interpreter()

    print()
    print("=" * 78)
    print("EXPORT MASTER — report.odm -> report.pdf, links and fields updated")
    print("=" * 78)

    if not MASTER_ODM.exists():
        return _fail(f"{MASTER_ODM} not found", 2)
    if _find_soffice() is None:
        return _fail("no soffice/libreoffice on PATH", 2)
    if not _uno_available():
        return _fail("python3-uno is not importable — "
                     "apt install python3-uno", 2)

    # LibreOffice returns None from loadComponentFromURL on a locked document
    # and says nothing about why, in headless mode, because the dialog it
    # wants to show has nowhere to go. Diagnosed once, on 2026-08-28, at the
    # cost of four load attempts with different property sets — so it is
    # checked by name here and reported before anything is started.
    info = read_lock()
    if info is not None:
        if lock_is_our_own_corpse(info) or a.force_unlock:
            dest = LOCK.with_name(f"{LOCK.name}.stale-{int(time.time())}")
            what = ("this tool's own" if lock_is_our_own_corpse(info)
                    else "the")
            try:
                LOCK.rename(dest)
                print(f"  cleared {what} stale lock -> {dest.name}")
                print("  (moved, not deleted: a bridge mount refuses unlink)")
            except OSError as e:
                return _fail(f"could not clear the stale lock: {e}", 2)
        else:
            print(f"  the master is LOCKED by LibreOffice:")
            print(f"      user    {info.get('username') or '?'}")
            print(f"      since   {info.get('when') or '?'}")
            print(f"      profile {info.get('host') or ''}"
                  f"{info.get('profile') or ''}")
            return _fail("close report.odm in LibreOffice and re-run. "
                         "A headless load of a locked document returns "
                         "nothing, silently.\n         If you are certain "
                         "nothing has it open, --force-unlock moves the lock "
                         "aside.", 2)

    target = pathlib.Path(a.out).resolve() if a.out else PUBLISHED
    tmp = pathlib.Path(f"/tmp/report_export_{uuid.uuid4().hex[:8]}.pdf")

    t0 = time.time()
    try:
        ok = export(tmp)
    except Exception as e:                       # noqa: BLE001
        return _fail(f"{type(e).__name__}: {e}")
    if not ok or not tmp.exists():
        return _fail("no PDF was produced")
    print(f"  wrote {tmp}  ({tmp.stat().st_size / 1e6:.1f} MB, "
          f"{time.time() - t0:.0f}s)")

    print("\n  linting the export before publishing it ...")
    passed, out = lint(tmp)
    for line in out.strip().splitlines():
        print(f"    {line}")
    if not passed:
        return _fail(f"the export did not pass figref_lint and has NOT been "
                     f"published.\n         The bad export is at {tmp} — open "
                     f"it before re-running.\n         {target} is untouched.")

    # A clean lint on a document that lost half its chapters is still clean:
    # the captions it kept are consecutive and the references it kept resolve.
    # The published PDF is the baseline that catches that.
    if not a.no_baseline and target.exists():
        was, now = caption_count(target), caption_count(tmp)
        if was and now and now < was:
            return _fail(f"the export has {now} captions against {was} in the "
                         f"published PDF — chapters are missing, which is what "
                         f"a partial link update looks like.\n         Not "
                         f"published. The export is at {tmp}.\n         "
                         f"Re-run, or pass --no-baseline if the report really "
                         f"did get shorter.")
        if was and now:
            print(f"    baseline: {now} captions against {was} published — OK")

    if a.check:
        print(f"\n  --check: passed, not published. Export at {tmp}")
        return 0

    if target.exists():
        was, now = target.stat().st_size, tmp.stat().st_size
        frac = (now - was) / was if was else 0.0
        line = (f"    size: {now / 1e6:.1f} MB against {was / 1e6:.1f} MB "
                f"published ({frac:+.0%})")
        print(line)
        if frac > SIZE_WARN_FRACTION:
            print(f"    NOTE that is more than {SIZE_WARN_FRACTION:.0%} larger. "
                  f"This file is committed to git at full size on every")
            print( "         rebuild, so a step change is worth a look before it "
                   "becomes the new baseline.")
            print( "         PDF_FILTER_DATA at the top of this file is where the "
                   "image settings live.")

    shutil.copy2(tmp, target)
    tmp.unlink(missing_ok=True)
    print(f"\n  published {target.relative_to(REPO) if target.is_relative_to(REPO) else target}")
    print("  report.pdf is now built, not hand-exported — "
          "tools/export_lag.py's note about File > Export as PDF is retired.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
