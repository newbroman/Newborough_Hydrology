#!/usr/bin/env python3
"""
update_forecaster_feed.py
=========================

Derive the forecaster's live-state feed (`latest_readings.json`) from the
canonical living readings hub and the frozen cluster partition.

This is the "small step" in the monthly run that turns the latest field round
into the per-well + per-cluster current state the forecaster prepopulates its
inputs with. It does NOT touch the frozen analysis (the PL / technical report)
and it does NOT push to git — it only writes the JSON. The user commits and
pushes `latest_readings.json` (and the hub CSV) to NHGR manually.

Contracts
---------
Living hub CSV (tidy long, one row per well per month):
    well,date,water_mAOD,depth_below_ground
  - well   : lowercase well id (e.g. 'ceh6'), matching 03_master_data.csv
             Name_Original and the forecaster bundle's well names.
  - date   : YYYY-MM or YYYY-MM-DD; the month the reading belongs to.
  - water_mAOD          : water-table elevation, metres AOD.
  - depth_below_ground  : water_mAOD - ground_elev (negative = below ground).

Cluster map (frozen, from the PL — outputs/03_master_data.csv):
    Name_Original,Cluster,...      Cluster is an integer 1..5.

Output JSON (latest_readings.json):
    {
      "as_of": "2026-05",
      "generated": "2026-06-18T12:34:56Z",
      "n_wells": 64,
      "wells":   { "ceh6": {"water_mAOD": 7.99, "depth_below_ground": -0.47}, ... },
      "clusters":{ "C1": {"mean_water_mAOD": ..., "mean_depth_below_ground": ...,
                          "n": 6}, ... }
    }

The forecaster consumes this with the fallback chain:
    well's own reading  ->  its cluster's current mean  ->  bundle long-term default.
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import pandas as pd


def _month_key(series: pd.Series) -> pd.Series:
    """Normalise a date column to a YYYY-MM month key."""
    dt = pd.to_datetime(series, errors="coerce")
    if dt.isna().all():
        raise ValueError("Could not parse any dates in the hub 'date' column.")
    return dt.dt.strftime("%Y-%m")


def load_hub(hub_path: str) -> pd.DataFrame:
    df = pd.read_csv(hub_path)
    required = {"well", "date", "water_mAOD", "depth_below_ground"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Hub {hub_path} is missing column(s): {sorted(missing)}. "
            f"Found: {list(df.columns)}"
        )
    df["well"] = df["well"].astype(str).str.strip().str.lower()
    df["month"] = _month_key(df["date"])
    return df


def load_cluster_map(master_path: str) -> dict:
    """Return {well_id_lower: 'C{n}'} from the frozen 03_master_data.csv."""
    m = pd.read_csv(master_path)
    if "Name_Original" not in m.columns or "Cluster" not in m.columns:
        raise ValueError(
            f"{master_path} must have 'Name_Original' and 'Cluster' columns; "
            f"found {list(m.columns)}"
        )
    out = {}
    for _, row in m.iterrows():
        well = str(row["Name_Original"]).strip().lower()
        try:
            cid = int(row["Cluster"])
        except (ValueError, TypeError):
            continue
        out[well] = f"C{cid}"
    return out


def build_feed(hub: pd.DataFrame, cluster_map: dict) -> dict:
    # Latest month present in the hub.
    as_of = sorted(hub["month"].dropna().unique())[-1]
    latest = hub[hub["month"] == as_of].copy()

    # Drop rows with no usable level (dry / inaccessible / not read this round).
    latest = latest.dropna(subset=["water_mAOD"])

    # Per-well block — last value wins if a well somehow appears twice.
    wells = {}
    for _, r in latest.iterrows():
        well = r["well"]
        entry = {"water_mAOD": round(float(r["water_mAOD"]), 3)}
        if pd.notna(r["depth_below_ground"]):
            entry["depth_below_ground"] = round(float(r["depth_below_ground"]), 3)
        wells[well] = entry

    # Per-cluster means — only over wells that carry a frozen cluster assignment.
    latest["cluster"] = latest["well"].map(cluster_map)
    clusters = {}
    for cid, grp in latest.dropna(subset=["cluster"]).groupby("cluster"):
        clusters[cid] = {
            "mean_water_mAOD": round(float(grp["water_mAOD"].mean()), 3),
            "mean_depth_below_ground": (
                round(float(grp["depth_below_ground"].dropna().mean()), 3)
                if grp["depth_below_ground"].notna().any() else None
            ),
            "n": int(grp["water_mAOD"].notna().sum()),
        }

    return {
        "as_of": as_of,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_wells": len(wells),
        "wells": wells,
        "clusters": dict(sorted(clusters.items())),
    }


def main():
    ap = argparse.ArgumentParser(
        description="Build the forecaster latest_readings.json from the living hub."
    )
    ap.add_argument("--hub", required=True,
                    help="Path to the living hub CSV "
                         "(well,date,water_mAOD,depth_below_ground).")
    ap.add_argument("--cluster-map", required=True,
                    help="Path to the frozen 03_master_data.csv (Name_Original, Cluster).")
    ap.add_argument("--out", required=True,
                    help="Path to write latest_readings.json.")
    args = ap.parse_args()

    try:
        hub = load_hub(args.hub)
        cluster_map = load_cluster_map(args.cluster_map)
        feed = build_feed(hub, cluster_map)
    except Exception as e:  # noqa: BLE001 — surface a clean message, not a traceback
        print(f"  [ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(feed, f, indent=2)
        f.write("\n")

    n_clusters = len(feed["clusters"])
    print(f"  Forecaster feed written: {args.out}")
    print(f"    as_of    : {feed['as_of']}")
    print(f"    wells    : {feed['n_wells']}")
    print(f"    clusters : {n_clusters} "
          f"({', '.join(f'{k}:n={v[chr(110)]}' for k, v in feed['clusters'].items())})")
    print()
    print("  Commit to NHGR:")
    print(f"    git add {args.out} <living hub csv>")
    print(f"    git commit -m 'forecaster feed: {feed['as_of']}'")
    print(f"    git push")


if __name__ == "__main__":
    main()
