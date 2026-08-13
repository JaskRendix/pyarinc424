from json import dumps, loads
from pathlib import Path
from typing import Any

import click

from arinc424 import parser


@click.command()
@click.argument("infile", type=click.Path(exists=True, path_type=Path))
@click.argument("outfile", type=click.Path(exists=False, path_type=Path))
def main(infile: Path, outfile: Path) -> None:
    """Read an ARINC 424 file, extract waypoint records, and write JSON output."""
    df = parser.read_waypoints(infile)

    df.to_json(outfile, orient="records")

    if len(df) > 5:
        row_json: str = df.iloc[5].to_json()
        parsed: dict[str, Any] = loads(row_json)
        print(dumps(parsed, indent=4))


if __name__ == "__main__":
    main()
