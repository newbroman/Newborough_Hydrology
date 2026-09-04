#!/usr/bin/env python3
"""
table_gen.py — generate a report table's cells from its pipeline CSV, in place.

WHY

  The pipeline-first number ledger (spec 2026-09-04, Martin's ruling: option B)
  makes the committed CSVs the source of every number a document quotes. Prose
  is checked forward from the ledger; TABLES are the bulk of the numbers, and
  for them the check becomes unnecessary if the cells are WRITTEN from the CSV
  rather than typed and then compared. This does that: for each table in
  `tools/table_configs.py` it reads the source CSV(s), renders the cells at the
  table's own precision, and rewrites the ODT's cell text — nothing else.

WHAT IT DOES, EXACTLY

  1. Opens the chapter ODT, finds `<table:table table:name="...">` by name.
     The name is an attribute LibreOffice keeps stable across edits; the
     typed "Table 1.3" is a caption field and renumbers, so it is not used.
  2. Reads the header row and REFUSES if it differs from the config's header.
     A table found by name is not yet the table the entry describes.
  3. Reads every data cell as (start, end, current text) in content.xml
     coordinates. A cell must be one <text:p> holding plain text — the shape
     every table in report9 has. A cell with spans or breaks is reported and
     the table is refused, rather than guessed at.
  4. Builds the expected grid from the CSV rows, cell by cell, and diffs.
  5. `--check`: prints the drift and exits non-zero if any cell differs.
     `--write`: replaces the differing cells through `odt_edit.edit_spans`,
     which keeps the tag sequence byte-identical, refuses an em-space, and
     rezips with mimetype stored first. `--force` rewrites every data cell,
     changed or not — the whole-table path, for proving the mechanism.
  6. Before any write the ODT is copied to `scratch/table_gen_backups/`
     (gitignored, inside the tree so the bridge can write it). ODTs are not in
     git; the backup is the undo.

  After a write, the mirror is stale until `refresh_mirrors.py` runs (pandoc
  ≥ 3.0) and the chapter should be opened in headless LibreOffice and the
  table read back — a file that rezips is not a file that opens.

USAGE
    python3 tools/table_gen.py --check                 # every configured table
    python3 tools/table_gen.py --check --id report9/Table21
    python3 tools/table_gen.py --write --id report9/Table21
    python3 tools/table_gen.py --write --force --id report9/Table21 --out /tmp/x.odt
    python3 tools/table_gen.py --check --id report9/Table21 --src /tmp/copy.odt
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-04. Phase-4 prototype:
#   one table (report9 Table 1.3) generated end to end through odt_edit.

import argparse
import csv
import pathlib
import re
import shutil
import sys
import time
from xml.sax.saxutils import escape, unescape
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from doc_paths import REPO, chapter_odt, rel      # noqa: E402
from odt_edit import edit_spans                   # noqa: E402
import table_configs                              # noqa: E402

MINUS = "−"
BACKUP_DIR = REPO / "scratch" / "table_gen_backups"

# The self-closing forms go FIRST: `[^>]*>` would otherwise swallow a `/>` and
# the lazy body would run on to the NEXT cell's closing tag.
_CELL = re.compile(
    r"<table:covered-table-cell\b[^>]*/>"
    r"|<table:table-cell\b[^>]*/>"
    r"|<table:table-cell\b[^>]*>(.*?)</table:table-cell>", re.S)
_ROW = re.compile(r"<table:table-row\b[^>]*>(.*?)</table:table-row>", re.S)
_PLAIN_P = re.compile(r"^<text:p\b[^>]*>([^<]*)</text:p>$", re.S)


# ── rendering ────────────────────────────────────────────────────────────────
def _num(s: str) -> float:
    return float(s.strip())


def render(spec: dict, row: dict, sources: dict) -> str:
    """One cell's display text from one CSV row, per the column spec."""
    if "lookup" in spec:
        alias, key_col, value_col = spec["lookup"]
        hits = [r for r in sources[alias] if r[key_col] == row[key_col]]
        if len(hits) != 1:
            raise ValueError(f"lookup {spec['lookup']}: {len(hits)} match(es) "
                             f"for {key_col}={row[key_col]!r}")
        raw = hits[0][value_col]
    else:
        raw = row[spec["col"]]

    fmt = spec.get("fmt", "text")
    if fmt == "text":
        text = raw
    elif fmt == "int":
        text = str(int(round(_num(raw))))
    elif fmt == "fixed":
        text = f"{_num(raw):.{spec['dp']}f}".replace("-", MINUS)
    elif fmt == "pvalue":
        v = _num(raw)
        text = "<0.001" if v < 0.001 else f"{v:.{spec['dp']}f}"
    elif fmt == "map":
        text = spec["map"][raw].format(**row)
    else:
        raise ValueError(f"unknown fmt {fmt!r}")

    if "re" in spec:
        pat, rep = spec["re"]
        text = re.sub(pat, rep, text)
    return text


def expected_grid(cfg: dict) -> list[list[str | None]]:
    """The table's data rows as display text; None where a covered cell
    (a continuation of a rowspan) is expected."""
    sources = {}
    for alias, path in cfg["sources"].items():
        with open(REPO / path, newline="", encoding="utf-8") as fh:
            sources[alias] = list(csv.DictReader(fh))
    rows = sources[cfg["rows"]["source"]]
    for col, val in cfg["rows"].get("filter", {}).items():
        rows = [r for r in rows if r[col] == val]

    grid = [[render(spec, r, sources) for spec in cfg["columns"]] for r in rows]
    for j, spec in enumerate(cfg["columns"]):
        if not spec.get("rowspan"):
            continue
        head = None                       # the value the current merge shows
        for i in range(len(grid)):
            if grid[i][j] == head:
                grid[i][j] = None         # a continuation row: covered cell
            else:
                head = grid[i][j]
    return grid


# ── the ODT side ─────────────────────────────────────────────────────────────
def locate_table(xml: str, name: str) -> tuple[int, int]:
    m = re.search(rf'<table:table\b[^>]*\btable:name="{re.escape(name)}"[^>]*>', xml)
    if not m:
        raise LookupError(f"no <table:table> named {name!r}")
    end = xml.find("</table:table>", m.start())
    return m.start(), end + len("</table:table>")


def read_cells(xml: str, start: int, end: int):
    """[(row_index, [(abs_start, abs_end, text) | None]), ...] — None for a
    covered cell. Offsets address the TEXT inside the cell's <text:p>."""
    if xml.count("<table:table ", start, end) > 1:
        raise ValueError("nested table")
    out = []
    for ri, rm in enumerate(_ROW.finditer(xml, start, end)):
        cells = []
        for cm in _CELL.finditer(rm.group(1)):
            if cm.group(0).startswith("<table:covered-table-cell"):
                cells.append(None)
                continue
            inner = cm.group(1)
            if inner is None:
                raise ValueError(f"row {ri} cell {len(cells)}: empty self-closing "
                                 f"cell, no text node to write into")
            pm = _PLAIN_P.match(inner)
            if not pm:
                raise ValueError(
                    f"row {ri} cell {len(cells)}: not a single plain <text:p> — "
                    f"{inner[:120]!r}")
            # absolute offsets of the text node
            base = rm.start(1) + cm.start(1) + pm.start(1)
            cells.append((base, base + len(pm.group(1)), pm.group(1)))
        out.append((ri, cells))
    return out


def plan(cfg: dict, xml: str):
    """Compare the ODT table with the CSV. Returns (cells, drift, spans_all)."""
    s, e = locate_table(xml, cfg["table_name"])
    rows = read_cells(xml, s, e)
    header = [unescape(c[2]) if c else None for c in rows[0][1]]
    if header != cfg["header"]:
        raise ValueError(f"header mismatch\n    odt: {header}\n    cfg: {cfg['header']}")
    data = rows[1:]
    grid = expected_grid(cfg)
    if len(data) != len(grid):
        raise ValueError(f"{len(data)} data row(s) in the ODT, {len(grid)} from the CSV")
    drift, spans_all, n_cells = [], [], 0
    for (ri, cells), exp_row in zip(data, grid):
        if len(cells) != len(exp_row):
            raise ValueError(f"row {ri}: {len(cells)} cell(s) in the ODT, "
                             f"{len(exp_row)} configured")
        for ci, (cell, exp) in enumerate(zip(cells, exp_row)):
            if (cell is None) != (exp is None):
                raise ValueError(f"row {ri} col {ci}: covered-cell layout differs "
                                 f"(odt covered={cell is None}, cfg covered={exp is None})")
            if cell is None:
                continue
            n_cells += 1
            new = escape(exp)
            spans_all.append((cell[0], cell[1], new))
            if cell[2] != new:
                drift.append((ri, ci, unescape(cell[2]), exp))
    return n_cells, drift, spans_all


# ── driver ───────────────────────────────────────────────────────────────────
def run(cfg: dict, write: bool, force: bool, out: pathlib.Path | None,
        src: pathlib.Path | None = None) -> int:
    src = src or chapter_odt(cfg["doc"])
    with zipfile.ZipFile(src) as z:
        xml = z.read("content.xml").decode("utf-8")
    print(f"{cfg['id']}  ({cfg['caption']})")
    try:
        n_cells, drift, spans_all = plan(cfg, xml)
    except (ValueError, LookupError) as exc:
        print(f"  REFUSED: {exc}")
        return 2
    for ri, ci, old, new in drift:
        print(f"  DRIFT row {ri} col {ci}: {old!r} -> {new!r}")
    print(f"  {n_cells} data cell(s) read; {len(drift)} differ from the CSV")

    if not write:
        return 1 if drift else 0

    spans = spans_all if force else [(a, b, t) for (a, b, t) in spans_all
                                     if xml[a:b] != t]
    if not spans:
        print("  nothing to write — the table already matches its source")
        return 0
    dst = out or src
    if dst == src:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        bak = BACKUP_DIR / f"{src.name}.{time.strftime('%Y%m%d-%H%M%S')}.bak"
        shutil.copyfile(src, bak)
        print(f"  backup: {rel(bak)}")
    ok = edit_spans(src, dst, spans, expect=len(spans))
    if not ok:
        return 2
    print(f"  wrote {len(spans)} cell(s) -> {rel(dst)}"
          + ("  (mirror now stale: run refresh_mirrors.py)" if dst == src else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="report drift, write nothing")
    g.add_argument("--write", action="store_true", help="rewrite differing cells")
    ap.add_argument("--force", action="store_true",
                    help="with --write: rewrite every data cell, changed or not")
    ap.add_argument("--id", default=None, help="one table id from table_configs")
    ap.add_argument("--out", default=None,
                    help="write to this path instead of in place (no backup taken)")
    ap.add_argument("--src", default=None,
                    help="read this ODT instead of the chapter's (for a copy under test)")
    args = ap.parse_args()

    tables = [table_configs.by_id(args.id)] if args.id else table_configs.TABLES
    if (args.out or args.src) and len(tables) != 1:
        ap.error("--out / --src need exactly one --id")
    worst = 0
    for cfg in tables:
        worst = max(worst, run(cfg, args.write, args.force,
                               pathlib.Path(args.out) if args.out else None,
                               pathlib.Path(args.src) if args.src else None))
    verdict = {0: "OK", 1: "DRIFT", 2: "REFUSED"}[worst]
    print(f"table_gen: {verdict} ({len(tables)} table(s))")
    return worst


if __name__ == "__main__":
    sys.exit(main())
