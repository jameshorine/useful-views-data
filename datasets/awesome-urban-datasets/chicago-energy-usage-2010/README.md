# Chicago Energy Usage 2010

Useful views on the City of Chicago's [Energy Usage 2010](https://data.cityofchicago.org/d/8yq3-m6wp): the
electricity (kWh) and natural gas (therms) used in 2010 by each census block and building type in the city, with a
few census characteristics of each block. The data comes from ComEd and Peoples Gas, aggregated by Accenture.

- Built with [useful-views](https://jameshorine.github.io/useful-views/).
- Listed in [awesome-urban-datasets](https://github.com/urban-toolkit/awesome-urban-datasets); see
  [the folder README](../README.md).
- Tracked in [#60](https://github.com/jameshorine/useful-views-data/issues/60), part of
  [#59](https://github.com/jameshorine/useful-views-data/issues/59).

The portal says the data covers 88% of Chicago's buildings in 2010, 68% of the city's electricity use and 81% of its
gas use.

## Quick start

From this folder (`datasets/awesome-urban-datasets/chicago-energy-usage-2010`), with
[uv](https://docs.astral.sh/uv/) installed:

```sh
uv sync                      # the exact useful-views, duckdb and certifi versions in uv.lock
uv run python fetch_raw.py   # downloads the 37 MB CSV into raw/ and checks it
uv run useful-views sync     # builds the three views (a few seconds)
uv run useful-views check    # expect: No problems found.
```

Plan for about 52 MB of disk: 37 MB of raw data and 15 MB of views.

The portal hasn't changed this dataset since 2013, so `fetch_raw.py` pins the exact file its SODA2 endpoint serves
(a SHA-256 check). It uses certifi's certificates: the portal's certificate chain ends at GlobalSign Root R46, which
some Python installations don't have.

## The views

All in `useful-views/`. The generated catalog, [useful-views/README.md](useful-views/README.md), lists each one's
columns and the steps that made it.

| View | One row per | What it is |
|---|---|---|
| `energy-usage-2010` | community area × census block × building type × subtype | The table as published, every column typed: 67,051 rows and 75 columns. It includes 77 rows, one per community area, that the portal gives without a census block (see "Things to know"). |
| `energy-usage-2010-monthly` | the same, × month | kWh and therms for each month of 2010: 804,612 rows. |
| `energy-usage-2010-community-areas` | community area | Annual kWh and therms summed over each area's census-block rows: 77 rows. |

### Sample records

These are real rows. Run each snippet from this folder and you get the same output; the comments say what each
sample shows.

```python
import duckdb
```

**`energy-usage-2010`**: one Loop census block, and the Loop's row without a block.

```python
duckdb.sql("""
    SELECT census_block, building_type, building_subtype, total_kwh, electricity_accounts,
           electricity_accounts_note, total_therms, gas_accounts, gas_accounts_note
    FROM 'useful-views/energy-usage-2010.parquet'
    WHERE census_block = '170318390001000'
       OR (community_area_name = 'Loop' AND census_block IS NULL)
    -- Fewer than 4 accounts: the count is empty and the note says so; the usage is still given.
    ORDER BY census_block NULLS FIRST, building_type, building_subtype
""").show(max_width=200)
```

```text
┌─────────────────┬───────────────┬──────────────────┬───────────┬──────────────────────┬───────────────────────────┬──────────────┬──────────────┬───────────────────┐
│  census_block   │ building_type │ building_subtype │ total_kwh │ electricity_accounts │ electricity_accounts_note │ total_therms │ gas_accounts │ gas_accounts_note │
│     varchar     │    varchar    │     varchar      │   int64   │        int32         │          varchar          │    int64     │    int32     │      varchar      │
├─────────────────┼───────────────┼──────────────────┼───────────┼──────────────────────┼───────────────────────────┼──────────────┼──────────────┼───────────────────┤
│ NULL            │ NULL          │ NULL             │ 583174732 │                 2621 │ NULL                      │      9281778 │           90 │ NULL              │
│ 170318390001000 │ Commercial    │ Commercial       │   4265863 │                  284 │ NULL                      │        32305 │            8 │ NULL              │
│ 170318390001000 │ Commercial    │ Multi 7+         │   9165711 │                   24 │ NULL                      │          518 │         NULL │ Less than 4       │
│ 170318390001000 │ Commercial    │ Multi < 7        │     43475 │                 NULL │ Less than 4               │          565 │         NULL │ Less than 4       │
└─────────────────┴───────────────┴──────────────────┴───────────┴──────────────────────┴───────────────────────────┴──────────────┴──────────────┴───────────────────┘
```

**`energy-usage-2010-monthly`**: single-family homes in one Beverly block, a month from each season.

```python
duckdb.sql("""
    SELECT census_block, building_type, building_subtype, month, kwh, therms
    FROM 'useful-views/energy-usage-2010-monthly.parquet'
    WHERE census_block = '170317201001000' AND building_subtype = 'Single Family'
      AND month IN ('2010-01-01', '2010-04-01', '2010-07-01', '2010-10-01')
    -- Electricity peaks in summer (air conditioning), gas in winter (heating).
    ORDER BY month
""").show(max_width=200)
```

```text
┌─────────────────┬───────────────┬──────────────────┬────────────┬───────┬────────┐
│  census_block   │ building_type │ building_subtype │   month    │  kwh  │ therms │
│     varchar     │    varchar    │     varchar      │    date    │ int64 │ int64  │
├─────────────────┼───────────────┼──────────────────┼────────────┼───────┼────────┤
│ 170317201001000 │ Residential   │ Single Family    │ 2010-01-01 │  7588 │   3454 │
│ 170317201001000 │ Residential   │ Single Family    │ 2010-04-01 │  6070 │   1246 │
│ 170317201001000 │ Residential   │ Single Family    │ 2010-07-01 │ 12005 │    197 │
│ 170317201001000 │ Residential   │ Single Family    │ 2010-10-01 │  5221 │    295 │
└─────────────────┴───────────────┴──────────────────┴────────────┴───────┴────────┘
```

**`energy-usage-2010-community-areas`**: the five community areas that used the most electricity.

```python
duckdb.sql("""
    SELECT community_area_name, census_blocks, block_rows, total_kwh, total_therms
    FROM 'useful-views/energy-usage-2010-community-areas.parquet'
    ORDER BY total_kwh DESC
    LIMIT 5
""").show(max_width=200)
```

```text
┌─────────────────────┬───────────────┬────────────┬────────────┬──────────────┐
│ community_area_name │ census_blocks │ block_rows │ total_kwh  │ total_therms │
│       varchar       │     int32     │   int32    │   int64    │    int64     │
├─────────────────────┼───────────────┼────────────┼────────────┼──────────────┤
│ Loop                │           140 │        162 │ 1772626644 │     38637733 │
│ Near North Side     │           369 │        665 │ 1366253834 │     45972630 │
│ Near West Side      │           529 │        966 │  668769012 │     24447517 │
│ Lakeview            │           746 │       2065 │  363176548 │     41674883 │
│ Lincoln Park        │           558 │       1482 │  343792532 │     28187956 │
└─────────────────────┴───────────────┴────────────┴────────────┴──────────────┘
```

### Things to know before querying

**Keys and geography**
- **Census blocks** are 2010 block codes of 15 digits (state 17, Cook County 031, tract, block), stored as text.
  Join to 2010 census block geography on this code.
- **The key** is community area + census block + building type + subtype. A block alone isn't unique: 89 blocks
  appear in more than one community area (86 in two, one in three, two in four), with separate rows and separate
  usage in each.

**The 77 rows without a census block**
- There is one per community area, with no building type either.
- The portal says "Census blocks with less than 4 accounts is displayed at the Community Area without further
  geographic identifiers", but these rows overlap the block rows. Adding their population to the blocks' would put
  Albany Park at 70,842 people, against 51,542 in the 2010 census.
- So `energy-usage-2010-community-areas` leaves them out. Treat them as a separate summary that doesn't match the
  portal's description of it. Their kWh add up to 4.1 billion, against 11.6 billion over the block rows.

**Accounts and usage**
- **"Less than 4" accounts:** for 11,817 rows' electricity accounts and 12,577 rows' gas accounts, the portal gives
  only "Less than 4". The count column is empty and the note column says "Less than 4". The usage is still given on
  every one of these rows.
- **Missing usage:**
  - 871 rows have no electricity figures and 1,296 have no gas total.
  - A gas month can be empty while the year's total isn't; for example, 2,936 rows have an annual gas total but no
    February therms. No electricity month is empty when the year's total is given.
  - Each annual total is the sum of the months given, and the recipes check this.

**Block characteristics**
- Population, housing units, occupied and renter-occupied units, the two percentages and `average_housesize` are the
  same on every row of a block, so don't sum them across a block's rows. `average_stories` and
  `average_building_age` describe that row's buildings.
- **The two "percentage" columns are fractions from 0 to 1**, rounded to at most four decimals.
  `occupied_units_percentage` is occupied ÷ total units, and `renter_occupied_housing_percentage` is renter-occupied
  ÷ occupied units. Both are within 0.0006 of the counts in every row; recompute them from the counts if you need more
  precision.
- **`average_housesize` is the Census's average household size** (from its report QT-P11), which leaves out people in
  group quarters. So it is lower than population ÷ occupied units in 1,343 block rows (never higher), and it can't be
  recomputed from these columns. In the rows without a block it reaches 2,061.92.

**Columns as published**
- `ten_ohu_tot` (labelled "OCCUPIED HOUSING UNITS") repeats `occupied_units` in every row.
- The portal names April's therms `term_april_2010`; here it is `therm_april_2010`.
- The portal describes `kwh_total_sqft` and `therms_total_sqft` as the total square footage tied to the electricity
  or gas use, from Cook County Assessor records (300 up to 48.6 million).
- Of the statistics columns, only the means have a description ("Average Total KWHs for 2010", "Average kWh per
  square foot in 2010", and the same for therms). The `*_sqft_mean_2010` values are square feet (median 2,217), not
  energy per square foot. The standard deviations, quartiles, minimums and maximums have no description. All are given
  as published.

**Building types**
- Residential: Single Family, Multi < 7, Multi 7+.
- Commercial: Commercial, Multi < 7, Multi 7+, Municipal, and one Single Family row.
- Industrial.

## If the download no longer matches

`fetch_raw.py` keeps the new download as `raw/energy_usage_2010_download.csv`. Compare it with the pinned file using
DuckDB:
- **The rows are unchanged but the bytes differ** (for example, the portal changed how it writes numbers): update
  `SIZE` and `SHA256` in `fetch_raw.py`, the SHA-256 in `recipes/energy_usage_2010/01_type_and_check.py`, and
  `sources.toml`.
- **The rows changed:** check the dataset's "last updated" date on the portal, and treat it as a new snapshot. Update:
  - the pin, as above;
  - the known facts in `01_type_and_check.py`;
  - `sources.toml` (obtained date, rows, size, SHA-256, last-updated date);
  - the counts and sample records in this README;
  - this dataset's rows in [`../README.md`](../README.md) and [`../../README.md`](../../README.md).

After either change, run `uv run useful-views sync --all` and `uv run useful-views cookbook`.

## Sources and credit

City of Chicago, Energy Usage 2010, Chicago Data Portal, dataset 8yq3-m6wp:
https://data.cityofchicago.org/d/8yq3-m6wp. ComEd and Peoples Gas data, aggregated by Accenture.

The portal states no open license. The City of Chicago's
[data terms of use](https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html) apply. This repository
publishes recipes and records, not the data, and the terms ask for this disclaimer:

> This site provides applications using data that has been modified for use from its original source,
> www.cityofchicago.org, the official website of the City of Chicago. The City of Chicago makes no claims as to the
> content, accuracy, timeliness, or completeness of any of the data provided at this site. The data provided at this
> site is subject to change at any time. It is understood that the data provided at this site is being used at one's
> own risk.

The dataset is listed in [awesome-urban-datasets](https://github.com/urban-toolkit/awesome-urban-datasets), curated
by the [Urban Toolkit](https://urbantk.org/) lab at UIC.
