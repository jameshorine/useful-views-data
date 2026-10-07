# fas-psd

Useful views on USDA FAS [Production, Supply and Distribution (PSD)](https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads): estimates of production, trade, use and stocks for 63 agricultural commodities in about 200 countries, by marketing year from 1960.

PSD is revised every month and overwrites earlier estimates, so each release is named for the snapshot it was built from. Provenance and caveats are in [in/SOURCES.md](in/SOURCES.md).

## Releases

### `useful-views/psd_2026-09-24/`

| View | One row per | What it is |
|---|---|---|
| `psd_alldata` | commodity × country × market year × attribute | The PSD all-commodities file as published, every column unchanged but typed. |
| `commodity_attribute` | commodity × attribute | Every attribute PSD reports for each commodity, with its unit, as published. |

Column descriptions, keys, checksums and build details are in the release's `datapackage.json`.

## Build

```sh
uv run fas-psd            # steps 1-4; add --force to replace existing outputs
uv run python -m fas_psd.step4_verify --check   # fail if outputs differ from the committed datapackage.json
```

The source zip is not committed: download it as described in `in/SOURCES.md` first.
