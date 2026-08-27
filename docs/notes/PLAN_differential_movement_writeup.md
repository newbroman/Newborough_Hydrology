> ## Recovered 2026-08-26 — the guard-rails are live
>
> Recovered from `~/projects/NRG_plan/` under T-10 — it was on disk, in a
> sibling directory, never in the repository — and kept **verbatim below**.
> `src/32_differential_movement.py:12` cites it for its guard-rails.
>
> **The guard-rails are the reason this file matters and they are still in
> force.** Script 32 (v1.4.0, 2026-08-22) states them in its own header: the
> output is a differential-recession field, **not** an absolute-drying map and
> **not** a management-signature map. That distinction is easy to lose when the
> figure is looked at rather than read, and this is where it is argued.
>
> The plan-of-action sequencing below (design → sign-off → build) is spent: the
> script was built. Kept for the guard-rails and the framing.
>
> ---

# Plan of action — Differential water-table movement map

*Drafted as a navigation aid. Purpose: turn the exploratory work into one coherent
report section without losing the thread. Design -> sign-off -> build discipline
throughout; no pipeline code until the method spec (Step 2) is signed off.*

---

## The spine (hold this when lost)

The Warren is drying overall (climate-driven; the ET / heat-index signal lives in
the *common* trend). **This figure answers a different question: where is the table
changing _relative to the rest of the site_, and why?** Answer: the high,
slow-draining forest mound holds its position while the fast-draining lake and
coastal edges decline — a **differential-recession** pattern set by the aquifer's
own geometry, *not* by the management interventions. The management and coastal
effects are real, but they are isolated rigorously by the BACI / ANCOVA /
coastal-gradient analyses; at the whole-site differential scale they are
subordinate to recession geometry.

## The four map families and the one claim each is allowed to make

| Family | What it shows | Claim it is licensed to make |
|---|---|---|
| 1. Cause maps (Script 20: forest, scraping, coastal, SLR, net) | What each mechanism *would* imprint, assumed magnitude x aquifer geometry | "This is the *reach* of a labelled cause" — hypothesis, NOT a detection |
| 2. Structure fields (tau, beta-atlas, residual field) | The static recession geometry of the aquifer | "This is the *structure* that governs response" |
| 3. Observed-drift map (NEW anomaly-trend) | The actual differential change over time | "This is what *observably* moved relative to the site" |
| 4. Attribution (BACI scraping/clearfell, ANCOVA, coastal gradient) | Rigorous isolation of each intervention | "This is the *attributed* effect of a named cause" |

The new map is family 3. It does not replace 1 or 2; it adds the *temporal* layer
they lack.

---

## Steps, in order

**Step 1 — Write the figure's one-sentence claim. (small; do first)**
One sentence, the licensed claim for family 3 (see spine). Everything downstream
checks back against it. Output: one sentence. *This is the anchor — start here.*

**Step 2 — Lock the method spec for the new map. (sign-off gate)**
Pin down, on one page, for your approval before any code:
- spring months; reference panel rule for the site mean; exclusions (CEH13/14,
  lake gauge, the coastal-mask rule);
- the metric: per-well slope of (well minus site-mean spring level) vs year;
- the period (2011-2025 vs full record) and why;
- the autocorrelation caveat (point estimates fine; per-well significance needs
  an AR/bootstrap correction if claimed).
Output: signed-off spec.

**Step 3 — Place it in the figure architecture and prune. (decision gate)**
Slot family 3 as the observed-drift outcome. Then the hard parsimony check: does it
overlap tau / the residual field enough to demote one of those? Decide the figure
budget so the four families reinforce rather than blur. Output: figure list with
each one's distinct job confirmed.

**Step 4 — Reframe the existing pieces (framing only, no new analysis).**
- Promote the **no-rain recession thought experiment** from footnote to the
  interpretive *lead* — it is the mechanism that explains the new map.
- Reframe the **theoretical signature maps** as labelled causes / hypotheses, not
  predictions the new map confirms.
- Add the **honest negative**: two-window differencing is confounded by
  differential recession, so attribution rests on BACI / ANCOVA / coastal gradient.
  (This sentence justifies why those methods exist — it strengthens the report.)

**Step 5 — Build the figure. (after Step 2 sign-off)**
Promote the sketch to a pipeline script: complete file, version bump, changelog
entry, upload reminder. Honour the no-hardcoded-values rule; read from upstream
CSVs.

**Step 6 — Write the section to the spine.**
Order: hypothesis (cause maps) -> structure (recession geometry) -> observed drift
(new map) -> reconciliation / attribution (BACI / ANCOVA). Deliver as
anchor-quoted FIND/REPLACE blocks for you to apply in LibreOffice.

---

## Guard-rails (the traps we already found)

- Do **not** let the reader pattern-match the new map onto the clearfell / scraping
  signatures. It is recession geometry. C5 coastal pine behaves like the *coast*,
  not the forest — that is the proof.
- Do **not** caption the new map as ET-driven. Rising ET is the *common* (removed)
  drying; the spatial pattern is recession.
- Do **not** read C4's beta_2 as an evaporation rate (degeneracy inflates it). The
  cross-site beta_2 -> movement relationship is robust *without* C4, so report the
  relationship, not the C4 magnitude.
- The map is **relative** (mean-zero): it shows contrast, not absolute metres of
  change. Say so in the caption.
