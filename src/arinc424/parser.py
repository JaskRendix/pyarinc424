import io
import mmap
from pathlib import Path

import pandas as pd

from .schemas.loader import load_all_icd_schemas

_REGISTRY = load_all_icd_schemas()


def _resolve_schema(record_filter: str) -> tuple[str, dict]:
    if not record_filter or len(record_filter) < 2:
        raise ValueError(f"Invalid record_filter: {record_filter!r}")

    section = record_filter[0]
    subsection = record_filter[1]

    schema_name = _REGISTRY.routing.get(section, {}).get(subsection)
    if not schema_name:
        raise KeyError(f"No schema routing for {section}/{subsection}")

    schema = _REGISTRY.schemas.get(schema_name)
    if not schema:
        raise KeyError(f"Schema '{schema_name}' not found in registry")

    return schema_name, schema


def parse_arinc_file(
    file_path: str | Path,
    record_filter: str,
    merge_continuations: bool = True,
) -> tuple[str, pd.DataFrame]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    schema_name, schema = _resolve_schema(record_filter)

    target_section = record_filter[0]
    target_subsection = record_filter[1]

    lines: list[str] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            normalized = line.replace("\xa0", " ").rstrip("\r\n")
            if len(normalized) >= 5:
                sec = normalized[3:4]
                subsec = normalized[4:5]
                if sec == target_section and subsec == target_subsection:
                    lines.append(normalized + "\n")

    if not lines:
        return schema_name, pd.DataFrame(columns=schema["names"])

    df_all = pd.read_fwf(
        io.StringIO("".join(lines)),
        index_col=False,
        colspecs=schema["colspecs"],
        header=None,
        names=schema["names"],
        dtype=str,
    )

    # Coerce columns to string type and clean whitespace. fillna("") must run
    # BEFORE astype(str): on pandas >=3.0's default string dtype, astype(str)
    # keeps NaN as an actual missing value (it only *displays* as "nan"), so a
    # later `.replace(["nan", ...], "")` never matches it.
    for col in df_all.columns:
        df_all[col] = df_all[col].fillna("").astype(str).str.strip()
        df_all[col] = df_all[col].replace(["nan", "None", "<NA>"], "")

    if not merge_continuations:
        return schema_name, df_all

    cont_fields = _REGISTRY.continuation_rules.get(schema_name)
    if not cont_fields or "ContinuationRecordNo" not in df_all.columns:
        return schema_name, df_all

    base_mask = df_all["ContinuationRecordNo"].eq("")
    df_base = df_all[base_mask].copy()
    df_cont = df_all[~base_mask].copy()

    if df_cont.empty or "FileRecordNo" not in df_base.columns:
        return schema_name, df_base

    merged = df_base.copy()

    for _, row in df_cont.iterrows():
        file_no = row.get("FileRecordNo")
        if not file_no:
            continue

        base_idx = merged.index[merged["FileRecordNo"] == file_no]
        if base_idx.empty:
            continue

        for field in cont_fields:
            if field not in merged.columns or field not in row.index:
                continue

            val = str(row.get(field, "")).strip()
            if not val:
                continue

            curr = str(merged.loc[base_idx, field].values[0]).strip()
            if curr:
                merged.loc[base_idx, field] = (curr + " " + val).strip()
            else:
                merged.loc[base_idx, field] = val

    return schema_name, merged


def stream_arinc_file(file_path: str | Path, record_filter: str):
    path = Path(file_path)
    target_section = record_filter[0]
    target_subsection = record_filter[1]

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for line_bytes in iter(mm.readline, b""):
                line_str = line_bytes.decode("ascii", errors="ignore").replace(
                    "\xa0", " "
                )
                if len(line_str) >= 5:
                    sec = line_str[3:4]
                    subsec = line_str[4:5]
                    if sec == target_section and subsec == target_subsection:
                        yield line_str


def parse_header_details(file_path: str | Path) -> dict:
    header_info: dict[str, str | None] = {}
    path = Path(file_path)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.replace("\xa0", " ").strip()
            if line_str.startswith("HDR"):
                header_info["raw_header"] = line_str
                header_info["cycle_date"] = (
                    line_str[11:15] if len(line_str) >= 15 else None
                )
                header_info["effective_date"] = (
                    line_str[-4:] if len(line_str) >= 4 else None
                )
            elif line_str.startswith("H1"):
                header_info["provider"] = (
                    line_str[2:18].strip()
                    if len(line_str) >= 18
                    else line_str[2:].strip()
                )
                header_info["version"] = (
                    line_str[18:].strip() if len(line_str) >= 18 else None
                )
            elif line_str.startswith("H2"):
                header_info["coverage"] = line_str[2:].strip()
                break
    return header_info


def read_header(file: str | Path) -> dict[str, str | None]:
    path = Path(file)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    header_info: dict[str, str | None] = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.replace("\xa0", " ").strip()
            if line_str.startswith("HDR") or "HDR" in line_str[:5]:
                header_info["raw_header"] = line_str
                header_info["cycle_date"] = (
                    line_str[11:15] if len(line_str) >= 15 else None
                )
                header_info["effective_date"] = (
                    line_str[-4:] if len(line_str) >= 4 else None
                )
                break
    return header_info


def read_waypoints(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="EA")
    return df


def read_airports(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="PA")
    return df


def read_navaids(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="D ")
    return df


def read_airways(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="ER")
    return df


def read_airspace(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="UF")
    return df


def read_airspace_boundaries(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="UB")
    return df


def read_company_routes(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="CR")
    return df


def read_company_route_legs(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="CL")
    return df


def read_procedure_legs(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="PL")
    return df


def read_heliport_procedures(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="HP")
    return df


def read_grid_mora(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="GM")
    return df


def read_communications(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="RC")
    return df


def read_communications_extended(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="RE")
    return df


def read_avionics(file: str | Path) -> pd.DataFrame:
    _, df = parse_arinc_file(file, record_filter="GA")
    return df
