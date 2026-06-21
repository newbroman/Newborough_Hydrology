#!/usr/bin/env python3
"""
Newborough Water Level Monthly Report Generator
================================================
Automates:
1. Reading well records from the ODS spreadsheet (Absolute Level sheet)
2. Computing water level differences (month-on-month, year-on-year, since summer low)
3. Generating interpolated difference maps with DEM hillshade base
4. Writing a Met summary from RAF Valley data + Weather Underground local station
5. Producing a full monthly report (Markdown)

Usage (simplest — just the month):
    python newborough_report.py 2026-02

Full options:
    python newborough_report.py 2026-02 \\
        --wells Newborough_well_recordsA.ods \\
        --valley valleydata.txt \\
        --dem newborough_dem.tif \\
        --kml_dir ./kml \\
        --wu_station ILLANF24 \\
        --output_dir ./output
"""

import argparse
import sys
import os
import warnings
import re
import json
import calendar
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


# ─── Configuration / Defaults ────────────────────────────────────────────────

# Met Office data URL — stable public endpoint
VALLEY_DATA_URL = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/valleydata.txt"

# Paths — override with CLI args. Set these to match your local file layout.
DEFAULT_WELLS = 'data/Newborough_well_recordsA.ods'
DEFAULT_VALLEY = 'data/valleydata.txt'
DEFAULT_DEM = 'data/newborough_dem.tif'
DEFAULT_COORDS_CSV = 'data/Well_locations_height.csv'
DEFAULT_KML_DIR = 'kml'
DEFAULT_WU_STATION = 'ILLANF24'
DEFAULT_OUTPUT_DIR = 'output'

# Map extent for interpolation (Newborough Warren area, OSGB)
MAP_EXTENT = {
    'e_min': 240300, 'e_max': 243700,
    'n_min': 362500, 'n_max': 364900,
    'resolution': 50  # metres per pixel for interpolation grid
}

MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

# KML layer styling
KML_STYLES = {
    'site_boundary':     {'color': '#333333', 'linewidth': 1.5, 'linestyle': '-',  'fill': False},
    'streams':           {'color': '#1E90FF', 'linewidth': 1.0, 'linestyle': '-',  'fill': False},
    'clearfell':         {'color': '#8B4513', 'linewidth': 0.8, 'linestyle': '--', 'fill': True, 'facecolor': '#8B451320'},
    'broadleaf_restock': {'color': '#228B22', 'linewidth': 0.8, 'linestyle': '--', 'fill': True, 'facecolor': '#228B2220'},
    'Features':          {'color': '#FF6600', 'linewidth': 0.8, 'linestyle': '-',  'fill': False},
}

# WU reliability thresholds
WU_MAX_MISSING_DAYS = 5          # flag if more than 5 days missing
WU_VALLEY_RATIO_THRESHOLD = 3.0  # flag if WU/Valley ratio > 3 or < 1/3


# ─── Data Loading ────────────────────────────────────────────────────────────

def download_valley_data(filepath):
    """
    Download the latest RAF Valley climate data from the Met Office.
    Overwrites the local file if successful.
    """
    print(f"   Downloading RAF Valley data from Met Office...")
    try:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        req = urllib.request.Request(VALLEY_DATA_URL, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(filepath, 'wb') as f:
            f.write(data)
        lines = data.decode('utf-8', errors='replace').splitlines()
        data_lines = [l for l in lines if re.match(r'^\s*\d{4}\s+\d+', l)]
        last = data_lines[-1].strip().split() if data_lines else []
        last_date = f"{last[0]}-{int(last[1]):02d}" if len(last) >= 2 else "?"
        print(f"   Downloaded OK — {len(data_lines)} months, latest: {last_date}")
        return True
    except Exception as e:
        print(f"   Warning: Could not download Valley data: {e}")
        return False


def load_valley_data(filepath):
    """Parse the RAF Valley Met Office data file."""
    records = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            match = re.match(
                r'^\s*(\d{4})\s+(\d+)\s+([\d.+-]+)\*?\s+([\d.+-]+)\*?\s+([\d.+-]+)\*?\s+'
                r'([\d.\-]+|---)\*?\s+([\d.\-]+|---)',
                line
            )
            if match:
                yyyy = int(match.group(1))
                mm = int(match.group(2))
                tmax = float(match.group(3))
                tmin = float(match.group(4))
                af = float(match.group(5))
                rain_str = match.group(6).replace('---', '')
                sun_str = match.group(7).replace('#', '').replace('---', '').strip()
                rain = float(rain_str) if rain_str else None
                sun = float(sun_str) if sun_str else None
                records.append({
                    'year': yyyy, 'month': mm,
                    'tmax': tmax, 'tmin': tmin,
                    'af': af, 'rain': rain, 'sun': sun
                })
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    return df


def load_well_records(filepath):
    """
    Load well records from the Newborough ODS file.
    Uses the 'Absolute Level' sheet (water table elevation in metres AOD).
    Returns:
        wells: list of dicts with well_id, well_name, levels
        dates: list of measurement dates
        df_meas: measured sheet DataFrame
    """
    xls = pd.ExcelFile(filepath, engine='odf')

    df = pd.read_excel(xls, sheet_name='Absolute Level', header=None)

    # Row 1 has dates (columns 2 onwards)
    dates_row = df.iloc[1, 2:]
    dates = []
    for d in dates_row:
        if pd.notna(d):
            try:
                dates.append(pd.to_datetime(d))
            except Exception:
                dates.append(None)
        else:
            dates.append(None)

    # Wells start at row 2
    wells = []
    for i in range(2, len(df)):
        well_id = df.iloc[i, 0]
        well_name = df.iloc[i, 1]
        if pd.isna(well_name):
            continue
        well_name = str(well_name).strip()
        if not well_name:
            continue
        levels = df.iloc[i, 2:].values
        wells.append({
            'well_id': str(well_id).strip() if pd.notna(well_id) else '',
            'well_name': well_name,
            'levels': levels
        })

    df_meas = pd.read_excel(xls, sheet_name='measured', header=None)
    return wells, dates, df_meas


def load_well_coordinates(diff_creator_path=None, csv_path=None):
    """
    Load well coordinates.
    Tries: 1) difference creator ODS, 2) Well_locations_height.csv
    Returns dict: well_name -> (E, N)
    """
    coords = {}

    # Try ODS first
    if diff_creator_path and os.path.exists(diff_creator_path):
        df = pd.read_excel(diff_creator_path, engine='odf', header=None)
        for i in range(2, len(df)):
            name = df.iloc[i, 0]
            e = df.iloc[i, 1]
            n = df.iloc[i, 2]
            if pd.notna(name) and pd.notna(e) and pd.notna(n):
                try:
                    coords[str(name).strip()] = (float(e), float(n))
                except (ValueError, TypeError):
                    pass

    # Fallback/supplement from CSV
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            name = str(row['Name']).strip()
            if name and name not in coords:
                try:
                    coords[name] = (float(row['E']), float(row['N']))
                except (ValueError, TypeError):
                    pass
    
    # Auto-discover CSV in same directory as wells ODS
    if not coords:
        for candidate in ['Well_locations_height.csv', 'Well__info.csv']:
            for search_dir in ['.', 'data', os.path.dirname(diff_creator_path or '')]:
                p = os.path.join(search_dir, candidate)
                if os.path.exists(p):
                    df = pd.read_csv(p)
                    name_col = 'Name' if 'Name' in df.columns else 'Nane' if 'Nane' in df.columns else None
                    if name_col:
                        for _, row in df.iterrows():
                            name = str(row[name_col]).strip()
                            if name and pd.notna(row.get('E')) and pd.notna(row.get('N')):
                                try:
                                    coords[name] = (float(row['E']), float(row['N']))
                                except (ValueError, TypeError):
                                    pass
                    if coords:
                        break
            if coords:
                break

    return coords


# ─── KML Features (geopandas, matching map_utils.py) ─────────────────────────

def _safe_read_kml(path_obj):
    """Read a KML file, returning None and printing a warning on failure."""
    try:
        import geopandas as gpd
        import fiona
        fiona.drvsupport.supported_drivers['KML'] = 'rw'
        return gpd.read_file(str(path_obj))
    except Exception as exc:
        print(f"    [WARNING] Skipping {Path(path_obj).name}: KML unavailable ({exc})")
        return None


def add_kml_features(ax, kml_dir, include_streams=True):
    """
    Overlay site feature KML layers onto ax using geopandas.
    Matches the styling from map_utils.py exactly.
    Returns list of Line2D legend handles.
    """
    from matplotlib.lines import Line2D

    site_feature_handles = []
    kml_dir = Path(kml_dir)

    # ── Features.kml ──
    features_path = kml_dir / 'Features.kml'
    if features_path.exists():
        gdf_features = _safe_read_kml(features_path)
        if gdf_features is not None:
            gdf_features.set_crs(epsg=4326, inplace=True, allow_override=True)
            gdf_features = gdf_features.to_crs('EPSG:27700')
            feature_text = (
                gdf_features.get('Name', pd.Series('', index=gdf_features.index))
                .fillna('').astype(str)
            )
            lake_mask = feature_text.str.contains('lake|llyn|rhos', case=False, na=False)
            forest_mask = feature_text.str.contains(
                'forest|plantation|wood|boundary', case=False, na=False)
            broadleaf_mask = (
                feature_text.str.contains('broadleaf|restock', case=False, na=False) |
                gdf_features.get('description', pd.Series('', index=gdf_features.index))
                    .fillna('').astype(str)
                    .str.contains('broadleaf|restock', case=False, na=False)
            )

            # Other features first — dashed black
            gdf_features[~(lake_mask | forest_mask | broadleaf_mask)].plot(
                ax=ax, facecolor='none', edgecolor='black',
                linewidth=1.3, linestyle='--', zorder=2)
            # Forest boundary — solid purple
            gdf_features[forest_mask].plot(
                ax=ax, facecolor='none', edgecolor='purple',
                linewidth=2.2, zorder=2)
            # Lakes — filled dodgerblue
            gdf_features[lake_mask].plot(
                ax=ax, facecolor='dodgerblue', edgecolor='dodgerblue',
                linewidth=1.8, alpha=0.25, zorder=2)
            # Broadleaf restocking — dashed green
            if broadleaf_mask.any():
                gdf_features[broadleaf_mask].plot(
                    ax=ax, facecolor='none', edgecolor='#228B22',
                    linewidth=2.0, linestyle='--', zorder=2)
                site_feature_handles.append(
                    Line2D([0], [0], color='#228B22', linestyle='--',
                           linewidth=2.0, label='Broadleaf restocking block'))

            site_feature_handles.append(
                Line2D([0], [0], color='black', linestyle='--',
                       linewidth=1.6, label='Other Site Features'))
            site_feature_handles.append(
                Line2D([0], [0], color='purple', linestyle='-',
                       linewidth=2.2, label='Forest Boundary'))

    # ── broadleaf_restock.kml (separate file) ──
    bl_path = kml_dir / 'broadleaf_restock.kml'
    if bl_path.exists():
        gdf_bl = _safe_read_kml(bl_path)
        if gdf_bl is not None:
            gdf_bl.set_crs(epsg=4326, inplace=True, allow_override=True)
            gdf_bl = gdf_bl.to_crs('EPSG:27700')
            gdf_bl.plot(ax=ax, facecolor='none', edgecolor='#228B22',
                        linewidth=2.0, linestyle='--', zorder=2)

    # ── Streams ──
    if include_streams:
        streams_path = kml_dir / 'streams.kml'
        if streams_path.exists():
            gdf_streams = _safe_read_kml(streams_path)
            if gdf_streams is not None and not gdf_streams.empty:
                if gdf_streams.crs is None:
                    gdf_streams.set_crs(epsg=4326, inplace=True)
                gdf_streams.to_crs('EPSG:27700').plot(
                    ax=ax, facecolor='none', edgecolor='dodgerblue',
                    linewidth=1.8, zorder=2)
                site_feature_handles.append(
                    Line2D([0], [0], color='dodgerblue', linestyle='-',
                           linewidth=1.8, label='DEM-derived flow network and boundary'))

    # ── Clearfell ──
    cf_path = kml_dir / 'clearfell.kml'
    if cf_path.exists():
        gdf_cf = _safe_read_kml(cf_path)
        if gdf_cf is not None:
            if gdf_cf.crs is None:
                gdf_cf.set_crs(epsg=4326, inplace=True)
            gdf_cf.to_crs('EPSG:27700').plot(
                ax=ax, facecolor='none', edgecolor='darkorange',
                linewidth=2.2, linestyle='-.', zorder=2)
            site_feature_handles.append(
                Line2D([0], [0], color='darkorange', linestyle='-.',
                       linewidth=2.2, label='Felling Area'))

    # Deduplicate by label
    dedup = {}
    for handle in site_feature_handles:
        dedup[handle.get_label()] = handle
    return list(dedup.values())


# ─── DEM / Hillshade ─────────────────────────────────────────────────────────

def load_hillshade(dem_path, extent=MAP_EXTENT):
    """
    Load DEM and generate hillshade clipped to the map extent.
    Returns: hillshade array, plot extent [e_min, e_max, n_min, n_max]
    """
    try:
        import rasterio
        from matplotlib.colors import LightSource
    except ImportError:
        print("    Warning: rasterio not available, skipping hillshade")
        return None, None

    if not dem_path or not os.path.exists(dem_path):
        return None, None

    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        bounds = src.bounds
        res = src.res[0]

    ls = LightSource(azdeg=315, altdeg=35)
    hillshade = ls.hillshade(dem, dx=res, dy=res, vert_exag=3.0)

    # Clip to map extent
    col_min = max(0, int((extent['e_min'] - bounds.left) / res))
    col_max = min(hillshade.shape[1], int((extent['e_max'] - bounds.left) / res))
    row_min = max(0, int((bounds.top - extent['n_max']) / res))
    row_max = min(hillshade.shape[0], int((bounds.top - extent['n_min']) / res))

    hs_clip = hillshade[row_min:row_max, col_min:col_max]
    dem_clip = dem[row_min:row_max, col_min:col_max]
    plot_extent = [extent['e_min'], extent['e_max'], extent['n_min'], extent['n_max']]

    # Coordinate arrays for the clipped DEM (for ridge masking)
    dem_e_arr = np.arange(bounds.left + col_min * res, bounds.left + col_max * res, res)
    dem_n_arr = np.arange(bounds.top - row_min * res, bounds.top - row_max * res, -res)

    return hs_clip, plot_extent, dem_clip, dem_e_arr, dem_n_arr


# ─── Weather Underground Scraping ────────────────────────────────────────────

def fetch_wu_monthly(station_id, year, month):
    """
    Fetch monthly daily summary from Weather Underground PWS page.
    Parses the JSON embedded in <script id="app-root-state">.
    Returns: (result_dict, error_string)
    """
    days_in_month = calendar.monthrange(year, month)[1]
    url = (f"https://www.wunderground.com/dashboard/pws/{station_id}"
           f"/table/{year}-{month}-1/{year}-{month}-{days_in_month}/monthly")

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8')
    except Exception as e:
        return None, f"Failed to fetch WU page: {e}"

    # Extract embedded JSON
    m = re.search(
        r'<script id="app-root-state" type="application/json">(.*?)</script>', html
    )
    if not m:
        return None, "Could not find embedded JSON in WU page"

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        return None, f"Failed to parse WU JSON: {e}"

    # Find the key containing observations with imperial data
    observations = []
    for k, v in data.items():
        if not isinstance(v, dict):
            continue
        b = v.get('b')
        if not isinstance(b, dict):
            continue
        obs = b.get('observations', [])
        if (obs and isinstance(obs, list) and len(obs) > 0
                and isinstance(obs[0], dict) and 'imperial' in obs[0]):
            observations = obs
            break

    if not observations:
        return None, "No observations found in WU data"

    # Parse daily precipitation
    daily = []
    for obs in observations:
        precip_in = obs.get('imperial', {}).get('precipTotal')
        date_str = obs.get('obsTimeLocal', '')[:10]
        if precip_in is not None:
            daily.append({'date': date_str, 'precip_mm': precip_in * 25.4})
        else:
            daily.append({'date': date_str, 'precip_mm': None})

    days_with_data = len([d for d in daily if d['precip_mm'] is not None])
    total_mm = sum(d['precip_mm'] for d in daily if d['precip_mm'] is not None)

    # Check for suspicious single-day spikes (sensor malfunction)
    # A single day > 150mm in Anglesey is extremely unlikely
    spike_days = [d for d in daily if d['precip_mm'] is not None and d['precip_mm'] > 150]
    if spike_days:
        total_excl_spikes = sum(
            d['precip_mm'] for d in daily
            if d['precip_mm'] is not None and d['precip_mm'] <= 150
        )
        spike_dates = ', '.join(d['date'] for d in spike_days)
        spike_vals = ', '.join(str(round(d['precip_mm'])) + 'mm' for d in spike_days)
        spike_warning = (f"Suspect spike on {spike_dates} ({spike_vals}). "
                        f"Total excluding spikes: {total_excl_spikes:.1f} mm.")
    else:
        total_excl_spikes = total_mm
        spike_warning = None

    return {
        'station': station_id,
        'year': year, 'month': month,
        'total_mm': total_mm,
        'total_excl_spikes_mm': total_excl_spikes,
        'days_with_data': days_with_data,
        'days_expected': days_in_month,
        'missing_days': days_in_month - days_with_data,
        'spike_warning': spike_warning,
        'daily': daily,
    }, None


def assess_wu_reliability(wu_result, valley_rain_mm=None):
    """
    Assess whether WU station data is reliable for this month.
    Returns: (is_reliable: bool, warnings: list[str])
    """
    warnings_list = []

    if wu_result is None:
        return False, ["WU data unavailable"]

    # Check missing days
    if wu_result['missing_days'] > WU_MAX_MISSING_DAYS:
        warnings_list.append(
            f"Station offline for {wu_result['missing_days']} days "
            f"(threshold: {WU_MAX_MISSING_DAYS})"
        )

    # Check for spike anomalies
    if wu_result['spike_warning']:
        warnings_list.append(wu_result['spike_warning'])

    # Cross-check against Valley if available
    wu_total = wu_result['total_excl_spikes_mm']
    if valley_rain_mm is not None and valley_rain_mm > 0 and wu_total > 0:
        ratio = wu_total / valley_rain_mm
        if ratio > WU_VALLEY_RATIO_THRESHOLD or ratio < (1 / WU_VALLEY_RATIO_THRESHOLD):
            warnings_list.append(
                f"WU total ({wu_total:.0f} mm) differs from Valley ({valley_rain_mm:.0f} mm) "
                f"by factor {ratio:.1f}x"
            )

    is_reliable = len(warnings_list) == 0
    return is_reliable, warnings_list


def generate_rainfall_summary(wu_result, valley_rain_mm=None, valley_avg_mm=None):
    """
    Generate a structured text description of the monthly rainfall pattern
    from WU daily data, suitable for passing to an AI to write the narrative.
    """
    if wu_result is None:
        return None

    daily = wu_result['daily']
    month = wu_result['month']
    year = wu_result['year']
    station = wu_result['station']

    # Basic stats
    valid = [d for d in daily if d['precip_mm'] is not None]
    precip_vals = [d['precip_mm'] for d in valid]
    rain_days = [d for d in valid if d['precip_mm'] >= 1.0]
    dry_days = [d for d in valid if d['precip_mm'] < 1.0]
    total = sum(precip_vals)
    missing = wu_result['missing_days']

    # Find dry spells (consecutive days < 1mm)
    dry_spells = []
    wet_spells = []
    current_dry = []
    current_wet = []
    for d in daily:
        p = d['precip_mm']
        if p is not None and p < 1.0:
            current_dry.append(d['date'])
            if current_wet:
                wet_spells.append(current_wet)
                current_wet = []
        elif p is not None and p >= 1.0:
            current_wet.append((d['date'], p))
            if current_dry:
                dry_spells.append(current_dry)
                current_dry = []
        else:
            # Missing day — close both
            if current_dry:
                dry_spells.append(current_dry)
                current_dry = []
            if current_wet:
                wet_spells.append(current_wet)
                current_wet = []
    if current_dry:
        dry_spells.append(current_dry)
    if current_wet:
        wet_spells.append(current_wet)

    # Longest dry spell
    longest_dry = max(dry_spells, key=len) if dry_spells else []

    # Distribution: first half vs second half
    mid = len(daily) // 2
    first_half = sum(d['precip_mm'] for d in daily[:mid]
                     if d['precip_mm'] is not None)
    second_half = sum(d['precip_mm'] for d in daily[mid:]
                      if d['precip_mm'] is not None)

    # Wettest days
    top3 = sorted(valid, key=lambda d: d['precip_mm'], reverse=True)[:3]

    # Spike check
    spike_note = wu_result.get('spike_warning', '')

    # ── Build summary text ──
    lines = []
    lines.append(f"RAINFALL PATTERN SUMMARY: {MONTH_NAMES[month]} {year}")
    lines.append(f"Station: {station} (Weather Underground)")
    lines.append(f"{'='*60}")
    lines.append("")

    lines.append(f"Total rainfall: {total:.1f} mm from {len(valid)} days of data"
                 f" ({missing} days missing)")
    lines.append(f"Rain days (≥1mm): {len(rain_days)}")
    lines.append(f"Dry days (<1mm):  {len(dry_days)}")
    lines.append("")

    if valley_rain_mm is not None:
        lines.append(f"RAF Valley official total: {valley_rain_mm:.1f} mm")
    if valley_avg_mm is not None:
        lines.append(f"Valley long-term average for {MONTH_NAMES[month]}: "
                     f"{valley_avg_mm:.1f} mm")
    lines.append("")

    # Distribution
    lines.append(f"Distribution through the month:")
    lines.append(f"  1st–{mid}th: {first_half:.1f} mm")
    lines.append(f"  {mid+1}th–{len(daily)}th: {second_half:.1f} mm")
    if first_half > 0 and second_half > 0:
        ratio = first_half / second_half if second_half > 0 else float('inf')
        if ratio > 3:
            lines.append(f"  → Rainfall heavily concentrated in the first half")
        elif ratio > 1.5:
            lines.append(f"  → First half was wetter")
        elif 1/ratio > 3:
            lines.append(f"  → Rainfall heavily concentrated in the second half")
        elif 1/ratio > 1.5:
            lines.append(f"  → Second half was wetter")
        else:
            lines.append(f"  → Fairly evenly distributed")
    elif second_half < 0.5:
        lines.append(f"  → Almost all rain fell in the first half; "
                     f"second half essentially dry")
    lines.append("")

    # Wettest days
    lines.append(f"Wettest days:")
    for d in top3:
        lines.append(f"  {d['date']}: {d['precip_mm']:.1f} mm")
    lines.append("")

    # Dry spells
    if longest_dry and len(longest_dry) >= 3:
        lines.append(f"Longest dry spell: {len(longest_dry)} days "
                     f"({longest_dry[0]} to {longest_dry[-1]})")
    lines.append("")

    # Wet spells
    notable_wet = [s for s in wet_spells if len(s) >= 3]
    if notable_wet:
        lines.append(f"Notable wet spells (3+ consecutive rain days):")
        for spell in notable_wet:
            spell_total = sum(p for _, p in spell)
            lines.append(f"  {spell[0][0]} to {spell[-1][0]}: "
                         f"{len(spell)} days, {spell_total:.1f} mm")
    lines.append("")

    # Daily log
    lines.append(f"Daily rainfall log:")
    for d in daily:
        p = d['precip_mm']
        if p is not None:
            bar = '█' * max(1, int(p / 2)) if p >= 0.5 else '·'
            lines.append(f"  {d['date']}: {p:5.1f} mm {bar}")
        else:
            lines.append(f"  {d['date']}:   n/a  (missing)")
    lines.append("")

    if spike_note:
        lines.append(f"DATA QUALITY WARNING: {spike_note}")
        lines.append("")

    lines.append(f"{'='*60}")
    lines.append("Use the above to write a monthly weather narrative for the")
    lines.append("Newborough Warren Water Watch newsletter.")

    return '\n'.join(lines)


def prompt_alternative_station(station_id, warnings_list):
    """
    Interactive prompt when WU data is unreliable.
    Returns: (action, alt_station_id)
        action: 'use' (use anyway), 'skip' (Valley only), 'alt' (try another station)
    """
    print(f"\n  ⚠  Weather Underground station {station_id} flagged as unreliable:")
    for w in warnings_list:
        print(f"     • {w}")

    print(f"\n  Options:")
    print(f"    1) Use {station_id} data anyway (with warning in report)")
    print(f"    2) Skip local station — use RAF Valley data only")
    print(f"    3) Try a different WU station (enter ID)")

    while True:
        choice = input("\n  Enter choice [1/2/3]: ").strip()
        if choice == '1':
            return 'use', station_id
        elif choice == '2':
            return 'skip', None
        elif choice == '3':
            alt = input("  Enter alternative station ID: ").strip().upper()
            if alt:
                return 'alt', alt
            else:
                print("  No station ID entered, try again.")
        else:
            print("  Invalid choice, try again.")


# ─── Difference Calculations ────────────────────────────────────────────────

def find_closest_date(dates, target_date, max_days=45):
    """Find the closest measurement date to a target date."""
    target = pd.to_datetime(target_date)
    best = None
    best_diff = timedelta(days=max_days + 1)
    for i, d in enumerate(dates):
        if d is None or pd.isna(d):
            continue
        diff = abs(d - target)
        if diff < best_diff:
            best_diff = diff
            best = i
    if best is not None and best_diff <= timedelta(days=max_days):
        return best, dates[best]
    return None, None


def bucket_month(d):
    """Field-convention monthly bucket for a reading date.

    A dipwell reading is taken at the end of a month or the first ~15 days
    of the following month, and represents the month just ended:
        reading day  > 15  -> that calendar month
        reading day <= 15  -> the previous calendar month
    e.g. a reading dated 4 June is May's level; 31 May is also May.

    Returns a (year, month) tuple, or None if the date is missing.
    """
    if d is None or pd.isna(d):
        return None
    d = pd.Timestamp(d)
    if d.day > 15:
        return (d.year, d.month)
    if d.month == 1:
        return (d.year - 1, 12)
    return (d.year, d.month - 1)


def find_month_column(dates, year, month):
    """Deterministically find the Absolute-Level column for a calendar month.

    Returns (column_index, date) of the reading that buckets to (year, month)
    by the field rule, independent of any later months already in the sheet —
    so re-running an earlier month's report is reproducible. If more than one
    reading buckets to the same month, the latest-dated one is used. Returns
    (None, None) if no reading buckets to that month.
    """
    candidates = [(i, d) for i, d in enumerate(dates)
                  if bucket_month(d) == (year, month)]
    if not candidates:
        return None, None
    return max(candidates, key=lambda x: x[1])


def compute_differences_by_index(wells, coords, idx1, idx2):
    """
    Compute water level differences using column indices into the Absolute Level sheet.
    diff = level_at_idx2 - level_at_idx1.  Positive = water level rose.
    """
    results = []
    for well in wells:
        name = well['well_name']
        if name not in coords:
            continue
        e, n = coords[name]
        levels = well['levels']
        if idx1 < len(levels) and idx2 < len(levels):
            v1 = levels[idx1]
            v2 = levels[idx2]
            if pd.notna(v1) and pd.notna(v2):
                try:
                    diff = round(float(v2) - float(v1), 3)
                    results.append((e, n, diff))
                except (ValueError, TypeError):
                    pass
    return results


def write_difference_csv(results, filepath):
    """Write difference results to CSV in E,N,Z format."""
    with open(filepath, 'w') as f:
        f.write('E,N,Z\n')
        for e, n, z in results:
            if z != 0 and not np.isnan(z):
                f.write(f'{e},{n},{z:.2f}\n')
            else:
                f.write(f'{e},{n},\n')
    print(f"    Written {len(results)} wells to {os.path.basename(filepath)}")


# ─── Interpolation Map with Hillshade ────────────────────────────────────────

def create_difference_map(results, title, filepath, extent=MAP_EXTENT,
                          hillshade=None, hs_extent=None, kml_dir=None):
    """
    Create an interpolated difference map as a PNG.
    Overlays interpolation on DEM hillshade with KML feature layers.
    """
    try:
        from scipy.interpolate import griddata
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.colors import BoundaryNorm
        from matplotlib.patches import Polygon as MplPolygon
    except ImportError:
        print("    Warning: scipy/matplotlib not available, skipping map")
        return

    valid = [(e, n, z) for e, n, z in results if not np.isnan(z) and z != 0]
    if len(valid) < 4:
        print(f"    Warning: Only {len(valid)} valid points, need >=4 for interpolation")
        return

    es = np.array([v[0] for v in valid])
    ns = np.array([v[1] for v in valid])
    zs = np.array([v[2] for v in valid])

    # Interpolation grid
    grid_e = np.arange(extent['e_min'], extent['e_max'], extent['resolution'])
    grid_n = np.arange(extent['n_min'], extent['n_max'], extent['resolution'])
    grid_e, grid_n = np.meshgrid(grid_e, grid_n)
    grid_z = griddata((es, ns), zs, (grid_e, grid_n), method='cubic')

    # Clamp to observed data range to prevent cubic interpolation overshoots
    grid_z = np.clip(grid_z, np.nanmin(zs), np.nanmax(zs))

    # ── Figure ──
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    # 1. Hillshade base
    if hillshade is not None and hs_extent is not None:
        ax.imshow(hillshade, cmap='gray', extent=hs_extent, origin='upper',
                  aspect='equal', alpha=1.0, vmin=0.2, vmax=1.0)

    # 2. Colour scale
    if np.nanmin(zs) >= -0.01:
        # All rising — sequential blue
        z_max = np.nanmax(zs) + 0.05
        boundaries = np.linspace(0, z_max, 11)
        cmap = plt.cm.Blues
    elif np.nanmax(zs) <= 0.01:
        # All falling — sequential red reversed
        z_min = np.nanmin(zs) - 0.05
        boundaries = np.linspace(z_min, 0, 11)
        cmap = plt.cm.Reds_r
    else:
        # Mixed — diverging
        neg_bounds = np.linspace(np.nanmin(zs) - 0.02, 0, 6)
        pos_bounds = np.linspace(0, np.nanmax(zs) + 0.02, 6)[1:]
        boundaries = np.concatenate([neg_bounds, pos_bounds])
        cmap = plt.cm.RdYlBu

    norm = BoundaryNorm(boundaries, cmap.N)

    # 3. Interpolated surface
    alpha = 0.55 if hillshade is not None else 0.8
    im = ax.pcolormesh(grid_e, grid_n, grid_z, cmap=cmap, norm=norm, alpha=alpha)

    # 4. KML overlays
    kml_handles = []
    if kml_dir:
        kml_handles = add_kml_features(ax, kml_dir, include_streams=False)

    # 5. Well points
    ax.scatter(es, ns, c=zs, cmap=cmap, norm=norm,
               edgecolors='black', linewidth=0.5, s=30, zorder=5)

    # 6. Colorbar
    cbar = plt.colorbar(im, ax=ax, label='Water level change (m)',
                        boundaries=boundaries, ticks=boundaries)
    cbar.ax.tick_params(labelsize=7)

    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xlabel('Easting (m)')
    ax.set_ylabel('Northing (m)')
    ax.set_aspect('equal')
    ax.set_xlim(extent['e_min'], extent['e_max'])
    ax.set_ylim(extent['n_min'], extent['n_max'])

    if hillshade is None:
        ax.grid(True, alpha=0.3)

    if kml_handles:
        ax.legend(handles=kml_handles, loc='lower left', fontsize=7, framealpha=0.8)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    Map saved to {os.path.basename(filepath)}")


# ─── Met Report ──────────────────────────────────────────────────────────────

def generate_met_summary(valley_df, year, month, wu_result=None, wu_warnings=None):
    """Generate a meteorological summary for a given month."""
    row = valley_df[(valley_df['year'] == year) & (valley_df['month'] == month)]

    lines = []
    lines.append(f"## Meteorological Summary — {MONTH_NAMES[month]} {year}")

    # ── Valley data ──
    if row.empty:
        lines.append(f"\n*RAF Valley data not yet available for {MONTH_NAMES[month]} {year}.*")
        rain = None
    else:
        row = row.iloc[0]
        rain = row['rain']
        tmax = row['tmax']
        tmin = row['tmin']
        sun = row['sun']
        af = row['af']

        # Historical context (1991-2020 normals)
        month_data = valley_df[valley_df['month'] == month].dropna(subset=['rain'])
        recent = month_data[(month_data['year'] >= 1991) & (month_data['year'] <= 2020)]
        avg_data = recent if len(recent) > 10 else month_data

        avg_rain = avg_data['rain'].mean()
        avg_tmax = avg_data['tmax'].mean()
        avg_tmin = avg_data['tmin'].mean()
        avg_sun = avg_data['sun'].dropna().mean()

        rank = (month_data['rain'] < rain).sum() / len(month_data) * 100 if rain is not None else None

        yr_min = valley_df['year'].min()
        lines.append(f"### RAF Valley ({yr_min}–{year} record)")
        lines.append("")

        if rain is not None:
            pct_of_avg = (rain / avg_rain * 100) if avg_rain > 0 else 0
            rain_desc = "above" if rain > avg_rain else "below"
            well_prefix = 'well ' if abs(pct_of_avg - 100) > 30 else ''
            lines.append(
                f"**Rainfall**: {rain:.1f} mm — {pct_of_avg:.0f}% of the 1991–2020 average "
                f"({avg_rain:.1f} mm), {well_prefix}{rain_desc} normal."
            )
            if rank is not None:
                if rank > 90:
                    lines.append(f"This ranks as an exceptionally wet {MONTH_NAMES[month]} (top {100-rank:.0f}% of record).")
                elif rank > 75:
                    lines.append(f"This was a wetter than typical {MONTH_NAMES[month]} (top {100-rank:.0f}%).")
                elif rank < 10:
                    lines.append(f"This was an unusually dry {MONTH_NAMES[month]} (bottom {rank:.0f}% of record).")
                elif rank < 25:
                    lines.append(f"This was a drier than typical {MONTH_NAMES[month]}.")

        lines.append("")
        lines.append(
            f"**Temperature**: Max {tmax:.1f}°C (avg {avg_tmax:.1f}°C), "
            f"Min {tmin:.1f}°C (avg {avg_tmin:.1f}°C). "
            f"{'Milder' if tmin > avg_tmin else 'Cooler'} than average."
        )
        if af > 0:
            lines.append(f"There {'was' if int(af) == 1 else 'were'} {int(af)} day{'s' if int(af) != 1 else ''} of air frost.")
        else:
            lines.append("No air frost recorded.")

        if sun is not None and avg_sun is not None:
            lines.append(
                f"**Sunshine**: {sun:.1f} hours "
                f"({'above' if sun > avg_sun else 'below'} average of {avg_sun:.1f} hours)."
            )

        # Previous month comparison
        prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
        prev_row = valley_df[(valley_df['year'] == prev_year) & (valley_df['month'] == prev_month)]
        if not prev_row.empty and rain is not None:
            prev_rain = prev_row.iloc[0]['rain']
            if prev_rain is not None:
                lines.append("")
                lines.append(
                    f"Compared to {MONTH_NAMES[prev_month]}, rainfall "
                    f"{'increased' if rain > prev_rain else 'decreased'} "
                    f"from {prev_rain:.1f} mm to {rain:.1f} mm."
                )

        # Hydrological year cumulative
        if month >= 10:
            hydro_months = valley_df[(valley_df['year'] == year) & (valley_df['month'] >= 10)]
        else:
            hydro_months = pd.concat([
                valley_df[(valley_df['year'] == year - 1) & (valley_df['month'] >= 10)],
                valley_df[(valley_df['year'] == year) & (valley_df['month'] <= month)]
            ])
        cum_rain = hydro_months['rain'].sum()

        cum_avgs = []
        for y in range(1991, 2021):
            if month >= 10:
                h = valley_df[(valley_df['year'] == y) & (valley_df['month'] >= 10)]
            else:
                h = pd.concat([
                    valley_df[(valley_df['year'] == y - 1) & (valley_df['month'] >= 10)],
                    valley_df[(valley_df['year'] == y) & (valley_df['month'] <= month)]
                ])
            cum_avgs.append(h['rain'].sum())
        avg_cum = np.mean(cum_avgs) if cum_avgs else 0

        lines.append("")
        lines.append(
            f"**Hydrological year** (Oct–{MONTH_NAMES[month]}): Cumulative rainfall {cum_rain:.0f} mm "
            f"({'above' if cum_rain > avg_cum else 'below'} the average of {avg_cum:.0f} mm, "
            f"{cum_rain/avg_cum*100:.0f}%)."
        )

    # ── Weather Underground local station ──
    if wu_result is not None:
        lines.append("")
        lines.append(f"### Local station: {wu_result['station']} (Weather Underground)")
        lines.append("")
        lines.append(
            f"Monthly precipitation: {wu_result['total_mm']:.1f} mm "
            f"({wu_result['days_with_data']}/{wu_result['days_expected']} days recorded)."
        )
        if wu_result['spike_warning']:
            lines.append(f"*Note: {wu_result['spike_warning']}*")
            lines.append(
                f"Adjusted total (excluding spikes): {wu_result['total_excl_spikes_mm']:.1f} mm."
            )

        if wu_warnings:
            lines.append("")
            lines.append("**⚠ Data quality warnings:**")
            for w in wu_warnings:
                lines.append(f"- {w}")

    return '\n'.join(lines)


# ─── Difference Summary Table ────────────────────────────────────────────────

def generate_difference_table(results, coords, label):
    """Generate a markdown table of water level differences."""
    lines = []
    lines.append(f"\n## Water Level Changes: {label}")
    lines.append("")
    lines.append("| Well | E | N | Change (m) |")
    lines.append("|------|---|---|-----------|")

    name_lookup = {(e, n): name for name, (e, n) in coords.items()}

    for e, n, z in sorted(results, key=lambda x: x[2], reverse=True):
        name = name_lookup.get((e, n), '?')
        if not np.isnan(z):
            lines.append(f"| {name} | {e:.0f} | {n:.0f} | {z:+.3f} |")

    valid_z = [z for _, _, z in results if not np.isnan(z)]
    if valid_z:
        lines.append("")
        lines.append(
            f"**Summary**: {len(valid_z)} wells measured. "
            f"Mean change: {np.mean(valid_z):+.3f} m, "
            f"Range: {min(valid_z):+.3f} to {max(valid_z):+.3f} m."
        )
        rising = sum(1 for z in valid_z if z > 0.01)
        falling = sum(1 for z in valid_z if z < -0.01)
        stable = len(valid_z) - rising - falling
        lines.append(f"Rising: {rising}, Falling: {falling}, Stable (±0.01m): {stable}")

    return '\n'.join(lines)


# ─── PDF Report Generation ───────────────────────────────────────────────────

def generate_pdf_report(output_dir, year, month, met_text,
                        mom_results, mom_d1, mom_d2,
                        yoy_results, yoy_d1, yoy_d2,
                        low_results, low_d1, low_d2,
                        coords, wu_result=None, wu_warnings=None,
                        valley_df=None, wells=None, dates=None, latest_idx=None):
    """
    Generate a PDF report in the style of the Newborough Warren
    Weather & Water Watch newsletter.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm, cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Image, Table, TableStyle, PageBreak,
                                        KeepTogether)
    except ImportError:
        print("    Warning: reportlab not available, skipping PDF generation")
        return None

    pdf_path = os.path.join(output_dir, f"Newborough_Water_Watch_{year}_{month:02d}.pdf")

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    # ── Styles ──
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=20, spaceAfter=6*mm, textColor=HexColor('#1a5276'),
        fontName='Helvetica-Bold'
    )
    style_h2 = ParagraphStyle(
        'ReportH2', parent=styles['Heading2'],
        fontSize=14, spaceBefore=6*mm, spaceAfter=3*mm,
        textColor=HexColor('#2e86c1'), fontName='Helvetica-Bold'
    )
    style_h3 = ParagraphStyle(
        'ReportH3', parent=styles['Heading3'],
        fontSize=11, spaceBefore=4*mm, spaceAfter=2*mm,
        textColor=HexColor('#2874a6'), fontName='Helvetica-Bold'
    )
    style_body = ParagraphStyle(
        'ReportBody', parent=styles['Normal'],
        fontSize=10, leading=14, spaceAfter=3*mm,
        alignment=TA_JUSTIFY, fontName='Helvetica'
    )
    style_caption = ParagraphStyle(
        'Caption', parent=styles['Normal'],
        fontSize=9, leading=12, spaceAfter=4*mm,
        alignment=TA_CENTER, fontName='Helvetica-Oblique',
        textColor=HexColor('#666666')
    )
    style_warning = ParagraphStyle(
        'Warning', parent=styles['Normal'],
        fontSize=10, leading=13, spaceAfter=3*mm,
        fontName='Helvetica-Oblique', textColor=HexColor('#c0392b')
    )

    story = []

    # ── Title ──
    story.append(Paragraph(
        f"Newborough Warren Weather &amp; Water Watch: {MONTH_NAMES[month]} {year}",
        style_title
    ))
    story.append(Spacer(1, 4*mm))

    # ── Weather summary section ──
    story.append(Paragraph("Weather Summary", style_h2))

    # Build weather stats table
    valley_row = None
    if valley_df is not None:
        vr = valley_df[(valley_df['year'] == year) & (valley_df['month'] == month)]
        if not vr.empty:
            valley_row = vr.iloc[0]

    # Valley historical averages
    avg_rain = avg_tmax = avg_tmin = None
    if valley_df is not None:
        month_data = valley_df[valley_df['month'] == month].dropna(subset=['rain'])
        recent = month_data[(month_data['year'] >= 1991) & (month_data['year'] <= 2020)]
        avg_data = recent if len(recent) > 10 else month_data
        avg_rain = avg_data['rain'].mean()
        avg_tmax = avg_data['tmax'].mean()
        avg_tmin = avg_data['tmin'].mean()

    table_data = [
        ['Metric', 'Local Gauge\n(ILLANF24)', 'RAF Valley', f'Typical {MONTH_NAMES[month]}*']
    ]

    wu_rain = ''
    if wu_result:
        wu_total = wu_result['total_excl_spikes_mm'] if wu_result['spike_warning'] else wu_result['total_mm']
        wu_rain = f"{wu_total:.1f} mm"
    valley_rain_str = f"{valley_row['rain']:.1f} mm" if valley_row is not None and valley_row['rain'] is not None else 'N/A'
    avg_rain_str = f"~{avg_rain:.1f} mm" if avg_rain else 'N/A'
    table_data.append(['Total Rainfall', wu_rain or 'N/A', valley_rain_str, avg_rain_str])

    valley_tmax_str = f"{valley_row['tmax']:.1f} C" if valley_row is not None else 'N/A'
    avg_tmax_str = f"{avg_tmax:.1f} C" if avg_tmax else 'N/A'
    table_data.append(['Average Highs', '', valley_tmax_str, avg_tmax_str])

    valley_tmin_str = f"{valley_row['tmin']:.1f} C" if valley_row is not None else 'N/A'
    avg_tmin_str = f"{avg_tmin:.1f} C" if avg_tmin else 'N/A'
    table_data.append(['Average Lows', '', valley_tmin_str, avg_tmin_str])

    tbl = Table(table_data, colWidths=[35*mm, 40*mm, 35*mm, 40*mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2e86c1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8f9fa'), HexColor('#ffffff')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Paragraph("*Based on 1991-2020 Met Office climate averages (RAF Valley).", style_caption))

    # Rainfall narrative
    if valley_row is not None and valley_row['rain'] is not None and avg_rain:
        rain = valley_row['rain']
        pct = rain / avg_rain * 100
        if pct > 130:
            rain_narrative = (
                f"{MONTH_NAMES[month]} was exceptionally wet, with {rain:.1f} mm recorded at "
                f"RAF Valley - that is {pct:.0f}% of the long-term average ({avg_rain:.1f} mm). "
            )
        elif pct > 110:
            rain_narrative = (
                f"{MONTH_NAMES[month]} was wetter than average, with {rain:.1f} mm recorded at "
                f"RAF Valley ({pct:.0f}% of the {avg_rain:.1f} mm average). "
            )
        elif pct < 70:
            rain_narrative = (
                f"{MONTH_NAMES[month]} was notably dry, with just {rain:.1f} mm at "
                f"RAF Valley - only {pct:.0f}% of the average ({avg_rain:.1f} mm). "
            )
        else:
            rain_narrative = (
                f"{MONTH_NAMES[month]} saw {rain:.1f} mm at RAF Valley, "
                f"close to the {avg_rain:.1f} mm average ({pct:.0f}%). "
            )

        if valley_row['tmin'] > avg_tmin:
            rain_narrative += (
                f"Temperatures were milder than usual with lows of {valley_row['tmin']:.1f} C "
                f"(average {avg_tmin:.1f} C)."
            )
        else:
            rain_narrative += (
                f"Temperatures were cooler than average with lows of {valley_row['tmin']:.1f} C "
                f"(average {avg_tmin:.1f} C)."
            )
        story.append(Paragraph(rain_narrative, style_body))

    # Hydrological year context
    if valley_df is not None and valley_row is not None:
        if month >= 10:
            hydro = valley_df[(valley_df['year'] == year) & (valley_df['month'] >= 10)]
        else:
            hydro = pd.concat([
                valley_df[(valley_df['year'] == year - 1) & (valley_df['month'] >= 10)],
                valley_df[(valley_df['year'] == year) & (valley_df['month'] <= month)]
            ])
        cum = hydro['rain'].sum()
        cum_avgs = []
        for y in range(1991, 2021):
            if month >= 10:
                h = valley_df[(valley_df['year'] == y) & (valley_df['month'] >= 10)]
            else:
                h = pd.concat([
                    valley_df[(valley_df['year'] == y - 1) & (valley_df['month'] >= 10)],
                    valley_df[(valley_df['year'] == y) & (valley_df['month'] <= month)]
                ])
            cum_avgs.append(h['rain'].sum())
        avg_cum = np.mean(cum_avgs) if cum_avgs else 0
        if avg_cum > 0:
            story.append(Paragraph(
                f"The hydrological year cumulative rainfall (October to {MONTH_NAMES[month]}) "
                f"stands at {cum:.0f} mm, which is {cum/avg_cum*100:.0f}% of the average "
                f"({avg_cum:.0f} mm).",
                style_body
            ))

    # WU warnings
    if wu_warnings:
        for w in wu_warnings:
            story.append(Paragraph(f"Data quality note: {w}", style_warning))

    # ── Water levels section ──
    story.append(Paragraph("Local Water Levels", style_h2))

    # Count brimming wells (water within 5cm of surface)
    brimming = 0
    if wells and dates and latest_idx is not None:
        for well in wells:
            levels = well['levels']
            if latest_idx < len(levels):
                v = levels[latest_idx]
                if pd.notna(v):
                    try:
                        # In the measured sheet, low depth = high water
                        # But we're using Absolute Level — can't determine depth from surface
                        pass
                    except (ValueError, TypeError):
                        pass

    n_wells = len(mom_results) if mom_results else 0
    valid_z = [z for _, _, z in mom_results] if mom_results else []
    rising = sum(1 for z in valid_z if z > 0.01)
    falling = sum(1 for z in valid_z if z < -0.01)
    stable = n_wells - rising - falling
    mean_change = np.mean(valid_z) if valid_z else 0

    summary_text = (
        f"The latest well round on {mom_d2.strftime('%d/%m/%Y') if mom_d2 else 'N/A'} "
        f"covered {n_wells} monitoring dipwells across the reserve. "
    )
    if rising > falling:
        summary_text += (
            f"Water levels are predominantly rising: {rising} wells showed increases, "
            f"{falling} showed decreases, and {stable} were stable. "
            f"The mean change was {mean_change:+.3f} m."
        )
    elif falling > rising:
        summary_text += (
            f"Water levels are predominantly falling: {falling} wells showed decreases, "
            f"{rising} showed increases, and {stable} were stable. "
            f"The mean change was {mean_change:+.3f} m."
        )
    else:
        summary_text += f"The mean change was {mean_change:+.3f} m."
    story.append(Paragraph(summary_text, style_body))

    # ── Month-on-month map ──
    if mom_results and mom_d1 and mom_d2:
        mom_label = f"{mom_d1.strftime('%b%y')}-{mom_d2.strftime('%b%y')}"
        map_path = os.path.join(output_dir, f"map_month_{mom_label}.png")
        if os.path.exists(map_path):
            story.append(Paragraph(
                f"Month-on-Month Change: {mom_d1.strftime('%b %Y')} to {mom_d2.strftime('%b %Y')}",
                style_h3
            ))
            img = Image(map_path, width=160*mm, height=130*mm)
            story.append(img)
            story.append(Paragraph(
                f"Water level change (m) from {mom_d1.strftime('%d %b %Y')} to "
                f"{mom_d2.strftime('%d %b %Y')}. "
                f"Blue = rising, red = falling.",
                style_caption
            ))

    # ── Cumulative (since summer low) map ──
    if low_results and low_d1 and low_d2:
        low_label = f"{low_d1.strftime('%b%y')}-{low_d2.strftime('%b%y')}"
        map_path = os.path.join(output_dir, f"map_cumulative_{low_label}.png")
        if os.path.exists(map_path):
            story.append(Paragraph(
                f"Rebound from Summer Low: {low_d1.strftime('%b %Y')} to {low_d2.strftime('%b %Y')}",
                style_h3
            ))
            low_valid = [z for _, _, z in low_results if not np.isnan(z)]
            if low_valid:
                story.append(Paragraph(
                    f"Since the summer low in {low_d1.strftime('%B %Y')}, water levels have risen "
                    f"by an average of {np.mean(low_valid):+.2f} m across {len(low_valid)} wells, "
                    f"with a maximum rise of {max(low_valid):+.2f} m.",
                    style_body
                ))
            img = Image(map_path, width=160*mm, height=130*mm)
            story.append(img)
            story.append(Paragraph(
                f"Cumulative water level change since {low_d1.strftime('%d %b %Y')}.",
                style_caption
            ))

    # ── Year-on-year comparison ──
    if yoy_results and yoy_d1 and yoy_d2:
        story.append(Paragraph(
            f"Year-on-Year Comparison: {yoy_d1.strftime('%b %Y')} vs {yoy_d2.strftime('%b %Y')}",
            style_h3
        ))
        yoy_valid = [z for _, _, z in yoy_results if not np.isnan(z)]
        if yoy_valid:
            yoy_rising = sum(1 for z in yoy_valid if z > 0.01)
            story.append(Paragraph(
                f"Compared to this time last year, {yoy_rising} out of {len(yoy_valid)} wells "
                f"are showing higher water levels, with a mean change of "
                f"{np.mean(yoy_valid):+.3f} m (range {min(yoy_valid):+.3f} to "
                f"{max(yoy_valid):+.3f} m).",
                style_body
            ))

        yoy_label = f"{yoy_d1.strftime('%b%y')}-{yoy_d2.strftime('%b%y')}"
        yoy_map_path = os.path.join(output_dir, f"map_yoy_{yoy_label}.png")
        if os.path.exists(yoy_map_path):
            img = Image(yoy_map_path, width=160*mm, height=130*mm)
            story.append(img)
            story.append(Paragraph(
                f"Year-on-year water level change from {yoy_d1.strftime('%d %b %Y')} to "
                f"{yoy_d2.strftime('%d %b %Y')}.",
                style_caption
            ))

    # ── Well summary table (top & bottom 5) ──
    story.append(PageBreak())
    story.append(Paragraph("Well Measurement Summary", style_h2))

    if mom_results:
        name_lookup = {(e, n): name for name, (e, n) in coords.items()}
        sorted_wells = sorted(
            [(name_lookup.get((e, n), '?'), z) for e, n, z in mom_results if not np.isnan(z)],
            key=lambda x: x[1], reverse=True
        )

        # Top 5 risers and top 5 fallers
        table_rows = [['Well', 'Change (m)', '', 'Well', 'Change (m)']]
        top5 = sorted_wells[:5]
        bottom5 = sorted_wells[-5:]
        for i in range(5):
            t_name, t_z = top5[i] if i < len(top5) else ('', '')
            b_name, b_z = bottom5[i] if i < len(bottom5) else ('', '')
            t_z_str = f"{t_z:+.3f}" if isinstance(t_z, float) else ''
            b_z_str = f"{b_z:+.3f}" if isinstance(b_z, float) else ''
            table_rows.append([t_name, t_z_str, '', b_name, b_z_str])

        well_tbl = Table(table_rows, colWidths=[30*mm, 25*mm, 10*mm, 30*mm, 25*mm])
        well_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), HexColor('#27ae60')),
            ('BACKGROUND', (3, 0), (4, 0), HexColor('#c0392b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),
            ('GRID', (0, 0), (1, -1), 0.5, HexColor('#cccccc')),
            ('GRID', (3, 0), (4, -1), 0.5, HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        story.append(Paragraph("Largest Risers and Fallers (month-on-month)", style_h3))
        story.append(well_tbl)
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(
            f"Full data: {n_wells} wells. "
            f"Mean: {mean_change:+.3f} m. "
            f"Range: {min(valid_z):+.3f} to {max(valid_z):+.3f} m.",
            style_caption
        ))

    # ── Build PDF ──
    try:
        doc.build(story)
        print(f"    PDF report saved to {os.path.basename(pdf_path)}")
        return pdf_path
    except Exception as e:
        print(f"    Warning: PDF generation failed: {e}")
        return None


# ─── Mean Spring Water Level (MSL) ───────────────────────────────────────────

def create_msl_map(results, title, filepath, extent=MAP_EXTENT,
                   hillshade=None, hs_extent=None, kml_dir=None,
                   dem_data=None, dem_e_arr=None, dem_n_arr=None,
                   well_ground_elevs=None, ridge_mask_threshold=1.0):
    """
    Create an interpolated map of MSL depth below ground.
    Applies ridge masking: cells where the DEM is >threshold above the
    interpolated well ground surface are masked out (dune ridges).
    """
    try:
        from scipy.interpolate import griddata
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return

    valid = [(e, n, z) for e, n, z in results if not np.isnan(z)]
    if len(valid) < 4:
        return

    es = np.array([v[0] for v in valid])
    ns = np.array([v[1] for v in valid])
    zs = np.array([v[2] for v in valid])

    grid_e = np.arange(extent['e_min'], extent['e_max'], extent['resolution'])
    grid_n = np.arange(extent['n_min'], extent['n_max'], extent['resolution'])
    grid_e, grid_n = np.meshgrid(grid_e, grid_n)
    grid_z = griddata((es, ns), zs, (grid_e, grid_n), method='linear')

    # Ridge masking — hide dune ridges where MSL is meaningless
    if (dem_data is not None and dem_e_arr is not None and dem_n_arr is not None
            and well_ground_elevs is not None and ridge_mask_threshold is not None):
        from scipy.interpolate import RegularGridInterpolator

        # Build arrays of well positions and their ground elevations
        well_pts = []
        well_gls = []
        for wname, (we, wn, wgl) in well_ground_elevs.items():
            well_pts.append([we, wn])
            well_gls.append(wgl)

        if len(well_pts) >= 4:
            well_pts = np.array(well_pts)
            well_gls = np.array(well_gls)
            surf_dem = griddata(well_pts, well_gls, (grid_e, grid_n), method='linear')

            # Resample actual DEM to the grid
            dem_interp = RegularGridInterpolator(
                (dem_n_arr[::-1], dem_e_arr),
                dem_data[::-1, :],
                method='linear', bounds_error=False, fill_value=np.nan
            )
            dem_at_grid = dem_interp(
                np.column_stack([grid_n.ravel(), grid_e.ravel()])
            ).reshape(grid_e.shape)

            ridge_mask = (dem_at_grid - surf_dem) > ridge_mask_threshold
            grid_z = np.where(ridge_mask, np.nan, grid_z)

    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    if hillshade is not None and hs_extent is not None:
        ax.imshow(hillshade, cmap='gray', extent=hs_extent, origin='upper',
                  aspect='equal', alpha=1.0, vmin=0.2, vmax=1.0)

    cmap = plt.cm.YlGnBu_r  # reversed: blue = shallow/wet, yellow = deep/dry
    alpha = 0.6 if hillshade is not None else 0.85
    im = ax.pcolormesh(grid_e, grid_n, grid_z, cmap=cmap, alpha=alpha)
    ax.scatter(es, ns, c=zs, cmap=cmap, edgecolors='black', linewidth=0.5,
               s=30, zorder=5)

    kml_handles = []
    if kml_dir:
        kml_handles = add_kml_features(ax, kml_dir, include_streams=False)

    cbar = plt.colorbar(im, ax=ax, label='Depth to water table (m below ground)')
    cbar.ax.tick_params(labelsize=7)

    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xlabel('Easting (m)')
    ax.set_ylabel('Northing (m)')
    ax.set_aspect('equal')
    ax.set_xlim(extent['e_min'], extent['e_max'])
    ax.set_ylim(extent['n_min'], extent['n_max'])

    if kml_handles:
        ax.legend(handles=kml_handles, loc='lower left', fontsize=7, framealpha=0.8)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    Map saved to {os.path.basename(filepath)}")


def load_depth_from_surface(filepath):
    """
    Load the 'depth from surface' sheet from the ODS.
    Returns: dict of well_name -> list of (date, depth_value) tuples.
    
    Convention in the sheet:
      negative = water below ground surface
      positive = water above ground surface (flooding)
    """
    df = pd.read_excel(filepath, sheet_name='depth from surface',
                       header=None, engine='odf')
    dates_row = df.iloc[1, 2:]
    well_data = {}
    for row_idx in range(2, len(df)):
        name = df.iloc[row_idx, 1]
        if pd.isna(name):
            continue
        name = str(name).strip()
        readings = []
        for col_idx in range(2, len(df.columns)):
            date_val = dates_row.iloc[col_idx - 2]
            cell_val = df.iloc[row_idx, col_idx]
            if pd.notna(date_val) and pd.notna(cell_val):
                try:
                    dt = pd.to_datetime(date_val)
                    readings.append((dt, float(cell_val)))
                except (ValueError, TypeError):
                    pass
        if readings:
            well_data[name] = readings
    return well_data


def compute_msl_summary(wells, dates, coords, current_year,
                        depth_data=None, n_ref_years=5, **kwargs):
    """
    Compute Mean Spring Water Level (March/April/May average) expressed as
    depth below ground surface (m, positive downward).
    
    Reads directly from the 'depth from surface' sheet — no DEM or ground
    elevation conversion needed.
    
    Sheet convention: negative = below ground, positive = above ground.
    MSL convention: positive = below ground (depth), negative = above ground.
    Curreli et al. (2013) thresholds: SD15b=0.61m, SD16=0.98m.
    """
    if not depth_data:
        return None
    
    def _find_spring_reading(well_readings, year, month):
        last_day = calendar.monthrange(year, month)[1]
        target = datetime(year, month, last_day)
        early = datetime(year, month, 15)
        late = (datetime(year, month + 1, 15) if month < 12
                else datetime(year + 1, 1, 15))
        candidates = [(dt, val, abs((dt - target).days))
                      for dt, val in well_readings
                      if early <= dt <= late]
        return min(candidates, key=lambda x: x[2])[:2] if candidates else (None, None)

    ref_start = current_year - n_ref_years
    ref_end = current_year - 1

    results = {}
    for name, readings in depth_data.items():
        if name not in coords:
            continue

        ref_msls = []
        for year in range(ref_start, ref_end + 1):
            year_depths = []
            for month in [3, 4, 5]:
                dt, val = _find_spring_reading(readings, year, month)
                if dt is not None:
                    year_depths.append(-val)  # negate: positive = below ground
            if len(year_depths) >= 2:
                ref_msls.append(np.mean(year_depths))

        cur_depths = []
        cur_months = 0
        for month in [3, 4, 5]:
            dt, val = _find_spring_reading(readings, current_year, month)
            if dt is not None:
                cur_depths.append(-val)
                cur_months += 1

        if len(ref_msls) >= 3 and len(cur_depths) >= 2:
            ref_msl = np.mean(ref_msls)
            cur_msl = np.mean(cur_depths)
            if ref_msl > 4.0 or cur_msl > 4.0:
                continue
            results[name] = {
                'ref_msl': ref_msl,
                'cur_msl': cur_msl,
                'diff': cur_msl - ref_msl,
                'n_ref_years': len(ref_msls),
                'n_cur_months': cur_months
            }

    if not results:
        return None

    diffs = [v['diff'] for v in results.values()]
    deeper = sum(1 for d in diffs if d > 0.01)
    shallower = sum(1 for d in diffs if d < -0.01)
    n_cur = results[list(results.keys())[0]]['n_cur_months']
    sorted_r = sorted(results.items(), key=lambda x: x[1]['diff'])

    return {
        'n_wells': len(results),
        'mean_diff': np.mean(diffs),
        'median_diff': np.median(diffs),
        'shallower': shallower,
        'deeper': deeper,
        'similar': len(diffs) - deeper - shallower,
        'ref_period': f"{ref_start}–{ref_end}",
        'n_cur_months': n_cur,
        'top5_wetter': sorted_r[:5],
        'top5_drier': sorted_r[-5:],
        'all_results': results,
    }


# ─── Main Report Generator ──────────────────────────────────────────────────

def generate_monthly_report(wells_path, valley_path, diff_creator_path,
                            target_month, output_dir, dem_path=None,
                            kml_dir=None, wu_station=None, coords_csv_path=None,
                            update_valley=False):
    """Generate the complete monthly report."""

    os.makedirs(output_dir, exist_ok=True)
    year = target_month.year
    month = target_month.month

    print(f"\n{'═'*60}")
    print(f"  Newborough Water Level Report: {MONTH_NAMES[month]} {year}")
    print(f"{'═'*60}\n")

    # ── 1. Load core data ──
    print("1. Loading data...")

    # Auto-download Valley data unless told not to
    if update_valley:
        download_valley_data(valley_path)

    valley_df = load_valley_data(valley_path)
    print(f"   Valley: {len(valley_df)} months ({valley_df['year'].min()}–{valley_df['year'].max()})")

    wells, dates, df_meas = load_well_records(wells_path)
    n_dates = sum(1 for d in dates if d is not None)
    print(f"   Wells: {len(wells)} wells, {n_dates} measurement dates")

    coords = load_well_coordinates(diff_creator_path, coords_csv_path)
    print(f"   Coordinates: {len(coords)} wells")

    # ── 2. Load DEM + KML layers ──
    print("\n2. Loading spatial data...")
    result = load_hillshade(dem_path)
    if result[0] is not None:
        hillshade, hs_extent, dem_clip, dem_e_arr, dem_n_arr = result
    else:
        hillshade, hs_extent, dem_clip, dem_e_arr, dem_n_arr = None, None, None, None, None
    if hillshade is not None:
        print(f"   Hillshade: {hillshade.shape[1]}x{hillshade.shape[0]} pixels")
    else:
        print("   Hillshade: not available (maps will use plain background)")

    kml_available = kml_dir and os.path.isdir(kml_dir)
    if kml_available:
        kml_files = [f for f in os.listdir(kml_dir) if f.lower().endswith('.kml')]
        print(f"   KML layers: {len(kml_files)} files found")
    else:
        print("   KML layers: none found")

    # ── 3. Weather Underground ──
    wu_result = None
    wu_warnings = []

    if wu_station:
        print(f"\n3. Fetching Weather Underground data ({wu_station})...")
        wu_result, wu_err = fetch_wu_monthly(wu_station, year, month)

        if wu_err:
            print(f"   Error: {wu_err}")
            wu_result = None
        else:
            print(f"   Total: {wu_result['total_mm']:.1f} mm "
                  f"({wu_result['days_with_data']}/{wu_result['days_expected']} days)")

            # Cross-check with Valley
            valley_row = valley_df[
                (valley_df['year'] == year) & (valley_df['month'] == month)
            ]
            valley_rain = valley_row.iloc[0]['rain'] if not valley_row.empty else None

            is_reliable, wu_warnings = assess_wu_reliability(wu_result, valley_rain)

            if not is_reliable:
                action, alt_id = prompt_alternative_station(wu_station, wu_warnings)
                if action == 'skip':
                    wu_result = None
                    print("   → Using Valley data only.")
                elif action == 'alt':
                    print(f"   → Trying alternative station {alt_id}...")
                    wu_result, wu_err = fetch_wu_monthly(alt_id, year, month)
                    if wu_err:
                        print(f"   Error: {wu_err}")
                        wu_result = None
                    else:
                        print(f"   {alt_id} total: {wu_result['total_mm']:.1f} mm")
                        _, wu_warnings = assess_wu_reliability(wu_result, valley_rain)
                else:
                    print("   → Using data with warnings in report.")
    else:
        print("\n3. WU station: skipped (no station specified)")

    # ── 4. Met summary ──
    print("\n4. Generating Met summary...")
    met_text = generate_met_summary(valley_df, year, month, wu_result, wu_warnings)
    print("   Done.")

    # ── 4b. Rainfall pattern summary for AI ──
    if wu_result is not None:
        valley_row = valley_df[(valley_df['year'] == year) & (valley_df['month'] == month)]
        v_rain = valley_row.iloc[0]['rain'] if not valley_row.empty else None
        month_hist = valley_df[valley_df['month'] == month].dropna(subset=['rain'])
        recent_hist = month_hist[(month_hist['year'] >= 1991) & (month_hist['year'] <= 2020)]
        v_avg = recent_hist['rain'].mean() if len(recent_hist) > 10 else month_hist['rain'].mean()

        rain_summary = generate_rainfall_summary(wu_result, v_rain, v_avg)
        if rain_summary:
            summary_path = os.path.join(output_dir, f"rainfall_summary_{year}_{month:02d}.txt")
            with open(summary_path, 'w') as f:
                f.write(rain_summary)
            print(f"   Rainfall summary saved to {os.path.basename(summary_path)}")

    # ── 5. Compute differences ──
    print("\n5. Computing water level differences...")
    print(f"   Report month: {MONTH_NAMES[month]} {year}")
    print(f"   (Well readings are taken end-of-month or early next month)")

    # ── Field-rule month → column selection (deterministic) ──
    # Each reading is bucketed to a calendar month by the field rule
    # (see bucket_month): day > 15 -> that month, day <= 15 -> previous
    # month. The report for month M uses the column that buckets to M,
    # regardless of any later months already present in the sheet, so
    # re-running an earlier month's report gives identical results.

    target_idx, target_date = find_month_column(dates, year, month)
    if target_idx is None:
        print(f"   Error: no reading buckets to {MONTH_NAMES[month]} {year}.")
        print(f"   Add the {MONTH_NAMES[month]} {year} column to the Absolute")
        print(f"   Level sheet (dated end-of-month or up to the 15th of the")
        print(f"   following month) and re-run.")
        return ""
    latest_idx, latest_date = target_idx, target_date

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev_idx, prev_date = find_month_column(dates, prev_year, prev_month)

    print(f"   Report month {MONTH_NAMES[month]} {year}: "
          f"{latest_date.strftime('%d %b %Y')} (col {latest_idx})")
    if prev_idx is not None:
        print(f"   Previous month {MONTH_NAMES[prev_month]} {prev_year}: "
              f"{prev_date.strftime('%d %b %Y')} (col {prev_idx})")
    else:
        print(f"   Previous month {MONTH_NAMES[prev_month]} {prev_year}: not present")

    # a) Month-on-month
    if prev_idx is not None:
        print(f"\n   a) Month-on-month: {prev_date.strftime('%d %b %Y')} → "
              f"{latest_date.strftime('%d %b %Y')}")
        mom_results = compute_differences_by_index(wells, coords, prev_idx, latest_idx)
        mom_d1, mom_d2 = prev_date, latest_date
    else:
        print(f"\n   a) Month-on-month: previous month not present — skipped")
        mom_results = []
        mom_d1 = mom_d2 = None

    # b) Year-on-year (same calendar month, previous year)
    yoy_col_idx, yoy_date = find_month_column(dates, year - 1, month)
    if yoy_col_idx is not None:
        print(f"   b) Year-on-year:  {yoy_date.strftime('%d %b %Y')} → "
              f"{latest_date.strftime('%d %b %Y')}")
        yoy_results = compute_differences_by_index(wells, coords, yoy_col_idx, latest_idx)
        yoy_d1, yoy_d2 = yoy_date, latest_date
    else:
        yoy_results = []
        yoy_d1 = yoy_d2 = None

    # c) Since summer low (August of the relevant year)
    aug_year = year - 1 if month <= 8 else year
    aug_col_idx, aug_date = find_month_column(dates, aug_year, 8)
    if aug_col_idx is not None:
        print(f"   c) Since summer low: {aug_date.strftime('%d %b %Y')} → "
              f"{latest_date.strftime('%d %b %Y')}")
        low_results = compute_differences_by_index(wells, coords, aug_col_idx, latest_idx)
        low_d1, low_d2 = aug_date, latest_date
    else:
        low_results = []
        low_d1 = low_d2 = None

    # ── 6. Write CSVs ──
    print("\n6. Writing difference CSVs...")
    if mom_results:
        mom_label = f"{mom_d1.strftime('%b%y')}-{mom_d2.strftime('%b%y')}"
        write_difference_csv(mom_results, os.path.join(output_dir, f"{mom_label}.csv"))
    if yoy_results:
        yoy_label = f"{yoy_d1.strftime('%b%y')}-{yoy_d2.strftime('%b%y')}"
        write_difference_csv(yoy_results, os.path.join(output_dir, f"{yoy_label}.csv"))
    if low_results:
        low_label = f"{low_d1.strftime('%b%y')}-{low_d2.strftime('%b%y')}"
        write_difference_csv(low_results, os.path.join(output_dir, f"{low_label}.csv"))

    # ── 7. Generate maps ──
    print("\n7. Generating difference maps...")
    if mom_results:
        mom_title = f"Water level change (m): {mom_d1.strftime('%b %y')} – {mom_d2.strftime('%b %y')}"
        create_difference_map(mom_results, mom_title,
                              os.path.join(output_dir, f"map_month_{mom_label}.png"),
                              hillshade=hillshade, hs_extent=hs_extent,
                              kml_dir=kml_dir)

    if low_results:
        low_title = f"Water level change (m): {low_d1.strftime('%b %y')} – {low_d2.strftime('%b %y')}"
        create_difference_map(low_results, low_title,
                              os.path.join(output_dir, f"map_cumulative_{low_label}.png"),
                              hillshade=hillshade, hs_extent=hs_extent,
                              kml_dir=kml_dir)

    if yoy_results:
        yoy_title = f"Water level change (m): {yoy_d1.strftime('%b %y')} – {yoy_d2.strftime('%b %y')}"
        create_difference_map(yoy_results, yoy_title,
                              os.path.join(output_dir, f"map_yoy_{yoy_label}.png"),
                              hillshade=hillshade, hs_extent=hs_extent,
                              kml_dir=kml_dir)

    # ── 8. Compile report ──
    # ── 8. Mean Spring Water Level ──
    msl_summary = None
    if month in (3, 4, 5):
        print("\n8. Computing Mean Spring Water Level (MSL)...")

        # Load depth-from-surface data directly from ODS
        depth_data = {}
        try:
            depth_data = load_depth_from_surface(wells_path)
            print(f"   Loaded depth-from-surface sheet: {len(depth_data)} wells")
        except Exception as e:
            print(f"   Could not load depth-from-surface sheet: {e}")

        if depth_data:
            msl_summary = compute_msl_summary(wells, dates, coords, year,
                                              depth_data=depth_data)
        if msl_summary:
            print(f"   {msl_summary['n_wells']} wells, {msl_summary['n_cur_months']}/3 spring months")
            print(f"   Mean MSL depth: {msl_summary['mean_diff']:+.3f} m vs "
                  f"{msl_summary['ref_period']} reference")
            print(f"   (positive = deeper/drier, negative = shallower/wetter)")
            print(f"   Shallower (wetter): {msl_summary['shallower']}, "
                  f"Deeper (drier): {msl_summary['deeper']}, "
                  f"Similar: {msl_summary['similar']}")

            msl_path = os.path.join(output_dir, f"msl_summary_{year}.txt")
            with open(msl_path, 'w') as f:
                f.write(f"MEAN SPRING WATER LEVEL (MSL) — {year}\n")
                f.write(f"Depth below ground surface (m, positive downward)\n")
                f.write(f"Reference period: {msl_summary['ref_period']}\n")
                f.write(f"{'='*60}\n\n")
                f.write(f"Wells: {msl_summary['n_wells']}\n")
                f.write(f"Spring months available: {msl_summary['n_cur_months']}/3\n")
                status = "PROVISIONAL" if msl_summary['n_cur_months'] < 3 else "FINAL"
                f.write(f"Status: {status}\n\n")
                f.write(f"Mean MSL diff vs reference: {msl_summary['mean_diff']:+.3f} m\n")
                f.write(f"  (positive = deeper/drier than benchmark)\n")
                f.write(f"  (negative = shallower/wetter than benchmark)\n\n")
                f.write(f"Shallower (wetter) than benchmark: {msl_summary['shallower']}\n")
                f.write(f"Deeper (drier) than benchmark: {msl_summary['deeper']}\n")
                f.write(f"Similar (±0.01m): {msl_summary['similar']}\n\n")
                f.write(f"Ecological thresholds (Curreli et al., 2013):\n")
                f.write(f"  Wet slack viability:  0.61 m\n")
                f.write(f"  Dry slack threshold:  0.98 m\n\n")
                f.write(f"{'Well':<12} {f'{year} MSL':>10} {'5yr ref':>10} {'Diff':>8}\n")
                f.write(f"{'-'*42}\n")
                for name, v in sorted(msl_summary['all_results'].items(),
                                      key=lambda x: x[1]['diff']):
                    f.write(f"{name:<12} {v['cur_msl']:10.3f} {v['ref_msl']:10.3f} "
                            f"{v['diff']:+8.3f}\n")
            print(f"   Saved to {os.path.basename(msl_path)}")

            # ── MSL maps (May only) ──
            if month == 5:
                print("\n   Generating MSL maps...")
                r = msl_summary['all_results']

                # Build well ground elevation lookup for ridge masking
                well_gl = {}
                if coords_csv_path and os.path.exists(coords_csv_path):
                    gl_df = pd.read_csv(coords_csv_path)
                    for _, row in gl_df.iterrows():
                        name = str(row['Name']).strip()
                        dem_elev = row.get('DEM_Ground_Elev')
                        if name in coords and pd.notna(dem_elev):
                            well_gl[name] = (coords[name][0], coords[name][1],
                                             float(dem_elev))

                # Map 1: MSL difference — negate so blue = wetter (better)
                msl_diff_data = [(coords[n][0], coords[n][1], -v['diff'])
                                 for n, v in r.items()]
                ref_label = msl_summary['ref_period']
                create_difference_map(
                    msl_diff_data,
                    f"MSL {year} vs {ref_label} (m, blue=wetter)",
                    os.path.join(output_dir, f"map_msl_diff_{year}.png"),
                    hillshade=hillshade, hs_extent=hs_extent, kml_dir=kml_dir)

                # Map 2: 5-year reference MSL (depth below ground, ridge-masked)
                msl_ref_data = [(coords[n][0], coords[n][1], v['ref_msl'])
                                for n, v in r.items()]
                create_msl_map(
                    msl_ref_data,
                    f"5-year MSL depth below ground (m): {ref_label}",
                    os.path.join(output_dir, f"map_msl_5yr_{ref_label.replace(chr(8211), '-')}.png"),
                    hillshade=hillshade, hs_extent=hs_extent, kml_dir=kml_dir,
                    dem_data=dem_clip, dem_e_arr=dem_e_arr, dem_n_arr=dem_n_arr,
                    well_ground_elevs=well_gl)

                # Map 3: Drift in 5-year benchmark
                prev_msl = compute_msl_summary(wells, dates, coords, year - 1,
                                               depth_data=depth_data)
                if prev_msl:
                    drift_data = []
                    for n, v in r.items():
                        if n in prev_msl['all_results']:
                            # Negate: blue = benchmark getting shallower (wetter)
                            cur_ref = v['ref_msl']
                            prev_ref = prev_msl['all_results'][n]['ref_msl']
                            drift_data.append((coords[n][0], coords[n][1],
                                               -(cur_ref - prev_ref)))
                    if len(drift_data) >= 4:
                        create_difference_map(
                            drift_data,
                            f"5yr MSL drift: {prev_msl['ref_period']} \u2192 {ref_label} (blue=wetter)",
                            os.path.join(output_dir, f"map_msl_drift_{year}.png"),
                            hillshade=hillshade, hs_extent=hs_extent, kml_dir=kml_dir)

    # ── 9. Compiling report ──
    print("\n9. Compiling report...")

    report = []
    report.append(f"# Newborough Water Levels — {MONTH_NAMES[month]} {year}")
    report.append("")
    report.append(met_text)

    if mom_results:
        label = f"{mom_d1.strftime('%d %b %Y')} → {mom_d2.strftime('%d %b %Y')}"
        report.append(generate_difference_table(
            mom_results, coords, f"Month-on-month ({label})"))

    if yoy_results:
        label = f"{yoy_d1.strftime('%d %b %Y')} → {yoy_d2.strftime('%d %b %Y')}"
        report.append(generate_difference_table(
            yoy_results, coords, f"Year-on-year ({label})"))

    if low_results:
        label = f"{low_d1.strftime('%d %b %Y')} → {low_d2.strftime('%d %b %Y')}"
        report.append(generate_difference_table(
            low_results, coords, f"Since summer low ({label})"))

    if msl_summary:
        status = "provisional" if msl_summary['n_cur_months'] < 3 else "final"
        report.append(f"\n## Mean Spring Water Level (MSL) — {year} ({status})")
        report.append("")
        report.append(
            f"MSL is the average depth to water table (below ground surface) across "
            f"March, April, and May — a standard ecohydrological index for dune slack "
            f"habitat assessment. Lower values = wetter conditions. "
            f"This year's MSL is based on {msl_summary['n_cur_months']} of 3 spring months "
            f"and is compared to the {msl_summary['ref_period']} five-year reference."
        )
        report.append("")
        report.append(
            f"**Mean MSL difference vs reference: {msl_summary['mean_diff']:+.3f} m** "
            f"(positive = deeper/drier) — "
            f"{msl_summary['shallower']} wells wetter than benchmark, "
            f"{msl_summary['deeper']} drier, "
            f"{msl_summary['similar']} similar."
        )

    report_text = '\n'.join(report)
    report_path = os.path.join(output_dir, f"report_{year}_{month:02d}.md")
    with open(report_path, 'w') as f:
        f.write(report_text)

    print(f"\n   Report saved to {report_path}")

    # ── 9. Generate PDF report ──
    print("\n9. Generating PDF report...")
    pdf_path = generate_pdf_report(
        output_dir, year, month, met_text,
        mom_results, mom_d1, mom_d2,
        yoy_results, yoy_d1, yoy_d2,
        low_results, low_d1, low_d2,
        coords, wu_result=wu_result, wu_warnings=wu_warnings,
        valley_df=valley_df, wells=wells, dates=dates, latest_idx=latest_idx
    )

    print(f"\n{'═'*60}")
    print(f"  Complete! Output files in {output_dir}/")
    print(f"{'═'*60}")

    return report_text


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Newborough Water Level Monthly Report Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 2026-02
  %(prog)s 2026-03 --wu_station ILLANF24
  %(prog)s 2026-02 --wells path/to/records.ods --valley path/to/valleydata.txt
  %(prog)s 2026-02 --dem newborough_dem.tif --kml_dir ./kml
        """
    )

    parser.add_argument('month', help='Target month (YYYY-MM)')
    parser.add_argument('--wells', default=DEFAULT_WELLS,
                        help=f'Path to well records ODS (default: {DEFAULT_WELLS})')
    parser.add_argument('--valley', default=DEFAULT_VALLEY,
                        help=f'Path to RAF Valley data (default: {DEFAULT_VALLEY})')
    parser.add_argument('--diff_creator', default=None,
                        help='Path to difference creator ODS (for well coordinates)')
    parser.add_argument('--coords_csv', default=DEFAULT_COORDS_CSV,
                        help=f'Path to Well_locations_height.csv (default: {DEFAULT_COORDS_CSV})')
    parser.add_argument('--dem', default=DEFAULT_DEM,
                        help=f'Path to DEM GeoTIFF (default: {DEFAULT_DEM})')
    parser.add_argument('--kml_dir', default=DEFAULT_KML_DIR,
                        help=f'Directory containing KML overlay files (default: {DEFAULT_KML_DIR})')
    parser.add_argument('--wu_station', default=DEFAULT_WU_STATION,
                        help=f'Weather Underground station ID (default: {DEFAULT_WU_STATION})')
    parser.add_argument('--no_wu', action='store_true',
                        help='Skip Weather Underground data')
    parser.add_argument('--no_valley_update', action='store_true',
                        help='Skip auto-downloading latest Valley data from Met Office')
    parser.add_argument('--output_dir', default=DEFAULT_OUTPUT_DIR,
                        help=f'Output directory (default: {DEFAULT_OUTPUT_DIR})')

    args = parser.parse_args()
    target = datetime.strptime(args.month, '%Y-%m')
    wu = None if args.no_wu else args.wu_station

    generate_monthly_report(
        wells_path=args.wells,
        valley_path=args.valley,
        diff_creator_path=args.diff_creator,
        coords_csv_path=args.coords_csv,
        target_month=target,
        output_dir=args.output_dir,
        dem_path=args.dem,
        kml_dir=args.kml_dir,
        wu_station=wu,
        update_valley=not args.no_valley_update,
    )


if __name__ == '__main__':
    main()
