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
# (which ODT version each published PDF came from). report.pdf is NOT built here:
# report.odm is a master document, and a plain convert-to neither pulls its linked
# chapters nor refreshes the sequence fields the figure numbers live in. Since
# 2026-08-28 tools/export_master_pdf.py does that through UNO and lints the result
# before publishing it; nrg_git.sh offers it immediately after this script runs.
#
# Since 2026-09-05 (W137/D-135) the per-document export refreshes the TOC and
# sequence fields first, through UNO (tools/export_odt_pdf.py, sharing
# tools/uno_pdf.py with the master export). If python3-uno is not importable it
# WARNS and falls back to a plain --convert-to (page/figure numbers unrefreshed).

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

built=0; current=0; stale=0; missing=0; noodt=0; fellback=0
NEW_MANIFEST="$TMP/manifest"; : > "$NEW_MANIFEST"

# Find a UNO-capable interpreter for the refreshing export. python3-uno lives in
# the system dist-packages; a venv built without --system-site-packages cannot
# import it (the nrg_git 1.13.0 lesson). Empty => fall back to --convert-to.
UNO_PY=""
if [[ $CHECK -eq 0 ]]; then
  for c in python3 /usr/bin/python3 python3.12 /usr/bin/python3.12; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import uno' >/dev/null 2>&1; then
      UNO_PY="$c"; break
    fi
  done
  if [[ -z "$UNO_PY" ]]; then
    echo "  WARNING: python3-uno not importable by any interpreter tried."
    echo "           Falling back to 'soffice --convert-to' — the TOC page numbers"
    echo "           and figure/table numbers will NOT be refreshed (W137)."
    echo "           Install python3-uno for refreshed PDFs."
    echo
  fi
fi

# Decide per row; collect the ones that need building.
# Explicit empty-array assignment (not `declare -a`): under set -u a declared-but-
# never-assigned array errors on ${#arr[@]} when nothing is stale (bash 5.1).
B_SRC=(); B_OUT=()
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
  B_SRC+=("$src"); B_OUT+=("$out")
done

# Build the collected rows, in one soffice session where UNO is available.
if [[ $CHECK -eq 0 && ${#B_SRC[@]} -gt 0 ]]; then
  marker="$TMP/.mk"; touch -d '1 second ago' "$marker" 2>/dev/null || touch "$marker"
  if [[ -n "$UNO_PY" ]]; then
    ARGS=(); for k in "${!B_SRC[@]}"; do ARGS+=("${B_SRC[$k]}" "${B_OUT[$k]}"); done
    "$UNO_PY" tools/export_odt_pdf.py "${ARGS[@]}" || true
  else
    for k in "${!B_SRC[@]}"; do
      src="${B_SRC[$k]}"; out="${B_OUT[$k]}"
      "$SOFFICE" --headless --convert-to pdf --outdir "$TMP" "$src" >/dev/null 2>&1 || true
      gen="$TMP/$(basename "${src%.odt}").pdf"
      [[ -f "$gen" ]] && mv -f "$gen" "$out"
    done
  fi
  # A file is built iff it was written after the marker (src ODTs are older).
  for k in "${!B_OUT[@]}"; do
    src="${B_SRC[$k]}"; out="${B_OUT[$k]}"
    if [[ -f "$out" && "$out" -nt "$marker" ]]; then
      if [[ -n "$UNO_PY" ]]; then echo "  built     $out  <- $(basename "$src")"
      else echo "  built*    $out  <- $(basename "$src")  (unrefreshed fallback)"; fellback=$((fellback+1)); fi
      built=$((built+1)); manifest_line "$out" "$src" >> "$NEW_MANIFEST"
    else
      echo "  FAILED    $out  <- $(basename "$src")"
    fi
  done
fi

echo
if [[ $CHECK -eq 1 ]]; then
  echo "Check: $current current, $stale stale/missing, $noodt with no ODT source."
  [[ $stale -gt 0 ]] && echo "Run 'build_pdfs.sh' to rebuild." || true
else
  { echo "# published PDF  <-  source ODT  |  built (UTC)"; sort "$NEW_MANIFEST"; } > "$MANIFEST"
  echo "Rebuilt $built PDF(s); $current already current. Manifest: $MANIFEST"
  [[ $fellback -gt 0 ]] && echo "  NOTE: $fellback built via --convert-to fallback (UNrefreshed) — install python3-uno."
  echo "Note: report.pdf (from report.odm) is not built here — a master document needs its"
  echo "      links, fields and indexes refreshed first. tools/export_master_pdf.py does that"
  echo "      and lints the result; nrg_git.sh offers it straight after this step."
fi
