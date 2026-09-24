#!/usr/bin/env python3
"""freeze_requirements.py — keep requirements.txt equal to the venv.

`requirements.txt` is the venv's full freeze (D-093: venv/ IS the environment).
It has drifted twice: on 2026-09-17 a whole-file sort scrambled its header, and
by 2026-09-24 it held 52 of the 94 packages installed — everything added for
the film (Scripts 45/47), the Sentinel tools and the capture tools had been
`pip install`ed and never pinned. `env_audit` compares the record against the
pins but probes only the fifteen libraries the pipeline imports directly, so
neither fault was visible to any gate.

    python3 tools/freeze_requirements.py --check    # pins == venv?  (check_all)
    python3 tools/freeze_requirements.py --write    # rewrite the pins from the venv

The pins are read from the venv's `*.dist-info` directories, not from `pip
freeze`, so the check runs wherever venv/ is on disk — the publishing machine
and the bridge mount alike — and needs no subprocess. Where there is no venv/
(a cloud clone) the check reports that and passes: it cannot say anything about
an environment it cannot see. `pip` itself is never pinned. --write keeps the
header above the `--- the pinned list ---` line untouched and the existing
spelling of any pin already present (adjustText, ImageIO); it sorts only the
pins, case-insensitively.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-09-24. Martin: "the requirements list needs updating"

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO / "requirements.txt"
VENV = REPO / "venv"
MARKER = "# --- the pinned list ---\n"
EXCLUDE = {"pip"}


def _norm(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def site_packages() -> Path | None:
    hits = sorted(VENV.glob("lib/python3.*/site-packages"))
    return hits[-1] if hits else None


def venv_pins(sp: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for d in sp.iterdir():
        m = re.match(r"(.+?)-([0-9][^-]*)\.dist-info$", d.name)
        if m and _norm(m.group(1)) not in EXCLUDE:
            out[_norm(m.group(1))] = m.group(2)
    return out


def file_pins(text: str) -> tuple[str, dict[str, tuple[str, str]]]:
    """(header, {normalised name: (spelling, version)})."""
    head, sep, body = text.partition(MARKER)
    if not sep:
        raise SystemExit(f"requirements.txt has no '{MARKER.strip()}' line — "
                         "the header and the pins cannot be told apart")
    pins: dict[str, tuple[str, str]] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, _, ver = line.partition("==")
        pins[_norm(name)] = (name.strip(), ver.strip())
    return head + MARKER, pins


def diff(venv: dict[str, str], pins: dict[str, tuple[str, str]]) -> list[str]:
    out = []
    for n in sorted(set(venv) | set(pins)):
        if n not in pins:
            out.append(f"  installed, not pinned : {n}=={venv[n]}")
        elif n not in venv:
            out.append(f"  pinned, not installed : {pins[n][0]}=={pins[n][1]}")
        elif venv[n] != pins[n][1]:
            out.append(f"  version differs       : {n} venv {venv[n]} / pinned {pins[n][1]}")
    return out


def render(header: str, venv: dict[str, str], pins: dict[str, tuple[str, str]]) -> str:
    lines = []
    for n in sorted(venv, key=str.lower):
        spelling = pins[n][0] if n in pins else n
        lines.append(f"{spelling}=={venv[n]}")
    return header + "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="fail if the pins differ from the venv")
    g.add_argument("--write", action="store_true", help="rewrite the pins from the venv")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    sp = site_packages()
    if sp is None:
        print("  freeze_requirements: no venv/ here — nothing to compare (not this machine)")
        return 0
    text = REQUIREMENTS.read_text(encoding="utf-8")
    header, pins = file_pins(text)
    venv = venv_pins(sp)
    delta = diff(venv, pins)

    if a.write:
        REQUIREMENTS.write_text(render(header, venv, pins), encoding="utf-8")
        print(f"  freeze_requirements: wrote {len(venv)} pins from {sp.relative_to(REPO)}"
              + (f" ({len(delta)} change(s))" if delta else " (no change)"))
        return 0

    if delta:
        print(f"  freeze_requirements: requirements.txt disagrees with venv/ "
              f"({len(delta)} line(s)):")
        for line in delta[:40]:
            print(line)
        if len(delta) > 40:
            print(f"  … {len(delta) - 40} more")
        print("  (run python3 tools/freeze_requirements.py --write on the publishing machine)")
        return 1
    if not a.quiet:
        print(f"  freeze_requirements: {len(venv)} pins match venv/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
