# Iteration 43 – Spinner and carrier indicators

## Goals
- [x] Record the ampersand flag indices that drive the spinner and carrier indicator cells.
- [x] Extend the runtime `chkflags` override so it mirrors the spinner and carrier side effects.
- [x] Exercise the new indicator logic through unit tests.

## Findings

### Spinner flag index
- When the left lightbar bitmap exposes bit `$02`, `gotob01c` jumps into `gotob17f`, which animates the spinner by mutating `$049c` across the `$b0`–`$b9` glyph range. This bit therefore corresponds to ampersand flag index `2` on the left-column mask.【F:v1.2/source/ml-1_2-y2k.asm†L2809-L3041】

### Carrier indicator flag index
- The carrier-status routine checks `chk_left & $04` before touching the leading and indicator cells at `$0400` and `$0427`, which ties flag index `4` to the modem indicator pair on the sysop status line.【F:v1.2/source/ml-1_2-y2k.asm†L3055-L3100】

## Updates
- `handle_chkflags` now recognises flag indices `2` and `4`, toggling the spinner glyph and carrier cells in lockstep with the assembly logic while continuing to call the default dispatcher.【F:scripts/prototypes/runtime/ampersand_overrides.py†L22-L121】
- The ampersand override tests now assert that the spinner cell and both carrier cells change when `&,52` is invoked with operations `0`, `1`, and `2`, verifying the Python implementation mirrors the observed C64 side effects.【F:tests/test_ampersand_overrides.py†L1-L79】
