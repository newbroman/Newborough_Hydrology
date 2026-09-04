> ## Reconstructed 2026-09-04 under T-10 — NOT the original dated audit
>
> The original `AUDIT_10series_PRE_FELL_START.md` (the pre-fell start-date audit
> behind *clearfell_common*) was never committed to this repository and was not
> found in any store, on disk, in the desktop trash, or in any archived project
> bundle — searched under T-10 on 2026-08-26 and again on 2026-09-04. This
> document is a **reconstruction dated 2026-09-04**, rebuilt from the surviving
> material so the live citations resolve to a real document. It is not passed off
> as the original audit.
>
> **Rebuilt from:** the *clearfell_common* v1.7.0 changelog and the
> `PRE_FELL_START` comment block in `src/utils/clearfell_common.py`, and the
> Methods Supplement §1747 paragraph, both of which state the audit's conclusion
> in full.
>
> **Cited by:** `src/utils/clearfell_common.py:502` and `:861`, the Methods
> Supplement §1747 ("The audit basis is *AUDIT_10series_PRE_FELL_START.md*"), and
> `notes/findings/DIAGNOSTIC_script21_vs_script10_summer_minima.md:185`.
>
> **Authority.** The code and the committed Methods Supplement are the authority.
> Where they differ from this reconstruction, they win.
>
> ---

# Audit — the 10-series pre-fell start date

*Reconstruction of the audit basis for the `PRE_FELL_START` migration in*
*clearfell_common v1.7.0.*

## Question

The legacy 10-series clearfell sub-scripts (10a / 10b / 10e / 10h) and the
four-zone scripts historically used **different** pre-felling BACI cutoffs. The
audit asked whether the legacy 10-series should share the four-zone
`PRE_FELL_START`, and — crucially — whether changing it would move any published
number, i.e. whether it was an **artefact fix** or a **consistency change**.

## Finding

**The migration is a consistency change, not the artefact fix.**

*clearfell_common* v1.7.0 migrated the shared `PRE_FELL_START` cutoff from
**1 July 2010 → 1 January 2011**, so the legacy 10-series shares the four-zone
scripts' pre-felling start (`PRE_FELL_START_FOURZONE`). 2011-01 is the first full
calendar year clear of the 2010 install ramp; the pre-fell window is then 83
months (Jan 2011 → Nov 2017), the default for the clearfell-suite BACI ANCOVA.

For the centroid-based scripts (10a / 10h) this is a **consistency** change: the
2010 install-ramp months were **already outside** the ANCOVA window after the
cumulative-water-balance inner-join, so moving the named cutoff does not change
what those scripts actually fit.

The **artefact fix** is a separate, coordinated change in the same v1.7.0 commit:
the **fixed-membership control centroid** in `compute_control_centroid()`. Each
control centroid is now computed only over months in which *every* roster well
has a value; a month with any roster well missing is excluded from the BACI
series. The earlier implementation took a NaN-skipping monthly mean, so the
centroid silently re-weighted whenever a control well went offline — the dominant
case being the joint outage of NW10 and CEH2 from September 2011 to September
2012, during which the Forest-control centroid was the mean of only CEH32, CEH33
and CEH34.

## Numerical effect (of the artefact fix)

The fixed-membership rule lowers the Forest × Impact annual clearfell step from
**+0.135 m to +0.120 m** as then computed (both p < 0.001) and the model R² from
0.37 to 0.27; the result remains positive and highly significant. On current
pipeline data the step is **+0.113 m (p = 0.002)** — a live figure that shifts on
rerun and must be re-traced to `10a_report_numbers.csv` before publication.

## State of the constants now

`PRE_FELL_START` and `PRE_FELL_START_FOURZONE` are now **numerically equal**
(both 2011-01-01). They are kept as two named constants for the moment; collapsing
them into one is a deliberate follow-up, because it requires re-pointing the
four-zone scripts. Consumers of CEH34 that include data before 2010-08-01 must
call `load_ceh34_hindcast_series()` so the synthetic 2010-07-01 hindcast value is
substituted in, rather than reading `wells['ceh34']` directly.
