#!/usr/bin/env bash
# check_all.sh — the gate. Run before every commit, and in CI.
#
# Each check answers a question that was answered wrongly at least once:
#   versions   does a document's in-text version string still agree with the
#              filename it was saved under? The Methods Supplement said 1.9.7
#              while its filename said _v1_9_24.
#   mirrors    are the lints reading current text, or yesterday's?
#   cite       does the corpus still agree with the committed pipeline outputs?
#   decisions  did a change encode a choice that nobody recorded?
#   basis      does the Methods Supplement still describe which record each
#              analysis is fitted on? It asserted a fitting window for Script 07
#              for months; Script 07 performs no fit.
#
# Exit non-zero if any gate fails. --fix syncs the document version strings and
# regenerates the mirrors instead of failing on them — the two failures with a
# safe automatic remedy. The version sync runs FIRST: it edits the ODTs, so
# mirrors regenerated before it would be stale the moment it ran.
#
# ============================================================================
# VERSION 1.41.0 - 2026-11-11   proof_copy --refresh moved to the HQ daily pass (J-12, T-196;
#                               Martin 2026-11-09, Q9 of the J-10 review). Its section is renamed
#                               "inequality claims" for the gate left in it, inequality_lint, which
#                               keeps its position (40) and its rc. Measured runtime before/after in
#                               changelog 2026-11-11 J-12.
#   1.40.0 (2026-11-11): pipeline index section (T-197, J-13): tools/build_pipeline_index.py
#                               --selftest and --check gate pipeline_index.html, the generated
#                               script index index.html's Pipeline section links to.
#   1.39.0 (2026-11-09): the PULL path's safety property, in the records section (J-4).
#                               tools/nrg_git_selftest.sh runs nrg_git.sh's history_guard and
#                               pull_working against throwaway repository pairs in the four states
#                               a private pull can be in. Until nrg_git.sh 1.34.0 option 4 guarded
#                               and pulled the PUBLIC repo only, so a machine could be brought "up
#                               to date" with its records half behind, and nothing asserted the
#                               guard that J-4's brief calls "the whole safety property". A grep
#                               for the call would test the text; this tests the behaviour.
#                               SKIPS in a public clone. Negative-tested three ways.
# VERSION 1.38.0 - 2026-11-07   job_runner's selftest gated, with its detail shown (T-156's
#                               shape): the pass over the job queue is what keeps a queued job
#                               from waiting on a human noticing, so it is gated like the
#                               registers it reads.
# VERSION 1.37.0 - 2026-11-06
# CHANGELOG
#   1.38.0 (2026-11-08): mention_lint runs its --selftest first, as csv_mention_lint already did.
#     mention_lint 1.2.0 scopes the version check to the SENTENCE, not the line: "and until" ended
#     one line of CLAUDE.md §4g while "`nrg_git.sh` 1.32.0" began the next, so true testimony read
#     as a claim about the tree the moment another chat moved that file to 1.33.2. The selftest pins
#     the scope at both edges -- a wrapped history word exempts, one in a previous paragraph or
#     bullet does not -- because the bug was invisible until an unrelated version bump exposed it.
#   1.37.0 (2026-11-06, T-156): the claims section SHOWS the doc_lock selftest's failing lines.
#     The call was `--selftest >/dev/null || echo FAIL`, so a red printed one bare line and
#     discarded every line naming the assertion - the same defect as the `tail -1` at line 378
#     that 1.36.0 removed the day before. It cost a session the whole NRG_DOC_LOCK_HOLDER
#     diagnosis: the ship reported "FAIL doc_lock selftest" and nothing else. Negative-tested
#     with a stub that fails and prints two FAIL lines: both are shown, indented, and rc=1.
#   1.36.0 (2026-11-05): the model-form section GATES. form_label_lint was advisory from 1.32.0
#     "until the 2026-10-28 edit set lands"; it has landed, and the suppression had been printing
#     FAIL - 6 field(s) without a form into a section whose verdict read OK. Martin 2026-11-05:
#     "act on the third finding ... we need to resolve this". The six are fixed (form_label_lint
#     1.1.0 knows the water-balance basis; Paper M v1_44 names it in the bracket sentence), so the
#     gate turns on with nothing owed. `tail -1` dropped so a failure names the value.
#   1.35.0 (2026-11-05): the conduct checks (D-301 phase 3, T-137). tools/rule_audit.py gains a
#     gated --selftest and an advisory --check in the claims section: it audits the audit trail -
#     commits against claims, handover entries, decision fields, document and script version bumps,
#     the chat register, the override log - and reads this script's own summary for every rule that
#     already has a gate, so no lint is implemented twice. --check never fails the run (D-302).
#   1.34.0 (2026-11-05): per-section verdicts (D-301, spec D5a). `section` replaces the fifty
#     `echo "── … ──"` headers, printing each one byte-identically and recording the previous
#     section's verdict; it RESETS rc, because rc is sticky and a snapshot without a reset reads
#     every section after the first failure as green. `_total_rc` carries the run. Writes
#     scratch/check_all_summary.json (override with NRG_GATE_SUMMARY), each section keyed by
#     position as well as name. cite_check's section is renamed "asserted claims": it and the chat
#     claims board were both headed "claims", and a page reporting one of them had to say which.
#     New gates: chat_register
#     and job_queue --selftest and --check (D-301).
#   1.33.0 (2026-11-04): claims gate gains doc_lock --selftest (GATED, like the other two modules
#     that keep chats apart) and board_artifact --check (advisory: it says the phone view is behind,
#     which only a session can fix by republishing). doc_lock 1.4.0 refuses to call an unreadable
#     lock "free" - D-300, after a public-only clone was told every claim was free while another
#     chat held doc:PaperM. The selftest runs the whole of the spec's section 6 against throwaway
#     trees; it never reads or writes the real lock.
#   1.32.0 (2026-10-28): model-form section (form_label_lint, D-284), advisory until the
#     2026-10-28 edit set lands.
#   1.31.0 (2026-10-25): references gate gains tools/paper_refs.py (--selftest, then the check):
#     the papers type their caption numbers, alt text and references by hand, and nothing
#     checked any of them; reference_lint reads only the report master. Caption meanings are
#     pinned in tools/paper_caption_snapshot.csv.
#   1.30.0 (2026-10-25): references gate runs repoint_refs --selftest (1.7.0) first: the
#     matcher's refusals (block crossing, script figure ids, filename stems) are what kept
#     the 2026-10-25a renumber from corrupting 18 Methods Supplement labels only after the
#     fact; a selftest that nothing runs rots.
#   1.29.0 (2026-10-15): claims gate also runs cite_check --selftest-claims (1.35.0): the
#     outside/inside/cmp rules, whose bounds are pipeline values, must be able to come out false
#     (spec NRG_spec_claims_range_rules_2026-10-15).
#   1.28.0 (2026-10-13): film text gate after ledgers - film_text_lint: the three language
#     tables of Script 47 1.9.0 (en, cy, pl) hold the same keys and template fields
#   1.27.0 (2026-10-10): "claims (who is doing what?)", advisory: tools/work_board.py --gate names
#     uncommitted work under a claim nobody holds and work a ship held back and never put back
#     (spec NRG_spec_parallel_chats_2026-10-10). Plus the register_io and ship_scope self-tests, gated.
#   1.26.0 (2026-10-08): chatbot gate after public decisions - build_chat_corpus --selftest
#     (the denylist still keeps the papers, the working log and copyrighted literature out)
#     and --check (no denied path allowlisted; the published chatbot's stamp matches its
#     sources). Spec claude/NRG_spec_chatbot_2026-10-08.md.
#   1.25.0 (2026-10-06): self-citation gate after cross-references - self_cite_lint: one
#     fixed 2026 letter per work in every paper (tools/self_citations.csv; changelog 2026-10-06f).
#   1.24.0 (2026-10-01): number-fields gate (D-219) after table cells - field_sync --check:
#     every user field in every document is registered and equals its committed value.
#   1.23.0 (2026-09-30): ship_regen_lint gate (D-213) beside rule_gate_lint - every
#     derived artefact this script gates must be rebuilt by nrg_git.sh's
#     ship_regenerate(); three ships on 2026-09-30 died on gates the ship could
#     have cleared itself. SKIPPED, not failed, in a public clone (no working/).
#   1.22.0 (2026-09-29): proof copies section (advisory) after the tasks gate -
#     proof_copy --refresh keeps scratch/proof_bundle/ current from the mirrors and
#     the captured task_lint output, and reports whether the published proof
#     artifact is behind the bundle (a session republishes and stamps).
#   1.21.0 (2026-09-27): make_site_outline --check gates (D-204) - the site
#     outline every map masks with must be the union of the committed KML.
#   1.20.0 (2026-09-25): month_step_lint after month_bucket_lint (D-195) - every
#     calendar month has a row, the one-month bridge fills only lone interior
#     months, and build_ssm_frame pairs every month with the previous one.
#   1.19.0 (2026-09-24): sync_index_counts --check gates (derived counts in
#     markers; undated unmarkered counts fail); mention_lint 1.1.0 also checks
#     quoted tool versions and "X gates" claims. Martin: "if this is the case
#     then it needs to be included as a gate". starmath_log --check: the
#     EQUATION_LEDGER was the one generated ledger with no --check (R22) and
#     was 16 lines stale.
#   1.18.0 (2026-09-24): mention_lint after csv_mention_lint — every script, tool
#     and path a root document names must exist (exemptions with reasons in
#     tools/mention_lint_exempt.csv). The documentation-layer audit's gate.
#   1.17.0 (2026-09-24): freeze_requirements --check after env_audit: the pins
#     in requirements.txt must equal venv/'s dist-info (pip excepted). Found 42
#     unpinned packages and a scrambled header that env_audit could not see.
#   1.16.0 (2026-09-21): five gates from the rule -> gate matrix's work list.
#     retired_phrase_lint (retired wordings and numbers in every mirror),
#     docglob_lint (every ODT and mirror inside the drift net), csv_mention_lint
#     (every CSV/JSON a document names exists), table_provenance_lint (R23 -
#     CLAUDE.md named it as the enforcer and nothing ran it), and --check for
#     DOC_LEDGER, NUMBER_LEDGER (collisions) and VALUE_LEDGER, with the retired
#     TABLE_LEDGER asserted still retired (R22). record_basis_claims_lint: each
#     methods section states the record its analysis uses (option B, R39).
#   1.15.0 (2026-09-21): rule -> gate matrix. rule_gate_lint checks that
#     tools/rule_gate_matrix.csv - one row per CLAUDE.md / project-box rule
#     and the gate that enforces it - still describes the tree: every named
#     gate exists and every 'gated' row names a tool this file runs. Gates the
#     MATRIX, not the rules; the 'none' and 'partial' rows are the work list.
#   1.14.0 (2026-09-21): cross-reference gate. xref_lint fails on any report
#     chapter that sends its reader to the Methods Supplement - CLAUDE.md's rule
#     since the Supplement existed, checked by nothing until two edit batches
#     added six such pointers in one morning and Martin found them reading the
#     proof copy. Pre-existing pointers sit in xref_allow.csv with the reason,
#     each awaiting his ruling; a new one fails. The Supplement's own
#     self-references by chapter are counted, advisory.
#   1.13.0 (2026-09-08): bibliography gate. bib_lint checks report13's entries
#     against the report corpus in both directions (an entry nobody cites; a
#     citation with no entry), with a reasoned allowlist in bib_exemptions.csv.
#     Six uncited entries and one orphaned citation (Sun et al., 2015) were found
#     by hand on 2026-09-08 - and (Jennings, 1990) was orphaned by an edit the
#     same morning - with nothing to report either. Sits beside docref_lint.
#   1.12.1 (2026-09-08): section_map.py --check (1.3.0) now also compares the
#     headings with tools/section_map_snapshot.csv - a section number whose
#     heading changed or vanished since the pin fails here, the way a figure
#     number's caption does in reference_lint. Re-pin with --snapshot once the
#     typed references have been re-pointed. No new line; the existing gate.
#   1.12.0 (2026-09-08): two gates from the 09-07 cross-reference audit (P2 process).
#     section_map.py --check runs before section_ref_audit: the map was stale on
#     09-07 and 09-08 (a new section missing) while the audit scored against it
#     and read OK. build_figure_ledger.py --check runs after reference_lint
#     --kind figure: a caption with no resolvable Source: marker, or a ledger
#     that no longer matches the captions, now fails here rather than waiting
#     for someone to regenerate the ledger by hand (Figure 75, 2026-09-08).
#   1.11.0 (2026-09-07): step provenance gate (S1). provenance_lint reads
#     outputs/pipeline_provenance.json (run_analysis 2.15.0) and fails when a
#     committed output was produced from an upstream that has since changed, or
#     rests on a documented first-pass default. Skips until the first recorded
#     run, as input_provenance did. --selftest first.
#   1.10.0 (2026-09-07): ms_chapters gate (D-144 §4) beside the ledgers: every
#     registered step has a Methods Supplement chapter heading naming it and a
#     SCRIPT_LEDGER row. run_analysis.py refuses registration on the same
#     check; this makes the gate read red before the pipeline does.
#   1.9.0 (2026-09-07): phases gate (D-144). doc_tier_lint: every ODT family has
#     a doc_tier.csv row, `current` agrees with the phase, every set_by and every
#     logged frozen-document write cites a real D-number or changelog id. The
#     refusal itself lives in odt_edit._write; this checks the register it reads.
#   1.8.0 (2026-09-07): records gate (D-143). session_handover.py --check fails
#     when the project's own records are stale: DECISION_INDEX behind the log,
#     the newest HANDOFF older than the newest substantive commit, no dated
#     HANDOVER_NOTE entry for the newest commit day (or one over 40 lines), a
#     script commit in the last 3 days with no changelog naming it, Tier 0 over
#     budget. Exists because the Tier-0 machinery built 2026-08-28 was bypassed
#     within three days and the index sat 32 decisions behind while every gate
#     read green - the D-102/D-133 shape, applied to the records themselves.
#     --selftest first, as for input_provenance.
#   1.7.0 (2026-09-05): input_provenance_lint gate (W132) beside output_lag —
#     watches the input->output boundary. Skips cleanly until run_analysis.py
#     records the raw-input hashes; --selftest first.
#   1.6.0 (2026-09-05): venv self-guard. The gate now activates the project
#     venv itself when no virtualenv is active, so a forgotten activate no
#     longer drops the run onto system python. env_audit still gates right
#     after, so the guard removes a manual step without ever masking a wrong
#     interpreter. Prompted by a 2026-09-05 run under system python (numpy
#     1.26 vs recorded 2.4.6, cairosvg missing) reading as a FAIL.
#   1.5.0 (2026-08-31): output_lag GATES (D-102). It ran advisory since
#     2026-08-27 because it cannot tell a coefficient change from a docstring
#     edit, and a check that cries stale over comments is one people learn to
#     skip. That argument prices the false positive, which costs one re-run. The
#     false negative was priced on 2026-08-31 and it was silent:
#     24b_residual_climatology.py is an OPT-IN step, --full does not run it, and
#     it sat with edited code and outputs from the previous version while every
#     other gate read green - because every other gate reads the outputs and
#     finds them self-consistent, which they are, with the older code. The
#     pre-commit run is now `run_analysis.py --full --with-supplementary` and
#     this is what enforces it. Wired only after confirming it passes.
#   1.4.0 (2026-08-26): env_audit runs first. Half the checks below print a
#     version and act on it, and none of them said whose. A Cowork sandbox's
#     pandoc 2.9.2 and python 3.10 were read as this project's for a day, and a
#     five-week outage was written up for a script that had never failed. The
#     environment line now names the machine before anything else reports.
#     (The VERSION line above read 1.2.0 against a 1.3.0 changelog entry until
#     this bump — the header had drifted from its own history.)
#   1.3.0 (2026-08-23): ref_audit and section_ref_audit join the chain, and the
#     reference-form census prints with them. Resolution was never the weak
#     point — pointing at the wrong thing was, and nothing looked for it.
#   1.2.0 (2026-08-23): symbol_check and reference_lint join the chain. Both
#       were written months apart, both were run by hand, and neither gated —
#       which is why a register collision and a table-reference cascade could
#       both sit undetected. Each splits its exit code: the structural fault
#       gates, the inherited backlog reports.
#   1.1.0 (2026-08-19): document-version gate added, ahead of the mirrors block
#       for the ordering reason above. tools/doc_version_sync.py --check.
#   1.0.0: this script's state before it carried a version number. 1.0.0 marks
#       the number's introduction, not the start of the script's history.
# ============================================================================
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

FIX=0
[ "${1:-}" = "--fix" ] && FIX=1
rc=0

# ── per-section verdicts (1.34.0, D-301, spec NRG_handover_HQ_page_2026-11-05 D5a) ──
#
# This script printed ONE verdict for fifty sections, so the HQ page could not say which section
# went red, and every chat that wanted to know grepped the log for "FAIL".
#
# `section` prints the header EXACTLY as the fifty `echo "── … ──"` lines did - byte for byte, so
# anything grepping `^──` is unaffected - and records the previous section's verdict on the way past.
#
# IT RESETS rc, AND THAT IS THE WHOLE TRICK. rc is sticky: once a check sets rc=1 it stays 1 to the
# end. Snapshotting it per section without resetting would attribute the first failure correctly and
# then read every later section as green, because rc was already 1 when they started. So rc becomes
# the CURRENT section's flag, `_total_rc` carries the run's, and none of the ninety-seven `rc=1`
# sites needs touching. Measured before changing anything: rc was read in exactly two places, the
# two lines at the end of this file.
GATE_SUMMARY="${NRG_GATE_SUMMARY:-scratch/check_all_summary.json}"
_sec_tsv="$(mktemp "${TMPDIR:-/tmp}/check_all_sections.XXXXXX")"
_sec_name=""
_sec_t0=0
_total_rc=0

_sec_flush() {
    [ -z "$_sec_name" ] && return 0
    local verdict="OK"
    if [ "$rc" != "0" ]; then verdict="FAIL"; _total_rc=1; fi
    printf '%s\t%s\t%s\n' "$_sec_name" "$verdict" "$(( $(date +%s) - _sec_t0 ))" >> "$_sec_tsv"
    rc=0
}

section() {
    _sec_flush
    echo "$1"
    # the section's NAME: the header text before the trailing dashes and before any "(question)"
    local t="${1#── }"
    t="${t%%─*}"
    t="${t%% (*}"
    _sec_name="$(printf '%s' "$t" | sed -e 's/[[:space:]]*$//')"
    _sec_t0="$(date +%s)"
}

_sec_write_summary() {
    _sec_flush
    mkdir -p "$(dirname "$GATE_SUMMARY")" 2>/dev/null || true
    python3 - "$_sec_tsv" "$GATE_SUMMARY" "$_total_rc" <<'PYSUM' || true
import datetime, json, pathlib, platform, sys
tsv, out, total = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
secs = []
for line in tsv.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    name, verdict, seconds = (line.split("\t") + ["", "", ""])[:3]
    secs.append({"index": len(secs) + 1, "key": f"{len(secs) + 1:02d} {name}",
                 "section": name, "verdict": verdict, "seconds": int(seconds or 0)})
out.write_text(json.dumps({
    "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "host": platform.node(),
    "verdict": "OK" if total == "0" else "FAIL",
    "sections": secs,
    "counts": {"sections": len(secs),
               "failed": len([x for x in secs if x["verdict"] != "OK"])},
}, indent=2) + "\n", encoding="utf-8")
PYSUM
    rm -f "$_sec_tsv" 2>/dev/null || true
}

# Run under the project venv (the recorded interpreter) unless a virtualenv is
# already active. Spares a forgotten `source venv/bin/activate` dropping the run
# onto system python (env_audit then fails on the wrong libs, as it did on
# 2026-09-05). This NEVER masks a mismatch: env_audit runs immediately below and
# gates, so a machine whose venv is not the recorded interpreter still fails
# loudly. A venv already active (direnv, manual activate, or a bridge shim that
# exports VIRTUAL_ENV) is left untouched.

# --fast / --docs: hand off to the document-only gate profile (review phase).
# Runs the doc-facing gates only (~1 min) and skips the pipeline/provenance/
# output/analysis gates, which cannot change during a text-only review. NOT a
# substitute for the full run before a push that includes pipeline changes.
case "${1:-}" in
  --fast|--docs) exec bash "$(dirname "$0")/check_docs.sh" "${@:2}" ;;
esac
if [ -z "${VIRTUAL_ENV:-}" ] && [ -f venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

# FIRST, deliberately. Several checks below print a version and act on it -
# refresh_mirrors refuses to write under an old pandoc, figref_lint needs
# pdftotext, build_pdfs needs LibreOffice - and none of them says WHOSE version
# it is reporting. On 2026-08-26 that cost a day: a Cowork sandbox's pandoc 2.9.2
# and python 3.10 were read as this project's, and a five-week outage was written
# up for a script that had never failed. env_audit runs before anything else so
# that every line after it is read against the right machine.
#
# IT GATES SINCE 2026-08-29, and only on the two faults that are true wherever
# they are seen: a library the pipeline imports being NOT IMPORTABLE, and the
# record disagreeing with requirements.txt. Identity never gates - a second
# machine SHOULD report "NOT THE MACHINE", that is the tool working - and
# version drift gates only on the recorded machine, where re-recording is the
# one-command fix. Until this date the line ended `|| true`: it ran, printed the
# whole finding, and could not fail, which is how a recorded reference that
# CANNOT RUN THE PIPELINE sat here for weeks with every gate green (D-093).
section "── environment (is this the machine the pipeline runs on?) ──────────"
python3 tools/env_audit.py --quiet --gate || rc=1
# requirements.txt must equal venv/ (D-093). env_audit compares the RECORD
# against the pins but probes only the libraries the pipeline imports directly;
# 42 packages installed for the film, the Sentinel and capture tools sat
# unpinned for weeks and a whole-file sort scrambled the header (2026-09-17) with
# every gate green. Reads the venv's dist-info directly; passes where there is
# no venv/ (a clone), because it cannot see the environment it would compare.
python3 tools/freeze_requirements.py --check --quiet || rc=1

echo
section "── document versions (does the text agree with the filename?) ───────"
if [ "$FIX" = "1" ]; then
    python3 tools/doc_version_sync.py --quiet || rc=1
else
    python3 tools/doc_version_sync.py --check --quiet || {
        echo "  (run tools/check_all.sh --fix to sync them)"
        rc=1
    }
fi

echo
section "── mirrors ──────────────────────────────────────────────────────────"
if [ "$FIX" = "1" ]; then
    python3 tools/refresh_mirrors.py || rc=1
else
    python3 tools/refresh_mirrors.py --check || {
        echo "  (run tools/check_all.sh --fix to regenerate)"
        rc=1
    }
fi
# --check compares modification times and gates on them because it is instant.
# It cannot tell you whether a mirror is what its source PRODUCES. When that is
# the question — a mirror that keeps coming back changed, a suspicion that two
# pandocs disagree — `--verify` regenerates every mirror and compares bytes. It
# is not in the gate because it runs pandoc 23 times.
echo "  (content check, on demand: python3 tools/refresh_mirrors.py --verify)"

echo
section "── pipeline (are the SCRIPTS importing the right numbers?) ───────────"
# defaults and backward dependencies GATE: a default masquerading as a result,
# or a script reading an output that does not exist yet, both put a wrong number
# into the outputs silently. The literal lint is advisory — it over-reports, and
# a gate that fires 30 times on day one gets switched off by day three.
python3 tools/pipeline_lint.py --check defaults || rc=1
python3 tools/pipeline_lint.py --check deps     || rc=1
# runid GATES too, and asks a provenance question the two above cannot: is
# pipeline_site_observations.csv the product of ONE pass? It is run-scoped, so a
# producer run on its own writes a real value into a file otherwise recording
# the previous pass. Not a nineteenth gate script — a fourth sub-check of the
# tool that already owns the "are the scripts working from the right numbers?"
# family. See D-101.
python3 tools/pipeline_lint.py --check runid    || rc=1
python3 tools/pipeline_lint.py --check literals 2>/dev/null | grep -cE "FAIL" \
  | xargs -I{} echo "  {} hard-coded constant(s) — python3 tools/pipeline_lint.py --check literals"
# defaults_lint asks the OTHER defaults question: pipeline_lint asks whether a
# committed parameter is still a first-pass default; this asks whether each
# documented default still equals the committed cell its comment names. It
# GATES: the trailing comment on every entry IS the advisory, and the drift
# recurred five times in eleven days regardless.
python3 tools/defaults_lint.py || rc=1

echo
section "── record basis (does §F.6 still describe the code?) ─────────────────"
python3 tools/record_basis_lint.py --quiet || rc=1
# ... and does each methods section STATE it? Option B (Martin, 2026-09-21): a
# statement per method, gated — tools/record_basis_claims.csv carries the
# fragment each section must contain; code -> register -> sentence.
python3 tools/record_basis_claims_lint.py --selftest >/dev/null || rc=1
python3 tools/record_basis_claims_lint.py --quiet || rc=1

echo
section "── model form (does every split and timescale say Model A or Model B?) ──"
# D-284 (Martin 2026-10-28 "all 3 please"): since D-283 the split is Model B's and most
# other quantities Model A's, so a share or timescale with no form named is ambiguous.
# GATED since 2026-11-05: the edit set has landed and the lint reads 0 without a form, which is
# the condition the advisory period was waiting for. It was advisory for eight days and spent the
# last of them printing FAIL into a section that reported OK - the shape of defect this whole
# evening was spent on - so the `|| true` the comment above used to prescribe replacing is replaced.
# `tail -1` went with it: a gating check must show WHICH value is unlabelled, not just how many.
python3 tools/form_label_lint.py 2>&1 || rc=1

echo
section "── month bucketing (one implementation of Script 01's day<=15 rule?) ──"
# T-32. The rule had five correct implementations and three written as
# `d - pd.offsets.MonthBegin(1)`, which is a NO-OP for days 2-15: the day<=15
# branch reads as applied and is not. It was fixed in one place on 2026-09-13
# and reintroduced in a new tool two days later, because the rule lived in a
# comment at each call site. This gate proves utils.buckets.month_bucket
# equivalent to every correct variant over every date from 1990 to 2040 - an
# exhaustive proof, not a sample, because dates are the whole input domain - and
# fails if any live line buckets with MonthBegin again.
python3 tools/month_bucket_lint.py || rc=1

echo
section "── month steps (is every monthly change one calendar month?) ──────────"
# D-195. A month no visit buckets to had no row (June 2005, December 2022), the
# bridge filled the first month of longer gaps, and build_ssm_frame differenced
# across holes: 151 of 13,211 reference-network pairs spanned 2-23 months.
python3 tools/month_step_lint.py || rc=1
python3 tools/month_step_lint.py --selftest >/dev/null || rc=1

echo
section "── table sources (config, map and caption agree on number->source?) ──"
python3 tools/table_source_lint.py || rc=1
echo

section "── table provenance (does every table trace to a committed CSV?) ─────"
# R23: table_provenance_lint.py is the enforcer CLAUDE.md §4e names ("a table
# cannot have no CSV") but was run by nothing until 2026-09-21.
python3 tools/table_provenance_lint.py --quiet || rc=1

echo
section "── table cells (does every generated table cell match its source CSV?) ──"
# Gate added 2026-09-19: table_source_lint checks a table DECLARES its source;
# this checks the cells MATCH it. 110 stale cells across 9 tables sat behind a
# green gate until this was wired (the W101/D-006 failure, for tables).
python3 tools/table_gen.py --check || rc=1

echo
section "── number fields (does every field in every document equal its committed value?) ──"
# Gate added 2026-10-01 (D-219): a pipeline number in a document is a user field named in
# tools/number_fields.csv; the ship sets them (field_sync --write), this proves it happened.
python3 tools/field_sync.py --check || rc=1

echo
section "── drift term (does any consumer name 10a's drift column by literal?) ──"
# D-111 swept the PRODUCER and not the consumers: 10a stopped emitting
# easting_x_time, Script 25 went on filtering on that literal, matched nothing,
# wrote a one-byte file over a committed artefact and killed a full pipeline
# run. drift_term() was written to resolve the column and raise before any
# write; this is what makes anyone use it. --selftest first, because a lint
# that passes proves nothing unless its detection still works.
python3 tools/drift_term_lint.py --selftest || rc=1
python3 tools/drift_term_lint.py || rc=1

echo
section "── seasons (is any seasonal window defined outside config.py?) ──────"
python3 tools/season_lint.py --quiet || rc=1
echo

section "── pipeline counts (does the corpus agree with the manifest?) ──────"
# CLAUDE.md's first non-negotiable is that the step count is derived, never
# hard-typed. On 2026-09-09 it was found typed in nine places at FOUR different
# vintages (43 / 52 / 53 / 54), every one of them in a sentence that also told
# the reader the canonical count lives in the manifest. sync_index_counts.py
# stamps the two plain-text files; this gates the ones inside ODTs, which no
# script can rewrite safely.
python3 tools/pipeline_count_lint.py || rc=1
echo

section "── cross-references (does any chapter send the reader to the Supplement?) ──"
# CLAUDE.md: "Do not send a reader to the Methods Supplement. Say the thing, or
# name the script that does it." A rule in a prose file is re-broken by every
# fresh session; this is what checks it. xref_allow.csv lists the pointers
# Martin has chosen, or has yet to rule on, each with its reason.
python3 tools/xref_lint.py --selftest >/dev/null || rc=1
python3 tools/xref_lint.py --quiet || rc=1
echo

section "── self-citations (does each paper letter the author's 2026 works the same way?) ──"
# "Hollingham, 2026a" meant the report in Paper 1 and Paper 1 in Papers 2 and M; Paper 2 used one
# label for two works. tools/self_citations.csv fixes one letter per work (Martin, 2026-10-06).
python3 tools/self_cite_lint.py --selftest >/dev/null || rc=1
python3 tools/self_cite_lint.py || rc=1
echo

section "── retired wording (does any retired phrase or number reappear?) ─────"
# tau as a residence time, 117 measuring points, 8.4 ha, 1,172 ha, 53.15, the
# stale step counts, an em space, a Pye & Blott figure: tools/retired_phrases.csv
# is the list, each row with its reason; YYYY-MM-DD dates are advisory.
python3 tools/retired_phrase_lint.py --selftest >/dev/null || rc=1
python3 tools/retired_phrase_lint.py --quiet || rc=1
echo

section "── document net (is every ODT and mirror inside the drift net?) ──────"
# The gap that has appeared three times: a glob that does not match the
# filename hides a document from cite_check and audit_number_drift.
python3 tools/docglob_lint.py --selftest >/dev/null || rc=1
python3 tools/docglob_lint.py --quiet || rc=1
echo

section "── file mentions (does every CSV or JSON a document names exist?) ────"
# 17_wtf_well_sy.csv was retired on 2026-08-19 and four documents still named
# it as current on 2026-09-21; nine more names were typos one script over.
python3 tools/csv_mention_lint.py --selftest >/dev/null || rc=1
python3 tools/csv_mention_lint.py --quiet || rc=1
# Scripts, tools and paths the ROOT documents name must exist (the documentation
# layer: CLAUDE.md, MACHINE_SETUP, the READMEs, index.html, the bootstrap). The
# 2026-09-24 audit found ./wgit and nrg_git.sh at the root a month after they
# moved, a renamed script, two output files that never existed and a hand-typed
# figure table on a numbering the report had left behind — none visible to a gate.
python3 tools/mention_lint.py --selftest >/dev/null || { echo "  mention_lint --selftest: FAIL"; rc=1; }
python3 tools/mention_lint.py || rc=1
# Counts that root documents state — pipeline steps, packages pinned, ledgers,
# report figures and tables, decisions, wells — are stamped from the tree into
# <!--PL:key--> markers and checked here; an undated count outside a marker
# fails (tools/count_claims_exempt.csv carries the exemptions). Until 2026-09-24
# the stamp ran only when somebody remembered, and readme.md sat at 57/52/18/43.
python3 tools/sync_index_counts.py --check || rc=1

section "── document media (does every stripped ODT still rebuild?) ──────────"
# Superseded versions carry their images in docs/media_store rather than inside
# the zip (W154, D-149). The guarantee is byte-identity, so it is checked rather
# than assumed: every stripped document is rebuilt IN MEMORY and compared with
# the md5 recorded when it was stripped. If this fails, an archived version can
# no longer be reconstituted, which is the only thing the design gives up.
python3 tools/odt_media.py verify || rc=1

section "── S10.1 schematic (does the picture still name the right figures?) ──"
# Supplementary Material Figure S10.1 is a drawn schematic that names four report
# figures INSIDE the picture, where no reference lint can see them. It said 63-66
# for 73-76 until 2026-10-02. tools/s10_schematic.py draws it from figure_map.csv
# and records the numbers it used; this fails when figure_map has moved since.
python3 tools/s10_schematic.py --check || rc=1

section "── rounding (has new store-time rounding appeared?) ─────────────────"
python3 tools/rounding_lint.py || rc=1

echo
section "── store round trip (does rewriting a store move rows nobody touched?) ─"
# The sibling of rounding_lint, and the only check that can see this fault.
# A store written one row at a time is read whole and rewritten whole, and
# pandas' default C float parser is not correctly rounded — so every write moved
# every OTHER row by a few ULP while leaving its updated/run_id stamp pointing
# at an earlier run. provenance_lint cannot see it: it hashes each output AS
# WRITTEN, so a store that drifts on every write hashes consistently. D-157.
python3 tools/store_roundtrip_lint.py --selftest || rc=1
python3 tools/store_roundtrip_lint.py || rc=1

echo
section "── artefacts (is a committed output truthful about itself?) ─────────"
# The gate the other fifteen did not cover: an output checked against ITSELF.
# Row arithmetic (a quantity must be reproduced by the columns that define it)
# and the empty artefact (a step that could not run must not overwrite its
# committed file with a header). Both start green; see W124 and W128.
python3 tools/artefact_lint.py || rc=1

echo
section "── geographic inputs ────────────────────────────────────────────────"
# Advisory, not a gate: the open TO CONFIRM fields are questions only Martin can
# answer, and failing the build on them every run would just teach us to ignore
# it. What would be a real failure is a layer with no entry at all, or an entry
# pointing at a file that has gone.
python3 tools/geo_provenance.py || true
python3 tools/geo_consistency.py || true   # W73: withdrawn geo values must not reappear (advisory)
# D-204: site_outline.geojson must be the union of the committed site_boundary.kml.
python3 tools/make_site_outline.py --check || rc=1

echo
section "── manifest (is the committed one what the orchestrator produces?) ───"
# The manifest is the number every document cites, and it is the one committed
# output any full pipeline run rewrites - so a run from an older tree silently
# reverts it. That happened on 2026-08-29 and dropped a registered script.
# GATED: a drifting manifest is a wrong citable number.
python3 tools/manifest_lint.py || rc=1

echo
section "── step/phase locators (do the MS step numbers match the manifest?) ──"
# D-023 put the HEADLINE counts under the manifest guard; nothing watched the
# per-step "Script XX ... step N/T, Phase P" LOCATORS in the prose, so they
# drifted silently (Script 27 read "step 44" and "step 49" while the manifest
# said 52). This keys each locator on the script beside it and checks its index,
# total and phase against the manifest. GATED.
python3 tools/step_number_lint.py --selftest >/dev/null || rc=1
python3 tools/step_number_lint.py || rc=1

echo
section "── withheld headlines ───────────────────────────────────────────────"
# Script 40 withholds its own rate when its gate fails (D-085). A silent
# absence reads as success, so the state is REPORTED here. Reported, not gated:
# withholding is the script working, and failing the build on it would teach us
# to route around the gate. What would be a real failure is the file vanishing
# or the D-060 regression breaking, and both are visible below.
python3 tools/withheld_report.py || true

echo
# deferred_report is the "what is waiting on ME" half of the decision record.
# REPORTED, NOT GATED: a deferral is a session declining to make someone else's
# call, which is the behaviour that keeps the record honest. What must not happen
# is it going quiet. Retire one by adding "Deferral discharged:" to its entry.
section "── deferred decisions (what is waiting on a person?) ─────────────────"
python3 tools/deferred_report.py || true

echo
# 1.27.0: several chats work in this tree at once. REPORTED, NOT GATED: an unclaimed change is
# Martin's own work as often as a chat's, and a ship takes it as it always did. The self-tests of
# the two modules that keep chats apart (row merge, held-back work) ARE gated.
section "── claims (who is doing what?) ──────────────────────────────────────"
python3 tools/work_board.py --gate || true
python3 tools/board_artifact.py --check || true          # 1.33.0: advisory - only a session can republish
python3 tools/register_io.py --selftest >/dev/null || { echo "  FAIL register_io selftest"; rc=1; }
python3 tools/ship_scope.py --selftest >/dev/null || { echo "  FAIL ship_scope selftest"; rc=1; }
# 2026-11-06 (T-156): the detail is SHOWN on failure. This was `>/dev/null || echo FAIL`,
# so a red printed one bare line and threw away every line naming the assertion that broke -
# the same defect as the `tail -1` this file carried at line 378 until 1.36.0 (changelog
# 2026-11-05j). It cost a session the whole of the NRG_DOC_LOCK_HOLDER diagnosis on
# 2026-11-06: the ship said "FAIL doc_lock selftest" and nothing else, while the selftest
# itself names 8a and 8b. A gate that knows what is wrong must say it.
_dl_out="$(python3 tools/doc_lock.py --selftest 2>&1)" || {
  echo "  FAIL doc_lock selftest"
  printf '%s\n' "$_dl_out" | grep -E "FAIL|REFUSED" | sed 's/^/    /'
  rc=1
}
# 1.34.0 (D-301): the two registers NRG HQ runs on. Their self-tests are gated for the same reason
# the three above are - they are what keeps one chat's work out of another's - and each register's
# own --check lands on the day it is written (§4d: a generated artefact with no --check rots).
python3 tools/chat_register.py --selftest >/dev/null || { echo "  FAIL chat_register selftest"; rc=1; }
python3 tools/job_queue.py --selftest >/dev/null || { echo "  FAIL job_queue selftest"; rc=1; }
# 1.38.0 (2026-11-07, Martin: "build the job runner"): the pass over that queue. Gated with its
# detail shown, per T-156 - a selftest that knows which property failed must say which.
_jr_out="$(python3 tools/job_runner.py --selftest 2>&1)" || {
  echo "  FAIL job_runner selftest"
  printf '%s\n' "$_jr_out" | grep -E "FAIL|REFUSED" | sed 's/^/    /'
  rc=1
}
python3 tools/chat_register.py --check || rc=1
python3 tools/job_queue.py --check || rc=1
python3 tools/hq_snapshot.py --selftest >/dev/null || { echo "  FAIL hq_snapshot selftest"; rc=1; }
python3 tools/hq_snapshot.py --check || rc=1
python3 tools/hq_page.py --check || true                 # advisory - only a session can republish
# 1.35.0 (D-301 phase 3, T-137): the conduct checks. The SELFTEST gates - a broken auditor is a
# broken check - while --check only REPORTS, and returns 0 with serious findings outstanding,
# because rule_audit reports and never intervenes (D-302) and an open finding is work outstanding,
# not a red gate. It re-implements no lint: it reads this script's own per-section summary.
# 2026-11-06 (T-156, second instance): the detail is SHOWN, as for doc_lock above. The first
# fix caught doc_lock's selftest line and missed its twin here, and this one then failed in a
# run while passing standalone — with nothing but "FAIL rule_audit selftest" to go on.
_ra_out="$(python3 tools/rule_audit.py --selftest 2>&1)" || {
  echo "  FAIL rule_audit selftest"
  printf '%s\n' "$_ra_out" | grep -E "FAIL|REFUSED" | sed 's/^/    /'
  rc=1
}
python3 tools/rule_audit.py --check || true              # report-only by design (D-302)

echo
section "── decisions ────────────────────────────────────────────────────────"
python3 tools/decision_lint.py --quiet || rc=1
# Every entry must say what it governs, or context_for cannot surface it and the
# next session works without it (D-080).
python3 tools/context_for.py --audit || true
# DECISIONS_PUBLIC.md is derived from the working record, which is no longer
# tracked. Nothing else would notice the two drifting apart, and the public one
# is the only one a reader outside this machine can see.
python3 tools/build_public_decisions.py --check || rc=1

# The chatbot answers from an allowlisted corpus of PUBLISHED documents. The
# denylist keeps the papers in preparation, the working decision log and the
# copyrighted literature out whatever the allowlist says; --check also fails when
# the sources, rules, tools or page have moved since the chatbot was last built. The
# ship rebuilds the public chatbot (chat/) itself; the private artifact copy is
# republished by a session.
python3 tools/build_chat_corpus.py --selftest >/dev/null || rc=1
python3 tools/build_chat_corpus.py --check || rc=1

echo
section "── records (did the last session leave the records a session needs?) ──"
# D-143. A rule that lives only in prose, an artefact nothing consumes and a
# verdict that depends on neither is how the onboarding system was forgotten.
# If this fails, the fix is to WRITE the record it names, never to skip it.
python3 tools/session_handover.py --selftest >/dev/null || rc=1
python3 tools/session_handover.py --check || rc=1
# Which rules have a gate at all. Martin, 2026-09-21: "now I am worried we
# dont have adequate checks to ensure the project rules are followed" - after
# a CLAUDE.md rule with no gate was broken six times in a morning.
python3 tools/rule_gate_lint.py --quiet || rc=1
# D-213: the ship rebuilds every derived artefact this script gates, before
# the gate. This keeps that list paired with the gates above and below.
python3 tools/ship_regen_lint.py --selftest >/dev/null || rc=1
python3 tools/ship_regen_lint.py --quiet || rc=1
# 1.39.0 (J-4): the PULL path, which is the other half of "a public commit without its working
# commit is a change nobody can account for later" (CLAUDE.md §4f). Until nrg_git.sh 1.34.0,
# option 4 guarded and pulled the public repository only and never touched .git-working, so a
# machine could be brought "up to date" with its records half behind - and nothing asserted the
# guard, which J-4's brief calls "the whole safety property". This RUNS history_guard and
# pull_working against throwaway repository pairs in the four states a private pull can be in,
# rather than grepping for the call: a grep would test the text, which is the defect class §3C of
# the J-10 review names. SKIPS in a public clone, where working/nrg_git.sh is absent by design.
# Negative-tested three ways (the private guard removed, the private pull removed, option 4 rewired)
# via NRG_GIT_SRC against broken copies; each reads FAIL.
bash tools/nrg_git_selftest.sh || rc=1

echo
section "── phases (which document is live; is every frozen write reasoned?) ──"
# D-144: one live document family at a time. odt_edit refuses a prose write to a
# frozen family without a recorded reason; this gate keeps the register it
# consults complete and consistent, so the refusal never fires for a missing row.
python3 tools/doc_tier_lint.py --selftest >/dev/null || rc=1
python3 tools/doc_tier_lint.py || rc=1

echo
section "── ledgers (does SCRIPT_LEDGER still describe the code?) ─────────────"
# D-144 §4: a registered step the Supplement does not document is refused at
# registration; the same derived check runs here so a missing chapter is red
# before anyone runs the pipeline.
python3 tools/ms_chapters.py --selftest >/dev/null || rc=1
python3 tools/ms_chapters.py || rc=1
# Gates on structural faults only — a script with no row, a row with no script.
# Version drift is printed and counted but does not gate: it was 29 rows deep on
# the day this landed, and a gate that fails from birth is a gate that gets
# commented out. Same treatment as pipeline_lint's literal check and export_lag.
ledger_out="$(python3 tools/ledger_lint.py 2>&1)" || rc=1
printf '%s\n' "$ledger_out" | grep -E "row\(s\) with a stale version|^  ledger_lint:" || true

echo
section "── pipeline index (does pipeline_index.html match a fresh build?) ──────"
# T-197 / J-13: the public page linked from index.html's Pipeline section - each script, what it
# reads, what it feeds and which documents use it - built from pipeline_provenance.json, the
# manifest, PROVENANCE_LEDGER and citation_index. Content against a fresh build, never mtimes;
# the ship rebuilds it (ship_regenerate), so red here after a ship is a defect in the builder.
python3 tools/build_pipeline_index.py --selftest >/dev/null || { echo "  build_pipeline_index --selftest: FAIL"; rc=1; }
python3 tools/build_pipeline_index.py --check || rc=1

echo
section "── film text (do the film's three language tables say the same things?) ──"
# Script 47 1.9.0 reads every word it shows from utils/film_text_<lang>.py. A key
# missing from a language falls back to English at render time; a template whose
# fields differ raises mid-render. Gated from the day it landed (CLAUDE.md §4d).
python3 tools/film_text_lint.py || rc=1

echo
section "── document references (does every cited .md exist?) ─────────────────"
# Gates on NEW dangling references only. 32 were already dangling on the day
# this landed - 99 citations, mostly build-era specs and audits that lived
# beside the project rather than in it - and they are frozen in the tool's
# KNOWN_DANGLING inventory rather than deleted, because a citation is evidence
# that the reasoning existed. The job of the gate is to stop the list growing.
docref_out="$(python3 tools/docref_lint.py 2>&1)" || rc=1
printf '%s\n' "$docref_out" | grep -E "known-missing document|^  docref_lint: (OK|FAULT)" || true


echo
section "── bibliography (is every entry cited, and every citation an entry?) ──"
# Both directions against the report mirrors; exemptions carry a reason and a date.
python3 tools/bib_lint.py 2>&1 | grep -E "^  (UNCITED|UNRESOLVED|EXEMPT)|^bib_lint:" || true
python3 tools/bib_lint.py >/dev/null 2>&1 || rc=1
echo
section "── tasks (is any outstanding job now finished, or newly broken?) ─────"
# Gates ONLY on a check that could not answer. An open task is work in hand and
# must not fail the build; a broken check is a lie waiting to happen, and does.
# task_lint executes every registered check, several of which invoke other
# linters, so it is the most expensive gate in the file - 10 s. It was run
# TWICE, once to gate and once to display. --open carries the same exit code,
# so one run does both.
task_out="$(python3 tools/task_lint.py --open 2>&1)" || rc=1
printf '%s\n' "$task_out" | grep -E "^  [0-9]+ open|OPEN |task\(s\): " || true

# The work register's own status cells are prose and prose does not fail. On
# 2026-09-09 sixteen were wrong at once and the dashboard published the error.
# register_lint checks only what is mechanically decidable: a cell contradicting
# task_lint, a claimed check_all gate that is not invoked, a file said not to
# exist that does. Typed counts are advisory.
python3 tools/register_lint.py || rc=1
# An id means ONE task. On 2026-11-08 two chats each minted a T-183 and a T-184 -- four
# tasks under two ids -- because each took max+1 over a --depth 50 clone it could see only
# part of. cloud_setup.sh now clones with --filter=blob:none so the view is whole; this asks
# the question the merge used to answer far too late, and says nothing when origin is
# unreachable rather than guessing agreement.
python3 tools/task_register.py --selftest >/dev/null || { echo "  task_register --selftest: FAIL"; rc=1; }
python3 tools/task_register.py --check || rc=1

section "── inequality claims (is every \"p < x\" still true of its value?) ──"
# The proof-copy refresh that headed this section until 1.41.0 (J-12, T-196) now runs in the HQ
# daily pass (tools/hq_snapshot.py 1.2.0), which can republish the page as well as report it; it
# took 249 to 269 of this script's seconds and gated nothing. inequality_lint, which DOES gate,
# stays here under its own name (Martin, 2026-11-09: "q9 move to the hq daily pass").

# "p < 0.001" carries no number, so every numeric check in this project is blind
# to it: the academic summaries stated it for a committed p = 0.0021 and nothing
# could see it (W148, fixed 2026-09-09). inequality_lint checks registered
# inequality claims against the committed value. It says so loudly when the
# register is empty, because a gate that checks nothing must not read as cover.
python3 tools/inequality_lint.py || rc=1

echo
section "── symbols (does the register contradict itself?) ───────────────────"
# The register GATES; the ambiguous-glyph inventory is advisory and prints only.
# Split deliberately: the backlog is 148 entries and gating on it kept this tool
# out of the chain entirely, which is how the register came to hand z to d_depth
# while z0 was the datum with nothing to catch it (D-062).
symbol_out="$(python3 tools/symbol_check.py 2>/dev/null)" || rc=1
printf '%s\n' "$symbol_out" | grep -E "^  (RESERVED|OCCUPIED|DUPLICATE)|^  register faults" || true

# COVERAGE, which the check above cannot see. symbol_check asks whether an
# occurrence matches a REGISTERED sense; a glyph carrying a second sense nobody
# registered has no sense to fail against, so it reads as silence. beta_1 meant
# the SSM recharge coefficient and an OLS transfer-function slope in one
# document for months, and every check above passed throughout. This gates on a
# glyph GAINING a group against tools/symbol_definition_index.csv; re-pin with
# `symbol_check.py --definitions --snapshot` when a new sense is deliberate.
defs_out="$(python3 tools/symbol_check.py --definitions 2>&1)" || rc=1
printf '%s\n' "$defs_out" | grep -E "^  FAULT |^  RESOLVED |^definitions_audit:" || true

# The equations are embedded ODF objects: each carries the formula as MathML AND
# as a StarMath annotation, and LibreOffice regenerates the first from the
# second. Edit one and not the other and the change survives every check above,
# renders correctly in the PDF, and reverts the next time the formula is opened.
# THAT gates. The displaced-glyph and variant-codepoint counts are advisory.
starmath_out="$(python3 tools/starmath_log.py --check 2>&1)" || rc=1
printf '%s\n' "$starmath_out" | grep -E "^  starmath_log:|MathML and StarMath disagree" || true
# --check (1.2.0): EQUATION_LEDGER.md must be what the documents produce. It had
# no --check (R22) and sat 16 lines stale from 2026-08-27 to 2026-09-24.

echo
section "── references (do typed Table/Figure numbers still resolve?) ─────────"
# Captions auto-number; in-text references are typed by hand and fall out of
# step silently. Read from the ODTs in master order, so no PDF export is needed
# and the check cannot run on a stale artefact.
# The renumber matcher's own cases (1.30.0): repoint_refs is run only at renumber
# time, so its regressions would otherwise surface as corrupted documents.
python3 tools/repoint_refs.py --selftest >/dev/null || { echo "  repoint_refs --selftest: FAIL"; rc=1; }
python3 tools/reference_lint.py --kind table || rc=1
# The papers (1.31.0): typed captions, alt text and references, per paper family.
python3 tools/paper_refs.py --selftest >/dev/null || { echo "  paper_refs --selftest: FAIL"; rc=1; }
python3 tools/paper_refs.py --quiet || rc=1
# FIGURES, since 2026-09-01. nrg_git.sh runs figref_lint at push time and its own
# comment says what that does NOT cover: "Semantic mistakes (a reference pointing
# at the wrong existing figure) are NOT caught here." figref_lint asks whether a
# number RESOLVES; this asks whether it still MEANS what it did. Remove one figure
# and every later caption renumbers while the typed references stay put - all of
# them resolve, to the wrong figure. Found on its first run: the project box gave
# the forest drawdown render as report Figure 50; it is 57, and 50 is the SSM water
# balance residual. figref_lint had passed that PDF clean, correctly.
python3 tools/reference_lint.py --kind figure || rc=1
# Every caption carries a "(Source: file)" marker that figure_map resolves on disk;
# FIGURE_LEDGER is generated from them. A missing marker or a stale ledger fails.
python3 tools/build_figure_ledger.py --check || rc=1
# PROVENANCE_LEDGER (exhibits by output file) and VALUE_REGISTER (cited values
# and symbols by output file). Gated for the reason TABLE_LEDGER was not: it was
# the only generated ledger with no --check in this file, and by 2026-09-19 it
# carried 19 empty sources and named a supplement version five bumps old.
python3 tools/build_provenance_ledger.py --check || rc=1
python3 tools/build_value_register.py --check || rc=1
# R22 (2026-09-21): the three generated ledgers that had no --check, and the
# one whose --check nothing ran. TABLE_LEDGER is retired (2026-09-19) and its
# check asserts the retirement banner is intact; NUMBER_LEDGER's is the
# collision test (one key, two values across scripts — study_area_ha was).
python3 tools/build_doc_ledger.py --check || rc=1
python3 tools/build_number_ledger.py --check || rc=1
python3 tools/build_value_ledger.py --check || rc=1
python3 tools/build_table_ledger.py --check || rc=1

echo
section "── references by meaning (does a number point at what the text names?) ─"
# reference_lint asks whether a number RESOLVES. These two ask whether it points
# at the right thing, which is a different question and the one that was missed:
# on 2026-08-23 nine table references and fifteen figure references were wrong
# while every resolution check was green (D-068). Both read evidence the corpus
# already carries — the script named beside a figure, the figure cited beside a
# section — and neither guesses.
# Run twice, as symbol_check above does: a pipeline's exit status is grep's, so
# `tool | grep || rc=1` gates on whether the GREP matched, not on the tool.
# section_ref_audit scores against tools/section_map.csv and cannot tell a stale
# map from a current one; this can. Regenerated by refresh_mirrors 1.2.0. Since
# 1.3.0 the same call checks the meaning snapshot (section_map_snapshot.csv).
python3 tools/section_map.py --check || rc=1
refaudit_out="$(python3 tools/ref_audit.py 2>&1)" || rc=1
printf '%s\n' "$refaudit_out" | grep -E "^   DISAGREES|^ref_audit:" || true
sectionrefaudit_out="$(python3 tools/section_ref_audit.py 2>&1)" || rc=1
printf '%s\n' "$sectionrefaudit_out" | grep -E "^  reference forms|^      [A-Z§]|^section_ref_audit:|disagree" || true

echo
section "── exports (is each published PDF newer than its sources?) ──────────"
# ADVISORY. A PDF export is slow and manual, and a gate firing between every ODT
# edit and the next export gets switched off inside a week — the same reasoning
# check_all already applies to pipeline_lint's literal check. It prints loudly
# instead, and figref_lint REFUSES outright rather than linting a stale export.
# --no-pages: export_lag 1.1.0 also compares the gh-pages branch against the
# working tree, and that section belongs at PUSH time, not here. Its lines do
# not match the grep below, so running it here would produce a check whose
# output is silently discarded — which is the one thing this file must never
# do. It runs in nrg_git.sh do_push instead, after the push, where the answer
# is actionable: `nrg_git.sh` option 13 republishes.
python3 tools/export_lag.py --no-pages | grep -E "^  (STALE|MISSING|UNMAPPED|UNBUILT)|behind their sources" || true

# export_lag asks whether each PDF is newer than its ODT. This asks the same
# question one layer down: whether a script has changed since the outputs in
# outputs/ were produced. Nothing asked it until 2026-08-27, so a script could be
# edited, committed and pushed while the corpus quoted the previous version's
# numbers with every gate green.
#
# A GATE since 2026-08-31 (D-102), not advice. It was advisory because it cannot
# tell a coefficient change from a docstring edit, and a check that cries stale
# over comments is one people learn to skip. What changed is that the cost of the
# false positive is now one command — re-run the script — while the cost of the
# false negative was demonstrated: 24b_residual_climatology.py is an OPT-IN step,
# `--full` does not run it, and it sat with edited code and outputs from the
# previous version while every other gate read green. No other check in this file
# can see that, because every one of them reads the outputs and finds them
# self-consistent. The pre-commit run is therefore
# `python3 run_analysis.py --full --with-supplementary`, and this is the gate
# that enforces it.
python3 tools/output_lag.py --quiet --gate || rc=1

echo
section "── input provenance (do the outputs match the committed INPUTS?) ────"
# W132: output_lag watches script->output; this watches input->output. A raw
# record can change under a corpus of committed numbers with every other gate
# green (the D-115 case). Skips cleanly until run_analysis.py records the
# hashes. --selftest first, because a green gate proves nothing if its
# detection has stopped working.
python3 tools/input_provenance_lint.py --selftest >/dev/null || rc=1
python3 tools/input_provenance_lint.py --gate || rc=1

echo
section "── step provenance (was each output made from the committed upstream?) ─"
# S1: D-133 records what the pipeline STARTED from; this records what each step
# READ from other steps and whether it fell back on a default. The remedy a
# failure names is the step to re-run, never skipping the check (D-102).
python3 tools/provenance_lint.py --selftest >/dev/null || rc=1
python3 tools/provenance_lint.py || rc=1

echo
section "── archive (are the canonical documents anywhere but this disk?) ─────"
# Advisory, like export_lag and for the same reason: an rclone copy is slow and
# manual. But it is the only check on the ONE risk the .gitignore creates - the
# .odt/.odm documents are in no repository, so between an edit and the next sync
# they exist once. MACHINE_SETUP.md told a new machine to touch .last_drive_archive
# and nothing ever read it; this is the check that marker was written for.
python3 tools/drive_lag.py || true

echo
section "── asserted claims ──────────────────────────────────────────────────"
python3 tools/cite_check.py --claims-only || rc=1
python3 tools/cite_check.py --selftest-claims >/dev/null || { echo "  cite_check --selftest-claims: FAIL"; rc=1; }

echo
section "── citation drift (confirmed rows must match the committed CSV) ──────"
# Gate added 2026-09-19: the confirmed-citation index-check. cite_check exits
# non-zero when a CONFIRMED citation no longer renders equal to its committed
# value. This is the drift that caught the 13 stale Sy citations; it was run
# advisory-only before, so confirmed drift passed green (W101/D-006, for prose).
python3 tools/cite_check.py --index-only || rc=1

echo
section "── citations (advisory: full triage list, does not gate) ─────────────"
# The claims gate above is instant. This triage LINE runs the full sweep —
# 1,700 committed values against 30 documents — and since the minus-tolerant
# match and the constants sources landed it takes the best part of a minute,
# which is enough to put check_all over the desktop bridge's ceiling. Same
# treatment as refresh_mirrors --verify: out of the chain, one line saying how
# to ask for it.
if [ "${CITE_TRIAGE:-0}" = "1" ]; then
    python3 tools/cite_check.py 2>/dev/null | grep "value(s) cited" || true
else
    echo "  (full citation triage, on demand: python3 tools/cite_check.py)"
fi

echo
_sec_write_summary
[ "$_total_rc" = "0" ] && echo "check_all: OK" || echo "check_all: FAIL"
exit "$_total_rc"
