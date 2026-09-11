"""
utils/site_observations.py
==========================
Registry and accessor module for **site-wide** pipeline-produced
observations — empirical values that are not per-cluster and so do not
fit the schema of ``pipeline_scenario_params.csv``.

Examples include single-well BACI step values (e.g. CEH36 vs CEH4 at
Pure_Scraping), site-aggregate water-balance quantities (e.g. long-term
annual P − PET), and other one-off observations that downstream scripts
may want to consume as a single number rather than re-derive.

Architecture
------------
Mirrors ``utils/pipeline_params.py`` (the per-cluster sibling).

Producer scripts call ``update_site_observation()`` after computing each
value::

    update_site_observation("ceh36_baci_pure_scraping",
                            value=0.1314,
                            producer_script="09a")

Consumer scripts call ``load_site_observation()`` to retrieve the value::

    from utils.site_observations import load_site_observation
    baci_step = load_site_observation("ceh36_baci_pure_scraping")

Script 01 calls ``write_initial_site_observations()`` once, near the
start of the pipeline, to create the file with placeholder rows
(``source="defaults"``).  Producers overwrite their rows with
``source="pipeline"`` once their values are computed.  Consumers will
return the defaults value even if no producer has updated it, but emit
a one-line warning so the user knows a second pipeline pass is needed
to settle.

File location
-------------
``outputs/01_data_prep/pipeline_site_observations.csv``

Schema (long format, one row per observation)::

    observation       (str)   snake_case key, unique
    value             (float) the observation
    unit              (str)   "m", "m/yr", etc.
    source            (str)   "pipeline" or "defaults"
    producer_script   (str)   e.g. "09a", "16"
    description       (str)   human-readable one-liner
    updated           (str)   ISO date of last write
    run_id            (str)   which pipeline pass wrote this row —
                              "run:<stamp>-<hex>" from NRG_RUN_ID, or
                              "standalone:<ISO timestamp>" if the writer was
                              called outside a run.  See _run_token().

Adding a new observation
------------------------
1. Add a new entry to ``_KNOWN_OBSERVATIONS`` below with default, unit,
   producer, and description.
2. In the producer script, after computing the value, call
   ``update_site_observation(key, value, producer_script="<id>")``.
3. In the consumer script(s), call ``load_site_observation(key)``.
4. Run the full pipeline at least twice so the second pass picks up
   pipeline-sourced values rather than defaults.
"""

__version__ = "1.6.0"  # Hollingham (2026) - 2026-09-11. write_initial_site_
#   observations() FILLS GAPS, IT NO LONGER RESETS THE STORE (Martin,
#   2026-09-11; D-158). It used to rebuild the file from _KNOWN_OBSERVATIONS on
#   every call, with every value set to its registered DEFAULT and every source
#   to "defaults". Script 01 calls it near the start of a pass, so in a FULL
#   pass the damage was invisible: 09a, 10j, 10k, 10l and the rest re-ran
#   afterwards and overwrote their own rows. Run Script 01 ALONE — as happened
#   on 2026-09-11 — and the store was silently gutted: 15 rows of committed
#   pipeline results replaced by placeholders, among them
#   impact_vs_edge_clearfell_monthly_step 0.0653363682133117 -> 0.063 and four
#   four_zone rows set to 0.0. It read as a successful run.
#
#   Now: a missing file is created exactly as before; an existing file keeps
#   EVERY existing row's value, source, updated and run_id, and only gains rows
#   for registered observations it lacks. The registry-owned METADATA columns
#   (unit, producer_script, description) ARE refreshed from _KNOWN_OBSERVATIONS,
#   because the registry is their authority and a stale description in this file
#   is reviewer-facing; the count of refreshed rows is reported rather than
#   done quietly. A row in the store that is no longer registered is KEPT and
#   warned about — deleting a measured value because its registry entry was
#   renamed is the same class of loss this change exists to prevent.
# v1.5.0  # Hollingham (2026) - 2026-09-11. EXACT ROUND TRIP.
#   EVERY read and write of this store goes through utils/store_io (D-157).
#   This file writes ONE row by reading the whole store and writing the whole
#   store back, and pandas' default C float parser is not correctly rounded, so
#   each write silently moved every OTHER row by up to a few ULP while leaving
#   that row's `updated` and `run_id` asserting it came from an earlier run.
#   Measured 2026-09-11: the next write under the old code would have changed 1
#   line of pipeline_site_observations.csv and 5 of pipeline_scenario_params.csv
#   with nothing recomputed. read_store() parses with float_precision=
#   "round_trip", so a read-modify-write is exact for every untouched row.
# v1.4.0  # Hollingham (2026) — 2026-08-31. Adds the run_id
#   column and the standalone-run guard (D-101). This file is RUN-SCOPED:
#   write_initial_site_observations() resets it to placeholders near the start
#   of each pass and seven producers overwrite their own rows, so a producer run
#   OUTSIDE a pass leaves a file that mixes two runs with nothing recording that
#   it does. Both writers now stamp run_id from the ENVIRONMENT (NRG_RUN_ID, set
#   by run_analysis.py before it launches anything) and NEVER from the file:
#   reading the existing token and writing it back would let a standalone write
#   inherit the previous pass's token, which is the defect, not the fix. With no
#   token in the environment the row is marked "standalone:<ISO timestamp>" and
#   update_site_observation() warns. It WARNS, it does not refuse — running a
#   single script is normal debugging practice here, and this project's culture
#   is gates that report rather than locks that prevent. The gate is
#   tools/pipeline_lint.py --check runid.
#
# v1.3.0  # Hollingham (2026) — 2026-05-22
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import os
from datetime import date, datetime

import pandas as pd

from utils.store_io import read_store, write_store


# ============================================================================
# OBSERVATION REGISTRY
# ============================================================================
# Master list of recognised site-wide observations.  Every observation
# that flows through this module must appear here.  This makes the
# schema explicit (vs implicit / appendable-at-will) and lets the
# loader / updater validate keys at call time.
#
# Defaults are best-guess placeholders used when the producer script
# has not yet run.  They should be roughly the right order of magnitude
# so that any consumer that fires before a fresh pipeline run produces
# sane (if approximate) results.

_KNOWN_OBSERVATIONS = {
    "ceh36_baci_pure_scraping": {
        "default": 0.131,
        "unit": "m",
        "producer": "09a",
        "description": "CEH36 paired BACI step (Pure_Scraping era, vs CEH4)",
    },
    "ceh36_baci_felling_pulse": {
        "default": 0.024,
        "unit": "m",
        "producer": "09a",
        "description": "CEH36 paired BACI step (Felling_Pulse era, vs CEH4)",
    },
    "site_p_minus_pet_annual": {
        "default": 0.232,
        "unit": "m/yr",
        "producer": "16",
        "description": "Long-term annual P − PET (water balance, RAF Valley)",
    },
    "impact_vs_edge_clearfell_monthly_step": {
        "default": 0.063,
        "unit": "m",
        "producer": "10j",
        "description": "Direct Impact-vs-Edge BACI contrast — monthly differential felling step (Impact − Edge, CWB-corrected, well-FE, cluster-robust)",
    },
    "impact_vs_edge_clearfell_monthly_step_se": {
        "default": 0.017,
        "unit": "m",
        "producer": "10j",
        "description": "Standard error of impact_vs_edge_clearfell_monthly_step",
    },
    "impact_vs_edge_clearfell_summer_step": {
        "default": 0.0,
        "unit": "m",
        "producer": "10j",
        "description": "Direct Impact-vs-Edge BACI contrast — annual Jun–Sep minimum differential felling step (Impact − Edge, well-FE, cluster-robust)",
    },
    "impact_vs_edge_clearfell_summer_step_se": {
        "default": 0.05,
        "unit": "m",
        "producer": "10j",
        "description": "Standard error of impact_vs_edge_clearfell_summer_step",
    },
    "four_zone_clearfell_step_impact": {
        "default": 0.033,
        "unit": "m",
        "producer": "10k",
        "description": "Four-zone pooled-panel BACI — Impact-vs-Forest differential felling step (monthly, well-FE, cluster-robust, zone-interacted CWB). Headline felling response.",
    },
    "four_zone_clearfell_step_edge": {
        "default": -0.031,
        "unit": "m",
        "producer": "10k",
        "description": "Four-zone pooled-panel BACI — Edge-vs-Forest differential felling step (monthly, well-FE, cluster-robust).",
    },
    "four_zone_clearfell_step_c3warren": {
        "default": 0.0,
        "unit": "m",
        "producer": "10k",
        "description": "Four-zone pooled-panel BACI — C3/Warren-vs-Forest differential felling step. C3/Warren is a second control zone; this step is expected to be ~0 and a clearly non-zero value is a flag, not a felling finding.",
    },
    "four_zone_summer_step_impact": {
        "default": 0.0,
        "unit": "m",
        "producer": "10l",
        "description": "Four-zone summer-minima BACI — Impact-vs-Forest differential felling step on the annual Jun–Sep minimum (well-FE, cluster-robust, 2011 balanced cutoff, no scraping/CWB term).",
    },
    "four_zone_summer_step_edge": {
        "default": 0.0,
        "unit": "m",
        "producer": "10l",
        "description": "Four-zone summer-minima BACI — Edge-vs-Forest differential felling step on the annual Jun–Sep minimum.",
    },
    "four_zone_summer_step_c3warren": {
        "default": 0.0,
        "unit": "m",
        "producer": "10l",
        "description": "Four-zone summer-minima BACI — C3/Warren-vs-Forest differential felling step on the annual Jun–Sep minimum. C3/Warren is a second control zone; this step is expected to be ~0 and a clearly non-zero value is a flag, not a felling finding.",
    },
    "four_zone_spring_step_impact": {
        "default": 0.0,
        "unit": "m",
        "producer": "10l",
        "description": "Four-zone spring-mean BACI — Impact-vs-Forest differential felling step on the annual Mar–May mean (well-FE, cluster-robust, 2011 balanced cutoff, no scraping/CWB term).",
    },
    "four_zone_spring_step_edge": {
        "default": 0.0,
        "unit": "m",
        "producer": "10l",
        "description": "Four-zone spring-mean BACI — Edge-vs-Forest differential felling step on the annual Mar–May mean.",
    },
    "four_zone_spring_step_c3warren": {
        "default": 0.0,
        "unit": "m",
        "producer": "10l",
        "description": "Four-zone spring-mean BACI — C3/Warren-vs-Forest differential felling step on the annual Mar–May mean. C3/Warren is a second control zone; this step is expected to be ~0 and a clearly non-zero value is a flag, not a felling finding.",
    },
}


# ============================================================================
# RUN TOKEN — the interlock
# ============================================================================

RUN_ID_ENV = "NRG_RUN_ID"
STANDALONE_PREFIX = "standalone:"
RUN_PREFIX = "run:"


def _run_token():
    """Return (token, is_standalone) for the CURRENT process.

    THE SOURCE OF THE TOKEN IS THE WHOLE MECHANISM, so it is worth being
    explicit about what is deliberately NOT done here.

    ``run_analysis.py`` sets ``NRG_RUN_ID`` once, at the top of ``main()``,
    before it launches anything; steps run as subprocesses, so every child
    inherits it. This function reads THAT, and never the ``run_id`` already in
    ``pipeline_site_observations.csv``.

    The file-reading version is the obvious implementation and it is inert. A
    producer run on its own would read the token the previous pass left in the
    file, write it back into its own row, and the resulting mixture would be
    indistinguishable from a clean pass — the pollution would be recorded as
    legitimate by the very column meant to detect it. Reading the environment
    instead means a row can only carry a genuine run token if it was written
    inside a run, which is the property the gate depends on.

    With no token in the environment the writer is outside a pipeline pass, and
    the row is marked so.
    """
    token = os.environ.get(RUN_ID_ENV, "").strip()
    if token:
        return token, False
    return f"{STANDALONE_PREFIX}{datetime.now().isoformat(timespec='seconds')}", True


# ============================================================================
# PATH HELPER
# ============================================================================

def _path():
    """Return the path to the pipeline site observations CSV."""
    from utils.paths import DIR_01
    return DIR_01 / "pipeline_site_observations.csv"


# ============================================================================
# WRITER — called by Script 01
# ============================================================================

COLUMNS = ["observation", "value", "unit", "source", "producer_script",
           "description", "updated", "run_id"]

#: Columns the REGISTRY owns, and may refresh on an existing row. `value`,
#: `source`, `updated` and `run_id` are owned by whichever producer last wrote
#: the row and are never touched here.
_REGISTRY_OWNED = ("unit", "producer_script", "description")


def _default_row(key, meta, today, token):
    return {"observation":     key,
            "value":           meta["default"],
            "unit":            meta["unit"],
            "source":          "defaults",
            "producer_script": meta["producer"],
            "description":     meta["description"],
            "updated":         today,
            "run_id":          token}


def write_initial_site_observations():
    """Ensure every registered observation has a row. Fill gaps; reset nothing.

    Called by Script 01 near the start of a pass. Until 1.6.0 this rebuilt the
    file from `_KNOWN_OBSERVATIONS` every time, so every producer's value was
    replaced by its registered default and every `source` by "defaults". In a
    full pass that was invisible — the producers re-ran afterwards. Run Script 01
    alone and the store was gutted without a word (D-158).

    So: a missing file is created with default rows, as before. An EXISTING file
    keeps every row's `value`, `source`, `updated` and `run_id` exactly as it
    found them, and gains a default row for each registered observation it
    lacks. The registry-owned metadata columns are refreshed, and a row whose
    observation is no longer registered is kept and warned about.

    Returns
    -------
    path : pathlib.Path
        Path to the written CSV.
    """
    from utils.console_utils import info as _info, warn as _warn

    today = date.today().isoformat()
    token, _ = _run_token()
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        df = pd.DataFrame(
            [_default_row(k, m, today, token)
             for k, m in _KNOWN_OBSERVATIONS.items()], columns=COLUMNS)
        write_store(df, path)
        _info(f"{path.name}: created with {len(df)} default row(s)")
        return path

    df = read_store(path)
    for col in COLUMNS:
        if col not in df.columns:
            # A file from a pass that predates the column. "unstamped" rather
            # than back-filled with this call's token, which would assert that
            # this run produced rows it did not.
            df[col] = "unstamped:pre-column" if col == "run_id" else ""

    have = set(df["observation"].astype(str))
    added = [_default_row(k, m, today, token)
             for k, m in _KNOWN_OBSERVATIONS.items() if k not in have]
    if added:
        df = pd.concat([df, pd.DataFrame(added, columns=COLUMNS)],
                       ignore_index=True)

    # Registry-owned metadata only. Counted and reported, never silent: a
    # description that changes under a committed value is worth one line.
    refreshed = 0
    for i, key in df["observation"].astype(str).items():
        meta = _KNOWN_OBSERVATIONS.get(key)
        if meta is None:
            continue
        for col, val in (("unit", meta["unit"]),
                         ("producer_script", meta["producer"]),
                         ("description", meta["description"])):
            if str(df.at[i, col]) != str(val):
                df.at[i, col] = val
                refreshed += 1

    unregistered = sorted(set(df["observation"].astype(str))
                          - set(_KNOWN_OBSERVATIONS))
    # Registry order first, then anything unregistered, so the file reads as the
    # registry does and an orphan is visible at the end rather than buried.
    order = {k: n for n, k in enumerate(_KNOWN_OBSERVATIONS)}
    df["_ord"] = df["observation"].astype(str).map(
        lambda k: order.get(k, len(order)))
    df = df.sort_values("_ord", kind="stable").drop(columns="_ord")
    df = df[COLUMNS]

    write_store(df, path)
    kept = len(df) - len(added)
    _info(f"{path.name}: {kept} existing row(s) left untouched, "
          f"{len(added)} gap(s) filled"
          + (f", {refreshed} metadata field(s) refreshed from the registry"
             if refreshed else ""))
    for row in added:
        _info(f"    added {row['observation']} at its registered default "
              f"({row['value']}) — its producer ({row['producer_script']}) has "
              f"not run yet")
    if unregistered:
        _warn(f"{path.name} holds {len(unregistered)} observation(s) no longer "
              f"in _KNOWN_OBSERVATIONS: {', '.join(unregistered)}. They are "
              f"KEPT — a measured value is not deleted because its registry "
              f"entry was renamed. Re-register or remove them deliberately.")
    return path


# ============================================================================
# UPDATER — called by producer scripts after computing each value
# ============================================================================

def update_site_observation(observation, value, producer_script,
                            *, source="pipeline"):
    """Update a single observation row in the site-observations CSV.

    Parameters
    ----------
    observation : str
        Registered key from ``_KNOWN_OBSERVATIONS`` (e.g.
        ``"ceh36_baci_pure_scraping"``).
    value : float
        The computed value.
    producer_script : str
        Identifier of the script doing the update (e.g. ``"09a"``).
        Recorded in the row for provenance.
    source : str, optional
        Defaults to ``"pipeline"``.  Use ``"defaults"`` only for
        writer-side seeding (not normally called by producer code).

    Raises
    ------
    KeyError
        If ``observation`` is not registered in ``_KNOWN_OBSERVATIONS``.

    Notes
    -----
    If the registry CSV does not yet exist, this function auto-creates
    it (by calling ``write_initial_site_observations()`` internally)
    before updating the row.  Producer scripts are therefore robust to
    being run in any order — Script 01 is not a hard prerequisite.
    Consumers (``load_site_observation()``) still require the registry
    to exist; they fail with FileNotFoundError if it's missing.
    """
    if observation not in _KNOWN_OBSERVATIONS:
        raise KeyError(
            f"Unknown site observation '{observation}'.  "
            f"Registered keys: {sorted(_KNOWN_OBSERVATIONS)}.  "
            f"To add a new one, edit _KNOWN_OBSERVATIONS in "
            f"utils/site_observations.py.")

    # From the environment, never from the file — see _run_token().
    token, standalone = _run_token()
    if standalone:
        # WARN, DO NOT REFUSE. Running one producer on its own is normal
        # practice here and blocking it would make debugging materially worse.
        # What is not acceptable is doing it SILENTLY: this file is run-scoped,
        # so the row just written belongs to a different run from every row
        # around it, and without this line nothing says so.
        from utils.console_utils import warn as _warn
        _warn(f"site_observations: '{observation}' is being written OUTSIDE a "
              f"pipeline run ({RUN_ID_ENV} is unset). The row will be marked "
              f"'{token}', and {_path().name} now mixes this write with "
              f"whatever the last full pass left. Re-run the pipeline before "
              f"trusting or committing it "
              f"(tools/pipeline_lint.py --check runid).")

    path = _path()
    if not path.exists():
        # Auto-bootstrap: producer script is updating a value before
        # Script 01 has run (or in a partial pipeline pass that skipped
        # Script 01).  Create the registry from _KNOWN_OBSERVATIONS
        # with defaults, then this call's update lands on top of the
        # default row for `observation`.  Producer scripts should not
        # crash because of a missing registry — that's a consumer
        # concern.
        write_initial_site_observations()

    df = read_store(path)
    if "run_id" not in df.columns:
        # A file left by a pass that predates this guard. The other rows'
        # provenance is genuinely unknown and must not be guessed: they are
        # marked as such rather than back-filled with this write's token, which
        # would assert that one run produced all of them.
        df["run_id"] = "unstamped:pre-guard"
    mask = df["observation"] == observation
    if not mask.any():
        # Row missing — append (defends against partial CSVs from older runs)
        meta = _KNOWN_OBSERVATIONS[observation]
        new_row = pd.DataFrame([{
            "observation":     observation,
            "value":           value,
            "unit":            meta["unit"],
            "source":          source,
            "producer_script": producer_script,
            "description":     meta["description"],
            "updated":         date.today().isoformat(),
            "run_id":          token,
        }])
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        df.loc[mask, "value"]           = value
        df.loc[mask, "source"]          = source
        df.loc[mask, "producer_script"] = producer_script
        df.loc[mask, "updated"]         = date.today().isoformat()
        df.loc[mask, "run_id"]          = token

    write_store(df, path)


# ============================================================================
# LOADER — called by consumer scripts
# ============================================================================

# Warnings issued only once per key per process to avoid log spam
_warned_defaults = set()


def load_site_observation(observation):
    """Return the float value of a single registered observation.

    Parameters
    ----------
    observation : str
        Registered key from ``_KNOWN_OBSERVATIONS``.

    Returns
    -------
    value : float
        The observation value.

    Raises
    ------
    KeyError
        If ``observation`` is not registered.
    FileNotFoundError
        If the site-observations CSV does not yet exist.

    Notes
    -----
    If the observation is still at its default value (because the
    producing script has not yet been run on this clone), the function
    returns the default but prints a one-line warning advising a fresh
    pipeline run.  Each key warns at most once per process.
    """
    row = load_site_observation_row(observation)
    if row["source"] == "defaults" and observation not in _warned_defaults:
        print(f"  [site_observations] WARNING: '{observation}' is at its "
              f"default value ({row['value']} {row['unit']}); "
              f"run Script {row['producer_script']} to refresh.")
        _warned_defaults.add(observation)
    return float(row["value"])


def load_site_observation_row(observation):
    """Return the full row (dict) for a single registered observation.

    Includes value, unit, source, producer_script, description, and
    updated.  Use this when a consumer needs to display provenance or
    quote the observation with its unit.

    Parameters
    ----------
    observation : str
        Registered key from ``_KNOWN_OBSERVATIONS``.

    Returns
    -------
    row : dict
        Keys: ``observation``, ``value``, ``unit``, ``source``,
        ``producer_script``, ``description``, ``updated``.
    """
    if observation not in _KNOWN_OBSERVATIONS:
        raise KeyError(
            f"Unknown site observation '{observation}'.  "
            f"Registered keys: {sorted(_KNOWN_OBSERVATIONS)}.")

    path = _path()
    if not path.exists():
        raise FileNotFoundError(
            f"Site observations CSV not found at {path}.  "
            f"Run Script 01 first (it calls write_initial_site_observations).")

    df = read_store(path)
    mask = df["observation"] == observation
    if not mask.any():
        raise KeyError(
            f"Observation '{observation}' is registered but missing from "
            f"{path.name}.  Re-run Script 01 to re-seed the file.")
    return df.loc[mask].iloc[0].to_dict()


def load_all_site_observations():
    """Return the full site-observations DataFrame.

    Convenience for consumers wanting to inspect or report all values
    at once.

    Returns
    -------
    df : pd.DataFrame
        Long-format DataFrame with the schema documented at the top
        of this module.
    """
    path = _path()
    if not path.exists():
        raise FileNotFoundError(
            f"Site observations CSV not found at {path}.  "
            f"Run Script 01 first (it calls write_initial_site_observations).")
    return read_store(path)
