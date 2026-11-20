"""Download this project's raw file into raw/ and check it.

Run it from this folder before `useful-views sync`:

    uv run python fetch_raw.py

FAS serves only the latest PSD snapshot at its download URL and replaces it
every month. So this works only until FAS publishes the next snapshot; after
that, the download no longer matches the SHA-256 below. Keep your copy of
raw/psd_alldata_csv_2026-11-17.zip: it can't be downloaded again. To move to
a newer snapshot, see README.md. Uses only the Python standard library.
"""

import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://apps.fas.usda.gov/psdonline/downloads/psd_alldata_csv.zip"
NAME = "psd_alldata_csv_2026-11-17.zip"  # named for the snapshot's server date
SIZE = 10459432
SHA256 = "a293f2b05b1b7b185d7fdb7e1a562c43e6a0f190c6bf0e03fbe3df876286bd32"

RAW = Path(__file__).resolve().parent / "raw"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    RAW.mkdir(exist_ok=True)
    target = RAW / NAME
    if target.is_file() and target.stat().st_size == SIZE and sha256(target) == SHA256:
        print(f"  {NAME}: already here and correct")
        return 0
    partial = target.with_name(NAME + ".part")
    try:
        with urllib.request.urlopen(URL, timeout=120) as response:
            served = response.headers.get("Last-Modified", "unknown")
            partial.write_bytes(response.read())
    except (urllib.error.URLError, OSError) as exc:
        partial.unlink(missing_ok=True)
        print(f"  Could not download {URL} ({getattr(exc, 'reason', exc)}). Check your connection and try again.")
        return 1
    if sha256(partial) != SHA256:
        kept = RAW / "psd_alldata_csv_download.zip"
        partial.replace(kept)
        print(
            f"  The file at {URL} is not the 2026-11-17 snapshot (the server dates it {served}).\n"
            "  Either FAS has published a newer snapshot, so this one can no longer be downloaded,\n"
            "  or the download was damaged or replaced on the way (a proxy or maintenance page).\n"
            f"  It is kept as raw/{kept.name} to look at. Use a kept copy of {NAME}, or move the\n"
            "  project to the new snapshot as README.md describes."
        )
        return 1
    partial.replace(target)
    print(f"  {NAME}: downloaded and checked. Next: uv run useful-views sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
