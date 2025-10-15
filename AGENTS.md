# Agent Notes for ImageBBS Repository

## Entry Point Information
- The BASIC loader sets the main-loop vector to the `stack` routine in `v1.2/source/image12.asm`. When the program loads, execution begins in this routine, which clears the screen, prints the Image 1.2 banner, stages the filename `ml 1.2`, and then jumps to `$c000` after loading the machine-language module.
- Within the machine-language module, the initialization entry point is label `lbl_c000` in `v1.2/source/ml-1_2-y2k.asm`. It immediately jumps to `gotoc00b`, which completes the startup sequence by configuring loader parameters and continuing system initialization.

## Porting Considerations
- ImageBBS 1.2 is tightly coupled to the Commodore 64 environment. The BASIC loader immediately manipulates Kernal vectors and hands off to 6502 machine code that assumes specific zero-page layouts, ROM entry points, and memory-mapped hardware.
- Assembly modules patch Kernal vectors and interact directly with CIA/ACIA registers (e.g., for the SwiftLink serial driver). Porting requires reimplementing interrupt handlers, buffering, and modem control logic rather than translating syntax line-for-line.
- Commodore BASIC routines interleave user features with direct register and screen memory manipulation (`POKE`, `OPEN`, `PRINT#`). Higher-level behavior depends on those side effects, so understanding each routine’s intent is a prerequisite to any rewrite.
- Treat porting as a ground-up reimplementation: document observable behavior under emulation, design abstractions for storage/networking/terminal I/O in the target platform, and rebuild functionality using that specification. An alternative is embedding the original code in a C64 emulator and exposing higher-level APIs, which trades extensibility for quicker integration.

## Research & Task Tracking Guidance
- Maintain a “porting log” that records findings about routine intent, hardware interactions, open questions, and decisions. Link each entry to corresponding code locations so future contributors can avoid repeating reverse-engineering work.
- Keep a living task backlog (Markdown checklist, issue tracker, etc.) that references the porting log. This keeps research synchronized with actionable tasks and highlights where user decisions are required.
- Python is a recommended coordination language for the project: it is broadly readable, has rich tooling for notebooks/scripts to prototype replacements, and can automate reporting or documentation updates tied to the porting log.

## Analysis Practices
- Inferring intent from usage is viable: trace where routines are entered and follow downstream calls/side effects (e.g., the BASIC `stack` routine leading into `gotoc00b`) to deduce purpose without external documentation.

