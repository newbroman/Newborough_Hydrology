"""
32_differential_movement.py — Secular differential movement of the spring water table
=====================================================================================

Maps where the spring water table is changing *relative to the Warren as a whole*.
For each well it fits the trend of its anomaly (well minus the site-mean spring
level) against year; the site-mean subtraction removes the common climate signal,
so what remains is the secular *relative* drift — the slow inland mound holding its
position while the fast-draining lake and coastal edges decline.

This is a differential-recession field, NOT an absolute-drying map and NOT a
management-signature map (see PLAN_differential_movement_writeup.md, guard-rails).

Anchor claim (report Step 1):
    "This map shows the secular differential movement of the spring water table
     across Newborough Warren: with the common climate signal removed, the high,
     slow-draining forest mound holds its position while the fast-draining
     lake-edge and coastal margins decline relative to the site as a whole — a
     pattern governed by the aquifer's recession geometry rather than by
     management intervention."

Method (signed-off spec, 2026-06-26):
  * Spring value per well-year = mean of available MAM readings (config.MSL_SPRING_MONTHS).
  * Anomaly = well spring level - site-mean spring level (same year).
  * Site-mean reference panel = wells present in >= PANEL_MIN_FRACTION of the
    period's springs (stable baseline; stops the reference drifting with coverage).
  * Metric = OLS slope of the per-well anomaly vs year. Colour = slope in mm/yr.
  * Per-well trend requires >= PER_WELL_MIN_YEARS spring-years in the period.
  * Significance: lag-1 AR-corrected t-test (effective N), cross-checked against a
    moving-block bootstrap CI. Significant wells drawn solid; non-significant hollow.
  * Exclusions: config.MSL5_EXCLUDED_WELLS (CEH13/CEH14) + the Llyn Rhos-Ddu gauge.
    All other wells retained on equal footing — coastal wells are NOT flagged or
    dropped; cause is the text layer, not a data surgery.
  * Periods: 2011-2025 primary; 2005-2025 robustness check.
  * IDW power 2, 50 m grid, 450 m mask.

Standalone diagnostic — NOT wired into run_analysis.py or paths.py. Pipeline
integration (paths/config constants, orchestrator slot, optional hillshade base via
map_utils.add_idw_surface) is deferred to the Step 3 figure-architecture decision.

Inputs (read at runtime; no values hardcoded):
    outputs/01_wells_clean.csv     per-well monthly levels (depth below ground)
    outputs/01_locations.csv       well E/N
    outputs/03_master_data.csv     per-well cluster id

Outputs (outputs/32_differential_movement/):
    32_differential_movement_per_well.csv   slope, mm/yr, significance, both periods
    32_differential_movement_2011_2025.png  primary map
    32_differential_movement_2005_2025.png  robustness map
    32_results.txt                          console summary

Version: 1.0.0 (2026-06-26)
"""

from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from utils import config, paths
from utils.console_utils import banner, phase, step, info, saved, note, result, done, hr

SCRIPT_ID = "32"
VERSION = "1.0.0"

# --- method constants (signed-off spec) ------------------------------------------
SPRING_MONTHS = config.MSL_SPRING_MONTHS          # (3, 4, 5)
PANEL_MIN_FRACTION = 13.0 / 15.0                  # site-mean reference-panel coverage
PER_WELL_MIN_YEARS = 8                            # min spring-years for a per-well trend
PERIODS = {                                       # (label, first_year, last_year)
    "2011_2025": (2011, 2025),                    # primary
    "2005_2025": (2005, 2025),                    # robustness
}
PRIMARY_PERIOD = "2011_2025"
IDW_POWER = 2
IDW_GRID_M = 50.0                                 # project convention (not 10b's 40 m)
IDW_MASK_M = 450.0                                # mask cells > this from nearest well
LAKE_GAUGE_KEYS = {"llyn rhos", "llyn rhos-ddu", "llyn rhos ddu"}
BOOT_N = 2000
BOOT_BLOCK = 3
BOOT_SEED = 20260626

# --- output paths (local; not in paths.py while standalone) ----------------------
OUT_DIR = paths.OUT_DIR / "32_differential_movement"
OUT_CSV = OUT_DIR / "32_differential_movement_per_well.csv"
OUT_TXT = OUT_DIR / "32_results.txt"
OUT_FIG = {p: OUT_DIR / f"32_differential_movement_{p}.png" for p in PERIODS}

# input CSVs read at runtime
IN_WELLS = paths.INT_WELLS_CLEAN
IN_LOCATIONS = paths.INT_LOCATIONS
IN_MASTER = paths.OUT_DIR / "03_master_data.csv"


# =================================================================================
# Data
# =================================================================================
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load cleaned levels, locations and per-well cluster ids."""
    levels = pd.read_csv(IN_WELLS, index_col=0, parse_dates=True)
    # drop the lake gauge column(s) if present
    drop = [c for c in levels.columns if c.lower().strip() in LAKE_GAUGE_KEYS]
    if drop:
        levels = levels.drop(columns=drop)

    loc = pd.read_csv(IN_LOCATIONS)
    loc["key"] = loc["Name"].astype(str).str.lower().str.strip()

    master = pd.read_csv(IN_MASTER)
    master["key"] = master["Name_Original"].astype(str).str.lower().str.strip()
    return levels, loc, master


def spring_year_table(levels: pd.DataFrame) -> pd.DataFrame:
    """Mean MAM level per well per year. Rows = year, columns = well."""
    spring = levels[levels.index.month.isin(SPRING_MONTHS)]
    return spring.groupby(spring.index.year).mean(numeric_only=True)


def build_anomalies(yr: pd.DataFrame, first: int, last: int) -> tuple[pd.DataFrame, list]:
    """Anomaly table (well minus site-mean each year) over [first, last]."""
    sub = yr.loc[first:last]
    n_years = last - first + 1
    coverage = sub.notna().sum(axis=0)
    panel = coverage[coverage >= PANEL_MIN_FRACTION * n_years].index.tolist()
    site = sub[panel].mean(axis=1, skipna=True)          # stable site-mean trajectory
    anom = sub.sub(site, axis=0)
    return anom, panel


# =================================================================================
# Per-well trend + significance
# =================================================================================
def trend_with_significance(years: np.ndarray, vals: np.ndarray,
                            n_boot: int = BOOT_N, block: int = BOOT_BLOCK,
                            seed: int = BOOT_SEED) -> dict | None:
    """OLS slope of vals vs years with a lag-1 AR-corrected t-test and a
    moving-block bootstrap CI cross-check."""
    mask = np.isfinite(vals)
    x = np.asarray(years, float)[mask]
    y = np.asarray(vals, float)[mask]
    n = len(x)
    if n < PER_WELL_MIN_YEARS:
        return None

    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    resid = y - yhat
    sxx = np.sum((x - x.mean()) ** 2)
    if sxx <= 0:
        return None
    s2 = np.sum(resid ** 2) / (n - 2)
    se_ols = np.sqrt(s2 / sxx) if s2 > 0 else 0.0

    # lag-1 residual autocorrelation, clamped to [0, 0.99)
    rho = np.corrcoef(resid[:-1], resid[1:])[0, 1] if n > 3 else 0.0
    rho = 0.0 if not np.isfinite(rho) else float(max(0.0, min(rho, 0.99)))

    # AR(1)-corrected t-test (variance inflation + effective df)
    se_adj = se_ols * np.sqrt((1 + rho) / (1 - rho)) if rho < 1 else se_ols
    n_eff = max(n * (1 - rho) / (1 + rho), 3.0)
    t = b / se_adj if se_adj > 0 else 0.0
    p_ar = float(2 * stats.t.sf(abs(t), max(n_eff - 2, 1)))

    # moving-block bootstrap of the slope (residual resampling) -> 95% CI
    rng = np.random.default_rng(seed)
    starts_max = n - block
    slopes = np.empty(n_boot)
    for i in range(n_boot):
        if starts_max <= 0:
            res_bs = rng.permutation(resid)[:n]
        else:
            idx: list[int] = []
            while len(idx) < n:
                s = int(rng.integers(0, starts_max + 1))
                idx.extend(range(s, s + block))
            res_bs = resid[np.array(idx[:n])]
        slopes[i] = np.polyfit(x, yhat + res_bs, 1)[0]
    lo, hi = np.percentile(slopes, [2.5, 97.5])
    boot_sig = bool(lo > 0 or hi < 0)

    return dict(
        n=n, slope_m_yr=float(b), slope_mm_yr=float(b * 1000.0),
        rho=rho, n_eff=float(n_eff), se_adj=float(se_adj),
        p_ar=p_ar, sig=bool(p_ar < 0.05),
        boot_lo_mm_yr=float(lo * 1000.0), boot_hi_mm_yr=float(hi * 1000.0),
        boot_sig=boot_sig,
    )


def per_well_trends(yr: pd.DataFrame, loc: pd.DataFrame, master: pd.DataFrame,
                    first: int, last: int, excluded: set) -> pd.DataFrame:
    anom, panel = build_anomalies(yr, first, last)
    rows = []
    for col in anom.columns:
        key = col.lower().strip()
        if key in excluded:
            continue
        res = trend_with_significance(anom.index.values.astype(float), anom[col].values)
        if res is None:
            continue
        res["col"] = col
        res["key"] = key
        rows.append(res)
    out = pd.DataFrame(rows)
    out = out.merge(master[["key", "Cluster"]], on="key", how="left")
    out = out.merge(loc[["key", "E", "N"]], on="key", how="left")
    return out.dropna(subset=["E", "N"]).reset_index(drop=True), panel


# =================================================================================
# Map
# =================================================================================
def idw_surface(px, py, pv, gx, gy, power=IDW_POWER, mask=IDW_MASK_M):
    GX, GY = np.meshgrid(gx, gy)
    num = np.zeros_like(GX)
    den = np.zeros_like(GX)
    nearest = np.full_like(GX, 1e18)
    for x, y, v in zip(px, py, pv):
        dd = np.sqrt((GX - x) ** 2 + (GY - y) ** 2)
        dd = np.where(dd < 1e-6, 1e-6, dd)
        w = 1.0 / dd ** power
        num += w * v
        den += w
        nearest = np.minimum(nearest, dd)
    Z = num / den
    Z[nearest > mask] = np.nan
    return GX, GY, Z


def make_map(df: pd.DataFrame, loc: pd.DataFrame, period_label: str,
             first: int, last: int, out_path):
    colours = config.get_cluster_colours()
    labels = config.CLUSTER_LABELS

    E = loc["E"].values
    N = loc["N"].values
    gx = np.arange(np.nanmin(E) - 150, np.nanmax(E) + 150, IDW_GRID_M)
    gy = np.arange(np.nanmin(N) - 150, np.nanmax(N) + 150, IDW_GRID_M)
    GX, GY, Z = idw_surface(df.E.values, df.N.values, df.slope_mm_yr.values, gx, gy)

    vmax = float(np.nanpercentile(np.abs(df.slope_mm_yr), 98))
    vmax = max(vmax, 1.0)
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-vmax, vmax=vmax)

    fig, ax = plt.subplots(figsize=(9.5, 9))
    im = ax.pcolormesh(GX, GY, Z, cmap=plt.cm.RdBu, norm=norm, shading="auto", alpha=0.92)

    for cid in sorted(df.Cluster.dropna().unique()):
        sub = df[df.Cluster == cid]
        sig = sub[sub.sig]
        nsig = sub[~sub.sig]
        col = colours.get(int(cid), "#444444")
        # significant wells: solid; non-significant: hollow (equal footing, no coast flag)
        ax.scatter(sig.E, sig.N, c=col, edgecolor="k", linewidth=0.6, s=58,
                   zorder=5, label=labels.get(int(cid), f"C{int(cid)}"))
        ax.scatter(nsig.E, nsig.N, facecolor="none", edgecolor=col, linewidth=1.6,
                   s=58, zorder=5)

    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    leg = ax.legend(fontsize=8.5, loc="lower left", framealpha=0.9, title="cluster")
    leg._legend_box.align = "left"
    # significance key
    ax.scatter([], [], c="#555555", edgecolor="k", s=58, label="trend p < 0.05")
    ax.scatter([], [], facecolor="none", edgecolor="#555555", linewidth=1.6, s=58,
               label="not significant")

    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label("Differential drift of spring water table (mm/yr)\n"
                 "site-mean (common climate) removed\n"
                 "blue = holds up vs Warren   red = sinks vs Warren", fontsize=9.5)
    tag = " (primary)" if period_label == PRIMARY_PERIOD else " (robustness)"
    ax.set_title(
        f"Newborough Warren: secular differential movement of the spring water table{tag}\n"
        f"Anomaly trend {first}-{last}; solid = significant (AR-corrected), hollow = not. "
        f"CEH13/14 excluded.",
        fontsize=10.5, loc="left")
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


# =================================================================================
# Main
# =================================================================================
def main() -> int:
    banner(SCRIPT_ID, "Differential water-table movement (anomaly-trend map)", VERSION)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phase(1, "Load inputs")
    levels, loc, master = load_inputs()
    yr = spring_year_table(levels)
    excluded = set(k.lower() for k in config.MSL5_EXCLUDED_WELLS) | LAKE_GAUGE_KEYS
    info(f"spring-year table: {yr.shape[1]} wells x {yr.shape[0]} years "
         f"({int(yr.index.min())}-{int(yr.index.max())})")
    note(f"excluded from trends: {sorted(config.MSL5_EXCLUDED_WELLS)} + lake gauge")

    all_results: dict[str, pd.DataFrame] = {}
    lines: list[str] = []
    for plabel, (first, last) in PERIODS.items():
        phase(2, f"Per-well anomaly trends {first}-{last}")
        df, panel = per_well_trends(yr, loc, master, first, last, excluded)
        all_results[plabel] = df

        n_sig = int(df.sig.sum())
        agree = int((df.sig == df.boot_sig).sum())
        med = df.slope_mm_yr.median()
        step(f"site-mean panel: {len(panel)} wells")
        result(f"{plabel} wells mapped", str(len(df)))
        result(f"{plabel} significant (AR p<0.05)", f"{n_sig}/{len(df)}")
        result(f"{plabel} bootstrap agreement", f"{agree}/{len(df)}")
        result(f"{plabel} median drift", f"{med:+.2f} mm/yr")

        # top movers either way
        up = df.sort_values("slope_mm_yr", ascending=False).head(5)
        dn = df.sort_values("slope_mm_yr").head(5)
        lines.append(f"\n=== {plabel}  ({first}-{last}) ===")
        lines.append(f"site-mean panel: {len(panel)} wells; mapped: {len(df)}; "
                     f"significant: {n_sig}; bootstrap agreement: {agree}/{len(df)}")
        lines.append("holds up (mm/yr): " +
                     ", ".join(f"{r.col} {r.slope_mm_yr:+.2f}{'*' if r.sig else ''}"
                               for r in up.itertuples()))
        lines.append("sinks    (mm/yr): " +
                     ", ".join(f"{r.col} {r.slope_mm_yr:+.2f}{'*' if r.sig else ''}"
                               for r in dn.itertuples()))

        phase(3, f"Render map {plabel}")
        make_map(df, loc, plabel, first, last, OUT_FIG[plabel])
        saved(OUT_FIG[plabel])

    # combined per-well CSV (one row per well, both periods side by side)
    phase(4, "Write per-well CSV")
    base = all_results[PRIMARY_PERIOD][["key", "col", "Cluster", "E", "N"]].copy()
    for plabel, df in all_results.items():
        cols = ["key", "slope_mm_yr", "p_ar", "sig", "rho",
                "boot_lo_mm_yr", "boot_hi_mm_yr", "boot_sig", "n"]
        ren = {c: f"{c}_{plabel}" for c in cols if c != "key"}
        base = base.merge(df[cols].rename(columns=ren), on="key", how="outer")
    base.to_csv(OUT_CSV, index=False)
    saved(OUT_CSV)

    OUT_TXT.write_text("\n".join(lines) + "\n")
    saved(OUT_TXT)
    hr()
    for ln in lines:
        print(ln)
    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
