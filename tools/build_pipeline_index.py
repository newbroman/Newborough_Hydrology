#!/usr/bin/env python3
"""Write pipeline_index.html: one entry per pipeline script, saying what it does, what it reads, what it feeds and which documents use its outputs.

Why this exists (T-197, J-13; brief NRG_brief_pipeline_index_2026-11-10).

  Martin, 2026-11-10: the project's index.html should lead to "an index of scripts in the pipe line
  and their depenancies and to which scripts they are fed". A hand-kept index rots -
  notes/ledgers/SCRIPT_LEDGER.md was last reconciled on 2026-08-26 - so this page is GENERATED from
  what the pipeline already records about itself, and check_all gates it (CLAUDE.md section 4d: every
  generated artefact gets its --check on the day it is written).

Where each part comes from.

  steps, phase, tier    outputs/pipeline_manifest.json (run_analysis.py's step registry) and the
                        phase titles in run_analysis.py's ALL_PHASES, read by ast - nothing imported.
  reads / feeds         outputs/pipeline_provenance.json: each step's `inputs` and `emitted`. Step B is
                        fed by step A wherever B's inputs include a file A emitted. An input no
                        registered step emitted is external data (data/...) or an earlier output.
                        A provenance record for a script that is no longer registered (a renamed
                        script's last run) is left out and listed at the foot of the page.
  documents             notes/ledgers/PROVENANCE_LEDGER.md (exhibits, keyed by output file) and
                        tools/citation_index.csv (quoted values, keyed by source CSV) - the same two
                        sources VALUE_REGISTER and PROVENANCE_LEDGER are built from (CLAUDE.md 4e).
                        Internal reference notes (notes/...) are not documents and are left out.
  what it does          the first usable line of the script's module docstring, which travels with
                        the code. A script whose docstring opens with nothing usable (only its file
                        name, or only a rule) is FLAGGED on the page and shown with its step
                        description from the registry instead; nothing is invented. SCRIPT_LEDGER
                        has no description column, so it cannot serve as the fallback.

The page is deterministic: no clock is read, so --check can compare CONTENT against a fresh build
(never mtimes - the J-10 review's lesson). It is a public page: it names no private path and reads
nothing under working/.

Usage:
    python3 tools/build_pipeline_index.py            # write pipeline_index.html
    python3 tools/build_pipeline_index.py --check    # exit 1 if the committed page differs from a fresh build
    python3 tools/build_pipeline_index.py --selftest # the description and graph rules on fixed cases
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-11-11. T-197 / J-13: first issue.

import argparse
import ast
import csv
import difflib
import html
import json
import pathlib
import re
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "pipeline_index.html"
MANIFEST = REPO / "outputs/pipeline_manifest.json"
PROVENANCE = REPO / "outputs/pipeline_provenance.json"
RUN_ANALYSIS = REPO / "run_analysis.py"
SRC = REPO / "src"
EXHIBITS = REPO / "notes/ledgers/PROVENANCE_LEDGER.md"
CITATIONS = REPO / "tools/citation_index.csv"

TIER = {"A": "analytical", "D": "display / utility", "X": "diagnostic"}
EXEC = {"default": "runs in the default pass", "optin": "opt-in (--with-supplementary)",
        "ondemand": "on demand only"}

# Document families, in the order a reader meets them. (pattern on the file stem, label).
DOC_FAMILIES = [
    (r"Paper ?1", "Paper 1"),
    (r"PAPER1_SI_methods", "Paper 1 supplementary methods"),
    (r"Paper1_plain", "Paper 1, plain-language companion"),
    (r"(Hollingham_2026_)?Paper ?2(_amended)?", "Paper 2"),
    (r"Paper2_plain", "Paper 2, plain-language companion"),
    (r"PaperM", "Methods paper (Paper M)"),
    (r"PaperM_plain", "Methods paper, plain-language companion"),
    (r"report(\d*)", "Technical report"),
    (r"Newborough_Methods_Supplement", "Methods Supplement"),
    (r"Supplementary_Material", "Supplementary Material"),
    (r"academic_Summary", "Academic summary"),
    (r"crynodeb_academaidd", "Academic summary (Welsh)"),
    (r"public_summary_(EN|CY|PL)", "Public summary"),
    (r"NRG_Web_Tools_Technical_Note", "Web tools technical note"),
    (r"NRG_Web_Tools_User_Manual", "Web tools user manual"),
    (r"PIPELINE_README", "Pipeline reference (PIPELINE_README)"),
    (r"readme", "Project readme"),
    (r"index", "Project website"),
]
_RULE = re.compile(r"^[=\-─~*#_.\s]+$")
# a line ending like this has its sentence running on to the next line
_OPEN_END = (r"(,|\b(a|an|the|of|for|to|in|on|at|by|from|with|and|or|but|between|against|over|"
             r"under|into|through|as|that|which|whose|its|their|per))$")


# ── descriptions ─────────────────────────────────────────────────────────────
def describe(script: str, doc: str | None) -> str | None:
    """The first usable line of a module docstring, without the script's own name in front of it,
    carried on while its sentence wraps. None when there is nothing usable (the caller flags it)."""
    if not doc:
        return None
    lines = [l.strip() for l in doc.splitlines()]
    stem = script[:-3] if script.endswith(".py") else script
    num = re.match(r"^(run_)?(\d+[a-z]?)", stem)
    num = num.group(2) if num else None
    i = 0
    while i < len(lines) and (not lines[i] or _RULE.match(lines[i])):
        i += 1
    if i >= len(lines):
        return None
    first = lines[i]
    prefix = r"(?:" + re.escape(script) + r"|Script\s+" + (re.escape(num) if num else r"\S+") \
        + (r"|" + re.escape(num) if num else "") + r")"
    first = re.sub(r"^" + prefix + r"\s*(?:—|–|--|-|:)?\s*", "", first)
    first = re.sub(r"\s*\(\s*[\w.-]+\.py\s*\)\s*$", "", first)     # "(00_climate_summary.py)", an old name
    first = re.sub(r"^PHASE\s+\d+\s*:\s*", "", first)
    if len(first.split()) < 3:
        return None
    text = first
    # carry a wrapped sentence on: same paragraph, no rule, not yet ended
    j = i + 1
    while (j < len(lines) and j <= i + 3 and lines[j] and not _RULE.match(lines[j])
           and not re.search(r"[.?!:)]$", text) and not re.match(r"^[A-Z][A-Za-z ]{0,24}:\s", lines[j])
           and (re.search(_OPEN_END, text) or lines[j][:1].islower())):
        text += " " + lines[j]
        j += 1
    text = text.strip()
    return text[0].upper() + text[1:]


def docstring(path: pathlib.Path) -> str | None:
    try:
        return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None


# ── sources ──────────────────────────────────────────────────────────────────
def phase_titles() -> dict[int, str]:
    """Phase number -> title, from run_analysis.py's ALL_PHASES, by ast (nothing imported)."""
    tree = ast.parse(RUN_ANALYSIS.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "ALL_PHASES" for t in node.targets):
            out = {}
            for n, elt in enumerate(node.value.elts, start=1):
                label = elt.elts[0].value
                out[n] = re.sub(r"^PHASE\s+\d+\s*[—–-]+\s*", "", label).strip()
            return out
    raise SystemExit("build_pipeline_index: ALL_PHASES not found in run_analysis.py")


def exhibits() -> dict[str, list[tuple[str, str]]]:
    """Output file name -> [(document, 'figure'|'table'|'exhibit')], from PROVENANCE_LEDGER.md."""
    out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    if not EXHIBITS.exists():
        return out
    cur = None
    for line in EXHIBITS.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            break                       # the "outputs no exhibit renders" list follows
        if not line.startswith("| ") or line.startswith("| Output file"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0]:
            cur = cells[0].strip("`")
        if cur:
            kind = cells[2].split()[0].lower() if cells[2] else "exhibit"
            out[cur].append((cells[1], kind if kind in ("figure", "table") else "exhibit"))
    return out


def citations() -> dict[str, dict[str, set[str]]]:
    """Source CSV name -> document -> {citation keys}, from tools/citation_index.csv.
    Same reading as build_value_register.py; reference notes under notes/ are not documents."""
    out: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    if not CITATIONS.exists():
        return out
    with CITATIONS.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            doc = (r.get("document") or "").strip()
            key = (r.get("key") or "").strip()
            src = pathlib.Path(r.get("source_csv") or "").name
            if not (doc and key and src) or doc.startswith("notes/"):
                continue
            out[src][pathlib.PurePath(doc).name].add(key)
    return out


def family(docname: str) -> tuple[int, str, str | None]:
    """(order, label, version-or-None) for a document name ('report9.odt', 'Paper 1', 'Paper1.md')."""
    stem = re.sub(r"\.(odt|md|html|odm)$", "", docname)
    stem = re.sub(r"_v\d+(_\d+)*$", "", stem)
    for n, (pat, label) in enumerate(DOC_FAMILIES):
        m = re.fullmatch(pat, stem)
        if m:
            ver = stem if label == "Technical report" and m.group(1) else None
            return n, label, ver
    return len(DOC_FAMILIES), stem, None


# ── the graph ────────────────────────────────────────────────────────────────
def build_graph(steps: list[dict], prov: dict) -> dict:
    """Per registered script: fed_by, feeds, external inputs, earlier outputs, emitted; and the
    provenance records left out because their script is no longer registered."""
    reg = [s["script"] for s in steps]
    regset = set(reg)
    producers: dict[str, set[str]] = defaultdict(set)
    for script in reg:
        for f in (prov.get(script) or {}).get("emitted", {}) or {}:
            producers[f].add(script)
    g = {s: {"fed_by": set(), "feeds": set(), "external": set(), "earlier": set(),
             "emitted": sorted((prov.get(s) or {}).get("emitted", {}) or {}),
             "recorded": s in prov, "started": (prov.get(s) or {}).get("started", "")}
         for s in reg}
    for script in reg:
        for f in (prov.get(script) or {}).get("inputs", []) or []:
            makers = producers.get(f, set()) - {script}
            if makers:
                for a in makers:
                    g[script]["fed_by"].add(a)
                    g[a]["feeds"].add(script)
            elif f not in producers:
                (g[script]["earlier"] if f.startswith("outputs/") else g[script]["external"]).add(f)
    stale = sorted(k for k in prov if k not in regset)
    return {"steps": g, "stale": stale}


def documents_for(emitted: list[str], ex: dict, cites: dict) -> list[tuple[str, str]]:
    """[(document label, what it uses)] for a step's emitted files, in family order."""
    figs: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    vals: dict[tuple, set[str]] = defaultdict(set)
    seen_ex: set[tuple] = set()
    for f in emitted:
        name = pathlib.PurePath(f).name
        for doc, kind in ex.get(name, []):
            o, label, ver = family(doc)
            if (doc, kind, name) in seen_ex:
                continue
            seen_ex.add((doc, kind, name))
            figs[(o, label)][kind] += 1
        for doc, keys in cites.get(name, {}).items():
            o, label, ver = family(doc)
            vals[(o, label)] |= {(doc, k) for k in keys}
    out = []
    for key in sorted(set(figs) | set(vals)):
        parts = []
        for kind in ("figure", "table", "exhibit"):
            n = figs.get(key, {}).get(kind, 0)
            if n:
                parts.append(f"{n} {kind}{'s' if n != 1 else ''} drawn from its outputs")
        nv = len({k for _d, k in vals.get(key, set())})
        if nv:
            parts.append(f"{nv} quoted value{'s' if nv != 1 else ''}")
        out.append((key[1], "; ".join(parts)))
    return out


# ── rendering ────────────────────────────────────────────────────────────────
CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--sand:#f4f0e6;--sand-dark:#e8e0cc;--dune:#c8b878;--slate:#3a4a52;--slate-light:#5a6e78;
--water:#4a7a8a;--water-light:#6a9aaa;--water-pale:#e8f2f5;--pine:#3d5c3a;--pine-light:#5a7d56;
--text:#2a3338;--text-light:#5a6a72;--border:#d4c8a8;--card:#ffffff;--flag:#8a5a1a;--flag-bg:#fbf1dc}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--sand:#1b2125;--sand-dark:#232b30;
--slate:#2a363c;--slate-light:#3a4a52;--water:#8ab8c6;--water-light:#5a8a9a;--water-pale:#1f2d33;
--pine:#8fb58a;--pine-light:#7aa275;--text:#e4e6e2;--text-light:#a4b0b5;--border:#3a4448;--card:#222a2e;
--flag:#e8b86a;--flag-bg:#33291a}}
:root[data-theme=dark]{--sand:#1b2125;--sand-dark:#232b30;--slate:#2a363c;--slate-light:#3a4a52;
--water:#8ab8c6;--water-light:#5a8a9a;--water-pale:#1f2d33;--pine:#8fb58a;--pine-light:#7aa275;
--text:#e4e6e2;--text-light:#a4b0b5;--border:#3a4448;--card:#222a2e;--flag:#e8b86a;--flag-bg:#33291a}
html{scroll-behavior:smooth}
body{font-family:'Source Sans 3',sans-serif;background:var(--sand);color:var(--text);line-height:1.6}
header{background:var(--slate);color:#fff;padding:2.4rem 2rem 2rem;position:relative}
header::after{content:'';position:absolute;bottom:0;left:0;right:0;height:4px;
background:linear-gradient(90deg,var(--dune),var(--water),var(--pine))}
.inner{max-width:1080px;margin:0 auto}
.site-label{font-weight:300;font-size:.78rem;letter-spacing:.18em;text-transform:uppercase;color:var(--dune);margin-bottom:.6rem}
h1{font-family:'Libre Baskerville',Georgia,serif;font-size:clamp(1.4rem,3.2vw,2rem);line-height:1.25;margin-bottom:.6rem}
.header-meta{font-size:.85rem;color:rgba(255,255,255,.7);font-weight:300}
.header-meta a{color:var(--dune)}
main{max-width:1080px;margin:0 auto;padding:1.5rem 2rem 4rem}
.intro{margin-bottom:1.2rem}.intro p{margin-bottom:.7rem}
.legend{font-size:.85rem;color:var(--text-light)}
input#q{width:100%;max-width:460px;padding:.55rem .8rem;border:1px solid var(--border);border-radius:4px;
background:var(--card);color:var(--text);font:inherit;margin:.4rem 0 1rem}
.toc{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1rem}
.toc a{font-size:.8rem;border:1px solid var(--border);border-radius:99px;padding:.1rem .6rem;background:var(--card)}
section.phase{padding:1.6rem 0 .6rem;border-top:1px solid var(--border)}
.section-label{font-size:.72rem;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--water);margin-bottom:.3rem}
h2{font-family:'Libre Baskerville',Georgia,serif;font-size:1.2rem;color:var(--text);margin-bottom:.9rem;line-height:1.3}
article{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--water);border-radius:4px;
padding:.9rem 1.1rem;margin-bottom:.8rem}
article.tier-D{border-left-color:var(--dune)}article.tier-X{border-left-color:var(--pine-light)}
article:target{outline:2px solid var(--water)}
.does{font-size:1.02rem;margin-bottom:.35rem}
.id{font-size:.8rem;color:var(--text-light);margin-bottom:.6rem}
.id code{font-family:ui-monospace,Menlo,'Courier New',monospace;font-size:.82rem;color:var(--text)}
dl{display:grid;grid-template-columns:7.5rem 1fr;gap:.25rem .8rem;font-size:.88rem}
dt{color:var(--text-light);font-weight:600}
dd ul{list-style:none}dd li{margin-bottom:.1rem}
.chip{display:inline-block;font-family:ui-monospace,Menlo,'Courier New',monospace;font-size:.78rem;
border:1px solid var(--border);border-radius:3px;padding:0 .35rem;margin:0 .25rem .2rem 0;background:var(--water-pale)}
.ext{font-family:ui-monospace,Menlo,'Courier New',monospace;font-size:.78rem}
.none{color:var(--text-light);font-style:italic}
.flag{display:inline-block;font-size:.75rem;color:var(--flag);background:var(--flag-bg);border-radius:3px;padding:0 .4rem;margin-left:.3rem}
.about{margin-top:2rem;padding:1rem 1.2rem;background:var(--water-pale);border:1px solid var(--water-light);border-radius:4px;font-size:.88rem}
.about h2{font-size:1.05rem}.about ul{margin:.3rem 0 .8rem 1.2rem}.about p{margin-bottom:.6rem}
a{color:var(--water);text-decoration:none}a:hover{text-decoration:underline}
footer{background:var(--slate);color:rgba(255,255,255,.6);font-size:.8rem;padding:1.6rem 2rem}
footer a{color:var(--dune)}
@media (max-width:600px){header{padding:1.8rem 1rem 1.6rem}main{padding:1rem 1rem 3rem}
dl{grid-template-columns:1fr}dt{margin-top:.3rem}}
"""

JS = """
const q=document.getElementById('q'),arts=[...document.querySelectorAll('article')],secs=[...document.querySelectorAll('section.phase')];
q.addEventListener('input',()=>{const v=q.value.toLowerCase().trim();
arts.forEach(a=>a.style.display=!v||a.textContent.toLowerCase().includes(v)?'':'none');
secs.forEach(s=>s.style.display=[...s.querySelectorAll('article')].some(a=>a.style.display!=='none')?'':'none')});
"""


def anchor(script: str) -> str:
    return "s-" + re.sub(r"[^A-Za-z0-9_-]", "-", script[:-3] if script.endswith(".py") else script)


def render(steps, titles, graph, ex, cites, generated: str) -> tuple[str, list[str]]:
    e = html.escape
    by_script = {s["script"]: s for s in steps}
    flagged: list[str] = []
    phases: dict[int, list[dict]] = defaultdict(list)
    for s in steps:
        phases[s["phase"]].append(s)

    def chip(script: str) -> str:
        s = by_script[script]
        return f'<a class="chip" href="#{anchor(script)}" title="{e(script)}">{s["index"]} · {e(script)}</a>'

    body = []
    for ph in sorted(phases):
        body.append(f'<section class="phase" id="phase-{ph}"><p class="section-label">Phase {ph}</p>'
                    f'<h2>{e(titles.get(ph, ""))}</h2>')
        for s in sorted(phases[ph], key=lambda x: x["index"]):
            script = s["script"]
            node = graph["steps"][script]
            text = describe(script, docstring(SRC / script))
            flag = ""
            if text is None:
                flagged.append(script)
                text = s["desc"]
                flag = '<span class="flag" title="The script\'s docstring has no usable first line; this is its step description from run_analysis.py.">from the step registry</span>'
            ident = (f'Step {s["index"]} · <code>{e(script)}</code> · {e(TIER.get(s["tier"], s["tier"]))}'
                     f' · {e(EXEC.get(s["exec"], s["exec"]))}')
            rows = []
            if not node["recorded"]:
                rows.append(("Links", '<span class="none">Not run in the recorded pass (it runs on demand only), '
                                      'so what it reads and writes is not recorded.</span>'))
            else:
                reads = []
                if node["fed_by"]:
                    reads.append("<li>Results of " + "".join(chip(a) for a in sorted(node["fed_by"], key=lambda x: by_script[x]["index"])) + "</li>")
                if node["external"]:
                    reads.append("<li>External data: " + ", ".join(f'<span class="ext">{e(f)}</span>' for f in sorted(node["external"])) + "</li>")
                if node["earlier"]:
                    reads.append("<li>Earlier outputs no step wrote in the recorded pass: "
                                 + ", ".join(f'<span class="ext">{e(f)}</span>' for f in sorted(node["earlier"])) + "</li>")
                rows.append(("Reads", f"<ul>{''.join(reads)}</ul>" if reads else '<span class="none">nothing recorded</span>'))
                rows.append(("Feeds", "".join(chip(b) for b in sorted(node["feeds"], key=lambda x: by_script[x]["index"]))
                             or '<span class="none">no later step reads its outputs</span>'))
                docs = documents_for(node["emitted"], ex, cites)
                rows.append(("Used in", "<ul>" + "".join(f"<li><strong>{e(d)}</strong>: {e(w)}</li>" for d, w in docs) + "</ul>"
                             if docs else '<span class="none">no document draws on its outputs directly</span>'))
            dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
            body.append(f'<article id="{anchor(script)}" class="tier-{e(s["tier"])}"><p class="does">{e(text)}{flag}</p>'
                        f'<p class="id">{ident}</p><dl>{dl}</dl></article>')
        body.append("</section>")

    toc = "".join(f'<a href="#phase-{ph}">{ph}. {e(titles.get(ph, ""))}</a>' for ph in sorted(phases))
    about = ['<div class="about"><h2>How this page is made</h2>',
             "<p>It is generated, never edited by hand, by <code>tools/build_pipeline_index.py</code>, and the "
             "project's checks fail if it falls behind. Each part comes from a record the pipeline already keeps:</p><ul>",
             "<li><strong>Steps, phases and tiers</strong> from the step registry in <code>run_analysis.py</code> "
             "(<code>outputs/pipeline_manifest.json</code>).</li>",
             "<li><strong>Reads and feeds</strong> from <code>outputs/pipeline_provenance.json</code>, which records the files "
             "every step read and wrote on the last full run. One step feeds another wherever the second read a file the "
             "first wrote.</li>",
             "<li><strong>Used in</strong> from the project's provenance ledger (figures and tables) and citation index "
             "(numbers quoted in the text).</li>",
             "<li><strong>What it does</strong> from the first line of each script's own description.</li></ul>",
             f"<p>Run record used: {e(generated)}.</p>"]
    if flagged:
        about.append("<p>These scripts' own descriptions open with nothing a reader can use, so their entries show the "
                     "step registry's wording instead: " + ", ".join(f'<a href="#{anchor(s)}">{e(s)}</a>' for s in flagged) + ".</p>")
    if graph["stale"]:
        about.append("<p>Left out: run records for scripts that are no longer registered (renamed or retired): "
                     + ", ".join(f"<code>{e(s)}</code>" for s in graph["stale"]) + ".</p>")
    about.append("</div>")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- GENERATED by tools/build_pipeline_index.py {__version__} - do not edit; regenerate. -->
<title>Pipeline index</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@300;400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header><div class="inner">
<p class="site-label">Newborough Warren &middot; Reproducible analysis</p>
<h1>Pipeline index</h1>
<p class="header-meta">Every script in the analysis pipeline: what it does, what it reads, which scripts it feeds and which documents use its results. &middot; <a href="index.html#pipeline">Back to the project page</a></p>
</div></header>
<main>
<div class="intro">
<p>The pipeline runs these scripts in order, phase by phase. Each entry starts with what the script does, then where its
inputs come from (other scripts' results, or data collected outside the pipeline), which later scripts use its results,
and which of the project's documents draw on them. The script names are the keys: click one to jump to its entry.</p>
<p class="legend">Left border: blue for an analytical step, sand for a display or utility step, green for a diagnostic.</p>
<input id="q" type="search" placeholder="Filter - a script number, a word, a document&hellip;" aria-label="Filter the index">
</div>
<nav class="toc" aria-label="Phases">{toc}</nav>
{''.join(body)}
{''.join(about)}
</main>
<footer><div class="inner">Newborough Warren Groundwater Research &middot; M. Hollingham, 2026 &middot;
<a href="https://github.com/newbroman/Newborough_Hydrology">GitHub repository</a></div></footer>
<script>{JS}</script>
</body>
</html>
"""
    return page, flagged


def build() -> tuple[str, list[str], list[str]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provd = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    steps = sorted(manifest["steps"], key=lambda s: s["index"])
    graph = build_graph(steps, provd.get("steps", {}))
    page, flagged = render(steps, phase_titles(), graph, exhibits(), citations(),
                           str(provd.get("generated", "")).replace("T", " "))
    return page, flagged, graph["stale"]


# ── selftest ─────────────────────────────────────────────────────────────────
def selftest() -> int:
    fails = []

    def eq(name, got, want):
        if got != want:
            fails.append(f"{name}: got {got!r}, want {want!r}")

    eq("bare filename", describe("02_clustering.py", "02_clustering.py\nPurpose: Performs Ward's..."), None)
    eq("rule then name", describe("06_x.py", "=====\n06_x.py\n"), None)
    eq("dash prefix", describe("25_coastal_gradient.py", "25_coastal_gradient.py — Coastal-Retreat Gradient Analysis\nCoastal-retreat gradient analysis"),
       "Coastal-Retreat Gradient Analysis")
    eq("wrapped", describe("11c_p.py", "11c_p.py — Per-well categorical priority map for\nP_flood-based scrape-target identification.\n\nX"),
       "Per-well categorical priority map for P_flood-based scrape-target identification.")
    eq("Script N", describe("41_canopy_cover.py", "Script 41 — canopy and forest-cover change from the dated aerial series.\n"),
       "Canopy and forest-cover change from the dated aerial series.")
    eq("parenthetical name", describe("00_climate_summary.py", "=====\nCLIMATE AND WELL NETWORK SUMMARY (00_climate_summary.py)\n===="),
       "CLIMATE AND WELL NETWORK SUMMARY")
    eq("no docstring", describe("x.py", None), None)
    steps = [{"script": "a.py"}, {"script": "b.py"}, {"script": "c.py"}]
    prov = {"a.py": {"inputs": ["data/raw.csv"], "emitted": {"outputs/a.csv": "h"}},
            "b.py": {"inputs": ["outputs/a.csv", "outputs/b.csv", "outputs/old.csv"], "emitted": {"outputs/b.csv": "h"}},
            "old.py": {"inputs": [], "emitted": {"outputs/a.csv": "h"}}}
    g = build_graph(steps, prov)
    eq("fed_by", g["steps"]["b.py"]["fed_by"], {"a.py"})
    eq("feeds", g["steps"]["a.py"]["feeds"], {"b.py"})
    eq("self-read is no edge", "b.py" in g["steps"]["b.py"]["fed_by"], False)
    eq("external", g["steps"]["a.py"]["external"], {"data/raw.csv"})
    eq("earlier", g["steps"]["b.py"]["earlier"], {"outputs/old.csv"})
    eq("unrecorded", g["steps"]["c.py"]["recorded"], False)
    eq("stale record left out", g["stale"], ["old.py"])
    eq("family report", family("report9.odt")[1], "Technical report")
    eq("family paper2", family("Hollingham_2026_Paper2_amended.md")[1], "Paper 2")
    eq("family paper 1", family("Paper 1")[1], "Paper 1")
    for f in fails:
        print("  selftest FAIL -", f)
    print(f"  build_pipeline_index --selftest: {'FAIL' if fails else 'OK'} ({len(fails)} failure(s))")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="exit 1 if pipeline_index.html differs from a fresh build")
    g.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    page, flagged, stale = build()
    rel = OUT.relative_to(REPO)
    if args.check:
        if not OUT.exists():
            print(f"  build_pipeline_index: FAIL - {rel} is missing; run python3 tools/build_pipeline_index.py")
            return 1
        have = OUT.read_text(encoding="utf-8")
        if have != page:
            diff = list(difflib.unified_diff(have.splitlines(), page.splitlines(), "committed", "fresh", n=0, lineterm=""))
            print(f"  build_pipeline_index: FAIL - {rel} differs from a fresh build ({len(diff)} diff line(s)); "
                  "run python3 tools/build_pipeline_index.py")
            for line in diff[:12]:
                print("    " + line[:160])
            return 1
        print(f"  build_pipeline_index: OK - {rel} matches a fresh build "
              f"({len(flagged)} script(s) flagged for their docstring, {len(stale)} stale run record(s) left out)")
        return 0
    OUT.write_text(page, encoding="utf-8")
    print(f"  wrote {rel} ({len(page):,} bytes); {len(flagged)} script(s) flagged for their docstring: "
          + (", ".join(flagged) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
