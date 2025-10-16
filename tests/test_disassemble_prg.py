import subprocess
import sys
from pathlib import Path


def test_disassemble_basic_control_flow(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "disassemble_prg.py"

    load_addr = 0xC000
    code = bytes([
        0xA9, 0x01,        # lda #$01
        0x8D, 0x00, 0xD0,  # sta $d000
        0xD0, 0x04,        # bne (forward)
        0xEA,              # nop
        0xEA,              # nop
        0xEA,              # nop
        0xEA,              # nop
        0xA9, 0x02,        # lda #$02 (branch target)
        0x4C, 0x00, 0xC0,  # jmp $c000 (loop)
    ])
    prg_data = bytes([
        load_addr & 0xFF,
        load_addr >> 8,
    ]) + code

    prg_path = tmp_path / "sample.prg"
    asm_path = tmp_path / "sample.asm"
    prg_path.write_bytes(prg_data)

    subprocess.run([sys.executable, str(script), str(prg_path), str(asm_path)], check=True)

    expected = """; Auto-generated disassembly of sample.prg
; Load address: $c000

                * = $c000

loc_c000:
                lda #$01
                sta $d000
                bne loc_c00b
                nop
                nop
                nop
                nop
loc_c00b:
                lda #$02
                jmp loc_c000
"""

    assert asm_path.read_text() == expected
