#!/usr/bin/env bash
# l14_run.sh — run the full pipeline on the L14 and publish the result.
#
# WHY THIS EXISTS (2026-11-08). A cloud container will not carry a full run: on
# 2026-11-08 four attempts were killed part-way (steps 4, 4, 31 and, alongside the
# last, a standalone Script 50), each with no exit code, no traceback, 15 GB of
# memory free and no OOM. Two unrelated processes dying 90 seconds apart is a
# container reclaim, not a fault in either. Until that changes, a full
# --with-supplementary run happens on a machine that has built the environment
# (D-227), which in practice means the L14.
#
#   bash tools/l14_run.sh              # preflight, run, gates, then ASK before shipping
#   bash tools/l14_run.sh --dry-run    # preflight and report only, run nothing
#   bash tools/l14_run.sh --resume N   # continue a killed run from step N
#
# It does NOT push on its own. CLAUDE.md §7: pushing is Martin's call each time,
# so the ship is offered and waits for a yes.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
REPO="$PWD"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="scratch/l14_run_${STAMP}.log"
mkdir -p scratch

DRY=0; RESUME=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    --resume)  RESUME="${2:-}"; shift 2 ;;
    *) echo "unknown argument: $1"; exit 2 ;;
  esac
done

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '   \033[32mok\033[0m    %s\n' "$*"; }
bad()  { printf '   \033[31mSTOP\033[0m  %s\n' "$*"; }
note() { printf '   .     %s\n' "$*"; }

FAIL=0
say "1/6  Preflight"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BRANCH" = "main" ]; then ok "on main"
else bad "on branch '$BRANCH' — this project ships from main (§4g)"; FAIL=1; fi

if [ -z "$(git status --porcelain)" ]; then ok "public tree clean"
else bad "public tree has uncommitted changes — commit or stash first:"; git status --short | sed 's/^/           /'; FAIL=1; fi

# The environment is the thing that makes outputs comparable (D-227). env_audit
# compares libraries and the BLAS pin; the hostname is reported, not compared.
if python3 tools/env_audit.py >/dev/null 2>&1; then ok "environment matches tools/environment.json"
else bad "env_audit FAILED — build it first:  bash tools/nrg_env.sh"; FAIL=1; fi

say "2/6  Fetch and fast-forward both repositories"
for R in "public:git" "private:git --git-dir=.git-working --work-tree=."; do
  NAME="${R%%:*}"; GIT="${R#*:}"
  if ! $GIT fetch -q origin 2>/dev/null; then bad "$NAME: fetch failed"; FAIL=1; continue; fi
  BEHIND="$($GIT rev-list --count HEAD..origin/main 2>/dev/null || echo '?')"
  AHEAD="$($GIT rev-list --count origin/main..HEAD 2>/dev/null || echo '?')"
  if [ "$BEHIND" = "0" ]; then ok "$NAME: up to date (${AHEAD} ahead)"
  elif [ "$DRY" = "1" ]; then note "$NAME: ${BEHIND} behind — would fast-forward"
  elif $GIT merge --ff-only origin/main >/dev/null 2>&1; then ok "$NAME: fast-forwarded ${BEHIND} commit(s)"
  else bad "$NAME: ${BEHIND} behind and will not fast-forward — merge by hand first"; FAIL=1; fi
done

# The claim is checked AFTER the fetch, deliberately. The lock record lives in the
# private repository, so before the fetch this reads whatever this clone last saw --
# which on 2026-11-08 was a release that had been taken locally but not published,
# and would have reported "free" for a claim GitHub still showed as held.
CLAIM="$(python3 tools/doc_lock.py status 2>/dev/null | awk '/^ *pipeline /{print; exit}')"
if [ -n "$CLAIM" ]; then
  bad "the 'pipeline' claim is held (as published, after the fetch):"
  printf '           %s\n' "$CLAIM"
  note "release it in that chat and let the release PUBLISH, or export NRG_CHAT to"
  note "that chat's name if it is you. A release that says LOCAL ONLY has not landed."
  FAIL=1
else ok "pipeline claim free on GitHub"; fi

if [ "$FAIL" != "0" ]; then printf '\n\033[31mPreflight failed — nothing was run.\033[0m\n'; exit 1; fi
if [ "$DRY" = "1" ]; then printf '\n\033[32mDry run: preflight passed. Re-run without --dry-run.\033[0m\n'; exit 0; fi

say "3/6  Full pipeline  (this is the long one — expect hours)"
note "logging to $LOG"
if [ -n "$RESUME" ]; then
  note "resuming from step $RESUME"
  ARGS=(--from "$RESUME" --with-supplementary)
else
  # --with-supplementary is NOT optional before a commit (D-102): --full alone
  # skips the opt-in diagnostics, and an opt-in step can then sit on main with
  # edited code and outputs from the previous version while every gate reads green.
  ARGS=(--full --with-supplementary)
fi
START=$(date +%s)
python3 run_analysis.py "${ARGS[@]}" 2>&1 | tee "$LOG"
RC=${PIPESTATUS[0]}
ELAPSED=$(( $(date +%s) - START ))
printf '\n   pipeline exited %s after %dm %ds\n' "$RC" $((ELAPSED/60)) $((ELAPSED%60))
if [ "$RC" != "0" ]; then
  LAST="$(tr '\r' '\n' < "$LOG" | grep -oE 'STEP [0-9]+/[0-9]+' | tail -1)"
  bad "pipeline did not finish (last: ${LAST:-unknown})"
  note "resume with:  bash tools/l14_run.sh --resume <N>"
  exit 1
fi
ok "pipeline complete"

say "4/6  Gates"
bash tools/check_all.sh 2>&1 | tee -a "$LOG" | tail -3
VERDICT="$(python3 - <<'PY' 2>/dev/null
import json
try:
    d = json.load(open("scratch/check_all_summary.json"))
    red = [s["key"] for s in d["sections"] if s["verdict"] != "OK"]
    print(f'{d["verdict"]} — {len(d["sections"])} sections, {len(red)} red' + (": " + ", ".join(red) if red else ""))
except Exception as e:
    print(f"could not read the summary ({e})")
PY
)"
printf '   check_all: %s\n' "$VERDICT"

say "5/6  What changed"
git status --short | head -30
printf '   %s file(s) changed in the public tree\n' "$(git status --porcelain | wc -l)"

say "6/6  Ship?"
cat <<EOF
   A ship commits BOTH repositories, runs the gates again and pushes (§4f), and
   archives the ODTs to Drive. Nothing has been pushed yet.

       ./working/nrg_git.sh --ship

   Quote this in the message:   check_all: ${VERDICT}

   Once it has pushed, tell the cloud chat and it will pull. If you would rather
   look first, stop here — the log is ${LOG}.
EOF
read -r -p "   Run the ship now? [y/N] " REPLY
case "$REPLY" in
  [yY]*) say "Shipping"; ./working/nrg_git.sh --ship ;;
  *)     note "not shipped — run ./working/nrg_git.sh --ship when ready" ;;
esac
