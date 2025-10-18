# Iteration 38 – Direct screen write integration map

## Goals
- [x] Expand the iteration 37 audit with concrete address ranges, update patterns, and semantics for every direct screen or colour RAM write in the machine-language overlay.
- [x] Derive host integration requirements so each routine's expectations map onto an explicit API surface.

## Findings

### Direct screen and colour RAM writes
| Routine(s) | Screen RAM writes | Colour RAM writes | Update pattern | Observed semantics |
| --- | --- | --- | --- | --- |
| `gotoa722` / `skipa739` | `$041e-$0420` via `videoram+30/32` status cells | — | Single-cell `STA` updates that fire whenever abort/pause control codes are detected | Toggles the sysop pause (`P`) and abort (`A`) indicators without going through Kernal output.【F:v1.2/source/ml-1_2-y2k.asm†L1504-L1524】 |
| `sub_a91f` | `$04de-$04e1` via `videoram+222/224/225` | — | Three sequential `STA` writes push PETSCII digits when the sysop display is active | Refreshes the idle timer seconds/minutes readout in place on the status line.【F:v1.2/source/ml-1_2-y2k.asm†L1820-L1837】 |
| `sub_b0c3` | `$0428-$0517` swapped with buffer `$4100-$41EF` | `$d828-$d917` swapped with `tempcol` | 240-byte indexed swap that mirrors the chat/lightbar region between on-screen memory and an off-screen buffer | Exchanges the active chat transcript with the saved overlay when toggling split/full screen modes.【F:v1.2/source/ml-1_2-y2k.asm†L2880-L2916】 |
| `loopb0e8` | — | `$db98-$dbE7` swapped with `$4050-$409F` | 80-byte indexed swap restoring highlight colours under the bottom mask | Keeps colour attributes for the bottom overlay in sync with the saved copy during screen mode switches.【F:v1.2/source/ml-1_2-y2k.asm†L2917-L2936】 |
| `skipb195` / `skipb19e` / `skipb1ae` | `$049c` via `videoram+156` | — | Byte-level increment/decrement with boundary checks | Animates the spinner glyph in the sysop status bar by mutating a single cell directly.【F:v1.2/source/ml-1_2-y2k.asm†L3189-L3216】 |
| `skipb1ef` / `skipb202` | `$0400`, `$0427` via `videoram` / `videoram+39` | — | Single-byte `STX` writes conditioned on modem state | Lights the carrier indicator and leading status cell without invoking ROM routines.【F:v1.2/source/ml-1_2-y2k.asm†L3217-L3232】 |
| `sub_b410` | `$041e-$0420` via `videoram+30-32` | `$d800-$d827` via `colormem,x` | 40-byte colour fill plus three cell writes | Seeds the pause/abort/status columns and resets their palette after mode changes.【F:v1.2/source/ml-1_2-y2k.asm†L3342-L3351】 |
| `sub_b66c` | `$041f` via `videoram+31` | — | Single-cell `STA` paired with timed clear | Flashes a capital `G` while the garbage collector compacts strings, then restores a blank.【F:v1.2/source/ml-1_2-y2k.asm†L3710-L3723】 |
| `loopad37` | — | `$dbcc-$dbdb` via `colorram+972,x` | 16-byte descending colour fill | Repaints the sysop pane colour strip based on the current chat buffer selection.【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2427】 |
| `sub_ad62` | `$0518+Y` via `var_0518,y` | `$d918+Y` via `colorram+280,y` | Indexed writes over a variable span anchored by `Y` | Draws the buffered keystroke and its colour into the masked sysop pane overlay.【F:v1.2/source/ml-1_2-y2k.asm†L2444-L2454】 |
| `loopb94e` | `$0770-$0797` via `var_0770,y` | `$db70-$db97` via `colorram+880,y` | Reverse copy that restores 40 characters plus colours | Restores the saved bottom status overlay (mask and highlight colours) after buffer manipulation.【F:v1.2/source/ml-1_2-y2k.asm†L4094-L4124】 |

## Host integration action items
- **Expose status-line cell pokes** — Provide an API that lets the host set raw PETSCII and colour values for `$0400-$0420` so routines such as `gotoa722`, `skipa739`, `sub_b410`, and `sub_b66c` can flip indicators without repainting the whole line.【F:v1.2/source/ml-1_2-y2k.asm†L1504-L1524】【F:v1.2/source/ml-1_2-y2k.asm†L3342-L3351】【F:v1.2/source/ml-1_2-y2k.asm†L3710-L3723】
- **Support block swaps for chat/lightbar regions** — Implement host-side helpers that atomically swap 240-byte screen regions and 80-byte colour spans so `sub_b0c3` and `loopb0e8` can exchange overlays as written.【F:v1.2/source/ml-1_2-y2k.asm†L2880-L2936】
- **Allow targeted numeric overlays** — Surface a method that rewrites three contiguous cells for timers/metrics to accommodate `sub_a91f`’s idle counter updates on `$04de-$04e1`.【F:v1.2/source/ml-1_2-y2k.asm†L1820-L1837】
- **Expose spinner/carrier toggles** — Map single-byte writes at `$0400`, `$0427`, and `$049c` to dedicated host indicators so `skipb195`, `skipb1ae`, `skipb1ef`, and `skipb202` can drive status animations.【F:v1.2/source/ml-1_2-y2k.asm†L3189-L3232】
- **Mirror sysop pane overlays** — Add APIs that copy arbitrary spans into the masked sysop pane and its colour RAM so `loopad37`, `sub_ad62`, and `loopb94e` can draw overlays and restore highlights when the host mask is active.【F:v1.2/source/ml-1_2-y2k.asm†L2404-L2454】【F:v1.2/source/ml-1_2-y2k.asm†L4094-L4124】
