"""Compatibility helpers for mirroring prototype modules."""
from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any, Iterable


def mirror_module(globals_dict: dict[str, Any], target: str) -> ModuleType:
    """Populate ``globals_dict`` with public members from ``target`` module.

    The helper imports ``target`` lazily, re-exports its ``__all__`` symbols into
    ``globals_dict``, and returns the imported module so wrappers can forward
    attribute access for names that fall outside the published surface area.
    """

    module = import_module(target)
    exports: Iterable[str] | None = getattr(module, "__all__", None)
    if exports is None:
        exports = [name for name in module.__dict__ if not name.startswith("_")]
    else:
        exports = list(exports)

    for name in exports:
        globals_dict[name] = getattr(module, name)

    exports_list = list(exports)
    globals_dict["__all__"] = exports_list
    globals_dict["__doc__"] = module.__doc__

    def _forward_getattr(name: str) -> Any:
        return getattr(module, name)

    def _forward_dir() -> list[str]:
        combined = set(exports_list)
        combined.update(dir(module))
        return sorted(combined)

    globals_dict["__getattr__"] = _forward_getattr
    globals_dict["__dir__"] = _forward_dir
    return module
