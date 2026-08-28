#!/usr/bin/env python3
"""docref_lint — every markdown document a source file cites must exist.

WHY THIS EXISTS

  Writing INTERCEPTION_TREATMENT.md on 2026-08-25 turned up three references to
  documents that had never been written:

      DECISION_LOG.md D-022     -> INTERCEPTION_TREATMENT.md
      DECISION_LOG.md D-020     -> PARTITION_HISTORY.md
      17_wtf_specific_yield.py  -> wtf_interception_methodology.md
      20_spatial_figures.py     -> DEFECT_NOTE_script20_residual_field_2026-08-06.md

  Each read as a promise that the reasoning was recorded somewhere. None of them
  was. A reader following the pointer finds nothing; a reader who does not
  follow it assumes the derivation exists and moves on. Both are worse than an
  honest silence.

  This is the same failure the project has now found in five registers, in its
  purest form: a reference nothing matches is invisible to the thing that would
  report it. So this gate matches them.

WHAT IT DOES

  Sweeps the source and prose for anything shaped like a markdown filename and
  checks that it resolves — either at the path given, or by basename anywhere in
  the repository. A reference that resolves nowhere is a FAULT and fails the
  gate.

WHAT IT DELIBERATELY DOES NOT DO

  It does not check anchors, section numbers, or whether the document says what
  the citation claims. It answers one question - does the file exist - because
  that is the question that can be answered mechanically and without judgement.
"""
import re, sys, pathlib, argparse

REPO = pathlib.Path(__file__).resolve().parents[1]

# Live source and live prose only. changelogs/ is deliberately absent: a
# changelog is a dated record of what was true then, and a path that existed in
# June and does not exist now is history, not a fault. Rewriting dated records
# to make a linter happy is the one thing this project does not do.
# This list has now lost references TWICE to a directory move, on the same day,
# in the tool whose whole job is to notice a reference going missing.
#   notes/**    added when the root tidy moved 26 documents there: 347 -> 287.
#   working/*   added when tier 2 moved DECISION_LOG.md, WORK_REGISTER.md and
#               README_WORKING.md off the root: 357 -> 290.
# Only working/*.md, deliberately — NOT working/**. The 231 files under
# working/changelogs/ and working/updates/ have never been scanned; they are
# dated working records, they cite documents that were superseded or lost on
# purpose, and sweeping them would bury the live corpus in historical dangles.
# ANY move of a scanned document must be followed by re-running this tool and
# comparing the count. A move is exactly when the net silently narrows.
SCAN_GLOBS = ["src/**/*.py", "tools/*.py", "*.md", "docs/**/*.md",
              "notes/**/*.md", "working/*.md", "data/*.md"]

# Directories that hold snapshots, recoveries and scratch. A dangling reference
# inside a backup is a fact about the past, not a fault in the project.
SKIP_PARTS = {".git", ".git-working", "backups", "_recovered_2026-08-25",
              "_audit_tmp", "_to_delete", "_frozen", "_superseded",
              "node_modules", "__pycache__",
              # third-party code vendored under src/. Its citations are other
              # projects' documentation and none of this project's business.
              "venv", "site-packages"}

# Not references. Each needs a reason, and the reason has to be that the string
# is not a pointer to a document - never that the document is missing.
EXEMPT = {
    # glob patterns in tool configuration, not filenames
    "*.md", "**/*.md", "*.py", "text/*.md",
    # a filename built at runtime from a template
    "{name}.md", "{stem}.md",
    # tools/build_diary.py names its own --public output, which exists only once
    # that flag is used. A path a tool CREATES is not a dangling reference.
    "notes/PROJECT_HISTORY.md",
    # scratch names constructed inside a tool at run time, never on disk
    "out.md", "probe.md", "a.md", "b.md",
    # placeholders with a stand-in for a number, written as prose in the
    # recovered documents: "methods_supplement_master_v1_8_N" means any of the
    # v1_8_* series, "report_edits/text/reportN.md" means report8, 9, 10...
    "methods_supplement_master_v1_8_N.md", "report_edits/text/reportN.md",
}

# A reference inside a URL is a link to someone else's repository, not a
# pointer into this one. Matched on the whole line rather than the token,
# because the token itself looks like a path.
_URLISH = re.compile(r"https?://|www\.|github\.com|\.org/|\.io/")

# ── the frozen debt ─────────────────────────────────────────────────────────
# Documents the live source cites that do not exist in the repository, as
# inventoried on 2026-08-25 when this gate was written. They are almost all
# working notes, specs and audits from the build - the kind of thing that lived
# beside the project rather than in it. Whether each was lost, never committed,
# or still sits in a folder on the author's machine is not yet established.
#
# 2026-08-25, later the same day: the question is answered for some of them.
# Four were found and two recovered into this repository - wtf_interception_
# methodology and site_geography, both with a superseded-values banner because
# they predate the k=5 repartition. Local backups held none of the rest, and
# git has never carried any of them: they were written beside the project, not
# in it.
# They are in the author's Google Drive project store, under `methods/` and its
# parent - INTERCEPTION_TREATMENT.md and PARTITION_HISTORY.md were recovered
# from there and are now in this repository. Entries below carry the Drive id
# where one is known, so recovery is a fetch rather than a search.
#
# They are frozen here rather than deleted or repointed for one reason: a
# citation is evidence that the reasoning existed, and a silent deletion
# destroys that evidence. The gate's job is to stop the list GROWING.
#
# Remove an entry when the document is found, written, or the citation is
# repointed. Do not add one without deciding, explicitly, that the document is
# not going to be recovered.
#
# 2026-08-26, T-10 closing pass. Two more recovered and now in this repository:
# DDP_EVALUATION.md, from a zip member in ~/Downloads (the only archive hit in
# 108 archives), and DIAGNOSTIC_script21_vs_script10_summer_minima.md, from
# ~/Downloads/cleanup - the question whose answer,
# FINDINGS_script21_summer_minima.md, was recovered earlier the same day. Both
# carry status banners: the DDP recommendation still stands and every number in
# it has moved, and all five script-21 divergences were fixed by v1.1.0 the day
# the brief was written. Restoring the DDP note added BETA2_DECOMPOSITION.md to
# this list, below. The old c3_detrend results file is gone from both dicts: it
# was a committed output under a different name, and on 2026-08-26 its one
# citation in Script 29 was repointed at outputs/28_c3_detrend/, so there is
# nothing left to freeze.
#
# Ten of the original thirteen remain. They were searched for on 2026-08-26
# across every mounted root (home, Downloads, Documents, Desktop, Files_sync,
# projects, audit, NRG-rewrite and the whole of Google Drive including the
# earlier NRG tree under Reports/Gemini Paper/scripts/NRG), inside 108 archives,
# and in the git history of the audit clone and NRG-rewrite. Not one of the ten
# leaves a trace anywhere. They were working notes that lived beside the project
# and were never in it. The full account is in
# Updates_required/T10_RECOVERY_2026-08-26.md.

# Documents that are missing BY RULING, not by loss. Searching the disk for
# these is wasted effort and finding one is not good news: an old copy of a
# retired document is exactly the fork the ruling removed. Frozen for gating
# like KNOWN_DANGLING, but excluded from --list-missing.
RETIRED = {
    'paper2.md':
        "deleted deliberately — WORK_REGISTER M33, closed 2026-08-23: a month "
        "stale, carried the superseded +0.120 m clearfell step and the withdrawn "
        "climate ranking. the PAPER2_EDITS, PAPER2_TABLES and PAPER2_FIGURES notes are the maintained surface.",
    'methods_supplement_master_v1_9_7.md':
        "retired by D-012 as a hand-maintained master — a second editable copy of "
        "a document is a fork, not a source. The ODT is canonical; "
        "docs/report/text/Newborough_Methods_Supplement.md is its mirror.",
    '_to_delete/ledgers_DECISION_LOG_premerge_2026-08-16.md':
        "the pre-merge original behind the D-id collision. An archival trace, not "
        "a live document; the merged root DECISION_LOG.md supersedes it.",
}

KNOWN_DANGLING = {
    # --- surfaced 2026-08-27, when the root tidy put notes/** into SCAN_GLOBS ---
    # Not new dangles. The ledgers were outside the scan until that day, so these
    # three had never been checked. Sixty references joined the net with them.
    'TABLE_LEDGER.md':
        "PROPOSED, never written. notes/ledgers/README.md:24 lists it as one of "
        "three ledgers still to build, with its seed source named. A plan is not "
        "a missing document.",
    'DOC_LEDGER.md':
        "PROPOSED, never written. notes/ledgers/README.md:25, same as above — it "
        "would track the 'ODT bumped, PDF lags' state that tools/export_lag.py "
        "now answers directly, so it may never be needed.",
    'NRG_methods_code_audit_2026-08-14.md':
        "LOST. The code-vs-doc audit the script ledger was seeded from "
        "(notes/ledgers/SCRIPT_LEDGER.md:10). Not on disk, in either repository, "
        "or in any Claude project store searched during T-10. Its findings "
        "survive as the ledger's own rows; the reasoning behind them does not.",
    'claude/HANDOVER_cowork_NRG_2026-08-13.md':
        "NEW 2026-08-26: named by the recovered 2026-08-13b handover as the "
        "authoritative onboarding document for that session. Not in the project "
        "store, on disk, or in the repository.",
    'AUDIT_10series_PRE_FELL_START.md':
        "the pre-fell start-date audit behind clearfell_common; also cited from "
        "the recovered script-21 diagnostic brief",
    'BETA2_DECOMPOSITION.md':
        "NEW 2026-08-26: introduced by restoring DDP_EVALUATION.md, whose section 4 "
        "cites it for the superseded C4 lambda=0.05. The pre-rebuild beta-2 note; "
        "its successor BETA2_DECOMPOSITION_UPDATED.md is in the repository and "
        "carries two superseded banners of its own. Restoring a document restores "
        "its bibliography, and this is that cost, paid openly.",
    'CHANGELOG.md':
        "a generic pointer; the project keeps dated deltas in changelogs/",
    'CHANGELOG_delta_2026-08-08_pipe_top_upstand_correction.md':
        "dated delta cited by the recovered geometry spec; never carried into changelogs/",
    'DEFECT_NOTE_script20_residual_field_2026-08-06.md':
        "the DEFECT D1 note; substance now in INTERCEPTION_TREATMENT.md sec 4",
    'DIAGNOSTIC_REPORT_script_26_cluster_assignment.md':
        "script 26 cluster-assignment diagnostic",
    'FIGURE_LEDGER.md':
        "never written, not lost. ledgers/README.md lists it as **proposed** - "
        "'seed from tools/figure_table_manifest.csv and "
        "NRG_report_figure_xref_2026-08-13.csv' - alongside TABLE_LEDGER and "
        "DOC_LEDGER, which are equally unwritten. tools/cite_check.py:893 names it "
        "as a ledger to check. Do not search the disk: T-10's archive sweep matched "
        "two 13-byte members reading 'fixture body', which are that tool's own test "
        "fixtures. The close is to write the ledger, not to find it.",
    'HANDOVER_c3_detrend_check.md':
        "handover for script 28; also cited from PIPELINE_README",
    'SPEC_script35_per_well_amplification_metric.md':
        "spec for the amplification metric",
    'SPEC_script37_scale_factor_regression_2026-07-06.md':
        "spec for the driver-validation regression",
}

_CAND = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\\-]*\.md\b")


# working/PROJECT_DIARY.md is GENERATED by tools/build_diary.py and quotes commit
# subjects and note titles verbatim — including documents renamed or retired
# months ago, which is the point of a history. Scanning it turned every historical
# filename into a dangling reference and took this gate red within a minute of
# the diary first being built. A derived record cannot be evidence about what
# exists now.
_GENERATED = ("working/PROJECT_DIARY.md", "notes/PROJECT_HISTORY.md")


def iter_files():
    for g in SCAN_GLOBS:
        for p in REPO.glob(g):
            if not p.is_file():
                continue
            if SKIP_PARTS & set(p.relative_to(REPO).parts):
                continue
            if p.relative_to(REPO).as_posix() in _GENERATED:
                continue
            yield p


def resolves(ref, basenames):
    if "*" in ref or "{" in ref:
        return True
    if (REPO / ref).exists():
        return True
    return pathlib.PurePosixPath(ref).name in basenames


# Files whose whole job is to tell someone where to look. A dead path in an
# analysis note is a stale note; a dead path in one of these is a person sent to
# a folder that does not exist — which is what happened on 2026-08-28, when
# WORK_REGISTER.md went on naming `Updates_required/` and `store/` for a day
# after the restructure renamed both.
SIGNPOSTS = [
    "working/WORK_REGISTER.md", "working/README_WORKING.md",
    "BOOTSTRAP.md", "CLAUDE.md", "readme.md", "PIPELINE_README.md",
]
# A line may name a path deliberately dead — the "was -> is" table in
# WORK_REGISTER.md documents exactly the names that stopped working. Marking the
# line opts it out. Local to the line, so no central exemption list to maintain.
_FORMER = "<!-- former path -->"
_PATHISH = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*/[A-Za-z0-9_./-]*)`")


def check_signposts() -> int:
    """Does every path a signpost names still exist?"""
    faults = []
    for rel in SIGNPOSTS:
        f = REPO / rel
        if not f.exists():
            continue
        for n, line in enumerate(f.read_text(encoding="utf8",
                                             errors="replace").splitlines(), 1):
            if _FORMER in line:
                continue
            for m in _PATHISH.finditer(line):
                path = m.group(1).rstrip("/")
                if path.startswith(("http", "~", "$")) or " " in path:
                    continue
                # a bare domain is a URL, not a path on this disk
                if re.match(r"^[\w.-]+\.(com|org|net|io|uk|gov)(/|$)", path):
                    continue
                # a signpost inside working/ writes `changelogs/`, meaning the
                # one beside it. Resolve relative to the FILE as well as to the
                # repository root before calling a path dead.
                # Documents write paths relative to an implied root:
                # PIPELINE_README says `utils/mechanism_fig_utils.py` meaning
                # src/, and `01_data_prep/...` meaning outputs/. A path that
                # resolves under any known root is findable; the fault this
                # check exists for is a path that resolves under NONE.
                roots = [REPO, f.parent, REPO / "src", REPO / "outputs",
                         REPO / "working", REPO / ".git", REPO / "docs"]
                if any((r / path).exists() for r in roots):
                    continue
                # a glob or a pattern is not a claim that a file is there
                if any(c in path for c in "*?["):
                    continue
                faults.append((rel, n, path))
    if faults:
        print("  docref_lint: FAULT — signpost names a path that does not exist")
        for rel, n, path in faults:
            print(f"    {rel}:{n}  {path}")
        print("  These files exist to send someone to the right place. Fix the")
        print(f"  path, or mark the line {_FORMER} if the name is deliberately")
        print("  historical.")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--list-missing", action="store_true",
                    help="print the documents worth searching for, one per line: "
                         "KNOWN_DANGLING minus RETIRED minus names too generic to "
                         "search by. The recovery tools read this rather than "
                         "keeping their own copy of the list.")
    a = ap.parse_args()

    if a.list_missing:
        # 'CHANGELOG.md' is a generic pointer, not a document with that name.
        for name in sorted(KNOWN_DANGLING):
            if name in RETIRED or name == "CHANGELOG.md":
                continue
            print(name.rsplit("/", 1)[-1])
        return 0

    basenames = {p.name for p in REPO.rglob("*.md")
                 if not (SKIP_PARTS & set(p.relative_to(REPO).parts))}

    faults, frozen, n_refs = {}, {}, 0
    for p in iter_files():
        rel = p.relative_to(REPO).as_posix()
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _CAND.finditer(text):
            ref = m.group(0).replace("\\", "/")
            if ref in EXEMPT:
                continue
            ls = text.rfind("\n", 0, m.start()) + 1
            le = text.find("\n", m.end())
            if _URLISH.search(text[ls: le if le > 0 else len(text)]):
                continue
            n_refs += 1
            if resolves(ref, basenames):
                continue
            line = text.count("\n", 0, m.start()) + 1
            known = ref in KNOWN_DANGLING or ref in RETIRED
            bucket = frozen if known else faults
            bucket.setdefault(ref, []).append(f"{rel}:{line}")

    if frozen and not a.quiet:
        n = sum(len(v) for v in frozen.values())
        n_ret = sum(1 for r in frozen if r in RETIRED)
        print(f"  docref_lint: {len(frozen) - n_ret} known-missing + {n_ret} "
              f"retired-by-ruling document(s), {n} citation(s) — frozen inventory")

    rc_sign = check_signposts()

    if faults:
        print("  docref_lint: FAULT — NEW reference(s) to documents that do not exist")
        for ref in sorted(faults):
            print(f"    {ref}")
            for w in faults[ref]:
                print(f"        cited at {w}")
        print("  Write the document, repoint the citation, or add the string to")
        print("  EXEMPT with a reason that is not 'the file is missing'.")
        return 1
    if rc_sign:
        return 1

    if not a.quiet:
        n_frozen = sum(len(v) for v in frozen.values())
        print(f"  docref_lint: OK — {n_refs} document reference(s) checked, "
              f"{n_refs - n_frozen} resolve, {n_frozen} frozen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
