#!/usr/bin/env bash
# find_missing_docs.sh — hunt the documents the live source cites and the
# repository does not contain (T-10). Read-only: it finds, it never moves.
#
# The list comes from docref_lint.py --list-missing, so it can never drift
# from what the linter is actually freezing.
#
#   bash tools/find_missing_docs.sh            names only, home + trash + mounts
#   bash tools/find_missing_docs.sh --content  also grep file CONTENTS, for a
#                                              document that was renamed
set -uo pipefail
LIST="$(mktemp)"; trap 'rm -f "$LIST"' EXIT
# One list, one place. docref_lint.py owns it: KNOWN_DANGLING minus the three
# documents that are missing by ruling (see its RETIRED dict) minus names too
# generic to search by. Never keep a second copy here.
python3 "$(dirname "$0")/docref_lint.py" --list-missing > "$LIST" || {
  echo "cannot read the missing-document list from tools/docref_lint.py" >&2; exit 1; }
echo "== $(grep -c . "$LIST") document(s) to look for =="

# Where to look. tools/_search_roots.sh owns that list — including the cloud
# drives, which -xdev would otherwise skip.
# shellcheck source=/dev/null
source "$(dirname "$0")/_search_roots.sh"
echo "== ${#ROOTS[@]} search root(s); cloud drives included (NRG_SKIP_CLOUD=1 to skip) =="

echo "== searching by FILENAME =="
for r in "${ROOTS[@]}"; do
  [ -d "$r" ] || continue
  printf '  ... %s\n' "$r" >&2
  find "$r" -xdev -type f -print 2>/dev/null | grep -Ff "$LIST" || true
done | sort -u | sed 's/^/  /'

echo
echo "== trash metadata (a Trash entry records where the file came from) =="
grep -rlFf "$LIST" "$HOME/.local/share/Trash/info" 2>/dev/null \
  | while read -r i; do echo "  $(basename "$i" .trashinfo)"; grep '^Path=' "$i"; done

if [ "${1:-}" = "--content" ]; then
  echo
  echo "== searching by CONTENT (catches a renamed file) =="
  for pat in "PRE_FELL_START" "BETA2_DECOMPOSITION" "canopy buffering" \
             "scrape drawdown physics" "per-well amplification" \
             "scale factor regression" "comparative footing" \
             "cluster assignment diagnostic" "window policy"; do
    hits=$(grep -rlI --exclude-dir=.git --include='*.md' --include='*.txt' \
             -- "$pat" "${ROOTS[@]}" 2>/dev/null | sort -u | head -8)
    [ -n "$hits" ] && { echo "  [$pat]"; echo "$hits" | sed 's/^/     /'; }
  done
fi

echo
echo "Nothing is moved. Copy anything found into ~/projects/NRG and tell Claude."
