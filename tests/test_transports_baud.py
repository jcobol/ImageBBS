import asyncio
from typing import List, Tuple

from imagebbs.device_context import LoopbackModemTransport
from imagebbs.runtime.transports import (
    BaudLimitedTransport,
    TelnetModemTransport,
    _TelnetEditorIO,
)
from imagebbs.session_kernel import SessionState


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0
        self._waiters: List[Tuple[float, asyncio.Future[object]]] = []

    def time(self) -> float:
        return self.current

    async def sleep(self, delay: float) -> object:
        if delay <= 0:
            await asyncio.sleep(0)
            return None
        loop = asyncio.get_running_loop()
        future: asyncio.Future[object] = loop.create_future()
        target = self.current + delay
        self._waiters.append((target, future))
        try:
            return await future
        finally:
            self._waiters = [(t, f) for (t, f) in self._waiters if f is not future]

    def advance(self, delta: float) -> None:
        self.current += delta
        ready: List[asyncio.Future[object]] = []
        pending: List[Tuple[float, asyncio.Future[object]]] = []
        for target, future in self._waiters:
            if target <= self.current:
                ready.append(future)
            else:
                pending.append((target, future))
        self._waiters = pending
        for future in ready:
            if not future.done():
                future.set_result(None)


class _StubRunner:
    def __init__(self) -> None:
        self.console = None
        self.state = SessionState.EXIT

    def read_output(self) -> str:
        return ""

    def send_command(self, command: str) -> SessionState:
        return self.state


class _StubReader:
    async def readline(self) -> bytes:
        return b""


class _RecordingWriter:
    def __init__(self) -> None:
        self.buffer: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.buffer.append(data)

    async def drain(self) -> None:
        await asyncio.sleep(0)


def test_baud_limited_transport_throttles_send() -> None:
    async def _exercise() -> None:
        loopback = LoopbackModemTransport()
        clock = FakeClock()
        transport = BaudLimitedTransport(
            loopback,
            80,
            time_provider=clock.time,
            sleep=clock.sleep,
        )

        transport.open()
        transport.send("x" * 30)
        await asyncio.sleep(0)

        first = loopback.collect_transmit()
        assert first == "x" * 10

        clock.advance(1.0)
        await asyncio.sleep(0)
        second = loopback.collect_transmit()
        assert second == "x" * 10

        clock.advance(1.0)
        await asyncio.sleep(0)
        third = loopback.collect_transmit()
        assert third == "x" * 10

        transport.close()
        await asyncio.sleep(0)

    asyncio.run(_exercise())


def test_telnet_editor_io_uses_crlf_by_default() -> None:
    async def _exercise() -> tuple[str, str]:
        runner = _StubRunner()
        reader = _StubReader()
        writer = _RecordingWriter()

        transport = TelnetModemTransport(
            runner,
            reader,  # type: ignore[arg-type]
            writer,  # type: ignore[arg-type]
        )
        io = _TelnetEditorIO(transport)
        await io.write_line("Hello")
        return (
            b"".join(writer.buffer).decode("latin-1"),
            transport.collect_transmit(),
        )

    transmitted, recorded = asyncio.run(_exercise())
    assert transmitted == "Hello\r\n"
    assert recorded == "Hello\r\n"


def test_telnet_transport_newline_translation_crlf() -> None:
    runner = _StubRunner()
    reader = _StubReader()
    writer = _RecordingWriter()

    telnet = TelnetModemTransport(
        runner,
        reader,  # type: ignore[arg-type]
        writer,  # type: ignore[arg-type]
        newline_translation="\r\n",
    )
    wrapper = BaudLimitedTransport(telnet, baud_limit=None)

    wrapper.send("First line\nSecond line\n")

    payload = b"".join(writer.buffer)
    assert payload == b"First line\r\nSecond line\r\n"
    assert wrapper.collect_transmit() == "First line\r\nSecond line\r\n"
    assert telnet.translate_incoming("Alpha\r\nBeta\r\n") == "Alpha\nBeta\n"


def test_telnet_transport_newline_translation_supports_cr_only() -> None:
    runner = _StubRunner()
    reader = _StubReader()
    writer = _RecordingWriter()

    telnet = TelnetModemTransport(
        runner,
        reader,  # type: ignore[arg-type]
        writer,  # type: ignore[arg-type]
        newline_translation="\r",
    )
    wrapper = BaudLimitedTransport(telnet, baud_limit=None)

    wrapper.send("Alpha\nBeta\n")

    payload = b"".join(writer.buffer)
    assert payload == b"Alpha\rBeta\r"
    assert wrapper.collect_transmit() == "Alpha\rBeta\r"
    assert telnet.translate_incoming("Gamma\rDelta\r") == "Gamma\nDelta\n"


def test_baud_limited_transport_throttles_receive() -> None:
    async def _exercise() -> None:
        loopback = LoopbackModemTransport()
        clock = FakeClock()
        transport = BaudLimitedTransport(
            loopback,
            80,
            time_provider=clock.time,
            sleep=clock.sleep,
        )

        transport.open()
        payload = "abcdefghij" * 3
        transport.feed(payload)

        first = transport.receive()
        assert first == "abcdefghij"
        assert transport.receive() == ""

        clock.advance(1.0)
        second = transport.receive()
        assert second == "abcdefghij"

        clock.advance(1.0)
        third = transport.receive()
        assert third == "abcdefghij"
        assert transport.receive() == ""

        transport.close()
        await asyncio.sleep(0)

    asyncio.run(_exercise())
