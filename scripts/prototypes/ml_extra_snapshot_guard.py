"""Guard the recovered ``ml.extra`` metadata snapshot against drift.

Example:
    $ python -m scripts.prototypes.ml_extra_snapshot_guard \
        --baseline docs/porting/artifacts/ml-extra-overlay-metadata.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from . import ml_extra_sanity


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


def render_diff_summary(baseline: Path, diff: dict[str, object]) -> str:
    """Return a human-readable summary for ``diff`` results."""

    lines: list[str] = []
    if diff.get("matches", False):
        lines.append(f"Baseline snapshot matches {baseline}")
        return "\n".join(lines)

    lines.append(f"Drift detected relative to {baseline}:")
    report_lines = diff.get("report_lines")
    if isinstance(report_lines, list) and report_lines:
        lines.extend(f"  {entry}" for entry in report_lines)
        return "\n".join(lines)

    for label in ("added", "removed", "changed"):
        entries = diff.get(label)
        if not isinstance(entries, list) or not entries:
            continue
        lines.append(f"  {label}:")
        for entry in entries:
            if not isinstance(entry, dict):
                lines.append(f"    {entry}")
                continue
            path = entry.get("path", "<unknown>")
            value = entry.get("value")
            lines.append(f"    {path}: {value}")
    return "\n".join(lines)


def _render_diff_summary(baseline: Path, diff: dict[str, object]) -> str:
    return render_diff_summary(baseline, diff)


def main(argv: List[str] | None = None) -> int:
    """Entry point for ``ml_extra_snapshot_guard`` CLI commands."""

    args = parse_args(argv)
    report = ml_extra_sanity.run_checks(args.overlay)
    metadata_snapshot = report.get("metadata_snapshot")
    if metadata_snapshot is None:
        raise SystemExit("metadata snapshot unavailable from ml_extra_sanity.run_checks")

    baseline_path: Path = args.baseline
    if not baseline_path.exists():
        raise SystemExit(f"baseline metadata not found: {baseline_path}")

    baseline_snapshot = json.loads(baseline_path.read_text(encoding="utf-8"))
    diff = ml_extra_sanity.diff_metadata_snapshots(baseline_snapshot, metadata_snapshot)

    if args.json:
        print(json.dumps(diff, indent=2, sort_keys=True))
    else:
        print(render_diff_summary(baseline_path, diff))

    if args.update_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(
            json.dumps(metadata_snapshot, indent=2) + "\n", encoding="utf-8"
        )
        if not args.json:
            print(f"Refreshed baseline snapshot at {baseline_path}")
        return 0

    return 0 if diff.get("matches", False) else 1


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())
