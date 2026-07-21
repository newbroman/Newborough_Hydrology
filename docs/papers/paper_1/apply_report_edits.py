#!/usr/bin/env python3
"""
apply_report_edits.py — interactive, validated application of report edits to an ODT.

Walks a JSON edit manifest one edit at a time. For each edit it locates the target in
the live document, shows you a before/after preview, and asks whether to apply it. The
SCRIPT does the placement; you only read and decide. Rejected edits and edits that
cannot be located are collected and listed at the end for review. Nothing is written
until the walk completes, and the source file is never overwritten.

Backend: odfpy (no headless LibreOffice needed). Find/replace is cross-span aware, so
text that LibreOffice has fragmented across <text:span> runs is still matched; the
replacement inherits the formatting of the run where the match begins (lossless for the
plain-body numeric edits this is built for). For edits that straddle differently
formatted runs, prefer a replace_paragraph edit.

Manifest schema (see HANDOVER_scripted_report_edits.md):
  edit types: find_replace | replace_paragraph | insert_paragraph_after |
              insert_paragraph_before
  common:      id, section, type, trace, note
  find_replace: find, replace_, [expect_count=1], [anchor_before], [anchor_after]
  replace_paragraph: anchor_contains, replacement
  insert_*:    anchor_contains, text, [heading], [style]

Usage:
  python3 apply_report_edits.py --doc report.odt --edits edits_5p7p5.json
  python3 apply_report_edits.py --doc report.odt --edits edits_5p7p5.json --out report_edited.odt
  python3 apply_report_edits.py --doc report.odt --edits edits_5p7p5.json --yes-all   # non-interactive

Version: 1.5.0 (2026-06-27)
  1.5.0 — colour: diff-style colouring of previews (removed text red, new text green),
          coloured y/n/q choices and status markers, and a coloured end summary.
          Auto-enabled on a TTY; disabled when piped, under NO_COLOR, or with
          --no-color. The .log.txt is always plain text.
  1.4.0 — terminal word-wrap: previews wrap to the terminal width with a hanging
          indent. Content being approved (FIND/REPLACE, NEW, inserted heading/text/
          caption) is shown in full; orientation text (existing paragraph, anchor,
          match context) is capped at a few lines. Replaces the old hard 160-char trim.
  1.3.2 — fix: style-existence check now inspects only style:style elements
          (doc.styles.getElementsByType(Style)). The old scan of every styles-section
          child called getAttribute("name") on name-less children (default styles,
          configs), which raises in odfpy 1.4.x — crashing on real reports the first
          time a heading/caption run-style was created. No behaviour change otherwise.
  1.3.1 — doc: a `heading` spec is a bold run-in heading = body text, bold (the report's
          level-4-and-below convention); the tool only ever makes body paragraphs, so it
          cannot produce a styled Heading element. No behaviour change.
  1.3.0 — table policy: table edits go through find_replace only (edits the run in
          place, preserving cell formatting incl. 10pt). Removed the user-facing
          {"fontsize"} spec field added in 1.2.0 — captions keep their internal 10pt.
  1.2.0 — font sizing: captions render at 10pt (italic body, bold-italic label).
  1.1.0 — caption support: paragraph specs gain a {"caption","label"} kind (italic
          caption, bold-italic label) for figure/table captions, available in
          inserts (paragraphs list or top-level caption/label) and in
          replace_paragraph (replacement_spec).
  1.0.0 — initial: find_replace, replace_paragraph, insert_paragraph_after/before;
          interactive y/n/q walk; validation gate; new-file output.
"""
from __future__ import annotations
import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

from odf.opendocument import load
from odf.text import P, Span, H

__version__ = "1.5.0"

TEXT_NODE = 3
PARA_TAGS = {"p", "h"}


class C:
    """ANSI colours, blanked unless enabled (TTY + not NO_COLOR + not --no-color)."""
    RESET = BOLD = DIM = RED = GREEN = YELLOW = CYAN = ""


def _init_colour(enable):
    if enable:
        C.RESET, C.BOLD, C.DIM = "\033[0m", "\033[1m", "\033[2m"
        C.RED, C.GREEN, C.YELLOW, C.CYAN = (
            "\033[31m", "\033[32m", "\033[33m", "\033[36m")
    else:
        C.RESET = C.BOLD = C.DIM = C.RED = C.GREEN = C.YELLOW = C.CYAN = ""


def _c(text, colour):
    return f"{colour}{text}{C.RESET}" if colour else text


# ── document helpers ─────────────────────────────────────────────────────────
def iter_paragraphs(doc):
    """Yield every text:p / text:h element in document order."""
    out = []

    def walk(node):
        for c in node.childNodes:
            if getattr(c, "qname", None) and c.qname[1] in PARA_TAGS:
                out.append(c)
            if c.nodeType != TEXT_NODE:
                walk(c)
    walk(doc.text)
    return out


def text_nodes(p):
    """Ordered list of Text (nodeType==3) descendants of a paragraph."""
    out = []

    def walk(node):
        for c in node.childNodes:
            if c.nodeType == TEXT_NODE:
                out.append(c)
            else:
                walk(c)
    walk(p)
    return out


def flat(p):
    return "".join(n.data for n in text_nodes(p))


def _ensure_run_style(doc, bold=False, italic=False, size=None):
    """Return the name of a reusable text style for the given weight/slant/size,
    creating it once. Used for headings (bold), captions (italic body,
    bold-italic label, 10pt), and any spec that sets an explicit fontsize."""
    from odf.style import Style, TextProperties
    tag = "ARE" + ("B" if bold else "") + ("I" if italic else "")
    tag += ("S" + size.replace("pt", "") if size else "") + "run"
    # Inspect only style:style elements — a real document's <office:styles> also
    # holds name-less children (default styles, configs) whose getAttribute("name")
    # raises in some odfpy versions.
    for s in doc.styles.getElementsByType(Style):
        try:
            if s.getAttribute("name") == tag:
                return tag
        except Exception:
            continue
    props = {}
    if bold:
        props["fontweight"] = "bold"
    if italic:
        props["fontstyle"] = "italic"
    if size:
        props["fontsize"] = size
    st = Style(name=tag, family="text")
    st.addElement(TextProperties(**props))
    doc.styles.addElement(st)
    return tag


def fill_paragraph(doc, p, spec):
    """Clear paragraph p and (re)build its runs from a paragraph spec.

    spec is a dict with exactly one content key:
      {"text": "..."}                            → plain body (document default size)
      {"heading": "..."}                          → bold run-in heading = body text,
                                                    bold (level-4-and-below convention;
                                                    never a styled Heading element)
      {"caption": "...", "label": "Figure 60."}   → 10pt italic caption,
                                                    label bold-italic 10pt

    Table cells are NOT rebuilt here — table edits go through find_replace, which
    edits the run in place and preserves the cell's formatting (incl. 10pt).
    """
    for c in list(p.childNodes):
        if c.nodeType == TEXT_NODE:
            c.data = ""
        else:
            p.removeChild(c)
    if "heading" in spec:
        p.addElement(Span(stylename=_ensure_run_style(doc, bold=True),
                          text=spec["heading"]))
    elif "caption" in spec:
        label = (spec.get("label") or "").strip()
        if label:
            p.addElement(Span(stylename=_ensure_run_style(
                doc, bold=True, italic=True, size="10pt"), text=label + " "))
        p.addElement(Span(stylename=_ensure_run_style(doc, italic=True, size="10pt"),
                          text=spec["caption"]))
    else:
        p.addText(spec.get("text", ""))


def replace_one_occurrence(p, find, repl, occ_index=0):
    """Replace the occ_index-th occurrence of `find` inside paragraph `p`,
    editing the underlying text nodes; cross-span aware, formatting at the
    match start preserved. Returns True on success."""
    nodes = text_nodes(p)
    s = "".join(n.data for n in nodes)
    start = -1
    for _ in range(occ_index + 1):
        start = s.find(find, start + 1)
        if start < 0:
            return False
    end = start + len(find)
    pos = 0
    spans = []
    for n in nodes:
        spans.append((pos, pos + len(n.data), n))
        pos += len(n.data)
    placed = False
    for lo, hi, n in spans:
        if hi <= start or lo >= end:
            continue
        a = max(lo, start) - lo
        b = min(hi, end) - lo
        prefix, suffix = n.data[:a], n.data[b:]
        if not placed:
            n.data = prefix + repl + suffix
            placed = True
        else:
            n.data = prefix + suffix
    return placed


# ── match resolution ─────────────────────────────────────────────────────────
def resolve_find(doc, edit):
    """Return (status, matches) for a find_replace edit.
    matches = list of (paragraph, occ_index_within_paragraph). status in
    {'ok','none','count'}."""
    find = edit["find"]
    ab = edit.get("anchor_before", "")
    af = edit.get("anchor_after", "")
    want = edit.get("expect_count", 1)
    matches = []
    for p in iter_paragraphs(doc):
        s = flat(p)
        i = -1
        occ = 0
        while True:
            i = s.find(find, i + 1)
            if i < 0:
                break
            ok = True
            if ab and s[max(0, i - len(ab)):i] != ab:
                ok = False
            if af and s[i + len(find):i + len(find) + len(af)] != af:
                ok = False
            if ok:
                matches.append((p, occ))
            occ += 1
    if not matches:
        return "none", matches
    if len(matches) != want:
        return "count", matches
    return "ok", matches


def resolve_paragraph(doc, anchor):
    """Return list of paragraphs whose flattened text contains `anchor`."""
    return [p for p in iter_paragraphs(doc) if anchor in flat(p)]


# ── previews ─────────────────────────────────────────────────────────────────
def _term_width():
    import shutil
    return max(40, shutil.get_terminal_size((100, 24)).columns)


def _wrap(prefix, text, full=True, max_lines=3, colour=None):
    """Wrap `text` after `prefix` to the terminal width, continuation lines
    hanging-indented to align under the value. `full=False` caps orientation
    text (existing paragraph, anchor, context) at max_lines with an ellipsis.
    `colour` (an ANSI code) tints the whole block — applied after wrapping so
    width maths are unaffected."""
    import textwrap
    text = " ".join(str(text).split())
    body = textwrap.fill(text, width=_term_width(),
                         initial_indent=prefix,
                         subsequent_indent=" " * len(prefix)) or prefix.rstrip()
    if not full:
        lines = body.split("\n")
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1].rstrip() + " …"
            body = "\n".join(lines)
    return _c(body, colour) if colour else body


def preview(edit, status, matches):
    t = edit["type"]
    lines = [f"  id: {_c(edit['id'], C.BOLD)}    §{edit.get('section','?')}    [{t}]",
             _c(f"  trace: {edit.get('trace','—')}", C.DIM)]
    if edit.get("note"):
        lines.append(_wrap("  note: ", edit["note"], colour=C.DIM))
    if t == "find_replace":
        if status == "ok":
            p, occ = matches[0]
            s = flat(p)
            i = -1
            for _ in range(occ + 1):
                i = s.find(edit["find"], i + 1)
            ctx = (s[max(0, i - 50):i] + "⟦" + edit["find"] + "⟧"
                   + s[i + len(edit['find']):i + len(edit['find']) + 50])
            lines.append(_wrap("  context: ", "…" + ctx + "…", full=False, colour=C.DIM))
        lines.append(_wrap("  FIND:    ", edit["find"], colour=C.RED))
        lines.append(_wrap("  REPLACE: ", edit.get("replace_", ""), colour=C.GREEN))
    elif t == "replace_paragraph":
        if status == "ok":
            lines.append(_wrap("  OLD: ", flat(matches[0]), full=False, colour=C.RED))
        spec = edit.get("replacement_spec")
        if spec and "caption" in spec:
            lines.append(_wrap("  NEW (caption): ",
                               f"{spec.get('label','')} {spec['caption']}", colour=C.GREEN))
        elif spec and "heading" in spec:
            lines.append(_wrap("  NEW (heading): ", spec["heading"], colour=C.GREEN))
        else:
            lines.append(_wrap("  NEW: ", edit.get("replacement", ""), colour=C.GREEN))
    elif t in ("insert_paragraph_after", "insert_paragraph_before"):
        where = "AFTER" if t.endswith("after") else "BEFORE"
        if status == "ok":
            lines.append(_wrap(f"  ANCHOR ({where}): ", flat(matches[0]),
                               full=False, colour=C.DIM))
        for spec in _insert_specs(edit):
            if "heading" in spec:
                lines.append(_wrap("  + HEADING: ", spec["heading"], colour=C.GREEN))
            elif "caption" in spec:
                lines.append(_wrap("  + CAPTION: ",
                                   f"{spec.get('label','')} {spec['caption']}", colour=C.GREEN))
            else:
                lines.append(_wrap("  + TEXT:    ", spec.get("text", ""), colour=C.GREEN))
    return "\n".join(lines)


# ── apply ────────────────────────────────────────────────────────────────────
def apply_find_replace(edit, matches):
    # apply right-to-left within a paragraph so earlier offsets stay valid
    by_par = {}
    for p, occ in matches:
        by_par.setdefault(id(p), (p, []))[1].append(occ)
    done = 0
    for p, occs in by_par.values():
        for occ in sorted(occs, reverse=True):
            if replace_one_occurrence(p, edit["find"], edit.get("replace_", ""), occ):
                done += 1
    return done == len(matches)


def _new_paragraph(doc, spec, style=None):
    p = P(stylename=style) if style else P()
    fill_paragraph(doc, p, spec)
    return p


def _insert_specs(edit):
    """Normalise an insert edit into an ordered list of paragraph specs."""
    if edit.get("paragraphs"):
        return edit["paragraphs"]
    specs = []
    if edit.get("heading"):
        specs.append({"heading": edit["heading"]})
    if edit.get("caption"):
        specs.append({"caption": edit["caption"], "label": edit.get("label", "")})
    if edit.get("text"):
        specs.append({"text": edit["text"]})
    return specs


def apply_replace_paragraph(doc, edit, para):
    spec = edit.get("replacement_spec")
    if spec is None:
        spec = {"text": edit["replacement"]}
    fill_paragraph(doc, para, spec)
    return True


def apply_insert(doc, edit, anchor, after=True):
    parent = anchor.parentNode
    style = edit.get("style")
    new_ps = [_new_paragraph(doc, spec, style) for spec in _insert_specs(edit)]
    ref = anchor.nextSibling if after else anchor
    for np_ in new_ps:
        if ref is not None:
            parent.insertBefore(np_, ref)
        else:
            parent.addElement(np_)
    return True


# ── main walk ────────────────────────────────────────────────────────────────
def ask(prompt):
    try:
        return input(prompt).strip().lower()
    except EOFError:
        return "q"


def main():
    ap = argparse.ArgumentParser(description="Interactively apply a JSON edit manifest to an ODT.")
    ap.add_argument("--doc", required=True, help="path to the live .odt (never overwritten)")
    ap.add_argument("--edits", required=True, help="path to the JSON edit manifest")
    ap.add_argument("--out", default=None, help="output .odt (default: <doc>_edited_<timestamp>.odt)")
    ap.add_argument("--report", default=None, help="path for the summary log (default: alongside --out)")
    ap.add_argument("--yes-all", action="store_true", help="apply every locatable edit without prompting")
    ap.add_argument("--no-color", action="store_true", help="disable coloured output")
    args = ap.parse_args()

    import os as _os
    _init_colour(sys.stdout.isatty() and not args.no_color
                 and _os.environ.get("NO_COLOR") is None)

    doc_path = Path(args.doc)
    man = json.loads(Path(args.edits).read_text(encoding="utf-8"))
    edits = man["edits"]
    doc = load(str(doc_path))

    applied, review = [], []   # review = list of (id, reason)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    print(f"\napply_report_edits v{__version__}")
    print(f"document : {doc_path}")
    print(f"manifest : {args.edits}  ({len(edits)} edits, spelling={man.get('spelling','?')})")
    print("-" * 72)

    for k, edit in enumerate(edits, 1):
        t = edit["type"]
        if t == "find_replace":
            status, matches = resolve_find(doc, edit)
            anchor = None
        else:
            anchor = edit["anchor_contains"]
            ps = resolve_paragraph(doc, anchor)
            status, matches = ("ok", ps) if len(ps) == 1 else (
                "none" if not ps else "count", ps)

        print(f"\n[{k}/{len(edits)}]")
        print(preview(edit, status, matches))

        if status == "none":
            print(_c("  ✗ could not locate — flagged for review", C.RED))
            review.append((edit["id"], "no match in document"))
            continue
        if status == "count":
            n = len(matches)
            exp = edit.get("expect_count", 1) if t == "find_replace" else 1
            print(_c(f"  ✗ ambiguous: found {n}, expected {exp} — flagged for review", C.RED))
            review.append((edit["id"], f"matched {n}, expected {exp}"))
            continue

        if args.yes_all:
            choice = "y"
        else:
            prompt = (f"  Apply this edit? [{_c('y', C.GREEN)}]es / "
                      f"[{_c('n', C.YELLOW)}]o (review) / [{_c('q', C.RED)}]uit: ")
            choice = ask(prompt)

        if choice in ("q", "quit"):
            review.append((edit["id"], "skipped — user quit before this edit"))
            for later in edits[k:]:
                review.append((later["id"], "not reached — user quit"))
            print(_c("  ⏹ quit — stopping the walk", C.YELLOW))
            break
        if choice in ("n", "no"):
            print(_c("  ↳ rejected — flagged for review", C.YELLOW))
            review.append((edit["id"], "rejected by user"))
            continue

        # apply
        ok = False
        if t == "find_replace":
            ok = apply_find_replace(edit, matches)
        elif t == "replace_paragraph":
            ok = apply_replace_paragraph(doc, edit, matches[0])
        elif t == "insert_paragraph_after":
            ok = apply_insert(doc, edit, matches[0], after=True)
        elif t == "insert_paragraph_before":
            ok = apply_insert(doc, edit, matches[0], after=False)
        else:
            review.append((edit["id"], f"unknown type {t}"))
            print(f"  ✗ unknown edit type {t} — flagged for review")
            continue
        if ok:
            applied.append(edit["id"])
            print(_c("  ✓ applied", C.GREEN))
        else:
            review.append((edit["id"], "apply failed after match"))
            print(_c("  ✗ apply failed — flagged for review", C.RED))

    # ── write + summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print(_c(f"APPLIED ({len(applied)}): {', '.join(applied) if applied else '—'}", C.GREEN))
    print(_c(f"FOR REVIEW ({len(review)}):", C.YELLOW))
    for eid, reason in review:
        print(_c(f"   · {eid}: {reason}", C.DIM))

    out_path = Path(args.out) if args.out else doc_path.with_name(
        f"{doc_path.stem}_edited_{ts}.odt")
    rep_path = Path(args.report) if args.report else out_path.with_suffix(".log.txt")

    if applied:
        doc.save(str(out_path))
        print(f"\nwrote: {out_path}")
    else:
        print("\nno edits applied — source left untouched, no output written")

    lines = [f"apply_report_edits v{__version__}  {ts}",
             f"document: {doc_path}", f"manifest: {args.edits}",
             f"output:   {out_path if applied else '(none)'}", "",
             f"APPLIED ({len(applied)}):"]
    lines += [f"  {e}" for e in applied] or ["  —"]
    lines += ["", f"FOR REVIEW ({len(review)}):"]
    lines += [f"  {e}: {r}" for e, r in review] or ["  —"]
    rep_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"log:   {rep_path}")
    return 0 if not review else 2


if __name__ == "__main__":
    sys.exit(main())
