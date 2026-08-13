from dataclasses import dataclass

import pandas as pd


@dataclass
class NavigationAidModel:
    identifier: str
    runway_identifier: str
    frequency: str
    latitude: float | None
    longitude: float | None
    facility_type: str
    cycle_date: str


def df_to_navigation_aids(
    df: pd.DataFrame, facility_type: str = "LOCALIZER"
) -> list[NavigationAidModel]:
    """Converts a parsed navigation aid DataFrame (Localizer, Glideslope, DME, MLS, GLS) into typed objects."""
    if df.empty:
        return []

    navaids = []
    for _, row in df.iterrows():
        # Dynamically determine the identifier column based on schema schema names
        ident_col = next(
            (c for c in df.columns if c.endswith("Identifier")), "LocalizerIdentifier"
        )
        lat_col = next((c for c in df.columns if "Latitude" in c), "LocalizerLatitude")
        lon_col = next(
            (c for c in df.columns if "Longitude" in c), "LocalizerLongitude"
        )
        freq_col = next(
            (c for c in df.columns if "Frequency" in c or "Channel" in c), "Frequency"
        )

        lat = row.get(lat_col)
        if pd.isna(lat):
            lat = None

        lon = row.get(lon_col)
        if pd.isna(lon):
            lon = None

        navaids.append(
            NavigationAidModel(
                identifier=str(row.get(ident_col, "")).strip(),
                runway_identifier=str(row.get("RunwayIdentifier", "")).strip(),
                frequency=str(row.get(freq_col, "")).strip(),
                latitude=lat,
                longitude=lon,
                facility_type=facility_type,
                cycle_date=str(row.get("CycleDate", "")).strip(),
            )
        )
    return navaids
