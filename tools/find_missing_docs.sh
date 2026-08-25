#!/usr/bin/env bash
# find_missing_docs.sh — hunt the documents the live source cites and the
# repository does not contain (T-10). Read-only: it finds, it never moves.
#
# The list below is the searchable subset of docref_lint.py's KNOWN_DANGLING
# (29 entries; 'CHANGELOG.md' is too generic to search for by name).
#
#   bash tools/find_missing_docs.sh            names only, home + trash + mounts
#   bash tools/find_missing_docs.sh --content  also grep file CONTENTS, for a
#                                              document that was renamed
set -uo pipefail
LIST="$(mktemp)"; trap 'rm -f "$LIST"' EXIT
cat > "$LIST" <<'EOF'
AUDIT_10series_PRE_FELL_START.md
BETA2_DECOMPOSITION_UPDATED.md
CHANGELOG_date_formatting_sweep.md
CHANGELOG_delta_2026-06-30_scrape_drawdown_physics.md
CHANGELOG_delta_2026-08-08_pipe_top_upstand_correction.md
CHANGELOG_delta_2026-08-10_18_sy_spatial_trends.md
CHANGELOG_forecaster_simplification.md
DEFECT_NOTE_script20_residual_field_2026-08-06.md
DIAGNOSTIC_REPORT_script_26_cluster_assignment.md
FIGURE_LEDGER.md
FINDINGS_script21_summer_minima.md
FINDING_canopy_buffering_consolidated.md
HANDOVER_SCRIPT03_DATUM.md
HUB_CORRECTION_NOTE_2026-08-08.md
HANDOVER_c3_detrend_check.md
MODEL_SPECIFICATION_AUDIT.md
NRG_spring_BACI_spec_2026-08-13.md
NRG_window_policy_spec_2026-08-14.md
PLAN_differential_movement_writeup.md
REPORT_STRUCTURE.md
SCRAPING_EFFECTS_KNOWLEDGE.md
SPEC_script35_per_well_amplification_metric.md
SPEC_script37_scale_factor_regression_2026-07-06.md
SPEC_script37b_partB_comparative_footing_2026-07-06.md
c3_detrend_check_results.md
ledgers_DECISION_LOG_premerge_2026-08-16.md
methods_supplement_master_v1_9_7.md
paper2.md
EOF

# Every place a deleted or stray file can hide. -xdev per root so one slow
# network mount cannot stall the sweep; missing paths are skipped silently.
ROOTS=( "$HOME" /tmp /var/tmp )
for t in "$HOME/.local/share/Trash/files" "$HOME/.Trash" /media/*/.Trash-"$(id -u)" \
         /run/media/"$USER"/*/.Trash-"$(id -u)" /media/"$USER"/*; do
  [ -d "$t" ] && ROOTS+=( "$t" )
done

echo "== searching by FILENAME =="
for r in "${ROOTS[@]}"; do
  [ -d "$r" ] || continue
  find "$r" -xdev -type f -print 2>/dev/null | grep -Ff "$LIST" || true
done | sort -u | sed 's/^/  /'

echo
echo "== trash metadata (a Trash entry records where the file came from) =="
grep -rlFf "$LIST" "$HOME/.local/share/Trash/info" 2>/dev/null \
  | while read -r i; do echo "  $(basename "$i" .trashinfo)"; grep '^Path=' "$i"; done

if [ "${1:-}" = "--content" ]; then
  echo
  echo "== searching by CONTENT (catches a renamed file) =="
  for pat in "PRE_FELL_START" "BETA2_DECOMPOSITION" "canopy buffering" \
             "scrape drawdown physics" "per-well amplification" \
             "scale factor regression" "comparative footing" \
             "cluster assignment diagnostic" "window policy"; do
    hits=$(grep -rlI --exclude-dir=.git --include='*.md' --include='*.txt' \
             -- "$pat" "$HOME" 2>/dev/null | head -5)
    [ -n "$hits" ] && { echo "  [$pat]"; echo "$hits" | sed 's/^/     /'; }
  done
fi

echo
echo "Nothing is moved. Copy anything found into ~/projects/NRG and tell Claude."
