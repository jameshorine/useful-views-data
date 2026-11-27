import hashlib

import duckdb

CSV = "raw/pctile_to_dollar_cw.csv"
SHA256 = "89af2fc8d4a330a6ba36e4128f172f200c53f8e7f5175a392f8ac5f2db23cdb0"  # as in fetch_raw.py and sources.toml
OUT = "useful-views/percentile-dollars.parquet"

digest = hashlib.sha256()
with open(CSV, "rb") as file:
    for chunk in iter(lambda: file.read(1 << 20), b""):
        digest.update(chunk)
if digest.hexdigest() != SHA256:  # not an assert: python -O would skip it
    raise SystemExit(f"{CSV} is not the pinned download (its SHA-256 is {digest.hexdigest()}). Run fetch_raw.py.")

DOLLARS = ["kid_hh_income", "kid_indiv_income", "kid_wageflex", "kid_hh_income_age26", "kid_indiv_income_age26",
           "parent_hh_income"]
con = duckdb.connect()
con.execute(f"CREATE VIEW csv AS SELECT * FROM read_csv('{CSV}', header = true, all_varchar = true)")
header = [r[0] for r in con.execute("SELECT column_name FROM (DESCRIBE csv)").fetchall()]
assert header == ["percentile"] + DOLLARS, f"The CSV's columns differ from the codebook's: {header}"
select = ", ".join(["CAST(percentile AS INTEGER) AS percentile"] + [f"CAST({c} AS DOUBLE) AS {c}" for c in DOLLARS])
con.execute(f"COPY (SELECT {select} FROM csv ORDER BY percentile) TO '{OUT}' (FORMAT PARQUET, COMPRESSION ZSTD)")

one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
assert one(f"SELECT list(percentile ORDER BY percentile) FROM '{OUT}'") == list(range(101)), "The percentiles are not 0 to 100"
# Parents' income has no value at percentile 0; every other value is given.
assert one(f"SELECT count(*) FROM '{OUT}' WHERE parent_hh_income IS NULL") == 1, "Not one missing parent income"
assert one(f"SELECT percentile FROM '{OUT}' WHERE parent_hh_income IS NULL") == 0, "The missing parent income is not at percentile 0"
for c in DOLLARS:
    assert one(f"SELECT count(*) FROM (SELECT {c} - lag({c}) OVER (ORDER BY percentile) AS step FROM '{OUT}') WHERE step < 0") == 0, \
        f"{c} falls as the percentile rises"
