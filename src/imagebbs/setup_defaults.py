"""Host-friendly view of the default data staged by ``setup``."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Protocol, Tuple


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
    read_only: bool = False
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
    def read_only(self) -> bool:
        """Whether the backing locator should be treated as read-only."""

        locator = self.locator
        return bool(getattr(locator, "read_only", False))

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


@dataclass(frozen=True)
class IndicatorDefaults:
    """Optional indicator overrides surfaced by the setup stub."""

    pause_colour: Optional[int] = None
    abort_colour: Optional[int] = None
    spinner_colour: Optional[int] = None
    carrier_leading_colour: Optional[int] = None
    carrier_indicator_colour: Optional[int] = None
    spinner_frames: Tuple[int, ...] | None = None

    # Why: translate indicator defaults into constructor kwargs so instrumentation wiring can honour host preferences.
    def controller_kwargs(self) -> Dict[str, object]:
        payload: Dict[str, object] = {}
        if self.pause_colour is not None:
            payload["pause_colour"] = int(self.pause_colour) & 0xFF
        if self.abort_colour is not None:
            payload["abort_colour"] = int(self.abort_colour) & 0xFF
        if self.spinner_colour is not None:
            payload["spinner_colour"] = int(self.spinner_colour) & 0xFF
        if self.carrier_leading_colour is not None:
            payload["carrier_leading_colour"] = int(self.carrier_leading_colour) & 0xFF
        if self.carrier_indicator_colour is not None:
            payload["carrier_indicator_colour"] = int(self.carrier_indicator_colour) & 0xFF
        if self.spinner_frames is not None:
            payload["spinner_frames"] = tuple(int(code) & 0xFF for code in self.spinner_frames)
        return payload


@dataclass(frozen=True)
class FileLibraryEntry:
    """Structured metadata describing a single upload/download record."""

    number: int
    filename: str
    blocks: int
    downloads: int
    description: str
    uploader: str
    validated: bool


@dataclass(frozen=True)
class FileLibraryDescriptor:
    """Configuration surfaced for each logical file-transfer library."""

    code: str
    identifier: str
    name: str
    drive_slot: int
    directory: str
    macro: str
    path: Tuple[str, ...]
    total_files: int
    new_files: int
    credit_balance: int
    protocol: str
    subops: Tuple[str, ...]
    entries: Tuple[FileLibraryEntry, ...] = ()

    @property
    def display_path(self) -> str:
        """Return the hierarchical label used when listing directories."""

        return " / ".join(self.path) if self.path else self.name


DEFAULT_MODEM_BAUD_LIMIT = 1200


@dataclass(frozen=True)
class SetupConfig:
    """Loaded drive assignments and ampersand overrides."""

    drives: Tuple[DriveAssignment, ...]
    ampersand_overrides: Dict[int, str]
    modem_baud_limit: Optional[int] = None
    indicator: IndicatorDefaults = field(default_factory=IndicatorDefaults)

    def __post_init__(self) -> None:
        # Ensure mutable values are not shared between instances.
        object.__setattr__(self, "ampersand_overrides", dict(self.ampersand_overrides))


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
    indicator: IndicatorDefaults = field(default_factory=IndicatorDefaults)
    library_macros: Mapping[str, str] = field(default_factory=dict)
    file_libraries: Tuple[FileLibraryDescriptor, ...] = field(
        default_factory=tuple
    )

    @property
    def active_drives(self) -> Tuple[DriveAssignment, ...]:
        """Return the drive slots that point at configured devices."""

        return tuple(assignment for assignment in self.drives if assignment.is_configured)

    @property
    # Why: summarise configured library groups so runtime modules can discover available codes.
    def library_codes(self) -> Tuple[str, ...]:
        """Expose the library codes provisioned by the setup stub."""

        return tuple(sorted({entry.code for entry in self.file_libraries}))

    # Why: offer a deterministic ordering so session modules can switch between libraries reliably.
    def libraries_for_code(self, code: str) -> Tuple[FileLibraryDescriptor, ...]:
        """Return the libraries matching ``code`` while preserving stub order."""

        normalised = code.upper()
        return tuple(entry for entry in self.file_libraries if entry.code == normalised)

    # Why: expose introductory text so runtime modules can emulate BASIC's entry banners.
    def library_macro(self, macro: str) -> Optional[str]:
        """Return the introductory macro text associated with ``macro``."""

        return self.library_macros.get(macro)

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
    def data_records(self) -> "SetupDataRecords":
        """Expose the ``DATA`` statements parsed from ``setup.bas``."""

        return load_setup_data_records()

    @classmethod
    def stub(cls) -> "SetupDefaults":
        """Return the deterministic defaults recorded alongside ``setup``."""

        # Why: decode the stub manifest so host tooling can rebuild runtime defaults deterministically.
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
        indicator_defaults = _coerce_indicator_defaults(defaults.get("indicator"))
        library_macros = _coerce_library_macros(defaults.get("library_macros", {}))
        library_descriptors = _coerce_library_descriptors(
            defaults.get("libraries", ())
        )

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
            indicator=indicator_defaults,
            macro_modules=macro_modules,
            library_macros=library_macros,
            file_libraries=library_descriptors,
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
    "IndicatorDefaults",
    "SetupConfig",
    "SetupDefaults",
    "SysopProfile",
    "FileLibraryDescriptor",
    "FileLibraryEntry",
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

_DEFAULT_PATTERN = re.compile(
    r"^\s*\d*\s*rem\s+stub-default\s+([a-z0-9_]+)\s*=\s*(.+)$", re.IGNORECASE
)
_DATA_PATTERN = re.compile(r"^\s*\d+\s+data\s+(.+)$", re.IGNORECASE)

_MISSING = object()


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


# Why: normalise stub indicator overrides so runtime wiring honours configured palette and spinner choices.
def _coerce_indicator_defaults(raw: Any) -> IndicatorDefaults:
    if not isinstance(raw, Mapping):
        return IndicatorDefaults()

    def _coerce_colour(value: Any) -> Optional[int]:
        colour = _coerce_optional_int(value)
        if colour is None:
            return None
        if not 0 <= colour <= 0xFF:
            raise ValueError("indicator colours must be between 0 and 255")
        return colour

    overrides: Dict[str, Any] = {}
    for key in (
        "pause_colour",
        "abort_colour",
        "spinner_colour",
        "carrier_leading_colour",
        "carrier_indicator_colour",
    ):
        if key in raw:
            overrides[key] = _coerce_colour(raw.get(key))

    frames_raw = raw.get("spinner_frames", _MISSING)
    if frames_raw is not _MISSING:
        if frames_raw is None:
            overrides["spinner_frames"] = None
        else:
            if not isinstance(frames_raw, (list, tuple)):
                raise TypeError("indicator spinner_frames must be a list or tuple")
            frames: list[int] = []
            for entry in frames_raw:
                frame = int(entry)
                if not 0 <= frame <= 0xFF:
                    raise ValueError("indicator spinner frames must be between 0 and 255")
                frames.append(frame)
            overrides["spinner_frames"] = tuple(frames)

    return IndicatorDefaults(**overrides)


# Why: normalise stub macro mappings so runtime modules can replay entry banners.
def _coerce_library_macros(raw: Any) -> Dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    macros: Dict[str, str] = {}
    for key, value in raw.items():
        macros[str(key)] = str(value)
    return macros


# Why: translate stub file entries into immutable records consumable by runtime modules.
def _coerce_library_entry(raw: Mapping[str, Any]) -> FileLibraryEntry:
    return FileLibraryEntry(
        number=int(raw.get("number", 0)),
        filename=str(raw.get("filename", "")),
        blocks=int(raw.get("blocks", 0)),
        downloads=int(raw.get("downloads", 0)),
        description=str(raw.get("description", "")),
        uploader=str(raw.get("uploader", "")),
        validated=bool(raw.get("validated", False)),
    )


# Why: expose hierarchical library metadata derived from stub dictionaries.
def _coerce_library_descriptor(raw: Mapping[str, Any]) -> FileLibraryDescriptor:
    entries_raw = raw.get("entries", ())
    if isinstance(entries_raw, Mapping):
        entries_raw = (entries_raw,)
    entries: Tuple[FileLibraryEntry, ...] = tuple(
        _coerce_library_entry(entry)
        for entry in entries_raw
        if isinstance(entry, Mapping)
    )
    path_raw = raw.get("path")
    if isinstance(path_raw, (list, tuple)):
        path = tuple(str(segment) for segment in path_raw)
    elif isinstance(path_raw, str) and path_raw:
        path = tuple(segment.strip() for segment in path_raw.split("/") if segment.strip())
    else:
        path = (str(raw.get("name", "Library")),)
    subops_raw = raw.get("subops", ())
    if isinstance(subops_raw, str):
        subops = (subops_raw,)
    else:
        subops = tuple(str(entry) for entry in subops_raw) if isinstance(subops_raw, (list, tuple)) else tuple()
    return FileLibraryDescriptor(
        code=str(raw.get("code", "UD")).upper(),
        identifier=str(raw.get("identifier", "1")),
        name=str(raw.get("name", "Library")),
        drive_slot=int(raw.get("drive_slot", 8)),
        directory=str(raw.get("directory", "")),
        macro=str(raw.get("macro", "s.UD")),
        path=path,
        total_files=int(raw.get("total_files", len(entries))),
        new_files=int(raw.get("new_files", 0)),
        credit_balance=int(raw.get("credit_balance", 0)),
        protocol=str(raw.get("protocol", "Punter")),
        subops=subops,
        entries=entries,
    )


# Why: convert the heterogeneous stub library payload into strongly typed descriptors.
def _coerce_library_descriptors(raw: Any) -> Tuple[FileLibraryDescriptor, ...]:
    if isinstance(raw, Mapping):
        raw_iterable = raw.values()
    else:
        raw_iterable = raw
    descriptors: list[FileLibraryDescriptor] = []
    if isinstance(raw_iterable, Iterable):
        for entry in raw_iterable:
            if isinstance(entry, Mapping):
                descriptors.append(_coerce_library_descriptor(entry))
    return tuple(descriptors)


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

