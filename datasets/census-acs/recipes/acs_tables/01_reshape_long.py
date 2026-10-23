# Reshape each ACS table file (one column per estimate and per margin of error)
# into one row per geography and variable, with the estimate and margin of
# error side by side, still as Census wrote them.
import polars as pl

# The tables this recipe makes. To add one, add its ID here, and its raw file
# and view to recipe.toml, then run `useful-views sync`.
TABLES = ["b01003", "b01001", "b19013", "b17001", "b15003", "b25077"]

# B19013_E001 -> B19013_001 (estimate), B19013_M001 -> B19013_001 (margin of error)
VARIABLE = r"^(.+)_[EM](\d{3})$"


def long(table: pl.DataFrame, kind: str, name: str) -> pl.DataFrame:
    columns = [c for c in table.columns if c != "GEO_ID" and c.split("_")[-1].startswith(kind)]
    return table.unpivot(index="GEO_ID", on=columns, variable_name="variable", value_name=name).with_columns(
        pl.col("variable").str.replace(VARIABLE, "${1}_${2}")
    )


for name in TABLES:
    table = pl.read_csv(f"raw/acsdt5y2024-{name}.dat", separator="|", infer_schema=False)
    estimates = long(table, "E", "estimate_raw")
    moes = long(table, "M", "moe_raw")
    both = estimates.join(moes, on=["GEO_ID", "variable"], how="full", coalesce=True, validate="1:1")
    assert both.height == estimates.height == moes.height, f"{name}: estimates and margins of error do not pair up"
    both.rename({"GEO_ID": "geo_id"}).write_parquet(f"work/acs_tables/{name}_long.parquet")
