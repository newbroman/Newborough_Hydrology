#!/usr/bin/env python3
"""
table_ref_audit.py — what does each typed "Table N" actually point at?

WHY

  The report, Paper 1 and Paper 2 each number their tables from 1, and the
  Methods Supplement cites all of them with the same bare form. Nothing in the
  corpus distinguishes them, so a renumber pass that moves "Table N" moves
  references to the OTHER documents' tables with equal enthusiasm. Worse, some
  of the existing numbers are already wrong: PIPELINE_README's table column runs
  one ahead of the report, and the Methods Supplement gives two different
  numbers for the same forecast CSV in two different chapters.

  This was found on 2026-09-19 when a dry run of the 1.4a-d promotion reported
  124 references it would move. Applying it would have preserved every existing
  error and added three to it.

WHAT IT DOES

  It does NOT decide. For each reference it lays the candidates side by side:
  the report caption at that number, the Paper 1 caption at that number, and how
  well the surrounding prose matches each. A person reads the result. The point
  is to turn "124 references, meaning unknown" into a short list of rows that
  need a judgement and a long list that plainly do not.

  Report captions are read from the ODT mirrors in document order rather than
  from tools/reference_index_table.csv, because that index records only ONE of
  the four 1.4a-d tables (it has a row for 1.4a and then jumps to 1.5) — the
  omission that let the lettered group drift outside every reference gate.

Usage:
    python3 tools/table_ref_audit.py                     # full listing
    python3 tools/table_ref_audit.py --unclear           # only rows needing a call
    python3 tools/table_ref_audit.py --out PATH
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-19.

import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

DOCS = ["report_edits/text/report8.md", "report_edits/text/report9.md",
        "report_edits/text/report10.md", "report_edits/text/report11.md",
        "report_edits/text/report12.md",
        "docs/report/text/Newborough_Methods_Supplement.md",
        "docs/report/text/Supplementary_Material.md",
        "docs/academic_summaries/text/academic_Summary.md",
        "PIPELINE_README.md", "readme.md", "notes/ledgers/SCRIPT_LEDGER.md"]

# (?![\w.]) not (?![\d.]): a pandoc simple-table row joins a "Reference table"
# column to a "21_forestry_03_....csv" column, and the loose form read that
# as a citation of Table 21. A reference number is never the start of an
# identifier.
REF = re.compile(r"(?i)\btables?\s+(\d{1,2})[a-d]?(?![\w.])")
STOP = set("the a an of and or in on at to for by with is are was were be been "
           "this that these those its it as from per each all both which "
           "table tables report paper section figure csv".split())


def _words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z_0-9]{3,}", s.lower()) if w not in STOP}


CSV = re.compile(r"([0-9a-zA-Z_]+\.csv)")
WINDOW = 200          # characters either side of a reference
TABLES_SUFFIX = "_TABLES" + ".md"   # split so docref_lint does not read
                                    # a format string as a missing document


def report_csv_map() -> dict[str, str]:
    """{csv basename: report table number} from tools/figure_table_sources.csv.

    This is the deterministic link, and it is the reason this tool works at all.
    Prose similarity cannot tell the report's Table 6 from Paper 1's Table 6 —
    both are about benchmarking, both score alike. But every table in every
    document is generated from a named pipeline CSV, and that mapping is already
    recorded per document. So the question "which Table 6?" becomes "which table
    does THIS CSV make, in THIS document?", which has one answer.
    """
    out: dict[str, set[str]] = {}
    # tools/table_configs.py FIRST: it is the maintained, per-table record of
    # which CSV fills which table, and it covers 42 of them. figure_table_sources
    # .csv carries 28 report rows and is missing, among others, the climate
    # summary and both P_flood tables — every one of which came back "in no
    # table-source map" until this was added.
    try:
        import sys as _sys
        _sys.path.insert(0, str(REPO / "tools"))
        from table_configs import TABLES as CONFIGS              # noqa: E402
    except Exception:
        CONFIGS = []
    for cfg in CONFIGS:
        if not str(cfg.get("id", "")).startswith("report"):
            continue
        m = re.search(r"Table\s+1\.(\d+)\s*(?:\(([a-d])\))?", cfg.get("caption", ""))
        if not m:
            continue
        num = m.group(1) + (m.group(2) or "")
        for src_path in cfg.get("sources", {}).values():
            out.setdefault(pathlib.Path(src_path).name, set()).add(num)
    src = REPO / "tools/figure_table_sources.csv"
    for row in csv_rows(src):
        if row.get("type") == "Table" and row.get("document", "").startswith("report"):
            # One CSV can feed more than one table — 11_forecast_pflood_threshold
            # _equations.csv is behind both 1.14 and 1.15. Keeping only the first
            # made the second read as WRONG.
            out.setdefault(pathlib.Path(row["source"]).name, set()).add(row["number"])
    return out


def paper_csv_map(n: int) -> dict[str, str]:
    """{csv basename: paper table number} from that paper's table-source manifest."""
    p = REPO / "docs" / "papers" / f"paper_{n}" / f"PAPER{n}{TABLES_SUFFIX}"
    if not p.exists():
        return {}
    out: dict[str, set[str]] = {}
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*`?([^|`]+?)`?\s*\|",
                         p.read_text(encoding="utf-8"), re.M):
        out.setdefault(pathlib.Path(m.group(2).strip()).name, set()).add(m.group(1))
    return out



_OUT_INDEX = None


def csv_exists(name: str) -> bool:
    """Is this CSV basename anywhere under outputs/?

    A registry row naming a file that was never produced is a worse fault than a
    wrong number, and it reads identically until you look: PIPELINE_README lists
    the specific-yield table's source as 17_wtf_01_sy_table.csv, which does not
    exist — the file is 17_wtf_01_sy_estimates.csv.
    """
    global _OUT_INDEX
    if _OUT_INDEX is None:
        _OUT_INDEX = {q.name for q in (REPO / "outputs").rglob("*.csv")}
    return name in _OUT_INDEX


def csv_rows(path: pathlib.Path):
    import csv as _csv
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(_csv.DictReader(fh))


def report_index() -> dict[str, str]:
    """{'4a': caption, '5': caption, ...} in document order, from the mirrors."""
    idx = {}
    for doc in ("report_edits/text/report9.md", "report_edits/text/report10.md"):
        p = REPO / doc
        if not p.exists():
            continue
        for m in re.finditer(r"\*\*Table ([0-9]*\.?[0-9]*[a-d]?)[:.]\s*\*\*(.{0,110})",
                             p.read_text(encoding="utf-8")):
            key = m.group(1).split(".")[-1] or m.group(1)
            idx.setdefault(key, m.group(2).strip())
    return idx


def paper_index(n: int) -> dict[str, str]:
    p = REPO / f"docs/papers/paper_{n}/text/Paper{n}.md"
    if not p.exists():
        return {}
    return {m.group(1): m.group(2).strip() for m in
            re.finditer(r"\*\*Table (\d+)[.:]\*\*(.{0,110})", p.read_text(encoding="utf-8"))}


# ── registry tables ───────────────────────────────────────────────────────────
# PIPELINE_README and the Methods Supplement both carry tables whose whole job is
# to say which pipeline output becomes which numbered table. Those rows are the
# highest-value references in the corpus and the easiest to get wrong from prose
# context, because a character window reaches into the row above. They are read
# FIELD BY FIELD instead: the row is split into cells, the "Table N" is taken
# from its own cell and the CSV from its own cell, and nothing outside the row
# is consulted.
#
# Two formats. PIPELINE_README writes pipe tables. The Methods Supplement mirror
# is pandoc's SIMPLE table: a rule line of dash runs sets the column spans and
# every row is sliced at those offsets. Parsing either one with a regex over the
# whole line is what produced six false WRONG verdicts on the first run.

RULE = re.compile(r"^\s*(-{3,}(?:\s+-{3,})+)\s*$")
CELL_REF = re.compile(r"(?i)\btables?\s+(\d{1,2})([a-d])?(?![\w.])")


def _spans(rule_line: str):
    return [(m.start(), m.end()) for m in re.finditer(r"-{3,}", rule_line)]


def _simple_tables(text: str):
    """Yield [[cell, ...], ...] for each pandoc simple table in `text`."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if not RULE.match(lines[i]):
            i += 1
            continue
        spans = _spans(lines[i])
        rows, j = [], i + 1
        while j < len(lines) and lines[j].strip() and not RULE.match(lines[j]):
            rows.append([lines[j][a:b].strip() for a, b in spans])
            j += 1
        if len(rows) > 1:
            yield rows
        i = j + 1


def _pipe_tables(text: str):
    """Yield [[cell, ...], ...] for each markdown pipe table in `text`."""
    rows, out = [], []
    for line in text.split("\n"):
        if line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                rows.append(cells)
        else:
            if len(rows) > 1:
                out.append(rows)
            rows = []
    if len(rows) > 1:
        out.append(rows)
    return out


def registry_rows(text: str):
    """(label, cited_number, letter, csv_basename, row_text) for every registry row.

    A registry row is one that carries a "Table N" in one cell and a .csv name in
    another. Rows with neither, or with the number and the CSV in the same cell,
    are left to the prose pass.
    """
    for rows in list(_pipe_tables(text)) + list(_simple_tables(text)):
        for row in rows[1:]:
            num_cell = csv_cell = None
            for cell in row:
                if num_cell is None and CELL_REF.search(cell):
                    num_cell = cell
                elif csv_cell is None and CSV.search(cell):
                    csv_cell = cell
            if num_cell is None or csv_cell is None:
                continue
            m = CELL_REF.search(num_cell)
            yield (num_cell, m.group(1), m.group(2) or "",
                   pathlib.Path(CSV.search(csv_cell).group(1)).name,
                   " | ".join(c for c in row if c))
            # NOT truncated here: the disclaimer that says a row is not a table
            # mapping sits at the END of a long description cell, and capping
            # the row at 150 characters hid it from the check that reads it.


def _row_text(text: str, a: int, b: int):
    """The registry-row key for a reference, or None if it is not in a table."""
    ls = text.rfind("\n", 0, a) + 1
    le = text.find("\n", b)
    le = len(text) if le < 0 else le
    line = text[ls:le]
    if line.lstrip().startswith("|"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
    elif "  " in line.strip():
        cells = [c for c in re.split(r"\s{2,}", line.strip()) if c]
    else:
        return None
    return " | ".join(c for c in cells if c)


def _context(text: str, a: int, b: int) -> str:
    """The evidence window for one reference.

    A fixed +/- 200 characters is wrong inside a markdown table: both the
    Methods Supplement and PIPELINE_README list their tables as one row each,
    "| Table 8 | ... | `some_output.csv` |", so a fixed window reaches into the
    NEIGHBOURING row and pairs a reference with the row above's CSV. The first
    run read 17 references as WRONG on exactly that mistake. Inside a table the
    row IS the context; outside one, the surrounding prose is.
    """
    ls = text.rfind("\n", 0, a) + 1
    le = text.find("\n", b)
    le = len(text) if le < 0 else le
    line = text[ls:le]
    if line.lstrip().startswith("|"):
        return line
    if re.match(r"\s*[-*\u2022]\s", line):
        # A list of "- **Table 8** --- ..., source: *x.csv*." bullets is a
        # registry in prose clothing. A character window spanning two bullets
        # pairs a reference with the neighbouring bullet's CSV, which is how
        # the supplement's (correct) Table 10 bullet read as WRONG.
        return line
    return text[max(0, a - WINDOW):b + WINDOW].replace("\n", " ")


TABLE_SOURCES: dict[str, set[str]] = {}


def verdict(doc: str, cited: str, ctx: str, rmap, p1map, p2map):
    """(tag, note). The CSV link decides where it can; scoping decides the rest."""
    # A report chapter citing a bare "Table N" means the report's table. There is
    # no other numbering in scope inside the report's own prose.
    in_report = doc.startswith("report_edits/")
    names = [pathlib.Path(c).name for c in CSV.findall(ctx)]
    hits = []
    for nm in names:
        for label, mp in (("report", rmap), ("paper1", p1map), ("paper2", p2map)):
            if nm in mp:
                hits.append((label, mp[nm], nm))   # mp[nm] is a SET of numbers
    if not hits:
        # A REFERENCE has no CSV and is not supposed to have one. It names a
        # table; the TABLE carries the provenance. "NO CSV" was auditing the
        # wrong object and made 60 sound references look unresolved. So resolve
        # the number against the table inventory and quote the table's own
        # source — tools/table_provenance_lint.py is what guarantees every table
        # has one.
        if in_report:
            return "REPORT-SCOPED", ""
        nums = TABLE_SOURCES.get(cited) or TABLE_SOURCES.get(cited + "a")
        if nums:
            return "RESOLVED", f"report Table {cited} <- {sorted(nums)[0]}"
        return "NO SUCH TABLE", f"the report has no Table {cited}"
    exact = [h for h in hits if cited in {n.split(".")[-1] for n in h[1]}]
    if exact:
        label, nums, nm = exact[0]
        if label == "report" or in_report:
            return "OK", f"{nm} -> report {'/'.join(sorted(nums))}"
        return f"PAPER {label[-1]}", f"{nm} -> {label} {'/'.join(sorted(nums))} (do not renumber)"
    rep = [h for h in hits if h[0] == "report"]
    if rep:
        label, nums, nm = rep[0]
        return "WRONG", f"{nm} is report {'/'.join(sorted(nums))}, cited as {cited}"
    label, nums, nm = hits[0]
    return f"PAPER {label[-1]}?", f"{nm} -> {label} {'/'.join(sorted(nums))}, cited as {cited}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unclear", action="store_true",
                    help="only rows the CSV link cannot settle")
    ap.add_argument("--faults", action="store_true",
                    help="only WRONG and PAPER rows — the ones that must not be "
                         "renumbered blind")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rmap, p1map, p2map = report_csv_map(), paper_csv_map(1), paper_csv_map(2)
    # number -> {csv}: the inverse of rmap, so a reference can be resolved
    # through the table it names rather than through whatever text sits near it.
    for nm, nums in rmap.items():
        for num in nums:
            TABLE_SOURCES.setdefault(num.split(".")[-1], set()).add(nm)
    rep, p1 = report_index(), paper_index(1)
    lines = [f"# Table-reference audit ({__version__})", "",
             f"CSV->table maps: report {len(rmap)}, Paper 1 {len(p1map)}, "
             f"Paper 2 {len(p2map)}", ""]
    tally = {}
    for doc in DOCS:
        p = REPO / doc
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        rows = []
        seen = set()
        # The registry pass first: these rows state the mapping outright, so a
        # fault here is a fault in the record itself, not in someone's prose.
        for num_cell, cited, letter, nm, rowtext in registry_rows(text):
            seen.add(rowtext)
            if "not itself a numbered report table" in rowtext:
                # The row says outright that this output does not become a
                # numbered table. Reading the "Table 14" in its prose as a claim
                # about `nm` inverts what the row is for.
                tally["DISCLAIMED"] = tally.get("DISCLAIMED", 0) + 1
                continue
            nums = rmap.get(nm)
            if nums is None:
                for lbl, mp in (("paper1", p1map), ("paper2", p2map)):
                    if nm in mp:
                        tag = (f"PAPER {lbl[-1]}" if cited in mp[nm]
                               else f"PAPER {lbl[-1]}?")
                        note = f"{nm} -> {lbl} {'/'.join(sorted(mp[nm]))}"
                        break
                else:
                    if not csv_exists(nm):
                        tag = "NO SUCH CSV"
                        note = (f"{nm} is not under outputs/ — the row names a "
                                f"file that does not exist")
                    else:
                        tag, note = "REGISTRY NO MAP", (
                            f"{nm} exists but no table-source record claims it")
            elif cited in {n.split(".")[-1] for n in nums}:
                tag, note = "OK", f"registry: {nm} -> report {'/'.join(sorted(nums))}"
            else:
                tag = "WRONG"
                note = (f"registry: {nm} is report {'/'.join(sorted(nums))}, "
                        f"row says Table {cited}{letter}")
            tally[tag] = tally.get(tag, 0) + 1
            if args.faults and not (tag.startswith("WRONG") or tag.startswith("PAPER")
                                    or tag.startswith("REGISTRY")):
                continue
            if args.unclear and tag != "NO CSV":
                continue
            rows.append((cited + letter, tag, note, rowtext[:150]))
        for m in REF.finditer(text):
            cited = m.group(1)
            ctx = _context(text, m.start(), m.end())
            row = _row_text(text, m.start(), m.end())
            if row is not None and row in seen:
                continue          # already judged, field by field
            if row is not None and "not itself a numbered report table" in row:
                # A registry row whose number and CSV share one cell never
                # reaches the field-aware pass; the disclaimer still governs.
                tally["DISCLAIMED"] = tally.get("DISCLAIMED", 0) + 1
                continue
            tag, note = verdict(doc, cited, ctx, rmap, p1map, p2map)
            tally[tag] = tally.get(tag, 0) + 1
            if args.faults and not (tag.startswith("WRONG") or tag.startswith("PAPER")):
                continue
            if args.unclear and tag != "NO CSV":
                continue
            near = text[max(0, m.start() - 70):m.end() + 25].replace("\n", " ")
            rows.append((cited, tag, note, near))
        if rows:
            lines.append(f"\n## {doc}  ({len(rows)})")
            for cited, tag, note, near in rows:
                lines.append(f"\n- **Table {cited}**  `{tag}`  {note}")
                lines.append(f"  - ...{near.strip()}...")
    lines.append("\n---\n" + "   ".join(f"{k}: {v}" for k, v in sorted(tally.items())))
    out = "\n".join(lines)
    if args.out:
        pathlib.Path(args.out).write_text(out, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(out)
    print("  " + "   ".join(f"{k}: {v}" for k, v in sorted(tally.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
