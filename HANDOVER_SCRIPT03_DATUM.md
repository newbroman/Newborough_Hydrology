> ## Recovered 2026-08-26 — IMPLEMENTED, kept as the rationale
>
> Never committed, recovered from Trash under T-10 and kept **verbatim below**.
> `src/utils/config.py:185` cites it as the justification for `DRAINAGE_DATUM`.
>
> **This was adopted and it worked.** `DRAINAGE_DATUM = 3.7` is live in
> `config.py`, and the defect the handover was written to fix is gone. Checked
> 2026-08-26 against `03_03_cluster_mechanistic_coefficients.csv`: β₃ is
> **positive in all five clusters** (C1 0.0886, C2 0.0643, C3 0.0569, C4 0.0185,
> C5 0.0449) and **significant in all five** (largest p = 0.0016, at C4). The
> handover's own acceptance condition — 3.7 m being the minimum reference depth
> at which every cluster gives a positive *and* significant β₃ — is met.
>
> Kept because `config.py` states the value but not the reasoning, and a bare
> constant with no derivation is how a datum gets "tidied" by someone who does
> not know what it is load-bearing for. The negative-β₃ problem it describes —
> a model predicting that drier wells keep getting drier — is the thing this
> constant exists to prevent.
>
> ---

# Handover — Script 03 Datum Change: Displacement from 3.7m Below Ground

**Context:** Martin Hollingham's Newborough Warren groundwater pipeline.
The water balance work (Script 16) exposed a fundamental problem with the
SSM's β₃ (storage decay / drainage) coefficient. Under the current
depth-below-surface formulation, β₃ is negative for three of five clusters
(C3, C4, C5), meaning the model predicts that drier wells keep getting
drier — the opposite of Darcy-consistent drainage. This makes the β₃ term
physically uninterpretable for the water balance decomposition.

A sensitivity analysis (conducted in the Script 16 chat) found that
reformulating the SSM to use **displacement above a reference datum 3.7m
below ground surface** resolves the sign problem: all five clusters
produce positive, statistically significant β₃ values with comparable or
improved R².

---

## The problem with the current formulation

The SSM equation is:

    Δh = β₁·P(t−1) + β₂·(−PET) + β₃·(−h_prev)

In Script 03 as currently written, h is depth below ground surface
(negative convention). The design matrix column for β₃ is `−h_prev`,
which is positive when the water table is low (deep).

**With positive β₃ (C1, C2):** dry wells recover (upward push). This is
mean-reversion / lateral inflow — physically plausible for lake-adjacent
and shallow dune clusters.

**With negative β₃ (C3, C4, C5):** dry wells keep dropping. This is
physically inconsistent with gravity drainage under Darcy's law, where
higher head should produce more outflow.

The published TFN/SSM literature (von Asmuth et al., 2002; Knotters and
Bierkens, 2000; Pastas — Collenteur et al., 2019) models **head** or
**displacement from a reference level**, not depth below surface. In that
convention, the autoregressive term represents mean-reversion toward
equilibrium, and β₃ should always be positive.

The report's own text (Section 3.4) describes β₃ as producing behaviour
where "a deeper/higher antecedent water table generates greater drainage,
tending to restore equilibrium." The negative β₃ values at C3–C5
contradict this stated physical interpretation.

---

## The solution: displacement from 3.7m below ground

Replace:

    h = depth below ground surface (negative, e.g. −1.5m)

With:

    h_disp = 3.7 + h_depth = 3.7 − |depth|

So:
- Water table at ground surface → h_disp = 3.7 m
- Water table at 1m below ground → h_disp = 2.7 m
- Water table at 3.7m below ground → h_disp = 0.0 m

**Physical interpretation:** h_disp is the height of the water table above
an effective drainage base 3.7m below ground. Higher h_disp = more head =
more drainage potential. β₃ > 0 means higher head drives faster drainage.
This is Darcy-consistent.

**Why 3.7m?** A sensitivity analysis tested uniform reference depths from
0.5m to 8.0m in 0.1m steps. At each depth, the SSM was fitted to all five
cluster centroids and evaluated on:
1. All β₃ positive (physical consistency)
2. All β₃ significant at p < 0.05
3. Mean R² across clusters
4. Sum of AIC

3.7m is the **minimum reference depth where all five clusters produce
positive AND significant β₃**. Below 3.7m, C4 (Main Forest) has
non-significant β₃. Above 3.7m, results are stable but β₃ values
decrease slowly with no further benefit.

Mean R² at 3.7m (0.729) is within 0.001 of the peak (0.730 at 2.5m).
The cost of achieving physical consistency across all clusters is
negligible.

The deepest recorded water table in the dataset is C4 at 2.49m below
ground, so 3.7m provides clearance for all observed values.

---

## Results at 3.7m datum (from sensitivity analysis)

```
Cluster              β₁        β₂        β₃      p(β₃)    R²     LCSC
C1 (Lake Edge)       0.00434   0.00148   +0.088   <0.001   0.764  23.0%
C2 (Dune)            0.00352   0.00209   +0.058   <0.001   0.775  28.4%
C3 (W. Residual)     0.00319   0.00200   +0.057   <0.001   0.808  31.3%
C4 (Main Forest)     0.00213   0.00233   +0.017   0.050    0.599  46.9%
C5 (Coastal Forest)  0.00209   0.00154   +0.041   <0.001   0.699  47.8%
```

Note: these are approximate values from the sensitivity scan at 0.1m
resolution. The definitive coefficients should come from the refitted
Script 03.

Compare with current (depth-below-surface) values:

```
Cluster              β₁        β₂        β₃      p(β₃)    R²
C1 (Lake Edge)       0.00215   0.00433   +0.223   <0.001   0.717
C2 (Dune)            0.00231   0.00359   +0.066   <0.001   0.724
C3 (W. Residual)     0.00260   0.00288   −0.024   0.129    0.747
C4 (Main Forest)     0.00238   0.00222   −0.035   0.006    0.605
C5 (Coastal Forest)  0.00182   0.00206   −0.015   0.148    0.655
```

Key changes:
- **β₃ signs flip for C3, C4, C5** — all now positive
- **R² improves for C1 (+0.05), C2 (+0.05), C3 (+0.06), C5 (+0.05)**
- **R² essentially unchanged for C4** (−0.006)
- **β₁ increases, β₂ decreases** — the properly specified β₃ is no
  longer distorting the other coefficients
- **All β₃ significant** at p < 0.05

---

## What needs changing in Script 03

### 1. The `fit_ssm()` function

Currently (line ~275 of 03_state_space_model_1_.py):

```python
X = pd.DataFrame({
    "beta_1": df["P_lag"].values,
    "beta_2": -df["PET"].values,
    "beta_3": -df["h_prev"].values,
})
```

Where `h` is the raw depth-below-surface series. Change to apply the
3.7m displacement before fitting:

```python
DRAINAGE_DATUM = 3.7  # m below ground surface

# In the data prep section, before building the design matrix:
df["h_disp"] = DRAINAGE_DATUM + df["h"]  # h is negative, so this gives 3.7 - |depth|
df["h_disp_prev"] = df["h_disp"].shift(1)
df["Delta_h"] = df["h_disp"] - df["h_disp_prev"]
# Note: Delta_h is identical whether computed from h or h_disp (the constant cancels)

X = pd.DataFrame({
    "beta_1": df["P_lag"].values,
    "beta_2": -df["PET"].values,
    "beta_3": -df["h_disp_prev"].values,
})
```

**Important:** Δh is the same regardless of datum (it's a first difference).
Only the h_prev column in the design matrix changes. So the dependent
variable y = Δh is unchanged. Only the β₃ predictor changes.

### 2. The centroid hydrograph construction

The cluster-centroid hydrographs (used for centroid SSM fits) are built
from z-score standardised, datum-corrected per-well series. The datum
correction and z-scoring should proceed as before — the 3.7m displacement
is applied **after** the centroid is computed, at the point where the
design matrix is built for the OLS fit. The centroid time series stored
in `03_regional_averages.csv` can remain in the original
depth-below-surface convention; the displacement is a modelling choice,
not a data transformation.

### 3. Per-well SSM fits

The same 3.7m displacement should be applied to per-well fits (the
`03_master_data.csv` output). Each well's h series gets 3.7 added before
building the design matrix.

### 4. Output CSVs

`03_03_cluster_mechanistic_coefficients.csv` should be regenerated with
the new β values. Add a column or header note recording the datum
(DRAINAGE_DATUM = 3.7m).

`03_master_data.csv` per-well coefficients should also be regenerated.

### 5. The docstring and report text

Update the model equation description to specify the displacement
formulation:

    Δh(t) = β₁·P(t−1) − β₂·PET(t) − β₃·h_disp(t−1)

    where h_disp = 3.7 + h_depth (displacement above drainage datum)

Add a methods note explaining:
- The choice of 3.7m as the minimum depth producing physically
  consistent β₃ across all clusters
- The sensitivity analysis that identified it
- The alignment with TFN literature convention (von Asmuth et al., 2002;
  Knotters and Bierkens, 2000)

### 6. The β₃ sign assertion

Currently Script 03 does NOT assert β₃ > 0 (line 44: "beta_3 reported
with no hard assertion"). With the displacement formulation, β₃ > 0 is
now physically expected and could be promoted to a soft assertion (warn
but don't fail) or at least documented as the expected sign.

---

## What does NOT change

- **Δh is identical** — the datum constant cancels in first differences
- **β₁ and β₂ predictor columns** are unchanged (P and −PET)
- **The lag-1 specification** — unchanged
- **Cluster assignments** — unchanged
- **The no-intercept constraint** — unchanged (Model A)
- **The Model B intercept audit** (Script 07) — the intercept α may
  change slightly because the h_prev term is different, but the audit
  methodology is the same
- **The cluster-centroid hydrograph CSVs** — can stay in depth convention;
  the displacement is applied at fit time

---

## Downstream impacts

Scripts that consume β₃ values from `03_master_data.csv` or
`03_03_cluster_mechanistic_coefficients.csv` will get different (and
physically consistent) values. The main consumers:

- **Script 16 (water balance)** — this is the motivation for the change.
  The water balance decomposition using positive β₃ values gives
  physically sensible drainage terms for all clusters. The Script 16 chat
  will handle the redesign of figures and tables once the new
  coefficients are available.

- **Script 07 (boundary intercept)** — Model B intercepts may shift.
  Worth checking but unlikely to change the qualitative conclusions.

- **Script 08 (model benchmarking)** — SSM vs TLM comparison. R² values
  change. The displacement formulation may actually strengthen the case
  for SSM over TLM since R² improves for 4/5 clusters.

- **Script 11 (forecasting thresholds)** — uses SSM coefficients for
  P_flood calculations. These will need regenerating with the new β values.

- **Script 19/20 (spatial groundwater)** — uses per-well β values for
  spatial mapping. New per-well fits needed.

- **Script 21 (forestry scenarios)** — uses β values for scenario
  modelling. New fits needed.

---

## The DRAINAGE_DATUM constant

Add to `utils/config.py`:

```python
DRAINAGE_DATUM = 3.7  # m below ground surface; SSM displacement reference
```

All scripts that apply the displacement should import from config to
ensure consistency. The sensitivity analysis supporting this value should
be documented (either in a supplementary script or in this handover).

---

## Datum sensitivity analysis (new diagnostic output)

Script 03 should include a datum sensitivity analysis as a diagnostic
output, similar to the existing lag diagnostic (03_04). This makes the
3.7m choice reproducible and auditable from the pipeline rather than
dependent on a chat transcript.

**Method:**
1. Sweep reference depths from 0.5m to 8.0m in 0.1m steps
2. At each depth, fit the centroid SSM for all 5 clusters
3. Record: β₁, β₂, β₃, p-values, R², AIC per cluster

**Output files:**
- `03_08_datum_sensitivity.csv` — full results table (ref_depth × cluster)
- `03_08_datum_sensitivity.png` — panel figure showing:
  - Top panel: β₃ vs reference depth per cluster (with p < 0.05 band)
  - Middle panel: R² vs reference depth per cluster
  - Bottom panel: mean R² and sum AIC vs reference depth
  - Vertical line at the selected datum (3.7m)

**Selection criterion (to be stated in the figure caption and methods):**
The reference datum is the minimum depth at which β₃ is positive AND
significant (p < 0.05) for all five clusters simultaneously.

The selected value (3.7m) should be stored as `DRAINAGE_DATUM` in
`utils/config.py` and imported by all scripts that use it.

If the receiving chat finds a slightly different optimum (due to any
differences in data windowing, z-score handling, etc.), the criterion
is what matters — not the exact 3.7m number. The sensitivity analysis
will show whether the optimum shifts and by how much.

---

## Validation checklist

After refitting:

1. ✅ All centroid β₃ > 0
2. ✅ All centroid β₃ significant (p < 0.05)
3. ✅ β₁ > 0 and β₂ > 0 (hard assertions — should still pass)
4. ✅ R² comparable or improved vs current
5. ✅ Iterative simulation NSE — check this hasn't degraded
6. ✅ Per-well β₃ distribution — check what fraction of individual wells
   now have positive β₃ (should increase substantially)
7. ✅ Bootstrap CIs — rerun B=1000 bootstrap with new formulation
8. ✅ Lag diagnostic — confirm lag-1 still preferred (it should be, since
   Δh is unchanged)

---

## User's working preferences

- Conversational tone, surface decisions explicitly
- **Consult before making code changes on scientific questions**
- Ship complete files, not diffs
- Flag mistakes directly
- Claude does script edits directly (not Copilot)
