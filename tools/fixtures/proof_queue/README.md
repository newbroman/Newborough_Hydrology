# proof_copy --queue: the executed acceptance test

`python3 tools/proof_copy.py --selftest` runs `--queue` against `verdicts.csv` over
`queue_fixture.md` and compares the export with `expected.json`, field for field.

**Why a fixture and not the September file.** The hand-built September work list
(`scratch/t96/emits.json`, 189 rows) was gitignored, in a cloud clone that no longer
exists. It cannot be produced, so it cannot be a witness. Two things stand in its place:

- **the field set** — `--queue --schema september` emits exactly the eight fields recorded
  in the committed brief `working/updates/NRG_spec_T96_emits_2026-09-29.md` (appendix,
  "Your work list"): `id, doc, section, number, script, what, reason, sentence`;
- **the behaviour** — these five rows, which are the four cases that matter:

| row | what it proves |
|---|---|
| `7d746497a5` | a `needs emit` denial is exported, with the script from the "Script NN" phrase and a key slugged from the quantity |
| `a97f1b0f81` | the computed value is the one after the `=`, not the script number; the `kind` guess reads `9 / 1272` as a derivation |
| `23600aac18` | a located value (`label = value [file]`) is exported, with the owner script taken from the file's own prefix and the Well cell from the label |
| `d7d869534a` | a denial that corrects the MATCHER ("'1)' is a list-item marker") is **not** exported — it owes no emit |
| `deadbeef01` | a better retired on 2026-10-06 (T-96) is **not** exported without `--include-retired`, and its id is no longer in any mirror |

`section` is empty for every fixture item because a section number comes from
`tools/section_map.csv`, which carries no row for a fixture chapter. Section recovery is
witnessed by the live run instead (§3.4, §4.2.3, §5.7.7 … on the real verdicts).

Regenerating `expected.json` is a judgement, not housekeeping: if a change to the guesses
is intended, re-copy the export and say in the changelog which field moved and why.
