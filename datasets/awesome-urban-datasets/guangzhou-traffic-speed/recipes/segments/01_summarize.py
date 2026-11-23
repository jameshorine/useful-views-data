import duckdb

IN = "useful-views/guangzhou-traffic-speed.parquet"
OUT = "useful-views/guangzhou-traffic-speed-segments.parquet"
WINDOWS = 61 * 144  # 61 days of 144 ten-minute windows

con = duckdb.connect()
# Speeds have three decimals, so thousandths are whole numbers: summing them as integers makes the
# mean exact, the same on every run.
con.execute(f"""
    COPY (
        SELECT road_id,
               CAST(count(*) AS INTEGER) AS observations,
               CAST({WINDOWS} - count(*) AS INTEGER) AS missing_windows,
               CAST(count(DISTINCT day_id) AS SMALLINT) AS days_with_data,
               min(speed) AS min_speed,
               round(CAST(sum(CAST(round(speed * 1000) AS BIGINT)) AS DOUBLE) / count(*) / 1000, 3) AS mean_speed,
               max(speed) AS max_speed
        FROM '{IN}'
        GROUP BY road_id
        ORDER BY road_id
    ) TO '{OUT}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")

one = lambda sql: con.execute(sql).fetchone()  # noqa: E731
assert one(f"SELECT count(*), count(DISTINCT road_id) FROM '{OUT}'") == (214, 214), "Not one row per segment"
assert one(f"SELECT sum(observations), sum(missing_windows) FROM '{OUT}'") == (1_855_589, 214 * WINDOWS - 1_855_589), \
    "Observations and missing windows don't add up to the dataset's totals"
assert one(f"SELECT count(*) FROM '{OUT}' WHERE NOT (min_speed <= mean_speed AND mean_speed <= max_speed)")[0] == 0, \
    "A mean outside its segment's range"
