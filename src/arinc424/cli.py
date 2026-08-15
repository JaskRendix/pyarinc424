import json
from collections.abc import Callable, Iterable
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

import click
import pandas as pd

from .parser import parse_arinc_file, parse_header_details
from .schemas.loader import load_all_icd_schemas
from .utils import apply_decoders
from .validation import validate_dataframe_schema


@lru_cache(maxsize=1)
def get_registry():
    """Lazy load and cache schema registry on first use."""
    return load_all_icd_schemas()


def _resolve_converter(
    schema_name: str,
) -> Callable[[pd.DataFrame], Iterable[object]] | None:
    """Resolve a model converter dynamically from the registry."""
    return get_registry().model_converters.get(schema_name)


def _json_default(obj: object) -> object:
    """Fallback JSON serializer for dates, decimals, sets, and custom objects."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    return str(obj)


@click.group()
@click.version_option()
def cli():
    """ARINC 424 Parser CLI Tool powered by unified ICD schema registry."""
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--filter",
    "-f",
    required=True,
    help="Record filter code (e.g., AE, UB, CL, PA, EA). Must match ARINC section/subsection.",
)
@click.option(
    "--model",
    "-m",
    is_flag=True,
    help="Convert rows into typed dataclass objects before output.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output path for export.",
)
@click.option(
    "--format",
    "-F",
    "out_format",
    type=click.Choice(["json", "csv", "parquet"], case_sensitive=False),
    default="json",
    help="Output file format (default: json).",
)
@click.option(
    "--strict",
    "-s",
    is_flag=True,
    help="Aborts parsing if schema validation errors are detected.",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit number of records processed/output.",
)
def parse(
    file: Path,
    filter: str,
    model: bool,
    output: Path | None,
    out_format: str,
    strict: bool,
    limit: int | None,
):
    """Parse an ARINC 424 file using unified ICD schema routing."""
    click.echo(f"Parsing records '{filter}' from {file}...", err=True)

    try:
        schema_name, df = parse_arinc_file(file, record_filter=filter)
    except Exception as exc:
        raise click.ClickException(str(exc))

    if limit is not None:
        df = df.head(limit)

    df = apply_decoders(df)

    registry = get_registry()
    schema = registry.schemas.get(schema_name, {})
    errors = validate_dataframe_schema(df, schema)

    if errors:
        click.echo(f"Validation found {len(errors)} issues:", err=True)
        for err in errors:
            click.echo(f"- {err}", err=True)
        if strict:
            raise click.ClickException(
                f"Schema validation failed with {len(errors)} issues in strict mode."
            )

    out_format = out_format.lower()

    if model:
        converter = _resolve_converter(schema_name)

        if converter is None:
            click.echo(
                f"No typed model converter registered for schema '{schema_name}'. "
                f"Falling back to raw dictionaries.",
                err=True,
            )
            records = df.to_dict(orient="records")
        else:
            records = [asdict(r) for r in converter(df)]
            click.echo(
                f"Converted {len(records)} records using model '{schema_name}'.",
                err=True,
            )

        export_df = pd.DataFrame(records)

        if output:
            if out_format == "csv":
                export_df.to_csv(output, index=False)
            elif out_format == "parquet":
                export_df.to_parquet(output, index=False)
            else:
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2, default=_json_default)
            click.echo(f"Saved results to {output}", err=True)
        else:
            if out_format == "csv":
                click.echo(export_df.head().to_csv(index=False))
            elif out_format == "parquet":
                click.echo(
                    "Parquet format stdout preview not supported. Specify --output.",
                    err=True,
                )
            else:
                click.echo(json.dumps(records[:5], indent=2, default=_json_default))

    else:
        click.echo(f"Parsed {len(df)} records.", err=True)
        if output:
            if out_format == "csv":
                df.to_csv(output, index=False)
            elif out_format == "parquet":
                df.to_parquet(output, index=False)
            else:
                df.to_json(output, orient="records", indent=2)
            click.echo(f"Saved results to {output}", err=True)
        else:
            if out_format == "csv":
                click.echo(df.head().to_csv(index=False))
            elif out_format == "parquet":
                click.echo(
                    "Parquet format stdout preview not supported. Specify --output.",
                    err=True,
                )
            else:
                click.echo(df.head().to_string())


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def header(file: Path):
    """Extract metadata and cycle info from file headers."""
    info = parse_header_details(file)
    click.echo(json.dumps(info, indent=2, default=_json_default))


@cli.command(name="schemas")
def list_schemas():
    """List all loaded ARINC 424 schemas and routing rules."""
    registry = get_registry()
    click.echo("--- Routing Table (Section/Subsection → Schema) ---")
    click.echo(json.dumps(registry.routing, indent=2))

    click.echo("\n--- Available Schema Definitions ---")
    click.echo(json.dumps(list(registry.schemas.keys()), indent=2))

    click.echo("\n--- Registered Model Converters ---")
    click.echo(json.dumps(list(registry.model_converters.keys()), indent=2))


if __name__ == "__main__":
    cli()
