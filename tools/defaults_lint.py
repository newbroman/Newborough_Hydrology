#!/usr/bin/env python3
"""
defaults_lint — does each documented first-pass default still equal the
committed cell it mirrors?

WHY

  `pipeline_params._DEFAULTS` holds the values late scripts fall back to when an
  output they need has not been written yet in the same pass (the two-pass
  mechanism: 09b/09d for Sy, 09f for lambda and delta_0, coastal_utils for the
  retreat rate). Each entry carries a comment naming the CSV and column it
  mirrors, and that comment is the only thing that has ever checked it.

  It has not held. The drift has recurred five times in eleven days:
  pipeline_params v1.2.1 (lambda), v1.5.0 (climate_c, wrong in SIGN), the
  2026-08-28 sweep ("four of the six below had drifted"), and v1.8.0 (the two
  mechanism entries, one of which had been stale for months). D-091 recorded the
  gap and deliberately left the tool to Martin:

      "Nothing gates a documented default against the CSV it mirrors; a
       defaults_lint is a design question for Martin, deliberately not built
       here."

  This is that tool.

WHY A REGISTRY AND NOT A COMMENT PARSER

  The comments are prose written for a person. Of the 24 entries, ZERO carry all
  four fields a checker needs (file, row, column, scale); only 7 name an exact
  column; the token "09a" appears in no filename; "10a" prefix-matches 15 files;
  and the scale is written "x1000" in one entry and "×1000" in another. A
  parser over that is a guess wearing a tool's clothes. So the basis is
  DECLARED, in tools/defaults_basis.csv, exactly as tools/record_basis.csv
  declares which record each analysis fits — same idiom, same reason.

  The registry names the paths.py SYMBOL rather than a path, so "all I/O via
  paths.py" is enforced for free and a renamed output is a fault rather than a
  silent skip.

TOLERANCE — the decimals the literal is written to, and nothing else

  These are rounded mirrors: 226.4 mirrors 226.44221643042582 and is correct.
  Exact equality would fail every honestly-written entry. A relative band cannot
  work either, because climate_c_mm_yr crosses zero and a relative band around
  zero is meaningless.

  So: read `d`, the number of decimal places in the literal AS WRITTEN IN THE
  SOURCE TEXT, and require

      | default - scale x committed |  <=  0.5 * 10**-d  +  1e-9

  `d` must come from the source text, never from repr(float): -81.00 reprs as
  -81.0, which would give d=1 and a tolerance ten times too loose.

  Every passing entry is exactly round(committed, d). That is not luck — it is
  the convention the file already follows; this only makes it checkable.

GATED, not advisory. The trailing comment on every entry IS the advisory, and it
did not hold five times. The backlog when this was written was two entries, not
thirty-two, so the docref_lint reasoning ("a gate that fails from birth is a
gate that gets commented out") does not apply.

WHAT IT CANNOT SEE

  * It checks the default against the cell it DECLARES, not the right one. A
    wrong registry row goes green forever. A registry is a claim, not a proof.
  * 8 of 24 entries stay outside the net — 7 seed placeholders and one derived
    aggregate (uniform_residual_mm_yr, computed in 37b). Reported every run,
    never verified, so the absence is visible rather than silent.
  * It compares against COMMITTED CSVs, so on a tree whose outputs are stale
    against the scripts, a default refreshed to a stale CSV passes. output_lag
    asks that question; the two are only jointly meaningful.
  * It does not check that the live loader reads the cell the registry declares.
    _load_clearfell_recovery_mm selects positionally (df.columns[3]); insert a
    column upstream and the loader reads the wrong one while this stays green.

__version__ : 1.0.0
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-29. First issue, with
#   tools/defaults_basis.csv. Built after D-091 flagged the gap and D-092's
#   spec work found two live drifts that no gate could see.

import csv
import pathlib
import re
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
REGISTRY = ROOT / "tools" / "defaults_basis.csv"
PARAMS = SRC / "utils" / "pipeline_params.py"

GREEN, YELLOW, RED, DIM, RESET = (
    "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[0m")

EPS = 1e-9


def literal_decimals(text: str) -> dict[str, tuple[float, int]]:
    """key -> (value, decimals AS WRITTEN) from the _DEFAULTS block source."""
    out: dict[str, tuple[float, int]] = {}
    block = re.search(r"_DEFAULTS\s*(?::[^=]*)?=\s*\{(.*?)^\}", text,
                      re.S | re.M)
    if not block:
        return out
    for m in re.finditer(r'^\s*"([A-Za-z0-9_]+)"\s*:\s*(-?\d+(?:\.\d+)?)',
                         block.group(1), re.M):
        key, lit = m.group(1), m.group(2)
        out[key] = (float(lit), len(lit.split(".")[1]) if "." in lit else 0)
    return out


def resolve_symbol(sym: str):
    sys.path.insert(0, str(SRC))
    from utils import paths as P            # noqa: E402  (deliberately late)
    return getattr(P, sym, None)


def select(df: pd.DataFrame, spec: str, path: pathlib.Path):
    """Return (row, error). spec is '#0' or 'col=val;col=val'."""
    if spec.startswith("#"):
        i = int(spec[1:])
        if i >= len(df):
            return None, f"row {spec} is beyond the {len(df)}-row file"
        return df.iloc[i], None
    mask = pd.Series(True, index=df.index)
    for term in spec.split(";"):
        col, _, val = term.partition("=")
        col, val = col.strip(), val.strip()
        if col not in df.columns:
            return None, f"selector column {col!r} is not in {path.name}"
        mask &= df[col].astype(str).str.strip() == val
    hits = df[mask]
    if len(hits) == 0:
        return None, f"selector {spec!r} matches no row"
    if len(hits) > 1:
        return None, f"selector {spec!r} matches {len(hits)} rows — ambiguous"
    return hits.iloc[0], None


def main() -> int:
    if not REGISTRY.exists():
        print(f"  {RED}FAIL{RESET}  {REGISTRY.relative_to(ROOT)} is missing")
        return 1
    lits = literal_decimals(PARAMS.read_text(encoding="utf-8"))
    if not lits:
        print(f"  {RED}FAIL{RESET}  could not read _DEFAULTS from "
              f"{PARAMS.relative_to(ROOT)}")
        return 1

    rows = list(csv.DictReader(REGISTRY.open(encoding="utf-8")))
    declared = {r["key"] for r in rows}
    faults: list[str] = []

    # Coverage, both ways. A default added without a row is the recurrence route.
    for k in lits:
        if k not in declared:
            faults.append(f"_DEFAULTS['{k}'] has no row in "
                          f"{REGISTRY.name} — add one")
    for k in declared:
        if k not in lits:
            faults.append(f"{REGISTRY.name} has a row for '{k}', which is not "
                          f"in _DEFAULTS — remove it")

    checked = drifted = 0
    derived = [r for r in rows if r["verify"] == "derived"]
    seeds = [r for r in rows if r["verify"] == "seed"]
    cache: dict[pathlib.Path, pd.DataFrame] = {}

    for r in rows:
        if r["verify"] != "cell" or r["key"] not in lits:
            continue
        key = r["key"]
        value, dec = lits[key]
        path = resolve_symbol(r["path_symbol"])
        if path is None:
            faults.append(f"{key}: paths.py has no symbol "
                          f"{r['path_symbol']!r}")
            continue
        path = pathlib.Path(path)
        if not path.exists():
            faults.append(f"{key}: {r['path_symbol']} -> {path.name} "
                          f"is absent (these outputs are committed)")
            continue
        if path not in cache:
            cache[path] = pd.read_csv(path)
        row, err = select(cache[path], r["row"], path)
        if err:
            faults.append(f"{key}: {err}")
            continue
        if r["column"] not in row.index:
            faults.append(f"{key}: column {r['column']!r} is not in "
                          f"{path.name}")
            continue
        scale = float(r["scale"] or 1.0)
        committed = float(row[r["column"]]) * scale
        tol = 0.5 * 10 ** (-dec) + EPS
        checked += 1
        if abs(value - committed) > tol:
            drifted += 1
            sc = "" if scale == 1.0 else f" x{scale:g}"
            print(f"  {RED}FAIL{RESET}  {key} = {value:g}, but {path.name}")
            print(f"        [{r['row']}].{r['column']}{sc} = {committed:g}")
            print(f"        off by {abs(value - committed):g} "
                  f"(tolerance {tol - EPS:g} — the default is written to "
                  f"{dec} dp)")
            print(f"        {DIM}A stale fallback is worse than none: the "
                  f"warning says \"default\" and the reader believes it.{RESET}")
            print(f"        {DIM}Refresh in src/utils/pipeline_params.py and "
                  f"bump __version__.{RESET}")

    for f in faults:
        print(f"  {RED}FAIL{RESET}  {f}")

    if not drifted and not faults:
        print(f"  {GREEN}OK{RESET}    {checked} default(s) match the CSV they "
              f"mirror, at the precision they are written to")
    for r in derived:
        print(f"  {DIM}·     derived: {r['key']} — {r['note']} — reported, "
              f"not checked{RESET}")
    print(f"  {DIM}·     {len(seeds)} seed placeholder(s) — not mirrors of any "
          f"CSV{RESET}")

    bad = drifted or faults
    print(f"defaults_lint: {RED}FAIL{RESET}" if bad
          else f"defaults_lint: {GREEN}OK{RESET}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
