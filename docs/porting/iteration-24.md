# Iteration 24 – Probing the `ml.extra` pointer directory

## Goals
- Prototype a Python helper that can read the recovered `ml.extra` PRG and surface machine-language data as structured output.
- Use the helper to locate the pointer directory documented in Iteration 23 and verify the slot ordering against the live binary.

## Findings
- The overlay stores two 4 KB segments: the first relocates to $c000 and carries the macro/bitmap routines, while the second copies to $d000 and contains the flag pointer directory plus additional tables.【F:scripts/prototypes/ml_extra_extract.py†L10-L82】
- Parsing the $d115 pointer block yields the expected slot order `[04, 09, 0d, 14, 15, 16, 17, 18, 19, 0e, 0f, 02]`, matching the disassembly walkthrough from Iteration 23.【F:scripts/prototypes/ml_extra_extract.py†L71-L94】
- The strings referenced by those pointers decode to PETSCII-heavy control sequences rather than human-friendly labels, implying the BASIC stub’s prose will have to be replaced with the overlay’s command macros during the data transplant.【F:scripts/prototypes/ml_extra_extract.py†L55-L69】

## Next steps
- Keep refining the extractor's PETSCII mapper so JSON output captures control codes in the `{CBM-…}` notation used elsewhere in the logs.
- Maintain the lightbar/palette offsets in the helper as additional tables are decoded so future automation does not regress the recovered addresses.
