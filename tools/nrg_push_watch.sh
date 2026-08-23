#!/usr/bin/env bash
# ============================================================================
# nrg_push_watch.sh  -  VERSION 1.0.0  (2026-08-12)
# Cron watcher. When the sentinel file ~/projects/NRG/.nrg_push/request appears,
# run nrg_autopush.sh once and remove the sentinel. Install in your crontab:
#   * * * * * /home/john/projects/NRG/tools/nrg_push_watch.sh
# flock ensures a slow push never overlaps the next minute's tick.
# ============================================================================
set -uo pipefail
REPO_DIR="${HOME}/projects/NRG"
STATE_DIR="${REPO_DIR}/.nrg_push"
SENTINEL="${STATE_DIR}/request"
LOCK="${STATE_DIR}/watch.lock"
WORKER="${REPO_DIR}/tools/nrg_autopush.sh"
mkdir -p "$STATE_DIR"

[[ -e "$SENTINEL" ]] || exit 0                 # nothing requested - quiet exit
exec 9>"$LOCK" || exit 0
flock -n 9 || exit 0                            # a previous push is still running

note="$(cat "$SENTINEL" 2>/dev/null || true)"
rm -f "$SENTINEL"                               # consume inside the lock
echo "[$(date +'%F %T')] sentinel seen (note: ${note:-none}) - running autopush" >> "${STATE_DIR}/watch.log"
bash "$WORKER"
