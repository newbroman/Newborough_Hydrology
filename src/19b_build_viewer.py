"""
19b_build_viewer.py  v2026-04-13-clean
========================================
Fresh rewrite of the scenario viewer.

Tab structure
-------------
  Forest Management  — diff maps for forest_removal, thinning, species_change
  Climate Change     — diff maps for climate_dry, climate_wet
  Baseline Maps      — all baseline figures
  Seasonal Profiles  — hydrographs + scatter link
"""

import base64, shutil
from pathlib import Path
import sys

SRC_DIR = Path(__file__).parent
sys.path.insert(0, str(SRC_DIR))
from utils.paths import OUT_DIR

BASE_DIR  = OUT_DIR / "19_spatial_groundwater"
DIFF_DIR  = BASE_DIR / "difference_maps"
ROOT_DIR  = OUT_DIR.parent
_REL_BASE = "outputs/19_spatial_groundwater"
_REL_DIFF = f"{_REL_BASE}/difference_maps"

SCATTER_SRC  = OUT_DIR / "14_climate_projections" / "14_seasonal_extremes_scatter.html"
SCATTER_ROOT = ROOT_DIR / "seasonal_extremes_scatter.html"

# ── Figure definitions ─────────────────────────────────────────────────────────
FOREST_SCENARIOS = [
    ("forest_removal",  "Full clearfell vs baseline"),
    ("forest_thinning", "Forest thinning 50% vs baseline"),
    ("species_change",  "Broadleaf conversion vs baseline"),
]
CLIMATE_SCENARIOS = [
    ("climate_dry", "Climate dry vs baseline"),
    ("climate_wet", "Climate wet vs baseline"),
]
DIFF_FIELDS = [
    ("mean_head",           "Mean water table (m AOD)"),
    ("winter_head",         "Winter mean water table (m AOD)"),
    ("summer_head",         "Summer minimum water table (m AOD)"),
    ("recharge_m_mon",      "Recharge (m/month)"),
    ("et_draw_m_mon",       "ET draw (m/month)"),
    ("drainage_m_mon",      "Drainage (m/month)"),
    ("lateral_inflow_m_mon","Lateral inflow residual (m/month)"),
    ("storage_change_mm",   "Seasonal storage change (mm)"),
    ("winter_depth_bg",     "Winter depth below ground (m)"),
    ("summer_depth_bg",     "Summer depth below ground (m)"),
]
BASELINE_FIGS = [
    ("19_head_mean_darcy.png",     "Mean water table + Darcy flux"),
    ("19_head_mean_map.png",       "Mean water table (m AOD)"),
    ("19_head_surface_winter.png", "Winter mean water table"),
    ("19_head_surface_summer.png", "Summer minimum water table"),
    ("19_aquifer_thickness.png",   "Aquifer thickness"),
    ("19_wb_recharge.png",         "Recharge"),
    ("19_wb_et.png",               "ET draw"),
    ("19_wb_drainage.png",         "Drainage"),
    ("19_lateral_flux.png",        "Darcy lateral flux"),
    ("19_winter_flooding.png",     "Winter flooding"),
    ("19_depth_to_watertable.png", "Depth to water table"),
    ("19_storage_change.png",      "Seasonal storage change"),
    ("19_residual_comparison.png", "SSM lateral inflow residual"),
]
HYGRO_FIGS = [
    ("cluster_hydrographs.png", "Seasonal hydrographs — all scenarios"),
    ("scenario_summary.png",    "Scenario summary — Δ summer depth"),
]


# ── Helpers ────────────────────────────────────────────────────────────────────
def b64(path):
    p = Path(path)
    return base64.b64encode(p.read_bytes()).decode("ascii") if p.exists() else None

def img(path, alt="", linked_rel=None):
    if linked_rel:
        p = Path(path)
        return (f'<img src="{linked_rel}" alt="{alt}" class="fig-img">'
                if p.exists() else
                f'<div class="missing">Not found: {alt}</div>')
    data = b64(path)
    return (f'<img src="data:image/png;base64,{data}" alt="{alt}" class="fig-img">'
            if data else
            f'<div class="missing">Not found: {alt}</div>')

def card(label, content):
    return (f'<div class="card">'
            f'<div class="card-label">{label}</div>'
            f'{content}</div>\n')


# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
:root{--bg:#0d1117;--surf:#161b22;--card:#1f2937;--border:#30363d;
      --text:#e6edf3;--muted:#8b949e;--accent:#64ffda;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);
     font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
     font-size:14px;line-height:1.5;}
/* ── Nav bar ── */
.navbar{background:var(--surf);border-bottom:2px solid var(--accent);
        position:sticky;top:0;z-index:100;}
.navbar-top{display:flex;align-items:center;padding:8px 12px 6px;
            border-bottom:1px solid var(--border);}
.navbar h1{font-size:1.05rem;color:var(--accent);font-weight:700;
           white-space:nowrap;margin:0;}
.scatter-nav-link{margin-left:auto;padding:4px 12px;
                  color:var(--accent);font-size:0.82rem;
                  text-decoration:none;white-space:nowrap;}
.scatter-nav-link:hover{text-decoration:underline;}
.navbar-tabs{display:flex;align-items:center;padding:0 8px;}
.nav-tab{background:none;border:none;color:var(--muted);font-size:0.85rem;
         padding:10px 16px;cursor:pointer;
         border-bottom:3px solid transparent;
         transition:color 0.15s;white-space:nowrap;}
.nav-tab:hover{color:var(--text);}
.nav-tab.active{color:var(--accent);border-bottom-color:var(--accent);}
/* ── Panels ── */
.panel{padding:18px 22px;}
.hidden{display:none!important;}
.sec-title{font-size:1.0rem;color:var(--accent);font-weight:600;
           border-bottom:1px solid var(--border);padding-bottom:5px;
           margin-bottom:4px;}
.sec-desc{color:var(--muted);font-size:0.78rem;margin-bottom:14px;}
/* ── Grids ── */
.grid-1{display:grid;grid-template-columns:1fr;gap:16px;}
.grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;}
.grid-auto{display:grid;
  grid-template-columns:repeat(auto-fill,minmax(480px,1fr));gap:14px;}
/* ── Scenario groups ── */
.scen-group{margin-bottom:24px;}
.scen-group-title{font-size:0.95rem;font-weight:700;color:var(--accent);
                  padding:6px 0;border-bottom:1px solid var(--border);
                  margin-bottom:10px;}
/* ── Cards ── */
.card{background:var(--surf);border:1px solid var(--border);
      border-radius:8px;overflow:hidden;}
.card:hover{border-color:var(--accent);}
.card-label{background:var(--card);border-bottom:1px solid var(--border);
            padding:5px 11px;font-size:0.74rem;color:var(--muted);}
.card-label strong{color:var(--text);}
.fig-img{width:100%;display:block;}
.missing{padding:20px;text-align:center;color:var(--muted);
         font-size:0.75rem;border:1px dashed var(--border);margin:6px;}
/* ── Scrollbar ── */
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px;}
"""

JS = """
function showTab(w){
  document.querySelectorAll('.panel').forEach(p=>p.classList.add('hidden'));
  document.querySelectorAll('.nav-tab').forEach(b=>b.classList.remove('active'));
  document.getElementById('p-'+w).classList.remove('hidden');
  document.querySelector('[data-tab="'+w+'"]').classList.add('active');
}
"""


# ── Builder ────────────────────────────────────────────────────────────────────
def build(linked=False):

    def _img(folder, fname):
        path = BASE_DIR / folder / fname
        rel  = f"{_REL_BASE}/{folder}/{fname}"
        return img(path, fname, rel if linked else None)

    def _dimg(sf, col):
        fname = f"diff_{sf}_{col}.png"
        path  = DIFF_DIR / sf / fname
        rel   = f"{_REL_DIFF}/{sf}/{fname}"
        return img(path, fname, rel if linked else None)

    def _hdimg(fname):
        path = DIFF_DIR / fname
        rel  = f"{_REL_DIFF}/{fname}"
        return img(path, fname, rel if linked else None)

    # Scatter link
    if linked:
        s_href = "seasonal_extremes_scatter.html" if SCATTER_ROOT.exists() else None
    else:
        s_href = str(SCATTER_SRC) if SCATTER_SRC.exists() else (
                 str(SCATTER_ROOT) if SCATTER_ROOT.exists() else None)
    scatter_link = (f'<a class="scatter-nav-link" href="{s_href}" target="_blank">'
                    f'&#x2197; Seasonal Extremes scatter</a>'
                    if s_href else '')

    # ── Forest diff tab ───────────────────────────────────────────────────────
    forest_html = ""
    for sf, slbl in FOREST_SCENARIOS:
        forest_html += f'<div class="scen-group"><div class="scen-group-title">{slbl}</div><div class="grid-auto">'
        for col, clbl in DIFF_FIELDS:
            forest_html += card(f"<strong>{clbl}</strong>", _dimg(sf, col))
        forest_html += "</div></div>\n"

    # ── Climate diff tab ──────────────────────────────────────────────────────
    climate_html = ""
    for sf, slbl in CLIMATE_SCENARIOS:
        climate_html += f'<div class="scen-group"><div class="scen-group-title">{slbl}</div><div class="grid-auto">'
        for col, clbl in DIFF_FIELDS:
            climate_html += card(f"<strong>{clbl}</strong>", _dimg(sf, col))
        climate_html += "</div></div>\n"

    # ── Baseline tab ──────────────────────────────────────────────────────────
    base_html = ""
    for fname, flbl in BASELINE_FIGS:
        base_html += card(f"<strong>{flbl}</strong>", _img("baseline", fname))

    # ── Hydrograph tab ────────────────────────────────────────────────────────
    hygro_html = ""
    for fname, hlbl in HYGRO_FIGS:
        hygro_html += card(f"<strong>{hlbl}</strong>", _hdimg(fname))

    mode = "Linked" if linked else "Standalone"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Newborough Warren — Scenario Viewer</title>
  <style>{CSS}</style>
</head>
<body>
<nav class="navbar">
  <div class="navbar-top">
    <h1>Newborough Warren — Groundwater Scenario Viewer</h1>
    {scatter_link}
  </div>
  <div class="navbar-tabs">
    <button class="nav-tab active" data-tab="forest"
            onclick="showTab('forest')">Forest Management</button>
    <button class="nav-tab" data-tab="climate"
            onclick="showTab('climate')">Climate Change</button>
    <button class="nav-tab" data-tab="baseline"
            onclick="showTab('baseline')">Baseline Maps</button>
    <button class="nav-tab" data-tab="hygro"
            onclick="showTab('hygro')">Seasonal Profiles</button>
  </div>
</nav>

<div id="p-forest" class="panel">
  <div class="sec-title">Forest Management — Difference Maps vs Baseline</div>
  <div class="sec-desc">
    Red = higher than baseline &nbsp;|&nbsp; Blue = lower than baseline.<br>
    Head (m AOD): red = wetter, blue = drier. &nbsp;
    Depth below ground: red = shallower (wetter), blue = deeper (drier).<br>
    Maps auto-scaled from p5–p95 of actual well Δ values.
    Maps omitted where |Δ| &lt; threshold (no meaningful change).
    Source: Hollingham (2026).
  </div>
  <div class="grid-1">{forest_html}</div>
</div>

<div id="p-climate" class="panel hidden">
  <div class="sec-title">Climate Change — Difference Maps vs Baseline</div>
  <div class="sec-desc">
    Climate dry: ΔP = −89 mm/yr, ΔPET = +54 mm/yr. &nbsp;
    Climate wet: ΔP = +89 mm/yr, ΔPET = −27 mm/yr.<br>
    Red = higher than baseline &nbsp;|&nbsp; Blue = lower than baseline.<br>
    Head: red = wetter, blue = drier. Site-wide mean Δh: dry −0.23 m, wet +0.16 m.
    Source: Hollingham (2026).
  </div>
  <div class="grid-1">{climate_html}</div>
</div>

<div id="p-baseline" class="panel hidden">
  <div class="sec-title">Baseline Maps — 2005–2026 Observed Mean</div>
  <div class="sec-desc">
    Spatial distribution of hydrogeological variables under baseline conditions.
    K = 6.0 m/day (Connell 2003). C4 canopy interception 24% (Freeman 2008).
  </div>
  <div class="grid-2">{base_html}</div>
</div>

<div id="p-hygro" class="panel hidden">
  <div class="sec-title">Seasonal Water Table Profiles</div>
  <div class="sec-desc">
    Mean monthly depth below ground (m) per cluster. Y-axis inverted:
    0 = surface at top, 2 m at bottom. Summer dips downward.
    Thresholds: Curreli et al. (2013). Hollingham (2026).
  </div>
  <div class="grid-1">{hygro_html}</div>
</div>

<script>{JS}</script>
</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    # Standalone
    html = build(linked=False)
    out  = BASE_DIR / "scenario_viewer.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Standalone: {out}  ({out.stat().st_size/1e6:.1f} MB)")

    # Linked
    html = build(linked=True)
    out  = ROOT_DIR / "scenario_viewer.html"
    out.write_text(html, encoding="utf-8")
    print(f"  Linked:     {out}  ({out.stat().st_size/1e3:.0f} KB)")

    # Copy scatter to root
    if SCATTER_SRC.exists():
        shutil.copy2(SCATTER_SRC, SCATTER_ROOT)
        print(f"  Scatter:    {SCATTER_ROOT}")


if __name__ == "__main__":
    main()
