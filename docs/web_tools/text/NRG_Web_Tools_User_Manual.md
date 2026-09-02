<!-- GENERATED MIRROR of docs/web_tools/NRG_Web_Tools_User_Manual.odt — do not edit.
     Regenerate with: python3 tools/refresh_mirrors.py -->

2

Newborough Warren

Interactive Web Tools

User Manual

Forecaster · Scenario Viewer · Seasonal Extremes Scatter

Hollingham (2026)

May 2026

Part A

Groundwater Flooding Forecaster

# A1. Introduction

Document version --- updated 2026-08-12.

The Groundwater Flooding Forecaster is a self-contained, single-file HTML tool that provides per-well flood-risk assessments for the Newborough Warren dipwell network. It is designed to be opened in any modern web browser, on desktop or mobile, with no installation required.

The forecaster presents the report's cluster-block transfer functions (Tables 6, 7, and 10) directly, with coefficients substituted inline so the user can audit each calculation. It answers three linked questions for any selected dipwell:

1.  What winter peak water level is expected, given the current summer minimum and a chosen rainfall scenario? (Table 6)
2.  What summer minimum follows from the cluster-mean winter peak? (Table 7)
3.  How much cumulative rainfall is needed to bring groundwater to the slack floor --- P_flood? (Table 10)

# A2. Opening the Forecaster

Open forecaster.html in a web browser. The page loads instantly because all well data, map geometry, and model coefficients are bundled into the file. No server or internet connection is required for the core functionality.

On first load the tool will attempt to fetch live rainfall data from the Met Office (see Section A5). This requires an internet connection but is optional; the tool falls back to climatological defaults if the fetch fails.

# A3. Interface Layout

The interface is arranged in three panels beneath a header bar and a live-data banner:

  -------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Panel          Purpose
  Left sidebar   Well selection (dropdown grouped by cluster), observed-depth input, and well details: coordinates, elevation, cluster assignment, per-well and cluster long-term depth tables.
  Centre map     Square SVG plan of Newborough Warren showing every dipwell as a colour-coded dot. A hillshade base layer and KML feature overlays provide spatial context. The rainfall-multiplier slider and map legend overlay the top corners.
  Right panel    Three forecast cards for the selected well with inline equations, value substitutions, ecological badges, and a method note. A "Forecasts as of \<Month\> \<Year\>" timestamp appears at the top.
  -------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

All three panels are separated by draggable 6 px gutters. Drag a gutter sideways to widen or narrow the adjacent panel; your preferred widths persist between visits (stored in the browser's localStorage). On narrow screens (\< 960 px) the panels stack vertically and the gutters are hidden.

# A4. Selecting a Well and Entering Depths

Wells can be selected in two ways:

-   Dropdown menu (left sidebar): wells are grouped by cluster (C1--C5) with descriptive labels and well counts. Wells marked with an asterisk (\*) are nearest-type assignments, meaning they sit outside the SSM operational domain and forecasts should be interpreted with caution.
-   Map click: click any dot on the centre map to select that well. The selected well is highlighted with a larger radius.

When a well is selected, two depth inputs in the sidebar are pre-populated from cluster defaults. Each input drives a different forecast:

  ------------------------ -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Input                    Purpose and default
  Current observed depth   Today's dipwell reading. Drives Forecast 3 (P_flood: rainfall needed to lift the water table from this depth to the slack floor). Default: cluster's long-term mean depth for the current calendar month.
  Summer minimum depth     The annual summer trough. Drives Forecast 1 (next winter peak). Default: cluster's long-term summer minimum. The hint explains three options: this year's observed value if known, last year's if available, or keep the long-term default for a "typical year" projection.
  ------------------------ -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Editing either input immediately recalculates the relevant forecast. Forecast 2 (following summer minimum) uses the cluster-mean winter peak and takes no user input.

## A4.1 Well details panel

Below the depth input, a well-details section shows the selected well's coordinates, ground elevation, and cluster assignment. Beneath this, two stacked depth tables appear:

-   Well long-term depths: the selected well's own monthly climatology (from 01_wells_clean.csv), showing this month's long-term mean, the summer minimum (labelled by the well's own trough month), and the winter peak (labelled by the well's own peak month). Omitted if the well lacks sufficient record length.
-   Cluster long-term depths: the cluster-average equivalents, using the cluster's trough and peak months.

This lets you compare the individual well's behaviour against its cluster average. Trough and peak months may differ between the well and cluster (e.g. a well may peak in February while its cluster peaks in March).

# A5. Live Met Office Data

On load, the forecaster fetches the Met Office Historic Station Data file for RAF Valley (valleydata.txt). If the fetch succeeds, a banner below the header shows:

-   Cumulative winter rainfall (Oct--Mar) for the current and/or most recently completed hydrological winter.
-   The observed rainfall expressed as m_P, the ratio of observed to climatological winter total.

Two preset links appear above the slider allowing you to set the rainfall multiplier to the live m_P or to the climatological default (m_P = 1.00).

## A5.1 Manual fallback

If the live fetch fails (CORS restriction, no internet, server down), a Retry button and an Enter rainfall manually button appear. The manual option opens a modal where you can paste the full contents of valleydata.txt copied from a browser tab. The parser extracts the same monthly totals and populates the banner identically.

# A6. The Rainfall Multiplier (m_P)

The slider at the top-right of the map controls the assumed winter rainfall multiplier m_P, ranging from 0.60× (dry winter) to 2.00× (exceptional winter). As you drag it:

-   The map dots re-colour in real time to reflect updated P_flood vulnerability.
-   The forecast panel recalculates all three forecasts.
-   A descriptive label updates: Dry winter, Climatological, Wet winter, Very wet winter, or Exceptional winter.
-   

# A7. Understanding the Forecasts

The right panel displays three forecast cards. Each card shows the general form of the equation (from the report table), then the same equation with values substituted and the result evaluated. A coloured ecological badge and explanatory text accompany each result.

## A7.1 Forecast 1 --- Next winter peak (Table 6)

Uses the block transfer function to predict winter peak depth from the entered summer minimum and assumed winter rainfall. The equation is displayed inline:

h_peak = a_P · P_winter + a_h · h_min + intercept

An amber timing note appears if the current date is before the cluster's trough month (i.e. this year's summer minimum has not yet been observed). The note explains three options: wait for the observation, enter last summer's known value, or keep the long-term cluster mean as a "typical year" projection.

Ecological badge thresholds:

-   SD15b met (green): peak reaches within 0.10 m of the surface.
-   SD16 only (amber): peak reaches 0.10--0.25 m below ground.
-   Below SD16 (red): peak remains deeper than 0.25 m.

## A7.2 Forecast 2 --- Following summer minimum (Table 7)

Projects the deepest summer water-table depth from the cluster-mean winter peak and climatological summer rainfall (Apr--Sep). The equation is displayed inline:

h_min = a_P · P_summer + a_h · h_max(winter) + intercept

Ecological badge thresholds:

-   SD15b viable (green): minimum ≤0.61 m below ground.
-   SD16 only (amber): 0.61--0.98 m.
-   Below SD16 (red): deeper than 0.98 m.

## A7.3 Forecast 3 --- P_flood to slack floor (Table 10)

Calculates the cumulative rainfall (in mm) over the cluster's horizon period needed to bring groundwater from its current depth to the slack floor (0 m). The equation is displayed inline:

P_flood = A · d + B

The result is also expressed as m_P, the multiple of climatological rainfall:

-   Reachable (green): m_P \< 1.0 --- surface flooding possible under normal rainfall.
-   Wet winter required (amber): m_P 1.0--1.3.
-   Exceptional winter (red): m_P 1.3--2.0.
-   Structurally unreachable (grey): m_P \> 2.0 --- flooding essentially impossible.

## A7.4 Ecohydrology indices (EWI, EbF, MSL5)

Below the three forecasts, the well panel shows up to three ecohydrology indices. Unlike the forecasts, which answer a specific question about a coming season, these describe the well\'s overall wetness state:

Equilibrium Wetness Index (EWI) --- a model-derived index of the well\'s typical equilibrium wetness, expressed as an equilibrium water-table position in metres below ground (a higher, shallower value means a wetter well). Because it comes from the site model rather than a single reading, it is available even where the measured record is short. It is most meaningful on the open dune.

Ellenberg-F (EbF) --- a projected vegetation-moisture value, labelled measured, projected or extrapolated to show how directly it is supported by data.

Five-year mean spring level (MSL5) --- the most recent five-year mean spring water level for the well, shown with the date it is current to (as of a given round) when a live feed is available.

These values update automatically from the project\'s live feed. If the page is offline or opened as a standalone file they fall back to the long-term climatology and the as-of label is omitted; some extended-network wells with short records will not show these rows.

# A8. Reading the Map

The map uses a square viewBox (1000 × 1000) matching the square base-layer extent (3800 m × 3800 m). Well dots occupy a horizontal strip across the middle of the map reflecting their actual geography. Each dot is coloured by P_flood vulnerability:

  -------- -------------------------- ---------------------
  Colour   Category                   m_P range
  Green    Reachable                  \< 1.0× climatology
  Amber    Wet winter required        1.0--1.3×
  Red      Exceptional winter         1.3--2.0×
  Grey     Structurally unreachable   \> 2.0×
  -------- -------------------------- ---------------------

The legend and rainfall slider overlay the top-left and top-right corners of the map respectively. The map content is top-aligned within its container; any spare vertical space appears below as sand-coloured background.

# A9. Nearest-Type Assignments

Some wells are flagged with an asterisk (\*) and display a nearest-type assignment notice. These wells sit outside the SSM operational domain and were assigned to the nearest cluster as a best-available estimate. Forecasts for these wells should be treated as indicative rather than precise.

# A10. Practical Tips

-   After selecting a well, check both depth inputs: the current-depth default is the cluster's long-term mean for this calendar month, and the summer-minimum default is the cluster's long-term trough. Edit either to match your actual observations.
-   Use the live m_P preset when available --- it incorporates the actual current-season rainfall.
-   Compare the per-well long-term depths against the cluster averages in the well-details panel; large differences indicate the well behaves atypically within its cluster.
-   The forecaster works entirely offline after the initial page load; you can save the HTML file to a USB stick or phone for field use.
-   Drag the panel gutters to adjust the sidebar, map, and forecast panel widths to suit your screen.

Part B

Hydrological Scenario Viewer

# B1. Introduction

The Hydrological Scenario Viewer is an interactive HTML tool that allows you to explore how different climate and management scenarios affect groundwater levels across the Newborough Warren dipwell network. It computes per-well changes in equilibrium head (Δh) using the site's fitted state-space model coefficients and displays the results as an IDW-interpolated surface map, a cluster-level bar chart, a numeric data table, and summary metric cards.

The viewer is generated by Script 19 (19_spatial_groundwater.py) and contains all data embedded in the file. No server or internet connection is required.

# B2. Interface Layout

  -------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Panel          Purpose
  Left sidebar   Scenario presets, climate sliders (winter/summer P and PET multipliers), forestry controls (interception, β₂ scaling), display toggles, and Sy mode selector. A draggable splitter adjusts its width.
  Season tabs    Toggle between Annual, Winter (Nov--Mar), and Summer (May--Sep) views. All forecasts, map, and table update accordingly.
  Map            Canvas-rendered IDW interpolation surface of Δh (or absolute head, or depth-below-surface). Hillshade basemap with KML overlays.
  Bar chart      Per-cluster Δh shown as horizontal bars, coloured red (drying) or blue (wetting).
  Data table     Numeric breakdown per cluster: Δh, scenario head, storage shift, effective precipitation, and PET draw.
  Metric cards   Summary cards for all clusters, each C1--C5, and a Forest (C4+C5) aggregate. Each shows Δh, Sy, and storage shift.
  -------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

On narrow screens (\< 640 px) the layout stacks vertically.

# B3. Scenario Presets

Six preset buttons configure all sliders to physically meaningful combinations:

+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Preset       | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Baseline     | Current observed conditions. All multipliers at 1.00, forest interception at 24% (Corsican pine; Freeman 2008).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| UKCP18 2050s | Central estimate (50th percentile, RCP8.5) for Wales. Wetter winters (+10% P, +5% PET), drier summers (−15% P, +20% PET).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| UKCP18 2080s | End-century projection. Winter P +20% and PET +10%; summer P −30% and PET +35%.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|              | What the UKCP18 presets do, and do not, do. They do not rebuild the site's climate from a projected temperature. They take the rainfall and evaporative demand actually measured at RAF Valley and scale them by the UKCP18 percentages, so the shape of the record --- which months are wet, which are dry --- is kept and only its size changes.                                                                                                                                                                                                                                                                                                                    |
|              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|              | One point is worth knowing when reading the summer results. The UKCP18 evaporation changes are worked out on a physically based footing, while the site's own PET figures come from the Thornthwaite method, and the two do not respond to warming in the same proportion: Thornthwaite damps its own response, moving about 0.42 as far over the RAF Valley record. Applying the UKCP18 change to a Thornthwaite baseline is a deliberate and cautious choice --- the presets impose more evaporative demand than the site's own PET method would produce from the same warming, so the summer drying they show reads as a firm case rather than an understated one. |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Clearfell    | Complete canopy removal. Interception set to 0%. The β₂ multiplier is not a fixed number: it is recomputed on each pipeline run from the BACI-corrected Edge-tier ratio (Script 10e) and applied equally to both seasons. The viewer shows the value in use.                                                                                                                                                                                                                                                                                                                                                                                                          |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Broadleaf    | Restocking with deciduous species. Interception reduced to 15% (Komatsu et al. 2011). Seasonally varying β₂: winter 0.88× (leaf-off), summer 1.08× (leaf-on), from Script 21 deciduous phenology profile.                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Thinning     | 50% canopy density reduction. Interception halved to 12%. The β₂ multiplier is half the clearfell perturbation above 1.00×, recomputed with it on each run and applied equally to both seasons.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

You can also adjust any slider individually after selecting a preset; the display updates in real time.

# B4. Climate Sliders

Four sliders control the climate forcing multipliers independently:

-   Winter P (×): scales November--March precipitation.

-   Summer P (×): scales May--September precipitation.

-   Winter PET (×): scales winter potential evapotranspiration.

-   Summer PET (×): scales summer PET.

    All four sliders run from 0.50× to 1.50× in steps of 0.01 and start at 1.00×. That common range brackets the UKCP18 end-century probabilistic ranges for Wales under RCP8.5 while staying inside the linear steady-state domain of the fitted model.

A warning banner appears if slider combinations exceed UKCP18 plausible ranges or create physically contradictory configurations.

# B5. Forestry Controls

Separate interception sliders are provided for C4 (Main Forest) and C5 (Coastal Forest):

-   Interception fraction: the proportion of rainfall intercepted by the canopy. Corsican pine baseline is 0.24; broadleaf is 0.15; clearfell is 0.00.

Below the interception sliders, a shared β₂ scaling panel applies identically to both C4 and C5, with separate winter and summer controls:

-   Winter β₂: scales the evapotranspiration coefficient for the winter season. Range 0.5--2.0.
-   Summer β₂: scales the evapotranspiration coefficient for the summer season. Range 0.5--2.0.

The seasonal split captures deciduous phenology under broadleaf conversion: the Broadleaf preset sets winter β₂ to 0.88× (reduced transpiration when leaves are absent) and summer β₂ to 1.08× (elevated transpiration during the growing season). These controls only affect C4 and C5 wells; non-forest clusters are unaffected.

# B6. Map Rendering Modes

Three tabs above the map switch the colour surface:

-   Δh vs baseline (default): change from baseline equilibrium head. Blue = wetter, red = drier.
-   Absolute head: scenario-adjusted head in metres AOD, sequential colour scale.
-   Depth below ground: depth below ground surface (DEM minus IDW-interpolated head), anchored to Curreli et al. (2013) ecological thresholds: SD15b at 0.61 m and SD16 at 0.98 m.

In depth mode, a ridge-mask toggle suppresses interpolation over dune ridges where the DEM exceeds the local well-derived surface by more than 1.0 m.

# B7. Display Toggles and Tooltips

-   KML overlays: shows/hides the forest plantation, broadleaf restock area, clearfell compartment, and Llyn Rhos-ddu.

-   Well labels: toggles well identifiers on the map.

-   Mask dune ridges: in depth view, suppresses interpolation over dune ridges. On by default.

    Paths and lines: draws the eighteen linear features held in the site's Features.kml --- the four named paths and the numbered lines --- as dashed brown lines over the surface. Off by default, because they are reference features on the ground rather than analysis units.

    Which coefficients the viewer uses. Two buttons sit at the right of the map heading and choose which set of fitted coefficients the whole page uses: the map surface, the cluster chart and the data table all switch together, so you are never looking at a mixture. Whole record, the default, uses coefficients fitted to each well's complete monitoring record, which is the basis the report uses. Recent 100 months uses the most recent 100 months of valid readings at each well, reaching further back where a record has gaps. The buttons carry the actual dates, taken from the fits themselves rather than typed in.

    Choosing the recent basis brings up an orange note above the map. A shorter record makes drainage harder to measure, and on that basis several clusters --- the Main Forest most of all --- have a drainage rate the data can no longer tell apart from zero. The note gives the counts cluster by cluster. Leave the viewer on the whole record unless you have a specific reason to look at recent behaviour.

    Basemap slider. A slider at the right of the map buttons sets how strongly the shaded-relief background shows through beneath the water-table colours, from 0 to 200 per cent, starting at 60. Up to 100 per cent the relief fades in; above that the viewer darkens the shaded slopes further without washing out the lit ones, which helps when the colour surface is pale. It changes appearance only --- no value, colour scale or table figure depends on it.

Hovering over any well dot shows a floating tooltip with the well name, cluster, baseline head, Δh, scenario-adjusted head, specific yield, and storage shift.

# B8. Practical Tips

-   Start with a preset to see a scenario's overall effect, then fine-tune individual sliders.
-   Use the season tabs to compare winter wetting against summer drying under the same scenario.
-   Switch to Depth below ground with KML overlays on to see which areas breach the SD15b/SD16 thresholds.
-   The sidebar is resizable via the splitter; the map canvas is also resizable (drag the bottom-right corner).
-   The viewer works entirely offline once loaded.

Part C

Seasonal Extremes Scatter

# C1. Introduction

The Seasonal Extremes Scatter is an interactive chart plotting each well's mean annual summer minimum water-table depth against its mean annual winter maximum depth for the monitoring period 2005--2026. Wells are coloured by hydrogeological cluster, and Curreli et al. (2013) eco-hydrological threshold lines are overlaid. The chart provides an at-a-glance summary of which wells and clusters meet the SD15b and SD16 habitat condition targets.

The page is generated by Script 14 (14_climate_projections.py) and uses Chart.js for rendering.

# C2. Opening the Page

Open 14_seasonal_extremes_scatter.html in any modern web browser. Chart.js is loaded from a CDN, so an internet connection is needed on first load (or the library can be cached). The well data is embedded inline.

# C3. Reading the Chart

Each dot represents one well. The axes are:

-   X-axis: Mean annual summer minimum depth (m below pipe top). More negative = deeper water table in summer.
-   Y-axis: Mean annual winter maximum depth (m below pipe top). More negative = deeper water table in winter.

Wells in the upper-right quadrant have shallow water tables in both seasons (favourable for wet slack habitat). Wells in the lower-left have deep water tables year-round.

# C4. Threshold Lines

Four dashed lines mark the Curreli et al. (2013) eco-hydrological thresholds:

  ------------------ ------------------------ --------------------------------------------------------------------------------
  Line               Threshold                Meaning
  Vertical green     SD15b summer (−0.61 m)   Summer minimum must be shallower than 0.61 m for wet slack viability.
  Vertical red       SD16 summer (−0.98 m)    Summer minimum must be shallower than 0.98 m for dry slack viability.
  Horizontal green   SD15b winter (−0.10 m)   Winter maximum must reach within 0.10 m of the surface for wet slack flooding.
  Horizontal red     SD16 winter (−0.25 m)    Winter maximum must reach within 0.25 m for dry slack flooding.
  ------------------ ------------------------ --------------------------------------------------------------------------------

A well meeting both the summer and winter SD15b thresholds (upper-right of both green lines) has full wet slack habitat viability.

# C5. Cluster Legend

The legend shows the colour for each cluster: C1 (Lake Edge), C2 (Dune), C3 (Western Residual), C4 (Main Forest), and C5 (Coastal Forest). Wells not assigned to a core cluster appear as "UNKNOWN" in grey.

# C6. Search and Highlight

A search box above the chart lets you type a well name (e.g. "ceh36" or "nw10"). Matching wells are highlighted in orange with an enlarged dot; all other wells fade. The result text shows the well's exact values and cluster.

Click Clear to reset the view.

# C7. Practical Tips

-   Use the search to locate specific wells of management interest.
-   Wells plotting far to the left within C4 and C5 indicate forest-influenced water-table suppression.
-   Compare the cluster distribution relative to the threshold lines to assess which parts of the site meet conservation targets.
