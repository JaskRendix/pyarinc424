from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class AvionicsModel:
    identifier: str
    record_type: str
    section_code: str
    subsection_code: str
    latitude: str
    longitude: str
    elevation: str
    cycle_date: str


def df_to_general_aviation(df: pd.DataFrame) -> list[AvionicsModel]:
    """Converts a parsed Avionics/General Aviation DataFrame into typed objects."""
    if df.empty:
        return []

    def clean_str(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    records = []
    for _, row in df.iterrows():

        ident_col = next(
            (
                c
                for c in df.columns
                if c.endswith("Identifier")
                or c == "WaypointIdentifier"
                or c == "NavaidIdentifier"
            ),
            "WaypointIdentifier",
        )

        lat_col = next(
            (c for c in df.columns if c.endswith("Latitude")),
            "WaypointLatitude",
        )

        lon_col = next(
            (c for c in df.columns if c.endswith("Longitude")),
            "WaypointLongitude",
        )

        elev_col = next(
            (
                c
                for c in df.columns
                if c.endswith("Elevation") or c == "AirportElevation"
            ),
            "AirportElevation",
        )

        records.append(
            AvionicsModel(
                identifier=clean_str(row.get(ident_col)),
                record_type=clean_str(row.get("RecordType")),
                section_code=clean_str(row.get("SectionCode")),
                subsection_code=clean_str(row.get("SubsectionCode")),
                latitude=clean_str(row.get(lat_col)),
                longitude=clean_str(row.get(lon_col)),
                elevation=clean_str(row.get(elev_col)),
                cycle_date=clean_str(row.get("CycleDate")),
            )
        )

    return records
