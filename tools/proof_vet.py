#!/usr/bin/env python3
"""
proof_vet.py
============
Record Martin's verdict on a number in the proof copy so it STAYS recorded.

Why this exists.

  Martin, 2026-09-21: "I'm sure I have vetted all the values in the abstract
  before. This task is going to take forever if I keep having to go back and
  check values." Until now a queue item he sent ("n is the sample size of the
  C5 coastal retreat analysis") was acted on in the chat and then forgotten:
  the next proof bundle re-derived every verdict from the matcher, and a number
  the matcher cannot trace came back red however many times he had read it.

  tools/proof_reading_verdicts.csv is the durable store (the reading pass's
  verdicts live there too). This tool adds a `vetted` row keyed the way
  proof_copy keys a number — a hash of the number, its sentence and its offset
  — so the verdict holds exactly as long as the number and its sentence do. A
  changed value, or a rewritten sentence, is a new id and comes back red on
  its own; nothing Martin vetted can go stale silently.

What it takes.

  Queue items as proof_copy's page stores them (doc, value, context, note),
  either as a directory of JSON documents exported from the artifact store
  (`--store DIR`) or as the pasted "PROOF CORRECTIONS" block (`--text FILE`).
  Each item is located in the current mirror by its value and context; the
  number's reading id is computed; a `vetted` row is written with Martin's note
  as the reason. Items the mirror no longer contains (the sentence was rewritten
  since) are reported and skipped — the rewrite is the fix.

Usage:
    python3 tools/proof_vet.py --store scratch/queue/corrections            # every item
    python3 tools/proof_vet.py --store scratch/queue/corrections --only ID  # some of them
    python3 tools/proof_vet.py --text scratch/queue/pasted.txt
    python3 tools/proof_vet.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import pathlib
import re
import sys

__version__ = "1.0.0"  # Hollingham (2026) — 2026-09-21. Vetted verdicts persist.

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import proof_copy as pc  # noqa: E402

VERDICTS = REPO / "tools" / "proof_reading_verdicts.csv"
FIELDS = ["id", "verdict", "reason", "better", "batch", "attribution_read"]
_PASTED = re.compile(r"^- \[(?P<doc>\w+) §[^\]]*\] \"(?P<value>[^\"]+)\" → [^\n]*? — (?P<note>[^\n]*)\n\s+context: (?P<context>.*)$", re.M)


def locate(text: str, value: str, context: str) -> tuple[int, int] | None:
    """(start, end) of `value` inside the occurrence of `context` in the mirror.
    The context is the page's window around the number, ellipses at its ends."""
    ctx = context.strip().strip("…").strip()
    ctx = pc.mask_markup(ctx) if hasattr(pc, "mask_markup") else ctx
    masked = pc.mask_markup(text)
    # the page quotes the mirror's text with markdown stripped; match on the
    # normalised alphanumerics of the context's two halves around the number
    i = masked.find(ctx)
    if i < 0:
        # fall back: the longest run of the context either side of the value
        head, _, tail = ctx.partition(value)
        head, tail = head[-40:], tail[:40]
        for m in re.finditer(re.escape(value), masked):
            if head and masked[max(0, m.start() - len(head)):m.start()] != head:
                continue
            if tail and masked[m.end():m.end() + len(tail)] != tail:
                continue
            return m.start(), m.end()
        return None
    j = masked.find(value, i)
    if j < 0 or j > i + len(ctx):
        return None
    return j, j + len(value)


def reading_id(doc: str, text: str, s: int, e: int) -> str:
    masked = pc.mask_markup(text)
    sent_full = " ".join(pc._sentence(masked, s, e, full=True).split())
    return f"{doc}:{pc._reading_id(text[s:e], sent_full, s - masked.rfind(chr(10), 0, s))}"


def items_from_store(d: pathlib.Path) -> list[dict]:
    out = []
    for f in sorted(d.glob("*.json")):
        j = json.loads(f.read_text(encoding="utf8"))
        j["_id"] = f.stem
        out.append(j)
    return out


def items_from_text(p: pathlib.Path) -> list[dict]:
    return [dict(doc=m.group("doc"), value=m.group("value"), note=m.group("note"), context=m.group("context"), _id=f"paste{i}")
            for i, m in enumerate(_PASTED.finditer(p.read_text(encoding="utf8")))]


def vet(items: list[dict], batch: str, only: set[str] | None = None, write: bool = True) -> tuple[list[str], list[str]]:
    existing = {}
    if VERDICTS.exists():
        with VERDICTS.open(encoding="utf8", newline="") as fh:
            existing = {r["id"]: r for r in csv.DictReader(fh)}
    added, skipped = [], []
    texts = {}
    for it in items:
        if only and it["_id"] not in only:
            continue
        doc = it["doc"]
        if doc not in texts:
            texts[doc] = pc.resolve_doc(doc).read_text(encoding="utf8")
        span = locate(texts[doc], str(it["value"]), it.get("context", ""))
        if span is None:
            skipped.append(f"{it['_id']} {doc} {it['value']!r}: not found in the current mirror (sentence rewritten?)")
            continue
        rid = reading_id(doc, texts[doc], *span)
        note = (it.get("note") or "").strip() or "vetted"
        existing[rid] = {"id": rid, "verdict": "vetted", "reason": note, "better": "", "batch": batch, "attribution_read": ""}
        added.append(f"{rid}  {doc} {it['value']!r} — {note[:60]}")
    if write and added:
        with VERDICTS.open("w", encoding="utf8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(existing.values())
    return added, skipped


def selftest() -> bool:
    text = "# T\n\nThe network has 66 wells (n = 3 in the subset; see Section 4). Another sentence.\n"
    span = locate(text, "3", "…network has 66 wells (n = 3 in the subset; see Sec…")
    ok = span is not None and text[span[0]:span[1]] == "3"
    rid1 = reading_id("t", text, *span) if ok else ""
    rid2 = reading_id("t", text.replace("n = 3", "n = 4"), *locate(text.replace("n = 3", "n = 4"), "4", "wells (n = 4 in")) if ok else ""
    ok = ok and rid1 != rid2 and rid1.startswith("t:")
    if not ok:
        print("  selftest FAIL", span, rid1, rid2)
    return ok


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", help="directory of JSON documents exported from the page's corrections store")
    ap.add_argument("--text", help="a pasted PROOF CORRECTIONS block")
    ap.add_argument("--only", nargs="*", help="store ids (or pasteN) to vet; default all")
    ap.add_argument("--batch", default=f"Martin {dt.date.today().isoformat()}")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        ok = selftest()
        print("  proof_vet selftest: " + ("OK" if ok else "FAIL"))
        return 0 if ok else 1
    items = items_from_store(pathlib.Path(a.store)) if a.store else items_from_text(pathlib.Path(a.text)) if a.text else []
    if not items:
        print("  nothing to vet: give --store DIR or --text FILE")
        return 1
    added, skipped = vet(items, a.batch, set(a.only) if a.only else None, write=not a.dry_run)
    for x in added:
        print("  vetted  " + x)
    for x in skipped:
        print("  skipped " + x)
    print(f"  proof_vet: {len(added)} vetted, {len(skipped)} skipped" + (" (dry run)" if a.dry_run else f" -> {VERDICTS.relative_to(REPO)}"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
