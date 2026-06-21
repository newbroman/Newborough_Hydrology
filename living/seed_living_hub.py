#!/usr/bin/env python3
"""
seed_living_hub.py
==================

One-time seed of the canonical living readings hub from the frozen, cleaned
per-well level series the published analysis used.

Why this exists
---------------
The forecaster's living products (current-state feed + living MSL5) read a
single operational series, the "hub". MSL5 needs five years of spring data, so
the hub must start with the full historical record, not just future rounds.
We seed it from the PL's cleaned mAOD output (`01_wells_clean_maod.csv`) so the
historical levels in the hub are identical to those behind the published MSL5.

This reads frozen PL outputs as static inputs; it does NOT re-run the PL and
does not change any PL/TR number. After seeding, `intake_monthly.py` appends
each new month to the same hub.

Geometry note
-------------
For internal consistency, depth_below_ground must use the SAME geometry that
produced the frozen mAOD. Pass the geometry CSV the frozen run used. Well names
are normalised exactly as Script 01 does (lower-case, strip spaces and
underscores), so spaced ids like "ceh 1" / "nw 4b" resolve to ceh1 / nw4b.

Hub schema (tidy long, one row per well per month)
--------------------------------------------------
    well,date,water_mAOD,depth_below_ground
"""

import argparse
import sys

import pandas as pd


def _norm(s: pd.Series) -> pd.Series:
    """Normalise well ids exactly as Script 01 does."""
    return (s.astype(str).str.strip().str.lower()
            .str.replace(" ", "", regex=False)
            .str.replace("_", "", regex=False))


def load_geometry(loc_path: str) -> pd.DataFrame:
    g = pd.read_csv(loc_path)
    g.columns = [c.strip() for c in g.columns]
    need = {"Name", "Upstand_m", "Pipe_Top_Elev"}
    missing = need - set(g.columns)
    if missing:
        raise ValueError(f"{loc_path} missing column(s): {sorted(missing)}")
    g["well"] = _norm(g["Name"])
    # ground_elev = pipe-top minus upstand, so depth_below_ground reduces to
    # raw_depth + upstand — exactly Script 26's below-ground frame.
    g["ground_elev"] = g["Pipe_Top_Elev"] - g["Upstand_m"]
    return g[["well", "ground_elev"]].dropna(subset=["ground_elev"]).drop_duplicates("well")


def seed(maod_path: str, loc_path: str) -> pd.DataFrame:
    wide = pd.read_csv(maod_path, index_col=0)
    wide.index = pd.to_datetime(wide.index, errors="coerce")
    if wide.index.isna().any():
        raise ValueError(f"{maod_path}: some row labels are not dates.")

    long = (
        wide.reset_index(names="date")
        .melt(id_vars="date", var_name="well", value_name="water_mAOD")
        .dropna(subset=["water_mAOD"])
    )
    long["well"] = _norm(long["well"])
    long["date"] = long["date"].dt.strftime("%Y-%m")

    geom = load_geometry(loc_path)
    merged = long.merge(geom, on="well", how="left")

    no_geom = sorted(merged.loc[merged["ground_elev"].isna(), "well"].unique())
    if no_geom:
        print(f"  [WARN] {len(no_geom)} well(s) have no geometry in "
              f"{loc_path}; depth_below_ground left blank: {', '.join(no_geom)}",
              file=sys.stderr)

    merged["depth_below_ground"] = (merged["water_mAOD"] - merged["ground_elev"]).round(3)
    merged["water_mAOD"] = merged["water_mAOD"].round(3)

    return (merged[["well", "date", "water_mAOD", "depth_below_ground"]]
            .sort_values(["well", "date"]).reset_index(drop=True))


def main():
    ap = argparse.ArgumentParser(
        description="Seed the living readings hub from the frozen cleaned mAOD series."
    )
    ap.add_argument("--maod", required=True,
                    help="Path to 01_wells_clean_maod.csv (frozen PL output).")
    ap.add_argument("--locations", required=True,
                    help="Geometry CSV that the frozen run used "
                         "(Well_locations_height.csv).")
    ap.add_argument("--out", required=True,
                    help="Path to write the seeded hub CSV (readings_living.csv).")
    args = ap.parse_args()

    try:
        hub = seed(args.maod, args.locations)
    except Exception as e:  # noqa: BLE001
        print(f"  [ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    hub.to_csv(args.out, index=False)
    months = sorted(hub["date"].unique())
    print(f"  Living hub seeded: {args.out}")
    print(f"    rows  : {len(hub)}")
    print(f"    wells : {hub['well'].nunique()}")
    print(f"    span  : {months[0]} .. {months[-1]} ({len(months)} months)")
    print()
    print("  Historical seed. intake_monthly.py appends new months; commit to NHGR once.")


if __name__ == "__main__":
    main()
