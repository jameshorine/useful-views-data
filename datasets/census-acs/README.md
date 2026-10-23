# Census ACS: shared views

Shared, documented views on the U.S. Census Bureau's American Community
Survey (ACS), 2020-2024 5-year estimates, built with
[useful-views](https://jameshorine.github.io/useful-views/). The point is
that every student's analysis starts from the same data and the same
cleaning. The data is downloaded from Census, Census's special values are
decoded one way, and the same geographies are used throughout. Each student
then adds their own recipes on top of these views.

No Census data is stored in git. You download it from Census with
`fetch_raw.py`, which checks every file against the SHA-256 recorded in
[SOURCES.md](SOURCES.md), and `useful-views sync` builds the views on your
machine.

## Quick start

From this folder (`datasets/census-acs`), with [uv](https://docs.astral.sh/uv/)
installed:

```sh
uv sync                      # installs the exact useful-views and polars versions in uv.lock
python fetch_raw.py          # downloads about 570 MB from Census into raw/ and checks it
uv run useful-views sync     # builds every view (about a minute)
uv run useful-views check    # expect: No problems found.
```

Run useful-views through `uv run`: the steps run with the same Python as
useful-views, and that is the one with polars installed. Plan for about
1.3 GB of disk: 570 MB of raw files, 700 MB of in-between files in `work/`,
and 42 MB of views.

## The shared views

All views are in `useful-views/`. The generated catalog,
[useful-views/README.md](useful-views/README.md), lists each one's columns
and the steps that made it.

| View | One row per | What it is |
|---|---|---|
| `acs5-2024-geographies` | geography | The 88,657 geographies the views cover: the nation, 52 states (with DC and Puerto Rico), 3,222 counties and 85,382 census tracts. `geo_id`, `name`, `level`, FIPS codes. |
| `acs5-2024-variables` | ACS variable | What every ACS variable means (28,437 of them, across all 1,199 tables), from the Census table shells: `variable` (such as `B19013_001`), `table_id`, `label`, `title`, `universe`. |
| `acs5-2024-b01003` | geography × variable | Total population |
| `acs5-2024-b01001` | geography × variable | Sex by age (49 variables) |
| `acs5-2024-b19013` | geography × variable | Median household income (2024 inflation-adjusted dollars) |
| `acs5-2024-b17001` | geography × variable | Poverty status by sex by age (59 variables) |
| `acs5-2024-b15003` | geography × variable | Educational attainment, population 25 and over (25 variables) |
| `acs5-2024-b25077` | geography × variable | Median value of owner-occupied housing units |

Every table view has the same columns: `geo_id`, `variable`, `estimate`,
`moe`, `estimate_note` and `moe_note`. `moe` is the margin of error at
Census's 90% confidence level. Join a table to the geographies on `geo_id`,
and to the variables on `variable`:

```python
import polars as pl

income = pl.read_parquet("useful-views/acs5-2024-b19013.parquet")
geos = pl.read_parquet("useful-views/acs5-2024-geographies.parquet")
counties = income.join(geos, on="geo_id").filter(pl.col("level") == "county")
```

### Notes: Census's special values

Census writes some estimates and margins of error as special numbers, such as
`-666666666`. Used as numbers, they would wreck any average. The views turn
them into a null, or a usable value, with a note, following Census's
[Notes on ACS Estimate and Annotation Values](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html):

| Column | Note | Census code | What it means | Value in the view |
|---|---|---|---|---|
| `estimate_note` | `insufficient-sample` | `-666666666` | Too few sample observations to compute the estimate. | `estimate` is null |
| `estimate_note` | `not-displayable` | `-999999999` | Too few sample cases in this geography. | `estimate` is null |
| `estimate_note` | `not-applicable` | `-888888888` | Not applicable or not available. | `estimate` is null |
| `estimate_note` | `median-upper-bound` | (varies) | The median is in the highest, open-ended interval: `250001` means "250,000 or more". | `estimate` is the bound |
| `estimate_note` | `median-lower-bound` | (varies) | The median is in the lowest, open-ended interval: `2499` means "under 2,500". | `estimate` is the bound |
| `moe_note` | `insufficient-sample` | `-222222222` | Too few sample observations to compute the margin of error. | `moe` is null |
| `moe_note` | `open-ended-median` | `-333333333` | The median is in an open-ended interval, so no margin of error. | `moe` is null |
| `moe_note` | `controlled` | `-555555555` | The estimate is controlled to an independent estimate and has no sampling error; Census says the margin of error "may be treated as zero". | `moe` is 0 |

A row with no notes is an ordinary estimate. The build fails if Census uses a
code that is not in this list.

## Adding your own analysis

1. Start a branch from the latest `dev`: `git switch dev && git pull && git switch -c feature/<you>-<topic>`.
2. Make a recipe: `uv run useful-views new-recipe <you>_<topic>`. In its
   `recipe.toml`, list the shared views you read as `inputs` (for example
   `useful-views/acs5-2024-b19013.parquet` and
   `useful-views/acs5-2024-geographies.parquet`) and your own views as
   `outputs`. Write its steps as `01_….py`, `02_….py`, each starting with a
   comment saying what it does.
3. Build and record: `uv run useful-views sync`, then
   `uv run useful-views cookbook`.
4. Commit your recipe folder with the regenerated `datapackage.json`,
   `useful-views/README.md` and `cookbook.json`, and open a pull request into
   `dev`.

Never edit `datapackage.json`, `useful-views/README.md` or `cookbook.json` by
hand, and never resolve a merge conflict in them by hand. Merge `dev` into
your branch, run `uv run useful-views sync` and `uv run useful-views cookbook`,
and commit what they write. Never commit anything from `raw/` or `work/`, or
any `.parquet` file: this project's `.gitignore` keeps them out.

### Changing the shared base

- **More geography levels** (places, ZCTAs, block groups): add the level to
  `LEVELS` and its count to `EXPECTED` in
  `recipes/acs_geographies/01_keep_levels.py`, then run
  `uv run useful-views sync --all`.
- **More tables:** add the table file to `fetch_raw.py` and
  [SOURCES.md](SOURCES.md) with its size and SHA-256. Add its raw file and
  view to `recipes/acs_tables/recipe.toml`, and its ID to `TABLES` in
  `recipes/acs_tables/01_reshape_long.py`. Then run `uv run useful-views sync`.

Change the shared base in its own pull request, so everyone's work moves to
it together.

## Known issues in the source data

- **Suffolk County, New York: 14 census tracts are missing.** Census found a
  data collection error in the Wyandanch and Brentwood CDPs and suppressed
  them, and every geography nested in them, from the 2019-2023 and 2020-2024
  5-year data ([ACS Errata Note 148](https://www.census.gov/programs-surveys/acs/technical-documentation/errata/148.html)).
  The 14 tracts are not in Census's files, so they are not in these views.
  The county, state and national totals still include those people, so
  Suffolk's tracts sum to 77,579 fewer people than the county. Everywhere
  else, tracts sum to their county and counties to their state.
- **Medians are not additive.** Never sum or average `B19013` or `B25077`
  across geographies. An open-ended median (see the notes above) is a bound,
  not a point value.

## Sources and credit

U.S. Census Bureau, 2020-2024 American Community Survey 5-Year Estimates,
table-based Summary File. The files, their URLs and checksums are in
[SOURCES.md](SOURCES.md). This project is not affiliated with or endorsed by
the U.S. Census Bureau.
