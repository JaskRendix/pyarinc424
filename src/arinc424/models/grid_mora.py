from dataclasses import dataclass

import pandas as pd


@dataclass
class GridMoraModel:
    latitude_band: str
    longitude_band: str
    mora_altitude: str
    mora_type: str
    latitude: float | None
    longitude: float | None
    cycle_date: str


def df_to_grid_mora(df: pd.DataFrame) -> list[GridMoraModel]:
    """Converts a parsed Grid MORA DataFrame into typed objects."""
    if df.empty:
        return []

    records = []
    for _, row in df.iterrows():

        lat = row.get("Latitude")
        if pd.isna(lat):
            lat = None

        lon = row.get("Longitude")
        if pd.isna(lon):
            lon = None

        records.append(
            GridMoraModel(
                latitude_band=str(row.get("LatitudeBand", "")).strip(),
                longitude_band=str(row.get("LongitudeBand", "")).strip(),
                mora_altitude=str(row.get("MORAAltitude", "")).strip(),
                mora_type=str(row.get("MORAType", "")).strip(),
                latitude=lat,
                longitude=lon,
                cycle_date=str(row.get("CycleDate", "")).strip(),
            )
        )
    return records
