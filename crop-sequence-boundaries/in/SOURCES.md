# Sources

Where every input in `in/` came from. Inputs are read-only: scripts read them, nothing writes to them. Values marked *checked* are also in [`config.py`](../src/crop_sequence_boundaries/config.py), and the scripts stop if the data doesn't match.

## Crop Sequence Boundaries 2018–2025 (rev23)

| | |
|---|---|
| Publisher | USDA National Agricultural Statistics Service (NASS) |
| Release | 2025 Crop Sequence Boundaries (2018–2025), revision 23 |
| Publication date | 2026-03-27 (from the metadata) |
| Landing page | https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/index.php |
| Download | https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/datasets/NationalCSB_2018-2025_rev23.zip |
| Server last-modified | 2026-05-15 17:58:04 GMT (ETag `"dffef247-651def4540300"`) |
| Zip size | 3,758,027,335 bytes |
| Zip SHA256 | `32c5e138141a1526ee356c8d8c8888844b5531fcca8ca4ac0b36ba37d7c087bb` |
| Downloaded | 2026-10-06. First downloaded on or before 2026-09-29; the 2026-10-06 copy was compared to the existing `.gdb` and all 63 files match (name, size, CRC). |
| Licence | Public domain. The metadata's Use_Constraints: "provided to the public as is and are considered public domain and free to redistribute. The USDA NASS does not warrant any conclusions drawn from these data." The metadata file itself has "No restrictions on the distribution or use", which covers the two `.htm` copies committed here. |
| Credit | USDA National Agricultural Statistics Service, 2025 Crop Sequence Boundaries (2018–2025), revision 23, published 2026-03-27. Not endorsed by USDA. |

The zip contains:

| Zip entry | Saved as | In git |
|---|---|---|
| `NationalCSB_2018-2025_rev23/CSB1825.gdb/` | `in/CSB1825.gdb/` | No (5.7 GB, gitignored) |
| `NationalCSB_2018-2025_rev23/NationalCSB_2018-2025_rev23_metadata.htm` | `in/csb_2025_metadata.htm` | Yes |

### `CSB1825.gdb`, checked

| | |
|---|---|
| Layer | `national1825` (MultiPolygon) |
| Features | 15,973,095 |
| States (`STATEFIPS`) | 48 |
| CRS | NAD83 / Conus Albers, EPSG:5070 |

### `csb_2025_metadata.htm`, checked

| | |
|---|---|
| SHA256 | `d4840e7bb11ef9e641e34a7092c5a57543dba8e3bdd1c8d84fc3b9c1da60730a` |
| Size | 79,567 bytes |
| Used for | the land-cover code dictionary (135 codes) |

This is the source of record for the land-cover lookup because it ships with the data it describes.

## Known discrepancy: the live metadata page

`in/csb_2025_metadata_web_2026-10-05.htm` is the live metadata page as saved on 2026-10-05 from
https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/metadata_Crop-Sequence-Boundaries-2025.htm
(SHA256 `c16606c53199148ad8d5f4e32e1cde2a4ca982af72b9c78b8b0712f28ea9d311`, 79,564 bytes).

It differs from the copy in the zip in two places:

- `Point_and_Vector_Object_Count` is **15,973,106** on the web page and **15,973,095** in the zip. The data has 15,973,095 features, so the zip copy is the one that matches.
- The zip copy starts with a UTF-8 byte-order mark (BOM); the web copy doesn't.

The 135 land-cover codes are identical in both. The web copy is kept only as evidence of this mismatch; no script reads it.

## Updating a source

1. Download the new release and record everything above for it: URL, server headers (`curl -sI <url>`), size, SHA256 (`shasum -a 256 <file>`) and the date.
2. Update the expected values in `config.py` to match.
3. Rebuild the views and note the change in the commit message.
