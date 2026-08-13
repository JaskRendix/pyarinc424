from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class ExtendedCommunicationModel:
    identifier: str
    service_type: str
    frequency: str
    guard_frequency: str
    time_code: str
    sectorization: str
    latitude: float | None
    longitude: float | None
    cycle_date: str


def df_to_extended_communications(df: pd.DataFrame) -> list[ExtendedCommunicationModel]:
    """Converts a parsed Extended Communications DataFrame into typed objects."""
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

        ident_col = next(
            (
                c
                for c in df.columns
                if c.endswith("Identifier") or c.endswith("StationIdentifier")
            ),
            "AirportIdentifier",
        )

        freq_col = next(
            (c for c in df.columns if c.endswith("Frequency") or c == "Frequency"),
            "Frequency",
        )

        service_col = (
            "ServiceType"
            if "ServiceType" in df.columns
            else "BroadcastType" if "BroadcastType" in df.columns else None
        )

        comms.append(
            ExtendedCommunicationModel(
                identifier=clean(row.get(ident_col)),
                service_type=clean(row.get(service_col)),
                frequency=clean(row.get(freq_col)),
                guard_frequency=clean(row.get("GuardFrequency")),
                time_code=clean(row.get("TimeCode")),
                sectorization=clean(row.get("Sectorization")),
                latitude=clean_coord(row.get("Latitude")),
                longitude=clean_coord(row.get("Longitude")),
                cycle_date=clean(row.get("CycleDate")),
            )
        )
    return comms
