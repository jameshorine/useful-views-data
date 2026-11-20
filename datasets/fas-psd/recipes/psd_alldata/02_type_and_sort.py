import duckdb

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
KEY = "Commodity_Code, Country_Code, Market_Year, Attribute_ID"
ANY_NULL = " OR ".join(f"{column} IS NULL" for column in COLUMN_TYPES)

# Facts about the 2026-11-17 snapshot, profiled when it was added (see README.md).
EXPECTED = {"rows": 2_095_339, "commodities": 63, "countries": 214, "attributes": 69, "units": 11,
            "first_year": 1960, "last_year": 2027}

# read_csv assigns the types by position, so check the header first.
with open("work/psd_alldata/psd_alldata.csv", encoding="utf-8-sig") as file:
    header = file.readline().strip().split(",")
assert header == list(COLUMN_TYPES), f"Unexpected columns: {header}"

con = duckdb.connect()
con.execute(
    f"""
    COPY (
        SELECT * FROM read_csv('work/psd_alldata/psd_alldata.csv', header = true, columns = {COLUMN_TYPES})
        ORDER BY {KEY}
    ) TO 'useful-views/psd-2026-11-17-alldata.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
)

rows, keys, nulls, commodities, countries, attributes, units, first_year, last_year = con.execute(
    f"""
    SELECT count(*), count(DISTINCT ({KEY})), count(*) FILTER ({ANY_NULL}),
           count(DISTINCT Commodity_Code), count(DISTINCT Country_Code), count(DISTINCT Attribute_ID),
           count(DISTINCT Unit_ID), min(Market_Year), max(Market_Year)
    FROM 'useful-views/psd-2026-11-17-alldata.parquet'
    """
).fetchone()
found = {"rows": rows, "commodities": commodities, "countries": countries, "attributes": attributes,
         "units": units, "first_year": first_year, "last_year": last_year}
assert found == EXPECTED, f"Snapshot facts {found} differ from {EXPECTED}"
assert keys == rows, f"The key is not unique: {rows - keys:,} duplicate rows"
assert nulls == 0, f"{nulls:,} rows with a missing value"
