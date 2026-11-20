import hashlib

import polars as pl

# The tables this recipe makes. To add one, add its ID here, and its raw file
# and view to recipe.toml, then run `useful-views sync`.
TABLES = ["b01003", "b01001", "b19013", "b17001", "b15003", "b25077"]

# Each table file's SHA-256, as in fetch_raw.py and SOURCES.md.
SHA256 = {
    "b01003": "38d1a992bb058d184009b10b9b34987279aee575e4323165cfb5706c69b6ca90",
    "b01001": "1637b18a96881b81e050df1cd3d5ac38a33208b9b69b40e1dbeb3c4e13718f0e",
    "b19013": "b25a176b0e6c339b6f3a2a0d3d8446bf06f5f080b4395993ec9a8313efb1c229",
    "b17001": "707adda8aaff136382f4fe0858617d09062da48b1a3d2ab2e9a1047def09b531",
    "b15003": "d0c8609e958022459215c8a31d7452ef7528ee8dd70fbb6f9a99de0f491f42d7",
    "b25077": "89eb2153764a2330b23959d8bbc29b3a8f3016f087b990f2a8ea0d5096d9a816",
}


def check_sha256(path: str, expected: str) -> None:
    """Stop if a raw file is not the one fetch_raw.py and SOURCES.md record."""
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    assert digest.hexdigest() == expected, f"{path} is not the file SOURCES.md records. Run fetch_raw.py."

# B19013_E001 -> B19013_001 (estimate), B19013_M001 -> B19013_001 (margin of error)
VARIABLE = r"^(.+)_[EM](\d{3})$"


def long(table: pl.DataFrame, kind: str, name: str) -> pl.DataFrame:
    columns = [c for c in table.columns if c != "GEO_ID" and c.split("_")[-1].startswith(kind)]
    return table.unpivot(index="GEO_ID", on=columns, variable_name="variable", value_name=name).with_columns(
        pl.col("variable").str.replace(VARIABLE, "${1}_${2}")
    )


for name in TABLES:
    check_sha256(f"raw/acsdt5y2024-{name}.dat", SHA256[name])
    table = pl.read_csv(f"raw/acsdt5y2024-{name}.dat", separator="|", infer_schema=False)
    estimates = long(table, "E", "estimate_raw")
    moes = long(table, "M", "moe_raw")
    both = estimates.join(moes, on=["GEO_ID", "variable"], how="full", coalesce=True, validate="1:1")
    assert both.height == estimates.height == moes.height, f"{name}: estimates and margins of error do not pair up"
    both.rename({"GEO_ID": "geo_id"}).write_parquet(f"work/acs_tables/{name}_long.parquet")
