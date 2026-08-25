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
SCAN_GLOBS = ["src/**/*.py", "tools/*.py", "*.md", "docs/**/*.md", "data/*.md"]

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
    # scratch names constructed inside a tool at run time, never on disk
    "out.md", "probe.md", "a.md", "b.md",
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
KNOWN_DANGLING = {
    'AUDIT_10series_PRE_FELL_START.md':
        "the pre-fell start-date audit behind clearfell_common",
    'BETA2_DECOMPOSITION_UPDATED.md':
        "beta-2 decomposition note, cited from the MS",
    'CHANGELOG.md':
        "a generic pointer; the project keeps dated deltas in changelogs/",
    'CHANGELOG_date_formatting_sweep.md':
        "dated delta not carried into changelogs/",
    'CHANGELOG_delta_2026-06-30_scrape_drawdown_physics.md':
        "dated delta predating changelogs/",
    'CHANGELOG_delta_2026-08-10_18_sy_spatial_trends.md':
        "dated delta not carried into changelogs/",
    'CHANGELOG_forecaster_simplification.md':
        "dated delta not carried into changelogs/",
    'CHAPTER_FLAGS_TO_REVIEW.md':
        "build-era review flags; 4 scripts in the 10-series and 21 IN DRIVE: 1gXTSFwHwnSRG_E4z_0AGv9GCYIxcjGQk (84 KB, 2026-05-15).",
    'COASTAL_NET_VS_EASTING_MEMO.md':
        "the coastal-vs-easting memo; 3 MS citations",
    'DEFECT_NOTE_script20_residual_field_2026-08-06.md':
        "the DEFECT D1 note; substance now in INTERCEPTION_TREATMENT.md sec 4",
    'DIAGNOSTIC_REPORT_script_26_cluster_assignment.md':
        "script 26 cluster-assignment diagnostic",
    'FIGURE_LEDGER.md':
        "referenced by cite_check; the figure ledger was never committed",
    'FINDINGS_script21_summer_minima.md':
        "summer-minima findings behind script 21",
    'FINDING_canopy_buffering_consolidated.md':
        "the canopy-buffering finding behind 10a",
    'GEOMETRY_ARCHITECTURE_SPEC.md':
        "the site-geometry spec; cited from 8 scripts, the widest orphan",
    'HANDOVER_SCRIPT03_DATUM.md':
        "the drainage-datum handover, cited from config.py",
    'HANDOVER_c3_detrend_check.md':
        "handover for script 28; also cited from PIPELINE_README",
    'MODEL_SPECIFICATION_AUDIT.md':
        "model-specification audit behind script 23",
    'NRG_window_policy_spec_2026-08-14.md':
        "window-policy spec behind a decision entry",
    'PLAN_differential_movement_writeup.md':
        "plan for the script 32 write-up",
    'REPORT_STRUCTURE.md':
        "cited by cite_check DOC_GLOBS and symbol_check; never existed here",
    'SCRAPING_EFFECTS_KNOWLEDGE.md':
        "scraping mechanism notes behind 09g and the MS",
    'SPEC_script35_per_well_amplification_metric.md':
        "spec for the amplification metric",
    'SPEC_script37_scale_factor_regression_2026-07-06.md':
        "spec for the driver-validation regression",
    'SPEC_script37b_partB_comparative_footing_2026-07-06.md':
        "spec for 37b part B",
    '_to_delete/ledgers_DECISION_LOG_premerge_2026-08-16.md':
        "RECOVERABLE: the file was retrieved to Updates_required/_recovered_2026-08-25/",
    'c3_detrend_check_results.md':
        "results file for the C3 detrend check",
    'claude/NRG_spring_BACI_spec_2026-08-13.md':
        "spring-BACI spec, in a working folder never committed",
    'methods_supplement_master_v1_9_7.md':
        "a superseded MS working filename IN DRIVE, dropped version suffix: 1cbTlyO1P2utddeIbc0rzyT1XcwdmclLr (440 KB).",
    'paper2.md':
        "removed deliberately (see the 2026-08-23d delta); the ODT text is the live copy",
    'site_geography.md':
        "site-geography note cited from the MS IN DRIVE: 1FaTyM0EBnMWxgwx6IfmxV-bErAcJLR69 (6 KB, 2026-05-01).",
    'wtf_interception_methodology.md':
        "the WTF interception derivation; substance now in INTERCEPTION_TREATMENT.md sec 3c IN DRIVE: 1Gso77njdZwge3B07fyOoNAF30zfBzY2C (11 KB, 2026-04-17).",
}

_CAND = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\\-]*\.md\b")


def iter_files():
    for g in SCAN_GLOBS:
        for p in REPO.glob(g):
            if not p.is_file():
                continue
            if SKIP_PARTS & set(p.relative_to(REPO).parts):
                continue
            yield p


def resolves(ref, basenames):
    if "*" in ref or "{" in ref:
        return True
    if (REPO / ref).exists():
        return True
    return pathlib.PurePosixPath(ref).name in basenames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

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
            bucket = frozen if ref in KNOWN_DANGLING else faults
            bucket.setdefault(ref, []).append(f"{rel}:{line}")

    if frozen and not a.quiet:
        n = sum(len(v) for v in frozen.values())
        print(f"  docref_lint: {len(frozen)} known-missing document(s), "
              f"{n} citation(s) — frozen inventory, see KNOWN_DANGLING")

    if faults:
        print("  docref_lint: FAULT — NEW reference(s) to documents that do not exist")
        for ref in sorted(faults):
            print(f"    {ref}")
            for w in faults[ref]:
                print(f"        cited at {w}")
        print("  Write the document, repoint the citation, or add the string to")
        print("  EXEMPT with a reason that is not 'the file is missing'.")
        return 1

    if not a.quiet:
        n_frozen = sum(len(v) for v in frozen.values())
        print(f"  docref_lint: OK — {n_refs} document reference(s) checked, "
              f"{n_refs - n_frozen} resolve, {n_frozen} frozen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
