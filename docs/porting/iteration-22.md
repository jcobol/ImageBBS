# Iteration 22 – Inventorying the recovered `ml.extra`

## Goals
- Verify the binary and PETSCII listings staged for the authentic `ml.extra` overlay so upcoming disassembly work references the right artefacts.
- Revisit the prior recovery notes to understand expectations carried over from the stub and flag any assumptions that still need confirmation.
- Catalogue every placeholder inside `ml_extra_stub.asm` that will need replacement once the real tables are decoded.

## Source material audit
- The `v1.2/from-floppy/` directory still contains the raw `ml.extra` PRG alongside its PETCAT companion, confirming the recovered artefacts are available for analysis.【05efa7†L1-L2】
- Inspecting the PRG header shows a load address of `$1000`, matching the metadata captured when the floppy images were first ingested and giving us the base offset required for symbol mapping during disassembly.【7b45d7†L1-L2】【F:v1.2/from-floppy/README.md†L9-L14】
- A quick skim of the PETCAT dump reiterates that the overlay is dense PETSCII/machine code, reinforcing the need to treat its data segments separately from instruction streams when extracting lightbar tables.【df08da†L1-L13】

## Prior findings
- Iteration 19 documented the recovery of both `setup` and `ml.extra`, emphasising that the next step is to replace the stubbed lightbar tables and ampersand handlers with the authentic overlay data. Those notes remain the authoritative source on why the stub exists and what behaviour it attempts to mimic.【F:docs/porting/iteration-19.md†L1-L27】

## Stub placeholders to eliminate
- The stub seeds deterministic lightbar defaults (`DEFAULT_PAGE1_LEFT`/`RIGHT`, underline character/colour) and pushes them into the runtime buffers, all of which should be overwritten by values extracted from the recovered overlay.【F:v1.2/source/ml_extra_stub.asm†L75-L110】
- Human-readable flag descriptors and their default-state bytes live in `lightbar_flag_directory` and the `flag_desc_##` strings; these must be replaced with the real PETSCII records discovered in the disassembly.【F:v1.2/source/ml_extra_stub.asm†L112-L163】
- The helper copy of the lightbar bitmaps (`lightbar_stub_bitmaps`) and the placeholder palette/macro directory need to be swapped with authentic data once identified in `ml.extra`.【F:v1.2/source/ml_extra_stub.asm†L165-L188】

## Next steps
- Disassemble `ml.extra` with data-aware tooling so the real flag tables, palette bytes, and macro directory can be transplanted into the source tree.
- Update the stubs and host-side helpers to consume the recovered tables, then remove any commentary that labels them as provisional.
