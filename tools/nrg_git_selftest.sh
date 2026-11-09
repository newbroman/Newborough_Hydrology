#!/usr/bin/env bash
# nrg_git_selftest.sh — the pull path's safety property, tested rather than grepped.
#
# WHY THIS EXISTS
#
#   J-4's brief asks for "a check that nrg_git.sh's pull path still calls the guard for BOTH
#   repositories — the guard is the whole safety property and nothing asserts it today". Until
#   1.34.0 the pull path (`integrate`, option 4) guarded and pulled the PUBLIC repository only and
#   never touched `.git-working`, so "Pull latest" left the records half of the project behind.
#
#   A grep for the call would assert the text and not the behaviour, which is the defect class the
#   J-10 review names (working/updates/NRG_structure_gates_review_2026-11-08.md §3C: a check that
#   tests a token the subject can produce without doing the work). So this extracts
#   `history_guard` and `pull_working` from working/nrg_git.sh and RUNS them against throwaway
#   repository pairs, in the four states a private pull can be in. The witness is behaviour.
#
#   Two assertions are necessarily textual — that `integrate` calls `pull_working`, and that
#   `update_machine` calls `pull_documents` and `update_residue` — because wiring is text. They are
#   labelled as such below, and they are cheap: a function that exists but is never called is the
#   other half of the same fault.
#
# SKIPS, exit 0, when working/nrg_git.sh is not in this checkout: it is in the PRIVATE repository,
# and a public-only clone cannot see it. A check that errors where its input is absent by design
# gates nothing (the T-27 / T-127 lesson, and the review's design C2).
#
# Usage:  bash tools/nrg_git_selftest.sh          # verdict line, exit non-zero on a failure
#         bash tools/nrg_git_selftest.sh -v       # show each case's output
#
# Version 1.0.0 — Hollingham (2026) — 2026-11-09. First issue (J-4).
set -uo pipefail
cd "$(dirname "$0")/.."

# NRG_GIT_SRC exists so that this script's own detection can be negative-tested against a
# deliberately broken copy. A check that has never been seen to fail is not evidence.
SRC="${NRG_GIT_SRC:-working/nrg_git.sh}"
VERBOSE=0; [ "${1:-}" = "-v" ] && VERBOSE=1

if [ ! -f "$SRC" ]; then
  echo "  nrg_git_selftest: SKIP — $SRC is not in this checkout (private repository, by design)"
  exit 0
fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/nrg_git_selftest.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
pass=0; fail=0
note(){ [ "$VERBOSE" = 1 ] && printf '%s\n' "$1"; }
check(){ # name, condition-as-rc, detail
  if [ "$2" = 0 ]; then pass=$((pass+1)); note "    ok   $1"
  else fail=$((fail+1)); echo "  FAIL $1"; [ -n "${3:-}" ] && printf '%s\n' "$3" | sed 's/^/        /'; fi
}

# ── the functions under test, extracted ───────────────────────────────────────────────
sed -n '/^history_guard(){/,/^}/p' "$SRC" > "$WORK/fn.sh"
sed -n '/^pull_working(){/,/^}/p'  "$SRC" >> "$WORK/fn.sh"
for f in history_guard pull_working; do
  grep -q "^${f}(){" "$WORK/fn.sh" || { echo "  FAIL ${f}() not found in $SRC — the pull path has been restructured"; exit 1; }
done

cat > "$WORK/harness.sh" <<'HARNESS'
set -uo pipefail
C=''; G=''; R=''; Y=''; B=''; N=''
say(){ echo "   -- $1 --"; }
ok(){   echo "   OK $1"; }
fail(){ echo "   x $1"; }
SLIM_GUARD_AHEAD=100
GA="-c user.email=t@t -c user.name=t"
. "$FN"
WGIT_DIR=".git-working"
wgit(){ git --git-dir="$WGIT_DIR" --work-tree="." "$@"; }
have_working_repo(){ [ -d "$WGIT_DIR" ]; }

build(){
  rm -rf "$1"; mkdir -p "$1"
  git init -q --bare "$1/up.git"
  git --git-dir="$1/up.git" symbolic-ref HEAD refs/heads/main
  git init -q "$1/src"
  ( cd "$1/src"; echo one > rec.md; git add rec.md
    git $GA commit -q -m "rec one"; git push -q "$1/up.git" HEAD:main )
  git clone -q "$1/up.git" "$1/tree" 2>/dev/null
  mv "$1/tree/.git" "$1/tree/.git-working"
  ( cd "$1/tree"; git --git-dir=.git-working --work-tree=. config core.bare false )
}
upstream_commit(){ ( cd "$1/src"; git fetch -q "$1/up.git" main; git reset -q --hard FETCH_HEAD
    echo "$2" >> "$3"; git add "$3"; git $GA commit -q -m "$2"; git push -q "$1/up.git" HEAD:main ); }
local_commit(){ ( cd "$1/tree"; echo "$2" >> "$3"; wgit add "$3"; wgit $GA commit -q -m "$2" ); }
HARNESS

one(){ # $1 case dir, $2 setup function body file — prints output, then "rc=N"
  ( FN="$WORK/fn.sh"; . "$WORK/harness.sh"; . "$1"; ) 2>&1
}

# ── A: level with GitHub ───────────────────────────────────────────────────────────────
cat > "$WORK/a.sh" <<'EOF'
build "$CASE"; cd "$CASE/tree"; pull_working; echo "rc=$?"
EOF
out="$(CASE="$WORK/A" one "$WORK/a.sh")"; note "$out"
check "A level with GitHub: reports level, rc 0" \
  "$([[ "$out" == *"level with GitHub"* && "$out" == *"rc=0"* ]] && echo 0 || echo 1)" "$out"

# ── B: behind only → fast-forward ──────────────────────────────────────────────────────
cat > "$WORK/b.sh" <<'EOF'
build "$CASE"; upstream_commit "$CASE" two rec.md
cd "$CASE/tree"; pull_working; echo "rc=$?"
EOF
out="$(CASE="$WORK/B" one "$WORK/b.sh")"; note "$out"
check "B behind only: fast-forwards and says so, rc 0" \
  "$([[ "$out" == *"fast-forward"* && "$out" == *"rc=0"* ]] && echo 0 || echo 1)" "$out"

# ── C: diverged, different files → merge ───────────────────────────────────────────────
cat > "$WORK/c.sh" <<'EOF'
build "$CASE"; upstream_commit "$CASE" two rec.md; local_commit "$CASE" mine other.md
cd "$CASE/tree"; pull_working; echo "rc=$?"
EOF
out="$(CASE="$WORK/C" one "$WORK/c.sh")"; note "$out"
check "C diverged, no conflict: MERGES and keeps both sides, rc 0" \
  "$([[ "$out" == *"merged"* && "$out" == *"rc=0"* ]] && echo 0 || echo 1)" "$out"

# ── D: diverged, same file → refuse, keep both, leave the merge for the operator ───────
cat > "$WORK/d.sh" <<'EOF'
build "$CASE"; upstream_commit "$CASE" theirs rec.md; local_commit "$CASE" mine rec.md
cd "$CASE/tree"; pull_working; echo "rc=$?"
ls .git-working/MERGE_HEAD >/dev/null 2>&1 && echo "MERGE_IN_PROGRESS"
EOF
out="$(CASE="$WORK/D" one "$WORK/d.sh")"; note "$out"
check "D conflict: refuses with KEEP BOTH SIDES, rc 1" \
  "$([[ "$out" == *"KEEP BOTH SIDES"* && "$out" == *"rc=1"* ]] && echo 0 || echo 1)" "$out"
check "D conflict: the merge is left in progress, so abort and resolve are both open" \
  "$([[ "$out" == *"MERGE_IN_PROGRESS"* ]] && echo 0 || echo 1)" "$out"
check "D conflict: never offers 'keep GitHub's / keep mine' for records" \
  "$([[ "$out" != *"Keep GitHub's version"* ]] && echo 0 || echo 1)" "$out"

# ── wiring, necessarily textual ────────────────────────────────────────────────────────
ibody="$(sed -n '/^integrate(){/,/^}/p' "$SRC")"
ubody="$(sed -n '/^update_machine(){/,/^}/p' "$SRC")"
check "wiring (text): integrate() pulls the private repo too" \
  "$([[ "$ibody" == *pull_working* ]] && echo 0 || echo 1)"
check "wiring (text): integrate() guards the PUBLIC repo" \
  "$([[ "$ibody" == *"history_guard public"* ]] && echo 0 || echo 1)"
check "wiring (text): pull_working() guards the PRIVATE repo" \
  "$(grep -A40 '^pull_working(){' "$SRC" | grep -q 'history_guard private' && echo 0 || echo 1)"
check "wiring (text): integrate() does NOT pull documents (do_push calls it)" \
  "$([[ "$ibody" != *pull_documents* ]] && echo 0 || echo 1)"
check "wiring (text): update_machine() runs the documents step and the residue report" \
  "$([[ "$ubody" == *pull_documents* && "$ubody" == *update_residue* ]] && echo 0 || echo 1)"
check "wiring (text): option 4 runs update_machine, not integrate" \
  "$(grep -q '"\$OPT_PULL") update_machine' "$SRC" && echo 0 || echo 1)"

total=$((pass+fail))
if [ "$fail" = 0 ]; then echo "  nrg_git_selftest: OK — ${pass} of ${total} (4 behavioural, the rest wiring)"; exit 0; fi
echo "  nrg_git_selftest: FAIL — ${fail} of ${total}"
exit 1
