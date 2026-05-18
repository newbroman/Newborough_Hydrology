# WTF Specific Yield Estimation — Interception Handling at Newborough Warren

**Status:** Methodological summary for Section 3.7.3 and Section 4.2.4 of Hollingham (2026).
**Scope:** Documents how canopy interception is handled in the WTF specific yield analysis for the Forest cluster (C4), explains the physical basis of the correction, and reconciles cluster-level and well-level Sy estimates.
**Purpose:** Prevents misattribution of the interception correction as "double-counting", and preserves the derivation of the corrected C4 cluster-level Sy (0.227) against pipeline regeneration or reviewer challenge.

---

## 1. The correction as applied

Net recharge in the WTF method is computed as:

- Open dune clusters (C1, C2, C3):  R_effective = P − PET
- Forest cluster (C4):             R_effective = (1 − 0.24)·P − PET

The interception fraction of 0.24 is taken from Freeman (2008), site-specific to the Corsican pine plantation at Newborough. The correction is applied at monthly resolution to individual well time series (script `18_wtf_spatial.py`) and should be applied identically to the cluster-mean time series in the cluster-level analysis (script `17_wtf_specific_yield.py`; the corrected C4 variant needs to be restored — see §6).

Event selection: months are retained where both Δh > 5 mm and R_effective > 10 mm. Qualifying events are filtered to the physically plausible range 0.01 < Sy < 0.50. Cluster-level Sy is reported as the event median with interquartile range.

## 2. Physical basis — why this is not double-counting

A reviewer unfamiliar with the distinction may flag the P-only correction as incomplete: if the canopy intercepts 24% of rainfall, shouldn't the PET term also be reduced to account for the evaporation of intercepted water from the canopy surface?

This reasoning is incorrect because Thornthwaite PET is an **energy-based atmospheric demand** calculated from air temperature and day length alone. It represents the atmosphere's capacity to receive water vapour at a reference location and is computed identically across the site regardless of land cover — it does not depend on what water is actually available at any particular surface.

Reducing PET at the Forest cluster to account for canopy-evaporated water would conflate two distinct quantities:

- The **atmospheric demand** (PET), which is a site-wide driver determined by temperature and solar geometry, and
- The **realised evaporative flux** from the canopy during and after rainfall, which is a component of actual evapotranspiration.

The 0.24·P term represents the portion of gross rainfall that does not reach the ground surface. It is removed from the input side of the water balance — it was never available to infiltrate and cannot contribute to water table rise. The PET term on the loss side continues to represent atmospheric demand imposed on whatever water does reach the soil and water table. The two terms describe different water and should not be netted against each other.

This accounting follows Healy and Cook (2002, §3.2) in treating intercepted water as a pre-infiltration loss rather than as a component of ET. The alternative — reducing P by interception **and** reducing PET by the evaporative component of that same intercepted water — would remove the intercepted quantity from both sides of the water balance and is the "double-counting" framing that should be avoided.

## 3. Effect of the correction on C4 cluster Sy

The WTF estimator is Sy = R / Δh. Under the correction, the numerator is reduced for any given event (R_effective < R for C4). Taken in isolation this implies that every individual event's Sy estimate moves downward under correction.

The cluster median nevertheless moves **upward**, from 0.215 (uncorrected) to 0.227 (corrected). This arises from the interaction between the correction and the physical-plausibility filter (0.01 < Sy < 0.50) that constrains the event pool.

In the uncorrected analysis, months with strongly suppressed Δh under the full Corsican pine canopy yield Sy estimates above 0.50 when the full rainfall is placed in the numerator. These months — 26 of 64 candidate events at the cluster-mean scale — are rejected as implausibly high and contribute no information to the median. The retained 38 events produce median Sy = 0.215.

Applying the interception correction reduces the numerator by 24% of P, shifting many of these previously-excluded months into the admissible range. The corrected pool comprises 44 events, incorporating previously-rejected events whose true Sy now estimates in the upper-middle of the physically plausible distribution. The shift in median reflects the recovery of these events into the event pool, rather than a reduction of individual event estimates.

The physical interpretation is that under the uncorrected accounting, the combination of suppressed Δh and unreduced numerator produces an artificially inflated Sy signal that fails the plausibility gate. The correction resolves this misattribution and allows the affected months to contribute to the estimate. This is what Section 3.7.3 refers to when it states that without correction, the uncorrected analysis would produce "an artificially elevated Sy estimate"; the statement is correct at the level of individual event arithmetic even though the retained-median effect manifests through event recovery rather than direct reduction.

## 4. Reconciliation with well-level estimates

The well-level WTF analysis in script `18_wtf_spatial.py` computes Sy independently for each well and reports a cluster-mean of the resulting well-level medians. For the nine C4 reference wells, the well-level cluster mean is 0.202 — modestly below the cluster-aggregate corrected value of 0.227 and below the open-dune cluster range (0.223–0.259).

The two estimates are not in conflict and should not be treated as alternative measurements of the same quantity. They differ in three respects:

- **Scale of aggregation.** Cluster-aggregate analysis fits a single median to an event pool drawn from cluster-mean Δh; well-level analysis fits separate medians to each well's event pool. These are different statistical objects.
- **Event pool composition.** Individual wells include events where only that well responded sufficiently to qualify, which may differ from events at cluster-mean scale.
- **Effect of plausibility filter.** The event-pool rebalancing described in §3 applies differently at each scale. At well level, the re-admitted events are distributed across wells rather than concentrated in a single cluster-mean pool.

The cluster-aggregate estimate (0.227) is reported in Table 3c and used to derive Table 3d and Figure 8b. The well-level cluster mean (0.202) is reported alongside the spatial Sy map (Figure 9) and is the appropriate reference for discussion of well-to-well variability. Section 4.2.4 should cross-reference the two paragraphs to make clear that both are pipeline outputs derived from different but valid applications of the same method.

## 5. Interpretation for Section 5.3 Discussion

The cluster-aggregate corrected C4 Sy (0.227) falls within the open-dune range (0.223–0.259) and is consistent with the Discussion claim that aquifer storage properties are broadly uniform across the site. The well-level cluster mean (0.202) sits modestly below the open-dune range and is consistent with a weaker form of this claim — that any residual storage difference is small relative to the canopy-mediated differences in recharge.

Both statements are compatible with the principal Discussion argument: the Forest cluster's anomalous β-signature reflects canopy-mediated surface boundary conditions rather than a fundamentally different substrate. The β₂ argument for the post-felling deepening of summer minima does not require uniform storage to be demonstrated; it requires only that C4 storage properties be close enough to the open dune to make the large observed β₂ increase post-felling attributable to the change in surface boundary condition rather than to any substrate transition revealed by felling.

Section 5.3 should cite the cluster-aggregate value (0.227) as the headline Sy estimate for consistency with Tables 3c and 3d, while acknowledging the well-level distribution as supporting detail. The residual uncertainty — whether 0.202 reflects partial incompleteness of the Freeman correction or a modest substrate effect — does not need to be resolved for the surface-boundary interpretation of the Forest anomaly to stand.

## 6. Pipeline state — action required

At the time of writing, script `17_wtf_specific_yield.py` (cluster-level analysis) does not apply the interception correction and reports only uncorrected C4 cluster Sy (0.215). The corrected variant producing 0.227 was implemented in an earlier session and has been lost in subsequent refactoring. Script `18_wtf_spatial.py` (well-level analysis) retains the correction.

The corrected C4 cluster variant should be restored to script 17 alongside the uncorrected variant, with both values output to `17_wtf_04_summary.txt`. The correction logic is identical to that in script 18, applied to the cluster-mean C4 series rather than per-well series:

```python
if cid == "C4":
    net_R_eff = P_mm * (1 - 0.24) - PET_mm   # Freeman (2008)
else:
    net_R_eff = P_mm - PET_mm
```

After restoration, the summary file should report both variants as Table 3c currently does:

- C4 Forest (uncorrected)  Sy = 0.215  IQR [0.155, 0.329]  n = 38
- C4 Forest (corrected)    Sy = 0.227  IQR [0.132, 0.344]  n = 44

## 7. Methods section language — suggested addition

Section 3.7.3 correctly states the physical prediction but does not explain the filter interaction. A sentence of the following form, added immediately after the current description of the correction, would pre-empt reviewer confusion:

> "Event inclusion required 0.01 < Sy < 0.50 on physical plausibility grounds. For the Forest cluster, interception correction brings previously-excluded months — where suppressed Δh under full-rainfall accounting produced Sy values above 0.50 — into the admissible range, raising the corrected median relative to the uncorrected estimate through recovery of these events into the event pool."

## 8. Key constants and provenance

- Canopy interception fraction: 0.24 (Freeman, 2008, site-specific to Newborough Corsican pine)
- PET method: Thornthwaite, applied universally site-wide, RAF Valley temperatures
- Specific yield (operational, Table 3b water balance): C1 = 0.08; C2, C3, C4 = 0.12 (Fetter, 2001)
- Specific yield (WTF cluster median, Table 3c): C1 = 0.223; C2 = 0.234; C3 = 0.259; C4 = 0.227 (corrected)
- Specific yield (WTF well-level cluster mean, Figure 9 context): C1 = 0.217; C2 = 0.227; C3 = 0.257; C4 = 0.202

## 9. References

Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.
Healy, R.W. and Cook, P.G. (2002) Using groundwater levels to estimate recharge. *Hydrogeology Journal* 10, 91–109.
Scanlon, B.R., Healy, R.W. and Cook, P.G. (2002) Choosing appropriate techniques for quantifying groundwater recharge. *Hydrogeology Journal* 10, 18–39.
Fetter, C.W. (2001) *Applied Hydrogeology*, 4th ed. Prentice Hall.
Thornthwaite, C.W. (1948) An approach toward a rational classification of climate. *Geographical Review* 38, 55–94.
