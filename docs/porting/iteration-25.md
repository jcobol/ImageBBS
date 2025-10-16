# Iteration 25 – Capturing raw `ml.extra` pointer payloads

## Goals
- Extend the pointer-directory prototype so future tooling can emit the raw byte sequences referenced by the lightbar slots instead of only presenting lossy placeholder text.
- Inventory the extracted payloads to confirm record boundaries and highlight the additional decoding work still required before the stub can be replaced with the real overlay data.

## Findings
- `ml_extra_extract.py` now records the PETSCII blobs verbatim for each of the twelve directory slots, making it possible to diff the recovered bytes against the on-disk overlay during the upcoming transplant step.【F:scripts/prototypes/ml_extra_extract.py†L18-L100】
- The helper continues to emit a best-effort PETSCII transcription for quick inspection, but the raw byte arrays clarify that the authentic overlay stores macro bodies rather than human-readable prose, so the stub will need to embed those binary sequences directly.【F:scripts/prototypes/ml_extra_extract.py†L42-L94】

## Next steps
- Decode the `$c200` lightbar tables and palette/macro metadata so `ml_extra_stub.asm` can be populated with the authentic defaults.
- Translate the captured PETSCII control codes into the `{CBM-…}` notation used throughout the porting logs to ease manual review of the binary blobs.
