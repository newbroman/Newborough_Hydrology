"""
35_per_well_amplification.py — Per-well climate-sensitivity coefficient (amplification metric)
==============================================================================================

A frame-independent per-well coefficient describing how much each well magnifies (>1) or
damps (<1) the shared SPRING climate swing, co-temporally normalised so wells measured on
different extreme-year subsets stay comparable, SSM-calibrated, and extended to short /
inconsistent-record wells that the Script 33 matched surface and the SSM cannot reach.

This is the discrete per-well COMPANION to Script 33's interpolated field. It produces NO
surface — a coefficient table (with CI + confidence tier), an SSM-calibration figure, and a
discrete per-well marker map — so it does not duplicate Script 33's maps.

Method (locked spec, 2026-06-27; SPEC_script35_per_well_amplification_metric.md)
  * Spring value per well-year = mean of available MAM (config.MSL_SPRING_MONTHS).
  * Extreme-year pools (antecedent-screened supersets of the canonical + recent sets):
        DRY = config.ENVELOPE_METRIC_DRY_POOL   WET = config.ENVELOPE_METRIC_WET_POOL
  * Per-well state = mean over the pool years the well holds (>=1 of each required).
  * Co-temporal normalisation: reference core = wells with FULL dry coverage (all DRY_POOL
    years) and >= ENVELOPE_METRIC_REF_MIN_WET wet years; the coefficient is the well's swing
    divided by the core's mean swing RECOMPUTED over that well's own extreme years. This
    cancels the common climate signal window-by-window, so it reproduces the matched-window
    amplification (validated r ~ 0.98) while removing coverage artefacts (e.g. the CEH9/CEH39
    25 m step on the Figure 60a surface, where CEH39 lacks the extreme 2012 spring).
  * Confidence tiers: A (>=2 dry & >=2 wet), B (>=1 each, not A), C (1 dry & 1 wet).
  * CI: delete-one-extreme-year jackknife; for singleton sides (tier C / n=1), the within-state
    single-year noise (estimated from the multi-year wells) is folded in. 90% (z=1.645).
  * Validation: the coefficient tracks the independently-fitted SSM response (amp vs beta_2,
    amp vs beta_3); calibration regression written to the figure + results.

Honesty: the coefficient is validated where beta_2 exists (long-record wells). Short-record
wells are both the use case and the place it cannot be directly verified — the tiers, CIs and
the beta_2/beta_3 calibration are how that extrapolation is kept honest. Language throughout is
"consistent with the fitted drainage/draw response", never "confirms".

Inputs
  outputs/01_wells_clean.csv      spring levels
  outputs/01_locations.csv        well E/N
  outputs/03_master_data.csv      beta_1/2/3 + Cluster (calibration + cluster)
  outputs/06_pear_membership_audit_sitewide.csv   cluster fallback for unclustered wells

Version: 1.0.0 (2026-06-27)
"""

from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D

from utils import config, paths
from utils import envelope_metric as em
from utils.map_utils import load_dem_hillshade, add_kml_features, add_en_axes
from utils.console_utils import banner, phase, step, info, saved, note, result, done, hr

SCRIPT_ID = "35"
VERSION = "1.0.0"

# --- method constants (from utils.config) -----------------------------------------
SPRING_MONTHS = config.MSL_SPRING_MONTHS
DRY_POOL = config.ENVELOPE_METRIC_DRY_POOL
WET_POOL = config.ENVELOPE_METRIC_WET_POOL
REF_MIN_WET = config.ENVELOPE_METRIC_REF_MIN_WET
CI_Z = config.ENVELOPE_METRIC_CI_Z
LAKE_GAUGE_KEYS = config.LAKE_GAUGE_KEYS

# --- paths ------------------------------------------------------------------------
OUT_DIR = paths.DIR_35
OUT_CSV = paths.OUT_35_PER_WELL
OUT_FIG_CALIB = paths.OUT_35_FIG_CALIB
OUT_FIG_MARKERS = paths.OUT_35_FIG_MARKERS
OUT_TXT = paths.OUT_35_RESULTS

IN_WELLS = paths.INT_WELLS_CLEAN
IN_LOCATIONS = paths.INT_LOCATIONS
IN_MASTER = paths.OUT_DIR / "03_master_data.csv"
IN_MEMBERSHIP = paths.OUT_DIR / "06_pear_membership_audit_sitewide.csv"


# =================================================================================
# Data
# =================================================================================
def load_inputs():
    levels = pd.read_csv(IN_WELLS, index_col=0, parse_dates=True)
    drop = [c for c in levels.columns if c.lower().strip() in LAKE_GAUGE_KEYS]
    if drop:
        levels = levels.drop(columns=drop)
    loc = pd.read_csv(IN_LOCATIONS)
    loc["key"] = loc["Name"].astype(str).str.lower().str.strip()
    master = pd.read_csv(IN_MASTER)
    master["key"] = master["Name_Original"].astype(str).str.lower().str.strip()
    membership = None
    if IN_MEMBERSHIP.exists():
        membership = pd.read_csv(IN_MEMBERSHIP)
        membership["key"] = membership["Well_Normalised"].astype(str).str.lower().str.strip()
    return levels, loc, master, membership


def spring_year_table(levels):
    spring = levels[levels.index.month.isin(SPRING_MONTHS)]
    return spring.groupby(spring.index.year).mean(numeric_only=True)


# =================================================================================
# Co-temporal amplification + CI  (compute lives in utils.envelope_metric — single source)
# =================================================================================
def attach_cluster_loc_beta(df, loc, master, membership):
    df = df.merge(master[["key", "Cluster", "beta_2_atmospheric_draw", "beta_3_drainage"]],
                  on="key", how="left")
    if membership is not None:
        bm = membership.set_index("key")["Best_Match_Cluster"].to_dict()
        miss = df["Cluster"].isna()
        df.loc[miss, "Cluster"] = df.loc[miss, "key"].map(bm)
    df = df.merge(loc[["key", "E", "N"]], on="key", how="left")
    return df


# =================================================================================
# Figures
# =================================================================================
def fig_calibration(df, out_path, calib_exclude=None):
    """amp coefficient vs the independently-fitted SSM beta_2 / beta_3 — the mechanistic
    grounding. The regression uses only wells with RELIABLE β; SSM-unreliable wells
    (calib_exclude, e.g. CEH13/CEH14 whose fit failed) are shown as hollow markers but NOT
    fitted — you cannot validate a coefficient against a failed fit. Metric-only wells (no
    fitted β) are the extrapolation set."""
    from scipy.stats import pearsonr
    calib_exclude = set(calib_exclude or [])
    colours = config.get_cluster_colours()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (xc, xlab) in zip(axes, [("beta_2_atmospheric_draw", "β₂ atmospheric draw"),
                                      ("beta_3_drainage", "β₃ drainage")]):
        full = df.dropna(subset=[xc, "amp_coefficient"])
        unrel = full[full.key.isin(calib_exclude)]
        s = full[~full.key.isin(calib_exclude)]                  # reliable-β wells only -> regression
        for cid in sorted(s.Cluster.dropna().unique()):
            ss = s[s.Cluster == cid]
            ax.scatter(ss[xc], ss.amp_coefficient, c=[colours.get(int(cid), "#444")],
                       edgecolor="k", linewidth=0.4, s=55,
                       label=config.CLUSTER_LABELS.get(int(cid), f"C{int(cid)}"))
        if len(unrel):
            ax.scatter(unrel[xc], unrel.amp_coefficient, facecolor="none", edgecolor="k",
                       marker="D", s=75, linewidths=1.4,
                       label="SSM-unreliable β\n(shown, not fitted)")
        if len(s) > 3:
            r, p = pearsonr(s[xc], s.amp_coefficient)
            b, a = np.polyfit(s[xc], s.amp_coefficient, 1)
            xs = np.linspace(s[xc].min(), s[xc].max(), 50)
            ax.plot(xs, a + b * xs, "k--", lw=1.2, alpha=0.7)
            ax.set_title(f"coefficient vs {xlab}\nPearson r = {r:+.2f} (p = {p:.3f}, n = {len(s)})", fontsize=10)
        ax.axhline(1.0, color="grey", lw=0.7, ls=":")
        ax.set_xlabel(xlab)
        ax.set_ylabel("per-well amplification coefficient")
    axes[0].legend(fontsize=7.5, loc="upper left", title="cluster")
    n_only = int(df["beta_2_atmospheric_draw"].isna().sum())
    fig.suptitle("Script 35 — the per-well coefficient is mechanistically grounded: it tracks the "
                 f"independently-fitted SSM response\n({n_only} short-record wells have no fitted β — "
                 "the extrapolation set the coefficient exists to reach)", fontsize=10.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig_markers(df, out_path):
    """Discrete per-well coefficient map — colour = coefficient, marker = confidence tier.
    NO interpolation (this is deliberately not a surface; that is Script 33's job)."""
    d = df.dropna(subset=["E", "N"]).copy()
    norm = TwoSlopeNorm(vcenter=1.0, vmin=0.55, vmax=1.55)
    cmap = plt.get_cmap("RdBu_r")
    fig, ax = plt.subplots(figsize=(11, 9))
    load_dem_hillshade(ax, paths.DATA_DIR, alpha=1.0, vert_exag=3.0, zorder=1)
    add_en_axes(ax, osgb_label=False)
    add_kml_features(ax, paths.DATA_DIR)
    tier_style = {"A": dict(marker="o", s=85, lw=0.6), "B": dict(marker="s", s=85, lw=1.4),
                  "C": dict(marker="^", s=110, lw=1.8)}
    for t, sty in tier_style.items():
        s = d[d.tier == t]
        if not len(s):
            continue
        ax.scatter(s.E, s.N, c=cmap(norm(s.amp_coefficient.values)),
                   edgecolor="k", zorder=5, **sty)
    add_en_axes(ax, apply_extent=False, osgb_label=False)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label("per-well amplification coefficient  (>1 amplifies, <1 damps)", fontsize=9.5)
    handles = [Line2D([0], [0], marker=tier_style[t]["marker"], markerfacecolor="#bbb",
                      markeredgecolor="k", markeredgewidth=tier_style[t]["lw"], linestyle="none",
                      markersize=9, label=f"Tier {t}")
               for t in ["A", "B", "C"] if (d.tier == t).any()]
    ax.legend(handles=handles, fontsize=8.5, loc="lower left", framealpha=0.9,
              title="confidence (record completeness)")
    ax.set_title("Newborough Warren: per-well spring climate-sensitivity coefficient\n"
                 "Co-temporal normalisation (artefact-free); discrete per-well — not interpolated. "
                 "Marker = confidence tier.", fontsize=10.5, loc="left")
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


# =================================================================================
# Validation (co-temporal reproduces the matched-window amplification)
# =================================================================================
def matched_window_check(yr, df):
    """Cross-check: per-well coefficient vs a simple matched-window amplification on the
    canonical years, for the wells present in both. Reports r / bias to the results file."""
    from scipy.stats import pearsonr
    dyrs = [y for y in DRY_POOL if y in (2011, 2012, 2019)]
    wyrs = [y for y in WET_POOL if y in (2014, 2016, 2021, 2024)]
    ds = yr.reindex(dyrs); ws = yr.reindex(wyrs)
    keep = [c for c in yr.columns if ds[c].notna().sum() >= 2 and ws[c].notna().sum() >= 2]
    sw = (ws[keep].mean() - ds[keep].mean()) * 1000.0
    matched = (sw / sw.mean()).rename("amp_matched")
    matched.index = [k.lower().strip() for k in matched.index]
    J = df.set_index("key")[["amp_coefficient"]].join(matched, how="inner").dropna()
    if len(J) < 5:
        return None
    r, _ = pearsonr(J.amp_coefficient, J.amp_matched)
    bias = (J.amp_coefficient - J.amp_matched)
    return dict(n=len(J), r=r, bias=bias.mean(), max_dev=bias.abs().max())


# =================================================================================
# Main
# =================================================================================
def main() -> int:
    banner(SCRIPT_ID, "Per-well climate-sensitivity coefficient (amplification metric)", VERSION)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    phase(1, "Load inputs")
    levels, loc, master, membership = load_inputs()
    yr = spring_year_table(levels)
    info(f"spring months {SPRING_MONTHS}; dry pool {DRY_POOL}; wet pool {WET_POOL}")

    phase(2, "Reference core + per-well coefficients")
    # Blanket include: amplification coefficient is observational, so CEH13/CEH14 are INCLUDED
    # (lake gauge only excluded). MSL5/SSM exclusion is retained for the calibration regression.
    excluded = set(config.ENVELOPE_METRIC_EXCLUDE) | set(LAKE_GAUGE_KEYS)
    df = em.coefficients(yr, DRY_POOL, WET_POOL, excluded,
                         ref_min_wet=REF_MIN_WET, with_ci=True, ci_z=CI_Z)
    core_n = df.attrs.get("reference_core_n"); sigma_year = df.attrs.get("sigma_year_mm", 0.0)
    info(f"reference core = {core_n} full-dry-coverage wells; single-year σ = {sigma_year:.0f} mm; "
         f"blanket include (CEH13/14 in; lake gauge out)")
    df = attach_cluster_loc_beta(df, loc, master, membership)
    result("wells with a coefficient", str(len(df)))
    tiers = df.tier.value_counts().to_dict()
    result("by tier", "  ".join(f"{t}={tiers.get(t, 0)}" for t in ["A", "B", "C"]))
    metric_only = sorted(df[df.beta_2_atmospheric_draw.isna()].key)
    result("short-record (no fitted β₂)", f"{len(metric_only)}: {metric_only}")

    phase(3, "Validation vs matched-window amplification")
    chk = matched_window_check(yr, df)
    if chk:
        step(f"co-temporal vs matched: n={chk['n']}  r={chk['r']:.3f}  "
             f"bias={chk['bias']:+.3f}  max|dev|={chk['max_dev']:.3f}")

    phase(4, "SSM calibration")
    from scipy.stats import pearsonr
    calib_exclude = set(config.ENVELOPE_METRIC_CALIB_EXCLUDE)
    calib = {}
    for b, lab in [("beta_2_atmospheric_draw", "β₂"), ("beta_3_drainage", "β₃")]:
        s = df[~df.key.isin(calib_exclude)].dropna(subset=[b, "amp_coefficient"])
        if len(s) > 3:
            r, p = pearsonr(s.amp_coefficient, s[b])
            calib[lab] = (r, p, len(s))
            step(f"amp vs {lab}: r={r:+.2f} (p={p:.3f}, n={len(s)}; SSM-unreliable dropped)")
    if calib_exclude:
        step(f"calibration drops SSM-unreliable wells (β untrustworthy): {sorted(calib_exclude)}")

    phase(5, "Render figures")
    fig_calibration(df, OUT_FIG_CALIB, calib_exclude=calib_exclude); saved(OUT_FIG_CALIB)
    fig_markers(df, OUT_FIG_MARKERS); saved(OUT_FIG_MARKERS)

    phase(6, "Write outputs")
    cols = ["key", "Cluster", "E", "N", "dry_m", "wet_m", "swing_mm", "amp_coefficient",
            "ci_lo", "ci_hi", "se", "n_dry", "n_wet", "tier", "dry_2012_present",
            "beta_2_atmospheric_draw", "beta_3_drainage"]
    out = df[[c for c in cols if c in df.columns]].sort_values("amp_coefficient", ascending=False)
    out.to_csv(OUT_CSV, index=False); saved(OUT_CSV)

    lines = [f"Per-well spring climate-sensitivity coefficient (Script {SCRIPT_ID} v{VERSION})",
             f"spring months {SPRING_MONTHS}; dry pool {DRY_POOL}; wet pool {WET_POOL}",
             f"reference core = {core_n} full-dry-coverage wells; single-year σ = {sigma_year:.0f} mm",
             f"wells with a coefficient: {len(df)}  (tiers: " +
             ", ".join(f"{t}={tiers.get(t, 0)}" for t in ['A', 'B', 'C']) + ")",
             f"short-record wells (no fitted β₂, the extrapolation set): {metric_only}", ""]
    if chk:
        lines.append(f"VALIDATION — co-temporal reproduces matched-window amplification: "
                     f"n={chk['n']}, r={chk['r']:.3f}, mean bias={chk['bias']:+.3f}, "
                     f"max|dev|={chk['max_dev']:.3f}")
    for lab, (r, p, n) in calib.items():
        lines.append(f"CALIBRATION — coefficient vs SSM {lab}: r={r:+.2f} (p={p:.3f}, n={n})")
    lines += ["",
              "NOTE: co-temporal normalisation removes coverage artefacts present in the Script 33",
              "matched surface (e.g. the CEH9/CEH39 25 m step — CEH39 lacks the extreme 2012 spring).",
              "It re-anchors the scale relative to 33's naive panel-mean convention (forest ~1.5x ->",
              "~1.6x): a normalisation-convention difference, not a correction to either product.",
              "The coefficient is validated where β₂ exists (long record); for short-record wells the",
              "tiers and CIs carry the extrapolation honestly — read as 'consistent with' the fitted",
              "drainage/draw response, not as confirmation."]
    OUT_TXT.write_text("\n".join(lines) + "\n"); saved(OUT_TXT)
    hr()
    done(SCRIPT_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
