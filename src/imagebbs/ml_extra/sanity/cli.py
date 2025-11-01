"""Command-line entry point for ``ml.extra`` sanity checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .core import MetadataDiff, SanityReport, diff_metadata_snapshots, run_checks
from .reporting import format_report

__all__ = ["parse_args", "main"]


# Why: Provide a reusable parser so tests and other entry points can configure the CLI deterministically.
def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "overlay",
        type=Path,
        nargs="?",
        help="Override the default overlay binary path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary",
    )
    parser.add_argument(
        "--metadata-json",
        type=Path,
        help="Write overlay metadata to the specified JSON file",
    )
    parser.add_argument(
        "--baseline-metadata",
        type=Path,
        default=None,
        help=(
            "Compare against a baseline metadata snapshot (e.g. "
            "docs/porting/artifacts/ml-extra-overlay-metadata.json)"
        ),
    )
    return parser.parse_args(argv)


# Why: Orchestrate data collection, optional baseline comparison, and output rendering for the CLI.
def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)
    report: SanityReport = run_checks(args.overlay)
    metadata_snapshot = report.metadata_snapshot
    exit_code = 0
    baseline_diff: MetadataDiff | None = None

    if args.baseline_metadata:
        baseline_path = args.baseline_metadata
        if not baseline_path.exists():
            raise SystemExit(f"baseline metadata not found: {baseline_path}")
        if not metadata_snapshot:
            raise SystemExit(
                "baseline comparison requested but metadata snapshot is unavailable"
            )
        baseline_snapshot = json.loads(baseline_path.read_text(encoding="utf-8"))
        baseline_diff = diff_metadata_snapshots(baseline_snapshot, metadata_snapshot)
        if not baseline_diff.matches:
            exit_code = 1

    if args.metadata_json and metadata_snapshot:
        args.metadata_json.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_json.write_text(
            json.dumps(metadata_snapshot, indent=2, sort_keys=True) + "\n"
        )

    if args.json:
        payload = report.to_dict()
        if baseline_diff is not None:
            payload["baseline_diff"] = baseline_diff.to_dict()
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(report, baseline_diff))

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
