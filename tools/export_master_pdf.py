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

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-28.

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


def _find_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _uno_available() -> bool:
    try:
        import uno  # noqa: F401
        return True
    except ImportError:
        return False


def _connect(port: int, profile: pathlib.Path, soffice: str):
    """Start a private headless soffice and return (desktop, context, proc).

    A PRIVATE PROFILE, every time. Sharing the user's profile means this
    refuses to start whenever LibreOffice is already open — which, on the
    machine where the document is being edited, is most of the time.
    """
    import uno
    from com.sun.star.connection import NoConnectException

    proc = subprocess.Popen(
        [soffice, "--headless", "--norestore", "--invisible", "--nologo",
         "--nodefault", "--nolockcheck",
         f"-env:UserInstallation=file://{profile}",
         f"--accept=socket,host=127.0.0.1,port={port};urp;"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    url = (f"uno:socket,host=127.0.0.1,port={port};urp;"
           f"StarOffice.ComponentContext")
    deadline = time.time() + 120
    while True:
        try:
            ctx = resolver.resolve(url)
            break
        except NoConnectException:
            if time.time() > deadline:
                proc.terminate()
                raise TimeoutError("soffice did not accept a UNO connection "
                                   "within 120 s")
            time.sleep(0.5)
    desktop = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", ctx)
    return desktop, ctx, proc


def _prop(name, value):
    import uno
    from com.sun.star.beans import PropertyValue
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def export(out_pdf: pathlib.Path) -> bool:
    import uno  # noqa: F401
    soffice = _find_soffice()
    port = 2002 + (os.getpid() % 500)
    profile = pathlib.Path(f"/tmp/lo_master_{uuid.uuid4().hex[:8]}")
    profile.mkdir(parents=True, exist_ok=True)
    desktop = proc = None
    doc = None
    try:
        desktop, _ctx, proc = _connect(port, profile, soffice)
        src = uno.systemPathToFileUrl(str(MASTER_ODM))
        # UpdateDocMode.FULL_UPDATE = 3. Named as an integer because the
        # constant group is not always importable from python3-uno.
        load = (_prop("Hidden", True),
                _prop("UpdateDocMode", 3),
                _prop("ReadOnly", False))
        print(f"  opening {MASTER_ODM.relative_to(REPO)} ...")
        doc = desktop.loadComponentFromURL(src, "_blank", 0, load)
        if doc is None:
            return not _fail("LibreOffice returned no document")

        # 1. links — the sub-documents. Without this the master is a shell.
        try:
            doc.updateLinks()
            print("  links updated (sub-documents pulled)")
        except AttributeError:
            print("  note: this document exposes no XLinkUpdate — "
                  "not a master, or already flat")

        # 2. fields — the Figure/Table sequence numbers.
        doc.getTextFields().refresh()
        print("  text fields refreshed")

        # 3. indexes — contents and the figure index.
        idx = doc.getDocumentIndexes()
        for i in range(idx.getCount()):
            idx.getByIndex(i).update()
        print(f"  {idx.getCount()} index(es) rebuilt")

        # 4. fields again — an index rebuild moves page numbers under them.
        doc.getTextFields().refresh()
        doc.refresh()

        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        dst = uno.systemPathToFileUrl(str(out_pdf))
        print("  exporting PDF ...")
        doc.storeToURL(dst, (_prop("FilterName", "writer_pdf_Export"),))
        return True
    finally:
        try:
            if doc is not None:
                doc.close(False)
        except Exception:
            pass
        try:
            if desktop is not None:
                desktop.terminate()
        except Exception:
            pass
        if proc is not None:
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()


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

    shutil.copy2(tmp, target)
    tmp.unlink(missing_ok=True)
    print(f"\n  published {target.relative_to(REPO) if target.is_relative_to(REPO) else target}")
    print("  report.pdf is now built, not hand-exported — "
          "tools/export_lag.py's note about File > Export as PDF is retired.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
