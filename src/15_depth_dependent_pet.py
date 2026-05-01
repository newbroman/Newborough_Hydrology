"""
15_depth_dependent_pet.py
Purpose: Explore a depth-dependent PET coefficient using exponential decay.

The standard SSM (lag-1 headline, displacement formulation) is:
    Δh_t = β₁·P(t−1)  −  β₂·PET(t)  −  β₃·h_disp_prev(t)

    where h_disp = DRAINAGE_DATUM + h_depth     (displacement above 3.7 m datum)

The modified model replaces the fixed β₂ with a depth-dependent term:
    Δh_t = β₁·P(t−1)  −  β₂·exp(−λ·d_{t-1})·PET(t)  −  β₃·h_disp_prev(t)

where d_{t-1} = depth below ground surface at the previous timestep:
    d_{t-1} = −h_{t-1} + mean_cluster_upstand     (m, always ≥ 0)

IMPORTANT: The depth-coupling term d_prev is a PHYSICAL DISTANCE from the
soil surface, used for PET extinction. It is NOT the displacement term.
The displacement h_disp = DRAINAGE_DATUM + h is for the β₃ design matrix
only (hydraulic drainage above a reference base). These are two different
uses of depth and must not be conflated.

λ is a new free parameter (m⁻¹). When λ=0, exp(−λd) = 1 and the standard
SSM is recovered exactly. As λ → ∞, PET influence vanishes at depth.

The physical interpretation: capillary connectivity between root zone and
saturated zone decays exponentially with depth, so evapotranspiration exerts
diminishing influence as the water table falls.

Fitting strategy:
    - Grid search λ over [0, 6] in steps of 0.05
    - At each λ, the modified predictor  −exp(−λ·d)·PET  is linear in β₂,
      so β₁, β₂, β₃ are recovered by no-intercept OLS
    - Best λ selected by iterative NSE on held-out simulation

Outputs (in outputs/15_depth_dependent_pet/):
    15_01_lambda_profile.png        — NSE vs λ for each cluster
    15_02_fit_comparison.png        — Observed vs fitted (best model vs SSM)
    15_03_benchmark_table.csv       — Cluster-level comparison table
    15_04_best_params.csv           — Optimal λ and β coefficients per cluster
"""

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — replicate the structure from paths.py without importing the full
# pipeline, so this script can run standalone.
# ---------------------------------------------------------------------------
from utils.paths import (
    make_all_dirs, DIR_15,
    INT_WELLS_CLEAN, INT_CLIMATE, INT_CLUSTER_STATS,
    INT_LOCATIONS, INT_WELL_ELEVATIONS,
    OUT_15_LAMBDA_PROFILE, OUT_15_FIT_COMPARISON,
    OUT_15_BENCHMARK_TABLE, OUT_15_BEST_PARAMS,
)
from utils.config import CLUSTER_LABELS, CLUSTER_COLOURS, DRAINAGE_DATUM, HEADLINE_LAG
make_all_dirs()

INT_WELL_ELEV       = INT_WELL_ELEVATIONS   # local alias used throughout script
OUT_LAMBDA_PROFILE  = OUT_15_LAMBDA_PROFILE
OUT_FIT_COMPARISON  = OUT_15_FIT_COMPARISON
OUT_BENCHMARK_TABLE = OUT_15_BENCHMARK_TABLE
OUT_BEST_PARAMS     = OUT_15_BEST_PARAMS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LAMBDA_MIN   = 0.0
LAMBDA_MAX   = 6.0
LAMBDA_STEP  = 0.05
DATA_LIMIT   = 100   # months — same cap as script 03

# HEADLINE_LAG imported from config.py (= 0 after bucketing fix).

# CLUSTER_LABELS and CLUSTER_COLOURS imported from utils.config (k=5 partition).

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_well_name(name: str) -> str:
    """Lower-case, strip spaces — matches script 03 / data_utils convention."""
    return str(name).lower().replace(" ", "")


def nse(observed: np.ndarray, simulated: np.ndarray) -> float:
    """Nash-Sutcliffe Efficiency."""
    obs = np.asarray(observed, dtype=float)
    sim = np.asarray(simulated, dtype=float)
    mask = np.isfinite(obs) & np.isfinite(sim)
    obs, sim = obs[mask], sim[mask]
    if len(obs) < 5:
        return np.nan
    ss_res = np.sum((obs - sim) ** 2)
    ss_tot = np.sum((obs - np.mean(obs)) ** 2)
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan


def iterative_simulate(h0: float, P: np.ndarray, PET: np.ndarray,
                       upstand: float,
                       b1: float, b2: float, b3: float,
                       lam: float,
                       drainage_datum: float = DRAINAGE_DATUM) -> np.ndarray:
    """
    Simulate water table iteratively from initial condition h0.

    Uses the displacement formulation for β₃ and lag-1 rainfall, matching
    Script 03's headline SSM specification.

    For the standard SSM (lam=0), depth_prev is ignored because exp(0)=1.
    For the depth-dependent model, depth_prev is recalculated at each step
    from the *simulated* h, so the decay feedback is genuine.

    Parameters
    ----------
    h0       : initial water table (negative convention, m from ground surface)
    P        : precipitation array (m) — already lag-1 aligned by caller
    PET      : PET array (m) — contemporaneous
    upstand  : cluster mean upstand (m above ground)
    b1,b2,b3 : OLS coefficients (β₃ fitted against displacement)
    lam      : decay parameter λ (m⁻¹)
    drainage_datum : reference depth for displacement (default 3.7 m)
    """
    n = len(P)
    h = np.full(n, np.nan)
    h_t = h0

    for t in range(n):
        # PET extinction depth: physical distance below ground surface (≥ 0)
        # This is NOT the displacement term — it is a separate concept.
        d_t = max(-h_t + upstand, 0.0)
        decay = np.exp(-lam * d_t)

        # Displacement above drainage datum for β₃ term
        h_disp_t = drainage_datum + h_t

        delta = b1 * P[t] - b2 * decay * PET[t] - b3 * h_disp_t
        h_t = h_t + delta
        h[t] = h_t

    return h


def fit_at_lambda(df: pd.DataFrame, lam: float, upstand: float,
                  drainage_datum: float = DRAINAGE_DATUM) -> dict:
    """
    Given a cluster centroid DataFrame with columns [h, P_m, PET, h_prev,
    h_disp_prev], fit the depth-dependent SSM by OLS at a fixed lambda.

    Uses lag-1 rainfall and displacement for β₃, matching Script 03.

    Returns dict with b1, b2, b3, r2_onestep.
    """
    # PET extinction depth: physical distance below ground (always ≥ 0)
    d_prev = np.maximum(-df["h_prev"].values + upstand, 0.0)
    decay  = np.exp(-lam * d_prev)

    X = pd.DataFrame({
        "beta_1_recharge":         df["P_lag1"].values,
        "beta_2_atmospheric_draw": -decay * df["PET"].values,
        "beta_3_drainage":         -df["h_disp_prev"].values,
    }, index=df.index)

    model = sm.OLS(df["Delta_h"], X).fit()

    return {
        "b1":  model.params["beta_1_recharge"],
        "b2":  model.params["beta_2_atmospheric_draw"],
        "b3":  model.params["beta_3_drainage"],
        "r2":  model.rsquared,
    }


def evaluate_iterative_nse(df: pd.DataFrame, lam: float, upstand: float,
                            b1: float, b2: float, b3: float) -> float:
    """
    Run the full iterative simulation and return NSE vs observed centroid.
    """
    h_sim = iterative_simulate(
        h0      = df["h"].iloc[0],
        P       = df["P_lag1"].values,
        PET     = df["PET"].values,
        upstand = upstand,
        b1=b1, b2=b2, b3=b3, lam=lam,
    )
    return nse(df["h"].values, h_sim)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data():
    print("Loading data...")
    wells_clean   = pd.read_csv(INT_WELLS_CLEAN,   index_col=0, parse_dates=True)
    climate       = pd.read_csv(INT_CLIMATE,       index_col=0, parse_dates=True)
    cluster_stats = pd.read_csv(INT_CLUSTER_STATS)
    locations     = pd.read_csv(INT_LOCATIONS)

    # Normalise names
    cluster_stats["Match_ID"] = cluster_stats["Match_ID"].apply(normalize_well_name)
    locations["Match_ID"]     = locations["Match_ID"].apply(normalize_well_name)
    well_col_lookup = {normalize_well_name(c): c for c in wells_clean.columns}

    # Load upstand data if available
    upstand_map = {}
    if INT_WELL_ELEV.exists():
        elev_df = pd.read_csv(INT_WELL_ELEV)
        # Expect columns: Name_norm, Upstand_m (Script 01 output format)
        name_col = "Name_norm" if "Name_norm" in elev_df.columns else (
            "Well" if "Well" in elev_df.columns else elev_df.columns[0]
        )
        if "Upstand_m" in elev_df.columns:
            for _, row in elev_df.iterrows():
                k = normalize_well_name(str(row[name_col]))
                v = row["Upstand_m"]
                if pd.notna(v):
                    upstand_map[k] = float(v)
        print(f"  Loaded upstand data for {len(upstand_map)} wells")
    else:
        print("  WARNING: 01_well_elevations.csv not found — upstand set to 0.05m for all wells")

    return wells_clean, climate, cluster_stats, locations, well_col_lookup, upstand_map


def build_cluster_centroids(wells_clean, cluster_stats, well_col_lookup, upstand_map):
    """
    Build upstand-corrected centroid series per cluster.
    Returns dict: {cluster_id (int): (centroid_series, mean_upstand)}
    """
    print("Building cluster centroids...")
    cluster_ids = sorted(
        pd.to_numeric(cluster_stats["Cluster"], errors="coerce")
        .dropna().astype(int).unique()
    )

    centroids = {}
    for cid in cluster_ids:
        c_wells = cluster_stats[
            pd.to_numeric(cluster_stats["Cluster"], errors="coerce") == cid
        ]["Match_ID"].astype(str).values

        available_cols = []
        well_upstands  = []
        for w in c_wells:
            col = well_col_lookup.get(normalize_well_name(w))
            if col is not None:
                available_cols.append(col)
                us = upstand_map.get(normalize_well_name(w), 0.05)
                well_upstands.append(us)

        if not available_cols:
            print(f"  C{cid}: no wells found — skipping")
            continue

        # Upstand-correct each well then average
        corrected = pd.DataFrame(index=wells_clean.index)
        for col, us in zip(available_cols, well_upstands):
            # depth in clean file is negative below pipe; subtract upstand gives
            # depth relative to ground (still negative when below ground)
            corrected[col] = wells_clean[col] - us

        centroid = corrected.mean(axis=1)
        mean_upstand = float(np.mean(well_upstands))

        print(f"  C{cid}: {len(available_cols)} wells, mean upstand = {mean_upstand:.3f} m")
        centroids[cid] = (centroid, mean_upstand)

    return centroids


def build_regression_df(centroid: pd.Series, climate: pd.DataFrame,
                        data_limit: int = DATA_LIMIT,
                        drainage_datum: float = DRAINAGE_DATUM) -> pd.DataFrame:
    """Merge centroid with climate and build Δh, h_prev, h_disp_prev, P_lag1."""
    df = centroid.to_frame(name="h").join(climate[["P_m", "PET"]], how="inner")
    df["h_prev"]  = df["h"].shift(1)
    df["Delta_h"] = df["h"] - df["h_prev"]

    # Displacement above drainage datum for β₃ predictor
    df["h_disp_prev"] = drainage_datum + df["h_prev"]

    # Rainfall lag (HEADLINE_LAG from config)
    df["P_lag1"] = df["P_m"].shift(HEADLINE_LAG)

    df = df.dropna(subset=["Delta_h", "P_lag1", "PET", "h_prev", "h_disp_prev"])
    if len(df) > data_limit:
        df = df.iloc[-data_limit:]
    return df


# ---------------------------------------------------------------------------
# Standard SSM baseline (λ=0)
# ---------------------------------------------------------------------------

def fit_standard_ssm(df: pd.DataFrame) -> dict:
    X = pd.DataFrame({
        "beta_1_recharge":         df["P_lag1"].values,
        "beta_2_atmospheric_draw": -df["PET"].values,
        "beta_3_drainage":         -df["h_disp_prev"].values,
    }, index=df.index)
    model = sm.OLS(df["Delta_h"], X).fit()
    b1 = model.params["beta_1_recharge"]
    b2 = model.params["beta_2_atmospheric_draw"]
    b3 = model.params["beta_3_drainage"]

    # One-step R²
    r2 = model.rsquared

    # Iterative NSE — for the standard SSM (λ=0), upstand doesn't affect
    # the PET decay (exp(0)=1), but we still need displacement for β₃.
    h_sim = iterative_simulate(
        h0=df["h"].iloc[0], P=df["P_lag1"].values, PET=df["PET"].values,
        upstand=0.0,   # upstand=0 → no PET depth correction, standard model
        b1=b1, b2=b2, b3=b3, lam=0.0,
    )
    nse_val = nse(df["h"].values, h_sim)

    return {"b1": b1, "b2": b2, "b3": b3, "r2_onestep": r2, "nse_iterative": nse_val}


# ---------------------------------------------------------------------------
# Grid search
# ---------------------------------------------------------------------------

def grid_search_lambda(df: pd.DataFrame, upstand: float) -> pd.DataFrame:
    """
    Search λ over [LAMBDA_MIN, LAMBDA_MAX] and record OLS R² and
    iterative NSE at each step.
    """
    lambdas = np.arange(LAMBDA_MIN, LAMBDA_MAX + LAMBDA_STEP / 2, LAMBDA_STEP)
    records = []

    for lam in lambdas:
        fit = fit_at_lambda(df, lam, upstand)
        # Only evaluate iterative NSE if all coefficients are physically
        # plausible (positive β₁, positive β₂, positive β₃)
        if fit["b1"] > 0 and fit["b2"] > 0 and fit["b3"] > 0:
            nse_val = evaluate_iterative_nse(
                df, lam, upstand, fit["b1"], fit["b2"], fit["b3"]
            )
        else:
            nse_val = np.nan

        records.append({
            "lambda": round(lam, 4),
            "b1": fit["b1"],
            "b2": fit["b2"],
            "b3": fit["b3"],
            "r2_onestep":    fit["r2"],
            "nse_iterative": nse_val,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

CLUSTER_ORDER = sorted(CLUSTER_LABELS.keys())   # all clusters under k=5


def plot_lambda_profiles(profiles: dict, ssm_baselines: dict):
    """
    One panel per cluster: NSE vs λ, with horizontal dashed line at SSM NSE.
    """
    n = len(CLUSTER_ORDER)
    # 2x3 grid accommodates up to 6 clusters; unused panels hidden after the loop.
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), dpi=150)
    axes = axes.flatten()

    for ax, cid in zip(axes, CLUSTER_ORDER):
        if cid not in profiles:
            ax.set_visible(False)
            continue

        prof = profiles[cid]
        ssm  = ssm_baselines[cid]
        col  = CLUSTER_COLOURS.get(cid, "steelblue")
        label = CLUSTER_LABELS.get(cid, f"C{cid}")

        ax.plot(prof["lambda"], prof["nse_iterative"], color=col, lw=2,
                label="Depth-dependent model")
        ax.axhline(ssm["nse_iterative"], color="black", lw=1.5, ls="--",
                   label=f"Standard SSM (NSE = {ssm['nse_iterative']:.3f})")

        # Mark best λ
        best_idx = prof["nse_iterative"].idxmax()
        if pd.notna(prof.loc[best_idx, "nse_iterative"]):
            best_lam = prof.loc[best_idx, "lambda"]
            best_nse = prof.loc[best_idx, "nse_iterative"]
            ax.axvline(best_lam, color=col, lw=1, ls=":", alpha=0.7)
            ax.scatter([best_lam], [best_nse], color=col, zorder=5, s=60,
                       label=f"Best λ = {best_lam:.2f} m⁻¹")

        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_xlabel("λ (m⁻¹)", fontsize=10)
        ax.set_ylabel("Iterative NSE", fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(LAMBDA_MIN, LAMBDA_MAX)

    # Hide any unused panels (e.g. the 6th in a 2x3 grid with 5 clusters).
    for ax in axes[len(CLUSTER_ORDER):]:
        ax.set_visible(False)

    fig.suptitle("Depth-Dependent PET Model: NSE vs Decay Parameter λ\n"
                 "(dashed = Standard SSM baseline)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(OUT_LAMBDA_PROFILE, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUT_LAMBDA_PROFILE.name}")


def plot_fit_comparison(regression_dfs: dict, centroids: dict, climate: pd.DataFrame,
                        best_params: dict, ssm_baselines: dict):
    """
    For each cluster: observed vs iterative simulation (standard SSM and best
    depth-dependent model), shown as time series.
    """
    n = len(CLUSTER_ORDER)
    fig = plt.figure(figsize=(17, 10), dpi=150)
    # 2x3 grid; unused cells stay empty.
    gs  = gridspec.GridSpec(2, 3, hspace=0.45, wspace=0.3)

    for i, cid in enumerate(CLUSTER_ORDER):
        if cid not in regression_dfs or cid not in best_params:
            continue

        ax  = fig.add_subplot(gs[i // 3, i % 3])
        df  = regression_dfs[cid]
        bp  = best_params[cid]
        ssm = ssm_baselines[cid]
        col = CLUSTER_COLOURS.get(cid, "steelblue")
        label = CLUSTER_LABELS.get(cid, f"C{cid}")
        upstand = centroids[cid][1]

        # Standard SSM simulation (λ=0, upstand irrelevant for PET decay)
        h_ssm = iterative_simulate(
            h0=df["h"].iloc[0], P=df["P_lag1"].values, PET=df["PET"].values,
            upstand=0.0, b1=ssm["b1"], b2=ssm["b2"], b3=ssm["b3"], lam=0.0,
        )

        # Depth-dependent simulation
        h_ddp = iterative_simulate(
            h0=df["h"].iloc[0], P=df["P_lag1"].values, PET=df["PET"].values,
            upstand=upstand, b1=bp["b1"], b2=bp["b2"], b3=bp["b3"],
            lam=bp["best_lambda"],
        )

        ax.plot(df.index, df["h"].values, color="black", lw=1.5,
                label="Observed centroid")
        ax.plot(df.index, h_ssm, color="grey", lw=1, ls="--",
                label=f"SSM (NSE={ssm['nse_iterative']:.2f})")
        ax.plot(df.index, h_ddp, color=col, lw=1.5,
                label=f"Depth-dep. λ={bp['best_lambda']:.2f} (NSE={bp['nse_iterative']:.2f})")

        ax.set_title(label, fontsize=10, fontweight="bold")
        ax.set_ylabel("Depth to WT (m)", fontsize=9)
        ax.legend(fontsize=7.5)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    fig.suptitle("Iterative Simulation: Standard SSM vs Depth-Dependent PET Model",
                 fontsize=13, fontweight="bold")
    plt.savefig(OUT_FIT_COMPARISON, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {OUT_FIT_COMPARISON.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 65)
    print("  15: Depth-Dependent PET Model — Grid Search")
    print("=" * 65)

    # Load
    wells_clean, climate, cluster_stats, locations, well_col_lookup, upstand_map = load_data()
    centroids = build_cluster_centroids(wells_clean, cluster_stats, well_col_lookup, upstand_map)

    # Build regression DataFrames
    regression_dfs = {}
    for cid, (centroid, upstand) in centroids.items():
        df = build_regression_df(centroid, climate)
        if len(df) > 30:
            regression_dfs[cid] = df

    # Standard SSM baseline
    print("\nFitting standard SSM baselines (λ=0)...")
    ssm_baselines = {}
    for cid, df in regression_dfs.items():
        ssm = fit_standard_ssm(df)
        ssm_baselines[cid] = ssm
        print(f"  C{cid}  one-step R²={ssm['r2_onestep']:.3f}  "
              f"iterative NSE={ssm['nse_iterative']:.3f}")

    # Grid search
    print(f"\nGrid searching λ ∈ [{LAMBDA_MIN}, {LAMBDA_MAX}] "
          f"step {LAMBDA_STEP} ({int((LAMBDA_MAX - LAMBDA_MIN) / LAMBDA_STEP) + 1} values)...")
    profiles = {}
    for cid, df in regression_dfs.items():
        _, upstand = centroids[cid]
        print(f"  C{cid} ...", end=" ", flush=True)
        prof = grid_search_lambda(df, upstand)
        profiles[cid] = prof
        valid = prof.dropna(subset=["nse_iterative"])
        if not valid.empty:
            best = valid.loc[valid["nse_iterative"].idxmax()]
            print(f"best λ={best['lambda']:.2f}  NSE={best['nse_iterative']:.3f}")
        else:
            print("no valid λ found")

    # Extract best params per cluster
    print("\nExtracting best parameters...")
    best_params = {}
    for cid, prof in profiles.items():
        valid = prof.dropna(subset=["nse_iterative"])
        if valid.empty:
            continue
        best_row = valid.loc[valid["nse_iterative"].idxmax()]
        _, upstand = centroids[cid]
        best_params[cid] = {
            "best_lambda":    best_row["lambda"],
            "b1":             best_row["b1"],
            "b2":             best_row["b2"],
            "b3":             best_row["b3"],
            "r2_onestep":     best_row["r2_onestep"],
            "nse_iterative":  best_row["nse_iterative"],
            "upstand":        upstand,
        }

    # -----------------------------------------------------------------------
    # Console summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("  BENCHMARK SUMMARY — Depth-Dependent vs Standard SSM")
    print("=" * 65)
    print(f"{'Cluster':<8} {'SSM NSE':>9} {'DDP NSE':>9} {'Δ NSE':>8}  "
          f"{'Best λ':>8}  {'Note'}")
    print("-" * 65)

    benchmark_rows = []
    for cid in sorted(CLUSTER_LABELS.keys()):
        ssm = ssm_baselines.get(cid)
        bp  = best_params.get(cid)
        if ssm is None:
            continue
        ssm_nse = ssm["nse_iterative"]
        ddp_nse = bp["nse_iterative"] if bp else np.nan
        delta   = ddp_nse - ssm_nse if (bp and pd.notna(ddp_nse)) else np.nan
        best_lam = bp["best_lambda"] if bp else np.nan

        # Flag if improvement is marginal (< 0.01) or model performs worse
        if pd.isna(delta):
            note = "no valid fit"
        elif delta > 0.02:
            note = "↑ improvement"
        elif delta > 0.005:
            note = "~ marginal gain"
        elif delta > -0.005:
            note = "~ equivalent"
        else:
            note = "↓ worse"

        print(f"  C{cid:<5}  {ssm_nse:>9.3f}  {ddp_nse:>9.3f}  {delta:>+8.3f}  "
              f"{best_lam:>8.2f}  {note}")

        benchmark_rows.append({
            "Cluster":           f"C{cid}",
            "Label":             CLUSTER_LABELS.get(cid, ""),
            "SSM_Iterative_NSE": round(ssm_nse, 3),
            "DDP_Iterative_NSE": round(ddp_nse, 3) if pd.notna(ddp_nse) else np.nan,
            "Delta_NSE":         round(delta, 3)   if pd.notna(delta) else np.nan,
            "Best_Lambda_m-1":   round(best_lam, 2) if pd.notna(best_lam) else np.nan,
            "DDP_b1":            round(bp["b1"], 4) if bp else np.nan,
            "DDP_b2":            round(bp["b2"], 4) if bp else np.nan,
            "DDP_b3":            round(bp["b3"], 4) if bp else np.nan,
            "SSM_OneStep_R2":    round(ssm["r2_onestep"], 3),
            "DDP_OneStep_R2":    round(bp["r2_onestep"], 3) if bp else np.nan,
        })

    print("=" * 65)

    # -----------------------------------------------------------------------
    # Save outputs
    # -----------------------------------------------------------------------
    print("\nSaving outputs...")

    pd.DataFrame(benchmark_rows).to_csv(OUT_BENCHMARK_TABLE, index=False)
    print(f"  Saved: {OUT_BENCHMARK_TABLE.name}")

    params_rows = []
    for cid, bp in best_params.items():
        ssm = ssm_baselines.get(cid, {})
        params_rows.append({
            "Cluster":        f"C{cid}",
            "Label":          CLUSTER_LABELS.get(cid, ""),
            "Best_Lambda":    bp["best_lambda"],
            "b1":             bp["b1"],
            "b2":             bp["b2"],
            "b3":             bp["b3"],
            "Mean_Upstand_m": bp["upstand"],
            "R2_OneStep":     bp["r2_onestep"],
            "NSE_Iterative":  bp["nse_iterative"],
            "SSM_b1":         ssm.get("b1", np.nan),
            "SSM_b2":         ssm.get("b2", np.nan),
            "SSM_b3":         ssm.get("b3", np.nan),
            "SSM_NSE":        ssm.get("nse_iterative", np.nan),
        })
    pd.DataFrame(params_rows).to_csv(OUT_BEST_PARAMS, index=False)
    print(f"  Saved: {OUT_BEST_PARAMS.name}")

    # Lambda profile for all clusters (including C5, C6 if fitted)
    profile_all = pd.concat(
        {f"C{cid}": prof for cid, prof in profiles.items()},
        names=["Cluster"]
    ).reset_index(level="Cluster")
    profile_all.to_csv(DIR_15 / "15_00_lambda_profiles_raw.csv", index=False)

    # Figures
    print("\nGenerating figures...")
    plot_lambda_profiles(profiles, ssm_baselines)
    plot_fit_comparison(regression_dfs, centroids, climate, best_params, ssm_baselines)

    print("\n15 Complete.")


if __name__ == "__main__":
    main()
