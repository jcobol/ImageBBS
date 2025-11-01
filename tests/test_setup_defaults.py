"""Unit tests for :mod:`imagebbs.setup_defaults`."""
from __future__ import annotations

from pathlib import Path

from imagebbs.setup_defaults import (
    CommodoreDeviceDrive,
    DriveAssignment,
    DriveInventory,
    DeviceDriveMap,
    FilesystemDriveLocator,
    IndicatorDefaults,
    SetupDefaults,
    derive_drive_inventory,
    extract_overlay_sequence,
    load_setup_data_records,
)


EXPECTED_OVERLAYS = (
    "E.I.MACRO,S,R",
    "E.I.PROMPT,S,R",
    "E.AMAINT,S,R",
    "LBSETUP",
    "E.LOG",
    "ML.RS232",
    "ML.PMODES",
)


def test_extract_overlay_sequence_matches_stub_defaults() -> None:
    """The overlay sequence should mirror the stubbed metadata."""

    overlays = extract_overlay_sequence()
    assert overlays == EXPECTED_OVERLAYS


def test_derive_drive_inventory_filters_non_commodore() -> None:
    """Inventory computation should only consider Commodore tuples."""

    drives = (
        DriveAssignment(slot=1, locator=CommodoreDeviceDrive(device=8, drive=0)),
        DriveAssignment(slot=2, locator=CommodoreDeviceDrive(device=9, drive=0)),
        DriveAssignment(slot=3, locator=FilesystemDriveLocator(path=Path("/tmp"))),
        DriveAssignment(slot=4, locator=None),
    )
    inventory = derive_drive_inventory(drives)

    assert inventory == DriveInventory(
        highest_device=9,
        highest_device_minus_seven=2,
        device_count=2,
        logical_unit_count=2,
        devices=(
            DeviceDriveMap(device=8, drives=(0,)),
            DeviceDriveMap(device=9, drives=(0,)),
        ),
    )


def test_setup_defaults_stub_matches_known_defaults() -> None:
    """The native stub should expose the same data as the BASIC runtime."""

    defaults = SetupDefaults.stub()

    # Drive inventory.
    assert tuple(assignment.legacy_tuple() for assignment in defaults.drives) == (
        (8, 0),
        (9, 0),
        (10, 0),
        (11, 0),
        (0, 0),
        (0, 0),
    )
    assert defaults.drive_inventory.highest_device == 11
    assert defaults.drive_inventory.highest_device_minus_seven == 4
    assert defaults.drive_inventory.device_count == 4
    assert defaults.drive_inventory.logical_unit_count == 4
    assert defaults.active_drives == defaults.drives[:4]

    # Board metadata.
    assert defaults.board_identifier == "IM"
    assert defaults.board_name == "IMAGE BBS"
    assert defaults.prompt == "{pound}READY{pound}"
    assert defaults.new_user_credits == 25
    assert defaults.copyright_notice == "(c) 1990 FandF Products"

    # Sysop and statistics.
    assert defaults.sysop.login_id == "SYSOP"
    assert defaults.statistics.last_caller == "NO CALLERS YET"
    assert defaults.statistics.password_subs_password == ""
    assert defaults.statistics.total_calls == 0

    # Prime time and chat banners.
    assert not defaults.prime_time.is_enabled
    assert defaults.chat_mode_entering == "{cyan}* Entering Chat Mode *"
    assert defaults.chat_mode_exiting == "{yellow}* Exiting Chat Mode *"
    assert (
        defaults.chat_mode_returning_to_editor
        == "{white}* Returning to the Editor *"
    )

    # Modem defaults and overlays.
    assert defaults.modem.baud_limit == 1200
    indicator = defaults.indicator
    assert isinstance(indicator, IndicatorDefaults)
    assert indicator.pause_colour is None
    assert indicator.abort_colour is None
    assert indicator.spinner_colour is None
    assert indicator.carrier_leading_colour is None
    assert indicator.carrier_indicator_colour is None
    assert indicator.spinner_frames == tuple(range(0xB0, 0xBA))
    assert defaults.macro_modules == EXPECTED_OVERLAYS

    # DATA records pulled from the recovered listing.
    records = load_setup_data_records()
    assert records.co_options[0] == "COMMODORE 64"
    assert records.lightbar_char_codes[:3] == (32, 32, 32)
    assert records.lightbar_labels[-1] == "CONT"
