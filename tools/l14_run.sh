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
  else
    # Distinguish the two reasons a fast-forward fails, because they need different fixes
    # and the wrong message sends you hunting for a divergence that is not there (L14,
    # 2026-11-08: reported "will not fast-forward" when the only problem was one dirty
    # generated file, and `log origin/main..HEAD` was empty).
    DIRTY="$($GIT status --porcelain 2>/dev/null | head -5)"
    LOCAL="$($GIT rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
    if [ "$LOCAL" != "0" ]; then
      bad "$NAME: ${BEHIND} behind AND ${LOCAL} local commit(s) — histories diverged, merge by hand:"
      note "  $GIT merge --no-edit origin/main"
    elif [ -n "$DIRTY" ]; then
      bad "$NAME: ${BEHIND} behind, blocked by uncommitted file(s) — it IS a fast-forward:"
      printf '           %s\n' "$DIRTY"
      note "  discard them if generated, or commit them, then re-run"
    else
      bad "$NAME: ${BEHIND} behind and the fast-forward failed for an unknown reason"
    fi
    FAIL=1
  fi
done

# The claim is checked AFTER the fetch, deliberately. The lock record lives in the
# private repository, so before the fetch this reads whatever this clone last saw --
# which on 2026-11-08 was a release that had been taken locally but not published,
# and would have reported "free" for a claim GitHub still showed as held.
# Read the lock as ORIGIN publishes it, not as this clone happens to hold it. doc_lock
# status reads the working tree, which in --dry-run has not been fast-forwarded and after a
# plain fetch may be many commits behind -- on 2026-11-08 that reported a held pipeline
# claim on the L14 that had already been released and published. "Published" is the whole
# meaning of the gate, so ask the published record.
CLAIM="$(git --git-dir=.git-working show origin/main:working/DOCUMENT_LOCK.json 2>/dev/null \
  | python3 -c 'import json,sys
try:
    c = json.load(sys.stdin).get("claims", {})
except Exception:
    sys.exit(0)
v = c.get("pipeline")
if v:
    print(f"   pipeline  chat {v.get(\"chat\")!r}  since {v.get(\"since\",\"?\")}  {v.get(\"note\",\"\")}")' 2>/dev/null)"
if [ -n "$CLAIM" ]; then
  bad "the 'pipeline' claim is held, as published on GitHub:"
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

say "5/6  Run summary, on a path the cloud chat can read"
# CLAUDE.md §4: "RUN IT HERE, tee IT, READ IT" -- do not make Martin paste output back.
# The tee'd log goes to scratch/, which is gitignored, and a cloud session has no access
# to this machine's filesystem, so the log alone cannot reach the chat that asked for the
# run. This writes a short summary to a TRACKED path in the private repository instead,
# which the ship then pushes: the chat reads the outcome from git rather than from a paste.
SUMMARY="working/updates/l14_run_${STAMP}.md"
mkdir -p working/updates
{
  printf '# L14 pipeline run %s\n\n' "$STAMP"
  printf -- '- host: `%s`\n' "$(hostname)"
  printf -- '- command: `run_analysis.py %s`\n' "${ARGS[*]}"
  printf -- '- pipeline exit: **%s** after %dm %ds\n' "$RC" $((ELAPSED/60)) $((ELAPSED%60))
  printf -- '- check_all: **%s**\n' "$VERDICT"
  printf -- '- public files changed: %s\n\n' "$(git status --porcelain | wc -l)"
  printf '## Steps, slowest first\n\n```\n'
  tr '\r' '\n' < "$LOG" | awk '
    /▶ STEP/ { step = $0; sub(/^ *▶ */, "", step) }
    /✓ done/ { t = $0; sub(/^.*\(/, "", t); sub(/\).*$/, "", t);
               if (step != "") { print t "\t" step; step = "" } }' \
    | sort -t'\t' -k1 -gr | head -15
  printf '```\n\n## Inside the slowest steps\n\n'
  # Step times alone say WHICH script is slow, not which part of it. Script 03 prints its
  # own phase breakdown (its _tick/_tick_report), and any `[   12.3s] label` line from a
  # script that gains the same. Without this the breakdown falls outside the log tail and
  # the summary says a script took 33 minutes without saying where they went.
  printf '```\n'
  tr '\r' '\n' < "$LOG" | grep -E '^\s+\[ *[0-9]+\.[0-9]s\]|^ *[0-9]+\.[0-9]s +[0-9.]+%%' | head -40
  tr '\r' '\n' < "$LOG" | grep -A25 'phase timings' | head -30
  printf '```\n\n## Warnings\n\n```\n'
  tr '\r' '\n' < "$LOG" | grep -E "WARNING|⚠" | sed 's/^ *//' | sort -u | head -25
  printf '```\n\n## Last 25 lines\n\n```\n'
  tr '\r' '\n' < "$LOG" | grep -v '^\s*$' | tail -25
  printf '```\n'
} > "$SUMMARY"
ok "wrote $SUMMARY"
note "the ship pushes it; the cloud chat reads it from the private repo"

say "5b/6  What changed"
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
