"""Download this project's raw file into raw/ and check it.

Run it from this folder before `useful-views sync`:

    uv run python fetch_raw.py

FAS replaces the file at its main download URL at every PSD release, at least
once a month, but keeps each month's last file in a monthly archive. So
this script downloads the 2026-11-17 snapshot from the November 2026 archive,
and tries the main URL only if the archive is unavailable. Either way, the
file must match the SHA-256 below. Uses only the Python standard library.
"""

import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

URLS = [
    "https://apps.fas.usda.gov/psdonline/downloads/archives/2026/11/psd_alldata_csv.zip",  # FAS's monthly archive
    "https://apps.fas.usda.gov/psdonline/downloads/psd_alldata_csv.zip",  # latest release only
]
NAME = "psd_alldata_csv_2026-11-17.zip"  # named for the snapshot's server date
SIZE = 10459432
SHA256 = "a293f2b05b1b7b185d7fdb7e1a562c43e6a0f190c6bf0e03fbe3df876286bd32"  # also in recipes/psd_alldata/01_extract_csv.py

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
    problems = []
    for url in URLS:
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                served = response.headers.get("Last-Modified", "unknown")
                partial.write_bytes(response.read())
        except (urllib.error.URLError, OSError) as exc:
            problems.append(f"{url}: could not download ({getattr(exc, 'reason', exc)})")
            continue
        if sha256(partial) == SHA256:
            partial.replace(target)
            print(f"  {NAME}: downloaded from {url} and checked. Next: uv run useful-views sync")
            return 0
        problems.append(f"{url}: a different file (dated {served}), not the 2026-11-17 snapshot")
    if partial.exists():
        kept = RAW / "psd_alldata_csv_download.zip"
        partial.replace(kept)
        problems.append(f"the last download is kept as raw/{kept.name} to look at")
    print(f"  Could not get {NAME}:", *(f"  - {p}" for p in problems), sep="\n")
    print("  Check your connection and try again, or move the project to a newer snapshot as README.md describes.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
