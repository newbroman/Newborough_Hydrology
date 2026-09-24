# T-85 brief — results/discussion register pass (Newborough hydrology report)

You are auditing the prose REGISTER of a scientific report chapter. Read-only: do not edit any file.

Files (repository root):
- `report_edits/text/report9.md` — Chapter 4, Results.
- `report_edits/text/report10.md` — Chapter 5, Discussion. Its heading map with line numbers is at
  the §5 heading map (`grep -n "^#" report_edits/text/report10.md`)
  (the file's `##` are §5.1, 5.2, … in order; `###` are 5.n.1, 5.n.2, … in order under each `##`).
  Use `grep -n '^#' report_edits/text/report10.md` to number them yourself if in doubt.
- Chapter 4 headings: `grep -n '^#' report_edits/text/report9.md`; `##` are §4.1, 4.2, … in order; `###` are 4.n.m.

Rubric. For every paragraph in your range classify it:
- REPORTS — states what was measured, fitted, counted or rendered; gives the number, the sign, the uncertainty, what a figure/table shows; says which method produced it. Belongs in §4.
- INTERPRETS — one or more of: (a) MECHANISM — explains WHY the pattern occurs (physical process, canopy, geology); (b) DRIVER-WEIGHING — ranks drivers or interventions against one another or judges which matters more; (c) IMPLICATION — management, monitoring, restoration or policy consequence; (d) LITERATURE — compares with other sites/studies or cites external literature to interpret; (e) ALTERNATIVE READING — argues a competing explanation away or for; (f) GLOSS — evaluative adjectives/adverbs on a result ("remarkably", "strikingly", "reassuringly", "importantly") or a sentence restating a result's meaning without new content.
A paragraph that reports AND then interprets counts as interpretive for the interpreting sentences only.

Output: a markdown table, one row per interpretive PASSAGE (a passage may be one sentence or a whole paragraph), columns:
| # | Line(s) | §4 subsection | Quote (first ~12 words, verbatim) | Class (a–f) | Severity | Where it belongs |
- Severity: **move** — the passage argues and should relocate to §5 (or be deleted if §5 already says it); **trim** — one or two sentences to cut or soften in place; **minor** — a word-level gloss.
- Where it belongs: the §5.n.m from the heading map, and if §5 ALREADY says it, write "dup §5.n.m" (check by grepping report10.md for the key phrase or number).
- Quotes must be VERBATIM from the file at the line you cite — I will spot-check them.

After the table: (1) one line per §4 subsection in your range with a verdict: "reports" / "mixed" / "reads as discussion"; (2) the three headline cases with a sentence each; (3) counts: paragraphs read, passages flagged, by severity.

Do NOT flag: statements of method choice ("we used the forest-free fit because …" — that is method, belongs in §3 not §5; note it separately as "method-in-results" if it's more than a clause); caveats that bound a NUMBER ("the C4 value is not identified on the window"); and reference to a §5 section ("discussed in Section 5.6.1") — those are pointers, fine.

Be thorough but keep quotes short. No advice on how to rewrite.
