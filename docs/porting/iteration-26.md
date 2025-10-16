# Iteration 26 – Host access to recovered `ml.extra` tables

## Goals
- Provide a host-friendly helper that reads the archived `ml.extra` overlay directly so prototypes no longer depend on the stubbed flag and macro tables.
- Mirror the structure of `setup_defaults.py` by exposing dataclasses for the pointer-directory slots and resolving the overlay path from the repository tree.

## Findings
- The `MLExtraDefaults` helper now exposes the overlay's lightbar defaults, underline metadata, editor palette, and macro pointer directory so host tooling can read the authoritative values without consulting the stub.【F:scripts/prototypes/ml_extra_defaults.py†L1-L149】
- The helper remains part of the `scripts.prototypes` namespace, providing a single import path for downstream utilities and a centralised `default_overlay_path()` for reproducible ingestion.【F:scripts/prototypes/__init__.py†L1-L39】【F:scripts/prototypes/ml_extra_defaults.py†L141-L149】

## Next steps
- Audit consumers of `MLExtraDefaults` to ensure they account for the newly exposed lightbar and palette fields.
- Keep refining the PETSCII decoding helpers so the macro payload previews remain readable even after the binary data replaced the prose placeholders in `ml_extra_stub.asm`.
