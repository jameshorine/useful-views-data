"""Step 4: describe the release's views as a Frictionless Data Package.

Writes useful-views/<release>/datapackage.json, the data bill of materials for
the release: each view's file, size, SHA256, fields, keys and joins, plus a
custom `build` section recording what the views were built from.

Field types come from the Parquet files themselves; descriptions and keys are
declared below. The build fails if a view has a column with no description,
so the documentation can't drift from the data.

The file has no timestamp, so rebuilding identical outputs from the same
commit writes an identical file. It is committed to git (the views are not);
check a rebuild with `git diff`.

Spec: https://datapackage.org
"""

import json
import platform
import subprocess
from importlib.metadata import version

import pyarrow as pa
import pyarrow.parquet as pq

from crop_sequence_boundaries.config import (
    DATAPACKAGE_PATH,
    EXPECTED_EPSG,
    METADATA_PATH,
    METADATA_SHA256,
    NATIONAL_PARQUET_PATH,
    OUTPUT_PATHS,
    PROJECT_ROOT,
    RELEASE,
    RELEASE_VIEWS_DIR,
    ZIP_NAME,
    ZIP_SHA256,
    require_outputs,
    sha256,
)

CSB_URL = "https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/"

# One entry per view: what a row is, its keys, and what each column means.
VIEWS = {
    "csb_field_year": {
        "description": "Land cover for every field, every year. One row per field per year.",
        "primaryKey": ["csb_id", "year"],
        "foreignKeys": {"csb_id": "csb_field", "land_cover_code": "land_cover_codes"},
        "fields": {
            "csb_id": "CSB field identifier. Specific to this release.",
            "year": "Crop year.",
            "land_cover_code": "Cropland Data Layer land-cover code for this field and year.",
        },
    },
    "csb_field": {
        "description": "One row per field: area, location and boundary.",
        "primaryKey": ["csb_id"],
        "foreignKeys": {"county_geoid": "county"},
        "fields": {
            "csb_id": "CSB field identifier. Specific to this release.",
            "county_geoid": "5-digit county GEOID (state FIPS + county FIPS).",
            "csb_acres": "Field area in acres.",
            "inside_x": f"Easting of a point inside the field, EPSG:{EXPECTED_EPSG} metres.",
            "inside_y": f"Northing of a point inside the field, EPSG:{EXPECTED_EPSG} metres.",
            "geometry": f"Field boundary as WKB (GeoParquet), EPSG:{EXPECTED_EPSG}.",
        },
    },
    "county": {
        "description": "One row per county.",
        "primaryKey": ["county_geoid"],
        "foreignKeys": {},
        "fields": {
            "county_geoid": "5-digit county GEOID (state FIPS + county FIPS).",
            "state_fips": "2-digit state FIPS code.",
            "county_fips": "3-digit county FIPS code.",
            "county_name": "County name.",
            "asd_code": "Agricultural statistics district: state FIPS + 2-digit ASD.",
        },
    },
    "land_cover_codes": {
        "description": "Names for Cropland Data Layer land-cover codes, from the release metadata.",
        "primaryKey": ["land_cover_code"],
        "foreignKeys": {},
        "fields": {
            "land_cover_code": "Cropland Data Layer land-cover code.",
            "land_cover_name": "Land-cover name.",
        },
    },
}

# What determines the outputs. Notebook or README edits don't make a build dirty.
BUILD_INPUTS = ("src", "in", "pyproject.toml", "uv.lock")


def table_schema_type(arrow_type: pa.DataType) -> str:
    if pa.types.is_integer(arrow_type):
        return "integer"
    if pa.types.is_floating(arrow_type):
        return "number"
    if pa.types.is_string(arrow_type) or pa.types.is_large_string(arrow_type):
        return "string"
    if pa.types.is_boolean(arrow_type):
        return "boolean"
    return "any"


def git(*args: str) -> str:
    """Run a git command in the project folder and return its output."""
    return subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def git_commit() -> str | None:
    """The commit the build ran from, with "-dirty" if build inputs had uncommitted changes."""
    try:
        commit = git("rev-parse", "--short", "HEAD")
        dirty = git("status", "--porcelain", "--", *BUILD_INPUTS)
    except (OSError, subprocess.CalledProcessError):
        return None
    return f"{commit}-dirty" if dirty else commit


def file_record(path) -> dict:
    return {
        "bytes": path.stat().st_size,
        "hash": f"sha256:{sha256(path)}",
    }


def geometry_properties(geo: dict, column: str) -> dict:
    """Describe a geometry column using the file's own GeoParquet metadata.

    Table Schema has no geometry type, so the column stays "any" and gains a
    custom `geoparquet` property, plus `rdfType` naming the OGC Simple Features
    class when the column holds a single geometry type.
    """
    meta = geo["columns"][column]
    crs = meta.get("crs", "missing")
    if crs == "missing":
        # GeoParquet: an absent crs means OGC:CRS84 (longitude/latitude).
        crs_id, crs_name = "OGC:CRS84", "WGS 84 (CRS84)"
    elif crs is None:
        crs_id, crs_name = None, "unknown"
    else:
        crs_id = f"{crs['id']['authority']}:{crs['id']['code']}" if "id" in crs else None
        crs_name = crs.get("name")

    properties = {
        "geoparquet": {
            "version": geo["version"],
            "encoding": meta["encoding"],
            "geometry_types": meta["geometry_types"],
            "crs": crs_id,
            "crs_name": crs_name,
            **({"bbox": meta["bbox"]} if "bbox" in meta else {}),
        }
    }
    types = {t.split()[0] for t in meta["geometry_types"]}  # "Polygon Z" -> "Polygon"
    if len(types) == 1:
        properties["rdfType"] = f"http://www.opengis.net/ont/sf#{types.pop()}"
    return properties


def resource(name: str, view: dict) -> dict:
    path = RELEASE_VIEWS_DIR / f"{name}.parquet"
    schema = pq.read_schema(path)
    geo = json.loads(schema.metadata[b"geo"]) if b"geo" in (schema.metadata or {}) else None

    columns = schema.names
    undocumented = [c for c in columns if c not in view["fields"]]
    stale = [c for c in view["fields"] if c not in columns]
    if undocumented or stale:
        raise ValueError(
            f"{name}: fields out of sync with {path.name}. "
            f"Undocumented: {undocumented}. Declared but missing: {stale}."
        )

    table_schema = {
        "fields": [
            {
                "name": field.name,
                "type": table_schema_type(field.type),
                "description": view["fields"][field.name],
                **(geometry_properties(geo, field.name) if geo and field.name in geo["columns"] else {}),
            }
            for field in schema
        ],
        "primaryKey": view["primaryKey"],
    }
    # The spec requires foreignKeys to be omitted, not empty, when there are none.
    if view["foreignKeys"]:
        table_schema["foreignKeys"] = [
            {"fields": [column], "reference": {"resource": target, "fields": [column]}}
            for column, target in view["foreignKeys"].items()
        ]

    return {
        "name": name,
        "type": "table",
        "path": path.name,
        "format": "parquet",
        **file_record(path),
        "description": view["description"],
        "schema": table_schema,
    }


def run(force: bool = False) -> None:
    """Always rewrites datapackage.json; it only describes outputs that exist."""
    require_outputs(OUTPUT_PATHS, before="steps 1-3")

    package = {
        "$schema": "https://datapackage.org/profiles/2.0/datapackage.json",
        "name": RELEASE.replace("_", "-"),
        "title": "Crop Sequence Boundaries 2018-2025 (rev23): tidy views",
        "description": (
            "Tidy views on the USDA NASS Crop Sequence Boundaries 2018-2025 release. "
            "Credit: USDA National Agricultural Statistics Service, 2025 Crop Sequence Boundaries (rev23). "
            "Not endorsed by USDA. See in/SOURCES.md in the useful-views-data repository for full provenance."
        ),
        "licenses": [
            {
                "name": "other-pd",
                "title": (
                    "Public domain. USDA NASS: \"provided to the public as is and are considered public "
                    "domain and free to redistribute. The USDA NASS does not warrant any conclusions "
                    "drawn from these data.\""
                ),
                "path": f"{CSB_URL}metadata_Crop-Sequence-Boundaries-2025.htm",
            }
        ],
        "sources": [
            {"title": f"USDA NASS {ZIP_NAME}", "path": f"{CSB_URL}datasets/{ZIP_NAME}"},
        ],
        "resources": [resource(name, view) for name, view in VIEWS.items()],
        # Custom section: not part of the Data Package spec, ignored by its tools.
        "build": {
            "commit": git_commit(),
            "inputs": {
                ZIP_NAME: f"sha256:{ZIP_SHA256}",
                METADATA_PATH.name: f"sha256:{METADATA_SHA256}",
            },
            "intermediate": {
                str(NATIONAL_PARQUET_PATH.relative_to(PROJECT_ROOT)): file_record(NATIONAL_PARQUET_PATH),
            },
            "rows": {
                str(path.relative_to(PROJECT_ROOT)): pq.ParquetFile(path).metadata.num_rows
                for path in OUTPUT_PATHS
            },
            "tools": {
                "python": platform.python_version(),
                **{name: version(name) for name in ("duckdb", "polars", "pyarrow")},
            },
        },
    }

    DATAPACKAGE_PATH.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {DATAPACKAGE_PATH}")


def main() -> None:
    run()


if __name__ == "__main__":
    main()
