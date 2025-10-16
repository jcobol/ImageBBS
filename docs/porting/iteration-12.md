# Iteration 12 – Enriching the `setup` and `ml.extra` stubs

## Goals
- Capture the lightbar flag semantics wired into `&,52` so ports can expose
  meaningful labels while the real `ml.extra` binary is missing.
- Mirror the sysop manual’s description of the configuration files (`bd.data`,
  `u.config`, `e.data`) inside the BASIC `setup` stub so bootstraps get
  repeatable defaults.

## `ml.extra` Updates
- The stub seeds the `chk_left`, `chk_right`, and page-two bitmaps that the
  machine-language dispatcher expects, mirroring the recovered overlay defaults
  so host prototypes surface the same initial lightbar state as Image 1.2
  proper.【F:v1.2/source/ml_extra_stub.asm†L19-L47】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L1895-L2043】
- Palette, underline, and banner metadata from the rediscovered module now live
  alongside the XOR-encoded flag-directory block, letting ports lift the
  original VIC-II and PETSCII defaults directly from the stub without bundling
  the full PRG.【F:v1.2/source/ml_extra_stub.asm†L49-L88】
- The macro pointer table and payload blobs have been transplanted wholesale
  from the overlay, keeping the runtime slot ordering, targets, and staged
  bytecode available for inspection while the BASIC bootstrap continues to load
  this lighter-weight surrogate.【F:v1.2/source/ml_extra_stub.asm†L89-L136】【F:v1.2/core/setup.stub.txt†L100-L144】

## `setup` Updates
- The BASIC stub now reads DATA statements that approximate the first records
  of `bd.data`, `u.config`, and `e.data`, matching the manual’s narrative so
  the default drive map, sysop profile, and statistics fields stay in sync
  across environments.【F:v1.2/core/setup.stub.txt†L20-L144】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6880-L6940】
- Plus-module metadata has been expanded to include the modem helpers called
  out by the manual and machine-language loader, allowing host prototypes to
  surface consistent module lists during development.【F:v1.2/core/setup.stub.txt†L100-L144】【F:v1.2/source/ml-1_2-y2k.asm†L4826-L4841】

## Follow-ups
- **Done (Iteration 23):** The conservative lightbar defaults and placeholder
  macros were replaced with the archived overlay payloads now embedded in the
  stub, ensuring `ml.extra` consumers see authentic data during bootstrap.
  【F:v1.2/source/ml_extra_stub.asm†L19-L136】【F:docs/porting/iteration-23.md†L131-L139】
- Verify the DATA-driven defaults against a real `setup` listing to confirm
  whether additional variables (for example prime-time windows or colour
  palettes) should be preloaded before jumping into `im`.
