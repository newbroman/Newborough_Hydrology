# Brief — rebuild the forestry and scraping scenarios on the observed BACI step (D-333)

*Queued 2026-11-12 by chat 'Cloud setup J-14' on Martin's word ("Separate task", answering how the D-333 scenario
rebuild should fit with J-9 phase 2b). Task **T-209**. Claim `pipeline`. Read D-333 and D-332 in full first.*

## Why

D-333: neither model form detects the December 2017 felling in its coefficients. The scenarios built from β
multipliers of single-well era refits (Script 10e → `clearfell_common.load_clearfell_impact_b2_multiplier` → Scripts
19 and 21; the 09b/09d scrape bars) are sign changes of quantities inside their noise, amplified by 1/β₃: C4 clearfell
+0.35 m under Model A, −0.92 m under Model B. Those values are withdrawn pending this rebuild. The independent review
behind D-333 (scratch scripts s1–s5, J-9 session) is summarised in D-333's Decision and Rationale.

## What to do

1. **Anchor the clearfell scenario to the detection result:** the control-differenced BACI step of Scripts 10a/10k
   (+0.108 m against the Forest controls, HAC CI about −0.02 to +0.24 m; +0.066 m combined; −0.019 m against Climate),
   stated as winter-loaded (Oct–Mar gain, none Jun–Sep). Propose to Martin, before coding, how it is applied: a level
   response at the felled-well scale, or a recharge-season flux gain where β₃ is identified. Never convert through
   1/β₃ in C4 (Model B β₃ not identified there): C4 propagation is "not quantified", or bounded by the observed step.
2. **Thinning and broadleaf:** state how each relates to the anchored clearfell (fraction of it, or not quantified);
   the interception-return and open-dune end-state runs remain the upper bounds (D-239).
3. **Scraping (09b, 09d):** the same rule — the paired contrast at CEH36 (Script 09a) is the detection; the Δβ₃
   propagation bars are withdrawn unless a datum-free test supports them.
4. **Attribution outputs:** add the paired differential test (WMC3 minus control mean, seasonal steps Oct–Mar and
   Jun–Sep, PET- and P-scaling, with the placebo distribution over control wells) as a committed output with report
   numbers, so D-333's figures are read from a CSV, not a scratch run.
5. Retire `load_clearfell_impact_b2_multiplier` from the scenario path (keep 10e's era shifts as named sensitivities
   with their t-values).

## Acceptance

The scenario outputs carry the anchored values with their interval; no scenario reads a β multiplier from 10e; the
paired-test output exists with report numbers; full run and `bash tools/check_all.sh` OK (or red only on the
expected citation drift, listed for the documents). Ask before every push.

## Also in scope (found while flagging, 2026-11-12)

- The multiplier also surfaces in `utils/pipeline_params.py` (`clearfell_b2_mult` / `thinning_b2_mult` written to
  `pipeline_scenario_params.csv`), `utils/scraping_common.compute_scenario_bars`, and 09d's `CLEARFELL_MATCH_HINT`
  caption constant — retire or re-anchor each.
- Figures to redraw legibly when rebuilt: the Script 21 hydrograph (legend over the observed C1/C2 lines) and 09b_04
  (text boxes over the C4/C5 scrape bars).
- The flagged values carry `config.D333_WITHDRAWN_NOTE` and a `status` = `D333_WITHDRAWN_STATUS` column; the rebuild
  removes the flags with the values it replaces.

## The water-balance residual check (2026-11-12, Martin: "run the scratch check now")

Script 55's residual D = P_eff − PET − S_a·Δh, with each well's law slope fixed from the before era, BACI against the
controls with HAC errors and a placebo distribution (review scripts, private: `working/updates/NRG_d333_review_scripts_2026-11-12/`
`c55.py`, `s6.py`–`s9.py`; the earlier D-333 review is `s1.py`–`s5.py`).

- **Clearfell (WMC3; it is in cluster 3, so Script 55 gives it gross rain in both eras):** not detected against the
  placebo spread (−1.7 ± 2.1 mm/month against the Forest controls; opposite sign against the Climate controls). A full
  return of the 24 % interception would lower the residual by ≈ 18 mm/month (P-slope −0.24); the observed P-slope
  (−0.01 ± 0.04) excludes it by about six standard errors. **Upper bound for the rebuild:** at most a small fraction of
  the nominal interception gain reached the water table — roughly a tenth, up to about two-fifths depending on the
  drainage rate assumed (consistent with D-239). Season and driver not resolved. The scenario must not assume the full
  24 %.
- **Scrape (CEH36 vs CEH4, also CEH18; series already in the post-scrape LiDAR frame, truncated 2023-09 before the
  unrecorded re-scrape):** detected (no placebo comparable): level +0.14 m relative to control, monthly fluctuations
  damped by about a quarter (Δh-on-Δh slope 0.92 → 0.74), no added summer loss (it loses less at equal head). The
  damping means S_a changed (plausibly the pond 16 m away); with S_a fixed the seasonal split is set by the S_a assumed,
  so storage, drainage-law and summer-loss changes cannot be separated from heads.
- **Structural limit:** the matched-head residual step is algebraically −c × the paired level step — a restatement of the
  level BACI in water units, not an independent detection. Script 55 is a diagnostic (D-303).
- **Suggested attribution sentences** (for the rebuild and phase 3):
  *Clearfell.* The water-balance residual at the felled well shows no change after felling beyond the spread among
  untreated wells (−1.7 ± 2.1 mm/month against the forest controls). A return of the full 24 % interception to the
  water table would have lowered it by about 18 mm/month and is excluded; at most a small fraction reached the water
  table. Its season and driver are not resolved.
  *Scrape.* After the 2015 scrape the water table at CEH36 stood 0.14 m higher relative to its control and its monthly
  fluctuations were damped by about a quarter; the residual shows no added summer loss. Whether the change is in storage,
  in the drainage law or in summer loss cannot be separated from heads.
- **What would settle it:** throughfall at the felled compartment; a stage record of the scrape pond or a logger pair at
  CEH36.
