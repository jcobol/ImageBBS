"""Automate an overlay metadata refresh and baseline comparison."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from . import ml_extra_snapshot_guard
from .ml_extra.baseline import run_baseline_workflow
from .ml_extra.sanity import reporting as sanity_reporting

# Why: Expose defaults and entry points so automation can discover the refresh pipeline helpers programmatically.
__all__ = ["DEFAULT_BASELINE", "parse_args", "main"]

DEFAULT_BASELINE = ml_extra_snapshot_guard.DEFAULT_BASELINE


# Why: Provide a CLI-friendly parsing layer so automation can supply custom paths and toggles.
def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Return parsed command-line arguments for the refresh pipeline."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overlay",
        type=Path,
        default=None,
        help="Override the default ml.extra binary path",
    )
    parser.add_argument(
        "--metadata-json",
        type=Path,
        default=DEFAULT_BASELINE,
        help=(
            "Destination for the refreshed overlay metadata snapshot."
            " Defaults to docs/porting/artifacts/ml-extra-overlay-metadata.json."
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help=(
            "Baseline metadata snapshot to compare against."
            " Defaults to docs/porting/artifacts/ml-extra-overlay-metadata.json."
        ),
    )
    parser.add_argument(
        "--if-changed",
        action="store_true",
        help="Only overwrite the metadata JSON when the contents change.",
    )
    return parser.parse_args(argv)


# Why: Drive the refresh pipeline end-to-end so CI can enforce overlay metadata drift detection.
def main(argv: List[str] | None = None) -> int:
    """Entry point for the ``ml_extra_refresh_pipeline`` CLI."""

    args = parse_args(argv)
    try:
        result = run_baseline_workflow(
            overlay_path=args.overlay,
            baseline_path=args.baseline,
            metadata_path=args.metadata_json,
            metadata_only_if_changed=args.if_changed,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error

    metadata_path = result.metadata_path or args.metadata_json
    if args.if_changed:
        if result.metadata_updated:
            print(f"Metadata snapshot updated: {metadata_path}")
        else:
            print(f"Metadata snapshot already up to date: {metadata_path}")
    else:
        print(f"Metadata snapshot written to: {metadata_path}")

    diff = result.diff
    baseline_path = result.baseline_path or args.baseline
    if diff is None:
        raise SystemExit(
            "baseline comparison requested but metadata snapshot is unavailable"
        )

    print(sanity_reporting.render_diff_summary(baseline_path, diff))
    matches = diff.matches
    return 0 if matches else 1


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())
