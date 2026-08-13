import pandas as pd
import pytest

from arinc424.models.airways import df_to_airways


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_airways(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "AirwayIdentifier": "A1",
                "FromWaypoint": "WP01",
                "ToWaypoint": "WP02",
                "MinimumAltitude": "3000",
                "MaximumAltitude": "12000",
                "AirwayType": "RNAV",
                "AirwayDirection": "B",
                "CycleDate": "2401",
            }
        ]
    )

    airways = df_to_airways(df)
    assert len(airways) == 1

    a = airways[0]
    assert a.airway_identifier == "A1"
    assert a.from_waypoint == "WP01"
    assert a.to_waypoint == "WP02"
    assert a.minimum_altitude == "3000"
    assert a.maximum_altitude == "12000"
    assert a.airway_type == "RNAV"
    assert a.airway_direction == "B"
    assert a.cycle_date == "2401"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "AirwayIdentifier": "A2",
                # Everything else missing
            }
        ]
    )

    a = df_to_airways(df)[0]

    assert a.airway_identifier == "A2"
    assert a.from_waypoint == ""
    assert a.to_waypoint == ""
    assert a.minimum_altitude == ""
    assert a.maximum_altitude == ""
    assert a.airway_type == ""
    assert a.airway_direction == ""
    assert a.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "AirwayIdentifier": " A3 ",
                "FromWaypoint": " WP01 ",
                "ToWaypoint": " WP02 ",
                "MinimumAltitude": " 3000 ",
                "MaximumAltitude": " 12000 ",
                "AirwayType": " RNAV ",
                "AirwayDirection": " B ",
                "CycleDate": " 2401 ",
            }
        ]
    )

    a = df_to_airways(df)[0]

    assert a.airway_identifier == "A3"
    assert a.from_waypoint == "WP01"
    assert a.to_waypoint == "WP02"
    assert a.minimum_altitude == "3000"
    assert a.maximum_altitude == "12000"
    assert a.airway_type == "RNAV"
    assert a.airway_direction == "B"
    assert a.cycle_date == "2401"


@pytest.mark.parametrize(
    "field,attr",
    [
        ("MinimumAltitude", "minimum_altitude"),
        ("MaximumAltitude", "maximum_altitude"),
        ("AirwayType", "airway_type"),
        ("AirwayDirection", "airway_direction"),
    ],
)
def test_nan_values_become_empty_strings(field, attr):
    df = make_df(
        [
            {
                "AirwayIdentifier": "A4",
                field: float("nan"),
            }
        ]
    )

    a = df_to_airways(df)[0]
    assert getattr(a, attr) == ""


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"AirwayIdentifier": "A", "FromWaypoint": "W1"},
            {"AirwayIdentifier": "B", "FromWaypoint": "W2"},
            {"AirwayIdentifier": "C", "FromWaypoint": "W3"},
        ]
    )

    airways = df_to_airways(df)

    assert len(airways) == 3
    assert [a.airway_identifier for a in airways] == ["A", "B", "C"]
    assert [a.from_waypoint for a in airways] == ["W1", "W2", "W3"]
