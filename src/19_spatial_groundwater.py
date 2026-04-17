"""
19_spatial_groundwater.py
=========================
Spatial Groundwater Analysis — Newborough Warren 2005-2026
Hollingham (2026)

Reads pipeline intermediates and writes a single self-contained interactive
HTML file: scenario_viewer.html

Physical constants:
    K = 6 m/day (Connell 2003)
    Forest interception = 24% (Freeman 2008, Corsican pine)
    Broadleaf interception = 25% (deciduous default)
    Sy floor: C1 = 6%, C2-C5 = 12%
    Wells excluded from IDW: ceh12 (bedrock), ceh15 (forest slack edge)

Usage:
    python 19_spatial_groundwater.py
    python 19_spatial_groundwater.py --out /path/to/custom.html
"""

__version__ = "2.0.0"   # Hollingham (2026) -- 2026-04-15

import sys
import json
import warnings
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from utils.paths import (
    make_all_dirs,
    DATA_DIR,
    DATA_KML_FEATURES,
    DATA_KML_CLEARFELL,
    KML_BROADLEAF,
    DIR_19,
    INT_LOCATIONS,
    INT_CLIMATE,
    INT_CLUSTER_STATS,
    INT_MASTER_DATA,
    INT_WELL_ELEVATIONS,
    INT_WELLS_CLEAN_MAOD,
    OUT_18_WELL_SY_TABLE,
)
from utils.data_utils import normalize_well_name

# Physical constants
FOREST_INTERCEPTION    = 0.24   # Corsican pine -- Freeman (2008)
BROADLEAF_INTERCEPTION = 0.25   # Deciduous default
MONITOR_START = "2005-04-01"
MONITOR_END   = "2026-02-28"
WINTER_MONTHS = [11, 12, 1, 2, 3]
SUMMER_MONTHS = [5, 6, 7, 8, 9]
SY_DEFAULTS   = {1: 0.08, 2: 0.12, 3: 0.12, 4: 0.12, 5: 0.10, 6: 0.10}
SY_FLOOR      = {1: 0.06, 2: 0.12, 3: 0.12, 4: 0.12, 5: 0.12, 6: 0.12}
EXCLUDE_WELLS = {"ceh12", "ceh15"}


# ============================================================================
# DATA LOADING
# ============================================================================

def _norm(s):
    return str(s).lower().replace(" ", "").replace("-", "").strip()


def load_data():
    """Load and merge all required pipeline intermediates."""
    loc  = pd.read_csv(INT_LOCATIONS)
    loc["id"] = loc["Match_ID"].apply(_norm)
    cl   = pd.read_csv(INT_CLUSTER_STATS)
    cl["id"] = cl["Match_ID"].apply(_norm)
    md   = pd.read_csv(INT_MASTER_DATA)
    md["id"] = md["Name_Original"].apply(_norm)
    elev = pd.read_csv(INT_WELL_ELEVATIONS)
    elev["id"] = elev["Name_norm"].apply(_norm)
    maod = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    maod.columns = [_norm(c) for c in maod.columns]
    maod = maod.loc[MONITOR_START:MONITOR_END]
    clim = pd.read_csv(INT_CLIMATE, parse_dates=["Date"], index_col="Date")
    clim = clim.loc[MONITOR_START:MONITOR_END]
    sy_df = None
    if OUT_18_WELL_SY_TABLE.exists():
        sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
        wcol = ("Well_Normalised" if "Well_Normalised" in sy_df.columns else "Well")
        sy_df["id"] = sy_df[wcol].apply(_norm)
    else:
        warnings.warn(f"{OUT_18_WELL_SY_TABLE.name} not found -- cluster defaults used.")
    return loc, cl, md, elev, maod, clim, sy_df


def build_well_table(loc, cl, md, elev, maod, clim, sy_df):
    """Build per-well table with heads, betas, Sy, and coordinates."""
    P_bar   = clim["P_m"].mean()
    PET_bar = clim["PET"].mean()
    wm = clim[clim.index.month.isin(WINTER_MONTHS)]
    sm = clim[clim.index.month.isin(SUMMER_MONTHS)]
    climate_stats = {
        "annual": (P_bar, PET_bar),
        "winter": (wm["P_m"].mean(), wm["PET"].mean()),
        "summer": (sm["P_m"].mean(), sm["PET"].mean()),
    }
    wt = loc[["id", "E", "N"]].copy()
    wt = wt.merge(cl[["id", "Cluster"]], on="id", how="left")
    wt = wt.merge(
        md[["id", "beta_1_recharge", "beta_2_atmospheric_draw",
            "beta_3_internal_brake"]].rename(columns={
            "beta_1_recharge": "b1",
            "beta_2_atmospheric_draw": "b2",
            "beta_3_internal_brake": "b3",
        }), on="id", how="left")
    heads_all = maod.mean()
    heads_win = maod[maod.index.month.isin(WINTER_MONTHS)].mean()
    heads_sum = maod[maod.index.month.isin(SUMMER_MONTHS)].mean()
    wt["mh"] = wt["id"].map(heads_all)
    wt["wh"] = wt["id"].map(heads_win)
    wt["sh"] = wt["id"].map(heads_sum)
    if sy_df is not None:
        sy_map = dict(zip(sy_df["id"], sy_df["Sy_median"]))
        wt["sy"] = wt["id"].map(sy_map)
    else:
        wt["sy"] = np.nan
    def fill_sy(row):
        if pd.notna(row["sy"]):
            return row["sy"]
        return SY_DEFAULTS.get(int(row["Cluster"]) if pd.notna(row["Cluster"]) else 3, 0.12)
    wt["sy"] = wt.apply(fill_sy, axis=1)
    wt = wt[~wt["id"].isin(EXCLUDE_WELLS)]
    wt = wt.dropna(subset=["E", "N", "mh"])
    wt = wt.reset_index(drop=True)
    print(f"  Well table: {len(wt)} wells")
    print(f"  beta available: {wt['b1'].notna().sum()} wells")
    print(f"  C4 wells (forest): {(wt['Cluster'] == 4).sum()}")
    print(f"  P_bar  = {P_bar*1000:.2f} mm/mo   PET_bar = {PET_bar*1000:.2f} mm/mo")
    return wt, climate_stats


# ============================================================================
# KML GEOREFERENCING
# ============================================================================

def load_kml_polygons():
    """
    Load KML polygons and reproject EPSG:4326 to EPSG:27700 via pyproj.
    Uses path constants from utils/paths.py (all pointing to DATA_DIR).
    Falls back to hardcoded coordinates for any polygon whose KML is absent.
    """
    HARDCODED = {
        "clearfell": [[241062,363621],[241170,363796],[241354,363679],
                       [241235,363505],[241062,363621]],
        "broadleaf": [[241298,364491],[241316,364469],[241348,364365],
                       [241428,364295],[241424,364259],[241411,364210],
                       [241406,364158],[241607,364051],[241717,364207],
                       [241692,364218],[241654,364245],[241629,364259],
                       [241539,364315],[241465,364360],[241327,364543],
                       [241298,364491]],
        "lake":      [[242613,364937],[242576,364938],[242543,364924],
                       [242512,364902],[242479,364860],[242457,364849],
                       [242429,364818],[242397,364788],[242360,364764],
                       [242352,364750],[242356,364729],[242384,364730],
                       [242405,364749],[242435,364773],[242476,364786],
                       [242507,364807],[242531,364822],[242554,364832],
                       [242574,364853],[242597,364869],[242619,364882],
                       [242631,364899],[242628,364919],[242613,364937]],
        "forest":    [[241554,364966],[241380,364725],[241715,364622],
                       [241805,364349],[241024,363184],[240920,363331],
                       [240650,363417],[240650,365100],[241409,365100],
                       [241554,364966]],
        "site":      [[241088,362784],[240016,363370],[240000,364300],
                       [240954,365000],[241436,365096],[242932,365034],
                       [243680,364434],[243762,364180],[243604,363794],
                       [243962,363656],[243816,363012],[243036,362266],
                       [242066,362294],[241780,362156],[241088,362784]],
    }
    polys = {}
    try:
        import fiona
        fiona.drvsupport.supported_drivers["KML"] = "rw"
        import geopandas as gpd

        def kml_to_bng(path):
            if path is None or not Path(path).exists():
                return []
            gdf = gpd.read_file(str(path), driver="KML")
            gdf = gdf.set_crs(epsg=4326, allow_override=True).to_crs("EPSG:27700")
            results = []
            for _, row in gdf.iterrows():
                geom = row.geometry
                nm = str(row.get("Name", "")) if "Name" in row.index else ""
                if geom is None:
                    continue
                def pts_from(g):
                    if g.geom_type == "Polygon":
                        return [[round(x), round(y)]
                                for x, y in zip(g.exterior.xy[0], g.exterior.xy[1])]
                    if g.geom_type == "LineString":
                        return [[round(x), round(y)] for x, y in zip(g.xy[0], g.xy[1])]
                    if g.geom_type == "Point":
                        return [[round(geom.x), round(geom.y)]]
                    if "Multi" in g.geom_type:
                        return pts_from(list(g.geoms)[0])
                    return []
                pts = pts_from(geom)
                if pts:
                    results.append({"name": nm, "pts": pts})
            return results

        cf = kml_to_bng(DATA_KML_CLEARFELL)
        if cf:
            polys["clearfell"] = cf[0]["pts"]
            print(f"  clearfell.kml: {len(polys['clearfell'])} pts")

        ft = kml_to_bng(DATA_KML_FEATURES)
        for f in ft:
            nm_lower = f["name"].lower()
            if "llyn" in nm_lower or "rhos" in nm_lower or "lake" in nm_lower:
                polys["lake"] = f["pts"]
            elif "forest" in nm_lower or "plantation" in nm_lower:
                polys["forest_raw"] = f["pts"]
        if ft:
            print(f"  Features.kml: found {[k for k in ('lake','forest_raw') if k in polys]}")

        bl = kml_to_bng(KML_BROADLEAF)
        if bl:
            polys["broadleaf"] = bl[0]["pts"]
            print(f"  broadleaf_restock.kml: {len(polys['broadleaf'])} pts")

        site_path = DATA_DIR / "site_boundary.kml"
        sb = kml_to_bng(site_path)
        if sb:
            try:
                from shapely.geometry import Polygon as _SP
                from shapely.ops import unary_union
                all_p = [_SP([(p[0], p[1]) for p in f["pts"]]) for f in sb if len(f["pts"]) >= 3]
                merged = unary_union(all_p)
                simp = merged.simplify(100, preserve_topology=True)
                if simp.geom_type == "Polygon":
                    polys["site"] = [[round(x), round(y)]
                                     for x, y in zip(simp.exterior.xy[0], simp.exterior.xy[1])]
                else:
                    biggest = max(list(simp.geoms), key=lambda p: p.area)
                    polys["site"] = [[round(x), round(y)]
                                     for x, y in zip(biggest.exterior.xy[0], biggest.exterior.xy[1])]
                print(f"  site_boundary.kml: {len(polys['site'])} pts (simplified)")
            except Exception:
                polys["site"] = max(sb, key=lambda x: len(x["pts"]))["pts"]
                print(f"  site_boundary.kml: {len(polys['site'])} pts")

        if "forest_raw" in polys:
            try:
                from shapely.geometry import Polygon as _FP
                fp = _FP([(p[0], p[1]) for p in polys["forest_raw"]])
                clip = _FP([(240650,362600),(243200,362600),(243200,365100),(240650,365100)])
                clipped = fp.intersection(clip).simplify(50)
                if not clipped.is_empty:
                    if clipped.geom_type == "Polygon":
                        polys["forest"] = [[round(x), round(y)]
                                            for x, y in zip(clipped.exterior.xy[0], clipped.exterior.xy[1])]
                    else:
                        lg = max(list(clipped.geoms), key=lambda g: g.area)
                        polys["forest"] = [[round(x), round(y)]
                                            for x, y in zip(lg.exterior.xy[0], lg.exterior.xy[1])]
                    print(f"  Forest (clipped): {len(polys['forest'])} pts")
            except Exception as e:
                warnings.warn(f"Forest polygon clip failed: {e}")
            del polys["forest_raw"]

    except ImportError:
        warnings.warn("geopandas/fiona not available -- using hardcoded KML coordinates.")

    for key, coords in HARDCODED.items():
        if key not in polys:
            polys[key] = coords
            print(f"  {key}: using hardcoded coordinates (KML not loaded)")

    return polys


# ============================================================================
# SERIALISATION HELPERS
# ============================================================================

def _r(v, d=4):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return round(float(v), d)


def serialise_wells(wt):
    rows = []
    for _, r in wt.iterrows():
        cl_int = int(r["Cluster"]) if pd.notna(r["Cluster"]) else 3
        rows.append({"n": r["id"], "cl": cl_int,
                     "E": round(float(r["E"])), "N": round(float(r["N"])),
                     "mh": _r(r["mh"],3), "wh": _r(r["wh"],3), "sh": _r(r["sh"],3),
                     "sy": _r(r["sy"],4), "b1": _r(r["b1"],6),
                     "b2": _r(r["b2"],6), "b3": _r(r["b3"],6)})
    return rows


def serialise_climate(wt, climate_stats):
    out = {}
    for sea_key, (P, PET) in climate_stats.items():
        h_col = {"annual": "mh", "winter": "wh", "summer": "sh"}[sea_key]
        cluster_heads = {}
        for cl_int in [1, 2, 3, 4, 5]:
            sub = wt[wt["Cluster"] == cl_int][h_col].dropna()
            cluster_heads[cl_int] = _r(sub.mean(), 4) if len(sub) else 0.0
        out[sea_key] = {"P": _r(P,7), "PET": _r(PET,7), "cluster_heads": cluster_heads}
    cluster_betas = {}
    for cl_int in [1, 2, 3, 4, 5]:
        sub = wt[(wt["Cluster"] == cl_int) & wt["b1"].notna()]
        if len(sub) == 0:
            sub = wt[wt["Cluster"] == cl_int]
        cluster_betas[cl_int] = {"b1": _r(sub["b1"].mean(),6) if len(sub) else None,
                                  "b2": _r(sub["b2"].mean(),6) if len(sub) else None,
                                  "b3": _r(sub["b3"].mean(),6) if len(sub) else None}
    out["cluster_betas"] = cluster_betas
    return out


# ============================================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Newborough Warren — Hydrological Scenario Viewer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{{
  --sand:#f4f0e6; --sand-dark:#e8e0cc; --dune:#c8b878;
  --slate:#3a4a52; --slate-light:#5a6e78;
  --water:#4a7a8a; --water-light:#6a9aaa; --water-pale:#e8f2f5;
  --pine:#3d5c3a; --pine-light:#5a7d56;
  --text:#2a3338; --text-light:#5a6a72; --border:#d4c8a8;
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Source Sans 3',sans-serif;font-weight:400;
     font-size:14px;background:var(--sand);color:var(--text);line-height:1.6;}}

/* Header */
header{{background:var(--slate);color:#fff;padding:1.3rem 1.5rem 1.1rem;
       position:relative;overflow:hidden;}}
header::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;
              background:linear-gradient(90deg,var(--dune),var(--water),var(--pine));}}
.site-label{{font-size:0.68rem;font-weight:600;letter-spacing:0.18em;
            text-transform:uppercase;color:var(--dune);margin-bottom:0.45rem;}}
header h1{{font-family:'Libre Baskerville',Georgia,serif;font-weight:700;
          font-size:clamp(1.05rem,2.8vw,1.4rem);line-height:1.25;
          color:#fff;margin-bottom:0.35rem;}}
header p{{font-size:0.78rem;color:rgba(255,255,255,0.58);font-weight:300;}}

/* Layout grid */
.main{{display:grid;grid-template-columns:215px minmax(0,1fr);gap:12px;
       padding:12px;align-items:start;}}
@media(max-width:640px){{.main{{grid-template-columns:1fr;}}}}

/* Controls sidebar */
.ctrl{{background:#fff;border:1px solid var(--border);border-radius:4px;padding:12px;}}
@media(min-width:641px){{.ctrl{{position:sticky;top:0;max-height:98vh;overflow-y:auto;}}}}
.ch{{font-size:0.65rem;font-weight:600;letter-spacing:0.15em;text-transform:uppercase;
     color:var(--water);border-bottom:1px solid var(--border);
     padding-bottom:4px;margin-bottom:7px;}}
.sc{{display:block;width:100%;text-align:left;padding:5px 8px;margin-bottom:3px;
     background:transparent;border:1px solid var(--border);border-radius:3px;
     cursor:pointer;font-size:11px;color:var(--text);line-height:1.3;
     font-family:'Source Sans 3',sans-serif;}}
.sc:hover{{background:var(--water-pale);border-color:var(--water-light);}}
.sc.on{{border:1.5px solid var(--water);background:var(--water-pale);
        color:var(--water);font-weight:600;}}
.sc-note{{font-size:10px;color:var(--text-light);line-height:1.45;margin-top:6px;
          padding:5px 8px;background:var(--sand);
          border-left:2px solid var(--dune);border-radius:0 3px 3px 0;}}
.srow{{display:flex;align-items:center;gap:5px;margin-bottom:5px;}}
.srow label{{font-size:11px;color:var(--text-light);flex:1;}}
.sv{{font-size:10px;font-weight:600;min-width:34px;text-align:right;color:var(--slate);}}
.srow input[type=range]{{flex:1;min-width:0;accent-color:var(--water);}}
.ckrow{{display:flex;align-items:center;gap:6px;margin-bottom:4px;
        font-size:11px;color:var(--text-light);cursor:pointer;}}
.hr{{height:1px;background:var(--border);margin:8px 0;}}

/* Right column */
.rp{{min-width:0;display:flex;flex-direction:column;gap:10px;}}

/* Season tabs */
.tabs{{display:flex;gap:5px;flex-wrap:wrap;}}
.tab{{padding:4px 11px;border-radius:20px;font-size:11px;border:1px solid var(--border);
      background:transparent;cursor:pointer;color:var(--text-light);
      font-family:'Source Sans 3',sans-serif;}}
.tab.on{{background:var(--slate);color:#fff;border-color:var(--slate);}}

/* Warning banner */
.warn{{background:#fdf5e3;border:1px solid var(--dune);border-left:3px solid var(--dune);
       border-radius:0 3px 3px 0;padding:6px 10px;
       font-size:11px;color:var(--text);line-height:1.45;}}

/* Metric cards */
.metrics{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;}}
@media(max-width:420px){{.metrics{{grid-template-columns:repeat(2,1fr);}}}}
.mc{{background:#fff;border:1px solid var(--border);border-radius:3px;padding:8px 10px;}}
.mc .ml{{font-size:10px;color:var(--text-light);margin-bottom:2px;}}
.mc .mv{{font-size:15px;font-weight:700;}}
.mc .mu{{font-size:10px;color:var(--text-light);}}

/* Panels */
.panel{{background:#fff;border:1px solid var(--border);border-radius:4px;padding:12px;}}
.panel h4{{font-size:11px;font-weight:600;color:var(--slate-light);margin-bottom:6px;
          letter-spacing:0.04em;text-transform:uppercase;}}
.phead{{display:flex;align-items:center;justify-content:space-between;
        margin-bottom:7px;flex-wrap:wrap;gap:5px;}}
.phead h4{{margin:0;}}
.rtabs{{display:flex;gap:4px;flex-wrap:wrap;}}
.rt{{padding:3px 8px;border-radius:3px;font-size:10px;border:1px solid var(--border);
     background:transparent;cursor:pointer;color:var(--text-light);
     font-family:'Source Sans 3',sans-serif;}}
.rt.on{{background:var(--water-pale);border-color:var(--water);
        color:var(--water);font-weight:600;}}

/* Map canvas */
.mapwrap{{position:relative;width:100%;overflow:hidden;border-radius:3px;}}
.mapwrap canvas{{display:block;width:100%;}}
#mapBg{{position:relative;}}
#mapC{{position:absolute;top:0;left:0;cursor:crosshair;}}
.leg{{display:flex;flex-wrap:wrap;align-items:center;gap:7px;
      margin-top:5px;font-size:10px;color:var(--text-light);}}
.ls{{width:10px;height:10px;border-radius:2px;display:inline-block;
     vertical-align:middle;margin-right:2px;}}
.tip{{font-size:11px;color:var(--text-light);margin-top:3px;min-height:14px;}}

/* Chart + table */
.chwrap{{position:relative;width:100%;height:155px;}}
.tblwrap{{overflow-x:auto;}}
.tbl{{display:grid;grid-template-columns:110px repeat(5,minmax(0,1fr));
      gap:2px;min-width:480px;}}
.th{{font-size:10px;color:var(--text-light);text-align:center;padding:3px 2px;font-weight:600;}}
.tl{{font-size:10px;color:var(--text-light);display:flex;align-items:center;
     padding-right:3px;white-space:nowrap;}}
.tc{{border-radius:2px;padding:4px 3px;text-align:center;font-size:10px;
     font-weight:500;background:var(--sand);color:var(--text);}}

/* Footer */
.nav-links{{background:var(--slate-light);border-bottom:1px solid rgba(255,255,255,0.08);
           padding:0.4rem 1rem;display:flex;gap:0;flex-wrap:wrap;overflow-x:auto;}}
.nav-links a{{display:block;padding:0.45rem 1rem;font-size:0.75rem;font-weight:600;
             letter-spacing:0.05em;text-transform:uppercase;color:rgba(255,255,255,0.65);
             text-decoration:none;white-space:nowrap;}}
.nav-links a:hover{{color:#fff;}}
.nav-links a.active{{color:#fff;border-bottom:2px solid var(--dune);}}
footer{{background:var(--slate);color:rgba(255,255,255,0.5);
        font-size:10px;padding:12px 18px;line-height:1.6;margin-top:4px;}}
footer a{{color:var(--dune);text-decoration:none;}}
footer a:hover{{text-decoration:underline;}}
</style>
</head>
<body>
<header>
  <div class="site-label">Newborough Warren NNR &middot; Anglesey SAC</div>
  <h1>Hydrological Scenario Viewer</h1>
  <p>{n_wells} dipwells &middot; 2005&#8211;2026 monitoring record &middot;
     SSM state-space model &middot; Hollingham (2026)</p>
</header>

<nav class="nav-links">
  <a href="index.html">&#8592; Home</a>
  <a href="seasonal_extremes_scatter.html">Seasonal extremes</a>
  <a href="scenario_viewer.html" class="active">Scenario viewer &#8594;</a>
</nav>

<div class="main" id="mainGrid">

<div class="ctrl">
  <div class="ch">Scenarios</div>
  <button class="sc on" id="btn_baseline"    onclick="loadSc('baseline')">Baseline (2005&#8211;2026)</button>
  <button class="sc"    id="btn_climate_wet" onclick="loadSc('climate_wet')">Climate wet (+10% P)</button>
  <button class="sc"    id="btn_climate_dry" onclick="loadSc('climate_dry')">Climate dry (&#8722;10% P, +10% PET)</button>
  <button class="sc"    id="btn_clearfell"   onclick="loadSc('clearfell')">Clearfell (interception&#8594;0, &#946;&#8322;&#8593;)</button>
  <button class="sc"    id="btn_broadleaf"   onclick="loadSc('broadleaf')">Broadleaf conversion</button>
  <button class="sc"    id="btn_thinning"    onclick="loadSc('thinning')">Forest thinning (50%)</button>
  <div class="sc-note">Presets represent single discrete scenarios. Use the sliders to explore combined pressures &#8212; the SSM is additive so combinations are physically valid, but constitute exploratory analysis rather than named management scenarios.</div>
  <div class="hr"></div>

  <div class="ch">Climate</div>
  <div class="srow"><label>P scaling</label>
    <input type="range" min="0.5" max="1.5" step="0.01" value="1" id="sP" oninput="onSl()">
    <span class="sv" id="vP">1.00&#215;</span></div>
  <div class="srow"><label>PET scaling</label>
    <input type="range" min="0.5" max="1.5" step="0.01" value="1" id="sPET" oninput="onSl()">
    <span class="sv" id="vPET">1.00&#215;</span></div>
  <div class="hr"></div>

  <div class="ch">Forest C4</div>
  <div class="srow"><label>Interception</label>
    <input type="range" min="0" max="0.4" step="0.01" value="0.24" id="sI" oninput="onSl()">
    <span class="sv" id="vI">24%</span></div>
  <div class="srow"><label>&#946;&#8322; scaling</label>
    <input type="range" min="0.5" max="2" step="0.05" value="1" id="sB2" oninput="onSl()">
    <span class="sv" id="vB2">1.00&#215;</span></div>
  <div class="hr"></div>

  <div class="ch">Specific yield</div>
  <div class="srow"><label>Sy scaling</label>
    <input type="range" min="0.5" max="2" step="0.05" value="1" id="sSy" oninput="onSl()">
    <span class="sv" id="vSy">1.00&#215;</span></div>
  <div style="font-size:10px;color:var(--text-light);line-height:1.4;margin-top:3px;">
    Per-well WTF medians (scripts 17/18).<br>Floor: C1&nbsp;6%, C2&#8211;C5&nbsp;12%.</div>
  <div class="hr"></div>

  <div class="ch">Map</div>
  <label class="ckrow"><input type="checkbox" id="chkKml" checked onchange="drawMap()">
    KML overlays</label>
  <label class="ckrow"><input type="checkbox" id="chkLbl" onchange="drawMap()">
    Well labels</label>
</div>

<div class="rp">
  <div class="tabs">
    <button class="tab on" id="tab_annual" onclick="setSeas('annual')">Annual</button>
    <button class="tab" id="tab_winter" onclick="setSeas('winter')">Winter (Nov&#8211;Mar)</button>
    <button class="tab" id="tab_summer" onclick="setSeas('summer')">Summer (May&#8211;Sep)</button>
  </div>
  <div id="warnBox" class="warn" style="display:none"></div>
  <div class="metrics" id="mrow"></div>

  <div class="panel">
    <div class="phead">
      <h4>IDW head surface &#8212; masked to site boundary</h4>
      <div class="rtabs">
        <button class="rt on" id="rt_dh"  onclick="setMM('dh')">&#916;h vs baseline</button>
        <button class="rt"    id="rt_abs" onclick="setMM('abs')">Absolute head</button>
      </div>
    </div>
    <div class="mapwrap" id="mwrap">
      <canvas id="mapBg"></canvas>
      <canvas id="mapC" role="img" aria-label="IDW groundwater head surface, Newborough Warren"></canvas>
    </div>
    <div class="leg" id="legDiv"></div>
    <div class="tip" id="tipDiv"></div>
  </div>

  <div class="panel">
    <div class="phead">
      <h4>Head by cluster</h4>
      <div class="rtabs">
        <button class="rt on" id="ct_dh"  onclick="setCM('dh')">&#916;h (m)</button>
        <button class="rt"    id="ct_abs" onclick="setCM('abs')">Absolute (m AOD)</button>
      </div>
    </div>
    <div class="chwrap"><canvas id="hC" aria-label="Cluster head bar chart"></canvas></div>
  </div>

  <div class="panel">
    <h4>Cluster summary</h4>
    <div class="tblwrap"><div class="tbl" id="tbl"></div></div>
  </div>
</div>
</div>

<footer>
  &#916;h from SSM increment model using per-well &#946;&#8321;, &#946;&#8322;, &#946;&#8323; (scripts 01&#8211;03).
  IDW (power&nbsp;=&nbsp;2) masked to site boundary (EPSG:27700).
  Interception: Corsican pine 24% (Freeman 2008); broadleaf 25%.
  K&nbsp;=&nbsp;6&nbsp;m/day (Connell 2003). Sy: WTF medians (scripts 17/18);
  floors C1&nbsp;=&nbsp;6%, C2&#8211;C5&nbsp;=&nbsp;12%.
  CEH14 boundary subsidy &#945;&nbsp;=&nbsp;+0.222&nbsp;m/month (script 07).
  <a href="https://newbroman.github.io/Newborough-Hydrology_models/">Newborough Hydrology Models</a>
  &middot; Hollingham (2026) &#8212; <em>Journal of Hydrology: Regional Studies</em>.
</footer>

<script>
var WELLS={wells_json};
var POLYS={polys_json};
var CLIMATE={climate_json};
var SY_FLOOR={sy_floor_json};
var FOREST_INTERCEPTION={forest_interception};
var BROADLEAF_INTERCEPTION={broadleaf_interception};
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
var CL_LABS={{1:'C1 Eastern lake-buffer',2:'C2 Eastern mature dune',
              3:'C3 Western mature dune',4:'C4 Forest',5:'C5 Coastal'}};
var CL_COLS={{1:'#1565C0',2:'#00897B',3:'#E64A19',4:'#558B2F',5:'#6A1B9A'}};
var EMIN=240650,EMAX=243200,NMIN=362600,NMAX=365100;
var SCEN={{
  baseline:    {{sP:1,    sPET:1,   sI:FOREST_INTERCEPTION,           sB2:1,    sSy:1}},
  climate_wet: {{sP:1.10, sPET:1,   sI:FOREST_INTERCEPTION,           sB2:1,    sSy:1}},
  climate_dry: {{sP:0.90, sPET:1.1, sI:FOREST_INTERCEPTION,           sB2:1,    sSy:1}},
  clearfell:   {{sP:1,    sPET:1,   sI:0,                             sB2:1.35, sSy:1}},
  broadleaf:   {{sP:1,    sPET:1,   sI:BROADLEAF_INTERCEPTION,        sB2:1.45, sSy:1}},
  thinning:    {{sP:1,    sPET:1,   sI:FOREST_INTERCEPTION*0.5,       sB2:1.15, sSy:1}},
}};
var WARN={{
  clearfell:   'Post-felling: canopy interception removed, \u03b2\u2082 increases. Study finding: clearfell deepens summer minima \u2014 the dominant control on winter flooding probability.',
  broadleaf:   'Broadleaf conversion (25% interception, higher \u03b2\u2082). Study finding: hydrologically worse for wet slack conservation than Corsican pine.',
  climate_dry: 'Climate dry: \u221210% P, +10% PET. Summer minima deepen across all clusters.',
}};
var sea='annual',mm='dh',cm='dh',hChart=null;
var DH={{}},SH={{}},CUR_SL={{}};
var MW=0,MH=0;

function gs(){{return{{sP:+document.getElementById('sP').value,sPET:+document.getElementById('sPET').value,sI:+document.getElementById('sI').value,sB2:+document.getElementById('sB2').value,sSy:+document.getElementById('sSy').value}};}}
function rl(){{var s=gs();document.getElementById('vP').textContent=s.sP.toFixed(2)+'\xd7';document.getElementById('vPET').textContent=s.sPET.toFixed(2)+'\xd7';document.getElementById('vI').textContent=(s.sI*100).toFixed(0)+'%';document.getElementById('vB2').textContent=s.sB2.toFixed(2)+'\xd7';document.getElementById('vSy').textContent=s.sSy.toFixed(2)+'\xd7';}}
function onSl(){{rl();go();}}
function loadSc(n){{document.querySelectorAll('.sc').forEach(function(b){{b.classList.remove('on');}});document.getElementById('btn_'+n).classList.add('on');var sc=SCEN[n];['sP','sPET','sI','sB2','sSy'].forEach(function(k){{document.getElementById(k).value=sc[k];}});rl();var wb=document.getElementById('warnBox');if(WARN[n]){{wb.textContent=WARN[n];wb.style.display='block';}}else wb.style.display='none';go();}}
function setSeas(s){{sea=s;document.querySelectorAll('.tab').forEach(function(b){{b.classList.remove('on');}});document.getElementById('tab_'+s).classList.add('on');go();}}
function setMM(m){{mm=m;document.querySelectorAll('[id^="rt_"]').forEach(function(b){{b.classList.remove('on');}});document.getElementById('rt_'+m).classList.add('on');drawMap();}}
function setCM(m){{cm=m;document.querySelectorAll('[id^="ct_"]').forEach(function(b){{b.classList.remove('on');}});document.getElementById('ct_'+m).classList.add('on');renderBar();}}
function syEff(w,sl){{return Math.max((w.sy!=null?w.sy:0.12)*sl.sSy,SY_FLOOR[w.cl]||0.12);}}

function go(){{
  var sl=gs();CUR_SL=sl;
  var cld=CLIMATE[sea],P0=cld.P,PET0=cld.PET;
  var well_dh={{}};
  for(var i=0;i<WELLS.length;i++){{
    var w=WELLS[i],b1=w.b1,b2=w.b2,b3=w.b3;
    if(b1==null){{var cb=CLIMATE.cluster_betas[w.cl]||{{}};b1=cb.b1;b2=cb.b2;b3=cb.b3;}}
    if(b1==null)continue;
    var h=sea==='annual'?w.mh:sea==='winter'?w.wh:w.sh;
    if(h==null)continue;
    var Pb0=(w.cl===4)?P0*(1-FOREST_INTERCEPTION):P0;
    var net0=b1*Pb0-b2*PET0-b3*Math.abs(h);
    var Psc=P0*sl.sP,PETsc=PET0*sl.sPET;
    var Peff_sc=(w.cl===4)?Psc*(1-sl.sI):Psc;
    var b2sc=(w.cl===4)?b2*sl.sB2:b2;
    well_dh[w.n]=(b1*Peff_sc-b2sc*PETsc-b3*Math.abs(h)-net0)/syEff(w,sl);
  }}
  var dh={{}},sh={{}};
  for(var cl=1;cl<=5;cl++){{
    var wc=WELLS.filter(function(w){{return w.cl===cl;}}),sum=0,cnt=0;
    for(var i=0;i<wc.length;i++){{if(well_dh[wc[i].n]!=null){{sum+=well_dh[wc[i].n];cnt++;}}}}
    dh[cl]=cnt>0?sum/cnt:0;
    sh[cl]=(cld.cluster_heads[cl]||0)+dh[cl];
  }}
  DH=dh;SH=sh;
  for(var i=0;i<WELLS.length;i++){{
    WELLS[i]._dh=well_dh[WELLS[i].n]!=null?well_dh[WELLS[i].n]:null;
    var hb=sea==='annual'?WELLS[i].mh:sea==='winter'?WELLS[i].wh:WELLS[i].sh;
    WELLS[i]._sh=(hb!=null&&WELLS[i]._dh!=null)?hb+WELLS[i]._dh:null;
  }}
  drawMap();renderBar();renderTable();renderMetrics();
}}

function dhCol(t){{t=Math.max(-1,Math.min(1,t));if(t>0){{var f=t;return[Math.round(255*(1-f*0.75)),Math.round(255*(1-f*0.75)),255];}}if(t<0){{var f=-t;return[255,Math.round(255*(1-f*0.75)),Math.round(255*(1-f*0.75))];}}return[255,255,255];}}
var GS=[[0,'#08306b'],[0.25,'#2171b5'],[0.5,'#74c476'],[0.75,'#fed976'],[1,'#e31a1c']];
function abCol(t){{t=Math.max(0,Math.min(1,t));for(var i=0;i<GS.length-1;i++){{if(t<=GS[i+1][0]){{var f=(t-GS[i][0])/(GS[i+1][0]-GS[i][0]),a=GS[i][1],b=GS[i+1][1];return[Math.round(parseInt(a.slice(1,3),16)+(parseInt(b.slice(1,3),16)-parseInt(a.slice(1,3),16))*f),Math.round(parseInt(a.slice(3,5),16)+(parseInt(b.slice(3,5),16)-parseInt(a.slice(3,5),16))*f),Math.round(parseInt(a.slice(5,7),16)+(parseInt(b.slice(5,7),16)-parseInt(a.slice(5,7),16))*f)];}}}}return[8,48,107];}}
function pip(px,py,poly){{var ins=false,n=poly.length;for(var i=0,j=n-1;i<n;j=i++){{var xi=poly[i][0],yi=poly[i][1],xj=poly[j][0],yj=poly[j][1];if(((yi>py)!==(yj>py))&&(px<(xj-xi)*(py-yi)/(yj-yi)+xi))ins=!ins;}}return ins;}}
function idw(px,py,pts){{var n=0,d=0;for(var i=0;i<pts.length;i++){{var dx=px-pts[i].E,dy=py-pts[i].N,d2=dx*dx+dy*dy;if(d2<1)return pts[i].v;var w=1/d2;n+=w*pts[i].v;d+=w;}}return d>0?n/d:0;}}
function tc(E,N){{return{{x:(E-EMIN)/(EMAX-EMIN)*MW,y:MH-(N-NMIN)/(NMAX-NMIN)*MH}};}}

function sizeMap(){{var wrap=document.getElementById('mwrap');MW=wrap.clientWidth;MH=Math.round(MW*(NMAX-NMIN)/(EMAX-EMIN));['mapBg','mapC'].forEach(function(id){{var c=document.getElementById(id);c.width=MW;c.height=MH;c.style.height=MH+'px';}});}}
function drawBg(){{var c=document.getElementById('mapBg'),ctx=c.getContext('2d');ctx.fillStyle='#c0ccba';ctx.fillRect(0,0,MW,MH);var sp=POLYS.site;if(!sp||!sp.length)return;ctx.beginPath();var p0=tc(sp[0][0],sp[0][1]);ctx.moveTo(p0.x,p0.y);for(var i=1;i<sp.length;i++){{var p=tc(sp[i][0],sp[i][1]);ctx.lineTo(p.x,p.y);}}ctx.closePath();ctx.fillStyle='#daebd2';ctx.fill();ctx.strokeStyle='#7aaa70';ctx.lineWidth=1.3;ctx.stroke();}}
function dpoly(ctx,poly,fill,stroke,lw){{if(!poly||poly.length<2)return;var p0=tc(poly[0][0],poly[0][1]);ctx.beginPath();ctx.moveTo(p0.x,p0.y);for(var i=1;i<poly.length;i++){{var p=tc(poly[i][0],poly[i][1]);ctx.lineTo(p.x,p.y);}}ctx.closePath();if(fill){{ctx.fillStyle=fill;ctx.fill();}}if(stroke){{ctx.strokeStyle=stroke;ctx.lineWidth=lw||1.6;ctx.setLineDash([]);ctx.stroke();}};}}

function drawMap(){{
  if(!MW)return;
  var canvas=document.getElementById('mapC'),ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,MW,MH);
  var pts=[];
  for(var i=0;i<WELLS.length;i++){{var w=WELLS[i];if(!w.E||!w.N)continue;var v=(mm==='dh')?(w._dh!=null?w._dh:0):(w._sh!=null?w._sh:0);pts.push({{E:w.E,N:w.N,v:v}});}}
  if(!pts.length)return;
  var vals=pts.map(function(p){{return p.v;}}),vMn=Math.min.apply(null,vals),vMx=Math.max.apply(null,vals);
  var dhMx=Math.max(Math.abs(vMn),Math.abs(vMx),0.005);
  var site=POLYS.site||[],ST=Math.max(10,Math.round(MW/55));
  var img=ctx.createImageData(MW,MH);
  for(var k=0;k<img.data.length;k+=4)img.data[k+3]=0;
  for(var py=0;py<MH;py+=ST){{for(var px=0;px<MW;px+=ST){{
    var E=EMIN+(px/MW)*(EMAX-EMIN),N=NMIN+((MH-py)/MH)*(NMAX-NMIN);
    if(site.length&&!pip(E,N,site))continue;
    var v=idw(E,N,pts),rgb=(mm==='dh')?dhCol(v/dhMx):abCol((v-vMn)/(vMx-vMn));
    for(var dy=0;dy<ST&&py+dy<MH;dy++){{for(var dx=0;dx<ST&&px+dx<MW;dx++){{
      if(site.length){{var E2=EMIN+((px+dx)/MW)*(EMAX-EMIN),N2=NMIN+((MH-py-dy)/MH)*(NMAX-NMIN);if(!pip(E2,N2,site))continue;}}
      var idx=4*((py+dy)*MW+(px+dx));img.data[idx]=rgb[0];img.data[idx+1]=rgb[1];img.data[idx+2]=rgb[2];img.data[idx+3]=215;
    }}}}
  }}}}
  ctx.putImageData(img,0,0);
  var kml=document.getElementById('chkKml').checked;
  if(kml){{
    if(POLYS.forest)    dpoly(ctx,POLYS.forest,   'rgba(80,40,130,0.12)','#6a0dad',1.7);
    if(POLYS.broadleaf) dpoly(ctx,POLYS.broadleaf,'rgba(30,120,80,0.35)','#1a7a50',1.8);
    if(POLYS.clearfell) dpoly(ctx,POLYS.clearfell,'rgba(230,100,20,0.45)','#e65014',2.0);
    if(POLYS.lake)      dpoly(ctx,POLYS.lake,     'rgba(20,80,200,0.50)','#1a50b0',1.5);
  }}
  var syV=WELLS.filter(function(w){{return w.sy!=null;}}).map(function(w){{return w.sy;}}),syMn=Math.min.apply(null,syV),syMx=Math.max.apply(null,syV);
  var showLbl=document.getElementById('chkLbl').checked;
  for(var i=0;i<WELLS.length;i++){{
    var w=WELLS[i];if(!w.E||!w.N)continue;
    var p=tc(w.E,w.N),r=w.sy!=null?2.5+((w.sy-syMn)/(syMx-syMn))*3.5:2.5;
    ctx.beginPath();ctx.arc(p.x,p.y,r,0,2*Math.PI);
    ctx.fillStyle='rgba(255,255,255,0.9)';ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.48)';ctx.lineWidth=0.7;ctx.stroke();
    if(showLbl&&MW>360){{ctx.fillStyle='rgba(0,0,0,0.6)';ctx.font='7px sans-serif';ctx.textAlign='left';ctx.fillText(w.n,p.x+r+1,p.y+2.5);}}
  }}
  var ld=document.getElementById('legDiv');
  var kl=kml?'<span><span class="ls" style="background:rgba(230,100,20,0.55);border:1px solid #e65014;"></span>Clearfell</span><span><span class="ls" style="background:rgba(30,120,80,0.45);border:1px solid #1a7a50;"></span>Broadleaf</span><span><span class="ls" style="background:rgba(80,40,130,0.25);border:1px solid #6a0dad;"></span>Forest</span><span><span class="ls" style="background:rgba(20,80,200,0.5);border:1px solid #1a50b0;"></span>Llyn Rhos-ddu</span>':'';
  if(mm==='dh'){{ld.innerHTML='<span style="color:#b71c1c">'+vMn.toFixed(3)+'&#8202;m</span><canvas id="lc" width="70" height="9" style="width:70px;height:9px;border-radius:2px;vertical-align:middle;"></canvas><span style="color:#0d47a1">+'+(vMx).toFixed(3)+'&#8202;m</span><span>red&#8202;=&#8202;drier &middot; blue&#8202;=&#8202;wetter</span>'+kl;setTimeout(function(){{var c=document.getElementById('lc');if(!c)return;var x=c.getContext('2d'),g=x.createLinearGradient(0,0,70,0);g.addColorStop(0,'rgb(255,100,100)');g.addColorStop(0.5,'rgb(255,255,255)');g.addColorStop(1,'rgb(100,100,255)');x.fillStyle=g;x.fillRect(0,0,70,9);}},30);}}
  else{{ld.innerHTML='<span>Low</span><canvas id="lc" width="70" height="9" style="width:70px;height:9px;border-radius:2px;vertical-align:middle;"></canvas><span>High (m AOD)</span>'+kl;setTimeout(function(){{var c=document.getElementById('lc');if(!c)return;var x=c.getContext('2d'),g=x.createLinearGradient(0,0,70,0);GS.forEach(function(s){{g.addColorStop(s[0],s[1]);}});x.fillStyle=g;x.fillRect(0,0,70,9);}},30);}}
}}

document.addEventListener('DOMContentLoaded',function(){{
  document.getElementById('mapC').addEventListener('mousemove',function(e){{
    if(!MW)return;
    var r=this.getBoundingClientRect(),sx=MW/r.width,mx=(e.clientX-r.left)*sx,my=(e.clientY-r.top)*sx;
    var best=null,bd=Infinity;
    for(var i=0;i<WELLS.length;i++){{var w=WELLS[i];if(!w.E||!w.N)continue;var p=tc(w.E,w.N),d=Math.hypot(mx-p.x,my-p.y);if(d<bd){{bd=d;best=w;}}}}
    var tip=document.getElementById('tipDiv');
    if(best&&bd<18){{var hb=sea==='annual'?best.mh:sea==='winter'?best.wh:best.sh,dh=best._dh||0;tip.textContent=best.n+' \u00b7 C'+best.cl+' \u00b7 baseline '+hb.toFixed(2)+'\u00a0m\u00a0AOD \u00b7 scenario '+(hb+dh).toFixed(2)+'\u00a0m\u00a0AOD \u00b7 \u0394h '+(dh>=0?'+':'')+dh.toFixed(3)+'\u00a0m'+(best.sy?' \u00b7 Sy\u00a0'+(best.sy*100).toFixed(1)+'%':'');}}else tip.textContent='';
  }});
}});

function renderBar(){{
  var cls=[1,2,3,4,5];if(hChart)hChart.destroy();var ds,yL;
  if(cm==='dh'){{yL='\u0394h (m)';ds=[{{label:'\u0394h vs baseline',data:cls.map(function(c){{return+(DH[c]||0).toFixed(4);}}),backgroundColor:cls.map(function(c){{var v=DH[c]||0;return v>0.001?'rgba(21,101,192,0.65)':v<-0.001?'rgba(183,28,28,0.65)':'rgba(120,120,120,0.3)'}}),borderColor:cls.map(function(c){{var v=DH[c]||0;return v>0.001?'#1565c0':v<-0.001?'#b71c1c':'#aaa'}}),borderWidth:1.5}}];}}
  else{{yL='m AOD';ds=[{{label:'Baseline',data:cls.map(function(c){{return+(CLIMATE[sea].cluster_heads[c]||0).toFixed(3);}}),backgroundColor:'rgba(120,120,120,0.2)',borderColor:'rgba(120,120,120,0.55)',borderWidth:1}},{{label:'Scenario',data:cls.map(function(c){{return+(SH[c]||0).toFixed(3);}}),backgroundColor:cls.map(function(c){{return CL_COLS[c]+'99';}}),borderColor:cls.map(function(c){{return CL_COLS[c];}}),borderWidth:1.5}}];}}
  hChart=new Chart(document.getElementById('hC').getContext('2d'),{{type:'bar',data:{{labels:cls.map(function(c){{return CL_LABS[c];}}),datasets:ds}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{font:{{size:10}},boxWidth:9,padding:7}}}}}},scales:{{y:{{title:{{display:true,text:yL,font:{{size:10}}}},ticks:{{font:{{size:10}}}},grid:{{color:'rgba(0,0,0,0.06)'}}}},x:{{ticks:{{font:{{size:10}},maxRotation:15}}}}}}}}}});
}}

function renderTable(){{
  var cls=[1,2,3,4,5],sl=CUR_SL||{{sSy:1}},cld=CLIMATE[sea],P=cld.P,PET=cld.PET;
  var rows=[
    {{l:'Baseline (m AOD)',v:cls.map(function(c){{return(cld.cluster_heads[c]||0).toFixed(2);}}),d:false}},
    {{l:'Scenario (m AOD)',v:cls.map(function(c){{return(SH[c]||0).toFixed(2);}}),d:false}},
    {{l:'\u0394 head (m)',v:cls.map(function(c){{return(DH[c]>=0?'+':'')+(DH[c]||0).toFixed(3);}}),d:true}},
    {{l:'Mean Sy (%)',v:cls.map(function(c){{var cw=WELLS.filter(function(w){{return w.cl===c&&w.sy!=null;}});if(!cw.length)return'\u2014';var s=cw.reduce(function(acc,w){{return acc+Math.max((w.sy||0.12)*sl.sSy,SY_FLOOR[c]||0.12);}},0)/cw.length;return(s*100).toFixed(1)+'%';}}),d:false}},
    {{l:'P\u2091\u2091 mm/mo',v:cls.map(function(c){{return((c===4?P*sl.sP*(1-sl.sI):P*sl.sP)*1000).toFixed(1);}}),d:false}},
    {{l:'PET draw mm/mo',v:cls.map(function(c){{var cb=CLIMATE.cluster_betas[c]||{{}},b2=cb.b2||0,b2s=(c===4)?b2*sl.sB2:b2;return(b2s*PET*sl.sPET*1000).toFixed(1);}}),d:false}},
  ];
  function bg(v,d){{if(!d)return'#f5f5f5';var n=parseFloat(v);return n>0.005?'#c8e6c9':n<-0.005?'#ffcdd2':'#f5f5f5';}}
  function tx(v,d){{if(!d)return'#333';var n=parseFloat(v);return n>0.005?'#1b5e20':n<-0.005?'#b71c1c':'#555';}}
  document.getElementById('tbl').innerHTML='<div class="th"></div>'+cls.map(function(c){{return'<div class="th">C'+c+'</div>';}}).join('')+rows.map(function(r){{return'<div class="tl">'+r.l+'</div>'+r.v.map(function(v){{return'<div class="tc" style="background:'+bg(v,r.d)+';color:'+tx(v,r.d)+'">'+v+'</div>';}}).join('');}}).join('');
}}

function renderMetrics(){{
  var cls=[1,2,3,4,5],sl=CUR_SL||{{sSy:1}};
  var mDH=cls.reduce(function(s,c){{return s+(DH[c]||0);}},0)/5,c4DH=DH[4]||0;
  function dc(v){{return v>0.002?'#0d47a1':v<-0.002?'#b71c1c':'#333';}}
  function mc(l,v,u,col){{return'<div class="mc"><div class="ml">'+l+'</div><div class="mv" style="color:'+col+'">'+v+' <span class="mu">'+u+'</span></div></div>';}}
  var cw=WELLS.filter(function(w){{return w.sy!=null;}}),mSy=cw.length?cw.reduce(function(s,w){{return s+Math.max((w.sy||0.12)*sl.sSy,SY_FLOOR[w.cl]||0.12);}},0)/cw.length:0.15;
  var c4w=WELLS.filter(function(w){{return w.cl===4&&w.sy!=null;}}),c4Sy=c4w.length?c4w.reduce(function(s,w){{return s+Math.max((w.sy||0.12)*sl.sSy,SY_FLOOR[4]||0.12);}},0)/c4w.length:0.12;
  document.getElementById('mrow').innerHTML=mc('Mean \u0394h',(mDH>=0?'+':'')+mDH.toFixed(3),'m',dc(mDH))+mc('C4 \u0394h',(c4DH>=0?'+':'')+c4DH.toFixed(3),'m',dc(c4DH))+mc('Mean Sy',(mSy*100).toFixed(1),'%','#333')+mc('C4 Sy',(c4Sy*100).toFixed(1),'%','#333');
}}

function applyLayout(){{document.getElementById('mainGrid').style.gridTemplateColumns=window.innerWidth<640?'1fr':'210px minmax(0,1fr)';}}
function init(){{applyLayout();sizeMap();drawBg();document.getElementById('sI').value=FOREST_INTERCEPTION;rl();go();}}
setTimeout(init,60);
window.addEventListener('resize',function(){{applyLayout();sizeMap();drawBg();drawMap();}});
</script>
</body>
</html>
"""


# ============================================================================
# MAIN
# ============================================================================

def main(out_path=None):
    make_all_dirs()
    out_path = Path(out_path) if out_path else DIR_19 / "scenario_viewer.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Script 19 -- Scenario Viewer Generator")
    print(f"Output: {out_path}")
    print("=" * 60)

    print("\n[1/4] Loading data...")
    loc, cl, md, elev, maod, clim, sy_df = load_data()

    print("\n[2/4] Building well table...")
    wt, climate_stats = build_well_table(loc, cl, md, elev, maod, clim, sy_df)

    print("\n[3/4] Loading KML polygons from DATA_DIR...")
    print(f"  DATA_DIR = {DATA_DIR}")
    polys = load_kml_polygons()

    print("\n[4/4] Generating HTML...")
    wells_list   = serialise_wells(wt)
    climate_data = serialise_climate(wt, climate_stats)
    sy_floor_js  = {str(k): v for k, v in SY_FLOOR.items()}

    html = HTML_TEMPLATE.format(
        n_wells=len(wt),
        wells_json=json.dumps(wells_list, separators=(",", ":")),
        polys_json=json.dumps(polys, separators=(",", ":")),
        climate_json=json.dumps(climate_data, separators=(",", ":")),
        sy_floor_json=json.dumps(sy_floor_js, separators=(",", ":")),
        forest_interception=FOREST_INTERCEPTION,
        broadleaf_interception=BROADLEAF_INTERCEPTION,
    )

    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024

    print(f"\n  Saved   : {out_path}")
    print(f"  Size    : {size_kb:.1f} KB")
    print(f"  Wells   : {len(wt)} total  "
          f"(beta available: {wt['b1'].notna().sum()})")
    print(f"  KML     : {list(polys.keys())}")
    print(f"\n--- Script 19 complete ---")
    print(f"Open {out_path.name} in any browser.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script 19 -- Generate self-contained scenario viewer HTML")
    parser.add_argument(
        "--out", default=None,
        help="Output path (default: outputs/19_spatial_groundwater/"
             "scenario_viewer.html)")
    args = parser.parse_args()
    main(out_path=args.out)
