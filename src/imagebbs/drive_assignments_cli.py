"""CLI helper that reports ImageBBS drive slot assignments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Mapping, TypedDict

from .device_context import DiskDrive, bootstrap_device_context
from .setup_config import SetupConfig, load_drive_config
from .setup_defaults import (
    CommodoreDeviceDrive,
    DriveAssignment,
    FilesystemDriveLocator,
)


class SlotRecord(TypedDict, total=False):
    """Structured representation of a logical drive slot."""

    slot: int
    scheme: str | None
    description: str
    configured_path: str
    resolved_host_path: str
    device: int
    drive: int
    read_only: bool


class AmpersandOverrideRecord(TypedDict):
    """Structured representation of an ampersand override mapping."""

    flag: int
    module: str


class AssignmentPayload(TypedDict):
    """Structured payload that captures drive slots and overrides."""

    slots: list[SlotRecord]
    ampersand_overrides: list[AmpersandOverrideRecord]


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Return parsed command-line arguments for the drive mapping CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the drive configuration TOML file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON describing configured slots",
    )
    return parser.parse_args(argv)


def build_assignment_payload(
    assignments: Iterable[DriveAssignment],
    *,
    ampersand_overrides: Mapping[int, str] | None = None,
) -> AssignmentPayload:
    """Collect structured drive slot records for downstream rendering."""

    assignment_list = list(assignments)
    context = bootstrap_device_context(
        assignment_list, ampersand_overrides=ampersand_overrides
    )

    records: list[SlotRecord] = []
    for assignment in assignment_list:
        slot = assignment.slot
        locator = assignment.locator

        if isinstance(locator, FilesystemDriveLocator):
            record: SlotRecord = {
                "slot": slot,
                "scheme": locator.scheme,
                "description": locator.describe(),
                "configured_path": str(locator.path),
            }
            device = context.devices.get(f"drive{slot}")
            if isinstance(device, DiskDrive) and device.root is not None:
                record["resolved_host_path"] = str(device.root)
        elif isinstance(locator, CommodoreDeviceDrive):
            record = {
                "slot": slot,
                "scheme": locator.scheme,
                "description": locator.describe(),
                "device": locator.device,
                "drive": locator.drive,
            }
        elif locator is None:
            record = {
                "slot": slot,
                "scheme": None,
                "description": "<unassigned>",
            }
        else:
            describe = getattr(locator, "describe", None)
            details = describe() if callable(describe) else str(locator)
            record = {
                "slot": slot,
                "scheme": getattr(locator, "scheme", None),
                "description": details,
            }

        record["read_only"] = assignment.read_only
        records.append(record)

    overrides: list[AmpersandOverrideRecord] = []
    if ampersand_overrides:
        overrides = [
            {"flag": flag_index, "module": import_path}
            for flag_index, import_path in sorted(ampersand_overrides.items())
        ]

    return {
        "slots": records,
        "ampersand_overrides": overrides,
    }


def render_assignments(
    assignments: Iterable[DriveAssignment],
    *,
    ampersand_overrides: Mapping[int, str] | None = None,
) -> list[str]:
    """Return formatted mapping lines for ``assignments``."""

    payload = build_assignment_payload(
        assignments, ampersand_overrides=ampersand_overrides
    )
    lines: list[str] = ["Configured drive slots:"]
    for record in payload["slots"]:
        slot = record["slot"]
        scheme = record["scheme"]
        if scheme == "fs":
            configured_path = record.get("configured_path", "")
            line = (
                f"slot {slot} (drive{slot}): filesystem -> {configured_path}"
            )
            annotations: list[str] = []
            if record.get("read_only"):
                annotations.append("read-only")
            resolved = record.get("resolved_host_path")
            if resolved and resolved != configured_path:
                annotations.append(f"mounted at {resolved}")
            if annotations:
                line = f"{line} ({'; '.join(annotations)})"
        elif scheme == "cbm":
            line = (
                f"slot {slot}: cbm device {record.get('device')} "
                f"drive {record.get('drive')}"
            )
        elif scheme is None:
            line = f"slot {slot}: <unassigned>"
        else:
            line = f"slot {slot}: {scheme} -> {record['description']}"
        lines.append(line)
    overrides = payload["ampersand_overrides"]
    if overrides:
        lines.append("")
        lines.append("Ampersand overrides:")
        for override in overrides:
            lines.append(
                f"flag {override['flag']:#04x} -> {override['module']}"
            )
    return lines


def main(argv: List[str] | None = None) -> int:
    """Entry point for ``drive_assignments_cli`` commands."""

    args = parse_args(argv)
    config_path: Path = args.config
    if not config_path.exists():
        raise SystemExit(f"configuration file not found: {config_path}")

    config: SetupConfig = load_drive_config(config_path)
    if args.json:
        payload = build_assignment_payload(
            config.drives, ampersand_overrides=config.ampersand_overrides
        )
        print(json.dumps(payload))
    else:
        lines = render_assignments(
            config.drives, ampersand_overrides=config.ampersand_overrides
        )
        print("\n".join(lines))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via python -m
    raise SystemExit(main())
