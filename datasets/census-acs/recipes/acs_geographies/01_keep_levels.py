import hashlib

import polars as pl

# The geography levels the shared views cover: Census summary level -> name.
# This is the one place the code lists them. To add one, add it here with its
# expected count below, name it in the descriptions in
# recipes/acs_geographies/recipe.toml, then run `useful-views sync --all`.
# Common choices: "160": "place", "860": "zcta", "150": "block group".
LEVELS = {"010": "nation", "040": "state", "050": "county", "140": "tract"}
EXPECTED = {"nation": 1, "state": 52, "county": 3222, "tract": 85382}  # 2020-2024 release


def check_sha256(path: str, expected: str) -> None:
    """Stop if a raw file is not the one fetch_raw.py and SOURCES.md record."""
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    assert digest.hexdigest() == expected, f"{path} is not the file SOURCES.md records. Run fetch_raw.py."


check_sha256("raw/Geos20245YR.txt", "b87a1d1a4db9f826d0d133d20cbf7d011932f9ec2cfa74eacf8c9cf387aea344")
geos = pl.read_csv("raw/Geos20245YR.txt", separator="|", infer_schema=False)
view = (
    geos.filter(pl.col("SUMLEVEL").is_in(list(LEVELS)) & (pl.col("COMPONENT") == "00"))
    .select(
        pl.col("GEO_ID").alias("geo_id"),
        pl.col("NAME").alias("name"),
        pl.col("SUMLEVEL").replace_strict(LEVELS).alias("level"),
        pl.col("SUMLEVEL").alias("sumlevel"),
        pl.col("STUSAB").alias("stusab"),
        pl.col("STATE").alias("state"),
        pl.col("COUNTY").alias("county"),
        pl.col("TRACT").alias("tract"),
    )
    .sort("sumlevel", "geo_id")
)

counts = dict(view.group_by("level").len().iter_rows())
assert counts == EXPECTED, f"Geography counts {counts} differ from {EXPECTED}"
assert view["geo_id"].is_unique().all(), "GEO_ID is not unique"
view.write_parquet("useful-views/acs5-2024-geographies.parquet")
