"""Download this project's raw Census files into raw/ and check them.

Run it from this folder before `useful-views sync`:

    python fetch_raw.py

Each file comes from the U.S. Census Bureau's ACS Summary File and is checked
against the size and SHA-256 recorded below (and in SOURCES.md). A file that
is already in raw/ and matches is not downloaded again; one that does not
match is downloaded again. Uses only the Python standard library.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF"

# File in raw/ -> (path under BASE, size in bytes, SHA-256). Keep in step with SOURCES.md.
FILES = {
    "acsdt5y2024-b01003.dat": ("data/5YRData/acsdt5y2024-b01003.dat", 18313708, "38d1a992bb058d184009b10b9b34987279aee575e4323165cfb5706c69b6ca90"),
    "acsdt5y2024-b01001.dat": ("data/5YRData/acsdt5y2024-b01001.dat", 200356282, "1637b18a96881b81e050df1cd3d5ac38a33208b9b69b40e1dbeb3c4e13718f0e"),
    "acsdt5y2024-b19013.dat": ("data/5YRData/acsdt5y2024-b19013.dat", 17917916, "b25a176b0e6c339b6f3a2a0d3d8446bf06f5f080b4395993ec9a8313efb1c229"),
    "acsdt5y2024-b17001.dat": ("data/5YRData/acsdt5y2024-b17001.dat", 118607125, "707adda8aaff136382f4fe0858617d09062da48b1a3d2ab2e9a1047def09b531"),
    "acsdt5y2024-b15003.dat": ("data/5YRData/acsdt5y2024-b15003.dat", 92292840, "d0c8609e958022459215c8a31d7452ef7528ee8dd70fbb6f9a99de0f491f42d7"),
    "acsdt5y2024-b25077.dat": ("data/5YRData/acsdt5y2024-b25077.dat", 18496426, "89eb2153764a2330b23959d8bbc29b3a8f3016f087b990f2a8ea0d5096d9a816"),
    "Geos20245YR.txt": ("documentation/Geos20245YR.txt", 90707242, "b87a1d1a4db9f826d0d133d20cbf7d011932f9ec2cfa74eacf8c9cf387aea344"),
    "ACS20245YR_Table_Shells.txt": ("documentation/ACS20245YR_Table_Shells.txt", 5622840, "5b46f4af873744a415c4974204010db976e2a61ff916674732f81c496a6b517d"),
}

RAW = Path(__file__).resolve().parent / "raw"
CHUNK = 1 << 20


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matches(path: Path, size: int, expected: str) -> bool:
    return path.is_file() and path.stat().st_size == size and sha256(path) == expected


def download(url: str, target: Path, size: int) -> None:
    """Stream url to target through a temporary file, showing progress."""
    partial = target.with_name(target.name + ".part")
    done = 0
    with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as out:
        for chunk in iter(lambda: response.read(CHUNK), b""):
            out.write(chunk)
            done += len(chunk)
            print(f"\r  {target.name}: {done / 1e6:,.1f} of {size / 1e6:,.1f} MB", end="", flush=True)
    print()
    partial.replace(target)


def main() -> int:
    RAW.mkdir(exist_ok=True)
    failed = []
    for name, (path, size, expected) in FILES.items():
        target = RAW / name
        if matches(target, size, expected):
            print(f"  {name}: already here and correct")
            continue
        try:
            download(f"{BASE}/{path}", target, size)
        except OSError as exc:
            print(f"\n  {name}: download failed ({exc})")
            failed.append(name)
            continue
        if not matches(target, size, expected):
            print(f"  {name}: does not match SOURCES.md (size or SHA-256); Census may have replaced the file")
            failed.append(name)
    if failed:
        print(f"Problems with {len(failed)} file(s): {', '.join(failed)}")
        return 1
    print(f"All {len(FILES)} raw files are in raw/ and match SOURCES.md. Next: uv run useful-views sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
