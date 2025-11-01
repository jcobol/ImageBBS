"""Unit tests covering Telnet newline translation behaviour."""

from __future__ import annotations

import pytest

from imagebbs.runtime.transports import TelnetModemTransport


class _FakeRunner:
    def __init__(self) -> None:
        # Why: retain a predictable console buffer stub for transport construction.
        self._output = ""

    def read_output(self) -> str:
        # Why: provide the transport with an empty initial transcript during tests.
        return self._output


class _FakeReader:
    def __init__(self) -> None:
        # Why: supply the transport with an asyncio reader dependency placeholder.
        self._buffer = bytearray()


class _FakeWriter:
    def __init__(self) -> None:
        # Why: capture transport writes for validation in higher level tests.
        self.buffer: list[bytes] = []

    def write(self, data: bytes) -> None:
        # Why: store encoded payloads so TelnetModemTransport can operate in tests.
        self.buffer.append(data)


@pytest.mark.parametrize(
    ("newline_translation", "text", "expected"),
    (
        ("\r\n", "Alpha\nBeta\n", "Alpha\r\nBeta\r\n"),
        ("\n", "Gamma\nDelta\n", "Gamma\nDelta\n"),
        (None, "No translation\n", "No translation\n"),
    ),
)
def test_telnet_translate_outgoing_variants(
    newline_translation: str | None, text: str, expected: str
) -> None:
    # Why: ensure translate_outgoing maps ``\n`` to the configured newline sequence.
    transport = TelnetModemTransport(
        _FakeRunner(),
        _FakeReader(),  # type: ignore[arg-type]
        _FakeWriter(),  # type: ignore[arg-type]
        newline_translation=newline_translation,
    )

    assert transport.translate_outgoing(text) == expected


@pytest.mark.parametrize(
    ("newline_translation", "text", "expected"),
    (
        ("\r\n", "Alpha\r\nBeta\nGamma\r\n", "Alpha\nBeta\nGamma\n"),
        ("\n", "Delta\r\nEpsilon\n", "Delta\nEpsilon\n"),
    ),
)
def test_telnet_translate_incoming_variants(
    newline_translation: str, text: str, expected: str
) -> None:
    # Why: confirm translate_incoming normalises CRLF/LF input back to ``\n``.
    transport = TelnetModemTransport(
        _FakeRunner(),
        _FakeReader(),  # type: ignore[arg-type]
        _FakeWriter(),  # type: ignore[arg-type]
        newline_translation=newline_translation,
    )

    assert transport.translate_incoming(text) == expected


def test_telnet_translate_incoming_none_passthrough() -> None:
    # Why: verify newline translation ``None`` leaves inbound text untouched.
    transport = TelnetModemTransport(
        _FakeRunner(),
        _FakeReader(),  # type: ignore[arg-type]
        _FakeWriter(),  # type: ignore[arg-type]
        newline_translation=None,
    )

    payload = "Literal\r\nContent\n"

    assert transport.translate_incoming(payload) == payload
