# Iteration 21 – Aligning the `setup` stub with the recovered overlay

## Goals
- Catalogue the gaps between `v1.2/core/setup.stub.txt` and the authentic
  `setup.bas`, focusing on `DATA` records, staged variables, and overlay loads.
- Sync the stub so its commentary, staged defaults, and placeholders mirror the
  real BASIC control flow.
- Teach the Python prototypes to source defaults from the annotated stub and to
  extract canonical data straight from `setup.bas`.

## Implementation notes
- Reworked `setup.stub.txt` into an annotated mirror of the recovered program:
  it now documents the dimensioning pass, the BD.DATA staging sequence, REL/ML
  overlay loads, and the authentic lightbar `DATA` records. Stub-default
  annotations mark the deterministic values consumed by host tooling, while
  placeholders flag the still-missing disk-backed records.【F:v1.2/core/setup.stub.txt†L1-L148】
- Cross-referenced the stub against the authentic BASIC listing to confirm the
  carousel `DATA` strings, the BD.DATA/TABLE staging loop, and the overlay load
  order (`E.I.MACRO`, `E.I.PROMPT`, `E.AMAINT`, `LBSETUP`, `E.LOG`, `ML.RS232`,
  `ML.PMODES`). The new Python helpers parse these sequences directly from
  `setup.bas`, eliminating guesswork in future audits.【F:v1.2/source/setup.bas†L82-L194】【F:v1.2/source/setup.bas†L167-L172】
- Extended `scripts/prototypes/setup_defaults.py` with utilities to read the
  annotated stub, decode the `DATA` statements, and derive the overlay load
  sequence. `SetupDefaults.stub()` now reuses those helpers so host prototypes
  stay synchronized with the curated listings.【F:scripts/prototypes/setup_defaults.py†L1-L430】

## Follow-ups
- Replace the remaining placeholders once the project extracts canonical
  `bd.data`/`u.config` records from disk images. The parsing hooks are ready to
  absorb the verified values with minimal code churn.
