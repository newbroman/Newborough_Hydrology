# Canopy Interception Treatment in the SSM Water Balance

## Context

The Newborough Warren SSM (state-space model) represents the monthly water
table response as:

    Δh(t) = β₁·P(t−1) − β₂·PET(t) − β₃·|h(t−1)|

where P is gross rainfall (mm), PET is potential evapotranspiration
(Thornthwaite, mm), and h is water table depth below pipe top (m).

Corsican pine plantation covers clusters C4 (Main Forest) and C5 (Coastal
Forest). Freeman (2008) measured canopy interception at 24% of incident
rainfall at the Newborough site.

---

## How interception enters the SSM

Thornthwaite PET quantifies the **total atmospheric energy available for
evaporation**. It does not distinguish between:

- water evaporated from intercepted rainfall on leaf surfaces,
- transpiration through stomata, or
- direct evaporation from the soil/water table surface.

All three processes consume the same atmospheric energy budget. So PET is
the total demand; the question is how that demand is **partitioned** at the
land surface.

Under forest canopy, 24% of incident rainfall is intercepted by the canopy
and re-evaporated. This interception consumes part of the available PET
energy. The remaining PET energy drives transpiration and direct
evaporation from the water table.

**Critically: interception is not additive to PET.** It is a partition of
the same energy budget. The β₂ coefficient for forest clusters implicitly
includes the interception effect because the SSM was fitted on gross
rainfall and Thornthwaite PET — both of which are measured above the
canopy. The fitted β₂ for forest clusters therefore reflects the combined
effect of interception re-evaporation plus sub-canopy evapotranspiration.

---

## Water balance bar chart treatment

The water balance bar chart (Script 16, Figure 8) decomposes the monthly
SSM head change into losses and inputs:

**Left bar (losses):**

| Component | Formula | Stacking order |
|-----------|---------|----------------|
| Gravity drainage | β₃·\|h̄\| | Bottom |
| Remaining atmospheric draw | β₂·PET − 0.24·P̄ | Middle |
| Canopy interception (C4, C5 only) | 0.24·P̄ | Top |
| **Total** | **β₂·PET + β₃·\|h̄\|** | |

For non-forest clusters (C1, C2, C3), there is no interception partition:
the full β₂·PET is shown as "atmospheric draw" and the interception band
is absent.

**Right bar (inputs):**

| Component | Formula |
|-----------|---------|
| Recharge | β₁·P̄ |

**Residual:**

The residual is the difference between total losses and recharge:

    residual = (β₂·PET + β₃·|h̄|) − β₁·P̄

- If **positive** (losses > recharge): residual is plotted on the inputs
  bar (on top of recharge), making both bars equal.
- If **negative** (recharge > losses): residual is plotted on the losses
  bar (on top of losses), making both bars equal.

Both bars are always the same height by construction.

**Key point:** The interception band is a *visual partition* of the β₂·PET
term. It does not change the total losses, the residual, or the bar
heights. It makes visible how much of the atmospheric draw in forest
clusters is attributable to canopy interception (24% of P) versus direct
evapotranspiration (the remainder).

---

## What this means for interpretation

1. **Forest β₂ is not "lower" than open-Warren β₂ because of interception.**
   Forest β₂ reflects the *total* atmospheric demand including interception.
   Comparing β₂ across clusters compares total atmospheric draw, not just
   transpiration.

2. **The interception band shows the forest canopy's hydrological cost.**
   For C4 (Main Forest), the interception band represents ~24% of mean
   monthly rainfall that is lost to re-evaporation before it can recharge
   the aquifer. This is the rainfall "tax" imposed by the canopy.

3. **Removing forest (clearfell scenario) would eliminate the interception
   band** — all of the atmospheric draw would become direct PET on the
   newly exposed surface. Whether total atmospheric draw increases or
   decreases depends on the relative magnitudes of canopy interception
   loss versus increased ground-level evaporation (wind exposure, reduced
   shading). This is the subject of the forestry scenario analysis
   (Script 21).

---

## References

- Freeman, S. (2008). *Hydrological impact of Corsican pine afforestation
  at Newborough Warren.* MSc thesis, University of Birmingham.
- Thornthwaite, C.W. (1948). *An approach toward a rational classification
  of climate.* Geographical Review, 38(1), 55–94.
- Hollingham, M. (2026). *Hydrogeological Dynamics, Behavioural Clustering
  and Management Intervention Analysis at Newborough Warren Coastal Sand
  Dune Aquifer, Wales.* Journal of Hydrology: Regional Studies.
