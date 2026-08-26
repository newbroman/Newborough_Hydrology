> ## Recovered 2026-08-26 — READ THIS FIRST
>
> Written **27 April 2026**, superseded-banner added 26 May 2026, never committed,
> recovered from `~/Downloads/keep` under T-10 and kept **verbatim below**.
> Cited from the Methods Supplement. A second copy was found in Trash without the
> May banner; it is otherwise byte-identical and was discarded.
>
> **The note carries its own SUPERSEDED banner from 26 May 2026. That banner is
> right about the note and wrong about itself: its "canonical" columns are now
> three months old and every one of them has moved.** Checked 2026-08-26 against
> the committed pipeline:
>
> | | note (Apr) | May banner "canonical" | pipeline today |
> |---|---|---|---|
> | β₂ C1 | 1.42 | 0.9635 | **0.9228** |
> | β₂ C2 | 2.01 | 1.7668 | **1.7419** |
> | β₂ C3 | 1.818 | 1.8477 | **1.8073** |
> | β₂ C4 | 2.15 | 2.5480 | **2.5626** |
> | β₂ C5 | 1.41 | 1.3238 | **1.2743** |
>
> Source: `outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv`.
> The depth-PET λ values in the May banner have moved too — today's are C1 2.25,
> C2 0.95, C3 0.45, C4 0.20, C5 0.50, with ΔNSE +0.033 to +0.184
> (`outputs/15_depth_dependent_pet/15_03_benchmark_table.csv`), against the
> banner's C1 1.9, C2 0.8, C3 0.4, C4 0.15, C5 0.5 and +0.028 to +0.182.
>
> **Take no number from this file, including from its own correction table.**
> Both layers are dated records. The pipeline CSVs are the only current source.
>
> **The May banner's two conclusions do survive**, and they are the reason the
> file is worth keeping:
>
> - **The 22.6% β₂-ratio interception cross-check stays withdrawn.** On today's
>   coefficients `1 − β₂_C5/β₂_C3` gives **29.5%**, further still from Freeman's
>   24% than the 28.4% the banner computed. The figure is not a usable
>   cross-validation, and §5.6 keeps only the qualitative statement.
> - The decomposition **method** and the C4-anomaly reasoning are what this note
>   is for.
>
> **Two cautions on the May banner's own wording.** It attributes the β₂ shift to
> the move from lag-1 to lag-0. That is doubtful: D-008, `config.py:188` and the
> Methods Supplement all state that the lag change is a relabelling under which
> the coefficients are numerically identical, so something else moved these
> numbers — most likely the intervening Script 03 work. The cause is not
> established here, only that the movement is real. And the banner cites
> `SSM_FORMULATION_REFERENCE`, which does not exist in this repository under any
> name; the live authority for the headline lag is **D-008**, `config.py:188`,
> and the Methods Supplement section "History: why HEADLINE_LAG was 1 and is now 0".
>
> ---

> # ⚠️ SUPERSEDED — DO NOT CITE FIGURES FROM THIS NOTE
>
> **Marked superseded:** 26 May 2026, during the §5 main-report editorial pass.
>
> This note dates from the **27 April 2026 Script 03 rebuild** and describes a
> **lag-1 displacement model**. The canonical pipeline is now **HEADLINE_LAG = 0**
> (same-month rainfall; see `SSM_FORMULATION_REFERENCE`). Every β₂ value, and
> therefore every Sy / Kc / interception figure derived from it in this note, is
> **stale**. The note is retained only as a record of the decomposition *method*
> and the C4-anomaly reasoning; its **numbers must not be re-imported** into the
> report, the methods supplement, or any downstream note.
>
> **Stale → canonical β₂ (cluster centroid, `03_03_cluster_mechanistic_coefficients.csv`):**
>
> | Cluster | This note | Canonical |
> |---|---|---|
> | C1 | 1.42 | 0.9635 |
> | C2 | 2.01 | 1.7668 |
> | C3 | 1.818 / 1.82 | 1.8477 |
> | C4 | 2.15 / 2.149 | 2.5480 |
> | C5 | 1.41 / 1.407 | 1.3238 |
>
> **The "I = 22.6%" β₂-ratio interception cross-check is withdrawn.** It was a
> hand-calculation (`I = 1 − β₂_C5/β₂_C3`) on the stale 1.407 / 1.818 pair. On the
> canonical β₂ the same definition gives ≈28.4% — further from Freeman's 24%, not
> closer — so the figure is not a usable cross-validation. Per Martin's decision
> (May 2026), the main report §5.6 drops the specific number and keeps only the
> qualitative statement that the open-dune vs forest β₂ contrast is *consistent
> with* a canopy interception loss of the order Freeman (2008) reports. The
> methods supplement never carried the 22.6% figure and needs no change.
>
> **Depth-PET λ values** in this note (C3 0.35, C4 0.20, C5 0.45) are also stale;
> canonical values are C1 1.9, C2 0.8, C3 0.4, C4 0.15, C5 0.5
> (`15_03_benchmark_table.csv`), ΔNSE range +0.028 to +0.182.
>
> ---
>
# β₂ Decomposition, Interception Estimates, and C4 Anomaly

**Written:** 27 April 2026, Script 03 rebuild chat
**Updated:** 27 April 2026 — Script 15 λ values corrected to current pipeline output
**Status:** Findings from the displacement-formulation SSM (lag-1, datum 3.7 m)

---

## Summary

The SSM's β₂ coefficient (fitted on the −PET column) is a compound
parameter that absorbs crop coefficient (Kc), specific yield (Sy),
canopy interception (I), and depth-coupling effects:

    β₂ ≈ Kc · (1 − I) / Sy

### Thornthwaite reference surface — IMPORTANT

Thornthwaite PET was developed from watershed water balance data
across temperate forested catchments (eastern US). The implicit
reference surface is **temperate forest**, NOT grassland.
(The grass reference convention comes from FAO Penman-Monteith /
FAO-56, which is a different method.)

This means:
- For forest clusters (C4, C5): Kc ≈ 1.0 under Thornthwaite
- For open-ground clusters (C1 Lake Edge, C2 Dune, C3 Western):
  Kc < 1.0 (open ground transpires less than forest per unit PET)

This fundamentally changes the β₂ interpretation. C4 Main Forest's
high β₂ is NOT anomalous — it's behaving as expected for forest
under a forest-referenced PET. The variation in β₂ across clusters
is driven primarily by Sy differences (substrate geology — clay vs
sand), not by crop coefficient or interception differences.

---

## Results (centroid fits, lag-1, datum 3.7 m)

| Cluster | β₂ | Vegetation | Substrate | Interpretation |
|---|---|---|---|---|
| C1 Lake Edge | 1.42 | Mixed, lake | Clay | Low Kc (<1), low Sy (clay) — effects offset |
| C2 Dune | 2.01 | Open dune | Clay | Low Kc (<1) but very low Sy (clay) — Sy dominates |
| C3 Western Res. | 1.82 | Mixed | Sand | Low-moderate Kc, moderate Sy (sand) |
| C4 Main Forest | 2.15 | Corsican pine | Clay/bedrock? | Kc ≈ 1, low Sy — β₂ reflects 1/Sy |
| C5 Coastal Forest | 1.41 | Corsican pine | Sand | Kc ≈ 1, higher Sy (sandier, younger forest) |

### Implied Sy (assuming Kc ≈ 1.0 for forest, Kc ≈ 0.7 for open ground)

Using approximate Kc values (Thornthwaite convention):

| Cluster | Kc (approx) | I | Sy = Kc·(1−I)/β₂ |
|---|---|---|---|
| C1 Lake Edge | 0.7 | 0.0 | 0.7/1.42 = 49% |
| C2 Dune | 0.7 | 0.0 | 0.7/2.01 = 35% |
| C3 Western Res. | 0.7 | 0.0 | 0.7/1.82 = 38% |
| C4 Main Forest | 1.0 | 0.24 | 1.0·0.76/2.15 = 35% |
| C5 Coastal Forest | 1.0 | 0.24 | 1.0·0.76/1.41 = 54% |

These Sy estimates are physically plausible:
- C1, C5: ~50–54% — sand aquifer with good porosity
- C2, C3, C4: ~35–38% — lower Sy consistent with clay substrate
  (C2, C3) or root-modified/thinner aquifer (C4)
- C4 ≈ C2 ≈ 35% — C4's apparent Sy anomaly disappears under the
  correct Thornthwaite convention; its low Sy is in line with the
  clay-underlain eastern clusters

### The C4 vs C5 comparison: isolating Sy

C4 and C5 are both Corsican pine with the same interception (I ≈ 0.24)
and the same Kc (both sparse pine on sand, similarly exposed). So
comparing their β₂ values isolates Sy:

    β₂_C4 / β₂_C5 = Sy_C5 / Sy_C4 = 2.15 / 1.41 = 1.52

C5's Sy is 52% higher than C4's. This is a direct, model-derived
measurement of the substrate difference between the two forest
clusters, with no dependence on Kc or I (both cancel).

### Anchoring the Sy values

**From C3 vs C5:** The interception estimate (I = 22.6%) implies
Sy_C3 ≈ Sy_C5 (both on sandy substrate, β₂ ratio matches the
expected (1−I) scaling). So:

    Sy_C5 ≈ Sy_C3

**From C4 vs C5:**

    Sy_C4 = Sy_C5 / 1.52

**From literature:** Medium dune sand Sy is typically 25–35%.
Taking Sy_C5 ≈ Sy_C3 ≈ 30% (mid-range for well-sorted dune sand):

| Cluster | Sy (estimated) | Substrate |
|---|---|---|
| C3 Western Residual | ~30% | Sandy aquifer (control) |
| C5 Coastal Forest | ~30% | Sandy, younger/thinner forest |
| C4 Main Forest | ~20% | Lower Sy — thinner aquifer over clay/bedrock |

**Cross-check:** Using Sy_C5 = 30% to back out Kc:

    From C5: Kc = β₂_C5 · Sy_C5 / (1−I) = 1.41 · 0.30 / 0.76 = 0.56
    From C3: Sy_C3 = Kc / β₂_C3 = 0.56 / 1.82 = 0.31 (≈ 30%) ✓

Kc ≈ 0.56 for Newborough vegetation under Thornthwaite. This is
physically reasonable: neither sparse pine nor dune scrub transpires
at temperate-deciduous-forest rates.

**Cross-check via C4:**

    From C4: β₂_C4 = Kc · (1−I) / Sy_C4
             2.15 = 0.56 · 0.76 / Sy_C4
             Sy_C4 = 0.43 / 2.15 = 0.198 ≈ 20% ✓

### Physical interpretation of C4's low Sy

C4 Main Forest's Sy ≈ 20% vs C3/C5's ~30% is a ~33% reduction in
effective drainable storage. Three mechanisms, likely in combination:

1. **Thinner aquifer over bedrock/clay** — C4 may sit where the
   sand body is thinner, with the underlying till or Carboniferous
   bedrock closer to the water table. A thinner saturated column
   gives less drainable volume per unit head change.

2. **Root-modified porosity** — decades of mature pine root growth,
   organic matter incorporation, and biological soil crusting reduce
   the effective macroporosity of the upper sand horizon.

3. **Both acting together** — the forest was planted preferentially
   on the higher ground (closer to bedrock) and the root system has
   further reduced the already-lower porosity.

This finding is consistent with the earlier observation that C4
was the binding constraint for the displacement datum (3.7 m was
needed to get C4's β₃ significant, while other clusters achieved
significance at 0.5–1.3 m). A thinner aquifer means the drainage
base is closer to the water table, requiring a deeper datum to
produce a positive displacement.

### Summary of the β₂ decomposition chain

Starting from three observables (β₂_C3, β₂_C4, β₂_C5) and two
assumptions (same I and Kc for C4 and C5; same Sy for C3 and C5):

    I = 1 − β₂_C5/β₂_C3 = 22.6%     (cf. literature 24%)
    Sy_C3 ≈ Sy_C5 ≈ 30%              (cf. literature 25–35% for dune sand)
    Sy_C4 ≈ 20%                       (thinner aquifer / root-modified)
    Kc ≈ 0.56                         (sparse vegetation, Thornthwaite ref.)

All four values are physically plausible and internally consistent.
The interception estimate agrees with the literature and with the
earlier WTF forward-prediction method.

### Interception estimate: C3 vs C5 (corrected method)

An independent interception estimate is still possible if we compare
an open cluster with a forest cluster, accounting for the Kc
difference:

    β₂_open = Kc_open · 1.0 / Sy
    β₂_forest = Kc_forest · (1−I) / Sy

If Sy is the same between the two clusters:

    I = 1 − (β₂_forest · Kc_open) / (β₂_open · Kc_forest)

Using C3 (open, Kc ≈ 0.7) and C5 (forest, Kc ≈ 1.0), assuming
similar sand substrate:

    I = 1 − (1.41 · 0.7) / (1.82 · 1.0)
      = 1 − 0.987 / 1.82
      = 1 − 0.542
      = 0.458 (45.8%)

This is HIGHER than the 24% literature value. Possible explanations:
- Kc_open is not 0.7 — it could be higher (closer to 0.85–0.9),
  which would bring the estimate down toward 24%
- Sy is not the same between C3 and C5 — C5 (coastal sand) may
  have higher Sy than C3 (western, possibly more heterogeneous),
  which inflates the ratio
- The method is sensitive to the assumed Kc values

With Kc_open = 0.85 (reasonable for mixed vegetation):

    I = 1 − (1.41 · 0.85) / (1.82 · 1.0) = 1 − 0.659 = 0.341 (34%)

With Kc_open = 0.95:

    I = 1 − (1.41 · 0.95) / (1.82 · 1.0) = 1 − 0.736 = 0.264 (26%)

The estimate converges on the literature value (~24%) at Kc_open ≈ 1.0,
which would mean the open ground at Newborough transpires at nearly
the same rate as the Thornthwaite reference forest. Given that C3
Western Residual has substantial scrub and regenerating vegetation
(not bare sand), Kc_open near 1.0 is not implausible.

**Bottom line:** The β₂ ratio method can reproduce the 24%
interception estimate but is sensitive to the assumed Kc for open
ground. The Thornthwaite convention makes this less clean than the
original (incorrect) grass-reference analysis suggested.

---

## Implications for the pipeline

### Script 03 (SSM fits)
No code change needed. The β₂ values and the interpretation above
are derived from existing output (`03_03_cluster_mechanistic_coefficients.csv`).
The interception estimate is a post-hoc calculation, not a model
input.

### Script 15 (depth-dependent PET)
The depth-coupling effect is modelled in Script 15 but not fed back
into Script 03's PET series. If depth-adjusted PET were used as the
Script 03 input, β₂ would change — specifically, C4's β₂ would
increase further (because the PET presented to the model would be
smaller, requiring a larger coefficient to explain the same head
change). This would widen the C4 anomaly, not resolve it.

### Script 16 (water balance)
The water balance decomposition uses β₂ to estimate the ET fraction.
The C4 anomaly means that naively using β₂_C4 · PET as the ET
component overstates ET for C4 relative to what the canopy actually
transpires. The excess β₂ is absorbing storage and/or recharge
effects that belong in other terms.

### Script 23 result: ridge recharge ruled out as β₂ driver

Script 23 (ridge recharge lag test) found no significant distance-lag
relationship between SSM residuals and ridge distance (Spearman
rho = 0.085, p = 0.53, n = 56). The ridge recharge hypothesis
(mechanism #3) does not explain C4's high β₂ through a time-varying
signal. A steady-state ridge baseflow is possible but would be
absorbed by the Model B intercept (α), not by β₂. **Mechanism #3
is effectively ruled out as a β₂ driver.**

### Script 15 result (UPDATED — lag-1 displacement model): depth coupling

Script 15 was rerun under the lag-1 displacement specification.
The results are dramatically different from the old (lag-0, no datum) run:

| Cluster | Old λ | Old ΔNSE | **New λ** | **New ΔNSE** |
|---|---|---|---|---|
| C1 Lake Edge | 0.00 | 0.000 | **1.90** | **+0.182** |
| C2 Dune | 0.00 | 0.000 | **0.80** | **+0.073** |
| C3 Western Res. | 0.15 | −0.004 | **0.35** | **+0.025** |
| C4 Main Forest | 0.80 | −0.017 | **0.20** | **+0.104** |
| C5 Coastal Forest | 0.90 | +0.011 | **0.45** | **+0.032** |

**Key finding:** The old model was conflating two depth effects — depth
dependence of ET (a β₂ effect) and depth dependence of drainage (a β₃
effect). The displacement datum separates them. Once β₃ is correctly
specified via displacement, the residual depth-dependent PET signal:
- Is STRONGEST for C1 Lake Edge (λ=1.90, +0.18 NSE) — shallow water
  table evaporation near the lake is the dominant ET pathway
- Is MODERATE for C2 Dune (λ=0.80, +0.07 NSE) — oscillating shallow
  water tables with real depth-dependent ET
- Is WEAKEST for C4 Main Forest (λ=0.20, +0.10 NSE) — despite the
  large ΔNSE, C4 has the smallest λ, meaning the depth coupling is
  the most gradual. The improvement reflects C4's narrow depth range
  (thin aquifer) amplifying even weak coupling, not a strong
  depth-dependent ET mechanism.

The AIC comparison (n=99, k=3 vs k=4) favours the DDP at every cluster
(ΔAIC +17 to +98; ΔBIC +14 to +96). However, the DDP introduces a
nonlinearity that breaks the closed-form threshold and scenario
equations used throughout the pipeline. The standard SSM is therefore
retained as the primary operational model, with the DDP acknowledged
as a diagnostic finding (see DDP_EVALUATION.md).

### Updated mechanism ranking for C4 β₂ anomaly

1. **Lower Sy** — aquifer thinner over bedrock/clay, root-modified
   porosity. Now effectively the ONLY mechanism standing. DOMINANT.
2. **Root-modified storage** — subsumed into mechanism #1 (both act
   through Sy). CONTRIBUTING.
3. **Ridge recharge subsidy** — ruled out by Script 23 (H0 not
   rejected, rho = 0.085, p = 0.53).
4. **Deep-root transpiration (Kc > 1)** — ruled out by updated
   Script 15 (C4 has the lowest λ of all clusters; its depth
   coupling is the weakest, not strongest).
5. **Depth coupling (opposite direction)** — no longer relevant;
   the old finding (λ=0.80 worsening C4) was an artefact of the
   mis-specified β₃ term.

### Report text
The C5 interception estimate (22.6% from β₂ ratio, consistent with
24% from literature and WTF forward prediction) should appear in
the methods discussion as independent cross-validation. The C4
anomaly should be acknowledged with the three candidate mechanisms
listed. The equal-Sy assumption should be stated explicitly so
readers can evaluate the method's applicability.

---

## Key numbers for reference

| Quantity | Value | Source |
|---|---|---|
| β₂ C3 (reference) | 1.818 | Script 03 centroid fit |
| β₂ C5 | 1.407 | Script 03 centroid fit |
| I_C5 (β₂ ratio vs C3) | 22.6% | This analysis |
| I_C5 95% CI | 12.8–52.8% | Bootstrap, per-well β₂ |
| I literature (Corsican pine) | 24% | Project assumption |
| I broadleaf (literature) | 15% | Project assumption |
| β₂ C4 | 2.149 | Script 03 centroid fit |
| I_C4 (β₂ ratio vs C3) | −18.2% | Physically implausible |
| Sy_C4 needed for I=24% | ~35% | Back-calculated |
| DDP λ C1 | 1.90 m⁻¹ | Script 15, current pipeline |
| DDP λ C2 | 0.80 m⁻¹ | Script 15, current pipeline |
| DDP λ C3 | 0.35 m⁻¹ | Script 15, current pipeline |
| DDP λ C4 | 0.20 m⁻¹ | Script 15, current pipeline |
| DDP λ C5 | 0.45 m⁻¹ | Script 15, current pipeline |
| DDP ΔNSE range | +0.025 to +0.182 | Script 15, current pipeline |
| DDP ΔAIC range | +17 to +98 | This analysis (n=99, Δk=1) |
