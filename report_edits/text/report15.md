<!-- GENERATED MIRROR of report_edits/odt/report15.odt — do not edit.
     Regenerate with: python3 tools/refresh_mirrors.py -->

# []{#anchor}Data Availability

## []{#anchor-1}Data Availability and Software

The complete dipwell monitoring network, comprising 117 wells across Newborough Warren and the adjacent dune systems, is mapped at: [*https://www.google.com/maps/d/edit?mid=1hXLAauiMeaVsXhBR_IoUTziAtjk*](https://www.google.com/maps/d/edit?mid=1hXLAauiMeaVsXhBR_IoUTziAtjk) (M. Hollingham, unpublished).

The analytical pipeline underpinning this study is documented at [*https://newbroman.github.io/Newborough_Hydrology/*](https://newbroman.github.io/Newborough_Hydrology/) and comprises 50 steps across 17 phases covering data preparation, state-space modelling, and intervention analysis and mapping. A per-script methods supplement (Hollingham, 2026c) documents the analytical rationale, implementation decisions, and limitations for each pipeline step; it is available as a supplementary document accompanying this report. All analyses were implemented in Python using NumPy (Harris et al., 2020), pandas (McKinney, 2010), SciPy (Virtanen et al., 2020), statsmodels (Seabold and Perktold, 2010), scikit-learn (Pedregosa et al., 2011) and seaborn (Waskom, 2021), with figures produced in matplotlib (Hunter, 2007). Spatial analysis used GeoPandas (Jordahl et al., 2020), rasterio (Gillies, 2013), contextily (Arribas-Bel et al., 2020) and adjustText (Flyamer et al., 2020).

Full diagnostic outputs for all 66 reference network wells and all 17 clearfell BACI wells are reproducible by running the published pipeline. Groundwater monitoring data supporting this study are also available.

**Source Data Credits:**

-   **Climate Data:** Meteorological records for RAF Valley were obtained from the UK Met Office (MIDAS Open Government Licence).

-   **Topographic Data:** Terrain analysis was performed using the 2 m resolution LiDAR digital terrain model provided by Natural Resources Wales (NRW) and accessed via DataMapWales (the Welsh Government geospatial portal, successor to the decommissioned Lle Geo-Portal); 2 m DTM, captured March 2023. © Natural Resources Wales and Ordnance Survey.

-   **Groundwater Data:** The primary dipwell monitoring record was independently maintained by the author.

-   **Historic Mapping:** The nineteenth-century shoreline and dune edge were digitised from Ordnance Survey, Anglesey Sheet XXV.NW, revised 1899, published 1901, reproduced with the permission of the National Library of Scotland (https://maps.nls.uk) under CC-BY-NC-SA 4.0. The sheet was georeferenced to OSGB36 / British National Grid from 27 ground control points (RMSE 5.95 m; 3.27 m excluding two outliers). The source raster is not redistributed; the digitised vectors are original work.

-   **Shoreline Data:** The mean-high-water shoreline from which every well-to-coast distance in this study is measured was derived from OpenStreetMap (**natural=coastline**), retrieved via the Overpass API and clipped to the west-facing Caernarfon Bay frontage. Map data © OpenStreetMap contributors, available under the Open Database Licence (ODbL, https://www.openstreetmap.org/copyright).

-   **Methods Supplement:** Hollingham, M., 2026c. Newborough Warren Hydrogeological Analysis --- Methods Supplement. Unpublished technical document, version 1.5.3. Accompanies this report.
