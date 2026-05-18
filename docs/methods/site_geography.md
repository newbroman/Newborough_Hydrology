# Newborough Warren — Site Geography Reference

## Location

Newborough Warren occupies the south-western tip of the Isle of Anglesey in north-west Wales (National Grid Reference SH 406 636). The site comprises approximately 1,300 hectares of late-glacial blown sand resting on weakly permeable glacial till, with a Carboniferous limestone and shale bedrock ridge forming the dominant boundary condition along the site's western and north-western edge.

## Coastline and Sea Boundaries

The site is bounded by sea on three sides:

- **Southern coast** — Caernarfon Bay, approximately N 362350. Low ground (<2 m AOD) across the full width; full-width zero-head anchors apply.
- **Eastern coast** — Menai Strait, approximately E 243850. Elevation 1–5 m AOD throughout (N 362500–365300). The Strait runs the full eastern flank from south to north.
- **Western coast** — open water (estuary) only below approximately N 363400, where the bedrock ridge meets the sea. North of that point the ridge replaces the sea as the western boundary.
- **Northern edge** — Malltraeth estuary lies beyond the northern dune edge. No zero-head anchors are needed here; the ridge is the dominant boundary.

Groundwater discharges across the foreshore as tides recede.

## The Bedrock Ridge

### Geometry

The ridge is a **linear NNW–SSE feature** running along the **western edge** of the site. It is not a central feature and not L-shaped.

Key facts from DEM analysis (newborough_dem.tif, 2 m resolution, EPSG:27700):

- Ground elevation >20 m AOD is confined almost entirely to E 240000–241000.
- Ground elevation >30 m AOD is west of E 241000, north of N 364200.
- Maximum elevation ~53 m AOD in the northwest corner.
- The ridge's eastern toe (where high ground meets the dune system) runs from approximately (243000, 363700) in the south to (241800, 364400) in the north — a NNW–SSE line.
- The dune system lies to the east and south of this line.

At E 240200 the elevation profile climbs from below sea level south of N 363300 (estuary), to 6 m at N 363500, 17 m at N 363900, and 36–45 m by N 364500. The ridge meets the sea at its southern end around N 363400–363500 on the western flank.

A separate, lower **coastal dune crest** (15–27 m AOD) sits at N 362400–362900, E 241500–242200. These are the seaward dunes, not the bedrock ridge.

### Groundwater Significance

The ridge is the **dominant boundary condition** for the entire aquifer. It forms a hydrological divide: dune systems on its northern flank, draining toward the Malltraeth estuary, are geologically and hydraulically separate from the study area and are excluded from all analyses.

Lateral recharge descending from the ridge contributes boundary subsidies, most pronounced at C4 Forest wells closest to the ridge crest. CEH14 sits at the ridge crest (~14.4 m AOD ground elevation, ~13.3 m AOD mean head) and carries the largest persistent boundary subsidy (α = +0.222 m/month). Ridge-derived lateral recharge is the primary sustaining mechanism for the Forest cluster.

Any land management that interrupts ridge-to-site lateral flow — including vegetation clearance on ridge slopes — poses a greater long-term hydrological risk than any management of within-site land cover.

## Eastern Block vs Western Block

The Eastern and Western blocks are distinguished by a **subsurface till-and-sand contrast** — not by the ridge.

- **Eastern Block (C1, C2)** — underlain by shallow till and estuarine deposits. A thin, storage-limited aquifer with a flashy, responsive water table. LCSC values of 63.9% (C1) and 59.7% (C2); high β₁ (1.565, 1.674). Consistent with a fill-and-spill mechanism where shallow till promotes surface ponding and rapid lateral overflow.
- **Western Block (C3)** — occupies deep, clean aeolian sand. A capacious, buffered aquifer with attenuated seasonal fluctuations. LCSC = 83.3%; β₁ = 1.201. The deep unsaturated sand buffer attenuates the rainfall-to-water-table transfer.
- **Forest (C4)** — shares the same deep sandy substrate as C3 but segregates into its own hydrogeological unit due to canopy interception by the Corsican pine plantation. LCSC = 104.5%; β₁ = 0.957 (anomalously low, reflecting interception not additional aquifer depth). Sits in the northern part of the site, closest to the ridge, which is why C4 wells receive the largest ridge-derived lateral recharge.
- **Coastal (C5)** — south-western margin. Tidal exchange rather than gravity drainage governs baseline recession. β₃ = 0.017 (non-significant).
- **Lake (C6)** — Llyn Rhos-Ddu. Near-permanent surface water; treated as a fixed-head boundary.

## Llyn Rhos-Ddu

A small lake acting as a near-fixed head body, receiving groundwater in winter and recharging the aquifer during drier months. C1 (Eastern Block Lake-buffer) wells are hydraulically connected to the lake.

## The Corsican Pine Plantation

The northern ~700 ha were afforested with Corsican pine (*Pinus nigra* var. *laricio*) between 1948 and 1965. An experimental clearfell of approximately 8.4 ha was completed in December 2017 at the plantation–open dune transition. Natural slack conditions — including winter flooding — existed within the forest footprint before afforestation, as documented by Ranwell (1959) and Hill and Wallace (1989).

## Key Spatial Reference Constants (OSGB36)

| Constant | Value | Description |
|---|---|---|
| SEA_SOUTH_N | 362350 | Southern shoreline Northing |
| SEA_EAST_E | 243850 | Eastern shoreline Easting (Menai Strait) |
| SEA_WEST_E | 239200 | Western estuary Easting |
| SEA_WEST_N_MAX | 363400 | Northern limit for western anchors (ridge begins) |
| SEA_EAST_N_MAX | 365400 | Northern limit for eastern anchors (full flank) |
| SEA_ANCHOR_SPACING | 200 | Spacing of boundary anchor points (m) |
| GRID_RES | 50 | Computational grid resolution (m) |

## Climate Reference

Meteorological data from RAF Valley, approximately 16 km from the site. Mean annual rainfall 856 mm (full record 1930–2026); 890 mm (monitoring period 2005–2026). Monthly monitoring interval aligned with RAF Valley precipitation record.
