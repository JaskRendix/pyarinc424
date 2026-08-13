import pandas as pd
import pytest

from arinc424.models.company_route_legs import df_to_company_route_legs


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_company_route_legs(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "CompanyRouteIdentifier": "CR001",
                "SequenceNumber": "01",
                "FixIdentifier": "ABCD",
                "PathTerminator": "IF",
                "Course": "090",
                "Distance": "12.5",
                "AltitudeDescription": "AT",
                "Altitude1": "3000",
                "Altitude2": "5000",
                "SpeedLimit": "210",
                "CycleDate": "2401",
            }
        ]
    )

    legs = df_to_company_route_legs(df)
    assert len(legs) == 1

    leg = legs[0]
    assert leg.company_route_identifier == "CR001"
    assert leg.sequence_number == "01"
    assert leg.fix_identifier == "ABCD"
    assert leg.path_terminator == "IF"
    assert leg.course == "090"
    assert leg.distance == "12.5"
    assert leg.altitude_description == "AT"
    assert leg.altitude_1 == "3000"
    assert leg.altitude_2 == "5000"
    assert leg.speed_limit == "210"
    assert leg.cycle_date == "2401"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "CompanyRouteIdentifier": "CRX",
                # Everything else missing
            }
        ]
    )

    leg = df_to_company_route_legs(df)[0]

    assert leg.company_route_identifier == "CRX"
    assert leg.sequence_number == ""
    assert leg.fix_identifier == ""
    assert leg.path_terminator == ""
    assert leg.course == ""
    assert leg.distance == ""
    assert leg.altitude_description == ""
    assert leg.altitude_1 == ""
    assert leg.altitude_2 == ""
    assert leg.speed_limit == ""
    assert leg.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "CompanyRouteIdentifier": " CR002 ",
                "SequenceNumber": " 02 ",
                "FixIdentifier": " FIX1 ",
                "PathTerminator": " IF ",
                "Course": " 180 ",
                "Distance": " 7.0 ",
                "AltitudeDescription": " AT ",
                "Altitude1": " 2000 ",
                "Altitude2": " 4000 ",
                "SpeedLimit": " 180 ",
                "CycleDate": " 2402 ",
            }
        ]
    )

    leg = df_to_company_route_legs(df)[0]

    assert leg.company_route_identifier == "CR002"
    assert leg.sequence_number == "02"
    assert leg.fix_identifier == "FIX1"
    assert leg.path_terminator == "IF"
    assert leg.course == "180"
    assert leg.distance == "7.0"
    assert leg.altitude_description == "AT"
    assert leg.altitude_1 == "2000"
    assert leg.altitude_2 == "4000"
    assert leg.speed_limit == "180"
    assert leg.cycle_date == "2402"


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"CompanyRouteIdentifier": "A", "SequenceNumber": "01"},
            {"CompanyRouteIdentifier": "B", "SequenceNumber": "02"},
            {"CompanyRouteIdentifier": "C", "SequenceNumber": "03"},
        ]
    )

    legs = df_to_company_route_legs(df)

    assert len(legs) == 3
    assert [l.company_route_identifier for l in legs] == ["A", "B", "C"]
    assert [l.sequence_number for l in legs] == ["01", "02", "03"]


@pytest.mark.parametrize(
    "field,model_attr",
    [
        ("Course", "course"),
        ("Distance", "distance"),
        ("Altitude1", "altitude_1"),
        ("Altitude2", "altitude_2"),
        ("SpeedLimit", "speed_limit"),
    ],
)
def test_none_values_become_empty_strings(field, model_attr):
    df = make_df(
        [
            {
                "CompanyRouteIdentifier": "CR777",
                field: None,
            }
        ]
    )

    leg = df_to_company_route_legs(df)[0]
    assert getattr(leg, model_attr) == ""
