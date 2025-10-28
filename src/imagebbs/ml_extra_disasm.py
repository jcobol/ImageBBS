"""Disassemble the ``ml.extra`` macro handlers for inspection."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Sequence, Tuple

from . import ml_extra_defaults
from . import ml_extra_reporting

__all__ = [
    "Instruction",
    "disassemble_bytes",
    "format_instructions",
    "disassemble_macro",
    "parse_args",
    "main",
]

OP_INFO: Dict[int, Tuple[str, str]] = {
    0x00: ("brk", "imp"),
    0x01: ("ora", "indx"),
    0x05: ("ora", "zp"),
    0x06: ("asl", "zp"),
    0x08: ("php", "imp"),
    0x09: ("ora", "imm"),
    0x0A: ("asl", "acc"),
    0x0D: ("ora", "abs"),
    0x0E: ("asl", "abs"),
    0x10: ("bpl", "rel"),
    0x11: ("ora", "indy"),
    0x15: ("ora", "zpx"),
    0x16: ("asl", "zpx"),
    0x18: ("clc", "imp"),
    0x19: ("ora", "absy"),
    0x1D: ("ora", "absx"),
    0x1E: ("asl", "absx"),
    0x20: ("jsr", "abs"),
    0x21: ("and", "indx"),
    0x24: ("bit", "zp"),
    0x25: ("and", "zp"),
    0x26: ("rol", "zp"),
    0x28: ("plp", "imp"),
    0x29: ("and", "imm"),
    0x2A: ("rol", "acc"),
    0x2C: ("bit", "abs"),
    0x2D: ("and", "abs"),
    0x2E: ("rol", "abs"),
    0x30: ("bmi", "rel"),
    0x31: ("and", "indy"),
    0x35: ("and", "zpx"),
    0x36: ("rol", "zpx"),
    0x38: ("sec", "imp"),
    0x39: ("and", "absy"),
    0x3D: ("and", "absx"),
    0x3E: ("rol", "absx"),
    0x40: ("rti", "imp"),
    0x41: ("eor", "indx"),
    0x45: ("eor", "zp"),
    0x46: ("lsr", "zp"),
    0x48: ("pha", "imp"),
    0x49: ("eor", "imm"),
    0x4A: ("lsr", "acc"),
    0x4C: ("jmp", "abs"),
    0x4D: ("eor", "abs"),
    0x4E: ("lsr", "abs"),
    0x50: ("bvc", "rel"),
    0x51: ("eor", "indy"),
    0x55: ("eor", "zpx"),
    0x56: ("lsr", "zpx"),
    0x58: ("cli", "imp"),
    0x59: ("eor", "absy"),
    0x5D: ("eor", "absx"),
    0x5E: ("lsr", "absx"),
    0x60: ("rts", "imp"),
    0x61: ("adc", "indx"),
    0x65: ("adc", "zp"),
    0x66: ("ror", "zp"),
    0x68: ("pla", "imp"),
    0x69: ("adc", "imm"),
    0x6A: ("ror", "acc"),
    0x6C: ("jmp", "ind"),
    0x6D: ("adc", "abs"),
    0x6E: ("ror", "abs"),
    0x70: ("bvs", "rel"),
    0x71: ("adc", "indy"),
    0x75: ("adc", "zpx"),
    0x76: ("ror", "zpx"),
    0x78: ("sei", "imp"),
    0x79: ("adc", "absy"),
    0x7D: ("adc", "absx"),
    0x7E: ("ror", "absx"),
    0x81: ("sta", "indx"),
    0x84: ("sty", "zp"),
    0x85: ("sta", "zp"),
    0x86: ("stx", "zp"),
    0x88: ("dey", "imp"),
    0x8A: ("txa", "imp"),
    0x8C: ("sty", "abs"),
    0x8D: ("sta", "abs"),
    0x8E: ("stx", "abs"),
    0x90: ("bcc", "rel"),
    0x91: ("sta", "indy"),
    0x94: ("sty", "zpx"),
    0x95: ("sta", "zpx"),
    0x96: ("stx", "zpy"),
    0x98: ("tya", "imp"),
    0x99: ("sta", "absy"),
    0x9A: ("txs", "imp"),
    0x9D: ("sta", "absx"),
    0xA0: ("ldy", "imm"),
    0xA1: ("lda", "indx"),
    0xA2: ("ldx", "imm"),
    0xA4: ("ldy", "zp"),
    0xA5: ("lda", "zp"),
    0xA6: ("ldx", "zp"),
    0xA8: ("tay", "imp"),
    0xA9: ("lda", "imm"),
    0xAA: ("tax", "imp"),
    0xAC: ("ldy", "abs"),
    0xAD: ("lda", "abs"),
    0xAE: ("ldx", "abs"),
    0xB0: ("bcs", "rel"),
    0xB1: ("lda", "indy"),
    0xB4: ("ldy", "zpx"),
    0xB5: ("lda", "zpx"),
    0xB6: ("ldx", "zpy"),
    0xB8: ("clv", "imp"),
    0xB9: ("lda", "absy"),
    0xBA: ("tsx", "imp"),
    0xBC: ("ldy", "absx"),
    0xBD: ("lda", "absx"),
    0xBE: ("ldx", "absy"),
    0xC0: ("cpy", "imm"),
    0xC1: ("cmp", "indx"),
    0xC4: ("cpy", "zp"),
    0xC5: ("cmp", "zp"),
    0xC6: ("dec", "zp"),
    0xC8: ("iny", "imp"),
    0xC9: ("cmp", "imm"),
    0xCA: ("dex", "imp"),
    0xCC: ("cpy", "abs"),
    0xCD: ("cmp", "abs"),
    0xCE: ("dec", "abs"),
    0xD0: ("bne", "rel"),
    0xD1: ("cmp", "indy"),
    0xD5: ("cmp", "zpx"),
    0xD6: ("dec", "zpx"),
    0xD8: ("cld", "imp"),
    0xD9: ("cmp", "absy"),
    0xDD: ("cmp", "absx"),
    0xDE: ("dec", "absx"),
    0xE0: ("cpx", "imm"),
    0xE1: ("sbc", "indx"),
    0xE4: ("cpx", "zp"),
    0xE5: ("sbc", "zp"),
    0xE6: ("inc", "zp"),
    0xE8: ("inx", "imp"),
    0xE9: ("sbc", "imm"),
    0xEA: ("nop", "imp"),
    0xEC: ("cpx", "abs"),
    0xED: ("sbc", "abs"),
    0xEE: ("inc", "abs"),
    0xF0: ("beq", "rel"),
    0xF1: ("sbc", "indy"),
    0xF5: ("sbc", "zpx"),
    0xF6: ("inc", "zpx"),
    0xF8: ("sed", "imp"),
    0xF9: ("sbc", "absy"),
    0xFD: ("sbc", "absx"),
    0xFE: ("inc", "absx"),
}

MODE_SIZES: Dict[str, int] = {
    "imp": 1,
    "acc": 1,
    "imm": 2,
    "zp": 2,
    "zpx": 2,
    "zpy": 2,
    "indx": 2,
    "indy": 2,
    "abs": 3,
    "absx": 3,
    "absy": 3,
    "ind": 3,
    "rel": 2,
}


@dataclass(frozen=True)
class Instruction:
    """Single 6502 instruction recovered from a macro payload."""

    address: int
    bytes: Tuple[int, ...]
    opcode: int
    mnemonic: str | None
    mode: str
    target: int | None = None

    def byte_repr(self) -> str:
        return " ".join(f"{value:02x}" for value in self.bytes)


def _payload_sha256(payload: Sequence[int]) -> str:
    """Return the SHA-256 digest for ``payload``."""

    return hashlib.sha256(bytes(payload)).hexdigest()


def disassemble_bytes(payload: Sequence[int], start_address: int) -> List[Instruction]:
    """Return a best-effort disassembly for ``payload`` starting at ``start_address``."""

    instructions: List[Instruction] = []
    index = 0
    address = start_address
    length = len(payload)

    while index < length:
        opcode = payload[index]
        info = OP_INFO.get(opcode)
        if info is None:
            instructions.append(
                Instruction(
                    address=address,
                    bytes=(opcode,),
                    opcode=opcode,
                    mnemonic=None,
                    mode="byte",
                )
            )
            index += 1
            address += 1
            continue

        mnemonic, mode = info
        size = MODE_SIZES[mode]
        if index + size > length:
            instructions.append(
                Instruction(
                    address=address,
                    bytes=(opcode,),
                    opcode=opcode,
                    mnemonic=None,
                    mode="byte",
                )
            )
            index += 1
            address += 1
            continue

        chunk = tuple(payload[index : index + size])
        instructions.append(
            Instruction(
                address=address,
                bytes=chunk,
                opcode=opcode,
                mnemonic=mnemonic,
                mode=mode,
            )
        )
        index += size
        address += size

    end_address = start_address + length
    for entry in instructions:
        if entry.mnemonic is None:
            continue
        mode = entry.mode
        if mode == "rel":
            offset = entry.bytes[1]
            if offset >= 0x80:
                offset -= 0x100
            target = (entry.address + len(entry.bytes) + offset) & 0xFFFF
            object.__setattr__(entry, "target", target)
        elif mode in {"abs", "absx", "absy", "ind"}:
            operand = entry.bytes[1] | (entry.bytes[2] << 8)
            object.__setattr__(entry, "target", operand)

    label_targets = {
        entry.target
        for entry in instructions
        if entry.target is not None
        and start_address <= entry.target < end_address
    }
    label_names = {addr: f"loc_{addr:04x}" for addr in sorted(label_targets)}

    for entry in instructions:
        if entry.mnemonic is None:
            continue
        mode = entry.mode
        if mode == "rel":
            target = entry.target
            if target in label_names:
                object.__setattr__(entry, "operand_repr", label_names[target])
            else:
                object.__setattr__(entry, "operand_repr", f"${target:04x}")
        elif mode == "acc":
            object.__setattr__(entry, "operand_repr", "a")
        elif mode == "imm":
            object.__setattr__(entry, "operand_repr", f"#${entry.bytes[1]:02x}")
        elif mode == "zp":
            object.__setattr__(entry, "operand_repr", f"${entry.bytes[1]:02x}")
        elif mode == "zpx":
            object.__setattr__(entry, "operand_repr", f"${entry.bytes[1]:02x},x")
        elif mode == "zpy":
            object.__setattr__(entry, "operand_repr", f"${entry.bytes[1]:02x},y")
        elif mode == "indx":
            object.__setattr__(entry, "operand_repr", f"(${entry.bytes[1]:02x},x)")
        elif mode == "indy":
            object.__setattr__(entry, "operand_repr", f"(${entry.bytes[1]:02x}),y")
        elif mode in {"abs", "absx", "absy", "ind"}:
            target = entry.target or 0
            suffix = ""
            if mode == "absx":
                suffix = ",x"
            elif mode == "absy":
                suffix = ",y"
            if mode == "ind":
                operand_repr = f"({target:04x})"
            else:
                operand_repr = f"${target:04x}{suffix}"
            if target in label_names:
                name = label_names[target]
                if mode == "ind":
                    operand_repr = f"({name})"
                else:
                    operand_repr = f"{name}{suffix}"
            object.__setattr__(entry, "operand_repr", operand_repr)
        elif mode == "imp":
            object.__setattr__(entry, "operand_repr", "")
        else:  # pragma: no cover - defensive fallback
            object.__setattr__(entry, "operand_repr", "")

        label = label_names.get(entry.address)
        if label is not None:
            object.__setattr__(entry, "label", label)

    return instructions


def format_instructions(instructions: Sequence[Instruction]) -> Iterator[str]:
    """Yield formatted assembly lines for ``instructions``."""

    for entry in instructions:
        label = getattr(entry, "label", None)
        if label:
            yield f"{label}:"
        byte_repr = entry.byte_repr()
        if entry.mnemonic is None:
            yield f"${entry.address:04x}:  {byte_repr:<11} .byte ${entry.opcode:02x}"
            continue
        operand = getattr(entry, "operand_repr", "")
        if operand:
            text = f"{entry.mnemonic} {operand}"
        else:
            text = entry.mnemonic
        yield f"${entry.address:04x}:  {byte_repr:<11} {text}"


def disassemble_macro(entry: ml_extra_defaults.MacroDirectoryEntry) -> List[str]:
    """Return formatted disassembly lines for ``entry``."""

    instructions = disassemble_bytes(entry.payload, entry.address)
    return list(format_instructions(instructions))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay", type=Path, help="Override path to ml.extra overlay")
    parser.add_argument(
        "--slot",
        type=int,
        action="append",
        help="Macro slot to disassemble (defaults to all)",
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="Print lightbar/palette/hardware metadata before the disassembly",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    defaults = ml_extra_defaults.MLExtraDefaults.from_overlay(args.overlay)
    entries_by_slot = {entry.slot: entry for entry in defaults.macros}

    slots = args.slot or sorted(entries_by_slot)
    missing = [slot for slot in slots if slot not in entries_by_slot]
    if missing:
        missing_text = ", ".join(str(slot) for slot in missing)
        raise SystemExit(f"unknown macro slot(s): {missing_text}")

    if args.metadata:
        metadata = ml_extra_reporting.collect_overlay_metadata(defaults)
        for line in ml_extra_reporting.format_overlay_metadata(metadata):
            print(line)
        print()
        print("Macro payload hashes:")
        for slot in slots:
            entry = entries_by_slot[slot]
            print(f"  slot {slot}: {_payload_sha256(entry.payload)}")
        print()

    for slot in slots:
        entry = entries_by_slot[slot]
        print(f"Macro slot {slot} @ ${entry.address:04x} ({len(entry.payload)} bytes)")
        for line in disassemble_macro(entry):
            print(f"  {line}")
        print()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
