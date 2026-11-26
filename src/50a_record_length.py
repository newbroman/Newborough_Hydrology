"""
50a_record_length.py — What the record length decides (D-222).

Script 50 suite, step 50a (J-15, T-208; Martin 2026-11-24: five families, numbered 50a-50e,
all opt-in). Split from 50_record_length.py 1.30.0, whose full version history is kept in git and in
50a_record_length.py; every function moved whole with its dated comments. Shared helpers live in
utils/reclen_common.py.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-11-24 (J-15, T-208). Split from Script 50 1.30.0.

# ──────────────────────────────────────────────────────────────────────────────
# Script 50 (50_record_length.py) as it was at 1.30.0, carried over whole by J-15: its docstring, then its
# version history. The suite's other steps (50b-50e) point here for it.
# ──────────────────────────────────────────────────────────────────────────────
# | """
# | 50_record_length.py — what the record length decides: the coefficients, forecasting and hindcasting
# | =====================================================================================================
# | WHAT THIS IS
# |   The monthly state-space model (Script 03) is fitted on two records: the cluster centroids on the
# |   full record, and each reference well on a common comparison window of LCSC_DATA_LIMIT months. Its
# |   coefficients belong to the record they were fitted on, and the network was installed
# |   progressively, so "the record" is not one thing. This step measures how much that matters (D-222;
# |   spec working/updates/NRG_spec_record_length_2026-10-01.md, approved by Martin 2026-10-01).
# |
# |   At every reference well, Model A (no intercept, datum DRAINAGE_DATUM) and Model B (free
# |   intercept, which is Model A at the fitted datum DRAINAGE_DATUM - alpha/beta_3) are fitted on
# |   records of each length L in RECLEN_LENGTHS_MONTHS and on the full record. L counts fitted
# |   monthly changes (rows of the SSM frame), so a gap in a record lengthens its calendar span but
# |   not L. Four experiments:
# |
# |     forecast         fitted on the L months before MODEL_AB_SPLIT_DATE; free-run over every
# |                      month after it from the first reading there (Script 48's split-sample
# |                      forward test, which the full-length row reproduces exactly).
# |     hindcast_within  fitted on the L months from MODEL_AB_SPLIT_DATE; free-run over the months
# |                      before it from their first reading (Script 48's reverse test).
# |     ccw_hindcast     at the wells Script 39 admits: fitted on the first L months of the modern
# |                      record ("start") or the last L ("end"), then run through Script 39's hindcast
# |                      unchanged (utils/hindcast_utils.py) over the CCW 1989-96 readings, which no
# |                      fit ever sees. L = LCSC_DATA_LIMIT at the end is exactly the published
# |                      coefficients, and reproduces Script 39.
# |     stability        every non-overlapping placement of L months within the record, from its
# |                      start; beta_3 against the full-record beta_3 of the same form.
# |
# |   A well's STABLE LENGTH (per form) is the shortest L from which the median over placements of
# |   |beta_3(L)/beta_3(full) - 1| stays below RECLEN_STABLE_TOL at every longer L. Divided by the
# |   well's full-record Model B mean-reversion time, it answers whether the record a drainage
# |   coefficient needs is a fixed number of months or a multiple of the response.
# |
# |   The same run emits, on the full record, the expected spring persistence (1 - beta_3)^12 of both
# |   forms (D-221), so the methods paper can quote persistence and mean-reversion time on one record,
# |   and (T-103) the per-well ratio of the comparison-window beta_3 to the full-record beta_3 from
# |   Script 03's 03_15.
# |
# | WHAT IT DOES NOT DO
# |   It fits nothing Script 03 publishes and changes no other output. Fits shorter than SSM_MIN_OBS
# |   are deliberate here (RECLEN_MIN_FIT_MONTHS) and are confined to this step.
# |
# | INPUTS — all committed
# |   E13 (D-273) reads two raw inputs through utils/pet_alternatives.py, a documented raw-input exception like
# |   Scripts 09/10/24 and E8d's utils/midas_rain.py: data/RAF_Valley_Climate.csv (monthly Tmax, Tmin, sunshine)
# |   and data/midas_weather/valley_01145/ (MIDAS Open hourly weather and radiation; data/MIDAS_WEATHER_PROVENANCE.md).
# |   01_wells_clean.csv, 01_climate.csv, 03_master_data.csv (reference membership and clusters),
# |   03_15_per_well_window_sensitivity.csv (T-103), data/ccw_1989_1996_depths.csv and
# |   data/ccw_1989_1996_code_map.csv (the CCW hindcast; skipped cleanly when absent, as Script 39).
# |   For the identity checks only, when present: 48_04_model_a_b_diagnostics.csv, 39_01_hindcast_per_well.csv.
# |
# | OUTPUTS (outputs/50_record_length/)
# |   50_01_record_length_per_well.csv   one row per well x form x experiment x length x placement
# |   50_02_record_length_by_cluster.csv medians and 10th/90th percentiles by cluster (and all)
# |   50_03_ccw_hindcast_by_length.csv   the CCW hindcast per well x form x length x end
# |   50_05_stable_length_per_well.csv   each well's stable length, in months and in mean-reversion times
# |   50_04_record_length.png            stability, forecast, within-record and CCW hindcast against L
# |   50_18 .. 50_20                     E8d, rain event structure (D-234)
# |   50_21 .. 50_23                     E8e, the 1998 felling north of NW9 and its regrowth (D-235)
# |   50_24 .. 50_25                     E8f, the shore clearance step, 2012-17 (D-236)
# |   50_26_precanopy_by_case.csv        E8g, a store drawn down by the plantation: the pre-canopy test (T-121, D-255)
# |   50_27_forest_forcing_by_well.csv   E10, the forest forcing test (D-260)
# |   50_28_ranwell_need_grid.csv        E11, what Ranwell's readings need: every pairing x coefficient scales (D-261)
# |   50_29_ranwell_epoch_candidates.csv E11, each candidate sized against the need (D-261)
# |   50_30_basis_by_test.csv            E12, per well or per cluster (D-268)
# |   50_40_placement_by_test.csv        E12b, can a short record place a new well? (D-282)
# |   50_45_ccw_quantile_map.csv         E18, does a modern-record calibration transfer to CCW 1989-96? (D-290)
# |   50_46 .. 50_47                     E19, does the film's correction transfer to CCW 1989-96? months and years (D-292)
# |   50_31 .. 50_35                     E13, other evaporation estimates and a beta_1 break (D-273)
# |   50_36 .. 50_39                     E13b, Penman-Monteith against Thornthwaite; residual seasonality under each (D-274)
# |   50_report_numbers.csv
# |
# | Registered in run_analysis.py, Phase 19, tier X, opt-in (--with-supplementary).
# | Run directly:  python3 src/50_record_length.py [--no-fig]
# | """
# | (version history)
# | __version__ = "1.30.0"  # Hollingham (2026) - 2026-11-23 (J-25, Martin: "Figure, prose kept"). plot_decision_tree() draws
# | #   Paper M Section 4.6 as a decision tree (50_54_decision_tree.png, Figure 7): own or cluster coefficients, full record or
# | #   RECLEN_MIN_FIT_MONTHS, scored on the coming years, another climate's seasons and a lasting drier shift, with C4 as
# | #   the forest exit. It READS the saved 50_report_numbers.csv and 48_report_numbers.csv after they are written, so the
# | #   figure cannot letter a number the CSVs do not hold; pass/fail marks come from the basis_*/placement_* holds flags
# | #   (the rule fixed before the run), and the own-coefficient drier-shift rows from BASIS_TOL_BIAS_M.
# | # 1.29.0  # Hollingham (2026) - 2026-11-20 (J-23, T-173 under Model B; Martin's three decisions of 2026-11-20).
# | #   neighbour_transfer(intercept=True): every fit Model B, the borrowed intercept travelling with the betas (full
# | #   transfer, each set at its own implied datum), the centroid the median of betas and intercepts; the neighbour is
# | #   still the nearest other well with a pre-2018 fit, any cluster. 50_50 gains form "B" rows. Report keys
# | #   transfer_B_* per cluster, open dune, forest and all: median r2 and |bias| (own, neighbour, centroid), the
# | #   neighbour-minus-own differences, and the criterion flags (config TRANSFER_R2_TOL, TRANSFER_BIAS_TOL_M).
# | # 1.28.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). Script 03 1.31.0 puts Model B in
# | #   03_master_data / 03_03 / 03_15's unsuffixed coefficient columns and Model A in *_model_a. Every read of them here
# | #   means Model A, so all now go through _model_a_store(): the usable_codes admission (Script 39's Model A rule, in
# | #   the record-length CCW hindcast, E5, E8, E8b/c, E12, E16/E17, E18 and E19), transfer_rule's coefficient
# | #   differences (T-173b), E11's open-ground ratios, E8g's 03_03 centroids, and the window_full_beta3_ratio_* keys
# | #   (03_15). Model B is this script's own fit throughout; no Model B result changes.
# | # 1.27.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). Script 15 1.11.0 fits the 15_05
# | #   depth-dependent sets as Model B (free α): E7's fall_ddp_m now runs each set at its own implied base, 15_05
# | #   implied_datum_m (β₃·(h + z) = β₃·(h + DRAINAGE_DATUM) − α; the PET attenuation reads depth below ground), not at
# | #   DRAINAGE_DATUM. A set whose implied base is not below ground is left out and counted
# | #   (projection_ddp_n_sets_excluded_datum). ddp_identity_check stays at DRAINAGE_DATUM: it is a function identity on
# | #   synthetic coefficients at 1/L_E = 0, where the response does not depend on the datum.
# | # 1.26.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b). Figure 50_49 (plot_split_series) picks
# | #   each cluster's example well as the MEDIAN-NSE well under Model B (was Model A at 3.7 m), and its observed line and
# | #   suptitle follow. Figure only: no CSV or report number changes.
# | # 1.25.0  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2a; brief NRG_brief_model_B_single_form
# | #   Addendum 3, "Phase 2, task 1, widened"). The MHW form -- Model A at each well's depth to mean high water
# | #   (ground_elev_m less 01b's tide_mhw_m; Script 48's form M, E16's mhw spec) -- runs beside Model A at
# | #   DRAINAGE_DATUM and Model B, as form "M", in: the record-length forecast / within-record hindcast / stability
# | #   experiment (50_01, 50_02, 50_05; reclen_*_M_* keys: stable length and return times, stable length by cluster,
# | #   forecast at every length); the January 2018 split kept month by month (50_48 form M; 50_49 draws it, and its
# | #   legend moves below the panels, off the data); and T-173's neighbour transfer (50_50 gains a form column; M
# | #   rows fit each well at its own MHW floor and run every borrowed set at the TARGET well's floor; the centroid
# | #   row is the median of the members' MHW-floor coefficients run at the target's floor -- a design choice, since
# | #   a centroid has no ground level; transfer_median_nse_{own,neighbour,centroid}_mhw). Every free run passes
# | #   base= explicitly (free_run's default binds DRAINAGE_DATUM at definition). Identity: the M rows' full-length
# | #   split NSE against Script 48's nse_fwd_M / nse_rev_M (reclen_check_vs48_M_max_abs_nse_diff); the A/B check
# | #   keeps its A/B scope. Model B's beta_3 is bounded below (model_utils 1.14.0): fits that were dropped for
# | #   beta_3 <= 0 are kept at the bound, describe() carries beta_3_bound, and beta3_bound_B_n_* count them per
# | #   test. E5/E6/E12/E13/E10 are unchanged in scope (E12 cannot carry the form: a centroid has no MHW floor).
# | # 1.24.0  # Hollingham (2026) - 2026-11-10 (D-322, Martin: "option 1"). The CCW record-length
# | #   hindcast (RB-50b) moves from D-281's tier 3 to tier 1: each fit is Script 03's, censored on the well's
# | #   dry months (fit_ssm(..., dry_bound=dry_bounds(col))) over CALENDAR months, the last L (window=L) or the
# | #   first L from the record's first month. It dropped dry months and took the trailing L VALID rows, so at the
# | #   five CCW wells that go dry its window reached back to 2016 and never saw the driest months; its own check
# | #   against Script 39 (reclen_check_vs39_max_abs_nse_diff) has read 0.94 instead of 0 since D-281.
# | #   Extended the same day (D-322, Martin: "extend D-322 to both"): the CCW hindcast at every datum (E5, RB-50d)
# | #   and E12's own-well fits (RB-50p: CCW, Ranwell and the split forecast) fit the same way, through
# | #   _censored_well_fit(); E12's cluster side reads Script 03's centroids, which D-281 already treats.
# | #   The split forecast in E12 was then RESTORED to Script 48's fit (D-281 tier 2): censoring it broke the
# | #   check against Script 48 at 82 of 264 pairs (basis_vs48_max_abs_nse_diff 70.4).
# | #   Widened to ALL of Script 50 (Martin, 2026-11-10: "put all of Script 50 on it"): no window counts rows.
# | #   Every "last 100" is the last LCSC_DATA_LIMIT CALENDAR months, censored -- E9 Ranwell by datum (RB-50e),
# | #   E16/E17 (RB-50t/u), the centroid window -- and E18's own-well CCW fit is censored. RB-50a's lengths
# | #   are L calendar months either side of the split and RB-50c's blocks are L calendar months from the
# | #   record's first month; both stay tier 2/3 (dry months dropped), as the split forecast and Script 48 do.
# | # 1.23.0 - 2026-11-07 (J-6, Martin: "I want j6 run and sorted").
# | #   split_series() keeps the Jan-2018 split-sample free run MONTH BY MONTH for BOTH forms
# | #   (50_48_split_series.csv), and plot_split_series() draws it (50_49_split_both_models.png).
# | #   Scenario 1 -- the case inside the recorded climate, the one Model B is supposed to win --
# | #   had 10,032 rows of NSE in 50_07 and no series anyone could plot, so every hindcast figure
# | #   in the corpus showed ONE form. Emit-only: same fit, free run and datum convention as
# | #   split_by_datum, verified by recomputing Model A NSE against 50_07 at DRAINAGE_DATUM
# | #   (max |difference| 2.8e-14 over 132 well/direction pairs).
# | # "1.22.0"  # Hollingham (2026) - 2026-11-01 (T-133, D-292; Martin 2026-11-01 "Test A otherwise c", "no model B
# | #   arms, approve majority of years"). E19: does the FILM's correction transfer to CCW 1989-96? E18 tested a per-well map;
# | #   the film maps one series, the open-dune warren run (Script 47's load_warren / run_recurrence, read through importlib,
# | #   the Script 30 precedent) onto the network's observed median. E19 runs exactly that, then scores three arms against
# | #   the median of the admitted CCW wells over the months every one of them reads uncensored: raw, quantile-mapped
# | #   (Script 47's calibrate, unchanged) and offset only (the modern mean bias over the same calibration months). The
# | #   rule is E18's, fixed before the run, with "a majority of the 9-year record's years" (D-207 hydrology years, May to
# | #   April, at least E19_MIN_MONTHS_PER_YEAR scored months) in place of "a majority of wells". Outcome: the map if it
# | #   passes, else the offset if it passes, else neither (the film keeps its map, caveated). Writes 50_46 (months) and
# | #   50_47 (years) and the e19_* report numbers; --only-e19 runs it alone. Nothing else moves. Additive.
# | # 1.21.0  # Hollingham (2026) - 2026-10-29 (T-130, D-290; findings NRG_findings_ccw_quantile_map_2026-10-29,
# | #   Martin 2026-10-29 "Yes, rule as proposed"). E18: does a calibration fitted on the modern record transfer to the CCW
# | #   1989-96 decade? Script 39's CCW protocol unchanged (each well's own Model A at the project datum, its equilibrium
# | #   seed, censored months dropped), and the same on E12's cluster basis; per well, utils.hindcast_utils.quantile_map
# | #   (Script 47's map) fitted on the well's modern record against the SAME continuous run, and applied unchanged to
# | #   1989-96. The rule is fixed before the run (e18_verdict, config.E18_*). Writes 50_45_ccw_quantile_map.csv and the
# | #   e_qm_* report numbers; --only-e18 runs E18 alone and replaces only the e_qm_* rows. Ranwell is not used. Additive.
# | # 1.20.0  # Hollingham (2026) - 2026-10-28 (D-287; spec NRG_spec_E16_paperM_and_E17_cluster_base_2026-10-28,
# | #   Martin 04:28 "S"). E17: a drainage base in elevation per cluster, every member well at ground - z_c, z_c chosen from
# | #   the modern record only (S: E16's split NSE per cluster, primary; R: 03_09 R2-max datums; B: 48_04 Model B bases),
# | #   then tested on the drier epochs cluster by cluster against the depth datum by the rule fixed before the run
# | #   (e17_verdict). Writes 50_43_cluster_base_by_test.csv, 50_44_cluster_base_summary.csv, e17_* report numbers;
# | #   --only-e17. E16 gains per-cluster report numbers (e16_ccw_nse_median_C*, e16_ccw_n_*, e16_efold_median_C*,
# | #   e16_r2_median_*, e16_ranwell_n) for Paper M's fields. elevation_datum_tests takes specs and datum_of. Additive.
# | # 1.19.0  # Hollingham (2026) - 2026-10-28 (D-286; Martin 03:15 "please write the script"). E16: Model A(ii),
# | #   every well referred to ONE drainage base z0 m AOD (a per-well datum of ground - z0, Script 03's datum_aod_sweep), over
# | #   DATUM_AOD_SWEEP_* and mean high water, scored on the forward tests on E5/E9/E6's code paths (CCW 1989-96, Ranwell
# | #   1951-53, the within-record split) against Model A at the depth datum on the same wells, with beta_3's identification
# | #   and the Spearman rho of beta_3 against the per-well datum (does beta_3 only restate the height above the base?).
# | #   The adoption rule is fixed before the run (elevation_datum_verdict). Writes 50_41_elevation_datum_by_test.csv and
# | #   50_42_elevation_datum_summary.csv and the e16_* report numbers; --only-e16 runs E16 alone and replaces only the
# | #   e16_* rows. The verdict compares like for like: the best datum is chosen among the datums that score every well the
# | #   depth datum scores (the first run chose 7 m AOD on 5 of 9 CCW wells; same verdict either way). Additive.
# | # 1.18.0  # Hollingham (2026) - 2026-10-27 (D-281, tier 1; Martin 02:14 "Agree with the 3 tiers"). E7's
# | #   Model A refit at each datum, behind the projections, passes the well's dry-month bounds (the censored fit, model_utils
# | #   1.12.0) on the fixed calendar comparison window, instead of tailing a frame that dropped its dry months. Model B (03_16)
# | #   and the depth-dependent sets (15_05) come in already treated. The forecast tests (E1-E6, E9, E12) are tier 2.
# | # 1.17.0  # Hollingham (2026) - 2026-10-27 (D-282; Martin 02:14 "Add the script 50 short record placement
# | #   test ... Carry out the short record test"). E12b: each reference well is placed from its first PLACEMENT_LENGTHS_MONTHS
# | #   months alone (Pearson r with each centroid built without it, Script 06's allocation), shifted to that centroid over
# | #   those months only, and run through E12's three tests on the placed cluster's coefficients; E12's rule against the
# | #   per-well basis decides. 50_40_placement_by_test.csv; placement_* report numbers. Additive: no existing value changes.
# | # 1.16.0  # Hollingham (2026) - 2026-10-27 (D-280; Martin 01:21 "Add the depth-dependent model as a third
# | #   projection beside Model A and Model B, in Script 50 and the viewer"). E7 projects each well under the depth-dependent
# | #   set from 15_05_ddp_per_well.csv at the project datum (model_utils.sustained_monthly_response_ddp, the difference of
# | #   two periodic steady states): 50_08 gains fall_ddp_m; report numbers projection_<scen>_n_wells_trio and
# | #   _summer_fall_median_trio_{model_a,model_b,ddp}; identity check projection_check_ddp_k0_vs_closed_form. The pair's
# | #   keys are unchanged.
# | # 1.15.0  # Hollingham (2026) - 2026-10-26 (D-279; Martin 08:38 "Like numbers fields, this should be standard
# | #   with every edit that we do. Make scripts to produce the figures where they cannot be typed"). E7's report numbers
# | #   carry the 2050s beside the 2080s (projection_2050s_*), with projection_<scen>_n_wells_pair; water_balance_report()
# | #   emits each scenario's annual P - PET shift and the CCW epoch's shift from the same modern mean. The seasonal
# | #   multipliers move into scenario_scales_12(), shared by both; no existing value changes.
# | # 1.14.1  # Hollingham (2026) - 2026-10-24 (D-274; the text walk-through, Martin 21:05-21:20). E13b also
# | #   emits each series' percentage difference from Thornthwaite over the year and over E13B_SEASON_A_MONTHS and
# | #   E13B_SEASON_B_MONTHS (ratio of the seasonal totals), so the report's seasonal figures bind to committed keys. No
# | #   other value changes.
# | # 1.14.0  # Hollingham (2026) - 2026-10-24 (D-274; Martin 05:30 "a comparison analysis against
# | #   thornthwaite and include that in the report", 05:37 "does PM resolve [the residual-by-month analysis]?", 05:43 "build E13b
# | #   into the batch"; spec NRG_spec_E13b_pet_comparison_2026-10-24). E13b: Penman-Monteith (and the radiation estimates)
# | #   against Thornthwaite over the MIDAS span and over the measured-radiation years - annual means and ratios, each calendar
# | #   month, correlations, trends, first and last E13B_WINDOW_YEARS and the temperature elasticity; Script 24's residual
# | #   seasonality (Model B per well, its well set) with Thornthwaite and with Penman-Monteith on the same span, identity
# | #   against 24_residual_climatology.csv, and the rule fixed before the run. 50_36, 50_37, 50_38; e13b_* keys.
# | #   Phase 17 E13b, outputs 18.
# | # 1.13.0  # Hollingham (2026) - 2026-10-23 (D-273; Martin 23:20 "Make e13 a proper step"; spec
# | #   NRG_spec_E13_build_2026-10-23, approved, centroids as the member-well mean). E13: does an evaporation estimate other
# | #   than Thornthwaite, or a beta_1 break, explain the 2006-08 excess (D-231)? Hargreaves, Priestley-Taylor and Makkink
# | #   on the full climate span; FAO-56 Penman-Monteith from MIDAS Open hourly weather and radiation, with wind and then
# | #   vapour pressure held at their day-of-year means, on the MIDAS span with Thornthwaite re-run there; Model A and
# | #   Model B at each member-well-mean centroid, free-run from continuous_start; the rule fixed before the scratch run
# | #   (E13_EXCESS_SHARE, E13_RMSE_TOL, E13_CLUSTERS). Per well (E8e set), Model A with beta_1 free before a break profiled
# | #   over E13_BREAK_WINDOW. A fit with beta_3 <= 0 is flagged unstable and never read. 50_31 .. 50_35; e13_* keys.
# | #   Phase 16 E13, outputs 17. Reproduces the scratch runs (working/nvc_laurence/scripts/26_, 27_) on every stable row.
# | # 1.12.0  # Hollingham (2026) - 2026-10-16 (D-268; Martin 11:07 "paper M needs to cover the clustering processes
# | #   and how robust the model is relative to hindcasting, whether it's per cluster or per well", 11:34 the spec's three calls;
# | #   spec NRG_spec_cluster_vs_well_hindcast_2026-10-16). E12: the CCW 1989-96 hindcast (full modern record), the Ranwell
# | #   1951-53 hindcast (comparison window, Script 44's scoring) and the split-sample test (Script 48's), each on the well's
# | #   own coefficients and on its cluster centroid's fitted on the same span, both forms; the centroid run shifted by the
# | #   well-centroid mean difference over the fitted months. The rule fixed before the run (BASIS_TOL_NSE, BASIS_TOL_BIAS_M):
# | #   basis_verdict_A/B. 50_30_basis_by_test.csv; basis_* report numbers; identity against Scripts 48 and 44.
# | # 1.11.0  # Hollingham (2026) - 2026-10-15 (D-266; Martin 13:08 "I approve the spec"; spec
# | #   NRG_spec_E8_identified_timescales_2026-10-15). E8 and E8g report a store's e-folding time only where the fit
# | #   identifies it: a store carrying under TWO_STORE_SHARE_MIN of the response has its e-fold (and SE) emitted as
# | #   NaN, the fitted value kept in fast/slow_efold_months_raw, with fast/slow_identified; an identified e-fold within
# | #   TWO_STORE_BOUND_TOL of its bound is flagged fast/slow_at_bound (lower/upper). No fit, share, BIC, split NSE or
# | #   verdict changes. 50_12, 50_26 and the two_store_C*_slow_efold_months report numbers.
# | # 1.10.0  # Hollingham (2026) - 2026-10-14 (D-261; Martin 07:22 "Let's include it in the paper. Test for
# | #   effects of vegetation. What about years previous to 1951", 07:30 "say what the model needs to match the groundwater's
# | #   water levels and then go through each possible intervention and size up its possible effects ... it's an exploration,
# | #   not a test and put it into script 50"; spec NRG_spec_E11_ranwell_epoch_2026-10-14 as amended). E11: what Ranwell's
# | #   1951-53 readings need of the model, and what could supply it. The need: every Script 44 pairing with beta_1, beta_2,
# | #   beta_3 scaled over RANWELL_NEED_K*_GRID (single-coefficient profiles, the joint best and the cells within
# | #   RANWELL_NEED_NSE_TOL), and the same profiles with the model capped at the pipe's foot. The candidates: seasonality
# | #   (RANWELL_SEASON_WINDOW_YEARS windows), the years before (RANWELL_ANTECEDENT_YEARS; the model's memory over
# | #   RANWELL_MEMORY_MONTHS), on-site rain (Parc Mawr), the swing then and now, today's forest (its drawdown reach, from the
# | #   open-ground wells within and beyond it), and the literature candidates of
# | #   data/ranwell_epoch_candidates.csv sized at the ends of their range. 50_28, 50_29; ranwell_need_*, ranwell_epoch_*.
# | #   Phase 14 E11, outputs 15.
# | # 1.9.0  # Hollingham (2026) - 2026-10-13 (D-260; Martin 22:05 "1- 0.1, 2 agreed, 3 - yes to both. 4 script 50",
# | #   22:08 "f3"; spec NRG_spec_forest_ET_forcing_2026-10-13 as revised). E10: is the forest's poor forecasting the
# | #   drainage or the forcing? Every C4/C5 well under F0 observed forcing, F1 rainfall less FOREST_INTERCEPTION, F2
# | #   interception scaled by Script 41's canopy (clearfell region at EDGE_WELLS, forest control elsewhere), F3 F2 with
# | #   a post-felling evaporation coefficient at the edge wells (full record only: the felling falls at the split).
# | #   Both forms; full-record BIC, forward/reverse split NSE, Model B identification, summer-minus-winter residual; the
# | #   rule fixed before the run (FORCING_NSE_GAIN). 50_27_forest_forcing_by_well.csv; forest_forcing_* report numbers.
# | #   Phase 13 E10, outputs 14. POST HOC (Martin 22:18 "b for the forest", after the rule's run; outside the rule,
# | #   forest_forcing_posthoc_* keys): F2e changes only the edge wells' forcing; F2s replaces the inner wells' canopy
# | #   with one step at the felling, a placebo for the inner-well forecast gain.
# | # 1.8.0  # Hollingham (2026) - 2026-10-10 (T-121, D-255; Martin 17:06-17:11, spec
# | #   NRG_spec_precanopy_T121_T122_2026-10-10, "Please continue" 18:06). E8g: was a store drawn down by the plantation
# | #   at C4 and C5? E8 warmed up on the forest coefficients from 1941, so it could not see one. Per forest cluster
# | #   centroid, the effective recharge R = beta_1(t) P - beta_2(t) PET with the coefficients moving along a logistic
# | #   canopy share from the open-dune analogue's (PRECANOPY_ANALOGUE, D-254) to the forest's, for each planting year
# | #   x closure age (PRECANOPY_*), fed to the single and two-store responses; against the same with the forest
# | #   coefficients throughout. Strict rule fixed before the run: supported only if every case's two-store fit beats
# | #   the better forest-throughout fit by TWO_STORE_BIC_STRONG, holds the forward split, and shrinks |2006-08
# | #   residual|. Two-store fits start from a grid (PRECANOPY_SLOW_STARTS_DAYS x PRECANOPY_SHARE_STARTS), lowest
# | #   BIC kept: the fit is multi-modal. 50_26_precanopy_by_case.csv; precanopy_* report numbers. Phase 12 E8g, outputs 13.
# | # 1.7.0  # Hollingham (2026) - 2026-10-03 (D-236; Martin: "Otherwise I approve", 07:49, spec
# | #   NRG_spec_E8f_shore_clearance_step_2026-10-03). E8f: did the 2014/15 shore clearance put a step into the wells
# | #   around it? Per well within E8F_NEAR_M of the strip, and placebo wells beyond E8F_FAR_M, the E8 single store against
# | #   the same with one step whose date is profiled monthly over E8F_STEP_WINDOW; test 1, a step at the BACI coastal
# | #   controls or the scrape control (E8F_CONTROL_WELLS); test 2, at most E8F_PLACEBO_MAX_FRAC of the placebo wells
# | #   step. 50_24_clearance_step_by_well.csv, 50_25_clearance_step.png; e8f_* report numbers. Phase 11 E8f, outputs 12.
# | # 1.6.0  # Hollingham (2026) - 2026-10-02 (D-235; Martin: "e8e spec approve", 23:33, spec
# | #   NRG_spec_E8e_felling_regrowth_2026-10-02). E8e: was the 2006-08 high water at NW9 the 1998 felling north of
# | #   it and the pine's return? Per well, the E8 single store on the full record (wells with E8E_MIN_EARLY_MONTHS
# | #   readings in 2006-08): test 1, the excess falls with 01_locations dist_1998_replant_m (Spearman, p < E8E_P)
# | #   more strongly than with dist_coast_m; test 2, NW9's half-decline year against the year Script 41's canopy
# | #   ratio over felling_1998_1 (vp1) is halfway to its highest; test 3 (reported), open-dune wells beyond
# | #   E8E_FAR_M. 50_21_felling_distance_by_well.csv, 50_22_nw9_regrowth_timing.csv, 50_23_felling_regrowth.png;
# | #   e8e_* report numbers. Phase 10 E8e, outputs become phase 11.
# | # 1.5.0  # Hollingham (2026) - 2026-10-02 (D-234; Martin: "approve", spec
# | #   NRG_spec_E8d_rain_event_structure_2026-10-02). E8d: did long rain events, which a monthly total hides, drive
# | #   the 2006-08 excess? Daily MIDAS gauges (Llyn Alaw primary, RAF Valley check; utils/midas_rain.py, a
# | #   documented raw-input exception): per winter the share of rain in long events against the gauge's own
# | #   1974-2005 baseline (tests 1-2), and per cluster centroid a long-event stress on the single store
# | #   (test 3). 50_18_rain_events_by_winter.csv, 50_19_event_stress_by_cluster.csv, 50_20_rain_events.png;
# | #   e8d_* report numbers. Phase 9 E8d, outputs become phase 10.
# | # 1.4.0  # Hollingham (2026) - 2026-10-02 (D-232; Martin: "go ahead with e8b and e8c" / "approve").
# | #   E8b: one non-climatic term on E8's single store per cluster centroid - a step (ps.StepModel, One), a
# | #   relaxing step (StepModel, Exponential), a linear trend (ps.LinearTrend) - its date fitted inside
# | #   CHANGE_TSTART_BOUNDS; the best by BIC is kept if it beats the single store by TWO_STORE_BIC_STRONG and
# | #   holds the split test (CHANGE_SPLIT_DIRECTIONS); direction, a common date across clusters, the NW9 winters,
# | #   and the CCW check. E8c: surface flow - ps.TarsoModel (a second drainage above a fitted level) and the
# | #   single store with ps.ThresholdTransform - judged by BIC, the split test, the bias of months starting within
# | #   SURFACE_BAND_M of the ground, a threshold within SURFACE_THRESHOLD_MAX_DEPTH_M of it; CCW and Ranwell's C1
# | #   sites as checks. 50_15_two_store_change.csv, 50_16_surface_flow.csv, 50_17_change_and_surface.png.
# | #   Spec NRG_spec_E8b_E8c_2026-10-02, with its two amendments made before any real fit was read: E8b's split
# | #   test is forward only (Martin, 13:20, "yes"; the reverse half trains after every admissible change date),
# | #   and change dates and the threshold transform's level are PROFILED (_profile), because Pastas returns
# | #   them at their initial value with a standard error of 0; the 95% intervals are profile intervals.
# | # 1.3.0  # Hollingham (2026) - 2026-10-02 (D-231; Martin: "I approve the spec of the E8 model").
# | #   E8: two drainage time scales per cluster. Pastas Exponential (term for term Model B) against
# | #   DoubleExponential (two parallel linear stores sharing the recharge), fitted to each cluster centroid,
# | #   warmed up over the climate record from its last gap (utils/pastas_utils), so no starting level is
# | #   fitted; with and without the AR(1) noise model. The four tests and the verdict are the rule fixed
# | #   before the run (config TWO_STORE_*; spec NRG_spec_E8_two_store_2026-10-02): BIC and the split test;
# | #   the CCW drier-decade bias at the cluster's CCW wells; agreement of the slow time scales; the 2006-08
# | #   residual and the NW9 winters. C4 and C5 fitted whole (felling years in) and reported separately.
# | #   50_12_two_store_by_cluster.csv, 50_13_two_store_check_well.csv, 50_14_two_store.png.
# | # 1.2.0  # Hollingham (2026) - 2026-10-02 (D-229; Martin: "Spec adding Ranwell" / "Approve").
# | #   E9: Ranwell's 1951-53 readings as the second drier epoch. Model A refitted at every datum and Model B,
# | #   comparison window and full record, hindcast from the 1930 spin-up at Script 44's pairings and scored as
# | #   Script 44 scores them (utils/hindcast_utils.compare_offset_censored: offset removed, censored at the
# | #   ground). The rule fixed before the run: the datum maximizing the median NSE over the headline pairings
# | #   (Model A, comparison window), the band within RECLEN_DATUM_NSE_TOL; "does not discriminate" when the
# | #   median moves by less than that tolerance over the whole grid; otherwise "consistent" with CCW when the
# | #   bands overlap, "disagrees" when they do not. Checks, never the rule: all pairings, the dry year 1953
# | #   alone, the amplitude ratio, the full record. Identity check against Script 44 at the project datum.
# | #   50_10_ranwell_hindcast_by_datum.csv; 50_09 gains the Ranwell panel. Spec
# | #   NRG_spec_ranwell_by_datum_2026-10-02.
# | # 1.1.0  # Hollingham (2026) - 2026-10-01 (D-225; Martin: "please spec it" / "I approve your
# | #   choices"). Which datum does the drier past support? Model A refitted at every datum of Script 03's
# | #   sweep: the CCW 1989-96 hindcast (comparison window and full record), the within-record split test,
# | #   and the UKCP18 sustained projection with each well's room left above the datum (forest withheld by
# | #   the D-224 pairing). The supported datum is fixed by a rule stated before the run: the datum
# | #   maximizing the median CCW NSE on the comparison window, and the band within RECLEN_DATUM_NSE_TOL of
# | #   it. Three identity checks at DRAINAGE_DATUM (Scripts 39, 48 and 19). Spec
# | #   NRG_spec_datum_against_the_drier_past_2026-10-01.
# | # 1.0.0  # Hollingham (2026) - 2026-10-01 (D-222). First issue, to the approved spec
# | #   NRG_spec_record_length_2026-10-01 (Martin: "approved"). Numbered 50 because 49 is the former name
# | #   of 01b_water_table.py and is still cited by that name in the records.
# | 


import argparse
import importlib.util
import warnings
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils import paths                                       # noqa: E402
from utils.paths import (                                     # noqa: E402
    DIR_50A, OUT_50A_REPORT_NUMBERS, OUT_50_PER_WELL, OUT_50_BY_CLUSTER, OUT_50_CCW, OUT_50_STABLE, OUT_50_FIG,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_MASTER_DATA,
    OUT_03_PER_WELL_WINDOW_SENS, OUT_48_MODEL_AB, OUT_39_PER_WELL,
    OUT_03_MODEL_B_PERSISTENCE, OUT_19_SCENARIO_PERWELL_MODEL_A, INT_LOCATIONS, OUT_15_DDP_PER_WELL,
    OUT_50_CCW_DATUM, OUT_50_SPLIT_DATUM, OUT_50_SPLIT_SERIES, OUT_50_SPLIT_FIG,
    OUT_50_NEIGHBOUR, OUT_50_NEIGHBOUR_FIG, OUT_50_TRANSFER_RULE, OUT_50_TRANSFER_FIG, OUT_50_DECISION_FIG,
    OUT_50_PROJ_DATUM, OUT_50_DATUM_FIG,
    OUT_50_RANWELL_DATUM, OUT_44_METRICS, RANWELL_LEVELS,
    OUT_50_TWO_STORE, OUT_50_TWO_STORE_WELL, OUT_50_TWO_STORE_FIG, INT_REGIONAL_AVG,
    OUT_50_CHANGE, OUT_50_SURFACE, OUT_50_CHANGE_SURFACE_FIG,
    MIDAS_RAIN_DIR, OUT_50_RAIN_EVENTS, OUT_50_EVENT_STRESS, OUT_50_RAIN_EVENTS_FIG,
    OUT_50_FELLING_DIST, OUT_50_NW9_TIMING, OUT_50_FELLING_FIG,
    OUT_50_CLEARANCE_STEP, OUT_50_CLEARANCE_FIG, DATA_SHORE_CLEARANCE_2015,
    OUT_03_MECHANISTIC_TABLE, OUT_50_PRECANOPY, OUT_41_INDEX, OUT_50_FOREST_FORCING,
    OUT_50_RANWELL_NEED, OUT_50_RANWELL_EPOCH, OUT_50_BASIS, OUT_50_PLACEMENT, OUT_50_PET_ALT, OUT_50_E13_PET, OUT_50_E13_BREAK, OUT_50_E13_WEATHER,
    OUT_50_E13_FIG, OUT_50_ELEV_DATUM_TESTS, OUT_50_ELEV_DATUM_SUMMARY, OUT_01B_REPORT_NUMBERS, OUT_50_CLUSTER_BASE_TESTS, OUT_50_CLUSTER_BASE_SUMMARY, OUT_03_WELL_OPTIMAL_DATUMS, OUT_50_CCW_QMAP, OUT_50_CCW_FILM_MAP, OUT_50_CCW_FILM_MAP_YEARS, OUT_50_E13B_CMP, OUT_50_E13B_FIG, OUT_50_E13B_RESID, OUT_50_E13B_INPUTS, INT_24_CLIMATOLOGY_TABLE, MIDAS_WEATHER_DIR, INT_WELLS_REFERENCE, INT_WELLS_EXTENDED, RANWELL_PARC_MAWR_RAIN, RANWELL_EPOCH_CANDIDATES, DATA_FOREST_BOUNDARY, OUT_20_REPORT_NUMBERS,
)
from utils.config import (                                    # noqa: E402
    DRAINAGE_DATUM, HEADLINE_LAG, CLUSTER_LABELS, CLUSTER_COLOURS, LCSC_DATA_LIMIT,
    MODEL_AB_SPLIT_DATE, MODEL_AB_MIN_TEST_MONTHS, PASTAS_IDENT_EFOLD_WINDOW_FRAC,
    TRANSFER_R2_TOL, TRANSFER_BIAS_TOL_M,
    RECLEN_LENGTHS_MONTHS, RECLEN_MIN_FIT_MONTHS, RECLEN_STABLE_TOL,
    RECLEN_DATUM_NSE_TOL, DATUM_SWEEP_MIN_M, DATUM_SWEEP_MAX_M, DATUM_SWEEP_STEP_M,
    DATUM_AOD_SWEEP_MIN_M, DATUM_AOD_SWEEP_MAX_M, DATUM_AOD_SWEEP_STEP_M, E17_CANDIDATES, E17_PRIMARY_CANDIDATE,
    E18_RMSE_CUT_M, E18_BASES, E18_PRIMARY_BASIS, QMAP_MIN_MONTHS, QMAP_MIN_WELLS, E19_MIN_MONTHS_PER_YEAR,
    FOREST_INTERCEPTION, UKCP18_SCENARIOS, WINTER_WET_CLIMATE_MONTHS, SUMMER_DRY_CLIMATE_MONTHS,
    RECORD_START_DISPLAY, REFERENCE_CUTOFF_DATE,
    TWO_STORE_FAST_INIT_DAYS, TWO_STORE_FAST_BOUNDS_DAYS, TWO_STORE_SLOW_INIT_DAYS,
    TWO_STORE_SLOW_BOUNDS_DAYS, TWO_STORE_SLOW_SHARE_INIT, TWO_STORE_EARLY_YEARS,
    TWO_STORE_EARLY_REDUCTION, TWO_STORE_LATER_RMSE_TOL_M, TWO_STORE_CCW_BIAS_TOL_M,
    TWO_STORE_CHECK_WELL, TWO_STORE_CHECK_CLUSTER, TWO_STORE_FLOOD_WINTERS, TWO_STORE_NEAR_WINTERS,
    TWO_STORE_DRY_WINTERS, TWO_STORE_SURFACE_TOL_M, TWO_STORE_NEAR_TOL_M, DAYS_PER_MONTH,
    TWO_STORE_SHARE_MIN, TWO_STORE_BOUND_TOL, BASIS_TOL_NSE, BASIS_TOL_BIAS_M, PLACEMENT_LENGTHS_MONTHS,
    TWO_STORE_BIC_STRONG, CHANGE_TSTART_INIT, CHANGE_TSTART_BOUNDS, CHANGE_SPLIT_DIRECTIONS,
    CHANGE_GRID_COARSE_MONTHS, SURFACE_THRESHOLD_GRID,
    SURFACE_BAND_M, SURFACE_THRESHOLD_MAX_DEPTH_M,
    E8D_PRIMARY_GAUGE, E8D_CHECK_GAUGE, E8D_WET_DAY_MM, E8D_EVENT_MIN_DAYS, E8D_EVENT_PCTL,
    E8D_BASELINE_END_YEAR, E8D_WINTER_MONTHS, E8D_MAX_MISSING_FRAC, E8D_UNUSUAL_PCTL, E8D_UNUSUAL_MIN_COUNT,
    E8D_TEST_WINTERS, E8D_FLOOD_WINTER, E8D_LATER_WINTERS, E8D_FIT_START, E8D_FIT_END,
    E8D_RESIDUAL_REDUCTION, E8D_CLUSTERS_WITH_EXCESS,
    E8E_MIN_EARLY_MONTHS, E8E_LATER_YEARS, E8E_P, E8E_NEAR_M, E8E_FAR_M, E8E_TIMING_BASE_YEARS,
    E8E_TIMING_TOL_YEARS, E8E_CHECK_WELL, E8E_CANOPY_REGION, E8E_CANOPY_VIEWPOINT, LAKE_GAUGE_KEYS,
    E8F_STEP_WINDOW, E8F_MIN_SIDE_MONTHS, E8F_NEAR_M, E8F_FAR_M, E8F_CONTROL_WELLS, E8F_PLACEBO_MAX_FRAC,
    E8F_WIDE_WINDOW, E8F_WIDE_STEP_MONTHS,
    PRECANOPY_ANALOGUE, PRECANOPY_PLANTING_YEARS, PRECANOPY_CLOSURE_YEARS, PRECANOPY_W_TAILS,
    PRECANOPY_SLOW_STARTS_DAYS, PRECANOPY_SHARE_STARTS,
    FORCING_NSE_GAIN, FOREST_FORCING_CLUSTERS, FOREST_FORCING_EDGE_REGION, FOREST_FORCING_BASE_REGION,
    RANWELL_NEED_K1_GRID, RANWELL_NEED_K2_GRID, RANWELL_NEED_K3_GRID, RANWELL_NEED_NSE_TOL, RANWELL_PIPE_FOOT_M,
    RANWELL_SEASON_WINDOW_YEARS, RANWELL_ANTECEDENT_YEARS, RANWELL_MEMORY_MONTHS, RANWELL_SURFACE_CENSOR_M,
    CLEARFELL_DATE_ISO, RAF_VALLEY_LAT_DEG,
    E13_EXCESS_SHARE, E13_RMSE_TOL, E13_CLUSTERS, E13_BREAK_WINDOW, E13_MIN_LATER_MONTHS,
    E13B_WINDOW_YEARS, E13B_SEASON_A_MONTHS, E13B_SEASON_B_MONTHS, E13B_RESID_SUMMER_MONTHS, E13B_RESID_WINTER_MONTHS, E13B_RESID_WINTER_PHASE,
    RESIDUAL_DIAG_MIN_MONTHS, MIDAS_MONTH_MIN_DAYS, MODEL_B_BETA3_MIN,
)
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.model_utils import (build_ssm_frame, fit_ssm, fit_ssm_intercept, simulate_ssm, get_metrics,   # noqa: E402
                               sustained_monthly_response, climate_forcing_change_12, response_identified,
                               sustained_monthly_response_ddp, dry_bounds)
from utils.hindcast_utils import (                            # noqa: E402
    load_ccw, observed_series, hindcast_well, equilibrium_depth, usable_codes, compare_offset_censored,
    quantile_map,
)
from utils.render_utils import (MPL_DEFAULTS, apply_house_style,   # noqa: E402
                                render_figure)                     # noqa: E402  (J-6)
from utils.pastas_utils import spread_daily, continuous_start  # noqa: E402
from utils.midas_rain import read_daily  # noqa: E402
from utils.pet_alternatives import monthly_radiation_pet, midas_monthly_pm, midas_span, read_raf_monthly  # noqa: E402
from utils.clearfell_common import EDGE_WELLS  # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402
from utils.console_utils import (banner, done, info, phase, result, saved, step, track,  # noqa: E402
                                 warn)                                                   # noqa: E402

FORMS = (("A", False), ("B", True))
# 1.25.0 (D-332): the MHW form -- Model A at each well's depth to mean high water (Script 48's form M). It runs
# where a well has a ground level, at that well's own datum, so it is not a member of FORMS (whose fits are all
# built at DRAINAGE_DATUM); REPORT_FORMS is FORMS plus it, for the summaries and report numbers.
FORM_MHW = "M"
REPORT_FORMS = FORMS + ((FORM_MHW, False),)
FULL = "full"
LENGTHS = tuple(str(L) for L in RECLEN_LENGTHS_MONTHS) + (FULL,)
SIG_P = 0.05
from utils.reclen_common import (   # noqa: E402  (the suite's shared helpers, J-15)
    _censored_well_fit, _dkey, _e16_grounds, _e16_mhw, _model_a_store,
    _nse, beta3_bound_report, describe, fit_frame, free_run,
    load_inputs, mhw_depths, run_datum,
)


def well_experiments(well: str, cluster: int, h: pd.Series, cl: pd.DataFrame, mhw_datum: float = None) -> list:
    """forecast, hindcast_within and stability rows for one well, both forms; and (1.25.0, D-332) the MHW form
    "M", Model A at `mhw_datum` (the well's depth to mean high water), where one is given."""
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    te = {"forecast": h[h.index >= split], "hindcast_within": h[h.index < split]}
    by_datum = {}   # NB not `frames`: the stability loop below binds that name

    def frames_at(D):
        """full, pre and post frames built at datum D (the datum moves h_disp only, never the rows)."""
        if D not in by_datum:
            by_datum[D] = (build_ssm_frame(h, cl, lag=HEADLINE_LAG, drainage_datum=D),
                           build_ssm_frame(h[h.index < split], cl, lag=HEADLINE_LAG, drainage_datum=D),
                           build_ssm_frame(h[h.index >= split], cl, lag=HEADLINE_LAG, drainage_datum=D))
        return by_datum[D]
    forms = [(form, icpt, DRAINAGE_DATUM) for form, icpt in FORMS]
    if mhw_datum is not None and np.isfinite(mhw_datum):
        forms.append((FORM_MHW, False, float(mhw_datum)))
    rows = []
    base = {"well": well, "cluster": cluster}
    for form, icpt, D in forms:
        full, pre, post = frames_at(D)
        side = {"forecast": (pre, "tail"), "hindcast_within": (post, "head")}
        for exp in ("forecast", "hindcast_within"):
            fr_all, end = side[exp]
            for L in LENGTHS:
                if L == FULL:
                    fr = fr_all
                else:   # 1.24.0 (D-322): L calendar months adjacent to the split, not L rows
                    if end == "tail":
                        fr = fr_all[fr_all.index >= split - pd.DateOffset(months=int(L))]
                    else:
                        fr = fr_all[fr_all.index < split + pd.DateOffset(months=int(L))]
                    if not len(fr) or (fr.index[-1].to_period("M") - fr.index[0].to_period("M")).n + 1 < int(L) - 1:
                        continue   # the side does not span L calendar months
                f = fit_frame(fr, icpt)
                row = dict(base, form=form, experiment=exp, length=L, placement="adjacent")
                row.update(describe(f, icpt, fr))
                row.update(free_run(te[exp], cl, f, icpt, base=D))     # base explicit: the default binds 3.7 m
                rows.append(row)
        for L in LENGTHS:
            if L == FULL:
                frames = [("all", full)]
            else:
                # 1.24.0 (D-322): blocks of L calendar months from the record's first month, not L rows
                t0 = full.index[0] if len(full) else None
                k = ((full.index[-1].to_period("M") - t0.to_period("M")).n + 1) // int(L) if len(full) else 0
                frames = [(str(i), full[(full.index >= t0 + pd.DateOffset(months=i * int(L))) &
                                        (full.index < t0 + pd.DateOffset(months=(i + 1) * int(L)))]) for i in range(k)]
            for plc, fr in frames:
                f = fit_frame(fr, icpt)
                row = dict(base, form=form, experiment="stability", length=L, placement=plc)
                row.update(describe(f, icpt, fr))
                rows.append(row)
    return rows


def ccw_experiment(lev, lev_cols, cl, master):
    """The CCW 1989-96 hindcast at every length, from the start and from the end of the modern
    record, both forms. Script 39's admission, seeding, spin-up, censoring and offsets, unchanged."""
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        warn("CCW historic inputs not present — the ccw_hindcast experiment is skipped")
        return pd.DataFrame()
    obs, cmap = load_ccw()
    md = _model_a_store(pd.read_csv(INT_MASTER_DATA))
    md["k"] = md["Name_Original"].astype(str).str.lower().str.strip()
    md = md.set_index("k")
    adm = usable_codes(cmap, md, obs)
    adm = adm[adm["admitted"]]
    clh = cl[["P_m", "PET"]].apply(pd.to_numeric, errors="coerce").dropna()
    p_mean, pet_mean = float(clh["P_m"].mean()), float(clh["PET"].mean())
    first_month, last_month = obs["month"].min(), obs["month"].max()
    rows = []
    for r in adm.itertuples():
        col = lev_cols.get(normalize_well_name(r.well))
        if col is None:
            continue
        o, _n_cens = observed_series(obs, r.code, r.datum_offset_m)
        if o.empty:
            continue
        # 1.24.0 (D-322): Script 03's fit, censored on the dry months, over calendar months.
        h = lev[col].dropna()
        db = dry_bounds(col)
        db = db if len(db) else None
        t0 = min([h.index.min()] + ([db.index.min()] if db is not None else []))
        t1 = max([h.index.max()] + ([db.index.max()] if db is not None else []))
        span = (t1.year - t0.year) * 12 + (t1.month - t0.month) + 1      # calendar months on record
        cluster = int(md.loc[r.well, "Cluster"]) if "Cluster" in md.columns else -1
        for form, icpt in FORMS:
            for L in LENGTHS:
                for end in ("start", "end"):
                    if L == FULL:
                        if end == "start":
                            continue                       # the full record has one placement
                        hs, dbs, win = h, db, None
                    elif span >= int(L):
                        if end == "end":
                            hs, dbs, win = h, db, int(L)
                        else:
                            cut = t0 + pd.DateOffset(months=int(L))
                            hs = h[h.index < cut]
                            dbs = db[db.index < cut] if db is not None else None
                            dbs = dbs if (dbs is not None and len(dbs)) else None
                            win = int(L)
                    else:
                        continue
                    try:
                        f = fit_ssm(hs, cl, lag=HEADLINE_LAG, window=win, drainage_datum=DRAINAGE_DATUM,
                                    min_obs=RECLEN_MIN_FIT_MONTHS, intercept=icpt, with_corr=True,
                                    dry_bound=dbs)
                    except Exception:
                        f = None
                    row = {"well": r.well, "code": r.code, "cluster": cluster, "form": form,
                           "length": L, "end": end if L != FULL else "all"}
                    row.update(describe(f, icpt, f["resid"] if f is not None else None))
                    if f is None or not (f["beta_3_drainage"] > 0):
                        rows.append(row)
                        continue
                    betas = (f["beta_1_recharge"], f["beta_2_atmospheric_draw"], f["beta_3_drainage"])
                    datum = run_datum(f, icpt)
                    h0 = equilibrium_depth(betas, p_mean, pet_mean, drainage_datum=datum)
                    pred, _spin = hindcast_well(clh, betas, h0, first_month, last_month, 1.0,
                                                drainage_datum=datum)
                    common = o.index.intersection(pred.index)
                    nse, rmse, bias = get_metrics(o.loc[common], pred.loc[common])
                    oc, pc = o.loc[common].values, pred.loc[common].values
                    r_shape = float(np.corrcoef(oc, pc)[0, 1]) if len(oc) > 2 else np.nan
                    off = float(np.mean(pc - oc))
                    den = float(np.sum((oc - oc.mean()) ** 2))
                    row.update({"n_test": int(len(common)), "nse": float(nse), "rmse_m": float(rmse),
                                "bias_m": float(bias), "pearson_r": r_shape,
                                "nse_bias_removed": (1.0 - float(np.sum((oc - (pc - off)) ** 2)) / den)
                                if den > 0 else np.nan})
                    rows.append(row)
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Summaries
# ──────────────────────────────────────────────────────────────────────────────
def relative_deviation(df: pd.DataFrame) -> pd.DataFrame:
    """Per well x form x length: median over placements of |beta_3(L)/beta_3(full) - 1|."""
    st = df[(df["experiment"] == "stability") & df["fitted"].fillna(False).astype(bool)]
    ref = st[st["length"] == FULL].set_index(["well", "form"])["beta_3"]
    st = st[st["length"] != FULL].copy()
    st["b3_full"] = [ref.get((w, f), np.nan) for w, f in zip(st["well"], st["form"])]
    st["rel_dev"] = (st["beta_3"] / st["b3_full"] - 1.0).abs()
    st.loc[~(st["b3_full"] > 0), "rel_dev"] = np.nan
    g = st.groupby(["well", "cluster", "form", "length"])
    return g["rel_dev"].median().rename("rel_dev_median").reset_index().merge(
        g["identified"].mean().rename("identified_share").reset_index(),
        on=["well", "cluster", "form", "length"])


def stable_lengths(dev: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Each well's stable length per form, and that length in full-record Model B mean-reversion times."""
    efold_b = (df[(df["experiment"] == "stability") & (df["length"] == FULL) & (df["form"] == "B")]
               .set_index("well")["efold_months"])
    rows = []
    for (w, c, form), g in dev.groupby(["well", "cluster", "form"]):
        g = g.assign(L=g["length"].astype(int)).sort_values("L")
        ok = (g["rel_dev_median"] < RECLEN_STABLE_TOL).values
        stable = np.nan
        for i in range(len(g)):
            if ok[i:].all():
                stable = float(g["L"].iloc[i])
                break
        ef = float(efold_b.get(w, np.nan))
        rows.append({"well": w, "cluster": c, "form": form, "stable_length_months": stable,
                     "longest_length_tested": float(g["L"].max()), "efold_B_full_months": ef,
                     "stable_length_in_efolds": stable / ef if (np.isfinite(stable) and ef > 0) else np.nan})
    return pd.DataFrame(rows)


def groups(df: pd.DataFrame):
    yield "all", df
    for c, g in df.groupby("cluster"):
        if int(c) > 0:
            yield f"C{int(c)}", g


def by_cluster(df: pd.DataFrame, dev: pd.DataFrame, ccw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    def stats_(v):
        v = pd.to_numeric(v, errors="coerce").dropna()
        if not len(v):
            return np.nan, np.nan, np.nan, 0
        return float(v.median()), float(np.percentile(v, 10)), float(np.percentile(v, 90)), int(len(v))
    for exp in ("forecast", "hindcast_within"):
        sub = df[df["experiment"] == exp]
        for gname, g in groups(sub):
            for (form, L), gg in g.groupby(["form", "length"]):
                for metric in ("nse", "bias_m", "beta_3", "efold_months", "drainage_share"):
                    m, p10, p90, n = stats_(gg[metric])
                    rows.append(dict(group=gname, experiment=exp, form=form, length=L, end="",
                                     metric=metric, median=m, p10=p10, p90=p90, n_wells=n))
                rows.append(dict(group=gname, experiment=exp, form=form, length=L, end="",
                                 metric="identified_share", median=float(gg["identified"].fillna(False).astype(bool).mean()),
                                 p10=np.nan, p90=np.nan, n_wells=int(len(gg))))
    for gname, g in groups(dev):
        for (form, L), gg in g.groupby(["form", "length"]):
            for metric in ("rel_dev_median", "identified_share"):
                m, p10, p90, n = stats_(gg[metric])
                rows.append(dict(group=gname, experiment="stability", form=form, length=L, end="",
                                 metric=metric, median=m, p10=p10, p90=p90, n_wells=n))
    if len(ccw):
        for (form, L, end), gg in ccw.groupby(["form", "length", "end"]):
            for metric in ("nse", "bias_m", "pearson_r", "nse_bias_removed"):
                m, p10, p90, n = stats_(gg[metric])
                rows.append(dict(group="all", experiment="ccw_hindcast", form=form, length=L, end=end,
                                 metric=metric, median=m, p10=p10, p90=p90, n_wells=n))
    out = pd.DataFrame(rows)
    order = {L: i for i, L in enumerate(LENGTHS)}
    return out.sort_values(["experiment", "group", "form", "metric", "end"],
                           key=lambda s: s.map(order) if s.name == "length" else s,
                           kind="stable").reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# Identity checks: the full-length rows must reproduce Scripts 48 and 39
# ──────────────────────────────────────────────────────────────────────────────
def identity_checks(df: pd.DataFrame, ccw: pd.DataFrame) -> dict:
    out = {"vs48_max_abs_diff": np.nan, "vs48_n": 0, "vs39_max_abs_diff": np.nan, "vs39_n": 0,
           "vs48_M_max_abs_diff": np.nan, "vs48_M_n": 0}
    if OUT_48_MODEL_AB.exists():
        ab = pd.read_csv(OUT_48_MODEL_AB)
        ab["well"] = ab["well"].astype(str).apply(normalize_well_name)
        ab = ab.set_index("well")
        # 1.25.0: the A/B check keeps its scope; the MHW form is checked separately against Script 48's form M
        for forms_, key in (({"A", "B"}, "vs48"), ({FORM_MHW}, "vs48_M")):
            diffs = []
            for exp, d_ in (("forecast", "fwd"), ("hindcast_within", "rev")):
                f = df[(df["experiment"] == exp) & (df["length"] == FULL) & df["form"].isin(forms_)]
                for _, r in f.iterrows():
                    col = f"nse_{d_}_{r['form']}"
                    w = normalize_well_name(r["well"])
                    if w in ab.index and col in ab.columns and np.isfinite(r["nse"]) and np.isfinite(ab.loc[w, col]):
                        diffs.append(abs(r["nse"] - ab.loc[w, col]))
            if diffs:
                out.update({f"{key}_max_abs_diff": float(max(diffs)), f"{key}_n": len(diffs)})
    if len(ccw) and OUT_39_PER_WELL.exists():
        p39 = pd.read_csv(OUT_39_PER_WELL).set_index("well")
        c = ccw[(ccw["form"] == "A") & (ccw["length"] == str(LCSC_DATA_LIMIT)) & (ccw["end"] == "end")]
        diffs = [abs(r["nse"] - p39.loc[r["well"], "nse"]) for _, r in c.iterrows()
                 if r["well"] in p39.index and np.isfinite(r.get("nse", np.nan))]
        if diffs:
            out.update(vs39_max_abs_diff=float(max(diffs)), vs39_n=len(diffs))
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Report numbers
# ──────────────────────────────────────────────────────────────────────────────
def report_numbers(df, dev, stab, ccw, summ, checks) -> ReportNumbers:
    # J-15 (Script 50 suite 1.0.0): the transfer keys moved to 50c's transfer_report(); the record-length
    # keys below are unchanged.
    rr = ReportNumbers()
    def get(exp, group, form, L, metric, end=""):
        s = summ[(summ.experiment == exp) & (summ.group == group) & (summ.form == form)
                 & (summ.length == L) & (summ.metric == metric) & (summ.end == end)]
        return (float(s["median"].iloc[0]), int(s["n_wells"].iloc[0])) if len(s) else (np.nan, 0)
    gnames = ["all"] + [f"C{c}" for c in sorted(int(x) for x in df["cluster"].unique() if int(x) > 0)]
    for exp, tag in (("forecast", "fwd"), ("hindcast_within", "rev")):
        for g in gnames:
            for form, _ in REPORT_FORMS:          # 1.25.0: and the MHW form, M
                for L in LENGTHS:
                    v, n = get(exp, g, form, L, "nse")
                    if n:
                        rr.add(f"reclen_nse_{tag}_{form}_median_L{L}_{g}", v, unit="",
                               note=f"median free-run NSE, Model {form}, fitted on {L} months "
                                    + ("before" if tag == "fwd" else "from")
                                    + f" {MODEL_AB_SPLIT_DATE}; n = {n} wells ({g})")
    for g in gnames:
        for form, _ in REPORT_FORMS:
            for L in LENGTHS[:-1]:
                v, n = get("stability", g, form, L, "rel_dev_median")
                if n:
                    rr.add(f"reclen_beta3_reldev_{form}_median_L{L}_{g}", v, unit="fraction",
                           note=f"median over wells of the median over placements of |beta_3(L)/beta_3(full) - 1|, "
                                f"Model {form}, L = {L}; n = {n} wells ({g})")
                v, n = get("stability", g, form, L, "identified_share")
                if n:
                    rr.add(f"reclen_identified_share_{form}_median_L{L}_{g}", v, unit="fraction",
                           note=f"median over wells of the share of placements of {L} months on which Model {form}'s "
                                f"beta_3 is identified; n = {n} wells ({g})")
    for g, gg in groups(stab):
        for form, _ in REPORT_FORMS:
            s = gg[gg["form"] == form]
            for col, unit, lab in (("stable_length_months", "months", "stable length"),
                                   ("stable_length_in_efolds", "", "stable length in full-record Model B mean-reversion times")):
                v = pd.to_numeric(s[col], errors="coerce").dropna()
                rr.add(f"reclen_{col}_{form}_median_{g}", float(v.median()) if len(v) else np.nan, unit=unit,
                       note=f"median {lab}, Model {form} (tolerance {RECLEN_STABLE_TOL:g}); "
                            f"{len(v)} of {len(s)} wells reach it within the lengths tested ({g})")
            rr.add(f"reclen_stable_n_wells_reached_{form}_{g}",
                   float(pd.to_numeric(s["stable_length_months"], errors="coerce").notna().sum()), unit="count",
                   note=f"wells whose Model {form} beta_3 becomes stable within the lengths tested ({g})")
    if len(ccw):
        for form, _ in FORMS:
            for L in LENGTHS:
                for end in (("all",) if L == FULL else ("start", "end")):
                    for metric in ("nse", "bias_m", "pearson_r"):
                        v, n = get("ccw_hindcast", "all", form, L, metric, end)
                        if n:
                            rr.add(f"reclen_ccw_{metric}_{form}_median_L{L}_{end}", v,
                                   unit="m" if metric == "bias_m" else "",
                                   note=f"CCW 1989-96 hindcast, Model {form} fitted on {L} months from the "
                                        f"{end} of the modern record; median over n = {n} wells")
    full = df[(df["experiment"] == "stability") & (df["length"] == FULL)]
    for g, gg in groups(full):
        for form, _ in REPORT_FORMS:
            s = gg[gg["form"] == form]
            for col, unit, lab in (("rho_ar1_expected", "", "expected spring persistence (1 - beta_3)^12 (D-221)"),
                                   ("efold_months", "months", "mean-reversion time -1/ln(1 - beta_3)")):
                v = pd.to_numeric(s[col], errors="coerce").dropna()
                rr.add(f"reclen_{col}_full_{form}_median_{g}", float(v.median()) if len(v) else np.nan, unit=unit,
                       note=f"median {lab}, Model {form}, full record; n = {len(v)} wells ({g})")
    # T-103: the comparison window against the full record, per well (Script 03's 03_15)
    ws = pd.read_csv(OUT_03_PER_WELL_WINDOW_SENS)
    pv = _model_a_store(ws).pivot_table(index=["Name_Original", "Cluster"], columns="basis",
                                        values="beta_3_drainage").reset_index()   # 1.28.0: Model A (*_model_a)
    if {"comparison_window", "full_record"} <= set(pv.columns):
        pv["ratio"] = pv["comparison_window"] / pv["full_record"]
        pv.loc[~(pv["full_record"] > 0), "ratio"] = np.nan
        pv = pv.rename(columns={"Cluster": "cluster"})
        for g, gg in groups(pv):
            v = gg["ratio"].dropna()
            for q, val in (("median", v.median()), ("p10", np.percentile(v, 10) if len(v) else np.nan),
                           ("p90", np.percentile(v, 90) if len(v) else np.nan)):
                rr.add(f"window_full_beta3_ratio_{q}_{g}", float(val), unit="",
                       note=f"per-well beta_3 on the comparison window ({LCSC_DATA_LIMIT} months) over beta_3 on the "
                            f"full record, Model A (03_15); {q} over n = {len(v)} wells ({g}); T-103")
    rr.add("reclen_check_vs48_max_abs_nse_diff", checks["vs48_max_abs_diff"], unit="",
           note=f"identity check: full-length forecast / hindcast_within NSE against Script 48's split-sample NSE; "
                f"largest absolute difference over {checks['vs48_n']} well-form-direction pairs (expected 0)")
    rr.add("reclen_check_vs48_M_max_abs_nse_diff", checks["vs48_M_max_abs_diff"], unit="",
           note=f"identity check: full-length forecast / hindcast_within NSE of the MHW form against Script 48's form M "
                f"(nse_fwd_M / nse_rev_M); largest absolute difference over {checks['vs48_M_n']} well-direction pairs "
                f"(expected 0)")
    rr.add("reclen_check_vs39_max_abs_nse_diff", checks["vs39_max_abs_diff"], unit="",
           note=f"identity check: CCW hindcast NSE, Model A on the last {LCSC_DATA_LIMIT} months, against Script 39; "
                f"largest absolute difference over {checks['vs39_n']} wells (expected 0)")
    return rr


# ──────────────────────────────────────────────────────────────────────────────
# Figure
# ──────────────────────────────────────────────────────────────────────────────
def plot(summ: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    Ls = [L for L in LENGTHS if L != FULL]
    x = np.array([int(L) for L in Ls], dtype=float)
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 6.6), dpi=160)
    panels = ((axes[0, 0], "stability", "rel_dev_median", "(a) |β₃(L)/β₃(full) − 1|, median over wells"),
              (axes[0, 1], "forecast", "nse", f"(b) Forecast NSE after {MODEL_AB_SPLIT_DATE[:4]}"),
              (axes[1, 0], "hindcast_within", "nse", f"(c) Hindcast NSE before {MODEL_AB_SPLIT_DATE[:4]}"))
    clusters = sorted(int(g[1:]) for g in summ["group"].unique() if g.startswith("C"))
    for ax, exp, metric, title in panels:
        for c in clusters:
            for form, ls in (("A", "-"), ("B", "--")):
                s = summ[(summ.experiment == exp) & (summ.group == f"C{c}") & (summ.form == form)
                         & (summ.metric == metric)].set_index("length").reindex(Ls)
                ax.plot(x, s["median"].values, ls=ls, marker="o", ms=3, lw=1.1,
                        color=CLUSTER_COLOURS.get(c, "0.4"),
                        label=(CLUSTER_LABELS.get(c, f"C{c}") if form == "A" else None))
        ax.set_title(title, loc="left", fontsize=9)
        ax.set_xlabel("record fitted, L (months)")
        ax.grid(alpha=0.3)
    axes[0, 0].axhline(RECLEN_STABLE_TOL, color="0.4", lw=0.8, ls=":")
    axes[0, 0].set_ylim(bottom=0)
    for ax in (axes[0, 1], axes[1, 0]):
        ax.axhline(0, color="0.5", lw=0.7)
        ax.set_ylim(-1, 1)
    ax = axes[1, 1]
    for form, ls in (("A", "-"), ("B", "--")):
        for end, mk in (("end", "o"), ("start", "s")):
            s = summ[(summ.experiment == "ccw_hindcast") & (summ.group == "all") & (summ.form == form)
                     & (summ.metric == "nse") & (summ.end == end)].set_index("length").reindex(Ls)
            ax.plot(x, s["median"].values, ls=ls, marker=mk, ms=3, lw=1.1, color="0.25",
                    label=f"Model {form}, L from the {end}")
    ax.axhline(0, color="0.5", lw=0.7)
    n_ccw = int(summ[(summ.experiment == "ccw_hindcast") & (summ.metric == "nse")]["n_wells"].max() or 0)
    ax.set_title(f"(d) CCW 1989–96 hindcast NSE, median of {n_ccw} wells", loc="left", fontsize=9)
    ax.set_xlabel("record fitted, L (months)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=6.5, loc="lower right")
    axes[0, 1].legend(fontsize=6.5, loc="lower right", title="solid Model A, dashed Model B", title_fontsize=6.5)
    for a in axes.ravel():
        a.set_xlim(x.min() - 6, x.max() + 6)
    fig.tight_layout()
    fig.savefig(OUT_50_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_50_FIG.name)


# ──────────────────────────────────────────────────────────────────────────────
def main(no_fig: bool = False) -> int:
    banner("50a", "What the record length decides (D-222)", version=__version__)
    DIR_50A.mkdir(parents=True, exist_ok=True)

    phase(1, "Inputs")
    lev, lev_cols, cl, master = load_inputs()
    info(f"{len(master)} reference wells; lengths {', '.join(LENGTHS)} (fitted monthly changes); "
         f"split {MODEL_AB_SPLIT_DATE}; stability tolerance {RECLEN_STABLE_TOL:g}")

    phase(2, "Forecast, within-record hindcast and stability, both forms and the MHW form, every well")
    mhw = mhw_depths()          # 1.25.0 (D-332): the MHW form's per-well datum
    info(f"MHW form: {sum(1 for k in master['_n'] if k in mhw)} of {len(master)} reference wells have a ground level")
    rows = []
    for _, r in master.iterrows():
        col = lev_cols.get(r["_n"])
        if col is None:
            warn(f"{r['Name_Original']}: no level column")
            continue
        rows += well_experiments(r["_n"], int(r["Cluster"]), lev[col].dropna(), cl, mhw_datum=mhw.get(r["_n"]))
    df = pd.DataFrame(rows)
    df["fitted"] = df["fitted"].fillna(False).astype(bool)
    info(f"{len(df)} fits ({int(df['fitted'].sum())} succeeded)")

    phase(3, "The CCW 1989-96 hindcast at every length")
    ccw = ccw_experiment(lev, lev_cols, cl, master)
    if len(ccw):
        info(f"{ccw['well'].nunique()} admitted wells, {len(ccw)} hindcasts")

    phase(4, "Stable lengths and the cluster summary")
    dev = relative_deviation(df)
    stab = stable_lengths(dev, df)
    summ = by_cluster(df, dev, ccw)
    for form, _ in REPORT_FORMS:
        s = stab[stab["form"] == form]
        v = s["stable_length_months"].dropna()
        e = s["stable_length_in_efolds"].dropna()
        step(f"Model {form}: stable length median {v.median():.0f} months "
             f"({len(v)} of {len(s)} wells reach it); in mean-reversion times, median {e.median():.2f}")

    phase(5, "Identity checks against Scripts 48 and 39")
    checks = identity_checks(df, ccw)
    for k in ("vs48", "vs48_M", "vs39"):
        d, n = checks[f"{k}_max_abs_diff"], checks[f"{k}_n"]
        (step if (n and d < 1e-9) else warn)(f"{k}: largest |ΔNSE| {d:.3g} over {n} comparisons")

    phase(6, "Outputs")
    df.to_csv(OUT_50_PER_WELL, index=False); saved(f"{OUT_50_PER_WELL.name} ({len(df)} rows)")
    summ.to_csv(OUT_50_BY_CLUSTER, index=False); saved(f"{OUT_50_BY_CLUSTER.name} ({len(summ)} rows)")
    ccw.to_csv(OUT_50_CCW, index=False); saved(f"{OUT_50_CCW.name} ({len(ccw)} rows)")
    stab.to_csv(OUT_50_STABLE, index=False); saved(f"{OUT_50_STABLE.name} ({len(stab)} rows)")
    rr = report_numbers(df, dev, stab, ccw, summ, checks)
    beta3_bound_report(rr, {   # 1.25.0 (D-332)
        "reclen_fits": (df, "beta_3", "every record-length fit (50_01: forecast, within-record hindcast, stability)"),
        "reclen_full_record": (df[(df["experiment"] == "stability") & (df["length"] == FULL)], "beta_3",
                               "full-record fit per well (50_01 stability, full)"),
        "ccw_by_length": (ccw, "beta_3", "the CCW hindcast at every length (50_03)"),
    })
    rr.save(OUT_50A_REPORT_NUMBERS); saved(f"{OUT_50A_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    if not no_fig:
        plot(summ)
    result("record length", f"{df['well'].nunique()} wells; see {OUT_50_BY_CLUSTER.name}")
    done("50a")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="What the record length decides (D-222)")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
