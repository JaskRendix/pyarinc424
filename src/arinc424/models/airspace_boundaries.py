from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class AirspaceBoundaryModel:
    identifier: str
    airspace_class: str
    boundary_via: str
    boundary_point_identifier: str
    lower_limit: str
    upper_limit: str
    airspace_type: str
    airspace_control: str
    cycle_date: str


def df_to_airspace_boundaries(df: pd.DataFrame) -> list[AirspaceBoundaryModel]:
    """Converts a parsed Airspace Boundaries DataFrame into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    boundaries = []
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

        boundaries.append(
            AirspaceBoundaryModel(
                identifier=clean(row.get(ident_col)),
                airspace_class=clean(row.get(class_col)),
                boundary_via=clean(row.get("BoundaryVia")),
                boundary_point_identifier=clean(row.get("BoundaryPointIdentifier")),
                lower_limit=clean(row.get("LowerLimit")),
                upper_limit=clean(row.get("UpperLimit")),
                airspace_type=clean(row.get(type_col)),
                airspace_control=clean(row.get(control_col)),
                cycle_date=clean(row.get("CycleDate")),
            )
        )

    return boundaries
