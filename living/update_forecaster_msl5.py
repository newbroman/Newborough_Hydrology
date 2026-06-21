#!/usr/bin/env python3
"""
update_forecaster_msl5.py
=========================

Build the forecaster's own living MSL5 file (`forecaster_msl5.json`) from the
canonical living hub, using the van Willegen method shared with Script 26
(via msl_common). Run monthly with WW and pushed to NHGR alongside
`latest_readings.json`. Does NOT touch the PL/TR.

MSL5 is a 5-year mean of spring (Mar-May) levels, so it only moves once a full
spring completes (~annually). Regenerating monthly is harmless; the value is
simply unchanged between springs.

Output JSON (forecaster_msl5.json):
    {
      "generated": "2026-06-18T..Z",
      "method": "van Willegen 2025 MSL5 (5-yr mean spring level, m below ground)",
      "n_wells": 77,
      "wells":    { "ceh6": {"MSL5_m_bg": -0.47, "window_end_year": 2025,
                             "n_years_in_window": 5}, ... },
      "clusters": { "C1": {"mean_MSL5_m_bg": -0.31, "n": 6}, ... }
    }

Per-well is the headline (what the forecaster shows on well-select); per-cluster
is a simple mean of member wells' latest MSL5, for the same fallback chain the
current-levels feed uses (well -> cluster -> default).
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import msl_common  # noqa: E402


def load_hub_long(hub_path: str) -> pd.DataFrame:
    df = pd.read_csv(hub_path).dropna(subset=["depth_below_ground"])
    req = {"well", "date", "depth_below_ground"}
    missing = req - set(df.columns)
    if missing:
        raise ValueError(f"Hub {hub_path} missing column(s): {sorted(missing)}")
    df["well"] = df["well"].astype(str).str.strip().str.lower()
    df["year"] = df["date"].str[:4].astype(int)
    df["month"] = df["date"].str[5:7].astype(int)
    return df.rename(columns={"depth_below_ground": "level_bg"})[
        ["well", "year", "month", "level_bg"]]


def load_cluster_map(master_path: str) -> dict:
    m = pd.read_csv(master_path)
    if "Name_Original" not in m.columns or "Cluster" not in m.columns:
        raise ValueError(f"{master_path} needs Name_Original and Cluster columns")
    out = {}
    for _, r in m.iterrows():
        try:
            out[str(r["Name_Original"]).strip().lower()] = f"C{int(r['Cluster'])}"
        except (ValueError, TypeError):
            continue
    return out


def build(hub_path: str, master_path: str) -> dict:
    latest = msl_common.msl5_latest_from_long(load_hub_long(hub_path))
    cluster_map = load_cluster_map(master_path)

    wells = {}
    for _, r in latest.iterrows():
        wells[r["well"]] = {
            "MSL5_m_bg": round(float(r["MSL5_m_bg"]), 3),
            "window_end_year": int(r["window_end_year"]),
            "n_years_in_window": int(r["n_years_in_window"]),
        }

    latest = latest.copy()
    latest["cluster"] = latest["well"].map(cluster_map)
    clusters = {}
    for cid, grp in latest.dropna(subset=["cluster"]).groupby("cluster"):
        clusters[cid] = {
            "mean_MSL5_m_bg": round(float(grp["MSL5_m_bg"].mean()), 3),
            "n": int(len(grp)),
        }

    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "van Willegen 2025 MSL5 (5-yr mean spring level, m below ground)",
        "n_wells": len(wells),
        "wells": wells,
        "clusters": dict(sorted(clusters.items())),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Build the forecaster living MSL5 file from the hub.")
    ap.add_argument("--hub", required=True, help="Living hub CSV.")
    ap.add_argument("--cluster-map", required=True,
                    help="03_master_data.csv (Name_Original, Cluster).")
    ap.add_argument("--out", required=True, help="Path to write forecaster_msl5.json.")
    args = ap.parse_args()

    try:
        feed = build(args.hub, args.cluster_map)
    except Exception as e:  # noqa: BLE001
        print(f"  [ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(feed, f, indent=2)
        f.write("\n")

    yrs = sorted({v["window_end_year"] for v in feed["wells"].values()})
    print(f"  Forecaster MSL5 written: {args.out}")
    print(f"    wells          : {feed['n_wells']}")
    print(f"    clusters       : {len(feed['clusters'])}")
    print(f"    window-end yrs : {yrs[0]}..{yrs[-1]} (per-well; latest valid window)")
    print()
    print(f"  Commit to NHGR with latest_readings.json.")


if __name__ == "__main__":
    main()
