"""
19b_scraping_simulator.py
=========================
Scraping & Coastal Erosion Simulator — Newborough Warren 2005-2026
Hollingham (2026)

Standalone interactive HTML tool that simulates two processes the
equilibrium scenario viewer (Script 19) cannot represent:

  1. Dune scraping — a one-off level shift that equilibrates over time
     via the SSM drainage mechanism (β₃).
  2. Coastal erosion — a progressive, spatially-structured head decline
     propagating inland from the SW coastline.

Output: a single self-contained HTML file with embedded well data.

Usage:
    python 19b_scraping_simulator.py
"""

__version__ = "1.1.0"   # Hollingham (2026) — 2026-05-07
                         # v1.1.0: Resizable chart panel (drag bottom edge);
                         #         map shows per-well projected Δdepth at
                         #         selected map-year; Y-axis clamped to
                         #         user-set range; no DEM hillshade.

import sys, json, warnings
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from utils.paths import (
    make_all_dirs, DATA_DIR, OUT_DIR,
    INT_LOCATIONS, INT_CLIMATE, INT_CLUSTER_STATS,
    INT_MASTER_DATA, INT_WELL_ELEVATIONS,
    INT_WELLS_CLEAN, INT_WELLS_CLEAN_MAOD, OUT_18_WELL_SY_TABLE,
)
from utils.data_utils import normalize_well_name
from utils.config import (
    DRAINAGE_DATUM, FOREST_INTERCEPTION,
    CLUSTER_COLOURS, CLUSTER_LABELS,
    SD15b, SD16, SD15b_WINTER,
)

DIR_19B = OUT_DIR / "19b_scraping_simulator"
OUT_19B_SIMULATOR = DIR_19B / "scraping_simulator.html"

MONITOR_START = "2005-04-01"
MONITOR_END   = "2026-02-28"
S_COAST_N, W_COAST_E = 362350, 240200
SY_DEFAULTS = {1: 0.08, 2: 0.12, 3: 0.12, 4: 0.12, 5: 0.10}
EXCLUDE_WELLS = {"ceh12", "ceh15"}
VIEWER_EMIN, VIEWER_EMAX = 240200, 243700
VIEWER_NMIN, VIEWER_NMAX = 362400, 364800

def _norm(s):
    return str(s).lower().replace(" ", "").replace("-", "").strip()

def load_data():
    loc  = pd.read_csv(INT_LOCATIONS);  loc["id"] = loc["Match_ID"].apply(_norm)
    cl   = pd.read_csv(INT_CLUSTER_STATS); cl["id"] = cl["Match_ID"].apply(_norm)
    md   = pd.read_csv(INT_MASTER_DATA);   md["id"] = md["Name_Original"].apply(_norm)
    elev = pd.read_csv(INT_WELL_ELEVATIONS); elev["id"] = elev["Name_norm"].apply(_norm)
    wells_bg = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    wells_bg.columns = [_norm(c) for c in wells_bg.columns]
    wells_bg = wells_bg.loc[MONITOR_START:MONITOR_END]
    maod = pd.read_csv(INT_WELLS_CLEAN_MAOD, index_col=0, parse_dates=True)
    maod.columns = [_norm(c) for c in maod.columns]
    maod = maod.loc[MONITOR_START:MONITOR_END]
    clim = pd.read_csv(INT_CLIMATE, parse_dates=["Date"], index_col="Date")
    clim = clim.loc[MONITOR_START:MONITOR_END]
    sy_df = None
    if OUT_18_WELL_SY_TABLE.exists():
        sy_df = pd.read_csv(OUT_18_WELL_SY_TABLE)
        wcol = "Well_Normalised" if "Well_Normalised" in sy_df.columns else "Well"
        sy_df["id"] = sy_df[wcol].apply(_norm)
    return loc, cl, md, elev, wells_bg, maod, clim, sy_df

def build_well_data(loc, cl, md, elev, wells_bg, maod, clim, sy_df):
    wt = loc[["id", "E", "N"]].copy()
    wt = wt.merge(cl[["id", "Cluster"]], on="id", how="left")
    wt = wt.merge(md[["id", "beta_1_recharge", "beta_2_atmospheric_draw",
        "beta_3_drainage"]].rename(columns={"beta_1_recharge":"b1",
        "beta_2_atmospheric_draw":"b2","beta_3_drainage":"b3"}), on="id", how="left")
    if "DEM_Ground_Elev" in elev.columns:
        wt = wt.merge(elev[["id","DEM_Ground_Elev"]].rename(
            columns={"DEM_Ground_Elev":"dem_g"}), on="id", how="left")
    else: wt["dem_g"] = np.nan
    if sy_df is not None:
        wt["sy"] = wt["id"].map(dict(zip(sy_df["id"], sy_df["Sy_median"])))
    else: wt["sy"] = np.nan
    def fill_sy(r):
        if pd.notna(r["sy"]): return r["sy"]
        return SY_DEFAULTS.get(int(r["Cluster"]) if pd.notna(r["Cluster"]) else 3, 0.12)
    wt["sy"] = wt.apply(fill_sy, axis=1)
    def dist_to_coast(r):
        return max(0, min(r["N"] - S_COAST_N, r["E"] - W_COAST_E))
    wt["coast_dist"] = wt.apply(dist_to_coast, axis=1)
    wt = wt[~wt["id"].isin(EXCLUDE_WELLS)].dropna(subset=["E","N"]).reset_index(drop=True)

    climate_monthly = [{"date":dt.strftime("%Y-%m"),
        "P":round(float(clim.loc[dt,"P_m"]),5),
        "PET":round(float(clim.loc[dt,"PET"]),5)} for dt in clim.index]
    cmm = clim.groupby(clim.index.month).agg(P_m=("P_m","mean"),PET=("PET","mean"))
    mean_year = [{"P":round(float(cmm.loc[m,"P_m"]),5),
        "PET":round(float(cmm.loc[m,"PET"]),5)} for m in range(1,13)]

    wells_list = []
    for _, r in wt.iterrows():
        wid = r["id"]; cl_int = int(r["Cluster"]) if pd.notna(r["Cluster"]) else 3
        depth_ts = []
        if wid in wells_bg.columns:
            depth_ts = [round(float(v),4) if pd.notna(v) else None for v in wells_bg[wid]]
        mh = float(maod[wid].mean()) if wid in maod.columns and maod[wid].notna().any() else None
        wells_list.append({"n":wid,"cl":cl_int,
            "E":round(float(r["E"])),"N":round(float(r["N"])),
            "b1":round(float(r["b1"]),6) if pd.notna(r["b1"]) else None,
            "b2":round(float(r["b2"]),6) if pd.notna(r["b2"]) else None,
            "b3":round(float(r["b3"]),6) if pd.notna(r["b3"]) else None,
            "sy":round(float(r["sy"]),4) if pd.notna(r["sy"]) else 0.12,
            "dg":round(float(r["dem_g"]),2) if pd.notna(r["dem_g"]) else None,
            "cd":round(float(r["coast_dist"])),
            "mh":round(float(mh),3) if mh is not None else None,
            "ts":depth_ts})
    dates = [dt.strftime("%Y-%m") for dt in wells_bg.index]
    print(f"  Well table: {len(wells_list)} wells")
    print(f"  Beta available: {sum(1 for w in wells_list if w['b1'] is not None)} wells")
    print(f"  Climate months: {len(climate_monthly)}, TS months: {len(dates)}")
    return wells_list, climate_monthly, mean_year, dates

HARDCODED_POLYS = {
    "clearfell":[[241062,363621],[241170,363796],[241354,363679],[241235,363505],[241062,363621]],
    "broadleaf":[[241298,364491],[241316,364469],[241348,364365],[241428,364295],[241424,364259],[241411,364210],[241406,364158],[241607,364051],[241717,364207],[241692,364218],[241654,364245],[241629,364259],[241539,364315],[241465,364360],[241327,364543],[241298,364491]],
    "lake":[[242613,364937],[242576,364938],[242543,364924],[242512,364902],[242479,364860],[242457,364849],[242429,364818],[242397,364788],[242360,364764],[242352,364750],[242356,364729],[242384,364730],[242405,364749],[242435,364773],[242476,364786],[242507,364807],[242531,364822],[242554,364832],[242574,364853],[242597,364869],[242619,364882],[242631,364899],[242628,364919],[242613,364937]],
    "forest":[[241554,364966],[241380,364725],[241715,364622],[241805,364349],[241024,363184],[240920,363331],[240650,363417],[240650,365100],[241409,365100],[241554,364966]],
    "site":[[241088,362784],[240016,363370],[240000,364300],[240954,365000],[241436,365096],[242932,365034],[243680,364434],[243762,364180],[243604,363794],[243962,363656],[243816,363012],[243036,362266],[242066,362294],[241780,362156],[241088,362784]],
}

def load_kml_polygons():
    polys = {}
    try:
        import fiona; fiona.drvsupport.supported_drivers["KML"]="rw"
        import geopandas as gpd
        def kml_to_bng(path):
            if path is None or not Path(path).exists(): return []
            gdf = gpd.read_file(str(path),driver="KML").set_crs(epsg=4326,allow_override=True).to_crs("EPSG:27700")
            r = []
            for _,row in gdf.iterrows():
                g = row.geometry
                if g and g.geom_type=="Polygon":
                    r.append([[round(x),round(y)] for x,y in zip(g.exterior.xy[0],g.exterior.xy[1])])
            return r
        from utils.paths import DATA_KML_CLEARFELL, DATA_KML_FEATURES, KML_BROADLEAF
        cf = kml_to_bng(DATA_KML_CLEARFELL)
        if cf: polys["clearfell"]=cf[0]; print(f"  Clearfell (KML): {len(cf[0])} pts")
        bl = kml_to_bng(KML_BROADLEAF)
        if bl: polys["broadleaf"]=bl[0]; print(f"  Broadleaf (KML): {len(bl[0])} pts")
    except ImportError:
        print("  geopandas/fiona not available — using hardcoded KML coordinates.")
    for key, coords in HARDCODED_POLYS.items():
        if key not in polys:
            polys[key] = coords; print(f"  {key}: using hardcoded coordinates")
    return polys


# ============================================================================
# HTML TEMPLATE (single long string, double-braced for .format())
# ============================================================================

HTML_TEMPLATE = r"""<!DOCTYPE html>
<!-- Newborough Warren Scraping & Coastal Erosion Simulator v{version} -->
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Scraping & Coastal Erosion Simulator — Newborough Warren</title>
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{{--sand:#f4f0e6;--sand-dark:#e8e0cc;--dune:#c8b878;--slate:#3a4a52;--slate-light:#5a6e78;
  --water:#4a7a8a;--water-light:#6a9aaa;--pine:#3d5c3a;--text:#2a3338;--text-light:#5a6a72;
  --border:#d4c8a8;--alert:#c62828;--benefit:#1b5e20;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Source Sans 3',sans-serif;font-size:14px;background:var(--sand);color:var(--text);line-height:1.6;}}
header{{background:var(--slate);color:#fff;padding:1.2rem 1.5rem 1rem;position:relative;overflow:hidden;}}
header::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--dune),var(--water),var(--pine));}}
.sl{{font-size:.68rem;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--dune);margin-bottom:.35rem;}}
header h1{{font-family:'Libre Baskerville',Georgia,serif;font-weight:700;font-size:clamp(1rem,2.5vw,1.3rem);line-height:1.25;color:#fff;margin-bottom:.25rem;}}
header p{{font-size:.75rem;color:rgba(255,255,255,.55);font-weight:300;}}
.bk{{position:absolute;top:1rem;right:1.5rem;font-size:.72rem;color:var(--dune);text-decoration:none;opacity:.7;}}
.bk:hover{{opacity:1;}}
.main{{display:flex;gap:0;padding:12px;align-items:flex-start;}}
@media(max-width:760px){{.main{{flex-direction:column;}}.ctrl{{width:100%!important;}}}}
.ctrl{{background:#fff;border:1px solid var(--border);border-radius:4px;padding:14px;width:230px;flex-shrink:0;overflow-y:auto;max-height:95vh;position:sticky;top:6px;}}
.ctrl h3{{font-family:'Libre Baskerville',Georgia,serif;font-size:.82rem;color:var(--slate);margin:.9rem 0 .4rem;border-bottom:1px solid var(--border);padding-bottom:.25rem;}}
.ctrl h3:first-child{{margin-top:0;}}
.ctrl label{{display:flex;align-items:center;gap:6px;font-size:.78rem;margin:6px 0;cursor:pointer;}}
.ctrl input[type=checkbox]{{accent-color:var(--water);}}
.sr{{display:flex;align-items:center;gap:6px;margin:5px 0;}}
.sr label{{flex:1;font-size:.75rem;margin:0;}}
.sr input[type=range]{{flex:2;height:4px;}}
.sr .val{{min-width:46px;text-align:right;font-size:.72rem;font-weight:600;color:var(--slate);}}
.ctrl select{{width:100%;padding:4px 6px;font-size:.75rem;border:1px solid var(--border);border-radius:3px;background:#fff;}}
.ctrl .note{{font-size:.68rem;color:var(--text-light);margin-top:4px;line-height:1.4;}}
.content{{flex:1;min-width:0;padding:0 0 0 12px;}}
.mw{{position:relative;width:100%;aspect-ratio:640/440;border:1px solid var(--border);border-radius:4px;overflow:hidden;background:#c0ccba;}}
.mw canvas{{display:block;width:100%;height:100%;position:absolute;top:0;left:0;}}
#mapC{{z-index:2;cursor:crosshair;}}#mapBg{{z-index:1;}}
.myr{{display:flex;align-items:center;gap:8px;margin-top:6px;font-size:.75rem;color:var(--text-light);}}
.myr input[type=range]{{flex:1;height:4px;}}.myr .val{{font-weight:600;color:var(--slate);min-width:40px;text-align:right;}}
.legend{{font-size:.68rem;color:var(--text-light);margin-top:4px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}}
.cw{{margin-top:12px;background:#fff;border:1px solid var(--border);border-radius:4px;padding:14px 14px 4px;position:relative;overflow:hidden;}}
.cw h3{{font-family:'Libre Baskerville',Georgia,serif;font-size:.82rem;color:var(--slate);margin-bottom:8px;}}
.ci{{position:relative;height:280px;overflow:hidden;}}.ci canvas{{width:100%!important;height:100%!important;}}
.cr{{height:7px;cursor:ns-resize;display:flex;align-items:center;justify-content:center;}}
.cr::after{{content:'';width:32px;height:3px;border-radius:2px;background:var(--border);transition:background .15s;}}
.cr:hover::after{{background:var(--water);}}
.metrics{{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px;}}
.mc{{background:#fff;border:1px solid var(--border);border-radius:4px;padding:10px 14px;flex:1;min-width:140px;}}
.mc .ml{{font-size:.68rem;color:var(--text-light);text-transform:uppercase;letter-spacing:.08em;}}
.mc .mv{{font-size:1.15rem;font-weight:600;margin-top:2px;}}.mc .mu{{font-size:.7rem;font-weight:400;color:var(--text-light);}}
.tip{{position:fixed;z-index:999;background:rgba(255,255,255,.96);border:1px solid var(--border);border-radius:4px;padding:6px 10px;font-size:.72rem;pointer-events:none;display:none;box-shadow:0 2px 8px rgba(0,0,0,.12);max-width:260px;line-height:1.5;}}
footer{{text-align:center;padding:1rem;font-size:.65rem;color:var(--text-light);}}footer a{{color:var(--water);}}
</style></head><body>
<header><div class="sl">Newborough Warren</div>
<h1>Scraping &amp; Coastal Erosion Simulator</h1>
<p>Forward SSM integration &middot; Hollingham (2026) &middot; v{version}</p>
<a class="bk" href="https://newbroman.github.io/Newborough_Hydrology/">&larr; Research Tools</a></header>
<div class="main">
<div class="ctrl" id="ctrlPanel">
<h3>Scraping</h3>
<label><input type="checkbox" id="chkScrape" checked onchange="run()"> Enable scraping</label>
<div><label style="font-size:.72rem;margin-bottom:2px">Scrape location</label>
<select id="selWell" onchange="run()"></select>
<div class="note">Or click a well on the map</div></div>
<div class="sr"><label>Depth</label><input type="range" id="slScrape" min="0.05" max="0.40" step="0.01" value="0.20" oninput="updSl();run()"><span class="val" id="vScrape">0.20 m</span></div>
<h3>Coastal Erosion</h3>
<label><input type="checkbox" id="chkCoast" onchange="run()"> Enable coastal erosion</label>
<div class="sr"><label>Rate</label><input type="range" id="slRate" min="0" max="60" step="1" value="29" oninput="updSl();run()"><span class="val" id="vRate">29 mm/yr</span></div>
<div class="sr"><label>K (m/d)</label><input type="range" id="slK" min="1" max="20" step="0.5" value="5" oninput="updSl();run()"><span class="val" id="vK">5.0</span></div>
<h3>Projection</h3>
<div class="sr"><label>Period</label><input type="range" id="slYears" min="5" max="50" step="1" value="20" oninput="updSl();run()"><span class="val" id="vYears">20 yr</span></div>
<div style="margin-top:6px"><label style="font-size:.72rem">Climate forcing</label>
<select id="selClimate" onchange="run()"><option value="observed">Observed monthly</option><option value="mean">Mean-year cycle</option></select></div>
<h3>Control Well</h3>
<select id="selCtrl" onchange="run()"><option value="auto">Auto (nearest same-cluster)</option></select>
<h3>Display</h3>
<label><input type="checkbox" id="chkLabels" onchange="drawMap()"> Well labels</label>
<label><input type="checkbox" id="chkKml" checked onchange="drawMap()"> KML overlays</label>
<label><input type="checkbox" id="chkCoastLine" checked onchange="drawMap()"> Coast reference</label>
<div class="note" style="margin-top:12px"><strong>Model:</strong> Forward SSM with &beta;<sub>1</sub>/&beta;<sub>2</sub>/&beta;<sub>3</sub> from Script&nbsp;03. Coastal erosion via 1D diffusion (erfc). Depth relative to <em>new</em> surface at scraped well.</div>
</div>
<div class="content">
<div class="mw" id="mwrap"><canvas id="mapBg"></canvas><canvas id="mapC"></canvas></div>
<div class="myr"><span>Map year:</span><input type="range" id="slMapYear" min="1" max="50" step="1" value="5" oninput="updMapYear()"><span class="val" id="vMapYear">5 yr</span></div>
<div class="legend" id="legDiv"></div>
<div class="cw" id="chartWrap"><h3 id="chartTitle">Projected Depth Below Surface</h3>
<div class="ci" id="chartInner"><canvas id="tsChart"></canvas></div>
<div class="cr" id="chartResize"></div></div>
<div class="metrics" id="metricsRow"></div>
</div></div>
<div class="tip" id="tipDiv"></div>
<footer>Scraping &amp; Coastal Erosion Simulator v{version} &middot; <a href="https://github.com/newbroman/Newborough_Hydrology">Newborough Hydrology</a> &middot; Hollingham (2026)</footer>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
var W={wells_json},CL={climate_json},MY={mean_year_json},DT={dates_json},PO={polys_json};
var EMIN={emin},EMAX={emax},NMIN={nmin},NMAX={nmax},DAT={datum};
var SD15b={sd15b},SD16={sd16},FI={forest_i},SCN={s_coast_n},WCE={w_coast_e};
var CC={{1:'#1a6faf',2:'#2ca02c',3:'#d62728',4:'#7f77dd',5:'#8B4513'}};
var CL_L={{1:'C1 Lake',2:'C2 Dune',3:'C3 Western',4:'C4 Forest',5:'C5 Coastal'}};
var MW=0,MH=0,tsCh=null,WSM={{}};

function tc(E,N){{return{{x:(E-EMIN)/(EMAX-EMIN)*MW,y:MH-(N-NMIN)/(NMAX-NMIN)*MH}};}}
function pip(px,py,po){{var ins=false,n=po.length;for(var i=0,j=n-1;i<n;j=i++){{var xi=po[i][0],yi=po[i][1],xj=po[j][0],yj=po[j][1];if(((yi>py)!==(yj>py))&&(px<(xj-xi)*(py-yi)/(yj-yi)+xi))ins=!ins;}}return ins;}}
function erfc(x){{var t=1/(1+.3275911*Math.abs(x)),y=t*(.254829592+t*(-.284496736+t*(1.421413741+t*(-1.453152027+t*1.061405429)))),e=y*Math.exp(-x*x);return x>=0?e:2-e;}}

function updSl(){{
  document.getElementById('vScrape').textContent=parseFloat(document.getElementById('slScrape').value).toFixed(2)+' m';
  document.getElementById('vRate').textContent=document.getElementById('slRate').value+' mm/yr';
  document.getElementById('vK').textContent=parseFloat(document.getElementById('slK').value).toFixed(1);
  document.getElementById('vYears').textContent=document.getElementById('slYears').value+' yr';
  var yr=parseInt(document.getElementById('slYears').value),my=document.getElementById('slMapYear');
  my.max=yr;if(parseInt(my.value)>yr)my.value=yr;updMapYear();
}}
function updMapYear(){{document.getElementById('vMapYear').textContent=document.getElementById('slMapYear').value+' yr';drawMap();}}

function popDD(){{
  var sel=document.getElementById('selWell'),ctrl=document.getElementById('selCtrl');
  var wb=W.filter(function(w){{return w.b1!=null&&w.ts&&w.ts.length>0&&w.dg!=null;}});
  wb.sort(function(a,b){{return a.n<b.n?-1:1;}});
  for(var i=0;i<wb.length;i++){{
    var w=wb[i],o=document.createElement('option');o.value=w.n;o.textContent=w.n+' (C'+w.cl+')';
    if(w.n==='ceh36')o.selected=true;sel.appendChild(o);
    var o2=document.createElement('option');o2.value=w.n;o2.textContent=w.n+' (C'+w.cl+')';ctrl.appendChild(o2);
  }}
}}
function getCtrl(sw){{
  var s=document.getElementById('selCtrl').value;
  if(s!=='auto')return W.find(function(w){{return w.n===s;}});
  var b=null,bd=1e9;
  for(var i=0;i<W.length;i++){{var w=W[i];if(w.n===sw.n||w.b1==null||!w.ts||!w.ts.length||w.dg==null)continue;if(w.cl!==sw.cl)continue;var d=Math.hypot(w.E-sw.E,w.N-sw.N);if(d<bd){{bd=d;b=w;}}}}
  if(!b)for(var i=0;i<W.length;i++){{var w=W[i];if(w.n===sw.n||w.b1==null||!w.ts||!w.ts.length||w.dg==null)continue;var d=Math.hypot(w.E-sw.E,w.N-sw.N);if(d<bd){{bd=d;b=w;}}}}
  return b;
}}

// Forward SSM for one well. sd=0 means no scrape.
function fwd(well,sd,cOn,cRate,K,nM,cm){{
  var b1=well.b1,b2=well.b2,b3=well.b3;if(b1==null||well.dg==null)return null;
  var iF=(well.cl===4||well.cl===5),dO=well.dg,dN=dO-sd;
  var ts=well.ts,lD=null;for(var k=ts.length-1;k>=0;k--)if(ts[k]!=null){{lD=ts[k];break;}}
  if(lD==null)return null;
  var h=dO+lD,cs=[];
  if(cm==='observed')for(var m=0;m<nM;m++)cs.push(CL[m%CL.length]);
  else for(var m=0;m<nM;m++)cs.push(MY[m%12]);
  var res=[];
  for(var t=0;t<nM;t++){{
    var hp=h,hd=DAT+(hp-dO),P=cs[t].P,PET=cs[t].PET;
    var Pe=iF?P*(1-FI):P;var dh=b1*Pe-b2*PET-b3*Math.max(0,hd);h=hp+dh;
    var cdh=0;
    if(cOn&&cRate>0&&well.cd>0){{var td=(t+1)*30.44,D=K/(well.sy||.12),L=well.cd;cdh=-(cRate/1000)*(td/365.25)*erfc(L/(2*Math.sqrt(D*Math.max(td,1))));h+=cdh;}}
    res.push({{m:t,h:h,dn:dN-h,do_:dO-h,cd:cdh}});
  }}return res;
}}

function runAll(swn,sd,cOn,cRate,K,yr,cm){{
  WSM={{}};var nM=yr*12,scrOn=document.getElementById('chkScrape').checked;
  for(var i=0;i<W.length;i++){{var w=W[i];if(w.b1==null||w.dg==null||!w.ts||!w.ts.length)continue;
    var s=(w.n===swn&&scrOn)?sd:0;var r=fwd(w,s,cOn,cRate,K,nM,cm);if(r)WSM[w.n]=r;}}
}}

function run(){{
  var scrOn=document.getElementById('chkScrape').checked,cOn=document.getElementById('chkCoast').checked;
  var sd=scrOn?parseFloat(document.getElementById('slScrape').value):0;
  var cRate=parseFloat(document.getElementById('slRate').value),K=parseFloat(document.getElementById('slK').value);
  var yr=parseInt(document.getElementById('slYears').value),cm=document.getElementById('selClimate').value;
  var wn=document.getElementById('selWell').value,sw=W.find(function(w){{return w.n===wn;}});
  if(!sw||sw.b1==null||!sw.dg)return;
  var cw=getCtrl(sw),nM=yr*12;
  var sim=fwd(sw,sd,cOn,cRate,K,nM,cm),simB=fwd(sw,0,cOn,cRate,K,nM,cm);
  var simC=cw?fwd(cw,0,cOn,cRate,K,nM,cm):null;
  if(!sim||!simB)return;
  runAll(wn,parseFloat(document.getElementById('slScrape').value),cOn,cRate,K,yr,cm);
  drawMap(sw,cw);renderChart(sim,simB,simC,sw,cw,sd,yr);renderMet(sim,simB,sd,sw,cOn,yr);
}}

function sizeMap(){{var wr=document.getElementById('mwrap');MW=wr.clientWidth;MH=wr.clientHeight;
  ['mapBg','mapC'].forEach(function(id){{var c=document.getElementById(id);c.width=MW;c.height=MH;}});}}
function drawBg(){{var c=document.getElementById('mapBg'),x=c.getContext('2d');x.fillStyle='#c0ccba';x.fillRect(0,0,MW,MH);
  var sp=PO.site;if(sp&&sp.length){{x.beginPath();var p0=tc(sp[0][0],sp[0][1]);x.moveTo(p0.x,p0.y);
  for(var i=1;i<sp.length;i++){{var p=tc(sp[i][0],sp[i][1]);x.lineTo(p.x,p.y);}}x.closePath();x.fillStyle='#daebd2';x.fill();x.strokeStyle='#7aaa70';x.lineWidth=1.3;x.stroke();}}}}
function dpoly(x,po,fl,st,lw){{if(!po||po.length<2)return;var p0=tc(po[0][0],po[0][1]);x.beginPath();x.moveTo(p0.x,p0.y);
  for(var i=1;i<po.length;i++){{var p=tc(po[i][0],po[i][1]);x.lineTo(p.x,p.y);}}x.closePath();
  if(fl){{x.fillStyle=fl;x.fill();}}if(st){{x.strokeStyle=st;x.lineWidth=lw||1.6;x.setLineDash([]);x.stroke();}}}}

function drawMap(sw,cw){{
  if(!MW)return;var cv=document.getElementById('mapC'),x=cv.getContext('2d');x.clearRect(0,0,MW,MH);
  if(document.getElementById('chkKml').checked){{
    if(PO.forest)dpoly(x,PO.forest,'rgba(80,40,130,.10)','#6a0dad',1.3);
    if(PO.broadleaf)dpoly(x,PO.broadleaf,'rgba(30,120,80,.25)','#1a7a50',1.3);
    if(PO.clearfell)dpoly(x,PO.clearfell,'rgba(230,100,20,.35)','#e65014',1.6);
    if(PO.lake)dpoly(x,PO.lake,'rgba(20,80,200,.40)','#1a50b0',1.2);
  }}
  if(document.getElementById('chkCoastLine').checked){{
    var pS0=tc(EMIN,SCN),pS1=tc(EMAX,SCN);x.beginPath();x.moveTo(pS0.x,pS0.y);x.lineTo(pS1.x,pS1.y);
    x.strokeStyle='rgba(0,100,200,.35)';x.lineWidth=1.5;x.setLineDash([6,4]);x.stroke();x.setLineDash([]);
    var pW0=tc(WCE,NMIN),pW1=tc(WCE,NMAX);x.beginPath();x.moveTo(pW0.x,pW0.y);x.lineTo(pW1.x,pW1.y);x.stroke();x.setLineDash([]);
    x.fillStyle='rgba(0,100,200,.45)';x.font='9px Source Sans 3,sans-serif';x.textAlign='left';x.fillText('S coast',pS0.x+4,pS0.y-4);
  }}
  // Compute per-well Δdepth at the map year
  var mY=parseInt(document.getElementById('slMapYear').value),mM=Math.min(mY*12-1,99999);
  var wDh={{}},mxA=.001;
  for(var wn in WSM){{var s=WSM[wn];if(!s||!s.length)continue;
    var w=W.find(function(ww){{return ww.n===wn;}});if(!w||w.dg==null)continue;
    var lD=null;for(var k=w.ts.length-1;k>=0;k--)if(w.ts[k]!=null){{lD=w.ts[k];break;}}
    if(lD==null)continue;
    var startD=-lD,endD=s[Math.min(mM,s.length-1)].do_,dh=startD-endD;
    wDh[wn]=dh;if(Math.abs(dh)>mxA)mxA=Math.abs(dh);
  }}
  var sL=document.getElementById('chkLabels').checked;
  for(var i=0;i<W.length;i++){{var w=W[i];if(!w.E||!w.N)continue;var p=tc(w.E,w.N);
    var dh=wDh[w.n],r=3.5,fl,sc;
    if(dh!=null){{var t=Math.max(-1,Math.min(1,dh/mxA));
      if(t>0)fl='rgba('+Math.round(255*(1-t*.7))+','+Math.round(255*(1-t*.7))+',255,.85)';
      else if(t<0){{var f=-t;fl='rgba(255,'+Math.round(255*(1-f*.7))+','+Math.round(255*(1-f*.7))+',.85)';}}
      else fl='rgba(200,200,200,.7)';
      r=3+Math.min(1,Math.abs(dh)/mxA)*3.5;sc='rgba(0,0,0,.35)';
    }}else{{fl='rgba(180,180,180,.5)';sc='rgba(0,0,0,.2)';r=2.5;}}
    x.beginPath();x.arc(p.x,p.y,r,0,2*Math.PI);x.fillStyle=fl;x.fill();x.strokeStyle=sc;x.lineWidth=.8;x.stroke();
    if(sL&&MW>300){{x.fillStyle='rgba(0,0,0,.5)';x.font='7px sans-serif';x.textAlign='left';x.fillText(w.n,p.x+r+2,p.y+3);}}
  }}
  if(sw){{var ps=tc(sw.E,sw.N);x.beginPath();x.arc(ps.x,ps.y,8,0,2*Math.PI);x.strokeStyle='#e65014';x.lineWidth=2.5;x.stroke();
    x.fillStyle='rgba(230,80,20,.15)';x.fill();x.fillStyle='#e65014';x.font='bold 9px Source Sans 3,sans-serif';x.textAlign='left';x.fillText('SCRAPE: '+sw.n,ps.x+11,ps.y+3);}}
  if(cw){{var pc=tc(cw.E,cw.N);x.beginPath();x.arc(pc.x,pc.y,6,0,2*Math.PI);x.strokeStyle='#1565c0';x.lineWidth=2;x.setLineDash([3,3]);x.stroke();x.setLineDash([]);
    x.fillStyle='#1565c0';x.font='8px Source Sans 3,sans-serif';x.textAlign='left';x.fillText('CTRL: '+cw.n,pc.x+9,pc.y+3);}}
  // Legend
  var ld=document.getElementById('legDiv');
  ld.innerHTML='<span>&Delta;depth at year '+mY+':</span> <span style="color:#b71c1c">&minus;'+(mxA*1000).toFixed(0)+' mm</span> '+
    '<canvas id="lc" width="80" height="9" style="width:80px;height:9px;border-radius:2px;vertical-align:middle"></canvas> '+
    '<span style="color:#0d47a1">+'+(mxA*1000).toFixed(0)+' mm</span><span style="margin-left:8px;font-size:.65rem">red=deeper &middot; blue=shallower</span>';
  setTimeout(function(){{var c=document.getElementById('lc');if(!c)return;var g=c.getContext('2d').createLinearGradient(0,0,80,0);
    g.addColorStop(0,'rgb(255,80,80)');g.addColorStop(.5,'rgb(220,220,220)');g.addColorStop(1,'rgb(80,80,255)');
    c.getContext('2d').fillStyle=g;c.getContext('2d').fillRect(0,0,80,9);}},30);
}}

function renderChart(sim,simB,simC,sw,cw,sd,yr){{
  if(tsCh)tsCh.destroy();var ctx=document.getElementById('tsChart').getContext('2d');
  var lb=sim.map(function(s){{return(s.m/12).toFixed(1);}}),ds=[],n=sim.length;
  if(sd>0){{
    ds.push({{label:sw.n+' (scraped)',data:sim.map(function(s){{return+s.dn.toFixed(4);}}),borderColor:'#e65014',borderWidth:2,fill:false,pointRadius:0,tension:.3}});
    ds.push({{label:sw.n+' (no scrape)',data:simB.map(function(s){{return+s.do_.toFixed(4);}}),borderColor:'#888',borderDash:[5,5],borderWidth:1.5,fill:false,pointRadius:0,tension:.3}});
  }}else{{
    ds.push({{label:sw.n+' (baseline)',data:simB.map(function(s){{return+s.do_.toFixed(4);}}),borderColor:'#e65014',borderWidth:2,fill:false,pointRadius:0,tension:.3}});
  }}
  if(simC)ds.push({{label:cw.n+' (control)',data:simC.map(function(s){{return+s.do_.toFixed(4);}}),borderColor:'#1565c0',borderWidth:1.5,fill:false,pointRadius:0,tension:.3,borderDash:[4,4]}});
  ds.push({{label:'SD15b ('+SD15b.toFixed(2)+' m)',data:new Array(n).fill(SD15b),borderColor:'rgba(21,101,192,.35)',borderDash:[8,4],borderWidth:1,pointRadius:0,fill:false}});
  ds.push({{label:'SD16 ('+SD16.toFixed(2)+' m)',data:new Array(n).fill(SD16),borderColor:'rgba(183,28,28,.35)',borderDash:[8,4],borderWidth:1,pointRadius:0,fill:false}});

  // Map-year vertical line via annotation plugin (or simple afterDraw)
  var myM=parseInt(document.getElementById('slMapYear').value)*12;
  document.getElementById('chartTitle').textContent='Depth: '+sw.n+(sd>0?' ('+sd.toFixed(2)+' m scrape)':'');

  tsCh=new Chart(ctx,{{type:'line',data:{{labels:lb,datasets:ds}},
    options:{{responsive:true,maintainAspectRatio:false,animation:{{duration:0}},
      plugins:{{legend:{{labels:{{font:{{size:10}},boxWidth:12,padding:8}}}},
        tooltip:{{mode:'index',intersect:false,callbacks:{{
          title:function(it){{return'Year '+it[0].label;}},
          label:function(it){{return it.dataset.label+': '+parseFloat(it.raw).toFixed(3)+' m';}}
        }}}}}},
      scales:{{
        x:{{title:{{display:true,text:'Years from start',font:{{size:11}}}},
          ticks:{{font:{{size:9}},callback:function(v,i){{return i%12===0?lb[i]:'';}},maxRotation:0}},
          grid:{{color:'rgba(0,0,0,.04)'}}}},
        y:{{reverse:true,min:0,max:Math.max(1.5,SD16+.3),
          title:{{display:true,text:'Depth below surface (m)',font:{{size:11}}}},
          ticks:{{font:{{size:10}}}},grid:{{color:'rgba(0,0,0,.06)'}}}}
      }}
    }},
    plugins:[{{id:'mapYearLine',afterDraw:function(chart){{
      var xA=chart.scales.x;if(!xA||myM>=n)return;
      var xP=xA.getPixelForValue(myM),yA=chart.scales.y;
      var ctx2=chart.ctx;ctx2.save();ctx2.beginPath();ctx2.moveTo(xP,yA.top);ctx2.lineTo(xP,yA.bottom);
      ctx2.strokeStyle='rgba(0,0,0,.25)';ctx2.lineWidth=1;ctx2.setLineDash([4,3]);ctx2.stroke();ctx2.setLineDash([]);
      ctx2.fillStyle='rgba(0,0,0,.4)';ctx2.font='9px sans-serif';ctx2.textAlign='center';
      ctx2.fillText('yr '+document.getElementById('slMapYear').value,xP,yA.top-4);ctx2.restore();
    }}}}]
  }});
}}

function renderMet(sim,simB,sd,well,cOn,yr){{
  var el=document.getElementById('metricsRow');if(!sim||!simB){{el.innerHTML='';return;}}
  var h='';function mc(l,v,u,c){{return'<div class="mc"><div class="ml">'+l+'</div><div class="mv" style="color:'+(c||'var(--text)')+'">'+v+' <span class="mu">'+u+'</span></div></div>';}}
  if(sd>0){{
    h+=mc('Initial benefit','+'+(sd*1000).toFixed(0),'mm','var(--benefit)');
    var fS=sim[sim.length-1].dn,fB=simB[simB.length-1].do_,ret=(fB-fS)*1000,rP=(ret/(sd*1000)*100).toFixed(0);
    h+=mc('Retained at '+yr+'yr',(ret>=0?'+':'')+ret.toFixed(0)+' mm ('+rP+'%)','','var(--benefit)');
    var eq=null;for(var t=1;t<sim.length;t++){{if(simB[t].do_-sim[t].dn<sd*.8){{eq=t;break;}}}}
    if(eq)h+=mc('80% equilibration','~'+(eq/12).toFixed(1),'years','var(--slate)');
    var cr=null;for(var t=0;t<sim.length;t++){{if(sim[t].dn>=simB[t].do_){{cr=t;break;}}}}
    if(cr!=null)h+=mc('Crossover',(cr/12).toFixed(1),'years','var(--alert)');
    else h+=mc('Crossover','> '+yr,'years','var(--text-light)');
  }}
  if(cOn){{var ct=sim[sim.length-1].cd;if(ct!=null&&Math.abs(ct)>.0001)h+=mc('Coastal impact',(ct*1000).toFixed(0),'mm',ct<-.01?'var(--alert)':'var(--text-light)');
    h+=mc('Dist to coast',well.cd,'m','var(--text-light)');}}
  el.innerHTML=h;
}}

function setupClick(){{
  document.getElementById('mapC').addEventListener('click',function(e){{
    var r=e.target.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,b=null,bd=1e9;
    for(var i=0;i<W.length;i++){{var w=W[i];if(!w.E||!w.N||w.b1==null||!w.ts||!w.ts.length||w.dg==null)continue;
      var p=tc(w.E,w.N),d=Math.hypot(mx-p.x,my-p.y);if(d<bd){{bd=d;b=w;}}}}
    if(b&&bd<25){{document.getElementById('selWell').value=b.n;run();}}
  }});
  document.getElementById('mapC').addEventListener('mousemove',function(e){{
    var r=e.target.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,b=null,bd=1e9;
    for(var i=0;i<W.length;i++){{var w=W[i];if(!w.E||!w.N)continue;var p=tc(w.E,w.N),d=Math.hypot(mx-p.x,my-p.y);if(d<bd){{bd=d;b=w;}}}}
    var tip=document.getElementById('tipDiv');
    if(b&&bd<15){{
      var mY=parseInt(document.getElementById('slMapYear').value),st=WSM[b.n],dt='';
      if(st){{var idx=Math.min(mY*12-1,st.length-1),lD=null;
        for(var k=b.ts.length-1;k>=0;k--)if(b.ts[k]!=null){{lD=b.ts[k];break;}}
        if(lD!=null){{var dh=(-lD)-st[idx].do_;dt='<br>&Delta;depth yr '+mY+': <b style="color:'+(dh>.001?'#0d47a1':dh<-.001?'#b71c1c':'#555')+'">'+(dh>=0?'+':'')+(dh*1000).toFixed(0)+' mm</b>';}}}}
      tip.innerHTML='<b>'+b.n+'</b> &middot; C'+b.cl+' '+(CL_L[b.cl]||'')+
        '<br>DEM: '+(b.dg!=null?b.dg.toFixed(1)+' m AOD':'?')+'<br>Coast: '+b.cd+' m'+
        (b.b1!=null?'<br>&beta;&#x2081;='+b.b1.toFixed(3)+' &beta;&#x2082;='+b.b2.toFixed(3)+' &beta;&#x2083;='+b.b3.toFixed(3):'')+
        '<br>Sy: '+(b.sy*100).toFixed(1)+'%'+dt;
      tip.style.display='block';var tx=e.clientX+14,ty=e.clientY-10;
      if(tx+tip.offsetWidth>window.innerWidth-10)tx=e.clientX-tip.offsetWidth-14;if(ty<5)ty=5;
      tip.style.left=tx+'px';tip.style.top=ty+'px';
    }}else tip.style.display='none';
  }});
  document.getElementById('mapC').addEventListener('mouseleave',function(){{document.getElementById('tipDiv').style.display='none';}});
}}

function setupResize(){{
  var h=document.getElementById('chartResize'),inn=document.getElementById('chartInner'),drag=false,sY=0,sH=0;
  h.addEventListener('mousedown',function(e){{drag=true;sY=e.clientY;sH=inn.offsetHeight;e.preventDefault();}});
  document.addEventListener('mousemove',function(e){{if(!drag)return;var nH=Math.max(120,Math.min(800,sH+(e.clientY-sY)));inn.style.height=nH+'px';if(tsCh)tsCh.resize();}});
  document.addEventListener('mouseup',function(){{drag=false;}});
}}

window.addEventListener('DOMContentLoaded',function(){{popDD();sizeMap();drawBg();updSl();setupClick();setupResize();run();}});
window.addEventListener('resize',function(){{sizeMap();drawBg();run();}});
</script></body></html>"""


def main():
    DIR_19B.mkdir(parents=True, exist_ok=True)
    out_path = OUT_19B_SIMULATOR
    print("=" * 60)
    print("Script 19b — Scraping & Coastal Erosion Simulator")
    print(f"Output: {out_path}")
    print("=" * 60)
    print("\n[1/4] Loading data...")
    loc, cl, md, elev, wells_bg, maod, clim, sy_df = load_data()
    print("\n[2/4] Building well data...")
    wells_list, climate_monthly, mean_year, dates = build_well_data(
        loc, cl, md, elev, wells_bg, maod, clim, sy_df)
    print("\n[3/4] Loading KML polygons...")
    polys = load_kml_polygons()
    print("\n[4/4] Generating HTML...")
    html = HTML_TEMPLATE.format(
        version=__version__,
        wells_json=json.dumps(wells_list, separators=(",", ":")),
        climate_json=json.dumps(climate_monthly, separators=(",", ":")),
        mean_year_json=json.dumps(mean_year, separators=(",", ":")),
        dates_json=json.dumps(dates, separators=(",", ":")),
        polys_json=json.dumps(polys, separators=(",", ":")),
        emin=VIEWER_EMIN, emax=VIEWER_EMAX,
        nmin=VIEWER_NMIN, nmax=VIEWER_NMAX,
        datum=DRAINAGE_DATUM, sd15b=SD15b, sd16=SD16,
        forest_i=FOREST_INTERCEPTION,
        s_coast_n=S_COAST_N, w_coast_e=W_COAST_E,
    )
    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"\n  Saved   : {out_path}")
    print(f"  Version : v{__version__}")
    print(f"  Size    : {size_kb:.1f} KB")
    print(f"  Wells   : {len(wells_list)} total  "
          f"(beta: {sum(1 for w in wells_list if w['b1'] is not None)})")
    print(f"\n--- Script 19b complete ---")
    print(f"Open {out_path.name} in any browser.")

if __name__ == "__main__":
    main()
