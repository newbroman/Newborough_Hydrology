#!/usr/bin/env python3
"""
compare_model_inputs.py

Flag differences between two versions of Newborough_Cleaned_For_Model.csv
BEFORE running the pipeline, so you know what to expect downstream.

Layout assumption (matches the cleaned model input):
  - row 0  : junk comma row (skipped)
  - row 1  : reading dates  -> column header
  - col 0  : well IDs       -> row index

Usage:
  python compare_model_inputs.py BASELINE.csv MODIFIED.csv

Separates:
  - genuine value changes (> TOL)
  - gap fills    (NaN -> value)
  - deletions    (value -> NaN)
  - cosmetic float-precision noise (<= TOL)
  - well-ID relabels / additions / removals
  - date-column additions / removals
"""
import sys
import pandas as pd
import numpy as np

TOL = 1e-6  # below this, treat as float-precision cosmetic only


def load(path):
    df = pd.read_csv(path, header=1, index_col=0)
    df.index = df.index.astype(str).str.strip()
    df = df[(df.index != "nan") & (df.index != "")]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def norm_ids(idx):
    """Normalise well IDs (strip all whitespace, lowercase) for alignment."""
    return (pd.Index(idx).astype(str).str.strip()
            .str.replace(r"\s+", "", regex=True).str.lower())


def main(baseline, modified):
    a_raw, b_raw = load(baseline), load(modified)

    # --- ID-level changes (before normalising) ---
    a_ids, b_ids = list(a_raw.index), list(b_raw.index)
    a_n = dict(zip(norm_ids(a_ids), a_ids))
    b_n = dict(zip(norm_ids(b_ids), b_ids))
    relabels = {a_n[k]: b_n[k] for k in (set(a_n) & set(b_n))
                if a_n[k] != b_n[k]}
    removed_wells = sorted(a_n[k] for k in set(a_n) - set(b_n))
    added_wells = sorted(b_n[k] for k in set(b_n) - set(a_n))

    # --- align on normalised IDs + common date columns ---
    a = a_raw.copy(); a.index = norm_ids(a.index)
    b = b_raw.copy(); b.index = norm_ids(b.index)
    a = a.apply(pd.to_numeric, errors="coerce")
    b = b.apply(pd.to_numeric, errors="coerce")
    wells = [w for w in a.index if w in b.index]
    cols = [c for c in a.columns if c in b.columns]
    a, b = a.loc[wells, cols], b.loc[wells, cols]

    removed_dates = sorted(set(a_raw.columns) - set(b_raw.columns))
    added_dates = sorted(set(b_raw.columns) - set(a_raw.columns))

    na, nb = a.isna(), b.isna()
    filled = (na & ~nb)
    deleted = (~na & nb)
    both = (~na & ~nb)
    diff = (a - b).abs()
    changed = both & (diff > TOL)
    cosmetic = both & (diff > 0) & (diff <= TOL)

    print(f"BASELINE : {baseline}  ({a_raw.shape[0]} wells x {a_raw.shape[1]} dates)")
    print(f"MODIFIED : {modified}  ({b_raw.shape[0]} wells x {b_raw.shape[1]} dates)")
    print()
    print("=== STRUCTURE ===")
    print(f"  well relabels   : {relabels or 'none'}")
    print(f"  wells added     : {added_wells or 'none'}")
    print(f"  wells removed   : {removed_wells or 'none'}")
    print(f"  date cols added : {added_dates or 'none'}")
    print(f"  date cols removed: {removed_dates or 'none'}")
    print()
    print("=== CELLS (aligned) ===")
    print(f"  values changed (>{TOL}): {int(changed.values.sum())}")
    print(f"  gaps filled (NaN->val) : {int(filled.values.sum())}")
    print(f"  deletions (val->NaN)   : {int(deleted.values.sum())}")
    print(f"  cosmetic float-only    : {int(cosmetic.values.sum())}")
    print()

    if changed.values.sum():
        ch = changed.stack(); idx = ch[ch].index
        rows = [(w, d, a.loc[w, d], b.loc[w, d], b.loc[w, d] - a.loc[w, d])
                for w, d in idx]
        cd = pd.DataFrame(rows, columns=["well", "date", "baseline", "modified", "delta_m"])
        g = (cd.assign(absd=cd.delta_m.abs())
             .groupby("well").agg(n=("delta_m", "size"),
                                  mean_delta=("delta_m", "mean"),
                                  max_abs=("absd", "max"))
             .sort_values("n", ascending=False))
        # flag constant-offset wells (datum corrections)
        g["constant_offset?"] = (cd.groupby("well").delta_m.std().fillna(0) < 1e-9).reindex(g.index)
        print("=== VALUE CHANGES BY WELL (constant_offset=True => likely datum fix) ===")
        print(g.to_string())
        print()
        print("=== LARGEST 20 ABSOLUTE CHANGES ===")
        print(cd.assign(absd=cd.delta_m.abs()).sort_values("absd", ascending=False)
              .head(20).drop(columns="absd").to_string(index=False))
        print()

    if filled.values.sum():
        fl = filled.sum(axis=0).sort_values(ascending=False)
        whole_col = fl[fl == len(wells)].index.tolist()
        print(f"=== GAP FILLS ===  (dates filled for ALL wells = restored survey rounds: {whole_col or 'none'})")
        print(fl[fl > 0].head(12).to_string())
        print()

    if deleted.values.sum():
        dl = deleted.stack(); didx = dl[dl].index
        print("=== DELETIONS (well, date) ===")
        for w, d in didx:
            print(f"  {w}  {d}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python compare_model_inputs.py BASELINE.csv MODIFIED.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
