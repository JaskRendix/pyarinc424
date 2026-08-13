from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class AirportInfrastructureModel:
    airport_identifier: str
    feature_identifier: str
    feature_type: str
    latitude: str
    longitude: str
    magnetic_variation: str
    cycle_date: str


def df_to_airport_infrastructure(df: pd.DataFrame) -> list[AirportInfrastructureModel]:
    """Converts a parsed Airport Infrastructure DataFrame into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    infrastructure = []
    for _, row in df.iterrows():
        ident_col = next(
            (
                c
                for c in df.columns
                if c.endswith("Identifier") and c != "AirportIdentifier"
            ),
            "TaxiwayIdentifier",
        )

        type_col = next(
            (c for c in df.columns if c.endswith("Type") or c.endswith("SystemType")),
            "TaxiwayType",
        )

        lat_col = next(
            (
                c
                for c in df.columns
                if c in ("Latitude", "StartLatitude", "StandLatitude")
            ),
            "Latitude",
        )

        lon_col = next(
            (
                c
                for c in df.columns
                if c in ("Longitude", "StartLongitude", "StandLongitude")
            ),
            "Longitude",
        )

        infrastructure.append(
            AirportInfrastructureModel(
                airport_identifier=clean(row.get("AirportIdentifier")),
                feature_identifier=clean(row.get(ident_col)),
                feature_type=clean(row.get(type_col)),
                latitude=clean(row.get(lat_col)),
                longitude=clean(row.get(lon_col)),
                magnetic_variation=clean(row.get("MagneticVariation")),
                cycle_date=clean(row.get("CycleDate")),
            )
        )
    return infrastructure
