"""Step 2: build the land-cover lookup from the release's metadata page.

Refuses to overwrite existing outputs; pass --force to replace them.
"""

import argparse
import re

import polars as pl
from bs4 import BeautifulSoup

from crop_sequence_boundaries.config import (
    LAND_COVER_CSV_PATH,
    LAND_COVER_PARQUET_PATH,
    METADATA_PATH,
    METADATA_SHA256,
    prepare_outputs,
    require_file,
)


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


def run(force: bool = False) -> None:
    # Parse the archived metadata from the release zip, not the live web page.
    # The live page can change; see in/SOURCES.md.
    require_file(METADATA_PATH, METADATA_SHA256)
    rows = extract_land_cover(METADATA_PATH.read_bytes())

    prepare_outputs([LAND_COVER_CSV_PATH, LAND_COVER_PARQUET_PATH], force)
    table = pl.DataFrame(
        rows,
        schema={"land_cover_code": pl.Int16, "land_cover_name": pl.String},
        orient="row",
    )
    table.write_csv(LAND_COVER_CSV_PATH) 
    table.write_parquet(LAND_COVER_PARQUET_PATH)
    print(f"Wrote {len(rows)} land-cover codes to {LAND_COVER_CSV_PATH}")
    print(f"Wrote {len(rows)} land-cover codes to {LAND_COVER_PARQUET_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="replace existing outputs")
    args = parser.parse_args()
    run(args.force)


if __name__ == "__main__":
    main()
