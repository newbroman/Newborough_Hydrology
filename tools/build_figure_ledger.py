#!/usr/bin/env python3
"""
build_figure_ledger.py — the figure ledger, derived from figure_map captions.

WHY

  v1 seeded the ledger from tools/figure_table_manifest.csv, a hand-maintained
  file that went stale the instant a figure was renumbered.

  The authoritative source is the figure's own caption. Every report figure
  caption ends with a marker naming the file that produced it, e.g.
  "(Source: 41_05_canopy_trajectory.png)" (Martin, 2026-09-07). figure_map.py
  parses that marker (caption_source) and resolves it on disk, so the whole
  ledger — global number, section, caption title AND source PNG — is derived
  live from the ODTs, current by construction, with no side registry to lag.
  A figure whose caption carries no resolvable marker is listed and FLAGGED,
  not dropped, so a genuine gap shows up rather than being silently wrong.

  figure_map covers the report master (report7-16), which carries the captioned
  Source: markers; the papers, Methods Supplement and academic summary caption
  their figures without such markers and are not listed here.

  Regenerate with: python3 tools/build_figure_ledger.py

CHANGELOG
  2.2.0  2026-09-07  Pure caption-derived; figure_table_sources.csv retired for
                     figures (its Figure rows removed), so the registry appendix
                     is gone.
  2.1.0  2026-09-07  Source column from the caption Source: marker via
                     figure_map.caption_source.
  2.0.0  2026-09-07  Rederive the list from figure_map (live).
  1.0.0             Seeded from figure_table_manifest.csv.
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

__version__ = "2.2.0"

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import figure_map as fm                                          # noqa: E402

DEFAULT_OUT = REPO / "notes" / "ledgers" / "FIGURE_LEDGER.md"

_TITLE = re.compile(r"\s*Figure\s+[\d.]+[ab]?\s*:\s*(.*)", re.I)

BANNER = (
    "<!-- GENERATED LEDGER — do not edit.\n"
    "     Regenerate with: python3 tools/build_figure_ledger.py -->"
)


def build() -> str:
    rows = fm.build()                       # live: number..caption, source

    docs: list[str] = []
    by_doc: dict[str, list[dict]] = {}
    for r in rows:
        d = r["document"]
        if d not in by_doc:
            by_doc[d] = []
            docs.append(d)
        by_doc[d].append(r)

    n_total = len(rows)
    n_resolved = 0
    flagged: list[int] = []

    out = [BANNER, "",
           "# FIGURE_LEDGER — figures by document, number, section and source",
           "",
           "*Derived live from `tools/figure_map.py`: the Source column is each "
           "figure's caption `Source:` marker, resolved on disk. Regenerate, do "
           "not hand-edit.*",
           ""]

    body: list[str] = []
    for d in docs:
        body.append(f"## {d}")
        body.append("")
        body.append("| Fig. | § | Caption | Source | On disk |")
        body.append("|---|---|---|---|---|")
        for r in by_doc[d]:
            gnum = r["number"]
            cap = r["caption"]
            mt = _TITLE.match(cap)
            title = (mt.group(1) if mt else cap).replace("|", "\\|").strip()[:70]
            src = (r.get("source") or "").strip()
            if src:
                n_resolved += 1
                srccell = f"`{src}`"
                disk = "yes"
            else:
                srccell = "*no source marker*"
                disk = "—"
                flagged.append(int(gnum))
            body.append(f"| {gnum} | {r['section']} | {title} | {srccell} | {disk} |")
        body.append("")

    n_flag = len(flagged)
    out.append(f"**{n_total} report figures** across {len(docs)} documents — "
               f"{n_resolved} resolve to a source on disk, "
               f"{n_flag} flagged"
               + (f" (numbers: {', '.join(map(str, sorted(flagged)))})"
                  if flagged else "") + ".")
    out.append("")
    if flagged:
        out.append("*Flagged = the caption carries no resolvable `Source:` "
                   "marker. Add one to the figure's caption in the ODT.*")
        out.append("")
    out.extend(body)

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    out.append(f"*Generated {stamp} by `tools/build_figure_ledger.py` "
               f"v{__version__}.*")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stdout", action="store_true", help="print, write nothing")
    ap.add_argument("--out", help="write somewhere other than the default")
    a = ap.parse_args()
    text = build()
    if a.stdout:
        print(text)
        return 0
    dest = pathlib.Path(a.out) if a.out else DEFAULT_OUT
    dest.write_text(text, encoding="utf-8")
    print(f"wrote {dest.relative_to(REPO)}: {text.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
