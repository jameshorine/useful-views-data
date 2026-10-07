"""Step 2: list every attribute PSD reports for each commodity, with its unit.

Writes commodity_attribute.parquet to the release folder: one row per
(commodity, attribute) pair found in psd_alldata, with the descriptions and
unit exactly as PSD publishes them. It answers "what does PSD report for this
commodity, and in what unit?" without scanning two million rows.

Refuses to overwrite an existing output; pass --force to replace it.
"""

import argparse

import duckdb

from fas_psd.config import (
    COMMODITY_ATTRIBUTE_PATH,
    EXPECTED_COMMODITY_ATTRIBUTES,
    PSD_PARQUET_PATH,
    prepare_outputs,
    require_outputs,
)

COMMODITY_ATTRIBUTE_SQL = """
SELECT DISTINCT
    Commodity_Code,
    Commodity_Description,
    Attribute_ID,
    Attribute_Description,
    Unit_Description
FROM psd
ORDER BY Attribute_ID, Commodity_Code
"""


def one(con: duckdb.DuckDBPyConnection, sql: str):
    return con.execute(sql).fetchone()


def run(force: bool = False) -> None:
    require_outputs([PSD_PARQUET_PATH], before="step 1")
    prepare_outputs([COMMODITY_ATTRIBUTE_PATH], force)

    con = duckdb.connect()
    con.execute(f"CREATE VIEW psd AS SELECT * FROM read_parquet('{PSD_PARQUET_PATH}')")
    con.execute(
        f"COPY ({COMMODITY_ATTRIBUTE_SQL}) TO '{COMMODITY_ATTRIBUTE_PATH}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    con.execute(f"CREATE VIEW commodity_attribute AS SELECT * FROM read_parquet('{COMMODITY_ATTRIBUTE_PATH}')")
    print(f"Wrote {COMMODITY_ATTRIBUTE_PATH}")

    # Checks: one row per pair (so one description and unit each), and every
    # row of psd_alldata finds its pair.
    rows, keys = one(con, "SELECT count(*), count(DISTINCT (Commodity_Code, Attribute_ID)) FROM commodity_attribute")
    assert rows == keys, f"{rows:,} rows but {keys:,} pairs: a description or unit varies within a pair"
    assert rows == EXPECTED_COMMODITY_ATTRIBUTES, f"Got {rows} pairs, expected {EXPECTED_COMMODITY_ATTRIBUTES}"

    nulls = one(con, """
        SELECT count(*) FROM commodity_attribute
        WHERE Commodity_Code IS NULL OR Commodity_Description IS NULL OR Attribute_ID IS NULL
           OR Attribute_Description IS NULL OR Unit_Description IS NULL
    """)[0]
    assert nulls == 0, f"{nulls} rows with a missing value"

    orphans = one(con, "SELECT count(*) FROM psd ANTI JOIN commodity_attribute USING (Commodity_Code, Attribute_ID)")[0]
    assert orphans == 0, f"{orphans:,} psd_alldata rows with no commodity_attribute row"

    print(f"Checks passed: {rows} commodity-attribute pairs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="replace existing output")
    args = parser.parse_args()
    run(args.force)


if __name__ == "__main__":
    main()
