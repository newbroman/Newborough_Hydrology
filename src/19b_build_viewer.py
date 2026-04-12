"""
19b_build_viewer.py
===================
Generates a self-contained HTML scenario viewer for script 19 outputs.
All images are embedded as base64 so the file opens directly in any
browser with no server needed.

Usage
-----
  python 19b_build_viewer.py

Output
------
  outputs/19_spatial_groundwater/scenario_viewer.html

Open the HTML file in any browser. No internet connection required.
"""

import base64
import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.paths import OUT_DIR, OUT_14_SEASONAL_SCATTER

BASE_DIR    = OUT_DIR / "19_spatial_groundwater"
OUT_HTML    = BASE_DIR / "scenario_viewer.html"
SCATTER_HTML = OUT_14_SEASONAL_SCATTER

# ── Scenario definitions (must match 19a_scenario_runner.py) ─────────────────
SCENARIOS = [
    ("baseline",        "Baseline",             "2005–2026 observed mean"),
    ("forest_removal",  "Full clearfell",        "β₂ ×1.15, interception removed"),
    ("forest_thinning", "Forest thinning 50%",   "Partial removal effect"),
    ("species_change",  "Broadleaf conversion",  "β₁ ×0.90 in autumn"),
    ("climate_dry",     "Climate — dry",         "ΔP −10%, ΔPET +10%"),
    ("climate_wet",     "Climate — wet",         "ΔP +10%, ΔPET −5%"),
]

# ── Figure definitions ────────────────────────────────────────────────────────
# (filename, display_label, scenario_sensitive)
FIGURES = [
    ("19_head_surface_mean.png",    "Mean head + Darcy flux",        True),
    ("19_head_surface_seasonal.png","Seasonal head (winter/summer)", True),
    ("19_lateral_flux.png",         "Darcy lateral flux",            True),
    ("19_water_balance.png",        "Water balance components",      True),
    ("19_winter_flooding.png",      "Winter flooding",               True),
    ("19_depth_to_watertable.png",  "Depth to water table",         True),
    ("19_storage_change.png",       "Seasonal storage change",       True),
    ("19_beta_fields.png",          "β coefficient fields",          False),
    ("19_aquifer_thickness.png",    "Aquifer thickness",             False),
    ("19_residual_comparison.png",  "Residual comparison",          False),
]

DIFF_FIGURES = [
    ("diff_forest_removal.png",  "Full clearfell vs baseline"),
    ("diff_forest_thinning.png", "Forest thinning vs baseline"),
    ("diff_species_change.png",  "Broadleaf conversion vs baseline"),
    ("diff_climate_dry.png",     "Climate dry vs baseline"),
    ("diff_climate_wet.png",     "Climate wet vs baseline"),
    ("scenario_summary.png",     "All scenarios — summary"),
    ("cluster_hydrographs.png",  "Cluster seasonal hydrographs"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def img_to_b64(path):
    """Return base64-encoded PNG string, or None if file missing."""
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def load_scatter_srcdoc(path):
    """
    Read the seasonal extremes scatter HTML and return it as a string suitable
    for use in an iframe srcdoc attribute (double-quotes escaped).
    Returns None if the file does not exist.
    """
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    # srcdoc requires double-quotes to be HTML-entity escaped
    return raw.replace('"', "&quot;")


def img_tag(b64, alt="", cls=""):
    """Build an <img> tag from a base64 string."""
    if b64 is None:
        return f'<div class="missing">Image not found:<br>{alt}</div>'
    return (f'<img src="data:image/png;base64,{b64}" '
            f'alt="{alt}" class="{cls}" '
            f'onclick="zoom(this)" />')


# ── Build HTML ────────────────────────────────────────────────────────────────

def build_html():
    print(f"Building scenario viewer...")
    print(f"  Base directory: {BASE_DIR}")

    # ── Load seasonal scatter HTML (from script 14) ───────────────────────────
    scatter_srcdoc = load_scatter_srcdoc(SCATTER_HTML)
    if scatter_srcdoc:
        print(f"  Seasonal scatter: found ({SCATTER_HTML.name})")
    else:
        print(f"  Seasonal scatter: NOT FOUND — tab will show placeholder")
        print(f"    Expected at: {SCATTER_HTML}")

    # ── Pre-load all images ───────────────────────────────────────────────────
    # Scenario figures
    scen_imgs = {}   # {(subfolder, filename): b64}
    for subfolder, label, desc in SCENARIOS:
        scenario_dir = BASE_DIR / subfolder
        for fname, flabel, sensitive in FIGURES:
            if not sensitive and subfolder != "baseline":
                continue   # static figures only from baseline
            b64 = img_to_b64(scenario_dir / fname)
            scen_imgs[(subfolder, fname)] = b64

    # Difference maps
    diff_imgs = {}
    for fname, label in DIFF_FIGURES:
        diff_imgs[fname] = img_to_b64(BASE_DIR / "difference_maps" / fname)

    # ── Build figure tab panels ───────────────────────────────────────────────
    fig_tabs_nav = ""
    fig_tabs_content = ""

    for i, (fname, flabel, sensitive) in enumerate(FIGURES):
        tab_id = f"fig_{i}"
        active = "active" if i == 0 else ""
        fig_tabs_nav += (f'<button class="tab-btn {active}" '
                         f'onclick="showTab(\'{tab_id}\')">'
                         f'{flabel}</button>\n')

        panels_html = ""
        if sensitive:
            # All scenarios
            for subfolder, slabel, sdesc in SCENARIOS:
                b64 = scen_imgs.get((subfolder, fname))
                found = "✓" if b64 else "✗ missing"
                panels_html += f'''
                <div class="scenario-panel">
                  <div class="scenario-label">
                    <span class="scen-name">{slabel}</span>
                    <span class="scen-desc">{sdesc}</span>
                  </div>
                  {img_tag(b64, f"{slabel} — {flabel}", "scenario-img")}
                </div>'''
        else:
            # Baseline only
            b64 = scen_imgs.get(("baseline", fname))
            panels_html += f'''
            <div class="scenario-panel wide">
              <div class="scenario-label">
                <span class="scen-name">Baseline (all scenarios identical)</span>
              </div>
              {img_tag(b64, f"Baseline — {flabel}", "scenario-img")}
            </div>'''

        fig_tabs_content += f'''
        <div id="{tab_id}" class="tab-panel {"" if i == 0 else "hidden"}">
          <h2>{flabel}</h2>
          <div class="scenarios-grid {"single" if not sensitive else ""}">
            {panels_html}
          </div>
        </div>'''

    # ── Difference maps panel ─────────────────────────────────────────────────
    diff_html = ""
    for fname, dlabel in DIFF_FIGURES:
        b64 = diff_imgs.get(fname)
        diff_html += f'''
        <div class="scenario-panel">
          <div class="scenario-label">
            <span class="scen-name">{dlabel}</span>
          </div>
          {img_tag(b64, dlabel, "scenario-img")}
        </div>'''

    # ── Count available images ────────────────────────────────────────────────
    n_found   = sum(1 for v in scen_imgs.values() if v is not None)
    n_total   = len(scen_imgs)
    n_diff    = sum(1 for v in diff_imgs.values() if v is not None)
    n_diff_t  = len(diff_imgs)

    print(f"  Scenario figures: {n_found}/{n_total} found")
    print(f"  Difference maps:  {n_diff}/{n_diff_t} found")

    # ── Seasonal scatter panel ────────────────────────────────────────────────
    if scatter_srcdoc:
        scatter_panel = f'<div class="scatter-wrap"><iframe srcdoc="{scatter_srcdoc}" title="Seasonal extremes scatter plot"></iframe></div>'
    else:
        scatter_panel = (
            '<div class="scatter-missing">'
            'Seasonal extremes scatter plot not found.<br>'
            'Run script 14 first to generate this figure.'
            '<code>outputs/14_climate_projections/14_seasonal_extremes_scatter.html</code>'
            '</div>'
        )

    # ── Assemble full HTML ────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Newborough Warren — Scenario Viewer</title>
<style>
  :root {{
    --bg: #1a1a2e;
    --surface: #16213e;
    --card: #0f3460;
    --accent: #e94560;
    --text: #eaeaea;
    --muted: #8892b0;
    --border: #334;
    --green: #64ffda;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Segoe UI", system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }}

  /* ── Header ── */
  header {{
    background: var(--surface);
    border-bottom: 2px solid var(--accent);
    padding: 16px 24px;
    display: flex;
    align-items: baseline;
    gap: 16px;
  }}
  header h1 {{ font-size: 1.3rem; color: var(--green); }}
  header p  {{ font-size: 0.8rem; color: var(--muted); }}
  .badge {{
    margin-left: auto;
    font-size: 0.72rem;
    color: var(--muted);
    background: var(--card);
    padding: 4px 10px;
    border-radius: 12px;
  }}

  /* ── Main tabs (Scenarios / Difference Maps) ── */
  .main-nav {{
    display: flex;
    gap: 4px;
    padding: 12px 24px 0;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }}
  .main-tab {{
    padding: 8px 20px;
    border: none;
    background: transparent;
    color: var(--muted);
    font-size: 0.9rem;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
  }}
  .main-tab.active {{
    color: var(--green);
    border-bottom-color: var(--green);
  }}
  .main-tab:hover {{ color: var(--text); }}

  /* ── Figure type tabs ── */
  .fig-nav {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    padding: 12px 24px;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  .tab-btn {{
    padding: 5px 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--card);
    color: var(--muted);
    font-size: 0.78rem;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .tab-btn.active {{
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }}
  .tab-btn:hover {{ color: var(--text); }}

  /* ── Content area ── */
  .content {{ padding: 20px 24px; }}
  h2 {{
    font-size: 1rem;
    color: var(--green);
    margin-bottom: 16px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }}

  /* ── Scenarios grid ── */
  .scenarios-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
    gap: 16px;
  }}
  .scenarios-grid.single {{
    grid-template-columns: 1fr;
    max-width: 900px;
  }}
  .scenario-panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    transition: box-shadow 0.2s;
  }}
  .scenario-panel:hover {{
    box-shadow: 0 4px 20px rgba(100,255,218,0.15);
  }}
  .scenario-panel.wide {{ grid-column: 1 / -1; }}
  .scenario-label {{
    padding: 8px 14px;
    background: var(--card);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: baseline;
    gap: 10px;
  }}
  .scen-name {{
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--green);
  }}
  .scen-desc {{
    font-size: 0.72rem;
    color: var(--muted);
  }}
  .scenario-img {{
    width: 100%;
    height: auto;
    display: block;
    cursor: zoom-in;
  }}
  .missing {{
    padding: 40px;
    text-align: center;
    color: var(--muted);
    font-size: 0.8rem;
    background: var(--card);
    min-height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  /* ── Hidden ── */
  .hidden {{ display: none !important; }}

  /* ── Lightbox ── */
  #lightbox {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.92);
    z-index: 1000;
    cursor: zoom-out;
    align-items: center;
    justify-content: center;
  }}
  #lightbox.show {{ display: flex; }}
  #lightbox img {{
    max-width: 96vw;
    max-height: 96vh;
    object-fit: contain;
    border: 2px solid var(--green);
    border-radius: 4px;
  }}
  #lightbox-close {{
    position: absolute;
    top: 16px; right: 20px;
    font-size: 2rem;
    color: var(--green);
    cursor: pointer;
    background: none;
    border: none;
    line-height: 1;
  }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

  /* ── Seasonal scatter iframe ── */
  .scatter-wrap {{
    background: white;
    border-radius: 8px;
    overflow: hidden;
    padding: 0;
  }}
  .scatter-wrap iframe {{
    width: 100%;
    height: 620px;
    border: none;
    display: block;
  }}
  .scatter-missing {{
    padding: 60px 40px;
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 8px;
  }}
  .scatter-missing code {{
    display: block;
    margin-top: 10px;
    font-size: 0.75rem;
    color: var(--accent);
  }}
</style>
</head>
<body>

<header>
  <h1>Newborough Warren — Groundwater Scenario Viewer</h1>
  <p>Hydrogeological Dynamics, Behavioural Clustering and Management
     Intervention Analysis &nbsp;|&nbsp; Hollingham (2026)</p>
  <span class="badge">{n_found}/{n_total} scenario figures &nbsp;·&nbsp;
    {n_diff}/{n_diff_t} difference maps</span>
</header>

<!-- Main tab nav -->
<nav class="main-nav">
  <button class="main-tab active" onclick="showMain('scenarios')">
    Scenario Figures
  </button>
  <button class="main-tab" onclick="showMain('diffs')">
    Difference Maps
  </button>
  <button class="main-tab" onclick="showMain('scatter')">
    Seasonal Extremes
  </button>
</nav>

<!-- Scenarios section -->
<div id="main-scenarios">
  <div class="fig-nav">
    {fig_tabs_nav}
  </div>
  <div class="content">
    {fig_tabs_content}
  </div>
</div>

<!-- Difference maps section -->
<div id="main-diffs" class="hidden">
  <div class="content">
    <h2>Difference Maps — Scenario vs Baseline</h2>
    <p style="font-size:0.8rem;color:var(--muted);margin-bottom:16px">
      Blue = wetter than baseline &nbsp;|&nbsp; Red = drier than baseline
    </p>
    <div class="scenarios-grid">
      {diff_html}
    </div>
  </div>
</div>

<!-- Seasonal extremes scatter section -->
<div id="main-scatter" class="hidden">
  <div class="content">
    <h2>Seasonal Extremes — Well Network vs Ecological Thresholds</h2>
    <p style="font-size:0.8rem;color:var(--muted);margin-bottom:16px">
      Mean annual summer minimum vs winter maximum water table depth per well,
      coloured by hydrogeological cluster. Dashed lines: Curreli et al. (2013)
      eco-hydrological thresholds. Hover over points for well values; use the
      search box to locate a specific well.
    </p>
    {scatter_panel}
  </div>
</div>

<!-- Lightbox -->
<div id="lightbox" onclick="closeLightbox()">
  <button id="lightbox-close" onclick="closeLightbox()">✕</button>
  <img id="lightbox-img" src="" alt="">
</div>

<script>
  // ── Tab switching ──────────────────────────────────────────────────────────
  function showTab(id) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.remove('hidden');
    event.currentTarget.classList.add('active');
  }}

  function showMain(which) {{
    ['scenarios', 'diffs', 'scatter'].forEach(id => {{
      document.getElementById('main-' + id).classList.toggle('hidden', id !== which);
    }});
    document.querySelectorAll('.main-tab').forEach(b => b.classList.remove('active'));
    event.currentTarget.classList.add('active');
  }}

  // ── Lightbox ───────────────────────────────────────────────────────────────
  function zoom(img) {{
    document.getElementById('lightbox-img').src = img.src;
    document.getElementById('lightbox').classList.add('show');
  }}
  function closeLightbox() {{
    document.getElementById('lightbox').classList.remove('show');
  }}
  document.addEventListener('keydown', e => {{
    if (e.key === 'Escape') closeLightbox();
  }});
</script>
</body>
</html>"""

    return html


def main():
    html = build_html()
    OUT_HTML.write_text(html, encoding="utf-8")
    size_mb = OUT_HTML.stat().st_size / 1_048_576
    print(f"\nViewer written to: {OUT_HTML}")
    print(f"File size: {size_mb:.1f} MB")
    print(f"Open in any browser — no server needed.")


if __name__ == "__main__":
    main()
