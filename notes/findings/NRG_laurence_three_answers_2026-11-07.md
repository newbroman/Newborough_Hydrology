# Three of Laurence's questions, answered from committed data

**2026-11-07, Pipeline chat. Measured, not inferred. Prepared for Laurence's note.**

---

## 1. Is our Sy the specific yield of the aquifer material?

**No, and four independent lines of evidence say so.** Martin put it first:
*"what we are measuring is a different quantity and should be named differently"*.

| evidence | number |
|---|---|
| literature dune sand (Fetter), carried in the corpus as `Sy_assumed` | **0.08–0.12** |
| what we measure (WTF, event median) | **0.21–0.42** |
| same record, drainage-corrected OLS vs rapid-recharge episodes, C1 | **0.346 vs 0.180** |
| **C4 with and without the 24 % canopy interception assumption** | **0.321 → 0.256** |
| C5, the same | **0.364 → 0.316** |

The fourth row is the one that settles it. **The specific yield of sand cannot
depend on what grows above it.** That number is a property of our recharge
estimate, not of the aquifer material. The corpus already half-knows: Script 55
calls its version "apparent Sy", and the Methods Supplement says the WTF values
are *"reliable for ranking clusters but high in absolute terms"*.

**What it actually is.** Sy = R/Δh at monthly event scale: a storage RESPONSE
coefficient lumping drainable porosity with the state of the capillary fringe
(hence depth to water), concurrent drainage, and the recharge estimate fed in.

**Recommendation, not yet acted on (needs a decision, D-318).** Rename to `S_e`,
the **event storage coefficient**, glossed on first use as "apparent specific
yield in the WTF sense (Healy and Cook, 2002)", and reserve `Sy` for the material
property where a literature value is used. Scope is wider than D-316's L_E
rename: λ = √(Kb/(Sy·β₃)), Paper 1 Table 4, report Table 8, the WTF chapter,
Script 55.

**Why it also answers Laurence.** His premise is that the material is uniform.
Under the correct name that stops being a disagreement: `S_e` is not claimed to be
a material property, and its spatial variation is a statement about geometry and
depth, not about grains.

---

## 2. LiDAR vertical accuracy (T-172)

Quoted nowhere in the corpus. **Measured here instead of citing a generic
specification**, from the 81 wells carrying both a DEM elevation and a DGPS
survey (`01_well_elevations.csv`):

| statistic | value |
|---|---|
| bias (DEM − DGPS) | **+0.077 m** (the DEM reads high) |
| SD | 0.145 m |
| **RMSE** | **0.163 m** |
| within 0.15 m | 68/81 (84 %) |
| within 0.30 m | 77/81 (95 %) |
| worst | 0.710 m at CEH2 |

**Forest against open** — RMSE 0.211 vs 0.137, bias +0.127 vs +0.081. The
direction canopy penetration predicts, but **Mann–Whitney p = 0.11 on n = 14**:
suggestive, **not established**, and it must be reported that way.

**What it means.** Every depth-below-ground quantity carries about ±0.16 m. The
per-well datum sweep steps at 0.1 m — finer than the DEM's own error. And
**L_E at C1 is 0.43 m**, so the DEM error is ~38 % of that length scale; that
belongs beside the L_E result rather than buried.

---

## 3. Saturated thickness: what does *b* = 5.0 m affect?

`config.DRAWDOWN_B_M = 5.0` carries an explicit note in the code that it is an
assumption, not a measurement. It feeds three quantities, computed here at the
C3 anchor (Sy = 0.2982, β₃ = 0.06195, K = 6.0 m/day):

| b | λ = √(Kb/(Sy·β₃)) | D = Kb/Sy | timescale L_B²·Sy/(Kb), L_B = 200 m |
|---|---|---|---|
| **5 m** | **222 m** | 101 m²/day | 1.09 yr |
| 10 m | 314 m (1.41×) | 201 (2.0×) | 0.54 yr |
| 15 m | 385 m (1.73×) | 302 (3.0×) | 0.36 yr |

**λ goes only as √b**, so tripling the thickness raises the reach by 73 %. The
222 m at b = 5 m reproduces the ~220 m the corpus quotes.

**The error direction helps the published argument.** Paper 2 argues the 4.2 ha
clearfell compartment (115 m radius) is narrower than the drawdown reach, so a
thicker aquifer strengthens it rather than weakening it. **D and the propagation
timescale are linear in b** — those are where the assumption actually bites, and
a reader should be told so.
