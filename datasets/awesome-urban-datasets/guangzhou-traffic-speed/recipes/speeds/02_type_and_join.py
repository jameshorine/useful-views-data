import duckdb

DIR = "work/speeds/Data"
OUT = "useful-views/guangzhou-traffic-speed.parquet"
HEADERS = {
    "traffic_speed_data": ["road_id", "day_id", "time_id", "speed"],
    "day_information_table": ["day_id", "date"],
    "time_information_table": ["time_id", "start_time", "end_time"],
}
EXPECTED = {
    "rows": 1_855_589, "segments": 214, "days": 61, "windows": 144,
    "complete segments": 206, "speeds with float noise": 455_175,
}

con = duckdb.connect()
for table, header in HEADERS.items():
    con.execute(f"CREATE VIEW {table} AS SELECT * FROM read_csv('{DIR}/{table}.csv', header = true, all_varchar = true)")
    columns = [row[0] for row in con.execute(f"SELECT column_name FROM (DESCRIBE {table})").fetchall()]
    assert columns == header, f"{table}.csv has the columns {columns}, expected {header}"
one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731

# The lookup tables: day 1 is 2016-08-01, and window 1 starts at 00:00; each window is 10 minutes long.
con.execute("""
    CREATE TABLE days AS
    SELECT CAST(day_id AS SMALLINT) AS day_id, CAST(strptime(date, '%Y/%-m/%-d') AS DATE) AS date
    FROM day_information_table
""")
con.execute("""
    CREATE TABLE windows AS
    SELECT CAST(time_id AS SMALLINT) AS time_id,
           CAST(strptime(start_time, '%-H:%M:%S') AS TIME) AS start_time,
           CAST(strptime(end_time, '%-H:%M:%S') AS TIME) AS end_time
    FROM time_information_table
""")
assert one("SELECT count(*) FROM days WHERE date <> DATE '2016-08-01' + (day_id - 1)") == 0, "Days are not 2016-08-01 onwards"
assert one("SELECT count(*) FROM days") == 61, "Not 61 days"
assert one("""SELECT count(*) FROM windows
              WHERE start_time <> TIME '00:00:00' + INTERVAL (10 * (time_id - 1)) MINUTE
                 OR end_time <> start_time + INTERVAL 10 MINUTE""") == 0, "Windows are not consecutive 10-minute steps"
assert one("SELECT count(*) FROM windows") == 144, "Not 144 windows"

con.execute(f"""
    COPY (
        SELECT CAST(s.road_id AS SMALLINT) AS road_id,
               CAST(s.day_id AS SMALLINT) AS day_id,
               CAST(s.time_id AS SMALLINT) AS time_id,
               d.date + w.start_time AS window_start,
               round(CAST(s.speed AS DOUBLE), 3) AS speed
        FROM traffic_speed_data s
        JOIN days d ON CAST(s.day_id AS SMALLINT) = d.day_id
        JOIN windows w ON CAST(s.time_id AS SMALLINT) = w.time_id
        ORDER BY road_id, day_id, time_id
    ) TO '{OUT}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
con.execute(f"CREATE VIEW v AS SELECT * FROM '{OUT}'")

facts = {
    "rows": one("SELECT count(*) FROM v"),
    "segments": one("SELECT count(DISTINCT road_id) FROM v"),
    "days": one("SELECT count(DISTINCT day_id) FROM v"),
    "windows": one("SELECT count(DISTINCT time_id) FROM v"),
    "complete segments": one("SELECT count(*) FROM (SELECT road_id FROM v GROUP BY 1 HAVING count(*) = 61 * 144)"),
    "speeds with float noise": one("SELECT count(*) FROM traffic_speed_data WHERE round(CAST(speed AS DOUBLE), 3) <> CAST(speed AS DOUBLE)"),
}
assert facts == EXPECTED, f"Known facts differ: {facts}"
assert one("SELECT count(*) FROM traffic_speed_data") == facts["rows"], "Rows were lost in the join"
assert one("SELECT count(*) FROM (SELECT road_id, day_id, time_id FROM v GROUP BY ALL HAVING count(*) > 1)") == 0, \
    "The key (segment, day, window) is not unique"
assert one("SELECT count(*) FROM v WHERE road_id NOT BETWEEN 1 AND 214 OR speed IS NULL OR speed <= 0") == 0, \
    "A segment outside 1-214, or a missing or non-positive speed"
# Rounding only removes float noise: no published speed moves by more than a billionth.
assert one("SELECT max(abs(round(CAST(speed AS DOUBLE), 3) - CAST(speed AS DOUBLE))) FROM traffic_speed_data") < 1e-9, \
    "Rounding to three decimals changed a speed by more than float noise"
assert one("""SELECT count(*) FROM v WHERE window_start NOT BETWEEN TIMESTAMP '2016-08-01 00:00:00'
                                                        AND TIMESTAMP '2016-09-30 23:50:00'""") == 0, "A window outside the period"
