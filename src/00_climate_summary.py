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
)
from utils.config import REFERENCE_CUTOFF_DATE

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import re
import os
from scipy.stats import linregress

__version__ = "1.0.1"  # Hollingham (2026) — last revised 2026-04-26

# Colorblind-safe palette used throughout the project
CB_BLUE = "#0072B2"
CB_GREEN = "#009E73"
CB_ORANGE = "#E69F00"
CB_RED = "#D55E00"
CB_BROWN = "#8C564B"
CUTOFF_DATE = pd.Timestamp(REFERENCE_CUTOFF_DATE)
MIN_RECORD_MONTHS = 100
DETREND_START = pd.Timestamp("2004-12-01")
DETREND_END = pd.Timestamp("2025-12-01")


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

    summary_row = pd.DataFrame(
        {
            "Year": ["Long-term mean"],
            "Annual_P_mm": [annual["Annual_P_mm"].mean()],
            "Annual_PET_mm": [annual["Annual_PET_mm"].mean()],
            "P_PET_ratio": [annual["P_PET_ratio"].mean(skipna=True)],
            "Months_complete": [annual["Months_complete"].mean()],
            "Notes": ["Mean of yearly values"],
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

        ax4.plot(mean_ts.index, mean_ts, color=CB_GREEN, linewidth=2.3, label="Network mean well level")
        ax4.fill_between(mean_ts.index, mean_ts - std_ts, mean_ts + std_ts, color=CB_GREEN, alpha=0.22, label="Inter-well SD")
        ax4.set_ylabel("Well level (m)")
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
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


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
    ax_tr.set_xlabel("Depth below pipe top (m)")
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
    ax_bl.set_ylabel("Depth below pipe top (m)")
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
    ax_br.set_ylabel("Depth below pipe top (m)")
    ax_br.set_xticks(list(range(1, 13)))
    ax_br.grid(axis="y", linestyle=":", alpha=0.35)

    for ax in (ax_tl, ax_tr, ax_bl, ax_br):
        ax.tick_params(axis="both", labelsize=10)

    fig.tight_layout()
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
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
    df = pd.concat([parsed, raw[["max_temp"]]], axis=1)
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

    meta_rows = pd.DataFrame([
        {"year": "slope_C_per_yr",     "summer_max_mean": round(reg.slope, 5)},
        {"year": "intercept_C",        "summer_max_mean": round(reg.intercept, 3)},
        {"year": "r_squared",          "summer_max_mean": round(reg.rvalue ** 2, 4)},
        {"year": "p_value",            "summer_max_mean": reg.pvalue},
        {"year": "n_years",            "summer_max_mean": int(len(yrs))},
        {"year": "year_range",         "summer_max_mean": f"{int(yrs.min())}-{int(yrs.max())}"},
        {"year": "pre_2013_mean_C",    "summer_max_mean": round(pre_mean, 3)},
        {"year": "post_2013_mean_C",   "summer_max_mean": round(post_mean, 3)},
        {"year": "post_2013_anomaly",  "summer_max_mean": round(anomaly, 3)},
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
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


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
    make_figure1_climate_timeseries(climate_short, wells_short, paths_short["fig1"], "short")
    make_figure2_well_network(wells_short, table2_short, paths_short["fig2"])

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


def main() -> None:
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
        print(f"[ERROR] {exc}")
        raise
