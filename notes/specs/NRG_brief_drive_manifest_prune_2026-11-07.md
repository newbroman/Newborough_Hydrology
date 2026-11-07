# Brief — a ship leaves the next cloud ship unable to start: DRIVE_MANIFEST against prune_versions

**Raised:** 2026-11-06/07, by the `Pipeline Nov 5` chat, after `cloud_ship.sh` refused with
`SHIP: FAIL drive-not-current` on a tree whose previous ship had succeeded two hours earlier.
**Claim:** `tools` (and `working/nrg_git.sh`, which is in the private repo).
**Do not start by "fixing" the manifest.** See *What not to do*.

## The refusal, verbatim

    [2/7] Drive is the last archive (working/DRIVE_MANIFEST.json)
        download missing   docs/papers/paper_M/PaperM_plain_v1_6.odt
        download missing   docs/papers/paper_M/PaperM_v1_42.odt
        download missing   docs/papers/paper_M/PaperM_v1_43.odt
        download missing   docs/report/Newborough_Methods_Supplement_v2_0_120.odt
        download missing   docs/report/Newborough_Methods_Supplement_v2_0_121.odt
      231 documents in the manifest; 5 mismatch(es)
    SHIP: FAIL drive-not-current

All five are **superseded** versions. The current ones (`PaperM_v1_44`, `PaperM_plain_v1_7`,
`..._v2_0_122`) are present and correct.

## What is actually happening

`nrg_git.sh --ship` does, in order: archive the ODTs to Drive → write
`working/DRIVE_MANIFEST.json` → `prune_versions.py --keep N`. The manifest records **what Drive
holds**, and Drive keeps superseded versions deliberately. `prune_versions` then moves those same
superseded versions out of `docs/` into `archive/`:

    archive/papers/paper_M/PaperM_v1_43.odt
    archive/report/Newborough_Methods_Supplement_v2_0_121.odt

So the manifest describes a tree state that **the same ship invalidated seconds later**.
`cloud_ship.sh` check 2 compares the manifest against the *downloaded local copy* and finds those
five absent. Measured: manifest `archived_at 2026-11-06T21:19:17Z`, 231 entries, written by the
ship that then pruned.

**Therefore every cloud ship after a ship that prunes fails this check.** That is the same class as
the `NRG_DOC_LOCK_HOLDER` regression of the same evening (changelog 2026-11-06e): a ship leaving a
state that blocks the next one, deterministically, with nobody in between to notice.

## What not to do

1. **Do not hand-edit `DRIVE_MANIFEST.json`.** CLAUDE.md §4 records what hand-editing
   `docs/PDF_MANIFEST.txt` cost: the manifest is what the checker reads, so editing it **certifies**
   the state instead of verifying it, and that put a foreign PDF in the published corpus for three
   days.
2. **Do not just run `drive_pull.sh`.** It would fetch the five back into `docs/`, and the next
   prune would move them out again — a loop that fights `prune_versions`' purpose.
3. **Do not relax check 2 to "current versions only" without reading what it is for.** It exists so
   a cloud ship cannot archive from a Drive copy that is not the last archive (D-233). Weakening it
   to make a red go green is the failure mode D-213 warns about.

## The question to answer

Which of these is the manifest *for*?

- **(a) "what Drive holds"** — then check 2 is comparing the wrong things, and it should compare the
  manifest against **Drive**, with the local copy checked only for the files `drive_pull` fetches
  (the current set). The fix is in `cloud_ship.sh`.
- **(b) "what this tree should have"** — then the manifest should be written **after** the prune, or
  exclude pruned paths. The fix is in `nrg_git.sh`'s `do_ship()` ordering.

Read `nrg_git.sh` 1.26.0's own note ("the manifest of what Drive now holds goes to the private repo
at once, not a ship later, so a cloud ship can compare against the archive that actually happened")
before choosing — it suggests (a) was the intent, which would make this a `cloud_ship` defect.

## Also found, and probably separate

The manifest lists **scratch/** copies:

    scratch/sweep/sm1/Supplementary_Material_v1_43.odt
    scratch/sweep/sm2/Supplementary_Material_v1_43.odt
    scratch/sweep/sm3/Supplementary_Material_v1_43.odt
    scratch/t54/Supplementary_Material_v1_42.odt
    scratch/t54/mid/Supplementary_Material_v1_42.odt

`scratch/` is gitignored and ephemeral, so these look like stray uploads that an archive filter
should never have sent. Worth checking whether the upload filter is scoped to `docs/` and
`report_edits/odt/`, and whether these are on Drive taking space.

## Done when

- A cloud ship runs through check 2 on a tree whose previous ship pruned — **demonstrated**, not
  reasoned, by shipping twice in a row.
- A task row carries a check that would have caught it: something that asserts the manifest and the
  prune cannot disagree, or that check 2 compares the right set.
- `notes/reference/` or CLAUDE.md §4g records which of (a)/(b) the manifest means, since two tools
  read it and disagreed.

## State when this was written

Public `3d92c90b` and private (merged) are on `origin/main`; `check_all: OK` 50/50. The refusal
blocked nothing else — it stopped before any write, archive or prune, which is the design working.
