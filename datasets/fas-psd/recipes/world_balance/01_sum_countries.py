import duckdb

# Rates and ratios, not quantities, so a sum across countries is meaningless: 181 Extr. Rate,
# 182 Milling Rate, 183 Seed to Lint Ratio, 184 Yield, 195 Stocks-to-Use, 220 Annual % Change Per Cap. Cons.
NON_ADDITIVE = ("181", "182", "183", "184", "195", "220")

# Commodity-years where Total Supply != Beginning Stocks + Production + Imports, or
# Total Distribution != Exports + Domestic Consumption + Ending Stocks, by more than 1 unit.
IMBALANCED = """
SELECT DISTINCT Commodity_Code, Market_Year FROM (
    PIVOT (SELECT {by}, 'a' || Attribute_ID AS a, Value FROM {table}
           WHERE Attribute_ID IN ('020', '028', '057', '086', '088', '125', '176', '178'))
    ON a USING first(Value)
)
WHERE abs(a086 - (a020 + a028 + a057)) > 1 OR abs(a178 - (a088 + a125 + a176)) > 1
"""

con = duckdb.connect()
con.execute("CREATE VIEW psd AS SELECT * FROM 'useful-views/psd-2026-11-17-alldata.parquet'")

# The sum below is exact only if no value has more than 2 decimal places.
finer = con.execute("SELECT count(*) FROM psd WHERE round(Value, 2) <> Value").fetchone()[0]
assert finer == 0, f"{finer:,} values have more than 2 decimal places: widen the DECIMAL scale below"

con.execute(
    f"""
    COPY (
        SELECT Commodity_Code, Commodity_Description, Market_Year, Attribute_ID, Attribute_Description,
               Unit_Description,
               CAST(sum(CAST(Value AS DECIMAL(18, 2))) AS DOUBLE) AS Value,
               CAST(count(*) FILTER (WHERE Value <> 0) AS SMALLINT) AS n_countries
        FROM psd
        WHERE Attribute_ID NOT IN {NON_ADDITIVE}
        GROUP BY ALL
        ORDER BY Commodity_Code, Market_Year, Attribute_ID
    ) TO 'useful-views/psd-2026-11-17-world-balance.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
)
con.execute("CREATE VIEW world AS SELECT * FROM 'useful-views/psd-2026-11-17-world-balance.parquet'")

rows, keys = con.execute("SELECT count(*), count(DISTINCT (Commodity_Code, Market_Year, Attribute_ID)) FROM world").fetchone()
assert rows == keys, f"{rows:,} rows but {keys:,} keys: a description or unit varies within a key"
source = con.execute(
    f"SELECT count(DISTINCT (Commodity_Code, Market_Year, Attribute_ID)) FROM psd WHERE Attribute_ID NOT IN {NON_ADDITIVE}"
).fetchone()[0]
assert rows == source, f"{rows:,} rows, expected {source:,}"
left_out = con.execute(f"SELECT count(*) FROM world WHERE Attribute_ID IN {NON_ADDITIVE}").fetchone()[0]
assert left_out == 0, f"{left_out} rows of rates or ratios in the world balance"
world_total, country_total = con.execute(
    f"""SELECT (SELECT sum(CAST(Value AS DECIMAL(38, 2))) FROM world),
               (SELECT sum(CAST(Value AS DECIMAL(38, 2))) FROM psd WHERE Attribute_ID NOT IN {NON_ADDITIVE})"""
).fetchone()
assert world_total == country_total, f"World values sum to {world_total}, country values to {country_total}"

# Summing adds no imbalance: every world imbalance is inherited from a country.
country = IMBALANCED.format(by="Commodity_Code, Country_Code, Market_Year", table="psd")
world = IMBALANCED.format(by="Commodity_Code, Market_Year", table="world")
new = con.execute(f"SELECT * FROM ({world}) EXCEPT SELECT * FROM ({country})").fetchall()
assert not new, f"World imbalances not explained by any country: {new}"
