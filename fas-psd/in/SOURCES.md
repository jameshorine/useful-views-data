# Sources

Where every input in `in/` came from. Inputs are read-only: scripts read them, nothing writes to them.

## FAS Production, Supply and Distribution (PSD), all commodities

| | |
|---|---|
| Publisher | USDA Foreign Agricultural Service (FAS) |
| Dataset | PSD Online, "All Commodities (CSV Format)" |
| Landing page | https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads |
| Download | https://apps.fas.usda.gov/psdonline/downloads/psd_alldata_csv.zip |
| Server last-modified | 2026-09-24 19:03:01 GMT (the downloads page lists 9/24/2026) |
| Zip size | 10,444,053 bytes |
| Zip SHA256 | `dccef5678cffecc1e7722342396c751442eb245d06dff4498ec87c346908c41f` |
| Downloaded | 2026-10-07 |
| Saved as | `in/psd_alldata_csv_2026-09-24.zip` (gitignored; renamed with the server date) |
| Licence | Not stated on the downloads page. As a work of the US federal government it is likely public domain (17 U.S.C. §105); confirm with FAS before redistributing. |

### This is a snapshot

PSD is revised every month, and **old estimates are overwritten in place**: the file holds only the latest value for each commodity, country, year and attribute, not the history of revisions. The same URL serves a different file after each update. So:

- The snapshot date (2026-09-24) is part of the dataset's identity. It names the release folder, `useful-views/psd_2026-09-24/`.
- To keep a snapshot, keep its zip. A later download of the same URL will not reproduce it.
- Each new snapshot gets its own dated zip in `in/`, its own section here, and its own release folder.

### Contents

| Zip entry | Size | Rows |
|---|---|---|
| `psd_alldata.csv` | 202,088,459 bytes (dated 2026-09-24 15:01 in the zip) | 2,093,353 plus a header |

Columns: `Commodity_Code`, `Commodity_Description`, `Country_Code`, `Country_Name`, `Market_Year`, `Calendar_Year`, `Month`, `Attribute_ID`, `Attribute_Description`, `Unit_ID`, `Unit_Description`, `Value`.

### Facts about the 2026-09-24 snapshot

Profiled on 2026-10-07. These are what the pipeline checks.

| | |
|---|---|
| Rows | 2,093,353 |
| Key | (`Commodity_Code`, `Country_Code`, `Market_Year`, `Attribute_ID`) is unique |
| Commodities | 63 |
| Countries and regions | 214 |
| Attributes | 69 |
| Units | 11 |
| Commodity–attribute pairs | 752 |
| Market years | 1960–2026 |
| Missing values | none |
| Code → description | one description per commodity, country, attribute and unit code |
| Unit | one unit per (commodity, attribute) |

### Things to know before using it

- **Country codes are not ISO 3166.** They follow the older US FIPS 10-4 style: China is `CH`, Germany `GM`, Spain `SP`, Japan `JA`, Switzerland `SZ`. Some codes are FAS-specific, such as `E4` for the European Union; 5 codes contain digits. Joining to other country data needs a crosswalk.
- **`Calendar_Year` and `Month` give when a value was last revised**, not when it applies. There are 289 distinct revision months, from 1960 to 2026-09. Some rows have month `00`.
- **Market years are local marketing years**, which start in different months for different commodities and countries. A market year is not a calendar year.
- **Units are mixed**: 1000 MT, MT, 1000 HA, 1000 60 kg bags, 1000 480 lb bales, 1000 head, MT/HA, KG/HA, 1000 MT CWE, percent and ratio. Never sum across units.
- **Some attributes are totals of others.** For example, Total Supply = Beginning Stocks + Production + Imports, which holds in all but 12 of 146,974 cases.
- **711,988 values (34%) are zero and 756 are negative.** Whether a zero means "zero" or "not reported" is not documented in the file; check before treating zeros as data.

## Updating a source

1. Download the new snapshot and save it as `in/psd_alldata_csv_<server date>.zip`, with the date from the `last-modified` header (`curl -sI <url>`).
2. Add a section here with its URL, headers, size, SHA256 (`shasum -a 256 <file>`) and download date, and re-profile the facts.
3. Update the snapshot name and expected values in `config.py` to match.
4. Build the new release folder. Keep the previous snapshot's zip and section.
