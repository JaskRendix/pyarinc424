import pandas as pd
import pytest

from arinc424.models.heliport_procedures import df_to_heliport_procedures


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_heliport_procedures(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "HeliportIdentifier": "H123",
                "ProcedureIdentifier": "HP01",
                "RouteType": "DEP",
                "TransitionIdentifier": "TRANS1",
                "SequenceNumber": "01",
                "PathTerminator": "IF",
                "FixIdentifier": "FIXA",
                "Course": "090",
                "Distance": "3.5",
                "AltitudeDescription": "AT",
                "Altitude1": "1500",
                "Altitude2": "2500",
                "SpeedLimit": "120",
                "CycleDate": "2401",
            }
        ]
    )

    result = df_to_heliport_procedures(df)
    assert len(result) == 1

    hp = result[0]
    assert hp.heliport_identifier == "H123"
    assert hp.procedure_identifier == "HP01"
    assert hp.route_type == "DEP"
    assert hp.transition_identifier == "TRANS1"
    assert hp.sequence_number == "01"
    assert hp.path_terminator == "IF"
    assert hp.fix_identifier == "FIXA"
    assert hp.course == "090"
    assert hp.distance == "3.5"
    assert hp.altitude_description == "AT"
    assert hp.altitude_1 == "1500"
    assert hp.altitude_2 == "2500"
    assert hp.speed_limit == "120"
    assert hp.cycle_date == "2401"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "HeliportIdentifier": "H999",
                # Everything else missing
            }
        ]
    )

    hp = df_to_heliport_procedures(df)[0]

    assert hp.heliport_identifier == "H999"
    assert hp.procedure_identifier == ""
    assert hp.route_type == ""
    assert hp.transition_identifier == ""
    assert hp.sequence_number == ""
    assert hp.path_terminator == ""
    assert hp.fix_identifier == ""
    assert hp.course == ""
    assert hp.distance == ""
    assert hp.altitude_description == ""
    assert hp.altitude_1 == ""
    assert hp.altitude_2 == ""
    assert hp.speed_limit == ""
    assert hp.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "HeliportIdentifier": " H001 ",
                "ProcedureIdentifier": " HP02 ",
                "RouteType": " APP ",
                "TransitionIdentifier": " T1 ",
                "SequenceNumber": " 02 ",
                "PathTerminator": " IF ",
                "FixIdentifier": " FIXB ",
                "Course": " 180 ",
                "Distance": " 4.2 ",
                "AltitudeDescription": " AT ",
                "Altitude1": " 2000 ",
                "Altitude2": " 3000 ",
                "SpeedLimit": " 140 ",
                "CycleDate": " 2402 ",
            }
        ]
    )

    hp = df_to_heliport_procedures(df)[0]

    assert hp.heliport_identifier == "H001"
    assert hp.procedure_identifier == "HP02"
    assert hp.route_type == "APP"
    assert hp.transition_identifier == "T1"
    assert hp.sequence_number == "02"
    assert hp.path_terminator == "IF"
    assert hp.fix_identifier == "FIXB"
    assert hp.course == "180"
    assert hp.distance == "4.2"
    assert hp.altitude_description == "AT"
    assert hp.altitude_1 == "2000"
    assert hp.altitude_2 == "3000"
    assert hp.speed_limit == "140"
    assert hp.cycle_date == "2402"


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"HeliportIdentifier": "H1", "ProcedureIdentifier": "P1"},
            {"HeliportIdentifier": "H2", "ProcedureIdentifier": "P2"},
            {"HeliportIdentifier": "H3", "ProcedureIdentifier": "P3"},
        ]
    )

    result = df_to_heliport_procedures(df)

    assert len(result) == 3
    assert [hp.heliport_identifier for hp in result] == ["H1", "H2", "H3"]
    assert [hp.procedure_identifier for hp in result] == ["P1", "P2", "P3"]


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
                "HeliportIdentifier": "H777",
                field: None,
            }
        ]
    )

    hp = df_to_heliport_procedures(df)[0]
    assert getattr(hp, model_attr) == ""
