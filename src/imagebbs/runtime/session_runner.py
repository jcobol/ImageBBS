"""Runtime session runner that integrates the concrete main-menu module."""
from __future__ import annotations

from ..session_kernel import SessionState
from .main_menu import MainMenuEvent, MainMenuModule
from scripts.prototypes.runtime.session_runner import SessionRunner as _PrototypeSessionRunner


class SessionRunner(_PrototypeSessionRunner):
    """Adapter around the prototype runner that injects local modules."""

    def __post_init__(self) -> None:
        self._ENTER_EVENTS = dict(self._ENTER_EVENTS)
        self._ENTER_EVENTS[SessionState.MAIN_MENU] = MainMenuEvent.ENTER
        self._COMMAND_EVENTS = dict(self._COMMAND_EVENTS)
        self._COMMAND_EVENTS[SessionState.MAIN_MENU] = MainMenuEvent.SELECTION
        if not isinstance(self.main_menu_module, MainMenuModule):
            self.main_menu_module = MainMenuModule()
        super().__post_init__()


__all__ = ["SessionRunner"]
