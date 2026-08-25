# Partition history & cluster identity

> **Provenance.** First written 2026-04-25 and held in the project's Drive store
> rather than the repository, which is why D-020 pointed at a filename that did
> not exist here. Recovered and extended 2026-08-25. The April text is preserved
> wherever it still holds; §2, §6 and §7 are new, and §5 marks a section that is
> now superseded but kept because April-era documents quote it.

This note exists because the cluster numbering has changed at least once, and
that kind of change has gotchas. Anyone working on this project — human or LLM —
should read this before touching code that is keyed on cluster ID.

## 1. Current partition (k = 5)

The authoritative source for IDs, labels and colours is `utils/config.py`. The
anchors that map Ward's raw output to these canonical IDs are in
`02_clustering.py`'s `CLUSTER_ID_ANCHORS` dict. A guard at module load asserts
the two agree.

| ID | Label | n | Anchor wells | Old-partition equivalent |
|---|---|---|---|---|
| C1 | Lake Edge | 7 | `ceh5`, `ceh11` | Old C1 (Eastern Block Lake) |
| C2 | Dune | 24 | `d10` | Old C2 (Eastern Block Mature Dune) |
| C3 | Western Residual | 21 | `nw1` | Old C3 (Western Block Mature Dune) |
| C4 | Main Forest | 9 | `ceh2` | Old C4 (Forest) |
| C5 | Coastal Forest | 5 | `ceh16`, `nw9` | Subset of Old C3 — forested wells split out |

Counts verified 2026-08-25 against
`outputs/02_clustering/02_07_cluster_membership_k5.csv`.

The block label for C1 is **"Lake Edge"** in any new prose. "Lake-buffer" and
"Eastern Block Lake" are old labels and should not appear in new code, prose or
figures.

k is fixed by the analyst rather than selected, because silhouette's peak on this
network is the trivial k = 2 split. That is stated at the partition step as a
reviewer-visible note, and the partition is defended instead by corroboration
from attributes the algorithm never saw: spatial compactness p = 0.0001,
join-count z = 18.8, per-cluster Moran's I 0.45–0.74, forest-footprint recovery
κ = 0.914.

**Separation is not recoverability.** Every independent attribute *separates* the
clusters far better than it *reconstructs* them — the forest flag gives
η² = 0.85 but ARI = 0.25. The claim is convergent corroboration, and it must not
become a claim that the attributes rebuild the partition: had easting alone
rebuilt it at ARI ≈ 1, the clustering would be geography relabelled.

## 2. The raw integers are not the canonical IDs

Ward's `fcluster` assigns integers in an order that is arbitrary and unstable
across runs. Script 02 therefore re-numbers deterministically by anchor-well
identity (`_remap_cluster_ids_by_anchor`, line 264). **The raw integers are not
thrown away** — they are written to `02_07_cluster_membership_k5.csv` in the
column `cluster_k5`, and they are not the canonical IDs:

| raw `cluster_k5` | n | canonical | label |
|---|---|---|---|
| 1 | 7 | **C1** | Lake Edge |
| 2 | 24 | **C2** | Dune |
| 3 | 9 | **C4** | Main Forest |
| 4 | 5 | **C5** | Coastal Forest |
| 5 | 21 | **C3** | Western Residual |

Two of the five integers land on a *different* physical cluster of the same
number:

> **raw 3 is the Main Forest. Canonical C3 is the Western Residual.**
> **raw 5 is the Western Residual. Canonical C5 is the Coastal Forest.**

Anyone who reads `cluster_k5` as a cluster ID gets forest wells labelled Western
Residual and open dune labelled Coastal Forest — a silent, plausible, entirely
wrong result. This is why D-020 says IDs come **only** from
`config.CLUSTER_LABELS`, never from the membership CSV's integers. It is also §4
happening inside a single run, not hypothetically across a repartition.

## 3. Dropped from the partition (old k = 6 → new k = 5)

These were small-n / physically unreliable groups in the old partition and were
dropped at the partition step. **Their names re-appear in the new partition but
refer to different physical clusters — do not conflate.**

- Old C5 (Coastal, n = 1) — dropped
- Old C6 (Lake, n = 1) — dropped (this is **NOT** the new C1 Lake Edge)

A document that says "the Coastal cluster" without a date is therefore ambiguous
between a singleton and a five-well cluster. Do not assume a rise in n reflects
wells being added; the cluster is a different object.

## 4. Identity vs integer — the gotcha

Most code keyed on cluster ID happens to transfer cleanly under the current
renumber because the integers 1–4 align with their old equivalents. But the
distinction below matters and will bite again if the partition changes:

- **Things keyed on cluster identity** (labels, colours, markers, anchor wells,
  well-to-cluster membership) — these move with the partition. When it changes,
  they stay attached to the same physical cluster and get reassigned to whatever
  new ID that cluster carries.

- **Things keyed on cluster integer** (Python dicts mapping `1`, `2`, … to
  specific yields, peak months, trend values, flood frequencies, residual
  standard errors) — these are physical inputs to downstream arithmetic. The dict
  key is just an integer; it does not follow a cluster around. There is no error,
  no exception, no visible symptom. Each entry must be checked **individually**:
  does the value still apply to whatever physical cluster now has that ID?

Convention going forward: if a dict is keyed by integer cluster ID and holds
anything other than labels / colours / markers, treat it as physical data tied to
a specific cluster. When the partition changes, walk through every such dict and
verify each entry. Do not assume. The fact that a dict "still has five keys"
proves nothing.

## 5. Specific yield — the April values, superseded

> **Superseded 2026-08-25. Kept because April-era documents quote these numbers
> and this file's job is to let someone date a figure they have found.**
>
> The April note gave two methods and instructed that the Fetter values be used
> "anywhere `SY = {...}` appears":
>
> | | C1 | C2 | C3 | C4 | C5 |
> |---|---|---|---|---|---|
> | Fetter (mass-balance) | 0.08 | 0.12 | 0.12 | 0.12 | 0.12 |
> | WTF (empirical) | 0.223 | 0.234 | 0.259 | 0.227 | not yet computed |

Two things have changed.

**D-021 made the Script 16 water balance Sy-free.** The headline ET/drainage
partition is computed from β-fluxes only, so no assumed Sy enters it. The Fetter
values survive only as the `Sy_assumed` column of
`17_wtf_01_sy_estimates.csv`, for comparison.

**The WTF estimates have all moved, and C5 is computed.** Live values, event
median, from `17_wtf_01_sy_estimates.csv`:

| | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|
| uncorrected | 0.210 | 0.267 | 0.327 | 0.312 | 0.355 |
| interception-corrected | — | — | — | 0.260 | 0.321 |

The forest clusters carry an interception correction that did not exist in April
(see `INTERCEPTION_TREATMENT.md` §4c), and it is what brings C4 inside the
open-dune range. Any figure in the April table should be treated as belonging to
a different analysis, not as a rounding difference.

## 6. ID-keyed dicts flagged in April — where they stand now

The April note listed four dicts as "committed under the old partition, needing
recomputation, NOT label-pass items". Status as of 2026-08-25:

| dict | script | status |
|---|---|---|
| `SUMMER_TRENDS` | 16 | **gone** — no longer in Script 16 |
| `FLOOD_FREQ` | 16 | **gone** — no longer in Script 16 |
| `RESIDUAL_PCT_SE` | 16 | **gone** — no longer in Script 16 |
| `CLUSTER_PEAK_MONTH` | 11, 11b | **still present** — still needs the April check |

The first three were removed rather than recomputed. D-021 records the residue:
Methods Supplement line 285 still references `SUMMER_TRENDS` / `FLOOD_FREQ`
"in Script 16", dicts that no longer exist. `CLUSTER_PEAK_MONTH` carried old
values `{C1: 1, C2: 1, C3: 2, C4: 4}`; C4 (Main Forest) maps cleanly to old C4
(Forest, peak April), and the rest still need re-deriving from the new
cluster-average hydrographs.

## 7. Superseded counts, and the blacklist that moved them

**The April-2026 counts: `C1 8 · C2 28 · C3 22`.** Superseded. A document quoting
any of those three is pre-May-2026 and its cluster-level figures belong to a
different partition.

**The v1.3.0 tidal-well blacklist.** `pdfs` was added to
`EXTENDED_NETWORK_BLACKLIST` on 2026-05-24 — a tidal-influence signature making
its hydrograph unrepresentative of water-table behaviour, the same exclusion
principle already applied to CEH3 and CEH22 in the reference whitelist and to
Llyn Rhos. Re-clustering after the exclusion **moved two wells from C2 to C3**.

CEH3 and CEH22 are excluded on the same grounds but at a different level: they
are out of the *reference* network used for clustering (Ward's identifies both as
singleton outliers resistant to grouping at every k), while remaining available
elsewhere. `pdfs` is excluded from **both** networks.

## 8. What should NOT change with the partition

*From the April text, and still current.*

- The amplitude descriptor outputs (`02_08_…per_well.csv`,
  `02_09_…summary.csv`) — derived from per-well time series with the cluster ID
  attached at the end. Renumbering changes only which cluster they are filed
  under, not the underlying numbers.
- The cluster anchors as a concept — the anchor wells stay the same; only which
  canonical ID they map to changes.
- The state-space model and BACI analysis specifications.

## 9. What is guarded, and what is not

**Guarded.** `02_clustering.py` raises at module load if `CLUSTER_ID_ANCHORS`
keys disagree with `config.CLUSTER_LABELS` keys — the failure mode where one is
updated and the other is not, which went unnoticed for an entire run cycle before
the guard was added. `_remap_cluster_ids_by_anchor` errors if an anchor is
missing or if two anchors for one canonical ID land in different raw clusters.
Downstream code reads the realised partition back through
`pipeline_params.get_cluster_ids()` rather than assuming 1–5.

**Not guarded.** Nothing checks integer-keyed dictionaries against the partition
they were written for; nothing prevents a document quoting a superseded count;
nothing stops a reader taking `cluster_k5` at face value. Those three are the
residual risk this file describes rather than removes.

## 10. Found while revising this

The head-of-file partition block in `src/02_clustering.py` (lines 146–200) gives
membership as **Dune n = 26, Western Residual n = 19**. The live output gives
**24 and 21**. Both sum to 66, so no total flags it, and the two counts are
exactly the pair the v1.3.0 blacklist moved (§7) — the comment block records the
pre-blacklist membership and was not updated when the re-clustering ran.

It is a comment, so nothing downstream reads it and no output is wrong. But it is
the first thing a reader of Script 02 meets. Registered as **T-11**.

**Revisit-if** (D-020): the blacklist changes, the extended network is folded
into the clustering input, or a rerun moves the Pearson+Ward reproduction ARI off
1.000.

---

**Sources for the 2026-08-25 revision.** `src/02_clustering.py`
(`CLUSTER_ID_ANCHORS`, `_remap_cluster_ids_by_anchor`, the partition comment
block); `src/01_data_prep.py` (`EXTENDED_NETWORK_BLACKLIST`);
`src/utils/config.py`; D-020 and D-021. Membership counts and the raw→canonical
mapping computed live from
`outputs/02_clustering/02_07_cluster_membership_k5.csv`; specific yields from
`outputs/17_wtf_specific_yield/17_wtf_01_sy_estimates.csv`. The k = 6 partition
and the April-2026 counts are recorded in D-020 and the April text only; they are
not reconstructible from the current pipeline.
