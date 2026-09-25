# What D-195/D-196 moved — the first full run after the monthly-calendar correction

**Provenance:** Claude Opus 5.5, session `session_01A3XmyBJYxysNudx48fRJSa`, Cowork bridge. Compared: `git HEAD` against Martin's full run of 2026-09-25 (`scratch/full_D195.log`, check_all `scratch/check_all_D195.log`).
**Row-level diff:** `notes/findings/NRG_D195_report_numbers_diff_2026-09-25.csv`. It covers every `*_report_numbers.csv` row as old, new and relative change, with SIGN / SIG05 / SIG001 flags.
- The 09c rows are key-collision artefacts: duplicate keys paired in both orders. They are not changes.

## Scale

- 2,042 report-number rows; 1,328 changed.
- 998 changed by more than 1 %, 535 by more than 5 %, 238 by more than 20 %.
- check_all failed on four gates:
  - `defaults_lint`: 18 stale fallbacks. **Refreshed**; pipeline_params 1.13.0.
  - `table_gen`: 47 generated tables drift.
  - `cite_check`: 334 confirmed citations drifted, plus 937 unreviewed rows.
  - `inequality_lint`: the synthetic clearfell p is now 0.0014, so "p < 0.001" is false in report12 and the abstract.

## Results whose reading changes (Martin's call before any text is written)

1. **Partition (D-196, accepted):** five boundary wells moved from C2 to C3. The partition is now C2 19 and C3 26. C3's median bootstrap stability fell from 0.49 to 0.38.
2. **Model benchmarking (Script 08, report Table 5, §4.4):**
   - The traditional model's failure was largely an artefact of the alignment defect. Every well's 100-month window contained the Nov 2022 → Jan 2023 two-month pair, fitted as one January month. With an intercept, the TLM integrates that bias over 100 iterative months.
   - The SSM is still better, by half as much as before:

   | | Before | After |
   |---|---|---|
   | TLM median iterative NSE | −0.025 | +0.421 |
   | SSM median iterative NSE | 0.719 | 0.767 |
   | Median ΔNSE | 0.824 | 0.372 |
   | Wells with TLM NSE > 0 | 30 / 66 | 55 / 66 |
   | CEH6 (TLM, SSM) | −1.885, 0.674 | −0.348, 0.708 |

   - The largest improvement is now D7 (6.91), not CEH27.
   - The correlations of ΔNSE with β₂ and β₃ weaken: r −0.62 → −0.37 and +0.60 → +0.42, still p < 0.01.
3. **Clearfell BACI (10a / 10h / 10l):**
   - The monthly Forest headline moves from +113.1 to **+108.2 mm**.
   - The **summer (Jun–Sep) step goes from +50 mm to −1 mm**: sign flipped, no longer significant, and N 52 → 50. The two summer months removed were the first-month fills inside summer gaps, the exact case Defect E set limit=1 to exclude. The summer step without the CWB term goes from +123 to +91 mm.
   - The synthetic-control clearfell p goes from 0.0009 to 0.0014.
   - The four-zone spring contrasts involving C3/Warren change sign; they are small either way.
4. **Scraping:** the WMC3 BACI drawdown goes from −55.2 to −45.8 mm, and the CEH36 scrape response from 0.129 to 0.128 m.
5. **Clusters versus covariates (Script 07):** β₁ goes from not significant (p 0.20) to significant (p 0.016, ΔAIC −6.4). This follows from the partition change.
6. **Coefficient shifts at felling (10e):** NW5, NW6 and NW7 Δβ₁ change sign. These are the wells that had the most bridged cells removed.
7. **Coastal / forest drawdown:** δ₀ −31.35 → −31.28, L 894 → 902 m, λ 226 → 221 m, CEH6 drawdown 8.27 → 7.74 mm; small.

## Before the sweep

The first pass of this run read the STALE fallbacks for its two-pass steps (the run log warns about exactly this). With the defaults now refreshed, **a second full run** gives the final numbers. The document sweep should be made against that run, not this one.
