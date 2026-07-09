#!/usr/bin/env bash
# =============================================================================
# make_text_mirror.sh — regenerate the diffable text mirror of the report
#                       subdocuments.
#
# WHY THIS EXISTS
#   .odt files are zip archives. Git cannot delta-compress or diff them, so a
#   committed .odt shows up as an opaque binary blob with no readable history.
#   This script emits a markdown mirror under report_edits/text/ so that caption
#   edits, figure renumbering and cross-reference changes appear as ordinary
#   line diffs in version control.
#
#   Pandoc preserves embedded OpenDocument Formula objects as LaTeX, so the
#   mirror carries the equations too — it is a complete rendering of the
#   document, not just its prose.
#
#   report4.odt and report9.odt (~195 MB each) are NOT committed: they exceed
#   GitHub's 100 MB file limit, and their figures already live in outputs/.
#   Their markdown mirror is therefore the ONLY versioned record of those
#   chapters' content. Mirroring every subdocument is not optional.
#
# USAGE
#   Run before nrg_git.sh:
#       ./report_edits/make_text_mirror.sh
#
#   Then commit both trees together:
#       ./nrg_git.sh
#
# VERSION
#   v1.0.0  2026-07-09  initial
# =============================================================================

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ODT_DIR="${HERE}/odt"
TXT_DIR="${HERE}/text"

# --- preflight ---------------------------------------------------------------
if ! command -v pandoc >/dev/null 2>&1; then
    echo "error: pandoc not found on PATH. Install with: sudo apt install pandoc" >&2
    exit 1
fi

if [ ! -d "${ODT_DIR}" ]; then
    echo "error: no such directory: ${ODT_DIR}" >&2
    exit 1
fi

mkdir -p "${TXT_DIR}"

# --- collect subdocuments in natural order (report2 before report10) ---------
shopt -s nullglob
mapfile -t odts < <(printf '%s\n' "${ODT_DIR}"/*.odt | sort -V)
shopt -u nullglob

if [ "${#odts[@]}" -eq 0 ]; then
    echo "warn: no .odt files found in ${ODT_DIR} — nothing to mirror" >&2
    exit 0
fi

echo "mirroring ${#odts[@]} subdocument(s) from ${ODT_DIR}"
echo

mirrored=0
skipped=0
failed=0

for odt in "${odts[@]}"; do
    base="$(basename "${odt}" .odt)"
    out="${TXT_DIR}/${base}.md"

    # Skip empty subdocuments (e.g. report0.odt, the LibreOffice split artefact
    # holding the fragment before the first heading). Pandoc errors on these.
    if [ ! -s "${odt}" ]; then
        printf '  %-16s skipped (0 bytes)\n' "${base}.odt"
        skipped=$((skipped + 1))
        continue
    fi

    # --wrap=none keeps one paragraph per line, so a reworded sentence appears
    # as a single changed line rather than reflowing the whole paragraph.
    if pandoc "${odt}" \
        --from=odt \
        --to=markdown_strict \
        --wrap=none \
        --output="${out}" 2>/dev/null
    then
        size="$(du -h "${out}" | cut -f1)"
        printf '  %-16s -> text/%-16s %s\n' "${base}.odt" "${base}.md" "${size}"
        mirrored=$((mirrored + 1))
    else
        printf '  %-16s FAILED\n' "${base}.odt" >&2
        failed=$((failed + 1))
    fi
done

# --- note any stale mirrors whose .odt has gone away -------------------------
for md in "${TXT_DIR}"/*.md; do
    [ -e "${md}" ] || continue
    base="$(basename "${md}" .md)"
    if [ ! -f "${ODT_DIR}/${base}.odt" ]; then
        echo "  note: text/${base}.md has no matching .odt (stale mirror?)" >&2
    fi
done

# --- summary -----------------------------------------------------------------
echo
echo "mirrored: ${mirrored}   skipped: ${skipped}   failed: ${failed}"

if [ "${failed}" -gt 0 ]; then
    echo >&2
    echo "error: ${failed} subdocument(s) failed to convert — mirror is incomplete." >&2
    echo "       Do NOT commit until resolved." >&2
    exit 1
fi

echo
echo "reminder: report4.odt and report9.odt are gitignored (>100 MB). Their .md"
echo "          mirror is the only versioned record of those chapters."
