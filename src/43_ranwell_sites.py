#!/usr/bin/env python3
"""Script 43 - Ranwell (1959) historical water-table sites, georeferenced (W95).

Georeferences the 17 water-table pipe sites of Ranwell (1959) Fig 3 (J. Ecology
47(3), p.577) into OSGB and reports, per site, the nearest modern dipwell - the
historical out-of-sample locational cross-check Martin asked for ("which of our
wells are close to Ranwell's").

Two independent routes; their agreement is the check (see D-... / W95 spec):

  Route A -- HEADLINE, geometric similarity.  Fitted from the digitised control
    table alone: Penlon Lake (the one hard OSGB point, from Features.kml) anchors
    translation, the 1/4 km scale bar sets the scale, and rotation is taken as
    grid-north-up.  The inset north arrow is NOT in the main-map frame and only
    Penlon Lake is a hard point, so north-up is a documented assumption, not a
    fitted rotation; the shore-line and Route-B diagnostics below reveal whether
    it holds.  Applied to the digitised site pixels -> OSGB positions.

  Route B -- VALIDATION, elevational.  Each site's OD height is tabulated in the
    figure.  Sampling the DEM at the Route-A position and differencing against the
    tabulated height is independent of A's placement (it uses elevation, which A
    never sees).  A large A-vs-B disagreement flags a mis-registered or
    mis-digitised site rather than being averaged away.

Copyright (D-081 shape): the in-copyright JSTOR scan is NOT read here and is in
neither repository.  Inputs are DERIVED DATA - the digitised pixel tables
(data/geo/ranwell_1959_control.csv, ranwell_1959_sites_px.csv) - plus the KMLs,
the DEM and the modern network.  Sites not yet digitised (blank pixels) are
carried through and reported, not guessed.

Tier D (display/utility): a locational cross-reference; nothing downstream
consumes it.  Skips cleanly when its inputs are absent.
"""
__version__ = "1.0.1"  # 1.0.1 (2026-09-06): D-035 - drop store-time round() at 8 sites; store full precision, round at display  # Hollingham (2026) - 2026-09-06. W95: new tier-D step;
#                         Ranwell 1959 Fig 3 sites georeferenced, two routes,
#                         nearest-well table. Site positions PROVISIONAL
#                         (label-position proxy; sites 2/3/7 undigitised).

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from utils.paths import (  # noqa: E402
    DIR_43,
    OUT_43_SITES,
    OUT_43_NEAREST,
    OUT_43_DIAGNOSTIC,
    OUT_43_OVERLAY,
    OUT_43_VECTOR,
    OUT_43_REPORT_NUMBERS,
    DATA_RANWELL_CONTROL,
    DATA_RANWELL_SITES_PX,
    DATA_KML_FEATURES,
    DATA_KML_COAST_2006,
    DATA_DEM,
    INT_LOCATIONS,
    INT_WELLS_REFERENCE,
    INT_WELLS_EXTENDED,
)
from utils.config import (  # noqa: E402
    RANWELL_SCALEBAR_M,
    RANWELL_PENLON_NAME,
    RANWELL_ANALOGUE_RADIUS_M,
    RANWELL_ROUTE_B_FLAG_M,
)
from utils.console_utils import banner, phase, step, info, warn, saved  # noqa: E402
from utils.render_utils import apply_house_style, render_figure  # noqa: E402


def _skip(msg):
    warn(f"Script 43 skipped: {msg}")
    return 0


def _penlon_osgb():
    """Centroid of the 'Llyn Rhos Ddu' placemark in Features.kml, in OSGB (E, N)."""
    from utils.kml_io import read_kml
    gdf = read_kml(DATA_KML_FEATURES)  # EPSG:27700
    sel = gdf[gdf["Name"].astype(str).str.strip() == RANWELL_PENLON_NAME]
    if sel.empty:
        raise RuntimeError(
            f"placemark {RANWELL_PENLON_NAME!r} not found in {DATA_KML_FEATURES.name}"
        )
    c = sel.geometry.iloc[0].centroid
    return float(c.x), float(c.y)


def _fit_route_a(control, penlon_en):
    """Grid-north-up similarity: pixel (x right, y down) -> OSGB (E, N).

    Returns a function px(x, y) -> (E, N) and the fitted scale (m per pixel).
    """
    ctrl = {r["role"]: (float(r["px_x"]), float(r["px_y"])) for _, r in control.iterrows()}
    p_px = ctrl["penlon_lake_centroid"]
    z0 = np.array(ctrl["scalebar_zero"])
    z1 = np.array(ctrl["scalebar_quarter"])
    bar_px = float(np.hypot(*(z1 - z0)))
    if bar_px <= 0:
        raise RuntimeError("scale-bar endpoints coincide")
    m_per_px = RANWELL_SCALEBAR_M / bar_px  # metres of ground per figure pixel
    pe, pn = penlon_en

    def to_en(x, y):
        # north-up: +x -> +East, +y (down) -> -North (i.e. South)
        e = pe + (float(x) - p_px[0]) * m_per_px
        n = pn - (float(y) - p_px[1]) * m_per_px
        return e, n

    return to_en, m_per_px


def _sample_dem(points_en):
    """DEM height (m OD) at each (E, N); NaN outside coverage. rasterio."""
    import rasterio
    out = []
    with rasterio.open(str(DATA_DEM)) as src:
        band = src.read(1)
        nodata = src.nodata
        for e, n in points_en:
            try:
                row, col = src.index(e, n)
            except Exception:
                out.append(np.nan)
                continue
            if 0 <= row < band.shape[0] and 0 <= col < band.shape[1]:
                v = band[row, col]
                out.append(np.nan if (nodata is not None and v == nodata) else float(v))
            else:
                out.append(np.nan)
    return np.array(out, dtype=float)


def _shore_misfit(control, to_en):
    """Median distance (m) from the transformed figure shore points to coast2006."""
    try:
        from utils.kml_io import read_kml
        from shapely.geometry import Point
        from shapely.ops import unary_union
        coast = unary_union(list(read_kml(DATA_KML_COAST_2006).geometry))
    except Exception as exc:  # coast KML or shapely unavailable
        info(f"shore diagnostic unavailable: {exc}")
        return np.nan
    ctrl = {r["role"]: (float(r["px_x"]), float(r["px_y"])) for _, r in control.iterrows()}
    ds = []
    for role in ("shore_point_a", "shore_point_b"):
        if role in ctrl:
            e, n = to_en(*ctrl[role])
            ds.append(Point(e, n).distance(coast))
    return float(np.median(ds)) if ds else np.nan


def _modern_network():
    """Modern dipwell E/N with a reference/extended tag, from 01_locations.csv."""
    loc = pd.read_csv(INT_LOCATIONS)
    ec = next(c for c in loc.columns if c.lower() in ("e", "easting", "x"))
    nc = next(c for c in loc.columns if c.lower() in ("n", "northing", "y"))
    idc = next(c for c in loc.columns if c.lower() in ("name", "well", "id"))
    loc = loc[[idc, ec, nc]].rename(columns={idc: "well", ec: "E", nc: "N"})
    loc = loc.dropna(subset=["E", "N"]).copy()

    def _ids(path):
        try:
            cols = pd.read_csv(path, nrows=0).columns
            return {str(c).strip().lower() for c in cols}
        except Exception:
            return set()

    ref = _ids(INT_WELLS_REFERENCE)
    ext = _ids(INT_WELLS_EXTENDED)

    def _tag(w):
        wl = str(w).strip().lower()
        if wl in ref:
            return "reference"
        if wl in ext:
            return "extended"
        return "other"

    loc["network"] = loc["well"].map(_tag)
    return loc


def main():
    apply_house_style()
    banner("43", "Ranwell (1959) historical water-table sites, georeferenced",
           version=__version__)

    for p in (DATA_RANWELL_CONTROL, DATA_RANWELL_SITES_PX, DATA_KML_FEATURES,
              DATA_DEM, INT_LOCATIONS):
        if not p.exists():
            return _skip(f"missing input {p.name}")

    DIR_43.mkdir(parents=True, exist_ok=True)

    phase(1, "Register Ranwell Fig 3 sites into OSGB (Route A, geometric)")
    control = pd.read_csv(DATA_RANWELL_CONTROL)
    sites = pd.read_csv(DATA_RANWELL_SITES_PX)
    penlon_en = _penlon_osgb()
    to_en, m_per_px = _fit_route_a(control, penlon_en)
    info(f"scale {m_per_px:.3f} m/px; Penlon anchor E{penlon_en[0]:.0f} N{penlon_en[1]:.0f}")

    digit = sites.dropna(subset=["px_x", "px_y"]).copy()
    undig = sites[sites["px_x"].isna() | sites["px_y"].isna()].copy()
    en = [to_en(r.px_x, r.px_y) for r in digit.itertuples()]
    digit["easting"] = [e for e, _ in en]
    digit["northing"] = [n for _, n in en]
    step(f"{len(digit)} of {len(sites)} sites digitised and registered"
         + (f"; pending: {', '.join(str(int(s)) for s in undig.site_no)}" if len(undig) else ""))

    phase(2, "Elevational cross-check (Route B, DEM vs tabulated height)")
    dem_h = _sample_dem(list(zip(digit["easting"], digit["northing"])))
    digit["dem_height_m"] = dem_h
    digit["route_b_resid_m"] = digit["dem_height_m"] - digit["height_m_od"]
    resid = digit["route_b_resid_m"].abs()
    digit["route_b_flag"] = resid > RANWELL_ROUTE_B_FLAG_M
    shore_m = _shore_misfit(control, to_en)
    med_resid = float(resid.median()) if len(resid.dropna()) else np.nan
    step(f"Route-A-vs-B median |height residual| {med_resid:.2f} m; "
         f"{int(digit['route_b_flag'].sum())} site(s) over {RANWELL_ROUTE_B_FLAG_M:.0f} m; "
         f"shore misfit {shore_m:.0f} m")

    phase(3, "Nearest modern dipwell per Ranwell site")
    net = _modern_network()
    nearest_rows = []
    for r in digit.itertuples():
        d = np.hypot(net["E"] - r.easting, net["N"] - r.northing)
        order = np.argsort(d.values)
        top = net.iloc[order[:3]].copy()
        top_d = d.values[order[:3]]
        nearest_rows.append({
            "ranwell_site": int(r.site_no),
            "nearest_well": top.iloc[0]["well"],
            "nearest_well_network": top.iloc[0]["network"],
            "nearest_well_dist_m": float(top_d[0]),
            "nearest_3_wells": "; ".join(
                f"{w} ({dist:.0f} m)" for w, dist in zip(top["well"], top_d)),
        })
    nearest = pd.DataFrame(nearest_rows)
    digit = digit.merge(
        nearest[["ranwell_site", "nearest_well", "nearest_well_dist_m"]],
        left_on="site_no", right_on="ranwell_site", how="left").drop(columns="ranwell_site")

    # reverse view: modern wells with a 1950s analogue within the radius
    rev_rows = []
    for w in net.itertuples():
        if digit.empty:
            break
        d = np.hypot(digit["easting"] - w.E, digit["northing"] - w.N)
        dmin = float(d.min())
        if dmin <= RANWELL_ANALOGUE_RADIUS_M:
            j = int(np.argmin(d.values))
            rev_rows.append({
                "modern_well": w.well,
                "network": w.network,
                "nearest_ranwell_site": int(digit.iloc[j]["site_no"]),
                "dist_m": dmin,
            })
    reverse = pd.DataFrame(rev_rows).sort_values("dist_m") if rev_rows else pd.DataFrame(
        columns=["modern_well", "network", "nearest_ranwell_site", "dist_m"])
    step(f"{len(reverse)} modern well(s) within {RANWELL_ANALOGUE_RADIUS_M:.0f} m of a 1950s site")

    phase(4, "Outputs, vector and overlay figure")
    site_cols = ["site_no", "easting", "northing", "height_m_od", "slack_type",
                 "confidence", "dem_height_m", "route_b_resid_m", "route_b_flag",
                 "nearest_well", "nearest_well_dist_m"]
    out_sites = digit[[c for c in site_cols if c in digit.columns]].copy()
    out_sites.to_csv(OUT_43_SITES, index=False)
    saved(OUT_43_SITES.name)
    nearest.to_csv(OUT_43_NEAREST, index=False)
    saved(OUT_43_NEAREST.name)

    diag = pd.DataFrame([{
        "n_sites_total": len(sites),
        "n_sites_digitised": len(digit),
        "n_sites_pending": len(undig),
        "scale_m_per_px": m_per_px,
        "penlon_easting": penlon_en[0],
        "penlon_northing": penlon_en[1],
        "route_b_median_abs_resid_m": med_resid if med_resid == med_resid else np.nan,
        "route_b_flagged_sites": int(digit["route_b_flag"].sum()),
        "shore_misfit_m": shore_m if shore_m == shore_m else np.nan,
        "rotation_assumption": "grid-north-up (documented; not fitted)",
    }])
    diag.to_csv(OUT_43_DIAGNOSTIC, index=False)
    saved(OUT_43_DIAGNOSTIC.name)

    # vector (GeoJSON) of the registered sites - derived product, D-081 safe
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        gv = gpd.GeoDataFrame(
            out_sites.copy(),
            geometry=[Point(e, n) for e, n in zip(out_sites["easting"], out_sites["northing"])],
            crs="EPSG:27700")
        gv.to_file(OUT_43_VECTOR, driver="GeoJSON")
        saved(OUT_43_VECTOR.name)
    except Exception as exc:
        warn(f"vector not written ({exc})")

    # overlay figure on the canonical extent
    try:
        import matplotlib.pyplot as plt
        from utils.map_utils import add_en_axes, load_dem_hillshade
        fig, ax = plt.subplots(figsize=(7.5, 7.0))
        try:
            load_dem_hillshade(ax, DATA_DEM.parent)
        except Exception:
            pass
        add_en_axes(ax)
        ax.scatter(net["E"], net["N"], s=10, c="#4444aa", label="Modern dipwells", zorder=5)
        if not digit.empty:
            ax.scatter(digit["easting"], digit["northing"], s=55, marker="^",
                       facecolor="#cc5500", edgecolor="k", linewidths=0.6,
                       label="Ranwell 1959 sites", zorder=6)
            for r in digit.itertuples():
                ax.annotate(str(int(r.site_no)), (r.easting, r.northing),
                            textcoords="offset points", xytext=(4, 3), fontsize=7)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
        ax.set_title("Ranwell (1959) water-table sites against the modern network "
                     "(site positions provisional)")
        render_figure(fig, OUT_43_OVERLAY)
        saved(OUT_43_OVERLAY.name)
    except Exception as exc:
        warn(f"overlay figure not written ({exc})")

    rn = pd.DataFrame([
        ("ranwell_sites_total", len(sites), "count",
         "water-table pipe sites in Ranwell 1959 Fig 3 (numbered 1-16, 18)"),
        ("ranwell_sites_registered", len(digit), "count",
         "sites with a digitised pixel and a Route-A OSGB position"),
        ("ranwell_sites_pending_digitisation", len(undig), "count",
         "sites not yet confidently digitised (provisional label-proxy pass)"),
        ("ranwell_route_b_median_abs_resid_m",
         round(med_resid, 3) if med_resid == med_resid else "", "m",
         "median |DEM height - tabulated OD height| across registered sites"),
        ("ranwell_shore_misfit_m", round(shore_m, 1) if shore_m == shore_m else "", "m",
         "median distance of transformed figure shore points to coast2006"),
        ("ranwell_modern_wells_with_analogue", len(reverse), "count",
         f"modern wells within {RANWELL_ANALOGUE_RADIUS_M:.0f} m of a 1950s site"),
    ], columns=["key", "value", "unit", "note"])
    rn.to_csv(OUT_43_REPORT_NUMBERS, index=False)
    saved(OUT_43_REPORT_NUMBERS.name)

    info("NOTE: site positions are a provisional label-position proxy (W95); "
         "Route A rotation is grid-north-up by assumption. Re-run after precise "
         "digitisation to finalise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
