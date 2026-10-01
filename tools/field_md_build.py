#!/usr/bin/env python3
"""
field_md_build.py — build a NEW document from markdown whose pipeline numbers are fields from birth (D-219).

A document written fresh (Paper M, 2026-10-01) need not pass through typed numbers and a later
field_convert: its draft names each number by its committed source and key, and this tool sets it.

Token syntax in the markdown (one per quoted number):

    ⟪ALIAS|KEY|SPEC⟫

  ALIAS  a short name for the source file (ALIASES below), or a repo-relative path.
  KEY    the label cite_check.collect_values() gives the value (field_sync.values()).
  SPEC   space-separated rendering: dpN (decimals, required), xS (scale, e.g. x100), abs, plus, th
         (thousands separator), hy (hyphen-minus instead of U+2212).

The tool renders every token from the committed value, converts the markdown with pandoc (a freshly
generated reference document, never the project's own), turns each rendered number into an ODF
user field (declaration + use, as field_sync expects), and adds the fields to tools/number_fields.csv.
A field already registered by another document is reused when its source, key and rendering agree
— that is the point: the report and the paper quote the same quantity through the same field.

It refuses to write when any token names a value that is not committed, when a field name is
registered with a different spec, or when the output exists (versioned documents are never
overwritten — bump the version).

Usage:
    python3 tools/field_md_build.py SOURCE_MARKDOWN OUT.odt [--resource-path DIR] [--dry-run]
"""
from __future__ import annotations

__version__ = "1.0.1"  # Hollingham (2026) — 2026-10-01 (D-220). The temporary pandoc input is in.txt
#   (read as markdown), so docref_lint does not take it for a cited document.
# 1.0.0  # 2026-10-01 (D-219). First issue, for Paper M.

import argparse
import html
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import field_sync as fs        # noqa: E402
from field_convert import field_name  # noqa: E402

ALIASES = {
    "cfg": "src/utils/config.py",
    "00": "outputs/00_climate_summary/00_report_numbers.csv",
    "01": "outputs/01_data_prep/01_report_numbers.csv",
    "01b": "outputs/01b_water_table/01b_report_numbers.csv",
    "03": "outputs/03_state_space_model/03_report_numbers.csv",
    "03_14": "outputs/03_state_space_model/03_14_centroid_window_sensitivity.csv",
    "03_18": "outputs/03_state_space_model/03_18_datum_invariance.csv",
    "12": "outputs/12_figure_site_overview/12_report_numbers.csv",
    "26": "outputs/26_van_willegen_msl/26_report_numbers.csv",
    "48": "outputs/48_pastas_crosscheck/48_report_numbers.csv",
}
TOKEN = re.compile(r"⟪([^|⟫]+)\|([^|⟫]+)\|([^⟫]+)⟫")
MARK = "ZQF{:04d}QZ"


def spec_of(s: str) -> dict:
    parts = s.split()
    dp = [p for p in parts if re.fullmatch(r"dp\d+", p)]
    if len(dp) != 1:
        raise ValueError(f"spec {s!r}: exactly one dpN required")
    scale = next((p[1:] for p in parts if re.fullmatch(r"x[\d.]+", p)), "1")
    unknown = [p for p in parts if not re.fullmatch(r"dp\d+|x[\d.]+|abs|plus|th|hy", p)]
    if unknown:
        raise ValueError(f"spec {s!r}: unknown {unknown}")
    return {"scale": scale, "abs": "1" if "abs" in parts else "", "dp": dp[0][2:],
            "plus": "1" if "plus" in parts else "", "minus": "-" if "hy" in parts else "−",
            "thousands": "," if "th" in parts else ""}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("out")
    ap.add_argument("--resource-path", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    src, out = pathlib.Path(a.source), pathlib.Path(a.out)
    if out.exists() and not a.dry_run:
        raise SystemExit(f"{out} exists — versioned documents are never overwritten; bump the version")
    md = src.read_text(encoding="utf-8")
    reg = fs.load_register()
    vals = fs.values()
    fields, uses, faults = {}, [], []
    def sub(m):
        alias, key, spec_s = (g.strip() for g in m.groups())
        source = ALIASES.get(alias, alias)
        try:
            spec = spec_of(spec_s)
        except ValueError as e:
            faults.append(str(e)); return m.group(0)
        v = vals.get((source, key))
        if v is None:
            faults.append(f"not committed: {source} · {key}"); return m.group(0)
        name = field_name(key, spec)
        row = dict(spec, field=name, source_csv=source, key=key, note=f"born a field in {out.stem.split('_v')[0]}")
        old = reg.get(name) or fields.get(name)
        if old and any(old.get(k) != row.get(k) for k in ("source_csv", "key", "scale", "abs", "dp", "plus", "minus", "thousands")):
            faults.append(f"field {name} registered with a different spec"); return m.group(0)
        fields.setdefault(name, reg.get(name, row))
        uses.append((name, fs.render(v, row)))
        return MARK.format(len(uses) - 1)
    md2 = TOKEN.sub(sub, md)
    if "⟪" in md2 or "⟫" in md2:
        faults.append("unparsed token(s) remain: " + ", ".join(re.findall(r"⟪[^⟫]*⟫?", md2)[:5]))
    new = [n for n in fields if n not in reg]
    print(f"field_md_build: {len(uses)} number(s) as {len(fields)} field(s) "
          f"({len(fields) - len(new)} shared with documents already registered, {len(new)} new)")
    for f in faults:
        print("  FAIL", f)
    if faults:
        return 1
    if a.dry_run:
        for n in sorted(fields):
            print(f"  {n:70s} {fs.rendered(fields[n])}")
        return 0
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        (td / "in.txt").write_text(md2, encoding="utf-8")
        ref = td / "ref.odt"
        with ref.open("wb") as fh:
            subprocess.run(["pandoc", "--print-default-data-file", "reference.odt"], stdout=fh, check=True)
        rp = a.resource_path or str(src.parent)
        subprocess.run(["pandoc", "-f", "markdown", str(td / "in.txt"), "-o", str(td / "out.odt"), "--reference-doc", str(ref),
                        "--resource-path", rp], check=True)
        with zipfile.ZipFile(td / "out.odt") as z:
            names = z.namelist()
            blobs = {n: z.read(n) for n in names}
        xml = blobs["content.xml"].decode("utf-8")
        for i, (name, shown) in enumerate(uses):
            mk = MARK.format(i)
            if xml.count(mk) != 1:
                raise SystemExit(f"marker {mk} for {name} found {xml.count(mk)} times after pandoc")
            xml = xml.replace(mk, f'<text:user-field-get text:name="{name}">{html.escape(shown, quote=False)}</text:user-field-get>')
        decls = "".join(f'<text:user-field-decl office:value-type="string" office:string-value="'
                        f'{html.escape(fs.rendered(fields[n]), quote=True)}" text:name="{n}"/>' for n in sorted(fields))
        ot = xml.index("<office:text")
        i = xml.index(">", ot) + 1
        first_block = min(x for x in (xml.find("<text:p", i), xml.find("<text:h", i), len(xml)) if x != -1)
        for anchor in ("</text:sequence-decls>", "</text:variable-decls>"):
            k = xml.find(anchor, i, first_block)
            if k != -1:
                i = k + len(anchor)
                break
        xml = xml[:i] + "<text:user-field-decls>" + decls + "</text:user-field-decls>" + xml[i:]
        blobs["content.xml"] = xml.encode("utf-8")
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = td / "final.odt"
        with zipfile.ZipFile(tmp, "w") as z:
            z.writestr(zipfile.ZipInfo("mimetype"), blobs["mimetype"], compress_type=zipfile.ZIP_STORED)
            for n in names:
                if n != "mimetype":
                    z.writestr(n, blobs[n], compress_type=zipfile.ZIP_DEFLATED)
        shutil.copyfile(tmp, out)
    reg.update({n: fields[n] for n in new})
    fs.save_register(reg)
    print(f"  wrote {out}; registered {len(new)} new field(s) in tools/number_fields.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
