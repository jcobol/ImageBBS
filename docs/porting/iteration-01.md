# Iteration 01 – Loader and Startup Recon

## Context
This iteration establishes a baseline understanding of how Image BBS 1.2 boots
from its BASIC loader into the machine-language core. The goal is to document
the execution chain, note direct hardware dependencies, and enumerate open
questions to guide subsequent porting work.

## Boot Chain Observations
- **BASIC loader (`stack` routine).** The loader resets the BASIC main-loop
  vector, clears the screen, prints the "Image 1.2" banner, and loads the
  `ml 1.2` module before jumping into machine language at `$c000`.
- **Machine-language entry (`lbl_c000` → `gotoc00b`).** The first machine-code
  routine captures the current output device, opens the `screen 1.2` file, and
  loads it using standard Kernal `SETLFS`, `SETNAM`, and `LOAD` calls.
- **Module staging.** After staging `screen 1.2`, the loader fetches the BASIC
  program `im`, adjusts BASIC's `TSTTAB`/`VARTAB`/`ARYTAB` pointers to account
  for the freshly loaded code, links the program, and then pulls in the
  `ml.extra` and `ml.editor` overlays.
- **Vector initialization.** The loader copies values into zero-page vectors
  (`TXT TAB`, `VARTAB`, `AR-TAB`, `STREND`) and eventually calls the BASIC
  linking routine at `$a533` to integrate the `im` program into memory.

## Hardware and Environment Interactions
- **Display control.** The BASIC loader directly updates `$d020/$d021` to set
  border/background colors and uses the `$93` (clear screen) control code on the
  console. The machine-language bootstrap later clears status-line buffers and
  sets up screen masks used by the sysop UI.
- **RS-232 buffers.** Both the BASIC loader and `gotoc00b` zero out RS-232
  handler space at `$4300`-ish (`rsinit`), demonstrating a reliance on the
  Commodore 64's memory-mapped serial routines.
- **Memory map control.** The bootstrap toggles `$01` between `$36` and `$37`
  while calling routines such as `$cb00`, indicating it momentarily pages out
  ROM to access I/O or extra RAM during initialization.

## BASIC Program Surface Scan (`im.txt`)
- The `im` BASIC program begins around line 1000 with device/disk management
  utilities (`gosub 1001`, `gosub 1010`, etc.), confirming that disk handling is
  interleaved with user-visible text routines.
- Early routines rely on global arrays (e.g., `dv%`, `dr%`, `tt$`) and make
  heavy use of `PRINT#` and channel commands, underscoring how tightly the code
  is bound to Commodore DOS semantics.
- The program dedicates substantial code to file uploads/downloads (`open6` with
  `",s,r"` and `",s,w"` modes) and terminal interactions (`poke 53249`,
  `poke 53252`), which will need abstraction when ported.

## Open Questions
- How do the `ml.extra` and `ml.editor` overlays extend the base system, and do
  they rely on additional hardware state that must be emulated?
- What responsibilities are handled by routines invoked during bootstrap
  (`sub_c21b`, `sub_c240`, `sub_c283`, `sub_c29a`, `sub_c335`), and which of
  them are essential for a minimal port versus optional diagnostics/UI setup?
- Which Kernal vectors or zero-page locations are ultimately patched by the
  overlays after the initial load sequence completes?

## Suggested Next Steps
- Trace each bootstrap subroutine (starting at `$c21b`) to map out IRQ setup,
  modem initialization, and memory configuration dependencies.
- Catalogue the BASIC `im` program's major GOSUB entry points and their side
  effects to identify logical modules (user I/O, sysop utilities, message base,
  etc.).
- Investigate the RS-232 handling code in `ml.rs232-192k.asm` to understand the
  expectations of the modem driver and how it interfaces with SwiftLink or
  user-port hardware.
