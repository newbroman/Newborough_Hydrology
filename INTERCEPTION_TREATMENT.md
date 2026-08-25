# Forest interception: where it enters, and where it must not

**The derivation D-022 promised.** `FOREST_INTERCEPTION = 0.24` is the single
most widely consumed land-cover constant in the pipeline — thirteen scripts
import it — and it is consumed in four arithmetically different ways. Three of
those are correct. The fourth was live in the codebase for one version, produced
a figure whose headline contrast was smaller than the error inside it, and is
the reason this document exists.

D-022 states the decision in one line: interception is **a partition of the PET
energy budget, not an additive term on top of PET**. That line is true but it is
not sufficient, because it does not say *which* PET, in *which* equation. Two
places in the project invoke "double-counting" to justify opposite arithmetic —
Script 16's header reduces PET by I, Methods Supplement §S.12 says PET must not
be reduced — and both are right about their own equation. What follows is the
rule that reconciles them.

---

## 1. The constant

| | | |
|---|---|---|
| `FOREST_INTERCEPTION` | 0.24 | Freeman (2008), throughfall gauge at C5, Corsican pine (*Pinus nigra* var. *maritima*) |
| `FOREST_CIDS` | (4, 5) | the clusters carrying that canopy |
| `BROADLEAF_INTERCEPTION` | 0.15 | Komatsu et al. (2011), deciduous annual mean |

0.24 is a site measurement under one canopy density in one stand, not a generic
pine value. Its own uncertainty is not propagated anywhere downstream; §S.12
records that omission and judges the Sy range itself the dominant term.

## 2. The rule

> **Interception is subtracted from rainfall exactly once, and only where the
> term it would modify was not itself fitted on gross rainfall.**

Everything below is a consequence of that sentence. The test to apply at any new
call site is a single question: *does the coefficient I am about to multiply
already know about the canopy?* If it was fitted by Script 03, it does.

## 3. The four arithmetics

### (a) The fitted-coefficient world — do **not** reduce P

Script 03 fits the state-space model on **gross rainfall and above-canopy
Thornthwaite PET**:

```
Δh = β₁·P − β₂·PET − β₃·h_disp
```

with `"P": climate["P_m"]` — no interception term appears anywhere in Script 03.
The canopy is therefore *inside the fitted coefficients*: it is why C4 and C5
return β₁ of 2.48 and 2.43 against 3.57–4.58 in the open dune, and the
interception loss at the forest clusters is already carried in the fitted
β₂·PET̄.

Any downstream use of those β values on a **level** — a mean, an annual field, a
map of the modelled state — must use gross P̄. Writing `β₁·P̄·(1 − I)` at a
forest well subtracts the canopy a second time.

### (b) Scenario differences — reduce P on both sides; the level cancels

Scripts 19, 21, 09b, 09d, 19b and `utils/scraping_common.py` all set
`P_eff = P·(1 − I)` at the baseline, which looks like exactly the error just
described. It is not, because none of them report the level. `monthly_perturbation()`
computes

```
Δh_shift(m) = β₁·(P_scen(m) − P_base(m)) − (β₂_scen(m) − β₂_base)·PET(m)
```

— a difference. The spurious `β₁·I·P̄` sits in `P_base` and in every scenario
that retains a canopy, so it cancels. Where the scenario removes the canopy
(`P_cf = monthly_P`, gross), the difference *is* `β₁·I·P̄`, which is the
clearfell recharge gain and the thing being measured.

The same term is the defect in (a) and the signal in (b). That is the whole
distinction: **levels no, differences yes.**

### (c) The WTF estimator — reduce P, leave PET gross

Scripts 17 and 18 estimate specific yield from rising-limb events,
`Sy = R / Δh`, where R is the water that actually arrived at the water table:

```python
df["net_R_forest_corr"] = df["P_m"] * (1 - FOREST_INTERCEPTION) - df["PET"]
```

No β is involved, so nothing here knows about the canopy and the correction must
be made explicitly. Uncorrected, the method attributes intercepted rainfall to
recharge and inflates apparent Sy — which is exactly the observed artefact: the
raw forest medians (C4 0.315, C5 0.356) sit at or above the open-dune range and
fall inside it once corrected (C4 0.259, C5 0.321).

**PET stays gross**, and §S.12 gives the reason: Thornthwaite PET is an
energy-based atmospheric demand computed from temperature and daylength,
independent of land cover. Reducing it as well would restore the gross value —
`(P − I) − (PET − I) = P − PET` — and assert that the canopy has no effect on
recharge at all.

There is a second, harder reason, and it is why the energy-partition identity
cannot simply be applied here. `PET − I` is an **annual-mean** statement. At
monthly resolution over the RAF Valley record it fails outright:

| | Dec | Jan | Feb | Nov |
|---|---|---|---|---|
| PET (mm) | 18.8 | 16.9 | 18.3 | 26.8 |
| I = 0.24·P (mm) | 23.0 | 20.4 | 14.4 | 24.0 |

In December and January the identity returns a **negative** residual demand, and
in the two shoulder months it leaves under 4 mm. This is the classic wet-canopy
result — evaporation from a wetted canopy is advection-driven and routinely
exceeds the Penman-family demand of the same period, let alone the Thornthwaite
estimate — and it means the partition is a closure statement about the year, not
an operation available month by month. Scripts 17 and 18 work month by month.

### (d) The volumetric balance — subtract once, display twice

Script 16 is the one place the partition is stated as such. Interception appears
on **both** bars of Figure 11b: it reduces the rainfall input to `P_net = P − I`,
and it appears again as a loss, accounting for canopy water that returns to the
atmosphere without reaching the water table. The two appearances are identical
and cancel in the net surplus.

Crucially, the ET/drainage split is then applied to `P_net`:

```python
et_mid    = P_net * (1 - df_mid)
drain_mid = P_net * df_mid
```

So interception is subtracted once, from the input, and the balance closes.

## 4. The trap, sprung

Between v1.34.0 and v1.35.0 the residual field in `20_spatial_figures.py`
applied `β₁·P̄·(1 − FOREST_INTERCEPTION)` at forest wells — case (a) treated as
case (c). At C4, β₁ = 2.477, so the spurious addition is `β₁·I·P̄` ≈ 0.59·P̄:
of order 44 mm/month of head at the site mean rainfall, **larger than the entire
forest-versus-open contrast the figure was drawn to display**. The figure was
legible, plausible, and wrong by more than its own signal.

The fix is recorded in the code as DEFECT D1 (`src/20_spatial_figures.py:549`),
and the guard is a comment rather than an assertion because there is no
mechanical test for it: both arithmetics run, both produce a field, and only the
physics distinguishes them. That is the argument for this document.

## 5. Every consumer

| script | what it does with I | case |
|---|---|---|
| 03 state-space model | nothing — fits on gross P | — |
| 07 spatial coefficients | nothing — consumes fitted β | (a) |
| 16 water balance | `I = 0.24·P`; `P_net = P − I`; split applies to `P_net` | (d) |
| 17 WTF Sy | `R_eff = (1−I)·P − PET`, Approaches B and C | (c) |
| 18 WTF spatial | same correction, per well, C4/C5 | (c) |
| 19 spatial scenarios | `sI_c4`/`sI_c5` sliders; baseline `P(1−I)` | (b) |
| 19b scraping simulator | passes I to the browser model | (b) |
| 20 spatial figures | **gross P̄ in the residual field**; broadleaf drawdown scaling | (a), below |
| 21 forestry scenarios | `P_base`, `P_thin` (I/2), `P_bl` | (b) |
| 09b scraping propagation | `p_eff = P(1−I)` if forest | (b) |
| 09d scenario comparison | pine / thinning / broadleaf variants | (b) |
| 24b residual climatology | tests whether I is over-estimated | diagnostic |
| `utils/scraping_common.py` | shared scenario engine | (b) |

## 6. The broadleaf variant

The 2005→2025 driver-change map needs a drawdown for the restocked broadleaf
block. It is derived from the pine value rather than measured:

```
H0_BL_full = DRAWDOWN_H0_MM × (BROADLEAF_INTERCEPTION / FOREST_INTERCEPTION)
           = 150 × (0.15 / 0.24) ≈ 94 mm at full canopy
```

with only the canopy-establishment increment over the window entering the map
(`BL_CANOPY_FRACTION_2005 = 0.4` → 0.6 × 94 ≈ 56 mm at source). This is a
proportionality assumption — that steady-state drawdown scales linearly with
interception fraction, other things equal — and it is the least constrained
field on that map. The figure caption flags the patch as modelled and indicative.

Note that broadleaf phenology is carried **separately**, in β₂
(`BROADLEAF_B2_SUMMER = 1.0750`, `BROADLEAF_B2_WINTER = 0.8817`), not in the
interception fraction. `BROADLEAF_INTERCEPTION = 0.15` is a flat annual mean
approximating ~25 % leafed and ~0 % leafless; the seasonality of the *water*
loss is therefore smeared while the seasonality of the *energy* draw is
resolved. The two are not symmetric, and a canopy-phenology interception term is
one of the standing candidates for the C4 semi-annual residual (D-022,
Revisit-if).

## 7. What writing this exposed

Three things, none of which this document resolves:

1. **Script 16's header states an identity the code does not compute.** It reads
   `ET at WT = PET − I (interception consumes PET energy)`. The code splits
   `P_net` by the drainage fraction and never evaluates `PET − I`; and as §3(c)
   shows, that identity is negative in two months of the year. It is a correct
   intuition written as an equation it cannot support. Recommend rewording to
   the closure statement the code actually implements.

2. **Two more document references point at nothing.** `17_wtf_specific_yield.py`
   cites `wtf_interception_methodology.md`; `20_spatial_figures.py` cites
   `DEFECT_NOTE_script20_residual_field_2026-08-06.md`. Neither exists anywhere
   in the repository. This file was the third such reference until today. The
   substance of both is now here (§3c and §4 respectively); the citations should
   be repointed rather than the files written.

3. **`FOREST_INTERCEPTION`'s explanatory comment is orphaned in `config.py`.**
   The six-line block ending "See INTERCEPTION_TREATMENT.md" sits at line 203;
   the whole UKCP18 scenario block intervenes; the constant is assigned at line
   228. A reader arriving at the constant does not meet its justification.

---

**Provenance.** Written 2026-08-25 against D-022 (`Traces to:` this file),
`src/utils/config.py`, Methods Supplement §S.11–S.12, and the DEFECT D1 note at
`src/20_spatial_figures.py:549`. Coefficients quoted live from
`outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv`;
monthly climatology from `outputs/01_climate.csv`.

**References.** Freeman, S. (2008) *Hydrological impact of Corsican pine at
Newborough Warren.* — Komatsu, H., Kume, T. and Otsuki, K. (2011) *Increasing
annual runoff — broadleaf or coniferous forests?* Hydrological Processes 25.
