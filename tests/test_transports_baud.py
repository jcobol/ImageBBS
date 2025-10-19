import asyncio
from pathlib import Path
from typing import List, Tuple

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prototypes.device_context import LoopbackModemTransport  # noqa: E402
from scripts.prototypes.runtime.transports import BaudLimitedTransport  # noqa: E402


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
