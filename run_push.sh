#!/usr/bin/env bash
# run_push.sh - what the "Newborough Push" desktop launcher runs.
cd "${HOME}/projects/NRG" || { echo "Can't find ~/projects/NRG"; read -rp "Press Enter to close"; exit 1; }
./push_frozen.sh
echo
read -rp "Finished. Press Enter to close this window."
