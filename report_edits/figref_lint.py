#!/usr/bin/env python3
# =============================================================================
# figref_lint.py — figure reference linter for the Newborough report
#
# WHY
#   Captions in report.odm auto-number correctly across all subdocuments, but the
#   in-text references are typed by hand (cross-references cannot span the master's
#   sections). When a figure is added or removed, the captions renumber themselves
#   and the typed references silently fall out of step. This linter catches that.
#
# WHAT IT DOES
#   Reads the EXPORTED PDF (the only artefact where both captions and references
#   carry resolved numbers), extracts:
#     - the caption sequence   (lines like "Figure 58: Clearfell step-change map…")
#     - every in-text reference ("Figure 58", "Figures 7 and 8", "Figure 47a")
#   then reports:
#     1. sequence health   — gaps, duplicates, whether it runs 1..N clean
#     2. dangling refs      — a reference to a figure number with no caption
#     3. an index dump      — number -> caption title, for eyeballing
#
#   It does NOT judge whether a reference points at the *right* figure — only
#   whether the number exists. Semantic checks (does "parametric net state map"
#   really cite 59?) still need a human or the correction-list workflow.
#
# USAGE
#   Export report.odm to PDF first (File > Export as PDF), then:
#       python3 figref_lint.py path/to/report.pdf
#       python3 figref_lint.py path/to/report.pdf --index      # also dump the index
#       python3 figref_lint.py path/to/report.pdf --json out.json
#
#   Requires `pdftotext` (poppler-utils) on PATH. No Python dependencies.
#
# EXIT CODE
#   0 = clean (sequence 1..N, no gaps/dupes, no dangling refs)
#   1 = problems found (details printed)
#   2 = usage / environment error
#
# VERSION
#   v1.1.0  2026-08-12  caption detector now ignores in-text references that wrap
#                       onto a line start (e.g. "…drawn in\nFigure 73. A dune…").
#                       These were being miscounted as duplicate captions and
#                       failing the sequence check (Figures 43, 52, 73).
#   v1.0.0  2026-07-12
# =============================================================================

import os
import re
import sys
import json
import shutil
import subprocess
from collections import Counter

C_RED = "\033[31m"; C_GRN = "\033[32m"; C_YEL = "\033[33m"; C_DIM = "\033[2m"; C_0 = "\033[0m"
def _c(s, c):
    return s if not sys.stdout.isatty() else f"{c}{s}{C_0}"


def _refuse_if_stale(pdf_path):
    """A stale PDF does not make this lint fail — it makes it LIE.

    On 2026-08-23 report.pdf was dated 06:51 while four of its source documents
    had been edited after it, so this tool parsed a document that no longer
    existed and reported it clean. Reading an out-of-date artefact is worse than
    not reading one, because the green result is taken as evidence.
    """
    import subprocess as _sp
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lag = os.path.join(repo, "tools", "export_lag.py")
    if not os.path.exists(lag):
        return
    r = _sp.run([sys.executable, lag, "--strict"], capture_output=True, text=True)
    if r.returncode != 0 and os.path.basename(pdf_path) in r.stdout:
        sys.exit(_c(r.stdout + "\nrefusing to lint a PDF older than its sources — "
                    "re-export first", C_RED))


def extract_text(pdf_path):
    _refuse_if_stale(pdf_path)
    if not shutil.which("pdftotext"):
        sys.exit(_c("error: pdftotext not found (install poppler-utils)", C_RED))
    try:
        out = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        sys.exit(_c(f"error: pdftotext failed: {e}", C_RED))
    return out.stdout


# A caption line: starts (after optional leading space) with "Figure N. Title"
# or "Figure N: Title" — LibreOffice caption fields render with a PERIOD after
# the number ("Figure 3a. Data coverage…"), not a colon. Accept either.
# The ^\s* anchor plus the required whitespace after the separator keeps this from
# matching a mid-sentence "…in Figure 3. The next…" unless that reference has
# wrapped to the very start of a line AND is followed by a capitalised word.
# That case DOES occur in this document: Figures 43, 52 and 73 are cross-referenced
# from the long captions of neighbouring multi-panel figures (and from body text),
# and the reference wraps to a line start ("…drawn schematically in\nFigure 73. A
# dune scrape…"). parse_captions() filters those out by inspecting the preceding
# line — see _is_wrapped_reference() below.
CAPTION_RE = re.compile(r"^\s*Figure (\d+[a-z]?)[.:]\s+(.*)$")

# An in-text reference. Handles "Figure 58", "Figures 7 and 8", "Figures 36-39",
# "Figures 22, 23", "Figure 47a". Captures the leading number plus any tail list
# so ranges/lists can be expanded.
REF_RE = re.compile(
    r"Figures?\s+"
    r"(\d+[a-z]?"                        # first number
    r"(?:\s*(?:,|and|&|–|-|to)\s*\d+[a-z]?)*"  # optional list/range tail
    r")"
)


# Running page header / footer lines. Treated as transparent (like a blank line)
# when deciding whether a caption-shaped line begins a fresh block: a real caption
# can sit immediately after a page break.
_HEADER_RE = re.compile(r"confidential draft|Newborough Warren Coastal Aquifer")

# Characters that close a sentence or a caption. If the line before a "Figure N."
# match ends with one of these — or is blank, or is a running header — the match
# starts a fresh block and is a genuine caption. If it ends mid-sentence, the match
# is an in-text reference that has wrapped onto a line start and must not be counted.
_SENTENCE_END = (".", ":", "!", "?")


def _is_wrapped_reference(lines, i):
    """True when the caption-shaped line at index ``i`` is really an in-text
    reference that wrapped onto a line start (e.g. a sentence "…drawn in" whose
    next line begins "Figure 73. A dune scrape…").

    The tell is the immediately-preceding line: a genuine caption is preceded by a
    blank line or a running header (the start of its own block), whereas a wrapped
    reference is preceded by body text that ends mid-sentence.
    """
    if i == 0:
        return False
    prev = lines[i - 1]
    if not prev.strip():                 # blank line before → genuine caption block
        return False
    if _HEADER_RE.search(prev):          # page header/footer → genuine caption
        return False
    return not prev.rstrip().endswith(_SENTENCE_END)


def parse_captions(lines):
    """Return list of (number_str, title) in document order, skipping stray
    heading-styled lines that masquerade as captions and in-text references that
    have wrapped onto a line start (see _is_wrapped_reference)."""
    caps = []
    for i, ln in enumerate(lines):
        m = CAPTION_RE.match(ln)
        if not m:
            continue
        if _is_wrapped_reference(lines, i):
            continue
        num, title = m.group(1), m.group(2).strip()
        # a real caption has descriptive text; if the line is short, pull the next
        if len(title) < 25 and i + 1 < len(lines):
            title = (title + " " + lines[i + 1].strip()).strip()
        caps.append((num, title[:80]))
    return caps


def expand_ref(chunk):
    """'7 and 8' -> ['7','8']; '36-39' -> ['36','37','38','39']; '47a' -> ['47a']."""
    chunk = chunk.replace("&", ",").replace(" and ", ",").replace(" to ", "-")
    out = []
    for part in re.split(r"\s*,\s*", chunk):
        part = part.strip()
        if not part:
            continue
        rng = re.match(r"^(\d+)\s*[–-]\s*(\d+)$", part)
        if rng:
            a, b = int(rng.group(1)), int(rng.group(2))
            out.extend(str(n) for n in range(a, b + 1))
        else:
            out.append(part)
    return out


def parse_refs(lines):
    """Return list of (line_index, number_str) for every in-text figure reference,
    excluding the caption lines themselves."""
    refs = []
    for i, ln in enumerate(lines):
        if CAPTION_RE.match(ln):
            continue
        for m in REF_RE.finditer(ln):
            for num in expand_ref(m.group(1)):
                refs.append((i + 1, num))
    return refs


def base_int(num_str):
    m = re.match(r"\d+", num_str)
    return int(m.group()) if m else None


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(2)
    pdf = args[0]
    want_index = "--index" in args
    json_out = None
    if "--json" in args:
        json_out = args[args.index("--json") + 1]

    text = extract_text(pdf)
    lines = text.split("\n")

    # Captions must be parsed line-by-line (they start at a line boundary).
    caps = parse_captions(lines)

    # References, by contrast, wrap across line breaks in -layout output
    # ("Figure\n34"). Scan a whitespace-collapsed copy so split refs are caught,
    # after blanking the caption lines so a caption's own number isn't counted.
    scan_lines = ["" if CAPTION_RE.match(ln) else ln for ln in lines]
    flat = re.sub(r"\s+", " ", " ".join(scan_lines))
    refs = []
    for m in REF_RE.finditer(flat):
        for num in expand_ref(m.group(1)):
            refs.append((0, num))  # line number not meaningful after flattening

    cap_nums = [n for n, _ in caps]
    cap_ints = sorted({base_int(n) for n in cap_nums if base_int(n)})
    cap_int_set = set(cap_ints)
    cap_letter_set = {n for n in cap_nums}  # includes '3a', '46a' etc.

    problems = []

    # --- 1. sequence health --------------------------------------------------
    dupes = [n for n, c in Counter(cap_nums).items() if c > 1]
    mx = max(cap_ints) if cap_ints else 0
    gaps = [i for i in range(1, mx + 1) if i not in cap_int_set]

    print(_c("── caption sequence ──", C_DIM))
    print(f"  captions found : {len(caps)}")
    print(f"  distinct numbers: {len(cap_ints)}  (max {mx})")
    if dupes:
        problems.append(("duplicate caption numbers", dupes))
        print(_c(f"  DUPLICATES     : {', '.join(dupes)}", C_RED))
    if gaps:
        problems.append(("gaps in caption sequence", gaps))
        print(_c(f"  GAPS           : {', '.join(map(str, gaps))}", C_RED))
    if not dupes and not gaps:
        print(_c(f"  clean 1..{mx}, no gaps, no duplicates", C_GRN))

    # --- 2. dangling references ---------------------------------------------
    dangling = Counter()
    for _, num in refs:
        ok = (base_int(num) in cap_int_set) or (num in cap_letter_set)
        if not ok:
            dangling[num] += 1
    print(_c("\n── in-text references ──", C_DIM))
    print(f"  references found: {len(refs)}")
    if dangling:
        problems.append(("references to non-existent figures", dict(dangling)))
        print(_c(f"  DANGLING       : {len(dangling)} number(s) with no caption", C_RED))
        for num in sorted(dangling, key=lambda x: (base_int(x) or 0, x)):
            print(f"      Figure {num:<5} -> no such caption   (x{dangling[num]})")
    else:
        print(_c("  every reference points at an existing caption", C_GRN))

    # --- 3. figures never referenced (informational) ------------------------
    referenced = {base_int(n) for _, n in refs if base_int(n)}
    orphan_caps = [n for n in cap_ints if n not in referenced]
    if orphan_caps:
        print(_c("\n── figures with NO in-text reference (check these are cited) ──", C_YEL))
        titles = {base_int(n): t for n, t in caps}
        for n in orphan_caps:
            print(f"  Figure {n:<3} {C_DIM}{titles.get(n,'')[:60]}{C_0}"
                  if sys.stdout.isatty() else f"  Figure {n:<3} {titles.get(n,'')[:60]}")

    # --- optional index dump ------------------------------------------------
    if want_index:
        print(_c("\n── caption index ──", C_DIM))
        for num, title in caps:
            print(f"  {num:>5}  {title}")

    if json_out:
        json.dump({
            "captions": caps,
            "reference_count": len(refs),
            "duplicates": dupes,
            "gaps": gaps,
            "dangling": dangling,
            "unreferenced_captions": orphan_caps,
        }, open(json_out, "w"), indent=2)
        print(_c(f"\nwrote {json_out}", C_DIM))

    # --- verdict ------------------------------------------------------------
    print()
    if problems:
        print(_c(f"FAIL — {len(problems)} problem class(es) found", C_RED))
        sys.exit(1)
    print(_c("PASS — captions clean and every reference resolves", C_GRN))
    if orphan_caps:
        print(_c(f"note: {len(orphan_caps)} figure(s) are never referenced (see above)", C_YEL))
    sys.exit(0)


if __name__ == "__main__":
    main()
