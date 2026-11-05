# Job brief: Paper M §5.3 and the §7.1 clause, from Script 55's outputs

**Queued job J-2** in the NRG HQ job queue (`working/job_queue.csv`). Ready when **J-1** is done —
that is, when Script 55 is on `main` with its outputs committed.

**Target `notify`, deliberately.** One session cannot message another, and the chat holding
`doc:PaperM` is the one that must make these edits: it holds the claim, it knows the version state,
and it is mid-pass on the plain companion. So this job does not start a session. It notifies Martin
with this brief, and he passes it to that chat — or, if `doc:PaperM` has been released by then, a
new session takes the claim and runs it.

**Written:** 2026-11-05 by the HQ build session (`tools`), from
`notes/specs/NRG_spec_water_balance_diagnostic_2026-11-04.md` §9, which is the signed-off document
plan. Nothing here is new editorial judgement; it is the plan's own instruction, made self-contained.

## What the work is

From the spec's §9, for Paper M only:

1. A short new **§5.3**, "Water-balance residual analysis: a fourth reading of the split", placed
   straight after §5.2's recession reading, which it complements. One figure (Stage B or D), detail
   in the SI.
2. **One added clause in §7.1**, beside §2.4's floor and §5.2's reading. The v1_42 wording of §7.1
   stands; this is an addition, not a rewrite. The clause frames the four readings by what each is
   free of:
   - §2.4's floor needs no datum, no fitted base and no Sy; it gives bounds only, and fails under
     canopy.
   - §5.2's recession ratio needs no datum and no Sy, but is a share of *summer recession*.
   - Models A and B give the annual-loss share, but each needs a datum or a fitted base, and they
     disagree.
   - The water balance gives the annual-loss share at the median well, but needs Sy — hence its
     bracket.
   The floor and the water balance bear on §7.1's quantity from opposite directions, and §5.2's
   independence of Sy stays its own virtue.
3. A sentence each in **§7.4** (the forest forcing reading) and **§8**.

## The renumber, which is the part that bites

Inserting §5.3 renumbers the current §5.3–§5.6 to §5.4–§5.7 and moves **six typed internal
references** (two to §5.4, one to §5.5, three to §5.6).

Run the renumber by CLAUDE.md §4d's recipe, in this order, because `reference_lint` **cannot see a
reference that moved twice** — twelve went undetected on 2026-09-20 for exactly that reason:

    plan pass  ->  tools/figure_map.py  ->  tools/repoint_verify.py
               ->  tools/reference_lint.py --snapshot  ->  tools/ref_audit.py

Draft the passages calling the new section **§5.3**, and name any later section by its **title as
well as** its post-renumber number, so a reader of the draft can tell which section is meant
whichever side of the renumber they are on. The insertion and the renumber go in as **one version
bump**.

## Before any prose

- Register the chat (compulsory, D-301):
  `python3 tools/chat_register.py register --chat "<name>" --kind document --claim doc:PaperM
  --purpose "§5.3 insertion and the §7.1 clause from Script 55"`
- `python3 tools/work_board.py` and hold `doc:PaperM`.
- **Register the field keys first.** The spec is explicit that the keys go to the Paper M chat so it
  can register them before they are quoted. The keys are Script 55's, named in the spec's §7
  (`wb_drain_share_median` and its `_sy_lo` / `_sy_hi` bracket among them); take their values from
  the committed CSVs under `outputs/`, never from J-1's conversation.
- ODTs go through `tools/odt_edit.py` only, and a document is versioned: edit `PaperM_v1_42.odt`,
  write `PaperM_v1_43.odt`. Read every edited passage back from the saved file.

## The plain companion

`PaperM_plain` follows in its **next** pass, not this one.

## Unattended rule

If a question of editorial judgement comes up that this brief and the spec do not answer — which
sentence carries the Sy bracket, how much of the SI detail belongs in §5.3 — stop, set out the
question with a recommendation, and wait for Martin. Do not decide it.
