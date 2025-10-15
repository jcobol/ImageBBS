# Iteration 07 – Ampersand Argument Evaluation and IGONE Loop

## Goals
- Document how the ampersand dispatcher reuses BASIC ROM helpers to parse the byte arguments that flow into `sub_cd00`.
- Capture the patched `IGONE` handler so a port can mirror how Image chains through multiple `&` tokens on the same BASIC line.

## Findings

### `sub_cc02` Wraps `CHRGOT`/`GETBYT` to Produce Byte Arguments
`sub_cc02` peeks at the current character with `chrgot`, clears `X`, and only proceeds when it sees a comma separator, matching the way Image writes its ampersand calls with leading commas (for example, `&,52,13,3`).【F:v1.2/source/ml-1_2-y2k.asm†L5557-L5562】【F:v1.2/core/im.txt†L60-L78】When the delimiter is present it jumps into the ROM `GETBYT` entry (`lbl_b79a+1`), which evaluates the following numeric expression, clamps it to one byte, and leaves the value in both `A` and `X` while advancing `txtptr` past the argument.【F:v1.2/source/ml-1_2-y2k.asm†L5557-L5562】【F:v1.2/source/ml-1_2-y2k.asm†L3874-L3880】Each successful parse is cached in `sareg`, `sxreg`, and `syreg` by `sub_cc0f` so the dispatcher can reload them as `A`, `X`, and `Y` before jumping into the selected machine-language routine.【F:v1.2/source/ml-1_2-y2k.asm†L5564-L5573】Any port that mirrors the ampersand API therefore needs a `GETBYT` analogue that honours BASIC’s expression syntax, whitespace rules, and 0–255 saturation before storing the final register values.

### The Patched `IGONE` Vector Iterates Through Ampersand Tokens
Image replaces BASIC’s `IGONE` vector with a loop that banks out the ROM, calls `chrget` until it encounters an ampersand, and then hands control to `sub_cd00` for each `&` it finds.【F:v1.2/source/ml-1_2-y2k.asm†L5727-L5739】After every dispatcher call it invokes `chrgot` to prime the next character and rewinds `txtptr` when the scan ends so the interpreter can resume normal token processing from the correct position.【F:v1.2/source/ml-1_2-y2k.asm†L5738-L5746】This design lets overlays embed several ampersand calls inside a single BASIC statement without losing the interpreter’s place, something a host implementation must respect when it hooks its own control-flow manager into the BASIC port.

## Implications for the Port
- Provide a byte-oriented expression parser that matches `GETBYT` semantics so ampersand callers receive the same register values the 6502 helpers expect.【F:v1.2/source/ml-1_2-y2k.asm†L5557-L5573】【F:v1.2/source/ml-1_2-y2k.asm†L3874-L3880】
- Preserve the interpreter scan loop around `IGONE` so multiple ampersand invocations on one BASIC line continue to work once the overlays are ported.【F:v1.2/source/ml-1_2-y2k.asm†L5727-L5746】

## Follow-Ups
- Verify, once the missing overlays are recovered, whether any ampersand callers depend on `GETBYT` edge cases (hex literals, unary operators, or overflow wrap-around) that the port’s expression parser must reproduce.【F:v1.2/source/ml-1_2-y2k.asm†L5557-L5562】
- Investigate how overlays pass string data through the ampersand interface so the modern dispatcher can extend beyond the byte-oriented path documented here.【F:v1.2/source/ml-1_2-y2k.asm†L5557-L5573】
