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

# stdout and stderr both. 1.1.0 (2026-11-08): keep the HEAD *and* the TAIL. `head -c 200000`
# threw away the end of anything longer -- and a --ship log is longer, with its VERDICT on the
# last line. Worse, head closing the pipe sent SIGPIPE upstream, so RC read 141 instead of the
# command's own exit. Measured on the 2026-11-08 ship: the reds were visible, the verdict was not.
set +e
TMP="$(mktemp)"
eval "$CMD" 2>&1 | tr -d '\r' | tee "$TMP"
RC=${PIPESTATUS[0]}
set -e
BYTES=$(wc -c < "$TMP")
if [ "$BYTES" -gt 200000 ]; then
  head -c 120000 "$TMP" >> "$OUT"
  printf '\n\n[... %s bytes elided by l14_say 1.1.0: head 120 kB, then the tail 80 kB ...]\n\n' \
     "$(( BYTES - 200000 ))" >> "$OUT"
  tail -c 80000 "$TMP" >> "$OUT"
else
  cat "$TMP" >> "$OUT"
fi
rm -f "$TMP"
{ printf '```\n\n- exit: %s\n' "$RC"; } >> "$OUT"

G=(git --git-dir=.git-working --work-tree=.)
"${G[@]}" add "$DIR" >/dev/null 2>&1
if "${G[@]}" diff --cached --quiet; then
  echo; echo "  (nothing to commit)"; exit $RC
fi
# 1.1.0: git REFUSES a commit while a merge is unresolved, and `-q >/dev/null 2>&1` swallowed
# the refusal whole -- a transcript was written, never committed, and never reached the chat.
if [ -f .git-working/MERGE_HEAD ]; then
  echo; echo "  written to $OUT but NOT committed: a merge is in progress in the private repo."
  echo "  Resolve it (./working/wgit status), then: ./working/wgit add $DIR && ./working/wgit commit -m 'l14_say ${STAMP}' && ./working/wgit push origin main"
  exit $RC
fi
if ! "${G[@]}" commit -q -m "l14_say ${STAMP}: ${CMD:0:60}"; then
  echo; echo "  written to $OUT but the COMMIT FAILED (output above). Nothing was pushed."
  exit $RC
fi
echo; echo "  written to $OUT and committed privately"
if [ "$PUSH" = "1" ]; then
  if "${G[@]}" push -q origin main >/dev/null 2>&1; then
    echo "  pushed — tell the chat to pull"
  else
    echo "  PUSH FAILED (behind, or no credentials). Run:  ./working/wgit push origin main"
  fi
fi
exit $RC
