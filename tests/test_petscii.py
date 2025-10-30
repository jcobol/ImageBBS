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


def test_decoder_feed_returns_incremental_output() -> None:
    decoder = petscii.PetsciiStreamDecoder()

    assert decoder.feed([ord("H"), ord("i")]) == "Hi"
    assert decoder.feed([0x0D, ord("!")]) == "\n!"
    assert decoder.feed([]) == ""


def test_decoder_feed_handles_control_bytes_across_calls() -> None:
    decoder = petscii.PetsciiStreamDecoder()

    assert decoder.feed([0x01, ord("A")]) == "A"
    assert decoder.feed([ord("B")]) == "B"
    assert decoder.feed([0x14, ord("C")]) == "\rA \rAC"


def test_decoder_feed_wraps_output_at_configured_width() -> None:
    decoder = petscii.PetsciiStreamDecoder(width=4)

    assert decoder.feed([ord(char) for char in "ABC"]) == "ABC"
    assert decoder.feed([ord("D"), ord("E")]) == "D\nE"


def test_decoder_feed_handles_reverse_mode_toggles() -> None:
    decoder = petscii.PetsciiStreamDecoder()

    assert decoder.feed([0x12]) == ""
    assert decoder.feed([ord("a")]) == "a"
    assert decoder.feed([0x92, ord("b")]) == "b"


def test_decoder_reset_restores_initial_state() -> None:
    decoder = petscii.PetsciiStreamDecoder(width=3)

    assert decoder.feed([ord("A"), ord("B"), ord("C")]) == "ABC\n"
    decoder.reset()
    assert decoder.feed([ord("X"), 0x0D, ord("Y")]) == "X\nY"

