#!/usr/bin/env bash
# ============================================================================
# nrg_git.sh - Newborough git toolkit.
# Safe order of operations: COMMIT your work first, THEN pull, THEN push.
# Handles the "local changes would be overwritten by merge" situation.
# ============================================================================
set -uo pipefail

REPO_DIR="${HOME}/projects/NRG"
LIVING="${REPO_DIR}/living"
HUB="${LIVING}/readings_living.csv"
CLUSTER_MAP="${REPO_DIR}/outputs/03_master_data.csv"
FEED_JSON="${LIVING}/latest_readings.json"
MSL5_JSON="${LIVING}/forecaster_msl5.json"
SCATTER_SRC="${REPO_DIR}/outputs/14_climate_projections/14_seasonal_extremes_scatter.html"
SCATTER_DST="${REPO_DIR}/seasonal_extremes_scatter.html"
VIEWER_SRC="${REPO_DIR}/outputs/19_spatial_groundwater/scenario_viewer.html"
VIEWER_DST="${REPO_DIR}/scenario_viewer.html"

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; C='\033[0;36m'; B='\033[1m'; N='\033[0m'
say(){  echo -e "\n${C}-- $1 --${N}"; }
ok(){   echo -e "  ${G}OK${N} $1"; }
fail(){ echo -e "  ${R}x $1${N}"; }

cd "${REPO_DIR}" 2>/dev/null || { echo -e "${R}Can't find ${REPO_DIR}${N}"; read -rp "Press Enter to close"; exit 1; }

# --- helpers ---------------------------------------------------------------
stage_all(){ git add -A; }
have_staged(){ ! git diff --cached --quiet; }   # true (0) when something is staged

commit_staged(){                                # $1 = message; prompt if empty
  local msg="$1"
  if [[ -z "$msg" ]]; then
    read -rp "$(echo -e "${Y}Short description of these changes: ${N}")" msg
    [[ -z "$msg" ]] && msg="update $(date +%Y-%m-%d)"
  fi
  git commit -m "$msg"
}

handle_conflicts(){                             # called when a pull conflicts
  local conflicted
  conflicted=$(git diff --name-only --diff-filter=U)
  [[ -z "$conflicted" ]] && return 0
  fail "Merge conflict - these files were changed both on your PC and on GitHub:"
  echo "$conflicted" | sed 's/^/      /'
  echo ""
  echo "  How do you want to resolve them?"
  echo -e "    ${B}k${N}) Keep GitHub's version   (usual choice when the pipeline pushed updated scripts)"
  echo -e "    ${B}m${N}) Keep My version         (when your local copy is the one to keep)"
  echo -e "    ${B}a${N}) Abort                   (undo the merge, change nothing, get help)"
  echo ""
  read -rp "Choose [k/m/a]: " cr
  case "$cr" in
    k|K) while IFS= read -r f; do [[ -n "$f" ]] && git checkout --theirs -- "$f" && git add "$f"; done <<< "$conflicted"
         git commit --no-edit && ok "kept GitHub's versions - merge complete"; return 0 ;;
    m|M) while IFS= read -r f; do [[ -n "$f" ]] && git checkout --ours   -- "$f" && git add "$f"; done <<< "$conflicted"
         git commit --no-edit && ok "kept your versions - merge complete"; return 0 ;;
    *)   git merge --abort; fail "merge aborted - nothing changed. Your committed work is safe."; return 1 ;;
  esac
}

integrate(){                                    # pull remote in; assumes clean/committed tree
  say "Pulling latest from GitHub"
  if git pull origin main --no-rebase --no-edit; then ok "merged with GitHub"; return 0
  else handle_conflicts; return $?; fi
}

push_if_ahead(){                                # push only if we have commits GitHub doesn't
  local ahead
  ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
  if [[ "$ahead" == "0" ]]; then ok "GitHub already up to date - nothing to push."; return 0; fi
  say "Ready to push ${ahead} commit(s) to GitHub"
  git log --oneline origin/main..HEAD | sed 's/^/      /'
  echo ""
  read -rp "$(echo -e "${Y}Push now? [y/N]: ${N}")" r
  if [[ "$r" =~ ^[Yy] ]]; then
    git push && echo -e "  ${G}${B}Pushed.${N} Pages refreshes in a minute or two." || fail "push failed - choose 4) Status."
  else
    echo "  Not pushed. Your commit is saved locally - run the option again when ready."
  fi
}

# --- main actions ----------------------------------------------------------
do_push(){
  stage_all
  if have_staged; then
    say "Your local changes (committing these first)"
    git status --short
    echo ""
    commit_staged "" || { fail "commit failed"; return; }
    ok "committed on your PC"
  else
    ok "no new local changes to commit"
  fi
  integrate || return
  push_if_ahead
}

do_sync(){
  # 1) commit any stray local edits FIRST, so the pull can't be blocked
  stage_all
  if have_staged; then
    say "You have other local changes - committing them first"
    git status --short
    echo ""
    commit_staged "" || { fail "commit failed"; return; }
  fi
  # 2) get latest from GitHub
  integrate || return
  # 3) rebuild the live outputs
  say "Staging web tools to root"
  [[ -f "$SCATTER_SRC" ]] && cp -f "$SCATTER_SRC" "$SCATTER_DST" && echo "  staged seasonal_extremes_scatter.html" || echo "  (no scatter source - skipped)"
  [[ -f "$VIEWER_SRC"  ]] && cp -f "$VIEWER_SRC"  "$VIEWER_DST"  && echo "  staged scenario_viewer.html"        || echo "  (no viewer source - skipped)"
  say "Rebuilding forecaster feeds from the hub"
  python3 "$LIVING/update_forecaster_feed.py" --hub "$HUB" --cluster-map "$CLUSTER_MAP" --out "$FEED_JSON"  || { fail "feed build failed"; return; }
  python3 "$LIVING/update_forecaster_msl5.py" --hub "$HUB" --cluster-map "$CLUSTER_MAP" --out "$MSL5_JSON" || { fail "MSL5 build failed"; return; }
  git add "$HUB" "$FEED_JSON" "$MSL5_JSON" "$SCATTER_DST" "$VIEWER_DST"
  if have_staged; then
    git commit -m "monthly forecaster update $(date +%Y-%m)" && ok "feeds committed"
  else
    ok "feeds unchanged - nothing new to commit"
  fi
  # 4) push
  push_if_ahead
}

do_size(){
  say "Repository size"
  local total dotgit nfiles tsize
  total=$(du -sh --exclude=.git "$REPO_DIR" 2>/dev/null | cut -f1)
  dotgit=$(du -sh "$REPO_DIR/.git" 2>/dev/null | cut -f1)
  nfiles=$(git ls-files | wc -l | tr -d ' ')
  tsize=$(git ls-files -z | du -ch --files0-from=- 2>/dev/null | tail -1 | cut -f1)

  echo "  On your disk:"
  echo "    Working tree (all your files):    ${total:-?}"
  echo "    Git storage (.git folder):        ${dotgit:-?}"
  echo ""
  echo "  Tracked by git (what gets pushed / cloned):"
  echo "    Files tracked:                    ${nfiles:-?}"
  echo "    Their total size:                 ${tsize:-?}"
  echo ""
  echo "  Biggest top-level folders on disk:"
  du -sh "$REPO_DIR"/*/ 2>/dev/null | sort -rh | head | sed 's/^/      /'
  echo ""
  echo -e "  ${Y}Note:${N} working-tree size includes gitignored folders (venv/, Living_output/)"
  echo "  that stay on your machine and are never pushed. The 'tracked' figures above"
  echo "  are what actually lives in the repo. If .git is far bigger than the tracked"
  echo "  size, sweep up dead objects with:  git gc --prune=now"
}

do_cleanup(){
  say "Clean up git storage"
  local before after
  before=$(du -sh "$REPO_DIR/.git" 2>/dev/null | cut -f1)
  echo "  Current .git size: ${before:-?}"
  echo "  This sweeps up unreferenced (dead) objects. It does NOT touch your files,"
  echo "  your commits, or anything on GitHub - purely local housekeeping."
  echo ""
  read -rp "$(echo -e "${Y}Run cleanup now? [y/N]: ${N}")" r
  [[ "$r" =~ ^[Yy] ]] || { echo "  Skipped."; return; }
  rm -f "$REPO_DIR/.git/gc.log"
  git gc --prune=now && ok "first pass done" || fail "gc reported a problem"
  after=$(du -sh "$REPO_DIR/.git" 2>/dev/null | cut -f1)
  echo -e "  .git size now: ${B}${after:-?}${N}  (was ${before:-?})"
  echo ""
  read -rp "$(echo -e "${Y}Run the deeper sweep too (expire reflog + gc)? [y/N]: ${N}")" r2
  if [[ "$r2" =~ ^[Yy] ]]; then
    git reflog expire --expire=now --all && git gc --prune=now && ok "deep sweep done" || fail "deep sweep reported a problem"
    after=$(du -sh "$REPO_DIR/.git" 2>/dev/null | cut -f1)
    echo -e "  .git size now: ${B}${after:-?}${N}"
  fi
}

# --- menu ------------------------------------------------------------------
while true; do
  echo ""
  echo -e "${C}${B}===== Newborough Git Toolkit =====${N}"
  echo "  1) Sync forecaster      (monthly: rebuild feeds + web tools, then push)"
  echo "  2) Push my changes      (commit + push anything I've edited OR added)"
  echo "  3) Pull latest          (just fetch what's on GitHub)"
  echo "  4) Status               (show what's changed, untracked, etc.)"
  echo "  5) Repo size            (how big the repo and git history are)"
  echo "  6) Clean up git storage (sweep up dead objects, shrink .git)"
  echo "  7) Quit"
  echo ""
  read -rp "Choose [1-7]: " choice
  case "$choice" in
    1) do_sync ;;
    2) do_push ;;
    3) integrate ;;
    4) say "Current status"; git status ;;
    5) do_size ;;
    6) do_cleanup ;;
    7) echo "Bye."; break ;;
    *) echo "Please pick 1-7." ;;
  esac
done
