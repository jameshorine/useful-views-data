"""Download this project's raw file into raw/ and check it.

Run it from this folder before `useful-views sync`:

    uv run python fetch_raw.py

The Urban Traffic Speed Dataset of Guangzhou is one file, Data.zip, on Zenodo
(record 1205229, DOI 10.5281/zenodo.1205229). Zenodo doesn't change a published
file, and the record has only this version, so the file must match the SHA-256
below. Zenodo publishes its MD5, which this script checks too.

Temporary errors are retried. Uses the Python standard library plus certifi's
certificates, as the other projects here do.
"""

import hashlib
import http.client
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    import certifi

    CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # run outside the project's environment: Python's own certificates
    CONTEXT = ssl.create_default_context()

URL = "https://zenodo.org/records/1205229/files/Data.zip?download=1"
NAME = "Data.zip"
SIZE = 17562786
SHA256 = "4bf27e535928df9abbbde7cdb26075f11b1d70ab2d5a4e71107272e1c4add299"  # also in recipes/speeds/01_extract_csvs.py
MD5 = "9ea898ba4b03043ad5f60d9c7b881c44"  # as Zenodo lists it
TRIES = 5
RETRY = (429, 500, 502, 503, 504)  # rate limited, or a temporary server error

RAW = Path(__file__).resolve().parent / "raw"


def digests(path: Path) -> tuple[str, str]:
    sha256, md5 = hashlib.sha256(), hashlib.md5()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            sha256.update(chunk)
            md5.update(chunk)
    return sha256.hexdigest(), md5.hexdigest()


def download(target: Path) -> None:
    """Save URL to target, retrying temporary errors."""
    request = urllib.request.Request(URL, headers={"User-Agent": "useful-views-data fetch_raw.py"})
    for attempt in range(1, TRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=300, context=CONTEXT) as response, open(target, "wb") as out:
                while chunk := response.read(1 << 20):
                    out.write(chunk)
                if response.length:  # a Content-Length was sent and not reached: the transfer was cut off
                    raise http.client.IncompleteRead(b"", response.length)
            return
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRY or attempt == TRIES:
                raise
            why = f"HTTP {exc.code}"
        except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:  # reset, timeout, cut off
            reason = getattr(exc, "reason", exc)
            if attempt == TRIES or isinstance(reason, ssl.SSLCertVerificationError):  # won't fix itself
                raise
            why = str(reason) or type(reason).__name__
        wait = 2**attempt
        print(f"  Zenodo did not answer ({why}, try {attempt} of {TRIES}); trying again in {wait} s")
        time.sleep(wait)


def main() -> int:
    RAW.mkdir(exist_ok=True)
    target = RAW / NAME
    if target.is_file() and target.stat().st_size == SIZE and digests(target) == (SHA256, MD5):
        print(f"  {NAME}: already here and correct")
        return 0
    partial = target.with_name(NAME + ".part")
    try:
        download(partial)
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, ssl.SSLCertVerificationError):
            print(f"  Could not check Zenodo's certificate ({reason}).")
            print("  Run it as `uv run python fetch_raw.py`, which uses certifi's certificates.")
        else:
            print(f"  Could not download {NAME} ({reason}). Check your connection and try again.")
        return 1
    if partial.stat().st_size == SIZE and digests(partial) == (SHA256, MD5):
        partial.replace(target)
        print(f"  {NAME}: downloaded and checked. Next: uv run useful-views sync")
        return 0
    kept = RAW / "Data_download.zip"
    partial.replace(kept)
    sha256, md5 = digests(kept)
    print(f"  Zenodo served a different file ({kept.stat().st_size:,} bytes, SHA-256 {sha256}, MD5 {md5}).")
    print(f"  It is kept as raw/{kept.name} to look at. Zenodo doesn't change published files, so check the URL.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
