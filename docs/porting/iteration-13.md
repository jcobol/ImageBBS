# Iteration 13 – Documenting `bd.data` fields and host-side defaults

## Goals
- Bring the `setup` stub's `bd.data` and `e.data` placeholders in line with
the sysop manual so that future overlays can rely on the same field ordering as
the original program.
- Provide a Python helper that mirrors those deterministic defaults so host
prototypes do not need to scrape BASIC listings to stage configuration data.

## `setup` Stub Updates
- Stage 2 now reads the board identifier, new-user credits, highest-device
marker, drive count, board name, prompt text, and copyright string from a single
`DATA` record, mirroring the manual's description of the sequential
`bd.data` layout.【F:v1.2/core/setup.stub.txt†L12-L30】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6933-L6956】
- The stub preserves any identifier supplied by that `DATA` row and only falls
back to `"IM"` when absent while keeping the sysop profile initialisation the
real overlay performs.【F:v1.2/core/setup.stub.txt†L32-L41】
- Stage 4 now seeds the prime-time flag alongside its start and end markers so
the `pt%`, `p1%`, `p2%`, and `p3%` variables match the manual's summary of
`e.data` record 20.【F:v1.2/core/setup.stub.txt†L43-L47】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6898-L7004】

## Host Defaults Helper
- Introduced `scripts/prototypes/setup_defaults.py`, which wraps the stubbed
values—drive assignments, sysop profile, prime-time window, and plus-module
list—in typed dataclasses so host tooling can import a structured view of the
boot defaults without reimplementing the BASIC reader.【F:scripts/prototypes/setup_defaults.py†L1-L104】【F:v1.2/core/setup.stub.txt†L21-L53】
- Re-exported the new helper classes from the prototypes package so existing
experiments can pull the shared defaults from a single namespace.【F:scripts/prototypes/__init__.py†L3-L45】

## Follow-ups
- Swap the placeholder constants with verified values once an authentic copy of
the `setup` overlay is recovered and confirm the prime-time tuple matches the
real `e.data` record formatting.
- Extend the helper with parsed access-group definitions and BAR statistics
once the backing REL files are available for inspection.
