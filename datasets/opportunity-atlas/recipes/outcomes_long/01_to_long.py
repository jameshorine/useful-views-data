import duckdb

OUT = "useful-views/outcomes-long.parquet"
RACES = ("pooled", "white", "black", "hisp")
GENDERS = ("pooled", "female", "male")
OUTCOMES = ("kfr", "jail")
LEVELS = {"tract": "tract_fips", "county": "county_fips", "cz": "CAST(cz AS VARCHAR)"}  # geography -> its id as text

con = duckdb.connect()
parts = [
    f"SELECT '{level}' AS geography, {gid} AS geography_id, cz, czname, '{o}' AS outcome, '{r}' AS race, "
    f"'{g}' AS gender, 25 AS parent_percentile, {o}_{r}_{g}_p25 AS estimate, {o}_{r}_{g}_p25_se AS standard_error, "
    f"{r}_{g}_count AS children FROM 'useful-views/{level}-outcomes.parquet' WHERE {o}_{r}_{g}_p25 IS NOT NULL"
    for level, gid in LEVELS.items() for o in OUTCOMES for r in RACES for g in GENDERS
]
order = "CASE geography WHEN 'tract' THEN 1 WHEN 'county' THEN 2 ELSE 3 END, geography_id, outcome, race, gender"
con.execute(f"COPY (SELECT * FROM ({' UNION ALL '.join(parts)}) ORDER BY {order}) TO '{OUT}' (FORMAT PARQUET, COMPRESSION ZSTD)")

one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
published = sum(
    one(f"SELECT count({o}_{r}_{g}_p25) FROM 'useful-views/{level}-outcomes.parquet'")
    for level in LEVELS for o in OUTCOMES for r in RACES for g in GENDERS
)
rows = one(f"SELECT count(*) FROM '{OUT}'")
assert rows == published, f"{rows:,} rows, but the wide tables have {published:,} estimates"
assert one(f"SELECT count(*) FROM (SELECT geography, geography_id, outcome, race, gender FROM '{OUT}' GROUP BY ALL HAVING count(*) > 1)") == 0, \
    "The key (geography, geography_id, outcome, race, gender) is not unique"
assert one(f"SELECT count(*) FROM '{OUT}' WHERE standard_error IS NULL") == 48, "Not the 48 tract estimates known to lack a standard error"
