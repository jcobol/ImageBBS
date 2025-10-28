"""Storage configuration helpers for Commodore drive mappings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import tomllib


VALID_DRIVE_RANGE = range(0, 31)


class StorageConfigError(ValueError):
    """Raised when a storage configuration file fails validation."""


@dataclass(frozen=True)
class DriveMapping:
    """Resolved host directory for a Commodore device drive."""

    drive: int
    root: Path
    read_only: bool = False

    def resolve_path(self, filename: str) -> Path:
        """Return the host path for ``filename`` within this drive."""

        preserved = validate_filename(filename)
        return self.root / preserved


@dataclass(frozen=True)
class StorageConfig:
    """Active drive mappings used by the host runtime."""

    drives: Dict[int, DriveMapping]
    default_drive: int | None

    def __post_init__(self) -> None:  # pragma: no cover - dataclass internals
        object.__setattr__(self, "drives", dict(self.drives))

    def require_drive(self, drive: int) -> DriveMapping:
        """Return ``DriveMapping`` for ``drive`` or raise a ``KeyError``."""

        mapping = self.drives.get(drive)
        if mapping is None:
            raise KeyError(f"drive {drive} is not configured")
        return mapping

    def resolve(self, filename: str, drive: int | None = None) -> Path:
        """Resolve ``filename`` using ``drive`` or the default drive."""

        drive_number = drive if drive is not None else self.default_drive
        if drive_number is None:
            raise StorageConfigError(
                "no drive specified and no default_drive configured"
            )
        mapping = self.require_drive(drive_number)
        return mapping.resolve_path(filename)

    def validate_save_target(self, filename: str, drive: int | None = None) -> Path:
        """Resolve ``filename`` ensuring the selected drive is writable."""

        target = self.resolve(filename, drive=drive)
        drive_number = drive if drive is not None else self.default_drive
        assert drive_number is not None  # ``resolve`` already guards this case
        if self.require_drive(drive_number).read_only:
            raise StorageConfigError(f"drive {drive_number} is read-only")
        return target


def load_storage_config(config_path: Path) -> StorageConfig:
    """Parse and validate storage configuration at ``config_path``."""

    with config_path.open("rb") as stream:
        raw_data = tomllib.load(stream)

    storage = _parse_storage_section(raw_data)
    drives = _parse_drive_mappings(storage.get("drives", []), base=config_path.parent)

    if not drives:
        raise StorageConfigError("storage configuration must define at least one drive")

    default_drive = storage.get("default_drive")
    if default_drive is None and len(drives) == 1:
        default_drive = next(iter(drives))
    elif default_drive is not None:
        default_drive = _coerce_drive_number(default_drive)
        if default_drive not in drives:
            raise StorageConfigError(
                f"default_drive {default_drive} does not match a configured drive"
            )

    return StorageConfig(drives=drives, default_drive=default_drive)


def _parse_storage_section(data: Mapping[str, Any]) -> Mapping[str, Any]:
    storage = data.get("storage")
    if storage is None:
        raise StorageConfigError("storage configuration requires a [storage] table")
    if not isinstance(storage, Mapping):
        raise StorageConfigError("[storage] section must be a mapping")
    return storage


def _parse_drive_mappings(
    entries: Any, *, base: Path
) -> Dict[int, DriveMapping]:
    if entries is None:
        return {}
    if not isinstance(entries, Iterable):
        raise StorageConfigError("[[storage.drives]] must be an array of tables")

    resolved: Dict[int, DriveMapping] = {}
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, Mapping):
            raise StorageConfigError(
                f"drive entry #{index} must be a mapping, received {type(entry)!r}"
            )
        drive = _coerce_drive_number(entry.get("drive"))
        root = _normalise_drive_path(entry.get("path"), base=base)
        read_only = bool(entry.get("read_only", False))

        if drive in resolved:
            raise StorageConfigError(f"drive {drive} defined multiple times")

        if not root.exists():
            raise StorageConfigError(f"drive {drive} root does not exist: {root}")
        if not root.is_dir():
            raise StorageConfigError(f"drive {drive} root is not a directory: {root}")

        resolved[drive] = DriveMapping(drive=drive, root=root, read_only=read_only)
    return resolved


def _coerce_drive_number(raw_drive: Any) -> int:
    if raw_drive is None:
        raise StorageConfigError("drive entries must include a drive number")
    if isinstance(raw_drive, int):
        drive = raw_drive
    elif isinstance(raw_drive, str):
        text = raw_drive.strip()
        try:
            drive = int(text, base=10)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise StorageConfigError(f"invalid drive number: {raw_drive!r}") from exc
    else:  # pragma: no cover - defensive guard
        raise StorageConfigError("drive number must be an integer")

    if drive not in VALID_DRIVE_RANGE:
        raise StorageConfigError(
            f"drive {drive} outside supported range {VALID_DRIVE_RANGE.start}-"
            f"{VALID_DRIVE_RANGE.stop - 1}"
        )
    return drive


def _normalise_drive_path(raw_path: Any, *, base: Path) -> Path:
    if raw_path is None:
        raise StorageConfigError("drive entries must include a path")
    if isinstance(raw_path, (str, Path)):
        path = Path(raw_path).expanduser()
    else:  # pragma: no cover - defensive guard
        raise StorageConfigError("drive path must be a string or path-like")

    if not path.is_absolute():
        path = (base / path).resolve()
    else:
        path = path.resolve()
    return path


def validate_filename(filename: str) -> str:
    """Ensure ``filename`` preserves Commodore semantics without host escapes."""

    if not isinstance(filename, str):
        raise StorageConfigError("filenames must be text")
    preserved = filename.strip()
    if not preserved:
        raise StorageConfigError("filenames must not be empty")

    illegal = {"/", "\\", ":"}
    if any(char in preserved for char in illegal):
        blocked = ", ".join(sorted(illegal))
        raise StorageConfigError(
            f"filename '{filename}' contains forbidden path characters ({blocked})"
        )
    if preserved != filename:
        raise StorageConfigError(
            "filename trimming would alter Commodore semantics; supply exact name"
        )
    return preserved


__all__ = [
    "DriveMapping",
    "StorageConfig",
    "StorageConfigError",
    "load_storage_config",
    "validate_filename",
]
