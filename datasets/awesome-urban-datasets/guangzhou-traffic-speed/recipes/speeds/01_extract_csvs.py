import hashlib
import zipfile

ZIP = "raw/Data.zip"
SHA256 = "4bf27e535928df9abbbde7cdb26075f11b1d70ab2d5a4e71107272e1c4add299"  # as in fetch_raw.py and sources.toml
MEMBERS = ["Data/", "Data/day_information_table.csv", "Data/tensor.mat",
           "Data/time_information_table.csv", "Data/traffic_speed_data.csv"]
CSVS = ["Data/day_information_table.csv", "Data/time_information_table.csv", "Data/traffic_speed_data.csv"]

digest = hashlib.sha256()
with open(ZIP, "rb") as file:
    for chunk in iter(lambda: file.read(1 << 20), b""):
        digest.update(chunk)
if digest.hexdigest() != SHA256:  # not an assert: python -O would skip it
    raise SystemExit(f"{ZIP} is not the pinned Zenodo file (its SHA-256 is {digest.hexdigest()}). Run fetch_raw.py.")

with zipfile.ZipFile(ZIP) as archive:
    names = sorted(archive.namelist())
    assert names == sorted(MEMBERS), f"Unexpected zip contents: {names}"
    # tensor.mat holds the same observations as a 214 x 61 x 144 array (0 where missing), with 4,396 values that
    # differ slightly from the CSV's. The record calls the CSV the original data, so these views use it.
    for name in CSVS:
        archive.extract(name, "work/speeds")
