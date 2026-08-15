import json

import pandas as pd
import pytest

from arinc424.gis import (
    _ensure_decimal_coords,
    _extract_point,
    _get_properties,
    dataframe_to_geojson,
    df_to_geojson_lines,
    df_to_geojson_points,
    df_to_geojson_polygons,
    save_geojson,
    to_geodataframe,
)


def test_ensure_decimal_coords_existing_columns():
    df = pd.DataFrame({"Latitude": [10], "Longitude": [20]})
    out, lat, lon = _ensure_decimal_coords(df, "Latitude", "Longitude")
    assert lat == "Latitude"
    assert lon == "Longitude"
    assert out.equals(df)


def test_ensure_decimal_coords_decimal_fallback(monkeypatch):
    def fake_decoder(df):
        df["Lat_decimal"] = df["Lat"] + 0.5
        df["Lon_decimal"] = df["Lon"] + 0.5
        return df

    monkeypatch.setattr("arinc424.gis.apply_decoders", fake_decoder)

    df = pd.DataFrame({"Lat": [10], "Lon": [20]})
    out, lat, lon = _ensure_decimal_coords(df, "Lat", "Lon")

    assert lat == "Lat_decimal"
    assert lon == "Lon_decimal"
    assert "Lat_decimal" in out.columns
    assert "Lon_decimal" in out.columns


@pytest.mark.parametrize(
    "row,lat,lon,expected",
    [
        (
            pd.Series({"Latitude": 10, "Longitude": 20}),
            "Latitude",
            "Longitude",
            [20, 10],
        ),
        (pd.Series({"Latitude": None, "Longitude": 20}), "Latitude", "Longitude", None),
        (
            pd.Series({"Latitude": "bad", "Longitude": 20}),
            "Latitude",
            "Longitude",
            None,
        ),
        (pd.Series({"Latitude": 10, "Longitude": None}), "Latitude", "Longitude", None),
    ],
)
def test_extract_point(row, lat, lon, expected):
    assert _extract_point(row, lat, lon) == expected


def test_get_properties_excludes_and_converts():
    row = pd.Series(
        {
            "Latitude": 10,
            "Longitude": 20,
            "Name": "Test",
            "Value": pd.Series([5]).iloc[0],
            "Empty": "",
            "NaN": float("nan"),
        }
    )
    props = _get_properties(row, {"Latitude", "Longitude"})
    assert props == {"Name": "Test", "Value": 5}


def test_df_to_geojson_points_basic():
    df = pd.DataFrame({"Latitude": [10], "Longitude": [20], "Name": ["A"]})
    gj = df_to_geojson_points(df)
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) == 1
    f = gj["features"][0]
    assert f["geometry"]["coordinates"] == [20, 10]
    assert f["properties"]["Name"] == "A"


def test_df_to_geojson_points_include_fields():
    df = pd.DataFrame({"Latitude": [10], "Longitude": [20], "A": 1, "B": 2})
    gj = df_to_geojson_points(df, include_fields=["A"])
    props = gj["features"][0]["properties"]
    assert props == {"A": 1}


def test_df_to_geojson_points_skips_invalid():
    df = pd.DataFrame({"Latitude": [10, None], "Longitude": [20, 30]})
    gj = df_to_geojson_points(df)
    assert len(gj["features"]) == 1


def test_df_to_geojson_lines_grouped():
    df = pd.DataFrame(
        {
            "RouteIdentifier": ["R1", "R1", "R1"],
            "SequenceNumber": [2, 1, 3],
            "Latitude": [10, 11, 12],
            "Longitude": [20, 21, 22],
        }
    )
    gj = df_to_geojson_lines(df)
    coords = gj["features"][0]["geometry"]["coordinates"]
    assert coords == [[21, 11], [20, 10], [22, 12]] or coords == [
        [20, 10],
        [21, 11],
        [22, 12],
    ]


def test_df_to_geojson_lines_no_group():
    df = pd.DataFrame({"Latitude": [10, 11], "Longitude": [20, 21]})
    gj = df_to_geojson_lines(df)
    assert len(gj["features"]) == 1
    assert gj["features"][0]["geometry"]["type"] == "LineString"


def test_df_to_geojson_lines_insufficient_points():
    df = pd.DataFrame({"Latitude": [10], "Longitude": [20]})
    gj = df_to_geojson_lines(df)
    assert gj["features"] == []


def test_df_to_geojson_polygons_grouped():
    df = pd.DataFrame(
        {
            "AirspaceCenter": ["A", "A", "A"],
            "SequenceNumber": [2, 1, 3],
            "Latitude": [10, 11, 12],
            "Longitude": [20, 21, 22],
        }
    )
    gj = df_to_geojson_polygons(df)
    coords = gj["features"][0]["geometry"]["coordinates"][0]
    assert coords[0] == coords[-1]


def test_df_to_geojson_polygons_no_group():
    df = pd.DataFrame(
        {
            "Latitude": [10, 11, 12],
            "Longitude": [20, 21, 22],
        }
    )
    gj = df_to_geojson_polygons(df)
    coords = gj["features"][0]["geometry"]["coordinates"][0]
    assert coords[0] == coords[-1]


def test_df_to_geojson_polygons_insufficient_points():
    df = pd.DataFrame({"Latitude": [10, 11], "Longitude": [20, 21]})
    gj = df_to_geojson_polygons(df)
    assert gj["features"] == []


@pytest.mark.parametrize(
    "schema,cols,expected",
    [
        ("Airways", [], "linestring"),
        ("ProcedureLegs", [], "linestring"),
        ("CompanyRoutes", [], "linestring"),
        ("Airspaces", [], "polygon"),
        ("AirspaceBoundaries", [], "polygon"),
        (None, ["RouteIdentifier"], "linestring"),
        (
            None,
            ["AirspaceCenter"],
            "linestring",
        ),  # Grouped/ungrouped line detection fallback
        (None, [], "point"),
    ],
)
def test_dataframe_to_geojson_auto(schema, cols, expected):
    num_rows = 3 if expected in ("linestring", "polygon") else 1
    data = {
        "Latitude": [10, 11, 12][:num_rows],
        "Longitude": [20, 21, 22][:num_rows],
        "RouteIdentifier": ["R1"] * num_rows,
        "AirspaceCenter": ["A"] * num_rows,
    }
    for c in cols:
        if c not in data:
            data[c] = ["A"] * num_rows

    df = pd.DataFrame(data)
    gj = dataframe_to_geojson(df, schema_name=schema)
    if expected == "point":
        assert len(gj["features"]) == 1
    else:
        assert gj["features"]
    assert gj["features"][0]["geometry"]["type"].lower() in (
        expected,
        "linestring" if expected == "line" else expected,
    )


def test_save_geojson(tmp_path):
    data = {"type": "FeatureCollection", "features": []}
    out = tmp_path / "test.json"
    save_geojson(data, out)
    assert out.exists()
    with open(out) as f:
        assert json.load(f) == data


def test_to_geodataframe_basic():
    try:
        import geopandas as gpd
    except ImportError:
        pytest.skip("geopandas not installed")

    df = pd.DataFrame({"Latitude": [10], "Longitude": [20], "Name": ["A"]})
    gdf = to_geodataframe(df)
    assert len(gdf) == 1
    assert gdf.geometry.iloc[0].x == 20
    assert gdf.geometry.iloc[0].y == 10
