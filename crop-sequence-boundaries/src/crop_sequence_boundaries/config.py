"""Project paths and expected facts about the source data.

Paths are resolved from this file, not the working directory, so scripts
write to the same place no matter where they are run from.

The expected values below are copied from in/SOURCES.md. If you change a
source, update both.
"""

import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IN_DIR = PROJECT_ROOT / "in"
OUT_DIR = PROJECT_ROOT / "out"
VIEWS_DIR = PROJECT_ROOT / "useful-views"

# Source: NationalCSB_2018-2025_rev23.zip
GDB_PATH = IN_DIR / "CSB1825.gdb"
GDB_LAYER = "national1825"
EXPECTED_FEATURES = 15_973_095
EXPECTED_STATES = 48
EXPECTED_EPSG = 5070

# Metadata page shipped inside the same zip.
METADATA_PATH = IN_DIR / "csb_2025_metadata.htm"
METADATA_SHA256 = "d4840e7bb11ef9e641e34a7092c5a57543dba8e3bdd1c8d84fc3b9c1da60730a"


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
