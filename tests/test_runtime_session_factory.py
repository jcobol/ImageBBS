from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import pytest

from imagebbs.runtime.cli import parse_args
from imagebbs.runtime.message_store import MessageStore
from imagebbs.runtime.session_factory import DEFAULT_RUNTIME_SESSION_FACTORY
from imagebbs.setup_defaults import FilesystemDriveLocator
from imagebbs.storage_config import StorageConfigError


def _namespace(**kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_factory_missing_drive_config_raises(tmp_path: Path) -> None:
    factory = DEFAULT_RUNTIME_SESSION_FACTORY
    missing = tmp_path / "missing.toml"
    args = _namespace(drive_config=missing, baud_limit=None, messages_path=None)

    with pytest.raises(SystemExit, match="drive configuration not found"):
        factory.build_defaults(args)


def test_factory_missing_storage_config_raises(tmp_path: Path) -> None:
    factory = DEFAULT_RUNTIME_SESSION_FACTORY
    missing = tmp_path / "missing.toml"
    args = parse_args(["--storage-config", str(missing)])

    with pytest.raises(SystemExit, match="storage configuration not found"):
        factory.build_defaults(args)


def test_factory_applies_cli_baud_override(tmp_path: Path) -> None:
    config_path = tmp_path / "drives.toml"
    config_path.write_text(
        "\n".join(
            [
                "[slots]",
                '1 = "."',
                "[modem]",
                "baud_limit = 2400",
                "",
            ]
        )
    )

    args = parse_args(
        [
            "--drive-config",
            str(config_path),
            "--baud-limit",
            "9600",
        ]
    )

    factory = DEFAULT_RUNTIME_SESSION_FACTORY
    defaults = factory.build_defaults(args)

    assert defaults.modem.baud_limit == 9600


def test_factory_translates_storage_config_to_filesystem_drives(
    tmp_path: Path,
) -> None:
    drive8 = tmp_path / "drive8"
    drive9 = tmp_path / "drive9"
    drive8.mkdir()
    drive9.mkdir()
    storage_path = tmp_path / "storage.toml"
    storage_path.write_text(
        textwrap.dedent(
            """
            [storage]
            default_drive = 9

            [[storage.drives]]
            drive = 8
            path = "drive8"

            [[storage.drives]]
            drive = 9
            path = "drive9"
            read_only = true
            """
        ),
        encoding="utf-8",
    )

    args = parse_args(["--storage-config", str(storage_path)])

    factory = DEFAULT_RUNTIME_SESSION_FACTORY
    defaults = factory.build_defaults(args)

    filesystem_assignments = [
        assignment
        for assignment in defaults.drives
        if isinstance(assignment.locator, FilesystemDriveLocator)
    ]
    assert filesystem_assignments
    paths_by_slot = {
        assignment.slot: assignment.locator.path
        for assignment in filesystem_assignments
    }
    assert paths_by_slot[1] == drive8.resolve()
    assert paths_by_slot[2] == drive9.resolve()

    read_only_flags = {
        assignment.slot: assignment.read_only for assignment in filesystem_assignments
    }
    assert read_only_flags[1] is False
    assert read_only_flags[2] is True

    assert defaults.filesystem_drive_roots == {
        8: drive8.resolve(),
        9: drive9.resolve(),
    }
    assert defaults.default_filesystem_drive == 9
    assert defaults.default_filesystem_drive_slot == 2

    storage = getattr(defaults, "storage_config", None)
    assert storage is not None

    with pytest.raises(StorageConfigError, match="read-only"):
        storage.validate_save_target("IMMUTABLE", drive=9)

    target = storage.validate_save_target("WRITABLE", drive=8)
    assert target == drive8 / "WRITABLE"


def test_factory_registers_persistence_hook(tmp_path: Path) -> None:
    messages_path = tmp_path / "messages.json"
    args = parse_args(["--messages-path", str(messages_path)])

    factory = DEFAULT_RUNTIME_SESSION_FACTORY
    defaults = factory.build_defaults(args)
    store = factory.build_message_store(args)
    assert isinstance(store, MessageStore)
    context = factory.build_session_context(
        defaults, store=store, messages_path=messages_path
    )

    services = context.services
    assert services is not None
    assert services["message_store_persistence"] == {"path": messages_path}
