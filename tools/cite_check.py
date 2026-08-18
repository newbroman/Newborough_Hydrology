#!/usr/bin/env python3
"""
cite_check.py
=============
Standing check that the document corpus still agrees with the committed
pipeline outputs.

tools/audit_number_drift.py is CHANGE-triggered: it diffs two git refs and
hunts for renderings of the value that just changed. It cannot see a number
that went stale before anyone was watching — which is how report9 and Paper 1
both carried five superseded cluster coefficients for weeks while the tooling
reported clean.

This tool is STANDING: it asks, of every value the pipeline currently publishes,
whether the corpus still quotes it — and, where it does not, whether the corpus
quotes a NEAR MISS instead. A near miss is the signature of a stale citation:
0.090 where the CSV now says 0.088, VIF 1.11 where it says 1.09.

It also evaluates a small register of CLAIMS — the assertions that carry no
number and so no numeric tool can check. "C4 has the lowest VIF in the network"
is either true of the committed CSV or it is not; the register makes that
machine-decidable and names every document asserting it.

Usage:
    python3 tools/cite_check.py                  # numbers + claims
    python3 tools/cite_check.py --claims-only
    python3 tools/cite_check.py --dp 2 3 4 --near 2
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]

# Mirrors, plus the documents that are already text. Never the ODTs. Keep in
# step with refresh_mirrors.py.
#
# "docs/**/text/*.md" replaces the two narrower docs globs so that adding a
# mirror directory to refresh_mirrors.py is enough - the corpus follows, and a
# document cannot be mirrored but unchecked.
#
# The repo's own markdown and index.html need no mirror: they are text already,
# and strip_markup() handles index.html's HTML. index.html is the only published
# page that states pipeline numbers, and only its step and phase counts were
# protected before 2026-08-18, via the PL markers.
DOC_GLOBS = [
    "report_edits/text/report*.md",
    "docs/**/text/*.md",
    "index.html",
    "readme.md",
    "PIPELINE_README.md",
    "REPORT_STRUCTURE.md",
    "DECISION_LOG.md",
    "ledgers/*.md",
]

# Headline tables whose values are cited directly rather than via a
# report-numbers key. (csv path, key column, value columns).
HEADLINE_TABLES = [
    ("outputs/03_state_space_model/03_03_cluster_mechanistic_coefficients.csv",
     "Cluster_Label",
     # Every column the mechanistic table renders, so the whole table is
     # covered rather than four of its six numeric columns.
     ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage",
      "R2", "LCSC_percent"]),
]

# Claims register. rule is evaluated against the named CSV.
#   argmin:<col>  / argmax:<col>  -> `expect` must be the value of `key_col`
# Extend this rather than restating a claim in prose.
CLAIMS_REGISTER = "tools/claims_register.csv"

# Exact citation index, built by tools/build_citation_index.py. Each row says
# "key K is quoted in document D as the literal string S". When the index has a
# row, the check is EXACT — no proximity guessing, no near-miss heuristic. The
# heuristic scan is then only for values the index does not yet cover.
CITATION_INDEX = "tools/citation_index.csv"

# Archived output trees produced by no live script — their values are history,
# not current publications, so they must not drive a staleness verdict.
EXCLUDE_OUTPUT_DIRS = ("30_c4_constrained_fit",)

# A rendering is searchable only if it carries enough significant digits to be
# distinctive. "0.02" matches thousands of unrelated places; "0.0183" does not.
MIN_SIG_DIGITS = 3

# Significant digits alone are not enough. In documents dense with per-well
# tables almost any 3-digit value collides with SOMETHING: the first triage run
# reported 14 hits above a 1% gap and all 14 were coincidences — a BACI spring
# shift "matched" the upper end of a cluster's beta_3 range, a p-value "matched"
# a seasonal amplitude in metres. A near miss is evidence only when it sits near
# a token identifying the quantity. Anchors are derived from the key.
ANCHOR_WINDOW = 400          # characters either side of the candidate number
_STOPWORDS = {
    "mean", "median", "shift", "after", "before", "step", "pct", "percent",
    "delta", "diff", "value", "total", "count", "min", "max", "range", "sum",
    "headline", "resid", "residual", "impact", "control", "ctrl", "model",
    "spring", "summer", "winter", "annual", "monthly", "per", "well", "wells",
    "cluster", "vs", "and", "the", "for", "with", "from", "test", "fit",
    "depth", "minimum", "maximum", "coeff", "intercept", "slope", "weight",
    # cluster-label words: they appear on every row of every per-well table
    "forest", "dune", "lake", "edge", "coastal", "residual", "western", "main",
    "warren", "reference", "extended", "calibration",
}


def anchors(key: str) -> list[str]:
    """Distinctive tokens from a report-numbers key: well ids, cluster ids,
    topic words. Generic words are dropped — they anchor nothing."""
    out = []
    for t in re.split(r"[_\W]+", key):
        if not t or t.lower() in _STOPWORDS:
            continue
        if re.fullmatch(r"(?i)(ceh|nw|wmc|lis|fe|d|t)\d+[a-z]?", t):
            out.append(t)                       # well id
        elif re.fullmatch(r"(?i)c[1-5]", t):
            out.append(t)                       # cluster id
        elif t.isupper() and len(t) >= 3:
            out.append(t)                       # acronym: BACI, ANCOVA, MSL...
        elif len(t) >= 5 and not t.isdigit():
            out.append(t)                       # topic word
    return out


def anchored(text: str, needle: str, keys: list[str]) -> bool:
    """True if `needle` occurs anywhere within ANCHOR_WINDOW of an anchor."""
    if not keys:
        return True
    low = text.lower()
    lowkeys = [k.lower() for k in keys]
    for m in re.finditer(re.escape(needle), text):
        window = low[max(0, m.start() - ANCHOR_WINDOW): m.start() + ANCHOR_WINDOW]
        if any(k in window for k in lowkeys):
            return True
    return False


def _sig_digits(s: str) -> int:
    return len(re.sub(r"[^1-9]", "", s.lstrip("-0.").replace(".", "")) or "") + \
        len(re.findall(r"(?<=[1-9])0", s.replace(".", "")))


def searchable(s: str) -> bool:
    digits = re.sub(r"[^0-9]", "", s).lstrip("0")
    return len(digits) >= MIN_SIG_DIGITS


# An HTML tag: opens with a letter (element) or "!" (comment/doctype) and, in
# particular, contains NO further "<". That exclusion is load-bearing. The
# earlier pattern <[^>]+> matched from any "<" to the next ">" anywhere in the
# file, and the mirrors are full of bare less-than signs — every "p < 0.001" in
# a statistics table. One such "<" swallowed everything up to the next ">",
# which was typically hundreds of lines later, deleting whole tables of cited
# values before the checker ever saw them: report9 stripped from 267 kB to
# 97 kB, and 117 indexed citations were reported MOVED when the numbers were
# sitting in the document all along. Silent blindness, not noise — a drifted
# value inside a swallowed table could never have been caught. See D-018.
_MARKUP = re.compile(r"</?[A-Za-z!][^<>]*>")
_IMGREF = re.compile(r"!?\[[^\]]*\]\([^)]*\)")   # markdown links / images


def strip_markup(text: str) -> str:
    """Remove markup so only prose and table CONTENT is searched.

    The mirrors carry raw HTML for figures and tables. Without this, a CSS
    dimension (style="height:10.118cm") or an image filename is a searchable
    number, and every one of them is a false positive waiting to happen.
    """
    return _IMGREF.sub(" ", _MARKUP.sub(" ", text))


def load_documents() -> dict[str, str]:
    docs: dict[str, str] = {}
    for g in DOC_GLOBS:
        for p in REPO.glob(g):
            try:
                docs[str(p.relative_to(REPO))] = strip_markup(
                    p.read_text(encoding="utf8"))
            except OSError:
                pass
    return docs


def render(v: float, dp: int) -> str:
    return f"{v:.{dp}f}"


def near_misses(v: float, dp: int, span: int) -> list[str]:
    """Renderings within `span` units of the last decimal place, excluding v."""
    step = 10 ** -dp
    out = []
    for k in range(-span, span + 1):
        if k == 0:
            continue
        out.append(render(v + k * step, dp))
    return out


def collect_values() -> list[tuple[str, str, float]]:
    """[(source, label, value)] from report-numbers files and headline tables."""
    vals: list[tuple[str, str, float]] = []
    for p in sorted(REPO.glob("outputs/**/*report_numbers*.csv")):
        if any(d in p.parts for d in EXCLUDE_OUTPUT_DIRS):
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = {c.lower(): c for c in df.columns}
        kcol = cols.get("key") or df.columns[0]
        vcol = cols.get("value")
        if vcol is None:
            num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if not num:
                continue
            vcol = num[0]
        for _, r in df.iterrows():
            try:
                vals.append((str(p.relative_to(REPO)), str(r[kcol]), float(r[vcol])))
            except (TypeError, ValueError):
                continue
    for rel, kcol, vcols in HEADLINE_TABLES:
        p = REPO / rel
        if not p.exists():
            continue
        df = pd.read_csv(p)
        for _, r in df.iterrows():
            for c in vcols:
                try:
                    vals.append((rel, f"{r[kcol]} · {c}", float(r[c])))
                except (TypeError, ValueError, KeyError):
                    continue
    return vals


def check_numbers(docs, dps, span, min_rel=0.0, csv_out=None) -> int:
    print("=" * 78)
    print("NUMBERS — every published value vs the corpus")
    print("=" * 78)
    stale, uncited, ok = [], [], 0
    seen: set[tuple[str, float]] = set()
    for source, label, v in collect_values():
        if not (abs(v) > 0):
            continue
        # 10_consolidated_report_numbers.csv republishes the per-script 10x
        # values verbatim; counting both inflates the hit list without adding
        # a single new place to check.
        if (label, v) in seen:
            continue
        seen.add((label, v))
        hit_dp = None
        anc = anchors(label)
        for dp in dps:
            s = render(v, dp)
            if not searchable(s):
                continue
            if any(s in t and anchored(t, s, anc) for t in docs.values()):
                hit_dp = dp
                break
        if hit_dp is not None:
            ok += 1
            continue
        found = []
        for dp in sorted(dps, reverse=True):   # most precise first
            if not searchable(render(v, dp)):
                continue
            anc = anchors(label)
            for nm in near_misses(v, dp, span):
                if not searchable(nm):
                    continue
                where = [d for d, t in docs.items()
                         if nm in t and anchored(t, nm, anc)]
                if where:
                    found.append((nm, dp, where))
            if found:
                break                          # one precision level is enough
        if found:
            gaps = [abs(float(nm) - v) / abs(v) for nm, _, _ in found]
            rel = min(gaps) if gaps else 0.0
            if rel >= min_rel:
                stale.append((source, label, v, found, rel))
        else:
            uncited.append((source, label, v))

    stale.sort(key=lambda r: -r[4])          # widest gap first: triage top-down

    if csv_out:
        import csv as _csv
        with open(csv_out, "w", newline="", encoding="utf8") as fh:
            w = _csv.writer(fh)
            w.writerow(["rel_gap_pct", "key", "committed", "corpus_value",
                        "documents", "source_csv"])
            for source, label, v, found, rel in stale:
                nm, _dp, where = found[0]
                w.writerow([f"{rel*100:.2f}", label, f"{v:g}", nm,
                            "; ".join(sorted(where)), source])
        print(f"  triage list written to {csv_out}")
    else:
        for source, label, v, found, rel in stale:
            print(f"\n  STALE?  {label}   (gap {rel*100:.2f}%)")
            print(f"          committed {v:g}   ({source})")
            for nm, dp, where in found[:3]:
                print(f"          corpus has {nm} at {dp}dp in: "
                      f"{', '.join(sorted(where))}")

    print(f"\n  {ok} value(s) cited and current; {len(stale)} possible stale "
          f"citation(s){f' above {min_rel*100:g}%' if min_rel else ''}; "
          f"{len(uncited)} not cited anywhere (informational).")
    return len(stale)


def check_index(docs, values) -> int:
    """Exact verification of every indexed citation.

    Three outcomes per row, and the distinction matters:
      OK       the document still quotes the current value.
      DRIFTED  the document still contains the indexed string, but the pipeline
               value has moved — the citation is now stale. This is the failure
               the whole exercise exists to catch, and it is exact: no
               proximity, no rounding guess.
      MOVED    the indexed string is gone from the document. Usually the prose
               was rewritten. Not an error, but the index row needs re-pointing
               or the citation has been dropped.
    """
    idx = REPO / CITATION_INDEX
    print()
    print("=" * 78)
    print("CITATIONS — exact check of the citation index")
    print("=" * 78)
    if not idx.exists():
        print(f"  no index at {CITATION_INDEX} — run "
              "tools/build_citation_index.py")
        return 0

    current = {}
    for _src, label, v in values:
        current.setdefault(label, v)

    ok = drifted = moved = unknown = advisory = 0
    for row in csv.DictReader(open(idx, encoding="utf8")):
        # Rejected rows are recorded coincidences — keeping them stops the
        # builder re-proposing them, but they are not citations to check.
        if row.get("status") == "rejected":
            continue
        key, doc, quoted = row["key"], row["document"], row["quoted"]
        text = docs.get(doc)
        if text is None:
            continue
        if key not in current:
            unknown += 1
            continue
        dp = len(quoted.split(".")[1]) if "." in quoted else 0
        want = render(current[key], dp)
        present = quoted in text
        if present and want == quoted:
            ok += 1
        elif present:
            if row.get("status") == "confirmed":
                drifted += 1
            else:
                advisory += 1
            print(f"\n  DRIFTED  {key}  [{row.get('status','')}]")
            print(f"           {doc} quotes {quoted}, pipeline now says {want}")
            if row.get("before") or row.get("after"):
                print(f"           ...{row.get('before','')[-50:]} "
                      f"[{quoted}] {row.get('after','')[:50]}...")
        else:
            moved += 1
            if want in text:
                ok += 0   # value updated in prose but index not re-pointed
                print(f"\n  REPOINT  {key}: {doc} now quotes {want} "
                      f"(index still says {quoted}) — update the index row")
            else:
                print(f"\n  MOVED    {key}: {quoted} no longer in {doc} "
                      "— prose rewritten, or citation dropped")
    print(f"\n  {ok} citation(s) exact and current; {drifted} DRIFTED "
          f"(confirmed rows — these gate); {advisory} drifted on unreviewed "
          f"rows (advisory); {moved} moved/re-pointed; "
          f"{unknown} key(s) no longer published.")
    return drifted


def check_claims(docs) -> int:
    reg = REPO / CLAIMS_REGISTER
    print()
    print("=" * 78)
    print("CLAIMS — assertions with no number, checked against the CSV")
    print("BREACH = the CSV says the claim is false AND a document asserts it")
    print("=" * 78)
    if not reg.exists():
        print(f"  no register at {CLAIMS_REGISTER} — skipped")
        return 0
    bad = 0
    for row in csv.DictReader(open(reg, encoding="utf8")):
        p = REPO / row["csv"]
        if not p.exists():
            print(f"  SKIP   {row['claim_id']}: {row['csv']} missing")
            continue
        df = pd.read_csv(p)
        kind, _, col = row["rule"].partition(":")
        if kind not in {"argmin", "argmax"} or col not in df.columns:
            print(f"  SKIP   {row['claim_id']}: unsupported rule {row['rule']!r}")
            continue
        idx = df[col].idxmin() if kind == "argmin" else df[col].idxmax()
        actual = str(df.loc[idx, row["key_col"]])
        holds = actual == row["expect"]

        needle = row.get("phrase", "").strip()
        where = [d for d, t in docs.items() if needle in t] if needle else []

        # Gate on ASSERTED-AND-FALSE, not on false alone. Entries kept as
        # tripwires are false by design — that is the point of keeping them.
        asserted_false = (not holds) and bool(where)
        if asserted_false:
            bad += 1

        verdict = "BREACH" if asserted_false else ("HOLDS " if holds else "false ")
        did = (row.get("decision_id") or "").strip()
        print(f"  {verdict} {row['claim_id']}"
              f"{f' [{did}]' if did else ''}: {row['assertion']}")
        if not holds:
            print(f"          {row['rule']} is {actual!r}, not {row['expect']!r}")
        if where:
            print(f"          asserted in: {', '.join(sorted(where))}")
        elif not holds:
            print("          not asserted in the corpus — tripwire only")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dp", nargs="+", type=int, default=[2, 3, 4])
    ap.add_argument("--near", type=int, default=2,
                    help="near-miss span in units of the last decimal place")
    ap.add_argument("--claims-only", action="store_true")
    ap.add_argument("--index-only", action="store_true",
                    help="exact citation-index check only; skip the heuristic "
                         "near-miss scan")
    ap.add_argument("--min-rel", type=float, default=0.0,
                    help="only report hits whose relative gap exceeds this "
                         "(e.g. 0.005 hides rounding-level differences)")
    ap.add_argument("--csv", default=None,
                    help="write the triage list to a CSV and print a summary only")
    args = ap.parse_args()

    docs = load_documents()
    if not docs:
        print("No mirrors found — run tools/refresh_mirrors.py first.")
        return 1
    print(f"corpus: {len(docs)} mirror(s)\n")

    rc = 0
    if not args.claims_only:
        values = collect_values()
        rc += check_index(docs, values)
        if not args.index_only:
            rc += check_numbers(docs, args.dp, args.near, args.min_rel, args.csv)
    rc += check_claims(docs)
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
