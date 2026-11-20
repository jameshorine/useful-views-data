import duckdb

EXPECTED_PAIRS = 752  # 2026-11-17 snapshot

con = duckdb.connect()
con.execute("CREATE VIEW psd AS SELECT * FROM 'useful-views/psd-2026-11-17-alldata.parquet'")
con.execute(
    """
    COPY (
        SELECT DISTINCT Commodity_Code, Commodity_Description, Attribute_ID, Attribute_Description, Unit_Description
        FROM psd
        ORDER BY Attribute_ID, Commodity_Code
    ) TO 'useful-views/psd-2026-11-17-commodity-attribute.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
)
con.execute("CREATE VIEW pairs AS SELECT * FROM 'useful-views/psd-2026-11-17-commodity-attribute.parquet'")

rows, keys = con.execute("SELECT count(*), count(DISTINCT (Commodity_Code, Attribute_ID)) FROM pairs").fetchone()
assert rows == keys, f"{rows:,} rows but {keys:,} pairs: a description or unit varies within a pair"
assert rows == EXPECTED_PAIRS, f"Got {rows} pairs, expected {EXPECTED_PAIRS}"
nulls = con.execute(
    """SELECT count(*) FROM pairs
       WHERE Commodity_Code IS NULL OR Commodity_Description IS NULL OR Attribute_ID IS NULL
          OR Attribute_Description IS NULL OR Unit_Description IS NULL"""
).fetchone()[0]
assert nulls == 0, f"{nulls} pairs with a missing value"
orphans = con.execute("SELECT count(*) FROM psd ANTI JOIN pairs USING (Commodity_Code, Attribute_ID)").fetchone()[0]
assert orphans == 0, f"{orphans:,} psd_alldata rows with no commodity_attribute row"
