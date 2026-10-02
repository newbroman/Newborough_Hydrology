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
# (gdrivefile:NRG_documents_v2) - for a cloud session, the [gdrivefile] section of rclone.conf supplied
# as the secret NRG_RCLONE_CONF_B64 (base64, one line; tools/drive_token.sh writes it) or NRG_RCLONE_CONF - the ODTs are copied down with the same filter the
# archive uses. Without it the session works from the committed mirrors and does not edit
# ODTs. Taking the document lock (tools/doc_lock.py) before an ODT edit is still required.
#
# Pushing is Martin's call every time (CLAUDE.md section 7): this script never pushes.
#
# Version 1.1.2 — Hollingham (2026) — 2026-10-03. Refuses when the installed private exclude ignores
#   working/ (the first cloud-ship dry run failed at lock-push on a stale tracked exclude, now corrected).
# 1.1.1 — 2026-10-02. rclone comes from its GitHub release into ~/bin: the
#   cloud proxy refuses rclone.org (403), found by the first claude.ai/code token test, which PASSED.
# 1.1.0 — 2026-10-02. The remote is gdrivefile:NRG_documents_v2: the rclone
#   client is published with the drive.file scope only, so its token no longer lapses weekly (T-65), and
#   NRG_documents_v2 is the copy that remote created (rclone check: 656 files, 0 differences). The
#   remote is tested with lsf, which drive.file always permits.
# 1.0.3 — 2026-10-02. Reads NRG_RCLONE_CONF_B64 (one line, base64) as well as
#   NRG_RCLONE_CONF: a multi-line value did not survive the environment editor.
# 1.0.2 — 2026-10-02. The lapsed-token message names tools/drive_token.sh.
# 1.0.1 — 2026-10-02. rclone installed when a token is supplied;
#   a configured token that Drive refuses is reported as LAPSED with the refresh steps.
# 1.0.0 — 2026-10-02 (D-227). First issue.
set -euo pipefail
DIR="${1:-$HOME/NRG}"
PUB="${NRG_PUBLIC_URL:-https://github.com/newbroman/Newborough_Hydrology.git}"     # override for testing
PRIV="${NRG_PRIVATE_URL:-https://github.com/newbroman/Newborough_Hydrology_working.git}"
DRIVE_REMOTE="gdrivefile:NRG_documents_v2"
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
# 1.1.2: the private repo must be able to stage under working/ (its exclude ignores /* and re-includes
# /working/). The tracked copy of that exclude was a pre-2026-08-27 version without the re-include, so the
# first cloud-ship dry run could not stage the document lock. Fail here, naming the cause.
if git --git-dir=.git-working --work-tree=. check-ignore -q working/DOCUMENT_LOCK.json; then
  echo "      >>> the private repo IGNORES working/ - .git-working/info/exclude lacks !/working/"
  echo "      >>> (it is installed from working/.git-working/info/exclude). Not continuing."
  exit 1
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
# 1.0.3: the secret may come as NRG_RCLONE_CONF_B64 (the [gdrivefile] section base64-encoded on one line,
# which survives any .env editor; tools/drive_token.sh writes it) or as NRG_RCLONE_CONF (raw, multi-line).
if [ -z "${NRG_RCLONE_CONF:-}" ] && [ -n "${NRG_RCLONE_CONF_B64:-}" ]; then
  NRG_RCLONE_CONF="$(printf '%s' "$NRG_RCLONE_CONF_B64" | base64 -d 2>/dev/null || true)"
  [ -n "$NRG_RCLONE_CONF" ] || echo "      NRG_RCLONE_CONF_B64 is set but does not decode - re-copy it with tools/drive_token.sh"
fi
if [ -n "${NRG_RCLONE_CONF:-}" ] && [ ! -f "$HOME/.config/rclone/rclone.conf" ]; then
  mkdir -p "$HOME/.config/rclone"; printf '%s\n' "$NRG_RCLONE_CONF" > "$HOME/.config/rclone/rclone.conf"
  chmod 600 "$HOME/.config/rclone/rclone.conf"
fi
if [ -n "${NRG_RCLONE_CONF:-}" ] && ! command -v rclone >/dev/null 2>&1; then
  # 1.1.1: from rclone's GitHub release, into ~/bin. The cloud proxy refuses rclone.org (403, measured
  # 2026-10-02 by the first claude.ai/code token test); GitHub downloads are allowed. No sudo needed.
  RCLONE_VERSION="v1.68.2"
  _rz="/tmp/rclone-${RCLONE_VERSION}.zip"
  if curl -sSfL -o "$_rz" "https://github.com/rclone/rclone/releases/download/${RCLONE_VERSION}/rclone-${RCLONE_VERSION}-linux-amd64.zip"; then
    mkdir -p "$HOME/bin"
    python3 -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); n=[m for m in z.namelist() if m.endswith('/rclone')][0]; open(sys.argv[2],'wb').write(z.read(n))" \
      "$_rz" "$HOME/bin/rclone" && chmod +x "$HOME/bin/rclone" && echo "      rclone ${RCLONE_VERSION} installed in ~/bin"
  else
    echo "      rclone could not be downloaded from GitHub here"
  fi
fi
if command -v rclone >/dev/null 2>&1 && rclone lsf "$DRIVE_REMOTE" --max-depth 1 >/dev/null 2>&1; then
  rclone copy "$DRIVE_REMOTE" . --filter-from tools/rclone-odt-filter.txt --stats 10s --stats-one-line
  echo "      ODTs copied from $DRIVE_REMOTE"
else
  if [ -n "${NRG_RCLONE_CONF:-}" ] && command -v rclone >/dev/null 2>&1; then
    # A token is configured but Drive refuses it. Since 1.1.0 the client is published, so this
    # is no longer the weekly Testing lapse (T-65): the token was revoked, or the secret is an old
    # [gdrive] section. Say so loudly rather than burying it.
    echo "      >>> DRIVE TOKEN REFUSED - refresh it: on the laptop run"
    echo "      >>>     bash tools/drive_token.sh"
    echo "      >>> which puts the new [gdrivefile] section on the clipboard; paste it into the cloud"
    echo "      >>> environment's variables (NRG_RCLONE_CONF_B64=) and start a new session."
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
