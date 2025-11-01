"""Snapshot guard that compares recovered metadata with the committed baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from . import ml_extra_metadata_io
from .ml_extra.sanity import core as sanity_core
from .ml_extra.sanity import reporting as sanity_reporting

__all__ = [
    "DEFAULT_BASELINE",
    "parse_args",
    "render_diff_summary",
    "main",
]

DEFAULT_BASELINE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "porting"
    / "artifacts"
    / "ml-extra-overlay-metadata.json"
)

_DEFAULT_BASELINE = DEFAULT_BASELINE


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Return parsed command-line arguments for the snapshot guard."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overlay",
        type=Path,
        default=None,
        help="Override the default ml.extra binary path",
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
        "--json",
        action="store_true",
        help="Emit the diff payload as JSON instead of a text summary",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Overwrite the baseline with the freshly generated snapshot",
    )
    return parser.parse_args(argv)


def render_diff_summary(baseline: Path, diff: sanity_core.MetadataDiff) -> str:
    """Return a human-readable summary for ``diff`` results."""

    return sanity_reporting.render_diff_summary(baseline, diff)


def _render_diff_summary(baseline: Path, diff: sanity_core.MetadataDiff) -> str:
    return render_diff_summary(baseline, diff)


def main(argv: List[str] | None = None) -> int:
    """Entry point for ``ml_extra_snapshot_guard`` CLI commands."""

    args = parse_args(argv)
    report = sanity_core.run_checks(args.overlay)
    metadata_snapshot = report.metadata_snapshot
    if not metadata_snapshot:
        raise SystemExit("metadata snapshot unavailable from ml_extra_sanity.run_checks")

    baseline_path: Path = args.baseline
    if not baseline_path.exists():
        raise SystemExit(f"baseline metadata not found: {baseline_path}")

    baseline_snapshot = ml_extra_metadata_io.read_metadata_snapshot(baseline_path)
    diff = sanity_core.diff_metadata_snapshots(baseline_snapshot, metadata_snapshot)

    if args.json:
        print(json.dumps(diff.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_diff_summary(baseline_path, diff))

    if args.update_baseline:
        baseline_updated = ml_extra_metadata_io.write_metadata_snapshot(
            baseline_path, metadata_snapshot, only_if_changed=True
        )
        if not args.json:
            if baseline_updated:
                print(f"Refreshed baseline snapshot at {baseline_path}")
            else:
                print(f"Baseline snapshot already up to date: {baseline_path}")
        return 0

    return 0 if diff.matches else 1


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())
