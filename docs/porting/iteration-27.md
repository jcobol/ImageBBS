# Iteration 27 – Sanity-checking the recovered `ml.extra` data

## Goals
- Diff the recovered macro directory against the stub placeholders so we know what will change once the authentic overlay replaces the documentation-only defaults.
- Add a repeatable check that validates the pointer-directory payloads (slot count, termination) before we depend on them in host tooling.

## Findings
- Introduced `ml_extra_sanity.py`, a CLI helper that loads the archived overlay, parses the stubbed macro directory for comparison, and prints a slot-by-slot summary including payload length, decoded PETSCII preview, and the placeholder string (if any). The script doubles as a JSON emitter so future regression tooling can ingest the same facts.【F:scripts/prototypes/ml_extra_sanity.py†L1-L170】
- Running the helper confirms the overlay exposes twelve macro slots versus the stub’s four and that every payload is null-terminated. The recovered data is mostly machine-language tokens rather than the human-readable macro names baked into the stub, which explains why the placeholders diverge so sharply from the live system.【ed1937†L1-L17】

## Next steps
- Re-run the sanity check after transplanting the authentic tables into `ml_extra_stub.asm` to document the behavioural deltas.
- Extend the helper once we decode the lightbar bitmaps and palette bytes so the regression report covers the entire overlay payload.
