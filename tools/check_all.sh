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
# VERSION 1.2.0 - 2026-08-23
# CHANGELOG
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
python3 tools/pipeline_lint.py --check literals 2>/dev/null | grep -cE "FAIL" \
  | xargs -I{} echo "  {} hard-coded constant(s) — python3 tools/pipeline_lint.py --check literals"

echo
echo "── record basis (does §F.6 still describe the code?) ─────────────────"
python3 tools/record_basis_lint.py --quiet || rc=1

echo
echo "── rounding (has new store-time rounding appeared?) ─────────────────"
python3 tools/rounding_lint.py || rc=1

echo
echo "── decisions ────────────────────────────────────────────────────────"
python3 tools/decision_lint.py --quiet || rc=1
# DECISIONS_PUBLIC.md is derived from the working record, which is no longer
# tracked. Nothing else would notice the two drifting apart, and the public one
# is the only one a reader outside this machine can see.
python3 tools/build_public_decisions.py --check || rc=1

echo
echo "── symbols (does the register contradict itself?) ───────────────────"
# The register GATES; the ambiguous-glyph inventory is advisory and prints only.
# Split deliberately: the backlog is 148 entries and gating on it kept this tool
# out of the chain entirely, which is how the register came to hand z to d_depth
# while z0 was the datum with nothing to catch it (D-062).
python3 tools/symbol_check.py 2>/dev/null | grep -E "^  (RESERVED|OCCUPIED|DUPLICATE)|^  register faults" || true
python3 tools/symbol_check.py >/dev/null 2>&1 || rc=1

echo
echo "── references (do typed Table/Figure numbers still resolve?) ─────────"
# Captions auto-number; in-text references are typed by hand and fall out of
# step silently. Read from the ODTs in master order, so no PDF export is needed
# and the check cannot run on a stale artefact.
python3 tools/reference_lint.py --kind table || rc=1

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
python3 tools/ref_audit.py | grep -E "^   DISAGREES|^ref_audit:" || true
python3 tools/ref_audit.py >/dev/null 2>&1 || rc=1
python3 tools/section_ref_audit.py | grep -E "^  reference forms|^      [A-Z§]|^section_ref_audit:|disagree" || true
python3 tools/section_ref_audit.py >/dev/null 2>&1 || rc=1

echo
echo "── exports (is each published PDF newer than its sources?) ──────────"
# ADVISORY. A PDF export is slow and manual, and a gate firing between every ODT
# edit and the next export gets switched off inside a week — the same reasoning
# check_all already applies to pipeline_lint's literal check. It prints loudly
# instead, and figref_lint REFUSES outright rather than linting a stale export.
python3 tools/export_lag.py | grep -E "^  (STALE|MISSING|UNMAPPED|UNBUILT)|behind their sources" || true

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
