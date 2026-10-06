# Crop Sequence Boundaries

Taking USDA crop boundaries and making a few useful views. DuckDB, Polars, and Parquet. Gosh this stuff is fast.

Currently working with the 2025 release (rev23), covering 2018-2025. Where every input came from, with checksums, is in [in/SOURCES.md](in/SOURCES.md).

## Getting started

From this folder (`crop-sequence-boundaries`):

```sh
uv sync --locked
```

Use this project's `.venv` as your notebook kernel. Not the Anaconda base environment. Ask me how I know.

## The data

- Download the zip listed in [in/SOURCES.md](in/SOURCES.md) and unzip `CSB1825.gdb/` to `in/CSB1825.gdb/`. The metadata file from the zip is already committed as `in/csb_2025_metadata.htm`.
- [sandbox.ipynb](sandbox/sandbox.ipynb) explores the source.
- [example-querries.ipynb](sandbox/example-querries.ipynb) has sample queries, land-cover codes, and a look at the geometry.

The notebooks expect their working directory to be `sandbox/`. They use DuckDB's spatial extension; run `INSTALL spatial` once if `LOAD spatial` fails because it isn't installed.

Scripts resolve their paths from the project, so they can be run from any folder. Paths and the expected input facts live in [config.py](src/crop_sequence_boundaries/config.py).

## National export

```sh
uv run src/crop_sequence_boundaries/utils/export_national.py
```

Converts the `national1825` layer to GeoParquet at `out/national1825.parquet`, then checks the feature count, state count and CRS against `in/SOURCES.md`. It won't overwrite an existing file; pass `--force` to replace it.

## Land-cover lookup

```sh
uv run src/crop_sequence_boundaries/utils/extract_csb_land_cover_codes.py
```

Reads `in/csb_2025_metadata.htm` (checked against its SHA256) and writes `land_cover_code` and `land_cover_name` to:

- `out/land_cover_codes.csv`
- `useful-views/land_cover_codes.parquet`

Rerunning replaces both files. Both output folders are gitignored; generate them locally.

## A couple of notes

- `Shape` is geometry. Use `ST_AsText(Shape)` for WKT, or leave it out of table previews. GitHub's notebook render gets very wide, very fast.
- Keep the national data in Parquet. A giant geometry CSV is not particularly useful here.

## USDA links

- [Crop Sequence Boundaries](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/index.php)
- [2025 metadata and land-cover dictionary](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/metadata_Crop-Sequence-Boundaries-2025.htm) (the live page; its feature count differs from the data, see [in/SOURCES.md](in/SOURCES.md#known-discrepancy-the-live-metadata-page))

