#!/usr/bin/env python3
# =============================================================================
# step_number_lint.py — a per-step locator in the corpus must agree with the
#                       script it names, as the manifest numbers it.
#
# WHY
#   run_analysis.py is the source of truth for pipeline step numbering;
#   outputs/pipeline_manifest.json is the committed snapshot it emits (per-step
#   index, total, and phase — the phase field added at orchestrator v2.9.0). The
#   Methods Supplement locates scripts inline: "Script 27 ... step 49/50, Phase
#   17". D-023 already put the HEADLINE counts under the manifest guard
#   (_DOCUMENTED_COUNTS), but nothing watched these prose LOCATORS, so they
#   drifted silently: Script 27 read "step 44" and "step 49" in different places
#   while the manifest said 52; 09f/09g/27 kept their pre-insertion numbers after
#   Scripts 39/40/41 were registered ahead of them. This is that missing watch.
#
# THE INVARIANT — keyed on script identity, deliberately narrow
#   A locator of the form  step N[/T][, Phase P]  that names a script beside it
#   (either "<n><letter?>_name.py" or "Script <n><letter?>") must satisfy, for
#   THAT script's manifest record:
#       N == index      T (if written) == total_registered      P (if written) == phase
#   Only locators paired with a resolvable script are checked. A "step" with no
#   script beside it is not validated — which is what keeps this off the
#   supplement's own "Step 1 / 27" chapter walk (a deliberate, separate scheme
#   that annotates the run_analysis phase in parentheses and denominates by the
#   count of analytical chapters, not the pipeline total). Denominator 27 is also
#   skipped explicitly as belt-and-braces against the walk.
#
# WHY CHECK-ONLY
#   The corpus files are pandoc mirrors of ODT sources; a fix belongs in the ODT
#   (tools/odt_edit.py) with a version bump and a mirror rebuild — a document
#   edit made deliberately. This reports drift and prints the exact old->new the
#   ODT needs.
#
# EXIT CODES
#   0 clean   1 a script-tied locator disagrees with the manifest   2 usage
# =============================================================================
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_globs import DOC_GLOBS

__version__ = "2.0.1"  # Hollingham (2026) — 2026-09-03. Excludes HISTORY_DOCS
#   (decision log, public decisions, ledgers) which quote superseded/example
#   locators. v2.0.0 keyed on script identity;
#   excludes the supplement's 27-chapter walk. (v1 keyed on numerator alone and
#   false-flagged the walk.)

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "outputs" / "pipeline_manifest.json"

WALK_DENOMINATOR = 27  # the supplement's analytical-chapter walk; never a step total

# History documents quote superseded and example locators by design (the decision
# log describes drift like Script 27 "step 44"; the ledgers record past states).
# cite_check excludes the same set from its spread/citation checks — this is the
# same idea, not a coincidence. DECISIONS_PUBLIC.md is built from the decision log.
HISTORY_DOCS = {"DECISION_LOG.md", "DECISIONS_PUBLIC.md", "NUMBER_LEDGER.md",
                "SCRIPT_LEDGER.md", "FIGURE_LEDGER.md", "TABLE_LEDGER.md",
                "DOC_LEDGER.md", "PARTITION_HISTORY.md"}

# a script named in prose: a filename prefix, or "Script NN[x]"
SCRIPT_RE = re.compile(
    r"(?:\brun_)?(?P<fkey>\d{1,2}[a-z]?)_[A-Za-z0-9_]+\.py"
    r"|\bScript\s+(?P<skey>\d{1,2}[a-z]?)\b"
)
STEP_RE = re.compile(r"(?i)\bstep\s+(?P<num>\d+)\s*(?:/\s*(?P<den>\d+))?")
PHASE_NEAR_RE = re.compile(r"(?i)\bphase\s+(?P<p>\d+)")


def norm_key(k: str) -> str:
    # "09" and "9" name the same script; keep any trailing letter (09f, 37b).
    m = re.match(r"(\d+)([a-z]?)", k)
    return f"{int(m.group(1))}{m.group(2)}"


def load_manifest():
    if not MANIFEST.exists():
        print(f"  step_number_lint: no manifest at {MANIFEST.relative_to(REPO)} "
              f"— run `python run_analysis.py --manifest-only`", file=sys.stderr)
        raise SystemExit(2)
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    total = int(m["total_registered"])
    steps = m.get("steps", [])
    if not steps or "phase" not in steps[0]:
        print("  step_number_lint: manifest carries no per-step 'phase' — rebuild "
              "with orchestrator >= v2.9.0 (`python run_analysis.py --manifest-only`)",
              file=sys.stderr)
        raise SystemExit(2)
    by_key = {}
    for s in steps:
        fk = re.match(r"(?:run_)?(\d{1,2}[a-z]?)_", s["script"])
        if fk:
            by_key[norm_key(fk.group(1))] = (int(s["index"]), int(s["phase"]))
    return total, by_key


def scripts_on_line(line: str):
    out = []
    for mo in SCRIPT_RE.finditer(line):
        key = mo.group("fkey") or mo.group("skey")
        out.append((mo.start(), norm_key(key)))
    return out


# Cross-reference words: "as Step 43", "see Step 29", "than Step 37" etc. name
# ANOTHER step, not the adjacent script's own position — never a locator.
_XREF_BEFORE = re.compile(r"(?i)\b(?:see|as|than|to|unlike|like|versus|vs)\s*$")


def pair_script(scripts, sm, line):
    """The script a step locator belongs to, or None if it is a cross-reference.

    Prefers a script named immediately AFTER the step ("Step 48 — 09g_...");
    otherwise the nearest script named just BEFORE it ("Script 09f ... step 47"),
    within a tight window. Returns None for possessive cross-refs ("Step 37's")
    and for prepositional cross-refs ("companion to Step 43")."""
    start, end = sm.start(), sm.end()
    # possessive: "Step 37's surface" -> a reference to step 37, not a locator
    if line[end:end + 1] in ("'", "\u2019"):
        return None
    # a cross-reference verb/preposition immediately before "step"
    before = line[max(0, start - 14):start]
    word = re.search(r"(?i)step\s*$", line[max(0, start - 6):start])  # the "step" token itself
    lead = line[max(0, start - 14):start]
    if _XREF_BEFORE.search(re.sub(r"(?i)\bsteps?\s*$", "", lead)):
        return None
    # "Step 10 (run_10_clearfell.py)" / "Step 48 — 09g_...": a step that
    # INTRODUCES its script — the gap to the following script is only an opening
    # paren or a dash — owns that script. But "at step 32/52), Script 09f" closes
    # 26c's own parenthetical first (a ")" in the gap), so the following script is
    # a new clause, not this step's subject.
    tight = [(pp, k) for pp, k in scripts if end < pp <= end + 8]
    if tight:
        gap = line[end:tight[0][0]]
        if re.match(r"^\s*[(\u2014-]", gap) and ")" not in gap:
            return tight[0][1]
    # Otherwise a script's own locator reads "Script XX (..., step N, ...)": the
    # nearest script named just BEFORE the step, inside its clause.
    before_s = [(pp, k) for pp, k in scripts if pp < start and start - pp <= 60]
    if before_s:
        return before_s[-1][1]
    # Last, a step labelling a slightly-further following script.
    after = [(pp, k) for pp, k in scripts if end <= pp <= end + 18]
    return after[0][1] if after else None


def check() -> int:
    total, by_key = load_manifest()
    findings = []
    for g in DOC_GLOBS:
        for p in sorted(REPO.glob(g)):
            if not p.is_file():
                continue
            rel = str(p.relative_to(REPO))
            if p.name in HISTORY_DOCS:
                continue
            for lineno, line in enumerate(
                    p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                scripts = scripts_on_line(line)
                if not scripts:
                    continue
                for sm in STEP_RE.finditer(line):
                    num = int(sm.group("num"))
                    den = int(sm.group("den")) if sm.group("den") else None
                    if den == WALK_DENOMINATOR:
                        continue
                    key = pair_script(scripts, sm, line)
                    if key is None or key not in by_key:
                        continue
                    idx, phase = by_key[key]
                    ctx = line[max(0, sm.start() - 20): sm.end() + 22].strip()
                    if num != idx:
                        old = sm.group(0)
                        new = re.sub(r"(?i)(step\s+)\d+", rf"\g<1>{idx}", old, count=1)
                        findings.append((rel, lineno, f"Script {key}: step {num} "
                                         f"but manifest index is {idx}", ctx, old, new))
                    if den is not None and den != total:
                        findings.append((rel, lineno, f"Script {key}: denominator /{den} "
                                         f"!= total_registered /{total}", ctx,
                                         f"/{den}", f"/{total}"))
                    pm = re.match(r"[\s,]*Phase\s+(\d+)", line[sm.end():sm.end() + 14])
                    if pm and int(pm.group(1)) != phase:
                        findings.append((rel, lineno, f"Script {key}: Phase "
                                         f"{pm.group(1)} but manifest phase is {phase}",
                                         ctx, f"Phase {pm.group(1)}", f"Phase {phase}"))
    if findings:
        print(f"\n  step_number_lint: {len(findings)} script-tied locator(s) disagree "
              f"with the manifest (total_registered = {total}):\n")
        cur = None
        for rel, ln, reason, ctx, old, new in findings:
            if rel != cur:
                print(f"  {rel}"); cur = rel
            print(f"      line {ln}: {reason}")
            print(f"          …{ctx}…")
            print(f"          ODT fix: {old!r} -> {new!r}")
        print("\n  Corpus files are pandoc mirrors; apply fixes to the ODT source "
              "via tools/odt_edit.py and rebuild the mirror.")
        return 1
    print(f"  step_number_lint: OK — every script-tied step/phase locator agrees "
          f"with the manifest (total_registered = {total}).")
    return 0


SELFTEST = [
    # (line, expect_findings)
    ("Script 27 (greyscale, step 49/50, Phase 17).", 2),      # num + den wrong; Phase 17 ok
    ("Script 27 renders figures, step 52/52, Phase 17.", 0),  # all correct
    ("the 27_greyscale_figures.py utility is step 44 of the pipeline", 1),  # num wrong
    ("Step 1 / 27. Phase 1.", 0),                              # chapter walk, no script
    ("Script 09g runs at the end of Phase 17 (step 51)", 0),   # correct
    ("Script 09g runs at the end of Phase 16 (step 48)", 1),   # num wrong (phase not in same clause)
    ("Script 36 (36_absolute_climate_trend.py) — Step 39/52, Phase 15", 0),  # correct
    ("discrete companion to Step 37's surface (Script 35)", 0),  # possessive cross-ref
    ("Unlike Step 36's differential anomaly, Script 35", 0),   # possessive cross-ref
    ("Script 26b writes per-well CSV (see Step 29 below)", 0),  # 'see Step' cross-ref
    ("standalone companion to Step 43 (Script 31b)", 0),       # 'to Step' cross-ref
    ("Step 48 — 09g_mechanism_diagrams.py runs late", 1),      # script labelled by step: 48!=51
    ("(Script 26c, step 32). Phase 14 runs the cluster work", 0),  # phase is a new sentence
]
_ST_KEYS = {"27": (52, 17), "9g": (51, 17), "36": (39, 15), "35": (38, 15),
            "26b": (31, 13), "31b": (44, 16), "26c": (32, 13)}
_ST_TOTAL = 52


def selftest() -> int:
    failed = 0
    for line, want in SELFTEST:
        got = 0
        scripts = scripts_on_line(line)
        for sm in STEP_RE.finditer(line):
            num = int(sm.group("num"))
            den = int(sm.group("den")) if sm.group("den") else None
            if den == WALK_DENOMINATOR:
                continue
            key = pair_script(scripts, sm, line)
            if key is None or key not in _ST_KEYS:
                continue
            idx, phase = _ST_KEYS[key]
            if num != idx:
                got += 1
            if den is not None and den != _ST_TOTAL:
                got += 1
            pm = re.match(r"[\s,]*Phase\s+(\d+)", line[sm.end():sm.end() + 14])
            if pm and int(pm.group(1)) != phase:
                got += 1
        ok = got == want
        failed += not ok
        print(f"  {'ok  ' if ok else 'FAIL'}  want {want} got {got}: {line!r}")
    if failed:
        print(f"\n  step_number_lint --selftest: {failed} case(s) wrong")
        return 1
    print(f"\n  step_number_lint --selftest: {len(SELFTEST)} case(s), all correct")
    return 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return check()


if __name__ == "__main__":
    sys.exit(main())
