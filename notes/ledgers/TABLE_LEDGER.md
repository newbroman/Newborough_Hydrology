<!-- RETIRED 2026-09-19. Do not regenerate. -->

# TABLE_LEDGER — retired

Superseded by [`PROVENANCE_LEDGER.md`](PROVENANCE_LEDGER.md), which covers tables
and figures together and is keyed by OUTPUT FILE rather than by document.

This ledger was built from `tools/figure_table_manifest.csv` and had drifted
badly: 48 tables of which 20 were flagged, 19 rows carrying an empty source, and
a document list still naming `Newborough_Methods_Supplement_v1_9_6.odt` against a
live `v2_0_6`. `FIGURE_LEDGER.md`, generated the same way from the same manifest,
was correct throughout — the only difference between them is that
`build_figure_ledger.py --check` is a line in `tools/check_all.sh` and
`build_table_ledger.py --check` never was.

Two answers to one question is worse than one, so this file is not maintained.
`build_provenance_ledger.py --check` and `build_value_register.py --check` are
both gated, for the reason this one rotted.
