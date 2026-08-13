from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class AirwayRestrictionModel:
    airway_identifier: str
    from_waypoint: str
    to_waypoint: str
    minimum_altitude: str
    maximum_altitude: str
    rnav_requirement: str
    cycle_date: str


def df_to_airway_restrictions(df: pd.DataFrame) -> list[AirwayRestrictionModel]:
    """Converts a parsed Airway Restrictions DataFrame into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    restrictions = []
    for _, row in df.iterrows():
        restrictions.append(
            AirwayRestrictionModel(
                airway_identifier=clean(row.get("AirwayIdentifier")),
                from_waypoint=clean(row.get("FromWaypoint")),
                to_waypoint=clean(row.get("ToWaypoint")),
                minimum_altitude=clean(row.get("MinimumAltitude")),
                maximum_altitude=clean(row.get("MaximumAltitude")),
                rnav_requirement=clean(row.get("RNAVRequirement")),
                cycle_date=clean(row.get("CycleDate")),
            )
        )
    return restrictions
