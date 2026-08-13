import pandas as pd
import pytest

from arinc424.models.grid_mora import df_to_grid_mora


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_grid_mora(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "LatitudeBand": "N45",
                "LongitudeBand": "E009",
                "MORAAltitude": "3500",
                "MORAType": "GRID",
                "Latitude": 45.0,
                "Longitude": 9.0,
                "CycleDate": "2401",
            }
        ]
    )

    result = df_to_grid_mora(df)
    assert len(result) == 1

    mora = result[0]
    assert mora.latitude_band == "N45"
    assert mora.longitude_band == "E009"
    assert mora.mora_altitude == "3500"
    assert mora.mora_type == "GRID"
    assert mora.latitude == 45.0
    assert mora.longitude == 9.0
    assert mora.cycle_date == "2401"


def test_missing_optional_fields_become_empty_strings_or_none():
    df = make_df(
        [
            {
                "LatitudeBand": "N00",
                # Everything else missing
            }
        ]
    )

    mora = df_to_grid_mora(df)[0]

    assert mora.latitude_band == "N00"
    assert mora.longitude_band == ""
    assert mora.mora_altitude == ""
    assert mora.mora_type == ""
    assert mora.latitude is None
    assert mora.longitude is None
    assert mora.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "LatitudeBand": " N10 ",
                "LongitudeBand": " E020 ",
                "MORAAltitude": " 4500 ",
                "MORAType": " GRID ",
                "Latitude": 10.0,
                "Longitude": 20.0,
                "CycleDate": " 2402 ",
            }
        ]
    )

    mora = df_to_grid_mora(df)[0]

    assert mora.latitude_band == "N10"
    assert mora.longitude_band == "E020"
    assert mora.mora_altitude == "4500"
    assert mora.mora_type == "GRID"
    assert mora.latitude == 10.0
    assert mora.longitude == 20.0
    assert mora.cycle_date == "2402"


@pytest.mark.parametrize("field", ["Latitude", "Longitude"])
def test_nan_coordinates_become_none(field):
    df = make_df(
        [
            {
                "LatitudeBand": "N99",
                field: float("nan"),
            }
        ]
    )

    mora = df_to_grid_mora(df)[0]

    if field == "Latitude":
        assert mora.latitude is None
    else:
        assert mora.longitude is None


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"LatitudeBand": "N01", "LongitudeBand": "E001"},
            {"LatitudeBand": "N02", "LongitudeBand": "E002"},
            {"LatitudeBand": "N03", "LongitudeBand": "E003"},
        ]
    )

    result = df_to_grid_mora(df)

    assert len(result) == 3
    assert [m.latitude_band for m in result] == ["N01", "N02", "N03"]
    assert [m.longitude_band for m in result] == ["E001", "E002", "E003"]
