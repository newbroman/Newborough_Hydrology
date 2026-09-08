# Spec — Script 44: Ranwell's 1951–53 water-table record against the modern network and the SSM hindcast (W95 → new item; D-140 lineage)

**Provenance.** Cowork session `01PhSvhMMGSWW9UnSFdTK5GU` · configured `claude-fable-5-1` ·
2026-09-08. Martin: "compare the 1951 to 53 water levels with our levels today … test the SSM
… whether the water table is declining or what the rate of movement of the water table is over
the last century … enable any analysis that allows that to take place". Design → sign-off →
build. The prototype numbers in §4 are from the bridge (numpy recurrence, identical to
`simulate_ssm`) against the committed `03_master_data`, `01_climate`, `01_wells_clean`,
`01_locations` — they are for deciding the design, not for quoting.

## 1. What Ranwell (1959) actually contains, read this session

No table of readings. Seventeen pipes (1 m galvanised, driven to about 95 cm), levelled to OD in
1951 (re-surveyed 1953 at mobile-dune sites, agreement within a few cm); readings at least
fortnightly February 1951 – August 1953 except June–September 1952. What is printed:

- **Fig. 4** — the time series, depth below surface, for **Site 1** (1951–53), **Site 4**
  (1951–53) and **Site 8** (1951 only), with daily rainfall at Parc Mawr.
- **Fig. 7** — monthly ranges (one open bar per month, all years pooled) for **Sites 1, 4,
  11, 12, 13, 16, 18**: the wet-slack / dry-slack habitat definitions rest on it.
- **Fig. 2** — monthly rainfall at Parc Mawr 1950–53 (annual 1037 / 987 / 707 / 690 mm): a check
  on the RAF Valley forcing over exactly the hindcast years.
- Fig. 3 heights (already used, Script 43); Fig. 5 diurnal; Fig. 6 water-table profile at a
  dune foot; text: annual range 70–100 cm everywhere, 1950–51 flooding, no tidal signal at
  Site 10, a subterranean divide near Clwt Gwlyb with drainage south to the sea and north to
  Penlon (Llyn Rhos-Ddu).

**Digitised this session (Fig. 4 → `data/ranwell_1951_53_water_levels.csv`, 146 readings):**
300 dpi render; hollow markers found as enclosed white components, crosses by template match,
fifteen occluded markers added by hand from gridded zooms; axes calibrated on the tick marks
(≈3.9 px/cm, ≈117.5 px/month); every panel re-plotted and checked against the original
(`ranwell_fig4_digitised_check.png`). Accuracy about ±1 cm and ±2 days. Columns: `site_no,
date, depth_below_surface_cm, level_m_od` (= Fig. 3 height − depth), `source, px_x, px_y`.
Fig. 7 (84 monthly ranges, 7 sites) and Fig. 2 (48 months of Parc Mawr rainfall) were digitised the same session — `data/ranwell_1951_53_monthly_ranges.csv`, `data/ranwell_1950_53_parc_mawr_rain.csv`; method, accuracy and the Fig. 4/Fig. 7 cross-check (±4 cm in 20 of 24 months) in `data/RANWELL_PROVENANCE.md`. These are
factual data recovered from a published figure; the figure itself stays uncommitted (D-081).

## 2. The three questions, and what each can honestly answer

**Q1 — Does the SSM hindcast 1951–53?** The dynamics test. Drive each modern well's fitted
Model A coefficients with RAF Valley climate from 1930 (Script 39's recurrence, `simulate_ssm`,
the June-1941 gap dropped as 39 does) and compare the modelled series at the well nearest each
Ranwell site *in the same DEM basin* (Script 43 Route T) with Ranwell's readings **after
removing the mean offset** — because the two are not at the same point and a metre of ground
separates them. Metrics: r, NSE-after-offset, observed vs modelled seasonal range, timing of the
spring fall and autumn recovery. This is Script 39's out-of-sample test taken 38 years further
back, to the start of the climate record's useful span, with the stationarity caveat 39 already
carries (β₁ then was plausibly higher). It does not depend on the site positions beyond "same
slack".

**Q2 — Has the water table in the slacks moved since 1951–53?** The absolute test. Ranwell's
mean level in m OD at a site (his levelling agrees with the modern DEM to +0.06 m, Script 43
Route H) against the **modern mean water-table surface interpolated to that point** — IDW of
per-well modern mean levels (k = 6, r ≤ 400 m, p = 2, wells with ≥ 60 readings), at Martin's
position and at the height-refined one — minus the **climate-only expectation** for the same
two spans from Q1's hindcast. What is left is the change climate does not explain.

**Error model, per site, four terms in quadrature (added 2026-09-08 after the LOO test):**
(i) *interpolation* — leave-one-out RMSE of the IDW over the six contributing wells
(`RANWELL_IDW_K`), each predicted from the others; (ii) *position* — the modern surface's
gradient at the site (central difference, `RANWELL_GRAD_STEP_M` = 20) times the positional
uncertainty from Script 43 Route H (`RANWELL_POS_SIGMA_M` = 40 for a flat-floor site, the
refinement move for a flank site); (iii) *sampling* — the difference between the Fig. 4
reading-mean and the Fig. 7 mid-range mean where both exist (0.05 m at Sites 1 and 4;
`RANWELL_SAMPLING_SIGMA_M` = 0.05 applied everywhere); (iv) *datum* — Route H's global offset
(0.06 m). Sites combine by inverse-variance weighting; the χ²/dof is reported so excess scatter
is visible; `resolved` = |Δ| > 2σ. Site 8 (coastal, 1951 only, 118 m from one well) is
reported but excluded from the combined figure, with the reason in the CSV.

**Q3 — The rate over the last century.** Not a regression through two points. The script emits,
per site, Δ = (modern − 1951–53) − (climate-only expectation), its spread, and Δ/Δt in mm yr⁻¹
with Δt from the record midpoints (≈ 63 years, 1952 → 2015); the write-up sets it beside the
CCW 1989–96 epoch contrast (Script 39, a recovery) and the modern record's own trend, so the
century is read as three epochs, not one line. Whether a rate is *resolved* is a statement the
spread decides, and the script says which sites resolve one.

## 3. Script 44 `44_ranwell_hindcast.py` — outputs (`outputs/44_ranwell_hindcast/`)

- `44_01_ranwell_readings.csv` — the Fig. 4 readings joined to site, basin, paired well.
- `44_02_ranwell_monthly_ranges.csv` — the Fig. 7 ranges joined to site, basin and the
  monthly mid-range level used for the site mean.
- `44_03_hindcast_series.csv` — per Ranwell site: month, observed monthly mean (m OD), modelled
  mid-month level at the paired well (m OD), modelled at each same-basin well; 1951-01 to 1953-12.
- `44_04_hindcast_metrics.csv` — per site × paired well: n, offset, r, NSE_after_offset, range
  obs/model, spring-fall timing difference (months), plus Script 39's β₁-scaling envelope.
- `44_05_level_change.csv` — per site: Ranwell mean and n, modern IDW mean at Martin and refined
  positions, contributing wells (names, distances, levels), the four error terms and their
  quadrature sum, climate-only expectation, Δ, z, Δt, rate mm yr⁻¹, `resolved`, `in_combined`;
  plus one `COMBINED` row (inverse-variance mean, se, χ²/dof, n sites).
- `44_06_climate_check.csv` — Parc Mawr monthly rainfall 1950–53 (Fig. 2, digitised) against RAF
  Valley `P_m` for the same months: ratio and r. If they disagree materially the hindcast forcing
  is the first suspect and the CSV says so.
- `44_07_hindcast.png` — three panels (Sites 1, 4, 8): Ranwell's readings and the modelled
  series at the paired well, offset applied, 1951–53.
- `44_08_level_change.png` — per site, Ranwell mean vs modern IDW mean with the contributing
  wells as points, the climate-only expectation as a bar.
- `44_report_numbers.csv` — `ranwell_hindcast_r_median`, `ranwell_hindcast_nse_median`,
  `ranwell_sites_compared`, per-site `ranwell_delta_m_site{N}` and `_spread_m`,
  `ranwell_rate_mm_yr_site{N}`, `ranwell_forcing_ratio_1951_53`.

**Constants (config.py):** `RANWELL_HINDCAST_SPAN` = ("1951-02", "1953-08"); `RANWELL_IDW_K` = 6,
`RANWELL_IDW_RADIUS_M` = 400, `RANWELL_IDW_POWER` = 2, `RANWELL_MIN_MODERN_N` = 60;
`RANWELL_PAIR_MAX_M` = 300 (a paired well must be in the same basin and within this);
`RANWELL_GRAD_STEP_M` = 20, `RANWELL_POS_SIGMA_M` = 40, `RANWELL_SAMPLING_SIGMA_M` = 0.05.
**Inputs (paths.py):** `RANWELL_LEVELS` (data/ranwell_1951_53_water_levels.csv),
`RANWELL_RANGES` (data/ranwell_1951_53_monthly_ranges.csv), `RANWELL_PARC_MAWR_RAIN`
(data/ranwell_1950_53_parc_mawr_rain.csv); `OUT_43_SITES` (Script 43 v2, basins and positions);
`INT_MASTER_DATA`, `INT_CLIMATE`, `INT_WELLS_CLEAN`, `INT_LOCATIONS`.
**Registration:** tier A, `exec default`, after 43 (it reads 43_01); raw-input exception
recorded (as D-051 did for 39); SKIPS cleanly if the Ranwell CSVs are absent. `record_basis`
row RB-44: wells = same-basin paired wells; fitted = Model A per well (RB-04); evaluated over
1951-02 to 1953-08 against Ranwell's readings. `ms_chapters` will refuse the registration until
the MS chapter exists → §S.23c written in the same batch (MS frozen, `REASON=`).
**Shared code:** the recurrence via `model_utils.simulate_ssm`; the IDW via `map_utils` only if
its function returns point values (it renders surfaces — if not, a 15-line `idw_at_points` goes
into `map_utils`, not the script); basin ids from Script 43's output, never recomputed.

## 4. Prototype, bridge, 2026-09-08 (design evidence, not quotable)

**Hindcast (Q1), Fig. 4 sites, paired well in the same basin:**

| Site (slack) | Ranwell readings | Paired well | r | NSE after offset | Seasonal range obs vs model |
|---|---|---|---|---|---|
| 1 (PL) | 39, 1951–53 | ceh23 | 0.86 | 0.72 | 0.90 vs 0.72 m |
| 4 (CG) | 50, 1951–53 | nw2 | 0.84 | 0.62 | 0.80 vs 0.89 m |
| 8 (AS) | 28, 1951 | nw5 | 0.91 | 0.80 | 0.60 vs 0.57 m |

Forcing check (Fig. 2 vs RAF Valley, 36 months 1951–53): ratio 0.95, r 0.91 — the RAF Valley
record is a fair proxy for Newborough rainfall in the hindcast years.

**Absolute change (Q2), all eight printed sites; Ranwell mean from Fig. 4 where it exists,
else the mean of Fig. 7 monthly mid-ranges (the two agree to 0.05 m at Sites 1 and 4):**

| Site | Slack | Ranwell mean m OD | Modern IDW at Martin / refined position | Contributing wells (range; n; distances) | Δ modern − 1951–53 |
|---|---|---|---|---|---|
| 1 | PL | 8.61 | 8.69 / 8.63 | 7.76–9.58; 6; 93–304 m | +0.08 |
| 16 | PL | 9.38 | 9.58 / 9.58 | 8.65–10.54; 6; 1–335 m | +0.20 |
| 4 | CG | 11.28 | 10.96 / 10.94 | 10.54–11.36; 6; 133–262 m | −0.32 |
| 11 | CG | 10.65 | 10.19 / 10.18 | 9.58–10.54; 6; 133–301 m | −0.46 |
| 12 | CG | 10.70 | 10.90 / 11.07 | 10.00–11.36; 6; 51–211 m | +0.20 |
| 13 | CG | 10.72 | 10.76 / 10.76 | 10.00–11.36; 6; 12–191 m | +0.03 |
| 18 | AS | 6.83 | 6.90 / 6.89 | 5.11–7.32; 5; 145–333 m | +0.07 |
| 8 | AS | 6.39 (1951 only) | 5.11 / 5.08 | 2.67–7.32; 6; 118–348 m | −1.28 |

Climate-only expectation for 1951–53 against the modern span (Q1 hindcast at the paired wells):
−0.03 to +0.03 m — climate does not separate the two epochs.

**With the four-term error (LOO run on the bridge, 2026-09-08):** network LOO RMSE of the IDW
is 0.58 m overall but 0.11–0.31 m at the seven inland Ranwell sites, which sit in the
best-instrumented part of the network (Site 18: 0.71, five wells). Per site, Δ ± σ: Site 1
+0.08 ± 0.35; 16 +0.20 ± 0.19; 4 −0.32 ± 0.19; 11 −0.46 ± 0.19; 12 +0.20 ± 0.27; 13 +0.03 ± 0.24;
18 +0.07 ± 0.74. **Inverse-variance mean over the seven inland sites: −0.10 ± 0.09 m
(χ²/dof 1.6)** — a fall of about a decimetre, not resolved at 2σ; the 2σ bound on a fall is
about 0.27 m and on a rise about 0.08 m. Sites 4 and 11 (CG, 130 m from their nearest wells)
are the two individually low sites, at 1.7σ and 2.4σ; Sites 12 and 13, also CG and 12–51 m
from wells, are not.

Reading: **Q1 is a result** — coefficients fitted 2005–26 reproduce the shape and amplitude of
1951–53 at r 0.84–0.91, fifty-four years before calibration. **Q2:** away from the coast the
slack water table today is within about a decimetre of where Ranwell found it, the combined
estimate being a fall of 0.10 ± 0.09 m; a regional fall larger than about 0.3 m is excluded.
The forest drawdown the report models at the CG sites' distances from the canopy (60–80 mm,
`DRAWDOWN_H0_MM` and λ) sits inside that interval, so the comparison is consistent with it and
cannot confirm it; no Ranwell site is under the canopy. Site 8, at the seaward, accreting end
of the AS slack, is 1.3 m lower against a single well 118 m away on a retreated coast (D-060)
— a coastal-geometry change or a mis-pairing, reported separately. **Q3:** the century
statement the data support is *no resolved change in slack water-table level between 1951–53
and 2005–26 away from the coast (−0.10 ± 0.09 m), with any monotonic trend over the interval
smaller in magnitude than about 4 mm yr⁻¹*; set beside the CCW 1989–96 depression-and-recovery
(Script 39) the century reads as fluctuation about a near-stationary level, not the decline the
secondary literature asserts. That is the sentence that replaces report6's "well-documented
trend of water table decline (Ranwell, 1959)". **BS has no Ranwell series at all** — Fig. 4 and
Fig. 7 cover PL, CG and AS only — so nothing can be said for it.

**The literature the report should answer** (delegated search, 2026-09-08,
`NRG_newborough_decline_claims_inventory_2026-09-08.md`; Martin's own publications excluded):
no source found asserts a *measured* long-term decline at Newborough. Ranwell (1959) is cited
only for seasonal range; the 1970s–90s "drier phase" is called anecdotal by Davy et al. (2010)
and attributed there to rainfall, with the afforestation attribution appearing uncited
(Wikipedia) or as a generic management-plan statement (NRW SAC plan); the only quantified
"decline" (1–3 m by 2080) is a climate projection for dune systems generally; NRW's 2025 Forest
Resource Plan says its 2016 hydrological trial is still running. Jennings (1990) — the likely
origin of the afforestation strand — could not be located. Script 44's result is the first
measured answer to that literature, and report6's historical paragraph should say so in those
terms: what was claimed, on what evidence, and what the 1951–53 comparison finds.

## 5. Records and documents

- Decision entry **D-145**: Ranwell's 1951–53 readings recovered from Fig. 4/7 and used for an
  out-of-sample SSM test and a basin-level absolute comparison; what it does not establish (a
  point-to-point comparison; a single rate for the century). Retires the 08-22 "per-site
  absolute-level comparison abandoned" for the *basin-level* form only. Revisit-if: Ranwell's
  field books or a metric survey of the pipes surface.
- `DECISION_LOG` D-140: add the lineage bullet. W95 closes with Script 43 v2; **new register row
  W140** for this script.
- MS §S.23c (new chapter, `ms_chapters_extra.csv` row 44); `data/RANWELL_PROVENANCE.md` (the
  digitisation record above, with the check figure); SCRIPT_LEDGER row 44; `record_basis` RB-44;
  `figure_table_sources` when the report cites it.
- Report: a subsection in the historical-context chapter (Martin's call where) carrying Q1 as a
  validation result and Q2/Q3 as bounded statements; report6's "well-documented trend of decline
  (Ranwell 1959)" sentence rewritten from what 44_05 says.
- Paper 1 is frozen; if Q1 belongs there it goes through `REASON=` as a one-sentence addition to
  the out-of-sample paragraph, later.

## 6. Order of work

1. Sign-off on this spec (the pairing rule, the IDW constants, tier A/default, D-145).
2. ~~Digitise Fig. 7 and Fig. 2~~ — done 2026-09-08, committed to `data/`.
3. Script 43 v2 build (spec of 2026-09-08b) — 44 reads its basins.
4. Script 44 build; L14 run; read-back against the §4 prototype (offsets and r must reproduce
   to 2 d.p. at the three Fig. 4 sites).
5. §S.23b/§S.23c, D-140/D-145, registers, provenance, changelog; then the report subsection with
   Martin.

## 7. For Martin

- Pairing rule: nearest same-basin well within 300 m, or all same-basin wells within 300 m
  reported and the nearest used for the headline? I propose the second (the CSV carries all).
- Tier A default (moves the registered count and needs the MS chapter) or opt-in X? It answers a
  scientific question the report will cite, so A.
- Is there any chance Ranwell's field data survive (Nature Conservancy / NRW archive at Bangor)?
  A single table would replace the digitisation and add fourteen sites.
