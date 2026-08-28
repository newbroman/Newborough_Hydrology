> ## Recovered 2026-08-26 — its instruction to the pipeline is live
>
> Written **2026-05-25** against HEAD `31cdc62`, never committed, recovered from
> `~/Downloads/cleanup` under T-10 and kept **verbatim below**.
> `src/10a_ancova_baci.py:560` cites it.
>
> **What the script takes from it is a standing instruction, not a number.**
> Script 10a's comment block states the position this document argued for: the
> curvature variant is not on its own proof of a dry-period canopy-buffering
> mechanism, state dependence has alternative explanations — post-felling
> non-stationary drift, the coastal-erosion gradient — and the result is to be
> reported **neutrally and as preliminary**. That instruction still governs the
> §4.6 text.
>
> **Its numbers have not been re-checked** against the current pipeline. It is
> written against a May 2026 HEAD and the coefficients have moved since; treat
> every figure in it as dated. The argument is what is being kept.
>
> ---

# Finding — canopy climate buffering: consolidated assessment for §4.6

*Diagnostic chat, 2026-05-25. Repo `main`, HEAD `31cdc62`. Consolidates the
buffering / interaction / seasonal-signature work into a single
recommendation for the §4.6 editorial pass. Science assessment — no pipeline
edits. One feature fix-brief carried at the end.*

---

## The question §4.6 was set up to answer

Did the Corsican pine canopy **buffer the water table against climate
extremes** — was the table less sensitive to climate forcing under canopy
than after the canopy was removed?

Four analyses bear on it: the clearfell ANCOVA step, the linear CWB × felling
interaction, a non-linear (curvature) extension, and the seasonal SSM
coefficient split. Their combined verdict is below.

## Headline verdict

**Buffering is not detectable as a change in the *linear* climate sensitivity
of the water table. It IS detectable as a non-linear, state-dependent effect —
the felling response is significantly larger in dry conditions than wet — but
that signal, while statistically robust, rests on a single interacted
quadratic and one felling event, so it supports a *qualified* buffering
statement, not a clean positive claim.**

This is not "no buffering." It is "no *linear* buffering; a real non-linear
state-dependence consistent with dry-period canopy buffering, reported as
preliminary." §4.6 should say exactly that.

## The evidence, in order

### 1. The clearfell step — a level effect, not a buffering effect

Forest-control ANCOVA, live `10a_report_numbers.csv`:
- Impact zone: clearfell step **+120 mm, p < 0.001**
- Edge zone: +33 mm, p = 0.19 (n.s.)

The step is the vertical offset between pre- and post-felling regression
lines at mean CWB. It answers "did felling shift the mean level" — yes — not
"did felling change climate sensitivity." It is a **level** quantity and is
not, on its own, evidence for or against buffering. It stands as the §4.6
headline regardless of the buffering question.

### 2. The linear CWB × felling interaction — null

The interaction coefficient is the difference in slope of BACI displacement
vs CWB, pre- vs post-felling — the *linear* buffering test. Forest-control:
- Impact: −0.000138, **p = 0.40** (pre slope −0.42 mm/m, post −0.56 mm/m)
- Edge: −0.000163, **p = 0.16** (pre −0.53, post −0.69)

Non-significant at both zones. On a whole-range linear slope, the pre- and
post-felling climate sensitivities are not distinguishable. Taken alone, the
linear test says: felling produced a level shift, not a sensitivity change.

### 3. The curvature term — significant, and the substantive result

A linear interaction is a blunt instrument for a hypothesis about *extremes* —
buffering could be real at the tails yet average to zero across the range. A
`CWB² × felling` term tests this directly. Fitted **inside the full ANCOVA
specification** (scraping covariate, easting × time, all headline controls
present — verified to reproduce the live headline coefficients exactly):

| | Forest Impact | Forest Edge |
|--|---------------|-------------|
| `cwb2_x_fell` | −2.75 × 10⁻⁶, **p = 0.016** | −2.22 × 10⁻⁶, **p = 0.008** |
| `cwb2_c` (pre-felling curvature) | +2.3 × 10⁻⁷, p = 0.73 (n.s.) | −3.3 × 10⁻⁷, p = 0.48 (n.s.) |
| joint F (both curvature terms) | F = 3.99, **p = 0.021** | F = 7.30, **p < 0.001** |
| ΔAIC vs linear headline | **−4.2** | **−10.7** |
| R² | 0.27 → 0.31 | 0.48 → 0.53 |

Three points make this a real result, not a fishing artefact:

- **It is specifically the interaction.** `cwb2_c` (pre-felling curvature) is
  non-significant — the pre-felling relationship is linear. Only the
  *post-felling* relationship bends. That is the exact shape a buffering
  hypothesis predicts: the canopied system tracked climate one way, the
  felled system tracks it differently, and the difference is non-linear.
- **The linear interaction collapses once curvature is admitted.**
  `cwb_x_fell` goes to p = 0.79 (Impact) and p = 0.91 (Edge) in the curvature
  model. The linear null in §2 was not measuring an absent effect — it was a
  straight line fitted through a bend, averaging to ≈ 0. This is a
  substantive point: the linear test *failed to detect* a real effect, it did
  not *establish its absence*.
- **The negative sign means the post-felling response is concave** — felling
  uplift largest at the dry (low-CWB) end. A tercile cross-check agrees: the
  post-felling shift in the driest CWB tercile is roughly double the wettest
  tercile (Impact +180 vs +109 mm; Edge +84 mm significant vs +32 mm n.s.).

### 4. The seasonal SSM split — consistent, and explains the mechanism

Winter (Nov–Apr) vs summer (May–Oct) SSM fits on cluster centroids (canonical
`fit_ssm()`, 116–125 obs per fit, β₂ significant throughout):

- The forest's distinctive signature is **suppressed recharge (low β₁)**,
  present year-round and marginally *stronger in summer*: C4 recharge gap
  below open dune −1.07 (winter), **−1.47 (summer)**.
- The forest's elevated atmospheric-draw (β₂) excess over open dune is
  **winter-concentrated** (+1.04 winter vs +0.11 summer) — the evergreen pine
  standing out against dormant open-dune vegetation.
- The universal winter > summer β₂ level (every cluster, forest and dune) is
  a table-depth capillary-decoupling effect, **not** a forest signal — it
  must not be read as one.

This reconciles the felling results: the curvature term says felling adds the
most water in dry/low-CWB states (summer), and the seasonal split shows the
forest's recharge suppression is largest in summer. Both point to the same
mechanism — **the canopy's effect on the water table was disproportionately a
dry-season recharge effect**, which is what a buffering interpretation would
predict. The felling experiment and the mechanistic model agree.

## So — is there climate buffering?

The most defensible answer for the report:

- There is **no detectable change in the linear climate sensitivity** of the
  water table after felling — the simple "slopes differ" buffering test is
  null.
- There **is** a statistically robust **non-linear, state-dependent change**:
  the post-felling water table responds to climate in a CWB-state-dependent
  way that the canopied system did not, with the felling effect concentrated
  in dry conditions. This is *consistent with* dry-period canopy buffering and
  is corroborated by the seasonal recharge-suppression pattern.
- It falls short of a clean positive buffering claim because it is one
  interacted quadratic on a single felling event at a single site, and
  "state-dependence" has alternative explanations (post-felling non-stationary
  drift, the coastal-erosion gradient) not fully excluded.

"There isn't any buffering" overstates the null. "The canopy buffered the
water table" overstates the curvature result. The report should sit between
them, explicitly.

## What §4.6 should do — recommendation

§4.6 should **not stand as is** if it currently either (a) reports only the
+120 mm step with no climate-sensitivity statement, or (b) implies the felling
lines diverge in slope (the 10a_06 figure currently implies this — see below).
A reader who sees the scatter will ask the buffering question; §4.6 should
answer it rather than leave it open.

The minimal correct §4.6 addition is three sentences:

1. **Headline unchanged:** clearfell produced a +120 mm level rise at the
   Impact zone (p < 0.001), +33 mm at Edge (n.s.) — recovered recharge after
   removal of the canopy's interception/transpiration losses.
2. **Linear sensitivity — reported as a clean null:** the CWB × felling
   interaction was tested and is non-significant at both zones — no detectable
   change in the *linear* sensitivity of the water table to climate forcing.
   (This pre-empts the "those lines look divergent" question.)
3. **Non-linear result — reported as a flagged preliminary finding:** a
   non-linear extension (CWB² × felling) is significant at both zones
   (p = 0.016 / 0.008; ΔAIC −4 / −11), indicating the felling response is
   larger in dry conditions than wet — consistent with the canopy's
   hydrological effect having been concentrated in dry periods. Reported
   neutrally, explicitly as preliminary, with the single-event caveat.

The decision Martin must make is **how prominent (3) is**:

- **Conservative (recommended):** keep +120 mm as the §4.6 headline; report
  the curvature result as a sensitivity finding in §4.6 and develop the
  buffering interpretation in §5 Discussion as a preliminary hypothesis. This
  matches the project's scientific-neutrality principle and does not re-cut
  the headline number on the strength of one quadratic term.
- **Adopt:** make the curvature model the primary climate-sensitivity result.
  Cost: the clearfell step itself moves under the curvature model (+120 → +146
  mm Impact; +33 → +50 mm Edge — the step is re-referenced when curvature is
  added), so this re-cuts the §4.6 headline and §5 would need reconciling.
  Defensible given the Edge ΔAIC of −10.7, but a bigger editorial change.

Either way, §4.6 should not be left silent on climate sensitivity.

For **§5 Discussion**: the curvature + seasonal-recharge story is the
interesting science and belongs there — "the canopy's hydrological effect
appears concentrated in dry/summer conditions via recharge suppression, which
a whole-range linear sensitivity test averages away" — explicitly flagged as
preliminary and single-event.

## The 10a_06 figure

`10a_06_climate_sensitivity.png` currently plots **free per-period `np.polyfit`
regressions** (Script 10a ~lines 744–757), not the fitted ANCOVA lines, and
has **no legend key** for the pre/post trend lines. Because the per-period
fits are unconstrained, they diverge freely and visually imply a slope change
the non-significant linear interaction does not support — the figure plots a
different model than its title. This must be fixed whichever reporting route
is chosen:
- Conservative route → plot the ANCOVA-fitted lines (effectively parallel,
  since the linear interaction is n.s.), so the gap between them *is* the
  +120 mm step; add a full legend.
- Adopt route → plot the fitted pre-felling line against the fitted
  post-felling quadratic, so the concave dry-end response is visible.
Drop the free polyfits either way, and add a complete legend.

## Feature fix-brief (route to a fix chat — NOT a defect, NOT done here)

To let §4.6 cite the curvature result from a pipeline output rather than this
diagnostic, Script 10a (`10a_ancova_baci.py`) should gain one optional model
variant: the headline ANCOVA design plus `cwb2_c` and `cwb2_x_fell`, fitted in
the full specification, emitting into `10a_report_numbers.csv` and
`10a_02_ancova_full_coefficients.csv`:
- `coeff_cwb2_x_fell` and `coeff_cwb2_c` (value, SE, p) for Forest Impact and
  Edge;
- the curvature-model R² and the ΔAIC vs the linear-interaction model.

~15–20 lines, mirroring the existing `_summer` variant block (a second
`run_ancova`-style fit on a modified design — the pattern is already in the
script). It is a *feature*, not a defect: the linear-only spec is a
legitimate model. The 10a_06 figure fix should be bundled into the same fix
chat, since the figure's correct design depends on whether the variant is
adopted as headline or reported as a sensitivity result.

Verified figures for the fix chat (full-spec curvature fit, this diagnostic):

```
Forest Impact :  cwb2_x_fell = -2.75e-6  p=0.0157   dAIC = -4.18   step 120->146 mm
Forest Edge   :  cwb2_x_fell = -2.22e-6  p=0.0082   dAIC =-10.68    step  33-> 50 mm
```

## FE/LIS wells — for completeness

The in-footprint FE/LIS wells cannot enter any buffering test: FE3/FE4/LIS1
have 2–9 pre-felling months (no estimable pre-felling slope), and FE1/FE2 have
only 29, entirely post-scraping, giving a truncated non-comparable pre-period.
No FE-inclusive interaction test, headline or robustness. §3.1.1 exclusion
reason (a) — insufficient pre-felling baseline — is decisive. §4.6 can note
this in a footnote if the buffering paragraph invites the question.

---

## Note added 2026-08-28 — the numbers have now been re-checked, and the substantive result reverses

The 2026-08-26 recovery header said *"its numbers have not been re-checked
against the current pipeline … treat every figure in it as dated."* They have
been, under T-18. The body above is **kept verbatim**; this note records what
the check found.

The 10a curvature block was refitted directly from the committed data, and the
re-fit reproduces `10a_report_numbers.csv` to every digit — including all eight
committed headline clearfell steps — so the current CSV is what the current code
and data produce. Against §3 of this document:

| | this document | committed 2026-08-28 |
|---|---|---|
| Impact `cwb2_x_fell` | −2.75 × 10⁻⁶, **p = 0.016** | −1.550678e−06, **p = 0.1705** |
| Edge `cwb2_x_fell` | −2.22 × 10⁻⁶, **p = 0.008** | −9.116139e−07, **p = 0.2806** |
| ΔAIC vs linear | −4 / −11 | **+0.63 (Impact) / −2.27 (Edge)** |
| joint F | significant at both | **p = 0.2010 / 0.0509** |
| linear CWB × felling | p = 0.40 / 0.16 | p = 0.6347 / 0.3487 |

**§3's heading — "The curvature term — significant, and the substantive result"
— no longer holds.** The interaction is negative at both zones, which is the
direction this document argues for, and significant at neither. At Impact the
curvature model is not preferred over the linear one by AIC, which is the
opposite of what ΔAIC −4 asserts. The Edge joint F at p = 0.051 is on the line.

What survives is the part the recovery header already identified as the thing
worth keeping: the **standing instruction**. Report the variant neutrally; state
dependence has alternative explanations; a linear slope is a blunt instrument for
a tail effect. That instruction is unaffected, and `src/10a_ancova_baci.py:560`
can go on citing it.

What must not survive is the claim's onward propagation. The significant version
had reached `report9` §4.6.2, `report10` §4.12 and §5, and the Methods
Supplement, where it carries an argument. Draft replacement wording for all four
is in `working/updates/T18_A3_DRAFT_2026-08-28.md`; **none of it has been
applied**, because withdrawing a finding from the defended surface is Martin's
call, not a number fix.

*Nothing above this note has been edited. — T-18, 2026-08-28.*
