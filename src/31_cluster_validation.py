#!/usr/bin/env python3
"""
31_cluster_validation.py  --  Independent validation of the k=5 partition.

STANDALONE DIAGNOSTIC. Not wired into run_analysis.py. Run directly:

    python3 src/31_cluster_validation.py

The canonical clusters are formed in Script 02 by Ward's linkage on
(1 - Pearson correlation) distance between well HYDROGRAPHS. This script asks
whether that partition is corroborated by evidence the clustering never used,
organised by how independent each line of evidence actually is:

  Tier 1  EXTERNAL  -- data orthogonal to the hydrographs (geography, the
                      forest-canopy polygon, distance-to-coast, elevation).
  Tier 2  METRIC-INDEPENDENT -- magnitude descriptors of the hydrographs
                      (mean depth, amplitude, summer minima, dry depth). The
                      clustering used the CORRELATION structure (shape/timing),
                      so magnitude is largely orthogonal to the input.
  Tier 3  CONVERGENT -- same water-level series, different estimation method
                      (SSM betas, WTF Sy, LCSC). Supporting, NOT independent.
  Tier 4  ROBUSTNESS -- does k=5 survive a different linkage / distance metric
                      (average, complete; Spearman, DTW)? Adjusted Rand Index
                      against the canonical Ward+Pearson partition.

All canonical numbers are read from live pipeline CSVs; nothing is hardcoded.

Outputs (outputs/31_cluster_validation/):
  31_validation_summary.csv      one row per test (tier, statistic, p, independence)
  31_method_robustness_ari.csv   ARI of each alternative clustering vs canonical
  31_forest_confusion.csv        cluster x forest-polygon crosstab + Cohen's kappa
  31_forest_borderline.csv       wells inside the +/- edge band, with signed distance
  31_cluster_validation_panel.png  4-panel figure

Version: 1.0.0  (2026-06-25)
"""
from __future__ import annotations
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform, pdist
from sklearn.metrics import adjusted_rand_score, cohen_kappa_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.config import CLUSTER_COLOURS, CLUSTER_LABELS
from utils.data_utils import normalize_well_name
from utils.paths import OUT_DIR, DATA_GEO_DIR

import xml.etree.ElementTree as ET
from shapely.geometry import Point, Polygon
from pyproj import Transformer

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# Tunable parameters
# ---------------------------------------------------------------------------
KNN_K           = 6      # neighbours for spatial weights (Moran, join-count)
N_PERM          = 10000  # permutations for spatial tests
EDGE_BUFFER_M   = 50.0   # +/- band around the forest boundary => "borderline"
SUMMER_MONTHS   = (6, 7, 8, 9)
MIN_YEAR_OBS    = 6      # min monthly obs in a year to use it for amplitude
DTW_WINDOW      = 12     # Sakoe-Chiba band (months) for DTW
K_CANONICAL     = 5
RNG             = np.random.default_rng(20260625)

OUTDIR = OUT_DIR / "31_cluster_validation"
OUTDIR.mkdir(parents=True, exist_ok=True)

BETA_COLS = ["beta_1_recharge", "beta_2_atmospheric_draw", "beta_3_drainage"]
FOREST_CLUSTERS = {4, 5}


# ===========================================================================
# Data loading
# ===========================================================================
def load_data():
    master = pd.read_csv(OUT_DIR / "03_master_data.csv")
    master["key"] = master["Name_Original"].map(normalize_well_name)

    elev = pd.read_csv(OUT_DIR / "01_well_elevations.csv")
    elev["key"] = elev["Name"].map(normalize_well_name)
    master = master.merge(
        elev[["key", "DEM_Ground_Elev", "dist_coast_m"]], on="key", how="left"
    )

    wtf = pd.read_csv(OUT_DIR / "17_wtf_well_sy.csv")
    wtf["key"] = wtf["Well"].map(normalize_well_name)
    master = master.merge(wtf[["key", "Sy_median"]], on="key", how="left")

    # per-well monthly hydrographs (restrict to reference wells in master)
    wells = pd.read_csv(OUT_DIR / "01_wells_clean.csv", index_col=0)
    wells.index = pd.to_datetime(wells.index)
    wells.columns = [normalize_well_name(c) for c in wells.columns]
    ref_keys = [k for k in master["key"] if k in wells.columns]
    wells = wells[ref_keys]

    dry = pd.read_csv(OUT_DIR / "01_dry_depths.csv")
    dry["key"] = dry["well"].map(normalize_well_name)
    dry_med = dry.groupby("key")["dry_depth_m"].median().rename("dry_depth_med")
    master = master.merge(dry_med, on="key", how="left")

    return master, wells


def load_polygon(name: str) -> Polygon:
    """Return the named KML polygon transformed to OSGB (EPSG:27700)."""
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    root = ET.fromstring((DATA_GEO_DIR / "Features.kml").read_text())
    tr = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    for pm in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        nm = pm.find("k:name", ns)
        if nm is not None and nm.text == name:
            txt = pm.find(".//k:coordinates", ns).text.strip().split()
            lonlat = [tuple(map(float, c.split(",")[:2])) for c in txt]
            en = [tr.transform(lon, lat) for lon, lat in lonlat]
            return Polygon(en)
    raise ValueError(f"Polygon {name!r} not found in Features.kml")


# ===========================================================================
# Generic statistics
# ===========================================================================
def eta_squared(values, labels):
    """One-way ANOVA F, p and eta^2 (between-group / total SS)."""
    df = pd.DataFrame({"v": values, "g": labels}).dropna()
    groups = [g["v"].values for _, g in df.groupby("g")]
    F, p = stats.f_oneway(*groups)
    grand = df["v"].mean()
    ss_tot = ((df["v"] - grand) ** 2).sum()
    ss_bet = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
    return F, p, (ss_bet / ss_tot if ss_tot else np.nan), len(df)


def kruskal(values, labels):
    df = pd.DataFrame({"v": values, "g": labels}).dropna()
    groups = [g["v"].values for _, g in df.groupby("g")]
    H, p = stats.kruskal(*groups)
    return H, p


# ===========================================================================
# Tier 1 -- spatial weights, permutation compactness, join-count, Moran's I
# ===========================================================================
def knn_adjacency(coords, k):
    """Symmetric binary kNN adjacency and row-standardised weights."""
    n = len(coords)
    d = squareform(pdist(coords))
    np.fill_diagonal(d, np.inf)
    A = np.zeros((n, n))
    for i in range(n):
        for j in np.argsort(d[i])[:k]:
            A[i, j] = 1
    A = np.maximum(A, A.T)                      # symmetrise
    W = A / A.sum(axis=1, keepdims=True)        # row-standardised
    return A, W


def perm_compactness(coords, labels, n_perm):
    """Mean within-cluster pairwise distance vs label-shuffle null (one-sided)."""
    d = squareform(pdist(coords))
    labels = np.asarray(labels)

    def within_mean(lab):
        same = lab[:, None] == lab[None, :]
        np.fill_diagonal(same, False)
        return d[same].mean()

    obs = within_mean(labels)
    null = np.empty(n_perm)
    for b in range(n_perm):
        null[b] = within_mean(RNG.permutation(labels))
    p = (np.sum(null <= obs) + 1) / (n_perm + 1)   # compact => small distance
    return obs, null.mean(), p


def join_count_bb(A, labels, n_perm):
    """Same-cluster join count (BB) vs label-shuffle null (one-sided, more joins)."""
    labels = np.asarray(labels)

    def bb(lab):
        same = (lab[:, None] == lab[None, :]).astype(float)
        return 0.5 * np.sum(A * same)

    obs = bb(labels)
    null = np.array([bb(RNG.permutation(labels)) for _ in range(n_perm)])
    z = (obs - null.mean()) / null.std()
    p = (np.sum(null >= obs) + 1) / (n_perm + 1)
    return obs, null.mean(), z, p


def morans_i(W, y, n_perm):
    """Global Moran's I for indicator y with row-standardised W (one-sided)."""
    y = np.asarray(y, float)
    z = y - y.mean()
    denom = np.sum(z ** 2)

    def I(zz):
        return (zz[:, None] * zz[None, :] * W).sum() / denom

    obs = I(z)
    null = np.array([I(RNG.permutation(z)) for _ in range(n_perm)])
    p = (np.sum(null >= obs) + 1) / (n_perm + 1)
    return obs, p


# ===========================================================================
# Tier 1 -- forest-footprint recovery
# ===========================================================================
def forest_recovery(master):
    forest = load_polygon("Forest")
    felling = load_polygon("Felling experiment")
    boundary = forest.exterior

    rows = []
    for _, r in master.iterrows():
        pt = Point(r["Easting"], r["Northing"])
        inside = forest.contains(pt)
        dist = pt.distance(boundary)
        signed = dist if inside else -dist          # +inside / -outside
        if abs(signed) < EDGE_BUFFER_M:
            cls = "edge"
        elif inside:
            cls = "inside"
        else:
            cls = "outside"
        rows.append({
            "well": r["Name_Original"], "Cluster": int(r["Cluster"]),
            "in_forest_poly": bool(inside),
            "signed_dist_m": round(signed, 1), "poly_class": cls,
            "in_felling_poly": bool(felling.contains(pt)),
            "in_forest_cluster": int(r["Cluster"]) in FOREST_CLUSTERS,
        })
    fr = pd.DataFrame(rows)

    # confusion: forest polygon membership vs forest-cluster membership
    conf = pd.crosstab(fr["in_forest_poly"], fr["in_forest_cluster"])
    kappa_all = cohen_kappa_score(fr["in_forest_poly"], fr["in_forest_cluster"])
    core = fr[fr["poly_class"] != "edge"]
    kappa_core = cohen_kappa_score(core["in_forest_poly"], core["in_forest_cluster"])
    borderline = fr[fr["poly_class"] == "edge"].sort_values("signed_dist_m")
    return fr, conf, kappa_all, kappa_core, borderline


# ===========================================================================
# Tier 2 -- magnitude descriptors from hydrographs
# ===========================================================================
def magnitude_descriptors(wells):
    yr = wells.index.year
    mo = wells.index.month
    out = {}
    for w in wells.columns:
        s = wells[w]
        out.setdefault("mean_depth", {})[w] = s.mean()
        # median annual amplitude (max-min within years with enough obs)
        amps = []
        for y in np.unique(yr):
            sy = s[yr == y].dropna()
            if len(sy) >= MIN_YEAR_OBS:
                amps.append(sy.max() - sy.min())
        out.setdefault("amplitude", {})[w] = np.median(amps) if amps else np.nan
        # median annual summer minimum depth
        mins = []
        for y in np.unique(yr):
            sy = s[(yr == y) & (np.isin(mo, SUMMER_MONTHS))].dropna()
            if len(sy):
                mins.append(sy.min())
        out.setdefault("summer_min", {})[w] = np.median(mins) if mins else np.nan
    return pd.DataFrame(out)


# ===========================================================================
# Tier 4 -- method robustness
# ===========================================================================
def banded_dtw(a, b, window):
    """Sakoe-Chiba banded DTW distance between two 1-D arrays (path-normalised)."""
    n, m = len(a), len(b)
    w = max(window, abs(n - m))
    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        jlo, jhi = max(1, i - w), min(m, i + w)
        for j in range(jlo, jhi + 1):
            cost = (a[i - 1] - b[j - 1]) ** 2
            D[i, j] = cost + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return np.sqrt(D[n, m] / (n + m))


def _corr_distance(matrix, method):
    """1 - corr distance, pairwise-complete, exactly as Script 02's
    _correlation_distance (pandas .corr, fillna(0), clip, symmetrise)."""
    corr = matrix.corr(method=method).fillna(0).values
    sq = np.clip(1.0 - corr, 0.0, None)
    np.fill_diagonal(sq, 0.0)
    sq = (sq + sq.T) / 2.0
    return sq, list(matrix.columns)


def _dtw_distance(wells):
    """DTW needs complete series, so interpolate over a well-covered window
    and z-score. This gap-filling is a documented requirement of DTW and a
    genuine difference from the correlation distances."""
    cover = wells.notna().mean(axis=1)
    span = wells.index[cover >= 0.90]
    sub = wells.loc[span[0]:span[-1]].interpolate(limit_direction="both")
    sub = sub.dropna(axis=1, how="any")
    Z = ((sub - sub.mean()) / sub.std()).values.T   # wells x time
    cols = list(sub.columns)
    n = len(cols)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            D[i, j] = D[j, i] = banded_dtw(Z[i], Z[j], DTW_WINDOW)
    return D, cols


def robustness(wells, master):
    key2cl = master.set_index("key")["Cluster"]

    def cut_and_score(sq, cols, method):
        cond = squareform(sq, checks=False)
        Zl = linkage(cond, method=method)
        lab = fcluster(Zl, t=K_CANONICAL, criterion="maxclust")
        canon = key2cl.loc[cols].values
        return round(adjusted_rand_score(canon, lab), 3), len(cols)

    rows = []
    # correlation distances on the raw reference matrix (Script 02 method)
    pear_sq, pear_cols = _corr_distance(wells, "pearson")
    spear_sq, spear_cols = _corr_distance(wells, "spearman")
    dtw_sq, dtw_cols = _dtw_distance(wells)

    plan = [
        ("Pearson",  "ward",     "reproduction", pear_sq,  pear_cols),
        ("Pearson",  "average",  "alt linkage",  pear_sq,  pear_cols),
        ("Pearson",  "complete", "alt linkage",  pear_sq,  pear_cols),
        ("Spearman", "ward",     "alt distance", spear_sq, spear_cols),
        ("DTW",      "ward",     "alt distance", dtw_sq,   dtw_cols),
    ]
    for dist, meth, note, sq, cols in plan:
        ari, n = cut_and_score(sq, cols, meth)
        rows.append({"distance": dist, "linkage": meth, "note": note,
                     "k": K_CANONICAL, "n_wells": n, "ARI_vs_canonical": ari})
    return pd.DataFrame(rows), len(pear_cols)


# ===========================================================================
# Figure
# ===========================================================================
def make_panel(master, mag, ari_df, summary_df, fr):
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # (a) spatial cluster map
    ax = axes[0, 0]
    for cid in sorted(master["Cluster"].unique()):
        sub = master[master["Cluster"] == cid]
        ax.scatter(sub["Easting"], sub["Northing"], s=42,
                   c=CLUSTER_COLOURS[cid], edgecolors="k", linewidths=0.4,
                   label=CLUSTER_LABELS[cid])
    try:
        fx, fy = load_polygon("Forest").exterior.xy
        ax.plot(fx, fy, color="darkgreen", lw=1.4, ls="--", label="Forest polygon")
    except Exception:
        pass
    ax.set_title("(a) Spatial coherence of hydrograph clusters")
    ax.set_xlabel("Easting (m)"); ax.set_ylabel("Northing (m)")
    ax.set_aspect("equal"); ax.legend(fontsize=7, loc="best")

    # (b) external & convergent eta^2
    ax = axes[0, 1]
    es = summary_df[summary_df["statistic_name"] == "eta2"].copy()
    es = es.sort_values("statistic")
    colours = {"external": "#2c7fb8", "metric-independent": "#7fcdbb",
               "convergent": "#cccccc"}
    ax.barh(es["descriptor"], es["statistic"],
            color=[colours.get(t, "#999") for t in es["independence"]])
    ax.set_xlabel("eta^2  (variance in descriptor explained by partition)")
    ax.set_title("(b) Descriptor separation by independence tier")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colours.values()]
    ax.legend(handles, colours.keys(), fontsize=7, loc="lower right")
    ax.axvline(0, color="k", lw=0.5)

    # (c) magnitude descriptor boxplots (amplitude)
    ax = axes[1, 0]
    m2 = master.merge(mag, left_on="key", right_index=True, how="left")
    cids = sorted(m2["Cluster"].unique())
    data = [m2.loc[m2["Cluster"] == cid, "amplitude"].dropna() for cid in cids]
    bp = ax.boxplot(data, patch_artist=True)
    ax.set_xticks(range(1, len(cids) + 1))
    ax.set_xticklabels([CLUSTER_LABELS[c].split()[0] for c in cids])
    for patch, cid in zip(bp["boxes"], cids):
        patch.set_facecolor(CLUSTER_COLOURS[cid]); patch.set_alpha(0.75)
    ax.set_title("(c) Seasonal amplitude by cluster (metric-independent)")
    ax.set_ylabel("median annual amplitude (m)")

    # (d) robustness ARI
    ax = axes[1, 1]
    lab = ari_df["distance"] + "+" + ari_df["linkage"]
    bars = ax.barh(lab, ari_df["ARI_vs_canonical"], color="#756bb1")
    ax.axvline(1.0, color="green", ls=":", lw=1)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Adjusted Rand Index vs canonical (Ward+Pearson)")
    ax.set_title("(d) Partition robustness to linkage / distance")
    for b, v in zip(bars, ari_df["ARI_vs_canonical"]):
        ax.text(v + 0.01, b.get_y() + b.get_height() / 2, f"{v:.2f}",
                va="center", fontsize=8)

    fig.suptitle("Cluster validation panel -- k=5 partition vs independent evidence",
                 fontsize=14, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    path = OUTDIR / "31_cluster_validation_panel.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


# ===========================================================================
# Main
# ===========================================================================
def main():
    master, wells = load_data()
    labels = master["Cluster"].values
    coords = master[["Easting", "Northing"]].values
    rows = []  # summary rows

    # ---- Tier 1: spatial -------------------------------------------------
    A, W = knn_adjacency(coords, KNN_K)
    obs_c, null_c, p_c = perm_compactness(coords, labels, N_PERM)
    rows.append(dict(tier="1 external", test="within-cluster compactness",
                     descriptor="geographic distance", statistic_name="mean_within_m",
                     statistic=round(obs_c, 1), p_value=round(p_c, 4),
                     independence="external"))
    bb, bb0, bb_z, bb_p = join_count_bb(A, labels, N_PERM)
    rows.append(dict(tier="1 external", test="join-count (BB)",
                     descriptor="same-cluster adjacency", statistic_name="z",
                     statistic=round(bb_z, 2), p_value=round(bb_p, 4),
                     independence="external"))
    for cid in sorted(master["Cluster"].unique()):
        ind = (master["Cluster"] == cid).astype(int).values
        I, pI = morans_i(W, ind, N_PERM)
        rows.append(dict(tier="1 external", test=f"Moran's I (C{cid} indicator)",
                         descriptor=f"C{cid} spatial autocorr",
                         statistic_name="morans_I", statistic=round(I, 3),
                         p_value=round(pI, 4), independence="external"))
    for var, lbl in [("dist_coast_m", "distance to coast"),
                     ("DEM_Ground_Elev", "ground elevation")]:
        F, p, e2, n = eta_squared(master[var], labels)
        H, pk = kruskal(master[var], labels)
        rows.append(dict(tier="1 external", test="ANOVA / Kruskal", descriptor=lbl,
                         statistic_name="eta2", statistic=round(e2, 3),
                         p_value=round(p, 4), independence="external"))

    # ---- forest recovery -------------------------------------------------
    fr, conf, kappa_all, kappa_core, borderline = forest_recovery(master)
    rows.append(dict(tier="1 external", test="forest-footprint recovery",
                     descriptor="canopy polygon vs forest clusters",
                     statistic_name="cohen_kappa", statistic=round(kappa_all, 3),
                     p_value=np.nan, independence="external"))
    rows.append(dict(tier="1 external", test="forest recovery (edge excluded)",
                     descriptor="canopy polygon vs forest clusters",
                     statistic_name="cohen_kappa", statistic=round(kappa_core, 3),
                     p_value=np.nan, independence="external"))

    # ---- Tier 2: magnitude descriptors ----------------------------------
    mag = magnitude_descriptors(wells)
    m2 = master.merge(mag, left_on="key", right_index=True, how="left")
    for var, lbl in [("mean_depth", "mean depth to water"),
                     ("amplitude", "seasonal amplitude"),
                     ("summer_min", "summer minimum"),
                     ("dry_depth_med", "dry depth")]:
        col = m2[var] if var in m2 else master[var]
        F, p, e2, n = eta_squared(col, labels)
        rows.append(dict(tier="2 metric-indep", test="ANOVA", descriptor=lbl,
                         statistic_name="eta2", statistic=round(e2, 3),
                         p_value=round(p, 4), independence="metric-independent"))

    # ---- Tier 3: convergent (same series) -------------------------------
    for var, lbl in [("beta_1_recharge", "SSM beta1"),
                     ("beta_2_atmospheric_draw", "SSM beta2"),
                     ("beta_3_drainage", "SSM beta3"),
                     ("Sy_median", "WTF Sy"),
                     ("LCSC_Regression_Percent", "LCSC")]:
        F, p, e2, n = eta_squared(master[var], labels)
        rows.append(dict(tier="3 convergent", test="ANOVA", descriptor=lbl,
                         statistic_name="eta2", statistic=round(e2, 3),
                         p_value=round(p, 4), independence="convergent"))

    summary_df = pd.DataFrame(rows)

    # ---- Tier 4: robustness ---------------------------------------------
    ari_df, n_rob = robustness(wells, master)

    # ---- write outputs ---------------------------------------------------
    summary_df.to_csv(OUTDIR / "31_validation_summary.csv", index=False)
    ari_df.to_csv(OUTDIR / "31_method_robustness_ari.csv", index=False)
    conf.to_csv(OUTDIR / "31_forest_confusion.csv")
    borderline.to_csv(OUTDIR / "31_forest_borderline.csv", index=False)
    panel = make_panel(master, mag, ari_df, summary_df, fr)

    # ---- console ---------------------------------------------------------
    pd.set_option("display.width", 120)
    print("\n=== TIER 1-3 VALIDATION SUMMARY ===")
    print(summary_df.to_string(index=False))
    print("\n=== TIER 4 METHOD ROBUSTNESS (ARI vs canonical) ===")
    print(ari_df.to_string(index=False))
    print(f"\nForest recovery: kappa(all)={kappa_all:.3f}  "
          f"kappa(edge excluded)={kappa_core:.3f}")
    print("Confusion (rows=in_forest_poly, cols=in_forest_cluster):")
    print(conf.to_string())
    print(f"\nBorderline wells (|dist to forest edge| < {EDGE_BUFFER_M:.0f} m):")
    print(borderline[["well", "Cluster", "signed_dist_m",
                      "in_forest_cluster"]].to_string(index=False))
    mism = fr[(fr["in_forest_poly"]) & (~fr["in_forest_cluster"])]
    if len(mism):
        print("\nInside forest polygon but NOT in a forest cluster (kappa misses):")
        print(mism[["well", "Cluster", "signed_dist_m"]].to_string(index=False))
    print(f"\nWritten to {OUTDIR}")


if __name__ == "__main__":
    main()
