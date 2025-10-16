# Iteration 20 – Reflowing the recovered `setup` overlay

## Goals
- Replace the one-off PETCAT dump of the recovered BASIC overlay with a
  repository-native decoding pipeline.
- Commit a reproducible listing under `v1.2/source/` so future research can
  annotate the authentic `setup` program instead of relying on the stopgap
  stub.

## Implementation notes
- Added `scripts/decode_basic_prg.py`, a pure-Python tokenizer that walks the
  Commodore BASIC V2 line structure, expands keywords, and preserves PETSCII
  control bytes as `{${hex}}` escape markers. The helper mirrors PETCAT's
  “upper/graphics” mode so we can rebuild listings without requiring the VICE
  toolchain.【F:scripts/decode_basic_prg.py†L1-L274】
- Ran the decoder against `v1.2/from-floppy/setup` and checked in the resulting
  listing as `v1.2/source/setup.bas`. The file captures the original variable
  seeding logic, disk overlay loads, and lightbar configuration strings that the
  stub only approximated.【F:v1.2/source/setup.bas†L1-L205】
- Documented the workflow in `v1.2/from-floppy/README.md` so contributors know
  how to refresh the listings when new disk images land.【F:v1.2/from-floppy/README.md†L22-L33】

## Follow-ups
- Integrate the decoded overlay into the existing annotation workflow so the
  backlog items around `lbl_c2e5` variable tracing can pivot away from the
  stubbed defaults.
- Extend `decode_basic_prg.py` with optional PETSCII glyph tables so that future
  listings can substitute human-friendly mnemonics (`{CBM-R}`, `{SHIFT-*}`,
  etc.) when the additional fidelity aids analysis.
