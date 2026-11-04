What monthly water levels can tell us: a plain-language guide to the methods paper

M. Hollingham

November 2026

This guide explains, without equations, a scientific paper about whether a simple groundwater model fitted to monthly water levels can be trusted to forecast: *Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you* (Hollingham, 2026). It follows the paper section by section, with the same section numbers. Every number in it is taken from the same project files as the paper, so the two always agree. Words in **bold** on first use are explained in the glossary at the end.

# 1. Why this matters

Dune slacks, the damp hollows between sand dunes, are among the richest wildlife habitats on the coast, and they depend on groundwater. How wet a slack is in spring and how far the water falls in summer decide which plants and animals can live there.

At most sites the only record of that groundwater is a set of shallow pipes, called **dipwells**, in which someone measures the water level by hand about once a month. Newborough Warren on Anglesey has ⟪outputs/01_data_prep/01_report_numbers.csv|wells_classified_n|dp0⟫ of them across ⟪outputs/12_figure_site_overview/12_report_numbers.csv|study_area_ha|dp0⟫ hectares of dunes and pine forest, and some have been read for over twenty years.

What managers most want from that record is a forecast: how the water table will respond to the coming years, and to a changing climate. The rain that soaks in, the water that drains away underground and the water drawn back up by plants and the sun are rarely measured at such sites, so the forecast comes from a simple model fitted to the water levels themselves.

That model can be fitted in two common ways, and which one was used is seldom reported. The choice changes what the model's main number means, and how the model behaves when it is run forward. A forecast cannot be checked until the future arrives, so the paper checks what can be checked now: how each version does on recent years held back from the fit, and how each does on old records from a drier climate than the one it was fitted on. It asks what a model like this can be trusted to forecast.

# 2. The model in one picture

## The bath with a slow leak

Think of the ground as a bath with a slow leak. Each month:

-   **rain** tops it up;
-   **evaporation and plant use** draw water back out from the top;
-   **drainage** lets water leak away underground, faster when the water stands higher.

The model says exactly this, one month at a time, and predicts how far the water level will move. It has three numbers, worked out from the record at each well:

-   how much the water rises for each millimetre of rain;
-   how much it falls for each millimetre of evaporating power in the air;
-   how quickly it drains away, which the paper calls the **drainage coefficient**.

## The floor, and two versions of the model

Drainage has to be measured from somewhere. The model takes it to run faster the higher the water stands above an imaginary floor, the **datum**, at a fixed depth below the ground. There are two ways to deal with that floor.

-   In **Model A** the floor is chosen in advance. The study uses a single depth of ⟪src/utils/config.py|DRAINAGE_DATUM|dp1⟫ metres for every well.
-   In **Model B** the model adds a constant to the sum and so finds its own floor, wherever the record puts it.

The two are one model family, separated only by where the floor comes from: Model B is Model A with the floor moved to the level at which the fitted drainage is zero.

The drainage coefficient means something different in each. In Model A it describes water draining towards the chosen floor, so its value changes if the floor is moved. In Model B it describes how quickly the water table returns to its own normal level after a wet or dry spell, and that does not depend on any floor.

Leaving drainage out altogether gives the simplest model of all, the **traditional linear model**: rain in, evaporation out, nothing else. Run forward on its own, it has nothing pulling the water table back towards a usual level, so each month's error is carried into every month after it.

## A check against widely used software

Pastas is widely used software that does the same job. Model B is exactly what Pastas fits, written one month at a time, so when the two agree that shows the code is right. It is not independent evidence that either version is right. Model A has no match in Pastas, which has no fixed floor.

## What neither version can decide

The water table loses water in two ways: by drainage, and by evaporation and plant use. The levels alone cannot say how the loss splits between them, because the split depends on the level that drainage is measured from. Model A sets that level by assumption and Model B by fit. Without a direct measurement of drainage, evaporation or recharge, neither can fix the true split. Model A's drainage share also leans high, because it counts some evaporation from a shallow water table as drainage. A forecast does not need the split: it needs the model's numbers working together, not each flow apart.

# 3. The site, the record and the wells

Newborough Warren is a coastal dune system of ⟪outputs/12_figure_site_overview/12_report_numbers.csv|study_area_ha|dp0⟫ hectares. The ⟪outputs/01_data_prep/01_report_numbers.csv|wells_classified_n|dp0⟫ dipwells are read at the end of each month. Monthly rainfall and evaporating power come from one weather station, RAF Valley, ⟪outputs/00_climate_summary/00_report_numbers.csv|raf_valley_distance_km|dp0⟫ km away.

The study uses a reference network of ⟪outputs/00_climate_summary/00_report_numbers.csv|reference_n_wells|dp0⟫ wells: those with at least ⟪src/utils/config.py|LCSC_DATA_LIMIT|dp0⟫ months of record that are still being read at the end of it. Their records are longer than that minimum, with a median of ⟪outputs/00_climate_summary/00_report_numbers.csv|reference_record_months_median|dp0⟫ months (from ⟪outputs/00_climate_summary/00_report_numbers.csv|reference_record_months_min|dp0⟫ to ⟪outputs/00_climate_summary/00_report_numbers.csv|reference_record_months_max|dp0⟫).

The wells fall into five groups that rise and fall together, found from the shape of their records before any model was fitted. Three groups are open dune (the Lake Edge, the Dune and the Western Residual) and two are under pine (the Main Forest and the Coastal Forest). The groups are stable when wells or months are left out at random, but groups built separately from two halves of the record agree only moderately (a score of ⟪outputs/02_clustering/02_report_numbers.csv|cluster_splithalf_ari_mean|dp2⟫ where 1 is identical). So they are a useful way of dividing one continuous aquifer, not sharply bounded units.

The numbers a study reports belong to the stretch of record they were fitted on, so the paper says which applies to every result. One basis is the average hydrograph of each group, fitted on every month available. The other is each well on its own, on its full record or on a common window, the most recent ⟪src/utils/config.py|LCSC_DATA_LIMIT|dp0⟫ months at every well, so that wells are compared under the same weather. The tests that split the record fit each well on the years before January 2018 and test it on the years after.

# 4. Can the record forecast?

## 4.1 What the drainage term adds

At each well, three models were fitted on the common window: the traditional linear model, Model A and Model B. Each was then run freely over the same months, starting from the first observed level and working out each month from the model's own previous month, never from the readings. That is a hard test: it asks whether a model can reproduce the course of the water table without being corrected by it.

Results are scored with the **forecast skill**, on a scale where 1 is perfect, 0 is no better than the average level, and below 0 is worse. Across ⟪outputs/08_model_benchmarking/08_report_numbers.csv|benchmark_n_wells|dp0⟫ wells the traditional linear model scores ⟪outputs/08_model_benchmarking/08_report_numbers.csv|benchmark_median_NSE_TLM|dp2⟫ at the median well, and at ⟪outputs/08_model_benchmarking/08_report_numbers.csv|benchmark_negative_NSE_TLM|dp0⟫ wells it does worse than simply guessing the average. Adding the drainage term lifts the median to ⟪outputs/08_model_benchmarking/08_report_numbers.csv|benchmark_median_NSE_ModelB|dp2⟫ for Model B, positive at all ⟪outputs/08_model_benchmarking/08_report_numbers.csv|benchmark_positive_NSE_ModelB|dp0⟫ wells, and ⟪outputs/08_model_benchmarking/08_report_numbers.csv|benchmark_median_NSE_SSM|dp2⟫ for Model A, positive at ⟪outputs/08_model_benchmarking/08_report_numbers.csv|benchmark_positive_NSE_SSM|dp0⟫.

The pine forest is the exception, because drainage there is slow and the traditional model's build-up of error does least harm. At one forest well, CEH14, Model A's drainage coefficient is negative and its free run diverges (a skill of ⟪outputs/08_model_benchmarking/08_perwell_nse.csv|CEH14 · SSM_NSE|dp2⟫, against ⟪outputs/08_model_benchmarking/08_perwell_nse.csv|CEH14 · TLM_NSE|dp2⟫ for the traditional model), while Model B scores ⟪outputs/08_model_benchmarking/08_perwell_nse.csv|CEH14 · ModelB_NSE|dp2⟫. A model without drainage cannot forecast. But where a fixed floor leaves the drainage term unidentified, the term can cost more than it adds.

## 4.2 Forecasting within the recorded climate

Each version was fitted on the record before January 2018 and run freely over the years after, and then the test was run the other way round. Looking forward, Model B's median skill is ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_fwd_B_median_all|dp2⟫ against ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_fwd_A_median_all|dp2⟫ for Model A, and Model B is better at ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_fwd_share_B_better_all|dp0 x100⟫ % of wells. Looking back, Model B scores ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_rev_B_median_all|dp2⟫ against ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_rev_A_median_all|dp2⟫, and is better at ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_rev_share_B_better_all|dp0 x100⟫ % of wells. The advantage is clearest in the open dune. Under the coastal forest the two are close.

Under the main forest both forecast poorly: Model B scores ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_fwd_B_median_C4|dp2⟫ and Model A ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_fwd_A_median_C4|dp2⟫. The split at January 2018 falls a month after the December 2017 clearfell beside the main forest, so those forecasts are scored over years in which the canopy changed.

## 4.3 Forecasting into a different climate

A forecast inside the modern record is dominated by the yearly swing. A changing climate asks something else of the model: a lasting shift in the level. The one test of that which no fit has seen is the Countryside Council for Wales record of 1989--96, read before the present network was installed, at ⟪outputs/39_ccw_hindcast/39_report_numbers.csv|n_wells_admitted|dp0⟫ wells that are still read today. That decade was drier than anything in the modern record.

Run back over that decade from the fit to each well's whole modern record, Model A is close to unbiased: its water level is off by ⟪outputs/50_record_length/50_report_numbers.csv|reclen_ccw_bias_m_A_median_Lfull_all|dp2⟫ metres at the median well. Model B puts the water table too high by ⟪outputs/50_record_length/50_report_numbers.csv|reclen_ccw_bias_m_B_median_Lfull_all|dp2⟫ metres. Both forecast skills are below zero (⟪outputs/50_record_length/50_report_numbers.csv|reclen_ccw_nse_A_median_Lfull_all|dp2⟫ for Model A and ⟪outputs/50_record_length/50_report_numbers.csv|reclen_ccw_nse_B_median_Lfull_all|dp2⟫ for Model B), because that decade's average is exactly the shift the test asks the model to find, so it is the bias, not the skill score, that separates the two. The ordering holds at every record length tried. The two tests split by what they score: a fast return follows the yearly swing well, and the lasting shift is what Model A carries and Model B does not.

The same decade can be asked which floor Model A should use. The floor that fits it best is ⟪outputs/50_record_length/50_report_numbers.csv|datum_ccw_supported_m|dp1⟫ metres (band ⟪outputs/50_record_length/50_report_numbers.csv|datum_ccw_band_min_m|dp1⟫ to ⟪outputs/50_record_length/50_report_numbers.csv|datum_ccw_band_max_m|dp1⟫), where the median skill is ⟪outputs/50_record_length/50_report_numbers.csv|datum_ccw_nse_median_at_D2.9|dp2⟫, against ⟪outputs/50_record_length/50_report_numbers.csv|datum_ccw_nse_median_at_D3.7|dp2⟫ at the study's ⟪src/utils/config.py|DRAINAGE_DATUM|dp1⟫ metres. Deeper floors do worse on every measure, so the dry decade does not ask for a deeper floor, and the study's floor is close to unbiased on the same fits (off by ⟪outputs/50_record_length/50_report_numbers.csv|reclen_ccw_bias_m_A_median_L100_end|dp2⟫ metres).

A second old record is Derek Ranwell's readings of 1951--53 at three places on the Warren. Their positions are uncertain, so the test uses only the *seasonal rise and fall*. Here the answer is the other way round. A floor of ⟪outputs/50_record_length/50_report_numbers.csv|datum_ranwell_supported_m|dp1⟫ metres (band ⟪outputs/50_record_length/50_report_numbers.csv|datum_ranwell_band_min_m|dp1⟫ to ⟪outputs/50_record_length/50_report_numbers.csv|datum_ranwell_band_max_m|dp1⟫) makes Model A behave as Model B does, both scoring ⟪outputs/50_record_length/50_report_numbers.csv|ranwell_nse_median_at_supported|dp2⟫, against ⟪outputs/50_record_length/50_report_numbers.csv|ranwell_nse_median_at_project|dp2⟫ at the study's floor. That ⟪outputs/50_record_length/50_report_numbers.csv|datum_ranwell_supported_m|dp1⟫ metres is not a water level or an error: it is the floor depth that makes Model A fast enough to follow the seasons, which is how Model B behaves anyway.

The two old records disagree because they score different things. With its average removed, Ranwell's record tests only the yearly swing, which a fast return follows. The dry decade tests a lasting shift of the average, which the deeper floor carries. Why Ranwell's swing differs was explored after the comparison, so the paper describes it rather than tests it: his seasonal swing was ⟪outputs/50_record_length/50_report_numbers.csv|ranwell_epoch_swing_smaller_pct_min|dp0⟫--⟪outputs/50_record_length/50_report_numbers.csv|ranwell_epoch_swing_smaller_pct_max|dp0⟫ % smaller, relative to the model, than it is now, and ordinary weather, his rain gauge, the forest planted since and a slightly lower sea each fail to supply it. Drains dug for the young plantation point the right way, but are not recorded.

The two records seem to ask for two speeds: a quick return, and a slow hold that keeps the level down through a drier decade. A single store has only one. So a second, slower store was tried at every group, including one drawn down by the pine plantation as its canopy closed. No version passed the tests fixed before the fit. At Newborough a model fitted to water levels alone has one speed, and which version is used decides which.

## 4.4 How much record a forecast needs

Within the modern record, Model B forecasts better at every length of fit. Fitted on only ⟪src/utils/config.py|RECLEN_MIN_FIT_MONTHS|dp0⟫ months before 2018, its median skill is already ⟪outputs/50_record_length/50_report_numbers.csv|reclen_nse_fwd_B_median_L24_all|dp2⟫, and it reaches ⟪outputs/50_record_length/50_report_numbers.csv|reclen_nse_fwd_B_median_Lfull_all|dp2⟫ with all of them. Model A starts at ⟪outputs/50_record_length/50_report_numbers.csv|reclen_nse_fwd_A_median_L24_all|dp2⟫ and reaches ⟪outputs/50_record_length/50_report_numbers.csv|reclen_nse_fwd_A_median_Lfull_all|dp2⟫ with all of them. A site with a few years of record can forecast its own water table with Model B.

The drainage numbers need more. Each well's drainage coefficient was refitted on shorter and shorter stretches, and the length at which it settles taken as the shortest record on which it lies within ⟪src/utils/config.py|RECLEN_STABLE_TOL|dp0 x100⟫ % of the full-record value. For Model A that is about ⟪outputs/50_record_length/50_report_numbers.csv|reclen_stable_length_months_A_median_all|dp0⟫ months at a typical well, the shortest length tried, so it may need less. For Model B it is ⟪outputs/50_record_length/50_report_numbers.csv|reclen_stable_length_months_B_median_all|dp0⟫ months. Counted in each well's own return times, the stable length is ⟪outputs/50_record_length/50_report_numbers.csv|reclen_stable_length_in_efolds_A_median_all|dp1⟫ for Model A and ⟪outputs/50_record_length/50_report_numbers.csv|reclen_stable_length_in_efolds_B_median_all|dp1⟫ for Model B. A rule of thumb follows: a record should span several return times before the return time read from it is trusted, and the rule binds Model B harder.

The forest is the exception for both. Under the main forest Model A needs ⟪outputs/50_record_length/50_report_numbers.csv|reclen_stable_length_months_A_median_C4|dp0⟫ months and Model B ⟪outputs/50_record_length/50_report_numbers.csv|reclen_stable_length_months_B_median_C4|dp0⟫, and Model B settles within the lengths tried at only ⟪outputs/50_record_length/50_report_numbers.csv|reclen_stable_n_wells_reached_B_C4|dp0⟫ of its wells.

## 4.5 Per well, or per group?

The groups come from the shape of the hydrographs alone, so a new well can be placed in one by comparing its record with the group averages, without fitting it. Can it then borrow the group's numbers? The paper tests this by running each skill test twice, on each well's own numbers and on its group's, with the tolerances fixed before the run: ⟪src/utils/config.py|BASIS_TOL_NSE|dp2⟫ in skill, and for the dry decade ⟪src/utils/config.py|BASIS_TOL_BIAS_M|dp2⟫ metres in the typical error of the level.

With both versions the group numbers pass all three tests. With Model A, on the dry decade, their median skill is ⟪outputs/50_record_length/50_report_numbers.csv|basis_ccw_nse_median_cluster_A|dp2⟫ against ⟪outputs/50_record_length/50_report_numbers.csv|basis_ccw_nse_median_well_A|dp2⟫ for the wells' own, and forecasting forward from January 2018 they score ⟪outputs/50_record_length/50_report_numbers.csv|basis_split_nse_median_cluster_A_fwd|dp2⟫ against ⟪outputs/50_record_length/50_report_numbers.csv|basis_split_nse_median_well_A_fwd|dp2⟫. So within the tolerances set before the run, group numbers forecast and look back as well as each well's own.

Where a well's own record has a gap, it is better filled from a measured neighbour than from the model. With stretches of ⟪src/utils/config.py|GAPFILL_HOLDOUT_MONTHS|dp0⟫ months hidden in turn, each well's average spring level was put back from its nearest neighbour in the same group with a typical miss of ⟪outputs/51_cluster_gap_fill/51_report_numbers.csv|gapfill_pooled_nearest_cluster_excluded_msl_abs_err_median|dp3⟫ metres, against ⟪outputs/51_cluster_gap_fill/51_report_numbers.csv|gapfill_pooled_ssm_model_a_excluded_msl_abs_err_median|dp3⟫ metres from Model A run on the weather.

## 4.6 Which form to forecast with

Within the climate the record spans, use Model B: it forecasts better, needs only a few years of record, and its return time is the one the record supports (Section 5). A forecast into a different climate, whether a look back at a drier past or a projection, asks for a lasting shift of the level, and there the one independent test favours Model A. So forward runs into a changed climate use Model A at the study's floor, with Model B beside it as the fast-return bound. The two are reported as a pair on the same wells and never averaged, and the floor that the dry decade supports is carried as a check. Neither version serves a quantity it cannot work out. That is why the main forest is withheld from projection.

## 4.7 What the record projects

The paper takes the Met Office's high-emissions climate scenario (UKCP18), applied as seasonal changes to the observed rain and evaporating power, with fits on the common window at the ⟪outputs/50_record_length/50_report_numbers.csv|projection_2050s_n_wells_pair|dp0⟫ wells for which both versions work.

In the 2050s, the typical lasting fall of the summer water level is ⟪outputs/50_record_length/50_report_numbers.csv|projection_2050s_summer_fall_median_at_project|dp2 abs⟫ metres under Model A at the study's floor, ⟪outputs/50_record_length/50_report_numbers.csv|projection_2050s_summer_fall_median_at_supported|dp2 abs⟫ metres under Model A at ⟪outputs/50_record_length/50_report_numbers.csv|datum_ccw_supported_m|dp1⟫ metres, and ⟪outputs/50_record_length/50_report_numbers.csv|projection_2050s_summer_fall_median_model_b|dp2 abs⟫ metres under Model B. That scenario lowers the yearly balance of rain less evaporation by ⟪outputs/50_record_length/50_report_numbers.csv|projection_2050s_annual_wb_shift_mm_yr|dp0 abs⟫ millimetres, about as much as the dry decade of 1989--96 fell below the modern record (⟪outputs/50_record_length/50_report_numbers.csv|ccw_epoch_annual_wb_shift_mm_yr|dp0 abs⟫ millimetres). So this projection sits inside the range that the look back has tested.

In the 2080s the fall is ⟪outputs/50_record_length/50_report_numbers.csv|projection_2080s_summer_fall_median_at_project|dp2 abs⟫ metres under Model A at the study's floor, ⟪outputs/50_record_length/50_report_numbers.csv|projection_2080s_summer_fall_median_at_supported|dp2 abs⟫ at ⟪outputs/50_record_length/50_report_numbers.csv|datum_ccw_supported_m|dp1⟫ metres and ⟪outputs/50_record_length/50_report_numbers.csv|projection_2080s_summer_fall_median_model_b|dp2 abs⟫ under Model B. That scenario lowers the balance by ⟪outputs/50_record_length/50_report_numbers.csv|projection_2080s_annual_wb_shift_mm_yr|dp0 abs⟫ millimetres a year, more than anything in the record, so this is an extrapolation. It is reported as the range between the two versions, not as one figure. That range is the honest statement of what a model fitted to water levels alone can say about a climate it has not seen.

In both periods the fall is larger in summer than over the year, and larger under Model A, whose slower recession carries the summer deficit forward. The main forest is not projected, because its drainage number cannot be worked out from the record.

# 5. What the numbers mean

## 5.1 Two time scales from one number

In both versions the drainage coefficient sets a time scale, the **e-folding time**: how long it takes a disturbance to shrink to about a third of its size. But the two versions measure it from different levels, so they answer different questions. In Model A it is a **recession time**: how long the water stored above the floor would take to fall to about a third if rain and evaporation stopped. In Model B it is a **return time**: how quickly a wet or dry spell dies away while the climate carries on. The recession time depends on where the floor is set; the return time does not. At the median well the recession time under Model A is ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_A_months_median_all|dp1⟫ months and the return time under Model B is ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_B_months_median_all|dp1⟫.

## 5.2 A check that uses no model

The return time can be measured without either model. Take each month's level less the usual level for that calendar month, and ask how much of an unusual month is still there the month after. Over the whole record the model-free answer is a return time of ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_obs_months_median_all|dp1⟫ months at the median well. That is close to Model B and about a third of Model A.

Group by group, Model B sits with it: at the lake edge ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_B_months_median_C1|dp1⟫ months against ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_obs_months_median_C1|dp1⟫ measured, and under the coastal forest ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_B_months_median_C5|dp1⟫ against ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_obs_months_median_C5|dp1⟫. Under the main forest the measured time is ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_obs_months_median_C4|dp1⟫ months and Model B's drainage number cannot be worked out. The model-free check was repeated with two corrections that push in opposite directions. Taking out any long-term trend in a well's record, the model-free time is ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_obs_detr_months_median_all|dp1⟫ months. Allowing for small errors in the readings, it is ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_obs_yw_months_median_all|dp1⟫ months, a model-free figure too. With either, Model B stays the nearer version at every group where it can be worked out.

## 5.3 Does a dry year carry over to the next spring?

A short return time means that one spring's level says little about the next. If the drainage term is right, the link from one spring to the next should be ⟪outputs/50_record_length/50_report_numbers.csv|reclen_rho_ar1_expected_full_B_median_all|dp2⟫ at the median well under Model B and ⟪outputs/50_record_length/50_report_numbers.csv|reclen_rho_ar1_expected_full_A_median_all|dp2⟫ under Model A, on a scale where 0 means no link. The readings give ⟪outputs/26_van_willegen_msl/26_report_numbers.csv|rho_lag1_median|dp2⟫: successive springs are close to independent. Taken at face value, Model A would make a five-year average of spring levels a poorly averaged quantity, and the record does not support that.

## 5.4 What the floor decides in Model A

The paper refitted Model A at every floor depth from ⟪src/utils/config.py|DATUM_SWEEP_MIN_M|dp1⟫ to ⟪src/utils/config.py|DATUM_SWEEP_MAX_M|dp0⟫ metres down.

**Too shallow, and the model cannot tell.** Shallower than ⟪outputs/03_state_space_model/03_18_datum_invariance.csv|all clusters · all_beta3_pos_sig_from_m|dp1⟫ metres the floor sits inside the range the water table moves through, and at some groups the model cannot work out a drainage rate at all. The paper calls this depth the **identification floor**.

**What fitting alone would choose.** The floor that fits each group best differs from group to group, from ⟪outputs/03_state_space_model/03_18_datum_invariance.csv|C1 (Lake Edge) · aic_optimal_datum_m|dp1⟫ metres at the lake edge to ⟪outputs/03_state_space_model/03_18_datum_invariance.csv|C4 (Main Forest) · aic_optimal_datum_m|dp1⟫ under the main forest. At every group it matches, within one step of the sweep, the floor that Model B works out for itself. So choosing the floor by fit alone turns Model A into Model B, and gives an answer about how quickly the water table returns to normal, not about drainage.

**Deep enough, and the water budget settles.** Below the identification floor the drainage coefficient keeps getting smaller as the floor goes deeper, but the *amount* of water draining each month hardly changes: at ⟪src/utils/config.py|DRAINAGE_DATUM|dp1⟫ metres it is ⟪outputs/03_state_space_model/03_report_numbers.csv|partition_drainage_flux_ratio_datum_to_deepest · C4 (Main Forest) · 3.7 m / 8 m|dp2⟫ to ⟪outputs/03_state_space_model/03_report_numbers.csv|partition_drainage_flux_ratio_datum_to_deepest · C1 (Lake Edge) · 3.7 m / 8 m|dp2⟫ of its value at the deepest floor tried. The paper calls this steady range the **plateau**. The recession time keeps scaling with the floor, so it must always be reported as depending on it. The study uses a single floor of ⟪src/utils/config.py|DRAINAGE_DATUM|dp1⟫ metres for every well, which lies on the plateau and below the range of the water table everywhere.

## 5.5 Can the floor be tied to something physical?

Is the floor a fixed height, the same everywhere, or a depth below ground that follows the shape of the land? A common height fits slightly worse than a depth at every level tried, and higher levels leave the drainage term unidentified at many wells. So the study uses depth.

At a coastal site the most defensible floor is the level the aquifer finally drains to. Each well was refitted with its floor at its depth to mean high water (⟪outputs/01b_water_table/01b_report_numbers.csv|tide_mhw_m|dp2⟫ metres above Ordnance Datum), which puts the floors between ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_datum_mhw_min_all|dp1⟫ and ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_datum_mhw_max_all|dp1⟫ metres below ground. This gives the same water budget (⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_drainage_share_M_median_all|dp0 x100⟫ % drainage at the typical well, against ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_drainage_share_A_median_all|dp0 x100⟫ % with the ⟪src/utils/config.py|DRAINAGE_DATUM|dp1⟫-metre floor). But it is the worse forecaster. In Model A the recession time roughly doubles, to ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_M_months_median_all|dp0⟫ months against ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_A_months_median_all|dp0⟫ at the study's floor, when the model-free time is ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_efold_obs_months_median_all|dp1⟫. The forecast skill falls to ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_fwd_M_median_all|dp2⟫ looking forward, against ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_nse_fwd_A_median_all|dp2⟫. A physical floor answers the objection that one depth is arbitrary, because the budget is the same. It is not adopted, because the dynamics are worse.

A single common height, tried as a forecaster, looks back at the dry decade better but forecasts the modern record worse (a skill of ⟪outputs/50_record_length/50_report_numbers.csv|e16_split_nse_median_at_best|dp2⟫ against ⟪outputs/50_record_length/50_report_numbers.csv|e16_split_nse_median_at_depth|dp2⟫), and one more well loses its drainage term. The medians hide a split by group: it helps most of the Western Residual wells and fails at the open-dune wells. Under one common base the return time is short near the coast and long inland. A drainage path to a coastal base would predict that pattern, but Model A produces it mechanically too, so the fit cannot tell the two apart. It is not adopted. The level the aquifer drains to varies within groups as well as between them, which is why a floor that follows the ground serves every group.

## 5.6 Why Model B does not set the floor

Model B pays for its fit. Its constant and its drainage number are almost interchangeable: their estimates correlate at ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_corr_alpha_beta_3_B_median_all|dp2⟫ at the median well. So the level its drainage refers to is fitted rather than physical, and lies near each well's own average, a median ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_base_depth_B_m_median_all|dp1⟫ metres below ground, at the identification floor. With it, more of the loss is booked to evaporation and plant use: a drainage share of ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_drainage_share_B_median_all|dp0 x100⟫ % against Model A's ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_drainage_share_A_median_all|dp0 x100⟫ %. That is the split the paper quotes. It follows from the rain and evaporation numbers, which Model B identifies and Pastas reproduces, and a constant that absorbs the floor leaves it the same at every floor. Using Model B's base as the floor would simply make Model A identical to Model B.

Pastas, fitted to the same wells on the full record, agrees with Model B well by well: rank correlations of ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|pastas_vs_ssmB_beta_1_recharge_rho_identified_full|dp2⟫, ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|pastas_vs_ssmB_beta_2_atmospheric_draw_rho_identified_full|dp2⟫ and ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|pastas_vs_ssmB_beta_3_drainage_rho_identified_full|dp2⟫ for the rain, evaporation and drainage numbers, on the ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|pastas_n_identified_full_record|dp0⟫ wells for which Pastas works out a response time. That agreement is expected: it checks the implementation, not the model.

# 6. A checklist for other sites

For a site with a monthly water-level record and no direct measurement of where the water goes, the paper's procedure comes down to these steps.

1.  Fit both versions, with and without the constant, at the scale at which the results will be used: each well, or each group of wells that rise and fall together. For the version without the constant, try the floor at many depths and choose one on the plateau, below the range the water table occupies.
2.  Test what the drainage term adds. Run each version freely from the first observed level and compare it with the same model without drainage.
3.  Test forecasts within the record. Fit on one part and run freely over the other, in both directions. Use the version that wins, at Newborough Model B, to forecast within the climate the record spans.
4.  Test against a different climate wherever an older record exists, even a few wells or a few years. Use the version it supports for projections, with the other beside it, and report the pair, not an average.
5.  Check the record is long enough. Refit on shorter stretches and see when the drainage number stops moving. The record should span several return times.
6.  Check the time scale without a model, and report the return time as how quickly the water table recovers, not the recession time, which depends on the floor.
7.  Treat the numbers as coefficients, not as flows of water. Report the split of the loss between drainage and evaporation as depending on the floor, or not at all.
8.  Say which stretch of record every result comes from, and fill gaps in a well's record from measured neighbours rather than from the model.

# 7. What the record cannot tell us

## 7.1 What water levels alone can and cannot give

A model fitted to water levels can always balance the average books, because the level records the net of what comes in and goes out. What it can be trusted to forecast depends on the test it has passed. Within the recorded climate, the test on held-back years and the time scale measured without a model agree on Model B. Beyond it, only an independent record can say, and here it favours Model A. Someone forecasting next year's spring level and someone projecting the 2080s should not use the same version, and should know why.

What water levels alone cannot give is the split of the loss between evaporation and drainage. Model A answers with an assumption and Model B with a fitted resting level, and the two answers differ (⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_drainage_share_A_median_all|dp0 x100⟫ against ⟪outputs/48_pastas_crosscheck/48_report_numbers.csv|modelab_drainage_share_B_median_all|dp0 x100⟫ % drainage at the median well). Only an independent measurement of a flow, from tracers, outflow gauging or eddy covariance, can settle it. The scientific literature often calls the drainage number a "memory". Neither reading is a memory, and the two differ by more than a factor of two.

## 7.2 These are properties of this aquifer

The identification floor, Model B's resting level and the plateau are properties of the water-table depths at Newborough, not general constants. At another site the depth sweep must be repeated, not the numbers reused, and so must the record length each version needs.

## 7.3 Relation to common practice

Transfer-function models such as Pastas estimate the Model B form. That is the right form for forecasting within the recorded climate. What this practice does not usually do is test a forecast against a different climate, and at this site that test reverses the ranking.

## 7.4 Limits

The weather comes from one station outside the site, at monthly resolution, and the evaporation figure is an index of demand rather than a measured flow. The model is straight-line and unchanging in time, and the projections assume its numbers hold under a climate the record has not seen, which the look-back tests reach only as far as the 2050s. Under the main forest, Model B's drainage number cannot be worked out. A slow response is one reading of that, and a forcing that misrepresents the forest's evaporation is another, and the record does not tell them apart. The independent tests of the lasting response rest on ⟪outputs/39_ccw_hindcast/39_report_numbers.csv|n_wells_admitted|dp0⟫ wells in one decade and three approximately placed sites in another.

# 8. In short

A model fitted to a monthly water-level record can forecast that record's water table, but which version can be trusted depends on what is being forecast. Within the climate the record spans, the version with a free constant (Model B) forecasts better, needs only a few years of record, and measures the time the water table takes to return to its usual level, which a measurement that uses no model confirms. Against a drier decade that no fit had seen, the version without the constant (Model A), with its floor on the plateau, reproduces the lasting shift of the level, and Model B does not.

Projections into a changed climate should therefore use the version an independent record supports, with the other beside it, and report the pair. At Newborough, under a high-emissions climate, the two versions put the typical fall of the summer water level at ⟪outputs/50_record_length/50_report_numbers.csv|projection_2050s_summer_fall_median_model_b|dp2 abs⟫--⟪outputs/50_record_length/50_report_numbers.csv|projection_2050s_summer_fall_median_at_project|dp2 abs⟫ metres in the 2050s, inside the range the look back has tested, and ⟪outputs/50_record_length/50_report_numbers.csv|projection_2080s_summer_fall_median_model_b|dp2 abs⟫--⟪outputs/50_record_length/50_report_numbers.csv|projection_2080s_summer_fall_median_at_project|dp2 abs⟫ metres in the 2080s, beyond it. The main forest is withheld, because its drainage number cannot be worked out from the record.

The numbers themselves are not flows of water. The split of the loss between drainage and evaporation depends on the floor, and the recession time describes the floor as much as the aquifer. Each quantity should be taken from the version that identifies it, with the stretch of record declared and the tests repeated at every site.

# Glossary

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

# Further reading

Hollingham, M. (2026) Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you. In preparation.

Ranwell, D.S. (1959) Newborough Warren, Anglesey. I. The dune system and dune slack habitat. *Journal of Ecology* 47(3), 571--601.

The project's data, analysis and documents: https://github.com/newbroman/Newborough_Hydrology
