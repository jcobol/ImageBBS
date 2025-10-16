# Iteration 19 – Verifying the recovered `setup` and `ml.extra` overlays

## Goals
- Catalogue the newly recovered PRGs from the original ImageBBS 1.2B disk.
- Confirm the assets align with the expectations documented in the interim
  stubs so downstream tracing work can pivot to the authentic code.

## Disk artefacts
- `setup` and `ml.extra` now live under `v1.2/from-floppy/` alongside PETCAT
  listings, including header-derived load addresses that match the BASIC and
  machine-language stubs checked into the source tree.【F:v1.2/from-floppy/README.md†L1-L21】
- The BASIC listing enumerates the chat-mode banner variables (`c1$`–`c3$`),
  the paging state `ak$`, and the ampersand call that reaches the lightbar
  overlay via `&,52`, mirroring the placeholders we maintained in the stub to
  keep host prototypes deterministic.【F:v1.2/from-floppy/setup.txt†L59-L63】【F:v1.2/from-floppy/setup.txt†L143-L159】
- Disk loads for macro, prompt, and configuration REL files (`e.i.macro`,
  `e.i.prompt`, `e.amaint`, `lbsetup`, etc.) are all present, so the recovered
  overlay should let us finish the remaining `lbl_c2e5` variable audit once the
  token stream is fully decoded.【F:v1.2/from-floppy/setup.txt†L115-L147】
- The `ml.extra` PETCAT dump is densely PETSCII-encoded but confirms the PRG is
  machine-language. Disassembling it will be necessary to replace the stubbed
  lightbar tables and expose the remaining ampersand verbs.【F:v1.2/from-floppy/ml.extra.txt†L2-L15】

## Follow-ups
- Build a repeatable decode pipeline (e.g., `petcat` or custom tokenizer) so
  the BASIC listing can be reflowed into commented source and committed under
  `v1.2/source/` alongside the existing stubs.
- Use `64tass`/`cc65`-friendly disassembly helpers to convert `ml.extra` into
  an analysable assembly module, focusing first on the `&,52` handlers and
  lightbar flag tables referenced throughout the BASIC code.
- Once the overlays are disassembled, revisit the task backlog items related to
  tracing the remaining `lbl_c2e5` variables and chat-mode behaviours with the
  authentic data in hand.
