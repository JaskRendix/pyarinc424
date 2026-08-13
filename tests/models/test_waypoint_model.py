import pandas as pd
import pytest

from arinc424.models.waypoints import df_to_waypoints


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_waypoints(df) == []


def test_basic_conversion_with_standard_columns():
    df = make_df(
        [
            {
                "WaypointIdentifier": "ABC",
                "Latitude_decimal": 10.0,
                "Longitude_decimal": 20.0,
                "WaypointType": "NDB",
                "WaypointUsage": "ENRT",
                "CycleDate": "2401",
            }
        ]
    )

    result = df_to_waypoints(df)
    assert len(result) == 1

    wp = result[0]
    assert wp.identifier == "ABC"
    assert wp.latitude == 10.0
    assert wp.longitude == 20.0
    assert wp.waypoint_type == "NDB"
    assert wp.usage == "ENRT"
    assert wp.cycle_date == "2401"


@pytest.mark.parametrize(
    "ident_col,type_col,usage_col",
    [
        ("FixIdentifier", "FixType", "FixUsage"),
        ("PointIdentifier", "PointType", "PointUsage"),
        ("SomeIdentifier", "SomeType", "SomeUsage"),
    ],
)
def test_dynamic_column_detection(ident_col, type_col, usage_col):
    df = make_df(
        [
            {
                ident_col: "XYZ",
                type_col: "VFR",
                usage_col: "TMA",
                "Latitude_decimal": 45.0,
                "Longitude_decimal": 9.0,
                "CycleDate": "2402",
            }
        ]
    )

    result = df_to_waypoints(df)
    wp = result[0]

    assert wp.identifier == "XYZ"
    assert wp.waypoint_type == "VFR"
    assert wp.usage == "TMA"
    assert wp.latitude == 45.0
    assert wp.longitude == 9.0
    assert wp.cycle_date == "2402"


def test_fallback_to_non_decimal_coordinates():
    df = make_df(
        [
            {
                "WaypointIdentifier": "AAA",
                "Latitude": 12.34,
                "Longitude": 56.78,
                "WaypointType": "RNAV",
                "WaypointUsage": "ENRT",
                "CycleDate": "2403",
            }
        ]
    )

    wp = df_to_waypoints(df)[0]
    assert wp.latitude == 12.34
    assert wp.longitude == 56.78


def test_missing_optional_fields_are_empty_strings():
    df = make_df(
        [
            {
                "WaypointIdentifier": "BBB",
                "Latitude_decimal": None,
                "Longitude_decimal": None,
                # Missing type, usage, cycle date
            }
        ]
    )

    wp = df_to_waypoints(df)[0]
    assert wp.identifier == "BBB"
    assert wp.waypoint_type == ""
    assert wp.usage == ""
    assert wp.cycle_date == ""
    assert wp.latitude is None
    assert wp.longitude is None


def test_stripping_whitespace_in_fields():
    df = make_df(
        [
            {
                "WaypointIdentifier": "  CDE  ",
                "WaypointType": " RNAV ",
                "WaypointUsage": " ENRT ",
                "Latitude_decimal": 1.0,
                "Longitude_decimal": 2.0,
                "CycleDate": " 2404 ",
            }
        ]
    )

    wp = df_to_waypoints(df)[0]
    assert wp.identifier == "CDE"
    assert wp.waypoint_type == "RNAV"
    assert wp.usage == "ENRT"
    assert wp.cycle_date == "2404"
