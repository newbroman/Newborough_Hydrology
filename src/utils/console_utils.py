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

__version__ = "1.2.1"  # 2026-09-23: durations under two minutes print in seconds —
#   "0m elapsed, ~0m left" over a 40 s loop said nothing (seen on Script 32).
# 1.2.0  # 2026-09-23: track() — wrap any loop in one word and get
#   progress() for free, so the twelve scripts that run past 30 s can show they are
#   running (Martin, 2026-09-23). The bar ends its own line when the loop ends.
# 1.1.0  # 2026-09-15: progress() — Martin's rule that a long run
#   must show it is running (CLAUDE.md "SHOW PROGRESS"). Additive; nothing else changed.

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


def _span(seconds: float) -> str:
    """A duration for a progress line: seconds below two minutes, else minutes.
    A 40-second loop that reads "0m elapsed, ~0m left" says nothing (1.2.1)."""
    if seconds < 120:
        return f"{seconds:.0f} s"
    return f"{seconds / 60:.0f} min"


def progress(n: int, total: int, label: str = "", started: float | None = None,
             width: int = 30) -> None:
    """
    One-line, in-place completion bar with elapsed and remaining time.

    Martin's rule (2026-09-15): anything he is handed to run must show that it is
    running. Call once per unit of work; prints a carriage-return line, so the
    caller should `print()` once after the loop to end it. `started` is the
    `time.time()` at the loop's start; without it only the count is shown.

    Example output:
         [##########....................]  37 %  112/298  2019-07-29  4m elapsed, ~7m left
    """
    import time                                               # noqa: PLC0415
    n = max(0, min(n, total))
    fill = int(width * n / total) if total else width
    bar = "#" * fill + "." * (width - fill)
    pct = 100.0 * n / total if total else 100.0
    timing = ""
    if started is not None and n > 0:
        el = time.time() - started
        eta = el / n * (total - n)
        timing = f"  {_span(el)} elapsed, ~{_span(eta)} left"
    sys.stdout.write(f"\r  [{bar}] {pct:3.0f} %  {n}/{total}  {label}{timing}   ")
    sys.stdout.flush()


def track(items, label: str = "", total: int | None = None, min_seconds: float = 0.0,
          lines: bool = False):
    """
    Iterate `items`, reporting completion after each one.

    Default: the in-place progress() bar, ended with a newline when the loop
    finishes. `lines=True` prints one full line per item instead — use it when
    the loop body prints its own output (a "Saved:" per figure, say), which
    would otherwise overwrite the bar mid-line:
        [ 24 %   4/17   0m elapsed, ~1m left ]  Figure 2b — ridge hillslope gradient

    `total` is needed for a generator; `min_seconds` suppresses the report for
    loops that finish faster than that, so a two-second step on one machine does
    not shout on another. The label can be a callable of the current item.

        for name, build in track(figures, lambda f: f[0], lines=True):
            build()
    """
    import time                                               # noqa: PLC0415
    seq = list(items) if total is None else items
    n_total = total if total is not None else len(seq)
    started = time.time()
    shown = False
    for i, item in enumerate(seq, 1):
        yield item
        if not shown and time.time() - started < min_seconds and i < n_total:
            continue
        shown = True
        text = label(item) if callable(label) else label
        if lines:
            el = time.time() - started
            eta = el / i * (n_total - i)
            print(f"  [{100.0 * i / n_total:3.0f} %  {i:3d}/{n_total}  "
                  f"{_span(el)} elapsed, ~{_span(eta)} left ]  {text}")
        else:
            progress(i, n_total, text, started)
    if shown and not lines:
        sys.stdout.write("\n")
        sys.stdout.flush()


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
