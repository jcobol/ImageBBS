"""Unit tests for telnet negotiation filtering."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from imagebbs.runtime.transports import TelnetModemTransport


class _DummyWriter:
    def __init__(self) -> None:
        # Why: capture telnet replies for assertions without issuing network writes.
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> None:
        # Why: store outgoing frames emitted during negotiation so tests can examine them later.
        self.writes.append(data)

    async def drain(self) -> None:
        # Why: satisfy the transport's expectation that the writer exposes an awaitable drain method.
        return None


@pytest.fixture
def telnet_transport() -> TelnetModemTransport:
    # Why: provide a TelnetModemTransport with inert dependencies for isolated negotiation testing.
    runner = SimpleNamespace()
    reader = SimpleNamespace()
    writer = _DummyWriter()
    return TelnetModemTransport(runner, reader, writer)


def test_filter_telnet_negotiations_handles_payload_and_escaped_iac(
    telnet_transport: TelnetModemTransport,
) -> None:
    # Why: confirm regular payload bytes and escaped IAC characters survive filtering unchanged.
    data = b"hello" + bytes([telnet_transport._IAC, telnet_transport._IAC]) + b"world"
    payload, replies = telnet_transport._filter_telnet_negotiations(data)
    assert payload == b"hello" + bytes([telnet_transport._IAC]) + b"world"
    assert replies == []
    assert telnet_transport._telnet_buffer == bytearray()


def test_filter_telnet_negotiations_ignores_subnegotiation_frames(
    telnet_transport: TelnetModemTransport,
) -> None:
    # Why: ensure sub-negotiation sequences are discarded while surrounding payload is preserved.
    iac = telnet_transport._IAC
    sb = telnet_transport._SB
    se = telnet_transport._SE
    frame = bytes([iac, sb, 0x24, 0x01, iac, iac, 0x02, iac, se])
    mixed = b"abc" + frame + b"xyz"
    payload, replies = telnet_transport._filter_telnet_negotiations(mixed)
    assert payload == b"abcxyz"
    assert replies == []
    assert telnet_transport._telnet_buffer == bytearray()


def test_filter_telnet_negotiations_handles_command_replies_and_expectations(
    telnet_transport: TelnetModemTransport,
) -> None:
    # Why: verify WILL/DO style negotiations trigger the correct replies and clear expectations.
    iac = telnet_transport._IAC
    will = telnet_transport._WILL
    do = telnet_transport._DO
    dont = telnet_transport._DONT
    option_reply = 0x01
    option_expected = 0x02
    telnet_transport._expected_telnet_responses[option_expected] = {do}
    stream = b"x" + bytes([iac, will, option_reply, iac, do, option_expected])
    payload, replies = telnet_transport._filter_telnet_negotiations(stream)
    assert payload == b"x"
    assert replies == [bytes([iac, dont, option_reply])]
    assert option_expected not in telnet_transport._expected_telnet_responses
    assert telnet_transport._telnet_buffer == bytearray()


def test_filter_telnet_negotiations_buffers_incomplete_subnegotiation(
    telnet_transport: TelnetModemTransport,
) -> None:
    # Why: make sure incomplete sub-negotiation frames remain buffered until completion.
    iac = telnet_transport._IAC
    sb = telnet_transport._SB
    se = telnet_transport._SE
    first = b"a" + bytes([iac, sb, 0x30])
    payload, replies = telnet_transport._filter_telnet_negotiations(first)
    assert payload == b"a"
    assert replies == []
    assert telnet_transport._telnet_buffer == bytearray([iac, sb, 0x30])

    second = bytes([0x01, iac, se]) + b"b"
    payload, replies = telnet_transport._filter_telnet_negotiations(second)
    assert payload == b"b"
    assert replies == []
    assert telnet_transport._telnet_buffer == bytearray()
