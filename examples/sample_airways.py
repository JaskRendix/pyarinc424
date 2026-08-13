from pathlib import Path

import click

from arinc424 import parser


@click.command()
@click.argument("infile", type=click.Path(exists=True, path_type=Path))
def main(infile: Path) -> None:
    """Read an ARINC 424 file and extract airway records."""
    df = parser.read_airways(infile)
    print(df.head())


if __name__ == "__main__":
    main()
