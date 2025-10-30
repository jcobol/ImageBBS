import pytest

from imagebbs import petscii


def test_translate_petscii_returns_glyph_and_reverse_flag() -> None:
    assert petscii.translate_petscii(0x41) == ("A", False)
    assert petscii.translate_petscii(0xC1) == ("A", True)


@pytest.mark.parametrize(
    "byte, expected",
    [
        (0x41, "A"),
        (0x8D, "\n"),
        (0xC1, "A"),
        (0xFF, "{CBM-$FF}"),
    ],
)
def test_petscii_to_cli_glyph(byte: int, expected: str) -> None:
    assert petscii.petscii_to_cli_glyph(byte) == expected


def test_decode_petscii_stream_basic_line_handling() -> None:
    payload = [ord("A"), 0x0D, ord("B")]
    assert petscii.decode_petscii_stream(payload) == "A\nB"


def test_decode_petscii_stream_wraps_at_width() -> None:
    payload = [ord(char) for char in "ABCDE"]
    assert petscii.decode_petscii_stream(payload, width=4) == "ABCD\nE"


def test_decoder_ignores_unprintable_and_handles_backspace() -> None:
    decoder = petscii.PetsciiStreamDecoder()
    payload = [0x01, ord("A"), ord("B"), 0x14, ord("C")]
    assert decoder.decode(payload) == "AB\rA \rAC"


def test_decoder_feed_is_incremental() -> None:
    decoder = petscii.PetsciiStreamDecoder()
    first = decoder.feed([ord("A"), 0x0D])
    second = decoder.feed([ord("B"), ord("C")])

    assert first == "A\n"
    assert second == "BC"


def test_decoder_feed_wraps_and_handles_reverse_toggle() -> None:
    decoder = petscii.PetsciiStreamDecoder(width=4)

    assert decoder.feed([0x12, ord("A"), ord("B")]) == "AB"
    assert decoder.feed([ord("C"), 0x92, ord("D")]) == "CD\n"


def test_decoder_reset_restores_state() -> None:
    decoder = petscii.PetsciiStreamDecoder(width=3)

    decoder.feed([ord("X"), ord("Y"), ord("Z")])
    decoder.reset()

    assert decoder.feed([ord("A")]) == "A"

