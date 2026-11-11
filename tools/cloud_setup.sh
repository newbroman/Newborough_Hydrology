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
# Version 1.4.0 — Hollingham (2026) — 2026-11-11. J-14 follow-ups: step 1 finishes a half-done PUBLIC checkout too
#   (a clone killed in its checkout leaves HEAD, no index, no files); both halves share finish_checkout(), which
#   fetches the missing blobs in one request (1,724 files in 19 s, against ~200 a minute one by one).
# 1.3.0 — Hollingham (2026) — 2026-11-11. T-198 (J-14): step 2 finishes a half-done private checkout.
#   A present .git-working no longer means a complete one: each of its steps is tested and completed on every run
#   (index, config, missing tracked files restored by name without -f, upstream, exclude). Do not wrap this
#   script in a timeout; run it in the background and read its log (CLAUDE.md section 4g).
# 1.2.0 — Hollingham (2026) — 2026-10-21. T-118: step 4 fetches only the files working/DRIVE_MANIFEST.json
#   names (tools/drive_manifest_list.py), not the superseded versions Drive keeps; the filter is the fallback
#   when the private store or its manifest is absent; an MD5 report follows.
# 1.1.4 — Hollingham (2026) — 2026-10-20. T-117: RCLONE_VERSION v1.68.2 -> v1.75.2, the version the L14 runs.
# 1.1.3 — Hollingham (2026) — 2026-10-03. The private clone's main tracks origin/main (a --bare
#   clone sets no upstream, so the dry3 dry run's lock push was refused).
# 1.1.2 — 2026-10-03. Refuses when the installed private exclude ignores
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

# finish_checkout GIT... — complete a checkout that a killed run left half done (1.3.0, T-198; 1.4.0 both halves).
# "Present" is not "complete": the HQ pass of 2026-11-11 ran this script under `timeout 170`, which cut the private
# checkout short, and every later run took the "present" branch and never checked the rest out (~2,159 files
# missing). A public clone killed in its checkout is worse: HEAD, no index, no files (measured 2026-11-11). So both
# halves come through here on EVERY run. Nothing that exists is overwritten: missing files are restored by name
# (no -f, never `reset --hard`), and only a file left EMPTY by the kill is rewritten.
# GIT is the repository's git command with its work tree, e.g. `git` or `git --git-dir=.git-working --work-tree=.`.
finish_checkout() {
  local gd missing total empty
  gd="$("$@" rev-parse --git-dir)"
  # No index means the run stopped before one was written; ls-files would then list nothing and read as complete.
  if [ ! -f "$gd/index" ]; then "$@" read-tree HEAD; echo "      index built (read-tree HEAD)"; fi
  missing="$("$@" ls-files --deleted | wc -l)"
  [ "$missing" -gt 0 ] || return 0
  total="$("$@" ls-files | wc -l)"
  echo "      checkout incomplete: $missing of $total tracked files missing - checking them out. Present files"
  echo "      are not touched. Do not time-limit this script; run it in the background and read its log."
  if [ "$missing" -lt "$total" ]; then
    "$@" ls-files --deleted | sed -n '1,5s/^/        missing: /p' || true
  fi
  # 1.4.0: fetch the missing blobs in ONE request, as `git clone` does for its own checkout. Left to itself,
  # checkout-index on a blobless clone fetches each blob separately: ~200 files a minute, measured 2026-11-11
  # (2,075 private files took 750 s), against 1,724 public files in 19 s batched. The command is the one git's
  # own lazy fetch runs; if it fails, checkout-index still fetches what it needs, only slowly.
  local t0=$SECONDS
  if "$@" ls-files -s --deleted | awk '{print $2}' | sort -u | \
     "$@" -c fetch.negotiationAlgorithm=noop fetch --quiet origin --no-tags --no-write-fetch-head \
        --recurse-submodules=no --filter=blob:none --stdin; then
    echo "      contents fetched in one request ($(( SECONDS - t0 )) s)"
  else
    echo "      batched fetch failed - checkout-index will fetch each file itself (slow)"
  fi
  "$@" ls-files --deleted -z | "$@" checkout-index -z --stdin
  # The file being written when the first run was killed is left EMPTY, not missing (measured: 0 bytes
  # against 20,621 in HEAD), so --deleted cannot see it. An empty file that differs from HEAD holds nothing
  # to lose; only those are rewritten with -f. A file with any content is left as it is.
  empty="$("$@" ls-files --modified | while IFS= read -r f; do [ -e "$f" ] && [ ! -s "$f" ] && printf '%s\n' "$f"; done || true)"
  if [ -n "$empty" ]; then
    printf '%s\n' "$empty" | sed 's/^/        empty (cut short): /'
    printf '%s\n' "$empty" | "$@" checkout-index -f --stdin
  fi
  missing="$("$@" ls-files --deleted | wc -l)"
  if [ "$missing" -gt 0 ]; then
    echo "      >>> $missing tracked files are still missing after checkout-index. Not continuing."
    exit 1
  fi
  echo "      checkout complete: $total tracked files present"
}

# ── 1/6 public repository: the working tree ────────────────────────────────────
step "1/6" "public repository → $DIR"
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" fetch --quiet origin main && git -C "$DIR" status -sb --untracked-files=no | sed -n 1p   # sed, not head: head closes the pipe on a long status and pipefail ends the script (1.4.0)
else
  # --filter=blob:none, NOT --depth: a partial clone has the FULL commit history and fetches
  # file contents on demand. A shallow clone does not, and on 2026-11-08 that cost a day:
  # a chat minting a task id takes max+1 over the ids it can SEE, two chats each saw only a
  # 50-commit window, both read T-182 as the maximum, and both minted T-183 and T-184 --
  # four tasks under two ids, found only at merge time. The same truncation made every
  # ahead/behind count meaningless (the private clone read 961 behind, which is the full
  # history it could not see) and produced a false "the histories have diverged" reading.
  git clone --quiet --filter=blob:none "$PUB" "$DIR"
fi
cd "$DIR"
if ! git rev-parse -q --verify HEAD >/dev/null; then
  echo "      >>> $DIR/.git has no HEAD - its clone did not finish. Move it aside (mv $DIR $DIR.broken) and re-run."
  exit 1
fi
finish_checkout git
grep -qx '/working/' .git/info/exclude 2>/dev/null || {
  printf '%s\n' "# The private half lives under /working (and a few forced paths), tracked by" \
    "# .git-working - never by this repository (CLAUDE.md section 4f)." "/working/" >> .git/info/exclude; }

# ── 2/6 private repository: a second git directory over the same tree ─────────
step "2/6" "private repository → $DIR/.git-working"
# 1.3.0 (T-198): each step tests its own result and is finished on every run, fresh clone or not.
WG=(git --git-dir=.git-working)
WT=(git --git-dir=.git-working --work-tree=.)
if [ -d .git-working ]; then
  echo "      present"
else
  git clone --quiet --bare --filter=blob:none "$PRIV" .git-working
  echo "      cloned"
fi
if ! "${WG[@]}" rev-parse -q --verify HEAD >/dev/null; then
  echo "      >>> .git-working has no HEAD - its clone did not finish. Nothing has been checked out from it,"
  echo "      >>> so nothing is lost: move it aside (mv .git-working .git-working.broken) and re-run."
  exit 1
fi
[ "$("${WG[@]}" config --get core.bare || true)" = false ] || "${WG[@]}" config core.bare false
"${WG[@]}" config --get remote.origin.fetch >/dev/null || \
  "${WG[@]}" config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
"${WG[@]}" config --get status.showUntrackedFiles >/dev/null || "${WG[@]}" config status.showUntrackedFiles no
"${WG[@]}" fetch --quiet origin
finish_checkout "${WT[@]}"
# 1.1.3: a --bare clone sets no upstream, so a plain `push` was refused (the dry3 dry run).
"${WG[@]}" rev-parse -q --verify 'main@{upstream}' >/dev/null 2>&1 || \
  "${WG[@]}" branch --quiet --set-upstream-to=origin/main main
# The private repo's own exclude is tracked inside it; install it over git's template (comments only),
# never over an installed copy, which a session may have changed.
if ! grep -qv '^[[:space:]]*\(#\|$\)' .git-working/info/exclude 2>/dev/null; then
  mkdir -p .git-working/info
  cp working/.git-working/info/exclude .git-working/info/exclude
  echo "      private exclude installed"
fi
echo "      merge GitHub's newer commits with: ./working/wgit pull"
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
  RCLONE_VERSION="v1.75.2"
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
  _list="$(mktemp)"
  if python3 tools/drive_manifest_list.py list "$DRIVE_REMOTE" > "$_list" 2>/dev/null; then
    rclone copy "$DRIVE_REMOTE" . --files-from "$_list" --no-traverse --stats 10s --stats-one-line
    echo "      $(wc -l < "$_list") current documents copied from $DRIVE_REMOTE (by working/DRIVE_MANIFEST.json)"
    python3 tools/drive_manifest_list.py verify | sed 's/^  /      /'
  else
    rclone copy "$DRIVE_REMOTE" . --filter-from tools/rclone-odt-filter.txt --stats 10s --stats-one-line
    echo "      ODTs copied from $DRIVE_REMOTE by filter (no usable manifest: superseded versions included)"
  fi
  rm -f "$_list"
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
