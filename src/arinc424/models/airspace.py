from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class AirspaceModel:
    identifier: str
    airspace_class: str
    boundary_via: str
    boundary_point: str
    lower_limit: str
    upper_limit: str
    airspace_type: str
    airspace_control: str
    cycle_date: str


def df_to_airspaces(df: pd.DataFrame) -> list[AirspaceModel]:
    """Converts a parsed Airspace DataFrame into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    airspaces = []
    for _, row in df.iterrows():

        ident_col = next(
            (
                c
                for c in df.columns
                if c.endswith("Identifier") or c.endswith("AirspaceIdentifier")
            ),
            "AirspaceIdentifier",
        )

        class_col = next(
            (
                c
                for c in df.columns
                if c.endswith("Class") or c.endswith("AirspaceClass")
            ),
            "AirspaceClass",
        )

        type_col = next(
            (c for c in df.columns if c.endswith("Type") or c.endswith("AirspaceType")),
            "AirspaceType",
        )

        control_col = next(
            (
                c
                for c in df.columns
                if c.endswith("Control") or c.endswith("AirspaceControl")
            ),
            "AirspaceControl",
        )

        airspaces.append(
            AirspaceModel(
                identifier=clean(row.get(ident_col)),
                airspace_class=clean(row.get(class_col)),
                boundary_via=clean(row.get("BoundaryVia")),
                boundary_point=clean(row.get("BoundaryPoint")),
                lower_limit=clean(row.get("LowerLimit")),
                upper_limit=clean(row.get("UpperLimit")),
                airspace_type=clean(row.get(type_col)),
                airspace_control=clean(row.get(control_col)),
                cycle_date=clean(row.get("CycleDate")),
            )
        )

    return airspaces
