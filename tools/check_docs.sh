#!/usr/bin/env bash
# ============================================================================
# check_docs.sh — the FAST, document-only gate profile for the REVIEW phase.
#
# check_all.sh runs the full pipeline+document chain (minutes) because during
# EDITING the analysis outputs change. In REVIEW you touch only frozen-ODT text,
# captions, numbers and spacing — the pipeline outputs never move — so the
# provenance / output-lag / analysis gates cannot fail and are pure wait.
#
# This runs ONLY the document-facing gates (seconds). It is NOT a substitute for
# check_all before a push that includes pipeline changes — run the full check_all
# (or nrg option 2) at those checkpoints.
#
# Usage:
#   bash tools/check_docs.sh                 # refresh all mirrors, run doc gates
#   bash tools/check_docs.sh --only report9  # refresh just that chapter's mirror
#   bash tools/check_docs.sh --no-mirror     # skip refresh (mirrors already current)
# ============================================================================
set -u
ONLY=""; NOMIRROR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --only) ONLY="$2"; shift 2;;
    --no-mirror) NOMIRROR=1; shift;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

# venv self-guard (same as check_all.sh): the doc gates are stdlib-only, but keep
# the recorded interpreter so behaviour matches the full run.
if [ -z "${VIRTUAL_ENV:-}" ] && [ -f venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

rc=0
G="\033[0;32m"; R="\033[0;31m"; N="\033[0m"
run() {  # run <label> <cmd...>
  local label="$1"; shift
  local out; out="$("$@" 2>&1)"; local r=$?
  if [ $r -ne 0 ]; then
    printf "  ${R}FAIL${N}  %s\n" "$label"
    echo "$out" | grep -iE "fail|fault|✗|abort|mismatch|expected|does not|since changed|behind" | head -4 | sed 's/^/        /'
    rc=1
  else
    printf "  ${G}ok${N}    %s\n" "$label"
  fi
}

echo "── mirrors ──────────────────────────────────────────────────────────"
if [ -n "$NOMIRROR" ]; then
  echo "  (skipped — --no-mirror)"
elif [ -n "$ONLY" ]; then
  run "refresh_mirrors --only $ONLY" python3 tools/refresh_mirrors.py --only "$ONLY"
else
  run "refresh_mirrors (all)"        python3 tools/refresh_mirrors.py
fi

echo "── document gates ───────────────────────────────────────────────────"
run "doc_version_sync"        python3 tools/doc_version_sync.py --check --quiet
run "reference_lint (table)"  python3 tools/reference_lint.py --kind table
run "reference_lint (figure)" python3 tools/reference_lint.py --kind figure
run "table_cells"            python3 tools/table_gen.py --check
run "citation_drift"         python3 tools/cite_check.py --index-only
run "section_map"             python3 tools/section_map.py --check
run "section_ref_audit"       python3 tools/section_ref_audit.py
run "rounding_lint"           python3 tools/rounding_lint.py
run "symbol_check"            python3 tools/symbol_check.py
run "build_figure_ledger"     python3 tools/build_figure_ledger.py --check
run "odt_media verify"        python3 tools/odt_media.py verify
run "pipeline_count_lint"     python3 tools/pipeline_count_lint.py
run "decision_lint"           python3 tools/decision_lint.py --quiet
run "doc_tier_lint"           python3 tools/doc_tier_lint.py
run "ms_chapters"             python3 tools/ms_chapters.py
run "bib_lint"                python3 tools/bib_lint.py
run "docref_lint"             python3 tools/docref_lint.py
run "ledger_lint"             python3 tools/ledger_lint.py
run "task_lint"               python3 tools/task_lint.py --open
run "register_lint"           python3 tools/register_lint.py
run "inequality_lint"         python3 tools/inequality_lint.py
run "session_handover"        python3 tools/session_handover.py --check

echo "─────────────────────────────────────────────────────────────────────"
if [ $rc -eq 0 ]; then printf "  ${G}DOC GATES PASS${N} — safe for a doc-only commit (run full check_all before a pipeline push)\n"
else printf "  ${R}DOC GATES FAILED${N}\n"; fi
exit $rc
