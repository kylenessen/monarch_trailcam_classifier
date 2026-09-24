"""Create a working configurations.json without changing archived annotations."""

import argparse
import json
from pathlib import Path
import re


def prepare_configuration(data, rows=None, columns=None):
    if not isinstance(data, dict):
        raise ValueError("Annotations must be a JSON object.")
    wrapped = "classifications" in data
    if wrapped:
        if rows is not None or columns is not None:
            raise ValueError("Use the grid dimensions already stored in this file.")
        rows, columns = data.get("rows"), data.get("columns")
        records = data["classifications"]
    else:
        records = data
    if any(type(n) is not int or n <= 0 for n in (rows, columns)):
        raise ValueError("Legacy files require positive integer --rows and --columns.")
    if not isinstance(records, dict):
        raise ValueError("Classifications must be an object keyed by image filename.")
    # Copy before adding compatibility fields. Preserve all original annotation fields.
    result = json.loads(json.dumps(data if wrapped else {
        "rows": rows, "columns": columns, "classifications": records
    }))
    for filename, record in result["classifications"].items():
        if not isinstance(record, dict) or not isinstance(record.get("cells", {}), dict):
            raise ValueError(f"Invalid image record for {filename}.")
        for key, cell in record.get("cells", {}).items():
            match = re.fullmatch(r"cell_(\d+)_(\d+)", key)
            if not match or int(match[1]) >= rows or int(match[2]) >= columns:
                raise ValueError(f"Cell {key} in {filename} falls outside the supplied grid.")
            if not isinstance(cell, dict):
                raise ValueError(f"Invalid cell {key} in {filename}.")
            if "directSun" not in cell and "sunlight" in cell:
                if type(cell["sunlight"]) is not bool:
                    raise ValueError(f"Invalid sunlight flag in {filename}, {key}.")
                cell["directSun"] = cell["sunlight"]
    return result


def prepare_file(source, destination, rows=None, columns=None):
    configuration = prepare_configuration(json.loads(source.read_text()), rows, columns)
    # Exclusive creation prevents overwriting either the archive or earlier work.
    with destination.open("x") as stream:
        json.dump(configuration, stream, indent=2)
        stream.write("\n")
    return len(configuration["classifications"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, help="New configurations.json beside the deployment images")
    parser.add_argument("--rows", type=int)
    parser.add_argument("--columns", type=int)
    args = parser.parse_args()
    try:
        count = prepare_file(args.source, args.destination, args.rows, args.columns)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Cannot prepare deployment. {exc}\n")
    print(f"Prepared {count} image records in {args.destination}")


if __name__ == "__main__":
    main()
