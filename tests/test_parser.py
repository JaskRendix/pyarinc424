from pathlib import Path

import pandas as pd
import pytest

from arinc424 import parser


def build_line(record_type, section, subsection, fileno, contno, name):
    cont = contno if contno else "  "
    return (
        f"{record_type}{section}{subsection}"
        f"{fileno:0>5}"
        f"{cont}"
        f"{name.ljust(20)}"
    )


class DummyRegistry:
    def __init__(self):
        self.routing = {
            "E": {"A": "Waypoints", "R": "Airways"},
            "P": {"A": "Airports", "L": "ProcedureLegs"},
            "D": {" ": "Navaids"},
            "U": {"F": "Airspace", "B": "AirspaceBoundaries"},
            "C": {"R": "CompanyRoutes", "L": "CompanyRouteLegs"},
            "H": {"P": "HeliportProcedures"},
            "G": {"M": "GridMora", "A": "Avionics"},
            "R": {"C": "Communications", "E": "CommunicationsExtended"},
        }

        base_schema = {
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

        self.schemas = {
            name: base_schema
            for name in [
                "Waypoints",
                "Airports",
                "Navaids",
                "Airways",
                "Airspace",
                "AirspaceBoundaries",
                "CompanyRoutes",
                "CompanyRouteLegs",
                "ProcedureLegs",
                "HeliportProcedures",
                "GridMora",
                "Communications",
                "CommunicationsExtended",
                "Avionics",
            ]
        }
        self.continuation_rules = {"Waypoints": ["Name"]}


@pytest.fixture(autouse=True)
def patch_registry(monkeypatch):
    dummy = DummyRegistry()
    monkeypatch.setattr(parser, "_REGISTRY", dummy)
    return dummy


def test_resolve_schema_valid():
    schema_name, schema = parser._resolve_schema("EA")
    assert schema_name == "Waypoints"
    assert "names" in schema
    assert "colspecs" in schema


def test_resolve_schema_invalid_filter_short():
    with pytest.raises(ValueError):
        parser._resolve_schema("E")


def test_resolve_schema_no_routing():
    with pytest.raises(KeyError):
        parser._resolve_schema("ZZ")


def test_parse_arinc_file_no_matches(tmp_path: Path):
    p = tmp_path / "test.arinc"
    p.write_text("HDR SOME HEADER\nEAxxx\n", encoding="utf-8")
    schema_name, df = parser.parse_arinc_file(p, record_filter="PA")
    assert schema_name == "Airports"
    assert df.empty


def test_parse_arinc_file_with_continuations(tmp_path: Path):
    p = tmp_path / "test_cont.arinc"
    base_line = build_line("REC", "E", "A", "00001", "", "BASE_NAME")
    cont_line = build_line("REC", "E", "A", "00001", "01", "CONT_NAME")
    p.write_text(base_line + "\n" + cont_line + "\n", encoding="utf-8")
    schema_name, df = parser.parse_arinc_file(
        p, record_filter="EA", merge_continuations=True
    )
    assert schema_name == "Waypoints"
    assert len(df) == 1
    assert df.iloc[0]["FileRecordNo"] == "00001"
    assert df.iloc[0]["Name"] == "BASE_NAME CONT_NAME"


def test_parse_arinc_file_without_continuations_flag(tmp_path: Path):
    p = tmp_path / "test_nocont.arinc"
    base_line = build_line("REC", "E", "A", "00001", "", "BASE_NAME")
    cont_line = build_line("REC", "E", "A", "00001", "01", "CONT_NAME")
    p.write_text(base_line + "\n" + cont_line + "\n", encoding="utf-8")
    schema_name, df = parser.parse_arinc_file(
        p, record_filter="EA", merge_continuations=False
    )
    assert schema_name == "Waypoints"
    assert len(df) == 2


def test_stream_arinc_file(tmp_path: Path):
    p = tmp_path / "test_stream.arinc"
    p.write_text(
        "HDR HEADER LINE\n" "XXXEAFOO\n" "YYYPAFOO\n" "ZZZEA BAR\n",
        encoding="utf-8",
    )
    results = list(parser.stream_arinc_file(p, record_filter="EA"))
    assert len(results) == 2
    assert results[0][3:5] == "EA"
    assert results[1][3:5] == "EA"


def test_parse_header_details(tmp_path: Path):
    p = tmp_path / "test_header.arinc"
    hdr = "HDRSOMEHDR 12342025\n"
    h1 = "H1PROVIDER_NAME    V0001\n"
    h2 = "H2COVERAGE   REST\n"
    p.write_text(hdr + h1 + h2, encoding="utf-8")
    info = parser.parse_header_details(p)
    assert info["cycle_date"] == "1234"
    assert info["effective_date"] == "2025"
    assert info["provider"] == "PROVIDER_NAME"
    assert info["version"] == "V0001"
    assert info["coverage"].startswith("COVERAGE")


def test_read_header_valid(tmp_path: Path):
    p = tmp_path / "test_read_header.arinc"
    hdr = "HDRSOMEHDR 56782030\n"
    p.write_text(hdr, encoding="utf-8")
    info = parser.read_header(p)
    assert info["cycle_date"] == "5678"
    assert info["effective_date"] == "2030"


def test_read_header_missing_file(tmp_path: Path):
    p = tmp_path / "missing.arinc"
    with pytest.raises(FileNotFoundError):
        parser.read_header(p)


def test_read_waypoints(tmp_path: Path):
    p = tmp_path / "wp.arinc"
    line = build_line("REC", "E", "A", "00001", "", "WP1")
    p.write_text(line + "\n", encoding="utf-8")
    df = parser.read_waypoints(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "WP1"


def test_read_airports(tmp_path: Path):
    p = tmp_path / "ap.arinc"
    line = build_line("REC", "P", "A", "00002", "", "APT")
    p.write_text(line + "\n", encoding="utf-8")
    df = parser.read_airports(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "APT"


def test_read_navaids(tmp_path: Path):
    p = tmp_path / "nav.arinc"
    sp = chr(32)
    line = "RECD" + sp + "00003" + sp * 2 + "NAV".ljust(20)
    p.write_text(line + "\n", encoding="utf-8")

    df = parser.read_navaids(p)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["Name"].strip() == "NAV"


def test_read_airways(tmp_path: Path):
    p = tmp_path / "airways.arinc"
    p.write_text(
        build_line("REC", "E", "R", "00004", "", "J1") + "\n", encoding="utf-8"
    )
    df = parser.read_airways(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "J1"


def test_read_airspace(tmp_path: Path):
    p = tmp_path / "airspace.arinc"
    p.write_text(
        build_line("REC", "U", "F", "00005", "", "RESTRICTED") + "\n", encoding="utf-8"
    )
    df = parser.read_airspace(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "RESTRICTED"


def test_read_airspace_boundaries(tmp_path: Path):
    p = tmp_path / "boundaries.arinc"
    p.write_text(
        build_line("REC", "U", "B", "00006", "", "BOUND") + "\n", encoding="utf-8"
    )
    df = parser.read_airspace_boundaries(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "BOUND"


def test_read_company_routes(tmp_path: Path):
    p = tmp_path / "croutes.arinc"
    p.write_text(
        build_line("REC", "C", "R", "00007", "", "CROUTE1") + "\n", encoding="utf-8"
    )
    df = parser.read_company_routes(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "CROUTE1"


def test_read_company_route_legs(tmp_path: Path):
    p = tmp_path / "clegs.arinc"
    p.write_text(
        build_line("REC", "C", "L", "00008", "", "LEG1") + "\n", encoding="utf-8"
    )
    df = parser.read_company_route_legs(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "LEG1"


def test_read_procedure_legs(tmp_path: Path):
    p = tmp_path / "plegs.arinc"
    p.write_text(
        build_line("REC", "P", "L", "00009", "", "PROCLEG") + "\n", encoding="utf-8"
    )
    df = parser.read_procedure_legs(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "PROCLEG"


def test_read_grid_mora(tmp_path: Path):
    p = tmp_path / "mora.arinc"
    p.write_text(
        build_line("REC", "G", "M", "00010", "", "MORA") + "\n", encoding="utf-8"
    )
    df = parser.read_grid_mora(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "MORA"


def test_read_communications(tmp_path: Path):
    p = tmp_path / "comm.arinc"
    p.write_text(
        build_line("REC", "R", "C", "00011", "", "TWR") + "\n", encoding="utf-8"
    )
    df = parser.read_communications(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "TWR"


def test_read_avionics(tmp_path: Path):
    p = tmp_path / "avionics.arinc"
    p.write_text(
        build_line("REC", "G", "A", "00012", "", "AVIONICS") + "\n", encoding="utf-8"
    )
    df = parser.read_avionics(p)
    assert len(df) == 1
    assert df.iloc[0]["Name"] == "AVIONICS"
