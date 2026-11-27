import hashlib

import duckdb

PINS = {  # as in fetch_raw.py and sources.toml
    "raw/tract_covariates.csv": "270297349f75a60b39873ed5b71184ca68fc297397feeab7755221e1f6a82319",
    "raw/cty_covariates.csv": "4eb4f2f89292eb8f1d299bf104f870247ec432fe572a46e42fda89ec5ac98416",
    "raw/cz_covariates.csv": "e00c7e08bfd208d4c881d7a82b34a9a53d62b3fab79e0ab6131c4abf5828c41c",
}
for path, expected in PINS.items():
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:  # not an assert: python -O would skip it
        raise SystemExit(f"{path} is not the pinned download (its SHA-256 is {digest.hexdigest()}). Run fetch_raw.py.")

# view -> (CSV, its key columns as published, the typed key expressions, sort key, measures, rows, rows without a CZ)
TABLES = {
    "tract": ("raw/tract_covariates.csv", ["state", "county", "tract", "cz", "czname"], [
        "lpad(state, 2, '0') || lpad(county, 3, '0') || lpad(tract, 6, '0') AS tract_fips",
        "lpad(state, 2, '0') AS state", "lpad(county, 3, '0') AS county", "lpad(tract, 6, '0') AS tract",
        "CAST(cz AS INTEGER) AS cz", "czname"], "tract_fips", 33, 74_044, 950),
    "county": ("raw/cty_covariates.csv", ["state", "county", "cz", "czname"], [
        "lpad(state, 2, '0') || lpad(county, 3, '0') AS county_fips",
        "lpad(state, 2, '0') AS state", "lpad(county, 3, '0') AS county",
        "CAST(cz AS INTEGER) AS cz", "czname"], "county_fips", 31, 3_221, 81),
    "cz": ("raw/cz_covariates.csv", ["cz", "czname"], ["CAST(cz AS INTEGER) AS cz", "czname"], "cz", 33, 741, 0),
}

con = duckdb.connect()
one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
for level, (csv, keys, typed_keys, key, n_measures, rows, no_cz) in TABLES.items():
    out = f"useful-views/{level}-covariates.parquet"
    con.execute(f"CREATE OR REPLACE VIEW csv AS SELECT * FROM read_csv('{csv}', header = true, all_varchar = true)")
    header = [r[0] for r in con.execute("SELECT column_name FROM (DESCRIBE csv)").fetchall()]
    assert header[:len(keys)] == keys, f"{csv} does not start with {keys}: {header[:len(keys)]}"
    measures = header[len(keys):]
    assert len(measures) == n_measures, f"{csv} has {len(measures)} measures, not {n_measures}"
    for m in measures:  # every characteristic is a number or empty
        assert one(f'SELECT count(*) FROM csv WHERE "{m}" IS NOT NULL AND TRY_CAST("{m}" AS DOUBLE) IS NULL') == 0, f"{csv}: {m} is not numeric"
    select = ", ".join(typed_keys + [f'CAST("{m}" AS DOUBLE) AS {m}' for m in measures])
    con.execute(f"COPY (SELECT {select} FROM csv ORDER BY {key}) TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.execute(f"CREATE OR REPLACE VIEW {level} AS SELECT * FROM '{out}'")

    assert one(f"SELECT count(*) FROM {level}") == rows, f"{level}: not {rows:,} rows"
    assert one(f"SELECT count(DISTINCT {key}) FROM {level}") == rows, f"{level}: {key} is not unique"
    assert one(f"SELECT count(*) FROM {level} WHERE (cz IS NULL) <> (czname IS NULL)") == 0, f"{level}: cz and czname disagree"
    assert one(f"SELECT count(*) FROM {level} WHERE cz IS NULL") == no_cz, f"{level}: not {no_cz} rows without a commuting zone"

# Outside Puerto Rico, the rows without a commuting zone (1990 definitions) are Alaska areas newer than them
# (Kusilvak, given here under both its old code 02270 and its new one 02158, and Yakutat, 02282) and, in the
# tracts, three tracts of Shannon County, South Dakota (46113, now Oglala Lakota County, 46102).
assert one("SELECT list(tract_fips ORDER BY tract_fips) FROM tract WHERE cz IS NULL AND state <> '72'").__len__() == 5, \
    "Not 5 tracts outside Puerto Rico without a commuting zone"
assert one("SELECT list(DISTINCT substr(tract_fips, 1, 5) ORDER BY 1) FROM tract WHERE cz IS NULL AND state <> '72'") == \
    ["02270", "02282", "46113"], "The tracts outside Puerto Rico without a CZ are not in 02270, 02282 and 46113"
assert one("SELECT list(county_fips ORDER BY county_fips) FROM county WHERE cz IS NULL AND state <> '72'") == \
    ["02158", "02270", "02282"], "The counties outside Puerto Rico without a CZ are not 02158, 02270 and 02282"
assert one("SELECT count(*) FROM tract WHERE NOT regexp_full_match(tract_fips, '[0-9]{11}')") == 0, "A tract_fips is not 11 digits"
for level in ("tract", "county"):
    assert one(f"SELECT count(*) FROM {level} t LEFT JOIN cz USING (cz) WHERE t.cz IS NOT NULL AND cz.czname IS DISTINCT FROM t.czname") == 0, \
        f"A {level}'s commuting zone is missing from the CZ table or named differently"
# Shares and rates are fractions.
for level, (_, keys, *_rest) in TABLES.items():
    cols = [r[0] for r in con.execute(f"SELECT column_name FROM (DESCRIBE {level})").fetchall()]
    for c in cols:
        if c.startswith(("share_", "poor_share", "frac_coll_plus", "singleparent_share", "foreign_share", "traveltime15", "emp2000", "mail_return_rate")):
            assert one(f"SELECT count(*) FROM {level} WHERE {c} NOT BETWEEN 0 AND 1") == 0, f"{level}: {c} is outside 0 to 1"
