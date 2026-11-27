# C3 de-trending check — results

*Diagnostic from `28_c3_detrend_check.py`, routed from
`HANDOVER_c3_detrend_check.md`.*

## Live fit values (forest-free linear-capped, Script 25)

| Parameter | Value |
|---|---|
| δ₀ (coast-edge slope) | **-31.28 mm/yr** |
| L (decay length)      | **902 m** |
| Sensitivity δ₀ (full fit) | -31.58 mm/yr |
| Sensitivity L (full fit)  | 1005 m |

## Headline result — C3 hydrographs after forest-free monthly-uniform de-trending

**10 of 12 C3 wells** carry a Script 25 dist_coast and
hydrograph (excluded: 2 wells without coastal-distance metadata —
typically the forest-zone or heavily perturbed wells dropped from Script 25's
forest-free fit, e.g. CEH36 and WMC3).

After de-trending against the un-de-trended cluster centroids:

| Destination | n | % of n_with_drift |
|---|---|---|
| **→ C1** | 0 | 0% |
| **→ C2** | 0 | 0% |
| **→ C3o** | 10 | 100% |
| **→ C4** | 0 | 0% |
| **→ C3f** | 0 | 0% |

**Verdict.** **H0 confirmed.** C3 is a genuinely distinct cluster; gradient adds drift but is not the constitutive mechanism.

## Sanity checks

| Source cluster | n (with drift) | Stays in cluster | % retained |
|---|---|---|---|
| C2 | 20 | 20 | 100% |
| C4 | 2 | 2 | 100% |
| C3f | 1 | 0 | 0% |

A high C2 retention is required for the procedure to be valid (C2 wells should
not be perturbed by a small δ(d) correction). Low C2 retention would indicate
the procedure is contaminating hydrographs rather than testing a hypothesis.

## Sensitivities (C3 only)

| Variant | → C2 | → C3 | Other |
|---|---|---|---|
| forest-free, monthly-uniform (HEADLINE) | 0 | 10 | 0 |
| forest-free, summer-only Jun–Sep | 0 | 9 | 1 |
| full δ₀ (includes forest) | 0 | 10 | 0 |
| L = 500 m | 0 | 10 | 0 |
| L = 1500 m | 0 | 10 | 0 |

## Excluded wells (no dist_coast_m available)

- `nw10` (C4 (Main Forest))
- `ceh2` (C4 (Main Forest))
- `ceh16` (C3f (Western Dune, forest))
- `ceh17` (C3f (Western Dune, forest))
- `ceh19` (C3f (Western Dune, forest))
- `ceh20` (C4 (Main Forest))
- `ceh30` (C4 (Main Forest))
- `ceh31` (C3f (Western Dune, forest))
- `ceh32` (C4 (Main Forest))
- `ceh33` (C4 (Main Forest))
- `ceh34` (C4 (Main Forest))
- `ceh36` (C3o (Western Dune, open))
- `ceh40` (C2 (Dune))
- `ceh41` (C2 (Dune))
- `ceh42` (C3o (Western Dune, open))
- `wmc3` (C3f (Western Dune, forest))

## Next step

See *What follows from the result* in `HANDOVER_c3_detrend_check.md`. Headline
verdict above maps onto either the H1-follow-on (report reframing) or the
H0-follow-on (single sentence in §5.4.3 noting the check was performed).

Per-well detail in `c3_detrend_check.csv`. Figure (if generated): `c3_detrend_check_panel.png`.
