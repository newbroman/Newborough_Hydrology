#!/usr/bin/env bash
# cloud_setup.sh — a Claude cloud session's working copy of the project, in one command (D-227).
#
# Lays out what the publishing machine has: the public repository as the working tree, the
# private repository (Newborough_Hydrology_working) as a second git directory `.git-working`
# over the SAME tree (CLAUDE.md section 4f), each excluding the other's half; then the pinned
# environment (tools/nrg_env.sh), the ODTs from Drive when a token is available, and the
# session handover (D-143).
#
# Usage (from anywhere; nothing needs to exist beforehand):
#   curl -sSL https://raw.githubusercontent.com/newbroman/Newborough_Hydrology/main/tools/cloud_setup.sh | bash -s -- [DIR]
#   bash tools/cloud_setup.sh [DIR]        # DIR defaults to $HOME/NRG
#
# Drive (D-227 E5, route a): if rclone is configured with the remote that nrg_git.sh uses
# (gdrive:NRG_documents) - for a cloud session, an rclone.conf supplied as the secret
# NRG_RCLONE_CONF (the file's contents) - the ODTs are copied down with the same filter the
# archive uses. Without it the session works from the committed mirrors and does not edit
# ODTs. Taking the document lock (tools/doc_lock.py) before an ODT edit is still required.
#
# Pushing is Martin's call every time (CLAUDE.md section 7): this script never pushes.
#
# Version 1.0.1 — Hollingham (2026) — 2026-10-02. rclone installed when a token is supplied;
#   a configured token that Drive refuses is reported as LAPSED with the refresh steps.
# 1.0.0 — 2026-10-02 (D-227). First issue.
set -euo pipefail
DIR="${1:-$HOME/NRG}"
PUB="${NRG_PUBLIC_URL:-https://github.com/newbroman/Newborough_Hydrology.git}"     # override for testing
PRIV="${NRG_PRIVATE_URL:-https://github.com/newbroman/Newborough_Hydrology_working.git}"
DRIVE_REMOTE="gdrive:NRG_documents"
step() { printf '\n  [%s] %s\n' "$1" "$2"; }

# ── 1/6 public repository: the working tree ────────────────────────────────────
step "1/6" "public repository → $DIR"
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" fetch --quiet origin main && git -C "$DIR" status -sb | head -1
else
  git clone --quiet --depth 50 "$PUB" "$DIR"
fi
cd "$DIR"
grep -qx '/working/' .git/info/exclude 2>/dev/null || {
  printf '%s\n' "# The private half lives under /working (and a few forced paths), tracked by" \
    "# .git-working - never by this repository (CLAUDE.md section 4f)." "/working/" >> .git/info/exclude; }

# ── 2/6 private repository: a second git directory over the same tree ─────────
step "2/6" "private repository → $DIR/.git-working"
if [ -d .git-working ]; then
  git --git-dir=.git-working --work-tree=. fetch --quiet origin
  echo "      present; fetched (merge with: ./working/wgit pull)"
else
  git clone --quiet --bare --depth 50 "$PRIV" .git-working
  git --git-dir=.git-working config core.bare false
  git --git-dir=.git-working config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
  git --git-dir=.git-working config status.showUntrackedFiles no
  git --git-dir=.git-working --work-tree=. read-tree HEAD
  git --git-dir=.git-working --work-tree=. checkout-index -a -f
  git --git-dir=.git-working --work-tree=. fetch --quiet origin
  # The private repo's own exclude is tracked inside it; install it.
  cp working/.git-working/info/exclude .git-working/info/exclude
fi
for k in user.name user.email; do
  v="$(git config "$k" || true)"; [ -n "$v" ] && git --git-dir=.git-working config "$k" "$v"
done
echo "      $(git --git-dir=.git-working --work-tree=. log --oneline -1)"

# ── 3/6 the pinned environment ─────────────────────────────────────────────────
step "3/6" "environment (tools/nrg_env.sh)"
bash tools/nrg_env.sh | sed 's/^/  /'
export PATH="$HOME/bin:$PATH"

# ── 4/6 the ODTs from Drive ────────────────────────────────────────────────────
step "4/6" "documents from Drive"
if [ -n "${NRG_RCLONE_CONF:-}" ] && [ ! -f "$HOME/.config/rclone/rclone.conf" ]; then
  mkdir -p "$HOME/.config/rclone"; printf '%s\n' "$NRG_RCLONE_CONF" > "$HOME/.config/rclone/rclone.conf"
  chmod 600 "$HOME/.config/rclone/rclone.conf"
fi
if [ -n "${NRG_RCLONE_CONF:-}" ] && ! command -v rclone >/dev/null 2>&1; then
  curl -sSL https://rclone.org/install.sh | sudo bash >/dev/null 2>&1 \
    || echo "      rclone could not be installed here"
fi
if command -v rclone >/dev/null 2>&1 && rclone about "$DRIVE_REMOTE" >/dev/null 2>&1; then
  rclone copy "$DRIVE_REMOTE" . --filter-from tools/rclone-odt-filter.txt --stats 10s --stats-one-line
  echo "      ODTs copied from $DRIVE_REMOTE"
else
  if [ -n "${NRG_RCLONE_CONF:-}" ] && command -v rclone >/dev/null 2>&1; then
    # A token is configured but Drive refuses it: the weekly lapse of the rclone-nrg client
    # (still in Google's Testing status, T-65). Martin refreshes it weekly (2026-10-02), so
    # say so loudly rather than burying it.
    echo "      >>> DRIVE TOKEN LAPSED - refresh it: on the laptop run"
    echo "      >>>     rclone config reconnect gdrive:"
    echo "      >>> then paste the new [gdrive] section of ~/.config/rclone/rclone.conf into the"
    echo "      >>> cloud environment's NRG_RCLONE_CONF and start a new session."
  else
    echo "      NOT FETCHED: no rclone remote $DRIVE_REMOTE here (rclone absent or NRG_RCLONE_CONF"
    echo "      unset). This session works from the committed mirrors and must not edit ODTs."
  fi
fi

# ── 5/6 what binds this session ────────────────────────────────────────────────
step "5/6" "document lock"
venv/bin/python tools/doc_lock.py status 2>/dev/null | sed 's/^/      /' || echo "      (doc_lock status unavailable)"

step "6/6" "session handover (D-143): read working/HANDOVER_BOOTSTRAP.md next"
venv/bin/python tools/session_handover.py | tail -25
