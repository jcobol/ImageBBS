# Iteration 23 – Mapping the `ml.extra` lightbar tables

## Goals
- Follow the machine-language overlay’s routines that walk the `$c200` data to learn how each entry is structured before extracting real tables.
- Confirm how those records feed the page-one and page-two bitmaps in `$ce77/$ce27` so the decoded data can replace the stub defaults.
- Locate the directory that hands flag descriptors back to BASIC so later work can swap in the authentic strings.

## `loc_1866` scans `$c200` in variable-length records
The dispatcher zeroes `$64/$65` and points them at `$c200` before iterating through the table with a mix of header and mask tests.【F:docs/porting/iteration-23.md†L10-L28】 The header byte’s top bit gates the entry through the `$c0dd/$c0dc` masks (bits 0–1 drive the `$c0dd` comparison, a zero in those bits falls back to the `$c0dc` mask stored at offset `$02`). Bit 3 distinguishes two record layouts: the loop adds either `$08` or `$20` to `$64/$65` when it skips an entry, so the short form is eight bytes long while the long form spans thirty-two bytes.【F:docs/porting/iteration-23.md†L29-L44】 Reaching the `$c8xx` end marker resets the pointer and returns through `$c1cd`, establishing where the real table terminates.【F:docs/porting/iteration-23.md†L45-L53】

```text
                lda #$00
                sta $64
                lda #$c2
                sta $65
loc_1866:
                lda ($64),y
                bpl loc_18b4
                and #$03
                beq loc_1873
                and $c0dd
                beq loc_18b4
loc_1873:
                ldy #$01
                lda ($64),y
                and $c0db
                bne loc_1885
                ldy #$02
                lda ($64),y
                and $c0dc
                beq loc_18b4
loc_1885:
                ldy #$00
                lda ($64),y
                pha
                and #$08
                bne loc_1894
                jsr $c0de
                jmp $c097
```

## `loc_18e2` applies bitmap payloads
Once `$64/$65` reference a matching record, the helper at `loc_18e2` revalidates the candidate by comparing the bytes starting at offset `$03` against the active page-one bitmap in `$ce77` (up to seven bytes, terminated by `$00`).【F:docs/porting/iteration-23.md†L55-L69】 When the existing state matches, the routine copies the fourteen-byte payload beginning at offset `$0a` into `$ce77`, updating `$d00f` to reflect the number of bytes staged and calling `$c1cd` so the runtime mirror stays in sync.【F:docs/porting/iteration-23.md†L70-L83】 A second pass lifts eight bytes from offset `$18` into `$ce27` for the page-two flags and then forwards the trailing byte at offset `$1f` to `$c1cd`, implying that the final slot in each record identifies which host-side pointer or string needs to be refreshed after the bitmap swap.【F:docs/porting/iteration-23.md†L84-L102】

```text
loc_18e2:
                lda ($64),y
                beq loc_18f1
                cmp $ce77,x
                bne loc_18f6
                iny
                inx
                cpx #$07
                bne loc_18e2
loc_18f8:
                ldy #$18
                lda ($64),y
                beq loc_18fe
loc_18fe:
                ldy #$0a
                ldx #$00
loc_1902:
                lda ($64),y
                beq loc_190f
                sta $ce77,x
                iny
                inx
                cpx #$0e
                bcc loc_1902
```

## `loc_1964` handles short updates
Entries flagged with bit 2 (`and #$04`) only expect the left-column seed to change. That path re-checks offsets `$03/$04` against `$ce77/$ce78`, rewrites the two bytes at offsets `$05/$06`, and refreshes the host mirror with the pointer stored at offset `$07`.【F:docs/porting/iteration-23.md†L104-L123】 This confirms that even the compact eight-byte records follow the same layout: header, two-byte mask, two-byte comparison value, two-byte replacement value, and a one-byte directory reference.

```text
loc_1964:
                lda $d00f
                cmp #$02
                bne loc_197d
loc_196b:
                ldy #$03
                lda ($64),y
                cmp $ce77
                bne loc_197d
                ldy #$04
                lda ($64),y
                cmp $ce78
                beq loc_197f
loc_197f:
                ldy #$05
                lda ($64),y
                sta $ce77
                ldy #$06
                lda ($64),y
                sta $ce78
```

## `$d9c3` flag records resolve the version-banner payloads
The 0x46-byte block following `loc_29b7` is copied into `$c1c3` and XORed before the dispatcher walks it. `_FLAG_TABLE_ADDR` in `ml_extra_defaults.py` decodes that payload into one short-form record, one long-form record, and the trailing PETSCII banner string used by the pointer callback.【F:scripts/prototypes/ml_extra_defaults.py†L19-L298】 The recovered entries line up with the code flow documented above:

* Header `$8b` is a short-form record: it matches the `"08"` seed in the left/right bitmaps, replaces those bytes with `"IM"`, and jumps through pointer `$c1` to refresh the host directory.【F:scripts/prototypes/ml_extra_defaults.py†L91-L158】
* Header `$c7` is a long-form record. It checks for `"BBS V1."` in the left-column history, writes `"2 S{$$23} {$$5c}{$$24}A{$$5c}{$$23}4{$$5c}{$$25}B"` into `$ce77`, seeds `$ce27` with `"{$$8b}{$$5c}{$$5f}04{$$28}C{$$29}"`, and advances the pointer directory with `$29`.【F:scripts/prototypes/ml_extra_defaults.py†L241-L298】
* The remaining bytes decode to `"1989 NEW IMAGE SOFTWARE, INC.{$$8b}"`, confirming that the banner text for the long-form update lives adjacent to the flag table.【F:scripts/prototypes/ml_extra_defaults.py†L241-L298】【F:scripts/prototypes/ml_extra_sanity.py†L120-L155】

## Flag descriptor directory at `$c115`
The overlay routine beginning at `loc_20ea` takes the flag index in `$fe`, walks a 14-entry list stored at `$c115`, and on a match uses the pointer tables at `$c123/$c124` to seed `$c151/$c152` with the correct PETSCII string address before jumping through the host vector.【F:docs/porting/iteration-23.md†L125-L147】 The data immediately following the `jmp $c0c1` call shows the hard-coded slot order (`04, 09, 0d, 14, 15, 16, 17, 18, 19, 0e, 0f, 02`) and the paired pointers that trace into the overlay’s `$c1xx/$c2xx` string table, establishing the map the extraction script will need to replicate.【F:docs/porting/iteration-23.md†L148-L165】

```text
loc_20ea:
                cmp $c115,x
                beq loc_213d
                dex
                bne loc_20ea
                jsr $c368
                bcc loc_20c1
                jmp $c0c1
                .byte $04,$09,$0d,$14,$15,$16,$17,$18,$19,$0e,$0f,$02
                .byte $53,$c1,$71,$c1,$93,$c1,$ab,$c1,$e6,$c1,$f4,$c1
                .byte $0d,$c2,$25,$c2,$30,$c2,$4a,$c2,$61,$c2,$9d,$c2
                .byte $b0,$c2,$ca
```

## Hardware defaults around `loc_2a14`
The initialisation path pulses the underline register and restores the editor palette before returning to the caller. `loc_2a14` raises `$d404` to `$10` momentarily before clearing it, while `loc_2a3f` seeds `$d403` with `$08`, resets `$d404`, and spins a short delay loop so the VIC-II state settles.【F:v1.2/source/ml_extra.asm†L4623-L4665】 The follow-on routine primes `$42fe/$42ff` with `$00/$2c`, walks that pointer up to `$44`, then rewinds to `$2c` so the underline sweep ends with the original offset in place.【F:v1.2/source/ml_extra.asm†L4666-L4699】 The setup block finishes by loading `$0f` into `$d418`, leaving the colour helper at `$dac6/$dac9` to mirror whatever `$d405/$d406` payload the caller supplies for future updates.【F:v1.2/source/ml_extra.asm†L4701-L4706】

`MLExtraDefaults.hardware` now collects these writes so tooling can report the recovered underline and palette defaults without re-decoding the PRG, including the pointer scan bounds that gate the `$42ff` sweep.【F:scripts/prototypes/ml_extra_defaults.py†L185-L357】 The `ml_extra_sanity` summary prints the pointer start, scan limit, and each VIC/SID register touched during setup, making the recovered constants part of the standard regression report.【F:scripts/prototypes/ml_extra_sanity.py†L90-L175】

## Tooling report for the macro directory
`MLExtraDefaults` now exposes the slot metadata as `MacroDirectoryEntry` instances with a helper that renders the leading bytes of each payload, making it easier to cross-reference the pointer fan-out without dumping the entire binary.【F:src/imagebbs/ml_extra_defaults.py†L1-L12】 The `ml_extra_sanity` report consumes those entries and prints the runtime order, byte previews, and the best-effort PETSCII decode for each slot, confirming that the recovered overlay publishes twelve ampersand targets and that only the first four carry meaningful payloads (67-, 37-, 3-, and 9-byte routines respectively).【F:src/imagebbs/ml_extra_sanity.py†L1-L12】 Subsequent passes mirrored the file-transfer header, prompt, and error panes into slots `$28`–`$2A`, bringing the archived macro directory to fifteen entries while keeping the stubbed defaults aligned with the runtime shim.【F:src/imagebbs/ml_extra_defaults.py†L1-L12】【F:docs/porting/artifacts/ml-extra-macro-screens.json.gz.base64†L1-L1】 Running `python3 -m imagebbs.ml_extra_sanity --metadata-json docs/porting/artifacts/ml-extra-overlay-metadata.json` now produces the summary and refreshes the canonical metadata diff artefact for downstream automation.【23a911†L1-L111】【F:docs/porting/artifacts/ml-extra-overlay-metadata.json†L1-L197】

With the stub now populated by real bytes, `ml_extra_sanity` also parses `ml_extra_stub.asm` directly and diffs every slot’s length, pointer, and payload against the recovered overlay. Any mismatch is flagged in the report so the checked-in stub cannot diverge from the archival data without tripping the regression gate.【F:scripts/prototypes/ml_extra_sanity.py†L1-L234】

`MLExtraDefaults.flag_dispatch` now captures the descriptor list at `$d115` alongside the slot IDs and handler pointers at `$d116/$d123`, exposing a 12-entry map from ampersand flag index to macro routine with the leading `$c0`/`$2e` markers preserved for reference.【F:scripts/prototypes/ml_extra_defaults.py†L175-L220】【F:scripts/prototypes/ml_extra_defaults.py†L362-L396】 The sanity report prints those relationships verbatim so it’s easy to confirm that, for example, flag `$04` routes to slot `$04`/`$c153` while flag `$02` lands on slot `$02`/`$c29d` when reviewing regressions.【F:scripts/prototypes/ml_extra_sanity.py†L186-L314】

With those bytes decoded, `ml_extra_stub.asm` now embeds the archival lightbar,
palette, flag-directory, and macro payloads so the bootstrap exposes the same
constants as the recovered overlay without loading the full binary. The stub
keeps the runtime slot ordering, macro targets, and XOR-encoded tail intact so
tooling can diff against the source overlay during CI runs.【F:v1.2/source/ml_extra_stub.asm†L19-L136】【F:scripts/prototypes/ml_extra_sanity.py†L1-L234】

## Macro payload dump helper
`scripts/prototypes/ml_extra_dump_macros.py` exports the same pointer directory as structured PETSCII strings so transcription work can focus on the byte-for-byte payloads rather than the surrounding report formatting.【F:scripts/prototypes/ml_extra_dump_macros.py†L1-L103】 It accepts optional `--slot` filters (decimal, `$`-prefixed hex with quoting, or `0x` literals) and prints each selection with its runtime address, byte length, complete hex listing, and decoded PETSCII, allowing the long-form flag targets at `$c153/$c171/$c193/$c1ab` to be captured verbatim for later documentation.【8f7739†L1-L7】 The tool also supports `--json` for machine-readable dumps, which will simplify the later step that replaces the stubbed constants with the recovered overlay data.

Running `python -m imagebbs.ml_extra_dump_macros --slot '$04' --slot '$09' --slot '$0d' --slot '$14'` captures the archival bytes and PETSCII rendering for the four populated slots in the `$c1xx` table.【ec6373†L1-L9】 The decoded payloads align with the stubbed constants in `v1.2/source/ml_extra_stub.asm`, giving the transcription a stable anchor in source control for later audits.【F:v1.2/source/ml_extra_stub.asm†L73-L122】

### PETSCII transcription for slots `$04/$09/$0d/$14`
The dumps below quote both the raw byte streams and the helper’s PETSCII decode. Each entry links back to the archival offsets and the stub labels (`macro_payload_04`, `macro_payload_09`, `macro_payload_13`, and `macro_payload_20`) so the documentation stays tied to the mirror shipped in the bootstrap.

* **Slot `$04` @ `$c153`** (`macro_payload_04`)
  * Bytes: ``$c2 $9d $66 $c2 $bd $e6 $c2 $9d $e7 $c2 $bd $67 $c3 $9d $68 $c3 $ca $ec $e2 $c1 $d0 $e2 $a5 $03 $9d $e5 $c1 $a5 $04 $9d $66 $c2 $a5 $05 $9d $e7 $c2 $a5 $06 $9d $68 $c3 $ad $e1 $c1 $c9 $80 $f0 $03 $ee $e1 $c1 $60 $e8 $ec $e1 $c1 $90 $a2 $e0 $80 $90 $d7 $60 $60 $a2 $00``
  * PETSCII: ``B{$$9d}fB{$$9d}gB{$$9d}hCJlbAPb%{$$03}{$$9d}eA%{$$04}{$$9d}fB%{$$05}{$$9d}gB%{$$06}{$$9d}hC-aAI{$$80}p{$$03}naA`hlaA{$$90}"`{$$80}{$$90}W``"``
* **Slot `$09` @ `$c171`** (`macro_payload_09`)
  * Bytes: ``$66 $c2 $a5 $05 $9d $e7 $c2 $a5 $06 $9d $68 $c3 $ad $e1 $c1 $c9 $80 $f0 $03 $ee $e1 $c1 $60 $e8 $ec $e1 $c1 $90 $a2 $e0 $80 $90 $d7 $60 $60 $a2 $00``
  * PETSCII: ``fB%{$$05}{$$9d}gB%{$$06}{$$9d}hC-aAI{$$80}p{$$03}naA`hlaA{$$90}"`{$$80}{$$90}W``"``
* **Slot `$0d` @ `$c193`** (`macro_payload_13`)
  * Bytes: ``$60 $a2 $00``
  * PETSCII: ``\`"``
* **Slot `$14` @ `$c1ab`** (`macro_payload_20`)
  * Bytes: ``$68 $c3 $85 $06 $8e $e2 $c1 $a0 $00``
  * PETSCII: ``hC{$$85}{$$06}{$$8e}bA``

## Macro handler disassembly helper
The new `ml_extra_disasm` prototype wraps the repository opcode tables so macro payloads can be rendered as 6502 assembly without running the full PRG disassembler.【F:scripts/prototypes/ml_extra_disasm.py†L1-L395】 Slot 4’s output shows the routine copying source/destination pointers into `$c1e5/$c266/$c2e7/$c368` before incrementing `$c1e1`, matching the insertion logic traced earlier in the overlay disassembly.【314f88†L1-L33】

## Macro slot staging notes
Tracing the four non-trivial handlers revealed a shared staging loop anchored at `$c130` that walks `$c1e5/$c266/$c2e7/$c368` as circular buffers before copying the current `$03-$06` zero-page pointer tuple into the active slot.【F:scripts/prototypes/ml_extra_disasm.py†L347-L390】 Each pass keeps `$c1e1` in bounds (`<$80`) so follow-up calls reuse the recorded address pairs. The post-handler sweep at `$c196` walks those buffers in reverse, restoring the pointer tuple into `$03-$06` ahead of the indirect copy into `$ce77`. Slots `$04/$09/$0d/$14` are simply entry points into that shared loop: slot $04 seeds a new entry, slot $09 shortcuts to the write-back branch, slot $0d exits immediately, and slot $14 handles the `$0333/$0334` pointer adjustment before tail-calling the reload logic.【F:scripts/prototypes/ml_extra_disasm.py†L180-L255】 These notes give the next pass a concrete map of how `$c151/$c152` are primed before the text renderer runs.

## Flag-tail dump helper
`scripts/prototypes/ml_extra_dump_flag_strings.py` exposes the 70-byte, XOR-encoded block at `$d9c3` that feeds the flag directory tail and banner text. The helper prints both the raw payload and the decoded PETSCII, making it easy to capture the “1989 NEW IMAGE SOFTWARE, INC.” footer and surrounding metadata without manually poking the PRG.【F:scripts/prototypes/ml_extra_dump_flag_strings.py†L1-L71】 This gives us a reproducible byte-for-byte dump for transcription while the remaining macro payloads are decoded.

## Next steps
- Finalise the PETSCII transcription of the macro payloads (particularly the
  slot `$04/$09/$0d/$14` outputs) so the documentation includes the rendered
  strings alongside the disassembly notes.【F:scripts/prototypes/ml_extra_dump_macros.py†L1-L118】
