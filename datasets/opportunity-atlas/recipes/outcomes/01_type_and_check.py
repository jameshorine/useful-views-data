import hashlib

import duckdb

PINS = {  # as in fetch_raw.py and sources.toml
    "raw/tract_outcomes_simple.csv": "d246a041179cac832983f1814725e91c8f99adc41d31b06ee3ac9b4f662be10b",
    "raw/county_outcomes_simple.csv": "c355f7cade477637edb57a09b81e11bc102cb61d76a4758bea640590f51a5895",
    "raw/cz_outcomes_simple.csv": "b096cdb13e1e94f7fac740d7d0d1cbb7cd09eafc6e5cb0774a06d39a9a4c0c84",
}
for path, expected in PINS.items():
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:  # not an assert: python -O would skip it
        raise SystemExit(f"{path} is not the pinned download (its SHA-256 is {digest.hexdigest()}). Run fetch_raw.py.")

RACES = ("pooled", "white", "black", "hisp")
GENDERS = ("pooled", "female", "male")
# The codebooks' 60 measures (Tables 1-3): kfr and jail at p25 with standard errors, and the count, per race and gender.
MEASURES = {f"{o}_{r}_{g}_p25{se}" for o in ("kfr", "jail") for r in RACES for g in GENDERS for se in ("", "_se")} | {
    f"{r}_{g}_count" for r in RACES for g in GENDERS}

# view -> (CSV, its key columns as published, the typed key expressions, sort key, expected rows)
TABLES = {
    "tract": ("raw/tract_outcomes_simple.csv", ["state", "county", "tract", "cz", "czname"], [
        "lpad(state, 2, '0') || lpad(county, 3, '0') || lpad(tract, 6, '0') AS tract_fips",
        "lpad(state, 2, '0') AS state", "lpad(county, 3, '0') AS county", "lpad(tract, 6, '0') AS tract",
        "CAST(cz AS INTEGER) AS cz", "czname"], "tract_fips", 73_278),
    "county": ("raw/county_outcomes_simple.csv", ["state", "county", "cz", "czname"], [
        "lpad(state, 2, '0') || lpad(county, 3, '0') AS county_fips",
        "lpad(state, 2, '0') AS state", "lpad(county, 3, '0') AS county",
        "CAST(cz AS INTEGER) AS cz", "czname"], "county_fips", 3_219),
    "cz": ("raw/cz_outcomes_simple.csv", ["cz", "czname"], ["CAST(cz AS INTEGER) AS cz", "czname"], "cz", 741),
}

# (geography, outcome) -> estimates below 0 and above 1, over every race-gender cell
OUTSIDE = {("tract", "kfr"): (35, 18), ("tract", "jail"): (136_726, 6), ("county", "kfr"): (0, 0),
           ("county", "jail"): (2_677, 0), ("cz", "kfr"): (0, 0), ("cz", "jail"): (447, 0)}

con = duckdb.connect()
one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
for level, (csv, keys, typed_keys, key, rows) in TABLES.items():
    out = f"useful-views/{level}-outcomes.parquet"
    con.execute(f"CREATE OR REPLACE VIEW csv AS SELECT * FROM read_csv('{csv}', header = true, all_varchar = true)")
    header = [r[0] for r in con.execute("SELECT column_name FROM (DESCRIBE csv)").fetchall()]
    assert header[:len(keys)] == keys, f"{csv} does not start with {keys}: {header[:len(keys)]}"
    measures = header[len(keys):]
    assert len(measures) == len(MEASURES) and set(measures) == MEASURES, f"{csv}'s measures differ from the codebook's 60"
    select = ", ".join(typed_keys + [f'CAST("{m}" AS DOUBLE) AS {m}' for m in measures])
    con.execute(f"COPY (SELECT {select} FROM csv ORDER BY {key}) TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.execute(f"CREATE OR REPLACE VIEW {level} AS SELECT * FROM '{out}'")

    assert one(f"SELECT count(*) FROM {level}") == rows, f"{level}: not {rows:,} rows"
    assert one(f"SELECT count(DISTINCT {key}) FROM {level}") == rows, f"{level}: {key} is not unique"
    assert one(f"SELECT count(*) FROM {level} WHERE (cz IS NULL) <> (czname IS NULL)") == 0, f"{level}: cz and czname disagree"
    # Standard errors and counts are never negative.
    assert one(f"SELECT count(*) FROM {level} WHERE least({', '.join(m for m in measures if m.endswith(('_se', '_count')))}) < 0") == 0, \
        f"{level}: a negative standard error or count"
    # Estimates are predictions from a regression plus privacy noise (see the README), so they can fall outside
    # 0 to 1, mostly in small tract cells. These counts are the published files' own.
    for outcome in ("kfr", "jail"):
        cells = [m for m in measures if m.startswith(outcome) and m.endswith("_p25")]
        below = sum(one(f"SELECT count(*) FROM {level} WHERE {m} < 0") for m in cells)
        above = sum(one(f"SELECT count(*) FROM {level} WHERE {m} > 1") for m in cells)
        assert (below, above) == OUTSIDE[level, outcome], f"{level} {outcome}: {below:,} estimates below 0 and {above:,} above 1"
    # A standard error never comes without its estimate. 48 tract estimates have no standard error, and the
    # count of their race-gender cell is 0.
    cells = [m for m in measures if m.endswith("_p25")]
    assert sum(one(f"SELECT count(*) FROM {level} WHERE {m} IS NULL AND {m}_se IS NOT NULL") for m in cells) == 0, \
        f"{level}: a standard error without its estimate"
    no_se = [f"SELECT {m} AS estimate, {'_'.join(m.split('_')[1:3])}_count AS children FROM {level} WHERE {m} IS NOT NULL AND {m}_se IS NULL"
             for m in cells]
    assert one(f"SELECT count(*) FROM ({' UNION ALL '.join(no_se)})") == (48 if level == "tract" else 0), \
        f"{level}: estimates without a standard error are not the 48 known in the tracts"
    assert one(f"SELECT count(*) FROM ({' UNION ALL '.join(no_se)}) WHERE children IS DISTINCT FROM 0") == 0, \
        f"{level}: an estimate without a standard error whose cell count is not 0"

assert one("SELECT count(*) FROM tract WHERE NOT regexp_full_match(tract_fips, '[0-9]{11}')") == 0, "A tract_fips is not 11 digits"
assert one("SELECT count(DISTINCT state) FROM tract") == 52, "The tracts are not in 50 states, DC and Puerto Rico"
assert one("SELECT count(DISTINCT state) FROM county") == 52, "The counties are not in 50 states, DC and Puerto Rico"
# The commuting zones (1990 definitions) leave out Puerto Rico and Yakutat, Alaska (02282, a borough
# since 1992), whose one tract has no commuting zone either.
assert one("SELECT count(*) FROM tract WHERE cz IS NULL") == 726, "Not 726 tracts without a commuting zone"
assert one("SELECT count(*) FROM tract WHERE cz IS NULL AND state <> '72'") == 1, "Not one tract outside Puerto Rico without a CZ"
assert one("SELECT list(county_fips ORDER BY county_fips) FROM county WHERE cz IS NULL AND state <> '72'") == ["02282"], \
    "The counties outside Puerto Rico without a commuting zone are not just 02282"
assert one("SELECT count(*) FROM county WHERE state = '72'") == 78 and \
    one("SELECT count(*) FROM county WHERE state = '72' AND cz IS NOT NULL") == 0, "Puerto Rico's 78 municipios are not all without a CZ"

# Every tract and county lies in a commuting zone of the CZ table, under the same name.
for level in ("tract", "county"):
    assert one(f"SELECT count(*) FROM {level} t LEFT JOIN cz USING (cz) WHERE t.cz IS NOT NULL AND cz.czname IS DISTINCT FROM t.czname") == 0, \
        f"A {level}'s commuting zone is missing from the CZ table or named differently"
assert one("SELECT count(*) FROM tract t ANTI JOIN county c ON substr(t.tract_fips, 1, 5) = c.county_fips") == 0, \
    "A tract's county is not in the county table"
