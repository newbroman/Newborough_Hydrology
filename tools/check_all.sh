#!/usr/bin/env bash
# check_all.sh — the gate. Run before every commit, and in CI.
#
# Each check answers a question that was answered wrongly at least once:
#   versions   does a document's in-text version string still agree with the
#              filename it was saved under? The Methods Supplement said 1.9.7
#              while its filename said _v1_9_24.
#   mirrors    are the lints reading current text, or yesterday's?
#   cite       does the corpus still agree with the committed pipeline outputs?
#   decisions  did a change encode a choice that nobody recorded?
#   basis      does the Methods Supplement still describe which record each
#              analysis is fitted on? It asserted a fitting window for Script 07
#              for months; Script 07 performs no fit.
#
# Exit non-zero if any gate fails. --fix syncs the document version strings and
# regenerates the mirrors instead of failing on them — the two failures with a
# safe automatic remedy. The version sync runs FIRST: it edits the ODTs, so
# mirrors regenerated before it would be stale the moment it ran.
#
# ============================================================================
# VERSION 1.5.0 - 2026-08-31
# CHANGELOG
#   1.5.0 (2026-08-31): output_lag GATES (D-102). It ran advisory since
#     2026-08-27 because it cannot tell a coefficient change from a docstring
#     edit, and a check that cries stale over comments is one people learn to
#     skip. That argument prices the false positive, which costs one re-run. The
#     false negative was priced on 2026-08-31 and it was silent:
#     24b_residual_climatology.py is an OPT-IN step, --full does not run it, and
#     it sat with edited code and outputs from the previous version while every
#     other gate read green - because every other gate reads the outputs and
#     finds them self-consistent, which they are, with the older code. The
#     pre-commit run is now `run_analysis.py --full --with-supplementary` and
#     this is what enforces it. Wired only after confirming it passes.
#   1.4.0 (2026-08-26): env_audit runs first. Half the checks below print a
#     version and act on it, and none of them said whose. A Cowork sandbox's
#     pandoc 2.9.2 and python 3.10 were read as this project's for a day, and a
#     five-week outage was written up for a script that had never failed. The
#     environment line now names the machine before anything else reports.
#     (The VERSION line above read 1.2.0 against a 1.3.0 changelog entry until
#     this bump — the header had drifted from its own history.)
#   1.3.0 (2026-08-23): ref_audit and section_ref_audit join the chain, and the
#     reference-form census prints with them. Resolution was never the weak
#     point — pointing at the wrong thing was, and nothing looked for it.
#   1.2.0 (2026-08-23): symbol_check and reference_lint join the chain. Both
#       were written months apart, both were run by hand, and neither gated —
#       which is why a register collision and a table-reference cascade could
#       both sit undetected. Each splits its exit code: the structural fault
#       gates, the inherited backlog reports.
#   1.1.0 (2026-08-19): document-version gate added, ahead of the mirrors block
#       for the ordering reason above. tools/doc_version_sync.py --check.
#   1.0.0: this script's state before it carried a version number. 1.0.0 marks
#       the number's introduction, not the start of the script's history.
# ============================================================================
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

FIX=0
[ "${1:-}" = "--fix" ] && FIX=1
rc=0

# FIRST, deliberately. Several checks below print a version and act on it -
# refresh_mirrors refuses to write under an old pandoc, figref_lint needs
# pdftotext, build_pdfs needs LibreOffice - and none of them says WHOSE version
# it is reporting. On 2026-08-26 that cost a day: a Cowork sandbox's pandoc 2.9.2
# and python 3.10 were read as this project's, and a five-week outage was written
# up for a script that had never failed. env_audit runs before anything else so
# that every line after it is read against the right machine.
#
# IT GATES SINCE 2026-08-29, and only on the two faults that are true wherever
# they are seen: a library the pipeline imports being NOT IMPORTABLE, and the
# record disagreeing with requirements.txt. Identity never gates - a second
# machine SHOULD report "NOT THE MACHINE", that is the tool working - and
# version drift gates only on the recorded machine, where re-recording is the
# one-command fix. Until this date the line ended `|| true`: it ran, printed the
# whole finding, and could not fail, which is how a recorded reference that
# CANNOT RUN THE PIPELINE sat here for weeks with every gate green (D-093).
echo "── environment (is this the machine the pipeline runs on?) ──────────"
python3 tools/env_audit.py --quiet --gate || rc=1

echo
echo "── document versions (does the text agree with the filename?) ───────"
if [ "$FIX" = "1" ]; then
    python3 tools/doc_version_sync.py --quiet || rc=1
else
    python3 tools/doc_version_sync.py --check --quiet || {
        echo "  (run tools/check_all.sh --fix to sync them)"
        rc=1
    }
fi

echo
echo "── mirrors ──────────────────────────────────────────────────────────"
if [ "$FIX" = "1" ]; then
    python3 tools/refresh_mirrors.py || rc=1
else
    python3 tools/refresh_mirrors.py --check || {
        echo "  (run tools/check_all.sh --fix to regenerate)"
        rc=1
    }
fi
# --check compares modification times and gates on them because it is instant.
# It cannot tell you whether a mirror is what its source PRODUCES. When that is
# the question — a mirror that keeps coming back changed, a suspicion that two
# pandocs disagree — `--verify` regenerates every mirror and compares bytes. It
# is not in the gate because it runs pandoc 23 times.
echo "  (content check, on demand: python3 tools/refresh_mirrors.py --verify)"

echo
echo "── pipeline (are the SCRIPTS importing the right numbers?) ───────────"
# defaults and backward dependencies GATE: a default masquerading as a result,
# or a script reading an output that does not exist yet, both put a wrong number
# into the outputs silently. The literal lint is advisory — it over-reports, and
# a gate that fires 30 times on day one gets switched off by day three.
python3 tools/pipeline_lint.py --check defaults || rc=1
python3 tools/pipeline_lint.py --check deps     || rc=1
# runid GATES too, and asks a provenance question the two above cannot: is
# pipeline_site_observations.csv the product of ONE pass? It is run-scoped, so a
# producer run on its own writes a real value into a file otherwise recording
# the previous pass. Not a nineteenth gate script — a fourth sub-check of the
# tool that already owns the "are the scripts working from the right numbers?"
# family. See D-101.
python3 tools/pipeline_lint.py --check runid    || rc=1
python3 tools/pipeline_lint.py --check literals 2>/dev/null | grep -cE "FAIL" \
  | xargs -I{} echo "  {} hard-coded constant(s) — python3 tools/pipeline_lint.py --check literals"
# defaults_lint asks the OTHER defaults question: pipeline_lint asks whether a
# committed parameter is still a first-pass default; this asks whether each
# documented default still equals the committed cell its comment names. It
# GATES: the trailing comment on every entry IS the advisory, and the drift
# recurred five times in eleven days regardless.
python3 tools/defaults_lint.py || rc=1

echo
echo "── record basis (does §F.6 still describe the code?) ─────────────────"
python3 tools/record_basis_lint.py --quiet || rc=1

echo
echo "── drift term (does any consumer name 10a's drift column by literal?) ──"
# D-111 swept the PRODUCER and not the consumers: 10a stopped emitting
# easting_x_time, Script 25 went on filtering on that literal, matched nothing,
# wrote a one-byte file over a committed artefact and killed a full pipeline
# run. drift_term() was written to resolve the column and raise before any
# write; this is what makes anyone use it. --selftest first, because a lint
# that passes proves nothing unless its detection still works.
python3 tools/drift_term_lint.py --selftest || rc=1
python3 tools/drift_term_lint.py || rc=1

echo
echo "── seasons (is any seasonal window defined outside config.py?) ──────"
python3 tools/season_lint.py --quiet || rc=1
echo

echo "── rounding (has new store-time rounding appeared?) ─────────────────"
python3 tools/rounding_lint.py || rc=1

echo
echo "── artefacts (is a committed output truthful about itself?) ─────────"
# The gate the other fifteen did not cover: an output checked against ITSELF.
# Row arithmetic (a quantity must be reproduced by the columns that define it)
# and the empty artefact (a step that could not run must not overwrite its
# committed file with a header). Both start green; see W124 and W128.
python3 tools/artefact_lint.py || rc=1

echo
echo "── geographic inputs ────────────────────────────────────────────────"
# Advisory, not a gate: the open TO CONFIRM fields are questions only Martin can
# answer, and failing the build on them every run would just teach us to ignore
# it. What would be a real failure is a layer with no entry at all, or an entry
# pointing at a file that has gone.
python3 tools/geo_provenance.py || true
python3 tools/geo_consistency.py || true   # W73: withdrawn geo values must not reappear (advisory)

echo
echo "── manifest (is the committed one what the orchestrator produces?) ───"
# The manifest is the number every document cites, and it is the one committed
# output any full pipeline run rewrites - so a run from an older tree silently
# reverts it. That happened on 2026-08-29 and dropped a registered script.
# GATED: a drifting manifest is a wrong citable number.
python3 tools/manifest_lint.py || rc=1

echo
echo "── step/phase locators (do the MS step numbers match the manifest?) ──"
# D-023 put the HEADLINE counts under the manifest guard; nothing watched the
# per-step "Script XX ... step N/T, Phase P" LOCATORS in the prose, so they
# drifted silently (Script 27 read "step 44" and "step 49" while the manifest
# said 52). This keys each locator on the script beside it and checks its index,
# total and phase against the manifest. GATED.
python3 tools/step_number_lint.py --selftest >/dev/null || rc=1
python3 tools/step_number_lint.py || rc=1

echo
echo "── withheld headlines ───────────────────────────────────────────────"
# Script 40 withholds its own rate when its gate fails (D-085). A silent
# absence reads as success, so the state is REPORTED here. Reported, not gated:
# withholding is the script working, and failing the build on it would teach us
# to route around the gate. What would be a real failure is the file vanishing
# or the D-060 regression breaking, and both are visible below.
python3 tools/withheld_report.py || true

echo
# deferred_report is the "what is waiting on ME" half of the decision record.
# REPORTED, NOT GATED: a deferral is a session declining to make someone else's
# call, which is the behaviour that keeps the record honest. What must not happen
# is it going quiet. Retire one by adding "Deferral discharged:" to its entry.
echo "── deferred decisions (what is waiting on a person?) ─────────────────"
python3 tools/deferred_report.py || true

echo
echo "── decisions ────────────────────────────────────────────────────────"
python3 tools/decision_lint.py --quiet || rc=1
# Every entry must say what it governs, or context_for cannot surface it and the
# next session works without it (D-080).
python3 tools/context_for.py --audit || true
# DECISIONS_PUBLIC.md is derived from the working record, which is no longer
# tracked. Nothing else would notice the two drifting apart, and the public one
# is the only one a reader outside this machine can see.
python3 tools/build_public_decisions.py --check || rc=1

echo
echo "── ledgers (does SCRIPT_LEDGER still describe the code?) ─────────────"
# Gates on structural faults only — a script with no row, a row with no script.
# Version drift is printed and counted but does not gate: it was 29 rows deep on
# the day this landed, and a gate that fails from birth is a gate that gets
# commented out. Same treatment as pipeline_lint's literal check and export_lag.
ledger_out="$(python3 tools/ledger_lint.py 2>&1)" || rc=1
printf '%s\n' "$ledger_out" | grep -E "row\(s\) with a stale version|^  ledger_lint:" || true

echo
echo "── document references (does every cited .md exist?) ─────────────────"
# Gates on NEW dangling references only. 32 were already dangling on the day
# this landed - 99 citations, mostly build-era specs and audits that lived
# beside the project rather than in it - and they are frozen in the tool's
# KNOWN_DANGLING inventory rather than deleted, because a citation is evidence
# that the reasoning existed. The job of the gate is to stop the list growing.
docref_out="$(python3 tools/docref_lint.py 2>&1)" || rc=1
printf '%s\n' "$docref_out" | grep -E "known-missing document|^  docref_lint: (OK|FAULT)" || true

echo
echo "── tasks (is any outstanding job now finished, or newly broken?) ─────"
# Gates ONLY on a check that could not answer. An open task is work in hand and
# must not fail the build; a broken check is a lie waiting to happen, and does.
# task_lint executes every registered check, several of which invoke other
# linters, so it is the most expensive gate in the file - 10 s. It was run
# TWICE, once to gate and once to display. --open carries the same exit code,
# so one run does both.
task_out="$(python3 tools/task_lint.py --open 2>&1)" || rc=1
printf '%s\n' "$task_out" | grep -E "^  [0-9]+ open|OPEN |task\(s\): " || true

echo
echo "── symbols (does the register contradict itself?) ───────────────────"
# The register GATES; the ambiguous-glyph inventory is advisory and prints only.
# Split deliberately: the backlog is 148 entries and gating on it kept this tool
# out of the chain entirely, which is how the register came to hand z to d_depth
# while z0 was the datum with nothing to catch it (D-062).
symbol_out="$(python3 tools/symbol_check.py 2>/dev/null)" || rc=1
printf '%s\n' "$symbol_out" | grep -E "^  (RESERVED|OCCUPIED|DUPLICATE)|^  register faults" || true

# COVERAGE, which the check above cannot see. symbol_check asks whether an
# occurrence matches a REGISTERED sense; a glyph carrying a second sense nobody
# registered has no sense to fail against, so it reads as silence. beta_1 meant
# the SSM recharge coefficient and an OLS transfer-function slope in one
# document for months, and every check above passed throughout. This gates on a
# glyph GAINING a group against tools/symbol_definition_index.csv; re-pin with
# `symbol_check.py --definitions --snapshot` when a new sense is deliberate.
defs_out="$(python3 tools/symbol_check.py --definitions 2>&1)" || rc=1
printf '%s\n' "$defs_out" | grep -E "^  FAULT |^  RESOLVED |^definitions_audit:" || true

# The equations are embedded ODF objects: each carries the formula as MathML AND
# as a StarMath annotation, and LibreOffice regenerates the first from the
# second. Edit one and not the other and the change survives every check above,
# renders correctly in the PDF, and reverts the next time the formula is opened.
# THAT gates. The displaced-glyph and variant-codepoint counts are advisory.
starmath_out="$(python3 tools/starmath_log.py 2>&1)" || rc=1
printf '%s\n' "$starmath_out" | grep -E "^  starmath_log:|MathML and StarMath disagree" || true

echo
echo "── references (do typed Table/Figure numbers still resolve?) ─────────"
# Captions auto-number; in-text references are typed by hand and fall out of
# step silently. Read from the ODTs in master order, so no PDF export is needed
# and the check cannot run on a stale artefact.
python3 tools/reference_lint.py --kind table || rc=1
# FIGURES, since 2026-09-01. nrg_git.sh runs figref_lint at push time and its own
# comment says what that does NOT cover: "Semantic mistakes (a reference pointing
# at the wrong existing figure) are NOT caught here." figref_lint asks whether a
# number RESOLVES; this asks whether it still MEANS what it did. Remove one figure
# and every later caption renumbers while the typed references stay put - all of
# them resolve, to the wrong figure. Found on its first run: the project box gave
# the forest drawdown render as report Figure 50; it is 57, and 50 is the SSM water
# balance residual. figref_lint had passed that PDF clean, correctly.
python3 tools/reference_lint.py --kind figure || rc=1

echo
echo "── references by meaning (does a number point at what the text names?) ─"
# reference_lint asks whether a number RESOLVES. These two ask whether it points
# at the right thing, which is a different question and the one that was missed:
# on 2026-08-23 nine table references and fifteen figure references were wrong
# while every resolution check was green (D-068). Both read evidence the corpus
# already carries — the script named beside a figure, the figure cited beside a
# section — and neither guesses.
# Run twice, as symbol_check above does: a pipeline's exit status is grep's, so
# `tool | grep || rc=1` gates on whether the GREP matched, not on the tool.
refaudit_out="$(python3 tools/ref_audit.py 2>&1)" || rc=1
printf '%s\n' "$refaudit_out" | grep -E "^   DISAGREES|^ref_audit:" || true
sectionrefaudit_out="$(python3 tools/section_ref_audit.py 2>&1)" || rc=1
printf '%s\n' "$sectionrefaudit_out" | grep -E "^  reference forms|^      [A-Z§]|^section_ref_audit:|disagree" || true

echo
echo "── exports (is each published PDF newer than its sources?) ──────────"
# ADVISORY. A PDF export is slow and manual, and a gate firing between every ODT
# edit and the next export gets switched off inside a week — the same reasoning
# check_all already applies to pipeline_lint's literal check. It prints loudly
# instead, and figref_lint REFUSES outright rather than linting a stale export.
# --no-pages: export_lag 1.1.0 also compares the gh-pages branch against the
# working tree, and that section belongs at PUSH time, not here. Its lines do
# not match the grep below, so running it here would produce a check whose
# output is silently discarded — which is the one thing this file must never
# do. It runs in nrg_git.sh do_push instead, after the push, where the answer
# is actionable: `nrg_git.sh` option 13 republishes.
python3 tools/export_lag.py --no-pages | grep -E "^  (STALE|MISSING|UNMAPPED|UNBUILT)|behind their sources" || true

# export_lag asks whether each PDF is newer than its ODT. This asks the same
# question one layer down: whether a script has changed since the outputs in
# outputs/ were produced. Nothing asked it until 2026-08-27, so a script could be
# edited, committed and pushed while the corpus quoted the previous version's
# numbers with every gate green.
#
# A GATE since 2026-08-31 (D-102), not advice. It was advisory because it cannot
# tell a coefficient change from a docstring edit, and a check that cries stale
# over comments is one people learn to skip. What changed is that the cost of the
# false positive is now one command — re-run the script — while the cost of the
# false negative was demonstrated: 24b_residual_climatology.py is an OPT-IN step,
# `--full` does not run it, and it sat with edited code and outputs from the
# previous version while every other gate read green. No other check in this file
# can see that, because every one of them reads the outputs and finds them
# self-consistent. The pre-commit run is therefore
# `python3 run_analysis.py --full --with-supplementary`, and this is the gate
# that enforces it.
python3 tools/output_lag.py --quiet --gate || rc=1

echo
echo "── archive (are the canonical documents anywhere but this disk?) ─────"
# Advisory, like export_lag and for the same reason: an rclone copy is slow and
# manual. But it is the only check on the ONE risk the .gitignore creates - the
# .odt/.odm documents are in no repository, so between an edit and the next sync
# they exist once. BOOTSTRAP.md told a new machine to touch .last_drive_archive
# and nothing ever read it; this is the check that marker was written for.
python3 tools/drive_lag.py || true

echo
echo "── claims ───────────────────────────────────────────────────────────"
python3 tools/cite_check.py --claims-only || rc=1

echo
echo "── citations (advisory: triage list, does not gate) ──────────────────"
# The claims gate above is instant. This triage LINE runs the full sweep —
# 1,700 committed values against 30 documents — and since the minus-tolerant
# match and the constants sources landed it takes the best part of a minute,
# which is enough to put check_all over the desktop bridge's ceiling. Same
# treatment as refresh_mirrors --verify: out of the chain, one line saying how
# to ask for it.
if [ "${CITE_TRIAGE:-0}" = "1" ]; then
    python3 tools/cite_check.py 2>/dev/null | grep "value(s) cited" || true
else
    echo "  (full citation triage, on demand: python3 tools/cite_check.py)"
fi

echo
[ "$rc" = "0" ] && echo "check_all: OK" || echo "check_all: FAIL"
exit "$rc"
