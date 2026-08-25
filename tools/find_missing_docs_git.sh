#!/usr/bin/env bash
# find_missing_docs_git.sh — for documents that exist nowhere on disk, look in
# git history. A file that was committed and later deleted is still in the
# object store; the working tree just does not show it.
#
#   bash tools/find_missing_docs_git.sh            report only
#   bash tools/find_missing_docs_git.sh --recover  extract what it finds
#
# Searches every repo it can see, including the audit clone and NRG_plan, and
# both git directories over the NRG working tree.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
REPO="$PWD"
RECOVER=0; [ "${1:-}" = "--recover" ] && RECOVER=1
DEST="$REPO/Updates_required/_recovered_$(date +%F)"
[ "$RECOVER" -eq 1 ] && mkdir -p "$DEST"

LIST="$(mktemp)"; trap 'rm -f "$LIST"' EXIT
python3 "$REPO/tools/docref_lint.py" --list-missing > "$LIST" || {
  echo "cannot read the missing-document list from tools/docref_lint.py" >&2; exit 1; }

# Candidate git dirs. The NRG tree has two; the audit clone and the plan dir
# are separate repos. Missing paths are skipped silently.
gitdirs=()
for g in "$REPO/.git" "$REPO/.git-working" "$REPO/wgit" \
         "$HOME/audit/Newborough_Hydrology/.git" \
         "$HOME/projects/NRG_plan/.git"; do
  [ -d "$g" ] && gitdirs+=("$g")
done
# Anything else that looks like a clone of this project.
while IFS= read -r g; do
  case " ${gitdirs[*]} " in *" $g "*) continue ;; esac
  gitdirs+=("$g")
done < <(find "$HOME" -xdev -maxdepth 4 -type d -name .git 2>/dev/null | grep -i -E 'newborough|NRG' || true)

echo "== searching ${#gitdirs[@]} git store(s) =="
for g in "${gitdirs[@]}"; do echo "   $g"; done
echo

found=0; miss=0
while IFS= read -r name; do
  [ -z "$name" ] && continue
  hit=0
  for g in "${gitdirs[@]}"; do
    # --all covers every branch and tag; --diff-filter=D finds the deletion.
    while IFS=$'\t' read -r sha date path; do
      [ -z "$sha" ] && continue
      hit=1; found=$((found+1))
      echo "  $name"
      echo "      $path"
      echo "      last seen $date in ${g}  ${sha:0:9}"
      if [ "$RECOVER" -eq 1 ]; then
        out="$DEST/${name%.md}__git_${sha:0:7}.md"
        if git --git-dir="$g" show "${sha}:${path}" > "$out" 2>/dev/null; then
          echo "      recovered -> $(basename "$out")"
        else
          rm -f "$out"
          echo "      could not extract (blob missing from this store)"
        fi
      else
        echo "      git --git-dir=$g show ${sha:0:9}:$path"
      fi
    done < <(
      git --git-dir="$g" log --all --pretty=format:'%H%x09%ad' --date=short \
          --name-only --diff-filter=AM -- "*/$name" "$name" 2>/dev/null |
      awk -v RS='' '{
        split($0, L, "\n"); split(L[1], H, "\t");
        for (i=2; i<=length(L); i++) if (L[i] != "") print H[1] "\t" H[2] "\t" L[i];
        exit
      }'
    )
    [ "$hit" -eq 1 ] && break
  done
  [ "$hit" -eq 0 ] && { miss=$((miss+1)); echo "  -- no history anywhere: $name"; }
done < "$LIST"

echo
echo "$found document(s) located in history, $miss with no trace"
if [ "$RECOVER" -eq 1 ]; then
  echo "extracted into Updates_required/_recovered_$(date +%F)/"
  echo "Nothing committed. Tell Claude it is there."
else
  echo "re-run with --recover to extract them"
fi
