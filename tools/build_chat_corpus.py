#!/usr/bin/env python3
"""build_chat_corpus.py — the published corpus the project chatbot answers from.

The chatbot (stage 1: a private Claude artifact; stage 3: the public site)
answers only from what this tool emits: `outputs/chat/chat_corpus.json`, and the
page `outputs/chat/chatbot.html` that embeds it. What goes in is decided by ONE
allowlist, `tools/chat_corpus_sources.csv`; what can never go in is decided by
the DENYLIST below, which is checked on every path the allowlist expands to. An
allowlist typo can therefore widen nothing past the denylist: the papers under
review, the working decision log and the private store stay out however the
allowlist is edited.

    python3 tools/build_chat_corpus.py            # build corpus + page
    python3 tools/build_chat_corpus.py --check    # gate: exit 1 if a denied path is
                                                  #   allowlisted, or the published
                                                  #   chatbot is stale
    python3 tools/build_chat_corpus.py --selftest # the denylist catches what it must

Four kinds of entry:
  chunks      prose from the documents, split at headings (heading path kept)
  numbers     rows of committed CSVs — every number the bot may quote, with its file
  references  the literature manifest: citation, source, terms. Citations only —
              the documents are under publisher or agency copyright (literature/README.md)
  meta        commit-independent fingerprint of the sources, for --check

The corpus and page are build artefacts and are NOT committed (4 MB each, and a
new copy on every source change would bloat the public history). What is
committed is `outputs/chat/chat_corpus_stamp.json`: the source fingerprint and
counts of the build that was last published as the chatbot. Staleness is judged
on the SOURCES' content (a sha256 over every included file), never on the commit
hash, so a commit that touches nothing in the corpus does not make it stale; a
commit that does makes --check fail until the corpus is rebuilt and the chatbot
republished.

See claude/NRG_spec_chatbot_2026-10-08.md and the decision recorded with it.
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-08. New: chatbot corpus builder
#   (stage 1). Allowlist tools/chat_corpus_sources.csv; hard denylist; heading
#   chunker; CSV rows as numbers; literature manifest as references; page build
#   from tools/chat_page_template.html; --check on a source fingerprint held in
#   the committed stamp (corpus and page are uncommitted build artefacts).

import argparse
import csv
import fnmatch
import glob
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "tools" / "chat_corpus_sources.csv"
TEMPLATE = ROOT / "tools" / "chat_page_template.html"
OUT_DIR = ROOT / "outputs" / "chat"
OUT_JSON = OUT_DIR / "chat_corpus.json"
OUT_HTML = OUT_DIR / "chatbot.html"
OUT_STAMP = OUT_DIR / "chat_corpus_stamp.json"
PLACEHOLDER = "/*__CHAT_CORPUS__*/null"

# Never in the corpus, whatever the allowlist says. fnmatch on the repo-relative
# path, case-insensitive. Unpublished work and the working record.
DENY = [
    "docs/papers/*",
    "*paper1*", "*paper2*", "*paperm*", "*paper_m*",
    "*decision_log*",
    "working/*", "*handover*", "*changelog*",
    "*_spec_*", "store/*", "ledgers/*",
]
# Literature: only files under literature/open/ (open licence) and the manifest.
LIT_ALLOW = ["literature/README.md", "literature/open/*"]

CHUNK_TARGET = 4000   # characters; a heading section longer than this is split
CHUNK_MAX = 6000      # at paragraph breaks


def denied(rel: str) -> str | None:
    low = rel.lower()
    for pat in DENY:
        if fnmatch.fnmatch(low, pat):
            return pat
    if low.startswith("literature/") and not any(
            fnmatch.fnmatch(low, p.lower()) for p in LIT_ALLOW):
        return "literature/* (copyright)"
    return None


def expand(pattern: str) -> list[str]:
    hits = sorted(glob.glob(str(ROOT / pattern), recursive=True))
    return [str(Path(h).relative_to(ROOT)) for h in hits if Path(h).is_file()]


def read_sources() -> list[dict]:
    with open(SOURCES, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- text cleanup
_ANCHOR = re.compile(r"\[\]\{#[^}]*\}")
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_ATTR = re.compile(r"\{[#.][^}\n]*\}")


def clean_md(text: str) -> str:
    text = _COMMENT.sub("", text)
    text = _ANCHOR.sub("", text)
    text = _ATTR.sub("", text)
    text = text.replace("\u2003", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def html_text(raw: str) -> str:
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)
    raw = re.sub(r"<br\s*/?>|</(p|div|li|h[1-6]|tr|section)>", "\n", raw, flags=re.I)
    raw = re.sub(r"<h([1-6])[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", raw,
                 flags=re.I)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = html.unescape(raw)
    lines = [ln.strip() for ln in raw.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def pdf_text(path: Path) -> str:
    out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                         capture_output=True, text=True, check=True).stdout
    out = out.replace("\f", "\n")
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", out)).strip()


# --------------------------------------------------------------------- chunker
_HEAD = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def split_long(body: str) -> list[str]:
    if len(body) <= CHUNK_MAX:
        return [body]
    parts, cur = [], ""
    for para in body.split("\n\n"):
        if cur and len(cur) + len(para) > CHUNK_TARGET:
            parts.append(cur)
            cur = ""
        cur = f"{cur}\n\n{para}" if cur else para
        while len(cur) > CHUNK_MAX:          # one enormous paragraph or table
            parts.append(cur[:CHUNK_TARGET])
            cur = cur[CHUNK_TARGET:]
    if cur:
        parts.append(cur)
    return parts


def chunk_markdown(text: str) -> list[tuple[str, str]]:
    """[(heading path, body)] — the body excludes the heading line."""
    out, stack, buf = [], [], []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            path = " > ".join(h for _, h in stack)
            for part in split_long(body):
                out.append((path, part))
        buf.clear()

    for line in text.splitlines():
        m = _HEAD.match(line)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).replace("**", "").strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
        else:
            buf.append(line)
    flush()
    return out


# ------------------------------------------------------------------- numbers
def csv_rows(path: Path, rel: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for i, row in enumerate(csv.DictReader(fh), start=2):
            fields = {k: v for k, v in row.items() if k and v not in (None, "")}
            if fields:
                rows.append({"file": rel, "line": i, "fields": fields})
    return rows


def manifest_rows(path: Path, rel: str) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows, top = [], {}
    for k, v in data.items():
        if isinstance(v, (str, int, float)):
            top[k] = str(v)
        elif isinstance(v, dict):
            for k2, v2 in v.items():
                top[f"{k}.{k2}"] = str(v2)
    rows.append({"file": rel, "line": 0, "fields": top})
    for step in data.get("steps", []):
        if isinstance(step, dict):
            rows.append({"file": rel, "line": 0,
                         "fields": {k: str(v) for k, v in step.items()
                                    if isinstance(v, (str, int, float))}})
    return rows


# ---------------------------------------------------------------- references
def literature_refs(path: Path) -> list[dict]:
    refs, header = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            if header:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        rec = dict(zip(header, cells))
        refs.append({
            "citation": rec.get("citation", ""),
            "source": rec.get("source", ""),
            "terms": rec.get("terms", ""),
        })
    return refs


# ---------------------------------------------------------------------- build
def collect() -> tuple[dict, list[str]]:
    corpus = {"chunks": [], "numbers": [], "references": [], "sources": []}
    problems: list[str] = []
    digest = hashlib.sha256()
    seen = set()
    for src in read_sources():
        files = expand(src["path"])
        if not files and "*" not in src["path"]:
            problems.append(f"allowlisted file missing: {src['path']}")
        for rel in files:
            if rel in seen:
                continue
            seen.add(rel)
            why = denied(rel)
            if why:
                problems.append(f"DENIED {rel} (matches {why})")
                continue
            p = ROOT / rel
            raw = p.read_bytes()
            digest.update(rel.encode() + b"\0" + raw + b"\0")
            kind = src["kind"]
            title = src["title"]
            if kind == "md" and src["path"].startswith("report_edits/"):
                title = f"Report — {Path(rel).stem}"
            if src["path"].startswith("literature/open/"):
                title = Path(rel).stem
            corpus["sources"].append({"path": rel, "kind": kind, "title": title,
                                      "lang": src["lang"]})
            if kind in ("md", "html", "pdf", "text"):
                if kind == "md":
                    text = clean_md(raw.decode("utf-8"))
                elif kind == "html":
                    text = html_text(raw.decode("utf-8"))
                elif kind == "pdf":
                    text = pdf_text(p)
                else:
                    text = raw.decode("utf-8")
                pieces = chunk_markdown(text) if kind in ("md", "html") else \
                    [("", part) for part in split_long(text)]
                for n, (head, body) in enumerate(pieces):
                    corpus["chunks"].append({
                        "id": f"{rel}#{n}", "source": rel, "title": title,
                        "lang": src["lang"], "heading": head, "text": body})
            elif kind == "numbers":
                corpus["numbers"].extend(csv_rows(p, rel))
            elif kind == "json":
                corpus["numbers"].extend(manifest_rows(p, rel))
            elif kind == "references":
                corpus["references"].extend(literature_refs(p))
            else:
                problems.append(f"unknown kind {kind!r} for {rel}")
    corpus["meta"] = {
        "builder": f"tools/build_chat_corpus.py {__version__}",
        "source_sha256": digest.hexdigest(),
        "counts": {k: len(corpus[k]) for k in
                   ("sources", "chunks", "numbers", "references")},
    }
    return corpus, problems


def write_page(corpus_json: str) -> None:
    page = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in page:
        sys.exit(f"template has no {PLACEHOLDER} placeholder")
    # A literal </script> inside the data would end the script element.
    safe = corpus_json.replace("</", "<\\/")
    OUT_HTML.write_text(page.replace(PLACEHOLDER, safe), encoding="utf-8")


def check() -> int:
    corpus, problems = collect()
    rc = 0
    for p in problems:
        print(f"  FAIL {p}")
        rc = 1
    if not OUT_STAMP.exists():
        print(f"  FAIL {OUT_STAMP.relative_to(ROOT)} missing — build and publish the chatbot")
        return 1
    stamp = json.loads(OUT_STAMP.read_text(encoding="utf-8"))
    for path in stamp.get("sources", []):
        if denied(path):
            print(f"  FAIL the published chatbot carries denied {path}")
            rc = 1
    if stamp.get("source_sha256") != corpus["meta"]["source_sha256"]:
        print("  FAIL the published chatbot is stale — rebuild "
              "(python3 tools/build_chat_corpus.py) and republish the artifact")
        rc = 1
    print(f"build_chat_corpus --check: {'OK' if rc == 0 else 'FAIL'}")
    return rc


def selftest() -> int:
    must_deny = [
        "docs/papers/paper_1/text/Paper1.md",
        "docs/papers/paper_2/text/Hollingham_2026_Paper2_amended.md",
        "docs/papers/paper_M/text/PaperM.md",
        "DECISION_LOG.md", "working/updates/HANDOVER_NOTE.md",
        "literature/ranwell_1959_dune_slack_habitat.pdf",
        "literature/stratford_robins_hollingham_nd_hydrology_land_use_two_welsh_dunes.pdf",
        "docs/report/text/Paper1_extract.md",
    ]
    must_allow = [
        "report_edits/text/report9.md", "DECISIONS_PUBLIC.md",
        "docs/report/text/Newborough_Methods_Supplement.md",
        "literature/README.md", "literature/open/van_willegen_2025.md",
        "outputs/20_spatial_figures/20_report_numbers.csv",
    ]
    bad = [p for p in must_deny if not denied(p)] + \
          [p for p in must_allow if denied(p)]
    for p in bad:
        print(f"  selftest FAIL: {p}")
    print(f"build_chat_corpus --selftest: {'OK' if not bad else 'FAIL'}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.check:
        return check()
    corpus, problems = collect()
    for p in problems:
        print(f"  FAIL {p}")
    if any(p.startswith("DENIED") for p in problems):
        print("refusing to write a corpus with a denied path in the allowlist")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(corpus, ensure_ascii=False, separators=(",", ":"))
    OUT_JSON.write_text(text, encoding="utf-8")
    write_page(text)
    OUT_STAMP.write_text(json.dumps({
        "source_sha256": corpus["meta"]["source_sha256"],
        "builder": corpus["meta"]["builder"],
        "counts": corpus["meta"]["counts"],
        "sources": [s["path"] for s in corpus["sources"]],
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    c = corpus["meta"]["counts"]
    print(f"saved {OUT_JSON.relative_to(ROOT)} ({len(text) / 1e6:.2f} MB): "
          f"{c['sources']} sources, {c['chunks']} chunks, {c['numbers']} number rows, "
          f"{c['references']} references")
    print(f"saved {OUT_HTML.relative_to(ROOT)}")
    print(f"saved {OUT_STAMP.relative_to(ROOT)} — commit it when the chatbot is republished")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
