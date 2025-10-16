# Iteration 26 – Host access to recovered `ml.extra` tables

## Goals
- Provide a host-friendly helper that reads the archived `ml.extra` overlay directly so prototypes no longer depend on the stubbed flag and macro tables.
- Mirror the structure of `setup_defaults.py` by exposing dataclasses for the pointer-directory slots and resolving the overlay path from the repository tree.

## Findings
- The new `MLExtraDefaults` helper wraps the existing extractor so callers receive immutable records for each macro slot, including the relocation address, raw byte payload, and decoded PETSCII preview.  This removes the need to hard-code stubbed strings inside host tooling and paves the way for future lightbar and palette data once those segments are decoded.【F:scripts/prototypes/ml_extra_defaults.py†L1-L74】
- The prototype is wired into the `scripts.prototypes` namespace, giving downstream utilities parity with `setup_defaults.py` and centralising the default overlay path under `default_overlay_path()` for reproducible ingestion.【F:scripts/prototypes/__init__.py†L1-L39】【F:scripts/prototypes/ml_extra_defaults.py†L76-L88】

## Next steps
- Extend the helper once the `$c200` lightbar tables and palette bytes are decoded so the dataclass set reflects the entire overlay dataset.
- Use the new API to transplant the authentic macro payloads into `ml_extra_stub.asm`, replacing the prose placeholders captured during the initial stub creation.
