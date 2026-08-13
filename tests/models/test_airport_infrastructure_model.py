import pandas as pd
import pytest

from arinc424.models.airport_infrastructure import df_to_airport_infrastructure


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_airport_infrastructure(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "AirportIdentifier": "LIMC",
                "TaxiwayIdentifier": "TWY-A",
                "TaxiwayType": "TWY",
                "Latitude": "45.6300",
                "Longitude": "8.7200",
                "MagneticVariation": "2E",
                "CycleDate": "2401",
            }
        ]
    )

    infra = df_to_airport_infrastructure(df)
    assert len(infra) == 1

    r = infra[0]
    assert r.airport_identifier == "LIMC"
    assert r.feature_identifier == "TWY-A"
    assert r.feature_type == "TWY"
    assert r.latitude == "45.6300"
    assert r.longitude == "8.7200"
    assert r.magnetic_variation == "2E"
    assert r.cycle_date == "2401"


def test_dynamic_feature_identifier_column():
    df = make_df(
        [
            {
                "RunwayIdentifier": "16L",
                "AirportIdentifier": "LIMC",
            }
        ]
    )

    r = df_to_airport_infrastructure(df)[0]
    assert r.feature_identifier == "16L"


def test_dynamic_feature_type_column():
    df = make_df(
        [
            {
                "SystemType": "ILS",
                "AirportIdentifier": "LIMC",
            }
        ]
    )

    r = df_to_airport_infrastructure(df)[0]
    assert r.feature_type == "ILS"


def test_dynamic_lat_lon_columns():
    df = make_df(
        [
            {
                "StartLatitude": "45.00",
                "StartLongitude": "9.00",
                "AirportIdentifier": "LIMC",
            }
        ]
    )

    r = df_to_airport_infrastructure(df)[0]
    assert r.latitude == "45.00"
    assert r.longitude == "9.00"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "AirportIdentifier": "LIMC",
                # Everything else missing
            }
        ]
    )

    r = df_to_airport_infrastructure(df)[0]

    assert r.airport_identifier == "LIMC"
    assert r.feature_identifier == ""
    assert r.feature_type == ""
    assert r.latitude == ""
    assert r.longitude == ""
    assert r.magnetic_variation == ""
    assert r.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "AirportIdentifier": " LIMC ",
                "TaxiwayIdentifier": " TWY-A ",
                "TaxiwayType": " TWY ",
                "Latitude": " 45.6300 ",
                "Longitude": " 8.7200 ",
                "MagneticVariation": " 2E ",
                "CycleDate": " 2401 ",
            }
        ]
    )

    r = df_to_airport_infrastructure(df)[0]

    assert r.airport_identifier == "LIMC"
    assert r.feature_identifier == "TWY-A"
    assert r.feature_type == "TWY"
    assert r.latitude == "45.6300"
    assert r.longitude == "8.7200"
    assert r.magnetic_variation == "2E"
    assert r.cycle_date == "2401"


@pytest.mark.parametrize(
    "field,attr",
    [
        ("Latitude", "latitude"),
        ("Longitude", "longitude"),
        ("MagneticVariation", "magnetic_variation"),
    ],
)
def test_nan_values_become_empty_strings(field, attr):
    df = make_df(
        [
            {
                "AirportIdentifier": "LIMC",
                field: float("nan"),
            }
        ]
    )

    r = df_to_airport_infrastructure(df)[0]
    assert getattr(r, attr) == ""


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"AirportIdentifier": "A", "TaxiwayIdentifier": "T1"},
            {"AirportIdentifier": "B", "TaxiwayIdentifier": "T2"},
            {"AirportIdentifier": "C", "TaxiwayIdentifier": "T3"},
        ]
    )

    infra = df_to_airport_infrastructure(df)

    assert len(infra) == 3
    assert [r.airport_identifier for r in infra] == ["A", "B", "C"]
    assert [r.feature_identifier for r in infra] == ["T1", "T2", "T3"]
