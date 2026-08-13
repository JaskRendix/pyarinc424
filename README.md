# ARINC 424‑20 Parser

A modern, schema‑driven ARINC 424 navigation data parser supporting full file decoding, validation, and structured DataFrame output.

This project is a modernization and expansion of [varnav/pyarinc424](https://github.com/varnav/pyarinc424), adding ARINC 424‑18/19/20 schema support, full file parsing, DataFrame output, validation, and an extended CLI.

## Installation

```bash
pip install -e .
pip install -e .[test]
```

## Features

- Record parsing for ARINC 424 fixed‑width data files into pandas DataFrames and typed objects.
- Schema definitions for ARINC 424‑18, 424‑19, and 424‑20.
- Coordinate and field decoding for ARINC formats.
- Header parsing for AIRAC cycle information and file metadata.
- CLI interface for parsing, validation, schema inspection, and JSON export.

## Usage

### Python API

```python
from arinc424 import pyarinc424 as a

df = a.read_waypoints("path/to/arinc424.txt")
header = a.read_header("path/to/arinc424.txt")
```

### CLI

```bash
arinc424 --help
arinc424 parse path/to/arinc424.txt --output out.json
arinc424 parse path/to/arinc424.txt --model
arinc424 schemas
arinc424 header path/to/arinc424.txt
```

## Supported Record Types

- Waypoints  
- Airways  
- Airspace  
- Airspace boundaries  
- Airports and airport infrastructure  
- Communications  
- Extended communications  
- Navigation aids  
- Company routes  
- Company route legs  
- Procedures  
- Procedure legs  
- Heliport procedures  
- Grid MORA  
- Avionics and general aviation

## Schema System

Schemas are defined in YAML files under `src/arinc424/schemas/`.  
Routing rules are defined in `routing.json`.  
Continuation rules are defined in `continuations.json`.

## Validation

`validate_dataframe_schema(df, schema)` checks required fields, field types, and structural constraints defined in the YAML schema.

## Examples

Example scripts are available in `examples/`.

```bash
python examples/sample_loadfile.py
```

## Development

```bash
pytest -q
```
