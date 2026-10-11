"""Step 4: describe the release's views as a Frictionless Data Package.

Writes useful-views/<release>/datapackage.json, the data bill of materials for
the release: each view's file, size, SHA256, fields and keys, plus a custom
`build` section recording what the views were built from.

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

from fas_psd.config import (
    DATAPACKAGE_PATH,
    OUTPUT_PATHS,
    PROJECT_ROOT,
    RELEASE,
    RELEASE_VIEWS_DIR,
    SNAPSHOT_DATE,
    ZIP_PATH,
    ZIP_SHA256,
    ZIP_URL,
    require_outputs,
    sha256,
)
from fas_psd.step1_export_psd import KEY

# One entry per view: what a row is, its keys, and what each column means.
VIEWS = {
    "psd_alldata": {
        "description": (
            f"The PSD all-commodities file as published on {SNAPSHOT_DATE}, every column unchanged "
            "but typed. One row per commodity, country, market year and attribute."
        ),
        "primaryKey": list(KEY),
        "foreignKeys": {},
        "fields": {
            "Commodity_Code": "7-digit PSD commodity code, zero-padded (e.g. 0440000 Corn).",
            "Commodity_Description": "Commodity name. One name per Commodity_Code.",
            "Country_Code": (
                "2-character PSD country code, FIPS 10-4 style, not ISO 3166 (e.g. CH China, GM Germany). "
                "Includes aggregates such as E4 European Union that overlap their member countries, "
                "and historical entities such as UR Union of Soviet Socialist Republics that overlap their "
                "successors; summing countries can double count."
            ),
            "Country_Name": "Country or region name. One name per Country_Code.",
            "Market_Year": (
                "Marketing year the value applies to. Local marketing years start in different months "
                "for different commodities and countries; not a calendar year."
            ),
            "Calendar_Year": "Year the value was last revised, not the year it applies to.",
            "Month": "Month the value was last revised (1-12); 0 where PSD gives no month.",
            "Attribute_ID": "3-digit PSD attribute code, zero-padded (e.g. 028 Production).",
            "Attribute_Description": "Attribute name as PSD publishes it. One name per Attribute_ID.",
            "Unit_ID": "2-digit PSD unit code. One unit per (Commodity_Code, Attribute_ID).",
            "Unit_Description": "Unit name as PSD publishes it (e.g. (1000 MT), (MT/HA)). Never sum across units.",
            "Value": (
                "The value, in Unit_Description. The latest estimate as of the snapshot: PSD overwrites "
                "earlier estimates. 34% of values are zero; whether a zero means zero or not reported "
                "is not documented."
            ),
        },
    },
    "commodity_attribute": {
        "description": (
            "Every attribute PSD reports for each commodity, with its unit, as published. "
            "One row per commodity and attribute pair found in psd_alldata."
        ),
        "primaryKey": ["Commodity_Code", "Attribute_ID"],
        "foreignKeys": {},
        "fields": {
            "Commodity_Code": "7-digit PSD commodity code, zero-padded (e.g. 0440000 Corn).",
            "Commodity_Description": "Commodity name as PSD publishes it.",
            "Attribute_ID": "3-digit PSD attribute code, zero-padded (e.g. 028 Production).",
            "Attribute_Description": "Attribute name as PSD publishes it.",
            "Unit_Description": (
                "Unit of this attribute for this commodity, as PSD publishes it. The same attribute "
                "can have different units for different commodities (e.g. Production is 1000 MT for "
                "corn but 1000 480 lb. Bales for cotton)."
            ),
        },
    },
    "world_balance": {
        "description": (
            "Every country in psd_alldata summed to a world total. One row per commodity, market "
            "year and attribute. Rates and ratios are left out (Extr. Rate, Milling Rate, Seed to "
            "Lint Ratio, Yield, Stocks-to-Use, Annual % Change Per Cap. Cons.)."
        ),
        "primaryKey": ["Commodity_Code", "Market_Year", "Attribute_ID"],
        "foreignKeys": {},
        "fields": {
            "Commodity_Code": "7-digit PSD commodity code, zero-padded (e.g. 0440000 Corn).",
            "Commodity_Description": "Commodity name as PSD publishes it.",
            "Market_Year": (
                "Marketing year. Each country's local marketing year is summed as is, so world "
                "imports and exports don't match: compare TY Imports and TY Exports for trade."
            ),
            "Attribute_ID": "3-digit PSD attribute code, zero-padded (e.g. 028 Production).",
            "Attribute_Description": "Attribute name as PSD publishes it.",
            "Unit_Description": "Unit as PSD publishes it. Never sum across units.",
            "Value": (
                "Sum of Value over every country in psd_alldata, with no country dropped or adjusted. "
                "A few known cases count the same quantity twice; see the README's known overlaps."
            ),
            "n_countries": "Number of countries with a nonzero Value.",
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


def resource(name: str, view: dict) -> dict:
    path = RELEASE_VIEWS_DIR / f"{name}.parquet"
    schema = pq.read_schema(path)

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
        "title": f"USDA FAS Production, Supply and Distribution (PSD), {SNAPSHOT_DATE} snapshot",
        "description": (
            f"Views on the USDA FAS PSD all-commodities file as published on {SNAPSHOT_DATE}. "
            "PSD overwrites earlier estimates every month, so the snapshot date is part of the data's "
            "identity. The views are retyped and, in world_balance, summed by useful-views-data: they "
            "are not official USDA figures and are not endorsed by USDA. Credit: USDA Foreign "
            "Agricultural Service, PSD Online. See in/SOURCES.md in the useful-views-data repository "
            "for full provenance."
        ),
        "licenses": [
            {
                "name": "CC-BY-4.0",
                "title": (
                    "Creative Commons Attribution 4.0, as listed in FAS's data.gov record USDA-26341. "
                    "Also a work of the US federal government (17 U.S.C. §105)."
                ),
                "path": "https://creativecommons.org/licenses/by/4.0/",
            }
        ],
        "sources": [
            {"title": f"USDA FAS PSD Online, All Commodities (CSV), {SNAPSHOT_DATE}", "path": ZIP_URL},
        ],
        "resources": [resource(name, view) for name, view in VIEWS.items()],
        # Custom section: not part of the Data Package spec, ignored by its tools.
        "build": {
            "commit": git_commit(),
            "inputs": {
                ZIP_PATH.name: f"sha256:{ZIP_SHA256}",
            },
            "intermediate": {},
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
