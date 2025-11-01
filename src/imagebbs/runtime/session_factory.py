"""Factory helpers for constructing runtime session components."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Callable, Dict

from ..message_editor import MessageEditor, SessionContext
from ..setup_config import load_drive_config
from ..setup_defaults import (
    DriveAssignment,
    FilesystemDriveLocator,
    IndicatorDefaults,
    ModemDefaults,
    SetupDefaults,
)
from ..storage_config import StorageConfig, load_storage_config
from .main_menu import MainMenuModule
from .message_store import MessageStore
from .message_store_repository import load_message_store, save_message_store
from .session_runner import SessionRunner


SessionRunnerBuilder = Callable[
    [SetupDefaults, MessageStore, SessionContext, Path | None], SessionRunner
]
SessionContextBuilder = Callable[
    [SetupDefaults, MessageStore, Path | None, argparse.Namespace | None],
    SessionContext,
]
DefaultsBuilder = Callable[[argparse.Namespace], SetupDefaults]
MessageStoreLoader = Callable[[argparse.Namespace], MessageStore]
MessageStoreSaver = Callable[[MessageStore, Path], None]


class RuntimeSessionFactory:
    """Factory orchestrating the construction of runtime sessions."""

    def __init__(
        self,
        *,
        defaults_builder: DefaultsBuilder,
        message_store_loader: MessageStoreLoader,
        session_context_builder: SessionContextBuilder,
        message_store_saver: MessageStoreSaver,
        runner_builder: SessionRunnerBuilder,
    ) -> None:
        self._defaults_builder = defaults_builder
        self._message_store_loader = message_store_loader
        self._session_context_builder = session_context_builder
        self._message_store_saver = message_store_saver
        self._runner_builder = runner_builder

    def build_defaults(self, args: argparse.Namespace) -> SetupDefaults:
        """Return setup defaults configured according to ``args``."""

        return self._defaults_builder(args)

    def build_message_store(self, args: argparse.Namespace) -> MessageStore:
        """Return the message store backing the session."""

        return self._message_store_loader(args)

    def build_session_context(
        self,
        defaults: SetupDefaults,
        *,
        store: MessageStore,
        messages_path: Path | None,
        args: argparse.Namespace | None = None,
    ) -> SessionContext:
        """Return a :class:`SessionContext` seeded with the persistence hooks."""

        return self._session_context_builder(defaults, store, messages_path, args)

    def create_runner(self, args: argparse.Namespace) -> SessionRunner:
        """Create a :class:`SessionRunner` configured with ``args``."""

        defaults = self.build_defaults(args)
        store = self.build_message_store(args)
        messages_path: Path | None = getattr(args, "messages_path", None)
        session_context = self.build_session_context(
            defaults, store=store, messages_path=messages_path, args=args
        )
        return self._runner_builder(defaults, store, session_context, messages_path)

    def persist_messages(self, args: argparse.Namespace, runner: SessionRunner) -> None:
        """Persist ``runner``'s message store if the CLI supplied a path."""

        path: Path | None = getattr(args, "messages_path", None)
        if path is None:
            return
        initial_keys = getattr(runner, "_initial_message_keys", None)
        self._message_store_saver(
            runner.message_store, path, initial_keys=initial_keys
        )


def _indicator_override_kwargs(args: argparse.Namespace) -> Dict[str, object]:
    # Why: normalise CLI indicator arguments into dataclass-compatible override payloads.
    mapping = {
        "indicator_pause_colour": "pause_colour",
        "indicator_abort_colour": "abort_colour",
        "indicator_spinner_colour": "spinner_colour",
        "indicator_carrier_leading_colour": "carrier_leading_colour",
        "indicator_carrier_indicator_colour": "carrier_indicator_colour",
    }
    overrides: Dict[str, object] = {}
    for arg_name, field_name in mapping.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            overrides[field_name] = value
    spinner_frames = getattr(args, "indicator_spinner_frames", None)
    if spinner_frames is not None:
        overrides["spinner_frames"] = tuple(spinner_frames)
    return overrides


def _merge_indicator_defaults(
    base: IndicatorDefaults, overrides: Dict[str, object]
) -> IndicatorDefaults:
    # Why: reuse dataclass replacement so CLI overrides respect config- or stub-sourced defaults.
    if not overrides:
        return base
    return replace(base, **overrides)


def _apply_indicator_overrides(
    defaults: SetupDefaults, overrides: Dict[str, object]
) -> SetupDefaults:
    # Why: weave indicator overrides into the defaults object while preserving other configuration mutations.
    if not overrides:
        return defaults
    merged_indicator = _merge_indicator_defaults(defaults.indicator, overrides)
    return replace(defaults, indicator=merged_indicator)


def _build_defaults_from_args(args: argparse.Namespace) -> SetupDefaults:
    # Why: merge CLI-supplied configuration into stub defaults before sessions spin up.
    defaults = SetupDefaults.stub()
    indicator_overrides = _indicator_override_kwargs(args)

    storage_config_path: Path | None = getattr(args, "storage_config", None)
    if storage_config_path is not None:
        if not storage_config_path.exists():
            raise SystemExit(f"storage configuration not found: {storage_config_path}")
        storage = load_storage_config(storage_config_path)
        defaults = _apply_storage_config(defaults, storage)
        baud_override = getattr(args, "baud_limit", None)
        if baud_override is not None:
            defaults = replace(defaults, modem=ModemDefaults(baud_limit=baud_override))
        defaults = _apply_indicator_overrides(defaults, indicator_overrides)
        return defaults

    config_path: Path | None = getattr(args, "drive_config", None)
    if config_path is None:
        baud_override = getattr(args, "baud_limit", None)
        if baud_override is not None:
            defaults = replace(defaults, modem=ModemDefaults(baud_limit=baud_override))
        defaults = _apply_indicator_overrides(defaults, indicator_overrides)
        return defaults

    if not config_path.exists():
        raise SystemExit(f"drive configuration not found: {config_path}")

    config = load_drive_config(config_path)
    defaults = replace(defaults, drives=config.drives, indicator=config.indicator)
    ampersand_overrides = dict(config.ampersand_overrides)
    modem_override = config.modem_baud_limit
    baud_override = getattr(args, "baud_limit", None)
    if baud_override is not None:
        modem_override = baud_override
    if modem_override is not None:
        defaults = replace(defaults, modem=ModemDefaults(baud_limit=modem_override))
    defaults = _apply_indicator_overrides(defaults, indicator_overrides)
    object.__setattr__(defaults, "ampersand_overrides", ampersand_overrides)
    return defaults


def _apply_storage_config(
    defaults: SetupDefaults, storage: StorageConfig
) -> SetupDefaults:
    assignments = list(defaults.drives)
    drive_slots: Dict[int, int] = {}

    def ensure_slot(slot: int) -> None:
        while len(assignments) < slot:
            assignments.append(
                DriveAssignment(slot=len(assignments) + 1, locator=None)
            )

    for drive, mapping in sorted(storage.drives.items()):
        slot = drive - 7
        if slot < 1:
            slot = len(assignments) + 1
        ensure_slot(slot)
        assignments[slot - 1] = DriveAssignment(
            slot=slot,
            locator=FilesystemDriveLocator(
                path=mapping.root, read_only=mapping.read_only
            ),
        )
        drive_slots[drive] = slot

    defaults = replace(defaults, drives=tuple(assignments))

    filesystem_roots = {drive: mapping.root for drive, mapping in storage.drives.items()}
    object.__setattr__(defaults, "filesystem_drive_roots", filesystem_roots)
    object.__setattr__(defaults, "default_filesystem_drive", storage.default_drive)
    default_slot = (
        drive_slots.get(storage.default_drive) if storage.default_drive is not None else None
    )
    object.__setattr__(defaults, "default_filesystem_drive_slot", default_slot)
    object.__setattr__(defaults, "filesystem_drive_slots", drive_slots)
    object.__setattr__(defaults, "storage_config", storage)
    return defaults


def _load_message_store_from_args(args: argparse.Namespace) -> MessageStore:
    messages_path: Path | None = getattr(args, "messages_path", None)
    if messages_path is None:
        return MessageStore()
    return load_message_store(messages_path)


def _build_session_context_from_defaults(
    defaults: SetupDefaults,
    store: MessageStore,
    messages_path: Path | None,
    args: argparse.Namespace | None,
) -> SessionContext:
    board_override = getattr(args, "board_id", None) if args is not None else None
    user_override = getattr(args, "user_id", None) if args is not None else None

    board_id = board_override or getattr(defaults, "board_identifier", None) or "main"
    sysop = getattr(defaults, "sysop", None)
    default_user_id = getattr(sysop, "login_id", None) or "sysop"
    user_id = user_override or default_user_id

    context = SessionContext(board_id=board_id, user_id=user_id, store=store)
    services = dict(context.services or {})
    if messages_path is not None:
        services["message_store_persistence"] = {"path": messages_path}
    context.services = services
    return context


def _build_session_runner(
    defaults: SetupDefaults,
    store: MessageStore,
    session_context: SessionContext,
    messages_path: Path | None,
) -> SessionRunner:
    return SessionRunner(
        defaults=defaults,
        main_menu_module=MainMenuModule(
            message_editor_factory=lambda: MessageEditor(store=store)
        ),
        session_context=session_context,
        message_store=store,
        message_store_path=messages_path,
    )


DEFAULT_RUNTIME_SESSION_FACTORY = RuntimeSessionFactory(
    defaults_builder=_build_defaults_from_args,
    message_store_loader=_load_message_store_from_args,
    session_context_builder=_build_session_context_from_defaults,
    message_store_saver=save_message_store,
    runner_builder=_build_session_runner,
)


__all__ = [
    "DEFAULT_RUNTIME_SESSION_FACTORY",
    "RuntimeSessionFactory",
]
