#!/usr/bin/env bash
# ============================================================================
# nhgr_sync.sh - one-command sync to GitHub.
#
#   1. git pull (merge)    - bring down anything pushed since last time
#   2. stage web tools     - copy the two HTML tools from outputs/ up to root
#                            (where GitHub Pages serves them)
#   3. rebuild the feeds    - regenerate the two forecaster JSONs from the hub
#   4. show what changed
#   5. ask, then commit + push
#
# Run with:   cd ~/projects/NRG && ./nhgr_sync.sh
# ============================================================================
set -uo pipefail

REPO_DIR="${HOME}/projects/NRG"

LIVING="${REPO_DIR}/living"
HUB="${LIVING}/readings_living.csv"
CLUSTER_MAP="${REPO_DIR}/outputs/03_master_data.csv"
FEED_JSON="${LIVING}/latest_readings.json"
MSL5_JSON="${LIVING}/forecaster_msl5.json"

# web tools: outputs/ source  ->  repo-root dest (the name index.html links to)
SCATTER_SRC="${REPO_DIR}/outputs/14_climate_projections/14_seasonal_extremes_scatter.html"
SCATTER_DST="${REPO_DIR}/seasonal_extremes_scatter.html"
VIEWER_SRC="${REPO_DIR}/outputs/19_spatial_groundwater/scenario_viewer.html"
VIEWER_DST="${REPO_DIR}/scenario_viewer.html"

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; C='\033[0;36m'; B='\033[1m'; N='\033[0m'
say()  { echo -e "\n${C}-- $1 --${N}"; }
ok()   { echo -e "  ${G}OK${N} $1"; }
fail() { echo -e "  ${R}x $1${N}"; }
stage_one() { if [[ -f "$1" ]]; then cp -f "$1" "$2" && echo "  staged: $(basename "$2")"; else echo -e "  ${Y}!! missing source: $1${N}"; fi; }

cd "${REPO_DIR}" 2>/dev/null || { fail "Can't find ${REPO_DIR}"; exit 1; }

say "Pulling anything new from GitHub"
git pull --no-rebase --no-edit || {
    fail "git pull hit a problem - STOP, do not push. Run 'git status' and send it over."
    exit 1
}
ok "up to date"

say "Staging web tools to repo root"
stage_one "${SCATTER_SRC}" "${SCATTER_DST}"
stage_one "${VIEWER_SRC}"  "${VIEWER_DST}"

say "Rebuilding the forecaster feeds from the hub"
python3 "${LIVING}/update_forecaster_feed.py" \
    --hub "${HUB}" --cluster-map "${CLUSTER_MAP}" --out "${FEED_JSON}"  || { fail "feed build failed"; exit 1; }
python3 "${LIVING}/update_forecaster_msl5.py" \
    --hub "${HUB}" --cluster-map "${CLUSTER_MAP}" --out "${MSL5_JSON}" || { fail "MSL5 build failed"; exit 1; }

say "What changed"
git add "${HUB}" "${FEED_JSON}" "${MSL5_JSON}" "${SCATTER_DST}" "${VIEWER_DST}"
if git diff --cached --quiet; then
    ok "nothing changed - nothing to push"
    exit 0
fi
git status --short

echo ""
read -rp "$(echo -e "${Y}Push these to GitHub? [y/N]: ${N}")" REPLY
if [[ "${REPLY}" =~ ^[Yy] ]]; then
    git commit -m "sync $(date +%Y-%m-%d): feeds + web tools" || { fail "commit failed"; exit 1; }
    git push || { fail "push failed - check your sign-in / git remote."; exit 1; }
    echo -e "\n  ${G}${B}Pushed.${N} GitHub Pages will refresh within a minute or two."
else
    echo "  Left unpushed. Your changes are staged - re-run when ready."
fi
