"""Host configuration helpers for ImageBBS storage prototypes."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import tomllib

from .setup_defaults import (
    DriveAssignment,
    FilesystemDriveLocator,
    SetupDefaults,
)


def load_drive_config(config_path: Path) -> tuple[DriveAssignment, ...]:
    """Merge TOML drive slot overrides with :func:`SetupDefaults.stub`."""

    defaults = SetupDefaults.stub()
    overrides = _parse_drive_config(config_path)

    merged: list[DriveAssignment] = []
    remaining = dict(overrides)
    for assignment in defaults.drives:
        merged.append(remaining.pop(assignment.slot, assignment))

    for slot in sorted(remaining):
        merged.append(remaining[slot])

    return tuple(merged)


def _parse_drive_config(config_path: Path) -> Dict[int, DriveAssignment]:
    with config_path.open("rb") as stream:
        data = tomllib.load(stream)

    raw_slots = data.get("slots", data)
    if not isinstance(raw_slots, dict):
        raise ValueError("drive config must define a mapping of slots to paths")

    overrides: Dict[int, DriveAssignment] = {}
    for raw_slot, raw_path in raw_slots.items():
        slot = _coerce_slot(raw_slot)
        locator_path = _normalise_drive_path(raw_path, base=config_path.parent)
        overrides[slot] = DriveAssignment(
            slot=slot,
            locator=FilesystemDriveLocator(path=locator_path),
        )
    return overrides


def _coerce_slot(raw_slot: Any) -> int:
    if isinstance(raw_slot, int):
        slot = raw_slot
    elif isinstance(raw_slot, str):
        try:
            slot = int(raw_slot)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"invalid drive slot '{raw_slot}'") from exc
    else:  # pragma: no cover - defensive guard
        raise TypeError("drive slot keys must be integers")

    if slot < 1:
        raise ValueError("drive slot numbers must be positive")
    return slot


def _normalise_drive_path(raw_path: Any, *, base: Path) -> Path:
    if isinstance(raw_path, (str, Path)):
        path = Path(raw_path).expanduser()
    else:  # pragma: no cover - defensive guard
        raise TypeError("drive paths must be strings or path-like")

    if not path.is_absolute():
        path = (base / path).resolve()
    else:
        path = path.resolve()
    return path


__all__ = ["load_drive_config"]
