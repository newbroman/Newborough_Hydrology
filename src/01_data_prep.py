"""
01_data_prep.py
Purpose: Prepares raw groundwater, location, and climate data, producing cleaned
outputs and reference/extended network splits for downstream scripts.

Outputs (intermediate — outputs/ root):
    01_locations.csv
    01_climate.csv
    01_wells_clean.csv
    01_wells_provenance.csv
    01_wells_reference.csv
    01_wells_extended.csv

Requirements:
    pandas, numpy
"""

__version__ = "1.7.0"  # Hollingham (2026) — 2026-06-20 (interpolated cells now a solid distinct colour, not a hatch)
# 2026-07-19: figure saves routed through render_utils.render_figure (A4 dpi cap)
# Changelog:
#   1.4.1 (2026-06-15) — Coverage-figure fix-up: (1) cluster band labels are now
#     horizontal at each band midpoint (pulled from CLUSTER_LABELS), fixing the
#     overprint that rendered "C9"/"C4)" on the thin C4/C5 bands; all bands read
#     C1-C5. (2) Figure axis now starts April 2005 (RECORD_START_DISPLAY): the
#     lone 13/04/2005 pre-system reading buckets to March 2005 and is dropped
#     from the display so figure and report agree; title reads "Apr 2005 - Feb
#     2026".
#   1.4.0 (2026-06-15) — Merged the data-coverage figure (former
#     01b_coverage_figure.py) into Script 01. After cleaning the wells, parse the
#     field comments in the raw records spreadsheet (DATA_WELL_RECORDS_ODS) into
#     per-cell observation states {dry, flooded, not_found, inaccessible}, add
#     inferred-dry (dry-season + missing-run block-fill), scope to the pipeline
#     wells and months, and write two NEW outputs: 01_observation_states.csv and
#     01_dry_depths.csv. Then render 01_coverage_states.png. Both the parse and
#     the figure are guarded: the parse is skipped (falling back to any committed
#     state CSV) if the .ods is absent; the figure is deferred on a cold first
#     pass because it colours wells by cluster and 03_master_data.csv is produced
#     downstream — re-run Script 01 after a full pipeline pass to render it.
#     PURELY ADDITIVE to existing outputs: 01_wells_provenance.csv and its
#     {measured, interpolated, missing} vocabulary are unchanged. Parsing lives
#     in utils/comment_states.py; vocabulary/dates in utils/config.py.
#     Reviewer-proofing in the same release: (a) a dry/not_found/inaccessible
#     comment overrides only a BLANK or INTERPOLATED cell, never a genuine
#     measurement — collisions are kept as measured and logged to
#     01_observation_state_conflicts.csv for adjudication; (b) the figure
#     respects BW_MODE (colours/hatches from config, greyscale-safe); (c) the
#     output is 01_coverage_states.png and the palette lives in config.
#   1.3.0 (2026-05-24) — Added "pdfs" to EXTENDED_NETWORK_BLACKLIST: the well
#     carries a tidal-influence signature and is unrepresentative of
#     water-table behaviour (same exclusion principle as CEH3/CEH22 in the
#     reference whitelist, same family as Llyn Rhos). With p1's elevation row
#     now completed in well_metadata.csv, the classified network
#     settles at 88 wells (66 reference + 22 extended). See
#     FIX_BRIEF_pdfs_p1_network_88.md.
#   1.2.0 (2026-05-19) — Defect E fix: emit 01_wells_provenance.csv alongside
#     01_wells_clean.csv, recording per-cell origin as one of
#     {"measured", "interpolated", "missing"}. This is paired with the
#     clean_well_series policy change (limit=3 -> limit=1) in
#     utils/data_utils.py: single missed monthly visits are bridged, but
#     multi-month gaps now stay NaN. Downstream consumers (clearfell_common,
#     Script 10d summer minima, Script 03 SSM sensitivity path) read the
#     provenance file to filter or report interpolated rows. See
#     DEFECT_E_INTERPOLATION_AUDIT.md for the diagnostic that motivated
#     this change.
#   1.1.1 (2026-05-14) — Docstring fix: REFERENCE_NETWORK_WHITELIST comment
#     said "69 wells"; corrected to 66 (= published partition, no real wells
#     lost; stale text from a pre-publication count).
#   1.1.0 (2026-05-14) — Clarified the well-cleaning call to call out the
#     depth-floor sign-convention fix in utils/data_utils.py. The cleaning
#     function now masks readings deeper than -4.0 m (corrected comparison
#     direction); positive readings, which represent slack flooding above
#     pipe top, are retained.
#   1.0.0 (2026-04-10) — Initial pipeline release.

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from utils.console_utils import (
    banner, phase, step, info, saved, warn, error, note, done, result,
    hr, skipped,
)
del _sys, _os

import pandas as pd
import numpy as np

from utils.paths import (
    make_all_dirs,
    DATA_WELLS_RAW, DATA_LOCATIONS_RAW, DATA_CLIMATE_RAW,
    DATA_WELL_ELEVATIONS,
    DATA_DIR,
    INT_LOCATIONS, INT_CLIMATE, INT_WELLS_CLEAN, INT_WELLS_CLEAN_MAOD,
    INT_WELLS_PROVENANCE,
    INT_WELLS_REFERENCE, INT_WELLS_EXTENDED,
    INT_WELL_ELEVATIONS,
    DATA_WELL_RECORDS_ODS, INT_OBSERVATION_STATES, INT_DRY_DEPTHS, OUT_DIR,
    INT_COVERAGE_FIGURE_REF, INT_COVERAGE_FIGURE_EXT,
    INT_OBS_STATE_CONFLICTS, INT_PEAR_AUDIT_SITEWIDE,
)
from utils.data_utils import normalize_well_name, parse_met_date, clean_well_series
from utils.comment_states import parse_comment_states, assemble_observation_states
from utils.config import (REFERENCE_CUTOFF_DATE, RAF_VALLEY_LAT_DEG, CLUSTER_LABELS,
    RECORD_START_DISPLAY, EXCLUDED_STUDY_AREA_WELLS, LAKE_GAUGE_REASON,
    get_cluster_colour, get_obs_state_colours, get_obs_state_hatches)
from utils.render_utils import render_figure

# Consolidated well elevation / upstand reference, read via the paths constant
# (was hardcoded to Well_locations_height.csv, which bypassed the consolidation
# so the maOD step could silently use a stale elevation source).
_WELL_ELEV_FILE = DATA_WELL_ELEVATIONS

MIN_MONTHS_THRESH   = 100
RECENCY_DATE        = pd.Timestamp(REFERENCE_CUTOFF_DATE)
MIN_EXTENDED_MONTHS = 24

# ──────────────────────────────────────────────────────────────────────────────
# REFERENCE NETWORK WHITELIST
#
# The cluster analysis (Script 02) and the mechanistic SSM fits (Script 03)
# assume each cluster represents a coherent hydrogeological population whose
# water-level response to climate forcing is stationary over the monitoring
# period. Wells that have experienced a non-stationary regime change — for
# instance, clearfelling which removes the canopy interception loss and
# initiates an ongoing upward drift in the water table — violate this
# assumption. Their single-β SSM fit does not describe any real physical
# state; it averages over a pre-transition regime, a transition period,
# and an incomplete post-transition equilibrium.
#
# This whitelist pins the reference network to the 66 wells that were
# clustered and modelled in the published analysis (Hollingham 2026,
# Table 2). It excludes:
#
#   - The five "FE" and "LIS" wells (FE1, FE2, FE3, FE4, LIS1) from the
#     clearfell management footprint. These remain available in the
#     extended-network analysis (Script 06) and form the treatment arm
#     of the clearfell BACI analysis (Script 10 / Section 4.6).
#
#   - The Llyn Rhos well, which reads a lake surface rather than a water
#     table. An SSM fit treating Llyn Rhos as a water-table response is
#     physical nonsense; it is excluded from the reference network on
#     the same "not in a stationary single-β regime" grounds as FE/LIS.
#     Llyn Rhos is also excluded from the extended network via the
#     EXTENDED_NETWORK_BLACKLIST (see below) because its lake-stage
#     signal is not interpretable as groundwater behaviour.
#
#   - CEH3 and CEH22, which Ward's hierarchical clustering consistently
#     identifies as singleton outliers. Their correlation structure does
#     not align with any of the behavioural groups in the rest of the
#     network — a signature consistent with tidal-signal contamination
#     on top of the climate-forcing response the SSM is designed to
#     capture. Both wells are low-elevation and coastal (ground elevation
#     3.3 m at CEH22; CEH3 shows the clearest tidal signature on
#     inspection). Including them distorts the Ward's tree at lower k
#     values: CEH3 suppresses the Lake/Dune split at k=4 on a 68-well
#     network, and CEH22 is a persistent singleton at k=5..9 on a 67-
#     well network. Like FE/LIS and Llyn Rhos, CEH3 and CEH22 remain in
#     the extended network for per-well analyses.
#
#   - Any other wells that meet the automatic record-length criterion
#     (>=100 monthly observations, record extending to 2026-02) but were
#     not part of the original 2026 reference network. Those wells may
#     have joined the network more recently and are available in the
#     extended-network analyses.
#
# To restore the fully automatic reference-network selection (i.e., let
# any well meeting MIN_MONTHS_THRESH and RECENCY_DATE into the reference
# network), set REFERENCE_NETWORK_WHITELIST = None.
# ──────────────────────────────────────────────────────────────────────────────
REFERENCE_NETWORK_WHITELIST = frozenset({
    "ceh1",  "ceh10", "ceh11", "ceh13", "ceh14", "ceh16", "ceh17", "ceh18",
    "ceh19", "ceh2",  "ceh20", "ceh21", "ceh23", "ceh24", "ceh25",
    "ceh26", "ceh27", "ceh28", "ceh30", "ceh31", "ceh32", "ceh33",
    "ceh34", "ceh36", "ceh39", "ceh4",  "ceh40", "ceh41", "ceh42", "ceh5",
    "ceh6",  "ceh9",  "d10",   "d15",   "d17",   "d25",   "d38",   "d41",
    "d43",   "d44",   "d5",    "d6",    "d7",    "d8",    "d9",    "l7",
    "nw1",   "nw10",  "nw11",  "nw13",  "nw2",   "nw3",   "nw4",
    "nw4b",  "nw5",   "nw6",   "nw7",   "nw9",   "t41a",  "t41b",  "t41c",
    "t41d",  "wmc1",  "wmc2",  "wmc3",  "wmc4",
})

# ──────────────────────────────────────────────────────────────────────────────
# EXTENDED NETWORK BLACKLIST
#
# Wells excluded from BOTH networks — not just the reference network.
# The reference whitelist already keeps these out of the clustering and SSM,
# but by default they still appear in the extended network (Script 06) because
# they meet the minimum-record-length criterion.
#
# Llyn Rhos-ddu is a lake-stage measurement, not a water-table observation.
# Including it in the extended Pearson affinity audit adds a physically
# meaningless data point (best-match r = 0.66, lowest in the sitewide
# audit) that cannot be interpreted as groundwater behaviour. It is
# excluded here so that Scripts 05/06 remain purely algorithmic and the
# exclusion rationale is documented in one place.
#
# pdfs carries a tidal-influence signature: its hydrograph is unrepresentative
# of water-table behaviour, the same exclusion principle applied to CEH3 and
# CEH22 in the reference whitelist (and the same family as Llyn Rhos). It is
# excluded from both networks on that ground.
#
# To include a blacklisted well in the extended network (e.g. for a
# lake-level comparison study), remove it from this set.
# ──────────────────────────────────────────────────────────────────────────────
EXTENDED_NETWORK_BLACKLIST = frozenset({
    "llynrhos",   # lake surface, not a water-table response
    "pdfs",       # tidal influence — excluded from both networks, 2026-05-24
})

# RAF Valley, Anglesey — site latitude for Thornthwaite day-length correction.
# Imported from utils.config (RAF_VALLEY_LAT_DEG = 53.25).


def thornthwaite_pet_m(t_mean: pd.Series, lat_deg: float = RAF_VALLEY_LAT_DEG) -> pd.Series:
    """
    Compute monthly PET in metres using the Thornthwaite (1948) method with the
    Thornthwaite & Mather (1955) day-length and month-length correction factor.

    The formula is:
        PET_unadj (mm) = 16 * (10 * T / I) ^ alpha     [for 0 < T < 26.5 °C]
        alpha = 6.75e-7 * I^3 - 7.71e-5 * I^2 + 1.792e-2 * I + 0.49239
        I = sum of monthly heat-index contributions i = (T/5)^1.514 over 12 months
        K = (N/12) * (NDM/30)   [day-length correction; N = mean photoperiod hours]
        PET_adj (m) = PET_unadj * K / 1000

    For T <= 0, PET = 0. For T >= 26.5, the Camargo et al. high-temperature
    linearisation is applied: PET = -415.85 + 32.24*T - 0.43*T^2.

    Parameters
    ----------
    t_mean  : pd.Series of mean monthly temperature (°C) with DatetimeIndex
              at month-start timestamps. NaN months are handled gracefully.
    lat_deg : site latitude in decimal degrees north (default 53.25, RAF Valley).

    Returns
    -------
    pd.Series of PET in metres per month, same index as t_mean.
    NaN is preserved where t_mean is NaN.

    References
    ----------
    Thornthwaite, C.W. (1948). An approach toward a rational classification of
        climate. Geographical Review, 38(1), 55-94.
    Thornthwaite, C.W. & Mather, J.R. (1955). The water balance. Publications in
        Climatology, 8(1), 1-104.
    """
    temps_pos = t_mean.clip(lower=0).fillna(0)

    # Annual heat index I: sum of 12 monthly contributions within each calendar year.
    # Months with missing temperature contribute zero to I (conservative).
    i_monthly = (temps_pos / 5) ** 1.514
    i_annual  = i_monthly.groupby(t_mean.index.year).sum()
    I = pd.Series(t_mean.index.year, index=t_mean.index).map(i_annual)
    I = I.replace(0, np.nan)  # guard against all-zero temperature years

    alpha = (6.75e-7 * I**3) - (7.71e-5 * I**2) + (1.792e-2 * I) + 0.49239

    # Unadjusted PET (mm, standard 30-day 12-hour basis)
    pet_unadj = np.where(
        temps_pos <= 0, 0.0,
        np.where(
            temps_pos < 26.5,
            16.0 * (10.0 * temps_pos / I) ** alpha,
            -415.85 + 32.24 * temps_pos - 0.43 * temps_pos ** 2,
        ),
    )

    # Day-length correction factor K = (N/12) * (NDM/30)
    lat_rad = np.radians(lat_deg)
    mid_doy = np.array([15, 46, 75, 106, 136, 167, 197, 228, 259, 289, 320, 350])
    decl    = np.radians(23.45 * np.sin(np.radians(360 * (mid_doy - 80) / 365)))
    cos_ha  = -np.tan(lat_rad) * np.tan(decl[t_mean.index.month - 1])
    N       = (24 / np.pi) * np.arccos(np.clip(cos_ha, -1, 1))
    K       = (N / 12) * (t_mean.index.days_in_month / 30)

    pet_m = pd.Series(pet_unadj * K / 1000, index=t_mean.index, name="PET")

    # Restore NaN where original temperature was missing
    pet_m[t_mean.isna()] = np.nan

    return pet_m


def _build_observation_states(wells_clean, provenance):
    """Build the observation-state layer and write the derived CSVs.

    REFRESH from the raw .ods when present (scoped to the pipeline wells and
    months, with provenance protecting genuine measurements); otherwise fall
    back to the committed state CSV. Returns the wide state grid, or None.
    """
    pipeline_wells = set(c.lower() for c in wells_clean.columns)
    pipeline_months = wells_clean.index

    if DATA_WELL_RECORDS_ODS.exists():
        comment_long, _ = parse_comment_states(DATA_WELL_RECORDS_ODS)
        scoped = comment_long[
            comment_long["well"].str.lower().isin(pipeline_wells)
            & comment_long["month"].isin(pipeline_months)
        ].copy()
        states, conflicts = assemble_observation_states(
            wells_clean, scoped, provenance=provenance
        )
        states.to_csv(INT_OBSERVATION_STATES)
        depths = scoped.dropna(subset=["dry_depth_m"])[
            ["well", "month", "dry_depth_m"]
        ]
        depths.to_csv(INT_DRY_DEPTHS, index=False)
        conflicts.to_csv(INT_OBS_STATE_CONFLICTS, index=False)
        saved(f"observation states -> {INT_OBSERVATION_STATES.name} "
              f"({states.shape[0]}x{states.shape[1]}); "
              f"{INT_DRY_DEPTHS.name} ({len(depths)} dry-at-depth cells)")
        if len(conflicts):
            warn(f"{len(conflicts)} comment(s) collided with a genuine "
                 f"measurement (kept the reading) -> {INT_OBS_STATE_CONFLICTS.name}")
        return states
    if INT_OBSERVATION_STATES.exists():
        note(f"{DATA_WELL_RECORDS_ODS.name} absent; using committed "
             f"{INT_OBSERVATION_STATES.name} for the coverage figure")
        return pd.read_csv(INT_OBSERVATION_STATES, index_col=0, parse_dates=True)
    note(f"observation-state layer skipped: neither "
         f"{DATA_WELL_RECORDS_ODS.name} nor {INT_OBSERVATION_STATES.name} present")
    return None


def _excluded_presence(months, names):
    """Measured-month presence (bool) for the excluded study-area dipwells, read
    straight from the raw measured sheet — these wells are deliberately not in
    the cleaned pipeline data, so only their raw presence is shown. Field-
    convention bucketing: a reading on day > 15 belongs to that month, else to
    the previous month."""
    import datetime
    out = pd.DataFrame(False, index=months, columns=[n.lower() for n in names])
    if not DATA_WELL_RECORDS_ODS.exists():
        return out
    g = pd.read_excel(DATA_WELL_RECORDS_ODS, sheet_name="measured",
                      engine="odf", header=None)
    date_cells = {c: g.iat[1, c] for c in range(g.shape[1])
                  if isinstance(g.iat[1, c], (pd.Timestamp, datetime.datetime))}
    want = {n.lower() for n in names}
    mset = set(months)

    def bucket(d):
        d = pd.Timestamp(d)
        if d.day > 15:
            return pd.Timestamp(d.year, d.month, 1)
        b = d.replace(day=1) - pd.offsets.MonthBegin(1)
        return pd.Timestamp(b.year, b.month, 1)

    for r in range(g.shape[0]):
        wid = g.iat[r, 10] if g.shape[1] > 10 else None
        if not (isinstance(wid, str) and wid.strip().lower() in want):
            continue
        nm = wid.strip().lower()
        for c, d in date_cells.items():
            v = g.iat[r, c]
            if isinstance(v, (int, float)) and pd.notna(v):
                m = bucket(d)
                if m in mset:
                    out.at[m, nm] = True
    return out


def _render_coverage_figure(wells_scope, states):
    """Render the data-coverage figure across all three tiers: 66 reference and
    22 extended wells (cluster-coloured; reference from 03_master_data, extended
    from the Pearson-affinity audit, tagged "(ext)"), then a grey presence-only
    block of the excluded study-area dipwells and the Llyn Rhos-Ddu lake gauge,
    each annotated with its exclusion reason. Off-system points (NF series,
    Aberffraw, pool markers) are not shown. Greyscale-safe via config."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import matplotlib.dates as mdates
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    from utils.clearfell_common import SCRAPING_DATE, INTERVENTION_DATE

    obs_face = get_obs_state_colours()
    obs_hatch = get_obs_state_hatches()
    GREY = mcolors.to_rgba("#9e9e9e")
    PRESENT = {"measured", "interpolated", "dry_recorded", "dry_inferred", "flooded"}

    # Canonical record start is April 2005; drop the lone March 2005 cell.
    states = states.loc[pd.Timestamp(RECORD_START_DISPLAY):]
    months = states.index
    colmap = {c.lower(): c for c in states.columns}

    # ── tier assembly ────────────────────────────────────────────────────────
    master = pd.read_csv(OUT_DIR / "03_master_data.csv")
    ref_cluster = {str(r["Name_Original"]).lower(): int(r["Cluster"])
                   for _, r in master.iterrows()}
    audit = pd.read_csv(INT_PEAR_AUDIT_SITEWIDE)
    ext_cluster = {str(w).lower(): int(c) for w, c
                   in zip(audit["Well_Normalised"], audit["Best_Match_Cluster"])}

    def first(col):
        return (wells_scope[col].dropna().index.min()
                if col in wells_scope.columns and wells_scope[col].notna().any()
                else pd.NaT)

    rows = []   # (kind, key, cluster, label)
    for cl in range(1, 6):
        refs = sorted([colmap[w] for w in ref_cluster
                       if ref_cluster[w] == cl and w in colmap], key=first)
        for col in refs:
            rows.append(("ref", col, cl, col))
        exts = sorted([colmap[w] for w in ext_cluster
                       if ext_cluster.get(w) == cl and w in colmap
                       and w not in ref_cluster], key=first)
        for col in exts:
            rows.append(("ext", col, cl, f"{col} (ext)"))

    presence = _excluded_presence(months, list(EXCLUDED_STUDY_AREA_WELLS))
    for w, reason in EXCLUDED_STUDY_AREA_WELLS.items():
        rows.append(("excl", w, None, f"{w} \u00b7 {reason}"))
    lake_col = next((colmap[w] for w in colmap
                     if "llyn" in w or "rhos" in w), None)
    if lake_col is not None:
        rows.append(("lake", lake_col, None,
                     "Llyn Rhos-Ddu \u00b7 non-network"))

    # ── raster ───────────────────────────────────────────────────────────────
    n = len(rows)
    img = np.ones((n, len(months), 4))
    hatch_cells = []
    for i, (kind, key, cl, _) in enumerate(rows):
        if kind in ("ref", "ext"):
            face = mcolors.to_rgba(get_cluster_colour(cl))
            interp = obs_face.get("interpolated")     # solid colour in colour mode
            light = tuple(0.40 * c + 0.60 for c in face[:3]) + (1.0,)  # BW fallback tint
            for j, st in enumerate(states[key].values):
                if st == "measured":
                    img[i, j, :] = face
                elif st == "interpolated":
                    if interp is not None:
                        img[i, j, :] = mcolors.to_rgba(interp)
                    else:
                        img[i, j, :] = light
                        hatch_cells.append((i, j, obs_hatch.get("interpolated", "..")))
                else:
                    img[i, j, :] = mcolors.to_rgba(obs_face.get(st, "#FFFFFF"))
                    if st in obs_hatch:
                        hatch_cells.append((i, j, obs_hatch[st]))
        elif kind == "lake":
            for j, st in enumerate(states[key].values):
                if st in PRESENT:
                    img[i, j, :] = GREY
        elif kind == "excl":
            pres = presence[key].values
            for j, p in enumerate(pres):
                if p:
                    img[i, j, :] = GREY

    # ── render as two plates (reference / extended+excluded) for legibility ──
    legend = [
        Patch(fc="#777777", label="measured (cluster colour)"),
        (Patch(fc=obs_face["interpolated"], label="interpolated (1-month bridge)")
         if "interpolated" in obs_face else
         Patch(fc="#c9c9c9", hatch="..", ec="#404040",
               label="interpolated (1-month bridge)")),
        Patch(fc=obs_face["dry_recorded"], hatch=obs_hatch.get("dry_recorded"),
              ec="#404040", label="dry \u2014 recorded"),
        Patch(fc=obs_face["dry_inferred"], label="dry \u2014 inferred"),
        Patch(fc=obs_face["flooded"], hatch=obs_hatch.get("flooded"),
              ec="#404040", label="flooded"),
        Patch(fc=obs_face["not_found"], ec="#404040", hatch=obs_hatch["not_found"],
              label="not found / lost"),
        Patch(fc=obs_face["inaccessible"], ec="#404040",
              hatch=obs_hatch["inaccessible"], label="inaccessible (buried/blocked)"),
        Patch(fc=GREY, label="excluded / lake gauge (presence only)"),
        Patch(fc="white", ec="#cccccc", label="not read / outside record"),
        Line2D([0], [0], color="black", ls="--", lw=1.0,
               label="intervention dates (2015 scrape, 2017 clearfell)"),
    ]
    x0, x1 = mdates.date2num(months[0]), mdates.date2num(months[-1])
    dx = (x1 - x0) / (len(months) - 1)

    def _plate(sel, out_path, title):
        m = len(sel)
        pos = {orig: k for k, orig in enumerate(sel)}
        sub_img = img[sel, :, :]
        sub_rows = [rows[i] for i in sel]
        sub_hatch = [(pos[i], j, h) for (i, j, h) in hatch_cells if i in pos]
        plot_h = m * 0.135
        top_pad, bot_pad, fig_w = 0.75, 1.05, 8.0
        fig_h = plot_h + top_pad + bot_pad
        left, right = 0.28, 0.80          # fixed margins -> identical x-axis on both plates
        fig = plt.figure(figsize=(fig_w, fig_h))
        ax = fig.add_axes([left, bot_pad / fig_h, right - left, plot_h / fig_h])
        ax.imshow(sub_img, aspect="auto", interpolation="none", extent=[x0, x1, m, 0])
        ax.xaxis_date()
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelsize=7)
        for (i, j, hatch) in sub_hatch:
            ax.add_patch(plt.Rectangle((mdates.date2num(months[j]) - dx / 2, i), dx, 1,
                                       fill=False, hatch=hatch, edgecolor="#404040",
                                       linewidth=0.0))
        kinds = [k for (k, _, _, _) in sub_rows]
        clusters = [cl for (_, _, cl, _) in sub_rows]
        excl_top = next((i for i, k in enumerate(kinds) if k in ("excl", "lake")), m)
        cl_bounds, prev = [], None
        for i in range(excl_top):
            if clusters[i] != prev:
                cl_bounds.append((i, clusters[i])); prev = clusters[i]
        for start, _ in cl_bounds:
            if start > 0:
                ax.axhline(start, color="black", lw=0.8)
        if excl_top < m:
            ax.axhline(excl_top, color="black", lw=1.4)
        for k, (start, cl) in enumerate(cl_bounds):
            end = cl_bounds[k + 1][0] if k + 1 < len(cl_bounds) else excl_top
            ax.text(1.01, 1 - (start + end) / 2 / m, CLUSTER_LABELS[cl],
                    transform=ax.transAxes, va="center", ha="left",
                    fontsize=8, color=get_cluster_colour(cl), fontweight="bold")
        if excl_top < m:
            ax.text(1.01, 1 - (excl_top + m) / 2 / m, "Excluded /\nnon-network",
                    transform=ax.transAxes, va="center", ha="left",
                    fontsize=8, color="#555555", fontweight="bold")
        ax.set_yticks(np.arange(m) + 0.5)
        ax.set_yticklabels([lbl for (_, _, _, lbl) in sub_rows], fontsize=8)
        ax.set_ylim(m, 0)
        for d in (pd.Timestamp(SCRAPING_DATE), pd.Timestamp(INTERVENTION_DATE)):
            ax.axvline(d, color="black", ls="--", lw=1.0, alpha=0.7)
        fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.015),
                   ncol=3, fontsize=7, frameon=False)
        ax.set_title(title, fontsize=10)
        ax.margins(x=0)
        render_figure(fig, out_path)
        plt.close(fig)
        saved(f"coverage figure -> {out_path.name}")

    ref_sel = [i for i, (k, _, _, _) in enumerate(rows) if k == "ref"]
    ext_sel = [i for i, (k, _, _, _) in enumerate(rows) if k in ("ext", "excl", "lake")]
    span = f"{months[0]:%b %Y} \u2013 {months[-1]:%b %Y}"
    _plate(ref_sel, INT_COVERAGE_FIGURE_REF,
           "Data coverage: monthly observation state \u2014 reference network\n"
           f"{len(ref_sel)} reference wells, {span}  (Source: 01_data_prep.py)")
    n_ext_only = sum(1 for i in ext_sel if rows[i][0] == "ext")
    _plate(ext_sel, INT_COVERAGE_FIGURE_EXT,
           "Data coverage: monthly observation state \u2014 extended network "
           "and excluded study-area markers\n"
           f"{n_ext_only} extended wells plus excluded dipwells and lake gauge, "
           f"{span}  (Source: 01_data_prep.py)")


if __name__ == "__main__":
    banner("01", "Data Preparation", version="1.5.0")
    make_all_dirs()
    print("Starting Data Preparation Pipeline...")

    locs_raw  = pd.read_csv(DATA_LOCATIONS_RAW)
    wells_raw = pd.read_csv(DATA_WELLS_RAW, header=1)

    # Sanity check
    print("\n" + "=" * 40)
    print("  DATA SANITY CHECK: Metadata vs. Time-Series")
    print("=" * 40)
    locs_raw.columns   = locs_raw.columns.str.strip()
    loc_names          = set(locs_raw["Name"].apply(normalize_well_name))
    well_names_in_data = set(wells_raw.iloc[:, 0].dropna().apply(normalize_well_name))
    missing_in_data    = loc_names - well_names_in_data
    missing_in_locs    = well_names_in_data - loc_names
    if not missing_in_data and not missing_in_locs:
        print("  ✅ SUCCESS: All wells match perfectly between files.")
    else:
        if missing_in_data:
            warn(f"{len(missing_in_data)} wells have locations but no time-series data.")
        if missing_in_locs:
            warn(f"{len(missing_in_locs)} wells have time-series but no location metadata.")
    print("=" * 40 + "\n")

    # Locations
    locs_raw["Match_ID"] = locs_raw["Name"].apply(normalize_well_name)
    locs_raw.dropna(subset=["E", "N"]).to_csv(INT_LOCATIONS, index=False)

    # Climate
    climate = pd.read_csv(DATA_CLIMATE_RAW)
    climate["Date"] = climate["Unnamed: 0"].apply(parse_met_date)
    climate = climate.set_index("Date")
    climate["P_m"] = (
        pd.to_numeric(climate["Rain (mm)"].replace("---", "0"), errors="coerce")
        .fillna(0) / 1000
    )
    t_max_col = "Max Temp ©" if "Max Temp ©" in climate.columns else "Max Temp (C)"
    t_mean = (
        pd.to_numeric(climate[t_max_col], errors="coerce")
        + pd.to_numeric(climate["Min Temp (C)"], errors="coerce")
    ) / 2
    climate["PET"] = thornthwaite_pet_m(t_mean)
    climate[["P_m", "PET"]].to_csv(INT_CLIMATE)

    # Wells
    wells = wells_raw.set_index(wells_raw.columns[0]).transpose()

    # ── Month bucketing: assign each reading to the month it represents ────
    # Fieldwork convention: a visit on day 1–15 of month M is the END-of-
    # previous-month reading (represents month M−1). A visit on day 16–31
    # is a within-month reading (represents month M).
    #
    # Example: 01/09/2011 → represents August 2011 → bucket to 2011-08.
    #          31/08/2011 → represents August 2011 → bucket to 2011-08.
    #
    # This ensures the monthly well index aligns with calendar months in
    # the climate record without requiring a compensating lag-1 shift in
    # downstream regressions. HEADLINE_LAG in config.py is set to 0.
    d = pd.to_datetime(wells.index, dayfirst=True, errors="coerce")
    prev_month = (d.to_period("M") - 1).to_timestamp()
    this_month = d.to_period("M").to_timestamp()
    wells.index = np.where(d.day <= 15, prev_month, this_month)
    wells = wells.apply(pd.to_numeric, errors="coerce").groupby(level=0).mean()
    if "NW8" in wells.columns and "NW8b" in wells.columns:
        wells["NW8"] = wells["NW8b"].combine_first(wells["NW8"])
        wells.drop(columns=["NW8b"], inplace=True)
    # clean_well_series masks readings deeper than MIN_PHYSICAL_DEPTH = -4.0 m
    # (a safety floor; the deepest plausible water table at Newborough is ~3 m
    # below ground). Positive readings are RETAINED — the slacks regularly
    # flood above pipe top and those readings are real flood-month
    # observations that the SSM and flood-threshold work depend on.
    #
    # Single-month gaps (one missed visit between two measurements) are
    # bridged by linear interpolation; multi-month gaps stay NaN. See
    # utils/data_utils.py for the history of both the depth-floor and the
    # interpolation-limit conventions (the limit was tightened from 3 to 1
    # in the 2026-05-19 Defect E fix). Per-cell provenance is captured in
    # the parallel `provenance` DataFrame and written to
    # INT_WELLS_PROVENANCE.
    provenance = pd.DataFrame(index=wells.index, columns=wells.columns, dtype=object)
    for col in wells.columns:
        cleaned_col, prov_col = clean_well_series(wells[col], return_provenance=True)
        wells[col] = cleaned_col
        provenance[col] = prov_col

    wells_clean = wells.dropna(axis=1, thresh=MIN_MONTHS_THRESH)
    wells_clean.to_csv(INT_WELLS_CLEAN)

    # Write the provenance file restricted to the same column set as the
    # cleaned wells file so downstream consumers can index it identically.
    provenance[wells_clean.columns].to_csv(INT_WELLS_PROVENANCE)

    # Network partition (reference / extended) is computed here — BEFORE the
    # observation-state layer — because the coverage figure must cover the full
    # classified network (66 reference + 22 extended), not just the reference-
    # scoped wells_clean. The extended wells live in `wells` with full
    # provenance; they are only dropped from wells_clean by the MIN_MONTHS
    # threshold, which is a reference-network criterion, not an exclusion.
    reference_wells, extended_wells = [], []
    demoted_wells = []   # wells that meet auto-criteria but are not whitelisted
    blacklisted_wells = []  # wells excluded from both networks
    for col in wells.columns:
        series = wells[col].dropna()
        if series.empty:
            continue
        col_norm = normalize_well_name(col)
        if col_norm in EXTENDED_NETWORK_BLACKLIST:
            blacklisted_wells.append(col)
            continue
        meets_reference_criteria = (
            len(series) >= MIN_MONTHS_THRESH
            and series.index.max() >= RECENCY_DATE
        )
        if meets_reference_criteria:
            if REFERENCE_NETWORK_WHITELIST is None or col_norm in REFERENCE_NETWORK_WHITELIST:
                reference_wells.append(col)
            else:
                demoted_wells.append(col)
                if len(series) >= MIN_EXTENDED_MONTHS:
                    extended_wells.append(col)
        elif len(series) >= MIN_EXTENDED_MONTHS:
            extended_wells.append(col)

    wells[reference_wells].to_csv(INT_WELLS_REFERENCE)
    wells[extended_wells].to_csv(INT_WELLS_EXTENDED)

    print(f"Complete. Retained {len(wells_clean.columns)} wells.")
    step(f"Reference: {len(reference_wells)} wells")
    step(f"Extended:  {len(extended_wells)} wells")
    if demoted_wells:
        print(f" -> Demoted to extended (not on reference-network whitelist): "
              f"{len(demoted_wells)} wells  "
              f"[{', '.join(sorted(str(w) for w in demoted_wells))}]")
    if blacklisted_wells:
        print(f" -> Excluded from both networks (blacklist): "
              f"{len(blacklisted_wells)} wells  "
              f"[{', '.join(sorted(str(w) for w in blacklisted_wells))}]")

    # ── Observation-state layer + coverage figure (v1.5.0) ───────────────────
    # Recover the field-comment reasons for absent/special readings (dry,
    # flooded, not-found, inaccessible) from the raw .ods, and build states over
    # the full CLASSIFIED network (reference + extended) plus the Llyn Rhos-Ddu
    # lake gauge, so the coverage figure shows all 88 classified wells, not just
    # the reference-scoped wells_clean. The figure renders if cluster
    # assignments exist (03_master_data.csv is produced downstream, so the figure
    # is deferred on a cold first pass). Purely additive; never breaks data prep.
    lake_cols = [c for c in wells.columns
                 if "llyn" in str(c).lower() or "rhos" in str(c).lower()]
    fig_scope = list(dict.fromkeys(reference_wells + extended_wells + lake_cols))
    try:
        obs_states = _build_observation_states(wells[fig_scope], provenance[fig_scope])
        if obs_states is not None and (OUT_DIR / "03_master_data.csv").exists():
            _render_coverage_figure(wells[fig_scope], obs_states)
        elif obs_states is not None:
            note("coverage figure deferred: 03_master_data.csv not yet present "
                 "(clusters assigned downstream); re-run Script 01 after a full "
                 "pipeline pass to render 01_coverage_states.png")
    except Exception as exc:  # observation-state layer must never break data prep
        warn(f"observation-state layer / coverage figure skipped: {exc}")


    # ------------------------------------------------------------------ #
    #  maOD CONVERSION                                                    #
    #  Convert depth-below-pipe-top (negative convention) to water table  #
    #  elevation in metres above Ordnance Datum (maOD).                  #
    #                                                                     #
    #  Formula:  maOD = Pipe_Top_Elev + raw_depth                        #
    #                                                                     #
    #  Raw depth is stored as a negative value (e.g. −1.5 m means the    #
    #  water table is 1.5 m below pipe top). Adding it to the pipe-top   #
    #  elevation therefore subtracts the depth, giving the correct        #
    #  upward-positive maOD value.                                        #
    #                                                                     #
    #  Pipe_Top_Elev is used directly (not reconstructed from            #
    #  DGPS_Ground_Elev + Upstand_m) because the two do not agree for    #
    #  70 of 97 wells — Pipe_Top_Elev is the independently measured       #
    #  value and is the correct reference datum for field readings.       #
    #                                                                     #
    #  Sign check: summer maOD < winter maOD (water table deeper in       #
    #  summer). Verified against nw1, ceh2, nw5, ceh14, d15.             #
    # ------------------------------------------------------------------ #
    print("\n -> Converting depth series to maOD...")
    if _WELL_ELEV_FILE.exists():
        elev_raw = pd.read_csv(_WELL_ELEV_FILE)
        elev_raw.columns = [c.strip() for c in elev_raw.columns]
        elev_raw["name_norm"] = (
            elev_raw["Name"].astype(str).str.strip()
            .str.lower().str.replace(" ", "").str.replace("_", "")
        )
        pipe_top_map = (
            elev_raw.dropna(subset=["Pipe_Top_Elev"])
            .set_index("name_norm")["Pipe_Top_Elev"]
            .to_dict()
        )
        maod_cols = {}
        n_converted = 0
        n_no_elev   = 0
        for col in wells_clean.columns:
            col_norm = normalize_well_name(col)
            pipe_top = pipe_top_map.get(col_norm)
            if pipe_top is not None:
                # raw depth is negative convention: maOD = Pipe_Top + depth
                maod_cols[col] = wells_clean[col] + pipe_top
                n_converted += 1
            else:
                n_no_elev += 1
        if maod_cols:
            wells_maod = pd.DataFrame(maod_cols, index=wells_clean.index)
            wells_maod.to_csv(INT_WELLS_CLEAN_MAOD)
            print(f"    Converted {n_converted} wells to maOD")
            if n_no_elev:
                warn(f"{n_no_elev} wells have no elevation data and are excluded from maOD file")
            saved(f"{INT_WELLS_CLEAN_MAOD.name}")
        else:
            warn("No wells could be converted to maOD — check elevation file contents")
    else:
        warn(f"Elevation file not found: {_WELL_ELEV_FILE}")
        print(f"    maOD file not produced — script 19 will fail without it")

    # ------------------------------------------------------------------ #
    #  ELEVATION LOOKUP EXPORT                                            #
    #  Exports upstand heights for use by script 03 centroid correction.  #
    #  Script 03 applies depth - upstand before averaging into centroids  #
    #  so all wells share a common ground-surface datum.                  #
    # ------------------------------------------------------------------ #
    print("\n -> Exporting well elevation lookup...")

    if _WELL_ELEV_FILE.exists():
        elev_df = pd.read_csv(_WELL_ELEV_FILE)
        elev_df.columns = [c.strip() for c in elev_df.columns]
        elev_df["Name_norm"] = (
            elev_df["Name"].astype(str).str.strip()
            .str.lower().str.replace(" ", "").str.replace("_", "")
        )
        elev_df.to_csv(INT_WELL_ELEVATIONS, index=False)
        print(f"    Saved elevation lookup: {INT_WELL_ELEVATIONS.name}")
    else:
        warn(f"Elevation file not found: {_WELL_ELEV_FILE}")
        print(f"    Upstand correction in script 03 will be skipped.")

    # ------------------------------------------------------------------ #
    #  PIPELINE SCENARIO PARAMETERS                                       #
    #  Writes the consolidated parameter file used by all downstream      #
    #  scenario scripts (09b, 09d, 19, 21). On re-runs, picks up real    #
    #  values from existing upstream outputs (03, 10e, 17); on first      #
    #  run, uses defaults with a flag.                                    #
    # ------------------------------------------------------------------ #
    print("\n -> Writing pipeline scenario parameters...")
    from utils.pipeline_params import write_initial_params
    write_initial_params(wells_clean, climate)

    # ------------------------------------------------------------------ #
    #  Seed site-wide observations CSV (long-format registry of single-  #
    #  value pipeline-produced observations that don't fit the per-      #
    #  cluster schema of pipeline_scenario_params.csv).  Defaults are    #
    #  written here; producer scripts (09a, 16, ...) overwrite their     #
    #  rows downstream.                                                  #
    # ------------------------------------------------------------------ #
    print("\n -> Writing pipeline site observations...")
    from utils.site_observations import write_initial_site_observations
    write_initial_site_observations()

    print("\n=== Script 01 complete ===")
