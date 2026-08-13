import pandas as pd
import pytest

from arinc424.validation import validate_dataframe_schema


def test_required_field_missing_column():
    df = pd.DataFrame({"A": [1, 2]})
    schema = {"fields": {"MissingField": {"required": True}}}
    errors = validate_dataframe_schema(df, schema)
    assert "Missing required field 'MissingField'" in errors[0]


def test_required_field_empty_values():
    df = pd.DataFrame({"A": ["", "   ", None]})
    schema = {"fields": {"A": {"required": True}}}
    errors = validate_dataframe_schema(df, schema)
    assert "Field 'A' has 3 missing/empty values." in errors


@pytest.mark.parametrize(
    "value,expected_type,valid",
    [
        ("123", "int", True),
        ("abc", "int", False),
        ("12.5", "float", True),
        ("abc", "float", False),
        ("true", "bool", True),
        ("FALSE", "bool", True),
        ("maybe", "bool", False),
        (123, "string", True),
    ],
)
def test_type_validation(value, expected_type, valid):
    df = pd.DataFrame({"A": [value]})
    schema = {"fields": {"A": {"type": expected_type}}}
    errors = validate_dataframe_schema(df, schema)
    assert (len(errors) == 0) if valid else (len(errors) == 1)


def test_numeric_bounds_min():
    df = pd.DataFrame({"A": [1, 2, 3]})
    schema = {"fields": {"A": {"type": "int", "min": 2}}}
    errors = validate_dataframe_schema(df, schema)
    assert "below minimum 2" in errors[0]


def test_numeric_bounds_max():
    df = pd.DataFrame({"A": [1, 2, 3]})
    schema = {"fields": {"A": {"type": "int", "max": 2}}}
    errors = validate_dataframe_schema(df, schema)
    assert "above maximum 2" in errors[0]


def test_numeric_bounds_valid():
    df = pd.DataFrame({"A": [5, 6, 7]})
    schema = {"fields": {"A": {"type": "int", "min": 1, "max": 10}}}
    errors = validate_dataframe_schema(df, schema)
    assert errors == []


def test_string_min_length():
    df = pd.DataFrame({"A": ["a", "bb", "ccc"]})
    schema = {"fields": {"A": {"type": "string", "min_length": 2}}}
    errors = validate_dataframe_schema(df, schema)
    assert "shorter than 2 characters" in errors[0]


def test_string_max_length():
    df = pd.DataFrame({"A": ["aaa", "bb", "c"]})
    schema = {"fields": {"A": {"type": "string", "max_length": 2}}}
    errors = validate_dataframe_schema(df, schema)
    assert "longer than 2 characters" in errors[0]


def test_string_length_valid():
    df = pd.DataFrame({"A": ["aa", "bb", "cc"]})
    schema = {"fields": {"A": {"type": "string", "min_length": 2, "max_length": 2}}}
    errors = validate_dataframe_schema(df, schema)
    assert errors == []


def test_enum_invalid():
    df = pd.DataFrame({"A": ["X", "Y", "Z"]})
    schema = {"fields": {"A": {"enum": ["X", "Y"]}}}
    errors = validate_dataframe_schema(df, schema)
    assert "not in allowed set" in errors[0]


def test_enum_valid():
    df = pd.DataFrame({"A": ["X", "Y"]})
    schema = {"fields": {"A": {"enum": ["X", "Y"]}}}
    errors = validate_dataframe_schema(df, schema)
    assert errors == []


def test_regex_invalid():
    df = pd.DataFrame({"A": ["ABC", "123", "A1B2"]})
    schema = {"fields": {"A": {"pattern": r"^[A-Z]+$"}}}
    errors = validate_dataframe_schema(df, schema)
    assert "not matching pattern" in errors[0]


def test_regex_valid():
    df = pd.DataFrame({"A": ["ABC", "XYZ"]})
    schema = {"fields": {"A": {"pattern": r"^[A-Z]+$"}}}
    errors = validate_dataframe_schema(df, schema)
    assert errors == []


def test_multiple_rules_combined():
    df = pd.DataFrame({"A": ["ABC", "12", ""]})
    schema = {
        "fields": {
            "A": {
                "required": True,
                "type": "string",
                "min_length": 2,
                "max_length": 3,
                "pattern": r"^[A-Z]+$",
            }
        }
    }
    errors = validate_dataframe_schema(df, schema)

    assert len(errors) == 3
    assert any("missing/empty" in e for e in errors)
    assert any("not matching pattern" in e for e in errors)
    assert any("shorter than" in e for e in errors)


def test_type_coercion_edge_cases():
    df = pd.DataFrame({"A": [" 123 ", "  45", "abc"]})
    schema = {"fields": {"A": {"type": "int"}}}
    errors = validate_dataframe_schema(df, schema)
    assert len(errors) == 1  # "abc" fails


def test_nan_handling():
    df = pd.DataFrame({"A": [None, float("nan"), ""]})
    schema = {"fields": {"A": {"required": True}}}
    errors = validate_dataframe_schema(df, schema)
    assert "missing/empty" in errors[0]


def test_missing_field_not_required():
    df = pd.DataFrame({"A": [1, 2]})
    schema = {"fields": {"B": {"required": False}}}
    errors = validate_dataframe_schema(df, schema)
    assert errors == []
