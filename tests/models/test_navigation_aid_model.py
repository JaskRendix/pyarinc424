import pandas as pd
import pytest

from arinc424.models.navigation_aids import df_to_navigation_aids


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_navigation_aids(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "LocalizerIdentifier": "LOC1",
                "RunwayIdentifier": "16L",
                "Frequency": "110.30",
                "LocalizerLatitude": 45.0,
                "LocalizerLongitude": 9.0,
                "CycleDate": "2401",
            }
        ]
    )

    result = df_to_navigation_aids(df)
    assert len(result) == 1

    nav = result[0]
    assert nav.identifier == "LOC1"
    assert nav.runway_identifier == "16L"
    assert nav.frequency == "110.30"
    assert nav.latitude == 45.0
    assert nav.longitude == 9.0
    assert nav.facility_type == "LOCALIZER"
    assert nav.cycle_date == "2401"


@pytest.mark.parametrize(
    "ident_col,lat_col,lon_col,freq_col",
    [
        (
            "GlideslopeIdentifier",
            "GlideslopeLatitude",
            "GlideslopeLongitude",
            "GlideslopeFrequency",
        ),
        ("DMEIdentifier", "DMELatitude", "DMELongitude", "DMEChannel"),
        ("MLSIdentifier", "MLSLatitude", "MLSLongitude", "MLSFrequency"),
    ],
)
def test_dynamic_column_detection(ident_col, lat_col, lon_col, freq_col):
    df = make_df(
        [
            {
                ident_col: "NAVX",
                "RunwayIdentifier": "22R",
                lat_col: 50.0,
                lon_col: 8.0,
                freq_col: "108.50",
                "CycleDate": "2402",
            }
        ]
    )

    nav = df_to_navigation_aids(df)[0]

    assert nav.identifier == "NAVX"
    assert nav.runway_identifier == "22R"
    assert nav.latitude == 50.0
    assert nav.longitude == 8.0
    assert nav.frequency == "108.50"
    assert nav.cycle_date == "2402"


def test_missing_optional_fields_become_empty_strings_or_none():
    df = make_df(
        [
            {
                "LocalizerIdentifier": "LOC2",
                # Missing runway, frequency, lat/lon, cycle date
            }
        ]
    )

    nav = df_to_navigation_aids(df)[0]

    assert nav.identifier == "LOC2"
    assert nav.runway_identifier == ""
    assert nav.frequency == ""
    assert nav.latitude is None
    assert nav.longitude is None
    assert nav.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "LocalizerIdentifier": " LOC3 ",
                "RunwayIdentifier": " 34L ",
                "Frequency": " 109.90 ",
                "LocalizerLatitude": 12.34,
                "LocalizerLongitude": 56.78,
                "CycleDate": " 2403 ",
            }
        ]
    )

    nav = df_to_navigation_aids(df)[0]

    assert nav.identifier == "LOC3"
    assert nav.runway_identifier == "34L"
    assert nav.frequency == "109.90"
    assert nav.latitude == 12.34
    assert nav.longitude == 56.78
    assert nav.cycle_date == "2403"


@pytest.mark.parametrize("field", ["LocalizerLatitude", "LocalizerLongitude"])
def test_nan_coordinates_become_none(field):
    df = make_df(
        [
            {
                "LocalizerIdentifier": "LOC4",
                field: float("nan"),
            }
        ]
    )

    nav = df_to_navigation_aids(df)[0]

    if field.endswith("Latitude"):
        assert nav.latitude is None
    else:
        assert nav.longitude is None


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"LocalizerIdentifier": "A", "RunwayIdentifier": "01"},
            {"LocalizerIdentifier": "B", "RunwayIdentifier": "02"},
            {"LocalizerIdentifier": "C", "RunwayIdentifier": "03"},
        ]
    )

    result = df_to_navigation_aids(df)

    assert len(result) == 3
    assert [n.identifier for n in result] == ["A", "B", "C"]
    assert [n.runway_identifier for n in result] == ["01", "02", "03"]
