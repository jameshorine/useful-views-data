"""Useful views on USDA FAS Production, Supply and Distribution (PSD).

`uv run fas-psd` runs every step in order. Each step can also be run on its
own, e.g. `uv run python -m fas_psd.step1_export_psd`.
"""

import argparse


def main() -> None:
    from fas_psd import step1_export_psd

    parser = argparse.ArgumentParser(description="Build every PSD view.")
    parser.add_argument("--force", action="store_true", help="replace existing outputs")
    args = parser.parse_args()

    steps = (step1_export_psd,)
    for step in steps:
        print(f"--- {step.__name__.rsplit('.', 1)[-1]}")
        step.run(args.force)
