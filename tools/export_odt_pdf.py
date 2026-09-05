#!/usr/bin/env python3
"""
export_odt_pdf — refresh (TOC + sequence fields) and export flat ODTs to PDF.

The refreshing counterpart of `soffice --convert-to pdf` for published PDFs
(W137 / D-135). Drives LibreOffice through UNO so a document's table-of-contents
page numbers and Figure/Table sequence fields are recomputed before the PDF is
written — which `--convert-to` does not do. Shares its plumbing with
export_master_pdf.py via tools/uno_pdf.py, so the two PDF paths cannot drift.

USAGE
    python3 tools/export_odt_pdf.py SRC1.odt OUT1.pdf [SRC2.odt OUT2.pdf ...]

    All pairs are processed in ONE soffice session. Each OUT is written directly
    (storeToURL names the output, unlike --convert-to). Existing OUT files are
    overwritten.

RUN IT WITH A UNO-CAPABLE INTERPRETER. python3-uno installs into the system
dist-packages; a venv built without --system-site-packages cannot import it.
build_pdfs.sh finds such an interpreter and falls back to --convert-to (with a
loud warning) when none is available.

EXIT
    0  every pair exported
    1  at least one pair failed
    2  the environment is missing something (no soffice, or no python3-uno)
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-05. W137 / D-135.

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import uno_pdf                                          # noqa: E402


def main(argv: list[str]) -> int:
    args = argv[1:]
    if not args or len(args) % 2 != 0:
        print(__doc__)
        print("  ERROR: expected an even number of SRC OUT arguments")
        return 2

    if uno_pdf.find_soffice() is None:
        print("  ABORT  no soffice/libreoffice on PATH")
        return 2
    if not uno_pdf.uno_available():
        print("  ABORT  python3-uno is not importable — apt install python3-uno "
              "(or run with an interpreter that can 'import uno')")
        return 2

    pairs = []
    for i in range(0, len(args), 2):
        src = pathlib.Path(args[i])
        out = pathlib.Path(args[i + 1])
        if not src.exists():
            print(f"  ABORT  source not found: {src}")
            return 2
        pairs.append((src, out))

    results = uno_pdf.export_many(pairs, update_links=False)

    ok = [o for _, o, good in results if good]
    bad = [o for _, o, good in results if not good]
    print()
    for src, out, good in results:
        print(f"  {'OK   ' if good else 'FAIL '} {out}")
    print(f"  {len(ok)} exported, {len(bad)} failed")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
