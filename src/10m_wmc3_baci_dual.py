#!/usr/bin/env python3
"""
====================================================================================
10m — WMC3 vs FOREST-CONTROL DUAL-PANEL INTERVENTION FIGURE
====================================================================================

Purpose
-------
A summary, interpretation-first figure of the Impact well WMC3 against the
Forest-control tier mean, across the three management interventions that bracket
the record: April 2015 scraping (CEH36 slack, 262 m south of WMC3), December 2017
Corsican-pine clearfell (~8 ha), and October 2023 re-scraping (CEH18/CEH21).

The figure exists because the 10a ANCOVA reports the clearfell as a climate-
corrected +120 mm step (the headline), whereas the raw, uncorrected before/after
evidence is easier to read as a difference-in-differences (DiD) on the WMC3 minus
forest-control gap.  Both are legitimate; this figure shows the raw evidence and
labels the ANCOVA headline on the plot so the two never come adrift.

Two panels, shared x-axis:

  (a)  WMC3 and forest-control-mean displacement (h_disp = DRAINAGE_DATUM + depth),
       6-month rolling means (bold) over faint monthly values, with the gap shaded
       and per-era mean bars.  Three dated intervention lines.  A boxed note carries
       the ANCOVA clearfell step alongside the raw DiD step.

  (b)  BACI difference (WMC3 - forest control), 6-month rolling mean over faint
       monthly values, per-era mean bars, zero line.  The three consecutive-era
       DiD steps are annotated at their boundaries.

Interpretation (even-handed framing — see project guardrails)
------------------------------------------------------------
The two scraping events each draw the WMC3-minus-control gap DOWN (drainage of the
neighbouring aquifer toward the lowered scrape surface); the clearfell raises it
(interception and transpiration demand removed).  The DiD removes climate shared by
both wells by construction, but NOT differential climate sensitivity, so the
scraping steps are described as "consistent with scraping drawdown" rather than as
a confirmed propagation magnitude.  The ANCOVA scraping covariate coefficients are
NOT plotted or quoted here: in the 10a model they are nuisance terms whose sign is
determined by variance partitioning against the CWB and easting-x-time covariates,
and they invert relative to the raw gap.

Inputs
------
  utils/clearfell_common.load_clearfell_data() — wells, tiers, dates
  outputs/10_clearfell_baci/10a_report_numbers.csv — ANCOVA clearfell step + CI + p
    (row ANCOVA_Forest_Impact_clearfell_step; loaded live, never hardcoded)

Outputs
-------
  outputs/10_clearfell_baci/10m_01_wmc3_baci_era_steps.csv
  outputs/10_clearfell_baci/10m_02_wmc3_baci_dual.png
  outputs/10_clearfell_baci/10m_report_numbers.csv
====================================================================================
"""

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os

from utils.console_utils import (
    banner, phase, info, saved, warn, done, result, hr,
)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

from utils.paths import (
    make_all_dirs, OUT_10A_REPORT,
    OUT_10M_ERA_STEPS, OUT_10M_DUAL_FIG, OUT_10M_REPORT,
)
from utils.clearfell_common import (
    load_clearfell_data,
    INTERVENTION_DATE, SCRAPING_DATE, SCRAPING_DATE_2,
    IMPACT_WELLS, FOREST_CONTROL_WELLS,
    ReportNumbers,
)
from utils.config import DRAINAGE_DATUM
from utils.render_utils import render_figure

__version__ = "1.1.0"  # Hollingham (2026) — 2026-07-04
#
# Nothing in this module should restate a pipeline result as a literal: model
# inputs come from utils/config.py, pipeline-derived quantities are read live
# from the committed CSVs (falling back to utils/pipeline_params.default_value()
# with a console warning on a first pass).


# ── House style (matches Script 10a) ─────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
})

_ROLL_WINDOW = 6          # months, centred
_ROLL_MINP   = 3

# Panel colours (aligned with the tier palette: WMC3 red, forest-control purple
# for the well pair; the BACI difference gets its own blue).
COL_WMC3  = '#D73027'
COL_CTRL  = '#7f77dd'
COL_BACI  = '#1a6faf'
COL_GAP   = '#f0c8c4'     # light red — shaded well gap in panel (a)
COL_BGAP  = '#c0d8f0'     # light blue — shaded BACI in panel (b)


# ── Data assembly ────────────────────────────────────────────────────────────
def build_series(wells):
    """WMC3 and forest-control-mean displacement, plus their difference.

    Displacement h_disp = DRAINAGE_DATUM + depth.  The datum cancels in the
    BACI difference, but both series are carried in displacement units so the
    two panels share a consistent vertical convention.
    """
    impact = IMPACT_WELLS[0]
    if impact not in wells.columns:
        raise KeyError(f"Impact well {impact!r} not found in wells frame.")

    ctrl_present = [w for w in FOREST_CONTROL_WELLS if w in wells.columns]
    missing = [w for w in FOREST_CONTROL_WELLS if w not in wells.columns]
    if missing:
        warn(f"Forest-control wells absent from data: {', '.join(missing)}")
    if not ctrl_present:
        raise KeyError("No forest-control wells present in wells frame.")

    df = pd.DataFrame(index=wells.index)
    df['wmc3'] = DRAINAGE_DATUM + wells[impact]
    df['ctrl'] = DRAINAGE_DATUM + wells[ctrl_present].mean(axis=1)
    df['baci'] = df['wmc3'] - df['ctrl']
    return df, impact, ctrl_present


def era_masks(index):
    """Four eras bracketed by the three intervention dates."""
    return [
        ('Pre-2015 scrape (baseline)',   index <  SCRAPING_DATE),
        ('Post-2015 scrape / pre-fell', (index >= SCRAPING_DATE)  & (index < INTERVENTION_DATE)),
        ('Post-clearfell / pre-2023',   (index >= INTERVENTION_DATE) & (index < SCRAPING_DATE_2)),
        ('Post-2023 scrape',             index >= SCRAPING_DATE_2),
    ]


def compute_era_steps(df):
    """Per-era means of the BACI gap and the consecutive-era DiD steps."""
    eras = era_masks(df.index)
    rows = []
    for name, mask in eras:
        s = df.loc[mask, 'baci']
        rows.append({
            'era': name,
            'baci_mean_m': s.mean(),
            'n_months': int(s.notna().sum()),
        })
    era_df = pd.DataFrame(rows)

    steps = []
    labels = [
        ('2015 scraping', 0, 1),
        ('2017 clearfell', 1, 2),
        ('2023 scraping', 2, 3),
    ]
    for label, i, j in labels:
        d = era_df.loc[j, 'baci_mean_m'] - era_df.loc[i, 'baci_mean_m']
        steps.append({
            'transition': label,
            'from_era': era_df.loc[i, 'era'],
            'to_era':   era_df.loc[j, 'era'],
            'did_step_m': d,
            'direction': 'falls' if d < 0 else 'rises',
        })
    step_df = pd.DataFrame(steps)
    return era_df, step_df


def load_ancova_clearfell(path):
    """Live ANCOVA clearfell step (m), p-string and CI from 10a_report_numbers."""
    if not path.exists():
        warn(f"10a report numbers not found at {path}; ANCOVA note omitted.")
        return None
    rn = pd.read_csv(path)
    row = rn[rn['Parameter'] == 'ANCOVA_Forest_Impact_clearfell_step']
    if row.empty:
        warn("ANCOVA_Forest_Impact_clearfell_step row absent; note omitted.")
        return None
    val_m = float(row['Value'].iloc[0])
    note_str = str(row['Note'].iloc[0])
    return {'step_m': val_m, 'note': note_str}


# ── Figure ───────────────────────────────────────────────────────────────────
def _roll(series):
    return series.rolling(_ROLL_WINDOW, center=True, min_periods=_ROLL_MINP).mean()


def _intervention_lines(ax, top_labels=False, y_top=None):
    specs = [
        (SCRAPING_DATE,   '#888888', '--', 1.0, 'Apr 2015\nCEH36 scraping'),
        (INTERVENTION_DATE, '#111111', '-', 1.6, 'Dec 2017\nCorsican pine\nclearfell (~8 ha)'),
        (SCRAPING_DATE_2, '#888888', ':',  1.0, 'Oct 2023\nCEH18/21\nre-scraping'),
    ]
    for dt, col, ls, lw, label in specs:
        ax.axvline(dt, color=col, ls=ls, lw=lw, zorder=2)
        if top_labels:
            ax.text(dt + pd.Timedelta(days=28), y_top, label,
                    fontsize=8, color=col, va='top', ha='left',
                    bbox=dict(fc='white', ec='none', alpha=0.78, pad=1.5))


def make_figure(df, era_df, step_df, ancova, impact, ctrl_present, out_path):
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), dpi=300,
                             gridspec_kw={'height_ratios': [1.6, 1]})
    fig.subplots_adjust(hspace=0.08)

    eras = era_masks(df.index)
    x0, x1 = df.index[0], df.index[-1]

    # ── Panel (a): well pair with shaded gap ─────────────────────────────────
    ax = axes[0]
    r_w = _roll(df['wmc3'])
    r_c = _roll(df['ctrl'])

    ax.plot(df.index, df['wmc3'], color=COL_WMC3, alpha=0.18, lw=0.7)
    ax.plot(df.index, df['ctrl'], color=COL_CTRL, alpha=0.18, lw=0.7)

    v = r_w.notna() & r_c.notna()
    ax.fill_between(df.index[v], r_w[v], r_c[v], color=COL_GAP, alpha=0.6,
                    zorder=1, label='BACI gap (WMC3 − forest control)')
    ax.plot(df.index, r_w, color=COL_WMC3, lw=2.0, zorder=3,
            label='WMC3  (C4 Impact well)')
    ax.plot(df.index, r_c, color=COL_CTRL, lw=2.0, ls='--', zorder=3,
            label='Forest control mean  ('
                  + '/'.join(w.upper() for w in ctrl_present) + ')')

    for name, mask in eras:
        mw = df.loc[mask, 'wmc3'].mean()
        mc = df.loc[mask, 'ctrl'].mean()
        t0 = df.index[mask][0] if mask.any() else x0
        t1 = df.index[mask][-1] if mask.any() else x1
        if pd.notna(mw):
            ax.hlines(mw, t0, t1, color=COL_WMC3, lw=2.2, alpha=0.9, zorder=4)
        if pd.notna(mc):
            ax.hlines(mc, t0, t1, color=COL_CTRL, lw=2.2, ls='--', alpha=0.9, zorder=4)

    y_lo, y_hi = ax.get_ylim()
    pad = (y_hi - y_lo) * 0.02
    _intervention_lines(ax, top_labels=True, y_top=y_hi - pad)

    ax.set_ylabel('Water-table displacement, h$_{disp}$ (m above datum)')
    ax.set_title('(a)  WMC3 and forest-control mean: water-table displacement  '
                 '(6-month rolling mean)', fontsize=12, loc='left', pad=6)
    ax.legend(loc='lower left', frameon=True, framealpha=0.95, fontsize=9, ncol=3)
    ax.grid(axis='y', color='#e8e8e8', lw=0.6)
    ax.set_xlim(x0, x1)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.set_xticklabels([])

    # On-figure ANCOVA note beside the raw DiD clearfell step
    did_fell = step_df.loc[step_df['transition'] == '2017 clearfell',
                           'did_step_m'].iloc[0] * 1000
    if ancova is not None:
        anc_mm = ancova['step_m'] * 1000
        note_txt = (
            f"Clearfell step:\n"
            f"ANCOVA climate-corrected +{anc_mm:.0f} mm (p<0.001);\n"
            f"raw difference-in-differences +{did_fell:.0f} mm.\n"
            f"The two differ because the raw step is\n"
            f"uncorrected for climate."
        )
        ax.text(0.985, 0.04, note_txt, transform=ax.transAxes,
                fontsize=8.2, va='bottom', ha='right', color='#222222',
                bbox=dict(boxstyle='round,pad=0.5', fc='#fbf7e8',
                          ec='#b0a060', lw=0.8, alpha=0.95))

    # ── Panel (b): BACI difference with DiD steps ────────────────────────────
    ax2 = axes[1]
    r_b = _roll(df['baci'])

    ax2.plot(df.index, df['baci'], color=COL_BACI, alpha=0.2, lw=0.8)
    ax2.fill_between(df.index, 0, r_b.where(r_b.notna(), 0),
                     color=COL_BGAP, alpha=0.45, zorder=1)
    ax2.plot(df.index, r_b, color=COL_BACI, lw=2.0, zorder=3,
             label='WMC3 − forest control  (6-month rolling mean)')
    ax2.axhline(0, color='#bbbbbb', lw=0.8)

    era_means_m = {}
    for name, mask in eras:
        mb = df.loc[mask, 'baci'].mean()
        t0 = df.index[mask][0] if mask.any() else x0
        t1 = df.index[mask][-1] if mask.any() else x1
        era_means_m[name] = mb
        if pd.notna(mb):
            ax2.hlines(mb, t0, t1, color=COL_BACI, lw=2.5, alpha=0.9, zorder=4)

    # Annotate the three consecutive-era DiD steps at their boundaries
    boundary_dates = {
        '2015 scraping':  SCRAPING_DATE,
        '2017 clearfell': INTERVENTION_DATE,
        '2023 scraping':  SCRAPING_DATE_2,
    }
    for _, r in step_df.iterrows():
        d_mm = r['did_step_m'] * 1000
        bd = boundary_dates[r['transition']]
        m_from = era_means_m[r['from_era']]
        m_to   = era_means_m[r['to_era']]
        if pd.isna(m_from) or pd.isna(m_to):
            continue
        # Vertical double-arrow just after the boundary
        ax_x = bd + pd.Timedelta(days=120)
        ax2.annotate('', xy=(ax_x, m_to), xytext=(ax_x, m_from),
                     arrowprops=dict(arrowstyle='<->', color='#333333', lw=1.3))
        sign = '+' if d_mm >= 0 else '−'
        ax2.text(ax_x + pd.Timedelta(days=30), (m_from + m_to) / 2,
                 f'{sign}{abs(d_mm):.0f} mm',
                 fontsize=8.5, color='#222222', va='center', ha='left',
                 fontweight='bold')

    ax2.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f'{x*1000:.0f}'))
    ax2.set_ylabel('WMC3 − forest control (mm)')
    ax2.set_title('(b)  BACI difference: WMC3 minus forest-control mean  '
                  '(consecutive-era steps are raw difference-in-differences)',
                  fontsize=12, loc='left', pad=6)
    ax2.legend(loc='upper left', frameon=True, framealpha=0.95, fontsize=9)
    ax2.grid(axis='y', color='#e8e8e8', lw=0.6)
    ax2.set_xlim(x0, x1)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_major_locator(mdates.YearLocator(2))
    _intervention_lines(ax2, top_labels=False)

    render_figure(fig, out_path, facecolor='white')
    plt.close(fig)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    banner("10m", "WMC3 vs forest-control dual-panel intervention figure",
           __version__)
    make_all_dirs()

    phase(1, "Load data")
    wells, _prov, _clim, _master, _locs, _tiers = load_clearfell_data()
    df, impact, ctrl_present = build_series(wells)
    info(f"Impact well: {impact.upper()}   "
         f"Forest control: {', '.join(w.upper() for w in ctrl_present)}")
    info(f"Record: {df.index[0]:%b %Y} – {df.index[-1]:%b %Y}  "
         f"({df['baci'].notna().sum()} paired months)")

    phase(2, "Era means and difference-in-differences steps")
    era_df, step_df = compute_era_steps(df)
    for _, r in era_df.iterrows():
        result(r['era'], f"{r['baci_mean_m']*1000:+.0f} mm  (n={r['n_months']})")
    hr()
    for _, r in step_df.iterrows():
        result(r['transition'],
               f"{r['did_step_m']*1000:+.0f} mm  ({r['direction']})")

    phase(3, "ANCOVA clearfell headline (live from 10a)")
    ancova = load_ancova_clearfell(OUT_10A_REPORT)
    if ancova is not None:
        info(f"ANCOVA clearfell step: {ancova['step_m']*1000:+.0f} mm  "
             f"[{ancova['note']}]")

    phase(4, "Build figure")
    make_figure(df, era_df, step_df, ancova, impact, ctrl_present,
                OUT_10M_DUAL_FIG)
    saved(OUT_10M_DUAL_FIG.name)

    phase(5, "Write outputs")
    era_out = era_df.copy()
    era_out['baci_mean_mm'] = (era_out['baci_mean_m'] * 1000).round(1)
    step_out = step_df.copy()
    step_out['did_step_mm'] = (step_out['did_step_m'] * 1000).round(1)
    # Combined tidy CSV: era means then steps
    era_out.to_csv(OUT_10M_ERA_STEPS, index=False)
    saved(OUT_10M_ERA_STEPS.name)

    rn = ReportNumbers()
    for _, r in step_df.iterrows():
        key = ('WMC3_BACI_DiD_step_'
               + r['transition'].split()[1])  # scraping / clearfell / scraping
        # disambiguate the two scraping transitions by year
        year = r['transition'].split()[0]
        rn.add(f'WMC3_BACI_DiD_step_{year}_{r["transition"].split()[1]}',
               r['did_step_m'], unit='m', well='WMC3',
               era=r['to_era'],
               note=f"raw difference-in-differences, {r['from_era']} → "
                    f"{r['to_era']}; consistent with "
                    f"{'scraping drawdown' if 'scraping' in r['transition'] else 'clearfell recovery'}")
    if ancova is not None:
        rn.add('WMC3_ANCOVA_clearfell_step_ref', ancova['step_m'], unit='m',
               well='WMC3', era='Post_felling',
               note=f"reference copy of 10a headline ({ancova['note']})")
    n = rn.save(OUT_10M_REPORT)
    saved(OUT_10M_REPORT.name, f"{n} rows")

    done("10m")


if __name__ == "__main__":
    main()
