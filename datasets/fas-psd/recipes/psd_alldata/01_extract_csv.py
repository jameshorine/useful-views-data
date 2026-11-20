import hashlib
import zipfile

ZIP = "raw/psd_alldata_csv_2026-11-17.zip"
SHA256 = "a293f2b05b1b7b185d7fdb7e1a562c43e6a0f190c6bf0e03fbe3df876286bd32"  # as in fetch_raw.py and sources.toml

with open(ZIP, "rb") as file:
    actual = hashlib.sha256(file.read()).hexdigest()
assert actual == SHA256, f"{ZIP} is not the 2026-11-17 snapshot (SHA-256 {actual}). Run fetch_raw.py."

with zipfile.ZipFile(ZIP) as archive:
    assert archive.namelist() == ["psd_alldata.csv"], f"Unexpected zip contents: {archive.namelist()}"
    archive.extract("psd_alldata.csv", "work/psd_alldata")
