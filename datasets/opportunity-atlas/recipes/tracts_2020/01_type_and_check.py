import hashlib

import duckdb

CSV = "raw/us_tract_2010_2020_crosswalk.csv"
SHA256 = "fe0f029d60bcfa2964faf4503438167f72b20124b8cfa26ebea3f9296fb0fbcb"  # as in fetch_raw.py and sources.toml
TRACTS = "useful-views/tracts-2020.parquet"
PAIRS = "useful-views/tracts-2020-to-2010.parquet"
OUTCOMES = "useful-views/tract-outcomes.parquet"

digest = hashlib.sha256()
with open(CSV, "rb") as file:
    for chunk in iter(lambda: file.read(1 << 20), b""):
        digest.update(chunk)
if digest.hexdigest() != SHA256:  # not an assert: python -O would skip it
    raise SystemExit(f"{CSV} is not the pinned download (its SHA-256 is {digest.hexdigest()}). Run fetch_raw.py.")

RANKS = range(1, 6)
HEADER = ["tract_2020"] + [f"{c}_{i}" for i in RANKS for c in ("tract_2010", "wgt", "kfr")] + ["kfr_largest_tract", "kfr_weighted"]
con = duckdb.connect()
con.execute(f"CREATE VIEW csv AS SELECT * FROM read_csv('{CSV}', header = true, all_varchar = true)")
header = [r[0] for r in con.execute("SELECT column_name FROM (DESCRIBE csv)").fetchall()]
assert header == HEADER, f"The CSV's columns differ from the ReadMe's: {header}"

listed = " + ".join(f"(tract_2010_{i} IS NOT NULL)::INTEGER" for i in RANKS)
con.execute(f"""COPY (
    SELECT tract_2020, substr(tract_2020, 1, 2) AS state, substr(tract_2020, 1, 5) AS county_fips,
           CAST(kfr_weighted AS DOUBLE) AS kfr_weighted, CAST(kfr_largest_tract AS DOUBLE) AS kfr_largest_tract,
           CAST({listed} AS INTEGER) AS tracts_2010
    FROM csv ORDER BY tract_2020
) TO '{TRACTS}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
pairs = " UNION ALL ".join(
    f"SELECT tract_2020, {i} AS overlap_rank, tract_2010_{i} AS tract_2010, CAST(wgt_{i} AS DOUBLE) AS overlap_weight, "
    f"CAST(kfr_{i} AS DOUBLE) AS kfr_2010 FROM csv WHERE tract_2010_{i} IS NOT NULL"
    for i in RANKS
)
con.execute(f"COPY (SELECT * FROM ({pairs}) ORDER BY tract_2020, overlap_rank) TO '{PAIRS}' (FORMAT PARQUET, COMPRESSION ZSTD)")

con.execute(f"CREATE VIEW t AS SELECT * FROM '{TRACTS}'")
con.execute(f"CREATE VIEW p AS SELECT * FROM '{PAIRS}'")
one = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731

facts = {
    "2020 tracts": one("SELECT count(*) FROM t"),
    "pairs": one("SELECT count(*) FROM p"),
    "distinct 2010 tracts": one("SELECT count(DISTINCT tract_2010) FROM p"),
    "states (with DC)": one("SELECT count(DISTINCT state) FROM t"),
    "no mobility": one("SELECT count(*) FROM t WHERE kfr_weighted IS NULL"),
    "by tracts listed": one("SELECT list(n ORDER BY k) FROM (SELECT tracts_2010 AS k, count(*) AS n FROM t GROUP BY k)"),
}
expected = {"2020 tracts": 84_095, "pairs": 121_433, "distinct 2010 tracts": 72_760, "states (with DC)": 51,
            "no mobility": 791, "by tracts listed": [57_561, 18_739, 5_493, 1_595, 707]}
assert facts == expected, f"Known facts differ: {facts}"
assert one("SELECT count(DISTINCT tract_2020) FROM t") == facts["2020 tracts"], "tract_2020 is not unique"
assert one("SELECT count(*) FROM t WHERE NOT regexp_full_match(tract_2020, '[0-9]{11}')") == 0, "A tract_2020 is not 11 digits"
assert one("SELECT count(*) FROM p WHERE NOT regexp_full_match(tract_2010, '[0-9]{11}')") == 0, "A tract_2010 is not 11 digits"
assert one("SELECT count(*) FROM (SELECT tract_2020, tract_2010 FROM p GROUP BY ALL HAVING count(*) > 1)") == 0, \
    "A 2010 tract is listed twice for one 2020 tract"
# The listed tracts fill ranks 1, 2, ... without gaps, from the largest overlap down.
assert one("SELECT count(*) FROM (SELECT tract_2020, max(overlap_rank) AS top, count(*) AS n FROM p GROUP BY ALL) WHERE top <> n") == 0, \
    "A gap in a 2020 tract's overlap ranks"
assert one("SELECT count(*) FROM (SELECT overlap_weight - lag(overlap_weight) OVER (PARTITION BY tract_2020 ORDER BY overlap_rank) AS step FROM p) WHERE step > 0") == 0, \
    "Overlap weights do not fall with rank"
assert one("SELECT count(*) FROM p WHERE overlap_weight IS NULL OR overlap_weight <= 0 OR overlap_weight > 1") == 0, \
    "An overlap weight outside (0, 1]"
# kfr_largest_tract is the largest overlap's kfr, and kfr_weighted is missing exactly when it is.
assert one("SELECT count(*) FROM t JOIN p USING (tract_2020) WHERE overlap_rank = 1 AND kfr_largest_tract IS DISTINCT FROM kfr_2010") == 0, \
    "kfr_largest_tract is not the kfr of the largest overlap"
assert one("SELECT count(*) FROM t WHERE (kfr_weighted IS NULL) <> (kfr_largest_tract IS NULL)") == 0, \
    "kfr_weighted and kfr_largest_tract are not missing together"
assert one("SELECT count(*) FROM t WHERE tracts_2010 = 1 AND kfr_weighted IS DISTINCT FROM kfr_largest_tract") == 0, \
    "A 2020 tract with one 2010 tract whose two estimates differ"
# Each listed 2010 tract's kfr is its kfr_pooled_pooled_p25 in tract-outcomes (some listed tracts aren't there).
assert one(f"SELECT count(*) FROM p JOIN '{OUTCOMES}' o ON p.tract_2010 = o.tract_fips WHERE p.kfr_2010 IS DISTINCT FROM o.kfr_pooled_pooled_p25") == 0, \
    "A kfr_2010 differs from the tract's kfr_pooled_pooled_p25 in tract-outcomes"
assert one(f"SELECT count(*) FROM p WHERE kfr_2010 IS NOT NULL AND tract_2010 NOT IN (SELECT tract_fips FROM '{OUTCOMES}')") == 0, \
    "A kfr_2010 for a tract that is not in tract-outcomes"
# kfr_weighted is the overlap-weighted mean of the listed kfr values, renormalized over those given, except in
# 443 tracts where the ReadMe's method can't be reproduced from the five tracts listed (see the README).
off = one("""SELECT count(*) FROM t JOIN (
        SELECT tract_2020, sum(overlap_weight * kfr_2010) / sum(overlap_weight) FILTER (WHERE kfr_2010 IS NOT NULL) AS mean
        FROM p GROUP BY tract_2020) USING (tract_2020)
    WHERE abs(mean - kfr_weighted) > 1e-6""")
assert off == 443, f"{off} tracts whose kfr_weighted is not the renormalized weighted mean, not 443"
