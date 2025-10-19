# File-transfer macro asset inventory

## Overlay dumps and listings
- `v1.2/from-floppy/ml.extra` captures the recovered `ml.extra` overlay pulled directly from the ImageBBS 1.2B distribution disks, and `v1.2/from-floppy/ml.extra.txt` retains the PETCAT text listing generated from the same PRG for inspection alongside the BASIC overlays.【F:v1.2/from-floppy/README.md†L1-L35】
- The `im` BASIC listing at `v1.2/core/im.txt` invokes ampersand macros `&,28`, `&,29`, and `&,2A` while driving the file-transfer menu, matching the slot constants consumed by the modern runtime shim.【F:v1.2/core/im.txt†L1681-L1862】【F:scripts/prototypes/runtime/file_transfers.py†L38-L151】

## Disk image sources
- Iteration 10 documents that the missing overlays—including `ml.extra`—were recovered from standard 174,848-byte D64 boot-disk dumps; the repository tooling uses those disk images as the authoritative source when regenerating the PRG snapshots.【F:docs/porting/iteration-10.md†L1-L17】

## Glyph and colour payload snapshots
- `docs/porting/artifacts/ml-extra-overlay-metadata.json` lists macro slots `40`, `41`, and `42`, confirming that the recovered overlay exposes payloads for the `$28`–`$2A` menu entries required by `FileTransfersModule`.【F:docs/porting/artifacts/ml-extra-overlay-metadata.json†L183-L199】【F:scripts/prototypes/runtime/file_transfers.py†L38-L151】
- `docs/porting/artifacts/ml-extra-macro-screens.json` stores the rendered PETSCII glyph matrices and colour maps for each recovered macro slot; the entries for slots `40`, `41`, and `42` hold the header, prompt, and invalid-selection panes that the runtime stages before issuing `&,50`.【F:docs/porting/artifacts/ml-extra-macro-screens.json†L1-L1】【F:scripts/prototypes/runtime/file_transfers.py†L38-L151】
