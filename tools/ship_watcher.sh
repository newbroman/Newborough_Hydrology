#!/usr/bin/env bash
# ship_watcher.sh — run `working/nrg_git.sh --ship` when a ship is requested, so a ship needs no
# terminal on the publishing laptop.
#
# WHY
#   A ship (nrg_git.sh option 17 / --ship) had to be started by Martin at a terminal on the L14.
#   A chat session can already write into ~/projects/NRG through the desktop bridge, but the bridge
#   VM cannot ship (env_audit fails there by design; CLAUDE.md section 4). So the chat writes a
#   REQUEST file, and this watcher - running on the laptop proper under systemd --user, inside the
#   built environment - picks it up and ships. Martin's "push" in the chat is what authorises the
#   request; the watcher cannot check that, and anything that can write to the folder can ask.
#
# THE PROTOCOL (all paths relative to the repository root)
#   working/.ship_request          the request. JSON, or "key: value" / "key=value" lines:
#                                    id            [A-Za-z0-9._-]{1,64}, unique per ship (required)
#                                    requested_at  ISO 8601, e.g. 2026-10-02T14:05:00Z (required)
#                                    requested_by  free text, e.g. the session (recorded only)
#                                    message       optional commit message for --ship
#                                    decisions     optional "D-145 D-146" -> NRG_SHIP_DECISIONS
#   working/.ship_requests_done/   every request ends here as <id>.req (never deleted), with
#                                  <id>.status.json beside it. A duplicate id -> <id>.dup.<ts>.req.
#   working/.ship_watcher.lock     held while a ship runs (pid/host/id; rename-into-place).
#   working/.ship_status.json      the latest request's state: waiting | running | done |
#                                  refused | interrupted, with exit_code, verdict, SHAs and log.
#   scratch/ship_watcher_<ts>_<id>.log and scratch/ship_watcher_last.log   the whole ship output.
#     (Not scratch/ship_<ts>.log: nrg_git.sh --ship writes that name itself, from the same
#     clock, and the two would collide.)
#
# RULES IT KEEPS
#   * one ship at a time: the lock above, plus a refusal while a hand-run nrg_git.sh is busy;
#   * an id runs once: a request whose id is already in .ship_requests_done/ is refused;
#   * a request older than SHIP_WATCHER_MAX_AGE (default 2 h) is refused as stale, and one dated
#     more than 5 min in the future is refused too - a request is a "push" said NOW;
#   * LibreOffice open on the desktop: the ship waits (headless exports clash with an open GUI,
#     tools/build_pdfs.sh header). SHIP_WATCHER_LO_POLICY=refuse|ignore changes that;
#   * the verdict is read from nrg_git's own last "SHIP:" line, NOT only its exit code: up to
#     nrg_git.sh 1.25.1 `--ship` exits 0 on "SHIP: FAIL check_all-or-push" and on "SHIP: PARTIAL"
#     (the group's status is the last echo; fixed in nrg_git.sh 1.25.2).
#
# Usage:  bash tools/ship_watcher.sh            # the service's command: poll for ever
#         bash tools/ship_watcher.sh --once     # one poll, then exit (testing, or by hand)
# Environment: NRG_REPO_DIR (default ~/projects/NRG), SHIP_WATCHER_POLL (20 s),
#   SHIP_WATCHER_MAX_AGE (7200 s), SHIP_WATCHER_TIMEOUT (4h, GNU timeout syntax),
#   SHIP_WATCHER_LO_POLICY (wait), SHIP_WATCHER_SHIP_CMD (working/nrg_git.sh; tests use a fake).
#
# Version 1.0.0 — Hollingham (2026) — 2026-10-02. First issue.
set -euo pipefail

__version__="1.0.0"
REPO="${NRG_REPO_DIR:-$HOME/projects/NRG}"
POLL="${SHIP_WATCHER_POLL:-20}"
MAX_AGE="${SHIP_WATCHER_MAX_AGE:-7200}"
FUTURE_SKEW="${SHIP_WATCHER_FUTURE_SKEW:-300}"
SHIP_TIMEOUT="${SHIP_WATCHER_TIMEOUT:-4h}"
LO_POLICY="${SHIP_WATCHER_LO_POLICY:-wait}"
SHIP_CMD="${SHIP_WATCHER_SHIP_CMD:-working/nrg_git.sh}"
HEARTBEAT_POLLS="${SHIP_WATCHER_HEARTBEAT_POLLS:-90}"   # an "idle" line every ~30 min at 20 s
ONCE=0
case "${1:-}" in
  --once) ONCE=1 ;;
  --version) echo "ship_watcher.sh ${__version__}"; exit 0 ;;
  -h|--help) sed -n '2,46p' "$0"; exit 0 ;;
  "") ;;
  *) echo "unknown argument: $1 (try --help)" >&2; exit 2 ;;
esac

REQ="working/.ship_request"
DONE="working/.ship_requests_done"
LOCK="working/.ship_watcher.lock"
STATUS="working/.ship_status.json"
SCRATCH="scratch"
HOST="$(hostname)"
PY="$(command -v /usr/bin/python3 || command -v python3 || true)"

# The child processes get a non-interactive environment: git must fail rather than wait for a
# username on a terminal that does not exist, and nothing may open a pager.
export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never GIT_PAGER=cat PAGER=cat
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}" LANG="${LANG:-C.UTF-8}"
export NRG_REPO_DIR="$REPO"

log()  { printf '[ship_watcher %s] %s\n' "$(date +%H:%M:%S)" "$*"; }
die()  { log "FATAL: $*"; exit 1; }
iso()  { date -u +%Y-%m-%dT%H:%M:%SZ; }

cd "$REPO" 2>/dev/null || die "cannot cd to $REPO (set NRG_REPO_DIR)"
[[ -n "$PY" ]] || die "no python3 for JSON handling"
[[ -f "$SHIP_CMD" ]] || die "no $SHIP_CMD in $REPO"
[[ -d working ]] || die "no working/ in $REPO - is the private half laid out? (CLAUDE.md 4f)"
mkdir -p "$DONE" "$SCRATCH"

# --- one watcher per repository ------------------------------------------------------------
# A kernel lock outside the tree: two watchers (the service plus a hand-run copy) would otherwise
# race for the same request. Released by the kernel when the process ends, so it cannot go stale.
INST_DIR="${XDG_RUNTIME_DIR:-/tmp}"
INST_LOCK="${INST_DIR}/nrg_ship_watcher.$(printf '%s' "$REPO" | md5sum | cut -c1-12).lock"
exec 9>"$INST_LOCK"
flock -n 9 || die "another ship_watcher is already watching $REPO ($INST_LOCK)"

# --- status file: JSON written by python (proper escaping), placed by rename -----------------
# usage: write_status key=value ...   (exit_code is written as a number when it is one)
write_status() {
  local tmp="${STATUS}.tmp.$$"
  "$PY" - "$tmp" "$@" <<'PY'
import json, sys
out, pairs = sys.argv[1], sys.argv[2:]
d = {}
for p in pairs:
    k, _, v = p.partition("=")
    if k == "exit_code" and v.lstrip("-").isdigit():
        v = int(v)
    d[k] = v if v != "" else None
with open(out, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
PY
  mv -f "$tmp" "$STATUS"
}
status_field() {  # status_field key -> value or empty
  [[ -f "$STATUS" ]] || return 0
  "$PY" -c 'import json,sys
try: print(json.load(open(sys.argv[1])).get(sys.argv[2]) or "")
except Exception: print("")' "$STATUS" "$1"
}

# --- the ship lock --------------------------------------------------------------------------
lock_field() { sed -n "s/^$1=//p" "$LOCK" 2>/dev/null | head -1 || true; }
lock_is_live() {  # 0 when the lock is held by a live watcher on this host
  [[ -f "$LOCK" ]] || return 1
  local pid host
  pid="$(lock_field pid)"; host="$(lock_field host)"
  [[ "$host" == "$HOST" && "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  # PID reuse: the holder must still be a ship watcher, not some later process with its number.
  tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null | grep -q 'ship_watcher' || return 1
  return 0
}
set_lock_aside() {  # a stale lock is moved, never deleted (the tree may be on the bridge mount)
  local dest
  dest="${DONE}/stale_lock.$(date +%Y%m%d_%H%M%S).$$"
  mv "$LOCK" "$dest" 2>/dev/null && log "stale lock (pid $(sed -n 's/^pid=//p' "$dest" | head -1), host $(sed -n 's/^host=//p' "$dest" | head -1)) moved to $dest"
}
acquire_lock() {  # $1 = request id
  if [[ -f "$LOCK" ]]; then
    lock_is_live && return 1
    set_lock_aside || return 1
  fi
  local tmp="${LOCK}.tmp.$$" nonce
  nonce="$$.$RANDOM.$(date +%s%N)"
  printf 'pid=%s\nhost=%s\nstarted=%s\nid=%s\nnonce=%s\n' "$$" "$HOST" "$(iso)" "$1" "$nonce" > "$tmp"
  mv -n "$tmp" "$LOCK" 2>/dev/null || true       # rename into place, never over an existing lock
  [[ -e "$tmp" ]] && mv "$tmp" "${DONE}/lost_lock_race.$$" 2>/dev/null   # we did not win
  [[ "$(lock_field nonce)" == "$nonce" ]]         # read it back: only the winner sees its nonce
}
release_lock() {
  [[ -f "$LOCK" && "$(lock_field pid)" == "$$" ]] || return 0
  rm -f "$LOCK" 2>/dev/null || mv "$LOCK" "${DONE}/released_lock.$(date +%s).$$" 2>/dev/null || true
}

# --- a hand-run nrg_git.sh --------------------------------------------------------------------
# An nrg_git.sh with child processes is DOING something (option 17, a push); one with none is a
# menu sitting at its prompt, which is not a ship. Returns 0 (busy) and prints the pid if busy.
manual_ship_busy() {
  local p a hit
  for p in $(pgrep -x bash 2>/dev/null || true); do
    [[ "$p" == "$$" ]] && continue
    # A SCRIPT ARGUMENT named nrg_git.sh, compared whole: `pgrep -f` also matches an editor, a
    # pager, or any `bash -c '...'` whose text merely mentions the file (measured in testing).
    hit=0
    while IFS= read -r -d '' a; do
      [[ "$a" =~ (^|/)nrg_git\.sh$ ]] && { hit=1; break; }
    done < <(tail -c +1 "/proc/$p/cmdline" 2>/dev/null | { IFS= read -r -d '' _; cat; })
    (( hit )) || continue
    if pgrep -P "$p" >/dev/null 2>&1; then echo "$p"; return 0; fi
  done
  return 1
}

notify() {  # best effort; the status file is the record
  command -v notify-send >/dev/null 2>&1 && notify-send -a "NRG ship" "NRG ship" "$*" >/dev/null 2>&1 9>&- || true
}

# --- the request ------------------------------------------------------------------------------
# Prints six lines: id, requested_at (epoch), requested_by, message, decisions, error.
parse_request() {
  "$PY" - "$1" <<'PY'
import datetime, json, re, sys
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
d = {}
try:
    d = json.loads(raw)
    if not isinstance(d, dict):
        d = {}
except ValueError:
    for line in raw.splitlines():
        m = re.match(r"\s*([A-Za-z_]+)\s*[:=]\s*(.*?)\s*$", line)
        if m:
            d[m.group(1).lower()] = m.group(2).strip('"\'')
def s(k, n=200):
    return re.sub(r"[\x00-\x1f\x7f]", " ", str(d.get(k) or ""))[:n].strip()
rid, err, ep = s("id") or s("request_id"), "", ""
if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", rid) or rid.startswith("."):
    err = f"missing or invalid id {rid!r} (allowed: [A-Za-z0-9._-], 1-64 chars)"
    rid = ""
ts = s("requested_at")
if not ts:
    err = err or "missing requested_at"
else:
    try:
        t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.astimezone()          # naive -> this machine's local time
        ep = str(int(t.timestamp()))
    except ValueError:
        err = err or f"unparseable requested_at {ts!r}"
dec = s("decisions")
if dec and not re.fullmatch(r"(?:[Nn]one|D-\d+(?:[ ,]+D-\d+)*)", dec):
    err = err or f"invalid decisions {dec!r} (expected e.g. 'D-145 D-146' or 'none')"
for v in (rid, ep, s("requested_by"), s("message"), dec, err):
    print(v)
PY
}

# --- recovery at start: a ship that was running when the watcher died ------------------------
recover() {
  if [[ "$(status_field state)" == "running" ]] && ! lock_is_live; then
    local id; id="$(status_field id)"
    log "status says ship ${id} was running, and no watcher holds the lock: marking it interrupted"
    write_status id="$id" state=interrupted requested_at="$(status_field requested_at)" \
      requested_by="$(status_field requested_by)" started="$(status_field started)" \
      finished="$(iso)" log="$(status_field log)" \
      reason="the watcher stopped while the ship ran (restart, logout or crash); read the log; the request is NOT re-run" \
      watcher_version="$__version__"
    [[ -n "$id" ]] && cp -f "$STATUS" "${DONE}/${id}.status.json" 2>/dev/null || true
    [[ -f "$LOCK" ]] && set_lock_aside || true
  fi
}

refuse() {  # $1 id-or-label  $2 reason  (the request has already been moved into DONE)
  log "REFUSED ${1}: ${2}"
  write_status id="$1" state=refused requested_at="${R_AT_ISO:-}" requested_by="${R_BY:-}" \
    finished="$(iso)" reason="$2" watcher_version="$__version__"
  cp -f "$STATUS" "${DONE}/${1}.status.json" 2>/dev/null || true
  notify "ship request ${1} refused: ${2}"
}

WAIT_NOTED=""
poll_once() {
  [[ -f "$REQ" ]] || return 0

  if lock_is_live; then
    [[ "$WAIT_NOTED" == "lock" ]] || log "request pending; a ship is already running (pid $(lock_field pid)) - it waits"
    WAIT_NOTED="lock"; return 0
  fi
  local busy
  if busy="$(manual_ship_busy)"; then
    [[ "$WAIT_NOTED" == "manual" ]] || { log "request pending; nrg_git.sh (pid $busy) is busy at a terminal - it waits"
      write_status state=waiting reason="nrg_git.sh pid $busy is running by hand" since="$(iso)" watcher_version="$__version__"; }
    WAIT_NOTED="manual"; return 0
  fi

  local -a f
  mapfile -t f < <(parse_request "$REQ")
  local id="${f[0]:-}" at="${f[1]:-}" msg="${f[3]:-}" dec="${f[4]:-}" err="${f[5]:-}"
  (( ${#f[@]} >= 6 )) || err="the request file could not be read or parsed"
  [[ -z "$err" && ! "$at" =~ ^[0-9]+$ ]] && err="requested_at did not parse to a time"
  R_BY="${f[2]:-}"; R_AT_ISO=""
  [[ -n "$at" ]] && R_AT_ISO="$(date -u -d "@$at" +%Y-%m-%dT%H:%M:%SZ)"
  local now age=0 stale=""
  now="$(date +%s)"
  if [[ -z "$err" ]]; then
    age=$(( now - at ))
    if (( age > MAX_AGE )); then stale="stale: requested ${age}s ago (limit ${MAX_AGE}s); ask for a new ship"
    elif (( -age > FUTURE_SKEW )); then stale="requested_at is $(( -age ))s in the future; check the clock"
    fi
  fi

  # LibreOffice open: wait (or refuse), unless the request is to be refused anyway.
  if [[ -z "$err" && -z "$stale" && "$LO_POLICY" != "ignore" ]] && pgrep -x soffice.bin >/dev/null 2>&1; then
    if [[ "$LO_POLICY" == "wait" ]]; then
      [[ "$WAIT_NOTED" == "lo:$id" ]] || { log "request ${id} waits: LibreOffice is open - close it and the ship starts"
        write_status id="$id" state=waiting requested_at="$R_AT_ISO" requested_by="$R_BY" \
          reason="LibreOffice is open on the laptop; the ship starts when it closes (stale after ${MAX_AGE}s)" \
          since="$(iso)" watcher_version="$__version__"
        notify "ship ${id} is waiting: close LibreOffice"; }
      WAIT_NOTED="lo:$id"; return 0
    fi
    stale="LibreOffice is open (SHIP_WATCHER_LO_POLICY=refuse)"
  fi
  WAIT_NOTED=""

  acquire_lock "${id:-invalid}" || { log "could not take the ship lock; will retry"; return 0; }
  local r=0
  process_request "$id" "$msg" "$dec" "$err" "$stale" "$age" || r=$?
  release_lock
  return "$r"
}

# Called only while this watcher holds the ship lock.
process_request() {
  local id="$1" msg="$2" dec="$3" err="$4" stale="$5" age="$6"
  # Pick the request up: move it into DONE under its id. Never deleted, never run twice.
  local stamp; stamp="$(date +%Y%m%d_%H%M%S)"
  if [[ -n "$err" ]]; then
    mv "$REQ" "${DONE}/invalid.${stamp}.req"; refuse "invalid.${stamp}" "$err"; return 0
  fi
  if [[ -e "${DONE}/${id}.req" ]]; then
    mv "$REQ" "${DONE}/${id}.dup.${stamp}.req"; refuse "$id" "duplicate id: ${id} was already handled (${DONE}/${id}.req)"; return 0
  fi
  mv -n "$REQ" "${DONE}/${id}.req"
  [[ -e "$REQ" ]] && { log "could not move the request aside; not shipping"; return 0; }
  [[ -n "$stale" ]] && { refuse "$id" "$stale"; return 0; }

  # --- ship ---
  local log_f="${SCRATCH}/ship_watcher_${stamp}_${id}.log" last="${SCRATCH}/ship_watcher_last.log"
  local started; started="$(iso)"
  write_status id="$id" state=running requested_at="$R_AT_ISO" requested_by="$R_BY" \
    started="$started" log="$log_f" watcher_version="$__version__"
  log "SHIP ${id} starting (requested by ${R_BY:-?}, ${age}s ago) - output to ${log_f}"
  notify "ship ${id} started"

  local t0 tick_pid rc
  t0="$(date +%s)"
  ( while sleep 60; do
      e=$(( $(date +%s) - t0 ))
      printf '[ship_watcher %s]   [ ship %s running  %dm%02ds ]\n' "$(date +%H:%M:%S)" "$id" $((e/60)) $((e%60))
    done ) 9>&- &
  tick_pid=$!

  local -a args=(--ship)
  [[ -n "$msg" ]] && args+=("$msg")
  set +e
  {
    echo "===== ship_watcher ${__version__}: request ${id}, requested_by ${R_BY:-?}, at ${R_AT_ISO} ====="
    NRG_SHIP_WATCHER_ID="$id" NRG_SHIP_DECISIONS="$dec" \
      timeout -k 60 "$SHIP_TIMEOUT" bash "$SHIP_CMD" "${args[@]}" </dev/null 2>&1 9>&-
    echo "===== ship_watcher: nrg_git exit ${?} ====="
  } | tee "$log_f" "$last"
  set -e
  # Kill the ticker AND its sleep: an orphaned `sleep 60` is harmless, but anything a ship leaves
  # running must not hold the watcher's instance lock (fd 9), hence the `9>&-` on every child.
  pkill -P "$tick_pid" 2>/dev/null || true; kill "$tick_pid" 2>/dev/null || true
  wait "$tick_pid" 2>/dev/null || true

  rc="$(sed -n 's/^===== ship_watcher: nrg_git exit \([0-9]*\) =====$/\1/p' "$log_f" | tail -1)"
  rc="${rc:-1}"
  local verdict line exit_code
  line="$(grep -a '^SHIP: ' "$log_f" | tail -1 || true)"
  verdict="$(awk '{print $2}' <<<"$line")"
  case "$verdict" in
    OK)      exit_code=0 ;;
    PARTIAL) exit_code=2 ;;
    FAIL)    exit_code=1 ;;
    *)       verdict="NO_VERDICT"; exit_code="$rc"; (( exit_code == 0 )) && exit_code=1 ;;
  esac
  (( rc == 124 || rc == 137 )) && { verdict="TIMEOUT"; exit_code=124; }
  # nrg_git exit and verdict disagreeing is the known 1.25.1 defect, not news: record both.

  local sha_pub sha_priv pushed_pub="" pushed_priv="" ship_log
  sha_pub="$(GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD 2>/dev/null || true)"
  sha_priv="$(GIT_OPTIONAL_LOCKS=0 git --git-dir=.git-working rev-parse HEAD 2>/dev/null || true)"
  [[ -n "$sha_pub" ]] && { [[ "$(git rev-parse -q --verify origin/main 2>/dev/null || true)" == "$sha_pub" ]] && pushed_pub=yes || pushed_pub=no; }
  [[ -n "$sha_priv" ]] && { [[ "$(git --git-dir=.git-working rev-parse -q --verify origin/main 2>/dev/null || true)" == "$sha_priv" ]] && pushed_priv=yes || pushed_priv=no; }
  ship_log="$(grep -o 'scratch/ship_[0-9_]*\.log' <<<"$line" | head -1 || true)"

  write_status id="$id" state=done requested_at="$R_AT_ISO" requested_by="$R_BY" \
    started="$started" finished="$(iso)" exit_code="$exit_code" verdict="$verdict" \
    nrg_git_exit="$rc" ship_line="$line" sha_public="$sha_pub" sha_private="$sha_priv" \
    public_matches_origin="$pushed_pub" private_matches_origin="$pushed_priv" \
    log="$log_f" ship_log="$ship_log" watcher_version="$__version__"
  cp -f "$STATUS" "${DONE}/${id}.status.json" 2>/dev/null || true
  log "SHIP ${id} finished: ${verdict} (exit_code ${exit_code}, nrg_git exit ${rc}) - ${line:-no SHIP: line}"
  notify "ship ${id}: ${verdict}"
  return 0
}

on_term() {
  log "stopping (signal)"
  if [[ -f "$LOCK" && "$(lock_field pid)" == "$$" ]]; then
    local id; id="$(lock_field id)"
    write_status id="$id" state=interrupted finished="$(iso)" log="$(status_field log)" \
      reason="the watcher was stopped while the ship ran; read the log; the request is NOT re-run" \
      watcher_version="$__version__"
    cp -f "$STATUS" "${DONE}/${id}.status.json" 2>/dev/null || true
    release_lock
  fi
  exit 143
}
trap on_term TERM INT

recover
log "ship_watcher ${__version__} watching ${REPO}/${REQ} every ${POLL}s (stale after ${MAX_AGE}s, LibreOffice policy ${LO_POLICY})"
n=0
while true; do
  poll_once || log "poll failed (rc $?) - continuing"
  (( ONCE )) && break
  n=$(( n + 1 ))
  if (( n % HEARTBEAT_POLLS == 0 )); then log "idle - no request (polling every ${POLL}s)"; fi
  sleep "$POLL" 9>&- & wait $! || true
done
