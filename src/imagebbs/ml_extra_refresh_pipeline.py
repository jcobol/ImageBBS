"""Automate an overlay metadata refresh and baseline comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from . import ml_extra_sanity
from . import ml_extra_snapshot_guard

__all__ = ["DEFAULT_BASELINE", "parse_args", "main"]

DEFAULT_BASELINE = ml_extra_snapshot_guard.DEFAULT_BASELINE


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


def _write_metadata_snapshot(
    path: Path, payload: dict[str, object], *, only_if_changed: bool = False
) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded_payload = json.dumps(payload, indent=2) + "\n"

    if only_if_changed and path.exists():
        current_contents = path.read_text(encoding="utf-8")
        if current_contents == encoded_payload:
            return False

    path.write_text(encoded_payload, encoding="utf-8")
    return True


def main(argv: List[str] | None = None) -> int:
    """Entry point for the ``ml_extra_refresh_pipeline`` CLI."""

    args = parse_args(argv)
    report = ml_extra_sanity.run_checks(args.overlay)
    metadata_snapshot = report.get("metadata_snapshot")
    if metadata_snapshot is None:
        raise SystemExit("metadata snapshot unavailable from ml_extra_sanity.run_checks")

    baseline_path: Path = args.baseline
    if not baseline_path.exists():
        raise SystemExit(f"baseline metadata not found: {baseline_path}")

    baseline_snapshot = json.loads(baseline_path.read_text(encoding="utf-8"))

    metadata_path: Path = args.metadata_json
    snapshot_updated = _write_metadata_snapshot(
        metadata_path, metadata_snapshot, only_if_changed=args.if_changed
    )

    if args.if_changed:
        if snapshot_updated:
            print(f"Metadata snapshot updated: {metadata_path}")
        else:
            print(f"Metadata snapshot already up to date: {metadata_path}")
    else:
        print(f"Metadata snapshot written to: {metadata_path}")

    diff = ml_extra_sanity.diff_metadata_snapshots(baseline_snapshot, metadata_snapshot)
    print(ml_extra_snapshot_guard.render_diff_summary(baseline_path, diff))
    return 0 if diff.get("matches", False) else 1


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())
