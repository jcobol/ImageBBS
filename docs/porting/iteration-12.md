# Iteration 12 – Enriching the `setup` and `ml.extra` stubs

## Goals
- Capture the lightbar flag semantics wired into `&,52` so ports can expose
  meaningful labels while the real `ml.extra` binary is missing.
- Mirror the sysop manual’s description of the configuration files (`bd.data`,
  `u.config`, `e.data`) inside the BASIC `setup` stub so bootstraps get
  repeatable defaults.

## `ml.extra` Updates
- The stub now seeds the `chk_left`, `chk_right`, and `bar` bitmaps that the
  machine-language dispatcher expects, defaulting only the sysop chat page to
  “on” and leaving other automation toggles cleared until configured by the
  operator.【F:v1.2/source/ml_extra_stub.asm†L27-L86】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L1895-L2043】
- A host-facing directory enumerates all 32 flag slots with PETSCII
  descriptions and default states so tooling can present the same terminology
  documented in the manual.【F:v1.2/source/ml_extra_stub.asm†L88-L151】
- The macro directory placeholder mirrors the BASIC stub’s list of
  “little modem” overlays so both halves of the boot chain agree on the files
  that should exist while archival recovery continues.【F:v1.2/source/ml_extra_stub.asm†L157-L166】【F:v1.2/core/setup.stub.txt†L100-L144】

## `setup` Updates
- The BASIC stub now reads DATA statements that approximate the first records
  of `bd.data`, `u.config`, and `e.data`, matching the manual’s narrative so
  the default drive map, sysop profile, and statistics fields stay in sync
  across environments.【F:v1.2/core/setup.stub.txt†L20-L144】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6880-L6940】
- Plus-module metadata has been expanded to include the modem helpers called
  out by the manual and machine-language loader, allowing host prototypes to
  surface consistent module lists during development.【F:v1.2/core/setup.stub.txt†L100-L144】【F:v1.2/source/ml-1_2-y2k.asm†L4826-L4841】

## Follow-ups
- Replace the conservative lightbar defaults with the real persisted bitmaps
  once the genuine `ml.extra` overlay is recovered from distribution disks.
- Verify the DATA-driven defaults against a real `setup` listing to confirm
  whether additional variables (for example prime-time windows or colour
  palettes) should be preloaded before jumping into `im`.
