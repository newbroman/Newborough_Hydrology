# report6 — the historical paragraph, redrafted from Script 44 (for Martin's wording)

**Provenance.** Cowork session `01PhSvhMMGSWW9UnSFdTK5GU` · configured `claude-fable-5-1` ·
2026-09-08. Numbers read from the committed L14 run: `outputs/44_ranwell_hindcast/44_05_level_change.csv`
(rows COMBINED_ALL, COMBINED_CONSTRAINED), `44_04_hindcast_metrics.csv` (headline rows),
`44_report_numbers.csv` (`ranwell_interval_years`, `ranwell_forcing_ratio_1951_53`). The report is
the live document (D-144), so this is a plain `odt_edit` on `report_edits/odt/report6.odt` once you
settle the wording; the mirror regenerates. D-145 records the reasoning.

## Current (report6, §1, third paragraph, first sentence)

> A well-documented trend of water table decline has been observed at the site over the past six
> decades (Ranwell, 1959; Jennings, 1990). Conservation management has included a December 2017
> experimental clearfell of 8.4 ha within the plantation, and topographical dune scraping at
> selected slack sites. …

The sentence is wrong on its own citation: Ranwell (1959) records a seasonal range and a 1951–53
baseline and makes no decline claim; Jennings (1990) could not be located. No source found in the
literature sweep measures a long-term decline at the site (`NRG_newborough_decline_claims_inventory_2026-09-08.md`).

## Proposed replacement (two sentences in, one out; the rest of the paragraph unchanged)

> A decline of the water table since afforestation has long been asserted for the site, but it
> has not previously been measured: the one early record, Ranwell's fortnightly readings at
> seventeen levelled pipes in 1951–53 (Ranwell, 1959), established a seasonal range of
> 70–100 cm and a baseline, not a trend, and later accounts of a drier phase in the 1970s–90s are
> anecdotal and coincide with a run of dry winters. Setting Ranwell's readings against the modern
> network (Section 5.7.8) shows the open slacks he measured standing, on average, within about a
> decimetre of their 1951–53 level today once the climate of the two periods is allowed for
> (−0.09 ± 0.10 m over eight sites and sixty-six years; no site differs at two standard errors),
> and the same coefficients that describe the modern aquifer reproduce his 1951–53 seasonal cycle
> (r 0.74–0.91). The record therefore supports fluctuation about a near-stationary level rather
> than progressive decline, with the 1989–96 depression and its recovery (Section 5.7.8) as the
> one documented excursion. Conservation management has included a December 2017 experimental
> clearfell of 8.4 ha within the plantation, and topographical dune scraping at selected slack
> sites. …

## Notes for the wording

- **Where the numbers live:** `44_05` COMBINED_ALL `delta_m` −0.093, `sigma_total_m` 0.103,
  `n_contributing` 8; `ranwell_interval_years` 66.2; `44_04` headline `r` 0.744 / 0.747 / 0.914.
  "About a decimetre" and "−0.09 ± 0.10 m" are renderings of those cells; `cite_check` will index
  them once the mirror is refreshed. If you prefer the constrained-sites figure (six sites,
  −0.07 ± 0.11) say so — I used all eight because the CSV's inverse-variance weighting already
  discounts the two unconstrained coastal-slack sites and the two combinations agree.
- **Section reference:** I have pointed at §5.7.8, where Script 39's CCW hindcast is discussed,
  on the assumption that the Script 44 result is written up there beside it (the two are the same
  kind of test, 38 years apart). That subsection does not yet carry the Script 44 text — a
  second edit, in report10, once you say where it goes. If you'd rather it had its own
  subsection, the reference changes.
- **What the paragraph does not claim:** nothing about the forest (no Ranwell site is under the
  canopy; the modelled drawdown at the Clwt Gwlyb sites is inside the comparison's error), nothing
  about the BS slack (no printed series), and nothing about a rate — "near-stationary" is the
  bound, and the 2σ interval (roughly −0.3 to +0.1 m over the interval) is what "near" means.
- **Citations:** Ranwell (1959) is already in the bibliography. The "later accounts" clause is
  written without a citation; if you want one, Davy et al. (2010) is the source that calls the
  1970s dry phase anecdotal and rainfall-driven, and it would need a bibliography entry. Jennings
  (1990) is dropped from the sentence because it could not be read; it can stay in the
  bibliography if cited elsewhere.
- **Introduction versus results:** this is the §1 framing; the full result (Q1 hindcast figure
  `44_07`, the per-site figure `44_08`, the error model, Site 8) belongs in the §5.7.8 write-up,
  which I'll draft next if you approve the direction.
