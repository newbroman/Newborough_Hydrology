r"""

====================================================================================
CLIMATE AND WELL NETWORK SUMMARY (00_climate_summary.py)
====================================================================================
Purpose:
    Generates publication-ready climate summary figures and tables for the
    groundwater study baseline context.

Profiles:
    - full: full climate record outputs (legacy default filenames)
    - short: well-record overlap window outputs ("_short" filenames)
    - both: generate both full and short outputs in one run

Inputs:
  - outputs/01_climate.csv
  - outputs/01_wells_clean.csv

Outputs (outputs/00_climate_summary/):
    full profile:
    - 00_01_climate_timeseries.png
    - 00_02_well_network_summary.png
    - 00_03_summer_warming_trend.png        (new — RAF Valley summer max-temp trend, full 95-year record)
    - 00_01_annual_climate_summary.csv
    - 00_02_well_network_summary.csv
    - 00_03_summer_warming_stats.csv        (new — per-year summer means + regression stats)

    short profile:
    - 00_01_climate_timeseries_short.png
    - 00_02_well_network_summary_short.png
    - 00_01_annual_climate_summary_short.csv
    - 00_02_well_network_summary_short.csv

    Note: the summer warming trend figure is generated on the 'full' profile
    only — it exists to show the 95-year climate context, and plotting it
    on the monitoring-period subset would defeat that purpose.
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
from utils.paths import (
    make_all_dirs,
    INT_CLIMATE,
    INT_WELLS_CLEAN,
    DATA_CLIMATE_RAW,
    OUT_00_CLIMATE_TIMESERIES,
    OUT_00_WELL_NETWORK_FIG,
    OUT_00_SUMMER_WARMING,
    OUT_00_ANNUAL_CLIMATE_TABLE,
    OUT_00_WELL_NETWORK_TABLE,
    OUT_00_SUMMER_WARMING_TABLE,
    OUT_00_CLIMATOLOGY,
    OUT_00_REPORT_NUMBERS,
)
from utils.report_numbers_utils import ReportNumbers
from utils.paths import OUT_00_PET_WARMING
from utils.config import REFERENCE_CUTOFF_DATE
from utils.render_utils import render_figure

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import re
import os
from scipy.stats import linregress

__version__ = "1.4.1"  # Hollingham (2026) -- 2026-08-18. Store-time rounding
#   removed from make_figure3_summer_warming's stats rows (D-035); Script 00
#   was outside the original sweep. Emits the PET response
#   to warming (00_05 and four report numbers). Thornthwaite carries the heat
#   index in the denominator and builds it from the same temperatures, so the
#   formula partly cancels its own response to warming. The report and Paper 1
#   both argue that rising evaporative demand reaches the aquifer through the
#   atmospheric-draw term, so how much of the warming the PET series actually
#   carries is a number those arguments rest on.
#
# v1.3.0  # Hollingham (2026) — 2026-08-12
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).
#
# Changelog
#   1.3.0 (2026-08-12) — Water-level axis labels corrected from "below pipe top"
#         to "below ground". 01_wells_clean.csv carries the master's `depth from
#         surface` values (level = upstand - dip), already referenced to the
#         ground surface, so these axes have always plotted below-ground levels
#         and the old labels misstated the frame (GEOMETRY_ARCHITECTURE_SPEC.md
#         §3; cf. Script 26 v1.6.0, which fixed the same residue). Plotted
#         values are unchanged — this is a labelling correction only. String
#         matches the house form used by Scripts 26/26b/26c. Also fixed the
#         banner() version literal, which had drifted to 1.0.2.
#   1.2.0 (2026-06-22) — see CHANGELOG.
CB_BLUE = "#0072B2"
CB_GREEN = "#009E73"
CB_ORANGE = "#E69F00"
CB_RED = "#D55E00"
CB_BROWN = "#8C564B"
CUTOFF_DATE = pd.Timestamp(REFERENCE_CUTOFF_DATE)
MIN_RECORD_MONTHS = 100
DETREND_START = pd.Timestamp("2004-12-01")
DETREND_END = pd.Timestamp("2025-12-01")


# Length of the early and late comparison periods used by
# pet_warming_response(). Thirty years is the standard climatological
# normal; the station record holds three of them.
PET_RESPONSE_PERIOD_YEARS = 30


def _build_output_paths(profile: str) -> dict[str, str]:
    suffix = "_short" if profile == "short" else ""
    return {
        "fig1": os.path.join(os.path.dirname(OUT_00_CLIMATE_TIMESERIES), f"00_01_climate_timeseries{suffix}.png"),
        "fig2": os.path.join(os.path.dirname(OUT_00_WELL_NETWORK_FIG), f"00_02_well_network_summary{suffix}.png"),
        "fig3": str(OUT_00_SUMMER_WARMING),  # full-record only; no _short variant
        "table1": os.path.join(os.path.dirname(OUT_00_ANNUAL_CLIMATE_TABLE), f"00_01_annual_climate_summary{suffix}.csv"),
        "table2": os.path.join(os.path.dirname(OUT_00_WELL_NETWORK_TABLE), f"00_02_well_network_summary{suffix}.csv"),
        "table3": str(OUT_00_SUMMER_WARMING_TABLE),  # full-record only
    }


def _season_color(month: int) -> str:
    if month in (12, 1, 2):
        return CB_BLUE   # DJF
    if month in (3, 4, 5):
        return CB_GREEN  # MAM
    if month in (6, 7, 8):
        return CB_ORANGE # JJA
    return CB_BROWN      # SON


def _safe_ratio(num: float, den: float):
    if pd.isna(num) or pd.isna(den) or den == 0:
        return pd.NA
    return num / den


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True)
    wells = pd.read_csv(INT_WELLS_CLEAN, index_col=0, parse_dates=True)

    climate = climate.sort_index()
    wells = wells.sort_index()

    if "P_m" not in climate.columns or "PET" not in climate.columns:
        raise ValueError("01_climate.csv must contain columns 'P_m' and 'PET'.")

    return climate, wells


def _filter_wells_min_record(
    wells: pd.DataFrame,
    cutoff: pd.Timestamp = CUTOFF_DATE,
    min_months: int = MIN_RECORD_MONTHS,
) -> pd.DataFrame:
    """Keep wells with at least `min_months` non-null records up to `cutoff`."""
    # Llyn Rhos-ddu is a lake-stage measurement, not a water-table observation;
    # exclude from network summaries (see Script 01 EXTENDED_NETWORK_BLACKLIST).
    drop = [c for c in wells.columns if c.lower().replace(" ", "") == "llynrhos"]
    wells = wells.drop(columns=drop, errors="ignore")
    subset = wells.loc[wells.index <= cutoff].copy()
    valid_counts = subset.notna().sum(axis=0)
    keep = valid_counts[valid_counts >= min_months].index.tolist()
    return wells[keep].copy()


def _restrict_to_well_record_period(
    climate: pd.DataFrame,
    wells: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]:
    """Restrict climate and wells to the date span where the selected wells have data."""
    wells_num = wells.apply(pd.to_numeric, errors="coerce")
    row_has_any_obs = wells_num.notna().any(axis=1)
    if not row_has_any_obs.any():
        raise ValueError("No valid well observations found for the selected network.")

    period_index = wells_num.index[row_has_any_obs]
    start = period_index.min()
    end = period_index.max()
    climate_clip = climate.loc[(climate.index >= start) & (climate.index <= end)].copy()
    wells_clip = wells.loc[(wells.index >= start) & (wells.index <= end)].copy()
    return climate_clip, wells_clip, start, end


def make_table1_annual_climate(climate: pd.DataFrame, out_csv: str) -> pd.DataFrame:
    df = climate[["P_m", "PET"]].copy()
    df["P_mm"] = df["P_m"] * 1000.0
    df["PET_mm"] = df["PET"] * 1000.0
    df["Year"] = df.index.year
    df["complete_month"] = df[["P_mm", "PET_mm"]].notna().all(axis=1).astype(int)

    annual = (
        df.groupby("Year", dropna=True)
        .agg(
            Annual_P_mm=("P_mm", "sum"),
            Annual_PET_mm=("PET_mm", "sum"),
            Months_complete=("complete_month", "sum"),
        )
        .reset_index()
    )
    annual["P_PET_ratio"] = annual.apply(
        lambda r: _safe_ratio(r["Annual_P_mm"], r["Annual_PET_mm"]), axis=1
    )
    annual["Notes"] = annual["Months_complete"].apply(lambda n: "*" if n < 12 else "")

    # Long-term mean row — COMPLETE YEARS ONLY.
    # Partial years (a year with fewer than 12 measured months — e.g. 2005
    # April-Dec and 2026 January-only at the ends of the well-monitoring
    # record) are flagged with "*" in the Notes column above, and must be
    # excluded from the summary mean.  Averaging them in drags the mean
    # annual totals down and is the defect this row previously carried
    # (the tell was Months_complete ≈ 11.4 instead of 12).  The partial
    # years still appear as their own rows in the table; only this summary
    # row's calculation excludes them.
    complete = annual[annual["Months_complete"] == 12]
    summary_row = pd.DataFrame(
        {
            "Year": ["Long-term mean"],
            "Annual_P_mm": [complete["Annual_P_mm"].mean()],
            "Annual_PET_mm": [complete["Annual_PET_mm"].mean()],
            "P_PET_ratio": [complete["P_PET_ratio"].mean(skipna=True)],
            "Months_complete": [complete["Months_complete"].mean()],
            "Notes": ["Mean of complete years only (Months_complete = 12)"],
        }
    )

    out = pd.concat([annual, summary_row], ignore_index=True)
    out.to_csv(out_csv, index=False)
    return out


def make_table2_well_network(wells: pd.DataFrame, out_csv: str) -> pd.DataFrame:
    total_months = len(wells.index)
    rows = []

    for well in wells.columns:
        s = pd.to_numeric(wells[well], errors="coerce")
        valid = s.dropna()

        if valid.empty:
            record_start = pd.NA
            record_end = pd.NA
            n_months = 0
            mean_wl = pd.NA
            std_wl = pd.NA
            amp = pd.NA
            missing_pct = 100.0
        else:
            record_start = valid.index.min().date().isoformat()
            record_end = valid.index.max().date().isoformat()
            n_months = int(valid.shape[0])
            mean_wl = float(valid.mean())
            std_wl = float(valid.std()) if n_months > 1 else pd.NA

            feb_mean = valid[valid.index.month == 2].mean()
            aug_mean = valid[valid.index.month == 8].mean()
            amp = aug_mean - feb_mean if (pd.notna(aug_mean) and pd.notna(feb_mean)) else pd.NA

            # Mean annual summer minimum (Jun-Sep) and winter maximum (Oct-Mar)
            # computed per hydrological year (Oct start) then averaged.
            summer_months = valid[valid.index.month.isin([6, 7, 8, 9])]
            winter_months = valid[valid.index.month.isin([10, 11, 12, 1, 2, 3])]
            hyd_yr_summer = summer_months.index.year
            hyd_yr_winter = winter_months.index.map(
                lambda d: d.year if d.month >= 10 else d.year - 1)
            ann_s_min = summer_months.groupby(hyd_yr_summer).min()
            ann_w_max = winter_months.groupby(hyd_yr_winter).max()
            mean_summer_min = float(ann_s_min.mean()) if len(ann_s_min) >= 3 else pd.NA
            mean_winter_max = float(ann_w_max.mean()) if len(ann_w_max) >= 3 else pd.NA

            missing_pct = float(((total_months - n_months) / total_months) * 100.0) if total_months else pd.NA

        rows.append(
            {
                "Well": str(well),
                "Record_start": record_start,
                "Record_end": record_end,
                "N_months": n_months,
                "Mean_WL_m": mean_wl,
                "Std_WL_m": std_wl,
                "Seasonal_amplitude_m": amp,
                "Mean_Summer_Min_m": mean_summer_min,
                "Mean_Winter_Max_m": mean_winter_max,
                "Missing_pct": missing_pct,
            }
        )

    out = pd.DataFrame(rows).sort_values(["N_months", "Well"], ascending=[False, True]).reset_index(drop=True)
    out.to_csv(out_csv, index=False)
    return out


def make_figure1_climate_timeseries(climate: pd.DataFrame, wells: pd.DataFrame, out_png: str, profile: str) -> None:
    df = climate[["P_m", "PET"]].copy()
    df["P_mm"] = df["P_m"] * 1000.0
    df["PET_mm"] = df["PET"] * 1000.0
    df["SeasonColor"] = [ _season_color(m) for m in df.index.month ]

    p_roll_12 = df["P_mm"].rolling(12, min_periods=6).mean()
    pet_roll_12 = df["PET_mm"].rolling(12, min_periods=6).mean()

    fig1_stats: dict = {}   # short-profile centring + cumbal-vs-WL regression (for report_numbers)

    if profile == "short":
        net_balance = df["P_mm"] - df["PET_mm"]

        full_climate = pd.read_csv(INT_CLIMATE, index_col=0, parse_dates=True).sort_index()
        full_balance = (full_climate["P_m"] * 1000.0) - (full_climate["PET"] * 1000.0)
        detrend_window = full_balance.loc[(full_balance.index >= DETREND_START) & (full_balance.index <= DETREND_END)]
        if detrend_window.empty:
            raise ValueError("No climate rows in detrending window Dec 1989-Dec 2025.")
        detrend_mean = float(detrend_window.mean(skipna=True))

        net_corrected = net_balance - detrend_mean
        cum_balance_corrected = net_corrected.fillna(0).cumsum()
        net_roll_12 = net_corrected.rolling(12, min_periods=6).mean()

        # Suppress 12-month trend lines in the first 12 months of the short window.
        if len(df.index) >= 12:
            trend_mask = np.arange(len(df.index)) >= 12
            p_roll_12_plot = p_roll_12.where(trend_mask, np.nan)
            pet_roll_12_plot = pet_roll_12.where(trend_mask, np.nan)
            net_roll_12_plot = net_roll_12.where(trend_mask, np.nan)
        else:
            p_roll_12_plot = p_roll_12 * np.nan
            pet_roll_12_plot = pet_roll_12 * np.nan
            net_roll_12_plot = net_roll_12 * np.nan

        fig, (ax1, ax2, ax3, ax4) = plt.subplots(
            4, 1, figsize=(14, 15), dpi=300, sharex=True,
            gridspec_kw={"height_ratios": [1.2, 1.1, 1.25, 1.2]}
        )

        for _ax, _lbl in zip([ax1, ax2, ax3, ax4], ["(a)", "(b)", "(c)", "(d)"]):
            _ax.text(0.015, 0.97, _lbl, transform=_ax.transAxes,
                     fontsize=13, fontweight="bold", va="top", ha="left",
                     zorder=10,
                     bbox={"facecolor": "white", "edgecolor": "none",
                           "alpha": 0.8, "pad": 1.5})

        ax1.step(df.index, df["P_mm"], where="mid", color=CB_BLUE, linewidth=1.4, alpha=0.95, label="Monthly precipitation")
        ax1.axhline(df["P_mm"].mean(skipna=True), color="black", linestyle="--", linewidth=1.4, alpha=0.8)
        ax1.plot(df.index, p_roll_12_plot, color=CB_BLUE, linewidth=2.0, label="P 12-month rolling mean")
        ax1.set_ylabel("Precipitation (mm)")
        ax1.set_title("Climate Record Summary: Monthly Forcing and Annual Balances", fontweight="bold")
        ax1.grid(axis="y", linestyle=":", alpha=0.35)
        ax1.legend(loc="upper left", bbox_to_anchor=(0.04, 1.0), frameon=False)

        ax2.fill_between(df.index, 0, df["PET_mm"], color=CB_ORANGE, alpha=0.35)
        ax2.plot(df.index, pet_roll_12_plot, color=CB_RED, linewidth=2.0, label="PET 12-month rolling mean")
        ax2.set_ylabel("PET (mm)")
        ax2.grid(axis="y", linestyle=":", alpha=0.35)
        ax2.legend(loc="upper left", bbox_to_anchor=(0.04, 1.0), frameon=False)

        ax3.plot(df.index, cum_balance_corrected, color=CB_BLUE, linewidth=2.2, label="Leveled cumulative (P-PET)")
        ax3.plot(df.index, net_roll_12_plot, color=CB_RED, linewidth=1.5, linestyle="--", label="12-month rolling mean (corrected net)")
        ax3.axhline(0, color="black", linestyle=":", linewidth=1.0, alpha=0.7)
        ax3.set_ylabel("Water balance (mm)")
        ax3.grid(axis="y", linestyle=":", alpha=0.35)
        ax3.legend(loc="upper left", bbox_to_anchor=(0.04, 1.0), frameon=False, ncol=1)
        ax3.xaxis.set_major_locator(mdates.YearLocator(5))
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax3.tick_params(axis="x", rotation=45)
        ax3.text(
            0.99,
            0.96,
            f"Detrending mean (Dec 2004-Dec 2025): {detrend_mean:+.2f} mm/month",
            transform=ax3.transAxes,
            ha="right",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7, "pad": 2.0},
        )

        wells_num = wells.apply(pd.to_numeric, errors="coerce")
        mean_ts = wells_num.mean(axis=1, skipna=True)
        std_ts = wells_num.std(axis=1, skipna=True)
        fit_df = pd.concat([cum_balance_corrected.rename("x"), mean_ts.rename("y")], axis=1).dropna()
        if len(fit_df) >= 2:
            x = fit_df["x"].to_numpy()
            y = fit_df["y"].to_numpy()
            slope, intercept = np.polyfit(x, y, 1)
            y_hat = slope * x + intercept
            ss_res = np.sum((y - y_hat) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2_lag0 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
        else:
            r2_lag0 = np.nan

        fig1_stats = {
            "centring_mm":     float(detrend_mean),
            "cumbal_wl_r2":    float(r2_lag0) if pd.notna(r2_lag0) else np.nan,
            "cumbal_wl_slope": float(slope) if len(fit_df) >= 2 else np.nan,
            "cumbal_wl_n":     int(len(fit_df)),
        }

        ax4.plot(mean_ts.index, mean_ts, color=CB_GREEN, linewidth=2.3, label="Network mean well level")
        ax4.fill_between(mean_ts.index, mean_ts - std_ts, mean_ts + std_ts, color=CB_GREEN, alpha=0.22, label="Inter-well SD")
        ax4.set_ylabel("Water level (m, below ground)")
        ax4.grid(axis="y", linestyle=":", alpha=0.35)
        ax4.legend(loc="upper left", bbox_to_anchor=(0.04, 1.0), frameon=False)
        if pd.notna(r2_lag0):
            ax4.text(
                0.99,
                0.96,
                f"Lag 0, unsmoothed fit vs cumulative (P-PET): R^2 = {r2_lag0:.3f}",
                transform=ax4.transAxes,
                ha="right",
                va="top",
                fontsize=9,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7, "pad": 2.0},
            )

        intervention_date = pd.Timestamp("2018-01-01")
        for ax in (ax1, ax2, ax3, ax4):
            ax.axvline(intervention_date, color="black", linestyle="--", linewidth=1.1, alpha=0.8)

        ax1.text(
            intervention_date, 0.93,
            "Clear-fell intervention", rotation=90, va="top", ha="right", fontsize=9,
            transform=ax1.get_xaxis_transform(),
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.6, "pad": 2.0}
        )
        ax4.set_xlabel("Date / Year")
    else:
        annual = df[["P_mm", "PET_mm"]].resample("YE").sum(min_count=1)
        annual["P_PET_ratio"] = annual["P_mm"] / annual["PET_mm"].replace(0, pd.NA)

        fig, (ax1, ax2, ax3) = plt.subplots(
            3, 1, figsize=(14, 12), dpi=300, sharex=True,
            gridspec_kw={"height_ratios": [1.2, 1.1, 1.25]}
        )

        ax1.bar(df.index, df["P_mm"], width=25, color=df["SeasonColor"], edgecolor="none", alpha=0.95)
        ax1.axhline(df["P_mm"].mean(skipna=True), color="black", linestyle="--", linewidth=1.4, alpha=0.8)
        ax1.plot(df.index, p_roll_12, color=CB_BLUE, linewidth=2.0, label="P 12-month rolling mean")
        ax1.set_ylabel("Precipitation (mm)")
        ax1.set_title("Climate Record Summary: Monthly Forcing and Annual Balances", fontweight="bold")
        ax1.grid(axis="y", linestyle=":", alpha=0.35)
        ax1.legend(loc="upper left", frameon=False)

        ax2.fill_between(df.index, 0, df["PET_mm"], color=CB_ORANGE, alpha=0.35)
        ax2.plot(df.index, pet_roll_12, color=CB_RED, linewidth=2.0, label="PET 12-month rolling mean")
        ax2.set_ylabel("PET (mm)")
        ax2.grid(axis="y", linestyle=":", alpha=0.35)
        ax2.legend(loc="upper left", frameon=False)

        ax3.bar(
            annual.index - pd.Timedelta(days=70),
            annual["P_mm"],
            width=120,
            color=CB_BLUE,
            alpha=0.7,
            label="Annual precipitation",
        )
        ax3.bar(
            annual.index + pd.Timedelta(days=70),
            annual["PET_mm"],
            width=120,
            color=CB_ORANGE,
            alpha=0.7,
            label="Annual PET",
        )
        ax3.set_ylabel("Annual total (mm)")
        ax3.grid(axis="y", linestyle=":", alpha=0.35)
        ax3_ratio = ax3.twinx()
        ax3_ratio.plot(annual.index, annual["P_PET_ratio"], color=CB_BROWN, linewidth=1.8, label="P/PET ratio")
        ax3_ratio.axhline(1.0, color="black", linestyle="--", linewidth=1.0, alpha=0.6)
        ax3_ratio.set_ylabel("P/PET ratio")
        h1, l1 = ax3.get_legend_handles_labels()
        h2, l2 = ax3_ratio.get_legend_handles_labels()
        ax3.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, ncol=1)
        ax3.xaxis.set_major_locator(mdates.YearLocator(5))
        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax3.tick_params(axis="x", rotation=45)

        intervention_date = pd.Timestamp("2018-01-01")
        for ax in (ax1, ax2, ax3):
            ax.axvline(intervention_date, color="black", linestyle="--", linewidth=1.1, alpha=0.8)

        ax1.text(
            intervention_date, 0.93,
            "Clear-fell intervention", rotation=90, va="top", ha="right", fontsize=9,
            transform=ax1.get_xaxis_transform(),
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.6, "pad": 2.0}
        )
        ax3.set_xlabel("Date / Year")

    fig.tight_layout()
    render_figure(fig, out_png)
    plt.close(fig)
    return fig1_stats


def compute_climatology(climate: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """12-month rainfall/PET climatology over COMPLETE calendar years only
    (partial start/end years excluded), plus the winter (Oct-Mar) / summer
    (Apr-Sep) rainfall split and the peak/trough months. Used to make the
    Fig 3 §4.1.1 climate statistics traceable.

    On the monitoring-period (short) climate this is the full-years
    well-period basis (e.g. 2006-2025; partial 2005 and 2026 excluded).
    """
    c = climate[["P_m", "PET"]].copy()
    c["P_mm"] = c["P_m"] * 1000.0
    c["PET_mm"] = c["PET"] * 1000.0
    counts = c.groupby(c.index.year).size()
    complete = counts[counts == 12].index
    cf = c[c.index.year.isin(complete)]
    clim = (cf.groupby(cf.index.month)[["P_mm", "PET_mm"]].mean()
              .reindex(range(1, 13)))
    clim.index.name = "month"
    winter = float(clim.loc[[10, 11, 12, 1, 2, 3], "P_mm"].sum())
    summer = float(clim.loc[[4, 5, 6, 7, 8, 9], "P_mm"].sum())
    stats = {
        "n_complete_years":   int(len(complete)),
        "year_first":         int(min(complete)) if len(complete) else None,
        "year_last":          int(max(complete)) if len(complete) else None,
        "winter_rainfall_mm": winter,
        "summer_rainfall_mm": summer,
        "rain_peak_month":    int(clim["P_mm"].idxmax()),
        "rain_peak_mm":       float(clim["P_mm"].max()),
        "rain_trough_month":  int(clim["P_mm"].idxmin()),
        "rain_trough_mm":     float(clim["P_mm"].min()),
        "pet_peak_month":     int(clim["PET_mm"].idxmax()),
        "pet_peak_mm":        float(clim["PET_mm"].max()),
    }
    return clim.reset_index(), stats


def make_figure2_well_network(wells: pd.DataFrame, table2: pd.DataFrame, out_png: str) -> None:
    fig, axs = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    ax_tl, ax_tr, ax_bl, ax_br = axs.flatten()

    # Top-left: record lengths
    rec_lengths = pd.to_numeric(table2["N_months"], errors="coerce").dropna()
    ax_tl.hist(rec_lengths, bins=14, color=CB_BLUE, alpha=0.85, edgecolor="white")
    ax_tl.axvline(100, color=CB_RED, linestyle="--", linewidth=1.4, label="100-month threshold")
    ax_tl.set_title("Record Length Distribution")
    ax_tl.set_xlabel("Months")
    ax_tl.set_ylabel("Well count")
    ax_tl.legend(frameon=False)
    ax_tl.grid(axis="y", linestyle=":", alpha=0.35)

    # Top-right: distribution of mean water levels
    well_means = pd.to_numeric(table2["Mean_WL_m"], errors="coerce").dropna()
    ax_tr.hist(well_means, bins=14, color=CB_ORANGE, alpha=0.85, edgecolor="white")
    ax_tr.set_title("Mean Water Level by Well")
    ax_tr.set_xlabel("Water level (m, below ground)")
    ax_tr.set_ylabel("Well count")
    ax_tr.grid(axis="y", linestyle=":", alpha=0.35)

    # Bottom-left: network mean monthly line with inter-well std envelope
    wells_num = wells.apply(pd.to_numeric, errors="coerce")
    mean_ts = wells_num.mean(axis=1, skipna=True)
    std_ts = wells_num.std(axis=1, skipna=True)

    ax_bl.plot(mean_ts.index, mean_ts, color=CB_BLUE, linewidth=2.4, label="Network mean")
    ax_bl.fill_between(mean_ts.index, mean_ts - std_ts, mean_ts + std_ts, color=CB_BLUE, alpha=0.2, label="Inter-well SD")
    ax_bl.axvline(pd.Timestamp("2018-01-01"), color="black", linestyle="--", linewidth=1.1, alpha=0.8)
    ax_bl.set_title("Network Mean Monthly Water Level")
    ax_bl.set_ylabel("Water level (m, below ground)")
    ax_bl.grid(axis="y", linestyle=":", alpha=0.35)
    ax_bl.legend(frameon=False, loc="best")

    # Bottom-right: monthly boxplots across all wells
    long_df = wells_num.stack(future_stack=True).dropna().reset_index()
    long_df.columns = ["Date", "Well", "WL"]
    long_df["Month"] = pd.to_datetime(long_df["Date"]).dt.month

    month_data = []
    for m in range(1, 13):
        month_data.append(long_df.loc[long_df["Month"] == m, "WL"].tolist())

    bp = ax_br.boxplot(month_data, patch_artist=True, widths=0.6, showfliers=False)
    for box in bp["boxes"]:
        box.set(facecolor=CB_GREEN, alpha=0.35, edgecolor=CB_GREEN)
    for median in bp["medians"]:
        median.set(color=CB_GREEN, linewidth=1.5)

    ax_br.set_title("Seasonal Cycle Across Network")
    ax_br.set_xlabel("Calendar month")
    ax_br.set_ylabel("Water level (m, below ground)")
    ax_br.set_xticks(list(range(1, 13)))
    ax_br.grid(axis="y", linestyle=":", alpha=0.35)

    for ax in (ax_tl, ax_tr, ax_bl, ax_br):
        ax.tick_params(axis="both", labelsize=10)

    fig.tight_layout()
    render_figure(fig, out_png)
    plt.close(fig)


_MONTH_MAP = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
              "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}


def _parse_raf_valley_date(s: str) -> tuple[int | None, int | None]:
    """Parse the raw RAF Valley date format 'MMM YY' into (year, month).

    Two-digit year rule: values 30-99 are 1930-1999; values 00-29 are 2000-2029.
    This matches the record span (December 1930 onwards).
    """
    m = re.match(r"(\w+)\s*(\d+)", str(s))
    if not m:
        return None, None
    mon = _MONTH_MAP.get(m.group(1))
    if mon is None:
        return None, None
    yr_2d = int(m.group(2))
    yr = 1900 + yr_2d if yr_2d >= 30 else 2000 + yr_2d
    return yr, mon


def make_figure3_summer_warming(out_png: str, out_csv: str) -> None:
    """RAF Valley summer (JJA) maximum-temperature trend over the full 95-year record.

    Loads the raw RAF_Valley_Climate.csv directly (not the pipeline-filtered
    01_climate.csv, which is P/PET only) and plots year-by-year JJA mean max
    temperature as red/blue bars relative to the pre-2013 mean, with a linear
    trend overlay. Only years with all three summer months recorded are used.

    Matches the 'Figure 5' style of the lay-summary document (Hollingham 2026,
    Newborough_Public_Summary). Produced on the full profile only — running
    it on the well-record subset (2005 onwards) would remove the long-baseline
    context that makes the trend interpretable.
    """
    raw = pd.read_csv(DATA_CLIMATE_RAW)
    raw.columns = ["date_str", "max_temp", "min_temp", "af_days", "rain_mm", "sun_hrs"]

    parsed = raw["date_str"].apply(lambda s: pd.Series(_parse_raf_valley_date(s)))
    parsed.columns = ["year", "month"]
    df = pd.concat([parsed, raw[["max_temp"]]], axis=1, sort=False)
    df = df.dropna(subset=["year", "month", "max_temp"])
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)

    # JJA summer months only, and only years where all three are present
    summer = df[df["month"].isin([6, 7, 8])].copy()
    counts = summer.groupby("year").size()
    complete_years = counts[counts == 3].index
    summer = summer[summer["year"].isin(complete_years)]

    annual = (summer.groupby("year", as_index=False)["max_temp"].mean()
                    .rename(columns={"max_temp": "summer_max_mean"}))
    annual = annual.sort_values("year").reset_index(drop=True)

    # Regression + pre/post-2013 split
    yrs = annual["year"].to_numpy()
    vals = annual["summer_max_mean"].to_numpy()
    reg = linregress(yrs, vals)

    pre_mask = yrs < 2013
    pre_mean = float(vals[pre_mask].mean()) if pre_mask.any() else float("nan")
    post_mean = float(vals[~pre_mask].mean()) if (~pre_mask).any() else float("nan")
    anomaly = post_mean - pre_mean

    # ------------------------------------------------------------------
    # Write stats table
    # ------------------------------------------------------------------
    annual_out = annual.copy()
    annual_out["anomaly_vs_pre2013"] = annual_out["summer_max_mean"] - pre_mean
    annual_out["is_post_2013"] = (annual_out["year"] >= 2013).astype(int)
    # Append regression summary row
    summary_row = pd.DataFrame({
        "year": ["TREND_STATS"],
        "summer_max_mean": [float("nan")],
        "anomaly_vs_pre2013": [float("nan")],
        "is_post_2013": [""],
    })
    annual_out = pd.concat([annual_out, summary_row], ignore_index=True)

    # Stored at computed precision (D-035): rounding is a rendering decision.
    meta_rows = pd.DataFrame([
        {"year": "slope_C_per_yr",     "summer_max_mean": float(reg.slope)},
        {"year": "intercept_C",        "summer_max_mean": float(reg.intercept)},
        {"year": "r_squared",          "summer_max_mean": float(reg.rvalue ** 2)},
        {"year": "p_value",            "summer_max_mean": reg.pvalue},
        {"year": "n_years",            "summer_max_mean": int(len(yrs))},
        {"year": "year_range",         "summer_max_mean": f"{int(yrs.min())}-{int(yrs.max())}"},
        {"year": "pre_2013_mean_C",    "summer_max_mean": float(pre_mean)},
        {"year": "post_2013_mean_C",   "summer_max_mean": float(post_mean)},
        {"year": "post_2013_anomaly",  "summer_max_mean": float(anomaly)},
    ])
    annual_out = pd.concat([annual_out, meta_rows], ignore_index=True)
    annual_out.to_csv(out_csv, index=False)

    # ------------------------------------------------------------------
    # Plot: red/blue bars relative to pre-2013 mean + trend line
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.2))
    anoms = vals - pre_mean
    colors = [CB_RED if a >= 0 else CB_BLUE for a in anoms]
    ax.bar(yrs, anoms, color=colors, edgecolor="white", linewidth=0.4,
           alpha=0.85, zorder=3)

    # Trend line — plotted in anomaly space (subtract pre-2013 baseline)
    trend = reg.slope * yrs + reg.intercept - pre_mean
    ax.plot(yrs, trend, color="black", lw=2.0, zorder=4,
            label=f"Linear trend: {reg.slope:+.4f} °C yr⁻¹  (p = {reg.pvalue:.1e})")

    # Post-2013 mean as a horizontal reference line
    ax.axhline(anomaly, color=CB_RED, ls="--", lw=1.2, alpha=0.7, zorder=2,
               label=f"Post-2013 mean: {anomaly:+.2f} °C above pre-2013 baseline")
    ax.axhline(0.0, color="#555555", lw=0.8, zorder=1)

    # Baseline annotation
    ax.text(yrs.min() + 0.5, 0.02, f"Pre-2013 baseline ({pre_mean:.2f} °C)",
            fontsize=8, color="#555555", style="italic")

    ax.set_xlabel("Year")
    ax.set_ylabel("Summer (JJA) max-temperature anomaly\n(°C, relative to pre-2013 mean)")
    ax.set_title("RAF Valley summer maximum temperature, 1931–2025\n"
                 "Anomaly relative to pre-2013 mean; bars coloured by sign",
                 fontsize=11, fontweight="bold")
    ax.set_xlim(yrs.min() - 1, yrs.max() + 1)
    ax.grid(axis="y", linestyle=":", alpha=0.35, zorder=0)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    render_figure(fig, out_png)
    plt.close(fig)


def pet_warming_response(climate_full: pd.DataFrame, out_csv: str) -> dict:
    """
    How much of the station's warming actually reaches PET.

    Thornthwaite puts the heat index I in the denominator - PET scales as
    (10T/I)^a - and I is itself a sum of the same temperatures. A warming
    climate therefore raises both the numerator and the denominator, and the
    formula partly cancels its own response. This quantifies the cancellation,
    because the report and Paper 1 both argue that rising evaporative demand
    acts on the aquifer through the atmospheric-draw term, and the strength of
    that route depends on how much of the warming the PET series carries.

    Computed over complete calendar years of the FULL station record, on the
    first and last thirty of them, so the comparison is climatological rather
    than a regression through interannual noise. Temperature comes from the raw
    station file (as make_figure3_summer_warming does; 01_climate.csv carries
    P and PET only) and PET from the pipeline climate frame, so the two sides
    are the same series the SSM is fitted to.

    Returns a dict of statistics and writes the per-year table.
    """
    raw = pd.read_csv(DATA_CLIMATE_RAW)
    raw.columns = ["date_str", "max_temp", "min_temp", "af_days", "rain_mm", "sun_hrs"]
    parsed = raw["date_str"].apply(lambda x: pd.Series(_parse_raf_valley_date(x)))
    parsed.columns = ["year", "month"]
    t = pd.concat([parsed, raw[["max_temp", "min_temp"]]], axis=1, sort=False)
    t = t.dropna(subset=["year", "month", "max_temp", "min_temp"])
    t["year"] = t["year"].astype(int)
    t["month"] = t["month"].astype(int)
    t["t_mean"] = (t["max_temp"] + t["min_temp"]) / 2.0

    pet = climate_full[["PET"]].copy()
    pet["year"] = pet.index.year
    pet["month"] = pet.index.month
    j = t.merge(pet, on=["year", "month"], how="inner")

    counts = j.groupby("year").size()
    full_years = counts[counts == 12].index
    j = j[j["year"].isin(full_years)]
    ann = (j.groupby("year")
             .agg(T_mean_C=("t_mean", "mean"), PET_annual_mm=("PET", lambda v: v.sum() * 1000.0))
             .reset_index()
             .sort_values("year"))

    n_period = PET_RESPONSE_PERIOD_YEARS
    early, late = ann.head(n_period), ann.tail(n_period)
    dT = float(late["T_mean_C"].mean() - early["T_mean_C"].mean())
    pct_T = float(late["T_mean_C"].mean() / early["T_mean_C"].mean() - 1.0) * 100.0
    pct_PET = float(late["PET_annual_mm"].mean() / early["PET_annual_mm"].mean() - 1.0) * 100.0
    elasticity = pct_PET / pct_T if pct_T else float("nan")

    ann_out = ann.copy()
    ann_out["period"] = ""
    ann_out.loc[ann_out["year"].isin(early["year"]), "period"] = "early"
    ann_out.loc[ann_out["year"].isin(late["year"]), "period"] = "late"
    ann_out.to_csv(out_csv, index=False)

    stats = {
        "n_complete_years": int(len(ann)),
        "early_first": int(early["year"].iloc[0]), "early_last": int(early["year"].iloc[-1]),
        "late_first": int(late["year"].iloc[0]),   "late_last": int(late["year"].iloc[-1]),
        "T_early_C": float(early["T_mean_C"].mean()), "T_late_C": float(late["T_mean_C"].mean()),
        "PET_early_mm": float(early["PET_annual_mm"].mean()),
        "PET_late_mm": float(late["PET_annual_mm"].mean()),
        "dT_C": dT, "pct_T": pct_T, "pct_PET": pct_PET, "elasticity": elasticity,
    }
    print(f"  PET warming response: T {stats['T_early_C']:.2f} -> {stats['T_late_C']:.2f} degC "
          f"({pct_T:+.1f}%), annual PET {stats['PET_early_mm']:.1f} -> {stats['PET_late_mm']:.1f} mm "
          f"({pct_PET:+.1f}%), elasticity {elasticity:.2f}")
    return stats


def _run_all() -> None:
    """Generate all Script 00 outputs — full-record and monitoring-period — in one pass."""

    climate_full, wells_all = _load_inputs()
    wells_full = _filter_wells_min_record(wells_all)

    # --- Full-record outputs -----------------------------------------------
    print("\n--- Full-record outputs ---")
    paths_full = _build_output_paths("full")
    table1_full = make_table1_annual_climate(climate_full, paths_full["table1"])
    table2_full = make_table2_well_network(wells_full, paths_full["table2"])
    make_figure1_climate_timeseries(climate_full, wells_full, paths_full["fig1"], "full")
    make_figure2_well_network(wells_full, table2_full, paths_full["fig2"])
    print("Generating Figure 3 — RAF Valley summer warming trend (95-year record)...")
    make_figure3_summer_warming(paths_full["fig3"], paths_full["table3"])

    # --- Monitoring-period (short) outputs ---------------------------------
    print("\n--- Monitoring-period outputs ---")
    paths_short = _build_output_paths("short")
    climate_short, wells_short, analysis_start, analysis_end = _restrict_to_well_record_period(
        climate_full.copy(), wells_full.copy()
    )
    table1_short = make_table1_annual_climate(climate_short, paths_short["table1"])
    table2_short = make_table2_well_network(wells_short, paths_short["table2"])
    fig1_stats = make_figure1_climate_timeseries(climate_short, wells_short, paths_short["fig1"], "short")
    make_figure2_well_network(wells_short, table2_short, paths_short["fig2"])

    # --- §4.1.1 traceable climate report numbers (Fig 3) --------------------
    clim_df, clim_stats = compute_climatology(climate_short)
    clim_df.to_csv(OUT_00_CLIMATOLOGY, index=False)
    print(f"  Saved climatology → {os.path.basename(OUT_00_CLIMATOLOGY)} "
          f"({clim_stats['n_complete_years']} complete years "
          f"{clim_stats['year_first']}-{clim_stats['year_last']})")

    print("Computing PET response to warming (full record)...")
    pet_resp = pet_warming_response(climate_full, str(OUT_00_PET_WARMING))

    rr = ReportNumbers()
    # Seasonal-redistribution trends — the committed home for the numbers
    # section 4.10.3 uses. Sibling keys share a prefix so the trend and its
    # t-statistic travel together (one confirmation per result, not two).
    _srt = seasonal_redistribution_trends(climate_short)
    for _k, _unit, _what in (
            ("annual_pet", "mm/yr", "annual Thornthwaite PET"),
            ("winter_rainfall", "mm/yr", "Oct-Mar rainfall, winter keyed to its October year"),
            ("summer_balance", "mm/yr", "Jun-Sep (JJAS) water balance P-PET"),
            ("winter_balance", "mm/yr", "Oct-Mar water balance P-PET"),
            ("annual_balance", "mm/yr", "annual water balance P-PET")):
        rr.add(f"trend_{_k}", _srt[_k]["slope"], unit=_unit, era=_srt["era"],
               note=f"OLS trend in {_what}; complete seasons only, "
                    f"n={_srt[_k]['n']}")
        rr.add(f"trend_{_k}_t", _srt[_k]["t"], unit="", era=_srt["era"],
               note=f"t-statistic of trend_{_k}")

    # Long-record context for the PET trend, so the well-record figure is not
    # read as a secular rate, and the variability that explains why PET
    # separates from zero while a larger winter-rainfall trend does not.
    _plc = pet_long_record_context(climate)
    for _w, _r in _plc["windows"].items():
        rr.add(f"trend_annual_pet_{_w}", _r["slope"], unit="mm/yr", era=_r["era"],
               note=f"OLS trend in annual Thornthwaite PET over the {_r['era']} "
                    f"window, n={_r['n']}. Nested with the other PET windows and "
                    f"sharing an end year: evidence that the rise is of long "
                    f"standing and steepening, NOT a test of acceleration.")
        rr.add(f"trend_annual_pet_{_w}_t", _r["t"], unit="", era=_r["era"],
               note=f"t-statistic of trend_annual_pet_{_w}")
    _var = series_variability(climate_short)
    for _k in ("annual_pet", "winter_rainfall"):
        rr.add(f"var_{_k}_mean", _var[_k]["mean"], unit="mm", era=_var["era"],
               note=f"mean of the annual series, n={_var[_k]['n']}")
        rr.add(f"var_{_k}_sd", _var[_k]["sd"], unit="mm", era=_var["era"],
               note="standard deviation of the annual series")
        rr.add(f"var_{_k}_cv_pct", _var[_k]["cv_pct"], unit="%", era=_var["era"],
               note="coefficient of variation: sd as a percentage of the mean. "
                    "This is why PET separates from zero and a larger winter "
                    "rainfall trend does not.")
    rr.add("pet_warming_dT", pet_resp["dT_C"], unit="degC",
           era=f"{pet_resp['early_first']}-{pet_resp['early_last']} vs "
               f"{pet_resp['late_first']}-{pet_resp['late_last']}",
           note="change in mean annual temperature between the first and last "
                "30 complete years of the station record")
    rr.add("pet_warming_pct_T", pet_resp["pct_T"], unit="%",
           note="same comparison, as a percentage of the early-period mean")
    rr.add("pet_warming_pct_PET", pet_resp["pct_PET"], unit="%",
           note="change in mean annual Thornthwaite PET over the same comparison")
    rr.add("pet_warming_elasticity", pet_resp["elasticity"], unit="",
           note="pct_PET / pct_T: the fraction of the warming signal the "
                "Thornthwaite PET series carries, I being in the denominator")
    rr.add("winter_rainfall", clim_stats["winter_rainfall_mm"], unit="mm",
           era="Oct-Mar", note=f"sum of monthly climatology, full-years well period "
                               f"{clim_stats['year_first']}-{clim_stats['year_last']}")
    rr.add("summer_rainfall", clim_stats["summer_rainfall_mm"], unit="mm",
           era="Apr-Sep", note="sum of monthly climatology, full-years well period")
    rr.add("rain_peak_mm", clim_stats["rain_peak_mm"], unit="mm",
           era=f"month {clim_stats['rain_peak_month']}", note="rainfall climatology peak")
    rr.add("rain_trough_mm", clim_stats["rain_trough_mm"], unit="mm",
           era=f"month {clim_stats['rain_trough_month']}", note="rainfall climatology trough")
    rr.add("pet_peak_mm", clim_stats["pet_peak_mm"], unit="mm",
           era=f"month {clim_stats['pet_peak_month']}", note="PET climatology peak")
    if fig1_stats:
        rr.add("centring_constant", fig1_stats["centring_mm"], unit="mm/month",
               note="cumulative-balance centring = mean monthly net (P-PET), Dec2004-Dec2025")
        rr.add("cumbal_wl_r2", fig1_stats["cumbal_wl_r2"], unit="",
               note=f"R^2, network-mean WL vs cumulative balance, lag 0, n={fig1_stats['cumbal_wl_n']}")
        rr.add("cumbal_wl_slope", fig1_stats["cumbal_wl_slope"], unit="m/mm",
               note="regression slope (well level per mm cumulative balance)")
    n_saved = rr.save(OUT_00_REPORT_NUMBERS)
    print(f"  Saved → {os.path.basename(OUT_00_REPORT_NUMBERS)} ({n_saved} report numbers)")

    # --- Summary -----------------------------------------------------------
    n_wells = int(wells_short.shape[1])
    n_months_short = int(len(climate_short.index))
    n_months_full = int(len(climate_full.index))

    print("\nFiles created:")
    for p in [paths_full, paths_short]:
        for k, v in p.items():
            if os.path.exists(v):
                print(f" - {v}")

    print("\nHeadline statistics:")
    print(f" - Full climate record: {n_months_full / 12.0:.1f} years ({n_months_full} months)")
    print(f" - Analysis window: {analysis_start.date().isoformat()} to {analysis_end.date().isoformat()}"
          f" ({n_months_short} months)")
    print(f" - Reference wells: {n_wells}")

    print("\n00 climate summary complete.")


def seasonal_redistribution_trends(climate, year_first: int = 2007,
                                   year_last: int = 2025) -> dict:
    """OLS trends in annual PET, winter rainfall and the seasonal water balance.

    WHY THIS IS A PIPELINE OUTPUT AND NOT A SENTENCE

      Section 4.10.3 argues that a near-zero far-field constant is not evidence
      of an unchanging climate but of a change that is SEASONAL in character: a
      summer loss and a winter gain that very nearly cancel within the year, to
      which an annual-rate term is structurally blind. That argument was written
      from session probes. Under the project rule a number entering a document
      traces to a committed CSV, so it is computed here, once, from the same
      01_climate.csv every other climate number comes from.

    THE SEASONS ARE THE PROJECT'S, NOT THIS FUNCTION'S

      Summer = Jun-Sep (JJAS) and winter = Oct-Mar, with a winter keyed to the
      year its OCTOBER falls in. Both are taken from the winter-maximum /
      summer-minimum extraction in this same script, which is what the winter
      flooding thresholds SD15b_WINTER and SD16_WINTER are evaluated against.
      A first draft of this function used Apr-Sep and the opposite winter
      attribution — inventing seasons for one paragraph while the flooding
      analysis three hundred lines above used different ones (Martin,
      2026-08-23). Never define a season here. Read it from what the analysis
      already uses.

      These are HYDROLOGICAL seasons and are deliberately neither of the
      calendar definitions: meteorological winter is Dec-Feb, astronomical
      winter is the solstice to the equinox, and monthly data cannot represent
      the latter at all. Oct-Mar is the recharge season at this site, which is
      the quantity the water balance is about.

      Note the overlap with MSL_SPRING_MONTHS = (3, 4, 5): March belongs to both
      the hydrological winter and the MSL5 spring. That is not double counting —
      they answer different questions, a winter recharge total against a spring
      mean level — but a reader comparing the two should know the month is in
      both.

      The year attribution does NOT move the trend, only the labels: forward
      and backward attribution group the same months into the same winters and
      differ by a shift in the x-axis, so the slope is identical. Verified
      2026-08-23. Only complete seasons are used.
    """
    import numpy as np

    def _ols(y, x):
        x = np.asarray(x, float); y = np.asarray(y, float)
        m = np.isfinite(x) & np.isfinite(y)
        x, y = x[m], y[m]
        if len(y) < 3:
            return float("nan"), float("nan"), len(y)
        X = np.column_stack([np.ones_like(x), x])
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ b
        s2 = r @ r / (len(y) - 2)
        se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
        return float(b[1]), float(b[1] / se[1]), int(len(y))

    d = climate[(climate.index.year >= year_first)
                & (climate.index.year <= year_last)].copy()
    d["P"] = d["P_m"] * 1000.0
    d["PET_mm"] = d["PET"] * 1000.0
    d["bal"] = d["P"] - d["PET_mm"]
    d["yr"] = d.index.year
    # Winter keyed to the year its October falls in — the convention used by the
    # winter-maximum extraction in this script, and therefore by the flooding
    # analysis. Do not change it here without changing it there.
    d["wyr"] = np.where(d.index.month >= 10, d.index.year, d.index.year - 1)

    ann = d.groupby("yr").agg(PET=("PET_mm", "sum"), bal=("bal", "sum"),
                              n=("bal", "size"))
    ann = ann[ann["n"] == 12]
    # JJAS, matching SUMMER_MONTHS and the summer-minimum extraction. NOT Apr-Sep.
    smr = d[d.index.month.isin([6, 7, 8, 9])].groupby("yr").agg(
        bal=("bal", "sum"), n=("bal", "size"))
    smr = smr[smr["n"] == 4]
    wtr = d[d.index.month.isin([10, 11, 12, 1, 2, 3])].groupby("wyr").agg(
        P=("P", "sum"), bal=("bal", "sum"), n=("bal", "size"))
    wtr = wtr[wtr["n"] == 6]

    out = {}
    for key, series in (("annual_pet", ann["PET"]),
                        ("winter_rainfall", wtr["P"]),
                        ("summer_balance", smr["bal"]),
                        ("winter_balance", wtr["bal"]),
                        ("annual_balance", ann["bal"])):
        slope, tstat, n = _ols(series.values, series.index.values)
        out[key] = {"slope": slope, "t": tstat, "n": n}
    out["era"] = f"{year_first}-{year_last}"
    return out


def pet_long_record_context(climate_full, windows=((1931, 2025), (1960, 2025),
                                                   (1990, 2025))) -> dict:
    """Annual-PET trend over successively shorter windows, and the variability
    of PET against winter rainfall.

    WHY BOTH, AND WHY THE LONG WINDOWS

      Section 4.10.3 quotes the PET trend over the well record (+1.96 mm/yr,
      t = 2.67). Quoted alone that is a nineteen-year figure presented as a
      rate — which is the exact error the same subsection warns against two
      paragraphs later when it cautions that a short-window trend reports which
      years fall inside the window. The long-record trends are therefore emitted
      beside it so the short one can be read against them. They are nested and
      all end in the same year, so they establish that the trend is of long
      standing and STEEPENING; they do not constitute a test of acceleration and
      must not be quoted as one (Martin, 2026-08-23).

      The variability statistics answer the question the significance pattern
      raises. Winter rainfall's trend is the LARGER of the two in millimetres
      and the smaller relative to its own noise: PET varies by about 3% about
      its mean where winter rainfall varies by about 19%. Significance here is a
      statement about signal-to-noise, not about magnitude, and a reader who is
      told only the t-statistics will draw the wrong conclusion about which
      quantity is moving more.
    """
    import numpy as np

    def _ols(y, x):
        x = np.asarray(x, float); y = np.asarray(y, float)
        m = np.isfinite(x) & np.isfinite(y)
        x, y = x[m], y[m]
        if len(y) < 3:
            return float("nan"), float("nan"), len(y)
        X = np.column_stack([np.ones_like(x), x])
        b, *_ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ b
        s2 = r @ r / (len(y) - 2)
        se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
        return float(b[1]), float(b[1] / se[1]), int(len(y))

    out = {"windows": {}}
    for y0, y1 in windows:
        d = climate_full[(climate_full.index.year >= y0)
                         & (climate_full.index.year <= y1)].copy()
        d["yr"] = d.index.year
        d["PET_mm"] = d["PET"] * 1000.0
        ann = d.groupby("yr").agg(PET=("PET_mm", "sum"), n=("PET_mm", "size"))
        ann = ann[ann["n"] == 12]
        slope, tstat, n = _ols(ann["PET"].values, ann.index.values)
        out["windows"][f"{y0}_{y1}"] = {"slope": slope, "t": tstat, "n": n,
                                        "era": f"{y0}-{y1}"}
    return out


def series_variability(climate, year_first: int = 2007,
                       year_last: int = 2025) -> dict:
    """Mean, sd and coefficient of variation for annual PET and winter rainfall.

    Seasons as everywhere else in this script: winter is Oct-Mar, keyed to the
    year its October falls in. Complete seasons only.
    """
    import numpy as np
    d = climate[(climate.index.year >= year_first)
                & (climate.index.year <= year_last)].copy()
    d["P"] = d["P_m"] * 1000.0
    d["PET_mm"] = d["PET"] * 1000.0
    d["yr"] = d.index.year
    d["wyr"] = np.where(d.index.month >= 10, d.index.year, d.index.year - 1)
    ann = d.groupby("yr").agg(PET=("PET_mm", "sum"), n=("PET_mm", "size"))
    ann = ann[ann["n"] == 12]
    wtr = d[d.index.month.isin([10, 11, 12, 1, 2, 3])].groupby("wyr").agg(
        P=("P", "sum"), n=("P", "size"))
    wtr = wtr[wtr["n"] == 6]
    out = {"era": f"{year_first}-{year_last}"}
    for key, ser in (("annual_pet", ann["PET"]), ("winter_rainfall", wtr["P"])):
        mu = float(ser.mean()); sd = float(ser.std(ddof=1))
        out[key] = {"mean": mu, "sd": sd,
                    "cv_pct": 100.0 * sd / mu if mu else float("nan"),
                    "n": int(len(ser))}
    return out


def main() -> None:
    banner("00", "Climate Summary", version=__version__)
    make_all_dirs()

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "axes.labelsize": 12,
            "axes.titlesize": 14,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    _run_all()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        error(f"{exc}")
        raise
