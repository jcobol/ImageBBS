# Iteration 02 – Bootstrap Subroutines and Load Map

## Goals
- Annotate the key initialization helpers (`sub_c21b`, `sub_c240`, `sub_c283`, `sub_c29a`, `sub_c335`) invoked during the Image BBS 1.2 bootstrap sequence.
- Inventory every file loaded before control is handed to the BASIC program and point to the corresponding source artefacts (or gaps) in the repository.

## Initialization Helper Annotations

| Routine | Role in Bootstrap | Hardware / Kernal Touch Points |
| --- | --- | --- |
| `sub_c21b` | Hooks the `CHROUT` (`ibsout`) vector so Image's output filter at `$cd2f` intercepts character output. If the vector already points at `$cd2f`, the routine exits early; otherwise, it preserves the previous pointer at `$cd4d`/`$cd4e` for later fall-through and then patches the vector. | Stores and replaces the `CHROUT` vector at `$0326/$0327`; writes to the Image patch site at `$cd4c+1`. 【F:v1.2/source/ml-1_2-y2k.asm†L4853-L4873】 |
| `sub_c240` | Rehomes the IRQ vector to Image's raster interrupt service at `$cc32`, disables pending CIA #1 interrupts, enables VIC-II raster IRQs, and zeros the raster latch and Image's internal IRQ counter. | Updates CIA1 ICR at `$dc0d`, IRQ vector at `$0314/$0315`, VIC-II registers `$d01a`, `$d012`, `$d011`, and Image's `irqcount` state at `$d00d`. 【F:v1.2/source/ml-1_2-y2k.asm†L4875-L4896】 |
| `sub_c283` | Patches BASIC's `IGONE` vector to point at Image's warm-start shim (`$cd97`) while saving the original target at `mod_cdbd`. This lets Image layer custom recovery/warm-start behaviour without losing the original entry. | Reads and writes `IGONE` at `$0308/$0309`; stores the old target in Image's code block at `$cdbd/$cdbe`. 【F:v1.2/source/ml-1_2-y2k.asm†L4900-L4914】 |
| `sub_c29a` | Captures the existing `ILOAD` vector and redirects it to Image's loader hook at `$cac8`, enabling the BBS to intercept Kernal load calls (e.g., to toggle memory banks during overlay loads). | Copies `ILOAD` from `$0330/$0331` into `var_e404`, then sets `ILOAD` to `$cac8`. 【F:v1.2/source/ml-1_2-y2k.asm†L4916-L4928】 |
| `sub_c335` | Iterates through a table of 40 pre-defined BASIC variable names (via `sub_c2d4`) and seeds the BASIC variable table so that subsequent modules (notably `setup`) find DIMmed storage ready. Each pass points the current variable descriptor at the allocation pointed to by `varpnt`. | Uses BASIC workspace pointers (`varnam`, `varpnt`) and writes into `vartable` (`$b5cc` onward). Relies on `sub_c2d4`/`gotocd4f` to instantiate variables. 【F:v1.2/source/ml-1_2-y2k.asm†L4934-L4973】 |

## Bootstrap Load Map

| Load Order | Filename (as loaded) | Purpose in Boot | Repository Source Notes |
| --- | --- | --- | --- |
| 1 | `ml 1.2` | Primary machine-language core reached from the BASIC loader. | Source in `v1.2/source/ml-1_2-y2k.asm`. 【F:v1.2/source/image12.asm†L10-L44】【F:v1.2/source/ml-1_2-y2k.asm†L4739-L4764】 |
| 2 | `screen 1.2` | Stages screen masks/status templates before BASIC is linked. | No discrete PRG dump in repository; only the filename string is referenced in `ml-1_2-y2k.asm`. Extraction from original disk image required. 【F:v1.2/source/ml-1_2-y2k.asm†L4746-L4761】 |
| 3 | `im` | Main BASIC program containing user-visible logic. | Tokenised program available as `v1.2/core/im.txt` (generated from `im.prg`). 【F:v1.2/source/ml-1_2-y2k.asm†L4764-L4811】【F:v1.2/core/README.md†L1-L4】 |
| 4 | `setup` | Initializes BASIC variables, DIMs arrays, and configures devices before handing control to `RUN`. | Source PRG not tracked in repo; the manual documents behaviour but no listing is present. Noted gap for future extraction. 【F:v1.2/source/ml-1_2-y2k.asm†L4812-L4851】 |
| 5 | `ml.extra` | Machine-language overlay swapped into `$2000/$d000` blocks after load. | No matching assembly/disassembly file in tree; only referenced by name. Requires recovery from distribution disk. 【F:v1.2/source/ml-1_2-y2k.asm†L4826-L4841】 |
| 6 | `ml.editor` | Editor overlay providing the message editor and related routines. | Disassembly work-in-progress in `v1.2/source/ml_editor-converting.asm`. 【F:v1.2/source/ml-1_2-y2k.asm†L4842-L4867】【F:v1.2/source/ml_editor-converting.asm†L1-L64】 |

## Follow-up Questions
- The repository lacks PRG dumps for `screen 1.2`, `setup`, and `ml.extra`. Confirm where these assets should live (e.g., import from disk images or locate upstream disassemblies) so subsequent iterations can analyse them alongside `im` and `ml.editor`.
- `sub_c335` depends on the behaviour of `gotocd4f`; auditing that routine will clarify exactly how the BASIC variable table is being seeded.
