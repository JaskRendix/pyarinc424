import pandas as pd
import pytest

from arinc424.models.company_routes import df_to_company_routes


def make_df(rows):
    return pd.DataFrame(rows)


def test_empty_dataframe_returns_empty_list():
    df = make_df([])
    assert df_to_company_routes(df) == []


def test_basic_conversion_single_row():
    df = make_df(
        [
            {
                "CompanyRouteIdentifier": "CR001",
                "OriginAirport": "LIMC",
                "DestinationAirport": "LIRF",
                "RouteType": "N",
                "CycleDate": "2401",
            }
        ]
    )

    routes = df_to_company_routes(df)
    assert len(routes) == 1

    r = routes[0]
    assert r.company_route_identifier == "CR001"
    assert r.origin_airport == "LIMC"
    assert r.destination_airport == "LIRF"
    assert r.route_type == "N"
    assert r.cycle_date == "2401"


def test_missing_optional_fields_become_empty_strings():
    df = make_df(
        [
            {
                "CompanyRouteIdentifier": "CRX",
                # Everything else missing
            }
        ]
    )

    r = df_to_company_routes(df)[0]

    assert r.company_route_identifier == "CRX"
    assert r.origin_airport == ""
    assert r.destination_airport == ""
    assert r.route_type == ""
    assert r.cycle_date == ""


def test_whitespace_is_stripped():
    df = make_df(
        [
            {
                "CompanyRouteIdentifier": " CR002 ",
                "OriginAirport": " LIML ",
                "DestinationAirport": " LIPZ ",
                "RouteType": " N ",
                "CycleDate": " 2402 ",
            }
        ]
    )

    r = df_to_company_routes(df)[0]

    assert r.company_route_identifier == "CR002"
    assert r.origin_airport == "LIML"
    assert r.destination_airport == "LIPZ"
    assert r.route_type == "N"
    assert r.cycle_date == "2402"


def test_multiple_rows_are_all_converted():
    df = make_df(
        [
            {"CompanyRouteIdentifier": "A", "OriginAirport": "AAA"},
            {"CompanyRouteIdentifier": "B", "OriginAirport": "BBB"},
            {"CompanyRouteIdentifier": "C", "OriginAirport": "CCC"},
        ]
    )

    routes = df_to_company_routes(df)

    assert len(routes) == 3
    assert [r.company_route_identifier for r in routes] == ["A", "B", "C"]
    assert [r.origin_airport for r in routes] == ["AAA", "BBB", "CCC"]


@pytest.mark.parametrize(
    "field,model_attr",
    [
        ("OriginAirport", "origin_airport"),
        ("DestinationAirport", "destination_airport"),
        ("RouteType", "route_type"),
        ("CycleDate", "cycle_date"),
    ],
)
def test_none_values_become_empty_strings(field, model_attr):
    df = make_df(
        [
            {
                "CompanyRouteIdentifier": "CR777",
                field: None,
            }
        ]
    )

    r = df_to_company_routes(df)[0]
    assert getattr(r, model_attr) == ""
