#!/usr/bin/env python3
"""version_header_lint.py — does a shell tool's `# VERSION` header agree with its own changelog? (T-143)

check_all.sh carries its changelog in its leading comment block, in two styles that grew side by side:
`# VERSION N.N.N - date  …` and the indented `#   N.N.N (date): …`. Twice the header was written in one
place only (1.31.0 against a 1.34.0 changelog in 2026-10; 1.2.0 against 1.3.0 in 2026-08). This lint asks the
mechanical question: is the FIRST `# VERSION` line the highest version that the header's changelog names?
Only the leading comment block is read, so a version quoted in a comment further down cannot trip it.

    python3 tools/version_header_lint.py                 # tools/check_all.sh
    python3 tools/version_header_lint.py FILE [FILE…]
    python3 tools/version_header_lint.py --selftest
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-11-24. New (T-143).

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT = ["tools/check_all.sh"]
HEAD = re.compile(r"^# VERSION (\d+\.\d+\.\d+)\b")
ENTRY = re.compile(r"^#\s+(?:VERSION\s+)?(\d+\.\d+\.\d+)\s+(?:-\s+\d{4}-|\(\d{4}-)")


def header_block(text: str) -> list[str]:
    out = []
    for i, line in enumerate(text.splitlines()):
        if i == 0 and line.startswith("#!"):
            continue
        if not line.startswith("#"):
            break
        out.append(line)
    return out


def verdict(text: str) -> tuple[bool, str]:
    block = header_block(text)
    heads = [m.group(1) for m in map(HEAD.match, block) if m]
    if not heads:
        return True, "no # VERSION header (not checked)"
    vers = [m.group(1) for m in map(ENTRY.match, block) if m] + heads
    top = max(vers, key=lambda v: tuple(map(int, v.split("."))))
    return heads[0] == top, f"header {heads[0]}, changelog's highest {top}"


def selftest() -> int:
    good = "#!/bin/bash\n# VERSION 1.3.0 - 2026-01-03  x\n#   1.2.0 (2026-01-02): y\n# VERSION 1.1.0 - 2026-01-01\nrun\n# 9.9.9 (2026-01-09) body\n"
    bad = "#!/bin/bash\n# VERSION 1.2.0 - 2026-01-02  x\n#   1.3.0 (2026-01-03): y\nrun\n"
    ok = verdict(good)[0] and not verdict(bad)[0]
    print(f"  version_header_lint --selftest: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    rc = 0
    for f in (argv[1:] or DEFAULT):
        ok, why = verdict((REPO / f).read_text(encoding="utf-8"))
        print(f"  {'ok  ' if ok else 'FAIL'}  {f}: {why}")
        rc |= 0 if ok else 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
