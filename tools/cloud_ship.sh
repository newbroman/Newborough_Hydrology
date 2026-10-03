#!/usr/bin/env bash
# cloud_ship.sh — ship from a claude.ai/code cloud session, with the L14 switched off.
#
# Spec working/updates/NRG_spec_cloud_ship_2026-10-02.md, signed off by Martin 2026-10-02 17:50:
# the same ship as the L14's (ODT writes, archive, prune), pushed to main; refuses rather than
# runs the pipeline when outputs are stale; its log is committed to working/ship_logs/.
#
# It is a WRAPPER. The ship itself stays in working/nrg_git.sh --ship. What this adds is the set
# of checks that make a Drive copy of the documents safe to ship from, each of which stops the run
# BEFORE anything is written:
#   1. Drive reachable                         (else  SHIP: FAIL drive-token)
#   2. Drive is the last archive               (working/DRIVE_MANIFEST.json against the remote AND the
#                                                downloaded files, by MD5; else  FAIL drive-not-current)
#   3. clean tree, and the document lock free  (else  FAIL dirty-tree / docs-locked-by-<holder>)
#   4. no committed mirror is ahead of Drive   (refresh_mirrors --verify, on content not mtime;
#                                                else  FAIL mirrors-ahead-of-drive — CLAUDE.md 4b)
#   5. no outputs owed a rerun                 (output_lag --gate; else  FAIL outputs-stale — never
#                                                runs the pipeline unasked)
# then takes the lock as "cloud" (pushed privately), runs the ship, releases the lock with a note
# telling the L14 to pull, and commits the log.
#
# Run from the tree tools/cloud_setup.sh built (it decodes the Drive secret and copies the ODTs down).
# Usage:
#   bash tools/cloud_ship.sh --id <id> --approved "<Martin's words>" [--dry-run] [message]
# --dry-run stops after the checks, releases the lock, and tests the private push (CLAUDE.md 7: a
# dry run pushes nothing but the lock).
#
# Version 1.0.1 — Hollingham (2026) — 2026-10-03. Private pushes name origin HEAD:main rather than relying on
#   an upstream (the dry3 dry run: a --bare clone sets none, so the lock push was refused).
# 1.0.0 — 2026-10-02. First issue.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

ID="" APPROVED="" DRY=0 MSG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --id) ID="$2"; shift 2 ;;
    --approved) APPROVED="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) MSG="$1"; shift ;;
  esac
done
[ -n "$ID" ] && [ -n "$APPROVED" ] || { echo "SHIP: FAIL no-approval (need --id and --approved \"<Martin's words>\")"; exit 2; }
case "$ID" in *[!A-Za-z0-9_.-]*) echo "SHIP: FAIL bad-id"; exit 2 ;; esac

mkdir -p scratch
LOG="scratch/cloud_ship_${ID}.log"
exec > >(tee -a "$LOG") 2>&1
export PATH="$HOME/bin:$PATH"
VPY="venv/bin/python"; [ -x "$VPY" ] || VPY="python3"
WG=(git --git-dir=.git-working --work-tree=.)
export NRG_DOC_LOCK_HOLDER="cloud"
FILTER="tools/rclone-odt-filter.txt"
REMOTE="$(sed -n 's/^DRIVE_REMOTE="\([^"]*\)".*/\1/p' working/nrg_git.sh | head -1)"
LOCKED=0

step() { printf '\n  [%s] %s\n' "$1" "$2"; }

lock_push() {   # commit and push the lock file privately
  "${WG[@]}" add working/DOCUMENT_LOCK.json \
    && "${WG[@]}" commit -q -m "$1" -- working/DOCUMENT_LOCK.json \
    && "${WG[@]}" push -q origin HEAD:main
}

fail() {
  echo "  $2"
  if [ "$LOCKED" = 1 ]; then
    "$VPY" tools/doc_lock.py release --force --note "cloud ship ${ID} failed before shipping: $1" >/dev/null
    lock_push "doc lock released: cloud ship ${ID} failed ($1)" || echo "  (lock release not pushed)"
  fi
  echo "SHIP: FAIL $1  (log ${LOG})"
  exit 1
}

echo "===== NRG cloud ship ${ID}  $(date -u +%FT%TZ)  approved: \"${APPROVED}\" ====="
[ -n "$REMOTE" ] || fail no-remote "DRIVE_REMOTE not found in working/nrg_git.sh"

step 1/7 "Drive reachable ($REMOTE)"
command -v rclone >/dev/null || fail drive-token "rclone is not installed (tools/cloud_setup.sh installs it)"
rclone lsf "$REMOTE" --max-depth 1 >/dev/null 2>&1 \
  || fail drive-token "Drive refused the token, or the secret is missing: on the laptop run bash tools/drive_token.sh and paste the line into the claude.ai/code environment"

step 2/7 "Drive is the last archive (working/DRIVE_MANIFEST.json)"
[ -f working/DRIVE_MANIFEST.json ] || fail drive-not-current "no working/DRIVE_MANIFEST.json yet: one L14 ship (nrg_git.sh 1.26.0+) writes it"
rclone md5sum "$REMOTE" --filter-from "$FILTER" > scratch/drive_remote.md5 2>/dev/null \
  || fail drive-not-current "rclone md5sum on the remote failed"
rclone lsf -R . --filter-from "$FILTER" --files-only --hash MD5 --format hp --separator '|' > scratch/drive_local.md5 2>/dev/null
"$VPY" - <<'PY' || fail drive-not-current "Drive or the downloaded copy differs from the last archive (list above)"
import json
man = json.load(open("working/DRIVE_MANIFEST.json"))["files"]
remote = {}
for line in open("scratch/drive_remote.md5"):
    h, _, p = line.rstrip("\n").partition("  ")
    if p:
        remote[p] = h
local = dict(reversed(l.rstrip("\n").split("|", 1)) for l in open("scratch/drive_local.md5") if "|" in l)
bad = [(p, "remote " + ("missing" if p not in remote else "differs")) for p, h in man.items() if remote.get(p) != h]
bad += [(p, "download " + ("missing" if p not in local else "differs")) for p, h in man.items() if local.get(p) != h]
for p, why in bad[:20]:
    print(f"    {why:18s} {p}")
print(f"  {len(man)} documents in the manifest; {len(bad)} mismatch(es)")
raise SystemExit(1 if bad else 0)
PY

step 3/7 "clean tree, and the document lock"
[ -z "$(git status --porcelain --untracked-files=no)" ] || fail dirty-tree "the public tree has uncommitted changes: a cloud ship starts from a clean clone"
if ! "$VPY" tools/doc_lock.py check --quiet; then
  holder="$("$VPY" -c 'import json;print(json.load(open("working/DOCUMENT_LOCK.json")).get("holder"))' 2>/dev/null)"
  fail "docs-locked-by-${holder:-unknown}" "the documents are locked by ${holder}: release them there (after archiving) first"
fi
"$VPY" tools/doc_lock.py take --note "cloud ship ${ID}" >/dev/null && LOCKED=1
lock_push "doc lock: cloud ship ${ID}" || fail lock-push "could not push the lock to the private repo"

step 4/7 "no committed mirror is ahead of Drive (refresh_mirrors --verify, by content)"
"$VPY" tools/refresh_mirrors.py --verify \
  || fail mirrors-ahead-of-drive "a committed mirror differs from what Drive's ODT produces: some machine pushed a mirror without archiving its ODT. Archive from that machine (option 11), then ship again"

step 5/7 "no outputs owed a rerun (output_lag --gate)"
"$VPY" tools/output_lag.py --gate \
  || fail outputs-stale "outputs are behind their code (above). Run those steps deliberately, then ship; a cloud ship never runs the pipeline unasked"

if [ "$DRY" = 1 ]; then
  step 6/7 "DRY RUN: the private push works (Q6)"
  "${WG[@]}" push --dry-run origin HEAD >/dev/null 2>&1 && echo "  private push: OK" || echo "  private push: REFUSED"
  git push --dry-run origin HEAD >/dev/null 2>&1 && echo "  public push: OK" || echo "  public push: REFUSED"
  "$VPY" tools/doc_lock.py release --force --note "cloud ship ${ID}: dry run" >/dev/null
  lock_push "doc lock released: cloud ship ${ID} dry run" || echo "  (lock release not pushed)"
  echo "SHIP: DRYRUN OK  (every check passed; nothing shipped; log ${LOG})"
  exit 0
fi

step 6/7 "ship (working/nrg_git.sh --ship)"
./working/nrg_git.sh --ship "${MSG:-cloud ship ${ID}}"
rc=$?
line="$(grep -a '^SHIP: ' "$(ls -t scratch/ship_*.log 2>/dev/null | head -1)" 2>/dev/null | tail -1)"

step 7/7 "release the lock and keep the log"
"$VPY" tools/doc_lock.py release --force \
  --note "cloud ship ${ID} wrote ODTs to Drive: on the L14 run bash tools/drive_pull.sh before editing" >/dev/null
mkdir -p working/ship_logs
cp "$LOG" "working/ship_logs/${ID}.log"
"${WG[@]}" add working/DOCUMENT_LOCK.json "working/ship_logs/${ID}.log" \
  && "${WG[@]}" commit -q -m "cloud ship ${ID}: lock released, log" \
  && "${WG[@]}" push -q origin HEAD:main || echo "  note: lock release / log not pushed"
echo "${line:-SHIP: FAIL no-verdict (nrg_git.sh exit ${rc}; log ${LOG})}"
exit "$rc"
