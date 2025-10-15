# Iteration 14 – Deriving `bd.data` metadata from the stub drive map

## Goals
- Ensure the BASIC placeholder mirrors the manual's derived fields when
  `bd.data` omits explicit values for the highest configured device and the
  number of attached drives.
- Keep the host-side defaults helper in sync with the stub so experiments do
  not duplicate Commodore BASIC logic.

## `setup` Stub Updates
- After loading the six device/drive pairs the stub now copies the board
  identifier into `cc$` and, when either `bd` or `bu` is unset, calls a helper to
  compute the highest device minus seven and the distinct drive count from the
  staged tuples, matching the sysop manual's description of the record
  structure.【F:v1.2/core/setup.stub.txt†L19-L75】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6917-L6947】
- The new subroutine walks the populated `dv%()` array to find the largest
  device number and the unique device count so that subsequent overlays observe
  the same derived values the original program would have produced even without
  archival data files.【F:v1.2/core/setup.stub.txt†L76-L123】

## Host Defaults Helper
- `SetupDefaults.stub()` now derives the highest device and drive count from the
  declared drive assignments so Python prototypes automatically reflect the
  BASIC stub's computed metadata.【F:scripts/prototypes/setup_defaults.py†L64-L95】

## Follow-ups
- Extend the helper and stub once the recovered `bd.data` layout reveals how
  dual-drive and Lt. Kernal configurations encode multi-LU systems so the
  derived calculations stay faithful across hardware variants.
