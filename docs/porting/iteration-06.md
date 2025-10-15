# Iteration 06 – Ampersand Dispatch and BASIC Write Path

## Goals
- Document how the BASIC ampersand wedge (`&`) loads machine-language routines and feeds them register arguments so the variable write helpers can be mirrored in a modern port.
- Outline an approach for recovering the missing BASIC overlays (`setup`, `ml.extra`, etc.) that likely exercise the remaining `lbl_c2e5` variables.

## Findings

### `sub_cd00` Maps `&` Calls to Machine-Language Entry Points
`sub_cd00` is the dispatcher that runs whenever BASIC encounters an ampersand call. It first invokes `sub_cc0f`, which evaluates up to three comma-separated arguments and stashes the results in scratch locations (`sareg`, `sxreg`, `syreg`).【F:v1.2/source/ml-1_2-y2k.asm†L5557-L5573】【F:v1.2/source/ml-1_2-y2k.asm†L5640-L5645】`sub_cc6c` then doubles the routine number supplied in `A`, looks up the corresponding entry in `amptable`, and returns the target address split across `X` and `Y` while the dispatcher restores the machine configuration.【F:v1.2/source/ml-1_2-y2k.asm†L447-L506】【F:v1.2/source/ml-1_2-y2k.asm†L5607-L5623】`sub_cd00` patches that address into a self-modifying `JSR`, reloads the second and third arguments into `X` and `Y`, and finally jumps into the chosen machine routine with BASIC banked back in so helpers such as `ptrget1` remain callable.【F:v1.2/source/ml-1_2-y2k.asm†L5646-L5659】

The `im` program demonstrates the calling convention: line 1096 issues `&,52,13,3`, which selects table entry 52 (`chkflags`) and passes flag index `13` in `X` alongside operation `3` in `Y`.【F:v1.2/core/im.txt†L66-L66】【F:v1.2/source/ml-1_2-y2k.asm†L449-L503】【F:v1.2/source/ml-1_2-y2k.asm†L3210-L3247】This confirms that the wedge routes the first argument to the routine selector and the next two to the 6502 index registers, exactly matching the expectations encoded in the machine-language helpers.

### `sub_b552` and `putvar` Provide BASIC’s Variable Write Path
`sub_b552` consumes the variable index left in `X`, doubles it, and fetches a pointer from the pre-populated `vartable`, loading the descriptor address into `varpnt`.【F:v1.2/source/ml-1_2-y2k.asm†L3535-L3544】`putvar` uses that pointer to copy the five-byte floating accumulator image from `fac1` into the BASIC variable descriptor, giving machine code a symmetric way to write values after `usevar`/`sub_b597` fetch them.【F:v1.2/source/ml-1_2-y2k.asm†L3576-L3605】The dormant fall-through to `sub_b560` shows Image can also resolve variables by two-character token when callers provide a name instead of an index, mirroring the read-side helpers that jump through `gotocd4f`.【F:v1.2/source/ml-1_2-y2k.asm†L3535-L3554】【F:v1.2/source/ml-1_2-y2k.asm†L3592-L3599】Any port that emulates the ampersand API therefore needs to honor both calling conventions: direct index writes (`&,30,<slot>`) and ROM-assisted token lookups for overlays that supply explicit names.

### Missing Overlays Likely Drive the Remaining Variables
The Image 1.2B sysop manual confirms that after the machine-language bootstrap loads `im`, it immediately chains into the `setup` program to dimension variables and fetch configuration records before running the board.【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6864-L6883】Because `setup` and sibling overlays are absent from the repository, the variables without observed usage in iteration 05 (`D5`, `AK`, `MW`, `C1`–`C3`, `KP`) remain unexplained. Recovering those PRGs from the original boot disks is the next prerequisite for tracing how BASIC code exercises the write path and for validating the dormant token-based branch in `putvar`.

## Implications for the Port
- Host implementations must replicate the ampersand dispatcher so that the first numeric argument selects a routine and the next two map to the 6502 index registers before control jumps into ported helpers.
- The variable write API needs parity with the read path: provide an allocator that can return descriptors by table index and a lookup mechanism that can resolve two-character tokens via a BASIC-like symbol table when overlays supply explicit names.
- Overlay recovery is required to finish naming the seeded variables and to catalog the real-world `&,30` callers that motivate the `putvar` token branch.

## Follow-Ups
- Extract the `setup`, `ml.extra`, and related PRGs from an Image 1.2 disk image so their ampersand calls and variable usage can be documented alongside `im`.
- [x] Trace the ROM expression parser that `sub_cc02`/`sub_cc0f` rely on, ensuring the modern port can evaluate ampersand arguments (numbers, expressions, or strings) the same way the original wedge does. *(See iteration 07.)*
