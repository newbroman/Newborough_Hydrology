#!/usr/bin/env bash
# ============================================================================
# nrg_git.sh - Newborough git toolkit.
# Safe order of operations: COMMIT your work first, THEN pull, THEN push.
# Handles the "local changes would be overwritten by merge" situation.
# ============================================================================
# VERSION 1.6.0 - 2026-08-16
# CHANGELOG
#   1.6.0 (2026-08-16): menu 9) "Review citations" wired in.
#       * review_citations_menu() - walks the proposed rows of
#         tools/citation_index.csv, showing each cited number in its live
#         context with the section heading it sits under and a unique find
#         string to paste into LibreOffice, and records confirm/reject. Offers
#         the headline cluster-coefficient table (03_03) as the default subset,
#         since those are the values that actually went stale in report9 and
#         Paper 1. Curation, not a preflight: it is deliberately NOT run before
#         a push, because it needs judgement and would otherwise be skipped.
#       * Menu renumbered to 1-10; Quit is now 10.
#   1.5.0 (2026-08-16): decision logging plumbed into the push path.
#       * check_decisions() - new preflight in do_push and do_push_no_report.
#         Runs tools/decision_lint.py, which fails when a changelog delta dated
#         on or after the log's start names no D-nnn and does not say "no
#         decision", when a referenced D-nnn is absent from DECISION_LOG.md,
#         when the claims register cites an id that does not resolve, or when an
#         entry lacks Question/Decision/Rationale/Revisit-if. Unlike the other
#         audits this one PROMPTS rather than merely warning: an unrecorded
#         decision is the failure the log exists to prevent, and a silent
#         warning is how it would go unrecorded. Answer y to override.
#       * commit_staged() now asks for the decision ids the commit relates to
#         and appends them as a "Decisions:" trailer on the commit message, so
#         the link survives in git history and is greppable
#         (git log --grep='Decisions: D-005'). Entered ids are validated against
#         DECISION_LOG.md; "none"/blank is accepted and recorded as "none", so
#         the answer is always explicit. Never blocks a commit.
#       * refresh_mirror() now runs tools/refresh_mirrors.py, which mirrors the
#         report chapters AND the Methods Supplement, Supplementary Material and
#         both papers, resolving each versioned document to its highest version.
#         report_edits/make_text_mirror.sh covered the chapters only and is
#         SUPERSEDED - retire it rather than leaving two mirror generators that
#         can disagree. Falls back to the old script if the new one is absent.
#   1.4.0 (2026-08-12): stale .git/index.lock self-heal. New clear_stale_lock()
#       helper removes a leftover .git/index.lock when one is present AND no git
#       process is actually running - the safe definition of "stale". Called once
#       before the menu (so 5) Status works on launch) and at the top of do_push,
#       do_push_no_report, do_sync and integrate. Fixes the recurring "Unable to
#       create '.git/index.lock': File exists" failure: git run through the Cowork
#       device bridge can create the lock but not delete it, leaving a stale lock
#       that blocked the next real run. Never removes a live lock (a running git
#       process is detected and left alone).
#   1.3.0 (2026-08-12): three tools/ wired in.
#       * build_docs_pdfs() - a new pre-push preflight in do_push, do_push_no_report
#         and do_sync. Runs tools/build_pdfs.sh, which rebuilds each published PDF
#         from the latest versioned working ODT to the STABLE index.html filename,
#         but ONLY when that ODT is newer than its PDF - so it is a no-op when
#         nothing changed and never adds spurious binary diffs. report.pdf excepted
#         (that stays the hand-exported .odm). Warn-only; a missing LibreOffice or a
#         doc open in the GUI never blocks a push.
#       * audit_doc_numbers() - a warn-only step in do_push and do_push_no_report.
#         Runs tools/audit_number_drift.py --old origin/main to flag any document
#         still quoting a superseded pipeline number. Over-reports by design, so it
#         warns and never blocks. Skipped before the first fetch (no origin/main).
#       * menu 8) "Normalise script versions" - dry-run report from
#         tools/normalise_versions.py (edits nothing; --apply is run by hand).
#         Menu renumbered to 1-9; Quit is now 9.
#   1.2.0 (2026-08-09): new menu option 3, "Push, skip report". Pushes
#       everything EXCEPT report_edits/ and docs/report/, and skips the two
#       report preflight steps - refresh_mirror (regenerates ~700 KB of
#       markdown from 10 subdocuments) and lint_figrefs (reads the 57 MB
#       exported PDF). For the common case of pushing a script, output or
#       web-tool change while the report is mid-edit, where neither preflight
#       is relevant and a half-finished chapter must not ride along. Still
#       runs sync_index_counts and stage_web_tools. Reports what it held back
#       so skipped report changes cannot be forgotten. Menu renumbered to
#       1-8; Pull/Status/Size/Cleanup/Quit each shift down by one.
#   1.1.0 (2026-08-09): sync_index_counts() now regenerates
#       outputs/pipeline_manifest.json (--manifest-only, runs no analysis
#       steps) BEFORE stamping index.html. The manifest is only rewritten
#       when the pipeline runs, so a change to the step table could sit
#       unreflected in the manifest - and therefore in index.html - until the
#       next full run. Drift warnings from the orchestrator's document-count
#       guard are surfaced here rather than swallowed; the routine "Wrote..."
#       confirmation is hidden. A failed refresh warns and stamps from the
#       committed manifest rather than blocking the push. do_sync() now also
#       stages outputs/pipeline_manifest.json, which its explicit git-add list
#       previously missed (do_push picks it up via stage_all). Comment above
#       sync_index_counts() rewritten: it quoted the retired "46 analytical
#       steps" headline, deleted in run_analysis.py v2.3.0.
#   1.0.0 - prior state (unversioned).
# ============================================================================
set -uo pipefail

REPO_DIR="${HOME}/projects/NRG"
LIVING="${REPO_DIR}/living"
HUB="${LIVING}/readings_living.csv"
CLUSTER_MAP="${REPO_DIR}/outputs/03_master_data.csv"
FEED_JSON="${LIVING}/latest_readings.json"
MSL5_JSON="${LIVING}/forecaster_msl5.json"
INDICES_JSON="${LIVING}/forecaster_indices.json"
EWI_CSV="${REPO_DIR}/outputs/26_van_willegen_msl/26_equilibrium_wetness_index_per_well.csv"
EBF_CSV="${REPO_DIR}/outputs/26_van_willegen_msl/26_ebf_comparison.csv"
SCATTER_SRC="${REPO_DIR}/outputs/14_climate_projections/14_seasonal_extremes_scatter.html"
SCATTER_DST="${REPO_DIR}/seasonal_extremes_scatter.html"
VIEWER_SRC="${REPO_DIR}/outputs/19_spatial_groundwater/scenario_viewer.html"
VIEWER_DST="${REPO_DIR}/scenario_viewer.html"

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; C='\033[0;36m'; B='\033[1m'; N='\033[0m'
say(){  echo -e "\n${C}-- $1 --${N}"; }
ok(){   echo -e "  ${G}OK${N} $1"; }
fail(){ echo -e "  ${R}x $1${N}"; }

cd "${REPO_DIR}" 2>/dev/null || { echo -e "${R}Can't find ${REPO_DIR}${N}"; read -rp "Press Enter to close"; exit 1; }

# --- helpers ---------------------------------------------------------------
stage_all(){ git add -A; }

# --- stale index.lock guard ------------------------------------------------
# A git run through the Cowork device bridge (or any crashed git) can leave
# .git/index.lock behind: on the bridge's mount git can create the lock but not
# remove it, so the next real git command dies with "Unable to create
# '.../index.lock': File exists". This toolkit runs on your own machine where rm
# works, so if the lock is present AND no git process is actually running, it is
# stale - clear it before any git action. It never removes a live lock.
clear_stale_lock(){
  local lock="${REPO_DIR}/.git/index.lock"
  [[ -e "$lock" ]] || return 0
  if pgrep -x git >/dev/null 2>&1; then
    echo -e "  ${Y}note${N} a git process is running - leaving .git/index.lock alone"
    return 0
  fi
  rm -f "$lock" && ok "cleared a stale .git/index.lock (safe: no git process was running)"
}

# Stage everything EXCEPT the report. report_edits/ holds the .odt subdocuments
# and their markdown mirror; docs/report/ holds the exported PDF (57 MB). Both
# are excluded so a half-finished chapter never rides along with a script or
# output change, and so the slow mirror refresh can be skipped. Defined once so
# the exclusion list cannot drift between the two functions below.
REPORT_PATHS=( "report_edits" "docs/report" )
stage_all_but_report(){
  local excludes=() p
  for p in "${REPORT_PATHS[@]}"; do excludes+=( ":(exclude)${p}" ); done
  git add -A -- . "${excludes[@]}"
}

# True (0) when the report has uncommitted changes being deliberately held back.
report_has_changes(){
  local p
  for p in "${REPORT_PATHS[@]}"; do
    [[ -e "$p" ]] || continue
    git status --porcelain -- "$p" | grep -q . && return 0
  done
  return 1
}
have_staged(){ ! git diff --cached --quiet; }   # true (0) when something is staged

# Ask which decisions a commit relates to and record them as a git trailer, so
# the link between a change and its rationale survives in history and is
# greppable:  git log --grep='Decisions: D-005'
# Ids are validated against DECISION_LOG.md. Blank or "none" is accepted and
# recorded as "none" - the answer is always explicit, so a commit that encoded
# no decision is distinguishable from one where nobody was asked. Never blocks.
decision_trailer(){
  local log="DECISION_LOG.md" ans ids=() bad=() id
  [[ -f "$log" ]] || { echo ""; return 0; }
  read -rp "$(echo -e "${Y}Decision ids this relates to (e.g. D-005 D-011, or Enter for none): ${N}")" ans
  [[ -z "$ans" || "$ans" =~ ^([Nn]one|[Nn])$ ]] && { echo "none"; return 0; }
  for id in $ans; do
    id="${id%,}"
    if grep -q "^### ${id}\b" "$log"; then ids+=( "$id" ); else bad+=( "$id" ); fi
  done
  if (( ${#bad[@]} )); then
    echo -e "  ${Y}note${N} not in DECISION_LOG.md: ${bad[*]} - recorded anyway, add the entry" >&2
    ids+=( "${bad[@]}" )
  fi
  ( IFS=", "; echo "${ids[*]}" )
}

commit_staged(){                                # $1 = message; prompt if empty
  local msg="$1" dec
  if [[ -z "$msg" ]]; then
    read -rp "$(echo -e "${Y}Short description of these changes: ${N}")" msg
    [[ -z "$msg" ]] && msg="update $(date +%Y-%m-%d)"
  fi
  dec="$(decision_trailer)"
  if [[ -n "$dec" ]]; then
    git commit -m "$msg" -m "Decisions: ${dec}"
  else
    git commit -m "$msg"
  fi
}

handle_conflicts(){                             # called when a pull conflicts
  local conflicted
  conflicted=$(git diff --name-only --diff-filter=U)
  [[ -z "$conflicted" ]] && return 0
  fail "Merge conflict - these files were changed both on your PC and on GitHub:"
  echo "$conflicted" | sed 's/^/      /'
  echo ""
  echo "  How do you want to resolve them?"
  echo -e "    ${B}k${N}) Keep GitHub's version   (usual choice when the pipeline pushed updated scripts)"
  echo -e "    ${B}m${N}) Keep My version         (when your local copy is the one to keep)"
  echo -e "    ${B}a${N}) Abort                   (undo the merge, change nothing, get help)"
  echo ""
  read -rp "Choose [k/m/a]: " cr
  case "$cr" in
    k|K) while IFS= read -r f; do [[ -n "$f" ]] && git checkout --theirs -- "$f" && git add "$f"; done <<< "$conflicted"
         git commit --no-edit && ok "kept GitHub's versions - merge complete"; return 0 ;;
    m|M) while IFS= read -r f; do [[ -n "$f" ]] && git checkout --ours   -- "$f" && git add "$f"; done <<< "$conflicted"
         git commit --no-edit && ok "kept your versions - merge complete"; return 0 ;;
    *)   git merge --abort; fail "merge aborted - nothing changed. Your committed work is safe."; return 1 ;;
  esac
}

integrate(){                                    # pull remote in; assumes clean/committed tree
  clear_stale_lock
  say "Pulling latest from GitHub"
  if git pull origin main --no-rebase --no-edit; then ok "merged with GitHub"; return 0
  else handle_conflicts; return $?; fi
}

push_if_ahead(){                                # push only if we have commits GitHub doesn't
  local ahead
  ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
  if [[ "$ahead" == "0" ]]; then ok "GitHub already up to date - nothing to push."; return 0; fi
  say "Ready to push ${ahead} commit(s) to GitHub"
  git log --oneline origin/main..HEAD | sed 's/^/      /'
  echo ""
  read -rp "$(echo -e "${Y}Push now? [y/N]: ${N}")" r
  if [[ "$r" =~ ^[Yy] ]]; then
    git push && echo -e "  ${G}${B}Pushed.${N} Pages refreshes in a minute or two." || fail "push failed - choose 5) Status."
  else
    echo "  Not pushed. Your commit is saved locally - run the option again when ready."
  fi
}

# --- main actions ----------------------------------------------------------

# --- report_edits: refresh the markdown mirror before staging -----------------
# The .odt subdocuments are gitignored (two are ~200 MB). Their markdown mirror
# under report_edits/text/ is the ONLY versioned record of their content, and
# the only way a reader (or Claude) sees subdocument edits. Regenerate it before
# every commit so the mirror can never silently drift from the .odt files.
refresh_mirror(){
  say "Refreshing document text mirrors"
  # tools/refresh_mirrors.py supersedes report_edits/make_text_mirror.sh: same
  # pandoc conversion, but it also mirrors the Methods Supplement, Supplementary
  # Material and both papers, and resolves versioned documents to the highest
  # version so a filename bump is picked up without editing anything.
  local rc=0
  if [[ -f "tools/refresh_mirrors.py" ]] && command -v python3 >/dev/null 2>&1; then
    python3 tools/refresh_mirrors.py || rc=1
  else
    local script="report_edits/make_text_mirror.sh"
    [[ -x "$script" ]] || return 0              # nothing to do if absent
    "$script" || rc=1
  fi
  if [[ "$rc" == "0" ]]; then
    ok "mirrors up to date"
  else
    fail "mirror refresh failed - .odt changes would NOT be recorded"
    read -rp "$(echo -e "${Y}Continue anyway? [y/N]: ${N}")" r
    [[ "$r" =~ ^[Yy]$ ]] || return 1
  fi
}


# --- report_edits: lint figure references against the exported PDF -----------
# Captions in report.odm auto-number correctly; the in-text references are typed
# by hand and drift when a figure is added or removed. figref_lint.py reads the
# exported PDF and reports gaps/duplicates in the caption sequence and any
# reference to a figure number that has no caption. It WARNS but never blocks:
# a stale or missing PDF must not stop an unrelated commit. Semantic mistakes
# (a reference pointing at the wrong existing figure) are NOT caught here.
lint_figrefs(){
  local script="report_edits/figref_lint.py"
  [[ -f "$script" ]] || return 0
  # Prefer a PDF exported into report_edits/; fall back to the published one.
  local pdf=""
  for cand in report_edits/report.pdf report_edits/report_edits.pdf report_edits/report_draft.pdf docs/report/report.pdf; do
    [[ -f "$cand" ]] && { pdf="$cand"; break; }
  done
  [[ -n "$pdf" ]] || { echo -e "  ${Y}note${N} no report PDF found - skipping figure-reference lint"; return 0; }
  command -v python3 >/dev/null 2>&1 || return 0
  say "Linting figure references ($pdf)"
  if python3 "$script" "$pdf"; then
    ok "figure references consistent"
  else
    fail "figure-reference problems (see above) - the PDF may be stale; re-export report.odm"
    echo -e "  ${Y}(warning only - not blocking your push)${N}"
  fi
}

# --- web tools: keep the served root copies in step with outputs/ ------------
# scenario_viewer.html and seasonal_extremes_scatter.html are generated into
# outputs/ by Scripts 19 and 14, but GitHub Pages serves the copies at the repo
# root. Until 2026-08-07 this copy ran only in do_sync (menu 1, monthly), so a
# script rerun pushed via do_push (menu 2) updated outputs/ and left the served
# page stale - which is how the viewer sat at v2.8.1 while outputs/ was v2.9.0
# for a day. Both paths now call this, so the served copy can never lag a push.
# forecaster.html is deliberately NOT staged here. index.html links the copy
# under outputs/11b_spatial_thresholds/, and that is the only one that works:
# the page pulls its live feeds with relative URLs ("../../living/*.json"),
# which resolve off-site from the repo root. A root copy therefore renders with
# no readings. Briefly added and reverted 2026-08-18.
# Reports "refreshed" only when the file actually changed, so a real update is
# visible rather than buried in a list of no-ops.
stage_web_tools(){
  say "Staging web tools to root"
  local pair src dst name changed=0
  for pair in "$SCATTER_SRC|$SCATTER_DST" "$VIEWER_SRC|$VIEWER_DST"; do
    src="${pair%%|*}"; dst="${pair##*|}"; name="$(basename "$dst")"
    if [[ ! -f "$src" ]]; then
      echo "  (no source for ${name} - skipped)"
    elif [[ -f "$dst" ]] && cmp -s "$src" "$dst"; then
      echo "  ${name} already current"
    else
      cp -f "$src" "$dst" && { echo -e "  ${G}refreshed${N} ${name}"; changed=1; } \
                          || fail "could not copy ${name}"
    fi
  done
  [[ "$changed" == "1" ]] && echo -e "  ${Y}note${N} a served page changed - remember to push, or Pages stays stale."
  return 0
}

# --- index.html: keep the pipeline counts in step with the manifest ----------
# index.html is hand-maintained and is the only project document that states
# the pipeline counts without quoting outputs/pipeline_manifest.json. Its
# numbers sit inside <!--PL:key--> markers and are stamped from the manifest
# here. Two failures this guards against, both of which have happened:
#   * a marker going stale because nobody remembered to run the stamper;
#   * the manifest ITSELF going stale, because it is only rewritten when the
#     pipeline runs - so a change to the step table can sit unreflected in
#     both manifest and page until the next full run. --manifest-only closes
#     that gap: it rebuilds the manifest from the step table and executes no
#     analysis steps.
# Drift warnings from the orchestrator's document-count guard are printed here
# (they name which documents now disagree with the step table). WARNS but never
# blocks: neither a stale manifest nor a failed refresh should stop a push.
sync_index_counts(){
  local script="tools/sync_index_counts.py"
  [[ -f "$script" ]] || return 0
  command -v python3 >/dev/null 2>&1 || return 0
  say "Syncing index.html pipeline counts"
  if [[ -f "run_analysis.py" ]]; then
    local mout mrc
    mout=$(python3 run_analysis.py --manifest-only 2>&1); mrc=$?
    if [[ "$mrc" -ne 0 ]]; then
      echo -e "  ${Y}note${N} could not refresh the manifest - stamping from the committed copy"
    else
      # Hide the routine "Wrote ..." confirmation; surface anything else,
      # which is the document-count drift guard telling you what to update.
      echo "$mout" | grep -v "pipeline_manifest.json" | grep -v "^[[:space:]]*$" | sed 's/^/  /'
    fi
  fi
  if python3 "$script"; then
    :
  else
    fail "index.html counts not synced (see above)"
    echo -e "  ${Y}(warning only - not blocking your push)${N}"
  fi
  return 0
}

# --- published PDFs: rebuild any whose ODT changed, before staging ------------
# tools/build_pdfs.sh exports each versioned working ODT to the STABLE published
# filename index.html serves (report.pdf excepted - that is the hand-exported .odm).
# It rebuilds ONLY stale PDFs (ODT newer than its PDF), so it is a no-op when
# nothing changed and never creates spurious binary diffs. Warns but never blocks:
# a missing LibreOffice or a doc still open in the GUI must not stop a push.
build_docs_pdfs(){
  local script="tools/build_pdfs.sh"
  [[ -f "$script" ]] || return 0
  command -v soffice >/dev/null 2>&1 || command -v libreoffice >/dev/null 2>&1 || {
    echo -e "  ${Y}note${N} LibreOffice not found - skipping published-PDF rebuild"; return 0; }
  say "Rebuilding stale published PDFs"
  if bash "$script"; then :; else
    fail "PDF rebuild reported a problem (is a doc open in LibreOffice? close it and retry)"
    echo -e "  ${Y}(warning only - not blocking your push)${N}"
  fi
  return 0
}

# --- documents: warn if any quote a superseded pipeline number ---------------
# tools/audit_number_drift.py diffs committed CSV cells between origin/main (the
# last published state) and the working tree, then searches the document corpus
# for the OLD value where the new one differs. It OVER-REPORTS by design, so every
# hit needs eyeballing - hence warn-only, never blocking. Skipped when origin/main
# is unavailable (fresh clone before first fetch).
audit_doc_numbers(){
  local script="tools/audit_number_drift.py"
  [[ -f "$script" ]] || return 0
  command -v python3 >/dev/null 2>&1 || return 0
  git rev-parse --verify -q origin/main >/dev/null 2>&1 || {
    echo -e "  ${Y}note${N} no origin/main ref yet - skipping number-drift audit"; return 0; }
  say "Auditing documents for superseded pipeline numbers (origin/main -> working tree)"
  python3 "$script" --old origin/main || true
  echo -e "  ${Y}(warning only - triage any hits above; the tool over-reports by design)${N}"
  return 0
}

# --- citations: confirm which document numbers cite which pipeline value ------
# tools/cite_check.py can only check a citation EXACTLY once somebody has
# confirmed that a given number in a given document really is a given pipeline
# value. The builder proposes those links; roughly half are coincidences,
# because in a corpus this dense with per-well tables the same three digits can
# be a cluster mean in one sentence and a variance inflation factor in the next.
# This walks the proposals and records the answers. Confirmed rows then gate the
# push through check_decisions' sibling check; unreviewed rows only advise.
review_citations_menu(){
  local script="tools/review_citations.py"
  [[ -f "$script" ]] || { echo "  (tools/review_citations.py not found)"; return 0; }
  command -v python3 >/dev/null 2>&1 || { echo "  (python3 not found)"; return 0; }
  if [[ ! -f "tools/citation_index.csv" ]]; then
    say "No citation index yet - building one"
    python3 tools/build_citation_index.py || return 0
  fi
  echo ""
  echo "  Which citations do you want to review?"
  echo -e "    ${B}1${N}) Headline cluster coefficients (03_03)  - recommended first pass"
  echo -e "    ${B}2${N}) One document (you type part of its name)"
  echo -e "    ${B}3${N}) Everything still proposed"
  echo -e "    ${B}b${N}) Back"
  echo ""
  local pick doc
  read -rp "Choose [1/2/3/b]: " pick
  case "$pick" in
    1) python3 "$script" --source 03_03 ;;
    2) read -rp "$(echo -e "${Y}Document name fragment (e.g. report9): ${N}")" doc
       [[ -n "$doc" ]] && python3 "$script" --document "$doc" ;;
    3) python3 "$script" ;;
    *) return 0 ;;
  esac
}

# --- decisions: refuse to push an unrecorded methodological call --------------
# DECISION_LOG.md records WHY a call was made; tools/decision_lint.py makes the
# omission mechanical (see its docstring). This is the ONE audit here that
# prompts instead of merely warning. The others flag things that are wrong and
# fixable later; an unrecorded decision is different, because the reason is lost
# at the moment the session ends and cannot be reconstructed afterwards - which
# is precisely how the C4 triangulation was reintroduced weeks after being
# retired on evidence, and how the 100-month window changed meaning with nobody
# deciding it. Answering y records nothing and pushes anyway; that is your call
# to make knowingly rather than by default.
check_decisions(){
  local script="tools/decision_lint.py"
  [[ -f "$script" ]] || return 0
  command -v python3 >/dev/null 2>&1 || return 0
  say "Checking the decision log"
  if python3 "$script" --quiet; then
    ok "decision log consistent"
    return 0
  fi
  fail "decision log check failed (see above)"
  echo -e "  ${Y}A change may encode a decision that nobody has written down.${N}"
  echo    "  Add an entry to DECISION_LOG.md, or name the decision in the changelog"
  echo    "  delta (or say 'no decision' in it), then run this again."
  local r
  read -rp "$(echo -e "${Y}Push anyway without recording it? [y/N]: ${N}")" r
  [[ "$r" =~ ^[Yy] ]] && { echo -e "  ${Y}proceeding unrecorded${N}"; return 0; }
  return 1
}

# --- deliberate: report console version-reporting drift (dry run, edits nothing)
normalise_versions_report(){
  local script="tools/normalise_versions.py"
  [[ -f "$script" ]] || { echo "  (tools/normalise_versions.py not found)"; return 0; }
  command -v python3 >/dev/null 2>&1 || { echo "  (python3 not found)"; return 0; }
  say "Console version-reporting audit (dry run - edits nothing)"
  python3 "$script" || true
  echo -e "  ${Y}note${N} report only. To apply the fixes:  python3 tools/normalise_versions.py --apply"
}

do_push(){
  clear_stale_lock
  refresh_mirror || return
  lint_figrefs
  audit_doc_numbers
  check_decisions || { fail "push cancelled - record the decision first"; return; }
  sync_index_counts
  stage_web_tools
  build_docs_pdfs
  stage_all
  if have_staged; then
    say "Your local changes (committing these first)"
    git status --short
    echo ""
    commit_staged "" || { fail "commit failed"; return; }
    ok "committed on your PC"
  else
    ok "no new local changes to commit"
  fi
  integrate || return
  push_if_ahead
}

# Push everything except the report. Skips refresh_mirror and lint_figrefs -
# the two report preflight steps - and holds report_edits/ and docs/report/ out
# of the commit. Note this NEVER pushes the report, so docs/report/report.pdf
# will go stale on GitHub if only this option is ever used; option 2 remains
# the one that ships everything.
do_push_no_report(){
  clear_stale_lock
  audit_doc_numbers
  check_decisions || { fail "push cancelled - record the decision first"; return; }
  sync_index_counts
  stage_web_tools
  build_docs_pdfs
  stage_all_but_report
  if have_staged; then
    say "Your local changes, excluding the report"
    git status --short -- . ":(exclude)report_edits" ":(exclude)docs/report"
    echo ""
    commit_staged "" || { fail "commit failed"; return; }
    ok "committed on your PC"
  else
    ok "no new non-report changes to commit"
  fi
  if report_has_changes; then
    echo ""
    echo -e "  ${Y}held back${N} - the report still has uncommitted changes:"
    git status --short -- "${REPORT_PATHS[@]}" | sed 's/^/      /'
    echo -e "      run ${B}2) Push my changes${N} when you want those included."
  fi
  integrate || return
  push_if_ahead
}

do_sync(){
  clear_stale_lock
  # 1) commit any stray local edits FIRST, so the pull can't be blocked
  stage_all
  if have_staged; then
    say "You have other local changes - committing them first"
    git status --short
    echo ""
    commit_staged "" || { fail "commit failed"; return; }
  fi
  # 2) get latest from GitHub
  integrate || return
  # 3) rebuild the live outputs
  sync_index_counts
  stage_web_tools
  build_docs_pdfs
  say "Rebuilding forecaster feeds from the hub"
  python3 "$LIVING/update_forecaster_feed.py" --hub "$HUB" --cluster-map "$CLUSTER_MAP" --out "$FEED_JSON"  || { fail "feed build failed"; return; }
  python3 "$LIVING/update_forecaster_msl5.py" --hub "$HUB" --cluster-map "$CLUSTER_MAP" --out "$MSL5_JSON" || { fail "MSL5 build failed"; return; }
  # The indices feed is built from Script 26 outputs rather than the hub, so it
  # goes stale on a pipeline rerun rather than on a monthly reading. It was
  # missing from this block until 2026-08-18 and sat nine days behind the other
  # two feeds; rebuilding it here is idempotent when Script 26 has not moved.
  if [[ -f "$EWI_CSV" && -f "$EBF_CSV" ]]; then
    python3 "$LIVING/update_forecaster_indices.py" --ewi "$EWI_CSV" --ebf "$EBF_CSV" --out "$INDICES_JSON" \
      || fail "indices build failed (warning only - the other two feeds stand)"
  else
    echo "  (Script 26 outputs not present - indices feed left as is)"
  fi
  git add "$HUB" "$FEED_JSON" "$MSL5_JSON" "$INDICES_JSON" "$SCATTER_DST" "$VIEWER_DST" index.html \
          outputs/pipeline_manifest.json
  if have_staged; then
    git commit -m "monthly forecaster update $(date +%Y-%m)" && ok "feeds committed"
  else
    ok "feeds unchanged - nothing new to commit"
  fi
  # 4) push
  push_if_ahead
}

do_size(){
  say "Repository size"
  local total dotgit nfiles tsize
  total=$(du -sh --exclude=.git "$REPO_DIR" 2>/dev/null | cut -f1)
  dotgit=$(du -sh "$REPO_DIR/.git" 2>/dev/null | cut -f1)
  nfiles=$(git ls-files | wc -l | tr -d ' ')
  tsize=$(git ls-files -z | du -ch --files0-from=- 2>/dev/null | tail -1 | cut -f1)

  echo "  On your disk:"
  echo "    Working tree (all your files):    ${total:-?}"
  echo "    Git storage (.git folder):        ${dotgit:-?}"
  echo ""
  echo "  Tracked by git (what gets pushed / cloned):"
  echo "    Files tracked:                    ${nfiles:-?}"
  echo "    Their total size:                 ${tsize:-?}"
  echo ""
  echo "  Biggest top-level folders on disk:"
  du -sh "$REPO_DIR"/*/ 2>/dev/null | sort -rh | head | sed 's/^/      /'
  echo ""
  echo -e "  ${Y}Note:${N} working-tree size includes gitignored folders (venv/, Living_output/)"
  echo "  that stay on your machine and are never pushed. The 'tracked' figures above"
  echo "  are what actually lives in the repo. If .git is far bigger than the tracked"
  echo "  size, sweep up dead objects with:  git gc --prune=now"
}

do_cleanup(){
  say "Clean up git storage"
  local before after
  before=$(du -sh "$REPO_DIR/.git" 2>/dev/null | cut -f1)
  echo "  Current .git size: ${before:-?}"
  echo "  This sweeps up unreferenced (dead) objects. It does NOT touch your files,"
  echo "  your commits, or anything on GitHub - purely local housekeeping."
  echo ""
  read -rp "$(echo -e "${Y}Run cleanup now? [y/N]: ${N}")" r
  [[ "$r" =~ ^[Yy] ]] || { echo "  Skipped."; return; }
  rm -f "$REPO_DIR/.git/gc.log"
  git gc --prune=now && ok "first pass done" || fail "gc reported a problem"
  after=$(du -sh "$REPO_DIR/.git" 2>/dev/null | cut -f1)
  echo -e "  .git size now: ${B}${after:-?}${N}  (was ${before:-?})"
  echo ""
  read -rp "$(echo -e "${Y}Run the deeper sweep too (expire reflog + gc)? [y/N]: ${N}")" r2
  if [[ "$r2" =~ ^[Yy] ]]; then
    git reflog expire --expire=now --all && git gc --prune=now && ok "deep sweep done" || fail "deep sweep reported a problem"
    after=$(du -sh "$REPO_DIR/.git" 2>/dev/null | cut -f1)
    echo -e "  .git size now: ${B}${after:-?}${N}"
  fi
}

# --- menu ------------------------------------------------------------------
# Clear a stale lock left by an earlier Cowork/bridge session before the first
# menu action, so even 5) Status works on launch.
clear_stale_lock
while true; do
  echo ""
  echo -e "${C}${B}===== Newborough Git Toolkit =====${N}"
  echo "  1) Sync forecaster      (monthly: rebuild feeds + web tools, then push)"
  echo "  2) Push my changes      (commit + push anything I've edited OR added)"
  echo "  3) Push, skip report    (everything except report_edits/ and docs/report/)"
  echo "  4) Pull latest          (just fetch what's on GitHub)"
  echo "  5) Status               (show what's changed, untracked, etc.)"
  echo "  6) Repo size            (how big the repo and git history are)"
  echo "  7) Clean up git storage (sweep up dead objects, shrink .git)"
  echo "  8) Normalise versions   (dry-run report: script banner() vs __version__)"
  echo "  9) Review citations     (confirm which document numbers cite which pipeline value)"
  echo " 10) Quit"
  echo ""
  read -rp "Choose [1-10]: " choice
  case "$choice" in
    1) do_sync ;;
    2) do_push ;;
    3) do_push_no_report ;;
    4) integrate ;;
    5) say "Current status"; git status ;;
    6) do_size ;;
    7) do_cleanup ;;
    8) normalise_versions_report ;;
    9) review_citations_menu ;;
    10) echo "Bye."; break ;;
    *) echo "Please pick 1-10." ;;
  esac
done
