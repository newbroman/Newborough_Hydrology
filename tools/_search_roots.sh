#!/usr/bin/env bash
# _search_roots.sh — the one list of places a stray or deleted project document
# can be. Sourced by find_missing_docs.sh and stage_recovered_docs.sh; not
# runnable on its own. Sets ROOTS.
#
# Why this file exists: the first version of the sweep used `find "$HOME" -xdev`
# and so silently skipped both of Martin's cloud drives, which are FUSE mounts
# and therefore a different filesystem. `-xdev` is still right — one stalled
# network mount must not hang the whole sweep — but every mount then has to be
# named as a root of its own. The 2026-08-25 content sweep found an entire
# earlier NRG tree under Google Drive that the filename sweep had never seen.

_add_root() { [ -d "$1" ] && ROOTS+=( "$1" ); }

ROOTS=()
_add_root "$HOME"
_add_root /tmp
_add_root /var/tmp

# Trash, including removable-media trash cans.
for t in "$HOME/.local/share/Trash/files" "$HOME/.Trash" \
         /media/*/.Trash-"$(id -u)" /run/media/"$USER"/*/.Trash-"$(id -u)"; do
  _add_root "$t"
done

# Removable media.
for m in /media/"$USER"/* /media/* /mnt/*; do
  case "$m" in *"/.Trash-"*) continue ;; esac
  _add_root "$m"
done

# Cloud sync folders. These are the ones that matter most and the ones -xdev
# excludes. Named explicitly first, then any other mountpoint sitting directly
# under $HOME, so a drive not on this list is still picked up.
if [ "${NRG_SKIP_CLOUD:-0}" != "1" ]; then
  for c in "$HOME/Google Drive" "$HOME/GoogleDrive" "$HOME/gdrive" \
           "$HOME/pCloudDrive" "$HOME/Dropbox" "$HOME/OneDrive" \
           "$HOME/Nextcloud" "$HOME/ownCloud" "$HOME/Insync" "$HOME/Sync" \
           "$HOME/MEGA" "$HOME/Seafile"; do
    _add_root "$c"
  done
  for d in "$HOME"/*/; do
    d="${d%/}"
    case " ${ROOTS[*]} " in *" $d "*) continue ;; esac
    if command -v mountpoint >/dev/null 2>&1 && mountpoint -q "$d" 2>/dev/null; then
      _add_root "$d"
    fi
  done
fi

# De-duplicate, keeping order. A root that is a subdirectory of another is kept
# deliberately: $HOME is searched -xdev, so a mount beneath it is NOT covered by
# the $HOME pass and needs its own.
_seen=""; _uniq=()
for r in "${ROOTS[@]}"; do
  case " $_seen " in *" $r "*) continue ;; esac
  _seen="$_seen $r"; _uniq+=( "$r" )
done
ROOTS=( "${_uniq[@]}" )
