"""
17_wtf_specific_yield.py — Water Table Fluctuation (WTF) method: specific yield estimated cluster by cluster.
========================
Water Table Fluctuation (WTF) Method — Cluster-Level Specific Yield Estimation
Newborough Warren Coastal Sand Dune Aquifer, 2010–2026 (D-347's window; 1.13.0)

Produces cluster-level WTF S_a estimates (Approaches A and B) for all clusters
in the live partition. Forest groups (FOREST_CIDS from config — C4 and C3f, D-348)
additionally receive an interception-corrected variant following Freeman (2008),
applied to Approach B only. The corrected forest values populate Table 3c of
the manuscript and feed the WTF-S_a volumetric water balance (Table 3d,
Figure 11b).

Individual well-level WTF analysis and spatial mapping are in script 18.

Outputs:
    17_wtf_01_sy_estimates.csv   — cluster S_a estimates, inc. forest corrected rows
    17_wtf_02_regression.png     — OLS regression plots for Approach A
    17_wtf_03_event_boxplot.png  — S_a distribution plots for Approach B
    17_wtf_04_summary.txt        — plain-text summary for manuscript

References:
    Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal 10, 91-109.
    Scanlon, B.R., Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal 10, 18-39.
    Freeman, S. (2008) Hydrological impact of Corsican pine at Newborough Warren.

Full per-script methodology: see chapter S.12 of the Methods Supplement.
The interception-handling derivation (why only P is reduced, not PET) is in
S.12 §"Forest interception correction"; see also `wtf_interception_methodology.md`
in the project store.
"""

__version__ = "1.13.0"  # 2026-11-27 (D-349 (1) A5, (7) B5): the frame is cut at RECORD_FIT_START (D-347); Approach C's interception-corrected forest value is written on the Corrected=True row, not the uncorrected one; the interception sweep is reported as a robustness check that does not discriminate (C4 inside the open-dune range uncorrected), with the unclipped event median beside it; the interception evidence is C3f against C3o (same cluster, other cover): unclipped event medians and the beta_1 ratio from 03_03 (report numbers and summary); a Cluster_ID column so no consumer reads a group id from a label. Was "1.12.0"  # 2026-11-27 (D-348): text and notes name the forest groups C4 and C3f; the cluster series are Script 03's cluster-level centroids, no code change. Was "1.11.0"  # Hollingham (2026) — 2026-11-24 (T-178, D-317). The house style: render_utils.apply_house_style()
#   replaces this script's inline rcParams dict, so MPL_DEFAULTS (fonts, T-176's hinting pins) reaches its figures;
#   only the keys where it departs from the house are set after it. Figures move on the next run.
# "1.10.0"  # Hollingham (2026) - 2026-11-12 (D-332, J-9 phase 2b; Martin 2026-11-12: the drainage correction
#   becomes Model B's own drainage flux). Approach A's correction was dh + |beta_3|*|h| with the cluster-median per-well
#   beta_3 of 03_master_data, no datum, and the CURRENT month's head although the docstring said h_prev. It is now
#   dh + [beta_3*(h_prev + DRAINAGE_DATUM) - alpha] = dh + beta_3*(h_prev + implied_datum_m), with h_prev the previous
#   month's cluster-mean head (depth, negative below ground) and beta_3, alpha, implied_datum_m from Script 03's Model B
#   CENTROID fit (03_03): the series corrected is that centroid hydrograph, and alpha/beta_3 must come from one fit (a
#   per-well median of each is not a pair). A cluster whose implied base is not below ground gets no Approach A value
#   and is counted (wtf_a_n_clusters_model_b_excluded_datum). Approaches B and C do not use beta_3 and do not move.
# 1.9.1  # Hollingham (2026) - 2026-11-11. Docstring only: its first line now says what the script does, for pipeline_index.html (T-197 follow-up). No code change.
# 1.9.0  # Hollingham (2026) - 2026-10-10. Emit-first (spec NRG_spec_emit_first_report9_2026-10-09):
#   report9 SS4.2.4 quotes the event-selection funnel ranges across clusters; new rows in 17_report_numbers.csv,
#   summarised from the Sy table export_csv() builds: sy_event_n_min/_max and sy_event_n_pass_dh_min/_max (all
#   runs, corrected forest rows included), sy_event_n_pass_r_min/_max, sy_event_pct_censored_min and
#   sy_event_median_unclipped_min (uncorrected runs). Additive; no existing output changes.
# 1.8.0  # Hollingham (2026) - 2026-09-30. The Approach B event rules come from config
#   (WTF_EVENT_MIN_RISE_M / _MIN_NET_RECH_M / _SY_MIN / _SY_MAX) instead of module locals and literals,
#   shared with Script 18; the figure title renders them. Values and outputs unchanged.
# 1.7.0  # Hollingham (2026) - 2026-09-29. T-96 (batch 2): first report-numbers file,
#   17_report_numbers.csv (paths.OUT_17_REPORT_NUMBERS), from the uncorrected rows of the
#   17_wtf_01_sy_estimates.csv frame export_csv() builds: per cluster (Well = cluster label)
#   sy_event_clip_shift (unclipped minus clipped event median), sy_ols_to_event_ratio (Sy_OLS_winter /
#   Sy_event_median) and sy_estimator_range (max - min of the event, OLS-winter and rapid-event medians);
#   plus sy_ols_to_event_ratio_mean and sy_ols_to_event_ratio_n_above_1 over the clusters (report9
#   SS4.2.4). export_csv() now returns the frame it writes. Additive; no existing output changes.
# 1.6.0  # Hollingham (2026) — 2026-09-19. Event-selection funnel
#   and censoring disclosure. approach_b_events() now records the attrition at
#   each selection stage (months -> net R > 10 mm -> Δh > 5 mm -> 0.01 < Sy <
#   0.50) and the UNCLIPPED event median, emitted as seven new columns on
#   17_wtf_01_sy_estimates.csv (appended after the historical columns, so the
#   existing order stays byte-stable). 17_wtf_03_event_boxplot.png now draws
#   the 0.50 plausibility ceiling — previously off-axis at ylim 0.45 — and
#   annotates the censored fraction per run. Answers "why do the per-cluster
#   event counts differ (35-62), and is the analysis balanced?": the recharge
#   bar is climate-common, the rise bar tracks responsiveness, and the ceiling
#   censors 24-60% of qualifying events (C5 worst), biasing every event-median
#   low. Emission-only: no existing value changes.
#
# 1.5.0 (2026-09-07). Interception-fraction
#   sweep (17_wtf_06_interception_sweep.csv): Approach-B event-median Sy for the
#   forest clusters re-evaluated at every F on config's INTERCEPTION_SWEEP grid,
#   with the open-dune range (min/max of the uncorrected non-forest event
#   medians, from the same run) and a within-range flag per row. Answers the
#   reviewer question "would a different F give a different convergence?" with a
#   committed CSV rather than an argument (Paper 1 R1/R2). Emission-only: the
#   existing outputs are unchanged.
#
# v1.4.3  # Hollingham (2026) — 2026-08-30. WINTER_MONTHS now imported
#   from config.WINTER_WET_CLIMATE_MONTHS — same months, one definition
#   (D-100). No behavioural change; asserted equal to the literal it replaced.
#
# v1.4.2  # Hollingham (2026) -- 2026-08-18. Store-time rounding removed (D-035): these values
#   are written to CSV at the precision they were computed, and rounding
#   happens where they are displayed. Three decimals is a display rule for
#   quantities of order one; applied at storage it costs a significant
#   figure on the small ones - beta_3 ~ 0.018, Sy ~ 0.31 - and the loss
#   compounds through every statistic taken afterwards.
#
# v1.4.1  # Hollingham (2026) — last revised 2026-08-06
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import pandas as pd
import numpy as np
import matplotlib

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.render_utils import apply_house_style  # noqa: E402  (T-178)
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils.config import (
    WINTER_WET_CLIMATE_MONTHS,
    WTF_EVENT_MIN_RISE_M, WTF_EVENT_MIN_NET_RECH_M, WTF_EVENT_SY_MIN, WTF_EVENT_SY_MAX,
    CLUSTER_LABELS as _CFG_CLUSTER_LABELS,
    CLUSTER_COLOURS as _CFG_CLUSTER_COLOURS,
    FOREST_CIDS,
    FOREST_INTERCEPTION,
    INTERCEPTION_SWEEP_MIN, INTERCEPTION_SWEEP_MAX, INTERCEPTION_SWEEP_STEP,
    WTF_C_DRY_BASELINE, WTF_C_MIN_RISE_M, WTF_C_MAX_DURATION,
    WTF_C_SY_MIN, WTF_C_SY_MAX, WTF_C_BOOTSTRAP_N, WTF_RAPID_BOOT_SEED,
    RECORD_FIT_START,       # 1.13.0 (D-349 (1)): the D-347 record window
    GROUP_HYDRO_CLUSTER,    # 1.13.0 (D-349 (7)): C3f's open partner is the group of its own cluster
)
from utils.paths import (
    make_all_dirs, OUT_DIR, DIR_17, INT_MASTER_DATA, OUT_17_SY_TABLE, OUT_03_MECHANISTIC_TABLE,
    OUT_17_REGRESSION, OUT_17_BOXPLOT, OUT_17_SUMMARY, OUT_17_RAPID_EVENTS,
    OUT_17_INTERCEPTION_SWEEP, OUT_17_REPORT_NUMBERS,
)
from utils.report_numbers_utils import ReportNumbers
from utils.render_utils import render_figure
make_all_dirs()

# ── Constants ──────────────────────────────────────────────────────────────────
WINTER_MONTHS   = list(WINTER_WET_CLIMATE_MONTHS)   # Nov-Mar: PET negligible (D-100)
PET_MAX_WINTER  = 0.025                 # m/month — exclude months above this
# Approach B event rules: WTF_EVENT_* in config.py (shared with Script 18).

# Canopy interception fraction — Freeman (2008), site-specific to Newborough
# Corsican pine. Imported from config.py (authoritative per F.4 of the Methods
# Supplement). Applied to all clusters in FOREST_CIDS:
#   R_eff = (1 − FOREST_INTERCEPTION)·P − PET   (config.py)
# PET is not reduced — Thornthwaite PET is an energy-based atmospheric demand
# independent of land cover, so reducing only P avoids double-counting.
# See chapter S.12 §"Forest interception correction" for full derivation.

# ── Cluster bridge between config (int IDs) and DataFrame (string "C1"–"C5") ──
# config.CLUSTER_LABELS is keyed by integer cluster ID (1–5).
# The regional-averages DataFrame from Script 03 uses column headers "C1"–"C5".
# CLUSTER_IDS is the canonical iteration order; CLUSTER_LABELS / CLUSTER_COLOURS
# are local dicts keyed by the string convention so the rest of the script
# (DataFrame access, CSV labels, figure titles) stays readable.
CLUSTER_IDS     = sorted(_CFG_CLUSTER_LABELS.keys())  # [1, 2, 3, 4, 5]
CLUSTER_LABELS  = {f"C{i}": _CFG_CLUSTER_LABELS[i]  for i in CLUSTER_IDS}
CLUSTER_COLOURS = {f"C{i}": _CFG_CLUSTER_COLOURS[i] for i in CLUSTER_IDS}
FOREST_KEYS     = [f"C{i}" for i in FOREST_CIDS]  # ["C4", "C5"]; D-348: key C5 = C3f (Western Dune, forest)

# Assumed Sy for comparison (literature defaults for coastal sand). C1's lower
# value reflects the lake-buffered cluster's higher fines content; the other
# clusters take the conventional sand value. Values are illustrative comparators,
# not inputs to the WTF calculation itself.
SY_ASSUMED = {f"C{i}": (0.08 if i == 1 else 0.12) for i in CLUSTER_IDS}

apply_house_style()  # T-178: render_utils.MPL_DEFAULTS, then this script's own departures
plt.rcParams.update({'font.sans-serif': ['Arial', 'DejaVu Sans'], 'axes.labelsize': 11, 'axes.titlesize': 12, 'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.fontsize': 9})


# ── Run plan: which (cluster, corrected) pairs to evaluate ──────────────────
def _build_runs():
    """
    Return the list of (cluster_key, corrected_bool) tuples to evaluate.

    Uncorrected runs cover every cluster in the partition. Corrected runs
    cover only the forest clusters (where the canopy interception correction
    is physically motivated). The order is: all uncorrected clusters first
    in CLUSTER_IDS order, then forest-corrected variants in FOREST_CIDS order.
    """
    uncorrected = [(f"C{i}", False) for i in CLUSTER_IDS]
    corrected   = [(f"C{i}", True)  for i in FOREST_CIDS]
    return uncorrected + corrected


def _result_key(cid, corrected):
    """Dict key for the per-run result store."""
    return f"{cid}_corr" if corrected else cid


def _entry_label(cid, corrected):
    """Human-readable label for a (cluster, corrected) entry."""
    return CLUSTER_LABELS[cid] + (" (corrected)" if corrected else "")


def load_data(out_root):
    """Load climate and cluster-mean water table data."""
    climate  = pd.read_csv(out_root / "01_climate.csv",           parse_dates=["Date"])
    regional = pd.read_csv(out_root / "03_regional_averages.csv", parse_dates=["Date"])
    df = regional.merge(climate[["Date", "P_m", "PET"]], on="Date", how="inner")
    df = df.sort_values("Date").reset_index(drop=True)

    # Compute net recharge (m/month) and month
    df["net_R"] = df["P_m"] - df["PET"]
    # Forest interception-corrected recharge — Freeman (2008). Applied to all
    # FOREST_CIDS clusters; the column is shared because the correction
    # depends only on P, PET, and the interception fraction (not on cluster).
    df["net_R_forest_corr"] = df["P_m"] * (1 - FOREST_INTERCEPTION) - df["PET"]
    df["month"] = df["Date"].dt.month

    # Compute Δh (change in cluster-mean head, m/month) for every cluster
    # present in the regional-averages DataFrame.
    for cid in CLUSTER_LABELS.keys():
        if cid in df.columns:
            df[f"dh_{cid}"] = df[cid].diff()
            # 1.10.0 (D-332): the previous month's head, the h_prev of the SSM's drainage term
            df[f"hprev_{cid}"] = df[cid].shift(1)

    # 1.13.0 (D-349 (1), A5): D-347's window. Cut after the differences, so January 2010's rise (from December
    # 2009's head) is kept, as fit_ssm keeps it on a pre-built frame.
    df = df[df["Date"] >= pd.Timestamp(RECORD_FIT_START)].reset_index(drop=True)
    return df


def approach_a_ols(df):
    """
    Approach A: Corrected WTF regression accounting for storage decay.

    The observed Δh reflects both recharge and drainage. 1.10.0 (D-332; Martin 2026-11-12) takes the
    drainage as Model B's own flux,
        Δh = (R / S_a) − [β₃·(h_prev + DRAINAGE_DATUM) − α] = (R / S_a) − β₃·(h_prev + implied_datum_m)
    with h_prev the previous month's cluster-mean head (depth below ground, negative) and implied_datum_m
    = DRAINAGE_DATUM − α/β₃ the base Model B drains to. Rearranging:
        R = S_a · (Δh + β₃·(h_prev + implied_datum_m))
    so OLS regression of R against the corrected rise through the origin recovers S_a as the slope.
    β₃ and α are the cluster CENTROID fit of Script 03 (03_03), the fit to the very hydrograph corrected
    here; until 1.9.1 the correction was β₃·|h| with the cluster median of the per-well β₃, no datum and
    no α (a median of α and a median of β₃ are not one fit, so that source cannot carry α).
    A cluster whose implied base is not below ground gets no Approach A value (D-332).

    R² is reported in the uncentred (no-intercept) form 1 − SS_res / Σy²,
    appropriate for regression through the origin. The standard centred R²
    can return spurious negative values for through-origin fits because it
    compares against the mean of y rather than zero; that artefact (and the
    inverted S_a storage that compounded it) was the v1.1.0 → v1.2.0 fix.

    Approach A is fitted on uncorrected clusters only. Corrected-forest
    variants (Approach B only) are populated separately in approach_b_events.
    """
    # 1.10.0 (D-332): Model B centroid coefficients. If they cannot be read, Approach A falls back to
    # uncorrected Δh with a console warning (as before).
    excluded_datum = {}
    try:
        mech = pd.read_csv(OUT_03_MECHANISTIC_TABLE).set_index("Cluster")
        mb = {int(i): (float(r["beta_3_drainage"]), float(r["alpha"]), float(r["implied_datum_m"]))
              for i, r in mech.iterrows() if int(i) in CLUSTER_IDS}
        for i, (_b3, _a, _z) in list(mb.items()):
            if not _z > 0:
                warn(f"C{i}: Model B implied base {_z:+.2f} m is not below ground; no Approach A S_a (D-332)")
                excluded_datum[i] = _z
                del mb[i]
    except Exception as e:
        warn(f"Could not load Model B β₃/α ({type(e).__name__}: {e}) — using uncorrected Δh")
        mb = None

    results = {}
    winter = df[
        (df["month"].isin(WINTER_MONTHS)) &
        (df["PET"] < PET_MAX_WINTER)
    ].copy()

    # Approach A is fitted on uncorrected clusters only (no _corr entries).
    for cid in CLUSTER_LABELS.keys():
        rkey = cid
        if f"dh_{cid}" not in df.columns:
            results[rkey] = dict(sy=np.nan, r2=np.nan, n=0, se=np.nan)
            continue

        sub = winter[["net_R", f"dh_{cid}", cid, f"hprev_{cid}"]].dropna()
        sub = sub[sub["net_R"] > 0]

        if len(sub) < 10:
            results[rkey] = dict(sy=np.nan, r2=np.nan, n=len(sub), se=np.nan)
            continue

        # Correct Δh for drainage (1.10.0, D-332): Model B's flux, β₃·(h_prev + implied_datum_m)
        #   = β₃·(h_prev + DRAINAGE_DATUM) − α; h_prev is depth (negative below ground)
        cid_int = int(cid[1:])
        if cid_int in excluded_datum:
            results[rkey] = dict(sy=np.nan, r2=np.nan, n=0, se=np.nan)
            continue
        if mb is not None and cid_int in mb:
            b3_val, alpha_val, z_val = mb[cid_int]
            dh_corrected = sub[f"dh_{cid}"] + b3_val * (sub[f"hprev_{cid}"] + z_val)
        else:
            b3_val, alpha_val, z_val = None, None, None
            dh_corrected = sub[f"dh_{cid}"]

        # Only use months where corrected Δh is positive (net recharge signal)
        mask = dh_corrected > WTF_EVENT_MIN_RISE_M
        X = dh_corrected[mask].values
        y = sub["net_R"][mask].values

        if len(X) < 8:
            results[rkey] = dict(sy=np.nan, r2=np.nan, n=len(X), se=np.nan)
            continue

        # OLS through origin: R = Sy · Δh_corr, so the regression slope IS Sy
        slope = np.sum(X * y) / np.sum(X**2)
        Sy    = slope if slope > 0 else np.nan

        y_pred = slope * X
        ss_res = np.sum((y - y_pred) ** 2)
        # Uncentred R² is the appropriate fit metric for OLS through origin
        # (centred R² compares against mean(y) rather than zero and can be
        # spuriously negative even for fits that pass through the cloud
        # well). See Wooldridge, Introductory Econometrics, §6.3.
        ss_tot_uncentred = np.sum(y ** 2)
        r2     = 1 - ss_res / ss_tot_uncentred if ss_tot_uncentred > 0 else np.nan
        n      = len(X)
        mse    = ss_res / max(n - 1, 1)
        # SE(slope) for OLS through origin; since Sy = slope directly,
        # SE(Sy) = SE(slope) — no delta method needed.
        se_slope = np.sqrt(mse / np.sum(X ** 2))
        se_sy = se_slope if slope > 0 else np.nan

        # Soft physical-range check: Sy must lie in (0, 1) for any porous
        # medium; coastal sand is typically 0.20–0.40. A value outside
        # (0, 1) signals a misspecified regression on future data; print
        # a warning rather than raising so the script can still complete.
        if not np.isnan(Sy) and not (0.0 < Sy < 1.0):
            print(f"  [WARNING] {CLUSTER_LABELS[cid]} Approach A S_a = {Sy:.3f} "
                  "is outside the physical range (0, 1). "
                  "Regression may be misspecified.")

        results[rkey] = dict(
            sy=float(Sy), r2=float(r2), n=n,
            se=float(se_sy), data=sub,
            dh_corrected=dh_corrected[mask],
            b3=b3_val, alpha=alpha_val, implied_datum=z_val,
        )
        b3_str = (f"{b3_val:.3f}  α = {alpha_val:+.3f}  base {z_val:.2f} m" if b3_val is not None else "n/a")
        print(f"  {CLUSTER_LABELS[cid]:<32}  S_a = {Sy:.3f}  R² = {r2:.3f}  "
              f"n = {n}  SE = {se_sy:.4f}  β₃ = {b3_str}")

    # Forest corrected entries: NaN placeholders. The corrected fits were
    # unstable in the previous internal version and the report uses Approach B
    # for the corrected forest values. Keeping NaN entries here lets the CSV
    # export and summary writer iterate the same run plan as Approach B.
    for cid in FOREST_KEYS:
        results[f"{cid}_corr"] = dict(sy=np.nan, r2=np.nan, n=np.nan,
                                      se=np.nan)

    return results, excluded_datum


def approach_b_events(df):
    """
    Approach B: Event-based median S_a from rising limb months.
    Sy_i = net_R / Δh for months where Δh > WTF_EVENT_MIN_RISE_M and net_R > WTF_EVENT_MIN_NET_RECH_M.

    Run for every cluster (uncorrected) and additionally for FOREST_CIDS
    clusters with the Freeman (2008) interception correction applied.
    """
    results = {}
    for cid, corrected in _build_runs():
        rkey = _result_key(cid, corrected)
        r_col = "net_R_forest_corr" if corrected else "net_R"

        if f"dh_{cid}" not in df.columns:
            results[rkey] = dict(sy_median=np.nan, q25=np.nan, q75=np.nan,
                                 n=0, sy_values=np.array([]),
                                 n_months=0, n_pass_R=0, n_pass_dh=0,
                                 n_both=0, n_censored=0,
                                 pct_censored=np.nan,
                                 sy_median_unclipped=np.nan)
            continue

        sub = df[[r_col, f"dh_{cid}"]].dropna().copy()
        pass_R  = sub[r_col]        > WTF_EVENT_MIN_NET_RECH_M
        pass_dh = sub[f"dh_{cid}"]  > WTF_EVENT_MIN_RISE_M
        events = sub[pass_R & pass_dh].copy()
        events["sy_i"] = events[r_col] / events[f"dh_{cid}"]
        # SELECTION FUNNEL. The per-cluster event counts differ (35-62), which
        # invites the charge that the analysis is unbalanced. Record the
        # attrition at each stage so it can be explained rather than merely
        # reported: the net-recharge bar is climate-driven and near-identical
        # across clusters, the rise bar tracks cluster responsiveness, and the
        # 0.50 ceiling is the dominant term. The 0.01 floor removes nothing at
        # any cluster; the ceiling censors the UPPER tail only, so every
        # event-median is biased low by an amount that scales with pct_censored.
        n_months  = int(len(sub))
        n_pass_R  = int(pass_R.sum())
        n_pass_dh = int(pass_dh.sum())
        n_both    = int(len(events))
        n_cens    = int((events["sy_i"] >= 0.50).sum())
        med_unclipped = float(events["sy_i"].median()) if n_both else float("nan")
        # Drop physically implausible Sy values
        events = events[(events["sy_i"] > WTF_EVENT_SY_MIN) & (events["sy_i"] < WTF_EVENT_SY_MAX)]

        med = events["sy_i"].median()
        q25 = events["sy_i"].quantile(0.25)
        q75 = events["sy_i"].quantile(0.75)
        n   = len(events)

        results[rkey] = dict(
            sy_median=float(med), q25=float(q25), q75=float(q75),
            n=n, sy_values=events["sy_i"].values,
            n_months=n_months, n_pass_R=n_pass_R, n_pass_dh=n_pass_dh,
            n_both=n_both, n_censored=n_cens,
            pct_censored=(100.0 * n_cens / n_both) if n_both else float("nan"),
            sy_median_unclipped=med_unclipped,
        )
        print(f"  {_entry_label(cid, corrected):<32}  S_a median = {med:.3f}  "
              f"IQR [{q25:.3f}, {q75:.3f}]  n = {n}")

    return results


def _event_median_sy(df, cid, r_col):
    """Approach-B event-median S_a for one cluster and one recharge column —
    the same selection as approach_b_events(), factored so the sweep cannot
    drift from the headline computation."""
    sub = df[[r_col, f"dh_{cid}"]].dropna().copy()
    events = sub[(sub[r_col] > WTF_EVENT_MIN_NET_RECH_M) & (sub[f"dh_{cid}"] > WTF_EVENT_MIN_RISE_M)].copy()
    events["sy_i"] = events[r_col] / events[f"dh_{cid}"]
    med_unclipped = float(events["sy_i"].median()) if len(events) else float("nan")   # 1.13.0: ceiling lifted
    events = events[(events["sy_i"] > WTF_EVENT_SY_MIN) & (events["sy_i"] < WTF_EVENT_SY_MAX)]
    return (float(events["sy_i"].median()), float(events["sy_i"].quantile(0.25)),
            float(events["sy_i"].quantile(0.75)), int(len(events)), med_unclipped)


def approach_b_interception_sweep(df, b_results):
    """
    Sensitivity of the Approach-B forest-cluster S_a to the interception fraction.

    For every F on the config grid, recompute the forest clusters' event-median S_a
    with R_eff = (1 - F)·P - PET and compare it with the open-dune range - the
    min and max of the UNCORRECTED event medians of the non-forest clusters in
    this same run (so the range is never typed). One row per (F, cluster), plus
    the F-interval over which each forest cluster sits inside the range, printed
    and returned. F = FOREST_INTERCEPTION is always included in the grid so the
    headline row is present exactly.

    1.13.0 (D-349 (7), B5): this is a ROBUSTNESS CHECK, not a test of the interception fraction. The open-dune range
    is wide, the 0.50 ceiling censors the upper tail of every run, and C4 sits inside the range with no correction
    (F = 0), so the sweep cannot fail. It shows that the forest groups' convergence on the open dune does not depend
    on F. The evidence for interception is interception_evidence(): C3f against C3o.
    """
    open_dune = [b_results[f"C{i}"]["sy_median"] for i in CLUSTER_IDS
                 if i not in FOREST_CIDS and f"C{i}" in b_results
                 and np.isfinite(b_results[f"C{i}"]["sy_median"])]
    lo, hi = (min(open_dune), max(open_dune)) if open_dune else (np.nan, np.nan)
    grid = np.arange(INTERCEPTION_SWEEP_MIN, INTERCEPTION_SWEEP_MAX + 1e-9,
                     INTERCEPTION_SWEEP_STEP)
    grid = np.unique(np.append(grid, FOREST_INTERCEPTION))
    rows = []
    for F in grid:
        r_col = "_sweep_R"
        df[r_col] = df["P_m"] * (1.0 - F) - df["PET"]
        for i in FOREST_CIDS:
            cid = f"C{i}"
            if f"dh_{cid}" not in df.columns:
                continue
            med, q25, q75, n, med_u = _event_median_sy(df, cid, r_col)
            rows.append(dict(F=float(F), cluster=cid, label=CLUSTER_LABELS[cid],
                             Sy_event_median=med, Sy_event_Q25=q25, Sy_event_Q75=q75,
                             Sy_event_n=n, open_dune_min=lo, open_dune_max=hi,
                             within_open_dune_range=bool(np.isfinite(med) and lo <= med <= hi),
                             is_headline_F=bool(np.isclose(F, FOREST_INTERCEPTION)),
                             # 1.13.0 (D-349 (7)): appended; the ceiling censors the upper tail, so the clipped
                             # median is held inside the range at almost every F
                             Sy_event_median_unclipped=med_u))
        df.drop(columns=[r_col], inplace=True)
    sweep = pd.DataFrame(rows)
    print(f"  open-dune range (uncorrected event medians, non-forest clusters): "
          f"[{lo:.3f}, {hi:.3f}]")
    for i in FOREST_CIDS:
        cid = f"C{i}"
        inside = sweep[(sweep.cluster == cid) & sweep.within_open_dune_range]
        if len(inside):
            print(f"  {CLUSTER_LABELS[cid]:<20} inside the range for F in "
                  f"[{inside.F.min():.2f}, {inside.F.max():.2f}] "
                  f"({len(inside)} of {int((sweep.cluster == cid).sum())} grid points)")
        else:
            print(f"  {CLUSTER_LABELS[cid]:<20} never inside the range on this grid")
    print("  (a robustness check, not a test: it does not discriminate between interception fractions, D-349 (7))")
    return sweep


def _forest_open_pairs():
    """1.13.0 (D-349 (7)): (forest group, open group) pairs with the same hydrogeology - each forest group whose
    cluster also has an open group (GROUP_HYDRO_CLUSTER; group ids, never labels). Today [(5, 3)]: C3f and C3o.
    C4 is a cluster of its own and has no open partner."""
    pairs = []
    for g in FOREST_CIDS:
        h = GROUP_HYDRO_CLUSTER.get(g)
        if h is not None and h != g and h in CLUSTER_IDS and h not in FOREST_CIDS:
            pairs.append((g, h))
    return pairs


def interception_evidence(b_results, sweep):
    """1.13.0 (D-349 (7), B5): the evidence for interception - a forest group against the open group of the same
    hydrogeological cluster (C3f against C3o), on the quantities the 0.50 ceiling does not hold in range:

      - the UNCLIPPED event-median S_a of the forest group, uncorrected and corrected, against the open group's;
      - the interception fraction at which the forest group's unclipped median equals the open group's (linear
        interpolation on the sweep grid; NaN where the grid does not bracket it);
      - the ratio of the two groups' centroid beta_1 (03_03, Model B): if interception I = F*P sits in recharge, a
        regression on gross P absorbs it as (1 - F)*beta_1. The ratio also scales with 1/S_a, so it is suggestive,
        not diagnostic (stage 1 verification, finding 2).

    Returns a list of dicts, one per pair."""
    out = []
    try:
        mech = pd.read_csv(OUT_03_MECHANISTIC_TABLE).set_index("Cluster")
    except Exception as e:  # noqa: BLE001 - reported, the beta_1 ratio is then NaN
        warn(f"03_03 not readable ({type(e).__name__}: {e}); the beta_1 ratio is NaN")
        mech = None
    for g, h in _forest_open_pairs():
        fk, ok = f"C{g}", f"C{h}"
        u_f = b_results.get(fk, {}).get("sy_median_unclipped", np.nan)
        c_f = b_results.get(f"{fk}_corr", {}).get("sy_median_unclipped", np.nan)
        u_o = b_results.get(ok, {}).get("sy_median_unclipped", np.nan)
        F_match = np.nan
        sw = sweep[sweep["cluster"] == fk].sort_values("F") if len(sweep) else sweep
        if len(sw) and np.isfinite(u_o):
            d = (sw["Sy_event_median_unclipped"] - u_o).to_numpy(float)
            Fg = sw["F"].to_numpy(float)
            for i in range(len(d) - 1):
                if np.isfinite(d[i]) and np.isfinite(d[i + 1]) and d[i] * d[i + 1] <= 0 and d[i] != d[i + 1]:
                    F_match = float(Fg[i] - d[i] * (Fg[i + 1] - Fg[i]) / (d[i + 1] - d[i]))
                    break
        b1_ratio = np.nan
        if mech is not None and g in mech.index and h in mech.index:
            b1_ratio = float(mech.loc[g, "beta_1_recharge"]) / float(mech.loc[h, "beta_1_recharge"])
        out.append(dict(forest=g, open=h, forest_key=fk, open_key=ok,
                        sy_unclipped_forest_uncorrected=float(u_f), sy_unclipped_forest_corrected=float(c_f),
                        sy_unclipped_open=float(u_o), F_match_unclipped=F_match, beta_1_ratio=b1_ratio))
        print(f"  {CLUSTER_LABELS[fk]} against {CLUSTER_LABELS[ok]}: unclipped event-median S_a "
              f"{u_f:.3f} uncorrected, {c_f:.3f} corrected (F = {FOREST_INTERCEPTION:g}), against {u_o:.3f}; "
              f"equal at F = {F_match:.3f}; beta_1 ratio {b1_ratio:.3f} (1 - F = {1 - FOREST_INTERCEPTION:.3f})")
    return out


def approach_c_rapid_events(df):
    """
    Approach C: rapid-recharge-event S_a after Crosbie et al. (2005).

    Independent of Approaches A and B by construction. Where A corrects for
    drainage mechanistically (β₃) and B applies no correction (bias-low), C
    *selects* episodes in which the drainage contribution to the observed rise
    is negligible: short, sharply-rising events that follow a multi-month
    drainage baseline, so the naïve S_a = ΣR / Δh is approximately unbiased
    without a β₃ term.

    Per cluster, on the time-ordered cluster-mean head series:
      1. A candidate episode requires WTF_C_DRY_BASELINE consecutive prior
         months of Δh ≤ 0 (drainage-only quasi-steady state).
      2. It starts on the first month with Δh > 0 and runs while Δh > 0, up to
         the WTF_C_MAX_DURATION cap.
      3. The cumulative head rise h[e] − h[s−1] must be ≥ WTF_C_MIN_RISE_M.
      4. Per-episode Sy_i = Σ net_R[s..e] / (h[e] − h[s−1]), where net_R is the
         Freeman (2008) interception-corrected recharge for FOREST_CIDS
         clusters and the uncorrected recharge otherwise.
      5. Sy_i is kept only within [WTF_C_SY_MIN, WTF_C_SY_MAX]. The cluster
         estimate is the median of kept Sy_i, with a WTF_C_BOOTSTRAP_N-resample
         95 % CI on the median (seed WTF_RAPID_BOOT_SEED).

    Approach C is a reported triangulation only and does NOT propagate to any
    other pipeline script (the Approach B per-well S_a in Script 18 remains the
    pipeline-consumed canonical). Forest clusters are typically data-limited
    (small n); they are reported with n and CI shown and a small-sample caveat.
    """
    rng = np.random.default_rng(WTF_RAPID_BOOT_SEED)
    results = {}

    for cid in [f"C{i}" for i in CLUSTER_IDS]:
        corrected = int(cid[1:]) in FOREST_CIDS
        r_col = "net_R_forest_corr" if corrected else "net_R"

        if f"dh_{cid}" not in df.columns:
            results[cid] = dict(sy_median=np.nan, ci_lo=np.nan, ci_hi=np.nan,
                                n=0, mean_duration=np.nan, mean_rise=np.nan,
                                corrected=corrected,
                                episodes=pd.DataFrame())
            continue

        # Time-ordered arrays (df is sorted by Date in load_data).
        h  = df[cid].to_numpy(dtype=float)
        dh = df[f"dh_{cid}"].to_numpy(dtype=float)
        r  = df[r_col].to_numpy(dtype=float)
        dates = df["Date"].to_numpy()
        n_months = len(df)

        episodes = []
        i = WTF_C_DRY_BASELINE
        while i < n_months:
            # Need a defined rising month to open an episode.
            if not (np.isfinite(dh[i]) and dh[i] > 0):
                i += 1
                continue

            # Baseline: WTF_C_DRY_BASELINE prior months all with Δh ≤ 0.
            base = dh[i - WTF_C_DRY_BASELINE:i]
            if not (np.all(np.isfinite(base)) and np.all(base <= 0)):
                i += 1
                continue

            # Extend the episode while Δh > 0, up to the duration cap.
            s = i
            e = i
            while (e + 1 < n_months
                   and np.isfinite(dh[e + 1]) and dh[e + 1] > 0
                   and (e + 1 - s + 1) <= WTF_C_MAX_DURATION):
                e += 1

            rise = h[e] - h[s - 1]
            recharge = np.nansum(r[s:e + 1])

            if np.isfinite(rise) and rise >= WTF_C_MIN_RISE_M and recharge > 0:
                sy_i = recharge / rise
                if WTF_C_SY_MIN <= sy_i <= WTF_C_SY_MAX:
                    episodes.append({
                        "start":     pd.Timestamp(dates[s]).strftime("%Y-%m"),
                        "end":       pd.Timestamp(dates[e]).strftime("%Y-%m"),
                        "duration":  e - s + 1,
                        "rise_m":    float(rise),
                        "recharge_m": float(recharge),
                        "sy_i":      float(sy_i),
                    })

            i = e + 1  # non-overlapping episodes

        ep_df = pd.DataFrame(episodes)
        n = len(ep_df)

        if n == 0:
            results[cid] = dict(sy_median=np.nan, ci_lo=np.nan, ci_hi=np.nan,
                                n=0, mean_duration=np.nan, mean_rise=np.nan,
                                corrected=corrected, episodes=ep_df)
            print(f"  {CLUSTER_LABELS[cid]:<32}  no qualifying episodes")
            continue

        sy_vals = ep_df["sy_i"].to_numpy()
        med = float(np.median(sy_vals))

        if n >= 2:
            boot = np.array([
                np.median(rng.choice(sy_vals, size=n, replace=True))
                for _ in range(WTF_C_BOOTSTRAP_N)
            ])
            ci_lo, ci_hi = np.percentile(boot, [2.5, 97.5])
        else:
            ci_lo = ci_hi = np.nan

        results[cid] = dict(
            sy_median=float(med),
            ci_lo=float(ci_lo) if np.isfinite(ci_lo) else np.nan,
            ci_hi=float(ci_hi) if np.isfinite(ci_hi) else np.nan,
            n=n,
            mean_duration=float(ep_df["duration"].mean()),
            mean_rise=float(ep_df["rise_m"].mean()),
            corrected=corrected,
            episodes=ep_df,
        )
        ci_s = (f"[{ci_lo:.3f}, {ci_hi:.3f}]" if np.isfinite(ci_lo)
                else "[n/a — single episode]")
        corr_s = "  (interception-corrected)" if corrected else ""
        print(f"  {CLUSTER_LABELS[cid]:<32}  S_a = {med:.3f}  95% CI {ci_s}  "
              f"n = {n}{corr_s}")

    return results


def plot_rapid_events(c_results, out_path):
    """Figure: Approach C rapid-recharge-event S_a per cluster (median + CI + n)."""
    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor="white")
    ax.set_facecolor("#FAFAFA")

    cids = [f"C{i}" for i in CLUSTER_IDS]
    positions = list(range(1, len(cids) + 1))

    for pos, cid in zip(positions, cids):
        c = c_results[cid]
        if c["n"] == 0 or np.isnan(c["sy_median"]):
            continue
        colour = CLUSTER_COLOURS[cid]
        med = c["sy_median"]
        lo, hi = c["ci_lo"], c["ci_hi"]
        if np.isfinite(lo) and np.isfinite(hi):
            ax.errorbar(pos, med, yerr=[[med - lo], [hi - med]],
                        fmt="o", color=colour, ecolor=colour, elinewidth=1.6,
                        capsize=5, markersize=9, zorder=5,
                        markeredgecolor="black", markeredgewidth=0.6)
        else:
            ax.scatter(pos, med, color=colour, s=90, zorder=5,
                       edgecolor="black", linewidth=0.6, marker="o")
        # Overlay the individual per-episode Sy as a light strip.
        ep = c_results[cid]["episodes"]
        if not ep.empty:
            jitter = (np.random.default_rng(WTF_RAPID_BOOT_SEED + pos)
                      .uniform(-0.12, 0.12, len(ep)))
            ax.scatter(pos + jitter, ep["sy_i"], color=colour, alpha=0.35,
                       s=22, zorder=3)
        flag = "" if c["corrected"] is False else "†"
        ax.text(pos, hi + 0.012 if np.isfinite(hi) else med + 0.012,
                f"{med:.3f}{flag}\n(n={c['n']})",
                ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_xticks(positions)
    ax.set_xticklabels([CLUSTER_LABELS[c] for c in cids],
                       fontsize=8, rotation=20, ha="right")
    ax.set_ylabel("Apparent storage coefficient $S_a$ (WTF); dashed: assumed specific yield Sy")
    ax.set_ylim(0, 0.55)
    ax.axhline(0.12, color="gray", lw=1.0, ls=":", alpha=0.7,
               label="Assumed Sy non-C1 = 0.12")
    ax.axhline(0.08, color="gray", lw=1.0, ls="--", alpha=0.7,
               label="Assumed Sy C1 = 0.08")
    ax.legend(fontsize=8.5, framealpha=0.9, loc="upper left")
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    ax.set_title(
        "Approach C — WTF apparent storage coefficient $S_a$: Rapid-Recharge-Event Method\n"
        "Cluster median with 95% bootstrap CI; faint points = per-episode S_a\n"
        f"Episode: ≥{WTF_C_DRY_BASELINE} mo Δh≤0 baseline, rise ≥"
        f"{WTF_C_MIN_RISE_M*1000:.0f} mm over ≤{WTF_C_MAX_DURATION} mo "
        "(Crosbie et al., 2005). † = interception-corrected forest cluster",
        fontsize=10, fontweight="bold",
    )
    plt.tight_layout()
    render_figure(fig, out_path, facecolor="white")
    plt.close()
    print(f"Rapid-events figure saved → {out_path.name}")


def plot_regression(df, a_results, out_path):
    """Figure: OLS regression plots for Approach A (uncorrected clusters only)."""
    n_clusters = len(CLUSTER_IDS)
    # 2×3 layout works for up to 6 clusters; under k=5 the last cell is empty.
    nrows, ncols = 2, 3
    fig, axes = plt.subplots(nrows, ncols, figsize=(13, 8), facecolor="white")
    fig.patch.set_facecolor("white")
    axes = axes.flatten()

    cluster_keys = [f"C{i}" for i in CLUSTER_IDS]
    for ax, cid in zip(axes[:n_clusters], cluster_keys):
        r = a_results[cid]
        col = CLUSTER_COLOURS[cid]

        if np.isnan(r["sy"]) or "dh_corrected" not in r:
            ax.text(0.5, 0.5, "Insufficient data", transform=ax.transAxes,
                    ha="center", va="center")
            ax.set_title(CLUSTER_LABELS[cid], fontweight="bold")
            continue

        dh_c = r["dh_corrected"] * 1000
        net_r = r["data"].loc[r["dh_corrected"].index, "net_R"] * 1000

        ax.scatter(dh_c, net_r, color=col, alpha=0.65, s=35, zorder=3,
                   label=f"Winter months (n={r['n']})")

        if not np.isnan(r["sy"]):
            xline = np.linspace(0, dh_c.max(), 100)
            ax.plot(xline, xline * r["sy"], color="black", lw=1.8, zorder=4,
                    label=f"WTF: $S_a$ = {r['sy']:.3f} ± {r['se']:.3f}")
            ax.fill_between(
                xline,
                xline * max(r["sy"] - 2 * r["se"], 0.0),
                xline * (r["sy"] + 2 * r["se"]),
                color=col, alpha=0.15, zorder=2,
            )

        ax.axline((0, 0), slope=SY_ASSUMED[cid], color="gray",
                  lw=1.2, ls="--", label=f"Assumed Sy = {SY_ASSUMED[cid]:.2f}")

        ax.set_xlabel("Corrected water table rise Δh + β₃(h_prev + z)  (mm/month)")
        ax.set_ylabel("Net recharge P − PET  (mm/month)")
        ax.set_title(CLUSTER_LABELS[cid], fontweight="bold")
        ax.legend(fontsize=8, framealpha=0.9)
        ax.axhline(0, color="#CCCCCC", lw=0.8)
        ax.axvline(0, color="#CCCCCC", lw=0.8)
        ax.set_facecolor("#FAFAFA")
        ax.grid(True, lw=0.4, alpha=0.5)

        if not np.isnan(r["r2"]):
            ax.text(0.97, 0.07, f"R² = {r['r2']:.3f}",
                    transform=ax.transAxes, ha="right", fontsize=9,
                    color="black", style="italic")

    # Hide any unused axes (e.g. the 6th cell under k=5)
    for ax in axes[n_clusters:]:
        ax.set_visible(False)

    fig.suptitle(
        "Approach A — WTF apparent storage coefficient $S_a$: Drainage-Corrected OLS Regression\n"
        f"Newborough Warren {RECORD_FIT_START[:4]}–2026 (D-347)  |  Winter months (Nov–Mar, PET < 25 mm/month)\n"
        "Δh corrected for Model B drainage: Δh_corr = Δh + β₃·(h_prev + z), z = implied base (D-332)",
        fontsize=10, fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    render_figure(fig, out_path, facecolor="white")
    plt.close()
    print(f"Regression figure saved → {out_path.name}")


def plot_event_boxplot(b_results, out_path):
    """Figure: S_a distribution from Approach B event method (k=5 + forest-corrected)."""
    fig, ax = plt.subplots(figsize=(11, 5.9), facecolor="white")
    ax.set_facecolor("#FAFAFA")

    runs = _build_runs()
    positions = list(range(1, len(runs) + 1))
    rkeys = [_result_key(cid, corr) for cid, corr in runs]
    labels = [_entry_label(cid, corr) for cid, corr in runs]

    bp = ax.boxplot(
        [b_results[rk]["sy_values"] for rk in rkeys],
        positions=positions, widths=0.5, patch_artist=True,
        medianprops=dict(color="black", lw=2),
        whiskerprops=dict(lw=1.2), capprops=dict(lw=1.2),
        flierprops=dict(marker="o", markersize=3, alpha=0.4),
    )
    for patch, (cid, corrected) in zip(bp["boxes"], runs):
        patch.set_facecolor(CLUSTER_COLOURS[cid])
        patch.set_alpha(0.7)
        if corrected:
            patch.set_hatch("//")  # distinguish corrected variant

    # Add assumed-Sy markers — only for the uncorrected base clusters
    for pos, (cid, corrected) in zip(positions, runs):
        if not corrected:
            ax.scatter(pos + 0.3, SY_ASSUMED[cid],
                       marker="D", color="black", s=40, zorder=5,
                       label="Assumed Sy" if pos == 1 else "")

    for pos, rk in zip(positions, rkeys):
        med = b_results[rk]["sy_median"]
        if not np.isnan(med):
            ax.text(pos, med + 0.005, f"{med:.3f}",
                    ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Censored fraction per run, folded into the tick labels — the dominant term
    # behind the differing event counts, and invisible once the clipped values
    # are dropped from the boxes. Kept here rather than floating near the ceiling
    # so each figure ties to its own cluster and nothing collides with the legend.
    tick_labels = []
    for lab, rk in zip(labels, rkeys):
        # Three short HORIZONTAL lines — key / name / n + censored — rather than
        # one long tilted string. Tilted labels were hard to read and, kept
        # legible, forced a font small enough to trip the 160 mm legibility gate.
        corrected_run = " (corrected)" in lab
        base = lab.replace(" (corrected)", "")
        if " (" in base:
            head, rest = base.split(" (", 1)
            name = rest.partition(")")[0]
        else:
            head, name = base, ""
        if corrected_run:
            head += " (corr.)"
        pct = b_results[rk].get("pct_censored", np.nan)
        n_k = b_results[rk].get("n", 0)
        tail = ("" if (pct is None or np.isnan(pct))
                else f"\nn = {n_k} \u00b7 {pct:.0f}% cens.")
        tick_labels.append(f"{head}\n{name}{tail}")

    ax.set_xticks(positions)
    ax.set_xticklabels(tick_labels, fontsize=9, rotation=0, ha="center")
    ax.set_ylabel("Apparent storage coefficient $S_a$ (WTF); dashed: assumed specific yield Sy")
    # Raised from 0.45 so the plausibility ceiling is ON the axis (the clipped
    # boxes alone cannot show that 39-60% of qualifying events were censored),
    # and on to 0.70 so the legend sits in clear headroom ABOVE the ceiling
    # instead of clashing with the boxes.
    ax.set_ylim(0, 0.70)
    ax.axhline(0.50, color="#b3261e", lw=1.3, alpha=0.9,
               label="Plausibility ceiling = 0.50 (upper tail censored)")
    ax.axhline(0.12, color="gray", lw=1.0, ls=":", alpha=0.7,
               label="Assumed Sy non-C1 = 0.12")
    ax.axhline(0.08, color="gray", lw=1.0, ls="--", alpha=0.7,
               label="Assumed Sy C1 = 0.08")
    ax.legend(fontsize=9, framealpha=0.92, loc="upper left", ncol=2)
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    ax.set_title(
        "Approach B — WTF apparent storage coefficient $S_a$: Event-Based Estimates\n"
        "Monthly S_a from rising-limb events "
        f"(Δh > {WTF_EVENT_MIN_RISE_M * 1000:g} mm, net R > {WTF_EVENT_MIN_NET_RECH_M * 1000:g} mm, "
        f"{WTF_EVENT_SY_MIN:g} < S_a < {WTF_EVENT_SY_MAX:g})\n"
        f"Forest corrected: R = (1−{FOREST_INTERCEPTION:g})P − PET (Freeman, 2008); "
        "hatched boxes = interception-corrected",
        fontsize=10, fontweight="bold",
    )
    plt.tight_layout()
    render_figure(fig, out_path, facecolor="white")
    plt.close()
    print(f"Boxplot figure saved → {out_path.name}")


def export_csv(a_results, b_results, c_results, out_path):
    """Export summary CSV: one row per (cluster, corrected) entry.

    Approach A/B columns are unchanged. Approach C runs once per cluster, with the
    forest groups interception-corrected internally. 1.13.0 (D-349 (7), B5): its value is
    written on the row whose basis it shares - the open groups' (uncorrected) row, and the
    forest groups' Corrected=True row - so no row mixes bases; the forest groups'
    uncorrected rows carry NaN Approach C fields. Cluster_ID (appended) is the integer group id.
    """
    rows = []
    for cid, corrected in _build_runs():
        rkey = _result_key(cid, corrected)
        a = a_results[rkey]
        b = b_results[rkey]
        label = _entry_label(cid, corrected).replace(" (corrected)", " (corrected)")
        # Match the historical CSV-label suffix exactly: "<Label> (corrected)"
        # rather than the dropdown-friendly "(interception-corrected)".
        # Approach C is keyed by base cluster; attach it to the uncorrected row
        # only so the A/B corrected-forest rows stay exactly as before.
        # 1.13.0 (D-349 (7)): Approach C on the row of its own basis (corrected at the forest groups)
        c = c_results[cid] if corrected == bool(c_results[cid].get("corrected", False)) else None
        rows.append({
            "Cluster":               label,
            "Corrected":             corrected,
            "Sy_assumed":            SY_ASSUMED[cid],
            "Sy_OLS_winter":         a["sy"],
            "Sy_OLS_SE":             a["se"],
            "Sy_OLS_R2":             a["r2"],
            "Sy_OLS_n":              a["n"],
            # 1.10.0 (D-332): the Model B centroid drainage behind the Approach A correction
            "OLS_beta_3_model_b":    a.get("b3", np.nan),
            "OLS_alpha_model_b":     a.get("alpha", np.nan),
            "OLS_implied_datum_m":   a.get("implied_datum", np.nan),
            "Sy_event_median":       b["sy_median"],
            "Sy_event_Q25":          b["q25"],
            "Sy_event_Q75":          b["q75"],
            "Sy_event_n":            b["n"],
            "Sy_rapid_median":       c["sy_median"]     if c else np.nan,
            "Sy_rapid_CI_lo":        c["ci_lo"]         if c else np.nan,
            "Sy_rapid_CI_hi":        c["ci_hi"]         if c else np.nan,
            "Sy_rapid_n":            c["n"]             if c else np.nan,
            "Sy_rapid_mean_dur":     c["mean_duration"] if c else np.nan,
            "Sy_rapid_mean_rise_m":  c["mean_rise"]     if c else np.nan,
            # Selection funnel — appended after the historical columns so the
            # existing column order stays byte-stable for table_gen.
            "Sy_event_n_months":         b.get("n_months",  np.nan),
            "Sy_event_n_pass_R":         b.get("n_pass_R",  np.nan),
            "Sy_event_n_pass_dh":        b.get("n_pass_dh", np.nan),
            "Sy_event_n_qualifying":     b.get("n_both",    np.nan),
            "Sy_event_n_censored":       b.get("n_censored", np.nan),
            "Sy_event_pct_censored":     b.get("pct_censored", np.nan),
            "Sy_event_median_unclipped": b.get("sy_median_unclipped", np.nan),
            "Cluster_ID":                int(cid[1:]),   # 1.13.0 (D-349, rule 6): the group id, not read from a label
        })
    table = pd.DataFrame(rows)
    table.to_csv(out_path, index=False)
    print(f"CSV saved → {out_path.name}")
    return table


def write_report_numbers(table, out_path, excluded_datum=None, sweep=None, evidence=None):
    """T-96: the estimator comparisons report9 SS4.2.4 quotes, one row per
    cluster from the uncorrected rows of the S_a table. 1.13.0 (D-349 (7)): the
    rapid-event estimate sits on the forest groups' Corrected=True row, so at C4
    and C3f sy_estimator_range spans the two uncorrected estimators only.
    Then the sweep's robustness keys and the C3f-against-C3o evidence.
    Stored unrounded (D-035)."""
    rpt = ReportNumbers()
    base = table[~table["Corrected"].astype(bool)]
    est_cols = ["Sy_event_median", "Sy_OLS_winter", "Sy_rapid_median"]
    ratios = base["Sy_OLS_winter"] / base["Sy_event_median"]
    for (_, r), ratio in zip(base.iterrows(), ratios):
        lab = r["Cluster"]
        rpt.add("sy_event_clip_shift", float(r["Sy_event_median_unclipped"] - r["Sy_event_median"]),
                unit="", well=lab,
                note="Sy_event_median_unclipped minus Sy_event_median: the shift of the event median "
                     "when the plausibility ceiling is lifted (uncorrected run)")
        rpt.add("sy_ols_to_event_ratio", float(ratio), unit="", well=lab,
                note="Sy_OLS_winter / Sy_event_median (uncorrected run)")
        vals = r[est_cols].astype(float)
        rpt.add("sy_estimator_range", float(vals.max() - vals.min()), unit="", well=lab,
                note="max minus min of Sy_event_median, Sy_OLS_winter and Sy_rapid_median, uncorrected run; "
                     "at the forest groups the rapid-event estimate is on the Corrected=True row, so the range "
                     "spans the two uncorrected estimators (D-349 (7): one basis per row)")
    rpt.add("sy_ols_to_event_ratio_mean", float(ratios.mean()), unit="",
            note=f"mean of sy_ols_to_event_ratio over the n={len(ratios)} clusters (uncorrected run)")
    rpt.add("sy_ols_to_event_ratio_n_above_1", int((ratios > 1).sum()), unit="clusters",
            note=f"clusters whose Sy_OLS_winter exceeds Sy_event_median, of n={len(ratios)}")
    # 1.9.0 (emit-first, report9 SS4.2.4): event-selection funnel ranges across the clusters.
    # The event count and rise-criterion ranges span every run (the corrected forest rows
    # included), as the report sentence does; the rest span the uncorrected runs.
    n_all, n_base = len(table), len(base)
    sy_max = WTF_EVENT_SY_MAX
    for key, frame, col, how, unit, note in (
        ("sy_event_n_min", table, "Sy_event_n", "min", "events",
         f"fewest qualifying rising-limb events (Sy_event_n) in any cluster run, all n={n_all} runs "
         "including interception-corrected forest rows"),
        ("sy_event_n_max", table, "Sy_event_n", "max", "events",
         f"most qualifying rising-limb events (Sy_event_n) in any cluster run, all n={n_all} runs "
         "including interception-corrected forest rows"),
        ("sy_event_n_pass_r_min", base, "Sy_event_n_pass_R", "min", "months",
         f"fewest months meeting the net-recharge criterion (Sy_event_n_pass_R), n={n_base} uncorrected clusters"),
        ("sy_event_n_pass_r_max", base, "Sy_event_n_pass_R", "max", "months",
         f"most months meeting the net-recharge criterion (Sy_event_n_pass_R), n={n_base} uncorrected clusters"),
        ("sy_event_n_pass_dh_min", table, "Sy_event_n_pass_dh", "min", "months",
         f"fewest months meeting the water-table rise criterion (Sy_event_n_pass_dh), all n={n_all} runs"),
        ("sy_event_n_pass_dh_max", table, "Sy_event_n_pass_dh", "max", "months",
         f"most months meeting the water-table rise criterion (Sy_event_n_pass_dh), all n={n_all} runs"),
        ("sy_event_pct_censored_min", base, "Sy_event_pct_censored", "min", "%",
         f"lowest percent of months clearing both criteria censored by the S_a ceiling {sy_max} "
         f"(Sy_event_pct_censored), n={n_base} uncorrected clusters"),
        ("sy_event_median_unclipped_min", base, "Sy_event_median_unclipped", "min", "",
         f"lowest event-median S_a with the ceiling lifted (Sy_event_median_unclipped), "
         f"n={n_base} uncorrected clusters"),
    ):
        rpt.add(key, float(getattr(frame[col].astype(float), how)()), unit=unit, note=note)
    # 1.10.0 (D-332): clusters with no Approach A value because Model B's implied base is not below ground
    excl = excluded_datum or {}
    rpt.add("wtf_a_n_clusters_model_b_excluded_datum", len(excl), unit="clusters",
            note="clusters with no Approach A S_a: Model B centroid implied base DRAINAGE_DATUM - alpha/beta_3 "
                 "not below ground (D-332)" + (" (" + ", ".join(f"C{c} {v:+.2f} m" for c, v in
                                                                 sorted(excl.items())) + ")" if excl else ""))
    # 1.13.0 (D-349 (7), B5): the sweep is a robustness check, stated as one; the evidence is C3f against C3o
    if sweep is not None and len(sweep):
        for i in FOREST_CIDS:
            cid = f"C{i}"
            sw = sweep[sweep["cluster"] == cid]
            if sw.empty:
                continue
            inside = sw[sw["within_open_dune_range"].astype(bool)]
            at0 = sw[np.isclose(sw["F"], 0.0)]
            rpt.add("sy_sweep_inside_at_F0", int(bool(len(at0)) and bool(at0["within_open_dune_range"].iloc[0])),
                    unit="flag", well=cid,
                    note="1 = the uncorrected (F = 0) event-median S_a already lies inside the open-dune range, so the "
                         "interception sweep cannot discriminate between fractions here; the sweep is a robustness "
                         "check, not a test (D-349 (7))")
            rpt.add("sy_sweep_n_inside", len(inside), unit="grid points", well=cid,
                    note=f"interception fractions of the {len(sw)}-point sweep grid at which the event-median S_a "
                         "lies inside the open-dune range (robustness check, D-349 (7))")
            if len(inside):
                rpt.add("sy_sweep_F_inside_min", float(inside["F"].min()), unit="", well=cid,
                        note="smallest grid F with the event-median S_a inside the open-dune range")
                rpt.add("sy_sweep_F_inside_max", float(inside["F"].max()), unit="", well=cid,
                        note="largest grid F with the event-median S_a inside the open-dune range")
    for ev in (evidence or []):
        pair = f"{ev['forest_key']}_vs_{ev['open_key']}"
        _src = (f"{CLUSTER_LABELS[ev['forest_key']]} against {CLUSTER_LABELS[ev['open_key']]}, the same "
                "hydrogeological cluster under the other cover (D-349 (7))")
        rpt.add("sy_unclipped_forest_uncorrected", ev["sy_unclipped_forest_uncorrected"], unit="", well=pair,
                note=f"unclipped event-median S_a of the forest group, uncorrected; {_src}")
        rpt.add("sy_unclipped_forest_corrected", ev["sy_unclipped_forest_corrected"], unit="", well=pair,
                note=f"unclipped event-median S_a of the forest group, corrected at F = {FOREST_INTERCEPTION:g}; "
                     f"{_src}")
        rpt.add("sy_unclipped_open", ev["sy_unclipped_open"], unit="", well=pair,
                note=f"unclipped event-median S_a of the open group; {_src}")
        rpt.add("sy_unclipped_ratio_open_to_forest_uncorrected",
                ev["sy_unclipped_open"] / ev["sy_unclipped_forest_uncorrected"]
                if ev["sy_unclipped_forest_uncorrected"] else np.nan, unit="", well=pair,
                note=f"open over uncorrected forest unclipped event-median S_a; {_src}")
        rpt.add("sy_unclipped_F_match", ev["F_match_unclipped"], unit="", well=pair,
                note="interception fraction at which the forest group's unclipped event-median S_a equals the "
                     f"open group's (interpolated on the sweep grid; NaN if not bracketed); {_src}")
        rpt.add("beta_1_ratio_forest_to_open", ev["beta_1_ratio"], unit="", well=pair,
                note="centroid beta_1 (03_03, Model B) of the forest group over the open group's: if interception "
                     "sits in recharge, a fit on gross rain absorbs it as (1 - F) beta_1; beta_1 also scales with "
                     f"1/S_a, so suggestive, not diagnostic; {_src}")
    n_saved = rpt.save(out_path)
    saved(f"{out_path.name} ({n_saved} rows)")


def write_summary(a_results, b_results, c_results, out_path, df=None, sweep=None, evidence=None):
    """Plain-text summary for manuscript."""
    _span = (f"{df['Date'].min():%Y-%m} to {df['Date'].max():%Y-%m} (D-347)" if df is not None and len(df)
             else f"from {RECORD_FIT_START[:7]} (D-347)")
    lines = [
        "=" * 70,
        "SPECIFIC YIELD ESTIMATION — WATER TABLE FLUCTUATION METHOD",
        f"Newborough Warren, {_span}",
        "=" * 70,
        "",
        "Method: Healy and Cook (2002)",
        "  S_a = R / dh",
        "  R = net recharge (P - PET, winter months Nov-Mar, PET < 25 mm/month)",
        "  dh = corresponding water table rise",
        "",
        "APPROACH A — OLS Regression (winter months, origin-forced)",
        "-" * 70,
    ]
    # Approach A: uncorrected clusters only
    for cid in [f"C{i}" for i in CLUSTER_IDS]:
        a = a_results[cid]
        sy_s = f"{a['sy']:.3f}"   if not np.isnan(a['sy'])   else "  n/a"
        se_s = f"±{a['se']:.4f}"  if not np.isnan(a['se'])   else "       "
        r2_s = f"{a['r2']:.3f}"   if not np.isnan(a['r2'])   else "  n/a"
        n_s  = f"{int(a['n'])}"   if not np.isnan(a['n'])    else " n/a"
        lines.append(
            f"  {CLUSTER_LABELS[cid]:<32}  S_a = {sy_s}  "
            f"{se_s} (SE)  R² = {r2_s}  n = {n_s}"
        )

    lines += [
        "",
        "APPROACH B — Event Median (rising limb months)",
        "-" * 70,
    ]
    for cid, corrected in _build_runs():
        rkey = _result_key(cid, corrected)
        b = b_results[rkey]
        label = _entry_label(cid, corrected)
        suffix = (f"   [Freeman 2008; R_eff = (1 − {FOREST_INTERCEPTION:g})·P − PET]"
                  if corrected else "")
        lines.append(
            f"  {label:<32}  S_a = {b['sy_median']:.3f}  "
            f"IQR [{b['q25']:.3f}, {b['q75']:.3f}]  n = {b['n']}{suffix}"
        )

    lines += [
        "",
        "APPROACH C — Rapid Recharge Events (Crosbie et al., 2005)",
        "-" * 70,
        f"  Episode: >= {WTF_C_DRY_BASELINE} mo of dh <= 0 baseline, then rise",
        f"  >= {WTF_C_MIN_RISE_M*1000:.0f} mm over <= {WTF_C_MAX_DURATION} mo; "
        f"per-episode S_a in [{WTF_C_SY_MIN:.2f}, {WTF_C_SY_MAX:.2f}].",
        f"  Cluster S_a = median of episode Sy_i, 95% CI from "
        f"{WTF_C_BOOTSTRAP_N} bootstraps.",
        "",
    ]
    for cid in [f"C{i}" for i in CLUSTER_IDS]:
        c = c_results[cid]
        corr_s = "   [interception-corrected]" if c["corrected"] else ""
        if c["n"] == 0 or np.isnan(c["sy_median"]):
            lines.append(f"  {CLUSTER_LABELS[cid]:<32}  no qualifying episodes{corr_s}")
            continue
        ci_s = (f"[{c['ci_lo']:.3f}, {c['ci_hi']:.3f}]"
                if np.isfinite(c["ci_lo"]) else "[n/a — single episode]")
        caveat = "   <-- data-limited (small n)" if c["n"] < 5 else ""
        lines.append(
            f"  {CLUSTER_LABELS[cid]:<32}  S_a = {c['sy_median']:.3f}  "
            f"95% CI {ci_s}  n = {c['n']}{corr_s}{caveat}"
        )

    lines += [
        "",
        "COMPARISON WITH ASSUMED VALUES",
        "-" * 70,
        f"  {'Cluster':<33} {'Assumed':>8}  {'OLS':>8}  {'Event':>8}  {'Rapid':>8}",
    ]
    for cid, corrected in _build_runs():
        rkey = _result_key(cid, corrected)
        a = a_results[rkey]; b = b_results[rkey]
        label = _entry_label(cid, corrected)
        ols_s = f"{a['sy']:.3f}" if not np.isnan(a['sy']) else "n/a"
        # 1.13.0 (D-349 (7)): Approach C attaches to the row of its own basis (corrected at the forest groups).
        c = c_results[cid] if corrected == bool(c_results[cid].get("corrected", False)) else None
        if c and not np.isnan(c["sy_median"]):
            rap_s = f"{c['sy_median']:.3f}"
        elif c:
            rap_s = "n/a"
        else:
            rap_s = "-"
        lines.append(
            f"  {label:<33} {SY_ASSUMED[cid]:>8.3f}  "
            f"{ols_s:>8}  {b['sy_median']:>8.3f}  {rap_s:>8}"
        )

    # 1.13.0 (D-349 (7), B5): the sweep stated as a robustness check; the evidence is C3f against C3o
    lines += ["", "INTERCEPTION — ROBUSTNESS CHECK AND EVIDENCE (D-349 (7))", "-" * 70]
    if sweep is not None and len(sweep):
        lo, hi = float(sweep["open_dune_min"].iloc[0]), float(sweep["open_dune_max"].iloc[0])
        lines.append(f"  Open-dune range of event-median S_a (uncorrected, open groups): [{lo:.3f}, {hi:.3f}]")
        for i in FOREST_CIDS:
            cid = f"C{i}"
            sw = sweep[sweep["cluster"] == cid]
            if sw.empty:
                continue
            ins = sw[sw["within_open_dune_range"].astype(bool)]
            at0 = sw[np.isclose(sw["F"], 0.0)]
            in0 = bool(len(at0)) and bool(at0["within_open_dune_range"].iloc[0])
            span = (f"inside at {len(ins)} of {len(sw)} grid F in [{ins['F'].min():.2f}, {ins['F'].max():.2f}]"
                    if len(ins) else "never inside")
            lines.append(f"  {CLUSTER_LABELS[cid]:<32}  {span}; "
                         + ("inside with NO correction (F = 0)" if in0 else "outside at F = 0"))
        lines += ["  The sweep is a robustness check, not a test: the range is wide and the 0.50 ceiling",
                  "  holds the clipped medians in it, so it cannot discriminate between interception",
                  "  fractions. It shows the forest groups' convergence does not depend on F."]
    for ev in (evidence or []):
        fl, ol = CLUSTER_LABELS[ev["forest_key"]], CLUSTER_LABELS[ev["open_key"]]
        fm = (f"{ev['F_match_unclipped']:.3f}" if np.isfinite(ev["F_match_unclipped"]) else "not bracketed")
        lines += [f"  Evidence: {fl} against {ol} (same cluster, other cover)",
                  f"    unclipped event-median S_a: {ev['sy_unclipped_forest_uncorrected']:.3f} uncorrected, "
                  f"{ev['sy_unclipped_forest_corrected']:.3f} corrected, against {ev['sy_unclipped_open']:.3f};",
                  f"    the two are equal at F = {fm};",
                  f"    centroid beta_1 ratio (03_03) {ev['beta_1_ratio']:.3f}, against 1 - F = "
                  f"{1 - FOREST_INTERCEPTION:.3f} (suggestive: beta_1 also scales with 1/S_a)."]

    lines += [
        "",
        "NOTES",
        "-" * 70,
        "- Monthly resolution means individual storm events cannot be isolated.",
        "- Winter OLS (Approach A) is most defensible: PET negligible so",
        "  net recharge approximates actual recharge well.",
        "- Event method (Approach B) is noisier but provides uncertainty bounds.",
        "- Rapid-event method (Approach C, Crosbie et al. 2005) is a third,",
        "  methodologically independent estimator: it selects short, sharply-",
        "  rising episodes following a drainage baseline, so drainage during the",
        "  rise is negligible by construction and no beta_3 correction is needed.",
        "  A<->C convergence validates the Approach A drainage correction;",
        "  divergence is diagnostic. Approach C is a reported triangulation only",
        "  and does NOT propagate downstream (Approach B per-well S_a remains the",
        "  pipeline-consumed canonical). It is data-limited at the forest",
        "  clusters (small n) and reported there with n and CI shown.",
        "- Forest groups (C4 Main Forest, C3f Western Dune forest) are reported as",
        "  both uncorrected and interception-corrected (Freeman 2008) variants.",
        f"  The corrected variant applies R_effective = (1 − {FOREST_INTERCEPTION:g})·P − PET. PET",
        "  is not reduced because Thornthwaite PET is an energy-based atmospheric",
        "  demand (independent of land cover), so reducing only P is physically",
        "  motivated and not double-counting.",
        "- Approach C's forest values are interception-corrected and sit on the",
        "  corrected rows (D-349 (7)).",
        "- Approach A corrected variants are not fitted in this version (the",
        "  corrected fits were unstable; the report uses Approach B for the",
        "  corrected forest values populating Table 3c).",
        "- The corrected forest event pool is typically larger than the",
        "  uncorrected pool because reducing P brings previously-excluded high",
        "  events (S_a > 0.50) into the admissible range.",
        "- Both approaches give indicative S_a only; slug tests or pumping tests",
        "  at representative wells per cluster remain the gold standard.",
        "- Reference: Healy, R.W. and Cook, P.G. (2002) Hydrogeology Journal",
        "  10, 91-109. doi:10.1007/s10040-001-0178-0",
        "- Reference: Crosbie, R.S., Binning, P. and Kalma, J.D. (2005)",
        "  Water Resources Research 41(1), W01008. doi:10.1029/2004WR003077",
        "",
    ]

    out_path.write_text("\n".join(lines))
    print(f"Summary saved → {out_path.name}")


def main():
    # ── Paths ──────────────────────────────────────────────────────────────
    banner("17", "WTF apparent storage coefficient (S_a)", version=__version__)
    out_root     = OUT_DIR
    out_dir      = DIR_17
    path_table   = OUT_17_SY_TABLE
    path_reg     = OUT_17_REGRESSION
    path_box     = OUT_17_BOXPLOT
    path_summary = OUT_17_SUMMARY
    path_rapid   = OUT_17_RAPID_EVENTS

    # ── Run ────────────────────────────────────────────────────────────────
    print("Loading data...")
    df = load_data(out_root)
    print(f"  {len(df)} monthly records, "
          f"{df['Date'].min().date()} to {df['Date'].max().date()}")
    print(f"  Partition: k={len(CLUSTER_IDS)} "
          f"({', '.join(CLUSTER_LABELS[k] for k in CLUSTER_LABELS)})")
    print(f"  Forest clusters (interception-corrected): "
          f"{', '.join(CLUSTER_LABELS[k] for k in FOREST_KEYS)}")

    print("\nApproach A — OLS regression (winter months, drainage-corrected):")
    a_results, a_excluded_datum = approach_a_ols(df)

    print("\nApproach B — Event-based median:")
    b_results = approach_b_events(df)

    print("\nApproach C — Rapid recharge events (Crosbie et al., 2005):")
    c_results = approach_c_rapid_events(df)

    print("\nApproach B sensitivity — interception-fraction sweep:")
    sweep = approach_b_interception_sweep(df, b_results)

    print("\nGenerating figures...")
    plot_regression(df, a_results, path_reg)
    plot_event_boxplot(b_results, path_box)
    plot_rapid_events(c_results, path_rapid)

    print("\nExporting outputs...")
    sy_table = export_csv(a_results, b_results, c_results, path_table)
    print("\nInterception evidence — forest group against the open group of its cluster (D-349 (7)):")
    evidence = interception_evidence(b_results, sweep)
    write_report_numbers(sy_table, OUT_17_REPORT_NUMBERS, excluded_datum=a_excluded_datum,
                         sweep=sweep, evidence=evidence)
    sweep.to_csv(OUT_17_INTERCEPTION_SWEEP, index=False)   # full precision (D-035)
    saved(OUT_17_INTERCEPTION_SWEEP)
    write_summary(a_results, b_results, c_results, path_summary, df=df, sweep=sweep, evidence=evidence)

    print("\nAll outputs written to", out_dir)


if __name__ == '__main__':
    main()
