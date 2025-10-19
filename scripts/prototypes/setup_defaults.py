"""Host-friendly view of the default data staged by ``setup``.

The recovered BASIC overlay now lives in ``v1.2/source/setup.bas`` while
``v1.2/core/setup.stub.txt`` documents its control flow with annotated
placeholders.  This helper reads both listings so host-side prototypes can
reference verified defaults (drive slots, sysop metadata, statistics counters)
and the canonical ``DATA`` records without reimplementing a BASIC parser."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Protocol, Tuple


class DriveLocator(Protocol):
    """Identifies where a logical ImageBBS drive slot points on the host."""

    scheme: str


@dataclass(frozen=True)
class CommodoreDeviceDrive:
    """Legacy Commodore device/drive tuple referenced by the BASIC stub."""

    device: int
    drive: int
    scheme: str = field(init=False, default="cbm")

    def describe(self) -> str:
        """Return a human-readable representation of the tuple."""

        return f"device {self.device} drive {self.drive}"


@dataclass(frozen=True)
class FilesystemDriveLocator:
    """Host filesystem directory referenced by a logical drive slot."""

    path: Path
    scheme: str = field(init=False, default="fs")

    def describe(self) -> str:
        """Return a human-readable representation of the backing directory."""

        return str(self.path)


@dataclass(frozen=True)
class DriveAssignment:
    """Maps a logical ImageBBS drive slot to a host-specific locator."""

    slot: int
    locator: Optional[DriveLocator] = None

    @property
    def device(self) -> int:
        """Return the Commodore device number for legacy tuples."""

        locator = self.locator
        if isinstance(locator, CommodoreDeviceDrive):
            return locator.device
        return 0

    @property
    def drive(self) -> int:
        """Return the Commodore drive index for legacy tuples."""

        locator = self.locator
        if isinstance(locator, CommodoreDeviceDrive):
            return locator.drive
        return 0

    @property
    def is_configured(self) -> bool:
        """Whether the slot has been assigned to a backing store."""

        return self.locator is not None

    def legacy_tuple(self) -> Tuple[int, int]:
        """Expose the device/drive tuple used by the BASIC stub."""

        return self.device, self.drive


@dataclass(frozen=True)
class DeviceDriveMap:
    """Collects the logical units assigned to a Commodore device number."""

    device: int
    drives: Tuple[int, ...]


@dataclass(frozen=True)
class DriveInventory:
    """Derived metadata exposed by the `bd.data` header."""

    highest_device: int
    highest_device_minus_seven: int
    device_count: int
    logical_unit_count: int
    devices: Tuple[DeviceDriveMap, ...]


@dataclass(frozen=True)
class PrimeTimeWindow:
    """Prime-time configuration stored in ``e.data`` record 20."""

    # The first number toggles prime-time behaviour when non-zero and may also
    # encode the minutes-per-call allotment applied during that window in the
    # original program. The recovered BASIC listing reuses ``pt%`` for runtime
    # state, so the persisted value lives in ``p1%`` instead.

    indicator: int
    start_hour: int
    end_hour: int

    @property
    def is_enabled(self) -> bool:
        """Return ``True`` when prime time restrictions are active."""

        return self.indicator > 0


@dataclass(frozen=True)
class ChatModeMessages:
    """Messages displayed when the sysop enters or leaves chat."""

    entering: str
    exiting: str
    returning_to_editor: str


@dataclass(frozen=True)
class BoardStatistics:
    """Persisted caller metadata staged from ``e.data`` and ``e.stats``."""

    message_counts: Tuple[int, int, int, int]
    status_banner: str
    total_calls: int
    last_caller: str
    last_logon_timestamp: str
    password_subs_password: str

    @property
    def has_activity(self) -> bool:
        """Return ``True`` if any counters or the call total are non-zero."""

        if self.total_calls:
            return True
        return any(self.message_counts)


@dataclass(frozen=True)
class SysopProfile:
    """Subset of the sysop record staged from ``u.config``."""

    login_id: str
    board_title: str
    handle: str
    password: str
    first_name: str
    last_name: str
    phone: str


@dataclass(frozen=True)
class ModemDefaults:
    """Derived defaults for the host modem transport."""

    baud_limit: Optional[int] = None


DEFAULT_MODEM_BAUD_LIMIT = 1200


@dataclass(frozen=True)
class SetupDefaults:
    """Aggregates the stubbed values exposed by ``setup`` for host tooling."""

    drives: Tuple[DriveAssignment, ...]
    drive_inventory: DriveInventory
    board_identifier: str
    new_user_credits: int
    highest_device_minus_seven: int
    drive_count: int
    board_name: str
    prompt: str
    copyright_notice: str
    sysop: SysopProfile
    statistics: BoardStatistics
    prime_time: PrimeTimeWindow
    chat_mode_messages: ChatModeMessages
    macro_modules: Tuple[str, ...]
    modem: ModemDefaults = field(default_factory=ModemDefaults)

    @property
    def active_drives(self) -> Tuple[DriveAssignment, ...]:
        """Return the drive slots that point at configured devices."""

        return tuple(assignment for assignment in self.drives if assignment.is_configured)

    @property
    def last_caller(self) -> str:
        """Expose the last-caller string stored in ``e.data`` record 17."""

        return self.statistics.last_caller

    @property
    def stats_banner(self) -> str:
        """Expose the message banner stored alongside BAR statistics."""

        return self.statistics.status_banner

    @property
    def last_logon_timestamp(self) -> str:
        """Expose the last caller timestamp staged from ``e.data`` record 19."""

        return self.statistics.last_logon_timestamp

    @property
    def password_subs_password(self) -> str:
        """Expose the password used by password-protected subs."""

        return self.statistics.password_subs_password

    @property
    def chat_mode_entering(self) -> str:
        """Banner shown when the sysop accepts a chat request."""

        return self.chat_mode_messages.entering

    @property
    def chat_mode_exiting(self) -> str:
        """Banner shown when the sysop leaves chat mode."""

        return self.chat_mode_messages.exiting

    @property
    def chat_mode_returning_to_editor(self) -> str:
        """Banner shown when a caller returns to the editor after chat."""

        return self.chat_mode_messages.returning_to_editor

    @property
    def data_records(self) -> SetupDataRecords:
        """Expose the ``DATA`` statements parsed from ``setup.bas``."""

        return load_setup_data_records()

    @classmethod
    def stub(cls) -> "SetupDefaults":
        """Return the deterministic defaults recorded alongside ``setup``."""

        defaults = load_stub_defaults()
        raw_assignments = tuple(tuple(entry) for entry in defaults["drives"])
        drives = tuple(
            DriveAssignment(
                slot=index,
                locator=(
                    CommodoreDeviceDrive(device=device, drive=drive)
                    if device
                    else None
                ),
            )
            for index, (device, drive) in enumerate(raw_assignments, start=1)
        )
        inventory = derive_drive_inventory(drives)
        sysop = SysopProfile(**defaults["sysop"])
        statistics = BoardStatistics(**defaults["statistics"])
        prime_time = PrimeTimeWindow(**defaults["prime_time"])
        chat_messages = ChatModeMessages(**defaults["chat_mode_messages"])
        raw_modem = defaults.get("modem")
        modem_defaults = _derive_modem_defaults(raw_modem)

        stub_overlays = tuple(defaults.get("overlays", ()))
        actual_overlays = extract_overlay_sequence()
        if stub_overlays and actual_overlays and stub_overlays != actual_overlays:
            raise ValueError(
                "overlay list mismatch between setup stub and setup.bas"
            )
        macro_modules = actual_overlays or stub_overlays
        highest_device_minus_seven = inventory.highest_device_minus_seven
        drive_count = inventory.device_count
        return cls(
            drives=drives,
            drive_inventory=inventory,
            board_identifier=str(defaults["board_identifier"]),
            new_user_credits=int(defaults["new_user_credits"]),
            highest_device_minus_seven=highest_device_minus_seven,
            drive_count=drive_count,
            board_name=str(defaults["board_name"]),
            prompt=str(defaults["prompt"]),
            copyright_notice=str(defaults["copyright_notice"]),
            sysop=sysop,
            statistics=statistics,
            prime_time=prime_time,
            chat_mode_messages=chat_messages,
            modem=modem_defaults,
            macro_modules=macro_modules,
        )


def derive_drive_inventory(drives: Iterable[DriveAssignment]) -> DriveInventory:
    """Summarise Commodore tuples while ignoring future locator schemes."""

    device_map: Dict[int, set[int]] = {}
    for assignment in drives:
        locator = assignment.locator
        if not isinstance(locator, CommodoreDeviceDrive):
            continue
        slots = device_map.setdefault(locator.device, set())
        slots.add(locator.drive)
    devices = tuple(
        DeviceDriveMap(device=device, drives=tuple(sorted(slots)))
        for device, slots in sorted(device_map.items())
    )
    highest_device = devices[-1].device if devices else 0
    highest_minus_seven = highest_device - 7 if highest_device else 0
    logical_units = sum(len(entry.drives) for entry in devices)
    return DriveInventory(
        highest_device=highest_device,
        highest_device_minus_seven=highest_minus_seven,
        device_count=len(devices),
        logical_unit_count=logical_units,
        devices=devices,
    )


__all__ = [
    "CommodoreDeviceDrive",
    "DriveAssignment",
    "DriveLocator",
    "FilesystemDriveLocator",
    "DeviceDriveMap",
    "DriveInventory",
    "BoardStatistics",
    "ChatModeMessages",
    "PrimeTimeWindow",
    "ModemDefaults",
    "SetupDefaults",
    "SysopProfile",
    "SetupDataRecords",
    "extract_overlay_sequence",
    "load_setup_data_records",
    "load_stub_defaults",
    "derive_drive_inventory",
]
@dataclass(frozen=True)
class SetupDataRecords:
    """Structured view of the ``DATA`` statements embedded in ``setup.bas``."""

    co_options: Tuple[str, ...]
    lightbar_char_codes: Tuple[int, ...]
    lightbar_labels: Tuple[str, ...]


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SETUP_BAS_PATH = _REPO_ROOT / "v1.2/source/setup.bas"
_SETUP_STUB_PATH = _REPO_ROOT / "v1.2/core/setup.stub.txt"

_DEFAULT_PATTERN = re.compile(r"^\s*\d*\s*rem\s+stub-default\s+([a-z0-9_]+)\s*=\s*(.+)$", re.IGNORECASE)
_DATA_PATTERN = re.compile(r"^\s*\d+\s+data\s+(.+)$", re.IGNORECASE)


def _literal_eval(value: str, *, key: str, source: Path) -> Any:
    """Evaluate ``value`` using :func:`ast.literal_eval` with context."""

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError) as exc:  # pragma: no cover - defensive guard
        message = f"unable to parse stub default for {key!r} in {source}: {value}"
        raise ValueError(message) from exc


def _coerce_optional_int(value: Any) -> Optional[int]:
    """Return ``value`` as an optional ``int`` while tolerating ``None``."""

    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"expected integer value, received {value!r}") from exc


def _derive_modem_defaults(raw_modem: Any) -> ModemDefaults:
    """Return modem defaults seeded from stub metadata."""

    if isinstance(raw_modem, dict):
        if "baud_limit" in raw_modem:
            baud_limit = _coerce_optional_int(raw_modem.get("baud_limit"))
        else:
            baud_limit = DEFAULT_MODEM_BAUD_LIMIT
    else:
        baud_limit = DEFAULT_MODEM_BAUD_LIMIT

    return ModemDefaults(baud_limit=baud_limit)


def load_stub_defaults(stub_path: Optional[Path] = None) -> Dict[str, Any]:
    """Return the annotated defaults recorded in ``setup.stub.txt``."""

    path = stub_path or _SETUP_STUB_PATH
    defaults: Dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _DEFAULT_PATTERN.match(line)
        if not match:
            continue
        key, raw_value = match.groups()
        value = _literal_eval(raw_value.strip(), key=key.lower(), source=path)
        defaults[key.lower()] = value
    return defaults


def load_setup_data_records(listing_path: Optional[Path] = None) -> SetupDataRecords:
    """Parse ``DATA`` records from the authentic ``setup.bas`` listing."""

    path = listing_path or _SETUP_BAS_PATH
    values: list[Any] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _DATA_PATTERN.match(line)
        if not match:
            continue
        raw_values = match.group(1).strip()
        entries = _literal_eval(f"[{raw_values}]", key="data", source=path)
        if isinstance(entries, tuple):
            values.extend(entries)
        else:
            values.extend(entries if isinstance(entries, list) else [entries])

    if len(values) < 33:
        raise ValueError(
            "setup.bas DATA decode produced fewer than 33 elements; listing may be stale"
        )

    co_options = tuple(str(option) for option in values[:9])
    char_codes = tuple(int(code) for code in values[9:21])
    lightbar_labels = tuple(str(label) for label in values[21:33])
    return SetupDataRecords(
        co_options=co_options,
        lightbar_char_codes=char_codes,
        lightbar_labels=lightbar_labels,
    )


def extract_overlay_sequence(listing_path: Optional[Path] = None) -> Tuple[str, ...]:
    """Return overlays loaded by ``setup`` in execution order."""

    path = listing_path or _SETUP_BAS_PATH
    overlays: list[str] = []
    current_literal: Optional[str] = None

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.lstrip()
        if stripped[:1].isdigit():
            parts = stripped.split(None, 1)
            body = parts[1] if len(parts) > 1 else ""
        else:
            body = stripped
        statements = [segment.strip() for segment in body.split(":")]
        for statement in statements:
            if statement.upper().startswith("A$ = ") and '"' in statement:
                literal = statement.split("=", 1)[1].strip()
                if literal.startswith('"') and literal.endswith('"'):
                    current_literal = literal.strip('"')
                else:
                    current_literal = None
                continue
            if statement.upper().startswith("GOSUB "):
                target = statement[6:].strip()
                if not current_literal:
                    current_literal = None
                    continue
                if target.startswith("190"):
                    overlays.append(f"ML.{current_literal}")
                elif target.startswith("1011"):
                    overlays.append(current_literal)
                current_literal = None
                continue
        current_literal = None

    return tuple(overlays)

