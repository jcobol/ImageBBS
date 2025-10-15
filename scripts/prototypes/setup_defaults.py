"""Host-friendly view of the default data staged by ``setup.stub``.

The BASIC placeholder approximating the missing ``setup`` overlay seeds
configuration arrays, sysop metadata, and statistics counters so the rest of
the boot sequence can proceed.  This module mirrors the same defaults in a
Python structure that host-side prototypes can import without having to parse
BASIC ``DATA`` statements."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Protocol, Tuple


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
    last_caller: str
    stats_banner: str
    last_logon_timestamp: str
    prime_time: PrimeTimeWindow
    macro_modules: Tuple[str, ...]

    @property
    def active_drives(self) -> Tuple[DriveAssignment, ...]:
        """Return the drive slots that point at configured devices."""

        return tuple(assignment for assignment in self.drives if assignment.is_configured)

    @classmethod
    def stub(cls) -> "SetupDefaults":
        """Return the deterministic defaults from ``setup.stub``."""

        raw_assignments = ((8, 0), (9, 0), (10, 0), (11, 0), (0, 0), (0, 0))
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
        sysop = SysopProfile(
            login_id="SYSOP",
            board_title="Image BBS",
            handle="SYSOP",
            password="PASSWORD",
            first_name="SYSOP",
            last_name="SYSOP",
            phone="555-1212",
        )
        prime_time = PrimeTimeWindow(indicator=0, start_hour=0, end_hour=0)
        highest_device_minus_seven = inventory.highest_device_minus_seven
        drive_count = inventory.device_count
        return cls(
            drives=drives,
            drive_inventory=inventory,
            board_identifier="IM",
            new_user_credits=25,
            highest_device_minus_seven=highest_device_minus_seven,
            drive_count=drive_count,
            board_name="IMAGE BBS",
            prompt="{pound}READY{pound}",
            copyright_notice="(c) 1990 FandF Products",
            sysop=sysop,
            last_caller="NO CALLERS YET",
            stats_banner="",
            last_logon_timestamp="00/00/00 00:00",
            prime_time=prime_time,
            macro_modules=("+.lo", "+.modem", "+.lb move", "+.lb chat"),
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
    "DeviceDriveMap",
    "DriveInventory",
    "PrimeTimeWindow",
    "SetupDefaults",
    "SysopProfile",
    "derive_drive_inventory",
]
