# Canopy interception treatment in the SSM water balance

> **Provenance.** First written 2026-04-25 and held in the project's Drive store
> rather than the repository, which is why `config.py` and `DECISION_LOG.md`
> D-022 both pointed at a filename that did not exist here. Recovered and
> extended 2026-08-25. The April text is preserved below wherever it still holds;
> §4–§8 are new, and §3 corrects a description that the code has since outgrown.
>
> The April document already stated the rule that §5 records being broken in
> August. That is the argument for keeping this file *in* the repository.

## 1. Context

The Newborough Warren SSM (state-space model) represents the monthly water table
response as

```
Δh(t) = β₁·P(t−1) − β₂·PET(t) − β₃·|h(t−1)|
```

where P is **gross** rainfall (mm), PET is potential evapotranspiration
(Thornthwaite, mm), and h is water table depth below pipe top (m).

Corsican pine plantation covers clusters C4 (Main Forest) and C5 (Coastal
Forest). Freeman (2008) measured canopy interception at 24 % of incident
rainfall at the Newborough site.

| | | |
|---|---|---|
| `FOREST_INTERCEPTION` | 0.24 | Freeman (2008), throughfall gauge at C5, Corsican pine |
| `FOREST_CIDS` | (4, 5) | the clusters carrying that canopy |
| `BROADLEAF_INTERCEPTION` | 0.15 | Komatsu et al. (2011), deciduous annual mean |

0.24 is a site measurement under one canopy density in one stand, not a generic
pine value. Its uncertainty is not propagated downstream; Methods Supplement
§S.12 records that omission and judges the Sy range itself the dominant term.

## 2. How interception enters the SSM

Thornthwaite PET quantifies the **total atmospheric energy available for
evaporation**. It does not distinguish between

- water evaporated from intercepted rainfall on leaf surfaces,
- transpiration through stomata, or
- direct evaporation from the soil / water table surface.

All three consume the same atmospheric energy budget. PET is the total demand;
the question is how that demand is **partitioned** at the land surface.

Under forest canopy, 24 % of incident rainfall is intercepted and re-evaporated,
consuming part of the available PET energy. The remainder drives transpiration
and direct evaporation from the water table.

**Critically: interception is not additive to PET.** It is a partition of the
same energy budget. The β₂ coefficient for forest clusters *implicitly includes*
the interception effect, because the SSM was fitted on gross rainfall and
above-canopy Thornthwaite PET — Script 03 reads `"P": climate["P_m"]` and no
interception term appears anywhere in it. The fitted β₂ at a forest cluster
therefore reflects interception re-evaporation **plus** sub-canopy
evapotranspiration.

That is D-022 in full. What the decision does not say — and what the rest of
this document exists to supply — is *which* PET, in *which* equation. Two places
in the project invoke "double-counting" to justify opposite arithmetic: Script
16's header reduces PET by I, Methods Supplement §S.12 says PET must not be
reduced. Both are right about their own equation.

## 3. The rule

> **Interception is subtracted from rainfall exactly once, and only where the
> term it would modify was not itself fitted on gross rainfall.**

The test at any new call site is one question: *does the coefficient I am about
to multiply already know about the canopy?* If Script 03 fitted it, it does.

## 4. The four arithmetics

### (a) The fitted-coefficient world — do **not** reduce P

Any use of a fitted β on a **level** — a mean, an annual field, a map of the
modelled state — must use gross P̄. The canopy is inside the coefficient: it is
why C4 and C5 return β₁ of 2.48 and 2.43 against 3.57–4.58 in the open dune.
Writing `β₁·P̄·(1 − I)` at a forest well subtracts the canopy a second time.

### (b) Scenario differences — reduce P on both sides; the level cancels

Scripts 19, 21, 09b, 09d, 19b and `utils/scraping_common.py` set
`P_eff = P·(1 − I)` at the baseline, which looks like exactly the error above.
It is not, because none of them report the level. `monthly_perturbation()`
computes

```
Δh_shift(m) = β₁·(P_scen(m) − P_base(m)) − (β₂_scen(m) − β₂_base)·PET(m)
```

— a difference. The spurious `β₁·I·P̄` sits in `P_base` and in every scenario
that retains a canopy, so it cancels. Where the scenario removes the canopy
(`P_cf = monthly_P`, gross), the difference *is* `β₁·I·P̄`, which is the
clearfell recharge gain and the thing being measured.

The same term is the defect in (a) and the signal in (b). **Levels no,
differences yes.**

### (c) The WTF estimator — reduce P, leave PET gross

Scripts 17 and 18 estimate specific yield from rising-limb events,
`Sy = R / Δh`, where R is the water that actually arrived at the water table:

```python
df["net_R_forest_corr"] = df["P_m"] * (1 - FOREST_INTERCEPTION) - df["PET"]
```

No β is involved, so nothing here knows about the canopy and the correction must
be explicit. Uncorrected, the method attributes intercepted rainfall to recharge
and inflates apparent Sy — the observed artefact exactly: raw forest medians
(C4 0.312, C5 0.355) sit at or above the open-dune range and fall inside it once
corrected (C4 0.260, C5 0.321).

**PET stays gross.** §S.12 gives the reason: Thornthwaite PET is an energy-based
atmospheric demand computed from temperature and daylength, independent of land
cover. Reducing it too would restore the gross value —
`(P − I) − (PET − I) = P − PET` — and assert the canopy has no effect on
recharge at all.

There is a second reason, and it is why §2's energy identity cannot simply be
applied here. `PET − I` is an **annual-mean** statement. At monthly resolution
over the RAF Valley record it fails outright:

| | Dec | Jan | Feb | Nov |
|---|---|---|---|---|
| PET (mm) | 18.8 | 16.9 | 18.3 | 26.8 |
| I = 0.24·P (mm) | 23.0 | 20.4 | 14.4 | 24.0 |

In December and January the identity returns a **negative** residual demand, and
in the shoulder months it leaves under 4 mm. This is the classic wet-canopy
result — evaporation from a wetted canopy is advection-driven and routinely
exceeds the Penman-family demand of the same period, let alone the Thornthwaite
estimate. The partition is a closure statement about the year, not an operation
available month by month. Scripts 17 and 18 work month by month.

**Two further points, recovered from `wtf_interception_methodology.md`
(2026-04-17) and still current.**

*The accounting has a citation.* Treating intercepted water as a
**pre-infiltration loss** rather than a component of ET follows Healy and Cook
(2002, §3.2). The 0.24·P term is water that never reached the ground and could
never have infiltrated, so it leaves the input side; the PET term on the loss
side goes on describing demand imposed on whatever water *did* reach the soil.
The two terms describe different water and must not be netted against each
other. Reducing P by interception **and** reducing PET by the evaporation of
that same intercepted water would remove the same quantity from both sides —
and that, precisely, is the double-counting to avoid.

*The correction does not simply lower Sy — it changes which events qualify.*
Event-wise, reducing the numerator lowers every individual estimate. But the
event pool is filtered to 0.01 < Sy < 0.50 on plausibility grounds, and under
gross rainfall a forest month with strongly suppressed Δh returns an
implausibly high Sy and is thrown out. The correction pulls those months back
inside the filter. So the corrected pool is *larger* than the uncorrected one —
today 63 events against 51 at C4, 51 against 36 at C5 — and the median moves by
a competition between two effects: downward from the smaller numerator, upward
from the recovered events. In April the recovery won at C4 (0.215 → 0.227);
under the current partition the numerator wins (0.312 → 0.260). Both are the
same mechanism. Which way it resolves depends on how many events sit near the
0.50 clip, which is exactly why C5 — where a majority of rising limbs are
clip-constrained — is reported as only weakly corroborative.

### (d) The Script 16 figure — two panels, two different treatments

This is where the April text has been overtaken, and the difference matters
because the two panels of one figure do different things.

**Panel (a), head-space decomposition (m/month).** As coded today: the recharge
bar is `β₁·P̄` on **gross** rainfall, and the loss bar is `β₂·PET̄` stacked with
`β₃·h̄_disp`. There is no interception band. This is case (a) above, correctly
applied.

> *April 2026, superseded.* The panel then drew interception as a **visual
> partition** of the `β₂·PET̄` band — losses stacked as drainage `β₃·|h̄|`,
> remaining atmospheric draw `β₂·PET̄ − 0.24·P̄`, and canopy interception
> `0.24·P̄` on top, with the total unchanged at `β₂·PET̄ + β₃·|h̄|`. It changed
> neither the totals, the residual, nor the bar heights; it made visible how much
> of the forest atmospheric draw was attributable to the canopy. The band is gone
> from panel (a) in the current code — `C_INTCP` now appears only in panel (b) —
> but the construction is recorded here because figures drawn before the change
> carry it, and because it is the clearest statement of what "partition, not
> addition" means when drawn rather than written.

**Panel (b), volumetric balance (mm/yr).** Interception is entered explicitly and
appears on **both** bars: it reduces the rainfall input to `P_net = P − I`, and
appears again as a loss, accounting for canopy water returning to the atmosphere
without reaching the water table. The two appearances are identical and cancel in
the net surplus. The ET/drainage split is then applied to `P_net`:

```python
et_mid    = P_net * (1 - df_mid)
drain_mid = P_net * df_mid
```

So interception is subtracted once, from the input, and the balance closes.

## 5. The trap, sprung

Between v1.34.0 and v1.35.0 the residual field in `20_spatial_figures.py`
applied `β₁·P̄·(1 − FOREST_INTERCEPTION)` at forest wells — case (a) treated as
case (c). At C4, β₁ = 2.477, so the spurious addition is `β₁·I·P̄` ≈ 0.59·P̄:
of order 44 mm/month of head at the site mean rainfall, **larger than the entire
forest-versus-open contrast the figure was drawn to display.** The figure was
legible, plausible, and wrong by more than its own signal.

The rule it broke had been written down sixteen months earlier, in §2 of this
document — which was sitting in Drive, outside the repository, unread by anyone
working in the code. The fix is recorded as DEFECT D1 at
`src/20_spatial_figures.py:549`, and the guard is a comment rather than an
assertion because there is no mechanical test: both arithmetics run, both produce
a field, and only the physics distinguishes them.

## 6. Every consumer

| script | what it does with I | case |
|---|---|---|
| 03 state-space model | nothing — fits on gross P | — |
| 07 spatial coefficients | nothing — consumes fitted β | (a) |
| 16 water balance | panel (a) gross; panel (b) `P_net = P − I`, split on `P_net` | (a), (d) |
| 17 WTF Sy | `R_eff = (1−I)·P − PET`, Approaches B and C | (c) |
| 18 WTF spatial | same correction, per well, C4/C5 | (c) |
| 19 spatial scenarios | `sI_c4`/`sI_c5` sliders; baseline `P(1−I)` | (b) |
| 19b scraping simulator | passes I to the browser model | (b) |
| 20 spatial figures | **gross P̄ in the residual field**; broadleaf drawdown scaling | (a), §7 |
| 21 forestry scenarios | `P_base`, `P_thin` (I/2), `P_bl` | (b) |
| 09b scraping propagation | `p_eff = P(1−I)` if forest | (b) |
| 09d scenario comparison | pine / thinning / broadleaf variants | (b) |
| 24b residual climatology | tests whether I is over-estimated | diagnostic |
| `utils/scraping_common.py` | shared scenario engine | (b) |

## 7. The broadleaf variant

The 2005→2025 driver-change map needs a drawdown for the restocked broadleaf
block. It is derived from the pine value rather than measured:

```
H0_BL_full = DRAWDOWN_H0_MM × (BROADLEAF_INTERCEPTION / FOREST_INTERCEPTION)
           = 150 × (0.15 / 0.24) ≈ 94 mm at full canopy
```

with only the canopy-establishment increment over the window entering the map
(`BL_CANOPY_FRACTION_2005 = 0.4` → 0.6 × 94 ≈ 56 mm at source). This is a
proportionality assumption — that steady-state drawdown scales linearly with
interception fraction, other things equal — and it is the least constrained field
on that map. The caption flags the patch as modelled and indicative.

Broadleaf phenology is carried **separately**, in β₂
(`BROADLEAF_B2_SUMMER = 1.0750`, `BROADLEAF_B2_WINTER = 0.8817`), not in the
interception fraction. `BROADLEAF_INTERCEPTION = 0.15` is a flat annual mean
approximating ~25 % leafed and ~0 % leafless, so the seasonality of the *water*
loss is smeared while the seasonality of the *energy* draw is resolved. The two
are not symmetric, and a canopy-phenology interception term is one of the
standing candidates for the C4 semi-annual residual (D-022, Revisit-if).

## 8. What this means for interpretation

*From the April text, and still current.*

1. **Forest β₂ is not comparable to open-dune β₂ as a transpiration term.**
   Forest β₂ reflects the *total* atmospheric demand including interception.
   Comparing β₂ across clusters compares total atmospheric draw, not
   transpiration.

2. **The interception term is the canopy's hydrological cost.** At C4 it is
   ~24 % of mean monthly rainfall lost to re-evaporation before it can recharge
   the aquifer — the rainfall "tax" imposed by the canopy.

3. **Clearfell removes the interception term but not the ambiguity.** All of the
   atmospheric draw becomes direct PET on the newly exposed surface. Whether
   total draw rises or falls depends on the relative magnitudes of canopy
   interception loss and increased ground-level evaporation (wind exposure,
   reduced shading). That is the subject of the forestry scenario analysis
   (Script 21), and the BACI record is the observational check on it.

## 9. Open, as of 2026-08-25

1. **Script 16's header states an identity the code does not compute.** It reads
   `ET at WT = PET − I (interception consumes PET energy)`. The code splits
   `P_net` by the drainage fraction and never evaluates `PET − I`; and as §4(c)
   shows, that identity is negative in two months of the year. A correct
   intuition written as an equation it cannot support. Registered as **T-12**.

2. **`FOREST_INTERCEPTION`'s explanatory comment is orphaned in `config.py`.**
   The block ending "See INTERCEPTION_TREATMENT.md" sits at line 207; the whole
   UKCP18 scenario block intervenes; the constant is assigned at line 228.
   Registered as **T-13**.

3. **`wtf_interception_methodology.md` is recovered** (2026-08-25) and now lives
   at `docs/notes/wtf_interception_methodology.md` (moved there 2026-08-27 in the
   root tidy; it sat beside this file until then), carrying a superseded-values
   banner: its numbers predate the
   k = 5 repartition, and its §6 "action required" — restore the correction to
   Script 17 — was discharged long ago. Its §2 and §3 are folded into §4(c) above.
   `DEFECT_NOTE_script20_residual_field_2026-08-06.md`, cited by
   `20_spatial_figures.py:564`, was **not** found in any store; §5 above is now
   the record of that defect. Both remain part of **T-10**.

---

## References

- Freeman, S. (2008). *Hydrological impact of Corsican pine afforestation at
  Newborough Warren.* MSc thesis, University of Birmingham.
- Komatsu, H., Kume, T. and Otsuki, K. (2011). *Increasing annual runoff —
  broadleaf or coniferous forests?* Hydrological Processes, 25.
- Thornthwaite, C.W. (1948). *An approach toward a rational classification of
  climate.* Geographical Review, 38(1), 55–94.
- Hollingham, M. (2026). *Hydrogeological Dynamics, Behavioural Clustering and
  Management Intervention Analysis at Newborough Warren Coastal Sand Dune
  Aquifer, Wales.* Journal of Hydrology: Regional Studies.

**Sources for the 2026-08-25 revision.** `src/utils/config.py`;
`src/03_state_space_model.py`; `src/16_water_bal.py`; `src/17_wtf_specific_yield.py`;
`src/utils/model_utils.py::monthly_perturbation`; the DEFECT D1 note at
`src/20_spatial_figures.py:549`; Methods Supplement §S.11–S.12. Coefficients from
`outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv`;
Sy from `outputs/17_wtf_specific_yield/17_wtf_01_sy_estimates.csv`; monthly
climatology from `outputs/01_climate.csv`.
