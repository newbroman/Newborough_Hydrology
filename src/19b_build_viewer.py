"""
19b_build_viewer.py
===================
Generates two HTML scenario viewers for script 19 outputs.

Outputs
-------
  outputs/19_spatial_groundwater/scenario_viewer.html
      Standalone self-contained file — all images base64-embedded.
      Open directly in any browser with no server needed.
      Suitable for sharing with reviewers or archiving alongside the paper.

  scenario_viewer.html  (repository root)
      Lightweight linked version — images referenced by relative path.
      Designed for GitHub Pages deployment; requires the repository
      structure to be intact. Small file size (~50 KB).

Usage
-----
  python 19b_build_viewer.py

The linked version is also produced by run_analysis.py --viewer.
"""

import base64
import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.paths import OUT_DIR, OUT_14_SEASONAL_SCATTER

ROOT_DIR     = SRC_DIR.parent
BASE_DIR     = OUT_DIR / "19_spatial_groundwater"
OUT_STANDALONE = BASE_DIR / "scenario_viewer.html"
OUT_LINKED     = ROOT_DIR / "scenario_viewer.html"
SCATTER_HTML   = OUT_14_SEASONAL_SCATTER

# Relative path from repository root to the 19_spatial_groundwater folder
# Used by the linked viewer to reference images
_REL_BASE = "outputs/19_spatial_groundwater"
_REL_DIFF = "outputs/19_spatial_groundwater/difference_maps"

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
    """Read scatter HTML and return escaped for use in iframe srcdoc."""
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    return raw.replace('"', "&quot;")


def img_tag_b64(b64, alt="", cls=""):
    """Build an <img> tag from a base64 string."""
    if b64 is None:
        return f'<div class="missing">Image not found:<br>{alt}</div>'
    return (f'<img src="data:image/png;base64,{b64}" '
            f'alt="{alt}" class="{cls}" '
            f'onclick="zoom(this)" />')


def img_tag_linked(rel_path, exists, alt="", cls=""):
    """Build an <img> tag using a relative file path."""
    if not exists:
        return f'<div class="missing">Image not found:<br>{alt}</div>'
    return (f'<img src="{rel_path}" '
            f'alt="{alt}" class="{cls}" '
            f'onclick="zoom(this)" />')


# ── CSS (shared between both modes) ──────────────────────────────────────────

CSS = """
  :root {
    --bg: #1a1a2e;
    --surface: #16213e;
    --card: #0f3460;
    --accent: #e94560;
    --text: #eaeaea;
    --muted: #8892b0;
    --border: #334;
    --green: #64ffda;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Segoe UI", system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    background: var(--surface);
    border-bottom: 2px solid var(--accent);
    padding: 16px 24px;
    display: flex;
    align-items: baseline;
    gap: 16px;
  }
  header h1 { font-size: 1.3rem; color: var(--green); }
  header p  { font-size: 0.8rem; color: var(--muted); }
  .badge {
    margin-left: auto;
    font-size: 0.72rem;
    color: var(--muted);
    background: var(--card);
    padding: 4px 10px;
    border-radius: 12px;
  }

  /* ── Main tabs ── */
  .main-nav {
    display: flex;
    gap: 4px;
    padding: 12px 24px 0;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }
  .main-tab {
    padding: 8px 18px;
    background: var(--card);
    border: 1px solid var(--border);
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    color: var(--muted);
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .main-tab.active {
    background: var(--bg);
    color: var(--green);
    border-color: var(--accent);
  }

  /* ── Figure sub-tabs ── */
  .fig-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 12px 24px;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
  }
  .tab-btn {
    padding: 5px 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--muted);
    font-size: 0.78rem;
    cursor: pointer;
    transition: all 0.15s;
  }
  .tab-btn.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }
  .tab-btn:hover { color: var(--text); }

  /* ── Content ── */
  .content { padding: 20px 24px; }
  h2 {
    font-size: 1rem;
    color: var(--green);
    margin-bottom: 16px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }

  /* ── Scenarios grid ── */
  .scenarios-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
    gap: 16px;
  }
  .scenarios-grid.single {
    grid-template-columns: 1fr;
    max-width: 900px;
  }
  .scenario-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    transition: box-shadow 0.2s;
  }
  .scenario-panel:hover {
    box-shadow: 0 4px 20px rgba(100,255,218,0.15);
  }
  .scenario-panel.wide { grid-column: 1 / -1; }
  .scenario-label {
    padding: 8px 14px;
    background: var(--card);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: baseline;
    gap: 10px;
  }
  .scen-name { font-size: 0.85rem; font-weight: 600; color: var(--green); }
  .scen-desc { font-size: 0.72rem; color: var(--muted); }
  .scenario-img { width: 100%; height: auto; display: block; cursor: zoom-in; }
  .missing {
    padding: 40px;
    text-align: center;
    color: var(--muted);
    font-size: 0.8rem;
    background: var(--card);
    min-height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .hidden { display: none !important; }

  /* ── Lightbox ── */
  #lightbox {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.92);
    z-index: 1000;
    cursor: zoom-out;
    align-items: center;
    justify-content: center;
  }
  #lightbox.show { display: flex; }
  #lightbox img {
    max-width: 96vw;
    max-height: 96vh;
    object-fit: contain;
    border: 2px solid var(--green);
    border-radius: 4px;
  }
  #lightbox-close {
    position: absolute;
    top: 16px; right: 20px;
    font-size: 2rem;
    color: var(--green);
    cursor: pointer;
    background: none;
    border: none;
    line-height: 1;
  }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

  /* ── Scatter ── */
  .scatter-wrap {
    background: white;
    border-radius: 8px;
    overflow: hidden;
  }
  .scatter-wrap iframe {
    width: 100%;
    height: 620px;
    border: none;
    display: block;
  }
  .scatter-missing {
    padding: 60px 40px;
    text-align: center;
    color: var(--muted);
    font-size: 0.85rem;
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 8px;
  }
  .scatter-missing code {
    display: block;
    margin-top: 10px;
    font-size: 0.75rem;
    color: var(--accent);
  }
"""

JS = """
  function showTab(id) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.remove('hidden');
    event.currentTarget.classList.add('active');
  }
  function showMain(which) {
    ['scenarios', 'diffs', 'scatter'].forEach(id => {
      document.getElementById('main-' + id).classList.toggle('hidden', id !== which);
    });
    document.querySelectorAll('.main-tab').forEach(b => b.classList.remove('active'));
    event.currentTarget.classList.add('active');
  }
  function zoom(img) {
    document.getElementById('lightbox-img').src = img.src;
    document.getElementById('lightbox').classList.add('show');
  }
  function closeLightbox() {
    document.getElementById('lightbox').classList.remove('show');
  }
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeLightbox();
  });
"""


# ── HTML builder ──────────────────────────────────────────────────────────────

def build_html(mode="standalone"):
    """
    Build the viewer HTML.

    mode: "standalone" — embed all images as base64 (large, self-contained)
          "linked"     — reference images by relative path (small, needs repo)
    """
    assert mode in ("standalone", "linked")
    linked = (mode == "linked")

    # ── Scatter panel ─────────────────────────────────────────────────────────
    if linked:
        # Link to the scatter HTML at root level
        scatter_src = ROOT_DIR / "seasonal_extremes_scatter.html"
        if scatter_src.exists():
            scatter_panel = '<div class="scatter-wrap"><iframe src="seasonal_extremes_scatter.html" title="Seasonal extremes scatter plot"></iframe></div>'
        else:
            scatter_panel = '<div class="scatter-missing">Seasonal extremes scatter plot not found.<br><code>seasonal_extremes_scatter.html</code></div>'
    else:
        srcdoc = load_scatter_srcdoc(SCATTER_HTML)
        if srcdoc:
            scatter_panel = f'<div class="scatter-wrap"><iframe srcdoc="{srcdoc}" title="Seasonal extremes scatter plot"></iframe></div>'
        else:
            scatter_panel = '<div class="scatter-missing">Seasonal extremes scatter plot not found.<br>Run script 14 first.<br><code>outputs/14_climate_projections/14_seasonal_extremes_scatter.html</code></div>'

    # ── Scenario figures ──────────────────────────────────────────────────────
    fig_tabs_nav = ""
    fig_tabs_content = ""
    n_found = n_total = 0

    for i, (fname, flabel, sensitive) in enumerate(FIGURES):
        tab_id = f"fig_{i}"
        active = "active" if i == 0 else ""
        fig_tabs_nav += (f'<button class="tab-btn {active}" '
                         f'onclick="showTab(\'{tab_id}\')">'
                         f'{flabel}</button>\n')

        panels_html = ""
        scenarios_to_show = SCENARIOS if sensitive else [SCENARIOS[0]]

        for subfolder, slabel, sdesc in scenarios_to_show:
            img_path = BASE_DIR / subfolder / fname
            if linked:
                rel = f"{_REL_BASE}/{subfolder}/{fname}"
                tag = img_tag_linked(rel, img_path.exists(), f"{slabel} — {flabel}", "scenario-img")
            else:
                b64 = img_to_b64(img_path)
                tag = img_tag_b64(b64, f"{slabel} — {flabel}", "scenario-img")
                n_total += 1
                if b64: n_found += 1

            extra = "" if sensitive else " wide"
            label_html = f'<span class="scen-name">{slabel}</span>'
            if sensitive:
                label_html += f'<span class="scen-desc">{sdesc}</span>'
            else:
                label_html += '<span class="scen-desc">Baseline (all scenarios identical)</span>'

            panels_html += f'''
            <div class="scenario-panel{extra}">
              <div class="scenario-label">{label_html}</div>
              {tag}
            </div>'''

        grid_cls = "scenarios-grid" if sensitive else "scenarios-grid single"
        fig_tabs_content += f'''
        <div id="{tab_id}" class="tab-panel {"" if i == 0 else "hidden"}">
          <h2>{flabel}</h2>
          <div class="{grid_cls}">{panels_html}</div>
        </div>'''

    # ── Difference maps ───────────────────────────────────────────────────────
    diff_html = ""
    n_diff = n_diff_t = 0

    for fname, dlabel in DIFF_FIGURES:
        img_path = BASE_DIR / "difference_maps" / fname
        if linked:
            rel = f"{_REL_DIFF}/{fname}"
            tag = img_tag_linked(rel, img_path.exists(), dlabel, "scenario-img")
        else:
            b64 = img_to_b64(img_path)
            tag = img_tag_b64(b64, dlabel, "scenario-img")
            n_diff_t += 1
            if b64: n_diff += 1

        diff_html += f'''
        <div class="scenario-panel">
          <div class="scenario-label"><span class="scen-name">{dlabel}</span></div>
          {tag}
        </div>'''

    # For linked mode, count from filesystem
    if linked:
        n_found  = sum(1 for s, _, _ in SCENARIOS for f, _, sens in FIGURES
                       if (BASE_DIR / s / f).exists() and (sens or s == "baseline"))
        n_total  = sum(1 for s, _, _ in SCENARIOS for f, _, sens in FIGURES
                       if sens or s == "baseline")
        n_diff   = sum(1 for f, _ in DIFF_FIGURES if (BASE_DIR / "difference_maps" / f).exists())
        n_diff_t = len(DIFF_FIGURES)

    mode_label = "Standalone" if not linked else "GitHub Pages"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Newborough Warren — Scenario Viewer</title>
<style>{CSS}</style>
</head>
<body>

<header>
  <h1>Newborough Warren — Groundwater Scenario Viewer</h1>
  <p>Hydrogeological Dynamics, Behavioural Clustering and Management
     Intervention Analysis &nbsp;|&nbsp; Hollingham (2026)</p>
  <span class="badge">{n_found}/{n_total} scenario figures &nbsp;·&nbsp;
    {n_diff}/{n_diff_t} difference maps &nbsp;·&nbsp; {mode_label}</span>
</header>

<nav class="main-nav">
  <button class="main-tab active" onclick="showMain('scenarios')">Scenario Figures</button>
  <button class="main-tab" onclick="showMain('diffs')">Difference Maps</button>
  <button class="main-tab" onclick="showMain('scatter')">Seasonal Extremes</button>
</nav>

<div id="main-scenarios">
  <div class="fig-nav">{fig_tabs_nav}</div>
  <div class="content">{fig_tabs_content}</div>
</div>

<div id="main-diffs" class="hidden">
  <div class="content">
    <h2>Difference Maps — Scenario vs Baseline</h2>
    <p style="font-size:0.8rem;color:var(--muted);margin-bottom:16px">
      Blue = wetter than baseline &nbsp;|&nbsp; Red = drier than baseline
    </p>
    <div class="scenarios-grid">{diff_html}</div>
  </div>
</div>

<div id="main-scatter" class="hidden">
  <div class="content">
    <h2>Seasonal Extremes — Well Network vs Ecological Thresholds</h2>
    <p style="font-size:0.8rem;color:var(--muted);margin-bottom:16px">
      Mean annual summer minimum vs winter maximum water table depth per well,
      coloured by hydrogeological cluster. Dashed lines: Curreli et al. (2013)
      eco-hydrological thresholds.
    </p>
    {scatter_panel}
  </div>
</div>

<div id="lightbox" onclick="closeLightbox()">
  <button id="lightbox-close" onclick="closeLightbox()">✕</button>
  <img id="lightbox-img" src="" alt="">
</div>

<script>{JS}</script>
</body>
</html>"""

    return html


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Standalone version — self-contained, large file
    print("Building standalone viewer (base64-embedded images)...")
    html_standalone = build_html(mode="standalone")
    OUT_STANDALONE.write_text(html_standalone, encoding="utf-8")
    size_mb = OUT_STANDALONE.stat().st_size / 1_048_576
    print(f"  Written: {OUT_STANDALONE}")
    print(f"  Size:    {size_mb:.1f} MB")

    # Linked version — lightweight, for GitHub Pages
    print("\nBuilding linked viewer (relative image paths)...")
    html_linked = build_html(mode="linked")
    OUT_LINKED.write_text(html_linked, encoding="utf-8")
    size_kb = OUT_LINKED.stat().st_size / 1024
    print(f"  Written: {OUT_LINKED}")
    print(f"  Size:    {size_kb:.0f} KB")

    print("\nDone.")
    print(f"  Standalone: open {OUT_STANDALONE} directly in any browser")
    print(f"  GitHub Pages: commit {OUT_LINKED.name} to repository root")


if __name__ == "__main__":
    main()
