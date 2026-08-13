from __future__ import annotations

import re
from typing import Any

import pandas as pd


def _coerce_type(value: Any, expected: str) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    if expected == "string":
        return str(value)
    if expected == "int":
        try:
            return int(value)
        except Exception:
            return value
    if expected == "float":
        try:
            return float(value)
        except Exception:
            return value
    if expected == "bool":
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        if s in {"true", "t", "1", "y"}:
            return True
        if s in {"false", "f", "0", "n"}:
            return False
        return value
    return value


def validate_dataframe_schema(df: pd.DataFrame, schema: dict) -> list[str]:
    """
    Schema-driven validator.

    Expects schema to contain a 'fields' mapping:
      fields:
        FieldName:
          required: bool
          type: string|int|float|bool
          min: number
          max: number
          min_length: int
          max_length: int
          enum: [values...]
          pattern: regex
    """
    errors: list[str] = []

    fields: dict[str, dict] = schema.get("fields", {})

    for field_name, rules in fields.items():
        if field_name not in df.columns:
            if rules.get("required"):
                errors.append(f"Missing required field '{field_name}' in dataframe.")
            continue

        series = df[field_name]

        # Required: no empty/NaN values
        if rules.get("required"):
            missing = series.isna() | series.astype(str).str.strip().eq("")
            count_missing = int(missing.sum())
            if count_missing > 0:
                errors.append(
                    f"Field '{field_name}' has {count_missing} missing/empty values."
                )

        # Type coercion + type check
        expected_type = rules.get("type")
        if expected_type:
            coerced = series.map(lambda v: _coerce_type(v, expected_type))

            invalid_mask = pd.Series(False, index=series.index)

            if expected_type == "int":
                invalid_mask |= coerced.apply(
                    lambda v: v is not None and not isinstance(v, int)
                )

            elif expected_type == "float":
                invalid_mask |= coerced.apply(
                    lambda v: v is not None and not isinstance(v, float)
                )

            elif expected_type == "string":
                invalid_mask |= coerced.apply(
                    lambda v: v is not None and not isinstance(v, str)
                )

            elif expected_type == "bool":
                invalid_mask |= coerced.apply(
                    lambda v: v is not None and not isinstance(v, bool)
                )

            invalid_count = int(invalid_mask.sum())
            if invalid_count > 0:
                errors.append(
                    f"Field '{field_name}' has {invalid_count} values not matching type '{expected_type}'."
                )

        # Numeric bounds
        if expected_type in {"int", "float"}:
            min_val = rules.get("min")
            max_val = rules.get("max")
            numeric = pd.to_numeric(series, errors="coerce")

            if min_val is not None:
                below = numeric < min_val
                count_below = int(below.sum())
                if count_below > 0:
                    errors.append(
                        f"Field '{field_name}' has {count_below} values below minimum {min_val}."
                    )

            if max_val is not None:
                above = numeric > max_val
                count_above = int(above.sum())
                if count_above > 0:
                    errors.append(
                        f"Field '{field_name}' has {count_above} values above maximum {max_val}."
                    )

        # String length constraints
        if expected_type == "string":
            s = series.astype(str)
            min_len = rules.get("min_length")
            max_len = rules.get("max_length")

            if min_len is not None:
                too_short = s.str.len() < min_len
                count_short = int(too_short.sum())
                if count_short > 0:
                    errors.append(
                        f"Field '{field_name}' has {count_short} values shorter than {min_len} characters."
                    )

            if max_len is not None:
                too_long = s.str.len() > max_len
                count_long = int(too_long.sum())
                if count_long > 0:
                    errors.append(
                        f"Field '{field_name}' has {count_long} values longer than {max_len} characters."
                    )

        # Enum constraints
        enum_vals = rules.get("enum")
        if enum_vals:
            s = series.astype(str)
            invalid_enum = ~s.isin([str(v) for v in enum_vals])
            count_invalid_enum = int(invalid_enum.sum())
            if count_invalid_enum > 0:
                errors.append(
                    f"Field '{field_name}' has {count_invalid_enum} values not in allowed set {enum_vals}."
                )

        # Regex pattern
        pattern = rules.get("pattern")
        if pattern:
            s = series.astype(str)
            invalid_pattern = ~s.str.fullmatch(pattern)
            count_invalid_pattern = int(invalid_pattern.sum())
            if count_invalid_pattern > 0:
                errors.append(
                    f"Field '{field_name}' has {count_invalid_pattern} values not matching pattern '{pattern}'."
                )

    return errors
