"""Step 3: build the tidy CSB views from the step 1 export.

Writes three tables to the release folder (useful-views/csb_2025/), next to
land_cover_codes.parquet:
  csb_field_year  one row per field per year (land cover)
  csb_field       one row per field (acres, interior point, geometry)
  county          one row per county

Refuses to overwrite existing outputs; pass --force to replace them.
"""

import argparse

import duckdb

from crop_sequence_boundaries.config import (
    COUNTY_PATH,
    CSB_FIELD_PATH,
    CSB_FIELD_YEAR_PATH,
    EXPECTED_FEATURES,
    LAND_COVER_PARQUET_PATH,
    NATIONAL_PARQUET_PATH,
    YEARS,
    prepare_outputs,
    require_outputs,
)

FIELD_YEAR_SQL = """
SELECT
    CSBID AS csb_id,
    CAST(substr(cdl_column, 4) AS SMALLINT) AS year,
    CAST(land_cover_code AS SMALLINT) AS land_cover_code
FROM (
    UNPIVOT (SELECT CSBID, COLUMNS('^CDL\\d{4}$') FROM national)
    ON COLUMNS('^CDL\\d{4}$')
    INTO NAME cdl_column VALUE land_cover_code
)
ORDER BY csb_id, year
"""

FIELD_SQL = """
SELECT
    CSBID AS csb_id,
    STATEFIPS || CNTYFIPS AS county_geoid,
    CSBACRES AS csb_acres,
    INSIDE_X AS inside_x,
    INSIDE_Y AS inside_y,
    Shape AS geometry
FROM national
ORDER BY csb_id
"""

COUNTY_SQL = """
SELECT DISTINCT
    STATEFIPS || CNTYFIPS AS county_geoid,
    STATEFIPS AS state_fips,
    CNTYFIPS AS county_fips,
    CNTY AS county_name,
    STATEASD AS asd_code
FROM national
ORDER BY county_geoid
"""


def one(con: duckdb.DuckDBPyConnection, sql: str):
    return con.execute(sql).fetchone()


def run(force: bool = False) -> None:
    require_outputs([NATIONAL_PARQUET_PATH, LAND_COVER_PARQUET_PATH], before="steps 1 and 2")
    outputs = {
        "csb_field_year": (CSB_FIELD_YEAR_PATH, FIELD_YEAR_SQL),
        "csb_field": (CSB_FIELD_PATH, FIELD_SQL),
        "county": (COUNTY_PATH, COUNTY_SQL),
    }
    prepare_outputs([path for path, _ in outputs.values()], force)

    con = duckdb.connect()
    con.execute("INSTALL spatial")
    con.execute("LOAD spatial")
    con.execute(f"CREATE VIEW national AS SELECT * FROM read_parquet('{NATIONAL_PARQUET_PATH}')")
    con.execute(f"CREATE VIEW land_cover AS SELECT * FROM read_parquet('{LAND_COVER_PARQUET_PATH}')")

    for name, (path, sql) in outputs.items():
        con.execute(f"COPY ({sql}) TO '{path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{path}')")
        print(f"Wrote {path}")

    # Checks: row counts, unique keys, and joins that lose nothing.
    n_fields = EXPECTED_FEATURES
    n_years = len(YEARS)

    rows, keys = one(con, "SELECT count(*), count(DISTINCT (csb_id, year)) FROM csb_field_year")
    assert rows == keys == n_fields * n_years, f"csb_field_year: {rows:,} rows, {keys:,} keys"

    years = [r[0] for r in con.execute("SELECT DISTINCT year FROM csb_field_year ORDER BY 1").fetchall()]
    assert years == list(YEARS), f"Unexpected years: {years}"

    nulls = one(con, "SELECT count(*) FROM csb_field_year WHERE land_cover_code IS NULL")[0]
    assert nulls == 0, f"{nulls:,} missing land-cover codes"

    unknown = con.execute("""
        SELECT DISTINCT land_cover_code FROM csb_field_year
        ANTI JOIN land_cover USING (land_cover_code)
    """).fetchall()
    assert not unknown, f"Codes missing from land_cover_codes: {unknown}"

    rows, keys = one(con, "SELECT count(*), count(DISTINCT csb_id) FROM csb_field")
    assert rows == keys == n_fields, f"csb_field: {rows:,} rows, {keys:,} keys"

    rows, keys = one(con, "SELECT count(*), count(DISTINCT county_geoid) FROM county")
    assert rows == keys, f"county: {rows:,} rows but {keys:,} distinct county_geoid (name or ASD varies)"

    orphans = one(con, "SELECT count(*) FROM csb_field ANTI JOIN county USING (county_geoid)")[0]
    assert orphans == 0, f"{orphans:,} fields with no county row"

    print(f"Checks passed: {n_fields:,} fields x {n_years} years; {rows:,} counties")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="replace existing outputs")
    args = parser.parse_args()
    run(args.force)


if __name__ == "__main__":
    main()