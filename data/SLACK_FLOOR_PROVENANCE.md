# `slack_floor_wells.csv` — which dipwells stand on a slack floor, as field knowledge

**This file is an observation, not a measurement, and it is NOT a floor datum.** D-321 fixes what
it may and may not be used for. Read that entry before using it for anything.

## Why it exists

D-294 moved the community comparison from cluster means to single wells, and D-295 then had to ask
which wells stand on a slack floor. D-296 (2026-11-02) stopped that line of work on Martin's
ruling — *"we can't do MSL analysis properly, not without a proper DGPS survey, which is outside
the remit of our study"* — and retired D-295, which had been drafted and never shipped.

On 2026-11-09 Martin said he can state which wells stand on a slack floor, and asked the question
that had stalled the work: *"what counts as the slack floor — if its 20cm above is that the floor
or are we counting only the lowest point."*

**The arithmetic says why that question cannot be settled by eye.** Curreli's SD15b and SD16 sit
0.61 and 0.98 m below ground (0.64 / 0.96 on the Dune Managers Handbook's levels; D-242,
`outputs/11b_spatial_thresholds/11b_report_numbers.csv`). The band that separates the wet-slack
class from the dry-slack class is therefore **37 cm**, or 32 cm. A 20 cm uncertainty in what counts
as the floor consumes more than half of it — which is why D-296's `Revisit-if` asks for the floor
surveyed *"to better than about 0.1 m"*.

So the membership is recorded as what it is — field knowledge, useful for several things that need
no 0.1 m — and the elevation question stays where D-296 left it. The route to an elevation without
a DGPS campaign is **D-159**'s waterline-as-contour from the dated frames, which has been deferred
to a person since 2026-09-11 and whose rationale removes the definitional question outright:
*"no assumption about where a floor sits relative to anything."*

## What it may be used for

- scoping the DGPS survey of the slack floor that **D-296 rule (2)** already recommends: which wells
  it would have to visit;
- saying which wells the **van Willegen** quadrat check applies to (the quadrats are surveyed to
  quadrat ground; the check is only meaningful where a well stands on the same surface);
- qualifying a statement about slack wetness as being about slacks rather than ridges.

## What it may NOT be used for

- as a ground or floor **elevation**, or any substitute for one;
- to reinstate the comparison against SD15b / SD16, or any MSL comparison D-296 stopped;
- as a pipeline input. **Nothing in `src/` reads this file**, deliberately. The per-well pipeline
  table is `data/well_metadata.csv`, which six scripts read and `input_provenance_lint` hashes; a
  column added there would put every level-derived output into "produced from an input that has
  since changed" and demand a full re-run for an attribute no script computes with.

## The columns

| column | meaning |
|---|---|
| `well` | the `Name` in `data/well_metadata.csv` |
| `cluster` | `Cluster_Label` from `outputs/02_cluster_stats.csv`, blank where the well is not in the 66-well reference network |
| `dist_coast_m`, `ground_source` | copied from `well_metadata.csv` as an aid to placing the well; not authoritative here |
| `slack_floor` | `yes`, `marginal`, `no` or `unknown` |
| `source` | who says so — `martin` for field knowledge, or the file or survey it came from |
| `dated` | when that was recorded, `YYYY-MM-DD` |
| `note` | anything that qualifies the call |

**`marginal` exists because of Martin's own question.** A well sitting a little above the lowest
point of a slack is the case that has no good binary answer, and recording it as `yes` or `no`
would be inventing precision. `marginal` says: in a slack, not on its floor.

**`unknown` is a real value, not a gap to be tidied away.** Every row was seeded `unknown`.

## How it was made, and its scope

Seeded 2026-11-09 by chat 'Gates review' from `data/well_metadata.csv` (99 wells, the modern network
— those with coordinates and a ground elevation, i.e. the wells a DGPS survey would visit) joined to
`outputs/02_cluster_stats.csv` for the cluster label. **Hand-maintained from then on: it is not
regenerated**, because regenerating it would wipe the answers.

**Scope limit, and it needs Martin's word.** Twenty-one wells in the clustered reference network are
not in `well_metadata.csv` at all and are not resolvable by alias — `ceh32`, `d5`–`d10`, `d15`,
`d17`, `d25`, `d38`, `d41`, `d43`, `d44`, `l7`, `t41a`–`t41d`, `wmc1`, `wmc2` — the historic CCW and
Forestry series that live in `data/fc_wells_1989_95_locations.csv` and the `ccw_*` tables. They are
**not** in this file. Whether the question is worth asking of them is Martin's call: most are
defunct and several have no coordinates, so a DGPS survey could not visit them.

**A trap for the next reader.** `outputs/02_clustering/02_07_cluster_membership_k5.csv` carries RAW
WARD IDS at k=5 and its numbers do not correspond to C1–C5; comparing the two files well by well
shows 25 "disagreements" that are not disagreements. `CLUSTER_LABELS` in `src/utils/config.py` is
authoritative, and `outputs/02_cluster_stats.csv` is where the labelled assignment lives (matrix row
R34).
