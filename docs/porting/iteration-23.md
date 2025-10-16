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

## Next steps
- Use these offsets to teach the extractor how to parse the short and long record layouts so the authentic bitmaps and page-two payloads can replace the stub defaults.
- Decode the `$c123/$c124` pointer list into human-readable strings, confirming which flag descriptions map to each slot before swapping them into `ml_extra_stub.asm`.
