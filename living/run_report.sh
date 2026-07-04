#!/usr/bin/env bash
#
# Newborough Warren Monthly Water Level Report
# ============================================
# v2.0.0  (2026-07-04) — wired to the git clone layout (~/projects/NRG)
#   * Reads coords/DEM/KML from the repo: data/well_metadata.csv, data/geo/.
#   * Reads the MASTER workbook from its Google Drive home (one canonical copy;
#     never copied into the repo). Set MASTER_ODS below if your path differs.
#   * Monthly inputs (valleydata.txt) live in  living/inbox/  (gitignored).
#   * Outputs go to  living/output/<year>/<Month>/  (gitignored).
#   * Removed the old self-contained living/data + living/kml assumption and the
#     stale Well_locations_height.csv name.
#
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# ── Layout (resolved from this script's location) ────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # .../NRG/living
REPO_DIR="$(dirname "${SCRIPT_DIR}")"                         # .../NRG
DATA_DIR="${REPO_DIR}/data"                                   # coords, climate
GEO_DIR="${REPO_DIR}/data/geo"                                # DEM + KMLs
INBOX="${SCRIPT_DIR}/inbox"                                   # gitignored inputs
OUTPUT_DIR="${SCRIPT_DIR}/output"                             # gitignored outputs
REPORT_SCRIPT="${SCRIPT_DIR}/newborough_report.py"
VENV_DIR="${HOME}/.newborough_venv"

# ── The one path you may need to edit: the private master workbook ───────────
# Single canonical copy, left on Google Drive (backed up there). Scripts read it
# in place — it is never copied into the repo.
MASTER_ODS="${HOME}/Google Drive/projects/newborough/spreadsheets/Newborough_well_records.ods"

# ── Derived inputs ───────────────────────────────────────────────────────────
COORDS_FILE="${DATA_DIR}/well_metadata.csv"        # Name,E,N,...  (report reads Name/E/N)
DEM_FILE="${GEO_DIR}/newborough_dem.tif"
KML_DIR="${GEO_DIR}"
VALLEY_FILE="${INBOX}/valleydata.txt"
VALLEY_LINK="https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt"

mkdir -p "${INBOX}" "${OUTPUT_DIR}"

info()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn()   { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail()   { echo -e "  ${RED}✗${NC} $1"; }
step()   { echo -e "\n${CYAN}── $1 ──${NC}"; }

pause_and_exit() {
    local code=${1:-0}
    echo ""
    if [ "$code" -ne 0 ]; then
        echo -e "${RED}  Stopped. Fix the issue above and re-run.${NC}"
    fi
    echo -en "  Press Enter to close..."
    read -r
    exit "$code"
}

# ── Subcommands: setup / update / clean ──────────────────────────────────────
PKGS="pandas numpy scipy matplotlib rasterio geopandas fiona pyproj reportlab odfpy"

case "$(echo "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    setup)
        echo ""
        echo -e "${BLUE}  Newborough report — first-time setup${NC}"
        if command -v python3 &>/dev/null; then PYTHON_CMD="python3"
        elif command -v python &>/dev/null; then PYTHON_CMD="python"
        else fail "Python not found. Install Python 3.10+ from https://www.python.org/downloads/"; pause_and_exit 1; fi
        info "Python: $($PYTHON_CMD --version)"
        if [ ! -d "${VENV_DIR}" ]; then
            echo "  Creating virtual environment at ${VENV_DIR} ..."
            $PYTHON_CMD -m venv "${VENV_DIR}" || { fail "Could not create venv"; pause_and_exit 1; }
        else
            info "Venv already exists at ${VENV_DIR}"
        fi
        source "${VENV_DIR}/bin/activate"
        echo "  Installing packages..."
        pip install --quiet $PKGS || { fail "Package install failed"; pause_and_exit 1; }
        info "Setup complete. Run ./run_report.sh to generate a report."
        pause_and_exit 0
        ;;
    update)
        echo ""
        echo -e "${BLUE}  Newborough report — update Valley data${NC}"
        mkdir -p "${INBOX}"
        echo "  Downloading RAF Valley data from the Met Office..."
        DL_OK=false
        if command -v curl &>/dev/null; then
            curl -fsSL -A "Mozilla/5.0" "${VALLEY_LINK}" -o "${VALLEY_FILE}.tmp" && DL_OK=true
        elif command -v wget &>/dev/null; then
            wget -q --user-agent="Mozilla/5.0" -O "${VALLEY_FILE}.tmp" "${VALLEY_LINK}" && DL_OK=true
        else
            fail "Neither curl nor wget found. Download manually:"
            echo -e "  ${CYAN}${VALLEY_LINK}${NC}"
            echo "  and save it to: ${VALLEY_FILE}"
            pause_and_exit 1
        fi
        if [ "$DL_OK" = true ]; then
            mv "${VALLEY_FILE}.tmp" "${VALLEY_FILE}"
            LAST_LINE=$(grep -E '^\s+[0-9]{4}\s+[0-9]+' "${VALLEY_FILE}" | tail -1)
            if [ -n "$LAST_LINE" ]; then
                LAST_Y=$(echo "$LAST_LINE" | awk '{print $1}')
                LAST_M=$(echo "$LAST_LINE" | awk '{printf "%02d", $2}')
                info "Valley data updated — latest month now: ${LAST_Y}-${LAST_M}"
            else
                warn "Downloaded, but couldn't parse a month — check it opened correctly."
            fi
        else
            rm -f "${VALLEY_FILE}.tmp"
            fail "Download failed (existing file left untouched). Check your connection, or download manually:"
            echo -e "  ${CYAN}${VALLEY_LINK}${NC}"
            pause_and_exit 1
        fi
        pause_and_exit 0
        ;;
    clean)
        echo ""
        echo -e "${BLUE}  Newborough report — remove venv${NC}"
        if [ -d "${VENV_DIR}" ]; then
            echo -en "  ${YELLOW}?${NC} Remove ${VENV_DIR}? [y/N]: "
            read -r REPLY
            if [[ "$REPLY" =~ ^[Yy] ]]; then
                rm -rf "${VENV_DIR}"; info "Removed ${VENV_DIR}. It rebuilds on next run."
            else
                info "Left the venv in place."
            fi
        else
            info "No venv at ${VENV_DIR} — nothing to remove."
        fi
        pause_and_exit 0
        ;;
esac

# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Newborough Warren Water Level Report${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "  ${BOLD}Repo:${NC}   ${REPO_DIR}"
echo -e "  ${BOLD}Master:${NC} ${MASTER_ODS}"
echo -e "  ${BOLD}Inbox:${NC}  ${INBOX}"
echo -e "  ${BOLD}Output:${NC} ${OUTPUT_DIR}"

# ── Step 1: Which month? ─────────────────────────────────────────────────────
step "Step 1: Which month are we writing the report for?"
echo "  (The reading for this month was taken at month-end or early next month.)"

CUR_YEAR=$(date +%Y)
DEFAULT=$(date -d "last month" +%Y-%m 2>/dev/null || date -v-1m +%Y-%m 2>/dev/null || date +%Y-%m)

month_to_num() {
    case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
        jan*) echo 01 ;; feb*) echo 02 ;; mar*) echo 03 ;; apr*) echo 04 ;;
        may)  echo 05 ;; jun*) echo 06 ;; jul*) echo 07 ;; aug*) echo 08 ;;
        sep*) echo 09 ;; oct*) echo 10 ;; nov*) echo 11 ;; dec*) echo 12 ;;
        *) echo "" ;;
    esac
}

parse_month() {
    local input="$1"
    [ -z "$input" ] && echo "$DEFAULT" && return
    if echo "$input" | grep -qE '^[0-9]{4}-[0-9]{1,2}$'; then
        local y="${input%%-*}" m="${input##*-}"; printf "%s-%02d" "$y" "$((10#$m))"; return
    fi
    if echo "$input" | grep -qE '^[0-9]{1,2}$'; then
        local m=$((10#$input))
        if [ "$m" -ge 1 ] && [ "$m" -le 12 ]; then printf "%s-%02d" "$CUR_YEAR" "$m"; return; fi
    fi
    local mm; mm=$(month_to_num "$input")
    if [ -n "$mm" ]; then printf "%s-%s" "$CUR_YEAR" "$mm"; return; fi
    local word1 word2; word1=$(echo "$input" | awk '{print $1}'); word2=$(echo "$input" | awk '{print $2}')
    mm=$(month_to_num "$word1")
    if [ -n "$mm" ] && [ -n "$word2" ]; then
        local y="$word2"; [ ${#y} -eq 2 ] && y="20${y}"; printf "%s-%s" "$y" "$mm"; return
    fi
    echo ""
}

TARGET="${1:-}"
[ -n "$TARGET" ] && TARGET=$(parse_month "$TARGET")

while true; do
    if [ -z "$TARGET" ]; then
        echo -en "  ${YELLOW}?${NC} Enter month [${DEFAULT}]: "
        read -r INPUT; TARGET=$(parse_month "$INPUT")
    fi
    if echo "$TARGET" | grep -qE '^[0-9]{4}-[0-9]{2}$'; then
        MM_NUM=$((10#${TARGET##*-}))
        MONTH_NAMES=("" "January" "February" "March" "April" "May" "June"
                     "July" "August" "September" "October" "November" "December")
        info "Report month: ${MONTH_NAMES[$MM_NUM]} ${TARGET%%-*} (${TARGET})"
        break
    else
        warn "Didn't understand that. Try: 2026-07, 7, July, or press Enter for ${DEFAULT}"
        TARGET=""
    fi
done

# ── Step 2: Valley met data ──────────────────────────────────────────────────
step "Step 2: Valley met data"
TARGET_YEAR="${TARGET%%-*}"; TARGET_MM="${TARGET##*-}"; TARGET_MM_NUM=$((10#$TARGET_MM))

if [ ! -f "${VALLEY_FILE}" ]; then
    warn "No Valley data yet — fetching it now..."
    if command -v curl &>/dev/null; then
        curl -fsSL -A "Mozilla/5.0" "${VALLEY_LINK}" -o "${VALLEY_FILE}" || warn "fetch failed; continue without if you like"
    fi
fi

if [ -f "${VALLEY_FILE}" ] && grep -qE "^\s+${TARGET_YEAR}\s+${TARGET_MM_NUM}\s" "${VALLEY_FILE}"; then
    info "Valley data has ${TARGET} ✓"
else
    LAST_LINE=$(grep -E '^\s+[0-9]{4}\s+[0-9]+' "${VALLEY_FILE}" 2>/dev/null | tail -1)
    LAST_Y=$(echo "$LAST_LINE" | awk '{print $1}'); LAST_M=$(echo "$LAST_LINE" | awk '{printf "%02d", $2}')
    warn "Met Office Valley data for ${TARGET} isn't available yet (file runs to ${LAST_Y:-?}-${LAST_M:-?})."
    echo "  The Met Office publishes each month ~2nd working day after it ends."
    echo "  Fetch the latest with:  ${CYAN}./run_report.sh update${NC}"
    echo ""
    echo -en "  ${YELLOW}?${NC} Continue without Valley data for ${TARGET}? [y/N]: "
    read -r REPLY
    if [[ ! "$REPLY" =~ ^[Yy] ]]; then
        echo "  Waiting is usually the right call — re-run once it's published."
        pause_and_exit 0
    fi
    warn "Continuing — report will note Valley data unavailable"
fi

# ── Step 3: Python environment ───────────────────────────────────────────────
step "Step 3: Python environment"
if command -v python3 &>/dev/null; then PYTHON_CMD="python3"
elif command -v python &>/dev/null; then PYTHON_CMD="python"
else fail "Python not found. Install Python 3.10+"; pause_and_exit 1; fi
info "Python: $($PYTHON_CMD --version)"

if [ ! -d "${VENV_DIR}" ]; then echo "  Creating virtual environment..."; $PYTHON_CMD -m venv "${VENV_DIR}"; fi
source "${VENV_DIR}/bin/activate"
info "Venv active"

MISSING=""
for pkg in pandas numpy scipy matplotlib rasterio geopandas fiona pyproj reportlab odfpy; do
    IMPORT_NAME="$pkg"; [ "$pkg" = "odfpy" ] && IMPORT_NAME="odf"
    python -c "import ${IMPORT_NAME}" 2>/dev/null || MISSING="${MISSING} ${pkg}"
done
if [ -n "$MISSING" ]; then warn "Installing:${MISSING}"; pip install --quiet $MISSING; fi
info "All packages installed"

# ── Step 4: Data files ───────────────────────────────────────────────────────
step "Step 4: Data files"
OK=true

if [ -f "${MASTER_ODS}" ]; then
    info "Master workbook: $(basename "${MASTER_ODS}")"
else
    fail "Master not found at:"
    echo "        ${MASTER_ODS}"
    echo "        (edit MASTER_ODS near the top of this script if the path is different)"
    OK=false
fi
[ -f "${COORDS_FILE}" ] && info "Coordinates  ✓ ($(basename "${COORDS_FILE}"))" || { fail "well_metadata.csv missing in ${DATA_DIR}"; OK=false; }
[ -f "${DEM_FILE}" ]    && info "DEM          ✓" || warn "DEM missing — no hillshade on maps"
KML_N=$(find "${KML_DIR}" -maxdepth 1 -name "*.kml" 2>/dev/null | wc -l)
[ "$KML_N" -gt 0 ]     && info "KML layers   ✓ (${KML_N} in data/geo/)" || warn "No KMLs — no site features on maps"
[ -f "${REPORT_SCRIPT}" ] && info "Report script ✓" || { fail "newborough_report.py missing"; OK=false; }

[ "$OK" = false ] && pause_and_exit 1

# ── Step 5: Generate report ──────────────────────────────────────────────────
MONTH_OUTPUT="${OUTPUT_DIR}/${TARGET%%-*}/${MONTH_NAMES[$MM_NUM]}"
mkdir -p "${MONTH_OUTPUT}"
step "Step 5: Generating ${MONTH_NAMES[$MM_NUM]} ${TARGET%%-*} report"

python "${REPORT_SCRIPT}" "${TARGET}" \
    --wells "${MASTER_ODS}" \
    --valley "${VALLEY_FILE}" \
    --coords_csv "${COORDS_FILE}" \
    --dem "${DEM_FILE}" \
    --kml_dir "${KML_DIR}" \
    --output_dir "${MONTH_OUTPUT}" \
    --no_valley_update

echo ""
step "Done!"
info "Output files in: ${MONTH_OUTPUT}/"
ls -1 "${MONTH_OUTPUT}/" 2>/dev/null | sed 's/^/      /'

pause_and_exit 0
