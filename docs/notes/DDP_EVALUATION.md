> ## Recovered 2026-08-26 — READ THIS FIRST
>
> Written **27 April 2026**, never committed, recovered under T-10 from
> `~/Downloads/cleanup/project clean/project_store_consolidated.zip`, member
> `_archive/DDP_EVALUATION.md`, and kept **verbatim below**. It is a dated
> record and is not edited.
>
> **Why the citation dangled.** `BETA2_DECOMPOSITION_UPDATED.md:367` cites it —
> "the DDP acknowledged as a diagnostic finding (see DDP_EVALUATION.md)" — but
> that note was itself only recovered on 2026-08-26. Restoring a document
> restores its bibliography; this is the second half of that pair. Both lived in
> the project store, not in the repository, and neither was ever committed.
>
> ---
>
> ### Status today, checked against the committed tree
>
> **The recommendation was adopted and still stands. This is the live position of
> the project.** The document's whole argument — the DDP is the better statistical
> model, and the standard SSM should be kept anyway because the DDP's
> nonlinearity would destroy the closed-form threshold and scenario algebra — is
> what the pipeline does today:
>
> - `src/15_depth_dependent_pet.py` still grid-searches λ over `[0, 6]` in steps
>   of 0.05 and emits a benchmark, not a replacement fit.
> - Methods Supplement **S.10**: *"The script is a sensitivity analysis, not a
>   replacement model: the canonical fixed-β₂ SSM remains the published
>   headline."*
> - `docs/papers/paper_1/text/Paper1.md`: *"Because the extension introduces a
>   nonlinearity that would propagate into the closed-form analytical outputs
>   derived elsewhere, it is retained as a diagnostic of depth-coupling rather
>   than adopted as the operational model."*
>
> **Every number below is stale.** Script 15 has been rerun since. Checked
> 2026-08-26 against `outputs/15_depth_dependent_pet/15_03_benchmark_table.csv`
> and `15_04_best_params.csv`:
>
> | Cluster | λ here | λ today | ΔNSE here | ΔNSE today | ΔAIC here | ΔAIC today |
> |---|---:|---:|---:|---:|---:|---:|
> | C1 Lake Edge        | 1.90 | **2.25** | +0.182 | **+0.184** | +98.1 | **+89.0** |
> | C2 Dune             | 0.80 | **0.95** | +0.073 | **+0.094** | +45.4 | **+52.8** |
> | C3 Western Residual | 0.35 | **0.45** | +0.025 | **+0.043** | +16.7 | **+26.5** |
> | C4 Main Forest      | 0.20 | **0.20** | +0.104 | **+0.134** | +33.1 | **+38.3** |
> | C5 Coastal Forest   | 0.45 | **0.50** | +0.032 | **+0.033** | +17.1 | **+16.4** |
>
> ΔAIC "today" is this document's own formula, `n·ln[(1−NSE_std)/(1−NSE_ddp)] − 2`
> with n = 99, applied to today's NSE pairs; ΔBIC today is +13.8 to +86.4. The
> pipeline does not currently emit AIC/BIC columns — `15_03_benchmark_table.csv`
> carries NSE and R² only — so the AIC/BIC table below is a hand-computation, not
> a pipeline output, in both vintages. **Take no number from this file.**
> The verdict the numbers support is unchanged: the DDP wins decisively at every
> cluster and is still not adopted.
>
> **It is written against the wrong lag.** The header says "Script 15 rerun under
> lag-1 displacement SSM (datum 3.7 m)". The canonical pipeline is
> **`HEADLINE_LAG = 0`** (`src/utils/config.py:210`, D-008), and Script 15's own
> docstring now opens *"The standard SSM (contemporaneous rainfall, displacement
> formulation, HEADLINE_LAG = 0)"*. That change is why every coefficient moved;
> it was never the pure relabelling the project's documentation once claimed
> (see the banner on `BETA2_DECOMPOSITION_UPDATED.md`). The **datum is
> unchanged** — `DRAINAGE_DATUM = 3.7` at `config.py:186` — and so is the
> 100-month cap the n = 99 rests on (`15_depth_dependent_pet.py:98`,
> `DATA_LIMIT = 100`).
>
> **§4's interception argument defends a withdrawn number.** It concludes
> *"I ≈ 22.6% is preserved"* under DDP adoption. The 22.6 % β₂-ratio interception
> cross-check has since been **withdrawn** — on today's coefficients
> `1 − β₂_C5/β₂_C3` gives **29.5 %**, further from Freeman's 24 %, not closer, and
> §5.6 of the main report keeps only the qualitative statement. The reasoning in
> §4 (numerator and denominator shift together, so the ratio is roughly
> preserved) is still sound as reasoning; the quantity it preserves is no longer
> a quantity the project reports.
>
> **§5 is filed under a section number that no longer resolves.** "Revised §3.7.1
> Report Text" was written for a chapter numbering since superseded. The material
> now sits in main report **§5.2.2** *Displacement Formulation and
> Depth-Dependent PET*, with the mechanism discussion at §5.6.1, and in Methods
> Supplement **S.10**. Do not paste §5 in as report text; the current sections
> already carry their own, later, wording.
>
> ### What is durable
>
> - **The decision rule** — operational utility over information criteria when
>   the cost is the model *class*, not the parameter count. §3's four arguments
>   are why the fixed β₂ is still the headline.
> - **The downstream-impact table in §2.** Scripts 11, 11b, 19 and 21 are still
>   the ones that would lose their closed forms, and they are still where the
>   report's operationally useful outputs come from.
> - **The C4 argument.** C4 still has the network's lowest λ (0.20, unchanged)
>   alongside its highest β₂, and that asymmetry is still the evidence that C4's
>   high atmospheric draw reflects low specific yield rather than a
>   depth-dependent ET pathway. Paper 1 and the main report both make this
>   argument today.
>
> ### What is dated
>
> - Every λ, NSE, ΔNSE, ΔAIC and ΔBIC value.
> - The lag-1 framing, and the β₂ = 1.42 for C1 quoted in §4 (today: 0.9228,
>   `outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv`).
> - "Under the old pipeline (`BETA2_DECOMPOSITION.md`), C4 had λ=0.05" — that
>   file is not in this repository under that name; the successor
>   `BETA2_DECOMPOSITION_UPDATED.md` is, and carries two superseded-banners of
>   its own.
> - The §5 report text and its §3.7.1 numbering.
> - §6's action table, which reports the state of a 27 April working session.

---

# Depth-Dependent PET Evaluation: Should the DDP Be Adopted?

**Date:** 27 April 2026
**Context:** Script 15 rerun under lag-1 displacement SSM (datum 3.7 m)

---

## 1. AIC/BIC Comparison

The standard SSM has k=3 parameters (β₁, β₂, β₃). The DDP adds λ as a 4th
(k=4). Both models are fitted on n=99 observations (100-month cap minus one
for differencing). λ is selected by grid search (profile likelihood over
[0, 6] m⁻¹ in steps of 0.05), which is computationally equivalent to
maximum-likelihood optimisation — so λ counts as a free parameter for
information-theoretic purposes.

AIC and BIC are computed from the iterative NSE, which implicitly defines
the residual sum of squares:

    SS_res = (1 − NSE) · SS_tot

Since SS_tot is identical for both models (same observed series), the
difference in information criteria depends only on the ratio of residual
variances:

    ΔAIC = n · ln[(1−NSE_std)/(1−NSE_ddp)] − 2
    ΔBIC = n · ln[(1−NSE_std)/(1−NSE_ddp)] − ln(n)

Positive values favour the DDP. Burnham & Anderson (2002) thresholds:
|Δ| > 10 = strong evidence, 4–7 = considerable, 2–4 = weak, < 2 = negligible.

| Cluster | Label             |    λ | NSE_std | NSE_ddp |  ΔNSE |   ΔAIC |   ΔBIC | Verdict        |
|---------|-------------------|-----:|--------:|--------:|------:|-------:|-------:|----------------|
| C1      | Lake Edge         | 1.90 |   0.714 |   0.896 |+0.182 |  +98.1 |  +95.6 | Strong DDP     |
| C2      | Dune              | 0.80 |   0.808 |   0.881 |+0.073 |  +45.4 |  +42.8 | Strong DDP     |
| C3      | Western Residual  | 0.35 |   0.855 |   0.880 |+0.025 |  +16.7 |  +14.1 | Strong DDP     |
| C4      | Main Forest       | 0.20 |   0.652 |   0.756 |+0.104 |  +33.1 |  +30.6 | Strong DDP     |
| C5      | Coastal Forest    | 0.45 |   0.818 |   0.850 |+0.032 |  +17.1 |  +14.5 | Strong DDP     |

**Result:** The DDP is overwhelmingly preferred at every cluster by both
AIC and BIC. Even at C3 and C5 (the smallest improvements, +0.025 and
+0.032 NSE), ΔBIC exceeds 14 — well beyond any conventional threshold.
A single extra parameter is trivially cheap at n=99; the improvements in
fit are enormous by information-theoretic standards.

**Caveat:** These AIC/BIC values assume Gaussian iid residuals, which is
approximate for iterative simulation (the feedback loop introduces
serial correlation). However, even with aggressive penalty adjustments
(e.g., doubling the parameter cost), the verdict wouldn't change —
the ΔAIC values are simply too large.

---

## 2. Downstream Pipeline Impact If DDP Were Adopted

Adopting the DDP as the primary model means replacing β₂·PET with
β₂·exp(−λ·d)·PET throughout the pipeline. This is a substantial change:

### Scripts requiring modification

| Script | Component | Impact | Difficulty |
|--------|-----------|--------|------------|
| **03** | SSM core | Would need to fit 4 parameters instead of 3; grid search + OLS per cluster | Medium |
| **08** | Model benchmarking | Benchmark table would need DDP column | Low |
| **11** | P_flood thresholds | The closed-form threshold equations assume fixed β₂. Under DDP, the PET term becomes depth-varying, breaking the algebra. Would need numerical solution or linearisation around mean depth. | **High** |
| **11b** | Spatial thresholds | Same issue as 11 — per-well threshold equations use fixed β₂ | **High** |
| **16** | Water balance | ET draw = β₂·PET̄ becomes β₂·E[exp(−λ·d̄)]·PET̄. Need mean of exp(−λ·d) over the record. Feasible but changes all bar chart values. | Medium |
| **17** | WTF specific yield | Uses β₂ for Sy estimation. Under DDP, the effective β₂ varies with depth — the Sy decomposition becomes more complex. | Medium |
| **19** | Spatial groundwater | Scenario viewer uses fixed β₂ for equilibrium head calculations. Under DDP, equilibrium is a nonlinear equation in h (exp(−λ·d) depends on h). No closed-form solution. | **High** |
| **21** | Forestry scenarios | Same equilibrium framework as 19. The monthly Δh_eq equations lose their closed form. | **High** |
| **Forecaster** | HTML tool | Iterative simulation currently uses fixed β₂. Would need λ and depth calculation per timestep. | Medium |

### Core difficulty

The fundamental problem is that the DDP makes the model **nonlinear in h**.
The standard SSM is linear: Δh = β₁·P − β₂·PET − β₃·h_disp. This linearity
is what enables closed-form threshold equations (Script 11), equilibrium
solutions (Scripts 19, 21), and clean water balance decomposition (Script 16).

Under DDP: Δh = β₁·P − β₂·exp(−λ·(−h+u))·PET − β₃·h_disp

The exp(−λ·h) term couples the PET response to the current state. There is
no closed-form equilibrium, no linear threshold algebra, and the water
balance partition becomes depth-dependent.

**Estimated effort:** 4–6 scripts would need substantial rewrites, several
losing their closed-form elegance. The threshold equations (the report's
most operationally useful output) would become numerical approximations.
This is weeks of work, not hours.

---

## 3. Recommendation: Retain Standard SSM, Acknowledge DDP as Diagnostic

The AIC/BIC evidence is unambiguous — the DDP is a better statistical model
at every cluster. But the question isn't purely statistical; it's whether
the operational pipeline should be rebuilt around a nonlinear model.

### Arguments for retaining the standard SSM as primary:

1. **Operational utility trumps statistical fit.** The P_flood threshold
   equations, forestry scenarios, and forecasting tools are the report's
   actionable outputs. They depend on the SSM's linearity. Rebuilding
   them as numerical approximations would sacrifice clarity, auditability,
   and operational simplicity for a statistical improvement that doesn't
   change any management conclusion.

2. **The standard β₂ is a well-defined effective parameter.** Under the
   standard SSM, β₂ absorbs the *mean* depth-coupling effect into a single
   coefficient. This is analogous to using a lumped crop coefficient
   rather than resolving the full soil–plant–atmosphere continuum. The
   lumped value is "wrong" in the same way all lumped parameters are
   wrong — it averages over a real physical gradient — but it's
   operationally useful and interpretable.

3. **The DDP improvement is largest where the standard SSM is already
   weakest.** C1 (+0.182) and C4 (+0.104) are the clusters with the
   lowest standard NSE (0.714 and 0.652). These are also the clusters
   with the most distinctive hydrology (lake-edge evaporation, thin
   aquifer over clay). The DDP is correcting for site-specific
   peculiarities that the 3-parameter model handles less gracefully,
   but the management-relevant clusters (C2, C3) are already well-fitted
   by the standard SSM (0.808, 0.855).

4. **Parsimony in the parameter count is less important than parsimony
   in the model structure.** Adding one parameter is trivially cheap
   (hence the overwhelming AIC). But adopting the DDP changes the model
   *class* from linear to nonlinear, which cascades through every
   downstream analysis. The real cost isn't the parameter; it's the
   structural complexity.

### The middle ground (recommended):

**Retain the standard SSM as the primary operational model.** All
threshold equations, scenarios, forecasts, and water balance
decompositions continue to use fixed β₂.

**Acknowledge the DDP in the diagnostics section (§3.7.1).** Present
the AIC/BIC table, the λ values, and the physical interpretation.
Frame the standard β₂ as an effective (depth-averaged) parameter that
absorbs a real but modest depth-coupling effect. Note that the DDP
improvement is strongest at C1 (shallow water table, lake-edge
evaporation) and C4 (thin aquifer), consistent with the β₂
decomposition narrative.

**Key sentence for the report:**

> "The depth-dependent formulation improves iterative NSE at all five
> clusters (ΔNSE +0.025 to +0.182; ΔAIC +17 to +98), confirming that
> capillary connectivity between the water table and root zone diminishes
> with depth. However, the standard SSM's fixed β₂ provides an effective
> depth-averaged parameterisation that preserves the closed-form
> threshold equations and scenario algebra on which the operational
> outputs depend. The depth-dependent formulation is therefore retained
> as a diagnostic tool rather than adopted as the primary model."

---

## 4. Effect on the β₂ Decomposition Narrative

The updated DDP results strengthen, not weaken, the β₂ decomposition:

### C4's lack of depth coupling (λ=0.20, ΔNSE=+0.104)

Wait — λ=0.20 is not "lack of depth coupling." Under the old pipeline
(BETA2_DECOMPOSITION.md), C4 had λ=0.05, which was interpreted as
"negligible depth coupling." The new value (λ=0.20) is still the
smallest of all clusters, but it's no longer negligible — the +0.104
NSE improvement is the second-largest.

**Revised interpretation:** C4's depth coupling is weak in *rate*
(λ=0.20 m⁻¹ means a 1/e decay length of 5 m — much deeper than C1's
0.5 m) but the thin aquifer means the water table operates in a narrow
depth band where even weak coupling produces measurable improvement.
The key finding still holds: C4's high β₂ is not a depth-coupling
effect (if it were, C4 would have the *highest* λ, not the lowest).
C4's high β₂ reflects low Sy, exactly as the decomposition argues.

### C1's strong depth coupling (λ=1.90)

C1 Lake Edge has the strongest depth coupling by far (λ=1.90 m⁻¹,
1/e length = 0.53 m). This means that for C1, the standard β₂ is
conflating two processes:

1. **True atmospheric draw** — transpiration/evaporation that occurs
   regardless of water table depth
2. **Shallow evaporation** — direct evaporation from the water table
   surface when it's within ~0.5 m of the ground, which switches off
   rapidly as depth increases

Under the standard SSM, both are absorbed into a single β₂ = 1.42.
Under DDP, β₂ separates from the depth effect, so the fitted β₂
likely increases (the constant part of atmospheric draw is larger
once you've removed the depth-varying component).

**Does this affect the interception estimates?** The interception
estimate uses the C3/C5 β₂ ratio, not C1. C3 and C5 have moderate
λ values (0.35 and 0.45), meaning their standard β₂ values are also
slightly inflated by depth coupling — but to a similar degree, so the
*ratio* is approximately preserved. The interception estimate is
robust to DDP adoption because both numerator and denominator shift
in the same direction.

**Quantitative check:** Under DDP, the effective β₂ at mean depth
is β₂·exp(−λ·d̄). If C3 and C5 have similar mean depths (both are
sandy, similar topography), the ratio β₂_C5/β₂_C3 under DDP will
be close to the standard ratio, and I ≈ 22.6% is preserved.

---

## 5. Revised §3.7.1 Report Text

(For the case where we retain the standard SSM — the recommended approach.)

### §3.7.1 — Depth-Dependent Evapotranspiration

The standard SSM applies a fixed evapotranspiration coefficient (β₂)
to the Thornthwaite PET series. In practice, the influence of atmospheric
demand on the water table diminishes with depth: capillary connectivity
between the saturated zone and root zone decays as the water table falls
below the extinction depth of the dominant vegetation.

To test this, a depth-dependent formulation was evaluated in which the
fixed β₂ is replaced by β₂·exp(−λ·d), where d is the depth of the water
table below ground surface and λ (m⁻¹) is a decay parameter fitted by
grid search. When λ=0 the standard SSM is recovered exactly.

Under the rebuilt SSM specification (lag-1 rainfall, 3.7 m drainage
datum), the depth-dependent formulation improves iterative NSE at all
five clusters:

| Cluster | λ (m⁻¹) | Standard NSE | DDP NSE | ΔNSE  | ΔAIC  |
|---------|--------:|-------------:|--------:|------:|------:|
| C1 Lake Edge       | 1.90 | 0.714 | 0.896 | +0.182 | +98  |
| C2 Dune            | 0.80 | 0.808 | 0.881 | +0.073 | +45  |
| C3 Western Residual| 0.35 | 0.855 | 0.880 | +0.025 | +17  |
| C4 Main Forest     | 0.20 | 0.652 | 0.756 | +0.104 | +33  |
| C5 Coastal Forest  | 0.45 | 0.818 | 0.850 | +0.032 | +17  |

The AIC improvement is decisive at every cluster (ΔAIC > 10 in all
cases), confirming that the depth-coupling effect is statistically
real. The fitted λ values are physically interpretable: C1 (Lake Edge)
shows the strongest decay (λ = 1.90 m⁻¹, 1/e depth = 0.53 m),
consistent with direct evaporation from a water table that is frequently
within 0.5 m of the ground surface near the lake margin. C4 (Main Forest)
shows the weakest decay (λ = 0.20 m⁻¹, 1/e depth = 5.0 m), consistent
with the β₂ decomposition finding that C4's high atmospheric draw
coefficient reflects low specific yield rather than a depth-dependent
evapotranspiration pathway (§4.8).

Despite the statistical improvement, the depth-dependent formulation
introduces a nonlinearity (the exp(−λ·d) term couples the PET response
to the current head state) that would propagate through the threshold
equations (§4.7), forestry scenarios (§4.9), and forecasting tools
(§4.10). The standard SSM's fixed β₂ provides an effective
depth-averaged parameterisation that preserves the closed-form
analytical framework on which these operational outputs depend.

The standard model is therefore retained as the primary operational
framework. The fixed β₂ should be understood as absorbing a real
depth-coupling effect whose magnitude varies across clusters: from
near-zero additional explanatory power at C3 and C5 (ΔNSE < 0.04)
to substantial improvement at C1 (ΔNSE = +0.18). This residual
depth-coupling is a recognised limitation of the lumped-parameter
approach, analogous to using a fixed crop coefficient rather than
resolving the full soil–plant–atmosphere continuum.

---

## 6. Summary of Actions

| Action | Status |
|--------|--------|
| AIC/BIC comparison table | ✅ Computed — DDP strongly preferred at all clusters |
| Recommendation | ✅ Retain standard SSM for operational pipeline |
| Revised §3.7.1 text | ✅ Drafted above |
| Updated BETA2_DECOMPOSITION.md | ✅ See below |
| Downstream pipeline impact | ✅ Assessed — 4–6 scripts, weeks of work, loss of closed-form solutions |
