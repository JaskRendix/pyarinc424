import math

import pandas as pd
import pytest

from arinc424.utils import apply_decoders, decode_arinc_coordinate, decode_magvar


@pytest.mark.parametrize(
    "coord,expected",
    [
        ("N48073012", 48 + 7 / 60 + 30.12 / 3600),  # Normal north
        ("S48073012", -(48 + 7 / 60 + 30.12 / 3600)),  # South hemisphere
        (
            "E12345012",
            123 + 45 / 60 + 1.2 / 3600,
        ),  # East longitude (01 seconds + 2 tenths)
        ("W12345012", -(123 + 45 / 60 + 1.2 / 3600)),  # West longitude
        ("N00000000", 0.0),
        ("S00000000", -0.0),
    ],
)
def test_decode_arinc_coordinate_valid(coord, expected):
    result = decode_arinc_coordinate(coord)
    assert math.isclose(result, round(expected, 6), rel_tol=1e-9)


@pytest.mark.parametrize(
    "coord",
    [
        None,
        "",
        "ABC",
        "N123",  # too short
        "X48073012",  # invalid hemisphere
        "N48XX3012",  # invalid numeric
        12345,  # not a string
    ],
)
def test_decode_arinc_coordinate_invalid(coord):
    assert decode_arinc_coordinate(coord) is None


@pytest.mark.parametrize(
    "magvar,expected",
    [
        ("E0050", 0 + 50 / 60),  # East positive
        ("W0012", -(0 + 12 / 60)),  # West negative
        ("E1234", 12 + 34 / 60),
        ("W1234", -(12 + 34 / 60)),
    ],
)
def test_decode_magvar_valid(magvar, expected):
    result = decode_magvar(magvar)
    assert math.isclose(result, expected, rel_tol=1e-9)


@pytest.mark.parametrize(
    "magvar",
    [
        None,
        "",
        "ABC",
        "E12",  # too short
        "X0050",  # invalid hemisphere
        "E00XX",  # invalid numeric
        12345,
    ],
)
def test_decode_magvar_invalid(magvar):
    assert decode_magvar(magvar) is None


def test_apply_decoders_coordinates_and_magvar():
    df = pd.DataFrame(
        {
            "Latitude": ["N48073012", "S48073012"],
            "Longitude": ["E12345012", "W12345012"],
            "MagneticVariation": ["E0050", "W0012"],
        }
    )

    out = apply_decoders(df)

    assert "Latitude_decimal" in out.columns
    assert "Longitude_decimal" in out.columns
    assert "MagneticVariation_decimal" in out.columns

    assert math.isclose(
        out.loc[0, "Latitude_decimal"], round(48 + 7 / 60 + 30.12 / 3600, 6)
    )
    assert math.isclose(
        out.loc[1, "Latitude_decimal"], round(-(48 + 7 / 60 + 30.12 / 3600), 6)
    )

    assert math.isclose(
        out.loc[0, "Longitude_decimal"], round(123 + 45 / 60 + 1.2 / 3600, 6)
    )
    assert math.isclose(
        out.loc[1, "Longitude_decimal"], round(-(123 + 45 / 60 + 1.2 / 3600), 6)
    )

    assert math.isclose(out.loc[0, "MagneticVariation_decimal"], 50 / 60)
    assert math.isclose(out.loc[1, "MagneticVariation_decimal"], -(12 / 60))


def test_apply_decoders_ignores_unrelated_columns():
    df = pd.DataFrame(
        {
            "Foo": ["bar", "baz"],
            "LatitudeX": ["N48073012", "N48073012"],
        }
    )

    out = apply_decoders(df)

    assert "Foo" in out.columns
    assert "LatitudeX_decimal" not in out.columns


def test_apply_decoders_handles_empty_dataframe():
    df = pd.DataFrame(columns=["Latitude", "Longitude"])
    out = apply_decoders(df)

    assert "Latitude_decimal" in out.columns
    assert "Longitude_decimal" in out.columns
    assert out.empty


def test_apply_decoders_handles_nan_values():
    df = pd.DataFrame(
        {
            "Latitude": ["N48073012", None, "S48073012"],
            "Longitude": [None, "E12345012", "W12345012"],
        }
    )

    out = apply_decoders(df)

    assert out.loc[0, "Latitude_decimal"] is not None
    assert pd.isna(out.loc[1, "Latitude_decimal"])
    assert out.loc[2, "Latitude_decimal"] is not None

    assert pd.isna(out.loc[0, "Longitude_decimal"])
    assert out.loc[1, "Longitude_decimal"] is not None
    assert out.loc[2, "Longitude_decimal"] is not None
