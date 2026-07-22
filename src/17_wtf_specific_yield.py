"""
17_wtf_specific_yield.py
========================
Water Table Fluctuation (WTF) Method — Cluster-Level Specific Yield Estimation
Newborough Warren Coastal Sand Dune Aquifer, 2005–2026

Produces cluster-level WTF Sy estimates (Approaches A and B) for all clusters
in the live partition. Forest clusters (FOREST_CIDS from config — C4 and C5)
additionally receive an interception-corrected variant following Freeman (2008),
applied to Approach B only. The corrected forest values populate Table 3c of
the manuscript and feed the WTF-Sy volumetric water balance (Table 3d,
Figure 8b).

Individual well-level WTF analysis and spatial mapping are in script 18.

Outputs:
    17_wtf_01_sy_estimates.csv   — cluster Sy estimates, inc. forest corrected rows
    17_wtf_02_regression.png     — OLS regression plots for Approach A
    17_wtf_03_event_boxplot.png  — Sy distribution plots for Approach B
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

__version__ = "1.4.0"  # Hollingham (2026) — last revised 2026-07-22
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
# Changelog:
#   1.4.0 (2026-07-22) — Approach C revival (rapid-recharge-event method).
#     A third, methodologically independent Sy estimator added alongside
#     Approach A (drainage-corrected OLS) and Approach B (naïve event median),
#     reviving the 2026-06-11 prototype for reviewer-audit item B4. Approach C
#     identifies rapid recharge episodes by *selection*: a candidate episode
#     requires WTF_C_DRY_BASELINE consecutive prior months of Δh ≤ 0 (drainage-
#     only quasi-steady state), starts on the first month with Δh > 0, runs
#     until Δh ≤ 0 or the WTF_C_MAX_DURATION cap, and must accumulate a
#     cumulative head rise ≥ WTF_C_MIN_RISE_M. Per episode
#     Sy_i = Σ net_R[s..e] / (h[e] − h[s−1]); the cluster Sy is the median of
#     valid Sy_i (physical filter [WTF_C_SY_MIN, WTF_C_SY_MAX]) with a
#     WTF_C_BOOTSTRAP_N-resample 95 % CI on the median (seed
#     WTF_RAPID_BOOT_SEED). Forest clusters (FOREST_CIDS) use the Freeman
#     (2008) interception-corrected recharge net_R_forest_corr, matching
#     Approach B. The motivation is selection-based bias control rather than
#     mechanistic correction: short, well-isolated episodes have small
#     drainage during the rise by construction, so the naïve R/Δh formula is
#     approximately valid without the β₃ correction Approach A applies.
#     A↔C convergence validates the β₃ correction; divergence is diagnostic
#     of where β₃ may over- or under-state drainage. Approach C is data-
#     limited at the forest clusters (n small); it is reported with n and CI
#     shown and an explicit small-sample caveat rather than hidden.
#     IMPORTANT — Approach C is a *reported* triangulation only. It does NOT
#     propagate to any other pipeline script. The event-based per-well Sy
#     (Approach B lineage, Script 18 → 17_wtf_well_sy.csv, consumed by
#     09d/20/29/30/31/37b) remains the pipeline-consumed canonical. The only
#     downstream quantity that consumes an absolute Sy — the Figure 17 reach
#     λ = √(Kb/(Sy·β₃)) — and the Script 21 scenarios are therefore
#     undisturbed. (The storage–drainage index Sy/β₃ is a diagnostic, not a
#     used quantity; the residence time 1/β₃ is Sy-free.)
#     Edits:
#       (a) New config constants WTF_C_DRY_BASELINE, WTF_C_MIN_RISE_M,
#           WTF_C_MAX_DURATION, WTF_C_SY_MIN, WTF_C_SY_MAX, WTF_C_BOOTSTRAP_N,
#           WTF_RAPID_BOOT_SEED (config.py — no hardcoded thresholds).
#       (b) New function approach_c_rapid_events(df) returning a per-cluster
#           dict: sy_median, ci_lo, ci_hi, n, mean_duration, mean_rise,
#           episodes (DataFrame of qualifying episodes).
#       (c) main() calls approach_c_rapid_events after approach_b_events and
#           renders a new figure 17_wtf_05_rapid_events.png (OUT_17_RAPID_EVENTS).
#       (d) export_csv signature extended to (a, b, c, out_path); six new
#           columns Sy_rapid_median, Sy_rapid_CI_lo, Sy_rapid_CI_hi,
#           Sy_rapid_n, Sy_rapid_mean_dur, Sy_rapid_mean_rise_m. Approach A/B
#           columns are unchanged and byte-stable.
#       (e) write_summary signature extended; new APPROACH C section plus a
#           third column in the COMPARISON table.
#     Built on current main (v1.3.0, Defect D inversion fix) — NOT on the
#     prototype's v1.2.0 base. Prototype Sy figures (~0.32 C3, ~0.21 C1) were
#     reproduction checks only; reported values are whatever the live run
#     yields. References: Crosbie, R.S., Binning, P. & Kalma, J.D. (2005)
#     Water Resources Research 41(1), W01008, doi:10.1029/2004WR003077;
#     Healy & Cook (2002) Hydrogeology Journal 10, 91-109.
#   1.2.0 (2026-05-17) — Approach A Sy inversion fix (Defect D).
#     The OLS-through-origin slope for the regression R = Sy · Δh_corr IS Sy
#     directly, not 1/Sy. v1.1.0 and earlier stored Sy = 1/slope, returning
#     Sy = 2.4–3.4 (physically impossible — Sy ≤ 1 by definition). Diagnosis
#     in DEFECT_D_INVESTIGATION.md; cross-check 1/Sy_A_v1.1.0 ≈ Sy_B confirmed
#     the inversion. Five matched edits:
#       (a) `Sy = 1.0/slope` → `Sy = slope` in approach_a_ols.
#       (b) Delta-method SE collapses to SE(slope) directly.
#       (c) R² changed from centred form (which produces spurious negative
#           values for through-origin OLS) to uncentred form
#           1 − SS_res/Σy², appropriate for no-intercept regression.
#       (d) plot_regression: WTF line drawn as `xline * Sy` not
#           `xline / Sy`; the assumed-Sy reference axline now uses
#           `slope=SY_ASSUMED[cid]` not `1/SY_ASSUMED[cid]`.
#       (e) Docstring's "recovers Sy as the inverse of the slope" replaced
#           with "recovers Sy as the slope".
#     Soft warning added if Approach A's Sy is outside (0, 1) on a future run.
#     Downstream effects: Approach A columns in 17_wtf_01_sy_estimates.csv
#     regenerate (C1 0.334, C2 0.333, C3 0.342, C4 0.298, C5 0.410); the
#     figure regenerates; Approach B and all per-well outputs are
#     unchanged; no other pipeline scripts consume Approach A so no
#     downstream reruns required. Methods Supplement §S.12 line 2119
#     needs the same wording fix in chapter prose.
#   1.1.0 (2026-05-15) — k=5 partition support and column-name fix.
#     Brings the committed script into agreement with the live committed
#     output CSV, which was produced by an uncommitted hot-patched version
#     under k=5 with both forest clusters corrected. Defects B, C, A from
#     CHAPTER_FLAGS_TO_REVIEW.md (S.12 chapter audit) are addressed.
#       (a) Cluster iteration is now dynamic across config.CLUSTER_LABELS
#           (currently k=5: C1, C2, C3, C4, C5). The previous hard-coded
#           four-cluster lists in approach_a_ols, approach_b_events,
#           plot_regression, plot_event_boxplot, export_csv, write_summary
#           were the root cause: a fresh run from main produced k=4 output
#           that did not match the report.
#       (b) Interception correction is now applied to all clusters in
#           config.FOREST_CIDS (currently C4 and C5), not just C4.
#           Approach A's corrected entries are deliberately left as NaN
#           in the CSV — corrected fits at forest clusters were unstable
#           in the previous internal hot-patched version and the report
#           uses Approach B for the corrected values.
#       (c) Master-data column rename from `beta_3_internal_brake` to
#           `beta_3_drainage`, completing the 26 April 2026 sweep across
#           Scripts 17, 19, 20, 21 (Script 17 was missed at the time).
#           The defensive `except` block that previously swallowed the
#           KeyError silently and ran Approach A with uncorrected Δh
#           has been kept but is no longer expected to fire.
#       (d) CLUSTER_LABELS and CLUSTER_COLOURS now imported from
#           utils.config (authoritative per F.4 of the Methods Supplement);
#           local label and colour dicts removed. config keys are integer
#           cluster IDs (1–5); the script bridges to the DataFrame's
#           "C1"–"C5" column convention via _cid_label(i) -> "C" + str(i).
#       (e) Approach A is left structurally unchanged — Defect D in the
#           audit (Sy values of 2.4–3.4 with negative R² in the live
#           output) may resolve after this commit lands, since the
#           uncorrected-Δh fallback that defect C silently triggered is
#           no longer in play. A diagnostic pass is recommended after a
#           fresh run; if Approach A is still broken, the regression
#           form itself needs revisiting (separately from this commit).
#       (f) `sys.path.insert` now points at the script's parent so the
#           `utils` package imports work when the script is invoked
#           standalone; previous form pointed at `src/utils` which only
#           worked when the script was launched from the repo root via
#           run_analysis.py.
#   1.0.0 — Initial pipeline release. Hard-coded k=4 cluster list; applied
#           interception correction to C4 only; read master coefficients
#           under the pre-rename column name `beta_3_internal_brake`.

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

import pandas as pd
import numpy as np
import matplotlib

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils.config import (
    CLUSTER_LABELS as _CFG_CLUSTER_LABELS,
    CLUSTER_COLOURS as _CFG_CLUSTER_COLOURS,
    FOREST_CIDS,
    FOREST_INTERCEPTION,
    WTF_C_DRY_BASELINE, WTF_C_MIN_RISE_M, WTF_C_MAX_DURATION,
    WTF_C_SY_MIN, WTF_C_SY_MAX, WTF_C_BOOTSTRAP_N, WTF_RAPID_BOOT_SEED,
)
from utils.paths import (
    make_all_dirs, OUT_DIR, DIR_17, INT_MASTER_DATA, OUT_17_SY_TABLE,
    OUT_17_REGRESSION, OUT_17_BOXPLOT, OUT_17_SUMMARY, OUT_17_RAPID_EVENTS,
)
from utils.render_utils import render_figure
make_all_dirs()

# ── Constants ──────────────────────────────────────────────────────────────────
WINTER_MONTHS   = [11, 12, 1, 2, 3]    # Nov–Mar: PET negligible
PET_MAX_WINTER  = 0.025                 # m/month — exclude months above this
MIN_RISE_M      = 0.005                 # minimum detectable water table rise (m)
MIN_NET_RECH    = 0.010                 # minimum net recharge for event method (m)

# Canopy interception fraction — Freeman (2008), site-specific to Newborough
# Corsican pine. Imported from config.py (authoritative per F.4 of the Methods
# Supplement). Applied to all clusters in FOREST_CIDS: R_eff = (1 − 0.24)·P − PET.
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
FOREST_KEYS     = [f"C{i}" for i in FOREST_CIDS]  # ["C4", "C5"]

# Assumed Sy for comparison (literature defaults for coastal sand). C1's lower
# value reflects the lake-buffered cluster's higher fines content; the other
# clusters take the conventional sand value. Values are illustrative comparators,
# not inputs to the WTF calculation itself.
SY_ASSUMED = {f"C{i}": (0.08 if i == 1 else 0.12) for i in CLUSTER_IDS}

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
})


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

    return df


def approach_a_ols(df):
    """
    Approach A: Corrected WTF regression accounting for storage decay.

    The observed Δh reflects both recharge and drainage:
        Δh = (R / Sy) − β₃·|h_prev|

    Rearranging:
        R = Sy · (Δh + β₃·|h_prev|)
    so OLS regression of R against (Δh + β₃·|h_prev|) through the origin
    recovers Sy as the slope itself (R is the dependent variable,
    Δh + β₃·|h_prev| is the independent variable). β₃ is the cluster-median
    drainage coefficient from the SSM master table (Script 03).

    R² is reported in the uncentred (no-intercept) form 1 − SS_res / Σy²,
    appropriate for regression through the origin. The standard centred R²
    can return spurious negative values for through-origin fits because it
    compares against the mean of y rather than zero; that artefact (and the
    inverted Sy storage that compounded it) was the v1.1.0 → v1.2.0 fix.

    Approach A is fitted on uncorrected clusters only. Corrected-forest
    variants (Approach B only) are populated separately in approach_b_events.
    """
    # Load cluster-median β₃ from the SSM master table. The defensive except
    # is retained from v1.0.0 — under v1.1.0 the column name `beta_3_drainage`
    # is current and the except block should not fire on a healthy main; if it
    # ever does, Approach A falls back to uncorrected Δh with a console warning.
    try:
        master = pd.read_csv(INT_MASTER_DATA)
        b3 = master.groupby("Cluster")["beta_3_drainage"].median()
        beta3 = {i: abs(b3[i]) for i in CLUSTER_IDS if i in b3.index}
    except Exception as e:
        warn(f"Could not load β₃ values ({type(e).__name__}: {e}) — using uncorrected Δh")
        beta3 = None

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

        sub = winter[["net_R", f"dh_{cid}", cid]].dropna()
        sub = sub[sub["net_R"] > 0]

        if len(sub) < 10:
            results[rkey] = dict(sy=np.nan, r2=np.nan, n=len(sub), se=np.nan)
            continue

        # Correct Δh for drainage: Δh_corrected = Δh + β₃·|h_prev|
        cid_int = int(cid[1:])
        if beta3 is not None and cid_int in beta3:
            b3_val = beta3[cid_int]
            dh_corrected = sub[f"dh_{cid}"] + b3_val * sub[cid].abs()
        else:
            b3_val = None
            dh_corrected = sub[f"dh_{cid}"]

        # Only use months where corrected Δh is positive (net recharge signal)
        mask = dh_corrected > MIN_RISE_M
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
            print(f"  [WARNING] {CLUSTER_LABELS[cid]} Approach A Sy = {Sy:.3f} "
                  "is outside the physical range (0, 1). "
                  "Regression may be misspecified.")

        results[rkey] = dict(
            sy=round(Sy, 4), r2=round(r2, 3), n=n,
            se=round(se_sy, 4), data=sub,
            dh_corrected=dh_corrected[mask],
            b3=b3_val,
        )
        b3_str = f"{b3_val:.3f}" if b3_val is not None else "n/a"
        print(f"  {CLUSTER_LABELS[cid]:<32}  Sy = {Sy:.3f}  R² = {r2:.3f}  "
              f"n = {n}  SE = {se_sy:.4f}  β₃ = {b3_str}")

    # Forest corrected entries: NaN placeholders. The corrected fits were
    # unstable in the previous internal version and the report uses Approach B
    # for the corrected forest values. Keeping NaN entries here lets the CSV
    # export and summary writer iterate the same run plan as Approach B.
    for cid in FOREST_KEYS:
        results[f"{cid}_corr"] = dict(sy=np.nan, r2=np.nan, n=np.nan,
                                      se=np.nan)

    return results


def approach_b_events(df):
    """
    Approach B: Event-based median Sy from rising limb months.
    Sy_i = net_R / Δh for months where Δh > MIN_RISE and net_R > MIN_NET_RECH.

    Run for every cluster (uncorrected) and additionally for FOREST_CIDS
    clusters with the Freeman (2008) interception correction applied.
    """
    results = {}
    for cid, corrected in _build_runs():
        rkey = _result_key(cid, corrected)
        r_col = "net_R_forest_corr" if corrected else "net_R"

        if f"dh_{cid}" not in df.columns:
            results[rkey] = dict(sy_median=np.nan, q25=np.nan, q75=np.nan,
                                 n=0, sy_values=np.array([]))
            continue

        sub = df[[r_col, f"dh_{cid}"]].dropna().copy()
        events = sub[
            (sub[r_col]      > MIN_NET_RECH) &
            (sub[f"dh_{cid}"] > MIN_RISE_M)
        ].copy()
        events["sy_i"] = events[r_col] / events[f"dh_{cid}"]
        # Drop physically implausible Sy values
        events = events[(events["sy_i"] > 0.01) & (events["sy_i"] < 0.50)]

        med = events["sy_i"].median()
        q25 = events["sy_i"].quantile(0.25)
        q75 = events["sy_i"].quantile(0.75)
        n   = len(events)

        results[rkey] = dict(
            sy_median=round(med, 4), q25=round(q25, 4), q75=round(q75, 4),
            n=n, sy_values=events["sy_i"].values,
        )
        print(f"  {_entry_label(cid, corrected):<32}  Sy median = {med:.3f}  "
              f"IQR [{q25:.3f}, {q75:.3f}]  n = {n}")

    return results


def approach_c_rapid_events(df):
    """
    Approach C: rapid-recharge-event Sy after Crosbie et al. (2005).

    Independent of Approaches A and B by construction. Where A corrects for
    drainage mechanistically (β₃) and B applies no correction (bias-low), C
    *selects* episodes in which the drainage contribution to the observed rise
    is negligible: short, sharply-rising events that follow a multi-month
    drainage baseline, so the naïve Sy = ΣR / Δh is approximately unbiased
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
    other pipeline script (the Approach B per-well Sy in Script 18 remains the
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
                        "rise_m":    round(rise, 4),
                        "recharge_m": round(recharge, 4),
                        "sy_i":      round(sy_i, 4),
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
            sy_median=round(med, 4),
            ci_lo=round(float(ci_lo), 4) if np.isfinite(ci_lo) else np.nan,
            ci_hi=round(float(ci_hi), 4) if np.isfinite(ci_hi) else np.nan,
            n=n,
            mean_duration=round(float(ep_df["duration"].mean()), 2),
            mean_rise=round(float(ep_df["rise_m"].mean()), 4),
            corrected=corrected,
            episodes=ep_df,
        )
        ci_s = (f"[{ci_lo:.3f}, {ci_hi:.3f}]" if np.isfinite(ci_lo)
                else "[n/a — single episode]")
        corr_s = "  (interception-corrected)" if corrected else ""
        print(f"  {CLUSTER_LABELS[cid]:<32}  Sy = {med:.3f}  95% CI {ci_s}  "
              f"n = {n}{corr_s}")

    return results


def plot_rapid_events(c_results, out_path):
    """Figure: Approach C rapid-recharge-event Sy per cluster (median + CI + n)."""
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
    ax.set_ylabel("Specific yield Sy  (dimensionless)")
    ax.set_ylim(0, 0.55)
    ax.axhline(0.12, color="gray", lw=1.0, ls=":", alpha=0.7,
               label="Assumed Sy non-C1 = 0.12")
    ax.axhline(0.08, color="gray", lw=1.0, ls="--", alpha=0.7,
               label="Assumed Sy C1 = 0.08")
    ax.legend(fontsize=8.5, framealpha=0.9, loc="upper left")
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    ax.set_title(
        "Approach C — WTF Specific Yield: Rapid-Recharge-Event Method\n"
        "Cluster median with 95% bootstrap CI; faint points = per-episode Sy\n"
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
                    label=f"WTF: Sy = {r['sy']:.3f} ± {r['se']:.3f}")
            ax.fill_between(
                xline,
                xline * max(r["sy"] - 2 * r["se"], 0.0),
                xline * (r["sy"] + 2 * r["se"]),
                color=col, alpha=0.15, zorder=2,
            )

        ax.axline((0, 0), slope=SY_ASSUMED[cid], color="gray",
                  lw=1.2, ls="--", label=f"Assumed Sy = {SY_ASSUMED[cid]:.2f}")

        ax.set_xlabel("Corrected water table rise Δh + β₃|h|  (mm/month)")
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
        "Approach A — WTF Specific Yield: Drainage-Corrected OLS Regression\n"
        "Newborough Warren 2005–2026  |  Winter months (Nov–Mar, PET < 25 mm/month)\n"
        "Δh corrected for storage decay: Δh_corr = Δh + β₃·|h_prev|",
        fontsize=10, fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    render_figure(fig, out_path, facecolor="white")
    plt.close()
    print(f"Regression figure saved → {out_path.name}")


def plot_event_boxplot(b_results, out_path):
    """Figure: Sy distribution from Approach B event method (k=5 + forest-corrected)."""
    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor="white")
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
                    ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=8, rotation=20, ha="right")
    ax.set_ylabel("Specific yield Sy  (dimensionless)")
    ax.set_ylim(0, 0.45)
    ax.axhline(0.12, color="gray", lw=1.0, ls=":", alpha=0.7,
               label="Assumed Sy non-C1 = 0.12")
    ax.axhline(0.08, color="gray", lw=1.0, ls="--", alpha=0.7,
               label="Assumed Sy C1 = 0.08")
    ax.legend(fontsize=8.5, framealpha=0.9, loc="upper left")
    ax.grid(axis="y", lw=0.4, alpha=0.5)
    ax.set_title(
        "Approach B — WTF Specific Yield: Event-Based Estimates\n"
        "Distribution of monthly Sy estimates from rising-limb events "
        "(Δh > 5 mm, net R > 10 mm)\n"
        "Forest corrected: R = (1−0.24)P − PET (Freeman, 2008); "
        "hatched boxes = interception-corrected",
        fontsize=10, fontweight="bold",
    )
    plt.tight_layout()
    render_figure(fig, out_path, facecolor="white")
    plt.close()
    print(f"Boxplot figure saved → {out_path.name}")


def export_csv(a_results, b_results, c_results, out_path):
    """Export summary CSV: one row per (cluster, corrected) entry.

    Approach A/B columns are unchanged and byte-stable. Approach C columns are
    populated per base cluster (uncorrected rows only — Approach C runs once per
    cluster, with forest clusters interception-corrected internally); the
    forest-corrected duplicate rows carry NaN Approach C fields.
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
        c = c_results[cid] if not corrected else None
        rows.append({
            "Cluster":               label,
            "Corrected":             corrected,
            "Sy_assumed":            SY_ASSUMED[cid],
            "Sy_OLS_winter":         a["sy"],
            "Sy_OLS_SE":             a["se"],
            "Sy_OLS_R2":             a["r2"],
            "Sy_OLS_n":              a["n"],
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
        })
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"CSV saved → {out_path.name}")


def write_summary(a_results, b_results, c_results, out_path):
    """Plain-text summary for manuscript."""
    lines = [
        "=" * 70,
        "SPECIFIC YIELD ESTIMATION — WATER TABLE FLUCTUATION METHOD",
        "Newborough Warren 2005-2026",
        "=" * 70,
        "",
        "Method: Healy and Cook (2002)",
        "  Sy = R / dh",
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
            f"  {CLUSTER_LABELS[cid]:<32}  Sy = {sy_s}  "
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
        suffix = "   [Freeman 2008; R_eff = (1 − 0.24)·P − PET]" if corrected else ""
        lines.append(
            f"  {label:<32}  Sy = {b['sy_median']:.3f}  "
            f"IQR [{b['q25']:.3f}, {b['q75']:.3f}]  n = {b['n']}{suffix}"
        )

    lines += [
        "",
        "APPROACH C — Rapid Recharge Events (Crosbie et al., 2005)",
        "-" * 70,
        f"  Episode: >= {WTF_C_DRY_BASELINE} mo of dh <= 0 baseline, then rise",
        f"  >= {WTF_C_MIN_RISE_M*1000:.0f} mm over <= {WTF_C_MAX_DURATION} mo; "
        f"per-episode Sy in [{WTF_C_SY_MIN:.2f}, {WTF_C_SY_MAX:.2f}].",
        f"  Cluster Sy = median of episode Sy_i, 95% CI from "
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
            f"  {CLUSTER_LABELS[cid]:<32}  Sy = {c['sy_median']:.3f}  "
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
        # Approach C attaches to the base (uncorrected) cluster row only.
        c = c_results[cid] if not corrected else None
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
        "  and does NOT propagate downstream (Approach B per-well Sy remains the",
        "  pipeline-consumed canonical). It is data-limited at the forest",
        "  clusters (small n) and reported there with n and CI shown.",
        "- Forested clusters (C4 Main Forest, C5 Coastal Forest) are reported as",
        "  both uncorrected and interception-corrected (Freeman 2008) variants.",
        "  The corrected variant applies R_effective = (1 − 0.24)·P − PET. PET",
        "  is not reduced because Thornthwaite PET is an energy-based atmospheric",
        "  demand (independent of land cover), so reducing only P is physically",
        "  motivated and not double-counting.",
        "- Approach A corrected variants are not fitted in this version (the",
        "  corrected fits were unstable; the report uses Approach B for the",
        "  corrected forest values populating Table 3c).",
        "- The corrected forest event pool is typically larger than the",
        "  uncorrected pool because reducing P brings previously-excluded high",
        "  events (Sy > 0.50) into the admissible range.",
        "- Both approaches give indicative Sy only; slug tests or pumping tests",
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
    banner("17", "WTF Specific Yield", version=__version__)
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
    a_results = approach_a_ols(df)

    print("\nApproach B — Event-based median:")
    b_results = approach_b_events(df)

    print("\nApproach C — Rapid recharge events (Crosbie et al., 2005):")
    c_results = approach_c_rapid_events(df)

    print("\nGenerating figures...")
    plot_regression(df, a_results, path_reg)
    plot_event_boxplot(b_results, path_box)
    plot_rapid_events(c_results, path_rapid)

    print("\nExporting outputs...")
    export_csv(a_results, b_results, c_results, path_table)
    write_summary(a_results, b_results, c_results, path_summary)

    print("\nAll outputs written to", out_dir)


if __name__ == '__main__':
    main()
