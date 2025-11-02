"""Automate an overlay metadata refresh and baseline comparison."""

from __future__ import annotations

import argparse
import json
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
    comparison_group = parser.add_mutually_exclusive_group()
    comparison_group.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help=(
            "Baseline metadata snapshot to compare against."
            " Defaults to docs/porting/artifacts/ml-extra-overlay-metadata.json when"
            " not running in metadata-only mode."
        ),
    )
    comparison_group.add_argument(
        "--metadata-only",
        action="store_true",
        help="Skip baseline comparison and only refresh overlay metadata.",
    )
    parser.add_argument(
        "--if-changed",
        action="store_true",
        help="Only overwrite the metadata JSON when the contents change.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the diff payload as JSON instead of a text summary",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Overwrite the baseline with the freshly generated snapshot",
    )
    namespace = parser.parse_args(argv)
    if not namespace.metadata_only and namespace.baseline is None:
        namespace.baseline = DEFAULT_BASELINE
    return namespace


# Why: Drive the refresh pipeline end-to-end so CI can enforce overlay metadata drift detection.
def main(argv: List[str] | None = None) -> int:
    """Entry point for the ``ml_extra_refresh_pipeline`` CLI."""

    args = parse_args(argv)
    if args.metadata_only and args.update_baseline:
        raise SystemExit("--update-baseline requires a baseline comparison")
    baseline_path = None if args.metadata_only else args.baseline
    try:
        result = run_baseline_workflow(
            overlay_path=args.overlay,
            baseline_path=baseline_path,
            metadata_path=args.metadata_json,
            metadata_only_if_changed=args.if_changed,
            update_baseline=args.update_baseline if not args.metadata_only else False,
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

    if args.metadata_only:
        return 0

    diff = result.diff
    baseline_path = result.baseline_path or baseline_path
    if diff is None:
        raise SystemExit(
            "baseline comparison requested but metadata snapshot is unavailable"
        )

    if args.json:
        print(json.dumps(diff.to_dict(), indent=2, sort_keys=True))
    else:
        print(sanity_reporting.render_diff_summary(baseline_path, diff))

    if args.update_baseline:
        if not args.json:
            if result.baseline_updated:
                print(f"Refreshed baseline snapshot at {baseline_path}")
            else:
                print(f"Baseline snapshot already up to date: {baseline_path}")
        return 0

    matches = diff.matches
    return 0 if matches else 1


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())
