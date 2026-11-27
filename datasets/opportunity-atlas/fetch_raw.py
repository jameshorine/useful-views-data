"""Download this project's raw files into raw/ and check them.

Run it from this folder before `useful-views sync`:

    uv run python fetch_raw.py

Opportunity Insights publishes The Opportunity Atlas's tables as CSV files on
its website. Each file must match the size and SHA-256 below (also in
sources.toml and the recipe steps). A file already in raw/ that matches is not
downloaded again.

The site turns away Python's default User-Agent with HTTP 403, so the script
sends its own. A temporary error is retried. Uses the Python standard library,
plus certifi's certificates when they are installed.
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

BASE = "https://opportunityinsights.org/wp-content/uploads"

# File in raw/ -> (path under BASE, size in bytes, SHA-256). Keep in step with sources.toml and the recipe steps.
FILES = {
    "tract_outcomes_simple.csv": ("2018/10/tract_outcomes_simple.csv", 34406499, "d246a041179cac832983f1814725e91c8f99adc41d31b06ee3ac9b4f662be10b"),
    "county_outcomes_simple.csv": ("2018/10/county_outcomes_simple.csv", 1731009, "c355f7cade477637edb57a09b81e11bc102cb61d76a4758bea640590f51a5895"),
    "cz_outcomes_simple.csv": ("2018/10/cz_outcomes_simple.csv", 448750, "b096cdb13e1e94f7fac740d7d0d1cbb7cd09eafc6e5cb0774a06d39a9a4c0c84"),
    "tract_covariates.csv": ("2018/10/tract_covariates.csv", 24898454, "270297349f75a60b39873ed5b71184ca68fc297397feeab7755221e1f6a82319"),
    "cty_covariates.csv": ("2018/12/cty_covariates.csv", 1125129, "4eb4f2f89292eb8f1d299bf104f870247ec432fe572a46e42fda89ec5ac98416"),
    "cz_covariates.csv": ("2018/12/cz_covariates.csv", 270104, "e00c7e08bfd208d4c881d7a82b34a9a53d62b3fab79e0ab6131c4abf5828c41c"),
    "national_percentile_outcomes.csv": ("2018/10/national_percentile_outcomes.csv", 2553447, "058d0065412855c72899af390ebe9348e79cd0eeeee6d2f9d639db6512b7c873"),
    "pctile_to_dollar_cw.csv": ("2018/10/pctile_to_dollar_cw.csv", 9538, "89af2fc8d4a330a6ba36e4128f172f200c53f8e7f5175a392f8ac5f2db23cdb0"),
    "us_tract_2010_2020_crosswalk.csv": ("2021/05/us_tract_2010_2020_crosswalk.csv", 7121815, "fe0f029d60bcfa2964faf4503438167f72b20124b8cfa26ebea3f9296fb0fbcb"),
}
TRIES = 5
RETRY = (429, 500, 502, 503, 504)  # rate limited, or a temporary server error

RAW = Path(__file__).resolve().parent / "raw"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matches(path: Path, size: int, expected: str) -> bool:
    return path.is_file() and path.stat().st_size == size and sha256(path) == expected


def download(url: str, target: Path) -> None:
    """Save url to target, retrying temporary errors."""
    headers = {"User-Agent": "useful-views-data fetch_raw.py"}
    for attempt in range(1, TRIES + 1):
        try:
            request = urllib.request.Request(url, headers=headers)
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


def fetch(name: str, path: str, size: int, expected: str) -> bool:
    target = RAW / name
    if matches(target, size, expected):
        print(f"  {name}: already here and correct")
        return True
    partial = target.with_name(name + ".part")
    try:
        download(f"{BASE}/{path}", partial)
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, ssl.SSLCertVerificationError):
            print(f"  {name}: could not check the site's certificate ({reason}).")
            print("  Run it as `uv run python fetch_raw.py`, which uses certifi's certificates.")
        else:
            print(f"  {name}: could not download it ({reason}). Check your connection and try again.")
        return False
    if matches(partial, size, expected):
        partial.replace(target)
        print(f"  {name}: downloaded and checked")
        return True
    kept = target.with_name(target.stem + "_download" + target.suffix)
    partial.replace(kept)
    print(f"  {name}: the site served a different file ({kept.stat().st_size:,} bytes, SHA-256 {sha256(kept)}).")
    print(f"  It is kept as raw/{kept.name} to look at; see README.md, 'If a download no longer matches'.")
    return False


def main() -> int:
    RAW.mkdir(exist_ok=True)
    failed = [name for name, pin in FILES.items() if not fetch(name, *pin)]
    if failed:
        print(f"  Problems with {len(failed)} of {len(FILES)} files: {', '.join(failed)}")
        return 1
    print("  All files are here and correct. Next: uv run useful-views sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
