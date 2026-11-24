<!-- GENERATED LEDGER — do not edit.
     Regenerate with: python3 tools/build_doc_ledger.py -->

# DOC_LEDGER — published PDFs, their source ODTs, and lag state

*Generated from `docs/PDF_MANIFEST.txt` with the live lag state from `tools/export_lag.py`. Living current-state; regenerate, do not hand-edit. `tools/export_lag.py` is the live authority.*

**13 published PDFs** — 4 version-current, 4 lagging, 5 unversioned (mtime-only, not version-tracked).

| Published PDF | Source ODT (recorded) | Built (UTC) | State |
|---|---|---|---|
| `docs/academic_summaries/academic_summary.pdf` | `academic_Summary_v1_43.odt` | 2026-11-24T12:23:17Z | current |
| `docs/academic_summaries/crynodeb_academaidd.pdf` | `crynodeb_academaidd_v1_33.odt` | 2026-11-24T07:31:43Z | current |
| `docs/papers/paper_1/PAPER1_SI_methods.pdf` | `PAPER1_SI_methods_v1_43.odt` | 2026-11-24T07:31:44Z | current |
| `docs/papers/paper_1/Paper1.pdf` | `Paper1_v1_109.odt` | 2026-11-23T14:45:35Z | current |
| `docs/papers/paper_2/Hollingham_2026_Paper2_amended.pdf` | `Hollingham_2026_Paper2_amended_v54.odt` | 2026-11-24T17:33:35Z | **STALE** |
| `docs/public_summaries/Newborough_Warren_Podsumowanie.pdf` | `public_summary_PL.odt` | 2026-10-10T16:14:45Z | unversioned |
| `docs/public_summaries/Newborough_Warren_Public_Summary.pdf` | `public_summary_EN.odt` | 2026-10-10T16:14:44Z | unversioned |
| `docs/public_summaries/Niwbwrch_Crynodeb_Cyhoeddus.pdf` | `public_summary_CY.odt` | 2026-10-10T16:14:45Z | unversioned |
| `docs/report/Newborough_Methods_Supplement.pdf` | `Newborough_Methods_Supplement_v2_0_150.odt` | 2026-11-24T17:33:32Z | **STALE** |
| `docs/report/Supplementary_Material.pdf` | `Supplementary_Material_v1_70.odt` | 2026-11-24T17:33:34Z | **STALE** |
| `docs/report/report.pdf` | `report.odm+chapters sha256:e5549457e378c276` | 2026-11-24T17:59:18Z | **STALE** |
| `docs/web_tools/NRG_Web_Tools_Technical_Note.pdf` | `NRG_Web_Tools_Technical_Note.odt` | 2026-11-23T14:45:30Z | unversioned |
| `docs/web_tools/NRG_Web_Tools_User_Manual.pdf` | `NRG_Web_Tools_User_Manual.odt` | 2026-11-23T14:45:30Z | unversioned |

## Authored directly (no source ODT)

*Published PDFs with no ODT to rebuild from — export_lag declares these authored directly.*

- `docs/Glossaries/Dune_Hydrology_Glossary.pdf`
- `docs/Glossaries/Geirfa_Hydroleg_Twyni.pdf`
- `docs/Glossaries/Slownik_Hydrologii_Wydm.pdf`

> `report.pdf` is deliberately **absent** from `PDF_MANIFEST.txt` and from this ledger: it is built from the `report.odm` master via `tools/export_master_pdf.py`, not `build_pdfs.sh`. See the project working rules.

*Generated 2026-11-24 by `tools/build_doc_ledger.py` v1.1.0.*
