# P_flood achievability — results

*Diagnostic from `11c_pflood_achievability.py`. Routed from the 2026-05-29
main-report editorial review (gap C: per-well operational priority map for
§5.9 and §7 Conclusion 4).*

## Categorical scheme

Three bins on the rainfall multiplier λ from Script 11b (`11b_03_pflood_per_well.csv`).
λ is the cumulative winter-rainfall multiplier required to lift the cluster
summer minimum back above the relevant Curreli (2013) threshold by the end of
the recharge season.

| Category | λ band | Operational meaning |
|---|---|---|
| **Achievable** | λ < 1.5 | Reachable in normal-to-mildly-wet winters |
| **Marginal** | 1.5 ≤ λ < 2.5 | Reachable only in wet winters |
| **Unreachable** | λ ≥ 2.5 | Effectively unreachable under current climate |

## Counts by category and cluster

| Cluster | Achievable | Marginal | Unreachable | Cluster total |
|---|---|---|---|---|
| C1 | 8 | 0 | 0 | 8 |
| C2 | 28 | 4 | 0 | 32 |
| C3 | 21 | 4 | 0 | 25 |
| C4 | 2 | 9 | 2 | 13 |
| C5 | 0 | 7 | 3 | 10 |
| **All clusters** | **59** | **24** | **5** | **88** |

## Reading

- **Open dune zone (C1, C2, C3): 57 of 65 wells achievable**, with the remaining 8 marginal — none unreachable. This is the operational domain Conclusion 4 identifies for scrape targeting.
- **Forest zone (C4, C5): 2 of 23 wells achievable**, with 16 marginal and 5 unreachable. Most forest wells require more than mildly-wet winters; the unreachable wells split 3 in C5 Coastal Forest and 2 in C4 Main Forest.

The cluster pattern reflects the underlying mechanism. The open dune clusters
(C1 Lake Edge, C2 Dune, C3 Western Residual) sit on the shallow-substrate or
deep-sponge aquifer parcels where summer minima respond to winter recharge
with high efficiency (β₁ in the 2.5–4.6 range). The forest clusters (C4 Main
Forest, C5 Coastal Forest) carry canopy interception losses and lower β₁
(1.32–2.55), and C5 additionally carries the coastal-retreat gradient (Section
4.8.1), pushing its summer-minimum baseline progressively further below the
Curreli thresholds and increasing the rainfall multiplier required to recover.

## Drop-in text for §5.9 (Implications for Restoration and Monitoring)

Insert as a new paragraph in §5.9 after the topographic-scraping discussion,
between the existing "the operational zone for this intervention" sentence and
the prediction-equations paragraph:

> *Per-well categorisation against the P_flood multiplier (Figure N; `11c_pflood_achievability_per_well.csv`) operationalises the priority criterion identified in Conclusion 4. Of 57 wells across the open-dune clusters C1, C2 and C3, all but 8 are in the achievable category (λ < 1.5); none are unreachable. By contrast, of the 23 forest-zone wells in C4 and C5, only 2 sit in the achievable band and 5 are in the unreachable band (λ ≥ 2.5): 3 in C5 Coastal Forest (CEH17, FE3 and CEH31) and 2 in C4 Main Forest (CEH33 and CEH30). The categorisation provides a direct per-well lookup for scrape-targeting decisions: achievable wells in the C1/C2/C3 transitional zone are the operationally feasible candidates; the small number of marginal wells in the open dune (n = 8) define the upper edge of the operational envelope under current climate.*

## Suggested figure caption

> *Figure N. Per-well achievability categorisation against the P_flood rainfall multiplier (λ), the cumulative winter-rainfall depth required to lift each well's summer minimum back above the relevant Curreli (2013) threshold by end of recharge season, expressed as a multiple of climatological winter mean. Wells in the achievable category (λ < 1.5, green) are reachable in normal-to-mildly-wet winters; marginal wells (1.5 ≤ λ < 2.5, amber) only in wet winters; unreachable wells (λ ≥ 2.5, red) are effectively unreachable under current climate. The cluster pattern (open-dune C1/C2/C3 dominated by achievable; forest C4/C5 dominated by marginal-to-unreachable) operationalises Conclusion 4's priority criterion for scrape-target identification. Source: `11c_pflood_achievability.png`; per-well lookup table in `11c_pflood_achievability_per_well.csv`.*

## Caveats

- The λ values come from Script 11b's per-well calculation; they inherit Script 11b's assumptions about the cluster β coefficients and the climatological winter rainfall baseline. The categorical bin edges (1.5 and 2.5) are operational choices, not derived from any natural break in the data. Conclusion 4's text explicitly identifies the λ < 1.5 boundary; the marginal-vs-unreachable boundary at λ = 2.5 is selected to match the abstract's reference to a 1.5–2.5× rainfall multiplier band as the conservatively wet-winter zone.
- The achievability category describes whether the cluster summer minimum can be raised above the Curreli threshold by winter recharge alone. It does not account for scrape-as-drainage geometry effects (Section 4.5.3) or for forest-management interventions; these are separate degrees of freedom in the scenario framework (Section 4.10).
- Wells flagged as scraped in the existing per-well CSV (CEH36, CEH18, CEH21) retain their categorical assignment based on present-day λ; the category reflects post-intervention behaviour where applicable.

## Outputs

- `11c_pflood_achievability.png` — operational map for §5.9 / Conclusion 4.
- `11c_pflood_achievability_per_well.csv` — per-well lookup table with category column.
- `11c_pflood_achievability_results.md` — this memo.