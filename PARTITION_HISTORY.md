# Cluster partition: history, renumbering, and what an old "C3" means

**The file D-020 traces to.** Its purpose is narrow and specific: to let anyone
who meets a cluster number in an old document, an old figure, or a raw output
file work out *which physical group of wells it refers to*. Three separate
things have all been called "C3" at Newborough, and two of them are still live
in the repository today. This file is the concordance.

---

## 1. The partition now

**k = 5**, analyst-fixed, on Ward's variance-minimisation over `1 − Pearson`
between detrended well hydrographs, on the 66-well reference network.

| ID | Label | n | anchor wells |
|---|---|---|---|
| C1 | Lake Edge | 7 | `ceh5`, `ceh11` |
| C2 | Dune | 24 | `d10` |
| C3 | Western Residual | 21 | `nw1` |
| C4 | Main Forest | 9 | `ceh2` |
| C5 | Coastal Forest | 5 | `ceh16`, `nw9` |

Counts verified 2026-08-25 against
`outputs/02_clustering/02_07_cluster_membership_k5.csv`.

k is fixed by the analyst rather than selected, because silhouette's peak on
this network is the trivial k = 2 split. That is not a weakness concealed — it
is stated at the partition step as a reviewer-visible note, and the partition is
defended instead by corroboration from attributes the algorithm never saw:
spatial compactness p = 0.0001, join-count z = 18.8, per-cluster Moran's I
0.45–0.74, forest-footprint recovery κ = 0.914.

**Separation is not recoverability.** Every independent attribute *separates*
the clusters far better than it *reconstructs* them — the forest flag gives
η² = 0.85 but ARI = 0.25. The claim the project makes is convergent
corroboration. It does not claim the attributes rebuild the partition, and it
must not: had easting alone rebuilt it at ARI ≈ 1, the clustering would be
geography relabelled.

## 2. The renumbering, and the collision it creates

Ward's `fcluster` assigns integers in an order that is arbitrary and unstable
across runs. Script 02 therefore re-numbers deterministically by anchor-well
identity (`_remap_cluster_ids_by_anchor`, line 264), so canonical IDs survive a
re-run. **The raw integers are not thrown away** — they are written to
`02_07_cluster_membership_k5.csv` in the column `cluster_k5`, and they are not
the canonical IDs:

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
wrong result. This is why D-020 says IDs come **only** from `config.CLUSTER_LABELS`
and never from the membership CSV's integers.

## 3. Superseded states

Three earlier states exist in documents and correspondence. None can be
regenerated from the current pipeline; what follows is the record.

### (a) The old k = 6 partition — names reused, meanings changed

The previous partition ran to six clusters, of which **old C5 (Coastal, n = 1)**
and **old C6 (Lake, n = 1)** were singletons. Both were dropped when the
partition was re-cut at k = 5. The *names* Coastal and Lake then reappeared in
the new partition **attached to different physical clusters** — today's C5
Coastal Forest is a five-well forest strip, not the old one-well Coastal
cluster; today's C1 Lake Edge is a seven-well group, not the old singleton Lake.

A document that says "the Coastal cluster" without a date is therefore ambiguous
between a singleton and a five-well cluster. **Do not conflate them, and do not
assume a rise in n reflects wells being added — the cluster is a different
object.**

### (b) The April-2026 counts

`C1 8 · C2 28 · C3 22`. These predate the v1.3.0 blacklist (§c) and are
superseded. A document quoting any of those three numbers is pre-May-2026 and
its cluster-level figures should be treated as belonging to a different
partition, not as a rounding difference from the current ones.

### (c) The v1.3.0 tidal-well blacklist

`pdfs` was added to `EXTENDED_NETWORK_BLACKLIST` on 2026-05-24 — a tidal-influence
signature making its hydrograph unrepresentative of water-table behaviour, the
same exclusion principle already applied to CEH3 and CEH22 in the reference
whitelist and to Llyn Rhos. Re-clustering after the exclusion **moved two wells
from C2 to C3**.

Note that CEH3 and CEH22 are excluded on the same grounds but at a different
level: they are out of the *reference* network used for clustering (Ward's
identifies both as singleton outliers resistant to grouping at every k, with a
tidal signature), while remaining available elsewhere. `pdfs` is excluded from
**both** networks.

## 4. The integer-versus-identity trap

This is the rule to apply whenever the partition changes.

**Things keyed on cluster *identity* follow the cluster through a repartition:**
labels, colours, anchor wells, membership lists. They are defined against the
physical group and move with it.

**Things keyed on cluster *integer* do not.** Any `dict` in the codebase keyed
`{1: …, 2: …, 3: …}` — specific yields, peak months, trend values, flood
frequencies — silently re-points to a different physical cluster if the
numbering moves. There is no error, no exception, no visible symptom. Each entry
must be re-checked **individually** after any repartition; the fact that a dict
"still has five keys" proves nothing.

§2 is the standing demonstration that this is not hypothetical: the raw and
canonical numberings differ on two of five IDs *right now*, inside the same
pipeline, in the same run.

## 5. What is guarded, and what is not

**Guarded.** `02_clustering.py` raises at module load if `CLUSTER_ID_ANCHORS`
keys disagree with `config.CLUSTER_LABELS` keys — the failure mode where one is
updated and the other is not, which went unnoticed for an entire run cycle
before the guard was added. `_remap_cluster_ids_by_anchor` errors if an anchor
is missing or if two anchors for one canonical ID land in different raw
clusters. Downstream code reads the realised partition back through
`pipeline_params.get_cluster_ids()` rather than assuming 1–5.

**Not guarded.** Nothing checks integer-keyed dictionaries against the partition
they were written for; nothing prevents a document from quoting a superseded
count; nothing stops a reader taking `cluster_k5` at face value. Those three are
the residual risk this file exists to describe rather than remove.

## 6. Found while writing this

The head-of-file partition block in `src/02_clustering.py` (lines 146–200) gives
membership as **Dune n = 26, Western Residual n = 19**. The live output gives
**24 and 21**. Both sum to 66, so no total flags it, and the two numbers are the
two the v1.3.0 blacklist moved (§3c) — the comment block records the pre-blacklist
membership and was not updated when the re-clustering ran.

It is a comment, so nothing downstream reads it, and nothing is wrong in any
output. But it is the same fault this project has now found in five registers,
and the comment block is the first thing a reader of Script 02 meets. Recommend
correcting the five counts in place and dating the block.

**Revisit-if** (from D-020): the blacklist changes, the extended network is
folded into the clustering input, or a rerun moves the Pearson+Ward reproduction
ARI off 1.000.

---

**Provenance.** Written 2026-08-25 against D-020 (`Traces to:` this file),
`src/02_clustering.py` (`CLUSTER_ID_ANCHORS`, `_remap_cluster_ids_by_anchor`,
the partition comment block), `src/01_data_prep.py`
(`EXTENDED_NETWORK_BLACKLIST`), `src/utils/config.py` (`CLUSTER_LABELS`,
`CLUSTER_COLOURS`, `CLUSTER_BOOT_SEED`). Membership counts and the raw→canonical
mapping computed live from
`outputs/02_clustering/02_07_cluster_membership_k5.csv`. The k = 6 partition and
the April-2026 counts are recorded in D-020 only; they are not reconstructible
from the current pipeline.
