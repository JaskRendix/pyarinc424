from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class CompanyRouteModel:
    """ARINC 424 Company Route Header (CR Record)."""

    company_route_identifier: str
    origin_airport: str
    destination_airport: str
    route_type: str
    cycle_date: str


def df_to_company_routes(df: pd.DataFrame) -> list[CompanyRouteModel]:
    """Converts a parsed Company Routes DataFrame (CR Records) into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    routes = []
    for _, row in df.iterrows():
        routes.append(
            CompanyRouteModel(
                company_route_identifier=clean(row.get("CompanyRouteIdentifier")),
                origin_airport=clean(row.get("OriginAirport")),
                destination_airport=clean(row.get("DestinationAirport")),
                route_type=clean(row.get("RouteType")),
                cycle_date=clean(row.get("CycleDate")),
            )
        )
    return routes
