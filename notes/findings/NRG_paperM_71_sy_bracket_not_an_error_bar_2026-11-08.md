# Paper M §7.1 presents the water balance's Sy span as an error bar, and it is not one (2026-11-08)

Chat "Paper M editing", holding no claim; `doc:PaperM` was free when this was written. Nothing in any
document was changed. Every number below is recomputed from committed outputs
(`outputs/55_water_balance_drainage/`), not from a document.

## 1. The defect

Paper M v1_44 §7.1 reads:

> The water balance gives the annual share at the median well, but needs a specific yield, **which is
> why it carries a bracket of 36 to 55 %.**

and, three sentences earlier, puts the share at **31 %** at the median well. A central estimate cannot
lie outside its own uncertainty interval, and this one lies five points below it. The sentence reads
the span as an error bar on the 31 %, which is exactly what it is not.

All three numbers are correctly bound fields and the CSV agrees with them, so this is a prose defect
and not a stale value, a mis-registration or a pipeline fault:

| field | key | value | rendered |
|---|---|---|---|
| `wb_drain_share_median_x100_dp0` | `wb_drain_share_median` | 0.3052 | 31 % |
| `wb_drain_share_median_sy_hi_x100_dp0` | `wb_drain_share_median_sy_hi` | 0.3565 | 36 % |
| `wb_drain_share_median_sy_lo_x100_dp0` | `wb_drain_share_median_sy_lo` | 0.5460 | 55 % |

## 2. Script 55 is right, and says so explicitly

The span is not a confidence interval and was never meant as one. The 31 % uses Script 18's
fluctuation-method Sy, fixed before the fit; the two endpoints recompute the share at the Stage I
winter joint fit's two regression directions. Those bounds mostly lie BELOW the fluctuation-method Sy
(D-306), and a smaller Sy books less storage and so a larger drainage share — so the span sits above
the published value rather than around it.

`plot_share`'s docstring (`src/55_water_balance_drainage.py:954`) states the whole of it, including the
one exception, and the figure draws a span rather than an error bar for that reason. Version 1.1.0's
banner says the same: the bracket "sits ABOVE the published value because both bounds lie below the
fluctuation-method Sy". **The pipeline documented this correctly on the day it was written.**

## 3. Recomputed from the committed per-well CSV

Medians over each cluster's reference wells, `55_05_winter_law_et.csv`
(`drainage_share`, `drainage_share_sy_lo`, `drainage_share_sy_hi`):

| cluster | published | span low | span high | position |
|---|---|---|---|---|
| C1 Lake Edge | 0.472 | 0.209 | 0.608 | **straddles** |
| C2 Dune | 0.353 | 0.389 | 0.582 | wholly above |
| C3 Western Residual | 0.301 | 0.398 | 0.557 | wholly above |
| C4 Main Forest | 0.156 | 0.179 | 0.353 | wholly above |
| C5 Coastal Forest | 0.236 | 0.298 | 0.389 | wholly above |
| network median | 0.3052 | 0.3565 | 0.5460 | **wholly above** |

## 4. A second, smaller defect in §5.3

> The bracket's upper end sits at the fluctuation-method value at every cluster, which is what an
> estimate drawing on the capillary fringe should do.

**"At every cluster" is wrong: C1 is an exception**, and Paper M's own Figure 5 caption says so —
"it lies wholly above the bar at C2--C5 and straddles it only at C1". At C1 the span runs 0.209-0.608
across a published 0.472, so there the Sy bracket's upper end lies ABOVE the fluctuation-method value,
not at it. The direction of the claim fails at that one cluster.

"Sits at" is also an idealisation at C2-C5. If the Sy bracket's upper end were AT the fluctuation-method
Sy, the span's lower end would equal the published share; at C2 it is 0.389 against 0.353, at C3 0.398
against 0.301. The bracket lies below the fluctuation Sy there, not at it. Whether that wants rewording
is a judgement about how much precision the sentence is claiming; the C1 exception is not a judgement.

## 5. What is and is not wrong

Right, and needing no change: Script 55 and all its outputs; the three bound fields; **Figure 5's
caption**, which states the non-centring and names C1 as the exception; and **§5.3's own account of the
span** — "across that bracket the water-balance drainage share runs from 36 to 55 %" is a statement
about a range of estimates, not an error bar, and is correct.

Wrong: §7.1's "which is why it carries a bracket of 36 to 55 %", and §5.3's "at every cluster".

**§7.1's defect is the one that matters**, because §7.1 is where the paper compares the four readings
and a reader meeting 31 % beside a "bracket of 36 to 55 %" has been told the estimate is inside a
range it is outside. The paper already has the right words for it a few lines away, in §5.3 and in
Figure 5's caption.

## 6. Who decides

An uncertainty attached to a published number is a published claim, so the wording is Martin's
(CLAUDE.md §7). No gate catches it: `field_sync` checks a field's value against its CSV and not the
sentence around it, which is the §5 mispointing hazard in a new place — three correct values and a
wrong relation asserted between them. T-184 carries the check.

Decisions recorded: none.
