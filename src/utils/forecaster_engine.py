#!/usr/bin/env python3
"""
forecaster_engine — emit the forecast-engine constants as a hash-gated feed.

The Well Logger app (newbroman/Newborough_welllogger) reads the forecast
constants live from raw.githubusercontent rather than carrying a baked copy
that drifts. This writes that feed.

The feed is the *engine subset* of the 11b DATA bundle — the fields the
forecast maths actually reads — with the heavy DEM base_layer excluded:

    cluster_coeffs, block_tf, P_clim, PET_clim, winter_climatology_mm, wells

WHY THIS LIVES IN src/utils/ AND NOT IN living/

  The first draft put it in living/ and hooked it with a bare
  `from emit_forecaster_engine import emit_engine` inside Script 11b. That
  raises ModuleNotFoundError: 11b runs with sys.path[0] = src/, living/ is not
  on the path, and NO src/ script imports from living/ anywhere in this project
  — msl_common.py is imported only within the living lane. living/ is a
  separate lane (D-063) and it holds data and its own scripts, not modules the
  pipeline imports. So the code sits here, with every other shared module, and
  only its OUTPUT lands in living/, which is correct: the feed is a living
  artefact. The path comes from paths.py like all other I/O.

HASH-GATING, AND ITS LIMIT

  The file is rewritten only when the content hash of the engine subset moves,
  so no-op runs produce no commit and `last_changed` records when the forecast
  basis actually shifted. That is the granularity a monthly "has it changed?"
  check wants.

  THE LIMIT IS IN `wells`. The subset includes the 88 well objects, and each
  carries a twelve-month per-well climatology derived from the reading record.
  That moves whenever new readings land — so the hash moves roughly monthly,
  not only on a genuine SSM refit. `last_changed` therefore answers "did
  anything the app reads move?", which is the honest reading of it, and NOT
  "did the SSM refit". Splitting the well block into its own feed would
  recover the stronger property; that is a design question, not a defect, and
  it is recorded in the changelog rather than silently assumed away.

Hook in 11b (build_forecaster_html, just after the bundle is built):

    from utils.forecaster_engine import emit_engine
    bundle = _build_forecaster_data_bundle()
    emit_engine(bundle)

Bootstrap / verify from an already-rendered forecaster.html (path or URL):

    python3 src/utils/forecaster_engine.py --from-html outputs/11b_spatial_thresholds/forecaster.html

__version__ : 1.1.0
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-08-29. _hash() now
#   normalises through the serialised form before hashing. Integer month keys
#   sort numerically in memory and lexicographically after a JSON round-trip,
#   so a live run and any reader of the file hashed different canonical strings
#   for identical content — the gate could never report "unchanged" to the
#   standalone check it was built for. Found by running 11b and then
#   --from-html on that run's own output.
# v1.1.0  # Hollingham (2026) — 2026-08-29. Moved from
#   living/emit_forecaster_engine.py, where the documented 11b hook could not
#   import it. Output path now comes from paths.py. Logic unchanged.
import json
import hashlib
import datetime
from pathlib import Path

ENGINE_KEYS = ("cluster_coeffs", "block_tf", "P_clim",
               "PET_clim", "winter_climatology_mm", "wells")
SCHEMA = "nw-engine-1"

# All I/O via paths.py. The feed is a LIVING artefact: the code is pipeline
# code, its output is not a pipeline output.
try:                                    # imported as utils.forecaster_engine
    from utils.paths import LIVING_FORECASTER_ENGINE as DEFAULT_OUT
except ImportError:                     # run directly: python3 src/utils/...
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.paths import LIVING_FORECASTER_ENGINE as DEFAULT_OUT


def _engine_subset(bundle: dict) -> dict:
    return {k: bundle[k] for k in ENGINE_KEYS if k in bundle}


def _hash(subset: dict) -> str:
    """Content hash of the engine subset, stable across a JSON round-trip.

    THE ROUND-TRIP IS THE POINT, and getting it wrong made the gate useless in
    exactly the check it exists for. The month dictionaries (P_clim, PET_clim,
    each well's monthly_clim) are built with INTEGER keys. `sort_keys=True`
    orders those numerically — 1, 2, ... 12. Serialising to JSON turns every
    key into a string, and on the way back they sort lexicographically —
    "1", "10", "11", "12", "2", ... So a live run hashing the in-memory bundle
    and anything re-reading the file hash DIFFERENT canonical strings for
    identical content, and can never agree.

    Measured on 2026-08-29: an 11b run stamped d721b924cc5c8d77 while the file
    it had just written hashed to 07b23367e042cb6b, and `--from-html` on that
    same run's own forecaster.html reported "engine constants CHANGED" against
    a feed whose content was byte-identical.

    So normalise through the serialised form FIRST — which coerces keys to
    strings and numpy scalars to whatever `default` gives — and hash that.
    """
    canon = json.loads(json.dumps(subset, default=str))
    return hashlib.sha256(
        json.dumps(canon, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")).hexdigest()[:16]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def emit_engine(bundle: dict, out_path: Path | str | None = None) -> Path:
    """Write the engine feed, gated on the engine-subset content hash.

    Returns the output path. Prints a one-line console note (unchanged /
    written) so the weekly pipeline log shows when the basis last moved.
    """
    out = Path(out_path) if out_path else DEFAULT_OUT
    subset = _engine_subset(bundle)
    h = _hash(subset)

    prev_changed = None
    if out.exists():
        try:
            prev = json.loads(out.read_text(encoding="utf-8"))
            if prev.get("hash") == h:
                print(f"[emit_forecaster_engine] engine constants unchanged "
                      f"since {prev.get('last_changed', '?')} (hash {h}); no rewrite.")
                return out
            prev_changed = prev.get("last_changed")
        except Exception:
            pass  # unreadable prior -> treat as changed

    now = _now()
    payload = {
        "generated": now,
        "last_changed": now,           # hash moved -> this IS the change time
        "hash": h,
        "schema": SCHEMA,
        "source": "11b_spatial_thresholds DATA (base_layer excluded)",
    }
    payload.update(subset)
    out.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
    if prev_changed:
        print(f"[emit_forecaster_engine] engine constants CHANGED "
              f"(was {prev_changed}); wrote {out.name} (hash {h}).")
    else:
        print(f"[emit_forecaster_engine] wrote {out.name} (hash {h}).")
    return out


def _bundle_from_html(text: str) -> dict:
    """Extract the injected `const DATA = {...};` object from a rendered page."""
    import re
    m = re.search(r"(?:const|let|var)\s+DATA\s*=\s*", text)
    if not m:
        raise ValueError("no `DATA =` assignment found")
    i = text.index("{", m.end())
    depth, j = 0, i
    while j < len(text):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return json.loads(text[i:j + 1])


if __name__ == "__main__":
    import argparse
    import urllib.request
    ap = argparse.ArgumentParser(description="Emit / verify the forecaster engine feed.")
    ap.add_argument("--from-html", metavar="PATH_OR_URL",
                    help="Bootstrap the feed from an already-rendered forecaster.html")
    ap.add_argument("--out", default=None, help="Output path (default living/forecaster_engine.json)")
    args = ap.parse_args()
    if args.from_html:
        src = args.from_html
        if src.startswith("http"):
            text = urllib.request.urlopen(src, timeout=60).read().decode("utf-8", "replace")
        else:
            text = Path(src).read_text(encoding="utf-8")
        emit_engine(_bundle_from_html(text), args.out)
    else:
        ap.error("nothing to do: pass --from-html for standalone use, "
                 "or import emit_engine() from Script 11b.")
