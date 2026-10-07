#!/usr/bin/env python3
"""
reembed_paper_figures.py — put the CURRENT pipeline figure into each paper ODT.

WHY THIS IS NOT reembed_figures.py

  tools/reembed_figures.py keeps the REPORT's pictures current. It identifies an
  embedded picture by walking the declared output's git history for a revision
  whose bytes are embedded. That works for the report because the report embeds
  the pipeline's own bytes.

  The papers do not. Paper 1 and Paper 2 embed RESAMPLED copies: long edge 1600 px
  (Paper 1) or 1700 px (Paper 2), mostly re-encoded as JPEG, whatever the output's
  own size and format. No revision of any output has those bytes, so the report
  tool's byte match never fires on a paper and every paper figure is invisible to
  it — current or stale alike.

  So here a picture is identified by its CAPTION and compared by CONTENT:

  the map      docs/papers/paper_1/PAPER1_FIGURES.md and
               docs/papers/paper_2/PAPER2_FIGURES.md (figure number -> rendered
               file under outputs/). The paper captions do not reliably name their
               source; these tables are the durable record.
  the pairing  each draw:frame/draw:image in content.xml is paired with the
               caption that belongs to it: the "Figure N" paragraph inside the same
               text-box, else the paragraph that holds the frame when its own text
               begins "Figure N", else the first "Figure N" paragraph after it
               (stopping at a heading). "Figure N (continued)" belongs to N.
  the score    both pictures are flattened onto white, reduced to greyscale at
               SCORE_WIDTH px wide (the embedded picture's aspect), blurred by one
               pixel, aligned by the best whole-pixel shift within SCORE_SHIFT, and
               differenced. The score is the WORST BLOCK: the largest mean absolute
               difference (0-255) over a grid of SCORE_BLOCKS blocks across. A
               resample, a JPEG recompression or a one-pixel misregistration spreads
               a little difference over every edge; a re-rendered figure (a changed
               label, an added line, a moved contour) puts a lot of difference in
               one place. A whole-picture mean cannot tell those apart — it averages
               a changed number in a title into nothing (measured: see
               STALE_THRESHOLD).

  A figure whose map row names two or more files is a COMPOSITE. It is paired
  part-for-part, in document order, only when the paper embeds exactly as many
  images and that order is also the best-scoring assignment; otherwise it is
  reported and left alone. A row marked "DO NOT USE" is reported as excluded.

WRITING

  --apply replaces each STALE picture: the current output is resampled (PIL,
  LANCZOS) to the embedded picture's pixel WIDTH (never past the output's own
  width), keeping the output's aspect, and encoded in the embedded member's own
  format: a .png member gets PNG, a .jpg member gets JPEG quality 90. The member
  name, the manifest media-type and draw:mime-type are not rewritten, so the bytes
  must match them (most paper members are .jpg even where the output is a PNG,
  so "the output's own type" would put PNG bytes under a JPEG name). Where the new
  aspect differs from the frame's by more than ASPECT_TOL the frame's svg:height
  is recomputed from its kept svg:width, in whatever unit the frame uses (cm, in,
  mm, pt), exactly as reembed_figures 1.2.0 does.

  Every write goes through tools/odt_edit.py: edit() for the svg:height, then
  replace_image() once per picture. The chain is written into a temporary
  directory and only the final file is copied out, to the NEXT version filename
  beside the source (Paper1_v1_66.odt -> Paper1_v1_67.odt). A versioned document
  is never edited in place, and an existing next version is never overwritten.

Usage:
    python3 tools/reembed_paper_figures.py                      # dry run, both papers
    python3 tools/reembed_paper_figures.py --only paper1
    python3 tools/reembed_paper_figures.py --apply --only paper2
    python3 tools/reembed_paper_figures.py --only paper1 --odt /path/to/Paper1_v1_66.odt
"""
from __future__ import annotations

__version__ = "1.0.0"  # 2026-10-07 (Claude). First issue. Extends reembed_figures to the
#   papers, as Martin approved: the PAPER1_FIGURES.md and PAPER2_FIGURES.md tables are the map, pictures are paired
#   by caption and compared by content, and a stale one is resampled to the paper's own
#   embedded width (1600/1700 px). Needs odt_edit >= 1.9.0 (replace_image accepts JPEG).

import argparse
import io
import re
import shutil
import sys
import tempfile
import zipfile
from itertools import permutations
from pathlib import Path
from xml.dom import minidom

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import odt_edit                                                  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUTPUTS = REPO / "outputs"

PAPERS = {
    "paper1": (REPO / "docs/papers/paper_1", "Paper1", "PAPER1_FIGURES.md"),
    "paper2": (REPO / "docs/papers/paper_2", "Hollingham_2026_Paper2_amended",
               "PAPER2_FIGURES.md"),
}

SCORE_WIDTH = 400
SCORE_BLOCKS = 25          # blocks across, so 16 px blocks at SCORE_WIDTH
SCORE_SHIFT = 2            # px at SCORE_WIDTH searched for the best global alignment
# Worst-block score above which the embedded picture is a DIFFERENT picture from the
# current output. Calibrated 2026-10-07 on Paper1_v1_66 and Paper2_amended_v32, every
# borderline pair checked by eye side by side:
#   same picture      0.4 (P1 Fig 16, swapped in at v1_61)
#                     7.4 (P1 Fig 3: identical content, rendered at a 0.1 % different
#                          aspect, so every edge is misregistered by about a pixel)
#   real changes      11.8 (P1 Fig 11: one contour segment and its label moved)
#                     18.3 (P2 Fig 3: clearfell step 120 -> 108 mm, CUSUM final)
#                     22.9 (P1 Fig 6: detrending mean 19.46 -> 19.51, one axis label)
#                     23.0 (P1 Fig 19: lambda 228 -> 220 m), then 24.9 upward.
# The line goes in the gap and toward its low side, because the two errors are not
# equal: a false STALE re-embeds a fresh resample of the same current output (harmless),
# a false "current" leaves a stale figure in a paper. The whole-picture mean, tried
# first, could not do this: it scored P1 Fig 11 (changed) 0.8 and P1 Fig 3 (unchanged)
# 1.7, and put four changed figures (2.0-2.6) below the unchanged one's neighbourhood.
STALE_THRESHOLD = 9.0
ASPECT_TOL = 0.005
JPEG_QUALITY = 90


# ----------------------------------------------------------------------------- files

def version_key(path: Path, stem: str) -> tuple[int, ...] | None:
    m = re.fullmatch(re.escape(stem) + r"_v(\d+(?:_\d+)*)\.odt", path.name)
    return tuple(int(x) for x in m.group(1).split("_")) if m else None


def newest_version(folder: Path, stem: str) -> Path | None:
    """Highest version by NUMERIC comparison of the version field (v1_9_99 < v1_9_122)."""
    found = [(version_key(p, stem), p) for p in folder.glob(f"{stem}_v*.odt")]
    found = [(k, p) for k, p in found if k is not None]
    return max(found)[1] if found else None


def next_version(path: Path) -> Path:
    m = re.fullmatch(r"(.*_v)(\d+(?:_\d+)*)", path.stem)
    if not m:
        raise SystemExit(f"  cannot read a version field from {path.name}")
    parts = m.group(2).split("_")
    parts[-1] = str(int(parts[-1]) + 1)
    return path.with_name(m.group(1) + "_".join(parts) + path.suffix)


def resolve_output(name: str) -> tuple[Path | None, str]:
    """A map entry -> the file under outputs/. A path is tried as given, then the
    basename is searched for; more than one hit is ambiguous and not guessed."""
    direct = OUTPUTS / name
    if direct.is_file():
        return direct, ""
    hits = sorted(p for p in OUTPUTS.rglob(Path(name).name) if p.is_file())
    if len(hits) == 1:
        return hits[0], ""
    if not hits:
        return None, "not found under outputs/"
    return None, f"ambiguous: {len(hits)} files named {Path(name).name}"


# ----------------------------------------------------------------------------- the map

IMG_RE = re.compile(r"[\w./-]+\.(?:png|jpe?g)", re.I)


def parse_map(md: Path) -> dict[int, dict]:
    """{figure: {"files": [...], "excluded": bool}} from the paper's figure-source table (PAPER1_FIGURES.md or PAPER2_FIGURES.md).
    The rendered-file column is found by its header ('Rendered file' in Paper 1,
    'Source pipeline file' in Paper 2), never by position."""
    out: dict[int, dict] = {}
    col = None
    for line in md.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if col is None:
            for i, c in enumerate(cells):
                if re.search(r"rendered file|source pipeline file", c, re.I):
                    col = i
            continue
        if not cells or not cells[0].isdigit() or col >= len(cells):
            continue
        cell = cells[col]
        quoted = re.findall(r"`([^`]+)`", cell)
        files = [f for f in (quoted or IMG_RE.findall(cell)) if IMG_RE.fullmatch(f)]
        out[int(cells[0])] = {"files": files, "excluded": "DO NOT USE" in cell.upper()}
    if col is None:
        raise SystemExit(f"  {md.name}: no 'Rendered file' / 'Source pipeline file' column")
    return out


# ----------------------------------------------------------------------------- pairing

FRAME_RE = re.compile(r'<draw:frame\b([^>]*)>\s*<draw:image\b[^>]*?xlink:href="(Pictures/[^"]+)"',
                      re.S)
CAPTION_RE = re.compile(r"Figure\s*(\d+)")


def _plain(fragment: str) -> str:
    fragment = re.sub(r"<draw:frame\b.*?</draw:frame>", "", fragment, flags=re.S)
    return re.sub(r"<[^>]+>", "", fragment).strip()


def _caption_number(text: str) -> int | None:
    m = CAPTION_RE.match(text)
    return int(m.group(1)) if m else None


def pair_images(xml: str) -> list[dict]:
    """[{member, frame_attrs, pos, fig}] in document order; fig None when unpaired."""
    rows = []
    for m in FRAME_RE.finditer(xml):
        pos, fig = m.start(), None
        # 1. inside a text-box: the caption in the same box
        tb_open = xml.rfind("<draw:text-box", 0, pos)
        if tb_open != -1 and xml.rfind("</draw:text-box>", tb_open, pos) == -1:
            tb_close = xml.find("</draw:text-box>", pos)
            for p in re.finditer(r"<text:p\b[^>]*>(.*?)</text:p>", xml[tb_open:tb_close], re.S):
                fig = _caption_number(_plain(p.group(1)))
                if fig is not None:
                    break
        # 2. the paragraph holding the frame, when its own text is the caption
        p_open = max(xml.rfind("<text:p ", 0, pos), xml.rfind("<text:p>", 0, pos))
        p_close = xml.find("</text:p>", pos)
        if fig is None and p_open != -1 and p_close != -1:
            fig = _caption_number(_plain(xml[xml.find(">", p_open) + 1:p_close]))
        # 3. the first caption paragraph after it, stopping at a heading
        if fig is None and p_close != -1:
            for blk in re.finditer(r"<text:(p|h)\b[^>]*>(.*?)</text:\1>",
                                   xml[p_close:p_close + 60000], re.S):
                if blk.group(1) == "h":
                    break
                fig = _caption_number(_plain(blk.group(2)))
                if fig is not None:
                    break
        rows.append({"member": m.group(2), "frame_attrs": m.group(1), "pos": pos,
                     "fig": fig})
    return rows


# ----------------------------------------------------------------------------- content

def _flatten(im: Image.Image) -> Image.Image:
    im.load()
    if im.mode in ("RGBA", "LA", "P", "PA"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")


def grey(im: Image.Image) -> Image.Image:
    return _flatten(im).convert("L")


def score(embedded: Image.Image, source: Image.Image) -> float:
    """Worst-block mean absolute difference, 0-255, of two greyscale pictures."""
    w = SCORE_WIDTH
    h = max(SCORE_BLOCKS, round(w * embedded.size[1] / embedded.size[0]))

    def prep(im):
        im = im.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1))
        return np.asarray(im, dtype=float)

    a, b, r = prep(embedded), prep(source), SCORE_SHIFT
    core = a[r:h - r, r:w - r]
    best = None
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = np.abs(core - b[r + dy:h - r + dy, r + dx:w - r + dx])
            if best is None or d.mean() < best.mean():
                best = d
    blk = w // SCORE_BLOCKS
    hb, wb = best.shape[0] // blk, best.shape[1] // blk
    return float(best[:hb * blk, :wb * blk].reshape(hb, blk, wb, blk).mean(axis=(1, 3)).max())


# ----------------------------------------------------------------------------- planning

def plan(odt: Path, fmap: dict[int, dict]) -> list[dict]:
    z = zipfile.ZipFile(odt)
    xml = z.read("content.xml").decode("utf-8")
    images = pair_images(xml)
    for im in images:
        data = z.read(im["member"])
        im["data"] = data
        with Image.open(io.BytesIO(data)) as pic:
            im["size"] = pic.size
            im["grey"] = grey(pic)
    z.close()

    by_fig: dict[int, list[dict]] = {}
    for im in images:
        if im["fig"] is None:
            im.update(verdict="unpaired", source=None, score=None,
                      note="no 'Figure N' caption found for this frame")
        else:
            by_fig.setdefault(im["fig"], []).append(im)

    src_grey: dict[Path, Image.Image] = {}

    def source_grey(p: Path) -> Image.Image:
        if p not in src_grey:
            with Image.open(p) as pic:
                src_grey[p] = grey(pic)
        return src_grey[p]

    for fig, ims in by_fig.items():
        row = fmap.get(fig)
        if row is None or not row["files"]:
            for im in ims:
                im.update(verdict="unmapped", source=None, score=None,
                          note="figure has no rendered file in the map")
            continue
        resolved = [resolve_output(f) for f in row["files"]]
        missing = [f"{f}: {why}" for f, (p, why) in zip(row["files"], resolved) if p is None]
        if row["excluded"]:
            for im in ims:
                im.update(verdict="excluded", source=None, score=None,
                          note="map row is marked DO NOT USE")
            continue
        if missing:
            for im in ims:
                im.update(verdict="unmapped", source=None, score=None, note="; ".join(missing))
            continue
        paths = [p for p, _ in resolved]
        if len(paths) == 1 and len(ims) == 1:
            im = ims[0]
            s = score(im["grey"], source_grey(paths[0]))
            im.update(source=paths[0], score=s, note="",
                      verdict="current" if s <= STALE_THRESHOLD else "STALE")
            continue
        # composite: map names several files, or the paper embeds several images
        scores = [[score(im["grey"], source_grey(p)) for p in paths] for im in ims]
        if len(paths) == len(ims) and len(paths) > 1:
            n = len(paths)
            best = min(permutations(range(n)),
                       key=lambda perm: sum(scores[i][perm[i]] for i in range(n)))
            if best == tuple(range(n)):
                for i, im in enumerate(ims):
                    s = scores[i][i]
                    im.update(source=paths[i], score=s,
                              note=f"composite part {chr(97 + i)} of {n}, paired in order",
                              verdict="current" if s <= STALE_THRESHOLD else "STALE")
                continue
            why = "document order is not the best-scoring assignment"
        else:
            why = f"{len(ims)} embedded image(s) against {len(paths)} mapped file(s)"
        for i, im in enumerate(ims):
            j = min(range(len(paths)), key=lambda k: scores[i][k])
            im.update(verdict="composite", source=paths[j], score=scores[i][j],
                      note=f"not paired ({why}); nearest file shown")
    return images


# ----------------------------------------------------------------------------- writing

def _frame_size(attrs: str):
    wm = re.search(r'svg:width="([\d.]+)(cm|in|mm|pt)"', attrs)
    hm = re.search(r'svg:height="([\d.]+)(cm|in|mm|pt)"', attrs)
    if not (wm and hm and wm.group(2) == hm.group(2)):
        return None
    return float(wm.group(1)), hm.group(1), wm.group(2)


def resample(src: Path, width: int, member: str, out: Path) -> tuple[int, int]:
    with Image.open(src) as pic:
        pic.load()
        sw, sh = pic.size
        width = min(width, sw)                     # never upscale
        h = max(1, round(width * sh / sw))
        if member.lower().endswith((".jpg", ".jpeg")):
            img = _flatten(pic).resize((width, h), Image.LANCZOS)
            img.save(out, "JPEG", quality=JPEG_QUALITY)
        else:
            img = pic if pic.mode in ("RGB", "RGBA", "L", "LA") else pic.convert("RGBA")
            img.resize((width, h), Image.LANCZOS).save(out, "PNG")
    return width, h


def apply(odt: Path, jobs: list[dict], work: Path) -> Path | None:
    dst = next_version(odt)
    if dst.exists():
        print(f"  REFUSED: {dst.name} already exists - not overwriting a version")
        return None
    step = 0

    def next_step() -> Path:
        nonlocal step
        step += 1
        d = work / f"step{step:02d}"
        d.mkdir()
        return d / dst.name           # keeps the family name, so odt_edit's tier gate applies

    current = odt
    xml = zipfile.ZipFile(odt).read("content.xml").decode("utf-8")

    # 1. the new pictures, and the frame heights their aspects need
    subs = []
    for j in jobs:
        png = work / (Path(j["member"]).stem + Path(j["member"]).suffix)
        nw, nh = resample(j["source"], j["size"][0], j["member"], png)
        j["new_file"], j["new_size"] = png, (nw, nh)
        fs = _frame_size(j["frame_attrs"])
        if fs is None:
            print(f"  REFUSED Figure {j['fig']}: the frame's size could not be read")
            return None
        w, h_txt, unit = fs
        if abs((nw / nh) - (w / float(h_txt))) / (w / float(h_txt)) > ASPECT_TOL:
            m = re.search(r'<draw:frame\b[^>]*>\s*<draw:image\b[^>]*?xlink:href="'
                          + re.escape(j["member"]) + '"', xml, re.S)
            old = m.group(0)
            new_h = round(w * nh / nw, 4)
            new = old.replace(f'svg:height="{h_txt}{unit}"', f'svg:height="{new_h}{unit}"', 1)
            subs.append((old, new, 1))
            print(f"      Figure {j['fig']}: frame height {h_txt}{unit} -> {new_h}{unit} "
                  f"(aspect {w / float(h_txt):.4f} -> {nw / nh:.4f})")
    if subs:
        out = next_step()
        if not odt_edit.edit(current, out, subs, expect=len(subs), allow_tag_change=True):
            return None
        current = out

    # 2. one replace_image per picture
    for i, j in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] Figure {j['fig']}: {j['member']} <- {j['source'].name}")
        out = next_step()
        if not odt_edit.replace_image(current, out, j["member"], j["new_file"]):
            return None
        current = out

    shutil.copyfile(current, dst)
    return dst


def verify(new: Path, old: Path, jobs: list[dict]) -> bool:
    """Opens, parses, the replaced pictures now score current, nothing else changed."""
    ok = True
    with zipfile.ZipFile(new) as zn, zipfile.ZipFile(old) as zo:
        bad = zn.testzip()
        print(f"  verify: testzip {'OK' if bad is None else 'FAILED at ' + bad}")
        ok &= bad is None
        try:
            minidom.parseString(zn.read("content.xml"))
            print("  verify: content.xml parses")
        except Exception as e:                       # noqa: BLE001
            print(f"  verify: content.xml does NOT parse: {e}")
            ok = False
        replaced = {j["member"] for j in jobs}
        others = [n for n in zo.namelist() if n.startswith("Pictures/") and n not in replaced]
        changed = [n for n in others if zn.read(n) != zo.read(n)]
        print(f"  verify: {len(others) - len(changed)}/{len(others)} other pictures byte-identical")
        ok &= not changed
        for j in jobs:
            with Image.open(io.BytesIO(zn.read(j["member"]))) as pic:
                with Image.open(j["source"]) as src:
                    s = score(grey(pic), grey(src))
                size = pic.size
            flag = "current" if s <= STALE_THRESHOLD else "STILL STALE"
            print(f"  verify: Figure {j['fig']:<3} {size[0]}x{size[1]}  score {s:5.2f}  {flag}")
            ok &= s <= STALE_THRESHOLD
    return ok


# ----------------------------------------------------------------------------- main

def report(odt: Path, images: list[dict]) -> None:
    print(f"\n  {odt.name}   (stale above {STALE_THRESHOLD:.1f} of 255)")
    print(f"  {'Fig':>4}  {'embedded':>10}  {'source':<44} {'score':>6}  verdict")
    order = sorted(images, key=lambda r: (r["fig"] is None, r["fig"] or 0, r["pos"]))
    for n, r in enumerate(order, 1):
        fig = str(r["fig"]) if r["fig"] is not None else "-"
        size = f"{r['size'][0]}x{r['size'][1]}"
        src = r["source"].name if r.get("source") else "-"
        sc = f"{r['score']:6.2f}" if r.get("score") is not None else "     -"
        note = f"   ({r['note']})" if r.get("note") else ""
        print(f"  {fig:>4}  {size:>10}  {src:<44} {sc}  {r['verdict']}{note}"
              f"   [{n}/{len(order)}]")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="list only (the default)")
    mode.add_argument("--apply", action="store_true", help="replace STALE pictures")
    ap.add_argument("--only", choices=sorted(PAPERS))
    ap.add_argument("--odt", type=Path, help="use this ODT instead of the newest version "
                    "(testing); needs --only")
    args = ap.parse_args()
    if args.odt and not args.only:
        ap.error("--odt needs --only paper1|paper2")

    failed = False
    for key, (folder, stem, mapname) in PAPERS.items():
        if args.only and key != args.only:
            continue
        odt = args.odt.resolve() if args.odt else newest_version(folder, stem)
        if odt is None or not odt.is_file():
            print(f"\n  {key}: no {stem}_v*.odt in {folder.relative_to(REPO)}")
            failed = True
            continue
        print(f"\n  {key}: reading {odt.name} against {mapname} ...")
        fmap = parse_map(folder / mapname)
        images = plan(odt, fmap)
        report(odt, images)
        absent = sorted(set(fmap) - {r["fig"] for r in images})
        if absent:
            print("  in the map but not embedded: " + ", ".join(f"Figure {n}" for n in absent))
        counts: dict[str, int] = {}
        for r in images:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        print("  " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
        jobs = [r for r in images if r["verdict"] == "STALE"]
        if not args.apply:
            continue
        if not jobs:
            print("  nothing stale - no new version written")
            continue
        work = Path(tempfile.mkdtemp(prefix="reembed_paper_"))
        try:
            new = apply(odt, jobs, work)
        finally:
            shutil.rmtree(work, ignore_errors=True)      # one full archive per step
        if new is None:
            failed = True
            continue
        print(f"\n  wrote {new}  ({len(jobs)} picture(s) replaced; {odt.name} untouched)")
        failed |= not verify(new, odt, jobs)
    if not args.apply:
        print("\n  dry run - nothing written")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
