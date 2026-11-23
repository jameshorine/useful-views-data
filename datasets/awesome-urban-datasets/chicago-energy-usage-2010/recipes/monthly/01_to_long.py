import duckdb

IN = "useful-views/energy-usage-2010.parquet"
OUT = "useful-views/energy-usage-2010-monthly.parquet"
MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
KEY = ["community_area_name", "census_block", "building_type", "building_subtype"]

con = duckdb.connect()
months = " UNION ALL ".join(
    f"SELECT {', '.join(KEY)}, DATE '2010-{number:02d}-01' AS month, kwh_{name}_2010 AS kwh, therm_{name}_2010 AS therms "
    f"FROM '{IN}'"
    for number, name in enumerate(MONTHS, start=1)
)
order = ", ".join(f"{k} NULLS FIRST" for k in KEY)
con.execute(f"COPY (SELECT * FROM ({months}) ORDER BY {order}, month) TO '{OUT}' (FORMAT PARQUET, COMPRESSION ZSTD)")

one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
rows, wide = one(f"SELECT count(*) FROM '{OUT}'"), one(f"SELECT count(*) FROM '{IN}'")
assert rows == 12 * wide, f"{rows:,} rows, expected 12 x {wide:,}"
assert one(f"SELECT count(*) FROM (SELECT {', '.join(KEY)}, month FROM '{OUT}' GROUP BY ALL HAVING count(*) > 1)") == 0, \
    "The key (community area, census block, building type, subtype, month) is not unique"

# Each row's twelve months add up to the annual totals published in the wide table.
joined = " AND ".join(f"w.{k} IS NOT DISTINCT FROM m.{k}" for k in KEY)
mismatched = one(f"""
    SELECT count(*) FROM '{IN}' w JOIN (
        SELECT {', '.join(KEY)}, sum(kwh) AS kwh, sum(therms) AS therms FROM '{OUT}' GROUP BY ALL
    ) m ON {joined}
    WHERE w.total_kwh IS DISTINCT FROM m.kwh OR w.total_therms IS DISTINCT FROM m.therms
""")
assert mismatched == 0, f"{mismatched} rows whose months do not add up to their annual totals"
