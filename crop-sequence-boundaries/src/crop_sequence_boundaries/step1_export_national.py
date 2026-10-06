"""Step 1: export the national CSB layer from the file geodatabase to GeoParquet.

Moved from the last cell of sandbox/sandbox.ipynb. Refuses to overwrite an
existing output; pass --force to replace it.
"""

import argparse
import json
from pathlib import Path

import duckdb

from crop_sequence_boundaries.config import (
    EXPECTED_EPSG,
    EXPECTED_FEATURES,
    EXPECTED_STATES,
    GDB_LAYER,
    GDB_PATH,
    NATIONAL_PARQUET_PATH,
    prepare_outputs,
)


def run(force: bool = False, output_path: Path = NATIONAL_PARQUET_PATH) -> None:
    if not GDB_PATH.exists():
        raise FileNotFoundError(f"Missing input: {GDB_PATH}. See in/SOURCES.md.")
    prepare_outputs([output_path], force)

    con = duckdb.connect()
    con.execute("INSTALL spatial")
    con.execute("LOAD spatial")

    rows_written = con.execute(
        f"""
        COPY (
            SELECT * FROM ST_Read($gdb, layer='{GDB_LAYER}')
        ) TO $output (FORMAT PARQUET, COMPRESSION ZSTD)
        """,
        {"gdb": str(GDB_PATH), "output": str(output_path)},
    ).fetchone()[0]

    # Check the output against the facts recorded in in/SOURCES.md.
    metadata_row = con.execute(
        """
        SELECT decode(value) FROM parquet_kv_metadata($output)
        WHERE decode(key) = 'geo'
        """,
        {"output": str(output_path)},
    ).fetchone()
    assert metadata_row is not None, "GeoParquet metadata is missing"
    geo_metadata = json.loads(metadata_row[0])
    epsg = geo_metadata["columns"]["Shape"]["crs"]["id"]["code"]
    assert epsg == EXPECTED_EPSG, f"CRS is EPSG:{epsg}, expected EPSG:{EXPECTED_EPSG}"

    rows_read, n_states = con.execute(
        "SELECT count(*), count(DISTINCT STATEFIPS) FROM read_parquet($output)",
        {"output": str(output_path)},
    ).fetchone()
    assert rows_read == rows_written, "Export row count mismatch"
    assert rows_read == EXPECTED_FEATURES, (
        f"Got {rows_read:,} features, expected {EXPECTED_FEATURES:,}"
    )
    assert n_states == EXPECTED_STATES, (
        f"Got {n_states} states, expected {EXPECTED_STATES}"
    )

    print(f"Wrote {rows_written:,} features to {output_path}")
    print(f"GeoParquet {geo_metadata['version']}; CRS: EPSG:{epsg}; {n_states} states")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=NATIONAL_PARQUET_PATH)
    parser.add_argument("--force", action="store_true", help="replace existing output")
    args = parser.parse_args()
    run(args.force, args.output)


if __name__ == "__main__":
    main()
