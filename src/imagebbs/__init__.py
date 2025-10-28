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

from . import device_context as _device_context
from . import setup_config as _setup_config
from . import setup_defaults as _setup_defaults

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

for _override in getattr(_setup_defaults, "__all__", ()):  # pragma: no branch - data-driven
    globals()[_override] = getattr(_setup_defaults, _override)
    if _override not in __all__:
        __all__.append(_override)

for _override in getattr(_setup_config, "__all__", ()):  # pragma: no branch - data-driven
    globals()[_override] = getattr(_setup_config, _override)
    if _override not in __all__:
        __all__.append(_override)

for _override in getattr(_device_context, "__all__", ()):  # pragma: no branch - data-driven
    globals()[_override] = getattr(_device_context, _override)
    if _override not in __all__:
        __all__.append(_override)

def __getattr__(name: str) -> Any:
    return getattr(_prototypes, name)


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(dir(_prototypes)))
