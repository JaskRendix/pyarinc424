from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class CompanyRouteLegModel:
    """ARINC 424 Company Route Leg (CL Record)."""

    company_route_identifier: str
    sequence_number: str
    fix_identifier: str
    path_terminator: str
    course: str
    distance: str
    altitude_description: str
    altitude_1: str
    altitude_2: str
    speed_limit: str
    cycle_date: str


def df_to_company_route_legs(df: pd.DataFrame) -> list[CompanyRouteLegModel]:
    """Converts a parsed Company Route Legs DataFrame (CL Records) into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    legs = []
    for _, row in df.iterrows():
        legs.append(
            CompanyRouteLegModel(
                company_route_identifier=clean(row.get("CompanyRouteIdentifier")),
                sequence_number=clean(row.get("SequenceNumber")),
                fix_identifier=clean(row.get("FixIdentifier")),
                path_terminator=clean(row.get("PathTerminator")),
                course=clean(row.get("Course")),
                distance=clean(row.get("Distance")),
                altitude_description=clean(row.get("AltitudeDescription")),
                altitude_1=clean(row.get("Altitude1")),
                altitude_2=clean(row.get("Altitude2")),
                speed_limit=clean(row.get("SpeedLimit")),
                cycle_date=clean(row.get("CycleDate")),
            )
        )
    return legs
