"""
console_utils.py
================
Shared console-output helpers for the Newborough Warren pipeline.

All scripts should import from this module rather than calling print()
directly for structured output.  Plain print() remains acceptable for
tabular data dumps (e.g. pandas DataFrames) where formatting context is
clear from the surrounding calls.

Colour scheme
-------------
The palette uses ANSI codes via colorama.  On terminals that do not support
colour (e.g. redirected stdout, Windows cmd without VT mode) colorama strips
the codes automatically after init(strip=True is the default on non-TTY
streams).

  CYAN    — script banners and phase headers
  GREEN   — success / saved messages
  YELLOW  — warnings
  RED     — errors and hard failures
  MAGENTA — notes and informational asides
  WHITE   — body text (default)
  DIM     — secondary detail lines

Usage quick-reference
---------------------
  from utils.console_utils import (
      banner, phase, step, info, saved, warn, error, note, done, hr
  )

  banner("03", "State-Space Regression & LCSC")
  phase("1", "Loading inputs")
  step("Fitting cluster-centroid SSMs (lag 0)")
  info(f"Retained {n} wells")
  saved(path.name, extra="66 rows")
  warn("Elevation file not found — maOD outputs skipped")
  error("β₁ < 0 for C3 centroid — hard assertion failed")
  note("Bootstrap seed fixed at 42")
  done("03")
  hr()
"""

from __future__ import annotations

__version__ = "1.0.0"

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Colorama initialisation
# ---------------------------------------------------------------------------
try:
    import colorama
    colorama.init(autoreset=True)
    _C = colorama.Fore
    _S = colorama.Style
    _HAVE_COLOR = True
except ImportError:
    # Graceful degradation: define empty stubs so the rest of the module
    # works without modification.
    class _ForeStub:
        CYAN = GREEN = YELLOW = RED = MAGENTA = WHITE = RESET = ""
    class _StyleStub:
        BRIGHT = DIM = RESET_ALL = ""
    _C = _ForeStub()
    _S = _StyleStub()
    _HAVE_COLOR = False

# ---------------------------------------------------------------------------
# Width constant
# ---------------------------------------------------------------------------
WIDTH = 72  # column width for banners and horizontal rules

# ---------------------------------------------------------------------------
# Low-level colour helpers (kept internal)
# ---------------------------------------------------------------------------

def _cyan(text: str) -> str:
    return f"{_S.BRIGHT}{_C.CYAN}{text}{_S.RESET_ALL}"

def _green(text: str) -> str:
    return f"{_S.BRIGHT}{_C.GREEN}{text}{_S.RESET_ALL}"

def _yellow(text: str) -> str:
    return f"{_S.BRIGHT}{_C.YELLOW}{text}{_S.RESET_ALL}"

def _red(text: str) -> str:
    return f"{_S.BRIGHT}{_C.RED}{text}{_S.RESET_ALL}"

def _magenta(text: str) -> str:
    return f"{_C.MAGENTA}{text}{_S.RESET_ALL}"

def _dim(text: str) -> str:
    return f"{_S.DIM}{text}{_S.RESET_ALL}"

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hr(char: str = "─") -> None:
    """Print a full-width horizontal rule."""
    print(_dim(char * WIDTH))


def banner(script_id: str, title: str, version: str | None = None) -> None:
    """
    Print a prominent script-opening banner.

    Example output:
        ════════════════════════════════════════════════════════════════════════
        SCRIPT 03 — State-Space Regression & LCSC          [v1.1.0]
        ════════════════════════════════════════════════════════════════════════
    """
    bar = "═" * WIDTH
    ver_str = f"  [v{version}]" if version else ""
    label = f"SCRIPT {script_id} — {title}"
    # Pad label + version so the line is WIDTH chars wide (plain text)
    plain_line = f"{label}{ver_str}"
    print()
    print(_cyan(bar))
    print(_cyan(plain_line))
    print(_cyan(bar))


def phase(number: str | int, title: str) -> None:
    """
    Print a phase / section header.

    Example output:
        ── Phase 1 · Loading inputs ─────────────────────────────────────────
    """
    inner = f" Phase {number} · {title} "
    pad = max(0, WIDTH - len(inner) - 3)
    line = f"── {inner}" + "─" * pad
    print()
    print(_cyan(line))


def step(message: str) -> None:
    """
    Print a top-level processing step.

    Example output:
         ▸ Fitting cluster-centroid SSMs (lag 0)
    """
    print(f"  {_cyan('▸')} {message}")


def info(message: str) -> None:
    """
    Print an informational line (neutral, no status icon).

    Example output:
         · Retained 66 wells
    """
    print(f"  {_dim('·')} {message}")


def saved(filename: str | Path, extra: str | None = None) -> None:
    """
    Print a 'file saved' confirmation line.

    Example output:
         ✓ Saved: 03_master_data.csv  (66 rows)
    """
    extra_str = f"  ({extra})" if extra else ""
    print(f"  {_green('✓')} Saved: {_green(str(filename))}{extra_str}")


def warn(message: str) -> None:
    """
    Print a warning.

    Example output:
         ⚠ WARNING: Elevation file not found — maOD outputs skipped
    """
    print(f"  {_yellow('⚠')} {_yellow('WARNING:')} {message}", file=sys.stderr)


def error(message: str) -> None:
    """
    Print an error (does NOT raise; caller decides whether to abort).

    Example output:
         ✗ ERROR: β₁ < 0 for C3 centroid — hard assertion failed
    """
    print(f"  {_red('✗')} {_red('ERROR:')} {message}", file=sys.stderr)


def note(message: str) -> None:
    """
    Print a minor note or aside (dimmed).

    Example output:
         ↳ Bootstrap seed fixed at 42
    """
    print(f"  {_magenta('↳')} {_magenta(message)}")


def skipped(message: str) -> None:
    """
    Print a 'skipped' notice (yellow, lighter than a warning).

    Example output:
         ⊘ SKIPPED: Insufficient data for 2019–2025 trend (n < 4)
    """
    print(f"  {_yellow('⊘')} {_yellow('SKIPPED:')} {message}")


def done(script_id: str | None = None) -> None:
    """
    Print a script-completion footer.

    Example output:
        ────────────────────────────────────────────────────────────────────────
        Done  (Script 03)
    """
    label = f"  (Script {script_id})" if script_id else ""
    print()
    hr()
    print(f"{_green('Done')}{_dim(label)}")
    print()


def result(label: str, value: str) -> None:
    """
    Print a key–value result line.

    Example output:
         • Annual step:  +0.1196 m  (p = 0.012)
    """
    print(f"  {_magenta('•')} {label}: {_S.BRIGHT}{value}{_S.RESET_ALL}")


def table_header(columns: list[str], widths: list[int]) -> None:
    """
    Print a simple fixed-width table header row with an underline.

    Parameters
    ----------
    columns : list of column header strings
    widths  : list of column widths (ints) — must match len(columns)
    """
    row = "  " + "  ".join(f"{col:<{w}}" for col, w in zip(columns, widths))
    underline = "  " + "  ".join("─" * w for w in widths)
    print(_cyan(row))
    print(_dim(underline))
