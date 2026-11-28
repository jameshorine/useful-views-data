import hashlib
import re

import duckdb

CSV = "raw/national_percentile_outcomes.csv"
SHA256 = "058d0065412855c72899af390ebe9348e79cd0eeeee6d2f9d639db6512b7c873"  # as in fetch_raw.py and sources.toml
OUT = "useful-views/national-outcomes.parquet"

digest = hashlib.sha256()
with open(CSV, "rb") as file:
    for chunk in iter(lambda: file.read(1 << 20), b""):
        digest.update(chunk)
if digest.hexdigest() != SHA256:  # not an assert: python -O would skip it
    raise SystemExit(f"{CSV} is not the pinned download (its SHA-256 is {digest.hexdigest()}). Run fetch_raw.py.")

RACES = ("pooled", "white", "black", "hisp", "asian", "natam", "other")
GENDERS = ("pooled", "female", "male")
COLUMN = re.compile(rf"(s_|imp_)?(.+)_({'|'.join(RACES)})_({'|'.join(GENDERS)})(_n)?")
FIT = "CASE {0} WHEN -9 THEN 'monotonic' WHEN 0 THEN 'non-monotonic, kept' WHEN 1 THEN 'non-monotonic, pooled fit used' END"

con = duckdb.connect()
con.execute(f"CREATE TABLE csv AS SELECT * FROM read_csv('{CSV}', header = true, all_varchar = true)")
header = [r[0] for r in con.execute("SELECT column_name FROM (DESCRIBE csv)").fetchall()]
assert header[0] == "par_pctile", f"The first column is {header[0]}, not par_pctile"

cells = []  # (outcome, race, gender) with an estimate column
for name in header[1:]:
    match = COLUMN.fullmatch(name)
    assert match, f"{name} does not follow the codebook's column pattern"
    prefix, outcome, race, gender, n = match.groups()
    if outcome != "count" and not prefix and not n:
        cells.append((outcome, race, gender))
for outcome, race, gender in cells:  # each estimate has its count, LOWESS fit and fit flag
    base = f"{outcome}_{race}_{gender}"
    assert {f"{base}_n", f"s_{base}", f"imp_{base}"} <= set(header), f"{base} lacks its _n, s_ or imp_ column"
    assert f"count_{race}_{gender}" in header, f"count_{race}_{gender} is missing"
assert len(cells) * 4 + 21 + 1 == len(header), "Columns beyond the estimates, their companions and the 21 sample counts"

parts = [
    f"SELECT CAST(par_pctile AS INTEGER) AS parent_percentile, '{o}' AS outcome, '{r}' AS race, '{g}' AS gender, "
    f"CAST({o}_{r}_{g} AS DOUBLE) AS estimate, CAST(s_{o}_{r}_{g} AS DOUBLE) AS lowess, "
    f"CAST({o}_{r}_{g}_n AS BIGINT) AS children, CAST(imp_{o}_{r}_{g} AS INTEGER) AS lowess_flag, "
    f"{FIT.format(f'CAST(imp_{o}_{r}_{g} AS INTEGER)')} AS lowess_fit, "
    f"CAST(count_{r}_{g} AS BIGINT) AS sample_children FROM csv"
    for o, r, g in cells
]
con.execute(f"COPY (SELECT * FROM ({' UNION ALL '.join(parts)}) ORDER BY outcome, race, gender, parent_percentile) "
            f"TO '{OUT}' (FORMAT PARQUET, COMPRESSION ZSTD)")
con.execute(f"CREATE VIEW v AS SELECT * FROM '{OUT}'")
one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731

facts = {
    "rows": one("SELECT count(*) FROM v"),
    "outcomes": one("SELECT count(DISTINCT outcome) FROM v"),
    "race-gender cells": one("SELECT count(DISTINCT (race, gender)) FROM v"),
    "percentiles": one("SELECT count(DISTINCT parent_percentile) FROM v"),
    "no estimate": one("SELECT count(*) FROM v WHERE estimate IS NULL"),
}
assert facts == {"rows": 97_300, "outcomes": 47, "race-gender cells": 21, "percentiles": 100, "no estimate": 3_227}, \
    f"Known facts differ: {facts}"
assert one("SELECT min(parent_percentile) FROM v") == 1 and one("SELECT max(parent_percentile) FROM v") == 100, "Not percentiles 1 to 100"
assert one("SELECT count(*) FROM (SELECT outcome, race, gender, parent_percentile FROM v GROUP BY ALL HAVING count(*) > 1)") == 0, \
    "The key (outcome, race, gender, parent_percentile) is not unique"
# Teen births are reported for women only; every other outcome for all 21 race-gender cells.
assert one("SELECT list(DISTINCT gender) FROM v WHERE outcome = 'teenbrth'") == ["female"], "teenbrth is not for women only"
# An estimate and its count are missing together; the LOWESS fit and its flag are always given.
assert one("SELECT count(*) FROM v WHERE (estimate IS NULL) <> (children IS NULL)") == 0, "An estimate and its count disagree"
assert one("SELECT count(*) FROM v WHERE lowess IS NULL OR lowess_fit IS NULL OR sample_children IS NULL") == 0, \
    "A missing LOWESS fit, fit flag or sample count"
