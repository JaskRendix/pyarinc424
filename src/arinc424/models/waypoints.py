from dataclasses import dataclass

import pandas as pd


@dataclass
class WaypointModel:
    identifier: str
    latitude: float | None
    longitude: float | None
    waypoint_type: str
    usage: str
    cycle_date: str


def df_to_waypoints(df: pd.DataFrame) -> list[WaypointModel]:
    """Converts a parsed DataFrame of waypoints or fixes into a list of typed WaypointModel objects."""
    if df.empty:
        return []

    waypoints = []
    for _, row in df.iterrows():
        # Dynamically find identifier, type, and usage columns based on naming patterns in schemas
        ident_col = next(
            (c for c in df.columns if c.endswith("Identifier")), "WaypointIdentifier"
        )
        type_col = next((c for c in df.columns if c.endswith("Type")), "WaypointType")
        usage_col = next(
            (c for c in df.columns if c.endswith("Usage")), "WaypointUsage"
        )

        lat = row.get("Latitude_decimal")
        if pd.isna(lat):
            lat = row.get("Latitude")

        lon = row.get("Longitude_decimal")
        if pd.isna(lon):
            lon = row.get("Longitude")

        waypoints.append(
            WaypointModel(
                identifier=str(row.get(ident_col, "")).strip(),
                latitude=lat,
                longitude=lon,
                waypoint_type=str(row.get(type_col, "")).strip(),
                usage=str(row.get(usage_col, "")).strip(),
                cycle_date=str(row.get("CycleDate", "")).strip(),
            )
        )

    return waypoints
