"""Step 3: sum every country into a world balance.

Writes world_balance.parquet to the release folder: one row per commodity,
market year and attribute, with Value summed over every country exactly as
PSD publishes them, and n_countries counting the countries with a nonzero
value. Rates and ratios (config.NON_ADDITIVE_ATTRIBUTES) are left out.

The sum is plain: no country is dropped or adjusted. A few known cases count
the same production twice (an aggregate and a member both report it); they
are listed in the README for anyone who wants to propose an adjustment.

Values are summed as DECIMAL, which is exact (PSD values have at most two
decimal places), so the output is the same on every run.

Refuses to overwrite an existing output; pass --force to replace it.
"""

import argparse

import duckdb

from fas_psd.config import (
    NON_ADDITIVE_ATTRIBUTES,
    PSD_PARQUET_PATH,
    WORLD_BALANCE_PATH,
    prepare_outputs,
    require_outputs,
)

WORLD_BALANCE_SQL = f"""
SELECT
    Commodity_Code,
    Commodity_Description,
    Market_Year,
    Attribute_ID,
    Attribute_Description,
    Unit_Description,
    CAST(sum(CAST(Value AS DECIMAL(18, 2))) AS DOUBLE) AS Value,
    CAST(count(*) FILTER (WHERE Value <> 0) AS SMALLINT) AS n_countries
FROM psd
WHERE Attribute_ID NOT IN {NON_ADDITIVE_ATTRIBUTES}
GROUP BY ALL
ORDER BY Commodity_Code, Market_Year, Attribute_ID
"""

# Commodity-years where Total Supply != Beginning Stocks + Production + Imports
# or Total Distribution != Exports + Domestic Consumption + Ending Stocks, by
# more than 1 unit. `{by}` is the grouping: per country, or world.
IMBALANCED_SQL = """
SELECT DISTINCT Commodity_Code, Market_Year FROM (
    PIVOT (SELECT {by}, 'a' || Attribute_ID AS a, Value FROM {table}
           WHERE Attribute_ID IN ('020', '028', '057', '086', '088', '125', '176', '178'))
    ON a USING first(Value)
)
WHERE abs(a086 - (a020 + a028 + a057)) > 1
   OR abs(a178 - (a088 + a125 + a176)) > 1
"""


def one(con: duckdb.DuckDBPyConnection, sql: str):
    return con.execute(sql).fetchone()


def run(force: bool = False) -> None:
    require_outputs([PSD_PARQUET_PATH], before="step 1")
    prepare_outputs([WORLD_BALANCE_PATH], force)

    con = duckdb.connect()
    con.execute(f"CREATE VIEW psd AS SELECT * FROM read_parquet('{PSD_PARQUET_PATH}')")
    con.execute(f"COPY ({WORLD_BALANCE_SQL}) TO '{WORLD_BALANCE_PATH}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.execute(f"CREATE VIEW world_balance AS SELECT * FROM read_parquet('{WORLD_BALANCE_PATH}')")
    print(f"Wrote {WORLD_BALANCE_PATH}")

    # Checks: one row per key, one per key in the source, and nothing lost in the sum.
    rows, keys = one(con, "SELECT count(*), count(DISTINCT (Commodity_Code, Market_Year, Attribute_ID)) FROM world_balance")
    assert rows == keys, f"{rows:,} rows but {keys:,} keys: a description or unit varies within a key"

    source_keys = one(con, f"""
        SELECT count(DISTINCT (Commodity_Code, Market_Year, Attribute_ID)) FROM psd
        WHERE Attribute_ID NOT IN {NON_ADDITIVE_ATTRIBUTES}
    """)[0]
    assert rows == source_keys, f"{rows:,} rows, expected {source_keys:,}"

    left_out = one(con, f"SELECT count(*) FROM world_balance WHERE Attribute_ID IN {NON_ADDITIVE_ATTRIBUTES}")[0]
    assert left_out == 0, f"{left_out} rows of non-additive attributes"

    world_total, source_total = one(con, f"""
        SELECT (SELECT sum(CAST(Value AS DECIMAL(38, 2))) FROM world_balance),
               (SELECT sum(CAST(Value AS DECIMAL(38, 2))) FROM psd WHERE Attribute_ID NOT IN {NON_ADDITIVE_ATTRIBUTES})
    """)
    assert world_total == source_total, f"World values sum to {world_total}, country values to {source_total}"

    # The world balances wherever its countries do: summing adds no imbalance.
    country = IMBALANCED_SQL.format(by="Commodity_Code, Country_Code, Market_Year", table="psd")
    world = IMBALANCED_SQL.format(by="Commodity_Code, Market_Year", table="world_balance")
    new = con.execute(f"SELECT * FROM ({world}) EXCEPT SELECT * FROM ({country})").fetchall()
    assert not new, f"World imbalances not explained by any country: {new}"
    imbalanced = one(con, f"SELECT count(*) FROM ({world})")[0]

    print(
        f"Checks passed: {rows:,} commodity-year-attribute rows; "
        f"{imbalanced} commodity-years don't balance, all inherited from country rows"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="replace existing output")
    args = parser.parse_args()
    run(args.force)


if __name__ == "__main__":
    main()
