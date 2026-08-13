import pandas as pd
import pytest

from arinc424.models.airspace_boundaries import df_to_airspace_boundaries


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_airspace_boundaries(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "AirspaceIdentifier": "ASP01",
                "AirspaceClass": "C",
                "BoundaryVia": "DCT",
                "BoundaryPointIdentifier": "WP01",
                "LowerLimit": "3000",
                "UpperLimit": "12000",
                "AirspaceType": "CTR",
                "AirspaceControl": "MIL",
                "CycleDate": "2401",
            }
        ]
    )

    boundaries = df_to_airspace_boundaries(df)
    assert len(boundaries) == 1

    b = boundaries[0]
    assert b.identifier == "ASP01"
    assert b.airspace_class == "C"
    assert b.boundary_via == "DCT"
    assert b.boundary_point_identifier == "WP01"
    assert b.lower_limit == "3000"
    assert b.upper_limit == "12000"
    assert b.airspace_type == "CTR"
    assert b.airspace_control == "MIL"
    assert b.cycle_date == "2401"


def test_dynamic_identifier_column():
    df = make_df(
        [
            {
                "SectorIdentifier": "SEC99",
                "BoundaryVia": "DCT",
            }
        ]
    )

    b = df_to_airspace_boundaries(df)[0]
    assert b.identifier == "SEC99"


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
    b = df_to_airspace_boundaries(df)[0]
    assert b.airspace_class == "G"


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
    b = df_to_airspace_boundaries(df)[0]
    assert b.airspace_type == "TMA"


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
    b = df_to_airspace_boundaries(df)[0]
    assert b.airspace_control == "CIV"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "AirspaceIdentifier": "ASP02",
                # Everything else missing
            }
        ]
    )

    b = df_to_airspace_boundaries(df)[0]

    assert b.identifier == "ASP02"
    assert b.airspace_class == ""
    assert b.boundary_via == ""
    assert b.boundary_point_identifier == ""
    assert b.lower_limit == ""
    assert b.upper_limit == ""
    assert b.airspace_type == ""
    assert b.airspace_control == ""
    assert b.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "AirspaceIdentifier": " ASP03 ",
                "AirspaceClass": " C ",
                "BoundaryVia": " DCT ",
                "BoundaryPointIdentifier": " WP01 ",
                "LowerLimit": " 3000 ",
                "UpperLimit": " 12000 ",
                "AirspaceType": " CTR ",
                "AirspaceControl": " MIL ",
                "CycleDate": " 2401 ",
            }
        ]
    )

    b = df_to_airspace_boundaries(df)[0]

    assert b.identifier == "ASP03"
    assert b.airspace_class == "C"
    assert b.boundary_via == "DCT"
    assert b.boundary_point_identifier == "WP01"
    assert b.lower_limit == "3000"
    assert b.upper_limit == "12000"
    assert b.airspace_type == "CTR"
    assert b.airspace_control == "MIL"
    assert b.cycle_date == "2401"


@pytest.mark.parametrize(
    "field,attr",
    [
        ("BoundaryVia", "boundary_via"),
        ("BoundaryPointIdentifier", "boundary_point_identifier"),
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

    b = df_to_airspace_boundaries(df)[0]
    assert getattr(b, attr) == ""


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"AirspaceIdentifier": "A", "BoundaryVia": "DCT"},
            {"AirspaceIdentifier": "B", "BoundaryVia": "DCT"},
            {"AirspaceIdentifier": "C", "BoundaryVia": "DCT"},
        ]
    )

    boundaries = df_to_airspace_boundaries(df)

    assert len(boundaries) == 3
    assert [b.identifier for b in boundaries] == ["A", "B", "C"]
