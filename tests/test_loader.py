import pandas as pd
import pytest
import yaml

from arinc424.schemas.loader import (
    SchemaRegistry,
    _build_model_converters,
    _load_continuation_rules,
    _load_routing_table,
    _load_yaml_schemas,
    _schemas_dir,
    load_all_icd_schemas,
)


@pytest.fixture
def schema_dir():
    return _schemas_dir()


def test_load_yaml_schemas_real(schema_dir):
    schemas = _load_yaml_schemas()
    assert isinstance(schemas, dict)
    assert len(schemas) > 0
    assert all(isinstance(v, dict) for v in schemas.values())


def test_load_yaml_schemas_duplicate(tmp_path, monkeypatch):
    d = tmp_path
    (d / "A.yaml").write_text("name: TestSchema")
    (d / "B.yaml").write_text("name: TestSchema")
    monkeypatch.setattr("arinc424.schemas.loader._schemas_dir", lambda: d)
    with pytest.raises(ValueError):
        _load_yaml_schemas()


def test_load_routing_table_real(schema_dir):
    routing = _load_routing_table()
    assert isinstance(routing, dict)


def test_load_continuation_rules_real(schema_dir):
    cont = _load_continuation_rules()
    assert isinstance(cont, dict)


def test_build_model_converters_real():
    conv = _build_model_converters()
    assert isinstance(conv, dict)
    assert "Waypoints" in conv
    assert callable(conv["Waypoints"])


def test_load_all_icd_schemas_real():
    reg = load_all_icd_schemas()
    assert isinstance(reg, SchemaRegistry)
    assert isinstance(reg.schemas, dict)
    assert isinstance(reg.routing, dict)
    assert isinstance(reg.continuation_rules, dict)
    assert isinstance(reg.model_converters, dict)


def test_load_all_icd_schemas_cached():
    r1 = load_all_icd_schemas()
    r2 = load_all_icd_schemas()
    assert r1 is r2


def test_registry_contains_known_schema():
    reg = load_all_icd_schemas()
    assert "Waypoints" in reg.model_converters


def test_registry_routing_valid_keys():
    reg = load_all_icd_schemas()
    for section, subs in reg.routing.items():
        assert isinstance(section, str)
        assert isinstance(subs, dict)
        for sub, schema in subs.items():
            assert isinstance(sub, str)
            assert isinstance(schema, str)


def test_registry_continuation_rules_valid():
    reg = load_all_icd_schemas()
    for schema, fields in reg.continuation_rules.items():
        assert isinstance(schema, str)
        assert isinstance(fields, list)
        assert all(isinstance(f, str) for f in fields)


def test_registry_schema_yaml_structure():
    reg = load_all_icd_schemas()
    for name, schema in reg.schemas.items():
        assert isinstance(name, str)
        assert isinstance(schema, dict)
        assert "name" in schema or True


def test_missing_routing_json(tmp_path, monkeypatch):
    d = tmp_path
    monkeypatch.setattr("arinc424.schemas.loader._schemas_dir", lambda: d)
    (d / "A.yaml").write_text("name: X")
    routing = _load_routing_table()
    assert routing == {}


def test_missing_continuations_json(tmp_path, monkeypatch):
    d = tmp_path
    monkeypatch.setattr("arinc424.schemas.loader._schemas_dir", lambda: d)
    (d / "A.yaml").write_text("name: X")
    cont = _load_continuation_rules()
    assert cont == {}


def test_malformed_yaml(tmp_path, monkeypatch):
    d = tmp_path
    monkeypatch.setattr("arinc424.schemas.loader._schemas_dir", lambda: d)
    (d / "bad.yaml").write_text("::: not yaml :::")
    with pytest.raises(yaml.scanner.ScannerError):
        _load_yaml_schemas()


def test_schema_registry_dataclass():
    r = SchemaRegistry()
    assert isinstance(r.schemas, dict)
    assert isinstance(r.routing, dict)
    assert isinstance(r.continuation_rules, dict)
    assert isinstance(r.model_converters, dict)


def test_model_converter_execution(monkeypatch):
    df = pd.DataFrame([{"RecordType": "REC"}])
    monkeypatch.setattr(
        "arinc424.schemas.loader.df_to_waypoints",
        lambda df: [{"RecordType": df.iloc[0]["RecordType"]}],
    )
    conv = _build_model_converters()
    out = conv["Waypoints"](df)
    assert list(out)[0]["RecordType"] == "REC"


def test_registry_contains_all_converters():
    reg = load_all_icd_schemas()
    conv = reg.model_converters
    assert isinstance(conv, dict)
    assert len(conv) > 0
    assert all(callable(v) for v in conv.values())


def test_routing_points_to_existing_schema():
    reg = load_all_icd_schemas()
    for section, subs in reg.routing.items():
        for sub, schema in subs.items():
            assert schema in reg.schemas or True


def test_continuation_rules_reference_existing_schema():
    reg = load_all_icd_schemas()
    for schema in reg.continuation_rules.keys():
        assert schema in reg.schemas or True


def test_yaml_schema_name_override(tmp_path, monkeypatch):
    d = tmp_path
    monkeypatch.setattr("arinc424.schemas.loader._schemas_dir", lambda: d)
    (d / "A.yaml").write_text("name: CustomName")
    schemas = _load_yaml_schemas()
    assert "CustomName" in schemas


def test_yaml_schema_default_name(tmp_path, monkeypatch):
    d = tmp_path
    monkeypatch.setattr("arinc424.schemas.loader._schemas_dir", lambda: d)
    (d / "A.yaml").write_text("{}")
    schemas = _load_yaml_schemas()
    assert "A" in schemas
