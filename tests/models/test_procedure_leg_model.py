import pandas as pd
import pytest

from arinc424.models.procedures import df_to_procedure_legs


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_procedure_legs(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "AirportIdentifier": "LIMC",
                "ProcedureIdentifier": "I01L",
                "RouteType": "APP",
                "TransitionIdentifier": "TRANS1",
                "SequenceNumber": "01",
                "PathTerminator": "IF",
                "FixIdentifier": "ABCD",
                "Course": "090",
                "Distance": "5.0",
                "AltitudeDescription": "AT",
                "Altitude1": "3000",
                "Altitude2": "5000",
                "SpeedLimit": "210",
                "CycleDate": "2401",
            }
        ]
    )

    legs = df_to_procedure_legs(df)
    assert len(legs) == 1

    leg = legs[0]
    assert leg.airport_identifier == "LIMC"
    assert leg.procedure_identifier == "I01L"
    assert leg.route_type == "APP"
    assert leg.transition_identifier == "TRANS1"
    assert leg.sequence_number == "01"
    assert leg.path_terminator == "IF"
    assert leg.fix_identifier == "ABCD"
    assert leg.course == "090"
    assert leg.distance == "5.0"
    assert leg.altitude_description == "AT"
    assert leg.altitude_1 == "3000"
    assert leg.altitude_2 == "5000"
    assert leg.speed_limit == "210"
    assert leg.cycle_date == "2401"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "AirportIdentifier": "LIML",
                # Everything else missing
            }
        ]
    )

    leg = df_to_procedure_legs(df)[0]

    assert leg.airport_identifier == "LIML"
    assert leg.procedure_identifier == ""
    assert leg.route_type == ""
    assert leg.transition_identifier == ""
    assert leg.sequence_number == ""
    assert leg.path_terminator == ""
    assert leg.fix_identifier == ""
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
                "AirportIdentifier": " LIMC ",
                "ProcedureIdentifier": " I01L ",
                "RouteType": " APP ",
                "TransitionIdentifier": " TRANS ",
                "SequenceNumber": " 01 ",
                "PathTerminator": " IF ",
                "FixIdentifier": " ABCD ",
                "Course": " 090 ",
                "Distance": " 5.0 ",
                "AltitudeDescription": " AT ",
                "Altitude1": " 3000 ",
                "Altitude2": " 5000 ",
                "SpeedLimit": " 210 ",
                "CycleDate": " 2401 ",
            }
        ]
    )

    leg = df_to_procedure_legs(df)[0]

    assert leg.airport_identifier == "LIMC"
    assert leg.procedure_identifier == "I01L"
    assert leg.route_type == "APP"
    assert leg.transition_identifier == "TRANS"
    assert leg.sequence_number == "01"
    assert leg.path_terminator == "IF"
    assert leg.fix_identifier == "ABCD"
    assert leg.course == "090"
    assert leg.distance == "5.0"
    assert leg.altitude_description == "AT"
    assert leg.altitude_1 == "3000"
    assert leg.altitude_2 == "5000"
    assert leg.speed_limit == "210"
    assert leg.cycle_date == "2401"


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"AirportIdentifier": "AAA", "ProcedureIdentifier": "P1"},
            {"AirportIdentifier": "BBB", "ProcedureIdentifier": "P2"},
            {"AirportIdentifier": "CCC", "ProcedureIdentifier": "P3"},
        ]
    )

    legs = df_to_procedure_legs(df)
    assert len(legs) == 3
    assert [l.airport_identifier for l in legs] == ["AAA", "BBB", "CCC"]
    assert [l.procedure_identifier for l in legs] == ["P1", "P2", "P3"]


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
                "AirportIdentifier": "LIMC",
                field: None,
            }
        ]
    )

    leg = df_to_procedure_legs(df)[0]
    assert getattr(leg, model_attr) == ""
