; ----------------------------------------------------------------------
; ImageBBS 1.2B "ml.extra" overlay (recovered data stub)
; ----------------------------------------------------------------------
; The rediscovered ml.extra overlay seeds a handful of kernel-visible
; defaults before dispatching ampersand helpers: lightbar bitmaps, underline
; metadata, the editor palette, and a pointer directory for twelve macro
; slots.  Host-side ports historically relied on this file for placeholder
; values.  It now mirrors the recovered payload so tooling can interrogate the
; real defaults without bundling the full overlay binary.
; ----------------------------------------------------------------------
;
; References:
;   - Lightbar behaviour: v1.2/source/ml_extra.asm around $d3d6.
;   - Macro pointer directory: v1.2/source/ml_extra.asm around $d116.
;
; ----------------------------------------------------------------------
; Kernel-visible addresses expected by ml-1_2-y2k.asm
; ----------------------------------------------------------------------

chk_left        = $07f4     ; page-1 lightbar (left column)
chk_right       = $07f5     ; page-1 lightbar (right column)
lightbar_p2_l   = $42e5     ; page-2 lightbar (left column)
lightbar_p2_r   = $42e6     ; page-2 lightbar (right column)
undchr          = $42e7
undcol          = $42e8

; ----------------------------------------------------------------------
; Default lightbar/underline state recovered from ml.extra (@$d3f6).
; ----------------------------------------------------------------------

DEFAULT_PAGE1_LEFT  = $00
DEFAULT_PAGE1_RIGHT = $03
DEFAULT_PAGE2_LEFT  = $06
DEFAULT_PAGE2_RIGHT = $00
DEFAULT_UNDER_CHAR  = $00
DEFAULT_UNDER_COLOR = $00

; ----------------------------------------------------------------------
; Entry point exposed to the bootstrap so the overlay looks legitimate.
; ----------------------------------------------------------------------

                .org $2000

ml_extra_stub_entry:
        lda #DEFAULT_PAGE1_LEFT
        sta chk_left
        lda #DEFAULT_PAGE1_RIGHT
        sta chk_right
        lda #DEFAULT_PAGE2_LEFT
        sta lightbar_p2_l
        lda #DEFAULT_PAGE2_RIGHT
        sta lightbar_p2_r
        lda #DEFAULT_UNDER_CHAR
        sta undchr
        lda #DEFAULT_UNDER_COLOR
        sta undcol
        rts

; ----------------------------------------------------------------------
; Convenience copies of the recovered data tables.
; ----------------------------------------------------------------------

lightbar_default_bitmaps:
        .byte DEFAULT_PAGE1_LEFT, DEFAULT_PAGE1_RIGHT
        .byte DEFAULT_PAGE2_LEFT, DEFAULT_PAGE2_RIGHT

underline_default:
        .byte DEFAULT_UNDER_CHAR, DEFAULT_UNDER_COLOR

; VIC-II palette used by the recovered ml.extra overlay (@$c66a).
editor_palette_default:
        .byte $0a, $02, $08, $00

; Macro pointer directory exported by ml.extra (@$d116 / @$d123).
macro_slot_ids:
        .byte $04, $09, $0d, $14, $15, $16, $17, $18, $19, $0e, $0f, $02
macro_runtime_targets:
        .word $c153, $c171, $c193, $c1ab, $c1e6, $c1f4, $c20d, $c225, $c230, $c24a, $c261, $c29d

; Raw macro payloads lifted from the overlay for host inspection.

macro_payload_04:
        .byte $c2,$9d,$66,$c2,$bd,$e6,$c2,$9d,$e7,$c2,$bd,$67,$c3,$9d,$68,$c3
        .byte $ca,$ec,$e2,$c1,$d0,$e2,$a5,$03,$9d,$e5,$c1,$a5,$04,$9d,$66,$c2
        .byte $a5,$05,$9d,$e7,$c2,$a5,$06,$9d,$68,$c3,$ad,$e1,$c1,$c9,$80,$f0
        .byte $03,$ee,$e1,$c1,$60,$e8,$ec,$e1,$c1,$90,$a2,$e0,$80,$90,$d7,$60
        .byte $60,$a2,$00

macro_payload_09:
        .byte $66,$c2,$a5,$05,$9d,$e7,$c2,$a5,$06,$9d,$68,$c3,$ad,$e1,$c1,$c9
        .byte $80,$f0,$03,$ee,$e1,$c1,$60,$e8,$ec,$e1,$c1,$90,$a2,$e0,$80,$90
        .byte $d7,$60,$60,$a2,$00

macro_payload_13:
        .byte $60,$a2,$00

macro_payload_20:
        .byte $68,$c3,$85,$06,$8e,$e2,$c1,$a0,$00

macro_payload_21:
        .byte $00
macro_payload_22:
        .byte $00
macro_payload_23:
        .byte $00
macro_payload_24:
        .byte $00
macro_payload_25:
        .byte $00
macro_payload_14:
        .byte $00
macro_payload_15:
        .byte $00
macro_payload_02:
        .byte $00

; For convenience expose a directory of payload labels matching the runtime slots.
macro_payload_directory:
        .word macro_payload_04, macro_payload_09, macro_payload_13, macro_payload_20
        .word macro_payload_21, macro_payload_22, macro_payload_23, macro_payload_24
        .word macro_payload_25, macro_payload_14, macro_payload_15, macro_payload_02

                .end
