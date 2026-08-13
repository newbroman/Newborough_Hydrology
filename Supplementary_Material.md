**Supplementary Material**

*Hollingham (2026) --- Newborough Warren Coastal Sand Dune Aquifer, Isle of Anglesey*

Contact: [**martin.hollingham+nrg@gmail.com**](mailto:martin.hollingham+nrg@gmail.com)

ORCID: [**0000-0003-0253-9301**](https://orcid.org/0000-0003-0253-9301)

# **Supplementary Note S1: Interactive Map**

Supplementary File S1: Interactive map of the full dipwell monitoring network (Google Maps), accessible at:

[**https://www.google.com/maps/d/viewer?mid=1hXLAauiMeaVsXhBR_IoUTziAtjk**](https://www.google.com/maps/d/viewer?mid=1hXLAauiMeaVsXhBR_IoUTziAtjk)

# **Supplementary Note S2: Aquifer Geometry, Hydraulic Parameterisation and the Basis of the Spatial Flow Model**

## **S2.1 The Borehole Data Problem**

Darcy's law and any spatially explicit groundwater flow model require three spatially resolved inputs: hydraulic conductivity (K), aquifer thickness (b, from which transmissivity T = K·b is derived), and hydraulic gradient (∇h). For the Newborough Warren dune system, only the third of these --- the hydraulic gradient --- is well constrained, through the 88-dipwell monitoring network. Hydraulic conductivity and aquifer thickness are poorly constrained, because borehole logs providing lithological or geophysical evidence of the depth to the bedrock or glacial till substrate are absent across the great majority of the 700 ha dune system.

The available borehole evidence is confined to four locations documented in Betson et al. (2002), a report commissioned by the Countryside Council for Wales (Contract FC†73-05-18) covering hydrogeological investigations at the site. These boreholes provide minimum depth-to-basement constraints at four spatial points and constitute the only direct subsurface lithological evidence available for the site. They are summarised in Table S2.1.

  ---------------- ---------------------- ----------------------- ------------------------ ----------------------
  **Borehole**     **Easting (OSGB36)**   **Northing (OSGB36)**   **Sat. thickness (m)**   **Source**
  Water borehole   241,721                364,133                 12.8 (min.)              Betson et al. (2002)
  NH1              241,734                363,306                 6.5                      Betson et al. (2002)
  NH2              242,024                363,107                 6.5                      Betson et al. (2002)
  Borehole 3       242,837                363,288                 3.65                     Betson et al. (2002)
  ---------------- ---------------------- ----------------------- ------------------------ ----------------------

**Table S2.1.*** Borehole constraints on saturated thickness from Betson et al. (2002). Values represent confirmed minimum depth to the low-permeability substrate (glacial till or bedrock). The Water borehole value of 12.8 m is a minimum --- drilling did not reach the substrate. The eastern borehole (Borehole 3) shows progressive thinning toward the Menai Strait. These four boreholes constitute the only direct subsurface lithological evidence available for the 700 ha dune system and represent the most important data gap for any future spatially explicit groundwater model.*

The tracer test reported by Betson et al. (2002) provides the single direct estimate of hydraulic conductivity for the site, yielding K = 6.0 m/day at the central dune plain (range 3.0--9.0 m/day from the sensitivity analysis). This value is used as the site-wide K constant where transmissivity is required for the Darcy flow direction vectors in the spatial figures (§4.9.6, Figure 57), with the range providing the basis for the exploratory uncertainty envelope noted in the figure annotations.

## **S2.2 The β₁ Proxy for Relative Aquifer Thickness**

The physical interpretation of β₁ is the fraction of a unit rainfall pulse that reaches the water table as a head rise, integrated over the monthly timestep. In an unconfined aquifer, this is governed by the depth of the unsaturated zone and the specific yield: a thick unsaturated zone above a large storage volume attenuates the rainfall-to-head transfer, producing a low β₁. A shallow, low-storage aquifer (thin unsaturated zone, low Sy) produces a high β₁ --- rainfall arrives at the water table quickly and raises it sharply. Although β₁ cannot be inverted algebraically to yield aquifer thickness without independent knowledge of the recharge flux and specific yield, its spatial pattern is a reliable proxy for the relative contrast in aquifer thickness across the site.

The Eastern Block (C1: β₁ = 4.578; C2: β₁ = 3.978) and Western Residual cluster (C3: β₁ = 3.572) contrast is consistent with the geological interpretation of Stratford et al. (2007): the Eastern Block sits on shallow till and estuarine deposits, producing a thin, storage-limited aquifer with a flashy response; the Western Residual Cluster occupies deep, clean aeolian sand, producing a capacious, buffered aquifer with an attenuated response. The Forest cluster (C4: β₁ = 2.515) is anomalously low even relative to C3, reflecting canopy interception rather than additional aquifer depth --- confirmed by the depth-dependent PET analysis (Script 15) which found λ = 0 optimal for C4, indicating that capillary disconnection at depth is not the primary control. C5 (Coastal Forest: β₁ = 2.412) shows a comparable value to C4, consistent with both clusters carrying the same Corsican pine canopy on the same deep sand substrate.

  ------------- ------------------ -------- -------- -------- -----------------------------------------------------------------------------------
  **Cluster**   **Label**          **β₁**   **β₂**   **β₃**   **Geological context**
  C1            Lake Edge          4.578    0.963    0.090    Shallow till/estuarine substrate (NH1, NH2 boreholes: 6.5 m); rapid lake exchange
  C2            Dune               3.978    1.766    0.066    Shallow till substrate consistent with C1; mature open dune
  C3            Western Residual   3.572    1.850    0.058    Deep aeolian sand; Water borehole ≥12.8 m; DEM ridge geometry
  C4            Main Forest        2.515    2.546    0.020    Same deep sand substrate as C3; low β₁ reflects 24% canopy interception
  C5            Coastal Forest     2.412    1.324    0.045    Pine canopy on coastal sand; geomorphological thinning toward Menai Strait
  ------------- ------------------ -------- -------- -------- -----------------------------------------------------------------------------------

**Table S2.2.*** Cluster mechanistic coefficients (from Table 3, displacement-formulation SSM) and geological context. The β₁ contrast between Eastern Block (C1/C2) and Western Residual cluster (C3) is consistent with the stratigraphic interpretation of Stratford et al. (2007). C3 and C4 share the same deep aeolian sand body, confirmed by β₁ similarity after correcting for canopy interception and by Pearson affinity persistence post-felling. Borehole 3 (3.65 m, eastern margin) confirms progressive thinning toward the coast.*

### ***S2.2.1 Aquifer Thickness Surface (Developed for the PDE Model)***

During development, a two-dimensional finite-difference partial differential equation (PDE) solver was implemented as an alternative spatial framework (see S3.3). That model required a spatially continuous aquifer thickness surface to compute transmissivity T = K·b at each grid cell. Because only four borehole constraints were available, an IDW-interpolated thickness surface was constructed using the borehole values as hard nodes supplemented by cluster-level thickness priors derived from the β₁ proxy argument above and per-well overrides at geological boundaries. The surface was interpolated on a 50 m grid using power-1 IDW with a physical minimum of 0.3 m enforced.

The PDE model was subsequently evaluated and rejected (S3.3) because it produced near-zero site-wide differences for forest management scenarios, primarily due to dilution of the modified β coefficients during grid interpolation, weak drainage feedback at C4, and the absence of ridge-derived lateral recharge from the source terms. The thickness surface is therefore not used in any published result. The per-well equilibrium framework adopted in the main paper (Section 3.8) operates directly from the fitted β coefficients at each well and does not require a thickness parameterisation. The Darcy flow direction vectors shown in Figure 57 are normalised head-gradient vectors derived from the interpolated mean head surface and are independent of aquifer thickness.

The borehole constraints in Table S2.1 and the geological contrasts summarised in Table S2.2 remain relevant for any future spatially explicit model. Slug tests at two to three representative wells per cluster and a ground-penetrating radar survey of aquifer thickness are identified as the highest-priority data gaps for future field campaigns (§5.9).

### ***S2.2.2 Per-Well Geological Constraints***

Several wells occupy geological settings that depart from their cluster's typical substrate. These are noted here for reference, as they would serve as boundary constraints for any future spatial model.

CEH14 (241,292 E, 364,488 N), classified as C4, sits at the crest of the bedrock ridge at 14.4 m AOD with a mean water table head of 13.3 m AOD. The water table is approximately 1.1 m below ground surface here. CEH14 overlies irregular bedrock topography on the elevated ridge flank, where buried ridges impede lateral drainage --- consistent with its anomalous negative β₃ under the depth-from-surface formulation. Its water-balance residual is −0.011 m/month --- the most negative in the network, not the largest positive (§4.9.7, Figure 58).

Wells CEH7 (243,386 E, 363,613 N) and CEH8 (243,150 E, 363,382 N) sit at the far eastern estuarine margin of the site, where the DEM confirms ground elevation of 1.2--5.2 m AOD. Both represent coastal pinch-out positions where the aquifer thins to approximately 4.0 m. and their records are intermittent.

## **S2.3 Why C4 Retains Its Cluster Identity After Clearfell**

A key question for the scenario analysis is whether the clearfell treatment wells (FE1, FE2, FE4, LIS1) converged toward C3 open-dune behaviour after the December 2017 felling. The Pearson affinity analysis (Section 4.3) provides a direct empirical test: all four impact wells maintained r \> 0.97 affinity with C4 even in the post-felling period (2018--2026), with no significant shift toward C3 affinity.

This persistence is consistent with the interpretation that the Forest cluster signature at these wells reflects deep sandy substrate at high topographic elevation rather than canopy influence alone --- in which case convergence toward open-dune behaviour may not be achievable regardless of management intervention. C4 wells sit at the highest topographic positions in the dune system (mean head 9.52 m AOD), and their deep unsaturated zones and low recharge sensitivity reflect their geological position, not only their canopy cover. This conclusion is independently supported by the NW10 broadleaf comparison (§5.6.3): NW10, situated within the 1993 clearfell and 1996 broadleaf restocking block, has maintained C4 cluster affinity (r = 0.986) throughout the 18-year monitoring period despite its different canopy cover, confirming that substrate position rather than canopy type is the dominant control on cluster identity.

## **S2.4 Reproducibility**

The spatial model parameterisation documented in this note is implemented in 19_spatial_groundwater.py (scenario viewer data preparation, IDW thickness surface, per-well equilibrium calculations) and 20_spatial_figures.py (Darcy flow direction vectors, mean head surface, water balance residual field). The β₁ proxy analysis draws on the cluster-level SSM coefficients exported by 03_state_space_model.py (03_03_cluster_mechanistic_coefficients.csv). The Pearson affinity test for C4 cluster persistence post-felling is computed in 05_pearson_affinity.py. All scripts read intermediate data produced by the main pipeline and are maintained in the canonical pipeline sequence. The interactive scenario viewer (scenario_viewer.html) is a standalone browser application that reads the per-well coefficient and location CSVs exported by Script 19.

# **Supplementary Note S3: Scenario Modelling Framework and Limitations**

## **S3.1 Purpose and Scope of the Scenario Analysis**

An exploratory scenario analysis was developed to investigate whether the site's own SSM β coefficients could yield defensible quantitative predictions of water table response to management interventions and climate change. This note documents the scenario framework adopted (the per-well equilibrium framework described in Section 3.8), the alternative PDE-based approach that was evaluated and rejected during development, and the structural limitations that apply to any equilibrium representation of the system. The scenario outputs themselves are reported in Section 4.10 and discussed in Section 5.5.2 of the main paper; this note provides the technical reasoning behind the methodological choices and their limitations.

## **S3.2 The Per-Well Equilibrium Framework**

The scenario framework adopted in this study is a well-level equilibrium calculation that applies scenario-specific perturbations to the SSM forcing terms (rainfall, PET, canopy interception, atmospheric draw) and computes the resulting change in equilibrium head for each reference well. Per-well Δh values are then interpolated to a 50 m grid on the British National Grid by Delaunay triangulation with linear barycentric weighting (scipy.interpolate.griddata, method=\"linear\"), masked to the rectangular sea-boundary extent; the resulting field is rendered in the interactive scenario viewer rather than as a static map. The accompanying interactive scenario viewer (scenario_viewer.html) renders the same per-well Δh field using power-1 eight-nearest-neighbour inverse-distance weighting for responsiveness under slider-driven re-interpolation, and additionally offers a depth-below-surface view (DEM minus interpolated head, per cell) with dune-ridge cells masked --- see S3.7 for the viewer-specific rendering conventions. The full per-scenario × per-season × per-cluster Δh output is tabulated in the supplementary file 19_scenario_summary.csv.

The scenario head change for each well is computed directly from the fitted SSM equation as

*Δh = (β₁·P_eff,sc − β₂,sc·PET_sc − β₃·h̄\_disp) − (β₁·P_eff,0 − β₂·PET₀ − β₃·h̄\_disp)*

where the β₃·h̄\_disp term cancels algebraically between scenario and baseline expressions, so β₃ does not materially affect the computed Δh. Specific yield does not appear in the equation because the fitted β coefficients already embed the aquifer storage response through the SSM fit to observed head data; the per-well WTF-derived Sy values (Section 3.7.3) are retained as supplementary display information in the interactive viewer, not as a divisor on Δh. The framework is honest about what it is: a geometric aggregator of SSM responses across the cluster structure, not a physical model of groundwater flow.

The per-well framework has two important structural features that shape the interpretation of its outputs. First, scenario parameter changes for canopy interception and β₂ apply only to the C4 and C5 Forest cluster wells, because that is where the relevant physical changes occur under forest management. The framework therefore necessarily produces a response confined to the C4/C5 zone and its immediate interpolated surroundings, with effectively no propagation into C1, C2, or wider C3 clusters. Second, climate scenario parameter changes (ΔP, ΔPET) apply to all reference wells simultaneously, so the resulting Δh field is spatially continuous and reflects the site-wide β coefficient structure. The contrast between forest management and climate scenarios in the spatial outputs is therefore a direct consequence of which wells are affected by which perturbations, not an artefact of the numerical method.

## **S3.3 Evaluated-and-Rejected: The 2D Steady-State PDE Model**

During development, an alternative spatial framework was implemented as a two-dimensional finite-difference PDE solver based on the Helmholtz form of the steady-state groundwater flow equation:

*∇·(T·∇h) − β₃·h = −(β₁·P_eff − β₂·PET)*

with transmissivity T = K·b (K = 6.0 m/day after Betson et al., 2002; b IDW-interpolated from four borehole constraints supplemented by cluster-level priors derived from the β₁ proxy, also after Betson et al., 2002). Dirichlet head conditions (h = 0 m AOD) were applied at sea boundaries, and implicit Neumann no-flow conditions at the ridge. The sparse linear system of approximately 4,200 equations was solved using scipy.sparse.linalg.spsolve (Virtanen et al., 2020).

This approach is well-posed mathematically --- the Helmholtz structure guarantees a unique solution with the given boundary conditions --- and was physically consistent in that the β coefficients entering the source term are the same parameters estimated from the observed well records. The solver produced physically plausible baseline head surfaces and Darcy flux fields qualitatively similar to those obtained from the per-well framework.

However, the PDE solver produced near-zero site-wide differences for forest management scenarios (mean Δh = −0.003 to −0.008 m for full clearfell and thinning), for three structural reasons.

First, the forest management scenarios modify β coefficients only for the C4 and C5 Forest wells. These per-well β values are then IDW-interpolated to the 4,235-cell grid. Because the forest wells constitute a small minority of the 88-dipwell network, the modified β values are heavily diluted by the surrounding clusters during interpolation. The source term β₁·P_eff − β₂·PET therefore changes by only a small amount at each cell, and the resulting change in the steady-state head solution is proportionally small.

Second, the internal drainage term β₃·h provides a stabilising feedback in the Helmholtz equation. C4 has the lowest β₃ in the network (0.020, compared with 0.058 for C3 and 0.066 for C2; Table 3). This means that in the C4 zone the drainage feedback is weak, and a moderate source term change produces only a small equilibrium head change.

Third, and most fundamentally, the steady-state PDE does not capture the ridge-derived boundary subsidy that sustains the C4 water table. The observed mean head at C4 (9.52 m AOD) is substantially higher than the mean at C3 (6.09 m AOD), not because of C4's β coefficients but because the C4 wells are proximal to the bedrock ridge and receive lateral recharge from the ridge slope. The water-balance residual field does not support a ridge-derived flux: CEH14, the well most proximal to the ridge, carries the most negative residual in the network (−0.011 m/month), the three wells above +0.02 m/month all sit in the open dune (nw2, T41a, nw1), and the field shows no gradient on either axis (Spearman ρ = −0.02 on easting, p = 0.91; ρ = −0.14 on northing, p = 0.27). Whether the elevated C4 head reflects a lateral subsidy or simply the topographic setting of wells sited on the ridge flank cannot be resolved from the water-level record. What remains is the narrower and still valid point that the steady-state PDE source terms are parameterised from the SSM β coefficients alone and do not represent the elevated boundary condition at the ridge margin, so the PDE understates the C4 water table under both baseline and scenario conditions and the difference between the two solutions is correspondingly small (§4.9.7, Figure 58).

A fully calibrated continuous-flow model capable of representing the ridge boundary subsidy dynamically would require, at minimum: (i) slug tests at two to three representative wells per cluster to constrain the spatial distribution of K (currently constrained only by the single tracer test of Betson et al., 2002); (ii) a ground-penetrating radar survey of aquifer thickness to replace the indirect β₁-proxy constraints with direct measurements; and (iii) instrumentation of the ridge boundary subsidy pathway sufficient to parameterise a time-varying boundary flux term. These are the same parameter-sparsity constraints that produced calibration difficulties in the Betson et al. (2002) MODFLOW model at this site.

For these reasons, the PDE approach was judged to overclaim relative to the data available and was rejected in favour of the per-well equilibrium framework. The framework represents what the SSM parameterisation supports without claiming spatial flow dynamics the monitoring data cannot constrain.

## **S3.4 Climate Scenarios in the Per-Well Framework**

Climate scenarios applied under the per-well framework are based on the UKCP18 Regional 12 km projections for Wales (Met Office, 2018) and the CHESS-SCAPE bias-corrected projections of Robinson et al. (2023). Two scenarios are carried forward into the Results (Section 4.10): UKCP18 2050s (2040--2069) applies a winter precipitation increase of +10%, summer precipitation decrease of −15%, winter PET increase of +5% and summer PET increase of +20%; UKCP18 2080s (2070--2099) applies +20%, −30%, +10% and +35% respectively for the same four terms. Both scenarios use RCP8.5 central-estimate (50th-percentile) values. Perturbations are applied per season, with winter defined as November--March and summer as May--September; the climatological baselines against which the perturbations are applied are the 2005--2026 monthly means from the RAF Valley climate record. The resulting Δh for each well is computed for each season separately, and the annual Δh is reported as the 0.5-weighted mean of the winter and summer equilibrium responses --- this convention captures the physically significant seasonal asymmetry between winter recharge and summer evaporative loss that an annual-mean forcing would obscure.

Three limitations on the interpretation of these outputs apply. First, the perturbations used are central-estimate values; the UKCP18 probabilistic range at the 10th and 90th percentiles spans roughly half to twice the central perturbation for precipitation and a broader range still for PET, so the Δh values reported here are a central point within a substantially wider envelope of plausible responses. Users of the interactive scenario viewer (scenario_viewer.html) can explore perturbations across the full 0.5--1.5× range of the seasonal sliders to visualise this envelope. Second, the equilibrium framework computes the steady-state response to sustained seasonal perturbations and does not resolve within-year dynamical propagation of recharge between winter and summer --- for example, the effect of a wetter winter on the summer minimum through carry-over storage is captured only to the extent that the SSM β₃ drainage coefficient encodes it in the fitted mean. Third, the framework holds the SSM β coefficients themselves fixed at their historical values; it does not allow for structural changes in the β coefficients under future climate (for example, a higher β₂ under consistently warmer summers through increased vapour pressure deficit). Within these limitations, the climate scenario output is the most quantitatively defensible use of the equilibrium framework: every cluster's response is derived from its own fitted β coefficients under a uniform climate perturbation that reflects the current best estimate for the site's regional climate trajectory, and the result reflects the physical partition of rainfall and PET sensitivity that the SSM has estimated from 21 years of observation.

## **S3.5 Forest Management Scenarios in the Per-Well Framework**

Forest management scenarios (full clearfell, 50% thinning, broadleaf conversion) apply canopy parameter changes only to the C4 and C5 Forest wells, and the framework correctly produces a response confined to the C4/C5 zone. This is a feature of the framework, not a bug: under the SSM parameterisation, canopy management directly affects only the wells beneath the canopy, and there is no structural mechanism for canopy effects to propagate into the open dune clusters beyond the hydraulic gradient already implicit in the baseline heads. The BACI monitoring record provides empirical corroboration of this structural feature: post-felling displacement is concentrated at the core impact wells, and wells outside the C4 cluster show no detectable felling-specific response once common-mode climate variability is accounted for (§4.6.4).

The clearfell scenario applies a β₂ multiplier of ×1.108 at C4 and C5 wells, derived dynamically from the BACI-corrected Edge-tier post-felling β₂ ratio reported in §4.6.6 (Table 10): Edge mean ratio 1.101 minus Climate Control mean drift 0.993, plus 1.0. Canopy interception is set to 0%. The framework predicts modest annual water table rises at both forest clusters (C4: +0.028 m/month head, equivalent to +4.7 mm w.e./month; C5: +0.034 m/month head, +8.8 mm w.e./month), with a strongly asymmetric seasonal profile reflecting the dominance of summer PET in the β₂ sacrificial shielding mechanism established in §4.6.6 and §5.5.2.

The thinning scenario applies a β₂ multiplier of ×1.054 (half the clearfell perturbation) with canopy interception reduced from 24% to 12%. The framework predicts approximately half the clearfell response at both forest clusters (C4: +0.014 m/month, +2.3 mm w.e./month; C5: +0.017 m/month, +4.4 mm w.e./month), as expected.

The broadleaf conversion scenario is represented by replacing the Corsican pine canopy interception fraction of 24% (Freeman, 2008) with an annual-mean deciduous interception of 15% (following the temperate deciduous meta-analysis of Komatsu et al., 2011) while holding annual-mean β₂ at baseline. No annual-mean justification exists for a year-round β₂ adjustment under broadleaf: the canopy is leafed in summer and leafless in winter, and the annual mean β₂ is expected to be comparable to pine. The framework predicts a near-neutral annual response at both forest clusters (C4: +0.010 m/month head; C5: +0.012 m/month head), masking a pronounced seasonal asymmetry: winter head-space values are the largest of any forestry scenario, but the summer response is negative at C4 (−0.007 m/month) as the growing-season transpiration penalty under mature deciduous canopy (β₂ summer multiplier ×1.113) consumes the interception gain. The net annual volumetric effect is −3.4 mm w.e./month at C4 and +0.1 mm at C5. The seasonal asymmetry that underlies the phenological mechanism described in §5.5.2 --- larger winter recharge pulse under leafless canopy, steepened hydraulic gradient, accelerated drainage into summer --- is a dynamical trajectory response that the equilibrium framework does not resolve.

For the Figure 71 hydrograph (§5.7.4), a seasonally-varying β₂ is applied to the broadleaf scenario to represent the full-LAI summer canopy and leafless winter canopy. This seasonal parameterisation is a visualisation device and is not part of the §4.10 Results; it is used specifically to communicate the phenological argument from §5.5.2 alongside the BACI-observed record. The annual-mean output in 19_scenario_summary.csv remains the quantitatively citeable framework result.

## **S3.6 Implications and Future Work**

The per-well equilibrium framework is a lightweight analytical device for translating the SSM β coefficients into spatial summaries of equilibrium head response. Its strengths are that it makes no claims beyond what the SSM itself supports, that it is fully reproducible from the published CSV outputs, and that it is explorable through an interactive viewer that exposes all parameter choices to the user. Its limitations are those of any equilibrium framework: it does not resolve dynamical trajectory responses, it does not capture cluster-to-cluster hydraulic coupling, and it cannot simulate transient interventions in which the time evolution of the water table matters for ecological outcome. The framework is adequate for the questions the paper addresses --- whether forest management in the C4/C5 zone affects summer minima in C1 and C2, and how climate perturbations partition across the cluster structure --- and the BACI monitoring record confirms the framework's structural conclusions.

Answering a different class of question, such as how a hypothetical intervention along the CEH14 ridge subsidy pathway would propagate through the aquifer, would require a calibrated continuous-flow model. For that, the critical unknowns are hydraulic conductivity (currently constrained by a single tracer test at K = 6.0 m/day; Betson et al., 2002) and aquifer thickness (inferred from four borehole logs across 700 ha). Slug tests at two to three representative wells per cluster and a ground-penetrating radar survey of aquifer thickness are identified as the priority field measurements required to enable a properly calibrated continuous-flow model, should future work pursue intervention scenarios where lateral hydraulic propagation is central to the management question.

**Summary of scenario modelling approach**

**Primary framework: **Per-well equilibrium with triangulation-linear grid rendering (Sections 3.8, 4.10; scenario_viewer.html; 19_scenario_summary.csv)

**Evaluated and rejected: **2D steady-state Helmholtz PDE solver (Section 3.8 PDE paragraph; S3.3 above)

**Visualisation device: **Figure 71 synthetic hydrograph with seasonally-varying broadleaf β₂ (§5.7.4; Script 21)

**Empirical corroboration: **BACI monitoring record (§4.6)

## **S3.7 Interactive Viewer: Rendering Conventions and Depth-Mode Visualisation**

The companion interactive scenario viewer (scenario_viewer.html; Hollingham, 2026b) renders the per-well Δh field described in S3.2, but uses a distinct grid-rendering method at the browser to preserve responsiveness under slider-driven re-interpolation. The viewer implements inverse-distance weighting with power 1 and eight nearest neighbours (10 m distance floor; 5 m exact-value shortcut) rather than the triangulation-linear method used for the static figures. Power-1 IDW with a fixed neighbour set produces a smoother surface than the naïve power-2 IDW previously used, removes the bullseye halo artefacts that arose around individual wells on the Δh surface, and is sufficiently close to the triangulation-linear rendering at well locations that the two methods agree to within the mapped colour-scale resolution across the interpolated interior. At well locations the viewer returns the well's observed value unchanged; outside the convex hull of the wells it extrapolates under the IDW kernel where the triangulation-linear method would return no data. This distinction is most visible near the south-eastern coastal margin, where the viewer renders a short extrapolated zone that the static figures correctly leave blank.

The viewer offers three complementary display modes. The first two --- change in water table elevation (Δh) and absolute water table elevation (m AOD) --- are elevation-based surfaces, and are the two quantities exported to 19_scenario_summary.csv. The third mode, depth below surface (m), is a viewer-specific visualisation derived in the browser. It is computed per grid cell as d = h_DEM(E, N) − h_WT(E, N), where h_DEM is the bilinearly-interpolated LiDAR DEM elevation at cell centre and h_WT is the IDW-interpolated scenario water table elevation at the same cell. This per-cell subtraction is the quantity that mediates the ecological response: the Curreli et al. (2013) slack vegetation thresholds are defined in depth-below-surface terms (SD15b wet slack summer viability limit: 0.61 m; SD16 dry slack viability limit: 0.98 m), and rendering the scenario water table against the topographic surface permits direct visual identification of the slack positions where scenarios cross these thresholds. The viewer's depth-mode colour scale is anchored on these thresholds: light blue at the 0.10 m winter flooding limit, green at 0.61 m, orange at 0.98 m, and deep red at 1.50 m, with explicit black tick marks on the legend at the SD15b and SD16 threshold depths.

A dune-ridge mask is applied exclusively in depth-below-surface mode. The rationale is that the water table is a continuous surface in space, and its elevation relative to ordnance datum is well-defined at every point within the site regardless of whether the overlying ground is a ridge or a slack floor; elevation-based maps (modes one and two) therefore require no topographic masking. Depth below surface, however, is meaningful only where the ground is approximately at the well-plane elevation --- at a dune ridge the interpolated water table sits several metres below ground, but this is a consequence of the ridge height, not of any hydrological feature, and rendering such cells would produce a misleading strong-red patch on the depth map that obscures the ecologically relevant slack-floor response. The viewer masks a cell in depth mode when the DEM elevation at that cell exceeds the IDW-interpolated well-plane elevation (computed by the same IDW kernel applied to well DEM ground elevations) by more than 1.0 m. This threshold is user-toggleable from the viewer's control panel; disabling it reveals the unmasked depth field, which can be useful for diagnostic inspection but should not be used for ecological interpretation.

Additional viewer conventions of note: the basemap is a LiDAR-derived greyscale hillshade rendered at approximately 35% opacity underneath the scenario surface, matching the static figure hillshade convention of map_utils.load_dem_hillshade with azimuth 315°, altitude 35° and vertical exaggeration 3; climate perturbations can be explored across the full 0.5--1.5× range per season, extending substantially beyond the UKCP18 2050s and 2080s central-estimate presets to allow sensitivity analysis across the probabilistic envelope; and tooltips on any well display both the baseline and scenario-perturbed depth values alongside the absolute head and Δh, providing a direct visual link between the per-well framework output and the ecological depth-below-surface interpretation.

## **S3.8 Reproducibility**

The per-well equilibrium framework and climate/forestry scenario calculations are implemented in 19_spatial_groundwater.py, which exports the full per-scenario × per-season × per-cluster output to 19_scenario_summary.csv and generates the interactive scenario viewer. The interactive scenario viewer (scenario_viewer.html) implements the browser-side IDW rendering described in S3.7 and reads the same per-well data. The synthetic mean-year hydrograph (Figure 71) is generated by 21_forestry_scenarios.py, which reads BACI coefficients from the Script 10 clearfell suite outputs. All scenario parameters --- UKCP18 perturbation fractions, canopy interception values, β₂ multipliers, and seasonal definitions --- are defined as named constants at the head of each script and are fully documented in the scenario_viewer.html source.

# **Supplementary Note S4: Specific Yield Mapping**

## **S4.1 Per-Well Estimates**

**Table S4.1.** Individual Well WTF Specific Yield Estimates --- Newborough Warren 2005--2026: event-based median specific yield (Sy) derived from the water table fluctuation (WTF) method (Healy and Cook, 2002) for the 66 reference-network wells. Cl. = cluster under the k = 5 partition (C1 Lake Edge, C2 Dune, C3 Western Residual, C4 Main Forest, C5 Coastal Forest). n = number of qualifying monthly rising-limb events (criteria: Δh \> 5 mm, net recharge P − PET \> 10 mm). Q25/Q75 = interquartile range; a wide IQR reflects month-to-month variability in event estimates rather than measurement error. Wells in the forest clusters C4 and C5, marked Int. corr. = Yes, have net recharge adjusted for 24% canopy interception (Freeman, 2008). CEH12 (bedrock ridge --- WTF response reflects fractured rock) and CEH15 (forest slack floor --- slack topography dominates water table dynamics) are excluded from the IDW interpolation surface and do not appear here. Source: 18_wtf_01_well_sy_estimates.csv.

  ------- ---- ---- ------- ------- ------- -----
  CEH11   C1   59   0.235   0.158   0.307   
  CEH23   C1   44   0.207   0.123   0.252   
  CEH25   C1   54   0.178   0.134   0.246   
  CEH26   C1   49   0.214   0.115   0.276   
  CEH27   C1   52   0.216   0.140   0.298   
  CEH5    C1   65   0.194   0.159   0.275   
  CEH6    C1   70   0.216   0.123   0.347   
  CEH10   C2   64   0.263   0.161   0.353   
  CEH24   C2   52   0.239   0.168   0.317   
  CEH28   C2   41   0.236   0.183   0.314   
  D10     C2   50   0.279   0.222   0.393   
  D15     C2   54   0.288   0.232   0.370   
  D17     C2   54   0.271   0.198   0.351   
  D38     C2   54   0.227   0.172   0.287   
  D41     C2   46   0.240   0.191   0.312   
  D43     C2   59   0.271   0.212   0.347   
  D44     C2   50   0.220   0.164   0.316   
  D5      C2   49   0.274   0.202   0.348   
  D6      C2   57   0.267   0.202   0.360   
  D7      C2   50   0.286   0.220   0.323   
  D8      C2   47   0.247   0.179   0.371   
  D9      C2   49   0.259   0.203   0.362   
  L7      C2   63   0.286   0.223   0.337   
  NW3     C2   54   0.267   0.190   0.354   
  NW4     C2   58   0.265   0.173   0.339   
  NW4B    C2   54   0.240   0.159   0.318   
  T41A    C2   55   0.227   0.172   0.323   
  T41B    C2   45   0.215   0.159   0.313   
  T41C    C2   47   0.215   0.189   0.308   
  T41D    C2   47   0.254   0.197   0.334   
  WMC1    C2   51   0.274   0.207   0.406   
  CEH1    C3   67   0.273   0.226   0.346   
  CEH18   C3   53   0.364   0.284   0.433   
  CEH21   C3   31   0.413   0.356   0.445   
  CEH36   C3   38   0.349   0.297   0.422   
  CEH39   C3   38   0.349   0.287   0.407   
  CEH4    C3   53   0.349   0.255   0.400   
  CEH40   C3   27   0.285   0.243   0.323   
  CEH41   C3   36   0.306   0.256   0.345   
  CEH42   C3   34   0.351   0.284   0.389   
  CEH9    C3   53   0.347   0.275   0.395   
  D25     C3   45   0.289   0.242   0.393   
  NW1     C3   72   0.259   0.215   0.369   
  NW11    C3   68   0.285   0.229   0.336   
  NW13    C3   50   0.249   0.206   0.334   
  NW2     C3   68   0.252   0.212   0.342   
  NW5     C3   56   0.305   0.250   0.350   
  NW6     C3   45   0.281   0.206   0.346   
  NW7     C3   47   0.333   0.280   0.398   
  WMC2    C3   53   0.343   0.295   0.412   
  WMC3    C3   36   0.328   0.279   0.423   
  WMC4    C3   51   0.250   0.208   0.353   
  CEH13   C4   50   0.231   0.172   0.325   Yes
  CEH14   C4   55   0.194   0.126   0.265   Yes
  CEH2    C4   60   0.241   0.188   0.337   Yes
  CEH20   C4   50   0.254   0.208   0.312   Yes
  CEH30   C4   48   0.278   0.211   0.355   Yes
  CEH32   C4   49   0.240   0.181   0.366   Yes
  CEH33   C4   48   0.255   0.201   0.321   Yes
  CEH34   C4   50   0.264   0.196   0.342   Yes
  NW10    C4   68   0.256   0.199   0.331   Yes
  CEH16   C5   51   0.284   0.237   0.398   Yes
  CEH17   C5   40   0.322   0.248   0.406   Yes
  CEH19   C5   40   0.337   0.278   0.422   Yes
  CEH31   C5   42   0.295   0.235   0.387   Yes
  NW9     C5   60   0.308   0.241   0.382   Yes
  ------- ---- ---- ------- ------- ------- -----

## **S4.2 Reproducibility**

The WTF specific yield estimates tabulated in Table S4.1 are computed by 17_wtf_specific_yield.py, which identifies qualifying monthly rising-limb events, applies the canopy interception correction for C4 wells, and exports per-well Sy statistics to 17_wtf_well_sy.csv. The spatial IDW interpolation of Sy values and the exclusion of CEH12 and CEH15 from the interpolation surface are implemented in 18_wtf_spatial.py, which generates the Sy map figure and exports the interpolated surface. Both scripts read intermediate data from the main pipeline (01_wells_clean.csv, 01_climate.csv, 01_locations.csv, 02_cluster_stats.csv) and are maintained in the canonical pipeline sequence.

# **Supplementary Note S5: Residual-Lag Test of the Ridge-Recharge Attribution**

## **S5.1 Purpose**

An earlier boundary-subsidy argument attributed a persistent water-balance residual at forest-margin wells --- most visibly a positive residual at CEH14 --- to lateral recharge derived from the northern rock ridge. It rested on two lines of evidence: a spatially structured pattern of positive residuals concentrated along the forest--dune boundary, and a closure argument that no other plausible flux could account for the monthly deficit. The corrected residual field (Script 20, 2026-08-06; §4.9.7, Figure 58) removes both. Sixty of the sixty-six reference wells now fall within ±0.01 m/month, the field shows no gradient on either axis, the three wells above +0.02 m/month all sit in the open dune, and CEH14 is the most negative well in the network at −0.011 m/month. The balance closes without requiring an additional flux. The residual-lag analysis described below was designed as an independent, falsifiable test of the transport mechanism and is retained as a bound on what the 21-year monthly record could have detected: if ridge-derived recharge is delivered as a time-varying pulse, then water travelling from the ridge to successive dune wells must arrive at those wells with travel times that increase as a function of distance. The time structure of the SSM residuals, cross-correlated against rainfall, should therefore carry a distance-dependent lag signature. This Note documents the test and reports the null result.

## **S5.2 Extended State-Space Model**

The single-period SSM fitted in Section 3.4.3 expresses the water table increment as a function of contemporaneous rainfall, where h_disp_prev(t) = DRAINAGE_DATUM + h(t−1) is the displacement above the 3.7 m drainage datum at the start of month t:

*Δh(t) = α + β₁·P(t) − β₂·PET(t) − β₃·h_disp_prev(t) + ε(t)*

A preliminary analysis (Script 22) demonstrated that the residuals ε(t) from this formulation carry a generic lag-1 rainfall signal at every well on the site, irrespective of cluster or position. This is the expected monthly-timestep consequence of the vadose zone: recharge takes approximately one month to propagate to the water table, so monthly-averaged water-table response lags monthly-averaged rainfall by roughly one month. This generic signal dominates the cross-correlation function at every well and masks any ridge-specific structure that might be present at longer lags.

To remove this confound, the residual-lag test uses an extended model that explicitly includes both P(t) and P(t−1) as regressors:

*Δh(t) = α + β₁₀·P(t) + β₁₁·P(t−1) − β₂·PET(t) − β₃·h_disp_prev(t) + ε′(t)*

The β₁₀ and β₁₁ coefficients absorb the vadose-zone response between them; any remaining lag structure in ε′(t) is therefore post-vadose and is the candidate ridge-transport signal. Fitted coefficients show that the extended parameterisation is only partly identified: β₁₁ is statistically significant (p \< 0.05) at 27 of the 64 wells, and its sign is mixed (negative at 33 wells, positive at 31), so the two rainfall terms do not partition the vadose-zone response cleanly at every well. The cluster-median lagged-response fraction β₁₁ / (β₁₀ + β₁₁) nonetheless rises across the open-dune-to-forest sequence, from −0.08 in C1 and −0.03 in C2 to +0.11 in C3 and +0.28 in C4 (C5 +0.16), consistent with the slower drainage of forest soils. Mean R² rises from 0.72 under the single-period model to 0.75 under the extended model across the same 64 wells. The extended model is used solely for this diagnostic test; the β₁, β₂, β₃ and α values reported in the main text remain the authoritative parameterisation for all other analyses.

## **S5.3 Cross-Correlation and Pre-Whitening**

For each well with at least 140 months of data (n = 64 after excluding CEH3, CEH4, CEH7, CEH8 and CEH37 for reasons noted below), the Pearson cross-correlation r(ε′(t), P(t − N)) was computed for lags N = 0 to 12 months. Prior to cross-correlation, both the rainfall and residual series were pre-whitened using a first-order autoregressive filter: x′(t) = x(t) − φ·x(t−1), where φ is the AR(1) coefficient of the rainfall series (+0.211 at RAF Valley). Wells whose residuals retained AR(1) structure above \|φ\| = 0.2 were additionally pre-whitened against their own residual autocorrelation before the common filter was applied. Statistical significance was evaluated using the Bartlett 95% confidence interval for a white-noise series, \|r\| ≥ 1.96/√N, which for typical series lengths gives a threshold of approximately 0.15.

Wells excluded from the test: CEH3 (tidal boundary --- outside the SSM operational domain), CEH4 (coastal erosion drift plus post-2017 clearfell drawdown confounding any lag signal), CEH7, CEH8, CEH37 (standard upstream exclusions carried over from §4.9.4). Wells beyond the 140-month minimum were retained without further filtering.

## **S5.4 Hypothesis Test**

The test metric is the Spearman rank correlation between each well's peak-correlation lag N\* and its Euclidean distance from the ridge reference point at (E = 241750, N = 364500, OSGB36) --- a representative coordinate for the nearest point of the northern rock ridge to the dune field. Under the ridge-transport hypothesis, Spearman ρ should be significantly positive.

Of 64 wells fitted, 51 had a peak cross-correlation that exceeded the Bartlett significance threshold. Across these 51 wells the peak lag has a mean of 2.67 months, a median of 2 months and a standard deviation of 2.29 months: 43 wells peak at lag 2, five at lag 3, and three at lags of 11 or 12 months with no systematic geographic pattern. The Spearman rank correlation between peak lag and ridge distance was ρ = +0.002 (p = 0.99) --- no distance structure whatever. Cluster mean peak lags are 2.00 months at C1 and C2, 3.00 at C3 and 3.67 at C4 (C5 has a single significant well, at lag 11). A Mann-Whitney comparison of the C4 ridge-adjacent wells against the C2 and C3 dune-body wells does return significantly longer lags at C4 (3.67 against 2.31 months; U = 233.0, p \< 0.005), but that ordering is a cluster-level contrast in drainage behaviour rather than a distance effect: within the network as a whole, lag is uncorrelated with ridge distance. The hypothesis of distance-dependent ridge transport is not supported.

The magnitude of coupling does not single out the ridge margin. Mean peak \|r\| among significant wells is highest at C1 (0.274) and C2 (0.224), and the ridge-adjacent C4 wells (0.179) are indistinguishable from the geologically separate C3 wells (0.181), with C5 lowest (0.138). At the individual wells previously highlighted, CEH14 peaks at r = +0.21, CEH34 at +0.20, CEH2 at +0.18 and CEH13 at +0.16, against NW10 at +0.19 and NW1 at +0.13 in C3 --- a spread too narrow to support a ridge-specific coupling signal. Neither the strength of rainfall coupling nor its timing is distance-structured.

## **S5.5 Interpretation**

The null distance-lag result does not rule out ridge-derived recharge. It rules out one specific form of it: event-driven, pulse-delivered transport in which monthly rainfall on the ridge propagates to the dune field with travel times that scale with distance. The alternative interpretation --- that ridge recharge is delivered as a near-steady baseflow, sufficiently smoothed by its transit through fractured bedrock that its month-to-month variance falls below the detection threshold of monthly water-level records --- is consistent with the null. A steady baseflow of this kind would manifest observationally as a constant positive contribution to the local water balance at wells along the flow path, which is precisely what the SSM residual α already absorbs. The two mechanisms are therefore not distinguishable from water-level data alone.

The discussion of the boundary subsidy in §5.2.1 has been adjusted to reflect this constraint: the ridge contribution is retained as a mechanism consistent with the data, but its form is characterised as steady-state rather than event-driven. Definitive resolution of the transport mechanism would require either a ridge-crest rain gauge paired with bedrock piezometers, or direct geochemical tracer work on the ridge--dune flow path. Both are identified as priority further work in §5.9.

## **S5.6 Reproducibility**

The residual-lag test is implemented in two standalone analysis scripts, 22_residual_lag_analysis.py and 23_ridge_recharge_lag_test.py, which are maintained as supplementary diagnostics (Phase 12) alongside the main pipeline to preserve the reproducibility of the headline results from the canonical pipeline sequence. Script 22 generates the residuals and AR(1) diagnostics; Script 23 fits the extended model, computes the cross-correlations, and applies the Spearman test. Both scripts read the same intermediate data produced by the main pipeline (01_wells_clean.csv, 01_climate.csv, 01_locations.csv, 02_cluster_stats.csv) and produce independent outputs under 22_residual_lag_analysis/ and 23_ridge_recharge_lag_test/ in the project outputs tree. A plain-text summary of the hypothesis test result is written to 23_05_hypothesis_test_summary.txt at runtime.

# **Supplementary Note S6: Seasonal Climatology Diagnostic of the Residual**

## **S6.1 Purpose**

Supplementary Note S5 reported a null result for the event-driven ridge-transport hypothesis. This Note addresses the other leading candidate mechanism for the water-balance residual: that the Thornthwaite PET estimate underestimates the true summer atmospheric demand on the water table because it is temperature-only and does not capture net radiation, vapour pressure deficit, wind, or surface-condition effects. Thornthwaite PET is an empirical index of atmospheric evaporative demand derived from temperature and day length; it does not define a specific reference surface. If that were the dominant explanation, the residuals should carry a systematic summer-negative signature that the fitted β₂ has not absorbed. This Note tests for that signature, along with two subsidiary diagnostics that distinguish between the remaining candidate explanations (steady ridge baseflow, nonlinear recharge response, and residual model error).

## **S6.2 Diagnostics**

Three complementary tests are computed from the residuals ε(t) produced by Script 22 for the same 64 wells that passed the ≥ 140-month record-length filter and the site-extent exclusions detailed in S5.3.

**(i) Seasonal climatology.** For each well, the monthly climatology of the residual is computed as the mean of ε(t) by calendar month over the record, giving a 12-point annual cycle. A sinusoidal fit ε(m) = a₀ + a₁·cos(2πm/12) + a₂·sin(2πm/12) yields an amplitude √(a₁² + a₂²) and a phase (month of peak). Summer-minus-winter magnitude (JJA mean − DJF mean) is reported as a robust non-parametric proxy for the same quantity.

**(ii) Independent ET proxy.** A correlation of the residual against PET itself would be trivially zero because OLS fitting makes residuals orthogonal to every regressor by construction. Instead, the residual is correlated against monthly sunshine hours from the RAF Valley record --- a direct radiation-based measurement that is not in the regression. If Thornthwaite underestimates summer ET in a way that β₂ has not absorbed, high-insolation months should carry disproportionately negative residuals, yielding a systematic negative Pearson r.

**(iii) Spatial pattern within clusters.** For C3 (Western-block open dune), the cluster is split by Euclidean distance from the ridge reference point used in S5 at a 1 km threshold (5 forest-adjacent wells, 13 warren-interior wells), and a Mann-Whitney test asks whether forest-adjacent wells have systematically smaller seasonal amplitudes than warren-interior wells --- as would be expected if a steady ridge baseflow were flattening the residual at ridge-proximal locations.

## **S6.3 Result: the ET Hypothesis Is Not Supported**

The sunshine-hours correlation is consistently negative in sign across every cluster, with network mean r = −0.026 and per-cluster means ranging from −0.001 (C4 Main Forest) to −0.058 (C1 Lake Edge). None of the 64 wells exceeds the Bartlett 95% significance threshold of \|r\| = 0.15 --- all 64 fall inside the null band. The sign is directionally consistent with Thornthwaite slightly underestimating radiation-driven ET, but the magnitude of the bias is below the resolution of the monthly water-level data to detect.

Summer-minus-winter residuals are negative in every cluster except C5, where the sign reverses to +0.003 m, with magnitudes of order −0.004 m (C2) to −0.008 m (C3). These values are an order of magnitude smaller than the month-to-month variability of the residuals themselves (typical well-level residual standard deviation of order 0.1 m) and should not be read as a summer-ET signal. Notably, C4 --- the cluster where canopy interception would most plausibly produce Thornthwaite miscalibration --- has the weakest sunshine correlation of any cluster, indicating that the cluster-mean β₂ has absorbed forest-specific ET behaviour reasonably well despite the simplicity of the fitted model.

The C3 within-cluster split also returns a null: forest-adjacent C3 wells (n = 7) have marginally smaller seasonal amplitudes than warren-interior wells (n = 10) --- 0.0099 m against 0.0101 m; Mann-Whitney U = 33.0, p = 0.44, alternative "adjacent \< interior". The direction is the one a steady-ridge-baseflow mechanism would predict, but the difference is a fifth of a millimetre and nowhere near significant, so it carries no evidential weight either way.

## **S6.4 What the Residuals Actually Look Like**

The per-cluster seasonal climatologies reveal a structure that fits none of the candidate mechanisms cleanly: the annual cycle is bimodal, with positive residuals in January--February AND June--July, and negative troughs in April--May and September--October. The sinusoidal fit captures this poorly, which is why the fitted amplitudes appear modest relative to the visible annual range. The fitted sinusoid peaks in late autumn or winter in every open-dune cluster --- C1, C2 and C3 all in December, C5 in November --- and later, in February, at C4, the shift at the forest cluster being consistent with its slower drainage. Across the network, 48 of the 64 wells peak between November and March and not one peaks in the May--August summer band.

This bimodal structure is not the signature of unmodelled summer ET, which would produce a single summer trough. It is not the signature of flat steady ridge baseflow, which would produce no annual cycle at all. And it is not a simple winter-recharge-nonlinearity signature, which would produce a single winter peak. Its most parsimonious interpretation is that a linear lumped-parameter model with time-invariant β coefficients is a rough approximation of a system whose soil-moisture storage operates nonlinearly across the annual cycle --- wet-winter saturation increasing recharge efficiency beyond what the cluster-mean β₁ represents, shoulder-season soil drying reducing it below, and the whole cycle modulated by seasonal variation in vegetation water use that a constant β₂ cannot track.

The spatial pattern of seasonal amplitude nonetheless shows a coherent structure: the two largest amplitudes in the network are CEH14 (0.040 m) and CEH13 (0.026 m), both C4 forest-margin wells, against a network median of order 0.010 m; C4 has the largest cluster-mean amplitude (0.015 m) of any cluster. The two fields do not coincide, however: CEH14 carries the most negative water-balance residual in the network (−0.011 m/month; Figure 58, §4.9.7), at the opposite end of that distribution from the three open-dune wells that lead it. The rest of the C4 cluster sits within the general network spread rather than standing out. The elevated seasonal variance at CEH14 and CEH13 is therefore not accompanied by an elevated water-balance residual, which weakens the reading that larger seasonal boundary fluxes are responsible and leaves the alternative --- that cluster-mean β values are a worse approximation at ridge-margin wells than at dune-interior wells --- as the better-supported of the two. Water-level data alone cannot settle it.

## **S6.5 Combined Conclusion from S5 and S6**

Taken together, Supplementary Notes S5 and S6 have excluded the two leading specific attributions of the water-balance residual:

The residual does not show the distance-dependent lag signature of event-driven ridge transport (S5).

The residual does not show the summer-negative signature of unmodelled Thornthwaite underestimation of atmospheric demand (S6).

The main text of §5.2.1 has been framed accordingly: the model explains 50--70% of month-to-month variance in Δh depending on cluster, and the unexplained portion is real and spatially structured (concentrated at the forest margin) but cannot be uniquely attributed to any single physical mechanism from water-level data alone. The fitted residual α remains the most defensible summary statistic for the steady-state boundary contribution; the underlying mechanism is most plausibly a combination of steady ridge baseflow, nonlinear soil-moisture storage dynamics not captured by the linear SSM, and minor β coefficient miscalibration, in proportions that cannot be resolved without additional measurement of the kind identified as priority further work in §5.9.

## **S6.6 Reproducibility**

This analysis is implemented in 24_residual_seasonality.py, which like Scripts 22 and 23 is maintained as a supplementary diagnostic (Phase 12) alongside the main pipeline to preserve the reproducibility of the headline results. The script reads the same intermediate data as Script 22 (01_wells_clean.csv, 01_climate.csv, 01_locations.csv, 02_cluster_stats.csv) plus the raw RAF Valley climate file for sunshine hours (RAF_Valley_Climate.csv). All outputs are written to 24_residual_seasonality/ in the project outputs tree: a per-well climatology table (24_residual_climatology.csv), the per-cluster climatology panels (24_01_climatology_panels_by_cluster.png), the spatial amplitude map (24_02_seasonal_amplitude_map.png), the sunshine-correlation scatter (24_03_sun_residual_correlation.png), the per-cluster phase distribution (24_04_phase_by_cluster.png), and a plain-text summary of the diagnostic result (24_05_diagnostic_summary.txt).

# **Supplementary Note S7: Equilibrium Wetness Index --- Per-Well Reconstruction**

## **S7.1 Per-Well Reconstruction**

The equilibrium wetness index (EWI) is the steady-state water-table level implied by each well\'s fitted state-space coefficients under long-term mean climate. Because its forcing is the long-term normal rather than a specific observation window, it is climate-window-independent and computable from a shorter record than the five-year mean spring level (MSL5) requires. Section 3.7.6 of the main report defines the index and its uncertainty; Section 4.8.6 reports its calibration onto the MSL5 scale and its cross-validation against the Ellenberg-F vegetation data. This note carries the full per-well reconstruction that Section 4.8.6 refers to.

The calibration is scoped to the open-dune network (clusters C1--C3, reference and extended wells). Of the 64 open-dune wells carrying an index, 62 also carry an observed MSL5 and set the calibration; the remaining two have no valid five-year spring window and are reconstructed only. The 20 forest wells (C4, C5) are reconstructed but held out of scope: their coefficients are the least constrained on the site, and the reconstruction there is too coarse to place a well across a Curreli et al. (2013) slack threshold. All 84 wells are listed, with the scoping carried explicitly in the Status column, so that the boundary of the calibration is visible rather than implied. CEH13 and CEH14 do not appear: the drainage coefficient is the denominator of the equilibrium expression and is near zero or negative at both, leaving the index undefined.

Standard errors propagate uncertainty in the fitted coefficients through the equilibrium expression. The variant tabulated here propagates the drainage coefficient alone, which is the dominant term because the equilibrium displacement is inversely proportional to it; a first-order propagation over all three coefficients is carried alongside it in the source CSV. The propagation is anchored on the equilibrium displacement rather than on the datum-referenced index value: subtracting the constant drainage datum shifts the value but not its uncertainty, and anchoring on the shifted value understates the error, severely so at wells whose equilibrium level sits close to the datum. These standard errors are substantially larger than the sampling error on a five-year MSL5 mean at every well, which is the basis for treating the index as a complement to MSL5 rather than a replacement for it.

**Table S7.**1. Equilibrium wetness index and MSL5 reconstruction, per well (n = 84). Levels are metres below ground surface, negative below the surface. The index is reconstructed from the open-dune calibration MSL5 = +0.295 + 0.918·EWI (r = 0.92, RMSE = 119 mm), fitted on the 62 in-scope wells carrying an observed five-year mean spring level. A further 2 open-dune well(s) carry an index but no valid five-year spring window and are reconstructed only; the 20 C4/C5 forest wells are reconstructed but held out of scope, their coefficients being the least constrained on the site. Status reads: \'Calibration\', an in-scope well that entered the fit; \'Reconstructed\', in scope but with no observed spring level; \'Out of scope\', a forest well outside the calibration\'s scope. Standard errors on the index propagate the drainage coefficient alone, the dominant term; the full three-coefficient variant is carried in 26_equilibrium_wetness_index_per_well.csv. Source: 26_equilibrium_wetness_index_per_well.csv, 26_ewi_msl5_comparison.csv.

  ------- ----------- ----------------------- -------- -------- ------ -------- -------- ------ ---------------
  CEH11   Reference   C1 (Lake Edge)          0.0920   -0.627   322    -0.350   -0.281   69     Calibration
  CEH23   Reference   C1 (Lake Edge)          0.0899   -0.527   360    -0.218   -0.189   29     Calibration
  CEH25   Reference   C1 (Lake Edge)          0.1341   -0.521   301    -0.301   -0.183   118    Calibration
  CEH26   Reference   C1 (Lake Edge)          0.0871   -0.493   360    -0.243   -0.157   86     Calibration
  CEH27   Reference   C1 (Lake Edge)          0.0992   -0.458   315    -0.172   -0.125   47     Calibration
  CEH5    Reference   C1 (Lake Edge)          0.0984   -0.512   314    -0.213   -0.175   38     Calibration
  CEH6    Reference   C1 (Lake Edge)          0.1223   -0.376   273    -0.088   -0.050   38     Calibration
  P2      Extended    C1 (Lake Edge)          0.0990   -0.473   364    -0.296   -0.139   157    Calibration
  CEH10   Reference   C2 (Dune)               0.1053   -1.372   341    -1.030   -0.965   65     Calibration
  CEH24   Reference   C2 (Dune)               0.0767   -0.429   451    0.033    -0.099   -132   Calibration
  CEH28   Reference   C2 (Dune)               0.0684   -0.609   517    -0.396   -0.264   131    Calibration
  D10     Reference   C2 (Dune)               0.0583   -0.461   485    -0.134   -0.128   6      Calibration
  D15     Reference   C2 (Dune)               0.0635   -0.403   437    0.079    -0.075   -154   Calibration
  D17     Reference   C2 (Dune)               0.0718   -0.426   508    -0.113   -0.096   16     Calibration
  D38     Reference   C2 (Dune)               0.1118   -0.738   274    -0.323   -0.382   -59    Calibration
  D41     Reference   C2 (Dune)               0.0670   -0.478   454    -0.127   -0.144   -17    Calibration
  D43     Reference   C2 (Dune)               0.0754   -0.659   343    -0.363   -0.310   53     Calibration
  D44     Reference   C2 (Dune)               0.0898   -0.739   404    -0.360   -0.383   -23    Calibration
  D5      Reference   C2 (Dune)               0.0698   -0.590   456    -0.179   -0.247   -68    Calibration
  D6      Reference   C2 (Dune)               0.0660   -0.577   449    -0.215   -0.234   -19    Calibration
  D7      Reference   C2 (Dune)               0.0787   -0.470   432    -0.161   -0.136   25     Calibration
  D8      Reference   C2 (Dune)               0.0561   -0.435   526    -0.109   -0.105   5      Calibration
  D9      Reference   C2 (Dune)               0.0624   -0.567   459    -0.237   -0.226   11     Calibration
  L7      Reference   C2 (Dune)               0.0859   -1.596   242    -1.240   -1.170   70     Calibration
  NW3     Reference   C2 (Dune)               0.0625   -0.593   541    -0.248   -0.249   -1     Calibration
  NW4     Reference   C2 (Dune)               0.0551   -0.441   573    -0.118   -0.110   8      Calibration
  NW4B    Reference   C2 (Dune)               0.0607   -0.470   553    -0.131   -0.137   -6     Calibration
  T41A    Reference   C2 (Dune)               0.1043   -0.477   350    0.226    -0.143   -369   Calibration
  T41B    Reference   C2 (Dune)               0.0649   -0.399   483    -0.159   -0.071   88     Calibration
  T41C    Reference   C2 (Dune)               0.0715   -0.434   399    -0.087   -0.104   -17    Calibration
  T41D    Reference   C2 (Dune)               0.0691   -0.659   426    -0.265   -0.310   -45    Calibration
  WMC1    Reference   C2 (Dune)               0.0564   -0.598   538    -0.259   -0.254   5      Calibration
  CEH12   Extended    C2 (Dune)               0.0849   -1.168   383             -0.777          Reconstructed
  CEH22   Extended    C2 (Dune)               0.0563   -0.657   237    -0.507   -0.308   198    Calibration
  CEH35   Extended    C2 (Dune)               0.0658   -0.760   389    -0.612   -0.402   210    Calibration
  CEH37   Extended    C2 (Dune)               0.0780   -0.542   349    -0.119   -0.202   -83    Calibration
  CEH7    Extended    C2 (Dune)               0.0478   -0.617   661    -0.196   -0.271   -75    Calibration
  CEH8    Extended    C2 (Dune)               0.0322   -0.572   510    -0.163   -0.230   -67    Calibration
  PW      Extended    C2 (Dune)               0.0702   -0.852   441    -0.579   -0.487   92     Calibration
  CEH1    Reference   C3 (Western Residual)   0.0660   -0.712   411    -0.237   -0.358   -121   Calibration
  CEH18   Reference   C3 (Western Residual)   0.0554   -1.006   518    -0.635   -0.628   7      Calibration
  CEH21   Reference   C3 (Western Residual)   0.0422   -1.150   419    -0.873   -0.761   112    Calibration
  CEH36   Reference   C3 (Western Residual)   0.0459   -0.744   488    -0.455   -0.388   67     Calibration
  CEH39   Reference   C3 (Western Residual)   0.0310   -0.484   792    -0.213   -0.149   64     Calibration
  CEH4    Reference   C3 (Western Residual)   0.0681   -0.857   301    -0.535   -0.491   44     Calibration
  CEH40   Reference   C3 (Western Residual)   0.0351   -0.623   850    -0.332   -0.277   55     Calibration
  CEH41   Reference   C3 (Western Residual)   0.0350   -0.479   829    -0.171   -0.145   26     Calibration
  CEH42   Reference   C3 (Western Residual)   0.0525   -0.510   511    -0.071   -0.173   -101   Calibration
  CEH9    Reference   C3 (Western Residual)   0.0330   -0.712   736    -0.451   -0.359   92     Calibration
  D25     Reference   C3 (Western Residual)   0.0645   -0.642   415    -0.210   -0.294   -84    Calibration
  NW1     Reference   C3 (Western Residual)   0.1112   -1.628   264    -1.037   -1.199   -163   Calibration
  NW11    Reference   C3 (Western Residual)   0.0778   -0.878   341    -0.371   -0.511   -139   Calibration
  NW13    Reference   C3 (Western Residual)   0.0879   -0.802   311    -0.431   -0.441   -10    Calibration
  NW2     Reference   C3 (Western Residual)   0.0937   -0.816   320    0.104    -0.454   -558   Calibration
  NW5     Reference   C3 (Western Residual)   0.0498   -0.735   590    -0.407   -0.380   27     Calibration
  NW6     Reference   C3 (Western Residual)   0.0530   -0.625   534    -0.221   -0.279   -57    Calibration
  NW7     Reference   C3 (Western Residual)   0.0413   -1.421   594    -1.000   -1.009   -9     Calibration
  WMC2    Reference   C3 (Western Residual)   0.0476   -0.623   534    -0.297   -0.277   20     Calibration
  WMC3    Reference   C3 (Western Residual)   0.0326   -1.347   746    -0.896   -0.942   -46    Calibration
  WMC4    Reference   C3 (Western Residual)   0.0881   -0.835   300    -0.478   -0.471   7      Calibration
  CEH38   Extended    C3 (Western Residual)   0.0555   -0.779   433    -0.599   -0.420   180    Calibration
  NW8B    Extended    C3 (Western Residual)   0.0594   -1.592   342    -1.205   -1.166   39     Calibration
  P1      Extended    C3 (Western Residual)   0.0431   -0.289   868             0.030           Reconstructed
  PE      Extended    C3 (Western Residual)   0.0506   -0.702   550    -0.465   -0.350   115    Calibration
  CEH2    Reference   C4 (Main Forest)        0.0233   -1.203   1089   -0.136   -0.809   -673   Out of scope
  CEH20   Reference   C4 (Main Forest)        0.0287   -1.295   843    -0.817   -0.893   -76    Out of scope
  CEH30   Reference   C4 (Main Forest)        0.0236   -1.666   950    -1.364   -1.234   130    Out of scope
  CEH32   Reference   C4 (Main Forest)        0.0122   -1.439   2304   -1.296   -1.026   270    Out of scope
  CEH33   Reference   C4 (Main Forest)        0.0195   -1.622   1223   -1.349   -1.194   156    Out of scope
  CEH34   Reference   C4 (Main Forest)        0.0079   -0.389   3273   -0.434   -0.062   372    Out of scope
  NW10    Reference   C4 (Main Forest)        0.0430   -1.020   593    -0.541   -0.641   -100   Out of scope
  CEH15   Extended    C4 (Main Forest)        0.0361   -1.308   527    -0.761   -0.906   -144   Out of scope
  FE1     Extended    C4 (Main Forest)        0.0141   -0.763   1499   -0.333   -0.406   -73    Out of scope
  LIS1    Extended    C4 (Main Forest)        0.0257   -0.904   1166   -0.383   -0.534   -151   Out of scope
  CEH16   Reference   C5 (Coastal Forest)     0.0372   -0.973   542    -0.645   -0.598   47     Out of scope
  CEH17   Reference   C5 (Coastal Forest)     0.0574   -2.201   320    -1.871   -1.725   146    Out of scope
  CEH19   Reference   C5 (Coastal Forest)     0.0443   -1.049   398    -0.681   -0.668   13     Out of scope
  CEH31   Reference   C5 (Coastal Forest)     0.0418   -1.611   603    -1.211   -1.184   28     Out of scope
  NW9     Reference   C5 (Coastal Forest)     0.0494   -0.932   429    -0.645   -0.560   85     Out of scope
  CEH3    Extended    C5 (Coastal Forest)     0.0554   -1.160   262    -1.071   -0.770   301    Out of scope
  FE2     Extended    C5 (Coastal Forest)     0.0455   -1.648   390    -1.281   -1.218   63     Out of scope
  FE3     Extended    C5 (Coastal Forest)     0.0603   -1.972   340    -1.666   -1.515   151    Out of scope
  FE4     Extended    C5 (Coastal Forest)     0.0475   -1.561   486    -1.193   -1.138   55     Out of scope
  NW8     Extended    C5 (Coastal Forest)     0.0516   -1.394   361    -1.311   -0.985   326    Out of scope
  ------- ----------- ----------------------- -------- -------- ------ -------- -------- ------ ---------------

## **S7.2 Reproducibility**

The equilibrium wetness index, its calibration onto the MSL5 scale, and this table are computed by 26_van_willegen_msl.py. Reference-tier coefficients are read from 03_master_data.csv (Script 03) and extended-tier coefficients are fitted in the same script using the shared state-space routine in utils/model_utils.py. The per-well index and its standard errors are exported to 26_equilibrium_wetness_index_per_well.csv, the observed-versus-reconstructed comparison to 26_ewi_msl5_comparison.csv, and the calibration constants to 26_report_numbers.csv. The table above is emitted directly from those outputs as 26_table_s7_1_ewi_per_well.csv rather than transcribed, so it cannot drift from them.

# **Supplementary Note S8: Spring-Mean (MAM) Seasonal Robustness Analysis**

## **S8.1 Purpose**

The site's ecologically framed BACI and coastal-gradient analyses use the annual summer minimum (Jun–Sep) as the response metric — the drought-stress quantity that determines dune-slack habitat viability. This note tests whether that choice drives the conclusions, by re-running the seasonal analyses on the annual spring mean (Mar–May, the season the Curreli ecological thresholds are defined on) as a second metric through identical code paths. Spring is added, never substituted: the summer minimum remains the headline. The spring mean carries the same N as the summer minimum (one value per well-year) and, being a three-month mean rather than an extreme-order statistic, is the less noisy of the two. The spring window and its strict 3-of-3 completeness rule are the config constants MSL_SPRING_MONTHS = (3, 4, 5) and MSL_MIN_MONTHS_PER_SPRING = 3, shared with the van Willegen MSL analyses (Methods Supplement F.4).

## **S8.2 Scraping Intervention (Script 09c)**

At the scraped well CEH36, the spring mean shifts post-scraping by +117 mm against the paired CEH4 control (p = 0.003) and +46 mm against the climate centroid (p = 0.54, not significant), versus +195 mm and +161 mm respectively for the summer minimum. Scraping raises the spring level too, by less than it raises the summer minimum, and the two controls — which agreed in summer — disagree in spring because every non-impact well also shifts negative against the climate centroid, the signature of the regional spring centroid itself having risen rather than of the impact wells falling. With n_pre = 4 years these p-values are fragile.

## **S8.3 Clearfell BACI (Scripts 10d, 10l)**

The clearfell tier-mean spring shifts against the Forest control (Script 10d) are Impact −15, Edge −101, Forest-control −9 and Climate-control −78 mm, none individually significant. The four-zone spring model (Script 10l; 14-year panel, R² = 0.57) returns the differential felling steps in Table S8.1. The Edge step (−46 mm, p = 0.011) is the only nominally significant spring BACI result and is not robust: it is distributed across all four Edge wells (it survives dropping any one, −36 to −58 mm) but is leveraged by a single pre-felling year — dropping 2011 collapses it to −11 mm (p = 0.36) — and is fitted with cluster-robust standard errors on very few clusters. It is reported for completeness, not as a felling effect. In summer the felling signal sits at the Impact zone; the spring branch does not reproduce a significant Impact step, consistent with the felling effect being a growing-season phenomenon. The spring panel spans 14 years (2011 + 2013–2025) against the summer panel's 13, because WMC3's Mar–May record is near-complete and 2019 — unusable in summer — is fully measured in spring, even under the stricter 3-of-3 rule.

Table S8.1. Four-zone differential felling step relative to the Forest control zone, spring mean versus summer minimum (Scripts 10l_06, 10l_01). Steps in mm; C3/Warren is the second control zone, expected near zero.

| Zone | Spring step ± SE (mm) | Spring p | Summer step ± SE (mm) | Summer p |
|---|---|---|---|---|
| Impact | −14.7 ± 11.4 | 0.196 | −7.3 ± 7.9 | 0.358 |
| Edge | −46.4 ± 18.2 | 0.011 | −28.6 ± 20.5 | 0.162 |
| C3/Warren | −9.7 ± 11.7 | 0.407 | +12.0 ± 10.6 | 0.257 |

## **S8.4 Cluster Trends and the Coastal Gradient (Scripts 14, 25)**

The spring-mean cluster-centroid trend (Script 14) is flat for every cluster except C5 Coastal Forest (−0.038 m yr⁻¹, p = 0.020); C1–C4 lie between −0.001 and +0.007 m yr⁻¹, none significant. The contrast with the summer minimum is the substantive result (Table S8.2, Figure S8.1): summer minima decline across every cluster (−9 to −36 mm yr⁻¹), but spring means are essentially stable inland — the inland summer-minimum decline is a growing-season phenomenon, not a fall in the baseline water table. C5 is the exception: it declines in both seasons (summer −35.9, spring −37.9 mm yr⁻¹), and applying the all-season coastal-retreat gradient (Script 25, Methods Supplement S.15) to the spring metric attributes about 41 % of C5's spring decline to coastal retreat (predicted gradient −15.4 mm yr⁻¹ on the constant −6.35 mm yr⁻¹ climate background, residual −16.1 mm yr⁻¹). This is direct corroboration that C5's decline is a year-round coastal-boundary effect rather than a drought-season artefact.

The full-panel season × δ(d)·t interaction test (Methods Supplement S.15) confirms this at the gradient level: on the forest-free panel (11,777 observations, one model) the spring modulation of the gradient drift rate is γ = +0.058 ± 0.048 (t = 1.20, p = 0.23) for the linear-capped form and +0.059 ± 0.048 (p = 0.22) for the exponential. The coastal-retreat drift is about 6 % steeper in spring as a point estimate but statistically indistinguishable from season-independent, so the same all-season gradient applies to both seasons. A MAM-only refit of the gradient panel (a sensitivity block in 25_01_panel_fit_parameters.csv) loses power as expected — the coast-edge anomaly δ₀ standard error roughly doubles (1.92 to 3.34 mm yr⁻¹) — but leaves the point estimates essentially unchanged (δ₀ −31.0 mm yr⁻¹, L 894 m).

Table S8.2. Observed cluster-centroid slope, summer minimum versus spring mean, with the spring-mean decomposition under the all-season forest-free linear-capped gradient (Scripts 25_08, 25_03_cluster_partition_spring). Slopes in mm yr⁻¹; the climate background is a constant −6.35 mm yr⁻¹.

| Cluster | Summer obs | Spring obs | Spring coastal gradient | Spring residual |
|---|---|---|---|---|
| C1 (Lake Edge) | −10.9 | +6.5 | 0.0 | +12.9 |
| C2 (Dune) | −11.2 | +0.3 | 0.0 | +6.7 |
| C3 (Western Residual) | −9.4 | −1.0 | −2.2 | +7.6 |
| C4 (Main Forest) | −17.8 | −1.2 | 0.0 | +5.2 |
| C5 (Coastal Forest) | −35.9 | −37.9 | −15.4 | −16.1 |

Figure S8.1 (25_08_spring_vs_summer_comparison.png) shows the observed centroid slope by cluster, summer minimum versus spring mean, with the all-season gradient marked. Figure S8.2 (14_climate_trajectory_spring.png) shows the observed spring-mean trajectories by cluster with per-cluster OLS trends.

## **S8.5 Conclusion**

The spring-mean analysis confirms the summer-minimum conclusions rather than revising them. Scraping raises spring levels as it does summer minima; the qualitative clearfell-BACI picture does not depend on the choice of summer minimum over spring mean; the inland summer-minimum decline is growing-season specific (spring flat); and — via the null interaction test and the year-round C5 signal — the coastal-retreat gradient is season-independent. The one nominally significant spring-only result, the Edge four-zone step, is not robust to a single pre-felling year and is not interpreted as a felling effect.

## **S8.6 Reproducibility**

Scripts 09c (v1.5.0), 10d (v1.7.0), 10l (v1.2.0), 14 (v1.4.x), 25 (v1.5.x). Every spring output is additive and the committed summer outputs reproduce byte-identically. The spring season and completeness rule are config.MSL_SPRING_MONTHS and config.MSL_MIN_MONTHS_PER_SPRING; the interaction test and MAM sensitivity are described in Methods Supplement S.15.
