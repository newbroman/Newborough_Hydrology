#!/usr/bin/env bash
# slim_history.sh - strip superseded binary versions from both NRG repositories' history (D-257).
#
# WHAT IT KEEPS
#   Public repository (Newborough_Hydrology): every commit, every message, every date, and the whole
#   history of every text file (code, mirrors, CSVs, markdown). From BINARY files (figures, PDFs,
#   films, Office files) it keeps every version that is
#     - in the tip of any branch (main, gh-pages, any other),
#     - in any tag (each Zenodo release: V.0.9.0, v0.9.2.23, ...), or
#     - embedded in a current ODT in this tree. tools/reembed_figures.py identifies an ODT's copy of
#       a figure by finding its blob in the figure's history; a version still embedded must survive.
#   and strips every other version. gh-pages becomes one commit with no history (publish_pages has
#   worked that way since nrg_git.sh 1.30.0).
#   Private repository (Newborough_Hydrology_working): the regenerable caches named between the
#   "private-repo caches" markers in .gitignore are removed from ALL of its history. They stay on
#   this machine's disk, ignored.
#
# WHAT IT NEEDS
#   Run from the project root on the publishing machine (the ODTs must be here), with both
#   repositories committed and pushed, no chat holding a claim, and no ship running. It refuses
#   otherwise. git-filter-repo must be installed (sudo apt install git-filter-repo).
#
# USAGE
#   bash tools/slim_history.sh                 # dry run: what would go, how big each repo would be
#   bash tools/slim_history.sh --apply         # back up, rewrite, force-push, resync this machine
#   bash tools/slim_history.sh --resync        # ANOTHER machine after a slim: adopt GitHub's history
#   options: --public-only | --private-only | --backup-dir DIR (default ~/NRG_history_backups)
#
# Every --apply writes a git bundle of each repository's full history BEFORE anything changes
# (restore: git clone <bundle>), and the old->new commit maps to notes/history_maps/ (public) and
# working/history_maps/ (private), so a commit hash quoted in a dated record can still be resolved.
#
# Pushing is Martin's call (CLAUDE.md section 7): --apply asks before the first push.
#
# Version 1.0.0 - Hollingham (2026) - 2026-10-11 (D-257). First issue.
set -euo pipefail

PUB_URL="${NRG_PUBLIC_URL:-https://github.com/newbroman/Newborough_Hydrology.git}"
PRIV_URL="${NRG_PRIVATE_URL:-https://github.com/newbroman/Newborough_Hydrology_working.git}"
BIN_EXT_RE='\.(png|jpe?g|gif|tiff?|bmp|webp|pdf|mp4|webm|mov|avi|docx?|odt|ods|odm|xlsx?|pptx?|zip|gz|npz|npy|bundle)$'
PUSH_CHUNKS="${SLIM_PUSH_CHUNKS:-8}"   # GitHub's smart-HTTP upload times out on one large push

MODE=dry; DO_PUB=1; DO_PRIV=1; BACKUP_DIR="${HOME}/NRG_history_backups"
while (( $# )); do
  case "$1" in
    --apply) MODE=apply ;;
    --resync) MODE=resync ;;
    --public-only) DO_PRIV=0 ;;
    --private-only) DO_PUB=0 ;;
    --backup-dir) BACKUP_DIR="$2"; shift ;;
    -h|--help) sed -n '2,36p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (try --help)"; exit 2 ;;
  esac
  shift
done

R=$'\033[31m'; G=$'\033[32m'; Y=$'\033[33m'; C=$'\033[36m'; B=$'\033[1m'; N=$'\033[0m'
say(){ echo -e "\n${C}-- $1 --${N}"; }
ok(){ echo -e "  ${G}OK${N} $1"; }
warn(){ echo -e "  ${Y}note${N} $1"; }
die(){ echo -e "  ${R}x $1${N}"; exit 1; }
mb(){ awk -v b="$1" 'BEGIN{printf "%.0f MB", b/1048576}'; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not inside the project's git tree"
cd "$ROOT"
[[ -d .git-working ]] || die "no .git-working here - run this from the project root (CLAUDE.md section 4f)"
wgit(){ git --git-dir="$ROOT/.git-working" --work-tree="$ROOT" "$@"; }
STAMP="$(date +%Y-%m-%d_%H%M)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/nrg_slim.XXXXXX")"
trap '[[ "$MODE" == apply ]] && echo -e "\n  working copies kept in ${WORK} (delete when done)" || rm -rf "$WORK"' EXIT

# --- the private cache patterns: ONE list, in .gitignore between the markers ------------------
cache_patterns(){
  sed -n '/^# >>> private-repo caches/,/^# <<< private-repo caches/p' .gitignore \
    | grep -vE '^\s*(#|$)'
}
# .gitignore pattern -> git-filter-repo --path-glob (fnmatch: * also crosses /)
to_filter_glob(){
  local p="$1"
  p="${p%/}"; p="${p//\*\*\//}"
  if [[ "$1" == */ ]]; then echo "${p}/*"; else echo "$p"; fi
}

# --- refusals shared by --apply and --resync --------------------------------------------------
require_clean(){
  local label="$1"; shift
  if [[ -n "$("$@" status --porcelain --untracked-files=no 2>/dev/null)" ]]; then
    "$@" status --short --untracked-files=no | head -15 | sed 's/^/      /'
    die "${label}: uncommitted changes to tracked files - commit or ship them first"
  fi
}
require_pushed(){
  local label="$1"; shift
  "$@" fetch -q origin || die "${label}: could not fetch from GitHub"
  [[ "$("$@" rev-parse HEAD)" == "$("$@" rev-parse origin/main)" ]] \
    || die "${label}: local main and GitHub differ - ship or pull first, so GitHub holds everything"
}
require_quiet(){
  [[ -f working/.ship_watcher.lock ]] && die "the ship watcher holds working/.ship_watcher.lock - wait for the ship"
  local held
  held="$(python3 tools/doc_lock.py claims --json 2>/dev/null \
          | python3 -c 'import json,sys; h=json.load(sys.stdin).get("held") or {}; print("\n".join(f"{k}  ({v.get(\"chat\")})" for k,v in h.items()))' 2>/dev/null || true)"
  if [[ -n "$held" ]]; then
    echo "$held" | sed 's/^/      /'
    die "a chat holds a claim - every chat must ship and release before history is rewritten (python3 tools/work_board.py)"
  fi
}

# --- public: what to keep, what to strip ------------------------------------------------------
# $1 = a repository with full history. Writes $WORK/pub_strip.txt (blob ids) and prints a report.
plan_public(){
  local repo="$1" keep="$WORK/pub_keep.txt" all="$WORK/pub_blobs.txt"
  : > "$keep"
  local ref
  while IFS= read -r ref; do
    git -C "$repo" ls-tree -r "$ref" | awk '$2=="blob"{print $3}' >> "$keep"
  done < <(git -C "$repo" for-each-ref --format='%(refname)' refs/heads refs/tags refs/remotes/origin 2>/dev/null \
           | grep -v '/HEAD$')
  # blobs embedded in the ODTs on this machine (reembed_figures matches by blob id)
  local n_odt=0 odt
  echo "  reading the figures embedded in this tree's ODTs ..."
  while IFS= read -r -d '' odt; do
    n_odt=$((n_odt+1)); (( n_odt % 10 == 0 )) && echo "      ${n_odt} ODTs read"
    python3 - "$odt" >> "$keep" <<'PY'
import hashlib, sys, zipfile
try:
    z = zipfile.ZipFile(sys.argv[1])
except Exception:
    sys.exit(0)
for i in z.infolist():
    if i.filename.startswith("Pictures/"):
        d = z.read(i.filename)
        print(hashlib.sha1(b"blob %d\0" % len(d) + d).hexdigest())
PY
  done < <(find . \( -path ./scratch -o -path ./archive -o -path ./docs/media_store -o -path ./.git -o -path ./.git-working -o -path ./_to_delete \) -prune \
             -o -name '*.odt' -print0)
  (( n_odt > 0 )) || die "no ODTs found in this tree - run on the machine that holds them (tools/drive_pull.sh), or figures embedded in them would be stripped"
  sort -u -o "$keep" "$keep"
  git -C "$repo" rev-list --objects --all \
    | git -C "$repo" cat-file --batch-check='%(objecttype) %(objectname) %(objectsize:disk) %(rest)' \
    | awk '$1=="blob"' > "$all"
  python3 - "$all" "$keep" "$WORK/pub_strip.txt" "$BIN_EXT_RE" "$n_odt" <<'PY'
import collections, re, sys
allf, keepf, outf, ext_re, n_odt = sys.argv[1:6]
keep = set(open(keepf).read().split())
bin_re = re.compile(ext_re, re.I)
total = strip = 0; seen = set(); by = collections.Counter(); out = open(outf, "w")
for line in open(allf):
    p = line.rstrip("\n").split(" ", 3)
    sha, disk = p[1], int(p[2]); path = p[3] if len(p) > 3 else ""
    if sha in seen: continue
    seen.add(sha); total += disk
    if sha in keep or not bin_re.search(path): continue
    strip += disk; out.write(sha + "\n")
    by["/".join(path.split("/")[:2]) if "/" in path else path] += disk
M = 1048576
print(f"  blobs in history: {total/M:.0f} MB (compressed); kept from tips, tags and {n_odt} ODTs")
print(f"  superseded binary versions to strip: {strip/M:.0f} MB")
for k, v in by.most_common(8):
    print(f"      {v/M:7.0f} MB  {k}")
print(f"  expected size after: about {(total-strip)/M:.0f} MB")
PY
}

# --- private: what the cache patterns remove ---------------------------------------------------
plan_private(){
  local repo="$1"
  mapfile -t PATS < <(cache_patterns)
  (( ${#PATS[@]} )) || die ".gitignore has no 'private-repo caches' block - nothing to strip privately"
  git -C "$repo" rev-list --objects --all \
    | git -C "$repo" cat-file --batch-check='%(objecttype) %(objectname) %(objectsize:disk) %(rest)' \
    | awk '$1=="blob"' > "$WORK/priv_blobs.txt"
  python3 - "$WORK/priv_blobs.txt" "${PATS[@]}" <<'PY'
import collections, fnmatch, sys
pats = [p.rstrip("/") for p in sys.argv[2:]]
def hit(path):
    for p in pats:
        g = p.replace("**/", "*")
        if fnmatch.fnmatch(path, g) or fnmatch.fnmatch(path, g + "/*"): return p
    return None
total = gone = 0; seen = set(); by = collections.Counter()
for line in open(sys.argv[1]):
    q = line.rstrip("\n").split(" ", 3)
    sha, disk = q[1], int(q[2]); path = q[3] if len(q) > 3 else ""
    if sha in seen: continue
    seen.add(sha); total += disk
    h = hit(path)
    if h: gone += disk; by[h] += disk
M = 1048576
print(f"  blobs in history: {total/M:.0f} MB (compressed)")
print(f"  cache files to remove from every commit: {gone/M:.0f} MB")
for k, v in by.most_common(): print(f"      {v/M:7.0f} MB  {k}")
print(f"  expected size after: about {(total-gone)/M:.0f} MB")
PY
}

# --- push a rewritten branch in stages -----------------------------------------------------------
push_staged(){
  local repo="$1" url="$2" branch="$3" revs n step i first=1 tries
  mapfile -t revs < <(git -C "$repo" rev-list --first-parent --reverse "refs/heads/$branch")
  n=${#revs[@]}; (( n )) || return 0
  step=$(( (n + PUSH_CHUNKS - 1) / PUSH_CHUNKS )); (( step > 0 )) || step=1
  for (( i = step - 1; ; i += step )); do
    (( i >= n - 1 )) && i=$(( n - 1 ))
    for tries in 1 2; do
      if (( first )); then
        git -C "$repo" push --progress --force "$url" "${revs[$i]}:refs/heads/$branch" && break
      else
        git -C "$repo" push --progress "$url" "${revs[$i]}:refs/heads/$branch" && break
      fi
      (( tries == 2 )) && die "push of ${branch} stopped at commit $((i+1))/${n}. GitHub now holds part of the new history; re-run the push step: git -C ${repo} push --force ${url} ${branch}"
      warn "push attempt failed, retrying once"; sleep 5
    done
    first=0
    echo "      [ $(( 100 * (i+1) / n )) %  ${branch}: $((i+1))/${n} commits on GitHub ]"
    (( i == n - 1 )) && break
  done
}

# --- adopt GitHub's rewritten history in this tree ----------------------------------------------
# every local branch other than main: follow GitHub's rewritten copy, or say it pins old history
adopt_branches(){
  local b
  while IFS= read -r b; do
    [[ "$b" == main ]] && continue
    if "$@" rev-parse -q --verify "refs/remotes/origin/$b" >/dev/null; then
      "$@" update-ref "refs/heads/$b" "refs/remotes/origin/$b"
    else
      warn "local branch '$b' is not on GitHub and still holds the old history - delete it (branch -D $b) or the space is not freed"
    fi
  done < <("$@" for-each-ref --format='%(refname:short)' refs/heads)
  "$@" rev-parse -q --verify refs/stash >/dev/null && warn "a stash exists and holds old history - drop it when done"
  return 0
}
resync_public(){
  say "public repository: adopting GitHub's history"
  git fetch -q --force origin '+refs/heads/*:refs/remotes/origin/*' || die "fetch failed"
  git fetch -q --force origin '+refs/tags/*:refs/tags/*' || die "tag fetch failed"
  local here there
  here="$(git rev-parse 'HEAD^{tree}')"; there="$(git rev-parse 'origin/main^{tree}')"
  [[ "$here" == "$there" ]] || die "this machine's main has content GitHub's lacks (trees differ). Nothing changed here. Ship it first, or compare: git diff origin/main HEAD --stat"
  git reset -q origin/main
  adopt_branches git
  git reflog expire --expire=now --all && git gc -q --prune=now
  ok "public .git now $(du -sh .git | cut -f1)"
}
resync_private(){
  say "private repository: adopting GitHub's history"
  wgit fetch -q --force origin '+refs/heads/*:refs/remotes/origin/*' || die "private fetch failed"
  # the private tip changes (the caches leave the index), so compare everything EXCEPT them
  local pats=() p
  while IFS= read -r p; do pats+=( ":(exclude,glob)${p%/}" ":(exclude,glob)${p%/}/**" ); done < <(cache_patterns)
  if ! wgit diff --quiet origin/main HEAD -- working "${pats[@]}" 2>/dev/null; then
    wgit diff --stat origin/main HEAD -- working "${pats[@]}" | tail -5 | sed 's/^/      /'
    die "the private repo here has records GitHub's lacks - push them first (nrg_git.sh 2)"
  fi
  wgit reset -q origin/main
  adopt_branches wgit
  wgit reflog expire --expire=now --all && wgit gc -q --prune=now
  ok "private .git-working now $(du -sh .git-working | cut -f1); the caches stay on disk, untracked and ignored"
}

# ================================================================================================
echo -e "${C}${B}===== NRG history slim (${MODE}) =====${N}"

if [[ "$MODE" == resync ]]; then
  (( DO_PUB )) && { require_clean "public" git; resync_public; }
  (( DO_PRIV )) && resync_private
  ok "this machine now matches GitHub"
  exit 0
fi

if [[ "$MODE" == dry ]]; then
  if (( DO_PUB )); then
    say "public repository (from this clone; fetching GitHub's branches and tags first)"
    git fetch -q origin '+refs/heads/*:refs/remotes/origin/*' --tags 2>/dev/null || warn "could not fetch - using what is here"
    [[ "$(git rev-parse --is-shallow-repository)" == true ]] && die "this clone is shallow - the dry run needs full history (git fetch --unshallow)"
    plan_public "$ROOT/.git"
  fi
  if (( DO_PRIV )); then
    say "private repository (from this clone)"
    plan_private "$ROOT/.git-working"
  fi
  echo ""
  echo "  Dry run only - nothing changed. To do it:  bash tools/slim_history.sh --apply"
  exit 0
fi

# --- apply ------------------------------------------------------------------------------------
command -v git-filter-repo >/dev/null || git filter-repo --version >/dev/null 2>&1 \
  || die "git-filter-repo is not installed:  sudo apt install git-filter-repo   (or pipx install git-filter-repo)"
require_quiet
(( DO_PUB )) && { require_clean "public" git; require_pushed "public" git; }
(( DO_PRIV )) && { require_clean "private" wgit; require_pushed "private" wgit; }
mkdir -p "$BACKUP_DIR"

if (( DO_PUB )); then
  say "public: fresh copy from GitHub"
  git clone --progress --bare "$PUB_URL" "$WORK/pub.git" || die "clone failed"
  git -C "$WORK/pub.git" bundle create --progress "$BACKUP_DIR/Newborough_Hydrology_${STAMP}.bundle" --all
  git bundle verify -q "$BACKUP_DIR/Newborough_Hydrology_${STAMP}.bundle" >/dev/null || die "backup bundle failed to verify"
  ok "backup: $BACKUP_DIR/Newborough_Hydrology_${STAMP}.bundle ($(du -h "$BACKUP_DIR/Newborough_Hydrology_${STAMP}.bundle" | cut -f1))"
  plan_public "$WORK/pub.git"
fi
if (( DO_PRIV )); then
  say "private: fresh copy from GitHub"
  git clone --progress --bare "$PRIV_URL" "$WORK/priv.git" || die "clone failed"
  git -C "$WORK/priv.git" bundle create --progress "$BACKUP_DIR/Newborough_Hydrology_working_${STAMP}.bundle" --all
  git bundle verify -q "$BACKUP_DIR/Newborough_Hydrology_working_${STAMP}.bundle" >/dev/null || die "backup bundle failed to verify"
  ok "backup: $BACKUP_DIR/Newborough_Hydrology_working_${STAMP}.bundle ($(du -h "$BACKUP_DIR/Newborough_Hydrology_working_${STAMP}.bundle" | cut -f1))"
  plan_private "$WORK/priv.git"
fi

echo ""
echo -e "  ${B}Next: rewrite the copies above, then force-push them to GitHub.${N}"
echo    "  Until the last push finishes, other machines and chats must not pull or ship."
read -rp "$(echo -e "${Y}Type SLIM to rewrite and push, anything else to stop: ${N}")" go
[[ "$go" == SLIM ]] || { echo "  Stopped. Nothing on GitHub or in this tree has changed; backups are in ${BACKUP_DIR}."; exit 0; }

if (( DO_PUB )); then
  say "public: rewriting"
  P="$WORK/pub.git"
  declare -A TREE_BEFORE
  while IFS=' ' read -r ref tree; do TREE_BEFORE["$ref"]="$tree"; done \
    < <(git -C "$P" for-each-ref --format='%(refname) %(objectname)' refs/heads refs/tags \
        | while read -r r o; do echo "$r $(git -C "$P" rev-parse "$o^{tree}")"; done)
  ( cd "$P" && git filter-repo --force --strip-blobs-with-ids "$WORK/pub_strip.txt" \
                --prune-empty never --prune-degenerate never ) || die "git filter-repo failed"
  for ref in "${!TREE_BEFORE[@]}"; do
    [[ "$(git -C "$P" rev-parse "$ref^{tree}")" == "${TREE_BEFORE[$ref]}" ]] \
      || die "$ref's files changed in the rewrite - stopping before any push (bug; report it)"
  done
  ok "every branch tip and tag has exactly the same files as before"
  if git -C "$P" rev-parse -q --verify refs/heads/gh-pages >/dev/null; then
    gp="$(git -C "$P" commit-tree 'refs/heads/gh-pages^{tree}' -m "web tools and documents $(date +%F) - one commit, no history (D-257)")"
    git -C "$P" update-ref refs/heads/gh-pages "$gp"
    ok "gh-pages is now a single commit"
  fi
  git -C "$P" reflog expire --expire=now --all; git -C "$P" gc -q --prune=now
  ok "public repository now $(git -C "$P" count-objects -vH | sed -n 's/^size-pack: //p')"
  mkdir -p notes/history_maps
  { echo "# old -> new commit ids, Newborough_Hydrology history slim ${STAMP} (D-257, tools/slim_history.sh)"
    tail -n +2 "$P/filter-repo/commit-map"; } > "notes/history_maps/public_commit_map_${STAMP%%_*}.txt"
  ok "commit map: notes/history_maps/public_commit_map_${STAMP%%_*}.txt (commit it with the next ship)"
fi
if (( DO_PRIV )); then
  say "private: rewriting"
  Q="$WORK/priv.git"; args=()
  while IFS= read -r p; do args+=( --path-glob "$(to_filter_glob "$p")" ); done < <(cache_patterns)
  ( cd "$Q" && git filter-repo --force --invert-paths "${args[@]}" \
                --prune-empty never --prune-degenerate never ) || die "git filter-repo failed"
  git -C "$Q" reflog expire --expire=now --all; git -C "$Q" gc -q --prune=now
  ok "private repository now $(git -C "$Q" count-objects -vH | sed -n 's/^size-pack: //p')"
  mkdir -p working/history_maps
  { echo "# old -> new commit ids, Newborough_Hydrology_working history slim ${STAMP} (D-257, tools/slim_history.sh)"
    tail -n +2 "$Q/filter-repo/commit-map"; } > "working/history_maps/private_commit_map_${STAMP%%_*}.txt"
  ok "commit map: working/history_maps/private_commit_map_${STAMP%%_*}.txt"
fi

say "pushing to GitHub"
read -rp "$(echo -e "${Y}Force-push the rewritten history now? [y/N]: ${N}")" r
[[ "$r" =~ ^[Yy]$ ]] || { echo "  Held back. Push later from the copies in ${WORK}, then run --resync here."; MODE=apply; exit 0; }
if (( DO_PUB )); then
  push_staged "$P" "$PUB_URL" main
  while IFS= read -r b; do
    [[ "$b" == main ]] && continue
    git -C "$P" push -q --force "$PUB_URL" "refs/heads/$b:refs/heads/$b" && echo "      ${b}: pushed"
  done < <(git -C "$P" for-each-ref --format='%(refname:short)' refs/heads)
  git -C "$P" push -q --force "$PUB_URL" '+refs/tags/*:refs/tags/*' && echo "      tags: pushed"
  ok "public history on GitHub replaced"
fi
if (( DO_PRIV )); then
  push_staged "$Q" "$PRIV_URL" main
  while IFS= read -r b; do
    [[ "$b" == main ]] && continue
    git -C "$Q" push -q --force "$PRIV_URL" "refs/heads/$b:refs/heads/$b" && echo "      ${b}: pushed"
  done < <(git -C "$Q" for-each-ref --format='%(refname:short)' refs/heads)
  ok "private history on GitHub replaced"
fi

(( DO_PUB )) && resync_public
(( DO_PRIV )) && resync_private

echo ""
echo -e "${G}${B}Done.${N}"
echo "  Backups:     ${BACKUP_DIR}  - copy them to the USB drive; restore with: git clone <bundle>"
echo "  Commit maps: ride the next ship (nrg_git.sh 2 or 17)"
echo "  The A475 and any other existing clone: run  bash tools/slim_history.sh --resync  before"
echo "  its next pull or ship (nrg_git.sh refuses to merge the old history back). Cloud sessions"
echo "  clone fresh and need nothing."
rm -rf "$WORK"; MODE=finished
