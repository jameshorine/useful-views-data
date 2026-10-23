# Turn Census's special values (such as -666666666) into nulls with a note,
# following Census's "Notes on ACS Estimate and Annotation Values", and make
# every estimate and margin of error a number.
from pathlib import Path

import polars as pl

# https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html
ESTIMATE_CODES = {
    "-666666666": "insufficient-sample",  # "-": too few sample observations to compute the estimate
    "-999999999": "not-displayable",  # "N": too few sample cases in this geographic area
    "-888888888": "not-applicable",  # "(X)": not applicable or not available
}
MOE_CODES = {
    "-222222222": "insufficient-sample",  # "**": too few sample observations to compute the margin of error
    "-333333333": "open-ended-median",  # "***": the median is in an open-ended interval
    "-555555555": "controlled",  # "*****": controlled estimate, no sampling error; Census: "may be treated as zero"
    "-999999999": "not-displayable",
    "-888888888": "not-applicable",
}


def decode(raw: pl.Expr, codes: dict[str, str]) -> tuple[pl.Expr, pl.Expr]:
    is_code = raw.is_in(list(codes))
    value = pl.when(is_code | raw.is_null()).then(None).otherwise(raw).cast(pl.Float64)
    note = pl.when(raw.is_null()).then(pl.lit("no-data")).otherwise(raw.replace_strict(codes, default=None))
    return value, note


for path in sorted(Path("work/acs_tables").glob("*_long.parquet")):
    table = pl.read_parquet(path)
    unknown = table.filter(
        (pl.col("estimate_raw").str.starts_with("-") & ~pl.col("estimate_raw").is_in(list(ESTIMATE_CODES)))
        | (pl.col("moe_raw").str.starts_with("-") & ~pl.col("moe_raw").is_in(list(MOE_CODES)))
    )
    assert unknown.is_empty(), f"{path.name}: special values not in Census's list: {unknown.head(5).rows()}"

    estimate, estimate_note = decode(pl.col("estimate_raw"), ESTIMATE_CODES)
    moe, moe_note = decode(pl.col("moe_raw"), MOE_CODES)
    decoded = table.with_columns(estimate=estimate, estimate_note=estimate_note, moe=moe, moe_note=moe_note)

    # A controlled estimate has no sampling error: Census says its margin of error may be treated as zero.
    # An open-ended median is a bound, not a point: 250001 means "250,000 or more", 2499 means "under 2,500".
    open_ended = pl.col("moe_note") == "open-ended-median"
    decoded = decoded.with_columns(
        moe=pl.when(pl.col("moe_note") == "controlled").then(0.0).otherwise(pl.col("moe")),
        estimate_note=pl.when(open_ended & pl.col("estimate_raw").str.ends_with("1")).then(pl.lit("median-upper-bound"))
        .when(open_ended & pl.col("estimate_raw").str.ends_with("9")).then(pl.lit("median-lower-bound"))
        .otherwise(pl.col("estimate_note")),
    )
    bounds = decoded.filter(open_ended & pl.col("estimate").is_not_null())
    assert bounds["estimate_note"].is_in(["median-upper-bound", "median-lower-bound"]).all(), (
        f"{path.name}: an open-ended median that is neither an upper nor a lower bound"
    )
    assert (decoded["estimate"].drop_nulls() >= 0).all() and (decoded["moe"].drop_nulls() >= 0).all(), (
        f"{path.name}: a negative value survived decoding"
    )
    decoded.select("geo_id", "variable", "estimate", "moe", "estimate_note", "moe_note").write_parquet(
        path.with_name(path.name.replace("_long", "_decoded"))
    )
