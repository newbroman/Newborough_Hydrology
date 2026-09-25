# Numbers proof — report9 and report10, document first (2026-09-24j)

*Session `session_01A3XmyBJYxysNudx48fRJSa` (Claude Opus 5.5, Cowork bridge), against public `main` `2492be5`.
Method: `proof_copy.py report9 --bundle`, `proof_copy.py report10`; every UNTRACED and STALE row (118)
checked against the committed CSVs — first pass by three delegated readers, every DRIFT call then
re-derived by hand before an edit (the readers were wrong on five of them: 13.16, −0.82, +0.014,
the Forest-Control summer minima and the "stale" FE2 p-value all trace).*

report9: 2605 numbers — 80 DENIED (matcher false matches already adjudicated), 77 UNTRACED, 1 STALE,
117 ELSEWHERE. report10: 690 numbers — 74 DENIED, 38 UNTRACED, 2 STALE, 53 ELSEWHERE.
ELSEWHERE rows (a match in a CSV outside the section's declared sources) were not worked this pass.

## A. Corrected in place (factual drift; a CSV cell names the same quantity)

| Where | Was | Now | Source |
|---|---|---|---|
| report9 §4.5.5 | β₃–elevation r = −0.77, p = 0.001 | r = −0.831, p < 0.001 (as §4.9.4 says) | 10c_forest_zone_correlations.csv |
| report9 §4.6.4 | Jun–Sep Impact step +46 mm [−69, +162], p 0.44, R² 0.34 | +50 mm [−68, +168], p 0.41, R² 0.31 | 10_consolidated · ANCOVA_Forest_Impact_clearfell_step_summer / _summer_R2 |
| report9 §4.6.6 | tier Δβ₁ Forest −0.05, Coastal −0.32, Climate −0.13; 5.8 % | −0.06, −0.29, −0.12; 5.6 % | 10e_report_numbers / 10e_01 (Coastal mean derived) |
| report9 §4.6.6 | Forest-Ctrl mean Δβ₂ +0.15; WMC3 Δβ₂ −0.28; NW10/CEH2 Δβ₁ +0.28/+0.12 | +0.11; −0.31; +0.26/+0.09 | 10e_report_numbers |
| report10 §5.5 (2.81 → 2.65) | 5.8 % | 5.6 % | 10e_01 |
| report9 §4.6.7 | Edge synthetic control +41 mm, p 0.22 | +40 mm, p 0.23 | 10f_02_synthetic_control_results.csv |
| report9 §4.7.2 | "The negative P_winter coefficient in the Forest cluster (−0.00006)" | "near-zero … (+0.00005, p = 0.924)" — the table above it already said +0.00005 | 11_forecast_winter_transfer_functions.csv |
| report9 §4.7.5 | 214.10 | 214.11 | 11_forecast_pflood_threshold_equations.csv |
| report9 §4.8.4 | MSL5 = 0.257 + 0.959·EWI, r 0.98, RMSE 61; within 150 mm; 60 vs 63 mm; forest RMSE 152 | 0.378 + 0.964·EWI, r 0.97, RMSE 66; within 182 mm; 66 vs 67 mm; 181 mm | 26_report_numbers ewi_msl5_*; 26_ewi_msl5_comparison.csv |
| report9 §4.8.4 | index SE 454 / 512 / 1112 mm | 455 / 513 / 1115 | 26_index_precision_by_cluster (reference) |
| report9 §4.13.1 | 2080s annual −0.033 / C4 −0.047 / C1 −0.017; winter +0.056; summer −0.064 / −0.121, C2 −0.134; MSL5 2050s −12; summer ranges −38 to −70, −71 to −134 | −0.032 / −0.046 / −0.016; +0.055; −0.063 / −0.118, −0.131; −11; −37 to −69, −69 to −131 | 19_scenario_summary.csv (unchanged since 26 Aug); 26b_msl5_ukcp18_projection_summary.csv |
| report10 §5.2.1, §5.3.1 | sunshine-hours residual r = −0.026 (×2) | −0.032 | 24_residual_climatology.csv corr_sun_resid; 24_05_diagnostic_summary.txt |
| report10 §5.3.1 | median −0.0045, 58 of 66 negative | −0.0046, 54 of 66 (report9 already said twelve positive) | 20_residual_perwell.csv |
| report10 §5.5.1 | tier β₁ declines −3.8 / −2.0 / −10.2 / −13.1 % | −3.9 / −2.9 / −10.3 / −11.8 % (mean of per-well %) | 10e_01 |
| report10 §5.6.2 | NW2 −0.0029, CEH2 −0.0048 | −0.0015, −0.0052 | 20_residual_perwell.csv |
| report10 §5.6.3 | NW10 β₂ 2.628, CEH2 2.891, C4 median 2.634; NW10 β₃ 0.043, C4 median 0.019 | 2.623, 2.817, 2.554; 0.040, 0.018 (comparison window, 03_master_data, one basis throughout — the text had mixed bases) | 03_master_data.csv |
| report10 §5.7.2 | C4 mean residual −0.0067 | −0.0075 | 20_residual_perwell × 03_master_data Cluster |

22 confirmed citation rows added (`scratch/np25/cite_rows.py`); cite_check `--index-only` 0 DRIFTED.

## B. For Martin — a claim, not just a number

1. **report9 §4.9.6 and report10 §5.2.1 give different Spearman statistics for the same test** (residual magnitude vs Easting/Northing: −0.055/0.66, +0.093/0.46 against +0.099/0.43, +0.111/0.37; the signed-residual pair likewise). No script emits either set, and a recompute from the residual CSVs reproduces neither. Needs an emit (Script 16 or 20) before either chapter can be trusted.
2. **report10 §5.7.2: "the forest clusters carry the most negative residuals"** — C4 does (−0.0075); C5 is −0.0010, second least negative. The number is fixed; the sentence's claim about C5 is yours.
3. **report9 §4.1.1 "no significant trend over the full record (p = 0.498)"** — nothing emits it; OLS on the 94 complete years gives p = 0.57 (t 0.57). Conclusion unchanged; needs an emit in Script 00.
4. **report9 §4.9.2 / report10 §5.1.1: the 21-well C3 inland-axis correlations (β₁ +0.76, β₃ +0.58, Sy −0.83)** — no CSV carries a 21-well version; Script 29's is 16 wells on dist_coast (0.848 / 0.692 / −0.844). §4.5.5 quotes the β₃ one as p = 0.006, §4.9.2 as p = 0.009.
5. **Amplification vs β₂/β₃ (report9 §4.12, report10 §5.3.2: r ≈ +0.74, r = −0.49)** — reproduces from nothing: 35_per_well_amplification gives +0.73/−0.54 (n 66), 35_results.txt says +0.65/−0.42 (n 64, stale text file), Script 33's amplification gives +0.79/−0.56.
6. **Script 19 and Script 21 compute the forestry scenarios differently** (C5 clearfell annual 0.040 vs 0.042 m; C5 broadleaf summer +0.006 vs +0.001). §4.13.2 quotes 21, the viewer shows 19.
7. **§4.13.1 "three to five times smaller"** — the ratio is 3.0–5.4 (C1 exceeds five at both horizons).
8. **report10 §5.2.3 constrained β₂ = 0.92, CI [0.57, 1.19]** — in no 30_c4_* CSV.

## C. Consistent but unregistered — add to T-84 (emit and bind)

- 00: annual-rain trend p (above); wettest/second-wettest years 1,040 / 1,022 mm trace (thousands separator defeats the matcher).
- 10e: Coastal-Ctrl tier mean (no row); tier % declines (§5.5.1).
- 10d: Forest-Ctrl era means −1.822/−1.753/−1.766 and WMC3's (pooled well-years from 10d_01).
- 10h: FE2 donor divergence +28 mm, p = 0.0008 (the proof tool's "stale" flag pointed at the WMC3-only row).
- 25: rolling-window 10-yr SD 13.16 and c–covariate correlations −0.60 to −0.82 (usable rows of 25_13).
- 26: EWI residual bound, out-of-VW RMSE, forest RMSE (above).
- 19/26b: the §4.13.1 values (multi-key labels; no citation rows written).
- report10 unsourced: k = 6 sensitivity; n = 46 / Mann–Whitney p = 1.000 / carry-over p = 0.022 / −7.0, 7.03, 19.66 mm yr⁻¹ (§5.7.5, §5.7.7); 1989–96 rainfall 0.770 m yr⁻¹ (§4.14.1; windows tried give 0.767–0.772).

## D. Not done this pass

ELSEWHERE rows (170); the three xmean cross-references (report9 Figure 39 / Figure 68, report10 §4.8.1→Figures 46/47 placed in §4.8.3, §4.6.5→Figure 37 in §4.6.7) — read, none wrong on its face; chapters other than 9 and 10; the printed read.

## E. Martin's rulings on §B (2026-09-24, same evening) and what followed — changelog 24k

1. **Script 16 to emit the residual–position statistics.** Found: report9 §4.9.6's values reproduce exactly from `20_residual_perwell.csv` (|α| vs E −0.055/0.66, vs N +0.093/0.46; signed −0.024/0.85, −0.116/0.35); report10 §5.2.1's (+0.099, +0.111, −0.226, −0.171) are an older residual field, and its "eight positive residuals" is twelve. report10 §5.2.1 corrected to report9's values; the "weak west-to-east gradient" sentence goes with them (the signed residual has no gradient on either axis). Spec S1 below.
2. **Corrected:** report10 §5.7.2 now reads "the Main Forest cluster carries the most negative residual in the network (C4 mean −0.0075 m/month)".
3. **Script 01 to emit the annual-rainfall trend p.** Spec S3 below.
4. **Investigated.** The 21-well figures are a Pearson correlation against position projected on a 45° (SW–NE) bearing, never written to a CSV. Recomputed on the committed data: β₁ +0.758 (p < 0.001), β₃ +0.561 (p = 0.008), Sy (18_wtf_01 Sy_median) −0.846 (p < 0.001); fitted Sy 0.37 → 0.26 across the axis. The text's +0.76 still holds; +0.58/p 0.009 and −0.83 are an earlier state (and §4.5.5's p = 0.006 an earlier one again). Script 29 already emits the same gradient on the physical axis, distance from the coast, but for 16 wells (CEH36, WMC3 and three wells without a Script 25 dist_coast drop out): 0.848 / 0.692 / −0.844, Sy 0.398 (CEH21) → 0.246 (NW13). Options in S4.
5. **Yes — Script 35 is the source** (`phase 4, SSM calibration`: Pearson, amp_coefficient vs β₂/β₃, CEH13/CEH14 excluded as SSM-unreliable, n = 64). The documents carried the 18 Aug run (+0.74 / −0.49); the D-189 spring-convention run of 21 Sep moved it to **+0.65 / −0.42 (p = 0.001)**. Corrected in report9 §4.12 and report10 §5.3.2. Script 35 writes these only to `35_results.txt`, so nothing gates them — spec S5.
6. **Why Scripts 19 and 21 do not converge.** Same single-step perturbation (β₁·ΔP_eff − Δβ₂·PET; the β₃ term cancels in both), different inputs and aggregation:
   - *Coefficients:* 19 uses each well's own β and averages the per-well Δh over the cluster; 21 uses the cluster-centroid β from `pipeline_scenario_params.csv`. The mean of per-well responses is not the response of the mean coefficients.
   - *Where interception applies:* 19 applies it by land cover (the committed `in_forest` flag, D-046) — C4/C5 wells not under canopy get no interception change, and the two C3 wells that are under it do; 21 applies it to the whole cluster.
   - *Seasons:* 19's "annual" is the mean of its winter and summer responses, each on its own seasonal climatology; 21's annual is the mean over the twelve calendar months, winter Oct–Mar, summer Jun–Sep.
   - *Broadleaf β₂:* 19 uses two multipliers (winter 0.87×, summer 1.09×); 21 the twelve-month `BROADLEAF_B2_MONTHLY_MULT` profile. That is most of the C5 broadleaf-summer gap (+0.006 vs +0.001).
   Neither is wrong; they answer "what does the map show at each well" (19) and "what does the cluster do" (21). If the viewer and the report are to agree, one aggregation has to be chosen — your call.
7. **Accepted as is** ("three to five times").
8. **Investigated — it traces.** report10 §5.2.3's 0.92 is the **C1** centroid β₂ (not C4): `03_03_cluster_mechanistic_coefficients.csv` 0.923, p = 3.6 × 10⁻⁵; CI [0.57, 1.19] from `03_05_bootstrap_ci.csv` (0.566, 1.194). Three confirmed citation rows added.

### Specs awaiting sign-off (no code written)

**S1 — Script 16 1.6.0: the residual field and its spatial statistics.** The per-well steady-state residual α = β₂·P̄ET + β₃·h̄_disp − β₁·P̄ is computed today inside Script 20 `build_well_table()` (phase 9); Script 16 runs at phase 7, so it cannot read 20's output. Proposal: move the α computation into a shared function (`utils/model_utils.steady_state_residual()`), inputs unchanged (01 maod/locations/elevations, 03_master_data, climate over the well record); Script 16 calls it, writes `16_residual_perwell.csv`, and adds to `16_report_numbers.csv`: n, n_positive, median, max, per-cluster medians, and Spearman ρ and p of |α| and of α against Easting and Northing. Script 20 calls the same function (its `20_residual_perwell.csv` must come out byte-identical — the check). Citation rows for §4.9.6 and §5.2.1 follow.
**S3 — Script 01 1.22.0: annual-rainfall trend.** OLS of annual rainfall on year over complete calendar years (Months_complete = 12); emit slope (mm/yr), t, p and n to `01_report_numbers.csv`. Window to confirm: the full record 1931–2025 (n = 94; expected p ≈ 0.57, so §4.1.1's 0.498 becomes 0.57, conclusion unchanged). Note Script 00 already emits the parallel PET trends over the same window; putting the rainfall one in 01 splits the pair across two files.
**S4 — the C3 inland gradient, pick one.** (a) Rewrite §4.9.2/§5.1.1/§4.5.5 onto Script 29's existing, gated dist_coast figures (16 wells: 0.85 / 0.69 / −0.84; Sy 0.40 → 0.25) — no code. (b) Script 29 1.x adds the 21-well projection on a named bearing (`C3_INLAND_AXIS_BEARING_DEG` = 45 in config) and emits r/p/n and the fitted Sy ends; text becomes +0.76 / +0.56 (p = 0.008) / −0.85, Sy 0.37 → 0.26. Recommendation: (a) — it is already emitted, and distance from the eroding coast is the physical quantity the paragraph argues from.
**S5 — Script 35 1.3.0:** write the phase-4 calibration (r, p, n for β₂ and β₃, the exclusion list) to `35_report_numbers.csv` as well as the text file; bind the two report sentences.

## F. The rest of the corpus — report6–16 (except 9, 10), Methods Supplement, Supplementary Material (24k, Martin: "check the numbers in all chapters … the methods supplement and the supplementary methods")

`proof_copy` on every chapter: report6, 7, 12, 14, 15, 16 have no untraced rows; report8 19 + 2 xref, report11 1, report13 1, master 1; Methods Supplement 193 untraced + 2 stale + 4 xref; Supplementary Material 142 untraced + 2 xref. 360 rows checked by six delegated readers (`scratch/proof/verify_out_{R,M1,M2,M3,S1,S2}.csv`); every correction below re-derived by hand before it was made.

**The pattern:** most of the drift is fallout of the D-189 full run (21 Sep, spring = months 2–4): every spring quantity moved (Scripts 26, 32, 33, 34, 35, 10l) and the documents were never swept for them.

### Corrected
- **report8** §3.4.5 Sy vs 1/β₃ r 0.13 → 0.11 (18_wtf_05; Paper 1 already said 0.11); also report10 §5.6.1. §3.7.5 gap-fill counts 13/1302 (1.0 %), 28/895 (3.1 %) → 10/1274 (0.8 %), 32/869 (3.7 %) (26_report_numbers; 4 citation rows).
- **report10** §5.7.5 site-mean spring trend −7.0 (p 0.52) → −4.8 (p 0.63); §5.7.7 7.03 / 19.66 → 4.77 / 19.78 (32_results.txt, D-189 run).
- **Methods Supplement v2_0_20 → v2_0_23:** datum sensitivity (C4 p 0.044/0.0017/0.022 → 0.047/0.0016/0.023; C5 R² 0.648/0.685 → 0.643/0.683, p 2 → 1 × 10⁻¹⁶; ΔR² −0.059/−0.032 → −0.058/−0.031, twice); centroid n 236–248 → 237–249; C5 bootstrap CI 2.20–2.65 → 2.22–2.66; C1 post-2018 β₁ 4.93 (4.47–5.40) → 4.94 (4.50–5.42); CEH22 audit gap 0.0011 → 0.0007 (r 0.857 → 0.856); 09e forward residual +0.081 → +0.073; 10a p 0.253/0.562 → 0.249/0.555; 10k R² 0.856/N 2475 → 0.848/2489; 25 ΔAIC −4.9/−15.5 → −4.8/−15.3, far-field −6.14 → −6.35, C3 rate −24.47 → −24.45, C3 gradient −3.23 → −3.19, forest-free exponential δ₀/L/c −40.24/407/−5.24 → −40.63/489/+2.12; 22 Durbin–Watson IQR 2.11–2.37 → 2.15–2.41, φ median/mean −0.12/−0.13 → −0.13/−0.14; 32 spring trends (×2); 41 restock index 2026 0.975 → 0.853 (still the fall the text describes); C4 Sy 0.202/0.227 → 0.244/0.260 (direction holds); clearfell β₂ multiplier 1.0315 (0.9830 − 0.9515) → 1.0189 (0.9435 − 0.9247), thinning 1.0157 → 1.0094 (pipeline_scenario_params.csv); 10e tier Δβ₂ −0.28/−0.03 → −0.31/−0.10 ("under the v1.4.0 fits" → "on the current fits"); EWI fit 0.195 + 0.924·EWI, r 0.94, RMSE 107/100/160/227 → 0.378 + 0.964·EWI, r 0.97, RMSE 66/66/67/181.
- **Supplementary Material v1_33 → v1_34:** C4/C3 mean head 9.52/6.09 → 9.24/7.00 m AOD (as report9); rainfall AR(1) φ 0.211 → 0.207; spring trend −7.0/0.52 → −4.8/0.63; Table S10.1 figure numbers 61/62 → 73/74 (Script 36, Script 33 — figure_map.csv); **Table S7.1 regenerated** — it is now a generated table (`table_configs` 1.12.0, `sm/TableS71`); 497 of 840 cells were a pre-D-189 run; its caption constants refreshed (part of T-57; the new S7.2 is still owed).

### For Martin — claims, not numbers
1. **Script 34 envelope (report9 §4.12, MS Script 34 chapter, SM Note S11).** Now −0.16 to +0.23 m, 17 falling / 38 rising of 55 admissible pairs (was −0.14 to +0.22, 19/47 of 66); most negative 2017→2019 −161 mm, most positive 2015→2024 +230. The 2017→2023 anchor now returns −104.7 mm (n = 60), so the MS sentence "reproduces the −96.8 mm headline" is no longer true — the Script 20 two-window figure (−97 mm) and Script 34's anchor have parted. The conclusion (sign-changing, window-dependent) stands. Not edited.
2. **SM Table S8.1 / the four-zone spring model (10l_06).** R² 0.57 → 0.53; Edge spring step −46 mm (p = 0.011) → −32 mm (p = 0.36); C3/Warren −9.7 (p 0.41) → +29.8 (p 0.19). The text's "the Edge step … is the only nominally significant spring BACI result" no longer holds — no spring step is significant. Not edited.
3. **MS Script 29 "Headline result (2026-05-29)" table** — dated, and no longer what Script 29 returns (β₁ R² 0.864 not 0.813; τ's best-single Δ +0.608 not +0.317). Regenerate as a generated table, or keep it as a dated record? Also the S4 decision above bears on it.
4. **Unsourced in the MS/report8** (no CSV reproduces them): Feb-2026 PET anomaly 66.8 / 25.7 mm; CEH42 pre-felling baseline 3.4 years; coastal δ₀ ≈ 0.13 m and L ≈ 1.5 km; zero crossing "near 1400 m" (current fit ≈ 1469 m); 2.5 % of annual flux (Script 23); 1,433 / 1,304 annual rows; CEH14 NSE −3.21; n = 33, −0.513 (Script 41); r = 0.945, n = 829; report8 §3.2.3 CEH3 at k = 4 (no pre-blacklist run committed); report8 §3.5.4 Climate-control distances 571–1056 m (no metric reproduces 1056). report10 §5.7.5's own-panel OLS variant (−8.0, p 0.42) is not in 34_results.txt either.
5. **Broadleaf β₂ multipliers in the MS / viewer text** (0.87×/1.09×, 1.05/1.10) against `config.BROADLEAF_B2_WINTER/SUMMER` 0.8817/1.075 — flagged by the number index, not worked here.

## G. Martin's rulings on §E/§F (24l) and what was done

- **Q3 (which record?):** §4.1.1's sentence follows "over the full 95-year record" for summer temperature, so "the full record" means the RAF Valley record, 1931–2025. The quoted p = 0.498 reproduces from neither window: OLS on complete years gives p = 0.57 (1931–2025, n = 94) and p = 0.65 (2006–2025, n = 20); Mann–Kendall 0.78 / 0.58. Spec S3 now emits BOTH windows from Script 01 so the sentence can quote whichever is meant.
- **S4 done:** report9 §4.9.2, §4.5.5 and report10 §5.1.1 rewritten onto Script 29's committed figures (distance from the coast, 16 C3 wells: β₁ +0.85, β₃ +0.69 (p = 0.003), Sy −0.84, Sy 0.40 CEH21 → 0.25 NW13). 6 + 3 citation rows.
- **Script 35 1.3.0** (+ paths 1.32.0): the SSM calibration is written to `35_report_numbers.csv` (amp_vs_beta2/beta3 r, p, n). Exercised in an isolated copy (uv 3.12 + the project venv, committed inputs): `35_per_well_amplification.csv` byte-identical, the new CSV reads +0.648 / −0.420, p = 0.00055. **So the report's "p = 0.001" (taken from the rounded text file) is p < 0.001** — corrected in report9 §4.12 and report10 §5.3.2. The new CSV is placed in outputs from that run; Martin's `--step 35` rewrites it identically.
- **Scripts 19 and 21 both reported:** report9 §4.13.2 gains a paragraph giving Script 19's per-well-averaged values beside Script 21's cluster-centroid values, with the reasons they differ. (Not the land cover at C5: all five C5 wells are under canopy; the difference is per-well β, the season definitions and the broadleaf profile.) MS Script 19 chapter values refreshed and its "appear directly in §4.13.2" corrected.
- **Script 34 figures updated everywhere** — and the reason the anchor "no longer reproduced the headline" turned out to be that the headline itself was stale: Script 20's two-window change is now −105.1 mm (n = 59; network mean −467 → −572 mm), against Script 34's −104.7 mm (n = 60). The whole §4.12 MSL5-change block was pre-D-189: report9 §4.12 text and Figure 71 caption, report10 §5.7.x (three passages), report8 §3.8, the abstract (report.odm) and the MS/SM Script 34 notes. Per-well values (CEH22 −233, CEH21 −213, CEH18 −145, C5 coastal −164 to −172, WMC3 −90, CEH36 −97, C4 −138), 58 of 59 wells beyond ±25 mm, the spring SD/SE by cluster (SE 82–181 mm), the partial correlations (+0.60; +0.10, p = 0.42; Spearman +0.38), lag-1 (−0.14 to +0.01; +0.17, p = 0.17; site-mean −0.03 over 20 years), the EWI/MSL5 precision ratio (3.3–6.2). **One reading changed:** report10 said CEH36's −74 mm against −97 mm "is consistent with a small residual of the benefit persisting"; it is now −97 against −105, inside the ±25 mm display threshold, and the sentence says no residual is resolved.
- **SM Table S8.1 edited (it was wrong):** the spring four-zone model now gives Impact −97 ± 22 mm (p < 0.001), Edge −32 ± 35 (p = 0.36), C3/Warren +30 ± 23 (p = 0.19), R² 0.53. The text now says the Edge and C3/Warren steps are not significant, and that the Impact step rests on one well (14 well-years, cluster-robust SEs on very few clusters) and is not reproduced by the per-well comparison against the same control (WMC3 −2 mm, p = 0.97, Script 10d) — reported, not read as a felling effect. The 10d tier means (−2 / −107 / −9 / −63 mm) and S8.2's CEH36 spring shifts (+95, p = 0.022; +19, p = 0.79) refreshed; the old robustness sentence (drop-2011) removed, no longer applicable. **Martin: the Impact spring step is new and large; worth a look.**
- **MS Script 29 table regenerated as a generated table:** Script 29 1.10.0 writes `29_headline_models.csv` (isolated run: every existing Script 29 output byte-identical); `table_configs` 1.13.0 `ms/Script29Headline`; the MS column that said "R² (best single)" was the adjusted R² and is now labelled so; metric τ → the recession time t_R = 1/β₃ (what the script computes); interpretation text brought into line (dist_CEH36 strongest for the four SSM metrics and the slope, the coast strongest for seasonal amplitude); "on AIC the linear-capped form is marginally better" → the exponential.
- **§F.4 unsourced numbers, traced (`scratch/proof/unsourced_trace_24l.md`):** fixed from committed outputs — MS Script 26 coverage (1,430 / 1,274 (89 %) / 869 / 85 series incl. the lake gauge), CEH14 NSE −3.21 → −6.42 (08_perwell_nse), the MSL5↔annual-minimum figures left from the SM5 era (0.945/829/0.95/≈0.54 m ×5 → 0.943/648/0.94/≈0.69 m; "roughly at SD16" → "below SD16"), coastal "δ₀ ≈ 0.13 m, L ≈ 1.5 km" → δ₀ 31.4 mm yr⁻¹, L 894 m, h₀ ≈ 81 mm (20_report_numbers coastal_h0), report8 BACI tier distances (Forest control 306–752 m, Climate control 215–1010 m — fell-centroid distances; NW10 had been left out), report10's unsaved own-panel OLS variant (−8.0, p 0.42; lives only in a PNG legend) removed. Reproducible as typed: Feb-2026 PET 66.8 mm (a documented historical bug, D-036), CEH42 3.4 years, zero crossing ≈ 1,440 m ("near 1400"). **Still without a source:** report8 §3.2.3 "CEH3 suppresses the Lake–Dune separation at k = 4" (no run with CEH3/CEH22 was ever committed); MS Script 23 "≈ 2.5 % of annual flux" (a docstring estimate); MS Script 41 "r = +0.089 (n = 33) … −0.513" (typed into a warning string in the script — a hard-coded value); MS Script 29 "regression coefficient +1.046" (not in any output).

### Specs still awaiting sign-off
- **S1 — Script 16:** residual field and its spatial statistics (unchanged from §E).
- **S3 — Script 01:** annual-rainfall OLS trend for BOTH windows (1931–2025 and 2006–2025): slope, t, p, n.
- **S6 — Script 34:** write the envelope (range, pairs, sign split, anchor, extremes) to `34_report_numbers.csv`, as Script 35 now does, so the report's Script 34 numbers can be bound.
- **S7 — Script 41 and Script 23:** compute and emit the numbers now typed into their source (41's canopy correlations; 23's flux share) or drop the claims.

### Not yet swept
The academic summaries (EN and CY) carry the same pre-D-189 MSL5 figures (−97 mm, −588/−685, 56 of 59, 71–134 mm) and others — that is T-83, next.
