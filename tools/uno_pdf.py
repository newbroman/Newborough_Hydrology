#!/usr/bin/env python3
"""
uno_pdf — shared LibreOffice/UNO plumbing for building published PDFs.

One refresh routine, used by both PDF paths, so they cannot drift (W137 / D-135):

  * tools/export_master_pdf.py  — report.pdf from the report.odm MASTER
                                  (update_links=True: pull the linked chapters)
  * tools/export_odt_pdf.py     — every other published PDF from a flat ODT

WHY THIS IS NOT `soffice --convert-to pdf`.

  `--convert-to` renders a document's STORED table-of-contents page numbers and
  sequence fields (Figure/Table numbers) as-is; it does not recompute them. After
  any text edit the published PDF's TOC page numbers and figure numbers can be
  stale even though the entries are correct (W137). Driving LibreOffice through
  UNO lets us refresh fields and rebuild indexes first, in this order:

      1. load with UpdateDocMode = FULL_UPDATE
      2. (master only) XLinkUpdate.updateLinks() — pull the sub-documents
      3. TextFields.refresh()   — recompute the sequence fields
      4. every DocumentIndex .update() — rebuild the TOC and figure/table indexes
      5. TextFields.refresh() again — an index rebuild moves page numbers under fields

PRODUCER. UNO export uses the SAME local LibreOffice as `--convert-to`, so a
natively-built PDF carries the publishing machine's /Producer unchanged
(artefact_lint Check C); a bridge-built PDF still fails it. PDFs remain
native-only — this module does not change that.

REQUIRES python3-uno (apt install python3-uno) and libreoffice. `uno_available()`
and `find_soffice()` are provided so callers can check by name and fall back.
"""
from __future__ import annotations

__version__ = "1.1.1"  # Hollingham (2026) — 2026-09-06. Shim fix:
#   ensure_uno_interpreter() no longer skips a candidate whose realpath
#   matches this interpreter — a venv python symlinks to the system python,
#   so that skip wrongly rejected /usr/bin/python3 and the re-exec never fired.
# v1.1.0  # Hollingham (2026) — 2026-09-06. Adds
#   ensure_uno_interpreter(): re-exec under a python3-uno-capable
#   interpreter when the launching one (e.g. an active venv) cannot import
#   uno — the report.pdf rebuild trap. Guarded against re-exec loops.
# v1.0.0  # Hollingham (2026) — 2026-09-05. Extracted from
#   export_master_pdf.py 1.2.0 (W137 / D-135): the connect / refresh / store
#   plumbing, unchanged, so the master export and the new per-ODT export share
#   one routine. The master's report.pdf output is unchanged by the extraction.

import os
import pathlib
import subprocess
import time
import uuid


# PDF EXPORT SETTINGS ARE PINNED, BECAUSE THE DEFAULTS ARE NOT THE HAND EXPORT'S.
# Quality 80 and a 300 DPI ceiling match Martin's hand export on the L14 and
# config.FIG_TARGET_PRINT_DPI; API defaults (Quality 90, lossless) produced a
# file ~26% larger (export_master_pdf.py history, W126). Callers may override.
DEFAULT_PDF_FILTER_DATA = {
    "UseLosslessCompression": False,   # JPEG, not PNG-in-PDF
    "Quality": 80,                     # matches the hand export on the L14
    "ReduceImageResolution": True,
    "MaxImageResolution": 300,         # matches config.FIG_TARGET_PRINT_DPI
    "ExportBookmarks": True,           # headings, for navigation
    "UseTaggedPDF": True,              # accessibility; a journal will want it
}


def find_soffice() -> str | None:
    import shutil
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    return None


def uno_available() -> bool:
    try:
        import uno  # noqa: F401
        return True
    except ImportError:
        return False


def ensure_uno_interpreter(candidates=("python3", "/usr/bin/python3",
                                       "python3.12", "/usr/bin/python3.12")):
    """If `uno` cannot be imported in THIS interpreter, re-exec the running
    script under one that can. python3-uno installs into the SYSTEM interpreter's
    dist-packages; a venv built without --system-site-packages cannot see it, so
    `python tool.py` from an active venv fails to import uno even on a machine
    that has it (the 2026-09-06 report.pdf rebuild trap). Rather than fail, find a
    UNO-capable interpreter -- the same search build_pdfs.sh uses -- and hand off.

    A one-shot guard (NRG_UNO_REEXEC) prevents a loop: if the chosen interpreter
    still cannot import uno, control returns and the caller's own uno_available()
    check reports it cleanly. Returns True if uno is importable in this process,
    False if no capable interpreter was found (no re-exec happened)."""
    if uno_available():
        return True
    if os.environ.get("NRG_UNO_REEXEC") == "1":
        return False                       # already handed off once; do not loop
    import shutil
    import sys
    # Re-exec to the first candidate whose OWN `import uno` succeeds. Do NOT skip a
    # candidate whose realpath equals this interpreter's: a venv python is typically
    # a symlink to the system python, so the binaries share a realpath, yet the venv
    # invocation cannot see python3-uno (no system-site-packages) while a DIRECT
    # /usr/bin/python3 invocation can. The subprocess `import uno` test is the real
    # discriminator; the NRG_UNO_REEXEC guard above prevents any loop. (The realpath
    # skip here was the 2026-09-06 bug that left report.pdf unbuildable from a venv.)
    for cand in candidates:
        path = shutil.which(cand)
        if not path:
            continue
        try:
            ok = subprocess.run([path, "-c", "import uno"],
                                capture_output=True).returncode == 0
        except OSError:
            ok = False
        if ok:
            print(f"  (re-exec under {path} for python3-uno)")
            os.execve(path, [path] + sys.argv,
                      dict(os.environ, NRG_UNO_REEXEC="1"))   # never returns
    return False


def prop(name, value):
    from com.sun.star.beans import PropertyValue
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def filter_data(overrides: dict | None = None):
    d = dict(DEFAULT_PDF_FILTER_DATA)
    if overrides:
        d.update(overrides)
    return tuple(prop(k, v) for k, v in d.items())


def connect(port: int, profile: pathlib.Path, soffice: str):
    """Start a PRIVATE headless soffice and return (desktop, ctx, proc).

    A private profile every time: sharing the user's profile means this refuses
    to start whenever LibreOffice is already open — which, on the machine where
    the document is edited, is most of the time.
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


def refresh_document(doc, update_links: bool = False, verbose: bool = True):
    """The refresh sequence: (links) -> fields -> indexes -> fields.

    Returns the number of indexes rebuilt. Mirrors export_master_pdf.py 1.2.0
    exactly; update_links is master-only (a flat ODT exposes no XLinkUpdate).
    """
    if update_links:
        try:
            doc.updateLinks()
            if verbose:
                print("  links updated (sub-documents pulled)")
        except AttributeError:
            if verbose:
                print("  note: this document exposes no XLinkUpdate — "
                      "not a master, or already flat")
    doc.getTextFields().refresh()
    if verbose:
        print("  text fields refreshed")
    idx = doc.getDocumentIndexes()
    for i in range(idx.getCount()):
        idx.getByIndex(i).update()
    if verbose:
        print(f"  {idx.getCount()} index(es) rebuilt")
    doc.getTextFields().refresh()
    doc.refresh()
    return idx.getCount()


def _new_session(profile_prefix: str):
    soffice = find_soffice()
    if soffice is None:
        raise RuntimeError("no soffice/libreoffice on PATH")
    port = 2002 + (os.getpid() % 500)
    profile = pathlib.Path(f"/tmp/{profile_prefix}_{uuid.uuid4().hex[:8]}")
    profile.mkdir(parents=True, exist_ok=True)
    return connect(port, profile, soffice)


def _load_refresh_store(desktop, src_odt: pathlib.Path, out_pdf: pathlib.Path,
                        update_links: bool, pdf_overrides: dict | None,
                        verbose: bool) -> bool:
    import uno
    doc = None
    try:
        src = uno.systemPathToFileUrl(str(pathlib.Path(src_odt).resolve()))
        # UpdateDocMode.FULL_UPDATE = 3 (named as an int; the constant group is
        # not always importable from python3-uno).
        load = (prop("Hidden", True),
                prop("UpdateDocMode", 3),
                prop("ReadOnly", False))
        if verbose:
            print(f"  opening {src_odt} ...")
        doc = desktop.loadComponentFromURL(src, "_blank", 0, load)
        if doc is None:
            print(f"  ABORT  LibreOffice returned no document for {src_odt} "
                  "(locked, or not a document)")
            return False
        refresh_document(doc, update_links=update_links, verbose=verbose)
        out_pdf = pathlib.Path(out_pdf)
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        dst = uno.systemPathToFileUrl(str(out_pdf.resolve()))
        if verbose:
            print(f"  exporting {out_pdf.name} ...")
        doc.storeToURL(dst, (prop("FilterName", "writer_pdf_Export"),
                             prop("FilterData", uno.Any(
                                 "[]com.sun.star.beans.PropertyValue",
                                 filter_data(pdf_overrides)))))
        return True
    finally:
        try:
            if doc is not None:
                doc.close(False)
        except Exception:
            pass


def _teardown(desktop, proc):
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


def export_pdf(src_odt, out_pdf, *, update_links: bool = False,
               pdf_overrides: dict | None = None,
               profile_prefix: str = "lo_uno", verbose: bool = True) -> bool:
    """Refresh and export ONE document in its own private soffice session."""
    desktop = proc = None
    try:
        desktop, _ctx, proc = _new_session(profile_prefix)
        return _load_refresh_store(desktop, pathlib.Path(src_odt),
                                   pathlib.Path(out_pdf), update_links,
                                   pdf_overrides, verbose)
    finally:
        _teardown(desktop, proc)


def export_many(pairs, *, update_links: bool = False,
                pdf_overrides: dict | None = None,
                profile_prefix: str = "lo_uno", verbose: bool = True):
    """Refresh and export several (src_odt, out_pdf) pairs in ONE session.

    Returns a list of (src_odt, out_pdf, ok). Much cheaper than one soffice
    launch per file across a document map.
    """
    results = []
    desktop = proc = None
    try:
        desktop, _ctx, proc = _new_session(profile_prefix)
        for src_odt, out_pdf in pairs:
            try:
                ok = _load_refresh_store(desktop, pathlib.Path(src_odt),
                                         pathlib.Path(out_pdf), update_links,
                                         pdf_overrides, verbose)
            except Exception as e:                      # noqa: BLE001
                print(f"  ABORT  {type(e).__name__} on {src_odt}: {e}")
                ok = False
            results.append((str(src_odt), str(out_pdf), ok))
    finally:
        _teardown(desktop, proc)
    return results
