#!/usr/bin/env python3
"""
55_water_balance_drainage.py — the water-balance residual analysis: a fourth reading of the loss split

QUESTION
  Paper M §7.1 says heads alone cannot split the annual loss between evapotranspiration and
  drainage: Model A books 68 % of it as drainage at the median well, Model B 45 %, and the two
  forms are left apart. §2.4 bounds the split from below without a datum or a specific yield, and
  §5.2 reads a drainage share off the summer recession. This step is a FOURTH reading, and the only
  one on the same basis as the 68 % / 45 % pair — a drainage share of the ANNUAL loss at the median
  well. It gets there by taking the storage term out of the fit instead of fitting it.

METHOD (spec NRG_spec_water_balance_diagnostic_2026-11-04, D1-D11 signed off Martin 23:20-23:23)
  A basic water balance whose storage change is the water table through a specific yield fixed from
  outside the fit, so that what is left over is drainage:
      D(t) = P_eff(t) - PET(t) - Sy * dh(t)                     (m water / month)
  P_eff reduces rainfall by FOREST_INTERCEPTION under the canopy and leaves PET gross
  (INTERCEPTION_TREATMENT.md case (c)); Sy is Script 18's per-well Sy_median (D3), never fitted here.
  The residual is regressed on the previous month's head, as a line D = a + c*h_prev and as a
  threshold D = a + c*max(h_prev - h0, 0); k = c/Sy is the fraction of the head above h0 drained per
  month. The threshold is adopted only where it beats the line by more than WB_BIC_MARGIN in BIC,
  counting h0 as a fitted parameter (D6); otherwise the line stands.

  This is NOT Script 08's traditional linear model, which fits free rainfall and PET coefficients and
  carries no drainage term. Here those coefficients are 1/Sy by construction and only the drainage law
  is fitted. In documents it is "water-balance residual analysis", never "TLM" (D1).

  It is a DIAGNOSTIC, not a forecaster (D-303): inside the record it forecasts like Model A and below
  Model B, and in the drier decade it fails too wet, because its fitted constant ties the level to the
  modern mean. Stage G measures that rather than hiding it.

STAGES
  A  cluster-mean month: the surplus P_eff - PET on the mean dh; slope = apparent Sy
  B  per well: the residual drainage law, line and threshold, and the cluster summaries
  C  annual water balance from the fitted law
  D  winter law (ET is small enough there to trust PET), ET backed out in every month, the drainage
     share of the annual loss and its network median - the §7.1 basis - at the Stage I Sy bracket too
  E  sensitivities: C1 without CEH11, the below-ground-only winter fit, Script 17's cluster Sy
  F  the forest interception closure scan
  G  split-sample free run on Script 48's rule with Script 18's WINDOWED Sy (D8), and the CCW
     1989-96 hindcast on Script 39's series and censoring
  H  the dry-month drainage law: drainage is best measured when little rain falls (D9). Selection is
     on RAINFALL ONLY - dh sits inside the residual, so choosing months because the level fell would
     select on the outcome
  I  the winter joint fit: with ET = 0, Sy*dh = P_eff - D(h) has two unknowns, so winter months
     estimate Sy and the drainage law together without borrowing Script 18's. Both P and dh carry
     error, so both regression directions are fitted as a bracket (D11)

OUTPUTS (outputs/55_water_balance_drainage/)
  55_01_surplus_vs_dh.csv/.png        A  apparent Sy per cluster
  55_02_drainage_law_per_well.csv     B  line and threshold per well
  55_03_drainage_law_by_cluster.csv   B  cluster summaries
  55_02_drainage_law.png              B
  55_04_water_balance.csv             C  annual balance per well per year
  55_05_winter_law_et.csv             D  winter law, ET/PET and the drainage share per well
  55_06_et_monthly.csv                D  month x well backed-out ET
  55_05_et_vs_pet.png                 D
  55_07_sensitivity.csv               E
  55_08_interception_scan.csv         F
  55_09_split_sample.csv              G
  55_10_ccw_hindcast.csv              G
  55_11_dry_month_law_per_well.csv    H
  55_12_dry_month_law_by_cluster.csv  H
  55_13_winter_sy_per_well.csv        I
  55_14_winter_sy_by_cluster.csv      I
  55_13_winter_sy_bracket.png         I
  55_report_numbers.csv               wb_*

Run directly:  python3 src/55_water_balance_drainage.py [--no-fig]
"""
from __future__ import annotations

__version__ = "1.0.0"  # Hollingham (2026) - 2026-11-05. First issue (spec
#   NRG_spec_water_balance_diagnostic_2026-11-04, D1-D11; Martin 2026-11-04 "take a basic water balance ...
#   and regress that residual on head to get a drainage rate"). Per-cluster and network statistics are
#   per-well MEDIANS, matching the modelab_drainage_share_*_median_* fields this step is quoted beside
#   (Martin, 2026-11-05); the per-well mean is emitted alongside, because that is a rendering choice.

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
    DIR_55, OUT_55_SURPLUS_VS_DH, OUT_55_SURPLUS_FIG, OUT_55_LAW_PER_WELL, OUT_55_LAW_BY_CLUSTER,
    OUT_55_LAW_FIG, OUT_55_WATER_BALANCE, OUT_55_WINTER_LAW_ET, OUT_55_ET_MONTHLY,
    OUT_55_ET_VS_PET_FIG, OUT_55_SENSITIVITY, OUT_55_INTERCEPTION_SCAN, OUT_55_SPLIT_SAMPLE,
    OUT_55_CCW_HINDCAST, OUT_55_DRY_LAW_PER_WELL, OUT_55_DRY_LAW_BY_CLUSTER,
    OUT_55_WINTER_SY_PER_WELL, OUT_55_WINTER_SY_CLUSTER, OUT_55_WINTER_SY_FIG,
    OUT_55_REPORT_NUMBERS, INT_CLIMATE, INT_WELLS_REFERENCE, INT_MASTER_DATA,
    OUT_18_WELL_SY_TABLE, OUT_18_WELL_SY_BY_WINDOW, OUT_17_SY_TABLE, OUT_48_MODEL_AB,
)
from utils.config import (                                    # noqa: E402
    WB_WINTER_MONTHS, WB_SUMMER_MONTHS, WB_HINGE_GRID_PCT, WB_HINGE_GRID_N, WB_BIC_MARGIN,
    WB_MIN_MONTHS, WB_MIN_WINTER_MONTHS, WB_MIN_WELLS_PER_MONTH, WB_INTERCEPTION_SCAN,
    WB_DRY_RAIN_QUANTILE, WB_RISE_MARGIN_M, WB_DRY_WINTER_MONTHS, WINTER_RECESSION_MONTHS,
    FOREST_INTERCEPTION, FOREST_CIDS, CLUSTER_LABELS, MODEL_AB_SPLIT_DATE,
    MODEL_AB_MIN_TEST_MONTHS,
)
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.model_utils import simulate_water_balance          # noqa: E402
from utils.hindcast_utils import load_ccw, observed_series, usable_codes, BETA_COLS  # noqa: E402
from utils.console_utils import (                             # noqa: E402
    banner, phase, step, info, warn, saved, note, result, done, track,
)
from utils.render_utils import MPL_DEFAULTS                   # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402

CLUSTERS = (1, 2, 3, 4, 5)


# ── least squares, BIC and the two law forms ──────────────────────────────────────────────────────
def _ols(X: np.ndarray, y: np.ndarray):
    """(coefficients, BIC without the parameter penalty, R2). The penalty is added by the caller,
    which is the only place that knows how many parameters the form really cost."""
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    rss = float(r @ r)
    n = len(y)
    tss = float(((y - y.mean()) ** 2).sum())
    bic_core = n * np.log(rss / n) if rss > 0 and n else np.nan
    return b, bic_core, (1.0 - rss / tss if tss > 0 else np.nan)


def fit_line(h_prev: np.ndarray, D: np.ndarray) -> dict:
    """D = a + c*h_prev. Two parameters."""
    b, core, r2 = _ols(np.column_stack([np.ones(len(h_prev)), h_prev]), D)
    return dict(form="line", a=float(b[0]), c=float(b[1]), h0=np.nan,
                bic=core + 2 * np.log(len(h_prev)), r2=r2, n=len(h_prev))


def fit_hinge(h_prev: np.ndarray, D: np.ndarray) -> dict | None:
    """D = a + c*max(h_prev - h0, 0), h0 searched on a fixed grid between the
    WB_HINGE_GRID_PCT percentiles of this well's h_prev.

    THREE parameters, not two. h0 is chosen by the search, so counting only a and c lets the
    threshold win for free: without the third penalty it beats the line at 48 of the 66 reference
    wells instead of 29, and §2 of the spec reports 29 (measured 2026-11-05)."""
    lo, hi = np.percentile(h_prev, WB_HINGE_GRID_PCT)
    best = None
    for h0 in np.linspace(lo, hi, WB_HINGE_GRID_N):
        x = np.maximum(h_prev - h0, 0.0)
        if np.ptp(x) == 0:
            continue
        b, core, r2 = _ols(np.column_stack([np.ones(len(h_prev)), x]), D)
        bic = core + 3 * np.log(len(h_prev))
        if best is None or bic < best["bic"]:
            best = dict(form="threshold", a=float(b[0]), c=float(b[1]), h0=float(h0),
                        bic=bic, r2=r2, n=len(h_prev))
    return best


def select_law(h_prev: np.ndarray, D: np.ndarray) -> tuple[dict, dict, dict, float]:
    """(line, threshold, selected, dBIC). The threshold is adopted only where it beats the line by
    more than WB_BIC_MARGIN (D6); a tie, or no admissible hinge, leaves the line."""
    line = fit_line(h_prev, D)
    hinge = fit_hinge(h_prev, D)
    if hinge is None:
        return line, {}, line, np.nan
    dbic = hinge["bic"] - line["bic"]
    return line, hinge, (hinge if dbic < -WB_BIC_MARGIN else line), dbic


def predict(law: dict, h_prev) -> np.ndarray:
    h_prev = np.asarray(h_prev, dtype=float)
    if law.get("form") == "threshold":
        return law["a"] + law["c"] * np.maximum(h_prev - law["h0"], 0.0)
    return law["a"] + law["c"] * h_prev


def steady_head(law: dict, surplus: float) -> float:
    """The head at which the law drains the mean surplus — where a free run settles."""
    if not np.isfinite(law.get("c", np.nan)) or law["c"] <= 0:
        return np.nan
    h = (surplus - law["a"]) / law["c"]
    if law.get("form") == "threshold":
        above = (surplus - law["a"]) / law["c"]
        h = law["h0"] + above if above > 0 else law["h0"]
    return h


# ── inputs ────────────────────────────────────────────────────────────────────────────────────────
def load_inputs():
    """Climate, the reference wells, Script 18's per-well Sy (full record and by window) and the
    cluster membership. The single missing climate month (1941-06) is dropped exactly as Script 39
    drops it, so the two hindcasts run on the same forcing (spec §7.3)."""
    cl = (pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)[["P_m", "PET"]]
          .apply(pd.to_numeric, errors="coerce").dropna())
    wells = pd.read_csv(INT_WELLS_REFERENCE, index_col=0, parse_dates=True)
    sy = pd.read_csv(OUT_18_WELL_SY_TABLE)
    cols = {normalize_well_name(c): c for c in wells.columns}
    sy["col"] = sy["Well"].astype(str).apply(normalize_well_name).map(cols)
    missing = sy["col"].isna().sum()
    if missing:
        warn(f"{missing} Script 18 wells have no column in the reference frame — skipped")
        sy = sy[sy["col"].notna()]
    win = pd.read_csv(OUT_18_WELL_SY_BY_WINDOW) if OUT_18_WELL_SY_BY_WINDOW.is_file() else None
    return cl, wells, sy.reset_index(drop=True), win


def well_frame(wells: pd.DataFrame, col: str, cl: pd.DataFrame, cluster: int,
               sy_value: float, interception: float | None = None) -> pd.DataFrame | None:
    """One well's aligned monthly frame, with the residual already formed.

    Differenced on the monthly calendar before incomplete months drop (D-195), so a change across a
    missed visit is not booked as one month's."""
    f = interception if interception is not None else FOREST_INTERCEPTION
    h = pd.to_numeric(wells[col], errors="coerce")
    df = pd.DataFrame({"h": h}).join(cl, how="inner").sort_index()
    df["h_prev"] = df["h"].shift(1)
    df["Delta_h"] = df["h"] - df["h_prev"]
    df = df.dropna(subset=["h", "h_prev", "Delta_h", "P_m", "PET"])
    if len(df) < WB_MIN_MONTHS:
        return None
    forest = cluster in FOREST_CIDS
    df["P_eff"] = df["P_m"] * (1 - f) if forest else df["P_m"]
    df["interception"] = df["P_m"] * f if forest else 0.0
    df["storage_m"] = sy_value * df["Delta_h"]
    df["D_residual"] = df["P_eff"] - df["PET"] - df["storage_m"]
    return df


def all_frames(wells, cl, sy, interception=None) -> dict:
    """{(cluster, well): frame} over every admitted reference well."""
    out = {}
    for r in sy.itertuples():
        df = well_frame(wells, r.col, cl, int(r.Cluster), float(r.Sy_median), interception)
        if df is not None:
            out[(int(r.Cluster), r.Well)] = df
    return out


def _cluster_stats(df: pd.DataFrame, cols, by="Cluster") -> pd.DataFrame:
    """Per-well median AND mean per cluster. The median is what is registered and quoted — it is the
    statistic of the modelab_drainage_share_*_median_* fields this step sits beside (Martin,
    2026-11-05); the mean rides along because choosing between them is a rendering decision."""
    g = df.groupby(by)
    out = pd.DataFrame({"n_wells": g.size()})
    for c in cols:
        out[f"{c}_median"] = g[c].median()
        out[f"{c}_mean"] = g[c].mean()
    return out.reset_index()


# ── Stage A: the cluster-mean month ───────────────────────────────────────────────────────────────
def stage_a(wells, cl, sy) -> pd.DataFrame:
    """The surplus against the cluster-mean head change. Its slope is an APPARENT Sy — what a single
    regression would call the storage coefficient if drainage were ignored — and its intercept is the
    drainage at a steady level. Both are read, neither is used downstream."""
    rows = []
    for k in CLUSTERS:
        g = sy[sy["Cluster"] == k]
        if g.empty:
            continue
        h = wells[[c for c in g["col"]]]
        dh = h.diff()
        n_rep = dh.notna().sum(axis=1)
        mean_dh = dh.mean(axis=1).where(n_rep >= WB_MIN_WELLS_PER_MONTH)
        P = cl["P_m"].reindex(mean_dh.index)
        PET = cl["PET"].reindex(mean_dh.index)
        P_eff = P * (1 - FOREST_INTERCEPTION) if k in FOREST_CIDS else P
        d = pd.DataFrame({"Delta_h": mean_dh, "surplus": P_eff - PET}).dropna()
        b, _, r2 = _ols(np.column_stack([np.ones(len(d)), d["Delta_h"].values]),
                        d["surplus"].values)
        rows.append(dict(Cluster=k, Cluster_Label=CLUSTER_LABELS.get(k, ""),
                         n_wells=len(g), n_months=len(d),
                         apparent_Sy=float(b[1]), drainage_at_steady_level_m=float(b[0]),
                         r2=r2, Sy_wtf_cluster_median=float(g["Sy_median"].median()),
                         min_wells_per_month=WB_MIN_WELLS_PER_MONTH))
    return pd.DataFrame(rows)


# ── Stage B: the residual drainage law, per well ──────────────────────────────────────────────────
def stage_b(frames: dict, sy: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    syv = {(int(r.Cluster), r.Well): float(r.Sy_median) for r in sy.itertuples()}
    rows, laws = [], {}
    for key in track(sorted(frames), lambda k: f"C{k[0]} {k[1]}"):
        df = frames[key]
        s = syv[key]
        line, hinge, sel, dbic = select_law(df["h_prev"].values, df["D_residual"].values)
        laws[key] = {"line": line, "threshold": (hinge or None), "selected": sel}
        rows.append(dict(
            Well=key[1], Cluster=key[0], Cluster_Label=CLUSTER_LABELS.get(key[0], ""),
            Sy=s, n_months=len(df),
            a_line=line["a"], c_line=line["c"], k_line=line["c"] / s, r2_line=line["r2"],
            bic_line=line["bic"],
            a_hinge=hinge.get("a", np.nan), c_hinge=hinge.get("c", np.nan),
            k_hinge=hinge.get("c", np.nan) / s, h0_m=hinge.get("h0", np.nan),
            h0_depth_below_ground_m=-hinge.get("h0", np.nan), r2_hinge=hinge.get("r2", np.nan),
            bic_hinge=hinge.get("bic", np.nan), dBIC=dbic,
            threshold_beats_line=bool(np.isfinite(dbic) and dbic < -WB_BIC_MARGIN),
            form_selected=sel["form"],
            k_selected=sel["c"] / s, r2_selected=sel["r2"]))
    per = pd.DataFrame(rows).sort_values(["Cluster", "Well"]).reset_index(drop=True)
    cols = ["Sy", "k_line", "r2_line", "k_hinge", "h0_depth_below_ground_m", "r2_hinge",
            "k_selected", "r2_selected"]
    by = _cluster_stats(per, cols)
    wins = per.groupby("Cluster")["threshold_beats_line"].sum()
    by["n_threshold_beats_line"] = by["Cluster"].map(wins).astype(int)
    by["Cluster_Label"] = by["Cluster"].map(CLUSTER_LABELS)
    by["bic_margin"] = WB_BIC_MARGIN
    return per, by, laws


# ── Stage C: the annual water balance from the fitted law ─────────────────────────────────────────
def stage_c(frames: dict, laws: dict) -> pd.DataFrame:
    """Per well per calendar year: rainfall, interception, PET, the law's drainage, the storage
    change and the ET that closes the balance. Incomplete years are kept and flagged rather than
    dropped — a well with a gap still says something about the years it does cover."""
    rows = []
    for key, df in frames.items():
        d = df.copy()
        d["drainage_m"] = predict(laws[key]["selected"], d["h_prev"].values)
        d["ET_m"] = d["P_eff"] - d["drainage_m"] - d["storage_m"]
        g = d.groupby(d.index.year)
        for yr, sub in g:
            rows.append(dict(
                Well=key[1], Cluster=key[0], year=int(yr), n_months=len(sub),
                complete_year=bool(len(sub) == 12),
                P_m=float(sub["P_m"].sum()), interception_m=float(sub["interception"].sum()),
                P_eff_m=float(sub["P_eff"].sum()), PET_m=float(sub["PET"].sum()),
                drainage_m=float(sub["drainage_m"].sum()),
                storage_change_m=float(sub["storage_m"].sum()),
                ET_m=float(sub["ET_m"].sum()),
                form_selected=laws[key]["selected"]["form"]))
    return pd.DataFrame(rows).sort_values(["Cluster", "Well", "year"]).reset_index(drop=True)


# ── Stage D: the winter law, ET, and the drainage share of the annual loss ────────────────────────
def winter_law(df: pd.DataFrame):
    """The drainage law fitted on WB_WINTER_MONTHS only, where ET is small enough that subtracting
    gross PET does little damage. Returns (law, h_prev range) or None."""
    w = df[df.index.month.isin(WB_WINTER_MONTHS)]
    if len(w) < WB_MIN_WINTER_MONTHS:
        return None
    _, _, sel, _ = select_law(w["h_prev"].values, w["D_residual"].values)
    return sel, (float(w["h_prev"].min()), float(w["h_prev"].max())), len(w)


def stage_d(frames: dict, sy: pd.DataFrame, sy_bracket: pd.DataFrame | None = None):
    """ET is backed out in every month from the winter law, and the ratio to PET is read in summer
    and over the year. Months whose previous head lies outside the range the winter law was fitted on
    are EXCLUDED and counted: predicting there is extrapolation, and §5 of the spec attaches that
    exclusion to the whole of this stage, so every Stage D number rests on one set of months. The
    all-month variant rides along in the CSV so the size of that choice stays visible."""
    syv = {(int(r.Cluster), r.Well): float(r.Sy_median) for r in sy.itertuples()}
    lo_hi = {}
    if sy_bracket is not None:
        lo_hi = {(int(r.Cluster), r.Well): (r.Sy_winter_lo, r.Sy_winter_hi)
                 for r in sy_bracket.itertuples()}
    rows, et_cols = [], {}
    for key in sorted(frames):
        df = frames[key]
        got = winter_law(df)
        if got is None:
            note(f"C{key[0]} {key[1]}: fewer than {WB_MIN_WINTER_MONTHS} winter months — no winter law")
            continue
        law, (wlo, whi), n_win = got
        s = syv[key]
        d = df.copy()
        d["drainage_m"] = predict(law, d["h_prev"].values)
        d["ET_m"] = d["P_eff"] - d["drainage_m"] - d["storage_m"]
        d["in_winter_head_range"] = (d["h_prev"] >= wlo) & (d["h_prev"] <= whi)
        et_cols[f"{key[1]}"] = d["ET_m"].where(d["in_winter_head_range"])
        inr = d[d["in_winter_head_range"]]
        summer = inr[inr.index.month.isin(WB_SUMMER_MONTHS)]
        row = dict(Well=key[1], Cluster=key[0], Cluster_Label=CLUSTER_LABELS.get(key[0], ""),
                   Sy=s, form_selected=law["form"], a=law["a"], c=law["c"], h0_m=law["h0"],
                   k_winter=law["c"] / s, r2_winter=law["r2"], n_winter_months=n_win,
                   winter_h_prev_min=wlo, winter_h_prev_max=whi,
                   n_months=len(d), n_months_in_range=len(inr),
                   n_months_excluded=int(len(d) - len(inr)))
        for tag, sub in (("", inr), ("_all_months", d)):
            sm = sub[sub.index.month.isin(WB_SUMMER_MONTHS)] if tag else summer
            row[f"et_pet_summer{tag}"] = (float(sm["ET_m"].sum() / sm["PET"].sum())
                                          if sm["PET"].sum() > 0 else np.nan)
            row[f"et_pet_year{tag}"] = (float(sub["ET_m"].sum() / sub["PET"].sum())
                                        if sub["PET"].sum() > 0 else np.nan)
            loss = sub["drainage_m"].sum() + sub["ET_m"].sum() + sub["interception"].sum()
            row[f"drainage_share{tag}"] = (float(sub["drainage_m"].sum() / loss)
                                           if loss > 0 else np.nan)
        # the same share at the Stage I Sy bracket, so §7.1's quantity carries the Sy uncertainty
        for tag, idx in (("_sy_lo", 0), ("_sy_hi", 1)):
            v = lo_hi.get(key)
            row[f"drainage_share{tag}"] = np.nan
            if v is None or not np.isfinite(v[idx]) or v[idx] <= 0:
                continue
            alt = well_frame_resy(df, v[idx])
            g2 = winter_law(alt)
            if g2 is None:
                continue
            law2, (lo2, hi2), _ = g2
            a2 = alt.copy()
            a2["drainage_m"] = predict(law2, a2["h_prev"].values)
            a2["ET_m"] = a2["P_eff"] - a2["drainage_m"] - a2["storage_m"]
            a2 = a2[(a2["h_prev"] >= lo2) & (a2["h_prev"] <= hi2)]
            loss2 = a2["drainage_m"].sum() + a2["ET_m"].sum() + a2["interception"].sum()
            if loss2 > 0:
                row[f"drainage_share{tag}"] = float(a2["drainage_m"].sum() / loss2)
        rows.append(row)
    per = pd.DataFrame(rows).sort_values(["Cluster", "Well"]).reset_index(drop=True)
    cols = ["k_winter", "r2_winter", "et_pet_summer", "et_pet_year", "drainage_share",
            "et_pet_summer_all_months", "et_pet_year_all_months", "drainage_share_all_months",
            "drainage_share_sy_lo", "drainage_share_sy_hi"]
    by = _cluster_stats(per, cols)
    by["Cluster_Label"] = by["Cluster"].map(CLUSTER_LABELS)
    et = pd.DataFrame(et_cols)
    return per, by, et


def well_frame_resy(df: pd.DataFrame, sy_value: float) -> pd.DataFrame:
    """The same frame with the storage term and residual recomputed at another Sy. Sy enters both the
    residual and k = c/Sy, and the two largely cancel — which is why the k's barely move across the
    bracket while the share does."""
    d = df.copy()
    d["storage_m"] = sy_value * d["Delta_h"]
    d["D_residual"] = d["P_eff"] - d["PET"] - d["storage_m"]
    return d


# ── Stage E: the sensitivities ────────────────────────────────────────────────────────────────────
def stage_e(wells, cl, sy, dper: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def _summary(name, frame, note_):
        if frame.empty:
            return
        rows.append(dict(test=name, Cluster=1, Cluster_Label=CLUSTER_LABELS.get(1, ""),
                         et_pet_summer_median=float(frame["et_pet_summer"].median()),
                         et_pet_year_median=float(frame["et_pet_year"].median()),
                         drainage_share_median=float(frame["drainage_share"].median()),
                         n_wells=len(frame), note=note_))

    c1 = dper[dper["Cluster"] == 1]
    _summary("C1 as published", c1, "every C1 well")
    _summary("C1 without CEH11", c1[c1["Well"].astype(str).apply(normalize_well_name) != "ceh11"],
             "CEH11 is the well nearest the lake; dropping it tests whether C1's shortfall is a "
             "lake-proximity effect or is shared by the cluster")
    only = c1[c1["Well"].astype(str).apply(normalize_well_name) == "ceh11"]
    _summary("CEH11 alone", only, "the lake-edge well on its own")

    # the winter law fitted on BELOW-GROUND winter months only: if ponding were inflating C1's
    # storage term, removing the ponded months should move it
    syv = {(int(r.Cluster), r.Well): (float(r.Sy_median), r.col) for r in sy.itertuples()}
    bg = []
    for r in c1.itertuples():
        s, col = syv[(1, r.Well)]
        df = well_frame(wells, col, cl, 1, s)
        if df is None:
            continue
        w = df[df.index.month.isin(WB_WINTER_MONTHS)]
        w = w[(w["h"] < 0) & (w["h_prev"] < 0)]
        if len(w) < WB_MIN_WINTER_MONTHS:
            continue
        _, _, sel, _ = select_law(w["h_prev"].values, w["D_residual"].values)
        d = df.copy()
        d["drainage_m"] = predict(sel, d["h_prev"].values)
        d["ET_m"] = d["P_eff"] - d["drainage_m"] - d["storage_m"]
        d = d[(d["h_prev"] >= w["h_prev"].min()) & (d["h_prev"] <= w["h_prev"].max())]
        sm = d[d.index.month.isin(WB_SUMMER_MONTHS)]
        loss = d["drainage_m"].sum() + d["ET_m"].sum() + d["interception"].sum()
        bg.append(dict(Well=r.Well,
                       et_pet_summer=float(sm["ET_m"].sum() / sm["PET"].sum()),
                       et_pet_year=float(d["ET_m"].sum() / d["PET"].sum()),
                       drainage_share=float(d["drainage_m"].sum() / loss) if loss > 0 else np.nan,
                       below_ground_winter_share=float(len(w) / max(len(df[df.index.month.isin(WB_WINTER_MONTHS)]), 1))))
    bgf = pd.DataFrame(bg)
    if not bgf.empty:
        _summary("C1 winter law on below-ground months only", bgf,
                 f"{bgf['below_ground_winter_share'].median():.3f} of C1's winter months are "
                 "below ground; ponded months carry a storage coefficient near 1, not Sy")

    # Script 17's cluster Sy instead of Script 18's per-well Sy (D3: a sensitivity, never the headline)
    if OUT_17_SY_TABLE.is_file():
        s17 = pd.read_csv(OUT_17_SY_TABLE)
        s17["k"] = s17["Cluster"].astype(str).str.extract(r"^C(\d)").astype(float)
        for k in CLUSTERS:
            g = s17[(s17["k"] == k) & (s17["Corrected"] == (k in FOREST_CIDS))]
            if g.empty:
                g = s17[s17["k"] == k]
            if g.empty:
                continue
            s_cluster = float(g["Sy_event_median"].iloc[0])
            ks = []
            for r in sy[sy["Cluster"] == k].itertuples():
                df = well_frame(wells, r.col, cl, k, s_cluster)
                if df is None:
                    continue
                _, _, sel, _ = select_law(df["h_prev"].values, df["D_residual"].values)
                ks.append(sel["c"] / s_cluster)
            if ks:
                rows.append(dict(test="Sy = Script 17 cluster median", Cluster=k,
                                 Cluster_Label=CLUSTER_LABELS.get(k, ""),
                                 et_pet_summer_median=np.nan, et_pet_year_median=np.nan,
                                 drainage_share_median=np.nan, n_wells=len(ks),
                                 note=f"k median {np.median(ks):.4f} at Sy = {s_cluster:.4f} "
                                      f"(Script 17 event median); Script 18 per-well Sy is the headline"))
    return pd.DataFrame(rows)


# ── Stage F: the forest interception closure scan ─────────────────────────────────────────────────
def stage_f(wells, cl, sy) -> pd.DataFrame:
    """At each interception fraction, the ATMOSPHERIC loss the balance books, against PET. The
    fraction at which the two close is read by interpolation. It is a CLOSURE test, not a
    measurement: FOREST_INTERCEPTION stays at 0.24 (D4).

    The quantity is ET + interception, the two terms the atmosphere takes — not every loss. Total
    loss including drainage cannot be the test, because it is algebraically free of the fraction:
        ET + D + I = (P_eff - D - Sy·dh) + D + P·f = P - Sy·dh
    and the f's cancel. Measured 2026-11-05: that ratio is constant to every decimal across the
    whole scan. What does depend on f is the fitted drainage, because the winter law is refitted on a
    residual built from P_eff; a larger f leaves less water to book as drainage, so ET + I rises."""
    start, stop, stepv = WB_INTERCEPTION_SCAN
    fracs = np.round(np.arange(start, stop + stepv / 2, stepv), 6)
    rows = []
    for k in FOREST_CIDS:
        g = sy[sy["Cluster"] == k]
        for f in fracs:
            tot_loss, tot_pet, ks = [], [], []
            for r in g.itertuples():
                df = well_frame(wells, r.col, cl, k, float(r.Sy_median), interception=float(f))
                if df is None:
                    continue
                got = winter_law(df)
                if got is None:
                    continue
                law, (lo, hi), _ = got
                d = df.copy()
                d["drainage_m"] = predict(law, d["h_prev"].values)
                d["ET_m"] = d["P_eff"] - d["drainage_m"] - d["storage_m"]
                d = d[(d["h_prev"] >= lo) & (d["h_prev"] <= hi)]
                tot_loss.append(float(d["ET_m"].sum() + d["interception"].sum()))
                tot_pet.append(float(d["PET"].sum()))
                ks.append(law["c"] / float(r.Sy_median))
            if not tot_loss:
                continue
            ratios = [a / b for a, b in zip(tot_loss, tot_pet) if b > 0]
            rows.append(dict(Cluster=k, Cluster_Label=CLUSTER_LABELS.get(k, ""),
                             interception=float(f), n_wells=len(ratios),
                             atmos_loss_over_pet_median=float(np.median(ratios)),
                             atmos_loss_over_pet_mean=float(np.mean(ratios)),
                             k_median=float(np.median(ks))))
    scan = pd.DataFrame(rows)
    # the closing fraction, by linear interpolation on the median ratio crossing 1
    closes = []
    for k, g in scan.groupby("Cluster"):
        g = g.sort_values("interception")
        y = g["atmos_loss_over_pet_median"].values - 1.0
        x = g["interception"].values
        cross = np.nan
        for i in range(len(y) - 1):
            if np.isfinite(y[i]) and np.isfinite(y[i + 1]) and y[i] * y[i + 1] <= 0 and y[i] != y[i + 1]:
                cross = float(x[i] - y[i] * (x[i + 1] - x[i]) / (y[i + 1] - y[i]))
                break
        closes.append(dict(Cluster=k, interception_closing=cross))
    scan = scan.merge(pd.DataFrame(closes), on="Cluster", how="left")
    return scan


# ── Stage G: the split sample, and the CCW hindcast ───────────────────────────────────────────────
def _nse(obs: pd.Series, sim: pd.Series) -> tuple[float, int]:
    common = obs.index.intersection(sim.index)
    o, m = obs.loc[common].dropna(), sim.loc[common]
    m = m.reindex(o.index).dropna()
    o = o.reindex(m.index)
    if len(o) < MODEL_AB_MIN_TEST_MONTHS:
        return np.nan, len(o)
    den = float(((o - o.mean()) ** 2).sum())
    return (1.0 - float(((o - m) ** 2).sum()) / den if den > 0 else np.nan), len(o)


def _free_run(cl: pd.DataFrame, cluster: int, sy_value: float, law: dict,
              months: pd.DatetimeIndex, h0: float, interception=None) -> pd.Series:
    f = interception if interception is not None else FOREST_INTERCEPTION
    c = cl.reindex(months).dropna()
    P_eff = (c["P_m"] * (1 - f) if cluster in FOREST_CIDS else c["P_m"]).values
    h = simulate_water_balance(h0, P_eff, c["PET"].values, sy_value,
                               law["a"], law["c"], law.get("h0") if law["form"] == "threshold" else None)
    return pd.Series(h, index=c.index)


def stage_g_split(wells, cl, sy, win) -> pd.DataFrame:
    """Script 48's split-sample rule, run as a forecasting test should be: the Sy comes from the
    WINDOW the law is fitted on (D8), never from the full record, which has seen the test months.
    A well with no windowed Sy in a direction is skipped IN THAT DIRECTION and counted."""
    split = pd.Timestamp(MODEL_AB_SPLIT_DATE)
    wmap = {}
    if win is not None:
        for r in win.itertuples():
            wmap[normalize_well_name(str(r.Well))] = (r.Sy_median_pre, r.Sy_median_post)
    ab = pd.read_csv(OUT_48_MODEL_AB) if OUT_48_MODEL_AB.is_file() else None
    abmap = {}
    if ab is not None:
        for r in ab.itertuples():
            abmap[normalize_well_name(str(r.well))] = r
    rows = []
    for r in sy.itertuples():
        wn = normalize_well_name(str(r.Well))
        sy_pre, sy_post = wmap.get(wn, (np.nan, np.nan))
        row = dict(Well=r.Well, Cluster=int(r.Cluster),
                   Cluster_Label=CLUSTER_LABELS.get(int(r.Cluster), ""),
                   Sy_full=float(r.Sy_median), Sy_pre=sy_pre, Sy_post=sy_post, skipped="")
        skipped = []
        for direction, sy_w in (("fwd", sy_pre), ("rev", sy_post)):
            row[f"nse_{direction}"] = np.nan
            row[f"n_test_{direction}"] = 0
            if not (np.isfinite(sy_w) and sy_w > 0):
                skipped.append(f"{direction}: no windowed Sy")
                continue
            df = well_frame(wells, r.col, cl, int(r.Cluster), float(sy_w))
            if df is None:
                skipped.append(f"{direction}: too few months")
                continue
            train = df[df.index < split] if direction == "fwd" else df[df.index >= split]
            test = df[df.index >= split] if direction == "fwd" else df[df.index < split]
            if len(train) < WB_MIN_MONTHS or len(test) < MODEL_AB_MIN_TEST_MONTHS:
                skipped.append(f"{direction}: window too short")
                continue
            _, _, law, _ = select_law(train["h_prev"].values, train["D_residual"].values)
            months = pd.date_range(test.index[0], test.index[-1], freq="MS")
            sim = _free_run(cl, int(r.Cluster), float(sy_w), law, months,
                            float(test["h"].iloc[0]))
            nse, n = _nse(test["h"].iloc[1:], sim)
            row[f"nse_{direction}"] = nse
            row[f"n_test_{direction}"] = n
            row[f"form_{direction}"] = law["form"]
        a = abmap.get(wn)
        for direction in ("fwd", "rev"):
            for tag in ("A", "B"):
                row[f"nse_{direction}_model_{tag}"] = (getattr(a, f"nse_{direction}_{tag}", np.nan)
                                                       if a is not None else np.nan)
        row["skipped"] = "; ".join(skipped)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["Cluster", "Well"]).reset_index(drop=True)


def stage_g_ccw(wells, cl, sy, both_laws) -> pd.DataFrame:
    """The CCW 1989-96 hindcast, on Script 39's admitted codes, datum offsets and censoring.

    The forcing is Script 39's: the committed climate record with its single missing month
    (1941-06) dropped, simulated from the record's first month so the initial condition is long
    forgotten by 1989 (spec §7.3 — the scratch run started after the gap instead; the difference is
    spin-up length only, and this matches Script 39)."""
    if not (paths.CCW_DEPTHS.exists() and paths.CCW_CODE_MAP.exists()):
        warn("CCW historic inputs not present — Stage G's hindcast skipped")
        return pd.DataFrame()
    obs, cmap = load_ccw()
    md = pd.read_csv(INT_MASTER_DATA)
    md["k"] = md["Name_Original"].astype(str).str.lower().str.strip()
    md = md.set_index("k")
    adm = usable_codes(cmap, md, obs)
    admitted = adm[adm["admitted"]]
    first, last = obs["month"].min(), obs["month"].max()
    sykey = {normalize_well_name(str(r.Well)): (int(r.Cluster), float(r.Sy_median), r.col)
             for r in sy.itertuples()}
    lawkey = {normalize_well_name(str(w)): both_laws[(c, w)] for (c, w) in both_laws}
    rows = []
    for r in admitted.itertuples():
        wn = normalize_well_name(str(r.well))
        if wn not in sykey or wn not in lawkey:
            note(f"{r.code}: no water-balance law for {r.well}")
            continue
        cluster, sy_value, _ = sykey[wn]
        o, n_cens = observed_series(obs, r.code, r.datum_offset_m)
        if o.empty:
            note(f"{r.code}: no uncensored observations")
            continue
        sub = cl.loc[:last]
        P_eff = (sub["P_m"] * (1 - FOREST_INTERCEPTION) if cluster in FOREST_CIDS
                 else sub["P_m"])
        surplus = float((P_eff - sub["PET"]).mean())
        # BOTH forms are run at every code, not only the one BIC selected: the two carry the
        # diagnostic, and a bias quoted for "the line" has to be the line everywhere.
        for form in ("line", "threshold", "selected"):
            law = lawkey[wn].get(form)
            if not law:
                continue
            h0 = steady_head(law, surplus)
            if not np.isfinite(h0):
                note(f"{r.code}: the {form} law has no steady head — skipped")
                continue
            sim = pd.Series(simulate_water_balance(
                h0, P_eff.values, sub["PET"].values, sy_value, law["a"], law["c"],
                law.get("h0") if law["form"] == "threshold" else None), index=sub.index)
            spinup = int((sim.index < first).sum())
            pred = sim.loc[first:last]
            common = o.index.intersection(pred.index)
            if len(common) < MODEL_AB_MIN_TEST_MONTHS:
                note(f"{r.code}: {len(common)} overlapping months — not scored")
                continue
            oo, pp = o.loc[common], pred.loc[common]
            den = float(((oo - oo.mean()) ** 2).sum())
            rows.append(dict(code=r.code, Well=r.well, Cluster=cluster, Sy=sy_value,
                             law_form=form,
                             selected_form=lawkey[wn]["selected"]["form"],
                             n_months=len(common), n_censored=n_cens, spinup_months=spinup,
                             bias_m=float((pp - oo).mean()),
                             rmse_m=float(np.sqrt(((pp - oo) ** 2).mean())),
                             nse=(1.0 - float(((oo - pp) ** 2).sum()) / den if den > 0 else np.nan),
                             h0_start_m=h0))
    return pd.DataFrame(rows)


# ── Stage H: the dry-month drainage law ───────────────────────────────────────────────────────────
def dry_months(cl: pd.DataFrame, wells: pd.DataFrame) -> tuple[set, float]:
    """The site's driest WB_DRY_RAIN_QUANTILE of months over the reference period. One gauge, so ONE
    set of dry months for every well (D9), and the cut is on RAINFALL only — Delta_h sits inside the
    residual, so selecting months because the level fell would select on the outcome."""
    ref = cl.loc[wells.index.min():wells.index.max()]
    thr = float(ref["P_m"].quantile(WB_DRY_RAIN_QUANTILE))
    return set(ref.index[ref["P_m"] <= thr]), thr


def stage_h(frames: dict, sy: pd.DataFrame, dry: set, thr: float):
    """The LINE form on each month subset: the threshold's h0 cannot be identified on a dozen months.
    Dry-winter k is the cleaner estimate; the all-season dry k is an UPPER bound, because about half
    its months are summer and a deep table that evaporates below PET makes over-subtracting PET
    steepen the slope (the effect Script 15's depth-dependent model targets)."""
    syv = {(int(r.Cluster), r.Well): float(r.Sy_median) for r in sy.itertuples()}
    rows = []
    for key in sorted(frames):
        df = frames[key]
        s = syv[key]
        is_dry = pd.Series([i in dry for i in df.index], index=df.index)
        subsets = {
            "all": df,
            "dry_all": df[is_dry],
            "dry_winter": df[is_dry & df.index.month.isin(WB_DRY_WINTER_MONTHS)],
            "dry_rising": df[is_dry & (df["Delta_h"] > WB_RISE_MARGIN_M)],
            "dry_falling": df[is_dry & (df["Delta_h"] < 0)],
        }
        row = dict(Well=key[1], Cluster=key[0], Cluster_Label=CLUSTER_LABELS.get(key[0], ""), Sy=s,
                   dry_rain_threshold_m=thr)
        for nm, d in subsets.items():
            row[f"n_{nm}"] = len(d)
            row[f"mean_pet_{nm}"] = float(d["PET"].mean()) if len(d) else np.nan
            if len(d) < 10:
                row[f"k_{nm}"] = np.nan
                row[f"r2_{nm}"] = np.nan
                continue
            law = fit_line(d["h_prev"].values, d["D_residual"].values)
            row[f"k_{nm}"] = law["c"] / s
            row[f"r2_{nm}"] = law["r2"]
        nd = max(row["n_dry_all"], 1)
        row["dry_summer_share"] = float(
            len(subsets["dry_all"][subsets["dry_all"].index.month.isin(WB_SUMMER_MONTHS)]) / nd)
        # D9's rise test: a rise in a dry month means water arrived from somewhere else - or last
        # month's rain is still draining down. The previous month's rainfall is what tells them apart.
        d0 = subsets["dry_all"]
        rising = d0[d0["Delta_h"] > WB_RISE_MARGIN_M]
        falling = d0[d0["Delta_h"] <= WB_RISE_MARGIN_M]
        row["dry_rise_share"] = float(len(rising) / nd)
        row["n_dry_rise_winter_half"] = int(rising.index.month.isin((10, 11, 12, 1, 2, 3)).sum())
        row["n_dry_rise_summer_half"] = int(len(rising) - row["n_dry_rise_winter_half"])
        prev = df["P_m"].shift(1)
        row["prev_rain_dry_rising_m"] = float(prev.reindex(rising.index).mean()) if len(rising) else np.nan
        row["prev_rain_dry_falling_m"] = float(prev.reindex(falling.index).mean()) if len(falling) else np.nan
        row["rise_margin_m"] = WB_RISE_MARGIN_M
        rows.append(row)
    per = pd.DataFrame(rows).sort_values(["Cluster", "Well"]).reset_index(drop=True)
    cols = [c for c in per.columns if c.startswith(("k_", "r2_", "mean_pet_", "dry_", "prev_rain_"))]
    by = _cluster_stats(per, [c for c in cols if per[c].dtype.kind == "f"])
    by["Cluster_Label"] = by["Cluster"].map(CLUSTER_LABELS)
    return per, by


# ── Stage I: the winter joint fit of Sy and the drainage law ──────────────────────────────────────
def stage_i(wells, cl, sy):
    """With ET taken as zero, Sy*Delta_h = P_eff - D(h) has two unknowns, so the winter months
    estimate Sy and the drainage law TOGETHER and borrow nothing from Script 18.

    Both the rainfall (an off-site gauge) and the head change carry error, and errors-in-variables
    pulls the two regression directions opposite ways, so both are fitted and reported as a BRACKET
    (D11) rather than one of them as an answer:
        Delta_h on (P_eff, h_prev)   slope 1/Sy  ->  rain error biases Sy HIGH
        P_eff on (Delta_h, h_prev)   slope Sy    ->  level error biases Sy LOW
    Months at or above ground at either end are excluded: ponded storage is near 1, not Sy (D10).
    WINTER_RECESSION_MONTHS is reused so Script 16 and this step share one winter definition."""
    rows = []
    for r in sy.itertuples():
        s_wtf = float(r.Sy_median)
        df = well_frame(wells, r.col, cl, int(r.Cluster), s_wtf)
        if df is None:
            continue
        w = df[df.index.month.isin(WINTER_RECESSION_MONTHS)]
        w = w[(w["h"] < 0) & (w["h_prev"] < 0)]
        n_above = int(len(df[df.index.month.isin(WINTER_RECESSION_MONTHS)]) - len(w))
        if len(w) < WB_MIN_WINTER_MONTHS:
            note(f"C{int(r.Cluster)} {r.Well}: {len(w)} below-ground winter months — no joint fit")
            continue
        P = w["P_eff"].values
        dh = w["Delta_h"].values
        hp = w["h_prev"].values
        row = dict(Well=r.Well, Cluster=int(r.Cluster),
                   Cluster_Label=CLUSTER_LABELS.get(int(r.Cluster), ""),
                   Sy_wtf=s_wtf, n_winter_below_ground=len(w), n_winter_at_or_above_ground=n_above)
        for tag, et in (("", 0.0), ("_et_pet", None)):
            y_P = P - (w["PET"].values if et is None else 0.0)
            # Delta_h on P: slope is 1/Sy, so this direction is the HIGH bound
            b1, _, r2_1 = _ols(np.column_stack([np.ones(len(w)), y_P, hp]), dh)
            sy_hi = 1.0 / b1[1] if b1[1] > 0 else np.nan
            # P on Delta_h: slope is Sy itself, the LOW bound
            b2, _, r2_2 = _ols(np.column_stack([np.ones(len(w)), dh, hp]), y_P)
            sy_lo = float(b2[1]) if b2[1] > 0 else np.nan
            mid = (float(np.sqrt(sy_lo * sy_hi)) if (np.isfinite(sy_lo) and np.isfinite(sy_hi)
                                                     and sy_lo > 0 and sy_hi > 0) else np.nan)
            row.update({
                f"Sy_winter_lo{tag}": sy_lo, f"Sy_winter_hi{tag}": sy_hi,
                f"Sy_winter_mid{tag}": mid,
                f"k_winter_joint{tag}": (float(b2[2]) / sy_hi if np.isfinite(sy_hi) else np.nan),
                f"r2_dh_on_P{tag}": r2_1, f"r2_P_on_dh{tag}": r2_2,
            })
        rows.append(row)
    per = pd.DataFrame(rows).sort_values(["Cluster", "Well"]).reset_index(drop=True)
    cols = [c for c in per.columns if c.startswith(("Sy_w", "k_winter_joint", "r2_"))]
    by = _cluster_stats(per, cols)
    by["Cluster_Label"] = by["Cluster"].map(CLUSTER_LABELS)
    # does each direction rank wells as the WTF method does? Both are rise-against-rain methods, so
    # some agreement is expected; the question is whether the bracket's ends behave alike.
    rho = {}
    for tag in ("lo", "hi"):
        d = per[[f"Sy_winter_{tag}", "Sy_wtf"]].dropna()
        rho[tag] = (float(d.corr(method="spearman").iloc[0, 1]), len(d)) if len(d) > 3 else (np.nan, 0)
    return per, by, rho


# ── figures ───────────────────────────────────────────────────────────────────────────────────────
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    return plt


def plot_surplus(wells, cl, sy, a: pd.DataFrame) -> None:
    plt = _plt()
    fig, axes = plt.subplots(1, len(a), figsize=(3.1 * len(a), 3.0), dpi=160, sharey=True)
    axes = np.atleast_1d(axes)
    for ax, r in zip(axes, a.itertuples()):
        g = sy[sy["Cluster"] == r.Cluster]
        dh = wells[[c for c in g["col"]]].diff()
        md = dh.mean(axis=1).where(dh.notna().sum(axis=1) >= WB_MIN_WELLS_PER_MONTH)
        P = cl["P_m"].reindex(md.index)
        P_eff = P * (1 - FOREST_INTERCEPTION) if r.Cluster in FOREST_CIDS else P
        d = pd.DataFrame({"x": md, "y": P_eff - cl["PET"].reindex(md.index)}).dropna()
        ax.scatter(d["x"], d["y"], s=6, color="0.35", alpha=0.6, lw=0)
        xs = np.linspace(d["x"].min(), d["x"].max(), 50)
        ax.plot(xs, r.drainage_at_steady_level_m + r.apparent_Sy * xs, color="#b2182b", lw=1.2)
        ax.axhline(0, color="0.7", lw=0.5)
        ax.axvline(0, color="0.7", lw=0.5)
        ax.set_title(f"C{r.Cluster}  Sy$_{{app}}$ = {r.apparent_Sy:.3f}", fontsize=9)
        ax.set_xlabel("mean Δh (m)")
    axes[0].set_ylabel("P$_{eff}$ − PET (m/month)")
    fig.tight_layout()
    fig.savefig(OUT_55_SURPLUS_FIG)
    plt.close(fig)


def plot_law(per: pd.DataFrame) -> None:
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.4), dpi=160)
    ax = axes[0]
    for k in CLUSTERS:
        g = per[per["Cluster"] == k]
        ax.scatter(g["h0_depth_below_ground_m"], g["k_hinge"], s=18, lw=0, label=f"C{k}")
    ax.set_xlabel("h₀ (m below ground)")
    ax.set_ylabel("k above h₀ (/month)")
    ax.legend(fontsize=7, frameon=False)
    ax = axes[1]
    w = per.groupby("Cluster")["threshold_beats_line"].agg(["sum", "size"])
    ax.bar([f"C{k}" for k in w.index], w["sum"] / w["size"], color="#2166ac")
    ax.set_ylabel(f"wells where the threshold beats the line\n(ΔBIC < −{WB_BIC_MARGIN})")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(OUT_55_LAW_FIG)
    plt.close(fig)


def plot_et(dper: pd.DataFrame) -> None:
    plt = _plt()
    fig, ax = plt.subplots(figsize=(5.2, 3.4), dpi=160)
    for k in CLUSTERS:
        g = dper[dper["Cluster"] == k]
        ax.scatter(g["et_pet_year"], g["et_pet_summer"], s=18, lw=0, label=f"C{k}")
    lim = [0.3, 1.2]
    ax.plot(lim, lim, color="0.7", lw=0.6)
    ax.axhline(1, color="0.85", lw=0.5)
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_xlabel("ET/PET, year")
    ax.set_ylabel("ET/PET, summer")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_55_ET_VS_PET_FIG)
    plt.close(fig)


def plot_winter_sy(iper: pd.DataFrame) -> None:
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=160)
    d = iper.sort_values(["Cluster", "Sy_wtf"]).reset_index(drop=True)
    x = np.arange(len(d))
    ax.vlines(x, d["Sy_winter_lo"], d["Sy_winter_hi"], color="0.6", lw=1.2)
    ax.scatter(x, d["Sy_winter_mid"], s=12, color="#2166ac", lw=0, label="bracket midpoint")
    ax.scatter(x, d["Sy_wtf"], s=14, color="#b2182b", marker="x", label="WTF Sy (Script 18)")
    ax.set_xticks([])
    ax.set_xlabel("reference wells, by cluster then WTF Sy")
    ax.set_ylabel("specific yield")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_55_WINTER_SY_FIG)
    plt.close(fig)


# ── main ──────────────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fig", action="store_true")
    args = ap.parse_args()
    banner("55", "Water-balance residual analysis", version=__version__)
    DIR_55.mkdir(parents=True, exist_ok=True)

    phase(1, "Inputs")
    if not OUT_18_WELL_SY_TABLE.is_file():
        warn(f"{OUT_18_WELL_SY_TABLE.name} is absent — there is no defensible default Sy per well")
        note("run Script 18 first; skipping")
        return 0
    cl, wells, sy, win = load_inputs()
    info(f"{len(sy)} reference wells with a Script 18 Sy; climate {cl.index.min():%Y-%m} to "
         f"{cl.index.max():%Y-%m}")
    if win is None:
        warn(f"{OUT_18_WELL_SY_BY_WINDOW.name} is absent — Stage G's split sample will be skipped")
    frames = all_frames(wells, cl, sy)
    info(f"{len(frames)} wells with at least {WB_MIN_MONTHS} aligned months")

    phase(2, "Stage A — the cluster-mean month, and its apparent Sy")
    a = stage_a(wells, cl, sy)
    a.to_csv(OUT_55_SURPLUS_VS_DH, index=False)
    saved(OUT_55_SURPLUS_VS_DH.name)
    for r in a.itertuples():
        step(f"C{r.Cluster}  apparent Sy {r.apparent_Sy:.3f}  (WTF median {r.Sy_wtf_cluster_median:.3f}), "
             f"drainage at a steady level {r.drainage_at_steady_level_m:+.4f} m/month")

    phase(3, "Stage B — the residual drainage law, line and threshold")
    bper, bby, laws = stage_b(frames, sy)
    bper.to_csv(OUT_55_LAW_PER_WELL, index=False)
    saved(f"{OUT_55_LAW_PER_WELL.name} ({len(bper)} wells)")
    bby.to_csv(OUT_55_LAW_BY_CLUSTER, index=False)
    saved(OUT_55_LAW_BY_CLUSTER.name)
    for r in bby.itertuples():
        step(f"C{r.Cluster}  k above h₀ {r.k_hinge_median:.3f}/month, h₀ "
             f"{r.h0_depth_below_ground_m_median:.3f} m below ground, threshold beats the line at "
             f"{r.n_threshold_beats_line} of {r.n_wells}")

    phase(4, "Stage C — the annual water balance from the fitted law")
    c = stage_c(frames, laws)
    c.to_csv(OUT_55_WATER_BALANCE, index=False)
    saved(f"{OUT_55_WATER_BALANCE.name} ({len(c)} well-years, "
          f"{int(c['complete_year'].sum())} complete)")

    phase(5, "Stage I — the winter joint fit of Sy and drainage (before Stage D, which uses its bracket)")
    iper, iby, rho = stage_i(wells, cl, sy)
    iper.to_csv(OUT_55_WINTER_SY_PER_WELL, index=False)
    saved(f"{OUT_55_WINTER_SY_PER_WELL.name} ({len(iper)} wells)")
    iby.to_csv(OUT_55_WINTER_SY_CLUSTER, index=False)
    saved(OUT_55_WINTER_SY_CLUSTER.name)
    for r in iby.itertuples():
        step(f"C{r.Cluster}  winter Sy {r.Sy_winter_lo_median:.3f} – {r.Sy_winter_hi_median:.3f} "
             f"(mid {r.Sy_winter_mid_median:.3f}), WTF {r.Sy_wtf_median:.3f}, "
             f"k {r.k_winter_joint_median:+.3f}")
    result("Spearman of the low-bound Sy against the WTF Sy", f"{rho['lo'][0]:.3f} (n = {rho['lo'][1]})")
    result("Spearman of the high-bound Sy against the WTF Sy", f"{rho['hi'][0]:.3f} (n = {rho['hi'][1]})")

    phase(6, "Stage D — the winter law, ET, and the drainage share of the annual loss")
    dper, dby, et = stage_d(frames, sy, iper)
    dper.to_csv(OUT_55_WINTER_LAW_ET, index=False)
    saved(f"{OUT_55_WINTER_LAW_ET.name} ({len(dper)} wells)")
    et.to_csv(OUT_55_ET_MONTHLY, index_label="month")
    saved(OUT_55_ET_MONTHLY.name)
    for r in dby.itertuples():
        step(f"C{r.Cluster}  ET/PET summer {r.et_pet_summer_median:.3f}, year "
             f"{r.et_pet_year_median:.3f}, drainage share {r.drainage_share_median:.3f}  "
             f"(k winter {r.k_winter_median:.3f})")
    share_med = float(dper["drainage_share"].median())
    result("drainage share of the annual loss, per-well median over the network (the §7.1 basis)",
           f"{share_med:.3f}  (n = {len(dper)} wells)")
    _blo = float(dper["drainage_share_sy_lo"].median())
    _bhi = float(dper["drainage_share_sy_hi"].median())
    result("the same share across the Stage I Sy bracket",
           f"{min(_blo, _bhi):.3f} – {max(_blo, _bhi):.3f}  (a LOWER Sy books a smaller storage "
           f"change, so it leaves MORE of the loss as drainage)")
    note(f"months outside the winter head range, excluded and counted: "
         f"{int(dper['n_months_excluded'].sum())} of {int(dper['n_months'].sum())}")

    phase(7, "Stage E — the sensitivities")
    e = stage_e(wells, cl, sy, dper)
    e.to_csv(OUT_55_SENSITIVITY, index=False)
    saved(f"{OUT_55_SENSITIVITY.name} ({len(e)} rows)")
    for r in e.itertuples():
        if np.isfinite(r.et_pet_summer_median):
            step(f"{r.test}: ET/PET summer {r.et_pet_summer_median:.3f} ({r.n_wells} wells)")

    phase(8, "Stage F — the forest interception closure scan")
    f = stage_f(wells, cl, sy)
    f.to_csv(OUT_55_INTERCEPTION_SCAN, index=False)
    saved(f"{OUT_55_INTERCEPTION_SCAN.name} ({len(f)} rows)")
    for k, g in f.groupby("Cluster"):
        cf = g["interception_closing"].iloc[0]
        at = g[np.isclose(g["interception"], FOREST_INTERCEPTION)]
        step(f"C{k}  ET + interception over PET at the adopted {FOREST_INTERCEPTION:.2f}: "
             f"{at['atmos_loss_over_pet_median'].iloc[0]:.3f}" if len(at) else f"C{k}")
        step(f"      closes at interception "
             + (f"{cf:.3f}" if np.isfinite(cf) else "no crossing in the scanned range"))

    phase(9, "Stage G — the split sample, and the CCW 1989-96 hindcast")
    if win is not None:
        gs = stage_g_split(wells, cl, sy, win)
        gs.to_csv(OUT_55_SPLIT_SAMPLE, index=False)
        saved(f"{OUT_55_SPLIT_SAMPLE.name} ({len(gs)} wells)")
        for d_ in ("fwd", "rev"):
            both = gs[[f"nse_{d_}", f"nse_{d_}_model_A", f"nse_{d_}_model_B"]].dropna()
            if len(both):
                result(f"split-sample median NSE {d_} (water balance / A / B)",
                       f"{both[f'nse_{d_}'].median():.3f} / "
                       f"{both[f'nse_{d_}_model_A'].median():.3f} / "
                       f"{both[f'nse_{d_}_model_B'].median():.3f}   (n = {len(both)})")
        nsk = int((gs["skipped"] != "").sum())
        if nsk:
            note(f"{nsk} wells skipped in at least one direction for want of a windowed Sy")
    else:
        gs = pd.DataFrame()
    gc = stage_g_ccw(wells, cl, sy, laws)
    if not gc.empty:
        gc.to_csv(OUT_55_CCW_HINDCAST, index=False)
        saved(f"{OUT_55_CCW_HINDCAST.name} ({len(gc)} codes)")
        for form in ("line", "threshold", "selected"):
            g = gc[gc["law_form"] == form]
            if len(g):
                result(f"CCW 1989-96 bias on the {form} law, median over {len(g)} codes",
                       f"{g['bias_m'].median():+.3f} m")

    phase(10, "Stage H — the dry-month drainage law")
    dry, thr = dry_months(cl, wells)
    info(f"a dry month is at or below {thr * 1000:.1f} mm; {len(dry)} months in the reference period")
    hper, hby = stage_h(frames, sy, dry, thr)
    hper.to_csv(OUT_55_DRY_LAW_PER_WELL, index=False)
    saved(f"{OUT_55_DRY_LAW_PER_WELL.name} ({len(hper)} wells)")
    hby.to_csv(OUT_55_DRY_LAW_BY_CLUSTER, index=False)
    saved(OUT_55_DRY_LAW_BY_CLUSTER.name)
    for r in hby.itertuples():
        step(f"C{r.Cluster}  k all {r.k_all_median:+.3f}, dry {r.k_dry_all_median:+.3f} "
             f"(R² {r.r2_dry_all_median:.3f}), dry winter {r.k_dry_winter_median:+.3f} "
             f"(R² {r.r2_dry_winter_median:.3f})")
    result("summer share of the dry months", f"{hper['dry_summer_share'].median():.3f}")

    if not args.no_fig:
        plot_surplus(wells, cl, sy, a); saved(OUT_55_SURPLUS_FIG.name)
        plot_law(bper); saved(OUT_55_LAW_FIG.name)
        plot_et(dper); saved(OUT_55_ET_VS_PET_FIG.name)
        plot_winter_sy(iper); saved(OUT_55_WINTER_SY_FIG.name)

    phase(11, "Report numbers")
    rr = ReportNumbers()
    SPEC = "spec NRG_spec_water_balance_diagnostic_2026-11-04"
    MED = ("per-well MEDIAN over the cluster's reference wells, the statistic of the "
           "modelab_drainage_share_*_median_* fields this step is quoted beside")
    for r in bby.itertuples():
        k = int(r.Cluster)
        rr.add(f"wb_k_hinge_C{k}", r.k_hinge_median, unit="1/month",
               note=f"threshold-law k = c/Sy above h0; {MED}; {SPEC}")
        rr.add(f"wb_h0_m_C{k}", r.h0_depth_below_ground_m_median, unit="m",
               note=f"h0, metres BELOW ground; {MED}; {SPEC}")
        rr.add(f"wb_hinge_wells_C{k}", int(r.n_threshold_beats_line), unit="count",
               note=f"wells where the threshold beats the line by more than {WB_BIC_MARGIN} in BIC "
                    f"(h0 counted as a third parameter), of {int(r.n_wells)}; {SPEC}")
    for r in dby.itertuples():
        k = int(r.Cluster)
        rr.add(f"wb_et_pet_summer_C{k}", r.et_pet_summer_median, unit="",
               note=f"ET backed out of the winter law over WB_SUMMER_MONTHS, inside the winter head "
                    f"range; {MED}; {SPEC}")
        rr.add(f"wb_et_pet_year_C{k}", r.et_pet_year_median, unit="",
               note=f"as wb_et_pet_summer_C{k} over every month; {MED}; {SPEC}")
        rr.add(f"wb_drain_share_C{k}", r.drainage_share_median, unit="",
               note=f"drainage share of the annual loss, interception counted as loss; {MED}; {SPEC}")
    rr.add("wb_drain_share_median", share_med, unit="",
           note=f"per-well median of the annual drainage share over the reference network - the "
                f"Paper M §7.1 basis, the same quantity as modelab_drainage_share_A/B_median_all; {SPEC}")
    rr.add("wb_drain_share_median_sy_lo", float(dper["drainage_share_sy_lo"].median()), unit="",
           note=f"the §7.1 share recomputed at the Stage I LOW-bound winter Sy; {SPEC}")
    rr.add("wb_drain_share_median_sy_hi", float(dper["drainage_share_sy_hi"].median()), unit="",
           note=f"the §7.1 share recomputed at the Stage I HIGH-bound winter Sy; {SPEC}")
    for r in f.groupby("Cluster").first().reset_index().itertuples():
        rr.add(f"wb_interception_close_C{int(r.Cluster)}", r.interception_closing, unit="",
               note=f"the interception fraction at which the booked ET + interception equals PET, by linear "
                    f"interpolation on the per-well median ratio; FOREST_INTERCEPTION stays at "
                    f"{FOREST_INTERCEPTION} (D4); {SPEC}")
    if not gs.empty:
        for d_ in ("fwd", "rev"):
            s = gs[f"nse_{d_}"].dropna()
            rr.add(f"wb_nse_{d_}_median", float(s.median()) if len(s) else np.nan, unit="",
                   note=f"split-sample free-run NSE, {'forward' if d_ == 'fwd' else 'reverse'} of "
                        f"MODEL_AB_SPLIT_DATE, Sy from the FITTED window only (D8); median over "
                        f"{len(s)} wells; {SPEC}")
        rr.add("wb_n_split_wells", int(gs[["nse_fwd", "nse_rev"]].notna().any(axis=1).sum()),
               unit="count", note=f"wells scored in at least one direction; {SPEC}")
    if not gc.empty:
        for form, tag in (("line", "line"), ("threshold", "hinge")):
            g = gc[gc["law_form"] == form]
            rr.add(f"wb_ccw_bias_{tag}_m", float(g["bias_m"].median()) if len(g) else np.nan,
                   unit="m", note=f"CCW 1989-96 hindcast bias (modelled - observed), median over the "
                                  f"{len(g)} admitted codes, every well run on the {form} law; "
                                  f"Script 39's codes, datum offsets and censoring, and its forcing - "
                                  f"the committed climate record with 1941-06 dropped, from the record's "
                                  f"first month; {SPEC}")
        sel = gc[gc["law_form"] == "selected"]
        rr.add("wb_ccw_bias_selected_m", float(sel["bias_m"].median()) if len(sel) else np.nan,
               unit="m", note=f"as wb_ccw_bias_line_m with each well on the law BIC selected for it; {SPEC}")
        rr.add("wb_n_ccw_wells", int(gc["code"].nunique()), unit="count",
               note=f"CCW codes admitted and scored; {SPEC}")
    for r in e.itertuples():
        if r.test == "C1 without CEH11" and np.isfinite(r.et_pet_summer_median):
            rr.add("wb_c1_no_ceh11_et_pet_summer", r.et_pet_summer_median, unit="",
                   note=f"C1's summer ET/PET with the lake-nearest well dropped - the test of whether "
                        f"C1's shortfall is a lake-proximity effect; {SPEC}")
        if r.test.startswith("C1 winter law on below-ground") and np.isfinite(r.et_pet_summer_median):
            rr.add("wb_c1_below_ground_et_pet_summer", r.et_pet_summer_median, unit="",
                   note=f"C1's summer ET/PET with the winter law fitted on below-ground months only "
                        f"- the test of whether ponding explains the shortfall; {SPEC}")
    for r in hby.itertuples():
        k = int(r.Cluster)
        rr.add(f"wb_k_dry_all_C{k}", r.k_dry_all_median, unit="1/month",
               note=f"line-law k on the dry months of every season - an UPPER bound, about half its "
                    f"months being summer; {MED}; {SPEC}")
        rr.add(f"wb_k_dry_winter_C{k}", r.k_dry_winter_median, unit="1/month",
               note=f"line-law k on the dry months of WB_DRY_WINTER_MONTHS - the cleaner estimate; "
                    f"{MED}; {SPEC}")
        rr.add(f"wb_R2_dry_all_C{k}", r.r2_dry_all_median, unit="",
               note=f"R² of the dry all-season fit; {MED}; {SPEC}")
    rr.add("wb_dry_summer_share", float(hper["dry_summer_share"].median()), unit="",
           note=f"share of the dry months falling in WB_SUMMER_MONTHS; {SPEC}")
    for r in iby.itertuples():
        k = int(r.Cluster)
        rr.add(f"wb_sy_winter_lo_C{k}", r.Sy_winter_lo_median, unit="",
               note=f"winter joint-fit Sy, LOW bound (P on Delta_h; level error biases it low); "
                    f"{MED}; {SPEC}")
        rr.add(f"wb_sy_winter_hi_C{k}", r.Sy_winter_hi_median, unit="",
               note=f"winter joint-fit Sy, HIGH bound (Delta_h on P; rain error biases it high); "
                    f"{MED}; {SPEC}")
        rr.add(f"wb_sy_winter_mid_C{k}", r.Sy_winter_mid_median, unit="",
               note=f"geometric mean of the two bounds; {MED}; {SPEC}")
        rr.add(f"wb_k_winter_joint_C{k}", r.k_winter_joint_median, unit="1/month",
               note=f"drainage k from the winter joint fit, at the high-bound Sy; {MED}; {SPEC}")
    rr.add("wb_sy_winter_spearman_lo", rho["lo"][0], unit="",
           note=f"Spearman of the low-bound winter Sy against Script 18's WTF Sy over "
                f"{rho['lo'][1]} wells; {SPEC}")
    rr.add("wb_sy_winter_spearman_hi", rho["hi"][0], unit="",
           note=f"as wb_sy_winter_spearman_lo for the high bound over {rho['hi'][1]} wells; {SPEC}")
    rr.add("wb_n_wells", int(len(bper)), unit="count",
           note=f"reference wells with a Script 18 Sy and at least {WB_MIN_MONTHS} aligned months; {SPEC}")
    rr.save(OUT_55_REPORT_NUMBERS)
    saved(f"{OUT_55_REPORT_NUMBERS.name} ({len(rr.rows)} rows)")
    done("55")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
