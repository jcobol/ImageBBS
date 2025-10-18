"""High-level ampersand dispatcher that mirrors the ImageBBS wedge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import MutableMapping, Optional, Tuple

from .ampersand_registry import AmpersandRegistry, AmpersandResult


@dataclass(frozen=True)
class AmpersandInvocation:
    """Parsed representation of a single ampersand call."""

    routine: int
    argument_x: int
    argument_y: int
    expression: str


@dataclass(frozen=True)
class AmpersandDispatchContext:
    """Context wrapper passed to registry handlers."""

    invocation: AmpersandInvocation
    payload: object | None = None


class AmpersandDispatcher:
    """Parse ampersand expressions and delegate to registry handlers."""

    name = "ampersand"

    def __init__(
        self,
        registry: Optional[AmpersandRegistry] = None,
        *,
        services: Optional[MutableMapping[str, object]] = None,
    ) -> None:
        self._registry = registry or AmpersandRegistry(services=services)
        self._last_invocation: AmpersandInvocation | None = None
        self._last_remainder: str = ""

    @property
    def registry(self) -> AmpersandRegistry:
        """Return the backing :class:`AmpersandRegistry`."""

        return self._registry

    @property
    def services(self):
        """Expose the shared service mapping used by the registry."""

        return self._registry.services

    @property
    def last_invocation(self) -> AmpersandInvocation | None:
        """Return the most recent invocation parsed by :meth:`dispatch`."""

        return self._last_invocation

    @property
    def remainder(self) -> str:
        """Return the unparsed suffix from the most recent dispatch."""

        return self._last_remainder

    def dispatch(
        self, text: str, payload: object | None = None
    ) -> AmpersandResult:
        """Parse ``text`` and dispatch the selected routine."""

        invocation, remainder = self.parse_invocation(text)
        self._last_invocation = invocation
        self._last_remainder = remainder
        context = AmpersandDispatchContext(invocation=invocation, payload=payload)
        return self._registry.dispatch(invocation.routine, context)

    def parse_invocation(self, text: str) -> Tuple[AmpersandInvocation, str]:
        """Return the parsed invocation and the unconsumed suffix."""

        index = 0
        length = len(text)

        def skip_whitespace() -> None:
            nonlocal index
            while index < length and text[index].isspace():
                index += 1

        skip_whitespace()
        if index < length and text[index] == "&":
            index += 1
        skip_whitespace()
        if index < length and text[index] == ",":
            index += 1
        skip_whitespace()

        start_expression = 0

        routine_literal, index = self._read_literal(text, index)
        routine = self._coerce_byte(routine_literal)

        argument_x = 0
        argument_y = 0

        index = self._skip_whitespace(text, index)
        if index < length and text[index] == ",":
            index += 1
            literal, index = self._read_literal(text, index)
            argument_x = self._coerce_byte(literal)
            index = self._skip_whitespace(text, index)
            if index < length and text[index] == ",":
                index += 1
                literal, index = self._read_literal(text, index)
                argument_y = self._coerce_byte(literal)

        expression = text[start_expression:index]
        remainder = text[index:]
        invocation = AmpersandInvocation(
            routine=routine,
            argument_x=argument_x,
            argument_y=argument_y,
            expression=expression,
        )
        return invocation, remainder

    def _read_literal(self, text: str, index: int) -> Tuple[str, int]:
        length = len(text)
        index = self._skip_whitespace(text, index)
        start = index
        while index < length and text[index] not in ",:\r\n\t ":
            index += 1
        if start == index:
            raise ValueError("ampersand expression missing numeric literal")
        literal = text[start:index]
        return literal, index

    def _skip_whitespace(self, text: str, index: int) -> int:
        length = len(text)
        while index < length and text[index].isspace():
            index += 1
        return index

    def _coerce_byte(self, literal: str) -> int:
        text = literal.strip()
        if not text:
            raise ValueError("ampersand arguments must not be empty")
        base = 16 if text.lower().startswith("0x") else 10
        try:
            value = int(text, base=base)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"invalid ampersand argument '{literal}'") from exc
        return max(0, min(0xFF, value))


__all__ = [
    "AmpersandDispatcher",
    "AmpersandDispatchContext",
    "AmpersandInvocation",
]
