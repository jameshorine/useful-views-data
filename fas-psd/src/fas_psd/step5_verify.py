"""Step 4: compare the outputs with the committed datapackage.json.

Checks the hash, size and row count of every output against the version of
datapackage.json committed in git (HEAD), and reports what changed. The
build commit is ignored, since it changes even when the data doesn't.

In a full build this only reports: outputs are sometimes meant to change.
Run it on its own with --check to fail on any difference:

    uv run python -m fas_psd.step4_verify --check
"""

import argparse
import json
import subprocess
import sys

from fas_psd.config import DATAPACKAGE_PATH, PROJECT_ROOT
from fas_psd.step3_datapackage import git


def fingerprints(package: dict) -> dict[str, dict]:
    """Hash, bytes and rows for every output, keyed by its path in the project."""
    release_dir = DATAPACKAGE_PATH.parent.relative_to(PROJECT_ROOT)
    files = {
        str(release_dir / r["path"]): {"hash": r["hash"], "bytes": r["bytes"]}
        for r in package["resources"]
    }
    files.update(package["build"]["intermediate"])
    return {
        path: {**record, "rows": package["build"]["rows"].get(path)}
        for path, record in files.items()
    }


def compare() -> list[str] | None:
    """Changed outputs, or None if there is no committed datapackage.json to compare with."""
    path_in_git = f"HEAD:./{DATAPACKAGE_PATH.relative_to(PROJECT_ROOT)}"
    try:
        committed = json.loads(git("show", path_in_git))
    except (OSError, subprocess.CalledProcessError):
        return None

    old = fingerprints(committed)
    new = fingerprints(json.loads(DATAPACKAGE_PATH.read_text()))

    changed = []
    for path in sorted(old.keys() | new.keys()):
        if path not in old:
            changed.append(f"  NEW        {path}")
        elif path not in new:
            changed.append(f"  REMOVED    {path}")
        elif old[path] != new[path]:
            diffs = ", ".join(
                f"{key} {old[path][key]} -> {new[path][key]}"
                for key in ("hash", "bytes", "rows")
                if old[path][key] != new[path][key]
            )
            changed.append(f"  CHANGED    {path}: {diffs}")
    return changed


def run(force: bool = False) -> bool:
    """Print what changed. Returns True if the outputs match the committed record."""
    changed = compare()
    if changed is None:
        print("No committed datapackage.json to compare with; skipped.")
        return False
    if changed:
        print("Differs from the committed datapackage.json:", *changed, sep="\n")
        return False
    print("Unchanged: every output matches the committed datapackage.json.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit with an error unless everything matches")
    args = parser.parse_args()
    if not run() and args.check:
        sys.exit(1)


if __name__ == "__main__":
    main()
