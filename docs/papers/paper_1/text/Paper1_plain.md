<!-- GENERATED MIRROR of docs/papers/paper_1/Paper1_plain_v1_1.odt — do not edit. source-sha256=64ba0e7bf5d29795 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

Reading the water table: a plain-language guide to the dune-aquifer paper

M. Hollingham

October 2026

This companion follows the paper and adds nothing to it; where the two seem to differ, the paper is right.

It explains, without equations, the paper *A parameter-sparse state-space framework for characterizing coastal dune-aquifer architecture from manual dipwell records* (Hollingham, 2026a). Every number in it is taken from the paper or its Supporting Information. Words in **bold** on first use are explained in the glossary at the end.

# []{#anchor}1. Why this matters

Dune slacks, the damp hollows between sand dunes, are among the habitats most sensitive to water in north-west Europe. The wet-slack and dry-slack plant communities that conservation cares about each occupy a band of summer water depth only a few tens of centimetres wide.

That water comes from underground. Below a certain level, the **water table**, the dune sand is soaked; to understand a slack you need to know how the sand fills with rain, holds it and lets it go.

The usual tool is a detailed computer model of underground flow, which needs to know how easily water moves through the sand (its **hydraulic conductivity**) and how deep the sand is, everywhere. Those are costly to measure in loose dune sand, and an earlier model of that kind at Newborough ran into exactly these difficulties.

Many dune sites already have something cheaper: pipes in which someone measures the water level by hand once a month, and a weather station nearby. The paper asks whether that routine record, on its own, is enough to work out how the dune aquifer is built and how it behaves, without drilling, pumping tests or a full flow model.

# []{#anchor}2. The site and the record

## []{#anchor}Where is it?

Newborough Warren lies at the south-western tip of Anglesey. The present dunes formed after storms in 1330, over land that had been farmed. A rocky ridge marks the northern edge of the study area, which covers about 865 hectares. Beneath the sand lie glacial deposits (**till**) that let water through only slowly, so they act as the bottom of the sand. There are no permanent streams. The water leaves underground, mainly to the sea along Caernarfon Bay and the Menai Strait, and locally to Llyn Rhos-Ddu, a small lake that the groundwater feeds all year.

The northern part of the site is a Corsican pine plantation. Here the forest matters only for what its canopy does to the rain. The effects of felling part of it, and of scraping some dunes back to bare sand, are the subject of a companion paper (Hollingham, 2026b).

## []{#anchor}What was measured?

A **dipwell** is a narrow pipe with holes in it, pushed into the sand so that water can enter. To read it, you lower a tape until it touches the water. Newborough has 88 of them, read at the end of each month over 21 years. The 66 with long enough records are used to fit the model; the other 22, with shorter records, are placed into groups by how closely their ups and downs match.

Rain and temperature come from the RAF Valley weather station. Rain averaged about 891 mm a year. The drying power of the air, worked out from temperature (the **potential evapotranspiration**, or evaporative demand), averaged about 652 mm. So there is more rain than evaporation over a year, but not in summer, when the demand on the water table comes just as the rain is least. From year to year it is the rain that varies; evaporative demand changes little. Summers since 2013 have been warmer than before.

# []{#anchor}3. Five kinds of well

## []{#anchor}How were the groups found?

Before any model was fitted, the wells were sorted by the *shape* of their record: when the water rises and falls and by how much, ignoring whether a well is on high or low ground. Wells whose water goes up and down together count as alike. A standard sorting method (**hierarchical clustering**) gathered them into five groups, or **clusters**:

-   **C1 Lake Edge** (7 wells), in the east beside Llyn Rhos-Ddu: quick to rise and quick to drain to the lake.
-   **C2 Dune** (19 wells): the typical open dune, responsive but with no direct link to the lake.
-   **C3 Western Residual** (26 wells): open dune on deeper sand in the south-west, slower and more cushioned.
-   **C4 Main Forest** (9 wells): under the pines on the higher ground beside the ridge.
-   **C5 Coastal Forest** (5 wells): also under the pines, on the low ground nearer the coast.

The biggest division separates the Main Forest from everything else. The next splits the lively east (Lake Edge and Dune) from the cushioned west (Western Residual and Coastal Forest). So the Coastal Forest groups with the western dune, despite sharing the Main Forest's trees. This matches earlier work on the ground beneath: shallow sand over till in the east, deep wind-blown sand in the south-west.

## []{#anchor}Are the boundaries sharp?

No. A second check, comparing each well with the typical record of every group, supports the grouping of 60 of the 66 wells. Many wells resemble two neighbouring groups almost equally, as you would expect in one continuous body of sand. The Western Residual is the most blurred, and the paper reads it as the more cushioned south-western continuation of the open dune rather than a separate block.

# []{#anchor}4. The model in one picture

## []{#anchor}Rain in, evaporation out, drainage out

Think of the sand as a bath with a slow leak. Each month **rain** tops it up, **evaporation and plant use** draw water back out from the top, and **drainage** lets water leak away sideways underground, faster when the water stands higher. The model fitted at each well (a **state-space model**) says exactly this, one month at a time. It has three numbers, worked out from the record:

-   how far the water table rises for each millimetre of rain (the **recharge sensitivity**);
-   how far it falls for each millimetre of evaporative demand (the **atmospheric draw**);
-   what fraction of the water standing above a chosen depth drains away each month (the **drainage coefficient**).

It needs nothing but monthly rain and temperature from one station. Nobody has to measure the sand.

## []{#anchor}The imaginary floor

Drainage needs something to drain *towards*. The model assumes an imaginary floor, the **datum**, at a fixed depth below ground: the higher the water stands above it, the faster it drains. The study uses 3.7 m below ground at every well. This is a modelling choice, not a measured base, and the numbers are reported for that choice. A sister paper (Hollingham, 2026c) tried many depths and explains this one. Some results depend on it and some do not (Section 9).

## []{#anchor}What the numbers say

**Rain.** The Lake Edge responds most. About 22--26 mm of rain lifts the water table by 100 mm at the Lake Edge and Dune, but 40--41 mm under the pines: nearly twice as much rain for the same rise, consistent with the canopy catching part of it.

**Evaporation.** Atmospheric draw is highest in the Main Forest, where the water table loses slightly more per millimetre of evaporative demand than it gains per millimetre of rain, and lowest at the Lake Edge. The Coastal Forest, under the same trees, has less than half the Main Forest's draw.

**Drainage.** The strongest contrast of all: fastest at the Lake Edge, where the lake takes water quickly, similar in the Dune and Western Residual, slower in the Coastal Forest and slowest in the Main Forest.

## []{#anchor}Is it the trees or the ground?

The canopy is not the same everywhere. Measured from aerial photographs within 30 m of each forest well, its density varies widely from well to well. Yet it does not explain why the forest wells differ, and the Main Forest and Coastal Forest wells have much the same canopy. Height above sea level explains 98% of the difference in atmospheric draw between them: higher wells lose more. The paper reads this as the effect of a deeper water table under a thicker, drier layer of sand, and earlier measurements in the plantation (Freeman, 2008) found the water table about 1.07 m deeper than on the open Warren and the soil about half as moist. So the split between the two forest groups is best read as a difference of height and ground beneath one canopy. The ground under the plantation has not been drilled, so this rests on the shape of the land and the model's numbers.

# []{#anchor}5. Is the ground different under the forest?

## []{#anchor}How much water does the sand hold?

When the water table falls by a metre, only part of that metre was water; the rest was sand grains. The share that drains out as the water table falls is the **specific yield**. Sand with a higher specific yield needs more rain to raise its water table.

The paper estimates it simply (the **water-table-fluctuation method**): in months when the water rose, compare the rain that soaked in with how far the water rose. With monthly readings this tends to overestimate, so the results are treated as upper limits.

## []{#anchor}The forest puzzle

Taken at face value, the forest wells seem to hold as much water as the wettest open dune, or more. But the method assumes all the rain reaches the ground, and under pine it does not: the canopy catches about a quarter of it (24%, from the one measurement made in the plantation). Allowing for that, the Main Forest's specific yield falls within the open-dune range. The Coastal Forest's sits just above the top of that range, but it is the least reliable estimate in the network, pressed against the limit of what the sand could physically hold, so the paper gives it little weight. Trying other values for the canopy's catch, the Main Forest result holds; the Coastal Forest result does not.

## []{#anchor}What follows

Mapped across the site, specific yield changes smoothly, with no step at the edges of the groups; in the open dune it rises steadily towards the south-west. The paper's reading, consistent with the evidence but not proven, is that the forest wells behave differently mainly because the canopy catches rain at the surface, not because the sand beneath is different.

# []{#anchor}6. Where the water goes

## []{#anchor}Does the account balance?

The three numbers give a monthly budget for each group: rain in, evaporation and drainage out. Over the record the two sides agree to within 1.8% at every group, with no hidden extra source needed. The paper notes that this is partly built in, since a model fitted to water levels can be expected to balance on average; what it shows is that three terms are enough.

At individual wells the leftover (the **water-balance residual**) is small and shows no pattern across the site. Tests for water seeping in from the ridge, and for missing summer evaporation, found nothing. But monthly readings are too coarse to catch quick seepage through cracked rock, so the ridge test limits what this record can see rather than ruling it out. The leftover does have a seasonal rhythm, highest in winter and spring, which the paper leaves unexplained.

## []{#anchor}Drainage or evaporation?

With the floor at 3.7 m, drainage takes 85% of the water lost at the Lake Edge but only 24% in the Main Forest, where evaporation and the trees take most of it. This split depends on where the floor is put and cannot be read from water levels alone. Moving the floor from the shallowest workable depth to 8 m, the drainage share runs from 73% to 89% at the Lake Edge and from 4% to 28% in the Main Forest. The order of the groups never changes.

## []{#anchor}How quickly does it drain?

One measure is the time the water above the floor takes to halve under drainage alone, the **half-life**: typically 8.0 months at the Lake Edge and 23.0 months in the Main Forest, with the others between. The order holds at every floor depth tested, but the values grow as the floor is set deeper.

The half-life is not the time the water table takes to settle back after a wet or dry spell. Measured straight from the readings, with no model, it is shorter: a wet or dry spell shrinks to about a third of its size in 2.0 months at the Lake Edge, 4.1 in the Dune, 6.3 in the Western Residual, 12.0 in the Coastal Forest and 15.6 in the Main Forest. The gap is widest in the open dune and narrowest in the Coastal Forest. The two describe different things.

# []{#anchor}7. How well does it forecast?

The fair test is to give a model only the weather and the first reading, and let it run month after month without seeing the real levels, so that a weak model drifts away. The paper compared its model with a simpler one with rain and evaporation but no drainage. On a scale where 1 is perfect and 0 is no better than always guessing the average (the **Nash--Sutcliffe efficiency**), the typical well scores 0.42 with the simpler model and 0.77 with drainage added. The full model beats the average at 65 of the 66 wells, the simpler one at 55. Drainage stops the drift by pulling the water table back towards a normal level.

The gain is largest at the Lake Edge, where drainage is strongest, and smallest in the Main Forest, where it is weakest. So a map of where the drainage term helps is a map of where drainage controls the aquifer, drawn without drilling a hole.

The model also held up far outside the years it learned from. Driven by the station's weather back to 1930, with no refitting, it reproduced the seasonal rise and fall that the ecologist D.S. Ranwell recorded in three pipes in 1951--53 (correlations of 0.74--0.91, and the seasonal range to within a tenth of a metre).

# []{#anchor}8. The retreating coast

## []{#anchor}Why a shrinking shore lowers the water table

The western shore, along Caernarfon Bay, is eroding. The sea edge is where the groundwater drains out, so as it moves inland the water table near it is drawn down, a little more each year, quite apart from the weather. The effect should be strongest near the shore and fade inland.

## []{#anchor}What the record shows

The paper compared each open-dune well's long-term trend in its summer low with its distance from the shore. At 150 m from the shore the summer low has been falling by roughly 26 mm a year more than far inland, and the effect fades to nothing over about 900 m (at most about 1 km under other assumptions). The result is the same whether forest wells are included, left out or allowed for, so it is not the plantation's doing.

A check needing no model points the same way. Between a well near the shore and one beyond the reach, the difference in spring level has grown by 27.8 mm a year, close to the modelled figure. A gap that widens over time is what a moving shore produces, rather than a fixed difference in the ground or a swing in the weather.

## []{#anchor}Which groups does it touch?

The coast accounts for about half of the summer decline in the Coastal Forest, the group nearest the shore and falling more than twice as fast as any other. It accounts for most of the smaller decline in the Western Residual, half of whose wells lie within the reach. In the Main Forest, three of whose four wells lie within the reach, it accounts for about three-quarters of a small decline that the record does not measure firmly. It touches the Lake Edge negligibly and the Dune not at all.

The Coastal Forest share is an indication, not a measured fraction: few wells lie near the shore, and the share shifts with which wells the group contains. The maturing canopy may also contribute there; the record cannot separate it, and the paper leaves that open.

## []{#anchor}And climate?

Removing the coastal effect does not leave a clean climate figure: the part of the trend common to the whole site shifts a lot with the years chosen, so the paper gives no climate rate. But the coastal effect must be taken out first, or it will be mistaken for a site-wide decline. At the Lake Edge and in the Dune, beyond the coast's reach, the model leaves the whole of the summer decline unexplained, and climate is the leading candidate for it. Warmer summers raising evaporative demand and a change in how rain falls within the month are both possible routes; the paper does not settle which dominates.

Two further points. Rising sea level, about 4 mm a year, pushes the water table near the coast the other way, so the coastal figure is the net of the two and a cautious estimate of the erosion effect. And against Ranwell's readings, the open slacks beyond the coastal reach stand today within about a decimetre of their mid-century level once the weather of the two periods is allowed for: a dip within a near-steady century, not part of a long fall.

# []{#anchor}9. What the method cannot tell

-   **Where the floor is.** The drainage number, the half-life and the drainage--evaporation split depend on the chosen floor; the order of the groups does not. Fitting the record best does not find the real floor, because the best-fitting depth simply follows each well's usual water depth.
-   **How water moves between groups.** The model is fitted well by well and joined up on a map. It cannot say whether a change in one place would be felt in another; that needs a full flow model and the measurements behind it.
-   **Exact amounts.** The numbers are reliable for ranking places, less so as exact rates. Turning them into millimetres of water needs the specific yield, known only as an upper limit, and an evaporative demand worked out from temperature, whose absolute size is uncertain.
-   **The forest's reach.** One map shows how far the forest's effect might spread into the open dune. It alone needs a value for how easily water moves through the sand, from a single test, so it is an order-of-magnitude illustration.
-   **What lies beneath.** The ground under the forest has not been drilled, and drainage lines traced from the land surface are no guide to where the groundwater flows.

# []{#anchor}10. The questions people will ask

## []{#anchor}Is the forest drying the dunes?

The paper reads the forest's different behaviour as a surface effect, the canopy catching rain, not a different kind of ground. How far that effect spreads into the open dune is shown only as an illustration, and what felling did is for the companion paper.

## []{#anchor}Is it climate change or the coast?

Both, in different places. Near the western shore the retreating coast accounts for about half the summer decline in the Coastal Forest and most of it in the Western Residual. Away from it, the decline is left unexplained by the model; climate is the leading candidate, but no climate rate is measured. Against Ranwell's mid-century readings, the open slacks are close to where they were.

## []{#anchor}Can the method replace boreholes?

For a first picture of how an aquifer is built and behaves, it goes a long way without them. It cannot answer questions about sideways flow between parts of the site. The paper names the next measurements: tests of how easily water moves through the sand at representative wells in each group, and a radar survey of how deep the sand is.

# []{#anchor}11. Using the method elsewhere

Any coastal dune with hand-read dipwells and a nearby weather station can be treated the same way:

1.  Sort the wells into groups by the shape of their records, before fitting anything.
2.  Try the floor at many depths and choose one where the water budget stops changing. Do not reuse 3.7 m: the right depth follows the site's own water levels.
3.  Fit the three-number model at each well and each group.
4.  Run it freely against a model without drainage; where drainage helps most is where drainage governs.
5.  Estimate specific yield from the rises, allowing for any canopy, as an upper limit.
6.  Where a shore is eroding, fit the trend against distance from it and remove that before reading anything about climate.

# []{#anchor}Glossary

**Aquifer.** The soaked sand below the water table.

**Atmospheric draw.** How far the water table falls for each millimetre of evaporative demand.

**Datum (floor).** The imaginary depth below ground that the model assumes water drains towards.

**Dipwell.** A narrow perforated pipe in which the water level is measured by hand with a tape.

**Drainage coefficient.** The fraction of the water above the datum that drains away each month.

**Half-life.** The time the water above the datum takes to halve under drainage alone; it depends on the datum.

**Hydraulic conductivity.** How easily water moves through the sand. The method does not need it.

**Nash--Sutcliffe efficiency.** A score of how well a model's free run matches the readings: 1 is perfect, 0 is no better than the average level.

**Potential evapotranspiration (evaporative demand).** The drying power of the air in a month, worked out here from temperature.

**Recharge sensitivity.** How far the water table rises for each millimetre of rain.

**Specific yield.** The share of the sand's volume that drains out as the water table falls.

**Till.** Glacial deposits beneath the sand that let water through only slowly.

**Water-balance residual.** What is left over when modelled losses are set against modelled input.

**Water-table-fluctuation method.** Estimating specific yield by comparing the rain that soaked in with how far the water table rose.

# []{#anchor}Further reading

Hollingham, M. (2026a) A parameter-sparse state-space framework for characterizing coastal dune-aquifer architecture from manual dipwell records. In preparation.

Hollingham, M. (2026b) Companion paper on the dune scraping and partial clearfell at Newborough Warren. In preparation.

Hollingham, M. (2026c) Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you. In preparation.

Ranwell, D.S. (1959) Newborough Warren, Anglesey. *Journal of Ecology*.

The project's data, analysis and documents: https://github.com/newbroman/Newborough_Hydrology
