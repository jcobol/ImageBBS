# Iteration 27 – Sanity-checking the recovered `ml.extra` data

## Goals
- Diff the recovered macro directory against the stub placeholders so we know what will change once the authentic overlay replaces the documentation-only defaults.
- Add a repeatable check that validates the pointer-directory payloads (slot count, termination) before we depend on them in host tooling.

## Findings
- `ml_extra_sanity.py` now reports the overlay's lightbar defaults and palette alongside the macro slot diff so the regression output reflects the complete data set transplanted into the stub.【F:scripts/prototypes/ml_extra_sanity.py†L1-L119】
- The macro-dump and disassembly helpers gained a `--metadata` switch so reviewers can surface the lightbar, palette, and hardware tables without sifting through the JSON sanity output.【F:scripts/prototypes/ml_extra_dump_macros.py†L1-L132】【F:scripts/prototypes/ml_extra_disasm.py†L1-L204】
- `decode_petscii` renders control bytes as `{${hex}}` placeholders again, ensuring swapped-in control sequences stay readable; dedicated unit tests cover the new behaviour.【F:scripts/prototypes/ml_extra_extract.py†L1-L120】【F:tests/test_ml_extra_extract.py†L1-L20】
- Running the helper highlights the delta between the recovered macro payloads and the removed placeholders while noting that all twelve slots remain null-terminated and ready for host consumption.【853914†L1-L18】

## Next steps
- Monitor the sanity-check output after future edits to ensure the lightbar and palette metadata stay synchronised with the archived overlay.
- Extend the JSON schema if downstream tooling needs per-slot payload hashes or additional metadata beyond the current length/preview summary.
