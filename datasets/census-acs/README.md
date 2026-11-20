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
machine. Each recipe checks the files it reads again before reading them.

## Quick start

From this folder (`datasets/census-acs`), with [uv](https://docs.astral.sh/uv/)
installed:

```sh
uv sync                      # installs the exact useful-views and polars versions in uv.lock
uv run python fetch_raw.py   # downloads about 570 MB from Census into raw/ and checks it
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

### Sample records

Real rows from the 2020-2024 release. Run the setup once, then each snippet,
from this folder: you get the same output. The comments say why each row was
picked. When the data changes, re-run the snippets and paste the new output
here.

```python
import polars as pl

pl.Config.set_tbl_hide_dataframe_shape(True)
pl.Config.set_fmt_str_lengths(100)
pl.Config.set_tbl_width_chars(200)
pl.Config.set_fmt_float("full")
```

**`acs5-2024-geographies`**: one geography at each level.

```python
geos = pl.read_parquet("useful-views/acs5-2024-geographies.parquet")
print(geos.filter(pl.col("geo_id").is_in([
    "0100000US",             # the nation
    "0400000US17",           # a state: Illinois
    "0500000US17019",        # a county: Champaign
    "1400000US17019000200",  # a tract: its geo_id holds the state, county and tract codes
])))
```

```text
┌──────────────────────┬────────────────────────────────────────────┬────────┬──────────┬────────┬───────┬────────┬────────┐
│ geo_id               ┆ name                                       ┆ level  ┆ sumlevel ┆ stusab ┆ state ┆ county ┆ tract  │
│ ---                  ┆ ---                                        ┆ ---    ┆ ---      ┆ ---    ┆ ---   ┆ ---    ┆ ---    │
│ str                  ┆ str                                        ┆ str    ┆ str      ┆ str    ┆ str   ┆ str    ┆ str    │
╞══════════════════════╪════════════════════════════════════════════╪════════╪══════════╪════════╪═══════╪════════╪════════╡
│ 0100000US            ┆ United States                              ┆ nation ┆ 010      ┆ US     ┆ null  ┆ null   ┆ null   │
│ 0400000US17          ┆ Illinois                                   ┆ state  ┆ 040      ┆ IL     ┆ 17    ┆ null   ┆ null   │
│ 0500000US17019       ┆ Champaign County, Illinois                 ┆ county ┆ 050      ┆ IL     ┆ 17    ┆ 019    ┆ null   │
│ 1400000US17019000200 ┆ Census Tract 2, Champaign County, Illinois ┆ tract  ┆ 140      ┆ IL     ┆ 17    ┆ 019    ┆ 000200 │
└──────────────────────┴────────────────────────────────────────────┴────────┴──────────┴────────┴───────┴────────┴────────┘
```

**`acs5-2024-variables`**: what a variable means: its line in the table (`label`) and who it counts (`universe`).

```python
variables = pl.read_parquet("useful-views/acs5-2024-variables.parquet")
print(variables.filter(pl.col("variable").is_in(["B17001_001", "B17001_002", "B19013_001"]))
      .select("variable", "label", "universe"))
```

```text
┌────────────┬────────────────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────┐
│ variable   ┆ label                                                                              ┆ universe                                         │
│ ---        ┆ ---                                                                                ┆ ---                                              │
│ str        ┆ str                                                                                ┆ str                                              │
╞════════════╪════════════════════════════════════════════════════════════════════════════════════╪══════════════════════════════════════════════════╡
│ B17001_001 ┆ Total:                                                                             ┆ Population for whom poverty status is determined │
│ B17001_002 ┆ Income in the past 12 months below poverty level:                                  ┆ Population for whom poverty status is determined │
│ B19013_001 ┆ Median household income in the past 12 months (in 2024 inflation-adjusted dollars) ┆ Households                                       │
└────────────┴────────────────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────┘
```

**`acs5-2024-b01003`**: total population.

```python
population = pl.read_parquet("useful-views/acs5-2024-b01003.parquet")
print(population.filter(pl.col("geo_id").is_in([
    "0400000US17",           # state and county totals are controlled: margin of error 0
    "0500000US17019",
    "1400000US17019000200",  # a tract has an ordinary margin of error
])))
```

```text
┌──────────────────────┬────────────┬──────────┬─────┬───────────────┬────────────┐
│ geo_id               ┆ variable   ┆ estimate ┆ moe ┆ estimate_note ┆ moe_note   │
│ ---                  ┆ ---        ┆ ---      ┆ --- ┆ ---           ┆ ---        │
│ str                  ┆ str        ┆ f64      ┆ f64 ┆ str           ┆ str        │
╞══════════════════════╪════════════╪══════════╪═════╪═══════════════╪════════════╡
│ 0400000US17          ┆ B01003_001 ┆ 12694798 ┆ 0   ┆ null          ┆ controlled │
│ 0500000US17019       ┆ B01003_001 ┆ 208741   ┆ 0   ┆ null          ┆ controlled │
│ 1400000US17019000200 ┆ B01003_001 ┆ 2047     ┆ 442 ┆ null          ┆ null       │
└──────────────────────┴────────────┴──────────┴─────┴───────────────┴────────────┘
```

**`acs5-2024-b19013`**: median household income, one row of each kind.

```python
income = pl.read_parquet("useful-views/acs5-2024-b19013.parquet")
print(income.filter(pl.col("geo_id").is_in([
    "0500000US17019",        # an ordinary estimate
    "1400000US04013105003",  # median above the top of Census's scale: 250001 means "250,000 or more"
    "1400000US17019000401",  # median below the bottom: 2499 means "under 2,500"
    "1400000US01003990000",  # too few households sampled to estimate
])))
```

```text
┌──────────────────────┬────────────┬──────────┬──────┬─────────────────────┬─────────────────────┐
│ geo_id               ┆ variable   ┆ estimate ┆ moe  ┆ estimate_note       ┆ moe_note            │
│ ---                  ┆ ---        ┆ ---      ┆ ---  ┆ ---                 ┆ ---                 │
│ str                  ┆ str        ┆ f64      ┆ f64  ┆ str                 ┆ str                 │
╞══════════════════════╪════════════╪══════════╪══════╪═════════════════════╪═════════════════════╡
│ 0500000US17019       ┆ B19013_001 ┆ 63683    ┆ 1675 ┆ null                ┆ null                │
│ 1400000US01003990000 ┆ B19013_001 ┆ null     ┆ null ┆ insufficient-sample ┆ insufficient-sample │
│ 1400000US04013105003 ┆ B19013_001 ┆ 250001   ┆ null ┆ median-upper-bound  ┆ open-ended-median   │
│ 1400000US17019000401 ┆ B19013_001 ┆ 2499     ┆ null ┆ median-lower-bound  ┆ open-ended-median   │
└──────────────────────┴────────────┴──────────┴──────┴─────────────────────┴─────────────────────┘
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
   `outputs`. Write its steps as `01_….py`, `02_….py`, and list each one at
   the end of `recipe.toml` in a `[[steps]]` block, with a `file` and a
   one-sentence `description` of what it does. Sort the rows a step writes
   by columns that together identify each row (as the shared views do, by
   `geo_id` and `variable`), so the same data always gives the same
   fingerprint.
3. Build and record: `uv run useful-views sync`, then
   `uv run useful-views cookbook`. After editing a step's code, run that
   recipe with `uv run useful-views run <recipe>`, then what its warnings say.
4. Commit your recipe folder with the regenerated `datapackage.json`,
   `useful-views/README.md` and `cookbook.json`, and open a pull request into
   `dev`.

Never edit `datapackage.json`, `useful-views/README.md` or `cookbook.json` by
hand, and never resolve a merge conflict in them by hand. Merge `dev` into
your branch, run `uv run useful-views sync --all` and
`uv run useful-views cookbook`, and commit what they write. Use `sync --all`
after any `git pull`, merge or branch switch too. Never commit anything from
`raw/` or `work/`, or any `.parquet` file: this project's `.gitignore` keeps
them out.

### When the shared views change

`datapackage.json` records a fingerprint of every view, a hash of the data
it holds, and, for each recipe, the fingerprints of the views it read when
it last ran. So when a shared view is rebuilt with different data, `uv run
useful-views check` reports your recipe as `out-of-date` (reason
`input-data-changed`), and `uv run useful-views sync` runs it again. Your
results never silently rest on an older version of the shared data.

### Changing the shared base

- **More geography levels** (places, ZCTAs, block groups): add the level to
  `LEVELS` and its count to `EXPECTED` in
  `recipes/acs_geographies/01_keep_levels.py`. Name it in the recipe's
  `description` and in the step's `[[steps]]` description in
  `recipes/acs_geographies/recipe.toml`, and in the `acs5-2024-geographies`
  row of the table above. Then run `uv run useful-views sync --all`.
- **More tables:** add the table file to `fetch_raw.py` and
  [SOURCES.md](SOURCES.md) with its size and SHA-256, and to `files` in
  [sources.toml](sources.toml). Add its raw file and view to
  `recipes/acs_tables/recipe.toml`, and its ID and SHA-256 to `SHA256` in
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
[SOURCES.md](SOURCES.md). [sources.toml](sources.toml) records the source,
license and citation in the form useful-views reads, so the catalog and the
cookbook show them too. This project is not affiliated with or endorsed by
the U.S. Census Bureau.
