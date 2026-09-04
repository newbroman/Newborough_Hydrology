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
     coordinates. A cell must be one <text:p> holding plain text, or text
     spread across <text:span> runs (what LibreOffice leaves after a value
     is re-typed): the display text is the runs joined, a write goes into
     the first non-empty run and blanks the rest. A cell holding any other
     element is reported and the table is refused, rather than guessed at.
     A cell LibreOffice typed as a number (`office:value-type="float"
     office:value="6"`) is read with that attribute, and a write keeps the
     attribute equal to the text it shows.
  4. Builds the expected grid from the CSV rows, cell by cell, and diffs. A
     `transpose` table turns the grid: each CSV row is a table COLUMN and
     each column spec a table ROW, labelled by the spec's `label`.
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
    python3 tools/table_gen.py --write --id ms/Table12     # versioned: writes _v1_9_(N+1)
"""
from __future__ import annotations

__version__ = "1.5.1"  # Hollingham (2026) — 2026-09-04. Withdraws fmt "sum"
#   (added and reverted same day): D-126 keeps the config data-only and has the
#   SCRIPT emit derived quantities, so report9 Table 1.20's climate + far-field
#   column is now Script 25's committed climate_plus_far_field_mm_yr rendered
#   with plain "fixed", not a config-side sum. See CHANGELOG_delta 2026-09-04x.
# v1.5.0  # (superseded) added fmt "sum"; withdrawn per D-126.
# v1.4.0  # Hollingham (2026) — 2026-09-04. Transposed tables,
#   numeric cells, chained `re`. (1) `transpose: True` on a table whose CSV is
#   one row per displayed COLUMN (Table 1.17: one row per metric, the table
#   shows metrics across and statistics down): each column spec becomes a
#   table row with its `label` in the stub column, each surviving CSV row a
#   table column, and the header is asserted as before. (2) A cell LibreOffice
#   has typed as a number carries `office:value="6"` beside its text (Table
#   1.18's counts). LibreOffice displays the TEXT and drops the attribute on
#   its next save (measured on a mini ODT, 2026-09-04), so a stale value is
#   harmless to the reader — but a file this tool has written must not carry
#   a number that contradicts the number it shows. The attribute is read with
#   the cell, reported as drift when it disagrees, and rewritten with the
#   text; because that changes a TAG, the write goes through odt_edit with
#   allow_tag_change and its own stricter guard here: the tag sequence must be
#   byte-identical once `office:value="…"` is masked. A non-numeric text into
#   a numeric cell refuses. (3) `re` may be a LIST of [pattern, replacement]
#   pairs, applied in order, for a label needing two glyph substitutions.
#
# v1.3.0  # Hollingham (2026) — 2026-09-04. Cell vocabulary.
#   A data cell may now be a <text:p> whose content is text nodes and
#   <text:span> tags ONLY — the shape LibreOffice leaves behind after a cell is
#   re-typed (a "−0.04" run followed by a span holding "6", or a value wrapped
#   in nested emphasis/rsid spans). Its display text is the text nodes joined;
#   a write goes into the first non-empty text node and BLANKS the others, so
#   the tag sequence is byte-identical and odt_edit's guard still holds. Any
#   other element inside a cell (a line break, a tab, a frame) still refuses.
#   Column specs gain `when` / `unless` ({col: value | [values]}) with `else`
#   (default "—") for a cell the table shows only on some rows — Table 1.1's
#   P/PET ratio on complete years, Table 1.4c's OLS Sy on uncorrected rows —
#   and `scale` on fixed (multiply before rendering) for a column the table
#   displays with the opposite sign convention to its CSV (Table 1.2).
#
# v1.2.0  # Hollingham (2026) — 2026-09-04. Versioned documents.
#   `doc` may now be a repo-relative GLOB ("docs/report/Newborough_Methods_
#   Supplement_v*.odt"): the newest file by refresh_mirrors._version_key is
#   read — the same resolver the mirrors and doc_version_sync use, so the three
#   can never disagree about which file is live — and a --write goes to the
#   BUMPED filename (_v1_9_104 -> _v1_9_105), never in place, per the
#   versioned-document rule; the prior file stays on disk and no backup is
#   taken. After such a write run doc_version_sync.py (the in-text version
#   string) and refresh_mirrors.py --only (the mirror). `lookup` also accepts
#   a dict form with a constant `where` — {"source": a, "key": k, "col": c,
#   "where": {col: value}} — for a table whose columns are scenarios of one
#   long CSV (Table 73's 2050s / 2080s).
#
# v1.1.0  # Hollingham (2026) — 2026-09-04. Second batch (ten
#   more report9 tables). Formats gain `template` (str.format over the row
#   with NUMERIC specs — "{lo:+.3f}" — which covers "[lo, hi]", "v ± se",
#   "1819 m" and "1,044" without a formatter each), `ci`, `stars`, and `sign`
#   on fixed; fixed/pvalue/int pass a non-numeric cell through unchanged
#   ("30 / 66", "—", a CSV that already says "<0.001"); a row filter value
#   may be a list (membership); `order` sorts rows by a declared value list.
#
# v1.0.0  # Hollingham (2026) — 2026-09-04. Phase-4 prototype:
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
from refresh_mirrors import _version_key, _VER    # noqa: E402
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
# A cell whose paragraph holds only text and <text:span> tags: the runs
# LibreOffice leaves behind when a value is re-typed. Anything else refuses.
_SPAN_P = re.compile(r"^<text:p\b[^>]*>((?:[^<]|<text:span\b[^>]*>|</text:span>)*)</text:p>$", re.S)
_EMPTY_P = re.compile(r"^<text:p\b[^>]*/>$")
_VALUE_ATTR = re.compile(r'\boffice:value="([^"]*)"')


# ── rendering ────────────────────────────────────────────────────────────────
def _num(s: str) -> float:
    return float(s.strip().replace(",", ""))


def _is_num(s: str) -> bool:
    try:
        _num(s)
        return True
    except (ValueError, AttributeError):
        return False


class _Field(str):
    """A CSV cell that formats as a NUMBER when given a numeric spec.

    str.format cannot apply ".3f" to the string "0.1234"; this can, so a
    template like "[{lo:+.3f}, {hi:+.3f}]" or "{d:,.0f} m" is pure config.
    Negatives render with the Unicode minus, as every table in the corpus does.
    An empty spec ({name}) is the raw text, unchanged.
    """
    def __format__(self, spec):
        if spec:
            return format(_num(self), spec).replace("-", MINUS)
        return str(self)


def _fields(row: dict) -> dict:
    return {k: _Field(v) for k, v in row.items()}


def render(spec: dict, row: dict, sources: dict) -> str:
    """One cell's display text from one CSV row, per the column spec.

    fixed / pvalue / int pass a NON-NUMERIC cell through unchanged: some
    sources carry "30 / 66", "—" or an already-rendered "<0.001", and the
    table shows exactly that.
    """
    fmt = spec.get("fmt", "text")
    for key, want in (("when", True), ("unless", False)):
        for col, val in spec.get(key, {}).items():
            keep = set(val) if isinstance(val, (list, tuple)) else {val}
            if (row[col] in keep) != want:
                return spec.get("else", "—")
    if "lookup" in spec:
        lk = spec["lookup"]
        if isinstance(lk, dict):
            alias, key_col, value_col = lk["source"], lk["key"], lk["col"]
            where = lk.get("where", {})
        else:
            (alias, key_col, value_col), where = lk, {}
        hits = [r for r in sources[alias] if r[key_col] == row[key_col]
                and all(r[c] == v for c, v in where.items())]
        if len(hits) != 1:
            raise ValueError(f"lookup {lk}: {len(hits)} match(es) "
                             f"for {key_col}={row[key_col]!r}")
        raw = hits[0][value_col]
    elif fmt in ("template", "ci"):
        raw = None
    else:
        raw = row[spec["col"]]

    sign = "+" if spec.get("sign") else ""
    if fmt == "text":
        text = raw
    elif fmt == "int":
        text = str(int(round(_num(raw)))) if _is_num(raw) else raw
    elif fmt == "fixed":
        text = (f"{_num(raw) * spec.get('scale', 1):{sign}.{spec['dp']}f}"
                .replace("-", MINUS) if _is_num(raw) else raw)
    elif fmt == "pvalue":
        if _is_num(raw):
            v = _num(raw)
            text = "<0.001" if v < 0.001 else f"{v:.{spec['dp']}f}"
        else:
            text = raw
    elif fmt == "stars":
        v = _num(raw)
        text = ("***" if v < 0.001 else "**" if v < 0.01
                else "*" if v < 0.05 else "ns")
    elif fmt == "map":
        text = spec["map"][raw].format(**_fields(row))
    elif fmt == "template":
        text = spec["template"].format(**_fields(row))
    elif fmt == "ci":
        lo, hi = (row[c] for c in spec["cols"])
        d = spec["dp"]
        text = (f"[{_num(lo):{sign}.{d}f}, {_num(hi):{sign}.{d}f}]"
                .replace("-", MINUS))
    else:
        raise ValueError(f"unknown fmt {fmt!r}")

    if "re" in spec:
        pairs = spec["re"]
        if pairs and isinstance(pairs[0], str):   # a single [pattern, replacement]
            pairs = [pairs]
        for pat, rep in pairs:
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
        keep = set(val) if isinstance(val, (list, tuple)) else {val}
        rows = [r for r in rows if r[col] in keep]
    order = cfg["rows"].get("order")
    if order:                              # stable: ties keep CSV order
        col, values = order["col"], list(order["values"])
        missing = sorted({r[col] for r in rows} - set(values))
        if missing:
            raise ValueError(f"order: {col} value(s) {missing} not in the declared list")
        rows = sorted(rows, key=lambda r: values.index(r[col]))

    grid = [[render(spec, r, sources) for spec in cfg["columns"]] for r in rows]
    if cfg.get("transpose"):
        # one table ROW per column spec, its `label` in the stub column; one
        # table COLUMN per CSV row. A vertical merge has no meaning here.
        if any(spec.get("rowspan") for spec in cfg["columns"]):
            raise ValueError("transpose and rowspan do not combine")
        missing = [i for i, spec in enumerate(cfg["columns"]) if "label" not in spec]
        if missing:
            raise ValueError(f"transpose: column spec(s) {missing} carry no `label`")
        return [[spec["label"]] + [row_cells[i] for row_cells in grid]
                for i, spec in enumerate(cfg["columns"])]
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


def _cell_nodes(inner: str, base: int):
    """The text nodes of a span-only cell paragraph as [(abs_start, abs_end,
    text)], in document order, including the empty positions between tags."""
    pm = _SPAN_P.match(inner)
    if not pm:
        return None
    body, off = pm.group(1), base + pm.start(1)
    nodes, pos = [], 0
    for tag in re.finditer(r"<[^>]+>", body):
        nodes.append((off + pos, off + tag.start(), body[pos:tag.start()]))
        pos = tag.end()
    nodes.append((off + pos, off + len(body), body[pos:]))
    return nodes


def read_cells(xml: str, start: int, end: int):
    """[(row_index, [cell | None]), ...] — None for a covered cell.

    A cell is (abs_start, abs_end, text, extras, value): the text node a write
    goes into, the cell's DISPLAY text (every text node joined, XML-escaped as
    in the file), the other non-empty text nodes [(abs_start, abs_end)] that
    a write must blank so the display text is the written text alone, and the
    cell's `office:value` attribute as (abs_start, abs_end, current) when
    LibreOffice has typed the cell as a number, else None. A plain cell has no
    extras. Offsets address text inside the cell's <text:p>, or the attribute
    value inside the <table:table-cell> tag. An empty self-closing <text:p/>
    reads as "" with offsets -1: it can be left blank but never written into
    (that would change the tag sequence)."""
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
            base = rm.start(1) + cm.start(1)
            open_tag = cm.group(0)[:cm.group(0).index(">") + 1]
            am = _VALUE_ATTR.search(open_tag)
            value = ((rm.start(1) + cm.start() + am.start(1),
                      rm.start(1) + cm.start() + am.end(1), am.group(1))
                     if am else None)
            if _EMPTY_P.match(inner):      # <text:p .../>: reads as "", takes no text
                cells.append((-1, -1, "", [], value))
                continue
            pm = _PLAIN_P.match(inner)
            if pm:
                a = base + pm.start(1)
                cells.append((a, a + len(pm.group(1)), pm.group(1), [], value))
                continue
            nodes = _cell_nodes(inner, base)
            if nodes is None:
                raise ValueError(
                    f"row {ri} cell {len(cells)}: not text and <text:span> runs "
                    f"in one <text:p> — {inner[:120]!r}")
            filled = [n for n in nodes if n[2]]
            if filled:
                primary, extras = filled[0], [(a, b) for a, b, _ in filled[1:]]
            else:                          # all empty: write inside the spans
                depth = 0
                for tag in re.finditer(r"<[^>]+>", inner):
                    if tag.group(0).startswith("</"):
                        break
                    depth += 1
                primary, extras = nodes[max(depth - 1, 0)], []
            cells.append((primary[0], primary[1],
                          "".join(n[2] for n in nodes), extras, value))
        out.append((ri, cells))
    return out


def _attr_value(text: str) -> str:
    """The `office:value` form of a rendered cell: ASCII minus, no separators.
    LibreOffice writes the number the cell shows; so does this."""
    raw = text.replace(MINUS, "-").replace(",", "").strip()
    if not _is_num(raw):
        raise ValueError(f"{text!r} is not a number, and the cell is typed as one")
    return raw


def plan(cfg: dict, xml: str):
    """Compare the ODT table with the CSV.

    Returns (cells, drift, spans_all, attr_starts): the data-cell count, the
    differing cells, one (write group, differs) per cell, and the start
    offsets of the office:value attribute writes among those groups."""
    s, e = locate_table(xml, cfg["table_name"])
    rows = read_cells(xml, s, e)
    header = [unescape(c[2]) if c else None for c in rows[0][1]]
    if header != cfg["header"]:
        raise ValueError(f"header mismatch\n    odt: {header}\n    cfg: {cfg['header']}")
    data = rows[1:]
    grid = expected_grid(cfg)
    if len(data) != len(grid):
        raise ValueError(f"{len(data)} data row(s) in the ODT, {len(grid)} from the CSV")
    drift, writes_all, n_cells, attr_starts = [], [], 0, set()
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
            differs = cell[2] != new
            if cell[0] < 0:                # an empty self-closing paragraph
                if new:
                    raise ValueError(f"row {ri} col {ci}: the cell is an empty "
                                     f"self-closing <text:p/> and {exp!r} needs a text node")
                writes_all.append(([], False))
                continue
            # one write group per cell: the value, plus a blank for every
            # other text node the cell's display text was spread across
            group = [(cell[0], cell[1], new)] + [(a, b, "") for a, b in cell[3]]
            if differs:
                drift.append((ri, ci, unescape(cell[2]), exp))
            if cell[4] is not None:        # a numeric cell: office:value = the text
                try:
                    want = _attr_value(exp)
                except ValueError as exc:
                    raise ValueError(f"row {ri} col {ci}: {exc}") from None
                group.append((cell[4][0], cell[4][1], want))
                attr_starts.add(cell[4][0])
                if cell[4][2] != want:
                    differs = True
                    drift.append((ri, ci, f'office:value="{cell[4][2]}"',
                                  f'office:value="{want}"'))
            writes_all.append((group, differs))
    return n_cells, drift, writes_all, attr_starts


def _tags_masked(xml: str) -> list[str]:
    """The tag sequence with every office:value blanked — what must be
    byte-identical across a write that follows a numeric cell's attribute."""
    return re.findall(r"<[^>]+>", _VALUE_ATTR.sub('office:value=""', xml))


# ── documents ────────────────────────────────────────────────────────────────
def resolve_doc(doc) -> tuple[pathlib.Path, bool]:
    """(live ODT, versioned?) for a config `doc`.

    An int is a report chapter (report_edits/odt/reportN.odt, edited in place).
    A string is a repo-relative glob for a VERSIONED document; the live file is
    the highest version by refresh_mirrors._version_key — `ls | tail` sorts
    v1_9 after v1_18 and once produced a confident report against a stale file.
    """
    if isinstance(doc, int):
        return chapter_odt(doc), False
    matches = sorted(REPO.glob(doc))
    if not matches:
        raise LookupError(f"no document matches {doc!r}")
    return max(matches, key=_version_key), True


def bumped(path: pathlib.Path) -> pathlib.Path:
    """The next version's filename: _v1_9_104.odt -> _v1_9_105.odt."""
    m = _VER.search(path.name)
    if not m:
        raise ValueError(f"{path.name} carries no _vN version suffix")
    parts = m.group(1).split("_")
    parts[-1] = str(int(parts[-1]) + 1)
    return path.with_name(path.name[:m.start()] + "_v" + "_".join(parts) + ".odt")


# ── driver ───────────────────────────────────────────────────────────────────
def run(cfg: dict, write: bool, force: bool, out: pathlib.Path | None,
        src: pathlib.Path | None = None) -> int:
    versioned = False
    if src is None:
        try:
            src, versioned = resolve_doc(cfg["doc"])
        except LookupError as exc:
            print(f"{cfg['id']}\n  REFUSED: {exc}")
            return 2
    with zipfile.ZipFile(src) as z:
        xml = z.read("content.xml").decode("utf-8")
    print(f"{cfg['id']}  ({cfg['caption']})  <- {rel(src)}")
    try:
        n_cells, drift, spans_all, attr_starts = plan(cfg, xml)
    except (ValueError, LookupError) as exc:
        print(f"  REFUSED: {exc}")
        return 2
    for ri, ci, old, new in drift:
        print(f"  DRIFT row {ri} col {ci}: {old!r} -> {new!r}")
    n_differ = sum(1 for _, d in spans_all if d)     # cells, not drift lines
    print(f"  {n_cells} data cell(s) read; {n_differ} differ from the CSV")

    if not write:
        return 1 if drift else 0

    spans = [w for group, differs in spans_all if (differs or force)
             for w in group]
    if not spans:
        print("  nothing to write — the table already matches its source")
        return 0
    dst = out or (bumped(src) if versioned else src)
    if versioned and dst.exists():
        print(f"  REFUSED: {rel(dst)} already exists — the next version is taken")
        return 2
    if dst == src:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        bak = BACKUP_DIR / f"{src.name}.{time.strftime('%Y%m%d-%H%M%S')}.bak"
        shutil.copyfile(src, bak)
        print(f"  backup: {rel(bak)}")
    # A numeric cell's office:value lives in a TAG. Rewriting it is the one
    # tag change this tool makes, so it is allowed through odt_edit only
    # after proving here that nothing else in the tag sequence moves.
    allow = any(a in attr_starts for a, _, _ in spans)
    if allow:
        trial = xml
        for a, b, new in sorted(spans, reverse=True):
            trial = trial[:a] + new + trial[b:]
        if _tags_masked(trial) != _tags_masked(xml):
            print("  REFUSED: a write would change the tag sequence beyond "
                  "office:value attributes")
            return 2
    ok = edit_spans(src, dst, spans, expect=len(spans), allow_tag_change=allow)
    if not ok:
        return 2
    n_changed = sum(1 for _, d in spans_all if d or force)
    print(f"  wrote {n_changed} cell(s) ({len(spans)} replacement(s)) -> {rel(dst)}")
    if dst == src:
        print("  (mirror now stale: run refresh_mirrors.py --only)")
    elif versioned and out is None:
        print("  (new version: run doc_version_sync.py for the in-text version "
              "string, then refresh_mirrors.py --only for the mirror)")
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
