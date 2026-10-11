"""Step 1: convert the PSD snapshot CSV to typed Parquet.

Checks the zip against its SHA256, extracts the CSV to a temporary folder,
and writes every column unchanged but typed: codes stay zero-padded strings,
years and months become integers, values become numbers. Rows are sorted by
the key so the output is the same on every run.

Refuses to overwrite an existing output; pass --force to replace it.
"""

import argparse
import tempfile
import zipfile
from pathlib import Path

import duckdb

from fas_psd.config import (
    CSV_NAME,
    EXPECTED_ATTRIBUTES,
    EXPECTED_COMMODITIES,
    EXPECTED_COUNTRIES,
    EXPECTED_ROWS,
    EXPECTED_UNITS,
    MARKET_YEARS,
    OUT_DIR,
    PSD_PARQUET_PATH,
    ZIP_PATH,
    ZIP_SHA256,
    prepare_outputs,
    require_file,
)

# Codes are strings so leading zeros survive ("0577400", "020", "08").
COLUMN_TYPES = {
    "Commodity_Code": "VARCHAR",
    "Commodity_Description": "VARCHAR",
    "Country_Code": "VARCHAR",
    "Country_Name": "VARCHAR",
    "Market_Year": "SMALLINT",
    "Calendar_Year": "SMALLINT",
    "Month": "SMALLINT",
    "Attribute_ID": "VARCHAR",
    "Attribute_Description": "VARCHAR",
    "Unit_ID": "VARCHAR",
    "Unit_Description": "VARCHAR",
    "Value": "DOUBLE",
}
KEY = ("Commodity_Code", "Country_Code", "Market_Year", "Attribute_ID")


def run(force: bool = False, output_path: Path = PSD_PARQUET_PATH) -> None:
    require_file(ZIP_PATH, ZIP_SHA256)
    prepare_outputs([output_path], force)

    con = duckdb.connect()
    key = ", ".join(KEY)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUT_DIR) as tmp:
        with zipfile.ZipFile(ZIP_PATH) as archive:
            csv_path = Path(archive.extract(CSV_NAME, tmp))

        rows_written = con.execute(
            f"""
            COPY (
                SELECT * FROM read_csv($csv, header = true, columns = {COLUMN_TYPES})
                ORDER BY {key}
            ) TO $output (FORMAT PARQUET, COMPRESSION ZSTD)
            """,
            {"csv": str(csv_path), "output": str(output_path)},
        ).fetchone()[0]

    # Check the output against the facts recorded in in/SOURCES.md.
    con.execute(f"CREATE VIEW psd AS SELECT * FROM read_parquet('{output_path}')")
    rows, keys, null_values, commodities, countries, attributes, units, first_year, last_year = con.execute(
        f"""
        SELECT count(*), count(DISTINCT ({key})), count(*) FILTER (Value IS NULL),
               count(DISTINCT Commodity_Code), count(DISTINCT Country_Code),
               count(DISTINCT Attribute_ID), count(DISTINCT Unit_ID),
               min(Market_Year), max(Market_Year)
        FROM psd
        """
    ).fetchone()

    assert rows == rows_written == EXPECTED_ROWS, f"Got {rows:,} rows, expected {EXPECTED_ROWS:,}"
    assert keys == rows, f"Key {KEY} is not unique: {rows - keys:,} duplicate rows"
    assert null_values == 0, f"{null_values:,} missing values"
    assert commodities == EXPECTED_COMMODITIES, f"Got {commodities} commodities, expected {EXPECTED_COMMODITIES}"
    assert countries == EXPECTED_COUNTRIES, f"Got {countries} countries, expected {EXPECTED_COUNTRIES}"
    assert attributes == EXPECTED_ATTRIBUTES, f"Got {attributes} attributes, expected {EXPECTED_ATTRIBUTES}"
    assert units == EXPECTED_UNITS, f"Got {units} units, expected {EXPECTED_UNITS}"
    assert (first_year, last_year) == (MARKET_YEARS[0], MARKET_YEARS[-1]), (
        f"Market years {first_year}-{last_year}, expected {MARKET_YEARS[0]}-{MARKET_YEARS[-1]}"
    )

    print(f"Wrote {rows:,} rows to {output_path}")
    print(
        f"{commodities} commodities, {countries} countries, {attributes} attributes, "
        f"{units} units; market years {first_year}-{last_year}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=PSD_PARQUET_PATH)
    parser.add_argument("--force", action="store_true", help="replace existing output")
    args = parser.parse_args()
    run(args.force, args.output)


if __name__ == "__main__":
    main()
