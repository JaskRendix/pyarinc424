from __future__ import annotations

import math

import pandas as pd
import pytest

from arinc424.utils import (
    apply_decoders,
    decode_arinc_coordinate,
    decode_elevation,
    decode_frequency,
    decode_magvar,
)


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
        ("E0050", 5.0),  # 5-char tenths: E + 000 + 5 -> 5.0° East
        ("W0012", -1.2),  # 5-char tenths: W + 000 + 2 -> -1.2° West
        ("E1234", 123.4),  # 5-char tenths: E + 123 + 4 -> 123.4° East
        ("W1234", -123.4),  # 5-char tenths: W + 123 + 4 -> -123.4° West
        ("E12300", 12.5),  # 6-char legacy minutes: E + 12 + 30 -> 12° 30' = 12.5°
        ("T0000", 0.0),  # True North
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


@pytest.mark.parametrize(
    "freq,expected",
    [
        ("118100", 118.1),  # Encoded kHz
        ("118.1", 118.1),
        ("33500", 33.5),  # Encoded kHz (> 10000 -> 33500 / 1000 = 33.5 MHz)
        (None, None),
        ("", None),
        ("INVALID", None),
    ],
)
def test_decode_frequency(freq, expected):
    result = decode_frequency(freq)
    if expected is None:
        assert result is None
    else:
        assert math.isclose(result, expected, rel_tol=1e-9)


@pytest.mark.parametrize(
    "elev,expected",
    [
        ("1250", 1250.0),
        ("+1250", 1250.0),
        ("-150", -150.0),
        ("B50", -50.0),  # Below sea level prefix
        (None, None),
        ("", None),
        ("XYZ", None),
    ],
)
def test_decode_elevation(elev, expected):
    result = decode_elevation(elev)
    if expected is None:
        assert result is None
    else:
        assert math.isclose(result, expected, rel_tol=1e-9)


def test_apply_decoders_coordinates_and_magvar():
    df = pd.DataFrame(
        {
            "Latitude": ["N48073012", "S48073012"],
            "Longitude": ["E12345012", "W12345012"],
            "MagneticVariation": ["E0050", "W0012"],
            "CommsFrequency": ["118100", "121500"],
            "StationElevation": ["+1500", "-200"],
        }
    )

    out = apply_decoders(df)

    assert "Latitude_decimal" in out.columns
    assert "Longitude_decimal" in out.columns
    assert "MagneticVariation_decimal" in out.columns
    assert "CommsFrequency_decoded" in out.columns
    assert "StationElevation_decoded" in out.columns

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

    assert math.isclose(out.loc[0, "MagneticVariation_decimal"], 5.0)
    assert math.isclose(out.loc[1, "MagneticVariation_decimal"], -1.2)
    assert math.isclose(out.loc[0, "CommsFrequency_decoded"], 118.1)
    assert math.isclose(out.loc[0, "StationElevation_decoded"], 1500.0)
    assert math.isclose(out.loc[1, "StationElevation_decoded"], -200.0)


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
