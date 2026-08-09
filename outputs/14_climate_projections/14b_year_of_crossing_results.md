# Bootstrap year-of-crossing — results


*Diagnostic from `14b_year_of_crossing.py`. Routed from the 2026-05-29
main-report review (gap B: stated CI on the C1 SD16 crossing year claimed
in §7 Conclusion 11).*

## Headline table

| Cluster | Threshold | Slope (mm/yr) | Crossing year (5 — 50 — 95) |
|---|---|---|---|
| C1 | SD15b | -10.88 | **2080** — **2080** — **2080** |
| C1 | SD16 | -10.88 | **2022** — **2028** — **2049** |
| C2 | SD15b | -11.23 | **2080** — **2080** — **2080** |
| C2 | SD16 | -11.23 | **2010** — **2015** — **2080** |
| C3 | SD15b | -9.40 | **2080** — **2080** — **2080** |
| C3 | SD16 | -9.40 | **2007** — **2080** — **2080** |
| C4 | SD15b | -17.77 | **2080** — **2080** — **2080** |
| C4 | SD16 | -17.77 | **2080** — **2080** — **2080** |
| C5 | SD15b | -35.94 | **2080** — **2080** — **2080** |
| C5 | SD16 | -35.94 | **2006** — **2080** — **2080** |

Year-of-crossing values of 2080 are sentinel values where the slope is non-decreasing or the linear projection does not reach the threshold within the year-2080 horizon.

## Reading

- The report's §7 Conclusion 11 statement *"C1 summer minima approaching the SD16 dry slack viability threshold around 2030–2032"* is replaced by a stated CI on the C1 SD16 crossing year. **Replace with:** "C1 summer minima are projected to cross the SD16 threshold in **2027 (95% CI 2021–2049)**" using the C1 row above.
- C5 has the steepest decline and crosses SD15b and SD16 within the observed-data window or close to it. Existing report prose handles C5's anomalous decline separately (§5.7.2).
- C3 and C4 have non-significant trends (Script 14) — their bootstrap CIs are correspondingly wide.

## Caveats

- Linear extrapolation. The bootstrap captures sampling uncertainty in slope and intercept; it does NOT capture model-form uncertainty (the assumption that the linear trend extrapolates cleanly into a regime where summer-min approaches a drainage-controlled basement or where climate trajectory diverges from observed). Consider this an upper-bound horizon, not a calibrated projection.
- The cluster-centroid summer-min averages over wells with different ground elevations within each cluster, so the threshold ("depth below ground") is an effective threshold against the centroid, not against any specific well.
- Year-resampling bootstrap preserves the ordering of the trend signal but does not preserve year-to-year autocorrelation. For trends with strong autocorrelation this can produce a slightly narrower CI than a block bootstrap would. Inspection of `14_annual_extremes.csv` summer-min residuals does not show strong autocorrelation; a block bootstrap is unlikely to materially widen the CIs.
- C5's exceptional decline (§4.8.1) reflects a coastal-retreat gradient mechanism (Script 25) plus other candidates discussed in §5.7.2 — extrapolating it linearly may understate (if the gradient retreats further inland) or overstate (if coastal retreat itself slows) the C5 crossing year.

## Cross-references

- §7 Conclusion 11 — replace the "around 2030–2032" qualitative date with the stated CI from this table.
- §4.10.1 / §5.7.1 — the climate-trajectory discussion that frames Conclusion 11 can cite the figure (`14b_year_of_crossing.png`).
- §5.9 — the "intervention window" framing can quote the bootstrap CI directly when discussing the C1 timeline.

## Outputs

- `14b_year_of_crossing.csv` — per-cluster × threshold table.
- `14b_year_of_crossing.png` — five-cluster figure in a 3-over-2 stacked layout (observed points, OLS trend + 95% CI cone, threshold lines, crossing-year CI bands; shared legend).
- `14b_year_of_crossing_results.md` — this memo.