import sys
from pathlib import Path

OP_INFO = {
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

MODE_SIZES = {
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

if len(sys.argv) != 3:
    print("Usage: disassemble_prg.py <input_prg> <output_asm>")
    sys.exit(1)

inp = Path(sys.argv[1])
outp = Path(sys.argv[2])

data = inp.read_bytes()
if len(data) < 2:
    raise SystemExit("PRG file too short")
load_addr = data[0] | (data[1] << 8)
code = data[2:]
size = len(code)
end_addr = load_addr + size

entries = []
addr = load_addr
idx = 0
while idx < size:
    opcode = code[idx]
    if opcode in OP_INFO:
        mnemonic, mode = OP_INFO[opcode]
        length = MODE_SIZES[mode]
        operand = code[idx+1:idx+length]
        entries.append({
            "addr": addr,
            "opcode": opcode,
            "mnemonic": mnemonic,
            "mode": mode,
            "bytes": code[idx:idx+length],
        })
        idx += length
        addr += length
    else:
        entries.append({
            "addr": addr,
            "opcode": opcode,
            "mnemonic": None,
            "mode": "byte",
            "bytes": bytes([opcode]),
        })
        idx += 1
        addr += 1

label_targets = set()
for entry in entries:
    if entry["mnemonic"] is None:
        continue
    mode = entry["mode"]
    addr = entry["addr"]
    if mode == "rel":
        offset = entry["bytes"][1]
        if offset >= 0x80:
            offset -= 0x100
        target = (addr + len(entry["bytes"]) + offset) & 0xFFFF
        entry["target"] = target
        if load_addr <= target < end_addr:
            label_targets.add(target)
    elif mode in {"abs", "absx", "absy", "ind"}:
        operand = entry["bytes"][1] | (entry["bytes"][2] << 8)
        entry["target"] = operand
        if entry["mnemonic"] in {"jsr", "jmp"} and load_addr <= operand < end_addr:
            label_targets.add(operand)

label_names = {addr: f"loc_{addr:04x}" for addr in sorted(label_targets)}

def format_operand(entry):
    mode = entry["mode"]
    b = entry["bytes"]
    if mode == "imp":
        return ""
    if mode == "acc":
        return "a"
    if mode == "imm":
        return f"#$%02x" % b[1]
    if mode == "zp":
        return f"$%02x" % b[1]
    if mode == "zpx":
        return f"$%02x,x" % b[1]
    if mode == "zpy":
        return f"$%02x,y" % b[1]
    if mode == "indx":
        return f"($%02x,x)" % b[1]
    if mode == "indy":
        return f"($%02x),y" % b[1]
    if mode == "abs":
        target = entry.get("target")
        if target in label_names:
            return label_names[target]
        return f"$%04x" % target
    if mode == "absx":
        target = entry.get("target")
        if target in label_names:
            return f"{label_names[target]},x"
        return f"$%04x,x" % target
    if mode == "absy":
        target = entry.get("target")
        if target in label_names:
            return f"{label_names[target]},y"
        return f"$%04x,y" % target
    if mode == "ind":
        target = entry.get("target")
        if target in label_names:
            return f"({label_names[target]})"
        return f"($%04x)" % target
    if mode == "rel":
        target = entry.get("target")
        if target in label_names:
            return label_names[target]
        return f"$%04x" % target
    raise ValueError(f"Unhandled mode: {mode}")

lines = []
lines.append("; Auto-generated disassembly of %s" % inp.name)
lines.append(f"; Load address: ${load_addr:04x}")
lines.append("")
lines.append(f"                * = ${load_addr:04x}")
lines.append("")
for entry in entries:
    addr = entry["addr"]
    label = label_names.get(addr)
    if label:
        lines.append(f"{label}:")
    if entry["mnemonic"] is None:
        lines.append(f"                .byte ${entry['opcode']:02x}")
        continue
    operand = format_operand(entry)
    if operand:
        lines.append(f"                {entry['mnemonic']} {operand}")
    else:
        lines.append(f"                {entry['mnemonic']}")

outp.write_text("\n".join(lines) + "\n")
