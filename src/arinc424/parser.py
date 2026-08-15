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
    target_subsection = record_filter[1] if len(record_filter) > 1 else None

    lines: list[str] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            normalized = line.replace("\xa0", " ").rstrip("\r\n")
            if len(normalized) >= 5:
                sec = normalized[3:4]
                subsec = normalized[4:5]
                sec_match = sec == target_section
                subsec_match = target_subsection is None or subsec == target_subsection
                if sec_match and subsec_match:
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

    # Efficient O(N) vectorized continuation aggregation using pandas groupby
    existing_cont_fields = [f for f in cont_fields if f in df_cont.columns]

    if not existing_cont_fields:
        return schema_name, df_base

    cont_grouped = (
        df_cont.groupby("FileRecordNo")[existing_cont_fields]
        .agg(lambda cols: " ".join(v for v in cols if v.strip()))
        .reset_index()
    )

    merged = df_base.merge(
        cont_grouped, on="FileRecordNo", how="left", suffixes=("", "_cont")
    )

    for field in existing_cont_fields:
        cont_col = f"{field}_cont"
        if cont_col in merged.columns:
            base_val = merged[field].fillna("").astype(str).str.strip()
            val_cont = merged[cont_col].fillna("").astype(str).str.strip()
            merged[field] = (base_val + " " + val_cont).str.strip()
            merged.drop(columns=[cont_col], inplace=True)

    return schema_name, merged


def parse_all(
    file_path: str | Path,
    merge_continuations: bool = True,
) -> dict[str, pd.DataFrame]:
    """Read an entire ARINC 424 file in a single pass, route each line by its

    section/subsection code, and return a dictionary of DataFrames mapped by schema name.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Handle empty files gracefully before mmaping
    if path.stat().st_size == 0:
        return {}

    # Bucket lines by (section, subsection) or schema name
    schema_lines: dict[str, list[str]] = {}

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for line_bytes in iter(mm.readline, b""):
                line_str = (
                    line_bytes.decode("ascii", errors="ignore")
                    .replace("\xa0", " ")
                    .rstrip("\r\n")
                )
                if len(line_str) >= 5:
                    sec = line_str[3:4]
                    subsec = line_str[4:5]

                    # Lookup schema name from registry routing
                    schema_name = _REGISTRY.routing.get(sec, {}).get(subsec)
                    if not schema_name:
                        continue

                    schema_lines.setdefault(schema_name, []).append(line_str + "\n")

    datasets: dict[str, pd.DataFrame] = {}

    for schema_name, lines in schema_lines.items():
        schema = _REGISTRY.schemas.get(schema_name)
        if not schema or not lines:
            continue

        df_all = pd.read_fwf(
            io.StringIO("".join(lines)),
            index_col=False,
            colspecs=schema["colspecs"],
            header=None,
            names=schema["names"],
            dtype=str,
        )

        # Clean string whitespace and sentinel values
        for col in df_all.columns:
            df_all[col] = df_all[col].fillna("").astype(str).str.strip()
            df_all[col] = df_all[col].replace(["nan", "None", "<NA>"], "")

        if not merge_continuations:
            datasets[schema_name] = df_all
            continue

        cont_fields = _REGISTRY.continuation_rules.get(schema_name)
        if not cont_fields or "ContinuationRecordNo" not in df_all.columns:
            datasets[schema_name] = df_all
            continue

        base_mask = df_all["ContinuationRecordNo"].eq("")
        df_base = df_all[base_mask].copy()
        df_cont = df_all[~base_mask].copy()

        if df_cont.empty or "FileRecordNo" not in df_base.columns:
            datasets[schema_name] = df_base
            continue

        existing_cont_fields = [f for f in cont_fields if f in df_cont.columns]
        if not existing_cont_fields:
            datasets[schema_name] = df_base
            continue

        cont_grouped = (
            df_cont.groupby("FileRecordNo")[existing_cont_fields]
            .agg(lambda cols: " ".join(v for v in cols if v.strip()))
            .reset_index()
        )

        merged = df_base.merge(
            cont_grouped, on="FileRecordNo", how="left", suffixes=("", "_cont")
        )

        for field in existing_cont_fields:
            cont_col = f"{field}_cont"
            if cont_col in merged.columns:
                base_val = merged[field].fillna("").astype(str).str.strip()
                val_cont = merged[cont_col].fillna("").astype(str).str.strip()
                merged[field] = (base_val + " " + val_cont).str.strip()
                merged.drop(columns=[cont_col], inplace=True)

        datasets[schema_name] = merged

    return datasets


def stream_arinc_file(
    file_path: str | Path,
    record_filter: str,
    as_dict: bool = False,
    batch_size: int | None = None,
):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    schema_name, schema = _resolve_schema(record_filter) if as_dict else (None, None)
    target_section = record_filter[0]
    target_subsection = record_filter[1] if len(record_filter) > 1 else None

    batch: list[dict | str] = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for line_bytes in iter(mm.readline, b""):
                line_str = line_bytes.decode("ascii", errors="ignore").replace(
                    "\xa0", " "
                )
                if len(line_str) >= 5:
                    sec = line_str[3:4]
                    subsec = line_str[4:5]
                    sec_match = sec == target_section
                    subsec_match = (
                        target_subsection is None or subsec == target_subsection
                    )
                    if sec_match and subsec_match:
                        if as_dict and schema:
                            record = {}
                            for name, (start, end) in zip(
                                schema["names"], schema["colspecs"]
                            ):
                                record[name] = line_str[start:end].strip()
                            item = record
                        else:
                            item = line_str

                        if batch_size:
                            batch.append(item)
                            if len(batch) >= batch_size:
                                yield batch
                                batch = []
                        else:

                            yield item

    if batch_size and batch:
        yield batch


def parse_header_details(file_path: str | Path) -> dict[str, str | None]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    header_info: dict[str, str | None] = {}

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
    """Extract metadata and cycle info from file headers."""
    return parse_header_details(file)


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
