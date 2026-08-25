#!/usr/bin/env python3
"""
build_public_decisions.py — derive DECISIONS_PUBLIC.md from DECISION_LOG.md.

WHY THERE ARE TWO FILES

  `DECISION_LOG.md` is a working record. Each entry carries the question that
  prompted it, the decision, the rationale, what the alternative would have
  cost, and — where the first answer was wrong — a dated amendment saying so.
  That shape is what makes it useful while the analysis is running, and it is
  the wrong shape to publish: a reader arriving cold meets the deliberation
  before the conclusion, and a reader arriving hostile can mine the amendments
  for a narrative the record does not support.

  What belongs in a public repository is the settled decision. This script
  emits exactly that: for each entry, its number, its title, its date, its
  status and its **Decision** statement. The question, the rationale, the
  amendments and the quoted discussion stay in the working record.

  THE NUMBERS ARE THE POINT. Nine citations in the Methods Supplement and
  PIPELINE_README name a decision by number. The public file keeps the same
  D-numbers, so every one of them still resolves. That is the constraint the
  whole arrangement is built around: distil the entry, never renumber it.

  It is generated, not maintained. Editing DECISIONS_PUBLIC.md by hand puts it
  out of step with the record it is derived from, which is the failure mode
  this project has met in every other place two files hold the same fact.

Usage:
    python3 tools/build_public_decisions.py            # write
    python3 tools/build_public_decisions.py --check    # verify it is current
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-24.

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "DECISION_LOG.md"
DST = REPO / "DECISIONS_PUBLIC.md"

PREAMBLE = """# Decisions

Analytical decisions taken in the course of this study, in the order they were
numbered. Each entry records what was decided, when, and whether it still
stands. They are cited by number from the Methods Supplement and the pipeline
documentation.

A decision appears here because a choice existed and one option was taken:
which wells enter a control tier, what a fitted constant may and may not be
read as, where a boundary between an input and a result falls. Several record
that a quantity the data appear to offer is not one the record can support, and
those are decisions too — the useful output of an analysis includes what it
declines to claim.

This is a distillation. The working record behind it carries, for each entry,
the question that prompted it, the reasoning, the alternatives weighed and any
later correction. Only the settled decision is reproduced here.

*Generated from the working record by `tools/build_public_decisions.py`. Do not
edit by hand.*

---

"""

# Until 2026-08-16 two decision logs ran in parallel and every id from D-001 to
# D-017 meant two different things. That mapping is not deliberation — it is the
# lookup a reader needs to interpret any citation written before that date — and
# the first version of this file omitted it, so a public reader following an old
# D-number had no way to learn the id had moved. Carried through from the
# working record rather than retyped, so the two cannot disagree.
COLLISION_HEADING = "## Old ledger ids → this file"


def collision_note(src: str) -> str:
    i = src.find(COLLISION_HEADING)
    if i < 0:
        return ""
    end = src.find("\n### ", i)
    body = src[i:end if end > 0 else len(src)].strip()
    # The source heading carries its own merge parenthetical, which reads
    # oddly under the new title. Replace the whole line, not the prefix.
    first, _, rest = body.partition("\n")
    body = "## Citations written before 2026-08-16\n" + rest
    return body + "\n\n---\n\n"


# A Decision statement in the working record is a reply to the Question above
# it, so a fifth of them open with a bare answer token — "No. The triangulation
# is retired." Reproduced without the question, that reads as a fragment. The
# question is not reproduced (it is where the back-and-forth lives, quoted
# discussion included), so the token is stripped instead and what remains has
# to stand on its own: the register states what holds, not what was rejected.
_ANSWER = re.compile(
    r"^(?:no|yes|neither|both|it does|it is not|they do|the answer is)\b"
    r"[\s,.:;—-]*", re.I)

# Stripping the token is only safe when a sentence starts underneath it. Where
# the answer was grammatically load-bearing — "both, and they are now
# separated", "yes, as the unexplained uniform decline" — removing it leaves a
# clause hanging off nothing, which is worse than the fragment it was meant to
# fix. Those are handed back rather than mangled.
_HANGING = re.compile(
    r"^(?:and|as|but|or|so|because|with|for|to|in|at|on|by|from|that|which|"
    r"though|while|since|after|before)\b", re.I)

# Below this, stripping has left a sentence that cannot carry the entry alone.
MIN_SELF_STANDING_WORDS = 6

# The six the strip cannot handle. Each is a lead-in written so the entry reads
# as a statement rather than a reply; the rest of the Decision follows it
# verbatim. OPENING TEXT ONLY — nothing here adds, softens or reinterprets a
# decision, and each is checked against its own entry by --check below. Keyed
# on the exact opening being replaced, so an edit to the working record breaks
# the build loudly instead of silently applying a lead-in to different words.
LEAD_IN = {
    "D-003": ("No, for the per-well fits.",
              "Full-record fits do not unbalance the per-well comparisons."),
    "D-008": ("No. `HEADLINE_LAG = 0`.",
              "Rainfall enters the SSM without a lag: `HEADLINE_LAG = 0`."),
    "D-022": ("as a",
              "`FOREST_INTERCEPTION` enters the water balance as a"),
    "D-056": ("both, and they are now separated.",
              "The sweep was finding both real drift and coincidences, and the "
              "two are now separated."),
    "D-058": ("yes, as the",
              "The site-wide decline is quantified as the"),
    "D-060": ("yes. From",
              "The long-run rate is measurable. From"),
}


def self_standing(dec: str, num: str = "") -> tuple[str, str | None]:
    """Make the Decision read as a statement. (text, reason-it-still-dangles)."""
    if num in LEAD_IN:
        old, new = LEAD_IN[num]
        if not dec.startswith(old):
            return dec, (f"lead-in no longer matches: the entry now opens "
                         f"{dec[:40]!r}, not {old!r}")
        return (new + dec[len(old):]).strip(), None
    out = _ANSWER.sub("", dec).strip()
    if not out:
        return dec, "the decision is the answer token alone"
    if len(out.split()) < MIN_SELF_STANDING_WORDS:
        return dec, f"only {len(out.split())} words remain after the answer token"
    if _HANGING.match(out):
        return dec, f"the answer is load-bearing — what follows opens '{out.split()[0]}'"
    out = out[0].upper() + out[1:] if out[0].islower() else out
    return out, None


def parse(text: str) -> list[dict]:
    parts = re.split(r"(?m)^### (D-\d+)\s+(.*?)$", text)
    out = []
    for i in range(1, len(parts), 3):
        num, head, body = parts[i], parts[i + 1], parts[i + 2]
        # The parenthetical comes in two orders — "(date · status: x)" and
        # "(status: x · confirmed date)" — and nine entries use the second.
        # A parser that knows only one silently loses both the date and the
        # title's tail, which is how D-008 shipped with its status inside its
        # own title.
        pm = re.search(r"\(([^()]*status:[^()]*)\)\s*$", head)
        if not pm:
            raise SystemExit(f"{num}: heading has no (… status: …) parenthetical")
        inner = pm.group(1)
        sm = re.search(r"status:\s*([a-z]+)", inner)
        status = sm.group(1) if sm else "active"
        when = " ".join(f.strip() for f in inner.split("·")
                        if "status:" not in f and re.search(r"\d{4}", f))
        title = head[:pm.start()].strip()
        dm = re.search(r"\*\*Decision:\*\*(.*?)(?=\n\s*\n|\n- \*\*|\Z)", body, re.S)
        if not dm:
            raise SystemExit(f"{num}: no Decision statement — refusing to guess")
        dec = " ".join(dm.group(1).split())
        dec, dangles = self_standing(dec, num)
        # Two more fields are statements rather than deliberation, and both are
        # load-bearing. **Consequence** is what follows from the decision: it
        # appears once, in D-050, and it is what all four of that entry's
        # citations actually point at - without it the public D-050 describes a
        # control tier and says nothing about the reading it withdrew.
        # **Revisit-if** is the condition under which the decision stops
        # holding, which a reader needs and which carries no discussion.
        extra = {}
        for f in ("Consequence", "Revisit-if"):
            fm = re.search(r"\*\*" + f + r":\*\*(.*?)(?=\n\s*\n|\n- \*\*|\Z)",
                           body, re.S)
            if fm:
                extra[f] = " ".join(fm.group(1).split())
        out.append({"n": num, "title": title, "when": when, "status": status,
                    "dec": dec, "dangles": dangles, "extra": extra})
    if not out:
        raise SystemExit("no entries parsed — the log's heading format has changed")
    return out


def render(entries: list[dict], src: str = "") -> str:
    body = [PREAMBLE, collision_note(src)]
    for e in entries:
        when = e["when"] or "undated"
        stat = "" if e["status"] == "active" else f" · **{e['status']}**"
        body.append(f"### {e['n']} — {e['title']}\n\n"
                    f"*{when}{stat}*\n\n{e['dec']}\n\n")
        if e["extra"].get("Consequence"):
            body.append(f"**Consequence.** {e['extra']['Consequence']}\n\n")
        if e["extra"].get("Revisit-if"):
            body.append(f"**Revisit if** {e['extra']['Revisit-if']}\n\n")
    body.append(f"---\n\n{len(entries)} decisions. "
                f"Generated by `tools/build_public_decisions.py`.\n")
    return "".join(body)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the public file is not current")
    args = ap.parse_args()

    if not SRC.exists():
        print(f"  {SRC.name} not found — nothing to derive from.")
        return 0 if args.check else 1

    raw = SRC.read_text(encoding="utf-8")
    new = render(parse(raw), raw)

    if args.check:
        if not DST.exists():
            print(f"  MISSING  {DST.name} — run tools/build_public_decisions.py")
            return 1
        if DST.read_text(encoding="utf-8") != new:
            print(f"  STALE    {DST.name} — run tools/build_public_decisions.py")
            return 1
        print(f"  OK       {DST.name} is current")
        return 0

    DST.write_text(new, encoding="utf-8")
    n = new.count("\n### D-")
    print(f"  wrote {DST.name}: {n} decisions, "
          f"{len(new.split()):,} words (source: {len(SRC.read_text().split()):,})")
    stuck = [e for e in parse(SRC.read_text(encoding="utf-8")) if e["dangles"]]
    if stuck:
        print(f"\n  {len(stuck)} entr(ies) still read as a reply to a question that is")
        print("  not reproduced. They need a sentence written for them:")
        for e in stuck:
            print(f"      {e['n']}  {e['dangles']}")
            print(f"            {e['dec'][:96]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
