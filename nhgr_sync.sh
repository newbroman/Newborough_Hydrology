#!/usr/bin/env bash
# ============================================================================
# nhgr_sync.sh - monthly one-command sync of the living forecaster to GitHub.
#
#   1. git pull (merge)    - bring down anything the frozen-PL chat pushed
#   2. rebuild the two feeds from the hub (everything in /living/)
#   3. show you what changed
#   4. ask before pushing  - nothing leaves your machine without a "y"
#   5. git commit + push
#
# Run it with:   cd ~/projects/NRG && ./nhgr_sync.sh
# ============================================================================
set -uo pipefail

# --- Your master folder (already correct for this machine) ------------------
REPO_DIR="${HOME}/projects/NRG"
# ----------------------------------------------------------------------------

LIVING="${REPO_DIR}/living"
HUB="${LIVING}/readings_living.csv"
CLUSTER_MAP="${REPO_DIR}/outputs/03_master_data.csv"   # a frozen PL output
FEED_JSON="${LIVING}/latest_readings.json"
MSL5_JSON="${LIVING}/forecaster_msl5.json"

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; C='\033[0;36m'; B='\033[1m'; N='\033[0m'
say()  { echo -e "\n${C}-- $1 --${N}"; }
ok()   { echo -e "  ${G}OK${N} $1"; }
fail() { echo -e "  ${R}x $1${N}"; }

cd "${REPO_DIR}" 2>/dev/null || {
    fail "Can't find your folder at: ${REPO_DIR}"
    echo  "  Edit the REPO_DIR line near the top of this script."
    exit 1
}

say "Pulling anything new from GitHub (merge)"
git pull --no-rebase --no-edit || {
    fail "git pull hit a problem - STOP, do not push."
    echo  "  Most likely the frozen-PL chat changed the same file, or this folder"
    echo  "  isn't wired to GitHub yet. Run 'git status' and send it over before pushing."
    exit 1
}
ok "up to date"

say "Rebuilding the forecaster feeds from the hub"
python3 "${LIVING}/update_forecaster_feed.py" \
    --hub "${HUB}" --cluster-map "${CLUSTER_MAP}" --out "${FEED_JSON}"  || { fail "feed build failed"; exit 1; }
python3 "${LIVING}/update_forecaster_msl5.py" \
    --hub "${HUB}" --cluster-map "${CLUSTER_MAP}" --out "${MSL5_JSON}" || { fail "MSL5 build failed"; exit 1; }

say "What changed"
git add "${HUB}" "${FEED_JSON}" "${MSL5_JSON}"
if git diff --cached --quiet; then
    ok "nothing changed - nothing to push (the hub has no new readings yet)"
    exit 0
fi
git status --short

echo ""
read -rp "$(echo -e "${Y}Push these to GitHub? [y/N]: ${N}")" REPLY
if [[ "${REPLY}" =~ ^[Yy] ]]; then
    git commit -m "monthly forecaster update $(date +%Y-%m)" || { fail "commit failed"; exit 1; }
    git push || { fail "push failed - check your sign-in / git remote."; exit 1; }
    echo -e "\n  ${G}${B}Pushed.${N} The forecaster will refresh on GitHub Pages within a minute or two."
else
    echo "  Left unpushed. Your changes are staged - re-run when you're ready."
fi
