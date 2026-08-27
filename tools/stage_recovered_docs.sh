#!/usr/bin/env bash
# stage_recovered_docs.sh — copy every candidate found by find_missing_docs.sh
# into the repo so Claude can read them over the bridge (which sees only
# ~/projects/NRG). Copies only: sources are never moved, renamed or deleted.
#
#   bash tools/stage_recovered_docs.sh           stage into working/updates/_recovered_<today>/
#   bash tools/stage_recovered_docs.sh --dry-run show what it would copy
#
# Identical content is staged once. Differing copies of the same name are all
# staged, tagged by origin and content hash, so the newest is not assumed
# correct. MANIFEST.tsv records where each came from.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
REPO="$PWD"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

DEST="$REPO/working/updates/_recovered_$(date +%F)"
[ "$DRY" -eq 0 ] && mkdir -p "$DEST"
MAN="$DEST/MANIFEST.tsv"

# One list, shared with find_missing_docs.sh — never duplicated here.
LIST="$(mktemp)"; trap 'rm -f "$LIST"' EXIT
# One list, owned by docref_lint.py — never duplicated here.
python3 "$REPO/tools/docref_lint.py" --list-missing > "$LIST" || {
  echo "cannot read the missing-document list from tools/docref_lint.py" >&2; exit 1; }
n_names=$(grep -c . "$LIST")
echo "== staging candidates for $n_names document name(s) =="
[ "$DRY" -eq 0 ] && printf 'name\tstaged_as\tsource\tmtime\tbytes\tsha256\n' > "$MAN"

# shellcheck source=/dev/null
source "$REPO/tools/_search_roots.sh"
roots=( "${ROOTS[@]}" )
echo "== ${#roots[@]} search root(s); cloud drives included (NRG_SKIP_CLOUD=1 to skip) =="

staged=0; skipped=0
while IFS= read -r name; do
  [ -z "$name" ] && continue
  hits=""
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
    while IFS= read -r p; do
      case "$p" in
        "$REPO"/*) continue ;;            # already in the tree
        */.git/*)  continue ;;
      esac
      hits="$hits$p"$'\n'
    done < <(find "$root" -xdev -type f -name "$name" 2>/dev/null)
  done
  [ -z "$hits" ] && continue
  # Dedup is per NAME, not global: two different documents can hold identical
  # bytes (a stub, a one-line note) and both are wanted.
  seen_hashes=""

  while IFS= read -r src; do
    [ -z "$src" ] && continue
    h=$(sha256sum "$src" 2>/dev/null | cut -c1-12) || continue
    case "$seen_hashes" in *"$h"*) skipped=$((skipped+1)); continue ;; esac
    seen_hashes="$seen_hashes $h"
    case "$src" in
      *"/Trash/files/"*|*"/.Trash"*|*".Trash-"*) tag=trash ;;
      *"/Downloads/"*)                           tag=downloads ;;
      *"/audit/"*)                               tag=audit ;;
      *"/tmp"*)                                  tag=tmp ;;
      *)                                         tag=disk ;;
    esac
    base="${name%.md}"
    out="${base}__${tag}_${h}.md"
    mt=$(date -r "$src" +%F' '%T 2>/dev/null || echo unknown)
    sz=$(stat -c%s "$src" 2>/dev/null || echo 0)
    if [ "$DRY" -eq 1 ]; then
      printf '  %-58s <- %s  (%s, %s bytes)\n' "$out" "$src" "$mt" "$sz"
    else
      # cp -n so a re-run never clobbers a staged file. The name carries the
      # content hash, so an existing file of that name IS this content - record
      # the row either way, or a second run would produce an empty manifest.
      [ -e "$DEST/$out" ] || cp "$src" "$DEST/$out" 2>/dev/null
      printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$out" "$src" "$mt" "$sz" "$h" >> "$MAN"
    fi
    staged=$((staged+1))
  done <<< "$hits"
done < "$LIST"

echo
if [ "$DRY" -eq 1 ]; then
  echo "dry run: $staged file(s) would be staged, $skipped duplicate(s) skipped"
else
  echo "staged $staged file(s) into working/updates/_recovered_$(date +%F)/"
  echo "$skipped byte-identical duplicate(s) skipped"
  echo "manifest: $MAN"
  echo
  echo "Nothing has been committed. Tell Claude it is there."
fi
