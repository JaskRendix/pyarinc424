import pandas as pd
import pytest

from arinc424.models.airway_restrictions import df_to_airway_restrictions


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_airway_restrictions(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "AirwayIdentifier": "A1",
                "FromWaypoint": "WP01",
                "ToWaypoint": "WP02",
                "MinimumAltitude": "3000",
                "MaximumAltitude": "12000",
                "RNAVRequirement": "RNP1",
                "CycleDate": "2401",
            }
        ]
    )

    res = df_to_airway_restrictions(df)
    assert len(res) == 1

    r = res[0]
    assert r.airway_identifier == "A1"
    assert r.from_waypoint == "WP01"
    assert r.to_waypoint == "WP02"
    assert r.minimum_altitude == "3000"
    assert r.maximum_altitude == "12000"
    assert r.rnav_requirement == "RNP1"
    assert r.cycle_date == "2401"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "AirwayIdentifier": "A2",
                # Everything else missing
            }
        ]
    )

    r = df_to_airway_restrictions(df)[0]

    assert r.airway_identifier == "A2"
    assert r.from_waypoint == ""
    assert r.to_waypoint == ""
    assert r.minimum_altitude == ""
    assert r.maximum_altitude == ""
    assert r.rnav_requirement == ""
    assert r.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "AirwayIdentifier": " A3 ",
                "FromWaypoint": " WP01 ",
                "ToWaypoint": " WP02 ",
                "MinimumAltitude": " 3000 ",
                "MaximumAltitude": " 12000 ",
                "RNAVRequirement": " RNP1 ",
                "CycleDate": " 2401 ",
            }
        ]
    )

    r = df_to_airway_restrictions(df)[0]

    assert r.airway_identifier == "A3"
    assert r.from_waypoint == "WP01"
    assert r.to_waypoint == "WP02"
    assert r.minimum_altitude == "3000"
    assert r.maximum_altitude == "12000"
    assert r.rnav_requirement == "RNP1"
    assert r.cycle_date == "2401"


@pytest.mark.parametrize(
    "field,attr",
    [
        ("MinimumAltitude", "minimum_altitude"),
        ("MaximumAltitude", "maximum_altitude"),
        ("RNAVRequirement", "rnav_requirement"),
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

    r = df_to_airway_restrictions(df)[0]
    assert getattr(r, attr) == ""


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"AirwayIdentifier": "A", "FromWaypoint": "W1"},
            {"AirwayIdentifier": "B", "FromWaypoint": "W2"},
            {"AirwayIdentifier": "C", "FromWaypoint": "W3"},
        ]
    )

    res = df_to_airway_restrictions(df)

    assert len(res) == 3
    assert [r.airway_identifier for r in res] == ["A", "B", "C"]
    assert [r.from_waypoint for r in res] == ["W1", "W2", "W3"]
