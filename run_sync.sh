#!/usr/bin/env bash
# run_sync.sh - what the "Newborough Sync" desktop launcher runs.
# Opens in a terminal, runs the monthly sync, then waits so you can read the result.
cd "${HOME}/projects/NRG" || { echo "Can't find ~/projects/NRG"; read -rp "Press Enter to close"; exit 1; }
./nhgr_sync.sh
echo
read -rp "Finished. Press Enter to close this window."
