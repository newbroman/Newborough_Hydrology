#!/usr/bin/env python3
# =============================================================================
# drift_term_lint.py — a consumer of 10a's coefficients must not name the drift
#                      column by literal.
#
# WHY
#   D-111 made the coastal design the published one, so Script 10a stopped
#   emitting `easting_x_time` and started emitting `coastal_x_time`. The
#   PRODUCER was swept and the CONSUMERS were not. Script 25 went on filtering
#   its copy of the coefficient table on the literal string 'easting_x_time',
#   matched nothing, wrote a ONE-BYTE FILE over a committed artefact, and then
#   raised a KeyError on the next line — a traceback naming a display statement
#   while the cause sat forty lines earlier and the output was already gone.
#   A full pipeline run died there (W134).
#
#   utils.clearfell_common.drift_term() was written that day to resolve the
#   column by name and RAISE before any write when none is present. This lint
#   is the other half: nothing made anyone use it.
#
# THE INVARIANT, and it is deliberately narrow
#   A script that READS 10a_02_ancova_full_coefficients.csv must not contain a
#   drift-column string literal. It must go through drift_term().
#
#   Narrow because the literals are legitimate in three places, and a lint that
#   flags them teaches people to switch it off:
#
#     * Script 10a itself is the PRODUCER. It emits whichever column the design
#       selects and must name both.
#     * utils/clearfell_common.py DEFINES the names — that is what DRIFT_COLUMNS
#       is.
#     * Scripts 10h and 10k BUILD THEIR OWN easting column from well geometry
#       (`df['easting_x_time'] = delta_easting * months_since`). They are not
#       reading 10a's table, so there is nothing for them to resolve. Whether
#       those two SHOULD condition on an easting drift when the published design
#       is coastal is a live editorial question, but it is not this lint's:
#       conflating "names a literal" with "uses the wrong design" is how a
#       narrow check becomes an unreliable one.
#
# EXIT CODES
#   0 clean   1 a consumer names a drift column by literal   2 usage/environment
#
# VERSION
#   v1.0.0  2026-09-03  W134. Passes on the tree it was written against, which
#           is the point: it is a regression guard, not a backlog.
# =============================================================================
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-03. W134.

import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO / "src"

# The table whose columns are at issue.
PRODUCER_OUTPUT = "10a_02_ancova_full_coefficients"
PRODUCER_CONST = "OUT_10A_FULL_COEFFS"

# Files allowed to name a drift column, with the reason each is allowed.
EXEMPT = {
    "10a_ancova_baci.py":
        "the producer — it emits whichever column the design selects",
    "clearfell_common.py":
        "defines DRIFT_COLUMNS; this is where the names live",
    "paths.py":
        "names the artefact, not a column",
    "drift_term_lint.py":
        "this file",
}

DRIFT_NAMES = ("easting_x_time", "coastal_x_time")


# WHAT COUNTS AS A VIOLATION, and the distinction is the whole point.
#
#   BAD   df['easting_x_time']                  — looking a column up by name
#         frame[frame.term == 'easting_x_time'] — filtering rows by name
#         cols.append('easting_x_time')          — building a design by name
#         Each SURVIVES a design change silently: it matches nothing, and the
#         filter returns empty rather than raising.
#
#   FINE  if drift_col == 'coastal_x_time':      — testing a name ALREADY
#         resolved by drift_term(), which is how a script branches on the units
#         the two designs carry. Script 25 v1.21.0 exists because resolving the
#         NAME without resolving the UNITS produced -309,628,313 mm/yr in a
#         published table. Flagging that line would push people back toward the
#         bug this lint exists to prevent.
#
# So: a literal is a violation when it is a SUBSCRIPT, an argument, or compared
# against a subscript; it is fine when compared against a plain variable.
def violations(tree) -> list[tuple[int, str, str]]:
    import ast
    out = []

    def is_drift(node):
        return (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and node.value in DRIFT_NAMES)

    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and is_drift(n.slice):
            out.append((n.lineno, n.slice.value, "looked up as a column"))
        elif isinstance(n, ast.Compare):
            for side, other in ((n.left, n.comparators[0]),
                                (n.comparators[0], n.left)):
                if is_drift(side) and isinstance(other, (ast.Subscript, ast.Attribute)):
                    out.append((n.lineno, side.value, "compared against a frame column"))
        elif isinstance(n, ast.Call):
            for a in n.args:
                if is_drift(a):
                    fn = getattr(n.func, "attr", getattr(n.func, "id", "?"))
                    out.append((n.lineno, a.value, f"passed to {fn}()"))
    return out


def consumers() -> list[pathlib.Path]:
    """Scripts that read 10a's coefficient table."""
    out = []
    for p in sorted(SRC.rglob("*.py")):
        text = p.read_text(encoding="utf8", errors="ignore")
        if PRODUCER_CONST in text or PRODUCER_OUTPUT in text:
            out.append(p)
    return out


# The cases this lint exists for, and the ones it must leave alone. A check
# that passes on today's tree proves nothing on its own — it would also pass if
# the detection were broken. --selftest is the difference between "green" and
# "green for the right reason".
SELFTEST = [
    (True,  "the Script 25 bug, exactly as it was",
     "rows = coeffs[coeffs['term'] == 'easting_x_time']"),
    (True,  "a column lookup",
     "x = df['easting_x_time']"),
    (True,  "building a design by name",
     "cols.append('coastal_x_time')"),
    (False, "the units branch on an already-resolved name",
     "if drift_col == 'coastal_x_time':\n    pass"),
    (False, "the accessor used properly",
     "drift_col = drift_term(fit['col_names'])"),
]


def selftest() -> int:
    failed = 0
    for should_fire, label, src in SELFTEST:
        fired = bool(violations(ast.parse(src)))
        ok = fired == should_fire
        failed += not ok
        print(f"  {'ok  ' if ok else 'FAIL'}  "
              f"{'catches' if should_fire else 'allows '}  {label}")
    if failed:
        print(f"\ndrift_term_lint --selftest: {failed} case(s) wrong")
        return 1
    print(f"  drift_term_lint --selftest: {len(SELFTEST)} case(s), all correct")
    return 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    if not SRC.is_dir():
        print(f"no src/ at {SRC}")
        return 2
    bad = []
    checked = 0
    for p in consumers():
        if p.name in EXEMPT:
            continue
        checked += 1
        try:
            tree = ast.parse(p.read_text(encoding="utf8", errors="ignore"))
        except SyntaxError as e:
            print(f"  UNPARSEABLE  {p.relative_to(REPO)}: {e.msg}")
            return 2
        hits = violations(tree)
        if hits:
            bad.append((p, hits))

    for p, hits in bad:
        print(f"  RESOLVES A DRIFT COLUMN BY LITERAL  {p.relative_to(REPO)}")
        for ln, name, how in hits[:6]:
            print(f"      line {ln}: {name!r} {how} — use "
                  f"clearfell_common.drift_term() instead")
    if bad:
        print(f"\ndrift_term_lint: {len(bad)} consumer(s) of "
              f"{PRODUCER_OUTPUT}.csv name a drift column by literal.\n"
              f"  A literal survives a design change silently: it matches "
              f"nothing and the filter returns empty.\n"
              f"  drift_term() raises instead, before anything is written.")
        return 1
    print(f"  drift_term_lint: OK — {checked} consumer(s) of "
          f"{PRODUCER_OUTPUT}.csv, none naming a drift column by literal "
          f"({len(EXEMPT) - 1} declared exemption(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
