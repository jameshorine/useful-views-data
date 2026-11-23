# FAS PSD: commodity balances

Useful views on USDA FAS [Production, Supply and Distribution (PSD)](https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads):
estimates of production, trade, use and stocks for 63 agricultural
commodities in 214 countries and regions, by marketing year from 1960, built
with [useful-views](https://jameshorine.github.io/useful-views/). Tracked in
[#38](https://github.com/jameshorine/useful-views-data/issues/38).

PSD is revised at least once a month and overwrites its earlier estimates,
so the snapshot date is part of the data's identity: this project is built
from the snapshot of **2026-11-17**, and every view is named for it.

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

FAS replaces the file at its main download URL at every PSD release (see
"When PSD is updated" below; the next is due on 10 December 2026). It also
keeps each month's last file in a monthly archive, and
[archives/2026/11/psd_alldata_csv.zip](https://apps.fas.usda.gov/psdonline/downloads/archives/2026/11/psd_alldata_csv.zip)
served this snapshot byte for byte on 2026-11-20 and 2026-11-22, so
`fetch_raw.py` downloads it from there and tries the main URL only if the
archive is unavailable. FAS doesn't say how long it keeps archived files or
whether it changes them, and some are dated after their month ended (the June
2024 all-commodities file is dated 3 July 2024, and five of January 2026's
files 23 February 2026). So keep your copy of
`raw/psd_alldata_csv_2026-11-17.zip` as well: `fetch_raw.py` refuses any file
that doesn't match its SHA-256.

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
  or two are USDA projections, and PSD overwrites them at each release.
- Country codes are PSD's own (FIPS 10-4 style), not ISO: China is `CH`,
  Germany `GM`, the European Union `E4`.
- `Calendar_Year` and `Month` say when a value was last revised, not when it
  applies. Some rows have month `0`.
- About a third of the values are zero; whether a zero means "zero" or "not
  reported" is not documented.

## When PSD is updated

FAS rebuilds the all-commodities file every time it releases PSD data for any
commodity group: PSD Online says its downloadable files "are generated when
each commodity's data is released". The dates are in the "PSD Release
Schedule" tab of [PSD Online's downloads page](https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads),
which can list every release scheduled for the current calendar year.

- Grains, oilseeds and cotton are updated every month, at 12:00 PM Eastern on
  the day USDA releases its WASDE report. FAS's
  [monthly circulars](https://apps.fas.usda.gov/PSDOnline/Circulars/2026/11/Grain.pdf)
  say it "updates its production, supply and distribution (PSD) database for
  cotton, oilseeds, and grains at 12:00 p.m. on the day the World Agricultural
  Supply and Demand Estimates (WASDE) report is released".
- Livestock and poultry, sugar, coffee, dairy, citrus, tree nuts and other
  fruit are updated once or twice a year each, at 3:00 PM Eastern. Livestock
  and poultry come out on the April and October WASDE days.

So the file can change several times in one month. This snapshot is the file
as rebuilt at the sugar release of 17 November 2026; its grains, oilseeds and
cotton figures come from the WASDE-day release of 10 November.

## World totals: where the sum counts twice

`world_balance` is a plain sum of every code in the PSD file. Some codes are
blocs or former states that contain others: EU-15 (`E2`), EU-25 (`E3`), the
European Union (`E4`), the USSR (`UR`), Former Yugoslavia (`YO`), Yugoslavia
(>05/92) (`YU`), Former Czechoslovakia (`CZ`) and Belgium-Luxembourg (`BE`).
Yemen (`YM`) is the union of Yemen (Sanaa) (`YE`) and Yemen (Aden) (`YS`). PSD
mostly lists a country separately only while no bloc covers it, so the sum is
almost always right. We compared every bloc and former state with its members
and successors, and every country with the territories PSD lists separately,
wherever both report the same commodity, year and attribute. These are the
cases where a quantity is, or may be, counted twice. No adjustment is made for
them.

**Proven** by PSD's own figures:

| Overlap | Commodity | Years | Evidence |
|---|---|---|---|
| Yemen (`YM`) with Yemen (Sanaa) (`YE`) and Yemen (Aden) (`YS`) | Sugar | 1990–1991 | `YM` is their sum: consumption 310 = 250 + 60 in 1990, imports 322 = 260 + 62 in 1991 (thousand MT) |
| Former Yugoslavia (`YO`) with Yugoslavia (>05/92) (`YU`) | Apples, pears | 1992–1993 | The same figures in 1992 (apples 204,000 MT, pears 75,000 MT), close ones in 1993 |
| USSR (`UR`) with Belarus (`BO`) | Cattle, ending stocks | 1987 | The successors' 1988 opening herds, Belarus's included, add up to 99.6% of `UR`'s 1987 closing herd, so Belarus's 7.7 million head are counted twice |

**Likely**, where the bloc's figures look like the whole territory in those
years but PSD doesn't say so:

- `CZ` with the Czech Republic (`EZ`) and Slovakia (`LO`): cattle and beef,
  1990–1993, and with the Czech Republic also swine and pork.
- `E4` with Romania (`RO`): fluid milk, butter and cheese, 1999–2007.
  Romania's milk is about 4% of `E4`'s.
- `E2` with Austria (`AU`), Finland (`FI`) and Sweden (`SW`): sugar,
  1991–1994.
- `E2` with Finland: cattle, swine, beef and pork, 1993–1994.
- `UR` with Ukraine (`UP`): sugar, 1988.
- `UR` with Georgia (`GG`): sugar, 1986–1988.
- `UR` with Russia (`RS`): dry whole milk powder, 1992, 150 thousand MT (5% of
  world production).
- `YO` with Bosnia and Herzegovina (`BK`), Croatia (`HR`), North Macedonia
  (`MK`) and Slovenia (`SI`): sugar, 1990–1991.

**Possible**, where the data can't settle it:

- `E2` with Austria, Finland and Sweden: sugar, 1989–1990.
- `E2` with the United Kingdom (`UK`), Denmark (`DA`) and Ireland (`EI`):
  sugar, 1971, when `E2`'s consumption rises 17% while all three still report
  their own.
- The EU (`E2`, `E3`, `E4`) with the French West Indies (`Y2`): sugar,
  1994–2016. The EU's cane sugar production starts in 1994 and may include
  Guadeloupe and Martinique.
- The EU (`E2`, `E4`) with Réunion (`RE`): rice imports and consumption,
  1960–2022.
- Belgium-Luxembourg (`BE`) with Luxembourg (`LU`): nonfat dry milk,
  1965–1973.
- The United States (`US`) with Puerto Rico (`RQ`): sugar, 1972–1995.
- Israel (`IS`) with the Gaza Strip (`GZ`): citrus, 1970–1996.

In each case the amount is at most about 1.5% of world production of that
commodity in that year, apart from dry whole milk powder in 1992; stocks and
trade can be off by more. Some pairs are listed side by side without
overlapping: Ethiopia and Eritrea from 1993, Sudan and South Sudan from 2011,
and the European Union and the United Kingdom from 2016, when `E4` leaves the
UK out (its 2016 opening stocks are its 2015 closing stocks less the UK's).

World imports and exports also don't match, because each country's local
marketing year is summed as is; compare PSD's trade-year attributes (TY
Imports, TY Exports) for trade. If you know how USDA builds its own world
totals, please open an issue.

## Moving to a newer snapshot

1. Download the new zip and save it as `raw/psd_alldata_csv_<server date>.zip`,
   with the date from the `last-modified` header (`curl -sI <url>`). Point the
   archive URL in `fetch_raw.py` at that month's folder
   (`downloads/archives/YYYY/MM/`), and check it serves the same file.
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
