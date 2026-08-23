#!/usr/bin/env python3
"""
reembed_figures.py — put the CURRENT pipeline figure into the document.

THE PROBLEM

  A figure in the report is a copy. The pipeline writes
  `outputs/25_coastal_gradient/25_05_fit_diagnostic.jpg`; the document carries
  its own copy inside `Pictures/`. Re-running the pipeline updates the first and
  not the second, and nothing notices — the caption still numbers itself, the
  reference still resolves, the lint chain stays green, and the picture on the
  page is whatever it was when someone last dragged it in.

  Measured on 2026-08-23: 25 embedded figures differed from the output they
  declare, one of them by seven commits — the fit diagnostic whose panel (b) was
  redrawn that afternoon after Martin asked what the bar straddling zero meant.
  The report was describing the corrected figure and displaying the broken one.

HOW AN ENTRY IS IDENTIFIED — BY CONTENT, NOT POSITION

  `Pictures/10000001000010E400000C9FC2572737.png` says nothing about which
  figure it is. Pairing images to captions by document order would work until
  the first inline logo or the first figure whose frame sits after its caption.

  So the match is made through git instead. For a declared source that no longer
  matches anything embedded, we walk that file's history and look for the
  revision whose bytes ARE embedded. That revision identifies the entry exactly,
  and as a by-product says how far behind the document had fallen. A source
  whose history contains no embedded version is NOT replaced — it means the
  declaration points somewhere else, and guessing would put the wrong picture
  under a caption.

ASPECT RATIO

  The frame carries svg:width and svg:height in centimetres. Replacing the bytes
  under a frame whose proportions no longer fit stretches the image, which is
  worse than a stale figure because it looks deliberate. Where the new image's
  aspect differs by more than half a percent, the height is recomputed from the
  kept width.

Usage:
    python3 tools/reembed_figures.py --dry-run
    python3 tools/reembed_figures.py --apply
    python3 tools/reembed_figures.py --apply --only report9
    python3 tools/reembed_figures.py --dry-run --skip 20_driver_change_2005_2025_20yr.png
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) — 2026-08-23.

import argparse
import csv
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repoint_refs import ODTS                                    # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / "tools/figure_table_sources.csv"
FIGMAP = REPO / "tools/figure_map.csv"
HISTORY_DEPTH = 25


def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                          env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin",
                               "HOME": "/tmp"})


def blob_id(data: bytes) -> str:
    """git's object id for these bytes, so embedded images can be compared
    against history without checking anything out."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def dimensions(data: bytes) -> tuple[int, int] | None:
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(data)) as im:
            return im.size
    except Exception:
        return None


def outputs_index() -> dict[str, Path]:
    idx: dict[str, Path] = {}
    for p in (REPO / "outputs").rglob("*"):
        if p.suffix.lower() in (".png", ".jpg", ".jpeg") and p.is_file():
            idx.setdefault(p.name, p)
    return idx


def global_numbers() -> dict[tuple[str, str], str]:
    out = {}
    for r in csv.DictReader(FIGMAP.open(encoding="utf-8")):
        m = re.match(r"\s*Figure\s+([\d.]+)\s*:", r["caption"])
        if m:
            out[(r["document"], m.group(1))] = r["number"]
    return out


def history_ids(path: Path) -> list[tuple[str, str]]:
    """[(blob id, short rev)] newest first, for one tracked file."""
    rel = str(path.relative_to(REPO))
    revs = git("log", f"-{HISTORY_DEPTH}", "--format=%H", "--", rel
               ).stdout.decode().split()
    if not revs:
        return []
    spec = "\n".join(f"{r}:{rel}" for r in revs).encode()
    out = subprocess.run(["git", "cat-file", "--batch-check"], cwd=REPO,
                         input=spec, capture_output=True,
                         env={"GIT_OPTIONAL_LOCKS": "0", "PATH": "/usr/bin:/bin",
                              "HOME": "/tmp"}).stdout.decode().splitlines()
    pairs = []
    for rev, line in zip(revs, out):
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "blob":
            pairs.append((parts[0], rev[:7]))
    return pairs


def plan_for(odt: Path, srcidx, gnum, skip) -> tuple[list, list]:
    z = zipfile.ZipFile(odt)
    embedded = {}
    for i in z.infolist():
        if i.filename.startswith("Pictures/"):
            data = z.read(i.filename)
            embedded[blob_id(data)] = (i.filename, data)

    jobs, problems = [], []
    for r in csv.DictReader(SOURCES.open(encoding="utf-8")):
        if r["document"] != odt.name or r["type"] != "Figure":
            continue
        base = r["source"].split("/")[-1].replace("Script 26c output ", "").strip()
        if base in skip:
            continue
        cur = srcidx.get(base)
        if cur is None:
            continue
        new = cur.read_bytes()
        if blob_id(new) in embedded:
            continue                                   # already current
        hit = None
        for i, (bid, rev) in enumerate(history_ids(cur)):
            if bid in embedded:
                hit = (i, rev, *embedded[bid])
                break
        num = gnum.get((odt.name, r["number"]), "?")
        if hit is None:
            problems.append((num, base,
                             "no version in this file's history is embedded — "
                             "the declaration probably names the wrong output"))
            continue
        behind, rev, entry, old = hit
        od, nd = dimensions(old), dimensions(new)
        jobs.append({"fig": num, "src": base, "entry": entry, "new": new,
                     "behind": behind, "rev": rev, "old_dim": od, "new_dim": nd})
    return jobs, problems


ASPECT_TOL = 0.005


def rewrite(odt: Path, jobs: list) -> None:
    zin = zipfile.ZipFile(odt)
    xml = zin.read("content.xml").decode("utf-8")
    resized = []
    for j in jobs:
        od, nd = j["old_dim"], j["new_dim"]
        if not od or not nd:
            continue
        if abs((nd[0] / nd[1]) - (od[0] / od[1])) / (od[0] / od[1]) <= ASPECT_TOL:
            continue
        # the frame that carries this entry, and its stated box
        pat = re.compile(
            r'(<draw:frame\b[^>]*?svg:width="([\d.]+)cm"[^>]*?svg:height="([\d.]+)cm"'
            r'[^>]*>(?:(?!</draw:frame>).)*?xlink:href="' + re.escape(j["entry"]) + r'")',
            re.S)
        m = pat.search(xml)
        if not m:
            continue
        w = float(m.group(2))
        new_h = round(w * nd[1] / nd[0], 3)
        seg = m.group(1).replace(f'svg:height="{m.group(3)}cm"',
                                 f'svg:height="{new_h}cm"', 1)
        xml = xml[:m.start(1)] + seg + xml[m.end(1):]
        resized.append((j["fig"], m.group(3), f"{new_h}"))
    for f, o, n in resized:
        print(f"      frame resized for Figure {f}: {o}cm -> {n}cm tall "
              f"(aspect changed)")

    replace = {j["entry"]: j["new"] for j in jobs}
    tmp = Path(tempfile.mkdtemp()) / odt.name
    with zipfile.ZipFile(tmp, "w") as zout:
        if "mimetype" in zin.namelist():
            zout.writestr(zipfile.ZipInfo("mimetype"), zin.read("mimetype"),
                          compress_type=zipfile.ZIP_STORED)
        for info in zin.infolist():
            if info.filename == "mimetype":
                continue
            if info.filename == "content.xml":
                data = xml.encode("utf-8")
            else:
                data = replace.get(info.filename) or zin.read(info.filename)
            ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            # Preserve each entry's ORIGINAL compression. Storing the images
            # uncompressed instead would be five times faster and cost about 1%
            # in size, since PNG and JPEG are already compressed — but this tool
            # is here to change 24 pictures, not the storage of all 73, and a
            # document should come out of an edit looking like it went in.
            ni.compress_type = info.compress_type
            zout.writestr(ni, data)
    with zipfile.ZipFile(tmp) as zo:
        assert zo.namelist()[0] == "mimetype"
        assert zo.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert len(zo.namelist()) == len(zin.namelist())
    shutil.copyfile(tmp, odt)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--skip", nargs="*", default=[],
                    help="source filenames to leave alone")
    args = ap.parse_args()
    if not (args.apply or args.dry_run):
        ap.error("choose --dry-run or --apply")

    srcidx, gnum, skip = outputs_index(), global_numbers(), set(args.skip)
    total = 0
    for name, rel in ODTS.items():
        if args.only and args.only.lower() not in name.lower():
            continue
        odt = REPO / rel
        if odt.suffix not in (".odt", ".odm") or not odt.exists():
            continue
        jobs, problems = plan_for(odt, srcidx, gnum, skip)
        if not jobs and not problems:
            continue
        print(f"\n  {odt.name}")
        for j in sorted(jobs, key=lambda d: int(d["fig"]) if str(d["fig"]).isdigit() else 999):
            dim = ""
            if j["old_dim"] and j["new_dim"] and j["old_dim"] != j["new_dim"]:
                dim = f"   {j['old_dim'][0]}x{j['old_dim'][1]} -> {j['new_dim'][0]}x{j['new_dim'][1]}"
            print(f"      Figure {str(j['fig']):<4} {j['src']:<44} "
                  f"{j['behind']} rev(s) behind ({j['rev']}){dim}")
        for num, base, why in problems:
            print(f"      SKIPPED Figure {num:<4} {base:<44} {why}")
        total += len(jobs)
        if args.apply and jobs:
            rewrite(odt, jobs)
            print(f"      wrote {odt.name} ({len(jobs)} figure(s) replaced)")

    print(f"\n  {total} figure(s) "
          + ("replaced" if args.apply else "would be replaced — dry run"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
