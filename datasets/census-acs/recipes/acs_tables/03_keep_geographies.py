# Keep only the geographies in the shared geographies view, check that every
# one of them has every variable exactly once, and write one view per table.
from pathlib import Path

import polars as pl

geographies = pl.read_parquet("useful-views/acs5-2024-geographies.parquet").select("geo_id")

for path in sorted(Path("work/acs_tables").glob("*_decoded.parquet")):
    name = path.name.removesuffix("_decoded.parquet")
    table = pl.read_parquet(path).join(geographies, on="geo_id", how="semi").sort("geo_id", "variable")
    variables = table["variable"].n_unique()
    assert table["geo_id"].n_unique() == geographies.height, f"{name}: a shared geography is missing"
    assert table.height == geographies.height * variables, f"{name}: not one row per geography and variable"
    assert table.select("geo_id", "variable").is_unique().all(), f"{name}: a geography and variable appear twice"
    table.write_parquet(f"useful-views/acs5-2024-{name}.parquet")
