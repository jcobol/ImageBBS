"""Load host drive configuration overlays from TOML files."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import tomllib

from dataclasses import replace

from .setup_defaults import (
    DriveAssignment,
    FilesystemDriveLocator,
    IndicatorDefaults,
    SetupConfig,
    SetupDefaults,
)


def load_drive_config(config_path: Path) -> SetupConfig:
    """Merge TOML drive slot overrides with :func:`SetupDefaults.stub`."""

    with config_path.open("rb") as stream:
        data = tomllib.load(stream)

    defaults = SetupDefaults.stub()
    drive_overrides = _parse_drive_config(data, base=config_path.parent)
    ampersand_overrides = _parse_ampersand_overrides(data)
    modem_baud_limit = _parse_modem_baud_limit(data)
    indicator_overrides = _parse_indicator_config(data)

    merged: list[DriveAssignment] = []
    remaining = dict(drive_overrides)
    for assignment in defaults.drives:
        merged.append(remaining.pop(assignment.slot, assignment))

    for slot in sorted(remaining):
        merged.append(remaining[slot])

    indicator = defaults.indicator
    # Why: carry stubbed indicator defaults forward while letting TOML overrides adjust palette and spinner settings.
    if indicator_overrides:
        indicator = replace(indicator, **indicator_overrides)

    return SetupConfig(
        drives=tuple(merged),
        ampersand_overrides=ampersand_overrides,
        modem_baud_limit=modem_baud_limit,
        indicator=indicator,
    )


def _parse_drive_config(
    data: Mapping[str, Any], *, base: Path
) -> Dict[int, DriveAssignment]:
    raw_slots = data.get("slots", data)
    if not isinstance(raw_slots, dict):
        raise ValueError("drive config must define a mapping of slots to paths")

    overrides: Dict[int, DriveAssignment] = {}
    for raw_slot, raw_entry in raw_slots.items():
        slot = _coerce_slot(raw_slot)
        locator = _parse_drive_locator(raw_entry, base=base)
        overrides[slot] = DriveAssignment(slot=slot, locator=locator)
    return overrides


def _parse_drive_locator(raw_entry: Any, *, base: Path) -> FilesystemDriveLocator:
    if isinstance(raw_entry, Mapping):
        try:
            raw_path = raw_entry["path"]
        except KeyError as exc:
            raise ValueError("slot configuration tables must define a path") from exc

        read_only = raw_entry.get("read_only", False)
        if not isinstance(read_only, bool):
            raise TypeError("slot read_only flag must be a boolean")

        locator_path = _normalise_drive_path(raw_path, base=base)
        return FilesystemDriveLocator(path=locator_path, read_only=read_only)

    locator_path = _normalise_drive_path(raw_entry, base=base)
    return FilesystemDriveLocator(path=locator_path)


def _parse_ampersand_overrides(data: Mapping[str, Any]) -> Dict[int, str]:
    raw_overrides = data.get("ampersand_overrides", {})
    if raw_overrides is None:
        return {}
    if not isinstance(raw_overrides, dict):
        raise ValueError("ampersand_overrides must be a mapping of indices to callables")

    overrides: Dict[int, str] = {}
    for raw_index, raw_path in raw_overrides.items():
        index = _coerce_flag_index(raw_index)
        overrides[index] = _coerce_import_path(raw_path)
    return overrides


def _parse_modem_baud_limit(data: Mapping[str, Any]) -> int | None:
    raw_modem = data.get("modem")
    if raw_modem is None:
        return None
    if not isinstance(raw_modem, Mapping):
        raise ValueError("modem configuration must be a mapping")

    raw_limit = raw_modem.get("baud_limit")
    if raw_limit is None:
        return None
    if isinstance(raw_limit, int):
        return raw_limit
    if isinstance(raw_limit, str):
        text = raw_limit.strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError("modem.baud_limit must be an integer") from exc
    raise TypeError("modem.baud_limit must be an integer")


def _parse_indicator_config(data: Mapping[str, Any]) -> Dict[str, object]:
    # Why: merge optional indicator palette and spinner overrides with stub defaults for controller construction.
    raw_indicator = data.get("indicator")
    if raw_indicator is None:
        return {}
    if not isinstance(raw_indicator, Mapping):
        raise ValueError("indicator configuration must be a mapping")

    def _coerce_colour(value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, int):
            colour = value
        elif isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            base = 16 if text.lower().startswith("0x") else 10
            try:
                colour = int(text, base=base)
            except ValueError as exc:  # pragma: no cover - defensive guard
                raise ValueError("indicator colours must be integers") from exc
        else:
            raise TypeError("indicator colours must be integers")
        if not 0 <= colour <= 0xFF:
            raise ValueError("indicator colours must be between 0 and 255")
        return colour

    def _coerce_frame(value: Any) -> int:
        if isinstance(value, int):
            frame = value
        elif isinstance(value, str):
            text = value.strip()
            base = 16 if text.lower().startswith("0x") else 10
            try:
                frame = int(text, base=base)
            except ValueError as exc:  # pragma: no cover - defensive guard
                raise ValueError("indicator spinner frames must be integers") from exc
        else:
            raise TypeError("indicator spinner frames must be integers")
        if not 0 <= frame <= 0xFF:
            raise ValueError("indicator spinner frames must be between 0 and 255")
        return frame

    overrides: Dict[str, object] = {}
    for key in (
        "pause_colour",
        "abort_colour",
        "spinner_colour",
        "carrier_leading_colour",
        "carrier_indicator_colour",
    ):
        if key in raw_indicator:
            overrides[key] = _coerce_colour(raw_indicator.get(key))

    if "spinner_frames" in raw_indicator:
        frames_value = raw_indicator.get("spinner_frames")
        if frames_value is None:
            overrides["spinner_frames"] = None
        else:
            if not isinstance(frames_value, (list, tuple)):
                raise TypeError("indicator spinner_frames must be a list or tuple")
            overrides["spinner_frames"] = tuple(_coerce_frame(entry) for entry in frames_value)

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


def _coerce_flag_index(raw_index: Any) -> int:
    if isinstance(raw_index, int):
        index = raw_index
    elif isinstance(raw_index, str):
        text = raw_index.strip()
        base = 16 if text.lower().startswith("0x") else 10
        try:
            index = int(text, base=base)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"invalid ampersand flag index '{raw_index}'") from exc
    else:  # pragma: no cover - defensive guard
        raise TypeError("ampersand flag indices must be integers")

    if index < 0:
        raise ValueError("ampersand flag indices must be non-negative")
    return index


def _coerce_import_path(raw_path: Any) -> str:
    if not isinstance(raw_path, str):
        raise TypeError("ampersand override targets must be strings")
    target = raw_path.strip()
    if not target:
        raise ValueError("ampersand override targets must not be empty")
    return target


__all__ = ["load_drive_config", "SetupConfig"]
