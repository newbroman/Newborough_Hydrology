# Heads-up for the Paper M chat: a third reading of the ET/drainage split is coming

**From:** the 2026-11-04 water-balance chat (Claude Opus 5.5, claude.ai chat session).
**For:** whichever chat holds `doc:PaperM`. No action on the document yet; this is a warning so
current wording is not polished only to be reopened.

**What is coming.** A new diagnostic, the fixed-storage water balance (spec
`claude/NRG_spec_water_balance_diagnostic_2026-11-04.md`, awaiting Martin's sign-off). It fixes Sy from
Script 18 and treats rainfall less PET less storage change as drainage, then regresses that on head.
It is not Script 08's TLM, and must not be called "TLM" in Paper M.

**Where it touches Paper M:**
- **§7.1 and §5.2, the split.** *Corrected 23:10 against v1_42 (`380a497`); the first version of
  this note misread the paper.* §7.1 does not bracket the split by Model A and Model B. It leaves the
  two forms' answers apart and constrains the split by §2.4's floor and §5.2's recession reading,
  which v1_42 presents as a third estimate independent of both forms. The water balance is therefore
  a FOURTH reading: one clause in §7.1 beside the other two, not a rewrite. It puts drainage at about
  a third of the annual loss on the open dune, below both forms, and attributes the gap to the SSM's
  β₂/β₁ (how much of PET the fitted form books as ET). Not the same quantity as §5.2's share, which is
  a share of summer recession, not of the annual loss.
- **§5.2's own caveats.** Two of the three caveats v1_42 gives for the recession reading are ones
  the diagnostic addresses directly: it selects dry months on rainfall rather than on the level having
  fallen, and it fits drainage against head in winter rather than letting head inflate a winter mean
  rate. That makes it a natural companion to §5.2, not a replacement for it.
- **§7.4, the forest.** Paper M leaves open whether C4's unidentified β₃ is a slow response or a
  mis-specified ET forcing. The water balance favours the forcing reading.
- **§4 and §7.3, forecasting.** It forecasts like Model A within the record and fails the drier decade
  in the same direction as Model B, which supports the paper's argument that a fitted base is what
  breaks outside the recorded climate.
- A short new §5.7 and one figure are proposed; the drafted passages will come as a file.

**What not to do.** Do not type any of its numbers. They are scratch results until Script 55 is on
`main` with its `report_numbers` CSV. The drafted passages will cite field keys.

**Coordination.** The build session will hold `pipeline`, not `doc:PaperM`. Paper M stays yours; the
passages are applied by you on top of your current version as one bumped version. Two of us bumping
Paper M would fork the version chain.
