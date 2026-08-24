#!/usr/bin/env python3
"""
decision_lint.py
================
Make an unrecorded decision visible.

DECISION_LOG.md records WHY a methodological or editorial call was made. Its
failure mode is not that entries are wrong — it is that a session makes a call,
the session ends, and nobody writes it down. That is exactly how the C4
triangulation was reintroduced weeks after being retired on evidence, and how
the 100-month window changed meaning from a minimum into a cap with no one
deciding it.

This lint cannot make anyone think. It makes the omission mechanical:

  1. Every changelog delta dated on or after the log's own start date must
     either name a D-nnn or say "no decision". A code change that quietly
     encodes a scientific choice is the thing that went unrecorded before.
     Deltas predating the log are exempt automatically, by date in the filename.
  2. Every D-nnn referenced anywhere — changelogs, the claims register — must
     exist in the log.
  3. Every log entry must carry the load-bearing fields. An entry without a
     Revisit-if is an opinion, not a decision.
  4. There is exactly one decision log. Two ran in parallel until 2026-08-16
     and every id from D-001 to D-017 meant two different things depending on
     which file you opened, so a citation could not be followed safely (D-029).
  5. Entries marked RATIONALE UNCONFIRMED are reported, so backfilled
     reconstructions do not quietly harden into settled reasoning.

Usage:
    python3 tools/decision_lint.py            # report and exit non-zero on failure
    python3 tools/decision_lint.py --quiet    # only failures
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG = REPO / "DECISION_LOG.md"   # canonical since 2026-08-16 (D-029)
CHANGELOG_DIR = REPO / "changelogs"
CLAIMS = REPO / "tools" / "claims_register.csv"

# Deltas older than the log cannot be expected to reference it.
LOG_START = "2026-08-16"

REQUIRED_FIELDS = ["Question:", "Decision:", "Rationale:", "Revisit-if:"]
DECISION_RE = re.compile(r"\bD-(\d{3})\b")
DELTA_DATE_RE = re.compile(r"CHANGELOG_delta_(\d{4}-\d{2}-\d{2})")
EXEMPT_PHRASE = "no decision"


def parse_log() -> tuple[dict[str, str], list[str]]:
    """{id: body} for every entry, plus ids marked RATIONALE UNCONFIRMED."""
    if not LOG.exists():
        return {}, []
    text = LOG.read_text(encoding="utf8")
    entries, unconfirmed = {}, []
    parts = re.split(r"^### (D-\d{3})\b", text, flags=re.M)
    for i in range(1, len(parts), 2):
        did, body = parts[i], parts[i + 1]
        entries[did] = body
        if "RATIONALE UNCONFIRMED" in body.split("\n")[0]:
            unconfirmed.append(did)
    return entries, unconfirmed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    fail = 0

    # The working record is deliberately untracked (2026-08-24), so a clone of
    # the public repository has no DECISION_LOG.md at all and every checkout
    # would fail this gate on a file it is not meant to carry. An ABSENT log is
    # skipped with a note; a log that is PRESENT but yields nothing is still a
    # failure, because that means the format changed under the parser — which is
    # the thing this check exists to catch.
    if not LOG.exists():
        print(f"  SKIP  {LOG.name} is not in this checkout — the working record "
              f"is untracked by decision.")
        print(f"        Settled decisions are in DECISIONS_PUBLIC.md.")
        return 0

    entries, unconfirmed = parse_log()
    if not entries:
        print(f"FAIL  {LOG.name} is present but no entries parsed — the "
              f"heading format has changed under the parser.")
        return 1
    if not args.quiet:
        print(f"DECISION_LOG.md: {len(entries)} entries "
              f"({len(unconfirmed)} rationale-unconfirmed)\n")

    # --- 1. changelog deltas must name a decision, or disclaim one ----------
    checked = exempt = 0
    for p in sorted(CHANGELOG_DIR.glob("CHANGELOG_delta_*.md")) if CHANGELOG_DIR.exists() else []:
        m = DELTA_DATE_RE.search(p.name)
        if m and m.group(1) < LOG_START:
            exempt += 1
            continue
        checked += 1
        body = p.read_text(encoding="utf8")
        ids = set(f"D-{n}" for n in DECISION_RE.findall(body))
        if not ids and EXEMPT_PHRASE not in body.lower():
            print(f"FAIL  {p.name}\n      names no D-nnn and does not say "
                  f"{EXEMPT_PHRASE!r}")
            fail += 1
            continue
        missing = sorted(i for i in ids if i not in entries)
        if missing:
            print(f"FAIL  {p.name}\n      references {', '.join(missing)}, "
                  "which are not in DECISION_LOG.md")
            fail += 1
        elif not args.quiet:
            print(f"  OK    {p.name} -> "
                  f"{', '.join(sorted(ids)) if ids else 'no decision'}")
    if not args.quiet:
        print(f"\n  {checked} delta(s) checked, {exempt} exempt "
              f"(predate {LOG_START})\n")

    # --- 2. claims register decision ids must resolve -----------------------
    if CLAIMS.exists():
        for row in csv.DictReader(open(CLAIMS, encoding="utf8")):
            did = (row.get("decision_id") or "").strip()
            if did and did not in entries:
                print(f"FAIL  claims_register: {row['claim_id']} cites {did}, "
                      "which is not in DECISION_LOG.md")
                fail += 1
        if not args.quiet:
            print("  claims register decision ids resolve\n")

    # --- 3. entries must carry the load-bearing fields -----------------------
    for did, body in sorted(entries.items()):
        missing = [f for f in REQUIRED_FIELDS if f not in body]
        if missing:
            print(f"FAIL  {did} is missing: {', '.join(missing)}")
            fail += 1

    # --- 4. there must be exactly one decision log --------------------------
    # Two ran in parallel until 2026-08-16 and every id from D-001 to D-017
    # meant two different things depending on which file you opened (D-029).
    # A second log is not a filing untidiness: it silently redirects every
    # citation in the corpus. Cheap to detect, so detect it.
    others = [p for p in REPO.rglob("DECISION_LOG*.md")
              if p != LOG
              and "_to_delete" not in p.parts
              and ".git" not in p.parts
              and "retired" not in p.read_text(encoding="utf8", errors="ignore")[:400].lower()]
    if others:
        for p in others:
            print(f"FAIL  second decision log at {p.relative_to(REPO)}\n"
                  f"      {LOG.name} at the repo root is canonical (D-029). "
                  "Merge it in and leave a stub, or the ids collide.")
        fail += len(others)
    elif not args.quiet:
        print("  one decision log\n")

    # --- 5. surface the backfilled ones -------------------------------------
    if unconfirmed and not args.quiet:
        print("  RATIONALE UNCONFIRMED (backfilled — confirm before citing as "
              "settled reasoning):")
        for did in unconfirmed:
            first = entries[did].split("\n")[0].strip(" ·()")
            print(f"    {did}  {first[:70]}")
        print()

    print("decision_lint: FAIL" if fail else "decision_lint: OK")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
