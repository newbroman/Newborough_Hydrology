<!-- GENERATED MIRROR of docs/papers/paper_M/PaperM_plain_v1_1.odt — do not edit. source-sha256=d5e14ca1606660a9 pandoc=3.1.3 -->
<!--      Regenerate with: python3 tools/refresh_mirrors.py -->

What monthly water levels can tell us: a plain-language guide to the methods paper

M. Hollingham

October 2026

This guide explains, without equations, a scientific paper about how groundwater models are fitted to monthly water-level records: *Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you* (Hollingham, 2026). It follows the paper section by section. Every number in it is taken from the same project files as the paper, so the two always agree. Words in **bold** on first use are explained in the glossary at the end.

# []{#anchor}1. Why this matters

Dune slacks, the damp hollows between sand dunes, are among the richest wildlife habitats on the coast, and they depend on groundwater. How wet a slack is in spring and how far the water falls in summer decide which plants and animals can live there.

At most sites the only record of that groundwater is a set of shallow pipes, called **dipwells**, in which someone measures the water level by hand about once a month. Newborough Warren on Anglesey has 88 of them across 865 hectares of dunes and pine forest, and some have been read for over twenty years.

What managers usually want to know is not the level itself but what lies behind it. How much of the rain that soaks in drains away underground, and how much is drawn back up by plants and the sun? If a dry year lowers the water table, how long does the effect last? Neither question can be answered by measuring directly at most sites, because that needs expensive instruments. So scientists fit a simple model to the water levels and read the answers from the model.

The paper asks how far those answers can be trusted. It finds that three choices made when fitting the model, usually without comment, change what the answers mean.

# []{#anchor}2. The model in one picture

Think of the ground as a bath with a slow leak. Each month:

-   **rain** tops it up;
-   **evaporation and plant use** draw water back out from the top;
-   **drainage** lets water leak away underground, faster when the water stands higher.

The model fitted at Newborough says exactly this, one month at a time. It has three numbers, worked out from the record at each well:

-   how much the water rises for each millimetre of rain;
-   how much it falls for each millimetre of evaporating power in the air;
-   how quickly it drains away, which the paper calls the **drainage coefficient**.

The third number is the one this paper is about, because two quite different things can be read from it.

# []{#anchor}3. Three hidden choices

Before the model can be fitted, three choices have to be made. They are rarely reported, but each one changes what the drainage coefficient means.

1.  **Is there a constant term?** The model can include an extra fixed amount that is added every month, or leave it out. The paper calls the version without it **Model A** and the version with it **Model B**.
2.  **How deep is the floor?** Model A assumes the water drains towards an imaginary floor, the **datum**, at a fixed depth below the ground, and drains faster the higher the water stands above it. Somebody has to choose that depth.
3.  **Which stretch of record?** The model can be fitted to all the months a well has, or to a shorter, common stretch so that all wells are compared over the same weather.

# []{#anchor}4. The floor (the datum)

## []{#anchor}How the floor changes the answer

Where the floor is placed decides how the drainage coefficient behaves.

-   With a **deep floor**, the water table always stands far above it. Drainage is then a steady, slow pull, and the model's water table recovers slowly after a wet or dry spell.
-   With a **shallow floor**, the water table sits close to it. Small rises and falls change the drainage a lot, and the model snaps back quickly.

The paper tried every floor depth from 0.5 to 8 metres down and watched what happened.

## []{#anchor}Too shallow, and the model cannot tell

Shallower than about 1.6 metres the floor sits inside the range the water table moves through, and at some parts of the site the model cannot work out a drainage rate at all. The paper calls this depth the **identification floor**.

## []{#anchor}Deep enough, and the water budget settles

Below that depth something useful happens. The drainage coefficient keeps getting smaller as the floor goes deeper, but the *amount* of water draining away each month hardly changes, and neither does the split of the water budget between drainage and evaporation. At the lake edge, for example, drainage takes 73 % of the water lost with the floor at 1.6 metres, 86 % at 3.7 metres and 89 % at 8 metres. The paper calls this steady range the **plateau**.

So the water budget can be trusted once the floor is deep enough, even though nobody knows where the real floor is. The study uses a single floor of 3.7 metres for every well, which lies on the plateau everywhere.

## []{#anchor}What fitting alone would choose

If the floor depth is simply chosen to make the model fit the record best, it comes out shallow at the open-dune wells and deeper under the forest. That best-fitting floor turns out to be exactly the floor that Model B works out for itself. In other words, choosing the floor by fit alone turns Model A into Model B, and gives an answer about how quickly the water returns to normal, not about drainage.

## []{#anchor}Height above sea level, or depth below ground?

Is the floor a fixed height, the same everywhere, or does it follow the shape of the ground? The two fit the record almost equally well, but a fixed height leaves the drainage rate impossible to work out at many wells. A depth below ground does not, so the study uses depth. It also tried a floor set by the sea: the level of high tide, worked out as a depth at each well. That gives the same water budget (68 % drainage at a typical well, against 68 % with the 3.7-metre floor), but the model then forecasts worse, so it was not adopted.

# []{#anchor}5. Two readings of one number

## []{#anchor}Draining to a floor, or returning to normal

The drainage coefficient can be read in two ways.

-   In **Model A** it describes water draining towards the chosen floor. Its value depends on where the floor is.
-   In **Model B** the constant lets the model find its own resting level, and the number describes how quickly the water table returns to that level after a wet or dry spell. It does not depend on any floor.

At a typical well the two readings differ by more than a factor of two. A convenient way to compare them is the time a disturbance takes to shrink to about a third of its size, the **e-folding time**. Model A says about 16 months; Model B says about 6.5.

## []{#anchor}A check that uses no model

Which is right about how the water table behaves? The paper measured it directly from the readings. If this month's level is unusually high, how much of that is still there next month? The answer, worked out over the whole record, gives a return time without any model at all: 5.1 months at a typical well. That is close to Model B and about a third of Model A.

The check was repeated with two corrections that push in opposite directions: taking out any long-term trend in a well's record (5.0 months), and allowing for small errors in the readings (6.1 months). Either way Model B stays the closer. Rises and falls also return at the same rate: a wet spell fades as quickly as a dry one.

## []{#anchor}Does a dry year carry over to the next spring?

A short return time means that one spring's level says little about the next. The readings agree: spring levels in successive years are close to independent. Model A on its own would suggest that a dry year lingers into the next spring much more than it does.

## []{#anchor}Forecasting

The paper fitted each model on the years before 2018 and asked it to forecast the years after, without seeing them. Model B did better at 88 % of wells. Even with only 24 months of record to learn from, Model B forecasts its own well usefully (a skill of 0.72).

## []{#anchor}Why the drainage term matters at all

The simplest model of all leaves drainage out entirely: rain in, evaporation out, nothing else. Left to run on its own, that model drifts, because nothing pulls the water table back towards a normal level, and each month's error carries into the next. At a typical well its forecast skill is 0.42 on a scale where 1 is perfect, and at 11 wells it does worse than simply guessing the average. Adding the drainage term lifts the typical score to 0.82. The drainage term is what keeps the model anchored.

# []{#anchor}6. What the old records say

The modern network does not cover a long enough or varied enough period to settle everything, but two older sets of readings do something no model has seen.

## []{#anchor}The drier decade, 1989--96

The Countryside Council for Wales read water levels at Newborough between 1989 and 1996, before the present network was installed, at 9 wells that are still read today. That decade was drier than anything in the modern record, so it tests whether a model can carry a lasting shift in the water table.

Run back over that decade from today's record, Model A is close to right on average (off by 0.03 metres), while Model B puts the water table too high by 0.30 metres. For a long run of dry years, Model A does better. Asked which floor depth fits that decade best, the answer is about 2.9 metres: close to the 3.7 metres used, and not deeper.

## []{#anchor}Ranwell's readings, 1951--53

Derek Ranwell measured water levels at three places on the Warren between 1951 and 1953. Their exact positions are uncertain, so his average level cannot be trusted, and the test uses only the *seasonal rise and fall* he recorded.

Here the result is the other way round. With the floor at about 0.7 metres below ground, Model A reproduces Ranwell's seasons as well as Model B does (a score of 0.86 for both), and with the floor at 3.7 metres it does much worse (0.46). That 0.7 metres is not a water level or an error: it is the floor depth that makes Model A behave quickly enough to follow the seasons, which is how Model B behaves anyway.

## []{#anchor}Why both can be true

The two old records ask different questions. Ranwell's seasons ask how fast the water table bounces back, and the answer is: quickly. The dry decade asks whether the water table can stay low through a long run of dry years, and the answer is: yes, more than a quick bounce would allow. The aquifer seems to do both. A model with a single floor can only do one or the other, which is why the paper uses each version only for the question it answers.

# []{#anchor}7. How much record you need

The paper refitted every well on records of different lengths and asked how long a record each version needs before its drainage number stops changing.

-   **Model A** settles on about 24 months at a typical well. That was the shortest length tried, so it may need less.
-   **Model B** needs about 60 months.
-   **Under the main pine forest** both need far longer: about 120 and 144 months. The forest responds so slowly that Model B's return time cannot be pinned down there at all.

A rule of thumb follows: a record should span several return times before the return time read from it is trusted.

# []{#anchor}8. What it finds at Newborough

The wells fall into five groups that behave alike: three in open dune (the Lake Edge, the Dune and the Western Residual) and two under pine (the Main Forest and the Coastal Forest). Using each version of the model for what it is good at, the paper reports for each group:

-   **How the water budget splits.** With the floor anywhere on the plateau, drainage carries 86--89 % of the water lost at the lake edge, 69--72 % in the open dune, 65--69 % in the western dune, 63--68 % under the coastal forest and only 24--28 % under the main forest, where the trees take most of the rest. Evaporation and plant use take whatever drainage does not.
-   **How sure is that?** Moving the floor around the plateau, or setting it at each well's depth to high tide, changes these figures by only a few points, and individual wells scatter a little around their group. The bigger uncertainty is the version of the model. Letting the model work out its own resting level (Model B) gives drainage only 29--60 % of the loss, and least at the lake edge (37 %). The paper argues that the fixed floor is the right basis for the water budget, because Model B's resting level sits close to the average water level rather than at anything physical; but only a direct measurement of drainage or evaporation at the site could settle it.
-   **How quickly the water returns to normal.** From about 2.1 months at the lake edge to about 13.3 months under the coastal forest. Under the main forest it is too slow to measure on the present record.

These are shares, not amounts. Turning them into millimetres of water needs one more property of the sand, how much water it releases as the water table falls, which the water levels alone cannot give. That is dealt with in the companion study of the site.

# []{#anchor}9. The questions people will ask

## []{#anchor}Is there a second, slower store of water?

The two old records ask for two speeds: a quick return and a slow hold. The obvious idea is a second, slower store of water working alongside the first. The paper fitted one, and at every group the fit gave it nothing to do: one store was better.

## []{#anchor}Did the plantation drain a store that was once there?

The pine plantation was planted between 1947 and 1965. Perhaps it drew down water that had built up before the trees, and the early years of the record caught the last of it. To test this fairly, the years before the canopy closed were modelled as the open dune they then were, and the forest's effect was brought in gradually as the trees grew, over the 15 to 20 years a Corsican pine canopy usually takes to close. Three planting years and two closure times were tried, and the rule for a "yes" was fixed before the test was run. No case passed. Under the main forest a slow store fits the early years better if the planting was late, but it then forecasts the recent years far worse. On this record, a store drawn down by the plantation is not supported.

## []{#anchor}Was it the retreating coast?

The coastal forest group is nearest the eroding shore, and a retreating coast lowers the water table near it gradually. The change found there is not gradual: it is a fall over a few years that then settled. A storm that cut back the shore could do that, and so could a change in the trees. The water levels alone cannot tell the two apart at one group.

## []{#anchor}Was it how the rain fell?

Rain that falls in long, steady spells loses less to evaporation than a month's total suggests, and a monthly model cannot see that. Daily rainfall from a gauge on Anglesey shows that only one of the three wet winters at the start of the record was unusual in this way, and later wet winters had as much long-spell rain without the same effect. How the rain fell does not explain the early high water.

# []{#anchor}10. A checklist for other sites

For any site with a monthly water-level record and no direct measurement of where the water goes, the paper's procedure comes down to these steps.

1.  Try the floor at many depths, and note how the drainage number, the fit and the amount drained change.
2.  Find the shallowest floor at which every part of the site gives a sensible drainage rate.
3.  Fit the version with the constant as well. If the best-fitting floor matches its resting level, a floor chosen on fit alone is measuring the return time, not drainage.
4.  Find where the amount drained stops changing with depth (the plateau), and choose one floor there, deep enough for the part of the site with the deepest water table.
5.  Check whether the floor should follow the ground or be a fixed height, and what a physically meaningful floor would give.
6.  Report what the chosen floor costs in fit at each part of the site.
7.  Check the return time with the no-model method, and test forecasts on years the model has not seen.
8.  Use each version for what it is good at: the version without the constant for the water budget; the version with it for how long effects last and for short forecasts; for long-term changes, whichever version an independent old record supports, with the other alongside.
9.  Say which stretch of record every result comes from, check that the record is long enough for the number being read, and test long-term behaviour against an independent period wherever one exists.

# []{#anchor}Glossary

**Aquifer.** Water-saturated sand or rock below the water table; here, the dune sand.

**Constant (intercept).** A fixed amount added to the model every month. Including it (Model B) lets the model find its own resting level.

**Datum (floor).** The imaginary depth below ground that Model A assumes the water drains towards.

**Dipwell.** A shallow perforated pipe in which the water level is measured by hand.

**Drainage coefficient.** The model number that sets how quickly water drains away. Its meaning depends on the version of the model.

**Drainage share.** The part of the water lost each month that drains away underground rather than being taken by evaporation and plants.

**E-folding time.** The time a disturbance takes to shrink to about a third (more exactly 37 %) of its size. A convenient measure of how quickly the water table returns to normal.

**Forecast skill (efficiency).** A score of how well a model's run matches the readings: 1 is perfect, 0 is no better than the average level, and below 0 is worse.

**Identification floor.** The shallowest floor depth at which every part of the site gives a sensible drainage rate.

**Model A, Model B.** The model without the constant (Model A) and with it (Model B).

**Plateau.** The range of floor depths over which the water budget no longer changes with the depth chosen.

**Return time.** How quickly the water table goes back to its usual level after a wet or dry spell; measured here by the e-folding time.

# []{#anchor}Further reading

Hollingham, M. (2026) Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you. In preparation.

Ranwell, D.S. (1959) Newborough Warren, Anglesey. I. The dune system and dune slack habitat. *Journal of Ecology* 47(3), 571--601.

The project's data, analysis and documents: https://github.com/newbroman/Newborough_Hydrology
