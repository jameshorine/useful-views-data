# FAS PSD: commodity balances

Useful views on USDA FAS [Production, Supply and Distribution (PSD)](https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads):
estimates of production, trade, use and stocks for 63 agricultural
commodities in 214 countries and regions, by marketing year from 1960, built
with [useful-views](https://jameshorine.github.io/useful-views/). Tracked in
[#38](https://github.com/jameshorine/useful-views-data/issues/38).

PSD is revised every month and overwrites its earlier estimates, so the
snapshot date is part of the data's identity: this project is built from the
snapshot of **2026-11-17**, and every view is named for it.

## Quick start

From this folder (`datasets/fas-psd`), with [uv](https://docs.astral.sh/uv/)
installed:

```sh
uv sync                      # the exact useful-views and duckdb versions in uv.lock
uv run python fetch_raw.py   # downloads the 10 MB snapshot into raw/ and checks it
uv run useful-views sync     # builds the three views (a few seconds)
uv run useful-views check    # expect: No problems found.
```

Plan for about 210 MB of disk: 10 MB of raw data, about 195 MB in `work/`
(the extracted CSV) and 3 MB of views.

FAS serves only the latest snapshot at its download URL. Once FAS publishes
a newer one, `fetch_raw.py` says the file no longer matches and stops: this
snapshot can't be downloaded again, so keep your copy of
`raw/psd_alldata_csv_2026-11-17.zip`.

FAS also offers PSD through its [Open Data API](https://apps.fas.usda.gov/opendatawebV2/).
This project uses the bulk zip instead: it is one complete file with every
commodity, country and attribute, needs no key, and can be pinned by its
SHA-256.

## The views

All in `useful-views/`. The generated catalog,
[useful-views/README.md](useful-views/README.md), lists each one's columns
and the steps that made it.

| View | One row per | What it is |
|---|---|---|
| `psd-2026-11-17-alldata` | commodity × country × market year × attribute | The PSD all-commodities file as published, every column unchanged but typed: 2,095,339 rows. |
| `psd-2026-11-17-commodity-attribute` | commodity × attribute | Every attribute PSD reports for each commodity, with its unit: 752 pairs. |
| `psd-2026-11-17-world-balance` | commodity × market year × attribute | Every country summed to a world total. Rates and ratios (such as Yield) are left out. |

A quick start with DuckDB:

```python
import duckdb

duckdb.sql("""
    SELECT Market_Year, Attribute_Description, Unit_Description, Value
    FROM 'useful-views/psd-2026-11-17-world-balance.parquet'
    WHERE Commodity_Code = '0440000'   -- Corn
      AND Market_Year = 2025
    ORDER BY Attribute_ID
""").show()
```

### Sample records

Real rows from the 2026-11-17 snapshot. Run each snippet from this folder:
you get the same output. The comments say what each sample shows. When you
move to a newer snapshot, re-run the snippets and paste the new output here.

```python
import duckdb
```

**`psd-2026-11-17-alldata`**: US corn, marketing year 2025, a few of its 12 columns.

```python
duckdb.sql("""
    SELECT Commodity_Code, Country_Code, Market_Year, Calendar_Year, Month,
           Attribute_ID, Attribute_Description, Unit_Description, Value
    FROM 'useful-views/psd-2026-11-17-alldata.parquet'
    WHERE Commodity_Code = '0440000'   -- corn
      AND Country_Code = 'US'
      AND Market_Year = 2025
      AND Attribute_ID IN ('028', '088', '176', '184')
    -- Calendar_Year and Month: when the value was last revised, not when it applies.
    -- The unit differs by attribute: Yield is in tonnes per hectare.
    ORDER BY Attribute_ID
""").show(max_width=200)
```

```text
┌────────────────┬──────────────┬─────────────┬───────────────┬───────┬──────────────┬───────────────────────┬──────────────────┬──────────┐
│ Commodity_Code │ Country_Code │ Market_Year │ Calendar_Year │ Month │ Attribute_ID │ Attribute_Description │ Unit_Description │  Value   │
│    varchar     │   varchar    │    int16    │     int16     │ int16 │   varchar    │        varchar        │     varchar      │  double  │
├────────────────┼──────────────┼─────────────┼───────────────┼───────┼──────────────┼───────────────────────┼──────────────────┼──────────┤
│ 0440000        │ US           │        2025 │          2026 │    11 │ 028          │ Production            │ (1000 MT)        │ 430896.0 │
│ 0440000        │ US           │        2025 │          2026 │    11 │ 088          │ Exports               │ (1000 MT)        │  87106.0 │
│ 0440000        │ US           │        2025 │          2026 │    11 │ 176          │ Ending Stocks         │ (1000 MT)        │  53217.0 │
│ 0440000        │ US           │        2025 │          2026 │    11 │ 184          │ Yield                 │ (MT/HA)          │    11.71 │
└────────────────┴──────────────┴─────────────┴───────────────┴───────┴──────────────┴───────────────────────┴──────────────────┴──────────┘
```

**`psd-2026-11-17-commodity-attribute`**: the same attribute in three commodities.

```python
duckdb.sql("""
    SELECT * FROM 'useful-views/psd-2026-11-17-commodity-attribute.parquet'
    WHERE Attribute_ID = '028'   -- Production
      AND Commodity_Code IN ('0440000', '0711100', '2631000')
    -- One attribute, three units: never sum across commodities.
    ORDER BY Commodity_Code
""").show(max_width=200)
```

```text
┌────────────────┬───────────────────────┬──────────────┬───────────────────────┬────────────────────┐
│ Commodity_Code │ Commodity_Description │ Attribute_ID │ Attribute_Description │  Unit_Description  │
│    varchar     │        varchar        │   varchar    │        varchar        │      varchar       │
├────────────────┼───────────────────────┼──────────────┼───────────────────────┼────────────────────┤
│ 0440000        │ Corn                  │ 028          │ Production            │ (1000 MT)          │
│ 0711100        │ Coffee, Green         │ 028          │ Production            │ (1000 60 KG BAGS)  │
│ 2631000        │ Cotton                │ 028          │ Production            │ 1000 480 lb. Bales │
└────────────────┴───────────────────────┴──────────────┴───────────────────────┴────────────────────┘
```

**`psd-2026-11-17-world-balance`**: world corn, 2025.

```python
duckdb.sql("""
    SELECT * FROM 'useful-views/psd-2026-11-17-world-balance.parquet'
    WHERE Commodity_Code = '0440000'   -- world corn
      AND Market_Year = 2025
      AND Attribute_ID IN ('028', '088', '125', '176')
    -- n_countries: how many countries report a nonzero value.
    ORDER BY Attribute_ID
""").show(max_width=200)
```

```text
┌────────────────┬───────────────────────┬─────────────┬──────────────┬───────────────────────┬──────────────────┬───────────┬─────────────┐
│ Commodity_Code │ Commodity_Description │ Market_Year │ Attribute_ID │ Attribute_Description │ Unit_Description │   Value   │ n_countries │
│    varchar     │        varchar        │    int16    │   varchar    │        varchar        │     varchar      │  double   │    int16    │
├────────────────┼───────────────────────┼─────────────┼──────────────┼───────────────────────┼──────────────────┼───────────┼─────────────┤
│ 0440000        │ Corn                  │        2025 │ 028          │ Production            │ (1000 MT)        │ 1334715.0 │         115 │
│ 0440000        │ Corn                  │        2025 │ 088          │ Exports               │ (1000 MT)        │  215361.0 │          63 │
│ 0440000        │ Corn                  │        2025 │ 125          │ Domestic Consumption  │ (1000 MT)        │ 1306348.0 │         125 │
│ 0440000        │ Corn                  │        2025 │ 176          │ Ending Stocks         │ (1000 MT)        │  308310.0 │         108 │
└────────────────┴───────────────────────┴─────────────┴──────────────┴───────────────────────┴──────────────────┴───────────┴─────────────┘
```

### Things to know before querying

- Values are in the unit in `Unit_Description`, and the unit differs by
  commodity (Production is 1000 MT for corn, 1000 480 lb. Bales for cotton).
  Never sum across units; `commodity_attribute` lists every commodity's units.
- Market years are local marketing years, not calendar years. The latest one
  or two are USDA projections, and PSD overwrites them every month.
- Country codes are PSD's own (FIPS 10-4 style), not ISO: China is `CH`,
  Germany `GM`, the European Union `E4`.
- `Calendar_Year` and `Month` say when a value was last revised, not when it
  applies. Some rows have month `0`.
- About a third of the values are zero; whether a zero means "zero" or "not
  reported" is not documented.

## World totals: known overlaps

`world_balance` is a plain sum of every country as PSD publishes them. PSD
reports the EU and the USSR as they were made up at the time, and lists a
country separately only while it is outside the aggregate, so a plain sum is
almost always right. These cases, where the same quantity appears to be
counted twice, were found in the 2026-09-24 snapshot (the earlier version of
this project, at git commit `19ab074`):

| Case | Years | Why we think it overlaps |
|---|---|---|
| Romania (`RO`) dairy (fluid milk, butter, cheese) alongside the European Union (`E4`) | 1999–2007 | When Romania's rows stop in 2008, `E4` doesn't rise to absorb them, which suggests `E4` already included Romania. Likely, not proven. |
| Ukraine (`UP`) sugar alongside the USSR (`UR`) | 1988 | Ukraine was part of the USSR. |
| Russia (`RS`) dry whole milk powder alongside the USSR (`UR`) | 1992 | Russia was part of the USSR. |

The 2026-11-17 snapshot has more cases where an aggregate and one of its
members both report the same commodity, year and attribute. They haven't yet
been sorted into genuine double counts and harmless ones, so treat the list
above as incomplete. World imports and exports also don't match, because each country's local marketing year is summed as is; compare
PSD's trade-year attributes (TY Imports, TY Exports) for trade. No adjustment
is made. If you know how USDA builds its own world totals, please open an
issue.

## Moving to a newer snapshot

1. Download the new zip and save it as `raw/psd_alldata_csv_<server date>.zip`,
   with the date from the `last-modified` header (`curl -sI <url>`).
2. Update `fetch_raw.py` (name, size, SHA-256), `sources.toml`, and the SHA-256
   in `recipes/psd_alldata/01_extract_csv.py`.
3. In the three recipes, change the snapshot date in the paths and in the
   view names, and update the expected facts in
   `recipes/psd_alldata/02_type_and_sort.py` and
   `recipes/commodity_attribute/01_list_pairs.py` after profiling the new file.
4. Check the new file for new rates or ratios: they belong in `NON_ADDITIVE`
   in `recipes/world_balance/01_sum_countries.py`, or the world balance would
   sum them.
5. Run `uv run useful-views sync` and `uv run useful-views cookbook`.
6. Update this README (the snapshot date, the counts, the sample records:
   re-run the snippets) and the dataset's row in the catalogue,
   [`../README.md`](../README.md). Re-check the world-total overlaps.

## Sources and credit

USDA Foreign Agricultural Service, Production, Supply and Distribution (PSD)
Online, All Commodities. FAS's [catalog record on data.gov](https://catalog.data.gov/dataset/production-supply-and-distribution-database)
(USDA-26341) lists it under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); it is
also a work of the U.S. federal government. The views here are retyped and,
in `world_balance`, summed by this project: they are not official USDA
figures, and this project is not affiliated with or endorsed by USDA. The
details are in [sources.toml](sources.toml).
