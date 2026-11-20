import hashlib

import polars as pl


def check_sha256(path: str, expected: str) -> None:
    """Stop if a raw file is not the one fetch_raw.py and SOURCES.md record (the same SHA-256 is in all three)."""
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected:  # not an assert: python -O would skip it
        raise SystemExit(
            f"{path} is not the file this project records (its SHA-256 is {actual}). "
            "Run fetch_raw.py, or if Census replaced the file, see SOURCES.md."
        )


check_sha256("raw/ACS20245YR_Table_Shells.txt", "5b46f4af873744a415c4974204010db976e2a61ff916674732f81c496a6b517d")
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
