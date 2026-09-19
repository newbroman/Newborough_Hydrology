#!/usr/bin/env python3
"""
build_value_ledger.py — one proof-reading ledger joining every CITED value to its
pipeline CSV, its symbol, and every place it appears, with an authoritative drift
flag. GENERATED — never hand-edit; regenerate with --write.

Drift is computed by reusing cite_check's own live value map (collect_values),
renderer and locator, so this ledger AGREES WITH THE GATE by construction: a
CONFIRMED drift here is exactly a CONFIRMED drift in `cite_check --index-only`.

Sources: tools/citation_index.csv (the citations + confirmed/proposed status),
cite_check.collect_values() (live committed values from outputs/**/report_numbers
+ registered tables), tools/symbol_register.csv (symbol + defining section),
notes/ledgers/NUMBER_LEDGER.md (volatility), tools/section_map.csv + the mirrors
(report reading-order).

Outputs:
  notes/ledgers/VALUE_LEDGER.md          per-quantity master (tracked source of truth)
  notes/ledgers/VALUE_LEDGER_report.md   report reading-order view
  notes/ledgers/VALUE_LEDGER.html        both, navigable/searchable

Usage:
  python3 tools/build_value_ledger.py --write | --check | --stdout
"""
from __future__ import annotations
import argparse, csv, html, pathlib, re, sys
from collections import defaultdict

__version__ = "1.1.0"
REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import cite_check as cc  # noqa: E402  reuse the authoritative value/drift logic

SYMBOL_REGISTER = REPO / "tools" / "symbol_register.csv"
NUMBER_LEDGER = REPO / "notes" / "ledgers" / "NUMBER_LEDGER.md"
SECTION_MAP = REPO / "tools" / "section_map.csv"
CITATION_INDEX = REPO / "tools" / "citation_index.csv"
OUT_MD = REPO / "notes" / "ledgers" / "VALUE_LEDGER.md"
OUT_MD_REPORT = REPO / "notes" / "ledgers" / "VALUE_LEDGER_report.md"
OUT_HTML = REPO / "notes" / "ledgers" / "VALUE_LEDGER.html"
OUT_HTML_REPORT = REPO / "notes" / "ledgers" / "VALUE_LEDGER_report.html"

def _f(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def _same(a, b):
    f = lambda x: x.replace("−", "-").lstrip("+")
    return f(a) == f(b)

def load_symbols():
    syms = []
    if SYMBOL_REGISTER.is_file():
        with open(SYMBOL_REGISTER, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                pats = [p for p in (r.get("context_any") or "").split("|") if p.strip()]
                syms.append({"glyph": r["glyph"], "sense": r.get("sense_id",""),
                             "meaning": r.get("meaning",""), "units": r.get("units",""),
                             "defined_in": r.get("defined_in",""), "pats": pats})
    return syms

# Curated metric-token -> symbol map. The number_index key's last "·" segment
# is the metric; these families cover the scientifically-meaningful quantities.
# A blank symbol (no rule) is deliberate: better empty than wrong.
SYMBOL_RULES = [
    (r"^sy_|specific.?yield",               "S_y",  "specific yield — WTF storage coefficient"),
    (r"beta_?1|^b1_|β₁",                    "β₁",   "recharge sensitivity coefficient (SSM)"),
    (r"beta_?2|^b2_|β₂",                    "β₂",   "atmospheric-draw coefficient (SSM)"),
    (r"beta_?3|^b3_|β₃",                    "β₃",   "head-dependent drainage coefficient (SSM)"),
    (r"delta0|δ0|δ₀",                        "δ₀",  "coast-edge decline rate at zero distance"),
    (r"^s_coast",                            "δ(d)","coastal-gradient decline rate at distance d"),
    (r"\btau\b|^t_?r\b|half.?life|τ",       "τ",   "storage–drainage index S_y/β₃ (residence time)"),
    (r"lambda_mult|pflood.*mult|rainfall.?mult|_multiplier", "m_P", "P_flood rainfall multiplier (λ_pflood)"),
    (r"lambda_reach|drawdown.?reach|e.?fold|reach_m", "λ",   "drawdown e-folding reach √(Kb/(S_y·β₃))"),
    (r"ar1_phi|^phi\b|φ",                    "φ",   "AR(1) residual autocorrelation"),
    (r"^r2$|_r2$|r_squared|r²",              "R²",  "coefficient of determination"),
    (r"p_value|^p_|^pval",                   "p",   "significance probability"),
    (r"^h_?0\b|h₀",                          "h₀",  "coastal head-change scale"),
    (r"change_mm|dh_mean|dh_median|we_mean|we_median|peak_mm|amplitude", "Δh", "water-level change / amplitude"),
    (r"nse|kge|rmse",                        None,  None),   # skill scores: no symbol
]
_SYM_DEF = {}   # glyph -> (meaning, defined_in), filled from the register when available

def _load_symbol_defs(syms):
    for s in syms:
        _SYM_DEF.setdefault(s["glyph"], (s["meaning"], s["defined_in"]))

def resolve_symbol(key, context, syms):
    metric = re.split(r"[·/]", key)[-1].strip().lower()
    for pat, glyph, defn in SYMBOL_RULES:
        if glyph and re.search(pat, metric):
            base = glyph[0]
            reg_meaning, defined = _SYM_DEF.get(base, ("", ""))
            return {"glyph": glyph, "definition": defn or reg_meaning, "defined_in": defined}
    return None

def load_volatility():
    vol = {}
    if NUMBER_LEDGER.is_file():
        for line in NUMBER_LEDGER.read_text(encoding="utf-8").splitlines():
            if line.startswith("|") and "`" in line:
                cells = [c.strip() for c in line.strip("|").split("|")]
                m = re.search(r"`([^`]+)`", cells[0]) if cells else None
                if m:
                    for c in cells:
                        if c.lower() in ("constant","stable","volatile","moving"):
                            vol[m.group(1)] = c.lower(); break
    return vol

def load_section_map():
    smap = defaultdict(list)
    if SECTION_MAP.is_file():
        with open(SECTION_MAP, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                smap[r["document"]].append((r.get("number",""), r.get("heading","")))
    return smap

def section_for(text, headings, context, quoted):
    if not text: return ("", "")
    probe = (context or "").strip()[:40] or (quoted or "")
    off = text.find(probe) if probe else -1
    if off < 0 and quoted: off = text.find(quoted)
    if off < 0: return ("", "")
    best, best_off = ("", ""), -1
    for num, head in headings:
        if not head: continue
        h = text.find(head)
        if 0 <= h <= off and h > best_off:
            best_off, best = h, (num, head)
    return best

def build():
    current, source_by_key = {}, {}
    for source, label, v in cc.collect_values():
        current.setdefault(label, v)
        source_by_key.setdefault(label, source)
    docs = cc.load_documents()
    fp = cc.load_false_positives()
    syms, vol, smap = load_symbols(), load_volatility(), load_section_map()
    _load_symbol_defs(syms)

    qu = defaultdict(lambda: {"src": "", "committed": None, "sym": None, "occ": []})
    with open(CITATION_INDEX, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            st = (r.get("status") or "").strip()
            if st == "rejected":
                continue
            k, doc, quoted = r["key"], r["document"], r.get("quoted", "")
            if doc.split("/")[-1] in cc.HISTORY_DOCS:
                continue
            if k not in current:
                continue
            text = docs.get(doc)
            if text is None:
                continue
            dp = len(quoted.split(".")[1]) if "." in quoted else 0
            want = cc.render(current[k], dp)
            if cc.locate(text, quoted, r.get("before", ""), r.get("after", "")) is None:
                continue  # not actually present at that occurrence
            adjud = (k, doc, quoted) in fp
            drift = (not _same(want, quoted)) and not adjud
            fq = _f(quoted); gap = None
            if fq is not None and current[k]:
                gap = (fq - current[k]) / abs(current[k]) * 100.0
            ctx = f"{r.get('before','')} {r.get('after','')}".strip()
            q = qu[k]
            q["src"] = source_by_key.get(k, "")
            q["committed"] = current[k]
            q["occ"].append({"doc": doc, "quoted": quoted, "want": want, "gap": gap,
                             "drift": drift, "status": st, "context": ctx})
            if q["sym"] is None:
                q["sym"] = resolve_symbol(k, ctx, syms)
    return qu, vol, smap

def drift_rows(qu):
    out = []
    for k, q in qu.items():
        for o in q["occ"]:
            if o["status"] == "confirmed" and o["drift"]:
                out.append((k, q, o))
    return out

def _short(p): return p.split("/")[-1] if p else ""
def _defn(sym):
    if not sym: return ""
    d = sym.get("definition","") or ""
    sec = sym.get("defined_in","") or ""
    return f"{d} (def. {sec})" if (d and sec) else (d or sec)
def _num(v):
    if v is None: return ""
    return f"{v:.6g}"

def render_master_md(qu, vol):
    L = ["# VALUE_LEDGER — every cited value, its source, symbol and drift", "",
         "**GENERATED by `tools/build_value_ledger.py` — regenerate with `--write`; never hand-edit.**",
         "", "Drift agrees with `cite_check --index-only` by construction. `⚠` marks a CONFIRMED "
         "occurrence whose quoted value no longer renders equal to the committed pipeline value.", "",
         "| Quantity (key) | Symbol | Definition / § | Source CSV | Committed | Volatility | Cited in | Drift |",
         "|---|---|---|---|---|---|---|---|"]
    for k in sorted(qu):
        q = qu[k]; sym = q["sym"]["glyph"] if q["sym"] else ""
        conf = [o for o in q["occ"] if o["status"] == "confirmed"]
        dr = [o for o in conf if o["drift"]]
        docs = ", ".join(sorted({_short(o['doc']).replace('.md','') for o in q["occ"]})) or "—"
        flag = f"⚠ {len(dr)}" if dr else "ok"
        L.append(f"| {k} | {sym} | {_defn(q['sym'])} | `{_short(q['src'])}` | {_num(q['committed'])} | "
                 f"{vol.get(k,'')} | {docs} | {flag} |")
    return "\n".join(L) + "\n"

def render_report_md(qu, smap):
    bydoc = defaultdict(list)
    for k, q in qu.items():
        for o in q["occ"]:
            bydoc[o["doc"]].append((k, q, o))
    L = ["# VALUE_LEDGER (report reading-order)", "",
         "**GENERATED — regenerate with `tools/build_value_ledger.py --write`.**", ""]
    docs = cc.load_documents()
    for doc in sorted(bydoc):
        text = docs.get(doc, "")
        headings = smap.get(_short(doc).replace(".md", ".odt"), []) or smap.get(_short(doc), [])
        items = []
        for k, q, o in bydoc[doc]:
            num, head = section_for(text, headings, o["context"], o["quoted"])
            items.append((num or "zzz", head, k, q, o))
        items.sort(key=lambda t: ([int(x) for x in re.findall(r"\d+", t[0])] or [99]))
        L.append(f"\n## {_short(doc).replace('.md','')}\n")
        cur = None
        for num, head, k, q, o in items:
            if head and head != cur:
                cur = head; L.append(f"\n### §{num} {head}\n")
            sym = f"[{q['sym']['glyph']}]" if q["sym"] else ""
            dfn = _defn(q["sym"])
            flag = " ⚠" if o["drift"] else ""
            L.append(f"- **{k}** {sym} — quoted {o['quoted']} vs committed {_num(q['committed'])}{flag}  ·  `{_short(q['src'])}`"
                     + (f"  — _{dfn}_" if dfn else ""))
    return "\n".join(L) + "\n"

def render_report_html(qu, smap):
    import html as _h
    docs = cc.load_documents()
    bydoc = defaultdict(list)
    for k, q in qu.items():
        for o in q["occ"]:
            bydoc[o["doc"]].append((k, q, o))
    # order documents in a sensible reading order (report chapters, then papers, supplement, notes)
    def _dorder(d):
        n=_short(d)
        pri = 0 if n.startswith("report") else 1 if "Paper1" in n or "PAPER1" in n else 2 if "Supplement" in n or "Paper2" in n or "Hollingham" in n else 3
        m=re.search(r"report(\d+)", n); num=int(m.group(1)) if m else 0
        return (pri, num, n)
    ndrift = len(drift_rows(qu))
    nav, body = [], []
    for doc in sorted(bydoc, key=_dorder):
        text = docs.get(doc, "")
        headings = smap.get(_short(doc).replace(".md",".odt"), []) or smap.get(_short(doc), [])
        items=[]
        for k,q,o in bydoc[doc]:
            num,head = section_for(text, headings, o["context"], o["quoted"])
            items.append((num or "zzz", head, k, q, o))
        items.sort(key=lambda t:([int(x) for x in re.findall(r"\d+",t[0])] or [99]))
        did=_short(doc).replace(".md","")
        docdrift=sum(1 for _,_,_,_,o in items if o["drift"])
        nav.append(f'<a href="#{_h.escape(did)}">{_h.escape(did)}{" ⚠" if docdrift else ""}</a>')
        body.append(f'<section id="{_h.escape(did)}"><h2>{_h.escape(did)}'
                    f'{f" <span class=pill>{docdrift} ⚠</span>" if docdrift else ""}</h2>')
        cur=None
        for num,head,k,q,o in items:
            if head and head!=cur:
                cur=head; body.append(f'<h3>§{_h.escape(num)} {_h.escape(head)}</h3>')
            sym=q["sym"]["glyph"] if q["sym"] else ""
            dfn=_defn(q["sym"])
            cls=" class=drift" if o["drift"] else ""
            flag=" ⚠" if o["drift"] else ""
            body.append(f'<div class="v{cls}"><span class=k>{_h.escape(k)}</span>'
                        f'{f" <span class=sym>{_h.escape(sym)}</span>" if sym else ""}'
                        f' <span class=val>quoted {_h.escape(o["quoted"])} · committed {_h.escape(_num(q["committed"]))}{flag}</span>'
                        f'{f"<span class=def>{_h.escape(dfn)}</span>" if dfn else ""}'
                        f'<span class=src><code>{_h.escape(_short(q["src"]))}</code></span></div>')
        body.append("</section>")
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Value Ledger — reading order</title>
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#e4e4e4;--drift:#fff4f0;--driftfg:#b3261e;--accent:#0b6bcb}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#15171b;--fg:#e8e8e8;--mut:#9aa0a6;--line:#2b2e35;--drift:#2a1512;--driftfg:#ff8a75;--accent:#5aa2f0}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif}}
header{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:14px 16px;z-index:5}}
h1{{font-size:18px;margin:0 0 6px}}.sub{{color:var(--mut);font-size:12px;margin-bottom:8px}}
nav{{display:flex;flex-wrap:wrap;gap:6px}}nav a{{font-size:12px;color:var(--accent);text-decoration:none;border:1px solid var(--line);border-radius:99px;padding:2px 9px}}
input{{width:100%;max-width:440px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg);font-size:15px;margin-top:8px}}
main{{padding:8px 16px 60px}}section{{margin:0 0 8px}}h2{{font-size:16px;margin:20px 0 4px;padding-top:8px;border-top:2px solid var(--line)}}
h3{{font-size:13px;color:var(--mut);margin:14px 0 4px;font-weight:600}}
.v{{display:flex;flex-wrap:wrap;gap:6px 10px;padding:5px 8px;border-bottom:1px solid var(--line);font-size:13px;align-items:baseline}}
.v.drift{{background:var(--drift)}}.k{{font-weight:600}}.sym{{color:var(--accent);font-family:ui-monospace,Menlo,monospace}}
.val{{color:var(--fg)}}.v.drift .val{{color:var(--driftfg);font-weight:600}}.def{{color:var(--mut);font-size:12px;flex-basis:100%}}
.src code{{font:11px/1.3 ui-monospace,Menlo,monospace;color:var(--mut)}}.pill{{font-size:12px;color:var(--driftfg);font-weight:600}}
</style></head><body>
<header><h1>Value Ledger — report reading order</h1>
<div class=sub>{len(qu)} quantities · {ndrift} confirmed drift · read top-to-bottom alongside the document, or jump:</div>
<nav>{''.join(nav)}</nav>
<input id=q placeholder="filter values (e.g. Sy, β₃, ⚠)…"></header>
<main>{''.join(body)}</main>
<script>
const q=document.getElementById('q'),vs=[...document.querySelectorAll('.v')];
q.addEventListener('input',()=>{{const v=q.value.toLowerCase();vs.forEach(e=>e.style.display=e.textContent.toLowerCase().includes(v)?'':'none')}});
</script></body></html>"""

def render_html(qu, vol):
    dset = {(k, id(o)) for k, q, o in drift_rows(qu)}
    rows = []
    for k in sorted(qu):
        q = qu[k]; sym = q["sym"]["glyph"] if q["sym"] else ""
        conf = [o for o in q["occ"] if o["status"] == "confirmed"]
        dr = [o for o in conf if o["drift"]]
        docs = ", ".join(sorted({_short(o['doc']).replace('.md','') for o in q["occ"]})) or "—"
        cls = "drift" if dr else ""
        rows.append(f'<tr class="{cls}"><td>{html.escape(k)}</td><td>{html.escape(sym)}</td>'
                    f'<td>{html.escape(_defn(q["sym"]))}</td>'
                    f'<td><code>{html.escape(_short(q["src"]))}</code></td><td>{html.escape(_num(q["committed"]))}</td>'
                    f'<td>{html.escape(vol.get(k,""))}</td><td>{html.escape(docs)}</td>'
                    f'<td>{("⚠ "+str(len(dr))) if dr else "ok"}</td></tr>')
    nd = len(drift_rows(qu))
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Value Ledger</title>
<style>
:root{{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#e4e4e4;--drift:#fff4f0;--driftfg:#b3261e;--accent:#0b6bcb}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#15171b;--fg:#e8e8e8;--mut:#9aa0a6;--line:#2b2e35;--drift:#2a1512;--driftfg:#ff8a75;--accent:#5aa2f0}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}}
header{{padding:20px 16px;border-bottom:1px solid var(--line)}}h1{{font-size:19px;margin:0 0 4px}}.sub{{color:var(--mut);font-size:13px}}
.wrap{{padding:16px}}input{{width:100%;max-width:440px;padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg);margin-bottom:12px;font-size:15px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{position:sticky;top:0;background:var(--bg);cursor:pointer;white-space:nowrap}}tr.drift{{background:var(--drift)}}tr.drift td:last-child{{color:var(--driftfg);font-weight:600}}
code{{font:12px/1.4 ui-monospace,Menlo,monospace}}.pill{{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;font-weight:600;background:var(--drift);color:var(--driftfg)}}
</style></head><body>
<header><h1>Value Ledger</h1><div class=sub>{len(qu)} cited quantities · <span class=pill>{nd} confirmed drift</span> · generated from citation_index + cite_check live values. Tap a header to sort; the box filters all columns.</div></header>
<div class=wrap><input id=q placeholder="filter — e.g. Sy, β₃, report9, ⚠ / drift…">
<table id=t><thead><tr><th>Quantity</th><th>Symbol</th><th>Definition / §</th><th>Source CSV</th><th>Committed</th><th>Volatility</th><th>Cited in</th><th>Drift</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<script>
const q=document.getElementById('q'),rs=[...document.querySelectorAll('#t tbody tr')];
q.addEventListener('input',()=>{{const v=q.value.toLowerCase();rs.forEach(r=>r.style.display=r.textContent.toLowerCase().includes(v)?'':'none')}});
document.querySelectorAll('#t th').forEach((th,i)=>th.addEventListener('click',()=>{{const tb=th.closest('table').querySelector('tbody');const a=th.dataset.a=th.dataset.a==='1'?'':'1';
[...tb.rows].sort((x,y)=>(a?1:-1)*x.cells[i].textContent.localeCompare(y.cells[i].textContent,undefined,{{numeric:true}})).forEach(r=>tb.appendChild(r))}}));
</script></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--stdout", action="store_true")
    a = ap.parse_args()
    qu, vol, smap = build()
    dr = drift_rows(qu)
    if a.check:
        if dr:
            print(f"value_ledger: {len(dr)} CONFIRMED value(s) drift from their committed CSV:")
            for k, q, o in sorted(dr, key=lambda t: t[0]):
                print(f"  {k}: {_short(o['doc']).replace('.md','')} quotes {o['quoted']}, CSV renders {o['want']}")
            print("\n  Regenerate the affected tables/prose, then rerun. Ledger: notes/ledgers/VALUE_LEDGER.md")
            return 1
        print(f"value_ledger: OK — {len(qu)} cited quantities, 0 confirmed drift.")
        return 0
    if a.stdout:
        print(render_master_md(qu, vol)); return 0
    OUT_MD.write_text(render_master_md(qu, vol), encoding="utf-8")
    OUT_MD_REPORT.write_text(render_report_md(qu, smap), encoding="utf-8")
    OUT_HTML.write_text(render_html(qu, vol), encoding="utf-8")
    OUT_HTML_REPORT.write_text(render_report_html(qu, smap), encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(REPO)}, {OUT_MD_REPORT.relative_to(REPO)}, {OUT_HTML.relative_to(REPO)}")
    print(f"  {len(qu)} cited quantities; {len(dr)} confirmed drift(s).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
