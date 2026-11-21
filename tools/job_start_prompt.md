<!-- job_start_prompt.md — the start prompt for a queued job, in ONE place (J-20, 2026-11-18).
     tools/job_queue.py start_prompt() fills it from the queue row; hq_snapshot.py writes the
     filled text into the job's db row (jobs/<id>.start_prompt) and the HQ page shows it with a
     Copy button; `job_queue.py ready` prints the same text. So the wording is edited HERE and
     nowhere else.

     Placeholders: {{id}} {{title}} {{brief}} {{claim}} {{kind}} {{note}}
     Blocks: <!--if claim--> ... <!--end-->   kept when the value is non-empty
             <!--if !claim--> ... <!--end-->  kept when it is empty
     Every HTML comment is stripped from the filled prompt, so this header never reaches a chat. -->
Run job {{id}}: read {{brief}} (PRIVATE repository) in full and follow it.

The job: {{title}}
<!--if note-->

What Martin said when he queued it: {{note}}
<!--end-->

Setup: both repositories are attached by this environment — do NOT call add_repo; a session that
asks for one stalls on the auto-mode check (J-17). Run tools/cloud_setup.sh for the Drive copy of
the ODTs and the pinned venv, in the background with its log tee'd, and read the log:

    mkdir -p scratch && nohup bash tools/cloud_setup.sh "$PWD" > scratch/cloud_setup.log 2>&1 &

Pass "$PWD" from the checkout: with no argument it builds a second tree at $HOME/NRG, which is not
the one the environment attached. It takes a few minutes and must not be time-limited.

Then, in this order:

1. Read working/HANDOVER_BOOTSTRAP.md and run `python3 tools/session_handover.py` (D-143).
2. Mark the job fired: `python3 tools/job_queue.py fire {{id}} --by "<this chat>"`
3. Register this chat — compulsory, before any claim or commit (D-301):
   `python3 tools/chat_register.py register --chat "<short name> {{id}}" --kind {{kind}} <!--if claim-->--claim {{claim}} <!--end-->--purpose "{{id}}: <one line>" --link "<this chat's URL>"`
   The kinds are pipeline, document, tools, readonly, fieldwork — "docs" is refused. The link is the
   Claude-Session URL your harness gives you for commit messages: it is what makes this chat
   clickable on the HQ page, so Martin can find it again to carry on or to archive it.
<!--if claim-->
4. Take this job's claim and nothing else:
   `python3 tools/doc_lock.py take {{claim}} --chat "<this chat>" --note "{{id}}"`
   A claim another chat holds is a refusal, not advice: say so and wait for Martin, never --force.
<!--end-->
<!--if !claim-->
4. The queue row names no claim: take whatever claim the brief names for the work you do, and
   nothing else. A claim another chat holds is a refusal, not advice.
<!--end-->
5. Before any ODT edit, take the documents lock too:
   `python3 tools/doc_lock.py take --chat "<this chat>" --note "{{id}}"`
6. `export NRG_CHAT="<the name you registered>"` in EVERY shell call.
7. Read CLAUDE.md before touching anything — it is the traps, not the overview.

Then the work in the brief, and:

- ODTs are edited only through tools/odt_edit.py, never odfpy, and they are versioned: edit
  Doc_v1_9_46.odt and WRITE Doc_v1_9_47.odt. Read the passage back from the SAVED file through
  headless LibreOffice with `txt:Text (encoded):UTF8` — plain `txt:Text` prints Greek as '?'.
- Run the gates through tee and quote the verdict in the commit message:
  `bash tools/check_all.sh 2>&1 | tee scratch/check_all.log; echo "rc ${PIPESTATUS[0]}"`
  A gate you did not touch going red is a stop sign, not something to work around.
- ASK MARTIN BEFORE EVERY PUSH. Commits are always allowed; reaching GitHub is his call each time
  (CLAUDE.md §7, D-324). The record pushes doc_lock, chat_register and job_queue make for
  themselves are the exemption (D-314) — a claim nobody can see is not a claim.
- If the ODTs changed, archive them to Drive (working/nrg_git.sh option 11, or a ship) BEFORE
  releasing the documents lock: the release is what tells the next machine Drive is current.
- End the session with a dated entry at the TOP of working/updates/HANDOVER_NOTE.md, a changelog
  delta under working/changelogs/, and `python3 tools/session_handover.py --write` with `--check`
  green.
- Then `python3 tools/job_queue.py done {{id}}`, `python3 tools/chat_register.py status --chat
  "<this chat>" --set done --outcome "<one line>"`, and release your claim — the release is what
  makes the next job ready, and it prints the line that fires it.

If a design question comes up that the brief does not answer, STOP, set it out with your
recommendation, and wait for Martin. Do not decide it.
