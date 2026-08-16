#!/usr/bin/env python3
"""
review_citations.py
===================
Walk the proposed rows of tools/citation_index.csv one at a time, show each in
its live context, and record a yes/no.

WHY A HUMAN HAS TO DO THIS
    The index makes citation checking exact — but only for rows somebody has
    confirmed. The builder proposes a row wherever a published value appears
    verbatim with an identifying token nearby, and in a corpus this dense with
    per-well tables that is right roughly half the time: "1.75" is a cluster β₂
    mean in one sentence and a variance inflation factor in the next. Deciding
    which is which means reading the sentence. This tool makes that as fast as
    it can be, and nothing more.

WHAT THE ANSWERS MEAN
    y  this number IS that quantity      -> status=confirmed, checked exactly
    n  coincidence, different quantity   -> status=rejected, never re-proposed
    s  skip for now                      -> stays proposed, offered again
    b  go back one
    q  save and quit (progress is kept)

Answers are written back on quit and at the end, so a half-finished pass is
never lost. Re-running offers only what is still proposed.

Usage:
    python3 tools/review_citations.py
    python3 tools/review_citations.py --source 03_03      # headline table first
    python3 tools/review_citations.py --document report9
"""
from __future__ import annotations

import argparse
import csv
import glob
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "tools" / "citation_index.csv"
CONTEXT = 300           # characters of live context shown either side
FIND_WORDS = 6          # words before the number in the first find-string try
FIND_WORDS_MAX = 14     # ...extended until the phrase is unique in the document

G, Y, R, C, B, N = ("\033[0;32m", "\033[1;33m", "\033[0;31m",
                    "\033[0;36m", "\033[1m", "\033[0m")


def load_notes() -> dict[str, str]:
    """key -> its note text, so the reviewer can see what the value MEANS."""
    notes: dict[str, str] = {}
    for p in glob.glob(str(REPO / "outputs/**/*report_numbers*.csv"), recursive=True):
        try:
            with open(p, encoding="utf8") as fh:
                for row in csv.DictReader(fh):
                    vals = list(row.values())
                    notes.setdefault(vals[0], (row.get("note") or "").strip())
        except Exception:
            pass
    return notes


def load_docs() -> dict[str, str]:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cite_check", REPO / "tools" / "cite_check.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.load_documents()


def locate(text: str, row: dict) -> int:
    """Find the occurrence this row refers to, using the stored context."""
    quoted = row["quoted"]
    before = (row.get("before") or "")[-30:].strip()
    best = -1
    for m in re.finditer(re.escape(quoted), text):
        if best < 0:
            best = m.start()
        if before and before in " ".join(text[max(0, m.start() - 120):m.start()].split()):
            return m.start()
    return best


_RULE = re.compile(r"-{3,}")          # markdown table rules: ---- ------ ...
# Header-ish tokens to drop from a row label: anything starting with a digit or
# bracket (2080s, "(m)"), single characters ("n"), and anything carrying
# sub/superscripts (β₁, R²). Two-character tokens are KEPT — cluster ids are
# exactly two characters and are the most useful part of a row label.
_HDR_JUNK = re.compile(r"^[\d(]|^.$|[₀-₉⁰-⁹]")
_NUMERIC = re.compile(r"^[-−–—\d.,()%]+$")        # incl. unicode minus signs
_ROWID = re.compile(r"(?i)^(c[1-5]|(ceh|nw|wmc|lis|fe|d|t)\d+[a-z]?)$")


def _clean(tok: str) -> str:
    return re.sub(r"[|*_`#>\\]+", "", tok)


def _row_label(raw: str) -> str:
    """The label of the table row a number sits in — the only part of a table
    that is worth typing into a Find box.

    Everything before it is rule dashes and column headers ("---- Cluster β₁ β₂
    ΔMSL5 2050s (m)"), which match nothing in the ODT. Header-ish tokens are
    dropped — anything starting with a digit or bracket, anything one or two
    characters long, and anything carrying sub/superscripts — and the last few
    words that survive are the label.
    """
    toks = [_clean(w) for w in raw.split()]
    words = [w for w in toks
             if w and not _HDR_JUNK.search(w) and not _NUMERIC.match(w)]
    if not words:
        return ""
    # A row label starts at its identifier — "C1 Lake Edge", "C2 Dune" — so cut
    # back to the last one rather than blindly taking the final few words, which
    # would drag in the tail of the row above.
    for j in range(len(words) - 1, -1, -1):
        if _ROWID.match(words[j]):
            return " ".join(words[j:j + 4])
    return " ".join(words[-3:])


def find_string(text: str, pos: int, quoted: str) -> tuple[str, bool]:
    """A phrase you can paste into LibreOffice's Find box to reach this number.

    The context shown above comes from the markdown mirror, which is not what
    you are editing, so the reviewer needs a handle on the ODT itself.

    Prose: the words immediately before the number, lengthened until unique.
    Tables: the row label (see _row_label) — never the header run.
    """
    raw = text[max(0, pos - 400):pos]
    before = text[max(0, pos - 200):pos]
    after = text[pos:pos + 160]
    # A number in prose has words around it; a number in a table row has other
    # numbers around it. Counting both sides catches space-aligned tables that
    # carry no rule near the cell — which the "Cluster Label n β₁ β₂" table did.
    numeric = len(re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?\b", before + " " + after))
    in_table = bool(_RULE.search(before)) or numeric >= 5
    if in_table:
        label = _row_label(raw)
        if label:
            return label, text.count(label) == 1

    words = [w for w in (_clean(x) for x in raw.split()) if w]
    for k in range(FIND_WORDS, FIND_WORDS_MAX + 1):
        if k > len(words):
            break
        phrase = " ".join(words[-k:]).strip()
        if sum(c.isalpha() for c in phrase) < 6:
            continue
        if text.count(phrase) == 1:
            return phrase, True
    phrase = " ".join(words[-FIND_WORDS_MAX:]) if words else ""
    return " ".join(phrase.split()), False


def table_span(text: str, pos: int) -> tuple[int, int] | None:
    """The extent of the table block a number sits in, or None if it is prose.

    Some tables in these documents ARE a rendering of a pipeline CSV — the
    cluster mechanistic table is 03_03 laid out in five rows. Every cell is a
    citation, and asking about them one at a time is pointless: the judgement
    is "this table renders that CSV", made once.

    The span is found by walking outward in blocks while the numeric density
    stays table-like, which works whether or not the mirror emitted rule lines
    near the cell.
    """
    step, thresh = 120, 4          # numbers per block to still count as table
    def dense(a: int, b: int) -> bool:
        return len(re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?\b",
                              text[max(0, a):b])) >= thresh

    if not (dense(pos - step, pos) or dense(pos, pos + step)):
        return None
    start = pos
    while start > 0 and dense(start - step, start):
        start -= step
    end = pos
    while end < len(text) and dense(end, end + step):
        end += step
    return (max(0, start), min(len(text), end)) if end - start > step else None


def nearest_heading(text: str, pos: int) -> str:
    """The markdown heading this citation sits under — where to look in the ODT."""
    head = ""
    for m in re.finditer(r"^#{1,6}\s+(.+)$", text[:pos], flags=re.M):
        head = m.group(1)
    head = re.sub(r"\{#[^}]*\}", "", head)      # pandoc anchors {#anchor-293}
    head = re.sub(r"\[\]|[*_`\[\]]+", "", head)
    return " ".join(head.split())[:90]


def show(row: dict, text: str, note: str, i: int, total: int,
         prior: str | None = None) -> None:
    pos = locate(text, row)
    print("\n" + "=" * 78)
    print(f"{B}[{i}/{total}]{N}  {C}{row['key']}{N}   = {B}{row['quoted']}{N}"
          f"   ({row.get('confidence','?')} confidence)")
    print(f"        source: {row['source_csv'].split('/')[-1]}")
    print(f"        in:     {row['document']}")
    if note:
        print(f"        {Y}means:{N}  {note[:180]}")
    if prior:
        print(f"        {G}already {prior} for this key elsewhere{N} — "
              "same quantity, another place it is cited")
    print("-" * 78)
    if pos < 0:
        print(f"  {R}(string no longer present — the prose changed; answer n){N}")
        return
    pre = " ".join(text[max(0, pos - CONTEXT):pos].split())
    post = " ".join(text[pos + len(row["quoted"]):pos + len(row["quoted"]) + CONTEXT].split())
    print(f"  ...{pre}  {B}>>>{row['quoted']}<<<{N}  {post}...")

    head = nearest_heading(text, pos)
    phrase, unique = find_string(text, pos, row["quoted"])
    print("-" * 78)
    if head:
        print(f"  {C}section:{N} {head}")
    if phrase:
        flag = "" if unique else f"  {Y}(not unique — check which occurrence){N}"
        print(f"  {C}find in the document:{N}{flag}")
        print(f"    {B}{phrase}{N}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=None, help="substring filter on source CSV")
    ap.add_argument("--document", default=None, help="substring filter on document")
    ap.add_argument("--confidence", default=None, choices=["high", "low"])
    args = ap.parse_args()

    if not INDEX.exists():
        print("No index — run tools/build_citation_index.py first.")
        return 1
    with open(INDEX, encoding="utf8") as fh:
        rdr = csv.DictReader(fh)
        fields = rdr.fieldnames or []
        rows = list(rdr)

    docs = load_docs()
    notes = load_notes()

    todo = [r for r in rows if r.get("status") == "proposed"
            and (not args.source or args.source in r["source_csv"])
            and (not args.document or args.document in r["document"])
            and (not args.confidence or r.get("confidence") == args.confidence)]

    # A key confirmed once has been JUDGED once. Every other row for that key is
    # the same quantity cited somewhere else — a location, not a decision. Offer
    # to inherit those up front so the walk contains only genuinely new calls.
    # Rejections are deliberately NOT inherited: a number can be a coincidence
    # in one document and a real citation in another, and inheriting a rejection
    # would hide the real one silently, whereas a wrong inherited confirmation
    # surfaces later as a spurious DRIFTED.
    confirmed_keys = {r["key"] for r in rows if r.get("status") == "confirmed"}
    inherit = [r for r in todo if r["key"] in confirmed_keys]
    if inherit:
        where = ", ".join(sorted({r["document"].split("/")[-1] for r in inherit}))
        print(f"\n{Y}{len(inherit)} row(s){N} cite a value you have already "
              f"confirmed elsewhere ({where}).")
        try:
            ans = input(f"  {B}Apply those confirmations now? [Y/n]: {N}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            ans = "n"
        if ans in {"", "y"}:
            for r in inherit:
                r["status"] = "confirmed"
            todo = [r for r in todo if r["key"] not in confirmed_keys]
            print(f"  {G}{len(inherit)} inherited{N} — not shown below.")
            with open(INDEX, "w", newline="", encoding="utf8") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader(); w.writerows(rows)

    done = sum(1 for r in rows if r.get("status") in {"confirmed", "rejected"})
    print(f"{len(rows)} index rows: {done} decided, {len(todo)} to review here.")
    if not todo:
        print("Nothing to do.")
        return 0
    print(f"{Y}y{N}=yes  {Y}n{N}=coincidence  {Y}s{N}=skip  "
          f"{Y}b{N}=back  {Y}q{N}=save and quit")

    def save() -> None:
        with open(INDEX, "w", newline="", encoding="utf8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    def decided_elsewhere(key: str, exclude: dict):
        for r in rows:
            if r is not exclude and r["key"] == key and \
                    r.get("status") in {"confirmed", "rejected"}:
                return r["status"]
        return None

    def siblings(key: str, exclude: dict) -> list:
        """Other still-proposed rows for the SAME key: the same quantity cited
        somewhere else. The judgement has been made; only the location differs,
        so there is nothing further to decide — just more places to record."""
        return [r for r in rows
                if r is not exclude and r["key"] == key
                and r.get("status") == "proposed"]

    i = 0
    yes = no = 0
    shown = -1
    while 0 <= i < len(todo):
        row = todo[i]
        if row.get("status") != "proposed":       # settled by a bulk apply
            i += 1
            continue
        if shown != i:                            # redraw only on a new row
            show(row, docs.get(row["document"], ""), notes.get(row["key"], ""),
                 i + 1, len(todo), decided_elsewhere(row["key"], row))
            shown = i
        try:
            ans = input(f"  {B}confirm this citation? [y/n/s/b/q]: {N}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if ans in {"y", "n"}:
            status = "confirmed" if ans == "y" else "rejected"
            row["status"] = status
            if ans == "y":
                yes += 1
            else:
                no += 1
            # A table that renders a CSV: offer the whole block at once.
            text_ = docs.get(row["document"], "")
            pos_ = locate(text_, row)
            span = table_span(text_, pos_) if pos_ >= 0 else None
            if span:
                block = [r for r in rows
                         if r is not row and r.get("status") == "proposed"
                         and r["document"] == row["document"]
                         and span[0] <= locate(text_, r) <= span[1]]
                if len(block) >= 2:
                    srcs = sorted({r["source_csv"].split("/")[-1] for r in block}
                                  | {row["source_csv"].split("/")[-1]})
                    print(f"  {Y}this sits in a table block holding "
                          f"{len(block) + 1} indexed values{N} "
                          f"(from {', '.join(srcs)})")
                    try:
                        whole = input(f"  {B}apply '{status}' to the whole "
                                      f"table? [Y/n]: {N}").strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        whole = "n"
                    if whole in {"", "y"}:
                        for r in block:
                            r["status"] = status
                        if ans == "y":
                            yes += len(block)
                        else:
                            no += len(block)
                        print(f"  {G}applied to {len(block)} more in this "
                              f"table{N}")

            sib = siblings(row["key"], row)
            if sib:
                where = ", ".join(sorted({r["document"].split("/")[-1] for r in sib}))
                print(f"  {Y}{len(sib)} more occurrence(s) of this same value{N} "
                      f"in {where}")
                try:
                    same = input(f"  {B}apply '{status}' to those too? "
                                 f"[Y/n]: {N}").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    same = "n"
                if same in {"", "y"}:
                    for r in sib:
                        r["status"] = status
                    if ans == "y":
                        yes += len(sib)
                    else:
                        no += len(sib)
                    print(f"  {G}applied to {len(sib)} more{N}")
            i += 1
        elif ans == "s":
            i += 1
        elif ans == "b":
            i = max(0, i - 1)
        elif ans == "q":
            break
        else:
            print("  (y, n, s, b or q)")

    save()
    print(f"\n{G}saved{N} — {yes} confirmed, {no} rejected this session.")
    remaining = sum(1 for r in rows if r.get("status") == "proposed")
    print(f"{remaining} row(s) still proposed across the whole index.")
    print("Confirmed rows are now checked exactly by tools/cite_check.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
