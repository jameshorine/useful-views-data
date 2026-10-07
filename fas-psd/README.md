# fas-psd

Useful views on USDA FAS [Production, Supply and Distribution (PSD)](https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads): estimates of production, trade, use and stocks for 63 agricultural commodities in about 200 countries, by marketing year from 1960.

PSD is revised every month and overwrites earlier estimates, so each release is named for the snapshot it was built from. Provenance and caveats are in [in/SOURCES.md](in/SOURCES.md).

## Releases

### `useful-views/psd_2026-09-24/`

| View | One row per | What it is |
|---|---|---|
| `psd_alldata` | commodity × country × market year × attribute | The PSD all-commodities file as published, every column unchanged but typed. |
| `commodity_attribute` | commodity × attribute | Every attribute PSD reports for each commodity, with its unit, as published. |
| `world_balance` | commodity × market year × attribute | Every country summed to a world total. Rates and ratios (such as Yield) are left out. |

Column descriptions, keys, checksums and build details are in the release's `datapackage.json`.

## Example queries

[sandbox/example_querries.ipynb](sandbox/example_querries.ipynb) ends with worked examples on all three views: what PSD reports for a commodity, a country balance sheet, the world balance over time, top producers and their share of the world, world stocks-to-use with and without China, net exporters, and area versus yield by decade.

A quick start with DuckDB:

```python
import duckdb

duckdb.sql("""
    SELECT Market_Year, Attribute_Description, Unit_Description, Value
    FROM 'useful-views/psd_2026-09-24/world_balance.parquet'
    WHERE Commodity_Code = '0440000'   -- Corn
      AND Market_Year = 2025
    ORDER BY Attribute_ID
""").show()
```

Things to know before querying:

- Values are in the unit in `Unit_Description`, and the unit differs by commodity (Production is 1000 MT for corn, 1000 480 lb. Bales for cotton). Never sum across units; `commodity_attribute` lists every commodity's units.
- Market years are local marketing years, not calendar years. The latest one or two are USDA projections, and PSD overwrites them every month.
- Country codes are PSD's own (FIPS 10-4 style), not ISO: China is `CH`, Germany `GM`, the European Union `E4`.
- `Calendar_Year` and `Month` say when a value was last revised, not when it applies.

## World totals: known overlaps (help wanted)

`world_balance` is a plain sum of every country as PSD publishes them. PSD reports the EU and the USSR as they were made up at the time, and lists a country separately only while it is outside the aggregate, so a plain sum is almost always right. These are the known exceptions, where the same quantity appears to be counted twice:

| Case | Years | Size | Why we think it overlaps |
|---|---|---|---|
| Romania (`RO`) dairy (fluid milk, butter, cheese) alongside the European Union (`E4`) | 1999–2007 | Fluid milk about 5.8 million MT a year, about 4% of the EU figure | When Romania's rows stop in 2008, `E4` doesn't rise to absorb them, which suggests `E4` already included Romania. Likely, not proven. |
| Ukraine (`UP`) sugar alongside the USSR (`UR`) | 1988 | 650 thousand MT production | Ukraine was part of the USSR. |
| Russia (`RS`) dry whole milk powder alongside the USSR (`UR`) | 1992 | 150 thousand MT production | Russia was part of the USSR. |

World imports and exports also don't match, because each country's local marketing year is summed as is. That isn't an error; PSD's trade-year attributes (TY Imports, TY Exports) are the ones to compare.

We haven't adjusted for any of this. If you know how USDA builds its own world totals, can confirm or rule out an overlap, or find one that isn't listed, please [open an issue](https://github.com/jameshorine/useful-views/issues) or a pull request. We'd like the adjustment, if one is needed, to be documented and agreed rather than guessed.

## Build

```sh
uv run fas-psd            # steps 1-5; add --force to replace existing outputs
uv run python -m fas_psd.step5_verify --check   # fail if outputs differ from the committed datapackage.json
```

The source zip is not committed: download it as described in `in/SOURCES.md` first.
