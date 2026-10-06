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

## Building the views

Run every step in order:

```sh
uv run crop-sequence-boundaries
```

Each step refuses to overwrite its outputs; pass `--force` to rebuild. Every step can also be run on its own, e.g. `uv run python -m crop_sequence_boundaries.step2_land_cover_codes`. Scripts resolve their paths from the project, so they work from any folder. Paths, the release name and the expected input facts all live in [config.py](src/crop_sequence_boundaries/config.py).

| Step | Script | Reads | Writes |
|---|---|---|---|
| 1 | [step1_export_national.py](src/crop_sequence_boundaries/step1_export_national.py) | `in/CSB1825.gdb` | `out/national1825.parquet` |
| 2 | [step2_land_cover_codes.py](src/crop_sequence_boundaries/step2_land_cover_codes.py) | `in/csb_2025_metadata.htm` | `useful-views/csb_2025/land_cover_codes.parquet`, `out/land_cover_codes.csv` |
| 3 | [step3_tidy_views.py](src/crop_sequence_boundaries/step3_tidy_views.py) | steps 1 and 2 | `useful-views/csb_2025/csb_field_year.parquet`, `csb_field.parquet`, `county.parquet` |

Each step checks its result: step 1 the feature count, state count and CRS against `in/SOURCES.md`; step 2 the metadata file's SHA256; step 3 row counts, unique keys, and that every code and county joins. `out/` and `useful-views/` are gitignored; generate them locally.

## The views

All in `useful-views/csb_2025/`. Field IDs are specific to this release; see [in/SOURCES.md](in/SOURCES.md).

| View | One row per | Key | Columns |
|---|---|---|---|
| `csb_field_year` | field × year | `csb_id`, `year` | `land_cover_code` |
| `csb_field` | field | `csb_id` | `county_geoid`, `csb_acres`, `inside_x`, `inside_y`, `geometry` (EPSG:5070) |
| `county` | county | `county_geoid` | `state_fips`, `county_fips`, `county_name`, `asd_code` |
| `land_cover_codes` | land-cover code | `land_cover_code` | `land_cover_name` |

## A couple of notes

- `Shape` is geometry. Use `ST_AsText(Shape)` for WKT, or leave it out of table previews. GitHub's notebook render gets very wide, very fast.
- Keep the national data in Parquet. A giant geometry CSV is not particularly useful here.

## USDA links

- [Crop Sequence Boundaries](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/index.php)
- [2025 metadata and land-cover dictionary](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/metadata_Crop-Sequence-Boundaries-2025.htm) (the live page; its feature count differs from the data, see [in/SOURCES.md](in/SOURCES.md#known-discrepancy-the-live-metadata-page))

