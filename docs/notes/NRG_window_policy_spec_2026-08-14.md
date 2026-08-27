> ## Recovered 2026-08-26 — SIGNED OFF as D-002, kept as the evidence
>
> Written **2026-08-14**, never committed, recovered from `~/Downloads` under
> T-10 and kept **verbatim below**. Cited by `DECISION_LOG.md:117` and
> `DECISIONS_PUBLIC.md:68` as "full audit and evidence".
>
> **Its header says "SPEC — awaiting Martin's sign-off. No code changed." That
> is out of date: it was signed off.** The ruling is **D-002, "SSM fitting-window
> policy — the 100-month window is a comparison window, not a cap"**
> (2026-08-16, status active), and the public form is D-002 in
> `DECISIONS_PUBLIC.md`. The pipeline is not re-cut; the improvement available on
> full records is reported as a cited sensitivity rather than adopted.
>
> This document is the audit the decision rests on, which is why both logs point
> at it by name. The decision text is the ruling; this is the working.
>
> Not re-verified line by line against the current pipeline. Its numbers are
> 2026-08-14 numbers and should be treated as dated, as with every recovered
> record here.
>
> ---

# NRG — SSM Fitting-Window Policy

**Date:** 2026-08-14 · **Status:** SPEC — awaiting Martin's sign-off. No code changed.
**Settles:** Decision 3 of `HANDOVER_cowork_NRG_2026-08-14_C4_centroid_triangulation.md`
**Read against:** working copy `/home/john/projects/NRG` @ `a4cdd29` (ahead of the clone).

---

## 0. The steer, restated as a rule

> Full record where you are trying to identify a coefficient; keep the 100-month
> equal window only where a comparison needs it.

The audit below supports that rule, with one refinement the audit turned up: the
number 100 is doing **three different jobs** in the pipeline, only one of which is
the job it was designed for. Separating those three jobs is the whole fix.

---

## 1. What the audit found

### 1.1 Three roles wearing one number

| Role | Where | Verdict |
|---|---|---|
| **Admission minimum** — a well needs ≥100 months to enter the reference network | `01_data_prep.py MIN_MONTHS_THRESH = 100` | **Correct and original.** This *is* the "minimum record length, transferable to other sites" intent. Keep, untouched. |
| **Fit cap** — keep only the most recent 100 aligned months | `LCSC_DATA_LIMIT = 100`, mirrored in `model_utils`, `03`, `08`, `30`; `DATA_LIMIT = 100` in `15` | **The drift.** Never decided as a cap; inherited "to match the published analysis" / "for downstream consistency". |
| **Comparison window** — equal-length record so per-well metrics are poolable | `08_model_benchmarking.py` | **Legitimate, but only here.** |

The constant is mirrored as a per-script local in **five** modules, which also breaks
the project rule that shared constants live in `config.py` and are imported.

### 1.2 The cap always bites — the "minimum" reading is inoperative

Every one of the 66 reference wells has more than 100 aligned months:

```
full-record length across the reference network:  min 137,  median 189,  max 248
wells where window=100 truncates:                 66 of 66
```

So as written, the window never acts as a floor. It only ever throws data away —
between 37 and 148 months per well.

### 1.3 The cap is, by coincidence, a post-clearfell window

With records ending Jan/Feb 2026, the trailing 100 aligned months start
**mid-to-late 2017** (ceh2 → 2017-09, ceh20 → 2017-06, nw1 → 2017-09). The pine
clearfell is `INTERVENTION_DATE = 2017-12-01`.

Nobody chose that. The per-well coefficient table, the coefficient atlas and the
IDW surfaces are therefore all *post-clearfell-regime* estimates by accident, while
the centroid coefficients they are compared against are full-record. That is a
silent basis mismatch, and it is the same class of error as the window's origin
being lost.

### 1.4 Impact — measured, not asserted

Reproduced `03_master_data.csv` exactly from the committed inputs
(`max |β₃(window=100) − committed β₃| = 4.2e-16` across 66 wells), then refitted
every well on its full record.

**β₃ significance (p < 0.05 and β₃ > 0):**

| Cluster | wells | sig @100 | sig @full | gained | lost |
|---|---:|---:|---:|---:|---:|
| C1 Lake Edge | 7 | 7 | 7 | 0 | 0 |
| C2 Dune | 24 | 24 | 24 | 0 | 0 |
| C3 Western Residual | 21 | 21 | 21 | 0 | 0 |
| **C4 Main Forest** | 9 | **3** | **7** | **4** | 0 |
| C5 Coastal Forest | 5 | 5 | 5 | 0 | 0 |
| **Network** | 66 | 60 | 64 | 4 | 0 |

**No well loses significance, and the entire change is inside C4.** This confirms
Decision 3's claim (3 of 9 → 7 of 9) and bounds the blast radius of the narrative
change to one cluster.

**C4, per well:**

| well | n@100 | n@full | β₃@100 | p@100 | β₃@full | p@full | clearfell tier |
|---|---:|---:|---:|---:|---:|---:|---|
| nw10 | 100 | 206 | 0.0413 | 0.000 | 0.0436 | 0.000 | Forest Ctrl |
| ceh20 | 100 | 202 | 0.0278 | 0.008 | 0.0330 | 0.000 | **Edge** |
| ceh30 | 100 | 186 | 0.0230 | 0.041 | 0.0335 | 0.000 | **Edge** |
| ceh2 | 100 | 224 | 0.0176 | 0.127 | 0.0260 | 0.000 | Forest Ctrl |
| ceh33 | 100 | 185 | 0.0190 | 0.103 | 0.0292 | 0.000 | Forest Ctrl |
| Ceh32 | 100 | 184 | 0.0120 | 0.338 | 0.0210 | 0.015 | Forest Ctrl |
| ceh34 | 100 | 183 | 0.0077 | 0.323 | 0.0163 | 0.008 | Forest Ctrl |
| ceh13 | 100 | 217 | 0.0009 | 0.944 | 0.0066 | 0.388 | — |
| ceh14 | 100 | 221 | −0.0164 | 0.239 | −0.0128 | 0.144 | — |

**The four wells that gain significance are all Forest Control wells** — never
felled, a single uninterrupted forested regime across their whole record. So the
extra data is not smuggling a regime change into the C4 fit; it is exactly the
data a forest coefficient should be estimated on. The two *Edge* wells were
already significant. This is the strongest argument in the whole audit: for C4 the
full record is better **physically**, not just statistically.

**Cluster-median β₃ (what Script 17 Approach A consumes) and β₁:**

| Cluster | β₃ @100 | β₃ @full | Δ | β₁ @100 | β₁ @full | Δ |
|---|---:|---:|---:|---:|---:|---:|
| C1 Lake Edge | 0.0972 | 0.0858 | −11.8% | 5.075 | 4.616 | −9.1% |
| C2 Dune | 0.0674 | 0.0644 | −4.5% | 4.302 | 4.155 | −3.4% |
| C3 Western Residual | 0.0506 | 0.0500 | −1.2% | 3.242 | 3.295 | +1.7% |
| C4 Main Forest | 0.0176 | 0.0260 | **+47.7%** | 2.339 | 2.396 | +2.4% |
| C5 Coastal Forest | 0.0420 | 0.0485 | +15.5% | 2.207 | 2.379 | +7.8% |

Note β₃ falls slightly at the open-dune clusters and rises at the forest clusters —
consistent with the trailing window being a post-2017 slice, not with noise.

### 1.5 Two verification by-products

- **The handover's Decision 2 table reproduces exactly.** C4 centroid, full record,
  n=236: all 9 → β₃ 0.0183 (p=1.7e−3); drop CEH14 → 0.0241; drop CEH13+14 → 0.0287,
  1/β₃ = 34.9 mo, t½ = 24.2 mo, R² = 0.754.
- **New datum for the argument:** the same C4 centroid fitted on 100 months gives
  β₃ = 0.0100, **p = 0.29** — non-significant. The centroid's existing `window=None`
  is already carrying the C4 result; had centroids been capped too, C4 would have
  had no identifiable drainage at all.
- **Correction to the handover:** it states `Ceh32` is absent from
  `01_wells_clean.csv`. It is present (and fits cleanly, n=184). The membership
  count of 9 is right; the reason given for the earlier "8" is not.

---

## 2. Proposed policy

### 2.1 The rule

> **Identification fits use the full record.** Any fit whose *coefficients* are
> consumed downstream takes `window=None`.
>
> **Comparison fits use an equal window,** and only where a metric is pooled or
> ranked **across wells**. A capped fit must name `SSM_COMPARISON_WINDOW` and carry
> a one-line comment saying which comparison requires it.
>
> **Admission is separate.** The 100-month reference-network threshold is a
> record-length minimum and is unaffected by any of this.

### 2.2 Config surface

Replace the five mirrored locals with one imported constant set in `config.py`:

```python
# ── SSM fitting windows ──────────────────────────────────────────────────────
# Three distinct roles, deliberately three constants (see DECISION_LOG D-003).
REFERENCE_MIN_MONTHS  = 100   # network ADMISSION minimum (Script 01). The
                              # original "minimum record length" intent.
SSM_MIN_OBS           = 30    # minimum aligned rows for any single fit.
SSM_COMPARISON_WINDOW = 100   # equal-length window, cross-well metric
                              # comparability ONLY (Script 08 SSM-vs-TLM).
# There is NO global fit cap. Identification fits pass window=None.
```

`LCSC_DATA_LIMIT` / `DATA_LIMIT` are deleted from `model_utils.py`, `03`, `08`,
`15`, `30`. No alias is retained — a stale importer should fail loudly rather than
silently pick up a cap.

### 2.3 Site-by-site disposition

| # | Site | Feeds | Role | Proposed |
|---|---|---|---|---|
| 1 | `03 per_well_fits` (l.412) | **`03_master_data.csv`** → 19 scripts | identification | **full record** |
| 2 | `03` empirical LCSC trim (l.425–426) | `LCSC_Empirical_Percent` | identification | **full record** — and note the code contradicts its own comment three lines above, which already says "uses the full available record for each well" |
| 3 | `03` per-well datum sweep (l.1154, 1241) | `03_09_well_optimal_datums.csv`, datum figure | identification | **full record** |
| 4 | `30` per-well panel (l.221) | `30_c4_perwell.csv`, the "N of 9 non-significant" claim | identification diagnostic | **full record** (its centroid fits are already `window=None`) |
| 5 | `15_depth_dependent_pet` `DATA_LIMIT` | depth-dependent β₂ | identification; comment says "same cap as script 03" | **follow site 1 → full record** |
| 6 | `model_utils` intercept-audit helper (l.773) | Model A vs Model B per-well audit (Script 07) | comparison, cross-well | **keep equal window** → `SSM_COMPARISON_WINDOW` |
| 7 | `08_model_benchmarking` (l.164) | SSM-vs-TLM benchmark, Table 5, Figure 15/16 | comparison, cross-well | **keep equal window** → `SSM_COMPARISON_WINDOW` |

Sites 6 and 7 are Martin's SSM-vs-TLM carve-out. One nuance worth recording rather
than assuming: *within* a well, SSM and TLM see the same rows whatever the window,
so the cap is not what makes that comparison fair. What the cap buys is
**cross-well** comparability — the median NSE across 66 wells, the "SSM wins at 65
of 66" count, and the "100-month autonomous simulation" framing all assume equal
evaluation lengths. That is a real requirement, so the cap stays; it should just be
justified on those grounds in the Methods, not on "it matches Script 03".

Scripts **22** and **24** already fit on the full record, and the Methods Supplement
currently apologises for the mismatch ("the supplement's headline coefficients
remain the 100-month-window fits; Scripts 22, 23, 24 are diagnostic companions, not
revisions"). Adopting this policy **removes** that apology rather than adding one.

---

## 3. Consequences

### 3.1 Numbers that move

`03_master_data.csv` changes for all 66 wells (β₁, β₂, β₃, both LCSCs, R², n), so
every consumer of per-well coefficients re-traces:

- **Script 07** — coefficient atlas + IDW surfaces (report figures).
- **Script 08** — reads master data for context, keeps its own capped refits.
- **Scripts 09b, 09d, 11b, 18, 19, 19b, 20, 21, 31, 35, 37, 37b** — per-well β consumers.
- **Script 15** — depth-dependent β₂.
- **Script 17 Approach A only.** Approach A corrects Δh by the cluster-median β₃
  from master data, so Approach A Sy moves. **Approach B does not use β₃** — so the
  canonical Sy aggregations (C3 = 0.3255 event-median, C3 = 0.3057 per-well median),
  Paper 1 Table 4, and **λ are untouched.** Worth stating explicitly in the changelog,
  because "per-well β₃ changed" will otherwise read as "λ changed".
- **Script 26 / 26b** — EWI is built from per-well β₁/β₂/β₃, so EWI_annual and
  EWI_spring move; MSL products follow.
- **Script 30** — the per-well identifiability panel counts.
- **Script 03** — `03_09_well_optimal_datums.csv` and the per-well datum figure.

### 3.2 Documents that assert the current window

Each needs a sentence changed, not a rewrite:

- **report8 Methods** — §3.4.2, §3.4.3, and the "Summary of SSM fitting windows"
  paragraph (currently: three windows; becomes: full record for identification,
  equal window for the benchmark, 100-month admission minimum).
- **report9** — the C4 β₃ / "weakly identified" narrative, plus Table 5 and the
  Figure 15/16 captions where the 100-month framing is benchmark-specific (those
  stay correct).
- **Methods Supplement** — §S.3 (per-well fits, "the rationale ... is downstream
  consistency"), §S.7, §S.8 (incl. the "temporal-stationarity assumption"
  paragraph, which becomes the *justification* for the benchmark carve-out),
  §S.15, §S.22, §S.24.
- **Paper 1 SI methods** — the "most recent 100 aligned months" benchmark sentence
  stays true; check no identification claim leans on it.

### 3.3 Risks and how they are handled

| Risk | Handling |
|---|---|
| **Regime breaks inside a full record.** The clearfell Edge wells (ceh20, ceh30) and the scrape-footprint wells (CEH36, CEH4, CEH18, CEH21 — events 2013, 2015, 2023) span a management step change. | Both Edge wells are already significant and their β₃ rises modestly, so no headline depends on it. Recommend: state the caveat once in Methods, and keep the BACI per-well pre/post fits (§3.5.4) as the place where regime change is modelled explicitly. Flagging this is exactly the sort of thing that should be a Decision Log line rather than a silent default. |
| **Unequal epochs across wells on the coefficient maps.** Full-record fits span 137–248 months starting 2005–2012, so the IDW surfaces interpolate wells covering different periods. | Two options — (a) accept, and report `n` per well as a map layer / table column; (b) additionally run a common-calendar-window sensitivity (e.g. all wells 2011-01 onward, matching `PRE_FELL_START`) and report that the surfaces are qualitatively unchanged. Recommend (a) as the headline with (b) as a one-off check, not a permanent second product. |
| **The 3.7 m datum's supporting evidence regenerates.** The per-well datum sweep is one of the strands behind DRAINAGE_DATUM = 3.7. | Presentational, not structural: the datum now rests on the 2026-08-13 deeper-datum Darcy justification (Note S9). Re-run and report; do not re-litigate the datum. |
| **Reproducibility of published figures.** | Every changed figure gets a `regen-pending` row in the Figure ledger when that ledger is stood up; until then, list them in the changelog delta. |

---

## 4. Interaction with Decision 2 (CEH13/CEH14 exclusion)

Settling the window first, as the handover recommends, is right — and the audit
sharpens why. The C4 exclusion criterion was defined as "β₃ non-positive or
indistinguishable from zero **over the well's full record**," which under the
current code is a criterion evaluated on data the pipeline does not use. Once the
window policy lands, the criterion and the fit are on the same basis, and the
"six of nine C4 wells are non-significant" figure that made the criterion look
dangerous disappears (it becomes two of nine — exactly CEH13 and CEH14).

**Recommended order:** window policy → rerun 03 → then Decision 2's fit-only
exclusion on top. The C4 headline should be quoted once, after both.

---

## 5. Open decisions for Martin

1. **Sites 6 and 7 keep the cap — agreed?** (Recommended: yes, justified on
   cross-well comparability, not on matching Script 03.)
2. **Site 3, the per-well datum sweep** — full record, or leave capped to preserve
   the published datum figure exactly? (Recommended: full record; the datum's
   justification no longer rests on it.)
3. **Unequal epochs on the coefficient maps** — accept with `n` reported, or add
   the common-calendar-window sensitivity? (Recommended: accept + one-off check.)
4. **Deletion vs deprecation of `LCSC_DATA_LIMIT`.** (Recommended: delete; a stale
   importer should fail loudly.)
5. **Does the reference-network admission threshold stay at 100 months** now that
   it is the only surviving role for the number? (Recommended: yes, unchanged —
   changing it would move the 66-well network.)

---

## 6. Decision Log entry (draft — for `DECISION_LOG.md`)

```
### D-003  SSM fitting-window policy: full record for identification    (2026-08-14 · status: active)

- Question:  Should per-well SSM fits keep the trailing 100-month window?
- Decision:  No. Identification fits (any fit whose coefficients are consumed
             downstream) use the full record, window=None. An equal-length
             window is retained ONLY for cross-well metric comparison —
             Script 08's SSM-vs-TLM benchmark and the Script 07 intercept
             audit — via config.SSM_COMPARISON_WINDOW. The 100-month
             reference-network admission threshold is a separate constant
             (REFERENCE_MIN_MONTHS) and is unchanged.
- Rationale: 100 months was designed as a MINIMUM record length, transferable
             to other sites; it silently became an upper bound. Measured:
             all 66 reference wells exceed 100 months (min 137), so the cap
             never acted as a floor and discarded 37-148 months per well.
             The trailing window starts mid-2017, so it was accidentally a
             post-clearfell slice, on a different basis from the full-record
             centroid fits it is compared with. On full records, β₃ becomes
             significant at 64/66 wells vs 60/66; no well loses significance
             and the entire change is inside C4 (3/9 -> 7/9). The four C4
             wells that gain are all Forest Control wells — never felled, a
             single forested regime — so the added data is physically the
             right data for a forest coefficient.
- Supersedes / Retires: the global LCSC_DATA_LIMIT = 100 fit cap, mirrored in
             model_utils, 03, 08, 15, 30 (and DATA_LIMIT in 15). Do NOT
             reintroduce a global cap. The "C4 is weakly identified" framing
             is retired with it — it was largely a windowing artefact.
- Traces to: 03_master_data.csv (post-rerun), 30_c4_perwell.csv,
             08_lcsc_model_stats.csv (still capped, by design).
- Revisit-if: a future analysis needs per-well coefficients pooled or ranked
             across wells on a fit-quality metric — that needs an equal
             window and should use SSM_COMPARISON_WINDOW, not a new constant.
             Also revisit if a well acquires a regime break that the BACI
             pre/post fits do not already handle.
```

---

## 7. Verification note

Everything numeric above was computed from the committed inputs
(`01_wells_clean.csv`, `01_climate.csv`) in the working copy, replicating
`build_ssm_frame` + `fit_ssm` Model A exactly (DRAINAGE_DATUM = 3.7,
HEADLINE_LAG = 0, min_obs = 30), and validated against the committed
`03_master_data.csv` to 4×10⁻¹⁶. Nothing here is quoted from a docstring or a
prior document. Probe script and the full 66-well comparison table are attached
as `window_impact.py` / `window_impact.csv`.
