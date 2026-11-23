import duckdb

IN = "useful-views/energy-usage-2010.parquet"
OUT = "useful-views/energy-usage-2010-community-areas.parquet"

con = duckdb.connect()
# Only rows with a census block are summed. The portal's 77 rows without one (a row per
# community area) overlap the block rows: see the README, "Things to know".
con.execute(f"""
    COPY (
        SELECT community_area_name,
               CAST(count(DISTINCT census_block) AS INTEGER) AS census_blocks,
               CAST(count(*) AS INTEGER) AS block_rows,
               CAST(count(total_kwh) AS INTEGER) AS rows_with_kwh,
               CAST(sum(total_kwh) AS BIGINT) AS total_kwh,
               CAST(count(total_therms) AS INTEGER) AS rows_with_therms,
               CAST(sum(total_therms) AS BIGINT) AS total_therms
        FROM '{IN}'
        WHERE census_block IS NOT NULL
        GROUP BY community_area_name
        ORDER BY community_area_name
    ) TO '{OUT}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")

one = lambda sql: con.execute(sql).fetchone()  # noqa: E731
assert one(f"SELECT count(*), count(DISTINCT community_area_name) FROM '{OUT}'") == (77, 77), "Not one row per community area"
summed = one(f"SELECT sum(block_rows), sum(total_kwh), sum(total_therms) FROM '{OUT}'")
source = one(f"SELECT count(*), sum(total_kwh), sum(total_therms) FROM '{IN}' WHERE census_block IS NOT NULL")
assert summed == source, f"The areas add up to {summed}, the block rows to {source}"
