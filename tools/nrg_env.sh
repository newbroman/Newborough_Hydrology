#!/usr/bin/env bash
# nrg_env.sh — build the pipeline's environment on THIS machine (D-227).
#
# The pipeline's machine is not a host. It is a pinned environment, and any machine that builds
# it produces the same numbers:
#
#   Python      the version in tools/environment.json, installed by uv (NOT the OS's python,
#               so an OS upgrade - Mint, or anything else - cannot move it)
#   libraries   requirements.txt, the full freeze of the venv every published number came from
#   externals   pandoc, pdftotext, soffice, git at the recorded versions (checked; pandoc is
#               installed from its release tarball into ~/bin if it is absent or wrong)
#   BLAS        OPENBLAS_CORETYPE and the thread counts from environment.json's `blas` block,
#               written into the venv's sitecustomize.py so every interpreter started from the
#               venv - run_analysis.py, each script it launches, every tool - loads OpenBLAS with
#               the same kernel. Without the pin OpenBLAS picks kernels per CPU and the last
#               digits move between machines (measured 2026-10-01: Step 03 to 1.2e-10).
#
# Usage:
#   bash tools/nrg_env.sh            # build venv/ if absent, else sync it to requirements.txt
#   bash tools/nrg_env.sh --rebuild  # move venv/ aside and build it from scratch
#   bash tools/nrg_env.sh --system   # FIRST, on a new machine (needs sudo): the system tools
#                                    # (git, rclone, LibreOffice + python3-uno, poppler-utils),
#                                    # then a LibreOffice version check against the record
#
# The two halves are different in kind. Everything under venv/ - Python itself, every library,
# the BLAS/SIMD pin - is pinned and rebuilt identically anywhere, so an OS upgrade cannot move a
# published NUMBER. LibreOffice is a system package: the OS decides its version, and it decides
# the bytes of every published PDF (artefact_lint compares each PDF's Producer with the record).
# --system therefore checks it and, when it matches, offers to hold it against upgrades.
#
# Prints a step line as it goes and ends with tools/env_audit.py's verdict.
#
# Version 1.1.0 — Hollingham (2026) — 2026-10-02. --system: installs the apt tools the pipeline
#   shells out to and compares LibreOffice with the record (hold it, or build PDFs elsewhere).
# 1.0.0 — 2026-10-02 (D-227). First issue.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
REC="tools/environment.json"
step() { printf '  [%s] %s\n' "$1" "$2"; }

# ── --system: the OS-level tools (run once per machine, before the rest) ─────────
if [ "${1:-}" = "--system" ]; then
  REC_LO="$(python3 -c "import json;print(json.load(open('$REC'))['externals']['soffice'])")"
  PKGS="git rclone libreoffice python3-uno poppler-utils curl"
  step "sys" "apt packages: $PKGS"
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO apt-get update -qq && $SUDO apt-get install -y -qq $PKGS >/dev/null
  have_lo="$(soffice --version 2>/dev/null | head -1 | awk '{print $2}')"
  if [ "$have_lo" = "$REC_LO" ]; then
    step "sys" "LibreOffice $have_lo = the recorded version: published PDFs can be built here"
    held="$(apt-mark showhold 2>/dev/null | grep -c '^libreoffice' || true)"
    if [ "$held" = "0" ]; then
      echo "      It is NOT held, so the next system update may replace it. To hold it:"
      echo "        sudo apt-mark hold \$(dpkg -l 'libreoffice*' 'python3-uno' | awk '/^ii/{print \$2}')"
      echo "      and to release it later: the same with 'unhold'."
    else
      echo "      Held against upgrades ($held LibreOffice package(s))."
    fi
  else
    step "sys" "LibreOffice ${have_lo:-ABSENT}, recorded $REC_LO — PDFs built here would be REFUSED"
    echo "      (artefact_lint checks each published PDF's Producer). Either build PDFs in a cloud"
    echo "      session (tools/cloud_setup.sh; its image carries $REC_LO), or move the whole project"
    echo "      to the new version deliberately: rebuild every published PDF on it, then"
    echo "      'venv/bin/python tools/env_audit.py --record' — a decision-log entry, not a quiet fix."
  fi
  for t in git rclone pdftotext; do command -v "$t" >/dev/null || echo "      MISSING: $t"; done
  echo
  echo "  Now build the Python side:  bash tools/nrg_env.sh"
  exit 0
fi

PY_VER="$(python3 -c "import json;print(json.load(open('$REC'))['python']['version'])")"
read -r PANDOC_VER < <(python3 -c "import json;print(json.load(open('$REC'))['externals']['pandoc'])")

# ── 1/5 uv ─────────────────────────────────────────────────────────────────────
if ! command -v uv >/dev/null 2>&1; then
  step "1/5" "installing uv (user-level)"
  python3 -m pip install --user --quiet uv 2>/dev/null \
    || curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
step "1/5" "uv $(uv --version | awk '{print $2}')"

# ── 2/5 python ─────────────────────────────────────────────────────────────────
step "2/5" "python $PY_VER (uv-managed)"
uv python install "$PY_VER" >/dev/null
if [ "${1:-}" = "--rebuild" ] && [ -d venv ]; then
  mkdir -p _to_delete
  mv venv "_to_delete/venv.$(date +%Y%m%d%H%M%S)"       # a move, not rm: the bridge mount refuses unlink
fi
if [ ! -x venv/bin/python ] || [ "$(venv/bin/python -c 'import platform;print(platform.python_version())')" != "$PY_VER" ]; then
  [ -d venv ] && { mkdir -p _to_delete; mv venv "_to_delete/venv.$(date +%Y%m%d%H%M%S)"; }
  uv venv --quiet --python "$PY_VER" venv
fi

# ── 3/5 libraries ──────────────────────────────────────────────────────────────
step "3/5" "libraries from requirements.txt"
uv pip install --quiet --python venv/bin/python -r requirements.txt

# ── 4/5 the BLAS pin ───────────────────────────────────────────────────────────
SITE="$(venv/bin/python -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])')"
venv/bin/python - "$REC" "$SITE/sitecustomize.py" <<'PY'
import json, sys
rec, out = sys.argv[1], sys.argv[2]
pins = {k: v for k, v in json.load(open(rec))["blas"].items() if k != "kernel"}
lines = ['"""Written by tools/nrg_env.sh (D-227): pin the BLAS kernel and threading before numpy',
         'loads OpenBLAS, so every machine that builds this environment computes the same digits.',
         'Values from tools/environment.json `blas`. An explicit setting in the shell still wins."""',
         "import os"]
lines += [f"os.environ.setdefault({k!r}, {v!r})" for k, v in sorted(pins.items())]
open(out, "w").write("\n".join(lines) + "\n")
PY
step "4/5" "BLAS/SIMD pin: $(venv/bin/python - "$REC" <<'PY'
import json, os, sys
keys = [k for k in json.load(open(sys.argv[1]))["blas"] if k != "kernel"]
print(", ".join(f"{k}={os.environ.get(k)}" for k in sorted(keys)))
PY
)"

# ── 5/5 externals ──────────────────────────────────────────────────────────────
have_pandoc="$(pandoc --version 2>/dev/null | head -1 | awk '{print $2}' || true)"
if [ "$have_pandoc" != "$PANDOC_VER" ]; then
  if [ -x "$HOME/bin/pandoc" ] && [ "$("$HOME/bin/pandoc" --version | head -1 | awk '{print $2}')" = "$PANDOC_VER" ]; then
    :
  else
    step "5/5" "installing pandoc $PANDOC_VER into ~/bin"
    tmp="$(mktemp -d)"
    curl -sSL -o "$tmp/p.tgz" "https://github.com/jgm/pandoc/releases/download/$PANDOC_VER/pandoc-$PANDOC_VER-linux-amd64.tar.gz"
    tar xzf "$tmp/p.tgz" -C "$tmp" && mkdir -p "$HOME/bin" && cp "$tmp/pandoc-$PANDOC_VER/bin/pandoc" "$HOME/bin/"
  fi
  export PATH="$HOME/bin:$PATH"
  echo "      add to your shell profile:  export PATH=\"\$HOME/bin:\$PATH\""
fi
step "5/5" "externals: pandoc $(pandoc --version | head -1 | awk '{print $2}'), $(soffice --version 2>/dev/null | head -1 | awk '{print "soffice "$2}' || echo 'soffice ABSENT'), $(pdftotext -v 2>&1 | head -1 | awk '{print "pdftotext "$3}')"

echo
venv/bin/python tools/env_audit.py
echo
echo "  Activate with:  source $ROOT/venv/bin/activate"
