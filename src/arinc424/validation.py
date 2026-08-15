from __future__ import annotations

from typing import Any

import pandas as pd

_MISSING_SENTINELS = {"", "nan", "none", "<na>", "null"}
_BOOL_TRUE = {"true", "t", "1", "y", "yes"}
_BOOL_FALSE = {"false", "f", "0", "n", "no"}


def _get_missing_mask(series: pd.Series) -> pd.Series:
    """Identify missing, NaN, or empty string values in a Series."""
    isna = series.isna()
    str_vals = series.astype(str).str.strip().str.lower()
    return isna | str_vals.isin(_MISSING_SENTINELS)


def _format_indices(indices: list[Any], max_display: int = 5) -> str:
    """Format a list of row indices for clear error reporting."""
    if not indices:
        return ""
    if len(indices) <= max_display:
        return f" (rows: {indices})"
    truncated = ", ".join(str(idx) for idx in indices[:max_display])
    return f" (rows: [{truncated}, ... and {len(indices) - max_display} more])"


def validate_dataframe_schema(
    df: pd.DataFrame, schema: dict, coerce: bool = False
) -> tuple[list[str], list[str], pd.DataFrame]:
    """Schema-driven DataFrame validator with fully vectorized constraints,

    row-index reporting, severity levels, and optional auto-coercion.

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
          severity: "error" | "warning" (default: "error")
    """
    errors: list[str] = []
    warnings: list[str] = []
    validated_df = df.copy() if coerce else df

    fields: dict[str, dict] = schema.get("fields", {})

    for field_name, rules in fields.items():
        severity = rules.get("severity", "error").lower()
        target_list = warnings if severity == "warning" else errors

        if field_name not in df.columns:
            if rules.get("required"):
                target_list.append(
                    f"Missing required field '{field_name}' in dataframe."
                )
            continue

        series = df[field_name]
        missing_mask = _get_missing_mask(series)
        present_mask = ~missing_mask
        count_missing = int(missing_mask.sum())

        # 1. Required Check
        if rules.get("required") and count_missing > 0:
            missing_indices = series[missing_mask].index.tolist()
            target_list.append(
                f"Field '{field_name}' has {count_missing} missing/empty values"
                f"{_format_indices(missing_indices)}."
            )

        if not present_mask.any():
            continue

        present_series = series[present_mask]
        expected_type = rules.get("type")

        # 2. Type Checking & Auto-Coercion
        if expected_type == "int":
            numeric = pd.to_numeric(present_series, errors="coerce")
            invalid_int = numeric.isna() | (numeric % 1 != 0)
            if invalid_int.any():
                invalid_indices = present_series[invalid_int].index.tolist()
                target_list.append(
                    f"Field '{field_name}' has {len(invalid_indices)} non-integer values"
                    f"{_format_indices(invalid_indices)}."
                )
            elif coerce:
                validated_df.loc[present_mask, field_name] = numeric.astype(int)

        elif expected_type == "float":
            numeric = pd.to_numeric(present_series, errors="coerce")
            invalid_float = numeric.isna()
            if invalid_float.any():
                invalid_indices = present_series[invalid_float].index.tolist()
                target_list.append(
                    f"Field '{field_name}' has {len(invalid_indices)} non-numeric values"
                    f"{_format_indices(invalid_indices)}."
                )
            elif coerce:
                validated_df.loc[present_mask, field_name] = numeric.astype(float)

        elif expected_type == "bool":
            lower_str = present_series.astype(str).str.strip().str.lower()
            valid_bools = lower_str.isin(_BOOL_TRUE | _BOOL_FALSE)
            if (~valid_bools).any():
                invalid_indices = present_series[~valid_bools].index.tolist()
                target_list.append(
                    f"Field '{field_name}' has {len(invalid_indices)} non-boolean values"
                    f"{_format_indices(invalid_indices)}."
                )
            elif coerce:
                mapping = {val: True for val in _BOOL_TRUE} | {
                    val: False for val in _BOOL_FALSE
                }
                validated_df.loc[present_mask, field_name] = lower_str.map(mapping)

        elif expected_type == "string" and coerce:
            validated_df.loc[present_mask, field_name] = present_series.astype(str)

        # Re-evaluate present series numerical values if coerced or needed for bounds
        current_series = validated_df[field_name][present_mask]

        # 3. Numeric Bounds
        if expected_type in {"int", "float"}:
            min_val = rules.get("min")
            max_val = rules.get("max")
            numeric = pd.to_numeric(current_series, errors="coerce")

            if min_val is not None:
                below = numeric < min_val
                if below.any():
                    indices = current_series[below].index.tolist()
                    target_list.append(
                        f"Field '{field_name}' has {len(indices)} values below minimum {min_val}"
                        f"{_format_indices(indices)}."
                    )

            if max_val is not None:
                above = numeric > max_val
                if above.any():
                    indices = current_series[above].index.tolist()
                    target_list.append(
                        f"Field '{field_name}' has {len(indices)} values above maximum {max_val}"
                        f"{_format_indices(indices)}."
                    )

        # 4. String Length Constraints
        if expected_type == "string":
            str_series = current_series.astype(str)
            min_len = rules.get("min_length")
            max_len = rules.get("max_length")

            if min_len is not None:
                too_short = str_series.str.len() < min_len
                if too_short.any():
                    indices = current_series[too_short].index.tolist()
                    target_list.append(
                        f"Field '{field_name}' has {len(indices)} values shorter than {min_len} characters"
                        f"{_format_indices(indices)}."
                    )

            if max_len is not None:
                too_long = str_series.str.len() > max_len
                if too_long.any():
                    indices = current_series[too_long].index.tolist()
                    target_list.append(
                        f"Field '{field_name}' has {len(indices)} values longer than {max_len} characters"
                        f"{_format_indices(indices)}."
                    )

        # 5. Enum Constraints
        enum_vals = rules.get("enum")
        if enum_vals:
            str_series = current_series.astype(str)
            allowed = {str(v) for v in enum_vals}
            invalid_enum = ~str_series.isin(allowed)
            if invalid_enum.any():
                indices = current_series[invalid_enum].index.tolist()
                target_list.append(
                    f"Field '{field_name}' has {len(indices)} values not in allowed set {enum_vals}"
                    f"{_format_indices(indices)}."
                )

        # 6. Regex Pattern Constraints
        pattern = rules.get("pattern")
        if pattern:
            str_series = current_series.astype(str)
            invalid_pattern = ~str_series.str.fullmatch(pattern)
            if invalid_pattern.any():
                indices = current_series[invalid_pattern].index.tolist()
                target_list.append(
                    f"Field '{field_name}' has {len(indices)} values not matching pattern '{pattern}'"
                    f"{_format_indices(indices)}."
                )

    # Maintain backward compatibility if callers expect a single list of error strings
    # (Warnings can be appended or logged separately by the caller)
    return errors
