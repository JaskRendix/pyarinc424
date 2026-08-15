from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from .utils import apply_decoders


def _ensure_decimal_coords(
    df: pd.DataFrame, lat_col: str, lon_col: str
) -> tuple[pd.DataFrame, str, str]:
    """Ensure decimal latitude and longitude columns exist in the DataFrame."""
    out_df = df.copy()

    dec_lat = f"{lat_col}_decimal"
    dec_lon = f"{lon_col}_decimal"

    # If decimal columns already exist, use them
    if dec_lat in out_df.columns and dec_lon in out_df.columns:
        return out_df, dec_lat, dec_lon

    # If standard columns already exist and no decimal fallback is needed
    if (
        lat_col == "Latitude"
        and lon_col == "Longitude"
        and lat_col in out_df.columns
        and lon_col in out_df.columns
    ):
        return out_df, lat_col, lon_col

    # Otherwise, apply decoders if needed
    if dec_lat not in out_df.columns or dec_lon not in out_df.columns:
        try:
            out_df = apply_decoders(out_df)
        except Exception:
            pass

    if dec_lat in out_df.columns:
        lat_col = dec_lat
    if dec_lon in out_df.columns:
        lon_col = dec_lon

    return out_df, lat_col, lon_col


def _extract_point(row: pd.Series, lat_col: str, lon_col: str) -> list[float] | None:
    """Extract valid GeoJSON [longitude, latitude] pair from a row."""
    try:
        lat = float(row[lat_col])
        lon = float(row[lon_col])
        if pd.isna(lat) or pd.isna(lon):
            return None
        # GeoJSON uses [longitude, latitude] order
        return [round(lon, 6), round(lat, 6)]
    except (KeyError, ValueError, TypeError):
        return None


def _get_properties(row: pd.Series, exclude_cols: set[str]) -> dict[str, Any]:
    """Extract non-coordinate row attributes for GeoJSON feature properties."""
    props = {}
    for col, val in row.items():
        if col in exclude_cols or pd.isna(val) or val == "":
            continue
        if hasattr(val, "item"):  # numpy types to native python
            val = val.item()
        props[str(col)] = val
    return props


def df_to_geojson_points(
    df: pd.DataFrame,
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
    include_fields: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Convert point records (Waypoints, Navaids, Airports) into a GeoJSON FeatureCollection.

    GeoJSON Geometry: Point ([longitude, latitude])
    """
    df, lat_col, lon_col = _ensure_decimal_coords(df, lat_col, lon_col)
    features: list[dict[str, Any]] = []

    for _, row in df.iterrows():
        coord = _extract_point(row, lat_col, lon_col)
        if not coord:
            continue

        if include_fields:
            props = {
                k: row[k]
                for k in include_fields
                if k in row and pd.notna(row[k]) and row[k] != ""
            }
        else:
            props = _get_properties(row, {lat_col, lon_col, "Latitude", "Longitude"})

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coord},
                "properties": props,
            }
        )

    return {"type": "FeatureCollection", "features": features}


def df_to_geojson_lines(
    df: pd.DataFrame,
    group_col: str = "RouteIdentifier",
    seq_col: str = "SequenceNumber",
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
) -> dict[str, Any]:
    """Convert sequence records (Airways, Procedures, Company Routes) into LineString features.

    GeoJSON Geometry: LineString ([[lon1, lat1], [lon2, lat2], ...])
    """
    df, lat_col, lon_col = _ensure_decimal_coords(df, lat_col, lon_col)

    if group_col not in df.columns:
        coords = [
            pt for _, r in df.iterrows() if (pt := _extract_point(r, lat_col, lon_col))
        ]
        if len(coords) < 2:
            return {"type": "FeatureCollection", "features": []}

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {},
                }
            ],
        }

    if seq_col in df.columns:
        df = df.copy()
        df[seq_col] = pd.to_numeric(df[seq_col], errors="coerce").fillna(0)
        df = df.sort_values(by=[group_col, seq_col])

    features: list[dict[str, Any]] = []

    for route_id, group in df.groupby(group_col, sort=False):
        coords: list[list[float]] = []
        for _, row in group.iterrows():
            pt = _extract_point(row, lat_col, lon_col)
            if pt:
                coords.append(pt)

        if len(coords) < 2:
            continue

        first_row = group.iloc[0]
        props = _get_properties(
            first_row,
            {lat_col, lon_col, "Latitude", "Longitude", seq_col},
        )
        props[group_col] = str(route_id)
        props["total_legs"] = len(coords) - 1

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": props,
            }
        )

    return {"type": "FeatureCollection", "features": features}


def df_to_geojson_polygons(
    df: pd.DataFrame,
    group_col: str = "AirspaceCenter",
    seq_col: str = "SequenceNumber",
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
) -> dict[str, Any]:
    """Convert boundary records (Airspaces, FIRs/UIRs) into Polygon features.

    GeoJSON Geometry: Polygon ([[[lon1, lat1], ..., [lon1, lat1]]])
    Enforces linear ring closure (first coordinate == last coordinate).
    """
    df, lat_col, lon_col = _ensure_decimal_coords(df, lat_col, lon_col)

    if group_col not in df.columns:
        group_col = "AirspaceIdentifier" if "AirspaceIdentifier" in df.columns else None

    if not group_col:
        coords = [
            pt for _, r in df.iterrows() if (pt := _extract_point(r, lat_col, lon_col))
        ]
        if len(coords) < 3:
            return {"type": "FeatureCollection", "features": []}

        if coords[0] != coords[-1]:
            coords.append(coords[0])

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [coords]},
                    "properties": {},
                }
            ],
        }

    if seq_col in df.columns:
        df = df.copy()
        df[seq_col] = pd.to_numeric(df[seq_col], errors="coerce").fillna(0)
        df = df.sort_values(by=[group_col, seq_col])

    features: list[dict[str, Any]] = []

    for space_id, group in df.groupby(group_col, sort=False):
        coords: list[list[float]] = []
        for _, row in group.iterrows():
            pt = _extract_point(row, lat_col, lon_col)
            if pt:
                coords.append(pt)

        if len(coords) < 3:
            continue

        if coords[0] != coords[-1]:
            coords.append(coords[0])

        first_row = group.iloc[0]
        props = _get_properties(
            first_row,
            {lat_col, lon_col, "Latitude", "Longitude", seq_col},
        )
        props[group_col] = str(space_id)

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coords]},
                "properties": props,
            }
        )

    return {"type": "FeatureCollection", "features": features}


def dataframe_to_geojson(
    df: pd.DataFrame,
    schema_name: str | None = None,
    feature_type: str = "auto",
    **kwargs: Any,
) -> dict[str, Any]:
    """Auto-detect feature type and return a GeoJSON FeatureCollection dictionary.

    feature_type options: 'auto', 'point', 'line', 'polygon'
    """
    if feature_type == "auto":
        if schema_name in {"Airways", "ProcedureLegs", "CompanyRoutes"}:
            feature_type = "line"
        elif schema_name in {"Airspaces", "AirspaceBoundaries"}:
            feature_type = "polygon"
        else:
            cols = set(df.columns)
            # Only auto-detect lines/polygons if there's more than 1 row or it's explicitly structured
            if len(df) > 1:
                if "RouteIdentifier" in cols or "AirwayIdentifier" in cols:
                    feature_type = "line"
                elif "AirspaceCenter" in cols or "AirspaceIdentifier" in cols:
                    feature_type = "polygon"
                else:
                    feature_type = "point"
            else:
                feature_type = "point"

    if feature_type == "line":
        return df_to_geojson_lines(df, **kwargs)
    elif feature_type == "polygon":
        return df_to_geojson_polygons(df, **kwargs)
    else:
        return df_to_geojson_points(df, **kwargs)


def save_geojson(
    geojson_data: dict[str, Any], output_path: str | Path, indent: int = 2
) -> None:
    """Save GeoJSON dictionary to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=indent)


def to_geodataframe(df: pd.DataFrame, schema_name: str | None = None) -> Any:
    """Convert parsed DataFrame to a GeoPandas GeoDataFrame (requires geopandas)."""
    try:
        import geopandas as gpd
        from shapely.geometry import shape
    except ImportError as exc:
        raise ImportError(
            "geopandas and shapely are required for to_geodataframe(). "
            "Install with: pip install geopandas shapely"
        ) from exc

    geojson_dict = dataframe_to_geojson(df, schema_name=schema_name)
    if not geojson_dict["features"]:
        return gpd.GeoDataFrame()

    geometries = [shape(f["geometry"]) for f in geojson_dict["features"]]
    properties = [f["properties"] for f in geojson_dict["features"]]

    return gpd.GeoDataFrame(properties, geometry=geometries, crs="EPSG:4326")
