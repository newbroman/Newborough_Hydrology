# Job brief: build Script 55 (water-balance residual analysis) and the Script 18 windowed mode

**Queued job J-1** in the NRG HQ job queue. Fired when NRG HQ has shipped and `pipeline` is free.
**Written:** 2026-11-05, claude.ai chat session (Claude Opus 5.5). Self-contained: the session that
runs this starts with no memory of the conversation that produced the spec.

## Prompt for the session

Build Script 55 (water-balance residual analysis) and the Script 18 windowed mode, from the signed-off
spec: `notes/specs/NRG_spec_water_balance_diagnostic_2026-11-04.md` on branch
`notes/2026-11-04-water-balance-handovers` (also `claude/` in the project store). Read it in full
first. Decisions D1–D11 are signed off; do not reopen them.

Setup first:
1. `add_repo newbroman/Newborough_Hydrology access=push` and
   `add_repo newbroman/Newborough_Hydrology_working access=push`.
2. `tools/cloud_setup.sh` per `notes/reference/SESSION_MODES.md`, then the D-143 start
   (`working/HANDOVER_BOOTSTRAP.md`, `python3 tools/session_handover.py`).
3. Register this chat (NRG HQ registration, compulsory), run `python3 tools/work_board.py`, and take
   the `pipeline` claim only.

Then:
- Build per the spec. The scratch numbers in its §2 are the regression check: reproduce them to 3 d.p.
  where the method is unchanged, and explain any difference in the changelog.
- Also apply **T-135** (task register): the one-line `run_analysis.py` change so pipeline runs
  refresh the claim's `touched` time. The line is written out in changelog 2026-11-04g.
- Read every `report_numbers` key back from the written file; run `check_all` through `tee`, quote
  the verdict, and use `${PIPESTATUS[0]}` for the real exit code.
- Write the four decision-log entries listed in the spec (pull `main` first for the IDs).
- Ship, release `pipeline`, and mark J-1 done in the job queue.
- Hand the field keys on: J-2 (the Paper M §5.3 passages) becomes ready when this ships. The keys go to
  the chat holding `doc:PaperM`, which registers them before any prose.

Unattended rule: if a design question comes up that the spec does not answer, stop, set out the
question with your recommendation, and wait for Martin. Do not decide it.
