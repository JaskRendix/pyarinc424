import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import click
import pandas as pd
import pytest
from click.testing import CliRunner

from arinc424 import parser
from arinc424.cli import _json_default, cli


def build_line(record_type, section, subsection, fileno, contno, name):
    cont = contno if contno else "  "
    return (
        f"{record_type}{section}{subsection}"
        f"{str(fileno).zfill(5)}"
        f"{cont}"
        f"{name.ljust(20)}"
    )


@dataclass
class DummyModel:
    RecordType: str = "REC"
    Section: str = "E"
    Subsection: str = "A"
    FileRecordNo: str = "00001"
    ContinuationRecordNo: str = ""
    Name: str = "WP1"


class DummyRegistry:
    def __init__(self):
        self.routing = {"E": {"A": "Waypoints"}}
        self.schemas = {
            "Waypoints": {
                "fields": {
                    "RecordType": {"required": True, "type": "string"},
                    "Name": {"required": True, "type": "string"},
                },
                "names": [
                    "RecordType",
                    "Section",
                    "Subsection",
                    "FileRecordNo",
                    "ContinuationRecordNo",
                    "Name",
                ],
                "colspecs": [(0, 3), (3, 4), (4, 5), (5, 10), (10, 12), (12, 32)],
            }
        }
        self.model_converters = {
            "Waypoints": lambda df: [
                DummyModel(**r.to_dict()) for _, r in df.iterrows()
            ]
        }
        self.continuation_rules = {}


@pytest.fixture(autouse=True)
def patch_registry(monkeypatch):
    dummy = DummyRegistry()
    monkeypatch.setattr("arinc424.cli.get_registry", lambda: dummy)
    monkeypatch.setattr("arinc424.parser._REGISTRY", dummy)
    return dummy


@pytest.fixture(autouse=True)
def patch_click_path(monkeypatch):
    def fake_convert(self, value, param, ctx):
        return Path(value)

    monkeypatch.setattr(click.Path, "convert", fake_convert, raising=False)


@pytest.fixture
def runner():
    return CliRunner()


def test_parse_basic(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    p.write_text(build_line("REC", "E", "A", "00001", "", "WP1") + "\n")

    monkeypatch.setattr(
        parser,
        "parse_arinc_file",
        lambda f, record_filter: (
            "Waypoints",
            pd.DataFrame(
                [
                    {
                        "RecordType": "REC",
                        "Section": "E",
                        "Subsection": "A",
                        "FileRecordNo": "00001",
                        "ContinuationRecordNo": "",
                        "Name": "WP1",
                    }
                ]
            ),
        ),
    )

    result = runner.invoke(cli, ["parse", str(p), "-f", "EA"])
    assert "Parsed 1 records." in result.output


def test_parse_limit(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    p.write_text(
        build_line("REC", "E", "A", "00001", "", "A")
        + "\n"
        + build_line("REC", "E", "A", "00002", "", "B")
        + "\n"
    )

    df = pd.DataFrame(
        [
            {
                "RecordType": "REC",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00001",
                "ContinuationRecordNo": "",
                "Name": "A",
            },
            {
                "RecordType": "REC",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00002",
                "ContinuationRecordNo": "",
                "Name": "B",
            },
        ]
    )

    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    result = runner.invoke(cli, ["parse", str(p), "-f", "EA", "--limit", "1"])
    assert "Parsed 1 records." in result.output


def test_parse_model_conversion(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    p.write_text(build_line("REC", "E", "A", "00001", "", "WP1") + "\n")

    df = pd.DataFrame(
        [
            {
                "RecordType": "REC",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00001",
                "ContinuationRecordNo": "",
                "Name": "WP1",
            }
        ]
    )
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    result = runner.invoke(cli, ["parse", str(p), "-f", "EA", "--model"])
    assert "Converted 1 records using model 'Waypoints'." in result.output
    assert '"RecordType": "REC"' in result.output


def test_parse_model_no_converter(tmp_path, runner, monkeypatch, patch_registry):
    patch_registry.model_converters = {}
    p = tmp_path / "file.arinc"
    p.write_text("X\n")

    df = pd.DataFrame([{"RecordType": "REC", "Name": "WP1"}])
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    result = runner.invoke(cli, ["parse", str(p), "-f", "EA", "--model"])
    assert "Falling back to raw dictionaries" in result.output


def test_parse_output_json(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    out = tmp_path / "out.json"
    p.write_text(build_line("REC", "E", "A", "00001", "", "WP1") + "\n")

    df = pd.DataFrame(
        [
            {
                "RecordType": "REC",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00001",
                "ContinuationRecordNo": "",
                "Name": "WP1",
            }
        ]
    )
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    runner.invoke(cli, ["parse", str(p), "-f", "EA", "-o", str(out)])
    data = json.loads(out.read_text())
    assert data[0]["Name"] == "WP1"


def test_parse_validation_errors(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    p.write_text(build_line("REC", "E", "A", "00001", "", "") + "\n")

    df = pd.DataFrame(
        [
            {
                "RecordType": "",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00001",
                "ContinuationRecordNo": "",
                "Name": "",
            }
        ]
    )
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    result = runner.invoke(cli, ["parse", str(p), "-f", "EA"])
    assert "Validation found" in result.output


def test_parse_invalid_filter(tmp_path, runner):
    p = tmp_path / "file.arinc"
    p.write_text("X\n")
    result = runner.invoke(cli, ["parse", str(p), "-f", "Z"])
    assert result.exit_code != 0


def test_header_command(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    p.write_text("HDRSOMEHDR 12342025\n")

    monkeypatch.setattr(
        parser,
        "parse_header_details",
        lambda f: {"cycle_date": "1234", "effective_date": "2025"},
    )
    result = runner.invoke(cli, ["header", str(p)])
    assert '"cycle_date": "1234"' in result.output


def test_schemas_command(runner, patch_registry):
    result = runner.invoke(cli, ["schemas"])
    assert "Waypoints" in result.output


def test_parse_file_not_found(runner):
    result = runner.invoke(cli, ["parse", "missing.arinc", "-f", "EA"])
    assert "Error" in result.output


def test_header_file_not_found(runner):
    result = runner.invoke(cli, ["header", "missing.arinc"])
    assert result.exit_code != 0


def test_parse_strict_validation_error(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    p.write_text("REC\n")

    df = pd.DataFrame([{"RecordType": "REC", "Name": "WP1"}])
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    # Mock the validation function used in cli.py to return validation errors
    import arinc424.cli as cli_module

    monkeypatch.setattr(
        cli_module,
        "validate_dataframe_schema",
        lambda section_name, df: ["Schema validation error: invalid field"],
    )

    result = runner.invoke(cli, ["parse", str(p), "-f", "EA", "--strict"])
    assert result.exit_code != 0
    assert "strict mode" in result.output


def test_json_default_serializer():
    assert _json_default(date(2026, 6, 1)) == "2026-06-01"
    assert sorted(_json_default({"a", "b"})) == [
        "a",
        "b",
    ]  # Sort to handle set order deterministically
    assert _json_default(12345) == "12345"


def test_parse_export_csv(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    out = tmp_path / "out.csv"
    p.write_text(build_line("REC", "E", "A", "00001", "", "WP1") + "\n")

    df = pd.DataFrame(
        [
            {
                "RecordType": "REC",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00001",
                "ContinuationRecordNo": "",
                "Name": "WP1",
            }
        ]
    )
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    result = runner.invoke(
        cli, ["parse", str(p), "-f", "EA", "-F", "csv", "-o", str(out)]
    )
    assert out.exists()
    content = out.read_text()
    assert "RecordType" in content
    assert "WP1" in content


def test_parse_parquet_stdout_warning(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    p.write_text(build_line("REC", "E", "A", "00001", "", "WP1") + "\n")

    df = pd.DataFrame(
        [
            {
                "RecordType": "REC",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00001",
                "ContinuationRecordNo": "",
                "Name": "WP1",
            }
        ]
    )
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    result = runner.invoke(cli, ["parse", str(p), "-f", "EA", "-F", "parquet"])
    assert "Parquet format stdout preview not supported" in result.output


def test_parse_export_geojson(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    out = tmp_path / "out.geojson"
    p.write_text(build_line("REC", "E", "A", "00001", "", "WP1") + "\n")

    df = pd.DataFrame(
        [
            {
                "RecordType": "REC",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00001",
                "ContinuationRecordNo": "",
                "Latitude": "N10000000",
                "Longitude": "E02000000",
                "Latitude_decimal": 10.0,
                "Longitude_decimal": 20.0,
                "Name": "WP1",
            }
        ]
    )
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )
    # Return a DataFrame that already includes the decimal columns
    monkeypatch.setattr("arinc424.cli.apply_decoders", lambda d: df)

    result = runner.invoke(
        cli, ["parse", str(p), "-f", "EA", "-F", "geojson", "-o", str(out)]
    )
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    assert data["features"][0]["geometry"]["coordinates"] == [20.0, 10.0]


def test_parse_geojson_stdout(tmp_path, runner, monkeypatch):
    p = tmp_path / "file.arinc"
    p.write_text(build_line("REC", "E", "A", "00001", "", "WP1") + "\n")

    df = pd.DataFrame(
        [
            {
                "RecordType": "REC",
                "Section": "E",
                "Subsection": "A",
                "FileRecordNo": "00001",
                "ContinuationRecordNo": "",
                "Latitude": 10.0,
                "Longitude": 20.0,
                "Name": "WP1",
            }
        ]
    )
    monkeypatch.setattr(
        parser, "parse_arinc_file", lambda f, record_filter: ("Waypoints", df)
    )

    result = runner.invoke(cli, ["parse", str(p), "-f", "EA", "-F", "geojson"])
    assert result.exit_code == 0
    assert "FeatureCollection" in result.output
