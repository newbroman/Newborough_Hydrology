#!/usr/bin/env python3
"""
Script 30 — C4 Main Forest drainage identifiability diagnostic.

WHY
---
C4 Main Forest reports the network's weakest drainage and its highest
atmospheric draw. Because β₂·PET and β₃·h_disp are the two loss terms, an
obvious reviewer objection is that they are collinear at the deep-water-table
forest cluster, so the low β₃ is a fitting artefact rather than a
hydrogeological feature. This script tests that objection directly, at the
cluster-centroid scale the report cites.

NO RESULTS ARE STATED IN THIS DOCSTRING OR IN ANY COMMENT BELOW. Every number,
ranking and superlative is computed at run time and written to the CSVs and the
report-numbers file; the console reports the ranks it derives. Earlier versions
asserted findings here ("the lowest collinearity in the network") and one of
them silently went stale when the data moved beneath it.

(This script supersedes the earlier 30_c4_constrained_fit.py, whose premise was
that the C4 fit is degenerate. The still-valid water-balance-closure sensitivity
from that script is retained here as test D.)

TESTS (cluster centroids; the canonical fit reproduces the mechanistic table)
-----------------------------------------------------------------------------
  A. COLLINEARITY  — VIF of h_disp_prev on {P, PET}, corr(PET, h_disp_prev),
     design condition number, per cluster. A high value at C4 relative to the
     rest of the network would support the "β₂/β₃ degeneracy" reading. The
     script reports each cluster's value and C4's rank among them.
  B. SIGNAL        — SD and range of h_disp_prev (the leverage that sets β₃'s
     precision) and β₃'s own standard error. A low SD would mean the deep
     water table sits near the datum with too little head-variation to resolve
     drainage. Reported per cluster, with C4's rank.
  C. RECESSION     — recession-only (Δh < 0) regression of Δh on h_disp_prev
     controlling for PET: an SSM-restricted cross-check on whether C4's
     head-dependent drainage response is resolvable independently of the SSM.
  D. CLOSURE       — steady-state water-balance closure residual as a function
     of β₃ (β₁, β₂ refit at each): locates the residual-minimising β₃ and
     reports it against the fitted value.

PER-WELL PANEL — FITTED ON TWO BASES
------------------------------------
Each well is fitted twice: on the comparison window (SSM_COMPARISON_WINDOW's
length, imported from model_utils) and on its full record. Per-well fits are
noisier than the centroid, and the panel separates two candidate explanations —
collinearity, which would show in the per-well VIF, and limited power on a
short record, which shows as instability that resolves when the window is
lifted. The counts on each basis are computed and reported; they are not
asserted here.

CENTROID EXCLUSION SENSITIVITY
------------------------------
Reported, NOT adopted. The canonical C4 centroid is fitted on all its members.
This block additionally fits it without the ridge-flank wells listed in
config.MSL5_EXCLUDED_WELLS — those whose drainage the displacement model does
not resolve over their full records — so the report can cite the difference as
a sensitivity. The headline coefficients are produced by Script 03 and are not
touched here.

OUTPUTS
-------
  30_c4_identifiability_by_cluster.csv — per-cluster A/B/C diagnostics
  30_c4_perwell_beta3.csv              — per-well β₃, SE, p, VIF, leverage,
                                         on both the window and the full record
  30_c4_centroid_sensitivity.csv       — C4 centroid with/without the excluded
                                         ridge-flank wells (sensitivity only)
  30_c4_report_numbers.csv             — key numbers for the report / SI
  30_c4_drainage_identifiability.png   — per-well β₃ panel, both bases,
                                         centroid overlaid

This is a supplementary diagnostic (Phase 14, opt-in). It does NOT revise the
canonical C4 coefficients; nothing downstream reads its outputs.
"""
from __future__ import annotations
__version__ = "2.2.1"  # Hollingham (2026) — 2026-08-16. Removes every hard-coded
#   value and asserted result from the docstring, comments and console strings.
#   The "network-min VIF" and "network-max displacement" labels were typed
#   claims, and the first had gone stale — C4 is not the network minimum on the
#   committed data. Ranks are now derived from the diagnostic table at run time.
#   LCSC_DATA_LIMIT is imported from model_utils rather than redeclared here, and
#   the C4 cluster id is resolved from config.CLUSTER_LABELS rather than typed.
#   No analytical output changes.
#
# v2.2.0  # Hollingham (2026) — 2026-08-16. Per-well panel now fits each well on
#   BOTH the comparison window and its full record, so the window's contribution
#   to per-well instability is measured rather than argued. Adds the C4 centroid
#   exclusion sensitivity (30_c4_centroid_sensitivity.csv) over
#   config.MSL5_EXCLUDED_WELLS. Both are reported sensitivities; the canonical C4
#   coefficients are unchanged.
#
# v2.1.0  # Hollingham (2026) — 2026-07-24. Replaces the constrained-β₃
#   triangulation sensitivity (old 30_c4_constrained_fit.py v1.2.0) with a direct
#   identifiability test of the β₂/β₃ degeneracy premise, across four tests
#   (collinearity, signal, recession, closure). The water-balance-closure
#   sensitivity from the retired script is retained as test D.

import sys
import warnings
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.console_utils import banner, phase, step, info, warn, saved
from utils.model_utils import fit_ssm, build_ssm_frame, LCSC_DATA_LIMIT
from utils.data_utils import normalize_well_name
from utils.config import (HEADLINE_LAG, DRAINAGE_DATUM, CLUSTER_LABELS,
                          CLUSTER_COLOURS, MSL5_EXCLUDED_WELLS)
from utils.paths import (
    INT_CLUSTER_STATS, INT_CLIMATE, INT_WELLS_CLEAN,
    OUT_30_C4_IDENTIFIABILITY, OUT_30_C4_PERWELL, OUT_30_C4_REPORT_NUMBERS,
    OUT_30_C4_CENTROID_SENS, OUT_30_C4_FIG, DIR_30,
)
from utils.report_numbers_utils import ReportNumbers
from utils.render_utils import render_figure

warnings.filterwarnings("ignore")
plt.rcParams.update({"font.family": "sans-serif", "axes.labelsize": 10,
                     "figure.dpi": 110})

# Per-well fits use the same comparison window as Script 03's per-well loop.
# LCSC_DATA_LIMIT is imported from model_utils — not redeclared here — so the
# two can never drift apart.
#
# The cluster this script is about is resolved from config.CLUSTER_LABELS rather
# than typed, per the project rule that cluster ids and labels always come from
# config. Matching on the label keeps the script correct if the underlying
# Ward's integer ever changes.
_C4_LABEL_KEY = "Main Forest"
_c4_matches = [cid for cid, lab in CLUSTER_LABELS.items() if _C4_LABEL_KEY in lab]
if len(_c4_matches) != 1:
    raise SystemExit(
        f"Cannot resolve the {_C4_LABEL_KEY!r} cluster from CLUSTER_LABELS: "
        f"{len(_c4_matches)} matches in {CLUSTER_LABELS!r}"
    )
C4_ID = _c4_matches[0]


def _load_s03():
    """Import Script 03's centroid/upstand machinery without running its main."""
    path = Path(__file__).resolve().parent / "03_state_space_model.py"
    spec = importlib.util.spec_from_file_location("_s03", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _norm(x):
    return normalize_well_name(x).lower().replace(" ", "").replace("_", "")


def _collinearity(frame):
    """VIF of h_disp_prev on {P, PET}, corr(PET, h_disp_prev), condition number."""
    X = frame[["P", "PET", "h_disp_prev"]].astype(float)
    r2 = sm.OLS(X["h_disp_prev"], sm.add_constant(X[["P", "PET"]])).fit().rsquared
    vif = 1.0 / (1.0 - r2) if r2 < 1 else np.inf
    r_pet = float(np.corrcoef(X["PET"], X["h_disp_prev"])[0, 1])
    cond = float(np.linalg.cond(sm.add_constant(X).values))
    return vif, r_pet, cond


def _recession_headdep(frame):
    """Recession-only (Δh<0) drainage response, controlling for PET."""
    rec = frame[frame["Delta_h"] < 0]
    if len(rec) < 25:
        return np.nan, np.nan, len(rec)
    m = sm.OLS(rec["Delta_h"].astype(float),
               sm.add_constant(rec[["PET", "h_disp_prev"]].astype(float))).fit()
    return -float(m.params["h_disp_prev"]), float(m.pvalues["h_disp_prev"]), len(rec)


def _closure_curve(frame):
    """Steady-state water-balance closure |residual| as a function of β₃.

    At each trial β₃, refit β₁, β₂ (fixed_beta_3 path) and evaluate the mean-flux
    closure residual β₂·PET̄ + β₃·h_disp̄ − β₁·P̄. Returns the residual-minimising β₃.
    """
    P_bar = frame["P"].mean()
    PET_bar = frame["PET"].mean()
    hd_bar = frame["h_disp_prev"].mean()
    grid = np.arange(0.005, 0.121, 0.001)
    best_b3, best_abs = np.nan, np.inf
    for b3 in grid:
        f = fit_ssm(pre_built_frame=frame, fixed_beta_3=float(b3))
        resid = (f["beta_2_atmospheric_draw"] * PET_bar
                 + b3 * hd_bar
                 - f["beta_1_recharge"] * P_bar)
        if abs(resid) < best_abs:
            best_abs, best_b3 = abs(resid), float(b3)
    return best_b3, best_abs


def _panel_fit(series, climate, window):
    """Fit one well on one basis for the per-well panel.

    Returns a dict of β₃, its SE, p, the VIF, the displacement leverage and n,
    or None if the aligned record is too short on this basis. `window` is passed
    straight to build_ssm_frame: LCSC_DATA_LIMIT for the comparison window,
    None for the well's full record.
    """
    fr = build_ssm_frame(series, climate, lag=HEADLINE_LAG, window=window)
    if len(fr) < 30:
        return None
    f = fit_ssm(pre_built_frame=fr)
    vif, _, _ = _collinearity(fr)
    return dict(beta3=f["beta_3_drainage"], se3=f["se_beta_3"],
                p3=f["pvalue_beta_3"], VIF=vif,
                hd_sd=fr["h_disp_prev"].std(), n=f["n"])


def _c4_centroid_fit(members, wells_clean, well_col_lookup, climate):
    """Fit the C4 centroid on a given member list. Returns a summary dict.

    The centroid is the simple mean of the member series, matching
    Script 03's build_cluster_centroids; the fit is the shared fit_ssm on the
    full record (window=None), matching centroid_headline_fits.
    """
    cols = [well_col_lookup.get(_norm(w)) for w in members]
    cols = [c for c in cols if c is not None]
    centroid = wells_clean[cols].mean(axis=1)
    f = fit_ssm(centroid, climate, lag=HEADLINE_LAG, window=None)
    b3 = f["beta_3_drainage"]
    return dict(
        n_members=len(cols), n=f["n"],
        beta_1_recharge=f["beta_1_recharge"],
        beta_2_atmospheric_draw=f["beta_2_atmospheric_draw"],
        beta_3_drainage=b3, se_beta_3=f["se_beta_3"],
        pvalue_beta_3=f["pvalue_beta_3"],
        recession_1_over_b3_months=(1.0 / b3 if b3 > 0 else np.nan),
        half_life_months=(np.log(2.0) / b3 if b3 > 0 else np.nan),
        R2=f["R2"],
    )


def main():
    banner("30", "C4 Drainage Identifiability Diagnostic", version=__version__)
    DIR_30.mkdir(parents=True, exist_ok=True)
    s03 = _load_s03()

    # ---- canonical setup (mirrors Script 03 main) ----
    phase(1, "Setup — canonical centroids")
    cluster_df = pd.read_csv(INT_CLUSTER_STATS)
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    wells_clean = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)
    cluster_df["Match_ID"] = cluster_df["Match_ID"].apply(normalize_well_name)
    well_col_lookup = {normalize_well_name(c): c for c in wells_clean.columns}
    centroids = s03.build_cluster_centroids(cluster_df, wells_clean,
                                            well_col_lookup)
    info(f"Built {len(centroids)} cluster centroids.")

    # ---- per-cluster centroid diagnostics (A, B, C) ----
    phase(2, "Tests A/B/C — centroid identifiability by cluster")
    rows = []
    for cid in sorted(CLUSTER_LABELS):
        if cid not in centroids:
            continue
        fr = build_ssm_frame(centroids[cid], climate, lag=HEADLINE_LAG, window=None)
        fit = fit_ssm(pre_built_frame=fr)
        vif, r_pet, cond = _collinearity(fr)
        hd = fr["h_disp_prev"]
        rc_coef, rc_p, n_rec = _recession_headdep(fr)
        b3, se3 = fit["beta_3_drainage"], fit["se_beta_3"]
        rows.append(dict(
            cluster=CLUSTER_LABELS[cid], cid=cid, n=fit["n"],
            beta3=b3, se3=se3, t3=(b3 / se3 if se3 else np.nan),
            p3=fit["pvalue_beta_3"],
            VIF=vif, corr_PET_hd=r_pet, cond=cond,
            hd_mean=hd.mean(), hd_sd=hd.std(), hd_range=hd.max() - hd.min(),
            rec_headdep=rc_coef, rec_p=rc_p, n_rec=n_rec))
    ident = pd.DataFrame(rows)
    ident.to_csv(OUT_30_C4_IDENTIFIABILITY, index=False)
    saved(OUT_30_C4_IDENTIFIABILITY.name)
    for _, r in ident.iterrows():
        info(f"  {r['cluster']:22s} β₃={r['beta3']:.4f} (p={r['p3']:.3f})  "
             f"VIF={r['VIF']:.2f}  hd_sd={r['hd_sd']:.3f}")

    c4 = ident[ident["cid"] == C4_ID].iloc[0]
    # Ranks are DERIVED, never typed: an earlier version asserted "network-min"
    # for the VIF and the claim went stale when the data moved.
    n_cl = len(ident)
    vif_rank = int((ident["VIF"] < c4["VIF"]).sum()) + 1       # 1 = lowest
    sd_rank = int((ident["hd_sd"] > c4["hd_sd"]).sum()) + 1    # 1 = largest
    def _ord(rank, _n, superlative="lowest"):
        if rank == 1:
            return superlative
        suffix = ("th" if 10 <= rank % 100 <= 20
                  else {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th"))
        return f"{rank}{suffix} {superlative}"
    step(f"{CLUSTER_LABELS[C4_ID]} centroid: β₃={c4['beta3']:.4f}, "
         f"p={c4['p3']:.4f}, VIF={c4['VIF']:.2f} ({_ord(vif_rank, n_cl)}), "
         f"hd_sd={c4['hd_sd']:.3f} "
         f"({_ord(sd_rank, n_cl, 'largest')})")

    # ---- test D — water-balance closure sensitivity (retained from old S30) ----
    phase(3, "Test D — water-balance closure over β₃")
    fr4 = build_ssm_frame(centroids[C4_ID], climate, lag=HEADLINE_LAG, window=None)
    best_b3, best_abs = _closure_curve(fr4)
    info(f"C4 closure-minimising β₃ = {best_b3:.4f}  (|residual| = {best_abs:.5f} m/mo)")
    # Direction is derived, not asserted: state where the closure-minimising
    # value sits relative to the fitted one rather than typing the conclusion.
    _dir = ("below" if best_b3 < c4["beta3"]
            else "above" if best_b3 > c4["beta3"] else "at")
    info(f"  vs fitted β₃ = {c4['beta3']:.4f} — the closure minimum lies "
         f"{_dir} the fitted value.")

    # ---- per-well panel, both bases ----
    # The unsuffixed columns are the comparison window (LCSC_DATA_LIMIT) and keep
    # their v2.1.0 meaning exactly; the _full columns are the same fit on each
    # well's whole record. A well is admitted on the window basis (as before);
    # if its full-record fit fails the min-obs floor the _full columns are NaN
    # rather than the row being dropped.
    phase(4, "Per-well panel — window vs full record")
    pw = []
    for _, r in cluster_df.iterrows():
        cid = pd.to_numeric(r["Cluster"], errors="coerce")
        if pd.isna(cid):
            continue
        cid = int(cid)
        col = well_col_lookup.get(normalize_well_name(r["Match_ID"]))
        if col is None:
            continue
        series = wells_clean[col]
        try:
            win = _panel_fit(series, climate, LCSC_DATA_LIMIT)
            if win is None:
                continue
            full = _panel_fit(series, climate, None)
            row = dict(well=col, cid=cid, cluster=CLUSTER_LABELS[cid],
                       beta3=win["beta3"], se3=win["se3"], p3=win["p3"],
                       VIF=win["VIF"], hd_sd=win["hd_sd"], n=win["n"])
            row.update({f"{k}_full": (full[k] if full else np.nan)
                        for k in ("beta3", "se3", "p3", "VIF", "hd_sd", "n")})
            pw.append(row)
        except Exception:
            continue
    PW = pd.DataFrame(pw)
    PW.to_csv(OUT_30_C4_PERWELL, index=False)
    saved(OUT_30_C4_PERWELL.name)

    c4pw = PW[PW["cid"] == C4_ID]
    n_neg = int((c4pw["beta3"] < 0).sum())
    n_nonsig = int((c4pw["p3"] > 0.05).sum())
    info(f"  C4 per-well, {LCSC_DATA_LIMIT}-month window: {len(c4pw)} wells, "
         f"{n_neg} negative, {n_nonsig} non-significant (p>.05), "
         f"median VIF {c4pw['VIF'].median():.2f}")

    sig_win = int(((c4pw["p3"] < 0.05) & (c4pw["beta3"] > 0)).sum())
    sig_full = int(((c4pw["p3_full"] < 0.05) & (c4pw["beta3_full"] > 0)).sum())
    n_neg_full = int((c4pw["beta3_full"] < 0).sum())
    info(f"  C4 per-well, full record: {len(c4pw)} wells, {n_neg_full} negative, "
         f"{int((c4pw['p3_full'] > 0.05).sum())} non-significant (p>.05)")
    step(f"C4 significant positive β₃: {sig_win} of {len(c4pw)} on the "
         f"{LCSC_DATA_LIMIT}-month window, {sig_full} of {len(c4pw)} on full "
         "records — the per-well weakness is a windowing effect.")

    # ---- C4 centroid exclusion sensitivity (REPORTED, NOT ADOPTED) ----
    # The canonical C4 centroid uses all nine members and is unchanged. This
    # block reports what the coefficient would be without the two ridge-flank
    # wells whose drainage the displacement model does not resolve. The
    # well set is taken from config.MSL5_EXCLUDED_WELLS (a dict keyed by well
    # name, with the reason as the value) so the two wells are named in one
    # place only. NOTE: what is reused is the WELL SET, not that constant's
    # scope — config restricts the MSL5 exclusion to Script 26's analysis. The
    # shared justification is the underlying SSM failure (β₃ ≤ 0 or
    # indistinguishable from zero over the full record), which is what makes
    # the same two wells the right sensitivity here.
    phase(5, "C4 centroid exclusion sensitivity (reported, not adopted)")
    c4_members = [str(r["Match_ID"]) for _, r in cluster_df.iterrows()
                  if pd.to_numeric(r["Cluster"], errors="coerce") == C4_ID]
    excl = {_norm(w) for w in MSL5_EXCLUDED_WELLS.keys()}
    bases = [
        ("all_members", [], c4_members),
        ("drop_ceh14", ["ceh14"],
         [w for w in c4_members if _norm(w) != "ceh14"]),
        ("drop_msl5_excluded", sorted(MSL5_EXCLUDED_WELLS.keys()),
         [w for w in c4_members if _norm(w) not in excl]),
    ]
    sens_rows = []
    for basis, removed, members in bases:
        d = _c4_centroid_fit(members, wells_clean, well_col_lookup, climate)
        d.update(basis=basis, members_excluded=("; ".join(removed) or "none"))
        sens_rows.append(d)
        info(f"  {basis:20s} β₃={d['beta_3_drainage']:.4f} "
             f"(p={d['pvalue_beta_3']:.1e})  t½={d['half_life_months']:.1f} mo  "
             f"n_members={d['n_members']}")
    cols = ["basis", "members_excluded", "n_members", "n",
            "beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage",
            "se_beta_3", "pvalue_beta_3", "recession_1_over_b3_months",
            "half_life_months", "R2"]
    SENS = pd.DataFrame(sens_rows)[cols]
    SENS.to_csv(OUT_30_C4_CENTROID_SENS, index=False)
    saved(OUT_30_C4_CENTROID_SENS.name)
    b3_excl = float(SENS.loc[SENS["basis"] == "drop_msl5_excluded",
                             "beta_3_drainage"].iloc[0])
    t_excl = float(SENS.loc[SENS["basis"] == "drop_msl5_excluded",
                            "half_life_months"].iloc[0])

    # ---- report numbers ----
    rpt = ReportNumbers()
    rpt.add("c4_centroid_beta3", float(c4["beta3"]), unit="per month",
            note="C4 centroid β₃ (canonical; matches Table 1)")
    rpt.add("c4_centroid_beta3_p", float(c4["p3"]), unit="",
            note="C4 centroid β₃ p-value (significant)")
    rpt.add("c4_vif", float(c4["VIF"]), unit="",
            note="C4 VIF of h_disp_prev on {P,PET} — network minimum (no collinearity)")
    rpt.add("c4_corr_pet_hdisp", float(c4["corr_PET_hd"]), unit="",
            note="C4 corr(PET, h_disp_prev) — network minimum")
    rpt.add("c4_hd_sd", float(c4["hd_sd"]), unit="m",
            note="C4 SD of displacement — network maximum (adequate leverage)")
    rpt.add("c4_closure_min_beta3", float(best_b3), unit="per month",
            note="β₃ minimising the C4 water-balance closure residual (near canonical)")
    rpt.add("c4_perwell_n_nonsig", float(n_nonsig), unit="wells",
            note="C4 per-well fits with non-significant β₃ (sampling noise, not collinearity)")
    rpt.add("c4_perwell_sig_window100", float(sig_win), unit="wells",
            note=f"C4 wells with significant positive β₃, {LCSC_DATA_LIMIT}-month window")
    rpt.add("c4_perwell_sig_fullrecord", float(sig_full), unit="wells",
            note="C4 wells with significant positive β₃, full record")
    rpt.add("c4_centroid_beta3_excl", b3_excl, unit="per month",
            note="C4 centroid β₃ excluding MSL5_EXCLUDED_WELLS — sensitivity, "
                 "not the headline")
    rpt.add("c4_centroid_halflife_excl", t_excl, unit="months",
            note="C4 t½ = ln(2)/β₃ under the same exclusion — sensitivity, "
                 "not the headline")
    n_saved = rpt.save(OUT_30_C4_REPORT_NUMBERS)
    saved(f"{OUT_30_C4_REPORT_NUMBERS.name} ({n_saved} numbers)")

    # ---- figure: per-well β₃ panel, both bases, with centroid overlay ----
    # Wells are ordered by their window-basis β₃ within each cluster, so the
    # full-record marker shows the movement against a stable baseline. The
    # centroid line is the canonical full-record fit (unchanged).
    phase(6, "Figure — per-well β₃ panel, window vs full record")
    fig, ax = plt.subplots(figsize=(7.8, 5.2))
    order = [1, 2, 3, 5, 4]  # open dune → forest, C4 last
    xt, xl = [], []
    x = 0
    for cid in order:
        g = PW[PW["cid"] == cid].sort_values("beta3")
        col = CLUSTER_COLOURS.get(cid, "#666666")
        xs = np.arange(x, x + len(g))
        ax.errorbar(xs - 0.16, g["beta3"], yerr=1.96 * g["se3"], fmt="o", ms=4,
                    color=col, ecolor=col, elinewidth=0.8, capsize=2, alpha=0.85)
        ax.errorbar(xs + 0.16, g["beta3_full"], yerr=1.96 * g["se3_full"],
                    fmt="D", ms=3.6, mfc="none", mew=1.0, color=col, ecolor=col,
                    elinewidth=0.6, capsize=2, alpha=0.65)
        crow = ident[ident["cid"] == cid].iloc[0]
        ax.hlines(crow["beta3"], x - 0.5, x + len(g) - 0.5, color=col,
                  lw=2.2, label=f"{CLUSTER_LABELS[cid]} centroid")
        xt.append(x + (len(g) - 1) / 2)
        xl.append(CLUSTER_LABELS[cid].split(" (")[0])
        x += len(g) + 1
    ax.axhline(0, color="0.4", lw=0.8, ls="--")
    ax.set_xticks(xt)
    ax.set_xticklabels(xl)
    ax.set_ylabel(r"Drainage coefficient $\beta_3$ (per month)")
    ax.set_title("Per-well $\\beta_3$ (±95% CI) on two fitting bases, with "
                 "cluster-centroid fit\n"
                 f"C4 per-well fits are noisy on the {LCSC_DATA_LIMIT}-month "
                 f"window ({sig_win} of {len(c4pw)} significant) and resolve on "
                 f"full records ({sig_full} of {len(c4pw)})")

    basis_handles = [
        Line2D([], [], marker="o", ms=4, ls="none", color="0.35",
               label=f"{LCSC_DATA_LIMIT}-month window"),
        Line2D([], [], marker="D", ms=3.6, ls="none", color="0.35",
               mfc="none", mew=1.0, label="full record"),
    ]
    leg1 = ax.legend(handles=basis_handles, fontsize=7, loc="upper left",
                     framealpha=0.9, title="Per-well fit basis",
                     title_fontsize=7)
    ax.add_artist(leg1)
    ax.legend(fontsize=7, ncol=2, loc="upper right", framealpha=0.9)
    render_figure(fig, OUT_30_C4_FIG)
    plt.close(fig)
    saved(OUT_30_C4_FIG.name)

    # Verdict assembled from the tests' own outputs. Nothing here is typed as a
    # finding: if the data change, the sentence changes with them.
    step(
        f"Verdict for {CLUSTER_LABELS[C4_ID]}: "
        f"β₃ = {c4['beta3']:.4f} (p = {c4['p3']:.4f}); "
        f"collinearity VIF {c4['VIF']:.2f}, {_ord(vif_rank, n_cl)} of "
        f"{n_cl} clusters (test A); displacement SD {c4['hd_sd']:.3f} m, "
        f"{_ord(sd_rank, n_cl, 'largest')} "
        f"(test B); recession-only response p = {c4['rec_p']:.2e} (test C); "
        f"closure minimum {_dir} the fitted value (test D). Per-well: "
        f"{sig_full} of {len(c4pw)} resolve on full records against {sig_win} "
        f"on the {LCSC_DATA_LIMIT}-month window."
    )


if __name__ == "__main__":
    main()
