#!/usr/bin/env bash
# build_pdfs.sh — regenerate published PDFs from the LATEST working ODT, writing
# to the STABLE filenames index.html links to. No version ever touches the
# published PDF (name or content), so index.html never needs editing.
#
#   bash build_pdfs.sh           rebuild only STALE PDFs (ODT newer/missing) — idempotent
#   bash build_pdfs.sh --force   rebuild every published PDF regardless
#   bash build_pdfs.sh --check   report staleness only, build nothing
#
# Requires LibreOffice (soffice). Close the LibreOffice GUI first — a headless
# run can clash with an open instance. Version traceability -> docs/PDF_MANIFEST.txt
# (which ODT version each published PDF came from). report.pdf is NOT built here
# (report.odm is a master document — export it by hand to docs/report/report.pdf).

set -euo pipefail
# Work from the repo root no matter where this script lives (root, tools/, …).
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || echo "$HERE")"
cd "$ROOT"

CHECK=0; FORCE=0
case "${1:-}" in --check) CHECK=1 ;; --force) FORCE=1 ;; esac
MANIFEST="docs/PDF_MANIFEST.txt"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
SOFFICE="$(command -v soffice || command -v libreoffice || true)"
[[ -z "$SOFFICE" ]] && { echo "ERROR: LibreOffice (soffice) not found on PATH."; exit 1; }

# Convention: each working ODT lives in the SAME folder as its published PDF.
MAP=(
  "docs/report/Newborough_Methods_Supplement_v1_*.odt|docs/report/Newborough_Methods_Supplement.pdf"
  "docs/report/Supplementary_Material_v1_*.odt|docs/report/Supplementary_Material.pdf"
  "docs/academic_summaries/academic_Summary_v1_*.odt|docs/academic_summaries/academic_summary.pdf"
  "docs/academic_summaries/crynodeb_academaidd_v1_*.odt|docs/academic_summaries/crynodeb_academaidd.pdf"
  "docs/public_summaries/public_summary_EN.odt|docs/public_summaries/Newborough_Warren_Public_Summary.pdf"
  "docs/public_summaries/public_summary_CY.odt|docs/public_summaries/Niwbwrch_Crynodeb_Cyhoeddus.pdf"
  "docs/public_summaries/public_summary_PL.odt|docs/public_summaries/Newborough_Warren_Podsumowanie.pdf"
  "docs/web_tools/NRG_Web_Tools_Technical_Note.odt|docs/web_tools/NRG_Web_Tools_Technical_Note.pdf"
  "docs/web_tools/NRG_Web_Tools_User_Manual.odt|docs/web_tools/NRG_Web_Tools_User_Manual.pdf"
  # Paper 1 and its SI were absent from this list until 2026-08-18, so their
  # published PDFs were only ever exported by hand and drifted four days behind
  # the working ODTs. Same convention as every row above: newest versioned ODT
  # in, stable published filename out.
  "docs/papers/paper_1/Paper1_v1_*.odt|docs/papers/paper_1/Paper1.pdf"
  "docs/papers/paper_2/Hollingham_2026_Paper2_amended_v*.odt|docs/papers/paper_2/Hollingham_2026_Paper2_amended.pdf"
  "docs/papers/paper_1/PAPER1_SI_methods_v1_*.odt|docs/papers/paper_1/PAPER1_SI_methods.pdf"
)
latest() { ls -v $1 2>/dev/null | tail -1; }        # highest version matching the glob

manifest_line() {  # $1 pdf  $2 src ; use the PDF's own mtime (accurate whether built now or earlier)
  local when; when="$(date -u -r "$1" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "$1  <-  $(basename "$2")  |  $when"
}

built=0; current=0; stale=0; missing=0; noodt=0
NEW_MANIFEST="$TMP/manifest"; : > "$NEW_MANIFEST"
for row in "${MAP[@]}"; do
  glob="${row%%|*}"; out="${row##*|}"
  src="$(latest "$glob")"
  if [[ -z "$src" ]]; then echo "  NO-ODT    $out"; noodt=$((noodt+1)); continue; fi

  if [[ $CHECK -eq 1 ]]; then
    if [[ ! -f "$out" ]]; then echo "  MISSING   $out  <- $(basename "$src")"; stale=$((stale+1))
    elif [[ "$src" -nt "$out" ]]; then echo "  STALE     $out  <- $(basename "$src")"; stale=$((stale+1))
    else echo "  ok        $out  <- $(basename "$src")"; current=$((current+1)); fi
    continue
  fi

  if [[ $FORCE -eq 0 && -f "$out" && ! "$src" -nt "$out" ]]; then
    echo "  current   $out  <- $(basename "$src")"; current=$((current+1))
    manifest_line "$out" "$src" >> "$NEW_MANIFEST"; continue
  fi

  mkdir -p "$(dirname "$out")"
  "$SOFFICE" --headless --convert-to pdf --outdir "$TMP" "$src" >/dev/null 2>&1 || true
  gen="$TMP/$(basename "${src%.odt}").pdf"
  if [[ -f "$gen" ]]; then
    mv -f "$gen" "$out"
    echo "  built     $out  <- $(basename "$src")"; built=$((built+1))
    manifest_line "$out" "$src" >> "$NEW_MANIFEST"
  else
    echo "  FAILED    $out  <- $(basename "$src")"
  fi
done

echo
if [[ $CHECK -eq 1 ]]; then
  echo "Check: $current current, $stale stale/missing, $noodt with no ODT source."
  [[ $stale -gt 0 ]] && echo "Run 'build_pdfs.sh' to rebuild." || true
else
  { echo "# published PDF  <-  source ODT  |  built (UTC)"; sort "$NEW_MANIFEST"; } > "$MANIFEST"
  echo "Rebuilt $built PDF(s); $current already current. Manifest: $MANIFEST"
  echo "Reminder: report.pdf (from report.odm) is exported by hand — not built here."
fi
