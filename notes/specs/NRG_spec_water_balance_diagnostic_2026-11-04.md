# Spec: water-balance drainage diagnostic (fixed Sy, residual drainage law)

**Status:** DESIGN. Signed off 23:20 except D1 (name), which is open. No code, document text or citation until signed off. Revised 21:34 (Stages H and I, decisions D9–D11).
**Written:** 2026-11-04, claude.ai chat session (Claude Opus 5.5), against public `main` as cloned at 18:30.
**Provenance of the numbers below:** scratch scripts in that chat, run against committed CSVs on public
`main`. They are INDICATIVE ONLY: they show what the step is expected to find, and serve as a regression
check for the build. None may be quoted in any document until the step is on `main` and its
`report_numbers` CSV exists.

---

## 1. What it is, and why

Martin's question (2026-11-04): take a basic water balance, rainfall less PET, attribute the
storage change to the water table through a fixed specific yield, treat what is left as drainage,
and regress that residual on head to get a drainage rate.

    D(t) = P_eff(t) − PET(t) − Sy · Δh(t)                  (m water / month)
    P_eff = P · (1 − FOREST_INTERCEPTION) in C4/C5, gross P elsewhere
            (INTERCEPTION_TREATMENT.md case (c): reduce P, leave PET gross)
    Sy    = per-well Sy_median, 18_wtf_01_well_sy_estimates.csv (fixed, not fitted)

    Linear law:     D = a + c · h_prev
    Threshold law:  D = a + c · max(h_prev − h₀, 0)
    k = c / Sy  (fraction of the head above h₀ drained per month)

**Why it earns a step.** Paper M §7.1 says heads alone cannot split the loss between ET and
drainage (Model A 68 %, Model B 45 % at the median well). As of v1_42 (`380a497`) it leaves the two
forms' answers apart and constrains the split by §2.4's floor and §5.2's recession reading, the
latter presented as a third estimate independent of both forms. Fixing Sy from outside the fit, and
trusting PET only in winter when it is small, gives a fourth reading. It is also the only one of the
four on the SAME BASIS as the 68 % / 45 % §7.1 quotes, a drainage share of the annual loss at the
median well (indicative per-well median: 0.295, interception counted as loss, 66 wells), where §5.2's
recession share is a share of summer recession. That makes it the first independent reading directly
comparable with the two forms. It also answers two of the
three caveats §5.2 gives for the recession reading (months chosen on the fall; head inflating the
winter rate) through Stages H and I. It came out at about a third of the loss
on the open dune, below both forms, and it accounts for the gap: the SSM's free coefficients book only
β₂/β₁ ≈ 0.4–0.5 of PET as ET, against water-balance ET/PET ≈ 0.86–0.94.

**What it is NOT.** Not a forecaster. Within the record it forecasts like Model A and below Model B.
In the drier decade (1989–96) it fails in the same direction as Model B, too wet, because its fitted
constant ties the level to the modern mean. It is a diagnostic.

**Name: a decision for Martin (§8, D1).** The project already has a "TLM": Script 08's traditional
linear model, Δh = α + β₁P − β₂PET, with free coefficients and no drainage term. This step is not that
model. Proposed name in documents: **"the fixed-storage water balance"**, with code identifier `wb_`.
Calling it "TLM" anywhere would collide with Script 08 and Paper 1 §3.5.

## 2. Indicative findings (scratch, not citable)

| Test | C1 Lake Edge | C2 Dune | C3 Western Res. | C4 Main Forest | C5 Coastal Forest |
|---|---|---|---|---|---|
| Apparent Sy, slope of P−PET on cluster-mean Δh | 0.179 | 0.224 | 0.249 | 0.252 | 0.296 |
| Threshold k above h₀ (/month), per-well median | 0.540 | 0.328 | 0.199 | 0.047 | 0.156 |
| h₀ (m below ground), per-well median | 0.603 | 0.635 | 0.878 | 1.321 | 1.259 |
| Wells where the threshold beats the line (ΔBIC < −2) | 5 / 7 | 14 / 19 | 9 / 26 | 1 / 9 | 0 / 5 |
| Winter-law ET/PET, summer | 0.733 | 0.860 | 0.853 | 0.727 | 0.621 |
| Winter-law ET/PET, year | 0.794 | 0.902 | 0.941 | 0.835 | 0.736 |
| Drainage share of loss (interception counted as loss) | 0.427 | 0.336 | 0.311 | 0.145 | 0.229 |
| SSM β₂/β₁, full record, per-well median (03_15) | 0.184 | 0.409 | 0.476 | 0.934 | 0.510 |
| Interception at which total loss = PET | n/a | n/a | n/a | 0.142 | 0.204 |
| Split-sample NSE fwd (water balance / A / B) | 0.749 / 0.645 / 0.854 | 0.614 / 0.579 / 0.787 | 0.726 / 0.698 / 0.771 | −0.054 / 0.138 / 0.136 | 0.565 / 0.749 / 0.815 |

Network: split-sample median NSE forward 0.659 (A 0.635, B 0.776), reverse 0.589 (A 0.614, B 0.711),
45 wells. CCW 1989–96 hindcast, 8 wells: bias +0.383 m (line), +0.237 m (threshold), Model A
(Script 39, same wells) +0.125 m.

Other results, recorded for the write-up:
- Removing CEH11 from C1 changes nothing (summer ET/PET 0.733 either way; CEH11 alone 0.732), so
  C1's shortfall is shared by all its wells, not a lake-proximity effect.
- Fitting C1's winter law only on below-ground months (52 % of its winter months) leaves ET/PET at
  0.718: ponding does not explain the shortfall. Reading adopted in discussion: C1 wells sit in
  receiving positions on shallow till and take in groundwater, which a single-column balance books
  as missing ET (Martin, 21:04: the clay layer is shallow under C1/C2 and is what separates C2 from C3).
- The shared C1/C2 threshold (~0.6 m) against C3's (~0.9 m) is supporting evidence for the
  shallow-till eastern block (Paper 1 §5.1–5.2; drumlin memo 2026-09-19).
- Under the forest, drainage shows no head dependence at any interception fraction from 0 to 0.40
  (k −0.036 to 0.016 at C4), so its drainage law is a constant: assumed, not tested.
- Sy sensitivity: k barely moves between Sy = 0.20 and the Script 18/17 values (it enters both the
  residual and k = c/Sy, and the two largely cancel); R² rises with the WTF values.

**Added 21:34 (Martin's two refinements, 21:26 and 21:30).**

*Dry months (Stage H).* Drainage is best measured when the table is falling and little rain falls;
rising months mostly add noise. Per-well fit of the residual law on selected months:

| Months used | k C1 / C2 / C3 | R² C1 / C2 / C3 |
|---|---|---|
| All months | 0.468 / 0.249 / 0.160 | 0.545 / 0.385 / 0.245 |
| Falling, rain in the well's lowest quarter | 0.546 / 0.338 / 0.266 | 0.780 / 0.538 / 0.480 |
| Rain in the lowest quarter, any direction | 0.556 / 0.330 / 0.257 | 0.778 / 0.574 / 0.461 |
| Rain in the lowest quarter, Nov–Mar only | 0.357 / 0.189 / 0.148 | 0.543 / 0.321 / 0.333 |

- Select on RAINFALL, never on the fall: Δh sits inside the residual, so choosing months because the
  level fell selects on the outcome. Rainfall-only selection gives the same answer without that bias.
- About half the dry months are summer (mean PET ≈ 64 mm/month). If a deep table evaporates below
  PET, over-subtracting PET at low heads steepens the slope, so the dry-summer k is read as an UPPER
  bound that mixes in ET falling with depth (the effect Script 15's depth-dependent model targets).
- Dry winter months (PET ≈ 25 mm/month) are the cleanest, with 13–17 months per well, and return k
  close to the all-month and winter-law values. Forest: no head dependence on any selection (C4 k ≤
  0.095).

*Winter joint fit of Sy and drainage (Stage I).* With ET ≈ 0 in winter, Sy·Δh = P_eff − D(h): two
unknowns, so winter months estimate Sy and the drainage law together, without borrowing the WTF Sy.
Months at or above ground (start or end) are excluded (ponded storage ≈ 1, not Sy). Both P (off-site
gauge) and Δh carry error, so both regression directions are fitted as a bracket: Δh on P (rain error
biases Sy high) and P on Δh (level error biases Sy low).

| Cluster | WTF Sy | Winter Sy low / high | Winter k (high-bound fit) | R² |
|---|---|---|---|---|
| C1 Lake Edge | 0.211 | 0.138 / 0.299 | 0.430 | 0.808 |
| C2 Dune | 0.268 | 0.157 / 0.253 | 0.152 | 0.757 |
| C3 Western Residual | 0.298 | 0.189 / 0.262 | 0.110 | 0.795 |
| C4 Main Forest | 0.253 | 0.148 / 0.247 | −0.015 | 0.629 |
| C5 Coastal Forest | 0.308 | 0.184 / 0.270 | 0.054 | 0.744 |

- The WTF Sy sits at the top of the winter bracket, consistent with Paper 1's caution that WTF Sy are
  upper bounds (capillary-fringe release). The bracket midpoint (geometric mean, per-well median) is
  0.198 / 0.199 / 0.219 / 0.187 / 0.223.
- The low-bound direction ranks wells as WTF does (Spearman 0.745, 66 wells); the high-bound
  direction does not (0.066). Partly expected: both are rise-against-rain methods.
- Using winter PET as ET instead of zero barely moves either bound, so ET ≈ 0 is not driving it.
- Three routes now agree on the open-dune winter drainage rate: winter law (0.376 / 0.276 / 0.150),
  dry winter months (0.357 / 0.189 / 0.148), winter joint fit (0.430 / 0.152 / 0.110).
- The forest shows no head-dependent winter drainage even with Sy fitted freely, so that is not an
  artefact of the borrowed Sy.
- Knock-on for the write-up: if true Sy is below the WTF value, λ = √(Kb/(Sy·β₃)) lengthens roughly
  as 1/√Sy. Not acted on; flagged for the λ sensitivity text (report8 §3.7.4).

## 3. Placement

- **Script 55**, `src/55_water_balance_drainage.py`; outputs in `outputs/55_water_balance_drainage/`.
  (Highest current script number on `main` is 54; confirm none is reserved before taking 55.)
- **Tier X, exec `optin`.** It is a diagnostic; adding it moves only the registered total, not the
  analytical count. Read counts from the manifest after the change; never type them.
- **Two-pass dependency.** It reads Script 18 (Sy), Script 48 (A/B split-sample scores) and Script 39
  (the CCW series), so it registers after all three and goes in the `run_analysis.py` two-pass note.
  Each loader reads the live CSV and, if absent, SKIPS that stage with a `warn`. It does not fall back
  to a default: there is no defensible default Sy per well.
- Uses `build_ssm_frame()` for every alignment. Does NOT use `fit_ssm()`: there is no SSM fit here, so
  `record_basis_lint` needs a row that declares no `fit_ssm` call (as RB-05 does for a no-fit step).
  Confirm the lint accepts that, or extend the lint in the same pass.
- Free-running uses a local recurrence, h ← h + (P_eff − PET − D(h))/Sy, because `simulate_ssm` has
  no fixed-Sy, threshold form. Put it in `model_utils` as `simulate_water_balance()` so a later script
  cannot reimplement it. Agree that with Martin; it touches a shared module.

## 4. New config constants (`config.py`, valued there, named here)

- `WB_WINTER_MONTHS` = (11, 12, 1, 2) — the months the winter law is fitted on
- `WB_SUMMER_MONTHS` = (5, 6, 7, 8, 9) — the summer ET/PET ratio
- `WB_HINGE_GRID_PCT` = (5, 95), `WB_HINGE_GRID_N` = 91 — h₀ search range and density
- `WB_BIC_MARGIN` = 2 — the threshold must beat the line by more than this
- `WB_MIN_MONTHS` = 36, `WB_MIN_WINTER_MONTHS` = 20 — admission
- `WB_MIN_WELLS_PER_MONTH` = 2 — cluster-mean months
- `WB_INTERCEPTION_SCAN` = (0.0, 0.40, 0.02) — the interception scan
- `WB_DRY_RAIN_QUANTILE` = 0.25 — a dry month is one whose rainfall is in the lowest quarter of the
  site climate record over the reference period (Stage H); selection on rainfall only
- `WB_RISE_MARGIN_M` — the rise counted as real in a dry month (above reading error)
- `WB_DRY_WINTER_MONTHS` = (11, 12, 1, 2, 3) — the dry-winter subset of Stage H. Not
  `WB_WINTER_MONTHS`: March is included to give the subset enough months; agree or tighten (D9)
- Stage I reuses `WINTER_RECESSION_MONTHS` (Nov–Feb, already in config and used by Script 16)
  rather than `WB_WINTER_MONTHS`, if Martin agrees the two are the same definition (D10)
Reuses `FOREST_INTERCEPTION`, `MODEL_AB_SPLIT_DATE`, `MODEL_AB_MIN_TEST_MONTHS`. No value typed in
the script, its comments or its docstring.

## 5. Stages and outputs

| Stage | What it does | Output |
|---|---|---|
| A | Cluster-mean month: P−PET (P_eff in forest) on mean Δh; slope = apparent Sy, intercept = drainage at steady level | `55_01_surplus_vs_dh.csv`, `55_01_surplus_vs_dh.png` |
| B | Per well: residual D on h_prev, line and threshold, per-well Sy; cluster summaries | `55_02_drainage_law_per_well.csv`, `55_03_drainage_law_by_cluster.csv`, `55_02_drainage_law.png` |
| C | Annual water balance from the fitted law: P, interception, PET, drainage, storage change | `55_04_water_balance.csv` |
| D | Winter law (Nov–Feb) predicted from head in every month; ET backed out; months outside the winter head range excluded and counted; per-well drainage share of annual loss and its network median (the §7.1 basis), rerun at the Stage I low and high Sy so the share carries the Sy bracket | `55_05_winter_law_et.csv`, `55_06_et_monthly.csv`, `55_05_et_vs_pet.png` |
| E | Sensitivities: C1 without CEH11; below-ground-only winter fit; Sy = Script 17 cluster median | `55_07_sensitivity.csv` |
| F | Forest interception scan, total loss / PET at each fraction; the closing fraction by interpolation | `55_08_interception_scan.csv` |
| G | Split-sample free run (Script 48's rule) and CCW 1989–96 hindcast (Script 39's series and censoring) | `55_09_split_sample.csv`, `55_10_ccw_hindcast.csv` |
| H | Dry-month drainage law: per well, months with rain in the lowest `WB_DRY_RAIN_QUANTILE`, all seasons and `WB_DRY_WINTER_MONTHS` separately; also all, rising and falling months for comparison; season shares and mean PET of each subset | `55_11_dry_month_law_per_well.csv`, `55_12_dry_month_law_by_cluster.csv` |
| I | Winter joint fit of Sy and drainage: Nov–Feb, below-ground months, ET = 0 and ET = PET; both regression directions; Spearman of each against WTF Sy; bracket midpoint | `55_13_winter_sy_per_well.csv`, `55_14_winter_sy_by_cluster.csv`, `55_13_winter_sy_bracket.png` |
| — | Report numbers | `55_report_numbers.csv` |

Figures follow `MPL_DEFAULTS`; captions are supplied in document text, not in the figure.

**Report-number keys (proposed):** `wb_k_hinge_C{1..5}`, `wb_h0_m_C{1..5}`, `wb_hinge_wells_C{1..5}`,
`wb_et_pet_summer_C{1..5}`, `wb_et_pet_year_C{1..5}`, `wb_drain_share_C{1..5}`,
`wb_interception_close_C4`, `wb_interception_close_C5`, `wb_nse_fwd_median`, `wb_nse_rev_median`,
`wb_ccw_bias_line_m`, `wb_ccw_bias_hinge_m`, `wb_c1_no_ceh11_et_pet_summer`,
`wb_c1_below_ground_et_pet_summer`, `wb_drain_share_median` (per-well median, the §7.1 basis), `wb_drain_share_median_sy_lo`, `wb_drain_share_median_sy_hi`, `wb_k_dry_all_C{1..5}`, `wb_k_dry_winter_C{1..5}`,
`wb_R2_dry_all_C{1..5}`, `wb_dry_summer_share`, `wb_sy_winter_lo_C{1..5}`, `wb_sy_winter_hi_C{1..5}`,
`wb_sy_winter_mid_C{1..5}`, `wb_k_winter_joint_C{1..5}`, `wb_sy_winter_spearman_lo`,
`wb_sy_winter_spearman_hi`, plus the basis counts (`wb_n_wells`, `wb_n_split_wells`,
`wb_n_ccw_wells`).

## 6. `record_basis.csv` rows (proposed)

- RB-55a: residual drainage law, 66 reference wells (those with a Script 18 Sy), full record, no
  `fit_ssm` call; evaluated in-sample.
- RB-55b: winter-law ET, same wells, fitted on `WB_WINTER_MONTHS`, evaluated on months inside the
  winter head range.
- RB-55c: split-sample, Script 48's wells and rule (fitted one side of `MODEL_AB_SPLIT_DATE`).
- RB-55d: CCW hindcast, Script 39's confirmed wells, pipe-base readings excluded.
- RB-55e: dry-month drainage law, same wells as RB-55a, fitted on the dry-month subsets only.
- RB-55f: winter joint fit, wells with at least `WB_MIN_WINTER_MONTHS` below-ground winter months,
  Nov–Feb; no external Sy.

## 7. Verification before it counts as built

1. Run against the committed CSVs and READ BACK every report-number key from the written file.
2. The scratch results in §2 must be reproduced to 3 d.p. where the method is unchanged. Any
   difference is explained in the changelog, not smoothed over.
3. One known difference to settle: the scratch hindcast started its run after the single missing
   climate month (June 1941). Match whatever Script 39 does there, and state it.
4. `check_all.sh` verdict quoted in the changelog. `ledger_lint`, `record_basis_lint`, and the
   manifest guard all green.

## 8. Decisions for Martin (sign-off)

- **D1 Name. OPEN (Martin, 23:20).** Storage is not fixed; Sy is. It is the traditional linear model
  with its rainfall and PET coefficients set to 1/Sy, and the residual is what is analysed. Options:
  "water-balance residual analysis" (recommended; methods text states the TLM link in one sentence),
  "Sy-constrained TLM", "residual drainage analysis". Never bare "TLM" (Script 08). Code prefix `wb_`.
- **D2 Placement. SIGNED OFF.** Script 55, tier X, opt-in.
- **D3 Sy source. SIGNED OFF.** Script 18 per-well `Sy_median` (the value the rest of the pipeline uses;
  forest wells already interception-corrected), Script 17 as a sensitivity only.
- **D4 Interception. SIGNED OFF.** `FOREST_INTERCEPTION` stays at 0.24. The documents report the closure scan: C5
  consistent with 0.20–0.24 (the cluster containing the measurement site), C4 pointing lower but
  unresolved because its drainage law is a constant. The sparse canopy is a reason to expect a value
  below the conifer literature. (Agreed in discussion 21:02–21:04; needs a D-entry.)
- **D5 Winter months. SIGNED OFF.** Nov–Feb.
- **D6 Threshold rule. SIGNED OFF.** Threshold only where ΔBIC < −2; otherwise the line. Equal weight per well in
  cluster summaries.
- **D7 Shared code. SIGNED OFF.** `simulate_water_balance()` added to `model_utils`.
- **D8 Split-sample leakage. SIGNED OFF: windowed Script 18 (Martin, 23:20).** A forecasting test is
  run as a forecasting model, so Stage G uses Sy estimated on the fit side only. Script 18 gains a
  windowed mode that leaves every existing output unchanged and writes per-well Sy before and after
  `MODEL_AB_SPLIT_DATE` to a new file (proposed `18_wtf_06_well_sy_by_window.csv`); Stage G reads the
  pre-split Sy for the forward test and the post-split Sy for the reverse. Script 18 version bump,
  inline changelog, SCRIPT_LEDGER row and a `record_basis` row; no new pipeline step. A well with too
  few recharge events in a window is skipped in that direction and counted.
- **D9 Dry months. SIGNED OFF, amended (Martin, 23:20).** A dry month is one whose rainfall is in the
  lowest quarter of the SITE climate record over the reference period (one gauge, so one set of dry
  months for every well), chosen on rainfall only; dry-winter subset Nov–Mar. Dry-winter k is the
  cleaner estimate, all-season dry k an upper bound. Stage H also counts dry months in which the level
  ROSE by more than a reading-error margin, per well and by cluster, split winter half and summer, with
  the previous month's rainfall for rising and falling dry months. Martin's reading: a rise in a dry
  month means water arrived from elsewhere. Scratch result: rises are rare (cluster medians 0.017 to
  0.069), fall in the winter half, none in summer, and follow a wetter previous month (75.8 vs about
  64 mm; C4 118.4 vs 62.6), so they look like the previous month's rain still draining down, not
  lateral inflow. C1 has the fewest, so the test neither shows nor rules out C1 inflow, which would
  appear as a slower summer fall rather than a rise. New constant `WB_RISE_MARGIN_M` (scratch used
  0.02 m); `WB_DRY_RAIN_QUANTILE` now applies to the site record.
- **D10 Winter months (Stage I). SIGNED OFF.** Reuse `WINTER_RECESSION_MONTHS`, so Script 16 and this step share
  one definition; exclude months at or above ground.
- **D11 Sy bracket. SIGNED OFF.** Report the winter joint-fit Sy as a two-direction bracket beside the WTF Sy,
  not as a replacement. `FOREST_INTERCEPTION`, the Script 18 Sy and λ are unchanged; the λ
  sensitivity text notes that a lower Sy lengthens the reach.

**Decision-log entries to write in the build session** (take IDs immediately after pulling `main`; the
Paper M chat is also adding entries): (i) the fixed-storage water balance adopted as a diagnostic,
not a forecaster, with its Revisit-if; (ii) D4, the interception write-up; (iii) the C1
receiving-position reading, with CEH11 and the below-ground test as its evidence; (iv) the
winter joint fit as an independent Sy bracket (D11), with its Revisit-if (a direct Sy measurement,
or a rain gauge on site, which would remove the rain-error side of the bracket; Martin's IANGLESE3
station is a candidate).

## 9. Document plan (after the step is on `main`; each edit walked through first)

**Paper M** (via the chat holding `doc:PaperM`): a short new **§5.3** "Fixing storage: a fourth
reading of the split", placed straight after §5.2's recession reading which it complements, one
figure (Stage B or D), detail in the SI. Inserting it renumbers current §5.3–§5.6 to §5.4–§5.7 and
moves six typed internal references (two to §5.4, one to §5.5, three to §5.6). The Paper M chat runs
that renumber, by the CLAUDE.md §4d recipe (plan pass, figure_map.py, repoint_verify, reference_lint
--snapshot, ref_audit), because reference_lint alone cannot see a reference that moved twice. The
drafted passages therefore call the new section §5.3 and name any later section by its title as
well as its post-renumber number; one added clause in §7.1 beside §2.4's floor and §5.2's reading (v1_42 wording
stands);
the §7.1 clause frames the four readings by what each is free of (Paper M chat, 23:14):
§2.4's floor needs no datum, no fitted base and no Sy, gives bounds only and fails under canopy;
§5.2's recession ratio needs no datum and no Sy but is a share of summer recession; Models A and B
give the annual-loss share but each needs a datum or a fitted base, and they disagree; the water
balance gives the annual-loss share at the median well but needs Sy, hence its bracket. The floor and
the water balance then bear on §7.1's quantity from opposite directions, and §5.2's independence of
Sy stays its own virtue. Field keys go to the Paper M chat first so it can register them; the
insertion and the renumber go in as one version bump; a sentence each in §7.4 (the forest forcing reading) and §8. The plain companion
(PaperM_plain) follows in its next pass.

**Paper 1:** §4.4/§4.5 cite the third bracket beside the 85 %/24 % split and soften Table 3's C1
mid-point; §4.5 and Conclusion 3 state that the water-balance closure and the Sy convergence point
opposite ways at C5, and qualify "inconsistent with a mis-set fraction"; §4.5 records the forest
total-loss disagreement (Table 3 ≈ PET; water balance at 0.24 above it); §5.1–5.2 add the shared
C1/C2 threshold; §5.4 the C1 receiving-position reading. λ and Figure 19 untouched while D4 holds.

**Report:** report8 "Mean Monthly Water Balance Decomposition" and "Specific Yield Estimation: Water
Table Fluctuation Method" (method); report9 "Recharge and Losses: A Cluster-Level Water Balance",
"Specific Yield Estimation", "Drainage Decay Half-Life", "Water Balance Residual Field"; report10
"Recharge Partitioning and Atmospheric Draw", "Linking Groundwater Behaviour to Geology and Land
Cover"; report12 Conclusions (one line). Methods Supplement §S.11/§S.12 and
`INTERCEPTION_TREATMENT.md` (the closure test).

**Route.** The build runs in a session with BOTH repositories attached (SESSION_MODES.md), holding the
`pipeline` claim. Drafted passages go to `claude/NRG_draft_water_balance_passages_<date>.md` in the
project store, each citing its key; the chat holding each document family applies them.

## 10. Scratch scripts (reference only; the build is written fresh to project conventions)

`tlm_drainage.py`, `tlm_scatter.py`, `tlm_drainage_vs_level.py`, `sy_sens.py`, `tlm_threshold.py`,
`tlm_winter_test.py`, `tlm_followups.py`, `tlm_below_ground.py`, `tlm_split_sample.py`,
`tlm_ccw_hindcast.py`, `tlm_recession.py` (Stage H), `tlm_winter_sy.py` (Stage I), delivered in the
2026-11-04 chat.
