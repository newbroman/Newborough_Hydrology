What monthly water levels can tell us: a plain-language guide to the methods paper

M. Hollingham

November 2026

This guide explains, without equations, a scientific paper about whether a simple groundwater model fitted to monthly water levels can be trusted to forecast: *Intercept, datum and record: what a linear-reservoir model fitted to monthly groundwater levels can tell you* (Hollingham, 2026). It follows the paper section by section, with the same section numbers. Every number in it is taken from the same project files as the paper, so the two always agree. Words in **bold** on first use are explained in the glossary at the end.

# 1. Why this matters

Dune slacks, the damp hollows between sand dunes, are among the richest wildlife habitats on the coast, and they depend on groundwater. How wet a slack is in spring and how far the water falls in summer decide which plants and animals can live there.

At most sites the only record of that groundwater is a set of shallow pipes, called **dipwells**, in which someone measures the water level by hand about once a month. Newborough Warren on Anglesey has {{wells_classified_n_dp0}} of them across {{study_area_ha_dp0}} hectares of dunes and pine forest, and some have been read for over twenty years.

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

-   In **Model A** the floor is chosen in advance. The study uses a single depth of {{DRAINAGE_DATUM_dp1}} metres for every well.
-   In **Model B** the model adds a constant to the sum and so finds its own floor, wherever the record puts it.

The two are one model family, separated only by where the floor comes from: Model B is Model A with the floor moved to the level at which the fitted drainage is zero.

The drainage coefficient means something different in each. In Model A it describes water draining towards the chosen floor, so its value changes if the floor is moved. In Model B it describes how quickly the water table returns to its own normal level after a wet or dry spell, and that does not depend on any floor.

Leaving drainage out altogether gives the simplest model of all, the **traditional linear model**: rain in, evaporation out, nothing else. Run forward on its own, it has nothing pulling the water table back towards a usual level, so each month's error is carried into every month after it.

## A check against widely used software

Pastas is widely used software that does the same job. Model B is exactly what Pastas fits, written one month at a time, and each term in one has a match in the other. So when the two agree, that shows the code is right. It is not independent evidence that either version is right. Model A has no match in Pastas, which has no fixed floor.

## What neither version can decide

The water table loses water in two ways: by drainage, and by evaporation and plant use. The levels alone cannot say how the loss splits between them, because the split depends on the level that drainage is measured from. Model A sets that level by assumption and Model B by fit. Without a direct measurement of drainage, evaporation or recharge, neither can fix the true split.

Model A's split has a further weakness. Evaporation from a shallow water table also eases as the water table deepens, so it varies with the level as drainage does, and the fit counts it as drainage. Model A's drainage share therefore leans high, and the paper reports it only as depending on the floor. A forecast does not need the split: it needs the model's numbers working together, not each flux apart.

# 3. The site, the record and the wells

Newborough Warren is a coastal dune system of {{study_area_ha_dp0}} hectares. The {{wells_classified_n_dp0}} dipwells are read at the end of each month. Monthly rainfall and evaporating power come from one weather station, RAF Valley, {{raf_valley_distance_km_dp0}} km away.

The study uses a reference network of {{reference_n_wells_dp0}} wells: those with at least {{LCSC_DATA_LIMIT_dp0}} months of record that are still being read at the end of it. Their records are longer than that minimum, with a median of {{reference_record_months_median_dp0}} months (from {{reference_record_months_min_dp0}} to {{reference_record_months_max_dp0}}).

The wells fall into five groups that rise and fall together, found from the shape of their records before any model was fitted. Three groups are open dune (the Lake Edge, the Dune and the Western Residual) and two are under pine (the Main Forest and the Coastal Forest). The groups are stable when wells or months are left out at random. But groups built separately from two halves of the record agree only moderately (a score of {{cluster_splithalf_ari_mean_dp2}} on a scale where 1 is identical). So the five groups are a useful way of dividing one continuous aquifer, not sharply bounded units.

The numbers a study reports belong to the stretch of record they were fitted on, and in a network installed step by step that stretch is not the same everywhere. The paper therefore uses two bases and says which applies to every result. One is the average hydrograph of each group, fitted on every month available. The other is each well on its own, either on its full record or on a common window, the most recent {{LCSC_DATA_LIMIT_dp0}} months at every well, so that wells are compared under the same weather. The tests that split the record fit each well on the years before January 2018 and test it on the years after.

# 4. Can the record forecast?

## 4.1 What the drainage term adds

At each well, three models were fitted on the common window: the traditional linear model, Model A and Model B. Each was then run freely over the same months, starting from the first observed level and working out each month from the model's own previous month, never from the readings. That is a hard test: it asks whether a model can reproduce the course of the water table without being corrected by it.

Results are scored with the **forecast skill**, on a scale where 1 is perfect, 0 is no better than the average level, and below 0 is worse. Across {{benchmark_n_wells_dp0}} wells the traditional linear model scores {{benchmark_median_NSE_TLM_dp2}} at the median well, and at {{benchmark_negative_NSE_TLM_dp0}} wells it does worse than simply guessing the average. Add the drainage term and the median rises: to {{benchmark_median_NSE_ModelB_dp2}} for Model B, positive at all {{benchmark_positive_NSE_ModelB_dp0}} wells, and to {{benchmark_median_NSE_SSM_dp2}} for Model A, positive at {{benchmark_positive_NSE_SSM_dp0}}. If the models are instead corrected each month by the reading, the traditional model and Model A are indistinguishable: the reading supplies the return that the traditional model lacks.

The gain is largest where drainage is fastest, at the lake edge. The pine forest is the exception, because drainage there is slow and the traditional model's build-up of error does least harm. At one forest well, CEH14, Model A's drainage coefficient is negative and its free run diverges (a skill of {{CEH14_SSM_NSE_dp2}}, against {{CEH14_TLM_NSE_dp2}} for the traditional model), while Model B scores {{CEH14_ModelB_NSE_dp2}}. A model without drainage cannot forecast. But where a fixed floor leaves the drainage term unidentified, the term can cost more than it adds.

## 4.2 Forecasting within the recorded climate

Each version was fitted on the record before January 2018 and run freely over the years after, and then the test was run the other way round. Looking forward, Model B's median skill is {{modelab_nse_fwd_B_median_all_dp2}} against {{modelab_nse_fwd_A_median_all_dp2}} for Model A, and Model B is better at {{modelab_nse_fwd_share_B_better_all_x100_dp0}} % of wells. Looking back, Model B scores {{modelab_nse_rev_B_median_all_dp2}} against {{modelab_nse_rev_A_median_all_dp2}}, and is better at {{modelab_nse_rev_share_B_better_all_x100_dp0}} % of wells. The advantage is clearest in the open dune. Under the coastal forest the two are close.

Under the main forest both forecast poorly: Model B scores {{modelab_nse_fwd_B_median_C4_dp2}} and Model A {{modelab_nse_fwd_A_median_C4_dp2}}. The split at January 2018 falls a month after the December 2017 clearfell beside the main forest, so those forecasts are scored over years in which the canopy changed.

## 4.3 Forecasting into a different climate

A forecast inside the modern record is dominated by the yearly swing. A changing climate asks something else of the model: a lasting shift in the level. The one test of that which no fit has seen is the Countryside Council for Wales record of 1989--96, read before the present network was installed, at {{n_wells_admitted_dp0}} wells that are still read today. That decade was drier than anything in the modern record.

Run back over that decade from the fit to each well's whole modern record, Model A is close to unbiased: its water level is off by {{reclen_ccw_bias_m_A_median_Lfull_all_dp2}} metres at the median well. Model B puts the water table too high by {{reclen_ccw_bias_m_B_median_Lfull_all_dp2}} metres. Both forecast skills are below zero ({{reclen_ccw_nse_A_median_Lfull_all_dp2}} for Model A and {{reclen_ccw_nse_B_median_Lfull_all_dp2}} for Model B), because the monthly errors are bigger than the spread of the readings about their own 1989--96 average, and that average is exactly the shift the test asks the model to find. So on this test it is the bias, not the skill score, that separates the two. The ordering holds at every record length tried. The two tests split by what they score: a fast return follows the yearly swing well, and the lasting shift is what Model A carries and Model B does not.

The same decade can be asked which floor Model A should use. Refitting at every depth, the floor that fits the dry decade best is {{datum_ccw_supported_m_dp1}} metres (with a band from {{datum_ccw_band_min_m_dp1}} to {{datum_ccw_band_max_m_dp1}}), where the median skill is {{datum_ccw_nse_median_at_D2_9_dp2}}, against {{datum_ccw_nse_median_at_D3_7_dp2}} at the study's {{DRAINAGE_DATUM_dp1}} metres. Floors deeper than the study's do worse on every measure, so the dry decade does not ask for a deeper floor. The study's floor lies a little below the supported band, but its bias on the same fits is only {{reclen_ccw_bias_m_A_median_L100_end_dp2}} metres.

A second old record is Derek Ranwell's readings of 1951--53 at three places on the Warren. Their exact positions are uncertain, so his average level cannot be trusted, and the test uses only the *seasonal rise and fall*. By the same rule it supports a floor of {{datum_ranwell_supported_m_dp1}} metres (band {{datum_ranwell_band_min_m_dp1}} to {{datum_ranwell_band_max_m_dp1}}), and there Model A behaves as Model B does: both score {{ranwell_nse_median_at_supported_dp2}}, against {{ranwell_nse_median_at_project_dp2}} for the study's {{DRAINAGE_DATUM_dp1}}-metre floor. That {{datum_ranwell_supported_m_dp1}} metres is not a water level or an error. It is the floor depth that makes Model A fast enough to follow the seasons, which is how Model B behaves anyway.

The two old records disagree because they score different things. With its average removed, Ranwell's record tests only the yearly swing, which a fast return follows and which Model A reproduces only with a shallow floor. The dry decade tests a lasting shift of the average, which the deeper floor carries.

Why Ranwell's swing differs was explored after the comparison, so the paper describes it rather than tests it. His readings ask for a weaker response to rain, a stronger pull from evaporation and faster drainage than today's numbers give, and the seasonal swing then was {{ranwell_epoch_swing_smaller_pct_min_dp0}}--{{ranwell_epoch_swing_smaller_pct_max_dp0}} % smaller, relative to the model, than it is now. Ordinary weather, carry-over from earlier years, Ranwell's own rain gauge, the depth of his pipes, a barer rabbit-grazed dune, the forest planted since and a slightly lower sea each fail to supply it. Drains dug for the young plantation, and a lower outlet from Llyn Rhos-Ddu, point the right way, but neither is recorded.

The two old records seem to ask for two speeds: a quick return, and a slow hold that keeps the level down through a drier decade. A single store has only one. So a second, slower store was tried at every group, including one drawn down by the pine plantation as its canopy closed. No version passed the tests fixed before the fit: either one store was preferred, or the slow store forecast worse after 2018. At Newborough a model fitted to water levels alone has one speed, and which version is used decides which.

## 4.4 How much record a forecast needs

Within the modern record, Model B forecasts better at every length of fit. Fitted on only {{RECLEN_MIN_FIT_MONTHS_dp0}} months before 2018, its median skill is already {{reclen_nse_fwd_B_median_L24_all_dp2}}, and it reaches {{reclen_nse_fwd_B_median_Lfull_all_dp2}} with all of them. Model A starts at {{reclen_nse_fwd_A_median_L24_all_dp2}}, reaches {{reclen_nse_fwd_A_median_L100_all_dp2}} at {{LCSC_DATA_LIMIT_dp0}} months and {{reclen_nse_fwd_A_median_Lfull_all_dp2}} with all of them. A site with a few years of record can forecast its own water table with Model B.

The drainage numbers need more. Each well's drainage coefficient was refitted on shorter and shorter stretches, and the length at which it settles was taken as the shortest record on which it lies within {{RECLEN_STABLE_TOL_x100_dp0}} % of the full-record value. Model A's is the more robust: about {{reclen_stable_length_months_A_median_all_dp0}} months at a typical well, which was the shortest length tried and so may be too long, reached at {{reclen_stable_n_wells_reached_A_all_dp0}} wells. Model B's is {{reclen_stable_length_months_B_median_all_dp0}} months ({{reclen_stable_n_wells_reached_B_all_dp0}} wells), and on only {{reclen_identified_share_B_median_L24_all_x100_dp0}} % of {{RECLEN_MIN_FIT_MONTHS_dp0}}-month stretches can its drainage number be worked out at all. Counted in each well's own return times, the stable length is {{reclen_stable_length_in_efolds_A_median_all_dp1}} for Model A and {{reclen_stable_length_in_efolds_B_median_all_dp1}} for Model B. A rule of thumb follows: a record should span several return times before the return time read from it is trusted, and the rule binds Model B harder.

The forest is the exception for both. Under the main forest Model A needs {{reclen_stable_length_months_A_median_C4_dp0}} months and Model B {{reclen_stable_length_months_B_median_C4_dp0}}, and Model B settles within the lengths tried at only {{reclen_stable_n_wells_reached_B_C4_dp0}} of its wells. Fitting the common window instead of the full record shifts the main forest's drainage number by {{C4_Main_Forest_comparison_window_beta_3_pct_vs_full_record_dp0_plus}} %, against {{C1_Lake_Edge_comparison_window_beta_3_pct_vs_full_record_dp0_plus}} % or less elsewhere. Pastas tells the same story: the wells whose response time it cannot work out on the window are mainly forest wells ({{pastas_n_not_identified_C4_comparison_window_dp0}} of them under the main forest).

## 4.5 Per well, or per group?

The groups come from the shape of the hydrographs alone, so a new well can be placed in one by comparing its record with the group averages, without fitting it. Lending it the group's numbers then rests on two things: that a short record places the well correctly, and that the group's numbers forecast as well as its own. The paper tests the second. Each skill test was run twice, once on each well's own numbers and once on its group's, and the group's basis counted as holding if its median skill was within {{BASIS_TOL_NSE_dp2}} of the well's own or better, and, for the dry decade, its typical error in the level within {{BASIS_TOL_BIAS_M_dp2}} metres or smaller. The rule was fixed before the run.

With Model A the group numbers pass all three tests. On the dry decade their median skill is {{basis_ccw_nse_median_cluster_A_dp2}} against {{basis_ccw_nse_median_well_A_dp2}} for the wells' own, and their typical error {{basis_ccw_absbias_median_cluster_A_dp2}} metres against {{basis_ccw_absbias_median_well_A_dp2}}. Both skills are below zero, so on that test the comparison rests mainly on the error. Forecasting forward from January 2018, the group numbers score {{basis_split_nse_median_cluster_A_fwd_dp2}} against {{basis_split_nse_median_well_A_fwd_dp2}}. Model B passes all three too, and on the dry decade does much better with the group's numbers ({{basis_ccw_nse_median_cluster_B_dp2}} against {{basis_ccw_nse_median_well_B_dp2}}). Within the tolerances set before the run, group numbers forecast and look back as well as each well's own.

Where a well's own record has a gap, it is better filled from a measured neighbour than from the model. With stretches of {{GAPFILL_HOLDOUT_MONTHS_dp0}} months hidden in turn, each well's average spring level was put back from its nearest neighbour in the same group with a typical miss of {{gapfill_pooled_nearest_cluster_excluded_msl_abs_err_median_dp3}} metres, against {{gapfill_pooled_ssm_model_a_excluded_msl_abs_err_median_dp3}} metres from Model A run on the weather.

## 4.6 Which form to forecast with

Within the climate the record spans, use Model B: it forecasts better, needs only a few years of record, and its return time is the one the record supports (Section 5). A forecast into a different climate, whether a look back at a drier past or a projection, asks for a lasting shift of the level, and there the one independent test favours Model A. So forward runs into a changed climate use Model A at the study's floor, with Model B beside it as the fast-return bound. The two are reported as a pair on the same wells and never averaged, and the floor that the dry decade supports is carried as a check. Neither version serves a quantity it cannot work out. That is why the main forest is withheld from projection.

## 4.7 What the record projects

The paper takes the Met Office's high-emissions climate scenario (UKCP18), applied as seasonal changes to the observed rain and evaporating power, with fits on the common window at the {{projection_2050s_n_wells_pair_dp0}} wells for which both versions work.

In the 2050s, the typical lasting fall of the summer water level is {{projection_2050s_summer_fall_median_at_project_abs_dp2}} metres under Model A at the study's floor, {{projection_2050s_summer_fall_median_at_supported_abs_dp2}} metres under Model A at {{datum_ccw_supported_m_dp1}} metres, and {{projection_2050s_summer_fall_median_model_b_abs_dp2}} metres under Model B. That scenario lowers the yearly balance of rain less evaporation by {{projection_2050s_annual_wb_shift_mm_yr_abs_dp0}} millimetres, about as much as the dry decade of 1989--96 fell below the modern record ({{ccw_epoch_annual_wb_shift_mm_yr_abs_dp0}} millimetres). So this projection sits inside the range that the look back has tested.

In the 2080s the fall is {{projection_2080s_summer_fall_median_at_project_abs_dp2}} metres under Model A at the study's floor, {{projection_2080s_summer_fall_median_at_supported_abs_dp2}} at {{datum_ccw_supported_m_dp1}} metres and {{projection_2080s_summer_fall_median_model_b_abs_dp2}} under Model B. That scenario lowers the balance by {{projection_2080s_annual_wb_shift_mm_yr_abs_dp0}} millimetres a year, more than anything in the record, so this is an extrapolation. It is reported as the range between the two versions, not as one figure. That range is the honest statement of what a model fitted to water levels alone can say about a climate it has not seen.

In both periods the fall is larger in summer than over the year, and larger under Model A, whose slower recession carries the summer deficit forward. The main forest is not projected, because its drainage number cannot be worked out from the record.

# 5. What the numbers mean

## 5.1 Two time scales from one number

In both versions the drainage coefficient sets a time scale, the **e-folding time**: how long it takes a disturbance to shrink to about a third of its size. But the two versions measure it from different levels, so they answer different questions. In Model A it is a **recession time**: how long the water stored above the floor would take to fall to about a third if rain and evaporation stopped. In Model B it is a **return time**: how quickly a wet or dry spell dies away while the climate carries on. The recession time depends on where the floor is set; the return time does not. At the median well the recession time under Model A is {{modelab_efold_A_months_median_all_dp1}} months and the return time under Model B is {{modelab_efold_B_months_median_all_dp1}}.

## 5.2 A check that uses no model

The return time can be measured without either model. Take each month's level less the usual level for that calendar month, and ask how much of an unusual month is still there the month after. Over the whole record the answer gives a return time of {{modelab_efold_obs_months_median_all_dp1}} months at the median well. That is close to Model B and about a third of Model A.

Group by group, Model B sits with it. At the lake edge it is {{modelab_efold_B_months_median_C1_dp1}} months against {{modelab_efold_obs_months_median_C1_dp1}} measured, in the open dune {{modelab_efold_B_months_median_C2_dp1}} against {{modelab_efold_obs_months_median_C2_dp1}}, in the Western Residual {{modelab_efold_B_months_median_C3_dp1}} against {{modelab_efold_obs_months_median_C3_dp1}}, and under the coastal forest {{modelab_efold_B_months_median_C5_dp1}} against {{modelab_efold_obs_months_median_C5_dp1}}. Under the main forest the measured time is {{modelab_efold_obs_months_median_C4_dp1}} months and Model B's drainage number cannot be worked out. The check was repeated with two corrections that push in opposite directions: taking out any long-term trend in a well's record ({{modelab_efold_obs_detr_months_median_all_dp1}} months), and allowing for small errors in the readings ({{modelab_efold_obs_yw_months_median_all_dp1}} months). With either, Model B stays the nearer version at every group where it can be worked out.

## 5.3 Does a dry year carry over to the next spring?

A short return time means that one spring's level says little about the next. If the drainage term is right, the link from one spring to the next should be {{reclen_rho_ar1_expected_full_B_median_all_dp2}} at the median well under Model B and {{reclen_rho_ar1_expected_full_A_median_all_dp2}} under Model A, on a scale where 0 means no link. The readings give {{rho_lag1_median_dp2}}: successive springs are close to independent. Taken at face value, Model A would make a five-year average of spring levels a poorly averaged quantity, and the record does not support that.

## 5.4 What the floor decides in Model A

The paper refitted Model A at every floor depth from {{DATUM_SWEEP_MIN_M_dp1}} to {{DATUM_SWEEP_MAX_M_dp0}} metres down.

**Too shallow, and the model cannot tell.** Shallower than {{all_clusters_all_beta3_pos_sig_from_m_dp1}} metres the floor sits inside the range the water table moves through, and at some groups the model cannot work out a drainage rate at all. The paper calls this depth the **identification floor**.

**What fitting alone would choose.** The floor that fits each group best differs from group to group, from {{C1_Lake_Edge_aic_optimal_datum_m_dp1}} metres at the lake edge to {{C4_Main_Forest_aic_optimal_datum_m_dp1}} under the main forest. At every group it matches, within one step of the sweep, the floor that Model B works out for itself. In other words, choosing the floor by fit alone turns Model A into Model B, and gives an answer about how quickly the water table returns to normal, not about drainage.

**Deep enough, and the water budget settles.** Below the identification floor the drainage coefficient keeps getting smaller as the floor goes deeper, but the *amount* of water draining each month hardly changes. At {{DRAINAGE_DATUM_dp1}} metres it is {{partition_drainage_flux_ratio_datum_to_deepest_C4_Main_Forest_3_7_m_8_m_dp2}} to {{partition_drainage_flux_ratio_datum_to_deepest_C1_Lake_Edge_3_7_m_8_m_dp2}} of its value at the deepest floor tried, depending on the group. The paper calls this steady range the **plateau**. On it, the ranking of the groups' numbers and the water budget do not depend on the floor, though the recession time keeps scaling with it and must be reported as depending on it.

The study uses a single floor of {{DRAINAGE_DATUM_dp1}} metres for every well. It lies on the plateau for the deepest group and below the range of the water table everywhere. Against each group's own best floor it costs {{C1_Lake_Edge_delta_AIC_datum_vs_optimum_dp1}} points of a standard fit score at the lake edge, where the water table is shallowest, and almost nothing under the forest.

## 5.5 Can the floor be tied to something physical?

**Height above sea level, or depth below ground?** Is the floor one fixed height, the same everywhere, or does it follow the shape of the ground? A common height fits slightly worse than a depth at every level tried (a typical fit of {{datum_aod_r2_median_at_optimum_dp3}} against {{datum_aod_r2_median_depth_datum_dp3}}), and higher levels leave the drainage term unidentified at many wells. So the study uses depth.

**A floor set by the sea.** At a coastal site the most defensible floor is the level the aquifer finally drains to. Each well was refitted with its floor at its depth to mean high water ({{tide_mhw_m_dp2}} metres above Ordnance Datum), which puts the floors between {{modelab_datum_mhw_min_all_dp1}} and {{modelab_datum_mhw_max_all_dp1}} metres below ground. This gives the same water budget ({{modelab_drainage_share_M_median_all_x100_dp0}} % drainage at the typical well, against {{modelab_drainage_share_A_median_all_x100_dp0}} % with the {{DRAINAGE_DATUM_dp1}}-metre floor), because almost every well's depth to high water lies on the plateau. But it is the worse forecaster. The return time roughly doubles, to {{modelab_efold_M_months_median_all_dp0}} months against {{modelab_efold_A_months_median_all_dp0}} at {{DRAINAGE_DATUM_dp1}} metres and {{modelab_efold_obs_months_median_all_dp1}} measured, and the forecast skill falls to {{modelab_nse_fwd_M_median_all_dp2}} looking forward and {{modelab_nse_rev_M_median_all_dp2}} looking back, against {{modelab_nse_fwd_A_median_all_dp2}} and {{modelab_nse_rev_A_median_all_dp2}}. A physical floor answers the objection that one depth is arbitrary, because the budget is the same. It is not adopted, because the dynamics are worse.

**One common height as a forecaster.** The paper also fitted Model A with each well's floor at its height above one common base, anywhere between {{DATUM_AOD_SWEEP_MIN_M_dp0}} and {{DATUM_AOD_SWEEP_MAX_M_dp0}} metres above Ordnance Datum. By the rule fixed before the run, the best base is {{e16_z0_best_m_aod_dp2}} metres, just above mean high water. Against the study's floor on the same wells it looks back at the dry decade better (a median skill of {{e16_ccw_nse_median_at_best_dp2}} against {{e16_ccw_nse_median_at_depth_dp2}}) and follows Ranwell's seasons better ({{e16_ranwell_nse_median_at_best_dp2}} against {{e16_ranwell_nse_median_at_depth_dp2}}, on {{e16_ranwell_n_dp0}} pairings). But it forecasts the modern record worse ({{e16_split_nse_median_at_best_dp2}} against {{e16_split_nse_median_at_depth_dp2}}), and one more well loses its drainage term. It is not adopted.

The medians hide a split by group. In the Western Residual, {{e16_ccw_n_better_at_best_dp0}} of the {{e16_ccw_n_C3_dp0}} dry-decade wells look back better on the common base (median skill {{e16_ccw_nse_median_C3_at_best_dp2}} against {{e16_ccw_nse_median_C3_at_depth_dp2}}), while the {{e16_ccw_n_C2_dp0}} open-dune wells fail (median {{e16_ccw_nse_median_C2_at_best_dp2}} against {{e16_ccw_nse_median_C2_at_depth_dp2}} at the study's floor). Under one common base the return time is short near the coast and long inland (a rank correlation of {{e16_rho_beta3_vs_datum_at_best_dp2}} between the drainage number and the well's height above the base). A drainage path to a coastal base would predict that pattern, but Model A produces it mechanically too, so the fit cannot tell the two apart. A base for each group does no better, and the level the aquifer drains to varies within groups as well as between them. That is why a floor that follows the ground serves every group.

## 5.6 Why Model B does not set the floor

Model B pays for its fit. Its constant and its drainage number are almost interchangeable: their estimates correlate at {{modelab_corr_alpha_beta_3_B_median_all_dp2}} at the median well. So the level its drainage refers to is fitted rather than physical, and lies near each well's own average, a median {{modelab_base_depth_B_m_median_all_dp1}} metres below ground, at the identification floor. With it, more of the loss is booked to evaporation and plant use: a drainage share of {{modelab_drainage_share_B_median_all_x100_dp0}} % against Model A's {{modelab_drainage_share_A_median_all_x100_dp0}} %. That is the split the paper quotes. It follows from the rain and evaporation numbers, which Model B identifies and Pastas reproduces, and a constant that absorbs the floor leaves it the same at every floor. Using Model B's base as the floor would simply make Model A identical to Model B.

Pastas, fitted to the same wells on the full record, agrees with Model B well by well: rank correlations of {{pastas_vs_ssmB_beta_1_recharge_rho_identified_full_dp2}} for the rain number, {{pastas_vs_ssmB_beta_2_atmospheric_draw_rho_identified_full_dp2}} for the evaporation number and {{pastas_vs_ssmB_beta_3_drainage_rho_identified_full_dp2}} for the drainage number, on the {{pastas_n_identified_full_record_dp0}} wells for which Pastas works out a response time. As Section 2 says, that agreement is expected: it checks the implementation, not the model.

# 6. A checklist for other sites

For a site with a monthly water-level record and no direct measurement of where the water goes, the paper's procedure comes down to these steps.

1.  Fit both versions, with and without the constant, at the scale at which the results will be used: each well, or each group of wells that rise and fall together. For the version without the constant, try the floor at many depths and choose one on the plateau, where the amount drained stops changing, below the range the water table occupies.
2.  Test what the drainage term adds. Run each version freely from the first observed level, and compare it with the same model without drainage. A model that drifts without its drainage term cannot forecast.
3.  Test forecasts within the record. Fit on one part and run freely over the other, in both directions. Use the version that wins, at Newborough Model B, to forecast within the climate the record spans.
4.  Test against a different climate wherever an older record exists, even a few wells or a few years. A lasting shift of the level is the nearest test of a changed future. Use the version it supports for projections, with the other beside it, and report the pair, not an average.
5.  Check the record is long enough. Refit on shorter stretches and see when the drainage number stops moving. The record should span several return times, and slow forest wells need much longer.
6.  Check the time scale without a model. Compare each version's e-folding time with the one measured from the readings, and report the return time as how quickly the water table recovers, not the recession time, which depends on the floor.
7.  Treat the numbers as coefficients, not as flows of water. The split of the loss between drainage and evaporation depends on the floor and leans towards drainage where the water table is shallow, so report it as depending on the floor, or not at all.
8.  Say which stretch of record every result comes from, and fill gaps in a well's record from measured neighbours rather than from the model.

# 7. What the record cannot tell us

## 7.1 What water levels alone can and cannot give

A model fitted to water levels can always balance the average books, because the level records the net of what comes in and goes out. What it can be trusted to forecast depends on the test it has passed. Within the recorded climate, the test on held-back years and the time scale measured without a model agree on Model B. Beyond it, only an independent record can say, and here it says something different: the drier decade is reproduced by the slower version, Model A, and a second store driven by the same climate does not reconcile the two. Someone forecasting next year's spring level and someone projecting the 2080s should not use the same version, and should know why.

What water levels alone cannot give is the split of the loss between evaporation and drainage. Model A answers with an assumption about where drainage is measured from and Model B with a fitted resting level, and the two answers differ ({{modelab_drainage_share_A_median_all_x100_dp0}} against {{modelab_drainage_share_B_median_all_x100_dp0}} % drainage at the median well). Only an independent measurement of a flow, from tracers, outflow gauging or eddy covariance, can settle it. Turning shares into millimetres of water would also need how much water the sand releases as the water table falls, which levels alone cannot give.

The scientific literature often calls both readings of the drainage number a "memory": the time a groundwater system takes to settle after a change in recharge, or the persistence of unusual levels. Neither is a memory, and here the two differ by more than a factor of two. Reading persistence through the recession time overstates it, by more the deeper the floor.

## 7.2 These are properties of this aquifer

The identification floor sits near the shallow end of the range of the water table, and Model B's resting level sits on it. Both are properties of the water-table depths at Newborough, not general constants, and so is the plateau, whose start in each group follows that group's average depth to water. At another site the depth sweep must be repeated, not the numbers reused, and the same is true of the record length each version needs.

## 7.3 Relation to common practice

Transfer-function models such as Pastas estimate the Model B form. That is the right form for forecasting within the recorded climate, and its agreement here with the measurement that uses no model, and with the test on held-back years, supports its use. What this practice does not usually do is test a forecast against a different climate, and at this site that test reverses the ranking. The two practices are complementary: the free-resting-level model serves the dynamics within the record, and the fixed-floor model on the plateau, tested against an independent record, serves the lasting response.

## 7.4 Limits

The weather comes from one station outside the site, at monthly resolution. The evaporation figure is an index of demand rather than a measured flow, so its number is an effective one, and Model A's drainage number includes evaporation from the water table as well as drainage. The model is straight-line and unchanging in time; changes in land cover over the record are handled elsewhere. The projections scale the observed climate by seasonal factors and assume the numbers hold under a climate the record has not seen, which the look-back tests reach only as far as the 2050s.

Under the main forest, Model B's drainage number cannot be worked out from the record, which withholds it from forecasts and projections. A slow response is one reading of that, and a forcing that misrepresents the forest's evaporation is another, and the record does not tell them apart. The independent tests of the lasting response rest on {{n_wells_admitted_dp0}} wells in one decade and three approximately placed sites in another, and why the earlier record's swing differs is not resolved.

# 8. In short

A model fitted to a monthly water-level record can forecast that record's water table, but which version can be trusted depends on what is being forecast. Within the climate the record spans, the version with a free constant (Model B) forecasts better, needs only a few years of record, and measures the time the water table takes to return to its usual level, which a measurement that uses no model confirms. Against a drier decade that no fit had seen, the version without the constant (Model A), with its floor on the plateau, reproduces the lasting shift of the level, and Model B does not.

Projections into a changed climate should therefore use the version an independent record supports, with the other beside it, and report the pair. At Newborough, under a high-emissions climate, the two versions put the typical fall of the summer water level at {{projection_2050s_summer_fall_median_model_b_abs_dp2}}--{{projection_2050s_summer_fall_median_at_project_abs_dp2}} metres in the 2050s, inside the range the look back has tested, and {{projection_2080s_summer_fall_median_model_b_abs_dp2}}--{{projection_2080s_summer_fall_median_at_project_abs_dp2}} metres in the 2080s, beyond it. The main forest is withheld, because its drainage number cannot be worked out from the record.

The numbers themselves are not flows of water. The split of the loss between drainage and evaporation depends on the floor and leans towards drainage where the water table is shallow, and the recession time describes the floor as much as the aquifer. Each quantity should be taken from the version that identifies it, with the stretch of record declared and the tests repeated at every site.

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
