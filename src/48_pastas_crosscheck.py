#!/usr/bin/env python3
"""
48_pastas_crosscheck.py — the per-well SSM against an independent transfer-function
model (Pastas): gain, response time, evaporation factor and base level, well by well
====================================================================================
WHAT THIS IS
  The state-space model (Script 03) is a linear-reservoir transfer-function-noise
  model at monthly resolution. Its diagnostic form, Model B (free intercept), is
  term for term the exponential-response recharge model of Pastas (Collenteur et
  al., 2019): the response time is -1/ln(1 - beta_3) months, the steady gain
  beta_1/beta_3, the evaporation factor -beta_2/beta_1, and the fitted constant is
  the level at which the fitted drainage is zero, -(z0 - alpha_B/beta_3). The
  published form, Model A (no intercept, drainage evaluated at DRAINAGE_DATUM), has
  no Pastas counterpart: its beta_3 carries the datum (D-007, D-109).

  This step fits Pastas at each reference well on the same monthly record — once
  without a noise model (comparable to the OLS fits) and once with Pastas's AR(1)
  noise model (honest standard errors) — and sets the four Pastas quantities beside
  Model B (the counterpart) and Model A (datum-conditional, for reference). Two
  independent codes on the same record: where they agree the SSM coefficients
  inherit Pastas's standing; where they do not, the disagreement is emitted.

  Monthly data in a daily engine: the dipwell reading is the end-of-month level, so
  heads are stamped at month-end; the RAF Valley monthly totals are spread evenly
  over each month's days as daily stresses. Pastas's parameters come out per day
  and are converted to per month with config.DAYS_PER_MONTH.

INPUTS — all committed
  01_wells_all.csv ................. monthly levels, m relative to ground
  01_climate.csv ................... monthly P_m and PET, m/month
  03_master_data.csv ............... the 66 reference wells: cluster, Model A beta
  03_16_model_b_persistence.csv .... the per-well Model B rows (alpha_B, beta_i_B) and
                                     their window; the centroid rows for the synthetic wells
  03_15_per_well_window_sensitivity.csv  Model A per well on the full record

OUTPUTS — outputs/48_pastas_crosscheck/
  48_01_pastas_per_well.csv ........ per well: Pastas (no noise / AR1 noise) gain,
                                     response time, f, base level, R2, standard
                                     errors, and the SSM coefficients they imply
                                     (beta_3 = 1 - exp(-1/a), beta_1 = gain*beta_3,
                                     beta_2 = -f*beta_1); Model B and Model A beside them
  48_02_pastas_agreement.csv ....... per comparison and quantity: Pearson r,
                                     Spearman rho, median Pastas:SSM ratio with
                                     p16/p84, n — overall and per cluster
  48_03_synthetic_recovery.csv ..... the unit conversion checked: a Model B well
                                     synthesised from each cluster centroid's
                                     committed coefficients on the real climate,
                                     refitted by Pastas; true against recovered
  48_01_pastas_vs_ssm.png .......... portrait, 4 x 2: beta_1, beta_2, beta_3, then
                                     gain, response time, f, base level; Pastas (AR1)
                                     against Model B (filled) and Model A (hollow);
                                     wells not identified on the window crossed
  48_report_numbers.csv ............ the headline agreement (r, median ratio) for
                                     the four quantities, n, the Pastas version

USAGE
  python3 run_analysis.py --step 48        # part of --full
  python3 src/48_pastas_crosscheck.py      # standalone
  python3 src/48_pastas_crosscheck.py --no-fig
"""
from __future__ import annotations
__version__ = "1.3.0"  # Hollingham (2026) - 2026-09-24. Martin: "the C4 well records are longer
#   than 100 months". Two bases per well: comparison_window (the report's per-well
#   basis, Model A from 03_master_data and Model B from 03_16) and full_record (Model
#   A from 03_15, Model B fitted here with fit_ssm_intercept, Pastas on every month).
#   48_01 is long (well x basis), 48_02 and the report numbers carry both (full-record
#   keys suffixed _full), the figure shows config.PASTAS_FIGURE_BASIS. On the full
#   record six of the nine C4 wells identify and the two codes agree there.
# 1.2.0  # Hollingham (2026) - 2026-09-24. Martin: the figure must be portrait,
#   and C4's divergence is not the canopy. Per-well identifiability flag: a Pastas
#   response time longer than PASTAS_IDENT_EFOLD_WINDOW_FRAC of the fitted months,
#   or with a relative SE above PASTAS_IDENT_MAX_REL_SE, is not identified on the
#   window (gain, response time and base level trade off; C4 is where it bites);
#   the agreement table gains an "identified" group, the report numbers carry both
#   groups and the per-cluster counts, the figure is 4 x 2 portrait at text width
#   with the unidentified wells crossed and the panel statistics on the identified
#   set. Same fits, same numbers.
# 1.1.0  # Hollingham (2026) - 2026-09-24. Martin: "no beta_3 comparison" -
#   the figure and the agreement table now carry beta_1, beta_2, beta_3 as well as
#   Pastas's native four, with Pastas's parameters converted exactly to the SSM's
#   coefficients (beta_3 = 1 - exp(-1/a), beta_1 = gain*beta_3, beta_2 = -f*beta_1);
#   three synthetic ratios more in the report numbers. Same fits, same numbers.
# 1.0.0  # Hollingham (2026) - 2026-09-24. First issue (Martin: "lets
#   implement the pastas check"; default tier, Model A and Model B both compared).
#   Pastas 2.0: stress models take the Model as their first argument; the noise
#   model is added with add_noisemodel(ArNoiseModel(model)). No output of any
#   other script changes.

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402
from scipy import stats as scipy_stats                        # noqa: E402

from utils.paths import (                                     # noqa: E402
    DIR_48, OUT_48_PER_WELL, OUT_48_AGREEMENT, OUT_48_SYNTHETIC, OUT_48_FIG, OUT_48_REPORT_NUMBERS,
    INT_WELLS_ALL, INT_CLIMATE, INT_MASTER_DATA, OUT_03_MODEL_B_PERSISTENCE,
    OUT_03_PER_WELL_WINDOW_SENS,
)
from utils.config import (                                    # noqa: E402
    DRAINAGE_DATUM, DAYS_PER_MONTH, PASTAS_RESPONSE, PASTAS_WARMUP_YEARS,
    PASTAS_IDENT_EFOLD_WINDOW_FRAC, PASTAS_IDENT_MAX_REL_SE, PASTAS_FIGURE_BASIS,
    HEADLINE_LAG, CLUSTER_LABELS, CLUSTER_COLOURS,
)
from utils.render_utils import MPL_DEFAULTS                   # noqa: E402
from utils.data_utils import normalize_well_name              # noqa: E402
from utils.model_utils import fit_ssm_intercept               # noqa: E402
from utils.report_numbers_utils import ReportNumbers          # noqa: E402
from utils.console_utils import (                             # noqa: E402
    banner, done, info, phase, result, saved, step, track, warn,
)

# The four quantities compared, with the SSM columns they are read from.
QUANTITIES = ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage",
              "gain", "efold_months", "f_evap", "base_level_m")
BETAS = QUANTITIES[:3]
FITS = ("pastas", "pastas_ar1")


# ──────────────────────────────────────────────────────────────────────────────
# Inputs
# ──────────────────────────────────────────────────────────────────────────────
def load_inputs():
    lev = pd.read_csv(INT_WELLS_ALL, index_col=0)
    lev.index = pd.to_datetime(lev.index)
    cl = pd.read_csv(INT_CLIMATE, index_col=0)
    cl.index = pd.to_datetime(cl.index)
    master = pd.read_csv(INT_MASTER_DATA)
    mb_all = pd.read_csv(OUT_03_MODEL_B_PERSISTENCE)
    mb = mb_all[mb_all["level"] == "well"].copy()
    mb["_n"] = mb["well"].astype(str).apply(normalize_well_name)
    master["_n"] = master["Name_Original"].astype(str).apply(normalize_well_name)
    lev_cols = {normalize_well_name(c): c for c in lev.columns}
    ws = pd.read_csv(OUT_03_PER_WELL_WINDOW_SENS)
    ws = ws[ws["basis"] == "full_record"].copy()
    ws["_n"] = ws["Name_Original"].astype(str).apply(normalize_well_name)
    return lev, lev_cols, cl, master, mb.set_index("_n"), mb_all, ws.set_index("_n")


def daily_stresses(cl: pd.DataFrame, first_head: pd.Timestamp):
    """The monthly P and PET totals spread evenly over each month's days (m/day),
    from PASTAS_WARMUP_YEARS before the first head to the end of the climate record.
    A stress stamped YYYY-MM-01 is the total for that month (Script 01 convention)."""
    start = pd.Timestamp(year=first_head.year - PASTAS_WARMUP_YEARS, month=1, day=1)
    c = cl.loc[start:].dropna(subset=["P_m", "PET"])
    days = pd.date_range(c.index[0], c.index[-1] + pd.offsets.MonthEnd(0), freq="D")
    per = days.to_period("M")
    ndays = pd.Series(days, index=days).groupby(per).size()
    pm = c["P_m"].copy(); pm.index = pm.index.to_period("M")
    em = c["PET"].copy(); em.index = em.index.to_period("M")
    P = pd.Series((pm.reindex(per) / ndays.reindex(per)).to_numpy(), index=days, name="P")
    E = pd.Series((em.reindex(per) / ndays.reindex(per)).to_numpy(), index=days, name="E")
    return P.dropna(), E.dropna()


# ──────────────────────────────────────────────────────────────────────────────
# The fits
# ──────────────────────────────────────────────────────────────────────────────
def _rfunc(ps):
    try:
        return getattr(ps, PASTAS_RESPONSE)()
    except AttributeError as exc:
        raise ValueError(f"config.PASTAS_RESPONSE = {PASTAS_RESPONSE!r} is not a Pastas "
                         "response function") from exc


def fit_pastas(ps, head: pd.Series, P: pd.Series, E: pd.Series, name: str,
               noise: bool, tmin=None, tmax=None) -> dict:
    """One Pastas fit: linear recharge R = P + f·E through the configured response,
    plus a constant, on [tmin, tmax] — the window Script 03's per-well fits used, so
    the three models see the same months. Parameters converted to per-month units."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ml = ps.Model(head, name=name)
        ps.RechargeModel(ml, P, E, rfunc=_rfunc(ps), name="rch", recharge=ps.rch.Linear())
        if noise:
            ml.add_noisemodel(ps.ArNoiseModel(ml))
        ml.solve(tmin=tmin, tmax=tmax, report=False)
    p = ml.parameters
    opt, se = p["optimal"], p["stderr"]
    gain = float(opt["rch_A"]) / DAYS_PER_MONTH
    efold = float(opt["rch_a"]) / DAYS_PER_MONTH
    f = float(opt["rch_f"])
    # The SSM's coefficients implied by Pastas's parameters: the monthly
    # reservoir with e-fold a months loses the fraction 1 - exp(-1/a) per month
    # (beta_3); the steady gain is beta_1/beta_3; f = -beta_2/beta_1.
    beta_3 = 1.0 - np.exp(-1.0 / efold) if efold > 0 else np.nan
    beta_1 = gain * beta_3
    beta_2 = -f * beta_1
    out = {
        "gain": gain,                                           # m per (m/month)
        "gain_se": float(se["rch_A"]) / DAYS_PER_MONTH,
        "efold_months": float(opt["rch_a"]) / DAYS_PER_MONTH,
        "efold_months_se": float(se["rch_a"]) / DAYS_PER_MONTH,
        "f_evap": float(opt["rch_f"]),
        "f_evap_se": float(se["rch_f"]),
        "base_level_m": float(opt["constant_d"]),
        "base_level_m_se": float(se["constant_d"]),
        "beta_1_recharge": beta_1,
        "beta_2_atmospheric_draw": beta_2,
        "beta_3_drainage": beta_3,
        "R2": float(ml.stats.rsq()),
        "n_obs": int(ml.observations().shape[0]),
    }
    if noise:
        out["ar1_alpha_days"] = float(opt.get("noise_alpha", np.nan))
    return out


def _betas_to_quantities(prefix: str, b1: float, b2: float, b3: float, base: float, r2: float) -> dict:
    """The four Pastas quantities from three SSM coefficients and a base level.
    efold uses the exact discrete-to-continuous conversion -1/ln(1 - beta_3);
    1/beta_3 is emitted beside it for the documents that quote it."""
    return {
        f"{prefix}_beta_1_recharge": b1, f"{prefix}_beta_2_atmospheric_draw": b2, f"{prefix}_beta_3_drainage": b3,
        f"{prefix}_gain": b1 / b3 if b3 > 0 else np.nan,
        f"{prefix}_efold_months": -1.0 / np.log1p(-b3) if 0 < b3 < 1 else np.nan,
        f"{prefix}_inv_beta3_months": 1.0 / b3 if b3 > 0 else np.nan,
        f"{prefix}_f_evap": -b2 / b1 if b1 != 0 else np.nan,
        f"{prefix}_base_level_m": base,
        f"{prefix}_R2": r2,
    }


def ssm_counterparts_window(master_row: pd.Series, mb_row: pd.Series | None) -> dict:
    """Comparison-window basis: Model A from 03_master_data, Model B from 03_16."""
    out = _betas_to_quantities("ssmA", float(master_row["beta_1_recharge"]),
                               float(master_row["beta_2_atmospheric_draw"]),
                               float(master_row["beta_3_drainage"]), -float(DRAINAGE_DATUM),
                               float(master_row.get("Model_R2", np.nan)))
    if mb_row is None:
        out.update({k: np.nan for k in _betas_to_quantities("ssmB", 1, 1, 0.5, 0, 0)})
        return out
    a, c1, c2, c3 = (float(mb_row["alpha_B"]), float(mb_row["beta_1_B"]),
                     float(mb_row["beta_2_B"]), float(mb_row["beta_3_B"]))
    z0 = float(mb_row["drainage_datum_m"])
    out.update(_betas_to_quantities("ssmB", c1, c2, c3, -(z0 - a / c3) if c3 > 0 else np.nan,
                                    float(mb_row["R2_B"])))
    return out


def ssm_counterparts_full(ws_row: pd.Series | None, head_full: pd.Series, cl: pd.DataFrame) -> dict:
    """Full-record basis: Model A from 03_15 (basis == full_record), Model B fitted
    here on the full record with the shared fit_ssm_intercept (Script 03 emits Model B
    per well on the comparison window only)."""
    if ws_row is None:
        out = {k: np.nan for k in _betas_to_quantities("ssmA", 1, 1, 0.5, 0, 0)}
    else:
        out = _betas_to_quantities("ssmA", float(ws_row["beta_1_recharge"]),
                                   float(ws_row["beta_2_atmospheric_draw"]),
                                   float(ws_row["beta_3_drainage"]), -float(DRAINAGE_DATUM),
                                   float(ws_row["R2"]))
    fb = fit_ssm_intercept(head_full, cl, lag=HEADLINE_LAG, window=None)
    if fb is None:
        out.update({k: np.nan for k in _betas_to_quantities("ssmB", 1, 1, 0.5, 0, 0)})
        return out
    a, c1, c2, c3 = (float(fb["alpha"]), float(fb["beta_1_recharge"]),
                     float(fb["beta_2_atmospheric_draw"]), float(fb["beta_3_drainage"]))
    out.update(_betas_to_quantities("ssmB", c1, c2, c3,
                                    -(float(DRAINAGE_DATUM) - a / c3) if c3 > 0 else np.nan,
                                    float(fb.get("R2", np.nan))))
    return out


def per_well_table(ps, lev, lev_cols, cl, master, mb, ws, P, E) -> pd.DataFrame:
    """One row per well and basis. comparison_window: the months Script 03's per-well
    fits used (tmin/tmax from 03_16), the report's per-well basis. full_record: every
    month of the well, the basis on which a slow response can be identified."""
    wells = master.sort_values("Name_Original")
    rows = []
    for w in track(wells.to_dict("records"), lambda r: r["Name_Original"]):
        n = w["_n"]
        if n not in lev_cols:
            warn(f"{w['Name_Original']}: no level column — skipped")
            continue
        head_raw = lev[lev_cols[n]].dropna().copy()
        head = head_raw.copy()
        head.index = head.index + pd.offsets.MonthEnd(0)     # the reading is the end-of-month level
        base = {"well": w["Name_Original"], "Cluster": int(w["Cluster"]),
                "Cluster_Label": CLUSTER_LABELS.get(int(w["Cluster"]), f"C{int(w['Cluster'])}")}
        bases = []
        if n in mb.index:
            tmin = pd.Timestamp(str(mb.loc[n, "fit_start"])) + pd.offsets.MonthEnd(0)
            tmax = pd.Timestamp(str(mb.loc[n, "fit_end"])) + pd.offsets.MonthEnd(0)
            bases.append(("comparison_window", tmin, tmax,
                          {"fit_start": str(mb.loc[n, "fit_start"]), "fit_end": str(mb.loc[n, "fit_end"])},
                          ssm_counterparts_window(pd.Series(w), mb.loc[n])))
        bases.append(("full_record", None, None,
                      {"fit_start": head_raw.index.min().strftime("%Y-%m"), "fit_end": head_raw.index.max().strftime("%Y-%m")},
                      ssm_counterparts_full(ws.loc[n] if n in ws.index else None, head_raw, cl)))
        for basis, tmin, tmax, span, ssm in bases:
            row = dict(base); row["basis"] = basis; row.update(span)
            for fit, noise in (("pastas", False), ("pastas_ar1", True)):
                try:
                    r = fit_pastas(ps, head, P, E, f"{w['Name_Original']}_{basis}_{fit}", noise, tmin, tmax)
                except Exception as exc:                      # noqa: BLE001 — one well must not stop the table
                    warn(f"{w['Name_Original']} {basis} {fit}: {exc}")
                    r = {}
                row.update({f"{fit}_{k}": v for k, v in r.items()})
            row.update(ssm)
            rows.append(row)
    df = pd.DataFrame(rows)
    # Identifiability on the fitted months: a response time longer than
    # PASTAS_IDENT_EFOLD_WINDOW_FRAC of them never contains a full recession, and
    # gain, response time and base level then trade off; the relative standard
    # error on the response time is the other symptom.
    n_win = df["pastas_ar1_n_obs"]
    rel_se = df["pastas_ar1_efold_months_se"] / df["pastas_ar1_efold_months"]
    df["identified"] = ((df["pastas_ar1_efold_months"] <= PASTAS_IDENT_EFOLD_WINDOW_FRAC * n_win)
                        & (rel_se <= PASTAS_IDENT_MAX_REL_SE))
    df["ident_reason"] = np.where(df["identified"], "",
                                  np.where(df["pastas_ar1_efold_months"] > PASTAS_IDENT_EFOLD_WINDOW_FRAC * n_win,
                                           "response time longer than the window allows", "response time SE too large"))
    return df


# ──────────────────────────────────────────────────────────────────────────────
# The conversion, verified: Pastas on a well the SSM generated
# ──────────────────────────────────────────────────────────────────────────────
def synthetic_recovery(ps, cl: pd.DataFrame, mb_all: pd.DataFrame, P: pd.Series, E: pd.Series,
                       head_index: pd.DatetimeIndex) -> pd.DataFrame:
    """For each cluster centroid's committed Model B coefficients, generate the
    noise-free monthly series h_t = h_{t-1} + b1·P_t − b2·PET_t − b3·(z0 + h_{t-1}) + α
    on the real climate, stamp it like the record, fit Pastas, and set the
    recovered gain, e-fold, f and base level beside the values the generating
    coefficients imply. If the conversion is right the ratios are 1; any offset the
    real wells then show is a difference between the two fitting approaches, not
    the units."""
    cent = mb_all[mb_all["level"] == "centroid"]
    rows = []
    for _, c in cent.iterrows():
        b1, b2, b3, a, z0 = (float(c["beta_1_B"]), float(c["beta_2_B"]), float(c["beta_3_B"]),
                             float(c["alpha_B"]), float(c["drainage_datum_m"]))
        h = [-(z0 - a / b3)]                                  # start at the model's own equilibrium
        for t in range(1, len(cl)):
            h.append(h[-1] + b1 * cl["P_m"].iloc[t] - b2 * cl["PET"].iloc[t] - b3 * (z0 + h[-1]) + a)
        H = pd.Series(h, index=cl.index).reindex(head_index).dropna()
        H.index = H.index + pd.offsets.MonthEnd(0)
        r = fit_pastas(ps, H, P, E, f"synthetic_C{int(c['Cluster'])}", noise=False)
        true = {"beta_1_recharge": b1, "beta_2_atmospheric_draw": b2, "beta_3_drainage": b3,
                "gain": b1 / b3, "efold_months": -1.0 / np.log1p(-b3), "f_evap": -b2 / b1,
                "base_level_m": -(z0 - a / b3)}
        row = {"Cluster": int(c["Cluster"]), "Cluster_Label": c["Cluster_Label"], "n_months": len(H)}
        for q in QUANTITIES:
            row[f"true_{q}"] = true[q]
            row[f"pastas_{q}"] = r[q]
            row[f"ratio_{q}"] = r[q] / true[q] if q != "base_level_m" else np.nan
            row[f"diff_{q}"] = r[q] - true[q]
        row["pastas_R2"] = r["R2"]
        rows.append(row)
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# Agreement
# ──────────────────────────────────────────────────────────────────────────────
def agreement(df_all: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for basis, df in df_all.groupby("basis"):
        rows.extend(_agreement_one(df, basis))
    return pd.DataFrame(rows)


def _agreement_one(df: pd.DataFrame, basis: str) -> list:
    rows = []
    groups = ([("all", df), ("identified", df[df["identified"]])]
              + [(f"C{c}", g) for c, g in df.groupby("Cluster")])
    for fit in FITS:
        for model in ("ssmB", "ssmA"):
            for q in QUANTITIES:
                x_col, y_col = f"{model}_{q}", f"{fit}_{q}"
                for label, g in groups:
                    d = g[[x_col, y_col]].replace([np.inf, -np.inf], np.nan).dropna()
                    if len(d) < 3:
                        continue
                    x, y = d[x_col].to_numpy(), d[y_col].to_numpy()
                    # Model A's base level is the datum at every well: no correlation is defined
                    # (the std is float noise on a constant, hence a tolerance, not == 0).
                    constant = np.nanstd(x) < 1e-9 * max(1.0, abs(np.nanmean(x))) or np.nanstd(y) < 1e-9 * max(1.0, abs(np.nanmean(y)))
                    ratio = y / x if q != "base_level_m" else np.full(len(x), np.nan)
                    rows.append({
                        "basis": basis, "fit": fit, "ssm_model": model, "quantity": q, "group": label, "n": len(d),
                        "pearson_r": np.nan if constant else float(np.corrcoef(x, y)[0, 1]),
                        "spearman_rho": np.nan if constant else float(scipy_stats.spearmanr(x, y).correlation),
                        "median_ratio_pastas_over_ssm": float(np.nanmedian(ratio)) if np.isfinite(ratio).any() else np.nan,
                        "ratio_p16": float(np.nanpercentile(ratio, 16)) if np.isfinite(ratio).any() else np.nan,
                        "ratio_p84": float(np.nanpercentile(ratio, 84)) if np.isfinite(ratio).any() else np.nan,
                        "median_difference": float(np.median(y - x)),
                        "rmse": float(np.sqrt(np.mean((y - x) ** 2))),
                    })
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# Figure
# ──────────────────────────────────────────────────────────────────────────────
def plot(df_all: pd.DataFrame, agree_all: pd.DataFrame) -> None:
    """Portrait, 4 x 2, at the report's 15.8 cm text width: the SSM's coefficients
    (top three panels), Pastas's native four, and the legend cell. Filled =
    Model B, hollow = Model A; a well not identified on the window is crossed."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(MPL_DEFAULTS)
    titles = {"beta_1_recharge": "β₁ recharge (m per m of rain)",
              "beta_2_atmospheric_draw": "β₂ atmospheric draw (m per m of PET)",
              "beta_3_drainage": "β₃ drainage (month⁻¹)",
              "gain": "steady gain β₁/β₃ (m per m/month)",
              "efold_months": "response time −1/ln(1−β₃) (months)",
              "f_evap": "evaporation factor f = −β₂/β₁",
              "base_level_m": "base level (m, 0 = ground)"}
    logscale = {"beta_3_drainage", "gain", "efold_months"}
    df = df_all[df_all["basis"] == PASTAS_FIGURE_BASIS]
    agree = agree_all[agree_all["basis"] == PASTAS_FIGURE_BASIS]
    fig, axes = plt.subplots(4, 2, figsize=(7.5, 13.5), dpi=160)
    flat = axes.ravel()
    panels = list(zip(flat[:7], QUANTITIES))
    ident = df["identified"].astype(bool)
    for ax, q in panels:
        for c, g in df.groupby("Cluster"):
            col = CLUSTER_COLOURS.get(int(c), "0.3")
            ok = ident.loc[g.index]
            ax.scatter(g.loc[ok, f"ssmB_{q}"], g.loc[ok, f"pastas_ar1_{q}"], s=20, color=col, edgecolors="k",
                       linewidths=0.4, label=CLUSTER_LABELS.get(int(c), f"C{c}"), zorder=3)
            ax.scatter(g.loc[~ok, f"ssmB_{q}"], g.loc[~ok, f"pastas_ar1_{q}"], s=34, marker="x", color=col,
                       linewidths=1.0, zorder=4)
            if q != "base_level_m":
                ax.scatter(g[f"ssmA_{q}"], g[f"pastas_ar1_{q}"], s=20, facecolors="none",
                           edgecolors=col, linewidths=0.7, zorder=2)
        both = pd.concat([df[f"ssmB_{q}"], df[f"pastas_ar1_{q}"]]).replace([np.inf, -np.inf], np.nan).dropna()
        both = both[both > 0] if q in logscale else both
        lo, hi = np.nanpercentile(both, [1, 99])
        pad = 0.05 * (hi - lo)
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], "k--", lw=0.8, zorder=1)
        a = agree[(agree.fit == "pastas_ar1") & (agree.ssm_model == "ssmB") & (agree.quantity == q) & (agree.group == "identified")]
        if len(a):
            r = a.iloc[0]
            ax.set_title(f"{titles[q]}\nidentified wells vs Model B: ρ = {r.spearman_rho:.2f}, n = {int(r.n)}"
                         + ("" if q == "base_level_m" else f", median ratio {r.median_ratio_pastas_over_ssm:.2f}"),
                         fontsize=7.5)
        ax.set_xlabel("SSM — Model B filled, Model A hollow", fontsize=7)
        ax.set_ylabel("Pastas (AR1 noise)", fontsize=7)
        ax.tick_params(labelsize=7)
        if q in logscale:
            ax.set_xscale("log"); ax.set_yscale("log")
    ax = flat[7]; ax.axis("off")
    h, l = flat[0].get_legend_handles_labels()
    ax.legend(h, l, loc="upper left", fontsize=7, title="cluster", title_fontsize=7)
    n_id = int(ident.sum())
    ax.text(0.02, 0.50, f"× — not identified on the window\n({len(df) - n_id} of {len(df)} wells: response time\n"
                        f"longer than {PASTAS_IDENT_EFOLD_WINDOW_FRAC:g} × the fitted months, or its\n"
                        f"relative SE above {PASTAS_IDENT_MAX_REL_SE:g}); excluded from\nthe panel statistics.\n\n"
                        "Top: the SSM's coefficients, from\nPastas's parameters (β₃ = 1 − e^(−1/a),\nβ₁ = gain·β₃, β₂ = −f·β₁).\n"
                        "Bottom: Pastas's own parameters.\nDashed: 1:1. Model A's β₃ carries the\ndatum; Model B is the exact counterpart.",
            fontsize=7, va="top", transform=ax.transAxes)
    fig.suptitle(f"The per-well SSM against Pastas on the same monthly record ({PASTAS_FIGURE_BASIS.replace('_', ' ')})", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT_48_FIG, dpi=160)
    plt.close(fig)
    saved(OUT_48_FIG.name)


# ──────────────────────────────────────────────────────────────────────────────
def main(no_fig: bool = False) -> int:
    banner("48", "Pastas cross-check of the per-well SSM", version=__version__)
    try:
        import pastas as ps
    except ImportError:
        warn("pastas is not importable — install it in the venv (requirements.txt: "
             "pastas, tqdm) and re-record the environment; step skipped")
        return 1
    ps.set_log_level("ERROR")
    DIR_48.mkdir(parents=True, exist_ok=True)

    phase(1, "Inputs: the monthly record, the climate, Model A and Model B")
    lev, lev_cols, cl, master, mb, mb_all, ws = load_inputs()
    info(f"{len(master)} reference wells; Model B rows for {master['_n'].isin(mb.index).sum()}; "
         f"Pastas {ps.__version__}, response {PASTAS_RESPONSE}")
    first = min(lev[lev_cols[n]].dropna().index.min() for n in master["_n"] if n in lev_cols)
    P, E = daily_stresses(cl, first)
    info(f"daily stresses {P.index[0].date()} to {P.index[-1].date()} "
         f"({PASTAS_WARMUP_YEARS} y warm-up before the first head)")

    phase(2, "The unit conversion, verified on wells the SSM generated")
    syn = synthetic_recovery(ps, cl.loc[P.index[0]:].dropna(subset=["P_m", "PET"]), mb_all, P, E,
                             lev.index[lev.index >= first])
    syn.to_csv(OUT_48_SYNTHETIC, index=False)
    saved(f"{OUT_48_SYNTHETIC.name} ({len(syn)} centroids)")
    for _, r in syn.iterrows():
        step(f"{r['Cluster_Label']:22s} recovered/true: gain {r['ratio_gain']:.3f}, e-fold {r['ratio_efold_months']:.3f}, "
             f"f {r['ratio_f_evap']:.3f}, base {r['diff_base_level_m']:+.3f} m (R² {r['pastas_R2']:.4f})")

    phase(3, "Pastas at each well, without and with the AR(1) noise model")
    df = per_well_table(ps, lev, lev_cols, cl, master, mb, ws, P, E)
    df.to_csv(OUT_48_PER_WELL, index=False)
    saved(f"{OUT_48_PER_WELL.name} ({len(df)} wells)")

    for basis, g in df.groupby("basis"):
        info(f"{basis}: {int(g['identified'].sum())} of {len(g)} wells identified; not identified: "
             + (", ".join(g.loc[~g["identified"], "well"].astype(str)) or "none"))

    phase(4, "Agreement")
    agree = agreement(df)
    agree.to_csv(OUT_48_AGREEMENT, index=False)
    saved(f"{OUT_48_AGREEMENT.name} ({len(agree)} rows)")
    for basis in df["basis"].unique():
      for q in QUANTITIES:
        a = agree[(agree.basis == basis) & (agree.fit == "pastas_ar1") & (agree.ssm_model == "ssmB") & (agree.quantity == q) & (agree.group == "identified")]
        if len(a):
            r = a.iloc[0]
            step(f"{basis:18s} {q:24s} identified, Pastas(AR1) vs Model B: r = {r.pearson_r:+.3f}, ρ = {r.spearman_rho:+.3f}, "
                 + (f"median ratio {r.median_ratio_pastas_over_ssm:.3f} [{r.ratio_p16:.2f}, {r.ratio_p84:.2f}]"
                    if q != "base_level_m" else f"median difference {r.median_difference:+.3f} m")
                 + f", n = {int(r.n)}")

    phase(5, "Report numbers")
    rr = ReportNumbers()
    rr.add("pastas_version", ps.__version__, unit="", note="Pastas release the cross-check ran on")
    rr.add("pastas_n_wells", int(df["well"].nunique()), unit="wells",
           note="reference wells with a converged Pastas AR(1) fit")
    for basis, g in df.groupby("basis"):
        rr.add(f"pastas_n_identified_{basis}", int(g["identified"].sum()), unit="wells",
               note=f"{basis}: wells whose response time is identified on the fitted months (e-fold <= {PASTAS_IDENT_EFOLD_WINDOW_FRAC} x n and relative SE <= {PASTAS_IDENT_MAX_REL_SE})")
        for c, gc in g.groupby("Cluster_Label"):
            rr.add(f"pastas_n_not_identified_C{gc['Cluster'].iloc[0]}_{basis}", int((~gc["identified"]).sum()), unit="wells",
                   note=f"{basis}, {c}: wells not identified (of {len(gc)})")
    for basis in df["basis"].unique():
      bsuf = "" if basis == "comparison_window" else "_full"
      for grp, suffix in (("all", ""), ("identified", "_identified")):
        for q in QUANTITIES:
            for model in ("ssmB", "ssmA"):
                a = agree[(agree.basis == basis) & (agree.fit == "pastas_ar1") & (agree.ssm_model == model) & (agree.quantity == q) & (agree.group == grp)]
                if not len(a):
                    continue
                r = a.iloc[0]
                rr.add(f"pastas_vs_{model}_{q}_r{suffix}{bsuf}", r.pearson_r, unit="",
                       note=f"Pearson r, Pastas (AR1 noise) {q} against SSM {model} at n = {int(r.n)} wells ({grp}, {basis})")
                rr.add(f"pastas_vs_{model}_{q}_rho{suffix}{bsuf}", r.spearman_rho, unit="",
                       note=f"Spearman rho, Pastas (AR1 noise) {q} against SSM {model} at n = {int(r.n)} wells ({grp}, {basis})")
                if q != "base_level_m":
                    rr.add(f"pastas_vs_{model}_{q}_median_ratio{suffix}{bsuf}", r.median_ratio_pastas_over_ssm, unit="",
                           note=f"median Pastas:{model} ratio of {q} (p16 {r.ratio_p16:.3f}, p84 {r.ratio_p84:.3f}; {grp}, {basis})")
                else:
                    rr.add(f"pastas_vs_{model}_{q}_median_diff{suffix}{bsuf}", r.median_difference, unit="m",
                           note=f"median Pastas minus {model} base level ({grp}, {basis})")
    for q in ("beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage", "gain", "efold_months", "f_evap"):
        rr.add(f"pastas_synthetic_{q}_ratio_median", float(syn[f"ratio_{q}"].median()), unit="",
               note=f"median over the five synthetic centroid wells of Pastas-recovered / generating {q}: the unit conversion check")
    rr.add("pastas_synthetic_base_level_diff_median", float(syn["diff_base_level_m"].median()), unit="m",
           note="median Pastas-recovered minus generating base level on the synthetic wells")
    rr.save(OUT_48_REPORT_NUMBERS)
    saved(OUT_48_REPORT_NUMBERS.name)

    if not no_fig:
        phase(6, "Figure")
        plot(df, agree)
    result("Pastas cross-check", f"{len(df)} wells; see {OUT_48_AGREEMENT.name}")
    done("48")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pastas cross-check of the per-well SSM")
    ap.add_argument("--no-fig", action="store_true", help="write the CSVs only, no figure")
    args = ap.parse_args()
    sys.exit(main(no_fig=args.no_fig))
