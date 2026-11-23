import hashlib

import duckdb

CSV = "raw/energy_usage_2010.csv"
SHA256 = "6e59d593ef8c0a21aea92fcea363bcbb1770fdad221e2f8d2ca199ee9391802b"  # as in fetch_raw.py and sources.toml
OUT = "useful-views/energy-usage-2010.parquet"

digest = hashlib.sha256()
with open(CSV, "rb") as file:
    for chunk in iter(lambda: file.read(1 << 20), b""):
        digest.update(chunk)
if digest.hexdigest() != SHA256:  # not an assert: python -O would skip it
    raise SystemExit(f"{CSV} is not the pinned download (its SHA-256 is {digest.hexdigest()}). Run fetch_raw.py.")

MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
STATS = ["mean", "standard_deviation", "minimum", "1st_quartile", "2nd_quartile", "3rd_quartile", "maximum"]
KEY = ["community_area_name", "census_block", "building_type", "building_subtype"]
# The portal's columns, in its order (API field names). It spells April's therms "term_april_2010".
HEADER = (
    KEY
    + [f"kwh_{m}_2010" for m in MONTHS] + ["total_kwh", "electricity_accounts", "zero_kwh_accounts"]
    + [("term" if m == "april" else "therm") + f"_{m}_2010" for m in MONTHS] + ["total_therms", "gas_accounts"]
    + ["kwh_total_sqft", "therms_total_sqft"]
    + [f"{group}_{s}_2010" for group in ("kwh", "kwh_sqft", "therm", "therms_sqft") for s in STATS]
    + ["total_population", "total_units", "average_stories", "average_building_age", "average_housesize",
       "occupied_units", "occupied_units_percentage", "renter_occupied_housing_units",
       "renter_occupied_housing_percentage", "ten_ohu_tot"]
)
ACCOUNTS = ("electricity_accounts", "gas_accounts")  # a count, or the text "Less than 4"
INTEGERS = ("zero_kwh_accounts", "total_population", "total_units", "occupied_units",
            "renter_occupied_housing_units", "ten_ohu_tot")
DECIMALS = tuple(f"{group}_{s}_2010" for group in ("kwh", "kwh_sqft", "therm", "therms_sqft")
                 for s in STATS if s not in ("minimum", "maximum")) + (
    "average_stories", "average_building_age", "average_housesize",
    "occupied_units_percentage", "renter_occupied_housing_percentage")
EXPECTED = {
    "rows": 67_051, "rows without a block": 77, "community areas": 77, "census blocks": 35_699,
    'electricity "Less than 4"': 11_817, 'gas "Less than 4"': 12_577,
}


def typed(name: str) -> str:
    """The SELECT expression for one of the portal's columns."""
    column = f'"{name}"'
    if name in KEY:
        return column
    if name in ACCOUNTS:
        return (f"CAST(NULLIF({column}, 'Less than 4') AS INTEGER) AS {name}, "
                f"CASE WHEN {column} = 'Less than 4' THEN 'Less than 4' END AS {name}_note")
    alias = "therm_april_2010" if name == "term_april_2010" else name
    kind = "INTEGER" if name in INTEGERS else "DOUBLE" if name in DECIMALS else "BIGINT"
    return f"CAST({column} AS {kind}) AS {alias}"


con = duckdb.connect()
con.execute(f"CREATE VIEW csv AS SELECT * FROM read_csv('{CSV}', header = true, all_varchar = true)")
header = [row[0] for row in con.execute("SELECT column_name FROM (DESCRIBE csv)").fetchall()]
assert header == HEADER, f"The CSV's columns differ from the portal's 73: {header}"

order = ", ".join(f"{k} NULLS FIRST" for k in KEY)
con.execute(f"COPY (SELECT {', '.join(typed(n) for n in HEADER)} FROM csv ORDER BY {order}) "
            f"TO '{OUT}' (FORMAT PARQUET, COMPRESSION ZSTD)")
con.execute(f"CREATE VIEW v AS SELECT * FROM '{OUT}'")
one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731

facts = {
    "rows": one("SELECT count(*) FROM v"),
    "rows without a block": one("SELECT count(*) FROM v WHERE census_block IS NULL"),
    "community areas": one("SELECT count(DISTINCT community_area_name) FROM v"),
    "census blocks": one("SELECT count(DISTINCT census_block) FROM v"),
    'electricity "Less than 4"': one("SELECT count(*) FROM v WHERE electricity_accounts_note IS NOT NULL"),
    'gas "Less than 4"': one("SELECT count(*) FROM v WHERE gas_accounts_note IS NOT NULL"),
}
assert facts == EXPECTED, f"Known facts differ: {facts}"

# A row without a census block has no building type either: one per community area.
assert one("SELECT count(*) FROM v WHERE (census_block IS NULL) <> (building_type IS NULL) "
           "OR (census_block IS NULL) <> (building_subtype IS NULL)") == 0, "A row has a block but no type, or a type but no block"
assert one("SELECT count(DISTINCT community_area_name) FROM v WHERE census_block IS NULL") == 77, "Not one block-less row per area"
assert one("SELECT count(*) FROM v WHERE community_area_name IS NULL") == 0, "A row has no community area"
assert one("SELECT count(*) FROM v WHERE NOT regexp_full_match(census_block, '17031[0-9]{10}')") == 0, \
    "A census block is not a 15-digit Cook County block code"
assert one(f"SELECT count(*) FROM (SELECT {', '.join(KEY)} FROM v GROUP BY ALL HAVING count(*) > 1)") == 0, \
    "The key (community area, census block, building type, subtype) is not unique"

# Each account count is a number of at least 4, or the note "Less than 4", or missing (no accounts reported).
for name in ACCOUNTS:
    assert one(f"SELECT count(*) FROM v WHERE {name} < 4 OR ({name} IS NOT NULL AND {name}_note IS NOT NULL)") == 0, \
        f"{name} and its note disagree"

# The published annual totals are the sums of their months, exactly.
for total, prefix in (("total_kwh", "kwh"), ("total_therms", "therm")):
    months = " + ".join(f"coalesce({prefix}_{m}_2010, 0)" for m in MONTHS)
    assert one(f"SELECT count(*) FROM v WHERE {total} <> {months}") == 0, f"{total} is not the sum of its months"
    assert one(f"SELECT count(*) FROM v WHERE {total} IS NULL AND {months} <> 0") == 0, f"Months without a {total}"
energy = [f"{p}_{m}_2010" for p in ("kwh", "therm") for m in MONTHS] + ["total_kwh", "total_therms"]
assert one(f"SELECT count(*) FROM v WHERE least({', '.join(energy)}) < 0") == 0, "Negative energy use"

# The two "percentage" columns are fractions; the portal's last column repeats occupied_units.
for name in ("occupied_units_percentage", "renter_occupied_housing_percentage"):
    assert one(f"SELECT count(*) FROM v WHERE {name} NOT BETWEEN 0 AND 1") == 0, f"{name} is outside 0 to 1"
assert one("SELECT count(*) FROM v WHERE ten_ohu_tot IS DISTINCT FROM occupied_units") == 0, "ten_ohu_tot differs from occupied_units"
