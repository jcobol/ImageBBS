; Auto-generated disassembly of ml.extra
; Load address: $1000

                * = $1000

loc_1000:
                lda $03
                pha
                lda $04
                pha
                lda $05
                pha
                lda $06
                pha
                lda $07
                pha
                lda $08
                pha
                lda $31
                ldx $32
                sta $c1e3
                stx $c1e4
                lda $37
                ldx $38
                sta $33
                stx $34
loc_1024:
                lda #$00
                sta $c1e1
                lda $2d
                ldx $2e
                sta $03
                stx $04
                lda $03
                cmp $2f
                bne loc_103d
                lda $04
                cmp $30
                beq loc_1062
loc_103d:
                ldy #$00
                lda ($03),y
                bmi loc_105a
                iny
                lda ($03),y
                bpl loc_105a
                lda #$02
                jsr $c0b3
                ldy #$00
                jsr $c102
                lda #$05
                jsr $c0b3
                jmp $c031
loc_105a:
                lda #$07
                jsr $c0b3
                jmp $c031
loc_1062:
                lda $03
                cmp $31
                bne loc_106e
                lda $04
                cmp $32
                beq loc_1091
loc_106e:
                ldy #$00
                lda ($03),y
                bmi loc_107d
                iny
                lda ($03),y
                bpl loc_107d
                iny
                jsr $c0bd
loc_107d:
                ldy #$02
                clc
                lda $03
                adc ($03),y
                tax
                iny
                lda $04
                adc ($03),y
                stx $03
                sta $04
                jmp $c062
loc_1091:
                lda $c1e1
                beq loc_10a0
                jsr $c194
                lda $c1e1
                cmp #$80
                beq loc_1024
loc_10a0:
                pla
                sta $08
                pla
                sta $07
                pla
                sta $06
                pla
                sta $05
                pla
                sta $04
                pla
                sta $03
                rts
                clc
                adc $03
                sta $03
                bcc loc_10bc
                inc $04
loc_10bc:
                rts
                clc
                lda ($03),y
                adc $03
                sta $07
                iny
                lda ($03),y
                adc $04
                sta $08
                lda $03
                pha
                lda $04
                pha
                iny
                lda ($03),y
                asl a
                clc
                adc #$05
                jsr $c0b3
loc_10db:
                lda $03
                cmp $07
                bne loc_10e7
                lda $04
                cmp $08
                beq loc_10fa
loc_10e7:
                ldy #$00
                jsr $c102
                clc
                lda $03
                adc #$03
                sta $03
                bcc loc_10db
                inc $04
                jmp $c0db
loc_10fa:
                pla
                sta $04
                pla
                sta $03
                rts
loc_1101:
                rts
                lda ($03),y
                tax
                iny
                lda ($03),y
                sta $05
                iny
                lda ($03),y
                sta $06
                cpx #$00
                beq loc_1101
                lda $05
                cmp $c1e3
                lda $06
                sbc $c1e4
                bcc loc_1101
                lda $05
                cmp $33
                lda $06
                sbc $34
                bcs loc_1101
                ldx $c1e1
                beq loc_1169
                ldx #$00
loc_1130:
                lda $06
                cmp $c368,x
                bcc loc_1188
                bne loc_1142
                lda $05
                cmp $c2e7,x
                bcc loc_1188
                beq loc_1187
loc_1142:
                stx $c1e2
                cpx #$7f
                beq loc_1169
                ldx #$7f
loc_114b:
                lda $c1e4,x
                sta $c1e5,x
                lda $c265,x
                sta $c266,x
                lda $c2e6,x
                sta $c2e7,x
                lda $c367,x
                sta $c368,x
                dex
                cpx $c1e2
                bne loc_114b
loc_1169:
                lda $03
                sta $c1e5,x
                lda $04
                sta $c266,x
                lda $05
                sta $c2e7,x
                lda $06
                sta $c368,x
                lda $c1e1
                cmp #$80
                beq loc_1187
                inc $c1e1
loc_1187:
                rts
loc_1188:
                inx
                cpx $c1e1
                bcc loc_1130
                cpx #$80
                bcc loc_1169
                rts
loc_1193:
                rts
                ldx #$00
                cpx $c1e1
                beq loc_1193
                lda $c1e5,x
                sta $03
                lda $c266,x
                sta $04
                lda $c2e7,x
                sta $05
                lda $c368,x
                sta $06
                stx $c1e2
                ldy #$00
                lda ($03),y
                tax
                sec
                lda $33
                sbc ($03),y
                sta $33
                lda $34
                sbc #$00
                sta $34
                txa
                tay
                dey
loc_11c7:
                lda ($05),y
                sta ($33),y
                dey
                dex
                bne loc_11c7
                ldy #$01
                lda $33
                sta ($03),y
                iny
                lda $34
                sta ($03),y
                ldx $c1e2
                inx
                jmp $c196
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                jmp $460f
                jmp $f4a5
                brk
                ora ($02,x)
                .byte $04
                php
                bpl loc_142d
                rti
                .byte $80
                sta $93
                jsr $4306
                lda $b7
                beq loc_1437
                ldy #$00
                sty $90
                lda ($bb),y
                cmp #$24
                beq loc_1437
                lda $ba
                cmp #$08
                bcc loc_1437
                cmp #$10
                bcs loc_1437
                and #$07
                tax
                lda $4607,x
                and $4606
                bne loc_143c
loc_1437:
                lda $93
                jmp $4603
loc_143c:
                tsx
                stx $4752
                lda $d011
                sta $4756
                lda $dc0e
                sta $475b
                lda $d01a
                sta $4760
                ldy #$00
                ldx #$00
                sty $dc0e
                sty $d01a
                sty $d011
                sty $4722
loc_1462:
                cpy $b7
                bcs loc_1477
                lda ($bb),y
                iny
                sta $48af,x
                inx
                cmp #$3a
                bne loc_1473
                ldx #$00
loc_1473:
                cpx #$10
                bcc loc_1462
loc_1477:
                lda #$a0
loc_1479:
                cpx #$10
                bcs loc_1483
                sta $48af,x
                inx
                bcc loc_1479
loc_1483:
                lda $c3
                sta $ae
                lda $c4
                sta $af
                jsr $478b
                lda #$49
                jsr $ffa8
                jsr $ffae
                lda #$49
                sta $46bd
                lda #$04
                sta $46b1
                lda #$0a
                sta $4778
                ldx #$00
loc_14a7:
                lda #$57
                jsr $4779
                txa
                jsr $ffa8
                lda #$04
                jsr $ffa8
                lda #$1e
                tay
                jsr $ffa8
loc_14bb:
                lda $479e,x
                jsr $ffa8
                inx
                bne loc_14ca
                inc $46b1
                inc $46bd
loc_14ca:
                dey
                bne loc_14bb
                jsr $ffae
                dec $4778
                bne loc_14a7
                lda #$45
                jsr $4779
                lda #$d0
                jsr $ffa8
                lda #$04
                jsr $ffa8
                jsr $ffae
                lda #$07
                sta $dd00
loc_14ec:
                bit $dd00
                bmi loc_14ec
loc_14f1:
                ldy #$00
loc_14f3:
                ldx #$04
loc_14f5:
                bit $dd00
                bpl loc_14f5
                pha
                pla
                pha
                pla
                pha
                pla
                pha
                pla
loc_1502:
                lda $dd00
                asl a
                rol $ff
                asl a
                rol $ff
                nop
                nop
                nop
                nop
                dex
                bne loc_1502
                lda $ff
                sta $4900,y
                iny
                bne loc_14f3
                lda $4900
                bmi loc_156c
                ldx #$01
                lda #$00
                bne loc_1538
                dec $4722
                lda $b9
                beq loc_1536
                lda $4902
                sta $ae
                lda $4903
                sta $af
loc_1536:
                ldx #$03
loc_1538:
                inx
                lda $4900,x
                ldy #$00
                sta ($ae),y
                inc $ae
                bne loc_1546
                inc $af
loc_1546:
                cpx $4901
                bcc loc_1538
                lda $4900
                bne loc_14f1
                clc
loc_1551:
                ldx #$00
                txs
                pha
                lda #$00
                sta $d011
                lda #$00
                sta $dc0e
                lda #$00
                and #$7f
                sta $d01a
                pla
                ldx $ae
                ldy $af
                rts
loc_156c:
                lda #$04
                bit $05a9
                ldx #$80
                stx $90
                sec
                bcs loc_1551
                .byte $bf
                pha
                jsr $478b
                lda #$4d
                jsr $ffa8
                lda #$2d
                jsr $ffa8
                pla
                jmp $ffa8
                lda $ba
                jsr $ffb1
                lda $90
                bne loc_156f
                lda #$ff
                jsr $ff93
                lda $90
                bne loc_156f
                rts
                lda #$03
                sta $31
                lda $22
                cmp $08
                bne loc_1606
                jsr $f50a
loc_15ab:
                bvc loc_15ab
                clv
                lda $1c01
                sta ($30),y
                iny
                bne loc_15ab
                ldy #$ba
loc_15b8:
                bvc loc_15b8
                clv
                lda $1c01
                sta $0100,y
                iny
                bne loc_15b8
                jsr $f8e0
                jmp $0400
                pla
                clc
                adc #$01
                sta $042a
                pla
                jmp $0400
loc_15d5:
                lda $0300
                sta $08
                beq loc_1609
                lda $0301
                sta $09
                jsr $042c
loc_15e4:
                ldx #$00
                ldy $23
                lda $0302,y
                cmp #$82
                bne loc_15fb
loc_15ef:
                lda $0511,x
                cmp #$2a
                beq loc_1614
                cmp $0305,y
                beq loc_160e
loc_15fb:
                lda $23
                clc
                adc #$20
                sta $23
                bcs loc_15d5
                bcc loc_15e4
loc_1606:
                lda #$00
                bit $0ca9
loc_160b:
                jmp $f969
loc_160e:
                iny
                inx
                cpx #$10
                bcc loc_15ef
loc_1614:
                ldy $23
                lda $0303,y
                sta $08
                lda $0304,y
                sta $09
loc_1620:
                jsr $042c
                lda $0301
                sta $09
                lda $0300
                sta $08
                beq loc_1634
                lda #$ff
                sta $0301
loc_1634:
                lda $0300
                sta $21
                ldx #$04
                lda #$00
                sta $1800
loc_1640:
                lda #$00
                asl $21
                rol a
                asl $21
                rol a
                tay
                lda $04cc,y
                sta $1800
                dex
                bne loc_1640
                pha
                pla
                pha
                pla
                pha
                pla
                lda #$02
                sta $1800
                inc $0497
                bne loc_1634
                lda $08
                bne loc_1620
                lda #$01
                bne loc_160b
                asl a
                .byte $02
                php
                brk
                lda #$02
                sta $1800
                lda #$37
                sta $042a
                lda #$12
                sta $08
                lda #$00
                sta $23
                sta $09
loc_1682:
                lda #$e0
                sta $01
loc_1686:
                lda $01
                bmi loc_1686
                beq loc_1682
                sei
                ldx #$9d
                lda #$60
                sta $0300,x
loc_1694:
                lda $eb24,x
                sta $02ff,x
                dex
                bne loc_1694
                txa
loc_169e:
                sta $00,x
                inx
                bne loc_169e
                ldx #$45
                txs
                jsr $0300
                jsr $f263
                jmp $0521
                ldy #$a0
                ldy #$a0
                ldy #$a0
                ldy #$a0
                ldy #$a0
                ldy #$a0
                ldy #$a0
                ldy #$a0
                lda #$20
                jsr $f993
                inc $3e
                jmp $ebc5
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                cpx #$01
                beq loc_1807
                jmp $c022
loc_1807:
                ldx #$1e
                jsr $c1c8
                lda $62
                sta $14
                lda $61
                sta $15
                lda $01
                pha
                lda #$37
                sta $01
                jsr $a8a3
                pla
                sta $01
                rts
                ldx #$00
                jsr $c1c8
                ldy $61
                sty $d00f
loc_182c:
                lda ($62),y
                sta $ce77,y
                dey
                bpl loc_182c
                ldx #$18
                jsr $c1c8
                ldx $62
                sec
                lda #$00
                sta $c0db
                sta $c0dc
loc_1844:
                rol $c0db
                rol $c0dc
                dex
                bpl loc_1844
                ldx #$1e
                jsr $c1c8
                lda $62
                sta $c0dd
                lda $d00f
                beq loc_18a3
                ldy #$00
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
loc_1894:
                jsr $c155
                pla
                bcc loc_18b4
                lsr a
                lsr a
                lsr a
                lsr a
                and #$03
                clc
                adc #$01
loc_18a3:
                sta $62
                lda #$00
                sta $61
                sta $63
                sta $64
                sta $65
                ldx #$1e
                jmp $c1cd
loc_18b4:
                ldy #$00
                lda ($64),y
                and #$c0
                beq loc_18a3
                ldy #$00
                lda ($64),y
                ldx #$08
                and #$08
                bne loc_18c8
                ldx #$20
loc_18c8:
                clc
                txa
                adc $64
                sta $64
                tya
                adc $65
                sta $65
                cmp #$c8
                bne loc_1866
                lda #$00
                beq loc_18a3
                brk
                brk
                brk
                ldx #$00
                ldy #$03
loc_18e2:
                lda ($64),y
                beq loc_18f1
                cmp $ce77,x
                bne loc_18f6
                iny
                inx
                cpx #$07
                bne loc_18e2
loc_18f1:
                cpx $d00f
                beq loc_18f8
loc_18f6:
                clc
                rts
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
loc_190f:
                stx $d00f
                stx $61
                lda #$77
                sta $62
                lda #$ce
                sta $63
                ldx #$02
                jsr $c1cd
                ldy #$18
                ldx #$00
loc_1925:
                lda ($64),y
                beq loc_1932
                sta $ce27,x
                iny
                inx
                cpx #$08
                bcc loc_1925
loc_1932:
                stx $d00f
                stx $61
                lda #$27
                sta $62
                lda #$ce
                sta $63
                ldx #$01
                jsr $c1cd
                ldy #$1f
                lda ($64),y
                sta $62
                lda #$00
                sta $61
                ldx #$1f
                jsr $c1cd
                sec
                rts
                ldy #$00
                lda ($64),y
                and #$04
                beq loc_1964
                lda $d00f
                cmp #$02
                bcs loc_196b
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
loc_197d:
                clc
                rts
loc_197f:
                ldy #$05
                lda ($64),y
                sta $ce77
                ldy #$06
                lda ($64),y
                sta $ce78
                ldx #$02
                stx $d00f
                stx $61
                lda #$77
                sta $62
                lda #$ce
                sta $63
                ldx #$02
                jsr $c1cd
                ldy #$07
                lda ($64),y
                sta $62
                lda #$00
                sta $61
                ldx #$1f
                jsr $c1cd
                ldx #$01
                jsr $c1c8
                lda #$00
                sta $61
                lda #$27
                sta $62
                lda #$ce
                sta $63
                ldx #$01
                jsr $c1cd
                sec
                rts
                lda #$1d
                jmp $cd03
                lda #$1e
                jmp $cd03
                lda #$00
                jmp $cd03
                lda #$01
                ldy #$00
                jmp $cd03
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                jmp $c04b
                jmp $c05d
                jmp $c3b9
                jmp $c3d6
                lda #$17
                jmp $cd03
                sta $fe
                pha
                txa
                pha
                tya
                pha
                lda #$18
                jsr $cd03
                pla
                tay
                pla
loc_2020:
                tax
                pla
                rts
                lda #$1d
                jmp $cd03
                lda #$1e
                jmp $cd03
                lda #$1f
                jmp $cd03
                lda #$2b
                jmp $cd03
                lda #$2c
                jmp $cd03
                lda #$2e
                jmp $cd03
                lda #$2f
                jmp $cd03
                lda #$38
                jmp $cd03
                stx $d002
                sty $42fa
                ldx #$10
                jsr $c023
                lda $61
                and #$01
                sta $d001
                ldy #$00
                sty $d00f
                sty $07fc
                sty $07e8
                sty $d006
                sty $ce77
                jsr $c344
                lda $d002
                and #$30
                beq loc_208e
                ldx #$1b
                jsr $c023
                ldy $61
                beq loc_20c1
                sty $07fc
loc_2084:
                dey
                lda ($62),y
                sta $ce77,y
                cpy #$00
                bne loc_2084
loc_208e:
                ldy #$00
                cpy $07fc
                beq loc_20a7
loc_2095:
                lda $ce77,y
                jsr $c011
                iny
                cpy $07fc
                bcc loc_2095
                lda $07fc
                sta $d00f
loc_20a7:
                lda $d002
                and #$20
                beq loc_20b9
                jsr $c3af
                lda #$00
                sta $d00f
                jsr $c344
loc_20b9:
                jsr $c02d
                ldx #$1b
                jsr $c028
loc_20c1:
                jsr $c00c
                sta $fe
                jsr $c041
                beq loc_20d8
                lda #$00
                sta $d00f
                lda #$03
                sta $d006
                jmp $c193
loc_20d8:
                jsr $c032
                beq loc_20e3
                jsr $c046
                jmp $c05d
loc_20e3:
                lda $fe
                ldy $d00f
                ldx #$0d
loc_20ea:
                cmp $c115,x
                beq loc_213d
                dex
                bne loc_20ea
                jsr $c368
                bcc loc_20c1
loc_20f7:
                cpy $d004
                bcc loc_20ff
                jmp $c2c6
loc_20ff:
                sta $ce77,y
                jsr $c011
                inc $d00f
                ldy $d00f
                cpy $07fc
                bcc loc_2113
                sty $07fc
loc_2113:
                jmp $c0c1
                .byte $04
                ora #$0d
                .byte $14
                ora $16,x
                .byte $17
                clc
                ora $0f0e,y
                .byte $02
                rol $c153
                adc ($c1),y
                .byte $93
                cmp ($ab,x)
                cmp ($e6,x)
                cmp ($f4,x)
                cmp ($0d,x)
                .byte $c2
                and $c2
                bmi loc_20f7
                lsr a
                .byte $c2
                adc ($c2,x)
                sta $b0c2,x
                .byte $c2
loc_213d:
                dex
                txa
                asl a
                tax
                lda $c123,x
                sta $c151
                lda $c124,x
                sta $c152
                ldy $d00f
                jmp $ffff
                ldx $07fc
                beq loc_216e
                cpx $d00f
                beq loc_216e
loc_215d:
                cpy $07fc
                bcs loc_216b
                lda $ce78,y
                sta $ce77,y
                iny
                bne loc_215d
loc_216b:
                dec $07fc
loc_216e:
                jmp $c0c1
                ldx $07fc
                cpx $d004
                bcs loc_2190
                cpx $d00f
                beq loc_2188
                lda $ce76,x
                sta $ce77,x
                dex
                jmp $c179
loc_2188:
                inc $07fc
                lda #$20
                sta $ce77,y
loc_2190:
                jmp $c0c1
                jsr $c3af
                lda $d00f
                sta $61
                lda #$77
                sta $62
                lda #$ce
                sta $63
                ldx #$00
                jsr $c028
                jmp $c037
                cpy #$00
                beq loc_21bb
                lda $ce76,y
                jsr $c1d0
                dec $d00f
loc_21b8:
                jmp $c0c1
loc_21bb:
                ldx $d002
                bpl loc_21b8
                lda #$14
                sta $ce77
                lda #$01
                sta $d006
                rts
loc_21cb:
                eor #$80
                jmp $c011
                ldx $07ef
                bmi loc_21e2
                jsr $c398
                bcc loc_21e5
                cmp #$12
                beq loc_21cb
                cmp #$92
                beq loc_21cb
loc_21e2:
                jmp $c3b4
loc_21e5:
                rts
                cpy $07fc
                bcs loc_21f1
                lda $ce77,y
                jmp $c0f7
loc_21f1:
                jmp $c0c1
                jsr $c3af
                jsr $c344
                ldy #$00
loc_21fc:
                cpy $d00f
                bcs loc_220a
                lda $ce77,y
                jsr $c011
                iny
                bne loc_21fc
loc_220a:
                jmp $c0c1
loc_220d:
                cpy #$00
                beq loc_221f
                dey
                lda $ce77,y
                jsr $c1d0
                lda $ce77,y
                cmp #$20
                bne loc_220d
loc_221f:
                sty $d00f
                jmp $c0c1
                lda #$5c
                jsr $c011
                jsr $c3af
                jmp $c05d
loc_2230:
                ldy $d00f
                cpy $07fc
                bcs loc_2247
                lda $ce77,y
                cmp #$20
                php
                jsr $c011
                inc $d00f
                plp
                bne loc_2230
loc_2247:
                jmp $c0c1
                ldy $d00f
                cpy $07fc
                bcs loc_225e
                lda $ce77,y
                jsr $c011
                inc $d00f
                jmp $c24a
loc_225e:
                jmp $c0c1
                cpy #$00
                beq loc_228f
                lda #$00
                sta $07fd
                lda $d00f
                sta $07fe
loc_2270:
                ldy $07fd
                lda $ce77,y
                ldy $d00f
                cpy $d004
                bcs loc_228f
                sta $ce77,y
                inc $d00f
                jsr $c011
                inc $07fd
                dec $07fe
                bne loc_2270
loc_228f:
                ldy $d00f
                cpy $07fc
                bcc loc_229a
                sty $07fc
loc_229a:
                jmp $c0c1
                cpy #$00
                beq loc_22ad
loc_22a1:
                lda $ce76,y
                jsr $c1d0
                dey
                bne loc_22a1
                sty $d00f
loc_22ad:
                jmp $c0c1
                cpy #$00
                bne loc_22c1
                lda $d002
                and #$02
                beq loc_22c1
                lda #$01
                sta $d006
                rts
loc_22c1:
                lda #$2e
                jmp $c0f7
                sta $07fd
                lda $d002
                and #$10
                bne loc_22d8
                lda #$07
                jsr $c011
                jmp $c0c1
loc_22d8:
                lda $07fd
                ldx #$00
                cmp #$20
                beq loc_232f
                nop
                sta $07fd
                dey
loc_22e6:
                lda $ce77,y
                cmp #$20
                beq loc_230a
                dey
                bne loc_22e6
                lda $07fd
                sta $ce27
                ldx #$01
                stx $61
                lda #$27
                sta $62
                lda #$ce
                sta $63
                ldx #$1b
                jsr $c028
                jmp $c193
loc_230a:
                ldx #$00
                sty $07fe
                iny
                cpy $d00f
                bcs loc_2325
loc_2315:
                lda $ce77,y
                sta $ce27,x
                jsr $c3b4
                inx
                iny
                cpy $d00f
                bcc loc_2315
loc_2325:
                lda $07fd
                sta $ce27,x
                inx
                ldy $07fe
loc_232f:
                iny
                sty $d00f
                lda #$20
                sta $ce76,y
                nop
                nop
                nop
                nop
                nop
                nop
                nop
                nop
                nop
                jmp $c2f8
                lda $d002
                and #$04
                bne loc_2367
                lda $42fa
                pha
                lda #$00
                sta $42fa
                ldx #$1c
                jsr $c03c
                lda #$3a
                jsr $c011
                lda #$20
                jsr $c011
                pla
                sta $42fa
loc_2367:
                rts
                pha
                lda $d002
                and #$01
                beq loc_237f
                pla
                jsr $c398
                bcc loc_2394
                cmp #$12
                beq loc_2394
                cmp #$92
                beq loc_2394
                pha
loc_237f:
                pla
                cmp #$20
                bcc loc_2396
                cmp #$80
                bcc loc_2394
                cmp #$a0
                bcs loc_2394
                cmp #$85
                bcc loc_2396
                cmp #$8d
                bcs loc_2396
loc_2394:
                sec
                rts
loc_2396:
                clc
                rts
                sty $42f6
                ldy #$0f
loc_239d:
                cmp $e8da,y
                beq loc_23aa
                dey
                bne loc_239d
                ldy $42f6
                sec
                rts
loc_23aa:
                ldy $42f6
                clc
                rts
                lda #$0d
                jmp $c011
                lda #$14
                jmp $c011
                lda #$01
                sta $d001
                lda #$0f
                sta $d004
                lda #$04
                sta $d002
                lda #$01
                sta $42fa
                jsr $c05d
                lda #$00
                sta $42fa
                rts
                lda $c3f6,x
                sta $c3e0
                jsr $c3e2
                jsr loc_1000
                pha
                txa
                pha
                tya
                pha
                lda #$10
                ldy #$d0
                ldx #$10
                jsr $ca80
                pla
                tay
                pla
                tax
                pla
                rts
                brk
                .byte $03
                asl $00
                brk
                brk
                brk
                brk
                brk
                brk
                jmp $c11a
                jmp $c087
                jmp $c35b
                jmp $c0f0
                jmp $c2f2
                lda #$00
                jmp $cd03
                lda #$02
                jmp $cd03
                lda #$16
                jmp $cd03
                lda #$17
                jmp $cd03
                sta $fe
                pha
                txa
                pha
                tya
                pha
                lda #$18
                jsr $cd03
                pla
                tay
                pla
                tax
                pla
                rts
                lda #$1d
                jmp $cd03
                lda #$1e
                jmp $cd03
                lda #$1f
                jmp $cd03
                lda #$20
                jmp $cd03
                lda #$2b
                jmp $cd03
                lda #$2c
                jmp $cd03
                lda #$2d
                jmp $cd03
                lda #$2e
                jmp $cd03
                lda #$2f
                jmp $cd03
                lda #$30
                jmp $cd03
                lda #$31
                jmp $cd03
                sta $fe
                lda #$32
                jmp $cd03
                lda #$33
                jmp $cd03
                lda #$37
                jmp $cd03
                lda #$0d
                jmp $c023
                lda #$14
                jmp $c023
                lda #$00
                sta $fe
                sta $d008
                ldx #$22
                jsr $c058
                lda #$01
                sta $d007
                lda $d001
                pha
                lda $d003
                pha
                lda #$00
                sta $d001
loc_24a5:
                jsr $c049
                beq loc_24c8
                lda $07f1
                bpl loc_24b4
                lda #$00
                sta $07f1
loc_24b4:
                jsr $c062
                bne loc_24be
                jsr $c067
                beq loc_24a5
loc_24be:
                cmp #$13
                beq loc_24a5
                jsr $c023
                jmp $c0a5
loc_24c8:
                pla
                cmp $d003
                bcc loc_24d1
                sta $d003
loc_24d1:
                pla
                sta $d001
                lda #$00
                sta $d007
                ldx #$23
                jsr $c058
                lda $d002
                and #$82
                beq loc_24eb
                ldx #$27
                jsr $c058
loc_24eb:
                ldx #$24
                jmp $c2f2
                jsr $c03f
                lda $d009
                bmi loc_2503
                ldx #$18
                jsr $c035
                lda $62
                sta $d009
                rts
loc_2503:
                and #$7f
                sta $d009
                sta $62
                lda #$00
                sta $61
                ldx #$18
                jsr $c03a
                rts
loc_2514:
                lda #$00
                sta $42f7
                rts
loc_251a:
                lda #$01
                sta $42f7
                lda $028d
                cmp #$06
                beq loc_2514
                jsr $c062
                beq loc_253d
                ldx $cb
                cpx #$3f
                bne loc_2538
                ldx $028d
                cpx #$02
                beq loc_254a
loc_2538:
                sta $fe
                jsr $c073
loc_253d:
                jsr $c067
                lda $fe
                beq loc_251a
                jsr $c165
                jmp $c11a
loc_254a:
                jsr $4306
                lda $dd00
                pha
                and #$fb
                sta $dd00
                ldx #$04
                jsr $c019
                pla
                sta $dd00
                jsr $4303
                jmp $c11a
                lda $42e5
                and #$02
                bne loc_257c
                jmp $c06e
loc_256f:
                ldx #$00
                stx $c29d
                jmp $c06e
loc_2577:
                inx
                stx $c29d
                rts
loc_257c:
                lda $fe
                ldx $c29d
                sta $c28b,x
                lda $c28b
                cmp #$1b
                bne loc_256f
                cpx #$01
                bcc loc_2577
                lda $c28c
                cmp #$5b
                bne loc_256f
                cpx #$02
                bcc loc_2577
                lda $c28b,x
                cmp #$3b
                beq loc_2577
                cmp #$30
                bcc loc_25a9
                cmp #$3a
                bcc loc_2577
loc_25a9:
                ldx #$02
                stx $c29d
                cmp #$4d
                beq loc_25dd
                cmp #$c1
                beq loc_260f
                cmp #$c2
                beq loc_2624
                cmp #$c3
                beq loc_2629
                cmp #$c4
                beq loc_262e
                cmp #$c6
                beq loc_263e
                cmp #$c8
                beq loc_263e
                cmp #$ca
                beq loc_2633
                jmp $c16f
loc_25d1:
                lda #$00
                sta $c29d
                sta $c28b
                sta $c28c
                rts
loc_25dd:
                jsr $c2a9
                bcs loc_25d1
                cmp #$00
                bne loc_25ee
                lda #$92
                jsr $c06c
                jmp $c1dd
loc_25ee:
                cmp #$07
                bne loc_25fa
                lda #$12
                jsr $c06c
                jmp $c1dd
loc_25fa:
                cmp #$1e
                bcc loc_25dd
                cmp #$26
                bcs loc_25dd
                sec
                sbc #$1e
                tax
                lda $c2a1,x
                jsr $c06c
                jmp $c1dd
loc_260f:
                lda #$91
                sta $c28a
                jsr $c2a9
                bcc loc_261b
                lda #$01
loc_261b:
                sta $c289
                jsr $c277
                jmp $c1d1
loc_2624:
                lda #$11
                jmp $c211
loc_2629:
                lda #$1d
                jmp $c211
loc_262e:
                lda #$9d
                jmp $c211
loc_2633:
                lda #$93
                jsr $c06c
                jmp $c1d1
loc_263b:
                jmp $c1d1
loc_263e:
                jsr $c2a9
                bcs loc_263b
                sec
                sbc #$01
                sta $c29f
                lda $d3
                sta $c29e
                jsr $c2a9
                bcs loc_2659
                sec
                sbc #$01
                sta $c29e
loc_2659:
                lda #$13
                jsr $c06c
                lda #$11
                ldx $c29f
                jsr $c271
                lda #$1d
                ldx $c29e
                jsr $c271
                jmp $c1d1
                sta $c28a
                stx $c289
                lda $c289
                beq loc_2688
                lda $c28a
                jsr $c06c
                dec $c289
                jmp $c277
loc_2688:
                rts
                brk
                brk
                jsr loc_2020
                jsr loc_2020
                jsr loc_2020
                jsr loc_2020
                jsr loc_2020
                jsr loc_2020
                brk
                brk
                brk
                brk
                bcc loc_26bf
                asl $1f9e,x
                .byte $9c
                .byte $9f
                ora $a9
                brk
                sta $c2a0
                ldx $c29d
                lda $c28b,x
                inc $c29d
                cmp #$3b
                bne loc_26c4
                ldx $c29d
                lda $c28b,x
                inc $c29d
loc_26c4:
                cmp #$30
                bcc loc_26d1
                cmp #$3a
                bcc loc_26d6
                clc
                lda $c2a0
                rts
loc_26d1:
                sec
                lda $c2a0
                rts
loc_26d6:
                pha
                lda $c2a0
                asl a
                asl a
                clc
                adc $c2a0
                asl a
                sta $c2a0
                pla
                sec
                sbc #$30
                clc
                adc $c2a0
                sta $c2a0
                jmp $c2bb
                inc $42fb
                lda $42f3
                bne loc_2755
                lda #$80
                sta $fd
                lda #$cc
                ldy #$07
                sta $fb
                sty $fc
                ldy #$0f
                lda #$20
                ora $fd
loc_270c:
                sta ($fb),y
                dey
                bpl loc_270c
                jsr $c035
                ldy #$00
                sty $c35a
                sty $c359
                lda $61
                beq loc_2755
                cmp #$10
                bcs loc_272d
                lda #$10
                sec
                sbc $61
                lsr a
                sta $c359
loc_272d:
                lda ($62),y
                jsr $c3cb
                sty $c35a
                cmp #$00
                bmi loc_273f
                cmp #$40
                bcc loc_273f
                eor #$40
loc_273f:
                ora $fd
                ldy $c359
                sta ($fb),y
                inc $c359
                ldy $c35a
                iny
                cpy #$10
                bcs loc_2755
                cpy $61
                bcc loc_272d
loc_2755:
                dec $42fb
                rts
                brk
                brk
                lda $2f
                sta $47
                lda $30
                sta $48
                ldy #$02
                lda ($47),y
                sta $14
                iny
                lda ($47),y
                sta $15
                cpx #$00
                beq loc_278f
                clc
                lda $14
                adc $47
                sta $47
                lda $15
                adc $48
                sta $48
                lda $47
                cmp $31
                bne loc_278b
                lda $48
                cmp $32
                beq loc_27c2
loc_278b:
                dex
                jmp $c363
loc_278f:
                clc
                lda $47
                adc #$07
                sta $47
                lda $48
                adc #$00
                sta $48
                sec
                lda $14
                sbc #$07
                sta $14
                lda $15
                sbc #$00
                sta $15
loc_27a9:
                ldy #$00
                tya
                sta ($47),y
                inc $47
                bne loc_27b4
                inc $48
loc_27b4:
                lda $14
                bne loc_27ba
                dec $15
loc_27ba:
                dec $14
                bne loc_27a9
                lda $15
                bne loc_27a9
loc_27c2:
                rts
                bit $223a
                rol a
                .byte $3f
                and $5e0d,x
                cmp #$85
                bcc loc_27e0
                cmp #$8d
                bcs loc_27e0
                stx $42f8
                sec
                sbc #$85
                tax
                lda $c3c3,x
                ldx $42f8
loc_27e0:
                rts
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                brk
                jmp $c095
                jmp $c080
                jmp $c122
                jmp $c12d
                jmp $c170
                jmp $c209
                lda #$00
                jmp $cd03
                lda #$02
                jmp $cd03
                lda #$16
                jmp $cd03
                lda #$17
                jmp $cd03
                sta $fe
                pha
                txa
                pha
                tya
                pha
                lda #$18
                jsr $cd03
                pla
                tay
                pla
                tax
                pla
                rts
                lda #$1d
                jmp $cd03
                lda #$1e
                jmp $cd03
                lda #$1f
                jmp $cd03
                lda #$20
                jmp $cd03
                lda #$2b
                jmp $cd03
                lda #$2c
                jmp $cd03
                lda #$2d
                jmp $cd03
                lda #$2e
                jmp $cd03
                lda #$2f
                jmp $cd03
                lda #$30
                jmp $cd03
                lda #$31
                jmp $cd03
                sta $fe
                lda #$32
                jmp $cd03
                lda #$37
                jmp $cd03
                lda #$39
                jmp $cd03
                cpx #$00
                beq loc_2887
                stx $07f7
loc_2887:
                lda #$01
                sta $07f6
                jsr $c0a3
                lda #$00
                sta $07f6
                rts
                cpx #$00
                beq loc_289c
                stx $07f7
loc_289c:
                cpy #$00
                beq loc_28a3
                jmp $c0ed
loc_28a3:
                ldx $07f7
                ldy #$00
                jsr $c017
                lda $90
                sta $42f5
                lda $d00f
                beq loc_28bc
                lda $ce27
                cmp #$5e
                beq loc_28ec
loc_28bc:
                jsr $c042
                lda $d00f
                cmp #$50
                beq loc_28c9
                jsr $c047
loc_28c9:
                ldx #$0f
                jsr $c03d
                jsr $c042
                ldx #$11
                jsr $c03d
                jsr $c012
                lda $42f5
                bne loc_28ec
                lda $07f6
                bne loc_28a3
                ldx #$11
                jsr $c038
                lda $61
                beq loc_28a3
loc_28ec:
                rts
                sty $c118
loc_28f0:
                ldx $07f7
                jsr $ffc6
                jsr $ffe4
                sta $fe
                jsr $ffb7
                sta $42f5
                jsr $ffcc
                ldx $c118
                jsr $c266
                jsr $c076
                lda $d006
                bne loc_2917
                lda $42f5
                beq loc_28f0
loc_2917:
                rts
                brk
                ldy #$00
loc_291b:
                dey
                bne loc_291b
                dex
                bne loc_291b
                rts
                ldx #$03
loc_2924:
                lda $2f,x
                sta $c16c,x
                dex
                bpl loc_2924
                rts
                lda $2f
                sta $ac
                lda $30
                sta $ad
                ldx #$03
loc_2937:
                lda $c16c,x
                sta $2f,x
                dex
                bpl loc_2937
                lda $2f
                sta $ae
                lda $30
                sta $af
                ldy #$00
                lda ($ac),y
                sta ($ae),y
                lda $ae
                cmp $31
                bne loc_295c
                lda $af
                cmp $32
                bne loc_295c
                jmp $c07b
loc_295c:
                clc
                inc $ac
                bne loc_2963
                inc $ad
loc_2963:
                inc $ae
                bne loc_2969
                inc $af
loc_2969:
                jmp $c149
                and ($32),y
                .byte $33
                .byte $34
                lda $cc00
                sta $a000
                lda $cc01
                sta $a001
                jsr $c1b5
                lda #$01
                sta $61
                lda #$fd
                sta $62
                lda #$02
                sta $63
                ldx #$01
                jsr $c03d
                lda $02fe
                sta $62
                lda $02ff
                sta $61
                ldx #$1f
                jsr $c03d
                lda #$46
                sta $61
                lda #$c3
                sta $62
                lda #$c1
                sta $63
                ldx #$00
                jsr $c03d
                ldx #$00
                jsr $c05b
                ldy #$45
loc_29b7:
                lda $c1c3,y
                eor #$ff
                sta $c1c3,y
                dey
                bpl loc_29b7
                rts
                .byte $74
                .byte $a3
                ldy #$cf
                .byte $c7
                rol $32,x
                rol $3a38,x
                .byte $df
                and $2c3d,x
                .byte $df
                and #$ce
                cmp ($cd),y
                .byte $df
                bit $dfdc
                .byte $a3
                .byte $db
                ldx $dca3,y
                .byte $cb
                .byte $a3
                .byte $da
                lda $a374,x
                ldy #$cf
                .byte $cb
                .byte $d7
                .byte $3c
                dec $ce,x
                dec $c7
                dec $df
                and ($3a),y
                plp
                .byte $df
                rol $32,x
                rol $3a38,x
                .byte $df
                bit $3930
                .byte $2b
                plp
                rol $3a2d,x
                .byte $d3
                .byte $df
                rol $31,x
                .byte $3c
                cmp ($74),y
                cpx #$00
                beq loc_2a3f
                cpx #$02
                beq loc_2a14
                jmp $c26f
loc_2a14:
                jsr $c2c0
                lda #$00
                ldx #$f9
                jsr $c2c6
                lda #$00
                ldx #$60
                jsr $c2cd
                lda #$11
                jsr $c2d4
                ldx #$20
                jsr $c119
                lda #$10
                sta $d404
                ldx #$80
                jsr $c119
                lda #$00
                sta $d404
                rts
loc_2a3f:
                jsr $c2c0
                lda #$10
                ldx #$f0
                jsr $c2c6
                lda #$08
                sta $d403
                lda #$00
                ldx #$40
                jsr $c2cd
                lda #$41
                jsr $c2d4
                ldx #$80
                jsr $c119
                lda #$00
                sta $d404
                ldx #$20
                ldy #$00
loc_2a68:
                dey
                bne loc_2a68
                dex
                bne loc_2a68
                rts
                jsr $c2c0
                lda #$10
                ldx #$f0
                jsr $c2c6
                lda #$00
                ldx #$2c
                sta $42fe
                stx $42ff
                jsr $c2cd
                lda #$11
                jsr $c2d4
loc_2a8b:
                lda $42fe
                ldx $42ff
                jsr $c2cd
                inc $42fe
                bne loc_2a9c
                inc $42ff
loc_2a9c:
                lda $42ff
                cmp #$44
                bne loc_2a8b
loc_2aa3:
                lda $42fe
                ldx $42ff
                jsr $c2cd
                dec $42fe
                bne loc_2ab4
                dec $42ff
loc_2ab4:
                lda $42ff
                cmp #$2c
                bne loc_2aa3
                lda #$00
                jmp $c2d4
                lda #$0f
                sta $d418
                rts
                sta $d405
                stx $d406
                rts
                sta $d400
                stx $d401
                rts
                ldx #$00
                stx $d404
                sta $d404
                rts
