# Iteration 11 – Stubbing the Missing `setup` and `ml.extra` Overlays

## Goals
- Provide deterministic placeholder assets for the absent `setup` BASIC overlay
  and the `ml.extra` machine-language module so host-side prototypes can run
  repeatable experiments while we continue sourcing the original PRGs.
- Capture the assumptions baked into those stubs so the real listings can swap
  in without surprising downstream tooling.

## `setup` Stub
- The sysop manual confirms that after the bootstrap loads `im` it runs
  `setup` to dimension variables, read `bd.data`, `u.config`, `e.data`, and
  `e.stats`, and only then transfers control to the main BASIC dispatcher.【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6864-L6918】
- The stub initialises the array slots that the machine-language bootstrap
  exposes via `lbl_c2e5`, seeds plausible defaults for the six drive pairs,
  and manufactures placeholder sysop records so routines such as line 1071 in
  `im` can concatenate user metadata without tripping over `GET`/`PRINT#`
  calls.【F:v1.2/core/setup.stub.txt†L1-L54】【F:v1.2/core/im.txt†L40-L48】
- Variables that never appear in the published `im` listing but are referenced
  in the bootstrap’s token table (`D5`, `AK`, `MW`, `C1`–`C3`, `KP`) receive
  explicit initialisers so future overlays may assume they exist even before
  we recover the authentic program.【F:v1.2/core/setup.stub.txt†L36-L38】【F:v1.2/source/ml-1_2-y2k.asm†L5120-L5155】

## `ml.extra` Stub
- Image’s ampersand dispatcher (`&,52`) relies on data supplied by `ml.extra`
  to evaluate feature bits for paging, macros, and expert mode toggles. The
  `im` listing exercises these combinations at lines 1599, 1648, 1813, 1851,
  and 1852, while the machine-language implementation of `chkflags` reveals the
  pointer arithmetic and mutation semantics expected of the overlay.【F:v1.2/core/im.txt†L150-L220】【F:v1.2/source/ml-1_2-y2k.asm†L3210-L3336】
- The stub defines a compact bitmap for the observed flag indices, minimal
  routines that clear the BASIC accumulator when queried, and scratch bytes so
  host tests can verify which toggles were exercised even without the real
  machine code.【F:v1.2/source/ml_extra_stub.asm†L34-L71】
- Placeholder palette and macro tables stand in for the data that the editor
  overlay expects to find after `ml.extra` is swapped into $2000/$d000, keeping
  the bootstrap sequence coherent until we can inspect the true binary.【F:v1.2/source/ml_extra_stub.asm†L73-L91】【F:v1.2/source/ml-1_2-y2k.asm†L4888-L4959】

## Next Steps
- Replace the stubs with verified dumps from archival disks as soon as they are
  sourced and update the documentation to describe the genuine control flow.
- Extend the prototype loader so it can consume either the stubs or real PRGs
  transparently once disk images land in the repository.
