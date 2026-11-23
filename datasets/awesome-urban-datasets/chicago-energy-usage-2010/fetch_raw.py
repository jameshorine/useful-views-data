"""Download this project's raw file into raw/ and check it.

Run it from this folder before `useful-views sync`:

    uv run python fetch_raw.py

The City of Chicago publishes Energy Usage 2010 as dataset 8yq3-m6wp on its data
portal. The data has not changed since 2013, so the portal's SODA2 endpoint
serves the same bytes for the query below (every row, in the portal's row
order). The file must match the SHA-256 below.

The portal sometimes answers with a temporary error, so the download is retried.
Set SOCRATA_APP_TOKEN to send an app token, which raises the portal's rate
limits. It is optional, and must never be committed.

Uses the Python standard library plus certifi's certificates. The portal's
certificate chain ends at GlobalSign Root R46, which some Python installations
don't have (on macOS, /etc/ssl/cert.pem lacks it).
"""

import hashlib
import http.client
import os
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

URL = "https://data.cityofchicago.org/resource/8yq3-m6wp.csv?$limit=100000&$order=:id"
NAME = "energy_usage_2010.csv"
SIZE = 37004866
SHA256 = "6e59d593ef8c0a21aea92fcea363bcbb1770fdad221e2f8d2ca199ee9391802b"  # also in recipes/energy_usage_2010/01_type_and_check.py
TRIES = 5
RETRY = (429, 500, 502, 503, 504)  # rate limited, or a temporary portal error

RAW = Path(__file__).resolve().parent / "raw"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(target: Path) -> None:
    """Save URL to target, retrying the portal's temporary errors."""
    headers = {"User-Agent": "useful-views-data fetch_raw.py"}
    if token := os.environ.get("SOCRATA_APP_TOKEN"):
        headers["X-App-Token"] = token
    for attempt in range(1, TRIES + 1):
        try:
            request = urllib.request.Request(URL, headers=headers)
            with urllib.request.urlopen(request, timeout=300, context=CONTEXT) as response, open(target, "wb") as out:
                got = 0
                while chunk := response.read(1 << 20):
                    out.write(chunk)
                    got += len(chunk)
                if response.length:  # a Content-Length was sent and not reached: the transfer was cut off
                    raise ConnectionError(f"cut off after {got:,} of {got + response.length:,} bytes")
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
        print(f"  The download failed ({why}, try {attempt} of {TRIES}); trying again in {wait} s")
        time.sleep(wait)


def main() -> int:
    RAW.mkdir(exist_ok=True)
    target = RAW / NAME
    if target.is_file() and target.stat().st_size == SIZE and sha256(target) == SHA256:
        print(f"  {NAME}: already here and correct")
        return 0
    partial = target.with_name(NAME + ".part")
    try:
        download(partial)
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, ssl.SSLCertVerificationError):
            print(f"  Could not check the portal's certificate ({reason}).")
            print("  Run it as `uv run python fetch_raw.py`, which uses certifi's certificates.")
        else:
            print(f"  Could not download {NAME} ({reason}). Check your connection and try again.")
        return 1
    if partial.stat().st_size == SIZE and sha256(partial) == SHA256:
        partial.replace(target)
        print(f"  {NAME}: downloaded and checked. Next: uv run useful-views sync")
        return 0
    kept = RAW / "energy_usage_2010_download.csv"
    partial.replace(kept)
    print(f"  The portal served a different file ({kept.stat().st_size:,} bytes, SHA-256 {sha256(kept)}).")
    print(f"  It is kept as raw/{kept.name} to look at; see README.md, 'If the download no longer matches'.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
