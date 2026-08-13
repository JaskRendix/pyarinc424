import pandas as pd
import pytest

from arinc424.models.avionics import df_to_general_aviation


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_general_aviation(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "WaypointIdentifier": "WP01",
                "RecordType": "W",
                "SectionCode": "E",
                "SubsectionCode": "A",
                "WaypointLatitude": "45.6300",
                "WaypointLongitude": "8.7200",
                "AirportElevation": "1200",
                "CycleDate": "2401",
            }
        ]
    )

    records = df_to_general_aviation(df)
    assert len(records) == 1

    r = records[0]
    assert r.identifier == "WP01"
    assert r.record_type == "W"
    assert r.section_code == "E"
    assert r.subsection_code == "A"
    assert r.latitude == "45.6300"
    assert r.longitude == "8.7200"
    assert r.elevation == "1200"
    assert r.cycle_date == "2401"


def test_dynamic_identifier_column_navaid_identifier():
    df = make_df(
        [
            {
                "NavaidIdentifier": "NAV123",
                "RecordType": "N",
            }
        ]
    )

    r = df_to_general_aviation(df)[0]
    assert r.identifier == "NAV123"


def test_dynamic_identifier_column_generic_identifier():
    df = make_df(
        [
            {
                "AirportIdentifier": "LIMC",
                "RecordType": "A",
            }
        ]
    )

    r = df_to_general_aviation(df)[0]
    assert r.identifier == "LIMC"


def test_dynamic_lat_lon_elev_columns():
    df = make_df(
        [
            {
                "CustomLatitude": "45.00",
                "CustomLongitude": "9.00",
                "CustomElevation": "500",
                "RecordType": "X",
                "SectionCode": "E",
                "SubsectionCode": "B",
                "CycleDate": "2402",
            }
        ]
    )

    # Rename columns to match dynamic resolution rules
    df = df.rename(
        columns={
            "CustomLatitude": "WaypointLatitude",
            "CustomLongitude": "WaypointLongitude",
            "CustomElevation": "AirportElevation",
        }
    )

    r = df_to_general_aviation(df)[0]

    assert r.latitude == "45.00"
    assert r.longitude == "9.00"
    assert r.elevation == "500"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "WaypointIdentifier": "WPX",
                # Everything else missing
            }
        ]
    )

    r = df_to_general_aviation(df)[0]

    assert r.identifier == "WPX"
    assert r.record_type == ""
    assert r.section_code == ""
    assert r.subsection_code == ""
    assert r.latitude == ""
    assert r.longitude == ""
    assert r.elevation == ""
    assert r.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "WaypointIdentifier": " WP02 ",
                "RecordType": " W ",
                "SectionCode": " E ",
                "SubsectionCode": " A ",
                "WaypointLatitude": " 45.6300 ",
                "WaypointLongitude": " 8.7200 ",
                "AirportElevation": " 1200 ",
                "CycleDate": " 2401 ",
            }
        ]
    )

    r = df_to_general_aviation(df)[0]

    assert r.identifier == "WP02"
    assert r.record_type == "W"
    assert r.section_code == "E"
    assert r.subsection_code == "A"
    assert r.latitude == "45.6300"
    assert r.longitude == "8.7200"
    assert r.elevation == "1200"
    assert r.cycle_date == "2401"


@pytest.mark.parametrize(
    "field,attr",
    [
        ("WaypointLatitude", "latitude"),
        ("WaypointLongitude", "longitude"),
        ("AirportElevation", "elevation"),
    ],
)
def test_nan_values_become_empty_strings(field, attr):
    df = make_df(
        [
            {
                "WaypointIdentifier": "WP03",
                field: float("nan"),
            }
        ]
    )

    r = df_to_general_aviation(df)[0]
    assert getattr(r, attr) == ""


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"WaypointIdentifier": "A", "RecordType": "W"},
            {"WaypointIdentifier": "B", "RecordType": "N"},
            {"WaypointIdentifier": "C", "RecordType": "A"},
        ]
    )

    records = df_to_general_aviation(df)

    assert len(records) == 3
    assert [r.identifier for r in records] == ["A", "B", "C"]
    assert [r.record_type for r in records] == ["W", "N", "A"]
