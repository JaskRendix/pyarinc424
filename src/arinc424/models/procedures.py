from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class ProcedureLegModel:
    airport_identifier: str
    procedure_identifier: str
    route_type: str
    transition_identifier: str
    sequence_number: str
    path_terminator: str
    fix_identifier: str
    course: str
    distance: str
    altitude_description: str
    altitude_1: str
    altitude_2: str
    speed_limit: str
    cycle_date: str


def df_to_procedure_legs(df: pd.DataFrame) -> list[ProcedureLegModel]:
    """Converts a parsed procedure DataFrame (SID, STAR, Approach, Missed Approach) into typed objects."""
    if df.empty:
        return []

    def clean(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    legs = []
    for _, row in df.iterrows():
        legs.append(
            ProcedureLegModel(
                airport_identifier=clean(row.get("AirportIdentifier")),
                procedure_identifier=clean(row.get("ProcedureIdentifier")),
                route_type=clean(row.get("RouteType")),
                transition_identifier=clean(row.get("TransitionIdentifier")),
                sequence_number=clean(row.get("SequenceNumber")),
                path_terminator=clean(row.get("PathTerminator")),
                fix_identifier=clean(row.get("FixIdentifier")),
                course=clean(row.get("Course")),
                distance=clean(row.get("Distance")),
                altitude_description=clean(row.get("AltitudeDescription")),
                altitude_1=clean(row.get("Altitude1")),
                altitude_2=clean(row.get("Altitude2")),
                speed_limit=clean(row.get("SpeedLimit")),
                cycle_date=clean(row.get("CycleDate")),
            )
        )
    return legs
