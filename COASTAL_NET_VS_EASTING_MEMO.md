# Memo — Coastal-process figures vs the BACI easting × time term

*Written 2026-05-28. Companion to Script 20 Figures 4–6 and Script 25.*

## Purpose

Figures 4–6 (Script 20) visualise the western-margin coastal processes:
erosion drawdown (Fig 4), sea-level-rise head gain (Fig 5), and their net
(Fig 6). This memo records how those figures relate to the BACI
`easting × time` correction (Script 10a) and the Script 25 coastal-gradient
corroboration — and, importantly, the limits of that comparison.

## The numbers

From the live pipeline at time of writing:

| Quantity | Value | Source |
|---|---|---|
| BACI `easting × time` absorbs (Forest–Impact) | **−16.8 ± 5.0 mm/yr** | Script 25 `25_04_baci_corroboration.csv` (from 10a coef 3.4e-05) |
| Erosion gradient model predicts | **−11.0 mm/yr** | Script 25, forest-free linear-capped δ₀/L |
| Residual (observed − erosion) | **−5.8 mm/yr** | unexplained by erosion alone |
| SLR head-gain rate near coast | **+4.0 mm/yr** | Script 20 Fig 5 (SLR_RISE_M/window) |
| Erosion + SLR net prediction near coast | **−7.0 mm/yr** | erosion − SLR gain |
| Gap to observed (−16.8) | **−9.8 mm/yr** | *widened* by including SLR |

## The finding (state carefully)

The BACI `easting × time` term absorbs MORE downward drift (−16.8 mm/yr)
than the coastal-erosion gradient alone predicts (−11.0 mm/yr). Adding the
sea-level-rise head gain does **not** close this gap — because SLR raises
the coastal water table, including it makes the net coastal prediction
*less* negative (−7.0 mm/yr), so the discrepancy with the observed
absorption *widens* to ~−9.8 mm/yr.

**Interpretation (for §5, hedged):** erosion and SLR are real, opposing,
similar-magnitude processes at the western margin, but together they account
for only part of the easting-correlated decline the BACI removes. A residual
network-wide deepening gradient remains unattributed — consistent with the
existing note that the easting × time covariate absorbs a coastal signal it
cannot fully decompose. The net map (Fig 6) shows this is spatially
concentrated in a narrow dune-toe band over the confounded C5 / western-C3
wells. None of this undermines the observed C5 decline (which is in the
measured record); it explains why a single linear easting term is a
first-order proxy rather than a clean attribution.

## CAVEATS — these must travel with any use of Figures 4–6

1. **Single shore only.** All three figures reference the eroding Caernarfon
   Bay (SW) shore. The Menai Strait / Malltraeth estuary margins are not
   represented. SLR acts on those margins too; omitting them under-states the
   site-wide SLR head response and means the figures speak only to the
   western dune system.

2. **Episodic vs gradual.** Erosion is modelled as ONE ~6 m retreat event
   (Storm Brendan exemplar); SLR is gradual accrual over the window. The two
   are deliberately NOT reduced to a common annual rate. A real 5-yr window
   could contain zero, one, or several storm pulses — the erosion-dominated
   (red) band in Fig 6 would deepen/widen in a storm-rich window and shrink
   in a quiet one. The net map is illustrative of relative spatial reach, not
   a deterministic 5-yr forecast.

3. **Start points / datums differ (by design).** SLR is referenced to mean
   sea level (0 m AOD); erosion to the dune toe (0.5 m AOD waterline + 100 m
   inland). Physically appropriate but means the two zero-distance lines
   differ by ~100 m. The southern dune face is steep, so the dune-toe front
   sits visibly inland of the bright dune face on the hillshade — this is
   correct (consistent 100 m offset), not a geometry error.

4. **Assumption-stacked parameters.** δ₀, L (live, Script 25), retreat rate
   (8.3 m/yr storm-inclusive — likely over-states the chronic rate; the ~50 m
   2014–2020 figure was Brendan-dominated), diffusivity (K=6, b=5 literature;
   Sy=0.311 live C3 WTF), window (5 yr) and SLR amount (0.02 m) are all
   flagged constants. Every headline number scales with them. The comparison
   above is therefore order-of-magnitude corroboration, not a fitted result.

5. **Not a water budget.** Fig 6 is a difference of two single-mechanism
   illustrative fields, not a closed mass balance. It cannot adjudicate the
   C5 attribution; the SSM scenario values (independent of the coastal
   confound) remain the mechanistically valid quantity.

## Where this lives

- Figures 4–6: Script 20, `outputs/20_spatial_figures/`.
- Quantitative corroboration (erosion gradient vs easting term):
  Script 25, `25_04_baci_corroboration.csv` — already in the pipeline.
- The SLR extension of that comparison (this memo) is NOT yet a pipeline
  output; if it is to be reported, it should be added to Script 25 as a
  documented extension, not hardcoded into the report text.
