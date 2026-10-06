"""Useful views on USDA Crop Sequence Boundaries.

`uv run crop-sequence-boundaries` runs every step in order. Each step can
also be run on its own, e.g. `uv run python -m crop_sequence_boundaries.step2_land_cover_codes`.
"""

import argparse


def main() -> None:
    from crop_sequence_boundaries import (
        step1_export_national,
        step2_land_cover_codes,
        step3_tidy_views,
        step4_datapackage,
        step5_verify,
    )

    parser = argparse.ArgumentParser(description="Build every CSB view, steps 1-5.")
    parser.add_argument("--force", action="store_true", help="replace existing outputs")
    args = parser.parse_args()

    steps = (
        step1_export_national,
        step2_land_cover_codes,
        step3_tidy_views,
        step4_datapackage,
        step5_verify,
    )
    for step in steps:
        print(f"--- {step.__name__.rsplit('.', 1)[-1]}")
        step.run(args.force)
