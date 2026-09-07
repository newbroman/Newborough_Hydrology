#!/usr/bin/env python3
"""
ms_chapters — does every registered pipeline step have a Methods Supplement chapter
and a SCRIPT_LEDGER row? (D-144 §4, the S2 refusal.)

Why this exists.

  The Methods Supplement documents the pipeline script by script. Keeping it in step
  was a rule in prose ("every code change ... updates its row"; "add the chapter"),
  and prose rules are the ones that get forgotten: Script 40 sat registered without a
  chapter until W116 noticed, and Script 43 was registered on 2026-09-06 with its
  chapter owed. D-144 makes it a refusal: `run_analysis.py` will not register a step
  whose script has no chapter mapping or no ledger row, and `check_all` runs the same
  check so the gate reads red before the pipeline does.

How a chapter is found — derived, never typed.

  The MS mirror's `##` and `###` headings name their scripts ("S.5 Scripts 07, 08",
  "S.6 Script 09 suite (a--e)", "S.9.3 Script 11c", "S.23b Script 43"). Those are
  parsed; nothing is hand-listed, so a heading renumber cannot desynchronise the map.
  The one script documented outside a heading (Script 27, Appendix A) is declared in
  `tools/ms_chapters_extra.csv` with the heading text that must exist in the mirror —
  an exception that is itself checked, not a bypass.

Usage:
    python3 tools/ms_chapters.py             # report; exit 1 if any step is unmapped
    python3 tools/ms_chapters.py --selftest
    from ms_chapters import unmapped_steps   # what run_analysis calls at registration
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-07. First issue (D-144 §4).

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MS_MIRROR = REPO / "docs" / "report" / "text" / "Newborough_Methods_Supplement.md"
EXTRA = REPO / "tools" / "ms_chapters_extra.csv"
LEDGER = REPO / "notes" / "ledgers" / "SCRIPT_LEDGER.md"

_ANCHOR = re.compile(r"\[\]\{#[^}]*\}")
_LIST = re.compile(r"Scripts?\s+([0-9][0-9a-z]*(?:\s*,\s*[0-9][0-9a-z]*)*)")
_SUITE = re.compile(r"Script (\d\d) suite \((\w)--(\w)\)")
_KEY = re.compile(r"(?:run_)?(\d{1,2}[a-z]?)_")


def script_key(script: str) -> str | None:
    """'43_ranwell_sites.py' -> '43'; '10a_ancova_baci.py' -> '10a'; '09f_...' -> '09f'."""
    m = _KEY.match(Path(script).name)
    return m.group(1) if m else None


def _norm(k: str) -> str:
    """'9' and '09' are the same script key; letters kept."""
    m = re.match(r"(\d+)([a-z]?)$", k)
    return f"{int(m.group(1)):02d}{m.group(2)}" if m else k


def chapter_map(text: str | None = None) -> dict[str, str]:
    """{normalised script key: heading} from the MS mirror's ## and ### headings,
    plus the declared extras. First heading naming a key wins."""
    if text is None:
        text = MS_MIRROR.read_text(encoding="utf-8") if MS_MIRROR.is_file() else ""
    out: dict[str, str] = {}
    for line in text.splitlines():
        if not (line.startswith("## ") or line.startswith("### ")):
            continue
        h = _ANCHOR.sub("", line).lstrip("# ").strip()
        keys = set()
        for mo in _LIST.finditer(h):
            keys.update(re.split(r"\s*,\s*", mo.group(1)))
        for mo in _SUITE.finditer(h):
            keys.update(mo.group(1) + chr(c)
                        for c in range(ord(mo.group(2)), ord(mo.group(3)) + 1))
        for k in keys:
            out.setdefault(_norm(k), h)
    if EXTRA.is_file():
        with EXTRA.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                k, heading = row["script_key"].strip(), row["heading_text"].strip()
                if heading and heading in text:          # the exception must still resolve
                    out.setdefault(_norm(k), heading)
    return out


def ledger_scripts() -> set[str]:
    """Script filenames that have a SCRIPT_LEDGER row, plus the ones the ledger itself
    declares are not rows ("Not rows: ... — utility/orchestration", the sub-runners) —
    read through ledger_lint's own parser so the two tools cannot disagree."""
    if not LEDGER.is_file():
        return set()
    text = LEDGER.read_text(encoding="utf-8")
    sys.path.insert(0, str(REPO / "tools"))
    from ledger_lint import declared_exemptions, ALWAYS_EXEMPT
    out = set(declared_exemptions(text)) | set(ALWAYS_EXEMPT)
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 8 and cells[1].endswith(".py"):
            out.add(cells[1])
    return out


def unmapped_steps(scripts, text: str | None = None,
                   ledger: set[str] | None = None) -> list[tuple[str, str]]:
    """[(script, what is missing)] for every registered script lacking a chapter
    heading or a ledger row. Empty list = registration may proceed."""
    cmap = chapter_map(text)
    led = ledger_scripts() if ledger is None else ledger
    faults = []
    for s in scripts:
        name = Path(s).name
        k = script_key(name)
        missing = []
        if k is None or _norm(k) not in cmap:
            missing.append("no Methods Supplement chapter heading names it")
        if name not in led:
            missing.append("no SCRIPT_LEDGER row")
        if missing:
            faults.append((name, "; ".join(missing)))
    return faults


def _registered_scripts() -> list[str]:
    import json
    man = REPO / "outputs" / "pipeline_manifest.json"
    if not man.is_file():
        return []
    return [s["script"] for s in json.loads(man.read_text(encoding="utf-8")).get("steps", [])]


def selftest() -> int:
    bad = []
    md = ("## S.5 Scripts 07, 08 --- maps\n## S.6 Script 09 suite (a--e) --- scrape\n"
          "### S.9.3 Script 11c --- map\n## S.23b Script 43 --- Ranwell\n")
    cm = chapter_map(md)
    for k in ("07", "08", "09a", "09e", "11c", "43"):
        if k not in cm:
            bad.append(f"chapter_map missed {k}")
    if "09f" in cm:
        bad.append("suite range over-extended")
    led = {"07_x.py", "43_ranwell_sites.py"}
    u = dict(unmapped_steps(["07_x.py", "43_ranwell_sites.py", "44_new.py", "08_y.py"], md, led))
    if "07_x.py" in u or "43_ranwell_sites.py" in u:
        bad.append("mapped script reported unmapped")
    if "44_new.py" not in u or "chapter" not in u["44_new.py"] or "SCRIPT_LEDGER" not in u["44_new.py"]:
        bad.append("new script not refused on both counts")
    if "08_y.py" not in u or "SCRIPT_LEDGER" not in u["08_y.py"]:
        bad.append("ledger-less script not refused")
    if script_key("run_10_clearfell.py") != "10" or script_key("09f_management_effects.py") != "09f":
        bad.append("script_key")
    if bad:
        print("ms_chapters --selftest: FAIL")
        for b in bad:
            print(f"    - {b}")
        return 1
    print("ms_chapters --selftest: OK")
    return 0


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()
    scripts = _registered_scripts()
    if not scripts:
        print("ms_chapters: no committed manifest — nothing to check")
        return 0
    faults = unmapped_steps(scripts)
    print(f"  {len(scripts)} registered steps, {len(scripts) - len(faults)} with a Methods "
          f"Supplement chapter and a ledger row")
    if faults:
        print("ms_chapters: FAULT — a registered step is undocumented (D-144 §4)")
        for s, why in faults:
            print(f"    - {s}: {why}")
        return 1
    print("ms_chapters: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
