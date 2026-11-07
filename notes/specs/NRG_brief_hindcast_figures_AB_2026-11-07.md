# Brief — the hindcast figures must show BOTH models, and scenario 1 has no figure at all

**Raised:** 2026-11-07 by Martin, reading the explanatory document written for Laurence
(`claude.ai/artifact/EnB1ysSshKBb1NA8TzPi9x`). **Claim:** `pipeline` (Scripts 39, 44, 50).
**Why it matters:** *"the argument seems mainly about why not just have one model"* — and every hindcast
figure in the corpus shows **one** model. The document argues that a fast return and a lasting shift
are different quantities needing different forms, then illustrates it with evidence from a single
form. That is the central claim of Paper M, unillustrated.

## What exists today

| scenario | figure | what it shows |
|---|---|---|
| 1 — modern split at Jan 2018 | **none** | `50_07_split_by_datum.csv`, 10,032 rows of NSE by datum and direction. No series, no plot. |
| 2 — the drier past, 1989–96 | `39_04_hindcast.png` | nine CCW wells, observed vs **one** free run, β₁ envelope |
| 3 — Ranwell 1951–53 | `44_07b_hindcast_report.png` | three sites, observed vs **one** free run, offset removed |
| neighbour transfer | **none** | §4.5's numbers are table-only |

`39_02_hindcast_series.csv` (723 rows) and `44_03_hindcast_series.csv` carry monthly
observed/predicted pairs, so scenarios 2 and 3 already have the series — they are plotted for one
form only. Scenario 1 has no series emitted at all.

## What is wanted

1. **Scenario 1 gets a figure, and the document leads with it.** It is the case *inside* the
   recorded climate — the one Model B is supposed to win — and currently the only one a reader
   cannot see. Needs a new emit from Script 50: the monthly free-run series for the Jan-2018 split,
   forward and backward, per well, for both forms.
2. **Every hindcast figure shows Model A and Model B together.** Same axes, same wells, observed in
   black. The point the reader must see unaided: B tracks the wiggles better, A sits at the right
   *level* against the dry decade. Today that contrast exists only as numbers in a table.
3. **The neighbour-transfer test gets a figure** (and the test itself is approved — see the
   companion task): fit on one well, free-run on a neighbour, scored per month on r² and bias.
   Report the open dune separately; the forest is the known exception.

## Two things to get right

- **The β₁ band is NOT a confidence interval**, and a reader will assume it is. It is a plausibility
  envelope over `CCW_BETA1_SCALINGS = (1.00, 1.03, 1.06, 1.10)` — the fitted value and up to 10 %
  higher — because the hindcast applies coefficients fitted 2005–2026 to 1989–96 while
  `src/utils/config.py:3052` records that the site-wide β₁ decline makes the 1989 value plausibly
  higher. Script 39's own header is blunt: it does **not** establish coefficient stationarity, "which
  it assumes and which the corpus contradicts". Any figure carrying that band must label it as an
  envelope, and say which direction the error runs: with the fitted value alone the hindcast
  under-predicts recharge and places the table too deep.
- **Where the β₁ decline is a problem elsewhere**: Script 37 gives its regression a free uniform
  intercept `c` specifically to absorb it, "so background drying cannot be laundered into
  `s_coast`" — described there as the key identification move. So the decline is real enough to
  change how another analysis is identified.
- **I could not find the decline QUANTIFIED anywhere** in `outputs/*/report_numbers.csv` or the
  report text. The 10 % ceiling of the envelope therefore rests on a magnitude that is not written
  down where a reader can check it. Either cite it or derive it in this job.

## Done when

- A figure per scenario showing both forms, and the document updated to lead with scenario 1.
- The β₁ band labelled as an envelope wherever it is drawn, with its direction stated.
- The quantified site-wide β₁ decline cited, or the envelope's ceiling justified from an output.
