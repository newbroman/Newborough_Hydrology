# Newborough Warren Report Chatbot — Specification

**Status:** Proposed (spec only, not started)
**Related:** `report.odm`, `tools/refresh_mirrors.py`, `forecaster.html`,
`scenario_viewer.html`, the GitHub Pages site

> **Provenance.** Drafted in a separate Claude chat session with Martin and
> handed over as a file on 2026-09-01. Filed here rather than at the
> `docs/newborough_chatbot_spec.md` that draft suggested: since the 2026-08-27
> restructure `docs/` is **deliverables only** and specifications live under
> `notes/specs/`. Content is otherwise as received, with the register entry
> moved to the live private register (`working/updates/NRG_WORK_REGISTER.md`,
> W121) because `WORK_REGISTER.md` at the repo root is a signpost, not the
> register.

## 1. Purpose

A public-facing web tool that answers questions about the Newborough Warren
sand-dune / aquifer report by retrieving and citing the report's own text. It
sits alongside the interactive tools already published from the repo.

## 2. Audience & context

Public and stakeholders. Newborough is an NRW/CNC-managed NNR, so a public
Welsh-language face effectively means treating Welsh no less favourably than
English. To confirm: whether the tool falls under a public body's Welsh Language
Standards obligations, or is Martin's own research output.

## 3. Principles

- **Grounded.** Answers come only from report passages, cite the section, and
  say plainly when the report doesn't cover something. No invented figures.
- **Traceable.** Mirrors the project's existing discipline (decision log,
  citation-review step).
- **In sync.** The corpus is rebuilt from the report mirrors whenever the
  report changes, so answers never come from stale text.
- **Bilingual.** English/Welsh; answer in the language asked; bilingual UI.

## 4. Corpus

Built from the plaintext mirrors that `refresh_mirrors.py` already produces.
Chunk by heading/section; store section id + heading + text (plus embeddings for
the semantic/LLM variants). Add a corpus-build step to `refresh_mirrors.py` so
the bot regenerates itself on every report change.

## 5. Architecture options

**A. Static, no-LLM (recommended first).** Precomputed chunks (and optional
embeddings) shipped as JSON; in-browser retrieval returns the best-matching
passages with section citations and a short extractive summary. Free, unlimited,
abuse-proof, drops straight into GitHub Pages, PWA-installable. Reads as very
good "smart search / jump to the right paragraph" rather than free conversation.
Welsh answers require a Welsh corpus to index.

**B. Cloud LLM RAG (upgrade path).** Retrieval plus an API-generated answer:
conversational, cites sections, and can answer in Welsh from an English source.
Requires a small serverless proxy that holds the key, rate-limits per IP, caches
common questions, and enforces a hard monthly spend cap — never a key in the
static page.

**C. In-browser model (WebLLM).** Truly offline conversation, but a multi-GB
download and limited quality and speed on a ThinkPad. Not recommended.

**Recommendation:** ship A first; keep a clean seam so B can be bolted on behind
a capped proxy if stakeholders later want true chat.

## 6. Welsh

- UI fully bilingual — trivial and static.
- Static variant: answers are limited to the languages present in the corpus.
  Cloud variant: answers can be generated cross-lingually.
- **Deciding question:** will a Welsh version of the report exist?
  - Yes, then the bilingual static bot is fully viable (index both languages).
  - English-only but Welsh answers needed, then this favours the cloud variant,
    which generates Welsh from the English source.
- Either way: Welsh technical (hydrology and ecology) terminology needs a
  Welsh-speaker review and an agreed bilingual glossary — prefer NRW's own
  terminology.

## 7. Deployment

Static page in the repo, published via GitHub Pages (`.nojekyll` already
present), listed alongside `forecaster` and `scenario_viewer`. PWA manifest and
offline cache for repeat visitors.

## 8. Cost & abuse control (cloud variant only)

Serverless proxy; per-IP rate limiting; cache of common questions and answers;
hard monthly spend cap; no key in the client.

## 9. Timing

Build any time against the current draft to settle the design — the corpus
auto-rebuilds from the mirrors, so there is no staleness penalty to starting
early. Public launch waits until the report is finalised and signed off, to
avoid answering stakeholders from a superseded draft.

## 10. Open decisions

- Welsh corpus: is a Welsh translation of the report expected? (drives the
  engine choice)
- Welsh Language Standards applicability.
- Static-first versus cloud-first for launch.

## 11. Rough phases

- **P1** — corpus builder wired into `refresh_mirrors.py`, emitting chunks JSON.
- **P2** — static retrieval page: citations, bilingual UI, PWA.
- **P3** *(optional)* — capped cloud proxy and conversational layer.
- **P4** — Welsh review and glossary.

---

## Notes added on filing, 2026-09-01

Three things the drafting session could not know, each of which bears on P1:

1. **A Welsh corpus partly exists already.** `docs/public_summaries/` holds
   `public_summary_CY.odt` and `docs/academic_summaries/` holds
   `crynodeb_academaidd_v1_9.odt`, both with committed mirrors under `text/`.
   Neither is the report, but a bilingual static bot need not start from zero,
   and a Welsh-language user asking a general question could be answered from
   the Welsh summary with an honest note that the detail is English-only.
   There is also a Polish public summary, which the spec does not consider.
2. **`refresh_mirrors.py` refuses below pandoc 3.0** and is byte-reproducible on
   3.1.3. A corpus builder bolted onto it inherits that gate, which is correct —
   but it means the bot cannot be rebuilt on any machine with an older pandoc,
   and that should be stated wherever the build is documented.
3. **The mirrors carry pandoc anchor artefacts** (`[]{#anchor-567}` and similar)
   and generated-file banners. P1 must strip these, or every retrieved passage
   will carry markup a public reader should never see.

**Not addressed here and worth deciding early:** whether the corpus is the
report alone, or the report plus the two papers, the Methods Supplement and the
Supplementary Material. The latter is a much larger and more technical corpus
and would change what "the report doesn't cover that" means.
