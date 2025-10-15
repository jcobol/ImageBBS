# Iteration 05 – BASIC Variable Directory and `gotocd4f` Callers

## Goals
- Decode the 40-entry token table at `lbl_c2e5` so each bootstrap variable can be named explicitly in modern ports.
- Catalogue every routine that tail-calls `gotocd4f` to understand how Image relies on the BASIC ROM variable lookup helper outside of the bootstrap loop.

## Findings

### `lbl_c2e5` Enumerates the BASIC Variables Seeded During Bootstrap
`sub_c2d4` multiplies the variable index in `X` by two, pulls a pair of bytes from `lbl_c2e5`, writes them into the `varnam` workspace, and then tail-calls `gotocd4f` so BASIC's `ptrget1` routine can locate the variable descriptor.【F:v1.2/source/ml-1_2-y2k.asm†L5109-L5139】`sub_c335` walks that table from entry `$27` down to `$00`, copying each descriptor pointer into `vartable` so the `setup` program sees a fully populated variable directory before it runs.【F:v1.2/source/ml-1_2-y2k.asm†L5141-L5155】

The bytes stored in `lbl_c2e5` are the tokenised variable names that `ptrget1` expects: the low byte is the first character, and the second byte is the final character with bit 7 set. Decoding each entry and cross-referencing the `im` BASIC listing reveals how those tokens map onto concrete globals used by the BBS. Table 1 lists every slot along with the forms observed in the `im` program (e.g., whether the BASIC code ever references the string or integer variant of a name).【F:v1.2/source/ml-1_2-y2k.asm†L5120-L5139】【F:v1.2/core/im.txt†L1-L112】【F:v1.2/core/im.txt†L158-212】 Duplicate bases such as `TR`, `A`, and `B` appear twice because the table seeds both the floating-point and integer incarnations that the BASIC overlays expect to find already present.

**Table 1 – Decoded entries in `lbl_c2e5`**

|Index|Token Bytes|Token|Observed `im` Forms|
|-----|-----------|-----|-------------------|
|0    |$41 $CE    |AN   |an, an$            |
|1    |$41 $80    |A    |a, a$, a%          |
|2    |$42 $80    |B    |b, b$, b%          |
|3    |$54 $D2    |TR   |tr, tr$, tr%       |
|4    |$44 $B1    |D1   |d1, d1$, d1%       |
|5    |$44 $B2    |D2   |d2, d2%            |
|6    |$44 $B3    |D3   |d3, d3%            |
|7    |$44 $B4    |D4   |d4, d4$            |
|8    |$44 $B5    |D5   |—                  |
|9    |$4C $C4    |LD   |ld, ld$            |
|10   |$54 $D4    |TT   |tt, tt$            |
|11   |$4E $C1    |NA   |na, na$, na%       |
|12   |$52 $CE    |RN   |rn, rn$            |
|13   |$50 $C8    |PH   |ph, ph$            |
|14   |$41 $CB    |AK   |—                  |
|15   |$4C $50    |LP   |lp                 |
|16   |$50 $4C    |PL   |pl                 |
|17   |$52 $43    |RC   |rc                 |
|18   |$53 $48    |SH   |sh                 |
|19   |$4D $57    |MW   |—                  |
|20   |$4E $4C    |NL   |nl                 |
|21   |$55 $4C    |UL   |ul                 |
|22   |$51 $45    |QE   |qe                 |
|23   |$52 $51    |RQ   |rq                 |
|24   |$C1 $C3    |AC   |ac, ac%            |
|25   |$45 $46    |EF   |ef                 |
|26   |$4C $46    |LF   |lf                 |
|27   |$57 $80    |W    |w, w$              |
|28   |$50 $80    |P    |p, p$              |
|29   |$D4 $D2    |TR   |tr, tr$, tr%       |
|30   |$C1 $80    |A    |a, a$, a%          |
|31   |$C2 $80    |B    |b, b$, b%          |
|32   |$C4 $D6    |DV   |dv, dv%            |
|33   |$44 $D2    |DR   |dr, dr$, dr%       |
|34   |$43 $B1    |C1   |—                  |
|35   |$43 $B2    |C2   |—                  |
|36   |$43 $CF    |CO   |co, co$, co%       |
|37   |$43 $C8    |CH   |ch                 |
|38   |$CB $D0    |KP   |—                  |
|39   |$43 $B3    |C3   |—                  |

Variables without an observed form (e.g., `D5`, `AK`, `MW`, the `C1`–`C3` trio, and `KP`) likely belong to overlays such as `setup` and `ml.extra`, which are not yet in the repository. Those should remain on the watch list when new PRGs are recovered.

### Other `gotocd4f` Tail-Callers
Beyond the bootstrap loop, Image centralises BASIC variable lookups through `sub_b560`, a helper that stores the caller-provided two-character token in `varnam` and then jumps straight into `gotocd4f` to execute `ptrget1` under the BASIC ROM bank.【F:v1.2/source/ml-1_2-y2k.asm†L3546-L3549】 Two higher-level routines use that shim:

- `sub_b597` (reached through `sub_a361`) consumes a table of MCI variable tokens, invokes `sub_b560` to resolve the descriptor, and copies the five-byte floating accumulator image into `fac1` so formatted output can read the value. This path underpins commands such as `&[`, `&,45`, and the MCI dispatcher itself.【F:v1.2/source/ml-1_2-y2k.asm†L913-L944】【F:v1.2/source/ml-1_2-y2k.asm†L3581-L3590】
- `putvar` uses `sub_b552` to fetch a descriptor pointer from `vartable`, falls through to `sub_b560` when the caller supplies an explicit token, and then writes the accumulator contents back into BASIC storage via the resolved descriptor. It mirrors the read path that `sub_b597` implements.【F:v1.2/source/ml-1_2-y2k.asm†L3592-L3604】

This shared helper means every machine-language feature that touches BASIC variables (MCI rendering, editor logic, disk overlays) depends on `ptrget1` being reachable via `gotocd4f`. Any port must therefore provide a ROM-equivalent lookup that can consume the two-byte tokens enumerated above and return descriptors compatible with the rest of the runtime.

## Follow-Ups
- Track down the overlays (`setup`, `ml.extra`, etc.) to confirm how the currently unobserved variables (`D5`, `AK`, `MW`, `C1`–`C3`, `KP`) are initialised and used.
- [x] Document how `putvar` and `sub_b552` are invoked from the BASIC side so the write path can be emulated alongside the read helpers already analysed. *(See iteration 06.)*
