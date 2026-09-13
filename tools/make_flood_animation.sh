#!/usr/bin/env bash
# Build the flood-series animation from the frames phase 14 rendered.
#
# WHY THIS IS A SEPARATE SCRIPT. The frames are working files, not artefacts:
# 229 PNGs at roughly a quarter of a megabyte each is 60 MB that the pipeline
# regenerates on demand, so they are gitignored and only the animation is kept.
# Rebuilding from the frames rather than re-running phase 14 also means the
# encode can be retried without recomputing 229 surfaces.
#
# Usage:  bash tools/make_flood_animation.sh [fps]
set -euo pipefail
FPS="${1:-6}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$HERE/working/updates/W94_frames"
OUT="$HERE/working/updates"

[ -d "$SRC" ] || { echo "no frames: run phase 14 with --frames first"; exit 1; }
N=$(find "$SRC" -name 'frame_*.png' | wc -l)
[ "$N" -gt 0 ] || { echo "no frames in $SRC"; exit 1; }
echo "  $N frame(s) at ${FPS} fps"

command -v ffmpeg >/dev/null || { echo "ffmpeg not found"; exit 1; }

# -pix_fmt yuv420p and the even-dimension pad: without both, the mp4 plays in
# ffplay and in nothing else. Frames are padded, never scaled, so the map keeps
# its geometry.
ffmpeg -y -loglevel error -framerate "$FPS" -pattern_type glob \
    -i "$SRC/frame_*.png" \
    -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=white" \
    -c:v libx264 -pix_fmt yuv420p -crf 20 \
    "$OUT/W94_54_flood_series.mp4"
echo "  wrote W94_54_flood_series.mp4  ($(du -h "$OUT/W94_54_flood_series.mp4" | cut -f1))"

# A GIF as well, at half rate and reduced width, for anywhere an mp4 will not
# embed. Palette generated from the whole sequence or the blues band.
ffmpeg -y -loglevel error -framerate "$((FPS/2>0?FPS/2:3))" -pattern_type glob \
    -i "$SRC/frame_*.png" \
    -vf "scale=900:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer" \
    "$OUT/W94_54_flood_series.gif"
echo "  wrote W94_54_flood_series.gif  ($(du -h "$OUT/W94_54_flood_series.gif" | cut -f1))"
