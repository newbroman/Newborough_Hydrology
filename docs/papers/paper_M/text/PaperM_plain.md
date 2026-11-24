<!-- GENERATED MIRROR of docs/papers/paper_M/PaperM_plain_v1_13.odt — do not edit. source-sha256=a2d81611158fd0e2 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

What monthly water levels can tell us: a plain-language guide to the methods paper

M. Hollingham

November 2026

This guide explains, without equations, a scientific paper about how far a simple groundwater model fitted to monthly water levels can be trusted: *One model for a dune water table: what a monthly linear-reservoir model fitted to dipwell levels can forecast, and how far to trust it* (Hollingham, 2026). It follows the paper section by section, with the same section numbers. Every number in it is taken from the same project files as the paper, so the two always agree. Words in bold on first use are explained in the glossary at the end.

# []{#anchor}1. Why this matters

Dune slacks, the damp hollows between sand dunes, are among the richest wildlife habitats on the coast, and they depend on groundwater. How wet a slack is in spring and how far the water falls in summer decide which plants and animals can live there.

At most sites the only record of that groundwater is a set of shallow pipes, called **dipwells**, in which someone measures the water level by hand about once a month. Newborough Warren on Anglesey has 88 of them across 865 hectares of dunes and pine forest, and some have been read for over twenty years.

What managers most want from that record is a forecast: how the water table will respond to the coming years, and to a changing climate. The rain that soaks in, the water that drains away underground and the water drawn back up by plants and the sun are rarely measured at such sites, so the forecast comes from a simple model fitted to the water levels themselves.

The paper takes the standard model for the job and asks four questions. What can it forecast, and how far can it be trusted? Can the model of one well stand in for its neighbours? How many years of readings does it need? And can water levels alone say where the water goes: how much drains away underground and how much is taken by evaporation and plants? A forecast cannot be checked until the future arrives, so the paper checks what can be checked now: how the model does on recent years held back from the fit, and on old records from before the present wells were installed.

# []{#anchor}2. The model in one picture

## []{#anchor}The bath with a slow leak

Think of the ground as a bath with a slow leak. Each month:

-   **rain** tops it up;
-   **evaporation and plant use** draw water back out from the top;
-   **drainage** lets water leak away underground, faster when the water stands higher.

The model says exactly this, one month at a time, and predicts how far the water level will move. It has three numbers, worked out from the record at each well:

-   how much the water rises for each millimetre of rain;
-   how much it falls for each millimetre of evaporating power in the air;
-   how quickly it drains away, which the paper calls the **drainage coefficient**.

## []{#anchor}Where it comes from: Pastas

**Pastas** is widely used free software for exactly this job: it fits a well's record against rainfall and evaporation. It finds the level the water table rests at for itself, so it never needs to know where the water drains to. The paper's model, called **Model B**, is the Pastas model written one month at a time. Fitted to the same wells, the two agree well by well, with rank correlations of 1.00, 0.96 and 0.98 for the rain, evaporation and drainage numbers on 63 wells. That shows the code does what it should; it is not evidence that the model is right.

## []{#anchor}What the drainage number means

Because the model finds its own resting level, its drainage coefficient describes how quickly the water table goes back to its usual level after a wet or dry spell: the **return time**. It is a property of the record, not of any chosen floor. To keep drainage running the right way, the drainage number is not allowed to fall below zero.

Leaving drainage out altogether gives the simplest model of all, the **traditional linear model**: rain in, evaporation out, nothing else. Run forward on its own, it has nothing pulling the water table back towards a usual level, so each month's error is carried into every month after it.

## []{#anchor}How the model is tested

Every test is a **free run**: the numbers are fitted to a stretch of record, and the model is then run forward on the weather alone, working out each month from its own previous month and never from the readings. It is scored with the **forecast skill**, where 1 is perfect, 0 is no better than the well's average level and below 0 is worse. Three tests take the model outside the months it was fitted on: the modern record split at January 2018, fitted on one side and run across the other, both ways; the Countryside Council for Wales readings of 1989--96 at 9 wells, in a decade drier than anything in the modern record; and Derek Ranwell's readings of 1951--53 at three places on the Warren, whose positions are uncertain, so that only the seasonal rise and fall is scored.

# []{#anchor}3. The site, the record and the wells

Newborough Warren is a coastal dune system of 865 hectares. The 88 dipwells are read at the end of each month. Monthly rainfall and evaporating power come from one weather station, RAF Valley, 16 km away.

The study uses a reference network of 66 wells: those with at least 100 months of record that are still being read at the end of it. Their records are longer than that minimum, with a median of 192 months (from 140 to 252).

The wells fall into five groups that rise and fall together, found from the shape of their records before any model was fitted. Three groups are open dune (the Lake Edge, the Dune and the Western Residual) and two are under pine (the Main Forest and the Coastal Forest). The groups are stable when wells or months are left out at random, but groups built separately from two halves of the record agree only moderately (a score of 0.53 where 1 is identical). So they are a useful way of dividing one continuous aquifer, not sharply bounded units.

The numbers a study reports belong to the stretch of record they were fitted on, so the paper says which applies to every result. One basis is the average hydrograph of each group, fitted on every month available. The other is each well on its own, on its full record or on a common window, the same 98 months at every well, ending in February 2026, so that wells are compared under the same weather. A month when a well was dry still counts, as a level too low for the pipe to read. The tests that split the record fit each well on the years before January 2018 and test it on the years after.

# []{#anchor}4. How the model does

## []{#anchor}4.1 What the drainage term adds

At each well the traditional linear model and Model B were fitted on the common window and run freely over the same months. Across 64 wells the traditional linear model scores 0.38 at the median well, and at 11 wells it does worse than simply guessing the average. Adding the drainage term lifts the median to 0.83, positive at all 64 wells. A model without drainage cannot forecast.

## []{#anchor}4.2 Within the recorded climate

Fitted on the years before January 2018 and run freely over the years after, Model B's median skill is 0.79; run the other way round, 0.78. It does well in every group of wells but one: from 0.72 to 0.85 by group and direction. Under the main forest it fails, at 0.08 forward and 0.20 back. The felling of December 2017 beside the forest falls at the split, but it touches only a handful of wells and cannot explain the forest's failure, which is the same running back from numbers fitted after it.

## []{#anchor}4.3 How much record it needs

Less than you might expect for a forecast, more for the drainage number. Fitted on only 24 months before 2018, Model B's median skill is already 0.71, against 0.79 with all of them. Model B's drainage number itself settles, to within 20 % of its full-record value, only after 60 months at a typical well, which is 8.7 return times. Under the main forest it settles at only 6 wells, and only after 144 months.

## []{#anchor}4.4 The two hindcasts

A **hindcast** runs the model over past years, using today's numbers. The paper uses two kinds, and they do different jobs: the well-by-well hindcasts test the model; the hindcast of the whole warren uses it.

In the well-by-well hindcasts each well is run from 1930 on the RAF Valley weather with its own present-day numbers, and its levels are compared with the old readings, which no fit has seen. The early start just lets the model forget where it began. The question is whether today's ground, given that era's weather, reproduces the levels then recorded. For the dry decade of 1989--96 it does not quite: Model B puts the water table 0.18 metres too high at the median well. For Ranwell's seasons it does well, with a median skill of 0.83 at the three main sites and 0.67 over all eleven pairings with modern wells. The two results do not conflict: the seasons test scores the swing about the average, and the dry decade scores the average itself.

The warren hindcast shows how wet the open dune as a whole would have been under the weather of every month since 1930. One rule for the open dune is run from 1930, matched to the measured median of the wells over the years they were read, and turned into areas of open water and wet slack floor with two curves fitted to 43 Sentinel-2 satellite images. Because it is matched to the well record, it is a picture of the past, not evidence that the model is right.

## []{#anchor}4.5 Neighbouring wells

The wells fall into groups from the shape of their records alone, so a new well can be placed in a group by comparing its record with the group averages, without fitting it. Can it then borrow the group's numbers? Across the 2018 split the group's numbers score 0.80 forward against 0.79 for each well's own, and on Ranwell's seasons 0.84 against 0.83. Two years of readings put a new well in the right group at 62 % of wells, and three years at 76 %. Placed from two years and given its group's numbers, it forecasts at 0.76.

Where a well's own record has a gap, it is better filled from a measured neighbour than from any model. With stretches of 54 months hidden in turn, each well's average spring level was put back from its nearest neighbour in the same group with a typical miss of 0.041 metres, against 0.139 metres from a model run on the weather. The direct test, one well's model run month by month at its neighbour, has still to be run with Model B.

## []{#anchor}4.6 What the model lets you predict

For the coming years, any of the ways of using it will do: a well's own numbers or its group's, from its whole record or from two years of it. For another climate's seasons, a well's own numbers or its group's will do. For a lasting drier spell, none of them will: every way of using the model puts the 1989--96 water table too high, because the error comes from the model, not from the wells or the record.

## []{#anchor}4.7 A check that uses no model

The return time can be measured without the model. Take each month's level less the usual level for that calendar month, and ask how much of an unusual month is still there the month after. The model-free answer is a return time of 5.1 months at the median well, against Model B's 6.5, and group by group Model B sits with it: at the lake edge 2.1 months against 2.0 measured, and under the coastal forest 13.3 against 12.0. A short return time also means one spring's level says little about the next: the readings give a link of −0.11 between successive springs, on a scale where 0 means none. So the drainage number measures how quickly the water table recovers, not drainage to a real floor.

# []{#anchor}5. Where the model falls short

## []{#anchor}5.1 A drier climate

For the dry decade of 1989--96 the model puts the water table about a fifth of a metre too high. The model learns its resting level from the modern record, which includes recent wet years, and returns to it quickly, so a lastingly drier climate pulls the modelled level down less than the real one fell. A second, slower store was tried and did not pass the tests set before the fit. Two other explanations were checked and ruled out: the model's numbers held from then to now away from the felled ground, and a different way of calculating evaporation would make the model wetter still, not drier.

## []{#anchor}5.2 The main forest

Under the main forest the drainage number cannot be worked out from the record, so the forest is not projected and is reported as a range. The coastal forest, which is also pine, behaves normally, which points to the main forest's ground rather than its trees.

## []{#anchor}5.3 The resting level is not a real floor

The model's constant and its drainage number are almost interchangeable: their estimates correlate at 0.96 at the median well. So the level its drainage refers to is fitted rather than physical, and lies about 1.6 metres below ground at the median well. It describes the water level, not the bottom of the aquifer.

## []{#anchor}5.4 What the record projects

Under the Met Office's high-emissions climate scenario (UKCP18), the typical lasting fall of the summer water level is 0.20 metres in the 2050s, a climate about as much drier as the 1989--96 decade, so within what the hindcast has tested. In the 2080s it is 0.37 metres, under a climate drier than anything in the record. Because the model is too wet in a drier climate, these falls are likely to be too small, so each is quoted with a bound: 0.27 and 0.48 metres, from a version of the model with a fixed floor (Section 7). The main forest is not projected.

# []{#anchor}6. Where the water goes

Water levels alone cannot say how much of the water lost each month drains away underground and how much is taken by evaporation and plants, because the answer depends on the level drainage is measured from, and the model's level is fitted. One thing can be said without measuring anything: evaporation cannot take more than the weather asks for, and over this long a record the water stored has not drifted, so drainage must carry at least the rain left over. That is a floor on drainage, not a split.

The paper gives three readings. Model B itself puts drainage at 45 % of the loss at the median well. The seasons give a second, with no model at all: winter falls are nearly all drainage and summer falls are drainage and evaporation together, so their ratio is a drainage share. A water balance gives a third, using a storage figure measured from how far the water table rises after rain, the **apparent storage**, which is not a property of the sand alone: it puts drainage at 31 % at the median well, or 36--55 % with a second way of estimating the storage figure. The three agree on the dune and differ most in the west and in the coastal forest. Only a direct measurement of one of the flows would settle it.

Under the pine forest the trees catch part of the rain, which evaporates before it reaches the ground. The model already carries that loss, so it is counted inside the evaporation, not added on top. So counted, the main forest's total evaporation is 631 millimetres a year, 0.97 times what the weather asks for: within what the weather allows.

# []{#anchor}7. A fixed floor: tried, and not adopted

The obvious alternative is to fix the floor that drainage runs towards in advance, so that drainage runs to a real level: 3.7 metres below ground at every well, or each well's depth to the sea at mean high water, the one real drainage level that can be named. Neither was adopted. It forecast no better (0.61 and 0.46, against Model B's 0.79). Choosing the floor that fits best simply turns it into Model B. Its own results depend on where the floor is put, and nothing measured fixes that. And at one forest well, CEH14, it still gave drainage running the wrong way, and its forecast fell apart (a skill of −11.54, against 0.38 for Model B).

It keeps two jobs. It is a check: a result counts as a finding only if it holds with the fixed floor too, and several results that seemed to show what forest management does to drainage did not, so they are not reported. And it gives the bound on a drier climate, because its slower return carries a dry spell forward.

# []{#anchor}8. A checklist for other sites

For a site with a monthly water-level record and no direct measurement of where the water goes, the paper's procedure comes down to these steps.

1.  Fit the model with its own resting level (Model B, or Pastas) at the scale at which the results will be used: each well, or each group of wells that rise and fall together. Keep the drainage number from going below zero.
2.  Test what the drainage term adds. Run the model freely from the first observed level and compare it with the same model without drainage.
3.  Test forecasts within the record. Fit on one part and run freely over the other, in both directions.
4.  Test against a different climate wherever an older record exists, even a few wells or a few years, and check the level, not only the swing. Where the model fails, quote its error beside every projection, with a bound.
5.  Check the record is long enough. Refit on shorter stretches and see when the drainage number stops moving. The record should span several return times.
6.  Check the return time without a model.
7.  Treat the split of the loss between drainage and evaporation as something water levels cannot settle.
8.  Say which stretch of record every result comes from, let a new well borrow its group's numbers once a short record has placed it, and fill gaps from measured neighbours rather than from the model.

# []{#anchor}9. What the record cannot tell us

Within the recorded climate the tests agree: the model forecasts the water table, from a short record and on borrowed numbers. Beyond it only an old record can say, and here it says the level of a lastingly drier climate is overestimated. Someone forecasting next year's spring level can use the model as it is; someone projecting the 2080s should quote it with its error and its bound.

Four questions remain open. How does the loss split between drainage and evaporation? A measured flow would settle it. Where is the bottom of the aquifer that the water drains to? A mapped clay surface or an outlet level would fix it. Does one well's model work at its neighbour? That test is still to be run with Model B. And what matters for the plants: the level each month, or how long the water stays above some depth, or when the spring peak comes? The model should be scored on whatever that is.

The weather comes from one station outside the site, at monthly resolution, and the evaporation figure is an index of demand rather than a measured flow. The model is straight-line and unchanging in time, and the projections assume its numbers hold under a climate the record has not seen, which the look-back tests reach only as far as the 2050s. Under the main forest, Model B's drainage number cannot be worked out. A slow response is one reading of that, and a forcing that misrepresents the forest's evaporation is another, and the record does not tell them apart. The independent tests of the lasting response rest on 9 wells in one decade and three approximately placed sites in another.

# []{#anchor}10. In short

A model fitted to a monthly water-level record, the standard Pastas model written one month at a time, forecasts that record's water table: within the recorded climate it does so from two years of readings, and a new well can borrow its group's numbers. Its drainage number measures how fast the water table returns to its usual level, which a check that uses no model confirms.

Its main weakness is a lastingly drier climate, where it puts the water table about a fifth of a metre too high. At Newborough, under a high-emissions climate, it puts the typical fall of the summer water level at 0.20 metres in the 2050s and 0.37 metres in the 2080s, perhaps as much as 0.48 metres. The main forest is left out, because its drainage number cannot be worked out from the record. And water levels alone cannot say how much water drains away and how much evaporates: that needs a measurement.

# []{#anchor}Glossary

**Apparent storage.** How far the water table rises for a given amount of rain, measured from the record; it takes in the damp sand above the water table as well as the sand below it.

**Constant (intercept).** A fixed amount added to the model every month. Including it lets the model find its own resting level.

**Dipwell.** A shallow perforated pipe in which the water level is measured by hand.

**Drainage coefficient.** The model number that sets how quickly the water table returns to its usual level.

**Drainage share.** The part of the water lost each month that drains away underground rather than being taken by evaporation and plants.

**E-folding time.** The time a disturbance takes to shrink to about a third (more exactly 37 %) of its size.

**Fixed floor.** A version of the model with the level drainage runs towards set in advance; tested, not adopted, and kept as a check and a bound.

**Forecast skill (efficiency).** A score of how well a model's run matches the readings: 1 is perfect, 0 is no better than the average level, and below 0 is worse.

**Free run.** Running the model forward on the weather alone, never correcting it with the readings.

**Hindcast.** Running the model back over past years, to compare it with old readings or to picture the past.

**Model B.** The paper's model: Pastas's model written one month at a time, with a constant that lets it find its own resting level.

**Pastas.** Widely used free software for fitting a well's record against rainfall and evaporation.

**Return time.** The e-folding time with which the water table goes back to its usual level after a wet or dry spell.

**Traditional linear model.** The model with no drainage term: rain in, evaporation out, nothing pulling the level back.

# []{#anchor}Further reading

Hollingham, M. (2026) One model for a dune water table: what a monthly linear-reservoir model fitted to dipwell levels can forecast, and how far to trust it. In preparation.

Ranwell, D.S. (1959) Newborough Warren, Anglesey. I. The dune system and dune slack habitat. *Journal of Ecology* 47(3), 571--601.

The project's data, analysis and documents: https://github.com/newbroman/Newborough_Hydrology
