#!/usr/bin/env bash
#
# Newborough Warren Monthly Water Level Report
#
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/data"
KML_DIR="${SCRIPT_DIR}/kml"
OUTPUT_DIR="${SCRIPT_DIR}/output"
REPORT_SCRIPT="${SCRIPT_DIR}/newborough_report.py"
VENV_DIR="${HOME}/.newborough_venv"
VALLEY_FILE="${DATA_DIR}/valleydata.txt"
COORDS_FILE="${DATA_DIR}/Well_locations_height.csv"
DEM_FILE="${DATA_DIR}/newborough_dem.tif"
VALLEY_LINK="https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt"

info()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn()   { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail()   { echo -e "  ${RED}✗${NC} $1"; }
step()   { echo -e "\n${CYAN}── $1 ──${NC}"; }

# ── Always pause before closing ──────────────────────────────────────────────
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
# Intercept $1 before it is treated as a month. Anything that is not one of
# these (a month, a number, "May", or empty) falls through to the report flow.
PKGS="pandas numpy scipy matplotlib rasterio geopandas fiona pyproj reportlab odfpy"

case "$(echo "${1:-}" | tr '[:upper:]' '[:lower:]')" in
    setup)
        echo ""
        echo -e "${BLUE}  Newborough report — first-time setup${NC}"
        if command -v python3 &>/dev/null; then
            PYTHON_CMD="python3"
        elif command -v python &>/dev/null; then
            PYTHON_CMD="python"
        else
            fail "Python not found. Install Python 3.10+ from https://www.python.org/downloads/"
            pause_and_exit 1
        fi
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
        mkdir -p "${DATA_DIR}"
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
                warn "Downloaded, but couldn't parse a month from the file — check it opened correctly."
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
                rm -rf "${VENV_DIR}"
                info "Removed ${VENV_DIR}. It will be rebuilt on the next run."
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
echo -e "  ${BOLD}Project:${NC} ${SCRIPT_DIR}"
echo -e "  ${BOLD}Venv:${NC}    ${VENV_DIR}"

# ── Step 1: Which month? ─────────────────────────────────────────────────────
step "Step 1: Which month are we writing the report for?"
echo "  (The well reading for this month will have been taken at the"
echo "   end of the month or early in the following month.)"

CUR_YEAR=$(date +%Y)
DEFAULT=$(date -d "last month" +%Y-%m 2>/dev/null || date -v-1m +%Y-%m 2>/dev/null || date +%Y-%m)

# Month name lookup
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

    # Empty → default
    [ -z "$input" ] && echo "$DEFAULT" && return

    # Already YYYY-MM
    if echo "$input" | grep -qE '^[0-9]{4}-[0-9]{1,2}$'; then
        local y="${input%%-*}" m="${input##*-}"
        printf "%s-%02d" "$y" "$((10#$m))"
        return
    fi

    # Just a number 1-12 → current year
    if echo "$input" | grep -qE '^[0-9]{1,2}$'; then
        local m=$((10#$input))
        if [ "$m" -ge 1 ] && [ "$m" -le 12 ]; then
            printf "%s-%02d" "$CUR_YEAR" "$m"
            return
        fi
    fi

    # Month name, e.g. "May" or "april"
    local mm
    mm=$(month_to_num "$input")
    if [ -n "$mm" ]; then
        printf "%s-%s" "$CUR_YEAR" "$mm"
        return
    fi

    # "May 2026" or "may 26"
    local word1 word2
    word1=$(echo "$input" | awk '{print $1}')
    word2=$(echo "$input" | awk '{print $2}')
    mm=$(month_to_num "$word1")
    if [ -n "$mm" ] && [ -n "$word2" ]; then
        local y="$word2"
        [ ${#y} -eq 2 ] && y="20${y}"
        printf "%s-%s" "$y" "$mm"
        return
    fi

    # Nothing matched
    echo ""
}

TARGET="${1:-}"
if [ -n "$TARGET" ]; then
    TARGET=$(parse_month "$TARGET")
fi

while true; do
    if [ -z "$TARGET" ]; then
        echo -en "  ${YELLOW}?${NC} Enter month [${DEFAULT}]: "
        read -r INPUT
        TARGET=$(parse_month "$INPUT")
    fi

    if echo "$TARGET" | grep -qE '^[0-9]{4}-[0-9]{2}$'; then
        # Extract readable name
        MM_NUM=$((10#${TARGET##*-}))
        MONTH_NAMES=("" "January" "February" "March" "April" "May" "June"
                     "July" "August" "September" "October" "November" "December")
        info "Report month: ${MONTH_NAMES[$MM_NUM]} ${TARGET%%-*} (${TARGET})"
        break
    else
        warn "Didn't understand that. Try: 2026-05, 5, May, or just press Enter for ${DEFAULT}"
        TARGET=""
    fi
done

# ── Step 2: Check Valley data ────────────────────────────────────────────────
step "Step 2: Valley met data"

TARGET_YEAR="${TARGET%%-*}"
TARGET_MM="${TARGET##*-}"
TARGET_MM_NUM=$((10#$TARGET_MM))

if [ ! -f "${VALLEY_FILE}" ]; then
    fail "valleydata.txt not found"
    echo ""
    echo "  Download it from:"
    echo -e "  ${CYAN}${VALLEY_LINK}${NC}"
    echo ""
    echo "  Save it to:"
    echo "  ${VALLEY_FILE}"
    pause_and_exit 1
fi

if grep -qE "^\s+${TARGET_YEAR}\s+${TARGET_MM_NUM}\s" "${VALLEY_FILE}"; then
    info "Valley data has ${TARGET} ✓"
else
    LAST_LINE=$(grep -E '^\s+[0-9]{4}\s+[0-9]+' "${VALLEY_FILE}" | tail -1)
    LAST_Y=$(echo "$LAST_LINE" | awk '{print $1}')
    LAST_M=$(echo "$LAST_LINE" | awk '{printf "%02d", $2}')
    warn "Met Office Valley data for ${TARGET} isn't available yet"
    echo "  (the file currently runs only to ${LAST_Y}-${LAST_M})."
    echo ""
    echo "  The Met Office publishes each month's Valley data on a rolling"
    echo "  basis, usually by the second working day after the month ends."
    echo "  If you're running this report early, ${TARGET}'s figures may"
    echo "  simply not be out yet — please wait until the second working"
    echo "  day after the month ends, then re-run."
    echo ""
    echo "  If it should already be published, fetch the latest file with:"
    echo -e "  ${CYAN}./run_report.sh update${NC}"
    echo "  (or download it manually from)"
    echo -e "  ${CYAN}${VALLEY_LINK}${NC}"
    echo "  and save it to: ${VALLEY_FILE}"
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

if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    fail "Python not found. Install Python 3.10+ from https://www.python.org/downloads/"
    pause_and_exit 1
fi
info "Python: $($PYTHON_CMD --version)"

if [ ! -d "${VENV_DIR}" ]; then
    echo "  Creating virtual environment..."
    $PYTHON_CMD -m venv "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"
info "Venv active"

# Check packages
MISSING=""
for pkg in pandas numpy scipy matplotlib rasterio geopandas fiona pyproj reportlab odfpy; do
    IMPORT_NAME="$pkg"
    [ "$pkg" = "odfpy" ] && IMPORT_NAME="odf"
    python -c "import ${IMPORT_NAME}" 2>/dev/null || MISSING="${MISSING} ${pkg}"
done
if [ -n "$MISSING" ]; then
    warn "Installing:${MISSING}"
    pip install --quiet $MISSING
fi
info "All packages installed"

# ── Step 4: Data files ───────────────────────────────────────────────────────
step "Step 4: Data files"

mkdir -p "${DATA_DIR}" "${KML_DIR}" "${OUTPUT_DIR}"
OK=true

# Wells ODS — auto-detect
WELLS_FILE=""
for f in "${DATA_DIR}"/*.ods; do
    [ -f "$f" ] && WELLS_FILE="$f" && break
done
if [ -n "${WELLS_FILE}" ]; then
    info "Well records: $(basename "${WELLS_FILE}")"
else
    fail "No .ods file found in ${DATA_DIR}/"
    OK=false
fi

[ -f "${COORDS_FILE}" ] && info "Coordinates  ✓" || { fail "Well_locations_height.csv missing"; OK=false; }
[ -f "${DEM_FILE}" ]    && info "DEM          ✓" || warn "DEM missing — no hillshade on maps"
KML_N=$(find "${KML_DIR}" -name "*.kml" 2>/dev/null | wc -l)
[ "$KML_N" -gt 0 ]     && info "KML layers   ✓ (${KML_N} files)" || warn "No KMLs — no site features on maps"
[ -f "${REPORT_SCRIPT}" ] && info "Report script ✓" || { fail "newborough_report.py missing"; OK=false; }

if [ "$OK" = false ]; then
    pause_and_exit 1
fi

# ── Step 5: Generate report ──────────────────────────────────────────────────
MONTH_OUTPUT="${OUTPUT_DIR}/${TARGET%%-*}/${MONTH_NAMES[$MM_NUM]}"
mkdir -p "${MONTH_OUTPUT}"
step "Step 5: Generating ${MONTH_NAMES[$MM_NUM]} ${TARGET%%-*} report"

python "${REPORT_SCRIPT}" "${TARGET}" \
    --wells "${WELLS_FILE}" \
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
