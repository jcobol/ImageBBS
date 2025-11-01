"""Runtime modules exposed by the ImageBBS package."""
from __future__ import annotations

from typing import Any

from . import ampersand_overrides as _ampersand_overrides
from . import cli as _cli
from . import console_ui as _console_ui
from . import file_transfers as _file_transfers
from . import indicator_controller as _indicator_controller
from . import macro_rendering as _macro_rendering
from . import main_menu as _main_menu
from . import masked_input as _masked_input
from . import masked_pane_staging as _masked_pane_staging
from . import message_store as _message_store
from . import message_store_repository as _message_store_repository
from . import session_instrumentation as _session_instrumentation
from . import session_runner as _session_runner
from . import sysop_options as _sysop_options
from . import transports as _transports

_modules = [
    _ampersand_overrides,
    _cli,
    _console_ui,
    _file_transfers,
    _indicator_controller,
    _macro_rendering,
    _main_menu,
    _masked_input,
    _masked_pane_staging,
    _message_store,
    _message_store_repository,
    _session_instrumentation,
    _session_runner,
    _sysop_options,
    _transports,
]

__all__: list[str] = []
_seen: set[str] = set()
for _module in _modules:
    for _name in _module.__all__:
        if _name not in _seen:
            _seen.add(_name)
            __all__.append(_name)
        globals()[_name] = getattr(_module, _name)


def __getattr__(name: str) -> Any:
    for _module in _modules:
        if hasattr(_module, name):
            return getattr(_module, name)
    raise AttributeError(name)


def __dir__() -> list[str]:
    return sorted(__all__)
