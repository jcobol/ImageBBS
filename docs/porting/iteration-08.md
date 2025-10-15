# Iteration 08 – Host Abstractions and BASIC Control-Flow Plan

## Goals
- Outline a host-platform abstraction layer for disk, console, and modem I/O that matches the behaviours observed in the Image 1.2 sources.
- Propose a modern representation for the `im` BASIC program's control flow so its subsystems can be ported incrementally.

## Commodore I/O Touchpoints the Port Must Cover
- The BASIC shell assumes direct access to Commodore DOS channels: it opens the command channel on device 15, routes file data through channels 2, 5, and 6, and emits raw disk commands (e.g., `PRINT#15,"S"` and `OPEN6...,"S,W"`) whenever it stages overlays or manipulates sysop assets.【F:v1.2/core/im.txt†L2-L24】【F:v1.2/core/im.txt†L50-L89】【F:v1.2/core/im.txt†L104-L108】
- Machine-language bootstrap code orchestrates staged loads via Kernal vectors, repeatedly calling `SETLFS`, `SETNAM`, and `LOAD` to bring in `screen 1.2`, `im`, `ml.extra`, and `ml.editor` before jumping into the main interpreter loop.【F:v1.2/source/ml-1_2-y2k.asm†L4743-L4854】【F:v1.2/source/ml-1_2-y2k.asm†L4896-L4934】
- Startup routines immediately patch output, IRQ, and loader vectors while zeroing custom RS-232 buffers, confirming the port must virtualise the C64's serial driver lifecycle (buffer resets, IRQ chaining, and vector restoration).【F:v1.2/source/ml-1_2-y2k.asm†L4811-L4840】【F:v1.2/source/ml-1_2-y2k.asm†L5012-L5093】

## Proposed Host Abstraction Layout
1. **Device Context** – Model Commodore device numbers as logical endpoints (`DiskDrive`, `Printer`, `Console`, `Modem`), each exposing async byte streams and a command channel. A dispatcher mirrors the `SETLFS` triple `(device, file#, secondary)` so BASIC-equivalent code can swap between disk files and modem output without rewriting call sites.
2. **DOS Command API** – Provide helpers that translate Image's raw strings (`"S"`, `"LG"`, directory reads) into host-level operations. The helper should also capture status/error words so routines like `GOSUB1012` can present the same formatted status strings observed in the BASIC UI.
3. **Overlay Loader** – Implement a loader facade that mimics the bootstrap's staged `LOAD` calls and bank swaps. On modern hosts this can be a module registry that resolves logical names (`screen`, `ml.extra`, etc.) to resource blobs while toggling any required interpreter state between loads.
4. **Serial/Modem Facade** – Wrap modem I/O in a ring-buffer service that supports the clear/initialise sequences performed in `gotoc00b` and `sub_c240`, exposing hooks for ISR-style receive/transmit loops as well as polling semantics used by the BASIC `&` handlers.
5. **Console Renderer** – Provide a PETSCII-aware output surface that honours the color and cursor control writes during startup (e.g., border/background pokes) and exposes convenience methods for status line refresh routines such as `GOSUB1378`.

This decomposition keeps the original device numbers and command strings intact while isolating host-specific code in well-defined adapters.

## Control-Flow Observations from `im`
- The program leans on a small set of dispatcher entry points: `GOSUB1010/1011` prepare device state, `GOSUB1009` refreshes drive selections, and `GOSUB1200/1202` seed UI prompts before branching via `ON...GOTO` tables.【F:v1.2/core/im.txt†L2-L24】【F:v1.2/core/im.txt†L90-L118】
- Command handlers are largely data-driven: many routines stash context in global arrays, then call ampersand (`&`) machine-language hooks like `&,52,13,3` or `&,8,2,1` to perform terminal or modem work before looping back to shared editor logic.【F:v1.2/core/im.txt†L63-L89】【F:v1.2/core/im.txt†L120-L183】

## Proposed Representation Strategy for the Port
1. **Module Map** – Partition the program by its major dispatcher families (disk utilities, message editor, user management). Each module exposes a `run(context)` method that returns the next menu state, mimicking the BASIC `ON...GOTO` patterns.
2. **State Machine Kernel** – Replace the implicit BASIC line-number fall-through with an explicit state machine that tracks the current menu, pending overlay loads, and active user session. Transitions are triggered by the same conditions the BASIC code tests (status flags, `an$` input, system timers), but encoded as readable enums.
3. **Shared Service Layer** – Route all ampersand calls through a service registry keyed by the same numeric opcodes. This keeps the dispatcher table from `ml-1_2-y2k.asm` authoritative while allowing each service to be implemented in the host language.
4. **Testing Harness** – Instrument the state machine with trace logging that mirrors BASIC's GOSUB entry points. Feeding the harness with captured BASIC transcripts will let us assert behavioural parity and catch deviations as we reimplement each module.

## Follow-Ups
- Prototype the device-context dispatcher so the DOS command helper can be validated against real disk directory listings and overlay loads.
- Build an initial state-machine skeleton for one subsystem (e.g., the message editor) to confirm the GOSUB-to-module mapping is viable before scaling across the entire program.
- Continue searching for the missing overlays to verify the planned service registry covers any additional ampersand handlers or variables staged by those modules.
