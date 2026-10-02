#!/usr/bin/env bash
# drive_token.sh — hand the cloud environment a fresh Drive token in one command (run on the laptop).
#
# The rclone client is published (2026-10-02) with the drive.file scope only, so its token no longer
# lapses every seven days (T-65 closed). Use this when the cloud reports DRIVE TOKEN REFUSED (a revoked
# token, or an old secret) or after setting up a new machine:
#   1. `rclone config reconnect gdrivefile:` — opens the browser for Google's consent (answer the
#      Shared Drive question n: drive.file may not list shared drives, and rclone aborts on y);
#   2. checks the new token against the folder;
#   3. puts the [gdrivefile] section of rclone.conf, base64-encoded as one NRG_RCLONE_CONF_B64= line, on
#      the clipboard (wl-copy, xclip or xsel), never on the screen, ready to paste into the cloud
#      environment's variables (tools/cloud_setup.sh decodes it). With no clipboard tool it writes the line
#      to a private file and says where.
#
# A credential is never typed into a Claude conversation (CLAUDE.md §4g): paste it into the environment
# settings only. Progress is printed as numbered steps.
#
# Usage:  bash tools/drive_token.sh
#
# Version 1.2.0 — Hollingham (2026) — 2026-10-02. The remote is gdrivefile (drive.file, published client);
#   the check is lsf of NRG_documents_v2. 1.1.0 — 2026-10-02. One NRG_RCLONE_CONF_B64= line (a multi-line
#   value did not survive the environment editor). 1.0.0 — 2026-10-02. First issue.
set -euo pipefail
REMOTE="gdrivefile"
FOLDER="NRG_documents_v2"
step() { printf '  [%s] %s\n' "$1" "$2"; }

command -v rclone >/dev/null || { echo "  rclone is not installed (bash tools/nrg_env.sh --system)"; exit 1; }

step "1/3" "reconnect ${REMOTE}: (a browser window opens for Google's consent)"
rclone config reconnect "${REMOTE}:"

step "2/3" "checking the new token against Drive"
if rclone lsf "${REMOTE}:${FOLDER}" --max-depth 1 >/dev/null 2>&1; then
  echo "      Drive accepts the token (${REMOTE}:${FOLDER} lists)"
else
  echo "      Drive REFUSED the token — run this again"; exit 1
fi

step "3/3" "the [${REMOTE}] section for the cloud secret NRG_RCLONE_CONF_B64"
CONF="$(rclone config file | tail -1)"
SECTION="$(awk -v s="[${REMOTE}]" '$0==s{p=1;print;next} /^\[/{p=0} p' "$CONF")"
[ -n "$SECTION" ] || { echo "      no [${REMOTE}] section in $CONF"; exit 1; }
# One line, base64: a multi-line value does not survive the environment editor (2026-10-02).
SECTION="NRG_RCLONE_CONF_B64=$(printf '%s\n' "$SECTION" | base64 -w0)"
if command -v wl-copy >/dev/null 2>&1; then printf '%s\n' "$SECTION" | wl-copy; where="clipboard (wl-copy)"
elif command -v xclip >/dev/null 2>&1; then printf '%s\n' "$SECTION" | xclip -selection clipboard; where="clipboard (xclip)"
elif command -v xsel >/dev/null 2>&1; then printf '%s\n' "$SECTION" | xsel --clipboard --input; where="clipboard (xsel)"
else
  OUT="${HOME}/.config/rclone/nrg_rclone_conf_for_cloud.txt"
  ( umask 077; printf '%s\n' "$SECTION" > "$OUT" ); where="$OUT (readable by you only; delete it after pasting)"
fi
echo "      copied to the ${where}"
echo
echo "  Now paste the line into the cloud environment's Environment variables (it starts NRG_RCLONE_CONF_B64=)"
echo "  (replace the old value), then start a new cloud session. Never paste it into a chat."
