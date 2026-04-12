"""
utils/map_utils.py
Shared GIS and map plotting helpers used across all spatial output scripts.

Key functions
-------------
load_dem_layer(ax, data_dir)
    Loads the site DEM onto an existing axes object using a coloured terrain
    colormap. Returns the image layer (for colorbar attachment) and a boolean
    indicating success. Used by all point-symbol metric maps (scripts 04, 07,
    08, 12, 13, 18).

load_dem_hillshade(ax, data_dir, alpha, vert_exag, zorder)
    Loads the site DEM as a greyscale hillshade (LightSource, azdeg=315,
    altdeg=35) onto an existing axes object. Returns the pcolormesh layer and
    a boolean indicating success. Used by continuous-surface maps where the
    metric surface is overlaid semi-transparently on top (scripts 11b, 19, 20).

add_kml_features(ax, data_dir)
    Overlays Features.kml, streams.kml, and clearfell.kml onto an axes object.
    Returns a list of legend handles for the features drawn.

add_osm_basemap(ax, gdf)
    Fallback basemap from OpenStreetMap when the DEM is unavailable.

add_idw_surface(ax, df, value_col, xi, yi, method, ridge_mask_threshold,
                dem_e_arr, dem_n_arr, dem_data, cmap, norm, alpha, zorder)
    IDW-interpolates a per-well metric to a regular grid, applies an optional
    ridge mask (cells where the DEM sits more than ridge_mask_threshold metres
    above the IDW-interpolated well-DEM surface are masked), and renders as a
    pcolormesh. Returns (pcolormesh_object, grid_x, grid_y, surf_masked) so
    the caller can attach a colorbar and draw contours. Used by scripts 11b,
    19, 20.

plot_metric_map(map_df, value_col, title, output_path, cmap, data_dir, vmin, vmax)
    Full publication-quality spatial metric map with DEM background, KML overlays,
    cluster-shape markers, dual colorbars, and legend.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LightSource
import geopandas as gpd
import contextily as ctx
import fiona
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.interpolate import griddata, RegularGridInterpolator
from pathlib import Path

from utils.config import (
    CLUSTER_COLOURS,
    CLUSTER_LABELS,
    CLUSTER_MARKERS,
    DEM_VMIN,
    DEM_VCENTER,
    DEM_VMAX,
)

fiona.drvsupport.supported_drivers["KML"] = "rw"


def _safe_read_kml(path_obj):
    """Read a KML file, returning None and printing a warning on failure."""
    try:
        return gpd.read_file(str(path_obj), driver="KML")
    except Exception as exc:
        print(f"  [WARNING] Skipping {Path(path_obj).name}: KML unavailable ({exc})")
        return None


def load_dem_layer(ax, data_dir: Path):
    """
    Load the site DEM and render it onto ax.

    Uses a custom terrain colormap with TwoSlopeNorm anchored at sea level (0 m),
    the dune crest inflection (12 m), and the DEM maximum. Sub-zero pixels are
    painted dodgerblue to represent water.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    data_dir : Path

    Returns
    -------
    dem_layer : AxesImage or None
        The imshow layer, suitable for attaching a colorbar.
    dem_loaded : bool
    """
    dem_path = data_dir / "newborough_dem.tif"
    if not dem_path.exists():
        return None, False

    try:
        import rasterio

        with rasterio.open(str(dem_path)) as src:
            dem_data = src.read(1)
            extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
            if src.nodata is not None:
                dem_data = np.ma.masked_where(dem_data == src.nodata, dem_data)

            terrain_colors = plt.cm.terrain(np.linspace(0.25, 1.0, 256))
            custom_topo = mcolors.LinearSegmentedColormap.from_list(
                "custom_topo", terrain_colors
            )
            custom_topo.set_under("dodgerblue")

            div_norm = mcolors.TwoSlopeNorm(
                vmin=DEM_VMIN, vcenter=DEM_VCENTER, vmax=DEM_VMAX
            )
            dem_layer = ax.imshow(
                dem_data,
                cmap=custom_topo,
                alpha=0.45,
                norm=div_norm,
                extent=extent,
                origin="upper",
                zorder=1,
            )
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(362000, 365000)
            return dem_layer, True

    except Exception as e:
        print(f"  [WARNING] DEM load failed: {e}. Falling back to OSM.")
        return None, False


def load_dem_hillshade(
    ax,
    data_dir: Path,
    alpha: float = 1.0,
    vert_exag: float = 3.0,
    azdeg: float = 315.0,
    altdeg: float = 35.0,
    zorder: int = 1,
):
    """
    Load the site DEM as a greyscale hillshade and render onto ax.

    Uses matplotlib.colors.LightSource to compute an illuminated surface.
    Intended as the base layer for continuous-surface maps (scripts 11b, 19,
    20) where a semi-transparent metric surface is overlaid on top. Contrast
    with load_dem_layer() which uses a coloured terrain colormap and is suited
    to point-symbol maps.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    data_dir : Path
        Directory containing newborough_dem.tif.
    alpha : float
        Opacity of the hillshade layer (default 1.0 — fully opaque base).
    vert_exag : float
        Vertical exaggeration for the hillshade (default 3.0).
    azdeg : float
        Azimuth of the light source in degrees (default 315 — NW).
    altdeg : float
        Altitude of the light source in degrees (default 35).
    zorder : int
        Drawing order (default 1 — bottom layer).

    Returns
    -------
    hs_mesh : QuadMesh or None
        The pcolormesh layer. None if DEM unavailable.
    dem_loaded : bool
    dem_e_arr : np.ndarray or None
        1-D array of easting coordinates matching DEM columns.
    dem_n_arr : np.ndarray or None
        1-D array of northing coordinates matching DEM rows (top to bottom).
    dem_data : np.ndarray or None
        2-D DEM elevation array (NaN where nodata). Returned so callers can
        use it for ridge masking without re-reading the file.
    """
    dem_path = data_dir / "newborough_dem.tif"
    if not dem_path.exists():
        print(f"  [WARNING] DEM not found at {dem_path}")
        return None, False, None, None, None

    try:
        import rasterio

        with rasterio.open(str(dem_path)) as src:
            raw = src.read(1).astype(float)
            transform = src.transform
            res_x = abs(transform.a)
            res_y = abs(transform.e)
            dem_e_arr = transform.c + np.arange(raw.shape[1]) * transform.a
            dem_n_arr = transform.f + np.arange(raw.shape[0]) * transform.e
            if src.nodata is not None:
                raw[raw == src.nodata] = np.nan

        dem_data = raw.copy()
        # Fill NaN for hillshade computation (NaN produces artefacts)
        filled = np.nan_to_num(raw, nan=0.0)

        ls = LightSource(azdeg=azdeg, altdeg=altdeg)
        hs = ls.hillshade(filled, vert_exag=vert_exag, dx=res_x, dy=res_y)

        DEM_E, DEM_N = np.meshgrid(dem_e_arr, dem_n_arr)
        hs_mesh = ax.pcolormesh(
            DEM_E, DEM_N, hs,
            cmap="gray", shading="auto",
            vmin=0.2, vmax=1.0,
            alpha=alpha, zorder=zorder,
        )
        return hs_mesh, True, dem_e_arr, dem_n_arr, dem_data

    except Exception as exc:
        print(f"  [WARNING] Hillshade load failed: {exc}")
        return None, False, None, None, None


def add_idw_surface(
    ax,
    df: pd.DataFrame,
    value_col: str,
    easting_col: str = "E",
    northing_col: str = "N",
    dem_col: str = "dem",
    xi: np.ndarray = None,
    yi: np.ndarray = None,
    method: str = "linear",
    ridge_mask_threshold: float = 1.0,
    dem_e_arr: np.ndarray = None,
    dem_n_arr: np.ndarray = None,
    dem_data: np.ndarray = None,
    cmap=None,
    norm=None,
    alpha: float = 0.65,
    zorder: int = 2,
    vmin: float = None,
    vmax: float = None,
):
    """
    Interpolate a per-well metric to a regular grid and render as pcolormesh.

    Applies an optional ridge mask: grid cells where the DEM raster elevation
    exceeds the IDW-interpolated well-DEM surface by more than
    ``ridge_mask_threshold`` metres are masked (set to NaN). This correctly
    removes inter-dune ridge areas that lie between wells and are not
    ecologically representative of the interpolated value.

    The caller is responsible for attaching a colorbar and drawing contours
    using the returned objects.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    df : DataFrame
        Must contain easting_col, northing_col, value_col. If ridge masking is
        requested, must also contain dem_col (the well ground elevation).
    value_col : str
        Column to interpolate.
    easting_col, northing_col : str
        Coordinate columns (default 'E', 'N').
    dem_col : str
        Well DEM elevation column used to build the IDW well-surface for ridge
        masking (default 'dem'). Ignored if dem_data is None.
    xi, yi : np.ndarray
        1-D arrays defining the interpolation grid. Defaults to
        np.arange(240200, 243800, 50) and np.arange(362200, 365800, 50).
    method : str
        scipy.interpolate.griddata method ('linear', 'nearest', 'cubic').
    ridge_mask_threshold : float
        Metres above IDW well surface at which a grid cell is considered a
        dune ridge and masked. Set to None to disable masking.
    dem_e_arr, dem_n_arr : np.ndarray or None
        DEM coordinate arrays from load_dem_hillshade(). Required for ridge
        masking; if None masking is skipped.
    dem_data : np.ndarray or None
        2-D DEM elevation array from load_dem_hillshade(). Required for ridge
        masking; if None masking is skipped.
    cmap : colormap or str
        Passed to pcolormesh.
    norm : matplotlib.colors.Normalize or None
        Passed to pcolormesh. If None, vmin/vmax are used.
    alpha : float
        Opacity of the surface (default 0.65).
    zorder : int
        Drawing order (default 2 — above hillshade, below wells/legend).
    vmin, vmax : float or None
        Colour scale limits used when norm is None.

    Returns
    -------
    mesh : QuadMesh
        The pcolormesh object for colorbar attachment.
    gx : np.ndarray
        2-D grid easting coordinates.
    gy : np.ndarray
        2-D grid northing coordinates.
    surf_masked : np.ndarray
        The interpolated surface after ridge masking (NaN where masked).
    """
    if xi is None:
        xi = np.arange(240200, 243800, 50)
    if yi is None:
        yi = np.arange(362200, 365800, 50)

    gx, gy = np.meshgrid(xi, yi)
    pts = df[[easting_col, northing_col]].values

    surf = griddata(pts, df[value_col].values, (gx, gy), method=method)

    # ── Ridge masking ──────────────────────────────────────────────────────
    surf_masked = surf.copy()
    if (ridge_mask_threshold is not None
            and dem_e_arr is not None
            and dem_n_arr is not None
            and dem_data is not None
            and dem_col in df.columns):

        # IDW-interpolate well DEM elevations to the same grid
        surf_dem = griddata(pts, df[dem_col].values, (gx, gy), method=method)

        # Resample DEM raster to grid resolution
        dem_interp = RegularGridInterpolator(
            (dem_n_arr[::-1], dem_e_arr),
            dem_data[::-1, :],
            method="linear",
            bounds_error=False,
            fill_value=np.nan,
        )
        dem_at_grid = dem_interp(
            np.column_stack([gy.ravel(), gx.ravel()])
        ).reshape(gx.shape)

        ridge_mask = (dem_at_grid - surf_dem) > ridge_mask_threshold
        surf_masked = np.where(ridge_mask, np.nan, surf)

    # ── Render ────────────────────────────────────────────────────────────
    kwargs = dict(shading="auto", alpha=alpha, zorder=zorder)
    if norm is not None:
        kwargs["norm"] = norm
        if cmap is not None:
            kwargs["cmap"] = cmap
    else:
        if cmap is not None:
            kwargs["cmap"] = cmap
        if vmin is not None:
            kwargs["vmin"] = vmin
        if vmax is not None:
            kwargs["vmax"] = vmax

    mesh = ax.pcolormesh(gx, gy, surf_masked, **kwargs)
    return mesh, gx, gy, surf_masked


def add_osm_basemap(ax, gdf):
    """Add an OpenStreetMap basemap as a fallback when the DEM is unavailable."""
    ctx.add_basemap(
        ax,
        crs=gdf.crs.to_string(),
        source=ctx.providers.OpenStreetMap.Mapnik,
        zorder=1,
        alpha=0.7,
    )


def add_kml_features(ax, data_dir: Path, include_streams: bool = True):
    """
    Overlay site feature KML layers onto ax.

    Draws Features.kml (lakes, forest boundary, broadleaf restock block, other features),
    streams.kml (if include_streams=True), and clearfell.kml. Returns a deduplicated list of
    Line2D legend handles for the layers actually drawn.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    data_dir : Path
    include_streams : bool, optional (default True)
        If False, streams.kml is not overlaid. Useful for maps where the
        drainage network would clutter the display.

    Returns
    -------
    site_feature_handles : list of Line2D
    """
    site_feature_handles = []

    features_path = data_dir / "Features.kml"
    if features_path.exists():
        gdf_features = _safe_read_kml(features_path)
        if gdf_features is not None:
            gdf_features.set_crs(epsg=4326, inplace=True, allow_override=True)
            gdf_features = gdf_features.to_crs("EPSG:27700")
            feature_text = (
                gdf_features.get("Name", pd.Series("", index=gdf_features.index))
                .fillna("")
                .astype(str)
            )
            lake_mask = feature_text.str.contains("lake|llyn|rhos", case=False, na=False)
            forest_mask = feature_text.str.contains(
                "forest|plantation|wood|boundary", case=False, na=False
            )
            broadleaf_mask = (
                feature_text.str.contains("broadleaf|restock", case=False, na=False) |
                gdf_features.get("description", pd.Series("", index=gdf_features.index))
                    .fillna("").astype(str)
                    .str.contains("broadleaf|restock", case=False, na=False)
            )
            gdf_features[~(lake_mask | forest_mask | broadleaf_mask)].plot(
                ax=ax, facecolor="none", edgecolor="black",
                linewidth=1.3, linestyle="--", zorder=2,
            )
            gdf_features[forest_mask].plot(
                ax=ax, facecolor="none", edgecolor="purple", linewidth=2.2, zorder=2
            )
            gdf_features[lake_mask].plot(
                ax=ax, facecolor="dodgerblue", edgecolor="dodgerblue",
                linewidth=1.8, alpha=0.25, zorder=2,
            )
            if broadleaf_mask.any():
                gdf_features[broadleaf_mask].plot(
                    ax=ax, facecolor="none", edgecolor="#228B22",
                    linewidth=2.0, linestyle="--", zorder=2,
                )
                site_feature_handles.append(
                    Line2D([0], [0], color="#228B22", linestyle="--",
                           linewidth=2.0, label="Broadleaf restocking block")
                )
            site_feature_handles.append(
                Line2D([0], [0], color="black", linestyle="--",
                       linewidth=1.6, label="Other Site Features")
            )
            site_feature_handles.append(
                Line2D([0], [0], color="purple", linestyle="-",
                       linewidth=2.2, label="Forest Boundary")
            )

    streams_path = data_dir / "streams.kml"
    if include_streams and streams_path.exists():
        gdf_streams = _safe_read_kml(streams_path)
        if gdf_streams is not None and not gdf_streams.empty:
            if gdf_streams.crs is None:
                gdf_streams.set_crs(epsg=4326, inplace=True)
            gdf_streams.to_crs("EPSG:27700").plot(
                ax=ax, facecolor="none", edgecolor="dodgerblue", linewidth=1.8, zorder=2
            )
            site_feature_handles.append(
                Line2D([0], [0], color="dodgerblue", linestyle="-",
                       linewidth=1.8, label="DEM-derived flow network and boundary")
            )

    clearfell_path = data_dir / "clearfell.kml"
    if clearfell_path.exists():
        gdf_clearfell = _safe_read_kml(clearfell_path)
        if gdf_clearfell is not None:
            if gdf_clearfell.crs is None:
                gdf_clearfell.set_crs(epsg=4326, inplace=True)
            gdf_clearfell.to_crs("EPSG:27700").plot(
                ax=ax, facecolor="none", edgecolor="darkorange",
                linewidth=2.2, linestyle="-.", zorder=2,
            )
            site_feature_handles.append(
                Line2D([0], [0], color="darkorange", linestyle="-.",
                       linewidth=2.2, label="Felling Area")
            )

    # Deduplicate by label
    dedup = {}
    for handle in site_feature_handles:
        dedup[handle.get_label()] = handle
    return list(dedup.values())


def plot_metric_map(
    map_df,
    value_col: str,
    title: str,
    output_path: Path,
    cmap: str,
    data_dir: Path,
    vmin=None,
    vmax=None,
):
    """
    Publication-quality spatial metric map.

    Renders well locations as cluster-shaped markers coloured by a numeric
    metric, over a DEM background with KML overlays. Produces dual colorbars
    (metric + elevation) and a cluster shape legend.

    Parameters
    ----------
    map_df : DataFrame
        Must contain columns: Easting, Northing, value_col.
        Optional: Cluster_ID (int 1-6).
    value_col : str
        Column in map_df to colour the markers by.
    title : str
    output_path : Path
    cmap : str
        Matplotlib colormap name. Diverging cmaps recommended for difference metrics.
    data_dir : Path
    vmin, vmax : float, optional
        Explicit colour scale limits. If None, inferred from data.
    """
    map_df = map_df.copy()
    required_cols = ["Easting", "Northing", value_col]
    missing_required = [c for c in required_cols if c not in map_df.columns]
    if missing_required:
        print(
            f"  [WARNING] Missing columns for map: {missing_required}. "
            f"Skipping {output_path.name}"
        )
        return

    if "Cluster_ID" not in map_df.columns:
        map_df["Cluster_ID"] = 1

    valid = map_df.dropna(subset=["Easting", "Northing", value_col]).copy()
    valid["Cluster_ID"] = (
        pd.to_numeric(valid["Cluster_ID"], errors="coerce").fillna(1).astype(int)
    )
    if valid.empty:
        print(
            f"  [WARNING] No mappable data for {value_col}. Skipping {output_path.name}"
        )
        return

    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)

    dem_layer, dem_loaded = load_dem_layer(ax, data_dir)
    if not dem_loaded:
        gdf_tmp = gpd.GeoDataFrame(
            valid,
            geometry=gpd.points_from_xy(valid.Easting, valid.Northing),
            crs="EPSG:27700",
        )
        add_osm_basemap(ax, gdf_tmp)

    site_feature_handles = add_kml_features(ax, data_dir)

    # Colour scaling
    is_intercept = "intercept" in value_col.lower()
    is_nse = value_col.lower().startswith("nse") or "penalty" in value_col.lower()

    if is_intercept:
        if vmin is not None and vmax is not None:
            norm = mcolors.TwoSlopeNorm(vmin=float(vmin), vcenter=0.0, vmax=float(vmax))
        else:
            max_abs = np.nanpercentile(
                np.abs(valid[value_col].to_numpy(dtype=float)), 99
            )
            max_abs = max(float(max_abs) * 1.15, 0.08)
            norm = mcolors.TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)
        scatter_norm = norm
        scatter_vmin = scatter_vmax = None
    elif is_nse:
        _vmin = valid[value_col].min() if vmin is None else vmin
        _vmax = valid[value_col].max() if vmax is None else vmax
        center = 0 if _vmin < 0 < _vmax else (_vmin + _vmax) / 2
        norm = mcolors.TwoSlopeNorm(vmin=_vmin, vcenter=center, vmax=_vmax)
        scatter_norm = norm
        scatter_vmin = scatter_vmax = None
        cmap = "RdYlBu"
    else:
        scatter_norm = None
        scatter_vmin = vmin
        scatter_vmax = vmax

    handles = []
    sc = None
    for cluster_id in sorted(valid["Cluster_ID"].dropna().unique()):
        marker = CLUSTER_MARKERS.get(int(cluster_id), "o")
        cluster_points = valid[valid["Cluster_ID"] == cluster_id]
        sc = ax.scatter(
            cluster_points["Easting"],
            cluster_points["Northing"],
            c=cluster_points[value_col],
            cmap=cmap,
            s=120,
            marker=marker,
            edgecolor="black",
            linewidth=0.6,
            alpha=0.9,
            norm=scatter_norm,
            vmin=scatter_vmin,
            vmax=scatter_vmax,
            zorder=5,
        )
        handles.append(
            plt.Line2D(
                [0], [0],
                marker=marker, color="w",
                label=CLUSTER_LABELS.get(int(cluster_id), f"C{int(cluster_id)}"),
                markerfacecolor="gray", markeredgecolor="black",
                markersize=12, linestyle="None",
            )
        )

    if sc is None:
        plt.close(fig)
        return

    divider = make_axes_locatable(ax)
    cax_metric = divider.append_axes("right", size="2.75%", pad=0.598)
    cbar = fig.colorbar(sc, cax=cax_metric)
    cbar.set_label(value_col.replace("_", " "), rotation=270, labelpad=32, fontsize=14)

    if dem_layer is not None:
        cax_dem = divider.append_axes("right", size="2.75%", pad=1.306)
        cbar_dem = fig.colorbar(dem_layer, cax=cax_dem, extend="both")
        cbar_dem.set_label("Elevation (m AOD)", rotation=270, labelpad=32, fontsize=14)

    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_aspect("equal", adjustable="box")

    cluster_legend = ax.legend(
        handles=handles, title="Core Cluster Assignments",
        loc="lower left", frameon=True,
    )
    ax.add_artist(cluster_legend)

    if site_feature_handles:
        ax.legend(
            handles=site_feature_handles, title="Site Features",
            loc="upper right", frameon=True,
        )

    plt.subplots_adjust(left=0.08, right=0.99, top=0.93, bottom=0.08)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
