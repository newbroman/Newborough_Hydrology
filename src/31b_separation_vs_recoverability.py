#!/usr/bin/env python3
"""
31b_separation_vs_recoverability.py  --  one figure, two questions.

STANDALONE companion to 31_cluster_validation.py. For each independent
variable X it places side by side:

  SEPARATION    eta^2  -- "do the pre-formed clusters DIFFER on X?"
                          (variance in X explained by the partition)
  RECOVERABILITY ARI   -- "does X ALONE rebuild the clusters?"
                          (Ward k=5 on standardised X, ARI vs canonical)

The point of the figure: separation is consistently high while recoverability
is consistently low. The clusters differ on these variables (so they are real),
but the variables do not reconstruct the clusters (because the hydrograph
timing carries information no static attribute holds). High eta^2 does not imply
high ARI.

"Distance to coast" here is the Caernarfon Bay MHW shoreline (Menai Strait
excluded), per well_metadata.csv (consolidated from well_distance_to_coast.csv).

Output (outputs/31_cluster_validation/):
  31b_separation_vs_recoverability.csv
  31b_separation_vs_recoverability.png

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
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.data_utils import normalize_well_name
from utils.paths import OUT_DIR, DATA_GEO_DIR

import xml.etree.ElementTree as ET
from shapely.geometry import Point, Polygon
from pyproj import Transformer

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)

OUTDIR = OUT_DIR / "31_cluster_validation"
OUTDIR.mkdir(parents=True, exist_ok=True)
K = 5
SUMMER = (6, 7, 8, 9)
MIN_YR = 6
C_SEP = "#2c7fb8"   # separation (eta^2)
C_REC = "#756bb1"   # recoverability (ARI)


def load():
    m = pd.read_csv(OUT_DIR / "03_master_data.csv")
    m["key"] = m["Name_Original"].map(normalize_well_name)
    elev = pd.read_csv(OUT_DIR / "01_well_elevations.csv")
    elev["key"] = elev["Name"].map(normalize_well_name)
    m = m.merge(elev[["key", "DEM_Ground_Elev", "dist_coast_m"]], on="key", how="left")

    w = pd.read_csv(OUT_DIR / "01_wells_clean.csv", index_col=0)
    w.index = pd.to_datetime(w.index)
    w.columns = [normalize_well_name(c) for c in w.columns]
    yr, mo = w.index.year, w.index.month
    md, amp, smin = {}, {}, {}
    for k in m["key"]:
        if k not in w.columns:
            continue
        s = w[k]
        md[k] = s.mean()
        a = [s[yr == y].dropna().max() - s[yr == y].dropna().min()
             for y in np.unique(yr) if s[yr == y].notna().sum() >= MIN_YR]
        amp[k] = np.median(a) if a else np.nan
        sm = [s[(yr == y) & (np.isin(mo, SUMMER))].dropna().min()
              for y in np.unique(yr) if s[(yr == y) & (np.isin(mo, SUMMER))].notna().any()]
        smin[k] = np.median(sm) if sm else np.nan
    m["mean_depth"] = m["key"].map(md)
    m["amplitude"] = m["key"].map(amp)
    m["summer_min"] = m["key"].map(smin)

    dry = pd.read_csv(OUT_DIR / "01_dry_depths.csv")
    dry["key"] = dry["well"].map(normalize_well_name)
    m["dry_depth"] = m["key"].map(dry.groupby("key")["dry_depth_m"].median())

    # Caernarfon Bay forest polygon -> per-well forest flag
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    root = ET.fromstring((DATA_GEO_DIR / "Features.kml").read_text())
    tr = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    poly = None
    for pm in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        nm = pm.find("k:name", ns)
        if nm is not None and nm.text == "Forest":
            c = pm.find(".//k:coordinates", ns).text.strip().split()
            poly = Polygon([tr.transform(*map(float, p.split(",")[:2])) for p in c])
    m["forest"] = [int(poly.contains(Point(e, n)))
                   for e, n in zip(m["Easting"], m["Northing"])]
    return m


def eta2(values, labels):
    df = pd.DataFrame({"v": values, "g": labels}).dropna()
    groups = [g["v"].values for _, g in df.groupby("g")]
    grand = df["v"].mean()
    ss_tot = ((df["v"] - grand) ** 2).sum()
    ss_bet = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
    return ss_bet / ss_tot if ss_tot else np.nan


def ari_on(m, col, canon):
    sub = m.dropna(subset=[col])
    X = StandardScaler().fit_transform(sub[[col]])
    lab = AgglomerativeClustering(K, linkage="ward").fit_predict(X)
    return adjusted_rand_score(sub["Cluster"].values, lab)


def main():
    m = load()
    canon = m["Cluster"].values

    # (label, column, is_binary)
    descriptors = [
        ("Easting",              "Easting",         False),
        ("Distance to coast\n(Caernarfon Bay)", "dist_coast_m", False),
        ("Mean depth to water",  "mean_depth",      False),
        ("Summer minimum",       "summer_min",      False),
        ("Dry depth",            "dry_depth",       False),
        ("Seasonal amplitude",   "amplitude",       False),
        ("Ground elevation",     "DEM_Ground_Elev", False),
        ("Forest (canopy flag)", "forest",          True),
    ]

    rows = []
    for lbl, col, is_bin in descriptors:
        sep = eta2(m[col], canon)
        rec = ari_on(m, col, canon)
        rows.append({"descriptor": lbl.replace("\n", " "), "column": col,
                     "binary": is_bin, "eta2_separation": round(sep, 3),
                     "ari_recoverability": round(rec, 3)})
    res = pd.DataFrame(rows).sort_values("eta2_separation", ascending=True)
    res.to_csv(OUTDIR / "31b_separation_vs_recoverability.csv", index=False)

    # ---- figure ----------------------------------------------------------
    labels = [d[0] for d in descriptors]
    order = res["column"].tolist()
    lbl_by_col = {d[1]: d[0] for d in descriptors}
    ylabels = [lbl_by_col[c] for c in order]
    sep = res["eta2_separation"].values
    rec = res["ari_recoverability"].values
    y = np.arange(len(order))
    h = 0.38

    fig, ax = plt.subplots(figsize=(11, 7))
    b1 = ax.barh(y + h / 2, sep, height=h, color=C_SEP,
                 label="Separation  (eta^2): do the clusters DIFFER on X?")
    b2 = ax.barh(y - h / 2, rec, height=h, color=C_REC,
                 label="Recoverability (ARI): does X ALONE rebuild the clusters?")
    for bars, vals in [(b1, sep), (b2, rec)]:
        for b, v in zip(bars, vals):
            ax.text(v + 0.012, b.get_y() + b.get_height() / 2, f"{v:.2f}",
                    va="center", fontsize=8.5)
    # gap shading between the two bars per row
    for yi, s, r in zip(y, sep, rec):
        ax.plot([r, s], [yi, yi], color="0.7", lw=0.8, zorder=0)

    ax.set_yticks(y)
    ax.set_yticklabels(ylabels, fontsize=9.5)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("score (0–1)")
    ax.axvline(0, color="k", lw=0.6)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax.set_title("Two different questions about each independent variable",
                 fontsize=14, pad=10)

    cap = ("Clusters differ strongly on variables they never saw (high eta^2), yet "
           "those variables do not reconstruct the clusters (low ARI).\nThe gap is the "
           "hydrograph-timing information no static attribute holds — high separation "
           "does not imply recoverability.\n"
           "Forest is a binary canopy flag, so its recoverability is a 2-way split with an "
           "inherently low ARI ceiling.  Distance to coast = Caernarfon Bay MHW (Menai "
           "Strait excluded).")
    fig.text(0.06, 0.005, cap, fontsize=8, color="0.30", va="bottom")
    fig.tight_layout(rect=[0, 0.13, 1, 0.96])
    path = OUTDIR / "31b_separation_vs_recoverability.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)

    print(res.to_string(index=False))
    print(f"\nWritten: {path}")


if __name__ == "__main__":
    main()
