# Keep the whole-area rows (geographic component 00) of the nation, states,
# counties and census tracts from the Census geography file, with each
# geography's name, level and FIPS codes.
import polars as pl

# The geography levels the shared views cover: Census summary level -> name.
# This is the one place they are listed. To add one, add it here with its
# expected count below, then run `useful-views sync --all`. Common choices:
# "160": "place", "860": "zcta", "150": "block group".
LEVELS = {"010": "nation", "040": "state", "050": "county", "140": "tract"}
EXPECTED = {"nation": 1, "state": 52, "county": 3222, "tract": 85382}  # 2020-2024 release

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
