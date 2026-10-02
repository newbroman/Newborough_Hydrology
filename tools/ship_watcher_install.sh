#!/usr/bin/env bash
# ship_watcher_install.sh — install, remove or inspect the NRG ship watcher (systemd --user).
#
#   bash tools/ship_watcher_install.sh              # install + enable + start; prints status
#   bash tools/ship_watcher_install.sh --status     # the unit, the last status file, the log tail
#   bash tools/ship_watcher_install.sh --uninstall  # stop, disable, remove the unit
#
# Run on the laptop (the publishing machine), from anywhere: it finds the repository from its own
# path. It never touches the repository's content, never prints a credential, and needs no sudo.
# The unit runs only while Martin is logged in; `loginctl enable-linger` would keep it running
# without a session, which is NOT done here (a ship needs the desktop's LibreOffice closed anyway).
#
# Version 1.0.1 — 2026-10-02: restarts only a watcher already running, and never during a ship.
# 1.0.0 — Hollingham (2026) — 2026-10-02. First issue.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT="nrg-ship-watcher.service"
DEST_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
DEST="${DEST_DIR}/${UNIT}"
TEMPLATE="${REPO}/tools/ship_watcher.service"
WATCHER="${REPO}/tools/ship_watcher.sh"
STATUS="${REPO}/working/.ship_status.json"

step() { printf '  [%s] %s\n' "$1" "$2"; }
ok()   { printf '      OK   %s\n' "$*"; }
warn() { printf '      WARN %s\n' "$*"; }
bad()  { printf '      FAIL %s\n' "$*"; }

command -v systemctl >/dev/null 2>&1 || { echo "systemctl not found - this needs systemd"; exit 1; }
systemctl --user show-environment >/dev/null 2>&1 \
  || { echo "no systemd user manager reachable (run this from your desktop session, not over ssh/sudo)"; exit 1; }

show_status() {
  step "1/3" "unit ${UNIT}"
  systemctl --user status "$UNIT" --no-pager --lines=0 2>/dev/null | sed 's/^/      /' || echo "      not installed"
  step "2/3" "last ship request (working/.ship_status.json)"
  if [[ -f "$STATUS" ]]; then sed 's/^/      /' "$STATUS"; else echo "      none yet"; fi
  [[ -f "${REPO}/working/.ship_request" ]] && echo "      a request is PENDING: working/.ship_request"
  step "3/3" "journal, last 15 lines"
  journalctl --user -u "$UNIT" -n 15 --no-pager 2>/dev/null | sed 's/^/      /' || true
}

case "${1:-}" in
  --status) show_status; exit 0 ;;
  --uninstall)
    step "1/2" "stop and disable ${UNIT}"
    systemctl --user disable --now "$UNIT" 2>/dev/null && ok "stopped and disabled" || warn "was not enabled"
    step "2/2" "remove ${DEST}"
    if [[ -f "$DEST" ]]; then rm -f "$DEST"; ok "removed"; else warn "not present"; fi
    systemctl --user daemon-reload
    systemctl --user reset-failed "$UNIT" 2>/dev/null || true
    echo
    echo "  Uninstalled. working/.ship_status.json, working/.ship_requests_done/ and the logs in"
    echo "  scratch/ are left as the record. A pending working/.ship_request will not be acted on."
    exit 0 ;;
  "") ;;
  *) sed -n '2,12p' "$0"; exit 2 ;;
esac

# ── install ────────────────────────────────────────────────────────────────────
step "1/5" "preflight (repository ${REPO})"
fails=0
for f in "$TEMPLATE" "$WATCHER" "${REPO}/working/nrg_git.sh"; do
  [[ -f "$f" ]] && ok "${f#$REPO/}" || { bad "missing ${f#$REPO/}"; fails=1; }
done
for f in "$WATCHER" "${REPO}/working/nrg_git.sh"; do
  [[ -f "$f" ]] && { bash -n "$f" && ok "bash -n ${f#$REPO/}" || { bad "syntax error in ${f#$REPO/}"; fails=1; }; }
done
[[ -x "${REPO}/venv/bin/python" ]] && ok "venv/ present" || warn "no venv/ - build it first: bash tools/nrg_env.sh"
for t in soffice rclone pdftotext git python3; do
  command -v "$t" >/dev/null 2>&1 && ok "$t on PATH" || warn "$t not on PATH - the ship will fail at the step that needs it"
done
[[ -x "$HOME/bin/pandoc" ]] && ok "pandoc in ~/bin" || warn "no ~/bin/pandoc - refresh_mirrors needs pandoc 3.1.3 (tools/nrg_env.sh installs it)"
# Credentials: report presence only, never content.
( cd "$REPO" && git config --get credential.helper >/dev/null ) && ok "public repo has a credential helper" \
  || warn "public repo: no credential.helper - a ship cannot push without one (CLAUDE.md section 4)"
( cd "$REPO" && git --git-dir=.git-working config --get credential.helper >/dev/null 2>&1 ) && ok "private repo has a credential helper" \
  || warn "private repo: no credential.helper - the second push of every ship will fail"
[[ -f "$HOME/.config/rclone/rclone.conf" ]] && ok "rclone config present (the Drive token still lapses weekly)" \
  || warn "no rclone config - every ship will end PARTIAL (archive failed)"
systemctl --user show-environment | grep -q '^LANG=' && ok "user manager has a LANG" \
  || warn "user manager has no LANG; the watcher falls back to C.UTF-8"
(( fails == 0 )) || { echo; echo "  Not installed: fix the FAIL lines above."; exit 1; }

step "2/5" "write ${DEST}"
mkdir -p "$DEST_DIR"
sed "s#@REPO@#${REPO}#g" "$TEMPLATE" > "${DEST}.tmp"
mv -f "${DEST}.tmp" "$DEST"
command -v systemd-analyze >/dev/null 2>&1 && { systemd-analyze --user verify "$DEST" 2>&1 | sed 's/^/      /' || true; }
ok "unit written"

step "3/5" "daemon-reload"
systemctl --user daemon-reload && ok "reloaded"

step "4/5" "enable --now"
# 1.0.1 (2026-10-02): restart ONLY a watcher that was already running before this install (so an updated
# script takes effect), and never while a ship holds the watcher lock. 1.0.0 restarted unconditionally,
# so on a first install the freshly started watcher picked up a waiting request and the restart killed
# that ship 18 s in (request ship-20261002T104310Z, interrupted, nothing committed).
was_active=0; systemctl --user is-active --quiet "$UNIT" && was_active=1
systemctl --user enable --now "$UNIT" 2>&1 | sed 's/^/      /'
if (( was_active )); then
  if [[ -e "${REPO}/working/.ship_watcher.lock" ]]; then
    warn "a ship is running (working/.ship_watcher.lock): NOT restarting; run this again when it has finished"
  else
    systemctl --user restart "$UNIT" && ok "restarted (the updated watcher script takes effect)"
  fi
fi
sleep 2
systemctl --user is-active --quiet "$UNIT" && ok "active" || { bad "not active - see the journal below"; }

step "5/5" "status"
show_status
echo
echo "  Installed. A ship is requested by writing working/.ship_request (see README_ship_watcher)."
echo "  Follow it live:   journalctl --user -u ${UNIT} -f"
echo "  Remove it:        bash tools/ship_watcher_install.sh --uninstall"
