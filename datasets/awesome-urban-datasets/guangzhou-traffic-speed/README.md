# Guangzhou traffic speed, 2016

Useful views on the [Urban Traffic Speed Dataset of Guangzhou, China](https://doi.org/10.5281/zenodo.1205229), by
Xinyu Chen, Yixian Chen and Zhaocheng He (2018): traffic speeds on 214 anonymized road segments, mainly urban
expressways and arterials, every 10 minutes for 61 days, from 1 August to 30 September 2016.

- Built with [useful-views](https://jameshorine.github.io/useful-views/).
- Listed in [awesome-urban-datasets](https://github.com/urban-toolkit/awesome-urban-datasets); see
  [the folder README](../README.md).
- Tracked in [#62](https://github.com/jameshorine/useful-views-data/issues/62), part of
  [#59](https://github.com/jameshorine/useful-views-data/issues/59).

## Quick start

From this folder (`datasets/awesome-urban-datasets/guangzhou-traffic-speed`), with
[uv](https://docs.astral.sh/uv/) installed:

```sh
uv sync                      # the exact useful-views, duckdb and certifi versions in uv.lock
uv run python fetch_raw.py   # downloads the 18 MB zip from Zenodo into raw/ and checks it
uv run useful-views sync     # builds the two views (a few seconds)
uv run useful-views check    # expect: No problems found.
```

Plan for about 62 MB of disk: 18 MB of raw data, 38 MB in `work/` (the extracted CSVs) and 7 MB of views.

Zenodo lets a record's files change only in its first 30 days, and after that only for exceptional reasons such as
personal data. This record was published in 2018 and has only one version, so the download is pinned: `fetch_raw.py`
checks its SHA-256, and the MD5 that Zenodo lists for it.

## The views

All in `useful-views/`. The generated catalog, [useful-views/README.md](useful-views/README.md), lists each one's
columns and the steps that made it.

| View | One row per | What it is |
|---|---|---|
| `guangzhou-traffic-speed` | road segment × 10-minute window | Every observation, typed, with the window's start as a timestamp: 1,855,589 rows. |
| `guangzhou-traffic-speed-segments` | road segment | Observations, missing windows, days with data, and lowest, mean and highest speed: 214 rows. |

### Sample records

These are real rows. Run each snippet from this folder and you get the same output; the comments say what each
sample shows.

```python
import duckdb
```

**`guangzhou-traffic-speed`**: segment 1's first four windows.

```python
duckdb.sql("""
    SELECT road_id, day_id, time_id, window_start, speed
    FROM 'useful-views/guangzhou-traffic-speed.parquet'
    WHERE road_id = 1 AND day_id = 1 AND time_id <= 4
    -- day_id and time_id are the dataset's own indices: day 1 is 2016-08-01, window 1 starts at 00:00.
    -- The file gives the last speed as 44.483000000000004; it is rounded to its three decimals.
    ORDER BY time_id
""").show(max_width=200)
```

```text
┌─────────┬────────┬─────────┬─────────────────────┬────────┐
│ road_id │ day_id │ time_id │    window_start     │ speed  │
│  int16  │ int16  │  int16  │      timestamp      │ double │
├─────────┼────────┼─────────┼─────────────────────┼────────┤
│       1 │      1 │       1 │ 2016-08-01 00:00:00 │ 40.893 │
│       1 │      1 │       2 │ 2016-08-01 00:10:00 │ 41.938 │
│       1 │      1 │       3 │ 2016-08-01 00:20:00 │ 44.098 │
│       1 │      1 │       4 │ 2016-08-01 00:30:00 │ 44.483 │
└─────────┴────────┴─────────┴─────────────────────┴────────┘
```

**`guangzhou-traffic-speed-segments`**: the five segments with the most missing windows.

```python
duckdb.sql("""
    SELECT road_id, observations, missing_windows, days_with_data, min_speed, mean_speed, max_speed
    FROM 'useful-views/guangzhou-traffic-speed-segments.parquet'
    -- A complete segment has 61 x 144 = 8,784 windows. These five are missing whole days.
    ORDER BY missing_windows DESC, road_id
    LIMIT 5
""").show(max_width=200)
```

```text
┌─────────┬──────────────┬─────────────────┬────────────────┬───────────┬────────────┬───────────┐
│ road_id │ observations │ missing_windows │ days_with_data │ min_speed │ mean_speed │ max_speed │
│  int16  │    int32     │      int32      │     int16      │  double   │   double   │  double   │
├─────────┼──────────────┼─────────────────┼────────────────┼───────────┼────────────┼───────────┤
│     123 │         2880 │            5904 │             20 │     1.484 │      27.59 │    45.787 │
│      48 │         4320 │            4464 │             30 │     9.079 │     34.608 │    49.124 │
│      55 │         4320 │            4464 │             30 │     1.054 │     24.347 │    41.512 │
│     146 │         4320 │            4464 │             30 │     6.122 │     36.265 │    51.515 │
│     147 │         4320 │            4464 │             30 │     1.846 │     22.639 │    51.309 │
└─────────┴──────────────┴─────────────────┴────────────────┴───────────┴────────────┴───────────┘
```

### Things to know before querying

**The segments**
- They are anonymized: the dataset gives an ID from 1 to 214, but no names, locations or geometry, so these views
  can't be mapped.

**Speeds**
- The record doesn't state the unit. The values run from 1.054 to 119.27, with a mean of 39.0, which fits km/h on
  expressways and arterials.
- Speeds have three decimals, except the 17 of 100 or more, which the CSV gives to at most two. All 17 are on segment
  166 on 8 September, between 00:00 and 03:50.
- 455,175 speeds are written with float noise (such as `44.483000000000004`), and these views round them to three
  decimals. No speed moves by more than a billionth, and the recipe checks this.

**Missing windows**
- 206 of the 214 segments have all 8,784 windows. The 24,187 missing windows (1.29%) are almost all whole days:
  - segments 48, 55, 146 and 147 have no data before 1 September;
  - segment 123 has none before 11 September;
  - segment 34 lacks two days.
- Only 139 windows are missing within days that otherwise have data: one day each for segments 3, 34 and 166.
- Missing windows are absent rows, not zeros or nulls.

**Times**
- `window_start` is the window's date and start time as the dataset gives them. The dataset doesn't name a time zone;
  it is presumably local time in Guangzhou (China Standard Time, UTC+8).
- Day 1 (1 August 2016) is a Monday.
- **`tensor.mat`** in the zip holds the same 1,855,589 observations as a 214 × 61 × 144 array (segment × day ×
  window), with 0 for each of the 24,187 missing windows.
  - 4,396 of its values differ from the CSV's, by 0.0005 to 0.004. It keeps a fourth decimal for most of segment
    211's speeds (62.0745 where the CSV has 62.075), and a third for 16 of segment 166's speeds of 100 or more
    (108.446 where the CSV has 108.45).
  - These views use the CSV, which the record calls the original data.

## If the download no longer matches

`fetch_raw.py` keeps a different download as `raw/Data_download.zip`. Check the URL first, then the record's page
for a notice. The pin lives in:
- `fetch_raw.py`: `SIZE`, `SHA256` and `MD5`;
- `recipes/speeds/01_extract_csvs.py`: `SHA256`;
- `sources.toml`.

The known facts are in `recipes/speeds/02_type_and_join.py`. After a change, run `uv run useful-views sync --all` and
`uv run useful-views cookbook`.

## Sources and credit

Xinyu Chen, Yixian Chen and Zhaocheng He (2018). Urban Traffic Speed Dataset of Guangzhou, China. Zenodo.
https://doi.org/10.5281/zenodo.1205229. Licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The record lists these papers, which use the data:
- Xinyu Chen, Zhaocheng He and Jiawei Wang (2018). Spatial-temporal traffic speed patterns discovery and incomplete
  data recovery via SVD-combined tensor decomposition. *Transportation Research Part C*, 86, 59–77.
- Xinyu Chen, Zhaocheng He and Lijun Sun (2019). A Bayesian tensor decomposition approach for spatiotemporal traffic
  data imputation. *Transportation Research Part C*, 98, 73–84.

The dataset is listed in [awesome-urban-datasets](https://github.com/urban-toolkit/awesome-urban-datasets), curated
by the [Urban Toolkit](https://urbantk.org/) lab at UIC.
