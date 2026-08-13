from pathlib import Path

import click

from arinc424 import parser


@click.command()
@click.argument("infile", type=click.Path(exists=True, path_type=Path))
@click.option("--filter", "-f", required=True)
def main(infile: Path, filter: str) -> None:
    schema_name, df = parser.parse_arinc_file(
        infile,
        record_filter=filter,
        merge_continuations=True,
    )

    print(schema_name)
    print(df.head())


if __name__ == "__main__":
    main()
