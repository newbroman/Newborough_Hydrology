#!/usr/bin/env bash
# drive_pull.sh — bring the documents down from Drive before editing on this machine.
#
# The other half of nrg_git.sh option 11 (which copies UP at a ship). Pull before you edit, archive
# when you ship, and hold the document lock in between (CLAUDE.md §4b): Drive has no conflict
# detection, so the lock is the protocol.
#
# --update: a file that is NEWER here than on Drive is kept, never overwritten — so an edit not yet
# archived survives a pull. Only the ODT/ODM set in tools/rclone-odt-filter.txt is touched.
# The remote is read from working/nrg_git.sh (DRIVE_REMOTE), so it is named in one place.
#
# Usage:  bash tools/drive_pull.sh             # pull
#         bash tools/drive_pull.sh --dry-run   # list what would change, change nothing
#
# Version 1.0.0 — Hollingham (2026) — 2026-10-02. First issue (with the switch to gdrivefile:NRG_documents_v2).
set -euo pipefail
cd "$(dirname "$0")/.."
step() { printf '  [%s] %s\n' "$1" "$2"; }
REMOTE="$(sed -n 's/^DRIVE_REMOTE="\([^"]*\)".*/\1/p' working/nrg_git.sh 2>/dev/null | head -1)"
REMOTE="${REMOTE:-gdrivefile:NRG_documents_v2}"
DRY=""; [ "${1:-}" = "--dry-run" ] && DRY="--dry-run"

command -v rclone >/dev/null || { echo "  rclone is not installed (bash tools/nrg_env.sh --system)"; exit 1; }

step "1/3" "document lock"
if ! python3 tools/doc_lock.py check; then
  echo "  WARNING: another machine holds the documents - its edits may not be on Drive yet."
  echo "           Pulling is safe (nothing here newer than Drive is overwritten), but do not edit until it is released."
fi

step "2/3" "reaching $REMOTE"
rclone lsf "$REMOTE" --max-depth 1 >/dev/null 2>&1 \
  || { echo "  cannot reach $REMOTE - run: bash tools/drive_token.sh"; exit 1; }

step "3/3" "copying documents down${DRY:+ (dry run: nothing changes)}"
rclone copy "$REMOTE" . --filter-from tools/rclone-odt-filter.txt --update $DRY --progress
echo "  done. Take the lock before editing:  python3 tools/doc_lock.py take --note \"what you are editing\""
