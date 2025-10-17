"""Service registry for dispatching ImageBBS ampersand handlers."""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Dict, Iterable, Mapping, MutableMapping, Optional

from .ml_extra_defaults import FlagRecord, MLExtraDefaults


@dataclass(frozen=True)
class AmpersandResult:
    """Outcome produced by an ampersand handler dispatch."""

    flag_index: int
    slot: int
    handler_address: int
    flag_records: tuple[FlagRecord, ...]
    flag_directory_block: tuple[int, ...]
    flag_directory_tail: tuple[int, ...]
    flag_directory_text: str
    context: object
    rendered_text: Optional[str] = None


AmpersandHandler = Callable[[object], AmpersandResult]


class AmpersandRegistry:
    """Registry that resolves ampersand flag indices to callable handlers."""

    def __init__(
        self,
        defaults: Optional[MLExtraDefaults] = None,
        override_imports: Optional[Mapping[int, str]] = None,
    ) -> None:
        self._defaults = defaults or MLExtraDefaults.from_overlay()
        self._default_handlers = self._build_default_handlers()
        self._overrides: Dict[int, AmpersandHandler] = {}
        if override_imports:
            self._load_override_imports(override_imports)

    @property
    def defaults(self) -> MLExtraDefaults:
        """Return the overlay defaults backing the registry."""

        return self._defaults

    def register_handler(self, flag_index: int, handler: AmpersandHandler) -> None:
        """Register an override handler for ``flag_index``."""

        if flag_index not in self._default_handlers:
            raise KeyError(f"unknown ampersand flag index: {flag_index:#x}")
        self._overrides[flag_index] = handler

    def unregister_handler(self, flag_index: int) -> None:
        """Remove a previously-registered override handler."""

        self._overrides.pop(flag_index, None)

    def dispatch(
        self,
        flag_index: int,
        context: object = None,
        *,
        use_default: bool = False,
    ) -> AmpersandResult:
        """Invoke the handler associated with ``flag_index``."""

        handler = self._resolve_handler(flag_index, use_default=use_default)
        return handler(context)

    def get_default_handler(self, flag_index: int) -> AmpersandHandler:
        """Return the default handler for ``flag_index``."""

        try:
            return self._default_handlers[flag_index]
        except KeyError as exc:  # pragma: no cover - defensive guard
            raise KeyError(f"no default handler for flag index: {flag_index:#x}") from exc

    def available_flag_indices(self) -> Iterable[int]:
        """Return the flag indices available in the registry."""

        return self._default_handlers.keys()

    def _resolve_handler(
        self, flag_index: int, *, use_default: bool = False
    ) -> AmpersandHandler:
        if not use_default:
            handler = self._overrides.get(flag_index)
            if handler is not None:
                return handler
        try:
            return self._default_handlers[flag_index]
        except KeyError as exc:
            raise KeyError(f"no handler registered for flag index: {flag_index:#x}") from exc

    def _build_default_handlers(self) -> MutableMapping[int, AmpersandHandler]:
        handlers: Dict[int, AmpersandHandler] = {}
        for entry in self._defaults.flag_dispatch.entries:
            handlers[entry.flag_index] = self._make_default_handler(entry.flag_index, entry.slot, entry.handler_address)
        return handlers

    def _make_default_handler(
        self, flag_index: int, slot: int, handler_address: int
    ) -> AmpersandHandler:
        def handler(context: object) -> AmpersandResult:
            return AmpersandResult(
                flag_index=flag_index,
                slot=slot,
                handler_address=handler_address,
                flag_records=self._defaults.flag_records,
                flag_directory_block=self._defaults.flag_directory_block,
                flag_directory_tail=self._defaults.flag_directory_tail,
                flag_directory_text=self._defaults.flag_directory_text,
                context=context,
            )

        return handler

    def _load_override_imports(self, override_imports: Mapping[int, str]) -> None:
        for flag_index, import_path in override_imports.items():
            handler = self._import_handler(import_path)
            self.register_handler(flag_index, handler)

    def _import_handler(self, import_path: str) -> AmpersandHandler:
        module_name, attribute_path = _split_import_path(import_path)
        module = import_module(module_name)
        handler: object = module
        for attribute in attribute_path.split("."):
            try:
                handler = getattr(handler, attribute)
            except AttributeError as exc:  # pragma: no cover - defensive guard
                raise ImportError(
                    f"ampersand override '{import_path}' missing attribute '{attribute}'"
                ) from exc

        if not callable(handler):
            raise TypeError(
                f"ampersand override '{import_path}' resolved to non-callable {type(handler)!r}"
            )

        return handler


def _split_import_path(import_path: str) -> tuple[str, str]:
    if ":" in import_path:
        module_name, attribute_path = import_path.split(":", 1)
    else:
        try:
            module_name, attribute_path = import_path.rsplit(".", 1)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(
                "ampersand override must include a module and attribute"
            ) from exc

    module_name = module_name.strip()
    attribute_path = attribute_path.strip()
    if not module_name or not attribute_path:
        raise ValueError("ampersand override must specify a module and attribute")

    return module_name, attribute_path


__all__ = ["AmpersandRegistry", "AmpersandResult", "AmpersandHandler"]
