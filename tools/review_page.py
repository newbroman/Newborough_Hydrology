#!/usr/bin/env python3
"""review_page.py — build the review page for a document: the project's default way to put a document in front of
Martin for review (Martin, 2026-11-24: the Paper 1 editing copy "is the clearest you have shown me for a document
edit. Its only drawback is that the figures arent visible please add this to the project as the default way to
present docs for review").

    python3 tools/review_page.py report_edits/text/report9.md              # -> scratch/review/report9/
    python3 tools/review_page.py docs/papers/paper_1/text/Paper1.md --title "Paper 1 review"
    python3 tools/review_page.py --selftest

From a document's markdown MIRROR (never the ODT's XML: the mirror is what the gates already check) it writes

    scratch/review/<doc>/index.html        tools/review_page_template.html, filled in
    scratch/review/<doc>/<doc>.json        the blocks the page shows: headings, paragraphs, list items, figure
                                           captions (all editable), tables (read only), figures (images)
    scratch/review/<doc>/fig/*.jpg         every figure, pulled from the ODT the mirror names and scaled to
                                           FIG_MAX_W px wide, JPEG quality FIG_Q
    working/updates/review_pages/<doc>_blocks_src.json
                                           PRIVATE: each block's raw mirror source beside its id, so an edit read
                                           back from the page's store maps to the ODT passage it came from

then prints the Artifact publish call. The page is an Artifact with the `db` capability: Martin's edits and notes
are saved in its `edits` collection as he types, and Claude reads them with ArtifactData and applies them through
tools/odt_edit.py as the next version. Numbers are fields: the page says so, and an edit to a number is read as
"this is wrong", never written in.
"""
from __future__ import annotations

__version__ = "1.2.0"  # Hollingham (2026) — 2026-11-26 (Martin: "change the existing editing document to include the
#   new drafts, so I can review them in place"). --compare-to CURRENT_MIRROR: the page is built from a DRAFT mirror and
#   every block that differs from the current one is marked - "chg": "changed" (with "was", the current text, shown
#   one click away) or "new" - and every block the draft removes is shown struck through ("k": "del", read only). A
#   changed block paired one-to-one with a current one keeps that block's id, so a note already saved on it stays
#   beside the proposal. --version-label names the draft (edits saved on the page record it).
# 1.1.0  # Hollingham (2026) — 2026-11-24. --keep-ids and --json-name: rebuild an existing page without
#   orphaning the edits already saved on it (the Paper 1 editing copy held two).
# 1.0.0  # Hollingham (2026) — 2026-11-24. New: the Paper 1 editing copy (working/updates/paper1_edit/,
#   2026-11-23) generalised to any mirrored document, with the figures shown.

import argparse
import hashlib
import io
import json
import pathlib
import re
import sys
import zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "tools" / "review_page_template.html"
FIG_MAX_W = 1600
FIG_Q = 82
PUBLISH_BUDGET = 60 * 1024 * 1024      # one Artifact publish carries at most 64 MB

SUP = str.maketrans("0123456789-−+()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁻⁺⁽⁾ⁿ")
SUB = str.maketrans("0123456789-+()", "₀₁₂₃₄₅₆₇₈₉₋₊₍₎")
IMG = re.compile(r"!\[((?:[^\[\]]|\[[^\]]*\])*)\]\((Pictures/[^)\s]+)[^)]*\)(\{[^}]*\})?")


def plain(s: str) -> str:
    """Mirror markdown -> the text a reader sees (as the Paper 1 builder did)."""
    s = re.sub(r"\[\]\{#[^}]*\}", "", s)
    s = re.sub(r"\[([^\]]*)\]\{[^}]*\}", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\^([^^\s]+)\^", lambda m: m.group(1).translate(SUP)
               if all(c in "0123456789-−+()n" for c in m.group(1)) else "^" + m.group(1), s)
    s = re.sub(r"~([^~\s]+)~", lambda m: m.group(1).translate(SUB)
               if all(c in "0123456789-+()" for c in m.group(1)) else m.group(1), s)
    s = s.replace("**", "").replace("---", "—").replace("--", "–")
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)\*", r"\1", s)
    s = re.sub(r"\\(.)", r"\1", s)
    return re.sub(r"[ \t]*\n[ \t]*", " ", s).strip()


def source_odt(md: str) -> tuple[str | None, str]:
    head = md.splitlines()[0] if md else ""
    m = re.search(r"GENERATED MIRROR of (\S+\.odt)", head)
    sha = re.search(r"source-sha256=(\w+)", head)
    return (m.group(1) if m else None), (sha.group(1) if sha else "")


def parse(md: str) -> list[dict]:
    """Blocks in reading order: h, p, li, cap (editable), table (read only), fig (image)."""
    body = re.sub(r"<!--.*?-->\n?", "", md, flags=re.S)
    blocks, sec = [], "Front matter"

    def add(kind, text, src, lvl=0, **kw):
        pid = f"b{len(blocks):04d}_" + hashlib.sha1((kind + src).encode()).hexdigest()[:6]
        blocks.append(dict(id=pid, k=kind, lvl=lvl, sec=sec, t=text, src=src, **kw))

    for raw in re.split(r"\n\s*\n", body):
        if not raw.strip():
            continue
        t = raw.strip("\n")
        m = re.match(r"^(#{1,4})\s+(.*)$", t)
        if m:
            sec = plain(m.group(2))
            add("h", sec, t, lvl=len(m.group(1)))
            continue
        if IMG.search(t):
            caps = []
            for im in IMG.finditer(t):
                add("fig", "", im.group(0), name=im.group(2).split("/", 1)[1], alt=plain(im.group(1))[:200])
                if im.group(1).strip():
                    caps.append(im.group(1))
            rest = IMG.sub("", t).strip()
            for c in caps + ([rest] if rest else []):
                if plain(c):
                    add("cap", plain(c), c)
            continue
        if re.match(r"^\s*(-{3,}|\+[-+]+\+|\|)", t) or re.search(r"\n\s*-{3,}\s+-{3,}", t):
            add("table", t, t)
            continue
        if t.startswith("-   "):
            for item in re.split(r"\n(?=-   )", t):
                add("li", plain(item[4:]), item)
            continue
        if re.match(r"^\*{0,3}(Figure|Table)\s*[\d.:]", t) or re.match(r"^\*{0,3}Figure\b", t):
            add("cap", plain(t), t)        # a caption the mirror keeps as its own paragraph
            continue
        add("p", plain(t), t)
    return blocks


def extract_figures(odt: pathlib.Path, blocks: list[dict], out: pathlib.Path) -> int:
    """Each fig block's image from the ODT, scaled; sets img/w/h. Returns bytes written."""
    from PIL import Image
    total = 0
    (out / "fig").mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(odt) as z:
        names = set(z.namelist())
        for b in blocks:
            if b["k"] != "fig":
                continue
            arc = "Pictures/" + b["name"]
            if arc not in names:
                continue
            try:
                im = Image.open(io.BytesIO(z.read(arc)))
                im.load()
            except Exception:              # an SVG or a format PIL cannot open: shown as missing
                continue
            if im.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", im.size, "white")
                im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1])
                im = bg
            elif im.mode != "RGB":
                im = im.convert("RGB")
            if im.width > FIG_MAX_W:
                im = im.resize((FIG_MAX_W, round(im.height * FIG_MAX_W / im.width)), Image.LANCZOS)
            rel = f"fig/{pathlib.Path(b['name']).stem}.jpg"
            im.save(out / rel, "JPEG", quality=FIG_Q, optimize=True, progressive=True)
            total += (out / rel).stat().st_size
            b.update(img=rel, w=im.width, h=im.height)
    return total


def keep_ids(blocks: list[dict], old: list[dict]) -> int:
    """Give a block the id an earlier page used for the same text, so edits already saved on that page stay attached
    to their paragraphs. Matched on the displayed text, first unused match in order; a changed paragraph gets a new
    id and its saved edit shows on the page as one to reconcile. Returns how many ids were kept."""
    pool: dict[str, list[str]] = {}
    for b in old:
        if b.get("k") in ("p", "li", "cap") and b.get("t"):
            pool.setdefault(b["t"], []).append(b["id"])
    taken = {b["id"] for b in blocks}
    n = 0
    for b in blocks:
        ids = pool.get(b["t"]) if b["k"] in ("p", "li", "cap") else None
        while ids:
            oid = ids.pop(0)
            if oid not in taken:
                taken.discard(b["id"])
                b["id"] = oid
                taken.add(oid)
                n += 1
                break
    return n


def mark_changes(blocks: list[dict], cur: list[dict]) -> tuple[list[dict], dict]:
    """1.2.0: compare the draft's blocks with the current mirror's (both already carrying the live page's ids where
    the text is unchanged). Returns the draft's blocks with the deletions interleaved, and counts."""
    import difflib
    key = lambda b: (b["k"], b.get("t", ""), b.get("name", ""))
    sm = difflib.SequenceMatcher(a=[key(b) for b in cur], b=[key(b) for b in blocks], autojunk=False)
    out: list[dict] = []
    n = {"changed": 0, "new": 0, "deleted": 0}
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out.extend(blocks[j1:j2]); continue
        olds, news = cur[i1:i2], blocks[j1:j2]
        # pair each new block with the most similar unpaired current block of the same kind (ratio >= 0.35);
        # the rest are deletions and additions. Deletions are shown where the current text stood.
        pair: dict[int, int] = {}
        used: set[int] = set()
        for jn, b in enumerate(news):
            best, bi = 0.0, None
            for io, o in enumerate(olds):
                if io in used or o["k"] != b["k"]:
                    continue
                r = difflib.SequenceMatcher(a=o.get("t", ""), b=b.get("t", ""), autojunk=False).ratio()
                if r > best:
                    best, bi = r, io
            if bi is not None and best >= 0.35:
                pair[jn] = bi; used.add(bi)
        for io, o in enumerate(olds):
            if io not in used and o["k"] in ("p", "li", "cap", "h", "fig", "table"):
                out.append({"id": "del_" + o["id"], "k": "del", "sec": o.get("sec", ""), "t": o.get("t", "")
                            or ("[figure " + o.get("name", "") + "]"), "was_k": o["k"]})
                n["deleted"] += 1
        for jn, b in enumerate(news):
            if jn in pair:
                o = olds[pair[jn]]
                b["chg"], b["was"] = "changed", o.get("t", "")
                if b["k"] in ("p", "li", "cap"):
                    b["id"] = o["id"]          # a note saved on the current paragraph stays beside the proposal
                n["changed"] += 1
            else:
                b["chg"] = "new"; n["new"] += 1
            out.append(b)
    return out, n


def build(mirror: pathlib.Path, title: str | None = None, out_root: pathlib.Path | None = None,
          json_name: str | None = None, old_ids: pathlib.Path | None = None,
          compare_to: pathlib.Path | None = None, version_label: str | None = None) -> dict:
    md = mirror.read_text(encoding="utf-8")
    odt_rel, sha = source_odt(md)
    name = mirror.stem
    out = (out_root or REPO / "scratch" / "review") / name
    out.mkdir(parents=True, exist_ok=True)
    blocks = parse(md)
    old_blocks = json.loads(old_ids.read_text(encoding="utf-8"))["blocks"] if old_ids else []
    kept = keep_ids(blocks, old_blocks) if old_ids else 0
    changes = None
    if compare_to:
        cur = parse(compare_to.read_text(encoding="utf-8"))
        if old_ids:
            keep_ids(cur, old_blocks)
        blocks, changes = mark_changes(blocks, cur)
    figbytes = 0
    if odt_rel and (REPO / odt_rel).is_file():
        figbytes = extract_figures(REPO / odt_rel, blocks, out)
    version = pathlib.Path(odt_rel).stem if odt_rel else name
    short = re.sub(r"^[A-Za-z]+\d*_", "", version) if re.search(r"_v\d", version) else version
    if version_label:
        version, short = version_label, version_label
    pub = [{k: b[k] for k in ("id", "k", "lvl", "sec", "t", "img", "w", "h", "alt", "name", "chg", "was", "was_k")
            if k in b} for b in blocks]
    jname = json_name or f"{name}.json"
    (out / jname).write_text(json.dumps({"version": version, "short": short, "sha": sha, "blocks": pub},
                                                 ensure_ascii=False), encoding="utf-8")
    src_dir = REPO / "working" / "updates" / "review_pages"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / f"{name}_blocks_src.json").write_text(json.dumps(
        {"mirror": str(mirror.relative_to(REPO)) if mirror.is_relative_to(REPO) else str(mirror),
         "odt": odt_rel, "version": version, "sha": sha, "blocks": blocks}, ensure_ascii=False, indent=0),
        encoding="utf-8")
    html = TEMPLATE.read_text(encoding="utf-8")
    title = title or f"{name} review"
    html = (html.replace("__TITLE__", title).replace("__DOCNAME__", title.replace(" review", ""))
                .replace("__JSON__", jname).replace("__LKEY__", f"{name}_review_local"))
    (out / "index.html").write_text(html, encoding="utf-8")
    figs = [b for b in blocks if b["k"] == "fig"]
    return dict(out=out, name=name, jname=jname, kept=kept, version=version, blocks=len(blocks), figs=len(figs),
                changes=changes,
                figs_found=sum(1 for b in figs if "img" in b), figbytes=figbytes,
                editable=sum(1 for b in blocks if b["k"] in ("p", "li", "cap")))


def selftest() -> int:
    import tempfile
    md = ("<!-- GENERATED MIRROR of x/none.odt — do not edit. source-sha256=abc123 pandoc=3.1.3 -->\n\n"
          "# Results\n\nA paragraph with **bold** and x^2^.\n\n-   one\n-   two\n\n"
          "![**Figure :** The map. (Source: a.png).](Pictures/AAA.png){width=\"1in\"}\n\n"
          "![](Pictures/BBB.jpg)\n\n**Figure 3.** Its caption, kept apart.\n\n"
          "  ---- ----\n  a    b\n  ---- ----\n")
    b = parse(md)
    kinds = [x["k"] for x in b]
    ok = kinds == ["h", "p", "li", "li", "fig", "cap", "fig", "cap", "table"]
    ok &= b[1]["t"] == "A paragraph with bold and x²." and b[5]["t"].startswith("Figure : The map.")
    ok &= b[4]["name"] == "AAA.png" and source_odt(md) == ("x/none.odt", "abc123")
    ok &= len({x["id"] for x in b}) == len(b)
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGBA", (3200, 1600), (10, 20, 30, 255)).save(buf, "PNG")
        odt = t / "d.odt"
        with zipfile.ZipFile(odt, "w") as z:
            z.writestr("Pictures/AAA.png", buf.getvalue())
        n = extract_figures(odt, b, t / "o")
        ok &= n > 0 and b[4].get("img") == "fig/AAA.jpg" and b[4]["w"] == FIG_MAX_W and b[4]["h"] == 800
        ok &= "img" not in b[6]         # absent from the ODT: shown as missing, not an error
    old = [{"id": "old_1", "k": "p", "t": b[1]["t"]}, {"id": "old_2", "k": "p", "t": "gone"}]
    ok &= keep_ids(b, old) == 1 and b[1]["id"] == "old_1"
    # 1.2.0: a changed paragraph keeps its id and carries the current text; a removed one shows as a deletion; an
    # added one is "new"; unchanged ones are unmarked.
    cur = [{"id": "c1", "k": "p", "t": "same"}, {"id": "c2", "k": "p", "t": "old wording"},
           {"id": "c3", "k": "p", "t": "to go"}]
    dr = [{"id": "d1", "k": "p", "t": "same"}, {"id": "d2", "k": "p", "t": "new wording"},
          {"id": "d4", "k": "h", "lvl": 2, "t": "3.4 Added"}]
    m, cnt = mark_changes(dr, cur)
    ok &= [x.get("chg") or x["k"] for x in m] == ["p", "del", "changed", "new"]
    ok &= "chg" not in m[0] and cnt["deleted"] >= 1
    ch = [x for x in m if x.get("chg") == "changed"]
    ok &= not ch or (ch[0]["id"] == "c2" and ch[0]["was"] == "old wording")
    print(f"  review_page --selftest: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mirror", nargs="?", help="the document's markdown mirror")
    ap.add_argument("--title", help="page title (default: '<doc> review')")
    ap.add_argument("--json-name", help="the page's data file name (keep an existing page's, e.g. paper1.json)")
    ap.add_argument("--keep-ids", help="an earlier page's blocks json: reuse its ids for unchanged paragraphs, so "
                                       "edits already saved there stay attached")
    ap.add_argument("--compare-to", help="1.2.0: the CURRENT mirror; the page marks every block the draft changes, adds "
                                         "or removes")
    ap.add_argument("--version-label", help="1.2.0: the draft's name on the page, e.g. 'v1_116 draft'")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.mirror:
        ap.error("name a mirror, e.g. report_edits/text/report9.md")
    mirror = (REPO / a.mirror).resolve() if not pathlib.Path(a.mirror).is_absolute() else pathlib.Path(a.mirror)
    r = build(mirror, a.title, json_name=a.json_name,
              old_ids=(REPO / a.keep_ids) if a.keep_ids else None,
              compare_to=(REPO / a.compare_to) if a.compare_to else None, version_label=a.version_label)
    out = r["out"]
    files = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "index.html")
    size = sum(p.stat().st_size for p in files)
    print(f"review_page {__version__}: {r['name']} ({r['version']}): {r['blocks']} blocks, {r['editable']} editable, "
          f"{r['figs_found']} of {r['figs']} figures ({r['figbytes'] / 1e6:.1f} MB); page files {size / 1e6:.1f} MB"
          + (f"; {r['kept']} earlier id(s) kept" if a.keep_ids else "")
          + (f"; proposed: {r['changes']['changed']} changed, {r['changes']['new']} new, "
             f"{r['changes']['deleted']} deleted" if r.get("changes") else ""))
    if r["figs_found"] < r["figs"]:
        print(f"  {r['figs'] - r['figs_found']} figure(s) not found in the ODT or not readable: shown as missing")
    if size > PUBLISH_BUDGET:
        print(f"  over one publish ({PUBLISH_BUDGET / 1e6:.0f} MB): publish the figures in several calls to the same url")
    rel = out.relative_to(REPO)
    print(f"  publish: Artifact file_path={rel}/index.html, files={{'{r['jname']}': '{rel}/{r['jname']}', "
          f"'fig/…': each of {rel}/fig/*}}, capabilities {{\"db\": {{}}}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
