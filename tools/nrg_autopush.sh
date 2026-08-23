#!/usr/bin/env bash
# ============================================================================
# nrg_autopush.sh  -  VERSION 1.0.0  (2026-08-12)
# Non-interactive commit + pull + push for the NRG repo, with a mass-deletion
# safety net. Runs on YOUR machine (has network) - never via the Cowork bridge
# (which is network-blocked). Triggered by nrg_push_watch.sh when a sentinel
# appears, or run by hand: bash tools/nrg_autopush.sh
#
# SAFETY NET
#   * "delete all" guard: refuses to commit/push if the staged change would
#     delete more than NRG_MAX_DEL_ABS files OR NRG_MAX_DEL_FRAC % of the repo.
#     On trip it unstages, commits nothing, pushes nothing, and records why.
#   * never force-pushes; aborts and reverts the merge on any pull conflict.
#   * clears only a STALE .git/index.lock (none running) - never a live one.
# ============================================================================
set -uo pipefail

REPO_DIR="${HOME}/projects/NRG"
STATE_DIR="${REPO_DIR}/.nrg_push"
LOG="${STATE_DIR}/autopush.log"
RESULT="${STATE_DIR}/result"
MAX_DEL_ABS="${NRG_MAX_DEL_ABS:-30}"     # abort if more than this many files deleted
MAX_DEL_FRAC="${NRG_MAX_DEL_FRAC:-25}"   # ...or this % (or more) of tracked files

mkdir -p "$STATE_DIR"
ts(){ date +'%Y-%m-%d %H:%M:%S'; }
log(){ echo "[$(ts)] $*" >> "$LOG"; }
finish(){ echo "$1" > "$RESULT"; log "RESULT: $1"; exit "${2:-0}"; }

cd "$REPO_DIR" 2>/dev/null || { echo "FAILED: no repo at $REPO_DIR" > "$RESULT"; exit 1; }

# stale lock only (safe: no git process running)
if [[ -e .git/index.lock ]] && ! pgrep -x git >/dev/null 2>&1; then
  rm -f .git/index.lock && log "cleared stale .git/index.lock"
fi

git add -A || finish "FAILED: git add error." 1

# ---- mass-deletion safety net --------------------------------------------
deletions=$(git diff --cached --diff-filter=D --name-only | wc -l | tr -d ' ')
tracked=$(git ls-tree -r HEAD --name-only 2>/dev/null | wc -l | tr -d ' ')
[[ "$tracked" -lt 1 ]] && tracked=1
frac=$(( deletions * 100 / tracked ))
if [[ "$deletions" -gt "$MAX_DEL_ABS" || "$frac" -ge "$MAX_DEL_FRAC" ]]; then
  git reset -q
  log "SAFETY: mass-deletion guard tripped: ${deletions} deletions = ${frac}% of ${tracked} tracked (limits: >${MAX_DEL_ABS} abs or >=${MAX_DEL_FRAC}%). Nothing committed or pushed."
  finish "BLOCKED: ${deletions} files (${frac}%) would be deleted - over the safety limit. Left uncommitted; review and push by hand if truly intended." 3
fi

# ---- commit / pull / push -------------------------------------------------
if ! git diff --cached --quiet; then
  msg="autopush $(ts)"
  git commit -q -m "$msg" || finish "FAILED: commit error." 1
  log "committed: $msg  (${deletions} deletions, within guard)"
else
  log "nothing staged to commit"
fi

if ! git pull --no-rebase --no-edit origin main >>"$LOG" 2>&1; then
  if git ls-files -u | grep -q .; then
    git merge --abort 2>>"$LOG"
    finish "FAILED: pull conflict - merge aborted, nothing pushed. Resolve by hand." 2
  fi
  finish "FAILED: pull error (see autopush.log) - nothing pushed." 2
fi

ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
if [[ "$ahead" == "0" ]]; then finish "OK: nothing to push (already up to date)." 0; fi
if git push origin main >>"$LOG" 2>&1; then
  finish "OK: pushed ${ahead} commit(s) to GitHub." 0
else
  finish "FAILED: push error (see autopush.log)." 2
fi
