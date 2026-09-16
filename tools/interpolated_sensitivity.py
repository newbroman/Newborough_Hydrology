#!/usr/bin/env python3
"""interpolated_sensitivity — the exclude_interpolated refit the Supplement describes and never ran.

WHY THIS EXISTS. Methods Supplement S.3 states that the canonical cluster SSM is
fitted with `exclude_interpolated=False`, so interpolated rows enter the design
matrix, and that `exclude_interpolated=True` is "the documented sensitivity" which
"the chapter does not run". It also argues the interpolated footprint is small and
diffuse — 275 cells, 1.3-1.6 % per cluster, and "the SSM aggregates over hundreds
of monthly rows per cluster and is correspondingly robust to this footprint".

Measured 2026-09-16: **127 of those 275 cells (46.2 %) are TWO MONTHS** —
2017-01 (74 wells) and 2011-09 (53) — the two recording breaks, where the raw
sheet's dated column exists and is empty and the whole network was interpolated.
The other 248 months hold 148 cells between them at a median of one. So the
footprint is not diffuse, and one of the two months is a WINTER month, where the
recharge signal and the winter maxima live. Whether that changes anything is the
question this tool answers rather than argues.

WHAT IT DOES. Rebuilds each cluster centroid exactly as Script 03 does, PROVES
the rebuild against the committed artefacts, then refits four ways:

  A  canonical            exclude_interpolated=False  (the published table)
  B  strict               drop any month where ANY member cell is interpolated
  C  breaks only          drop ONLY 2011-09 and 2017-01
  D  majority             drop months where most contributing members are interpolated

C is the one that isolates the disclosure question: it removes the two
network-wide outages and nothing else. B is the Supplement's own wording taken
strictly. Nothing is adopted; this writes to working/updates only.

    python3 tools/interpolated_sensitivity.py 2>&1 | tee scratch/interp_sens.log
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from utils.config import CLUSTER_LABELS, HEADLINE_LAG                  # noqa: E402
from utils.console_utils import banner, info, phase, saved, step, warn  # noqa: E402
from utils.data_utils import normalize_well_name                       # noqa: E402
from utils.model_utils import fit_ssm                                  # noqa: E402
from utils.paths import (INT_CLIMATE, INT_REGIONAL_AVG,                # noqa: E402
                         OUT_03_MECHANISTIC_TABLE)

__version__ = "1.1.0"  # Hollingham (2026) - 2026-09-16. Corrects 1.0.0 the same
#   day, before its verdict was recorded anywhere: the pass/fail test compared an
#   ABSOLUTE change of 0.005 across coefficients spanning 0.06 to 4.6, so it
#   flagged all three scenarios including one that moves nothing material. Now
#   relative to each coefficient's own value, with the rank and sign invariants
#   S.3 actually claims. Also drops a misattribution: S.3's "only at the second
#   decimal" sentence is about the interpolation LIMIT setting, not this flag.
# v1.0.0  # Hollingham (2026) - 2026-09-16. New, for T-35.

OUT = REPO / "working" / "updates"
WELLS_CLEAN = REPO / "outputs" / "01_wells_clean.csv"
PROVENANCE = REPO / "outputs" / "01_wells_provenance.csv"
CLUSTER_STATS = REPO / "outputs" / "02_cluster_stats.csv"
BREAK_MONTHS = ("2011-09", "2017-01")   # measured, not assumed — see the docstring
SELFTEST_TOL_BETA = 5e-4                # the committed table's own precision
SELFTEST_TOL_CENTROID_M = 1e-9
MAJORITY = 0.5
REL_MATERIAL_PCT = 5.0   # a coefficient moving less than this much of its
#   own value, with rank and sign intact, is what S.3 calls robust to the footprint

BETAS = ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage")


def _load():
    lev = pd.read_csv(WELLS_CLEAN, index_col=0, float_precision="round_trip")
    lev.index = pd.to_datetime(lev.index)
    prov = pd.read_csv(PROVENANCE, index_col=0)
    prov.index = pd.to_datetime(prov.index)
    cl = pd.read_csv(CLUSTER_STATS)
    clim = pd.read_csv(INT_CLIMATE, index_col=0, float_precision="round_trip")
    clim.index = pd.to_datetime(clim.index)
    return lev, prov, cl, clim


def _members(cl, lev):
    """{cluster_id: [column names]} — Script 03's own lookup and normalisation."""
    lookup = {normalize_well_name(c): c for c in lev.columns}
    out = {}
    for cid in sorted(pd.to_numeric(cl["Cluster"], errors="coerce")
                      .dropna().astype(int).unique()):
        names = cl[pd.to_numeric(cl["Cluster"], errors="coerce") == cid]["Match_ID"]
        cols = [lookup.get(normalize_well_name(str(w))) for w in names]
        cols = [c for c in cols if c is not None]
        if cols:
            out[int(cid)] = cols
    return out


def main() -> int:
    banner("interpolated sensitivity — the refit S.3 describes and never ran",
           __version__)
    lev, prov, cl, clim = _load()
    mem = _members(cl, lev)
    step(f"{len(mem)} cluster(s); members "
         + ", ".join(f"C{c}:{len(w)}" for c, w in sorted(mem.items())))

    # ── the interpolated footprint, measured rather than quoted ─────────────
    ip = prov.eq("interpolated")
    tot = int(ip.sum().sum())
    by_month = ip.sum(axis=1)
    brk = sum(int(by_month.get(pd.Timestamp(m + "-01"), 0)) for m in BREAK_MONTHS)
    phase("1", "The footprint: is the interpolation diffuse, as S.3 argues?")
    info(f"{tot} interpolated cell(s) in {prov.shape[0]}x{prov.shape[1]} panel "
         f"(S.3 quotes 275)")
    for m, n in by_month.sort_values(ascending=False).head(5).items():
        info(f"  {m:%Y-%m}: {int(n):3d} well(s)")
    step(f"the two breaks {', '.join(BREAK_MONTHS)} hold {brk} of {tot} = "
         f"{100 * brk / tot:.1f} % of ALL interpolation; the remaining "
         f"{prov.shape[0] - len(BREAK_MONTHS)} month(s) hold {tot - brk}, median "
         f"{by_month[by_month > 0].median():.0f} where any")

    # ── centroids, and the SELF-TEST that they are Script 03's ──────────────
    phase("2", "Self-test: the rebuild must reproduce the committed artefacts")
    cent = {c: lev[w].mean(axis=1) for c, w in mem.items()}
    ra = pd.read_csv(INT_REGIONAL_AVG, index_col=0, float_precision="round_trip")
    ra.index = pd.to_datetime(ra.index)
    worst = 0.0
    for c, s in cent.items():
        col = f"C{c}"
        if col not in ra.columns:
            continue
        j = pd.concat([s.rename("mine"), ra[col].rename("theirs")],
                      axis=1, sort=False).dropna()
        if len(j):
            worst = max(worst, float((j["mine"] - j["theirs"]).abs().max()))
    if worst > SELFTEST_TOL_CENTROID_M:
        warn(f"the rebuilt centroids differ from {INT_REGIONAL_AVG.name} by "
             f"{worst:.3e} m — this is NOT Script 03's construction, stopping")
        return 1
    info(f"centroids reproduce {INT_REGIONAL_AVG.name} to {worst:.1e} m")

    canon = pd.read_csv(OUT_03_MECHANISTIC_TABLE, float_precision="round_trip")
    canon["cid"] = canon["Cluster"].astype(str).str.lstrip("Cc").astype(int)
    base = {}
    worst_b, worst_name = 0.0, ""
    for c, s in sorted(cent.items()):
        f = fit_ssm(s, clim, lag=HEADLINE_LAG, window=None)
        base[c] = f
        row = canon[canon["cid"] == c]
        if f is None or not len(row):
            continue
        for b in BETAS:
            d = abs(float(f[b]) - float(row.iloc[0][b]))
            if d > worst_b:
                worst_b, worst_name = d, f"C{c} {b}"
    if worst_b > SELFTEST_TOL_BETA:
        warn(f"the baseline refit does not reproduce {OUT_03_MECHANISTIC_TABLE.name}: "
             f"worst {worst_name} off by {worst_b:.2e}. Every number below would be "
             f"measured against the wrong baseline — stopping")
        return 1
    info(f"baseline beta reproduce {OUT_03_MECHANISTIC_TABLE.name} to "
         f"{worst_b:.1e} (worst: {worst_name or 'none'})")

    # ── the four scenarios ──────────────────────────────────────────────────
    phase("3", "The refits")
    brk_ts = {pd.Timestamp(m + "-01") for m in BREAK_MONTHS}
    rows = []
    for c, s in sorted(cent.items()):
        cols = mem[c]
        ipc = prov[cols].eq("interpolated")
        n_contrib = lev[cols].notna().sum(axis=1).replace(0, np.nan)
        scen = {
            "A_canonical": None,
            "B_strict_any_member": (ipc.sum(axis=1) > 0),
            "C_breaks_only": pd.Series(
                [t in brk_ts for t in s.index], index=s.index),
            "D_majority_members": ((ipc.sum(axis=1) / n_contrib) > MAJORITY),
        }
        for name, mask in scen.items():
            if mask is None:
                f, dropped = base[c], 0
            else:
                mask = mask.reindex(s.index).fillna(False)
                pv = pd.Series(np.where(mask, "interpolated", "measured"),
                               index=s.index)
                f = fit_ssm(s, clim, lag=HEADLINE_LAG, window=None,
                            provenance=pv, exclude_interpolated=True)
                dropped = int(mask.sum())
            if f is None:
                warn(f"  C{c} {name}: no fit returned")
                continue
            r = {"cluster": f"C{c}", "label": CLUSTER_LABELS.get(c, ""),
                 "scenario": name, "months_masked": dropped, "n": int(f["n"]),
                 "R2": round(float(f["R2"]), 4)}
            for b in BETAS:
                r[b] = round(float(f[b]), 6)
                if name != "A_canonical":
                    r[f"d_{b}"] = round(float(f[b]) - float(base[c][b]), 6)
            rows.append(r)
    D = pd.DataFrame(rows)
    p = OUT / "NRG_interpolated_sensitivity.csv"
    D.to_csv(p, index=False)
    saved(f"{p.name}  ({len(D)} row(s))")

    # ── what it says ────────────────────────────────────────────────────────
    phase("4", "What moved")
    for name in ("B_strict_any_member", "C_breaks_only", "D_majority_members"):
        sub = D[D["scenario"] == name]
        if not len(sub):
            continue
        # RELATIVE, not absolute. beta_1 is ~4.6 and beta_3 ~0.06 in these units,
        # so one absolute threshold across the three is meaningless — the first
        # version of this tool used 0.005 and duly flagged every scenario,
        # including one that moves nothing. What S.3 actually claims for
        # exclude_interpolated is that the SSM "aggregates over hundreds of
        # monthly rows per cluster and is correspondingly robust to this
        # footprint", and separately that no cluster "changes rank, sign, or
        # mechanistic signature". Those are the claims tested here. (S.3's "only
        # at the second decimal" sentence is about the interpolation LIMIT
        # setting, not this flag, and is not what this tool measures.)
        base_s = D[D.scenario == "A_canonical"].set_index("cluster")
        sub_s = sub.set_index("cluster")
        rel = max(abs(100.0 * (sub_s.loc[c, b] - base_s.loc[c, b])
                      / abs(base_s.loc[c, b]))
                  for c in base_s.index for b in BETAS)
        ranks_ok, signs_ok = True, True
        for b in BETAS:
            if list(base_s.sort_values(b).index) != list(sub_s.sort_values(b).index):
                ranks_ok = False
            for c in base_s.index:
                if (base_s.loc[c, b] > 0) != (sub_s.loc[c, b] > 0):
                    signs_ok = False
        step(f"{name}: {int(sub['months_masked'].sum())} cluster-month(s) masked, "
             f"n {int(base_s['n'].sum())} -> {int(sub_s['n'].sum())}; "
             f"largest coefficient change {rel:.2f} % of its own value")
        for _, r in sub.iterrows():
            c = r["cluster"]
            pc = [100.0 * (r[b] - base_s.loc[c, b]) / abs(base_s.loc[c, b])
                  for b in BETAS]
            info(f"   {c} b1 {pc[0]:+6.2f}%  b2 {pc[1]:+6.2f}%  b3 {pc[2]:+6.2f}%  "
                 f"R2 {r['R2']:.4f} ({r['R2'] - base_s.loc[c, 'R2']:+.4f})  "
                 f"masked {int(r['months_masked'])}")
        info(f"   rank order preserved on every beta: {ranks_ok}; "
             f"every sign preserved: {signs_ok}")
        if rel < REL_MATERIAL_PCT and ranks_ok and signs_ok:
            step(f"   -> S.3's robustness claim HOLDS here: every coefficient within "
                 f"{REL_MATERIAL_PCT:.0f} % of its published value, no rank change, "
                 f"no sign change")
        else:
            step(f"   -> NOT robust at this scenario: {rel:.1f} % largest move"
                 + ("" if ranks_ok else ", RANK ORDER CHANGES")
                 + ("" if signs_ok else ", A SIGN CHANGES"))
    info("NOT ADOPTED. Writes to working/updates only; the canonical table is "
         "unchanged. Whether the two breaks need disclosing in S.1/S.3, and "
         "whether any fit should exclude them, are Martin's calls (T-35).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
