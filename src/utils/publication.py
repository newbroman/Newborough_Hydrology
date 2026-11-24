"""publication.py — the publication year of each of Martin Hollingham's works the corpus cites (D-341, draft).

The documents print these years as number fields (tools/number_fields.csv, source src/utils/publication.py),
so a work that comes out in a later year changes HERE and `field_sync --write` re-renders every citation of it.

WHY A SEPARATE MODULE, NOT config.py
  Every pipeline script imports utils/config.py, and tools/code_signature.py hashes each utils module a script
  imports: a constant added to config.py marks every step stale (a full three-hour run) for a value no script
  uses. Nothing in src/ imports this module, so editing it re-runs nothing. tools/cite_check.py lists it in
  CONSTANT_SOURCES, which is how a field reads it.

WHAT IS AND IS NOT HERE
  Only the years of Martin's own works, each cited as "Hollingham (YEAR[letter])". The letter after the year
  (a–f) stays typed text in the documents: same-year works are lettered by which works share a year, so a change
  of year here can change the letters and the order of the reference lists, which is a hand pass at submission.
  A work that has been PUBLISHED has a fixed year: its citations should then leave the field and become text.
  Never here: other authors' years (UKHO, JNCC), dated pipeline history ("Added 2026-07-18"), the years of the
  record, the imagery or the surveys. Those are facts, and a field would change them when the calendar did.

  The lettering the corpus uses (the same in every document that cites the work):
    2026a  Paper 1  — A parameter-sparse state-space framework …
    2026b  Paper 2  — Hydrological response of a coastal dune aquifer to plantation clearfell and dune scraping …
    2026c  Paper M  — One model for a dune water table …
    2026d  the technical report — Hydrogeological Dynamics, Behavioural Clustering and Management Intervention …
           (the Methods Supplement and the Supplementary Material carry the report's year on their title lines)
    2026e  the interactive modelling suite / scenario viewer (project page)
    2026f  Paper C  — Coastal retreat draws down a dune aquifer …
"""

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-24. New (D-341 draft; Martin: "draft the decision and do the 68").

PUB_YEAR_PAPER1 = 2026
PUB_YEAR_PAPER2 = 2026
PUB_YEAR_PAPERM = 2026
PUB_YEAR_REPORT = 2026
PUB_YEAR_VIEWER = 2026
PUB_YEAR_PAPERC = 2026
