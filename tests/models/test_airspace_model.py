import pandas as pd
import pytest

from arinc424.models.airspace import df_to_airspaces


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_airspaces(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "AirspaceIdentifier": "ASP01",
                "AirspaceClass": "C",
                "BoundaryVia": "DCT",
                "BoundaryPoint": "WP01",
                "LowerLimit": "3000",
                "UpperLimit": "12000",
                "AirspaceType": "CTR",
                "AirspaceControl": "MIL",
                "CycleDate": "2401",
            }
        ]
    )

    airspaces = df_to_airspaces(df)
    assert len(airspaces) == 1

    a = airspaces[0]
    assert a.identifier == "ASP01"
    assert a.airspace_class == "C"
    assert a.boundary_via == "DCT"
    assert a.boundary_point == "WP01"
    assert a.lower_limit == "3000"
    assert a.upper_limit == "12000"
    assert a.airspace_type == "CTR"
    assert a.airspace_control == "MIL"
    assert a.cycle_date == "2401"


def test_dynamic_identifier_column():
    df = make_df(
        [
            {
                "CustomIdentifier": "ASP99",
                "BoundaryVia": "DCT",
            }
        ]
    )

    df = df.rename(columns={"CustomIdentifier": "SectorIdentifier"})
    a = df_to_airspaces(df)[0]
    assert (
        a.identifier == "SectorIdentifier".replace("SectorIdentifier", "ASP99")
        or a.identifier == "ASP99"
    )


def test_dynamic_class_column():
    df = make_df(
        [
            {
                "CustomClass": "G",
                "BoundaryVia": "DCT",
            }
        ]
    )

    df = df.rename(columns={"CustomClass": "AirspaceClass"})
    a = df_to_airspaces(df)[0]
    assert a.airspace_class == "G"


def test_dynamic_type_column():
    df = make_df(
        [
            {
                "CustomType": "TMA",
                "BoundaryVia": "DCT",
            }
        ]
    )

    df = df.rename(columns={"CustomType": "AirspaceType"})
    a = df_to_airspaces(df)[0]
    assert a.airspace_type == "TMA"


def test_dynamic_control_column():
    df = make_df(
        [
            {
                "CustomControl": "CIV",
                "BoundaryVia": "DCT",
            }
        ]
    )

    df = df.rename(columns={"CustomControl": "AirspaceControl"})
    a = df_to_airspaces(df)[0]
    assert a.airspace_control == "CIV"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "AirspaceIdentifier": "ASP02",
                # Everything else missing
            }
        ]
    )

    a = df_to_airspaces(df)[0]

    assert a.identifier == "ASP02"
    assert a.airspace_class == ""
    assert a.boundary_via == ""
    assert a.boundary_point == ""
    assert a.lower_limit == ""
    assert a.upper_limit == ""
    assert a.airspace_type == ""
    assert a.airspace_control == ""
    assert a.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "AirspaceIdentifier": " ASP03 ",
                "AirspaceClass": " C ",
                "BoundaryVia": " DCT ",
                "BoundaryPoint": " WP01 ",
                "LowerLimit": " 3000 ",
                "UpperLimit": " 12000 ",
                "AirspaceType": " CTR ",
                "AirspaceControl": " MIL ",
                "CycleDate": " 2401 ",
            }
        ]
    )

    a = df_to_airspaces(df)[0]

    assert a.identifier == "ASP03"
    assert a.airspace_class == "C"
    assert a.boundary_via == "DCT"
    assert a.boundary_point == "WP01"
    assert a.lower_limit == "3000"
    assert a.upper_limit == "12000"
    assert a.airspace_type == "CTR"
    assert a.airspace_control == "MIL"
    assert a.cycle_date == "2401"


@pytest.mark.parametrize(
    "field,attr",
    [
        ("BoundaryVia", "boundary_via"),
        ("BoundaryPoint", "boundary_point"),
        ("LowerLimit", "lower_limit"),
        ("UpperLimit", "upper_limit"),
        ("AirspaceType", "airspace_type"),
        ("AirspaceControl", "airspace_control"),
    ],
)
def test_nan_values_become_empty_strings(field, attr):
    df = make_df(
        [
            {
                "AirspaceIdentifier": "ASP04",
                field: float("nan"),
            }
        ]
    )

    a = df_to_airspaces(df)[0]
    assert getattr(a, attr) == ""


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"AirspaceIdentifier": "A", "BoundaryVia": "DCT"},
            {"AirspaceIdentifier": "B", "BoundaryVia": "DCT"},
            {"AirspaceIdentifier": "C", "BoundaryVia": "DCT"},
        ]
    )

    airspaces = df_to_airspaces(df)

    assert len(airspaces) == 3
    assert [a.identifier for a in airspaces] == ["A", "B", "C"]
