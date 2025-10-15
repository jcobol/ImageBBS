# Iteration 03 – Memory Map and SwiftLink Driver Trace

## Goals
- Capture a working memory map for the zero-page and high-memory addresses mutated during Image BBS 1.2 startup so porting work can mirror required state.
- Analyse the SwiftLink/RS-232 driver to document how Image patches Kernal vectors, buffers serial traffic, and manages carrier detection.

## Zero-Page and High-Memory Touch Points

| Area | Purpose During Bootstrap | Source Notes |
| --- | --- | --- |
| `txttab`/`vartab`/`arytab`/`strend` | BASIC heap pointers are reset after loading the `im` program, then advanced to point at the free area before linking. | Bootstrap routine stores `txttab` at `$0146`, chains the other pointers, and calls the ROM linker. 【F:v1.2/source/ml-1_2-y2k.asm†L4771-L4804】【F:v1.2/source/equates-1_2.asm†L24-L32】 |
| `fa`/`sa`/`la` | Loader preserves the original logical/secondary address in `fa`, sets up LFS for overlay loads, and restores it after staging files. | `gotoc00b` saves the current output device from `fa` before each `SETLFS`. 【F:v1.2/source/ml-1_2-y2k.asm†L4744-L4785】【F:v1.2/source/equates-1_2.asm†L74-L79】 |
| `igone`, `ibsout`, `iload` | Image captures the Kernal warm-start, CHROUT, and load vectors to inject its own handlers while retaining the originals. | `sub_c283`, `sub_c21b`, and `sub_c29a` copy the old targets into private storage before patching the vectors. 【F:v1.2/source/ml-1_2-y2k.asm†L5012-L5084】【F:v1.2/source/equates-1_2.asm†L122-L132】 |
| `$01` CPU port | Startup toggles the memory configuration between `$36` and `$37` around overlay swaps to expose I/O or ROM as needed. | After installing vector hooks, the bootstrap writes `$36`, performs overlay setup, then restores `$37`. 【F:v1.2/source/ml-1_2-y2k.asm†L4988-L4994】 |
| `$d000` BBS flags and VIC-II | Interrupt prep zeroes `irqcount` and sets VIC raster control and colors, establishing Image’s ISR environment. | `sub_c240` writes CIA/VIC registers and the `$d00d` counter; `sub_c264` sets border/background colors. 【F:v1.2/source/ml-1_2-y2k.asm†L5032-L5061】【F:v1.2/source/ml-1_2-y2k.asm†L4981-L5055】 |
| RS-232 buffers (`$029b/$029c`, `$cb00`) | Bootstrap clears the SwiftLink jump table region and later relies on circular buffers managed by the driver. | `gotoc00b` fills the RS-232 stub with RTS bytes, and the driver’s NMI handler pushes characters into `$cb00` using the zero-page tail pointer. 【F:v1.2/source/ml-1_2-y2k.asm†L4811-L4822】【F:v1.2/source/ml.rs232-192k.asm†L123-L165】 |
| Serial number slots (`$02fd-$02ff`) | Hardware serial fields are reconstructed from the Image disk header immediately before returning to BASIC. | Final bootstrap steps decompose the packed ID bytes into prefix/value storage. 【F:v1.2/source/ml-1_2-y2k.asm†L4996-L5010】【F:v1.2/source/equates-1_2.asm†L118-L120】 |

## SwiftLink Driver Findings

### Vector Installation and Device Handshake
- `@rsinit` copies a jump table into the Kernal vector slots (`BRK`, `NMI`, `OPEN`, `CHROUT`, etc.) so Image’s replacements wrap the original handlers. It temporarily stores the original addresses and emits `JMP` opcodes inline. 【F:v1.2/source/ml.rs232-192k.asm†L27-L115】
- The routine primes the SwiftLink ACIA by disabling interrupts, zeroing `$de01`, setting the data-direction register on CIA #2, and recording the carrier detect bit into `$cfff`. 【F:v1.2/source/ml.rs232-192k.asm†L96-L114】

### Interrupt-Driven Receive Path
- The NMI handler (`newnmi`) disables ACIA IRQs, snapshots the SwiftLink status, and if carrier is present reads any queued byte from `$de00` into the circular buffer at `$cb00`, advancing the tail pointer at `$029b`. Finally it re-enables receive IRQs before returning. 【F:v1.2/source/ml.rs232-192k.asm†L123-L174】
- Buffer pointers align with the zero-page equates (`ridbe`/`ridbs`), confirming the expected `cb00` buffer layout referenced in the bootstrap memory map. 【F:v1.2/source/ml.rs232-192k.asm†L155-L165】【F:v1.2/source/equates-1_2.asm†L114-L115】

### Transmit Path and Channel Hooks
- `@rsout` blocks until the SwiftLink transmit register is clear (`$de01` bit 4), then writes the staged byte from `$9e` to `$de00`. 【F:v1.2/source/ml.rs232-192k.asm†L194-L206】
- Replacement `CHIN`, `CHOUT`, and `GETIN` handlers temporarily disable ACIA IRQs, defer to the ROM routines when the device number is not the SwiftLink channel (`#2`), and otherwise exchange data with the circular buffers while preserving registers. 【F:v1.2/source/ml.rs232-192k.asm†L208-L226】【F:v1.2/source/ml.rs232-192k.asm†L229-L245】

### Baud and Carrier Management
- `@rsbaud` interprets Image’s baud tokens: values below `$fe` index a table of ACIA control bytes for 300–38400 bps, while `$fe/$ff` switch between receive-only and full IRQ masks by writing `$de02`. 【F:v1.2/source/ml.rs232-192k.asm†L235-L269】
- Carrier status persists in `$cfff`, which both `@rsinit` and the NMI path refresh, providing a simple shared flag for higher-level modem logic. 【F:v1.2/source/ml.rs232-192k.asm†L111-L114】【F:v1.2/source/ml.rs232-192k.asm†L138-L146】

## Follow-Ups
- Confirm the size and wrap behaviour of the `$cb00` ring buffer so modern ports can allocate equivalent storage without depending on page alignment.
- Document `sub_c2d4` and `gotocd4f` to finish tracing how BASIC variables are pre-seeded after `sub_c335` runs.
