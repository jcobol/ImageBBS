"""Protocol drivers that approximate ImageBBS modem file transfers."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from ..device_context import ModemTransport


ProgressCallback = Callable[[int, Optional[int]], None]
AbortChecker = Callable[[], bool]


class FileTransferError(RuntimeError):
    """Raised when a protocol-level failure interrupts a transfer."""


class FileTransferAborted(FileTransferError):
    """Raised when the caller cancels an active transfer."""


# Why: preserve binary payloads when writing to ModemTransport's str interface.
def _bytes_to_text(payload: bytes) -> str:
    return payload.decode("latin-1")


# Why: recover binary payloads emitted by ModemTransport.receive.
def _text_to_bytes(payload: str) -> bytes:
    return payload.encode("latin-1")


# Why: compute CRC values used by ImageBBS's Xmodem CRC implementation.
def _crc16_ccitt(payload: bytes) -> int:
    crc = 0
    for byte in payload:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF


# Why: guarantee that protocol handlers read an exact payload length or fail loudly.
def _read_exact(transport: ModemTransport, size: int) -> bytes:
    buffer = bytearray()
    while len(buffer) < size:
        chunk = transport.receive(size - len(buffer))
        if not chunk:
            raise FileTransferError("remote peer closed stream during transfer")
        buffer.extend(_text_to_bytes(chunk))
    return bytes(buffer)


class FileTransferProtocolDriver:
    """Base class for drivers that stream payloads over a modem transport."""

    # Why: allow subclasses to initialise frame sizing without exposing kwargs everywhere.
    def __init__(self, *, block_size: int) -> None:
        self.block_size = block_size
        self.name = ""

    # Why: standardise upload semantics so menu modules can stream files without bespoke logic.
    def upload(
        self,
        transport: ModemTransport,
        payload: bytes,
        *,
        progress_callback: ProgressCallback | None = None,
        abort_checker: AbortChecker | None = None,
    ) -> None:
        raise NotImplementedError

    # Why: standardise download semantics while reporting status to the surrounding UI.
    def download(
        self,
        transport: ModemTransport,
        *,
        progress_callback: ProgressCallback | None = None,
        abort_checker: AbortChecker | None = None,
    ) -> bytes:
        raise NotImplementedError

    # Why: share guard logic so subclasses cancel cleanly when the caller raises the abort flag.
    def _check_abort(self, abort_checker: AbortChecker | None) -> None:
        if abort_checker is not None and abort_checker():
            raise FileTransferAborted("caller requested abort")


class XmodemProtocolDriver(FileTransferProtocolDriver):
    """Implements ImageBBS's Xmodem CRC and Xmodem 1K transport logic."""

    SOH = 0x01
    STX = 0x02
    EOT = 0x04
    ACK = 0x06
    NAK = 0x15
    CAN = 0x18

    # Why: configure block sizing to match CRC (128-byte) or 1K variants.
    def __init__(self, *, block_size: int = 128) -> None:
        super().__init__(block_size=block_size)
        self._frame_lead = self.STX if block_size > 128 else self.SOH

    # Why: mirror the BASIC uploader by chunking payloads and acknowledging receiver prompts.
    def upload(
        self,
        transport: ModemTransport,
        payload: bytes,
        *,
        progress_callback: ProgressCallback | None = None,
        abort_checker: AbortChecker | None = None,
    ) -> None:
        self._check_abort(abort_checker)
        start_prompt = transport.receive(1)
        if not start_prompt:
            raise FileTransferError("receiver failed to issue start prompt")
        prompt = start_prompt[0]
        if prompt not in ("C", chr(self.NAK)):
            raise FileTransferError(f"unexpected Xmodem start prompt {start_prompt!r}")

        total = len(payload)
        sent = 0
        block_size = self.block_size
        frame_lead = self._frame_lead
        block_number = 1
        while sent < total or (total == 0 and block_number == 1):
            self._check_abort(abort_checker)
            block = payload[sent : sent + block_size]
            sent += len(block)
            if len(block) < block_size:
                block += bytes((0x1A,)) * (block_size - len(block))
            header = bytes((frame_lead, block_number & 0xFF, (~block_number) & 0xFF))
            crc = _crc16_ccitt(block)
            frame = header + block + bytes(((crc >> 8) & 0xFF, crc & 0xFF))
            transport.send(_bytes_to_text(frame))
            ack = _read_exact(transport, 1)[0]
            if ack == self.CAN:
                raise FileTransferError("receiver cancelled transfer")
            if ack not in (self.ACK, self.NAK):
                raise FileTransferError(f"receiver returned {ack:#x} instead of ACK/NAK")
            if progress_callback is not None:
                progress_callback(min(sent, total), total)
            if ack == self.NAK:
                sent -= len(block)
                continue
            block_number = (block_number + 1) % 256
            if block_number == 0:
                block_number = 1

        transport.send(chr(self.EOT))
        final_ack = _read_exact(transport, 1)[0]
        if final_ack != self.ACK:
            raise FileTransferError(f"receiver rejected final EOT with {final_ack:#x}")
        if progress_callback is not None:
            progress_callback(total, total)

    # Why: consume Xmodem frames and expose the decoded payload to the caller.
    def download(
        self,
        transport: ModemTransport,
        *,
        progress_callback: ProgressCallback | None = None,
        abort_checker: AbortChecker | None = None,
    ) -> bytes:
        self._check_abort(abort_checker)
        transport.send("C")
        buffer = bytearray()
        block_size = self.block_size
        expected_number = 1
        while True:
            self._check_abort(abort_checker)
            lead = _read_exact(transport, 1)[0]
            if lead == self.EOT:
                transport.send(chr(self.ACK))
                break
            if lead not in (self.SOH, self.STX):
                raise FileTransferError(f"unexpected Xmodem lead byte {lead:#x}")
            actual_block_size = 1024 if lead == self.STX else 128
            header = _read_exact(transport, 2)
            block_number, complement = header[0], header[1]
            if block_number != ((~complement) & 0xFF):
                raise FileTransferError("Xmodem block number complement mismatch")
            if block_number != expected_number:
                raise FileTransferError("unexpected Xmodem block order")
            block = _read_exact(transport, actual_block_size)
            crc_bytes = _read_exact(transport, 2)
            crc = (crc_bytes[0] << 8) | crc_bytes[1]
            if _crc16_ccitt(block) != crc:
                transport.send(chr(self.NAK))
                continue
            transport.send(chr(self.ACK))
            if lead == self.SOH and block_size > 128:
                block = block + bytes((0x1A,)) * (block_size - 128)
            if lead == self.STX and block_size <= 128:
                block = block[: block_size]
            buffer.extend(block)
            if progress_callback is not None:
                progress_callback(len(buffer), None)
            expected_number = (expected_number + 1) % 256
            if expected_number == 0:
                expected_number = 1
        result = bytes(buffer).rstrip(b"\x1A")
        if progress_callback is not None:
            progress_callback(len(result), len(result))
        return result


class PunterProtocolDriver(FileTransferProtocolDriver):
    """Implements the ImageBBS Punter and Punter-C style framing rules."""

    START = b"S"
    FRAME = b"!"
    END = b"E"
    ACK = b"K"

    # Why: capture variant frame sizing (classic Punter vs. Punter-C/Multi-Punter).
    def __init__(self, *, block_size: int = 256, name: str = "Punter") -> None:
        super().__init__(block_size=block_size)
        self.name = name

    # Why: emit Punter blocks with checksums so receivers can validate each frame.
    def upload(
        self,
        transport: ModemTransport,
        payload: bytes,
        *,
        progress_callback: ProgressCallback | None = None,
        abort_checker: AbortChecker | None = None,
    ) -> None:
        self._check_abort(abort_checker)
        start = _read_exact(transport, 1)
        if start not in (self.START, self.START.lower()):
            raise FileTransferError("receiver did not enter Punter send mode")
        total = len(payload)
        sent = 0
        block_size = self.block_size
        while sent < total or (total == 0 and sent == 0):
            self._check_abort(abort_checker)
            block = payload[sent : sent + block_size]
            sent += len(block)
            header = bytes((len(block) >> 8, len(block) & 0xFF))
            checksum = sum(block) & 0xFF
            frame = self.FRAME + header + block + bytes((checksum,))
            transport.send(_bytes_to_text(frame))
            ack = _read_exact(transport, 1)
            if ack != self.ACK:
                raise FileTransferError("receiver rejected Punter frame")
            if progress_callback is not None:
                progress_callback(min(sent, total), total)
        transport.send(_bytes_to_text(self.END))
        if progress_callback is not None:
            progress_callback(total, total)

    # Why: parse framed blocks emitted by a Punter sender and expose assembled bytes.
    def download(
        self,
        transport: ModemTransport,
        *,
        progress_callback: ProgressCallback | None = None,
        abort_checker: AbortChecker | None = None,
    ) -> bytes:
        self._check_abort(abort_checker)
        transport.send(_bytes_to_text(self.START))
        data = bytearray()
        while True:
            self._check_abort(abort_checker)
            marker = _read_exact(transport, 1)
            if marker == self.END:
                break
            if marker != self.FRAME:
                raise FileTransferError("unexpected Punter frame marker")
            header = _read_exact(transport, 2)
            length = (header[0] << 8) | header[1]
            block = _read_exact(transport, length)
            checksum = _read_exact(transport, 1)[0]
            if (sum(block) & 0xFF) != checksum:
                transport.send(_bytes_to_text(b"?"))
                raise FileTransferError("punter checksum mismatch")
            data.extend(block)
            transport.send(_bytes_to_text(self.ACK))
            if progress_callback is not None:
                progress_callback(len(data), None)
        if progress_callback is not None:
            progress_callback(len(data), len(data))
        return bytes(data)


# Why: map human-readable protocol names to driver factories.
_DRIVER_FACTORIES: Dict[str, Callable[[], FileTransferProtocolDriver]] = {
    "punter": lambda: PunterProtocolDriver(block_size=256, name="Punter"),
    "punterc": lambda: PunterProtocolDriver(block_size=512, name="Punter-C"),
    "multipunter": lambda: PunterProtocolDriver(block_size=1024, name="Multi-Punter"),
    "xmodem": lambda: XmodemProtocolDriver(block_size=128),
    "xmodemcrc": lambda: XmodemProtocolDriver(block_size=128),
    "xmodem1k": lambda: XmodemProtocolDriver(block_size=1024),
    "xmodem-1k": lambda: XmodemProtocolDriver(block_size=1024),
}


# Why: ensure lookups tolerate the naming permutations used in ImageBBS menus.
def normalise_protocol_name(name: str) -> str:
    cleaned = "".join(ch.lower() for ch in name if ch.isalnum())
    return cleaned


# Why: expose a factory so runtime modules can instantiate drivers on demand.
def build_protocol_driver(name: str) -> FileTransferProtocolDriver:
    normalised = normalise_protocol_name(name)
    if normalised not in _DRIVER_FACTORIES:
        raise ValueError(f"unsupported file transfer protocol: {name}")
    driver = _DRIVER_FACTORIES[normalised]()
    driver.name = name
    return driver


__all__ = [
    "AbortChecker",
    "FileTransferAborted",
    "FileTransferError",
    "FileTransferProtocolDriver",
    "ProgressCallback",
    "PunterProtocolDriver",
    "XmodemProtocolDriver",
    "build_protocol_driver",
    "normalise_protocol_name",
]
