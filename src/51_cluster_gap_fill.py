#!/usr/bin/env python3
"""
51_cluster_gap_fill.py — filling gaps in the record from cluster-mates
======================================================================
WHAT THIS IS
  Clustering says which wells move together; a straight-line regression over the months two wells
  were both read carries one well's measured record into the other's missing months. This step
  tests that idea and, by a rule fixed before the run, adopts a donor rule and fills the network's
  gaps with it (D-275; spec working/updates/NRG_spec_cluster_gap_filling_2026-10-24.md, Martin
  2026-10-24 21:40 and 22:47).

  Part 1, cross-decade grouping. Is "which wells move together" a property of the ground or only of
  the years the clusters were built from? The CCW wells read in 1989-96 that are now in the network
  are clustered on 1989-96 alone, by Script 02's own method (Ward's linkage on 1 - Pearson r), cut
  at the number of modern clusters they span, and compared with the modern assignment (adjusted
  Rand index against a permutation null; the share of same-cluster pairs that stay together).
  Martin's own chart groups of the CCW wells (data/ccw_similarity_groups_martin.csv, from his
  workbook) are reported beside it. A control, added after the first run and outside the rule, clusters the
  same wells by the same method on their modern record: if that recovers the modern partition, a low
  1989-96 agreement is a property of the 1989-96 record and not of the test. Two sensitivities, also outside
  the rule (Martin: the early readings are often at the foot of the pipe), keep the pipe-base readings at the
  pipe-base value, and leave out the most-censored wells.

  Part 2, the hold-out test. At every well read through a window, the window is hidden and filled
  from a donor, under five rules:
      nearest          nearest well with r >= DONOR_MIN_R over the overlap
      best_r           best-correlated well, any distance
      nearest_cluster  nearest well of the same cluster with r >= DONOR_MIN_R
      cluster_median   the median of the target's cluster-mates (target excluded)
      ssm_model_a      Model A fitted outside the window and run freely through it (reference only)
  Two windows of GAPFILL_HOLDOUT_MONTHS: one from GAPFILL_EARLY_START (it holds the 2006-08 excess,
  D-231, and is the late-starting wells' own gap) and the last before REFERENCE_CUTOFF_DATE.
  Cluster membership never sees the hidden months: reference wells keep the committed partition
  (stated, not hidden), and each extended well's best match is recomputed against the reference
  centroids over the months outside the window. Twins (donor within DONOR_TWIN_EXCLUDE_M) are
  excluded from the headline and reported separately.

  The rule is chosen by the run, by the rule fixed before it: the lowest median absolute error of
  the window's spring level (MSL), twins excluded, both windows pooled; where another rule's median
  lies inside the best one's bootstrap 95% interval, the simpler is taken (cluster_median, then
  nearest_cluster, then nearest, then best_r). The SSM is a reference and is never adopted.

  Part 3, the products. Every well's missing months between RECORD_START_DISPLAY and
  REFERENCE_CUTOFF_DATE are filled gap by gap with the adopted rule, as the hold-out fills a window: the
  donor must have been read through enough of the gap, the line is fitted outside it, and only months the
  donor was read are filled. Two products (Martin, 2026-10-24 23:05, "do both"): "tested", where the donor
  covers GAPFILL_MIN_WINDOW_COVER of the gap (the hold-out's own rule, the headline); and "partial", where
  it covers GAPFILL_PRODUCT_PARTIAL_COVER, a separately stated rule the hold-out did not test. Every filled
  month is flagged reconstructed, and flagged again when the donor stood outside the range it was fitted over.

WHAT IT DOES NOT DO
  Reconstructed levels go only to this step's own files. They never feed 01_wells_*, clustering or
  any SSM fit, and no other step reads them (D-275).

INPUTS — committed
  01_wells_reference.csv, 01_wells_extended.csv, 01_climate.csv, 06_pear_membership_audit_sitewide.csv,
  data/well_metadata.csv (coordinates); the CCW 1989-96 depths and code map (as Scripts 39 and 50 read
  them, via utils/hindcast_utils.load_ccw); data/ccw_similarity_groups_martin.csv (a register
  transcribed from Martin's workbook, sheet "CCW chart ex"; a documented raw-input exception, as the
  CCW files are for Script 39). Part 1 is skipped cleanly when the CCW files are absent.

OUTPUTS (outputs/51_cluster_gap_fill/)
  51_01_ccw_cross_decade.csv         per CCW well: code, modern well, modern and 1989-96 cluster
  51_02_ccw_martin_groups.csv        per chart of Martin's: members, their modern and 1989-96 clusters
  51_03_gapfill_holdout.csv          per window x target x rule x twins: donor, distance, r, metrics
  51_04_gapfill_scores.csv           per window (and pooled) x rule x twins: medians, bootstrap CI, n
  51_05_gapfill_reconstructed_monthly.csv  well, month, level, source, donor, rule, extrapolated
  51_06_gapfill_pairs.csv            per well x gap: donor, distance, r, slope, intercept, overlap, months filled, share extrapolated
  51_08_gapfill_reconstructed_monthly_partial.csv, 51_09_gapfill_pairs_partial.csv   the "partial" product
  51_07_cluster_gap_fill.png         held-out error by rule and window; error against donor distance;
                                     the 1989-96 grouping against the modern clusters
  51_report_numbers.csv

Registered in run_analysis.py, Phase 20, tier X, opt-in (--with-supplementary).
Run directly:  python3 src/51_cluster_gap_fill.py [--no-fig]
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) - 2026-10-25. Two claims made in prose had no key to
#   bind (owed by 2026-10-25a): "less than half as much as Model A" (report10, Paper M) and the
#   "two-thirds" pair-share threshold (report8). Emitted now, from values already computed:
#   gapfill_<pooled|early|late>_adopted_to_model_a_msl_err_ratio (adopted rule's median |MSL
#   error| over Model A's, twins excluded) and gapfill_ccw_pair_share_threshold
#   (GAPFILL_DURABLE_PAIR_SHARE). Martin 2026-10-25 06:52 "build the ratio claim". No method
#   change; every existing key and output is unchanged.
# 1.0.0  # Hollingham (2026) - 2026-10-24 (D-275; Martin 21:32 "clustering suggests a way of filling
#   in missing records", 21:40 the spec's calls, 22:47 "proceed", the Paper 1 split; spec
#   NRG_spec_cluster_gap_filling_2026-10-24). First issue; the CCW pipe-base sensitivities added on Martin's 23:18 note.

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402

from utils import paths                                       # noqa: E402
from utils.paths import (                                     # noqa: E402
    DIR_51, OUT_51_CCW_CROSS, OUT_51_CCW_MARTIN, OUT_51_HOLDOUT, OUT_51_SCORES, OUT_51_RECON,
    OUT_51_PAIRS, OUT_51_RECON_PARTIAL, OUT_51_PAIRS_PARTIAL, OUT_51_FIG, OUT_51_REPORT_NUMBERS, INT_WELLS_REFERENCE, INT_WELLS_EXTENDED,
    INT_CLIMATE, INT_PEAR_AUDIT_SITEWIDE, DATA_WELL_METADATA, DATA_CCW_SIMILARITY_MARTIN,
)
from utils.config import (                                    # noqa: E402
    DONOR_MIN_R, DONOR_TWIN_EXCLUDE_M, DONOR_MIN_OVERLAP_MONTHS, GAPFILL_HOLDOUT_MONTHS,
    GAPFILL_EARLY_START, GAPFILL_MIN_WINDOW_COVER, GAPFILL_MIN_CLUSTER_MEMBERS, GAPFILL_N_BOOT,
    GAPFILL_N_PERM, GAPFILL_SEED, GAPFILL_DURABLE_PAIR_SHARE, GAPFILL_CCW_MAX_CENSORED_SHARE, GAPFILL_RULE_ORDER, GAPFILL_PRODUCT_PARTIAL_COVER, E8E_P,
    REFERENCE_CUTOFF_DATE, RECORD_START_DISPLAY, MSL_SPRING_MONTHS, MSL_MIN_MONTHS_PER_SPRING,
    SUMMER_MINIMUM_MONTHS, WINTER_RECHARGE_MONTHS, CLUSTER_LABELS, CLUSTER_COLOURS,
)
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.model_utils import fit_ssm, simulate_ssm           # noqa: E402
from utils.hindcast_utils import load_ccw                     # noqa: E402
from utils.render_utils import MPL_DEFAULTS                   # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402
from utils.console_utils import banner, done, info, phase, result, saved, step, warn   # noqa: E402

RULES = ("nearest", "best_r", "nearest_cluster", "cluster_median", "ssm_model_a")
DONOR_RULES = ("nearest", "best_r", "nearest_cluster")
TWINS = ("excluded", "allowed")


# ──────────────────────────────────────────────────────────────────────────────
# Inputs
# ──────────────────────────────────────────────────────────────────────────────
def load_inputs():
    ref = pd.read_csv(INT_WELLS_REFERENCE, index_col=0, parse_dates=True)
    ext = pd.read_csv(INT_WELLS_EXTENDED, index_col=0, parse_dates=True)
    ref.columns = [normalize_well_name(c) for c in ref.columns]
    ext.columns = [normalize_well_name(c) for c in ext.columns]
    W = pd.concat([ref, ext], axis=1).loc[RECORD_START_DISPLAY:REFERENCE_CUTOFF_DATE]
    aud = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
    aud["_n"] = aud["Well_Normalised"].apply(normalize_well_name)
    aud = aud.set_index("_n")
    meta = pd.read_csv(DATA_WELL_METADATA)
    meta["_n"] = meta["Name"].apply(normalize_well_name)
    xy = meta.drop_duplicates("_n").set_index("_n")[["E", "N"]]
    cl = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)[["P_m", "PET"]]
    return W, list(ref.columns), list(ext.columns), aud, xy, cl


def _dist(xy, a, b) -> float:
    if a not in xy.index or b not in xy.index:
        return float("nan")
    return float(np.hypot(*(xy.loc[a].values - xy.loc[b].values)))


# ──────────────────────────────────────────────────────────────────────────────
# Part 1: the CCW wells, 1989-96 against the modern clusters
# ──────────────────────────────────────────────────────────────────────────────
def _ward_clusters(df: pd.DataFrame, k: int) -> pd.Series:
    """Script 02's clustering: Ward's linkage on 1 - Pearson r (its _correlation_distance)."""
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    corr = df.corr().fillna(0).values
    sq = np.clip(1.0 - corr, 0.0, None)
    np.fill_diagonal(sq, 0.0)
    sq = (sq + sq.T) / 2.0
    lab = fcluster(linkage(squareform(sq, checks=False), method="ward"), k, criterion="maxclust")
    return pd.Series(lab, index=df.columns)


def cross_decade(aud, W):
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        return None, None, {}
    from sklearn.metrics import adjusted_rand_score
    obs, cmap = load_ccw()
    lev_all = obs.pivot_table(index="month", columns="code", values="depth_m_bg")   # pipe-base readings kept
    cen_share = obs.groupby("code")["censored_at_pipe_base"].mean()
    obs = obs[~obs["censored_at_pipe_base"]]
    lev = obs.pivot_table(index="month", columns="code", values="depth_m_bg")
    cm = cmap.set_index("code")
    rows = []
    for code in lev.columns:
        w = cm.loc[code, "well"] if code in cm.index else ""
        w = normalize_well_name(w) if isinstance(w, str) and w else ""
        mod = np.nan
        if w and w in aud.index:
            r = aud.loc[w]
            mod = r["Original_Cluster"] if pd.notna(r["Original_Cluster"]) else r["Best_Match_Cluster"]
        rows.append(dict(code=code, well=w, status=cm.loc[code, "status"] if code in cm.index else "",
                         modern_cluster=mod, n_readings=int(lev[code].notna().sum())))
    t = pd.DataFrame(rows)
    scored = t[t["modern_cluster"].notna() & (t["status"] == "confirmed")]
    k = int(scored["modern_cluster"].nunique())
    lab = _ward_clusters(lev, k)
    t["ccw_cluster"] = t["code"].map(lab)
    s = t.set_index("code").loc[scored["code"]]
    a, b = s["modern_cluster"].astype(int).values, s["ccw_cluster"].astype(int).values
    ari = float(adjusted_rand_score(a, b))
    rng = np.random.default_rng(GAPFILL_SEED)
    perm = np.array([adjusted_rand_score(rng.permutation(a), b) for _ in range(GAPFILL_N_PERM)])
    p = float((np.sum(perm >= ari) + 1) / (GAPFILL_N_PERM + 1))
    same = [(i, j) for i in range(len(a)) for j in range(i + 1, len(a)) if a[i] == a[j]]
    kept = sum(1 for i, j in same if b[i] == b[j])
    share = kept / len(same) if same else float("nan")
    durable = bool(p < E8E_P and share >= GAPFILL_DURABLE_PAIR_SHARE)
    # CONTROL (added after the first run, 2026-10-24, to check the test can discriminate; outside the rule):
    # the same wells, the same method and k, on their MODERN record. A high value means twelve wells are enough
    # to recover the modern partition, so a low 1989-96 value is about the 1989-96 record, not the test.
    mw = [w for w in s["well"] if w in W.columns]
    ctrl = _ward_clusters(W[mw], k)
    control_ari = float(adjusted_rand_score(s.set_index("well").loc[mw, "modern_cluster"].astype(int).values,
                                            ctrl.loc[mw].values))
    t["modern_record_group"] = t["well"].map(ctrl)
    # SENSITIVITY (Martin 2026-10-24 23:18: the early CCW readings are often at the foot of the pipe; outside the
    # rule): readings held at the pipe base are dropped above, which removes summer lows unevenly between wells.
    # (a) keep them at the pipe-base value; (b) leave out the wells with more than GAPFILL_CCW_MAX_CENSORED_SHARE of
    # their readings held there.
    def _ari(df, codes):
        mm = s.loc[codes, "modern_cluster"].astype(int)
        g = _ward_clusters(df[codes], int(mm.nunique()))
        return float(adjusted_rand_score(mm.values, g.loc[codes].values))
    codes_all = list(s.index)
    codes_low = [c for c in codes_all if cen_share.get(c, 0.0) <= GAPFILL_CCW_MAX_CENSORED_SHARE]
    sens_kept = _ari(lev_all, codes_all)
    sens_low = _ari(lev, codes_low)
    t["censored_share"] = t["code"].map(cen_share)
    # Martin's charts
    mg = pd.read_csv(DATA_CCW_SIMILARITY_MARTIN)
    tt = t.set_index("code")
    g_rows = []
    for (chart, title, sim), g in mg.groupby(["chart", "title", "similar"], sort=False):
        codes = list(g["code"])
        mods = [tt.loc[c, "modern_cluster"] if c in tt.index else np.nan for c in codes]
        ccws = [tt.loc[c, "ccw_cluster"] if c in tt.index else np.nan for c in codes]
        mods_k = [int(m) for m in mods if pd.notna(m)]
        g_rows.append(dict(chart=chart, title=title, similar=sim, codes=" ".join(codes),
                           wells=" ".join((tt.loc[c, "well"] or "?") if c in tt.index else "?" for c in codes),
                           modern_clusters=" ".join(str(m) for m in mods_k),
                           ccw_clusters=" ".join(str(int(c)) for c in ccws if pd.notna(c)),
                           one_modern_cluster=len(set(mods_k)) == 1 and len(mods_k) == len(codes)))
    groups = pd.DataFrame(g_rows)
    summ = dict(k=k, n_scored=len(scored), ari=ari, p=p, pair_share=share, n_pairs=len(same), control_ari=control_ari,
                sens_ari_censored_kept=sens_kept, sens_ari_low_censored=sens_low, sens_n_low_censored=len(codes_low),
                durable=durable, span=f"{lev.index.min():%Y-%m} to {lev.index.max():%Y-%m}",
                martin_similar_one_cluster=int(groups[groups["similar"] == "yes"]["one_modern_cluster"].sum()),
                martin_similar_n=int((groups["similar"] == "yes").sum()))
    return t, groups, summ


# ──────────────────────────────────────────────────────────────────────────────
# Part 2: the hold-out test
# ──────────────────────────────────────────────────────────────────────────────
def windows() -> dict:
    early = pd.date_range(GAPFILL_EARLY_START, periods=GAPFILL_HOLDOUT_MONTHS, freq="MS")
    late = pd.date_range(end=REFERENCE_CUTOFF_DATE, periods=GAPFILL_HOLDOUT_MONTHS, freq="MS")
    return {"early": early, "late": late}


def membership(W, ref_cols, ext_cols, aud, hide=None) -> dict:
    """Reference wells: the committed partition. Extended wells: best Pearson match to the reference
    centroids over the months NOT hidden (so the hidden window never informs the donor choice)."""
    mem = {w: int(aud.loc[w, "Original_Cluster"]) for w in ref_cols
           if w in aud.index and pd.notna(aud.loc[w, "Original_Cluster"])}
    vis = W if hide is None else W.drop(index=W.index.intersection(hide))
    cents = {c: vis[[w for w, k in mem.items() if k == c]].mean(axis=1) for c in sorted(set(mem.values()))}
    for w in ext_cols:
        s = vis[w]
        rs = {c: s.corr(cv) for c, cv in cents.items() if (s.notna() & cv.notna()).sum() >= DONOR_MIN_OVERLAP_MONTHS}
        rs = {c: r for c, r in rs.items() if pd.notna(r)}
        if rs:
            mem[w] = max(rs, key=rs.get)
    return mem


def _fit_line(x: pd.Series, y: pd.Series):
    b, a = np.polyfit(x.values, y.values, 1)
    return float(a), float(b)


def _candidates(W, t, win, xy, cover_min):
    """Donor candidates for target t: read through the window, enough overlap outside it."""
    out = []
    tv = W[t].drop(index=W.index.intersection(win)) if win is not None else W[t]
    for d in W.columns:
        if d == t:
            continue
        if win is not None and W[d].reindex(win).notna().mean() < cover_min:
            continue
        dv = W[d].drop(index=W.index.intersection(win)) if win is not None else W[d]
        ok = tv.notna() & dv.notna()
        if ok.sum() < DONOR_MIN_OVERLAP_MONTHS:
            continue
        r = float(np.corrcoef(tv[ok], dv[ok])[0, 1])
        out.append(dict(donor=d, r=r, dist=_dist(xy, t, d), n_overlap=int(ok.sum())))
    return pd.DataFrame(out)


def _pick(cands: pd.DataFrame, rule: str, twins: str, mem: dict, t: str):
    if cands.empty:
        return None
    c = cands.copy()
    if twins == "excluded":
        c = c[~(c["dist"] < DONOR_TWIN_EXCLUDE_M)]
    if rule == "best_r":
        return None if c.empty else c.sort_values("r", ascending=False).iloc[0]
    c = c[c["r"] >= DONOR_MIN_R]
    if rule == "nearest_cluster":
        c = c[c["donor"].map(mem.get) == mem.get(t)] if t in mem else c.iloc[0:0]
    c = c[c["dist"].notna()]
    return None if c.empty else c.sort_values("dist").iloc[0]


def _cluster_median(W, t, mem, exclude=()):
    if t not in mem:
        return None
    mates = [w for w, k in mem.items() if k == mem[t] and w != t and w not in exclude and w in W.columns]
    if len(mates) < GAPFILL_MIN_CLUSTER_MEMBERS:
        return None
    m = W[mates]
    return m.median(axis=1).where(m.notna().sum(axis=1) >= GAPFILL_MIN_CLUSTER_MEMBERS)


def _transfer(target: pd.Series, donor: pd.Series, fit_mask: pd.Series):
    ok = fit_mask & target.notna() & donor.notna()
    if ok.sum() < DONOR_MIN_OVERLAP_MONTHS:
        return None
    a, b = _fit_line(donor[ok], target[ok])
    lo, hi = float(donor[ok].min()), float(donor[ok].max())
    return dict(a=a, b=b, lo=lo, hi=hi, n=int(ok.sum()), r=float(np.corrcoef(donor[ok], target[ok])[0, 1]))


def _season_errors(obs: pd.Series, rec: pd.Series) -> dict:
    """Errors (reconstructed - observed) in the seasonal quantities the project reports."""
    both = pd.DataFrame({"o": obs, "r": rec}).dropna()
    out = {}
    sp = both[both.index.month.isin(MSL_SPRING_MONTHS)]
    g = sp.groupby(sp.index.year)
    sp_ok = g.size() >= MSL_MIN_MONTHS_PER_SPRING
    e_msl = (g["r"].mean() - g["o"].mean())[sp_ok]
    out["msl_abs_err"] = float(e_msl.abs().mean()) if len(e_msl) else np.nan
    out["msl_bias"] = float(e_msl.mean()) if len(e_msl) else np.nan
    out["n_springs"] = int(len(e_msl))
    su = both[both.index.month.isin(SUMMER_MINIMUM_MONTHS)]
    g = su.groupby(su.index.year)
    s_ok = g.size() == len(SUMMER_MINIMUM_MONTHS)
    e_min = (g["r"].min() - g["o"].min())[s_ok]
    out["summer_min_abs_err"] = float(e_min.abs().mean()) if len(e_min) else np.nan
    wi = both[both.index.month.isin(WINTER_RECHARGE_MONTHS)]
    first = min(WINTER_RECHARGE_MONTHS[0], 13)
    hy = np.where(wi.index.month >= first, wi.index.year + 1, wi.index.year)
    g = wi.groupby(hy)
    w_ok = g.size() == len(WINTER_RECHARGE_MONTHS)
    e_max = (g["r"].max() - g["o"].max())[w_ok]
    out["winter_max_abs_err"] = float(e_max.abs().mean()) if len(e_max) else np.nan
    d = both["r"] - both["o"]
    out["rmse"] = float(np.sqrt((d ** 2).mean())) if len(d) else np.nan
    out["bias"] = float(d.mean()) if len(d) else np.nan
    out["n_months"] = int(len(d))
    return out


def holdout(W, ref_cols, ext_cols, aud, xy, cl):
    rows = []
    for wname, win in windows().items():
        mem = membership(W, ref_cols, ext_cols, aud, hide=win)
        targets = [t for t in W.columns
                   if W[t].reindex(win).notna().mean() >= GAPFILL_MIN_WINDOW_COVER
                   and W[t].drop(index=W.index.intersection(win)).notna().sum() >= DONOR_MIN_OVERLAP_MONTHS]
        info(f"{wname} window {win[0]:%Y-%m} to {win[-1]:%Y-%m}: {len(targets)} targets")
        fit_mask = ~W.index.isin(win)
        fit_mask = pd.Series(fit_mask, index=W.index)
        for t in targets:
            obs = W[t].reindex(win)
            cands = _candidates(W, t, win, xy, GAPFILL_MIN_WINDOW_COVER)
            for rule in RULES:
                for twins in (TWINS if rule in DONOR_RULES else ("excluded",)):
                    rec, row = None, dict(window=wname, target=t, cluster=mem.get(t), rule=rule, twins=twins)
                    if rule in DONOR_RULES:
                        pick = _pick(cands, rule, twins, mem, t)
                        if pick is None:
                            rows.append(row); continue
                        tr = _transfer(W[t], W[pick["donor"]], fit_mask)
                        if tr is None:
                            rows.append(row); continue
                        dwin = W[pick["donor"]].reindex(win)
                        rec = tr["a"] + tr["b"] * dwin
                        row.update(donor=pick["donor"], donor_cluster=mem.get(pick["donor"]), dist_m=pick["dist"],
                                   r=tr["r"], n_overlap=tr["n"], slope=tr["b"], intercept=tr["a"],
                                   extrap_share=float(((dwin < tr["lo"]) | (dwin > tr["hi"]))[dwin.notna()].mean()))
                    elif rule == "cluster_median":
                        med = _cluster_median(W, t, mem)
                        if med is None:
                            rows.append(row); continue
                        tr = _transfer(W[t], med, fit_mask)
                        if tr is None:
                            rows.append(row); continue
                        mwin = med.reindex(win)
                        rec = tr["a"] + tr["b"] * mwin
                        row.update(donor=f"C{mem[t]} median", donor_cluster=mem[t], r=tr["r"], n_overlap=tr["n"],
                                   slope=tr["b"], intercept=tr["a"],
                                   extrap_share=float(((mwin < tr["lo"]) | (mwin > tr["hi"]))[mwin.notna()].mean()))
                    else:   # ssm_model_a: fitted outside the window, run freely through it from the month before
                        h = W[t].where(fit_mask)
                        f = fit_ssm(h, cl)
                        before = W[t].loc[:win[0]].iloc[:-1].dropna()
                        if f is None or before.empty or before.index[-1] != win[0] - pd.DateOffset(months=1):
                            rows.append(row); continue
                        c = cl.reindex(win)
                        if c.isna().any().any():
                            rows.append(row); continue
                        rec = pd.Series(simulate_ssm(float(before.iloc[-1]), c["P_m"].values, c["PET"].values,
                                                     f["beta_1_recharge"], f["beta_2_atmospheric_draw"],
                                                     f["beta_3_drainage"]), index=win)
                        row.update(donor="SSM Model A")
                    row.update(_season_errors(obs, rec))
                    rows.append(row)
    return pd.DataFrame(rows)


def _boot_ci(x: np.ndarray, rng) -> tuple[float, float]:
    if len(x) < 2:
        return float("nan"), float("nan")
    meds = [np.median(rng.choice(x, len(x), replace=True)) for _ in range(GAPFILL_N_BOOT)]
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def scores(ho: pd.DataFrame):
    rng = np.random.default_rng(GAPFILL_SEED)
    rows = []
    for (wname, rule, twins), g in list(ho.groupby(["window", "rule", "twins"])) + \
            [(("pooled", r, tw), g) for (r, tw), g in ho.groupby(["rule", "twins"])]:
        x = g["msl_abs_err"].dropna().values
        lo, hi = _boot_ci(x, rng)
        rows.append(dict(window=wname, rule=rule, twins=twins, n_targets=int(g["target"].nunique()),
                         n_scored=int(len(x)), msl_abs_err_median=float(np.median(x)) if len(x) else np.nan,
                         msl_ci_lo=lo, msl_ci_hi=hi,
                         msl_bias_median=float(g["msl_bias"].median()),
                         rmse_median=float(g["rmse"].median()), bias_median=float(g["bias"].median()),
                         summer_min_abs_err_median=float(g["summer_min_abs_err"].median()),
                         winter_max_abs_err_median=float(g["winter_max_abs_err"].median()),
                         extrap_share_median=float(g["extrap_share"].median()) if "extrap_share" in g else np.nan,
                         same_cluster_share=float((g["donor_cluster"] == g["cluster"]).mean())
                         if rule in DONOR_RULES else np.nan))
    sc = pd.DataFrame(rows)
    # the choice, by the rule fixed before the run
    pool = sc[(sc["window"] == "pooled") & (sc["twins"] == "excluded") & sc["rule"].isin(GAPFILL_RULE_ORDER)]
    pool = pool.dropna(subset=["msl_abs_err_median"])
    best = pool.loc[pool["msl_abs_err_median"].idxmin()]
    within = pool[pool["msl_abs_err_median"] <= best["msl_ci_hi"]]
    adopted = next(r for r in GAPFILL_RULE_ORDER if r in set(within["rule"]))
    return sc, adopted, best["rule"]


def distance_relation(ho: pd.DataFrame) -> dict:
    from scipy.stats import spearmanr
    g = ho[ho["rule"].isin(["nearest", "best_r"]) & (ho["twins"] == "allowed")].dropna(subset=["dist_m", "msl_abs_err"])
    if len(g) < 5:
        return dict(rho=np.nan, p=np.nan, n=len(g))
    r = spearmanr(g["dist_m"], g["msl_abs_err"])
    return dict(rho=float(r.statistic), p=float(r.pvalue), n=len(g))


# ──────────────────────────────────────────────────────────────────────────────
# Part 3: the product
# ──────────────────────────────────────────────────────────────────────────────
def _gap_blocks(miss: pd.Series) -> list:
    """Contiguous runs of missing months, each as a DatetimeIndex."""
    blocks, cur = [], []
    for m, v in miss.items():
        if v:
            cur.append(m)
        elif cur:
            blocks.append(pd.DatetimeIndex(cur)); cur = []
    if cur:
        blocks.append(pd.DatetimeIndex(cur))
    return blocks


def reconstruct(W, ref_cols, ext_cols, aud, xy, rule: str, cover: float, product: str):
    """Each contiguous gap of each well is filled as the hold-out test fills a window: the donor must have
    been read through at least `cover` of the gap, and the line is fitted on the months outside it; only the
    months the donor was read are filled. Cluster membership is the committed one (nothing is hidden here).
    `product` is "tested" (cover = GAPFILL_MIN_WINDOW_COVER, the hold-out's own rule) or "partial" (cover =
    GAPFILL_PRODUCT_PARTIAL_COVER, Martin 2026-10-24 23:05; a separately stated rule the hold-out did not test)."""
    mem = membership(W, ref_cols, ext_cols, aud)
    recs, pairs = [], []
    for t in W.columns:
        if W[t].notna().sum() < DONOR_MIN_OVERLAP_MONTHS:
            continue
        for m, v in W[t].dropna().items():
            recs.append(dict(well=t, month=f"{m:%Y-%m}", level_m=v, source="measured", donor="", rule="",
                             product=product, extrapolated=False))
        for blk in _gap_blocks(W[t].isna()):
            fit_mask = pd.Series(~W.index.isin(blk), index=W.index)
            if rule == "cluster_median":
                src = _cluster_median(W, t, mem)
                label, dist = (f"C{mem[t]} median" if t in mem else None), np.nan
                if src is not None and src.reindex(blk).notna().mean() < cover:
                    src = None
            else:
                cands = _candidates(W, t, blk, xy, cover)
                pick = _pick(cands, rule, "excluded", mem, t)
                src = None if pick is None else W[pick["donor"]]
                label, dist = (None, np.nan) if pick is None else (pick["donor"], pick["dist"])
            if src is None:
                pairs.append(dict(well=t, cluster=mem.get(t), gap_start=f"{blk[0]:%Y-%m}", gap_end=f"{blk[-1]:%Y-%m}",
                                  gap_months=len(blk), rule=rule, product=product, donor=None, n_filled=0))
                continue
            tr = _transfer(W[t], src, fit_mask)
            if tr is None:
                continue
            sb = src.reindex(blk)
            fill = (tr["a"] + tr["b"] * sb).dropna()
            ex = ((sb < tr["lo"]) | (sb > tr["hi"]))
            pairs.append(dict(well=t, cluster=mem.get(t), gap_start=f"{blk[0]:%Y-%m}", gap_end=f"{blk[-1]:%Y-%m}",
                              gap_months=len(blk), rule=rule, product=product, donor=label, dist_m=dist, r=tr["r"],
                              slope=tr["b"],
                              intercept=tr["a"], n_overlap=tr["n"], n_filled=len(fill),
                              share_extrapolated=float(ex[fill.index].mean()) if len(fill) else np.nan))
            for m, v in fill.items():
                recs.append(dict(well=t, month=f"{m:%Y-%m}", level_m=v, source="reconstructed", donor=label,
                                 rule=rule, product=product, gap_start=f"{blk[0]:%Y-%m}", extrapolated=bool(ex.loc[m])))
    return pd.DataFrame(recs).sort_values(["well", "month"]), pd.DataFrame(pairs)


# ──────────────────────────────────────────────────────────────────────────────
# Report and figure
# ──────────────────────────────────────────────────────────────────────────────
def report_numbers(cd, sc, adopted, best_rule, dr, pairs, recon, pairs_p, recon_p) -> ReportNumbers:
    rr = ReportNumbers()
    if cd:
        for k in ("k", "n_scored", "ari", "p", "pair_share", "n_pairs", "control_ari", "sens_ari_censored_kept",
                  "sens_ari_low_censored", "sens_n_low_censored", "martin_similar_one_cluster", "martin_similar_n"):
            rr.add(f"gapfill_ccw_{k}", cd[k], unit="" if k in ("ari", "pair_share", "control_ari", "sens_ari_censored_kept",
                                                            "sens_ari_low_censored") else ("p" if k == "p" else "count"),
                   note=f"CCW wells, {cd['span']}, clustered as Script 02 and compared with the modern clusters (D-275)")
        rr.add("gapfill_ccw_pair_share_threshold", float(GAPFILL_DURABLE_PAIR_SHARE), unit="fraction",
               note="GAPFILL_DURABLE_PAIR_SHARE: the pair share the durability rule requires (D-275)")
        rr.add("gapfill_ccw_durable", "durable" if cd["durable"] else "not shown", unit="text",
               note="the rule fixed before the run: p < E8E_P and pair share >= GAPFILL_DURABLE_PAIR_SHARE (D-275)")
    for r in sc.itertuples():
        key = f"gapfill_{r.window}_{r.rule}_{r.twins}"
        rr.add(f"{key}_msl_abs_err_median", r.msl_abs_err_median, note=f"median |MSL error|, {r.n_scored} targets (D-275)")
        rr.add(f"{key}_msl_ci_hi", r.msl_ci_hi, note="bootstrap 95% upper (D-275)")
        rr.add(f"{key}_msl_ci_lo", r.msl_ci_lo, note="bootstrap 95% lower (D-275)")
        rr.add(f"{key}_rmse_median", r.rmse_median, note="median monthly RMSE (D-275)")
        rr.add(f"{key}_bias_median", r.bias_median, note="median monthly bias (D-275)")
        rr.add(f"{key}_n", r.n_scored, unit="wells", note="targets scored (D-275)")
        if pd.notna(r.same_cluster_share):
            rr.add(f"{key}_same_cluster_share", r.same_cluster_share, unit="fraction",
                   note="share of chosen donors in the target's cluster (D-275)")
    rr.add("gapfill_adopted_rule", adopted, unit="text", note="adopted by the rule fixed before the run (D-275)")
    # 1.1.0: the adopted rule's error as a share of Model A's, per window (twins excluded), so
    # "less than half as much" and its early/late comparison bind to a committed value.
    ex = sc[sc["twins"] == "excluded"].set_index(["window", "rule"])["msl_abs_err_median"]
    for w in ("pooled", "early", "late"):
        a, m = ex.get((w, adopted), np.nan), ex.get((w, "ssm_model_a"), np.nan)
        if pd.notna(a) and pd.notna(m) and m > 0:
            rr.add(f"gapfill_{w}_adopted_to_model_a_msl_err_ratio", float(a / m), unit="ratio",
                   note=f"median |MSL error|, {adopted} over ssm_model_a, twins excluded (D-275)")
    rr.add("gapfill_best_rule", best_rule, unit="text", note="lowest pooled median |MSL error| (D-275)")
    rr.add("gapfill_distance_rho", dr["rho"], unit="rho", note=f"Spearman, |MSL error| against donor distance, n {dr['n']} (D-275)")
    rr.add("gapfill_distance_p", dr["p"], unit="p", note="(D-275)")
    rr.add("gapfill_wells_filled", int(pairs[pairs["n_filled"] > 0]["well"].nunique()) if len(pairs) else 0, unit="wells",
           note="wells with at least one month filled (D-275)")
    rr.add("gapfill_gaps_unfilled", int((pairs["n_filled"] == 0).sum()) if len(pairs) else 0, unit="gaps",
           note="gaps with no qualifying donor, left empty (D-275)")
    rr.add("gapfill_months_filled", int((recon["source"] == "reconstructed").sum()) if len(recon) else 0,
           unit="months", note="(D-275)")
    rr.add("gapfill_partial_wells_filled", int(pairs_p[pairs_p["n_filled"] > 0]["well"].nunique()) if len(pairs_p) else 0,
           unit="wells", note="partial product: donor read in at least GAPFILL_PRODUCT_PARTIAL_COVER of the gap; untested (D-275)")
    rr.add("gapfill_partial_months_filled", int((recon_p["source"] == "reconstructed").sum()) if len(recon_p) else 0,
           unit="months", note="partial product (D-275)")
    rr.add("gapfill_partial_gaps_unfilled", int((pairs_p["n_filled"] == 0).sum()) if len(pairs_p) else 0, unit="gaps",
           note="partial product (D-275)")
    rr.add("gapfill_share_extrapolated_median", float(pairs["share_extrapolated"].median()) if len(pairs) else np.nan,
           unit="fraction", note="median over filled wells of the share of filled months outside the fitted range (D-275)")
    return rr


def plot(ho, cdt, cd) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.8), dpi=160, gridspec_kw={"width_ratios": [1.6, 1, 0.9]})
    a = ax[0]
    h = ho[ho["twins"] == "excluded"]
    for j, (wname, col) in enumerate((("early", "#b2182b"), ("late", "#2166ac"))):
        for i, rule in enumerate(RULES):
            v = h[(h["window"] == wname) & (h["rule"] == rule)]["msl_abs_err"].dropna() * 1000
            x = i + (j - 0.5) * 0.3
            a.plot(np.full(len(v), x), v, "o", ms=2.5, color=col, alpha=0.4)
            if len(v):
                a.plot([x - 0.12, x + 0.12], [v.median()] * 2, color=col, lw=2,
                       label=f"{wname} window" if i == 0 else None)
    a.set_xticks(range(len(RULES)))
    a.set_xticklabels([r.replace("_", " ") for r in RULES], rotation=20, ha="right", fontsize=7)
    a.set_ylabel("held-out spring level (MSL) error, |mm|")
    a.set_yscale("log")
    a.set_title("(a) each rule, both windows, twins excluded; bars are medians", loc="left", fontsize=8)
    a.legend(fontsize=7)
    a = ax[1]
    g = ho[ho["rule"].isin(["nearest", "best_r"]) & (ho["twins"] == "allowed")].dropna(subset=["dist_m", "msl_abs_err"])
    for rule, mk in (("nearest", "o"), ("best_r", "s")):
        s = g[g["rule"] == rule]
        a.plot(s["dist_m"], s["msl_abs_err"] * 1000, mk, ms=3, alpha=0.6, label=rule.replace("_", " "))
    a.axvline(DONOR_TWIN_EXCLUDE_M, color="0.6", lw=0.7, ls="--")
    a.set_xscale("log")
    a.set_xlabel("donor distance (m)")
    a.set_ylabel("|MSL error| (mm)")
    a.set_title("(b) error against donor distance", loc="left", fontsize=8)
    a.legend(fontsize=7)
    a = ax[2]
    if cdt is not None:
        s = cdt[cdt["modern_cluster"].notna()]
        ct = pd.crosstab(s["modern_cluster"].astype(int), s["ccw_cluster"].astype(int))
        a.imshow(ct.values, cmap="Greys", aspect="auto")
        for (i, j), v in np.ndenumerate(ct.values):
            a.text(j, i, str(v), ha="center", va="center", color="w" if v > ct.values.max() / 2 else "k")
        a.set_yticks(range(len(ct.index)))
        a.set_yticklabels([CLUSTER_LABELS.get(int(c), f"C{c}") for c in ct.index], fontsize=7)
        a.set_xticks(range(len(ct.columns)))
        a.set_xticklabels([f"G{c}" for c in ct.columns], fontsize=7)
        a.set_xlabel("1989-96 group (Ward, 1 - r)")
        a.set_title(f"(c) CCW wells: ARI {cd['ari']:.2f}, p {cd['p']:.3f}", loc="left", fontsize=8)
    else:
        a.axis("off")
    fig.tight_layout()
    fig.savefig(OUT_51_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_51_FIG.name)


def main(no_fig: bool = False) -> int:
    banner("51", "Filling gaps in the record from cluster-mates", version=__version__)
    DIR_51.mkdir(parents=True, exist_ok=True)
    phase(1, "Inputs")
    W, ref_cols, ext_cols, aud, xy, cl = load_inputs()
    info(f"{len(ref_cols)} reference and {len(ext_cols)} extended wells, {W.index[0]:%Y-%m} to {W.index[-1]:%Y-%m}")

    phase(2, "The CCW wells, 1989-96 against the modern clusters")
    cdt, groups, cd = cross_decade(aud, W)
    if cd:
        step(f"{cd['n_scored']} wells, k {cd['k']}: ARI {cd['ari']:.3f} (p {cd['p']:.4f}); "
             f"same-cluster pairs kept together {cd['pair_share']:.2f} of {cd['n_pairs']}")
        step(f"Martin's 'similar' charts within one modern cluster: {cd['martin_similar_one_cluster']} of {cd['martin_similar_n']}")
        step(f"control (outside the rule): the same wells on their modern record, ARI {cd['control_ari']:.3f}")
        step(f"sensitivity (outside the rule): pipe-base readings kept, ARI {cd['sens_ari_censored_kept']:.3f}; "
             f"the {cd['sens_n_low_censored']} least-censored wells only, ARI {cd['sens_ari_low_censored']:.3f}")
        result("cross-decade grouping", "durable" if cd["durable"] else "not shown")
        cdt.to_csv(OUT_51_CCW_CROSS, index=False); saved(OUT_51_CCW_CROSS.name)
        groups.to_csv(OUT_51_CCW_MARTIN, index=False); saved(OUT_51_CCW_MARTIN.name)
    else:
        warn("CCW files absent: Part 1 skipped")

    phase(3, "The hold-out test")
    ho = holdout(W, ref_cols, ext_cols, aud, xy, cl)
    sc, adopted, best_rule = scores(ho)
    for r in sc[(sc["window"] == "pooled") & (sc["twins"] == "excluded")].itertuples():
        step(f"{r.rule:16s} median |MSL error| {r.msl_abs_err_median * 1000:6.1f} mm "
             f"[{r.msl_ci_lo * 1000:.1f}, {r.msl_ci_hi * 1000:.1f}], n {r.n_scored}")
    dr = distance_relation(ho)
    step(f"error against donor distance: Spearman {dr['rho']:+.3f} (p {dr['p']:.4f}, n {dr['n']})")
    result("adopted rule", f"{adopted} (lowest: {best_rule})")
    ho.to_csv(OUT_51_HOLDOUT, index=False); saved(f"{OUT_51_HOLDOUT.name} ({len(ho)} rows)")
    sc.to_csv(OUT_51_SCORES, index=False); saved(f"{OUT_51_SCORES.name} ({len(sc)} rows)")

    phase(4, "The products: every well's gaps filled by the adopted rule")
    recon, pairs = reconstruct(W, ref_cols, ext_cols, aud, xy, adopted, GAPFILL_MIN_WINDOW_COVER, "tested")
    recon_p, pairs_p = reconstruct(W, ref_cols, ext_cols, aud, xy, adopted, GAPFILL_PRODUCT_PARTIAL_COVER, "partial")
    # The partial product is the tested product PLUS half-cover fills of the gaps the tested rule left empty;
    # it never replaces a tested fill (a lower cover can make a different, less complete donor the nearest).
    tested_filled = set(zip(pairs.loc[pairs["n_filled"] > 0, "well"], pairs.loc[pairs["n_filled"] > 0, "gap_start"]))
    keep_p = ~pd.Series(list(zip(pairs_p["well"], pairs_p["gap_start"]))).isin(tested_filled).values
    pairs_p = pd.concat([pairs[pairs["n_filled"] > 0], pairs_p[keep_p]], ignore_index=True)
    add = recon_p[(recon_p["source"] == "reconstructed")
                  & ~pd.Series(list(zip(recon_p["well"], recon_p["gap_start"]))).isin(tested_filled).values]
    recon_p = pd.concat([recon, add], ignore_index=True).sort_values(["well", "month"])
    for rc in (recon, recon_p):
        rc.loc[rc["source"] == "measured", "product"] = "measured"
    for lab, rc, pr in (("tested", recon, pairs), ("partial", recon_p, pairs_p)):
        step(f"{lab}: {pr[pr['n_filled'] > 0]['well'].nunique()} wells, {int((rc['source'] == 'reconstructed').sum())} "
             f"months filled, {int((pr['n_filled'] == 0).sum())} gaps left empty")
    recon.to_csv(OUT_51_RECON, index=False); saved(f"{OUT_51_RECON.name} ({len(recon)} rows)")
    pairs.to_csv(OUT_51_PAIRS, index=False); saved(f"{OUT_51_PAIRS.name} ({len(pairs)} rows)")
    recon_p.to_csv(OUT_51_RECON_PARTIAL, index=False); saved(f"{OUT_51_RECON_PARTIAL.name} ({len(recon_p)} rows)")
    pairs_p.to_csv(OUT_51_PAIRS_PARTIAL, index=False); saved(f"{OUT_51_PAIRS_PARTIAL.name} ({len(pairs_p)} rows)")

    phase(5, "Outputs")
    rr = report_numbers(cd, sc, adopted, best_rule, dr, pairs, recon, pairs_p, recon_p)
    rr.save(OUT_51_REPORT_NUMBERS); saved(f"{OUT_51_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    if not no_fig:
        plot(ho, cdt, cd)
    done("51")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Filling gaps in the record from cluster-mates")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    sys.exit(main(no_fig=ap.parse_args().no_fig))
