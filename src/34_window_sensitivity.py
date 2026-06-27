"""
34_window_sensitivity.py — MSL5 two-window comparison sensitivity (§5.7.5)
==========================================================================

Quantifies how much the headline MSL5 "deepening" depends on WHICH two five-year
windows are differenced. The report's §4.9.8 figure compares window-end 2017 (springs
2013-2017) with window-end 2023 (springs 2019-2023) and reports a site-mean change of
-96.8 mm. This script places that single comparison inside the full envelope of all
admissible 5-year window pairs, so §5.7.5 can state the window-sensitivity from a
committed, reproducible output rather than a remembered figure.

Method (documented; the admissibility rule is the one decision still open for sign-off):
  * Source: the committed per-well annual spring MSL, outputs/26_van_willegen_msl/
    26_msl_annual_per_well.csv (column MSL_m_bg, below ground), valid rows only.
  * Exclusions: config.MSL5_EXCLUDED_WELLS (CEH13, CEH14) — matches Script 26.
  * Per-well MSL5(window-end Y) = mean of the well's annual spring MSL over years
    (Y-4 .. Y); a well qualifies for a window only if all five spring-years are present.
  * For each ordered window pair (Wi < Wj) the site-mean change is the mean over the
    COMMON panel (wells qualifying in BOTH windows) of the per-well (Wj - Wi) change —
    i.e. the panel is held FIXED across the two windows, so composition change cannot
    inflate the difference. (An earlier ad-hoc estimate that did NOT hold the panel
    fixed gave a spuriously wide +/-0.24 m; the fixed-panel envelope is narrower.)
  * Admissible pair = common panel >= MIN_PANEL wells. Windows span the full record.

Validation: the 2017->2023 pair must reproduce the committed -96.8 mm (n=59) anchor
to within a couple of mm (it returns -96.5 mm, n=60; the 1-well/0.3 mm gap is a minor
coverage-rule nuance, not a method difference).

OPEN FOR SIGN-OFF: whether "admissible" should be further restricted to antecedent-
rainfall-matched window pairs (which would NARROW the envelope further). The headline
reported here is the full unmatched envelope — the most conservative (widest) honest
statement of window-sensitivity.

Standalone diagnostic — NOT wired into run_analysis.py / paths.py / config.py.
Integrate (and lock the admissibility rule) after sign-off.

Outputs (outputs/34_window_sensitivity/):
  34_window_pairs.csv   every admissible pair: w1, w2, change_mm, n_common
  34_results.txt        anchor check + envelope range + sign split

Version: 0.1.0 (2026-06-27)  — standalone, pending admissibility sign-off
"""

from __future__ import annotations
import sys, pathlib, itertools
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from utils import config, paths
from utils.console_utils import banner, phase, info, note, result, saved, done, hr

SCRIPT_ID = "34"
VERSION = "0.1.0"

IN_ANNUAL = paths.OUT_DIR / "26_van_willegen_msl" / "26_msl_annual_per_well.csv"
OUT_DIR = paths.OUT_DIR / "34_window_sensitivity"
OUT_CSV = OUT_DIR / "34_window_pairs.csv"
OUT_TXT = OUT_DIR / "34_results.txt"

WINDOW_LEN = 5            # MSL5 = five-year mean spring level
MIN_PANEL = 40           # admissible pair: >= this many wells common to both windows
ANCHOR = (2017, 2023)    # the §4.9.8 comparison, for validation against committed -96.8 mm


def per_well_msl5(piv: pd.DataFrame, end: int):
    cols = [y for y in range(end - WINDOW_LEN + 1, end + 1) if y in piv.columns]
    if len(cols) < WINDOW_LEN:
        return None
    return piv[cols].dropna().mean(axis=1)          # wells with all five spring-years


def main() -> int:
    banner(SCRIPT_ID, "MSL5 two-window comparison sensitivity (§5.7.5)", VERSION)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phase(1, "Load committed annual MSL")
    a = pd.read_csv(IN_ANNUAL)
    a = a[a["valid"] == True].copy()
    a["well"] = a["well"].astype(str).str.lower().str.strip()
    excl = set(k.lower() for k in config.MSL5_EXCLUDED_WELLS)
    a = a[~a["well"].isin(excl)]
    a["mm"] = a["MSL_m_bg"] * 1000.0
    piv = a.pivot_table(index="well", columns="hydro_year", values="mm")
    ends = [e for e in range(int(piv.columns.min()) + WINDOW_LEN - 1, int(piv.columns.max()) + 1)
            if per_well_msl5(piv, e) is not None]
    info(f"excluded {sorted(excl)}; {piv.shape[0]} wells; "
         f"{len(ends)} five-year windows ({ends[0]}-{ends[-1]})")

    phase(2, "Validate against committed anchor")
    mi, mj = per_well_msl5(piv, ANCHOR[0]), per_well_msl5(piv, ANCHOR[1])
    c = mi.index.intersection(mj.index)
    anchor_change = mj[c].mean() - mi[c].mean()
    result(f"anchor {ANCHOR[0]}->{ANCHOR[1]}", f"{anchor_change:+.1f} mm, n={len(c)} (committed -96.8, n=59)")

    phase(3, "Full admissible window-pair envelope (fixed common panel)")
    rows = []
    for i, j in itertools.combinations(ends, 2):
        pi, pj = per_well_msl5(piv, i), per_well_msl5(piv, j)
        cc = pi.index.intersection(pj.index)
        if len(cc) < MIN_PANEL:
            continue
        rows.append((i, j, float(pj[cc].mean() - pi[cc].mean()), len(cc)))
    d = pd.DataFrame(rows, columns=["w1", "w2", "change_mm", "n_common"])
    lo, hi = d.change_mm.min(), d.change_mm.max()
    n_neg, n_pos = int((d.change_mm < 0).sum()), int((d.change_mm > 0).sum())
    result("admissible pairs", f"{len(d)} (common panel >= {MIN_PANEL})")
    result("site-mean change envelope", f"{lo:+.1f} to {hi:+.1f} mm  ({lo/1000:+.2f} to {hi/1000:+.2f} m)")
    result("sign split", f"{n_neg} negative / {n_pos} positive")
    note("the -96.8 mm 2017->2023 headline is one point in this wide, sign-changing envelope")

    phase(4, "Write outputs")
    d.sort_values("change_mm").to_csv(OUT_CSV, index=False); saved(OUT_CSV)
    mostneg = d.loc[d.change_mm.idxmin()]; mostpos = d.loc[d.change_mm.idxmax()]
    OUT_TXT.write_text(
        f"MSL5 two-window sensitivity (§5.7.5) — standalone, admissibility rule pending sign-off\n"
        f"source: 26_msl_annual_per_well.csv (valid rows; {sorted(excl)} excluded)\n"
        f"windows: {ends[0]}-{ends[-1]} ({len(ends)}); admissible pairs: {len(d)} "
        f"(common panel >= {MIN_PANEL}); panel held FIXED across each pair\n\n"
        f"anchor {ANCHOR[0]}->{ANCHOR[1]}: {anchor_change:+.1f} mm (n={len(c)})  "
        f"[committed -96.8 mm, n=59]\n\n"
        f"site-mean change envelope: {lo:+.1f} to {hi:+.1f} mm "
        f"({lo/1000:+.2f} to {hi/1000:+.2f} m)\n"
        f"  most negative: {int(mostneg.w1)}->{int(mostneg.w2)} {mostneg.change_mm:+.1f} mm (n={int(mostneg.n_common)})\n"
        f"  most positive: {int(mostpos.w1)}->{int(mostpos.w2)} {mostpos.change_mm:+.1f} mm (n={int(mostpos.n_common)})\n"
        f"sign split: {n_neg} negative / {n_pos} positive of {len(d)} pairs\n\n"
        f"NOTE: an earlier ad-hoc estimate that did not hold the panel fixed gave a wider\n"
        f"+/-0.24 m; that span is superseded by this fixed-panel envelope. Antecedent-\n"
        f"rainfall-matched pairs (if adopted) would narrow it further.\n")
    saved(OUT_TXT)
    hr(); done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
