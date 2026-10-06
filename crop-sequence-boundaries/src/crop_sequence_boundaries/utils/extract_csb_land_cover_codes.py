import csv
import re

import polars as pl
from bs4 import BeautifulSoup

from crop_sequence_boundaries.config import (
    METADATA_PATH,
    METADATA_SHA256,
    OUT_DIR,
    VIEWS_DIR,
    require_file,
)

# Paths to write to

FILE_NAME = "land_cover_codes"

CSV_PATH = OUT_DIR / f"{FILE_NAME}.csv"
PARQUET_PATH = VIEWS_DIR / f"{FILE_NAME}.parquet"


def extract_land_cover(html: bytes) -> list[tuple[int, str]]:
    soup = BeautifulSoup(html, "html.parser")
    blocks = [
        block.get_text()
        for block in soup.find_all("pre")
        if "Categorization Code" in block.get_text()
        and "Land Cover" in block.get_text()
    ]
    if len(blocks) != 1:
        raise ValueError("Expected exactly one land-cover dictionary.")

    rows = []
    codes = set()

    for line in blocks[0].splitlines():
        line = line.strip()
        if not line.startswith('"'):
            continue

        match = re.fullmatch(r'"(\d+)"\s+(.+)', line)
        if match is None:
            raise ValueError(f"Unexpected dictionary row: {line!r}")

        code = int(match.group(1))
        name = match.group(2).strip()

        if not 0 <= code <= 255 or code in codes or not name:
            raise ValueError(f"Invalid or duplicate dictionary row: {line!r}")

        codes.add(code)
        rows.append((code, name))

    if not rows:
        raise ValueError("No land-cover codes found.")

    return sorted(rows)


def main() -> None:
    # Parse the archived metadata from the release zip, not the live web page.
    # The live page can change; see in/SOURCES.md.
    require_file(METADATA_PATH, METADATA_SHA256)
    rows = extract_land_cover(METADATA_PATH.read_bytes())

    output = CSV_PATH
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(["land_cover_code", "land_cover_name"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} land-cover codes to {output}")

    parquet_output = PARQUET_PATH
    parquet_output.parent.mkdir(parents=True, exist_ok=True)
    table = pl.DataFrame(
        rows,
        schema={"land_cover_code": pl.Int64, "land_cover_name": pl.String},
        orient="row",
    )
    table.write_parquet(parquet_output)
    print(f"Wrote {len(rows)} land-cover codes to {parquet_output}")


if __name__ == "__main__":
    main()
