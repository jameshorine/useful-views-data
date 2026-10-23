# Keep one row per ACS variable (such as B19013_001) from the Census table
# shells, with its table, position, label, title, universe and type, and drop
# the heading rows that have no variable.
import polars as pl

shells = pl.read_csv("raw/ACS20245YR_Table_Shells.txt", separator="|", infer_schema=False)
variables = shells.filter(pl.col("Unique ID").is_not_null())
assert variables["Line"].str.ends_with(".0").all(), "A variable has a fractional line number"
view = (
    variables.select(
        pl.col("Unique ID").alias("variable"),
        pl.col("Table ID").alias("table_id"),
        pl.col("Line").cast(pl.Float64).cast(pl.Int32).alias("line"),
        pl.col("Indent").cast(pl.Int8).alias("indent"),
        pl.col("Label").alias("label"),
        pl.col("Title").alias("title"),
        pl.col("Universe").alias("universe"),
        pl.col("Type").alias("type"),
    )
    .sort("table_id", "line")
)

assert view["variable"].is_unique().all(), "A variable appears twice in the table shells"
assert view["variable"].str.contains(r"^[A-Z0-9]+_\d{3}$").all(), "Unexpected variable ID"
view.write_parquet("useful-views/acs5-2024-variables.parquet")
