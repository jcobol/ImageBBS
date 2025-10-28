"""Ampersand dispatcher wired to the native registry implementation."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Tuple

from .registry import AmpersandRegistry


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
        registry: AmpersandRegistry | None = None,
        *,
        services: MutableMapping[str, object] | None = None,
    ) -> None:
        self._registry = registry or AmpersandRegistry(services=services)
        self._last_invocation: AmpersandInvocation | None = None
        self._last_remainder: str = ""

    @property
    def registry(self) -> AmpersandRegistry:
        """Return the backing :class:`AmpersandRegistry`."""

        return self._registry

    @property
    def services(self) -> Mapping[str, object]:
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

    def dispatch(self, text: str, payload: object | None = None):
        """Parse ``text`` and dispatch the selected routine."""

        invocation, remainder = self.parse_invocation(text)
        self._last_invocation = invocation
        self._last_remainder = remainder
        merged_payload = self._build_dispatch_payload(payload)
        context = AmpersandDispatchContext(
            invocation=invocation, payload=merged_payload
        )
        return self._registry.dispatch(invocation.routine, context)

    def parse_invocation(self, text: str) -> Tuple[AmpersandInvocation, str]:
        """Return the parsed invocation and the unconsumed suffix."""

        index = 0
        length = len(text)

        def skip_initial_whitespace() -> None:
            nonlocal index
            while index < length and text[index].isspace():
                index += 1

        skip_initial_whitespace()
        if index < length and text[index] == "&":
            index += 1
        skip_initial_whitespace()
        if index < length and text[index] == ",":
            index += 1
        skip_initial_whitespace()

        start_expression = 0

        routine, index = self._consume_byte_expression(text, index)

        argument_x = 0
        argument_y = 0

        index = self._skip_whitespace(text, index)
        if index < length and text[index] == ",":
            index += 1
            argument_x, index = self._consume_byte_expression(text, index)
            index = self._skip_whitespace(text, index)
            if index < length and text[index] == ",":
                index += 1
                argument_y, index = self._consume_byte_expression(text, index)

        expression = text[start_expression:index]
        remainder = text[index:]
        invocation = AmpersandInvocation(
            routine=routine,
            argument_x=argument_x,
            argument_y=argument_y,
            expression=expression,
        )
        return invocation, remainder

    def _build_dispatch_payload(self, payload: object | None) -> object:
        base_payload: dict[str, object] = {
            "registry": self.registry,
            "services": self.services,
        }
        if payload is None:
            return base_payload
        if isinstance(payload, Mapping):
            merged_payload = dict(base_payload)
            merged_payload.update(payload)
            return merged_payload
        merged_payload = dict(base_payload)
        merged_payload["payload"] = payload
        return merged_payload

    def _consume_byte_expression(self, text: str, index: int) -> Tuple[int, int]:
        expression, index = self._read_expression(text, index)
        value = self._evaluate_numeric_expression(expression)
        return self._clamp_byte(value), index

    def _read_expression(self, text: str, index: int) -> Tuple[str, int]:
        length = len(text)
        index = self._skip_whitespace(text, index)
        start = index
        last_non_space = start - 1
        depth = 0

        while index < length:
            char = text[index]
            if char in ",:" and depth == 0:
                break
            if char in "\r\n":
                break
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    raise ValueError("ampersand expression has unmatched ')'")
            if not char.isspace():
                last_non_space = index
            index += 1

        if depth != 0:
            raise ValueError("ampersand expression has unmatched '('")

        if last_non_space < start:
            raise ValueError("ampersand expression missing numeric literal")

        expression = text[start : last_non_space + 1]
        index = self._skip_whitespace(text, index)
        return expression, index

    def _skip_whitespace(self, text: str, index: int) -> int:
        length = len(text)
        while index < length and text[index].isspace():
            index += 1
        return index

    def _evaluate_numeric_expression(self, expression: str) -> float:
        evaluator = _NumericExpressionEvaluator(expression)
        try:
            return evaluator.evaluate()
        except ZeroDivisionError as exc:  # pragma: no cover - defensive guard
            raise ValueError("ampersand expression division by zero") from exc
        except ValueError:
            raise
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"invalid ampersand expression '{expression}'") from exc

    def _clamp_byte(self, value: float) -> int:
        if math.isnan(value) or math.isinf(value):
            raise ValueError("ampersand expression produced non-finite result")
        integer = math.floor(value)
        if integer < 0:
            return 0
        if integer > 0xFF:
            return 0xFF
        return int(integer)


class _NumericExpressionEvaluator:
    """Parse and evaluate BASIC-style arithmetic expressions."""

    def __init__(self, text: str) -> None:
        self._text = text
        self._length = len(text)
        self._index = 0

    def evaluate(self) -> float:
        self._skip_whitespace()
        value = self._parse_expression()
        self._skip_whitespace()
        if self._index != self._length:
            raise ValueError(
                "unexpected trailing characters in ampersand expression: "
                f"{self._text[self._index:]}"
            )
        return value

    def _parse_expression(self) -> float:
        value = self._parse_term()
        while True:
            self._skip_whitespace()
            if self._match("+"):
                value += self._parse_term()
            elif self._match("-"):
                value -= self._parse_term()
            else:
                break
        return value

    def _parse_term(self) -> float:
        value = self._parse_power()
        while True:
            self._skip_whitespace()
            if self._match("*"):
                value *= self._parse_power()
            elif self._match("/"):
                divisor = self._parse_power()
                if divisor == 0:
                    raise ZeroDivisionError("division by zero in ampersand expression")
                value /= divisor
            else:
                break
        return value

    def _parse_power(self) -> float:
        value = self._parse_factor()
        self._skip_whitespace()
        if self._match("^"):
            exponent = self._parse_power()
            value = value ** exponent
        return value

    def _parse_factor(self) -> float:
        self._skip_whitespace()
        if self._match("+"):
            return self._parse_factor()
        if self._match("-"):
            return -self._parse_factor()
        return self._parse_primary()

    def _parse_primary(self) -> float:
        self._skip_whitespace()
        if self._match("("):
            value = self._parse_expression()
            self._skip_whitespace()
            if not self._match(")"):
                raise ValueError("ampersand expression has unmatched '('")
            return value
        return self._parse_number()

    def _parse_number(self) -> float:
        self._skip_whitespace()
        if self._index >= self._length:
            raise ValueError("ampersand expression missing numeric literal")

        start = self._index
        text = self._text
        if text[self._index] == "$":
            self._index += 1
            start_digits = self._index
            while self._index < self._length and text[self._index] in "0123456789abcdefABCDEF":
                self._index += 1
            if start_digits == self._index:
                raise ValueError("ampersand expression missing hex digits")
            return float(int(text[start_digits:self._index], 16))

        if (
            text[self._index] == "0"
            and self._index + 1 < self._length
            and text[self._index + 1] in "xX"
        ):
            self._index += 2
            start_digits = self._index
            while self._index < self._length and text[self._index] in "0123456789abcdefABCDEF":
                self._index += 1
            if start_digits == self._index:
                raise ValueError("ampersand expression missing hex digits")
            return float(int(text[start_digits:self._index], 16))

        has_digits = False
        while self._index < self._length and text[self._index].isdigit():
            self._index += 1
            has_digits = True

        if self._index < self._length and text[self._index] == ".":
            self._index += 1
            while self._index < self._length and text[self._index].isdigit():
                self._index += 1
                has_digits = True

        if not has_digits:
            raise ValueError("ampersand expression missing numeric literal")

        if (
            self._index < self._length
            and text[self._index] in "eE"
        ):
            self._index += 1
            if (
                self._index < self._length
                and text[self._index] in "+-"
            ):
                self._index += 1
            exp_start = self._index
            while self._index < self._length and text[self._index].isdigit():
                self._index += 1
            if exp_start == self._index:
                raise ValueError("ampersand expression has malformed exponent")

        number_text = text[start:self._index]
        try:
            return float(number_text)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise ValueError(
                f"invalid ampersand numeric literal '{number_text}'"
            ) from exc

    def _skip_whitespace(self) -> None:
        text = self._text
        while self._index < self._length and text[self._index] in " \t\r\n":
            self._index += 1

    def _match(self, token: str) -> bool:
        if self._index < self._length and self._text[self._index] == token:
            self._index += 1
            return True
        return False


__all__ = [
    "AmpersandDispatchContext",
    "AmpersandDispatcher",
    "AmpersandInvocation",
]


def _mirror_prototype_module() -> None:
    try:
        import scripts.prototypes.ampersand_dispatcher as _prototype  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        return

    for name in __all__:
        setattr(_prototype, name, globals()[name])

    try:
        import scripts.prototypes as _prototypes  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        _prototypes = None
    if _prototypes is not None:
        for name in __all__:
            setattr(_prototypes, name, globals()[name])

    import sys

    pkg = sys.modules.get("imagebbs")
    if pkg is not None:
        for name in __all__:
            setattr(pkg, name, globals()[name])
            try:
                exported = pkg.__all__  # type: ignore[attr-defined]
            except AttributeError:  # pragma: no cover - defensive guard
                continue
            if name not in exported:
                exported.append(name)

    try:
        import scripts.prototypes.session_kernel as _kernel  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        _kernel = None
    if _kernel is not None:
        if hasattr(_kernel, "AmpersandDispatcher"):
            _kernel.AmpersandDispatcher = AmpersandDispatcher
        if hasattr(_kernel, "AmpersandDispatchContext"):
            _kernel.AmpersandDispatchContext = AmpersandDispatchContext
        if hasattr(_kernel, "AmpersandInvocation"):
            _kernel.AmpersandInvocation = AmpersandInvocation

    try:
        import scripts.prototypes.runtime.ampersand_overrides as _overrides  # type: ignore[import-not-found]
    except ModuleNotFoundError:  # pragma: no cover - prototype mirrors optional at runtime
        _overrides = None
    if _overrides is not None:
        if hasattr(_overrides, "AmpersandDispatchContext"):
            _overrides.AmpersandDispatchContext = AmpersandDispatchContext
        if hasattr(_overrides, "AmpersandInvocation"):
            _overrides.AmpersandInvocation = AmpersandInvocation


_mirror_prototype_module()
