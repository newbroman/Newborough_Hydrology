<!-- GENERATED MIRROR of docs/papers/paper_M/PaperM_plain_v1_7.odt — do not edit. source-sha256=f6e040bfebc77505 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

What monthly water levels can tell us: a plain-language guide to the methods paper

M. Hollingham

November 2026

This guide explains, without equations, a scientific paper about whether a simple groundwater model fitted to monthly water levels can be trusted to forecast: *Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you* (Hollingham, 2026). It follows the paper section by section, with the same section numbers. Every number in it is taken from the same project files as the paper, so the two always agree. Words in **bold** on first use are explained in the glossary at the end.

# []{#anchor}1. Why this matters

Dune slacks, the damp hollows between sand dunes, are among the richest wildlife habitats on the coast, and they depend on groundwater. How wet a slack is in spring and how far the water falls in summer decide which plants and animals can live there.

At most sites the only record of that groundwater is a set of shallow pipes, called **dipwells**, in which someone measures the water level by hand about once a month. Newborough Warren on Anglesey has 88 of them across 865 hectares of dunes and pine forest, and some have been read for over twenty years.

What managers most want from that record is a forecast: how the water table will respond to the coming years, and to a changing climate. The rain that soaks in, the water that drains away underground and the water drawn back up by plants and the sun are rarely measured at such sites, so the forecast comes from a simple model fitted to the water levels themselves.

That model can be fitted in two common ways, and which one was used is seldom reported. The choice changes what the model's main number means, and how the model behaves when it is run forward. A forecast cannot be checked until the future arrives, so the paper checks what can be checked now: how each version does on recent years held back from the fit, and how each does on old records from a drier climate than the one it was fitted on. It asks what a model like this can be trusted to forecast.

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

## []{#anchor}The floor, and two versions of the model

Drainage has to be measured from somewhere. The model takes it to run faster the higher the water stands above an imaginary floor, the **datum**, at a fixed depth below the ground. There are two ways to deal with that floor.

-   In **Model A** the floor is chosen in advance. The study uses a single depth of 3.7 metres for every well.
-   In **Model B** the model adds a constant to the sum and so finds its own floor, wherever the record puts it.

The two are one model family, separated only by where the floor comes from: Model B is Model A with the floor moved to the level at which the fitted drainage is zero.

The drainage coefficient means something different in each. In Model A it describes water draining towards the chosen floor, so its value changes if the floor is moved. In Model B it describes how quickly the water table returns to its own normal level after a wet or dry spell, and that does not depend on any floor.

Leaving drainage out altogether gives the simplest model of all, the **traditional linear model**: rain in, evaporation out, nothing else. Run forward on its own, it has nothing pulling the water table back towards a usual level, so each month's error is carried into every month after it.

## []{#anchor}A check against widely used software

Pastas is widely used software that does the same job. Model B is exactly what Pastas fits, written one month at a time, so when the two agree that shows the code is right. It is not independent evidence that either version is right. Model A has no match in Pastas, which has no fixed floor.

## []{#anchor}What neither version can decide

The water table loses water in two ways: by drainage, and by evaporation and plant use. The levels alone cannot say how the loss splits between them, because the split depends on the level that drainage is measured from. Model A sets that level by assumption and Model B by fit. Without a direct measurement of drainage, evaporation or recharge, neither can fix the true split. One thing can be said without measuring anything. Evaporation and plant use cannot take more water than the weather asks for, and over a record this long the water stored underground has not drifted up or down, so drainage must carry at least the rain left over once that demand is met. That is a minimum for drainage, whichever version of the model is used, and it holds wherever the floor is put. It is a low minimum, and it does not fix the split: it bounds it. It also fails under the trees, where the canopy evaporates more in winter than the weather figures allow. Model A's drainage share also leans high, because it counts some evaporation from a shallow water table as drainage. A forecast does not need the split: it needs the model's numbers working together, not each flow apart.

# []{#anchor}3. The site, the record and the wells

Newborough Warren is a coastal dune system of 865 hectares. The 88 dipwells are read at the end of each month. Monthly rainfall and evaporating power come from one weather station, RAF Valley, 16 km away.

The study uses a reference network of 66 wells: those with at least 100 months of record that are still being read at the end of it. Their records are longer than that minimum, with a median of 192 months (from 140 to 252).

The wells fall into five groups that rise and fall together, found from the shape of their records before any model was fitted. Three groups are open dune (the Lake Edge, the Dune and the Western Residual) and two are under pine (the Main Forest and the Coastal Forest). The groups are stable when wells or months are left out at random, but groups built separately from two halves of the record agree only moderately (a score of 0.53 where 1 is identical). So they are a useful way of dividing one continuous aquifer, not sharply bounded units.

The numbers a study reports belong to the stretch of record they were fitted on, so the paper says which applies to every result. One basis is the average hydrograph of each group, fitted on every month available. The other is each well on its own, on its full record or on a common window, the most recent 100 months at every well, so that wells are compared under the same weather. The tests that split the record fit each well on the years before January 2018 and test it on the years after.

# []{#anchor}4. Can the record forecast?

## []{#anchor}4.1 What the drainage term adds

At each well, three models were fitted on the common window: the traditional linear model, Model A and Model B. Each was then run freely over the same months, starting from the first observed level and working out each month from the model's own previous month, never from the readings. That is a hard test: it asks whether a model can reproduce the course of the water table without being corrected by it.

Results are scored with the **forecast skill**, on a scale where 1 is perfect, 0 is no better than the average level, and below 0 is worse. Across 64 wells the traditional linear model scores 0.43 at the median well, and at 8 wells it does worse than simply guessing the average. Adding the drainage term lifts the median to 0.82 for Model B, positive at all 64 wells, and 0.77 for Model A, positive at 63.

The pine forest is the exception, because drainage there is slow and the traditional model's build-up of error does least harm. At one forest well, CEH14, Model A's drainage coefficient is negative and its free run diverges (a skill of −12.87, against −0.04 for the traditional model), while Model B scores 0.38. A model without drainage cannot forecast. But where a fixed floor leaves the drainage term unidentified, the term can cost more than it adds.

## []{#anchor}4.2 Forecasting within the recorded climate

Each version was fitted on the record before January 2018 and run freely over the years after, and then the test was run the other way round. Looking forward, Model B's median skill is 0.79 against 0.61 for Model A, and Model B is better at 88 % of wells. Looking back, Model B scores 0.78 against 0.67, and is better at 77 % of wells. The advantage is clearest in the open dune. Under the coastal forest the two are close.

Under the main forest both forecast poorly: Model B scores 0.08 and Model A 0.21. The split at January 2018 falls a month after the December 2017 clearfell beside the main forest, so those forecasts are scored over years in which the canopy changed.

## []{#anchor}4.3 Forecasting into a different climate

A forecast inside the modern record is dominated by the yearly swing. A changing climate asks something else of the model: a lasting shift in the level. The one test of that which no fit has seen is the Countryside Council for Wales record of 1989--96, read before the present network was installed, at 9 wells that are still read today. That decade was drier than anything in the modern record.

Run back over that decade from the fit to each well's whole modern record, Model A is close to unbiased: its water level is off by 0.03 metres at the median well. Model B puts the water table too high by 0.30 metres. Both forecast skills are below zero (−0.14 for Model A and −1.46 for Model B), because that decade's average is exactly the shift the test asks the model to find, so it is the bias, not the skill score, that separates the two. The ordering holds at every record length tried. The two tests split by what they score: a fast return follows the yearly swing well, and the lasting shift is what Model A carries and Model B does not.

The same decade can be asked which floor Model A should use. The floor that fits it best is 2.9 metres (band 2.8 to 2.9), where the median skill is 0.44, against −0.06 at the study's 3.7 metres. Deeper floors do worse on every measure, so the dry decade does not ask for a deeper floor, and the study's floor is close to unbiased on the same fits (off by −0.01 metres).

A second old record is Derek Ranwell's readings of 1951--53 at three places on the Warren. Their positions are uncertain, so the test uses only the *seasonal rise and fall*. Here the answer is the other way round. A floor of 0.7 metres (band 0.5 to 1.1) makes Model A behave as Model B does, both scoring 0.86, against 0.46 at the study's floor. That 0.7 metres is not a water level or an error: it is the floor depth that makes Model A fast enough to follow the seasons, which is how Model B behaves anyway.

The two old records disagree because they score different things. With its average removed, Ranwell's record tests only the yearly swing, which a fast return follows. The dry decade tests a lasting shift of the average, which the deeper floor carries. Why Ranwell's swing differs was explored after the comparison, so the paper describes it rather than tests it: his seasonal swing was 3--20 % smaller, relative to the model, than it is now, and ordinary weather, his rain gauge, the forest planted since and a slightly lower sea each fail to supply it. Drains dug for the young plantation point the right way, but are not recorded.

The two records seem to ask for two speeds: a quick return, and a slow hold that keeps the level down through a drier decade. A single store has only one. So a second, slower store was tried at every group, including one drawn down by the pine plantation as its canopy closed. No version passed the tests fixed before the fit. At Newborough a model fitted to water levels alone has one speed, and which version is used decides which.

## []{#anchor}4.4 How much record a forecast needs

Within the modern record, Model B forecasts better at every length of fit. Fitted on only 24 months before 2018, its median skill is already 0.72, and it reaches 0.79 with all of them. Model A starts at −0.14 and reaches 0.61 with all of them. A site with a few years of record can forecast its own water table with Model B.

The drainage numbers need more. Each well's drainage coefficient was refitted on shorter and shorter stretches, and the length at which it settles taken as the shortest record on which it lies within 20 % of the full-record value. For Model A that is about 24 months at a typical well, the shortest length tried, so it may need less. For Model B it is 60 months. Counted in each well's own return times, the stable length is 4.7 for Model A and 9.0 for Model B. A rule of thumb follows: a record should span several return times before the return time read from it is trusted, and the rule binds Model B harder.

The forest is the exception for both. Under the main forest Model A needs 120 months and Model B 144, and Model B settles within the lengths tried at only 5 of its wells.

## []{#anchor}4.5 Per well, or per group?

The groups come from the shape of the hydrographs alone, so a new well can be placed in one by comparing its record with the group averages, without fitting it. Can it then borrow the group's numbers? The paper tests this by running each skill test twice, on each well's own numbers and on its group's, with the tolerances fixed before the run: 0.05 in skill, and for the dry decade 0.05 metres in the typical error of the level.

Both models pass all three tests with the group's numbers. For Model A, the dry decade scores −0.17 with the group's numbers against −0.14 with each well's own, Ranwell's seasons 0.49 against 0.46, and the forecast forward from January 2018 0.72 against 0.61. Model B scores the same on Ranwell's seasons either way (0.86), and does much better on the dry decade with the group's numbers (−0.27 against −1.46). So within the tolerances set before the run, group numbers forecast and look back at least as well as each well's own.

Where a well's own record has a gap, it is better filled from a measured neighbour than from the model. With stretches of 54 months hidden in turn, each well's average spring level was put back from its nearest neighbour in the same group with a typical miss of 0.041 metres, against 0.139 metres from Model A run on the weather.

## []{#anchor}4.6 Which form to forecast with

Within the climate the record spans, use Model B: it forecasts better, needs only a few years of record, and its return time is the one the record supports (Section 5). A forecast into a different climate, whether a look back at a drier past or a projection, asks for a lasting shift of the level, and there the one independent test favours Model A. So forward runs into a changed climate use Model A at the study's floor, with Model B beside it as the fast-return bound. The two are reported as a pair on the same wells and never averaged, and the floor that the dry decade supports is carried as a check. Neither version serves a quantity it cannot work out. That is why the main forest is withheld from projection.

## []{#anchor}4.7 What the record projects

The paper takes the Met Office's high-emissions climate scenario (UKCP18), applied as seasonal changes to the observed rain and evaporating power, with fits on the common window at the 57 wells for which both versions work.

In the 2050s, the typical lasting fall of the summer water level is 0.28 metres under Model A at the study's floor, 0.24 metres under Model A at 2.9 metres, and 0.20 metres under Model B. That scenario lowers the yearly balance of rain less evaporation by 117 millimetres, about as much as the dry decade of 1989--96 fell below the modern record (110 millimetres). So this projection sits inside the range that the look back has tested.

In the 2080s the fall is 0.52 metres under Model A at the study's floor, 0.44 at 2.9 metres and 0.37 under Model B. That scenario lowers the balance by 210 millimetres a year, more than anything in the record, so this is an extrapolation. It is reported as the range between the two versions, not as one figure. That range is the honest statement of what a model fitted to water levels alone can say about a climate it has not seen.

In both periods the fall is larger in summer than over the year, and larger under Model A, whose slower recession carries the summer deficit forward. The main forest is not projected, because its drainage number cannot be worked out from the record.

# []{#anchor}5. What the numbers mean

## []{#anchor}5.1 Two time scales from one number

In both versions the drainage coefficient sets a time scale, the **e-folding time**: how long it takes a disturbance to shrink to about a third of its size. But the two versions measure it from different levels, so they answer different questions. In Model A it is a **recession time**: how long the water stored above the floor would take to fall to about a third if rain and evaporation stopped. In Model B it is a **return time**: how quickly a wet or dry spell dies away while the climate carries on. The recession time depends on where the floor is set; the return time does not. At the median well the recession time under Model A is 15.8 months and the return time under Model B is 6.5.

## []{#anchor}5.2 A check that uses no model

The return time can be measured without either model. Take each month's level less the usual level for that calendar month, and ask how much of an unusual month is still there the month after. Over the whole record the model-free answer is a return time of 5.1 months at the median well. That is close to Model B and about a third of Model A.

Group by group, Model B sits with it: at the lake edge 2.1 months against 2.0 measured, and under the coastal forest 13.3 against 12.0. Under the main forest the measured time is 15.6 months and Model B's drainage number cannot be worked out. The model-free check was repeated with two corrections that push in opposite directions. Taking out any long-term trend in a well's record, the model-free time is 5.0 months. Allowing for small errors in the readings, it is 6.1 months, a model-free figure too. With either, Model B stays the nearer version at every group where it can be worked out.

## []{#anchor}5.3 Does a dry year carry over to the next spring?

A short return time means that one spring's level says little about the next. If the drainage term is right, the link from one spring to the next should be 0.16 at the median well under Model B and 0.47 under Model A, on a scale where 0 means no link. The readings give −0.11: successive springs are close to independent. Taken at face value, Model A would make a five-year average of spring levels a poorly averaged quantity, and the record does not support that.

## []{#anchor}5.4 What the floor decides in Model A

The paper refitted Model A at every floor depth from 0.5 to 8 metres down.

**Too shallow, and the model cannot tell.** Shallower than 1.6 metres the floor sits inside the range the water table moves through, and at some groups the model cannot work out a drainage rate at all. The paper calls this depth the **identification floor**.

**What fitting alone would choose.** The floor that fits each group best differs from group to group, from 0.7 metres at the lake edge to 7.1 under the main forest. At every group it matches, within one step of the sweep, the floor that Model B works out for itself. So choosing the floor by fit alone turns Model A into Model B, and gives an answer about how quickly the water table returns to normal, not about drainage.

**Deep enough, and the water budget settles.** Below the identification floor the drainage coefficient keeps getting smaller as the floor goes deeper, but the *amount* of water draining each month hardly changes: at 3.7 metres it is 0.81 to 0.97 of its value at the deepest floor tried. The paper calls this steady range the **plateau**. The recession time keeps scaling with the floor, so it must always be reported as depending on it. The study uses a single floor of 3.7 metres for every well, which lies on the plateau and below the range of the water table everywhere.

## []{#anchor}5.5 Can the floor be tied to something physical?

Is the floor a fixed height, the same everywhere, or a depth below ground that follows the shape of the land? A common height fits slightly worse than a depth at every level tried, and higher levels leave the drainage term unidentified at many wells. So the study uses depth.

At a coastal site the most defensible floor is the level the aquifer finally drains to. Each well was refitted with its floor at its depth to mean high water (1.88 metres above Ordnance Datum), which puts the floors between 1.7 and 12.5 metres below ground. This gives the same water budget (68 % drainage at the typical well, against 68 % with the 3.7-metre floor). But it is the worse forecaster. In Model A the recession time roughly doubles, to 29 months against 16 at the study's floor, when the model-free time is 5.1. The forecast skill falls to 0.46 looking forward, against 0.61. A physical floor answers the objection that one depth is arbitrary, because the budget is the same. It is not adopted, because the dynamics are worse.

A single common height, tried as a forecaster, looks back at the dry decade better but forecasts the modern record worse (a skill of 0.56 against 0.64), and one more well loses its drainage term. The medians hide a split by group: it helps most of the Western Residual wells and fails at the open-dune wells. Under one common base the return time is short near the coast and long inland. A drainage path to a coastal base would predict that pattern, but Model A produces it mechanically too, so the fit cannot tell the two apart. It is not adopted. The level the aquifer drains to varies within groups as well as between them, which is why a floor that follows the ground serves every group.

## []{#anchor}5.6 Why Model B does not set the floor

Model B pays for its fit. Its constant and its drainage number are almost interchangeable: their estimates correlate at 0.96 at the median well. So the level its drainage refers to is fitted rather than physical, and lies near each well's own average, a median 1.6 metres below ground, at the identification floor. With it, more of the loss is booked to evaporation and plant use: a drainage share of 45 % against Model A's 68 %. That is the split the paper quotes. It follows from the rain and evaporation numbers, which Model B identifies and Pastas reproduces, and a constant that absorbs the floor leaves it the same at every floor. Using Model B's base as the floor would simply make Model A identical to Model B.

Pastas, fitted to the same wells on the full record, agrees with Model B well by well: rank correlations of 1.00, 0.96 and 0.98 for the rain, evaporation and drainage numbers, on the 63 wells for which Pastas works out a response time. That agreement is expected: it checks the implementation, not the model.

# []{#anchor}6. A checklist for other sites

For a site with a monthly water-level record and no direct measurement of where the water goes, the paper's procedure comes down to these steps.

1.  Fit both versions, with and without the constant, at the scale at which the results will be used: each well, or each group of wells that rise and fall together. For the version without the constant, try the floor at many depths and choose one on the plateau, below the range the water table occupies.
2.  Test what the drainage term adds. Run each version freely from the first observed level and compare it with the same model without drainage.
3.  Test forecasts within the record. Fit on one part and run freely over the other, in both directions. Use the version that wins, at Newborough Model B, to forecast within the climate the record spans.
4.  Test against a different climate wherever an older record exists, even a few wells or a few years. Use the version it supports for projections, with the other beside it, and report the pair, not an average.
5.  Check the record is long enough. Refit on shorter stretches and see when the drainage number stops moving. The record should span several return times.
6.  Check the time scale without a model, and report the return time as how quickly the water table recovers, not the recession time, which depends on the floor.
7.  Treat the numbers as coefficients, not as flows of water. Report the split of the loss between drainage and evaporation as depending on the floor, or not at all.
8.  Say which stretch of record every result comes from, and fill gaps in a well's record from measured neighbours rather than from the model.

# []{#anchor}7. What the record cannot tell us

## []{#anchor}7.1 What water levels alone can and cannot give

A model fitted to water levels can always balance the average books, because the level records the net of what comes in and goes out. What it can be trusted to forecast depends on the test it has passed. Within the recorded climate, the test on held-back years and the time scale measured without a model agree on Model B. Beyond it, only an independent record can say, and here it favours Model A. Someone forecasting next year's spring level and someone projecting the 2080s should not use the same version, and should know why.

What water levels alone cannot give is the split of the loss between evaporation and drainage. Model A answers with an assumption and Model B with a fitted resting level, and the two answers differ (68 against 45 % drainage at the median well). Only an independent measurement of a flow, from tracers, outflow gauging or eddy covariance, can settle it. The scientific literature often calls the drainage number a "memory". Neither reading is a memory, and the two differ by more than a factor of two.

## []{#anchor}7.2 These are properties of this aquifer

The identification floor, Model B's resting level and the plateau are properties of the water-table depths at Newborough, not general constants. At another site the depth sweep must be repeated, not the numbers reused, and so must the record length each version needs.

## []{#anchor}7.3 Relation to common practice

Transfer-function models such as Pastas estimate the Model B form. That is the right form for forecasting within the recorded climate. What this practice does not usually do is test a forecast against a different climate, and at this site that test reverses the ranking.

## []{#anchor}7.4 Limits

The weather comes from one station outside the site, at monthly resolution, and the evaporation figure is an index of demand rather than a measured flow. The model is straight-line and unchanging in time, and the projections assume its numbers hold under a climate the record has not seen, which the look-back tests reach only as far as the 2050s. Under the main forest, Model B's drainage number cannot be worked out. A slow response is one reading of that, and a forcing that misrepresents the forest's evaporation is another, and the record does not tell them apart. The independent tests of the lasting response rest on 9 wells in one decade and three approximately placed sites in another.

# []{#anchor}8. In short

A model fitted to a monthly water-level record can forecast that record's water table, but which version can be trusted depends on what is being forecast. Within the climate the record spans, the version with a free constant (Model B) forecasts better, needs only a few years of record, and measures the time the water table takes to return to its usual level, which a measurement that uses no model confirms. Against a drier decade that no fit had seen, the version without the constant (Model A), with its floor on the plateau, reproduces the lasting shift of the level, and Model B does not.

Projections into a changed climate should therefore use the version an independent record supports, with the other beside it, and report the pair. At Newborough, under a high-emissions climate, the two versions put the typical fall of the summer water level at 0.20--0.28 metres in the 2050s, inside the range the look back has tested, and 0.37--0.52 metres in the 2080s, beyond it. The main forest is withheld, because its drainage number cannot be worked out from the record.

The numbers themselves are not flows of water. The split of the loss between drainage and evaporation depends on the floor, and the recession time describes the floor as much as the aquifer. Each quantity should be taken from the version that identifies it, with the stretch of record declared and the tests repeated at every site.

# []{#anchor}Glossary

**Aquifer.** Water-saturated sand or rock below the water table; here, the dune sand.

**Constant (intercept).** A fixed amount added to the model every month. Including it (Model B) lets the model find its own resting level.

**Datum (floor).** The imaginary depth below ground that drainage is measured from. Model A fixes it; Model B finds it.

**Dipwell.** A shallow perforated pipe in which the water level is measured by hand.

**Drainage coefficient.** The model number that sets how quickly water drains away. Its meaning depends on the version of the model.

**Drainage share.** The part of the water lost each month that drains away underground rather than being taken by evaporation and plants.

**E-folding time.** The time a disturbance takes to shrink to about a third (more exactly 37 %) of its size.

**Forecast skill (efficiency).** A score of how well a model's run matches the readings: 1 is perfect, 0 is no better than the average level, and below 0 is worse.

**Free run.** A model run forward from the first observed level, each month worked out from its own previous month and never corrected by a reading.

**Identification floor.** The shallowest floor depth at which every part of the site gives a sensible drainage rate.

**Model A, Model B.** The model without the constant (Model A) and with it (Model B).

**Plateau.** The range of floor depths over which the amount of water draining no longer changes with the depth chosen.

**Recession time.** In Model A, the e-folding time of the water stored above the floor; it depends on where the floor is set.

**Return time.** In Model B, the e-folding time with which the water table goes back to its usual level after a wet or dry spell; it does not depend on any floor.

**Traditional linear model.** The model with no drainage term: rain in, evaporation out, nothing pulling the level back.

# []{#anchor}Further reading

Hollingham, M. (2026) Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you. In preparation.

Ranwell, D.S. (1959) Newborough Warren, Anglesey. I. The dune system and dune slack habitat. *Journal of Ecology* 47(3), 571--601.

The project's data, analysis and documents: https://github.com/newbroman/Newborough_Hydrology
