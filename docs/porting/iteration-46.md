# Iteration 46 – Slot `$29` prompt decode

## Goals
- [x] Re-run the macro dump tooling for slot `$29` to confirm the payload length, address, and checksum.
- [x] Capture the rendered glyph and colour buffers for the prompt macro so staging code can mirror the exact PETSCII/colour pairing.

## Findings

### Macro payload metadata
- `python -m scripts.prototypes.ml_extra_dump_macros --slot "$29"` surfaces the 22-byte prompt payload at `$0000`, decoded text `"COMMAND (Q TO EXIT):"`, and SHA-256 digest `ff429b988d00e0cadc5fadedb482816f4cee1805686aae0669a6e8a7630c8621`, matching the historical runtime behaviour.【a2397c†L1-L1】

### Glyph and colour capture
- The `ml-extra-macro-screens.json.gz.base64` snapshot records slot `41` (hex `$29`) with the prompt rendered on row 0: glyph bytes `C3 CF CD CD C1 CE C4 20 28 D1 20 D4 CF 20 C5 D8 C9 D4 29 3A 20 00` followed by PETSCII space padding, and colour bytes `0A` across the visible text with the `$00` null terminator retaining colour `$00` before the remaining `$20`/`$0A` padding completes the 40-column row.【F:docs/porting/artifacts/ml-extra-macro-screens.json.gz.base64†L1-L1】【923fe1†L1-L3】

## Next steps
- Thread the prompt payload into the masked-pane staging helper before `FileTransfersModule` invokes `&,50` so the host overlay mirrors the C64 colour scheme exactly.【F:scripts/prototypes/runtime/file_transfers.py†L103-L169】
