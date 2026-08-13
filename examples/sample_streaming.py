from pathlib import Path

import click

from arinc424 import parser


@click.command()
@click.argument("infile", type=click.Path(exists=True, path_type=Path))
@click.option("--filter", "-f", required=True)
def main(infile: Path, filter: str) -> None:
    for line in parser.stream_arinc_file(infile, filter):
        print(line.rstrip())


if __name__ == "__main__":
    main()
