"""
utils/comment_states.py
=======================
Parse the field comments embedded in the raw groundwater records spreadsheet
(``Newborough_well_recordsA.ods``, sheet ``measured``) into a per-cell
observation-state layer, and assemble the full coverage grid used by the data-
coverage figure.

Why this exists
---------------
A blank monthly cell in the cleaned well series is ambiguous: the well might
have been dry, flooded above the pipe, physically un-locatable, obstructed, or
simply not visited that month. The author recorded the reason as a cell comment
("dry at 1.83", "Flooded, over welly height", "Not found", "Blocked by ants",
...). Those comments are stripped before the data reach the pipeline CSV, so the
distinction is lost. This module recovers it directly from the .ods and exposes
it as a tidy state layer.

Two public functions
--------------------
``parse_comment_states(ods_path)``
    Returns a long DataFrame [well, month, state, dry_depth_m] of every comment
    that maps to a (well, month) cell, plus the count of unmapped comments.
    ``state`` is one of {dry, flooded, not_found, inaccessible}. ``dry_depth_m``
    is the censored depth-below-ground at which the well was found dry (water
    table at or below that level); it is time-varying by design — sediment in-
    fall reduces the effective pipe depth, pipe clearing restores it — so it is
    retained per observation, never collapsed to a per-well constant.

``assemble_observation_states(maod, comment_long, ...)``
    Combines the comment layer with measured-value presence and two inference
    rules (dry-season blanks; block-fill of missing runs that contain a recorded
    dry) to produce a wide month x well grid of states drawn from:
        measured | dry_recorded | dry_inferred | flooded |
        not_found | inaccessible | not_read | outside_record

Classification keywords, the dry-season window, and the cm/m depth threshold all
live in ``utils.config`` (no hardcoded vocabulary here).

NOTE ON PRIVACY: only the derived *state* (and parsed dry depth) is returned.
Raw comment text is never propagated to any output file.

Version
-------
1.1.0 (2026-06-15) - author adjudication of comment/measurement collisions:
    a dry note keeps an existing reading (marks dry only where no measurement);
    a not_found/inaccessible note treats any value as an estimate and mimics the
    pipeline (interpolate an isolated single-month gap, else leave not-measured).
    assemble_observation_states() gains provenance= and returns (states,
    conflicts); an interpolated state is surfaced.
1.0.0 (2026-06-15) - initial implementation. See CHANGELOG.
"""
from __future__ import annotations

import datetime
import re

import pandas as pd

from utils.config import (
    OBSERVATION_STATE_RULES,
    OBSERVATION_FLOOD_LEVEL_HINTS,
    DRY_SEASON_MONTHS,
    DRY_DEPTH_CM_THRESHOLD,
)

# Layout of the ``measured`` sheet (0-indexed): row 1 holds the survey dates,
# column 10 holds the canonical well id for each data row.
_DATE_HEADER_ROW = 1
_WELL_ID_COL = 10

# States that come straight from a comment (as opposed to being inferred).
COMMENT_STATES = tuple(state for state, _ in OBSERVATION_STATE_RULES)


# ── comment text handling ────────────────────────────────────────────────────
def _strip_author(text: str) -> str:
    """Remove the LibreOffice author/timestamp prefix from a comment string."""
    t = re.sub(r"^Unknown Author\d{4}-\d{2}-\d{2}T[\d:]+", "", text, flags=re.I)
    t = re.sub(r"^(Martin Hollingham|Martin)\s*:?\s*", "", t, flags=re.I)
    return t.strip()


def classify_comment(text: str) -> str | None:
    """Map a cleaned comment to an observation state, or None if it is not a
    coverage state (e.g. a reading-date note or a datum correction).

    Rules are applied in the priority order defined by OBSERVATION_STATE_RULES.
    The CEH24/CEH34 level-surface flood estimates name the partner well rather
    than using a flood keyword, so they are caught by an explicit hint check
    before the keyword loop.
    """
    s = text.lower()
    # CEH24/34 level-surface flood estimate (e.g. "infered from CEH 24 level",
    # "CEH 24 is at 0 then CEH 34 is at -0.12").
    if any(h in s for h in OBSERVATION_FLOOD_LEVEL_HINTS) and (
        "level" in s or "at 0" in s
    ):
        return "flooded"
    for state, keywords in OBSERVATION_STATE_RULES:
        if any(k in s for k in keywords):
            return state
    return None


def parse_dry_depth(text: str) -> float | None:
    """Parse the depth from a 'dry at X' comment into metres below ground.

    Values above DRY_DEPTH_CM_THRESHOLD are read as centimetres and converted
    (e.g. "dry at 110" -> 1.10 m); values at or below are already metres
    (e.g. "dry at 1.10" -> 1.10 m). Returns None if no number is present.
    """
    m = re.search(r"(\d+\.?\d*)", text)
    if not m:
        return None
    v = float(m.group(1))
    return round(v / 100.0, 3) if v > DRY_DEPTH_CM_THRESHOLD else v


def _bucket_to_month(d) -> pd.Timestamp:
    """Field-convention bucketing: a reading on day <= 15 belongs to the
    previous month; day > 15 belongs to the same month. Returns YYYY-MM-01."""
    d = pd.Timestamp(d)
    m = d.replace(day=1) if d.day > 15 else d.replace(day=1) - pd.offsets.MonthBegin(1)
    return pd.Timestamp(m.year, m.month, 1)


# ── public: parse comments -> long state table ───────────────────────────────
def parse_comment_states(ods_path, sheet: str = "measured"):
    """Read the .ods comment layer and return (long_df, n_unmapped).

    long_df columns: well, month (Timestamp, YYYY-MM-01), state, dry_depth_m.
    Only comments that resolve to a (well, month) cell and a coverage state are
    returned; sitewide notes and well-metadata comments are counted in
    n_unmapped and dropped.
    """
    # Local imports keep odfpy optional for consumers that only read the CSV.
    from odf.opendocument import load
    from odf.table import Table, TableRow, TableCell
    from odf.office import Annotation

    doc = load(str(ods_path))
    tbl = next(
        t for t in doc.spreadsheet.getElementsByType(Table)
        if t.getAttribute("name") == sheet
    )

    def _all_text(node):
        return "".join(
            c.data if c.nodeType == 3 else _all_text(c) for c in node.childNodes
        )

    # Walk the table tracking repeated rows/columns so coordinates stay correct.
    annotations = []
    r = 0
    for row in tbl.getElementsByType(TableRow):
        rep_r = int(row.getAttribute("numberrowsrepeated") or 1)
        c = 0
        for cell in row.getElementsByType(TableCell):
            rep_c = int(cell.getAttribute("numbercolumnsrepeated") or 1)
            for ann in cell.getElementsByType(Annotation):
                txt = _all_text(ann).strip()
                if txt:
                    annotations.append((r, c, txt))
            c += rep_c
        r += rep_r

    grid = pd.read_excel(ods_path, sheet_name=sheet, engine="odf", header=None)

    def _col_date(col):
        v = grid.iat[_DATE_HEADER_ROW, col] if col < grid.shape[1] else None
        return v if isinstance(v, (pd.Timestamp, datetime.datetime)) else None

    def _row_well(row):
        v = grid.iat[row, _WELL_ID_COL] if row < grid.shape[0] else None
        return str(v).strip().lower() if isinstance(v, str) else None

    records, n_unmapped = [], 0
    for (rr, cc, raw) in annotations:
        cleaned = _strip_author(raw)
        state = classify_comment(cleaned)
        well = _row_well(rr)
        date = _col_date(cc)
        if state is None or well is None or date is None:
            n_unmapped += 1
            continue
        depth = parse_dry_depth(cleaned) if state == "dry" else None
        records.append((well, _bucket_to_month(date), state, depth))

    long_df = pd.DataFrame(records, columns=["well", "month", "state", "dry_depth_m"])
    # Last comment wins for a given (well, month); flooded outranks dry outranks
    # the obstruction states if duplicates of differing severity occur.
    if not long_df.empty:
        priority = {"flooded": 0, "dry": 1, "not_found": 2, "inaccessible": 3}
        long_df["_p"] = long_df["state"].map(priority)
        long_df = (
            long_df.sort_values("_p")
            .drop_duplicates(["well", "month"], keep="first")
            .drop(columns="_p")
            .sort_values(["well", "month"])
            .reset_index(drop=True)
        )
    return long_df, n_unmapped


# ── public: assemble the full coverage grid ──────────────────────────────────
def assemble_observation_states(maod: pd.DataFrame, comment_long: pd.DataFrame,
                                provenance: pd.DataFrame = None,
                                dry_season_months=DRY_SEASON_MONTHS):
    """Build a wide month x well grid of observation states.

    Parameters
    ----------
    maod : DataFrame
        Cleaned per-well levels (index = month, columns = wells). Presence of a
        value -> candidate 'measured'; absence is resolved by the comment layer
        and the two inference rules below.
    comment_long : DataFrame
        Output of parse_comment_states (well, month, state, dry_depth_m).
    provenance : DataFrame, optional
        Same shape as maod, values in {measured, interpolated, missing}. Used to
        protect genuinely measured readings: a dry / not_found / inaccessible
        comment overrides only a BLANK or INTERPOLATED cell (the field note is
        authoritative over a fabricated or absent value), never a genuine
        measurement. Where such a comment collides with a measured value the
        measurement is kept and the collision is reported as a conflict for the
        author to adjudicate. If provenance is None, any valued cell is treated
        as measured (conservative: never override a value).
    dry_season_months : iterable[int]

    Returns
    -------
    (states, conflicts) : (DataFrame, DataFrame)
        states  -- wide grid drawn from {measured, interpolated, dry_recorded,
                   dry_inferred, flooded, not_found, inaccessible, not_read,
                   outside_record}.
        conflicts -- long table [well, month, comment_state, kept_value] of
                   comments that collided with a genuine measurement.

    State precedence per cell:
        flooded comment (always)  >  dry comment on a non-measured cell  >
        not_found/inaccessible (value present -> interpolated if a single-month
        gap, else the obstruction state; no value -> the obstruction state)  >
        measured / interpolated value  >  inferred-dry (dry-season blank, or
        blank inside a missing-run that contains a recorded dry)  >  not_read  >
        outside_record.
    """
    months = maod.index
    wells = list(maod.columns)
    cstate = {
        (str(w).lower(), m): s
        for w, m, s in comment_long[["well", "month", "state"]].itertuples(index=False)
    }
    state = pd.DataFrame(index=months, columns=wells, dtype=object)
    conflicts = []

    def _is_measured(col, m):
        """True iff the cell holds a genuine measurement (not blank, not bridged)."""
        if pd.isna(maod.at[m, col]):
            return False
        if provenance is None:
            return True
        if col in provenance.columns and m in provenance.index:
            return provenance.at[m, col] == "measured"
        return True

    for col in wells:
        wl = str(col).lower()
        series = maod[col]
        observed = series.dropna().index
        if len(observed):
            first, last = observed.min(), observed.max()
        else:
            first = last = None

        base = []
        n_months = len(months)
        for i_m, m in enumerate(months):
            cs = cstate.get((wl, m))
            if cs == "flooded":
                base.append("flooded")  # estimated flood entries are intended
            elif cs == "dry":
                # A dry note is qualitative: mark dry only where there is NO
                # measurement. Where a genuine reading exists (well held water
                # near the base) keep it and log the collision for review.
                if _is_measured(col, m):
                    conflicts.append((col, m, cs, float(series.loc[m])))
                    base.append("measured")
                else:
                    base.append("dry_recorded")
            elif cs in ("not_found", "inaccessible"):
                # The well could not be located / read, so any value here is an
                # ESTIMATE, not a measurement. Mimic the pipeline: interpolate an
                # isolated single-month gap (both neighbours present), otherwise
                # leave it not-measured (the obstruction state).
                if pd.isna(series.loc[m]):
                    base.append(cs)
                else:
                    prev_has = i_m > 0 and not pd.isna(series.iloc[i_m - 1])
                    next_has = i_m < n_months - 1 and not pd.isna(series.iloc[i_m + 1])
                    base.append("interpolated" if (prev_has and next_has) else cs)
            elif not pd.isna(series.loc[m]):
                # bridged single-month gaps are flagged distinctly from genuine
                # measurements so the figure shows where interpolation was used.
                if (provenance is not None and col in provenance.columns
                        and m in provenance.index
                        and provenance.at[m, col] == "interpolated"):
                    base.append("interpolated")
                else:
                    base.append("measured")
            else:
                base.append(None)  # resolve in pass 2

        # pass 2: resolve blanks with block-fill + dry-season inference
        n = len(months)
        within = lambda m: (first is not None) and (first <= m <= last)
        j = 0
        while j < n:
            if base[j] is None and within(months[j]):
                k = j
                while k < n and base[k] is None and within(months[k]):
                    k += 1
                run = range(j, k)
                # a recorded dry adjacent to, or inside, the run seeds block-fill
                seeded = (
                    (j > 0 and base[j - 1] in ("dry_recorded", "dry_inferred"))
                    or (k < n and base[k] in ("dry_recorded", "dry_inferred"))
                    or any(cstate.get((wl, months[b])) == "dry" for b in run)
                )
                for b in run:
                    if months[b].month in dry_season_months or seeded:
                        base[b] = "dry_inferred"
                    else:
                        base[b] = "not_read"
                j = k
            else:
                if base[j] is None:
                    base[j] = "outside_record"
                j += 1

        state[col] = base

    conflicts_df = pd.DataFrame(
        conflicts, columns=["well", "month", "comment_state", "kept_value"]
    )
    return state, conflicts_df
