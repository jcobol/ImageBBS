"""Host-friendly view of the default data staged by ``setup.stub``.

The BASIC placeholder approximating the missing ``setup`` overlay seeds
configuration arrays, sysop metadata, and statistics counters so the rest of
the boot sequence can proceed.  This module mirrors the same defaults in a
Python structure that host-side prototypes can import without having to parse
BASIC ``DATA`` statements."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DriveAssignment:
    """Maps a logical ImageBBS drive slot to a Commodore device/drive tuple."""

    device: int
    drive: int


@dataclass(frozen=True)
class PrimeTimeWindow:
    """Represents the prime-time configuration pulled from ``e.data`` record 20."""

    enabled: bool
    start: int
    end: int


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

    @classmethod
    def stub(cls) -> "SetupDefaults":
        """Return the deterministic defaults from ``setup.stub``."""

        drives = tuple(
            DriveAssignment(device, drive)
            for device, drive in ((8, 0), (8, 1), (9, 0), (9, 1), (10, 0), (11, 0))
        )
        sysop = SysopProfile(
            login_id="SYSOP",
            board_title="Image BBS",
            handle="SYSOP",
            password="PASSWORD",
            first_name="SYSOP",
            last_name="SYSOP",
            phone="555-1212",
        )
        prime_time = PrimeTimeWindow(enabled=False, start=0, end=0)
        distinct_devices = sorted({assignment.device for assignment in drives})
        highest_device_minus_seven = distinct_devices[-1] - 7 if distinct_devices else 0
        drive_count = len(distinct_devices)
        return cls(
            drives=drives,
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


__all__ = [
    "DriveAssignment",
    "PrimeTimeWindow",
    "SetupDefaults",
    "SysopProfile",
]
