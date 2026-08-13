from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

from arinc424.models.airport_infrastructure import df_to_airport_infrastructure
from arinc424.models.airspace import df_to_airspaces
from arinc424.models.airspace_boundaries import df_to_airspace_boundaries
from arinc424.models.airway_restrictions import df_to_airway_restrictions
from arinc424.models.airways import df_to_airways
from arinc424.models.avionics import df_to_general_aviation
from arinc424.models.communications import df_to_communications
from arinc424.models.company_routes import df_to_company_routes
from arinc424.models.grid_mora import df_to_grid_mora
from arinc424.models.heliport_procedures import df_to_heliport_procedures
from arinc424.models.navigation_aids import df_to_navigation_aids
from arinc424.models.procedures import df_to_procedure_legs
from arinc424.models.waypoints import df_to_waypoints

logger = logging.getLogger(__name__)
Converter = Callable[[pd.DataFrame], Iterable[object]]


@dataclass
class SchemaRegistry:
    schemas: dict[str, dict] = field(default_factory=dict)
    routing: dict[str, dict[str, str]] = field(default_factory=dict)
    continuation_rules: dict[str, list[str]] = field(default_factory=dict)
    model_converters: dict[str, Converter] = field(default_factory=dict)


def _schemas_dir() -> Path:
    return Path(__file__).parent


def _load_yaml_schemas() -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    for path in _schemas_dir().glob("*.yaml"):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        name = data.get("name") or path.stem
        if name in schemas:
            raise ValueError(
                f"Duplicate schema name '{name}' found in {path} (already loaded)"
            )
        schemas[name] = data
    return schemas


def _load_routing_table() -> dict[str, dict[str, str]]:
    routing_path = _schemas_dir() / "routing.json"
    if routing_path.exists():
        with open(routing_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _load_continuation_rules() -> dict[str, list[str]]:
    cont_path = _schemas_dir() / "continuations.json"
    if cont_path.exists():
        with open(cont_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _build_model_converters() -> dict[str, Converter]:
    return {
        # schema_name -> converter
        "Waypoints": df_to_waypoints,
        "Airports": df_to_airport_infrastructure,
        "Airspaces": df_to_airspaces,
        "AirspaceBoundaries": df_to_airspace_boundaries,
        "Airways": df_to_airways,
        "Communications": df_to_communications,
        "CompanyRoutes": df_to_company_routes,
        "GridMora": df_to_grid_mora,
        "HeliportProcedures": df_to_heliport_procedures,
        "NavigationAids": df_to_navigation_aids,
        "ProcedureLegs": df_to_procedure_legs,
        "GeneralAviation": df_to_general_aviation,
        "AirwayRestrictions": df_to_airway_restrictions,
    }


@lru_cache(maxsize=1)
def load_all_icd_schemas() -> SchemaRegistry:
    registry = SchemaRegistry()
    registry.schemas = _load_yaml_schemas()
    registry.routing = _load_routing_table()
    registry.continuation_rules = _load_continuation_rules()
    registry.model_converters = _build_model_converters()
    return registry
