> ## Recovered 2026-08-26 — live mechanism authority
>
> Never committed, recovered from Trash under T-10 and kept **verbatim below**.
> Cited by `src/09g_mechanism_diagrams.py:71` for the scrape framing, by
> `src/utils/mechanism_fig_utils.py:521` as the source of the corrected
> mechanism, and by the Methods Supplement.
>
> **This one is not a historical record — the pipeline draws its physics from
> it.** `mechanism_fig_utils.py` cites it by name for the correction that the
> phreatic surface does **not** move on excavation: the cut meets the water
> table and becomes a pool. The scrape cell of the mechanism figure is drawn to
> that description. Losing this file would have left that figure with no stated
> source for the mechanism it depicts.
>
> Its stated purpose — keeping report §5.4, the Methods Supplement, Script 20's
> spatial figures and the public-summary illustrations consistent with one
> another — is exactly the job it is still doing.
>
> **The mechanism statements are the durable part; any numbers in it are dated**
> and have not been re-checked against the current pipeline.
>
> ---

# Scraping Effects — Mechanism Reference

## Purpose

This document consolidates what is and isn't established about how dune
scraping affects the water table at Newborough Warren. It exists to keep the
main report (§5.4), the Methods Supplement, Script 20's spatial figures, and
the public-summary illustrations consistent with each other, since scraping
mechanisms have previously been described inconsistently across these
surfaces (see "Open decision" below). It is a mechanism reference, not a
numbers source — quantities here are for orientation and must still be
traced to the committed CSVs before entering any document (report, paper, or
figure caption) as a stated value.

The public-summary illustrations are qualitative and purely illustrative:
they are not held to the same numerical precision as the report. But the
*direction* and *relative* claims embedded in an illustration are still
truth claims, and this document exists so that "illustrative" doesn't become
a licence to draw a cleaner or more settled story than the evidence
supports.

---

## What scraping physically is

At CEH36 (April 2015), and at CEH18/CEH21 (October 2023), a shallow layer of
sand and vegetation was mechanically excavated to bring the ground surface
closer to the water table, restoring wet-slack conditions.

- **Excavation depth is not surveyed.** The ~0.4 m figure used at CEH36 in
  Script 20 (`_measured_ceh36_response()` → H0; depth is the *derived*,
  informed-estimate output, d_ex = H0/Sy ≈ 0.42 m) is a judgement call, not a
  field measurement, and is known to vary within and across the scraped
  area. CEH18 (0.50 m) and CEH21 (0.70 m) are committed DEM-correction
  values in `src/11b_spatial_thresholds.py`'s `SCRAPED` dict, used only to
  correct their post-2023 DEM elevation reference — treat these the same
  way: descriptive of the intervention, not inputs that mechanically
  determine the water-table response.
- **The vegetation removed at CEH36 included *Salix repens* (creeping
  willow)** — a woody, phreatophyte-like perennial, not just herbaceous
  slack vegetation — along with the organic-rich topsoil layer built up
  over the preceding decades.
- **Rejected mechanism — do not use.** Excavating a volume of sand at some
  porosity does **not** lower or raise the water table by a fraction of the
  excavation depth via a closed-system storage/porosity calculation. The
  aquifer is open and connected; the phreatic surface is set regionally, not
  by local mass balance in the pit. The pit simply refills to whatever the
  ambient water table already is. This applies both to the "excavation
  lowers the table by X% of depth" framing and to its inverse, "the observed
  rise implies the pit was Y deep" — both rest on the same invalid premise.
  Script 20 v1.10.0 already corrected this: H0 (the response) is the
  measured input; depth is the derived, non-causal, not-independently-valid
  output.

---

## Mechanisms at the scrape itself (on-site)

Three effects operate at the scraped patch, on different timescales, and
they do not all pull the same direction.

### 1. Transpiration removal (raises the table) — net sign context-dependent

Removing rooted vegetation removes a growing-season water draw. Support for
this being the dominant term specifically for the **summer minimum**:

- The vegetation removed included a genuine woody phreatophyte (*Salix
  repens*), comparable in habit to species in the water-salvage/phreatophyte
  literature (Tamarix/willow removal, US Southwest and Murray-Darling),
  where removal produces a real transpiration-loss reduction — though that
  literature also shows the effect is frequently smaller than expected, or
  eroded, where regrowth vegetation transpires an equivalent volume. Willow
  regrows fast from cut rootstock, which may explain why CEH36's initial
  gain has decayed against the climate control while the clearfell's (much
  slower-regrowing pine) has not (see "Observed decay shape" below).
- At CEH36's measured summer-minimum depth (~0.9–1.1 m below the post-scrape
  ground surface), capillary connection to the water table is probably weak
  — the capillary fringe in dune sand capable of sustaining meaningful
  evaporative flux (Gardner, 1958; Shokri & Salvucci, 2011) is typically a
  few tens of cm, not ~1 m. This narrows (does not resolve) the competing
  term below for the specific season being measured.

### 2. Bare-surface / open-water evaporation (lowers the table) — competing, season-dependent

Exposing bare sand or standing water increases direct evaporation. This is
most plausible when the scrape floor is ponded (winter/spring), less
plausible at the summer minimum specifically (see above). The broader
wetland-science literature on vegetated-marsh-ET vs. open-water evaporation
is itself an unresolved, actively-debated question (a 2011 *J. Hydrology*
review states explicitly there is no consensus) — this is not a locally
under-researched question at Newborough, it is a genuinely open one in the
field.

**Net sign, current position:** more likely than not net-positive (raises
the table) for the **summer minimum** specifically, given the above; **not
established** for the annual mean or winter signal, where ponding is
plausible and the wetland-ET debate applies more directly. Do not present
mechanism 1 as clean, settled physics in the report, the Supplement, or an
illustration.

### 3. Drainage-geometry effect (transient, on-site + near-field)

Cutting headward into the landward flank creates a new low point where the
inland head is naturally higher, steepening the gradient into the scrape
floor. Inflow is high initially and relaxes as the enhanced inflow draws the
surrounding head down and the gradient flattens — standard relief-drainage
physics (Hooghoudt, 1940; van Schilfgaarde, 1963; Freeze & Cherry, 1979),
quantified for a comparable fine-sand dune–swale setting as largely
completing within ~5 years (Gerla, 2019).

---

## Off-site effects (surrounding aquifer)

- **WMC3 (262 m from CEH36): a real, reproducible near-field signal.** The
  displacement gap against the forest control falls by ~55 mm at the 2015
  scraping and ~54 mm at the 2023 re-scraping — near-identical across two
  independent events, the signature a genuine drainage-capture effect would
  produce. This is solid evidence for mechanism 3 operating at at least this
  one location.
- **No coherent network-wide distance-decay signal beyond that.** A
  dedicated test (§4.5.5, Script 09b) across ten wells (250–780 m) found no
  distance-decay in the drainage coefficient; the observed β₃ pattern is
  attributed to pre-existing spatial gradients unrelated to scraping, and a
  diffusivity-timescale argument shows a genuine drainage front could not
  physically have reached ~570 m within the observation window regardless.
  **Do not draw or imply a smooth drawdown halo/cone radiating from the
  scrape at network scale** — the only evidenced point is WMC3; everywhere
  else is genuinely unresolved, not just unillustrated.

---

## What is actually, robustly observed at CEH36

- Monthly/annual mean: +129 mm (raw BACI vs CEH4), +137 mm (synthetic
  control), +81 mm (SSM residual, most conservative) — Pure Scraping era.
- Summer minimum: +195 mm (paired BACI vs CEH4, p = 0.004), +161 mm (vs
  climate control, p = 0.006).
- MSL5 (5-yr spring mean): sustained +50–100 mm separation from CEH4.
- **The benefit is expressed across all three metrics** — unlike the
  clearfell, whose recovery is confined to the monthly mean and does not
  reach either ecological-threshold metric (summer minimum or MSL5). This
  cross-metric pattern is itself evidence that the scrape's mechanism
  differs in kind from the clearfell's (interception/β₁ recovery, a
  rainfall-triggered, largely winter-loaded effect) — it points toward
  mechanisms 1 and/or 3 above, which have no reason to be winter-only.

## Observed decay shape

Against the climate control, the summer-minimum gap at CEH36 peaked at
~+422 mm (2017, ~2 years post-scrape) and has partially relaxed toward a
residual of ~+187 mm (−13.9 to −16.9 mm/yr depending on reference point).
Against the CEH4-paired control, there is **no decay** (+7 mm/yr, not
significant) — CEH4 sits at the seaward end of the slack and shares the
coastal-drawdown trend, so pairing cancels it out. **This decay is
currency-dependent and is reported as consistent with, not diagnostic of,
relief-drainage relaxation** — it could equally reflect vegetation
recolonisation (mechanism 1 eroding as *Salix* regrows) or genuine drainage
relaxation (mechanism 3), and the present data cannot separate the two. The
raw annual series is noisy and non-monotonic year-to-year (climate-driven),
which itself argues against reading too much shape into the decay curve.

---

## Open decision — equilibrium status (needs your call before either surface is finalised)

Two prior sessions have stated opposite things:

- **2026-07-04** (public-summary Figure 4 editing): scraping had **not** yet
  reached equilibrium, and only the forest canopy was described as
  genuinely settled.
- **2026-07-16** (scrape mechanism diagram footer): *"Equilibrium (settled)
  state, not the refill transient — the table relaxes toward this over a
  few years (cf. Gerla, 2019, ~90% within ~5 yr)."*

These can't both stand as written. Given the currency-dependence of the
observed decay (above), the more defensible position is probably closer to
the 07-04 statement — the CEH36 signal has been *sustained* through year 10
(the residual well above pre-scrape state), but whether it represents a
*settled equilibrium* versus an ongoing, confound-entangled trajectory is
not resolved by the current record. Recommend re-wording the diagram footer
along these lines unless you have a specific reason to prefer the
07-16 framing — but this is your call, not a default correction.

---

## References

- Gardner, W.R. (1958). Some steady-state solutions of the unsaturated
  moisture flow equation with application to evaporation from a water
  table. *Soil Science* 85(4), 228–232.
- Shokri, N. & Salvucci, G.D. (2011). Evaporation from porous media in the
  presence of a water table. *Vadose Zone Journal*.
- Hooghoudt, S.B. (1940). *Bijdragen tot de kennis van eenige natuurkundige
  grootheden van den grond*, No. 7.
- van Schilfgaarde, J. (1963). *Design and Theory of Tile and Ditch
  Drainage*.
- Freeze, R.A. & Cherry, J.A. (1979). *Groundwater*. Prentice-Hall.
- Gerla, P.J. (2019). [fine-sand dune–swale relaxation timescale study;
  cited in report §5.4.1 for the ~5-yr relief-drainage completion figure].
- Doody, T. et al. (2011). Potential for water salvage by removal of
  non-native woody vegetation from dryland river systems. *Hydrological
  Processes* 25, 4117–4131.
- "Wetland versus open water evaporation: an analysis and literature
  review" (2011), *Journal of Hydrology* — cited for the unresolved
  vegetated-ET-vs-open-water-evaporation debate.
- Robins, N.S., Pye, K. & Wallace, H. (2013). Dynamic coastal dune spit: the
  impact of morphological change on dune slacks at Whiteford Burrows, South
  Wales, UK. *J. Coast. Conserv.* 17(3), 473–482. [erosion-drawdown
  analogue; not scraping-specific but same width-vs-head physics].
- `INTERCEPTION_TREATMENT.md` — companion document for the forest/clearfell
  interception mechanism; explicitly *not* transferable to the scrape (no
  canopy at a bare slack).
- Report §5.4.1 (Measured Benefit and Durability), §5.4.2 (Interaction with
  the Clearfell), §4.5.2 (Paired BACI), §4.5.4 (Summer Minima), §4.5.5
  (Scraping Propagation into the Surrounding Aquifer), §5.6 (Hydrological
  Effects of the Plantation).
- Script 09a (paired BACI), 09b (propagation test), 09c (summer minima,
  equilibration stats), `src/20_spatial_figures.py` v1.10.0+ (H0 anchored on
  measured response; v1.33.0 docstring cleanup).
