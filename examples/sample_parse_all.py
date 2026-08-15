from pathlib import Path

from arinc424 import parser


def main():
    sample_file = Path("path/to/arinc424_sample.txt")

    if not sample_file.exists():
        print(f"Sample file not found at {sample_file}. Please update the path.")
        return

    print("Parsing entire ARINC 424 file in a single pass...")
    datasets = parser.parse_all(sample_file, merge_continuations=True)

    print(f"\nSuccessfully decoded {len(datasets)} dataset categories:\n")

    for schema_name, df in datasets.items():
        print(f"--- {schema_name} ({len(df)} records) ---")
        if not df.empty:
            print(df.head(2))
        print()


if __name__ == "__main__":
    main()
