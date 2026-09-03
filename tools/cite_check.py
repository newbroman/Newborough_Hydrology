#!/usr/bin/env python3
"""
cite_check.py
=============
Standing check that the document corpus still agrees with the committed
pipeline outputs.

tools/audit_number_drift.py is CHANGE-triggered: it diffs two git refs and
hunts for renderings of the value that just changed. It cannot see a number
that went stale before anyone was watching — which is how report9 and Paper 1
both carried five superseded cluster coefficients for weeks while the tooling
reported clean.

This tool is STANDING: it asks, of every value the pipeline currently publishes,
whether the corpus still quotes it — and, where it does not, whether the corpus
quotes a NEAR MISS instead. A near miss is the signature of a stale citation:
0.090 where the CSV now says 0.088, VIF 1.11 where it says 1.09.

It also evaluates a small register of CLAIMS — the assertions that carry no
number and so no numeric tool can check. "C4 has the lowest VIF in the network"
is either true of the committed CSV or it is not; the register makes that
machine-decidable and names every document asserting it.

Usage:
    python3 tools/cite_check.py                  # everything; takes minutes
    python3 tools/cite_check.py --out /tmp/cite.log      # ...and keep the log
    python3 tools/cite_check.py --claims-only    # ~1s; what check_all runs
    python3 tools/cite_check.py --dp 2 3 4 --near 2

  Five sections. Four cost about a second each; NUMBERS costs minutes, because
  it scans every mirror for every committed value at three precisions. Run them
  separately when that matters:

    --section columns   are the named value columns still in the CSVs?   ~1s
    --section index     the exact citation-index check                   ~1s
    --section numbers   every published value against the corpus         MINUTES
    --section spread    one quantity, several renderings                 ~1s
    --section claims    assertions with no number                        ~1s

  --section is repeatable. --docs SUBSTR restricts the corpus and is repeatable
  too, matched as OR, which is what makes NUMBERS runnable in pieces:

    python3 tools/cite_check.py --section numbers --docs report_edits
    python3 tools/cite_check.py --section numbers --docs docs/ --docs readme
"""
from __future__ import annotations

__version__ = "1.15.0"  # Hollingham (2026) — 2026-09-03. Scripts 17 and 38
#   enter EXTRA_VALUE_TABLES, and HISTORY_DOCS stops the CITATION check reading
#   the Decision Log and PARTITION_HISTORY — documents whose job is to record
#   what a value used to be, and which the spread check had always excluded.
#   Script 17 is keyed on (Cluster, Corrected); Script 38 registers only its
#   coast-minus-inland difference, its quoted trend being in a .txt no value
#   table can reach.
#
# v1.14.0   # Hollingham (2026) — 2026-09-03. Script 37 enters
#   EXTRA_VALUE_TABLES. It has no report-numbers file and was in no value table,
#   so collect_values() never read it and not one of its numbers had ever been
#   checked. D-104 corrected its fit on 2026-08-31 and retired every earlier
#   scale factor; the corpus went on quoting them for three days, with report9
#   and the Supplement disagreeing about one of them, and every gate green.
#   Keyed on (window, variant) because 2018_2025 appears twice. W101.
#
# v1.13.0   # Hollingham (2026) — 2026-08-31. The claims register
#   gains a threshold rule, a self-consistency check, and a hard failure for any
#   row it cannot evaluate. Martin: "I don't like the sound of numbers that
#   aren't being checked."
#
#   WHAT WENT WRONG. Paper 1's numbered conclusion 5 said "roughly 29 mm/yr"
#   and "around a third" while Paper 1's own §4.11 and §5 said "roughly 26 mm/yr
#   at 150 m" and "about a quarter", and the committed CSVs agreed with the
#   results section throughout — δ₀ −31.33, the 150 m rate −26.18 ± 1.45, C3's
#   coastal share 22.81%. Nothing fired, and three separate gaps are why.
#
#   (1) `band:<col>:<lo>:<hi>`. The register could express "C4 has the lowest
#   β₃" but not "C3's coastal share is about a quarter", because the rule
#   vocabulary was argmin/argmax only. A share is a threshold claim.
#   `expect` names the row, the band is checked against it, and the selection
#   must match EXACTLY ONE row or the entry faults — a band silently evaluated
#   against the first of several matching rows is worse than no band.
#
#   (2) COMPOSITE KEYS, `key_col = "source+model"`. 25_01_panel_fit_parameters
#   has no single identifying column: `source` matches two models, `model`
#   matches four sources. So the headline coastal fit could not be registered as
#   a claim AT ALL. That is why the coast-edge rate was unwatched.
#
#   (3) `contradicts`, and this is the one that would have caught it. Every
#   other check here asks whether the corpus matches the DATA. No committed
#   value had moved, so that question was answered correctly and the corpus was
#   still contradicting itself. `contradicts` is a pipe-separated list of
#   literal phrasings known to be wrong — in practice, wordings that were in the
#   corpus and were corrected. Their reappearance is a breach whatever the CSV
#   says. Enumerating wrong values in the abstract would be fragile; enumerating
#   the ones that actually occurred is not, and it is the same discipline as
#   keeping a falsified claim in the register so it cannot come back unnoticed.
#
#   AND THE SKIP IS GONE. An unrecognised rule, an absent column, a missing CSV
#   or an ambiguous key used to print SKIP and pass. That left rows sitting in
#   the register looking like cover while nothing evaluated them — the same
#   silent-gap failure as a renamed value column (check_value_columns) and the
#   swallowed git error in push_working. All four now FAULT and gate.

# v1.12.0  # Hollingham (2026) — 2026-08-31. The net is extended
#   on evidence rather than on recollection, and the key may now be composite.
#
#   WHAT WAS MEASURED. Every CSV under outputs/ that no report-numbers file and
#   no value table reaches was tested against the corpus: does a DISTINCTIVE
#   rendering of one of its values appear literally in a swept document?
#   Distinctive means four or more SIGNIFICANT digits — trailing zeros stripped,
#   not just leading ones, so 1.000, 2.000 and 11.00 are rejected. That
#   distinction is the whole difference between a shortlist and a list of
#   everything: with only leading zeros stripped, "1.000" reads as four digits
#   and every table in the tree looks quoted.
#
#   Candidates were then ranked by HIT RATE, not hit count. A per-well table
#   with 400 distinctive values collects chance matches in a 20-Mchar corpus
#   whatever it contains; a five-row summary table whose values keep appearing
#   is being quoted. Ranking by count put a file written the same day, cited
#   nowhere, at the top of the list.
#
#   AND THE FILTER THAT MATTERS MOST: a table is added only for the columns
#   carrying quantities NOT already watched elsewhere. Several of the highest-
#   scoring candidates score highly because they REPEAT the cluster betas, which
#   HEADLINE_TABLES already covers; adding those columns would inflate the index
#   and check the same number five times. The betas are excluded from every
#   table added below.
#
#   COMPOSITE KEYS. Three of the best candidates key on a pair — cluster and
#   scenario, zone and phase, cluster and basis — and the loop assumed a single
#   column, so every second row overwrote the first in the report's vocabulary.
#   `kcol` may now be a tuple, joined with " / ". Backward compatible: a string
#   behaves exactly as before, so no existing entry changes.

# v1.11.0  # Hollingham (2026) — 2026-08-23. M31: a value stored
#   in metres and quoted in millimetres could never match, because check_numbers
#   renders the stored value in its stored unit and no conversion existed. That
#   is not a rare shape: 22 metre-stored keys are quoted in mm at 105 places
#   across 7 documents, including the +113 mm clearfell headline, and NONE of
#   those 105 was covered by any index row or by this scan.
#
#   The pass added below is ADDITIVE — it runs after the same-unit scan and can
#   only add hits, so nothing that passes today can be broken by it. Two guards
#   decide whether it is usable, and both were measured before it shipped:
#
#     >= 3 significant digits   at 2 digits or fewer the mm rendering of a metre
#                               value collides constantly (0, 1, 7, 29 mm) and
#                               admits 160+ noise pairs. searchable() already
#                               enforces MIN_SIG_DIGITS = 3, so it is reused.
#     strict anchoring          at >= 3 digits with the permissive exact-hit
#                               anchor precision is 42%; with the strict anchor
#                               (subject AND quantity) it is 86% on 28 hand-
#                               adjudicated candidates. The strict anchor is not
#                               optional here, and this is also the answer to
#                               M23: the tightening M23 wanted is worth having
#                               exactly where this pass needs it, and nowhere
#                               else — applied to the existing exact-hit path it
#                               loses 102 recognitions and makes triage worse.
#
#   The unit token is also required: the matched number must be followed by mm.
#   Without that the pass is a bare 1000x sweep, which is the collision trap.
#
__version__ = "1.10.0"  # Hollingham (2026) — 2026-08-22. near_misses() was
#   generating the value's own rendering as a near miss of itself. It excluded
#   k = 0 but not the STRING: 2.0865 renders at 3 dp as "2.087", and so does
#   2.0865 + 0.001, because in binary that sum is 2.08749999999999991. Every
#   document quoting such a number CORRECTLY was reported as drifted. This is
#   the bulk of what made the triage list unreadable (M23).
#
# v1.9.0  # Hollingham (2026) — 2026-08-22. The sweep could tell
#   whether the corpus quotes the COMMITTED value. It could not tell whether the
#   corpus quotes the SAME value in every document, and that is the question that
#   bit: the forest reach was quoted at 220, 223, 225, 228 and 230 m across five
#   documents while the figure rendered 226 and the CSV held 226.442. None of
#   those matched at any searched precision, so the quantity sat in the "not
#   cited anywhere" bin, which is exactly where every deliberately-rounded prose
#   figure lives and where nothing had ever looked.
#
#   Two changes, both asked for by Martin on 2026-08-22:
#     (a) values of magnitude >= LARGE_VALUE_MIN are also searched at dp = 0, so
#         a quantity of order hundreds is findable in the form prose writes it;
#     (b) a new SPREAD check — for a registered quantity, collect EVERY rendering
#         near its anchor across the whole corpus and report the distinct set.
#         It fires on disagreement between documents, whether or not any of the
#         renderings matches the CSV, which is the case the other checks cannot
#         see. Advisory unless --spread-gate.
#
# v1.8.0  # Hollingham (2026) — 2026-08-21. EXTRA_VALUE_TABLES —
#   the third hole. collect_values() reads only *report_numbers*.csv, so any
#   script publishing into the documents without one was never checked at all.
#   Twenty-four output directories carry CSVs and no report-numbers file; the
#   register names the ones whose numbers are quoted, starting with Script 15,
#   which was stale in four of five values and had flipped a published ranking
#   while the gate stayed green.
#
# v1.7.0  # Hollingham (2026) — 2026-08-21. Manifest counts are
#   registered only where a phrase anchor exists. A small integer without one
#   cannot be distinguished from a step index, so the sub-step counts and
#   analytical_phases — the latter cited in no document by standing rule — were
#   reporting every occurrence of "11", "13" and "15" in the corpus as a stale
#   count. Checking a number badly is worse than not checking it: it fills the
#   triage list with noise and the real hits stop being read.
#
# v1.6.1  # Hollingham (2026) — 2026-08-21. The tier and exec
#   phrases needed the number in them. "analytical" and "default pass" sit
#   beside step indices as well as counts — "steps 36-41/50, all analytical-
#   default" — so the loose phrases matched indices and reported 38 and 41 as
#   stale counts. Every manifest phrase now pins {n}.
#
# v1.6.0  # Hollingham (2026) — 2026-08-21. Phrase anchors for the
#   manifest counts. A token anchor cannot separate "50 steps" from "step 50" —
#   both sit beside the word "steps" — so the counts fired on step indices and
#   the triage list was unusable. ANCHOR_PHRASES requires a phrase, in a 60-
#   character window rather than a 400-character one, with the number's own
#   value substituted into the phrase where it belongs.
#
# v1.5.0  # Hollingham (2026) — 2026-08-21. Integer-valued
#   quantities are searched at zero decimal places. The default precision set
#   is [2, 3, 4], so the step count was rendered "50.00" and matched nothing:
#   the manifest counts were registered, anchored and admitted, and still never
#   searched for. Whole numbers now get dp=0 added automatically.
#
# v1.4.0  # Hollingham (2026) — 2026-08-21. Adds the MIXED class,
#   which is where the corpus's real drift has been hiding. check_numbers()
#   stopped at the first document quoting a value correctly and called it
#   settled — so a number corrected in three documents and left stale in seven
#   reported as "cited and current". The scan now continues past that hit and
#   reports the stale occurrences as MIXED, sorted ahead of everything else: a
#   value that is right in one document and wrong in another is a sweep that
#   was started and not finished, which is more urgent than a value uniformly
#   out of date.
#
# v1.3.0  # Hollingham (2026) — 2026-08-21. The manifest counts
#   registered in v1.2.0 still did not fire, for two reasons found by probing
#   rather than by reading: the keys' anchors were the manifest's own field
#   names ("total", "registered") and not the words the documents use, and
#   searchable() rejects two-digit values outright, so "49" was never even
#   searched for. Keys are now named for the document vocabulary, and short
#   values are admitted for anchored manifest keys only. With both in place the
#   step count is found, anchored, in ten documents.
#
# v1.2.0  # Hollingham (2026) — 2026-08-21. Closes the two holes
#   that let stale numbers sit behind a clean gate.
#
#   (1) EVERY OCCURRENCE, not the indexed one. check_index() walks index ROWS,
#   and the index carries one row per (key, document). A value repeated across
#   documents was therefore checked in one of them: the clearfell step was
#   flagged in the Methods Supplement while the same stale figure stood in
#   report10 and in the Conclusions. sweep_repeats() now takes every stale
#   string the index check found and searches the WHOLE corpus for it, so a
#   number that appears in five documents is reported five times.
#
#   (2) THE MANIFEST COUNTS. A number with no key was never checked at all, and
#   the most-repeated numbers in the corpus - the registered step count, the
#   phase count, the tier and exec splits - had none. Registering Script 39
#   moved the step count from 49 to 50 and nine documents went stale in silence.
#   collect_values() now reads outputs/pipeline_manifest.json, so the counts
#   run_analysis.py already guards internally are guarded in the documents too.
#
# v1.1.0  # Hollingham (2026) — 2026-08-20. Matching is now
#        numeric-boundary aware and context aware, and the citation index's
#        stored `before`/`after` slices are finally used for what they were
#        recorded for. Every place that asked `needle in text` asked a
#        substring question and got a substring answer: 0.135 "found" inside
#        the frame height 10.135cm, 1.29 inside 11.298cm, 1.76 inside the
#        summer minimum -1.766 m, 30 inside "Figure 30" and inside "R2 <= 0.30",
#        15.45 inside width="15.45cm". Those matches drove both directions of
#        verdict - a phantom hit reported a value as "cited and current" when
#        no document quotes it, and a phantom near miss put a healthy value on
#        the triage list. `number_spans()` now yields only occurrences that are
#        whole numbers in a citable context, `quotes()` replaces the bare `in`
#        test, and `locate()` picks the occurrence an index row points at by
#        scoring the stored context against the document. No behaviour outside
#        matching changes: the anchor window, the near-miss span, the claims
#        rules and the exit codes are untouched.
#
# 1.0.0  marks the module's state before this change; it carried no
#        __version__ constant previously.

import argparse
import csv
import json
import math
import re
import sys
from bisect import bisect_left, bisect_right
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]

# Mirrors, plus the documents that are already text. Never the ODTs. Keep in
# step with refresh_mirrors.py.
#
# "docs/**/text/*.md" replaces the two narrower docs globs so that adding a
# mirror directory to refresh_mirrors.py is enough - the corpus follows, and a
# document cannot be mirrored but unchecked.
#
# The repo's own markdown and index.html need no mirror: they are text already,
# and strip_markup() handles index.html's HTML. index.html is the only published
# page that states pipeline numbers, and only its step and phase counts were
# protected before 2026-08-18, via the PL markers.
# DOC_GLOBS now lives in tools/doc_globs.py. This file and symbol_check
# each carried a copy, symbol_check's asserting the two 'should never
# diverge' -- and they had: INTERCEPTION_TREATMENT.md was swept here and
# not there. A comment asking for two lists to agree is a request; one
# list is a guarantee.
from doc_globs import DOC_GLOBS


# Paths the report sweeps must never read, whatever the globs above match.
#
# living/ is a separate operational lane (D-063): the Water Watch newsletter and
# the live forecaster feeds. Its hub, readings_living.csv, GROWS EVERY MONTH by
# design, while the report is fitted to a record that record_basis.csv declares.
# A sweep that read living/ would compare corpus numbers against a moving target
# and report drift that is not drift.
#
# It is excluded today only because no glob happens to reach it. That is not a
# guarantee — widening "docs/**/text/*.md" to "**/text/*.md" would pull it in
# silently — so the exclusion is stated here and enforced, rather than left to
# the accident of a pattern.
EXCLUDE_PREFIXES = ("living/",)


def _excluded(rel: str) -> bool:
    return any(rel.startswith(p) for p in EXCLUDE_PREFIXES)

# Headline tables whose values are cited directly rather than via a
# report-numbers key. (csv path, key column, value columns).
# Declared CONSTANTS. config.py and pipeline_params.py hold the pipeline's
# inputs — retreat rates, reference distances, datums, thresholds — and 60 of
# them are quoted somewhere in the corpus while none was a value this check
# could see. pipeline_lint asks whether a constant is a real parameter rather
# than a leftover default; nothing asked whether the PROSE still agrees with it.
#
# Fitted results do NOT belong here and are not read from here. A δ₀ written
# into a constants file would be a hard-coded result that could drift from its
# own fit, which is the thing pipeline_lint --check literals exists to catch.
# Inputs live in config.py; results live in report-numbers files. That is the
# same line the report draws between Methods and Results (D-075).
CONSTANT_SOURCES = ["src/utils/config.py", "src/utils/pipeline_params.py"]
_CONSTANT_RE = re.compile(r"(?m)^([A-Z][A-Z0-9_]{2,})\s*=\s*(-?\d+(?:\.\d+)?)\s*(?:#|$)")


HEADLINE_TABLES = [
    ("outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv",
     "Cluster_Label",
     # Every column the mechanistic table renders, so the whole table is
     # covered rather than four of its six numeric columns.
     ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage",
      "R2", "LCSC_percent"]),
]

# Value tables that are NOT report-numbers files but whose numbers reach the
# documents. collect_values() reads outputs/**/*report_numbers*.csv, so a script
# that publishes into the prose without one is invisible to the whole check —
# not "not cited", never looked at. Script 15 was stale in four of five lambda
# values and four of five NSE improvements, and had flipped a published ranking,
# with the gate green throughout. Twenty-four output directories carry CSVs and
# no report-numbers file; these are the ones whose values are quoted.
#   (csv path, key column, value columns)  — same shape as HEADLINE_TABLES.
EXTRA_VALUE_TABLES = [
    ("outputs/15_depth_dependent_pet/15_04_best_params.csv", "Cluster",
     # Best_Kappa from Script 15 v1.3.0 (2026-08-27). The column was
     # Best_Lambda; report8 §3.4.6 and the register have always called the
     # decay parameter κ. THIS GATE FAILS UNTIL SCRIPT 15 IS RERUN — the
     # committed CSV still carries the old header.
     ["Best_Kappa", "NSE_Iterative", "SSM_NSE", "R2_OneStep"]),
    # Script 19's scenario table. Added 2026-08-28 after the D-046 interception
    # fix moved 69 cells in it and the corpus turned out to quote them in seven
    # documents — none of it visible to any check, because this file has no
    # report-numbers counterpart and was in no value table. The forestry
    # scenarios moved 23-118%; nothing would have said so.
    ("outputs/19_spatial_groundwater/19_scenario_summary.csv", "cluster",
     ["dh_mean_m", "dh_median_m", "we_mean_mm", "we_median_mm"]),
    ("outputs/03_state_space_model/03_04_lag_diagnostic.csv", "Cluster_Label",
     ["R2"]),
    ("outputs/32_differential_movement/32_site_mean_trend.csv", "period",
     ["slope_mm_yr", "resid_sd_mm", "min_detectable_mm_yr"]),
    ("outputs/22_residual_lag_analysis/22_06_ssm_cluster_mean_inference.csv",
     "Cluster_Label", ["R2", "durbin_watson", "ar1_phi"]),
    ("outputs/39_ccw_hindcast/39_01_hindcast_per_well.csv", "well",
     ["nse", "pearson_r", "bias_m", "epoch_shift_m"]),

    # ── Added 2026-09-03 (W101). SCRIPT 37 WAS IN NO VALUE TABLE AND HAS NO
    # report-numbers FILE, so not one of its numbers had ever been looked at.
    # D-104 corrected the fit on 2026-08-31 — 29 of 59 wells had reached it
    # with fabricated zero predictors and four had defeated the C1 sluice
    # exclusion — and explicitly retired every pre-correction scale factor, CI,
    # R2 and n. The corpus went on quoting them for three days: report9 carried
    # s_cf 3.72 against a committed 1.65 and an intercept of -559 against -593,
    # while the Supplement carried s_coast 0.53 against report9's own 0.51 —
    # two documents disagreeing about one number, with every gate green,
    # because nothing was watching this file.
    # The key is (window, variant): 2018_2025 appears twice, once as the
    # primary fit and once as the broadleaf-covariate sensitivity, and keying
    # on the window alone would silently collapse them.
    # ── Added 2026-09-03, the next three of the twelve, ranked by how much of
    # each table the corpus actually quotes (a screen re-run AFTER the builder's
    # minus blindness was fixed, since the first ranking could not see a
    # negative number).
    #
    # 10c, 50.7% quoted. Two tables. The correlations file stacks TWO blocks
    # separated by a blank row, so beta_2 and beta_3 each appear twice as a
    # Coefficient — but the blocks populate disjoint columns, so keying on
    # Coefficient alone emits 26 distinct (label, column) keys and collides on
    # none of them. Checked rather than assumed, because the composite-key trap
    # has now bitten in Script 37 and Script 17.
    ("outputs/10c_forest_zone_analysis/10c_forest_zone_cluster_summary.csv",
     "Metric",
     ["C4_mean", "C4_sd", "C4_min", "C4_max",
      "C5_mean", "C5_sd", "C5_min", "C5_max", "t_statistic", "p_value"]),
    ("outputs/10c_forest_zone_analysis/10c_forest_zone_correlations.csv",
     "Coefficient",
     ["r_vs_Elevation", "p_vs_Elevation", "r_vs_Dist_from_ridge",
      "p_vs_Dist_from_ridge", "r_vs_Easting", "p_vs_Easting",
      "R2_elevation_only", "R2_elevation_plus_dist", "Marginal_gain",
      "R2_elevation_only_LOO"]),

    # 26b, 43.4%. Keyed on (cluster_label, scenario): ten rows are five
    # clusters times two UKCP18 scenarios, and the scenario is exactly what a
    # document means when it says "under the 2080s trajectory". The per-well
    # sibling adds `aggregation` for the same reason. The 120-row monthly
    # delta_h table is deliberately NOT registered — a per-month series is
    # working data, and registering it would propose noise rather than
    # citations.
    ("outputs/26b_van_willegen_msl_projections/26b_msl5_ukcp18_projection_summary.csv",
     ("cluster_label", "scenario"),
     # beta_1_recharge and beta_2_atmospheric_draw are OMITTED, following the
     # precedent above: 26b republishes the cluster SSM coefficients that
     # HEADLINE_TABLES already carries, and registering them here would check
     # one number twice under two keys. Left in, they were 176 of this table's
     # 181 proposals — the table's own quantities are the five MSL5 ones.
     ["spring_delta_h_mean_m",
      "msl5_observed_window_mean_m", "msl5_perturbed_window_mean_m",
      "msl5_shift_mean_m", "n_common_window_ends"]),
    ("outputs/26b_van_willegen_msl_projections/26b_msl5_ukcp18_projection_summary_perwell.csv",
     ("cluster_label", "scenario", "aggregation"),
     # same omission, same reason
     ["spring_delta_h_mean_m", "spring_delta_h_median_m", "n_wells"]),

    # 31, 39.4%. The validation summary is keyed on all three of tier, test and
    # descriptor: one descriptor is tested several ways and one test is applied
    # to several descriptors, so any pair of them collides. The k = 6 / linkage
    # robustness table is keyed on the whole specification for the same reason.
    ("outputs/31_cluster_validation/31_validation_summary.csv",
     ("tier", "test", "descriptor"), ["statistic", "p_value"]),
    ("outputs/31_cluster_validation/31_method_robustness_ari.csv",
     ("distance", "linkage", "k"), ["n_wells", "ARI_vs_canonical"]),
    ("outputs/31_cluster_validation/31b_separation_vs_recoverability.csv",
     ("descriptor", "column"), ["eta2_separation", "ari_recoverability"]),
    ("outputs/31_cluster_validation/31_forest_borderline.csv",
     "well", ["signed_dist_m"]),

    # ── Added 2026-09-03 (W101 follow-on). Two of the fourteen remaining
    # unregistered directories, taken first on RISK rather than on how many of
    # their numbers appear in the corpus.
    #
    # Script 17's specific yield is the file the project rules single out: two
    # Approach B aggregations exist and are NOT interchangeable — the
    # cluster-level Sy_event_median here, and the median of per-well event
    # estimates in Script 18 — and Sy is the only quantity lambda consumes
    # absolutely. A document quoting the wrong aggregation is a scientific
    # error, not a stale value, and nothing was watching either file.
    # Keyed on (Cluster, Corrected): the table carries seven rows, five
    # uncorrected and two corrected, so keying on Cluster alone would collapse
    # two different estimates of the same cluster onto one key — the Script 37
    # (window, variant) trap again.
    ("outputs/17_wtf_specific_yield/17_wtf_01_sy_estimates.csv",
     ("Cluster", "Corrected"),
     ["Sy_assumed", "Sy_OLS_winter", "Sy_OLS_SE", "Sy_OLS_R2",
      "Sy_event_median", "Sy_event_Q25", "Sy_event_Q75",
      "Sy_rapid_median", "Sy_rapid_CI_lo", "Sy_rapid_CI_hi"]),

    # Script 38's transect. Only the coast-minus-inland difference is
    # registered; the five per-well level columns are a working series, not
    # quoted values, and registering them would propose noise.
    #
    # This row used to carry a limit: the number the documents actually quote
    # from Script 38 — the AR(1)-corrected trend of -28.16 mm/yr, one of the
    # three grounds of the far-field ruling (D-105) — was in 38_results.txt, a
    # TEXT file no value table can reach. Script 38 v1.6.0 now emits
    # 38_report_numbers.csv, which collect_values() picks up by glob without
    # needing a row here, so the trend is gated and this entry covers only the
    # difference series it always did.
    ("outputs/38_coastal_transect/38_transect.csv", "year",
     ["diff_coast_inland_m"]),

    ("outputs/37_driver_validation/37_scale_factors_by_window.csv",
     ("window", "variant"),
     ["s_coast", "s_coast_ci_lo", "s_coast_ci_hi",
      "s_cf", "s_cf_ci_lo", "s_cf_ci_hi",
      "s_bl", "s_bl_ci_lo", "s_bl_ci_hi",
      "c", "c_ci_lo", "c_ci_hi", "r_squared", "n"]),

    # ── Added 2026-09-02 (T13). THE HEADLINE ANALYSIS WAS IN NO VALUE TABLE.
    # Of the whole Script 10 clearfell family only 10e_01 was registered, so
    # the +113 mm step, its CI, its p-value and the four-zone contrasts were
    # watched by nothing. Three stale numbers were found by hand on 2026-09-02
    # — report12's Edge step +33 against a committed 30, report10's pooled step
    # +28 against 24.1, and six report9 four-zone values whose R2 and N matched
    # the committed run while every coefficient and p-value did not. A full
    # cite_check run would have caught none of them.
    ("outputs/10_clearfell_baci/10a_01_ancova_comparison_table.csv", "Control",
     ["Clearfell_step_m", "Clearfell_CI_lo_m", "Clearfell_CI_hi_m", "Clearfell_p"]),
    ("outputs/10_clearfell_baci/10k_01_four_zone_results.csv", "zone",
     ["clearfell_step_m", "clearfell_ci_lo_m", "clearfell_ci_hi_m", "clearfell_p"]),
    ("outputs/10_clearfell_baci/10k_03_easting_sensitivity.csv", "zone",
     ["clearfell_step_m", "clearfell_p"]),
    ("outputs/10_clearfell_baci/10a_09_coastal_scale_factor.csv", "control_tier",
     ["s_coast", "s_coast_se", "coastal_differential_mm_yr"]),
    ("outputs/10_clearfell_baci/10a_10_coastal_fixed1_sensitivity.csv", "control_tier",
     ["clearfell_step_free_m", "clearfell_step_fixed1_m", "s_coast_fitted"]),

    # ── Added 2026-08-31 by the coverage sweep described in the v1.12.0 note.
    # Seven tables, each carrying quantities watched nowhere else. The cluster
    # betas are deliberately EXCLUDED from every one of them: they are already
    # in HEADLINE_TABLES, and re-registering them here would check one number
    # five times and tell the reader nothing.

    # The scenario parameter block. This is the file W100 caught carrying a
    # value that could not reproduce its own formula — thinning_b2_mult stored
    # at sixteen significant figures where seventeen were needed — and it had
    # no watcher of any kind at the time. The multipliers and Sy are quoted in
    # three documents. beta_1/2/3 and h_disp are omitted: HEADLINE_TABLES and
    # the Sy tables already carry them.
    ("outputs/01_data_prep/pipeline_scenario_params.csv", "Cluster",
     ["clearfell_b2_mult", "thinning_b2_mult",
      "broadleaf_b2_summer", "broadleaf_b2_winter"]),

    # The water-balance partition. The betas in this table are copies; the
    # partition itself — recharge, ET draw, drainage, residual and the two
    # percentages — exists only here and is quoted in report9 and report10.
    ("outputs/16_water_balance/16_water_bal_table.csv", "Label",
     ["Recharge_m_month", "ET_draw_m_month", "Drainage_m_month",
      "Total_loss_m_month", "Residual_m_month", "Drainage_pct", "ET_pct"]),

    # Per-well coefficient shifts across the clearfell. The SHIFTS are the
    # quantity — db1, db2, db3 — and they are quoted in report9; the before and
    # after levels are not, and registering them would triple the index for no
    # gain.
    ("outputs/10_clearfell_baci/10e_01_coefficient_shifts.csv", "Well",
     ["db1", "db2", "db3"]),

    # The driver footing table: peak, area-normalised and volumetric magnitudes
    # per driver, quoted in report9 and report13. Nothing else carries them.
    ("outputs/37b_driver_footing/37b_driver_footing.csv", "component",
     ["peak_mm", "area_mm_ha", "volume_m3"]),

    # ── Composite keys (the v1.12.0 change). Each of these has two rows per
    # label, so a single-column key silently collapsed them.
    ("outputs/03_state_space_model/03_14_centroid_window_sensitivity.csv",
     ("Cluster_Label", "basis"),
     ["R2", "LCSC_percent", "beta_3_pct_vs_full_record"]),
    ("outputs/26b_van_willegen_msl_projections/"
     "26b_msl5_ukcp18_projection_summary.csv",
     ("cluster_label", "scenario"),
     ["spring_delta_h_mean_m", "msl5_observed_window_mean_m",
      "msl5_perturbed_window_mean_m", "msl5_shift_mean_m"]),
    ("outputs/21_forestry_scenarios/21_forestry_04_baci_zone_means.csv",
     ("Zone", "Phase"),
     ["Mean_depth_m", "Median_depth_m", "SD_depth_m",
      "Min_depth_m", "Max_depth_m"]),
]


def _key_label(row, kcol) -> str:
    """The vocabulary a report line uses to name one cell of a value table.

    `kcol` is a column name, or a tuple of them for a table whose rows are
    identified by a pair. Joined with " / " so the report reads
    "C4 (Main Forest) / comparison_window · R2".
    """
    if isinstance(kcol, (tuple, list)):
        return " / ".join(str(row[c]) for c in kcol)
    return str(row[kcol])


def _key_columns(kcol) -> list:
    return list(kcol) if isinstance(kcol, (tuple, list)) else [kcol]

# Claims register. rule is evaluated against the named CSV.
#   argmin:<col>  / argmax:<col>  -> `expect` must be the value of `key_col`
# Extend this rather than restating a claim in prose.
CLAIMS_REGISTER = "tools/claims_register.csv"

# Exact citation index, built by tools/build_citation_index.py. Each row says
# "key K is quoted in document D as the literal string S". When the index has a
# row, the check is EXACT — no proximity guessing, no near-miss heuristic. The
# heuristic scan is then only for values the index does not yet cover.
CITATION_INDEX = "tools/citation_index.csv"

# Adjudicated false positives.
#
# The index locates a citation by its VALUE plus a slice of surrounding
# characters. Inside a wide table that is not enough: "1.83" in the Methods
# Supplement is a Durbin-Watson statistic, not a beta-2, and the neighbouring
# characters in a run of table cells look like any other run of table cells. On
# 2026-08-26 every value this check reported against the Methods Supplement, the
# Supplementary Material and report9 turned out to be one of these — a table
# cell, a confidence-interval bound, or a different quantity that happens to
# round the same way.
#
# The cost of not recording that is that the same eleven have to be
# re-adjudicated, by hand, on every run — and the reader learns to skim a
# gating check, which is worse than the check not existing.
#
# A row here is a claim that EVERY occurrence of that string in that document
# has been looked at and none of them is the citation. Not "the located one
# looked wrong": all of them. `what_it_actually_is` must say what the number
# really is, so the judgement can be re-examined rather than taken on trust.
#
# Remove a row when the document changes: a rewrite can put a real citation of
# that value into a document that previously only had coincidences.
CITATION_FALSE_POSITIVES = "tools/citation_false_positives.csv"


def load_false_positives() -> dict:
    """{(key, document, quoted): what_it_actually_is}"""
    path = REPO / CITATION_FALSE_POSITIVES
    if not path.exists():
        return {}
    import csv as _csv
    out = {}
    with path.open(encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            out[(row["key"].strip(), row["document"].strip(),
                 row["quoted"].strip())] = row.get("what_it_actually_is", "").strip()
    return out


_FALSE_POSITIVES = load_false_positives()

# Archived output trees produced by no live script — their values are history,
# not current publications, so they must not drive a staleness verdict.
EXCLUDE_OUTPUT_DIRS = ("30_c4_constrained_fit",)

# A rendering is searchable only if it carries enough significant digits to be
# distinctive. "0.02" matches thousands of unrelated places; "0.0183" does not.
MIN_SIG_DIGITS = 3

# Significant digits alone are not enough. In documents dense with per-well
# tables almost any 3-digit value collides with SOMETHING: the first triage run
# reported 14 hits above a 1% gap and all 14 were coincidences — a BACI spring
# shift "matched" the upper end of a cluster's beta_3 range, a p-value "matched"
# a seasonal amplitude in metres. A near miss is evidence only when it sits near
# a token identifying the quantity. Anchors are derived from the key.
ANCHOR_WINDOW = 400          # characters either side of the candidate number
_STOPWORDS = {
    "mean", "median", "shift", "after", "before", "step", "pct", "percent",
    "delta", "diff", "value", "total", "count", "min", "max", "range", "sum",
    "headline", "resid", "residual", "impact", "control", "ctrl", "model",
    "spring", "summer", "winter", "annual", "monthly", "per", "well", "wells",
    "cluster", "vs", "and", "the", "for", "with", "from", "test", "fit",
    "depth", "minimum", "maximum", "coeff", "intercept", "slope", "weight",
    # cluster-label words: they appear on every row of every per-well table
    "forest", "dune", "lake", "edge", "coastal", "residual", "western", "main",
    "warren", "reference", "extended", "calibration",
}


# Some keys need a PHRASE, not a token. The manifest counts are the case: they
# are small integers, and "49" sits near the word "steps" both when a document
# states the step COUNT and when it names step 49. A single-token anchor cannot
# tell those apart and floods the triage list with step indices. Where a key
# appears here, anchored() requires one of these phrases in the window instead
# of any derived token, and the phrase is matched with the number's own position
# so "50 steps" counts and "step 50" does not.
ANCHOR_PHRASES: dict[str, tuple[str, ...]] = {
    "pipeline_steps_registered": (
        "registered steps", "registered pipeline steps", "steps across",
        "steps in order", "-step", "step reproducible", "all {n} steps",
        "same {n} steps", "scripts ({n} steps", "total registered steps",
    ),
    "pipeline_phases_total": (
        "across {n} phases", "{n} phases", "phases 1-{n}", "phases 1--{n}",
    ),
    # These two need the NUMBER in the phrase. "analytical" and "default pass"
    # both sit beside step indices — "steps 36-41/50, all analytical-default" —
    # and a phrase that does not pin the number matches those too.
    "pipeline_steps_analytical": (
        "{n} analytical", "analytical top-level: {n}", "tier: {n}",
    ),
    "pipeline_steps_default": (
        "{n} in a default", "{n} run in a default", "execution: {n}",
        "default-exec {n}",
    ),
    "pipeline_steps_display": ("{n} display/utility",),
    "pipeline_steps_diagnostic": ("{n} diagnostic",),
    "pipeline_steps_optin": ("{n} opt-in", "{n} only under", "{n} only behind"),
}

PHRASE_WINDOW = 60           # characters either side, for phrase anchors


def phrase_anchored(text: str, needle: str, phrases) -> bool:
    """True if `needle` occurs with one of `phrases` close by.

    Deliberately tighter than anchored(): the window is a phrase's worth of
    characters, not a paragraph's, because the whole point is to separate a
    count from an index that sits near the same vocabulary.
    """
    low = text.lower()
    want = [ph.replace("{n}", needle).lower() for ph in phrases]
    for start, end in number_spans(text, needle):
        window = low[max(0, start - PHRASE_WINDOW): end + PHRASE_WINDOW]
        if any(w in window for w in want):
            return True
    return False


# A key often names BOTH a subject and a quantity — CoeffShift_CEH2_b1_before is
# well CEH2 and coefficient β₁. The subject alone is a weak anchor: report10 says
# "β₂ = 2.628 at NW10 is below CEH2 (β₂ = 2.891)", and a scan anchored on "CEH2"
# alone reads that 2.628 as a stale rendering of CEH2's β₁. Requiring a quantity
# marker too rejects it, because the quantity in that sentence is β₂.
#
# The coefficient shorthands never appear in prose in the form the CSV keys use,
# so the key's own token cannot do the work; this is the translation.
_QUANTITY_FORMS = {
    "b1": ["β₁", "beta_1", "beta 1", "recharge sensitivity"],
    "b2": ["β₂", "beta_2", "beta 2", "atmospheric draw"],
    "b3": ["β₃", "beta_3", "beta 3", "drainage coefficient", "drainage decay"],
    "r2": ["r²", "r2"],
    "sy": ["specific yield", "sy"],
    "nse": ["nse", "nash"],
    "se": ["standard error", "se"],
    "p": ["p ="],
}


def anchor_groups(key: str) -> tuple[list[str], list[str]]:
    """(subject anchors, quantity anchors) from a report-numbers key.

    Subjects are well and cluster ids — what the number is ABOUT. Quantities are
    the topic words and the coefficient shorthands — what the number IS. A key
    carrying both must match both, because a sentence naming the subject while
    reporting a different quantity is the commonest false positive in the sweep.
    """
    subj, quant = [], []
    for t in re.split(r"[_\W]+", key):
        if not t or t.lower() in _STOPWORDS:
            continue
        low = t.lower()
        if re.fullmatch(r"(?i)(ceh|nw|wmc|lis|fe|d|t)\d+[a-z]?", t):
            subj.append(t)                      # well id
        elif re.fullmatch(r"(?i)c[1-5]", t):
            subj.append(t)                      # cluster id
        elif low in _QUANTITY_FORMS:
            quant.extend(_QUANTITY_FORMS[low])
        elif t.isupper() and len(t) >= 3:
            quant.append(t)                     # acronym: BACI, ANCOVA, MSL...
        elif len(t) >= 5 and not t.isdigit():
            quant.append(t)                     # topic word
    return subj, quant


def anchors(key: str) -> list[str]:
    """Flat anchor list — kept for callers that do not need the split."""
    subj, quant = anchor_groups(key)
    return subj + quant


def anchored(text: str, needle: str, keys: list[str],
             key: str | None = None, strict: bool = False) -> bool:
    """True if `needle` occurs anywhere within ANCHOR_WINDOW of an anchor.

    A key listed in ANCHOR_PHRASES bypasses the token test entirely and must
    satisfy the tighter phrase test instead.

    `strict` demands a SUBJECT anchor and a QUANTITY anchor, not just either.
    The burden of proof scales with how speculative the claim is: finding the
    exact committed value near the well id is strong evidence the document is
    citing that number, so the exact-hit scan stays permissive. A NEAR MISS is
    weak evidence — it says "a different number sits near this well id" — and
    applied permissively it reports every other coefficient in the sentence.
    Demanding the quantity there costs nothing real and removes the commonest
    false positive in the triage list.
    """
    if key and key in ANCHOR_PHRASES:
        return phrase_anchored(text, needle, ANCHOR_PHRASES[key])
    if not keys:
        return True
    low = text.lower()
    subj, quant = anchor_groups(key) if key else ([], [])
    # When the key names both a subject and a quantity, demand both. When it
    # names only one, fall back to the flat any-match — tightening a key that
    # has nothing to tighten with only loses sensitivity.
    if strict and subj and quant:
        lowsubj = [k.lower() for k in subj]
        lowquant = [k.lower() for k in quant]
        for start, _end in number_spans(text, needle):
            window = low[max(0, start - ANCHOR_WINDOW): start + ANCHOR_WINDOW]
            if any(k in window for k in lowsubj) and any(k in window for k in lowquant):
                return True
        return False
    lowkeys = [k.lower() for k in keys]
    for start, _end in number_spans(text, needle):
        window = low[max(0, start - ANCHOR_WINDOW): start + ANCHOR_WINDOW]
        if any(k in window for k in lowkeys):
            return True
    return False


def _sig_digits(s: str) -> int:
    return len(re.sub(r"[^1-9]", "", s.lstrip("-0.").replace(".", "")) or "") + \
        len(re.findall(r"(?<=[1-9])0", s.replace(".", "")))


# Keys whose values are short whole numbers and would fail the significant-digit
# test, but which carry strong anchors ("pipeline", "steps", "phases") so a
# two-digit match near one of them is a citation rather than a coincidence. The
# manifest counts are the whole of this exception: they are the most-repeated
# numbers in the corpus and the general rule was hiding every one of them.
SHORT_VALUE_KEY_PREFIXES = ("pipeline_",)


def searchable(s: str, key: str | None = None) -> bool:
    digits = re.sub(r"[^0-9]", "", s).lstrip("0")
    if len(digits) >= MIN_SIG_DIGITS:
        return True
    if key and key.startswith(SHORT_VALUE_KEY_PREFIXES) and len(digits) >= 2:
        return True
    return False


# ---------------------------------------------------------------------------
# What counts as the corpus quoting a number
# ---------------------------------------------------------------------------
# `s in text` is a substring test, not a citation test, and a document is full
# of substrings that merely look like values. Three families account for
# nearly all of them:
#
#   EMBEDDED    the digits sit inside a longer number. 0.135 inside the frame
#               height 10.135cm; 1.29 inside 11.298cm; 1.76 inside the summer
#               minimum -1.766 m; 30 inside "R2 <= 0.30"; 3.30 inside 13.30.
#   GEOMETRY    the number is a page-layout dimension, not a measurement:
#               width="15.45cm", height="10.956cm". strip_markup() removes HTML
#               attributes but not the pandoc `{width=... height=...}` blocks
#               the mirrors are full of.
#   CROSS-REF   the number names a document part, not a quantity: "Figure 30",
#               "Figure 65", "Table 9".
#
# A phantom is not merely noise. It corrupts the verdict in BOTH directions: a
# phantom exact hit reports a value as "cited and current" when no document
# quotes it - masking a real omission - and a phantom near miss puts a healthy
# value on the triage list. Measured on the 2026-08-20 tree: 13 of 55 triage
# rows and 26 exact "cited and current" verdicts were substring artefacts, and
# 10 of the 59 locatable citation-index rows were being checked at a string
# that is not the citation.
#
# On signs: this corpus writes the Unicode minus U+2212 while render() emits an
# ASCII hyphen, and beta_2 is STORED positive but QUOTED negative (the design
# matrix negates PET). Sign agreement is therefore deliberately NOT required -
# a leading +, - or U+2212 is treated as a sign, so it neither breaks the
# numeric boundary nor has to match. What the boundary rule cares about is
# digits, not signs.

# Context immediately before the number that means it is not a citation.
_FRAME_ATTR = re.compile(r"(?i)(?:width|height)\s*[=:]\s*[\"']?$")
_XREF_LABEL = re.compile(
    r"(?i)\b(?:figure|fig|table|section|chapter|appendix|equation|eq|panel|"
    r"plate)s?\.?\s*$")
# Context immediately after: a typesetting unit glued to the digits. Units this
# project actually publishes in (m, mm, %, days) are never glued this way.
_TYPESET_UNIT = re.compile(r"(?i)^(?:cm|px|pt|em|ex)\b")

_CONTEXT_LOOKBEHIND = 40         # characters of preceding text the rules see


def _is_whole_number(text: str, start: int, end: int) -> bool:
    """True if text[start:end] is a complete number, not part of a longer one.

    Rejects a neighbouring digit on either side, a decimal point or thousands
    comma that itself has a digit beyond it (so "30" inside "0.30" and "234"
    inside "1,234" both fail), and a preceding ASCII letter, which is how a
    number glues to an identifier: "30" inside "CEH30", "3" inside "WMC3".
    """
    prev = text[start - 1] if start else ""
    nxt = text[end] if end < len(text) else ""
    if prev.isdigit() or nxt.isdigit():
        return False
    if prev in ".," and start >= 2 and text[start - 2].isdigit():
        return False
    if nxt in ".," and end + 1 < len(text) and text[end + 1].isdigit():
        return False
    if "a" <= prev.lower() <= "z":
        return False
    return True


def _citable_context(text: str, start: int, end: int) -> bool:
    """True unless the surrounding text says this number is not a quantity."""
    before = text[max(0, start - _CONTEXT_LOOKBEHIND):start]
    if _FRAME_ATTR.search(before) or _XREF_LABEL.search(before):
        return False
    if _TYPESET_UNIT.match(text[end:end + 6]):
        return False
    return True


# THE MINUS SIGN. render() writes an ASCII hyphen; the corpus writes U+2212.
# `re.escape("-31.3")` therefore matched NOTHING, in any document, for any
# negative value — and 529 of the committed values are negative. Measured on
# 2026-08-23: 40 matched, and 69 more appeared the moment the glyph was
# normalised, among them trend_summer_balance, the ANCOVA clearfell steps and
# the summer-minimum depths. That is why report8 and report9 could disagree
# about δ₀ = 31.3 versus 29.0 with the gate green.
#
# The substitution is character-for-character, so match offsets stay valid and
# _is_whole_number and _citable_context still see the same positions.
_MINUS_CLASS = "[-\u2212\u2013\u2010\u2011\u2012\u2014]"


def _minus_tolerant(needle: str) -> str:
    # Most needles have no sign at all, and a character class per character is
    # measurably slower than a literal across 1,700 values x 30 documents — the
    # citations pass went from comfortable to over the bridge's timeout. Only
    # pay for the class when there is a minus to be tolerant about.
    if "-" not in needle:
        return re.escape(needle)
    return "".join(_MINUS_CLASS if ch == "-" else re.escape(ch) for ch in needle)


def number_spans(text: str, needle: str):
    """Yield (start, end) for each occurrence of `needle` that is a whole
    number in a context where a number can be a citation."""
    for m in re.finditer(_minus_tolerant(needle), text):
        if _is_whole_number(text, m.start(), m.end()) and \
                _citable_context(text, m.start(), m.end()):
            yield m.start(), m.end()


def quotes(text: str, needle: str) -> bool:
    """True if the document quotes `needle` as a number. Use this, never
    `needle in text`."""
    return next(number_spans(text, needle), None) is not None


# Context relocation. build_citation_index.py stores CTX characters either side
# of each indexed citation, whitespace-normalised, precisely so the row can be
# re-found when a document has several renderings of the same string - and
# until now nothing read them except the DRIFTED printout. Scoring the stored
# slices against each candidate occurrence points the check at the citation the
# row is actually about.
_CONTEXT_SCAN = 120              # characters of document context compared


def _norm_ctx(s: str) -> str:
    """Normalise a context slice. Whitespace collapses (matching
    build_citation_index.norm) and backslashes are dropped: the mirrors gained
    pandoc escaping (`h\\_min`) after parts of the index were built, and the
    escape is not part of the text the citation sits in."""
    return " ".join(s.replace("\\", "").split()).lower()


def _common_tail(a: str, b: str) -> int:
    n = 0
    while n < min(len(a), len(b)) and a[-1 - n] == b[-1 - n]:
        n += 1
    return n


def _common_head(a: str, b: str) -> int:
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n


def _context_score(text: str, span: tuple[int, int], before: str,
                   after: str) -> int:
    """Characters of agreement between the stored context slices and the text
    actually surrounding `span`. Zero means the string is present but nowhere
    near where the index row recorded it."""
    s, e = span
    return (_common_tail(_norm_ctx(text[max(0, s - _CONTEXT_SCAN):s]),
                         _norm_ctx(before))
            + _common_head(_norm_ctx(text[e:e + _CONTEXT_SCAN]),
                           _norm_ctx(after)))


def locate(text: str, quoted: str, before: str = "",
           after: str = "") -> tuple[int, int] | None:
    """Span of the occurrence of `quoted` an index row points at, or None.

    With no stored context this is simply the first citable occurrence. With
    context it is the occurrence whose surroundings agree with the stored
    slices best. A poor best score is not grounds for rejection: prose gets
    rewritten around a number that is still cited, and the mirrors' escaping
    has changed since parts of the index were built.
    """
    spans = list(number_spans(text, quoted))
    if not spans:
        return None
    if not (before or after):
        return spans[0]
    return max(spans, key=lambda sp: _context_score(text, sp, before, after))


# An HTML tag: opens with a letter (element) or "!" (comment/doctype) and, in
# particular, contains NO further "<". That exclusion is load-bearing. The
# earlier pattern <[^>]+> matched from any "<" to the next ">" anywhere in the
# file, and the mirrors are full of bare less-than signs — every "p < 0.001" in
# a statistics table. One such "<" swallowed everything up to the next ">",
# which was typically hundreds of lines later, deleting whole tables of cited
# values before the checker ever saw them: report9 stripped from 267 kB to
# 97 kB, and 117 indexed citations were reported MOVED when the numbers were
# sitting in the document all along. Silent blindness, not noise — a drifted
# value inside a swallowed table could never have been caught. See D-018.
_MARKUP = re.compile(r"</?[A-Za-z!][^<>]*>")
_IMGREF = re.compile(r"!?\[[^\]]*\]\([^)]*\)")   # markdown links / images


def strip_markup(text: str) -> str:
    """Remove markup so only prose and table CONTENT is searched.

    The mirrors carry raw HTML for figures and tables. Without this, a CSS
    dimension (style="height:10.118cm") or an image filename is a searchable
    number, and every one of them is a false positive waiting to happen.
    """
    return _IMGREF.sub(" ", _MARKUP.sub(" ", text))


def load_documents() -> dict[str, str]:
    docs: dict[str, str] = {}
    for g in DOC_GLOBS:
        for p in REPO.glob(g):
            if _excluded(str(p.relative_to(REPO))):
                continue
            try:
                docs[str(p.relative_to(REPO))] = strip_markup(
                    p.read_text(encoding="utf8"))
            except OSError:
                pass
    return docs


def render(v: float, dp: int) -> str:
    return f"{v:.{dp}f}"


def near_misses(v: float, dp: int, span: int) -> list[str]:
    """Renderings within `span` units of the last decimal place, excluding v.

    "Excluding v" has to mean excluding v's own RENDERING, not merely skipping
    k = 0. Binary floating point breaks the two apart: 2.0865 renders at three
    decimals as "2.087", and so does 2.0865 + 0.001, because that sum is really
    2.08749999999999991. So the correct rendering was being generated as a near
    miss of itself, and every document quoting the number correctly was reported
    as drifted. That accounted for most of a 200-row triage list, all of it
    under a 1 % gap, and it is why the list had stopped being read.
    """
    step = 10 ** -dp
    self_render = render(v, dp)
    out = []
    for k in range(-span, span + 1):
        if k == 0:
            continue
        r = render(v + k * step, dp)
        if r != self_render and r not in out:
            out.append(r)
    return out


def collect_values() -> list[tuple[str, str, float]]:
    """[(source, label, value)] from report-numbers files and headline tables."""
    vals: list[tuple[str, str, float]] = []
    for p in sorted(REPO.glob("outputs/**/*report_numbers*.csv")):
        if any(d in p.parts for d in EXCLUDE_OUTPUT_DIRS):
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = {c.lower(): c for c in df.columns}
        kcol = cols.get("key") or df.columns[0]
        ucol = cols.get("unit")
        vcol = cols.get("value")
        if vcol is None:
            num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if not num:
                continue
            vcol = num[0]
        for _, r in df.iterrows():
            try:
                rel = str(p.relative_to(REPO))
                lab = str(r[kcol])
                vals.append((rel, lab, float(r[vcol])))
                if ucol is not None:
                    u = str(r[ucol]).strip()
                    if u and u.lower() != "nan":
                        VALUE_UNITS[(rel, lab)] = u
            except (TypeError, ValueError):
                continue
    # Manifest counts. These are the most-repeated numbers in the corpus and
    # had no key, so nothing checked them: run_analysis.py guards its own
    # _DOCUMENTED_COUNTS internally, but that guard never reached the prose.
    # Sourced from the committed manifest so the documents are checked against
    # what the pipeline actually registered, not against a second declaration.
    man = REPO / "outputs" / "pipeline_manifest.json"
    if man.exists():
        try:
            m = json.loads(man.read_text(encoding="utf8"))
            flat = {k: v for k, v in m.items() if isinstance(v, (int, float))}
            for grp in ("by_tier", "by_exec"):
                for k, v in (m.get(grp) or {}).items():
                    if isinstance(v, (int, float)):
                        flat[f"{grp}.{k}"] = v
            # Key names are chosen so anchors() derives the words the
            # DOCUMENTS use — "pipeline", "steps", "phases" — rather than the
            # manifest's own field names. A near miss is only reported when it
            # sits near an anchor, so "49 steps across 17 phases" is invisible
            # to a key anchored on "registered" and "total".
            rename = {
                "total_registered":            "pipeline_steps_registered",
                "total_phases":                "pipeline_phases_total",
                "analytical_phases":           "pipeline_phases_analytical",
                "scraping_substeps":           "pipeline_scraping_substeps",
                "clearfell_substeps":          "pipeline_clearfell_substeps",
                "by_tier.analytical_toplevel": "pipeline_steps_analytical",
                "by_tier.display_utility":     "pipeline_steps_display",
                "by_tier.optin_diagnostic":    "pipeline_steps_diagnostic",
                "by_exec.default":             "pipeline_steps_default",
                "by_exec.optin":               "pipeline_steps_optin",
            }
            for k, v in flat.items():
                name = rename.get(k, f"pipeline_{k}")
                # Only counts with a phrase anchor are registered. A small
                # integer without one cannot be told from a step index and
                # would report every occurrence of "13" in the corpus. Two are
                # deliberately absent: analytical_phases, which the working
                # rules say is emitted for completeness and cited nowhere, and
                # the sub-step counts, which appear only as ranges.
                if name not in ANCHOR_PHRASES:
                    continue
                vals.append(("outputs/pipeline_manifest.json", name, float(v)))
        except (OSError, ValueError):
            pass

    for rel in CONSTANT_SOURCES:
        f = REPO / rel
        if not f.exists():
            continue
        for m in _CONSTANT_RE.finditer(f.read_text(encoding="utf8")):
            vals.append((rel, m.group(1), float(m.group(2))))

    for rel, kcol, vcols in list(HEADLINE_TABLES) + list(EXTRA_VALUE_TABLES):
        p = REPO / rel
        if not p.exists():
            continue
        df = pd.read_csv(p)
        for _, r in df.iterrows():
            for c in vcols:
                try:
                    _v = float(r[c])
                except (TypeError, ValueError, KeyError):
                    continue
                # A BLANK CELL IS NOT A PUBLISHED VALUE. csv reads it as "" and
                # skips it; pandas reads it as NaN and float(NaN) succeeds, so
                # without this guard an empty cell registers as a value — and
                # where two rows share a key label, the NaN silently overwrites
                # the real number. 10c's correlations file stacks two blocks
                # separated by a blank row, so beta_2 and beta_3 each appear
                # twice with DISJOINT columns populated; every R2 in it read
                # back as nan and four true citations in report9 and Paper 1
                # were reported as drifted against it.
                if not math.isfinite(_v):
                    continue
                vals.append((rel, f"{_key_label(r, kcol)} · {c}", _v))
    return vals


# ---------------------------------------------------------------------------
# SPREAD — one quantity, several renderings
# ---------------------------------------------------------------------------
# Every other check in this file asks "does the corpus quote the committed
# value?". That question has a blind spot: a quantity the documents deliberately
# round — a modelled reach stated to the nearest tens of metres, say — never
# equals the CSV at any searched precision, so it lands in the uncited bin and
# no check ever looks at it again. Meanwhile the documents are free to disagree
# with each other, and they do.
#
# SPREAD asks the other question: does the corpus quote the SAME value
# everywhere? It collects every rendering that sits near the quantity's anchor
# and reports the distinct set. More than one member is the finding.
#
# Each register entry is (anchor phrases, window, relative band, exclusions):
#   anchors     one must appear within `window` characters of the number. For a
#               quantity with a symbol, the symbol is the anchor — it is far
#               tighter than the key's own vocabulary.
#   window      characters either side. Deliberately small; a paragraph-sized
#               window sweeps in every other number in the paragraph.
#   band        renderings are kept only within this relative distance of the
#               committed value, so an unrelated number near the same symbol is
#               not mistaken for a rendering of this quantity.
#   exclusions  a phrase in the window that means this occurrence is a DIFFERENT
#               quantity sharing the symbol. λ names both the drawdown reach and
#               the scraping covariate; the register is where they are separated,
#               and tools/symbol_register.csv carries the same distinction for
#               the symbol audit.
LARGE_VALUE_MIN = 100.0

# Documents whose job is to record what a value USED to be. A spread check on
# them reports the history as though it were disagreement, which inverts their
# purpose: the Decision Log and the ledgers are where a superseded number is
# supposed to survive. They stay inside every other check.
# Documents whose job is to record what a value USED to be. Checking them for
# CURRENCY inverts their purpose: a decision entry that no longer quotes the
# number it overturned has stopped being a record. The spread check has excluded
# them since it was written; the CITATION check did not, and on 2026-09-03 the
# index builder duly proposed 17 rows in the Decision Log and PARTITION_HISTORY
# — rows that would have gone red precisely when they were doing their job.
# PARTITION_HISTORY joins the list for the same reason: it states in its own
# header that the April text is preserved wherever it still holds.
HISTORY_DOCS = ("DECISION_LOG.md", "NUMBER_LEDGER.md",
                "SCRIPT_LEDGER.md", "FIGURE_LEDGER.md",
                "PARTITION_HISTORY.md")

# Kept as an alias: the spread check reads this name, and the two exclusions are
# the same idea rather than a coincidence.
SPREAD_EXCLUDE_DOCS = HISTORY_DOCS

QUANTITY_ANCHORS = {
    # The forest/scrape reach. λ also names the scraping BACI covariate and the
    # P_flood rainfall multiplier, so the exclusions carry the same sense
    # separation that tools/symbol_register.csv carries for the symbol audit.
    "drawdown_lambda": (["λ"], 40, 0.15,
                        ["scraping", "covariate", "spans roughly", "sensitivity",
                         "500 m", "p_flood", "p\\_flood", "multiplier"]),
    # The coastal fit's parameters, quoted rounded in six passages across three
    # chapters and previously drifted by a whole generation of the fit (D-047,
    # D-039). δ₀ is the shoreline amplitude, not the headline; the headline is
    # quoted at the reference distance and is registered separately.
    "Headline_fit_delta_0": (["δ₀"], 45, 0.12,
                             ["150 m", "reference distance", "95 % ci", "95% ci"]),
    "Headline_coastal_rate_at_ref": (["coast-edge trend", "at the 150 m",
                                      "reference distance"], 90, 0.12, []),
    "Headline_fit_L": (["reach", "strip-aquifer width", "inland over"], 45, 0.10,
                       # 2√(Dt) is the diffusive length-scale of the sea-level-rise
                       # field, and a cluster's mean distance to the coast is a
                       # position, not the reach. Both sit next to the word "reach".
                       ["scraping", "λ", "√(dt)", "mean distance", "roughly 900",
                        "about 900", "≈ 900"]),
}

# A leading minus is only a minus when nothing precedes it. In the pandoc
# mirrors an en dash is written "--", so "16--17" was yielding "-17" as a
# negative number and the phase count appeared to disagree with itself.
_NUMERIC = re.compile(r"(?<![\w.\-–—])(-?\d+(?:\.\d+)?)(?![\w.])")


_NUM_INDEX: list | None = None       # [(abs_value, doc, rendering, start, end)]
_NUM_KEYS: list | None = None        # the magnitudes alone, for bisect


def _number_index(docs) -> list:
    """Every numeric token in the corpus, once, sorted by magnitude.

    --spread-all asks the same question of a thousand values. Rescanning the
    corpus per value is a thousand passes; indexing once and bisecting into the
    band is one. Built lazily so the default run pays nothing extra.
    """
    global _NUM_INDEX, _NUM_KEYS
    if _NUM_INDEX is None:
        idx = []
        for doc, text in sorted(docs.items()):
            if doc.split("/")[-1] in SPREAD_EXCLUDE_DOCS:
                continue
            for m in _NUMERIC.finditer(text):
                try:
                    x = abs(float(m.group(1)))
                except ValueError:
                    continue
                idx.append((x, doc, m.group(1), m.start(), m.end()))
        idx.sort(key=lambda r: r[0])
        _NUM_INDEX = idx
        _NUM_KEYS = [r[0] for r in idx]
    return _NUM_INDEX


def renderings_near(docs, value, anchor_list, window, band, excludes,
                    require_all=False):
    """{rendering: [documents]} for every number near an anchor and in band."""
    idx = _number_index(docs)
    keys = _NUM_KEYS
    lo, hi = abs(value) * (1 - band), abs(value) * (1 + band)
    out: dict[str, list[str]] = defaultdict(list)
    lowanchors = [a.lower() for a in anchor_list]
    lowex = [e.lower() for e in excludes]
    for x, doc, rendering, start, end in idx[bisect_left(keys, lo):
                                             bisect_right(keys, hi)]:
        text = docs[doc]
        win = text[max(0, start - window): end + window].lower()
        ok = (all(a in win for a in lowanchors) if require_all
              else any(a in win for a in lowanchors))
        if not ok:
            continue
        if any(e in win for e in lowex):
            continue
        out[rendering].append(doc)
    return out


def generic_anchors(key: str):
    """Fallback register entry for --spread-all: the key's own vocabulary.

    Far stricter than a registered entry, and it has to be. A registered entry
    anchors on the quantity's own symbol, which is unambiguous; a key's tokens
    are words like "C3" and "NSE" that sit near dozens of unrelated numbers. So
    the fallback demands EVERY token inside a tight window and a 2 % band, and
    even then this mode is a way of finding quantities that DESERVE a register
    entry, not a findings list. Anything it surfaces should be read, checked by
    hand, and then registered properly with its own anchor.
    """
    toks = anchors(key)
    if len(toks) < 2:
        return None
    return (toks, 60, 0.02, [], True)


def check_spread(docs, values, spread_all=False, gate=False) -> int:
    print("=" * 78)
    print("SPREAD — does the corpus quote the same value everywhere?")
    print("=" * 78)
    print("  A quantity the documents round never matches the CSV at any searched"
          "\n  precision, so the other checks cannot see it disagree with itself."
          "\n  More than one rendering near the same anchor is the finding.")
    seen, hits = set(), 0
    for source, label, v in values:
        if not (abs(v) > 0) or (label, v) in seen:
            continue
        seen.add((label, v))
        entry = QUANTITY_ANCHORS.get(label)
        if entry is None:
            if not spread_all:
                continue
            entry = generic_anchors(label)
            if entry is None:
                continue
        found = renderings_near(docs, v, *entry)
        if len(found) <= 1:
            continue
        hits += 1
        print(f"\n  {label}   committed {v:g}   ({source})")
        for r, where in sorted(found.items(), key=lambda kv: -len(kv[1])):
            docs_ = sorted({d.split("/")[-1] for d in where})
            print(f"      {r:>10s}  x{len(where):<3d} {', '.join(docs_)}")
    if not hits:
        print("\n  No registered quantity is rendered inconsistently.")
    else:
        print(f"\n  {hits} quantity(ies) rendered inconsistently across the corpus.")
        if not gate:
            print("  Advisory — pass --spread-gate to make this a gating check.")
    return hits if gate else 0


# ---------------------------------------------------------------------------
# M31 — metre-stored values quoted in millimetres
# ---------------------------------------------------------------------------
# Populated by collect_values() from the report-numbers Unit column. Keyed on
# (source, label) because the same label appears in more than one CSV and the
# unit is a property of the row, not of the name.
VALUE_UNITS: dict[tuple[str, str], str] = {}

METRE_UNITS = {"m"}          # only the bare metre. m/yr, m/month and the like
                             # are rates and are not converted.
_MM_SUFFIX = re.compile(r"\s{0,2}mm\b")
# A DENOMINATED mm is a rate, not a length, and a rate is not 1000x a stored
# metre value — METRE_UNITS admits only the bare metre for exactly that reason.
# But `\bmm\b` matches "mm" in "mm/month" and "mm yr⁻¹" too, because "/" and " "
# are both word boundaries. Measured 2026-08-28: 13 of the 33 false rows on the
# millimetre pass were denominated units, including all three `_se` keys, which
# collided 3-for-3 with cluster trends in mm yr⁻¹.
# `w.e.` (water equivalent) is itself a length, so it is skipped over rather
# than rejected — what matters is whether a denominator follows it.
_MM_DENOM = re.compile(
    r"\s{0,3}(?:w\.e\.)?\s{0,3}(?:/|per\b|yr\b|month\b|day\b|a\b|⁻¹|-1\b)", re.I)


def quotes_as_mm(text: str, needle: str) -> bool:
    """True if the document quotes `needle` as a number followed by an mm unit.

    The unit token is the whole guard against a bare 1000x sweep. Requiring it
    is what takes the candidate pool from 483 occurrences to 105.
    """
    for a, b in number_spans(text, needle):
        m = _MM_SUFFIX.match(text, b)
        if not m:
            continue
        if _MM_DENOM.match(text, m.end()):
            continue                      # mm/month, mm yr⁻¹ — a rate
        return True
    return False


def mm_renderings(v: float) -> list[str]:
    """Millimetre renderings of a metre-stored value, at >= 3 sig digits.

    Unsigned: the corpus writes U+2212 for a minus, and some quantities are
    stored positive and quoted negative. number_spans() decides whether the
    digits are a number; the sign is not part of the match.
    """
    out = []
    mm = abs(v) * 1000.0
    for dp in (0, 1, 2):
        cands = [render(mm, dp)]
        # BANKER'S ROUNDING. Python renders 194.5 as "194" (ties-to-even), so a
        # corpus correctly writing "+195 mm" was never searched for and the gate
        # went hunting an unrelated value instead. Found 2026-08-28: the CEH36
        # paired-BACI shift, 0.1945 m, stated correctly as 195 mm in four
        # documents and as 165 mm in two, and M31 saw none of it. Every value
        # ending .5 at the searched precision had the same hole.
        import decimal as _d
        cands.append(str(_d.Decimal(repr(mm)).quantize(
            _d.Decimal(1).scaleb(-dp), rounding=_d.ROUND_HALF_UP)))
        for c in cands:
            if searchable(c) and c not in out:
                out.append(c)
    return out


def check_numbers(docs, dps, span, min_rel=0.0, csv_out=None) -> int:
    print("=" * 78)
    print("NUMBERS — every published value vs the corpus")
    print("=" * 78)
    stale, uncited, ok = [], [], 0
    mm_hits: list[tuple[str, str, float, str, list[str]]] = []
    seen: set[tuple[str, float]] = set()
    for source, label, v in collect_values():
        if not (abs(v) > 0):
            continue
        # 10_consolidated_report_numbers.csv republishes the per-script 10x
        # values verbatim; counting both inflates the hit list without adding
        # a single new place to check.
        if (label, v) in seen:
            continue
        seen.add((label, v))
        hit_dp = None
        anc = anchors(label)
        # Whole numbers are written without a decimal point, and the default
        # precision set starts at two: rendering the step count as "50.00" finds
        # nothing, and the count was never searched for at all. Any integer-
        # valued published quantity has the same problem.
        # Whole numbers, and any quantity of order hundreds or more, are
        # written without a decimal point in prose. Rendering a 226 m reach as
        # "226.44" finds nothing, and the quantity is then reported as uncited
        # rather than as quoted-and-rounded.
        dps_v = list(dps)
        if float(v).is_integer() or abs(v) >= LARGE_VALUE_MIN:
            dps_v = [0] + dps_v
        for dp in dps_v:
            s = render(v, dp)
            if not searchable(s, label):
                continue
            if any(quotes(t, s) and anchored(t, s, anc, label)
                   for t in docs.values()):
                hit_dp = dp
                break
        # A value found SOMEWHERE was previously treated as settled, and the
        # scan stopped. That is the deepest form of the repeats problem: a
        # number corrected in three documents and left stale in seven reads as
        # "cited and current", because one hit satisfied the check. The scan now
        # continues in both cases; when the current value is present the stale
        # occurrences are reported as MIXED, which is a different and more
        # urgent finding than a value that is wrong everywhere.
        # ---- M31: the same value quoted in millimetres --------------
        # Additive. Runs whether or not the metre rendering was found, so a
        # value that is current in one document and quoted in mm in another is
        # still reported rather than being settled by the first hit.
        if VALUE_UNITS.get((source, label), "").lower() in METRE_UNITS:
            for s in mm_renderings(v):
                where = [d for d, t in docs.items()
                         if quotes_as_mm(t, s)
                         and anchored(t, s, anc, label, strict=True)]
                if where:
                    mm_hits.append((source, label, v, s, where))
                    if hit_dp is None:
                        hit_dp = 0
                    break

        mixed = hit_dp is not None
        if mixed:
            ok += 1
        found = []
        for dp in sorted(dps_v, reverse=True):   # most precise first
            if not searchable(render(v, dp), label):
                continue
            anc = anchors(label)
            for nm in near_misses(v, dp, span):
                if not searchable(nm, label):
                    continue
                where = [d for d, t in docs.items()
                         if quotes(t, nm)
                         and anchored(t, nm, anc, label, strict=True)]
                if where:
                    found.append((nm, dp, where))
            if found:
                break                          # one precision level is enough
        if found:
            gaps = [abs(float(nm) - v) / abs(v) for nm, _, _ in found]
            rel = min(gaps) if gaps else 0.0
            if rel >= min_rel:
                stale.append((source, label, v, found, rel, mixed))
        elif not mixed:
            uncited.append((source, label, v))

    # MIXED first: a value that is right in one document and wrong in another
    # is the more urgent class, whatever the size of the gap.
    stale.sort(key=lambda r: (not r[5], -r[4]))

    if csv_out:
        import csv as _csv
        with open(csv_out, "w", newline="", encoding="utf8") as fh:
            w = _csv.writer(fh)
            w.writerow(["rel_gap_pct", "key", "committed", "corpus_value",
                        "documents", "source_csv", "class"])
            for source, label, v, found, rel, mixed in stale:
                nm, _dp, where = found[0]
                w.writerow([f"{rel*100:.2f}", label, f"{v:g}", nm,
                            "; ".join(sorted(where)), source,
                            "MIXED" if mixed else "STALE"])
        print(f"  triage list written to {csv_out}")
    else:
        for source, label, v, found, rel, mixed in stale:
            tag = "MIXED " if mixed else "STALE?"
            note = ("  — the current value IS quoted elsewhere, so these "
                    "documents were missed by an earlier sweep" if mixed else "")
            print(f"\n  {tag}  {label}   (gap {rel*100:.2f}%){note}")
            print(f"          committed {v:g}   ({source})")
            for nm, dp, where in found[:3]:
                print(f"          corpus has {nm} at {dp}dp in: "
                      f"{', '.join(sorted(where))}")

    if mm_hits:
        print("\n  MILLIMETRE CITATIONS (metre-stored value quoted in mm; M31)")
        for source, label, v, s, where in sorted(mm_hits, key=lambda r: r[1]):
            docs_s = ", ".join(sorted(where))
            print(f"      {label} = {v:.6g} m  quoted as {s} mm  in {docs_s}")
        print(f"    {len(mm_hits)} metre-stored value(s) cited in millimetres.")
        print("    Advisory. Measured precision at this gate is 86% (24 of 28\n    hand-adjudicated), so a few rows are numeric collisions in mm-dense\n    tables — an se quoted beside the estimate it belongs to, a cluster\n    trend equal to 1000x an unrelated metre value. Adjudicate before acting.")

    print(f"\n  {ok} value(s) cited and current; {len(stale)} possible stale "
          f"citation(s){f' above {min_rel*100:g}%' if min_rel else ''}; "
          f"{len(uncited)} not cited anywhere (informational).")
    return len(stale)


def check_index(docs, values) -> int:
    """Exact verification of every indexed citation.

    Three outcomes per row, and the distinction matters:
      OK       the document still quotes the current value.
      DRIFTED  the document still contains the indexed string, but the pipeline
               value has moved — the citation is now stale. This is the failure
               the whole exercise exists to catch, and it is exact: no
               proximity, no rounding guess.
      MOVED    the indexed string is gone from the document. Usually the prose
               was rewritten. Not an error, but the index row needs re-pointing
               or the citation has been dropped.
    """
    idx = REPO / CITATION_INDEX
    print()
    print("=" * 78)
    print("CITATIONS — exact check of the citation index")
    print("=" * 78)
    if not idx.exists():
        print(f"  no index at {CITATION_INDEX} — run "
              "tools/build_citation_index.py")
        return 0

    current = {}
    for _src, label, v in values:
        current.setdefault(label, v)

    ok = drifted = moved = unknown = advisory = 0
    # (key, stale string, current string, document the index row named). Filled
    # as rows are checked and swept across the whole corpus afterwards, because
    # the index carries one row per document and a repeated number is otherwise
    # checked in one place only.
    stale_strings: list[tuple[str, str, str, str]] = []
    adjudicated: list[tuple[str, str, str, str]] = []
    for row in csv.DictReader(open(idx, encoding="utf8")):
        # Rejected rows are recorded coincidences — keeping them stops the
        # builder re-proposing them, but they are not citations to check.
        if row.get("status") == "rejected":
            continue
        key, doc, quoted = row["key"], row["document"], row["quoted"]
        # A history document is not a citation site — see HISTORY_DOCS.
        if doc.split("/")[-1] in HISTORY_DOCS:
            continue
        text = docs.get(doc)
        if text is None:
            continue
        if key not in current:
            unknown += 1
            continue
        dp = len(quoted.split(".")[1]) if "." in quoted else 0
        want = render(current[key], dp)
        # Compare NUMBERS, not glyphs. Two of the drifted rows were never drift:
        # report9 quotes "−0.03" with U+2212 against a rendered "-0.03", and
        # "+0.82" with an explicit plus against a rendered "0.82". Both are the
        # same value written differently, and reporting them as stale citations
        # is how a gating check teaches its reader to ignore it.
        def _same(a: str, b: str) -> bool:
            f = lambda x: x.replace("\u2212", "-").lstrip("+")
            return f(a) == f(b)
        # The row's own before/after slices pick which occurrence it means.
        span = locate(text, quoted, row.get("before", ""), row.get("after", ""))
        present = span is not None
        if present and _same(want, quoted):
            ok += 1
        elif present and (key, doc, quoted) in _FALSE_POSITIVES:
            adjudicated.append((key, doc, quoted, _FALSE_POSITIVES[(key, doc, quoted)]))
        elif present:
            if row.get("status") == "confirmed":
                drifted += 1
            else:
                advisory += 1
            print(f"\n  DRIFTED  {key}  [{row.get('status','')}]")
            print(f"           {doc} quotes {quoted}, pipeline now says {want}")
            stale_strings.append((key, quoted, want, doc))
            # Context as the DOCUMENT now reads at the located occurrence,
            # not as the index recorded it: the point is to show where the
            # stale string still sits.
            s, e = span
            # A score of 0 means the string is present but not where the index
            # says: the located occurrence may be a coincidence rather than
            # the citation, and the row wants re-pointing before it is trusted.
            agree = _context_score(text, span, row.get("before", ""),
                                   row.get("after", ""))
            print(f"           ...{_norm_ctx(text[max(0, s - 50):s])} "
                  f"[{quoted}] {_norm_ctx(text[e:e + 50])}...")
            if not agree:
                print("           (stored context does not match here — "
                      "location unconfirmed, re-point the index row)")
        else:
            moved += 1
            if quotes(text, want):
                ok += 0   # value updated in prose but index not re-pointed
                print(f"\n  REPOINT  {key}: {doc} now quotes {want} "
                      f"(index still says {quoted}) — update the index row")
                # The indexed document has been updated; other documents may
                # still carry the old string, and nothing else would look.
                stale_strings.append((key, quoted, want, doc))
            else:
                print(f"\n  MOVED    {key}: {quoted} no longer in {doc} "
                      "— prose rewritten, or citation dropped")
    sweep_repeats(docs, stale_strings, adjudicated)
    if adjudicated:
        print()
        print("-" * 78)
        print("ADJUDICATED — checked by hand, not the citation, will not be "
              "reported again")
        print("-" * 78)
        for key, doc, quoted, why in sorted(adjudicated):
            print(f"  {key}: {quoted} in {doc.split('/')[-1]}")
            print(f"      {why}")
        print(f"\n  {len(adjudicated)} occurrence(s) held in "
              f"{CITATION_FALSE_POSITIVES}. Remove a row there if the document "
              "is rewritten — a rewrite can introduce a real citation of a "
              "value that was previously only a coincidence.")
    print(f"\n  {ok} citation(s) exact and current; {drifted} DRIFTED "
          f"(confirmed rows — these gate); {advisory} drifted on unreviewed "
          f"rows (advisory); {moved} moved/re-pointed; "
          f"{unknown} key(s) no longer published.")
    return drifted


def sweep_repeats(docs, stale_strings, adjudicated=None) -> None:
    """Search the whole corpus for every stale string the index check found.

    The index holds one row per (key, document), so a value quoted in five
    documents is verified in one of them and the other four stand unexamined
    behind a passing gate. This takes each stale string the index check
    identified and looks for it everywhere else, in a citable context, so the
    repeats surface with the original.

    Reported separately from DRIFTED because these locations have no index row:
    they are places to check and re-point, not rows that already gate.
    """
    if not stale_strings:
        return
    seen: set[tuple[str, str]] = set()
    hits: list[tuple[str, str, str, str]] = []
    for key, quoted, want, indexed_doc in stale_strings:
        for doc, text in docs.items():
            if doc == indexed_doc or (doc, quoted) in seen:
                continue
            if not quotes(text, quoted):
                continue
            seen.add((doc, quoted))
            if (key, doc, quoted) in _FALSE_POSITIVES:
                if adjudicated is not None:
                    adjudicated.append((key, doc, quoted,
                                        _FALSE_POSITIVES[(key, doc, quoted)]))
                continue
            hits.append((key, quoted, want, doc))
    if not hits:
        return
    print()
    print("-" * 78)
    print("REPEATS — the same stale string in documents the index does not cover")
    print("-" * 78)
    for key, quoted, want, doc in sorted(hits, key=lambda h: (h[0], h[3])):
        print(f"  UNINDEXED  {key}: {doc} also carries {quoted} "
              f"(pipeline says {want}) — no index row covers this occurrence")
    docs_hit = len({h[3] for h in hits})
    print(f"\n  {len(hits)} unindexed occurrence(s) across {docs_hit} document(s). "
          "Each needs the same edit as its indexed twin, and an index row so it "
          "is checked next time.")


def _claim_key_columns(key_col: str) -> list:
    """`key_col` may name one column or several joined with '+'.

    25_01_panel_fit_parameters.csv has no single column that identifies a row:
    `source` alone matches two models and `model` alone matches four sources.
    Without a composite key the headline fit cannot be registered as a claim at
    all — which is why the coast-edge rate was unwatched when Paper 1's
    conclusions quoted a value it never had.
    """
    return [c.strip() for c in key_col.split("+") if c.strip()]


def _claim_label(row, key_col: str) -> str:
    return "+".join(str(row[c]) for c in _claim_key_columns(key_col))


def _claim_mask(df, key_col: str, expect: str):
    cols = _claim_key_columns(key_col)
    want = [w.strip() for w in str(expect).split("+")]
    if len(cols) != len(want):
        return df.index == -1                     # selects nothing; caller faults
    m = None
    for c, w in zip(cols, want):
        this = df[c].astype(str) == w
        m = this if m is None else (m & this)
    return m


def check_claims(docs) -> int:
    reg = REPO / CLAIMS_REGISTER
    print()
    print("=" * 78)
    print("CLAIMS — assertions with no number, checked against the CSV")
    print("BREACH = the CSV says the claim is false AND a document asserts it")
    print("=" * 78)
    if not reg.exists():
        print(f"  no register at {CLAIMS_REGISTER} — skipped")
        return 0
    bad = 0
    for row in csv.DictReader(open(reg, encoding="utf8")):
        p = REPO / row["csv"]
        if not p.exists():
            print(f"  FAULT  {row['claim_id']}: {row['csv']} missing — this "
                  f"claim is NOT being checked")
            bad += 1
            continue
        df = pd.read_csv(p)
        kind, _, rest = row["rule"].partition(":")
        detail = ""
        if kind in {"argmin", "argmax"}:
            col = rest
            if col not in df.columns:
                print(f"  FAULT  {row['claim_id']}: no column {col!r} in "
                      f"{row['csv']} — this claim is NOT being checked")
                bad += 1
                continue
            idx = df[col].idxmin() if kind == "argmin" else df[col].idxmax()
            actual = _claim_label(df.loc[idx], row["key_col"])
            holds = actual == row["expect"]
            detail = f"{row['rule']} is {actual!r}, not {row['expect']!r}"
        elif kind == "band":
            col, _, bounds = rest.partition(":")
            lo_s, _, hi_s = bounds.partition(":")
            try:
                lo, hi = float(lo_s), float(hi_s)
            except ValueError:
                print(f"  FAULT  {row['claim_id']}: band needs "
                      f"band:<col>:<lo>:<hi>, got {row['rule']!r} — this claim "
                      f"is NOT being checked")
                bad += 1
                continue
            if col not in df.columns:
                print(f"  FAULT  {row['claim_id']}: no column {col!r} in "
                      f"{row['csv']} — this claim is NOT being checked")
                bad += 1
                continue
            hit = df[_claim_mask(df, row["key_col"], row["expect"])]
            if len(hit) != 1:
                print(f"  FAULT  {row['claim_id']}: {row['key_col']} == "
                      f"{row['expect']!r} selects {len(hit)} row(s), needs "
                      f"exactly 1 — this claim is NOT being checked")
                bad += 1
                continue
            val = float(hit.iloc[0][col])
            holds = lo <= val <= hi
            detail = f"{col} is {val:.4g}, outside [{lo:g}, {hi:g}]"
        else:
            # NOT a skip. An unrecognised rule used to print SKIP and pass,
            # which left a row sitting in the register looking like cover while
            # nothing evaluated it — the same silent-gap failure as a renamed
            # value column (check_value_columns) and a swallowed git error in
            # push_working. A register entry that cannot be evaluated is a
            # fault in the register, and the gate says so.
            print(f"  FAULT  {row['claim_id']}: unsupported rule "
                  f"{row['rule']!r} — this claim is NOT being checked")
            bad += 1
            continue

        needle = row.get("phrase", "").strip()
        where = [d for d, t in docs.items() if needle in t] if needle else []

        # CONTRADICTS — the corpus checked against itself, not against the CSV.
        #
        # The register's original question is "has the DATA moved out from under
        # a standing claim?". That question cannot catch the failure that put
        # this column here: Paper 1's conclusions said "around a third" and
        # "roughly 29 mm/yr" while Paper 1's own results section said "about a
        # quarter" and "roughly 26 mm/yr", and the CSV agreed with the results
        # section throughout. No committed value had moved, so nothing fired.
        #
        # A `contradicts` entry is a pipe-separated list of literal phrasings
        # that are KNOWN WRONG — in practice, wordings that were actually in the
        # corpus and were corrected. Their reappearance is a breach whatever the
        # CSV says. Enumerating wrong values in the abstract would be fragile;
        # enumerating the ones that have actually occurred is not, and it is the
        # same discipline as keeping a falsified claim in the register so it
        # cannot come back unnoticed.
        contra = [c.strip() for c in (row.get("contradicts") or "").split("|")
                  if c.strip()]
        contra_hits = {c: sorted(d for d, t in docs.items() if c in t)
                       for c in contra}
        contra_hits = {c: v for c, v in contra_hits.items() if v}

        # Gate on ASSERTED-AND-FALSE, not on false alone. Entries kept as
        # tripwires are false by design — that is the point of keeping them.
        asserted_false = (not holds) and bool(where)
        if asserted_false or contra_hits:
            bad += 1

        if contra_hits:
            verdict = "BREACH"
        elif asserted_false:
            verdict = "BREACH"
        else:
            verdict = "HOLDS " if holds else "false "
        did = (row.get("decision_id") or "").strip()
        print(f"  {verdict} {row['claim_id']}"
              f"{f' [{did}]' if did else ''}: {row['assertion']}")
        if not holds:
            print(f"          {detail}")
        if where:
            print(f"          asserted in: {', '.join(sorted(where))}")
        elif not holds:
            print("          not asserted in the corpus — tripwire only")
        for c, v in contra_hits.items():
            print(f"          CONTRADICTED: a corrected wording is back — "
                  f"{c!r} in {', '.join(v)}")
    return bad


class _Tee:
    """stdout that also writes to a file.

    cite_check's full output is ~450 lines and the run takes minutes, so it is
    read in a terminal once and then gone. `--out` keeps it. Written here rather
    than left to shell redirection because a check whose output is habitually
    discarded is a check nobody acts on.
    """

    def __init__(self, stream, path):
        self._s = stream
        # Line-buffered: NUMBERS takes minutes, and a log that only appears at
        # the end is no better than the terminal it was written to escape.
        self._f = open(path, "w", encoding="utf8", buffering=1)

    def write(self, text):
        self._s.write(text)
        self._f.write(text)
        return len(text)

    def flush(self):
        self._s.flush()
        self._f.flush()

    def close(self):
        self._f.close()


def check_value_columns() -> int:
    """Does every column HEADLINE_TABLES and EXTRA_VALUE_TABLES name still exist?

    `collect_values()` reads those columns inside a
    `except (TypeError, ValueError, KeyError): continue`. A column that has been
    renamed or dropped therefore does not fail — it SILENTLY LEAVES THE VALUE
    INDEX, and every number it carried stops being checked against the corpus
    while the gate stays green.

    That is not hypothetical for this exact file. The comment above
    EXTRA_VALUE_TABLES records the last time: "Script 15 was stale in four of
    five lambda values and four of five NSE improvements, and had flipped a
    published ranking, with the gate green throughout."

    Added 2026-08-27, immediately after renaming Best_Lambda to Best_Kappa and
    telling Martin the gate would fail until Script 15 was rerun. It would not
    have. It would have gone quiet, which is worse.

    Header row only, so this is cheap enough to run in --claims-only and reach
    check_all, which is the only mode check_all runs.
    """
    missing = []
    for rel, kcol, vcols in list(HEADLINE_TABLES) + list(EXTRA_VALUE_TABLES):
        f = REPO / rel
        if not f.exists():
            continue                      # absent files are reported elsewhere
        try:
            have = set(pd.read_csv(f, nrows=0).columns)
        except Exception as e:            # noqa: BLE001 — an unreadable table
            missing.append((rel, f"UNREADABLE: {e}"))
            continue
        for c in _key_columns(kcol) + list(vcols):
            if c not in have:
                missing.append((rel, c))
    if missing:
        print("  cite_check: FAULT — value column(s) named here and absent from "
              "the CSV")
        for rel, c in missing:
            print(f"    {rel}   no column {c!r}")
        print("  These numbers are NOT being checked against the corpus. Rerun the")
        print("  script, or update the column name here — do not leave it.")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dp", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--near", type=int, default=2,
                    help="near-miss span in units of the last decimal place")
    ap.add_argument("--claims-only", action="store_true")
    ap.add_argument("--index-only", action="store_true",
                    help="exact citation-index check only; skip the heuristic "
                         "near-miss scan")
    ap.add_argument("--min-rel", type=float, default=0.0,
                    help="only report hits whose relative gap exceeds this "
                         "(e.g. 0.005 hides rounding-level differences)")
    ap.add_argument("--csv", default=None,
                    help="write the triage list to a CSV and print a summary only")
    ap.add_argument("--spread-all", action="store_true",
                    help="run the SPREAD check over every published value using "
                         "the key's own vocabulary as the anchor, not just the "
                         "quantities in QUANTITY_ANCHORS. Exploratory: noisier, "
                         "and it is how a quantity earns a register entry.")
    ap.add_argument("--spread-gate", action="store_true",
                    help="make SPREAD a gating check rather than advisory")
    ap.add_argument("--section", action="append", default=None,
                    choices=["columns", "index", "numbers", "spread", "claims"],
                    help="run only these section(s); repeatable. Default: all. "
                         "NUMBERS is the slow one — minutes, where every other "
                         "section is about a second — so this is what makes the "
                         "check runnable in pieces.")
    ap.add_argument("--docs", action="append", default=None,
                    help="restrict the corpus to mirrors whose path contains "
                         "this substring; repeatable, matched as OR. Chunks "
                         "NUMBERS, whose cost is values x documents and which "
                         "takes minutes over the whole corpus.")
    ap.add_argument("--out", default=None,
                    help="also write everything printed to this file")
    args = ap.parse_args()

    tee = None
    if args.out:
        tee = _Tee(sys.stdout, args.out)
        sys.stdout = tee
    try:
        return _run(args)
    finally:
        if tee is not None:
            sys.stdout = tee._s
            tee.close()
            print(f"  (written to {args.out})")


def _run(args) -> int:
    # --claims-only and --index-only predate --section and still work. They are
    # what check_all and the habit of years call, so they select sections rather
    # than being replaced by them.
    if args.section:
        want = set(args.section)
    elif args.claims_only:
        want = {"columns", "claims"}
    elif args.index_only:
        want = {"columns", "index", "claims"}
    else:
        want = {"columns", "index", "numbers", "spread", "claims"}

    docs = load_documents()
    if args.docs:
        docs = {k: v for k, v in docs.items()
                if any(d in k for d in args.docs)}
        if not docs:
            print(f"No mirror path contains any of {args.docs!r} — "
                  "nothing to check.")
            return 1
    if not docs:
        print("No mirrors found — run tools/refresh_mirrors.py first.")
        return 1
    filt = f", filtered to {' | '.join(args.docs)}" if args.docs else ""
    print(f"corpus: {len(docs)} mirror(s){filt}")
    print(f"sections: {' '.join(sorted(want))}\n")

    rc = 0
    if "columns" in want:
        rc += check_value_columns()
    values = collect_values() if {"index", "spread"} & want else []
    if "index" in want:
        rc += check_index(docs, values)
    if "numbers" in want:
        rc += check_numbers(docs, args.dp, args.near, args.min_rel, args.csv)
    if "spread" in want:
        rc += check_spread(docs, values, args.spread_all, args.spread_gate)
    if "claims" in want:
        rc += check_claims(docs)
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
