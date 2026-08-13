from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class AirwayModel:
    airway_identifier: str
    from_waypoint: str
    to_waypoint: str
    minimum_altitude: str
    maximum_altitude: str
    airway_type: str
    airway_direction: str
    cycle_date: str


def df_to_airways(df: pd.DataFrame) -> list[AirwayModel]:
    """Converts a parsed Airways DataFrame into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    airways = []
    for _, row in df.iterrows():
        airways.append(
            AirwayModel(
                airway_identifier=clean(row.get("AirwayIdentifier")),
                from_waypoint=clean(row.get("FromWaypoint")),
                to_waypoint=clean(row.get("ToWaypoint")),
                minimum_altitude=clean(row.get("MinimumAltitude")),
                maximum_altitude=clean(row.get("MaximumAltitude")),
                airway_type=clean(row.get("AirwayType")),
                airway_direction=clean(row.get("AirwayDirection")),
                cycle_date=clean(row.get("CycleDate")),
            )
        )
    return airways
