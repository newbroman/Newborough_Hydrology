#!/usr/bin/env bash
# ============================================================================
# push_frozen.sh - commit and push your own local changes to GitHub.
# Works for anything you've edited: a script, the report, outputs, docs.
# Pulls first, shows you what changed, asks for a message, pushes on your "y".
# ============================================================================
set -uo pipefail
REPO_DIR="${HOME}/projects/NRG"

Y='\033[1;33m'; G='\033[0;32m'; R='\033[0;31m'; C='\033[0;36m'; B='\033[1m'; N='\033[0m'

cd "${REPO_DIR}" 2>/dev/null || { echo -e "${R}Can't find ${REPO_DIR}${N}"; exit 1; }

echo -e "${C}-- Pulling anything new from GitHub first --${N}"
git pull origin main --no-rebase --no-edit || {
    echo -e "${R}pull hit a problem - STOP. Run 'git status' and get help before pushing.${N}"
    exit 1
}

git add -A
if git diff --cached --quiet; then
    echo -e "${G}Nothing has changed - nothing to push.${N}"
    exit 0
fi

echo -e "\n${C}-- These changes will be pushed --${N}"
git status --short
N_FILES=$(git diff --cached --name-only | wc -l)
echo -e "\n(${N_FILES} file(s) changed)"
if (( N_FILES > 200 )); then
    echo -e "${Y}That's a lot of files. If you re-ran the whole pipeline, that's expected;${N}"
    echo -e "${Y}otherwise take a look before pushing.${N}"
fi

echo ""
read -rp "$(echo -e "${Y}Short description of these changes: ${N}")" MSG
[[ -z "${MSG}" ]] && MSG="update $(date +%Y-%m-%d)"
read -rp "$(echo -e "${Y}Push to GitHub? [y/N]: ${N}")" REPLY
if [[ "${REPLY}" =~ ^[Yy] ]]; then
    git commit -m "${MSG}" || { echo -e "${R}commit failed${N}"; exit 1; }
    git push || { echo -e "${R}push failed - check your sign-in, or run 'git status'.${N}"; exit 1; }
    echo -e "${G}${B}Pushed.${N}"
else
    echo "Left unpushed. Your changes are staged - re-run when ready."
fi
