# Proof pass over the report — 2026-09-24

**Session:** Fable (Cowork bridge / cloud clone), session_01EpgeUDxt66S79EacJHmXo5.
Martin: "I am wondering how to proof read the doc, are the tools we have sufficient and
should I print the pdf" → "yes please design that" → "let's proof the report first".

## What was run

Two passes the gates cannot do, over the committed mirrors (the chapter mirrors `report_edits/text/report6.md` to `report16.md`,
the abstract in `report.md`) and the committed figure PNGs, by seven Sonnet subagents in
parallel, read-only, each with a fixed brief and a table-of-findings output:

- **Continuity and contradiction** (three agents): abstract / introduction / conclusions /
  academic summary against §4 and §5; Methods §3 against Results §4 (with the Notation
  table, the symbol register and `record_basis.csv`); Discussion §5 and Limitations §6
  against §4 and the decision log. Classes: contradiction, unsupported, hedging drift,
  withdrawn claim still present, terminology, cross-reference, plain English.
- **Caption against figure** (four agents, 21 figures each): every caption read in full
  from the mirror and set against the rendered PNG — panels, axes and units, legend and
  series, numbers annotated on the figure, date span, the `(Source:)` marker.

Every text finding below was re-verified by the main session against the mirrors and, where
a number is in dispute, against the committed CSV that owns it. Figure findings marked
**verified** were re-read from the PNG by the main session; the rest are as the agent
reported them and are marked by how legible the evidence is. Two agent findings were
discarded on verification: "Table 3 vs Table 1.3" (a chapter-numbered sequence field, the
§4d artefact, not a defect) and a Figure 74 finding made against Figure 73's caption.

The academic summary's findings are parked (Martin: the report first) — they are listed
at the end so they are not lost.

## A. Numbers that trace to a committed CSV and are wrong in the text — fixed directly

| Where | Text says | CSV says | Source |
|---|---|---|---|
| report8 §3.7.x (t½ withheld wells) | CEH13 "t½ approximately 526 months, an order of magnitude beyond all other wells" | t½ = 224 months on the comparison window (β₃ 0.0031), 97 on the full record; the next-longest well is 82 | `03_master_data.csv`; `03_15_per_well_window_sensitivity.csv`. 526 traces to nothing. |
| report10 §5.6.1 | "C4 … t½ … mean 40 months, range 16–88 months" | mean 37.9, range 17.1–82.0 (the seven C4 wells after CEH13/14 are withheld) — as report9 §4.9.3 already states | `03_master_data.csv` |
| report10 §5.x (EWI), abstract | "reconstructs observed MSL5 across the open dune … to 61 mm RMSE" | 66.2 mm | `26_report_numbers.csv` `ewi_msl5_rmse_mm_open_dune` — **never registered in `citation_index.csv`**, which is why 0 drifted did not catch it |
| report12 Conclusion 5 | the same reconstruction "to 119 mm RMSE" | 66.2 mm | as above |
| report12 Conclusion 7 | clearfell "C4 +8.1 mm w.e./month, C5 +10.4"; broadleaf "C4 −0.7 mm, C5 +1.6" | report9 §4.13.2 and the abstract say +10.0 / +12.2 and +2.8 / +4.0 | Script 21 outputs (no report_numbers file — the conclusion was never re-pulled after the BACI correction; register the keys on the fix) |
| Figure 11 caption (§4.2.3) | "P̄ = 74.4 mm/month … Residuals < 2.3 % of losses" | figure panel: 74.3; residual max 1.79 % | `16_report_numbers.csv` |
| Figure 81 caption (§5.8.2) | "C4 ≈ 34 months" half-life; "≈ 120 mm, about 80 % of the 150 mm modelled equilibrium" | figure legend: C4 t½ = 38 mo (the CSV mean); annotation: 75 % of 150 mm at 8 yr | `03_master_data.csv`; `09f_01_reach_profile.csv` |
| Figure 75 caption (§4.12.1) | "the assumed rate (29 mm yr⁻¹, dashed line)" | figure legend: assumed δ₀ = 31.4 mm/yr; `Headline_fit_delta_0` = −31.35 | `25_report_numbers.csv` |
| Figure 65 caption (§4.11) | "CEH36 +130 mm, CEH21 +74 mm, CEH18 +9 mm" | figure text box: +129 · +74 · +8 mm | Script 20 numbers — a 1 mm rendering difference at the quoted precision; fix only if the CSV disagrees at 1 mm |
| Figure 20 caption (§4.5.2) | "SSM residual (+0.081 m)" | panel (c) bar: +0.073 m | `09c_report_numbers.csv` (check which key: the equilibration residual is 0.187 / 0.182; the spring residual 0.0097 / 0.099 — the caption's quantity must be named before the number is fixed) |
| Figure 47 caption (§4.8.4) | "spring basis (c, r = +0.67)" | panel (c) title: r = +0.56 (n = 18) | Script 26 EWI outputs |
| Figure 67 caption (§4.12) | "n = 70 wells retained" | figure footer: n = 71 wells | `10b_spatial_step_data.csv` |
| Figure 70 caption (§4.12) | "Network mean −588 mm (2017) to −685 mm (2023)" | figure annotation: net −467 mm (springs 2013–17) vs −572 mm (springs 2019–23) | Script 34 / 26 outputs — a different quantity or a stale render; name it before fixing |
| Figure 37 caption (§4.6.7) | "p = 0.19, ns" | panel (c): p = 0.171 | Script 10 outputs |
| Figure 60 caption (§4.10.4) | "δ₀ of −31.3 mm yr⁻¹" | figure: −31.4; CSV −31.35 | a rounding-boundary case (CLAUDE.md §3: do not churn) — leave |

## B. The figure is what is wrong, or the caption describes a different render — script or caption, one of them moves

| Figure | Finding | Proposed fix |
|---|---|---|
| **64** (§4.11, `20_drawdown_propagation_nohead.png`) — verified | Caption describes "mean annual water table elevation (m AOD) with normalized Darcy flow direction vectors (white arrows) … NW6: 55 mm"; the PNG is the *nohead* render: DEM hillshade + drawdown contour bands, no head surface, no arrows, no NW6 label | The caption was written for the with-head variant that is not the committed figure. Rewrite the caption to the nohead render (the project box already warns this figure is confused with others), or commit the with-head render — Martin's choice of which figure the report wants |
| **83** (§5.9, `11c_pflood_achievability.png`) | Caption and text use m_P; the figure's title and legend use λ — the symbol the report reserves for the forest drawdown reach | Script 11c label → m_P (a script edit; the caption is right) |
| **82** (§5.8.2, `09g_mechanism_grid.png`) | Caption "Four drivers of the Newborough water table"; figure title "Three drivers of water-table change" | Decide the count (the grid shows undisturbed + scrape + clearfell + coastal reach); align the figure title in Script 09g or the caption |
| **76** (§4.12.1, `37b_*`) | Caption "hatched, below the separator"; figure plots the hatched bar above it — and the figure's own footnote repeats "below" | Script 37b footnote + caption → "above" (or move the bar) |
| **71** (§4.12, `32_*`) | Caption "warm colours rise, cool colours decline"; colourbar "blue = holds up, red = sinks" | Caption → the figure's convention (blue rises) |
| **36** (§4.6.6, `10_*` panel d) | Caption promises Δβ₁, Δβ₂, Δβ₃; panel (d) plots Δβ₁ and Δβ₂ only | Add Δβ₃ to the panel (script) or drop it from the caption |
| **7** (§4.2, cluster validation) | Caption names silhouette, Calinski–Harabasz and Ward's merge distance; the figure has two panels (elbow, silhouette) | Drop CH from the caption unless Script 02 is meant to plot it |
| **58** (§4.10.2, `25_*`) | Caption describes three fits; panel (a) also carries a fourth (forest-free exponential, with a ΔAIC box) and there is an undescribed panel (b), the per-cluster decomposition | Caption to describe (b) and the exponential comparator, or Script 25 to drop them from the report render |
| **46** (§4.8.3, `14_*`) | Caption "2005–2025 … observed annual summer minimum … with OLS trend lines"; panel (a) runs to 2045 with extrapolated trends and a shaded "critical intervention window (2030–2039)" the caption never mentions; the panel's own title is "Projected Climate Trajectory" | Caption to say the panel projects to 2045 and what the shaded window is — or the render to stop at the record if the projection is not meant to be shown here (the no-extrapolation rule applies to quoting, not to a labelled projection, but say so) |
| **40** (§4.7.4, `11b_*`) | Caption "CEH18 and CEH21 use post-October 2023 data only"; figure inset "DEM-corrected only; full record used" | One of them is the record basis; `record_basis.csv` decides — fix the loser |
| **22** (§4.5.4, `09_scrape_*`) | Caption "CEH36 was scraped in April 2015 only"; figure title "CEH36 scraped Apr 2015 & Oct 2023" with a fourth era group | If CEH36 was re-scraped in October 2023 the caption (and any text saying "only") is wrong; if not, Script 09 has the wrong era table |
| **19** (§4.5.2, paired BACI) | Caption "CEH21 vs CEH22" as control; the CEH21 panel's y-axis label reads "CEH WELL − CEH4" like the other two | Script 09c axis label, or the caption's control pairing — check `09c` which control CEH21 is differenced against |
| **31** (§4.6.3, `10a_*`) | Caption "WMC3 minus Forest control centroid"; figure subtitle "Forest control — Impact zone" (reversed order; the sign carries the interpretation) | Align the subtitle's order with the quantity actually plotted (+113 mm is a rise at the Impact well, so the caption's order is the one the sign supports) |
| 53 (§4.9.3) | Caption "C3 t½ = 7–21 months"; agent read two C3 labels at ≈3.6 and ≈3.9 months | CSV: C3 range 6.8–21.1 — the caption is right; the agent's read is probably of another annotation. Not a finding unless the PNG shows otherwise |
| 26 (§4.5.5) | Caption "C3 control centroid step"; map subtitle "C3W controls median +0.003 m subtracted" | Cosmetic: name the same statistic in both |
| 1 (§2 site map), 25, 33, 37, 4, 32, 17, 73 | Elements plotted but not in the caption: restock and felling blocks in the legend (1); clearfell and re-scrape lines (25); a fourth panel (d) (33); panels (a) and (b) (37); clear-fell marker (4); the Edge-tier statistic +30 mm p = 0.25 in the panel subtitle (32); a strongly negative Main Forest outlier the caption calls "small gains" (17); the "filled triangles" the caption describes are not distinguishable (73) | Caption additions — Martin's call on each whether the element stays |
| 8 (§4.2 dendrogram) | Caption "C4 separates from the adjacent C3 at a lower linkage distance"; the dendrogram splits C4 from (C5+C3) first | Cosmetic wording |
| 52 (§4.9.2) | The `(Source:)` marker sits mid-caption, followed by the description of panel (b) | Move the marker to the end (`figref`/`reference_lint` anchor on captions; a mid-caption marker is the class CLAUDE.md warns about) |

## C. Martin's calls — prose that says two things

| Where | The two passages | The question |
|---|---|---|
| report10 §5.8.2 line ~496 | "on the shared five-year footing the accumulating coastal curve **crosses it at roughly 700 m** — coastal retreat is the larger driver along the western fringe" vs the same subsection: "A flat climate line and the distance at which the coastal curve would cross it are **not drawn**, because the level they would rest on is not separately identified" — and D-042 retired the crossing | Delete the "crosses it at roughly 700 m" clause? (D-042 says yes.) |
| report10 §5.6.x lines ~312, ~380 | "eight sinkers on the south-western coastal and western margin — CEH22, CEH21, CEH19 and **CEH11** … consistent with the coastal-retreat gradient of §4.10.2" vs report9: CEH11 "on the south-eastern coast … proximity to the Menai Strait", which §4.10.2's model excludes as a non-eroding boundary | Take CEH11 out of the coastal-retreat list, or say its decline is not that gradient? |
| report9 §4.12.1 Figure 75 vs text | δ₀ = −31.3 (text, twice) vs the caption's "assumed rate 29" | Covered in A (the caption is stale) — noted here because if 29 was a deliberate prior it needs a sentence |
| report10 §5.2.x lines 24 and 96 | "(Section 4.8.3, Figure 46)" cited for winter flooding frequency and for summer-minimum trends; §4.8.3 is the MSL5 subsection; the content is in §4.8.2 and §4.8.1 | Repoint to 4.8.2 / 4.8.1 (factual — I will do it unless you object) |
| report16 Notation | EWI row "§3.6; Script 19" (it is §3.7.6, Script 26); t½ "§3.7" (§3.4.5, beside t_R); MSL5 "§3.9" (§3.7.5); DEM/LiDAR/DGPS/AOD/OS "§3.2" (§3.1.1); PET/ET → §3.1.2; ESS "§3.3" (§3.2.2) | Factual — section pointers in the Notation table lag the restructuring; I will repoint them |
| report8 CEH13 sentence | "an order of magnitude beyond all other wells" — at 224 vs 82 it is under three times | Rewrite with the fix in A |

## D. Parked — the academic summary (carries an older draft)

30 of 66 TLM wells written as 44; 4 unreachable wells written as 5; SD16 / 2028 (CI 2022–49) written as SD15b / 2030–32; CEH22 −27.8 written as −26.5 and "outside the reference network"; 97 % written as 95 %; a "170–230 mm cumulative" sum of MSL5 and summer-minimum quantities that §4 says are not on a common footing; C1 amplification 0.66× vs 0.64×. To be taken with the other documents once the report is settled — though, as Martin says, reviewing them usually produces a report edit; the "170–230 mm" sum is the one to watch for that.

## What this pass cannot tell you

It reads the mirrors, not the page: layout, figure placement, widows, a caption on the wrong page, and the English of a sentence read at speed are the print's job. The two passes above found the contradictions and the caption drift; the printed read is for everything else, and it comes after A–C are settled, so the pages you read are the ones that will ship.
