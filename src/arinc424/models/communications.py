from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class CommunicationModel:
    airport_identifier: str
    service_type: str
    frequency: str
    guard_frequency: str
    time_code: str
    sectorization: str
    latitude: float | None
    longitude: float | None
    cycle_date: str


def df_to_communications(df: pd.DataFrame) -> list[CommunicationModel]:
    """Converts a parsed Communications DataFrame into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    def clean_coord(value: Any) -> float | None:
        if value is None or pd.isna(value):
            return None
        return float(value)

    comms = []
    for _, row in df.iterrows():
        comms.append(
            CommunicationModel(
                airport_identifier=clean(row.get("AirportIdentifier")),
                service_type=clean(row.get("ServiceType")),
                frequency=clean(row.get("Frequency")),
                guard_frequency=clean(row.get("GuardFrequency")),
                time_code=clean(row.get("TimeCode")),
                sectorization=clean(row.get("Sectorization")),
                latitude=clean_coord(row.get("Latitude")),
                longitude=clean_coord(row.get("Longitude")),
                cycle_date=clean(row.get("CycleDate")),
            )
        )
    return comms
