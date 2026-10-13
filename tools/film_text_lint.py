#!/usr/bin/env python3
"""
film_text_lint.py — do the film's language tables still say the same things?

WHAT GOES WRONG WITHOUT IT

  Script 47 1.9.0 reads every word it shows from utils/film_text_<lang>.py, one flat
  table per language, English the reference. A key added to the English table and
  forgotten in Welsh falls back to English at render time with a warning — the film
  still renders, in two languages on one slide. A template whose fields differ
  between languages ({floor_ha} in English, {floor} in Polish) raises KeyError in
  the middle of a ten-minute render. Neither is a fault a reader of the tables
  would see, and nothing else reads them.

WHAT IT CHECKS (all GATE — every fault here is unambiguous and cheap to fix)

  * every language has exactly the English key set — no missing, no extra
  * every template formats the same named fields as its English counterpart
  * MONTHS and MONTHS_SHORT carry twelve entries each
  * every English template formats with its fields' names (a smoke test of the
    reference itself: a stray brace in the English breaks every language)
  * no em space (U+2003) in any string — the project's standing rule for documents

Usage:  python3 tools/film_text_lint.py          exit 0 OK / 1 faults
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-13. First version, with Script 47 1.9.0.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from utils import film_text                                  # noqa: E402


def main() -> int:
    faults = []
    ref = film_text.table(film_text.DEFAULT_LANG)
    ref_keys = set(ref.T)
    for lang in film_text.LANGS:
        mod = film_text.table(lang)
        keys = set(mod.T)
        for k in sorted(ref_keys - keys):
            faults.append(f"{lang}: missing key '{k}'")
        for k in sorted(keys - ref_keys):
            faults.append(f"{lang}: extra key '{k}' (not in en)")
        for k in sorted(keys & ref_keys):
            a, b = film_text.template_fields(ref.T[k]), film_text.template_fields(mod.T[k])
            if a != b:
                faults.append(f"{lang}: '{k}' formats {sorted(b)}; en formats {sorted(a)}")
        for name in ("MONTHS", "MONTHS_SHORT"):
            if len(getattr(mod, name, [])) != 12:
                faults.append(f"{lang}: {name} has {len(getattr(mod, name, []))} entries, not 12")
        if not getattr(mod, "NAME", ""):
            faults.append(f"{lang}: no NAME")
        for k, v in mod.T.items():
            if " " in v:
                faults.append(f"{lang}: '{k}' contains an em space (U+2003)")
    # the reference's own templates format
    for k, v in ref.T.items():
        try:
            v.format(**{f: 1.0 for f in film_text.template_fields(v)})
        except (KeyError, ValueError, IndexError) as e:
            faults.append(f"en: '{k}' does not format: {e}")
    if faults:
        for f in faults:
            print(f"  FAULT {f}")
        print(f"  film_text_lint: {len(faults)} fault(s) across {len(film_text.LANGS)} language(s)")
        return 1
    print(f"  film_text_lint: OK — {len(ref_keys)} keys, {len(film_text.LANGS)} languages "
          f"({', '.join(film_text.LANGS)}) agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
