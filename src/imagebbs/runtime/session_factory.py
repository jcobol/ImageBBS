"""Factory helpers for constructing runtime session components."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Callable

from ..message_editor import MessageEditor, SessionContext
from ..setup_config import load_drive_config
from ..setup_defaults import ModemDefaults, SetupDefaults
from .main_menu import MainMenuModule
from .message_store import MessageStore
from .message_store_repository import load_message_store, save_message_store
from .session_runner import SessionRunner


SessionRunnerBuilder = Callable[
    [SetupDefaults, MessageStore, SessionContext, Path | None], SessionRunner
]
SessionContextBuilder = Callable[[SetupDefaults, MessageStore, Path | None], SessionContext]
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
    ) -> SessionContext:
        """Return a :class:`SessionContext` seeded with the persistence hooks."""

        return self._session_context_builder(defaults, store, messages_path)

    def create_runner(self, args: argparse.Namespace) -> SessionRunner:
        """Create a :class:`SessionRunner` configured with ``args``."""

        defaults = self.build_defaults(args)
        store = self.build_message_store(args)
        messages_path: Path | None = getattr(args, "messages_path", None)
        session_context = self.build_session_context(
            defaults, store=store, messages_path=messages_path
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


def _build_defaults_from_args(args: argparse.Namespace) -> SetupDefaults:
    defaults = SetupDefaults.stub()

    config_path: Path | None = getattr(args, "drive_config", None)
    if config_path is None:
        baud_override = getattr(args, "baud_limit", None)
        if baud_override is not None:
            defaults = replace(defaults, modem=ModemDefaults(baud_limit=baud_override))
        return defaults

    if not config_path.exists():
        raise SystemExit(f"drive configuration not found: {config_path}")

    config = load_drive_config(config_path)
    defaults = replace(defaults, drives=config.drives)
    ampersand_overrides = dict(config.ampersand_overrides)
    modem_override = config.modem_baud_limit
    baud_override = getattr(args, "baud_limit", None)
    if baud_override is not None:
        modem_override = baud_override
    if modem_override is not None:
        defaults = replace(defaults, modem=ModemDefaults(baud_limit=modem_override))
    object.__setattr__(defaults, "ampersand_overrides", ampersand_overrides)
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
) -> SessionContext:
    board_id = getattr(defaults, "board_identifier", None) or "main"
    sysop = getattr(defaults, "sysop", None)
    user_id = getattr(sysop, "login_id", None) or "sysop"

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
