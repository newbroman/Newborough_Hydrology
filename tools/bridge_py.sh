# tools/bridge_py.sh — the pipeline's Python and pandoc on the desktop bridge.
#
# SOURCE it at the top of every bridge shell call:
#     source tools/bridge_py.sh            (from the repository root)
# then run Python as  nrgpy <script>  and pandoc as  pandoc  (3.1.3).
#
# Why. The bridge sees only the connected folder. venv/bin/python links to the
# uv-managed CPython in ~/.local/share/uv on the L14, which the bridge cannot
# see, and the bridge's own python3 is 3.10 with no scipy. This script keeps a
# uv CPython 3.12.3 and pandoc 3.1.3 INSIDE the connected folder, under
# venv/.bridge/ (gitignored with venv/), and runs that interpreter on the
# venv's own site-packages. The venv's sitecustomize.py applies the BLAS/SIMD
# pin, so fitted numbers match the L14's. First use installs (about 30 s);
# every later session reuses the folder, so nothing is rebuilt.
#
# It also points TMPDIR and uv's caches at /tmp: the bridge's /sessions volume
# (its home folder) is shared with every past bridge session and is full.
#
# On any machine that is not the bridge it does nothing.
#
# Limits that remain (HANDOVER_BOOTSTRAP): one bridge call is capped, and
# background jobs die when the call returns — run the full pipeline natively.
#
# __version__ = "1.1.0"  # Hollingham (2026) — 2026-10-28. python3/python on PATH become the pipeline interpreter
#   (shim in /tmp/nrg_shim, VIRTUAL_ENV exported) so check_all runs on the venv's libraries over the bridge.
# 1.0.0  # Hollingham (2026) — 2026-10-28. First version; replaces
#   the per-session $HOME/nrgpy recipe of 2026-09-04 and the ~/projects/.uv-python
#   one of 2026-08-29 (that folder is not visible when only NRG is connected).

case "$HOME" in
  /sessions/*) ;;
  *) return 0 2>/dev/null || exit 0 ;;
esac

_nrg_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_nrg_b="$_nrg_root/venv/.bridge"
export TMPDIR=/tmp UV_CACHE_DIR=/tmp/uv-cache UV_PYTHON_BIN_DIR=/tmp/uv-bin
export UV_PYTHON_INSTALL_DIR="$_nrg_b/uv-python"
export NRG_PY_VERSION=3.12.3
export NRG_SITE="$_nrg_root/venv/lib/python3.12/site-packages"

_nrg_py="$(uv python find "$NRG_PY_VERSION" --no-project 2>/dev/null | grep "^$UV_PYTHON_INSTALL_DIR" )"
if [ -z "$_nrg_py" ]; then
  echo "bridge_py: installing CPython $NRG_PY_VERSION into venv/.bridge (once)" >&2
  mkdir -p "$UV_PYTHON_INSTALL_DIR"
  uv python install "$NRG_PY_VERSION" 2>&1 | tail -1 >&2
  _nrg_py="$(uv python find "$NRG_PY_VERSION" --no-project 2>/dev/null | grep "^$UV_PYTHON_INSTALL_DIR")"
fi

_nrg_pd="$_nrg_b/pandoc-3.1.3/bin"
if [ ! -x "$_nrg_pd/pandoc" ]; then
  echo "bridge_py: fetching pandoc 3.1.3 into venv/.bridge (once)" >&2
  curl -sSL -o /tmp/pandoc-3.1.3.tar.gz \
    https://github.com/jgm/pandoc/releases/download/3.1.3/pandoc-3.1.3-linux-amd64.tar.gz \
  && tar xzf /tmp/pandoc-3.1.3.tar.gz -C /tmp 2>/dev/null
  mkdir -p "$_nrg_pd" && cp /tmp/pandoc-3.1.3/bin/pandoc "$_nrg_pd/"
fi
export PATH="$_nrg_pd:$PATH"

if [ -n "$_nrg_py" ]; then
  export NRG_PY="$_nrg_py"
  nrgpy() { PYTHONPATH="$NRG_SITE${PYTHONPATH:+:$PYTHONPATH}" "$NRG_PY" "$@"; }
  export -f nrgpy
  # 1.1.0: a shim so a plain `python3` (check_all, nrg_git, any tool) is the pipeline's interpreter too.
  # check_all leaves an active VIRTUAL_ENV alone, so exporting it here stops it activating the venv,
  # whose bin/python links outside what the bridge can see.
  mkdir -p /tmp/nrg_shim/bin
  for _n in python3 python; do
    printf '#!/bin/sh\nPYTHONPATH="%s${PYTHONPATH:+:$PYTHONPATH}" exec "%s" "$@"\n' "$NRG_SITE" "$NRG_PY" > "/tmp/nrg_shim/bin/$_n"
    chmod +x "/tmp/nrg_shim/bin/$_n"
  done
  export VIRTUAL_ENV=/tmp/nrg_shim
  case ":$PATH:" in *":/tmp/nrg_shim/bin:"*) ;; *) export PATH="/tmp/nrg_shim/bin:$PATH" ;; esac
else
  echo "bridge_py: WARNING — no CPython $NRG_PY_VERSION; nrgpy not defined" >&2
fi
unset _nrg_root _nrg_b _nrg_py _nrg_pd
