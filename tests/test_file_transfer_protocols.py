from imagebbs.device_context import LoopbackModemTransport
from imagebbs.runtime.file_transfer_protocols import (
    PunterProtocolDriver,
    XmodemProtocolDriver,
)


# Why: mirror the runtime CRC routine for validating Xmodem frames.
def _crc16(payload: bytes) -> int:
    crc = 0
    for byte in payload:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF

# Why: ensure Xmodem upload framing matches the CRC/1K specification.
def test_xmodem_upload_sends_expected_frames() -> None:
    transport = LoopbackModemTransport()
    transport.open()
    driver = XmodemProtocolDriver()
    payload = b"hello"
    progress = []
    transport.feed("C" + chr(0x06) + chr(0x06))

    driver.upload(
        transport,
        payload,
        progress_callback=lambda transferred, total: progress.append((transferred, total)),
    )

    sent = transport.collect_transmit().encode("latin-1")
    padded = payload + bytes((0x1A,)) * (128 - len(payload))
    crc = _crc16(padded)
    expected_frame = (
        bytes((0x01, 0x01, 0xFE))
        + padded
        + bytes(((crc >> 8) & 0xFF, crc & 0xFF))
    )
    assert sent == expected_frame + b"\x04"
    assert progress[-1] == (len(payload), len(payload))

# Why: verify Xmodem download sequences decode payloads correctly.
def test_xmodem_download_receives_payload() -> None:
    transport = LoopbackModemTransport()
    transport.open()
    driver = XmodemProtocolDriver()
    payload = b"greetings"
    padded = payload + bytes((0x1A,)) * (128 - len(payload))
    crc = _crc16(padded)
    frame = (
        bytes((0x01, 0x01, 0xFE))
        + padded
        + bytes(((crc >> 8) & 0xFF, crc & 0xFF))
    )
    transport.feed((frame + b"\x04").decode("latin-1"))

    received = driver.download(transport)

    transmissions = transport.collect_transmit()
    assert transmissions == "C" + chr(0x06) + chr(0x06)
    assert received == payload

# Why: confirm Punter variants stream data bidirectionally with checksums.
def test_punter_upload_and_download_round_trip() -> None:
    transport = LoopbackModemTransport()
    transport.open()
    driver = PunterProtocolDriver()
    payload = b"ABC"
    checksum = sum(payload) & 0xFF
    frame = b"!" + bytes((0x00, len(payload))) + payload + bytes((checksum,))

    transport.feed("S" + "K")
    driver.upload(transport, payload)
    sent = transport.collect_transmit().encode("latin-1")
    assert sent == frame + b"E"

    # Now simulate the remote sender for download.
    transport.feed((frame + b"E").decode("latin-1"))
    received = driver.download(transport)
    transmissions = transport.collect_transmit()
    assert transmissions == "S" + "K"
    assert received == payload
