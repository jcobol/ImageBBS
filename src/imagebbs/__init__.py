"""Public ImageBBS API that mirrors the prototype re-exports."""
from __future__ import annotations

from importlib import import_module
from typing import Any

_prototypes = import_module("scripts.prototypes")
__all__ = list(getattr(_prototypes, "__all__", ()))
for _name in __all__:
    globals()[_name] = getattr(_prototypes, _name)

from .runtime.main_menu import MainMenuEvent, MainMenuModule, MenuCommand, MenuState
from .runtime.session_runner import SessionRunner

globals().update(
    MainMenuEvent=MainMenuEvent,
    MainMenuModule=MainMenuModule,
    MenuCommand=MenuCommand,
    MenuState=MenuState,
    SessionRunner=SessionRunner,
)

for _override in (
    "MainMenuEvent",
    "MainMenuModule",
    "MenuCommand",
    "MenuState",
    "SessionRunner",
):
    if _override not in __all__:
        __all__.append(_override)

def __getattr__(name: str) -> Any:
    return getattr(_prototypes, name)


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(dir(_prototypes)))
