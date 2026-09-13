#!/usr/bin/env python3
"""A KML that says WHICH SLACKS TO OUTLINE, and deliberately not what is in them.

WHY. Two automated discriminators have failed on the 2026-09-12 tiles — a global
Otsu-z against the open dune, and a local floor-versus-rim contrast — so the
flooded extent on 2021-04-04 is to be digitised by hand (Martin, 2026-09-12). A
thousand hollows is too many to trace and "the glare-affected ones" is not a
defined set, so this tool defines it: every slack is placed in a priority band
and written into its own KML folder, which Google Earth shows as a tick list.

**IT WITHHOLDS THE DIPWELL LEVELS, ON PURPOSE.** A slack is marked as HOLDING a
dipwell, never as holding a wet or a dry one. If the tracing were guided by the
record it is later scored against, the agreement statistic would be circular and
could not be reported as validation. The levels are in the pipeline and they stay
there until the polygons come back.

THE BANDS, in tracing order:

  A  holds a dipwell. These are the only slacks whose tracing can be SCORED, so
     they are worth the most per polygon and are drawn first.
  B  a glare signature in the measured contrast: floor brighter than its own rim
     AND less saturated than it. This is the set Martin identified by eye — the
     sun and clouds reflecting off the pools — named here from the numbers so it
     is reproducible rather than remembered.
  C  a dark signature: floor darker than its own rim. Classical standing water.
  D  everything else. Not expected to hold water; traced only if it plainly does,
     which is itself a finding.

A slack in A may also be in B or C; the description says so. The bands are a
work order, not a classification — nothing here asserts that any slack is wet.
That is what the tracing is for.

Usage:
    python3 tools/digitising_pack.py --date 2021-04-04
    python3 tools/digitising_pack.py --date 2021-04-04 --min-area 200
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) - 2026-09-12. The read's own
#   water outlines are included as their own folder where the date has been
#   read, so the slacks and the classified water can be compared in one
#   view. No band is blue any more — blue asserted the thing the file
#   withholds.
# 1.0.0  Hollingham (2026) - 2026-09-12. New: the digitising work order
#   for the hand-traced flood extent (D-159).

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from utils.console_utils import banner, info, phase, saved, step, warn  # noqa: E402

OUT = REPO / "working" / "updates"
CONTRAST = OUT / "W94_20_slack_contrast.csv"
HOLLOWS = OUT / "W94_06_hollows.geojson"
# The contrast is in units of the rim's own robust spread, so these are not
# thresholds on wetness — they only say which sign the measured difference had.
# A band is a work order; the tracing decides what is water.
SIGN_MIN = 0.25
# KML colour is aabbggrr, not aarrggbb. NO BAND IS BLUE: blue reads as "this is
# water", which is the one claim this file withholds — a band is a work order and
# the tracing decides what is wet. Magenta for the scorable set because nothing
# in a dune scene is magenta; cyan and orange for the two signatures because they
# separate on sand, which yellow against orange did not.
STYLES = {
    "A": ("ffff00ff", "A - holds a dipwell (trace first: these can be scored)"),
    "B": ("ff00a5ff", "B - glare signature (brighter than its rim, less saturated)"),
    "C": ("ffffff00", "C - dark signature (darker than its rim)"),
    "D": ("ffb0b0b0", "D - no signature either way (trace only if plainly wet)"),
}
# The read's OWN water outlines, where that date has been read. Green, and named
# so it cannot be confused with a slack: these are the pipeline's claim about
# where the water was, and the point of putting them in the same file is to see
# where they and the slacks disagree.
FLOOD_COLOUR = "ff00ff00"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument("--min-area", type=float, default=0.0,
                    help="skip slacks smaller than this, m2 (default: all)")
    a = ap.parse_args()
    banner("Digitising work order", __version__)

    import geopandas as gpd
    import pyproj
    from shapely.geometry import Point

    if not HOLLOWS.exists():
        warn(f"{HOLLOWS.name} is missing; phase 6 has not run")
        return 1
    hol = gpd.read_file(HOLLOWS).set_crs("EPSG:27700", allow_override=True)
    hol = hol[hol.geometry.notna() & hol["slack"].notna()].copy()
    hol["slack"] = hol["slack"].astype(int)
    hol["area_m2"] = hol.area
    if a.min_area > 0:
        hol = hol[hol["area_m2"] >= a.min_area]
    info(f"{len(hol)} slack(s) from phase 6")

    phase(1, "which slacks hold a dipwell")
    wells = pd.read_csv(REPO / "outputs" / "01_well_elevations.csv",
                        float_precision="round_trip")
    pts = gpd.GeoDataFrame(
        {"well": wells["Name"].astype(str)},
        geometry=[Point(e, n) for e, n in zip(wells["E"], wells["N"])],
        crs="EPSG:27700")
    # 3.93 m is the vp2 registration residual — the distance within which a well
    # and a slack cannot be told apart by the registration. Used here as the
    # join tolerance for the same reason phase 8 uses it.
    j = gpd.sjoin_nearest(pts, hol[["slack", "geometry"]], max_distance=3.93,
                          how="inner")
    holds = (j.groupby("slack")["well"]
             .apply(lambda s: ", ".join(sorted(set(s)))).to_dict())
    info(f"{len(holds)} slack(s) hold at least one dipwell "
         f"(join tolerance 3.93 m, the vp2 residual)")
    info("  the WET/DRY state of those wells is deliberately NOT in this file")

    phase(2, "the measured contrast, for the band only")
    con = {}
    if CONTRAST.exists():
        c = pd.read_csv(CONTRAST, float_precision="round_trip")
        c = c[c["date"].astype(str) == a.date]
        if len(c):
            con = {int(r.slack): r for r in c.itertuples()}
            info(f"{len(con)} slack(s) measured on {a.date} "
                 f"(phase 10, {CONTRAST.name})")
        else:
            warn(f"  {CONTRAST.name} has no rows for {a.date}; every slack "
                 f"falls in band D")
    else:
        warn(f"  no {CONTRAST.name}; every slack falls in band D")

    def band(sid):
        r = con.get(sid)
        if sid in holds:
            return "A"
        if r is None:
            return "D"
        dL = getattr(r, "dL", None)
        dS = getattr(r, "dS", None)
        if (dL is not None and np.isfinite(dL) and dL >= SIGN_MIN
                and dS is not None and np.isfinite(dS) and dS <= -SIGN_MIN):
            return "B"
        if dL is not None and np.isfinite(dL) and dL <= -SIGN_MIN:
            return "C"
        return "D"

    hol["band"] = [band(s) for s in hol["slack"]]
    step("work order:")
    for b in "ABCD":
        n = int((hol["band"] == b).sum())
        ha = float(hol.loc[hol["band"] == b, "area_m2"].sum()) / 1e4
        info(f"  {STYLES[b][1][:52]:54s} {n:5d} slack(s), {ha:6.1f} ha")

    phase(3, "writing the KML")
    fwd = pyproj.Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    k = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
         f'<name>digitise {a.date}</name>',
         f'<description>Slacks to outline on {a.date}. Bands are a WORK ORDER, '
         'not a classification: nothing here asserts that a slack is wet. '
         'Dipwell levels are withheld so the tracing stays independent of the '
         'record it will be scored against.</description>']
    for b, (colour, label) in STYLES.items():
        k.append(f'<Style id="b{b}"><LineStyle><color>{colour}</color>'
                 f'<width>2</width></LineStyle>'
                 f'<PolyStyle><fill>0</fill></PolyStyle></Style>')
    for b in "ABCD":
        g = hol[hol["band"] == b]
        if not len(g):
            continue
        k.append(f'<Folder><name>{STYLES[b][1]}</name>'
                 f'<open>{1 if b == "A" else 0}</open>')
        for _, r in g.sort_values("area_m2", ascending=False).iterrows():
            sid = int(r["slack"])
            c_ = con.get(sid)
            bits = [f"slack {sid}", f"{r['area_m2']:.0f} m2"]
            if sid in holds:
                bits.append(f"dipwell(s): {holds[sid]}")
            if c_ is not None:
                bits.append(f"dL {getattr(c_, 'dL', float('nan')):+.2f} "
                            f"dBR {getattr(c_, 'dBR', float('nan')):+.2f} "
                            f"dS {getattr(c_, 'dS', float('nan')):+.2f} "
                            f"(tile {getattr(c_, 'tile', '?')}, "
                            f"{getattr(c_, 'gsd_m', float('nan')):.2f} m/px)")
            geoms = (list(r.geometry.geoms)
                     if r.geometry.geom_type == "MultiPolygon" else [r.geometry])
            for poly in geoms:
                # The hollow polygons carry a Z ordinate (they come off the
                # DEM), so only the first two are taken — unpacking a 3-tuple
                # into two names is the error this replaces.
                cc = [(c[0], c[1]) for c in poly.exterior.coords]
                ll = [fwd.transform(x, y) for x, y in cc]
                coords = " ".join(f"{lo:.8f},{la:.8f},0" for lo, la in ll)
                k.append(
                    f'<Placemark><name>slack {sid}</name>'
                    f'<description>{"; ".join(bits)}</description>'
                    f'<styleUrl>#b{b}</styleUrl>'
                    f'<Polygon><tessellate>1</tessellate>'
                    f'<altitudeMode>clampToGround</altitudeMode>'
                    f'<outerBoundaryIs><LinearRing>'
                    f'<coordinates>{coords}</coordinates>'
                    f'</LinearRing></outerBoundaryIs></Polygon></Placemark>')
        k.append("</Folder>")
    # ── the read's own water, where this date has been read ─────────────────
    fl = OUT / f"W94_08_flood_{a.date}.geojson"
    flt = OUT / f"W94_08_flood_tiles_{a.date}.geojson"
    for src, lab in ((flt, "tiles"), (fl, "vp2")):
        if not src.exists():
            continue
        fg = gpd.read_file(src).set_crs("EPSG:27700", allow_override=True)
        if not len(fg):
            continue
        k.append(f'<Style id="flood{lab}"><LineStyle><color>{FLOOD_COLOUR}</color>'
                 f'<width>2</width></LineStyle>'
                 f'<PolyStyle><fill>0</fill></PolyStyle></Style>')
        k.append(f'<Folder><name>WATER as the {lab} read classified it — '
                 f'{len(fg)} bod(ies), {fg.area.sum() / 1e4:.1f} ha</name>'
                 f'<open>1</open>')
        for _, r in fg.iterrows():
            geoms = (list(r.geometry.geoms)
                     if r.geometry.geom_type == "MultiPolygon" else [r.geometry])
            sid = (int(r["slack"]) if "slack" in fg.columns
                   and pd.notna(r.get("slack")) else None)
            for poly in geoms:
                cc = [(c[0], c[1]) for c in poly.exterior.coords]
                coords = " ".join(f"{lo:.8f},{la:.8f},0"
                                  for lo, la in (fwd.transform(x, y)
                                                 for x, y in cc))
                k.append(
                    f'<Placemark><name>water {int(r.get("body_id", 0))}</name>'
                    f'<description>{r.get("area_m2", 0):.0f} m2'
                    + (f"; names slack {sid}" if sid is not None
                       else "; OUTSIDE every hollow") +
                    f'</description>'
                    f'<styleUrl>#flood{lab}</styleUrl><Polygon><tessellate>1'
                    f'</tessellate><altitudeMode>clampToGround</altitudeMode>'
                    f'<outerBoundaryIs><LinearRing><coordinates>{coords}'
                    f'</coordinates></LinearRing></outerBoundaryIs>'
                    f'</Polygon></Placemark>')
        k.append("</Folder>")
        info(f"included the {lab} read's water: {len(fg)} bod(ies), "
             f"{fg.area.sum() / 1e4:.1f} ha")
        break            # the tile read is primary; only one water layer

    k.append("</Document></kml>")
    p = REPO / "data" / "geo" / f"digitise_{a.date}.kml"
    p.write_text("\n".join(k), encoding="utf-8")
    saved(str(p.relative_to(REPO)))
    q = OUT / f"W94_21_digitise_order_{a.date}.csv"
    hol[["slack", "band", "area_m2"]].assign(
        dipwells=[holds.get(int(s), "") for s in hol["slack"]],
        dL=[getattr(con.get(int(s)), "dL", None) for s in hol["slack"]],
        dBR=[getattr(con.get(int(s)), "dBR", None) for s in hol["slack"]],
        dS=[getattr(con.get(int(s)), "dS", None) for s in hol["slack"]],
    ).sort_values(["band", "area_m2"], ascending=[True, False]).to_csv(
        q, index=False)
    saved(q.name)
    info("Trace the WATER'S edge as a new polygon in Google Earth; do not edit "
         "these outlines — they are the slack, not the water, and the whole "
         "question is where the two differ. Save your polygons to one KML and "
         "hand it back for ingest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
