# Sources

Where every file in `raw/` comes from. `raw/` is not in git; `python
fetch_raw.py` downloads these files and checks each one against the size
and SHA-256 below. If Census replaces a file, the check fails, and this page
and `fetch_raw.py` must be updated together, with a new section here for the
new file.

## ACS 2020-2024 5-year estimates, table-based Summary File

| | |
|---|---|
| Publisher | U.S. Census Bureau |
| Release | American Community Survey 2020-2024 5-year estimates, table-based Summary File |
| Landing page | https://www.census.gov/programs-surveys/acs/data/summary-file.html |
| Base URL | https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/ |
| Downloaded | 2026-10-23 |
| Licence | Public domain: a work of the U.S. federal government (17 U.S.C. §105). |
| Credit | U.S. Census Bureau, 2020-2024 American Community Survey 5-Year Estimates. Not affiliated with or endorsed by the U.S. Census Bureau. |
| Special values | [Notes on ACS Estimate and Annotation Values](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html) |
| Known errata | [Errata Note 148](https://www.census.gov/programs-surveys/acs/technical-documentation/errata/148.html): Wyandanch and Brentwood CDPs, New York, suppressed (14 Suffolk County tracts) |

| File in `raw/` | Path under the base URL | Bytes | Server last-modified | SHA-256 |
|---|---|---|---|---|
| `acsdt5y2024-b01003.dat` | `data/5YRData/` | 18,313,708 | 2026-01-29 12:31:45 GMT | `38d1a992bb058d184009b10b9b34987279aee575e4323165cfb5706c69b6ca90` |
| `acsdt5y2024-b01001.dat` | `data/5YRData/` | 200,356,282 | 2026-01-29 12:30:41 GMT | `1637b18a96881b81e050df1cd3d5ac38a33208b9b69b40e1dbeb3c4e13718f0e` |
| `acsdt5y2024-b19013.dat` | `data/5YRData/` | 17,917,916 | 2026-01-29 12:57:38 GMT | `b25a176b0e6c339b6f3a2a0d3d8446bf06f5f080b4395993ec9a8313efb1c229` |
| `acsdt5y2024-b17001.dat` | `data/5YRData/` | 118,607,125 | 2026-01-29 12:50:38 GMT | `707adda8aaff136382f4fe0858617d09062da48b1a3d2ab2e9a1047def09b531` |
| `acsdt5y2024-b15003.dat` | `data/5YRData/` | 92,292,840 | 2026-01-29 12:48:58 GMT | `d0c8609e958022459215c8a31d7452ef7528ee8dd70fbb6f9a99de0f491f42d7` |
| `acsdt5y2024-b25077.dat` | `data/5YRData/` | 18,496,426 | 2026-01-29 13:13:51 GMT | `89eb2153764a2330b23959d8bbc29b3a8f3016f087b990f2a8ea0d5096d9a816` |
| `Geos20245YR.txt` | `documentation/` | 90,707,242 | 2026-01-22 12:15:04 GMT | `b87a1d1a4db9f826d0d133d20cbf7d011932f9ec2cfa74eacf8c9cf387aea344` |
| `ACS20245YR_Table_Shells.txt` | `documentation/` | 5,622,840 | 2026-01-22 12:15:03 GMT | `5b46f4af873744a415c4974204010db976e2a61ff916674732f81c496a6b517d` |

### Facts about these files

Profiled on 2026-10-23. The recipes check them.

- **Format:** each table file is pipe-delimited, with `GEO_ID`, then
  `<table>_E<nnn>` (estimate) and `<table>_M<nnn>` (margin of error) for
  every variable, for every geography Census publishes the table for.
- **Geographic components:** `Geos20245YR.txt` has 616,690 geographies. It
  includes geographic components (urban and rural parts of an area, for
  example), and the shared views keep only component `00`, the whole area.
  At that component it has 1 nation, 52 states (the 50 states, DC and Puerto
  Rico), 3,222 counties and 85,382 census tracts. All six tables have a row
  for every one of them.
- **Values:** every value is a whole number. The special values that occur
  at these geographies:
  - estimates: `-666666666`;
  - margins of error: `-222222222`, `-333333333` and `-555555555`.
- **Open-ended medians,** where the margin of error is `-333333333`:
  - B19013: `2499` (under 2,500) and `250001` (250,000 or more);
  - B25077: `9999` (under 10,000) and `2000001` (2,000,000 or more).
- **The table shells** have 28,626 rows for 1,199 tables. 189 rows are
  headings with no variable ID (line numbers such as `0.5`). The other
  28,437 rows are one per variable.
