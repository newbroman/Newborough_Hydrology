> ## Recovered 2026-09-04 — kept as the record of the diagnostic brief
>
> Written for the 2026-05-27 Script-26 cluster-assignment investigation, never
> committed, recovered under T-10 from the desktop trash (deleted 2026-06-24; it
> had lived in `~/Downloads` under a name without the `_REPORT_` element) and
> kept **verbatim below**. It is a dated record and is not edited.
>
> **Why the citation dangled.** `src/26_van_willegen_msl.py:378` and `:1713` both
> point here. The file lived beside the project in Downloads and was later
> trashed; it was never in the repository. Recovered under the cited name.
>
> **Status not re-verified in this pass.** This is the diagnostic *brief* (scope
> and asks), not its resolution. Whether Script 26's per-well cluster source
> still diverges from `03_master_data.csv` was not re-checked during recovery;
> confirm against the current Script 26 before relying on the divergence
> described below.
>
> ---

# Diagnostic — Script 26 cluster reclassification

**For routing to the chat that designed the Script 19 v2.8.0 ΔMSL5 viewer
row and the Script 26b v1.1.0 per-well aggregation pathway.**

**Scope.** Diagnostic only — produce findings, no code edits. Identify
why Script 26's per-cluster output assigns wells to clusters
differently from the canonical SSM cluster assignment in
`03_master_data.csv`, and report which cluster definition is in use
and why. Recommend any corrective action only after the cause is
known.

---

## Issue

Surfaced 2026-05-27 while drafting the report's §4.8.4 MSL5 sub-section
against the per-well outputs of Script 26.

**Symptom.** The C5 (Coastal Forest) cluster contains **5 wells** in
`03_master_data.csv` (the canonical SSM-fitted cluster assignment used
throughout the report's §4.2, §4.6 and §4.9 framing) — namely
`nw9`, `ceh16`, `ceh17`, `ceh19`, `ceh31`. But `26_msl_5yr_latest_per_well.csv`
assigns **26 wells** to cluster_id = 5 (cluster_label = "C5 (Coastal
Forest)"), and these 26 wells do **not** include the five canonical C5
wells.

Worse: the Script 26 C5 list includes wells the rest of the report
places elsewhere:

- **WMC3** — the clearfell-Impact well, classified throughout §4.6 / §5.5
  as **C4 Main Forest** (the impact tier of the BACI design). Script 26
  has it in C5.
- **CEH4** — the un-manipulated control for the dune-scraping analysis
  in §4.5, classified as **C3 Western Residual**. Script 26 has it in C5.
- **CEH9** — a Climate-control reference well, classified per the BACI
  network as C4-or-C3 (Climate-control wells are not in C5 per the
  canonical scheme). Script 26 has it in C5.

This is not a benign extension to a wider classified network. The
report's §4.7 / §4.9 framing of "88-well classified network" applies a
**Pearson-affinity extension** of the canonical SSM clusters; under
that extension, wells retain their SSM cluster assignment and any
extended-network wells are added by Pearson affinity (Section 3.3).
The Script 26 assignment appears to do something different — it puts
wells like WMC3, classified canonically as C4 Main Forest, into "C5
Coastal Forest." That contradicts the report's existing cluster
framework, which has been verified across §3, §4, §5, §6 and §7 and is
canonical.

The misalignment was not caught earlier because:

1. The report's §4.7 / §4.9 framing uses cluster counts that look right
   on aggregate (e.g. "88 wells classified") without inspecting Script
   26's per-cluster well lists.
2. Script 26's run-transcript reports C5 = 26 wells, which read as
   plausible (an extended C5) without comparison to the canonical SSM
   list.
3. The Script 19 v2.8.0 viewer ΔMSL5 row and the Script 26b v1.1.0
   per-well pathway were built on this Script 26 cluster assignment as
   given, without it being noted that the assignment diverges from
   `03_master_data.csv`.

---

## Background — the report's canonical cluster framework

The canonical cluster assignment lives in `03_master_data.csv`
(written by Script 03) and contains the 66-well reference network only.
Cluster sizes: C1 = 7, C2 = 24, C3 = 21, C4 = 9, C5 = 5. The cluster IDs
and well memberships are referenced throughout the report and the
Methods Supplement; any divergence in another script is an inconsistency,
not an extension.

For analyses that operate on the wider 88-well classified network
(reference + extended), Scripts 05 and 06 apply Pearson-affinity
extension — each extended well is assigned to the SSM cluster whose
centroid hydrograph it correlates with most strongly. Under this
extension, the canonical reference wells retain their SSM assignment;
the extended wells are added.

So the question is: what cluster assignment does Script 26 use, and why
does it differ from `03_master_data.csv` for canonical reference wells?

---

## Diagnostic asks

1. **What cluster source does Script 26 read?** Trace the cluster_id /
   cluster_label assignment in `26_msl_5yr_latest_per_well.csv`,
   `26_msl_5yr_per_well.csv`, `26_msl_5yr_per_cluster.csv` and
   `26_msl_5yr_per_cluster_centroid.csv` back to whichever file or
   logic Script 26 uses to assign wells to clusters. Is it
   `03_master_data.csv`? An intermediate clustering file? A
   spatial/geographic zone definition independent of the SSM clusters?
   A stale cluster assignment from a pre-v2.8.0 iteration?

2. **Is the misalignment systematic or partial?** Does Script 26
   misclassify only a few wells, or is its entire C5 a different
   spatial/conceptual entity from the canonical C5? Inspect every
   cluster's wells, not just C5, and report the divergence per cluster.

3. **Where else does the Script 26 cluster assignment feed?** The
   v1.1.0 per-well pathway (`26b_msl5_ukcp18_projection_summary_perwell.csv`)
   and the Script 19 v2.8.0 viewer ΔMSL5 row both rest on the Script 26
   per-well outputs. If Script 26's cluster assignment is wrong (i.e.
   differs from canonical), both downstream products carry the same
   error. Document which downstream artefacts are affected and how.

4. **Is the divergence deliberate?** The Methods Supplement's new
   §S.18b.3.8 paragraph (which documents the v1.1.0 per-well pathway)
   does not mention the cluster reassignment, so it appears not to be
   deliberate. But there are legitimate reasons a script might reassign
   wells to a different cluster scheme — for example, the van Willegen
   2025 reference framework may use geographic-zone clustering rather
   than SSM-based Pearson clustering, in which case Script 26's
   alternative scheme is correct *for its purpose* but the difference
   must be documented. Determine which it is.

---

## What to deliver

A diagnostic report covering:

- Source of Script 26's cluster assignment (file path, code line, or
  derivation rule).
- Comparison of Script 26's cluster assignment against
  `03_master_data.csv` for every well in the canonical 66-well reference
  network — which wells diverge, and to which cluster.
- Per-cluster comparison of canonical-vs-Script-26 cluster sizes, with
  the canonical SSM cluster as the reference and the Script 26 cluster
  as the deviation.
- An assessment of whether the divergence is intentional (legitimate
  van Willegen / MSL5-framework reclassification documented somewhere)
  or accidental (stale file, mis-keyed dictionary, etc.).
- Recommendation for corrective action:
  - **If accidental**, point to the fix: change Script 26's cluster
    source to `03_master_data.csv` (or the Pearson-extended canonical
    set for the wider network), and regenerate the per-well, per-cluster
    and per-cluster-centroid CSVs plus the trajectory and map figures.
  - **If intentional**, document the divergence explicitly in
    §S.18b.3.8 (or wherever appropriate in the Methods Supplement) so
    that the report's §4.8.4 cluster-mean MSL5 figures can be
    unambiguously attributed to whichever scheme is in use, and so the
    Script 19 viewer ΔMSL5 row is interpretable against the same scheme.

---

## Affected downstream artefacts

Pending the diagnostic outcome, the following may need regeneration or
re-labelling:

- `26_msl_5yr_per_cluster.csv` (Script 26 cluster aggregation)
- `26_msl_5yr_per_cluster_centroid.csv` (Script 26 centroid-fitted)
- `26b_msl5_ukcp18_projection_summary.csv` (Script 26b centroid pathway)
- `26b_msl5_ukcp18_projection_summary_perwell.csv` (Script 26b v1.1.0
  per-well pathway)
- `fig_msl5_trajectory_report.png` / `26_msl_5yr_trajectory.png`
  (cluster trajectories)
- Script 19 v2.8.0 viewer ΔMSL5 row (if it sources cluster identity
  from Script 26 rather than from `03_master_data.csv`)

The §4.8.4 main-report sub-section, currently being drafted in a
separate chat, is paused on this issue. C5 in the §4.8.4 prose must
align with C5 in §4.2 / §4.6 / §4.9 of the report — five reference-
network wells (nw9, ceh16, ceh17, ceh19, ceh31) — and the §4.8.4
trajectory figure (Script 26c output) must reflect the same canonical
cluster assignment. If Script 26 currently uses a different scheme, it
needs reconciling before §4.8.4 can be finalised.

---

## Out of scope for this diagnostic

- Any change to the report's §4.8.4 prose, the Script 26c figure
  script, or the Methods Supplement §S.18c sub-section — these are
  being handled in a separate chat once the diagnostic outcome is in.
- Any change to the canonical SSM cluster assignment in
  `03_master_data.csv` — that is the source of truth and is not to be
  modified.
- Any analysis re-run unless the diagnostic concludes that a fix is
  required.
