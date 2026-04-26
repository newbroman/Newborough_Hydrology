"""
05_pearson_affinity.py
Inputs:  01_wells_clean.csv, 02_cluster_stats.csv, 01_locations.csv
Outputs (intermediate): 05_pear_membership_audit.csv
Outputs (final): outputs/05_pearson_affinity/
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); del _sys, _os
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import geopandas as gpd, fiona
from adjustText import adjust_text
from matplotlib.lines import Line2D
from utils.config import CLUSTER_COLOURS, CLUSTER_LABELS
from utils.data_utils import normalize_well_name
from utils.map_utils import load_dem_layer, add_kml_features, add_osm_basemap
from utils.paths import (make_all_dirs, DATA_DIR,
    INT_WELLS_CLEAN, INT_CLUSTER_STATS, INT_LOCATIONS, INT_PEAR_AUDIT,
    OUT_05_CONFIDENCE_MAP)

fiona.drvsupport.supported_drivers["KML"] = "rw"
EXPECTED_CLUSTERS = sorted(CLUSTER_LABELS.keys())
plt.rcParams.update({"font.family":"sans-serif","axes.labelsize":11,"axes.titlesize":13,
                     "xtick.labelsize":9,"ytick.labelsize":9,"legend.fontsize":9})

def safe_pearson(a, b):
    pair = pd.concat([a,b],axis=1).dropna()
    if len(pair)<24: return np.nan
    x,y = pair.iloc[:,0], pair.iloc[:,1]
    if x.std(ddof=0)==0 or y.std(ddof=0)==0: return np.nan
    return x.corr(y, method='pearson')

def load_matrix(path):
    raw = pd.read_csv(path, index_col=0)
    def date_ratio(labels):
        if not len(labels): return 0.0
        return float(pd.Series(labels,dtype="string").fillna("").str.strip()
                     .str.match(r"^\d{1,4}[-/]\d{1,2}[-/]\d{1,4}$",na=False).mean())
    if date_ratio(raw.index) >= date_ratio(raw.columns):
        m = raw.copy(); m.index = pd.to_datetime(m.index,errors="coerce")
        m = m.loc[m.index.notna()].apply(pd.to_numeric,errors="coerce").T
        m.columns = pd.to_datetime(m.columns,errors="coerce"); m = m.loc[:,m.columns.notna()]
    else:
        m = raw.copy(); m.columns = pd.to_datetime(m.columns,errors="coerce")
        m = m.loc[:,m.columns.notna()].apply(pd.to_numeric,errors="coerce")
    m.index = [normalize_well_name(w) for w in m.index]
    m = m[~pd.Index(m.index).duplicated(keep="first")]
    return m.sort_index(axis=1)

def zscore_rows(df):
    return df.sub(df.mean(axis=1),axis=0).div(df.std(axis=1,ddof=0).replace(0,np.nan),axis=0)

def build_centroids(z_wells, cluster_map):
    centroids = {}
    for cl in EXPECTED_CLUSTERS:
        members = [m for m in cluster_map.loc[cluster_map["Cluster"]==cl,"Match_ID"] if m in z_wells.index]
        centroids[cl] = z_wells.loc[members].mean(axis=0,skipna=True) if members else pd.Series(np.nan,index=z_wells.columns)
    df = pd.DataFrame(centroids); df.columns=[f"Cluster_{c}" for c in df.columns]; return df

def classify(assigned, corr_row):
    col = f"Cluster_{int(assigned)}"
    if col not in corr_row.index: return "Unclassified",np.nan,np.nan,np.nan,np.nan
    ar = corr_row.get(col,np.nan); valid = corr_row.dropna()
    if valid.empty: return "Unclassified",np.nan,np.nan,ar,np.nan
    best_col=valid.idxmax(); best_r=valid.max(); best_c=int(best_col.split("_")[1])
    others=valid.drop(index=col,errors="ignore"); best_other=others.max() if len(others)>0 else np.nan
    delta = ar-best_other if pd.notna(best_other) and pd.notna(ar) else np.nan
    if pd.isna(ar): return "Unclassified",delta,best_c,ar,best_r
    if best_c!=int(assigned): return "Spy",delta,best_c,ar,best_r
    if pd.notna(delta) and delta>0.05: return "Core",delta,best_c,ar,best_r
    return "Fuzzy",delta,best_c,ar,best_r

def main():
    make_all_dirs()
    print("Starting 05: Pearson Membership Affinity Audit...")
    wells_matrix = load_matrix(INT_WELLS_CLEAN)
    cluster_df = pd.read_csv(INT_CLUSTER_STATS)
    cluster_df["Match_ID"] = cluster_df["Match_ID"].apply(normalize_well_name)
    cluster_df["Cluster"]  = pd.to_numeric(cluster_df["Cluster"],errors="coerce").astype("Int64")
    cluster_df = cluster_df.dropna(subset=["Match_ID","Cluster"])
    reference_ids = set(cluster_df["Match_ID"].tolist())
    wells_matrix = wells_matrix.loc[
        [w for w in wells_matrix.index if w in reference_ids]
    ]
    loc_df = pd.read_csv(INT_LOCATIONS)
    loc_df["Match_ID"] = loc_df["Match_ID"].apply(normalize_well_name)

    z_wells   = zscore_rows(wells_matrix)
    centroids = build_centroids(z_wells, cluster_df)
    corr_rows = []
    for wid, row in z_wells.iterrows():
        rec = {"Well_Normalised": wid}
        for cl in EXPECTED_CLUSTERS: rec[f"Cluster_{cl}"] = safe_pearson(row, centroids[f"Cluster_{cl}"])
        corr_rows.append(rec)
    corr_df = pd.DataFrame(corr_rows).set_index("Well_Normalised").sort_index()
    assignment_map = cluster_df.drop_duplicates(subset=["Match_ID"]).set_index("Match_ID")["Cluster"]

    audit_rows = []
    for wid in corr_df.index:
        assigned = assignment_map.get(wid, pd.NA)
        if pd.isna(assigned):
            cl, delta, best_c, ar, br = "Unclassified",np.nan,pd.NA,np.nan,np.nan
        else:
            cl, delta, best_c, ar, br = classify(int(assigned), corr_df.loc[wid])
        sec = corr_df.loc[wid].dropna()
        sec_c = int(str(sec.sort_values(ascending=False).index[1]).split("_")[1]) if len(sec)>=2 else np.nan
        audit_rows.append({"Well_Normalised":wid,
            "Assigned_Cluster": int(assigned) if not pd.isna(assigned) else pd.NA,
            "Best_Match_Cluster":best_c,"Secondary_Cluster":sec_c,
            "Assigned_r":ar,"Best_Match_r":br,"Delta_Assigned_vs_NextBest":delta,
            "Class":cl,"MCA_Count_r_gt_0_90":int((corr_df.loc[wid]>0.90).sum())})

    audit_df = pd.DataFrame(audit_rows).sort_values("Well_Normalised").reset_index(drop=True)
    audit_df["MCA_Flag"] = audit_df["MCA_Count_r_gt_0_90"]>=3
    for cl in EXPECTED_CLUSTERS:
        audit_df[f"r_Cluster_{cl}"] = audit_df["Well_Normalised"].map(corr_df[f"Cluster_{cl}"])

    def mca_label(row):
        pairs = [(cl,row.get(f"r_Cluster_{cl}",np.nan)) for cl in EXPECTED_CLUSTERS if pd.notna(row.get(f"r_Cluster_{cl}",np.nan)) and row.get(f"r_Cluster_{cl}",np.nan)>0.90]
        if len(pairs)<3: return ""
        return "/".join([f"C{cl}" for cl in sorted([c for c,_ in sorted(pairs,key=lambda x:x[1],reverse=True)[:3]])])
    audit_df["MCA_Cluster_Label"] = audit_df.apply(mca_label, axis=1)
    audit_df.to_csv(INT_PEAR_AUDIT, index=False)

    # Affinity bar chart
    preferred = ["ceh1","nw1","ceh8","ceh19","d15","ceh17"]
    available = [w for w in preferred if w in corr_df.index]
    if len(available)<3:
        available = list(audit_df.set_index("Well_Normalised")["Delta_Assigned_vs_NextBest"].abs().sort_values(ascending=False).index[:6])
        available = [w for w in available if w in corr_df.index]
    if available:
        plot_df = corr_df.loc[available].copy()
        plot_df.columns = [c.replace("Cluster_","C") for c in plot_df.columns]
        fig, ax = plt.subplots(figsize=(16,7), dpi=300)
        x = np.arange(len(available)); width=0.12
        n_bars = len(plot_df.columns)
        for i,col in enumerate(plot_df.columns):
            cid = int(col.replace("C","")) if col.replace("C","").isdigit() else None
            ax.bar(x+(i-(n_bars-1)/2)*width, plot_df[col].values, width=width,
                   label=CLUSTER_LABELS.get(cid,col), color=CLUSTER_COLOURS.get(cid,"#808080"),
                   edgecolor="black", linewidth=0.6)
        ax.set_xticks(x); ax.set_xticklabels([w.upper() for w in available])
        ax.set_ylabel("Pearson Correlation (r)")
        ax.set_title("Membership Affinity by Cluster for Key Wells", fontweight="bold")
        ax.grid(True,axis="y",linestyle="--",alpha=0.4)
        y_max = float(np.nanmax(plot_df.values)) if not plot_df.empty else 1.0
        y_min = min(0.0, float(np.nanmin(plot_df.values))-0.02) if not plot_df.empty else 0.0
        ax.set_ylim(y_min, min(1.05,y_max+0.22))
        ax.legend(title="Cluster",loc="lower right",frameon=True)

    # Spatial confidence map
    map_df = audit_df.merge(loc_df[["Match_ID","E","N"]], left_on="Well_Normalised", right_on="Match_ID", how="left")
    map_df = map_df.dropna(subset=["E","N","Best_Match_Cluster"])
    if not map_df.empty:
        class_markers = {"Core":"o","Fuzzy":"D","Spy":"*","Unclassified":"x"}
        fig, ax = plt.subplots(figsize=(12,10), dpi=300)
        dem_layer, dem_loaded = load_dem_layer(ax, DATA_DIR)
        if not dem_loaded:
            add_osm_basemap(ax, gpd.GeoDataFrame(map_df, geometry=gpd.points_from_xy(map_df["E"],map_df["N"]),crs="EPSG:27700"))
        if dem_layer is not None:
            fig.colorbar(dem_layer,ax=ax,shrink=0.55,pad=0.02,extend="both").set_label("Elevation (m AOD)",rotation=270,labelpad=18)
        site_feature_handles = add_kml_features(ax, DATA_DIR)
        for cls, marker in class_markers.items():
            subset = map_df[map_df["Class"]==cls]
            if subset.empty:
                continue
            colours = [CLUSTER_COLOURS.get(int(c),"grey") for c in subset["Best_Match_Cluster"]]
            ax.scatter(subset["E"],subset["N"],c=colours,marker=marker,
                       s=120 if cls!="Spy" else 180,edgecolor="black",linewidth=0.6,alpha=0.9,zorder=5)

            # Show secondary cluster inside fuzzy/spy markers to mirror PEAR LCSC map logic.
            if cls in {"Fuzzy", "Spy"}:
                for _, row in subset.iterrows():
                    if pd.notna(row.get("Secondary_Cluster")):
                        ax.text(
                            row["E"],
                            row["N"],
                            f"{int(row['Secondary_Cluster'])}",
                            ha="center",
                            va="center",
                            fontsize=6.2,
                            fontweight="bold",
                            color="black",
                            zorder=7,
                        )

        # MCA overlay: add combination-specific symbols for wells with >=3 strong cluster affinities.
        mca_subset = map_df[map_df["MCA_Flag"]==True]
        mca_handles = []
        if not mca_subset.empty:
            symbol_cycle = ["s", "^", "v", "P", "X", "<", ">", "h", "8", "d"]
            combo_labels = sorted([lab for lab in mca_subset["MCA_Cluster_Label"].dropna().unique() if str(lab).strip()])
            combo_to_symbol = {lab: symbol_cycle[i % len(symbol_cycle)] for i, lab in enumerate(combo_labels)}

            for combo_label, marker in combo_to_symbol.items():
                sub = mca_subset[mca_subset["MCA_Cluster_Label"]==combo_label]
                if sub.empty:
                    continue

                combo_tag = combo_label.replace("C", "").replace("/", "")
                ax.scatter(
                    sub["E"],
                    sub["N"],
                    facecolors="none",
                    edgecolors="black",
                    marker=marker,
                    s=300,
                    linewidth=1.2,
                    alpha=0.95,
                    zorder=6,
                )
                mca_handles.append(
                    Line2D(
                        [0],
                        [0],
                        marker=marker,
                        color="black",
                        markerfacecolor="none",
                        markersize=10,
                        linestyle="None",
                        label=f"MCA {combo_label} ({combo_tag})",
                    )
                )

        texts = [ax.text(row["E"],row["N"],row["Well_Normalised"].upper(),fontsize=7,alpha=0.85,zorder=7) for _,row in map_df.iterrows()]
        ax.set_title("Membership Affinity Map: Best Match Cluster and Confidence",fontweight="bold")
        ax.set_xlabel("Easting (m)"); ax.set_ylabel("Northing (m)")
        ax.grid(True,linestyle="--",alpha=0.4); ax.set_aspect("equal",adjustable="box")
        status_handles = [
            Line2D([0],[0],marker="o",color="w",markerfacecolor="grey",markeredgecolor="black",markersize=8,linestyle="None",label="Core"),
            Line2D([0],[0],marker="D",color="w",markerfacecolor="grey",markeredgecolor="black",markersize=8,linestyle="None",label="Fuzzy (number = secondary cluster)"),
            Line2D([0],[0],marker="*",color="w",markerfacecolor="grey",markeredgecolor="black",markersize=11,linestyle="None",label="Spy (number = secondary cluster)"),
        ]
        cl1 = ax.legend(handles=status_handles,title="Status / Confidence",loc="upper left",frameon=True); ax.add_artist(cl1)
        cluster_handles = [Line2D([0],[0],marker="o",color="w",markerfacecolor=CLUSTER_COLOURS[c],markeredgecolor="black",markersize=8,label=CLUSTER_LABELS.get(c,f"C{c}")) for c in EXPECTED_CLUSTERS]
        cl2 = ax.legend(handles=cluster_handles,title="Best-Match Cluster",loc="lower left",frameon=True); ax.add_artist(cl2)

        if mca_handles:
            cl3 = ax.legend(handles=mca_handles,title="MCA Cx/Cy/Cz",loc="upper right",frameon=True)
            ax.add_artist(cl3)

        if site_feature_handles:
            dedup = {}
            for handle in site_feature_handles:
                dedup[handle.get_label()] = handle
            ax.legend(handles=list(dedup.values()),title="Site Features",loc="lower right",frameon=True)
        if texts: adjust_text(texts,arrowprops=dict(arrowstyle="-",color="gray",lw=0.5),ax=ax)
        plt.tight_layout(); plt.savefig(OUT_05_CONFIDENCE_MAP,dpi=300,bbox_inches="tight"); plt.close()

    core_c = int((audit_df["Class"]=="Core").sum())
    fuzzy_c = int((audit_df["Class"]=="Fuzzy").sum())
    spy_c = int((audit_df["Class"]=="Spy").sum())
    mca_wells = audit_df.loc[audit_df["MCA_Flag"]==True,"Well_Normalised"].str.upper().tolist()
    print(f"\nMembership Summary: Core={core_c} Fuzzy={fuzzy_c} Spy={spy_c} MCA={len(mca_wells)}")
    if mca_wells: print("MCA wells:", ", ".join(mca_wells))
    print(f"Saved: {INT_PEAR_AUDIT.name}, {OUT_05_CONFIDENCE_MAP.name}")

if __name__ == "__main__": main()
