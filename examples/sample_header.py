from pathlib import Path

import click

from arinc424 import parser


@click.command()
@click.argument("infile", type=click.Path(exists=True, path_type=Path))
def main(infile: Path) -> None:
    """Read an ARINC 424 file and print header metadata."""
    info = parser.read_header(infile)
    print(info)


if __name__ == "__main__":
    main()
