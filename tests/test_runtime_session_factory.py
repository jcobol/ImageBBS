import argparse
from pathlib import Path

import pytest

from imagebbs.runtime.cli import parse_args
from imagebbs.runtime.message_store import MessageStore
from imagebbs.runtime.session_factory import DEFAULT_RUNTIME_SESSION_FACTORY


def _namespace(**kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_factory_missing_drive_config_raises(tmp_path: Path) -> None:
    factory = DEFAULT_RUNTIME_SESSION_FACTORY
    missing = tmp_path / "missing.toml"
    args = _namespace(drive_config=missing, baud_limit=None, messages_path=None)

    with pytest.raises(SystemExit, match="drive configuration not found"):
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
