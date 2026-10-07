#!/usr/bin/env python3
"""
publish_water_watch.py — put a Water Watch issue on the public project site.

Copies the month's newsletter PDF into water_watch/ (served by GitHub Pages at
https://newbroman.github.io/Newborough_Hydrology/water_watch/) as
Newborough_Water_Watch_YYYY_MM.pdf, recompressing large map images to JPEG so an
issue stays near 1-2 MB in the public repository, and rebuilds water_watch/index.html
from the issues present (newest first).

Usage:
    python3 living/publish_water_watch.py 2026-09                 # PDF from living/output/2026/September/
    python3 living/publish_water_watch.py 2026-09 --pdf path.pdf  # an edited/exported PDF instead
    python3 living/publish_water_watch.py --index-only            # rebuild the index page only

Publish the issue you sent out: if you edited the ODT before sending, export that
ODT to PDF and pass it with --pdf. The site updates when the repository is pushed.

__version__ = "1.0.0"  # Hollingham (2026) - 2026-10-08. New (Martin: "the newsletters for
#   water watch arent public can we change that?"; chose the GitHub site).
"""
__version__ = "1.0.0"

import argparse
import calendar
import html
import io
import os
import re
import shutil
import sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "water_watch")
NAME_RE = re.compile(r"^Newborough_Water_Watch_(\d{4})_(\d{2})\.pdf$")


def _shrink(src, dst, min_width=600, quality=82):
    """Re-encode large images as JPEG where that is smaller. Falls back to a copy."""
    try:
        import pikepdf
        from PIL import Image  # noqa: F401  (pikepdf.PdfImage.as_pil_image needs Pillow)
    except ImportError:
        shutil.copyfile(src, dst)
        return False
    pdf = pikepdf.open(src)
    for page in pdf.pages:
        for _, raw in list(page.images.items()):
            try:
                pil = pikepdf.PdfImage(raw).as_pil_image()
            except Exception:
                continue
            if pil.width < min_width:
                continue
            if pil.mode not in ("RGB", "L"):
                pil = pil.convert("RGB")
            buf = io.BytesIO()
            pil.save(buf, "JPEG", quality=quality, optimize=True)
            if len(buf.getvalue()) < len(raw.read_raw_bytes()):
                raw.write(buf.getvalue(), filter=pikepdf.Name.DCTDecode)
                raw.ColorSpace = pikepdf.Name.DeviceRGB if pil.mode == "RGB" else pikepdf.Name.DeviceGray
                raw.BitsPerComponent = 8
                for k in ("/DecodeParms", "/SMask"):
                    if k in raw:
                        del raw[k]
    pdf.save(dst, compress_streams=True)
    if os.path.getsize(dst) >= os.path.getsize(src):
        shutil.copyfile(src, dst)
    return True


def _default_pdf(year, month):
    folder = os.path.join(REPO, "living", "output", str(year), calendar.month_name[month])
    return os.path.join(folder, f"Newborough_Water_Watch_{year}_{month:02d}.pdf")


def build_index():
    issues = []
    for f in os.listdir(OUT_DIR) if os.path.isdir(OUT_DIR) else []:
        m = NAME_RE.match(f)
        if m:
            y, mo = int(m.group(1)), int(m.group(2))
            issues.append((y, mo, f, os.path.getsize(os.path.join(OUT_DIR, f))))
    issues.sort(reverse=True)
    rows = []
    for i, (y, mo, f, size) in enumerate(issues):
        label = f"{calendar.month_name[mo]} {y}"
        tag = '<span class="latest">Latest</span>' if i == 0 else ""
        rows.append(f'<li><a href="{html.escape(f)}">{label}</a>{tag}'
                    f'<span class="size">PDF, {size / 1e6:.1f} MB</span></li>')
    page = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Newborough Warren Water Watch</title>
<style>
:root{{--bg:#f4f6f7;--card:#ffffff;--ink:#1d2b33;--muted:#5b6b73;--accent:#1a5276;--rule:#d8dfe2}}
@media (prefers-color-scheme: dark){{:root{{--bg:#121a1e;--card:#1a2429;--ink:#e3e9ec;--muted:#9fb0b8;--accent:#7fb3d5;--rule:#2a363c;color-scheme:dark}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "Helvetica Neue",Arial,sans-serif;padding:32px 16px 56px}}
main{{max-width:680px;margin:0 auto;display:grid;gap:20px}}
.eyebrow{{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}}
h1{{margin:0;color:var(--accent);font:600 clamp(26px,5vw,34px)/1.2 Georgia,"Times New Roman",serif}}
p{{margin:0;max-width:62ch}}
ul{{list-style:none;margin:0;padding:0;background:var(--card);border:1px solid var(--rule);border-radius:6px}}
li{{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;padding:12px 16px;border-top:1px solid var(--rule)}}
li:first-child{{border-top:0}}
a{{color:var(--accent);font-weight:600}}
.latest{{font-size:12px;color:var(--card);background:var(--accent);border-radius:3px;padding:1px 6px}}
.size{{margin-left:auto;font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}}
footer{{font-size:14px;color:var(--muted)}}
</style>
</head>
<body>
<main>
<div class="eyebrow">Newborough Warren · Anglesey</div>
<h1>Weather &amp; Water Watch</h1>
<p>A monthly newsletter on the dune water table at Newborough Warren: the month's rainfall
at RAF Valley and a local gauge, and how the water level changed at the monitoring dipwells,
with maps of the change since last month and since this time last year.</p>
<ul>
{chr(10).join(rows) if rows else '<li>No issues published yet.</li>'}
</ul>
<footer>Readings are taken at the end of each month or the first days of the next and count as that
month's level. <a href="../index.html">Newborough Warren groundwater study</a>. Page updated {date.today():%d %B %Y}.</footer>
</main>
</body>
</html>
"""
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("month", nargs="?", help="YYYY-MM")
    ap.add_argument("--pdf", help="the PDF to publish (default: the run_report.sh output for the month)")
    ap.add_argument("--index-only", action="store_true")
    a = ap.parse_args()
    if not a.index_only:
        if not a.month or not re.fullmatch(r"\d{4}-\d{2}", a.month):
            ap.error("give the month as YYYY-MM")
        y, mo = map(int, a.month.split("-"))
        src = a.pdf or _default_pdf(y, mo)
        if not os.path.isfile(src):
            sys.exit(f"  no PDF at {src} - pass the file with --pdf")
        os.makedirs(OUT_DIR, exist_ok=True)
        dst = os.path.join(OUT_DIR, f"Newborough_Water_Watch_{y}_{mo:02d}.pdf")
        _shrink(src, dst)
        print(f"  published {os.path.relpath(dst, REPO)} ({os.path.getsize(dst) / 1e6:.1f} MB, "
              f"from {os.path.getsize(src) / 1e6:.1f} MB)")
    issues = build_index()
    print(f"  water_watch/index.html lists {len(issues)} issue(s)")
    print("  public once pushed: https://newbroman.github.io/Newborough_Hydrology/water_watch/")


if __name__ == "__main__":
    main()
