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

## Stub updates after decoding
- The stub now copies the overlay's lightbar bitmaps (`$00,$03,$06,$00`) and zeroed underline defaults straight into the runtime buffers so the Y2K loader observes the same startup state as the original overlay.【F:v1.2/source/ml_extra_stub.asm†L26-L57】
- The human-readable `lightbar_flag_directory` scaffolding has been retired; in its place the file exposes the raw lightbar/underline bytes, palette, slot IDs, runtime targets, and macro payloads recovered from the overlay for downstream tooling.【F:v1.2/source/ml_extra_stub.asm†L59-L119】

## Next steps
- Propagate the recovered tables through the remaining host-side helpers so no documentation or tooling relies on the removed placeholders.
