import json
from collections.abc import Callable, Iterable
from dataclasses import asdict
from pathlib import Path

import click
import pandas as pd

from .parser import parse_arinc_file, parse_header_details
from .schemas.loader import load_all_icd_schemas
from .utils import apply_decoders
from .validation import validate_dataframe_schema

_REGISTRY = load_all_icd_schemas()


@click.group()
@click.version_option()
def cli():
    """ARINC 424 Parser CLI Tool powered by unified ICD schema registry."""
    pass


def _resolve_converter(
    schema_name: str,
) -> Callable[[pd.DataFrame], Iterable[object]] | None:
    """Resolve a model converter dynamically from the registry."""
    return _REGISTRY.model_converters.get(schema_name)


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
    help="Output path for JSON export.",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=None,
    help="Limit number of records processed/output.",
)
def parse(file: Path, filter: str, model: bool, output: Path | None, limit: int | None):
    """Parse an ARINC 424 file using unified ICD schema routing."""
    click.echo(f"Parsing records '{filter}' from {file}...")

    try:
        schema_name, df = parse_arinc_file(file, record_filter=filter)
    except Exception as exc:
        raise click.ClickException(str(exc))

    if limit is not None:
        df = df.head(limit)

    df = apply_decoders(df)

    schema = _REGISTRY.schemas.get(schema_name, {})
    errors = validate_dataframe_schema(df, schema)

    if errors:
        click.echo(f"Validation found {len(errors)} issues:")
        for err in errors:
            click.echo(f"- {err}")

    if model:
        converter = _resolve_converter(schema_name)

        if converter is None:
            click.echo(
                f"No typed model converter registered for schema '{schema_name}'. "
                f"Falling back to raw dictionaries."
            )
            records = df.to_dict(orient="records")
        else:
            records = [asdict(r) for r in converter(df)]
            click.echo(f"Converted {len(records)} records using model '{schema_name}'.")

        if output:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            click.echo(f"Saved results to {output}")
        else:
            click.echo(json.dumps(records[:5], indent=2))

    else:
        click.echo(f"Parsed {len(df)} records.")
        if output:
            df.to_json(output, orient="records", indent=2)
            click.echo(f"Saved results to {output}")
        else:
            click.echo(df.head().to_string())


@cli.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def header(file: Path):
    """Extract metadata and cycle info from file headers."""
    info = parse_header_details(file)
    click.echo(json.dumps(info, indent=2))


@cli.command(name="schemas")
def list_schemas():
    """List all loaded ARINC 424 schemas and routing rules."""
    click.echo("--- Routing Table (Section/Subsection → Schema) ---")
    click.echo(json.dumps(_REGISTRY.routing, indent=2))

    click.echo("\n--- Available Schema Definitions ---")
    click.echo(json.dumps(list(_REGISTRY.schemas.keys()), indent=2))

    click.echo("\n--- Registered Model Converters ---")
    click.echo(json.dumps(list(_REGISTRY.model_converters.keys()), indent=2))


if __name__ == "__main__":
    cli()
