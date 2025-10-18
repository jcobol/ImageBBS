# Iteration 37 – Screen buffer access audit

## Goals
- [x] Catalogue machine-language overlay routines that write directly to the C64 screen or colour RAM regions.
- [x] Distinguish routines that rely on Kernal/ampersand screen services so the host console can mirror their behaviour.

## Findings
### Direct screen RAM updates
- The pause/abort indicator handler around `gotoa722` and `skipa739` writes PETSCII control codes straight into the status line at `$0400+$1e-$20`, bypassing Kernal output.【F:v1.2/source/ml-1_2-y2k.asm†L1500-L1526】
- Idle timer digits are refreshed by `sub_a91f`, which stamps three PETSCII digits into `$0400+$de-$e1` whenever the sysop display is active.【F:v1.2/source/ml-1_2-y2k.asm†L1820-L1838】
- `sub_b0c3`/`loopb0e8` swap the chat transcript and lightbar buffers with on-screen memory using indexed `STA` loops that stream across `$0400+$28-$f7` and `$0798-$07e7`, meaning the host must support block copies against the live screen matrix.【F:v1.2/source/ml-1_2-y2k.asm†L2891-L2935】
- Spinner and carrier indicators are manipulated in-place: `skipb195`/`skipb19e`/`skipb1ae` twiddle the byte at `$0400+$9c`, while `skipb1ef` and `skipb202` push raw values into `$0400+$27` and the very first screen cell at `$0400` respectively.【F:v1.2/source/ml-1_2-y2k.asm†L3015-L3076】
- `sub_b410` seeds the pause/abort columns by writing `$a0` directly into `$0400+$1e-$20` after clearing colour RAM, and `sub_b66c` flashes the garbage-collection “G” marker in `$0400+$1f` during memory compaction.【F:v1.2/source/ml-1_2-y2k.asm†L3330-L3351】【F:v1.2/source/ml-1_2-y2k.asm†L3710-L3733】
- The key buffer presenter (`sub_ad62`) sprays key glyphs into the masked sysop pane at `$0518+$00-?`, and status-line maintenance (`loopb94e`) mirrors buffer snapshots back into `$0770+$00-?$`, both through indexed stores that expect byte-addressable screen RAM semantics.【F:v1.2/source/ml-1_2-y2k.asm†L2448-L2455】【F:v1.2/source/ml-1_2-y2k.asm†L4088-L4108】

### Colour RAM writes
- `loopad37` and `sub_ad62` push colour attributes into `$d800+$118` and `$d800+$118` windows tied to the sysop status panes, using both decrementing and indexed loops.【F:v1.2/source/ml-1_2-y2k.asm†L2415-L2455】
- Buffer swapper `loopb0e8` rotates saved colours through `$d800+$398` to restore the bottom mask, while `loopb94e` streams highlight colours back into `$d800+$370`.【F:v1.2/source/ml-1_2-y2k.asm†L2891-L2933】【F:v1.2/source/ml-1_2-y2k.asm†L4088-L4108】
- `sub_b410` clears the top-line palette by iterating `STA colormem,x`, writing `$06` across `$d800-$d827`.【F:v1.2/source/ml-1_2-y2k.asm†L3330-L3351】

### Kernal/ampersand mediated output
- `outscn` still depends on Kernal `OUT_SCRN` ($E716) when printing general PETSCII output, so text sent through ampersand `&,50` flows through the ROM routine instead of the raw screen buffer.【F:v1.2/source/ml-1_2-y2k.asm†L3882-L3945】【F:v1.2/source/ml-1_2-y2k.asm†L400-L406】
- `sub_b975` invokes ROM helpers (`var_e9f0`, `$ea24`) and then uses the `pnt` cursor pointer with `STA (pnt),Y` to fill the active row, showing that some routines still rely on the Kernal cursor APIs rather than absolute screen offsets.【F:v1.2/source/ml-1_2-y2k.asm†L4088-L4118】
- No `STA`/`STX` references to `$0400-$07e7` or `$d800-$dbff` appear in the SwiftLink or `ml.extra` overlays, confirming the direct screen mutations are confined to `ml-1_2-y2k.asm`.【700bd4†L1-L2】【6eba03†L1-L2】

## Implications
- The host console must expose both character and colour buffers that permit random access and block copies, because the overlay swaps multi-byte regions and tweaks individual cells without going through Kernal vectors.【F:v1.2/source/ml-1_2-y2k.asm†L2891-L2935】【F:v1.2/source/ml-1_2-y2k.asm†L3015-L3076】【F:v1.2/source/ml-1_2-y2k.asm†L3330-L3351】
- Kernal-compatible pathways are still required for ampersand routines that call `outscn` or use the ROM cursor pointer, so the port should emulate both the direct-memory API and higher-level screen I/O services.【F:v1.2/source/ml-1_2-y2k.asm†L3882-L3945】【F:v1.2/source/ml-1_2-y2k.asm†L4088-L4118】
