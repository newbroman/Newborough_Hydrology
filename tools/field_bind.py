#!/usr/bin/env python3
"""
field_bind.py — propose a binding for every number in a document, for review and conversion to fields.

WHY (spec claude/NRG_spec_report_fields_2026-10-09.md; Martin, 2026-10-09: "I find it hard to trust the
numbers, even the green numbers are flagged wrong")
  proof_copy colours a number by inference: green means a committed value with those digits sits in the
  section's sources, not that the sentence means it. A number field (D-219) binds the printed text to ONE
  committed value — file, key, rounding — and field_sync --check proves it on every ship. This tool makes
  the first step: it proposes, for every number in a chapter, the binding a field would carry, classes the
  numbers that are not pipeline values (literals, literature constants, derived quantities), and writes one
  row per number for the independent reading pass and Martin's review. Nothing here edits a document.

CLASSES (column `class`)
  field      a registered committed value (cite_check value tables or config.py); `spec` reproduces the
             printed text exactly, so conversion cannot change a character
  register   a value found only in a CSV no value table covers: the file must be registered first
  derived    counted from a file's geometry/columns (network counts, KML areas); no script emits it
  literal    a count, year, k, bound, definitional value, or a number the reading pass called literal
  vetted     Martin's earlier verdict holds (proof_reading_verdicts.csv)
  cited      a literature value in a citing clause, not a pipeline value
  unresolved the matcher found no binding it trusts (untraced / elsewhere / stale / tie / unknown):
             the best guess, if any, is given for the reader

Usage:
    python3 tools/field_bind.py propose report9            # -> scratch/bind/report9_proposals.csv
    python3 tools/field_bind.py review report9 --seed 20261009
        # proposals + the independent reading (scratch/bind/read/*.csv) + verified rebinds
        # (scratch/bind/report9_rebinds.json) -> tools/field_bindings/report9.csv, the tracked register,
        # with each row's status and whether it is in Martin's review queue
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-10-09 (spec NRG_spec_report_fields_2026-10-09). First issue: propose.

import argparse
import bisect
import csv
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import proof_copy as pc       # noqa: E402
import cite_check as cc       # noqa: E402
import field_sync as fs       # noqa: E402

OUT = REPO / "scratch" / "bind"
SCALES = (1, 100, 1000, 0.001, -1, -100, -1000)
_LEVEL = " as a level (negative below ground)"
FIELDS = ["rid", "doc", "section", "offset", "number", "verdict", "class", "source_csv", "key", "row", "column",
          "value", "spec", "field", "description", "runner_up", "margin", "sentence"]


def spec_for(v: float, quoted: str) -> dict | None:
    """A field_sync rendering spec whose rendering of v is exactly `quoted`, or None."""
    q = quoted.strip().replace("−", "−")
    m = re.fullmatch(r"([+−\-]?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?", q)
    if not m:
        return None
    sign, whole, frac = m.groups()
    row0 = {"dp": str(len(frac or "")), "plus": "1" if sign == "+" else "",
            "minus": sign if sign in ("−", "-") else "−", "thousands": "," if "," in whole else ""}
    for absf in ("", "1"):                     # a signed scale before |x|: "+0.09" is −(−0.09), a level
        for scale in SCALES:
            row = dict(row0, scale=str(scale), abs=absf)
            if fs.render(v, row) == q:
                return row
    return None


def field_name(key: str, spec: dict) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_")
    sc = spec["scale"]
    tag = "" if sc == "1" else "_x" + sc.replace(".", "p").replace("-", "neg")
    tag += "_abs" if spec["abs"] else ""
    tag += f"_dp{spec['dp']}"
    tag += "_plus" if spec["plus"] else ""
    tag += "_hy" if spec["minus"] == "-" else ""
    tag += "_th" if spec["thousands"] else ""
    return base + tag


_NOTES: dict[tuple[str, str], str] = {}


def _load_notes() -> None:
    """Each registered key's own description: the report_numbers Note column, config's comment."""
    for f in sorted(REPO.glob("outputs/**/*report_numbers*.csv")):
        rel = str(f.relative_to(REPO))
        try:
            rows = list(csv.DictReader(open(f, encoding="utf-8")))
        except Exception:
            continue
        for r in rows:
            p = (r.get("Parameter") or "").strip()
            if not p:
                continue
            q = [x for x in ((r.get("Well") or "").strip(), (r.get("Era") or "").strip()) if x]
            note = (r.get("Note") or r.get("Description") or "").strip()
            unit = (r.get("Unit") or "").strip()
            for k in {p, " · ".join([p] + q), " · ".join(q + [p]) if q else p}:
                _NOTES[(rel, k)] = (note + (f" [{unit}]" if unit else "")).strip()
    for rel in cc.CONSTANT_SOURCES:
        for line in (REPO / rel).read_text(encoding="utf-8").splitlines():
            m = re.match(r"^([A-Z][A-Z0-9_a-z]*)\s*=\s*[^#]*#\s*(.*)$", line)
            if m:
                _NOTES[(rel, m.group(1))] = m.group(2).strip()


def _reg_key(valmap: dict, c) -> str | None:
    """A cell or column statistic the matcher found in a REGISTERED table, as that table's own key:
    "2012" · Annual_P_mm -> "2012 · Annual_P_mm"; "max of Annual_P_mm" -> the row that holds the max."""
    lab = c.label
    for k in (lab, f"{lab} · {c.col}", f"{c.col} · {lab}"):
        if (c.rel, k) in valmap:
            return k
    hits = [k for (r, k), v in valmap.items() if r == c.rel and k.endswith(" · " + c.col)
            and abs(v - c.value) <= 1e-9 * max(1.0, abs(v))]
    return hits[0] if len(hits) == 1 else None


def describe(rel: str, key: str) -> str:
    d = _NOTES.get((rel, key))
    if d is None:
        d = next((v for (r, k), v in _NOTES.items() if r == rel and (k.startswith(key) or key.startswith(k))), "")
    return d[:300]


def propose(stem: str) -> list[dict]:
    values = cc.collect_values()
    look = pc.build_index(values, deep=True)
    mirror = pc.resolve_doc(stem)
    pc._DOC_STEM[0] = mirror.stem
    rel = str(mirror.relative_to(REPO))
    text = mirror.read_text(encoding="utf8")
    pc.TEXT_CACHE = text
    secs = pc.section_numbers(mirror)
    scope_map = pc.section_scope(text, secs, mirror.stem)
    masked = pc.mask_markup(text)
    idx = pc.index_spans(masked, rel, values)
    pc.CHOSEN.clear()
    marks = pc.classify(text, look, idx, secs, scope_map)
    rv = pc.reading_verdicts() or {}
    valmap = {(s, k): v for s, k, v in values}
    _load_notes()
    line_starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def sec_of(pos: int) -> str:
        ln = bisect.bisect_right(line_starts, pos) - 1
        cur = ""
        for hl, numb, h in secs:
            if hl <= ln:
                cur = f"{numb} {h}".strip()
        return cur

    rows = []
    for s, e, v, d in marks:
        num = text[s:e]
        sent = " ".join(pc._sentence(masked, s, e, full=True).split())
        off = s - masked.rfind("\n", 0, s)
        rid = f"{mirror.stem}:{pc._reading_id(num, sent, off)}"
        sec = sec_of(s)
        row = dict(rid=rid, doc=mirror.stem, section=sec, offset=s, number=num, verdict=v, sentence=sent[:600])
        hit = rv.get(rid)
        if hit and hit[0] == "vetted":
            row.update({"class": "vetted", "description": hit[1]})
        elif hit and hit[0] == "literal":
            row.update({"class": "literal", "description": hit[1], "source_csv": hit[2] if len(hit) > 2 else ""})
        elif v in ("count", "bound", "qty"):
            row.update({"class": "literal", "description": d.split(" ‖ ")[0][:200]})
        elif v == "cited":
            row.update({"class": "cited", "description": d.split(" ‖ ")[0][:200]})
        else:
            ch = pc.CHOSEN.get((s, e))
            ix = idx.get((s, e))
            if ix is not None and ix.get("committed") is not None and v in ("traced", "rounding", "stale", "unknown"):
                src, key, val = ix["source_csv"], ix["key"], ix["committed"]
                row.update(source_csv=src, key=key, value=val)
            elif ch is not None:
                c, rival, score, margin = ch
                key = c.label
                val = c.value
                if c.tier == "reg" or (c.rel in cc.CONSTANT_SOURCES):
                    if key.endswith(_LEVEL):
                        key = key[: -len(_LEVEL)]
                        val = valmap.get((c.rel, key), -c.value)
                    row.update(source_csv=c.rel, key=key, value=val)
                elif c.rel in pc.REG_FILES and c.col and _reg_key(valmap, c) is not None:
                    key = _reg_key(valmap, c)
                    row.update(source_csv=c.rel, key=key, value=valmap[(c.rel, key)])
                elif c.tier in ("net", "geo"):
                    row.update({"class": "derived", "source_csv": c.rel, "key": c.label, "value": c.value})
                else:
                    row.update({"class": "register", "source_csv": c.rel, "row": c.label, "column": c.col or "", "value": c.value})
                if rival is not None:
                    row["runner_up"] = f"{rival.label}{(' · ' + rival.col) if rival.col else ''} = {rival.value:g} [{pathlib.Path(rival.rel).name}]"
                row["margin"] = "" if margin is None else f"{margin:.1f}"
            if not row.get("class"):
                if row.get("key"):
                    sp = spec_for(float(row["value"]), num.replace("−", "−"))
                    if sp is None:
                        row["class"] = "unresolved"
                        row["description"] = "no rendering of the bound value reproduces the printed text exactly"
                    else:
                        row["spec"] = ";".join(f"{k}={sp[k]}" for k in ("scale", "abs", "dp", "plus", "minus", "thousands"))
                        row["field"] = field_name(row["key"], sp)
                        row["class"] = "field" if v in ("traced", "rounding") else "unresolved"
                    row["description"] = row.get("description") or describe(row["source_csv"], row["key"])
                else:
                    row["class"] = "unresolved"
            if row["class"] == "unresolved":
                row["description"] = (row.get("description") or "") + (" ‖ " if row.get("description") else "") + d.split(" ‖ ")[0][:200]
        rows.append({k: row.get(k, "") for k in FIELDS})
    return rows


REG_DIR = REPO / "tools" / "field_bindings"
REG_FIELDS = ["rid", "section", "number", "status", "source_csv", "key", "value", "spec", "field", "matcher_key",
              "reader", "reader_reason", "reader_better", "queue", "martin", "martin_note", "sentence"]


def review(stem: str, seed: int, sample: float = 0.10) -> list[dict]:
    """Merge the proposal, the independent reading and the mechanically verified rebinds into one
    register row per number, and choose Martin's queue (spec: doubts, unresolved, literature/config,
    reader-literal overrides, and a seeded random sample of the rest)."""
    import glob
    import json
    import random
    P = list(csv.DictReader(open(OUT / f"{stem}_proposals.csv", encoding="utf-8")))
    J = {}
    for f in sorted(glob.glob(str(OUT / "read" / "b*.csv"))):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            J[r["rid"]] = r
    RB = json.load(open(OUT / f"{stem}_rebinds.json", encoding="utf-8")) if (OUT / f"{stem}_rebinds.json").exists() else {}
    rows = []
    for p in P:
        j = J.get(p["rid"], {})
        jv = (j.get("judgement") or "").strip()
        r = dict(rid=p["rid"], section=p["section"], number=p["number"], source_csv=p["source_csv"],
                 key=p["key"] or (p["row"] + (" · " + p["column"] if p["column"] else "")), value=p["value"],
                 spec=p["spec"], field=p["field"], matcher_key=p["key"], reader=jv,
                 reader_reason=j.get("reason", ""), reader_better=j.get("better", ""), queue="", martin="",
                 martin_note="", sentence=p["sentence"])
        cls = p["class"]
        if cls in ("literal", "vetted", "cited") and jv in ("", "literal", "means"):
            r["status"] = "literal" if cls != "vetted" else "vetted"
        elif jv == "literal":
            r["status"] = "literal"
            if cls == "field":
                r["queue"] = "reader-literal"
        elif jv == "means" and cls == "field":
            r["status"] = "field"
            if r["source_csv"] in cc.CONSTANT_SOURCES:
                r["queue"] = "literature"
        elif jv == "means" and cls == "register":
            r["status"] = "register"
        elif jv == "means" and cls == "derived":
            r["status"] = "derived"
        elif jv == "wrong" and RB.get(p["rid"], [None])[0] == "rebind":
            src, key, val, sp = RB[p["rid"]][1]
            spec = ";".join(f"{k}={sp[k]}" for k in ("scale", "abs", "dp", "plus", "minus", "thousands"))
            r.update(status="rebind", source_csv=src, key=key, value=val, spec=spec, field=field_name(key, sp))
        else:
            r["status"] = "review"
            r["queue"] = "doubt" if jv == "doubt" else "unresolved" if cls == "unresolved" or jv == "wrong" else "check"
        rows.append(r)
    rest = [r for r in rows if not r["queue"] and r["status"] in ("field", "rebind", "register", "derived")]
    rng = random.Random(seed)
    for r in rng.sample(rest, max(1, round(sample * len(rest)))):
        r["queue"] = "sample"
    REG_DIR.mkdir(parents=True, exist_ok=True)
    with open(REG_DIR / f"{stem}.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REG_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("propose")
    p.add_argument("doc")
    p.add_argument("--summary", action="store_true")
    q = sub.add_parser("review")
    q.add_argument("doc")
    q.add_argument("--seed", type=int, default=20261009)
    a = ap.parse_args()
    if a.cmd == "review":
        from collections import Counter
        rows = review(a.doc, a.seed)
        print(f"field_bind review {a.doc}: {len(rows)} numbers — " + ", ".join(f"{k} {n}" for k, n in Counter(r['status'] for r in rows).most_common()))
        print("  Martin's queue: " + ", ".join(f"{k} {n}" for k, n in Counter(r['queue'] for r in rows if r['queue']).most_common())
              + f" = {sum(1 for r in rows if r['queue'])}")
        print(f"  wrote {(REG_DIR / (a.doc + '.csv')).relative_to(REPO)}")
        return 0
    rows = propose(a.doc)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{a.doc}_proposals.csv"
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    c = Counter(r["class"] for r in rows)
    print(f"field_bind {a.doc}: {len(rows)} numbers — " + ", ".join(f"{k} {n}" for k, n in c.most_common()))
    print(f"  wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
