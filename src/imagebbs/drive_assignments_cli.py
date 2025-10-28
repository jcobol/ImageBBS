"""CLI helper that reports ImageBBS drive slot assignments."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Mapping

from .device_context import DiskDrive, bootstrap_device_context
from .setup_config import SetupConfig, load_drive_config
from .setup_defaults import (
    CommodoreDeviceDrive,
    DriveAssignment,
    FilesystemDriveLocator,
)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Return parsed command-line arguments for the drive mapping CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the drive configuration TOML file",
    )
    return parser.parse_args(argv)


def render_assignments(
    assignments: Iterable[DriveAssignment],
    *,
    ampersand_overrides: Mapping[int, str] | None = None,
) -> list[str]:
    """Return formatted mapping lines for ``assignments``."""

    context = bootstrap_device_context(
        assignments, ampersand_overrides=ampersand_overrides
    )
    lines: list[str] = ["Configured drive slots:"]
    for assignment in assignments:
        locator = assignment.locator
        slot = assignment.slot
        if isinstance(locator, FilesystemDriveLocator):
            device = context.devices.get(f"drive{slot}")
            root = None
            if isinstance(device, DiskDrive):
                root = device.root
            path_text = str(locator.path)
            if root is not None and root != locator.path:
                path_text = f"{path_text} (mounted at {root})"
            mount = f"slot {slot} (drive{slot}): filesystem -> {path_text}"
        elif isinstance(locator, CommodoreDeviceDrive):
            mount = (
                f"slot {slot}: cbm device {locator.device} drive {locator.drive}"
            )
        elif locator is None:
            mount = f"slot {slot}: <unassigned>"
        else:
            describe = getattr(locator, "describe", None)
            details = describe() if callable(describe) else str(locator)
            mount = f"slot {slot}: {locator.scheme} -> {details}"
        lines.append(mount)
    if ampersand_overrides:
        lines.append("")
        lines.append("Ampersand overrides:")
        for flag_index, import_path in sorted(ampersand_overrides.items()):
            lines.append(f"flag {flag_index:#04x} -> {import_path}")
    return lines


def main(argv: List[str] | None = None) -> int:
    """Entry point for ``drive_assignments_cli`` commands."""

    args = parse_args(argv)
    config_path: Path = args.config
    if not config_path.exists():
        raise SystemExit(f"configuration file not found: {config_path}")

    config: SetupConfig = load_drive_config(config_path)
    lines = render_assignments(
        config.drives, ampersand_overrides=config.ampersand_overrides
    )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())
