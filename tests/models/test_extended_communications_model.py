import pandas as pd
import pytest

from arinc424.models.communications_extended import df_to_extended_communications


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_extended_communications(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "StationIdentifier": "MILAN-TWR",
                "ServiceType": "TWR",
                "Frequency": "118.500",
                "GuardFrequency": "121.500",
                "TimeCode": "H24",
                "Sectorization": "N",
                "Latitude": 45.63,
                "Longitude": 8.72,
                "CycleDate": "2401",
            }
        ]
    )

    comms = df_to_extended_communications(df)
    assert len(comms) == 1

    c = comms[0]
    assert c.identifier == "MILAN-TWR"
    assert c.service_type == "TWR"
    assert c.frequency == "118.500"
    assert c.guard_frequency == "121.500"
    assert c.time_code == "H24"
    assert c.sectorization == "N"
    assert c.latitude == 45.63
    assert c.longitude == 8.72
    assert c.cycle_date == "2401"


def test_dynamic_identifier_column_fallback():
    df = make_df(
        [
            {
                "AirportIdentifier": "LIMC",
                "Frequency": "118.500",
            }
        ]
    )

    c = df_to_extended_communications(df)[0]
    assert c.identifier == "LIMC"


def test_dynamic_service_type_fallback():
    df = make_df(
        [
            {
                "StationIdentifier": "MILAN-INFO",
                "BroadcastType": "ATIS",
                "Frequency": "127.800",
            }
        ]
    )

    c = df_to_extended_communications(df)[0]
    assert c.service_type == "ATIS"


def test_missing_optional_fields_become_empty_strings_and_none_coords():
    df = make_df(
        [
            {
                "StationIdentifier": "MILAN-TWR",
                # Everything else missing
            }
        ]
    )

    c = df_to_extended_communications(df)[0]

    assert c.identifier == "MILAN-TWR"
    assert c.service_type == ""
    assert c.frequency == ""
    assert c.guard_frequency == ""
    assert c.time_code == ""
    assert c.sectorization == ""
    assert c.latitude is None
    assert c.longitude is None
    assert c.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "StationIdentifier": " MILAN-TWR ",
                "ServiceType": " TWR ",
                "Frequency": " 118.500 ",
                "GuardFrequency": " 121.500 ",
                "TimeCode": " H24 ",
                "Sectorization": " N ",
                "Latitude": 45.63,
                "Longitude": 8.72,
                "CycleDate": " 2401 ",
            }
        ]
    )

    c = df_to_extended_communications(df)[0]

    assert c.identifier == "MILAN-TWR"
    assert c.service_type == "TWR"
    assert c.frequency == "118.500"
    assert c.guard_frequency == "121.500"
    assert c.time_code == "H24"
    assert c.sectorization == "N"
    assert c.cycle_date == "2401"


@pytest.mark.parametrize("field", ["Latitude", "Longitude"])
def test_nan_coordinates_become_none(field):
    df = make_df(
        [
            {
                "StationIdentifier": "MILAN-TWR",
                field: float("nan"),
            }
        ]
    )

    c = df_to_extended_communications(df)[0]

    if field == "Latitude":
        assert c.latitude is None
    else:
        assert c.longitude is None


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"StationIdentifier": "A", "ServiceType": "TWR"},
            {"StationIdentifier": "B", "ServiceType": "GND"},
            {"StationIdentifier": "C", "ServiceType": "APP"},
        ]
    )

    comms = df_to_extended_communications(df)

    assert len(comms) == 3
    assert [c.identifier for c in comms] == ["A", "B", "C"]
    assert [c.service_type for c in comms] == ["TWR", "GND", "APP"]
