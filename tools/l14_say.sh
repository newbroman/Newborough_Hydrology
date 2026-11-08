#!/usr/bin/env bash
# l14_say.sh — run a command on the L14 and put its output where the cloud chat can read it.
#
# WHY. A cloud session has no access to this machine's filesystem, so `| tee somewhere.log`
# leaves the output where nobody but Martin can see it, and he ends up pasting terminal
# scrollback by hand. CLAUDE.md §4 says "RUN IT HERE, tee IT, READ IT" -- this is the
# missing half: the tee goes to a TRACKED path in the private repository and is pushed, so
# the chat reads it from git.
#
#   bash tools/l14_say.sh 'git status --short'
#   bash tools/l14_say.sh --no-push 'some long diagnostic'     # write and commit only
#
# It pushes ONLY working/updates/l14_say/, never anything else: the commit stages that one
# directory by name. Running it is the authorisation (§7) -- you typed the command.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
PUSH=1
[ "${1:-}" = "--no-push" ] && { PUSH=0; shift; }
[ $# -eq 0 ] && { echo "usage: bash tools/l14_say.sh [--no-push] '<command>'"; exit 2; }

CMD="$*"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DIR="working/updates/l14_say"
OUT="$DIR/${STAMP}.md"
mkdir -p "$DIR"

{
  printf '# l14_say %s\n\n' "$STAMP"
  printf -- '- host: `%s`\n- cwd: `%s`\n- command:\n\n```\n%s\n```\n\n## Output\n\n```\n' \
     "$(hostname)" "$PWD" "$CMD"
} > "$OUT"

# stdout and stderr both, trimmed: a diagnostic that floods the repo helps nobody
set +e
eval "$CMD" 2>&1 | tr -d '\r' | head -c 200000 | tee -a "$OUT"
RC=${PIPESTATUS[0]}
set -e
{ printf '```\n\n- exit: %s\n' "$RC"; } >> "$OUT"

G=(git --git-dir=.git-working --work-tree=.)
"${G[@]}" add "$DIR" >/dev/null 2>&1
if "${G[@]}" diff --cached --quiet; then
  echo; echo "  (nothing to commit)"; exit $RC
fi
"${G[@]}" commit -q -m "l14_say ${STAMP}: ${CMD:0:60}" >/dev/null 2>&1
echo; echo "  written to $OUT and committed privately"
if [ "$PUSH" = "1" ]; then
  if "${G[@]}" push -q origin main >/dev/null 2>&1; then
    echo "  pushed — tell the chat to pull"
  else
    echo "  PUSH FAILED (behind, or no credentials). Run:  ./working/wgit push origin main"
  fi
fi
exit $RC
