# Crop Sequence Boundaries

Taking USDA crop boundaries and making a few useful views. DuckDB, Polars, and Parquet. Gosh this stuff is fast.

Currently working with the 2025 release, covering 2018-2025.

## Getting started

From this folder (`crop-sequence-boundaries`):

```sh
uv sync --locked
```

Use this project's `.venv` as your notebook kernel. Not the Anaconda base environment. Ask me how I know.

## The data

- Put the downloaded geodatabase at `in/CSB1825.gdb/`.
- [sandbox.ipynb](sandbox/sandbox.ipynb) explores the source and exports `out/national1825.parquet`.
- [example-querries.ipynb](sandbox/example-querries.ipynb) has sample queries, land-cover codes, and a look at the geometry.

The notebooks expect their working directory to be `sandbox/`. They use DuckDB's spatial extension; run `INSTALL spatial` once if `LOAD spatial` fails because it isn't installed.

## Land-cover lookup

Run from this folder:

```sh
uv run src/crop_sequence_boundaries/utils/extract_csb_land_cover_codes.py
```

Reads the USDA metadata page and writes `land_cover_code` and `land_cover_name` to:

- `out/land_cover_codes.csv`
- `useful-views/land_cover_codes.parquet`

Rerunning replaces both files. Both output folders are gitignored; generate them locally.

## A couple of notes

- `Shape` is geometry. Use `ST_AsText(Shape)` for WKT, or leave it out of table previews. GitHub's notebook render gets very wide, very fast.
- Keep the national data in Parquet. A giant geometry CSV is not particularly useful here.

## USDA links

- [Crop Sequence Boundaries](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/index.php)
- [2025 metadata and land-cover dictionary](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/metadata_Crop-Sequence-Boundaries-2025.htm)

