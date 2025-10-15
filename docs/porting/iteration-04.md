# Iteration 04 – SwiftLink Buffer Geometry and Variable Bootstrap

## Goals
- Resolve the open questions from iteration 03 by characterising the SwiftLink input buffer size and wrap behaviour.
- Document how `sub_c2d4` and `gotocd4f` cooperate to seed BASIC variables during the Image BBS bootstrap sequence.

## Findings

### SwiftLink Circular Buffer Behaviour
- The non-maskable interrupt handler `newnmi` copies any received byte from the SwiftLink ACIA into `$cb00,Y`, where `Y` is loaded from the tail pointer at `$029b` (`ridbe`). After incrementing `Y`, the routine uses `BPL` to detect when bit 7 is set and, if so, resets `Y` to `$00` before storing it back to `$029b`. This confines the tail pointer to the range `$00-$7f`, establishing a 128-byte receive buffer at `$cb00-$cb7f` that wraps cleanly at the halfway point of the page.【F:v1.2/source/ml.rs232-192k.asm†L123-L166】
- The `@rsget` routine applies the same logic to the head pointer at `$029c` (`ridbs`): when the consumer increments beyond `$7f`, it clears the pointer back to `$00` before writing it to `$029c`. The equality check against `$029b` therefore continues to work across wraps without extra bookkeeping, confirming a classic single-producer/single-consumer ring buffer sized to 128 bytes.【F:v1.2/source/ml.rs232-192k.asm†L229-L249】

### Variable Table Bootstrap Helpers
- `sub_c2d4` expects the BASIC variable index in `X`. It doubles the index to step through `lbl_c2e5`, a table of little-endian pointers to variable name tokens that live in Image’s BASIC memory. The routine copies the selected pointer into `varnam` and then tail-calls `gotocd4f` to delegate variable lookup to the ROM.【F:v1.2/source/ml-1_2-y2k.asm†L5109-L5139】
- `gotocd4f` temporarily pages in the BASIC ROM by storing `$37` into the 6510 I/O port, calls `ptrget1` (the standard interpreter helper that resolves `varnam` into a variable descriptor), and finally restores the previous memory configuration from the stack. Because `ptrget1` leaves the descriptor address in `varpnt`, the surrounding loop in `sub_c335` can copy those addresses into `vartable`, recreating BASIC’s variable directory exactly as Image expects before handing control back to BASIC.【F:v1.2/source/ml-1_2-y2k.asm†L5141-L5155】【F:v1.2/source/ml-1_2-y2k.asm†L5685-L5707】

## Implications for the Port
- Host implementations need to allocate at least 128 bytes for the modem receive queue and preserve the modulo-128 pointer semantics so that head/tail comparisons match the original code’s wrap logic.
- Any reimplementation of the bootstrap should reproduce the `sub_c2d4`/`gotocd4f` workflow: pre-load the same variable names, invoke a BASIC-like symbol table lookup that populates the equivalent of `varpnt`, and emit the resulting pointers into the variable table structure before executing the remainder of the BASIC program.

## Follow-Ups
- [x] Identify the full list of variable names referenced by `lbl_c2e5` so the modern port can name the bootstrap-era globals explicitly. *(See iteration 05.)*
- [x] Audit remaining routines that tail-call `gotocd4f` (e.g., `sub_b560`) to catalogue other code paths that rely on the same ROM-mediated lookup. *(See iteration 05.)*
