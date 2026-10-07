"""Project paths and expected facts about the source data.

Paths are resolved from this file, not the working directory, so scripts
write to the same place no matter where they are run from.

Everything specific to a PSD snapshot lives here. Moving to a new snapshot
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

# PSD is a monthly snapshot: USDA overwrites old estimates, so the snapshot
# date is part of the data's identity. Every view built from it goes here.
SNAPSHOT_DATE = "2026-09-24"
RELEASE = f"psd_{SNAPSHOT_DATE}"
RELEASE_VIEWS_DIR = VIEWS_DIR / RELEASE

# --- Inputs ---

ZIP_URL = "https://apps.fas.usda.gov/psdonline/downloads/psd_alldata_csv.zip"
ZIP_PATH = IN_DIR / f"psd_alldata_csv_{SNAPSHOT_DATE}.zip"
ZIP_SHA256 = "dccef5678cffecc1e7722342396c751442eb245d06dff4498ec87c346908c41f"
CSV_NAME = "psd_alldata.csv"

EXPECTED_ROWS = 2_093_353
EXPECTED_COMMODITIES = 63
EXPECTED_COUNTRIES = 214
EXPECTED_ATTRIBUTES = 69
EXPECTED_UNITS = 11
EXPECTED_COMMODITY_ATTRIBUTES = 752
MARKET_YEARS = range(1960, 2027)

# --- Outputs ---

# Step 1: the source CSV as typed Parquet, all columns, unchanged. This is
# the release's reference view, not an intermediate, so it lives with the views.
PSD_PARQUET_PATH = RELEASE_VIEWS_DIR / "psd_alldata.parquet"

# Step 2: one row per (commodity, attribute) pair that PSD reports, with its unit.
COMMODITY_ATTRIBUTE_PATH = RELEASE_VIEWS_DIR / "commodity_attribute.parquet"

# Step 3: every country summed to one row per commodity, market year and attribute.
WORLD_BALANCE_PATH = RELEASE_VIEWS_DIR / "world_balance.parquet"

# Rates and ratios, not quantities: a sum across countries is meaningless, so
# world_balance leaves them out. 181 Extr. Rate, 182 Milling Rate, 183 Seed to
# Lint Ratio, 184 Yield, 195 Stocks-to-Use, 220 Annual % Change Per Cap. Cons.
NON_ADDITIVE_ATTRIBUTES = ("181", "182", "183", "184", "195", "220")

# Every view in the release, in the order step 4 documents them.
OUTPUT_PATHS = (PSD_PARQUET_PATH, COMMODITY_ATTRIBUTE_PATH, WORLD_BALANCE_PATH)

# Step 4: the release's Data Package descriptor, committed to git.
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
