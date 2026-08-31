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

__version__ = "1.4.0"  # Hollingham (2026) — 2026-08-31. Adds the run_id
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

def write_initial_site_observations():
    """Create ``pipeline_site_observations.csv`` with placeholder rows.

    Called by Script 01 near the start of the pipeline.  Always
    overwrites any existing file (the producer scripts re-populate
    their rows downstream).

    All known observations are written with ``source="defaults"``,
    ``producer_script`` set to the registered producer, and the
    registered default value.  Producers will overwrite their rows
    later in the pipeline via ``update_site_observation()``.

    Returns
    -------
    path : pathlib.Path
        Path to the written CSV.
    """
    rows = []
    today = date.today().isoformat()
    token, _ = _run_token()
    for key, meta in _KNOWN_OBSERVATIONS.items():
        rows.append({
            "observation":     key,
            "value":           meta["default"],
            "unit":            meta["unit"],
            "source":          "defaults",
            "producer_script": meta["producer"],
            "description":     meta["description"],
            "updated":         today,
            "run_id":          token,
        })
    df = pd.DataFrame(rows, columns=[
        "observation", "value", "unit",
        "source", "producer_script", "description", "updated", "run_id"
    ])
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
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

    df = pd.read_csv(path)
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

    df.to_csv(path, index=False)


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

    df = pd.read_csv(path)
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
    return pd.read_csv(path)
