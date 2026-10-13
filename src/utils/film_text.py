"""
film_text.py - the hindcast film's words, one table per language (Script 47 1.9.0).

Every string the film shows - slides, the frame readout, the caption, the hydrograph labels,
chapter titles, the footer, the film's own free-run chart - lives in a language module
``film_text_<lang>.py`` beside this one as a flat dict ``T`` of key -> string or
``str.format`` template, plus ``MONTHS`` (twelve names), ``MONTHS_SHORT`` (twelve
abbreviations) and ``NAME`` (the language's own name, for the page's language line).
English (``film_text_en``) is the reference: its keys are the complete set, and a key
missing from another language falls back to English with a console warning naming it, so a
gap is visible in the console and in the caveats file, never a crash. ``tools/film_text_lint.py``
holds the three tables to the same key set and the same template fields.

Month names come from the table, not ``strftime("%B")``: that is locale-dependent and would
render Welsh months only on a machine with cy_GB installed.

    from utils.film_text import load
    T = load("cy")
    T["contents"]                       # a plain string
    T.f("study", floor_ha=307.0)        # a template, formatted
    T.month(3)                          # "Mawrth"
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-13 (spec NRG_spec_script47_v1_9_languages_2026-10-13).
#   The film's words moved out of Script 47 into per-language tables; en, cy, pl.

import importlib
import string

from utils.config import FILM_LANGS as LANGS          # noqa: E402  - en first: the reference wording

DEFAULT_LANG = LANGS[0]
_FMT = string.Formatter()


def template_fields(s: str) -> set:
    """The named fields a template formats, e.g. {'floor_ha'} - for the lint."""
    return {f for _, f, _, _ in _FMT.parse(s) if f}


class Text:
    """One language's table with English as the fallback."""

    def __init__(self, lang: str, table: dict, months: list, months_short: list, name: str,
                 fallback: dict | None, warn=None):
        self.lang, self.name = lang, name
        self._t, self._fb = table, fallback or {}
        self.months, self.months_short = list(months), list(months_short)
        self._warn, self.missing = warn, []

    def __getitem__(self, key: str) -> str:
        if key in self._t:
            return self._t[key]
        if key in self._fb:
            if key not in self.missing:
                self.missing.append(key)
                if self._warn:
                    self._warn(f"film_text_{self.lang}: no '{key}'; the English is shown")
            return self._fb[key]
        raise KeyError(f"film_text: no key '{key}' in {self.lang} or en")

    def __contains__(self, key: str) -> bool:
        return key in self._t or key in self._fb

    def f(self, key: str, **kw) -> str:
        """The template at `key`, formatted."""
        return self[key].format(**kw)

    def month(self, m: int) -> str:
        """The name of calendar month m (1-12)."""
        return self.months[m - 1]

    def month_short(self, m: int) -> str:
        return self.months_short[m - 1]

    def when(self, ts) -> str:
        """'Mar 2021' - the short month and the year, for a pandas Timestamp or date."""
        return f"{self.month_short(ts.month)} {ts.year}"

    def when_day(self, ts) -> str:
        """'4 Apr 2021' - day, short month and year."""
        return f"{ts.day} {self.month_short(ts.month)} {ts.year}"

    def keys(self):
        return self._t.keys()


def table(lang: str):
    """The raw language module (T, MONTHS, MONTHS_SHORT, NAME)."""
    if lang not in LANGS:
        raise ValueError(f"film_text: unknown language '{lang}'; one of {LANGS}")
    return importlib.import_module(f"utils.film_text_{lang}")


def load(lang: str = DEFAULT_LANG, warn=None) -> Text:
    """The table for `lang`, with English behind it."""
    mod = table(lang)
    fb = None if lang == DEFAULT_LANG else table(DEFAULT_LANG).T
    return Text(lang, mod.T, mod.MONTHS, mod.MONTHS_SHORT, mod.NAME, fb, warn)
