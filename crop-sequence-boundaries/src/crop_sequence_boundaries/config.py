"""Project paths and expected facts about the source data.

Paths are resolved from this file, not the working directory, so scripts
write to the same place no matter where they are run from.

Everything specific to a CSB release lives here. Moving to a new release
means editing this file and in/SOURCES.md, not the pipeline steps.

The expected values below are copied from in/SOURCES.md. If you change a
source, update both.
"""

import hashlib
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IN_DIR = PROJECT_ROOT / "in"
OUT_DIR = PROJECT_ROOT / "out"
VIEWS_DIR = PROJECT_ROOT / "useful-views"

# Every view built from this release goes here. CSB IDs and land-cover codes
# are specific to a release, so releases never share a folder.
RELEASE = "csb_2025"
RELEASE_VIEWS_DIR = VIEWS_DIR / RELEASE

# --- Inputs ---

# Source zip. Not kept in the repo, so its hash is recorded rather than checked;
# CSB1825.gdb was verified against it file by file (see in/SOURCES.md).
ZIP_NAME = "NationalCSB_2018-2025_rev23.zip"
ZIP_SHA256 = "32c5e138141a1526ee356c8d8c8888844b5531fcca8ca4ac0b36ba37d7c087bb"

GDB_PATH = IN_DIR / "CSB1825.gdb"
GDB_LAYER = "national1825"
YEARS = range(2018, 2026)
EXPECTED_FEATURES = 15_973_095
EXPECTED_STATES = 48
EXPECTED_EPSG = 5070

# Metadata page shipped inside the same zip.
METADATA_PATH = IN_DIR / "csb_2025_metadata.htm"
METADATA_SHA256 = "d4840e7bb11ef9e641e34a7092c5a57543dba8e3bdd1c8d84fc3b9c1da60730a"

# --- Outputs ---

# Step 1: the source layer as GeoParquet, all columns, unchanged.
NATIONAL_PARQUET_PATH = OUT_DIR / f"{GDB_LAYER}.parquet"

# Step 2: the land-cover lookup.
LAND_COVER_PARQUET_PATH = RELEASE_VIEWS_DIR / "land_cover_codes.parquet"

# Step 3: the tidy views.
CSB_FIELD_YEAR_PATH = RELEASE_VIEWS_DIR / "csb_field_year.parquet"
CSB_FIELD_PATH = RELEASE_VIEWS_DIR / "csb_field.parquet"
COUNTY_PATH = RELEASE_VIEWS_DIR / "county.parquet"

OUTPUT_PATHS = (
    NATIONAL_PARQUET_PATH,
    LAND_COVER_PARQUET_PATH,
    CSB_FIELD_YEAR_PATH,
    CSB_FIELD_PATH,
    COUNTY_PATH,
)

# Step 4: the Frictionless Data Package describing the views, with checksums.
# The only file in useful-views/ that is committed to git.
DATAPACKAGE_PATH = RELEASE_VIEWS_DIR / "datapackage.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, expected_sha256: str) -> None:
    """Fail loudly if an input is missing or not the file we documented."""
    if not path.exists():
        raise FileNotFoundError(f"Missing input: {path}. See in/SOURCES.md.")
    actual = sha256(path)
    if actual != expected_sha256:
        raise ValueError(
            f"{path.name} does not match in/SOURCES.md.\n"
            f"  expected {expected_sha256}\n"
            f"  actual   {actual}"
        )


def require_outputs(paths: Iterable[Path], *, before: str) -> None:
    """Fail if an earlier step's outputs are missing."""
    missing = [p for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing {missing}. Run {before} first.")


def prepare_outputs(paths: Iterable[Path], force: bool) -> None:
    """Refuse to overwrite existing outputs unless force; create parent folders."""
    paths = list(paths)
    existing = [p for p in paths if p.exists()]
    if existing and not force:
        raise FileExistsError(f"Outputs already exist: {existing} (use --force)")
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
