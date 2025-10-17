# Commodore 64 KERNAL Reference Notes

These notes capture planning-relevant details surfaced from
`docs/analysis/commodore64_reference_tj_tokens.jsonl`. Use the accompanying helper
script to gather additional context as questions arise.

## Query helper

Run the keyword searcher to pull passages from the JSONL dataset:

```
scripts/analysis/reference_search.py \
  docs/analysis/commodore64_reference_tj_tokens.jsonl \
  KERNAL "RS-232"
```

Provide as many keywords as needed; only passages containing all of them will be
reported, wrapped to the configured column width.

## Operating system structure

* The Commodore 64 ROM combines three cooperating modules: the BASIC interpreter,
  the KERNAL, and the screen editor. The KERNAL owns most interrupt-level
  processing and all low-level input/output while the screen editor manages video
  output and intercepts keyboard input for editing workflows.
* KERNAL vectors on page three of memory can be repointed to user routines, but
  IRQ replacements must still chain to the standard handler (ending with `RTI`)
  to keep CIA-driven services stable.

## Storage and BASIC integration

* Tape `SAVE` supports optional secondary addresses. Setting the secondary
  address to `1` reloads programs over the current memory image; `2` appends an
  end-of-tape marker; `3` combines both behaviours.
* The `STATUS` function (and `ST` variable) reports error bits for cassette,
  serial, tape-verify, disk, and RS-232 operations, enabling BASIC code to branch
  on EOF, checksum, or timeout conditions.

## Input hardware interactions

* The KERNAL scans the 8×8 keyboard matrix through CIA #1 registers at `$DC00`
  (columns) and `$DC01` (rows), depositing the resulting character code in
  location `197` and processing any buffered keystrokes queued via addresses
  `631–640` with a count stored at `198`.
* Light-pen input latches VIC-II positions into registers `$13` (X) and `$14`
  (Y), with RS-232 processing delivered by CIA #2 NMIs that run concurrently with
  foreground BASIC programs when buffers are available.

## Display memory pointers

* Screen memory can be relocated in 1 KB steps; after moving it you must update
  the screen-editor page pointer with `POKE 648, address/256`. Colour RAM remains
  fixed at `$D800–$DBE7` regardless of the chosen screen bank.

## Memory map and vectors

* The simplified memory map reserves `$0000–$03FF` for system use, places screen
  memory at `$0400–$07F7`, BASIC at `$A000–$BFFF`, and the KERNAL ROM at
  `$E000–$FFFF`, bracketing the I/O and SID ranges relevant to Image BBS.
* Zero-page locations `$0281–$0299` cover several crucial KERNAL variables,
  including the keyboard buffer size, repeat counters, and RS-232 register
  mirrors (`RSSTAT` at `$0297` and `BITNUM` at `$0298`).

## KERNAL entry points

* Common output routines appear at their usual ROM vectors: `CHKOUT ($FFC9)` and
  `CHROUT ($FFD2)` for character printing, plus `CHKIN ($FFC6)`, `CHRIN ($FFCF)`
  and `GETIN ($FFE4)` for buffered reads. `OPEN ($FFCO)` automatically allocates
  the RS-232 FIFO buffers and performs a BASIC `CLR`, so invoke it before
  creating variables.

## RS-232 workflow specifics

* The RS-232 interface allocates paired 256-byte FIFO buffers when opened. A
  second `OPEN` resets buffer pointers, dropping queued data, and `CLOSE`
  releases the memory.
* RS-232 transfers rely on the `ST`/`RSSTAT` status word: bit values report
  parity, framing, buffer overflow, break, and EOF conditions. Assign `ST` to a
  temporary variable before invoking routines that clear it.
* Zero-page locations `$00A7–$00B6` track bit-level RS-232 state, while `$00F7`
  and `$00F9` store the receiver/transmitter buffer base pointers that `OPEN`
  initialises and `CLOSE` clears.
* Use `CHKOUT` for RS-232 handshaking; the routine implements CTS-based flow
  control and raises RTS/TxD appropriately when the channel closes.

These reminders help close knowledge gaps when planning host abstractions or
porting tasks that lean on ROM services.
