# Geometry and level-frame spec — build contract

**Status:** **implemented 2026-08-13.** Written 2026-08-08 as a design awaiting
sign-off; the build was carried out and this line was corrected on 2026-08-25 after an
audit against §5.

Evidence the contract is in force:

- Script 01 derives `ground_elev_m`, `pipe_top_elev_m` and `ground_source` and exports
  `outputs/01_well_elevations.csv`; ten downstream scripts consume those columns rather
  than re-deriving them (§7 steps 2–4).
- Script 26 v1.7.0 (2026-08-13) removed its local `_ground_offset` re-derivation.
- Script 15's header now cites this spec by name: "No upstand is added:
  `01_wells_clean.csv` already carries the master's `depth from surface` values
  (GEOMETRY_ARCHITECTURE_SPEC.md §3)."
- Acceptance test 2 passes: the retired columns appear only in Script 01.
- No rule-6 violation remains among the five local re-derivations listed in §4.

The §6 projections were made before the rerun and have been overtaken by it: C4's
half-life now stands at **37.6 months** in the current outputs, against the 43.70 → 46.91
projected here. §6 is kept as the record of what was expected, not as a current value —
half-lives, β₃ and λ are read from the pipeline, never from this document.

---

## 1. Rulings recorded (Martin, 2026-08-08)

1. `Newborough_Cleaned_For_Model.csv` and `well_metadata.csv` are correct as they
   stand. No data values change.
2. The model CSV is the master's `depth from surface` sheet. It is **ground-referenced**
   — the upstand is already applied on export. Scripts use it raw.
3. **No upstand correction anywhere**, including the cluster centroid. Wells are already
   on a common ground datum.
4. The only other level series is maOD, computed cleanly from the metadata.
5. `ceh37`, `ceh40`, `ceh41`, `ceh42` use the LiDAR DEM as their ground elevation.
6. **Architectural rule: scripts share variable names and data sources. A derived
   quantity is computed once and passed on, never recalculated downstream.**

Rule 6 is the one that matters most. The defects found in this audit are all instances
of its violation: three scripts each re-derived a frame conversion from raw geometry,
and disagreed.

---

## 2. Canonical quantities

Computed **once**, in Script 01, written to `01_well_elevations.csv` (already read by
14 scripts). Nothing downstream re-derives them.

| name | definition | notes |
|---|---|---|
| `ground_elev_m` | per `ground_source` below | the only ground elevation any script may use |
| `pipe_top_elev_m` | `ground_elev_m + Upstand_m` | derived, never read from `Pipe_Top_Elev` |
| `ground_source` | `'lidar'` or `'dgps'` | provenance, carried through |

**Ground rule:**

```
ground_source = 'lidar'  where DGPS_Ground_Elev is absent            [17 wells]
                         or well ∈ LIDAR_GROUND_WELLS               [ceh37, ceh40, ceh41, ceh42]
              = 'dgps'   otherwise                                   [78 wells]

ground_elev_m = DEM_Ground_Elev   where ground_source == 'lidar'     [21 wells]
              = DGPS_Ground_Elev  where ground_source == 'dgps'
```

Coverage 99/99, no gaps.

`LIDAR_GROUND_WELLS` goes in `config.py`, not inline — per the project's no-hardcoded-
values rule. Better still, if you're willing to add one column to `well_metadata.csv`,
put `ground_source` there and let Script 01 read it rather than hold a well list in
config. That is the only metadata change proposed in this spec, and it adds a column
without altering a single existing value.

**Retired from downstream use:** `DEM_Ground_Elev`, `DGPS_Ground_Elev`, `Pipe_Top_Elev`.
They remain in `well_metadata.csv` as inputs to Script 01 and are read nowhere else.

---

## 3. Level series

| file | definition | frame |
|---|---|---|
| `01_wells_clean.csv` | model CSV passed through | height relative to ground, negative below |
| `01_wells_clean_maod.csv` | `01_wells_clean + ground_elev_m` | m AOD |

Two series, one conversion, no corrections applied anywhere else.

---

## 4. Script changes

**Delete the local re-derivations** — these are the rule-6 violations:

| script | what goes |
|---|---|
| 03 | `build_upstand_lookup()`; the `− u` at 366, 427, 651, 731, 819, 1051 |
| 22 | `_upstand_lookup()`; the `− u` at 385, 478 |
| 26 | `_ground_offset()`; the `+ up` at 552–553 |
| 30 | the `s03.build_upstand_lookup` import; the `− u` at 219 |
| 15 | `d = −h + upstand` → `d = −h` at 158, 183 |

**Naming, same scripts:** Script 26's `level_pipe`, `MSL_m_pipe`, `MAX_m_pipe`,
`EWI_pipe` are all ground-frame quantities. Rename to `_bg` and correct the header's
frame claim at lines 22–26. Script 03's docstrings at 337 and 396 and Script 01's
comment block at 810–813 assert the pipe-top frame and must be rewritten, not deleted —
a stale justifying comment is how this survived review.

**Point at the canonical column:** Scripts 07 (145–151), 10b (194), 19 (677),
19b (91), 29 (164), 31 (123, 497), 31b (87, 165) read `DEM_Ground_Elev` as a ground
elevation. All become `ground_elev_m`.

**Script 01, line 839:**

```python
maod_cols[col] = wells_clean[col] + ground_elev_m        # was: + Pipe_Top_Elev
```

**No change:** 05, 08, 09b, 11b, 20, 21, 25, 32, 33, 35, 36, 38. These already use the
series raw or consume maOD without re-deriving.

---

## 5. Acceptance tests

1. `Upstand_m` is **derived** only in Script 01 and `config.py`. Reading the carrier is
   allowed; re-deriving is not — Script 03's own formulation. Mechanically: every hit
   from `grep -rn "Upstand_m" src/` outside Script 01 and `config.py` must be a read
   that is reported or discarded, never added to a level series. The three legitimate
   readers are:
   - **Script 03** — upstand is reported in the audit output, not applied; the series is
     already ground-referenced.
   - **Script 15** — `mean_upstand = float(np.mean(well_upstands))   # reported, not
     applied`; discarded at the call site (line 522).
   - **Script 26** — read alongside EWI for the output table, never added.

   A fourth reader, or any of these three feeding an arithmetic operation on a level
   series, fails the test.
2. `grep -rn "DEM_Ground_Elev\|DGPS_Ground_Elev\|Pipe_Top_Elev" src/` returns hits only
   in Script 01.
3. `01_wells_clean_maod.csv` minus `01_wells_clean.csv` equals `ground_elev_m` exactly,
   per well, constant in time.
4. Cluster membership and `02_cluster_stats.csv` byte-identical to the current run.
5. Full pipeline runs clean; `pipeline_manifest.json` guard unchanged
   (`_EXPECTED_ANALYTICAL_TOPLEVEL = 39`).

Test 2 is the real safeguard: it makes rule 6 mechanically checkable rather than a
convention someone has to remember.

Test 1 was originally written as "hits only in Script 01 and `config.py`". That is
stricter than rule 6 requires and stricter than the build: it would have banned reading
a column in order to report it. It was relaxed on 2026-08-25 to forbid re-derivation
instead, which is the property rule 6 actually asserts.

---

## 6. Known consequences

Measured in the sandbox by rerunning 01→02→03 with the Script 03 correction removed:

| | median rel Δ | max rel Δ |
|---|---|---|
| β₁ | 0.06% | 1.74% |
| β₂ | 0.30% | 16.78% |
| **β₃** | **1.85%** | **24.42%** |

Cluster flips: **0**. Cluster stats byte-identical.

| cluster | β₃ | t½ |
|---|---|---|
| C1 Lake Edge | −1.6% | 6.71 → 6.82 months |
| C2 Dune | −2.2% | 9.50 → 9.71 months |
| C3 Western Residual | −3.5% | 12.01 → 12.45 months |
| **C4 Main Forest** | **−6.8%** | **43.70 → 46.91 months** |
| C5 Coastal Forest | −4.2% | 15.06 → 15.73 months |

λ = √(Kb/(Sy·β₃)) moves as β₃^(−½). Every published β₃, half-life and λ shifts.
Documents must be updated after the rerun, not before.

maOD falls by up to 2 × `Upstand_m` per well (mean 0.155 m, max 1.42 m), constant in
time. Per the 2026-08-08 session, Script 11b's `depth_bg` deepens by a median 6.5 cm
with one classification flip at T41a — the site has been reported marginally wetter
than it is.

---

## 7. Sequencing

1. Add `ground_source` to `well_metadata.csv` (or `LIDAR_GROUND_WELLS` to `config.py`).
2. Script 01: derive `ground_elev_m` / `pipe_top_elev_m`, export, change line 839.
3. Delete the five local re-derivations. Rerun 01→03, confirm zero cluster flips.
4. Repoint the seven Class D scripts. Full pipeline run, diff every output.
5. Living tools: hub recompute per `HUB_CORRECTION_NOTE_2026-08-08.md`.
6. Documents: report maOD formula and DEM validation passage, supplement, papers.

Steps 2 and 3 land together — splitting them leaves the pipeline internally
inconsistent between runs.

---

## 8. Open items

- **`nw13` / `wmc4` share easting 241761.0 / northing 364180.0.** Both have real records
  (166 and 169 hub rows). Martin: 1 m apart, separate by adding a decimal. Needs his
  pick of which moves and which way.
- **Prior work to reconcile.** A corrected `well_metadata.csv` and a standalone
  pipe-top/upstand correction changelog were produced on 2026-08-08 (67 wells;
  197 CSVs identical, 11 changed). That standalone changelog was never committed
  and is lost (searched under T-10, 2026-08-26 and 2026-09-04); the correction it
  recorded landed as part of the site-wide geometry rework recorded in this spec,
  and the corrected `well_metadata.csv` is the committed source of truth. The
  ceh13 pipe-top facet of that day's work is recorded in
  `notes/findings/HUB_CORRECTION_NOTE_2026-08-08.md`. This open item is historical:
  the rework has landed — confirm `well_metadata.csv` is current before step 1.
- **`L1`, `L4`** carry no readings and are not in the reference network. `L1`'s
  `DEM_Ground_Elev` is 0.696 m below master ground. Excluded from the ground rule by
  Martin's ruling; no action.
